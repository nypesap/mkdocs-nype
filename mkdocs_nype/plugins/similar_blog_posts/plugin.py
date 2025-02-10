"""MkDocs plugin made to automatically link related Blog posts

The ideation for the plugin was supported by ChatGPT, which suggested the usage of Jaccard Similarity
index method to calculate the relation score of the blog posts.

Calculating a static correlative number and ranking the relatedness of the posts allows to avoid
random selection purely based on same categories. A purely random selection would change the order
of the linked posts between MkDocs builds / deployments creating SEO noise.

If there is not enough similar posts, the plugin allows to fill up the list with not related posts.
This is random, but with the seed being the date of the post to prevent same results in similar cases,
while still stabilizing the results.

Can be seen in use here:

- https://fioritracker.org/usecases/preparation-for-upgrade/

MIT License 2024 Kamil Krzyśków (HRY) for Nype (npe.cm) and Fiori Tracker (fioritracker.org)
"""

import logging
import random
from pathlib import Path

from material.plugins.blog.plugin import BlogPlugin
from material.plugins.blog.structure import Category
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.plugins import BasePlugin, PrefixedLogger
from mkdocs.structure.files import Files
from mkdocs.structure.pages import Page

from .config import SimilarBlogPostsConfig


class SimilarBlogPostsPlugin(BasePlugin[SimilarBlogPostsConfig]):

    def __init__(self) -> None:

        self.blog_instance_map: dict[str, BlogPlugin] = {}
        self.sanitized_prefixes: list[str] = []

    def on_config(self, config: MkDocsConfig) -> MkDocsConfig | None:
        """Sanitize prefixes and load blog instances"""

        self.blog_instance_map.clear()
        self.sanitized_prefixes.clear()

        # The config value can be a str, convert it to a list
        if isinstance(self.config.hook_blog_dir, str):
            self.config.hook_blog_dir = [self.config.hook_blog_dir]

        # Prepare prefixes for synced validation
        self.sanitized_prefixes = [p.rstrip("/") + "/" for p in self.config.hook_blog_dir]

        # Load instances that have matching prefixes
        for name, instance in config.plugins.items():
            instance: BlogPlugin
            if name.split(" ")[0].endswith("/blog") and instance.config.enabled:
                blog_dir = instance.config.blog_dir.rstrip("/") + "/"
                if blog_dir in self.sanitized_prefixes:
                    self.blog_instance_map[blog_dir] = instance

        # Assert that all of the prefixes were added
        for prefix in self.sanitized_prefixes:
            if prefix not in self.blog_instance_map:
                LOG.warning(f"Prefix '{prefix}' not found among the blog instances")

        if self.blog_instance_map:
            LOG.info("Found matching blog instances")

    def on_page_markdown(
        self, markdown: str, /, *, page: Page, config: MkDocsConfig, files: Files
    ) -> str | None:
        """Add the section to a file"""

        # Ignore posts that don't have categories
        categories_self = page.meta.get("categories")
        if not categories_self:
            return

        # Use blog instance for current prefix
        for prefix in self.sanitized_prefixes:
            if page.file.src_uri.startswith(prefix):
                blog_instance = self.blog_instance_map[prefix]
                break
        else:
            return

        set_a = set(categories_self)
        similar_posts: list[Page, float] = []
        other_posts: list[Page, float] = []
        processed_post_ids = set()  # Track duplicates between categories

        # Find similar posts
        for view in blog_instance.blog.views:
            # Skip non-category views
            if not isinstance(view, Category):
                continue

            # Skip categories not related to current post
            if not self.config.allow_other_categories and view.name not in set_a:
                continue

            for post in view.posts:
                # Skip self and processed
                if post is page or id(post) in processed_post_ids:
                    continue

                categories_other = post.meta.get("categories")
                set_b = set(categories_other)
                score = self.weighted_jaccard_similarity(set_a, set_b)

                if score >= self.config.similarity_threshold:
                    similar_posts.append((post, score))
                elif self.config.allow_other_categories:
                    other_posts.append((post, score))

                processed_post_ids.add(id(post))

        # Early return if no similar posts were found
        if not similar_posts and not other_posts:
            return

        # Sort posts based on score from highest to lowest
        similar_posts = sorted(similar_posts, key=lambda p: -p[1])

        # Limit the result to max_shown
        if self.config.max_shown > 0 and len(similar_posts) > self.config.max_shown:
            similar_posts = similar_posts[: self.config.max_shown]

        # Randomize other_posts a bit to avoid padding all the posts with the same other_posts
        # Use seed to have somewhat constant results across different rebuilds, but also keep it unique to the post
        if len(similar_posts) < self.config.max_shown and other_posts:
            random.Random(str(page.meta["date"])).shuffle(other_posts)

        # Pad the missing links with posts from other categories
        while len(similar_posts) < self.config.max_shown and other_posts:

            if not self.config.allow_other_categories:
                break

            similar_posts.append(other_posts.pop())

        posts_md = ""
        current_path = Path(page.file.abs_src_path).parent

        for post, score in similar_posts:

            url_title = post.title
            url_path = (
                Path(post.file.abs_src_path).relative_to(current_path, walk_up=True).as_posix()
            )

            posts_md += f"- [{url_title}]({url_path})\n"

        section = SECTION_TEMPLATE.format(title=self.config.title, posts_md=posts_md)

        if self.config.append_at == "end":
            markdown += "\n\n" + section
        elif self.config.append_at == "start":
            # TODO Fix h1 tag handling
            LOG.warning("H1 handling is not done")
            markdown = section + "\n\n" + markdown
        else:
            LOG.error(f"Not supported setting {self.config.append_at=}")

        return markdown

    def weighted_jaccard_similarity(
        self, set_a: set[str], set_b: set[str], use_weights: bool = True
    ) -> float:
        """Jaccard Similarity method was suggested by ChatGPT. Currently only weighted variant is being used"""

        # Sanity check
        if not set_a or not set_b:
            return 0

        # Calculate the top part of the equation
        numerator = len(set_a.intersection(set_b))

        if numerator == 0:
            return 0

        # Use weights to handle small vs big sets a bit better
        if use_weights:
            weight_a = len(set_b) / (len(set_a) + len(set_b))
            weight_b = len(set_a) / (len(set_a) + len(set_b))
            denominator = (weight_a * len(set_a)) + (weight_b * len(set_b))
        else:
            # Calculate the bottom part of the equation
            denominator = len(set_a.union(set_b))

        return numerator / denominator


# region Constants

PLUGIN_NAME: str = "similar_blog_posts"
"""Name of this plugin. Used in logging."""

LOG: PrefixedLogger = PrefixedLogger(
    PLUGIN_NAME, logging.getLogger(f"mkdocs.plugins.{PLUGIN_NAME}")
)
"""Logger instance for this plugins."""

SECTION_TEMPLATE: str = (
    """
<div class="nype-similar" markdown>
<div class="nype-similar-title" markdown>{title}</div>
<div class="nype-similar-list" markdown>

{posts_md}

</div>
</div>
""".strip()
)

# endregion

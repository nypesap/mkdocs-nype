"""MkDocs plugin made to insert latest blog posts on a page.

This plugin was formerly a hook:
- https://github.com/nypesap/nypesap.github.io/blob/9951b6669868c657874740c6a124213785441864/overrides/hooks/latest_blog_posts.py

NOTE:
- Currently limited to the homepage.

MIT License 2024 Kamil Krzyśków (HRY) for Nype (npe.cm)
"""

import logging

from material.plugins.blog.plugin import BlogPlugin
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.exceptions import PluginError
from mkdocs.plugins import BasePlugin, PrefixedLogger
from mkdocs.structure.pages import Page
from mkdocs_minify_plugin import plugin as minify_plugin

from .config import LatestBlogPostsConfig


class LatestBlogPostsPlugin(BasePlugin[LatestBlogPostsConfig]):

    def __init__(self) -> None:
        super().__init__()

        self.exec_count = None

    def on_config(self, config: MkDocsConfig):
        BLOG_INSTANCE_MAP.clear()
        self.exec_count = {}

        for name, instance in config.plugins.items():
            instance: BlogPlugin
            if name.split(" ")[0].endswith("/blog"):
                if instance.config.enabled:
                    root = instance.config.blog_dir.rstrip("/") + "/"
                    BLOG_INSTANCE_MAP[root] = instance

    def on_page_markdown(self, markdown: str, page: Page, config: MkDocsConfig, files):

        if page.file.src_uri != "index.md":
            return

        # awesome-pages-plugin
        if config.nav is None:
            return

        self.exec_count[page.file.src_uri] = self.exec_count.get(page.file.src_uri, 0) + 1

        lines = markdown.split("\n")

        ext_body = ""
        ext_line = -1

        for i, line in enumerate(lines):
            if f"ext:{PLUGIN_NAME}" in line and ext_line < 0:
                if "-->" in line:
                    lines[i] = insert_latest_posts(line, config)
                else:
                    # TODO consider parsing this as the start tag, instead of fishing for it
                    if "<!--" in lines[i - 1]:
                        lines[i - 1] = ""
                    ext_body += line
                    ext_line = i
                    continue
            if ext_body:
                ext_body += " " + line.lstrip()
                lines[i] = ""
                if "-->" in line:
                    lines[ext_line] = insert_latest_posts(ext_body, config)
                    ext_body = ""
                    ext_line = -1

        # Add CSS on first exec
        if self.exec_count[page.file.src_uri] == 1:
            css = f"<style>{minify_plugin.csscompressor.compress(CSS_TEMLATE)}</style>\n"
            js = f"<script>{minify_plugin.jsmin.jsmin(JS_TEMPLATE)}</script>\n"
            lines[0] = f"{css}{js}{lines[0]}"

        return "\n".join(lines)


def insert_latest_posts(line, config: MkDocsConfig):

    raw_options = line.split("|")[-1].replace("-->", "").strip()
    options_pairs = [option.split("=") for option in raw_options.split(";") if option.strip()]
    options = {name.strip(): value.strip() for name, value in options_pairs}

    all_good = True

    for name in REQUIRED_OPTIONS:
        if name not in options:
            LOG.warning(f"Missing option {name}")
            all_good = False

    if not all_good:
        return line

    root = options["root"].rstrip("/") + "/"
    amount = int(options["amount"])
    display = options.get("display", "markdown").lower()
    title = options["title"]
    read_more = options["read_more"]
    strftime = options.get("strftime")
    if not strftime:
        strftime = "/timeago"

    if display != "markdown":
        LOG.warning("hook -> plugin migration only ported the display=markdown option")
        return line

    if root not in BLOG_INSTANCE_MAP:
        LOG.warning(f"Blog root {root} does not match any blog instance")
        return line

    instance: BlogPlugin = BLOG_INSTANCE_MAP[root]
    posts = instance.blog.posts[:amount]

    # Hack: extract title from nav, as the blog index file was not loaded yet
    blog_title = ""
    for entry in config.nav:
        for value in entry.values():
            if not isinstance(value, list):
                continue
            if root in value[0]:
                blog_title = list(entry.keys())[0]
        if blog_title:
            break

    li_entries = ""

    if display == "markdown":
        insert_body = MARKDOWN_GRID_TEMPLATE
        blog_index_url = instance.blog.file.src_uri
        for post in posts:
            href = post.file.src_uri
            text = post.title
            if strftime.startswith("/timeago"):
                date = post.config.date["created"]
                placeholder = post.config.date["created"].strftime("%Y-%m-%d")
                date_span = f'<span class="nype-latest-post-date" markdown>:material-clock-plus-outline: <span class="timeago" datetime="{date}" locale="en">{placeholder}</span></span>'
            else:
                date = post.config.date["created"].strftime(strftime)
                date_span = f'<span class="nype-latest-post-date">{date}</span>'
            li_entries += f"    - {date_span}\n    [{text}]({href})\n"
    elif display == "html_simple":
        insert_body = HTML_SIMPLE_TEMPLATE
        blog_index_url = instance.blog.file.url
        for post in posts:
            href = post.file.url
            text = post.title
            li_entries += f'<li><a href="{href}">{text}</a></li>\n'
    elif display == "html_grid":
        insert_body = HTML_GRID_TEMPLATE
        blog_index_url = instance.blog.file.url
        for post in posts:
            li_entries += render_html_grid_li(post, strftime)
    else:
        raise PluginError(f"display setting not supported: {display}")

    return insert_body.format(
        blog_title=blog_title,
        li_entries=li_entries,
        blog_index_url=blog_index_url,
        read_more=read_more,
        title=title,
    )


def render_html_grid_li(post, strftime):
    href = post.file.url
    text = post.title
    date = post.config.date["created"].strftime(strftime)
    return f"""
<li class="mdx-expect__item md-typeset" markdown>
<div class="mdx-expect__icon" markdown>
:material-feather:
</div>
<div class="mdx-expect__description" markdown>
<div class="extEntryTitle" markdown><a href="{href}" markdown>{text}</a></div>
<p markdown>{", ".join(post.config.categories)}</p>
<p markdown><span class="nype-latest-post-date">{date}</span></p>
</div>
</li>\n
""".lstrip()


PLUGIN_NAME: str = "latest_blog_posts"
"""Name of the plugin"""

LOG: PrefixedLogger = PrefixedLogger(
    PLUGIN_NAME, logging.getLogger(f"mkdocs.plugins.{PLUGIN_NAME}")
)
"""Logger instance for this plugin."""

BLOG_INSTANCE_MAP: dict[str, BlogPlugin] = {}
"""Mapping of active blog instances. Set in on_config"""

REQUIRED_OPTIONS: list[str] = ["root", "amount", "title", "read_more"]
"""List of lowercase required options to validate the input"""

HTML_SIMPLE_TEMPLATE: str = (
    """
<p>
<div>{title}</div>
<ul>
{li_entries}
</ul>
<div><a href="{blog_index_url}">{read_more}</a></div>
</p>
""".strip()
)

MARKDOWN_GRID_TEMPLATE: str = (
    """
- {title}

    ---

{li_entries}

    ---

    [{read_more}]({blog_index_url})

""".lstrip()
)

HTML_GRID_TEMPLATE: str = (
    """
<div class="md-grid" markdown>
<header class="md-typeset" markdown>
<h1 markdown>{title}</h1>
</header>
<div class="mdx-expect" markdown>
<ul class="mdx-expect__list" markdown>
{li_entries}
</ul>
</div>
<footer class="md-typeset" markdown>
<div class="extReadMore" markdown><a href="{blog_index_url}" markdown>{read_more}</a></div>
</footer>
</div>
""".strip()
)

CSS_TEMLATE: str = (
    """
.nype-latest-post-date {
    font-size: 0.65em;
    color: var(--md-default-fg-color--light);
    display: block;
}
.grid.cards ul {
    list-style: none;
}
.grid.cards ul li {
    margin-left: 0;
}
""".strip()
)

JS_TEMPLATE: str = (
    """
document.addEventListener("DOMContentLoaded", () => {
    "use strict";
    // Copied from 
    // https://github.com/timvink/mkdocs-git-revision-date-localized-plugin/blob/66b952c3ae8eae9fdd3b181bfaf9a3e1ee424208/mkdocs_git_revision_date_localized_plugin/js/timeago_mkdocs_material.js

    if (typeof document$ !== "undefined") {
        document$.subscribe(function() {
            const nodes = document.querySelectorAll('.timeago');
            if (nodes.length > 0) {
              const locale = nodes[0].getAttribute('locale');
              timeago.render(nodes, locale);
            }
        })
    } else {
        const nodes = document.querySelectorAll('.timeago');
        if (nodes.length > 0) {
          const locale = nodes[0].getAttribute('locale');
          timeago.render(nodes, locale);
        }
    }
});
""".strip()
)

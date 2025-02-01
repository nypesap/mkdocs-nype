"""MkDocs plugin made to add a custom categorization to the material/blog plugin.

This plugin was formerly a hook:
- https://github.com/nypesap/nypesap.github.io/blob/9951b6669868c657874740c6a124213785441864/overrides/hooks/add_industry_blog_view.py

By default the blog plugin only allows to use Archive and Category views.
This plugin adds another for a Custom view.

A lot of the code is based from the plugin as those instructions aren't in importable functions.

NOTE:
- This only generates the "back-end" Python data structures, the user has to add overrides for
  blog*.html templates. Use page.code_name or view.code_name to access the list of attached pages.
  (where code_name is the defined name in mkdocs.yml)

MIT License 2024 Kamil Krzyśków (HRY) for Nype (npe.cm)
"""

import inspect
import logging
import os
import posixpath
from typing import Optional

from material.plugins.blog.plugin import BlogPlugin
from material.plugins.blog.structure import View
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.exceptions import PluginError
from mkdocs.plugins import BasePlugin, PrefixedLogger, event_priority
from mkdocs.structure.files import Files, InclusionLevel
from mkdocs.structure.nav import Navigation, Section
from mkdocs.structure.pages import Page
from mkdocs.utils.templates import TemplateContext

from .config import CustomBlogCategorizationConfig

# region Core Logic Events


class CustomBlogCategorizationPlugin(BasePlugin[CustomBlogCategorizationConfig]):

    def __init__(self) -> None:
        super().__init__()

        self.blog_instance: BlogPlugin = None
        self.custom_view: View = None

    def on_config(self, config):
        """Load the Experience blog instance, override BlogPlugin._render_post"""

        self.blog_instance = self._get_exp_blog_instance(config)
        self.custom_view = self.config.view_generator()

        if self.blog_instance is None:
            LOG.warning("Blog instance with the given exp path was not found")
            return

        if not self.blog_instance.config.enabled:
            self.blog_instance = None
            LOG.info("Blog instance is not enabled")
            return

        if not isinstance(self.config.toc, bool):
            self.config.toc = self.blog_instance.config.blog_toc

        self.blog_instance._render_post = self.decorate_render_post(self.blog_instance._render_post)

        if self.blog_instance._render_post.__name__ != "wrapper":
            LOG.warning("_render_post toc override was not applied")
            return

        # Categories and Industries end with 'ies', or 'y' for singluar
        if self.config.singular_name is None:
            # Remove the last split element
            without_ies = self.config.render_name.split("ies")[:-1]
            # More ies than expected
            if not self.config.render_name.endswith("ies") or len(without_ies) != 1:
                raise PluginError(
                    f"Singular name could not be resolved for {self.config.render_name}. "
                    "Please set it manually."
                )
            else:
                self.config.singular_name = without_ies[0] + "y"

        LOG.info("Industry View override found no issues")

    # Run after the blog plugin
    @event_priority(-75)
    def on_files(self, files, *, config: MkDocsConfig):
        """Add the custom views to the blog"""
        if self.blog_instance is None:
            return

        if self.config.enabled:
            self.blog_instance.blog.views.extend(
                sorted(
                    self._generate_categorization_views(self.blog_instance, config, files),
                    key=lambda view: view.name,
                    reverse=False,
                )
            )

        if self.blog_instance.config.pagination:
            for view in self.blog_instance._resolve_views(self.blog_instance.blog):
                if not isinstance(view, self.custom_view):
                    continue
                for page in self.blog_instance._generate_pages(view, config, files):
                    view.pages.append(page)

    # Changing the priority can move position of the Categorizaion section from the bottom to the top
    @event_priority(-25)
    def on_nav(self, nav, *, config, files):
        """Attach views to navigation"""
        if self.blog_instance is None:
            return

        # Attach views for custom categorization
        if self.config.enabled:
            title = self.blog_instance._translate(self.config.render_name, config)
            views = [_ for _ in self.blog_instance.blog.views if isinstance(_, self.custom_view)]

            # Attach and link views for custom categorization, if any
            if self.blog_instance.blog.file.inclusion.is_in_nav() and views:
                self.blog_instance._attach_to(self.blog_instance.blog, Section(title, views), nav)

        # Attach pages for views
        if self.blog_instance.config.pagination:
            for view in self.blog_instance._resolve_views(self.blog_instance.blog):
                if not isinstance(view, self.custom_view):
                    continue
                for at in range(1, len(view.pages)):
                    self.blog_instance._attach_at(view.parent, view, view.pages[at])

    @event_priority(-75)
    def on_page_markdown(self, markdown, *, page, config, files):
        """Add custom categorization to the excerpt"""

        if not self.blog_instance or page not in self.blog_instance.blog.posts:
            return

        if not hasattr(page, self.config.code_name):
            return

        max_categorization = self.config.post_excerpt_max
        setattr(
            page.excerpt,
            self.config.code_name,
            getattr(page, self.config.code_name)[:max_categorization],
        )

        try:
            custom_categorizations = page.custom_categorizations
        except AttributeError:
            custom_categorizations = None

        if custom_categorizations is None:
            custom_categorizations = {}
            page.custom_categorizations = custom_categorizations
            page.excerpt.custom_categorizations = custom_categorizations

        custom_categorizations[self.config.code_name] = {
            "icon": self.config.icon,
            "plural_name": self.config.render_name,
            "singular_name": self.config.singular_name,
        }

    def decorate_render_post(self, func):
        """The categorization_toc isn't taken into account when rendering, so adjust the view afterwards"""

        if func.__name__ == "wrapper":
            return func

        expected_signature = "(excerpt: 'Excerpt', view: 'View')"
        current_signature = str(inspect.signature(func))

        if current_signature != expected_signature:
            LOG.error(f"signature is not the same\n'{current_signature}' != '{expected_signature}'")
            return func

        def wrapper(excerpt, view):
            excerpt = func(excerpt, view)

            if isinstance(view, self.custom_view):
                if self.config.toc and not self.blog_instance.config.blog_toc:
                    if excerpt.toc.items and view.toc.items:
                        view.toc.items[0].children.append(excerpt.toc.items[0])
                elif self.config.toc is False and self.blog_instance.config.blog_toc:
                    if view.toc.items:
                        view.toc.items[0].children = []

            return excerpt

        return wrapper

    def _get_exp_blog_instance(self, config: MkDocsConfig) -> Optional[BlogPlugin]:
        """Find the blog with the Experience URL"""

        for name, plugin in config.plugins.items():
            if not name.split(" ")[0].endswith("/blog"):
                continue
            if plugin.config.blog_dir == self.config.hook_blog_dir:
                return plugin

        return None

    def _generate_categorization_views(
        self, plugin: BlogPlugin, config: MkDocsConfig, files: Files
    ):
        """Generate views for custom categorization. Based on BlogPlugin._generate_categories"""
        for post in plugin.blog.posts:
            for name in post.meta.get(self.config.code_name, []):
                path = self._format_path_for_industry(plugin, name)

                # Ensure industry is in non-empty allow list
                allowed_names = self.config.allowed_values or [name]
                if name not in allowed_names:
                    docs = os.path.relpath(config.docs_dir)
                    path = os.path.relpath(post.file.abs_src_path, docs)
                    raise PluginError(
                        f"Error reading categorization name of post '{path}' in "
                        f"'{docs}': name '{name}' not in allow list"
                    )

                # Create file for view, if it does not exist
                file = files.get_file_from_path(path)
                if not file or plugin.temp_dir not in file.abs_src_path:
                    file = plugin._path_to_file(path, config)
                    files.append(file)

                    # Create file in temporary directory and temporarily remove
                    # from navigation, as we'll add it at a specific location
                    plugin._save_to_file(file.abs_src_path, f"# {name}")
                    file.inclusion = InclusionLevel.EXCLUDED

                # Create and yield view
                if not isinstance(file.page, self.custom_view):
                    yield self.custom_view(name, file, config)

                # Assign post to industry and vice versa
                assert isinstance(file.page, self.custom_view)
                file.page.posts.append(post)

                # Add custom list for our custom view type
                if not hasattr(post, self.config.code_name):
                    setattr(post, self.config.code_name, [])

                getattr(post, self.config.code_name).append(file.page)

    def _format_path_for_industry(self, plugin: BlogPlugin, name: str):
        """
        Format path for industry
        Based on BlogPlugin._format_path_for_category
        """
        path = self.config.url_format.format(slug=self._slugify_industry(name))

        # Normalize path and strip slashes at the beginning and end
        path = posixpath.normpath(path.strip("/"))
        return posixpath.join(plugin.config.blog_dir, f"{path}.md")

    def _slugify_industry(self, name: str):
        """Based on BlogPlugin._slugify_category"""
        separator = self.config.slugify_separator
        return self.config.slugify(name, separator)


# endregion


# region Constants

PLUGIN_NAME: str = "custom_blog_categorization"
"""Name of this plugin. Used in logging."""

LOG: PrefixedLogger = PrefixedLogger(
    PLUGIN_NAME, logging.getLogger(f"mkdocs.plugins.{PLUGIN_NAME}")
)
"""Logger instance for this plugins."""

# endregion

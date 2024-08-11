"""MkDocs plugin made to hide non-blog navigation entries when displaying a blog.

This plugin was formerly a hook:
- https://github.com/fioritracker/fioritracker.github.io/blob/3b6fb6ac0dea48aa40a8593fd94cce60d26a689c/overrides/hooks/display_blog_nav_only.py

MIT License Kamil Krzyśków (HRY) for Nype (npe.cm) and Fiori Tracker (fioritracker.org)
"""

import logging

from material.plugins.blog.plugin import BlogPlugin
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.plugins import BasePlugin, PrefixedLogger, event_priority
from mkdocs.structure.files import Files
from mkdocs.structure.nav import Navigation
from mkdocs.structure.pages import Page
from mkdocs.utils.templates import TemplateContext

from .config import OnlyBlogNavConfig


class OnlyBlogNavPlugin(BasePlugin[OnlyBlogNavConfig]):

    def __init__(self) -> None:
        self.non_blog_entries = []
        self.blog_entries = []
        self._all_entries_ref = None
        self.blog_parent = None
        self.is_nav_expand_enabled = False

    @event_priority(-75)
    def on_nav(
        self, nav: Navigation, /, *, config: MkDocsConfig, files: Files
    ) -> Navigation | None:
        """Run after blog plugin (-50). Gather 2 lists of nav entires that are inside and outside of the blog."""

        self.non_blog_entries.clear()
        self.blog_entries.clear()
        self._all_entries_ref = None
        self.blog_parent = None

        self.is_nav_expand_enabled = "navigation.expand" in config.theme["features"]

        for name, instance in config.plugins.items():
            instance: BlogPlugin
            if name.split(" ")[0].endswith("/blog"):
                if instance.config.blog_dir.strip("/").endswith(
                    self.config.hook_blog_dir.strip("/")
                ):
                    self.blog_parent = instance.blog.parent

        if self.blog_parent is None:
            LOG.warning(f"blog parent for {self.config.hook_blog_dir} not found")
            return nav

        self._all_entries_ref = nav.items

        for item in nav.items:
            if item is not self.blog_parent:
                self.non_blog_entries.append(item)
            else:
                self.blog_entries.append(item)

        LOG.info(f"blog parent for {self.config.hook_blog_dir} found")

    def on_page_context(
        self, context: TemplateContext, /, *, page: Page, config: MkDocsConfig, nav: Navigation
    ) -> TemplateContext | None:
        """Repalce the nav for pages in the blog"""

        if self.blog_parent is None:
            return

        if not page.file.src_uri.startswith(self.config.hook_blog_dir):
            if self.config.exclude_blog_from_nav:
                nav.items = self.non_blog_entries
            else:
                nav.items = self._all_entries_ref
            if self.config.material_navigation_expand and not self.is_nav_expand_enabled:
                if "navigation.expand" in config.theme["features"]:
                    config.theme["features"].remove("navigation.expand")
        else:
            nav.items = self.blog_entries
            if self.config.material_navigation_expand and not self.is_nav_expand_enabled:
                if "navigation.expand" not in config.theme["features"]:
                    config.theme["features"].append("navigation.expand")


PLUGIN_NAME: str = "only_blog_nav"
"""Name of the plugin"""

LOG: PrefixedLogger = PrefixedLogger(
    PLUGIN_NAME, logging.getLogger(f"mkdocs.plugins.{PLUGIN_NAME}")
)
"""Logger instance for this plugin."""

"""MkDocs plugin made to hide non-blog navigation entries.

This plugin was formerly a hook:
- https://github.com/fioritracker/fioritracker.github.io/blob/3b6fb6ac0dea48aa40a8593fd94cce60d26a689c/overrides/hooks/display_blog_nav_only.py

MIT License Kamil Krzyśków (HRY) for Nype (npe.cm) and Fiori Tracker (fioritracker.org)
"""

import logging

from material.plugins.blog.plugin import BlogPlugin
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.plugins import BasePlugin, PrefixedLogger, event_priority
from mkdocs.structure.nav import Navigation

from .config import OnlyBlogNavConfig


class OnlyBlogNavPlugin(BasePlugin[OnlyBlogNavConfig]):

    @event_priority(-75)
    def on_nav(self, nav: Navigation, config: MkDocsConfig, files):
        """Run after blog plugin (-50). Gather 2 lists of nav entires that are inside and outside of the blog."""

        NON_BLOG_ENTRIES.clear()
        BLOG_ENTRIES.clear()

        blog_parent = None
        for name, instance in config.plugins.items():
            instance: BlogPlugin
            if name.split(" ")[0].endswith("/blog"):
                if instance.config.blog_dir.strip("/").endswith(BLOG_ROOT):
                    blog_parent = instance.blog.parent

        if blog_parent is None:
            LOG.warning("blog parent not found")
            return nav

        for item in nav.items:
            if item is not blog_parent:
                NON_BLOG_ENTRIES.append(item)
            else:
                BLOG_ENTRIES.append(item)

        LOG.info("blog parent found")

    def on_page_context(self, context, page, config: MkDocsConfig, nav: Navigation):
        """Repalce the nav for pages in the blog"""

        if not page.file.src_uri.startswith(BLOG_ROOT):
            nav.items = NON_BLOG_ENTRIES
        else:
            nav.items = BLOG_ENTRIES


PLUGIN_NAME: str = "only_blog_nav"
"""Name of the plugin"""

LOG: PrefixedLogger = PrefixedLogger(
    PLUGIN_NAME, logging.getLogger(f"mkdocs.plugins.{PLUGIN_NAME}")
)
"""Logger instance for this plugin."""

NON_BLOG_ENTRIES = []
"""Non blog entries, filled in later"""

BLOG_ENTRIES = []
"""Blog entries, filled in later"""

BLOG_ROOT: str = "usecases"
"""blog_dir value to apply the instance"""

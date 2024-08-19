"""MkDocs plugin made to patch the date in a material/blog plugin instance.

This plugin was formerly a hook:
- https://github.com/nypesap/nypesap.github.io/blob/9951b6669868c657874740c6a124213785441864/overrides/hooks/patch_blog_date.py

By default when using multiple blog instances the `post_date_format` option of the last instance
modifies the date format for all instances. 
The patch replaces the date processor between pages to avoid the need to modify the template.

MIT License 2024 Kamil Krzyśków (HRY) for Nype (npe.cm)
"""

import logging
from datetime import datetime
from typing import Optional

from babel.dates import format_date, format_datetime
from jinja2 import Environment
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.plugins import BasePlugin, PrefixedLogger, event_priority

from .config import UniqueBlogDateConfig

# region Core Logic Events


class UniqueBlogDatePlugin(BasePlugin[UniqueBlogDateConfig]):

    def __init__(self) -> None:
        super().__init__()

        self.env_ref = None
        self.blog_filter_ref = None
        self.custom_filter_ref = None
        self._blog_root = None

    def on_config(self, config: MkDocsConfig) -> MkDocsConfig | None:
        """Validate a blog instance with the given root exists"""

        blog_instance = None
        for name, instance in config.plugins.items():
            if name.split(" ")[0].endswith("/blog"):
                if instance.config.blog_dir == self.config.hook_blog_dir:
                    blog_instance = instance

        if blog_instance is None:
            LOG.warning(f"Can't find blog {self.config.hook_blog_dir}")
            return

        self._blog_root = self.config.hook_blog_dir.rstrip("/") + "/"

    # Run after the blog plugin
    @event_priority(-100)
    def on_env(self, env: Environment, *, config: MkDocsConfig, **__) -> Optional[Environment]:
        """Main function. Triggers just before the build begins."""

        if not self._blog_root:
            return

        self.env_ref = env

        if not self.env_ref.filters.get("date"):
            return

        def custom_date_filter(date):
            return _format_date(date, self.config.date_format, config)

        self.custom_filter_ref = custom_date_filter
        self.blog_filter_ref = env.filters["date"]

        LOG.info("New blog date filter has been saved")

    @event_priority(-100)
    def on_page_context(self, context, page, config, nav):
        """Depending on the page url replace the filter"""

        if not self._blog_root or not self.env_ref.filters.get("date"):
            return

        if page.url.startswith(self._blog_root):
            LOG.debug("Custom filter applied")
            self.env_ref.filters["date"] = self.custom_filter_ref
        else:
            LOG.debug("Blog filter applied")
            self.env_ref.filters["date"] = self.blog_filter_ref


def _format_date(date: datetime, format: str, config: MkDocsConfig):
    """Copied from the material/blog plugin"""
    locale: str = config.theme["language"].replace("-", "_")
    if format in ["full", "long", "medium", "short"]:
        return format_date(date, format=format, locale=locale)
    else:
        return format_datetime(date, format=format, locale=locale)


# endregion


# region Constants

PLUGIN_NAME: str = "unique_blog_date"
"""Name of this plugin. Used in logging."""

LOG: PrefixedLogger = PrefixedLogger(
    PLUGIN_NAME, logging.getLogger(f"mkdocs.plugins.{PLUGIN_NAME}")
)
"""Logger instance for this plugin."""

# endregion

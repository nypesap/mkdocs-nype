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

_ENV_REF = None
_BLOG_FILTER_REF = None
_CUSTOM_FILTER_REF = None


class UniqueBlogDatePlugin(BasePlugin[UniqueBlogDateConfig]):

    # Run after the blog plugin
    @event_priority(-100)
    def on_env(self, env: Environment, *, config: MkDocsConfig, **__) -> Optional[Environment]:
        """Main function. Triggers just before the build begins."""
        global _ENV_REF
        global _BLOG_FILTER_REF
        global _CUSTOM_FILTER_REF

        _ENV_REF = env

        if not _ENV_REF.filters.get("date"):
            return

        def custom_date_filter(date):
            return _format_date(date, "yyyy MMMM", config)

        _CUSTOM_FILTER_REF = custom_date_filter
        _BLOG_FILTER_REF = env.filters["date"]

        LOG.info("New blog date filter has been saved")

    @event_priority(-100)
    def on_page_context(self, context, page, config, nav):
        """Depending on the page replace the filter"""

        if not _ENV_REF.filters.get("date"):
            return

        if page.url.startswith("exp/"):
            LOG.debug("Custom filter applied")
            _ENV_REF.filters["date"] = _CUSTOM_FILTER_REF
        else:
            LOG.debug("Blog filter applied")
            _ENV_REF.filters["date"] = _BLOG_FILTER_REF


def _format_date(date: datetime, format: str, config: MkDocsConfig):
    """Copied from the blog plugin"""
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

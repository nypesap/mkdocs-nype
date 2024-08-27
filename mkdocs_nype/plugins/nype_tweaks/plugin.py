"""MkDocs plugin made to apply small tweaks that don't need to be their own plugin.

This plugin is activated automatically for all projects using the mkdocs_nype theme.
This happens in the validate_with_nype_plugin_injection patch (__init__.py).

1. URL collision detection tweak:
Automatically detect page URL collisions. This is useful when a blog plugin uses
raw slugs and 2 pages can have the same slug.

2. Theme __init__.py issue count handler tweak:
When the --strict flag is used, warnings from the theme __init__.py were ignored.
This tweak fixes it. TODO There is probably a better way, because if nype_tweaks 
won't run automatically, due to an error, then this tweak will not be applied.

MIT License 2024 Kamil Krzyśków (HRY) for Nype (npe.cm)
"""

import logging

from mkdocs.config.defaults import MkDocsConfig
from mkdocs.plugins import BasePlugin, PrefixedLogger, event_priority
from mkdocs.structure.pages import Page
from mkdocs.utils import CountHandler

from .config import NypeTweaksConfig

# region Core Logic Events


class NypeTweaksPlugin(BasePlugin[NypeTweaksConfig]):

    def __init__(self) -> None:
        self.dest_url_mapping = {}

    @event_priority(110)
    def on_config(self, config: MkDocsConfig) -> MkDocsConfig | None:
        """Break convention of max 100 priority"""

        self.dest_url_mapping.clear()

        LOG.info("Tweaks initialized")

        # Theme __init__.py issue count handler tweak
        if config.strict:
            theme_counts = {}
            for handler in logging.getLogger("mkdocs.themes.mkdocs_nype").handlers:
                if isinstance(handler, CountHandler):
                    theme_counts = handler.counts
            for handler in logging.getLogger("mkdocs").handlers:
                if isinstance(handler, CountHandler):
                    for level, count in theme_counts.items():
                        handler.counts[level] += count

    @event_priority(-100)
    def on_post_page(self, output: str, /, *, page: Page, config: MkDocsConfig) -> str | None:

        # URL collision detection tweak
        if page.file.dest_uri in self.dest_url_mapping:
            file_path = self.dest_url_mapping[page.file.dest_uri]
            LOG.warning(
                f"URL: {page.file.dest_uri} is already used in {file_path}\nWarning from: {page.file.src_uri}"
            )
        else:
            self.dest_url_mapping[page.file.dest_uri] = page.file.src_uri


# endregion

# region Constants

PLUGIN_NAME: str = "nype_tweaks"
"""Name of this plugin. Used in logging."""

LOG: PrefixedLogger = PrefixedLogger(
    PLUGIN_NAME, logging.getLogger(f"mkdocs.plugins.{PLUGIN_NAME}")
)
"""Logger instance for this plugin."""

# endregion

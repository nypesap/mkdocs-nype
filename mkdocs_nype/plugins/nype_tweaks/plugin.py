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

3. Extend macros includes directory tweak:
mkdocs-macros-plugin only allows to set one directory for includes. However, the
Jinja2.loaders.FileSystemLoader supports a list of paths, so override the macros
plugin reference to FileSystemLoader.

4. HEX data obfuscation tweak:
Some data should be obfuscated in plain HTML to make it harder for bots to scrape 
them. The obfuscation happens just before passing data to JavaScript. Later on 
this data is deobfuscated in JavaScript.

MIT License 2024 Kamil Krzyśków (HRY) for Nype (npe.cm)
"""

import logging
import os
import sys

import material
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.livereload import LiveReloadServer
from mkdocs.plugins import BasePlugin, CombinedEvent, PrefixedLogger, event_priority
from mkdocs.structure.files import Files
from mkdocs.structure.pages import Page
from mkdocs.utils import CountHandler
from mkdocs_macros import plugin as macros_module

from ...utils import MACROS_INCLUDES_ROOT
from . import utils
from .config import NypeTweaksConfig
from .utils import ServeMode

# region Core Logic Events


class NypeTweaksPlugin(BasePlugin[NypeTweaksConfig]):

    def __init__(self) -> None:
        self.dest_url_mapping = {}

    @event_priority(110)
    def on_config(self, config: MkDocsConfig) -> MkDocsConfig | None:
        """Break convention of max 100 priority"""

        self.dest_url_mapping.clear()

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

        # Extend macros includes directory tweak
        if not ServeMode.run_once:
            macros_module.FileSystemLoader = utils.get_file_system_loader

        LOG.info("Tweaks initialized")

    def on_env(
        self, env: macros_module.Environment, /, *, config: MkDocsConfig, files: Files
    ) -> macros_module.Environment | None:
        # HEX data obfuscation tweak
        env.filters["obfuscate"] = utils.obfuscate

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

    @event_priority(-25)
    def _on_page_markdown_social_meta(
        self, markdown: str, /, *, page: Page, config: MkDocsConfig, files: Files
    ) -> str | None:
        """Run after community version Social plugin"""

        if "insiders" in material.__version__:
            return

        meta = page.meta.get("meta")

        if not meta:
            return

        for tag in meta:
            for attr, value in list(tag.items()):
                if attr == "property":
                    if value == "og:title":
                        tag["name"] = "title"
                    if value == "og:image":
                        tag["name"] = "image"

    on_page_markdown = CombinedEvent(_on_page_markdown_social_meta)

    def on_post_build(self, *, config: MkDocsConfig) -> None:

        # Generate robots.txt tweak
        sitemap_xml = config.site_url.rstrip("/") + "/sitemap.xml"
        robots_txt = os.path.join(config.site_dir, "robots.txt")
        with open(robots_txt, "w", encoding="utf-8") as file:
            file.write(
                "\n".join(
                    [
                        "User-agent: *",
                        "Allow: /",
                        "",
                        f"Sitemap: {sitemap_xml}",
                    ]
                )
            )

    def on_serve(
        self, server: LiveReloadServer, /, *, config: MkDocsConfig, builder
    ) -> LiveReloadServer | None:

        if "--watch-theme" in sys.argv:
            server.watch(str(MACROS_INCLUDES_ROOT))

        ServeMode.run_once = True


# endregion

# region Constants

PLUGIN_NAME: str = "nype_tweaks"
"""Name of this plugin. Used in logging."""

LOG: PrefixedLogger = PrefixedLogger(
    PLUGIN_NAME, logging.getLogger(f"mkdocs.plugins.{PLUGIN_NAME}")
)
"""Logger instance for this plugin."""

# endregion

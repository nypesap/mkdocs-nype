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

5. Blog cards tweak:
To convert a normal blog post Excerpt to a Grid Card some HTML needs to be read
from the page.content. The provided filter functions get called in the
post-card.html template.

6. Create nype_config for page and sync with global tweak:
This was previously done at render time in nype-base.html, but this is too late
for blog cards meta placeholders. To use the global value for the placeholder
better set it in the event. Errata: Turned out this train of thought was wrong,
as the posts' on_page events run after the blog index with the cards, so the
tweak doesn't make things easier. Global placeholder loading was moved to the
post-card.html template.

7. Enable default tag icon tweak:
The Material tags plugin allows to set icons for each tag, however there is
also the default icon, which isn't turned on without setting other icon mappings.
The tweak sets the required settings to show the default icon on tags.
https://github.com/squidfunk/mkdocs-material/issues/7688

8. footer_nav tweak:
To allow normal file system paths in the nype_config->footer_nav this tweak
needed to be implemented to convert the file system paths into the URLs used in
the copyright.html template.

MIT License 2024 Kamil Krzyśków (HRY) for Nype (npe.cm)
"""

import datetime
import logging
import os
import sys

import material
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.exceptions import PluginError
from mkdocs.livereload import LiveReloadServer
from mkdocs.plugins import BasePlugin, CombinedEvent, PrefixedLogger, event_priority
from mkdocs.structure.files import Files
from mkdocs.structure.nav import Navigation
from mkdocs.structure.pages import Page
from mkdocs.utils import CountHandler
from mkdocs.utils.templates import TemplateContext
from mkdocs_macros import plugin as macros_module
from pathspec.gitignore import GitIgnoreSpec

from ...utils import MACROS_INCLUDES_ROOT
from . import utils
from .config import NypeTweaksConfig
from .utils import ServeMode

# region Core Logic Events


class NypeTweaksPlugin(BasePlugin[NypeTweaksConfig]):

    def __init__(self) -> None:
        self.dest_url_mapping = {}
        self.draft_paths: GitIgnoreSpec = None
        self.nype_config_key = "nype_config"
        self.default_footer_nav = {
            "Contact": "contact.md",
            "Impressum": "impressum.md",
            "Offer": "offer.md",
        }

    @event_priority(110)
    def on_config(self, config: MkDocsConfig) -> MkDocsConfig | None:
        """Break convention of max 100 priority"""

        self.dest_url_mapping.clear()
        self.draft_paths = None

        draft_paths: str = config.theme.get("nype_config", {}).get("exclude_via_robots")
        if draft_paths:
            self.draft_paths = GitIgnoreSpec.from_lines(lines=draft_paths.splitlines())

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

        # Enable default tag icon tweak
        if not config.theme.get("icon"):
            config.theme["icon"] = {}
        if not config.theme["icon"].get("tag"):
            config.theme["icon"]["tag"] = {}
        if not config.theme["icon"]["tag"].get("default"):
            config.theme["icon"]["tag"]["default"] = "material/tag"
        if not config.extra.get("tags"):
            config.extra["tags"] = {"_": "_"}

        # Set current year in copyright tweak
        year: str = str(datetime.datetime.now().year)
        config.copyright = config.copyright.format(year=year)

        LOG.info("Tweaks initialized")

    def on_env(
        self, env: macros_module.Environment, /, *, config: MkDocsConfig, files: Files
    ) -> macros_module.Environment | None:
        # HEX data obfuscation tweak
        env.filters["obfuscate"] = utils.obfuscate

        # blog cards tweak
        env.filters["post_card_title"] = utils.post_card_title
        env.filters["post_card_description"] = utils.post_card_description

        # footer_nav tweak
        footer_nav = config.theme.get("nype_config", {}).get("footer_nav")

        # If the footer_nav is not defined, try to fill it in automatically
        if footer_nav is None:
            if config.theme.get("nype_config") is None:
                config.theme["nype_config"] = {}

            config.theme["nype_config"]["footer_nav"] = footer_nav = []

            for title, path in self.default_footer_nav.items():
                file = files.get_file_from_path(path)
                if file:
                    footer_nav.append({"title": title, "path": path})

        for i, item in enumerate(footer_nav):

            # Support both title: path dicts and pure path str
            if isinstance(item, dict) and item.get("path") is None:
                if len(item) > 1:
                    raise PluginError(f"footer_nav value structure not supported: {item}")
                key = next((key for key in item))
                footer_nav[i] = item = {"title": key, "path": item[key]}
            elif isinstance(item, str):
                footer_nav[i] = item = {"title": None, "path": item}

            file = files.get_file_from_path(item["path"])
            if not file:
                LOG.warning(f"footer_nav value {item['path']} doesn't link to a file")
                continue

            footer_nav[i]["path"] = file.page.url
            if footer_nav[i]["title"] is None:
                footer_nav[i]["title"] = file.page.title

    @event_priority(100)
    def on_template_context(
        self, context: TemplateContext, /, *, template_name: str, config: MkDocsConfig
    ) -> TemplateContext | None:

        prepare_context_with_nype_config(context, config)

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

    def _on_page_markdown_robots(
        self, markdown: str, /, *, page: Page, config: MkDocsConfig, files: Files
    ) -> str | None:
        """Set the meta noindex value for draft_paths"""

        if not self.draft_paths:
            return

        if not self.draft_paths.match_file(page.file.src_uri):
            return

        if page.meta.get("nype_config") is None:
            page.meta["nype_config"] = {}

        page.meta["nype_config"]["robots_content"] = "noindex"

        # Set urls to None to hide the page from the sitemap.xml
        # In case of bugs another option is to override the sitemap.xml template
        page.canonical_url = None
        page.abs_url = None

        LOG.debug(f"robots_content set for {page.file.src_uri}")

    @event_priority(100)
    def _on_page_markdown_nype_config(
        self, markdown: str, /, *, page: Page, config: MkDocsConfig, files: Files
    ) -> str | None:

        # Make sure meta keys are present
        # As they could be used in templates, or macros etc.
        meta_config = page.meta.get(self.nype_config_key)
        if meta_config is None:
            meta_config = page.meta[self.nype_config_key] = {}

        meta_js = meta_config.get("js")
        if meta_js is None:
            meta_js = meta_config["js"] = {}

        required_js_keys = meta_config.get("required_js_keys")
        if required_js_keys is None:
            required_js_keys = meta_config["required_js_keys"] = {}

    on_page_markdown = CombinedEvent(
        _on_page_markdown_social_meta,
        _on_page_markdown_robots,
        _on_page_markdown_nype_config,
    )

    @event_priority(100)
    def on_page_context(
        self, context: TemplateContext, /, *, page: Page, config: MkDocsConfig, nav: Navigation
    ) -> TemplateContext | None:

        prepare_context_with_nype_config(context, config, page=page)

    def on_post_build(self, *, config: MkDocsConfig) -> None:

        # Add the draft_paths into disallowed paths in the robots.txt file
        disallow_paths = set()
        if self.draft_paths:
            draft_paths: str = config.theme["nype_config"]["exclude_via_robots"].splitlines()
            for path in draft_paths:
                path = "/" + path.strip().strip("/") + "/"
                disallow_paths.add(path)

        # Generate robots.txt tweak
        site_url = config.site_url if config.site_url else ""
        if not site_url:
            LOG.warning("Expected config.site_url to be set, was empty or none")
        sitemap_xml = site_url.rstrip("/") + "/sitemap.xml"
        robots_txt = os.path.join(config.site_dir, "robots.txt")
        with open(robots_txt, "w", encoding="utf-8") as file:
            file.write(
                "\n".join(
                    [
                        "User-agent: *",
                        "Disallow: /ggl-db/",  # ggl - Google Analytics
                        "Disallow: /ggl-ggl/",
                        "Disallow: /ggl-tdb/",
                        "Disallow: /ggl-syn/",
                        "Disallow: /ggl-tm/",
                        "Disallow: /ggl-as2-str/",
                        "Disallow: /ggl-a2-/",
                        "Disallow: /ggl-a-/",
                        "Disallow: /nr/",  # nr - Nype Redirect
                        *([f"Disallow: {p}" for p in disallow_paths] + [""]),
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


def prepare_context_with_nype_config(
    context: TemplateContext, config: MkDocsConfig, page: Page = None
):
    """
    The context needs to be prepared for both the templates like 404.html and Pages
    Create nype_config for page and sync with global tweak
    """

    # Define a nype_config dict for the current page, instead of working with references
    page_nype_config = {"js": dict()}
    page_js = page_nype_config["js"]

    # Get global config
    theme_nype_config = config.theme.get("nype_config") or {}

    # Get the local meta config
    meta_config = {}
    if page:
        meta_config = page.meta.get("nype_config") or {}

    # Load global values into the local dict. Skip 'js' to not copy a reference
    for name, value in theme_nype_config.items():
        if name != "js":
            page_nype_config[name] = value

    # Load JavaScript separately to create new memory references
    theme_js = theme_nype_config.get("js") or {}
    for name, value in theme_js.items():
        page_js[name] = value

    # Load values from meta_config, which can override globals. Skip 'js' to not copy a reference
    for name, value in meta_config.items():
        if name != "js":
            page_nype_config[name] = value

    # Include global 'non-js' values in the js of the current page
    js_include = meta_config.get("js_include") or ""
    for name in js_include.split():
        value = page_nype_config.get(name)
        if value is None:
            LOG.warning(
                f"The value for page_nype_config.{name} is undefined. File: {page.file.src_uri}"
            )
        page_js[name] = value

    # Override JavaScript with values from meta config
    meta_js = meta_config.get("js") or {}
    for name, value in meta_js.items():
        page_js[name] = value

    # Validate all dict keys are lowercase to avoid any issues
    for key in page_nype_config.keys() | page_js.keys():
        if key != key.lower():
            LOG.warning(f"The '{key}' key is not lowercase. File: {page.file.src_uri}")

    # Validate all required keys are available. This can be set inside a macro template.
    required_js_keys = page_nype_config.get("required_js_keys") or {}
    for key in required_js_keys:
        if key not in page_js:
            LOG.warning(f"The required '{key}' key is not available. File: {page.file.src_uri}")

    # Obfuscate values that should not be in plain text in the HTML
    for name, value in page_js.items():
        if name.endswith("_hex"):
            value = utils.obfuscate(value)
            page_js[name] = value

    # Pass local variable to the templates
    for key in ("page_nype_config", "theme_nype_config", "meta_config"):
        if context.get(key):
            LOG.warning(f"'{key}' is already present in the Context, overriding...")
        context[key] = locals().get(key)


# endregion

# region Constants

PLUGIN_NAME: str = "nype_tweaks"
"""Name of this plugin. Used in logging."""

LOG: PrefixedLogger = PrefixedLogger(
    PLUGIN_NAME, logging.getLogger(f"mkdocs.plugins.{PLUGIN_NAME}")
)
"""Logger instance for this plugin."""

# endregion

"""MkDocs plugin made to handle custom links in Markdown and render them.

This is made as a plugin instead of a Markdown Extension, because we need to access page.meta.tags from MkDocs.
We could pass the page.meta object via mdx_configs to a Markdown Extension, however this would add complexity.

MIT License 2024 Kamil Krzyśków (HRY) for Nype (npe.cm)
"""

import logging
import re
from xml.etree import ElementTree as etree

from markdown import util as md_util
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.plugins import BasePlugin, PrefixedLogger, event_priority
from mkdocs.structure.files import Files
from mkdocs.structure.pages import Page

from .config import CustomAutoLinksConfig

# region Core Logic Events


class CustomAutoLinksPlugin(BasePlugin[CustomAutoLinksConfig]):

    def __init__(self) -> None:

        self.pattern = re.compile(
            pattern=r'(?P<prefix>\s|\]\(|")(?P<proto>fal)://(?P<mode>\w!)?(?P<url>.*?)(?=\s|\)|")',
            flags=re.IGNORECASE | re.MULTILINE,
        )

    @event_priority(100)
    def on_page_markdown(
        self, markdown: str, /, *, page: Page, config: MkDocsConfig, files: Files
    ) -> str | None:

        def process_links(match: re.Match) -> str:
            proto = match.group("proto")
            mode = match.group("mode")
            prefix = match.group("prefix") or ""

            el: etree.Element
            if proto == "fal":
                el = self._process_fal(match, page)
            else:
                raise NotImplementedError(f"'{proto}' protocol not supported")

            # Strip the prefix to find out if there is a character other than space
            if mode == "r!" or prefix.strip():
                return prefix + el.get("href")
            else:
                return prefix + etree.tostring(el, encoding="utf-8", method="html").decode(
                    encoding="utf-8"
                )

        return re.sub(pattern=self.pattern, repl=process_links, string=markdown)

    def _process_fal(self, match: re.Match, page: Page) -> etree.Element:
        url: str = match.group("url")
        url_no_params, *params = url.split("?")
        product_id, *md_release_id = url_no_params.rstrip("/").split("/")

        if len(md_release_id) > 1:
            raise ValueError(
                f"Too many '/' in the {match}, {md_release_id=}\nFile: {page.file.src_uri}"
            )

        if md_release_id:
            short_release_id = md_release_id[0]
        else:
            short_release_id = None
            meta_tags = page.meta.get("tags") or []
            for tag in meta_tags:
                if tag.startswith("SAP S/4HANA"):
                    short_release_id = tag.replace("SAP S/4HANA", "", 1).strip().replace(" ", "_")
                    break

        if not short_release_id:
            raise RuntimeError(
                f"Could not find short_release_id for the {match}"
                "\nThe issue could be a lack of 'tags' or a typo"
                f"\nFile: {page.file.src_uri}"
            )

        fal_release = FAL_RELEASE_MAPPING[short_release_id]
        href = f"https://fioriappslibrary.hana.ondemand.com/sap/fix/externalViewer/#/detail/Apps(%27{product_id}%27)/{fal_release}"

        el = etree.Element("a")
        el.set("href", href)
        el.set("target", "_blank")
        el.text = md_util.AtomicString(product_id)

        return el


# endregion

# region Constants

PLUGIN_NAME: str = "custom_auto_links"
"""Name of this plugin. Used in logging."""

LOG: PrefixedLogger = PrefixedLogger(
    PLUGIN_NAME, logging.getLogger(f"mkdocs.plugins.{PLUGIN_NAME}")
)
"""Logger instance for this plugin."""

FAL_RELEASE_MAPPING = {
    "1709": "S9OP",
    "1709_FPS01": "S10OP",
    "1709_FPS02": "S11OP",
    "1809": "S12OP",
    "1809_FPS01": "S13OP",
    "1809_FPS02": "S14OP",
    "1909": "S15OP",
    "1909_FPS01": "S16OP",
    "1909_FPS02": "S17OP",
    "2020": "S18OP",
    "2020_FPS01": "S19OP",
    "2020_FPS02": "S20OP",
    "2021": "S21OP",
    "2021_FPS01": "S22OP",
    "2021_FPS02": "S23OP",
    "2022": "S24OP",
    "2022_FPS01": "S25OP",
    "2022_FPS02": "S26OP",
    "2023": "S27OP",
    "2023_FPS01": "S28OP",
    "2023_FPS02": "S29OP",
}
"""Short release_id to actual URL release_id"""

# endregion

import logging
import os
from pathlib import Path

from mkdocs.config.defaults import MkDocsConfig
from mkdocs.plugins import BasePlugin, PrefixedLogger, event_priority
from mkdocs.structure.files import Files
from mkdocs.structure.pages import Page

from .config import CustomCallToActionSectionsConfig


class CustomCallToActionSectionsPlugin(BasePlugin[CustomCallToActionSectionsConfig]):

    def __init__(self) -> None:

        self.sanitized_paths: Path = []
        self.sanitized_target: Path = None

    def on_config(self, config: MkDocsConfig) -> MkDocsConfig | None:
        """Sanitize prefixes for later usage"""

        self.sanitized_paths.clear()
        docs_dir = Path(config.docs_dir)
        docs_dir_prefix = docs_dir.name + os.sep

        def sanitize_path(path: str) -> Path:
            path: str = path.replace("/", os.sep)
            if path.startswith(docs_dir_prefix):
                path = path.replace(docs_dir_prefix, "", 1)
            return docs_dir / path

        for path in self.config.paths:
            self.sanitized_paths.append(sanitize_path(path))
            LOG.debug(f"Added prefix: {self.sanitized_paths[-1]}")

        self.sanitized_target = sanitize_path(self.config.target)

        LOG.info("Sanitized paths and target")

    def on_page_markdown(
        self, markdown: str, /, *, page: Page, config: MkDocsConfig, files: Files
    ) -> str | None:
        """Add the section to a file file"""

        for path in self.sanitized_paths:
            if path.is_file() and page.file.abs_src_path == str(path):
                break
            if page.file.abs_src_path.startswith(str(path)):
                break
        else:
            return

        relative_target: str = self.sanitized_target.relative_to(
            Path(page.file.abs_src_path).parent, walk_up=True
        ).as_posix()

        section_template = ""
        if self.config.variant == "title_and_cta":
            section_template = TITLE_AND_CTA_TEMPLATE
        else:
            LOG.error(f"Not supported setting {self.config.variant=}")

        section = section_template.format(
            title=self.config.title,
            cta=self.config.cta,
            target=relative_target,
        )

        if self.config.append_at == "end":
            markdown += "\n\n" + section
        elif self.config.append_at == "start":
            # TODO Fix h1 tag handling
            LOG.warning("H1 handling is not done")
            markdown = section + "\n\n" + markdown
        else:
            LOG.error(f"Not supported setting {self.config.append_at=}")

        return markdown


# region Constants

PLUGIN_NAME: str = "custom_cta_sections"
"""Name of this plugin. Used in logging."""

LOG: PrefixedLogger = PrefixedLogger(
    PLUGIN_NAME, logging.getLogger(f"mkdocs.plugins.{PLUGIN_NAME}")
)
"""Logger instance for this plugins."""

TITLE_AND_CTA_TEMPLATE: str = (
    """
<div class="nype-cta" markdown>
<div class="nype-cta-title" markdown>{title}</div>
<div class="nype-cta-description" markdown>[{cta}]({target})</div>
</div>
""".strip()
)

# endregion

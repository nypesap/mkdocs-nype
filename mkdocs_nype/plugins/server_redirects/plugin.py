import logging
from pathlib import Path

from jinja2 import Environment
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.plugins import BasePlugin, PrefixedLogger
from mkdocs.structure.files import Files

from .config import ServerRedirectsConfig


class ServerRedirectsPlugin(BasePlugin[ServerRedirectsConfig]):

    def __init__(self) -> None:

        self.redirects_plugin = None
        self.output_redirects: dict[str, str] = {}

    def on_config(self, config: MkDocsConfig) -> MkDocsConfig | None:

        # Clear data from previous build
        self.redirects_plugin = None
        self.output_redirects.clear()

        # Find redirects plugin
        for name, instance in config.plugins.items():
            if name.split()[0].split("/")[-1] == "redirects":
                self.redirects_plugin = instance
                break

        # Check if there is anything to process
        redirect_maps = {}
        if self.redirects_plugin:
            redirect_maps = self.redirects_plugin.config.get("redirect_maps")

        if redirect_maps or self.config.raw_redirects:
            LOG.info("server-side redirects will be created")

    def on_env(
        self, env: Environment, /, *, config: MkDocsConfig, files: Files
    ) -> Environment | None:
        """Create the server redirects here, to allow other plugins to inject them before on_env"""

        if not config.use_directory_urls:
            LOG.warning("non-directory paths are not supported")
            return

        if self.config.raw_redirects:
            self.output_redirects.update(self.config.raw_redirects)

        redirect_maps = {}
        if self.redirects_plugin:
            redirect_maps = self.redirects_plugin.config.get("redirect_maps") or {}

        for old, new in redirect_maps.items():
            old_file = files.get_file_from_path(old)
            new_file = files.get_file_from_path(new)

            if new_file is None:
                LOG.warning(f"New path {new} couldn't be found. Skipping redirect creation")
                continue
            else:
                new_url = f'/{new_file.url.lstrip("./")}'

            if old_file:
                LOG.warning(
                    f"Old path {old} exists and will be overridden by the redirect to {new}"
                )
                old_url = f'/{old_file.url.lstrip("./")}'
            else:
                old_url = self.convert_filepath_to_url(old)

            if new_url in self.output_redirects.keys() or old_url in self.output_redirects.values():
                LOG.warning(f"Redirection chain detected with {old} -> {new}")

            if old_url and new_url:
                self.output_redirects[old_url] = new_url

    def convert_filepath_to_url(self, filepath: str):
        """Mainly used for the old non-existent file, as we take the file.url for existing files"""

        filepath: str = filepath.strip().strip("/")

        if filepath.lower() in ["index.md", "readme.md"]:
            path = ""
        elif filepath.lower().endswith(("/index.md", "/readme.md")):
            path = "/".join(filepath.split("/")[:-1]) + "/"
        elif filepath.endswith(".md") and filepath.count(".md") == 1:
            path = filepath.replace(".md", "/")
        else:
            LOG.warning(f"Filepath {filepath} could not be resolved to url")
            return ""

        return "/" + path

    def on_post_build(self, *, config: MkDocsConfig) -> None:
        """Save the file after the build"""

        if self.config.backend == "nginx":
            self.save_nginx(config)
        else:
            raise NotImplementedError(f"{self.config.backend} backend not supported")

    def save_nginx(self, config: MkDocsConfig):

        lines: list[str] = []

        for old, new in self.output_redirects.items():
            lines.append(f"rewrite {old} {new} permanent;")

        output_path = self.config.output_path.format(site_dir=config.site_dir)

        Path(output_path).write_text("\n".join(lines))


PLUGIN_NAME: str = "server_redirects"
"""Name of the plugin"""

LOG: PrefixedLogger = PrefixedLogger(
    PLUGIN_NAME, logging.getLogger(f"mkdocs.plugins.{PLUGIN_NAME}")
)
"""Logger instance for this plugin."""

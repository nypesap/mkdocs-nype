"""MkDocs plugin to convert images to WebP format

This plugin converts images concurrently and recursively to not block the main thread and injects the
web image path during Markdown path validation / resolution to not parse HTML output with regex.

Parts adapted based on:
- https://github.com/mur4d1n-lib/mkdocs-images-to-webp by mur4d1n (MIT)
- https://github.com/squidfunk/mkdocs-material/tree/master/material/plugins/social by squidfunk (MIT)
- https://gitlab.com/Shoun2137/ztexipy by Shoun2137 (GPLv3)

MIT License Kamil Krzyśków (HRY) for Nype (npe.cm) and Fiori Tracker (fioritracker.org)
"""

import json
import logging
import os
import shutil
from concurrent.futures import Future, ThreadPoolExecutor, thread
from pathlib import Path
from urllib.parse import urlsplit

from mkdocs.plugins import BasePlugin, PrefixedLogger, event_priority
from mkdocs.structure import pages
from mkdocs.structure.files import File
from PIL import Image

from .config import WebpImagesConfig


class WebpImagesPlugin(BasePlugin[WebpImagesConfig]):

    def __init__(self):
        self.executor: ThreadPoolExecutor = None
        self.promises: list[Future] = []

        self.extensions: list[str] = None
        self.old_new_webp_map: dict[str, str] = {}
        self.old_file_map: dict[str, File] = {}

        self.cache_base: Path = None
        self.cache_image_base: Path = None
        self.cached_mapping_file: Path = None
        self.site_dir_path: Path = None

    def on_config(self, config):
        if self.executor is None:
            self.executor = ThreadPoolExecutor(max_workers=self.config.workers)

        assert self.config.extensions, "config.extensions strings can't be empty"

        if self.extensions is None and "," in self.config.extensions:
            self.extensions = []
            for ext in self.config.extensions.split(","):
                ext = "." + ext.lstrip(".").strip().lower()
                self.extensions.append(ext)

        assert self.extensions, "file extensions weren't loaded"

        # Clear between server runs because images could change
        self.old_new_webp_map.clear()
        self.old_file_map.clear()
        self.promises.clear()

        # Output directory
        self.site_dir_path = Path(config.site_dir)

        # Configure cache
        if self.config.cache:
            lossless: str = "lossless-" if self.config.lossless else ""
            self.cache_base = Path(config.config_file_path).parent / self.config.cache_dir
            self.cached_mapping_file = self.cache_base / "map.json"

            self.cache_image_base = self.cache_base / "images" / f"{lossless}{self.config.quality}"

        # Wrap the path resolution logic to easily proxy webp files
        pages._RelativePathTreeprocessor.path_to_url = wrap_path_to_url(
            pages._RelativePathTreeprocessor.path_to_url, extensions=self.extensions
        )

    # Allow to inject files with other plugins
    @event_priority(-25)
    def on_files(self, files, /, *, config):
        # Gather all conversion paths
        for file in list(files):
            path: Path = Path(file.src_path)
            if path.suffix.lower() not in self.extensions:
                continue

            old: str = path.as_posix()
            new: str = path.with_suffix(".webp").as_posix()

            # Skip if sibling webp exists
            if files.get_file_from_path(new):
                continue

            # Store posix relative paths for cache to be OS agnostic
            self.old_new_webp_map[old] = new

            # Store file separately, because we remove the old files
            self.old_file_map[old] = file

            # TODO There was an attempt at using files.remove(file) and files.append(File.generated)
            # to directly target the .webp files inside wrap_path_to_url, but the images are created
            # concurrently, so they're often not ready before Markdown processing for being copied.
            # One solution could be to move the future.result() from on_post_build to on_env, but this
            # would likely impact the UX performance more than removing the old files in on_post_build.
            # files.remove(file)
            # files.append(File.generated(config, new, abs_src_path=str(self.site_dir_path / new)))

        # Load cached mapping to prevent processing the
        cached_mapping: dict[str, str] = {}
        if self.config.cache:
            if self.cached_mapping_file.exists():
                cached_mapping.update(
                    json.loads(self.cached_mapping_file.read_text(encoding="utf-8"))
                )

        # Remove obsolete cached files
        for old, obsolete_new in cached_mapping.items():
            if old in self.old_new_webp_map:
                continue
            obsolete_cached_file = self.cache_image_base / obsolete_new
            if obsolete_cached_file.exists():
                obsolete_cached_file.unlink()

        for old, new in self.old_new_webp_map.items():
            src: str = self.old_file_map[old].abs_src_path
            target = self.site_dir_path / new
            cached_target = (self.cache_image_base / new) if self.config.cache else None
            self.promises.append(
                self.executor.submit(self._convert_image, src, target, cached_target)
            )

    def _convert_image(self, src: str, target: Path, cached_target: Path | None):
        target.parent.mkdir(parents=True, exist_ok=True)

        if cached_target and cached_target.exists():
            shutil.copyfile(cached_target, target)
            return

        with Image.open(src) as image:
            image.save(target, lossless=self.config.lossless, quality=self.config.quality)

        if cached_target:
            cached_target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(target, cached_target)

    def on_post_build(self, *, config):
        for promise in self.promises:
            try:
                promise.result(timeout=2)
            except Exception as error:
                self.executor.shutdown(wait=False, cancel_futures=True)
                self.executor._threads.clear()
                thread._threads_queues.clear()
                raise

        LOG.info(f"Processed {len(self.promises)} WebP conversions")

        # Clean the old images after the build to not copy them for deployment
        # TODO See note in on_files
        for file in self.old_file_map.values():
            os.remove(file.abs_dest_path)

        if self.config.cache:
            with open(self.cached_mapping_file, "w", encoding="utf-8") as file:
                json.dump(self.old_new_webp_map, file, sort_keys=True, ensure_ascii=False, indent=2)

    def on_shutdown(self):
        if self.executor is not None:
            self.executor.shutdown(wait=False, cancel_futures=True)


def wrap_path_to_url(func, *, extensions):

    if func.__name__ == "wrapper":
        return func

    extensions = tuple(extensions)

    def wrapper(self, url: str):
        if url.endswith(extensions):
            scheme, netloc, path, query, anchor = urlsplit(url)
            # Hack the output to point at the converted file
            if not (scheme or netloc):
                return func(self, url).rsplit(".", maxsplit=1)[0] + ".webp"

        return func(self, url)

    return wrapper


PLUGIN_NAME: str = "webp_images"
"""Name of the plugin"""

LOG: PrefixedLogger = PrefixedLogger(
    PLUGIN_NAME, logging.getLogger(f"mkdocs.plugins.{PLUGIN_NAME}")
)
"""Logger instance for this plugin."""

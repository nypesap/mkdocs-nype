"""MkDocs plugin to convert images to WebP format

This plugin converts images concurrently and recursively to not block the main thread and injects the
web image path during Markdown path validation / resolution to not parse HTML output with regex.

Parts adapted based on:
- https://github.com/mur4d1n-lib/mkdocs-images-to-webp by mur4d1n (MIT)
- https://github.com/squidfunk/mkdocs-material/tree/master/material/plugins/social by squidfunk (MIT)
- https://gitlab.com/Shoun2137/ztexipy by Shoun2137 (GPLv3)

MIT License Kamil Krzyśków (HRY) for Nype (npe.cm) and Fiori Tracker (fioritracker.org)
"""

import hashlib
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
from mkdocs.utils import templates
from PIL import Image

try:
    from jinja2 import pass_context as contextfilter  # type: ignore
except ImportError:
    from jinja2 import contextfilter  # type: ignore

from .config import WebpImagesConfig


class WebpImagesPlugin(BasePlugin[WebpImagesConfig]):

    def __init__(self):
        self.executor: ThreadPoolExecutor = None
        self.promises: list[Future] = []

        self.extensions: list[str] = None
        self.old_file_map: dict[str, File] = {}

        self.cache_index: dict[str, str] = {}
        self.processed_images: set[str] = set()
        self.cache_index_file: Path = None

        self.cache_base: Path = None
        self.cache_image_base: Path = None
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
        self.cache_index.clear()
        self.processed_images.clear()
        self.old_file_map.clear()
        self.promises.clear()

        # Output directory
        self.site_dir_path = Path(config.site_dir)

        # Configure cache
        if self.config.cache:
            lossless: str = "lossless-" if self.config.lossless else ""
            self.cache_base = Path(config.config_file_path).parent / self.config.cache_dir
            self.cache_index_file = self.cache_base / "index.json"
            self.cache_image_base = self.cache_base / "images" / f"{lossless}{self.config.quality}"

        # Wrap the path resolution logic to easily proxy webp files
        pages._RelativePathTreeprocessor.path_to_url = wrap_path_to_url(
            pages._RelativePathTreeprocessor.path_to_url, extensions=self.extensions
        )
        templates.url_filter = wrap_url_filter(templates.url_filter, extensions=self.extensions)

    # Allow to inject files with other plugins
    @event_priority(-25)
    def on_files(self, files, /, *, config):
        # Load cached file hashes
        if self.config.cache and self.cache_index_file.exists():
            with open(self.cache_index_file, encoding="utf-8") as file:
                self.cache_index.update(json.load(file))

        ignore_processing: bool = (
            self.config.ignore_paths and self.config.ignore_mode == "processing"
        )

        # Gather all conversion paths
        for file in list(files):
            path: Path = Path(file.src_path)
            if path.suffix.lower() not in self.extensions:
                continue

            old: str = path.as_posix()
            new: str = path.with_suffix(".webp").as_posix()

            if ignore_processing and self.config.ignore_paths.match_file(old):
                LOG.debug(f"Skipped processing of '{old}'")
                continue

            # Skip if sibling webp exists
            if files.get_file_from_path(new):
                continue

            # Setup future promise
            src: str = file.abs_src_path
            dest = self.site_dir_path / new
            cached = (self.cache_image_base / new) if self.config.cache else None
            self.promises.append(self.executor.submit(self._convert_image, src, dest, cached, new))

            # Store file separately, because we remove the old files
            self.old_file_map[old] = file

            # TODO There was an attempt at using files.remove(file) and files.append(File.generated)
            # to directly target the .webp files inside wrap_path_to_url, but the images are created
            # concurrently, so they're often not ready before Markdown processing for being copied.
            # One solution could be to move the future.result() from on_post_build to on_env, but this
            # would likely impact the UX performance more than removing the old files in on_post_build.
            # files.remove(file)
            # files.append(File.generated(config, new, abs_src_path=str(self.site_dir_path / new)))

    def _convert_image(self, src: str, dest: Path, cache_dest: Path | None, name: str):
        dest.parent.mkdir(parents=True, exist_ok=True)
        self.processed_images.add(name)

        # Check if there is a cached entry for the given source hash
        cached_entry = False
        if cache_dest:
            image_hash = get_image_hash_key(src)
            cached_hash = self.cache_index.get(name)
            cached_entry = cached_hash == image_hash

        if cached_entry and cache_dest.exists():
            shutil.copyfile(cache_dest, dest)
            return

        with Image.open(src) as image:
            image.save(dest, lossless=self.config.lossless, quality=self.config.quality)

        if cache_dest:
            cache_dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(dest, cache_dest)
            self.cache_index[name] = image_hash

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
        ignore_deletion: bool = self.config.ignore_paths and self.config.ignore_mode == "deletion"
        for file in self.old_file_map.values():
            if ignore_deletion and self.config.ignore_paths.match_file(file.src_uri):
                LOG.debug(f"Skipped deletion of '{file.src_uri}'")
                continue
            os.remove(file.abs_dest_path)

        # Clean up obsolete caches
        for cached_path in list(self.cache_index):
            if cached_path in self.processed_images:
                continue

            self.cache_index.pop(cached_path)

            cached_path = self.cache_image_base / cached_path
            if cached_path.exists():
                LOG.debug(f"Removing '{cached_path}' from cache")
                cached_path.unlink()

        if self.config.cache:
            with open(self.cache_index_file, "w", encoding="utf-8") as file:
                json.dump(self.cache_index, file, ensure_ascii=False, indent=2)

    def on_shutdown(self):
        if self.executor is not None:
            self.executor.shutdown(wait=False, cancel_futures=True)


def get_image_hash_key(src: str, algo: str = "sha256", chunk_size=4096):
    """Load the file via stream and calculate hash during the process"""

    calculated_hash = hashlib.new(algo)

    with open(src, "rb") as file:
        for chunk in iter(lambda: file.read(chunk_size), b""):
            calculated_hash.update(chunk)

    return calculated_hash.hexdigest()


def wrap_path_to_url(func, *, extensions):
    """Wrap path_to_url logic to swap in WebP paths"""

    if func.__name__ == "wrapper":
        return func

    extensions = tuple(extensions)

    def wrapper(self, url: str):
        if url and url.endswith(extensions):
            scheme, netloc, path, query, anchor = urlsplit(url)
            # Hack the output to point at the converted file
            if not (scheme or netloc):
                return func(self, url).rsplit(".", maxsplit=1)[0] + ".webp"

        return func(self, url)

    return wrapper


def wrap_url_filter(func, *, extensions):
    """Wrap url_filter logic to swap in WebP paths"""

    if func.__name__ == "wrapper":
        return func

    extensions = tuple(extensions)

    @contextfilter
    def wrapper(context: templates.TemplateContext, value: str):
        if value and value.endswith(extensions):
            scheme, netloc, path, query, anchor = urlsplit(value)
            # Hack the output to point at the converted file
            if not (scheme or netloc):
                return func(context, value).rsplit(".", maxsplit=1)[0] + ".webp"

        return func(context, value)

    return wrapper


PLUGIN_NAME: str = "webp_images"
"""Name of the plugin"""

LOG: PrefixedLogger = PrefixedLogger(
    PLUGIN_NAME, logging.getLogger(f"mkdocs.plugins.{PLUGIN_NAME}")
)
"""Logger instance for this plugin."""

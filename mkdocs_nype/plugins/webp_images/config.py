import os

from mkdocs.config import Config
from mkdocs.config.config_options import Type


class WebpImagesConfig(Config):

    cache = Type(bool, default=True)
    """Enable cache flag"""

    cache_dir = Type(str, default=".cache/nype/webp_images")
    """Cache dir location to store converted images"""

    workers = Type(int, default=max(1, os.cpu_count() - 1))
    """Number of cores to use to process the images"""

    lossless = Type(bool, default=False)
    """Lossless flag for the writer"""

    quality = Type(int, default=80)
    """Quality level for the writer"""

    extensions = Type(str, default="jpg,jpeg,png,bmp")
    """Comma separated string list of image extensions to convert to WebP"""

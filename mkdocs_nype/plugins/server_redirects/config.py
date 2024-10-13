from mkdocs.config import Config
from mkdocs.config.config_options import Choice, DictOfItems, Type


class ServerRedirectsConfig(Config):

    backend = Choice(("nginx",), default="nginx")
    """Different backends might require other syntax etc."""

    raw_redirects = DictOfItems(Type(str), default={})
    """Mapping of raw redirects for the selected backend"""

    output_path = Type(str, default="{site_dir}/.nype-redirects.txt")
    """Output path for the file with the redirects"""

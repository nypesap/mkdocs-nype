from mkdocs.config import Config
from mkdocs.config.config_options import Type


class UniqueBlogDateConfig(Config):

    enabled = Type(bool, default=True)
    hook_blog_dir = Type(str)

    date_format = Type(str, default="yyyy MMMM")

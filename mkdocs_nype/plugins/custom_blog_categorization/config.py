from collections.abc import Callable

from material.plugins.blog.structure import View
from mkdocs.config import Config
from mkdocs.config.config_options import Optional, Type
from pymdownx.slugs import slugify


def get_custom_view() -> View:
    class Custom(View):
        pass

    return Custom


class CustomBlogCategorizationConfig(Config):

    enabled = Type(bool, default=True)
    hook_blog_dir = Type(str)

    # Based on the categories settings
    render_name = Type(str)
    code_name = Type(str)
    url_format = Type(str)
    slugify = Type(Callable, default=slugify(case="lower"))
    slugify_separator = Type(str, default="-")
    allowed_values = Type(list, default=[])
    toc = Optional(Type(bool))
    view_generator = Type(Callable, default=get_custom_view)

    # Settings for posts
    post_excerpt_max = Type(int, default=5)
    # post_url_max_industries = 1  # Currently has no effect, URLs require more overrides

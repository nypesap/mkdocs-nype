from typing import Any

from mkdocs.config import Config
from mkdocs.config.config_options import Choice, ListOfItems, Optional, Type


class SingleValueOrList(Type):
    """
    There is no mixed str/list[str] type provided by MkDocs, so this custom type allows for this
    """

    def run_validation(self, value: object):

        if isinstance(value, list):
            for v in value:
                super().run_validation(v)
        else:
            value = super().run_validation(value)

        return value


class SimilarBlogPostsConfig(Config):

    enabled = Type(bool, default=True)

    hook_blog_dir = SingleValueOrList(str)
    """A single value or list of matching blog_dir prefixes"""

    append_at = Choice(("start", "end"), default="end")
    title = Type(str)

    similarity_threshold = Type(float, default=0.32)
    """Float number between 0 and 1 to decide if the posts should be considered similar"""

    allow_other_categories = Type(bool, default=True)
    """If a given category doesn't have enough (max_shown) similar posts, show posts from other categories"""

    max_shown = Type(int, default=5)
    """Limit the number of shown posts"""

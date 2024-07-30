from mkdocs.config import Config
from mkdocs.config.config_options import Choice, ListOfItems, Optional, Type


class CustomCallToActionSectionsConfig(Config):

    enabled = Type(bool, default=True)

    paths = ListOfItems(Type(str))
    """List of string relative paths to directories or files. Can start with docs/, but don't have to."""

    append_at = Choice(("start", "end"), default="end")
    cta = Type(str)
    target = Type(str)
    title = Type(str)
    variant = Choice(("title_and_cta",), default="title_and_cta")

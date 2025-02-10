from mkdocs.config import Config
from mkdocs.config.config_options import Choice, ListOfItems, Optional, Type


class CustomCallToActionSectionsConfig(Config):
    """
    ```yaml title="Example config"
    - custom_cta_sections:
        title: Need something similar?
        cta: ':fontawesome-solid-handshake: Get a quote'
        target: contact.md
        paths:
        - docs/projects/posts
    ```
    """

    enabled = Type(bool, default=True)

    paths = ListOfItems(Type(str))
    """List of string relative paths to directories or files. Can start with docs/, but don't have to."""

    append_at = Choice(("start", "end"), default="end")
    """Where to append the section"""

    cta = Type(str)
    """Call to Action prompt like `Buy Now`"""

    target = Type(str)
    """Target path of the CTA endpoint file"""

    title = Type(str)
    """Title of the CTA section"""

    variant = Choice(("title_and_cta",), default="title_and_cta")
    """Variant choice"""

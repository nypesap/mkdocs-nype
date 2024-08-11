from mkdocs.config import Config
from mkdocs.config.config_options import Type


class OnlyBlogNavConfig(Config):

    enabled = Type(bool, default=True)
    hook_blog_dir = Type(str)

    exclude_blog_from_nav = Type(bool, default=False)
    """Blog navigation will be only shown after navigating to it, not on other pages"""

    material_navigation_expand = Type(bool, default=True)
    """Enable the navigation.expand feature"""

"""mkdocs-material extension module

Works through being invoked from the mkdocs-nype __init__.py file
before the mkdocs-material plugins get to load etc.

In some cases, mkdocs-material plugins lack configurability and typically 
this issue is solved by adding another plugin with its own configuration 
that later overrides stuff during the MkDocs event loop.

However, some of those cases don't make much sense as a separate plugin with 
its own event loop, so this module aims to add those micro adjustments.

1. Extend the blog config class to be able to configure more options.
2. Monkey-patch some events to add logic before or after their execution. 

MIT License 2024 Kamil Krzyśków (HRY) for Nype (npe.cm)
"""

from material.plugins.blog import config as blog_config
from material.plugins.blog.structure import View
from mkdocs.config.base import Config
from mkdocs.config.config_options import Choice, Deprecated, Optional, Type


def extend_blog():
    """
    This function must be executed before the BlogPlugin class is created
    and loaded into "Python memory" via some other "import"
    """

    blog_config.BlogConfig = BlogConfig

    # After modifying the config, import BlogPlugin to make further changes
    from material.plugins.blog import plugin as blog_plugin

    blog_plugin.BlogPlugin.on_page_context = wrap_blog_on_page_context(
        blog_plugin.BlogPlugin.on_page_context
    )


def wrap_blog_on_page_context(func):

    def extended(self, context, *, page, config, nav):

        view = self._resolve_original(page)
        blog_view = view in self._resolve_views(self.blog)
        blog_post = page in self.blog.posts

        result = func(self, context, page=page, config=config, nav=nav)

        # Pass on the extended config options to the template context
        if blog_view or blog_post:
            context["hide_read_more"] = self.config.hide_read_more
            context["hide_post_metadata"] = self.config.hide_post_metadata

        return result

    return extended


class BlogConfig(blog_config.BlogConfig):
    """Default values of the new options should match standard mkdocs-material behaviour"""

    hide_read_more = Type(bool, default=False)
    """
    Used later in templates to decide if the blog Views should show the read
    more link for Excerpts
    """

    hide_post_metadata = Type(bool, default=False)
    """
    Used later in templates to decide if the blog Views should show the metadata
    of the post, like the date and categories
    """

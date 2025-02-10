"""mkdocs-material extension module

Works through being invoked from the mkdocs-nype `__init__.py` file
before the mkdocs-material plugins get to load etc.

In some cases, mkdocs-material plugins lack configurability and typically
this issue is solved by adding another plugin with its own configuration
that later overrides stuff during the MkDocs event loop.

However, some of those cases don't make much sense as a separate plugin with
its own event loop, so this module aims to add those micro adjustments.

1. Extend the `BlogConfig` class to be able to configure more options.
2. Monkey-patch some events to add logic before or after their execution to use the new options.

MIT License 2024 Kamil Krzyśków (HRY) for Nype (npe.cm)
"""

from material.plugins.blog import config as blog_config
from material.plugins.blog.structure import Archive, Category, View
from mkdocs.config.base import Config
from mkdocs.config.config_options import Choice, Deprecated, DictOfItems, Optional, Type
from mkdocs.exceptions import PluginError
from mkdocs.plugins import event_priority


def extend_blog():
    """
    This function must be executed before the `BlogPlugin` class is created
    and loaded into "MkDocs memory" via some other "import" during Plugin load
    """

    blog_config.BlogConfig = BlogConfig

    # After modifying the config, import BlogPlugin to make further changes
    from material.plugins.blog import plugin as blog_plugin

    blog_plugin.BlogPlugin.on_config = wrap_blog_on_config(blog_plugin.BlogPlugin.on_config)
    blog_plugin.BlogPlugin.on_files = wrap_blog_on_files(blog_plugin.BlogPlugin.on_files)
    blog_plugin.BlogPlugin.on_page_markdown = wrap_blog_on_page_markdown(
        blog_plugin.BlogPlugin.on_page_markdown
    )
    blog_plugin.BlogPlugin.on_page_context = wrap_blog_on_page_context(
        blog_plugin.BlogPlugin.on_page_context
    )


def wrap_blog_on_config(func):

    def extended(self, config):

        result = func(self, config)

        blog_cards = self.config.blog_cards
        if blog_cards.startswith("index-grouped") and not self.config.categories_allowed:
            raise PluginError(
                f"blog_cards set to {blog_cards} also requires to set 'categories_allowed'"
            )

        return result

    return extended


def wrap_blog_on_files(func):

    @event_priority(-50)
    def extended(self, files, *, config):

        result = func(self, files, config=config)

        # Prepare category -> url map to allow to set link for categories within index-grouped
        self.config.categories_url_map = {}

        for category in self.config.categories_allowed:
            path = self._format_path_for_category(category)
            file = files.get_file_from_path(path)
            if not file:
                continue

            self.config.categories_url_map[category] = file.url

        return result

    return extended


def wrap_blog_on_page_markdown(func):

    @event_priority(-50)
    def extended(self, markdown: str, /, *, page, config, files):

        view = self._resolve_original(page)
        blog_view = view in self._resolve_views(self.blog)

        result = func(self, markdown, page=page, config=config, files=files)

        # Changes only for the Blog index root View
        if view is self.blog:
            if self.config.blog_cards == "index":
                view.meta["template"] = "blog-cards.html"
            elif self.config.blog_cards.startswith("index-grouped"):
                view.meta["template"] = "blog-cards-grouped.html"

        # Changes for all Views except for the Blog index root
        if blog_view and view is not self.blog:
            if not isinstance(view, Archive) and self.config.blog_cards != "off":
                blog_card_icons = self.config.blog_card_icons
                blog_card_icon = blog_card_icons.get(view.title, blog_card_icons.get("_default"))
                if not blog_card_icon:
                    blog_card_icon = "material/file-document"

                view.meta["icon"] = blog_card_icon

        # Changes for all Views which belong to this Blog
        if blog_view:
            if self.config.blog_cards == "all" or (
                view is not self.blog and self.config.blog_cards.endswith("+all")
            ):
                view.meta["template"] = "blog-cards.html"

        return result

    return extended


def wrap_blog_on_page_context(func):

    @event_priority(-100)
    def extended(self, context, *, page, config, nav):

        view = self._resolve_original(page)
        blog_view = view in self._resolve_views(self.blog)
        blog_post = page in self.blog.posts

        result = func(self, context, page=page, config=config, nav=nav)

        # Pass on the extended config options to the template context
        if blog_view or blog_post:
            context["hide_read_more"] = self.config.hide_read_more
            context["hide_post_metadata"] = self.config.hide_post_metadata

            if self.config.blog_cards != "off":

                context["blog_cards"] = self.config.blog_cards
                context["blog_card_continues"] = self.config.blog_card_continues
                context["blog_card_icons"] = self.config.blog_card_icons

                if isinstance(view, Category):
                    context["blog_card_category_view"] = view.title

                context["blog_categories_allowed"] = self.config.categories_allowed
                context["blog_categories_url_map"] = self.config.categories_url_map

        return result

    return extended


INDEX_VARIANTS = (
    "index",
    "index-grouped",
    "index-grouped-combo-a",
    "index-grouped-combo-b",
)
"""All of the index-only display variants"""

INDEX_CARDS_WITH_CARD_CATEGORIES = tuple([f"{var}+all" for var in INDEX_VARIANTS])
"""All of the index display variants + normal cards all"""


class BlogConfig(blog_config.BlogConfig):
    """Default values of the new options should match standard mkdocs-material behaviour"""

    hide_read_more = Type(bool, default=False)
    """
    Used later in templates to decide if the blog `View`s should show the read
    more link for `Excerpt`s
    """

    hide_post_metadata = Type(bool, default=False)
    """
    Used later in templates to decide if the blog Views should show the metadata
    of the post, like the date and categories
    """

    blog_cards = Choice(
        (
            "off",  # Turned off
            *INDEX_VARIANTS,
            "all",  # Default cards for both index and category pages
            *INDEX_CARDS_WITH_CARD_CATEGORIES,
        ),
        default="off",
    )
    """
    Toggle the blog_cards to show on all `View`s or only the index page
    """

    blog_card_continues = DictOfItems(Type(str), default={})
    """
    Mapping of category names to Continue Reading messages used in templates for
    the blog post cards. `_default` key is reserved for the Default value.
    """

    blog_card_icons = DictOfItems(Type(str), default={})
    """
    Mapping of category names to icon paths used in templates for the blog post
    cards. `_default` key is reserved for the Default value.
    """

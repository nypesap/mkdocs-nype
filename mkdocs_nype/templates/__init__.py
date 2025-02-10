"""Python representation of the `mkdocs_theme.yml` file

These data classes aren't used directly, just used as easy to read representation of all options.
"""

from typing import Any


class ThemeConfig:

    extends: str = "material"
    """This theme extends Material for MkDocs"""

    nype_config: "NypeConfig | dict" = {}
    """Global Nype theme configuration. Can be updated in `page.meta.nype_config` per page."""

    is_serve: bool
    """Global container for local serve status, can be set in `mkdocs.yml`, but there is a fallback in `nype-base.html`"""


class NypeConfig(dict):
    """nype_config is a dict and is used to separate configuration for the theme from the rest of the project.

    Some values can be set globally in `mkdocs.yml` and some only locally in `page.meta`.
    Some global values can be overriden via `page.meta` or hooks.

    So there are 3 kinds of `nype_config`:

    - theme-level, fetched from `mkdocs.yml.theme.nype_config`,
    - meta-level, fetched from `page.meta.nype_config`,
    - page-level, merged from adding `theme` + `meta` into one,
      overriding options with the latter when needed

    ```yaml
    theme:
      name: nype
      nype_config:
        js:
          some_value: true
        old_prefix: V2020
    ```

    ```yaml
    ---
    nype_config:
      js_include: old_prefix
    ---
    # Page title
    ```
    """

    blog_card_: str
    """Multiple `blog_card_` prefixed variables to control the `blog-cards` templates

    - `blog_card_icon` - SVG icon path to use for a given card, defaults to `material/file-document`
    - `blog_card_title` - Title of the blog card with format
    - `blog_card_description` - Description of the blog card with format 
    
    !!! info "page-level setting"
    """

    container_css: str
    """Whitespace separated names of `nype-{name}` CSS style classes that will influence the container.
    Refer to the `nype-main.css` file for all available options.

    !!! info "meta-level setting"
    
    E.g.: `container_css: 'hide-h1 content-only'`
    """

    css_include: str
    """Whitespace separated names of CSS files that will be included before `nype-main.css` and project `extra.css`.
    Refer to the `templates/assets/stylesheets` directory for all available files.
    
    !!! info "meta-level setting"

    E.g.: `css_include: 'neoteroi'`
    """

    discord_: str
    """Multiple `discord_` prefixed variables used in the `discord_invite.md` macro.
    
    - `js.discord_invite` - invite link passed to JavaScript
    - `discord_header` - invite card header
    - `discord_logo` - invite card logo
    - `discord_title` - invite card title
    - `discord_button` - invite button text

    !!! info "meta-level setting"
    
    """

    exclude_via_robots: str
    """Multi-line string with paths to exclude via robots.txt file
    
    !!! info "theme-level setting"
    """

    footer_nav: list[str | dict[str, str]]
    """Paths to files to include in the footer nav / dict with title and path.

    !!! info "theme-level setting"
    
    ```json title="Default footer_nav set in nype_tweaks"
    {
        "Contact": "contact.md",
        "Impressum": "impressum.md",
        "Offer": "offer.md",
    }
    ```
    """

    giscus_: str
    """Multiple `giscus_` prefixed variables used in the `comments.html` template

    - `giscus_prefixes` - Whitespace seprated list of path prefixes to constrain the inclusion of the `comment.html` file
        
        E.g. `giscus_prefixes: blog/`

    - `giscus_category_name` - Name of the category taken from Giscus creator
    - `giscus_category_id` - Id of the category taken from Giscus creator
    - `giscus_repo_name` - Repository name taken from Giscus creator, defaults to `nypesap/nypesap.github.io`
    - `giscus_repo_id` - Repository id taken from Giscus creator, defaults to `MDEwOlJlcG9zaXRvcnkyNjYwNDcwNzM=`

        Default target is: https://github.com/nypesap/nypesap.github.io/discussions

    - `giscus_term` - Type of the way how the generated discussion title is resolved, omit to default to `pathname`
    - `giscus_light_theme` - Giscus light theme variant, defaults to `light`
    - `giscus_dark_theme` - Giscus dark theme variant, defaults to `transparent_dark`
    
    !!! info "page-level setting"
    """

    head_tags: list[dict[str, dict[str, str]]]
    """List of HTML tag objects, which will be rendered in HTML for a given page. Page-Meta only.

    !!! info "page-level setting"
    
    E.g.: `{ "name": "script", "attributes": { "src": "https://...", "defer": "" } }`
    """

    js: dict[str, Any]
    """Values that will be passed to JavaScript via HTML injection.
    
    `key: value`, pairs where `key` is a string, and value `Any` other value, however deeply nested dicts weren't tested.
    
    !!! info "page-level setting"

    E.g.: `contact_form_action_hex: https://form.endpoint.com`
    """

    js_include: str
    """Whitespace separated names of `non-js` keys that will be passed on to the `js` too.

    !!! info "meta-level setting"
    
    E.g.: `js_include: 'contact_form_action_hex contact_form_email_hex'`

    !!! question "Why not simply, set them in `js`?"
        To avoid polluting every page with not needed data, better expose the values to `js` only on certain pages.
    """

    more_favicons: bool
    """Enable more favicon metadata. Requires proper file setup. Refer to the `nype-base.html` template for details.
    
    !!! info "theme-level setting"
    """

    old_prefix: str
    """For 404 page, old prefix to redirect old links from if not found. Was used for V2020 of Fiori Tracker.
    
    !!! info "page-level setting"
    """

    required_js: dict[str, None]
    """Container to hold required js keys to be included in a page. It's a dict, because it's created inside templates,
    where set() is not available.
    
    Used in macros to enable check for added contact_form keys to not expose empty forms online without attached action.

    !!! info "page-level setting"
    """

    safari_mask_color: str
    """Hex color to fill in the additional Safari SVG icon, enabled with `more_favicons`
    
    !!! info "theme-level setting"
    """

"""Modify how mkdocstrings operates

1. Change processed markdown in mkdocstrings
2. Changes how Classes are filtered to not show PluginConfig Aliases

"""

from griffe import Alias
from mkdocs.plugins import event_priority
from mkdocstrings.handlers.base import BaseHandler
from mkdocstrings_handlers.python import rendering


@event_priority(100)
def on_config(config):

    BaseHandler.do_convert_markdown = wrap_do_convert_markdown(BaseHandler.do_convert_markdown)
    rendering.do_filter_objects = wrap_do_filter_objects(rendering.do_filter_objects)


def wrap_do_convert_markdown(func):

    def wrapper(self, text, *args, **kwargs):

        for old, new in REPLACE_MAP.items():
            text = text.replace(old, new)

        return func(self, text, *args, **kwargs)

    return wrapper


def wrap_do_filter_objects(func):

    def wrapper(objects_dictionary: dict, *args, **kwargs):
        for key, value in list(objects_dictionary.items()):
            # Assuming it's a PluginConfig class imported in a .plugin.py file
            # .config.py files are rendered separately, so this removes duplication
            if key.endswith("Config") and isinstance(value, Alias):
                plugin_key = key[: len(key) - len("Config")] + "Plugin"
                if plugin_key in objects_dictionary:
                    objects_dictionary.pop(key)

        return func(objects_dictionary, *args, **kwargs)

    return wrapper


REPLACE_MAP: dict[str, str] = {
    "(HRY)": "([HRY](https://github.com/kamilkrzyskow))",
    "(npe.cm)": "([npe.cm](https://npe.cm))",
    "(fioritracker.org)": "([fioritracker.org](https://fioritracker.org))",
    " `nype-main.css`": " [`nype-main.css`](https://github.com/nypesap/mkdocs-nype/blob/main/mkdocs_nype/templates/assets/stylesheets/nype-main.css)",
    " `nype-base.html`": " [`nype-base.html`](https://github.com/nypesap/mkdocs-nype/blob/main/mkdocs_nype/templates/nype-base.html)",
}


def _validate():
    for key, value in REPLACE_MAP.items():
        assert (
            key not in value
        ), f"To avoid deep replacement nesting during mkdocs serve, the {key=} can't be in the {value=}"


_validate()

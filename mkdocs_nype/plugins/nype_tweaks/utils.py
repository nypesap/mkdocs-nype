from pathlib import Path

from jinja2.loaders import FileSystemLoader

from ...utils import MACROS_INCLUDES_ROOT


class ServeMode:
    """Helps to track if serve runs again"""

    run_once = False
    """Toggle"""


def get_file_system_loader(value: str | list[str]):
    """Proxy function to get the Jinja2 FileSystemLoader with theme macros_includes"""

    if isinstance(value, str):
        value = [value]

    theme_includes = str(MACROS_INCLUDES_ROOT)

    if theme_includes not in value:
        value.append(theme_includes)

    return FileSystemLoader(value)

import base64
import string
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


def is_hex_string(text: str):
    """Check if strings are represented in hex digits. Doesn't support 0x notation."""

    # empty or None is False
    if not text:
        return False

    for char in text:
        if char not in string.hexdigits:
            return False

    return True


def obfuscate(text: str):
    """Turn plain text into base64 and obfuscate it as hex"""

    if is_hex_string(text):
        return text

    base64_encoded = base64.b64encode(text.encode()).decode()
    hex_data = "".join(format(ord(c), "02x") for c in base64_encoded)

    assert text == deobfuscate(hex_data)

    return hex_data


def deobfuscate(hex_text: str):
    """Turn hex back to string"""

    return base64.b64decode(bytes.fromhex(hex_text)).decode()

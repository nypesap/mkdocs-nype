import base64
import re
import string
from pathlib import Path
from xml.etree import ElementTree

from jinja2.loaders import FileSystemLoader
from material.plugins.blog.structure import Excerpt
from mkdocs.utils.templates import contextfilter

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

    if not isinstance(text, str):
        raise ValueError(
            f"HEX obfuscation is only avaialble for text strings not {type(text)}({text})"
        )

    # side-effect, but we want consistent results
    text = text.strip()

    if is_hex_string(text):
        return text

    base64_encoded = base64.b64encode(text.encode()).decode()
    hex_data = "".join(format(ord(c), "02x") for c in base64_encoded)

    assert text == deobfuscate(hex_data)

    return hex_data


def deobfuscate(hex_text: str):
    """Turn hex back to string"""

    return base64.b64decode(bytes.fromhex(hex_text)).decode()


def post_card_title(post: Excerpt):
    """Get the title from the HTML, as post.title can differ"""

    title_attr = "card_title"

    if hasattr(post, title_attr):
        return getattr(post, title_attr)

    pattern = r"<a\s+[^>]*>(.*?)</a>"
    match: re.Match = re.search(pattern, post.content)
    if not match:
        raise ValueError(
            f"The Excerpt for {post.post.file.src_uri} does not contain an anchor tag with the title"
        )

    title = match.group(1)

    setattr(post, title_attr, title)

    return title


def post_card_description(post: Excerpt):
    """Get the contents of the Excerpt after the H2 tag"""

    description_attr = "card_description"

    if hasattr(post, description_attr):
        return getattr(post, description_attr)

    parts = post.content.split("</h2>")
    if len(parts) != 2:
        raise ValueError(
            f"The Excerpt for {post.post.file.src_uri} does not contain a h2 closing tag"
        )

    description = parts[-1]

    setattr(post, description_attr, description)

    return description

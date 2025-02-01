"""MkDocs Nype theme, based on the Material for MkDocs theme.

This __init__.py file gets loaded by MkDocs before plugins are initialized.
Therefore, this is a good place to monkey-patch changes into the build process.

load_plugin_with_namespace patch:
Due to how themename/pluginname namespaces work to make using Nype projects more convenient
we change the logic of how namespaces are resolved. `pluginname` will be resolved in order:
-> `nype/pluginname` -> `material/pluginname` -> `pluginname`

run_validation_with_nype_injection patch:
Instead of manually setting and enabling a plugin, every project would benefit from an
automatically enabled plugin at runtime that does some kind of validation during the event
loop, or enable any recommended plugin markdown extension in each project.

material extensions:
Instead of configuring other plugins and overriding internals of mkdocs-material plugins
extend them before they're loaded into "Python memory"

MIT License 2024 Kamil Krzyśków (HRY) for Nype (npe.cm)
"""

import hashlib
import inspect
import logging
import re
from collections import Counter

import mkdocs
from mkdocs.config.base import ValidationError
from mkdocs.config.config_options import Plugins
from mkdocs.plugins import PrefixedLogger
from mkdocs.utils import CountHandler

from .extensions import material as material_extension

LOG: PrefixedLogger = PrefixedLogger("mkdocs_nype", logging.getLogger(f"mkdocs.themes.mkdocs_nype"))

issue_counter = CountHandler()
"""This is fetched in nype_tweaks to trigger --strict flag based on __init__.py"""

issue_counter.setLevel(logging.WARNING)
LOG.logger.addHandler(issue_counter)


def patch_plugin_loading():

    if not hasattr(Plugins, "load_plugin_with_namespace"):
        LOG.error(
            "MkDocs doesn't expose load_plugin_with_namespace anymore, plugin loading patch not applied"
        )
        return

    checksum = _get_checksum(inspect.getsource(Plugins.load_plugin_with_namespace))
    working = "3f62dfaf6be408fd756b9ad17ce0ffaa32a17edbdcd3841358f73e80a63ccbb2"

    if checksum != working:
        LOG.warning(
            "load_plugin_with_namespace function has different content than the previous patch"
        )

    Plugins.load_plugin_with_namespace = load_plugin_with_namespace
    LOG.info("load_plugin_with_namespace patch applied")


def load_plugin_with_namespace(self, name: str, config):
    """Adapted code from the MkDocs 1.6.0 repository"""

    if "/" in name:  # It's already specified with a namespace.
        # Special case: allow to explicitly skip namespaced loading:
        if name.startswith("/"):
            name = name[1:]
    else:
        # Attempt to load with prepended namespace for the current theme.
        if self.theme_key and self._config:
            current_theme = self._config[self.theme_key]
            if not isinstance(current_theme, str):
                current_theme = current_theme["name"]
            if current_theme:
                expanded_name = f"{current_theme}/{name}"
                material_name = f"material/{name}"  # Customization add material/ scope handling
                if expanded_name in self.installed_plugins:
                    name = expanded_name
                # Customization add material/ scope handling
                elif material_name in self.installed_plugins:
                    name = material_name

    return (name, self.load_plugin(name, config))


def patch_default_plugins_auto_load():
    if not hasattr(Plugins, "run_validation"):
        LOG.error(
            "MkDocs doesn't expose run_validation anymore, default plugin auto load patch not applied"
        )
        return

    checksum = _get_checksum(inspect.getsource(Plugins.run_validation))
    working = "67a796e20054cbea416d9e596b657e4f0437dee5790636fc4de90a8d4baa4996"

    if checksum != working:
        LOG.warning("run_validation function has different content than the previous patch")

    Plugins.run_validation = run_validation
    LOG.info("run_validation_with_nype_injection patch applied")


def run_validation(self, value: object) -> mkdocs.plugins.PluginCollection:
    """Adapted code from the MkDocs 1.6.0 repository"""

    if not isinstance(value, (list, tuple, dict)):
        raise ValidationError("Invalid Plugins configuration. Expected a list or dict.")

    if not isinstance(value, list):
        raise NotImplementedError("The injection was only implemented for list-based plugins")

    plugin_names = set()
    wanted_plugins: tuple[tuple[str]] = (("nype", "nype_tweaks"),)
    """Tuple of tuples with (scope, plugin_name). Scope can be None"""

    # self._parse_configs modifies the internals of `value`, so use it directly
    for entry in value:
        if isinstance(entry, str):
            plugin_names.add(entry)
        else:
            plugin_names.add(next(iter(entry)))

    for scope, name in wanted_plugins:
        variants = [name]
        if scope:
            variants.insert(0, f"{scope}/{name}")

        for variant in variants:
            if variant in plugin_names:
                break
        else:
            value.append(variants[0])

    self.plugins = mkdocs.plugins.PluginCollection()
    self._instance_counter = Counter()

    for name, cfg in self._parse_configs(value):
        self.load_plugin_with_namespace(name, cfg)

    return self.plugins


def _get_checksum(source: str) -> str:
    """Remove comments, spaces, turn lowercase to get a minified token and return a sha256 hash from it"""
    token = re.sub(
        pattern=r'""".*?"""',
        repl="",
        string="".join(
            map(
                lambda line: "".join(line.split("#")[0].split(" ")),
                source.strip().lower().split("\n"),
            )
        ),
        flags=re.IGNORECASE | re.MULTILINE,
    )
    return hashlib.sha256(token.encode(encoding="utf-8")).hexdigest()


if __name__ == "mkdocs_nype":
    patch_default_plugins_auto_load()
    patch_plugin_loading()
    material_extension.extend_blog()

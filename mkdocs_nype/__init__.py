"""MkDocs Nype theme, based on the Material for MkDocs theme.

This `__init__.py` file gets loaded by MkDocs before plugins are initialized.
Therefore, this is a good place to monkey-patch changes into the build process.

**Consider both `nype/` and `material/` namespaces when loading plugins**

Due to how `themename/pluginname` namespaces work to make using Nype projects more convenient
we change the logic of how namespaces are resolved. `pluginname` will be resolved in order:

1. `nype/pluginname`
2. `material/pluginname`
3. `pluginname`

**Inject predefined plugins for loading even when they're not in `mkdocs.yml`**

Instead of requiring to enable a plugin in a project `mkdocs.yml`, enable it by default.
This allows `nype_tweaks` to operate as a project manager for the entirety of the event loop.

**Extend Material theme plugins directly**

Instead of configuring other plugins and overriding internals of mkdocs-material plugins during
the event loop, extend them before they're loaded into "Python MkDocs memory". This allows to directly
modify how the PluginConfig is resolved, therefore allows to add options directly under the
extended plugin in `mkdocs.yml` instead of under another plugin.

MIT License 2024 Kamil Krzyśków (HRY) for Nype (npe.cm)
"""

import hashlib
import inspect
import logging
import os
import re
from collections import Counter
from dataclasses import dataclass

import mkdocs
from mkdocs.config.base import ValidationError
from mkdocs.config.config_options import Plugins
from mkdocs.plugins import PrefixedLogger
from mkdocs.utils import CountHandler

from .extensions import material as material_extension

LOG: PrefixedLogger = PrefixedLogger("mkdocs_nype", logging.getLogger(f"mkdocs.themes.mkdocs_nype"))

issue_counter = CountHandler()
"""This is fetched in `nype_tweaks` to trigger `--strict` flag based on `__init__.py`"""

issue_counter.setLevel(logging.WARNING)
LOG.logger.addHandler(issue_counter)


def patch_plugin_loading():
    """Monkey patches the `load_plugin_with_namespace` function after confirming that the hash is the same."""

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
    """Adapted code from the MkDocs 1.6.0 repository. Modification adds `material/pluginname` fallback."""

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
    """Monkey patches the `run_validation` function after confirming that the hash is the same."""

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
    """Adapted code from the MkDocs 1.6.0 repository. Modification adds `nype_tweaks` plugin when missing."""

    if not isinstance(value, (list, tuple, dict)):
        raise ValidationError("Invalid Plugins configuration. Expected a list or dict.")

    if not isinstance(value, list):
        raise NotImplementedError("The injection was only implemented for list-based plugins")

    plugin_map: dict[str, dict] = {}

    # self._parse_configs modifies the internals of `value`, so use it directly with references
    for i, entry in enumerate(value):
        if isinstance(entry, str):
            # side effect, change form to dict to override more easily later
            value[i] = {entry: {}}
            plugin_map[entry] = value[i][entry]
        else:
            plugin_map.update(entry)

    for wanted_plugin in WANTED_PLUGINS:
        name = wanted_plugin.name
        scope = wanted_plugin.scope
        config = wanted_plugin.config or {}

        variants = [name]
        if scope:
            variants.insert(0, f"{scope}/{name}")

        for variant in variants:
            if variant in plugin_map:
                # Override config as needed
                plugin_map[variant].update(config)
                LOG.info(f"Updated config for {variants[0]} plugin")
                break
        else:
            value.append({variants[0]: {**config}})
            LOG.info(f"Injected {variants[0]} plugin")

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


def _parse_env_flag(varname: str = "CI", default: bool = False) -> bool:
    """Parse environment variable as a flag for injected plugin config"""

    value: str = os.getenv(varname)

    if value is None:
        return default

    value = value.strip()

    if value.isnumeric():
        return bool(int(value))
    else:
        return value.lower() == "true"


@dataclass
class PluginEntry:
    """Used for injecting plugins"""

    name: str
    scope: str = None
    config: dict = None


WANTED_PLUGINS: tuple[PluginEntry] = (
    PluginEntry("nype_tweaks", scope="nype"),
    PluginEntry(
        "minify_html",
        config={
            "enabled": _parse_env_flag(),
            "keep_html_and_head_opening_tags": True,
            "keep_closing_tags": True,
        },
    ),
    PluginEntry("webp_images", scope="nype", config={"enabled": _parse_env_flag()}),
)
"""Tuple of wanted PluginEntries. Scope can be None. Config can be None to use defaults."""


if __name__ == "mkdocs_nype":
    patch_default_plugins_auto_load()
    patch_plugin_loading()
    material_extension.extend_blog()

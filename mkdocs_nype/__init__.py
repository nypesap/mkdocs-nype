"""MkDocs Nype theme, based on the Material for MkDocs theme.

This __init__.py file gets loaded by MkDocs before plugins are initialized.
Therefore, this is a good place to monkey-patch changes into the build process.

Due to how themename/pluginname namespaces work to make using Nype projects more convenient 
we change the logic of how namespaces are resolved. `pluginname` will be resolved in order:
-> `nype/pluginname` -> `material/pluginname` -> `pluginname`

MIT License 2024 Kamil Krzyśków (HRY) for Nype (npe.cm)
"""

import logging

from mkdocs.plugins import PrefixedLogger

LOG: PrefixedLogger = PrefixedLogger("mkdocs_nype", logging.getLogger(f"mkdocs.themes.mkdocs_nype"))


def patch_plugin_loading():

    import hashlib
    import inspect

    from mkdocs.config.config_options import Plugins

    if not hasattr(Plugins, "load_plugin_with_namespace"):
        LOG.error(
            "MkDocs doesn't expose load_plugin_with_namespace anymore, plugin loading patch not applied"
        )
        return

    source = inspect.getsource(Plugins.load_plugin_with_namespace)

    # Remove comments, spaces, turn lowercase to get a minified token
    token = "".join(
        map(lambda line: "".join(line.split("#")[0].split(" ")), source.strip().lower().split("\n"))
    )
    checksum = hashlib.sha256(token.encode(encoding="utf-8")).hexdigest()
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


if __name__ == "mkdocs_nype":
    patch_plugin_loading()

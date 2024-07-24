"""MkDocs plugin made to allow to change the logo in the material/social plugin.

This plugin was formerly a hook:
- https://github.com/nypesap/nypesap.github.io/blob/9951b6669868c657874740c6a124213785441864/overrides/hooks/change_logo_for_social_cards.py

MIT License 2024 Kamil Krzyśków (HRY) for Nype (npe.cm)
"""

import inspect
import logging
from copy import deepcopy

from mkdocs.plugins import BasePlugin, PrefixedLogger, event_priority

from .config import CustomSocialLogoConfig

PLUGIN_NAME = "custom_social_logo"
LOG: PrefixedLogger = PrefixedLogger(
    PLUGIN_NAME, logging.getLogger(f"mkdocs.plugins.{PLUGIN_NAME}")
)


class CustomSocialLogoPlugin(BasePlugin[CustomSocialLogoConfig]):

    @event_priority(100)
    def on_config(self, config):

        from material.plugins.social.plugin import SocialPlugin

        # Skip if applied in mkdocs serev
        if SocialPlugin._load_logo.__name__ == "wrapper":
            return

        signature = "(self, config)"

        if str(inspect.signature(SocialPlugin._load_logo)) != signature:
            LOG.warning("function signature changed")
            return

        SocialPlugin._load_logo = load_logo_wrapper(SocialPlugin._load_logo, config.theme)


def load_logo_wrapper(func, theme):

    if func.__name__ == "wrapper":
        return func

    class DummyConfig: ...

    theme = deepcopy(theme)

    def wrapper(self, config):
        cfg = DummyConfig()
        cfg.theme = theme
        cfg.docs_dir = config.docs_dir
        cfg.theme["logo"] = "assets/images/social_logo.png"

        return func(self, cfg)

    return wrapper

from mkdocs.config import Config
from mkdocs.config.base import ConfigErrors, ConfigWarnings, ValidationError
from mkdocs.config.config_options import DictOfItems, ListOfItems, SubConfig, Type

SUPPORTED_PROTOCOLS = ("fal",)
"""Tuple of supported protocols"""


class FalProtocolExtras(Config):

    load_presets = Type(bool, default=True)
    """Load preset values like the releases"""

    releases_map = DictOfItems(Type((int, str)), default={})
    """Extra releases"""

    tags_map = DictOfItems(Type((int, str)), default={})
    """Extra tag handling"""

    fallback_id = Type((int, str), default="")
    """Fallback release id to use when not set in URL / tags"""

    def validate(self):
        failed, warnings = super().validate()

        def convert_values_to_str(mapping):
            for key, value in mapping.items():
                if isinstance(value, int):
                    mapping[key] = str(value)

        convert_values_to_str(self.releases_map)
        convert_values_to_str(self.tags_map)

        if isinstance(self.fallback_id, int):
            self.fallback_id = str(self.fallback_id)

        return failed, warnings


class CustomAutoLinksConfig(Config):

    fal = SubConfig(FalProtocolExtras, validate=True)
    """fal protocol extras"""


# This code was never used but works. Allows for runtime creation of the config schema.
# Doesn't autocomplete because of the runtime creation, so not practical for this use case.
#
# def extend_config(config: CustomAutoLinksConfig) -> CustomAutoLinksConfig:
#     protocol_extras = {
#         "fal": {
#             "load_presets": Type(bool, default=True),
#             "fallback_id": Type(str, default=""),
#             "releases": DictOfItems(Type(str), default={}),
#         }
#     }
#     """Template for the allowed protocol extras with their types"""

#     for name in protocol_extras:
#         if name not in SUPPORTED_PROTOCOLS:
#             raise ValidationError(f"Protocol not supported {name}")

#     # Extend the class dynamically with new attributes
#     for protocol, extras in protocol_extras.items():

#         if not extras:
#             continue

#         class ProtocolConfig(Config):
#             pass

#         for name, value in extras.items():
#             setattr(ProtocolConfig, name, value)

#         # Subclass needs to init again to go over the new attributes
#         ProtocolConfig.__init_subclass__()
#         setattr(config, protocol, SubConfig(ProtocolConfig, validate=True))

#     # Subclass needs to init again to go over the new attributes
#     config.__init_subclass__()

#     return config

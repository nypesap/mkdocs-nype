from pathlib import Path

import mkdocs_nype

THEME_ROOT: Path = Path(mkdocs_nype.__file__).parent
"""mkdocs_nype root directory"""

MACROS_INCLUDES_ROOT: Path = THEME_ROOT / "macros_includes"
"""mkdocs_nype/macros_includes directory"""

"""Generate the code reference pages. Adapted based on https://mkdocstrings.github.io/recipes/#automatic-code-reference-pages"""

from pathlib import Path

import mkdocs_gen_files
from mkdocs_gen_files.nav import Nav


def main():

    # Add manually created index.md file for navigation.indexes
    NAV["Index"] = Path("index.md").as_posix()

    for path in DOCS_TOP_LEVEL_PATH.rglob("*.md"):
        if path.name == "index.md":
            continue

        doc_path = path.relative_to(DOCS_TOP_LEVEL_PATH)
        parts = doc_path.with_suffix("").parts
        nav_label = list(map(process_nav_part, parts))

        NAV[nav_label] = doc_path.as_posix()

    for path in sorted(SRC.rglob("*.py")):
        content = path.read_text(encoding="utf-8").strip()
        if not content:
            continue

        module_path = path.relative_to(ROOT).with_suffix("")
        doc_path = path.relative_to(ROOT).with_suffix(".md")

        if doc_path.name.startswith("__"):
            doc_path = doc_path.parent / doc_path.name.replace("__", "")

        full_doc_path = Path(TOP_LEVEL_DIR, doc_path)

        parts = tuple(module_path.parts)

        # Set __init__ as index.md for navigation.indexes
        if parts[-1] == "__init__":
            parts = parts[:-1]
            if len(parts) != 1:
                doc_path = doc_path.with_name("index.md")
                full_doc_path = full_doc_path.with_name("index.md")
        # Empty __init__ files are skipped, so check other possible files
        elif parts[-1] == "plugin":
            init_sibling = path.with_name("__init__.py")
            assert init_sibling.exists()
            init_content = init_sibling.read_text(encoding="utf-8").strip()
            if not init_content:
                doc_path = doc_path.with_name("index.md")
                full_doc_path = full_doc_path.with_name("index.md")

        identifier = nav_label = ".".join(parts)
        assert identifier.strip()

        nav_label = nav_label.replace(f"{PACKAGE_NAME}.", "")
        if nav_label == PACKAGE_NAME:
            nav_label = "__init__"

        nav_label = nav_label.replace("__", "_\_")

        if "_\_" not in nav_label:
            nav_label = list(map(process_nav_part, nav_label.split(".")))
        elif "." not in nav_label:
            nav_label = ["Entry Points", nav_label]

        # Replace Plugin label with a combination of the previous part
        # Change browser history name for Plugin page
        if nav_label[-1] == "Plugin":
            nav_label[-1] = f"{nav_label[-2]} {nav_label[-1]}"

        NAV[nav_label] = doc_path.as_posix()

        with mkdocs_gen_files.open(full_doc_path, "w") as fd:
            # Change browser history name for Config page
            if nav_label[-1] == "Config":
                fd.write(f"---\n")
                fd.write(f"title: '{nav_label[-2]} {nav_label[-1]}'\n")
                fd.write(f"---\n")
            fd.write(f"::: {identifier}")

        mkdocs_gen_files.set_edit_path(full_doc_path, Path("..") / path.relative_to(ROOT))

    with mkdocs_gen_files.open(f"{TOP_LEVEL_DIR}/SUMMARY.md", "w") as nav_file:
        nav_file.writelines(NAV.build_literate_nav())


def process_nav_part(part: str):

    parts = part.split("_")
    for i, p in enumerate(parts):
        p = p.title()
        if len(p) < 3:
            p = p.upper()
        elif len(p) == 3:
            p = p.replace("Sap", "SAP")
            p = p.replace("Cta", "CTA")
        parts[i] = p

    part = " ".join(parts)

    return part


ROOT: Path = Path(__file__).parent.parent.parent
"""Root of the repository, place where the mkdocs.yml is"""

PACKAGE_NAME: str = "mkdocs_nype"
"""Name of the python package / source directory"""

SRC: Path = ROOT / PACKAGE_NAME
"""Source path of the python package"""

NAV: Nav = mkdocs_gen_files.Nav()
"""Nav object to store the generated navigation"""

TOP_LEVEL_DIR: str = "reference"
"""Top level root directory in nav"""

DOCS_PATH: Path = ROOT / "docs"
"""Path to the docs directory"""

DOCS_TOP_LEVEL_PATH: Path = DOCS_PATH / TOP_LEVEL_DIR
"""Path to the root of the generated nav containing the SUMMARY.md"""

main()

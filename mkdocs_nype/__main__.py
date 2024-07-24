"""mkdocs-nype module entry point

This script adds non-theme, non-MkDocs functionality.

1. JavaScript and Cascading Style Sheets minification

    This could likely be added in the `__init__.py` file and execute during theme import.
    However, modifying files while loading a theme doesn't seem right. So this feature
    moved here.

    As the minification is opt-in, the script can also modify local MkDocs project JS/CSS
    assets for the production deployment.

MIT License 2024 Kamil Krzyśków (HRY) for Nype (npe.cm)
"""

import hashlib
import sys
from pathlib import Path
from pprint import pprint

# Should be included in mkdocs-material[recommended].
# Imported like this, because the plugin does a csscompressor monkey-patch.
from mkdocs_minify_plugin import plugin as minify_plugin


def main():
    # TODO make the docs more helpful
    # TODO rewrite into argsparse to simplify args handling
    # TODO remove duplication

    args = list(map(lambda s: s.lower(), sys.argv[1:]))

    if "--help" in args:
        print(f"Read the source file to learn more:\n{__file__}")
        sys.exit(0)

    # Directory path to local project JavaScript files
    # Default: docs/assets/javascripts/
    if find(args, "--js-dir") > 0:
        js_dir = args[js_dir + 1]
        if js_dir.startswith("--"):
            sys.exit(f"invalid value {js_dir=}")
    else:
        js_dir = None

    # Directory path to local project CSS files
    # Default: docs/assets/stylesheets/
    if find(args, "--css-dir") > 0:
        css_dir = args[css_dir + 1]
        if css_dir.startswith("--"):
            sys.exit(f"invalid value {css_dir=}")
    else:
        css_dir = None

    # Part of the path to remove, to match Jinja2 templates
    # Default: docs/
    if find(args, "--remove-prefix") > 0:
        remove_prefix = args[remove_prefix + 1]
        if remove_prefix.startswith("--"):
            sys.exit(f"invalid value {remove_prefix=}")
    else:
        remove_prefix = None

    # Call minify function later?
    minify_flag = "--minify" in args

    # Replace originals with minified files? Without this flag, the execution is "dry"
    inject_minified_flag = "--inject-minified" in args

    if minify_flag:
        minify(inject_minified_flag, js_dir, css_dir, remove_prefix)


def minify(inject_minified_flag, js_dir, css_dir, remove_prefix):

    if js_dir is None:
        js_dir = "docs/assets/javascripts/"

    if css_dir is None:
        css_dir = "docs/assets/stylesheets/"

    if remove_prefix is None:
        remove_prefix = "docs/"

    nype_templates = Path(__file__).parent / "templates"

    rewrite_map = {}

    for path in nype_templates.glob("**/*.js"):
        if ".min." in str(path):
            continue
        minified = get_minified_content(path, minify_plugin.jsmin.jsmin)
        if inject_minified_flag:
            old = f"/{path.name}"
            hash_sum = hashlib.sha384(minified.encode("utf-8")).hexdigest()[:8]
            new = f"/{path.stem}.{hash_sum}.min.js"
            rewrite_map[old] = new
            Path(path.as_posix().replace(old, new)).write_text(minified, encoding="utf-8")

    for path in nype_templates.glob("**/*.css"):
        if ".min." in str(path):
            continue
        minified = get_minified_content(path, minify_plugin.csscompressor.compress)
        if inject_minified_flag:
            old = f"/{path.name}"
            hash_sum = hashlib.sha384(minified.encode("utf-8")).hexdigest()[:8]
            new = f"/{path.stem}.{hash_sum}.min.css"
            rewrite_map[old] = new
            Path(path.as_posix().replace(old, new)).write_text(minified, encoding="utf-8")

    if js_dir:
        for path in Path(js_dir).glob("**/*.js"):
            if ".min." in str(path):
                continue
            minified = get_minified_content(path, minify_plugin.jsmin.jsmin)
            if inject_minified_flag:
                old = f"/{path.name}"
                hash_sum = hashlib.sha384(minified.encode("utf-8")).hexdigest()[:8]
                new = f"/{path.stem}.{hash_sum}.min.js"
                rewrite_map[old] = new
                Path(path.as_posix().replace(old, new)).write_text(minified, encoding="utf-8")

    if css_dir:
        for path in Path(css_dir).glob("**/*.css"):
            if ".min." in str(path):
                continue
            minified = get_minified_content(path, minify_plugin.csscompressor.compress)
            if inject_minified_flag:
                old = f"/{path.name}"
                hash_sum = hashlib.sha384(minified.encode("utf-8")).hexdigest()[:8]
                new = f"/{path.stem}.{hash_sum}.min.css"
                rewrite_map[old] = new
                Path(path.as_posix().replace(old, new)).write_text(minified, encoding="utf-8")

    pprint(rewrite_map)

    # Modify local project templates and yaml configuration
    project_path = Path(".")
    paths: list[Path] = []
    paths.extend(project_path.glob("**/*.html"))
    paths.extend(project_path.glob("**/*.y*ml"))
    paths.extend(nype_templates.glob("**/*.html"))
    for path in paths:
        posix = path.as_posix()
        if posix.startswith(("venv/", "site/", "drafts/", "docs/")):
            continue

        if inject_minified_flag:
            print(f"Injecting minification for {posix}")
            content = path.read_text(encoding="utf-8")
            for old, new in rewrite_map.items():
                content = content.replace(old, new)
            path.write_text(content, encoding="utf-8")


def get_minified_content(file_path, processor):
    print(f"Minifying {file_path}")
    content = file_path.read_text(encoding="utf-8")
    if processor.__name__ == "jsmin":
        return processor(content, quote_chars="'\"`")
    else:
        return processor(content)


def find(lst, value):
    try:
        return lst.index(value)
    except ValueError:
        return -1


if __name__ == "__main__":
    main()

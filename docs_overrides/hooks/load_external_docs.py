import re
from pathlib import Path

from mkdocs.config.defaults import MkDocsConfig
from mkdocs.plugins import event_priority
from mkdocs.structure.files import Files
from mkdocs.structure.pages import Page

REPO_ROOT_PATH: Path = Path(__file__).parent.parent.parent
README_PATH: Path = REPO_ROOT_PATH / "README.md"
LICENSE_PATH: Path = REPO_ROOT_PATH / "LICENSE"


@event_priority(100)
def on_page_markdown(markdown: str, page: Page, config: MkDocsConfig, files: Files) -> str:
    if page.file.src_uri == "index.md":
        return inject_file(markdown, "README_PLACEHOLDER", process_readme_lines)
    elif page.file.src_uri == "license.md":
        return inject_file(markdown, "LICENSE_PLACEHOLDER", process_license_lines)


def inject_file(markdown: str, placeholder: str, placeholder_processor):
    found_placeholder = False

    lines = markdown.split("\n")
    output = []
    for line in lines:
        if placeholder in line:
            output.extend(placeholder_processor())
            found_placeholder = True
        else:
            output.append(line)

    assert found_placeholder, f"Placeholder not found {placeholder}"

    return "\n".join(output)


def process_readme_lines() -> list[str]:
    path_map: dict[str, str] = {
        "](LICENSE)": f"](license.md)",
    }

    # Skip first line with the title
    lines = README_PATH.read_text(encoding="utf-8").strip().split("\n")[1:]

    for i, line in enumerate(lines):
        for fs_path, url_path in path_map.items():
            if fs_path in line:
                lines[i] = line.replace(fs_path, url_path)

    return lines


def process_license_lines() -> list[str]:

    lines = LICENSE_PATH.read_text(encoding="utf-8").strip().split("\n")
    email_pattern = r"<.*@.*>"

    for i, line in enumerate(lines):
        if re.search(email_pattern, line):
            lines[i] = re.sub(email_pattern, "{% include 'hidden_email.md' %}", line)

    return lines

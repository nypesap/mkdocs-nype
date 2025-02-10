"""Scope currentcolor css for `code` tags in links

After enabling `anchorlink` for the `toc`, all headings turned blue, as they're in `code` tags.
Extra CSS is too much work, as we want to use the coloring from mkdocstrings.
Adding a `:not(.doc-symbol)` to the material theme color is simpler than to restore mkdocstring coloring.
Based on a previous solution: https://github.com/squidfunk/mkdocs-material/discussions/6844#discussioncomment-8670472

MIT License 2025 Kamil Krzyśków (HRY) for Nype (npe.cm)
"""

from pathlib import Path
from typing import Optional

from mkdocs.plugins import get_plugin_logger

LOG = get_plugin_logger("remove-currentcolor-css")


def on_post_build(config):
    site_dir: Path = Path(config["site_dir"])
    stylesheets_dir: Path = site_dir / "assets" / "stylesheets"

    # Find the bundle.js file to modify
    main_css_path: Optional[Path]
    for path in stylesheets_dir.glob("main*.css"):
        if str(path).lower().endswith(".css"):
            main_css_path = path
            break
    else:
        main_css_path = None

    # Bundle was not found, skip override
    if not main_css_path:
        LOG.error("No main.css found")
        return

    LOG.debug(f"Main CSS path: {main_css_path}")

    # Set LEFT and RIGHT marker strings
    left: str = ".md-typeset a code{"
    right: str = "color:currentcolor;"  # changed from "pipe"

    # Set old and new strings used for replacement
    # Set old as right to include right in the old lookup
    old: str = "a code"
    new: str = "a code:not(.doc-symbol)"

    # Set expected target region length
    expected_len: int = 19

    # Read the contents and find the LEFT marker string
    contents: str = main_css_path.read_text(encoding="utf8")
    left_pos: int = contents.find(left)

    # Negative number means not found, skip override
    if left_pos < 0:
        LOG.warning(f"The left marker - {left} - was not found")
        return

    # Move the cursor past the marker string
    left_pos_for_right_lookup = left_pos + len(left)

    # Now find the RIGHT marker string
    right_pos: int = contents.find(right, left_pos_for_right_lookup)

    # Negative number means not found, skip override
    if right_pos < 0:
        LOG.warning(f"The right marker - {right} - was not found")
        return

    # If the RIGHT marker string equals old then move the cursor past it
    if old == right:
        LOG.debug("The right marker is same as old, shifting cursor")
        right_pos += len(right)

    # Get target region based on the marker positions
    raw_target = contents[left_pos:right_pos]

    # Run with the `-v` verbose flag to see the value and store it for later use
    # with expected_len
    LOG.debug(f"len(raw_target) = {len(raw_target)}")
    LOG.debug(f"expected_len = {expected_len}")
    LOG.debug(f"raw_target = {raw_target}")
    LOG.debug(f"old = {old}")
    LOG.debug(f"new = {new}")

    # Validate the target region, and skip override if invalid
    if old not in raw_target:
        LOG.warning(f"{old} was not found in {raw_target}")
        return

    if expected_len != len(raw_target):
        LOG.warning(
            f"Expected len ({expected_len}) differs " f"from actual len ({len(raw_target)})"
        )
        return

    # Store separately for logging
    processed_target = raw_target.replace(old, new, 1)
    LOG.debug(f"processed_target = {processed_target}")

    # Merge parts
    result = "".join([contents[:left_pos], processed_target, contents[right_pos:]])

    # Shift left cursor back for final log entry
    left_pos -= len(left)

    # Shift right cursor if the processed_target is longer
    diff: int = len(processed_target) - len(raw_target)
    if diff > 0:
        right_pos += diff

    LOG.debug(f"final_target_range = {result[left_pos:right_pos]}")

    # Write new file contents
    LOG.info(f"Replaced {old} with {new} in {main_css_path.name}")
    main_css_path.write_text(result, encoding="utf8")

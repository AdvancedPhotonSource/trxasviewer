# Copyright © UChicago Argonne LLC
# See LICENSE file for details
"""Static checks for the macOS packaging assets.

Neither sips/iconutil (used by make_icns.sh) nor real icon generation can run
outside macOS, so these only check what IS verifiable here: the shell script
is syntactically valid and references the right paths, and the entitlements
file is a well-formed plist with the two keys notarization needs.
"""

import plistlib
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MAKE_ICNS = REPO_ROOT / "packaging" / "macos" / "make_icns.sh"
ENTITLEMENTS = REPO_ROOT / "packaging" / "macos" / "entitlements.plist"


def test_entitlements_plist_is_well_formed_with_required_keys():
    with open(ENTITLEMENTS, "rb") as f:
        data = plistlib.load(f)
    assert data["com.apple.security.cs.allow-unsigned-executable-memory"] is True
    assert data["com.apple.security.cs.disable-library-validation"] is True


def test_make_icns_script_is_valid_bash():
    result = subprocess.run(
        ["bash", "-n", str(MAKE_ICNS)], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr


def test_make_icns_script_references_icon_png_source_and_icns_output():
    content = MAKE_ICNS.read_text()
    assert "packaging/icon.png" in content
    assert "icon.icns" in content

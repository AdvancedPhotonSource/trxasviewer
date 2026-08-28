# Copyright © UChicago Argonne LLC
# See LICENSE file for details
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
APP_RUN = REPO_ROOT / "packaging" / "linux" / "AppRun"
DESKTOP_FILE = REPO_ROOT / "packaging" / "linux" / "trxasviewer.desktop"
BUILD_SCRIPT = REPO_ROOT / "packaging" / "linux" / "build-appimage.sh"


def test_apprun_is_valid_bash_and_execs_trxasviewer():
    result = subprocess.run(["bash", "-n", str(APP_RUN)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "usr/bin/trxasviewer/trxasviewer" in APP_RUN.read_text()


def test_desktop_file_has_required_keys():
    content = DESKTOP_FILE.read_text()
    assert "Name=TrXASViewer" in content
    assert "Exec=trxasviewer" in content
    assert "Icon=trxasviewer" in content
    assert "Categories=Science;" in content


def test_build_appimage_script_is_valid_bash():
    result = subprocess.run(["bash", "-n", str(BUILD_SCRIPT)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_build_appimage_script_references_spec_and_icon():
    content = BUILD_SCRIPT.read_text()
    assert "trxasviewer.spec" in content
    assert "packaging/icon.png" in content

# Copyright © UChicago Argonne LLC
# See LICENSE file for details
"""Structural checks for .github/workflows/build-releases.yml.

These don't run the workflow itself (that needs GitHub Actions plus real
Apple signing/notarization credentials) — they catch YAML mistakes and
job-wiring regressions (e.g. forgetting to gate github-release correctly)
without waiting on a live run.
"""

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "build-releases.yml"


def _load_workflow():
    with open(WORKFLOW_PATH) as f:
        return yaml.safe_load(f)


def _triggers(workflow):
    # PyYAML's default (YAML 1.1) resolver reads the bare key `on` as the
    # boolean True, not the string "on" — this is a well-known GitHub
    # Actions YAML gotcha. Handle both so this test doesn't silently pass
    # against an empty dict.
    return workflow.get("on", workflow.get(True))


def test_workflow_triggers_on_v_tags_and_manual_dispatch():
    workflow = _load_workflow()
    triggers = _triggers(workflow)
    assert triggers["push"]["tags"] == ["v*"]
    assert "version_tag" in triggers["workflow_dispatch"]["inputs"]


def test_workflow_has_four_jobs():
    workflow = _load_workflow()
    assert set(workflow["jobs"]) == {
        "windows-build",
        "linux-appimage-build",
        "macos-build",
        "github-release",
    }


def test_windows_job_runs_on_windows_latest():
    workflow = _load_workflow()
    assert workflow["jobs"]["windows-build"]["runs-on"] == "windows-latest"


def test_linux_job_uses_rockylinux_container():
    job = _load_workflow()["jobs"]["linux-appimage-build"]
    assert job["runs-on"] == "ubuntu-latest"
    assert job["container"] == "rockylinux:9"


def test_macos_job_targets_macos14_and_signing_environment():
    job = _load_workflow()["jobs"]["macos-build"]
    assert job["runs-on"] == "macos-14"
    assert job["environment"] == "macos-signing"


def test_release_job_needs_all_three_builds():
    job = _load_workflow()["jobs"]["github-release"]
    assert set(job["needs"]) == {"windows-build", "linux-appimage-build", "macos-build"}


def test_release_job_condition_hard_requires_only_windows_and_linux():
    job = _load_workflow()["jobs"]["github-release"]
    condition = job["if"]
    assert "needs.windows-build.result == 'success'" in condition
    assert "needs.linux-appimage-build.result == 'success'" in condition
    assert "needs.macos-build" not in condition


def test_macos_artifact_download_is_conditional_on_macos_success():
    steps = _load_workflow()["jobs"]["github-release"]["steps"]
    macos_download = next(s for s in steps if s.get("name") == "Download macOS dmg artifact")
    assert macos_download["if"] == "needs.macos-build.result == 'success'"


def test_release_files_glob_includes_all_three_platforms():
    steps = _load_workflow()["jobs"]["github-release"]["steps"]
    release_step = next(
        s for s in steps if s.get("uses", "").startswith("softprops/action-gh-release")
    )
    files = release_step["with"]["files"]
    assert "dist/trxasviewer-*-windows.exe" in files
    assert "dist/trxasviewer-*-x86_64.AppImage" in files
    assert "dist/trxasviewer-*-macos.dmg" in files

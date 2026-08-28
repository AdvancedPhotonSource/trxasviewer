# Single-File Executable Releases Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a GitHub Actions workflow that builds a Windows `.exe`, a Linux `.AppImage`, and a signed/notarized macOS `.dmg` for trxasviewer on every `v*` tag push, and publishes them as a GitHub Release.

**Architecture:** A single new PyInstaller spec (`trxasviewer.spec`) with three platform branches, fed by a small `packaging/entrypoint.py` wrapper around the existing `trxasviewer.cli.main()`. A new `.github/workflows/build-releases.yml` runs one build job per platform plus a `github-release` job that publishes whatever succeeded. The existing `.github/workflows/autobuild.yml` (sdist/wheel) is untouched.

**Tech Stack:** PyInstaller >= 6.21, GitHub Actions (`windows-latest`, `ubuntu-latest` + `rockylinux:9` container, `macos-14`), `softprops/action-gh-release`, Apple `codesign`/`notarytool`/`stapler`/`spctl`.

**Spec:** `docs/superpowers/specs/2026-08-28-executable-release-builds-design.md`

## Global Constraints

- Tag trigger pattern is `v*` (matches this repo's current tags: `v0.5.0`, `v0.5.1`), not the bare `*` that `autobuild.yml` uses.
- `pyinstaller>=6.21` as a new `[project.optional-dependencies.pyinstaller]` group.
- Build Python: `3.12` for Windows/macOS jobs; `python3.11` inside the `rockylinux:9` container for the Linux job (RockyLinux 9's system Python is 3.9 and lacks PyInstaller).
- macOS bundle identifier: `gov.anl.aps.trxasviewer`.
- macOS signing uses the `macos-signing` GitHub Environment on `AdvancedPhotonSource/trxasviewer`, already provisioned this session with secrets `BUILD_CERTIFICATE_BASE64`, `P12_PASSWORD`, `KEYCHAIN_PASSWORD`, `APPLE_ID`, `APPLE_APP_PASSWORD` and variable `APPLE_TEAM_ID`.
- Artifact naming: `trxasviewer-<tag>-windows.exe`, `trxasviewer-<tag>-x86_64.AppImage`, `trxasviewer-<tag>-macos.dmg`.
- `.github/workflows/autobuild.yml` is not modified.
- No PyPI publishing in this pass; no `model`-subcommand smoke test in this pass.
- No Qt Designer `.ui` files need to be bundled as PyInstaller `datas` — the app only imports the pre-generated `generated_ui.py` / `generated_modeling_ui.py`.
- `github-release`'s job-level `if:` requires only `windows-build` and `linux-appimage-build` to succeed; the macOS `.dmg` is attached only if `macos-build` also succeeded (downloaded conditionally), so one platform failing never blocks the other two.

---

### Task 1: Packaging project setup — `pyinstaller`/`Pillow`/`pyyaml` extras, `.gitignore` carve-out, entrypoint script

**Files:**
- Modify: `pyproject.toml`
- Modify: `.gitignore`
- Create: `packaging/entrypoint.py`
- Create: `tests/packaging/__init__.py`
- Test: `tests/packaging/test_entrypoint.py`

**Interfaces:**
- Consumes: `trxasviewer.cli.main` (existing, `src/trxasviewer/cli.py:68`).
- Produces: `packaging/entrypoint.py` — importable/runnable script that later tasks (Task 3's spec, Task 6's workflow) point PyInstaller at.

- [ ] **Step 1: Create the test package marker**

```bash
mkdir -p tests/packaging
touch tests/packaging/__init__.py
```

- [ ] **Step 2: Write the failing test**

Create `tests/packaging/test_entrypoint.py`:

```python
# Copyright © UChicago Argonne LLC
# See LICENSE file for details
import runpy
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[2]
ENTRYPOINT = REPO_ROOT / "packaging" / "entrypoint.py"


def test_entrypoint_calls_freeze_support_then_main():
    calls = []
    with patch(
        "multiprocessing.freeze_support",
        side_effect=lambda: calls.append("freeze_support"),
    ), patch(
        "trxasviewer.cli.main",
        side_effect=lambda: calls.append("main"),
    ):
        runpy.run_path(str(ENTRYPOINT), run_name="__main__")

    assert calls == ["freeze_support", "main"]
```

- [ ] **Step 3: Run test to verify it fails**

Run: `pytest tests/packaging/test_entrypoint.py -v`
Expected: FAIL — `packaging/entrypoint.py` does not exist yet (`FileNotFoundError` from `runpy.run_path`).

- [ ] **Step 4: Create `packaging/entrypoint.py`**

```python
# Copyright © UChicago Argonne LLC
# See LICENSE file for details
"""PyInstaller entry point for the trxasviewer GUI."""

import multiprocessing

from trxasviewer.cli import main


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
```

- [ ] **Step 5: Add the `pyinstaller` extra and test-only libs to `pyproject.toml`**

In `pyproject.toml`, change:

```toml
[project.optional-dependencies]
dev = ["coverage", "pytest", "pytest-cov", "mypy", "ruff", "twine", "pytest-qt"]
docs = ["sphinx", "sphinx-rtd-theme"]
```

to:

```toml
[project.optional-dependencies]
dev = ["coverage", "pytest", "pytest-cov", "mypy", "ruff", "twine", "pytest-qt", "Pillow", "PyYAML"]
docs = ["sphinx", "sphinx-rtd-theme"]
pyinstaller = ["pyinstaller>=6.21"]
```

(`Pillow` is needed by Task 2's icon test, `PyYAML` by Task 6's workflow test — both already import fine transitively today, this just makes the dependency explicit.)

- [ ] **Step 6: Carve `trxasviewer.spec` out of the blanket `*.spec` ignore**

In `.gitignore`, change:

```
# PyInstaller
#  Usually these files are written by a python script from a template
#  before PyInstaller builds the exe, so as to inject date/other infos into it.
*.manifest
*.spec
```

to:

```
# PyInstaller
#  Usually these files are written by a python script from a template
#  before PyInstaller builds the exe, so as to inject date/other infos into it.
*.manifest
*.spec
!trxasviewer.spec
```

- [ ] **Step 7: Run test to verify it passes**

Run: `pytest tests/packaging/test_entrypoint.py -v`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add pyproject.toml .gitignore packaging/entrypoint.py tests/packaging/__init__.py tests/packaging/test_entrypoint.py
git commit -m "chore: add PyInstaller packaging entrypoint and project setup"
```

---

### Task 2: Icon assets — `packaging/icon.png` + `packaging/icon.ico`

**Files:**
- Create: `packaging/icon.png`
- Create: `packaging/icon.ico`
- Test: `tests/packaging/test_icons.py`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: `packaging/icon.png` (source PNG, also used by `packaging/macos/make_icns.sh` in Task 4 and `packaging/linux/build-appimage.sh` in Task 5), `packaging/icon.ico` (consumed by `trxasviewer.spec`'s Windows branch in Task 3).

- [ ] **Step 1: Write the failing test**

Create `tests/packaging/test_icons.py`:

```python
# Copyright © UChicago Argonne LLC
# See LICENSE file for details
from pathlib import Path

from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_icon_png_exists_and_is_square():
    icon_png = REPO_ROOT / "packaging" / "icon.png"
    assert icon_png.exists()
    with Image.open(icon_png) as im:
        width, height = im.size
        assert width == height
        assert width >= 256


def test_icon_ico_contains_multiple_resolutions():
    icon_ico = REPO_ROOT / "packaging" / "icon.ico"
    assert icon_ico.exists()
    with Image.open(icon_ico) as im:
        sizes = set(im.info.get("sizes", []))
        assert (16, 16) in sizes
        assert (32, 32) in sizes
        assert (256, 256) in sizes
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/packaging/test_icons.py -v`
Expected: FAIL — neither file exists yet.

- [ ] **Step 3: Copy the source PNG into `packaging/`**

```bash
mkdir -p packaging
cp /home/beams/MQICHU/Downloads/icon.png packaging/icon.png
```

- [ ] **Step 4: Generate the multi-resolution `.ico`**

```bash
python3 -c "
from PIL import Image
im = Image.open('packaging/icon.png').convert('RGBA')
im.save('packaging/icon.ico', sizes=[(16, 16), (32, 32), (48, 48), (256, 256)])
"
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/packaging/test_icons.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add packaging/icon.png packaging/icon.ico tests/packaging/test_icons.py
git commit -m "feat: add trxasviewer app icon assets"
```

---

### Task 3: `trxasviewer.spec` — PyInstaller spec with three platform branches

**Files:**
- Create: `trxasviewer.spec`
- Test: `tests/packaging/test_trxasviewer_spec.py`

**Interfaces:**
- Consumes: `packaging/entrypoint.py` (Task 1), `packaging/icon.ico` (Task 2), `packaging/macos/icon.icns` (path referenced only — generated at build time in Task 4, does not need to exist for this task's test).
- Produces: `trxasviewer.spec` at repo root — consumed by `packaging/linux/build-appimage.sh` (Task 5) and by `.github/workflows/build-releases.yml` (Task 6).

- [ ] **Step 1: Write the failing test**

Create `tests/packaging/test_trxasviewer_spec.py`:

```python
# Copyright © UChicago Argonne LLC
# See LICENSE file for details
"""Exercises trxasviewer.spec's per-platform branches without needing a real
PyInstaller install or a macOS/Windows machine.

PyInstaller runs .spec files with exec(), injecting SPECPATH and the
Analysis/PYZ/EXE/BUNDLE/COLLECT builder names into the execution namespace.
We reproduce that here with recording stand-ins so the branch logic (which
builder gets which name/icon/bundle id) has real test coverage instead of
only being checkable by actually building on each target OS.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC_SOURCE = (REPO_ROOT / "trxasviewer.spec").read_text()


class _Recorder:
    """Stand-in for a PyInstaller builder class; records every call."""

    def __init__(self):
        self.calls = []
        self.results = []

    def __call__(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        result = object()
        self.results.append(result)
        return result


class _AnalysisStub:
    """Stand-in for PyInstaller's Analysis result.

    The spec accesses a.pure (for PYZ) and a.scripts/a.binaries/a.datas (for
    EXE/COLLECT) across its three platform branches, so all four must exist.
    Kwargs are also recorded so tests can inspect hiddenimports/datas.
    """

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.pure = []
        self.scripts = []
        self.binaries = []
        self.datas = []


def _run_spec(monkeypatch, platform):
    monkeypatch.setattr(sys, "platform", platform)
    exe_recorder = _Recorder()
    bundle_recorder = _Recorder()
    collect_recorder = _Recorder()
    namespace = {
        "SPECPATH": str(REPO_ROOT),
        "Analysis": _AnalysisStub,
        "PYZ": lambda *a, **k: object(),
        "EXE": exe_recorder,
        "BUNDLE": bundle_recorder,
        "COLLECT": collect_recorder,
    }
    exec(compile(SPEC_SOURCE, "trxasviewer.spec", "exec"), namespace)
    return namespace, exe_recorder, bundle_recorder, collect_recorder


def test_macos_branch_wraps_exe_in_app_bundle(monkeypatch):
    _, exe_rec, bundle_rec, collect_rec = _run_spec(monkeypatch, "darwin")

    assert len(exe_rec.calls) == 1
    assert len(collect_rec.calls) == 1
    assert len(bundle_rec.calls) == 1

    _, exe_kwargs = exe_rec.calls[0]
    assert exe_kwargs["codesign_identity"] is None
    assert exe_kwargs["exclude_binaries"] is True

    bundle_args, bundle_kwargs = bundle_rec.calls[0]
    assert bundle_args[0] is collect_rec.results[0]
    assert bundle_kwargs["name"] == "trxasviewer.app"
    assert bundle_kwargs["bundle_identifier"] == "gov.anl.aps.trxasviewer"
    assert bundle_kwargs["icon"].endswith("packaging/macos/icon.icns")


def test_windows_branch_unchanged_no_bundle(monkeypatch):
    _, exe_rec, bundle_rec, collect_rec = _run_spec(monkeypatch, "win32")

    assert len(exe_rec.calls) == 1
    assert len(bundle_rec.calls) == 0
    _, exe_kwargs = exe_rec.calls[0]
    assert exe_kwargs["icon"].endswith("packaging/icon.ico")


def test_linux_branch_unchanged_uses_collect(monkeypatch):
    _, exe_rec, bundle_rec, collect_rec = _run_spec(monkeypatch, "linux")

    assert len(exe_rec.calls) == 1
    assert len(collect_rec.calls) == 1
    assert len(bundle_rec.calls) == 0


def test_hiddenimports_cover_all_trxasviewer_submodules(monkeypatch):
    namespace, *_ = _run_spec(monkeypatch, "linux")
    hiddenimports = set(namespace["a"].kwargs["hiddenimports"])
    expected = {
        "trxasviewer.core.array_ops",
        "trxasviewer.core.constants",
        "trxasviewer.core.dataset",
        "trxasviewer.core.file_io",
        "trxasviewer.core.fitting",
        "trxasviewer.core.graph",
        "trxasviewer.core.io",
        "trxasviewer.core.plot",
        "trxasviewer.core.result",
        "trxasviewer.core.utilities",
        "trxasviewer.gui.control.viewer_controller",
        "trxasviewer.gui.control.workers",
        "trxasviewer.gui.model.viewer_model",
        "trxasviewer.gui.view.generated_ui",
        "trxasviewer.gui.view.pg_plot",
        "trxasviewer.gui.view.viewer_view",
        "trxasviewer.gui.view.widgets",
        "trxasviewer.modeling_gui.generated_modeling_ui",
        "trxasviewer.modeling_gui.kinetics_optimizer",
        "trxasviewer.modeling_gui.trxas_modeling",
        "trxasviewer.cli",
    }
    assert expected.issubset(hiddenimports)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/packaging/test_trxasviewer_spec.py -v`
Expected: FAIL/ERROR at collection — `trxasviewer.spec` does not exist yet, so `SPEC_SOURCE = (REPO_ROOT / "trxasviewer.spec").read_text()` raises `FileNotFoundError`.

- [ ] **Step 3: Create `trxasviewer.spec`**

```python
# trxasviewer.spec
# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for the trxasviewer GUI (.exe / one-dir bundle)
#
# Usage:
#   pyinstaller trxasviewer.spec
#
# The spec uses a small entrypoint in packaging/ so the packaged binary
# stays stable even if the internal import path changes.

from pathlib import Path

# SPECPATH is the directory containing this spec file (set by PyInstaller),
# not the file path itself. This spec lives at the repo root alongside
# packaging/ and src/, so both anchors are that same directory.
spec_dir = Path(SPECPATH)
repo_root = spec_dir

a = Analysis(
    [str(spec_dir / 'packaging' / 'entrypoint.py')],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'trxasviewer',
        'trxasviewer.core',
        'trxasviewer.core.array_ops',
        'trxasviewer.core.constants',
        'trxasviewer.core.dataset',
        'trxasviewer.core.file_io',
        'trxasviewer.core.fitting',
        'trxasviewer.core.graph',
        'trxasviewer.core.io',
        'trxasviewer.core.plot',
        'trxasviewer.core.result',
        'trxasviewer.core.utilities',
        'trxasviewer.gui',
        'trxasviewer.gui.control',
        'trxasviewer.gui.control.viewer_controller',
        'trxasviewer.gui.control.workers',
        'trxasviewer.gui.model',
        'trxasviewer.gui.model.viewer_model',
        'trxasviewer.gui.view',
        'trxasviewer.gui.view.generated_ui',
        'trxasviewer.gui.view.pg_plot',
        'trxasviewer.gui.view.viewer_view',
        'trxasviewer.gui.view.widgets',
        'trxasviewer.modeling_gui',
        'trxasviewer.modeling_gui.generated_modeling_ui',
        'trxasviewer.modeling_gui.kinetics_optimizer',
        'trxasviewer.modeling_gui.trxas_modeling',
        'trxasviewer.cli',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'pytest',
        'coverage',
        'setuptools',
        'pip',
        'wheel',
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

# Platform-specific EXE settings
import sys

if sys.platform == 'win32':
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
        [],
        name='trxasviewer',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=str(spec_dir / 'packaging' / 'icon.ico'),
    )
elif sys.platform == 'linux':
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name='trxasviewer',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
    )
    coll = COLLECT(
        exe,
        a.binaries,
        a.datas,
        strip=False,
        upx=False,
        upx_exclude=[],
        name='trxasviewer',
    )
else:
    # macOS or other — one-dir EXE + COLLECT wrapped in an .app bundle.
    # codesign_identity stays None: the release workflow does an explicit
    # `codesign --deep --options runtime` pass afterward so it can apply the
    # hardened-runtime entitlements notarization needs.
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name='trxasviewer',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
    )
    coll = COLLECT(
        exe,
        a.binaries,
        a.datas,
        strip=False,
        upx=False,
        upx_exclude=[],
        name='trxasviewer',
    )
    app = BUNDLE(
        coll,
        name='trxasviewer.app',
        icon=str(spec_dir / 'packaging' / 'macos' / 'icon.icns'),
        bundle_identifier='gov.anl.aps.trxasviewer',
        info_plist={
            'NSHighResolutionCapable': True,
        },
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/packaging/test_trxasviewer_spec.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add trxasviewer.spec tests/packaging/test_trxasviewer_spec.py
git commit -m "feat: add PyInstaller spec for trxasviewer GUI"
```

---

### Task 4: macOS packaging files — `entitlements.plist` + `make_icns.sh`

**Files:**
- Create: `packaging/macos/entitlements.plist`
- Create: `packaging/macos/make_icns.sh`
- Test: `tests/packaging/test_macos_packaging.py`

**Interfaces:**
- Consumes: `packaging/icon.png` (Task 2).
- Produces: `packaging/macos/entitlements.plist` and `packaging/macos/make_icns.sh` — both referenced by name in `.github/workflows/build-releases.yml`'s `macos-build` job (Task 6).

- [ ] **Step 1: Write the failing test**

Create `tests/packaging/test_macos_packaging.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/packaging/test_macos_packaging.py -v`
Expected: FAIL — neither file exists yet.

- [ ] **Step 3: Create `packaging/macos/entitlements.plist`**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>com.apple.security.cs.allow-unsigned-executable-memory</key>
    <true/>
    <key>com.apple.security.cs.disable-library-validation</key>
    <true/>
</dict>
</plist>
```

- [ ] **Step 4: Create `packaging/macos/make_icns.sh`**

```bash
#!/usr/bin/env bash
# Generates packaging/macos/icon.icns from packaging/icon.png.
#
# Uses sips/iconutil, which only exist on macOS, so this runs in CI
# (macos-14 runner) rather than being committed as a prebuilt binary asset.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SOURCE_PNG="$REPO_ROOT/packaging/icon.png"
ICONSET_DIR="$REPO_ROOT/packaging/macos/icon.iconset"
OUTPUT_ICNS="$REPO_ROOT/packaging/macos/icon.icns"

rm -rf "$ICONSET_DIR"
mkdir -p "$ICONSET_DIR"

for size in 16 32 128 256 512; do
  sips -z "$size" "$size" "$SOURCE_PNG" \
    --out "$ICONSET_DIR/icon_${size}x${size}.png" >/dev/null
  double=$((size * 2))
  sips -z "$double" "$double" "$SOURCE_PNG" \
    --out "$ICONSET_DIR/icon_${size}x${size}@2x.png" >/dev/null
done

iconutil -c icns "$ICONSET_DIR" -o "$OUTPUT_ICNS"
rm -rf "$ICONSET_DIR"

echo "Wrote $OUTPUT_ICNS"
```

- [ ] **Step 5: Make the script executable**

```bash
chmod +x packaging/macos/make_icns.sh
```

- [ ] **Step 6: Run test to verify it passes**

Run: `pytest tests/packaging/test_macos_packaging.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add packaging/macos/entitlements.plist packaging/macos/make_icns.sh tests/packaging/test_macos_packaging.py
git commit -m "feat: add macOS entitlements and icon-generation script"
```

---

### Task 5: Linux packaging files — `AppRun`, `.desktop`, `build-appimage.sh`

**Files:**
- Create: `packaging/linux/AppRun`
- Create: `packaging/linux/trxasviewer.desktop`
- Create: `packaging/linux/build-appimage.sh`
- Test: `tests/packaging/test_linux_packaging.py`

**Interfaces:**
- Consumes: `trxasviewer.spec` (Task 3), `packaging/icon.png` (Task 2).
- Produces: `packaging/linux/build-appimage.sh` — invoked by `.github/workflows/build-releases.yml`'s `linux-appimage-build` job (Task 6) as `bash packaging/linux/build-appimage.sh "$TAG"`.

- [ ] **Step 1: Write the failing test**

Create `tests/packaging/test_linux_packaging.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/packaging/test_linux_packaging.py -v`
Expected: FAIL — none of the three files exist yet.

- [ ] **Step 3: Create `packaging/linux/AppRun`**

```bash
#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"
exec "${HERE}/usr/bin/trxasviewer/trxasviewer" "$@"
```

- [ ] **Step 4: Create `packaging/linux/trxasviewer.desktop`**

```ini
[Desktop Entry]
Type=Application
Name=TrXASViewer
Comment=Visualize and analyze Time-Resolved X-ray Absorption Spectroscopy datasets
Exec=trxasviewer
Icon=trxasviewer
Terminal=false
Categories=Science;
```

- [ ] **Step 5: Create `packaging/linux/build-appimage.sh`**

```bash
#!/bin/bash
# packaging/linux/build-appimage.sh
# Build a Linux AppImage for trxasviewer.
#
# Usage (from repo root):
#   bash packaging/linux/build-appimage.sh <version-tag>
#
# Prerequisites:
#   - PyInstaller installed in the active Python environment
#   - curl (to download appimagetool)
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/../.."
REPO_ROOT="$(pwd)"
VERSION="${1:?Usage: build-appimage.sh <version-tag>}"

rm -rf build dist/trxasviewer dist/AppDir

# Prefer whatever "python" resolves to in the active environment (local dev:
# the activated venv/conda env with PyInstaller installed). Fall back to
# python3.11 before the bare "python3" system interpreter: rockylinux:9 ships
# its own /usr/bin/python3 (3.9) for OS tooling, which does NOT have
# PyInstaller installed by the CI workflow (that targets python3.11
# explicitly), so picking it up here would silently build with the wrong
# interpreter.
PYTHON="${PYTHON:-$(command -v python || command -v python3.11 || command -v python3)}"

# Build the one-dir bundle with PyInstaller
"$PYTHON" -m PyInstaller trxasviewer.spec

# --- Assemble AppDir ---
mkdir -p dist/AppDir/usr/bin
cp -r dist/trxasviewer dist/AppDir/usr/bin/trxasviewer
install -m 755 packaging/linux/AppRun dist/AppDir/AppRun
cp packaging/linux/trxasviewer.desktop dist/AppDir/trxasviewer.desktop
cp packaging/icon.png dist/AppDir/trxasviewer.png

# --- Download appimagetool ---
curl -sL -o dist/appimagetool \
  https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage
chmod +x dist/appimagetool

# --- Build AppImage ---
# appimagetool's --appimage-extract-and-run chdirs during self-extraction, so
# relative path arguments resolve against the wrong directory. Use absolute
# paths.
dist/appimagetool --appimage-extract-and-run \
  "$REPO_ROOT/dist/AppDir" \
  "$REPO_ROOT/dist/trxasviewer-${VERSION}-x86_64.AppImage"

echo "AppImage built: dist/trxasviewer-${VERSION}-x86_64.AppImage"
```

- [ ] **Step 6: Make scripts executable**

```bash
chmod +x packaging/linux/AppRun packaging/linux/build-appimage.sh
```

- [ ] **Step 7: Run test to verify it passes**

Run: `pytest tests/packaging/test_linux_packaging.py -v`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add packaging/linux/AppRun packaging/linux/trxasviewer.desktop packaging/linux/build-appimage.sh tests/packaging/test_linux_packaging.py
git commit -m "feat: add Linux AppImage packaging files"
```

---

### Task 6: `.github/workflows/build-releases.yml`

**Files:**
- Create: `.github/workflows/build-releases.yml`
- Test: `tests/packaging/test_build_releases_workflow.py`

**Interfaces:**
- Consumes: `trxasviewer.spec` (Task 3), `packaging/entrypoint.py` (Task 1), `packaging/macos/make_icns.sh` + `packaging/macos/entitlements.plist` (Task 4), `packaging/linux/build-appimage.sh` (Task 5), the `pyinstaller` extra (Task 1), the `macos-signing` GitHub Environment (already provisioned).
- Produces: nothing consumed by later tasks — this is the last task.

- [ ] **Step 1: Write the failing test**

Create `tests/packaging/test_build_releases_workflow.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/packaging/test_build_releases_workflow.py -v`
Expected: FAIL — `.github/workflows/build-releases.yml` does not exist yet.

- [ ] **Step 3: Create `.github/workflows/build-releases.yml`**

```yaml
name: Build GUI releases

on:
  push:
    tags: ["v*"]
  workflow_dispatch:
    inputs:
      version_tag:
        description: "Tag to use for artifact naming on a manual run"
        required: true
        default: "v0.0.0-dev"

env:
  PYTHON_VERSION: "3.12"

jobs:
  windows-build:
    name: Build Windows executable
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v7
        with:
          fetch-depth: 0

      - uses: actions/setup-python@v7
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Cache PyInstaller build
        uses: actions/cache@v5
        with:
          path: build/
          key: pyinstaller-win-${{ hashFiles('trxasviewer.spec', 'packaging/entrypoint.py') }}
          restore-keys: |
            pyinstaller-win-

      - name: Install project and PyInstaller
        run: |
          python -m pip install --upgrade pip
          python -m pip install -e ".[pyinstaller]"

      - name: Build executable
        run: pyinstaller trxasviewer.spec

      - name: Rename executable with version
        shell: bash
        run: |
          TAG="${{ github.event_name == 'push' && github.ref_name || github.event.inputs.version_tag }}"
          mv dist/trxasviewer.exe "dist/trxasviewer-${TAG}-windows.exe"

      - name: Smoke test executable launches
        shell: pwsh
        env:
          QT_QPA_PLATFORM: offscreen
        run: |
          $exe = Get-ChildItem dist -Filter "trxasviewer-*-windows.exe" | Select-Object -First 1
          if (-not $exe) { throw "No .exe found in dist/" }
          $proc = Start-Process -FilePath $exe.FullName -PassThru
          Start-Sleep -Seconds 8
          if ($proc.HasExited) {
            Write-Error "Executable exited early with code $($proc.ExitCode)"
            exit 1
          }
          Write-Host "Executable is running after 8s, smoke test passed"
          Stop-Process -Id $proc.Id -Force

      - name: Upload Windows executable artifact
        uses: actions/upload-artifact@v7
        with:
          name: windows-exe
          path: dist/trxasviewer-*-windows.exe
          retention-days: 14

  linux-appimage-build:
    name: Build Linux AppImage
    runs-on: ubuntu-latest
    container: rockylinux:9
    steps:
      - name: Install git
        run: dnf install -y git

      - uses: actions/checkout@v7
        with:
          fetch-depth: 0

      - name: Install system dependencies
        run: |
          dnf install -y python3.11 python3.11-pip \
            mesa-libGL mesa-libEGL libxkbcommon libxkbcommon-x11 \
            xcb-util-wm xcb-util-image xcb-util-keysyms xcb-util-renderutil \
            dbus-libs fontconfig freetype file

      - name: Cache PyInstaller build
        uses: actions/cache@v5
        with:
          path: build/
          key: pyinstaller-linux-${{ hashFiles('trxasviewer.spec', 'packaging/entrypoint.py') }}
          restore-keys: |
            pyinstaller-linux-

      - name: Install project and PyInstaller
        run: |
          python3.11 -m pip install --upgrade pip
          python3.11 -m pip install -e ".[pyinstaller]"

      - name: Build AppImage
        run: |
          TAG="${{ github.event_name == 'push' && github.ref_name || github.event.inputs.version_tag }}"
          bash packaging/linux/build-appimage.sh "$TAG"

      - name: Smoke test AppImage launches
        env:
          QT_QPA_PLATFORM: offscreen
        run: |
          APPIMAGE=$(ls dist/trxasviewer-*-x86_64.AppImage 2>/dev/null || echo "")
          if [ -z "$APPIMAGE" ]; then
            echo "No AppImage found"
            ls -la dist/
            exit 1
          fi
          chmod +x "$APPIMAGE"
          timeout 8 "$APPIMAGE" --appimage-extract-and-run > /tmp/run.log 2>&1 &
          RPID=$!
          sleep 6
          if kill -0 $RPID 2>/dev/null; then
            echo "Smoke test passed: AppImage is running after 6s"
            kill $RPID
          else
            wait $RPID || true
            echo "Smoke test FAILED: AppImage exited early"
            cat /tmp/run.log
            exit 1
          fi

      - name: Upload Linux AppImage artifact
        uses: actions/upload-artifact@v7
        with:
          name: linux-appimage
          path: dist/trxasviewer-*-x86_64.AppImage
          retention-days: 14

  macos-build:
    name: Build, sign, and notarize macOS app
    runs-on: macos-14
    environment: macos-signing
    steps:
      - uses: actions/checkout@v7
        with:
          fetch-depth: 0

      - uses: actions/setup-python@v7
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Cache PyInstaller build
        uses: actions/cache@v5
        with:
          path: build/
          key: pyinstaller-macos-${{ hashFiles('trxasviewer.spec', 'packaging/entrypoint.py') }}
          restore-keys: |
            pyinstaller-macos-

      - name: Install project and PyInstaller
        run: |
          python -m pip install --upgrade pip
          python -m pip install -e ".[pyinstaller]"

      - name: Generate .icns app icon
        run: bash packaging/macos/make_icns.sh

      - name: Import Developer ID certificate
        env:
          BUILD_CERTIFICATE_BASE64: ${{ secrets.BUILD_CERTIFICATE_BASE64 }}
          P12_PASSWORD: ${{ secrets.P12_PASSWORD }}
          KEYCHAIN_PASSWORD: ${{ secrets.KEYCHAIN_PASSWORD }}
        run: |
          CERTIFICATE_PATH="$RUNNER_TEMP/developer-id.p12"
          KEYCHAIN_PATH="$RUNNER_TEMP/signing.keychain-db"

          printf '%s' "$BUILD_CERTIFICATE_BASE64" \
            | base64 --decode > "$CERTIFICATE_PATH"

          security create-keychain -p "$KEYCHAIN_PASSWORD" "$KEYCHAIN_PATH"
          security set-keychain-settings -lut 21600 "$KEYCHAIN_PATH"
          security unlock-keychain -p "$KEYCHAIN_PASSWORD" "$KEYCHAIN_PATH"

          security import "$CERTIFICATE_PATH" \
            -k "$KEYCHAIN_PATH" \
            -P "$P12_PASSWORD" \
            -A \
            -t cert \
            -f pkcs12

          security set-key-partition-list \
            -S apple-tool:,apple:,codesign: \
            -s \
            -k "$KEYCHAIN_PASSWORD" \
            "$KEYCHAIN_PATH"

          security list-keychains -d user -s "$KEYCHAIN_PATH"
          security default-keychain -d user -s "$KEYCHAIN_PATH"

          echo "Available signing identities:"
          security find-identity -v -p codesigning "$KEYCHAIN_PATH"

          SIGNING_IDENTITY="$(
            security find-identity -v -p codesigning "$KEYCHAIN_PATH" \
              | grep "Developer ID Application" \
              | head -1 \
              | awk '{print $2}'
          )"

          if [ -z "$SIGNING_IDENTITY" ]; then
            echo "::error::Developer ID Application identity not found"
            exit 1
          fi

          echo "SIGNING_IDENTITY=$SIGNING_IDENTITY" >> "$GITHUB_ENV"
          echo "KEYCHAIN_PATH=$KEYCHAIN_PATH" >> "$GITHUB_ENV"

      - name: Build application
        run: pyinstaller trxasviewer.spec

      - name: Sign application bundle
        run: |
          codesign \
            --force \
            --deep \
            --options runtime \
            --timestamp \
            --entitlements packaging/macos/entitlements.plist \
            --sign "$SIGNING_IDENTITY" \
            "dist/trxasviewer.app"

      - name: Verify application signature
        run: |
          codesign --verify --deep --strict --verbose=2 "dist/trxasviewer.app"
          codesign --display --verbose=4 "dist/trxasviewer.app"

      - name: Notarize and staple app bundle
        env:
          APPLE_ID: ${{ secrets.APPLE_ID }}
          APPLE_APP_PASSWORD: ${{ secrets.APPLE_APP_PASSWORD }}
          APPLE_TEAM_ID: ${{ vars.APPLE_TEAM_ID }}
        run: |
          ditto -c -k --keepParent "dist/trxasviewer.app" "dist/trxasviewer.zip"

          xcrun notarytool submit "dist/trxasviewer.zip" \
            --apple-id "$APPLE_ID" \
            --password "$APPLE_APP_PASSWORD" \
            --team-id "$APPLE_TEAM_ID" \
            --wait

          xcrun stapler staple "dist/trxasviewer.app"
          rm -f "dist/trxasviewer.zip"

      - name: Smoke test app launches
        run: |
          "dist/trxasviewer.app/Contents/MacOS/trxasviewer" &
          APP_PID=$!
          sleep 8
          if kill -0 $APP_PID 2>/dev/null; then
            echo "Smoke test passed: app is running after 8s"
            kill $APP_PID
          else
            wait $APP_PID || true
            echo "Smoke test FAILED: app exited early"
            exit 1
          fi

      - name: Create DMG
        run: |
          mkdir -p dmg-root
          cp -R "dist/trxasviewer.app" dmg-root/
          ln -s /Applications dmg-root/Applications

          hdiutil create \
            -volname "trxasviewer" \
            -srcfolder dmg-root \
            -format UDZO \
            -ov \
            "dist/trxasviewer.dmg"

      - name: Sign DMG
        run: |
          codesign \
            --force \
            --timestamp \
            --sign "$SIGNING_IDENTITY" \
            "dist/trxasviewer.dmg"

      - name: Notarize and staple DMG
        env:
          APPLE_ID: ${{ secrets.APPLE_ID }}
          APPLE_APP_PASSWORD: ${{ secrets.APPLE_APP_PASSWORD }}
          APPLE_TEAM_ID: ${{ vars.APPLE_TEAM_ID }}
        run: |
          xcrun notarytool submit "dist/trxasviewer.dmg" \
            --apple-id "$APPLE_ID" \
            --password "$APPLE_APP_PASSWORD" \
            --team-id "$APPLE_TEAM_ID" \
            --wait

          xcrun stapler staple "dist/trxasviewer.dmg"
          xcrun stapler validate "dist/trxasviewer.dmg"

      - name: Check Gatekeeper
        run: |
          spctl \
            --assess \
            --type open \
            --context context:primary-signature \
            --verbose=4 \
            "dist/trxasviewer.dmg"

      - name: Rename DMG with version
        run: |
          TAG="${{ github.event_name == 'push' && github.ref_name || github.event.inputs.version_tag }}"
          mv "dist/trxasviewer.dmg" "dist/trxasviewer-${TAG}-macos.dmg"

      - name: Upload macOS dmg artifact
        uses: actions/upload-artifact@v7
        with:
          name: macos-dmg
          path: dist/trxasviewer-*-macos.dmg
          retention-days: 14

      - name: Delete temporary keychain
        if: always()
        run: |
          if [ -n "${KEYCHAIN_PATH:-}" ]; then
            security delete-keychain "$KEYCHAIN_PATH" || true
          fi

  github-release:
    name: Publish GitHub Release
    needs: [windows-build, linux-appimage-build, macos-build]
    if: |
      github.event_name == 'push' &&
      !cancelled() &&
      needs.windows-build.result == 'success' &&
      needs.linux-appimage-build.result == 'success'
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - name: Download Windows executable artifact
        uses: actions/download-artifact@v8
        with:
          name: windows-exe
          path: dist/

      - name: Download Linux AppImage artifact
        uses: actions/download-artifact@v8
        with:
          name: linux-appimage
          path: dist/

      - name: Download macOS dmg artifact
        if: needs.macos-build.result == 'success'
        uses: actions/download-artifact@v8
        with:
          name: macos-dmg
          path: dist/

      - name: Create/update GitHub Release
        uses: softprops/action-gh-release@v3
        with:
          tag_name: ${{ github.ref_name }}
          name: "trxasviewer ${{ github.ref_name }}"
          generate_release_notes: true
          files: |
            dist/trxasviewer-*-windows.exe
            dist/trxasviewer-*-x86_64.AppImage
            dist/trxasviewer-*-macos.dmg
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/packaging/test_build_releases_workflow.py -v`
Expected: PASS

- [ ] **Step 5: Run the full packaging test suite together**

Run: `pytest tests/packaging/ -v`
Expected: All tests from Tasks 1–6 PASS.

- [ ] **Step 6: Commit**

```bash
git add .github/workflows/build-releases.yml tests/packaging/test_build_releases_workflow.py
git commit -m "feat: add build-releases workflow for Windows/Linux/macOS executables"
```

---

## After all tasks: first live verification (not automatable from here)

This plan's tests confirm the spec/scripts/workflow are structurally correct without
needing PyInstaller installed or all three OSes. The real test is a live GitHub
Actions run:

1. Push the six commits above to a branch and open a PR (or push to `mc_dev` per
   existing convention), then trigger `build-releases.yml` via **Actions → Build GUI
   releases → Run workflow** (`workflow_dispatch`) rather than pushing a tag first.
2. Confirm all three build jobs succeed and their smoke tests pass.
3. For `macos-build` specifically, confirm in the log: `security find-identity` shows
   the Developer ID Application identity, `codesign --verify` passes, `notarytool`
   reports `status: Accepted`, and the final `spctl --assess` passes.
4. Only after a clean manual run, push a real `v*` tag and confirm `github-release`
   creates a GitHub Release with all three files attached.
5. If PyInstaller fails to freeze any dependency (most likely candidates: `h5py`'s
   bundled HDF5 libraries, or a `matplotlib`/`pyqtgraph`/`scienceplots` runtime data
   file PyInstaller's static analysis misses), fix it by adding to `trxasviewer.spec`'s
   `datas`/`hiddenimports`/`excludes` — not by restructuring the workflow.

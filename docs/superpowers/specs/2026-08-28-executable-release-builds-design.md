# Single-File Executable Releases — Design Spec

**Date:** 2026-08-28
**Scope:** New GitHub Actions workflow that builds and publishes Windows/Linux/macOS GUI
executables on tag push. No changes to the existing sdist/wheel workflow or to
application code.
**Reference implementation:** `pySimpleMask_development`'s
`.github/workflows/build-releases.yml` / `pysimplemask.spec` / `packaging/`.

---

## Problem

`trxasviewer` currently has no distributable end-user artifact — installing it means
setting up a Python/conda environment with the right dependencies on each platform.
`.github/workflows/autobuild.yml` builds an sdist/wheel on any tag push but only
uploads it as a workflow artifact (no PyPI publish, no GitHub Release).

This spec adds a second, independent workflow that builds a single-file distributable
per platform — a Windows `.exe`, a Linux `.AppImage`, and a signed/notarized macOS
`.dmg` — and publishes them as a GitHub Release whenever a `v*` tag is pushed, using
the same PyInstaller-based approach already proven in `pySimpleMask_development`.

**Non-goals / explicitly out of scope for this pass:**
- PyPI publishing — not requested; `autobuild.yml` stays as-is, no `publish.yml` added.
- Smoke-testing the `model` subcommand GUI in CI — only the default `view` launch gets
  a CI smoke test; extending to `model` is a small, separate follow-up.
- Universal2 (arm64 + x86_64) macOS builds — `macos-14` runners are Apple Silicon;
  arm64-only matches the precedent in `pySimpleMask_development`.
- A self-hosted Windows runner with real GPU/display — `windows-latest` gives a
  headless-only smoke test, same caveat as the reference implementation.

## Architecture

### Where this lives

New workflow `.github/workflows/build-releases.yml`, triggered on:
```yaml
on:
  push:
    tags: ["v*"]
  workflow_dispatch:
    inputs:
      version_tag:
        description: "Tag to use for artifact naming on a manual run"
        required: true
        default: "v0.0.0-dev"
```
The `v*` pattern matches this repo's current tag convention (`v0.5.0`, `v0.5.1`,
after an earlier bare `0.x.y` scheme). The `workflow_dispatch.inputs.version_tag`
declaration is a small correction over the reference implementation, whose
`build-releases.yml` reads `github.event.inputs.version_tag` without ever declaring
that input — on a manual dispatch there this evaluates to an empty string and
artifacts get named e.g. `pySimpleMask--windows.exe`. Declaring the input here avoids
that.

`.github/workflows/autobuild.yml` (sdist/wheel, any tag, no publish, no executables)
is untouched and keeps running independently, per your choice to keep both workflows.

### Jobs

1. **`windows-build`** (`windows-latest`) — onefile `.exe` via PyInstaller, smoke
   test, upload artifact.
2. **`linux-appimage-build`** (`ubuntu-latest`, `container: rockylinux:9`) — onedir
   PyInstaller build wrapped into an AppImage, smoke test, upload artifact. Building
   inside RockyLinux 9 (rather than directly on `ubuntu-latest`) targets an older
   glibc baseline so the AppImage stays runnable on older RHEL/CentOS-family Linux
   installs — the kind of system common at a synchrotron beamline — rather than only
   working on bleeding-edge Ubuntu.
3. **`macos-build`** (`macos-14`, `environment: macos-signing`) — PyInstaller onedir
   build wrapped into `trxasviewer.app`, codesigned with a Developer ID Application
   certificate, notarized, stapled, packaged into a `.dmg`, Gatekeeper-checked, smoke
   tested, uploaded.
4. **`github-release`** (`ubuntu-latest`) — `needs: [windows-build,
   linux-appimage-build, macos-build]`, but its `if:` only hard-requires
   `windows-build` and `linux-appimage-build` to have succeeded; the macOS `.dmg` is
   downloaded and attached only if `macos-build` also succeeded. This keeps a tag push
   always producing a Windows+Linux release even if the macOS job has a one-off
   failure (e.g. a transient notarization outage) — signing secrets are already
   provisioned (see below), so this is now a safety net rather than a hard requirement
   for a usable release.

### Packaging entry point

`packaging/entrypoint.py`:
```python
import multiprocessing
from trxasviewer.cli import main

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
```
`freeze_support()` is required here specifically (the reference implementation's
entrypoint doesn't need it): `gui/control/workers.py`'s `CacheWorker` and
`core/fitting.py`'s `global_fit_kinetic_model` both spawn multiprocessing worker
processes, and a frozen Windows executable without `freeze_support()` can relaunch
itself in a loop the moment a worker spawns.

Because `cli.main()` already inserts the `view` subcommand when none is given,
double-clicking the built `.exe` / `.app` / `.AppImage` with no arguments launches the
viewer GUI directly. Running the executable from a terminal with a trailing `model`
argument launches the kinetic modeler instead — one binary, both GUIs, matching how
the installed `trxasviewer` console script already behaves.

### `trxasviewer.spec` (repo root)

Same three-branch shape as `pysimplemask.spec`:
- **win32**: onefile `EXE`, icon `packaging/icon.ico`.
- **linux**: onedir `EXE` + `COLLECT` (the AppImage build wraps this directory).
- **else (macOS)**: onedir `EXE` + `COLLECT` wrapped in `BUNDLE()` →
  `trxasviewer.app`, `bundle_identifier="gov.anl.aps.trxasviewer"`,
  `codesign_identity=None` (the workflow signs explicitly afterward with
  `codesign --deep --options runtime`, matching the reference implementation's
  rationale for not relying on PyInstaller's shallower built-in signing).

`hiddenimports` lists every `trxasviewer.*` submodule explicitly (`core.array_ops`,
`core.constants`, `core.dataset`, `core.file_io`, `core.fitting`, `core.graph`,
`core.io`, `core.plot`, `core.result`, `core.utilities`, `gui.control.viewer_controller`,
`gui.control.workers`, `gui.model.viewer_model`, `gui.view.generated_ui`,
`gui.view.pg_plot`, `gui.view.viewer_view`, `gui.view.widgets`,
`modeling_gui.generated_modeling_ui`, `modeling_gui.kinetics_optimizer`,
`modeling_gui.trxas_modeling`, `cli`) — PyInstaller's static analysis doesn't always
walk every import path a PySide6 app takes at runtime, so the explicit list follows
the reference implementation's belt-and-suspenders approach rather than trusting
auto-detection alone.

`excludes`: `pytest`, `coverage`, `setuptools`, `pip`, `wheel` (matches reference —
these are dev-only and safe to drop from the frozen build).

No `.ui` files need to be bundled as `datas` — both `viewer.ui` and `modeling.ui` are
Qt Designer sources only; the app imports the pre-generated `generated_ui.py` /
`generated_modeling_ui.py` at runtime, never the `.ui` files themselves.

### Icon

`packaging/icon.png` — your supplied 512×512 RGBA PNG, committed as-is.
`packaging/icon.ico` — multi-resolution (16/32/48/256), generated once locally via
Pillow and committed as a static binary asset, same as the reference implementation's
`packaging/icon.ico`.
`packaging/macos/make_icns.sh` — generates `packaging/macos/icon.icns` at build time
on the macOS runner via `sips`/`iconutil` (macOS-only tools, so generated in CI rather
than committed).

### Linux packaging

`packaging/linux/AppRun`, `packaging/linux/trxasviewer.desktop`
(`Name=TrXASViewer`, `Exec=trxasviewer`, `Icon=trxasviewer`, `Categories=Science;`),
and `packaging/linux/build-appimage.sh` (same structure as the reference script,
names adapted). Since this repo has no `resources/logo.svg` equivalent,
`build-appimage.sh` copies `packaging/icon.png` → `dist/AppDir/trxasviewer.png`
directly for the desktop icon, instead of the reference's SVG-copy step.

### macOS signing — already provisioned

The `macos-signing` GitHub Environment was created on `AdvancedPhotonSource/trxasviewer`
this session, with secrets `BUILD_CERTIFICATE_BASE64`, `P12_PASSWORD`,
`KEYCHAIN_PASSWORD`, `APPLE_ID`, `APPLE_APP_PASSWORD` and variable `APPLE_TEAM_ID` —
the same Developer ID Application certificate already used for `pySimpleMask` and
`pyxpcsviewer`, plus a `trxasviewer`-labeled app-specific password generated fresh so
it can be revoked independently of the other two projects' credentials.

The `macos-build` job's steps mirror the reference implementation's `macos-build` job
verbatim: import certificate into a temporary keychain → `pyinstaller trxasviewer.spec`
→ `codesign --force --deep --options runtime --timestamp --entitlements
packaging/macos/entitlements.plist` → verify signature → smoke test the `.app`'s
embedded binary → build `.dmg` → sign `.dmg` → notarize+staple both `.app` and `.dmg`
→ `spctl` Gatekeeper check → rename to `trxasviewer-<tag>-macos.dmg` → upload →
delete the temporary keychain (`if: always()`).

New file `packaging/macos/entitlements.plist` — identical content to the reference
implementation's (`com.apple.security.cs.allow-unsigned-executable-memory` and
`com.apple.security.cs.disable-library-validation`), both near-universal requirements
for notarizing a PyInstaller bundle containing compiled extensions (numpy, scipy,
PySide6's Qt frameworks) that aren't all signed by the same Team ID.

### `pyproject.toml` change

Add:
```toml
[project.optional-dependencies]
pyinstaller = ["pyinstaller>=6.21"]
```

### `.gitignore` change

The existing blanket `*.spec` rule (added by a generic Python `.gitignore` template)
would silently exclude `trxasviewer.spec`. Add `!trxasviewer.spec` immediately after
it so the spec is tracked, same as `pysimplemask.spec` is in the reference repo.

### New test: `tests/packaging/test_trxasviewer_spec.py`

Mirrors the reference implementation's `test_pysimplemask_spec.py`: `exec()`s
`trxasviewer.spec`'s source with stand-in `Analysis`/`PYZ`/`EXE`/`BUNDLE`/`COLLECT`
recorder objects, patching `sys.platform` per case, and asserts:
- `darwin` → `EXE` has `codesign_identity=None`, `BUNDLE` wraps the `COLLECT` result
  with `name="trxasviewer.app"` and the right `bundle_identifier`/icon.
- `win32` → no `BUNDLE`/`COLLECT` call, `EXE` icon path ends with
  `packaging/icon.ico`.
- `linux` → `COLLECT` called, no `BUNDLE`.

This runs in the existing `pytest tests/` suite without needing PyInstaller installed
or access to all three OSes, giving real regression coverage for the spec's branching
logic between now and the first live Actions run.

## Files touched

**New:**
- `.github/workflows/build-releases.yml`
- `trxasviewer.spec`
- `packaging/entrypoint.py`
- `packaging/icon.png`
- `packaging/icon.ico`
- `packaging/macos/make_icns.sh`
- `packaging/macos/entitlements.plist`
- `packaging/linux/AppRun`
- `packaging/linux/trxasviewer.desktop`
- `packaging/linux/build-appimage.sh`
- `tests/packaging/test_trxasviewer_spec.py`

**Edited:**
- `pyproject.toml` — add `pyinstaller` optional-dependency group.
- `.gitignore` — carve out `!trxasviewer.spec`.

**Unchanged:**
- `.github/workflows/autobuild.yml`

## Error handling

- Missing/invalid certificate → the cert-import step fails explicitly rather than
  silently producing an unsigned build (matches reference implementation).
- Bad signature → caught by `codesign --verify --deep --strict` before spending a
  notarization round-trip.
- `notarytool submit --wait` surfaces Apple's rejection reason directly in the log if
  notarization fails.
- Temporary keychain cleanup runs `if: always()`.
- A `macos-build` failure no longer blocks the Windows/Linux release (see
  `github-release`'s `if:` above) — it did not block them before either, since secrets
  weren't provisioned until this session, but the guard is kept as ongoing protection
  against any future one-off notarization failure.

## Testing

This can't be fully verified without a live GitHub Actions run — there's no macOS/
Windows runner or Apple notarization service reachable from this environment. What's
checkable now, before any push:
- `pytest tests/packaging/test_trxasviewer_spec.py` — spec branch logic.
- `trxasviewer.spec` is valid Python (parses/execs without error).
- Workflow YAML is valid (`actionlint` or a dry read).
- Shell scripts (`build-appimage.sh`, `make_icns.sh`) are syntactically valid
  (`bash -n`).

Real verification is triggering `build-releases.yml` via `workflow_dispatch` first
(rather than a real tag) and confirming: the Windows `.exe` and Linux `.AppImage`
both launch and stay alive through the smoke test, `codesign --verify` passes on the
`.app`, `notarytool` reports `status: Accepted`, and `spctl --assess` passes on the
`.dmg`. Only after a clean manual run should a real `v*` tag be pushed.

## Open risks

- **PyInstaller freezing this dependency set cleanly is not guaranteed on the first
  try.** `numpy`, `PySide6`, `pyqtgraph`, `matplotlib`, `scienceplots`, `scipy`,
  `h5py`, `pandas`, and `psutil` together are a wide surface; likely trouble spots if
  the first CI run fails are `h5py`'s bundled HDF5 shared libraries and any
  runtime-only data files pulled in by `matplotlib`/`pyqtgraph`/`scienceplots`. Fixes
  for issues found here are additions to `trxasviewer.spec`'s `datas`/`hiddenimports`,
  not changes to the workflow's structure.
- **`packaging/icon.ico`'s visual correctness** (does it actually look right at 16px/
  32px, not just "technically a valid multi-res ICO") can only be confirmed by
  opening the built `.exe` on Windows or viewing the file in an icon viewer — not
  verifiable in this environment.
- **Entitlements sufficiency**: the two entitlements in `entitlements.plist` are the
  common baseline for PyInstaller/PySide6 apps, per the reference implementation's own
  spec, but if the first live run's notarization or Gatekeeper step fails, the next
  step is very likely tightening/loosening that file rather than restructuring the
  workflow.

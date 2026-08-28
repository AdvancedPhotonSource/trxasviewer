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

# Import PyInstaller (and its `compat` submodule) now, while sys.platform is
# still the real value, so it's cached in sys.modules before any test
# monkeypatches sys.platform. PyInstaller.compat runs OS-detection code at
# import time (e.g. probing win32ctypes / platform.mac_ver()) keyed off
# sys.platform; re-triggering that under a faked platform on a real Linux
# host raises errors unrelated to the spec logic under test.
import PyInstaller.utils.hooks  # noqa: F401

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


def test_analysis_bundles_package_metadata(monkeypatch):
    namespace, *_ = _run_spec(monkeypatch, "linux")
    assert namespace["a"].kwargs["datas"]


def test_windows_branch_disables_windowed_traceback(monkeypatch):
    _, exe_rec, _, _ = _run_spec(monkeypatch, "win32")

    _, exe_kwargs = exe_rec.calls[0]
    assert exe_kwargs["disable_windowed_traceback"] is True


def test_linux_and_macos_branches_keep_windowed_traceback_dialog(monkeypatch):
    _, linux_exe_rec, _, _ = _run_spec(monkeypatch, "linux")
    _, linux_exe_kwargs = linux_exe_rec.calls[0]
    assert linux_exe_kwargs["disable_windowed_traceback"] is False

    _, macos_exe_rec, _, _ = _run_spec(monkeypatch, "darwin")
    _, macos_exe_kwargs = macos_exe_rec.calls[0]
    assert macos_exe_kwargs["disable_windowed_traceback"] is False


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

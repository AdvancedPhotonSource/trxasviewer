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

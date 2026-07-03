# Build with:  pyinstaller RoyalSecrets.spec
#
# Produces a single-file, windowed (no console) exe. The `assets/` folder
# is bundled read-only inside the exe and extracted to a temp folder at
# runtime (core/config.py's ASSETS_DIR already knows to look there when
# frozen). The `data/` folder (registrations.db) is deliberately NOT
# bundled here — core/database.py creates it fresh next to the exe on
# first run, so registrations persist across runs and across rebuilds.

# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('assets', 'assets')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='RoyalSecrets',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,        # no terminal window — this is a kiosk app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,             # drop an .ico path here later if you want one
)

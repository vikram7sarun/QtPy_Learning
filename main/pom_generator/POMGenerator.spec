# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Codebase\\Personal\\QtPy_Learning\\main\\pom_generator\\pom_generator.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Codebase\\Personal\\QtPy_Learning\\main\\pom_generator\\temp_playwright\\playwright', 'playwright')],
    hiddenimports=['playwright', 'playwright.sync_api', 'PyQt5', 'PyQt5.QtWidgets', 'PyQt5.QtGui', 'PyQt5.QtCore'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='POMGenerator',
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
    icon=['app_icon.ico'],
)

# -*- mode: python ; coding: utf-8 -*-

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    Analysis = PYZ = EXE = COLLECT = lambda *args, **kwargs: lambda *args, **kwargs: None
    DISTPATH = SPECPATH = str()

import os
import shutil
from PyInstaller.utils.hooks import collect_submodules

a_main = Analysis(
    ['ui.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
main_pyz = PYZ(a_main.pure)

main_exe = EXE(
    main_pyz,
    a_main.scripts,
    [],
    exclude_binaries=True,
    name='main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

a_mathspace = Analysis(
    ['mathspace.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=(
        collect_submodules('selenium') + 
        collect_submodules('selene')
    ),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
mathspace_pyz = PYZ(a_mathspace.pure)

mathspace_exe = EXE(
    mathspace_pyz,
    a_mathspace.scripts,
    [],
    exclude_binaries=True,
    name='mathspace',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    main_exe,
    a_main.binaries,
    a_main.datas,
    mathspace_exe,
    a_mathspace.binaries,
    a_mathspace.datas,
    [('./README.md', './README.md', 'DATA')],
    strip=False,
    upx=True,
    upx_exclude=[],
    name='main',
)

dest_dir = os.path.join(DISTPATH, 'main') 
src_readme = os.path.join(SPECPATH, 'README.md')

if os.path.exists(src_readme):
    shutil.copy(src_readme, dest_dir)
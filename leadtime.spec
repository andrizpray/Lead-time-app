# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for LeadTime App.
Build: pyinstaller leadtime.spec
"""

import os
import sys
from pathlib import Path

block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets', 'assets'),
    ],
    hiddenimports=[
        'PySide6.QtCharts',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6.QtPrintSupport',
        'peewee',
        'pandas',
        'openpyxl',
        'reportlab',
        'src.core',
        'src.core.database',
        'src.core.models',
        'src.core.report',
        'src.core.settings',
        'src.ui',
        'src.ui.main_window',
        'src.ui.dashboard',
        'src.ui.do_form',
        'src.ui.do_table',
        'src.ui.import_wizard',
        'src.ui.report_widget',
        'src.ui.settings_widget',
        'src.utils',
        'src.utils.excel_handler',
        'src.utils.excel_exporter',
        'src.utils.pdf_generator',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'scipy',
        'PIL.ImageQt',
        'notebook',
        'IPython',
        'tkinter',
    ],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='LeadTimeApp',
    icon='assets/icon.ico',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # GUI app, no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    contents_directory='.',
    embed_manifest=True,
)

# Also create a one-file version (optional)
# coll = COLLECT(
#     exe,
#     a.binaries,
#     a.zipfiles,
#     a.datas,
#     strip=False,
#     upx=True,
#     upx_exclude=[],
#     name='LeadTimeApp',
# )

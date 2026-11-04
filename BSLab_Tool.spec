# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from PyInstaller.utils.hooks import collect_data_files, copy_metadata, collect_dynamic_libs

block_cipher = None

# CustomTkinter & mtkclient assets, themes, and binaries
datas = collect_data_files('customtkinter')
datas += copy_metadata('customtkinter')
datas += collect_data_files('mtkclient')

# Resources & Drivers bundled into distribution
datas += [
    ('resources', 'resources'),
    ('drivers', 'drivers'),
]

binaries = collect_dynamic_libs('mtkclient')

hidden_imports = [
    'customtkinter',
    'tkinter',
    'tkinter.ttk',
    'tkinter.filedialog',
    'tkinter.messagebox',
    'serial',
    'serial.tools.list_ports',
    'usb.core',
    'usb.backend.libusb1',
    'usb.util',
    'cryptography',
    'PIL',
    'PIL.Image',
    'PIL.ImageTk',
    'PIL._tkinter_finder',
    'engines',
    'engines.huawei',
    'engines.huawei.kirin_engine',
    'engines.samsung',
    'engines.samsung.samsung_modem',
    'engines.samsung.odin_protocol',
    'engines.samsung.samsung_flash',
    'engines.unpackers',
    'engines.unpackers.payload_unpacker',
    'engines.qualcomm',
    'engines.qualcomm.xml_parser',
    'engines.qualcomm.sahara',
    'engines.qualcomm.firehose',
    'engines.qualcomm.qcn_engine',
    'engines.mtk',
    'engines.mtk.brom',
    'engines.mtk.da_handler',
    'engines.unisoc',
    'engines.spd',
    'engines.spd.spd_protocol',
    'engines.unisoc.nv_engine',
    'mtk',
    'mtk.brom_engine',
    'mtk.flasher',
    'mtk.meta_engine',
    'core',
    'core.cloud_sync',
    'core.driver_manager',
    'core.model_repository',
    'core.path_utils',
    'core.sound_manager',
    'core.logger',
    'core.telemetry',
    'core.security_guard',
    'core.i18n',
    'core.port_watcher',
    'core.device_detector',
    'core.auth_manager',
    'core.model_database',
    'config',
    'config.settings_manager',
    'ui',
    'ui.theme',
    'ui.model_selector',
    'ui.main_window',
    'ui.components.header_bar',
    'ui.components.module_ribbon',
    'ui.components.console_panel',
    'ui.components.status_bar',
    'ui.views.mtk_view',
    'ui.views.qc_view',
    'ui.views.spd_view',
    'ui.views.fastboot_view',
    'ui.views.tp_view',
    'ui.views.unpacker_view',
    'ui.views.samsung_view',
    'ui.views.ai_analyzer_view',
    'ui.views.smart_hub_view',
    'ui.dialogs.driver_dialog',
    'ui.dialogs.testpoint_dialog',
    'ui.dialogs.login_window',
    'engines.testpoints',
    'engines.testpoints.tp_database',
    'urllib.request',
    'urllib.error',
    'uuid',
]

a = Analysis(
    ['main.py'],
    pathex=['C:\\BSLab_Tool'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['unittest', 'pytest', 'tests'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='BSLab_Tool',
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
    icon='resources\\icons\\app_icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='BSLab_Tool',
)

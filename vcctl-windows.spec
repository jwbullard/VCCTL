# -*- mode: python ; coding: utf-8 -*-
"""
VCCTL PyInstaller Specification File
Cross-platform packaging for Windows, macOS, and Linux
"""

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Platform detection
IS_WINDOWS = sys.platform == 'win32'
IS_MACOS = sys.platform == 'darwin'
IS_LINUX = sys.platform.startswith('linux')

# Platform-specific binary executables
if IS_WINDOWS:
    platform_binaries = [
        ('backend/bin-windows/genmic.exe', 'backend/bin/'),
        ('backend/bin-windows/disrealnew.exe', 'backend/bin/'),
        ('backend/bin-windows/elastic.exe', 'backend/bin/'),
        ('backend/bin-windows/genaggpack.exe', 'backend/bin/'),
        ('backend/bin-windows/perc3d.exe', 'backend/bin/'),
        ('backend/bin-windows/stat3d.exe', 'backend/bin/'),
        ('backend/bin-windows/oneimage.exe', 'backend/bin/'),
        ('backend/bin-windows/aggvrml.exe', 'backend/bin/'),
        ('backend/bin-windows/apstats.exe', 'backend/bin/'),
        ('backend/bin-windows/chlorattack3d.exe', 'backend/bin/'),
        ('backend/bin-windows/distfapart.exe', 'backend/bin/'),
        ('backend/bin-windows/distfarand.exe', 'backend/bin/'),
        ('backend/bin-windows/dryout.exe', 'backend/bin/'),
        ('backend/bin-windows/hydmovie.exe', 'backend/bin/'),
        ('backend/bin-windows/image100.exe', 'backend/bin/'),
        ('backend/bin-windows/leach3d.exe', 'backend/bin/'),
        ('backend/bin-windows/measagg.exe', 'backend/bin/'),
        ('backend/bin-windows/onepimage.exe', 'backend/bin/'),
        ('backend/bin-windows/perc3d-leach.exe', 'backend/bin/'),
        ('backend/bin-windows/poredist3d.exe', 'backend/bin/'),
        ('backend/bin-windows/rand3d.exe', 'backend/bin/'),
        ('backend/bin-windows/sulfattack3d.exe', 'backend/bin/'),
        ('backend/bin-windows/thames2vcctl.exe', 'backend/bin/'),
        ('backend/bin-windows/thames2vcctlcorr.exe', 'backend/bin/'),
        ('backend/bin-windows/totsurf.exe', 'backend/bin/'),
        ('backend/bin-windows/transport.exe', 'backend/bin/'),
        # Add DLL dependencies for C executables
        ('backend/build-windows/Release/getopt.dll', 'backend/bin/'),
        ('backend/build-windows/Release/libpng16.dll', 'backend/bin/'),
        ('backend/build-windows/Release/zlib1.dll', 'backend/bin/'),
    ]
elif IS_MACOS:
    platform_binaries = [
        ('backend/bin/genmic', 'backend/bin/'),
        ('backend/bin/disrealnew', 'backend/bin/'),
        ('backend/bin/elastic', 'backend/bin/'),
        ('backend/bin/genaggpack', 'backend/bin/'),
        ('backend/bin/perc3d', 'backend/bin/'),
        ('backend/bin/stat3d', 'backend/bin/'),
        ('backend/bin/oneimage', 'backend/bin/'),
    ]
elif IS_LINUX:
    platform_binaries = [
        ('backend/bin-linux/genmic', 'backend/bin/'),
        ('backend/bin-linux/disrealnew', 'backend/bin/'),
        ('backend/bin-linux/elastic', 'backend/bin/'),
        ('backend/bin-linux/genaggpack', 'backend/bin/'),
        ('backend/bin-linux/perc3d', 'backend/bin/'),
        ('backend/bin-linux/stat3d', 'backend/bin/'),
        ('backend/bin-linux/oneimage', 'backend/bin/'),
    ]
else:
    platform_binaries = []

# Add GTK DLLs on Windows (MSYS2)
if IS_WINDOWS:
    import glob
    mingw_bin = r'C:\msys64\mingw64\bin'
    # Collect all GTK-related DLLs
    gtk_dlls = glob.glob(os.path.join(mingw_bin, 'lib*.dll'))
    for dll in gtk_dlls:
        platform_binaries.append((dll, '.'))

# Collect GTK/GI data files
gi_typelibs = collect_data_files('gi')

# Add Windows-specific GioWin32 typelib (not collected automatically)
if IS_WINDOWS:
    giowin32_typelib = r'C:\msys64\mingw64\lib\girepository-1.0\GioWin32-2.0.typelib'
    if os.path.exists(giowin32_typelib):
        gi_typelibs.append((giowin32_typelib, 'gi_typelibs'))

    # Add GLib typelib (may not be collected automatically on some systems)
    glib_typelib = r'C:\msys64\mingw64\lib\girepository-1.0\GLib-2.0.typelib'
    if os.path.exists(glib_typelib):
        gi_typelibs.append((glib_typelib, 'gi_typelibs'))

# Hidden imports for GTK and other dependencies
hiddenimports = [
    'gi',
    'gi.repository.Gtk',
    'gi.repository.Gdk',
    'gi.repository.GLib',
    'gi.repository.Gio',
    'gi.repository.GObject',
    'gi.repository.Pango',
    'gi.repository.GdkPixbuf',
    'sqlalchemy',
    'sqlalchemy.ext.declarative',
    'sqlalchemy.orm',
    'pandas',
    'numpy',
    'matplotlib',
    'PIL',
    'yaml',
    'psutil',
    'app',
    'app.application',
]

# Attempt to add pyvista if available (optional dependency)
try:
    import pyvista
    hiddenimports.extend([
        'pyvista',
        'vtk',
        'vtkmodules',
        'vtkmodules.all',
        'vtkmodules.util',
        'vtkmodules.util.numpy_support',
        'vtkmodules.vtkCommonCore',
        'vtkmodules.vtkCommonDataModel',
        'vtkmodules.vtkRenderingCore',
        'vtkmodules.vtkFiltersCore',
    ])
except ImportError:
    pass

# Attempt to add pydantic if available (optional dependency)
try:
    import pydantic
    hiddenimports.append('pydantic')
except ImportError:
    pass

# jaraco.text is needed on some systems
try:
    import jaraco.text
    hiddenimports.append('jaraco.text')
except ImportError:
    pass

block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=['src'],  # Add src directory so app module can be found
    binaries=platform_binaries,
    datas=[
        ('vcctl-docs/site', 'docs/site'),  # Include built documentation
        ('src/app/resources', 'app/resources'),  # Include application resources
        ('icons', 'icons'),  # Include Carbon icons
        ('src/data', 'data'),  # Include database and data files
        ('particle_shape_set.tar.gz', 'data/'),  # Include compressed particle shape data (extracted on first launch)
        ('aggregate.tar.gz', 'data/'),  # Include compressed aggregate shape data (extracted on first launch)
        ('colors', 'colors'),  # Include phase colors CSV file
    ] + gi_typelibs,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='VCCTL',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Enable console window for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='src/app/resources/icon.ico' if IS_WINDOWS and os.path.exists('src/app/resources/icon.ico') else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='VCCTL',
)

# macOS .app bundle (only on macOS)
if IS_MACOS:
    app = BUNDLE(
        coll,
        name='VCCTL.app',
        icon='src/app/resources/icon.icns' if os.path.exists('src/app/resources/icon.icns') else None,
        bundle_identifier='edu.tamu.vcctl',
        info_plist={
            'CFBundleName': 'VCCTL',
            'CFBundleDisplayName': 'VCCTL',
            'CFBundleVersion': '10.0.0',
            'CFBundleShortVersionString': '10.0.0',
            'NSHighResolutionCapable': True,
        },
    )

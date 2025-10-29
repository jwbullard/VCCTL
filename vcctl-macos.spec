#!/usr/bin/env python3
"""
PyInstaller specification file for VCCTL
Creates standalone executables for all platforms
"""

import os
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Get project root directory (SPECPATH is provided by PyInstaller)
project_root = Path(SPECPATH).absolute()
src_dir = project_root / "src"

# Pydantic will be handled by custom hooks in hooks/ directory

# Collect all app submodules to ensure everything is included
app_submodules = collect_submodules('app')

# Collect unittest submodules (required by scipy, but excluded by default)
unittest_submodules = collect_submodules('unittest')

# Analysis configuration
a = Analysis(
    ['src/main.py'],
    pathex=[
        str(src_dir),
        str(project_root)
    ],
    binaries=[
        # Include C executables for VCCTL operations
        ('backend/bin/genmic', 'backend/bin/'),
        ('backend/bin/disrealnew', 'backend/bin/'),
        ('backend/bin/elastic', 'backend/bin/'),
        ('backend/bin/genaggpack', 'backend/bin/'),
        ('backend/bin/perc3d', 'backend/bin/'),
        ('backend/bin/stat3d', 'backend/bin/'),
        ('backend/bin/oneimage', 'backend/bin/'),
    ],
    datas=[
        # Include MkDocs built documentation
        ('vcctl-docs/site/', 'docs/site/'),
        # Include application resources
        ('src/app/resources/', 'app/resources/'),
        # Include Carbon icons (2,371 SVG icons for UI)
        ('icons/carbon/', 'icons/carbon/'),
        # Include application icons
        ('icons/vcctl.icns', 'icons/'),
        ('icons/vcctl-icon-maroon.png', 'icons/'),
        # Include particle shape sets (~23,000 files, critical for microstructure generation)
        ('particle_shape_set/', 'particle_shape_set/'),
        # Include hydration parameters (required for initialization)
        ('backend/examples/parameters.csv', 'backend/examples/'),
        # Include seed database with default materials (for fresh installations)
        ('src/data/database/vcctl.db', 'data/database/'),
        # Include slag/alkali characterization files (for advanced cements)
        ('alkalichar.dat', '.'),
        ('slagchar.dat', '.'),
        # Include phase colors for visualization
        ('colors/', 'colors/'),
        # Include desktop entry
        ('vcctl-gtk.desktop', '.'),
    ],
    hiddenimports=[
        'gi',
        'gi.repository',
        'gi.repository.Gtk',
        'gi.repository.Gdk',
        'gi.repository.GObject',
        'gi.repository.Gio',
        'gi.repository.GLib',
        'gi.repository.Pango',
        'gi.repository.GdkPixbuf',
        'cairo',
        'sqlite3',
        'pkg_resources',
        'pkg_resources.py2_warn',
        'pydantic',
        'pydantic.deprecated',
        'pydantic.deprecated.decorator',
        'pydantic_core',
        'sqlalchemy',
        'sqlalchemy.ext',
        'sqlalchemy.ext.declarative',
        'alembic',
        'matplotlib',
        'numpy',
        'pandas',
        'PIL',
        'pyvista',
        'vtkmodules',
        'vtkmodules.all',
        'yaml',
        # Scientific computing - scipy and dependencies
        'scipy',
        'scipy.ndimage',
        'scipy.sparse',
        # Setuptools vendored dependencies
        'jaraco',
        'jaraco.text',
        'jaraco.functools',
        'jaraco.context',
        'more_itertools',
        # Application modules - use collect_submodules result
        *app_submodules,
        # unittest modules (required by scipy)
        *unittest_submodules,
    ],
    hookspath=['hooks'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'test',
        'tests',
        'distutils',
        'setuptools',
        'mypy',
        'mypy.api',
        'mypy.util',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# Filter out development packages
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# Executable configuration
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='vcctl',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # GUI application
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='src/app/resources/icons/vcctl.ico' if os.path.exists('src/app/resources/icons/vcctl.ico') else None,
)

# Collect all files for distribution
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='vcctl'
)

# macOS App Bundle configuration
if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='VCCTL.app',
        icon='icons/vcctl.icns',
        bundle_identifier='gov.nist.vcctl',
        version='10.0.0',
        info_plist={
            'CFBundleName': 'VCCTL',
            'CFBundleDisplayName': 'Virtual Cement and Concrete Testing Laboratory',
            'CFBundleVersion': '10.0.0',
            'CFBundleShortVersionString': '10.0.0',
            'CFBundleIdentifier': 'gov.nist.vcctl',
            'CFBundleExecutable': 'vcctl',
            'CFBundleIconFile': 'vcctl.icns',
            'CFBundlePackageType': 'APPL',
            'CFBundleSignature': 'VCCT',
            'NSHighResolutionCapable': True,
            'NSRequiresAquaSystemAppearance': False,
            'LSMinimumSystemVersion': '10.14',
            'LSApplicationCategoryType': 'public.app-category.education',
            'CFBundleDocumentTypes': [
                {
                    'CFBundleTypeName': 'VCCTL Project',
                    'CFBundleTypeExtensions': ['vcctl'],
                    'CFBundleTypeRole': 'Editor',
                    'CFBundleTypeIconFile': 'vcctl.icns',
                }
            ],
        }
    )
"""
Custom hook for gi.repository.Gio on Windows
Helps PyInstaller find GTK shared libraries in MSYS2
"""
import os
from PyInstaller.utils.hooks import collect_dynamic_libs

# Collect all GTK-related DLLs from MSYS2 mingw64/bin
binaries = []

# Add the MSYS2 mingw64/bin directory to look for DLLs
mingw_bin = r'C:\msys64\mingw64\bin'
if os.path.exists(mingw_bin):
    # Collect all DLLs that Gio might need
    gio_libs = [
        'libgio-2.0-0.dll',
        'libglib-2.0-0.dll',
        'libgobject-2.0-0.dll',
        'libgmodule-2.0-0.dll',
    ]

    for lib in gio_libs:
        lib_path = os.path.join(mingw_bin, lib)
        if os.path.exists(lib_path):
            binaries.append((lib_path, '.'))

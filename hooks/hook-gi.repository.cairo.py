"""
Custom hook for gi.repository.cairo on Windows
Helps PyInstaller find GTK shared libraries in MSYS2
"""
import os

# Collect all GTK-related DLLs from MSYS2 mingw64/bin
binaries = []

mingw_bin = r'C:\msys64\mingw64\bin'
if os.path.exists(mingw_bin):
    cairo_libs = [
        'libcairo-gobject-2.dll',
        'libcairo-2.dll',
        'libglib-2.0-0.dll',
        'libgobject-2.0-0.dll',
    ]

    for lib in cairo_libs:
        lib_path = os.path.join(mingw_bin, lib)
        if os.path.exists(lib_path):
            binaries.append((lib_path, '.'))

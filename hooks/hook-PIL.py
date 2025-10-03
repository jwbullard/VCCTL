"""
PyInstaller hook for PIL to fix GTK conflicts on macOS.

Excludes PIL's bundled dylibs that conflict with system GTK libraries.
"""

from PyInstaller.utils.hooks import collect_dynamic_libs

# Get all PIL dylibs
binaries = collect_dynamic_libs('PIL')

# Filter out conflicting dylibs (particularly libharfbuzz)
filtered_binaries = []
exclude_libs = ['libharfbuzz', 'libfreetype', 'libpng', 'libjpeg']

for binary_path, dest_folder in binaries:
    # Check if this binary should be excluded
    should_exclude = any(excl in binary_path for excl in exclude_libs)
    if not should_exclude:
        filtered_binaries.append((binary_path, dest_folder))

binaries = filtered_binaries

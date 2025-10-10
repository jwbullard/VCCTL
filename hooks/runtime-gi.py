"""
Runtime hook for GI/GTK on Windows
Adds MSYS2 bin directory to PATH so GTK libraries can be found
"""
import os
import sys

# Add the directory containing the packaged DLLs to PATH
if sys.platform == 'win32':
    if hasattr(sys, '_MEIPASS'):
        # Running in PyInstaller bundle
        os.environ['PATH'] = sys._MEIPASS + os.pathsep + os.environ.get('PATH', '')

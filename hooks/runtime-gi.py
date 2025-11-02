"""
Runtime hook for GI/GTK
Sets up environment for GTK to find libraries and typelibs
"""
import os
import sys

if hasattr(sys, '_MEIPASS'):
    # Running in PyInstaller bundle

    if sys.platform == 'win32':
        # Windows: Add the directory containing the packaged DLLs to PATH
        os.environ['PATH'] = sys._MEIPASS + os.pathsep + os.environ.get('PATH', '')

    elif sys.platform == 'darwin':
        # macOS: Set GI_TYPELIB_PATH to find typelibs in the bundle
        typelib_paths = [
            os.path.join(sys._MEIPASS, 'gi_typelibs'),
        ]
        os.environ['GI_TYPELIB_PATH'] = os.pathsep.join(typelib_paths)

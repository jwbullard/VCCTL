#!/usr/bin/env python3
"""
VCCTL Application Information and Metadata

Contains application constants, metadata, and resource paths.
"""

import os
from pathlib import Path

# Application metadata
APP_NAME = "VCCTL"
APP_ID = "edu.tamu.vcctl.gtk"
APP_VERSION = "10.0.0"
APP_TITLE = "Virtual Cement and Concrete Testing Laboratory"
APP_DESCRIPTION = "Desktop application for cement and concrete materials modeling"
APP_WEBSITE = "https://github.com/jwbullard/VCCTL-GTK"

# Organization info
ORG_NAME = "Texas A&M University"
ORG_WEBSITE = "https://www.tamu.edu/"

# Application paths
BASE_DIR = Path(__file__).parent.parent.parent
RESOURCES_DIR = BASE_DIR / "app" / "resources"
ICONS_DIR = RESOURCES_DIR / "icons"
DATA_DIR = BASE_DIR / "data"
MATERIALS_DIR = DATA_DIR / "materials"

# User data directory (persists across uninstalls/reinstalls)
# Use AppData\Local on Windows, ~/.local/share on Linux, ~/Library/Application Support on macOS
if os.name == 'nt':  # Windows
    USER_DATA_DIR = Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData' / 'Local')) / APP_NAME
elif os.name == 'posix' and os.uname().sysname == 'Darwin':  # macOS
    USER_DATA_DIR = Path.home() / 'Library' / 'Application Support' / APP_NAME
else:  # Linux
    USER_DATA_DIR = Path.home() / '.local' / 'share' / APP_NAME

# Database is stored in user data directory (NOT in application directory)
DATABASE_DIR = USER_DATA_DIR / "database"

# Ensure directories exist
for directory in [RESOURCES_DIR, ICONS_DIR, DATA_DIR, MATERIALS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Ensure user data directories exist (these persist across app updates)
for directory in [USER_DATA_DIR, DATABASE_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Copy seed database on first launch (if user database doesn't exist)
USER_DB_PATH = DATABASE_DIR / "vcctl.db"
SEED_DB_PATH = DATA_DIR / "database" / "vcctl.db"
if not USER_DB_PATH.exists() and SEED_DB_PATH.exists():
    import shutil
    shutil.copy2(SEED_DB_PATH, USER_DB_PATH)

# Icon paths (will be used when we have actual icon files)
ICON_PATHS = {
    'app_icon': ICONS_DIR / "vcctl-app.png",
    'app_icon_svg': ICONS_DIR / "vcctl-app.svg",
    'window_icon': ICONS_DIR / "vcctl-window.png"
}

# Application authors and contributors
AUTHORS = [
    "Texas A&M University",
    "Jeffrey W. Bullard",
    "VCCTL Development Team"
]

# License information
LICENSE_TEXT = """MIT License

Copyright (c) 2024 Texas A&M University

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE."""

def get_resource_path(resource_name: str) -> Path:
    """Get the full path to a resource file."""
    return RESOURCES_DIR / resource_name

def get_icon_path(icon_name: str) -> Path:
    """Get the full path to an icon file."""
    return ICONS_DIR / icon_name
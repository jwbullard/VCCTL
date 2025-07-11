#!/usr/bin/env python3
"""
VCCTL Application Information and Metadata

Contains application constants, metadata, and resource paths.
"""

import os
from pathlib import Path

# Application metadata
APP_NAME = "VCCTL"
APP_ID = "gov.nist.vcctl.gtk"
APP_VERSION = "1.0.0"
APP_TITLE = "Virtual Cement and Concrete Testing Laboratory"
APP_DESCRIPTION = "Desktop application for cement and concrete materials modeling"
APP_WEBSITE = "https://vcctl.nist.gov/"

# Organization info
ORG_NAME = "NIST Building and Fire Research Laboratory"
ORG_WEBSITE = "https://www.nist.gov/el/building-and-fire-research-laboratory-bfrl"

# Application paths
BASE_DIR = Path(__file__).parent.parent.parent
RESOURCES_DIR = BASE_DIR / "app" / "resources"
ICONS_DIR = RESOURCES_DIR / "icons"
DATA_DIR = BASE_DIR / "data"
DATABASE_DIR = DATA_DIR / "database"
MATERIALS_DIR = DATA_DIR / "materials"

# Ensure directories exist
for directory in [RESOURCES_DIR, ICONS_DIR, DATA_DIR, DATABASE_DIR, MATERIALS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Icon paths (will be used when we have actual icon files)
ICON_PATHS = {
    'app_icon': ICONS_DIR / "vcctl-app.png",
    'app_icon_svg': ICONS_DIR / "vcctl-app.svg",
    'window_icon': ICONS_DIR / "vcctl-window.png"
}

# Application authors and contributors
AUTHORS = [
    "NIST Building and Fire Research Laboratory",
    "VCCTL Development Team"
]

# License information
LICENSE_TEXT = """
This software was developed by NIST employees and is not subject to copyright 
protection in the United States. This software may be subject to foreign copyright.

The identification of certain commercial equipment, instruments, or materials does 
not imply recommendation or endorsement by NIST, nor does it imply that the materials 
or equipment identified are necessarily the best available for the purpose.
"""

def get_resource_path(resource_name: str) -> Path:
    """Get the full path to a resource file."""
    return RESOURCES_DIR / resource_name

def get_icon_path(icon_name: str) -> Path:
    """Get the full path to an icon file."""
    return ICONS_DIR / icon_name
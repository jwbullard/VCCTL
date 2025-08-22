#!/usr/bin/env python3
"""
Icon Utilities for VCCTL

Provides functions for loading and managing custom SVG icons with fallback support.
"""

import gi
from pathlib import Path
from typing import Optional

gi.require_version('Gtk', '3.0')
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import Gtk, GdkPixbuf

# Base path to custom icons
ICONS_PATH = Path(__file__).parent.parent.parent.parent / "icons"

# Icon mapping for custom icons
ICON_MAPPING = {
    # Media controls
    "media-playback-start": "48-media-play-1.svg",
    "media-playback-pause": "48-media-pause-1.svg", 
    "media-playback-stop": "48-media-stop-1.svg",
    
    # File operations
    "document-save": "48-floppy-disk.svg",
    "document-open": "48-file-upload.svg",
    "document-export": "48-file-download.svg",
    
    # Data operations
    "view-refresh": "48-refresh-01.svg",
    "edit-delete": "48-trash-xmark.svg",
    "edit-clear": "48-clear-data.svg",
    
    # Analysis and reports
    "applications-science": "48-statistics.svg",
    "document-print": "48-file-download-1.svg", 
    "preferences-system": "48-cube.svg",
    
    # Database and storage
    "drive-harddisk": "48-database.svg",
    "folder": "48-cube.svg",
    
    # Validation and quality
    "dialog-information": "48-badge-check-2.svg",
    "security-high": "48-badge-check-2.svg",
    
    # History and time
    "document-revert": "48-history.svg",
    
    # 3D and visualization
    "48-cube": "48-cube.svg",
    
    # Love/favorites (for special buttons)
    "user-bookmarks": "48-hearts-suit.svg",
    
    # Additional file operations
    "filter": "48-filter.svg",
    
    # Direct mappings for 48-* icon names (used in File Panel and status indicators)
    "48-file-upload": "48-file-upload.svg",
    "48-file-download": "48-file-download.svg", 
    "48-file-download-1": "48-file-download-1.svg",
    "48-badge-check-2": "48-badge-check-2.svg",
    "48-filter": "48-filter.svg",
    "48-history": "48-history.svg",
    "48-trash-xmark": "48-trash-xmark.svg",
    "48-database": "48-database.svg",
    "48-floppy-disk": "48-floppy-disk.svg",
    "48-statistics": "48-statistics.svg",
    "48-clear-data": "48-clear-data.svg",
}


def load_custom_icon(icon_name: str, size: int = 24) -> Optional[GdkPixbuf.Pixbuf]:
    """
    Load a custom SVG icon with specified size.
    
    Args:
        icon_name: Standard GTK icon name to map to custom icon
        size: Icon size in pixels (default: 24)
    
    Returns:
        GdkPixbuf.Pixbuf or None if icon cannot be loaded
    """
    try:
        # Check if we have a custom mapping
        if icon_name in ICON_MAPPING:
            custom_icon_file = ICON_MAPPING[icon_name]
            icon_path = ICONS_PATH / custom_icon_file
            
            if icon_path.exists():
                # Load SVG with specified size
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                    str(icon_path), size, size, True
                )
                return pixbuf
    except Exception as e:
        print(f"Failed to load custom icon {icon_name}: {e}")
    
    return None


def create_icon_image(icon_name: str, size: int = 24) -> Gtk.Image:
    """
    Create a Gtk.Image widget with custom icon or fallback.
    
    Args:
        icon_name: Standard GTK icon name
        size: Icon size in pixels
        
    Returns:
        Gtk.Image widget
    """
    # Try to load custom icon first
    pixbuf = load_custom_icon(icon_name, size)
    
    if pixbuf:
        image = Gtk.Image.new_from_pixbuf(pixbuf)
    else:
        # Fallback to standard GTK icon
        image = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.LARGE_TOOLBAR)
    
    return image


def set_tool_button_custom_icon(tool_button: Gtk.ToolButton, icon_name: str, size: int = 24) -> None:
    """
    Set custom icon for a Gtk.ToolButton with fallback.
    
    Args:
        tool_button: The ToolButton to update
        icon_name: Standard GTK icon name to map
        size: Icon size in pixels
    """
    try:
        pixbuf = load_custom_icon(icon_name, size)
        if pixbuf:
            image = Gtk.Image.new_from_pixbuf(pixbuf)
            tool_button.set_icon_widget(image)
            image.show()
        else:
            # Keep the original icon_name as fallback
            tool_button.set_icon_name(icon_name)
    except Exception as e:
        print(f"Failed to set custom icon for {icon_name}: {e}")
        # Keep original icon as fallback
        tool_button.set_icon_name(icon_name)


def set_image_custom_icon(image: Gtk.Image, icon_name: str, size: int = 24) -> None:
    """
    Set custom icon for a Gtk.Image widget with fallback.
    
    Args:
        image: The Image widget to update
        icon_name: Standard GTK icon name to map
        size: Icon size in pixels
    """
    try:
        pixbuf = load_custom_icon(icon_name, size)
        if pixbuf:
            image.set_from_pixbuf(pixbuf)
        else:
            # Keep the original icon_name as fallback
            image.set_from_icon_name(icon_name, Gtk.IconSize.MENU)
    except Exception as e:
        print(f"Failed to set custom icon for {icon_name}: {e}")
        # Keep original icon as fallback
        image.set_from_icon_name(icon_name, Gtk.IconSize.MENU)


def create_button_with_icon(label: str, icon_name: str, size: int = 16) -> Gtk.Button:
    """
    Create a button with custom icon and text.
    
    Args:
        label: Button text
        icon_name: Standard GTK icon name to map
        size: Icon size in pixels
        
    Returns:
        Gtk.Button with icon and text
    """
    button = Gtk.Button()
    
    # Create horizontal box for icon and text
    box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
    
    # Add icon
    icon_image = create_icon_image(icon_name, size)
    box.pack_start(icon_image, False, False, 0)
    
    # Add label
    label_widget = Gtk.Label(label=label)
    box.pack_start(label_widget, False, False, 0)
    
    button.add(box)
    return button
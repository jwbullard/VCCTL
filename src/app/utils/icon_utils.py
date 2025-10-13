#!/usr/bin/env python3
"""
Icon Utilities for VCCTL

Enhanced icon management with IBM Carbon Design System integration.
Provides functions for loading Carbon icons with fallback to custom/system icons.
"""

import gi
import logging
import sys
from pathlib import Path
from typing import Optional

gi.require_version('Gtk', '3.0')
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import Gtk, GdkPixbuf

# Base path to icons - handle both development and PyInstaller bundle
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    # Running in PyInstaller bundle
    ICONS_PATH = Path(sys._MEIPASS) / "icons"
else:
    # Running in development
    ICONS_PATH = Path(__file__).parent.parent.parent.parent / "icons"

# Logger
logger = logging.getLogger('VCCTL.IconUtils')

# Carbon icon mapping - maps standard GTK icon names to Carbon icon names
CARBON_ICON_MAPPING = {
    # Media controls
    "media-playback-start": "play",
    "media-playback-pause": "pause", 
    "media-playback-stop": "stop",
    "play": "play",
    "pause": "pause",
    "stop": "stop",
    
    # File operations
    "document-save": "save",
    "document-save-symbolic": "save",
    "document-open": "document--import",
    "document-open-symbolic": "document--import", 
    "document-export": "document--export",
    "document-new": "add-alt",
    "folder": "folder",
    "folder-open": "folder--open",
    "folder--open": "folder--open",
    "folder-new": "folder--add",
    "folder--add": "folder--add",
    "save": "save",
    "export": "document--export",
    
    # Data operations
    "view-refresh": "renew",
    "view-refresh-symbolic": "renew",
    "edit-delete": "trash-can",
    "edit-delete-symbolic": "trash-can",
    "edit-clear": "erase", 
    "edit-copy": "copy",
    "edit-copy-symbolic": "copy",
    "edit-cut": "cut",
    "edit-paste": "paste",
    "edit-undo": "undo",
    "edit-redo": "redo",
    "edit-find-symbolic": "search",
    "refresh": "renew",
    "trash-can": "trash-can",
    "erase": "erase",
    "copy": "copy",
    "search": "search",
    
    # Navigation
    "go-previous": "arrow--left",
    "go-next": "arrow--right",
    "go-up": "arrow--up",
    "go-down": "arrow--down",
    "go-home": "home",
    "go-first": "skip--back",
    "go-last": "skip--forward",
    "go-first-symbolic": "skip--back",
    "go-last-symbolic": "skip--forward",
    "go-previous-symbolic": "arrow--left",
    "go-next-symbolic": "arrow--right",
    "arrow--left": "arrow--left",
    "arrow--right": "arrow--right",
    "arrow--up": "arrow--up",
    "skip--back": "skip--back",
    "skip--forward": "skip--forward",
    
    # Analysis and reports
    "applications-science": "analytics",
    "document-print": "printer", 
    "preferences-system": "settings",
    "preferences-system-symbolic": "settings",
    "view-list": "list",
    "view-list-symbolic": "list", 
    "view-grid": "grid",
    "list": "list",
    "settings": "settings",
    
    # Database and storage
    "drive-harddisk": "data-base",
    "network-server": "server",
    
    # Status and validation
    "dialog-information": "information",
    "dialog-information-symbolic": "information",
    "dialog-warning": "warning",
    "dialog-error": "error",
    "dialog-question": "help",
    "security-high": "security",
    "emblem-important": "warning-alt",
    "information": "information",
    "help": "help",
    
    # Tools and utilities
    "preferences-desktop": "settings",
    "system-search": "search",
    "system-run-symbolic": "play",
    "zoom-in": "zoom--in",
    "zoom-out": "zoom--out",
    "zoom-fit-best": "fit-to-screen",
    "filter": "filter",
    
    # Common actions
    "list-add": "add",
    "list-add-symbolic": "add",
    "list-remove": "subtract",
    "list-remove-symbolic": "subtract",
    "window-close": "close",
    "window-close-symbolic": "close", 
    "application-exit": "logout",
    "help-browser": "help",
    "help-about": "information",
    "open-menu-symbolic": "menu",
    "add": "add",
    "subtract": "subtract", 
    "close": "close",
    "menu": "menu",
    
    # 3D and visualization
    "cube": "cube",
    "48-cube": "cube",
    "48-floppy-disk": "activity",
    "3d": "3d-curve-auto-colon",
    
    # Process control
    "process-stop": "stop",
    "system-run": "play",
    
    # Document editing
    "document-edit-symbolic": "edit",
    "edit": "edit",
    
    # Development/debugging
    "utilities-terminal": "terminal",
    "text-editor": "edit",
    "development": "code",
}

# Legacy custom icon mapping for fallback support
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


def load_carbon_icon(icon_name: str, size: int = 24) -> Optional[GdkPixbuf.Pixbuf]:
    """
    Load a Carbon Design System SVG icon with specified size.
    
    Args:
        icon_name: Standard GTK icon name or Carbon icon name
        size: Icon size in pixels (default: 24)
    
    Returns:
        GdkPixbuf.Pixbuf or None if icon cannot be loaded
    """
    try:
        # Import Carbon icon manager
        from app.utils.carbon_icon_manager import get_carbon_icon_manager
        
        manager = get_carbon_icon_manager()
        
        # Check if we have a Carbon mapping for this GTK icon name
        carbon_name = CARBON_ICON_MAPPING.get(icon_name, icon_name)
        
        # Try to load the Carbon icon
        pixbuf = manager.load_icon_pixbuf(carbon_name, size)
        if pixbuf:
            return pixbuf
            
    except Exception as e:
        logger.warning(f"Failed to load Carbon icon {icon_name}: {e}")
    
    return None


def load_custom_icon(icon_name: str, size: int = 24) -> Optional[GdkPixbuf.Pixbuf]:
    """
    Load a custom SVG icon with specified size (legacy fallback).
    
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
        logger.warning(f"Failed to load custom icon {icon_name}: {e}")
    
    return None


def load_icon_with_fallback(icon_name: str, size: int = 24) -> Optional[GdkPixbuf.Pixbuf]:
    """
    Load icon with comprehensive fallback chain: Carbon → Custom → System.
    
    Args:
        icon_name: Standard GTK icon name
        size: Icon size in pixels (default: 24)
    
    Returns:
        GdkPixbuf.Pixbuf or None if no icon can be loaded
    """
    # Try Carbon icons first (preferred)
    pixbuf = load_carbon_icon(icon_name, size)
    if pixbuf:
        return pixbuf
    
    # Fallback to custom icons
    pixbuf = load_custom_icon(icon_name, size)
    if pixbuf:
        return pixbuf
    
    # Final fallback to system icons
    try:
        theme = Gtk.IconTheme.get_default()
        if theme.has_icon(icon_name):
            pixbuf = theme.load_icon(icon_name, size, Gtk.IconLookupFlags.USE_BUILTIN)
            return pixbuf
    except Exception as e:
        logger.warning(f"Failed to load system icon {icon_name}: {e}")
    
    return None


def create_icon_image(icon_name: str, size: int = 24) -> Gtk.Image:
    """
    Create a Gtk.Image widget with Carbon icon and comprehensive fallback.
    
    Args:
        icon_name: Standard GTK icon name
        size: Icon size in pixels
        
    Returns:
        Gtk.Image widget
    """
    # Try comprehensive fallback chain
    pixbuf = load_icon_with_fallback(icon_name, size)
    
    if pixbuf:
        image = Gtk.Image.new_from_pixbuf(pixbuf)
    else:
        # Final fallback to standard GTK icon with default size
        image = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.LARGE_TOOLBAR)
    
    return image


def set_tool_button_custom_icon(tool_button: Gtk.ToolButton, icon_name: str, size: int = 24) -> None:
    """
    Set Carbon icon for a Gtk.ToolButton with comprehensive fallback.
    
    Args:
        tool_button: The ToolButton to update
        icon_name: Standard GTK icon name to map
        size: Icon size in pixels
    """
    try:
        pixbuf = load_icon_with_fallback(icon_name, size)
        if pixbuf:
            image = Gtk.Image.new_from_pixbuf(pixbuf)
            tool_button.set_icon_widget(image)
            image.show()
        else:
            # Keep the original icon_name as fallback
            tool_button.set_icon_name(icon_name)
    except Exception as e:
        logger.error(f"Failed to set icon for {icon_name}: {e}")
        # Keep original icon as fallback
        tool_button.set_icon_name(icon_name)


def set_image_custom_icon(image: Gtk.Image, icon_name: str, size: int = 24) -> None:
    """
    Set Carbon icon for a Gtk.Image widget with comprehensive fallback.
    
    Args:
        image: The Image widget to update
        icon_name: Standard GTK icon name to map
        size: Icon size in pixels
    """
    try:
        pixbuf = load_icon_with_fallback(icon_name, size)
        if pixbuf:
            image.set_from_pixbuf(pixbuf)
        else:
            # Keep the original icon_name as fallback
            image.set_from_icon_name(icon_name, Gtk.IconSize.MENU)
    except Exception as e:
        logger.error(f"Failed to set icon for {icon_name}: {e}")
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


# New Carbon-specific convenience functions

def create_carbon_button(label: str, carbon_icon_name: str, size: int = 16) -> Gtk.Button:
    """
    Create a button with a specific Carbon icon (bypassing GTK mapping).
    
    Args:
        label: Button text
        carbon_icon_name: Direct Carbon icon name (e.g., 'add', 'save', 'folder--open')
        size: Icon size in pixels
        
    Returns:
        Gtk.Button with Carbon icon and text
    """
    from app.utils.carbon_icon_manager import create_carbon_icon_button
    return create_carbon_icon_button(carbon_icon_name, label, size)


def create_carbon_image(carbon_icon_name: str, size: int = 32) -> Optional[Gtk.Image]:
    """
    Create a Gtk.Image with a specific Carbon icon (bypassing GTK mapping).
    
    Args:
        carbon_icon_name: Direct Carbon icon name (e.g., 'add', 'save', 'folder--open')
        size: Icon size in pixels
        
    Returns:
        Gtk.Image widget or None if icon not found
    """
    from app.utils.carbon_icon_manager import create_carbon_icon_image
    return create_carbon_icon_image(carbon_icon_name, size)


def suggest_carbon_icon(action_description: str) -> Optional[str]:
    """
    Suggest a Carbon icon based on an action description.
    
    Args:
        action_description: Description of the action (e.g., 'save file', 'delete item')
        
    Returns:
        Carbon icon name or None if no suggestion found
    """
    try:
        from app.utils.carbon_icon_manager import get_carbon_icon_manager
        manager = get_carbon_icon_manager()
        return manager.suggest_icon_for_action(action_description)
    except Exception as e:
        logger.error(f"Failed to suggest icon for '{action_description}': {e}")
        return None


def browse_carbon_icons(parent_window: Optional[Gtk.Window] = None) -> Optional[str]:
    """
    Open the Carbon icon browser dialog.
    
    Args:
        parent_window: Parent window for the dialog
        
    Returns:
        Selected Carbon icon name or None if cancelled
    """
    try:
        from app.windows.dialogs.carbon_icon_browser import CarbonIconBrowser
        return CarbonIconBrowser.show_browser(parent_window)
    except Exception as e:
        logger.error(f"Failed to open Carbon icon browser: {e}")
        return None


# Backward compatibility aliases
def create_button_with_carbon_icon(label: str, icon_name: str, size: int = 16) -> Gtk.Button:
    """Backward compatibility alias for create_button_with_icon with Carbon icons."""
    return create_button_with_icon(label, icon_name, size)
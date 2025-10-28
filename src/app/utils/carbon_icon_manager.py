#!/usr/bin/env python3
"""
Carbon Icon Manager for VCCTL

Manages IBM Carbon Design System icons for GTK3 applications.
Provides icon loading, categorization, search, and preview functionality.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import Gtk, GdkPixbuf, GLib

class CarbonIconManager:
    """Manager for IBM Carbon Design System icons."""
    
    def __init__(self):
        """Initialize the Carbon icon manager."""
        self.logger = logging.getLogger('VCCTL.CarbonIconManager')

        # Determine paths - handle both development and PyInstaller bundle
        import sys
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            # Running in PyInstaller bundle
            self.project_root = Path(sys._MEIPASS)
        else:
            # Running in development
            self.project_root = Path(__file__).parent.parent.parent.parent

        self.carbon_icons_dir = self.project_root / "icons" / "carbon"
        self.metadata_file = self.carbon_icons_dir / "metadata.json"
        
        # Icon organization
        self.available_sizes = ["16", "20", "24", "32"]
        self.default_size = "32"
        self.metadata = {}
        self.icon_cache = {}  # Cache for loaded pixbufs
        self.categories = {}  # Icon categories from metadata
        
        # Load metadata
        self._load_metadata()
        
        self.logger.info(f"Carbon Icon Manager initialized with {len(self.metadata)} icons")
    
    def _load_metadata(self) -> None:
        """Load Carbon icons metadata for categorization and search."""
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r') as f:
                    raw_metadata = json.load(f)
                
                # Process metadata into usable format
                for icon_data in raw_metadata.get('icons', []):
                    name = icon_data.get('name', '').replace('--', '-')
                    self.metadata[name] = {
                        'name': name,
                        'category': icon_data.get('category', 'Uncategorized'),
                        'tags': icon_data.get('tags', []),
                        'description': icon_data.get('description', ''),
                        'aliases': icon_data.get('aliases', []),
                        'sizes': icon_data.get('sizes', self.available_sizes)
                    }
                    
                    # Build category index
                    category = icon_data.get('category', 'Uncategorized')
                    if category not in self.categories:
                        self.categories[category] = []
                    self.categories[category].append(name)
                
                self.logger.info(f"Loaded metadata for {len(self.metadata)} icons in {len(self.categories)} categories")
            else:
                self.logger.warning("No metadata file found, building from directory structure")
                self._build_metadata_from_files()
                
        except Exception as e:
            self.logger.error(f"Error loading metadata: {e}")
            self._build_metadata_from_files()
    
    def _build_metadata_from_files(self) -> None:
        """Build basic metadata from available SVG files."""
        try:
            # Use 32px directory as primary source
            icons_dir = self.carbon_icons_dir / "32"
            if icons_dir.exists():
                for svg_file in icons_dir.glob("*.svg"):
                    name = svg_file.stem
                    self.metadata[name] = {
                        'name': name,
                        'category': self._guess_category_from_name(name),
                        'tags': self._generate_tags_from_name(name),
                        'description': f"Carbon icon: {name}",
                        'aliases': [],
                        'sizes': self.available_sizes
                    }
                
                # Build categories from guessed data
                for icon_name, icon_data in self.metadata.items():
                    category = icon_data['category']
                    if category not in self.categories:
                        self.categories[category] = []
                    self.categories[category].append(icon_name)
                
                self.logger.info(f"Built metadata for {len(self.metadata)} icons from file structure")
                
        except Exception as e:
            self.logger.error(f"Error building metadata from files: {e}")
    
    def _guess_category_from_name(self, name: str) -> str:
        """Guess icon category from name patterns."""
        name_lower = name.lower()
        
        if any(word in name_lower for word in ['arrow', 'chevron', 'caret', 'direction']):
            return 'Navigation'
        elif any(word in name_lower for word in ['add', 'delete', 'edit', 'save', 'copy', 'cut', 'paste']):
            return 'Actions'
        elif any(word in name_lower for word in ['file', 'folder', 'document', 'page']):
            return 'Files'
        elif any(word in name_lower for word in ['user', 'person', 'account', 'profile']):
            return 'Users'
        elif any(word in name_lower for word in ['chart', 'graph', 'data', 'analytics']):
            return 'Data'
        elif any(word in name_lower for word in ['settings', 'configure', 'gear', 'preferences']):
            return 'Settings'
        elif any(word in name_lower for word in ['warning', 'error', 'success', 'info', 'alert']):
            return 'Status'
        elif any(word in name_lower for word in ['media', 'play', 'pause', 'stop', 'video']):
            return 'Media'
        elif any(word in name_lower for word in ['tools', 'wrench', 'screwdriver']):
            return 'Tools'
        else:
            return 'General'
    
    def _generate_tags_from_name(self, name: str) -> List[str]:
        """Generate search tags from icon name."""
        # Split on common delimiters and create tags
        parts = name.replace('-', ' ').replace('_', ' ').split()
        tags = []
        
        for part in parts:
            if len(part) > 2:  # Skip very short parts
                tags.append(part.lower())
        
        return tags
    
    def get_available_icons(self, category: Optional[str] = None) -> List[str]:
        """Get list of available icon names, optionally filtered by category."""
        if category and category in self.categories:
            return self.categories[category]
        return list(self.metadata.keys())
    
    def get_categories(self) -> List[str]:
        """Get list of available icon categories."""
        return sorted(self.categories.keys())
    
    def search_icons(self, query: str) -> List[str]:
        """Search icons by name, tags, or description."""
        query = query.lower().strip()
        if not query:
            return self.get_available_icons()
        
        matches = []
        for name, data in self.metadata.items():
            # Check name
            if query in name.lower():
                matches.append(name)
                continue
            
            # Check tags
            if any(query in tag.lower() for tag in data.get('tags', [])):
                matches.append(name)
                continue
            
            # Check description
            if query in data.get('description', '').lower():
                matches.append(name)
                continue
            
            # Check aliases
            if any(query in alias.lower() for alias in data.get('aliases', [])):
                matches.append(name)
                continue
        
        return sorted(matches)
    
    def get_icon_path(self, icon_name: str, size: str = None) -> Optional[Path]:
        """Get the file path for an icon."""
        if size is None:
            size = self.default_size
        
        if size not in self.available_sizes:
            self.logger.warning(f"Size {size} not available, using {self.default_size}")
            size = self.default_size
        
        # Try sizes in preference order: requested size first, then fallback to other sizes
        sizes_to_try = [size] + [s for s in ["32", "24", "20", "16"] if s != size]
        
        for try_size in sizes_to_try:
            # Try direct path first
            icon_path = self.carbon_icons_dir / try_size / f"{icon_name}.svg"
            if icon_path.exists():
                return icon_path
            
            # Try with dashes converted to double dashes (Carbon naming convention)
            carbon_name = icon_name.replace('-', '--')
            icon_path = self.carbon_icons_dir / try_size / f"{carbon_name}.svg"
            if icon_path.exists():
                return icon_path
        
        # Try in root directory (some icons are stored there)
        icon_path = self.carbon_icons_dir / f"{icon_name}.svg"
        if icon_path.exists():
            return icon_path
        
        self.logger.warning(f"Icon not found: {icon_name} (tried all sizes)")
        return None
    
    def load_icon_pixbuf(self, icon_name: str, size: int = 32) -> Optional[GdkPixbuf.Pixbuf]:
        """Load icon as GdkPixbuf for use in GTK widgets."""
        cache_key = f"{icon_name}_{size}"
        
        # Check cache first
        if cache_key in self.icon_cache:
            return self.icon_cache[cache_key]
        
        # Find best size match
        size_str = str(size)
        if size_str not in self.available_sizes:
            # Find closest size
            available_nums = [int(s) for s in self.available_sizes]
            closest = min(available_nums, key=lambda x: abs(x - size))
            size_str = str(closest)
        
        icon_path = self.get_icon_path(icon_name, size_str)
        if not icon_path:
            return None
        
        try:
            # Load SVG and scale to desired size
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                str(icon_path), size, size, True
            )
            
            # Cache the result
            self.icon_cache[cache_key] = pixbuf
            return pixbuf
            
        except Exception as e:
            self.logger.error(f"Error loading icon {icon_name}: {e}")
            return None
    
    def create_icon_image(self, icon_name: str, size: int = 32) -> Optional[Gtk.Image]:
        """Create a Gtk.Image widget with the specified Carbon icon."""
        pixbuf = self.load_icon_pixbuf(icon_name, size)
        if pixbuf:
            image = Gtk.Image.new_from_pixbuf(pixbuf)
            return image
        return None
    
    def get_icon_info(self, icon_name: str) -> Dict:
        """Get detailed information about an icon."""
        return self.metadata.get(icon_name, {
            'name': icon_name,
            'category': 'Unknown',
            'tags': [],
            'description': 'No description available',
            'aliases': [],
            'sizes': self.available_sizes
        })
    
    def suggest_icon_for_action(self, action_name: str) -> Optional[str]:
        """Suggest a Carbon icon based on an action name."""
        action_lower = action_name.lower()
        
        # Common action mappings
        action_mappings = {
            # File operations
            'save': 'save',
            'open': 'folder--open',
            'new': 'add',
            'delete': 'trash-can',
            'copy': 'copy',
            'cut': 'cut',
            'paste': 'paste',
            
            # Navigation
            'back': 'arrow--left',
            'forward': 'arrow--right',
            'up': 'arrow--up',
            'down': 'arrow--down',
            'refresh': 'refresh',
            'home': 'home',
            
            # Media controls
            'play': 'play',
            'pause': 'pause',
            'stop': 'stop',
            'record': 'circle--solid',
            
            # Common UI
            'settings': 'settings',
            'help': 'help',
            'info': 'information',
            'warning': 'warning',
            'error': 'error',
            'success': 'checkmark',
            'close': 'close',
            'menu': 'menu',
            'search': 'search',
            
            # Tools
            'edit': 'edit',
            'view': 'view',
            'print': 'printer',
            'export': 'export',
            'import': 'import',
            
            # Data/science
            'data': 'data-table',
            'chart': 'chart-line',
            'graph': 'chart-bar',
            'calculate': 'calculator',
            'analyze': 'analytics',
            '3d': 'cube',
            'plot': 'chart-scatter'
        }
        
        # Direct mapping
        if action_lower in action_mappings:
            suggested = action_mappings[action_lower]
            if self.get_icon_path(suggested):
                return suggested
        
        # Search for similar icons
        search_results = self.search_icons(action_name)
        if search_results:
            return search_results[0]
        
        return None
    
    def clear_cache(self) -> None:
        """Clear the icon cache to free memory."""
        self.icon_cache.clear()
        self.logger.info("Icon cache cleared")


# Global Carbon icon manager instance
_carbon_icon_manager = None

def get_carbon_icon_manager() -> CarbonIconManager:
    """Get the global Carbon icon manager instance."""
    global _carbon_icon_manager
    if _carbon_icon_manager is None:
        _carbon_icon_manager = CarbonIconManager()
    return _carbon_icon_manager


def create_carbon_icon_button(icon_name: str, text: str = "", size: int = 16) -> Gtk.Button:
    """Create a button with a Carbon icon."""
    manager = get_carbon_icon_manager()
    button = Gtk.Button()
    
    # Create horizontal box for icon and text
    box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
    
    # Add icon
    icon_image = manager.create_icon_image(icon_name, size)
    if icon_image:
        box.pack_start(icon_image, False, False, 0)
    
    # Add text if provided
    if text:
        label = Gtk.Label(text)
        box.pack_start(label, False, False, 0)
    
    button.add(box)
    return button


def create_carbon_icon_image(icon_name: str, size: int = 32) -> Optional[Gtk.Image]:
    """Create a Gtk.Image with a Carbon icon."""
    manager = get_carbon_icon_manager()
    return manager.create_icon_image(icon_name, size)
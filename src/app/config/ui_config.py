#!/usr/bin/env python3
"""
UI Configuration for VCCTL

Manages user interface preferences and settings.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Tuple, List


@dataclass
class UIConfig:
    """Configuration for user interface preferences."""
    
    # Theme and appearance
    theme: str = "system"  # "light", "dark", or "system"
    use_dark_theme: bool = False  # Explicit dark theme override
    
    # Window settings
    window_width: int = 1200
    window_height: int = 800
    window_maximized: bool = False
    window_position_x: int = -1  # -1 means center
    window_position_y: int = -1  # -1 means center
    
    # Font settings
    font_family: str = "Sans"
    font_size: int = 11
    monospace_font_family: str = "Monospace"
    monospace_font_size: int = 10
    
    # Toolbar and menu settings
    show_toolbar: bool = True
    show_statusbar: bool = True
    toolbar_style: str = "both"  # "icons", "text", "both"
    toolbar_icon_size: int = 24  # pixels
    
    # Panel layout
    show_sidebar: bool = True
    sidebar_width: int = 250
    show_bottom_panel: bool = True
    bottom_panel_height: int = 200
    
    # Tree view settings
    show_grid_lines: bool = True
    alternating_row_colors: bool = True
    tree_indent: int = 20
    
    # Notification settings
    show_notifications: bool = True
    notification_timeout: int = 5  # seconds
    sound_enabled: bool = False
    
    # Dialog settings
    confirm_on_exit: bool = True
    confirm_destructive_actions: bool = True
    remember_dialog_sizes: bool = True
    
    # Recent files and projects
    max_recent_files: int = 10
    max_recent_projects: int = 5
    
    # Performance settings
    animation_enabled: bool = True
    smooth_scrolling: bool = True
    use_opengl: bool = False
    
    # Accessibility
    high_contrast: bool = False
    large_icons: bool = False
    screen_reader_support: bool = False
    
    # Custom colors (RGB tuples)
    custom_colors: Dict[str, Tuple[int, int, int]] = field(default_factory=lambda: {
        'primary': (52, 101, 164),      # Blue
        'secondary': (92, 53, 102),     # Purple
        'success': (46, 125, 50),       # Green
        'warning': (255, 152, 0),       # Orange
        'error': (211, 47, 47),         # Red
        'info': (2, 136, 209)           # Light blue
    })
    
    # Keyboard shortcuts
    keyboard_shortcuts: Dict[str, str] = field(default_factory=lambda: {
        'new_project': '<Ctrl>n',
        'open_project': '<Ctrl>o',
        'save_project': '<Ctrl>s',
        'save_as': '<Ctrl><Shift>s',
        'quit': '<Ctrl>q',
        'preferences': '<Ctrl>comma',
        'about': 'F1',
        'fullscreen': 'F11'
    })
    
    # Plot and visualization settings
    plot_dpi: int = 100
    plot_style: str = "default"  # matplotlib style
    default_colormap: str = "viridis"
    show_plot_toolbar: bool = True
    
    @classmethod
    def create_default(cls) -> 'UIConfig':
        """Create default UI configuration."""
        return cls()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UIConfig':
        """Create UI configuration from dictionary."""
        # Handle custom colors conversion
        custom_colors = data.get('custom_colors', {})
        if custom_colors:
            # Convert string tuples back to tuples if needed
            for key, value in custom_colors.items():
                if isinstance(value, (list, tuple)) and len(value) == 3:
                    custom_colors[key] = tuple(value)
        
        return cls(
            theme=data.get('theme', 'system'),
            use_dark_theme=data.get('use_dark_theme', False),
            window_width=data.get('window_width', 1200),
            window_height=data.get('window_height', 800),
            window_maximized=data.get('window_maximized', False),
            window_position_x=data.get('window_position_x', -1),
            window_position_y=data.get('window_position_y', -1),
            font_family=data.get('font_family', 'Sans'),
            font_size=data.get('font_size', 11),
            monospace_font_family=data.get('monospace_font_family', 'Monospace'),
            monospace_font_size=data.get('monospace_font_size', 10),
            show_toolbar=data.get('show_toolbar', True),
            show_statusbar=data.get('show_statusbar', True),
            toolbar_style=data.get('toolbar_style', 'both'),
            toolbar_icon_size=data.get('toolbar_icon_size', 24),
            show_sidebar=data.get('show_sidebar', True),
            sidebar_width=data.get('sidebar_width', 250),
            show_bottom_panel=data.get('show_bottom_panel', True),
            bottom_panel_height=data.get('bottom_panel_height', 200),
            show_grid_lines=data.get('show_grid_lines', True),
            alternating_row_colors=data.get('alternating_row_colors', True),
            tree_indent=data.get('tree_indent', 20),
            show_notifications=data.get('show_notifications', True),
            notification_timeout=data.get('notification_timeout', 5),
            sound_enabled=data.get('sound_enabled', False),
            confirm_on_exit=data.get('confirm_on_exit', True),
            confirm_destructive_actions=data.get('confirm_destructive_actions', True),
            remember_dialog_sizes=data.get('remember_dialog_sizes', True),
            max_recent_files=data.get('max_recent_files', 10),
            max_recent_projects=data.get('max_recent_projects', 5),
            animation_enabled=data.get('animation_enabled', True),
            smooth_scrolling=data.get('smooth_scrolling', True),
            use_opengl=data.get('use_opengl', False),
            high_contrast=data.get('high_contrast', False),
            large_icons=data.get('large_icons', False),
            screen_reader_support=data.get('screen_reader_support', False),
            custom_colors=custom_colors or {
                'primary': (52, 101, 164), 'secondary': (92, 53, 102),
                'success': (46, 125, 50), 'warning': (255, 152, 0),
                'error': (211, 47, 47), 'info': (2, 136, 209)
            },
            keyboard_shortcuts=data.get('keyboard_shortcuts', {
                'new_project': '<Ctrl>n', 'open_project': '<Ctrl>o',
                'save_project': '<Ctrl>s', 'save_as': '<Ctrl><Shift>s',
                'quit': '<Ctrl>q', 'preferences': '<Ctrl>comma',
                'about': 'F1', 'fullscreen': 'F11'
            }),
            plot_dpi=data.get('plot_dpi', 100),
            plot_style=data.get('plot_style', 'default'),
            default_colormap=data.get('default_colormap', 'viridis'),
            show_plot_toolbar=data.get('show_plot_toolbar', True)
        )
    
    def get_window_geometry(self) -> Dict[str, int]:
        """Get window geometry settings."""
        return {
            'width': self.window_width,
            'height': self.window_height,
            'x': self.window_position_x,
            'y': self.window_position_y,
            'maximized': self.window_maximized
        }
    
    def set_window_geometry(self, width: int, height: int, x: int = -1, y: int = -1, maximized: bool = False) -> None:
        """Set window geometry settings."""
        self.window_width = max(400, width)  # Minimum width
        self.window_height = max(300, height)  # Minimum height
        self.window_position_x = x
        self.window_position_y = y
        self.window_maximized = maximized
    
    def get_font_description(self, monospace: bool = False) -> str:
        """Get font description string for GTK."""
        if monospace:
            return f"{self.monospace_font_family} {self.monospace_font_size}"
        else:
            return f"{self.font_family} {self.font_size}"
    
    def get_color_rgb(self, color_name: str) -> Tuple[int, int, int]:
        """Get RGB color tuple for a named color."""
        return self.custom_colors.get(color_name, (128, 128, 128))
    
    def get_color_hex(self, color_name: str) -> str:
        """Get hex color string for a named color."""
        r, g, b = self.get_color_rgb(color_name)
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def set_custom_color(self, color_name: str, r: int, g: int, b: int) -> None:
        """Set a custom color."""
        r = max(0, min(255, r))
        g = max(0, min(255, g))
        b = max(0, min(255, b))
        self.custom_colors[color_name] = (r, g, b)
    
    def get_keyboard_shortcut(self, action: str) -> str:
        """Get keyboard shortcut for an action."""
        return self.keyboard_shortcuts.get(action, "")
    
    def set_keyboard_shortcut(self, action: str, shortcut: str) -> None:
        """Set keyboard shortcut for an action."""
        # Basic validation of GTK accelerator format
        if shortcut and ('<' in shortcut or shortcut.startswith('F')):
            self.keyboard_shortcuts[action] = shortcut
    
    def get_theme_settings(self) -> Dict[str, Any]:
        """Get theme-related settings."""
        return {
            'theme': self.theme,
            'use_dark_theme': self.use_dark_theme,
            'high_contrast': self.high_contrast,
            'custom_colors': self.custom_colors
        }
    
    def get_accessibility_settings(self) -> Dict[str, bool]:
        """Get accessibility settings."""
        return {
            'high_contrast': self.high_contrast,
            'large_icons': self.large_icons,
            'screen_reader_support': self.screen_reader_support,
            'sound_enabled': self.sound_enabled
        }
    
    def get_layout_settings(self) -> Dict[str, Any]:
        """Get layout and panel settings."""
        return {
            'show_toolbar': self.show_toolbar,
            'show_statusbar': self.show_statusbar,
            'show_sidebar': self.show_sidebar,
            'sidebar_width': self.sidebar_width,
            'show_bottom_panel': self.show_bottom_panel,
            'bottom_panel_height': self.bottom_panel_height,
            'toolbar_style': self.toolbar_style,
            'toolbar_icon_size': self.toolbar_icon_size
        }
    
    def apply_theme_to_widget(self, widget) -> None:
        """Apply theme settings to a GTK widget (placeholder for actual implementation)."""
        # This would be implemented with actual GTK theming code
        # For now, just a placeholder to show the intended interface
        pass
    
    def validate(self) -> Dict[str, Any]:
        """Validate UI configuration."""
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Validate theme
        valid_themes = ['light', 'dark', 'system']
        if self.theme not in valid_themes:
            validation_result['errors'].append(f"Invalid theme '{self.theme}', must be one of {valid_themes}")
            validation_result['is_valid'] = False
        
        # Validate window dimensions
        if not (400 <= self.window_width <= 4000):
            validation_result['warnings'].append(f"Window width ({self.window_width}) outside reasonable range")
        
        if not (300 <= self.window_height <= 3000):
            validation_result['warnings'].append(f"Window height ({self.window_height}) outside reasonable range")
        
        # Validate font sizes
        if not (8 <= self.font_size <= 32):
            validation_result['warnings'].append(f"Font size ({self.font_size}) outside recommended range [8, 32]")
        
        if not (8 <= self.monospace_font_size <= 32):
            validation_result['warnings'].append(f"Monospace font size ({self.monospace_font_size}) outside recommended range")
        
        # Validate toolbar settings
        valid_toolbar_styles = ['icons', 'text', 'both']
        if self.toolbar_style not in valid_toolbar_styles:
            validation_result['errors'].append(f"Invalid toolbar style '{self.toolbar_style}'")
            validation_result['is_valid'] = False
        
        if not (16 <= self.toolbar_icon_size <= 64):
            validation_result['warnings'].append(f"Toolbar icon size ({self.toolbar_icon_size}) outside recommended range")
        
        # Validate panel dimensions
        if not (100 <= self.sidebar_width <= 800):
            validation_result['warnings'].append(f"Sidebar width ({self.sidebar_width}) outside reasonable range")
        
        if not (100 <= self.bottom_panel_height <= 600):
            validation_result['warnings'].append(f"Bottom panel height ({self.bottom_panel_height}) outside reasonable range")
        
        # Validate notification timeout
        if not (1 <= self.notification_timeout <= 60):
            validation_result['warnings'].append(f"Notification timeout ({self.notification_timeout}) outside reasonable range")
        
        # Validate colors
        for color_name, (r, g, b) in self.custom_colors.items():
            if not (0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255):
                validation_result['errors'].append(f"Invalid RGB values for color '{color_name}': ({r}, {g}, {b})")
                validation_result['is_valid'] = False
        
        # Validate plot settings
        if not (50 <= self.plot_dpi <= 300):
            validation_result['warnings'].append(f"Plot DPI ({self.plot_dpi}) outside recommended range [50, 300]")
        
        return validation_result
    
    def reset_to_defaults(self) -> None:
        """Reset UI configuration to default values."""
        default_config = self.create_default()
        
        # Copy all attributes from default
        for attr_name, attr_value in default_config.__dict__.items():
            setattr(self, attr_name, attr_value)
    
    def export_theme(self) -> Dict[str, Any]:
        """Export theme settings for sharing."""
        return {
            'name': 'Custom Theme',
            'theme': self.theme,
            'use_dark_theme': self.use_dark_theme,
            'custom_colors': self.custom_colors,
            'font_family': self.font_family,
            'font_size': self.font_size,
            'high_contrast': self.high_contrast
        }
    
    def import_theme(self, theme_data: Dict[str, Any]) -> None:
        """Import theme settings from external data."""
        if 'theme' in theme_data:
            self.theme = theme_data['theme']
        if 'use_dark_theme' in theme_data:
            self.use_dark_theme = theme_data['use_dark_theme']
        if 'custom_colors' in theme_data:
            self.custom_colors.update(theme_data['custom_colors'])
        if 'font_family' in theme_data:
            self.font_family = theme_data['font_family']
        if 'font_size' in theme_data:
            self.font_size = theme_data['font_size']
        if 'high_contrast' in theme_data:
            self.high_contrast = theme_data['high_contrast']
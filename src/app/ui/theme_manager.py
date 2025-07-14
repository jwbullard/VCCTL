#!/usr/bin/env python3
"""
VCCTL UI Theme Manager

Provides consistent theming, styling, and visual design across all VCCTL components.
Implements scientific software UI standards with professional appearance.
"""

import gi
import logging
from typing import Dict, Optional, Tuple, Any
from pathlib import Path
from enum import Enum

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GObject


class ColorScheme(Enum):
    """Available color schemes for VCCTL."""
    LIGHT = "light"
    DARK = "dark"
    SCIENTIFIC = "scientific"  # Blue/grey scientific theme
    HIGH_CONTRAST = "high_contrast"


class VCCTLColors:
    """VCCTL Color palette for consistent theming."""
    
    # Primary colors (scientific blue-grey theme)
    PRIMARY_BLUE = "#2E3440"           # Dark blue-grey
    PRIMARY_LIGHT = "#5E81AC"          # Light blue
    PRIMARY_ACCENT = "#88C0D0"         # Accent blue
    
    # Secondary colors
    SECONDARY_GREEN = "#A3BE8C"        # Success green
    SECONDARY_ORANGE = "#D08770"       # Warning orange
    SECONDARY_RED = "#BF616A"          # Error red
    SECONDARY_PURPLE = "#B48EAD"       # Info purple
    
    # Neutral colors
    BACKGROUND_LIGHT = "#ECEFF4"       # Light background
    BACKGROUND_MEDIUM = "#E5E9F0"      # Medium background
    BACKGROUND_DARK = "#D8DEE9"        # Dark background
    
    SURFACE_LIGHT = "#FFFFFF"          # Light surface
    SURFACE_MEDIUM = "#F8F9FA"         # Medium surface
    SURFACE_DARK = "#ECEFF4"           # Dark surface
    
    TEXT_PRIMARY = "#2E3440"           # Primary text
    TEXT_SECONDARY = "#4C566A"         # Secondary text
    TEXT_DISABLED = "#81A1C1"          # Disabled text
    TEXT_ON_PRIMARY = "#FFFFFF"        # Text on primary color
    
    # Border colors
    BORDER_LIGHT = "#D8DEE9"
    BORDER_MEDIUM = "#81A1C1"
    BORDER_DARK = "#5E81AC"
    
    # Status colors
    STATUS_SUCCESS = "#A3BE8C"
    STATUS_WARNING = "#EBCB8B"
    STATUS_ERROR = "#BF616A"
    STATUS_INFO = "#81A1C1"


class VCCTLFonts:
    """Font specifications for VCCTL."""
    
    # Font families
    UI_FONT_FAMILY = "Inter, -gtk-system-font, system-ui, sans-serif"
    MONO_FONT_FAMILY = "JetBrains Mono, Consolas, Monaco, 'Courier New', monospace"
    
    # Font sizes (in points)
    FONT_SIZE_SMALL = 9
    FONT_SIZE_NORMAL = 10
    FONT_SIZE_MEDIUM = 11
    FONT_SIZE_LARGE = 12
    FONT_SIZE_XLARGE = 14
    FONT_SIZE_TITLE = 16
    FONT_SIZE_HEADER = 18
    
    # Font weights
    FONT_WEIGHT_LIGHT = 300
    FONT_WEIGHT_NORMAL = 400
    FONT_WEIGHT_MEDIUM = 500
    FONT_WEIGHT_BOLD = 700


class VCCTLSpacing:
    """Consistent spacing values for VCCTL."""
    
    SPACING_NONE = 0
    SPACING_XS = 4
    SPACING_SM = 8
    SPACING_MD = 12
    SPACING_LG = 16
    SPACING_XL = 24
    SPACING_XXL = 32
    
    # Margins
    MARGIN_SMALL = 6
    MARGIN_NORMAL = 12
    MARGIN_LARGE = 18
    
    # Padding
    PADDING_SMALL = 6
    PADDING_NORMAL = 12
    PADDING_LARGE = 18
    
    # Border radius
    BORDER_RADIUS_SMALL = 4
    BORDER_RADIUS_NORMAL = 6
    BORDER_RADIUS_LARGE = 8


class ThemeManager(GObject.Object):
    """
    Manages theming and styling for VCCTL application.
    
    Features:
    - Consistent color schemes
    - Typography management
    - CSS styling application
    - Theme switching
    - Accessibility support
    """
    
    __gsignals__ = {
        'theme-changed': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
    }
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger('VCCTL.ThemeManager')
        
        self.current_scheme = ColorScheme.SCIENTIFIC
        self.css_provider = Gtk.CssProvider()
        self.style_context = Gtk.StyleContext()
        
        # Initialize theme
        self._setup_theme()
        self.apply_theme()
        
        self.logger.info("Theme manager initialized")
    
    def _setup_theme(self) -> None:
        """Setup initial theme configuration."""
        # Add CSS provider to default screen
        screen = Gdk.Screen.get_default()
        self.style_context.add_provider_for_screen(
            screen,
            self.css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
    
    def apply_theme(self, scheme: Optional[ColorScheme] = None) -> None:
        """Apply theme to the application."""
        if scheme:
            self.current_scheme = scheme
        
        css_content = self._generate_css()
        
        try:
            self.css_provider.load_from_data(css_content.encode('utf-8'))
            self.emit('theme-changed', self.current_scheme.value)
            self.logger.info(f"Applied theme: {self.current_scheme.value}")
        except Exception as e:
            self.logger.error(f"Failed to apply theme: {e}")
    
    def _generate_css(self) -> str:
        """Generate CSS content for current theme."""
        colors = self._get_colors_for_scheme(self.current_scheme)
        
        css = f"""
        /* VCCTL Application Theme - {self.current_scheme.value.title()} */
        
        /* Root variables */
        :root {{
            --primary-color: {colors['primary']};
            --primary-light: {colors['primary_light']};
            --primary-accent: {colors['primary_accent']};
            --background-color: {colors['background']};
            --surface-color: {colors['surface']};
            --text-color: {colors['text_primary']};
            --text-secondary: {colors['text_secondary']};
            --border-color: {colors['border']};
            --success-color: {colors['success']};
            --warning-color: {colors['warning']};
            --error-color: {colors['error']};
            --info-color: {colors['info']};
        }}
        
        /* Window styling */
        window {{
            background-color: {colors['background']};
            color: {colors['text_primary']};
            font-family: {VCCTLFonts.UI_FONT_FAMILY};
            font-size: {VCCTLFonts.FONT_SIZE_NORMAL}pt;
        }}
        
        /* Header bar styling */
        headerbar {{
            background: linear-gradient(to bottom, {colors['primary_light']}, {colors['primary']});
            color: {colors['text_on_primary']};
            border-bottom: 1px solid {colors['border']};
            min-height: 46px;
        }}
        
        headerbar button {{
            color: {colors['text_on_primary']};
            border: none;
            background: transparent;
            padding: {VCCTLSpacing.PADDING_SMALL}px;
            border-radius: {VCCTLSpacing.BORDER_RADIUS_NORMAL}px;
        }}
        
        headerbar button:hover {{
            background-color: rgba(255, 255, 255, 0.1);
        }}
        
        /* Notebook (tab) styling */
        notebook {{
            background-color: {colors['surface']};
            border: 1px solid {colors['border']};
            border-radius: {VCCTLSpacing.BORDER_RADIUS_NORMAL}px;
        }}
        
        notebook header {{
            background-color: {colors['background']};
            border-bottom: 1px solid {colors['border']};
        }}
        
        notebook tab {{
            padding: {VCCTLSpacing.PADDING_NORMAL}px {VCCTLSpacing.PADDING_LARGE}px;
            border: none;
            background-color: transparent;
            color: {colors['text_secondary']};
            font-weight: {VCCTLFonts.FONT_WEIGHT_MEDIUM};
        }}
        
        notebook tab:checked {{
            background-color: {colors['surface']};
            color: {colors['text_primary']};
            border-bottom: 2px solid {colors['primary_accent']};
        }}
        
        notebook tab:hover {{
            background-color: {colors['surface']};
            color: {colors['text_primary']};
        }}
        
        /* Button styling */
        button {{
            background: linear-gradient(to bottom, {colors['surface']}, {colors['background']});
            border: 1px solid {colors['border']};
            color: {colors['text_primary']};
            padding: {VCCTLSpacing.PADDING_SMALL}px {VCCTLSpacing.PADDING_NORMAL}px;
            border-radius: {VCCTLSpacing.BORDER_RADIUS_NORMAL}px;
            font-weight: {VCCTLFonts.FONT_WEIGHT_MEDIUM};
            min-height: 32px;
        }}
        
        button:hover {{
            background: linear-gradient(to bottom, {colors['primary_light']}, {colors['primary_accent']});
            border-color: {colors['primary_accent']};
            color: {colors['text_on_primary']};
        }}
        
        button:active {{
            background: {colors['primary']};
            border-color: {colors['primary']};
            color: {colors['text_on_primary']};
        }}
        
        button.suggested-action {{
            background: linear-gradient(to bottom, {colors['primary_accent']}, {colors['primary']});
            border-color: {colors['primary']};
            color: {colors['text_on_primary']};
        }}
        
        button.destructive-action {{
            background: linear-gradient(to bottom, {colors['error']}, #a54247);
            border-color: {colors['error']};
            color: white;
        }}
        
        /* Entry (text input) styling */
        entry {{
            background-color: {colors['surface']};
            border: 1px solid {colors['border']};
            color: {colors['text_primary']};
            padding: {VCCTLSpacing.PADDING_SMALL}px {VCCTLSpacing.PADDING_NORMAL}px;
            border-radius: {VCCTLSpacing.BORDER_RADIUS_NORMAL}px;
            min-height: 32px;
        }}
        
        entry:focus {{
            border-color: {colors['primary_accent']};
            box-shadow: 0 0 0 2px rgba(136, 192, 208, 0.2);
        }}
        
        entry:disabled {{
            background-color: {colors['background']};
            color: {colors['text_disabled']};
        }}
        
        /* TreeView styling */
        treeview {{
            background-color: {colors['surface']};
            color: {colors['text_primary']};
            border: 1px solid {colors['border']};
        }}
        
        treeview header {{
            background: linear-gradient(to bottom, {colors['background']}, {colors['surface']});
            border-bottom: 1px solid {colors['border']};
            font-weight: {VCCTLFonts.FONT_WEIGHT_MEDIUM};
        }}
        
        treeview header button {{
            background: transparent;
            border: none;
            border-right: 1px solid {colors['border']};
            padding: {VCCTLSpacing.PADDING_SMALL}px {VCCTLSpacing.PADDING_NORMAL}px;
        }}
        
        treeview:selected {{
            background-color: {colors['primary_accent']};
            color: {colors['text_on_primary']};
        }}
        
        /* ScrolledWindow styling */
        scrolledwindow {{
            border: 1px solid {colors['border']};
            border-radius: {VCCTLSpacing.BORDER_RADIUS_NORMAL}px;
        }}
        
        scrollbar {{
            background-color: {colors['background']};
            border-radius: {VCCTLSpacing.BORDER_RADIUS_SMALL}px;
        }}
        
        scrollbar slider {{
            background-color: {colors['border']};
            border-radius: {VCCTLSpacing.BORDER_RADIUS_SMALL}px;
            min-width: 8px;
            min-height: 8px;
        }}
        
        scrollbar slider:hover {{
            background-color: {colors['text_secondary']};
        }}
        
        /* Frame styling */
        frame {{
            border: 1px solid {colors['border']};
            border-radius: {VCCTLSpacing.BORDER_RADIUS_NORMAL}px;
            padding: {VCCTLSpacing.PADDING_NORMAL}px;
            background-color: {colors['surface']};
        }}
        
        frame > label {{
            color: {colors['text_secondary']};
            font-weight: {VCCTLFonts.FONT_WEIGHT_MEDIUM};
            margin-bottom: {VCCTLSpacing.SPACING_SM}px;
        }}
        
        /* MenuBar and Menu styling */
        menubar {{
            background-color: {colors['background']};
            border-bottom: 1px solid {colors['border']};
            padding: {VCCTLSpacing.PADDING_SMALL}px;
        }}
        
        menubar > menuitem {{
            padding: {VCCTLSpacing.PADDING_SMALL}px {VCCTLSpacing.PADDING_NORMAL}px;
            border-radius: {VCCTLSpacing.BORDER_RADIUS_SMALL}px;
        }}
        
        menubar > menuitem:hover {{
            background-color: {colors['primary_accent']};
            color: {colors['text_on_primary']};
        }}
        
        menu {{
            background-color: {colors['surface']};
            border: 1px solid {colors['border']};
            border-radius: {VCCTLSpacing.BORDER_RADIUS_NORMAL}px;
            padding: {VCCTLSpacing.PADDING_SMALL}px;
        }}
        
        menu menuitem {{
            padding: {VCCTLSpacing.PADDING_SMALL}px {VCCTLSpacing.PADDING_NORMAL}px;
            border-radius: {VCCTLSpacing.BORDER_RADIUS_SMALL}px;
        }}
        
        menu menuitem:hover {{
            background-color: {colors['primary_accent']};
            color: {colors['text_on_primary']};
        }}
        
        /* StatusBar styling */
        statusbar {{
            background-color: {colors['background']};
            border-top: 1px solid {colors['border']};
            padding: {VCCTLSpacing.PADDING_SMALL}px {VCCTLSpacing.PADDING_NORMAL}px;
            color: {colors['text_secondary']};
            font-size: {VCCTLFonts.FONT_SIZE_SMALL}pt;
        }}
        
        /* ProgressBar styling */
        progressbar {{
            background-color: {colors['background']};
            border: 1px solid {colors['border']};
            border-radius: {VCCTLSpacing.BORDER_RADIUS_NORMAL}px;
        }}
        
        progressbar progress {{
            background: linear-gradient(to right, {colors['primary_accent']}, {colors['primary_light']});
            border-radius: {VCCTLSpacing.BORDER_RADIUS_SMALL}px;
        }}
        
        /* Spinner styling */
        spinner {{
            color: {colors['primary_accent']};
        }}
        
        /* InfoBar styling */
        infobar {{
            border-radius: {VCCTLSpacing.BORDER_RADIUS_NORMAL}px;
            padding: {VCCTLSpacing.PADDING_NORMAL}px;
            margin: {VCCTLSpacing.MARGIN_SMALL}px;
        }}
        
        infobar.info {{
            background-color: {colors['info']};
            color: white;
        }}
        
        infobar.warning {{
            background-color: {colors['warning']};
            color: {colors['text_primary']};
        }}
        
        infobar.error {{
            background-color: {colors['error']};
            color: white;
        }}
        
        infobar.success {{
            background-color: {colors['success']};
            color: white;
        }}
        
        /* Dialog styling */
        dialog {{
            background-color: {colors['background']};
            border-radius: {VCCTLSpacing.BORDER_RADIUS_LARGE}px;
        }}
        
        dialog headerbar {{
            border-top-left-radius: {VCCTLSpacing.BORDER_RADIUS_LARGE}px;
            border-top-right-radius: {VCCTLSpacing.BORDER_RADIUS_LARGE}px;
        }}
        
        /* Tooltip styling */
        tooltip {{
            background-color: {colors['primary']};
            color: {colors['text_on_primary']};
            border-radius: {VCCTLSpacing.BORDER_RADIUS_NORMAL}px;
            padding: {VCCTLSpacing.PADDING_SMALL}px {VCCTLSpacing.PADDING_NORMAL}px;
            font-size: {VCCTLFonts.FONT_SIZE_SMALL}pt;
        }}
        
        /* Scientific data table styling */
        .scientific-table {{
            font-family: {VCCTLFonts.MONO_FONT_FAMILY};
            font-size: {VCCTLFonts.FONT_SIZE_SMALL}pt;
        }}
        
        .scientific-table treeview {{
            background-color: {colors['surface']};
        }}
        
        .scientific-table treeview:nth-child(even) {{
            background-color: {colors['background']};
        }}
        
        /* Material property styling */
        .material-property {{
            padding: {VCCTLSpacing.PADDING_SMALL}px;
            margin: {VCCTLSpacing.MARGIN_SMALL}px;
            border: 1px solid {colors['border']};
            border-radius: {VCCTLSpacing.BORDER_RADIUS_NORMAL}px;
            background-color: {colors['surface']};
        }}
        
        .material-property label {{
            font-weight: {VCCTLFonts.FONT_WEIGHT_MEDIUM};
            color: {colors['text_secondary']};
        }}
        
        /* Operation status styling */
        .status-running {{
            color: {colors['info']};
        }}
        
        .status-success {{
            color: {colors['success']};
        }}
        
        .status-error {{
            color: {colors['error']};
        }}
        
        .status-warning {{
            color: {colors['warning']};
        }}
        
        /* File browser styling */
        .file-browser treeview {{
            font-family: {VCCTLFonts.UI_FONT_FAMILY};
        }}
        
        .file-browser treeview row {{
            padding: {VCCTLSpacing.PADDING_SMALL}px;
        }}
        
        /* Keyboard focus styling */
        *:focus {{
            outline: 2px solid {colors['primary_accent']};
            outline-offset: 2px;
        }}
        
        /* High contrast mode adjustments */
        @media (prefers-contrast: high) {{
            * {{
                border-width: 2px;
            }}
            
            button {{
                border-width: 2px;
            }}
            
            entry {{
                border-width: 2px;
            }}
        }}
        """
        
        return css
    
    def _get_colors_for_scheme(self, scheme: ColorScheme) -> Dict[str, str]:
        """Get color dictionary for the specified scheme."""
        if scheme == ColorScheme.LIGHT:
            return {
                'primary': VCCTLColors.PRIMARY_BLUE,
                'primary_light': VCCTLColors.PRIMARY_LIGHT,
                'primary_accent': VCCTLColors.PRIMARY_ACCENT,
                'background': VCCTLColors.BACKGROUND_LIGHT,
                'surface': VCCTLColors.SURFACE_LIGHT,
                'text_primary': VCCTLColors.TEXT_PRIMARY,
                'text_secondary': VCCTLColors.TEXT_SECONDARY,
                'text_disabled': VCCTLColors.TEXT_DISABLED,
                'text_on_primary': VCCTLColors.TEXT_ON_PRIMARY,
                'border': VCCTLColors.BORDER_LIGHT,
                'success': VCCTLColors.STATUS_SUCCESS,
                'warning': VCCTLColors.STATUS_WARNING,
                'error': VCCTLColors.STATUS_ERROR,
                'info': VCCTLColors.STATUS_INFO,
            }
        elif scheme == ColorScheme.DARK:
            return {
                'primary': "#434C5E",
                'primary_light': "#5E81AC",
                'primary_accent': "#88C0D0",
                'background': "#2E3440",
                'surface': "#3B4252",
                'text_primary': "#ECEFF4",
                'text_secondary': "#D8DEE9",
                'text_disabled': "#4C566A",
                'text_on_primary': "#ECEFF4",
                'border': "#434C5E",
                'success': VCCTLColors.STATUS_SUCCESS,
                'warning': VCCTLColors.STATUS_WARNING,
                'error': VCCTLColors.STATUS_ERROR,
                'info': VCCTLColors.STATUS_INFO,
            }
        elif scheme == ColorScheme.HIGH_CONTRAST:
            return {
                'primary': "#000000",
                'primary_light': "#333333",
                'primary_accent': "#0066CC",
                'background': "#FFFFFF",
                'surface': "#F5F5F5",
                'text_primary': "#000000",
                'text_secondary': "#333333",
                'text_disabled': "#666666",
                'text_on_primary': "#FFFFFF",
                'border': "#000000",
                'success': "#006600",
                'warning': "#CC6600",
                'error': "#CC0000",
                'info': "#0066CC",
            }
        else:  # SCIENTIFIC (default)
            return {
                'primary': VCCTLColors.PRIMARY_BLUE,
                'primary_light': VCCTLColors.PRIMARY_LIGHT,
                'primary_accent': VCCTLColors.PRIMARY_ACCENT,
                'background': VCCTLColors.BACKGROUND_LIGHT,
                'surface': VCCTLColors.SURFACE_LIGHT,
                'text_primary': VCCTLColors.TEXT_PRIMARY,
                'text_secondary': VCCTLColors.TEXT_SECONDARY,
                'text_disabled': VCCTLColors.TEXT_DISABLED,
                'text_on_primary': VCCTLColors.TEXT_ON_PRIMARY,
                'border': VCCTLColors.BORDER_LIGHT,
                'success': VCCTLColors.STATUS_SUCCESS,
                'warning': VCCTLColors.STATUS_WARNING,
                'error': VCCTLColors.STATUS_ERROR,
                'info': VCCTLColors.STATUS_INFO,
            }
    
    def set_color_scheme(self, scheme: ColorScheme) -> None:
        """Set the application color scheme."""
        self.apply_theme(scheme)
    
    def get_current_scheme(self) -> ColorScheme:
        """Get the current color scheme."""
        return self.current_scheme
    
    def apply_widget_class(self, widget: Gtk.Widget, css_class: str) -> None:
        """Apply a CSS class to a widget."""
        style_context = widget.get_style_context()
        style_context.add_class(css_class)
    
    def create_styled_button(self, label: str, style_class: Optional[str] = None) -> Gtk.Button:
        """Create a consistently styled button."""
        button = Gtk.Button(label=label)
        if style_class:
            self.apply_widget_class(button, style_class)
        return button
    
    def create_styled_entry(self, placeholder: Optional[str] = None) -> Gtk.Entry:
        """Create a consistently styled entry."""
        entry = Gtk.Entry()
        if placeholder:
            entry.set_placeholder_text(placeholder)
        return entry
    
    def create_styled_frame(self, title: Optional[str] = None) -> Gtk.Frame:
        """Create a consistently styled frame."""
        frame = Gtk.Frame()
        if title:
            frame.set_label(title)
        return frame
    
    def create_scientific_table(self) -> Gtk.TreeView:
        """Create a scientific data table with appropriate styling."""
        treeview = Gtk.TreeView()
        self.apply_widget_class(treeview, "scientific-table")
        return treeview
    
    def get_status_color(self, status: str) -> str:
        """Get appropriate color for status indicators."""
        colors = self._get_colors_for_scheme(self.current_scheme)
        
        status_lower = status.lower()
        if 'success' in status_lower or 'complete' in status_lower:
            return colors['success']
        elif 'error' in status_lower or 'fail' in status_lower:
            return colors['error']
        elif 'warning' in status_lower or 'warn' in status_lower:
            return colors['warning']
        elif 'running' in status_lower or 'active' in status_lower:
            return colors['info']
        else:
            return colors['text_secondary']


# Global theme manager instance
_global_theme_manager: Optional[ThemeManager] = None


def get_theme_manager() -> ThemeManager:
    """Get the global theme manager instance."""
    global _global_theme_manager
    
    if _global_theme_manager is None:
        _global_theme_manager = ThemeManager()
    
    return _global_theme_manager


def apply_theme(scheme: Optional[ColorScheme] = None) -> None:
    """Convenience function to apply theme."""
    get_theme_manager().apply_theme(scheme)


def create_styled_widget(widget_type: type, **kwargs) -> Gtk.Widget:
    """Create a styled widget using the theme manager."""
    theme_manager = get_theme_manager()
    
    if widget_type == Gtk.Button:
        return theme_manager.create_styled_button(**kwargs)
    elif widget_type == Gtk.Entry:
        return theme_manager.create_styled_entry(**kwargs)
    elif widget_type == Gtk.Frame:
        return theme_manager.create_styled_frame(**kwargs)
    elif widget_type == Gtk.TreeView:
        return theme_manager.create_scientific_table()
    else:
        return widget_type()
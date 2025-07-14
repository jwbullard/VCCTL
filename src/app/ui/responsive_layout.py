#!/usr/bin/env python3
"""
VCCTL Responsive Layout Manager

Manages responsive layouts for different screen sizes and resolutions,
ensuring optimal user experience across various display configurations.
"""

import gi
import logging
from typing import Dict, Optional, List, Tuple, Callable, Any
from dataclasses import dataclass
from enum import Enum

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GObject


class ScreenSize(Enum):
    """Screen size categories."""
    COMPACT = "compact"      # < 1024x768
    NORMAL = "normal"        # 1024x768 to 1440x900
    LARGE = "large"          # 1440x900 to 1920x1080
    XLARGE = "xlarge"        # > 1920x1080


class LayoutMode(Enum):
    """Layout modes for different screen configurations."""
    COMPACT = "compact"      # Single column, stacked layout
    STANDARD = "standard"    # Traditional multi-column layout
    WIDE = "wide"           # Expanded layout for large screens
    SPLIT = "split"         # Side-by-side panels


@dataclass
class BreakPoint:
    """Responsive breakpoint definition."""
    name: str
    min_width: int
    min_height: int
    layout_mode: LayoutMode
    scaling_factor: float = 1.0


@dataclass
class LayoutConfiguration:
    """Layout configuration for a specific screen size."""
    screen_size: ScreenSize
    layout_mode: LayoutMode
    panel_arrangement: List[str]
    sidebar_width: int
    content_padding: int
    font_scale: float
    icon_scale: float
    spacing_scale: float


class ResponsiveLayoutManager(GObject.Object):
    """
    Manages responsive layouts for VCCTL application.
    
    Features:
    - Automatic layout adaptation based on screen size
    - Responsive breakpoints
    - Dynamic panel arrangement
    - Scalable fonts and icons
    - Adaptive spacing and padding
    - Screen orientation handling
    """
    
    __gsignals__ = {
        'layout-changed': (GObject.SignalFlags.RUN_FIRST, None, (str, str)),
        'breakpoint-changed': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
    }
    
    def __init__(self, main_window: Gtk.ApplicationWindow):
        super().__init__()
        self.logger = logging.getLogger('VCCTL.ResponsiveLayout')
        self.main_window = main_window
        
        # Current state
        self.current_screen_size = ScreenSize.NORMAL
        self.current_layout_mode = LayoutMode.STANDARD
        self.current_width = 0
        self.current_height = 0
        
        # Layout configurations
        self.configurations: Dict[ScreenSize, LayoutConfiguration] = {}
        self.breakpoints: List[BreakPoint] = []
        
        # Responsive callbacks
        self.resize_callbacks: List[Callable[[int, int], None]] = []
        self.layout_callbacks: List[Callable[[LayoutConfiguration], None]] = []
        
        # Setup responsive system
        self._setup_breakpoints()
        self._setup_configurations()
        self._setup_monitoring()
        
        # Apply initial layout
        self._detect_initial_size()
        self._apply_current_layout()
        
        self.logger.info("Responsive layout manager initialized")
    
    def _detect_initial_size(self) -> None:
        """Detect initial window size."""
        try:
            window_size = self.main_window.get_size()
            self.current_width = window_size.width
            self.current_height = window_size.height
            self.current_screen_size = self._determine_screen_size(self.current_width, self.current_height)
        except Exception as e:
            self.logger.error(f"Failed to detect initial size: {e}")
            # Set defaults
            self.current_width = 1200
            self.current_height = 800
            self.current_screen_size = ScreenSize.NORMAL
    
    def _apply_current_layout(self) -> None:
        """Apply layout for current screen size."""
        if self.current_screen_size in self.configurations:
            config = self.configurations[self.current_screen_size]
            self.current_layout_mode = config.layout_mode
            self._apply_layout_configuration(config)
        
        self.logger.info("Responsive layout manager initialized")
    
    def _setup_breakpoints(self) -> None:
        """Setup responsive breakpoints."""
        self.breakpoints = [
            BreakPoint("compact", 0, 0, LayoutMode.COMPACT, 0.9),
            BreakPoint("normal", 1024, 768, LayoutMode.STANDARD, 1.0),
            BreakPoint("large", 1440, 900, LayoutMode.WIDE, 1.1),
            BreakPoint("xlarge", 1920, 1080, LayoutMode.WIDE, 1.2),
        ]
    
    def _setup_configurations(self) -> None:
        """Setup layout configurations for different screen sizes."""
        
        # Compact layout (small screens, mobile-like)
        self.configurations[ScreenSize.COMPACT] = LayoutConfiguration(
            screen_size=ScreenSize.COMPACT,
            layout_mode=LayoutMode.COMPACT,
            panel_arrangement=["materials", "mix_design", "microstructure", "hydration"],
            sidebar_width=0,  # No sidebar in compact mode
            content_padding=8,
            font_scale=0.9,
            icon_scale=0.8,
            spacing_scale=0.8
        )
        
        # Normal layout (standard desktop)
        self.configurations[ScreenSize.NORMAL] = LayoutConfiguration(
            screen_size=ScreenSize.NORMAL,
            layout_mode=LayoutMode.STANDARD,
            panel_arrangement=["materials", "mix_design", "microstructure", "hydration", "file_management", "operations"],
            sidebar_width=250,
            content_padding=12,
            font_scale=1.0,
            icon_scale=1.0,
            spacing_scale=1.0
        )
        
        # Large layout (wide desktop)
        self.configurations[ScreenSize.LARGE] = LayoutConfiguration(
            screen_size=ScreenSize.LARGE,
            layout_mode=LayoutMode.WIDE,
            panel_arrangement=["materials", "mix_design", "microstructure", "hydration", "file_management", "operations"],
            sidebar_width=300,
            content_padding=16,
            font_scale=1.1,
            icon_scale=1.1,
            spacing_scale=1.2
        )
        
        # Extra large layout (ultra-wide displays)
        self.configurations[ScreenSize.XLARGE] = LayoutConfiguration(
            screen_size=ScreenSize.XLARGE,
            layout_mode=LayoutMode.SPLIT,
            panel_arrangement=["materials", "mix_design", "microstructure", "hydration", "file_management", "operations"],
            sidebar_width=350,
            content_padding=20,
            font_scale=1.2,
            icon_scale=1.2,
            spacing_scale=1.4
        )
    
    def _setup_monitoring(self) -> None:
        """Setup window size monitoring."""
        # Connect to window size changes
        self.main_window.connect('size-allocate', self._on_window_size_changed)
        self.main_window.connect('window-state-event', self._on_window_state_changed)
        
        # Monitor screen changes
        screen = self.main_window.get_screen()
        if screen:
            screen.connect('size-changed', self._on_screen_changed)
    
    def _detect_initial_layout(self) -> None:
        """Detect initial layout based on current window size."""
        window_size = self.main_window.get_size()
        self._update_layout(window_size.width, window_size.height)
    
    def _on_window_size_changed(self, widget: Gtk.Widget, allocation: Gdk.Rectangle) -> None:
        """Handle window size changes."""
        self._update_layout(allocation.width, allocation.height)
    
    def _on_window_state_changed(self, widget: Gtk.Widget, event: Gdk.EventWindowState) -> None:
        """Handle window state changes (maximize, fullscreen, etc.)."""
        # Trigger layout update when window state changes
        window_size = self.main_window.get_size()
        self._update_layout(window_size.width, window_size.height)
    
    def _on_screen_changed(self, screen: Gdk.Screen) -> None:
        """Handle screen configuration changes."""
        # Monitor for screen resolution changes, multiple monitors, etc.
        window_size = self.main_window.get_size()
        self._update_layout(window_size.width, window_size.height)
    
    def _update_layout(self, width: int, height: int) -> None:
        """Update layout based on new dimensions."""
        if width == self.current_width and height == self.current_height:
            return  # No change
        
        self.current_width = width
        self.current_height = height
        
        # Determine new screen size and layout
        new_screen_size = self._determine_screen_size(width, height)
        new_breakpoint = self._find_active_breakpoint(width, height)
        
        if new_screen_size != self.current_screen_size:
            self.current_screen_size = new_screen_size
            self.current_layout_mode = self.configurations[new_screen_size].layout_mode
            
            # Apply new layout
            self._apply_layout_configuration(self.configurations[new_screen_size])
            
            # Emit signals
            self.emit('layout-changed', new_screen_size.value, self.current_layout_mode.value)
            if new_breakpoint:
                self.emit('breakpoint-changed', new_breakpoint.name)
            
            self.logger.info(f"Layout changed to {new_screen_size.value} ({width}x{height})")
        
        # Notify resize callbacks
        for callback in self.resize_callbacks:
            try:
                callback(width, height)
            except Exception as e:
                self.logger.error(f"Resize callback error: {e}")
    
    def _determine_screen_size(self, width: int, height: int) -> ScreenSize:
        """Determine screen size category based on dimensions."""
        if width < 1024 or height < 768:
            return ScreenSize.COMPACT
        elif width < 1440 or height < 900:
            return ScreenSize.NORMAL
        elif width < 1920 or height < 1080:
            return ScreenSize.LARGE
        else:
            return ScreenSize.XLARGE
    
    def _find_active_breakpoint(self, width: int, height: int) -> Optional[BreakPoint]:
        """Find the active breakpoint for given dimensions."""
        active_breakpoint = None
        
        for breakpoint in sorted(self.breakpoints, key=lambda bp: bp.min_width, reverse=True):
            if width >= breakpoint.min_width and height >= breakpoint.min_height:
                active_breakpoint = breakpoint
                break
        
        return active_breakpoint or self.breakpoints[0]  # Default to first breakpoint
    
    def _apply_layout_configuration(self, config: LayoutConfiguration) -> None:
        """Apply a layout configuration to the application."""
        try:
            # Apply scaling
            self._apply_scaling(config)
            
            # Apply layout mode
            self._apply_layout_mode(config)
            
            # Apply spacing and padding
            self._apply_spacing(config)
            
            # Notify layout callbacks
            for callback in self.layout_callbacks:
                try:
                    callback(config)
                except Exception as e:
                    self.logger.error(f"Layout callback error: {e}")
            
        except Exception as e:
            self.logger.error(f"Failed to apply layout configuration: {e}")
    
    def _apply_scaling(self, config: LayoutConfiguration) -> None:
        """Apply font and icon scaling."""
        try:
            # Apply through theme manager if available
            from app.ui.theme_manager import get_theme_manager
            theme_manager = get_theme_manager()
            
            # CSS for scaling
            scaling_css = f"""
            * {{
                font-size: {config.font_scale}em;
            }}
            
            image {{
                -gtk-icon-transform: scale({config.icon_scale});
            }}
            """
            
            # Apply scaling (would need theme manager support)
            
        except ImportError:
            self.logger.debug("Theme manager not available for scaling")
    
    def _apply_layout_mode(self, config: LayoutConfiguration) -> None:
        """Apply layout mode changes."""
        if config.layout_mode == LayoutMode.COMPACT:
            self._apply_compact_layout()
        elif config.layout_mode == LayoutMode.STANDARD:
            self._apply_standard_layout()
        elif config.layout_mode == LayoutMode.WIDE:
            self._apply_wide_layout()
        elif config.layout_mode == LayoutMode.SPLIT:
            self._apply_split_layout()
    
    def _apply_compact_layout(self) -> None:
        """Apply compact layout for small screens."""
        # Single column layout, stacked panels
        # Hide or minimize sidebars
        # Smaller buttons and controls
        self.logger.debug("Applying compact layout")
    
    def _apply_standard_layout(self) -> None:
        """Apply standard layout for normal screens."""
        # Traditional multi-column layout
        # Normal sidebar width
        # Standard button and control sizes
        self.logger.debug("Applying standard layout")
    
    def _apply_wide_layout(self) -> None:
        """Apply wide layout for large screens."""
        # Expanded layout with more content visible
        # Wider sidebars
        # Larger spacing
        self.logger.debug("Applying wide layout")
    
    def _apply_split_layout(self) -> None:
        """Apply split layout for ultra-wide screens."""
        # Side-by-side panel arrangement
        # Multiple content areas
        # Maximized screen real estate usage
        self.logger.debug("Applying split layout")
    
    def _apply_spacing(self, config: LayoutConfiguration) -> None:
        """Apply spacing and padding configuration."""
        spacing_css = f"""
        .responsive-container {{
            padding: {config.content_padding}px;
        }}
        
        .responsive-spacing {{
            margin: {int(8 * config.spacing_scale)}px;
        }}
        
        .responsive-padding {{
            padding: {int(12 * config.spacing_scale)}px;
        }}
        """
        
        try:
            from app.ui.theme_manager import get_theme_manager
            theme_manager = get_theme_manager()
            # Apply spacing CSS (would need theme manager support)
        except ImportError:
            pass
    
    def add_resize_callback(self, callback: Callable[[int, int], None]) -> None:
        """Add callback for window resize events."""
        self.resize_callbacks.append(callback)
    
    def remove_resize_callback(self, callback: Callable[[int, int], None]) -> None:
        """Remove resize callback."""
        if callback in self.resize_callbacks:
            self.resize_callbacks.remove(callback)
    
    def add_layout_callback(self, callback: Callable[[LayoutConfiguration], None]) -> None:
        """Add callback for layout changes."""
        self.layout_callbacks.append(callback)
    
    def remove_layout_callback(self, callback: Callable[[LayoutConfiguration], None]) -> None:
        """Remove layout callback."""
        if callback in self.layout_callbacks:
            self.layout_callbacks.remove(callback)
    
    def get_current_configuration(self) -> LayoutConfiguration:
        """Get current layout configuration."""
        return self.configurations[self.current_screen_size]
    
    def get_screen_size(self) -> ScreenSize:
        """Get current screen size category."""
        return self.current_screen_size
    
    def get_layout_mode(self) -> LayoutMode:
        """Get current layout mode."""
        return self.current_layout_mode
    
    def get_dimensions(self) -> Tuple[int, int]:
        """Get current window dimensions."""
        return (self.current_width, self.current_height)
    
    def force_layout_mode(self, mode: LayoutMode) -> None:
        """Force a specific layout mode (override responsive behavior)."""
        # Find configuration with this mode
        for config in self.configurations.values():
            if config.layout_mode == mode:
                self.current_layout_mode = mode
                self._apply_layout_configuration(config)
                self.emit('layout-changed', self.current_screen_size.value, mode.value)
                break
    
    def set_custom_breakpoint(self, name: str, min_width: int, min_height: int, 
                             layout_mode: LayoutMode, scaling_factor: float = 1.0) -> None:
        """Add custom breakpoint."""
        breakpoint = BreakPoint(name, min_width, min_height, layout_mode, scaling_factor)
        self.breakpoints.append(breakpoint)
        
        # Sort breakpoints by width
        self.breakpoints.sort(key=lambda bp: bp.min_width)
    
    def get_optimal_panel_size(self, panel_type: str) -> Tuple[int, int]:
        """Get optimal panel size for current layout."""
        config = self.get_current_configuration()
        
        base_width = max(300, self.current_width // 3)
        base_height = max(200, self.current_height // 2)
        
        # Adjust based on layout mode
        if config.layout_mode == LayoutMode.COMPACT:
            width = min(base_width, self.current_width - 40)
            height = base_height // 2
        elif config.layout_mode == LayoutMode.SPLIT:
            width = self.current_width // 2 - config.sidebar_width
            height = self.current_height - 100
        else:
            width = base_width
            height = base_height
        
        return (int(width * config.font_scale), int(height * config.font_scale))
    
    def is_mobile_layout(self) -> bool:
        """Check if current layout is mobile-like."""
        return self.current_screen_size == ScreenSize.COMPACT
    
    def is_wide_layout(self) -> bool:
        """Check if current layout is wide screen."""
        return self.current_screen_size in [ScreenSize.LARGE, ScreenSize.XLARGE]
    
    def get_layout_info(self) -> Dict[str, Any]:
        """Get comprehensive layout information."""
        config = self.get_current_configuration()
        
        return {
            'screen_size': self.current_screen_size.value,
            'layout_mode': self.current_layout_mode.value,
            'dimensions': (self.current_width, self.current_height),
            'is_mobile': self.is_mobile_layout(),
            'is_wide': self.is_wide_layout(),
            'configuration': {
                'sidebar_width': config.sidebar_width,
                'content_padding': config.content_padding,
                'font_scale': config.font_scale,
                'icon_scale': config.icon_scale,
                'spacing_scale': config.spacing_scale
            },
            'active_breakpoint': self._find_active_breakpoint(self.current_width, self.current_height).name
        }


def create_responsive_layout_manager(main_window: Gtk.ApplicationWindow) -> ResponsiveLayoutManager:
    """Create and configure responsive layout manager."""
    return ResponsiveLayoutManager(main_window)
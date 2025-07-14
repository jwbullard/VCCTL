#!/usr/bin/env python3
"""
VCCTL UI Module

Comprehensive user interface management for VCCTL application including
theming, accessibility, keyboard shortcuts, responsive layout, and professional polish.
"""

from .theme_manager import (
    ThemeManager, 
    get_theme_manager, 
    apply_theme,
    create_styled_widget,
    ColorScheme,
    VCCTLColors,
    VCCTLFonts,
    VCCTLSpacing
)

from .keyboard_manager import (
    KeyboardManager,
    create_keyboard_manager,
    ShortcutCategory,
    KeyboardShortcut
)

from .accessibility_manager import (
    AccessibilityManager,
    create_accessibility_manager,
    AccessibilityLevel,
    FocusIndicatorStyle
)

from .responsive_layout import (
    ResponsiveLayoutManager,
    create_responsive_layout_manager,
    ScreenSize,
    LayoutMode,
    LayoutConfiguration
)

from .ui_polish import (
    UIPolishManager,
    create_ui_polish_manager
)

__all__ = [
    # Theme management
    'ThemeManager',
    'get_theme_manager',
    'apply_theme',
    'create_styled_widget',
    'ColorScheme',
    'VCCTLColors',
    'VCCTLFonts', 
    'VCCTLSpacing',
    
    # Keyboard shortcuts
    'KeyboardManager',
    'create_keyboard_manager',
    'ShortcutCategory',
    'KeyboardShortcut',
    
    # Accessibility
    'AccessibilityManager',
    'create_accessibility_manager',
    'AccessibilityLevel',
    'FocusIndicatorStyle',
    
    # Responsive layout
    'ResponsiveLayoutManager',
    'create_responsive_layout_manager',
    'ScreenSize',
    'LayoutMode',
    'LayoutConfiguration',
    
    # UI polish coordination
    'UIPolishManager',
    'create_ui_polish_manager'
]
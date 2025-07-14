#!/usr/bin/env python3
"""
VCCTL Accessibility Manager

Provides comprehensive accessibility features for VCCTL application including
screen reader support, high contrast mode, keyboard navigation, and ARIA compliance.
"""

import gi
import logging
from typing import Dict, Optional, List, Callable, Any
from enum import Enum

gi.require_version('Gtk', '3.0')
gi.require_version('Atk', '1.0')
from gi.repository import Gtk, Atk, GObject, Gdk


class AccessibilityLevel(Enum):
    """Accessibility enhancement levels."""
    BASIC = "basic"
    ENHANCED = "enhanced"
    HIGH_CONTRAST = "high_contrast"
    SCREEN_READER = "screen_reader"


class FocusIndicatorStyle(Enum):
    """Focus indicator visual styles."""
    SUBTLE = "subtle"
    NORMAL = "normal"
    HIGH_CONTRAST = "high_contrast"
    CUSTOM = "custom"


class AccessibilityManager(GObject.Object):
    """
    Manages accessibility features for VCCTL application.
    
    Features:
    - Screen reader support with ARIA labels
    - High contrast mode
    - Keyboard navigation enhancement
    - Focus indicators
    - Text scaling
    - Audio feedback
    - Accessibility shortcuts
    """
    
    __gsignals__ = {
        'accessibility-changed': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        'focus-changed': (GObject.SignalFlags.RUN_FIRST, None, (object,)),
    }
    
    def __init__(self, main_window: Gtk.ApplicationWindow):
        super().__init__()
        self.logger = logging.getLogger('VCCTL.AccessibilityManager')
        self.main_window = main_window
        
        # Accessibility settings
        self.accessibility_level = AccessibilityLevel.BASIC
        self.focus_indicator_style = FocusIndicatorStyle.NORMAL
        self.text_scale_factor = 1.0
        self.high_contrast_enabled = False
        self.screen_reader_enabled = False
        self.audio_feedback_enabled = False
        
        # Widget registry for accessibility
        self.accessible_widgets: Dict[str, Gtk.Widget] = {}
        self.focus_history: List[Gtk.Widget] = []
        
        # Initialize accessibility
        self._setup_accessibility()
        
        self.logger.info("Accessibility manager initialized")
    
    def _setup_accessibility(self) -> None:
        """Setup initial accessibility configuration."""
        # Check system accessibility settings
        self._detect_system_accessibility()
        
        # Setup focus tracking
        self._setup_focus_tracking()
        
        # Apply initial accessibility settings
        self._apply_accessibility_settings()
    
    def _detect_system_accessibility(self) -> None:
        """Detect system-level accessibility settings."""
        try:
            # Check for screen reader
            if self._is_screen_reader_active():
                self.screen_reader_enabled = True
                self.accessibility_level = AccessibilityLevel.SCREEN_READER
                self.logger.info("Screen reader detected")
            
            # Check for high contrast
            if self._is_high_contrast_active():
                self.high_contrast_enabled = True
                if self.accessibility_level == AccessibilityLevel.BASIC:
                    self.accessibility_level = AccessibilityLevel.HIGH_CONTRAST
                self.logger.info("High contrast mode detected")
                
        except Exception as e:
            self.logger.warning(f"Failed to detect system accessibility: {e}")
    
    def _is_screen_reader_active(self) -> bool:
        """Check if a screen reader is active."""
        try:
            # Check ATK registry
            registry = Atk.get_default_registry()
            return registry is not None
        except:
            return False
    
    def _is_high_contrast_active(self) -> bool:
        """Check if high contrast mode is active."""
        try:
            settings = Gtk.Settings.get_default()
            theme_name = settings.get_property("gtk-theme-name")
            return "high-contrast" in theme_name.lower() or "hc" in theme_name.lower()
        except:
            return False
    
    def _setup_focus_tracking(self) -> None:
        """Setup focus tracking for accessibility."""
        def on_focus_changed(window, widget):
            if widget:
                self._on_widget_focused(widget)
        
        self.main_window.connect('set-focus', on_focus_changed)
    
    def _apply_accessibility_settings(self) -> None:
        """Apply current accessibility settings."""
        if self.accessibility_level in [AccessibilityLevel.ENHANCED, AccessibilityLevel.SCREEN_READER]:
            self._enable_enhanced_accessibility()
        
        if self.high_contrast_enabled:
            self._enable_high_contrast()
        
        if self.screen_reader_enabled:
            self._enable_screen_reader_support()
    
    def _enable_enhanced_accessibility(self) -> None:
        """Enable enhanced accessibility features."""
        # Enhanced focus indicators
        self._apply_focus_enhancements()
        
        # Enhanced keyboard navigation
        self._enable_enhanced_keyboard_nav()
        
        # Tooltip enhancements
        self._enhance_tooltips()
    
    def _enable_high_contrast(self) -> None:
        """Enable high contrast mode."""
        # This would work with the theme manager
        try:
            from app.ui.theme_manager import get_theme_manager, ColorScheme
            theme_manager = get_theme_manager()
            theme_manager.set_color_scheme(ColorScheme.HIGH_CONTRAST)
        except ImportError:
            self.logger.warning("Theme manager not available for high contrast")
    
    def _enable_screen_reader_support(self) -> None:
        """Enable comprehensive screen reader support."""
        # Enhanced ARIA labels
        self._apply_aria_enhancements()
        
        # Audio feedback
        self.audio_feedback_enabled = True
        
        # Detailed descriptions
        self._add_detailed_descriptions()
    
    def register_widget(self, widget_id: str, widget: Gtk.Widget, 
                       accessibility_info: Optional[Dict[str, Any]] = None) -> None:
        """Register a widget for accessibility management."""
        self.accessible_widgets[widget_id] = widget
        
        if accessibility_info:
            self._apply_widget_accessibility(widget, accessibility_info)
        
        # Add basic accessibility if screen reader is enabled
        if self.screen_reader_enabled:
            self._enhance_widget_for_screen_reader(widget)
    
    def _apply_widget_accessibility(self, widget: Gtk.Widget, info: Dict[str, Any]) -> None:
        """Apply accessibility information to a widget."""
        try:
            accessible = widget.get_accessible()
            if accessible:
                # Set accessible name
                if 'name' in info:
                    accessible.set_name(info['name'])
                
                # Set accessible description
                if 'description' in info:
                    accessible.set_description(info['description'])
                
                # Set accessible role
                if 'role' in info:
                    role = getattr(Atk.Role, info['role'].upper(), None)
                    if role:
                        accessible.set_role(role)
            
            # Set tooltip as fallback
            if 'tooltip' in info:
                widget.set_tooltip_text(info['tooltip'])
            
        except Exception as e:
            self.logger.error(f"Failed to apply accessibility info: {e}")
    
    def _enhance_widget_for_screen_reader(self, widget: Gtk.Widget) -> None:
        """Enhance widget for screen reader accessibility."""
        try:
            accessible = widget.get_accessible()
            if not accessible:
                return
            
            # Add state information
            if isinstance(widget, Gtk.Button):
                accessible.set_role(Atk.Role.PUSH_BUTTON)
                if not accessible.get_name():
                    label = widget.get_label()
                    if label:
                        accessible.set_name(label)
            
            elif isinstance(widget, Gtk.Entry):
                accessible.set_role(Atk.Role.ENTRY)
                placeholder = widget.get_placeholder_text()
                if placeholder and not accessible.get_description():
                    accessible.set_description(f"Input field: {placeholder}")
            
            elif isinstance(widget, Gtk.TreeView):
                accessible.set_role(Atk.Role.TREE_TABLE)
                if not accessible.get_description():
                    accessible.set_description("Data table with selectable rows")
            
            elif isinstance(widget, Gtk.ProgressBar):
                accessible.set_role(Atk.Role.PROGRESS_BAR)
                if not accessible.get_description():
                    accessible.set_description("Progress indicator")
            
            elif isinstance(widget, Gtk.Notebook):
                accessible.set_role(Atk.Role.PAGE_TAB_LIST)
                if not accessible.get_description():
                    accessible.set_description("Tabbed interface")
            
        except Exception as e:
            self.logger.error(f"Failed to enhance widget for screen reader: {e}")
    
    def _apply_focus_enhancements(self) -> None:
        """Apply enhanced focus indicators."""
        # This would be implemented through CSS
        css_enhancement = """
        *:focus {
            outline: 3px solid #0078d4;
            outline-offset: 2px;
        }
        
        button:focus {
            box-shadow: 0 0 0 3px rgba(0, 120, 212, 0.3);
        }
        
        entry:focus {
            border: 2px solid #0078d4;
            box-shadow: 0 0 0 2px rgba(0, 120, 212, 0.2);
        }
        """
        
        try:
            from app.ui.theme_manager import get_theme_manager
            theme_manager = get_theme_manager()
            # Add enhancement CSS (would need to be implemented in theme manager)
        except ImportError:
            pass
    
    def _enable_enhanced_keyboard_nav(self) -> None:
        """Enable enhanced keyboard navigation."""
        # Add arrow key navigation for custom widgets
        def on_key_press(widget, event):
            if event.keyval in [Gdk.KEY_Up, Gdk.KEY_Down, Gdk.KEY_Left, Gdk.KEY_Right]:
                return self._handle_arrow_navigation(widget, event)
            return False
        
        self.main_window.connect('key-press-event', on_key_press)
    
    def _handle_arrow_navigation(self, widget: Gtk.Widget, event: Gdk.EventKey) -> bool:
        """Handle arrow key navigation."""
        try:
            # Get current focus
            focused = self.main_window.get_focus()
            if not focused:
                return False
            
            # Find appropriate navigation target
            container = focused.get_parent()
            if not container:
                return False
            
            # Simple navigation logic - can be enhanced
            children = []
            if hasattr(container, 'get_children'):
                children = container.get_children()
            
            if not children:
                return False
            
            current_index = -1
            try:
                current_index = children.index(focused)
            except ValueError:
                return False
            
            new_index = current_index
            if event.keyval in [Gdk.KEY_Right, Gdk.KEY_Down]:
                new_index = min(current_index + 1, len(children) - 1)
            elif event.keyval in [Gdk.KEY_Left, Gdk.KEY_Up]:
                new_index = max(current_index - 1, 0)
            
            if new_index != current_index and new_index < len(children):
                target = children[new_index]
                if target.get_can_focus():
                    target.grab_focus()
                    return True
            
        except Exception as e:
            self.logger.error(f"Arrow navigation error: {e}")
        
        return False
    
    def _enhance_tooltips(self) -> None:
        """Enhance tooltips for accessibility."""
        # Longer tooltip display time
        settings = Gtk.Settings.get_default()
        settings.set_property("gtk-tooltip-timeout", 2000)  # 2 seconds
    
    def _apply_aria_enhancements(self) -> None:
        """Apply ARIA enhancements for screen readers."""
        # This would enhance all registered widgets with comprehensive ARIA labels
        for widget_id, widget in self.accessible_widgets.items():
            self._add_comprehensive_aria_labels(widget, widget_id)
    
    def _add_comprehensive_aria_labels(self, widget: Gtk.Widget, widget_id: str) -> None:
        """Add comprehensive ARIA labels to a widget."""
        try:
            accessible = widget.get_accessible()
            if not accessible:
                return
            
            # Generate descriptive labels based on widget type and context
            if isinstance(widget, Gtk.Button):
                label = widget.get_label() or "Button"
                accessible.set_name(f"{label} button")
                accessible.set_description(f"Activate {label.lower()} action")
            
            elif isinstance(widget, Gtk.Entry):
                placeholder = widget.get_placeholder_text()
                if placeholder:
                    accessible.set_name(f"{placeholder} input field")
                    accessible.set_description(f"Enter {placeholder.lower()}")
                else:
                    accessible.set_name("Text input field")
            
            elif isinstance(widget, Gtk.ComboBox):
                accessible.set_name("Selection dropdown")
                accessible.set_description("Choose from available options")
            
            elif isinstance(widget, Gtk.CheckButton):
                label = widget.get_label() or "Option"
                accessible.set_name(f"{label} checkbox")
                accessible.set_description(f"Toggle {label.lower()} option")
            
            elif isinstance(widget, Gtk.RadioButton):
                label = widget.get_label() or "Choice"
                accessible.set_name(f"{label} radio button")
                accessible.set_description(f"Select {label.lower()} option")
            
        except Exception as e:
            self.logger.error(f"Failed to add ARIA labels: {e}")
    
    def _add_detailed_descriptions(self) -> None:
        """Add detailed descriptions for complex widgets."""
        for widget_id, widget in self.accessible_widgets.items():
            self._add_detailed_widget_description(widget, widget_id)
    
    def _add_detailed_widget_description(self, widget: Gtk.Widget, widget_id: str) -> None:
        """Add detailed description to a specific widget."""
        descriptions = {
            'materials_table': "Table containing material properties. Use arrow keys to navigate, Enter to select.",
            'mix_design_form': "Form for designing concrete mix. Tab through fields to enter values.",
            'microstructure_view': "Microstructure visualization. Image showing generated concrete structure.",
            'hydration_controls': "Hydration simulation controls. Start, pause, or stop simulation operations.",
            'file_browser': "File browser for importing and exporting data. Navigate files and folders.",
            'operations_monitor': "Operations monitoring panel. View running simulations and their progress."
        }
        
        if widget_id in descriptions:
            try:
                accessible = widget.get_accessible()
                if accessible:
                    accessible.set_description(descriptions[widget_id])
            except Exception as e:
                self.logger.error(f"Failed to set description for {widget_id}: {e}")
    
    def _on_widget_focused(self, widget: Gtk.Widget) -> None:
        """Handle widget focus change."""
        # Add to focus history
        self.focus_history.append(widget)
        if len(self.focus_history) > 50:  # Keep last 50 focus changes
            self.focus_history.pop(0)
        
        # Emit signal
        self.emit('focus-changed', widget)
        
        # Audio feedback if enabled
        if self.audio_feedback_enabled:
            self._provide_audio_feedback(widget)
        
        # Screen reader announcements
        if self.screen_reader_enabled:
            self._announce_widget_focus(widget)
    
    def _provide_audio_feedback(self, widget: Gtk.Widget) -> None:
        """Provide audio feedback for widget focus."""
        # Simple audio feedback implementation
        # In a real implementation, this would use audio libraries
        self.logger.debug(f"Audio feedback for {widget.__class__.__name__}")
    
    def _announce_widget_focus(self, widget: Gtk.Widget) -> None:
        """Announce widget focus to screen reader."""
        try:
            accessible = widget.get_accessible()
            if accessible:
                name = accessible.get_name()
                description = accessible.get_description()
                
                announcement = name or widget.__class__.__name__
                if description:
                    announcement += f". {description}"
                
                # In a real implementation, this would interface with screen reader APIs
                self.logger.debug(f"Screen reader announcement: {announcement}")
                
        except Exception as e:
            self.logger.error(f"Failed to announce widget focus: {e}")
    
    def set_accessibility_level(self, level: AccessibilityLevel) -> None:
        """Set the accessibility enhancement level."""
        self.accessibility_level = level
        self._apply_accessibility_settings()
        self.emit('accessibility-changed', level.value)
    
    def toggle_high_contrast(self) -> None:
        """Toggle high contrast mode."""
        self.high_contrast_enabled = not self.high_contrast_enabled
        if self.high_contrast_enabled:
            self._enable_high_contrast()
        else:
            # Restore normal theme
            try:
                from app.ui.theme_manager import get_theme_manager, ColorScheme
                theme_manager = get_theme_manager()
                theme_manager.set_color_scheme(ColorScheme.SCIENTIFIC)
            except ImportError:
                pass
    
    def set_text_scale(self, scale_factor: float) -> None:
        """Set text scaling factor."""
        self.text_scale_factor = max(0.5, min(3.0, scale_factor))  # Clamp between 0.5x and 3.0x
        
        # Apply text scaling through CSS
        css_scaling = f"""
        * {{
            font-size: {self.text_scale_factor}em;
        }}
        """
        
        try:
            from app.ui.theme_manager import get_theme_manager
            theme_manager = get_theme_manager()
            # Apply scaling (would need to be implemented in theme manager)
        except ImportError:
            pass
    
    def get_accessibility_info(self) -> Dict[str, Any]:
        """Get current accessibility configuration."""
        return {
            'level': self.accessibility_level.value,
            'high_contrast': self.high_contrast_enabled,
            'screen_reader': self.screen_reader_enabled,
            'audio_feedback': self.audio_feedback_enabled,
            'text_scale': self.text_scale_factor,
            'focus_style': self.focus_indicator_style.value,
            'registered_widgets': len(self.accessible_widgets)
        }
    
    def export_accessibility_report(self) -> str:
        """Export accessibility compliance report."""
        report = []
        report.append("VCCTL Accessibility Compliance Report")
        report.append("=" * 40)
        report.append(f"Accessibility Level: {self.accessibility_level.value}")
        report.append(f"High Contrast: {'Enabled' if self.high_contrast_enabled else 'Disabled'}")
        report.append(f"Screen Reader Support: {'Enabled' if self.screen_reader_enabled else 'Disabled'}")
        report.append(f"Registered Widgets: {len(self.accessible_widgets)}")
        report.append("")
        
        report.append("Widget Accessibility Status:")
        report.append("-" * 30)
        
        for widget_id, widget in self.accessible_widgets.items():
            try:
                accessible = widget.get_accessible()
                name = accessible.get_name() if accessible else "No name"
                description = accessible.get_description() if accessible else "No description"
                
                report.append(f"Widget: {widget_id}")
                report.append(f"  Type: {widget.__class__.__name__}")
                report.append(f"  Name: {name}")
                report.append(f"  Description: {description}")
                report.append(f"  Can Focus: {widget.get_can_focus()}")
                report.append("")
                
            except Exception as e:
                report.append(f"Widget: {widget_id} - Error: {e}")
                report.append("")
        
        return "\n".join(report)


def create_accessibility_manager(main_window: Gtk.ApplicationWindow) -> AccessibilityManager:
    """Create and configure accessibility manager."""
    return AccessibilityManager(main_window)
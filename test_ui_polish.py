#!/usr/bin/env python3
"""
VCCTL UI Polish Test Suite

Test script to verify all UI polish features are working correctly including
theming, accessibility, keyboard shortcuts, responsive layout, and professional appearance.
"""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject

from app.ui import (
    create_ui_polish_manager,
    get_theme_manager,
    ColorScheme,
    AccessibilityLevel,
    ScreenSize
)


class UIPolishTestWindow(Gtk.ApplicationWindow):
    """Test window for UI polish features."""
    
    def __init__(self):
        super().__init__()
        
        # Setup logging
        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger('UIPolishTest')
        
        # Window setup
        self.set_title("VCCTL UI Polish Test")
        self.set_default_size(1000, 700)
        self.set_position(Gtk.WindowPosition.CENTER)
        
        # Initialize UI polish manager
        self.ui_polish_manager = create_ui_polish_manager(self)
        
        # Setup test UI
        self._setup_test_ui()
        
        # Connect signals
        self.connect('destroy', Gtk.main_quit)
        
        self.logger.info("UI Polish test window initialized")
    
    def _setup_test_ui(self):
        """Setup test UI components."""
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        main_box.set_margin_left(20)
        main_box.set_margin_right(20)
        main_box.set_margin_top(20)
        main_box.set_margin_bottom(20)
        self.add(main_box)
        
        # Title
        title = Gtk.Label()
        title.set_markup("<span size='x-large'><b>VCCTL UI Polish Feature Test</b></span>")
        title.set_margin_bottom(20)
        main_box.pack_start(title, False, False, 0)
        
        # Create notebook for different test categories
        notebook = Gtk.Notebook()
        notebook.set_tab_pos(Gtk.PositionType.TOP)
        
        # Theme testing tab
        self._create_theme_test_tab(notebook)
        
        # Accessibility testing tab
        self._create_accessibility_test_tab(notebook)
        
        # Keyboard shortcuts testing tab
        self._create_keyboard_test_tab(notebook)
        
        # Responsive layout testing tab
        self._create_responsive_test_tab(notebook)
        
        # Scientific widgets testing tab
        self._create_scientific_test_tab(notebook)
        
        main_box.pack_start(notebook, True, True, 0)
        
        # Status bar
        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        status_label = Gtk.Label("Status: UI Polish features loaded successfully")
        status_label.get_style_context().add_class("dim-label")
        status_box.pack_start(status_label, True, True, 0)
        
        # Theme info
        theme_manager = get_theme_manager()
        theme_info = Gtk.Label(f"Theme: {theme_manager.get_current_scheme().value}")
        status_box.pack_end(theme_info, False, False, 0)
        
        main_box.pack_end(status_box, False, False, 0)
    
    def _create_theme_test_tab(self, notebook):
        """Create theme testing tab."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        box.set_margin_left(20)
        box.set_margin_right(20)
        box.set_margin_top(20)
        box.set_margin_bottom(20)
        
        # Theme selection
        theme_frame = Gtk.Frame(label="Theme Selection")
        theme_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        theme_box.set_margin_left(10)
        theme_box.set_margin_right(10)
        theme_box.set_margin_top(10)
        theme_box.set_margin_bottom(10)
        
        for scheme in ColorScheme:
            button = Gtk.Button(label=scheme.value.replace('_', ' ').title())
            button.connect('clicked', self._on_theme_changed, scheme)
            theme_box.pack_start(button, True, True, 0)
        
        theme_frame.add(theme_box)
        box.pack_start(theme_frame, False, False, 0)
        
        # Sample components
        components_frame = Gtk.Frame(label="Sample Components")
        components_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        components_box.set_margin_left(10)
        components_box.set_margin_right(10)
        components_box.set_margin_top(10)
        components_box.set_margin_bottom(10)
        
        # Buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        normal_button = Gtk.Button(label="Normal Button")
        button_box.pack_start(normal_button, False, False, 0)
        
        primary_button = Gtk.Button(label="Primary Button")
        primary_button.get_style_context().add_class("suggested-action")
        button_box.pack_start(primary_button, False, False, 0)
        
        danger_button = Gtk.Button(label="Danger Button")
        danger_button.get_style_context().add_class("destructive-action")
        button_box.pack_start(danger_button, False, False, 0)
        
        components_box.pack_start(button_box, False, False, 0)
        
        # Entry fields
        entry_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        entry1 = Gtk.Entry()
        entry1.set_placeholder_text("Normal entry")
        entry_box.pack_start(entry1, True, True, 0)
        
        entry2 = Gtk.Entry()
        entry2.set_placeholder_text("Scientific notation")
        entry2.set_text("1.23e-4")
        entry_box.pack_start(entry2, True, True, 0)
        
        components_box.pack_start(entry_box, False, False, 0)
        
        # Progress bar
        progress = Gtk.ProgressBar()
        progress.set_fraction(0.6)
        progress.set_text("60% Complete")
        progress.set_show_text(True)
        components_box.pack_start(progress, False, False, 0)
        
        # Scientific table
        self._create_sample_scientific_table(components_box)
        
        components_frame.add(components_box)
        box.pack_start(components_frame, True, True, 0)
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.add(box)
        
        tab_label = Gtk.Label("Theme Testing")
        notebook.append_page(scrolled, tab_label)
    
    def _create_accessibility_test_tab(self, notebook):
        """Create accessibility testing tab."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        box.set_margin_left(20)
        box.set_margin_right(20)
        box.set_margin_top(20)
        box.set_margin_bottom(20)
        
        # Accessibility level selection
        level_frame = Gtk.Frame(label="Accessibility Level")
        level_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        level_box.set_margin_left(10)
        level_box.set_margin_right(10)
        level_box.set_margin_top(10)
        level_box.set_margin_bottom(10)
        
        for level in AccessibilityLevel:
            button = Gtk.Button(label=level.value.replace('_', ' ').title())
            button.connect('clicked', self._on_accessibility_changed, level)
            level_box.pack_start(button, True, True, 0)
        
        level_frame.add(level_box)
        box.pack_start(level_frame, False, False, 0)
        
        # Accessibility features demonstration
        features_frame = Gtk.Frame(label="Accessibility Features")
        features_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        features_box.set_margin_left(10)
        features_box.set_margin_right(10)
        features_box.set_margin_top(10)
        features_box.set_margin_bottom(10)
        
        # High contrast toggle
        contrast_button = Gtk.Button(label="Toggle High Contrast")
        contrast_button.connect('clicked', self._on_high_contrast_toggled)
        features_box.pack_start(contrast_button, False, False, 0)
        
        # Text scaling
        scale_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        scale_label = Gtk.Label("Text Scale:")
        scale_box.pack_start(scale_label, False, False, 0)
        
        scale_spin = Gtk.SpinButton()
        scale_spin.set_range(0.5, 3.0)
        scale_spin.set_increments(0.1, 0.5)
        scale_spin.set_value(1.0)
        scale_spin.connect('value-changed', self._on_text_scale_changed)
        scale_box.pack_start(scale_spin, False, False, 0)
        
        features_box.pack_start(scale_box, False, False, 0)
        
        # Accessible widgets with proper ARIA labels
        accessible_entry = Gtk.Entry()
        accessible_entry.set_placeholder_text("Accessible input field")
        
        # Register with accessibility manager
        if hasattr(self.ui_polish_manager, 'accessibility_manager'):
            self.ui_polish_manager.accessibility_manager.register_widget(
                'test_entry', accessible_entry,
                {
                    'name': 'Test Input Field',
                    'description': 'Test input field for accessibility demonstration',
                    'tooltip': 'Enter test data here'
                }
            )
        
        features_box.pack_start(accessible_entry, False, False, 0)
        
        features_frame.add(features_box)
        box.pack_start(features_frame, True, True, 0)
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.add(box)
        
        tab_label = Gtk.Label("Accessibility")
        notebook.append_page(scrolled, tab_label)
    
    def _create_keyboard_test_tab(self, notebook):
        """Create keyboard shortcuts testing tab."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        box.set_margin_left(20)
        box.set_margin_right(20)
        box.set_margin_top(20)
        box.set_margin_bottom(20)
        
        # Instructions
        instructions = Gtk.Label()
        instructions.set_markup("""
<b>Keyboard Shortcuts Test</b>

Try these keyboard shortcuts:
• <b>F1</b> - Show shortcuts help
• <b>Ctrl+N</b> - New project
• <b>Ctrl+O</b> - Open project
• <b>Ctrl+S</b> - Save project
• <b>Ctrl+1-6</b> - Navigate to panels
• <b>F9</b> - Run simulation
• <b>F11</b> - Toggle fullscreen
• <b>Ctrl+Tab</b> - Next tab
• <b>Ctrl+Shift+Tab</b> - Previous tab
        """)
        instructions.set_justify(Gtk.Justification.LEFT)
        box.pack_start(instructions, False, False, 0)
        
        # Shortcuts help button
        help_button = Gtk.Button(label="Show Keyboard Shortcuts Help")
        help_button.connect('clicked', self._on_show_shortcuts)
        box.pack_start(help_button, False, False, 0)
        
        # Focusable elements for testing navigation
        focus_frame = Gtk.Frame(label="Focus Navigation Test")
        focus_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        focus_box.set_margin_left(10)
        focus_box.set_margin_right(10)
        focus_box.set_margin_top(10)
        focus_box.set_margin_bottom(10)
        
        for i in range(5):
            button = Gtk.Button(label=f"Focusable Button {i+1}")
            button.set_tooltip_text(f"Use Tab/Shift+Tab to navigate. This is button {i+1}")
            focus_box.pack_start(button, False, False, 0)
        
        focus_frame.add(focus_box)
        box.pack_start(focus_frame, True, True, 0)
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.add(box)
        
        tab_label = Gtk.Label("Keyboard Shortcuts")
        notebook.append_page(scrolled, tab_label)
    
    def _create_responsive_test_tab(self, notebook):
        """Create responsive layout testing tab."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        box.set_margin_left(20)
        box.set_margin_right(20)
        box.set_margin_top(20)
        box.set_margin_bottom(20)
        
        # Current layout info
        info_frame = Gtk.Frame(label="Layout Information")
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        info_box.set_margin_left(10)
        info_box.set_margin_right(10)
        info_box.set_margin_top(10)
        info_box.set_margin_bottom(10)
        
        self.layout_info_label = Gtk.Label()
        self._update_layout_info()
        info_box.pack_start(self.layout_info_label, False, False, 0)
        
        # Update button
        update_button = Gtk.Button(label="Update Layout Info")
        update_button.connect('clicked', lambda w: self._update_layout_info())
        info_box.pack_start(update_button, False, False, 0)
        
        info_frame.add(info_box)
        box.pack_start(info_frame, False, False, 0)
        
        # Resize instructions
        resize_label = Gtk.Label()
        resize_label.set_markup("""
<b>Responsive Layout Test</b>

Try resizing the window to see responsive behavior:
• <b>Small</b> (&lt; 1024x768): Compact layout
• <b>Normal</b> (1024x768 - 1440x900): Standard layout
• <b>Large</b> (1440x900 - 1920x1080): Wide layout
• <b>X-Large</b> (&gt; 1920x1080): Split layout

The layout information above will update as you resize.
        """)
        resize_label.set_justify(Gtk.Justification.LEFT)
        box.pack_start(resize_label, False, False, 0)
        
        # Sample responsive grid
        grid_frame = Gtk.Frame(label="Responsive Grid Example")
        grid = Gtk.Grid()
        grid.set_margin_left(10)
        grid.set_margin_right(10)
        grid.set_margin_top(10)
        grid.set_margin_bottom(10)
        grid.set_row_spacing(10)
        grid.set_column_spacing(10)
        
        for i in range(3):
            for j in range(4):
                button = Gtk.Button(label=f"Item {i*4+j+1}")
                grid.attach(button, j, i, 1, 1)
        
        grid_frame.add(grid)
        box.pack_start(grid_frame, True, True, 0)
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.add(box)
        
        tab_label = Gtk.Label("Responsive Layout")
        notebook.append_page(scrolled, tab_label)
    
    def _create_scientific_test_tab(self, notebook):
        """Create scientific widgets testing tab."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        box.set_margin_left(20)
        box.set_margin_right(20)
        box.set_margin_top(20)
        box.set_margin_bottom(20)
        
        # Scientific data table
        table_frame = Gtk.Frame(label="Scientific Data Table")
        self._create_sample_scientific_table(table_frame)
        box.pack_start(table_frame, True, True, 0)
        
        # Scientific form
        form_frame = Gtk.Frame(label="Scientific Input Form")
        form_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        form_box.set_margin_left(10)
        form_box.set_margin_right(10)
        form_box.set_margin_top(10)
        form_box.set_margin_bottom(10)
        form_box.get_style_context().add_class("professional-form")
        
        # Scientific notation entries
        entries = [
            ("Silicon Dioxide (SiO₂)", "20.5", "%"),
            ("Aluminum Oxide (Al₂O₃)", "5.2", "%"),
            ("Iron Oxide (Fe₂O₃)", "3.1", "%"),
            ("Calcium Oxide (CaO)", "65.0", "%"),
            ("Water/Cement Ratio", "0.35", "ratio"),
            ("Density", "2.15e3", "kg/m³")
        ]
        
        for label_text, value, unit in entries:
            row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            
            label = Gtk.Label(label_text)
            label.set_size_request(200, -1)
            label.set_halign(Gtk.Align.START)
            row_box.pack_start(label, False, False, 0)
            
            entry = Gtk.Entry()
            entry.set_text(value)
            entry.set_size_request(100, -1)
            entry.get_style_context().add_class("scientific-value")
            row_box.pack_start(entry, False, False, 0)
            
            unit_label = Gtk.Label(unit)
            unit_label.get_style_context().add_class("unit-label")
            row_box.pack_start(unit_label, False, False, 0)
            
            form_box.pack_start(row_box, False, False, 0)
        
        form_frame.add(form_box)
        box.pack_start(form_frame, False, False, 0)
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.add(box)
        
        tab_label = Gtk.Label("Scientific Widgets")
        notebook.append_page(scrolled, tab_label)
    
    def _create_sample_scientific_table(self, container):
        """Create a sample scientific data table."""
        # Create list store
        store = Gtk.ListStore(str, float, float, float, str)
        
        # Sample data
        materials = [
            ("Cement Type I", 20.5, 5.2, 3.1, "ASTM C150"),
            ("Cement Type II", 21.2, 4.8, 3.5, "ASTM C150"),
            ("Fly Ash Class F", 55.3, 23.1, 6.2, "ASTM C618"),
            ("Silica Fume", 96.2, 0.8, 0.4, "ASTM C1240"),
        ]
        
        for material in materials:
            store.append(material)
        
        # Create tree view
        treeview = Gtk.TreeView(model=store)
        treeview.get_style_context().add_class("scientific-table")
        
        # Columns
        columns = [
            ("Material", 0, str),
            ("SiO₂ (%)", 1, float),
            ("Al₂O₃ (%)", 2, float),
            ("Fe₂O₃ (%)", 3, float),
            ("Standard", 4, str)
        ]
        
        for title, col_id, data_type in columns:
            renderer = Gtk.CellRendererText()
            if data_type == float:
                renderer.set_property("xalign", 1.0)  # Right align numbers
            
            column = Gtk.TreeViewColumn(title, renderer, text=col_id)
            column.set_sort_column_id(col_id)
            treeview.append_column(column)
        
        # Add to scrolled window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.add(treeview)
        scrolled.set_size_request(-1, 200)
        
        if hasattr(container, 'add'):
            container.add(scrolled)
        else:
            container.pack_start(scrolled, True, True, 0)
    
    def _update_layout_info(self):
        """Update layout information display."""
        if hasattr(self.ui_polish_manager, 'responsive_manager'):
            layout_info = self.ui_polish_manager.responsive_manager.get_layout_info()
            
            info_text = f"""Current Layout Information:
Screen Size: {layout_info['screen_size']}
Layout Mode: {layout_info['layout_mode']}
Dimensions: {layout_info['dimensions'][0]} x {layout_info['dimensions'][1]}
Mobile Layout: {layout_info['is_mobile']}
Wide Layout: {layout_info['is_wide']}
Font Scale: {layout_info['configuration']['font_scale']:.1f}
Icon Scale: {layout_info['configuration']['icon_scale']:.1f}
Spacing Scale: {layout_info['configuration']['spacing_scale']:.1f}"""
            
            self.layout_info_label.set_text(info_text)
    
    # Event handlers
    
    def _on_theme_changed(self, button, scheme):
        """Handle theme change."""
        self.ui_polish_manager.set_theme_scheme(scheme)
        self.logger.info(f"Theme changed to: {scheme.value}")
    
    def _on_accessibility_changed(self, button, level):
        """Handle accessibility level change."""
        self.ui_polish_manager.enhance_accessibility(level)
        self.logger.info(f"Accessibility level changed to: {level.value}")
    
    def _on_high_contrast_toggled(self, button):
        """Handle high contrast toggle."""
        if hasattr(self.ui_polish_manager, 'accessibility_manager'):
            self.ui_polish_manager.accessibility_manager.toggle_high_contrast()
            self.logger.info("High contrast toggled")
    
    def _on_text_scale_changed(self, spin_button):
        """Handle text scale change."""
        scale = spin_button.get_value()
        if hasattr(self.ui_polish_manager, 'accessibility_manager'):
            self.ui_polish_manager.accessibility_manager.set_text_scale(scale)
            self.logger.info(f"Text scale changed to: {scale}")
    
    def _on_show_shortcuts(self, button):
        """Show keyboard shortcuts dialog."""
        if hasattr(self.ui_polish_manager, 'keyboard_manager'):
            self.ui_polish_manager.keyboard_manager.show_shortcuts_dialog()


class UIPolishTestApp(Gtk.Application):
    """Test application for UI polish features."""
    
    def __init__(self):
        super().__init__(application_id="org.nist.vcctl.ui_polish_test")
        
    def do_activate(self):
        window = UIPolishTestWindow()
        window.set_application(self)
        window.show_all()


def main():
    """Main entry point for UI polish test."""
    app = UIPolishTestApp()
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
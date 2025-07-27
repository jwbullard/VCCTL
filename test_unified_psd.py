#!/usr/bin/env python3
"""
Test script for the unified PSD widget.
Demonstrates the new PSD interface that can be used across all material types.
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject

from app.widgets.unified_psd_widget import UnifiedPSDWidget


class TestPSDDialog(Gtk.Dialog):
    """Test dialog to demonstrate the unified PSD widget."""
    
    def __init__(self, parent=None):
        super().__init__(
            title="Unified PSD Widget Test",
            parent=parent,
            flags=Gtk.DialogFlags.MODAL
        )
        
        self.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK, Gtk.ResponseType.OK
        )
        
        self.set_default_size(800, 600)
        
        # Create content area
        content_area = self.get_content_area()
        content_area.set_spacing(10)
        content_area.set_margin_left(10)
        content_area.set_margin_right(10)
        content_area.set_margin_top(10)
        content_area.set_margin_bottom(10)
        
        # Title
        title_label = Gtk.Label()
        title_label.set_markup("<b>Unified PSD Widget Test</b>")
        content_area.pack_start(title_label, False, False, 0)
        
        # Material type selection
        material_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        material_label = Gtk.Label("Material Type:")
        self.material_combo = Gtk.ComboBoxText()
        self.material_combo.append("fly_ash", "Fly Ash")
        self.material_combo.append("slag", "Slag")
        self.material_combo.append("cement", "Cement")
        self.material_combo.append("limestone", "Limestone")
        self.material_combo.append("silica_fume", "Silica Fume")
        self.material_combo.set_active(0)
        self.material_combo.connect('changed', self._on_material_changed)
        
        material_box.pack_start(material_label, False, False, 0)
        material_box.pack_start(self.material_combo, False, False, 0)
        content_area.pack_start(material_box, False, False, 0)
        
        # Unified PSD Widget
        self.psd_widget = UnifiedPSDWidget('fly_ash')
        self.psd_widget.set_change_callback(self._on_psd_changed)
        content_area.pack_start(self.psd_widget, True, True, 0)
        
        # Status label
        self.status_label = Gtk.Label()
        self.status_label.set_markup("<i>Ready</i>")
        content_area.pack_start(self.status_label, False, False, 0)
        
        # Test buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        load_test_button = Gtk.Button("Load Test Data")
        load_test_button.connect('clicked', self._load_test_data)
        button_box.pack_start(load_test_button, False, False, 0)
        
        export_data_button = Gtk.Button("Show Material Data")
        export_data_button.connect('clicked', self._show_material_data)
        button_box.pack_start(export_data_button, False, False, 0)
        
        content_area.pack_start(button_box, False, False, 0)
        
        self.show_all()
    
    def _on_material_changed(self, combo):
        """Handle material type change."""
        material_type = combo.get_active_id()
        
        # Create new PSD widget for the selected material type
        content_area = self.get_content_area()
        content_area.remove(self.psd_widget)
        
        self.psd_widget = UnifiedPSDWidget(material_type)
        self.psd_widget.set_change_callback(self._on_psd_changed)
        
        # Insert before status label
        children = content_area.get_children()
        content_area.pack_start(self.psd_widget, True, True, 0)
        content_area.reorder_child(self.psd_widget, len(children) - 3)
        
        self.psd_widget.show_all()
        
        self.status_label.set_markup(f"<i>Switched to {material_type}</i>")
    
    def _on_psd_changed(self):
        """Handle PSD data changes."""
        distribution = self.psd_widget.get_discrete_distribution()
        if distribution:
            num_points = len(distribution.points)
            d50 = distribution.d50
            self.status_label.set_markup(f"<i>PSD updated: {num_points} points, D₅₀={d50:.1f}μm</i>")
        else:
            self.status_label.set_markup("<i>No PSD data</i>")
    
    def _load_test_data(self, button):
        """Load test data into the PSD widget."""
        material_type = self.material_combo.get_active_id()
        
        # Create test material data based on material type
        if material_type == 'fly_ash':
            test_data = {
                'psd_mode': 'log_normal',
                'psd_median': 5.0,
                'psd_spread': 2.0
            }
        elif material_type == 'slag':
            test_data = {
                'psd_mode': 'rosin_rammler',
                'psd_d50': 15.0,
                'psd_n': 1.4,
                'psd_dmax': 75.0
            }
        elif material_type == 'cement':
            test_data = {
                'psd_mode': 'rosin_rammler',
                'psd_d50': 20.0,
                'psd_n': 1.2,
                'psd_dmax': 100.0
            }
        else:
            test_data = {
                'psd_mode': 'log_normal',
                'psd_median': 10.0,
                'psd_spread': 2.5
            }
        
        self.psd_widget.load_from_material_data(test_data)
        self.status_label.set_markup(f"<i>Loaded test data for {material_type}</i>")
    
    def _show_material_data(self, button):
        """Show the current material data dictionary."""
        data = self.psd_widget.get_material_data_dict()
        
        # Create a simple display dialog
        dialog = Gtk.MessageDialog(
            parent=self,
            flags=Gtk.DialogFlags.MODAL,
            type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            message_format="Material Data Dictionary"
        )
        
        # Format the data nicely
        formatted_data = []
        for key, value in data.items():
            if isinstance(value, float):
                formatted_data.append(f"'{key}': {value:.3f}")
            else:
                formatted_data.append(f"'{key}': {repr(value)}")
        
        data_text = "{\n  " + ",\n  ".join(formatted_data) + "\n}"
        dialog.format_secondary_text(data_text)
        
        dialog.run()
        dialog.destroy()


class TestApp(Gtk.Application):
    """Test application for the unified PSD widget."""
    
    def __init__(self):
        super().__init__(application_id="com.vcctl.test_psd")
    
    def do_activate(self):
        """Application activation handler."""
        window = Gtk.ApplicationWindow(application=self)
        window.set_title("VCCTL PSD Widget Test")
        window.set_default_size(400, 300)
        
        # Create a simple main window with a button to open the test dialog
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        box.set_margin_left(50)
        box.set_margin_right(50)
        box.set_margin_top(50)
        box.set_margin_bottom(50)
        
        title_label = Gtk.Label()
        title_label.set_markup("<b>VCCTL Unified PSD Widget Test</b>")
        box.pack_start(title_label, False, False, 0)
        
        desc_label = Gtk.Label()
        desc_label.set_markup(
            "This test demonstrates the new unified PSD widget that provides\n"
            "consistent particle size distribution editing across all material types.\n\n"
            "<b>Features:</b>\n"
            "• Mathematical models: Rosin-Rammler, Log-Normal, Fuller-Thompson\n"
            "• Automatic conversion to discrete points\n"
            "• Editable table display\n"
            "• CSV import/export\n"
            "• Real-time validation and preview"
        )
        desc_label.set_justify(Gtk.Justification.LEFT)
        box.pack_start(desc_label, True, True, 0)
        
        test_button = Gtk.Button("Open PSD Widget Test")
        test_button.connect('clicked', self._open_test_dialog)
        box.pack_start(test_button, False, False, 0)
        
        window.add(box)
        window.show_all()
        window.present()
    
    def _open_test_dialog(self, button):
        """Open the PSD test dialog."""
        window = self.get_active_window()
        dialog = TestPSDDialog(window)
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            print("PSD dialog completed successfully")
            
            # Get final PSD data
            data = dialog.psd_widget.get_material_data_dict()
            distribution = dialog.psd_widget.get_discrete_distribution()
            
            print("Final PSD data:")
            for key, value in data.items():
                print(f"  {key}: {value}")
            
            if distribution:
                print(f"Discrete distribution: {len(distribution.points)} points")
                print(f"D50: {distribution.d50:.2f} μm")
        
        dialog.destroy()


if __name__ == "__main__":
    import locale
    try:
        locale.setlocale(locale.LC_ALL, '')
    except locale.Error:
        pass
    
    app = TestApp()
    exit_status = app.run(sys.argv)
    sys.exit(exit_status)
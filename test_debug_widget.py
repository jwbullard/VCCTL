#!/usr/bin/env python3
"""
Test Widget with Debug Output

This will show exactly what parameters are being used and 
what results are generated.
"""

import sys
import os
import gi

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject

from app.widgets.unified_psd_widget import UnifiedPSDWidget

class DebugTestWindow(Gtk.Window):
    """Simple test window with debug output."""
    
    def __init__(self):
        super().__init__(title="Debug D_max Test - Check Terminal Output")
        self.set_default_size(600, 400)
        
        # Create main container
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        main_box.set_margin_left(20)
        main_box.set_margin_right(20)
        main_box.set_margin_top(20)
        main_box.set_margin_bottom(20)
        
        # Instructions
        instructions = Gtk.Label()
        instructions.set_markup(
            "<b>Debug D_max Test</b>\n\n"
            "1. Set D_max to 60 below\n"
            "2. Press 'Generate Table' button\n"
            "3. Check terminal output for debug info\n"
            "4. Look at table - should end at 60 μm"
        )
        instructions.set_justify(Gtk.Justification.LEFT)
        main_box.pack_start(instructions, False, False, 0)
        
        # Create PSD widget (with debugging enabled)
        self.psd_widget = UnifiedPSDWidget('cement')
        main_box.pack_start(self.psd_widget, True, True, 0)
        
        # Set up scenario: Rosin-Rammler with D_max = 60
        self.psd_widget.mode_combo.set_active_id("rosin_rammler")
        self.psd_widget.rosin_rammler_widgets['d50'].set_value(15.0)
        self.psd_widget.rosin_rammler_widgets['n'].set_value(1.4)
        self.psd_widget.rosin_rammler_widgets['dmax'].set_value(60.0)
        
        # Generate initial table
        print("🎯 Initial generation with D_max=60:")
        self.psd_widget._on_generate_clicked(None)
        
        self.add(main_box)
        self.show_all()

class DebugTestApp(Gtk.Application):
    """Debug test application."""
    
    def __init__(self):
        super().__init__(application_id="com.vcctl.debug_test")
    
    def do_activate(self):
        window = DebugTestWindow()
        self.add_window(window)
        window.present()

if __name__ == "__main__":
    print("🔍 Starting Debug Test - Watch for debug output below:")
    print("=" * 50)
    
    app = DebugTestApp()
    exit_status = app.run(sys.argv)
    sys.exit(exit_status)
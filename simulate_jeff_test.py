#!/usr/bin/env python3
"""
Simulate Jeff's Test Case

This simulates the exact scenario Jeff described:
1. Choose Rosin-Rammler distribution
2. Set D_max to 60
3. Press "Generate Table" button
4. Table should show max diameter of 60, not 75
"""

import sys
import os
import gi

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject

from app.widgets.unified_psd_widget import UnifiedPSDWidget

class JeffTestWindow(Gtk.Window):
    """Test window simulating Jeff's exact scenario."""
    
    def __init__(self):
        super().__init__(title="Jeff's Test: Rosin-Rammler D_max=60")
        self.set_default_size(800, 600)
        
        # Create main container
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        main_box.set_margin_left(20)
        main_box.set_margin_right(20)
        main_box.set_margin_top(20)
        main_box.set_margin_bottom(20)
        
        # Instructions
        instructions = Gtk.Label()
        instructions.set_markup(
            "<b>Jeff's Test Scenario:</b>\n"
            "1. ✅ Rosin-Rammler is already selected\n"
            "2. ✅ D_max is set to 60 μm\n"
            "3. ✅ Press 'Generate Table' button\n"
            "4. ✅ Check: Table should show max diameter = 60 μm, not 75 μm"
        )
        instructions.set_justify(Gtk.Justification.LEFT)
        main_box.pack_start(instructions, False, False, 0)
        
        # Create PSD widget
        self.psd_widget = UnifiedPSDWidget('cement')  # Use cement defaults for Rosin-Rammler
        self.psd_widget.set_change_callback(self._on_psd_changed)
        
        # Set up Jeff's test scenario BEFORE adding to window
        self._setup_jeff_scenario()
        
        main_box.pack_start(self.psd_widget, True, True, 0)
        
        # Status label
        self.status_label = Gtk.Label()
        main_box.pack_start(self.status_label, False, False, 0)
        
        # Test button
        test_button = Gtk.Button("🔍 Run Jeff's Test")
        test_button.connect('clicked', self._run_jeff_test)
        main_box.pack_start(test_button, False, False, 0)
        
        self.add(main_box)
        self.show_all()
        
        # Run the test automatically
        GObject.timeout_add(1000, self._run_jeff_test, None)
    
    def _setup_jeff_scenario(self):
        """Set up the exact scenario Jeff described."""
        # 1. Choose Rosin-Rammler distribution (already default for cement)
        self.psd_widget.mode_combo.set_active_id("rosin_rammler")
        
        # 2. Set D_max to 60
        self.psd_widget.rosin_rammler_widgets['dmax'].set_value(60.0)
        
        # Set other reasonable values
        self.psd_widget.rosin_rammler_widgets['d50'].set_value(15.0)
        self.psd_widget.rosin_rammler_widgets['n'].set_value(1.4)
    
    def _run_jeff_test(self, button):
        """Run Jeff's test: press Generate Table and check results."""
        print("\n🧪 RUNNING JEFF'S TEST")
        print("=" * 40)
        
        # 3. Press "Generate Table" button (simulate button click)
        print("1. Pressing 'Generate Table' button...")
        self.psd_widget._on_generate_clicked(None)
        
        # 4. Check results
        distribution = self.psd_widget.get_discrete_distribution()
        
        if distribution:
            max_diameter = max(distribution.diameters)
            num_bins = len(distribution.points)
            
            print(f"2. Generated {num_bins} bins")
            print(f"3. Maximum diameter in table: {max_diameter} μm")
            print(f"4. Expected maximum: 60 μm")
            
            if max_diameter == 60:
                result = "✅ PASS: Table correctly shows max diameter = 60 μm"
                color = "green"
            else:
                result = f"❌ FAIL: Table shows max diameter = {max_diameter} μm (should be 60)"
                color = "red"
            
            print(f"5. {result}")
            
            # Show in UI
            self.status_label.set_markup(f"<span color='{color}'><b>{result}</b></span>")
            
            # Show first few and last few bins
            print("\nFirst 5 bins:")
            for diameter, mass_fraction in distribution.points[:5]:
                percentage = mass_fraction * 100
                print(f"   {diameter:3.0f} μm: {percentage:5.2f}%")
            
            print("...")
            print("Last 5 bins:")
            for diameter, mass_fraction in distribution.points[-5:]:
                percentage = mass_fraction * 100
                print(f"   {diameter:3.0f} μm: {percentage:5.2f}%")
                
        else:
            result = "❌ ERROR: No distribution generated"
            print(result)
            self.status_label.set_markup(f"<span color='red'><b>{result}</b></span>")
        
        return False  # Don't repeat timeout
    
    def _on_psd_changed(self):
        """Handle PSD changes."""
        distribution = self.psd_widget.get_discrete_distribution()
        if distribution:
            max_diameter = max(distribution.diameters)
            num_bins = len(distribution.points)
            self.status_label.set_markup(
                f"<i>PSD Updated: {num_bins} bins, max diameter = {max_diameter} μm</i>"
            )

class JeffTestApp(Gtk.Application):
    """Application for Jeff's test."""
    
    def __init__(self):
        super().__init__(application_id="com.vcctl.jeff_test")
    
    def do_activate(self):
        window = JeffTestWindow()
        self.add_window(window)
        window.present()

if __name__ == "__main__":
    app = JeffTestApp()
    exit_status = app.run(sys.argv)
    sys.exit(exit_status)
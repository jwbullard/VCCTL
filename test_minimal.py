#!/usr/bin/env python3

import sys
import os

# Add src to path
sys.path.insert(0, 'src')

# Test GTK import
try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk, GLib
    print("✅ GTK imports successful")
except Exception as e:
    print(f"❌ GTK import failed: {e}")
    sys.exit(1)

# Test basic window
try:
    class MinimalWindow(Gtk.Window):
        def __init__(self):
            super().__init__(title="Minimal Test")
            self.set_default_size(400, 300)
            
            label = Gtk.Label(label="Test Window")
            self.add(label)
            
            self.connect('delete-event', Gtk.main_quit)
            self.show_all()
    
    print("✅ Window class created")
    
    # Create window but don't run main loop yet
    win = MinimalWindow()
    print("✅ Window instantiated and shown")
    
    # Quick test - don't run full main loop
    print("✅ Test completed successfully - GTK is working!")
    
except Exception as e:
    print(f"❌ Window creation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
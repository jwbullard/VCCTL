#!/usr/bin/env python3
"""
Minimal GTK test to isolate fundamental issues
"""

import gi
import sys
import time
import logging

print("Starting minimal GTK test...")
print(f"Python version: {sys.version}")

try:
    gi.require_version('Gtk', '3.0')
    print("GTK 3.0 requirement successful")
except Exception as e:
    print(f"ERROR: GTK requirement failed: {e}")
    sys.exit(1)

try:
    from gi.repository import Gtk, Gio, GLib
    print("GTK imports successful")
except Exception as e:
    print(f"ERROR: GTK import failed: {e}")
    sys.exit(1)

# Setup basic logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('MinimalTest')

class MinimalApp(Gtk.Application):
    def __init__(self):
        print("Creating minimal application...")
        super().__init__(
            application_id='test.minimal.gtk',
            flags=Gio.ApplicationFlags.FLAGS_NONE
        )
        self.window = None
        self.connect('activate', self.on_activate)
        print("Minimal application created")

    def on_activate(self, app):
        print("Application activated - creating window...")
        if self.window is None:
            self.window = Gtk.ApplicationWindow(application=self)
            self.window.set_title("Minimal Test")
            self.window.set_default_size(400, 300)
            
            # Add simple content
            label = Gtk.Label(label="Minimal GTK Test Window")
            self.window.add(label)
            
            print("Window created and configured")
        
        print("Presenting window...")
        self.window.show_all()
        self.window.present()
        print("Window should now be visible")

def main():
    print("Creating application instance...")
    app = MinimalApp()
    
    print("Running application...")
    try:
        exit_code = app.run(sys.argv)
        print(f"Application exited with code: {exit_code}")
        return exit_code
    except Exception as e:
        print(f"ERROR: Application run failed: {e}")
        return 1

if __name__ == "__main__":
    print("=== MINIMAL GTK TEST START ===")
    exit_code = main()
    print(f"=== MINIMAL GTK TEST END (exit code: {exit_code}) ===")
    sys.exit(exit_code)
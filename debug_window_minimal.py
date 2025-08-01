#!/usr/bin/env python3
"""
Minimal window test to isolate infinite surface size issue
"""

import gi
import sys
import logging

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio, GObject

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('MinimalWindowTest')

class MinimalMainWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        
        self.set_title("Minimal VCCTL Test Window")
        self.set_default_size(1200, 800)
        self.set_position(Gtk.WindowPosition.CENTER)
        
        # Create minimal UI structure similar to main window
        main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(main_vbox)
        
        # Create header bar (similar to main window)
        header_bar = Gtk.HeaderBar()
        header_bar.set_show_close_button(True)
        header_bar.set_title("Minimal Test")
        header_bar.set_subtitle("Testing infinite surface size issue")
        self.set_titlebar(header_bar)
        
        # Create notebook (similar to main window)
        notebook = Gtk.Notebook()
        notebook.set_show_tabs(True)
        notebook.set_show_border(True)
        notebook.set_scrollable(True)
        notebook.set_tab_pos(Gtk.PositionType.TOP)
        
        # Add minimal tabs
        for i in range(3):
            page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            page.set_margin_top(20)
            page.set_margin_bottom(20)
            page.set_margin_left(20)
            page.set_margin_right(20)
            
            label = Gtk.Label(f"Test Tab {i+1}")
            label.set_markup(f'<span size="large" weight="bold">Test Tab {i+1}</span>')
            page.pack_start(label, False, False, 0)
            
            # Add some content
            content_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            content_box.pack_start(Gtk.Label("Sample content"), False, False, 0)
            content_box.pack_start(Gtk.Button(label="Test Button"), False, False, 0)
            page.pack_start(content_box, False, False, 0)
            
            notebook.append_page(page, Gtk.Label(f"Tab {i+1}"))
        
        main_vbox.pack_start(notebook, True, True, 0)
        
        # Create status bar
        status_bar = Gtk.Statusbar()
        status_context_id = status_bar.get_context_id("main")
        status_bar.push(status_context_id, "Minimal test ready")
        main_vbox.pack_start(status_bar, False, False, 0)
        
        logger.info("Minimal main window created")

class MinimalApp(Gtk.Application):
    def __init__(self):
        super().__init__(
            application_id='test.minimal.vcctl',
            flags=Gio.ApplicationFlags.FLAGS_NONE
        )
        self.window = None
        self.connect('activate', self.on_activate)
        logger.info("Minimal application created")

    def on_activate(self, app):
        logger.info("Application activated - creating window...")
        if self.window is None:
            self.window = MinimalMainWindow(self)
        
        logger.info("Showing window...")
        self.window.show_all()
        logger.info("Window shown - checking for infinite surface size warnings...")

def main():
    logger.info("=== MINIMAL VCCTL WINDOW TEST START ===")
    app = MinimalApp()
    
    try:
        exit_code = app.run(sys.argv)
        logger.info(f"Application exited with code: {exit_code}")
        return exit_code
    except Exception as e:
        logger.error(f"Application run failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    logger.info(f"=== MINIMAL VCCTL WINDOW TEST END (exit code: {exit_code}) ===")
    sys.exit(exit_code)
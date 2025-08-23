#!/usr/bin/env python3
"""
Demo application to showcase custom SVG icons in VCCTL UI.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

from src.app.utils.icon_utils import create_button_with_icon, set_tool_button_custom_icon, ICON_MAPPING


class IconDemoWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="VCCTL Custom Icons Demo")
        self.set_default_size(800, 600)
        self.set_position(Gtk.WindowPosition.CENTER)
        
        # Main container
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        main_box.set_margin_left(20)
        main_box.set_margin_right(20)
        main_box.set_margin_top(20)
        main_box.set_margin_bottom(20)
        
        # Title
        title = Gtk.Label()
        title.set_markup('<span size="x-large"><b>VCCTL Custom SVG Icons Demo</b></span>')
        main_box.pack_start(title, False, False, 0)
        
        # Toolbar demo
        toolbar_frame = Gtk.Frame(label="Toolbar Icons (24px)")
        toolbar = Gtk.Toolbar()
        toolbar.set_style(Gtk.ToolbarStyle.BOTH_HORIZ)
        
        # Add toolbar buttons
        icons_for_toolbar = [
            ("media-playback-start", "Start"),
            ("media-playback-pause", "Pause"), 
            ("media-playback-stop", "Stop"),
            ("view-refresh", "Refresh"),
            ("edit-delete", "Delete"),
            ("preferences-system", "Settings")
        ]
        
        for icon_name, label in icons_for_toolbar:
            button = Gtk.ToolButton()
            button.set_icon_name(icon_name)
            button.set_label(label)
            set_tool_button_custom_icon(button, icon_name, 24)
            toolbar.insert(button, -1)
            
        toolbar_frame.add(toolbar)
        main_box.pack_start(toolbar_frame, False, False, 0)
        
        # Regular buttons demo
        buttons_frame = Gtk.Frame(label="Regular Buttons (16px)")
        buttons_grid = Gtk.Grid()
        buttons_grid.set_row_spacing(10)
        buttons_grid.set_column_spacing(10)
        buttons_grid.set_margin_left(10)
        buttons_grid.set_margin_right(10)
        buttons_grid.set_margin_top(10)
        buttons_grid.set_margin_bottom(10)
        
        # Add regular buttons in grid
        button_icons = [
            ("document-save", "Save"),
            ("document-open", "Open"),
            ("document-export", "Export"),
            ("edit-clear", "Clear"),
            ("applications-science", "Analyze"),
            ("dialog-information", "Validate"),
            ("48-cube", "3D View"),
            ("user-bookmarks", "Favorite")
        ]
        
        row, col = 0, 0
        for icon_name, label in button_icons:
            button = create_button_with_icon(label, icon_name, 16)
            buttons_grid.attach(button, col, row, 1, 1)
            
            col += 1
            if col >= 4:
                col = 0
                row += 1
        
        buttons_frame.add(buttons_grid)
        main_box.pack_start(buttons_frame, False, False, 0)
        
        # Icon mapping info
        info_frame = Gtk.Frame(label="Available Icon Mappings")
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(200)
        
        liststore = Gtk.ListStore(str, str)
        for gtk_name, svg_file in ICON_MAPPING.items():
            liststore.append([gtk_name, svg_file])
        
        treeview = Gtk.TreeView(model=liststore)
        
        # Add columns
        renderer_text = Gtk.CellRendererText()
        column_gtk = Gtk.TreeViewColumn("GTK Icon Name", renderer_text, text=0)
        column_svg = Gtk.TreeViewColumn("SVG File", renderer_text, text=1)
        treeview.append_column(column_gtk)
        treeview.append_column(column_svg)
        
        scrolled.add(treeview)
        info_frame.add(scrolled)
        main_box.pack_start(info_frame, True, True, 0)
        
        # Status
        status = Gtk.Label()
        status.set_markup(f'<span color="green">✅ Successfully loaded {len(ICON_MAPPING)} custom icon mappings</span>')
        main_box.pack_start(status, False, False, 0)
        
        self.add(main_box)


def main():
    app = Gtk.Application()
    app.connect('activate', lambda app: IconDemoWindow().show_all())
    app.run()


if __name__ == '__main__':
    main()
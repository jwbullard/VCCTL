#!/usr/bin/env python3
"""
Carbon Icon Browser for VCCTL

A comprehensive browser for exploring and selecting IBM Carbon Design System icons.
Provides search, categorization, and preview functionality.
"""

import gi
import logging
import threading
from typing import Optional, List, Callable
from pathlib import Path

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, GLib, Pango

from app.utils.carbon_icon_manager import get_carbon_icon_manager


class CarbonIconBrowser(Gtk.Dialog):
    """Browser dialog for Carbon Design System icons."""
    
    def __init__(self, parent: Gtk.Window = None, title: str = "Carbon Icon Browser"):
        """Initialize the icon browser."""
        super().__init__(
            title=title,
            parent=parent,
            flags=Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT
        )
        
        self.logger = logging.getLogger('VCCTL.CarbonIconBrowser')
        self.carbon_manager = get_carbon_icon_manager()
        
        # Dialog state
        self.selected_icon = None
        self.current_category = "All"
        self.current_search = ""
        self.icon_size = 32
        
        # UI components
        self.search_entry = None
        self.category_combo = None
        self.size_combo = None
        self.icon_grid = None
        self.scrolled_window = None
        self.info_label = None
        self.selected_info_label = None
        self.icon_count_label = None
        
        # Setup dialog
        self.set_default_size(900, 700)
        self.set_resizable(True)
        
        # Add buttons
        self.add_button("Cancel", Gtk.ResponseType.CANCEL)
        self.add_button("Select Icon", Gtk.ResponseType.OK)
        
        # Make OK button insensitive initially
        ok_button = self.get_widget_for_response(Gtk.ResponseType.OK)
        ok_button.set_sensitive(False)
        
        # Setup UI
        self._setup_ui()
        
        # Load initial data
        self._load_icons()
        
        self.logger.info("Carbon Icon Browser initialized")
    
    def _setup_ui(self) -> None:
        """Setup the browser UI."""
        content_area = self.get_content_area()
        content_area.set_spacing(10)
        content_area.set_margin_top(10)
        content_area.set_margin_bottom(10)
        content_area.set_margin_left(10)
        content_area.set_margin_right(10)
        
        # Create header with search and filters
        self._create_header(content_area)
        
        # Create icon grid area
        self._create_icon_grid_area(content_area)
        
        # Create status bar
        self._create_status_bar(content_area)
    
    def _create_header(self, parent: Gtk.Box) -> None:
        """Create the header with search and filter controls."""
        header_frame = Gtk.Frame(label="Search and Filters")
        header_frame.set_label_align(0.02, 0.5)
        
        header_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        header_box.set_margin_top(10)
        header_box.set_margin_bottom(10)
        header_box.set_margin_left(10)
        header_box.set_margin_right(10)
        
        # Search row
        search_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        search_label = Gtk.Label("Search:")
        search_label.set_size_request(80, -1)
        search_box.pack_start(search_label, False, False, 0)
        
        self.search_entry = Gtk.Entry()
        self.search_entry.set_placeholder_text("Type to search icons...")
        self.search_entry.connect("changed", self._on_search_changed)
        search_box.pack_start(self.search_entry, True, True, 0)
        
        clear_button = Gtk.Button("Clear")
        clear_button.connect("clicked", self._on_clear_search)
        search_box.pack_start(clear_button, False, False, 0)
        
        header_box.pack_start(search_box, False, False, 0)
        
        # Filter row
        filter_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        # Category filter
        category_label = Gtk.Label("Category:")
        category_label.set_size_request(80, -1)
        filter_box.pack_start(category_label, False, False, 0)
        
        self.category_combo = Gtk.ComboBoxText()
        self.category_combo.append("All", "All Categories")
        for category in self.carbon_manager.get_categories():
            self.category_combo.append(category, category)
        self.category_combo.set_active_id("All")
        self.category_combo.connect("changed", self._on_category_changed)
        filter_box.pack_start(self.category_combo, True, True, 0)
        
        # Size selector
        size_label = Gtk.Label("Size:")
        filter_box.pack_start(size_label, False, False, 0)
        
        self.size_combo = Gtk.ComboBoxText()
        sizes = ["16", "24", "32", "48"]
        for size in sizes:
            self.size_combo.append(size, f"{size}px")
        self.size_combo.set_active_id("32")
        self.size_combo.connect("changed", self._on_size_changed)
        filter_box.pack_start(self.size_combo, False, False, 0)
        
        header_box.pack_start(filter_box, False, False, 0)
        
        header_frame.add(header_box)
        parent.pack_start(header_frame, False, False, 0)
    
    def _create_icon_grid_area(self, parent: Gtk.Box) -> None:
        """Create the scrollable icon grid area."""
        # Create scrolled window
        self.scrolled_window = Gtk.ScrolledWindow()
        self.scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.scrolled_window.set_min_content_height(400)
        
        # Create icon grid (FlowBox for responsive layout)
        self.icon_grid = Gtk.FlowBox()
        self.icon_grid.set_valign(Gtk.Align.START)
        self.icon_grid.set_max_children_per_line(10)
        self.icon_grid.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.icon_grid.connect("child-activated", self._on_icon_selected)
        
        self.scrolled_window.add(self.icon_grid)
        parent.pack_start(self.scrolled_window, True, True, 0)
    
    def _create_status_bar(self, parent: Gtk.Box) -> None:
        """Create the status bar with icon info."""
        status_frame = Gtk.Frame(label="Icon Information")
        status_frame.set_label_align(0.02, 0.5)
        
        status_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        status_box.set_margin_top(10)
        status_box.set_margin_bottom(10)
        status_box.set_margin_left(10)
        status_box.set_margin_right(10)
        
        # Icon count
        self.icon_count_label = Gtk.Label()
        self.icon_count_label.set_halign(Gtk.Align.START)
        status_box.pack_start(self.icon_count_label, False, False, 0)
        
        # Selected icon info
        self.selected_info_label = Gtk.Label("No icon selected")
        self.selected_info_label.set_halign(Gtk.Align.START)
        self.selected_info_label.set_line_wrap(True)
        status_box.pack_start(self.selected_info_label, False, False, 0)
        
        status_frame.add(status_box)
        parent.pack_start(status_frame, False, False, 0)
    
    def _load_icons(self) -> None:
        """Load and display icons based on current filters."""
        # Clear existing icons
        for child in self.icon_grid.get_children():
            self.icon_grid.remove(child)
        
        # Get filtered icon list
        if self.current_search:
            icons = self.carbon_manager.search_icons(self.current_search)
        elif self.current_category != "All":
            icons = self.carbon_manager.get_available_icons(self.current_category)
        else:
            icons = self.carbon_manager.get_available_icons()
        
        # Update count
        self.icon_count_label.set_text(f"Showing {len(icons)} icons")
        
        # Add icons to grid (limit to first 200 for performance)
        display_icons = icons[:200]
        if len(icons) > 200:
            self.icon_count_label.set_text(f"Showing first 200 of {len(icons)} icons")
        
        for icon_name in display_icons:
            self._add_icon_to_grid(icon_name)
        
        self.icon_grid.show_all()
        
        # Scroll to top
        vadj = self.scrolled_window.get_vadjustment()
        vadj.set_value(0)
    
    def _add_icon_to_grid(self, icon_name: str) -> None:
        """Add a single icon to the grid."""
        # Create container
        icon_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        icon_box.set_margin_top(5)
        icon_box.set_margin_bottom(5)
        icon_box.set_margin_left(5)
        icon_box.set_margin_right(5)
        
        # Create icon image
        icon_image = self.carbon_manager.create_icon_image(icon_name, self.icon_size)
        if icon_image:
            icon_image.set_halign(Gtk.Align.CENTER)
            icon_box.pack_start(icon_image, False, False, 0)
        else:
            # Fallback for missing icons
            placeholder = Gtk.Label("?")
            placeholder.set_size_request(self.icon_size, self.icon_size)
            placeholder.set_halign(Gtk.Align.CENTER)
            icon_box.pack_start(placeholder, False, False, 0)
        
        # Create icon name label
        name_label = Gtk.Label(icon_name)
        name_label.set_max_width_chars(12)
        name_label.set_ellipsize(Pango.EllipsizeMode.END)
        name_label.set_halign(Gtk.Align.CENTER)
        name_label.set_size_request(self.icon_size + 20, -1)
        name_label.set_margin_top(2)
        icon_box.pack_start(name_label, False, False, 0)
        
        # Store icon name as data
        icon_box.icon_name = icon_name
        
        # Add to flow box
        self.icon_grid.add(icon_box)
    
    def _on_search_changed(self, entry: Gtk.Entry) -> None:
        """Handle search text changes."""
        self.current_search = entry.get_text().strip()
        self._load_icons()
    
    def _on_clear_search(self, button: Gtk.Button) -> None:
        """Clear the search field."""
        self.search_entry.set_text("")
    
    def _on_category_changed(self, combo: Gtk.ComboBoxText) -> None:
        """Handle category selection changes."""
        self.current_category = combo.get_active_id() or "All"
        self._load_icons()
    
    def _on_size_changed(self, combo: Gtk.ComboBoxText) -> None:
        """Handle icon size changes."""
        size_str = combo.get_active_id()
        if size_str:
            self.icon_size = int(size_str)
            self._load_icons()
    
    def _on_icon_selected(self, flowbox: Gtk.FlowBox, child: Gtk.FlowBoxChild) -> None:
        """Handle icon selection."""
        if child and hasattr(child.get_child(), 'icon_name'):
            icon_name = child.get_child().icon_name
            self.selected_icon = icon_name
            
            # Update selected icon info
            icon_info = self.carbon_manager.get_icon_info(icon_name)
            info_text = f"Selected: {icon_name}\n"
            info_text += f"Category: {icon_info.get('category', 'Unknown')}\n"
            info_text += f"Description: {icon_info.get('description', 'No description')}"
            
            if icon_info.get('tags'):
                info_text += f"\nTags: {', '.join(icon_info['tags'][:5])}"  # Show first 5 tags
            
            self.selected_info_label.set_text(info_text)
            
            # Enable OK button
            ok_button = self.get_widget_for_response(Gtk.ResponseType.OK)
            ok_button.set_sensitive(True)
            
            self.logger.info(f"Icon selected: {icon_name}")
    
    def get_selected_icon(self) -> Optional[str]:
        """Get the currently selected icon name."""
        return self.selected_icon
    
    @staticmethod
    def show_browser(parent: Gtk.Window = None, title: str = "Select Carbon Icon") -> Optional[str]:
        """Show the icon browser and return selected icon name."""
        browser = CarbonIconBrowser(parent, title)
        browser.show_all()
        
        response = browser.run()
        selected_icon = None
        
        if response == Gtk.ResponseType.OK:
            selected_icon = browser.get_selected_icon()
        
        browser.destroy()
        return selected_icon


class CarbonIconDemo(Gtk.Window):
    """Demo window for testing Carbon icons."""
    
    def __init__(self):
        """Initialize the demo window."""
        super().__init__(title="Carbon Icons Demo")
        
        self.set_default_size(600, 400)
        self.set_position(Gtk.WindowPosition.CENTER)
        
        # Main container
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        main_box.set_margin_top(20)
        main_box.set_margin_bottom(20)
        main_box.set_margin_left(20)
        main_box.set_margin_right(20)
        
        # Title
        title_label = Gtk.Label()
        title_label.set_markup('<span size="x-large" weight="bold">Carbon Icons Demo</span>')
        main_box.pack_start(title_label, False, False, 0)
        
        # Demo icons section
        demo_frame = Gtk.Frame(label="Sample Icons")
        demo_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        demo_box.set_margin_top(10)
        demo_box.set_margin_bottom(10)
        demo_box.set_margin_left(10)
        demo_box.set_margin_right(10)
        
        # Show some common icons
        manager = get_carbon_icon_manager()
        sample_icons = ['add', 'save', 'folder', 'settings', 'help', 'play', 'pause']
        
        for icon_name in sample_icons:
            icon_image = manager.create_icon_image(icon_name, 32)
            if icon_image:
                demo_box.pack_start(icon_image, False, False, 0)
        
        demo_frame.add(demo_box)
        main_box.pack_start(demo_frame, False, False, 0)
        
        # Browser button
        browser_button = Gtk.Button("Open Icon Browser")
        browser_button.connect("clicked", self._on_open_browser)
        main_box.pack_start(browser_button, False, False, 0)
        
        # Selected icon display
        self.selected_frame = Gtk.Frame(label="Selected Icon")
        self.selected_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.selected_box.set_margin_top(10)
        self.selected_box.set_margin_bottom(10)
        self.selected_box.set_margin_left(10)
        self.selected_box.set_margin_right(10)
        
        self.selected_label = Gtk.Label("No icon selected")
        self.selected_box.pack_start(self.selected_label, False, False, 0)
        
        self.selected_frame.add(self.selected_box)
        main_box.pack_start(self.selected_frame, True, True, 0)
        
        self.add(main_box)
    
    def _on_open_browser(self, button: Gtk.Button) -> None:
        """Open the icon browser."""
        selected_icon = CarbonIconBrowser.show_browser(self, "Demo: Select Carbon Icon")
        
        if selected_icon:
            # Clear previous content
            for child in self.selected_box.get_children():
                self.selected_box.remove(child)
            
            # Show selected icon
            manager = get_carbon_icon_manager()
            icon_image = manager.create_icon_image(selected_icon, 48)
            if icon_image:
                self.selected_box.pack_start(icon_image, False, False, 0)
            
            self.selected_label = Gtk.Label(f"Selected: {selected_icon}")
            self.selected_box.pack_start(self.selected_label, False, False, 0)
            
            self.selected_box.show_all()


def run_carbon_icon_demo():
    """Run the Carbon icon demo."""
    demo = CarbonIconDemo()
    demo.connect("destroy", Gtk.main_quit)
    demo.show_all()
    Gtk.main()


if __name__ == "__main__":
    run_carbon_icon_demo()
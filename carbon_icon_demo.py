#!/usr/bin/env python3
"""
Carbon Icon Integration Demo for VCCTL

Demonstrates the new Carbon Design System icon integration with:
- Icon browsing and selection
- Icon mapping and fallback testing
- Integration with existing VCCTL icon utilities
- Performance and visual comparison
"""

import sys
import os
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject

from app.utils.carbon_icon_manager import get_carbon_icon_manager
from app.utils.icon_utils import (
    create_button_with_icon, create_carbon_button, create_carbon_image,
    suggest_carbon_icon, browse_carbon_icons, load_icon_with_fallback
)


class CarbonIconDemo(Gtk.Window):
    """Comprehensive demo of Carbon icon integration."""
    
    def __init__(self):
        super().__init__(title="VCCTL Carbon Icons Integration Demo")
        
        self.set_default_size(1000, 700)
        self.set_position(Gtk.WindowPosition.CENTER)
        
        self.carbon_manager = get_carbon_icon_manager()
        
        # Setup UI
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the demo UI."""
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        main_box.set_margin_top(10)
        main_box.set_margin_bottom(10)
        main_box.set_margin_left(10)
        main_box.set_margin_right(10)
        
        # Title
        title_label = Gtk.Label()
        title_label.set_markup('<span size="xx-large" weight="bold">VCCTL Carbon Icons Demo</span>')
        main_box.pack_start(title_label, False, False, 0)
        
        # Stats
        stats_label = Gtk.Label()
        icon_count = len(self.carbon_manager.get_available_icons())
        category_count = len(self.carbon_manager.get_categories())
        stats_label.set_markup(f'<span size="large">{icon_count:,} icons in {category_count} categories</span>')
        main_box.pack_start(stats_label, False, False, 0)
        
        # Create notebook for different demo sections
        notebook = Gtk.Notebook()
        
        # Tab 1: Icon Browser
        self._create_browser_tab(notebook)
        
        # Tab 2: VCCTL Icon Mapping
        self._create_mapping_tab(notebook)
        
        # Tab 3: Performance Demo
        self._create_performance_tab(notebook)
        
        # Tab 4: Integration Examples
        self._create_integration_tab(notebook)
        
        main_box.pack_start(notebook, True, True, 0)
        
        self.add(main_box)
    
    def _create_browser_tab(self, notebook: Gtk.Notebook):
        """Create the icon browser demo tab."""
        page_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        page_box.set_margin_top(15)
        page_box.set_margin_bottom(15)
        page_box.set_margin_left(15)
        page_box.set_margin_right(15)
        
        # Description
        desc_label = Gtk.Label()
        desc_label.set_markup('<b>Browse and select from 2000+ Carbon Design System icons</b>')
        desc_label.set_halign(Gtk.Align.START)
        page_box.pack_start(desc_label, False, False, 0)
        
        # Browser button
        browser_button = Gtk.Button("Open Carbon Icon Browser")
        browser_button.connect("clicked", self._on_open_browser)
        browser_button.set_size_request(200, 40)
        page_box.pack_start(browser_button, False, False, 0)
        
        # Selected icon display
        self.selected_frame = Gtk.Frame(label="Selected Icon")
        selected_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        selected_box.set_margin_top(10)
        selected_box.set_margin_bottom(10)
        selected_box.set_margin_left(10)
        selected_box.set_margin_right(10)
        
        self.selected_icon_image = Gtk.Label("No icon selected")
        self.selected_icon_info = Gtk.Label("")
        
        selected_box.pack_start(self.selected_icon_image, False, False, 0)
        selected_box.pack_start(self.selected_icon_info, True, True, 0)
        
        self.selected_frame.add(selected_box)
        page_box.pack_start(self.selected_frame, False, False, 0)
        
        # Sample categories
        categories_frame = Gtk.Frame(label="Sample Icons by Category")
        categories_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        categories_box.set_margin_top(10)
        categories_box.set_margin_bottom(10)
        categories_box.set_margin_left(10)
        categories_box.set_margin_right(10)
        
        # Show some sample icons from different categories
        sample_categories = {
            'Actions': ['add', 'save', 'delete', 'edit', 'copy'],
            'Navigation': ['arrow--left', 'arrow--right', 'home', 'refresh'],
            'Files': ['folder', 'document', 'export', 'import'],
            'Media': ['play', 'pause', 'stop', 'volume--up']
        }
        
        for category, icons in sample_categories.items():
            cat_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
            
            cat_label = Gtk.Label(f"{category}:")
            cat_label.set_size_request(80, -1)
            cat_label.set_halign(Gtk.Align.START)
            cat_box.pack_start(cat_label, False, False, 0)
            
            for icon_name in icons:
                icon_image = create_carbon_image(icon_name, 24)
                if icon_image:
                    cat_box.pack_start(icon_image, False, False, 0)
            
            categories_box.pack_start(cat_box, False, False, 0)
        
        categories_frame.add(categories_box)
        page_box.pack_start(categories_frame, True, True, 0)
        
        notebook.append_page(page_box, Gtk.Label("Icon Browser"))
    
    def _create_mapping_tab(self, notebook: Gtk.Notebook):
        """Create the GTK-to-Carbon mapping demo tab."""
        page_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        page_box.set_margin_top(15)
        page_box.set_margin_bottom(15)
        page_box.set_margin_left(15)
        page_box.set_margin_right(15)
        
        # Description
        desc_label = Gtk.Label()
        desc_label.set_markup('<b>Standard GTK icon names automatically map to Carbon icons</b>')
        desc_label.set_halign(Gtk.Align.START)
        page_box.pack_start(desc_label, False, False, 0)
        
        # Mapping examples
        mapping_frame = Gtk.Frame(label="Icon Mapping Examples")
        mapping_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        mapping_box.set_margin_top(10)
        mapping_box.set_margin_bottom(10)
        mapping_box.set_margin_left(10)
        mapping_box.set_margin_right(10)
        
        # Sample mappings to demonstrate
        mappings = [
            ("document-save", "save"),
            ("edit-delete", "trash-can"),
            ("media-playback-start", "play"),
            ("view-refresh", "refresh"),
            ("folder", "folder"),
            ("preferences-system", "settings"),
            ("dialog-information", "information"),
            ("applications-science", "analytics")
        ]
        
        for gtk_name, carbon_name in mappings:
            row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=15)
            
            # GTK name
            gtk_label = Gtk.Label(gtk_name)
            gtk_label.set_size_request(150, -1)
            gtk_label.set_halign(Gtk.Align.START)
            row_box.pack_start(gtk_label, False, False, 0)
            
            # Arrow
            arrow_label = Gtk.Label("→")
            row_box.pack_start(arrow_label, False, False, 0)
            
            # Carbon name
            carbon_label = Gtk.Label(carbon_name)
            carbon_label.set_size_request(150, -1)
            carbon_label.set_halign(Gtk.Align.START)
            row_box.pack_start(carbon_label, False, False, 0)
            
            # Icon display
            icon_image = create_carbon_image(carbon_name, 24)
            if icon_image:
                row_box.pack_start(icon_image, False, False, 0)
            
            mapping_box.pack_start(row_box, False, False, 0)
        
        mapping_frame.add(mapping_box)
        page_box.pack_start(mapping_frame, True, True, 0)
        
        notebook.append_page(page_box, Gtk.Label("GTK Mapping"))
    
    def _create_performance_tab(self, notebook: Gtk.Notebook):
        """Create the performance and fallback demo tab."""
        page_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        page_box.set_margin_top(15)
        page_box.set_margin_bottom(15)
        page_box.set_margin_left(15)
        page_box.set_margin_right(15)
        
        # Description
        desc_label = Gtk.Label()
        desc_label.set_markup('<b>Performance testing and fallback behavior</b>')
        desc_label.set_halign(Gtk.Align.START)
        page_box.pack_start(desc_label, False, False, 0)
        
        # Performance test button
        perf_button = Gtk.Button("Run Performance Test (Load 100 Icons)")
        perf_button.connect("clicked", self._on_performance_test)
        page_box.pack_start(perf_button, False, False, 0)
        
        # Results area
        self.perf_results = Gtk.Label("")
        page_box.pack_start(self.perf_results, False, False, 0)
        
        # Fallback testing
        fallback_frame = Gtk.Frame(label="Fallback Chain Testing")
        fallback_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        fallback_box.set_margin_top(10)
        fallback_box.set_margin_bottom(10)
        fallback_box.set_margin_left(10)
        fallback_box.set_margin_right(10)
        
        # Test different icon sources
        test_icons = [
            ("Existing Carbon", "save"),
            ("Missing Carbon", "nonexistent-carbon-icon"),
            ("System Icon", "gtk-save"),
            ("Complete Fallback", "completely-missing-icon")
        ]
        
        for label, icon_name in test_icons:
            test_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            
            test_label = Gtk.Label(label)
            test_label.set_size_request(150, -1)
            test_label.set_halign(Gtk.Align.START)
            test_box.pack_start(test_label, False, False, 0)
            
            # Try to load with fallback
            pixbuf = load_icon_with_fallback(icon_name, 24)
            if pixbuf:
                image = Gtk.Image.new_from_pixbuf(pixbuf)
                test_box.pack_start(image, False, False, 0)
                result_label = Gtk.Label("✓ Loaded")
                result_label.set_markup('<span color="green">✓ Loaded</span>')
            else:
                result_label = Gtk.Label("✗ Failed")
                result_label.set_markup('<span color="red">✗ Failed</span>')
            
            test_box.pack_start(result_label, False, False, 0)
            fallback_box.pack_start(test_box, False, False, 0)
        
        fallback_frame.add(fallback_box)
        page_box.pack_start(fallback_frame, True, True, 0)
        
        notebook.append_page(page_box, Gtk.Label("Performance"))
    
    def _create_integration_tab(self, notebook: Gtk.Notebook):
        """Create the VCCTL integration examples tab."""
        page_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        page_box.set_margin_top(15)
        page_box.set_margin_bottom(15)
        page_box.set_margin_left(15)
        page_box.set_margin_right(15)
        
        # Description
        desc_label = Gtk.Label()
        desc_label.set_markup('<b>Examples of Carbon icons in VCCTL UI components</b>')
        desc_label.set_halign(Gtk.Align.START)
        page_box.pack_start(desc_label, False, False, 0)
        
        # Button examples
        buttons_frame = Gtk.Frame(label="Button Examples")
        buttons_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        buttons_box.set_margin_top(10)
        buttons_box.set_margin_bottom(10)
        buttons_box.set_margin_left(10)
        buttons_box.set_margin_right(10)
        
        # Common VCCTL buttons with Carbon icons
        button_examples = [
            ("Save", "document-save"),
            ("Open", "document-open"),
            ("Delete", "edit-delete"),
            ("Refresh", "view-refresh"),
            ("Settings", "preferences-system"),
            ("Analytics", "applications-science"),
            ("Play", "media-playback-start"),
            ("Stop", "media-playback-stop")
        ]
        
        for label, icon_name in button_examples:
            button = create_button_with_icon(label, icon_name, 16)
            buttons_box.pack_start(button, False, False, 0)
        
        buttons_frame.add(buttons_box)
        page_box.pack_start(buttons_frame, False, False, 0)
        
        # Toolbar example
        toolbar_frame = Gtk.Frame(label="Toolbar Example")
        toolbar = Gtk.Toolbar()
        toolbar.set_margin_top(10)
        toolbar.set_margin_bottom(10)
        toolbar.set_margin_left(10)
        toolbar.set_margin_right(10)
        
        toolbar_items = [
            ("New", "document-new"),
            ("Open", "document-open"),
            ("Save", "document-save"),
            ("", ""),  # Separator
            ("Delete", "edit-delete"),
            ("Refresh", "view-refresh"),
            ("", ""),  # Separator
            ("Settings", "preferences-system"),
            ("Help", "help-browser")
        ]
        
        for label, icon_name in toolbar_items:
            if not label:  # Separator
                separator = Gtk.SeparatorToolItem()
                toolbar.insert(separator, -1)
            else:
                button = Gtk.ToolButton()
                button.set_label(label)
                button.set_icon_name(icon_name)
                # The icon will be automatically replaced with Carbon via our updated utilities
                toolbar.insert(button, -1)
        
        toolbar_frame.add(toolbar)
        page_box.pack_start(toolbar_frame, False, False, 0)
        
        # Icon suggestion demo
        suggestion_frame = Gtk.Frame(label="Icon Suggestion Demo")
        suggestion_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        suggestion_box.set_margin_top(10)
        suggestion_box.set_margin_bottom(10)
        suggestion_box.set_margin_left(10)
        suggestion_box.set_margin_right(10)
        
        # Entry for action description
        entry_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        entry_label = Gtk.Label("Describe an action:")
        entry_box.pack_start(entry_label, False, False, 0)
        
        self.action_entry = Gtk.Entry()
        self.action_entry.set_placeholder_text("e.g., 'save file', 'delete item', 'analyze data'")
        entry_box.pack_start(self.action_entry, True, True, 0)
        
        suggest_button = Gtk.Button("Suggest Icon")
        suggest_button.connect("clicked", self._on_suggest_icon)
        entry_box.pack_start(suggest_button, False, False, 0)
        
        suggestion_box.pack_start(entry_box, False, False, 0)
        
        # Suggestion result
        self.suggestion_result = Gtk.Label("Enter an action description and click 'Suggest Icon'")
        suggestion_box.pack_start(self.suggestion_result, False, False, 0)
        
        suggestion_frame.add(suggestion_box)
        page_box.pack_start(suggestion_frame, True, True, 0)
        
        notebook.append_page(page_box, Gtk.Label("VCCTL Integration"))
    
    def _on_open_browser(self, button):
        """Open the Carbon icon browser."""
        selected_icon = browse_carbon_icons(self)
        
        if selected_icon:
            # Update selected icon display
            icon_info = self.carbon_manager.get_icon_info(selected_icon)
            
            # Clear previous display
            for child in self.selected_frame.get_child().get_children():
                self.selected_frame.get_child().remove(child)
            
            # Create new display
            selected_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            selected_box.set_margin_top(10)
            selected_box.set_margin_bottom(10)
            selected_box.set_margin_left(10)
            selected_box.set_margin_right(10)
            
            # Show icon at multiple sizes
            for size in [16, 24, 32, 48]:
                icon_image = create_carbon_image(selected_icon, size)
                if icon_image:
                    selected_box.pack_start(icon_image, False, False, 0)
            
            # Show info
            info_text = f"Icon: {selected_icon}\n"
            info_text += f"Category: {icon_info.get('category', 'Unknown')}\n"
            info_text += f"Description: {icon_info.get('description', 'No description')}"
            
            info_label = Gtk.Label(info_text)
            info_label.set_halign(Gtk.Align.START)
            selected_box.pack_start(info_label, True, True, 0)
            
            self.selected_frame.add(selected_box)
            self.selected_frame.show_all()
    
    def _on_performance_test(self, button):
        """Run a performance test loading multiple icons."""
        import time
        
        button.set_sensitive(False)
        self.perf_results.set_text("Running performance test...")
        
        # Force GUI update
        while Gtk.events_pending():
            Gtk.main_iteration()
        
        # Test loading 100 icons
        test_icons = self.carbon_manager.get_available_icons()[:100]
        
        start_time = time.time()
        loaded_count = 0
        
        for icon_name in test_icons:
            pixbuf = load_icon_with_fallback(icon_name, 24)
            if pixbuf:
                loaded_count += 1
        
        end_time = time.time()
        duration = end_time - start_time
        
        result_text = f"Performance Test Results:\n"
        result_text += f"Loaded {loaded_count}/{len(test_icons)} icons\n"
        result_text += f"Time: {duration:.2f} seconds\n"
        result_text += f"Average: {duration/len(test_icons)*1000:.1f}ms per icon"
        
        self.perf_results.set_text(result_text)
        button.set_sensitive(True)
    
    def _on_suggest_icon(self, button):
        """Suggest an icon based on the action description."""
        action = self.action_entry.get_text().strip()
        
        if not action:
            self.suggestion_result.set_text("Please enter an action description")
            return
        
        suggested_icon = suggest_carbon_icon(action)
        
        if suggested_icon:
            # Clear previous result
            for child in self.suggestion_result.get_parent().get_children()[2:]:
                self.suggestion_result.get_parent().remove(child)
            
            # Show suggestion with icon
            result_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            
            result_label = Gtk.Label(f"Suggested: {suggested_icon}")
            result_box.pack_start(result_label, False, False, 0)
            
            icon_image = create_carbon_image(suggested_icon, 24)
            if icon_image:
                result_box.pack_start(icon_image, False, False, 0)
            
            self.suggestion_result.get_parent().pack_start(result_box, False, False, 0)
            self.suggestion_result.get_parent().show_all()
            
            self.suggestion_result.set_text(f"Found suggestion for '{action}':")
        else:
            self.suggestion_result.set_text(f"No icon suggestion found for '{action}'")


def main():
    """Run the Carbon icon demo."""
    # Check if we're in the right directory
    if not (Path.cwd() / "src").exists():
        print("Please run this demo from the VCCTL project root directory")
        return 1
    
    print("Starting Carbon Icon Integration Demo...")
    print("Loading Carbon icons...")
    
    demo = CarbonIconDemo()
    demo.connect("destroy", Gtk.main_quit)
    demo.show_all()
    
    print("Demo ready! Explore the different tabs to see Carbon icon features.")
    Gtk.main()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
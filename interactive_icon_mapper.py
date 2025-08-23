#!/usr/bin/env python3
"""
Interactive Icon Mapping Tool for VCCTL Carbon Icon Migration
Helps user visually map current icons to Carbon equivalents
"""

import sys
import os
sys.path.insert(0, 'src')

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf, Gdk
import json
from pathlib import Path
import re

class InteractiveIconMapper(Gtk.Window):
    def __init__(self):
        super().__init__(title="VCCTL Icon Mapper - Choose Carbon Replacements")
        self.set_default_size(1400, 800)
        self.set_position(Gtk.WindowPosition.CENTER)
        
        # Load current icon usage data
        self.current_icons = self._load_current_icon_usage()
        self.carbon_icons = self._load_carbon_icons()
        self.mappings = {}
        
        self._setup_ui()
        self._populate_icon_list()

    def _load_current_icon_usage(self):
        """Load current icon usage from codebase scan"""
        icons = {}
        
        # Scan all Python files for icon usage
        src_dir = Path("src")
        if src_dir.exists():
            for py_file in src_dir.rglob("*.py"):
                try:
                    with open(py_file, 'r') as f:
                        content = f.read()
                    
                    # Find icon usage patterns
                    patterns = [
                        r'new_from_icon_name\(\s*["\']([^"\']+)["\']',
                        r'set_icon_name\(\s*["\']([^"\']+)["\']',
                        r'button_with_icon\([^,]+,\s*["\']([^"\']+)["\']',
                        r'from_icon_name\(\s*["\']([^"\']+)["\']',
                    ]
                    
                    for pattern in patterns:
                        matches = re.findall(pattern, content)
                        for match in matches:
                            if match not in icons:
                                icons[match] = []
                            icons[match].append(str(py_file))
                            
                except Exception as e:
                    continue
                    
        return icons

    def _load_carbon_icons(self):
        """Load available Carbon icons"""
        carbon_dir = Path("icons/carbon")
        if not carbon_dir.exists():
            return []
            
        icons = []
        for svg_file in carbon_dir.glob("*.svg"):
            icons.append(svg_file.stem)
        
        return sorted(icons)

    def _setup_ui(self):
        """Setup the user interface"""
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        main_box.set_margin_left(10)
        main_box.set_margin_right(10)
        main_box.set_margin_top(10)
        main_box.set_margin_bottom(10)
        self.add(main_box)
        
        # Header
        header_label = Gtk.Label()
        header_label.set_markup('<span size="20000"><b>Choose Carbon Icons for VCCTL</b></span>')
        main_box.pack_start(header_label, False, False, 10)
        
        # Instructions
        instructions = Gtk.Label()
        instructions.set_markup('''<span size="12000">
<b>Instructions:</b>
1. Select a current VCCTL icon from the left list
2. Choose a Carbon replacement from the right search/list  
3. Click "Map Icon" to save the mapping
4. Click "Generate Migration Script" when done to apply all mappings
</span>''')
        instructions.set_line_wrap(True)
        main_box.pack_start(instructions, False, False, 5)
        
        # Main content area
        content_paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        main_box.pack_start(content_paned, True, True, 0)
        
        # Left panel - Current icons
        self._setup_current_icons_panel(content_paned)
        
        # Right panel - Carbon icons
        self._setup_carbon_icons_panel(content_paned)
        
        # Bottom buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        main_box.pack_start(button_box, False, False, 10)
        
        # Map button
        self.map_button = Gtk.Button(label="Map Selected Icons")
        self.map_button.set_sensitive(False)
        self.map_button.connect('clicked', self._on_map_clicked)
        button_box.pack_start(self.map_button, False, False, 0)
        
        # Generate script button
        self.generate_button = Gtk.Button(label="Generate Migration Script")
        self.generate_button.connect('clicked', self._on_generate_clicked)
        button_box.pack_end(self.generate_button, False, False, 0)
        
        # Status label
        self.status_label = Gtk.Label()
        button_box.pack_start(self.status_label, True, True, 0)

    def _setup_current_icons_panel(self, parent):
        """Setup left panel with current VCCTL icons"""
        left_frame = Gtk.Frame(label="Current VCCTL Icons")
        left_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        left_box.set_margin_left(10)
        left_box.set_margin_right(10)
        left_box.set_margin_top(10)
        left_box.set_margin_bottom(10)
        left_frame.add(left_box)
        
        # Search entry
        self.current_search = Gtk.SearchEntry()
        self.current_search.set_placeholder_text("Search current icons...")
        self.current_search.connect('search-changed', self._on_current_search)
        left_box.pack_start(self.current_search, False, False, 0)
        
        # Icon list
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_size_request(400, -1)
        
        self.current_liststore = Gtk.ListStore(str, str, int)  # icon_name, usage_info, usage_count
        self.current_treeview = Gtk.TreeView(model=self.current_liststore)
        
        # Icon name column
        icon_renderer = Gtk.CellRendererText()
        icon_column = Gtk.TreeViewColumn("Icon Name", icon_renderer, text=0)
        icon_column.set_sort_column_id(0)
        self.current_treeview.append_column(icon_column)
        
        # Usage count column
        count_renderer = Gtk.CellRendererText()
        count_column = Gtk.TreeViewColumn("Uses", count_renderer, text=2)
        count_column.set_sort_column_id(2)
        self.current_treeview.append_column(count_column)
        
        # Usage info column
        usage_renderer = Gtk.CellRendererText()
        usage_renderer.set_property("ellipsize", 3)  # ELLIPSIZE_END
        usage_column = Gtk.TreeViewColumn("Files", usage_renderer, text=1)
        usage_column.set_expand(True)
        self.current_treeview.append_column(usage_column)
        
        self.current_treeview.connect('cursor-changed', self._on_current_icon_selected)
        
        scrolled.add(self.current_treeview)
        left_box.pack_start(scrolled, True, True, 0)
        
        parent.pack1(left_frame, True, True)

    def _setup_carbon_icons_panel(self, parent):
        """Setup right panel with Carbon icons"""
        right_frame = Gtk.Frame(label="Carbon Design System Icons")
        right_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        right_box.set_margin_left(10)
        right_box.set_margin_right(10)
        right_box.set_margin_top(10)
        right_box.set_margin_bottom(10)
        right_frame.add(right_box)
        
        # Search entry
        self.carbon_search = Gtk.SearchEntry()
        self.carbon_search.set_placeholder_text("Search Carbon icons...")
        self.carbon_search.connect('search-changed', self._on_carbon_search)
        right_box.pack_start(self.carbon_search, False, False, 0)
        
        # Suggestion label
        self.suggestion_label = Gtk.Label()
        self.suggestion_label.set_markup('<i>Select a current icon to see suggestions</i>')
        right_box.pack_start(self.suggestion_label, False, False, 0)
        
        # Icon list
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_size_request(600, -1)
        
        self.carbon_liststore = Gtk.ListStore(str, str)  # icon_name, preview
        self.carbon_treeview = Gtk.TreeView(model=self.carbon_liststore)
        
        # Icon name column
        name_renderer = Gtk.CellRendererText()
        name_column = Gtk.TreeViewColumn("Carbon Icon", name_renderer, text=0)
        name_column.set_sort_column_id(0)
        self.carbon_treeview.append_column(name_column)
        
        # Preview column (placeholder for now)
        preview_renderer = Gtk.CellRendererText()
        preview_column = Gtk.TreeViewColumn("Preview", preview_renderer, text=1)
        self.carbon_treeview.append_column(preview_column)
        
        self.carbon_treeview.connect('cursor-changed', self._on_carbon_icon_selected)
        
        scrolled.add(self.carbon_treeview)
        right_box.pack_start(scrolled, True, True, 0)
        
        parent.pack2(right_frame, True, True)

    def _populate_icon_list(self):
        """Populate the current icon list"""
        self.current_liststore.clear()
        
        for icon_name, files in self.current_icons.items():
            usage_info = ", ".join(Path(f).name for f in files[:3])  # Show first 3 files
            if len(files) > 3:
                usage_info += f", ... (+{len(files)-3} more)"
            
            self.current_liststore.append([icon_name, usage_info, len(files)])
        
        # Sort by usage count descending
        self.current_liststore.set_sort_column_id(2, Gtk.SortType.DESCENDING)
        
        # Populate Carbon icons
        self._populate_carbon_list()

    def _populate_carbon_list(self, filter_text=""):
        """Populate Carbon icon list with optional filtering"""
        self.carbon_liststore.clear()
        
        for icon in self.carbon_icons:
            if not filter_text or filter_text.lower() in icon.lower():
                self.carbon_liststore.append([icon, "📄 SVG"])

    def _on_current_search(self, entry):
        """Handle search in current icons"""
        search_text = entry.get_text().lower()
        
        self.current_liststore.clear()
        for icon_name, files in self.current_icons.items():
            if not search_text or search_text in icon_name.lower():
                usage_info = ", ".join(Path(f).name for f in files[:3])
                if len(files) > 3:
                    usage_info += f", ... (+{len(files)-3} more)"
                
                self.current_liststore.append([icon_name, usage_info, len(files)])

    def _on_carbon_search(self, entry):
        """Handle search in Carbon icons"""
        search_text = entry.get_text()
        self._populate_carbon_list(search_text)

    def _on_current_icon_selected(self, treeview):
        """Handle selection of current icon"""
        selection = treeview.get_selection()
        model, treeiter = selection.get_selected()
        
        if treeiter:
            icon_name = model[treeiter][0]
            self._suggest_carbon_icons(icon_name)
            self._update_map_button()

    def _on_carbon_icon_selected(self, treeview):
        """Handle selection of Carbon icon"""
        self._update_map_button()

    def _suggest_carbon_icons(self, current_icon):
        """Suggest Carbon icons based on current icon name"""
        suggestions = []
        
        # Simple keyword matching
        keywords = current_icon.lower().replace("-", " ").replace("_", " ").split()
        keywords = [k for k in keywords if k not in ['symbolic', 'gtk', 'stock']]
        
        for carbon_icon in self.carbon_icons:
            carbon_lower = carbon_icon.lower()
            score = 0
            
            for keyword in keywords:
                if keyword in carbon_lower:
                    score += 1
            
            if score > 0:
                suggestions.append((carbon_icon, score))
        
        # Sort by relevance
        suggestions.sort(key=lambda x: x[1], reverse=True)
        
        if suggestions:
            top_suggestions = [s[0] for s in suggestions[:5]]
            suggestion_text = f'<b>Suggested:</b> {", ".join(top_suggestions[:3])}'
            if len(top_suggestions) > 3:
                suggestion_text += f" (+{len(top_suggestions)-3} more)"
        else:
            suggestion_text = f'<i>No automatic suggestions for "{current_icon}"</i>'
        
        self.suggestion_label.set_markup(suggestion_text)
        
        # Filter carbon list to show suggestions first
        self.carbon_liststore.clear()
        
        # Add suggestions first
        for icon in suggestions[:10]:  # Top 10 suggestions
            self.carbon_liststore.append([icon[0], f"📄 SVG (Score: {icon[1]})"])
        
        # Add separator if we have suggestions
        if suggestions:
            self.carbon_liststore.append(["--- All Icons ---", ""])
        
        # Add all icons
        for icon in self.carbon_icons:
            if icon not in [s[0] for s in suggestions[:10]]:
                self.carbon_liststore.append([icon, "📄 SVG"])

    def _update_map_button(self):
        """Update map button sensitivity"""
        current_selected = self._get_selected_current_icon()
        carbon_selected = self._get_selected_carbon_icon()
        
        self.map_button.set_sensitive(
            current_selected is not None and 
            carbon_selected is not None and
            carbon_selected != "--- All Icons ---"
        )

    def _get_selected_current_icon(self):
        """Get currently selected current icon"""
        selection = self.current_treeview.get_selection()
        model, treeiter = selection.get_selected()
        return model[treeiter][0] if treeiter else None

    def _get_selected_carbon_icon(self):
        """Get currently selected Carbon icon"""
        selection = self.carbon_treeview.get_selection()
        model, treeiter = selection.get_selected()
        return model[treeiter][0] if treeiter else None

    def _on_map_clicked(self, button):
        """Handle mapping an icon"""
        current_icon = self._get_selected_current_icon()
        carbon_icon = self._get_selected_carbon_icon()
        
        if current_icon and carbon_icon and carbon_icon != "--- All Icons ---":
            self.mappings[current_icon] = carbon_icon
            self.status_label.set_markup(
                f'<span color="green">Mapped <b>{current_icon}</b> → <b>{carbon_icon}</b></span>'
            )
            
            # Update the current icon display to show it's mapped
            for row in self.current_liststore:
                if row[0] == current_icon:
                    row[1] = f"✅ → {carbon_icon} | {row[1].split(' | ')[-1] if ' | ' in row[1] else row[1]}"
                    break

    def _on_generate_clicked(self, button):
        """Generate migration script with all mappings"""
        if not self.mappings:
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.OK,
                text="No icon mappings defined"
            )
            dialog.format_secondary_text("Please map some icons before generating the migration script.")
            dialog.run()
            dialog.destroy()
            return
        
        # Generate comprehensive migration script
        script_content = self._generate_migration_script()
        
        # Save script
        script_path = Path("apply_user_chosen_carbon_migration.py")
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        # Save mappings
        mappings_path = Path("user_icon_mappings.json")
        with open(mappings_path, 'w') as f:
            json.dump(self.mappings, f, indent=2)
        
        # Show completion dialog
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Migration script generated!"
        )
        dialog.format_secondary_text(
            f"Created {script_path} with {len(self.mappings)} icon mappings.\n\n"
            f"Run 'python3 {script_path}' to apply all mappings."
        )
        dialog.run()
        dialog.destroy()

    def _generate_migration_script(self):
        """Generate the actual migration script"""
        script = '''#!/usr/bin/env python3
"""User-chosen VCCTL Carbon icon migration script"""

import re
from pathlib import Path

def migrate_icons():
    """Apply user-chosen icon mappings."""
    
    # Icon mappings chosen by user
    mappings = {
'''
        
        for old_icon, new_icon in self.mappings.items():
            script += f'        "{old_icon}": "{new_icon}",\n'
        
        script += '''    }
    
    print(f"Applying {len(mappings)} icon mappings...")
    
    # Find all Python files in src directory
    src_dir = Path("src")
    files_modified = 0
    
    for py_file in src_dir.rglob("*.py"):
        try:
            with open(py_file, 'r') as f:
                content = f.read()
            
            original_content = content
            
            # Apply each mapping
            for old_icon, new_icon in mappings.items():
                # Replace in various icon usage patterns
                patterns = [
                    rf'(new_from_icon_name\\(\\s*["\']){old_icon}(["\'])',
                    rf'(set_icon_name\\(\\s*["\']){old_icon}(["\'])',
                    rf'(from_icon_name\\(\\s*["\']){old_icon}(["\'])',
                    rf'(button_with_icon\\([^,]+,\\s*["\']){old_icon}(["\'])',
                ]
                
                for pattern in patterns:
                    content = re.sub(pattern, rf'\\1{new_icon}\\2', content)
            
            # Write back if changed
            if content != original_content:
                with open(py_file, 'w') as f:
                    f.write(content)
                files_modified += 1
                print(f"  Modified: {py_file}")
                
        except Exception as e:
            print(f"  Error processing {py_file}: {e}")
    
    print(f"\\n✅ Migration completed! {files_modified} files modified.")

if __name__ == "__main__":
    migrate_icons()
'''
        return script


def main():
    app = InteractiveIconMapper()
    app.connect("destroy", Gtk.main_quit)
    app.show_all()
    Gtk.main()

if __name__ == "__main__":
    main()
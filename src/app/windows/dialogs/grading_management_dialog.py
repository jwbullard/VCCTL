#!/usr/bin/env python3
"""
Grading Management Dialog for VCCTL

Professional interface for managing saved grading templates with search,
filtering, and bulk operations capabilities.
"""

import logging
from typing import List, Optional, Dict, Any
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GObject, Pango

from app.services.grading_service import GradingService
from app.models.grading import Grading, GradingType
from app.utils.grading_file_utils import grading_file_manager
from app.utils.icon_utils import create_carbon_image


class GradingManagementDialog(Gtk.Dialog):
    """Professional grading management dialog with advanced features."""
    
    def __init__(self, parent: Gtk.Window, db_service):
        """Initialize the grading management dialog."""
        super().__init__(
            title="Manage Grading Templates",
            parent=parent,
            flags=Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT
        )
        
        self.parent = parent
        self.db_service = db_service
        self.grading_service = GradingService(db_service)
        self.logger = logging.getLogger(__name__)
        
        # Selection tracking
        self.selected_grading = None
        self.selected_gradings = []  # For bulk operations
        
        # Set dialog size and position
        self.set_default_size(900, 600)
        self.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)
        
        # Build UI
        try:
            self._build_ui()
            self._setup_shortcuts()
            self._load_gradings()
            
            # Show all content
            self.show_all()
            
        except Exception as e:
            self.logger.error(f"Failed to build dialog UI: {e}")
            import traceback
            traceback.print_exc()
        
        # Connect signals
        self.connect("response", self._on_response)
    
    def _build_ui(self):
        """Build the main UI components."""
        # Get content area
        content_area = self.get_content_area()
        content_area.set_spacing(10)
        content_area.set_margin_left(10)
        content_area.set_margin_right(10)
        content_area.set_margin_top(10)
        content_area.set_margin_bottom(10)
        
        # Create main container
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        content_area.pack_start(main_box, True, True, 0)
        
        # Build toolbar
        self._build_toolbar(main_box)
        
        # Build search bar
        self._build_search_bar(main_box)
        
        # Build main content area with list and preview
        self._build_main_content(main_box)
        
        # Build status bar
        self._build_status_bar(main_box)
        
        # Make sure all content is visible
        main_box.show_all()
        
        # Add action buttons
        self.add_button("Close", Gtk.ResponseType.CLOSE)
    
    def _build_toolbar(self, parent: Gtk.Box):
        """Build the toolbar with action buttons."""
        toolbar = Gtk.Toolbar()
        toolbar.set_style(Gtk.ToolbarStyle.BOTH)
        toolbar.set_icon_size(Gtk.IconSize.SMALL_TOOLBAR)
        parent.pack_start(toolbar, False, False, 0)
        
        # Load button
        load_icon = create_carbon_image("folder--open", size=16)
        self.load_button = Gtk.ToolButton(icon_widget=load_icon, label="Load")
        self.load_button.set_tooltip_text("Load selected grading into editor")
        self.load_button.connect("clicked", self._on_load_clicked)
        self.load_button.set_sensitive(False)
        toolbar.insert(self.load_button, -1)
        
        toolbar.insert(Gtk.SeparatorToolItem(), -1)
        
        # Refresh button
        refresh_icon = create_carbon_image("renew", size=16)
        refresh_button = Gtk.ToolButton(icon_widget=refresh_icon, label="Refresh")
        refresh_button.set_tooltip_text("Refresh template list")
        refresh_button.connect("clicked", self._on_refresh_clicked)
        toolbar.insert(refresh_button, -1)
        
        toolbar.insert(Gtk.SeparatorToolItem(), -1)
        
        # Save As button
        save_icon = create_carbon_image("save", size=16)
        save_as_button = Gtk.ToolButton(icon_widget=save_icon, label="Save As")
        save_as_button.set_tooltip_text("Save current editor state as new template")
        save_as_button.connect("clicked", self._on_save_as_clicked)
        toolbar.insert(save_as_button, -1)
        
        # Duplicate button
        duplicate_icon = create_carbon_image("copy", size=16)
        self.duplicate_button = Gtk.ToolButton(icon_widget=duplicate_icon, label="Duplicate")
        self.duplicate_button.set_tooltip_text("Create copy of selected grading")
        self.duplicate_button.connect("clicked", self._on_duplicate_clicked)
        self.duplicate_button.set_sensitive(False)
        toolbar.insert(self.duplicate_button, -1)
        
        toolbar.insert(Gtk.SeparatorToolItem(), -1)
        
        # Export button
        export_icon = create_carbon_image("export", size=16)
        self.export_button = Gtk.ToolButton(icon_widget=export_icon, label="Export")
        self.export_button.set_tooltip_text("Export selected grading to .gdg file")
        self.export_button.connect("clicked", self._on_export_clicked)
        self.export_button.set_sensitive(False)
        toolbar.insert(self.export_button, -1)
        
        # Import button
        import_icon = create_carbon_image("import-export", size=16)
        import_button = Gtk.ToolButton(icon_widget=import_icon, label="Import")
        import_button.set_tooltip_text("Import grading from .gdg file")
        import_button.connect("clicked", self._on_import_clicked)
        toolbar.insert(import_button, -1)
        
        toolbar.insert(Gtk.SeparatorToolItem(), -1)
        
        # Delete button
        delete_icon = create_carbon_image("trash-can", size=16)
        self.delete_button = Gtk.ToolButton(icon_widget=delete_icon, label="Delete")
        self.delete_button.set_tooltip_text("Delete selected grading(s)")
        self.delete_button.connect("clicked", self._on_delete_clicked)
        self.delete_button.set_sensitive(False)
        toolbar.insert(self.delete_button, -1)
    
    def _build_search_bar(self, parent: Gtk.Box):
        """Build search and filter bar."""
        search_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        parent.pack_start(search_box, False, False, 0)
        
        # Search entry
        search_box.pack_start(Gtk.Label("Search:"), False, False, 0)
        
        self.search_entry = Gtk.Entry()
        self.search_entry.set_placeholder_text("Filter by name or description...")
        self.search_entry.set_icon_from_icon_name(Gtk.EntryIconPosition.SECONDARY, "system-search")
        self.search_entry.connect("changed", self._on_search_changed)
        search_box.pack_start(self.search_entry, True, True, 0)
        
        # Type filter
        search_box.pack_start(Gtk.Label("Type:"), False, False, 0)
        
        self.type_filter = Gtk.ComboBoxText()
        self.type_filter.append("ALL", "All Types")
        self.type_filter.append("FINE", "Fine Aggregate")
        self.type_filter.append("COARSE", "Coarse Aggregate")
        self.type_filter.append("STANDARD", "Standard Templates")
        self.type_filter.append("CUSTOM", "Custom Templates")
        self.type_filter.set_active_id("ALL")
        self.type_filter.connect("changed", self._on_filter_changed)
        search_box.pack_start(self.type_filter, False, False, 0)
        
        # Sort order
        search_box.pack_start(Gtk.Label("Sort:"), False, False, 0)
        
        self.sort_combo = Gtk.ComboBoxText()
        self.sort_combo.append("name_asc", "Name (A-Z)")
        self.sort_combo.append("name_desc", "Name (Z-A)")
        self.sort_combo.append("type_asc", "Type")
        self.sort_combo.append("created_desc", "Newest First")
        self.sort_combo.append("created_asc", "Oldest First")
        self.sort_combo.set_active_id("name_asc")
        self.sort_combo.connect("changed", self._on_filter_changed)
        search_box.pack_start(self.sort_combo, False, False, 0)
    
    def _build_main_content(self, parent: Gtk.Box):
        """Build main content area with list and preview."""
        # Horizontal paned container
        paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        paned.set_position(500)  # Default split position
        parent.pack_start(paned, True, True, 0)
        
        # Left panel - grading list
        self._build_grading_list(paned)
        
        # Right panel - preview
        self._build_preview_panel(paned)
    
    def _build_grading_list(self, parent: Gtk.Paned):
        """Build the grading list view."""
        # Scrolled window for list
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_size_request(450, -1)
        parent.pack1(scrolled, True, False)
        
        # Create TreeView with model
        self.list_store = Gtk.ListStore(
            str,      # name
            str,      # type
            str,      # description
            str,      # max_diameter
            str,      # created_at
            bool,     # is_standard
            int,      # sieve_point_count
            object    # grading object
        )
        
        self.tree_view = Gtk.TreeView(model=self.list_store)
        self.tree_view.set_rules_hint(True)
        self.tree_view.set_search_column(0)  # Search by name
        self.tree_view.get_selection().set_mode(Gtk.SelectionMode.MULTIPLE)
        self.tree_view.get_selection().connect("changed", self._on_selection_changed)
        self.tree_view.connect("row-activated", self._on_row_activated)
        scrolled.add(self.tree_view)
        
        # Create columns
        self._create_list_columns()
    
    def _create_list_columns(self):
        """Create columns for the grading list."""
        # Name column
        renderer = Gtk.CellRendererText()
        renderer.set_property("weight", Pango.Weight.BOLD)
        column = Gtk.TreeViewColumn("Name", renderer, text=0)
        column.set_sort_column_id(0)
        column.set_resizable(True)
        column.set_min_width(150)
        self.tree_view.append_column(column)
        
        # Type column with color coding
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Type", renderer, text=1)
        column.set_sort_column_id(1)
        column.set_resizable(True)
        column.set_min_width(80)
        self.tree_view.append_column(column)
        
        # Description column
        renderer = Gtk.CellRendererText()
        renderer.set_property("ellipsize", Pango.EllipsizeMode.END)
        column = Gtk.TreeViewColumn("Description", renderer, text=2)
        column.set_sort_column_id(2)
        column.set_resizable(True)
        column.set_expand(True)
        self.tree_view.append_column(column)
        
        # Max Diameter column
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Max Size (mm)", renderer, text=3)
        column.set_sort_column_id(3)
        column.set_resizable(True)
        column.set_min_width(90)
        self.tree_view.append_column(column)
        
        # Sieve Points column
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Points", renderer, text=6)
        column.set_sort_column_id(6)
        column.set_resizable(True)
        column.set_min_width(60)
        self.tree_view.append_column(column)
        
        # Created column
        renderer = Gtk.CellRendererText()
        renderer.set_property("foreground", "gray")
        column = Gtk.TreeViewColumn("Created", renderer, text=4)
        column.set_sort_column_id(4)
        column.set_resizable(True)
        column.set_min_width(100)
        self.tree_view.append_column(column)
    
    def _build_preview_panel(self, parent: Gtk.Paned):
        """Build the preview panel."""
        preview_frame = Gtk.Frame(label="Preview")
        preview_frame.set_size_request(350, -1)
        parent.pack2(preview_frame, False, False)
        
        # Scrolled container for preview content
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        preview_frame.add(scrolled)
        
        # Preview content box
        self.preview_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.preview_box.set_margin_left(10)
        self.preview_box.set_margin_right(10)
        self.preview_box.set_margin_top(10)
        self.preview_box.set_margin_bottom(10)
        scrolled.add(self.preview_box)
        
        # Initial empty state
        self._show_empty_preview()
    
    def _show_empty_preview(self):
        """Show empty preview state."""
        # Clear existing content
        for child in self.preview_box.get_children():
            self.preview_box.remove(child)
        
        # Empty state message
        label = Gtk.Label("Select a grading template to preview")
        label.set_markup("<i>Select a grading template to preview</i>")
        label.set_justify(Gtk.Justification.CENTER)
        self.preview_box.pack_start(label, True, True, 0)
        self.preview_box.show_all()
    
    def _show_grading_preview(self, grading: Grading):
        """Show preview for selected grading."""
        # Clear existing content
        for child in self.preview_box.get_children():
            self.preview_box.remove(child)
        
        # Grading info section
        info_frame = Gtk.Frame(label="Information")
        self.preview_box.pack_start(info_frame, False, False, 0)
        
        info_grid = Gtk.Grid()
        info_grid.set_column_spacing(10)
        info_grid.set_row_spacing(5)
        info_grid.set_margin_left(10)
        info_grid.set_margin_right(10)
        info_grid.set_margin_top(10)
        info_grid.set_margin_bottom(10)
        info_frame.add(info_grid)
        
        row = 0
        
        # Name
        info_grid.attach(Gtk.Label("Name:"), 0, row, 1, 1)
        name_label = Gtk.Label(grading.name)
        name_label.set_markup(f"<b>{grading.name}</b>")
        name_label.set_halign(Gtk.Align.START)
        info_grid.attach(name_label, 1, row, 1, 1)
        row += 1
        
        # Type
        info_grid.attach(Gtk.Label("Type:"), 0, row, 1, 1)
        type_str = grading.type.value if grading.type else "Unknown"
        type_label = Gtk.Label(type_str)
        type_label.set_halign(Gtk.Align.START)
        info_grid.attach(type_label, 1, row, 1, 1)
        row += 1
        
        # Description
        if grading.description:
            info_grid.attach(Gtk.Label("Description:"), 0, row, 1, 1)
            desc_label = Gtk.Label(grading.description)
            desc_label.set_line_wrap(True)
            desc_label.set_halign(Gtk.Align.START)
            info_grid.attach(desc_label, 1, row, 1, 1)
            row += 1
        
        # Max diameter
        if grading.max_diameter:
            info_grid.attach(Gtk.Label("Max Diameter:"), 0, row, 1, 1)
            max_label = Gtk.Label(f"{grading.max_diameter:.2f} mm")
            max_label.set_halign(Gtk.Align.START)
            info_grid.attach(max_label, 1, row, 1, 1)
            row += 1
        
        # Standard template indicator
        if grading.is_system_grading:
            info_grid.attach(Gtk.Label("Template:"), 0, row, 1, 1)
            std_label = Gtk.Label("Standard")
            std_label.set_markup("<i>Standard</i>")
            std_label.set_halign(Gtk.Align.START)
            info_grid.attach(std_label, 1, row, 1, 1)
            row += 1
        
        # Sieve data section
        if grading.has_grading_data:
            sieve_frame = Gtk.Frame(label="Sieve Analysis Data")
            self.preview_box.pack_start(sieve_frame, True, True, 0)
            
            sieve_scrolled = Gtk.ScrolledWindow()
            sieve_scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
            sieve_scrolled.set_min_content_height(200)
            sieve_frame.add(sieve_scrolled)
            
            # Create sieve data table
            sieve_store = Gtk.ListStore(str, str)  # size, percent
            sieve_view = Gtk.TreeView(model=sieve_store)
            sieve_view.set_headers_visible(True)
            sieve_scrolled.add(sieve_view)
            
            # Size column
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn("Sieve Size (mm)", renderer, text=0)
            column.set_min_width(120)
            sieve_view.append_column(column)
            
            # Percent column
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn("% Passing", renderer, text=1)
            column.set_min_width(100)
            sieve_view.append_column(column)
            
            # Populate sieve data
            sieve_data = grading.get_sieve_data()
            if sieve_data:
                # Sort by size (largest first)
                sorted_data = sorted(sieve_data, key=lambda x: x['sieve_size'], reverse=True)
                for point in sorted_data:
                    sieve_store.append([
                        f"{point['sieve_size']:.3f}",
                        f"{point['percent_passing']:.1f}"
                    ])
        
        self.preview_box.show_all()
    
    def _build_status_bar(self, parent: Gtk.Box):
        """Build status bar."""
        self.status_bar = Gtk.Statusbar()
        self.status_context = self.status_bar.get_context_id("grading_management")
        parent.pack_start(self.status_bar, False, False, 0)
        
        # Initial status
        self._update_status("Ready")
    
    def _setup_shortcuts(self):
        """Setup keyboard shortcuts."""
        accel_group = Gtk.AccelGroup()
        self.add_accel_group(accel_group)
        
        # Ctrl+F for search focus
        self.search_entry.add_accelerator(
            "grab-focus", accel_group,
            Gdk.keyval_from_name("f"), Gdk.ModifierType.CONTROL_MASK,
            Gtk.AccelFlags.VISIBLE
        )
        
        # Delete key for deletion
        self.delete_button.add_accelerator(
            "clicked", accel_group,
            Gdk.keyval_from_name("Delete"), 0,
            Gtk.AccelFlags.VISIBLE
        )
        
        # Ctrl+D for duplicate
        self.duplicate_button.add_accelerator(
            "clicked", accel_group,
            Gdk.keyval_from_name("d"), Gdk.ModifierType.CONTROL_MASK,
            Gtk.AccelFlags.VISIBLE
        )
    
    def _load_gradings(self):
        """Load all gradings into the list."""
        try:
            self._update_status("Loading gradings...")
            
            # Get all gradings
            all_gradings = self.grading_service.get_all_gradings_by_type()
            
            # Clear existing data
            self.list_store.clear()
            
            # Populate list
            for grading in all_gradings:
                # Format created date
                created_str = ""
                if grading.created_at:
                    created_str = grading.created_at.strftime("%Y-%m-%d")
                
                # Count sieve points
                sieve_count = 0
                if grading.has_grading_data:
                    sieve_data = grading.get_sieve_data()
                    if sieve_data:
                        sieve_count = len(sieve_data)
                
                # Format max diameter
                max_diam_str = ""
                if grading.max_diameter:
                    max_diam_str = f"{grading.max_diameter:.2f}"
                
                # Format type
                type_str = grading.type.value if grading.type else ""
                
                self.list_store.append([
                    grading.name,
                    type_str,
                    grading.description or "",
                    max_diam_str,
                    created_str,
                    grading.is_system_grading,
                    sieve_count,
                    grading
                ])
            
            self._update_status(f"Loaded {len(all_gradings)} grading templates")
            
        except Exception as e:
            self.logger.error(f"Failed to load gradings: {e}")
            self._update_status("Failed to load gradings")
    
    def refresh_templates(self):
        """Refresh the template list - useful when new templates are added."""
        self._load_gradings()
        self.logger.debug("Template list refreshed")
    
    def _apply_filters(self):
        """Apply current search and filter settings by reloading data."""
        search_text = self.search_entry.get_text().lower()
        type_filter = self.type_filter.get_active_id()
        
        try:
            # Get all gradings from database
            all_gradings = self.grading_service.get_all_gradings_by_type()
            
            # Clear current list
            self.list_store.clear()
            
            # Apply filters and populate list
            filtered_count = 0
            for grading in all_gradings:
                show_grading = True
                
                # Apply search filter (check name and description)
                if search_text:
                    name_match = search_text in grading.name.lower()
                    desc_match = search_text in (grading.description or "").lower()
                    if not (name_match or desc_match):
                        show_grading = False
                
                # Apply type filter
                if type_filter != "ALL" and show_grading:
                    grading_type_str = str(grading.type.value) if grading.type else None
                    if type_filter == "FINE" and grading_type_str != "FINE":
                        show_grading = False
                    elif type_filter == "COARSE" and grading_type_str != "COARSE":
                        show_grading = False
                    elif type_filter == "STANDARD" and not grading.is_system_grading:
                        show_grading = False
                    elif type_filter == "CUSTOM" and grading.is_system_grading:
                        show_grading = False
                
                # Add to list if it passes filters
                if show_grading:
                    # Format type display
                    type_str = "Fine Aggregate" if grading.type and grading.type.value == "FINE" else "Coarse Aggregate"
                    
                    # Format max diameter
                    max_diam_str = ""
                    if grading.has_grading_data:
                        sieve_data = grading.get_sieve_data()
                        if sieve_data:
                            max_size = max(point['sieve_size'] for point in sieve_data)
                            max_diam_str = f"{max_size:.1f} mm"
                    
                    # Format created date
                    created_str = ""
                    if grading.created_at:
                        created_str = grading.created_at.strftime("%Y-%m-%d")
                    
                    # Count sieve points
                    sieve_count = 0
                    if grading.has_grading_data:
                        sieve_data = grading.get_sieve_data()
                        if sieve_data:
                            sieve_count = len(sieve_data)
                    
                    # Add to list
                    self.list_store.append([
                        grading.name,
                        type_str,
                        grading.description or "",
                        max_diam_str,
                        created_str,
                        grading.is_system_grading,
                        sieve_count,
                        grading
                    ])
                    filtered_count += 1
            
            # Update status
            total_count = len(all_gradings)
            if search_text or type_filter != "ALL":
                filter_info = []
                if search_text:
                    filter_info.append(f"search: '{search_text}'")
                if type_filter != "ALL":
                    filter_info.append(f"type: {type_filter}")
                self._update_status(f"Showing {filtered_count} of {total_count} templates ({', '.join(filter_info)})")
            else:
                self._update_status(f"Showing {filtered_count} grading templates")
            
        except Exception as e:
            self.logger.error(f"Failed to apply filters: {e}")
            self._update_status("Error applying filters")
    
    def _update_status(self, message: str):
        """Update status bar message."""
        self.status_bar.remove_all(self.status_context)
        self.status_bar.push(self.status_context, message)
    
    # Event handlers
    def _on_selection_changed(self, selection: Gtk.TreeSelection):
        """Handle selection changes."""
        model, paths = selection.get_selected_rows()
        
        # Update button states
        has_selection = len(paths) > 0
        single_selection = len(paths) == 1
        
        self.load_button.set_sensitive(single_selection)
        self.duplicate_button.set_sensitive(single_selection)
        self.export_button.set_sensitive(single_selection)
        self.delete_button.set_sensitive(has_selection)
        
        # Update preview
        if single_selection:
            iter = model.get_iter(paths[0])
            grading = model.get_value(iter, 7)  # grading object column
            self.selected_grading = grading
            self._show_grading_preview(grading)
            
            # Update status
            sieve_count = model.get_value(iter, 6)
            grading_type = model.get_value(iter, 1)
            self._update_status(f"Selected: {grading.name} ({grading_type}, {sieve_count} points)")
        else:
            self.selected_grading = None
            self._show_empty_preview()
            if has_selection:
                self._update_status(f"{len(paths)} templates selected")
            else:
                self._update_status("Ready")
    
    def _on_row_activated(self, tree_view: Gtk.TreeView, path: Gtk.TreePath, column: Gtk.TreeViewColumn):
        """Handle double-click on row."""
        # Double-click loads the grading
        self._on_load_clicked(None)
    
    def _on_search_changed(self, entry: Gtk.Entry):
        """Handle search text changes."""
        self._apply_filters()
    
    def _on_filter_changed(self, combo: Gtk.ComboBox):
        """Handle filter changes."""
        self._apply_filters()
    
    def _on_load_clicked(self, button):
        """Handle Load button click."""
        if self.selected_grading:
            # Emit a custom signal that the parent can connect to
            # For now, just close dialog with OK response
            self._update_status(f"Loading {self.selected_grading.name}...")
            self.response(Gtk.ResponseType.OK)
    
    def _on_refresh_clicked(self, button):
        """Handle Refresh button click."""
        self.refresh_templates()
        self._update_status("Template list refreshed")
    
    def _on_save_as_clicked(self, button):
        """Handle Save As button click."""
        # Show info about where to find save functionality
        info_dialog = Gtk.MessageDialog(
            parent=self,
            flags=Gtk.DialogFlags.MODAL,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Save Current Grading"
        )
        info_dialog.format_secondary_text(
            "To save your current grading curve as a template:\n\n"
            "1. Open an aggregate grading dialog\n"
            "2. Configure your grading curve\n"
            "3. Click 'Save Template' in the grading widget toolbar\n\n"
            "The saved template will then appear in this management dialog."
        )
        info_dialog.run()
        info_dialog.destroy()
        self._update_status("Use 'Save Template' button in grading widget to create new templates")
    
    def _on_duplicate_clicked(self, button):
        """Handle Duplicate button click."""
        if not self.selected_grading:
            return
            
        # Show dialog to get new name
        dialog = Gtk.MessageDialog(
            parent=self,
            flags=Gtk.DialogFlags.MODAL,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.OK_CANCEL,
            text="Duplicate Grading Template"
        )
        
        dialog.format_secondary_text(f"Enter name for copy of '{self.selected_grading.name}':")
        
        # Add entry for new name
        content_area = dialog.get_content_area()
        entry = Gtk.Entry()
        entry.set_text(f"Copy of {self.selected_grading.name}")
        entry.select_region(0, -1)  # Select all text
        content_area.pack_start(entry, False, False, 10)
        content_area.show_all()
        
        response = dialog.run()
        new_name = entry.get_text().strip()
        dialog.destroy()
        
        if response == Gtk.ResponseType.OK and new_name:
            try:
                # Create duplicate
                duplicate = self.grading_service.duplicate_grading(
                    self.selected_grading.name, new_name
                )
                
                self._update_status(f"Created duplicate: {new_name}")
                self._load_gradings()  # Refresh list
                
            except Exception as e:
                self._show_error("Duplication Failed", str(e))
    
    def _on_export_clicked(self, button):
        """Handle Export button click."""
        if not self.selected_grading:
            return
            
        # File chooser for export location
        dialog = Gtk.FileChooserDialog(
            title="Export Grading Template",
            parent=self,
            action=Gtk.FileChooserAction.SAVE
        )
        
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_SAVE, Gtk.ResponseType.OK
        )
        
        # Set default filename
        default_name = f"{self.selected_grading.name}.gdg"
        dialog.set_current_name(default_name)
        
        # Add file filter
        filter_gdg = Gtk.FileFilter()
        filter_gdg.set_name("Grading files (*.gdg)")
        filter_gdg.add_pattern("*.gdg")
        dialog.add_filter(filter_gdg)
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            try:
                # Export to file
                sieve_data = self.selected_grading.get_sieve_data()
                if sieve_data:
                    # Write directly to chosen location
                    import os
                    file_dir = os.path.dirname(filename)
                    file_base = os.path.splitext(os.path.basename(filename))[0]
                    
                    file_path = grading_file_manager.write_gdg_file(
                        file_dir, file_base, sieve_data, 
                        self.selected_grading.type.value.lower() if self.selected_grading.type else None
                    )
                    
                    self._update_status(f"Exported to: {file_path}")
                else:
                    self._show_error("Export Failed", "No sieve data to export")
                    
            except Exception as e:
                self._show_error("Export Failed", str(e))
        
        dialog.destroy()
    
    def _on_import_clicked(self, button):
        """Handle Import button click."""
        # File chooser for import
        dialog = Gtk.FileChooserDialog(
            title="Import Grading Template",
            parent=self,
            action=Gtk.FileChooserAction.OPEN
        )
        
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )
        
        # Add file filter
        filter_gdg = Gtk.FileFilter()
        filter_gdg.set_name("Grading files (*.gdg)")
        filter_gdg.add_pattern("*.gdg")
        dialog.add_filter(filter_gdg)
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            try:
                # Read grading data
                sieve_data = grading_file_manager.read_gdg_file(filename)
                
                # Show dialog to get grading details
                import_dialog = self._show_import_details_dialog(filename, sieve_data)
                
            except Exception as e:
                self._show_error("Import Failed", str(e))
        
        dialog.destroy()
    
    def _show_import_details_dialog(self, filename: str, sieve_data: List[Dict[str, float]]):
        """Show dialog to get details for imported grading."""
        import os
        
        dialog = Gtk.Dialog(
            title="Import Grading Details",
            parent=self,
            flags=Gtk.DialogFlags.MODAL
        )
        
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK, Gtk.ResponseType.OK
        )
        
        content_area = dialog.get_content_area()
        content_area.set_spacing(10)
        content_area.set_margin_left(20)
        content_area.set_margin_right(20)
        content_area.set_margin_top(10)
        content_area.set_margin_bottom(10)
        
        # Info label
        info_text = f"Importing grading from: {os.path.basename(filename)}\n"
        info_text += f"Found {len(sieve_data)} sieve points"
        info_label = Gtk.Label(info_text)
        content_area.pack_start(info_label, False, False, 0)
        
        # Name entry
        grid = Gtk.Grid()
        grid.set_column_spacing(10)
        grid.set_row_spacing(5)
        content_area.pack_start(grid, False, False, 0)
        
        # Default name from filename
        default_name = os.path.splitext(os.path.basename(filename))[0]
        
        grid.attach(Gtk.Label("Name:"), 0, 0, 1, 1)
        name_entry = Gtk.Entry()
        name_entry.set_text(default_name)
        grid.attach(name_entry, 1, 0, 1, 1)
        
        # Type combo
        grid.attach(Gtk.Label("Type:"), 0, 1, 1, 1)
        type_combo = Gtk.ComboBoxText()
        type_combo.append("FINE", "Fine Aggregate")
        type_combo.append("COARSE", "Coarse Aggregate")
        type_combo.set_active_id("FINE")
        grid.attach(type_combo, 1, 1, 1, 1)
        
        # Description entry
        grid.attach(Gtk.Label("Description:"), 0, 2, 1, 1)
        desc_entry = Gtk.Entry()
        desc_entry.set_text(f"Imported from {os.path.basename(filename)}")
        grid.attach(desc_entry, 1, 2, 1, 1)
        
        content_area.show_all()
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            try:
                name = name_entry.get_text().strip()
                grading_type = type_combo.get_active_id()
                description = desc_entry.get_text().strip()
                
                if not name:
                    raise ValueError("Name is required")
                
                # Create grading
                imported_grading = self.grading_service.save_grading_with_sieve_data(
                    name, grading_type, sieve_data, description
                )
                
                self._update_status(f"Imported: {imported_grading.name}")
                self._load_gradings()  # Refresh list
                
            except Exception as e:
                self._show_error("Import Failed", str(e))
        
        dialog.destroy()
    
    def _on_delete_clicked(self, button):
        """Handle Delete button click."""
        selection = self.tree_view.get_selection()
        model, paths = selection.get_selected_rows()
        
        if not paths:
            return
        
        # Get selected grading names
        grading_names = []
        for path in paths:
            iter = model.get_iter(path)
            grading = model.get_value(iter, 7)
            grading_names.append(grading.name)
        
        # Confirmation dialog
        if len(grading_names) == 1:
            message = f"Delete grading template '{grading_names[0]}'?"
            secondary = "This action cannot be undone."
        else:
            message = f"Delete {len(grading_names)} grading templates?"
            secondary = "This action cannot be undone."
        
        dialog = Gtk.MessageDialog(
            parent=self,
            flags=Gtk.DialogFlags.MODAL,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.YES_NO,
            text=message
        )
        dialog.format_secondary_text(secondary)
        
        response = dialog.run()
        dialog.destroy()
        
        if response == Gtk.ResponseType.YES:
            try:
                # Delete selected gradings
                deleted_count = 0
                for name in grading_names:
                    try:
                        self.grading_service.delete(name)
                        deleted_count += 1
                    except Exception as e:
                        self.logger.error(f"Failed to delete {name}: {e}")
                
                self._update_status(f"Deleted {deleted_count} template(s)")
                self._load_gradings()  # Refresh list
                
            except Exception as e:
                self._show_error("Deletion Failed", str(e))
    
    def _on_response(self, dialog, response_id):
        """Handle dialog responses."""
        if response_id == Gtk.ResponseType.OK:
            # Load button was pressed or row double-clicked
            pass
        elif response_id == Gtk.ResponseType.CLOSE:
            pass
    
    def _show_error(self, title: str, message: str):
        """Show error dialog."""
        dialog = Gtk.MessageDialog(
            parent=self,
            flags=Gtk.DialogFlags.MODAL,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=title
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()
    
    def get_selected_grading(self) -> Optional[Grading]:
        """Get the currently selected grading."""
        return self.selected_grading
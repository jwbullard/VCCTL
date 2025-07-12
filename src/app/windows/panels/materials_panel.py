#!/usr/bin/env python3
"""
Materials Management Panel for VCCTL

Provides comprehensive materials management interface with tabbed views for different material types.
"""

import gi
import logging
from typing import TYPE_CHECKING, Optional, Dict, Any, List

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, Pango

if TYPE_CHECKING:
    from app.windows.main_window import VCCTLMainWindow

from app.services.service_container import get_service_container
from app.windows.dialogs import create_material_dialog
from app.widgets import MaterialTable


class MaterialsPanel(Gtk.Box):
    """Main materials management panel with tabbed interface for different material types."""
    
    def __init__(self, main_window: 'VCCTLMainWindow'):
        """Initialize the materials panel."""
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        self.main_window = main_window
        self.logger = logging.getLogger('VCCTL.MaterialsPanel')
        self.service_container = get_service_container()
        
        # Panel state
        self.current_material_type = None
        self.search_active = False
        self.filter_active = False
        
        # Setup UI
        self._setup_ui()
        
        # Connect signals
        self._connect_signals()
        
        self.logger.info("Materials panel initialized")
    
    def _setup_ui(self) -> None:
        """Setup the materials panel UI."""
        # Create header section
        self._create_header()
        
        # Create main content with material type tabs
        self._create_content_area()
        
        # Load initial data
        self._load_initial_data()
    
    def _create_header(self) -> None:
        """Create the panel header with search and controls."""
        header_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        header_box.set_margin_top(10)
        header_box.set_margin_bottom(10)
        header_box.set_margin_left(15)
        header_box.set_margin_right(15)
        
        # Title and description
        title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        title_label = Gtk.Label()
        title_label.set_markup('<span size="large" weight="bold">Materials Management</span>')
        title_label.set_halign(Gtk.Align.START)
        title_box.pack_start(title_label, False, False, 0)
        
        # Material count indicator
        self.material_count_label = Gtk.Label()
        self.material_count_label.set_markup('<span size="small" style="italic">Loading...</span>')
        self.material_count_label.set_halign(Gtk.Align.END)
        title_box.pack_end(self.material_count_label, False, False, 0)
        
        header_box.pack_start(title_box, False, False, 0)
        
        # Description
        desc_label = Gtk.Label()
        desc_label.set_markup('<span size="small">Manage cement, aggregates, and supplementary materials for concrete mix design</span>')
        desc_label.set_halign(Gtk.Align.START)
        header_box.pack_start(desc_label, False, False, 0)
        
        # Search and filter controls
        controls_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        # Search entry
        search_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        search_icon = Gtk.Image.new_from_icon_name("edit-find-symbolic", Gtk.IconSize.BUTTON)
        search_box.pack_start(search_icon, False, False, 0)
        
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Search materials by name, type, or properties...")
        self.search_entry.set_size_request(300, -1)
        search_box.pack_start(self.search_entry, True, True, 0)
        
        controls_box.pack_start(search_box, True, True, 0)
        
        # Filter button
        self.filter_button = Gtk.ToggleButton(label="Filters")
        filter_icon = Gtk.Image.new_from_icon_name("preferences-system-symbolic", Gtk.IconSize.BUTTON)
        self.filter_button.set_image(filter_icon)
        self.filter_button.set_always_show_image(True)
        controls_box.pack_start(self.filter_button, False, False, 0)
        
        # Add material button
        self.add_button = Gtk.Button(label="Add Material")
        add_icon = Gtk.Image.new_from_icon_name("list-add-symbolic", Gtk.IconSize.BUTTON)
        self.add_button.set_image(add_icon)
        self.add_button.set_always_show_image(True)
        self.add_button.get_style_context().add_class("suggested-action")
        controls_box.pack_start(self.add_button, False, False, 0)
        
        # Import/Export buttons
        io_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        io_box.get_style_context().add_class("linked")
        
        self.import_button = Gtk.Button(label="Import")
        import_icon = Gtk.Image.new_from_icon_name("document-open-symbolic", Gtk.IconSize.BUTTON)
        self.import_button.set_image(import_icon)
        self.import_button.set_always_show_image(True)
        self.import_button.set_tooltip_text("Import materials from file")
        io_box.pack_start(self.import_button, False, False, 0)
        
        self.export_button = Gtk.Button(label="Export")
        export_icon = Gtk.Image.new_from_icon_name("document-save-symbolic", Gtk.IconSize.BUTTON)
        self.export_button.set_image(export_icon)
        self.export_button.set_always_show_image(True)
        self.export_button.set_tooltip_text("Export materials to file")
        io_box.pack_start(self.export_button, False, False, 0)
        
        controls_box.pack_start(io_box, False, False, 0)
        
        header_box.pack_start(controls_box, False, False, 0)
        
        # Filter panel (initially hidden)
        self._create_filter_panel(header_box)
        
        self.pack_start(header_box, False, False, 0)
    
    def _create_filter_panel(self, parent: Gtk.Box) -> None:
        """Create the filter panel."""
        self.filter_revealer = Gtk.Revealer()
        self.filter_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)
        
        filter_frame = Gtk.Frame()
        filter_frame.get_style_context().add_class("view")
        
        filter_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=15)
        filter_box.set_margin_top(10)
        filter_box.set_margin_bottom(10)
        filter_box.set_margin_left(15)
        filter_box.set_margin_right(15)
        
        # Material type filter
        type_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        type_label = Gtk.Label("Material Type:")
        type_label.set_halign(Gtk.Align.START)
        type_box.pack_start(type_label, False, False, 0)
        
        self.type_combo = Gtk.ComboBoxText()
        self.type_combo.append("all", "All Types")
        self.type_combo.append("cement", "Cement")
        self.type_combo.append("aggregate", "Aggregate")
        self.type_combo.append("fly_ash", "Fly Ash")
        self.type_combo.append("slag", "Slag")
        self.type_combo.append("inert_filler", "Inert Filler")
        self.type_combo.set_active(0)
        type_box.pack_start(self.type_combo, False, False, 0)
        
        filter_box.pack_start(type_box, False, False, 0)
        
        # Specific gravity range
        sg_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        sg_label = Gtk.Label("Specific Gravity Range:")
        sg_label.set_halign(Gtk.Align.START)
        sg_box.pack_start(sg_label, False, False, 0)
        
        sg_range_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.sg_min_spin = Gtk.SpinButton.new_with_range(1.0, 5.0, 0.1)
        self.sg_min_spin.set_value(2.0)
        sg_range_box.pack_start(self.sg_min_spin, False, False, 0)
        
        sg_range_box.pack_start(Gtk.Label("to"), False, False, 0)
        
        self.sg_max_spin = Gtk.SpinButton.new_with_range(1.0, 5.0, 0.1)
        self.sg_max_spin.set_value(4.0)
        sg_range_box.pack_start(self.sg_max_spin, False, False, 0)
        
        sg_box.pack_start(sg_range_box, False, False, 0)
        filter_box.pack_start(sg_box, False, False, 0)
        
        # Clear filters button
        clear_button = Gtk.Button(label="Clear Filters")
        clear_button.connect('clicked', self._on_clear_filters_clicked)
        filter_box.pack_end(clear_button, False, False, 0)
        
        filter_frame.add(filter_box)
        self.filter_revealer.add(filter_frame)
        parent.pack_start(self.filter_revealer, False, False, 0)
    
    def _create_content_area(self) -> None:
        """Create the main content area with material table."""
        # Create main content container
        content_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        
        # Create material table
        self.material_table = MaterialTable(self.main_window)
        self.material_table.connect('material-selected', self._on_material_selected)
        self.material_table.connect('material-activated', self._on_material_activated)
        self.material_table.connect('materials-changed', self._on_materials_changed)
        
        content_box.pack_start(self.material_table, True, True, 0)
        
        # Create details panel (initially hidden)
        self._create_details_panel(content_box)
        
        self.pack_start(content_box, True, True, 0)
    
    def _create_details_panel(self, parent: Gtk.Box) -> None:
        """Create the material details panel."""
        # Create revealer for details panel
        self.details_revealer = Gtk.Revealer()
        self.details_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_LEFT)
        self.details_revealer.set_transition_duration(200)
        
        # Details panel container
        details_frame = Gtk.Frame()
        details_frame.set_size_request(300, -1)
        details_frame.get_style_context().add_class("view")
        
        # Details content
        details_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        details_box.set_margin_top(15)
        details_box.set_margin_bottom(15)
        details_box.set_margin_left(15)
        details_box.set_margin_right(15)
        
        # Details header
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        self.details_title = Gtk.Label()
        self.details_title.set_markup('<span size="large" weight="bold">Material Details</span>')
        self.details_title.set_halign(Gtk.Align.START)
        header_box.pack_start(self.details_title, True, True, 0)
        
        # Close button
        close_button = Gtk.Button()
        close_icon = Gtk.Image.new_from_icon_name("window-close-symbolic", Gtk.IconSize.BUTTON)
        close_button.set_image(close_icon)
        close_button.set_relief(Gtk.ReliefStyle.NONE)
        close_button.connect('clicked', self._on_close_details_clicked)
        header_box.pack_start(close_button, False, False, 0)
        
        details_box.pack_start(header_box, False, False, 0)
        
        # Separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        details_box.pack_start(separator, False, False, 0)
        
        # Details content (scrollable)
        details_scrolled = Gtk.ScrolledWindow()
        details_scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        self.details_content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        details_scrolled.add(self.details_content)
        
        details_box.pack_start(details_scrolled, True, True, 0)
        
        # Action buttons
        action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        action_box.get_style_context().add_class("linked")
        
        self.edit_button = Gtk.Button(label="Edit")
        edit_icon = Gtk.Image.new_from_icon_name("document-edit-symbolic", Gtk.IconSize.BUTTON)
        self.edit_button.set_image(edit_icon)
        self.edit_button.set_always_show_image(True)
        self.edit_button.get_style_context().add_class("suggested-action")
        action_box.pack_start(self.edit_button, True, True, 0)
        
        self.duplicate_button = Gtk.Button(label="Duplicate")
        duplicate_icon = Gtk.Image.new_from_icon_name("edit-copy-symbolic", Gtk.IconSize.BUTTON)
        self.duplicate_button.set_image(duplicate_icon)
        self.duplicate_button.set_always_show_image(True)
        action_box.pack_start(self.duplicate_button, True, True, 0)
        
        self.delete_button = Gtk.Button(label="Delete")
        delete_icon = Gtk.Image.new_from_icon_name("edit-delete-symbolic", Gtk.IconSize.BUTTON)
        self.delete_button.set_image(delete_icon)
        self.delete_button.set_always_show_image(True)
        self.delete_button.get_style_context().add_class("destructive-action")
        action_box.pack_start(self.delete_button, True, True, 0)
        
        details_box.pack_start(action_box, False, False, 0)
        
        details_frame.add(details_box)
        self.details_revealer.add(details_frame)
        parent.pack_start(self.details_revealer, False, False, 0)
        
        # Store selected material
        self.selected_material = None
    
    def _load_initial_data(self) -> None:
        """Load initial data into the materials table."""
        try:
            # Get material counts for display
            service_container = get_service_container()
            
            total_materials = 0
            
            # Count cement materials
            try:
                cement_count = len(service_container.cement_service.get_all())
                total_materials += cement_count
            except Exception as e:
                self.logger.warning(f"Error counting cement materials: {e}")
                cement_count = 0
            
            # Count aggregate materials
            try:
                aggregate_count = len(service_container.aggregate_service.get_all())
                total_materials += aggregate_count
            except Exception as e:
                self.logger.warning(f"Error counting aggregate materials: {e}")
                aggregate_count = 0
            
            # Update material count display
            self.material_count_label.set_markup(
                f'<span size="small" style="italic">{total_materials} materials total</span>'
            )
            
            self.logger.info(f"Loaded material counts: {cement_count} cement, {aggregate_count} aggregate")
            
        except Exception as e:
            self.logger.error(f"Error loading initial data: {e}")
            self.material_count_label.set_markup(
                '<span size="small" style="italic">Error loading materials</span>'
            )
    
    def _connect_signals(self) -> None:
        """Connect widget signals."""
        # Header controls
        self.search_entry.connect('search-changed', self._on_search_changed)
        self.filter_button.connect('toggled', self._on_filter_toggled)
        self.add_button.connect('clicked', self._on_add_material_clicked)
        self.import_button.connect('clicked', self._on_import_clicked)
        self.export_button.connect('clicked', self._on_export_clicked)
        
        # Filter controls
        self.type_combo.connect('changed', self._on_filter_changed)
        self.sg_min_spin.connect('value-changed', self._on_filter_changed)
        self.sg_max_spin.connect('value-changed', self._on_filter_changed)
        
        # Details panel
        self.edit_button.connect('clicked', self._on_edit_material_clicked)
        self.duplicate_button.connect('clicked', self._on_duplicate_material_clicked)
        self.delete_button.connect('clicked', self._on_delete_material_clicked)
    
    # Signal handlers
    def _on_search_changed(self, entry) -> None:
        """Handle search entry changes."""
        search_text = entry.get_text()
        self.material_table.apply_filters({'text': search_text})
    
    def _on_filter_toggled(self, button) -> None:
        """Handle filter button toggle."""
        self.filter_revealer.set_reveal_child(button.get_active())
    
    def _on_filter_changed(self, widget) -> None:
        """Handle filter control changes."""
        filters = {
            'type': self.type_combo.get_active_id(),
            'sg_min': self.sg_min_spin.get_value(),
            'sg_max': self.sg_max_spin.get_value()
        }
        self.material_table.apply_filters(filters)
    
    def _on_clear_filters_clicked(self, button) -> None:
        """Handle clear filters button click."""
        # Reset filter controls
        self.type_combo.set_active(0)
        self.sg_min_spin.set_value(1.0)
        self.sg_max_spin.set_value(5.0)
        self.search_entry.set_text("")
        
        # Clear table filters
        self.material_table.clear_filters()
    
    def _on_add_material_clicked(self, button) -> None:
        """Handle add material button click."""
        # Show material type selection dialog
        dialog = Gtk.Dialog(
            title="Add Material",
            transient_for=self.main_window,
            flags=0
        )
        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        dialog.add_button("Add", Gtk.ResponseType.OK)
        dialog.set_default_response(Gtk.ResponseType.OK)
        
        content_area = dialog.get_content_area()
        content_area.set_spacing(10)
        content_area.set_margin_top(20)
        content_area.set_margin_bottom(20)
        content_area.set_margin_left(20)
        content_area.set_margin_right(20)
        
        # Material type selection
        type_label = Gtk.Label("Select material type:")
        type_label.set_halign(Gtk.Align.START)
        content_area.pack_start(type_label, False, False, 0)
        
        type_combo = Gtk.ComboBoxText()
        type_combo.append("cement", "Cement")
        type_combo.append("aggregate", "Aggregate")
        type_combo.append("fly_ash", "Fly Ash")
        type_combo.append("slag", "Slag")
        type_combo.append("inert_filler", "Inert Filler")
        type_combo.set_active(0)
        content_area.pack_start(type_combo, False, False, 0)
        
        content_area.show_all()
        
        response = dialog.run()
        material_type = type_combo.get_active_id()
        dialog.destroy()
        
        if response == Gtk.ResponseType.OK and material_type:
            self._show_material_dialog(material_type)
    
    def _on_import_clicked(self, button) -> None:
        """Handle import button click."""
        # TODO: Implement material import
        self.main_window.update_status("Material import functionality will be implemented", "info", 3)
    
    def _on_export_clicked(self, button) -> None:
        """Handle export button click."""
        # Use the table's export functionality
        selected_materials = self.material_table.get_selected_materials()
        if selected_materials:
            # Export selected materials
            pass  # The table handles this
        else:
            # Export all materials
            self.main_window.update_status("Export all materials functionality will be implemented", "info", 3)
    
    def _on_material_selected(self, table, material_data) -> None:
        """Handle material selection from table."""
        self.selected_material = material_data
        self._update_details_panel(material_data)
        self.details_revealer.set_reveal_child(True)
    
    def _on_material_activated(self, table, material_data) -> None:
        """Handle material activation (double-click) from table."""
        self._show_material_dialog(material_data.material_type, material_data)
    
    def _on_materials_changed(self, table) -> None:
        """Handle materials data change."""
        self._load_initial_data()
    
    def _on_close_details_clicked(self, button) -> None:
        """Handle close details button click."""
        self.details_revealer.set_reveal_child(False)
        self.selected_material = None
    
    def _on_edit_material_clicked(self, button) -> None:
        """Handle edit material button click."""
        if self.selected_material:
            material_type = getattr(self.selected_material, 'material_type', 'cement')
            self._show_material_dialog(material_type, self.selected_material)
    
    def _on_duplicate_material_clicked(self, button) -> None:
        """Handle duplicate material button click."""
        # TODO: Implement material duplication
        self.main_window.update_status("Material duplication will be implemented", "info", 3)
    
    def _on_delete_material_clicked(self, button) -> None:
        """Handle delete material button click."""
        if not self.selected_material:
            return
        
        # Show confirmation dialog
        dialog = Gtk.MessageDialog(
            transient_for=self.main_window,
            flags=0,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.YES_NO,
            text=f"Delete material '{self.selected_material.name}'?"
        )
        dialog.format_secondary_text("This action cannot be undone.")
        
        response = dialog.run()
        dialog.destroy()
        
        if response == Gtk.ResponseType.YES:
            self._delete_material(self.selected_material)
    
    def _update_details_panel(self, material_data) -> None:
        """Update the details panel with material information."""
        # Clear existing content
        for child in self.details_content.get_children():
            self.details_content.remove(child)
        
        if not material_data:
            return
        
        # Material name and type
        name_label = Gtk.Label()
        name_label.set_markup(f'<span size="large" weight="bold">{material_data.name}</span>')
        name_label.set_halign(Gtk.Align.START)
        self.details_content.pack_start(name_label, False, False, 0)
        
        type_label = Gtk.Label()
        material_type = getattr(material_data, 'material_type', 'Unknown')
        type_label.set_markup(f'<span style="italic">{material_type.replace("_", " ").title()}</span>')
        type_label.set_halign(Gtk.Align.START)
        self.details_content.pack_start(type_label, False, False, 0)
        
        # Separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.details_content.pack_start(separator, False, False, 0)
        
        # Properties grid
        props_grid = Gtk.Grid()
        props_grid.set_row_spacing(5)
        props_grid.set_column_spacing(10)
        
        row = 0
        
        # Common properties
        if hasattr(material_data, 'specific_gravity'):
            self._add_property_row(props_grid, row, "Specific Gravity:", f"{material_data.specific_gravity:.3f}")
            row += 1
        
        if hasattr(material_data, 'description') and material_data.description:
            self._add_property_row(props_grid, row, "Description:", material_data.description)
            row += 1
        
        if hasattr(material_data, 'created_date') and material_data.created_date:
            date_str = material_data.created_date.strftime('%Y-%m-%d')
            self._add_property_row(props_grid, row, "Created:", date_str)
            row += 1
        
        self.details_content.pack_start(props_grid, False, False, 0)
        self.details_content.show_all()
    
    def _add_property_row(self, grid: Gtk.Grid, row: int, label_text: str, value_text: str) -> None:
        """Add a property row to the grid."""
        label = Gtk.Label(label_text)
        label.set_halign(Gtk.Align.END)
        label.get_style_context().add_class("dim-label")
        grid.attach(label, 0, row, 1, 1)
        
        value = Gtk.Label(value_text)
        value.set_halign(Gtk.Align.START)
        value.set_line_wrap(True)
        value.set_max_width_chars(30)
        grid.attach(value, 1, row, 1, 1)
    
    def _show_material_dialog(self, material_type: str, material_data=None) -> None:
        """Show the material dialog for adding or editing."""
        try:
            # Create and show material dialog
            dialog = create_material_dialog(self.main_window, material_type, material_data)
            
            response = dialog.run()
            
            if response == Gtk.ResponseType.OK:
                # Material was saved, refresh the table
                self.material_table.refresh_data()
                self._load_initial_data()
                self.main_window.update_status(f"Material {'updated' if material_data else 'created'} successfully", "success", 3)
            
            dialog.destroy()
            
        except Exception as e:
            self.logger.error(f"Error showing material dialog: {e}")
            self.main_window.update_status(f"Error opening material dialog: {e}", "error", 5)
    
    def _delete_material(self, material_data) -> None:
        """Delete a material."""
        try:
            material_type = getattr(material_data, 'material_type', 'cement')
            
            # Get appropriate service
            service_container = get_service_container()
            if material_type == 'cement':
                service = service_container.cement_service
            elif material_type == 'aggregate':
                service = service_container.aggregate_service
            else:
                raise ValueError(f"Unsupported material type: {material_type}")
            
            # Delete the material
            service.delete(material_data.id)
            
            # Refresh data
            self.material_table.refresh_data()
            self._load_initial_data()
            self.details_revealer.set_reveal_child(False)
            self.selected_material = None
            
            self.main_window.update_status(f"Material '{material_data.name}' deleted successfully", "success", 3)
            
        except Exception as e:
            self.logger.error(f"Error deleting material: {e}")
            self.main_window.update_status(f"Error deleting material: {e}", "error", 5)
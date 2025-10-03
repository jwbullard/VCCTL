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
from app.utils.icon_utils import create_icon_image
from app.help.panel_help_button import create_panel_help_button

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
    
    def _create_fallback_panel(self, error_message: str) -> None:
        """Create a simple fallback panel when the main panel fails."""
        fallback_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        fallback_box.set_margin_top(50)
        fallback_box.set_margin_bottom(50)
        fallback_box.set_margin_left(50)
        fallback_box.set_margin_right(50)
        
        error_label = Gtk.Label()
        error_label.set_markup(f'<span size="large" weight="bold">Materials Panel - Safe Mode</span>')
        error_label.set_halign(Gtk.Align.CENTER)
        fallback_box.pack_start(error_label, False, False, 0)
        
        message_label = Gtk.Label(error_message)
        message_label.set_halign(Gtk.Align.CENTER)
        message_label.set_line_wrap(True)
        fallback_box.pack_start(message_label, False, False, 0)
        
        self.pack_start(fallback_box, True, True, 0)
    
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

        # Add context-specific help button
        help_button = create_panel_help_button('MaterialsPanel', self.main_window)
        title_box.pack_start(help_button, False, False, 5)

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
        search_icon = create_icon_image("search", 16)
        search_box.pack_start(search_icon, False, False, 0)
        
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Search materials by name, type, or properties...")
        self.search_entry.set_size_request(200, -1)  # Reduced from 300 to allow narrower windows
        search_box.pack_start(self.search_entry, True, True, 0)
        
        controls_box.pack_start(search_box, True, True, 0)
        
        # Filter button
        self.filter_button = Gtk.ToggleButton(label="Filters")
        filter_icon = create_icon_image("settings", 16)
        self.filter_button.set_image(filter_icon)
        self.filter_button.set_always_show_image(True)
        controls_box.pack_start(self.filter_button, False, False, 0)
        
        # Add material button
        self.add_button = Gtk.Button(label="Add Material")
        add_icon = create_icon_image("add", 16)
        self.add_button.set_image(add_icon)
        self.add_button.set_always_show_image(True)
        self.add_button.get_style_context().add_class("suggested-action")
        controls_box.pack_start(self.add_button, False, False, 0)
        
        # Import/Export buttons
        io_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        io_box.get_style_context().add_class("linked")
        
        self.import_button = Gtk.Button(label="Import")
        import_icon = create_icon_image("folder--open", 16)
        self.import_button.set_image(import_icon)
        self.import_button.set_always_show_image(True)
        self.import_button.set_tooltip_text("Import materials from file")
        io_box.pack_start(self.import_button, False, False, 0)
        
        self.export_button = Gtk.Button(label="Export")
        export_icon = create_icon_image("save", 16)
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
        self.type_combo.append("filler", "Filler")
        self.type_combo.append("silica_fume", "Silica Fume")
        self.type_combo.append("limestone", "Limestone")
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
        close_icon = create_icon_image("close", 16)
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
        edit_icon = create_icon_image("edit", 16)
        self.edit_button.set_image(edit_icon)
        self.edit_button.set_always_show_image(True)
        self.edit_button.get_style_context().add_class("suggested-action")
        action_box.pack_start(self.edit_button, True, True, 0)
        
        self.duplicate_button = Gtk.Button(label="Duplicate")
        duplicate_icon = create_icon_image("copy", 16)
        self.duplicate_button.set_image(duplicate_icon)
        self.duplicate_button.set_always_show_image(True)
        action_box.pack_start(self.duplicate_button, True, True, 0)
        
        self.delete_button = Gtk.Button(label="Delete")
        delete_icon = create_icon_image("delete", 16)
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
        type_combo.append("filler", "Filler")
        type_combo.append("silica_fume", "Silica Fume")
        type_combo.append("limestone", "Limestone")
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
        self.logger.debug(f"Material selected: {getattr(material_data, 'name', 'Unknown')} (type: {type(material_data)})")
        self.selected_material = material_data
        self._update_details_panel(material_data)
        self.details_revealer.set_reveal_child(True)
    
    def _on_material_activated(self, table, material_data) -> None:
        """Handle material activation (double-click) from table."""
        material_type = self._get_material_type(material_data)
        self._show_material_dialog(material_type, material_data)
    
    def _on_materials_changed(self, table) -> None:
        """Handle materials data change."""
        self._load_initial_data()
    
    def _on_close_details_clicked(self, button) -> None:
        """Handle close details button click."""
        self.details_revealer.set_reveal_child(False)
        self.selected_material = None
    
    def _get_service_for_type(self, material_type: str):
        """Get the appropriate service for a material type."""
        service_container = get_service_container()
        service_map = {
            'cement': service_container.cement_service,
            'filler': service_container.filler_service,
            'aggregate': service_container.aggregate_service,
            'fly_ash': service_container.fly_ash_service,
            'slag': service_container.slag_service,
            'silica_fume': service_container.silica_fume_service,
            'limestone': service_container.limestone_service
        }
        return service_map.get(material_type)
    
    def _on_edit_material_clicked(self, button) -> None:
        """Handle edit material button click."""
        if self.selected_material:
            material_type = self._get_material_type(self.selected_material)
            
            # Re-fetch the material to get fresh data from database
            service = self._get_service_for_type(material_type)
            if service:
                try:
                    # Get fresh material data by name or id
                    if material_type == 'cement':
                        fresh_material = service.get_by_name(self.selected_material.name)
                    elif material_type == 'aggregate':
                        # Aggregate uses display_name as primary key
                        with service.db_service.get_read_only_session() as session:
                            fresh_material = session.query(service.model).filter_by(display_name=self.selected_material.display_name).first()
                    else:
                        # Other materials with integer IDs
                        fresh_material = service.get_by_name(self.selected_material.name)
                    
                    if fresh_material:
                        self._show_material_dialog(material_type, fresh_material)
                    else:
                        self.logger.error(f"Could not re-fetch material for editing")
                        self._show_material_dialog(material_type, self.selected_material)
                except Exception as e:
                    self.logger.error(f"Error re-fetching material: {e}")
                    # Fall back to using the cached material
                    self._show_material_dialog(material_type, self.selected_material)
            else:
                self._show_material_dialog(material_type, self.selected_material)
    
    def _on_duplicate_material_clicked(self, button) -> None:
        """Handle duplicate material button click."""
        if not self.selected_material:
            return
        
        try:
            # Get the material type to determine how to duplicate
            material_type = self._get_material_type(self.selected_material)
            
            # Create a copy of the material with a new name
            self._duplicate_material(self.selected_material, material_type)
            
        except Exception as e:
            self.logger.error(f"Error duplicating material: {e}")
            self.main_window.update_status(f"Error duplicating material: {e}", "error", 5)
    
    def _on_delete_material_clicked(self, button) -> None:
        """Handle delete material button click."""
        self.logger.info(f"Delete button clicked. Selected material: {self.selected_material}")
        if not self.selected_material:
            self.logger.warning("No material selected for deletion")
            self.main_window.update_status("No material selected for deletion", "warning", 3)
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
        
        self.logger.info(f"Delete confirmation dialog response: {response}")
        if response == Gtk.ResponseType.YES:
            self.logger.info(f"User confirmed deletion, calling _delete_material for: {self.selected_material.name}")
            self._delete_material(self.selected_material)
        else:
            self.logger.info("User cancelled deletion")
    
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
        material_type = self._get_material_type(material_data)
        type_label.set_markup(f'<span style="italic">{material_type.replace("_", " ").title()}</span>')
        type_label.set_halign(Gtk.Align.START)
        self.details_content.pack_start(type_label, False, False, 0)
        
        # Separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.details_content.pack_start(separator, False, False, 0)
        
        # Use ultra-simple display to isolate crash issue
        try:
            # Just show name and type for now
            name_grid = Gtk.Grid()
            name_grid.set_row_spacing(5)
            name_grid.set_column_spacing(10)
            
            row = 0
            
            # Material name
            try:
                name = getattr(material_data, 'name', 'Unknown')
                self._add_property_row(name_grid, row, "Name:", str(name))
                row += 1
            except Exception:
                pass
            
            # Material type
            try:
                material_type = self._get_material_type(material_data)
                self._add_property_row(name_grid, row, "Type:", material_type)
                row += 1
            except Exception:
                pass
            
            # Specific gravity
            try:
                if hasattr(material_data, 'specific_gravity'):
                    sg = getattr(material_data, 'specific_gravity', 'N/A')
                    self._add_property_row(name_grid, row, "Specific Gravity:", str(sg))
                    row += 1
            except Exception:
                pass
            
            # Add cement-specific information if it's a cement
            if hasattr(material_data, '__tablename__') and material_data.__tablename__ == 'cement':
                try:
                    # Particle size distribution
                    if hasattr(material_data, 'psd_data_id') and material_data.psd_data_id:
                        self._add_property_row(name_grid, row, "PSD Data ID:", str(material_data.psd_data_id))
                        row += 1
                except Exception:
                    pass
                
                try:
                    # Alkali file
                    if hasattr(material_data, 'alkali_file') and material_data.alkali_file:
                        self._add_property_row(name_grid, row, "Alkali File:", str(material_data.alkali_file))
                        row += 1
                except Exception:
                    pass
                
                # Description will be shown separately below due to length
                pass
                
                try:
                    # Binary data summary (safe counting)
                    binary_count = 0
                    binary_size = 0
                    binary_fields = ['pfc', 'gif', 'legend_gif', 'sil', 'c3s', 'c3a', 'n2o', 'k2o', 'alu', 'txt', 'xrd', 'inf', 'c4f']
                    
                    for field_name in binary_fields:
                        try:
                            if hasattr(material_data, field_name):
                                field_value = getattr(material_data, field_name)
                                if field_value is not None and len(field_value) > 0:
                                    binary_count += 1
                                    binary_size += len(field_value)
                        except Exception:
                            continue
                    
                    if binary_count > 0:
                        size_str = f"{binary_size / 1024:.1f} KB" if binary_size > 1024 else f"{binary_size} bytes"
                        self._add_property_row(name_grid, row, "Binary Data:", f"{binary_count} fields ({size_str})")
                        row += 1
                    else:
                        self._add_property_row(name_grid, row, "Binary Data:", "No data available")
                        row += 1
                except Exception:
                    self._add_property_row(name_grid, row, "Binary Data:", "Error accessing data")
                    row += 1
            
            self.details_content.pack_start(name_grid, False, False, 0)
            
            # Add full description for cement materials
            if hasattr(material_data, '__tablename__') and material_data.__tablename__ == 'cement':
                try:
                    self._add_full_cement_description(material_data)
                except Exception as e:
                    self.logger.warning(f"Error adding full description: {e}")
            
        except Exception as e:
            self.logger.error(f"Error in ultra-simple display: {e}")
            # Absolute fallback
            fallback_label = Gtk.Label("Material selected")
            fallback_label.set_halign(Gtk.Align.START)
            self.details_content.pack_start(fallback_label, False, False, 0)
        
        self.details_content.show_all()
    
    def _add_generic_material_details(self, material_data) -> None:
        """Add generic material details for non-cement materials."""
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
    
    def _add_minimal_details(self, material_data) -> None:
        """Add minimal material details as a fallback."""
        minimal_grid = Gtk.Grid()
        minimal_grid.set_row_spacing(5)
        minimal_grid.set_column_spacing(10)
        
        row = 0
        
        # Only show the most basic information
        try:
            if hasattr(material_data, 'name'):
                self._add_property_row(minimal_grid, row, "Name:", str(material_data.name))
                row += 1
        except Exception:
            pass
        
        try:
            if hasattr(material_data, 'specific_gravity'):
                self._add_property_row(minimal_grid, row, "Specific Gravity:", str(material_data.specific_gravity))
                row += 1
        except Exception:
            pass
        
        self.details_content.pack_start(minimal_grid, False, False, 0)
    
    def _add_simple_cement_details(self, cement_data) -> None:
        """Add simple cement details without complex UI elements that might crash."""
        try:
            # Single scrollable area with all cement properties
            cement_grid = Gtk.Grid()
            cement_grid.set_row_spacing(5)
            cement_grid.set_column_spacing(10)
            
            row = 0
            
            # Basic properties
            try:
                if hasattr(cement_data, 'specific_gravity') and cement_data.specific_gravity is not None:
                    self._add_property_row(cement_grid, row, "Specific Gravity:", f"{cement_data.specific_gravity:.3f}")
                    row += 1
            except Exception:
                pass
            
            try:
                if hasattr(cement_data, 'psd_data_id') and cement_data.psd_data_id:
                    self._add_property_row(cement_grid, row, "PSD Data ID:", str(cement_data.psd_data_id))
                    row += 1
            except Exception:
                pass
            
            try:
                if hasattr(cement_data, 'alkali_file') and cement_data.alkali_file:
                    self._add_property_row(cement_grid, row, "Alkali File:", str(cement_data.alkali_file))
                    row += 1
            except Exception:
                pass
            
            try:
                if hasattr(cement_data, 'description') and cement_data.description:
                    self._add_property_row(cement_grid, row, "Description:", str(cement_data.description))
                    row += 1
            except Exception:
                pass
            
            try:
                if hasattr(cement_data, 'density') and cement_data.density:
                    self._add_property_row(cement_grid, row, "Density:", f"{cement_data.density:.1f} kg/m³")
                    row += 1
            except Exception:
                pass
            
            # Add a separator for binary data
            try:
                separator_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
                separator_label = Gtk.Label()
                separator_label.set_markup('<span weight="bold">Binary Data Fields</span>')
                separator_label.set_halign(Gtk.Align.START)
                cement_grid.attach(separator_label, 0, row, 2, 1)
                row += 1
            except Exception:
                pass
            
            # Count binary fields safely
            try:
                binary_count = 0
                binary_size = 0
                binary_fields = ['pfc', 'gif', 'legend_gif', 'sil', 'c3s', 'c3a', 'n2o', 'k2o', 'alu', 'txt', 'xrd', 'inf', 'c4f']
                
                for field_name in binary_fields:
                    try:
                        if hasattr(cement_data, field_name):
                            field_value = getattr(cement_data, field_name)
                            if field_value is not None:
                                binary_count += 1
                                binary_size += len(field_value)
                    except Exception:
                        continue
                
                if binary_count > 0:
                    size_str = f"{binary_size / 1024:.1f} KB" if binary_size > 1024 else f"{binary_size} bytes"
                    self._add_property_row(cement_grid, row, "Binary Fields:", f"{binary_count} fields ({size_str} total)")
                    row += 1
                else:
                    self._add_property_row(cement_grid, row, "Binary Fields:", "No binary data")
                    row += 1
            except Exception:
                self._add_property_row(cement_grid, row, "Binary Fields:", "Error accessing binary data")
                row += 1
            
            self.details_content.pack_start(cement_grid, False, False, 0)
            
        except Exception as e:
            self.logger.error(f"Error in simple cement details: {e}")
            # Ultra-simple fallback
            simple_label = Gtk.Label(f"Cement: {getattr(cement_data, 'name', 'Unknown')}")
            simple_label.set_halign(Gtk.Align.START)
            self.details_content.pack_start(simple_label, False, False, 0)
    
    def _add_cement_details(self, cement_data) -> None:
        """Add detailed cement-specific information to the details panel."""
        try:
            # Create notebook for tabbed cement details
            notebook = Gtk.Notebook()
            notebook.set_tab_pos(Gtk.PositionType.TOP)
            
            # Always add Basic Properties Tab
            try:
                basic_box = self._create_basic_properties_tab(cement_data)
                notebook.append_page(basic_box, Gtk.Label("Basic"))
            except Exception as e:
                self.logger.error(f"Error creating basic properties tab: {e}")
                # Fallback to simple display
                self._add_generic_material_details(cement_data)
                return
            
            # Conditionally add other tabs with error handling
            try:
                if hasattr(cement_data, 'has_phase_data') and cement_data.has_phase_data:
                    phase_box = self._create_phase_composition_tab(cement_data)
                    notebook.append_page(phase_box, Gtk.Label("Phase Composition"))
            except Exception as e:
                self.logger.warning(f"Error creating phase composition tab: {e}")
            
            try:
                if hasattr(cement_data, 'has_gypsum_data') and cement_data.has_gypsum_data:
                    gypsum_box = self._create_gypsum_data_tab(cement_data)
                    notebook.append_page(gypsum_box, Gtk.Label("Gypsum"))
            except Exception as e:
                self.logger.warning(f"Error creating gypsum data tab: {e}")
            
            # Always try to add Binary Data Tab
            try:
                binary_box = self._create_binary_data_tab(cement_data)
                notebook.append_page(binary_box, Gtk.Label("Binary Data"))
            except Exception as e:
                self.logger.warning(f"Error creating binary data tab: {e}")
            
            self.details_content.pack_start(notebook, True, True, 0)
            
        except Exception as e:
            self.logger.error(f"Error creating cement details: {e}")
            # Fallback to generic display
            self._add_generic_material_details(cement_data)
    
    def _create_basic_properties_tab(self, cement_data) -> Gtk.Box:
        """Create basic properties tab for cement."""
        basic_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        basic_box.set_margin_top(10)
        basic_box.set_margin_bottom(10)
        basic_box.set_margin_left(10)
        basic_box.set_margin_right(10)
        
        basic_grid = Gtk.Grid()
        basic_grid.set_row_spacing(5)
        basic_grid.set_column_spacing(10)
        
        row = 0
        
        # Basic properties with safe attribute access
        try:
            if hasattr(cement_data, 'specific_gravity') and cement_data.specific_gravity is not None:
                self._add_property_row(basic_grid, row, "Specific Gravity:", f"{cement_data.specific_gravity:.3f}")
                row += 1
        except Exception as e:
            self.logger.warning(f"Error displaying specific gravity: {e}")
        
        try:
            if hasattr(cement_data, 'psd_data_id') and cement_data.psd_data_id:
                self._add_property_row(basic_grid, row, "PSD Data ID:", str(cement_data.psd_data_id))
                row += 1
        except Exception as e:
            self.logger.warning(f"Error displaying PSD: {e}")
        
        try:
            if hasattr(cement_data, 'alkali_file') and cement_data.alkali_file:
                self._add_property_row(basic_grid, row, "Alkali File:", str(cement_data.alkali_file))
                row += 1
        except Exception as e:
            self.logger.warning(f"Error displaying alkali file: {e}")
        
        try:
            if hasattr(cement_data, 'description') and cement_data.description:
                self._add_property_row(basic_grid, row, "Description:", str(cement_data.description))
                row += 1
        except Exception as e:
            self.logger.warning(f"Error displaying description: {e}")
        
        try:
            # Calculated properties
            if hasattr(cement_data, 'density') and cement_data.density:
                self._add_property_row(basic_grid, row, "Density:", f"{cement_data.density:.1f} kg/m³")
                row += 1
        except Exception as e:
            self.logger.warning(f"Error displaying density: {e}")
        
        basic_box.pack_start(basic_grid, False, False, 0)
        return basic_box
    
    def _create_phase_composition_tab(self, cement_data) -> Gtk.Box:
        """Create phase composition details tab."""
        phase_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        phase_box.set_margin_top(10)
        phase_box.set_margin_bottom(10)
        phase_box.set_margin_left(10)
        phase_box.set_margin_right(10)
        
        phase_grid = Gtk.Grid()
        phase_grid.set_row_spacing(5)
        phase_grid.set_column_spacing(10)
        
        row = 0
        
        # Phase fractions
        if hasattr(cement_data, 'c3s_mass_fraction') and cement_data.c3s_mass_fraction is not None:
            self._add_property_row(phase_grid, row, "C3S (Tricalcium Silicate):", f"{cement_data.c3s_mass_fraction:.3f}")
            row += 1
        
        if hasattr(cement_data, 'c2s_mass_fraction') and cement_data.c2s_mass_fraction is not None:
            self._add_property_row(phase_grid, row, "C2S (Dicalcium Silicate):", f"{cement_data.c2s_mass_fraction:.3f}")
            row += 1
        
        if hasattr(cement_data, 'c3a_mass_fraction') and cement_data.c3a_mass_fraction is not None:
            self._add_property_row(phase_grid, row, "C3A (Tricalcium Aluminate):", f"{cement_data.c3a_mass_fraction:.3f}")
            row += 1
        
        if hasattr(cement_data, 'c4af_mass_fraction') and cement_data.c4af_mass_fraction is not None:
            self._add_property_row(phase_grid, row, "C4AF (Tetracalcium Aluminoferrite):", f"{cement_data.c4af_mass_fraction:.3f}")
            row += 1
        
        # Total phase fraction
        if hasattr(cement_data, 'total_phase_fraction') and cement_data.total_phase_fraction is not None:
            self._add_property_row(phase_grid, row, "Total Phase Fraction:", f"{cement_data.total_phase_fraction:.3f}")
            row += 1
        
        phase_box.pack_start(phase_grid, False, False, 0)
        return phase_box
    
    def _create_gypsum_data_tab(self, cement_data) -> Gtk.Box:
        """Create gypsum data details tab."""
        gypsum_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        gypsum_box.set_margin_top(10)
        gypsum_box.set_margin_bottom(10)
        gypsum_box.set_margin_left(10)
        gypsum_box.set_margin_right(10)
        
        gypsum_grid = Gtk.Grid()
        gypsum_grid.set_row_spacing(5)
        gypsum_grid.set_column_spacing(10)
        
        row = 0
        
        # Gypsum fractions
        if hasattr(cement_data, 'dihyd') and cement_data.dihyd is not None:
            self._add_property_row(gypsum_grid, row, "Dihydrate Gypsum:", f"{cement_data.dihyd:.3f}")
            row += 1
        
        if hasattr(cement_data, 'anhyd') and cement_data.anhyd is not None:
            self._add_property_row(gypsum_grid, row, "Anhydrite Gypsum:", f"{cement_data.anhyd:.3f}")
            row += 1
        
        if hasattr(cement_data, 'hemihyd') and cement_data.hemihyd is not None:
            self._add_property_row(gypsum_grid, row, "Hemihydrate Gypsum:", f"{cement_data.hemihyd:.3f}")
            row += 1
        
        # Total gypsum fraction
        if hasattr(cement_data, 'total_gypsum_fraction') and cement_data.total_gypsum_fraction is not None:
            self._add_property_row(gypsum_grid, row, "Total Gypsum Fraction:", f"{cement_data.total_gypsum_fraction:.3f}")
            row += 1
        
        gypsum_box.pack_start(gypsum_grid, False, False, 0)
        return gypsum_box
    
    def _create_binary_data_tab(self, cement_data) -> Gtk.Box:
        """Create binary data details tab showing information about stored binary data."""
        binary_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        binary_box.set_margin_top(10)
        binary_box.set_margin_bottom(10)
        binary_box.set_margin_left(10)
        binary_box.set_margin_right(10)
        
        try:
            # Information label
            info_label = Gtk.Label()
            info_label.set_markup('<span size="small" style="italic">Binary data imported from Derby database</span>')
            info_label.set_halign(Gtk.Align.START)
            binary_box.pack_start(info_label, False, False, 0)
            
            binary_grid = Gtk.Grid()
            binary_grid.set_row_spacing(5)
            binary_grid.set_column_spacing(10)
            
            row = 0
            
            # Binary data fields with size information
            binary_fields = [
                ('pfc', 'Phase Fraction Data'),
                ('gif', 'GIF Image'),
                ('legend_gif', 'Legend GIF'),
                ('sil', 'Silica Data'),
                ('c3s', 'C3S Data'),
                ('c3a', 'C3A Data'),
                ('n2o', 'Na2O Data'),
                ('k2o', 'K2O Data'),
                ('alu', 'Aluminum Data'),
                ('txt', 'Text Data'),
                ('xrd', 'XRD Data'),
                ('inf', 'Information Data'),
                ('c4f', 'C4AF Data')
            ]
            
            for field_name, display_name in binary_fields:
                try:
                    if hasattr(cement_data, field_name):
                        field_value = getattr(cement_data, field_name)
                        if field_value is not None:
                            try:
                                size_kb = len(field_value) / 1024
                                if size_kb < 1:
                                    size_str = f"{len(field_value)} bytes"
                                else:
                                    size_str = f"{size_kb:.1f} KB"
                            except Exception:
                                size_str = "unknown size"
                            
                            # Add status indicator for different data types (without emoji for safety)
                            if field_name in ['gif', 'legend_gif']:
                                status = "Image"
                            elif 'data' in display_name.lower() or field_name in ['pfc', 'sil', 'c3s', 'c3a', 'n2o', 'k2o', 'alu', 'c4f']:
                                status = "Numerical"
                            elif field_name in ['txt', 'inf']:
                                status = "Text"
                            else:
                                status = "Binary"
                            
                            self._add_property_row(binary_grid, row, f"{display_name}:", f"{status} ({size_str})")
                            row += 1
                except Exception as e:
                    self.logger.warning(f"Error processing binary field {field_name}: {e}")
                    continue
            
            if row == 0:
                no_data_label = Gtk.Label("No binary data available")
                no_data_label.set_halign(Gtk.Align.START)
                binary_box.pack_start(no_data_label, False, False, 0)
            else:
                binary_box.pack_start(binary_grid, False, False, 0)
            
        except Exception as e:
            self.logger.error(f"Error creating binary data tab: {e}")
            error_label = Gtk.Label("Error displaying binary data")
            error_label.set_halign(Gtk.Align.START)
            binary_box.pack_start(error_label, False, False, 0)
        
        return binary_box
    
    def _get_material_type(self, material_data) -> str:
        """Determine the material type from the material data object."""
        if hasattr(material_data, '__tablename__'):
            tablename = material_data.__tablename__
            if tablename == 'cement':
                return 'cement'
            elif tablename == 'aggregate':
                return 'aggregate'
            elif tablename == 'fly_ash':
                return 'fly_ash'
            elif tablename == 'slag':
                return 'slag'
            elif tablename == 'filler':
                return 'filler'
            elif tablename == 'silica_fume':
                return 'silica_fume'
            elif tablename == 'limestone':
                return 'limestone'
        
        # Fallback: try to detect from class name
        class_name = material_data.__class__.__name__.lower()
        if 'cement' in class_name:
            return 'cement'
        elif 'aggregate' in class_name:
            return 'aggregate'
        elif 'flyash' in class_name or 'fly_ash' in class_name:
            return 'fly_ash'
        elif 'slag' in class_name:
            return 'slag'
        elif 'filler' in class_name:
            return 'filler'
        elif 'silica_fume' in class_name or 'silicafume' in class_name:
            return 'silica_fume'
        elif 'limestone' in class_name:
            return 'limestone'
        
        # Default fallback
        return 'cement'
    
    def _decode_description_if_hex(self, description: str) -> str:
        """Decode description from hex if it appears to be hex-encoded."""
        try:
            if not description or not description.strip():
                return ""
            
            desc_clean = description.strip()
            
            # Check if it looks like hex (even length, only hex characters)
            if (len(desc_clean) % 2 == 0 and 
                len(desc_clean) > 10 and  # Must be reasonably long
                all(c in '0123456789abcdefABCDEF' for c in desc_clean)):
                
                try:
                    import binascii
                    decoded_bytes = binascii.unhexlify(desc_clean)
                    decoded_text = decoded_bytes.decode('utf-8', errors='ignore')
                    # Keep the original line breaks for proper formatting
                    return decoded_text if decoded_text else description
                except Exception:
                    return description
            else:
                return description
                
        except Exception:
            return str(description) if description else ""
    
    def _add_full_cement_description(self, cement_data) -> None:
        """Add full cement description in a scrollable text view."""
        try:
            if not hasattr(cement_data, 'description') or not cement_data.description:
                return
            
            # Decode the full description
            full_description = self._decode_description_if_hex(cement_data.description)
            
            if not full_description.strip():
                return
            
            # Create a separator
            separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
            separator.set_margin_top(10)
            separator.set_margin_bottom(10)
            self.details_content.pack_start(separator, False, False, 0)
            
            # Description header
            desc_header = Gtk.Label()
            desc_header.set_markup('<span weight="bold">Detailed Information</span>')
            desc_header.set_halign(Gtk.Align.START)
            self.details_content.pack_start(desc_header, False, False, 0)
            
            # Create scrollable text view for the full description
            scrolled_window = Gtk.ScrolledWindow()
            scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
            scrolled_window.set_size_request(-1, 200)  # Fixed height
            scrolled_window.set_margin_top(5)
            
            # Text view with the full description
            text_view = Gtk.TextView()
            text_view.set_editable(False)
            text_view.set_cursor_visible(False)
            text_view.set_wrap_mode(Gtk.WrapMode.WORD)
            
            # Use monospace font for better alignment of tabular data
            try:
                import pango
                font_desc = pango.FontDescription("monospace 10")
                text_view.modify_font(font_desc)
            except Exception:
                # Fallback if pango import fails
                pass
            
            # Parse and format the description for better readability
            formatted_description = self._format_cement_description(full_description)
            
            # Set the text content
            text_buffer = text_view.get_buffer()
            text_buffer.set_text(formatted_description)
            
            # Style the text view
            text_view.set_margin_left(10)
            text_view.set_margin_right(10)
            text_view.set_margin_top(10)
            text_view.set_margin_bottom(10)
            
            scrolled_window.add(text_view)
            self.details_content.pack_start(scrolled_window, True, True, 0)
            
            # Try to add GIF image display (crash-safe)
            self._add_gif_display_safe(cement_data)
            
        except Exception as e:
            self.logger.error(f"Error creating full description display: {e}")
            # Simple fallback
            try:
                simple_desc = Gtk.Label("Description available but could not display")
                simple_desc.set_halign(Gtk.Align.START)
                self.details_content.pack_start(simple_desc, False, False, 0)
            except Exception:
                pass
    
    def _format_cement_description(self, description: str) -> str:
        """Format cement description for better readability with proper sections."""
        try:
            if not description:
                return ""
            
            # Split into lines and clean up
            lines = description.split('\n')
            formatted_lines = []
            
            for i, line in enumerate(lines):
                line = line.strip()
                if not line:
                    formatted_lines.append("")
                    continue
                
                # Add section headers with proper spacing
                if 'Phase Fractions for four major clinker phases' in line:
                    formatted_lines.append("")
                    formatted_lines.append("█" * 50)
                    formatted_lines.append("PHASE FRACTIONS (FOUR MAJOR CLINKER PHASES)")
                    formatted_lines.append("█" * 50)
                    formatted_lines.append("")
                elif 'Overall phase fractions' in line:
                    formatted_lines.append("")
                    formatted_lines.append("█" * 40)
                    formatted_lines.append("OVERALL PHASE FRACTIONS")
                    formatted_lines.append("█" * 40)
                    formatted_lines.append("")
                elif 'Extracted Correlation files' in line:
                    formatted_lines.append("")
                    formatted_lines.append("█" * 30)
                    formatted_lines.append("CORRELATION FILES")
                    formatted_lines.append("█" * 30)
                    formatted_lines.append("")
                elif line.startswith('PHASE') and ('AREA' in line or 'PERIMETER' in line):
                    formatted_lines.append("")
                    formatted_lines.append(line)
                    formatted_lines.append("-" * len(line))
                elif any(phase in line for phase in ['C3S', 'C2S', 'C3A', 'C4AF', 'Gypsum', 'Free lime']):
                    # Indent phase data for clarity
                    if any(char.isdigit() for char in line):  # Has numbers (phase values)
                        formatted_lines.append("    " + line)
                    else:
                        formatted_lines.append(line)
                elif '.gif' in line or '.psd' in line or '.sil' in line or '.c3s' in line or '.c4f' in line:
                    # Indent file references
                    formatted_lines.append("    " + line)
                else:
                    formatted_lines.append(line)
            
            return '\n'.join(formatted_lines)
            
        except Exception:
            return description
    
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
    
    def _duplicate_material(self, original_material, material_type: str) -> None:
        """Create a duplicate of the given material with a new name."""
        try:
            # Generate a unique name for the duplicate
            if material_type == 'aggregate':
                base_name = original_material.display_name
            else:
                base_name = original_material.name
            new_name = self._generate_unique_material_name(base_name, material_type)
            
            # Get the appropriate service
            service_container = get_service_container()
            if material_type == 'cement':
                service = service_container.cement_service
            elif material_type == 'aggregate':
                service = service_container.aggregate_service
            elif material_type == 'filler':
                service = service_container.filler_service
            elif material_type == 'fly_ash':
                service = service_container.fly_ash_service
            elif material_type == 'slag':
                service = service_container.slag_service
            elif material_type == 'silica_fume':
                service = service_container.silica_fume_service
            elif material_type == 'limestone':
                service = service_container.limestone_service
            elif material_type == 'filler':
                service = service_container.filler_service
            else:
                raise ValueError(f"Unsupported material type for duplication: {material_type}")
            
            # Create a new material instance with copied data
            duplicate_data = self._copy_material_data(original_material, new_name, material_type)
            
            # Save the duplicate to the database
            if material_type == 'cement':
                from app.models.cement import CementCreate
                cement_create = CementCreate(**duplicate_data)
                service.create(cement_create)
            elif material_type == 'aggregate':
                from app.models.aggregate import AggregateCreate
                aggregate_create = AggregateCreate(**duplicate_data)
                service.create(aggregate_create)
            elif material_type == 'filler':
                from app.models.filler import FillerCreate
                filler_create = FillerCreate(**duplicate_data)
                service.create(filler_create)
            elif material_type == 'fly_ash':
                from app.models.fly_ash import FlyAshCreate
                fly_ash_create = FlyAshCreate(**duplicate_data)
                service.create(fly_ash_create)
            elif material_type == 'slag':
                from app.models.slag import SlagCreate
                slag_create = SlagCreate(**duplicate_data)
                service.create(slag_create)
            elif material_type == 'silica_fume':
                from app.models.silica_fume import SilicaFumeCreate
                silica_fume_create = SilicaFumeCreate(**duplicate_data)
                service.create(silica_fume_create)
            elif material_type == 'limestone':
                from app.models.limestone import LimestoneCreate
                limestone_create = LimestoneCreate(**duplicate_data)
                service.create(limestone_create)
            elif material_type == 'filler':
                from app.models.filler import FillerCreate
                filler_create = FillerCreate(**duplicate_data)
                service.create(filler_create)
            
            # Refresh the table to show the new material
            self.material_table.refresh_data()
            self._load_initial_data()
            
            self.main_window.update_status(f"Material '{new_name}' duplicated successfully", "success", 3)
            
        except Exception as e:
            self.logger.error(f"Error duplicating material: {e}")
            raise
    
    def _generate_unique_material_name(self, base_name: str, material_type: str) -> str:
        """Generate a unique name for a duplicated material."""
        service_container = get_service_container()
        
        # Get the appropriate service
        if material_type == 'cement':
            service = service_container.cement_service
        elif material_type == 'aggregate':
            service = service_container.aggregate_service
        elif material_type == 'filler':
            service = service_container.filler_service
        elif material_type == 'fly_ash':
            service = service_container.fly_ash_service
        elif material_type == 'slag':
            service = service_container.slag_service
        elif material_type == 'silica_fume':
            service = service_container.silica_fume_service
        elif material_type == 'limestone':
            service = service_container.limestone_service
        elif material_type == 'filler':
            service = service_container.filler_service
        else:
            raise ValueError(f"Unsupported material type: {material_type}")
        
        # Try different suffixes until we find a unique name
        counter = 1
        while True:
            new_name = f"{base_name} (Copy {counter})"
            
            # Check if this name already exists
            try:
                if material_type == 'cement':
                    existing = service.get_by_name(new_name)
                elif material_type == 'aggregate':
                    # For aggregate, we need to check by display_name (primary key)
                    with service.db_service.get_read_only_session() as session:
                        existing = session.query(service.model).filter_by(display_name=new_name).first()
                else:
                    existing = service.get_by_name(new_name)
                
                if existing is None:
                    return new_name
                counter += 1
            except Exception:
                # If get_by_name fails, assume the name is available
                return new_name
            
            # Safety check to avoid infinite loops
            if counter > 100:
                import uuid
                return f"{base_name} (Copy {str(uuid.uuid4())[:8]})"
    
    def _copy_material_data(self, original_material, new_name: str, material_type: str) -> dict:
        """Create a copy of material data for duplication."""
        try:
            if material_type == 'cement':
                return self._copy_cement_data(original_material, new_name)
            elif material_type == 'aggregate':
                return self._copy_aggregate_data(original_material, new_name)
            elif material_type == 'filler':
                return self._copy_filler_data(original_material, new_name)
            elif material_type == 'fly_ash':
                return self._copy_fly_ash_data(original_material, new_name)
            elif material_type == 'slag':
                return self._copy_slag_data(original_material, new_name)
            elif material_type == 'silica_fume':
                return self._copy_silica_fume_data(original_material, new_name)
            elif material_type == 'limestone':
                return self._copy_limestone_data(original_material, new_name)
            elif material_type == 'filler':
                return self._copy_filler_data(original_material, new_name)
            else:
                raise ValueError(f"Unsupported material type: {material_type}")
        except Exception as e:
            self.logger.error(f"Error copying material data: {e}")
            raise
    
    def _copy_cement_data(self, original_cement, new_name: str) -> dict:
        """Create a copy of cement data."""
        # Handle description carefully - don't truncate hex-encoded data
        description = original_cement.description or ''
        
        if description:
            # Check if it looks like hex and preserve it completely
            hex_only = ''.join(description.strip().split())
            if (len(hex_only) % 2 == 0 and 
                len(hex_only) > 10 and
                all(c in '0123456789abcdefABCDEF' for c in hex_only)):
                # This is hex-encoded data, preserve it completely
                truncated_description = description
            else:
                # Regular text, safe to truncate
                truncated_description = description[:255]
        else:
            truncated_description = ''
        
        copy_data = {
            'name': new_name,
            'specific_gravity': original_cement.specific_gravity,
            'description': truncated_description,
            'psd_data_id': original_cement.psd_data_id,
            'alkali_file': original_cement.alkali_file,
        }
        
        # Copy phase fractions if available
        phase_fields = [
            'c3s_mass_fraction', 'c2s_mass_fraction', 'c3a_mass_fraction', 'c4af_mass_fraction',
            'k2so4_mass_fraction', 'na2so4_mass_fraction'
        ]
        for field in phase_fields:
            if hasattr(original_cement, field):
                copy_data[field] = getattr(original_cement, field)
        
        # Copy volume fractions if available
        volume_fields = [
            'c3s_volume_fraction', 'c2s_volume_fraction', 'c3a_volume_fraction', 'c4af_volume_fraction',
            'k2so4_volume_fraction', 'na2so4_volume_fraction'
        ]
        for field in volume_fields:
            if hasattr(original_cement, field):
                copy_data[field] = getattr(original_cement, field)
        
        # Copy surface fractions if available
        surface_fields = [
            'c3s_surface_fraction', 'c2s_surface_fraction', 'c3a_surface_fraction', 'c4af_surface_fraction',
            'k2so4_surface_fraction', 'na2so4_surface_fraction'
        ]
        for field in surface_fields:
            if hasattr(original_cement, field):
                copy_data[field] = getattr(original_cement, field)
        
        # Copy gypsum data if available
        gypsum_fields = ['dihyd', 'anhyd', 'hemihyd']
        print(f"DEBUG: _copy_cement_data - copying gypsum data from {original_cement.name}")
        for field in gypsum_fields:
            if hasattr(original_cement, field):
                value = getattr(original_cement, field)
                copy_data[field] = value
                print(f"DEBUG: Copied {field} = {value}")
            else:
                print(f"DEBUG: Original cement missing field {field}")
        
        # Copy new fields (setting times, fineness, PSD parameters)
        new_fields = [
            'initial_set_time', 'final_set_time', 'specific_surface_area',
            'psd_mode', 'psd_d50', 'psd_n', 'psd_dmax', 'psd_exponent', 'psd_custom_points',
            'source', 'notes'
        ]
        for field in new_fields:
            if hasattr(original_cement, field):
                copy_data[field] = getattr(original_cement, field)
        
        # Copy binary data fields (but not the actual binary data to avoid issues)
        # We'll skip binary data copying to avoid potential memory/storage issues
        binary_fields = ['pfc', 'gif', 'legend_gif', 'sil', 'c3s', 'c3a', 'n2o', 'k2o', 'alu', 'txt', 'xrd', 'inf', 'c4f']
        for field in binary_fields:
            if hasattr(original_cement, field):
                binary_data = getattr(original_cement, field)
                if binary_data is not None:
                    copy_data[field] = binary_data
        
        return copy_data
    
    def _copy_aggregate_data(self, original_aggregate, new_name: str) -> dict:
        """Create a copy of aggregate data."""
        copy_data = {
            'display_name': new_name,  # Primary key for aggregate
            'name': getattr(original_aggregate, 'name', new_name),
            'type': getattr(original_aggregate, 'type', None),
            'specific_gravity': original_aggregate.specific_gravity,
            'bulk_modulus': getattr(original_aggregate, 'bulk_modulus', None),
            'shear_modulus': getattr(original_aggregate, 'shear_modulus', None),
            'conductivity': getattr(original_aggregate, 'conductivity', 0.0),
        }
        
        # Copy new fields (source, notes)
        new_fields = ['source', 'notes']
        for field in new_fields:
            if hasattr(original_aggregate, field):
                copy_data[field] = getattr(original_aggregate, field)
        
        # Copy binary data if available
        binary_fields = ['image', 'txt', 'inf', 'shape_stats']
        for field in binary_fields:
            if hasattr(original_aggregate, field):
                binary_data = getattr(original_aggregate, field)
                if binary_data is not None:
                    copy_data[field] = binary_data
        
        return copy_data

    def _copy_filler_data(self, original_filler, new_name: str) -> dict:
        """Create a copy of filler data."""
        copy_data = {
            'name': new_name,
            'specific_gravity': getattr(original_filler, 'specific_gravity', None),
            'description': getattr(original_filler, 'description', None),
            'source': getattr(original_filler, 'source', None),
            'specific_surface_area': getattr(original_filler, 'specific_surface_area', None),
            'water_absorption': getattr(original_filler, 'water_absorption', None),
            'filler_type': getattr(original_filler, 'filler_type', None),
            'color': getattr(original_filler, 'color', None),
            'notes': getattr(original_filler, 'notes', None),
        }
        
        # Copy PSD data if available
        psd_fields = [
            'diameter_percentile_10', 'diameter_percentile_50', 'diameter_percentile_90'
        ]
        for field in psd_fields:
            if hasattr(original_filler, field):
                copy_data[field] = getattr(original_filler, field)
        
        return copy_data

    def _copy_fly_ash_data(self, original_fly_ash, new_name: str) -> dict:
        """Create a copy of fly ash data."""
        copy_data = {
            'name': new_name,
            'specific_gravity': getattr(original_fly_ash, 'specific_gravity', None),
            'description': getattr(original_fly_ash, 'description', None),
            'source': getattr(original_fly_ash, 'source', None),
            'notes': getattr(original_fly_ash, 'notes', None),
        }
        
        # Copy all PSD fields
        psd_fields = [
            'psd', 'psd_custom_points', 'psd_mode', 'psd_d50', 'psd_n', 'psd_dmax',
            'psd_median', 'psd_spread', 'psd_exponent'
        ]
        for field in psd_fields:
            if hasattr(original_fly_ash, field):
                copy_data[field] = getattr(original_fly_ash, field)
        
        # Copy phase distribution and fractions
        phase_fields = [
            'distribute_phases_by', 'aluminosilicate_glass_fraction',
            'calcium_aluminum_disilicate_fraction', 'tricalcium_aluminate_fraction',
            'calcium_chloride_fraction', 'silica_fraction', 'anhydrate_fraction'
        ]
        for field in phase_fields:
            if hasattr(original_fly_ash, field):
                copy_data[field] = getattr(original_fly_ash, field)
        
        # Copy chemical composition
        chemical_fields = [
            'sio2_content', 'al2o3_content', 'fe2o3_content', 'cao_content',
            'mgo_content', 'so3_content', 'na2o', 'k2o', 'na2o_equivalent',
            'loi', 'fineness_45um'
        ]
        for field in chemical_fields:
            if hasattr(original_fly_ash, field):
                copy_data[field] = getattr(original_fly_ash, field)
        
        # Copy activity and classification fields
        activity_fields = [
            'astm_class', 'activity_index', 'pozzolanic_activity', 'activation_energy'
        ]
        for field in activity_fields:
            if hasattr(original_fly_ash, field):
                copy_data[field] = getattr(original_fly_ash, field)
        
        return copy_data

    def _copy_slag_data(self, original_slag, new_name: str) -> dict:
        """Create a copy of slag data."""
        copy_data = {
            'name': new_name,
            'specific_gravity': getattr(original_slag, 'specific_gravity', None),
            'description': getattr(original_slag, 'description', None),
            'source': getattr(original_slag, 'source', None),
            'notes': getattr(original_slag, 'notes', None),
        }
        
        # Copy all PSD fields
        psd_fields = [
            'psd', 'psd_custom_points', 'psd_mode', 'psd_d50', 'psd_n', 'psd_dmax',
            'psd_median', 'psd_spread', 'psd_exponent'
        ]
        for field in psd_fields:
            if hasattr(original_slag, field):
                copy_data[field] = getattr(original_slag, field)
        
        # Copy basic slag properties
        basic_fields = [
            'glass_content', 'activity_index'
        ]
        for field in basic_fields:
            if hasattr(original_slag, field):
                copy_data[field] = getattr(original_slag, field)
        
        # Copy chemical composition (oxide content)
        chemical_fields = [
            'sio2_content', 'cao_content', 'al2o3_content', 'mgo_content',
            'fe2o3_content', 'so3_content'
        ]
        for field in chemical_fields:
            if hasattr(original_slag, field):
                copy_data[field] = getattr(original_slag, field)
        
        # Copy reaction parameters
        reaction_fields = [
            'activation_energy', 'reactivity_factor', 'rate_constant'
        ]
        for field in reaction_fields:
            if hasattr(original_slag, field):
                copy_data[field] = getattr(original_slag, field)
        
        # Copy molecular and chemical properties
        molecular_fields = [
            'molecular_mass', 'casi_mol_ratio', 'si_per_mole',
            'base_slag_reactivity', 'c3a_per_mole'
        ]
        for field in molecular_fields:
            if hasattr(original_slag, field):
                copy_data[field] = getattr(original_slag, field)
        
        # Copy hydration product (HP) properties
        hp_fields = [
            'hp_molecular_mass', 'hp_density', 'hp_casi_mol_ratio', 'hp_h2o_sio2_mol_ratio'
        ]
        for field in hp_fields:
            if hasattr(original_slag, field):
                copy_data[field] = getattr(original_slag, field)
        
        return copy_data

    def _copy_silica_fume_data(self, original_silica_fume, new_name: str) -> dict:
        """Create a copy of silica fume data."""
        copy_data = {
            'name': new_name,
            'specific_gravity': getattr(original_silica_fume, 'specific_gravity', 2.22),
            'description': getattr(original_silica_fume, 'description', None),
            'source': getattr(original_silica_fume, 'source', None),
            'notes': getattr(original_silica_fume, 'notes', None),
            'psd': getattr(original_silica_fume, 'psd', 'cement141'),
            'psd_custom_points': getattr(original_silica_fume, 'psd_custom_points', None),
            'distribute_phases_by': getattr(original_silica_fume, 'distribute_phases_by', None),
            'silica_fume_fraction': getattr(original_silica_fume, 'silica_fume_fraction', 1.0),
            'activation_energy': getattr(original_silica_fume, 'activation_energy', 54000.0),
        }
        
        return copy_data

    def _copy_limestone_data(self, original_limestone, new_name: str) -> dict:
        """Create a copy of limestone data."""
        copy_data = {
            'name': new_name,
            'specific_gravity': getattr(original_limestone, 'specific_gravity', 2.71),
            'description': getattr(original_limestone, 'description', None),
            'source': getattr(original_limestone, 'source', None),
            'notes': getattr(original_limestone, 'notes', None),
            'psd': getattr(original_limestone, 'psd', 'cement141'),
            'psd_custom_points': getattr(original_limestone, 'psd_custom_points', None),
            'distribute_phases_by': getattr(original_limestone, 'distribute_phases_by', None),
            'limestone_fraction': getattr(original_limestone, 'limestone_fraction', 1.0),
            'caco3_content': getattr(original_limestone, 'caco3_content', 97.0),
            'hardness': getattr(original_limestone, 'hardness', 3.0),
            'psd_median': getattr(original_limestone, 'psd_median', 5.0),
            'psd_spread': getattr(original_limestone, 'psd_spread', 2.0),
            'activation_energy': getattr(original_limestone, 'activation_energy', 54000.0),
        }
        
        return copy_data


    def _show_material_dialog(self, material_type: str, material_data=None) -> None:
        """Show the material dialog for adding or editing."""
        try:
            # Create and show material dialog
            # Convert SQLAlchemy object to dict for dialog
            if material_data:
                material_dict = {
                    'name': getattr(material_data, 'name', ''),
                    'display_name': getattr(material_data, 'display_name', ''),
                    'description': getattr(material_data, 'description', ''),
                    'specific_gravity': getattr(material_data, 'specific_gravity', 2.65),
                    'source': getattr(material_data, 'source', ''),
                    'notes': getattr(material_data, 'notes', ''),
                }
                # Add material-specific fields
                for attr in dir(material_data):
                    if not attr.startswith('_') and attr not in material_dict:
                        try:
                            value = getattr(material_data, attr)
                            if value is not None and not callable(value):
                                material_dict[attr] = value
                        except:
                            pass
                
                # Special handling for cement PSD data relationship
                if material_type == 'cement' and hasattr(material_data, 'psd_data') and material_data.psd_data:
                    # Flatten PSD data fields into the material dict
                    psd_data = material_data.psd_data
                    psd_fields = ['psd_mode', 'psd_d50', 'psd_n', 'psd_dmax', 'psd_median', 
                                 'psd_spread', 'psd_exponent', 'psd_custom_points',
                                 'diameter_percentile_10', 'diameter_percentile_50', 'diameter_percentile_90']
                    for field in psd_fields:
                        if hasattr(psd_data, field):
                            value = getattr(psd_data, field)
                            if value is not None:
                                material_dict[field] = value
                
                # Special handling for filler PSD data relationship
                if material_type == 'filler' and hasattr(material_data, 'psd_data') and material_data.psd_data:
                    # Flatten PSD data fields into the material dict
                    psd_data = material_data.psd_data
                    psd_fields = ['psd_mode', 'psd_d50', 'psd_n', 'psd_dmax', 'psd_median', 
                                 'psd_spread', 'psd_exponent', 'psd_custom_points',
                                 'diameter_percentile_10', 'diameter_percentile_50', 'diameter_percentile_90']
                    for field in psd_fields:
                        if hasattr(psd_data, field):
                            value = getattr(psd_data, field)
                            if value is not None:
                                material_dict[field] = value
                
                dialog = create_material_dialog(self.main_window, material_type, material_dict)
            else:
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
            material_type = self._get_material_type(material_data)
            
            # Get appropriate service
            service_container = get_service_container()
            if material_type == 'cement':
                service = service_container.cement_service
            elif material_type == 'aggregate':
                service = service_container.aggregate_service
            elif material_type == 'fly_ash':
                service = service_container.fly_ash_service
            elif material_type == 'slag':
                service = service_container.slag_service
            elif material_type == 'filler':
                service = service_container.filler_service
            elif material_type == 'silica_fume':
                service = service_container.silica_fume_service
            elif material_type == 'limestone':
                service = service_container.limestone_service
            else:
                raise ValueError(f"Unsupported material type: {material_type}")
            
            # Delete the material using the correct primary key
            if material_type == 'cement':
                service.delete(material_data.name)
            elif material_type == 'aggregate':
                service.delete(material_data.display_name)
            elif material_type in ['limestone', 'silica_fume', 'filler', 'fly_ash', 'slag']:
                # These services use name-based delete
                service.delete(material_data.name)
            else:
                # Fallback for any other material types
                service.delete(material_data.id)
            
            # Refresh data
            self.material_table.refresh_data()
            self._load_initial_data()
            self.details_revealer.set_reveal_child(False)
            self.selected_material = None
            
            # Refresh Mix Design panel material lists if it exists
            if hasattr(self.main_window, 'mix_design_panel'):
                self.main_window.mix_design_panel.refresh_material_lists()
            
            self.main_window.update_status(f"Material '{material_data.name}' deleted successfully", "success", 3)
            
        except Exception as e:
            self.logger.error(f"Error deleting material: {e}")
            import traceback
            self.logger.error(f"Full traceback: {traceback.format_exc()}")
            self.main_window.update_status(f"Error deleting material: {e}", "error", 5)
    
    def _add_gif_display_safe(self, cement_data) -> None:
        """Safely add GIF image display without causing crashes."""
        # TEMPORARILY DISABLE GIF DISPLAY TO ELIMINATE INFINITE SURFACE SIZE WARNINGS
        # This feature was causing infinite surface size errors during pixbuf creation
        try:
            # Check if cement has GIF data
            if not hasattr(cement_data, 'gif') or not cement_data.gif:
                return
            
            # Show GIF availability without actually displaying the image
            gif_data = cement_data.gif
            size_kb = len(gif_data) / 1024
            
            # Add info section instead of actual image
            separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
            separator.set_margin_top(10)
            separator.set_margin_bottom(10)
            self.details_content.pack_start(separator, False, False, 0)
            
            img_label = Gtk.Label()
            img_label.set_markup('<b>Microstructure Image Data</b>')
            img_label.set_halign(Gtk.Align.START)
            img_label.set_margin_bottom(5)
            self.details_content.pack_start(img_label, False, False, 0)
            
            info_label = Gtk.Label()
            info_label.set_markup(f'<span size="small" style="italic">GIF image data available ({size_kb:.1f} KB)</span>')
            info_label.set_halign(Gtk.Align.START)
            self.details_content.pack_start(info_label, False, False, 0)
            
            note_label = Gtk.Label()
            note_label.set_markup('<span size="small" color="#666666">Image display temporarily disabled to prevent rendering issues</span>')
            note_label.set_halign(Gtk.Align.START)
            note_label.set_margin_top(5)
            self.details_content.pack_start(note_label, False, False, 0)
            
        except Exception as e:
            self.logger.warning(f"Error adding GIF info for {cement_data.name}: {e}")
            # Don't let GIF info errors break the rest of the panel
    
    def _create_gif_display_section(self, cement_data, gif_data: bytes) -> None:
        """Create the GIF image display section."""
        try:
            # Add separator
            separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
            separator.set_margin_top(10)
            separator.set_margin_bottom(10)
            self.details_content.pack_start(separator, False, False, 0)
            
            # Header for images section
            img_header = Gtk.Label()
            img_header.set_markup('<span weight="bold">Cement Images</span>')
            img_header.set_halign(Gtk.Align.START)
            self.details_content.pack_start(img_header, False, False, 0)
            
            # Create image container
            img_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            img_box.set_margin_top(5)
            
            # Create GIF image from binary data
            try:
                from gi.repository import GdkPixbuf, Gio, GLib
                
                # Convert Python bytes to GLib.Bytes
                glib_bytes = GLib.Bytes.new(gif_data)
                
                # Create input stream from GLib bytes
                gif_stream = Gio.MemoryInputStream.new_from_bytes(glib_bytes)
                
                # Load pixbuf from stream
                pixbuf = GdkPixbuf.Pixbuf.new_from_stream(gif_stream, None)
                
                if pixbuf:
                    # Validate pixbuf dimensions to prevent infinite surface size errors
                    orig_width = pixbuf.get_width()
                    orig_height = pixbuf.get_height()
                    
                    # Check for invalid dimensions
                    if orig_width <= 0 or orig_height <= 0 or orig_width > 32768 or orig_height > 32768:
                        raise Exception(f"Invalid pixbuf dimensions: {orig_width}x{orig_height}")
                    
                    if orig_width > 300:
                        scale_factor = 300.0 / orig_width
                        new_width = 300
                        new_height = int(orig_height * scale_factor)
                        
                        # Validate scaled dimensions
                        if new_height <= 0 or new_height > 32768:
                            raise Exception(f"Invalid scaled dimensions: {new_width}x{new_height}")
                        
                        pixbuf = pixbuf.scale_simple(new_width, new_height, GdkPixbuf.InterpType.BILINEAR)
                    
                    # Create image widget
                    image = Gtk.Image.new_from_pixbuf(pixbuf)
                    image.set_halign(Gtk.Align.START)
                    
                    # Add image info
                    info_label = Gtk.Label()
                    size_kb = len(gif_data) / 1024
                    info_label.set_markup(f'<span size="small" style="italic">Size: {orig_width}x{orig_height} pixels ({size_kb:.1f} KB)</span>')
                    info_label.set_halign(Gtk.Align.START)
                    
                    img_box.pack_start(info_label, False, False, 0)
                    img_box.pack_start(image, False, False, 0)
                    
                    self.logger.info(f"Successfully loaded GIF for {cement_data.name}")
                else:
                    raise Exception("Failed to create pixbuf from GIF data")
                
            except Exception as e:
                self.logger.warning(f"Error creating GIF image for {cement_data.name}: {e}")
                # Fallback - show info about the GIF without displaying it
                fallback_label = Gtk.Label()
                size_kb = len(gif_data) / 1024
                fallback_label.set_markup(f'<span size="small">GIF image available ({size_kb:.1f} KB) - Display error: {str(e)}</span>')
                fallback_label.set_halign(Gtk.Align.START)
                img_box.pack_start(fallback_label, False, False, 0)
            
            self.details_content.pack_start(img_box, False, False, 0)
            
        except Exception as e:
            self.logger.error(f"Error creating GIF display section: {e}")
            # Ultra-safe fallback
            try:
                error_label = Gtk.Label("Image display not available")
                error_label.set_halign(Gtk.Align.START)
                self.details_content.pack_start(error_label, False, False, 0)
            except Exception:
                pass
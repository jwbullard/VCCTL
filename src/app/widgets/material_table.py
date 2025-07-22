#!/usr/bin/env python3
"""
Material Table Widget for VCCTL

Provides a comprehensive table widget for displaying and managing material data with sorting,
filtering, pagination, and export capabilities.
"""

import gi
import logging
import csv
import json
from typing import TYPE_CHECKING, Optional, Dict, Any, List, Callable, Tuple
from enum import Enum
from pathlib import Path

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, Gdk, Pango

if TYPE_CHECKING:
    from app.windows.main_window import VCCTLMainWindow

from app.services.service_container import get_service_container


class MaterialTableColumn(Enum):
    """Enumeration of material table columns."""
    NAME = 0
    TYPE = 1
    SPECIFIC_GRAVITY = 2
    CREATED_DATE = 3
    MODIFIED_DATE = 4
    DESCRIPTION = 5


class MaterialTable(Gtk.Box):
    """Advanced material table widget with sorting, filtering, and export capabilities."""
    
    # Custom signals
    __gsignals__ = {
        'material-selected': (GObject.SignalFlags.RUN_FIRST, None, (object,)),
        'material-activated': (GObject.SignalFlags.RUN_FIRST, None, (object,)),
        'materials-changed': (GObject.SignalFlags.RUN_FIRST, None, ()),
    }
    
    def __init__(self, main_window: 'VCCTLMainWindow'):
        """Initialize the material table."""
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        self.main_window = main_window
        self.logger = logging.getLogger('VCCTL.MaterialTable')
        self.service_container = get_service_container()
        
        # Table state
        self.materials_data = []
        self.selected_materials = set()
        self.sort_column = MaterialTableColumn.NAME
        self.sort_ascending = True
        self.current_page = 0
        self.items_per_page = 50
        self.total_items = 0
        
        # Filter state
        self.current_filters = {
            'text': '',
            'type': 'all',
            'sg_min': 1.0,
            'sg_max': 5.0
        }
        
        # Setup UI
        self._setup_ui()
        self._setup_columns()
        self._connect_signals()
        
        # Load initial data
        self._load_materials()
        
        self.logger.info("Material table initialized")
    
    def _setup_ui(self) -> None:
        """Setup the table UI components."""
        # Create table toolbar
        self._create_toolbar()
        
        # Create main table area
        self._create_table_area()
        
        # Create pagination controls
        self._create_pagination()
        
        # Create status bar
        self._create_status_bar()
    
    def _create_toolbar(self) -> None:
        """Create the table toolbar with controls."""
        toolbar_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        toolbar_box.set_margin_top(5)
        toolbar_box.set_margin_bottom(5)
        toolbar_box.set_margin_left(10)
        toolbar_box.set_margin_right(10)
        
        # Selection controls
        selection_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        selection_box.get_style_context().add_class("linked")
        
        self.select_all_button = Gtk.Button(label="Select All")
        self.select_all_button.set_tooltip_text("Select all visible items")
        selection_box.pack_start(self.select_all_button, False, False, 0)
        
        self.select_none_button = Gtk.Button(label="Select None")
        self.select_none_button.set_tooltip_text("Clear selection")
        selection_box.pack_start(self.select_none_button, False, False, 0)
        
        toolbar_box.pack_start(selection_box, False, False, 0)
        
        # Bulk operations
        bulk_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        bulk_box.get_style_context().add_class("linked")
        
        self.bulk_delete_button = Gtk.Button(label="Delete Selected")
        self.bulk_delete_button.set_sensitive(False)
        delete_icon = Gtk.Image.new_from_icon_name("edit-delete-symbolic", Gtk.IconSize.BUTTON)
        self.bulk_delete_button.set_image(delete_icon)
        self.bulk_delete_button.get_style_context().add_class("destructive-action")
        bulk_box.pack_start(self.bulk_delete_button, False, False, 0)
        
        self.bulk_export_button = Gtk.Button(label="Export Selected")
        self.bulk_export_button.set_sensitive(False)
        export_icon = Gtk.Image.new_from_icon_name("document-save-symbolic", Gtk.IconSize.BUTTON)
        self.bulk_export_button.set_image(export_icon)
        bulk_box.pack_start(self.bulk_export_button, False, False, 0)
        
        toolbar_box.pack_start(bulk_box, False, False, 0)
        
        # View controls
        view_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        # Items per page
        items_label = Gtk.Label("Items per page:")
        view_box.pack_start(items_label, False, False, 0)
        
        self.items_combo = Gtk.ComboBoxText()
        self.items_combo.append("25", "25")
        self.items_combo.append("50", "50")
        self.items_combo.append("100", "100")
        self.items_combo.append("200", "200")
        self.items_combo.set_active_id("50")
        view_box.pack_start(self.items_combo, False, False, 0)
        
        # Column visibility
        self.columns_button = Gtk.MenuButton()
        self.columns_button.set_label("Columns")
        columns_icon = Gtk.Image.new_from_icon_name("view-list-symbolic", Gtk.IconSize.BUTTON)
        self.columns_button.set_image(columns_icon)
        self.columns_button.set_always_show_image(True)
        view_box.pack_start(self.columns_button, False, False, 0)
        
        toolbar_box.pack_end(view_box, False, False, 0)
        
        # Refresh button
        self.refresh_button = Gtk.Button()
        refresh_icon = Gtk.Image.new_from_icon_name("view-refresh-symbolic", Gtk.IconSize.BUTTON)
        self.refresh_button.set_image(refresh_icon)
        self.refresh_button.set_tooltip_text("Refresh data")
        toolbar_box.pack_end(self.refresh_button, False, False, 0)
        
        self.pack_start(toolbar_box, False, False, 0)
    
    def _create_table_area(self) -> None:
        """Create the main table area."""
        # Create scrolled window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_shadow_type(Gtk.ShadowType.IN)
        
        # Create tree view
        self.tree_view = Gtk.TreeView()
        self.tree_view.set_grid_lines(Gtk.TreeViewGridLines.HORIZONTAL)
        self.tree_view.set_enable_search(True)
        self.tree_view.set_search_column(MaterialTableColumn.NAME.value)
        self.tree_view.set_rubber_banding(True)
        
        # Create list store model
        # Columns: name, type, specific_gravity, created_date, modified_date, description, material_data
        self.list_store = Gtk.ListStore(str, str, float, str, str, str, object)
        
        # Create filter model
        self.filter_model = self.list_store.filter_new()
        self.filter_model.set_visible_func(self._filter_visible_func)
        
        # Create sort model
        self.sort_model = Gtk.TreeModelSort(model=self.filter_model)
        self.tree_view.set_model(self.sort_model)
        
        # Enable multiple selection
        selection = self.tree_view.get_selection()
        selection.set_mode(Gtk.SelectionMode.MULTIPLE)
        
        scrolled.add(self.tree_view)
        self.pack_start(scrolled, True, True, 0)
    
    def _setup_columns(self) -> None:
        """Setup tree view columns."""
        # Selection column with checkbox
        selection_renderer = Gtk.CellRendererToggle()
        selection_column = Gtk.TreeViewColumn("", selection_renderer)
        selection_column.set_clickable(True)
        selection_column.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
        selection_column.set_fixed_width(30)
        self.tree_view.append_column(selection_column)
        
        # Column definitions
        columns = [
            ("Name", MaterialTableColumn.NAME, 200, True),
            ("Type", MaterialTableColumn.TYPE, 120, True),
            ("Specific Gravity", MaterialTableColumn.SPECIFIC_GRAVITY, 120, True),
            ("Created", MaterialTableColumn.CREATED_DATE, 120, True),
            ("Modified", MaterialTableColumn.MODIFIED_DATE, 120, True),
            ("Description", MaterialTableColumn.DESCRIPTION, 250, False)  # Hidden
        ]
        
        self.columns = {}
        
        for title, col_enum, width, visible in columns:
            # Create text renderer
            renderer = Gtk.CellRendererText()
            renderer.set_property("ellipsize", Pango.EllipsizeMode.END)
            
            # Create column
            column = Gtk.TreeViewColumn(title, renderer, text=col_enum.value)
            column.set_clickable(True)
            column.set_resizable(True)
            column.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
            column.set_fixed_width(width)
            column.set_sort_column_id(col_enum.value)
            column.set_visible(visible)
            
            # Add sort indicator
            column.set_sort_indicator(True)
            
            self.tree_view.append_column(column)
            self.columns[col_enum] = column
        
        # Set default sort
        self.sort_model.set_sort_column_id(
            MaterialTableColumn.NAME.value, 
            Gtk.SortType.ASCENDING
        )
    
    def _create_pagination(self) -> None:
        """Create pagination controls."""
        pagination_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        pagination_box.set_margin_top(5)
        pagination_box.set_margin_bottom(5)
        pagination_box.set_margin_left(10)
        pagination_box.set_margin_right(10)
        
        # Page navigation
        nav_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        nav_box.get_style_context().add_class("linked")
        
        self.first_page_button = Gtk.Button()
        first_icon = Gtk.Image.new_from_icon_name("go-first-symbolic", Gtk.IconSize.BUTTON)
        self.first_page_button.set_image(first_icon)
        self.first_page_button.set_tooltip_text("First page")
        nav_box.pack_start(self.first_page_button, False, False, 0)
        
        self.prev_page_button = Gtk.Button()
        prev_icon = Gtk.Image.new_from_icon_name("go-previous-symbolic", Gtk.IconSize.BUTTON)
        self.prev_page_button.set_image(prev_icon)
        self.prev_page_button.set_tooltip_text("Previous page")
        nav_box.pack_start(self.prev_page_button, False, False, 0)
        
        self.next_page_button = Gtk.Button()
        next_icon = Gtk.Image.new_from_icon_name("go-next-symbolic", Gtk.IconSize.BUTTON)
        self.next_page_button.set_image(next_icon)
        self.next_page_button.set_tooltip_text("Next page")
        nav_box.pack_start(self.next_page_button, False, False, 0)
        
        self.last_page_button = Gtk.Button()
        last_icon = Gtk.Image.new_from_icon_name("go-last-symbolic", Gtk.IconSize.BUTTON)
        self.last_page_button.set_image(last_icon)
        self.last_page_button.set_tooltip_text("Last page")
        nav_box.pack_start(self.last_page_button, False, False, 0)
        
        pagination_box.pack_start(nav_box, False, False, 0)
        
        # Page info
        self.page_info_label = Gtk.Label()
        self.page_info_label.set_markup("<i>No data</i>")
        pagination_box.pack_start(self.page_info_label, True, True, 0)
        
        # Jump to page
        jump_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        jump_label = Gtk.Label("Go to page:")
        jump_box.pack_start(jump_label, False, False, 0)
        
        self.page_spin = Gtk.SpinButton.new_with_range(1, 1, 1)
        self.page_spin.set_value(1)
        jump_box.pack_start(self.page_spin, False, False, 0)
        
        pagination_box.pack_end(jump_box, False, False, 0)
        
        self.pack_start(pagination_box, False, False, 0)
    
    def _create_status_bar(self) -> None:
        """Create status bar showing selection and filter info."""
        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        status_box.set_margin_top(2)
        status_box.set_margin_bottom(2)
        status_box.set_margin_left(10)
        status_box.set_margin_right(10)
        status_box.get_style_context().add_class("dim-label")
        
        self.selection_label = Gtk.Label()
        self.selection_label.set_halign(Gtk.Align.START)
        status_box.pack_start(self.selection_label, False, False, 0)
        
        self.filter_label = Gtk.Label()
        self.filter_label.set_halign(Gtk.Align.END)
        status_box.pack_end(self.filter_label, False, False, 0)
        
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        status_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        status_container.pack_start(separator, False, False, 0)
        status_container.pack_start(status_box, False, False, 0)
        
        self.pack_start(status_container, False, False, 0)
    
    def _connect_signals(self) -> None:
        """Connect widget signals."""
        # Selection signals
        self.select_all_button.connect('clicked', self._on_select_all_clicked)
        self.select_none_button.connect('clicked', self._on_select_none_clicked)
        
        # Bulk operation signals
        self.bulk_delete_button.connect('clicked', self._on_bulk_delete_clicked)
        self.bulk_export_button.connect('clicked', self._on_bulk_export_clicked)
        
        # View control signals
        self.items_combo.connect('changed', self._on_items_per_page_changed)
        self.refresh_button.connect('clicked', self._on_refresh_clicked)
        
        # Pagination signals
        self.first_page_button.connect('clicked', self._on_first_page_clicked)
        self.prev_page_button.connect('clicked', self._on_prev_page_clicked)
        self.next_page_button.connect('clicked', self._on_next_page_clicked)
        self.last_page_button.connect('clicked', self._on_last_page_clicked)
        self.page_spin.connect('value-changed', self._on_page_spin_changed)
        
        # Tree view signals
        selection = self.tree_view.get_selection()
        selection.connect('changed', self._on_selection_changed)
        self.tree_view.connect('row-activated', self._on_row_activated)
        self.tree_view.connect('button-press-event', self._on_button_press)
        
        # Sort model signals
        self.sort_model.connect('sort-column-changed', self._on_sort_changed)
    
    def _filter_visible_func(self, model, tree_iter, data=None) -> bool:
        """Filter function for the tree model."""
        try:
            # Get row data
            name = model.get_value(tree_iter, MaterialTableColumn.NAME.value) or ""
            material_type = model.get_value(tree_iter, MaterialTableColumn.TYPE.value) or ""
            sg = model.get_value(tree_iter, MaterialTableColumn.SPECIFIC_GRAVITY.value) or 0.0
            description = model.get_value(tree_iter, MaterialTableColumn.DESCRIPTION.value) or ""
            
            # Text filter (search in name and description)
            text_filter = self.current_filters.get('text', '').lower()
            if text_filter:
                text_match = (text_filter in name.lower() or 
                             text_filter in description.lower())
                if not text_match:
                    return False
            
            # Type filter
            type_filter = self.current_filters.get('type', 'all')
            if type_filter != 'all' and material_type != type_filter:
                return False
            
            # Specific gravity range filter
            sg_min = self.current_filters.get('sg_min', 1.0)
            sg_max = self.current_filters.get('sg_max', 5.0)
            if not (sg_min <= sg <= sg_max):
                return False
            
            return True
            
        except Exception as e:
            self.logger.warning(f"Error in filter function: {e}")
            return True
    
    def _load_materials(self) -> None:
        """Load materials data from the service."""
        try:
            # Clear existing data
            self.list_store.clear()
            self.materials_data.clear()
            
            # Load materials from all services
            materials = []
            
            # Load cement materials
            try:
                cement_service = self.service_container.cement_service
                cements = cement_service.get_all()
                for cement in cements:
                    materials.append({
                        'id': cement.name,  # Use name as ID since it's the primary key
                        'name': cement.name,
                        'type': 'cement',
                        'specific_gravity': cement.specific_gravity,
                        'created_date': cement.created_at.strftime('%Y-%m-%d') if cement.created_at else '',
                        'modified_date': cement.updated_at.strftime('%Y-%m-%d') if cement.updated_at else '',
                        'description': cement.description or '',
                        'data': cement
                    })
            except Exception as e:
                self.logger.warning(f"Error loading cement materials: {e}")
            
            # Load fly ash materials
            try:
                fly_ash_service = self.service_container.fly_ash_service
                fly_ashes = fly_ash_service.get_all()
                for fly_ash in fly_ashes:
                    materials.append({
                        'id': fly_ash.name,
                        'name': fly_ash.name,
                        'type': 'fly_ash',
                        'specific_gravity': fly_ash.specific_gravity,
                        'created_date': fly_ash.created_at.strftime('%Y-%m-%d') if fly_ash.created_at else '',
                        'modified_date': fly_ash.updated_at.strftime('%Y-%m-%d') if fly_ash.updated_at else '',
                        'description': fly_ash.description or '',
                        'data': fly_ash
                    })
            except Exception as e:
                self.logger.warning(f"Error loading fly ash materials: {e}")
            
            # Load slag materials
            try:
                slag_service = self.service_container.slag_service
                slags = slag_service.get_all()
                for slag in slags:
                    materials.append({
                        'id': slag.name,
                        'name': slag.name,
                        'type': 'slag',
                        'specific_gravity': slag.specific_gravity,
                        'created_date': slag.created_at.strftime('%Y-%m-%d') if slag.created_at else '',
                        'modified_date': slag.updated_at.strftime('%Y-%m-%d') if slag.updated_at else '',
                        'description': slag.description or '',
                        'data': slag
                    })
            except Exception as e:
                self.logger.warning(f"Error loading slag materials: {e}")
            
            # Load inert filler materials
            try:
                inert_filler_service = self.service_container.inert_filler_service
                inert_fillers = inert_filler_service.get_all()
                for inert_filler in inert_fillers:
                    materials.append({
                        'id': inert_filler.name,
                        'name': inert_filler.name,
                        'type': 'inert_filler',
                        'specific_gravity': inert_filler.specific_gravity,
                        'created_date': inert_filler.created_at.strftime('%Y-%m-%d') if inert_filler.created_at else '',
                        'modified_date': inert_filler.updated_at.strftime('%Y-%m-%d') if inert_filler.updated_at else '',
                        'description': inert_filler.description or '',
                        'data': inert_filler
                    })
            except Exception as e:
                self.logger.warning(f"Error loading inert filler materials: {e}")
            
            # Load silica fume materials
            try:
                silica_fume_service = self.service_container.silica_fume_service
                silica_fumes = silica_fume_service.get_all()
                for silica_fume in silica_fumes:
                    materials.append({
                        'id': silica_fume.name,
                        'name': silica_fume.name,
                        'type': 'silica_fume',
                        'specific_gravity': silica_fume.specific_gravity,
                        'created_date': silica_fume.created_at.strftime('%Y-%m-%d') if silica_fume.created_at else '',
                        'modified_date': silica_fume.updated_at.strftime('%Y-%m-%d') if silica_fume.updated_at else '',
                        'description': silica_fume.description or '',
                        'data': silica_fume
                    })
            except Exception as e:
                self.logger.warning(f"Error loading silica fume materials: {e}")
            
            # Load limestone materials
            try:
                limestone_service = self.service_container.limestone_service
                limestones = limestone_service.get_all()
                for limestone in limestones:
                    materials.append({
                        'id': limestone.name,
                        'name': limestone.name,
                        'type': 'limestone',
                        'specific_gravity': limestone.specific_gravity,
                        'created_date': limestone.created_at.strftime('%Y-%m-%d') if limestone.created_at else '',
                        'modified_date': limestone.updated_at.strftime('%Y-%m-%d') if limestone.updated_at else '',
                        'description': limestone.description or '',
                        'data': limestone
                    })
            except Exception as e:
                self.logger.warning(f"Error loading limestone materials: {e}")
            
            # Load aggregate materials
            try:
                aggregate_service = self.service_container.aggregate_service
                aggregates = aggregate_service.get_all()
                for aggregate in aggregates:
                    materials.append({
                        'id': aggregate.display_name,  # Use display_name as ID since it's the primary key
                        'name': aggregate.name,
                        'type': 'aggregate',
                        'specific_gravity': aggregate.specific_gravity,
                        'created_date': aggregate.created_at.strftime('%Y-%m-%d') if aggregate.created_at else '',
                        'modified_date': aggregate.updated_at.strftime('%Y-%m-%d') if aggregate.updated_at else '',
                        'description': getattr(aggregate, 'description', '') or '',
                        'data': aggregate
                    })
            except Exception as e:
                self.logger.warning(f"Error loading aggregate materials: {e}")
            
            # Store materials data
            self.materials_data = materials
            
            # Populate list store
            for material in materials:
                self.list_store.append([
                    material['name'],
                    material['type'],
                    material['specific_gravity'],
                    material['created_date'],
                    material['modified_date'],
                    material['description'],
                    material['data']
                ])
            
            # Update display
            self._update_pagination()
            self._update_status()
            
            self.logger.info(f"Loaded {len(materials)} materials")
            
        except Exception as e:
            self.logger.error(f"Error loading materials: {e}")
    
    def _update_pagination(self) -> None:
        """Update pagination controls."""
        # Calculate pagination info - count visible rows in filter model
        self.total_items = len(self.filter_model) if self.filter_model else len(self.materials_data)
        total_pages = max(1, (self.total_items + self.items_per_page - 1) // self.items_per_page)
        
        # Update page spinner
        self.page_spin.set_range(1, total_pages)
        self.page_spin.set_value(self.current_page + 1)
        
        # Update navigation buttons
        self.first_page_button.set_sensitive(self.current_page > 0)
        self.prev_page_button.set_sensitive(self.current_page > 0)
        self.next_page_button.set_sensitive(self.current_page < total_pages - 1)
        self.last_page_button.set_sensitive(self.current_page < total_pages - 1)
        
        # Update page info
        start_item = self.current_page * self.items_per_page + 1
        end_item = min((self.current_page + 1) * self.items_per_page, self.total_items)
        
        if self.total_items > 0:
            self.page_info_label.set_text(
                f"Showing {start_item}-{end_item} of {self.total_items} materials (Page {self.current_page + 1} of {total_pages})"
            )
        else:
            self.page_info_label.set_markup("<i>No materials found</i>")
    
    def _update_status(self) -> None:
        """Update status bar information."""
        # Selection status
        selected_count = len(self.selected_materials)
        if selected_count > 0:
            self.selection_label.set_text(f"{selected_count} materials selected")
            self.bulk_delete_button.set_sensitive(True)
            self.bulk_export_button.set_sensitive(True)
        else:
            self.selection_label.set_text("")
            self.bulk_delete_button.set_sensitive(False)
            self.bulk_export_button.set_sensitive(False)
        
        # Filter status
        active_filters = []
        if self.current_filters.get('text'):
            active_filters.append(f"text: '{self.current_filters['text']}'")
        if self.current_filters.get('type', 'all') != 'all':
            active_filters.append(f"type: {self.current_filters['type']}")
        
        if active_filters:
            self.filter_label.set_text(f"Filters: {', '.join(active_filters)}")
        else:
            self.filter_label.set_text("")
    
    # Signal handlers
    def _on_select_all_clicked(self, button) -> None:
        """Handle select all button click."""
        selection = self.tree_view.get_selection()
        selection.select_all()
    
    def _on_select_none_clicked(self, button) -> None:
        """Handle select none button click."""
        selection = self.tree_view.get_selection()
        selection.unselect_all()
        self.selected_materials.clear()
        self._update_status()
    
    def _on_bulk_delete_clicked(self, button) -> None:
        """Handle bulk delete button click."""
        if not self.selected_materials:
            return
        
        # Show confirmation dialog
        dialog = Gtk.MessageDialog(
            transient_for=self.main_window,
            flags=0,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.YES_NO,
            text=f"Delete {len(self.selected_materials)} selected materials?"
        )
        dialog.format_secondary_text("This action cannot be undone.")
        
        response = dialog.run()
        dialog.destroy()
        
        if response == Gtk.ResponseType.YES:
            self._delete_selected_materials()
    
    def _on_bulk_export_clicked(self, button) -> None:
        """Handle bulk export button click."""
        if not self.selected_materials:
            return
        
        # Show export dialog
        dialog = Gtk.FileChooserDialog(
            title="Export Selected Materials",
            parent=self.main_window,
            action=Gtk.FileChooserAction.SAVE
        )
        dialog.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
        dialog.add_button(Gtk.STOCK_SAVE, Gtk.ResponseType.OK)
        
        # Add file filters
        csv_filter = Gtk.FileFilter()
        csv_filter.set_name("CSV Files")
        csv_filter.add_pattern("*.csv")
        dialog.add_filter(csv_filter)
        
        json_filter = Gtk.FileFilter()
        json_filter.set_name("JSON Files")
        json_filter.add_pattern("*.json")
        dialog.add_filter(json_filter)
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            self._export_selected_materials(filename)
        
        dialog.destroy()
    
    def _on_items_per_page_changed(self, combo) -> None:
        """Handle items per page combo change."""
        self.items_per_page = int(combo.get_active_id())
        self.current_page = 0
        self._update_pagination()
    
    def _on_refresh_clicked(self, button) -> None:
        """Handle refresh button click."""
        self._load_materials()
    
    def _on_first_page_clicked(self, button) -> None:
        """Handle first page button click."""
        self.current_page = 0
        self._update_pagination()
    
    def _on_prev_page_clicked(self, button) -> None:
        """Handle previous page button click."""
        if self.current_page > 0:
            self.current_page -= 1
            self._update_pagination()
    
    def _on_next_page_clicked(self, button) -> None:
        """Handle next page button click."""
        total_pages = max(1, (self.total_items + self.items_per_page - 1) // self.items_per_page)
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self._update_pagination()
    
    def _on_last_page_clicked(self, button) -> None:
        """Handle last page button click."""
        total_pages = max(1, (self.total_items + self.items_per_page - 1) // self.items_per_page)
        self.current_page = total_pages - 1
        self._update_pagination()
    
    def _on_page_spin_changed(self, spin) -> None:
        """Handle page spinner change."""
        self.current_page = int(spin.get_value()) - 1
        self._update_pagination()
    
    def _on_selection_changed(self, selection) -> None:
        """Handle tree view selection change."""
        model, tree_paths = selection.get_selected_rows()
        self.selected_materials.clear()
        
        for path in tree_paths:
            tree_iter = model.get_iter(path)
            material_data = model.get_value(tree_iter, 6)  # material data column
            if material_data:
                # Use the correct identifier based on material type
                if hasattr(material_data, '__tablename__'):
                    if material_data.__tablename__ == 'cement':
                        material_id = material_data.name
                    elif material_data.__tablename__ == 'aggregate':
                        material_id = material_data.display_name
                    else:
                        material_id = getattr(material_data, 'id', material_data.name)
                else:
                    material_id = getattr(material_data, 'name', getattr(material_data, 'display_name', None))
                
                self.selected_materials.add(material_id)
        
        self._update_status()
        
        # Emit selection signal
        if len(tree_paths) == 1:
            tree_iter = model.get_iter(tree_paths[0])
            material_data = model.get_value(tree_iter, 6)
            self.emit('material-selected', material_data)
    
    def _on_row_activated(self, tree_view, path, column) -> None:
        """Handle row activation (double-click)."""
        model = tree_view.get_model()
        tree_iter = model.get_iter(path)
        material_data = model.get_value(tree_iter, 6)
        
        if material_data:
            self.emit('material-activated', material_data)
    
    def _on_button_press(self, tree_view, event) -> bool:
        """Handle button press events for context menu."""
        if event.button == 3:  # Right click
            path_info = tree_view.get_path_at_pos(int(event.x), int(event.y))
            if path_info:
                path, column, cell_x, cell_y = path_info
                tree_view.set_cursor(path, column, False)
                self._show_context_menu(event)
            return True
        return False
    
    def _on_sort_changed(self, model) -> None:
        """Handle sort column change."""
        sort_column_id, sort_order = model.get_sort_column_id()
        if sort_column_id is not None:
            self.sort_column = MaterialTableColumn(sort_column_id)
            self.sort_ascending = sort_order == Gtk.SortType.ASCENDING
    
    def _show_context_menu(self, event) -> None:
        """Show context menu for table rows."""
        menu = Gtk.Menu()
        
        # Edit item
        edit_item = Gtk.MenuItem(label="Edit Material")
        edit_item.connect('activate', self._on_context_edit)
        menu.append(edit_item)
        
        # Duplicate item
        duplicate_item = Gtk.MenuItem(label="Duplicate Material")
        duplicate_item.connect('activate', self._on_context_duplicate)
        menu.append(duplicate_item)
        
        menu.append(Gtk.SeparatorMenuItem())
        
        # Delete item
        delete_item = Gtk.MenuItem(label="Delete Material")
        delete_item.get_style_context().add_class("destructive-action")
        delete_item.connect('activate', self._on_context_delete)
        menu.append(delete_item)
        
        menu.append(Gtk.SeparatorMenuItem())
        
        # Export item
        export_item = Gtk.MenuItem(label="Export Material")
        export_item.connect('activate', self._on_context_export)
        menu.append(export_item)
        
        menu.show_all()
        menu.popup_at_pointer(event)
    
    def _on_context_edit(self, item) -> None:
        """Handle context menu edit action."""
        selection = self.tree_view.get_selection()
        model, tree_paths = selection.get_selected_rows()
        
        if tree_paths:
            tree_iter = model.get_iter(tree_paths[0])
            material_data = model.get_value(tree_iter, 6)
            if material_data:
                self.emit('material-activated', material_data)
    
    def _on_context_duplicate(self, item) -> None:
        """Handle context menu duplicate action."""
        selection = self.tree_view.get_selection()
        model, tree_paths = selection.get_selected_rows()
        
        if tree_paths:
            tree_iter = model.get_iter(tree_paths[0])
            material_data = model.get_value(tree_iter, 6)
            if material_data:
                # Use the parent's duplicate functionality
                try:
                    parent_panel = self.get_parent()
                    while parent_panel and not hasattr(parent_panel, '_duplicate_material'):
                        parent_panel = parent_panel.get_parent()
                    
                    if parent_panel and hasattr(parent_panel, '_duplicate_material'):
                        material_type = parent_panel._get_material_type(material_data)
                        parent_panel._duplicate_material(material_data, material_type)
                    else:
                        self.main_window.update_status("Could not access duplication functionality", "error", 3)
                except Exception as e:
                    self.logger.error(f"Error duplicating material: {e}")
                    self.main_window.update_status(f"Error duplicating material: {e}", "error", 5)
    
    def _on_context_delete(self, item) -> None:
        """Handle context menu delete action."""
        selection = self.tree_view.get_selection()
        model, tree_paths = selection.get_selected_rows()
        
        if tree_paths:
            tree_iter = model.get_iter(tree_paths[0])
            material_data = model.get_value(tree_iter, 6)
            if material_data:
                # Use the correct identifier based on material type
                if hasattr(material_data, '__tablename__'):
                    if material_data.__tablename__ == 'cement':
                        material_id = material_data.name
                    elif material_data.__tablename__ == 'aggregate':
                        material_id = material_data.display_name
                    else:
                        material_id = getattr(material_data, 'id', material_data.name)
                else:
                    material_id = getattr(material_data, 'name', getattr(material_data, 'display_name', None))
                
                self.selected_materials = {material_id}
                self._on_bulk_delete_clicked(None)
    
    def _on_context_export(self, item) -> None:
        """Handle context menu export action."""
        selection = self.tree_view.get_selection()
        model, tree_paths = selection.get_selected_rows()
        
        if tree_paths:
            tree_iter = model.get_iter(tree_paths[0])
            material_data = model.get_value(tree_iter, 6)
            if material_data:
                # Use the correct identifier based on material type
                if hasattr(material_data, '__tablename__'):
                    if material_data.__tablename__ == 'cement':
                        material_id = material_data.name
                    elif material_data.__tablename__ == 'aggregate':
                        material_id = material_data.display_name
                    else:
                        material_id = getattr(material_data, 'id', material_data.name)
                else:
                    material_id = getattr(material_data, 'name', getattr(material_data, 'display_name', None))
                
                self.selected_materials = {material_id}
                self._on_bulk_export_clicked(None)
    
    def _delete_selected_materials(self) -> None:
        """Delete the selected materials."""
        try:
            deleted_count = 0
            
            for material_id in self.selected_materials:
                # Find the material in our data
                material_data = None
                for material in self.materials_data:
                    data_obj = material['data']
                    # Check the correct identifier based on material type
                    if material['type'] == 'cement' and getattr(data_obj, 'name', None) == material_id:
                        material_data = material
                        break
                    elif material['type'] == 'aggregate' and getattr(data_obj, 'display_name', None) == material_id:
                        material_data = material
                        break
                    elif material['type'] in ['limestone', 'silica_fume'] and getattr(data_obj, 'name', None) == material_id:
                        material_data = material
                        break
                    elif getattr(data_obj, 'id', None) == material_id:
                        material_data = material
                        break
                
                if material_data:
                    material_type = material_data['type']
                    
                    # Delete from appropriate service
                    if material_type == 'cement':
                        service = self.service_container.cement_service
                    elif material_type == 'aggregate':
                        service = self.service_container.aggregate_service
                    elif material_type == 'fly_ash':
                        service = self.service_container.fly_ash_service
                    elif material_type == 'slag':
                        service = self.service_container.slag_service
                    elif material_type == 'inert_filler':
                        service = self.service_container.inert_filler_service
                    elif material_type == 'silica_fume':
                        service = self.service_container.silica_fume_service
                    elif material_type == 'limestone':
                        service = self.service_container.limestone_service
                    else:
                        continue
                    
                    # Delete using the material_id (which is the correct identifier for each type)
                    service.delete(material_id)
                    deleted_count += 1
            
            # Clear selection and reload
            self.selected_materials.clear()
            self._load_materials()
            
            self.main_window.update_status(f"Deleted {deleted_count} materials", "success", 3)
            self.emit('materials-changed')
            
        except Exception as e:
            self.logger.error(f"Error deleting materials: {e}")
            self.main_window.update_status(f"Error deleting materials: {e}", "error", 5)
    
    def _export_selected_materials(self, filename: str) -> None:
        """Export selected materials to file."""
        try:
            # Get selected material data
            selected_data = []
            for material_id in self.selected_materials:
                for material in self.materials_data:
                    if material['data'].id == material_id:
                        selected_data.append(material)
                        break
            
            file_path = Path(filename)
            
            if file_path.suffix.lower() == '.csv':
                self._export_to_csv(selected_data, file_path)
            elif file_path.suffix.lower() == '.json':
                self._export_to_json(selected_data, file_path)
            else:
                raise ValueError("Unsupported file format")
            
            self.main_window.update_status(f"Exported {len(selected_data)} materials to {file_path.name}", "success", 3)
            
        except Exception as e:
            self.logger.error(f"Error exporting materials: {e}")
            self.main_window.update_status(f"Error exporting materials: {e}", "error", 5)
    
    def _export_to_csv(self, materials: List[Dict], file_path: Path) -> None:
        """Export materials to CSV format."""
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            writer.writerow(['Name', 'Type', 'Specific Gravity', 'Created Date', 'Modified Date', 'Description'])
            
            # Write data
            for material in materials:
                writer.writerow([
                    material['name'],
                    material['type'],
                    material['specific_gravity'],
                    material['created_date'],
                    material['modified_date'],
                    material['description']
                ])
    
    def _export_to_json(self, materials: List[Dict], file_path: Path) -> None:
        """Export materials to JSON format."""
        export_data = []
        
        for material in materials:
            # Create a serializable version of the material data
            material_dict = {
                'name': material['name'],
                'type': material['type'],
                'specific_gravity': material['specific_gravity'],
                'created_date': material['created_date'],
                'modified_date': material['modified_date'],
                'description': material['description']
            }
            export_data.append(material_dict)
        
        with open(file_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(export_data, jsonfile, indent=2, ensure_ascii=False)
    
    # Public API methods
    def apply_filters(self, filters: Dict[str, Any]) -> None:
        """Apply filters to the table."""
        self.current_filters.update(filters)
        self.filter_model.refilter()
        self.current_page = 0
        self._update_pagination()
        self._update_status()
    
    def clear_filters(self) -> None:
        """Clear all filters."""
        self.current_filters = {
            'text': '',
            'type': 'all',
            'sg_min': 1.0,
            'sg_max': 5.0
        }
        self.filter_model.refilter()
        self.current_page = 0
        self._update_pagination()
        self._update_status()
    
    def refresh_data(self) -> None:
        """Refresh the table data."""
        self._load_materials()
    
    def get_selected_materials(self) -> List[Any]:
        """Get the currently selected materials."""
        selected_data = []
        for material_id in self.selected_materials:
            for material in self.materials_data:
                if material['data'].id == material_id:
                    selected_data.append(material['data'])
                    break
        return selected_data
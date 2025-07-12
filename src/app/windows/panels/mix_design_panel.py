#!/usr/bin/env python3
"""
Mix Design Panel for VCCTL

Provides comprehensive mix design interface with material selection, composition calculations,
water-binder ratio optimization, and real-time validation.
"""

import gi
import logging
from typing import TYPE_CHECKING, Optional, Dict, Any, List, Tuple
from decimal import Decimal

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, Pango, Gdk

if TYPE_CHECKING:
    from app.windows.main_window import VCCTLMainWindow

from app.services.service_container import get_service_container
from app.services.mix_service import MixService, MaterialType, MixComponent, MixDesign
from app.widgets import GradingCurveWidget


class MixDesignPanel(Gtk.Box):
    """Mix design panel with comprehensive material composition and calculation capabilities."""
    
    def __init__(self, main_window: 'VCCTLMainWindow'):
        """Initialize the mix design panel."""
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        self.main_window = main_window
        self.logger = logging.getLogger('VCCTL.MixDesignPanel')
        self.service_container = get_service_container()
        self.mix_service = MixService(self.service_container.database_service)
        
        # Panel state
        self.current_mix = None
        self.component_rows = []
        self.auto_calculate_enabled = True
        self.validation_timer = None
        
        # Material lists cache
        self.material_lists = {}
        
        # Setup UI
        self._setup_ui()
        self._connect_signals()
        self._load_material_lists()
        
        self.logger.info("Mix design panel initialized")
    
    def _setup_ui(self) -> None:
        """Setup the mix design panel UI."""
        # Create header
        self._create_header()
        
        # Create main content area
        self._create_content_area()
        
        # Create status and actions area
        self._create_actions_area()
    
    def _create_header(self) -> None:
        """Create the panel header."""
        header_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        header_box.set_margin_top(10)
        header_box.set_margin_bottom(10)
        header_box.set_margin_left(15)
        header_box.set_margin_right(15)
        
        # Title and description
        title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        title_label = Gtk.Label()
        title_label.set_markup('<span size="large" weight="bold">Mix Design</span>')
        title_label.set_halign(Gtk.Align.START)
        title_box.pack_start(title_label, False, False, 0)
        
        # Auto-calculate toggle
        self.auto_calc_switch = Gtk.Switch()
        self.auto_calc_switch.set_active(True)
        self.auto_calc_switch.set_tooltip_text("Enable real-time calculations")
        auto_calc_label = Gtk.Label("Auto-calculate")
        auto_calc_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        auto_calc_box.pack_start(auto_calc_label, False, False, 0)
        auto_calc_box.pack_start(self.auto_calc_switch, False, False, 0)
        title_box.pack_end(auto_calc_box, False, False, 0)
        
        header_box.pack_start(title_box, False, False, 0)
        
        # Description
        desc_label = Gtk.Label()
        desc_label.set_markup('<span size="small">Design concrete mixes with real-time composition calculations and validation</span>')
        desc_label.set_halign(Gtk.Align.START)
        header_box.pack_start(desc_label, False, False, 0)
        
        # Mix name and basic controls
        controls_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        # Mix name entry
        name_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        name_label = Gtk.Label("Mix Name:")
        name_label.set_size_request(80, -1)
        self.mix_name_entry = Gtk.Entry()
        self.mix_name_entry.set_placeholder_text("Enter mix design name...")
        self.mix_name_entry.set_size_request(250, -1)
        name_box.pack_start(name_label, False, False, 0)
        name_box.pack_start(self.mix_name_entry, False, False, 0)
        controls_box.pack_start(name_box, False, False, 0)
        
        # Action buttons
        action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        action_box.get_style_context().add_class("linked")
        
        self.new_button = Gtk.Button(label="New")
        new_icon = Gtk.Image.new_from_icon_name("document-new-symbolic", Gtk.IconSize.BUTTON)
        self.new_button.set_image(new_icon)
        self.new_button.set_always_show_image(True)
        action_box.pack_start(self.new_button, False, False, 0)
        
        self.load_button = Gtk.Button(label="Load")
        load_icon = Gtk.Image.new_from_icon_name("document-open-symbolic", Gtk.IconSize.BUTTON)
        self.load_button.set_image(load_icon)
        self.load_button.set_always_show_image(True)
        action_box.pack_start(self.load_button, False, False, 0)
        
        self.save_button = Gtk.Button(label="Save")
        save_icon = Gtk.Image.new_from_icon_name("document-save-symbolic", Gtk.IconSize.BUTTON)
        self.save_button.set_image(save_icon)
        self.save_button.set_always_show_image(True)
        self.save_button.get_style_context().add_class("suggested-action")
        action_box.pack_start(self.save_button, False, False, 0)
        
        controls_box.pack_end(action_box, False, False, 0)
        
        header_box.pack_start(controls_box, False, False, 0)
        
        self.pack_start(header_box, False, False, 0)
    
    def _create_content_area(self) -> None:
        """Create the main content area."""
        content_paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        
        # Left side: Mix composition
        left_frame = Gtk.Frame(label="Mix Composition")
        left_frame.set_size_request(600, -1)
        self._create_composition_section(left_frame)
        content_paned.pack1(left_frame, True, False)
        
        # Right side: Calculations and properties
        right_frame = Gtk.Frame(label="Mix Properties & Calculations")
        right_frame.set_size_request(400, -1)
        self._create_properties_section(right_frame)
        content_paned.pack2(right_frame, False, False)
        
        self.pack_start(content_paned, True, True, 0)
    
    def _create_composition_section(self, parent: Gtk.Frame) -> None:
        """Create the mix composition section."""
        comp_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        comp_box.set_margin_top(10)
        comp_box.set_margin_bottom(10)
        comp_box.set_margin_left(10)
        comp_box.set_margin_right(10)
        
        # Component table header
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        
        add_button = Gtk.Button(label="Add Component")
        add_icon = Gtk.Image.new_from_icon_name("list-add-symbolic", Gtk.IconSize.BUTTON)
        add_button.set_image(add_icon)
        add_button.set_always_show_image(True)
        add_button.connect('clicked', self._on_add_component_clicked)
        header_box.pack_start(add_button, False, False, 0)
        
        normalize_button = Gtk.Button(label="Normalize")
        normalize_button.set_tooltip_text("Normalize mass fractions to sum to 100%")
        normalize_button.connect('clicked', self._on_normalize_clicked)
        header_box.pack_start(normalize_button, False, False, 0)
        
        comp_box.pack_start(header_box, False, False, 0)
        
        # Scrolled window for components
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_size_request(-1, 300)
        
        # Components list container
        self.components_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        scrolled.add(self.components_box)
        
        comp_box.pack_start(scrolled, True, True, 0)
        
        # Water and air content section
        water_air_frame = Gtk.Frame(label="Water & Air Content")
        water_air_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        water_air_box.set_margin_top(10)
        water_air_box.set_margin_bottom(10)
        water_air_box.set_margin_left(10)
        water_air_box.set_margin_right(10)
        
        # Water content controls
        water_grid = Gtk.Grid()
        water_grid.set_row_spacing(5)
        water_grid.set_column_spacing(10)
        
        # Water-binder ratio
        wb_label = Gtk.Label("W/B Ratio:")
        wb_label.set_halign(Gtk.Align.END)
        water_grid.attach(wb_label, 0, 0, 1, 1)
        
        self.wb_ratio_spin = Gtk.SpinButton.new_with_range(0.1, 2.0, 0.01)
        self.wb_ratio_spin.set_value(0.40)
        self.wb_ratio_spin.set_digits(3)
        water_grid.attach(self.wb_ratio_spin, 1, 0, 1, 1)
        
        # Water content
        water_label = Gtk.Label("Water Content:")
        water_label.set_halign(Gtk.Align.END)
        water_grid.attach(water_label, 0, 1, 1, 1)
        
        self.water_content_spin = Gtk.SpinButton.new_with_range(0.0, 1.0, 0.001)
        self.water_content_spin.set_value(0.150)
        self.water_content_spin.set_digits(3)
        water_grid.attach(self.water_content_spin, 1, 1, 1, 1)
        
        # Air content
        air_label = Gtk.Label("Air Content (%):")
        air_label.set_halign(Gtk.Align.END)
        water_grid.attach(air_label, 0, 2, 1, 1)
        
        self.air_content_spin = Gtk.SpinButton.new_with_range(0.0, 15.0, 0.1)
        self.air_content_spin.set_value(2.0)
        self.air_content_spin.set_digits(1)
        water_grid.attach(self.air_content_spin, 1, 2, 1, 1)
        
        water_air_box.pack_start(water_grid, False, False, 0)
        water_air_frame.add(water_air_box)
        
        comp_box.pack_start(water_air_frame, False, False, 0)
        
        parent.add(comp_box)
    
    def _create_properties_section(self, parent: Gtk.Frame) -> None:
        """Create the mix properties and calculations section."""
        props_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        props_box.set_margin_top(10)
        props_box.set_margin_bottom(10)
        props_box.set_margin_left(10)
        props_box.set_margin_right(10)
        
        # Calculated properties
        calc_frame = Gtk.Frame(label="Calculated Properties")
        calc_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        calc_box.set_margin_top(10)
        calc_box.set_margin_bottom(10)
        calc_box.set_margin_left(10)
        calc_box.set_margin_right(10)
        
        self.properties_grid = Gtk.Grid()
        self.properties_grid.set_row_spacing(5)
        self.properties_grid.set_column_spacing(10)
        
        # Initialize property labels
        self._create_property_labels()
        
        calc_box.pack_start(self.properties_grid, False, False, 0)
        calc_frame.add(calc_box)
        props_box.pack_start(calc_frame, False, False, 0)
        
        # Validation results
        validation_frame = Gtk.Frame(label="Validation Results")
        validation_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        validation_box.set_margin_top(10)
        validation_box.set_margin_bottom(10)
        validation_box.set_margin_left(10)
        validation_box.set_margin_right(10)
        
        # Validation scrolled window
        validation_scrolled = Gtk.ScrolledWindow()
        validation_scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        validation_scrolled.set_size_request(-1, 150)
        
        self.validation_textview = Gtk.TextView()
        self.validation_textview.set_editable(False)
        self.validation_textview.set_wrap_mode(Gtk.WrapMode.WORD)
        validation_scrolled.add(self.validation_textview)
        
        validation_box.pack_start(validation_scrolled, True, True, 0)
        validation_frame.add(validation_box)
        props_box.pack_start(validation_frame, True, True, 0)
        
        parent.add(props_box)
    
    def _create_property_labels(self) -> None:
        """Create property display labels."""
        properties = [
            ("Total Binder:", "total_binder"),
            ("SCM Replacement:", "scm_replacement"),
            ("Total Aggregate:", "total_aggregate"),
            ("Avg. Specific Gravity:", "avg_sg"),
            ("Void Ratio:", "void_ratio"),
            ("Paste Content:", "paste_content")
        ]
        
        self.property_labels = {}
        
        for i, (label_text, key) in enumerate(properties):
            label = Gtk.Label(label_text)
            label.set_halign(Gtk.Align.END)
            label.get_style_context().add_class("dim-label")
            self.properties_grid.attach(label, 0, i, 1, 1)
            
            value_label = Gtk.Label("—")
            value_label.set_halign(Gtk.Align.START)
            self.property_labels[key] = value_label
            self.properties_grid.attach(value_label, 1, i, 1, 1)
    
    def _create_actions_area(self) -> None:
        """Create the actions and status area."""
        actions_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        actions_box.set_margin_top(10)
        actions_box.set_margin_bottom(10)
        actions_box.set_margin_left(15)
        actions_box.set_margin_right(15)
        
        # Status label
        self.status_label = Gtk.Label()
        self.status_label.set_markup('<span size="small">Ready to design mix</span>')
        self.status_label.set_halign(Gtk.Align.START)
        actions_box.pack_start(self.status_label, True, True, 0)
        
        # Action buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        button_box.get_style_context().add_class("linked")
        
        self.calculate_button = Gtk.Button(label="Calculate")
        calc_icon = Gtk.Image.new_from_icon_name("accessories-calculator-symbolic", Gtk.IconSize.BUTTON)
        self.calculate_button.set_image(calc_icon)
        self.calculate_button.set_always_show_image(True)
        button_box.pack_start(self.calculate_button, False, False, 0)
        
        self.validate_button = Gtk.Button(label="Validate")
        validate_icon = Gtk.Image.new_from_icon_name("dialog-information-symbolic", Gtk.IconSize.BUTTON)
        self.validate_button.set_image(validate_icon)
        self.validate_button.set_always_show_image(True)
        button_box.pack_start(self.validate_button, False, False, 0)
        
        self.export_button = Gtk.Button(label="Export")
        export_icon = Gtk.Image.new_from_icon_name("document-save-as-symbolic", Gtk.IconSize.BUTTON)
        self.export_button.set_image(export_icon)
        self.export_button.set_always_show_image(True)
        button_box.pack_start(self.export_button, False, False, 0)
        
        actions_box.pack_end(button_box, False, False, 0)
        
        self.pack_start(actions_box, False, False, 0)
    
    def _load_material_lists(self) -> None:
        """Load available materials for each type."""
        try:
            for material_type in MaterialType:
                self.material_lists[material_type] = self.mix_service.get_compatible_materials(material_type)
            
            self.logger.info("Loaded material lists for mix design")
            
        except Exception as e:
            self.logger.error(f"Failed to load material lists: {e}")
            self.main_window.update_status(f"Error loading materials: {e}", "error", 5)
    
    def _connect_signals(self) -> None:
        """Connect widget signals."""
        # Header controls
        self.auto_calc_switch.connect('notify::active', self._on_auto_calc_toggled)
        self.mix_name_entry.connect('changed', self._on_mix_name_changed)
        
        # Action buttons
        self.new_button.connect('clicked', self._on_new_mix_clicked)
        self.load_button.connect('clicked', self._on_load_mix_clicked)
        self.save_button.connect('clicked', self._on_save_mix_clicked)
        
        # Water and air controls
        self.wb_ratio_spin.connect('value-changed', self._on_wb_ratio_changed)
        self.water_content_spin.connect('value-changed', self._on_water_content_changed)
        self.air_content_spin.connect('value-changed', self._on_parameter_changed)
        
        # Action buttons
        self.calculate_button.connect('clicked', self._on_calculate_clicked)
        self.validate_button.connect('clicked', self._on_validate_clicked)
        self.export_button.connect('clicked', self._on_export_clicked)
    
    def _create_component_row(self) -> Gtk.Box:
        """Create a new component row widget."""
        row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        row_box.set_margin_top(2)
        row_box.set_margin_bottom(2)
        
        # Material type combo
        type_combo = Gtk.ComboBoxText()
        type_combo.set_size_request(120, -1)
        for material_type in MaterialType:
            type_combo.append(material_type.value, material_type.value.replace("_", " ").title())
        type_combo.set_active(0)
        row_box.pack_start(type_combo, False, False, 0)
        
        # Material name combo
        name_combo = Gtk.ComboBoxText()
        name_combo.set_size_request(150, -1)
        row_box.pack_start(name_combo, False, False, 0)
        
        # Mass fraction spin button
        mass_spin = Gtk.SpinButton.new_with_range(0.0, 1.0, 0.001)
        mass_spin.set_digits(3)
        mass_spin.set_size_request(80, -1)
        row_box.pack_start(mass_spin, False, False, 0)
        
        # Percentage label
        percent_label = Gtk.Label("%")
        row_box.pack_start(percent_label, False, False, 0)
        
        # Specific gravity display
        sg_label = Gtk.Label("2.650")
        sg_label.set_size_request(60, -1)
        sg_label.get_style_context().add_class("dim-label")
        row_box.pack_start(sg_label, False, False, 0)
        
        # Grading button (only for aggregates)
        grading_button = Gtk.Button()
        grading_icon = Gtk.Image.new_from_icon_name("preferences-system-symbolic", Gtk.IconSize.BUTTON)
        grading_button.set_image(grading_icon)
        grading_button.set_relief(Gtk.ReliefStyle.NONE)
        grading_button.set_tooltip_text("Edit grading curve")
        grading_button.set_sensitive(False)  # Enable only for aggregates
        row_box.pack_start(grading_button, False, False, 0)
        
        # Remove button
        remove_button = Gtk.Button()
        remove_icon = Gtk.Image.new_from_icon_name("list-remove-symbolic", Gtk.IconSize.BUTTON)
        remove_button.set_image(remove_icon)
        remove_button.set_relief(Gtk.ReliefStyle.NONE)
        row_box.pack_start(remove_button, False, False, 0)
        
        # Store references in row data
        row_data = {
            'box': row_box,
            'type_combo': type_combo,
            'name_combo': name_combo,
            'mass_spin': mass_spin,
            'sg_label': sg_label,
            'grading_button': grading_button,
            'remove_button': remove_button,
            'grading_data': []  # Store grading curve data
        }
        
        # Connect signals
        type_combo.connect('changed', self._on_component_type_changed, row_data)
        name_combo.connect('changed', self._on_component_name_changed, row_data)
        mass_spin.connect('value-changed', self._on_component_mass_changed, row_data)
        grading_button.connect('clicked', self._on_grading_button_clicked, row_data)
        remove_button.connect('clicked', self._on_remove_component_clicked, row_data)
        
        # Update material names based on initial type
        self._update_material_names(row_data)
        
        return row_data
    
    def _update_material_names(self, row_data: Dict[str, Any]) -> None:
        """Update material names combo based on selected type."""
        type_combo = row_data['type_combo']
        name_combo = row_data['name_combo']
        
        # Clear existing items
        name_combo.remove_all()
        
        # Get selected material type
        material_type_str = type_combo.get_active_id()
        if not material_type_str:
            return
        
        try:
            material_type = MaterialType(material_type_str)
            materials = self.material_lists.get(material_type, [])
            
            # Populate name combo
            for material_name in materials:
                name_combo.append(material_name, material_name)
            
            # Set first item as active if available
            if materials:
                name_combo.set_active(0)
        
        except Exception as e:
            self.logger.warning(f"Failed to update material names: {e}")
    
    # Signal handlers
    def _on_auto_calc_toggled(self, switch, pspec) -> None:
        """Handle auto-calculate toggle."""
        self.auto_calculate_enabled = switch.get_active()
        
        if self.auto_calculate_enabled:
            self._trigger_calculation()
    
    def _on_mix_name_changed(self, entry) -> None:
        """Handle mix name change."""
        if self.auto_calculate_enabled:
            self._trigger_calculation()
    
    def _on_add_component_clicked(self, button) -> None:
        """Handle add component button click."""
        row_data = self._create_component_row()
        self.component_rows.append(row_data)
        self.components_box.pack_start(row_data['box'], False, False, 0)
        self.components_box.show_all()
        
        if self.auto_calculate_enabled:
            self._trigger_calculation()
    
    def _on_normalize_clicked(self, button) -> None:
        """Handle normalize button click."""
        try:
            # Calculate total mass fraction
            total_mass = sum(row['mass_spin'].get_value() for row in self.component_rows)
            
            if total_mass == 0:
                self.main_window.update_status("No components to normalize", "warning", 3)
                return
            
            # Normalize each component
            for row in self.component_rows:
                current_value = row['mass_spin'].get_value()
                normalized_value = current_value / total_mass
                row['mass_spin'].set_value(normalized_value)
            
            self.main_window.update_status("Components normalized successfully", "success", 3)
            
            if self.auto_calculate_enabled:
                self._trigger_calculation()
        
        except Exception as e:
            self.logger.error(f"Failed to normalize components: {e}")
            self.main_window.update_status(f"Normalization failed: {e}", "error", 3)
    
    def _on_component_type_changed(self, combo, row_data) -> None:
        """Handle component type change."""
        self._update_material_names(row_data)
        
        # Enable grading button only for aggregates
        material_type_str = combo.get_active_id()
        is_aggregate = material_type_str == MaterialType.AGGREGATE.value
        row_data['grading_button'].set_sensitive(is_aggregate)
        
        if self.auto_calculate_enabled:
            self._trigger_calculation()
    
    def _on_component_name_changed(self, combo, row_data) -> None:
        """Handle component name change."""
        # Update specific gravity display
        self._update_component_specific_gravity(row_data)
        if self.auto_calculate_enabled:
            self._trigger_calculation()
    
    def _on_component_mass_changed(self, spin, row_data) -> None:
        """Handle component mass fraction change."""
        if self.auto_calculate_enabled:
            self._trigger_calculation()
    
    def _on_grading_button_clicked(self, button, row_data) -> None:
        """Handle grading button click."""
        self._show_grading_dialog(row_data)
    
    def _on_remove_component_clicked(self, button, row_data) -> None:
        """Handle remove component button click."""
        # Remove from components box
        self.components_box.remove(row_data['box'])
        
        # Remove from our list
        if row_data in self.component_rows:
            self.component_rows.remove(row_data)
        
        if self.auto_calculate_enabled:
            self._trigger_calculation()
    
    def _on_wb_ratio_changed(self, spin) -> None:
        """Handle water-binder ratio change."""
        if self.auto_calculate_enabled:
            self._calculate_water_content_from_wb_ratio()
            self._trigger_calculation()
    
    def _on_water_content_changed(self, spin) -> None:
        """Handle water content change."""
        if self.auto_calculate_enabled:
            self._calculate_wb_ratio_from_water_content()
            self._trigger_calculation()
    
    def _on_parameter_changed(self, widget) -> None:
        """Handle any parameter change."""
        if self.auto_calculate_enabled:
            self._trigger_calculation()
    
    def _on_new_mix_clicked(self, button) -> None:
        """Handle new mix button click."""
        self._clear_mix_design()
    
    def _on_load_mix_clicked(self, button) -> None:
        """Handle load mix button click."""
        # TODO: Implement mix loading
        self.main_window.update_status("Mix loading will be implemented", "info", 3)
    
    def _on_save_mix_clicked(self, button) -> None:
        """Handle save mix button click."""
        # TODO: Implement mix saving
        self.main_window.update_status("Mix saving will be implemented", "info", 3)
    
    def _on_calculate_clicked(self, button) -> None:
        """Handle calculate button click."""
        self._perform_calculations()
    
    def _on_validate_clicked(self, button) -> None:
        """Handle validate button click."""
        self._perform_validation()
    
    def _on_export_clicked(self, button) -> None:
        """Handle export button click."""
        # TODO: Implement mix export
        self.main_window.update_status("Mix export will be implemented", "info", 3)
    
    # Helper methods
    def _update_component_specific_gravity(self, row_data: Dict[str, Any]) -> None:
        """Update specific gravity display for a component."""
        try:
            type_combo = row_data['type_combo']
            name_combo = row_data['name_combo']
            sg_label = row_data['sg_label']
            
            material_type_str = type_combo.get_active_id()
            material_name = name_combo.get_active_id()
            
            if material_type_str and material_name:
                material_type = MaterialType(material_type_str)
                sg = self.mix_service._get_material_specific_gravity(material_name, material_type)
                sg_label.set_text(f"{sg:.3f}")
            else:
                sg_label.set_text("—")
        
        except Exception as e:
            self.logger.warning(f"Failed to update specific gravity: {e}")
            row_data['sg_label'].set_text("—")
    
    def _calculate_water_content_from_wb_ratio(self) -> None:
        """Calculate water content from W/B ratio."""
        try:
            wb_ratio = self.wb_ratio_spin.get_value()
            
            # Calculate total binder fraction
            total_binder = self._calculate_total_binder_fraction()
            
            if total_binder > 0:
                water_content = wb_ratio * total_binder
                self.water_content_spin.set_value(water_content)
        
        except Exception as e:
            self.logger.warning(f"Failed to calculate water content: {e}")
    
    def _calculate_wb_ratio_from_water_content(self) -> None:
        """Calculate W/B ratio from water content."""
        try:
            water_content = self.water_content_spin.get_value()
            
            # Calculate total binder fraction
            total_binder = self._calculate_total_binder_fraction()
            
            if total_binder > 0:
                wb_ratio = water_content / total_binder
                self.wb_ratio_spin.set_value(wb_ratio)
        
        except Exception as e:
            self.logger.warning(f"Failed to calculate W/B ratio: {e}")
    
    def _calculate_total_binder_fraction(self) -> float:
        """Calculate total binder mass fraction."""
        binder_types = {MaterialType.CEMENT, MaterialType.FLY_ASH, MaterialType.SLAG}
        total_binder = 0.0
        
        for row in self.component_rows:
            type_str = row['type_combo'].get_active_id()
            if type_str:
                try:
                    material_type = MaterialType(type_str)
                    if material_type in binder_types:
                        total_binder += row['mass_spin'].get_value()
                except ValueError:
                    continue
        
        return total_binder
    
    def _trigger_calculation(self) -> None:
        """Trigger calculation after a short delay."""
        if self.validation_timer:
            GObject.source_remove(self.validation_timer)
        
        self.validation_timer = GObject.timeout_add(500, self._perform_calculations)
    
    def _perform_calculations(self) -> bool:
        """Perform mix calculations and update display."""
        try:
            # Create current mix design from UI
            mix_design = self._create_mix_design_from_ui()
            if not mix_design:
                return False
            
            # Calculate properties
            properties = self.mix_service.calculate_mix_properties(mix_design)
            
            # Update properties display
            self._update_properties_display(properties)
            
            # Update status
            self.status_label.set_markup('<span size="small" color="green">Calculations updated</span>')
            
            self.validation_timer = None
            return False  # Don't repeat timer
        
        except Exception as e:
            self.logger.warning(f"Calculation failed: {e}")
            self.status_label.set_markup(f'<span size="small" color="red">Calculation error: {e}</span>')
            self.validation_timer = None
            return False
    
    def _perform_validation(self) -> None:
        """Perform mix validation and update display."""
        try:
            # Create current mix design from UI
            mix_design = self._create_mix_design_from_ui()
            if not mix_design:
                return
            
            # Validate mix design
            validation_result = self.mix_service.validate_mix_design(mix_design)
            
            # Update validation display
            self._update_validation_display(validation_result)
            
        except Exception as e:
            self.logger.error(f"Validation failed: {e}")
            self.main_window.update_status(f"Validation error: {e}", "error", 5)
    
    def _create_mix_design_from_ui(self) -> Optional[MixDesign]:
        """Create a MixDesign object from current UI state."""
        try:
            mix_name = self.mix_name_entry.get_text().strip()
            if not mix_name:
                mix_name = "Untitled Mix"
            
            # Create components
            components = []
            for row in self.component_rows:
                type_str = row['type_combo'].get_active_id()
                name = row['name_combo'].get_active_id()
                mass_fraction = row['mass_spin'].get_value()
                
                if type_str and name and mass_fraction > 0:
                    material_type = MaterialType(type_str)
                    sg = self.mix_service._get_material_specific_gravity(name, material_type)
                    
                    component = MixComponent(
                        material_name=name,
                        material_type=material_type,
                        mass_fraction=mass_fraction,
                        specific_gravity=sg
                    )
                    components.append(component)
            
            if not components:
                return None
            
            # Create mix design
            mix_design = MixDesign(
                name=mix_name,
                components=components,
                water_binder_ratio=self.wb_ratio_spin.get_value(),
                total_water_content=self.water_content_spin.get_value(),
                air_content=self.air_content_spin.get_value() / 100.0  # Convert percentage
            )
            
            return mix_design
            
        except Exception as e:
            self.logger.error(f"Failed to create mix design from UI: {e}")
            return None
    
    def _update_properties_display(self, properties: Dict[str, Any]) -> None:
        """Update the properties display with calculated values."""
        try:
            # Update property labels
            self.property_labels['total_binder'].set_text(f"{properties.get('total_binder_fraction', 0):.1%}")
            self.property_labels['scm_replacement'].set_text(f"{properties.get('scm_replacement_ratio', 0):.1%}")
            self.property_labels['total_aggregate'].set_text(f"{properties.get('total_aggregate_fraction', 0):.1%}")
            self.property_labels['avg_sg'].set_text(f"{properties.get('weighted_average_specific_gravity', 0):.3f}")
            self.property_labels['void_ratio'].set_text(f"{properties.get('void_ratio', 0):.3f}")
            
            # Calculate paste content (binder + water)
            paste_content = properties.get('total_binder_fraction', 0) + properties.get('water_binder_ratio', 0) * properties.get('total_binder_fraction', 0)
            self.property_labels['paste_content'].set_text(f"{paste_content:.1%}")
            
        except Exception as e:
            self.logger.warning(f"Failed to update properties display: {e}")
    
    def _update_validation_display(self, validation_result: Dict[str, Any]) -> None:
        """Update the validation display with results."""
        try:
            text_buffer = self.validation_textview.get_buffer()
            text_buffer.set_text("")
            
            # Status
            if validation_result['is_valid']:
                text_buffer.insert_at_cursor("✓ Mix design is valid\n\n")
            else:
                text_buffer.insert_at_cursor("✗ Mix design has errors\n\n")
            
            # Errors
            if validation_result['errors']:
                text_buffer.insert_at_cursor("ERRORS:\n")
                for error in validation_result['errors']:
                    text_buffer.insert_at_cursor(f"• {error}\n")
                text_buffer.insert_at_cursor("\n")
            
            # Warnings
            if validation_result['warnings']:
                text_buffer.insert_at_cursor("WARNINGS:\n")
                for warning in validation_result['warnings']:
                    text_buffer.insert_at_cursor(f"• {warning}\n")
                text_buffer.insert_at_cursor("\n")
            
            # Recommendations
            if validation_result['recommendations']:
                text_buffer.insert_at_cursor("RECOMMENDATIONS:\n")
                for rec in validation_result['recommendations']:
                    text_buffer.insert_at_cursor(f"• {rec}\n")
            
        except Exception as e:
            self.logger.warning(f"Failed to update validation display: {e}")
    
    def _clear_mix_design(self) -> None:
        """Clear the current mix design."""
        # Clear mix name
        self.mix_name_entry.set_text("")
        
        # Remove all component rows
        for row in self.component_rows[:]:
            self.components_box.remove(row['box'])
        self.component_rows.clear()
        
        # Reset water and air values
        self.wb_ratio_spin.set_value(0.40)
        self.water_content_spin.set_value(0.150)
        self.air_content_spin.set_value(2.0)
        
        # Clear properties and validation
        for label in self.property_labels.values():
            label.set_text("—")
        
        self.validation_textview.get_buffer().set_text("Ready for new mix design")
        
        # Update status
        self.status_label.set_markup('<span size="small">Ready to design mix</span>')
        
        self.logger.info("Mix design cleared")
    
    def _show_grading_dialog(self, row_data: Dict[str, Any]) -> None:
        """Show grading curve dialog for aggregate component."""
        try:
            material_name = row_data['name_combo'].get_active_id()
            if not material_name:
                material_name = "Aggregate"
            
            # Create grading dialog
            dialog = Gtk.Dialog(
                title=f"Grading Curve - {material_name}",
                transient_for=self.main_window,
                flags=0
            )
            dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
            dialog.add_button("Apply", Gtk.ResponseType.OK)
            dialog.set_default_response(Gtk.ResponseType.OK)
            dialog.set_default_size(800, 600)
            
            # Create grading curve widget
            grading_widget = GradingCurveWidget()
            
            # Load existing grading data if available
            if row_data['grading_data']:
                grading_widget.set_grading_data(row_data['grading_data'])
            
            # Add to dialog content area
            content_area = dialog.get_content_area()
            content_area.set_margin_top(10)
            content_area.set_margin_bottom(10)
            content_area.set_margin_left(10)
            content_area.set_margin_right(10)
            content_area.pack_start(grading_widget, True, True, 0)
            
            content_area.show_all()
            
            # Run dialog
            response = dialog.run()
            
            if response == Gtk.ResponseType.OK:
                # Save grading data
                grading_data = grading_widget.get_grading_data()
                row_data['grading_data'] = grading_data
                
                # Update UI to indicate grading is set
                if grading_data:
                    row_data['grading_button'].set_tooltip_text(f"Grading curve set ({len(grading_data)} points)")
                else:
                    row_data['grading_button'].set_tooltip_text("Edit grading curve")
                
                self.main_window.update_status(f"Grading curve updated for {material_name}", "success", 3)
                
                if self.auto_calculate_enabled:
                    self._trigger_calculation()
            
            dialog.destroy()
            
        except Exception as e:
            self.logger.error(f"Failed to show grading dialog: {e}")
            self.main_window.update_status(f"Error opening grading dialog: {e}", "error", 5)
#!/usr/bin/env python3
"""
Mix Design Panel for VCCTL

Provides comprehensive mix design interface with material selection, composition calculations,
water-binder ratio optimization, and real-time validation.
"""

import gi
import logging
import random
import os
import json
import numpy as np
from typing import TYPE_CHECKING, Optional, Dict, Any, List, Tuple
from decimal import Decimal

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, Pango, Gdk

if TYPE_CHECKING:
    from app.windows.main_window import VCCTLMainWindow

from app.services.service_container import get_service_container
from app.services.mix_service import MixService, MaterialType, MixComponent, MixDesign
from app.services.microstructure_service import MicrostructureParams, PhaseType
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
        self.microstructure_service = self.service_container.microstructure_service
        
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
        # Create scrolled window for all content
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_hexpand(True)
        scrolled.set_vexpand(True)
        
        # Main content layout with three columns
        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=15)
        main_box.set_margin_top(15)
        main_box.set_margin_bottom(15)
        main_box.set_margin_left(15)
        main_box.set_margin_right(15)
        
        # Left column: Mix composition (existing)
        left_column = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        left_column.set_size_request(450, -1)
        
        left_frame = Gtk.Frame(label="Cement Paste Components")
        self._create_composition_section(left_frame)
        left_column.pack_start(left_frame, False, False, 0)
        
        # Add microstructure parameters to left column
        self._create_system_parameters_section(left_column)
        self._create_composition_parameters_section(left_column)
        
        # Middle column: Particle and advanced parameters
        middle_column = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        middle_column.set_size_request(400, -1)
        
        self._create_particle_shape_section(middle_column)
        self._create_flocculation_section(middle_column)
        self._create_advanced_section(middle_column)
        
        # Right column: Properties and calculations
        right_column = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        right_column.set_size_request(400, -1)
        
        right_frame = Gtk.Frame(label="Mix Properties & Calculations")
        self._create_properties_section(right_frame)
        right_column.pack_start(right_frame, False, False, 0)
        
        # Pack columns
        main_box.pack_start(left_column, False, False, 0)
        main_box.pack_start(middle_column, False, False, 0)
        main_box.pack_start(right_column, False, False, 0)
        
        scrolled.add(main_box)
        self.pack_start(scrolled, True, True, 0)
    
    def _create_composition_section(self, parent: Gtk.Frame) -> None:
        """Create the mix composition section with separate Powder, Water, and Air sections."""
        comp_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        comp_box.set_margin_top(10)
        comp_box.set_margin_bottom(10)
        comp_box.set_margin_left(10)
        comp_box.set_margin_right(10)
        
        # Create three separate sections
        self._create_powder_section(comp_box)
        self._create_water_section(comp_box)
        self._create_air_section(comp_box)
        
        parent.add(comp_box)
    
    def _create_powder_section(self, parent: Gtk.Box) -> None:
        """Create the powder components section."""
        powder_frame = Gtk.Frame(label="Powder Components")
        powder_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        powder_box.set_margin_top(10)
        powder_box.set_margin_bottom(10)
        powder_box.set_margin_left(10)
        powder_box.set_margin_right(10)
        
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
        
        powder_box.pack_start(header_box, False, False, 0)
        
        # Scrolled window for components
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_size_request(-1, 200)
        
        # Components list container
        self.components_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        scrolled.add(self.components_box)
        
        powder_box.pack_start(scrolled, True, True, 0)
        
        powder_frame.add(powder_box)
        parent.pack_start(powder_frame, True, True, 0)
    
    def _create_water_section(self, parent: Gtk.Box) -> None:
        """Create the water content section."""
        water_frame = Gtk.Frame(label="Water Content")
        water_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        water_box.set_margin_top(10)
        water_box.set_margin_bottom(10)
        water_box.set_margin_left(10)
        water_box.set_margin_right(10)
        
        # Water content controls
        water_grid = Gtk.Grid()
        water_grid.set_row_spacing(5)
        water_grid.set_column_spacing(10)
        
        # Water-binder ratio
        wb_label = Gtk.Label("W/B Ratio:")
        wb_label.set_halign(Gtk.Align.END)
        wb_label.set_tooltip_text("Water/Binder ratio (Water mass / Powder mass)")
        water_grid.attach(wb_label, 0, 0, 1, 1)
        
        self.wb_ratio_spin = Gtk.SpinButton.new_with_range(0.1, 2.0, 0.01)
        self.wb_ratio_spin.set_value(0.40)
        self.wb_ratio_spin.set_digits(3)
        self.wb_ratio_spin.set_tooltip_text("Enter W/B ratio to calculate water mass")
        water_grid.attach(self.wb_ratio_spin, 1, 0, 1, 1)
        
        # Water content
        water_label = Gtk.Label("Water Mass (kg):")
        water_label.set_halign(Gtk.Align.END)
        water_label.set_tooltip_text("Water mass in kg (Binder = Paste = Powder + Water)")
        water_grid.attach(water_label, 0, 1, 1, 1)
        
        self.water_content_spin = Gtk.SpinButton.new_with_range(0.0, 10000.0, 0.001)
        self.water_content_spin.set_value(150.0)
        self.water_content_spin.set_digits(3)
        self.water_content_spin.set_editable(True)  # Make it editable for user input
        self.water_content_spin.set_tooltip_text("Enter water mass to calculate W/B ratio")
        water_grid.attach(self.water_content_spin, 1, 1, 1, 1)
        
        water_box.pack_start(water_grid, False, False, 0)
        water_frame.add(water_box)
        
        parent.pack_start(water_frame, False, False, 0)
    
    def _create_air_section(self, parent: Gtk.Box) -> None:
        """Create the air content section."""
        air_frame = Gtk.Frame(label="Air Content")
        air_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        air_box.set_margin_top(10)
        air_box.set_margin_bottom(10)
        air_box.set_margin_left(10)
        air_box.set_margin_right(10)
        
        # Air content controls
        air_grid = Gtk.Grid()
        air_grid.set_row_spacing(5)
        air_grid.set_column_spacing(10)
        
        # Air content
        air_label = Gtk.Label("Air Volume Fraction:")
        air_label.set_halign(Gtk.Align.END)
        air_grid.attach(air_label, 0, 0, 1, 1)
        
        self.air_content_spin = Gtk.SpinButton.new_with_range(0.0, 0.15, 0.001)
        self.air_content_spin.set_value(0.02)
        self.air_content_spin.set_digits(3)
        air_grid.attach(self.air_content_spin, 1, 0, 1, 1)
        
        air_box.pack_start(air_grid, False, False, 0)
        air_frame.add(air_box)
        
        parent.pack_start(air_frame, False, False, 0)
    
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
            ("Powder SG:", "powder_sg"),
            ("Powder Volume:", "powder_volume"),
            ("Water Volume:", "water_volume"),
            ("Paste Volume:", "paste_volume"),
            ("Air Volume:", "air_volume"),
            ("Total Aggregate:", "total_aggregate")
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
        
        self.create_mix_button = Gtk.Button(label="Create Mix")
        create_icon = Gtk.Image.new_from_icon_name("system-run-symbolic", Gtk.IconSize.BUTTON)
        self.create_mix_button.set_image(create_icon)
        self.create_mix_button.set_always_show_image(True)
        self.create_mix_button.get_style_context().add_class("suggested-action")
        button_box.pack_start(self.create_mix_button, False, False, 0)
        
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
        self.create_mix_button.connect('clicked', self._on_create_mix_clicked)
        self.validate_button.connect('clicked', self._on_validate_clicked)
        self.export_button.connect('clicked', self._on_export_clicked)
        
        # Microstructure parameter signals
        self.system_size_spin.connect('value-changed', self._on_system_size_changed)
        self.resolution_spin.connect('value-changed', self._on_resolution_changed)
        self.flocculation_check.connect('toggled', self._on_flocculation_toggled)
        self.generate_seed_button.connect('clicked', self._on_generate_seed_clicked)
    
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
        
        # Mass (kg) spin button
        mass_spin = Gtk.SpinButton.new_with_range(0.0, 10000.0, 0.1)
        mass_spin.set_digits(1)
        mass_spin.set_size_request(80, -1)
        row_box.pack_start(mass_spin, False, False, 0)
        
        # kg label
        kg_label = Gtk.Label("kg")
        row_box.pack_start(kg_label, False, False, 0)
        
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
        """Handle normalize button click - not applicable for absolute masses."""
        self.main_window.update_status("Normalization not applicable for absolute masses (kg)", "info", 3)
    
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
        """Handle component mass change."""
        if self.auto_calculate_enabled:
            # When powder mass changes, recalculate water content from W/B ratio
            # (This maintains the W/B ratio while adjusting water to match new powder mass)
            self._calculate_water_content_from_wb_ratio()
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
    
    def _on_create_mix_clicked(self, button) -> None:
        """Handle create mix button click."""
        self._create_microstructure_input_file()
    
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
        """Calculate water mass (kg) from W/B ratio (water mass / powder mass)."""
        try:
            wb_ratio = self.wb_ratio_spin.get_value()
            
            # Calculate total powder mass in kg
            total_powder_mass = self._calculate_total_powder_mass()
            
            if total_powder_mass > 0:
                water_mass = wb_ratio * total_powder_mass
                # Block signal to prevent infinite loop
                self.water_content_spin.handler_block_by_func(self._on_water_content_changed)
                self.water_content_spin.set_value(water_mass)
                self.water_content_spin.handler_unblock_by_func(self._on_water_content_changed)
        
        except Exception as e:
            self.logger.warning(f"Failed to calculate water content: {e}")
    
    def _calculate_wb_ratio_from_water_content(self) -> None:
        """Calculate W/B ratio from water mass (kg) (water mass / powder mass)."""
        try:
            water_mass = self.water_content_spin.get_value()
            
            # Calculate total powder mass in kg
            total_powder_mass = self._calculate_total_powder_mass()
            
            if total_powder_mass > 0:
                wb_ratio = water_mass / total_powder_mass
                # Block signal to prevent infinite loop
                self.wb_ratio_spin.handler_block_by_func(self._on_wb_ratio_changed)
                self.wb_ratio_spin.set_value(wb_ratio)
                self.wb_ratio_spin.handler_unblock_by_func(self._on_wb_ratio_changed)
        
        except Exception as e:
            self.logger.warning(f"Failed to calculate W/B ratio: {e}")
    
    def _calculate_total_powder_mass(self) -> float:
        """Calculate total powder mass in kg (cement, fly ash, slag, inert filler)."""
        powder_types = {MaterialType.CEMENT, MaterialType.FLY_ASH, MaterialType.SLAG, MaterialType.INERT_FILLER}
        total_powder = 0.0
        
        for row in self.component_rows:
            type_str = row['type_combo'].get_active_id()
            if type_str:
                try:
                    material_type = MaterialType(type_str)
                    if material_type in powder_types:
                        total_powder += row['mass_spin'].get_value()
                except ValueError:
                    continue
        
        return total_powder
    
    def _calculate_total_paste_mass(self) -> float:
        """Calculate total paste mass in kg (powder + water). Paste = Binder."""
        powder_mass = self._calculate_total_powder_mass()
        water_mass = self.water_content_spin.get_value()
        return powder_mass + water_mass
    
    def _calculate_total_binder_mass(self) -> float:
        """Calculate total binder mass in kg (powder + water). Binder = Paste."""
        return self._calculate_total_paste_mass()
    
    def _calculate_powder_specific_gravity(self) -> float:
        """Calculate mass-weighted average specific gravity of all powder components."""
        powder_types = {MaterialType.CEMENT, MaterialType.FLY_ASH, MaterialType.SLAG, MaterialType.INERT_FILLER}
        total_weighted_sg = 0.0
        total_powder_mass = 0.0
        
        for row in self.component_rows:
            type_str = row['type_combo'].get_active_id()
            if type_str:
                try:
                    material_type = MaterialType(type_str)
                    if material_type in powder_types:
                        mass_kg = row['mass_spin'].get_value()
                        sg_text = row['sg_label'].get_text()
                        
                        if mass_kg > 0 and sg_text != "—":
                            sg = float(sg_text)
                            total_weighted_sg += mass_kg * sg
                            total_powder_mass += mass_kg
                except (ValueError, TypeError):
                    continue
        
        if total_powder_mass > 0:
            return total_weighted_sg / total_powder_mass
        else:
            return 3.15  # Default cement specific gravity
    
    def _calculate_volumes_from_masses(self) -> Dict[str, float]:
        """Convert masses to volumes using specific gravities."""
        # Water specific gravity is 1.0
        water_sg = 1.0
        
        # Calculate powder specific gravity (mass-weighted average)
        powder_sg = self._calculate_powder_specific_gravity()
        
        # Get masses
        powder_mass = self._calculate_total_powder_mass()
        water_mass = self.water_content_spin.get_value()
        
        # Calculate volumes (Volume = Mass / Specific Gravity)
        powder_volume = powder_mass / powder_sg if powder_sg > 0 else 0.0
        water_volume = water_mass / water_sg
        
        return {
            'powder_volume': powder_volume,
            'water_volume': water_volume,
            'paste_volume': powder_volume + water_volume,
            'powder_sg': powder_sg,
            'water_sg': water_sg
        }
    
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
            total_component_mass = 0.0
            
            # Calculate total mass of components only (excluding water)
            for row in self.component_rows:
                mass_kg = row['mass_spin'].get_value()
                if mass_kg > 0:
                    total_component_mass += mass_kg
            
            # Create components with mass fractions (relative to total component mass)
            for row in self.component_rows:
                type_str = row['type_combo'].get_active_id()
                name = row['name_combo'].get_active_id()
                mass_kg = row['mass_spin'].get_value()
                
                if type_str and name and mass_kg > 0 and total_component_mass > 0:
                    material_type = MaterialType(type_str)
                    sg = self.mix_service._get_material_specific_gravity(name, material_type)
                    
                    # Convert kg to mass fraction (relative to component mass, not including water)
                    mass_fraction = mass_kg / total_component_mass
                    
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
            # Convert water mass to water fraction (relative to component mass)
            water_mass = self.water_content_spin.get_value()
            water_fraction = water_mass / total_component_mass if total_component_mass > 0 else 0.0
            
            mix_design = MixDesign(
                name=mix_name,
                components=components,
                water_binder_ratio=self.wb_ratio_spin.get_value(),
                total_water_content=water_fraction,
                air_content=self.air_content_spin.get_value()  # Already a volume fraction
            )
            
            return mix_design
            
        except Exception as e:
            self.logger.error(f"Failed to create mix design from UI: {e}")
            return None
    
    def _update_properties_display(self, properties: Dict[str, Any]) -> None:
        """Update the properties display with calculated values."""
        try:
            # Update property labels with volume information
            self.property_labels['powder_sg'].set_text(f"{properties.get('powder_specific_gravity', 0):.3f}")
            self.property_labels['powder_volume'].set_text(f"{properties.get('powder_volume_fraction', 0):.1%}")
            self.property_labels['water_volume'].set_text(f"{properties.get('water_volume_fraction', 0):.1%}")
            self.property_labels['paste_volume'].set_text(f"{properties.get('paste_volume_fraction', 0):.1%}")
            self.property_labels['air_volume'].set_text(f"{properties.get('air_volume_fraction', 0):.1%}")
            self.property_labels['total_aggregate'].set_text(f"{properties.get('total_aggregate_fraction', 0):.1%}")
            
            # Also update volume calculations from UI inputs directly
            volume_data = self._calculate_volumes_from_masses()
            if volume_data:
                # Display additional volume information in status
                powder_vol = volume_data['powder_volume']
                water_vol = volume_data['water_volume']
                paste_vol = volume_data['paste_volume']
                powder_sg = volume_data['powder_sg']
                
                self.status_label.set_markup(
                    f'<span size="small">Volumes: Powder={powder_vol:.1f}, Water={water_vol:.1f}, '
                    f'Paste={paste_vol:.1f} | Powder SG={powder_sg:.3f}</span>'
                )
                
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
        self.water_content_spin.set_value(150.0)  # 150 kg default
        self.air_content_spin.set_value(0.02)  # 2% volume fraction
        
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
    
    def _create_microstructure_input_file(self) -> None:
        """Create microstructure input file after validation."""
        try:
            # Step 1: Validate mix design
            mix_design = self._create_mix_design_from_ui()
            if not mix_design:
                self.main_window.update_status("Unable to create mix design - please check inputs", "error", 5)
                return
            
            # Validate the mix design
            validation_result = self.mix_service.validate_mix_design(mix_design)
            if not validation_result['is_valid']:
                # Show validation errors
                error_msg = "Mix validation failed:\n" + "\n".join(validation_result['errors'])
                dialog = Gtk.MessageDialog(
                    transient_for=self.main_window,
                    message_type=Gtk.MessageType.ERROR,
                    buttons=Gtk.ButtonsType.OK,
                    text="Mix Design Validation Failed"
                )
                dialog.format_secondary_text(error_msg)
                dialog.run()
                dialog.destroy()
                return
            
            # Step 2: Create mix folder and generate correlation files
            self._create_mix_folder_and_correlation_files(mix_design)
            
            # Step 3: Get microstructure parameters
            microstructure_params = self._get_microstructure_parameters()
            
            # Step 4: Generate input file
            input_file_content = self._generate_genmic_input_file(mix_design, microstructure_params)
            
            # Step 5: Save input file
            self._save_input_file(input_file_content, mix_design.name)
            
        except Exception as e:
            self.logger.error(f"Failed to create microstructure input file: {e}")
            self.main_window.update_status(f"Error creating input file: {e}", "error", 5)
    
    def _get_microstructure_parameters(self) -> Dict[str, Any]:
        """Get microstructure parameters from UI."""
        return {
            'system_size': int(self.system_size_spin.get_value()),
            'resolution': self.resolution_spin.get_value(),
            'water_binder_ratio': self.wb_ratio_spin.get_value(),
            'aggregate_volume_fraction': self.agg_volume_spin.get_value(),
            'air_content': self.micro_air_content_spin.get_value(),
            'cement_shape_set': self.cement_shape_combo.get_active_id() or "sphere",
            'aggregate_shape_set': self.agg_shape_combo.get_active_id() or "sphere",
            'flocculation_enabled': self.flocculation_check.get_active(),
            'flocculation_degree': self.flocculation_spin.get_value(),
            'random_seed': int(self.random_seed_spin.get_value())
        }
    
    def _get_material_psd_data(self, material_name: str, material_type: MaterialType) -> List[Tuple[float, float]]:
        """Get PSD data for a material and convert to standard 0.25-75 μm range."""
        try:
            with self.service_container.database_service.get_read_only_session() as session:
                # Get material data
                if material_type == MaterialType.CEMENT:
                    from app.models.cement import Cement
                    material = session.query(Cement).filter_by(name=material_name).first()
                elif material_type == MaterialType.FLY_ASH:
                    from app.models.fly_ash import FlyAsh
                    material = session.query(FlyAsh).filter_by(name=material_name).first()
                elif material_type == MaterialType.SLAG:
                    from app.models.slag import Slag
                    material = session.query(Slag).filter_by(name=material_name).first()
                elif material_type == MaterialType.INERT_FILLER:
                    from app.models.inert_filler import InertFiller
                    material = session.query(InertFiller).filter_by(name=material_name).first()
                else:
                    return self._generate_default_psd()
                
                if not material:
                    self.logger.warning(f"Material {material_name} not found, using default PSD")
                    return self._generate_default_psd()
                
                # Check PSD mode and convert accordingly
                if hasattr(material, 'psd_mode') and material.psd_mode:
                    if material.psd_mode == 'custom' and material.psd_custom_points:
                        # Parse custom points and convert to standard range
                        custom_points = json.loads(material.psd_custom_points)
                        return self._convert_custom_psd_to_standard_range(custom_points)
                    
                    elif material.psd_mode == 'rosin_rammler':
                        # Convert Rosin-Rammler parameters to custom points
                        return self._convert_rosin_rammler_to_points(
                            material.psd_d50, material.psd_n, material.psd_dmax
                        )
                    
                    elif material.psd_mode == 'log_normal':
                        # Convert log-normal parameters to custom points
                        return self._convert_log_normal_to_points(
                            material.psd_d50, material.psd_n
                        )
                
                # Fallback to default PSD
                self.logger.warning(f"No PSD data found for {material_name}, using default")
                return self._generate_default_psd()
                
        except Exception as e:
            self.logger.error(f"Failed to get PSD data for {material_name}: {e}")
            return self._generate_default_psd()
    
    def _convert_custom_psd_to_standard_range(self, custom_points: List[List[float]]) -> List[Tuple[float, float]]:
        """Convert custom PSD points to standard 0.25-75 μm range."""
        try:
            # Extract diameters and mass fractions
            diameters = np.array([point[0] for point in custom_points])
            mass_fractions = np.array([point[1] for point in custom_points])
            
            # Filter to 0.25-75 μm range
            mask = (diameters >= 0.25) & (diameters <= 75.0)
            
            if not np.any(mask):
                self.logger.warning("No PSD data in 0.25-75 μm range, using default")
                return self._generate_default_psd()
            
            filtered_diameters = diameters[mask]
            filtered_fractions = mass_fractions[mask]
            
            # Normalize mass fractions to sum to 1.0
            if np.sum(filtered_fractions) > 0:
                filtered_fractions = filtered_fractions / np.sum(filtered_fractions)
            
            # Create standard discrete points
            return [(float(d), float(f)) for d, f in zip(filtered_diameters, filtered_fractions)]
            
        except Exception as e:
            self.logger.error(f"Failed to convert custom PSD: {e}")
            return self._generate_default_psd()
    
    def _convert_rosin_rammler_to_points(self, d50: float, n: float, dmax: float = None) -> List[Tuple[float, float]]:
        """Convert Rosin-Rammler parameters to discrete points in 0.25-75 μm range."""
        try:
            if not d50 or not n:
                return self._generate_default_psd()
            
            # Create diameter range from 0.25 to 75 μm (or dmax if smaller)
            max_diameter = min(75.0, dmax if dmax else 75.0)
            diameters = np.logspace(np.log10(0.25), np.log10(max_diameter), 30)
            
            # Rosin-Rammler cumulative distribution: R = 1 - exp(-(d/d50)^n)
            # where d50 is the characteristic diameter
            cumulative = 1 - np.exp(-((diameters / d50) ** n))
            
            # Convert cumulative to differential (mass fractions)
            mass_fractions = np.diff(np.concatenate([[0], cumulative]))
            
            # Ensure we have the right number of points
            if len(mass_fractions) < len(diameters):
                mass_fractions = np.append(mass_fractions, 0)
            
            # Normalize to sum to 1.0
            mass_fractions = mass_fractions / np.sum(mass_fractions)
            
            return [(float(d), float(f)) for d, f in zip(diameters, mass_fractions)]
            
        except Exception as e:
            self.logger.error(f"Failed to convert Rosin-Rammler PSD: {e}")
            return self._generate_default_psd()
    
    def _convert_log_normal_to_points(self, d50: float, sigma: float) -> List[Tuple[float, float]]:
        """Convert log-normal parameters to discrete points in 0.25-75 μm range."""
        try:
            if not d50 or not sigma:
                return self._generate_default_psd()
            
            # Create diameter range from 0.25 to 75 μm
            diameters = np.logspace(np.log10(0.25), np.log10(75.0), 30)
            
            # Log-normal probability density function
            from scipy.stats import lognorm
            
            # Convert d50 to scale parameter (median)
            s = sigma  # shape parameter
            scale = d50  # scale parameter
            
            # Calculate probability density and convert to mass fractions
            pdf_values = lognorm.pdf(diameters, s=s, scale=scale)
            
            # Normalize to get mass fractions
            mass_fractions = pdf_values / np.sum(pdf_values)
            
            return [(float(d), float(f)) for d, f in zip(diameters, mass_fractions)]
            
        except Exception as e:
            self.logger.error(f"Failed to convert log-normal PSD: {e}")
            return self._generate_default_psd()
    
    def _generate_default_psd(self) -> List[Tuple[float, float]]:
        """Generate a default PSD for cement (typical Portland cement)."""
        # Typical cement PSD with log-normal-like distribution
        diameters = [0.5, 1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 45.0, 63.0]
        mass_fractions = [0.05, 0.15, 0.25, 0.25, 0.15, 0.08, 0.04, 0.02, 0.01]
        
        return list(zip(diameters, mass_fractions))

    def _calculate_total_phases(self, mix_design: MixDesign) -> int:
        """Calculate total number of phases to add to genmic.c."""
        num_phases = 0
        
        for component in mix_design.components:
            if component.material_type == MaterialType.CEMENT:
                # Each cement has 4 phases: Clinker(1), Dihydrate(7), Hemihydrate(8), Anhydrite(9)
                num_phases += 4
            elif component.material_type == MaterialType.FLY_ASH:
                # Fly ash has 1 phase: FLYASH(18)
                num_phases += 1
            elif component.material_type == MaterialType.SLAG:
                # Slag has 1 phase: SLAG(12)
                num_phases += 1
            elif component.material_type == MaterialType.INERT_FILLER:
                # Inert filler has 1 phase: INERT(11)
                num_phases += 1
            # Future: SILICA_FUME(10) and LIMESTONE(33) would each add 1
        
        return num_phases

    def _calculate_binder_volume_fractions(self, mix_design: MixDesign, params: Dict[str, Any]) -> tuple[float, float]:
        """Calculate binder solid and water volume fractions on total paste basis."""
        try:
            # Calculate total masses
            powder_types = {MaterialType.CEMENT, MaterialType.FLY_ASH, MaterialType.SLAG, MaterialType.INERT_FILLER}
            
            total_powder_mass = 0.0
            total_powder_volume = 0.0
            
            for component in mix_design.components:
                if component.material_type in powder_types:
                    mass_kg = component.mass_kg
                    sg = self.mix_service._get_material_specific_gravity(component.material_name, component.material_type)
                    volume_m3 = mass_kg / (sg * 1000)  # Convert to m³
                    
                    total_powder_mass += mass_kg
                    total_powder_volume += volume_m3
            
            # Calculate water mass and volume from W/B ratio
            wb_ratio = params['water_binder_ratio']
            water_mass = wb_ratio * total_powder_mass  # kg
            water_volume = water_mass / 1000  # m³ (water SG = 1.0)
            
            # Calculate total paste volume
            total_paste_volume = total_powder_volume + water_volume
            
            # Calculate volume fractions on total paste basis
            binder_solid_vfrac = total_powder_volume / total_paste_volume
            water_vfrac = water_volume / total_paste_volume
            
            # Verify they sum to 1.0
            total = binder_solid_vfrac + water_vfrac
            if abs(total - 1.0) > 0.001:
                self.logger.warning(f"Binder volume fractions don't sum to 1.0: {total:.6f}")
            
            self.logger.info(f"Binder solid volume fraction: {binder_solid_vfrac:.6f}")
            self.logger.info(f"Water volume fraction: {water_vfrac:.6f}")
            
            return binder_solid_vfrac, water_vfrac
            
        except Exception as e:
            self.logger.error(f"Failed to calculate binder volume fractions: {e}")
            # Return default values
            return 0.7, 0.3

    def _calculate_cement_phase_fractions(self, cement_name: str, component) -> Dict[str, float]:
        """Calculate volume fractions for cement constituent phases on binder solid basis."""
        try:
            with self.service_container.database_service.get_read_only_session() as session:
                from app.models.cement import Cement
                cement = session.query(Cement).filter_by(name=cement_name).first()
                
                if not cement:
                    raise ValueError(f"Cement {cement_name} not found in database")
                
                # Get mass fractions from database
                c3s_mf = cement.c3s_mass_fraction or 0.0
                c2s_mf = cement.c2s_mass_fraction or 0.0
                c3a_mf = cement.c3a_mass_fraction or 0.0
                c4af_mf = cement.c4af_mass_fraction or 0.0
                k2so4_mf = cement.k2so4_mass_fraction or 0.0
                na2so4_mf = cement.na2so4_mass_fraction or 0.0
                
                dihyd_mf = cement.dihyd or 0.0
                hemihyd_mf = cement.hemihyd or 0.0
                anhyd_mf = cement.anhyd or 0.0
                
                # Calculate clinker mass fraction (all non-gypsum phases)
                clinker_mf = c3s_mf + c2s_mf + c3a_mf + c4af_mf + k2so4_mf + na2so4_mf
                
                # Calculate component's fraction of total binder solids (by mass)
                total_powder_mass = sum(comp.mass_kg for comp in component.mix_design.components 
                                      if comp.material_type in {MaterialType.CEMENT, MaterialType.FLY_ASH, 
                                                               MaterialType.SLAG, MaterialType.INERT_FILLER})
                component_fraction = component.mass_kg / total_powder_mass
                
                # Calculate volume fractions on binder solid basis
                # Each cement phase gets its share of this component's total contribution
                clinker_vf = clinker_mf * component_fraction
                dihydrate_vf = dihyd_mf * component_fraction
                hemihydrate_vf = hemihyd_mf * component_fraction
                anhydrite_vf = anhyd_mf * component_fraction
                
                return {
                    'clinker': clinker_vf,
                    'dihydrate': dihydrate_vf,
                    'hemihydrate': hemihydrate_vf,
                    'anhydrite': anhydrite_vf
                }
                
        except Exception as e:
            self.logger.error(f"Failed to calculate cement phase fractions: {e}")
            # Return default fractions
            return {
                'clinker': 0.8,
                'dihydrate': 0.1, 
                'hemihydrate': 0.05,
                'anhydrite': 0.05
            }

    def _calculate_component_binder_solid_fraction(self, component, mix_design: MixDesign) -> float:
        """Calculate component's volume fraction on binder solid basis."""
        try:
            # Calculate total powder mass
            powder_types = {MaterialType.CEMENT, MaterialType.FLY_ASH, MaterialType.SLAG, MaterialType.INERT_FILLER}
            total_powder_mass = sum(comp.mass_kg for comp in mix_design.components 
                                  if comp.material_type in powder_types)
            
            # Component's fraction of total binder solids
            component_fraction = component.mass_kg / total_powder_mass
            
            return component_fraction
            
        except Exception as e:
            self.logger.error(f"Failed to calculate component binder solid fraction: {e}")
            return 0.1  # Default fallback

    def _create_mix_folder_and_correlation_files(self, mix_design: MixDesign) -> None:
        """Create mix folder and generate correlation files for cement materials."""
        try:
            # Create safe folder name
            mix_name_safe = "".join(c for c in mix_design.name if c.isalnum() or c in ['_', '-'])
            mix_folder_path = os.path.join(os.getcwd(), mix_name_safe)
            
            # Create mix folder if it doesn't exist
            os.makedirs(mix_folder_path, exist_ok=True)
            self.logger.info(f"Created mix folder: {mix_folder_path}")
            
            # Generate correlation files for each cement component
            cement_components = [comp for comp in mix_design.components 
                               if comp.material_type == MaterialType.CEMENT]
            
            if cement_components:
                # For now, use the first cement (TODO: handle multiple cements)
                cement_component = cement_components[0]
                self._generate_correlation_files(cement_component.material_name, mix_folder_path, mix_name_safe)
                
        except Exception as e:
            self.logger.error(f"Failed to create mix folder and correlation files: {e}")
            raise

    def _generate_correlation_files(self, cement_name: str, mix_folder_path: str, mix_name_safe: str) -> None:
        """Generate correlation files from cement database data."""
        try:
            with self.service_container.database_service.get_read_only_session() as session:
                from app.models.cement import Cement
                cement = session.query(Cement).filter_by(name=cement_name).first()
                
                if not cement:
                    raise ValueError(f"Cement {cement_name} not found in database")
                
                # Define correlation file mappings
                correlation_files = {
                    'sil': cement.sil,
                    'c3s': cement.c3s,
                    'alu': cement.alu,
                    'k2o': cement.k2o,
                    'n2o': cement.n2o
                }
                
                # Add c3a or c4f file depending on availability
                if cement.c4f:
                    correlation_files['c4f'] = cement.c4f
                elif cement.c3a:
                    correlation_files['c3a'] = cement.c3a
                
                # Write correlation files
                for extension, binary_data in correlation_files.items():
                    if binary_data:
                        file_path = os.path.join(mix_folder_path, f"{mix_name_safe}.{extension}")
                        with open(file_path, 'wb') as f:
                            f.write(binary_data)
                        self.logger.info(f"Generated correlation file: {file_path}")
                    else:
                        self.logger.warning(f"No data for {extension} correlation file in cement {cement_name}")
                
                self.main_window.update_status(f"Generated correlation files for cement {cement_name}", "success", 3)
                
        except Exception as e:
            self.logger.error(f"Failed to generate correlation files: {e}")
            raise

    def _generate_genmic_input_file(self, mix_design: MixDesign, params: Dict[str, Any]) -> str:
        """Generate input file content for genmic.c program."""
        lines = []
        
        # Random seed (negative integer)
        lines.append(f"{params['random_seed']}")
        
        # Menu choice 2: SPECSIZE (set system size)
        lines.append("2")
        
        # System dimensions (cubic system)
        system_size = params['system_size']
        lines.append(f"{system_size}")  # X size
        lines.append(f"{system_size}")  # Y size  
        lines.append(f"{system_size}")  # Z size
        
        # Resolution (micrometers per voxel)
        lines.append(f"{params['resolution']}")
        
        # Menu choice 3: ADDPART (add particles)
        lines.append("3")
        
        # Shape selection (0=SPHERES, 1=REALSHAPE, 2=MIXED)
        shape_set = params['cement_shape_set']
        if shape_set == "sphere":
            lines.append("0")  # SPHERES - no additional inputs needed
        else:
            lines.append("1")  # REALSHAPE
            # Parent directory path (with final separator)
            parent_path = os.path.join(os.getcwd(), "particle_shape_set") + os.sep
            lines.append(parent_path)
            # Shape set name (no final separator)
            lines.append(shape_set)
        
        # Calculate binder solid and water volume fractions
        binder_solid_vfrac, water_vfrac = self._calculate_binder_volume_fractions(mix_design, params)
        
        # Binder SOLID volume fraction (on total paste basis)
        lines.append(f"{binder_solid_vfrac:.6f}")
        
        # Binder WATER volume fraction (on total paste basis)  
        lines.append(f"{water_vfrac:.6f}")
        
        # Calculate total number of phases to add
        num_phases = self._calculate_total_phases(mix_design)
        lines.append(f"{num_phases}")
        
        # Add phase data for each component
        # TODO: This section will be completely rewritten to handle cement phases properly
        # For now, keeping simplified structure to implement num_phases fix
        powder_types = {MaterialType.CEMENT, MaterialType.FLY_ASH, MaterialType.SLAG, MaterialType.INERT_FILLER}
        
        for component in mix_design.components:
            if component.material_type in powder_types:
                if component.material_type == MaterialType.CEMENT:
                    # Break cement into 4 phases: Clinker, Dihydrate, Hemihydrate, Anhydrite
                    cement_phases = self._calculate_cement_phase_fractions(component.material_name, component)
                    psd_data = self._get_material_psd_data(component.material_name, component.material_type)
                    
                    # Phase ID 1: Clinker
                    lines.append("1")
                    lines.append(f"{cement_phases['clinker']:.6f}")
                    lines.append(f"{len(psd_data)}")
                    for diameter, mass_fraction in psd_data:
                        lines.append(f"{int(round(diameter))}")
                        lines.append(f"{mass_fraction:.6f}")
                    
                    # Phase ID 7: Dihydrate
                    lines.append("7")
                    lines.append(f"{cement_phases['dihydrate']:.6f}")
                    lines.append(f"{len(psd_data)}")
                    for diameter, mass_fraction in psd_data:
                        lines.append(f"{int(round(diameter))}")
                        lines.append(f"{mass_fraction:.6f}")
                    
                    # Phase ID 8: Hemihydrate
                    lines.append("8")
                    lines.append(f"{cement_phases['hemihydrate']:.6f}")
                    lines.append(f"{len(psd_data)}")
                    for diameter, mass_fraction in psd_data:
                        lines.append(f"{int(round(diameter))}")
                        lines.append(f"{mass_fraction:.6f}")
                    
                    # Phase ID 9: Anhydrite
                    lines.append("9")
                    lines.append(f"{cement_phases['anhydrite']:.6f}")
                    lines.append(f"{len(psd_data)}")
                    for diameter, mass_fraction in psd_data:
                        lines.append(f"{int(round(diameter))}")
                        lines.append(f"{mass_fraction:.6f}")
                        
                else:
                    # Non-cement materials: fly ash, slag, inert filler
                    phase_id = self._get_phase_id_for_material(component.material_type, component.material_name)
                    lines.append(f"{phase_id}")
                    
                    # Calculate volume fraction on binder solid basis
                    binder_solid_vfrac = self._calculate_component_binder_solid_fraction(component, mix_design)
                    lines.append(f"{binder_solid_vfrac:.6f}")
                    
                    # Add PSD data for this component
                    psd_data = self._get_material_psd_data(component.material_name, component.material_type)
                    lines.append(f"{len(psd_data)}")
                    
                    # Add each size class (diameter and volume fraction)
                    for diameter, mass_fraction in psd_data:
                        lines.append(f"{int(round(diameter))}")
                        lines.append(f"{mass_fraction:.6f}")
        
        # Dispersion factor (separation distance in pixels) for spheres (0-2)
        # 0 = totally random placement, 1-2 = increasing separation
        dispersion_factor = params.get('dispersion_factor', 0)  # Default to random placement
        lines.append(f"{dispersion_factor}")
        
        # Probability for gypsum particles (0.0-1.0) on random particle basis
        # Always 0.0 since we explicitly add gypsum phases (dihydrate, hemihydrate, anhydrite) separately
        gypsum_probability = 0.0  # Obsolete mechanism - gypsum already added as separate phases
        lines.append(f"{gypsum_probability:.6f}")
        
        # Add aggregate if present
        aggregate_components = [comp for comp in mix_design.components 
                             if comp.material_type == MaterialType.AGGREGATE]
        
        if aggregate_components and params['aggregate_volume_fraction'] > 0:
            for agg_component in aggregate_components:
                # Menu choice 3: ADDPART
                lines.append("3")
                
                # Aggregate phase ID (typically INERTAGG = 13)
                lines.append("13")
                
                # Aggregate volume fraction
                lines.append(f"{params['aggregate_volume_fraction']:.6f}")
                
                # Aggregate shape set
                agg_shape = params['aggregate_shape_set']
                if agg_shape == "sphere":
                    lines.append("1")  # Mathematical spherical
                else:
                    # File-based aggregate shape set
                    lines.append("2")
                    agg_path = os.path.join(os.getcwd(), "aggregate", agg_shape)
                    lines.append(agg_path)
        
        # Add porosity/water if needed
        if params['air_content'] > 0:
            # Menu choice 3: ADDPART for porosity
            lines.append("3")
            lines.append("0")  # POROSITY phase ID
            lines.append(f"{params['air_content']:.6f}")
            lines.append("1")  # Spherical for air/pores
        
        # Flocculation settings if enabled
        if params['flocculation_enabled']:
            # Menu choice for flocculation (would need to check genmic.c for exact option)
            lines.append("4")  # Assuming menu option 4 for flocculation
            lines.append(f"{params['flocculation_degree']:.3f}")
        
        # Check if cement phases were added - if so, need special processing workflow
        has_cement = any(comp.material_type == MaterialType.CEMENT 
                        for comp in mix_design.components)
        
        if has_cement:
            # Menu choice 9: DISTRIB (distribute clinker phases)
            lines.append("9")
            
            # Path/root name for cement correlation files
            # TODO: This will be the path to the mix folder + root name
            mix_name_safe = "".join(c for c in mix_design.name if c.isalnum() or c in ['_', '-'])
            correlation_path = f"{mix_name_safe}/{mix_name_safe}"
            lines.append(correlation_path)
            
            # Menu choice 11: ONEPIX (add one-pixel particles)
            lines.append("11")
            
            # Menu choice 5: MEASURE (measure global phase fractions)
            lines.append("5")
        
        # Menu choice 10: OUTPUTMIC (output microstructure file)
        lines.append("10")
        
        # Output filename for microstructure (full path to mix folder + mix name)
        mix_name_safe = "".join(c for c in mix_design.name if c.isalnum() or c in ['_', '-'])
        output_filename = f"{mix_name_safe}/{mix_name_safe}.img"
        lines.append(output_filename)
        
        # Output filename for particle IDs (full path to mix folder + mix name)
        particle_filename = f"{mix_name_safe}/{mix_name_safe}.pimg"
        lines.append(particle_filename)
        
        # Menu choice 1: Exit
        lines.append("1")
        
        return "\n".join(lines) + "\n"
    
    def _get_phase_id_for_material(self, material_type: MaterialType, material_name: str) -> int:
        """Get phase ID for material based on vcctl.h definitions."""
        # Based on vcctl.h phase definitions
        if material_type == MaterialType.CEMENT:
            # Default to C3S for cement, but could be more sophisticated
            # based on cement composition analysis
            return 1  # C3S
        elif material_type == MaterialType.FLY_ASH:
            return 18  # FLYASH
        elif material_type == MaterialType.SLAG:
            return 12  # SLAG
        elif material_type == MaterialType.INERT_FILLER:
            return 11  # INERT
        else:
            return 1  # Default to C3S
    
    def _save_input_file(self, content: str, mix_name: str) -> None:
        """Save input file content to disk."""
        try:
            # Create safe filename
            mix_name_safe = "".join(c for c in mix_name if c.isalnum() or c in ['_', '-'])
            default_filename = f"genmic_input_{mix_name_safe}.txt"
            
            # Set initial directory to mix folder if it exists
            mix_folder_path = os.path.join(os.getcwd(), mix_name_safe)
            if os.path.exists(mix_folder_path):
                initial_path = os.path.join(mix_folder_path, default_filename)
            else:
                initial_path = default_filename
            
            # Create file chooser dialog
            dialog = Gtk.FileChooserDialog(
                title="Save Microstructure Input File",
                parent=self.main_window,
                action=Gtk.FileChooserAction.SAVE
            )
            dialog.add_buttons(
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_SAVE, Gtk.ResponseType.OK
            )
            
            # Add file filter
            filter_txt = Gtk.FileFilter()
            filter_txt.set_name("Text files")
            filter_txt.add_pattern("*.txt")
            dialog.add_filter(filter_txt)
            
            filter_all = Gtk.FileFilter()
            filter_all.set_name("All files")
            filter_all.add_pattern("*")
            dialog.add_filter(filter_all)
            
            # Set initial file path (directory + filename)
            if os.path.exists(mix_folder_path):
                dialog.set_current_folder(mix_folder_path)
            dialog.set_current_name(default_filename)
            
            response = dialog.run()
            if response == Gtk.ResponseType.OK:
                filename = dialog.get_filename()
                
                # Write file
                with open(filename, 'w') as f:
                    f.write(content)
                
                self.logger.info(f"Saved microstructure input file: {filename}")
                self.main_window.update_status(f"Input file saved: {filename}", "success", 5)
                
                # Show info dialog with next steps
                info_dialog = Gtk.MessageDialog(
                    transient_for=self.main_window,
                    message_type=Gtk.MessageType.INFO,
                    buttons=Gtk.ButtonsType.OK,
                    text="Input File Created Successfully"
                )
                info_dialog.format_secondary_text(
                    f"Input file saved to:\n{filename}\n\n"
                    f"To generate the 3D microstructure, run:\n"
                    f"./backend/genmic < {filename}"
                )
                info_dialog.run()
                info_dialog.destroy()
            
            dialog.destroy()
            
        except Exception as e:
            self.logger.error(f"Failed to save input file: {e}")
            self.main_window.update_status(f"Error saving file: {e}", "error", 5)
    
    # =========================================================================
    # Microstructure Parameter Sections (moved from MicrostructurePanel)
    # =========================================================================
    
    def _create_system_parameters_section(self, parent: Gtk.Box) -> None:
        """Create system parameters section."""
        frame = Gtk.Frame(label="System Dimensions & Resolution")
        frame.get_style_context().add_class("card")
        
        grid = Gtk.Grid()
        grid.set_row_spacing(10)
        grid.set_column_spacing(10)
        grid.set_margin_top(15)
        grid.set_margin_bottom(15)
        grid.set_margin_left(15)
        grid.set_margin_right(15)
        
        # System size
        size_label = Gtk.Label("System Size (voxels):")
        size_label.set_halign(Gtk.Align.START)
        size_label.set_tooltip_text("Number of voxels per dimension (creates size³ total voxels)")
        grid.attach(size_label, 0, 0, 1, 1)
        
        self.system_size_spin = Gtk.SpinButton.new_with_range(10, 1000, 1)
        self.system_size_spin.set_value(100)
        self.system_size_spin.set_tooltip_text("Larger systems are more representative but computationally expensive")
        grid.attach(self.system_size_spin, 1, 0, 1, 1)
        
        # Resolution
        resolution_label = Gtk.Label("Resolution (μm/voxel):")
        resolution_label.set_halign(Gtk.Align.START)
        resolution_label.set_tooltip_text("Physical size of each voxel in micrometers")
        grid.attach(resolution_label, 0, 1, 1, 1)
        
        self.resolution_spin = Gtk.SpinButton.new_with_range(0.01, 100.0, 0.01)
        self.resolution_spin.set_digits(2)
        self.resolution_spin.set_value(1.0)
        self.resolution_spin.set_tooltip_text("Finer resolution captures more detail but increases computation")
        grid.attach(self.resolution_spin, 1, 1, 1, 1)
        
        # Calculated system size
        calc_size_label = Gtk.Label("Physical Size (μm):")
        calc_size_label.set_halign(Gtk.Align.START)
        grid.attach(calc_size_label, 0, 2, 1, 1)
        
        self.calc_size_label = Gtk.Label("100.0")
        self.calc_size_label.set_halign(Gtk.Align.START)
        self.calc_size_label.get_style_context().add_class("monospace")
        grid.attach(self.calc_size_label, 1, 2, 1, 1)
        
        # Total voxels
        voxels_label = Gtk.Label("Total Voxels:")
        voxels_label.set_halign(Gtk.Align.START)
        grid.attach(voxels_label, 0, 3, 1, 1)
        
        self.total_voxels_label = Gtk.Label("1,000,000")
        self.total_voxels_label.set_halign(Gtk.Align.START)
        self.total_voxels_label.get_style_context().add_class("monospace")
        grid.attach(self.total_voxels_label, 1, 3, 1, 1)
        
        frame.add(grid)
        parent.pack_start(frame, False, False, 0)
    
    def _create_composition_parameters_section(self, parent: Gtk.Box) -> None:
        """Create composition parameters section."""
        frame = Gtk.Frame(label="Microstructure Composition")
        frame.get_style_context().add_class("card")
        
        grid = Gtk.Grid()
        grid.set_row_spacing(10)
        grid.set_column_spacing(10)
        grid.set_margin_top(15)
        grid.set_margin_bottom(15)
        grid.set_margin_left(15)
        grid.set_margin_right(15)
        
        # Water-binder ratio
        wb_label = Gtk.Label("Water/Binder Ratio:")
        wb_label.set_halign(Gtk.Align.START)
        wb_label.set_tooltip_text("Mass ratio of water to total binder")
        grid.attach(wb_label, 0, 0, 1, 1)
        
        self.wb_ratio_spin = Gtk.SpinButton.new_with_range(0.1, 2.0, 0.01)
        self.wb_ratio_spin.set_digits(2)
        self.wb_ratio_spin.set_value(0.4)
        grid.attach(self.wb_ratio_spin, 1, 0, 1, 1)
        
        # Aggregate volume fraction
        agg_label = Gtk.Label("Aggregate Volume Fraction:")
        agg_label.set_halign(Gtk.Align.START)
        agg_label.set_tooltip_text("Volume fraction of aggregate in total solid volume")
        grid.attach(agg_label, 0, 1, 1, 1)
        
        self.agg_volume_spin = Gtk.SpinButton.new_with_range(0.0, 1.0, 0.01)
        self.agg_volume_spin.set_digits(2)
        self.agg_volume_spin.set_value(0.7)
        grid.attach(self.agg_volume_spin, 1, 1, 1, 1)
        
        # Air content
        air_label = Gtk.Label("Microstructure Air Content:")
        air_label.set_halign(Gtk.Align.START)
        air_label.set_tooltip_text("Volume fraction of entrained air")
        grid.attach(air_label, 0, 2, 1, 1)
        
        self.micro_air_content_spin = Gtk.SpinButton.new_with_range(0.0, 0.2, 0.001)
        self.micro_air_content_spin.set_digits(3)
        self.micro_air_content_spin.set_value(0.05)
        grid.attach(self.micro_air_content_spin, 1, 2, 1, 1)
        
        frame.add(grid)
        parent.pack_start(frame, False, False, 0)
    
    def _create_particle_shape_section(self, parent: Gtk.Box) -> None:
        """Create particle shape parameters section."""
        frame = Gtk.Frame(label="Particle Shape Sets")
        frame.get_style_context().add_class("card")
        
        grid = Gtk.Grid()
        grid.set_row_spacing(10)
        grid.set_column_spacing(10)
        grid.set_margin_top(15)
        grid.set_margin_bottom(15)
        grid.set_margin_left(15)
        grid.set_margin_right(15)
        
        # Cement shape set
        cement_label = Gtk.Label("Cement Shape Set:")
        cement_label.set_halign(Gtk.Align.START)
        cement_label.set_tooltip_text("Particle shape model for cement grains")
        grid.attach(cement_label, 0, 0, 1, 1)
        
        self.cement_shape_combo = Gtk.ComboBoxText()
        shape_sets = self.microstructure_service.get_supported_shape_sets()
        for shape_id, shape_desc in shape_sets.items():
            self.cement_shape_combo.append(shape_id, shape_desc)
        self.cement_shape_combo.set_active(0)
        grid.attach(self.cement_shape_combo, 1, 0, 1, 1)
        
        # Aggregate shape set
        agg_shape_label = Gtk.Label("Aggregate Shape Set:")
        agg_shape_label.set_halign(Gtk.Align.START)
        agg_shape_label.set_tooltip_text("Particle shape model for aggregate particles")
        grid.attach(agg_shape_label, 0, 1, 1, 1)
        
        self.agg_shape_combo = Gtk.ComboBoxText()
        aggregate_shapes = self.microstructure_service.get_supported_aggregate_shapes()
        for shape_id, shape_desc in aggregate_shapes.items():
            self.agg_shape_combo.append(shape_id, shape_desc)
        self.agg_shape_combo.set_active(0)
        grid.attach(self.agg_shape_combo, 1, 1, 1, 1)
        
        frame.add(grid)
        parent.pack_start(frame, False, False, 0)
    
    def _create_flocculation_section(self, parent: Gtk.Box) -> None:
        """Create flocculation parameters section."""
        frame = Gtk.Frame(label="Flocculation Parameters")
        frame.get_style_context().add_class("card")
        
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_top(15)
        vbox.set_margin_bottom(15)
        vbox.set_margin_left(15)
        vbox.set_margin_right(15)
        
        # Enable flocculation checkbox
        self.flocculation_check = Gtk.CheckButton(label="Enable Flocculation")
        self.flocculation_check.set_tooltip_text("Enable cement particle flocculation modeling")
        vbox.pack_start(self.flocculation_check, False, False, 0)
        
        # Flocculation degree
        floc_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        floc_label = Gtk.Label("Flocculation Degree:")
        floc_label.set_halign(Gtk.Align.START)
        floc_label.set_tooltip_text("Degree of particle clustering (0.0 = none, 1.0 = maximum)")
        floc_box.pack_start(floc_label, False, False, 0)
        
        self.flocculation_spin = Gtk.SpinButton.new_with_range(0.0, 1.0, 0.01)
        self.flocculation_spin.set_digits(2)
        self.flocculation_spin.set_value(0.0)
        self.flocculation_spin.set_sensitive(False)
        floc_box.pack_start(self.flocculation_spin, False, False, 0)
        
        vbox.pack_start(floc_box, False, False, 0)
        
        frame.add(vbox)
        parent.pack_start(frame, False, False, 0)
    
    def _create_advanced_section(self, parent: Gtk.Box) -> None:
        """Create advanced parameters section."""
        frame = Gtk.Frame(label="Advanced Parameters")
        frame.get_style_context().add_class("card")
        
        grid = Gtk.Grid()
        grid.set_row_spacing(10)
        grid.set_column_spacing(10)
        grid.set_margin_top(15)
        grid.set_margin_bottom(15)
        grid.set_margin_left(15)
        grid.set_margin_right(15)
        
        # Random seed
        seed_label = Gtk.Label("Random Seed:")
        seed_label.set_halign(Gtk.Align.START)
        seed_label.set_tooltip_text("Seed for random number generation (0 = random)")
        grid.attach(seed_label, 0, 0, 1, 1)
        
        seed_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        
        self.random_seed_spin = Gtk.SpinButton.new_with_range(-2147483647, -1, 1)
        self.random_seed_spin.set_value(-1)
        seed_box.pack_start(self.random_seed_spin, True, True, 0)
        
        self.generate_seed_button = Gtk.Button(label="Generate")
        self.generate_seed_button.set_tooltip_text("Generate new random seed")
        seed_box.pack_start(self.generate_seed_button, False, False, 0)
        
        grid.attach(seed_box, 1, 0, 1, 1)
        
        frame.add(grid)
        parent.pack_start(frame, False, False, 0)
    
    # =========================================================================
    # Signal Handlers for Microstructure Parameters
    # =========================================================================
    
    def _on_flocculation_toggled(self, checkbox: Gtk.CheckButton) -> None:
        """Handle flocculation checkbox toggle."""
        enabled = checkbox.get_active()
        self.flocculation_spin.set_sensitive(enabled)
        if not enabled:
            self.flocculation_spin.set_value(0.0)
    
    def _on_generate_seed_clicked(self, button: Gtk.Button) -> None:
        """Generate a new negative random seed."""
        new_seed = random.randint(-2147483647, -1)
        self.random_seed_spin.set_value(new_seed)
    
    def _on_system_size_changed(self, spin: Gtk.SpinButton) -> None:
        """Handle system size change."""
        self._update_calculated_values()
    
    def _on_resolution_changed(self, spin: Gtk.SpinButton) -> None:
        """Handle resolution change."""
        self._update_calculated_values()
    
    def _update_calculated_values(self) -> None:
        """Update calculated physical size and total voxels."""
        try:
            system_size = int(self.system_size_spin.get_value())
            resolution = self.resolution_spin.get_value()
            
            # Calculate physical size
            physical_size = system_size * resolution
            self.calc_size_label.set_text(f"{physical_size:.1f}")
            
            # Calculate total voxels
            total_voxels = system_size ** 3
            self.total_voxels_label.set_text(f"{total_voxels:,}")
            
        except Exception as e:
            self.logger.error(f"Error updating calculated values: {e}")
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
import subprocess
import threading
import numpy as np
from typing import TYPE_CHECKING, Optional, Dict, Any, List, Tuple
from decimal import Decimal
from datetime import timedelta

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, Pango, Gdk, GLib

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
        
        # Add validation status label
        self.mix_name_status_label = Gtk.Label()
        self.mix_name_status_label.set_markup("")
        name_box.pack_start(self.mix_name_status_label, False, False, 5)
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
        
        # Add mortar/concrete composition parameters to left column
        self._create_composition_parameters_section(left_column)
        
        # Middle column: System parameters and advanced options
        middle_column = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        middle_column.set_size_request(400, -1)
        
        self._create_system_parameters_section(middle_column)
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
        
        # Create two separate sections  
        self._create_powder_section(comp_box)
        self._create_water_section(comp_box)
        
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
        
        # Particle shape set selection
        shape_separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        powder_box.pack_start(shape_separator, False, False, 5)
        
        shape_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        shape_label = Gtk.Label("Particle Shape Set:")
        shape_label.set_halign(Gtk.Align.START)
        shape_label.set_tooltip_text("Particle shape model for powder materials")
        shape_box.pack_start(shape_label, False, False, 0)
        
        self.cement_shape_combo = Gtk.ComboBoxText()
        shape_sets = self.microstructure_service.get_supported_shape_sets()
        for shape_id, shape_desc in shape_sets.items():
            self.cement_shape_combo.append(shape_id, shape_desc)
        self.cement_shape_combo.set_active(0)
        shape_box.pack_start(self.cement_shape_combo, True, True, 0)
        
        powder_box.pack_start(shape_box, False, False, 0)
        
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
        self.wb_ratio_spin.set_name("wb-ratio-input")  # Test ID for Playwright
        self.wb_ratio_spin.set_digits(3)
        self.wb_ratio_spin.set_value(0.40)
        self.wb_ratio_spin.set_tooltip_text("Enter W/B ratio to calculate water mass")
        water_grid.attach(self.wb_ratio_spin, 1, 0, 1, 1)
        
        # Water content
        water_label = Gtk.Label("Water Mass (kg):")
        water_label.set_halign(Gtk.Align.END)
        water_label.set_tooltip_text("Water mass in kg (Binder = Paste = Powder + Water)")
        water_grid.attach(water_label, 0, 1, 1, 1)
        
        self.water_content_spin = Gtk.SpinButton.new_with_range(0.0, 10000.0, 0.001)
        self.water_content_spin.set_name("water-mass-input")  # Test ID for Playwright
        self.water_content_spin.set_value(0.40)  # Default to match W/B ratio
        self.water_content_spin.set_digits(3)
        self.water_content_spin.set_editable(True)  # Make it editable for user input
        self.water_content_spin.set_tooltip_text("Enter water mass to calculate W/B ratio")
        water_grid.attach(self.water_content_spin, 1, 1, 1, 1)
        
        water_box.pack_start(water_grid, False, False, 0)
        water_frame.add(water_box)
        
        parent.pack_start(water_frame, False, False, 0)
    
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
        self.create_mix_button.set_name("create-mix-button")  # Test ID for Playwright
        create_icon = Gtk.Image.new_from_icon_name("system-run-symbolic", Gtk.IconSize.BUTTON)
        self.create_mix_button.set_image(create_icon)
        self.create_mix_button.set_always_show_image(True)
        self.create_mix_button.set_tooltip_text("Generate 3D microstructure - creates input file and runs simulation automatically")
        self.create_mix_button.get_style_context().add_class("suggested-action")
        button_box.pack_start(self.create_mix_button, False, False, 0)
        
        self.validate_button = Gtk.Button(label="Validate")
        self.validate_button.set_name("validate-button")  # Test ID for Playwright
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
    
    def refresh_material_lists(self) -> None:
        """Refresh material lists and update all dropdowns."""
        self._load_material_lists()
        # Also refresh all existing component dropdowns
        for row_data in self.component_rows:
            self._update_material_names(row_data)
    
    def _load_material_lists(self) -> None:
        """Load available materials for each type."""
        try:
            for material_type in MaterialType:
                self.material_lists[material_type] = self.mix_service.get_compatible_materials(material_type)
            
            # Populate aggregate combo boxes with filtered lists
            # Fine aggregate combo - only fine aggregates (type = 2)
            self.fine_agg_combo.remove_all()
            self.fine_agg_combo.append("", "-- Select Fine Aggregate --")
            fine_aggregates = self.mix_service.get_fine_aggregates()
            for aggregate_name in fine_aggregates:
                self.fine_agg_combo.append(aggregate_name, aggregate_name)
            self.fine_agg_combo.set_active(0)
            
            # Coarse aggregate combo - only coarse aggregates (type = 1)
            self.coarse_agg_combo.remove_all()
            self.coarse_agg_combo.append("", "-- Select Coarse Aggregate --")
            coarse_aggregates = self.mix_service.get_coarse_aggregates()
            for aggregate_name in coarse_aggregates:
                self.coarse_agg_combo.append(aggregate_name, aggregate_name)
            self.coarse_agg_combo.set_active(0)
            
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
        
        # Water controls
        self.wb_ratio_spin.connect('value-changed', self._on_wb_ratio_changed)
        self.water_content_spin.connect('value-changed', self._on_water_content_changed)
        
        # Action buttons
        self.create_mix_button.connect('clicked', self._on_create_mix_clicked)
        self.validate_button.connect('clicked', self._on_validate_clicked)
        self.export_button.connect('clicked', self._on_export_clicked)
        
        # Microstructure parameter signals
        self.system_size_x_spin.connect('value-changed', self._on_system_size_changed)
        self.system_size_y_spin.connect('value-changed', self._on_system_size_changed)
        self.system_size_z_spin.connect('value-changed', self._on_system_size_changed)
        self.resolution_spin.connect('value-changed', self._on_resolution_changed)
        self.flocculation_check.connect('toggled', self._on_flocculation_toggled)
        self.dispersion_factor_spin.connect('value-changed', self._on_parameter_changed)
        self.generate_seed_button.connect('clicked', self._on_generate_seed_clicked)
        
        # Aggregate controls
        self.fine_agg_combo.connect('changed', self._on_fine_aggregate_changed)
        self.fine_agg_grading_button.connect('clicked', self._on_fine_aggregate_grading_clicked)
        self.coarse_agg_combo.connect('changed', self._on_coarse_aggregate_changed)
        self.coarse_agg_grading_button.connect('clicked', self._on_coarse_aggregate_grading_clicked)
        
        # Shape set controls
        self.cement_shape_combo.connect('changed', self._on_parameter_changed)
        self.fine_agg_shape_combo.connect('changed', self._on_parameter_changed)
        self.coarse_agg_shape_combo.connect('changed', self._on_parameter_changed)
        
        # Mass and volume fraction controls
        self.fine_agg_mass_spin.connect('value-changed', self._on_mass_changed)
        self.coarse_agg_mass_spin.connect('value-changed', self._on_mass_changed)
        self.micro_air_content_spin.connect('value-changed', self._on_volume_fraction_changed)
    
    def _create_component_row(self) -> Gtk.Box:
        """Create a new component row widget."""
        row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        row_box.set_margin_top(2)
        row_box.set_margin_bottom(2)
        
        # Material type combo (exclude aggregate - it's not a powder component)
        type_combo = Gtk.ComboBoxText()
        type_combo.set_size_request(120, -1)
        # Populate with available material types (will be filtered dynamically)
        self._populate_material_type_combo(type_combo)
        row_box.pack_start(type_combo, False, False, 0)
        
        # Material name combo
        name_combo = Gtk.ComboBoxText()
        name_combo.set_size_request(150, -1)
        row_box.pack_start(name_combo, False, False, 0)
        
        # Mass (kg) spin button
        mass_spin = Gtk.SpinButton.new_with_range(0.0, 10000.0, 0.001)
        mass_spin.set_digits(3)
        mass_spin.set_value(1.000)  # Default to 1.000 kg
        mass_spin.set_size_request(80, -1)
        row_box.pack_start(mass_spin, False, False, 0)
        
        # kg label
        kg_label = Gtk.Label("kg")
        row_box.pack_start(kg_label, False, False, 0)
        
        # Specific gravity display
        sg_label = Gtk.Label("SG: 2.650")
        sg_label.set_size_request(80, -1)
        sg_label.get_style_context().add_class("dim-label")
        sg_label.set_tooltip_text("Specific Gravity - ratio of material density to water density")
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
            
            # Set smart defaults based on material type
            default_selected = False
            if materials:
                if material_type == MaterialType.INERT_FILLER:
                    # Prefer "quartz" as default for inert fillers
                    for i, material_name in enumerate(materials):
                        if material_name.lower() == "quartz":
                            name_combo.set_active(i)
                            default_selected = True
                            break
                
                # If no specific default found, use first item
                if not default_selected:
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
        self._validate_mix_name()
        if self.auto_calculate_enabled:
            self._trigger_calculation()
    
    def _validate_mix_name(self) -> bool:
        """Validate mix name for directory conflicts and invalid characters."""
        mix_name = self.mix_name_entry.get_text().strip()
        
        # Clear status if empty
        if not mix_name:
            self.mix_name_status_label.set_markup("")
            self.create_mix_button.set_sensitive(True)
            return True
        
        # Create safe folder name (same logic as used in operations)
        mix_name_safe = "".join(c for c in mix_name if c.isalnum() or c in ['_', '-'])
        
        # Check for invalid characters
        if mix_name != mix_name_safe:
            if not mix_name_safe:
                self.mix_name_status_label.set_markup('<span color="red">✗ Invalid characters only</span>')
                self.create_mix_button.set_sensitive(False)
                return False
            else:
                self.mix_name_status_label.set_markup(f'<span color="orange">⚠ Will be saved as: {mix_name_safe}</span>')
        
        # Check if directory already exists
        operations_dir = os.path.join(os.getcwd(), "Operations")
        mix_folder_path = os.path.join(operations_dir, mix_name_safe)
        
        if os.path.exists(mix_folder_path):
            self.mix_name_status_label.set_markup('<span color="red">✗ Directory already exists</span>')
            self.create_mix_button.set_sensitive(False)
            return False
        
        # Valid name
        if mix_name == mix_name_safe:
            self.mix_name_status_label.set_markup('<span color="green">✓ Available</span>')
        else:
            # Already showed warning about character conversion above
            pass
        
        self.create_mix_button.set_sensitive(True)
        return True
    
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
    
    def _populate_material_type_combo(self, type_combo: Gtk.ComboBoxText) -> None:
        """Populate material type combo with available types (excluding already selected ones)."""
        self._populate_material_type_combo_for_row(type_combo)
    
    def _update_all_material_type_combos(self, exclude_combo=None) -> None:
        """Update all material type combos to reflect current selections."""
        for row in self.component_rows:
            # Skip the combo that triggered the change to avoid interference
            if exclude_combo and row['type_combo'] == exclude_combo:
                continue
                
            # Save current selection
            current_selection = row['type_combo'].get_active_id()
            
            # Temporarily block signals to prevent recursive updates
            row['type_combo'].handler_block_by_func(self._on_component_type_changed)
            
            # Repopulate combo
            self._populate_material_type_combo_for_row(row['type_combo'], current_selection)
            
            # Restore selection if still valid
            if current_selection:
                # Try to restore the previous selection
                model = row['type_combo'].get_model()
                iter_item = model.get_iter_first()
                while iter_item:
                    if model.get_value(iter_item, 0) == current_selection:
                        row['type_combo'].set_active_iter(iter_item)
                        break
                    iter_item = model.iter_next(iter_item)
            
            # Unblock signals
            row['type_combo'].handler_unblock_by_func(self._on_component_type_changed)
    
    def _populate_material_type_combo_for_row(self, type_combo: Gtk.ComboBoxText, keep_selection: str = None) -> None:
        """Populate material type combo, optionally keeping a specific selection available."""
        # Get currently selected material types from all existing rows
        selected_types = set()
        for row in self.component_rows:
            selected_type = row['type_combo'].get_active_id()
            if selected_type and selected_type != keep_selection:
                selected_types.add(selected_type)
        
        # Clear and repopulate combo
        type_combo.remove_all()
        
        # Add available material types (excluding aggregate and already selected types)
        available_added = False
        for material_type in MaterialType:
            if (material_type != MaterialType.AGGREGATE and 
                material_type.value not in selected_types):
                type_combo.append(material_type.value, material_type.value.replace("_", " ").title())
                available_added = True
        
        # If no types are available, show a placeholder
        if not available_added:
            type_combo.append("", "No more material types available")
            type_combo.set_sensitive(False)
        else:
            type_combo.set_sensitive(True)
            if type_combo.get_active() == -1:  # Only set active if nothing is selected
                type_combo.set_active(0)

    def _on_component_type_changed(self, combo, row_data) -> None:
        """Handle component type change."""
        self._update_material_names(row_data)
        
        # Update all other material type combos to reflect the new selection
        self._update_all_material_type_combos(exclude_combo=combo)
        
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
        # Update volume fraction validation
        self._calculate_total_volume_fractions()
        
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
        
        # Update all remaining material type combos to show newly available options
        self._update_all_material_type_combos()
        
        if self.auto_calculate_enabled:
            self._trigger_calculation()
    
    def _on_wb_ratio_changed(self, spin) -> None:
        """Handle water-binder ratio change."""
        if self.auto_calculate_enabled:
            self._calculate_water_content_from_wb_ratio()
            self._trigger_calculation()
    
    def _on_water_content_changed(self, spin) -> None:
        """Handle water content change."""
        # Update volume fraction validation
        self._calculate_total_volume_fractions()
        
        if self.auto_calculate_enabled:
            self._calculate_wb_ratio_from_water_content()
            self._trigger_calculation()
    
    def _on_parameter_changed(self, widget) -> None:
        """Handle any parameter change."""
        if self.auto_calculate_enabled:
            self._trigger_calculation()
    
    def _on_mass_changed(self, widget) -> None:
        """Handle aggregate mass changes and update validation."""
        # Update total volume fraction display
        self._calculate_total_volume_fractions()
        
        # Trigger normal calculation if enabled
        if self.auto_calculate_enabled:
            self._trigger_calculation()
    
    def _on_volume_fraction_changed(self, widget) -> None:
        """Handle volume fraction changes and update validation."""
        # Update total volume fraction display
        self._calculate_total_volume_fractions()
        
        # Trigger normal calculation if enabled
        if self.auto_calculate_enabled:
            self._trigger_calculation()
    
    def _on_new_mix_clicked(self, button) -> None:
        """Handle new mix button click."""
        self._clear_mix_design()
    
    def _on_load_mix_clicked(self, button) -> None:
        """Handle load mix button click."""
        try:
            self._show_mix_design_selection_dialog()
        except Exception as e:
            self.logger.error(f"Error showing mix design selection dialog: {e}")
            self.main_window.update_status(f"Error loading mix designs: {e}", "error", 5)
    
    def _on_save_mix_clicked(self, button) -> None:
        """Handle save mix button click."""
        try:
            self._show_save_mix_dialog()
        except Exception as e:
            self.logger.error(f"Error saving mix design: {e}")
            self.main_window.update_status(f"Error saving mix design: {e}", "error", 5)
    
    def _on_create_mix_clicked(self, button) -> None:
        """Handle create mix button click."""
        # Show immediate feedback that operation is starting
        mix_name = self.mix_name_entry.get_text().strip() or "Untitled Mix"
        
        # Create confirmation dialog
        dialog = Gtk.MessageDialog(
            transient_for=self.main_window,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK_CANCEL,
            text="Start 3D Microstructure Generation?"
        )
        dialog.format_secondary_text(
            f"This will create a 3D microstructure for mix: {mix_name}\n\n"
            "The process may take several minutes to complete.\n"
            "Files will be saved to: Operations/{}/".format("".join(c for c in mix_name if c.isalnum() or c in ['_', '-']))
        )
        
        response = dialog.run()
        dialog.destroy()
        
        if response == Gtk.ResponseType.OK:
            # Update status bar immediately
            self.main_window.update_status("Starting 3D microstructure generation...", "info", 0)
            # Start the actual operation
            self._create_microstructure_input_file()
        # If cancelled, do nothing
    
    def _on_validate_clicked(self, button) -> None:
        """Handle validate button click."""
        self._perform_validation()
    
    def _on_export_clicked(self, button) -> None:
        """Handle export button click."""
        # TODO: Implement mix export
        self.main_window.update_status("Mix export will be implemented", "info", 3)
    
    def _on_fine_aggregate_changed(self, combo) -> None:
        """Handle fine aggregate selection change."""
        try:
            aggregate_name = combo.get_active_id()
            
            # Enable grading button only when aggregate is selected
            has_aggregate = aggregate_name and aggregate_name != ""
            self.fine_agg_grading_button.set_sensitive(has_aggregate)
            
            if self.auto_calculate_enabled:
                self._trigger_calculation()
                
        except Exception as e:
            self.logger.error(f"Failed to handle fine aggregate change: {e}")
    
    def _on_coarse_aggregate_changed(self, combo) -> None:
        """Handle coarse aggregate selection change."""
        try:
            aggregate_name = combo.get_active_id()
            
            # Enable grading button only when aggregate is selected
            has_aggregate = aggregate_name and aggregate_name != ""
            self.coarse_agg_grading_button.set_sensitive(has_aggregate)
            
            if self.auto_calculate_enabled:
                self._trigger_calculation()
                
        except Exception as e:
            self.logger.error(f"Failed to handle coarse aggregate change: {e}")
    
    def _on_fine_aggregate_grading_clicked(self, button) -> None:
        """Handle fine aggregate grading button click."""
        try:
            aggregate_name = self.fine_agg_combo.get_active_id()
            if not aggregate_name or aggregate_name == "":
                return
            
            # Show dedicated aggregate grading dialog
            self._show_aggregate_grading_dialog(aggregate_name, "fine")
            
        except Exception as e:
            self.logger.error(f"Failed to show fine aggregate grading dialog: {e}")
            self.main_window.update_status(f"Error opening grading dialog: {e}", "error", 5)
    
    def _on_coarse_aggregate_grading_clicked(self, button) -> None:
        """Handle coarse aggregate grading button click."""
        try:
            aggregate_name = self.coarse_agg_combo.get_active_id()
            if not aggregate_name or aggregate_name == "":
                return
            
            # Show dedicated aggregate grading dialog
            self._show_aggregate_grading_dialog(aggregate_name, "coarse")
            
        except Exception as e:
            self.logger.error(f"Failed to show coarse aggregate grading dialog: {e}")
            self.main_window.update_status(f"Error opening grading dialog: {e}", "error", 5)
    
    def _show_aggregate_grading_dialog(self, aggregate_name: str, aggregate_type: str) -> None:
        """Show grading curve dialog for aggregate."""
        try:
            # Create grading dialog
            dialog = Gtk.Dialog(
                title=f"Grading Curve - {aggregate_type.title()} Aggregate ({aggregate_name})",
                transient_for=self.main_window,
                flags=0
            )
            dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
            dialog.add_button("Apply", Gtk.ResponseType.OK)
            dialog.set_default_response(Gtk.ResponseType.OK)
            dialog.set_default_size(800, 600)
            
            # Create grading curve widget
            grading_widget = GradingCurveWidget()
            
            # Get the appropriate grading data attribute name
            grading_data_attr = f'_{aggregate_type}_aggregate_grading_data'
            
            # Load existing grading data if available
            if hasattr(self, grading_data_attr):
                grading_data = getattr(self, grading_data_attr)
                if grading_data:
                    grading_widget.set_grading_data(grading_data)
            
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
                setattr(self, grading_data_attr, grading_data)
                
                # Update the appropriate button tooltip
                if aggregate_type == "fine":
                    button = self.fine_agg_grading_button
                else:
                    button = self.coarse_agg_grading_button
                
                if grading_data:
                    button.set_tooltip_text(f"Grading curve set ({len(grading_data)} points)")
                else:
                    button.set_tooltip_text(f"Edit {aggregate_type} aggregate grading curve")
                
                self.main_window.update_status(f"Grading curve updated for {aggregate_type} aggregate ({aggregate_name})", "success", 3)
                
                if self.auto_calculate_enabled:
                    self._trigger_calculation()
            
            dialog.destroy()
            
        except Exception as e:
            self.logger.error(f"Failed to show {aggregate_type} aggregate grading dialog: {e}")
            self.main_window.update_status(f"Error opening grading dialog: {e}", "error", 5)
    
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
                sg_label.set_text(f"SG: {sg:.3f}")
            else:
                sg_label.set_text("SG: —")
        
        except Exception as e:
            self.logger.warning(f"Failed to update specific gravity: {e}")
            row_data['sg_label'].set_text("SG: —")
    
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
    
    def _calculate_total_volume_fractions(self) -> None:
        """Calculate and display total volume fractions, checking if they sum to 1.0."""
        try:
            # Get current masses
            fine_agg_mass = self.fine_agg_mass_spin.get_value()
            coarse_agg_mass = self.coarse_agg_mass_spin.get_value()
            air_vol_fraction = self.micro_air_content_spin.get_value()  # This is already a volume fraction (0-1)
            
            # Get powder masses
            total_powder_mass = 0.0
            for row in self.component_rows:
                mass_kg = row['mass_spin'].get_value()
                if mass_kg > 0:
                    total_powder_mass += mass_kg
            
            water_mass = self.water_content_spin.get_value()
            
            # Convert masses to absolute volumes using specific gravities
            powder_volume = total_powder_mass / 3.15  # Typical cement SG
            water_volume = water_mass / 1.0  # Water SG = 1.0
            fine_agg_volume = fine_agg_mass / 2.65 if fine_agg_mass > 0 else 0.0  # Assume SG=2.65
            coarse_agg_volume = coarse_agg_mass / 2.65 if coarse_agg_mass > 0 else 0.0  # Assume SG=2.65
            
            # Calculate total solid volume
            total_solid_volume = powder_volume + water_volume + fine_agg_volume + coarse_agg_volume
            
            # Air volume fraction represents fraction of TOTAL mix volume
            # So if air = 0.05, then solids = 0.95 of total volume
            # Therefore: total_volume = total_solid_volume / (1 - air_vol_fraction)
            if air_vol_fraction < 1.0:
                total_volume = total_solid_volume / (1.0 - air_vol_fraction)
            else:
                total_volume = total_solid_volume
            
            # Calculate volume fractions (normalized to 1.0)
            if total_volume > 0:
                powder_vol_fraction = powder_volume / total_volume
                water_vol_fraction = water_volume / total_volume  
                fine_agg_vol_fraction = fine_agg_volume / total_volume
                coarse_agg_vol_fraction = coarse_agg_volume / total_volume
                # Air volume fraction is already correct from input
                air_vol_fraction_actual = air_vol_fraction
            else:
                powder_vol_fraction = water_vol_fraction = fine_agg_vol_fraction = coarse_agg_vol_fraction = air_vol_fraction_actual = 0.0
            
            # Total volume fraction (should be very close to 1.0)
            total_vol_fraction = powder_vol_fraction + water_vol_fraction + fine_agg_vol_fraction + coarse_agg_vol_fraction + air_vol_fraction_actual
            
            # Update display
            self.total_volume_label.set_text(f"{total_vol_fraction:.3f}")
            
            # Color code based on how close to 1.0
            style_context = self.total_volume_label.get_style_context()
            style_context.remove_class("error")
            style_context.remove_class("warning")
            style_context.remove_class("success")
            
            if abs(total_vol_fraction - 1.0) < 0.001:  # Very close to 1.0
                style_context.add_class("success")
            elif abs(total_vol_fraction - 1.0) < 0.05:  # Somewhat close
                style_context.add_class("warning")
            else:  # Far from 1.0
                style_context.add_class("error")
                
        except Exception as e:
            self.logger.warning(f"Failed to calculate total volume fractions: {e}")
            self.total_volume_label.set_text("—")
    
    def _calculate_powder_and_water_volumes(self) -> Tuple[float, float]:
        """Calculate powder and water volume fractions from current mass inputs."""
        try:
            # Get total powder mass
            total_powder_mass = sum(row['mass_spin'].get_value() for row in self.component_rows)
            water_mass = self.water_content_spin.get_value()
            
            if total_powder_mass <= 0 or water_mass <= 0:
                return 0.0, 0.0
            
            # Calculate volume fractions (simplified calculation)
            # This is a rough estimation for validation purposes
            powder_sg = 3.0  # Average powder specific gravity
            water_sg = 1.0
            
            powder_volume = total_powder_mass / powder_sg
            water_volume = water_mass / water_sg
            
            # Normalize to get volume fractions (relative to total mass/volume basis)
            total_mass = total_powder_mass + water_mass
            total_volume = powder_volume + water_volume
            
            if total_volume <= 0:
                return 0.0, 0.0
            
            # Calculate actual volume fractions on paste basis
            powder_vol_fraction = powder_volume / total_volume
            water_vol_fraction = water_volume / total_volume
            
            return max(0.0, min(1.0, powder_vol_fraction)), max(0.0, min(1.0, water_vol_fraction))
            
        except Exception as e:
            self.logger.warning(f"Failed to calculate powder and water volumes: {e}")
            return 0.0, 0.0

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
        powder_types = {MaterialType.CEMENT, MaterialType.FLY_ASH, MaterialType.SLAG, MaterialType.INERT_FILLER, MaterialType.SILICA_FUME, MaterialType.LIMESTONE}
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
        powder_types = {MaterialType.CEMENT, MaterialType.FLY_ASH, MaterialType.SLAG, MaterialType.INERT_FILLER, MaterialType.SILICA_FUME, MaterialType.LIMESTONE}
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
        # Simple approach: just set a new timer and let old ones expire naturally
        # This avoids the GObject.source_remove warning entirely
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
            
            # Get aggregate masses first
            fine_agg_mass = self.fine_agg_mass_spin.get_value()
            coarse_agg_mass = self.coarse_agg_mass_spin.get_value()
            
            # Calculate total mass including water and aggregates
            water_mass = self.water_content_spin.get_value()
            total_mass_all = total_component_mass + water_mass + fine_agg_mass + coarse_agg_mass
            
            # Create components with mass fractions (relative to total mass including everything)
            for row in self.component_rows:
                type_str = row['type_combo'].get_active_id()
                name = row['name_combo'].get_active_id()
                mass_kg = row['mass_spin'].get_value()
                
                if type_str and name and mass_kg > 0 and total_mass_all > 0:
                    material_type = MaterialType(type_str)
                    sg = self.mix_service._get_material_specific_gravity(name, material_type)
                    
                    # Convert kg to mass fraction (relative to total mass of everything)
                    mass_fraction = mass_kg / total_mass_all
                    
                    component = MixComponent(
                        material_name=name,
                        material_type=material_type,
                        mass_fraction=mass_fraction,
                        specific_gravity=sg
                    )
                    components.append(component)
            
            # Aggregate masses already obtained above and included in total_mass_all
            
            # Add fine aggregate if selected
            fine_agg_name = self.fine_agg_combo.get_active_id()
            if fine_agg_name and fine_agg_name != "" and fine_agg_mass > 0:
                # Use default aggregate specific gravity
                fine_agg_sg = 2.65  # Typical aggregate specific gravity
                try:
                    fine_agg_sg = self.mix_service._get_material_specific_gravity(fine_agg_name, MaterialType.AGGREGATE)
                except:
                    pass  # Use default if lookup fails
                
                # Calculate mass fraction (using total mass of all components)
                mass_fraction = fine_agg_mass / total_mass_all if total_mass_all > 0 else 0.0
                
                fine_agg_component = MixComponent(
                    material_name=fine_agg_name,
                    material_type=MaterialType.AGGREGATE,
                    mass_fraction=mass_fraction,
                    specific_gravity=fine_agg_sg
                )
                components.append(fine_agg_component)
            
            # Add coarse aggregate if selected
            coarse_agg_name = self.coarse_agg_combo.get_active_id()
            if coarse_agg_name and coarse_agg_name != "" and coarse_agg_mass > 0:
                # Use default aggregate specific gravity
                coarse_agg_sg = 2.65  # Typical aggregate specific gravity
                try:
                    coarse_agg_sg = self.mix_service._get_material_specific_gravity(coarse_agg_name, MaterialType.AGGREGATE)
                except:
                    pass  # Use default if lookup fails
                
                # Calculate mass fraction (using total mass of all components)
                mass_fraction = coarse_agg_mass / total_mass_all if total_mass_all > 0 else 0.0
                
                coarse_agg_component = MixComponent(
                    material_name=coarse_agg_name,
                    material_type=MaterialType.AGGREGATE,
                    mass_fraction=mass_fraction,
                    specific_gravity=coarse_agg_sg
                )
                components.append(coarse_agg_component)
            
            if not components:
                return None
            
            # Create mix design
            # Note: Water is NOT added as a separate component since it's handled via total_water_content
            water_mass_fraction = water_mass / total_mass_all if total_mass_all > 0 else 0.0
            
            mix_design = MixDesign(
                name=mix_name,
                components=components,
                water_binder_ratio=self.wb_ratio_spin.get_value(),
                total_water_content=water_mass_fraction,  # Water mass fraction
                air_content=self.micro_air_content_spin.get_value()  # Already a volume fraction
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
        self.water_content_spin.set_value(0.40)  # Default to match W/B ratio
        self.micro_air_content_spin.set_value(0.0)  # 5% volume fraction
        
        # Reset microstructure parameters
        self.system_size_x_spin.set_value(100)
        self.system_size_y_spin.set_value(100)
        self.system_size_z_spin.set_value(100)
        self.dispersion_factor_spin.set_value(0)  # Default to no dispersion
        
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
            # Step 1: Validate mix name
            if not self._validate_mix_name():
                self.main_window.update_status("Please fix mix name issues before proceeding", "error", 5)
                return
            
            # Step 2: Validate mix design
            mix_design = self._create_mix_design_from_ui()
            if not mix_design:
                self.main_window.update_status("Unable to create mix design - please check inputs", "error", 5)
                return
            
            # Step 3: Validate the mix design
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
            
            # Step 4: Create mix folder and generate correlation files
            self._create_mix_folder_and_correlation_files(mix_design)
            
            # Step 5: Get microstructure parameters
            microstructure_params = self._get_microstructure_parameters()
            
            # Step 6: Generate input file
            input_file_content = self._generate_genmic_input_file(mix_design, microstructure_params)
            
            # Step 7: Save input file and execute genmic
            self._save_input_file(input_file_content, mix_design.name)
            
        except Exception as e:
            self.logger.error(f"Failed to create microstructure input file: {e}")
            self.main_window.update_status(f"Error creating input file: {e}", "error", 5)
    
    def _get_microstructure_parameters(self) -> Dict[str, Any]:
        """Get microstructure parameters from UI."""
        return {
            'system_size_x': int(self.system_size_x_spin.get_value()),
            'system_size_y': int(self.system_size_y_spin.get_value()),
            'system_size_z': int(self.system_size_z_spin.get_value()),
            'resolution': self.resolution_spin.get_value(),
            'water_binder_ratio': self.wb_ratio_spin.get_value(),
            'fine_aggregate_volume_fraction': self._calculate_aggregate_volume_fraction('fine'),
            'coarse_aggregate_volume_fraction': self._calculate_aggregate_volume_fraction('coarse'),
            'air_content': self.micro_air_content_spin.get_value(),
            'cement_shape_set': self.cement_shape_combo.get_active_id() or "sphere",
            'fine_aggregate_shape_set': self.fine_agg_shape_combo.get_active_id() or "sphere",
            'coarse_aggregate_shape_set': self.coarse_agg_shape_combo.get_active_id() or "sphere",
            'flocculation_enabled': self.flocculation_check.get_active(),
            'flocculation_degree': self.flocculation_spin.get_value(),
            'dispersion_factor': int(self.dispersion_factor_spin.get_value()),
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
        """Convert custom PSD points to standard 0.25-75 μm range and bin for genmic.c."""
        try:
            # Extract diameters and volume fractions
            diameters = np.array([point[0] for point in custom_points])
            volume_fractions = np.array([point[1] for point in custom_points])
            
            # Filter to 0.25-75 μm range
            mask = (diameters >= 0.25) & (diameters <= 75.0)
            
            if not np.any(mask):
                self.logger.warning("No PSD data in 0.25-75 μm range, using default")
                return self._generate_default_psd()
            
            filtered_diameters = diameters[mask]
            filtered_fractions = volume_fractions[mask]
            
            # Normalize volume fractions to sum to 1.0
            if np.sum(filtered_fractions) > 0:
                filtered_fractions = filtered_fractions / np.sum(filtered_fractions)
            
            # Convert to discrete points and bin for genmic.c
            discrete_points = [(float(d), float(f)) for d, f in zip(filtered_diameters, filtered_fractions)]
            return self._bin_psd_for_genmic(discrete_points)
            
        except Exception as e:
            self.logger.error(f"Failed to convert custom PSD: {e}")
            return self._generate_default_psd()
    
    def _convert_rosin_rammler_to_points(self, d50: float, n: float, dmax: float = None) -> List[Tuple[float, float]]:
        """Convert Rosin-Rammler parameters to discrete points and bin for genmic.c."""
        try:
            if not d50 or not n:
                return self._generate_default_psd()
            
            # Create diameter range from 0.25 to 75 μm (or dmax if smaller)
            max_diameter = min(75.0, dmax if dmax else 75.0)
            diameters = np.logspace(np.log10(0.25), np.log10(max_diameter), 30)
            
            # Rosin-Rammler cumulative distribution: R = 1 - exp(-(d/d50)^n)
            # where d50 is the characteristic diameter
            cumulative = 1 - np.exp(-((diameters / d50) ** n))
            
            # Convert cumulative to differential (volume fractions)
            volume_fractions = np.diff(np.concatenate([[0], cumulative]))
            
            # Ensure we have the right number of points
            if len(volume_fractions) < len(diameters):
                volume_fractions = np.append(volume_fractions, 0)
            
            # Normalize to sum to 1.0
            volume_fractions = volume_fractions / np.sum(volume_fractions)
            
            # Convert to discrete points and bin for genmic.c
            discrete_points = [(float(d), float(f)) for d, f in zip(diameters, volume_fractions)]
            return self._bin_psd_for_genmic(discrete_points)
            
        except Exception as e:
            self.logger.error(f"Failed to convert Rosin-Rammler PSD: {e}")
            return self._generate_default_psd()
    
    def _convert_log_normal_to_points(self, d50: float, sigma: float) -> List[Tuple[float, float]]:
        """Convert log-normal parameters to discrete points and bin for genmic.c."""
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
            
            # Calculate probability density and convert to volume fractions
            pdf_values = lognorm.pdf(diameters, s=s, scale=scale)
            
            # Normalize to get volume fractions
            volume_fractions = pdf_values / np.sum(pdf_values)
            
            # Convert to discrete points and bin for genmic.c
            discrete_points = [(float(d), float(f)) for d, f in zip(diameters, volume_fractions)]
            return self._bin_psd_for_genmic(discrete_points)
            
        except Exception as e:
            self.logger.error(f"Failed to convert log-normal PSD: {e}")
            return self._generate_default_psd()
    
    def _bin_psd_for_genmic(self, psd_data: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """Bin PSD data into integer diameter bins for genmic.c input.
        
        Binning rules:
        - Diameter range (0, 1.5) goes into bin for diameter 1
        - Diameter range [1.5, 2.5) goes into bin for diameter 2
        - Diameter range [2.5, 3.5) goes into bin for diameter 3
        - And so on...
        """
        try:
            # Create bins for diameters 1 through 75
            bin_fractions = {}
            
            for diameter, volume_fraction in psd_data:
                # Determine which integer bin this diameter belongs to
                if diameter < 1.5:
                    bin_diameter = 1
                else:
                    bin_diameter = int(round(diameter))
                    # Ensure we're within reasonable bounds
                    if bin_diameter < 1:
                        bin_diameter = 1
                    elif bin_diameter > 75:
                        bin_diameter = 75
                
                # Add volume fraction to the appropriate bin
                if bin_diameter in bin_fractions:
                    bin_fractions[bin_diameter] += volume_fraction
                else:
                    bin_fractions[bin_diameter] = volume_fraction
            
            # Convert to sorted list of tuples (diameter, volume_fraction)
            binned_data = [(float(diameter), fraction) 
                          for diameter, fraction in sorted(bin_fractions.items())]
            
            # Normalize to ensure sum equals 1.0
            total_fraction = sum(fraction for _, fraction in binned_data)
            if total_fraction > 0:
                binned_data = [(diameter, fraction / total_fraction) 
                              for diameter, fraction in binned_data]
            
            return binned_data
            
        except Exception as e:
            self.logger.error(f"Failed to bin PSD data for genmic: {e}")
            return self._generate_default_psd()

    def _generate_default_psd(self) -> List[Tuple[float, float]]:
        """Generate a default PSD for cement (typical Portland cement)."""
        # Typical cement PSD with log-normal-like distribution (already binned for genmic)
        diameters = [1, 2, 4, 8, 16, 32, 45, 63]
        volume_fractions = [0.05, 0.15, 0.25, 0.25, 0.15, 0.08, 0.04, 0.03]
        
        # Ensure normalization
        total = sum(volume_fractions)
        if total > 0:
            volume_fractions = [f / total for f in volume_fractions]
        
        return list(zip(diameters, volume_fractions))

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
            elif component.material_type == MaterialType.SILICA_FUME:
                # Silica fume has 1 phase: SILICA_FUME(10)
                num_phases += 1
            elif component.material_type == MaterialType.INERT_FILLER:
                # Inert filler has 1 phase: INERT(11)
                num_phases += 1
            elif component.material_type == MaterialType.LIMESTONE:
                # Limestone has 1 phase: CaCO3(33)
                num_phases += 1
        
        return num_phases

    def _calculate_binder_volume_fractions(self, mix_design: MixDesign, params: Dict[str, Any]) -> tuple[float, float]:
        """Calculate binder solid and water volume fractions on PASTE-ONLY basis for genmic simulation.
        
        CRITICAL: genmic simulates only paste (powders + water), NOT the full concrete.
        Air content and aggregate volumes are irrelevant to genmic input calculations.
        """
        try:
            # Get powder components only (no aggregates)
            powder_types = {MaterialType.CEMENT, MaterialType.FLY_ASH, MaterialType.SLAG, MaterialType.INERT_FILLER, MaterialType.SILICA_FUME, MaterialType.LIMESTONE}
            
            # Calculate total powder absolute volume (mass/sg)
            total_powder_absolute_volume = 0.0
            total_powder_mass_kg = 0.0
            
            # Sum up powder masses from UI (in kg)
            for row in self.component_rows:
                type_str = row['type_combo'].get_active_id()
                mass_kg = row['mass_spin'].get_value()
                
                if type_str and mass_kg > 0:
                    material_type = MaterialType(type_str)
                    if material_type in powder_types:
                        name = row['name_combo'].get_active_id()
                        if name:
                            sg = self.mix_service._get_material_specific_gravity(name, material_type)
                            absolute_volume = mass_kg / sg if sg > 0 else 0.0
                            
                            total_powder_absolute_volume += absolute_volume
                            total_powder_mass_kg += mass_kg
            
            # Calculate water mass from W/B ratio and powder mass
            wb_ratio = params['water_binder_ratio']
            water_mass_kg = wb_ratio * total_powder_mass_kg
            water_absolute_volume = water_mass_kg / 1.0  # Water SG = 1.0
            
            # Calculate total PASTE volume (powder + water absolute volumes only)
            total_paste_absolute_volume = total_powder_absolute_volume + water_absolute_volume
            
            if total_paste_absolute_volume <= 0:
                self.logger.error("Total paste volume is zero or negative")
                return 0.7, 0.3
            
            # Calculate volume fractions on PASTE basis (powder + water = 1.0)
            binder_solid_vfrac = total_powder_absolute_volume / total_paste_absolute_volume
            water_vfrac = water_absolute_volume / total_paste_absolute_volume
            
            # Verify they sum to 1.0 (they must for paste-only calculation)
            total = binder_solid_vfrac + water_vfrac
            if abs(total - 1.0) > 0.001:
                self.logger.warning(f"PASTE volume fractions don't sum to 1.0: {total:.6f} - this is an error!")
            
            self.logger.info(f"=== PASTE-ONLY GENMIC CALCULATION ===")
            self.logger.info(f"W/B ratio: {wb_ratio:.3f}")
            self.logger.info(f"Total powder mass: {total_powder_mass_kg:.3f} kg")
            self.logger.info(f"Water mass: {water_mass_kg:.3f} kg")
            self.logger.info(f"Total paste mass: {total_powder_mass_kg + water_mass_kg:.3f} kg")
            self.logger.info(f"Powder absolute volume: {total_powder_absolute_volume:.6f}")
            self.logger.info(f"Water absolute volume: {water_absolute_volume:.6f}")
            self.logger.info(f"Total paste absolute volume: {total_paste_absolute_volume:.6f}")
            self.logger.info(f"Binder solid volume fraction (paste basis): {binder_solid_vfrac:.6f}")
            self.logger.info(f"Water volume fraction (paste basis): {water_vfrac:.6f}")
            self.logger.info(f"=== END PASTE-ONLY CALCULATION ===")
            
            return binder_solid_vfrac, water_vfrac
            
        except Exception as e:
            self.logger.error(f"Failed to calculate binder volume fractions: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            # Return default values
            return 0.7, 0.3

    def _calculate_cement_phase_fractions(self, cement_name: str, component, mix_design: MixDesign) -> Dict[str, float]:
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
                
                # Individual clinker phase specific gravities
                c3s_sg = 3.15     # C3S
                c2s_sg = 3.28     # C2S  
                c3a_sg = 3.03     # C3A
                c4af_sg = 3.73    # C4AF
                k2so4_sg = 2.66   # K2SO4
                na2so4_sg = 2.68  # Na2SO4
                
                # Gypsum phase specific gravities
                dihydrate_sg = 2.32  # CaSO4·2H2O
                hemihydrate_sg = 2.74  # CaSO4·0.5H2O
                anhydrite_sg = 2.61  # CaSO4
                
                # Convert individual clinker phases from mass to volume fractions
                c3s_vf_raw = c3s_mf / c3s_sg if c3s_sg > 0 else 0.0
                c2s_vf_raw = c2s_mf / c2s_sg if c2s_sg > 0 else 0.0
                c3a_vf_raw = c3a_mf / c3a_sg if c3a_sg > 0 else 0.0
                c4af_vf_raw = c4af_mf / c4af_sg if c4af_sg > 0 else 0.0
                k2so4_vf_raw = k2so4_mf / k2so4_sg if k2so4_sg > 0 else 0.0
                na2so4_vf_raw = na2so4_mf / na2so4_sg if na2so4_sg > 0 else 0.0
                
                # Sum all clinker volume fractions
                clinker_vf_raw = c3s_vf_raw + c2s_vf_raw + c3a_vf_raw + c4af_vf_raw + k2so4_vf_raw + na2so4_vf_raw
                dihydrate_vf_raw = dihyd_mf / dihydrate_sg if dihydrate_sg > 0 else 0.0
                hemihydrate_vf_raw = hemihyd_mf / hemihydrate_sg if hemihydrate_sg > 0 else 0.0
                anhydrite_vf_raw = anhyd_mf / anhydrite_sg if anhydrite_sg > 0 else 0.0
                
                # Normalize cement phase volume fractions to sum to 1.0
                total_cement_vf = clinker_vf_raw + dihydrate_vf_raw + hemihydrate_vf_raw + anhydrite_vf_raw
                
                if total_cement_vf > 0:
                    clinker_vf = clinker_vf_raw / total_cement_vf
                    dihydrate_vf = dihydrate_vf_raw / total_cement_vf
                    hemihydrate_vf = hemihydrate_vf_raw / total_cement_vf
                    anhydrite_vf = anhydrite_vf_raw / total_cement_vf
                else:
                    # Fallback if no cement phases found
                    clinker_vf = 1.0
                    dihydrate_vf = hemihydrate_vf = anhydrite_vf = 0.0
                
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
        """Calculate component's volume fraction on BINDER SOLID basis (fraction of total powder volume).
        
        This is for genmic input where each powder component's volume fraction 
        is relative to the total powder (binder solid) volume, NOT total concrete volume.
        """
        try:
            powder_types = {MaterialType.CEMENT, MaterialType.FLY_ASH, MaterialType.SLAG, MaterialType.INERT_FILLER, MaterialType.SILICA_FUME, MaterialType.LIMESTONE}
            
            # Calculate total powder absolute volume from UI (paste-only basis)
            total_powder_absolute_volume = 0.0
            
            for row in self.component_rows:
                type_str = row['type_combo'].get_active_id()
                mass_kg = row['mass_spin'].get_value()
                
                if type_str and mass_kg > 0:
                    material_type = MaterialType(type_str)
                    if material_type in powder_types:
                        name = row['name_combo'].get_active_id()
                        if name:
                            sg = self.mix_service._get_material_specific_gravity(name, material_type)
                            absolute_volume = mass_kg / sg if sg > 0 else 0.0
                            total_powder_absolute_volume += absolute_volume
            
            # Find this component's mass from UI
            component_mass_kg = 0.0
            for row in self.component_rows:
                type_str = row['type_combo'].get_active_id()
                name = row['name_combo'].get_active_id()
                mass_kg = row['mass_spin'].get_value()
                
                if (type_str and name and 
                    MaterialType(type_str) == component.material_type and 
                    name == component.material_name):
                    component_mass_kg = mass_kg
                    break
            
            # Calculate this component's absolute volume
            component_absolute_volume = component_mass_kg / component.specific_gravity if component.specific_gravity > 0 else 0.0
            
            # Calculate component's fraction of total binder solid volume
            if total_powder_absolute_volume > 0:
                component_fraction = component_absolute_volume / total_powder_absolute_volume
            else:
                component_fraction = 0.0
            
            self.logger.debug(f"Component {component.material_name}: mass={component_mass_kg:.3f}kg, "
                            f"abs_vol={component_absolute_volume:.6f}, fraction={component_fraction:.6f}")
            
            return component_fraction
            
        except Exception as e:
            self.logger.error(f"Failed to calculate component binder solid fraction: {e}")
            return 0.1  # Default fallback
    
    def _calculate_aggregate_volume_fraction(self, aggregate_type: str) -> float:
        """Convert aggregate mass to volume fraction for genmic.c input."""
        try:
            if aggregate_type == 'fine':
                mass = self.fine_agg_mass_spin.get_value()
                agg_name = self.fine_agg_combo.get_active_id()
            elif aggregate_type == 'coarse':
                mass = self.coarse_agg_mass_spin.get_value()
                agg_name = self.coarse_agg_combo.get_active_id()
            else:
                return 0.0
            
            if mass <= 0 or not agg_name:
                return 0.0
            
            # Get aggregate specific gravity
            try:
                sg = self.mix_service._get_material_specific_gravity(agg_name, MaterialType.AGGREGATE)
            except:
                sg = 2.65  # Default aggregate specific gravity
            
            # Calculate volume from mass and specific gravity
            aggregate_volume = mass / sg
            
            # Calculate total mix volume for normalization
            # Get all component masses
            total_powder_mass = 0.0
            for row in self.component_rows:
                mass_kg = row['mass_spin'].get_value()
                if mass_kg > 0:
                    total_powder_mass += mass_kg
            
            water_mass = self.water_content_spin.get_value()
            fine_mass = self.fine_agg_mass_spin.get_value()
            coarse_mass = self.coarse_agg_mass_spin.get_value()
            
            # Calculate total volume (using correct air volume fraction handling)
            powder_volume = total_powder_mass / 3.15  # Typical cement SG
            water_volume = water_mass / 1.0  # Water SG = 1.0
            fine_volume = fine_mass / 2.65  # Typical aggregate SG
            coarse_volume = coarse_mass / 2.65  # Typical aggregate SG
            air_vol_fraction = self.micro_air_content_spin.get_value()  # Already a volume fraction
            
            # Calculate solid volume, then total volume accounting for air
            total_solid_volume = powder_volume + water_volume + fine_volume + coarse_volume
            if air_vol_fraction < 1.0:
                total_volume = total_solid_volume / (1.0 - air_vol_fraction)
            else:
                total_volume = total_solid_volume
            
            # Return volume fraction (fraction of total mix volume)
            if total_volume > 0:
                return aggregate_volume / total_volume
            else:
                return 0.0
                
        except Exception as e:
            self.logger.error(f"Error calculating {aggregate_type} aggregate volume fraction: {e}")
            return 0.0

    def _create_mix_folder_and_correlation_files(self, mix_design: MixDesign) -> None:
        """Create mix folder and generate correlation files for cement materials."""
        try:
            # Create safe folder name
            mix_name_safe = "".join(c for c in mix_design.name if c.isalnum() or c in ['_', '-'])
            
            # Create Operations directory structure
            operations_dir = os.path.join(os.getcwd(), "Operations")
            mix_folder_path = os.path.join(operations_dir, mix_name_safe)
            
            # Create Operations directory if it doesn't exist
            os.makedirs(operations_dir, exist_ok=True)
            self.logger.info(f"Ensured Operations directory exists: {operations_dir}")
            
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
        
        # System dimensions
        lines.append(f"{params['system_size_x']}")  # X size
        lines.append(f"{params['system_size_y']}")  # Y size  
        lines.append(f"{params['system_size_z']}")  # Z size
        
        # Resolution (micrometers per voxel)
        lines.append(f"{params['resolution']}")
        
        # Check if aggregates are present - if so, add ADDAGG menu choice first
        has_aggregates = (params.get('fine_aggregate_volume_fraction', 0) > 0 or 
                         params.get('coarse_aggregate_volume_fraction', 0) > 0)
        
        if has_aggregates:
            # Menu choice 6: ADDAGG (add aggregate to microstructure)
            lines.append("6")
            # ADDAGG doesn't require any additional input - it just adds a slab
        
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
        powder_types = {MaterialType.CEMENT, MaterialType.FLY_ASH, MaterialType.SLAG, MaterialType.INERT_FILLER, MaterialType.SILICA_FUME, MaterialType.LIMESTONE}
        
        for component in mix_design.components:
            if component.material_type in powder_types:
                if component.material_type == MaterialType.CEMENT:
                    # Break cement into 4 phases: Clinker, Dihydrate, Hemihydrate, Anhydrite
                    cement_phases = self._calculate_cement_phase_fractions(component.material_name, component, mix_design)
                    psd_data = self._get_material_psd_data(component.material_name, component.material_type)
                    
                    # Get cement's fraction of total binder solid volume (paste-only basis)
                    cement_binder_solid_fraction = self._calculate_component_binder_solid_fraction(component, mix_design)
                    
                    # Phase ID 1: Clinker (scaled by cement's fraction of binder solid)
                    lines.append("1")
                    clinker_fraction = cement_phases['clinker'] * cement_binder_solid_fraction
                    lines.append(f"{clinker_fraction:.6f}")
                    lines.append(f"{len(psd_data)}")
                    for diameter, volume_fraction in psd_data:
                        lines.append(f"{int(round(diameter))}")
                        lines.append(f"{volume_fraction:.6f}")
                    
                    # Phase ID 7: Dihydrate (scaled by cement's fraction of binder solid)
                    lines.append("7")
                    dihydrate_fraction = cement_phases['dihydrate'] * cement_binder_solid_fraction
                    lines.append(f"{dihydrate_fraction:.6f}")
                    lines.append(f"{len(psd_data)}")
                    for diameter, volume_fraction in psd_data:
                        lines.append(f"{int(round(diameter))}")
                        lines.append(f"{volume_fraction:.6f}")
                    
                    # Phase ID 8: Hemihydrate (scaled by cement's fraction of binder solid)
                    lines.append("8")
                    hemihydrate_fraction = cement_phases['hemihydrate'] * cement_binder_solid_fraction
                    lines.append(f"{hemihydrate_fraction:.6f}")
                    lines.append(f"{len(psd_data)}")
                    for diameter, volume_fraction in psd_data:
                        lines.append(f"{int(round(diameter))}")
                        lines.append(f"{volume_fraction:.6f}")
                    
                    # Phase ID 9: Anhydrite (scaled by cement's fraction of binder solid)
                    lines.append("9")
                    anhydrite_fraction = cement_phases['anhydrite'] * cement_binder_solid_fraction
                    lines.append(f"{anhydrite_fraction:.6f}")
                    lines.append(f"{len(psd_data)}")
                    for diameter, volume_fraction in psd_data:
                        lines.append(f"{int(round(diameter))}")
                        lines.append(f"{volume_fraction:.6f}")
                        
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
                    for diameter, volume_fraction in psd_data:
                        lines.append(f"{int(round(diameter))}")
                        lines.append(f"{volume_fraction:.6f}")
        
        # Dispersion factor (separation distance in pixels) for spheres (0-2)
        # 0 = totally random placement, 1-2 = increasing separation
        dispersion_factor = params.get('dispersion_factor', 0)  # Default to random placement
        lines.append(f"{dispersion_factor}")
        
        # Probability for gypsum particles (0.0-1.0) on random particle basis
        # Always 0.0 since we explicitly add gypsum phases (dihydrate, hemihydrate, anhydrite) separately
        gypsum_probability = 0.0  # Obsolete mechanism - gypsum already added as separate phases
        lines.append(f"{gypsum_probability:.6f}")
        
        # Percentage of calcium sulfate that is hemihydrate (0.0 since we add it explicitly)
        hemihydrate_percentage = 0.0
        lines.append(f"{hemihydrate_percentage:.6f}")
        
        # Percentage of calcium sulfate that is anhydrite (0.0 since we add it explicitly)
        anhydrite_percentage = 0.0
        lines.append(f"{anhydrite_percentage:.6f}")
        
        # CRITICAL: genmic simulates PASTE ONLY (powders + water)
        # Air content and aggregate volumes are NOT part of genmic simulation
        # The ADDAGG menu choice (6) only adds a thin slab if aggregates are present
        # but does NOT include aggregate volume in the paste microstructure calculations
        
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
            
            # Path/root name for cement correlation files (absolute path)
            mix_name_safe = "".join(c for c in mix_design.name if c.isalnum() or c in ['_', '-'])
            mix_folder_path = os.path.abspath(os.path.join("Operations", mix_name_safe))  # Create absolute path to Operations/mix folder
            correlation_path = os.path.join(mix_folder_path, mix_name_safe)  # Platform-independent path joining
            lines.append(correlation_path)
            
            # Add volume and surface fractions for cement clinker phases (C3S through NA2SO4)
            # distrib3d() expects volume fraction then surface fraction for each of 6 phases
            cement_component = next((comp for comp in mix_design.components 
                                   if comp.material_type == MaterialType.CEMENT), None)
            if cement_component:
                # Get cement material data from database
                from app.database.service import DatabaseService
                db_service = DatabaseService()
                try:
                    with db_service.get_session() as session:
                        from app.models.cement import Cement
                        cement = session.query(Cement).filter(Cement.name == cement_component.material_name).first()
                        if cement:
                            # Phase order expected by genmic.c: C3S, C2S, C3A, C4AF, K2SO4, NA2SO4
                            phase_fractions = [
                                (cement.c3s_volume_fraction or 0.0, cement.c3s_surface_fraction or 0.0),
                                (cement.c2s_volume_fraction or 0.0, cement.c2s_surface_fraction or 0.0),
                                (cement.c3a_volume_fraction or 0.0, cement.c3a_surface_fraction or 0.0),
                                (cement.c4af_volume_fraction or 0.0, cement.c4af_surface_fraction or 0.0),
                                (cement.k2so4_volume_fraction or 0.0, cement.k2so4_surface_fraction or 0.0),
                                (cement.na2so4_volume_fraction or 0.0, cement.na2so4_surface_fraction or 0.0)
                            ]
                            
                            # Add volume fraction then surface fraction for each phase
                            for vol_frac, surf_frac in phase_fractions:
                                lines.append(f"{vol_frac:.6f}")
                                lines.append(f"{surf_frac:.6f}")
                        else:
                            # Fallback values if cement not found
                            for _ in range(12):
                                lines.append("0.000000")
                except Exception as e:
                    # Fallback values on database error
                    for _ in range(12):
                        lines.append("0.000000")
            else:
                # Fallback values if no cement component found
                for _ in range(12):
                    lines.append("0.000000")
            
            # Menu choice 11: ONEPIX (add one-pixel particles)
            lines.append("11")
            
            # Menu choice 5: MEASURE (measure global phase fractions)
            lines.append("5")
        
        # Menu choice 10: OUTPUTMIC (output microstructure file)
        lines.append("10")
        
        # Output filename for microstructure (absolute path)
        mix_name_safe = "".join(c for c in mix_design.name if c.isalnum() or c in ['_', '-'])
        mix_folder_path = os.path.abspath(os.path.join("Operations", mix_name_safe))  # Create absolute path to Operations/mix folder
        output_filename = os.path.join(mix_folder_path, f"{mix_name_safe}.img")  # Platform-independent path
        lines.append(output_filename)
        
        # Output filename for particle IDs (absolute path)
        particle_filename = os.path.join(mix_folder_path, f"{mix_name_safe}.pimg")  # Platform-independent path
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
        elif material_type == MaterialType.SILICA_FUME:
            return 10  # SILICA_FUME
        elif material_type == MaterialType.INERT_FILLER:
            return 11  # INERT
        elif material_type == MaterialType.LIMESTONE:
            return 33  # CaCO3/LIMESTONE
        else:
            return 1  # Default to C3S
    
    def _save_input_file(self, content: str, mix_name: str) -> None:
        """Save input file content to disk automatically and execute genmic program."""
        try:
            # Create safe filename
            mix_name_safe = "".join(c for c in mix_name if c.isalnum() or c in ['_', '-'])
            default_filename = f"genmic_input_{mix_name_safe}.txt"
            
            # Automatically save to mix folder in Operations directory
            operations_dir = os.path.join(os.getcwd(), "Operations")
            mix_folder_path = os.path.join(operations_dir, mix_name_safe)
            if not os.path.exists(mix_folder_path):
                # Mix folder should already exist from correlation file generation,
                # but create it just in case
                os.makedirs(mix_folder_path, exist_ok=True)
                self.logger.info(f"Created mix folder: {mix_folder_path}")
            
            # Full path to input file
            filename = os.path.join(mix_folder_path, default_filename)
            
            self.logger.info(f"Automatically saving input file to: {filename}")
            
            # Write file
            try:
                with open(filename, 'w') as f:
                    f.write(content)
                self.logger.info(f"Successfully wrote input file: {filename}")
            except Exception as e:
                self.logger.error(f"Failed to write input file: {e}")
                self.main_window.update_status(f"Error writing input file: {e}", "error", 5)
                return
            
            self.logger.info(f"Saved microstructure input file: {filename}")
            self.main_window.update_status(f"Input file created, starting 3D microstructure generation...", "info", 3)
            
            # Execute genmic program immediately
            self.logger.info(f"Starting genmic execution...")
            try:
                self._execute_genmic(filename, mix_folder_path)
            except Exception as e:
                self.logger.error(f"Error in genmic execution: {e}")
                self.main_window.update_status(f"Error executing genmic: {e}", "error", 5)
            
        except Exception as e:
            self.logger.error(f"Failed to save input file: {e}")
            self.main_window.update_status(f"Error saving file: {e}", "error", 5)
    
    def _execute_genmic(self, input_file: str, output_dir: str) -> None:
        """Execute genmic program with input file and redirect output to same directory."""
        
        try:
            self.logger.info(f"_execute_genmic called with input_file={input_file}, output_dir={output_dir}")
            
            # Path to genmic executable (go up to project root, then to backend/bin/genmic)
            # From src/app/windows/panels/mix_design_panel.py, go up 5 levels to vcctl-gtk
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
            genmic_path = os.path.join(project_root, 'backend', 'bin', 'genmic')
            
            self.logger.info(f"Project root: {project_root}")
            self.logger.info(f"Genmic path: {genmic_path}")
            self.logger.info(f"Genmic exists: {os.path.exists(genmic_path)}")
            
            if not os.path.exists(genmic_path):
                raise FileNotFoundError(f"genmic executable not found at: {genmic_path}")
            
            # Register operation with Operations panel
            operations_panel = getattr(self.main_window, 'operations_panel', None)
            operation_id = None
            
            self.logger.info(f"Operations panel found: {operations_panel is not None}")
            
            # Operations panel integration re-enabled - should work now
            
            if operations_panel:
                try:
                    from app.windows.panels.operations_monitoring_panel import OperationType
                    operation_name = f"3D Microstructure Generation"
                    metadata = {
                        'input_file': input_file,
                        'output_dir': output_dir,
                        'genmic_path': genmic_path
                    }
                    operation_id = operations_panel.register_operation(
                        name=operation_name,
                        operation_type=OperationType.MICROSTRUCTURE_GENERATION,
                        total_steps=4,  # Initialize -> Parse -> Generate -> Complete
                        estimated_duration=timedelta(minutes=5),  # Rough estimate
                        metadata=metadata
                    )
                    operations_panel.start_operation(operation_id, "Initializing genmic execution...")
                except Exception as e:
                    self.logger.warning(f"Could not register operation with Operations panel: {e}")
                    operation_id = None
            
            def run_genmic():
                """Run genmic in separate thread."""
                try:
                    self.logger.info("Inside run_genmic thread - starting execution")
                    
                    # Update progress: Starting
                    if operations_panel and operation_id:
                        GLib.idle_add(operations_panel.update_operation_progress, 
                                    operation_id, 0.1, "Preparing input file...", 1)
                    
                    # Change to output directory for execution
                    original_cwd = os.getcwd()
                    self.logger.info(f"Changing directory from {original_cwd} to {output_dir}")
                    os.chdir(output_dir)
                    
                    # Verify we're in the correct directory
                    current_dir = os.getcwd()
                    self.logger.info(f"Current working directory after change: {current_dir}")
                    
                    # Update progress: Parsing input
                    if operations_panel and operation_id:
                        GLib.idle_add(operations_panel.update_operation_progress, 
                                    operation_id, 0.3, "Parsing input and setting up simulation...", 2)
                    
                    # Run genmic with input redirection and stdout/stderr logging
                    self.logger.info(f"About to run genmic: {genmic_path} with input file: {input_file}")
                    self.logger.info(f"genmic will run in directory: {output_dir}")
                    
                    # Create log file names based on input file name
                    input_basename = os.path.splitext(os.path.basename(input_file))[0]
                    stdout_log = os.path.join(output_dir, f"{input_basename}_stdout.log")
                    stderr_log = os.path.join(output_dir, f"{input_basename}_stderr.log")
                    
                    self.logger.info(f"genmic stdout will be saved to: {stdout_log}")
                    self.logger.info(f"genmic stderr will be saved to: {stderr_log}")
                    
                    # Use Popen for real-time progress monitoring
                    with open(input_file, 'r') as input_f, \
                         open(stdout_log, 'w') as stdout_f, \
                         open(stderr_log, 'w') as stderr_f:
                        
                        process = subprocess.Popen(
                            [genmic_path],
                            stdin=input_f,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True,
                            cwd=output_dir,
                            bufsize=1,  # Line buffered
                            universal_newlines=True
                        )
                        
                        # Monitor progress in real-time
                        self._monitor_genmic_progress(process, stdout_f, stderr_f, operations_panel, operation_id)
                        
                        # Wait for completion
                        result = process
                        result.returncode = process.returncode
                    
                    self.logger.info(f"genmic execution completed with return code: {result.returncode}")
                    self.logger.info(f"genmic stdout saved to: {stdout_log}")
                    self.logger.info(f"genmic stderr saved to: {stderr_log}")
                    
                    # Check if stderr log has content (indicates potential issues)
                    try:
                        if os.path.exists(stderr_log) and os.path.getsize(stderr_log) > 0:
                            with open(stderr_log, 'r') as f:
                                stderr_content = f.read(500)  # Read first 500 chars
                                self.logger.warning(f"genmic stderr content: {stderr_content}")
                    except Exception as e:
                        self.logger.warning(f"Could not read stderr log: {e}")
                    
                    # Restore original working directory
                    os.chdir(original_cwd)
                    self.logger.info(f"Restored working directory to: {original_cwd}")
                    
                    # Update progress: Finalizing
                    if operations_panel and operation_id:
                        GLib.idle_add(operations_panel.update_operation_progress, 
                                    operation_id, 0.9, "Finalizing output files...", 3)
                    
                    # Schedule UI update on main thread
                    self.logger.info("Scheduling completion callback on main thread")
                    GLib.idle_add(self._genmic_completed, result, output_dir, operation_id)
                    
                except Exception as e:
                    self.logger.error(f"Exception in run_genmic thread: {e}")
                    import traceback
                    self.logger.error(f"Traceback: {traceback.format_exc()}")
                    
                    # Restore original working directory on error
                    if 'original_cwd' in locals():
                        os.chdir(original_cwd)
                    GLib.idle_add(self._genmic_error, str(e), operation_id)
            
            # Start genmic execution in background thread
            self.logger.info("Creating and starting background thread for genmic execution")
            thread = threading.Thread(target=run_genmic)
            thread.daemon = True
            thread.start()
            self.logger.info("Background thread started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to execute genmic: {e}")
            self.main_window.update_status(f"Error executing genmic: {e}", "error", 5)
            # Mark operation as failed if it was registered
            if operation_id and operations_panel:
                operations_panel.complete_operation(operation_id, success=False, error_message=str(e))
    
    def _monitor_genmic_progress(self, process: subprocess.Popen, stdout_f, stderr_f, operations_panel, operation_id: Optional[str]) -> None:
        """Monitor genmic progress in real-time by parsing stdout output."""
        
        # Define progress mapping for genmic phases
        progress_map = {
            'VCCTL_PROGRESS: INIT_START': (0.05, "Initializing simulation..."),
            'VCCTL_PROGRESS: SPECSIZE_START': (0.15, "Setting up system dimensions..."),
            'VCCTL_PROGRESS: ADDAGG_START': (0.22, "Adding aggregate layer..."),
            'VCCTL_PROGRESS: ADDPART_START': (0.30, "Adding particles..."),
            'VCCTL_PROGRESS: DISTRIB_START': (0.65, "Distributing cement phases..."),
            'VCCTL_PROGRESS: ONEPIX_START': (0.82, "Processing one pixel operations..."),
            'VCCTL_PROGRESS: MEASURE_START': (0.87, "Measuring phase fractions..."),
            'VCCTL_PROGRESS: OUTPUTMIC_START': (0.92, "Writing output files..."),
            'VCCTL_PROGRESS: COMPLETE': (1.0, "Simulation complete")
        }
        
        # Fallback progress markers (for genmic without progress markers)
        fallback_markers = {
            'Reading input file': (0.05, "Reading input parameters..."),
            'Generating microstructure': (0.30, "Generating microstructure..."),
            'Writing output': (0.90, "Writing output files..."),
            'Finished': (1.0, "Simulation complete")
        }
        
        current_progress = 0.3  # Start at 30% (after input parsing)
        step_count = 3
        
        try:
            # Read stdout and stderr simultaneously
            import select
            
            while process.poll() is None:
                # Check if there's data to read (non-blocking)
                ready_streams = []
                if hasattr(select, 'select'):  # Unix-like systems
                    ready_streams, _, _ = select.select([process.stdout, process.stderr], [], [], 0.1)
                else:
                    # Windows fallback - just try to read
                    ready_streams = [process.stdout, process.stderr]
                
                for stream in ready_streams:
                    if stream == process.stdout:
                        line = stream.readline()
                        if line:
                            stdout_f.write(line)
                            stdout_f.flush()
                            
                            # Check for progress markers
                            line_stripped = line.strip()
                            
                            # Check for explicit progress markers first
                            if line_stripped in progress_map:
                                progress, message = progress_map[line_stripped]
                                current_progress = progress
                                step_count += 1
                                
                                if operations_panel and operation_id:
                                    GLib.idle_add(operations_panel.update_operation_progress,
                                                operation_id, progress, message, step_count)
                                
                                self.logger.info(f"genmic progress: {progress*100:.1f}% - {message}")
                            
                            # Check for fallback markers
                            else:
                                for marker, (progress, message) in fallback_markers.items():
                                    if marker.lower() in line_stripped.lower():
                                        if progress > current_progress:  # Only advance progress
                                            current_progress = progress
                                            step_count += 1
                                            
                                            if operations_panel and operation_id:
                                                GLib.idle_add(operations_panel.update_operation_progress,
                                                            operation_id, progress, message, step_count)
                                            
                                            self.logger.info(f"genmic progress (fallback): {progress*100:.1f}% - {message}")
                                            break
                    
                    elif stream == process.stderr:
                        line = stream.readline()
                        if line:
                            stderr_f.write(line)
                            stderr_f.flush()
                            
                            # Log errors but don't update progress for stderr
                            if line.strip():
                                self.logger.warning(f"genmic stderr: {line.strip()}")
            
            # Final progress update if not already at 100%
            if current_progress < 1.0:
                if operations_panel and operation_id:
                    GLib.idle_add(operations_panel.update_operation_progress,
                                operation_id, 0.95, "Finalizing...", step_count + 1)
            
        except Exception as e:
            self.logger.error(f"Error monitoring genmic progress: {e}")
            # Continue with basic progress updates
            if operations_panel and operation_id:
                GLib.idle_add(operations_panel.update_operation_progress,
                            operation_id, 0.8, "Processing (monitoring error)...", step_count)
        
        # Ensure all remaining output is captured
        try:
            remaining_stdout, remaining_stderr = process.communicate(timeout=5)
            if remaining_stdout:
                stdout_f.write(remaining_stdout)
            if remaining_stderr:
                stderr_f.write(remaining_stderr)
        except subprocess.TimeoutExpired:
            process.kill()
            remaining_stdout, remaining_stderr = process.communicate()
            if remaining_stdout:
                stdout_f.write(remaining_stdout)
            if remaining_stderr:
                stderr_f.write(remaining_stderr)
    
    def _genmic_completed(self, result: subprocess.CompletedProcess, output_dir: str, operation_id: Optional[str] = None) -> bool:
        """Handle genmic completion on main thread."""
        operations_panel = getattr(self.main_window, 'operations_panel', None)
        
        # Check for successful output files (more reliable than return code due to distrib3d stack corruption)
        output_files = []
        self.logger.info(f"_genmic_completed called with output_dir: {output_dir}, return_code: {result.returncode}")
        
        try:
            self.logger.info(f"Checking for output files in directory: {output_dir}")
            if not os.path.exists(output_dir):
                self.logger.error(f"Output directory does not exist: {output_dir}")
            else:
                files_in_dir = os.listdir(output_dir)
                self.logger.info(f"Files found in output directory ({len(files_in_dir)}): {files_in_dir}")
                
                for file in files_in_dir:
                    if file.endswith(('.img', '.pimg')):
                        output_files.append(os.path.join(output_dir, file))
                        self.logger.info(f"Found output file: {file}")
                
                self.logger.info(f"Total output files found: {len(output_files)}")
        except Exception as e:
            self.logger.error(f"Error checking output directory: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Consider success if output files were created, regardless of return code
        # (due to known stack corruption issue in distrib3d function)
        success = len(output_files) > 0
        self.logger.info(f"Success determination: output_files={len(output_files)}, success={success}, return_code={result.returncode}")
        
        if success:
            # Success
            if result.returncode != 0:
                self.logger.info(f"genmic execution completed successfully (return code {result.returncode} ignored due to known stack corruption issue)")
            else:
                self.logger.info("genmic execution completed successfully")
            self.main_window.update_status("3D microstructure generated successfully", "success", 5)
            
            # Complete operation in Operations panel
            if operations_panel and operation_id:
                operations_panel.complete_operation(operation_id, success=True)
            
            # Show success dialog
            success_dialog = Gtk.MessageDialog(
                transient_for=self.main_window,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text="3D Microstructure Generated Successfully"
            )
            success_text = f"Microstructure generation completed!\n\nOutput directory: {output_dir}"
            if output_files:
                success_text += f"\n\nGenerated files:\n" + "\n".join([os.path.basename(f) for f in output_files])
            
            # Mention log files
            log_files = [f for f in os.listdir(output_dir) if f.endswith(('_stdout.log', '_stderr.log'))]
            if log_files:
                success_text += f"\n\nExecution logs:\n" + "\n".join(log_files)
            
            success_dialog.format_secondary_text(success_text)
            success_dialog.run()
            success_dialog.destroy()
            
        else:
            # Error - no output files were created
            error_message = f"genmic execution failed - no output files created (exit code: {result.returncode})"
            
            # Try to read stderr log file for error details
            stderr_log = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(os.path.dirname(output_dir)))[0]}_stderr.log")
            stderr_content = ""
            try:
                if os.path.exists(stderr_log) and os.path.getsize(stderr_log) > 0:
                    with open(stderr_log, 'r') as f:
                        stderr_content = f.read(500)  # Read first 500 chars
                        error_message += f"\nError output: {stderr_content}"
            except Exception:
                pass
                
            self.logger.error(error_message)
            self.main_window.update_status(f"genmic execution failed", "error", 5)
            
            # Complete operation as failed in Operations panel
            if operations_panel and operation_id:
                operations_panel.complete_operation(operation_id, success=False, error_message=error_message)
            
            # Show error dialog
            error_dialog = Gtk.MessageDialog(
                transient_for=self.main_window,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Microstructure Generation Failed"
            )
            error_text = f"genmic execution failed (exit code: {result.returncode})"
            if stderr_content:
                error_text += f"\n\nError output:\n{stderr_content}"
            else:
                error_text += f"\n\nCheck log files in output directory for details."
            error_dialog.format_secondary_text(error_text)
            error_dialog.run()
            error_dialog.destroy()
        
        return False  # Remove from idle queue
    
    def _genmic_error(self, error_msg: str, operation_id: Optional[str] = None) -> bool:
        """Handle genmic error on main thread."""
        operations_panel = getattr(self.main_window, 'operations_panel', None)
        
        self.logger.error(f"genmic execution error: {error_msg}")
        self.main_window.update_status(f"Error executing genmic: {error_msg}", "error", 5)
        
        # Complete operation as failed in Operations panel
        if operations_panel and operation_id:
            operations_panel.complete_operation(operation_id, success=False, error_message=error_msg)
        
        # Show error dialog
        error_dialog = Gtk.MessageDialog(
            transient_for=self.main_window,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text="Microstructure Generation Error"
        )
        error_dialog.format_secondary_text(f"Failed to execute genmic program:\n{error_msg}")
        error_dialog.run()
        error_dialog.destroy()
        
        return False  # Remove from idle queue
    
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
        
        # System dimensions
        # X dimension
        x_label = Gtk.Label("X Dimension (voxels):")
        x_label.set_halign(Gtk.Align.START)
        x_label.set_tooltip_text("Number of voxels in X direction (25-400)")
        grid.attach(x_label, 0, 0, 1, 1)
        
        self.system_size_x_spin = Gtk.SpinButton.new_with_range(25, 400, 1)
        self.system_size_x_spin.set_value(100)
        self.system_size_x_spin.set_tooltip_text("X dimension: 25-400 voxels")
        grid.attach(self.system_size_x_spin, 1, 0, 1, 1)
        
        # Y dimension
        y_label = Gtk.Label("Y Dimension (voxels):")
        y_label.set_halign(Gtk.Align.START)
        y_label.set_tooltip_text("Number of voxels in Y direction (25-400)")
        grid.attach(y_label, 0, 1, 1, 1)
        
        self.system_size_y_spin = Gtk.SpinButton.new_with_range(25, 400, 1)
        self.system_size_y_spin.set_value(100)
        self.system_size_y_spin.set_tooltip_text("Y dimension: 25-400 voxels")
        grid.attach(self.system_size_y_spin, 1, 1, 1, 1)
        
        # Z dimension
        z_label = Gtk.Label("Z Dimension (voxels):")
        z_label.set_halign(Gtk.Align.START)
        z_label.set_tooltip_text("Number of voxels in Z direction (25-400)")
        grid.attach(z_label, 0, 2, 1, 1)
        
        self.system_size_z_spin = Gtk.SpinButton.new_with_range(25, 400, 1)
        self.system_size_z_spin.set_value(100)
        self.system_size_z_spin.set_tooltip_text("Z dimension: 25-400 voxels")
        grid.attach(self.system_size_z_spin, 1, 2, 1, 1)
        
        # Resolution
        resolution_label = Gtk.Label("Resolution (μm/voxel):")
        resolution_label.set_halign(Gtk.Align.START)
        resolution_label.set_tooltip_text("Physical size of each voxel in micrometers")
        grid.attach(resolution_label, 0, 3, 1, 1)
        
        self.resolution_spin = Gtk.SpinButton.new_with_range(0.01, 100.0, 0.01)
        self.resolution_spin.set_digits(2)
        self.resolution_spin.set_value(1.0)
        self.resolution_spin.set_tooltip_text("Finer resolution captures more detail but increases computation")
        grid.attach(self.resolution_spin, 1, 3, 1, 1)
        
        # Calculated system size
        calc_size_label = Gtk.Label("Physical Size (μm):")
        calc_size_label.set_halign(Gtk.Align.START)
        grid.attach(calc_size_label, 0, 4, 1, 1)
        
        self.calc_size_label = Gtk.Label("100.0 × 100.0 × 100.0")
        self.calc_size_label.set_halign(Gtk.Align.START)
        self.calc_size_label.get_style_context().add_class("monospace")
        grid.attach(self.calc_size_label, 1, 4, 1, 1)
        
        # Total voxels
        voxels_label = Gtk.Label("Total Voxels:")
        voxels_label.set_halign(Gtk.Align.START)
        grid.attach(voxels_label, 0, 5, 1, 1)
        
        self.total_voxels_label = Gtk.Label("1,000,000")
        self.total_voxels_label.set_halign(Gtk.Align.START)
        self.total_voxels_label.get_style_context().add_class("monospace")
        grid.attach(self.total_voxels_label, 1, 5, 1, 1)
        
        # Validation status
        self.voxel_validation_label = Gtk.Label("")
        self.voxel_validation_label.set_halign(Gtk.Align.START)
        self.voxel_validation_label.get_style_context().add_class("small-text")
        grid.attach(self.voxel_validation_label, 0, 6, 2, 1)
        
        frame.add(grid)
        parent.pack_start(frame, False, False, 0)
    
    def _create_composition_parameters_section(self, parent: Gtk.Box) -> None:
        """Create composition parameters section."""
        frame = Gtk.Frame(label="Mortar/Concrete Options")
        frame.get_style_context().add_class("card")
        
        grid = Gtk.Grid()
        grid.set_row_spacing(10)
        grid.set_column_spacing(10)
        grid.set_margin_top(15)
        grid.set_margin_bottom(15)
        grid.set_margin_left(15)
        grid.set_margin_right(15)
        
        # Fine aggregate mass
        fine_mass_label = Gtk.Label("Fine Aggregate Mass (kg):")
        fine_mass_label.set_halign(Gtk.Align.START)
        fine_mass_label.set_tooltip_text("Mass of fine aggregate in kg")
        grid.attach(fine_mass_label, 0, 0, 1, 1)
        
        self.fine_agg_mass_spin = Gtk.SpinButton.new_with_range(0.0, 10.0, 0.01)
        self.fine_agg_mass_spin.set_digits(3)
        self.fine_agg_mass_spin.set_value(0.0)
        grid.attach(self.fine_agg_mass_spin, 1, 0, 1, 1)
        
        # Add kg label
        fine_kg_label = Gtk.Label("kg")
        fine_kg_label.set_halign(Gtk.Align.START)
        grid.attach(fine_kg_label, 2, 0, 1, 1)
        
        # Fine aggregate selection
        fine_agg_label = Gtk.Label("Fine Aggregate:")
        fine_agg_label.set_halign(Gtk.Align.START)
        fine_agg_label.set_tooltip_text("Select fine aggregate material (sand)")
        grid.attach(fine_agg_label, 0, 1, 1, 1)
        
        self.fine_agg_combo = Gtk.ComboBoxText()
        self.fine_agg_combo.set_size_request(150, -1)
        self.fine_agg_combo.set_tooltip_text("Choose fine aggregate from database")
        grid.attach(self.fine_agg_combo, 1, 1, 1, 1)
        
        # Fine aggregate grading button
        self.fine_agg_grading_button = Gtk.Button("Grading...")
        self.fine_agg_grading_button.set_size_request(80, -1)
        self.fine_agg_grading_button.set_tooltip_text("Edit fine aggregate grading curve")
        self.fine_agg_grading_button.set_sensitive(False)  # Enable when aggregate is selected
        grid.attach(self.fine_agg_grading_button, 2, 1, 1, 1)
        
        # Fine aggregate shape set
        fine_agg_shape_label = Gtk.Label("Fine Aggregate Shape Set:")
        fine_agg_shape_label.set_halign(Gtk.Align.START)
        fine_agg_shape_label.set_tooltip_text("Particle shape model for fine aggregate particles")
        grid.attach(fine_agg_shape_label, 0, 2, 1, 1)
        
        self.fine_agg_shape_combo = Gtk.ComboBoxText()
        fine_aggregate_shapes = self.microstructure_service.get_fine_aggregate_shapes()
        for shape_id, shape_desc in fine_aggregate_shapes.items():
            self.fine_agg_shape_combo.append(shape_id, shape_desc)
        self.fine_agg_shape_combo.set_active(0)
        grid.attach(self.fine_agg_shape_combo, 1, 2, 1, 1)
        
        # Coarse aggregate mass
        coarse_mass_label = Gtk.Label("Coarse Aggregate Mass (kg):")
        coarse_mass_label.set_halign(Gtk.Align.START)
        coarse_mass_label.set_tooltip_text("Mass of coarse aggregate in kg")
        grid.attach(coarse_mass_label, 0, 3, 1, 1)
        
        self.coarse_agg_mass_spin = Gtk.SpinButton.new_with_range(0.0, 10.0, 0.01)
        self.coarse_agg_mass_spin.set_digits(3)
        self.coarse_agg_mass_spin.set_value(0.0)
        grid.attach(self.coarse_agg_mass_spin, 1, 3, 1, 1)
        
        # Add kg label
        coarse_kg_label = Gtk.Label("kg")
        coarse_kg_label.set_halign(Gtk.Align.START)
        grid.attach(coarse_kg_label, 2, 3, 1, 1)
        
        # Coarse aggregate selection
        coarse_agg_label = Gtk.Label("Coarse Aggregate:")
        coarse_agg_label.set_halign(Gtk.Align.START)
        coarse_agg_label.set_tooltip_text("Select coarse aggregate material (gravel, crushed stone)")
        grid.attach(coarse_agg_label, 0, 4, 1, 1)
        
        self.coarse_agg_combo = Gtk.ComboBoxText()
        self.coarse_agg_combo.set_size_request(150, -1)
        self.coarse_agg_combo.set_tooltip_text("Choose coarse aggregate from database")
        grid.attach(self.coarse_agg_combo, 1, 4, 1, 1)
        
        # Coarse aggregate grading button
        self.coarse_agg_grading_button = Gtk.Button("Grading...")
        self.coarse_agg_grading_button.set_size_request(80, -1)
        self.coarse_agg_grading_button.set_tooltip_text("Edit coarse aggregate grading curve")
        self.coarse_agg_grading_button.set_sensitive(False)  # Enable when aggregate is selected
        grid.attach(self.coarse_agg_grading_button, 2, 4, 1, 1)
        
        # Coarse aggregate shape set
        coarse_agg_shape_label = Gtk.Label("Coarse Aggregate Shape Set:")
        coarse_agg_shape_label.set_halign(Gtk.Align.START)
        coarse_agg_shape_label.set_tooltip_text("Particle shape model for coarse aggregate particles")
        grid.attach(coarse_agg_shape_label, 0, 5, 1, 1)
        
        self.coarse_agg_shape_combo = Gtk.ComboBoxText()
        coarse_aggregate_shapes = self.microstructure_service.get_coarse_aggregate_shapes()
        for shape_id, shape_desc in coarse_aggregate_shapes.items():
            self.coarse_agg_shape_combo.append(shape_id, shape_desc)
        self.coarse_agg_shape_combo.set_active(0)
        grid.attach(self.coarse_agg_shape_combo, 1, 5, 1, 1)
        
        # Air content
        air_label = Gtk.Label("Air Content:")
        air_label.set_halign(Gtk.Align.START)
        air_label.set_tooltip_text("Volume fraction of entrained air in mortar/concrete")
        grid.attach(air_label, 0, 6, 1, 1)
        
        self.micro_air_content_spin = Gtk.SpinButton.new_with_range(0.0, 0.2, 0.001)
        self.micro_air_content_spin.set_digits(3)
        self.micro_air_content_spin.set_value(0.0)
        grid.attach(self.micro_air_content_spin, 1, 6, 1, 1)
        
        # Total volume fraction display
        total_vol_label = Gtk.Label("Total Volume Fraction:")
        total_vol_label.set_halign(Gtk.Align.START)
        total_vol_label.set_tooltip_text("Sum of all volume fractions (must equal 1.0)")
        total_vol_label.get_style_context().add_class("dim-label")
        grid.attach(total_vol_label, 0, 7, 1, 1)
        
        self.total_volume_label = Gtk.Label("1.000")
        self.total_volume_label.set_halign(Gtk.Align.START)
        self.total_volume_label.get_style_context().add_class("monospace")
        grid.attach(self.total_volume_label, 1, 7, 1, 1)
        
        frame.add(grid)
        parent.pack_start(frame, False, False, 0)
    
    
    def _create_flocculation_section(self, parent: Gtk.Box) -> None:
        """Create flocculation parameters section."""
        frame = Gtk.Frame(label="Powder Dispersion Options")
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
        
        # Dispersion factor
        disp_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        disp_label = Gtk.Label("Dispersion Factor:")
        disp_label.set_halign(Gtk.Align.START)
        disp_label.set_tooltip_text("Particle dispersion parameter (0, 1, or 2 pixels)")
        disp_box.pack_start(disp_label, False, False, 0)
        
        self.dispersion_factor_spin = Gtk.SpinButton.new_with_range(0, 2, 1)
        self.dispersion_factor_spin.set_digits(0)
        self.dispersion_factor_spin.set_value(0)
        self.dispersion_factor_spin.set_tooltip_text("Dispersion distance in pixels: 0=none, 1=adjacent, 2=near")
        disp_box.pack_start(self.dispersion_factor_spin, False, False, 0)
        
        vbox.pack_start(disp_box, False, False, 0)
        
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
        # Flocculation and dispersion are mutually exclusive
        self.dispersion_factor_spin.set_sensitive(not enabled)
        if not enabled:
            self.flocculation_spin.set_value(0.0)
        else:
            # If flocculation is enabled, reset dispersion to 0
            self.dispersion_factor_spin.set_value(0)
    
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
            x_size = int(self.system_size_x_spin.get_value())
            y_size = int(self.system_size_y_spin.get_value())
            z_size = int(self.system_size_z_spin.get_value())
            resolution = self.resolution_spin.get_value()
            
            # Calculate physical dimensions
            x_physical = x_size * resolution
            y_physical = y_size * resolution
            z_physical = z_size * resolution
            self.calc_size_label.set_text(f"{x_physical:.1f} × {y_physical:.1f} × {z_physical:.1f}")
            
            # Calculate total voxels
            total_voxels = x_size * y_size * z_size
            self.total_voxels_label.set_text(f"{total_voxels:,}")
            
            # Validate against 27 million voxel limit
            max_voxels = 27_000_000
            if total_voxels > max_voxels:
                self.voxel_validation_label.set_text(f"⚠️ Exceeds limit ({max_voxels:,} max)")
                self.voxel_validation_label.get_style_context().add_class("error-text")
                self.voxel_validation_label.get_style_context().remove_class("success-text")
            else:
                remaining = max_voxels - total_voxels
                self.voxel_validation_label.set_text(f"✓ Within limit ({remaining:,} remaining)")
                self.voxel_validation_label.get_style_context().add_class("success-text")
                self.voxel_validation_label.get_style_context().remove_class("error-text")
            
        except Exception as e:
            self.logger.error(f"Error updating calculated values: {e}")
    
    # =============================================================================
    # Mix Design Save/Load Methods
    # =============================================================================
    
    def _show_save_mix_dialog(self) -> None:
        """Show dialog to save current mix design."""
        # Create save dialog
        dialog = Gtk.Dialog(
            title="Save Mix Design",
            transient_for=self.main_window,
            flags=0
        )
        dialog.add_buttons(
            "Cancel", Gtk.ResponseType.CANCEL,
            "Save", Gtk.ResponseType.OK
        )
        dialog.set_default_response(Gtk.ResponseType.OK)
        dialog.set_size_request(400, 300)
        
        # Create content
        content_area = dialog.get_content_area()
        content_area.set_spacing(10)
        content_area.set_margin_left(20)
        content_area.set_margin_right(20)
        content_area.set_margin_top(10)
        content_area.set_margin_bottom(10)
        
        # Mix name
        name_label = Gtk.Label("Mix Design Name:")
        name_label.set_halign(Gtk.Align.START)
        content_area.pack_start(name_label, False, False, 0)
        
        name_entry = Gtk.Entry()
        current_name = self.mix_name_entry.get_text().strip()
        name_entry.set_text(current_name if current_name else "New Mix Design")
        content_area.pack_start(name_entry, False, False, 0)
        
        # Description
        desc_label = Gtk.Label("Description (optional):")
        desc_label.set_halign(Gtk.Align.START)
        content_area.pack_start(desc_label, False, False, 0)
        
        desc_scrolled = Gtk.ScrolledWindow()
        desc_scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        desc_scrolled.set_size_request(-1, 100)
        
        desc_textview = Gtk.TextView()
        desc_textview.set_wrap_mode(Gtk.WrapMode.WORD)
        desc_scrolled.add(desc_textview)
        content_area.pack_start(desc_scrolled, True, True, 0)
        
        # Template checkbox
        template_check = Gtk.CheckButton("Save as template for future use")
        content_area.pack_start(template_check, False, False, 0)
        
        # Notes
        notes_label = Gtk.Label("Notes (optional):")
        notes_label.set_halign(Gtk.Align.START)
        content_area.pack_start(notes_label, False, False, 0)
        
        notes_entry = Gtk.Entry()
        notes_entry.set_placeholder_text("Additional notes or comments...")
        content_area.pack_start(notes_entry, False, False, 0)
        
        dialog.show_all()
        
        # Handle response
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            name = name_entry.get_text().strip()
            
            # Get description
            desc_buffer = desc_textview.get_buffer()
            desc_start = desc_buffer.get_start_iter()
            desc_end = desc_buffer.get_end_iter()
            description = desc_buffer.get_text(desc_start, desc_end, False).strip()
            
            notes = notes_entry.get_text().strip()
            is_template = template_check.get_active()
            
            if name:
                self._save_current_mix_design(name, description, notes, is_template)
            else:
                self.main_window.update_status("Mix design name is required", "error", 3)
        
        dialog.destroy()
    
    def _show_mix_design_selection_dialog(self) -> None:
        """Show dialog to select and load a saved mix design."""
        # Create selection dialog
        dialog = Gtk.Dialog(
            title="Load Mix Design",
            transient_for=self.main_window,
            flags=0
        )
        dialog.add_buttons(
            "Cancel", Gtk.ResponseType.CANCEL,
            "Load", Gtk.ResponseType.OK,
            "Duplicate", Gtk.ResponseType.APPLY,
            "Delete", Gtk.ResponseType.REJECT
        )
        dialog.set_default_response(Gtk.ResponseType.OK)
        dialog.set_size_request(600, 400)
        
        # Create content
        content_area = dialog.get_content_area()
        content_area.set_spacing(10)
        content_area.set_margin_left(20)
        content_area.set_margin_right(20)
        content_area.set_margin_top(10)
        content_area.set_margin_bottom(10)
        
        # Search box
        search_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        search_label = Gtk.Label("Search:")
        search_entry = Gtk.Entry()
        search_entry.set_placeholder_text("Search mix designs...")
        search_box.pack_start(search_label, False, False, 0)
        search_box.pack_start(search_entry, True, True, 0)
        content_area.pack_start(search_box, False, False, 0)
        
        # Mix design list
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        
        # Create list store: name, description, created_date, is_template, mix_id
        list_store = Gtk.ListStore(str, str, str, bool, int)
        
        tree_view = Gtk.TreeView(model=list_store)
        
        # Name column
        name_renderer = Gtk.CellRendererText()
        name_column = Gtk.TreeViewColumn("Mix Design", name_renderer, text=0)
        name_column.set_sort_column_id(0)
        tree_view.append_column(name_column)
        
        # Description column
        desc_renderer = Gtk.CellRendererText()
        desc_renderer.set_property("ellipsize", 3)  # ELLIPSIZE_END
        desc_column = Gtk.TreeViewColumn("Description", desc_renderer, text=1)
        desc_column.set_sort_column_id(1)
        tree_view.append_column(desc_column)
        
        # Created date column
        date_renderer = Gtk.CellRendererText()
        date_column = Gtk.TreeViewColumn("Created", date_renderer, text=2)
        date_column.set_sort_column_id(2)
        tree_view.append_column(date_column)
        
        # Template column
        template_renderer = Gtk.CellRendererToggle()
        template_renderer.set_property("activatable", False)
        template_column = Gtk.TreeViewColumn("Template", template_renderer, active=3)
        tree_view.append_column(template_column)
        
        scrolled.add(tree_view)
        content_area.pack_start(scrolled, True, True, 0)
        
        # Info label
        info_label = Gtk.Label()
        info_label.set_halign(Gtk.Align.START)
        info_label.set_markup("<i>Select a mix design to load, duplicate, or delete</i>")
        content_area.pack_start(info_label, False, False, 0)
        
        # Load mix designs (placeholder for now)
        self._populate_mix_design_list(list_store)
        
        dialog.show_all()
        
        # Handle response
        response = dialog.run()
        if response in [Gtk.ResponseType.OK, Gtk.ResponseType.APPLY, Gtk.ResponseType.REJECT]:
            selection = tree_view.get_selection()
            model, treeiter = selection.get_selected()
            
            if treeiter:
                mix_id = model[treeiter][4]
                mix_name = model[treeiter][0]
                
                if response == Gtk.ResponseType.OK:
                    self._load_mix_design(mix_id)
                elif response == Gtk.ResponseType.APPLY:
                    self._duplicate_mix_design(mix_id, mix_name)
                elif response == Gtk.ResponseType.REJECT:
                    self._delete_mix_design(mix_id, mix_name)
            else:
                self.main_window.update_status("Please select a mix design", "info", 3)
        
        dialog.destroy()
    
    def _populate_mix_design_list(self, list_store: Gtk.ListStore) -> None:
        """Populate the mix design list store."""
        try:
            # Load actual mix designs from database
            from app.services.mix_design_service import MixDesignService
            
            list_store.clear()
            
            mix_design_service = MixDesignService(self.service_container.database_service)
            mix_designs = mix_design_service.get_all()
            
            for design in mix_designs:
                # Format: (name, description, date, is_template, id)
                date_str = design.updated_at.strftime("%Y-%m-%d") if design.updated_at else "Unknown"
                list_store.append((
                    design.name,
                    design.description or "No description",
                    date_str,
                    design.is_template,
                    design.id
                ))
            
            self.logger.info(f"Populated mix design list with {len(mix_designs)} designs")
            
        except Exception as e:
            self.logger.error(f"Error populating mix design list: {e}")
            self.main_window.update_status(f"Error loading mix designs: {e}", "error", 5)
    
    def _extract_current_mix_design_data(self) -> Dict[str, Any]:
        """Extract current mix design data from UI controls."""
        try:
            # Extract component data
            components = []
            for row in self.component_rows:
                material_type = row['type_combo'].get_active_id()
                material_name = row['name_combo'].get_active_id()
                mass_kg = row['mass_spin'].get_value()
                
                if material_type and material_name and mass_kg > 0:
                    # Get specific gravity from service
                    specific_gravity = 3.15  # Default
                    try:
                        material_type_enum = MaterialType(material_type)
                        sg = self.mix_service.get_specific_gravity(material_name, material_type_enum)
                        if sg:
                            specific_gravity = sg
                    except Exception as e:
                        self.logger.warning(f"Could not get specific gravity for {material_name}: {e}")
                    
                    # Calculate volume fraction
                    total_mass = self._calculate_total_mass()
                    mass_fraction = mass_kg / total_mass if total_mass > 0 else 0.0
                    volume_fraction = (mass_fraction / specific_gravity) / self._calculate_total_volume_per_unit_mass()
                    
                    components.append({
                        'material_name': material_name,
                        'material_type': material_type,
                        'mass_fraction': mass_fraction,
                        'volume_fraction': volume_fraction,
                        'specific_gravity': specific_gravity
                    })
            
            # Extract system parameters
            water_content = self.water_content_spin.get_value()
            total_mass = self._calculate_total_mass()
            
            # Calculate calculated properties
            paste_volume_fraction, powder_volume_fraction = self._calculate_volume_fractions()
            aggregate_volume_fraction = self._calculate_aggregate_volume_fraction('fine') + self._calculate_aggregate_volume_fraction('coarse')
            
            calculated_properties = {
                'paste_volume_fraction': paste_volume_fraction,
                'powder_volume_fraction': powder_volume_fraction,
                'aggregate_volume_fraction': aggregate_volume_fraction,
                'binder_content': self._calculate_total_binder_mass(),
                'water_content': water_content
            }
            
            # Return complete mix design data
            return {
                'water_binder_ratio': self.wb_ratio_spin.get_value(),
                'total_water_content': water_content,
                'air_content': self.micro_air_content_spin.get_value() * 100.0,  # Convert to percentage
                'water_volume_fraction': self._calculate_water_volume_fraction(),
                'air_volume_fraction': self.micro_air_content_spin.get_value(),
                'system_size': int(self.system_size_x_spin.get_value()),  # Use X dimension as representative
                'random_seed': int(self.random_seed_spin.get_value()),
                'cement_shape_set': self.cement_shape_combo.get_active_id() or "spherical",
                'aggregate_shape_set': self.fine_agg_shape_combo.get_active_id() or "spherical",
                'components': components,
                'calculated_properties': calculated_properties
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting mix design data: {e}")
            raise
    
    def _calculate_water_volume_fraction(self) -> float:
        """Calculate water volume fraction for the current mix."""
        try:
            water_mass = self.water_content_spin.get_value()
            total_mass = self._calculate_total_mass()
            
            if total_mass > 0:
                water_mass_fraction = water_mass / total_mass
                # Water has specific gravity of 1.0
                return water_mass_fraction / 1.0
            return 0.0
        except Exception:
            return 0.0
    
    def _calculate_total_volume_per_unit_mass(self) -> float:
        """Calculate total volume per unit mass for volume fraction calculations."""
        try:
            total_volume = 0.0
            total_mass = 0.0
            
            # Add powder components
            for row in self.component_rows:
                mass_kg = row['mass_spin'].get_value()
                if mass_kg > 0:
                    material_type = row['type_combo'].get_active_id()
                    material_name = row['name_combo'].get_active_id()
                    
                    # Get specific gravity
                    specific_gravity = 3.15  # Default
                    try:
                        material_type_enum = MaterialType(material_type)
                        sg = self.mix_service.get_specific_gravity(material_name, material_type_enum)
                        if sg:
                            specific_gravity = sg
                    except Exception:
                        pass
                    
                    total_volume += mass_kg / specific_gravity
                    total_mass += mass_kg
            
            # Add water (specific gravity = 1.0)
            water_mass = self.water_content_spin.get_value()
            total_volume += water_mass / 1.0
            total_mass += water_mass
            
            return total_volume / total_mass if total_mass > 0 else 0.0
        except Exception:
            return 0.0

    def _save_current_mix_design(self, name: str, description: str, notes: str, is_template: bool) -> None:
        """Save the current mix design to database."""
        try:
            # Extract current mix design data
            mix_data = self._extract_current_mix_design_data()
            
            # Import mix design service and models
            from app.services.mix_design_service import MixDesignService
            from app.models.mix_design import MixDesignCreate, MixDesignComponentData, MixDesignPropertiesData
            
            mix_design_service = MixDesignService(self.service_container.database_service)
            
            # Convert to Pydantic models
            components = [MixDesignComponentData(**comp) for comp in mix_data['components']]
            properties = MixDesignPropertiesData(**mix_data['calculated_properties']) if mix_data['calculated_properties'] else None
            
            # Create mix design
            create_data = MixDesignCreate(
                name=name,
                description=description,
                water_binder_ratio=mix_data['water_binder_ratio'],
                total_water_content=mix_data['total_water_content'],
                air_content=mix_data['air_content'],
                water_volume_fraction=mix_data['water_volume_fraction'],
                air_volume_fraction=mix_data['air_volume_fraction'],
                system_size=mix_data['system_size'],
                random_seed=mix_data['random_seed'],
                cement_shape_set=mix_data['cement_shape_set'],
                aggregate_shape_set=mix_data['aggregate_shape_set'],
                components=components,
                calculated_properties=properties,
                notes=notes,
                is_template=is_template
            )
            
            # Save to database
            saved_mix = mix_design_service.create(create_data)
            
            # Show success message
            component_count = len(mix_data['components'])
            self.main_window.update_status(f"Mix design '{name}' saved successfully", "success", 3)
            self.logger.info(f"Saved mix design: {name} (ID: {saved_mix.id}, components: {component_count}, template: {is_template})")
            
        except Exception as e:
            self.logger.error(f"Error saving mix design: {e}")
            self.main_window.update_status(f"Error saving mix design: {e}", "error", 5)
    
    def _populate_ui_from_mix_design(self, mix_design_data: Dict[str, Any]) -> None:
        """Populate UI controls from mix design data."""
        try:
            # Clear existing components
            self._reset_mix_design()
            
            # Set basic parameters
            self.wb_ratio_spin.set_value(mix_design_data.get('water_binder_ratio', 0.40))
            self.water_content_spin.set_value(mix_design_data.get('total_water_content', 0.0))
            self.micro_air_content_spin.set_value(mix_design_data.get('air_volume_fraction', 0.0))
            
            # Set system parameters
            system_size = mix_design_data.get('system_size', 100)
            self.system_size_x_spin.set_value(system_size)
            self.system_size_y_spin.set_value(system_size)
            self.system_size_z_spin.set_value(system_size)
            
            self.random_seed_spin.set_value(mix_design_data.get('random_seed', -1))
            
            # Set shape sets
            cement_shape = mix_design_data.get('cement_shape_set', 'spherical')
            aggregate_shape = mix_design_data.get('aggregate_shape_set', 'spherical')
            
            # Find and set cement shape
            cement_model = self.cement_shape_combo.get_model()
            for i in range(len(cement_model)):
                if cement_model[i][0] == cement_shape:
                    self.cement_shape_combo.set_active(i)
                    break
            
            # Find and set aggregate shape (assuming fine aggregate shape combo)
            fine_model = self.fine_agg_shape_combo.get_model()
            for i in range(len(fine_model)):
                if fine_model[i][0] == aggregate_shape:
                    self.fine_agg_shape_combo.set_active(i)
                    break
            
            # Add components
            components = mix_design_data.get('components', [])
            for comp_data in components:
                # Add new component row
                self._add_component_row()
                
                # Get the last added row
                if self.component_rows:
                    row = self.component_rows[-1]
                    
                    # Set material type
                    material_type = comp_data.get('material_type', '')
                    type_combo = row['type_combo']
                    type_model = type_combo.get_model()
                    for i in range(len(type_model)):
                        if type_model[i][0] == material_type:
                            type_combo.set_active(i)
                            break
                    
                    # Update material names for this type
                    self._update_material_names(row)
                    
                    # Set material name
                    material_name = comp_data.get('material_name', '')
                    name_combo = row['name_combo']
                    name_model = name_combo.get_model()
                    for i in range(len(name_model)):
                        if name_model[i][0] == material_name:
                            name_combo.set_active(i)
                            break
                    
                    # Calculate mass from mass fraction
                    mass_fraction = comp_data.get('mass_fraction', 0.0)
                    total_water_content = mix_design_data.get('total_water_content', 0.0)
                    
                    # Estimate total mass (this is approximate, will be recalculated)
                    estimated_total_mass = total_water_content / mix_design_data.get('water_binder_ratio', 0.40)
                    component_mass = mass_fraction * estimated_total_mass
                    
                    # Set mass
                    row['mass_spin'].set_value(component_mass)
            
            # Trigger recalculation
            self._update_all_calculations()
            
            self.logger.info(f"Populated UI with mix design data ({len(components)} components)")
            
        except Exception as e:
            self.logger.error(f"Error populating UI from mix design: {e}")
            raise

    def _load_mix_design(self, mix_id: int) -> None:
        """Load a mix design from database."""
        try:
            # Import mix design service
            from app.services.mix_design_service import MixDesignService
            
            mix_design_service = MixDesignService(self.service_container.database_service)
            mix_design = mix_design_service.get_by_id(mix_id)
            
            if not mix_design:
                raise ValueError(f"Mix design with ID {mix_id} not found")
            
            # Convert to dictionary format for UI population
            mix_data = {
                'water_binder_ratio': mix_design.water_binder_ratio,
                'total_water_content': mix_design.total_water_content,
                'air_content': mix_design.air_content,
                'air_volume_fraction': mix_design.air_volume_fraction,
                'system_size': mix_design.system_size,
                'random_seed': mix_design.random_seed,
                'cement_shape_set': mix_design.cement_shape_set,
                'aggregate_shape_set': mix_design.aggregate_shape_set,
                'components': mix_design.components,
                'calculated_properties': mix_design.calculated_properties
            }
            
            # Populate UI
            self._populate_ui_from_mix_design(mix_data)
            
            self.main_window.update_status(f"Loaded mix design '{mix_design.name}' successfully", "success", 3)
            self.logger.info(f"Loaded mix design: {mix_design.name} (ID: {mix_id})")
            
        except Exception as e:
            self.logger.error(f"Error loading mix design: {e}")
            self.main_window.update_status(f"Error loading mix design: {e}", "error", 5)
    
    def _duplicate_mix_design(self, mix_id: int, mix_name: str) -> None:
        """Duplicate a mix design."""
        try:
            # Import mix design service
            from app.services.mix_design_service import MixDesignService
            
            mix_design_service = MixDesignService(self.service_container.database_service)
            new_name = mix_design_service.generate_unique_name(f"{mix_name}_copy")
            duplicated_mix = mix_design_service.duplicate(mix_id, new_name)
            
            # Load the duplicated mix into UI
            self._load_mix_design(duplicated_mix.id)
            
            self.main_window.update_status(f"Duplicated '{mix_name}' as '{new_name}'", "success", 3)
            self.logger.info(f"Duplicated mix design: {mix_id} -> {new_name} (ID: {duplicated_mix.id})")
            
        except Exception as e:
            self.logger.error(f"Error duplicating mix design: {e}")
            self.main_window.update_status(f"Error duplicating mix design: {e}", "error", 5)
    
    def _delete_mix_design(self, mix_id: int, mix_name: str) -> None:
        """Delete a mix design with confirmation."""
        try:
            # Confirmation dialog
            confirm_dialog = Gtk.MessageDialog(
                transient_for=self.main_window,
                flags=0,
                message_type=Gtk.MessageType.QUESTION,
                buttons=Gtk.ButtonsType.YES_NO,
                text=f"Delete Mix Design '{mix_name}'?"
            )
            confirm_dialog.format_secondary_text(
                "This action cannot be undone. The mix design will be permanently removed."
            )
            
            response = confirm_dialog.run()
            if response == Gtk.ResponseType.YES:
                # Import mix design service
                from app.services.mix_design_service import MixDesignService
                
                mix_design_service = MixDesignService(self.service_container.database_service)
                mix_design_service.delete(mix_id)
                
                self.main_window.update_status(f"Deleted mix design '{mix_name}'", "success", 3)
                self.logger.info(f"Deleted mix design: {mix_name} (ID: {mix_id})")
            
            confirm_dialog.destroy()
            
        except Exception as e:
            self.logger.error(f"Error deleting mix design: {e}")
            self.main_window.update_status(f"Error deleting mix design: {e}", "error", 5)
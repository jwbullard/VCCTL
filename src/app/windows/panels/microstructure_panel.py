#!/usr/bin/env python3
"""
Microstructure Parameters Panel for VCCTL

Provides interface for setting 3D microstructure generation parameters including
system dimensions, resolution, particle shapes, and flocculation controls.
"""

import gi
import logging
import random
from typing import TYPE_CHECKING, Optional, Dict, Any, List, Tuple
from decimal import Decimal

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, Pango, Gdk, cairo

if TYPE_CHECKING:
    from app.windows.main_window import VCCTLMainWindow

from app.services.service_container import get_service_container
from app.services.microstructure_service import MicrostructureParams, PhaseType
from app.visualization import create_visualization_manager, Microstructure3DViewer


class MicrostructurePanel(Gtk.Box):
    """Microstructure parameters panel with 3D generation controls."""
    
    def __init__(self, main_window: 'VCCTLMainWindow'):
        """Initialize the microstructure panel."""
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        self.main_window = main_window
        self.logger = logging.getLogger('VCCTL.MicrostructurePanel')
        self.service_container = get_service_container()
        self.microstructure_service = self.service_container.microstructure_service
        
        # Initialize visualization manager
        self.plot_manager, self.plot_exporter = create_visualization_manager(main_window)
        self.microstructure_3d_viewer = None
        
        # Panel state
        self.current_params = None
        self.validation_result = None
        self.computation_estimate = None
        
        # Setup UI
        self._setup_ui()
        self._connect_signals()
        
        # Load default parameters
        self._load_default_parameters()
        
        self.logger.info("Microstructure panel initialized")
    
    def _setup_ui(self) -> None:
        """Setup the microstructure panel UI."""
        # Create header
        self._create_header()
        
        # Create main content area
        self._create_content_area()
        
        # Create status area
        self._create_status_area()
    
    def _create_header(self) -> None:
        """Create the panel header."""
        header_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        header_box.set_margin_top(10)
        header_box.set_margin_bottom(10)
        header_box.set_margin_left(15)
        header_box.set_margin_right(15)
        
        # Title and controls
        title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        title_label = Gtk.Label()
        title_label.set_markup('<span size="large" weight="bold">Microstructure Parameters</span>')
        title_label.set_halign(Gtk.Align.START)
        title_box.pack_start(title_label, False, False, 0)
        
        # Parameter preset controls
        preset_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        preset_label = Gtk.Label("Preset:")
        self.preset_combo = Gtk.ComboBoxText()
        self.preset_combo.append("custom", "Custom")
        self.preset_combo.append("coarse", "Coarse (Fast)")
        self.preset_combo.append("medium", "Medium (Balanced)")
        self.preset_combo.append("fine", "Fine (Detailed)")
        self.preset_combo.append("ultra_fine", "Ultra-Fine (Research)")
        self.preset_combo.set_active(0)
        preset_box.pack_start(preset_label, False, False, 0)
        preset_box.pack_start(self.preset_combo, False, False, 0)
        
        # Action buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        
        self.validate_button = Gtk.Button(label="Validate")
        self.validate_button.set_tooltip_text("Validate parameters and estimate computation")
        button_box.pack_start(self.validate_button, False, False, 0)
        
        self.reset_button = Gtk.Button(label="Reset")
        self.reset_button.set_tooltip_text("Reset to default parameters")
        button_box.pack_start(self.reset_button, False, False, 0)
        
        title_box.pack_end(button_box, False, False, 0)
        title_box.pack_end(preset_box, False, False, 0)
        
        header_box.pack_start(title_box, False, False, 0)
        
        # Description
        desc_label = Gtk.Label()
        desc_label.set_markup('<span size="small">Configure 3D microstructure generation parameters including system size, resolution, and particle characteristics.</span>')
        desc_label.set_halign(Gtk.Align.START)
        desc_label.get_style_context().add_class("dim-label")
        header_box.pack_start(desc_label, False, False, 0)
        
        self.pack_start(header_box, False, False, 0)
        
        # Separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.pack_start(separator, False, False, 0)
    
    def _create_content_area(self) -> None:
        """Create the main content area with parameter controls."""
        # Create scrolled window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_hexpand(True)
        scrolled.set_vexpand(True)
        
        # Main content box
        content_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=15)
        content_box.set_margin_top(15)
        content_box.set_margin_bottom(15)
        content_box.set_margin_left(15)
        content_box.set_margin_right(15)
        
        # Left column: System parameters
        left_column = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        left_column.set_size_request(400, -1)
        
        self._create_system_parameters_section(left_column)
        self._create_composition_parameters_section(left_column)
        
        # Right column: Particle and flocculation parameters
        right_column = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        right_column.set_size_request(400, -1)
        
        self._create_particle_shape_section(right_column)
        self._create_flocculation_section(right_column)
        self._create_advanced_section(right_column)
        self._create_preview_section(right_column)
        
        content_box.pack_start(left_column, False, False, 0)
        content_box.pack_start(right_column, False, False, 0)
        
        scrolled.add(content_box)
        self.pack_start(scrolled, True, True, 0)
    
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
        frame = Gtk.Frame(label="Mix Composition")
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
        air_label = Gtk.Label("Air Content:")
        air_label.set_halign(Gtk.Align.START)
        air_label.set_tooltip_text("Volume fraction of entrained air")
        grid.attach(air_label, 0, 2, 1, 1)
        
        self.air_content_spin = Gtk.SpinButton.new_with_range(0.0, 0.2, 0.001)
        self.air_content_spin.set_digits(3)
        self.air_content_spin.set_value(0.05)
        grid.attach(self.air_content_spin, 1, 2, 1, 1)
        
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
        for shape_id, shape_desc in shape_sets.items():
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
        
        self.random_seed_spin = Gtk.SpinButton.new_with_range(0, 2147483647, 1)
        self.random_seed_spin.set_value(0)
        seed_box.pack_start(self.random_seed_spin, True, True, 0)
        
        self.generate_seed_button = Gtk.Button(label="Generate")
        self.generate_seed_button.set_tooltip_text("Generate new random seed")
        seed_box.pack_start(self.generate_seed_button, False, False, 0)
        
        grid.attach(seed_box, 1, 0, 1, 1)
        
        frame.add(grid)
        parent.pack_start(frame, False, False, 0)
    
    def _create_preview_section(self, parent: Gtk.Box) -> None:
        """Create microstructure preview section."""
        frame = Gtk.Frame(label="Microstructure Preview")
        frame.get_style_context().add_class("card")
        
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_top(15)
        vbox.set_margin_bottom(15)
        vbox.set_margin_left(15)
        vbox.set_margin_right(15)
        
        # 3D Microstructure Viewer
        self.microstructure_3d_viewer = Microstructure3DViewer()
        self.microstructure_3d_viewer.set_size_request(250, 200)
        vbox.pack_start(self.microstructure_3d_viewer, True, True, 0)
        
        # Preview controls
        preview_controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        
        self.preview_button = Gtk.Button(label="Generate Preview")
        self.preview_button.set_tooltip_text("Generate 3D microstructure preview")
        preview_controls.pack_start(self.preview_button, True, True, 0)
        
        self.export_preview_button = Gtk.Button(label="Export")
        self.export_preview_button.set_tooltip_text("Export preview as image")
        self.export_preview_button.set_sensitive(False)
        preview_controls.pack_start(self.export_preview_button, False, False, 0)
        
        vbox.pack_start(preview_controls, False, False, 0)
        
        frame.add(vbox)
        parent.pack_start(frame, True, True, 0)
    
    def _create_status_area(self) -> None:
        """Create the status and validation area."""
        # Separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.pack_start(separator, False, False, 0)
        
        # Status area
        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=15)
        status_box.set_margin_top(10)
        status_box.set_margin_bottom(10)
        status_box.set_margin_left(15)
        status_box.set_margin_right(15)
        
        # Validation status
        validation_frame = Gtk.Frame(label="Validation Status")
        validation_frame.set_size_request(300, -1)
        
        self.validation_text = Gtk.TextView()
        self.validation_text.set_editable(False)
        self.validation_text.set_cursor_visible(False)
        self.validation_text.set_size_request(-1, 100)
        
        validation_scroll = Gtk.ScrolledWindow()
        validation_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        validation_scroll.add(self.validation_text)
        
        validation_frame.add(validation_scroll)
        status_box.pack_start(validation_frame, True, True, 0)
        
        # Computation estimate
        compute_frame = Gtk.Frame(label="Computation Estimate")
        compute_frame.set_size_request(300, -1)
        
        compute_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        compute_box.set_margin_top(10)
        compute_box.set_margin_bottom(10)
        compute_box.set_margin_left(10)
        compute_box.set_margin_right(10)
        
        self.memory_label = Gtk.Label()
        self.memory_label.set_halign(Gtk.Align.START)
        compute_box.pack_start(self.memory_label, False, False, 0)
        
        self.time_label = Gtk.Label()
        self.time_label.set_halign(Gtk.Align.START)
        compute_box.pack_start(self.time_label, False, False, 0)
        
        self.complexity_label = Gtk.Label()
        self.complexity_label.set_halign(Gtk.Align.START)
        compute_box.pack_start(self.complexity_label, False, False, 0)
        
        compute_frame.add(compute_box)
        status_box.pack_start(compute_frame, True, True, 0)
        
        self.pack_start(status_box, False, False, 0)
    
    def _connect_signals(self) -> None:
        """Connect UI signals."""
        # Parameter change signals
        self.system_size_spin.connect('value-changed', self._on_parameter_changed)
        self.resolution_spin.connect('value-changed', self._on_parameter_changed)
        self.wb_ratio_spin.connect('value-changed', self._on_parameter_changed)
        self.agg_volume_spin.connect('value-changed', self._on_parameter_changed)
        self.air_content_spin.connect('value-changed', self._on_parameter_changed)
        self.cement_shape_combo.connect('changed', self._on_parameter_changed)
        self.agg_shape_combo.connect('changed', self._on_parameter_changed)
        self.flocculation_check.connect('toggled', self._on_flocculation_toggled)
        self.flocculation_spin.connect('value-changed', self._on_parameter_changed)
        self.random_seed_spin.connect('value-changed', self._on_parameter_changed)
        
        # Control signals
        self.preset_combo.connect('changed', self._on_preset_changed)
        self.validate_button.connect('clicked', self._on_validate_clicked)
        self.reset_button.connect('clicked', self._on_reset_clicked)
        self.generate_seed_button.connect('clicked', self._on_generate_seed_clicked)
        
        # Preview signals
        self.preview_button.connect('clicked', self._on_preview_clicked)
        self.export_preview_button.connect('clicked', self._on_export_preview_clicked)
    
    def _load_default_parameters(self) -> None:
        """Load default parameters."""
        self._update_calculated_values()
        self._update_status("Ready - configure parameters and click Validate")
    
    def _on_parameter_changed(self, widget) -> None:
        """Handle parameter change."""
        self._update_calculated_values()
        self._clear_validation()
    
    def _on_flocculation_toggled(self, check) -> None:
        """Handle flocculation enable/disable."""
        enabled = check.get_active()
        self.flocculation_spin.set_sensitive(enabled)
        
        if not enabled:
            self.flocculation_spin.set_value(0.0)
        
        self._on_parameter_changed(check)
    
    def _on_preset_changed(self, combo) -> None:
        """Handle preset selection change."""
        preset = combo.get_active_id()
        
        if preset == "coarse":
            self.system_size_spin.set_value(50)
            self.resolution_spin.set_value(2.0)
        elif preset == "medium":
            self.system_size_spin.set_value(100)
            self.resolution_spin.set_value(1.0)
        elif preset == "fine":
            self.system_size_spin.set_value(200)
            self.resolution_spin.set_value(0.5)
        elif preset == "ultra_fine":
            self.system_size_spin.set_value(400)
            self.resolution_spin.set_value(0.25)
        # Custom - don't change values
    
    def _on_validate_clicked(self, button) -> None:
        """Handle validate button click."""
        try:
            # Get current parameters
            params = self._get_current_parameters()
            
            # Validate parameters
            validation_result = self.microstructure_service.validate_microstructure_feasibility(
                params, {}  # Empty phase volumes for now
            )
            
            # Estimate computation
            computation_estimate = self.microstructure_service.estimate_computation_time(params)
            
            # Update displays
            self._update_validation_display(validation_result)
            self._update_computation_display(computation_estimate)
            
            self.validation_result = validation_result
            self.computation_estimate = computation_estimate
            self.current_params = params
            
            self.logger.info("Parameter validation completed")
            
        except Exception as e:
            self.logger.error(f"Validation failed: {e}")
            self._update_status(f"Validation error: {e}")
    
    def _on_reset_clicked(self, button) -> None:
        """Handle reset button click."""
        self.system_size_spin.set_value(100)
        self.resolution_spin.set_value(1.0)
        self.wb_ratio_spin.set_value(0.4)
        self.agg_volume_spin.set_value(0.7)
        self.air_content_spin.set_value(0.05)
        self.cement_shape_combo.set_active(0)
        self.agg_shape_combo.set_active(0)
        self.flocculation_check.set_active(False)
        self.flocculation_spin.set_value(0.0)
        self.random_seed_spin.set_value(0)
        self.preset_combo.set_active(2)  # Medium preset
        
        self._clear_validation()
        self._update_status("Parameters reset to defaults")
    
    def _on_generate_seed_clicked(self, button) -> None:
        """Handle generate seed button click."""
        new_seed = random.randint(1, 2147483647)
        self.random_seed_spin.set_value(new_seed)
        self._update_status(f"Generated new random seed: {new_seed}")
    
    def _get_current_parameters(self) -> MicrostructureParams:
        """Get current parameter values from UI."""
        return MicrostructureParams(
            system_size=int(self.system_size_spin.get_value()),
            resolution=self.resolution_spin.get_value(),
            water_binder_ratio=self.wb_ratio_spin.get_value(),
            aggregate_volume_fraction=self.agg_volume_spin.get_value(),
            air_content=self.air_content_spin.get_value(),
            cement_shape_set=self.cement_shape_combo.get_active_id() or "sphere",
            aggregate_shape_set=self.agg_shape_combo.get_active_id() or "sphere",
            flocculation_enabled=self.flocculation_check.get_active(),
            flocculation_degree=self.flocculation_spin.get_value()
        )
    
    def _update_calculated_values(self) -> None:
        """Update calculated values display."""
        try:
            system_size = self.system_size_spin.get_value()
            resolution = self.resolution_spin.get_value()
            
            # Physical size
            physical_size = system_size * resolution
            self.calc_size_label.set_text(f"{physical_size:.1f}")
            
            # Total voxels
            total_voxels = int(system_size ** 3)
            self.total_voxels_label.set_text(f"{total_voxels:,}")
            
        except Exception as e:
            self.logger.error(f"Failed to update calculated values: {e}")
    
    def _update_validation_display(self, validation_result: Dict[str, Any]) -> None:
        """Update validation display."""
        buffer = self.validation_text.get_buffer()
        buffer.set_text("")
        
        if validation_result['is_feasible']:
            buffer.insert_at_cursor("✓ Parameters are feasible\n\n")
        else:
            buffer.insert_at_cursor("✗ Parameters have issues\n\n")
        
        if validation_result['errors']:
            buffer.insert_at_cursor("ERRORS:\n")
            for error in validation_result['errors']:
                buffer.insert_at_cursor(f"• {error}\n")
            buffer.insert_at_cursor("\n")
        
        if validation_result['warnings']:
            buffer.insert_at_cursor("WARNINGS:\n")
            for warning in validation_result['warnings']:
                buffer.insert_at_cursor(f"• {warning}\n")
            buffer.insert_at_cursor("\n")
        
        if validation_result['recommendations']:
            buffer.insert_at_cursor("RECOMMENDATIONS:\n")
            for rec in validation_result['recommendations']:
                buffer.insert_at_cursor(f"• {rec}\n")
    
    def _update_computation_display(self, computation_estimate: Dict[str, Any]) -> None:
        """Update computation estimate display."""
        total_voxels = computation_estimate.get('total_voxels', 0)
        time_hours = computation_estimate.get('estimated_time_hours', 0)
        
        # Estimate memory usage (rough approximation)
        memory_mb = total_voxels * 4 / (1024 * 1024)  # 4 bytes per voxel
        
        self.memory_label.set_text(f"Memory: ~{memory_mb:.1f} MB")
        
        if time_hours < 1:
            time_minutes = computation_estimate.get('estimated_time_minutes', 0)
            self.time_label.set_text(f"Time: ~{time_minutes:.1f} minutes")
        else:
            self.time_label.set_text(f"Time: ~{time_hours:.1f} hours")
        
        factors = computation_estimate.get('complexity_factors', {})
        complexity_text = "Complexity: "
        if factors.get('flocculation'):
            complexity_text += "Flocculation "
        if factors.get('fine_resolution'):
            complexity_text += "Fine-res "
        if not any(factors.values()):
            complexity_text += "Standard"
        
        self.complexity_label.set_text(complexity_text)
    
    def _clear_validation(self) -> None:
        """Clear validation displays."""
        buffer = self.validation_text.get_buffer()
        buffer.set_text("Click Validate to check parameters")
        
        self.memory_label.set_text("Memory: -")
        self.time_label.set_text("Time: -")
        self.complexity_label.set_text("Complexity: -")
        
        self.validation_result = None
        self.computation_estimate = None
    
    def _update_status(self, message: str) -> None:
        """Update status message."""
        self.logger.debug(f"Status: {message}")
        # Could add status bar here if needed
    
    def get_microstructure_parameters(self) -> Optional[MicrostructureParams]:
        """Get validated microstructure parameters."""
        if self.current_params and self.validation_result and self.validation_result['is_feasible']:
            return self.current_params
        return None
    
    def set_microstructure_parameters(self, params: MicrostructureParams) -> None:
        """Set microstructure parameters in UI."""
        try:
            self.system_size_spin.set_value(params.system_size)
            self.resolution_spin.set_value(params.resolution)
            self.wb_ratio_spin.set_value(params.water_binder_ratio)
            self.agg_volume_spin.set_value(params.aggregate_volume_fraction)
            self.air_content_spin.set_value(params.air_content)
            
            # Set shape sets
            cement_id = params.cement_shape_set
            agg_id = params.aggregate_shape_set
            
            # Find and set active items
            for i in range(self.cement_shape_combo.get_model().iter_n_children(None)):
                if self.cement_shape_combo.get_model().get_value(self.cement_shape_combo.get_model().get_iter_from_string(str(i)), 0) == cement_id:
                    self.cement_shape_combo.set_active(i)
                    break
            
            for i in range(self.agg_shape_combo.get_model().iter_n_children(None)):
                if self.agg_shape_combo.get_model().get_value(self.agg_shape_combo.get_model().get_iter_from_string(str(i)), 0) == agg_id:
                    self.agg_shape_combo.set_active(i)
                    break
            
            self.flocculation_check.set_active(params.flocculation_enabled)
            self.flocculation_spin.set_value(params.flocculation_degree)
            
            self.preset_combo.set_active(0)  # Custom
            self._clear_validation()
            
            self.logger.info("Microstructure parameters loaded")
            
        except Exception as e:
            self.logger.error(f"Failed to set microstructure parameters: {e}")
            self._update_status(f"Error loading parameters: {e}")
    
    def _on_preview_clicked(self, button) -> None:
        """Handle preview generation button click."""
        try:
            # Validate parameters first
            params = self._get_current_parameters()
            
            # Generate sample 3D microstructure data for preview
            voxel_data = self._generate_sample_microstructure(params)
            
            # Create phase mapping
            phase_mapping = {
                0: "Void/Pore",
                1: "C3S",
                2: "C2S", 
                3: "C3A",
                4: "C4AF",
                5: "Gypsum",
                6: "C-S-H",
                7: "CH"
            }
            
            # Load data into 3D viewer
            voxel_size = (params.resolution, params.resolution, params.resolution)
            success = self.microstructure_3d_viewer.load_voxel_data(
                voxel_data, phase_mapping, voxel_size
            )
            
            if success:
                self.export_preview_button.set_sensitive(True)
                self._update_status("3D preview generated successfully")
                self.logger.info("3D microstructure preview generated")
            else:
                self._update_status("Failed to generate 3D preview")
            
        except Exception as e:
            self.logger.error(f"Preview generation failed: {e}")
            self._update_status(f"Preview generation error: {e}")
    
    def _generate_sample_microstructure(self, params: MicrostructureParams) -> 'np.ndarray':
        """Generate sample microstructure data for preview."""
        import numpy as np
        
        # Use smaller dimensions for preview (max 50x50x50)
        preview_size = min(50, max(10, int(params.x_dimension / params.resolution / 4)))
        
        # Create random microstructure with realistic phase distributions
        voxel_data = np.zeros((preview_size, preview_size, preview_size), dtype=int)
        
        # Generate phases based on typical cement paste composition
        total_voxels = preview_size ** 3
        
        # Approximate phase volume fractions for cement paste
        phase_fractions = {
            0: 0.15,  # Pores
            1: 0.20,  # C3S (remaining)
            2: 0.10,  # C2S (remaining)
            3: 0.05,  # C3A (remaining)
            4: 0.03,  # C4AF (remaining)
            5: 0.02,  # Gypsum (remaining)
            6: 0.35,  # C-S-H (hydration product)
            7: 0.10   # CH (hydration product)
        }
        
        # Assign phases randomly but with clustering
        np.random.seed(42)  # For reproducible previews
        
        for phase_id, fraction in phase_fractions.items():
            n_voxels = int(total_voxels * fraction)
            
            if phase_id == 0:  # Pores - create connected pore structure
                # Create some connected pore channels
                for _ in range(n_voxels // 10):
                    start_x = np.random.randint(0, preview_size)
                    start_y = np.random.randint(0, preview_size) 
                    start_z = np.random.randint(0, preview_size)
                    
                    # Create small connected region
                    for _ in range(10):
                        if (0 <= start_x < preview_size and 
                            0 <= start_y < preview_size and 
                            0 <= start_z < preview_size):
                            voxel_data[start_x, start_y, start_z] = phase_id
                            
                            # Move to adjacent voxel
                            start_x += np.random.randint(-1, 2)
                            start_y += np.random.randint(-1, 2)
                            start_z += np.random.randint(-1, 2)
            else:
                # Create clusters for other phases
                remaining = n_voxels
                while remaining > 0:
                    # Find empty voxel
                    attempts = 0
                    while attempts < 100:
                        x = np.random.randint(0, preview_size)
                        y = np.random.randint(0, preview_size)
                        z = np.random.randint(0, preview_size)
                        
                        if voxel_data[x, y, z] == 0:
                            break
                        attempts += 1
                    
                    if attempts >= 100:
                        break
                    
                    # Create cluster
                    cluster_size = min(remaining, np.random.randint(1, 8))
                    for _ in range(cluster_size):
                        if (0 <= x < preview_size and 
                            0 <= y < preview_size and 
                            0 <= z < preview_size and
                            voxel_data[x, y, z] == 0):
                            voxel_data[x, y, z] = phase_id
                            remaining -= 1
                            
                            # Move to adjacent voxel for cluster growth
                            x += np.random.randint(-1, 2)
                            y += np.random.randint(-1, 2) 
                            z += np.random.randint(-1, 2)
        
        return voxel_data
    
    def _on_export_preview_clicked(self, button) -> None:
        """Handle preview export button click."""
        try:
            # Create file chooser dialog
            dialog = Gtk.FileChooserDialog(
                title="Export 3D Microstructure Preview",
                parent=self.main_window,
                action=Gtk.FileChooserAction.SAVE
            )
            dialog.add_buttons(
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_SAVE, Gtk.ResponseType.OK
            )
            
            # Add file filters
            for name, pattern in [("PNG Images", "*.png"), ("PDF Files", "*.pdf"), ("SVG Files", "*.svg")]:
                filter_type = Gtk.FileFilter()
                filter_type.set_name(name)
                filter_type.add_pattern(pattern)
                dialog.add_filter(filter_type)
            
            dialog.set_current_name("microstructure_preview.png")
            
            response = dialog.run()
            if response == Gtk.ResponseType.OK:
                filename = dialog.get_filename()
                if self.microstructure_3d_viewer:
                    format_type = filename.split('.')[-1].lower()
                    success = self.microstructure_3d_viewer.export_3d_view(filename, format_type)
                    if success:
                        self._update_status(f"3D preview exported to {filename}")
                    else:
                        self._update_status("Failed to export 3D preview")
                else:
                    self._update_status("No 3D preview available to export")
            
            dialog.destroy()
            
        except Exception as e:
            self.logger.error(f"Preview export failed: {e}")
            self._update_status(f"Export error: {e}")
    

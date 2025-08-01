#!/usr/bin/env python3
"""
Hydration Interface Panel for VCCTL

Provides comprehensive interface for hydration simulation parameters including
time controls, temperature profiles, aging modes, and progress monitoring.
"""

import gi
import logging
import math
from typing import TYPE_CHECKING, Optional, Dict, Any, List, Tuple
from decimal import Decimal

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, Pango, Gdk, GLib, cairo

if TYPE_CHECKING:
    from app.windows.main_window import VCCTLMainWindow

from app.services.service_container import get_service_container
from app.services.hydration_service import (
    HydrationParameters, TemperatureProfile, TemperaturePoint, 
    AgingMode, SimulationStatus, SimulationProgress
)
from app.visualization import create_visualization_manager, HydrationPlotWidget


class HydrationPanel(Gtk.Box):
    """Hydration simulation panel with comprehensive parameter controls and monitoring."""
    
    def __init__(self, main_window: 'VCCTLMainWindow'):
        """Initialize the hydration panel."""
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        self.main_window = main_window
        self.logger = logging.getLogger('VCCTL.HydrationPanel')
        self.service_container = get_service_container()
        self.hydration_service = self.service_container.hydration_service
        
        # Initialize visualization manager
        self.plot_manager, self.plot_exporter = create_visualization_manager(main_window)
        self.hydration_plot_widget = None
        
        # Panel state
        self.current_params = None
        self.current_temperature_profile = None
        self.simulation_running = False
        self.progress_update_timeout = None
        
        # Temperature profile editing
        self.temp_profile_points = []
        
        # Setup UI
        self._setup_ui()
        self._connect_signals()
        
        # Load default parameters
        self._load_default_parameters()
        
        # Register for simulation progress updates
        self.hydration_service.add_progress_callback(self._on_simulation_progress)
        
        self.logger.info("Hydration panel initialized")
    
    def _setup_ui(self) -> None:
        """Setup the hydration panel UI."""
        # Create header
        self._create_header()
        
        # Create main content area
        self._create_content_area()
        
        # Create simulation control area
        self._create_simulation_controls()
        
        # Create progress monitoring area
        self._create_progress_area()
    
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
        title_label.set_markup('<span size="large" weight="bold">Hydration Simulation</span>')
        title_label.set_halign(Gtk.Align.START)
        title_box.pack_start(title_label, False, False, 0)
        
        # Simulation status indicator
        self.status_label = Gtk.Label("Ready")
        self.status_label.set_halign(Gtk.Align.END)
        self.status_label.get_style_context().add_class("dim-label")
        title_box.pack_end(self.status_label, False, False, 0)
        
        header_box.pack_start(title_box, False, False, 0)
        
        # Description
        desc_label = Gtk.Label()
        desc_label.set_markup('<span size="small">Configure hydration simulation parameters including time controls, temperature profiles, and aging modes.</span>')
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
        
        # Left column: Time and cycles parameters
        left_column = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        left_column.set_size_request(350, -1)
        
        self._create_time_parameters_section(left_column)
        self._create_aging_mode_section(left_column)
        self._create_convergence_section(left_column)
        
        # Right column: Temperature profile and advanced parameters
        right_column = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        right_column.set_size_request(450, -1)
        
        self._create_temperature_profile_section(right_column)
        self._create_output_settings_section(right_column)
        
        content_box.pack_start(left_column, False, False, 0)
        content_box.pack_start(right_column, True, True, 0)
        
        scrolled.add(content_box)
        self.pack_start(scrolled, True, True, 0)
    
    def _create_time_parameters_section(self, parent: Gtk.Box) -> None:
        """Create time and cycles parameters section."""
        frame = Gtk.Frame(label="Time & Cycles")
        frame.get_style_context().add_class("card")
        
        grid = Gtk.Grid()
        grid.set_row_spacing(10)
        grid.set_column_spacing(10)
        grid.set_margin_top(15)
        grid.set_margin_bottom(15)
        grid.set_margin_left(15)
        grid.set_margin_right(15)
        
        # Total cycles
        cycles_label = Gtk.Label("Total Cycles:")
        cycles_label.set_halign(Gtk.Align.START)
        cycles_label.set_tooltip_text("Number of hydration cycles to simulate")
        grid.attach(cycles_label, 0, 0, 1, 1)
        
        self.cycles_spin = Gtk.SpinButton.new_with_range(100, 100000, 100)
        self.cycles_spin.set_value(2000)
        self.cycles_spin.set_tooltip_text("More cycles = longer simulation time but better accuracy")
        grid.attach(self.cycles_spin, 1, 0, 1, 1)
        
        # Time step
        timestep_label = Gtk.Label("Time Step (hours):")
        timestep_label.set_halign(Gtk.Align.START)
        timestep_label.set_tooltip_text("Time increment per cycle")
        grid.attach(timestep_label, 0, 1, 1, 1)
        
        self.timestep_spin = Gtk.SpinButton.new_with_range(0.0001, 1.0, 0.0001)
        self.timestep_spin.set_digits(4)
        self.timestep_spin.set_value(0.001)
        self.timestep_spin.set_tooltip_text("Smaller time steps increase accuracy but computation time")
        grid.attach(self.timestep_spin, 1, 1, 1, 1)
        
        # Maximum simulation time
        max_time_label = Gtk.Label("Max Time (hours):")
        max_time_label.set_halign(Gtk.Align.START)
        max_time_label.set_tooltip_text("Maximum simulation time limit")
        grid.attach(max_time_label, 0, 2, 1, 1)
        
        self.max_time_spin = Gtk.SpinButton.new_with_range(1.0, 8760.0, 1.0)
        self.max_time_spin.set_value(168.0)  # 7 days
        self.max_time_spin.set_tooltip_text("Simulation stops when this time is reached")
        grid.attach(self.max_time_spin, 1, 2, 1, 1)
        
        # Calculated total time
        calc_time_label = Gtk.Label("Calculated Time:")
        calc_time_label.set_halign(Gtk.Align.START)
        grid.attach(calc_time_label, 0, 3, 1, 1)
        
        self.calc_time_label = Gtk.Label("2.0 hours")
        self.calc_time_label.set_halign(Gtk.Align.START)
        self.calc_time_label.get_style_context().add_class("monospace")
        grid.attach(self.calc_time_label, 1, 3, 1, 1)
        
        frame.add(grid)
        parent.pack_start(frame, False, False, 0)
    
    def _create_aging_mode_section(self, parent: Gtk.Box) -> None:
        """Create aging mode selection section."""
        frame = Gtk.Frame(label="Aging Mode")
        frame.get_style_context().add_class("card")
        
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_top(15)
        vbox.set_margin_bottom(15)
        vbox.set_margin_left(15)
        vbox.set_margin_right(15)
        
        # Aging mode radio buttons
        self.aging_time_radio = Gtk.RadioButton.new_with_label(None, "Time-based")
        self.aging_time_radio.set_tooltip_text("Age based on simulation time")
        vbox.pack_start(self.aging_time_radio, False, False, 0)
        
        self.aging_calorimetry_radio = Gtk.RadioButton.new_with_label_from_widget(
            self.aging_time_radio, "Calorimetry-based")
        self.aging_calorimetry_radio.set_tooltip_text("Age based on heat release")
        vbox.pack_start(self.aging_calorimetry_radio, False, False, 0)
        
        self.aging_shrinkage_radio = Gtk.RadioButton.new_with_label_from_widget(
            self.aging_time_radio, "Chemical Shrinkage-based")
        self.aging_shrinkage_radio.set_tooltip_text("Age based on chemical shrinkage measurements")
        vbox.pack_start(self.aging_shrinkage_radio, False, False, 0)
        
        # Aging parameters
        aging_params_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        aging_param_label = Gtk.Label("Target Value:")
        aging_param_label.set_halign(Gtk.Align.START)
        aging_params_box.pack_start(aging_param_label, False, False, 0)
        
        self.aging_target_spin = Gtk.SpinButton.new_with_range(0.1, 1000.0, 0.1)
        self.aging_target_spin.set_digits(2)
        self.aging_target_spin.set_value(28.0)  # 28 days default
        self.aging_target_spin.set_tooltip_text("Target value for aging (days, J/g, or shrinkage %)")
        aging_params_box.pack_start(self.aging_target_spin, False, False, 0)
        
        vbox.pack_start(aging_params_box, False, False, 0)
        
        frame.add(vbox)
        parent.pack_start(frame, False, False, 0)
    
    def _create_convergence_section(self, parent: Gtk.Box) -> None:
        """Create convergence criteria section."""
        frame = Gtk.Frame(label="Convergence Criteria")
        frame.get_style_context().add_class("card")
        
        grid = Gtk.Grid()
        grid.set_row_spacing(10)
        grid.set_column_spacing(10)
        grid.set_margin_top(15)
        grid.set_margin_bottom(15)
        grid.set_margin_left(15)
        grid.set_margin_right(15)
        
        # Tolerance
        tolerance_label = Gtk.Label("Tolerance:")
        tolerance_label.set_halign(Gtk.Align.START)
        tolerance_label.set_tooltip_text("Convergence tolerance for each cycle")
        grid.attach(tolerance_label, 0, 0, 1, 1)
        
        self.tolerance_spin = Gtk.SpinButton.new_with_range(1e-9, 1e-3, 1e-9)
        self.tolerance_spin.set_digits(9)
        self.tolerance_spin.set_value(1e-6)
        grid.attach(self.tolerance_spin, 1, 0, 1, 1)
        
        # Max iterations per cycle
        max_iter_label = Gtk.Label("Max Iterations/Cycle:")
        max_iter_label.set_halign(Gtk.Align.START)
        max_iter_label.set_tooltip_text("Maximum iterations per hydration cycle")
        grid.attach(max_iter_label, 0, 1, 1, 1)
        
        self.max_iter_spin = Gtk.SpinButton.new_with_range(10, 1000, 10)
        self.max_iter_spin.set_value(100)
        grid.attach(self.max_iter_spin, 1, 1, 1, 1)
        
        frame.add(grid)
        parent.pack_start(frame, False, False, 0)
    
    def _create_temperature_profile_section(self, parent: Gtk.Box) -> None:
        """Create temperature profile section."""
        frame = Gtk.Frame(label="Temperature Profile")
        frame.get_style_context().add_class("card")
        
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_top(15)
        vbox.set_margin_bottom(15)
        vbox.set_margin_left(15)
        vbox.set_margin_right(15)
        
        # Profile selection
        profile_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        profile_label = Gtk.Label("Profile:")
        profile_box.pack_start(profile_label, False, False, 0)
        
        self.profile_combo = Gtk.ComboBoxText()
        self.profile_combo.append("custom", "Custom")
        
        # Add predefined profiles
        profiles = self.hydration_service.get_predefined_temperature_profiles()
        for name, profile in profiles.items():
            self.profile_combo.append(name.lower().replace(" ", "_"), name)
        
        self.profile_combo.set_active(0)
        profile_box.pack_start(self.profile_combo, True, True, 0)
        
        self.edit_profile_button = Gtk.Button(label="Edit")
        self.edit_profile_button.set_tooltip_text("Edit temperature profile")
        profile_box.pack_start(self.edit_profile_button, False, False, 0)
        
        vbox.pack_start(profile_box, False, False, 0)
        
        # TEMPORARILY DISABLE HYDRATION PLOT TO ELIMINATE INFINITE SURFACE SIZE WARNINGS
        # Temperature profile plot
        # self.hydration_plot_widget = HydrationPlotWidget(self.plot_manager)
        # # Ensure minimum valid size for plot widget  
        # self.hydration_plot_widget.set_size_request(max(400, 400), max(250, 200))
        # vbox.pack_start(self.hydration_plot_widget, True, True, 0)
        
        # Create placeholder for hydration plot instead of actual widget
        plot_placeholder = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        plot_placeholder.set_size_request(400, 200)
        
        # Add informational label
        info_label = Gtk.Label()
        info_label.set_markup('<span size="large">Hydration Plot</span>')
        info_label.set_halign(Gtk.Align.CENTER)
        plot_placeholder.pack_start(info_label, True, True, 0)
        
        enable_button = Gtk.Button(label="Enable Plot Widget")
        enable_button.set_tooltip_text("Click to enable the hydration plot widget")
        plot_placeholder.pack_start(enable_button, False, False, 0)
        
        vbox.pack_start(plot_placeholder, True, True, 0)
        
        # Store reference for potential later activation
        self.hydration_plot_widget = None
        self.plot_placeholder = plot_placeholder
        
        # Profile summary
        self.profile_summary_label = Gtk.Label()
        self.profile_summary_label.set_halign(Gtk.Align.START)
        self.profile_summary_label.get_style_context().add_class("dim-label")
        vbox.pack_start(self.profile_summary_label, False, False, 0)
        
        frame.add(vbox)
        parent.pack_start(frame, True, True, 0)
    
    def _create_output_settings_section(self, parent: Gtk.Box) -> None:
        """Create output settings section."""
        frame = Gtk.Frame(label="Output Settings")
        frame.get_style_context().add_class("card")
        
        grid = Gtk.Grid()
        grid.set_row_spacing(10)
        grid.set_column_spacing(10)
        grid.set_margin_top(15)
        grid.set_margin_bottom(15)
        grid.set_margin_left(15)
        grid.set_margin_right(15)
        
        # Save interval
        save_interval_label = Gtk.Label("Save Interval (cycles):")
        save_interval_label.set_halign(Gtk.Align.START)
        save_interval_label.set_tooltip_text("Save results every N cycles")
        grid.attach(save_interval_label, 0, 0, 1, 1)
        
        self.save_interval_spin = Gtk.SpinButton.new_with_range(1, 1000, 1)
        self.save_interval_spin.set_value(100)
        grid.attach(self.save_interval_spin, 1, 0, 1, 1)
        
        # Save intermediate results
        self.save_intermediate_check = Gtk.CheckButton(label="Save Intermediate Results")
        self.save_intermediate_check.set_tooltip_text("Save detailed results at each interval")
        grid.attach(self.save_intermediate_check, 0, 1, 2, 1)
        
        frame.add(grid)
        parent.pack_start(frame, False, False, 0)
    
    def _create_simulation_controls(self) -> None:
        """Create simulation control buttons."""
        # Separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.pack_start(separator, False, False, 0)
        
        # Control area
        control_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        control_box.set_margin_top(10)
        control_box.set_margin_bottom(10)
        control_box.set_margin_left(15)
        control_box.set_margin_right(15)
        
        # Validation and estimation
        self.validate_button = Gtk.Button(label="Validate Parameters")
        self.validate_button.set_tooltip_text("Validate parameters and estimate computation time")
        control_box.pack_start(self.validate_button, False, False, 0)
        
        # Computation estimate display
        self.estimate_label = Gtk.Label("Click Validate for time estimate")
        self.estimate_label.set_halign(Gtk.Align.START)
        self.estimate_label.get_style_context().add_class("dim-label")
        control_box.pack_start(self.estimate_label, False, False, 0)
        
        # Spacer
        control_box.pack_start(Gtk.Box(), True, True, 0)
        
        # Simulation control buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        button_box.get_style_context().add_class("linked")
        
        self.start_button = Gtk.Button(label="Start Simulation")
        self.start_button.set_sensitive(False)
        button_box.pack_start(self.start_button, False, False, 0)
        
        self.pause_button = Gtk.Button(label="Pause")
        self.pause_button.set_sensitive(False)
        button_box.pack_start(self.pause_button, False, False, 0)
        
        self.stop_button = Gtk.Button(label="Stop")
        self.stop_button.set_sensitive(False)
        button_box.pack_start(self.stop_button, False, False, 0)
        
        control_box.pack_end(button_box, False, False, 0)
        
        self.pack_start(control_box, False, False, 0)
    
    def _create_progress_area(self) -> None:
        """Create simulation progress monitoring area."""
        # Separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.pack_start(separator, False, False, 0)
        
        # Progress area
        progress_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=15)
        progress_box.set_margin_top(10)
        progress_box.set_margin_bottom(10)
        progress_box.set_margin_left(15)
        progress_box.set_margin_right(15)
        
        # Left side: Progress bars and status
        left_progress = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        left_progress.set_size_request(300, -1)
        
        # Overall progress
        overall_label = Gtk.Label("Overall Progress:")
        overall_label.set_halign(Gtk.Align.START)
        left_progress.pack_start(overall_label, False, False, 0)
        
        self.overall_progress = Gtk.ProgressBar()
        self.overall_progress.set_text("0%")
        self.overall_progress.set_show_text(True)
        left_progress.pack_start(self.overall_progress, False, False, 0)
        
        # Current operation
        self.operation_label = Gtk.Label("Ready to start simulation")
        self.operation_label.set_halign(Gtk.Align.START)
        self.operation_label.get_style_context().add_class("dim-label")
        left_progress.pack_start(self.operation_label, False, False, 0)
        
        # Performance metrics
        metrics_grid = Gtk.Grid()
        metrics_grid.set_row_spacing(5)
        metrics_grid.set_column_spacing(10)
        
        # Elapsed time
        elapsed_label = Gtk.Label("Elapsed:")
        elapsed_label.set_halign(Gtk.Align.START)
        metrics_grid.attach(elapsed_label, 0, 0, 1, 1)
        
        self.elapsed_time_label = Gtk.Label("00:00:00")
        self.elapsed_time_label.set_halign(Gtk.Align.START)
        self.elapsed_time_label.get_style_context().add_class("monospace")
        metrics_grid.attach(self.elapsed_time_label, 1, 0, 1, 1)
        
        # Remaining time
        remaining_label = Gtk.Label("Remaining:")
        remaining_label.set_halign(Gtk.Align.START)
        metrics_grid.attach(remaining_label, 0, 1, 1, 1)
        
        self.remaining_time_label = Gtk.Label("--:--:--")
        self.remaining_time_label.set_halign(Gtk.Align.START)
        self.remaining_time_label.get_style_context().add_class("monospace")
        metrics_grid.attach(self.remaining_time_label, 1, 1, 1, 1)
        
        # Cycles per second
        rate_label = Gtk.Label("Rate:")
        rate_label.set_halign(Gtk.Align.START)
        metrics_grid.attach(rate_label, 0, 2, 1, 1)
        
        self.rate_label = Gtk.Label("-- cycles/s")
        self.rate_label.set_halign(Gtk.Align.START)
        self.rate_label.get_style_context().add_class("monospace")
        metrics_grid.attach(self.rate_label, 1, 2, 1, 1)
        
        left_progress.pack_start(metrics_grid, False, False, 0)
        
        # Right side: Hydration metrics
        right_progress = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        right_progress.set_size_request(300, -1)
        
        metrics_frame = Gtk.Frame(label="Hydration Metrics")
        metrics_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        metrics_vbox.set_margin_top(10)
        metrics_vbox.set_margin_bottom(10)
        metrics_vbox.set_margin_left(10)
        metrics_vbox.set_margin_right(10)
        
        # Degree of hydration
        doh_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        doh_label = Gtk.Label("Degree of Hydration:")
        doh_box.pack_start(doh_label, False, False, 0)
        
        self.doh_value_label = Gtk.Label("0.00")
        self.doh_value_label.set_halign(Gtk.Align.END)
        self.doh_value_label.get_style_context().add_class("monospace")
        doh_box.pack_end(self.doh_value_label, False, False, 0)
        
        metrics_vbox.pack_start(doh_box, False, False, 0)
        
        # Heat released
        heat_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        heat_label = Gtk.Label("Heat Released (J/g):")
        heat_box.pack_start(heat_label, False, False, 0)
        
        self.heat_value_label = Gtk.Label("0.0")
        self.heat_value_label.set_halign(Gtk.Align.END)
        self.heat_value_label.get_style_context().add_class("monospace")
        heat_box.pack_end(self.heat_value_label, False, False, 0)
        
        metrics_vbox.pack_start(heat_box, False, False, 0)
        
        # Chemical shrinkage
        shrinkage_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        shrinkage_label = Gtk.Label("Chemical Shrinkage:")
        shrinkage_box.pack_start(shrinkage_label, False, False, 0)
        
        self.shrinkage_value_label = Gtk.Label("0.000")
        self.shrinkage_value_label.set_halign(Gtk.Align.END)
        self.shrinkage_value_label.get_style_context().add_class("monospace")
        shrinkage_box.pack_end(self.shrinkage_value_label, False, False, 0)
        
        metrics_vbox.pack_start(shrinkage_box, False, False, 0)
        
        metrics_frame.add(metrics_vbox)
        right_progress.pack_start(metrics_frame, False, False, 0)
        
        progress_box.pack_start(left_progress, False, False, 0)
        progress_box.pack_start(right_progress, False, False, 0)
        
        self.pack_start(progress_box, False, False, 0)
    
    def _connect_signals(self) -> None:
        """Connect UI signals."""
        # Parameter change signals
        self.cycles_spin.connect('value-changed', self._on_parameter_changed)
        self.timestep_spin.connect('value-changed', self._on_parameter_changed)
        self.max_time_spin.connect('value-changed', self._on_parameter_changed)
        
        # Aging mode signals
        self.aging_time_radio.connect('toggled', self._on_aging_mode_changed)
        self.aging_calorimetry_radio.connect('toggled', self._on_aging_mode_changed)
        self.aging_shrinkage_radio.connect('toggled', self._on_aging_mode_changed)
        self.aging_target_spin.connect('value-changed', self._on_parameter_changed)
        
        # Convergence signals
        self.tolerance_spin.connect('value-changed', self._on_parameter_changed)
        self.max_iter_spin.connect('value-changed', self._on_parameter_changed)
        
        # Temperature profile signals
        self.profile_combo.connect('changed', self._on_profile_changed)
        self.edit_profile_button.connect('clicked', self._on_edit_profile_clicked)
        
        # Output settings signals
        self.save_interval_spin.connect('value-changed', self._on_parameter_changed)
        self.save_intermediate_check.connect('toggled', self._on_parameter_changed)
        
        # Control signals
        self.validate_button.connect('clicked', self._on_validate_clicked)
        self.start_button.connect('clicked', self._on_start_clicked)
        self.pause_button.connect('clicked', self._on_pause_clicked)
        self.stop_button.connect('clicked', self._on_stop_clicked)
    
    def _load_default_parameters(self) -> None:
        """Load default parameters."""
        # Load default temperature profile (constant 25°C)
        profiles = self.hydration_service.get_predefined_temperature_profiles()
        self.current_temperature_profile = profiles.get("Constant 25°C")
        
        self._update_calculated_values()
        self._update_temperature_plot()
        self._update_profile_summary()
        self._update_status("Ready - configure parameters and click Validate")
    
    def _on_parameter_changed(self, widget) -> None:
        """Handle parameter change."""
        self._update_calculated_values()
        self._clear_validation()
    
    def _on_aging_mode_changed(self, radio) -> None:
        """Handle aging mode change."""
        if not radio.get_active():
            return
        
        # Update target spin button tooltip based on mode
        if self.aging_time_radio.get_active():
            self.aging_target_spin.set_tooltip_text("Target age in days")
            self.aging_target_spin.set_value(28.0)
        elif self.aging_calorimetry_radio.get_active():
            self.aging_target_spin.set_tooltip_text("Target heat release in J/g")
            self.aging_target_spin.set_value(300.0)
        elif self.aging_shrinkage_radio.get_active():
            self.aging_target_spin.set_tooltip_text("Target chemical shrinkage (%)")
            self.aging_target_spin.set_value(5.0)
    
    def _on_profile_changed(self, combo) -> None:
        """Handle temperature profile selection change."""
        profile_id = combo.get_active_id()
        
        if profile_id and profile_id != "custom":
            profiles = self.hydration_service.get_predefined_temperature_profiles()
            profile_name = combo.get_active_text()
            
            if profile_name in profiles:
                self.current_temperature_profile = profiles[profile_name]
                self._update_temperature_plot()
                self._update_profile_summary()
    
    def _on_edit_profile_clicked(self, button) -> None:
        """Handle edit temperature profile button click."""
        # TODO: Open temperature profile editor dialog
        self._update_status("Temperature profile editor not yet implemented")
    
    def _on_validate_clicked(self, button) -> None:
        """Handle validate parameters button click."""
        try:
            # Get current parameters
            params = self._get_current_parameters()
            
            # Validate parameters
            validation = self.hydration_service.validate_hydration_parameters(params)
            
            # Estimate computation time
            estimate = self.hydration_service.estimate_simulation_time(params)
            
            # Update displays
            self._update_validation_display(validation)
            self._update_estimate_display(estimate)
            
            # Enable start button if valid
            self.start_button.set_sensitive(validation['is_valid'])
            
            if validation['is_valid']:
                self.current_params = params
                self._update_status("Parameters validated - ready to start simulation")
            else:
                self._update_status("Parameter validation failed - check errors")
            
            self.logger.info("Parameter validation completed")
            
        except Exception as e:
            self.logger.error(f"Validation failed: {e}")
            self._update_status(f"Validation error: {e}")
    
    def _on_start_clicked(self, button) -> None:
        """Handle start simulation button click."""
        try:
            if not self.current_params:
                self._update_status("Please validate parameters first")
                return
            
            # Get microstructure data (placeholder)
            microstructure_data = {}  # Would come from microstructure panel
            
            # Start simulation
            if self.hydration_service.start_simulation(self.current_params, microstructure_data):
                self.simulation_running = True
                self._update_simulation_controls(True)
                self._start_progress_updates()
                self._update_status("Simulation starting...")
                self.logger.info("Hydration simulation started")
            
        except Exception as e:
            self.logger.error(f"Failed to start simulation: {e}")
            self._update_status(f"Start error: {e}")
    
    def _on_pause_clicked(self, button) -> None:
        """Handle pause simulation button click."""
        # TODO: Implement pause functionality
        self._update_status("Pause functionality not yet implemented")
    
    def _on_stop_clicked(self, button) -> None:
        """Handle stop simulation button click."""
        try:
            if self.hydration_service.stop_simulation():
                self.simulation_running = False
                self._update_simulation_controls(False)
                self._stop_progress_updates()
                self._update_status("Simulation stopped")
                self.logger.info("Hydration simulation stopped")
            
        except Exception as e:
            self.logger.error(f"Failed to stop simulation: {e}")
            self._update_status(f"Stop error: {e}")
    
    def _get_current_parameters(self) -> HydrationParameters:
        """Get current parameter values from UI."""
        # Get aging mode
        if self.aging_time_radio.get_active():
            aging_mode = AgingMode.TIME
        elif self.aging_calorimetry_radio.get_active():
            aging_mode = AgingMode.CALORIMETRY
        else:
            aging_mode = AgingMode.CHEMICAL_SHRINKAGE
        
        return HydrationParameters(
            total_cycles=int(self.cycles_spin.get_value()),
            time_step_hours=self.timestep_spin.get_value(),
            max_simulation_time_hours=self.max_time_spin.get_value(),
            temperature_profile=self.current_temperature_profile or TemperatureProfile(
                "Default", "Default", [TemperaturePoint(0.0, 25.0)]
            ),
            aging_mode=aging_mode,
            convergence_tolerance=self.tolerance_spin.get_value(),
            max_iterations_per_cycle=int(self.max_iter_spin.get_value()),
            save_interval_cycles=int(self.save_interval_spin.get_value()),
            save_intermediate_results=self.save_intermediate_check.get_active()
        )
    
    def _update_calculated_values(self) -> None:
        """Update calculated values display."""
        try:
            cycles = self.cycles_spin.get_value()
            time_step = self.timestep_spin.get_value()
            
            total_time = cycles * time_step
            
            if total_time < 1:
                time_text = f"{total_time * 60:.1f} minutes"
            elif total_time < 24:
                time_text = f"{total_time:.1f} hours"
            else:
                days = total_time / 24
                time_text = f"{days:.1f} days"
            
            self.calc_time_label.set_text(time_text)
            
        except Exception as e:
            self.logger.error(f"Failed to update calculated values: {e}")
    
    def _update_temperature_plot(self) -> None:
        """Update temperature profile plot."""
        if not self.hydration_plot_widget or not self.temp_profile_points:
            return
        
        try:
            # Convert temperature profile points to plot data
            import numpy as np
            
            times = np.array([point.time_hours for point in self.temp_profile_points])
            temperatures = np.array([point.temperature_celsius for point in self.temp_profile_points])
            
            # Create plot data dictionary
            plot_data = {
                'time': times / 24.0,  # Convert hours to days for consistency
                'temperature': temperatures,
                'type': 'temperature_profile'
            }
            
            # Update the plot
            self.hydration_plot_widget.set_data(plot_data)
            
        except Exception as e:
            self.logger.error(f"Failed to update temperature plot: {e}")
    
    def _update_profile_summary(self) -> None:
        """Update temperature profile summary."""
        if not self.current_temperature_profile:
            self.profile_summary_label.set_text("No profile selected")
            return
        
        points = self.current_temperature_profile.points
        if not points:
            self.profile_summary_label.set_text("Empty profile")
            return
        
        min_temp = min(p.temperature_celsius for p in points)
        max_temp = max(p.temperature_celsius for p in points)
        
        if len(points) == 1:
            summary = f"Constant {points[0].temperature_celsius:.1f}°C"
        else:
            duration = max(p.time_hours for p in points)
            summary = f"{min_temp:.1f}°C to {max_temp:.1f}°C over {duration:.1f} hours"
        
        self.profile_summary_label.set_text(summary)
    
    def _update_validation_display(self, validation: Dict[str, Any]) -> None:
        """Update validation status display."""
        # Could show validation results in a popup or status area
        pass
    
    def _update_estimate_display(self, estimate: Dict[str, Any]) -> None:
        """Update computation estimate display."""
        hours = estimate.get('estimated_hours', 0)
        
        if hours < 1:
            minutes = estimate.get('estimated_minutes', 0)
            time_text = f"~{minutes:.1f} minutes"
        else:
            time_text = f"~{hours:.1f} hours"
        
        self.estimate_label.set_text(f"Estimated computation time: {time_text}")
    
    def _clear_validation(self) -> None:
        """Clear validation displays."""
        self.estimate_label.set_text("Click Validate for time estimate")
        self.start_button.set_sensitive(False)
        self.current_params = None
    
    def _update_simulation_controls(self, running: bool) -> None:
        """Update simulation control button states."""
        self.start_button.set_sensitive(not running)
        self.pause_button.set_sensitive(running)
        self.stop_button.set_sensitive(running)
        self.validate_button.set_sensitive(not running)
    
    def _start_progress_updates(self) -> None:
        """Start periodic progress updates."""
        if self.progress_update_timeout:
            GLib.source_remove(self.progress_update_timeout)
        
        self.progress_update_timeout = GLib.timeout_add(
            100,  # Update every 100ms
            self._update_progress_display
        )
    
    def _stop_progress_updates(self) -> None:
        """Stop periodic progress updates."""
        if self.progress_update_timeout:
            GLib.source_remove(self.progress_update_timeout)
            self.progress_update_timeout = None
    
    def _update_progress_display(self) -> bool:
        """Update progress display (called periodically)."""
        progress = self.hydration_service.get_simulation_progress()
        
        if not progress:
            return True  # Continue timeout
        
        # Update progress bar
        self.overall_progress.set_fraction(progress.progress_fraction)
        self.overall_progress.set_text(f"{progress.progress_percentage:.1f}%")
        
        # Update operation label
        self.operation_label.set_text(progress.current_operation)
        
        # Update time displays
        elapsed_seconds = progress.elapsed_real_time_seconds
        elapsed_h = int(elapsed_seconds // 3600)
        elapsed_m = int((elapsed_seconds % 3600) // 60)
        elapsed_s = int(elapsed_seconds % 60)
        self.elapsed_time_label.set_text(f"{elapsed_h:02d}:{elapsed_m:02d}:{elapsed_s:02d}")
        
        remaining_seconds = progress.estimated_remaining_seconds
        if remaining_seconds > 0:
            remaining_h = int(remaining_seconds // 3600)
            remaining_m = int((remaining_seconds % 3600) // 60)
            remaining_s = int(remaining_seconds % 60)
            self.remaining_time_label.set_text(f"{remaining_h:02d}:{remaining_m:02d}:{remaining_s:02d}")
        else:
            self.remaining_time_label.set_text("--:--:--")
        
        # Update rate
        if progress.cycles_per_second > 0:
            self.rate_label.set_text(f"{progress.cycles_per_second:.2f} cycles/s")
        else:
            self.rate_label.set_text("-- cycles/s")
        
        # Update hydration metrics
        self.doh_value_label.set_text(f"{progress.degree_of_hydration:.3f}")
        self.heat_value_label.set_text(f"{progress.heat_released_j_per_g:.1f}")
        self.shrinkage_value_label.set_text(f"{progress.chemical_shrinkage:.3f}")
        
        # Check if simulation is finished
        if progress.status in [SimulationStatus.COMPLETED, SimulationStatus.FAILED, SimulationStatus.CANCELLED]:
            self.simulation_running = False
            self._update_simulation_controls(False)
            self._stop_progress_updates()
            
            if progress.status == SimulationStatus.COMPLETED:
                self._update_status("Simulation completed successfully")
            elif progress.status == SimulationStatus.FAILED:
                self._update_status(f"Simulation failed: {progress.last_error}")
            else:
                self._update_status("Simulation cancelled")
            
            return False  # Stop timeout
        
        return True  # Continue timeout
    
    def _on_simulation_progress(self, progress: SimulationProgress) -> None:
        """Handle simulation progress updates (called from hydration service)."""
        # Progress updates are handled by the periodic timeout
        pass
    
    def _on_draw_temperature_plot(self, widget, cr) -> bool:
        """Draw temperature profile plot. (DEPRECATED: Now using matplotlib plot widget)"""
        # This method is deprecated - now using HydrationPlotWidget
        return True
        try:
            if not self.current_temperature_profile:
                return False
            
            # Get drawing area size
            allocation = widget.get_allocation()
            width = allocation.width
            height = allocation.height
            
            # Margins
            margin = 40
            plot_width = width - 2 * margin
            plot_height = height - 2 * margin
            
            # Clear background
            cr.set_source_rgb(1.0, 1.0, 1.0)
            cr.rectangle(0, 0, width, height)
            cr.fill()
            
            # Draw border
            cr.set_source_rgb(0.7, 0.7, 0.7)
            cr.set_line_width(1.0)
            cr.rectangle(margin, margin, plot_width, plot_height)
            cr.stroke()
            
            points = self.current_temperature_profile.points
            if len(points) < 2:
                # Show single point or no data message
                cr.set_source_rgb(0.5, 0.5, 0.5)
                cr.set_font_size(12)
                if points:
                    text = f"Constant {points[0].temperature_celsius:.1f}°C"
                else:
                    text = "No temperature data"
                
                text_extents = cr.text_extents(text)
                x = (width - text_extents.width) / 2
                y = (height + text_extents.height) / 2
                cr.move_to(x, y)
                cr.show_text(text)
                return True
            
            # Find data ranges
            max_time = max(p.time_hours for p in points)
            min_temp = min(p.temperature_celsius for p in points) - 2
            max_temp = max(p.temperature_celsius for p in points) + 2
            
            if max_time <= 0 or max_temp <= min_temp:
                return True
            
            # Draw grid
            cr.set_source_rgba(0.9, 0.9, 0.9, 1.0)
            cr.set_line_width(0.5)
            
            # Vertical grid lines (time)
            for i in range(1, 6):
                x = margin + (i / 5.0) * plot_width
                cr.move_to(x, margin)
                cr.line_to(x, margin + plot_height)
                cr.stroke()
            
            # Horizontal grid lines (temperature)
            for i in range(1, 5):
                y = margin + (i / 4.0) * plot_height
                cr.move_to(margin, y)
                cr.line_to(margin + plot_width, y)
                cr.stroke()
            
            # Draw temperature curve
            cr.set_source_rgb(0.2, 0.4, 0.8)
            cr.set_line_width(2.0)
            
            # Convert first point to screen coordinates
            first_point = points[0]
            x = margin + (first_point.time_hours / max_time) * plot_width
            y = margin + plot_height - ((first_point.temperature_celsius - min_temp) / (max_temp - min_temp)) * plot_height
            cr.move_to(x, y)
            
            # Draw line to each subsequent point
            for point in points[1:]:
                x = margin + (point.time_hours / max_time) * plot_width
                y = margin + plot_height - ((point.temperature_celsius - min_temp) / (max_temp - min_temp)) * plot_height
                cr.line_to(x, y)
            
            cr.stroke()
            
            # Draw data points
            cr.set_source_rgb(0.8, 0.2, 0.2)
            for point in points:
                x = margin + (point.time_hours / max_time) * plot_width
                y = margin + plot_height - ((point.temperature_celsius - min_temp) / (max_temp - min_temp)) * plot_height
                cr.arc(x, y, 3.0, 0, 2 * math.pi)
                cr.fill()
            
            # Draw axes labels
            cr.set_source_rgb(0.3, 0.3, 0.3)
            cr.set_font_size(10)
            
            # X-axis (time)
            for i in range(6):
                time_val = (i / 5.0) * max_time
                x = margin + (i / 5.0) * plot_width
                text = f"{time_val:.1f}h"
                text_extents = cr.text_extents(text)
                cr.move_to(x - text_extents.width / 2, height - 10)
                cr.show_text(text)
            
            # Y-axis (temperature)
            for i in range(5):
                temp_val = min_temp + (i / 4.0) * (max_temp - min_temp)
                y = margin + plot_height - (i / 4.0) * plot_height
                text = f"{temp_val:.0f}°C"
                text_extents = cr.text_extents(text)
                cr.move_to(10, y + text_extents.height / 2)
                cr.show_text(text)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to draw temperature plot: {e}")
            return False
    
    def _update_status(self, message: str) -> None:
        """Update status message."""
        self.status_label.set_text(message)
        self.logger.debug(f"Status: {message}")
    
    def get_hydration_parameters(self) -> Optional[HydrationParameters]:
        """Get validated hydration parameters."""
        return self.current_params
    
    def set_hydration_parameters(self, params: HydrationParameters) -> None:
        """Set hydration parameters in UI."""
        try:
            self.cycles_spin.set_value(params.total_cycles)
            self.timestep_spin.set_value(params.time_step_hours)
            self.max_time_spin.set_value(params.max_simulation_time_hours)
            self.tolerance_spin.set_value(params.convergence_tolerance)
            self.max_iter_spin.set_value(params.max_iterations_per_cycle)
            self.save_interval_spin.set_value(params.save_interval_cycles)
            self.save_intermediate_check.set_active(params.save_intermediate_results)
            
            # Set aging mode
            if params.aging_mode == AgingMode.TIME:
                self.aging_time_radio.set_active(True)
            elif params.aging_mode == AgingMode.CALORIMETRY:
                self.aging_calorimetry_radio.set_active(True)
            else:
                self.aging_shrinkage_radio.set_active(True)
            
            # Set temperature profile
            self.current_temperature_profile = params.temperature_profile
            self._update_temperature_plot()
            self._update_profile_summary()
            
            self._clear_validation()
            self.logger.info("Hydration parameters loaded")
            
        except Exception as e:
            self.logger.error(f"Failed to set hydration parameters: {e}")
            self._update_status(f"Error loading parameters: {e}")
    
    def cleanup(self) -> None:
        """Cleanup resources when panel is destroyed."""
        self._stop_progress_updates()
        self.hydration_service.remove_progress_callback(self._on_simulation_progress)
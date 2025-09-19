#!/usr/bin/env python3
"""
Hydration Interface Panel for VCCTL

Provides comprehensive interface for hydration simulation parameters including
time controls, temperature profiles, aging modes, and progress monitoring.
"""

import gi
import logging
import math
import os
import time
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Dict, Any, List, Tuple
from decimal import Decimal

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, Pango, Gdk, GLib, cairo

if TYPE_CHECKING:
    from app.windows.main_window import VCCTLMainWindow

from app.services.service_container import get_service_container
from app.utils.icon_utils import create_button_with_icon
from app.services.hydration_service import (
    HydrationParameters, TemperatureProfile, TemperaturePoint, 
    AgingMode, SimulationStatus, SimulationProgress
)
from app.services.microstructure_hydration_bridge import MicrostructureHydrationBridge
from app.services.hydration_parameter_set_service import HydrationParameterSetService
from app.models.hydration_parameter_set import HydrationParameterSetCreate, HydrationParameterSetUpdate
from app.visualization import create_visualization_manager, HydrationPlotWidget


class TemperatureProfileDialog(Gtk.Dialog):
    """Dialog for editing temperature profiles."""
    
    def __init__(self, parent, profile: TemperatureProfile):
        """Initialize the temperature profile dialog."""
        super().__init__(
            title="Temperature Profile Editor",
            parent=parent,
            flags=Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT
        )
        
        # Store the original profile
        self.original_profile = profile
        self.profile = TemperatureProfile(
            name=profile.name,
            description=profile.description,
            points=[TemperaturePoint(p.time_hours, p.temperature_celsius) for p in profile.points]
        )
        
        # Dialog buttons
        self.add_button("Cancel", Gtk.ResponseType.CANCEL)
        save_button = self.add_button("Save", Gtk.ResponseType.ACCEPT)
        save_button.set_tooltip_text("Save profile to database for future use")
        self.add_button("OK", Gtk.ResponseType.OK)
        
        # Set dialog size
        self.set_size_request(600, 500)
        self.set_resizable(True)
        
        # Setup UI
        self._setup_ui()
        
        # Populate with current data
        self._populate_data()
    
    def _setup_ui(self):
        """Setup the dialog UI."""
        content_area = self.get_content_area()
        content_area.set_spacing(10)
        content_area.set_border_width(10)
        
        # Profile name and description
        header_grid = Gtk.Grid()
        header_grid.set_row_spacing(8)
        header_grid.set_column_spacing(10)
        
        # Name entry
        name_label = Gtk.Label("Profile Name:")
        name_label.set_halign(Gtk.Align.START)
        header_grid.attach(name_label, 0, 0, 1, 1)
        
        self.name_entry = Gtk.Entry()
        self.name_entry.set_hexpand(True)
        header_grid.attach(self.name_entry, 1, 0, 1, 1)
        
        # Description entry
        desc_label = Gtk.Label("Description:")
        desc_label.set_halign(Gtk.Align.START)
        header_grid.attach(desc_label, 0, 1, 1, 1)
        
        self.description_entry = Gtk.Entry()
        self.description_entry.set_hexpand(True)
        header_grid.attach(self.description_entry, 1, 1, 1, 1)
        
        content_area.pack_start(header_grid, False, False, 0)
        
        # Temperature points section
        points_label = Gtk.Label()
        points_label.set_markup("<b>Temperature Points</b>")
        points_label.set_halign(Gtk.Align.START)
        content_area.pack_start(points_label, False, False, 0)
        
        # Points list with scrolling
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)
        
        # Create list store and tree view
        # Columns: Time (hours), Temperature (°C)
        self.points_store = Gtk.ListStore(float, float)
        self.points_view = Gtk.TreeView(model=self.points_store)
        
        # Time column
        time_renderer = Gtk.CellRendererSpin()
        time_renderer.set_property("editable", True)
        time_renderer.set_property("adjustment", Gtk.Adjustment(0, 0, 8760, 0.1, 1, 0))  # 0-365 days
        time_renderer.set_property("digits", 1)
        time_renderer.connect("edited", self._on_time_edited)
        
        time_column = Gtk.TreeViewColumn("Time (hours)", time_renderer, text=0)
        time_column.set_min_width(100)  # Reduced to allow narrower windows
        self.points_view.append_column(time_column)
        
        # Temperature column
        temp_renderer = Gtk.CellRendererSpin()
        temp_renderer.set_property("editable", True)
        temp_renderer.set_property("adjustment", Gtk.Adjustment(25, -20, 100, 0.1, 1, 0))
        temp_renderer.set_property("digits", 1)
        temp_renderer.connect("edited", self._on_temperature_edited)
        
        temp_column = Gtk.TreeViewColumn("Temperature (°C)", temp_renderer, text=1)
        temp_column.set_min_width(120)  # Reduced to allow narrower windows
        self.points_view.append_column(temp_column)
        
        scrolled.add(self.points_view)
        content_area.pack_start(scrolled, True, True, 0)
        
        # Buttons for adding/removing points
        button_box = Gtk.ButtonBox(orientation=Gtk.Orientation.HORIZONTAL)
        button_box.set_layout(Gtk.ButtonBoxStyle.START)
        button_box.set_spacing(5)
        
        add_button = Gtk.Button(label="Add Point")
        add_button.connect("clicked", self._on_add_point)
        button_box.add(add_button)
        
        remove_button = Gtk.Button(label="Remove Point")
        remove_button.connect("clicked", self._on_remove_point)
        button_box.add(remove_button)
        
        content_area.pack_start(button_box, False, False, 0)
        
        self.show_all()
    
    def _populate_data(self):
        """Populate the dialog with current profile data."""
        self.name_entry.set_text(self.profile.name)
        self.description_entry.set_text(self.profile.description)
        
        # Add points to the list
        for point in self.profile.points:
            self.points_store.append([point.time_hours, point.temperature_celsius])
    
    def _on_time_edited(self, renderer, path, new_text):
        """Handle time cell editing."""
        try:
            new_time = float(new_text)
            if new_time >= 0:
                iter = self.points_store.get_iter(path)
                self.points_store.set_value(iter, 0, new_time)
                self._update_profile_from_ui()
        except ValueError:
            pass  # Invalid input, ignore
    
    def _on_temperature_edited(self, renderer, path, new_text):
        """Handle temperature cell editing."""
        try:
            new_temp = float(new_text)
            iter = self.points_store.get_iter(path)
            self.points_store.set_value(iter, 1, new_temp)
            self._update_profile_from_ui()
        except ValueError:
            pass  # Invalid input, ignore
    
    def _on_add_point(self, button):
        """Add a new temperature point."""
        # Find a good default time (after the last point)
        last_time = 0.0
        for row in self.points_store:
            if row[0] > last_time:
                last_time = row[0]
        
        new_time = last_time + 24.0  # Add 24 hours
        self.points_store.append([new_time, 25.0])
        self._update_profile_from_ui()
    
    def _on_remove_point(self, button):
        """Remove selected temperature point."""
        selection = self.points_view.get_selection()
        model, iter = selection.get_selected()
        
        if iter and len(self.points_store) > 1:  # Keep at least one point
            model.remove(iter)
            self._update_profile_from_ui()
    
    def _update_profile_from_ui(self):
        """Update the profile from UI data."""
        # Update basic info
        self.profile.name = self.name_entry.get_text()
        self.profile.description = self.description_entry.get_text()
        
        # Update points
        points = []
        for row in self.points_store:
            points.append(TemperaturePoint(row[0], row[1]))
        
        # Sort by time
        points.sort(key=lambda p: p.time_hours)
        self.profile.points = points
    
    def get_profile(self) -> TemperatureProfile:
        """Get the edited profile."""
        self._update_profile_from_ui()
        return self.profile


class HydrationPanel(Gtk.Box):
    """Hydration simulation panel with comprehensive parameter controls and monitoring."""
    
    def __init__(self, main_window: 'VCCTLMainWindow'):
        """Initialize the hydration panel."""
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        self.main_window = main_window
        self.logger = logging.getLogger('VCCTL.HydrationPanel')
        self.service_container = get_service_container()
        self.hydration_service = self.service_container.hydration_service
        self.bridge_service = MicrostructureHydrationBridge()
        
        # Initialize visualization manager
        self.plot_manager, self.plot_exporter = create_visualization_manager(main_window)
        self.hydration_plot_widget = None
        
        # Panel state
        self.current_params = None
        self.current_temperature_profile = None
        self.current_profile = None
        self.simulation_running = False
        self.progress_update_timeout = None
        self.selected_microstructure = None
        self.current_operation_name = None
        
        # Progress tracking from HydrationExecutorService
        self.latest_progress = None
        self.simulation_start_time = None
        
        # Temperature profile editing
        self.temp_profile_points = []
        
        # Setup UI
        self._setup_ui()
        self._connect_signals()
        
        # Load default parameters
        self._load_default_parameters()
        
        # Initialize time calibration mode display
        self._on_aging_mode_changed(self.aging_time_radio)
        
        # Register for simulation progress updates
        self.hydration_service.add_progress_callback(self._on_simulation_progress)
        
        # Initialize thermal mode UI state now that all elements are created
        self._on_thermal_mode_changed(self.isothermal_radio)
        
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
        desc_label.set_markup('<span size="small">Configure hydration simulation parameters including time controls and temperature profiles.</span>')
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
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        content_box.set_margin_top(15)
        content_box.set_margin_bottom(15)
        content_box.set_margin_left(15)
        content_box.set_margin_right(15)
        
        # Microstructure selection section (full width at top)
        self._create_microstructure_selection_section(content_box)
        
        # Parameter sections in horizontal layout
        params_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=15)
        
        # Left column: Time and cycles parameters
        left_column = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        
        self._create_time_parameters_section(left_column)
        self._create_aging_mode_section(left_column)
        self._create_curing_conditions_section(left_column)
        
        # Right column: Temperature profile and advanced parameters
        right_column = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        
        self._create_output_settings_section(right_column)
        self._create_advanced_settings_section(right_column)
        
        params_box.pack_start(left_column, False, False, 0)
        params_box.pack_start(right_column, True, True, 0)
        
        content_box.pack_start(params_box, True, True, 0)
        
        scrolled.add(content_box)
        self.pack_start(scrolled, True, True, 0)
    
    def _create_microstructure_selection_section(self, parent: Gtk.Box) -> None:
        """Create microstructure selection section."""
        frame = Gtk.Frame(label="Initial Microstructure")
        frame.get_style_context().add_class("card")
        
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_top(15)
        vbox.set_margin_bottom(15)
        vbox.set_margin_left(15)
        vbox.set_margin_right(15)
        
        # Description
        desc_label = Gtk.Label()
        desc_label.set_markup('<span size="small">Select the initial microstructure image created by the Mix Design Tool</span>')
        desc_label.set_halign(Gtk.Align.START)
        desc_label.get_style_context().add_class("dim-label")
        vbox.pack_start(desc_label, False, False, 0)
        
        # Microstructure selection
        selection_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        microstructure_label = Gtk.Label("Microstructure:")
        microstructure_label.set_halign(Gtk.Align.START)
        selection_box.pack_start(microstructure_label, False, False, 0)
        
        self.microstructure_combo = Gtk.ComboBoxText()
        self.microstructure_combo.set_tooltip_text("Select initial microstructure from Mix Design operations")
        selection_box.pack_start(self.microstructure_combo, True, True, 0)
        
        self.refresh_button = create_button_with_icon("Refresh", "refresh", 16)
        self.refresh_button.set_tooltip_text("Refresh list of available microstructures")
        selection_box.pack_start(self.refresh_button, False, False, 0)
        
        vbox.pack_start(selection_box, False, False, 0)
        
        # Microstructure info
        self.microstructure_info_label = Gtk.Label("No microstructure selected")
        self.microstructure_info_label.set_halign(Gtk.Align.START)
        self.microstructure_info_label.get_style_context().add_class("dim-label")
        vbox.pack_start(self.microstructure_info_label, False, False, 0)
        
        frame.add(vbox)
        parent.pack_start(frame, False, False, 0)
        
        # Populate microstructure list
        self._refresh_microstructure_list()
    
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
        
        # Max DOH (moved from Advanced Settings)
        max_doh_label = Gtk.Label("Max DOH:")
        max_doh_label.set_halign(Gtk.Align.START)
        max_doh_label.set_tooltip_text("Maximum degree of hydration (0.0-1.0)")
        grid.attach(max_doh_label, 0, 0, 1, 1)
        
        self.alpha_max_spin = Gtk.SpinButton.new_with_range(0.1, 1.0, 0.01)
        self.alpha_max_spin.set_digits(2)
        self.alpha_max_spin.set_value(1.0)
        self.alpha_max_spin.set_tooltip_text("Maximum degree of hydration (default 1.0)")
        grid.attach(self.alpha_max_spin, 1, 0, 1, 1)
        
        # Maximum simulation time
        max_time_label = Gtk.Label("Max Time (hours):")
        max_time_label.set_halign(Gtk.Align.START)
        max_time_label.set_tooltip_text("Maximum simulation time limit")
        grid.attach(max_time_label, 0, 1, 1, 1)
        
        self.max_time_spin = Gtk.SpinButton.new_with_range(1.0, 8760.0, 1.0)
        self.max_time_spin.set_value(168.0)  # 7 days
        self.max_time_spin.set_tooltip_text("Simulation stops when this time is reached")
        grid.attach(self.max_time_spin, 1, 1, 1, 1)
        
        frame.add(grid)
        parent.pack_start(frame, False, False, 0)
    
    def _create_aging_mode_section(self, parent: Gtk.Box) -> None:
        """Create time calibration mode selection section."""
        frame = Gtk.Frame(label="Time Calibration Mode")
        frame.get_style_context().add_class("card")
        
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_top(15)
        vbox.set_margin_bottom(15)
        vbox.set_margin_left(15)
        vbox.set_margin_right(15)
        
        # Time calibration mode radio buttons with inline parameters
        
        # Knudsen parabolic option with time conversion factor
        self.aging_time_radio = Gtk.RadioButton.new_with_label(None, "Knudsen parabolic")
        self.aging_time_radio.set_tooltip_text("Use Knudsen parabolic law for hydration kinetics")
        vbox.pack_start(self.aging_time_radio, False, False, 0)
        
        # Time conversion factor (directly under Knudsen parabolic)
        time_factor_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        time_factor_box.set_margin_left(25)  # Indent to show it belongs to Knudsen parabolic
        
        time_factor_label = Gtk.Label("Time Conversion Factor (h⁻²):")
        time_factor_label.set_halign(Gtk.Align.START)
        time_factor_box.pack_start(time_factor_label, False, False, 0)
        
        self.time_conversion_spin = Gtk.SpinButton.new_with_range(0.0001, 1.0, 0.0001)
        self.time_conversion_spin.set_digits(5)
        self.time_conversion_spin.set_value(0.00045)  # Default for Knudsen parabolic
        self.time_conversion_spin.set_tooltip_text("Time conversion factor for Knudsen parabolic law (units: h⁻²)")
        time_factor_box.pack_start(self.time_conversion_spin, False, False, 0)
        
        vbox.pack_start(time_factor_box, False, False, 0)
        
        # Calorimetry-based option
        self.aging_calorimetry_radio = Gtk.RadioButton.new_with_label_from_widget(
            self.aging_time_radio, "Calorimetry-based")
        self.aging_calorimetry_radio.set_tooltip_text("Calibrate hydration kinetics based on measured heat release data")
        vbox.pack_start(self.aging_calorimetry_radio, False, False, 0)
        
        # File chooser (for calorimetry and shrinkage modes)
        file_chooser_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        file_chooser_box.set_margin_left(25)  # Indent to show it belongs to file-based modes
        
        self.data_file_label = Gtk.Label("Data File:")
        self.data_file_label.set_halign(Gtk.Align.START)
        file_chooser_box.pack_start(self.data_file_label, False, False, 0)
        
        self.data_file_button = Gtk.FileChooserButton("Select calibration data file", Gtk.FileChooserAction.OPEN)
        self.data_file_button.set_tooltip_text("Select experimental data file for calibration")
        
        # Set up file filters
        file_filter = Gtk.FileFilter()
        file_filter.set_name("Data files")
        file_filter.add_pattern("*.txt")
        file_filter.add_pattern("*.csv")
        file_filter.add_pattern("*.dat")
        self.data_file_button.add_filter(file_filter)
        
        all_filter = Gtk.FileFilter()
        all_filter.set_name("All files")
        all_filter.add_pattern("*")
        self.data_file_button.add_filter(all_filter)
        
        file_chooser_box.pack_start(self.data_file_button, True, True, 0)
        
        vbox.pack_start(file_chooser_box, False, False, 0)
        
        # Chemical Shrinkage-based option (shares file chooser with calorimetry)
        self.aging_shrinkage_radio = Gtk.RadioButton.new_with_label_from_widget(
            self.aging_time_radio, "Chemical Shrinkage-based")
        self.aging_shrinkage_radio.set_tooltip_text("Calibrate hydration kinetics based on measured chemical shrinkage data")
        vbox.pack_start(self.aging_shrinkage_radio, False, False, 0)
        
        # Add separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        vbox.pack_start(separator, False, False, 10)
        
        
        frame.add(vbox)
        parent.pack_start(frame, False, False, 0)
        
        # Set default mode and initialize display
        self.aging_time_radio.set_active(True)  # Default to Knudsen parabolic
    
    def _create_curing_conditions_section(self, parent: Gtk.Box) -> None:
        """Create curing conditions section."""
        frame = Gtk.Frame(label="Curing Conditions")
        frame.get_style_context().add_class("card")
        
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        vbox.set_margin_top(15)
        vbox.set_margin_bottom(15)
        vbox.set_margin_left(15)
        vbox.set_margin_right(15)
        
        # Thermal conditions section
        thermal_label = Gtk.Label()
        thermal_label.set_markup('<span weight="bold">Thermal Conditions</span>')
        thermal_label.set_halign(Gtk.Align.START)
        vbox.pack_start(thermal_label, False, False, 0)
        
        # Initial temperature
        temp_grid = Gtk.Grid()
        temp_grid.set_row_spacing(10)
        temp_grid.set_column_spacing(10)
        temp_grid.set_margin_left(15)
        
        temp_label = Gtk.Label("Initial Temperature (°C):")
        temp_label.set_halign(Gtk.Align.START)
        temp_label.set_tooltip_text("Starting temperature for the hydration simulation")
        temp_grid.attach(temp_label, 0, 0, 1, 1)
        
        self.initial_temp_spin = Gtk.SpinButton.new_with_range(-10.0, 80.0, 0.1)
        self.initial_temp_spin.set_digits(1)
        self.initial_temp_spin.set_value(25.0)
        self.initial_temp_spin.set_tooltip_text("Typical range: 5°C to 50°C for concrete curing")
        temp_grid.attach(self.initial_temp_spin, 1, 0, 1, 1)
        
        vbox.pack_start(temp_grid, False, False, 0)
        
        # Thermal condition mode
        thermal_mode_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        thermal_mode_box.set_margin_left(15)
        
        self.isothermal_radio = Gtk.RadioButton.new_with_label(None, "Isothermal")
        self.isothermal_radio.set_tooltip_text("Temperature remains constant throughout simulation")
        thermal_mode_box.pack_start(self.isothermal_radio, False, False, 0)
        
        self.adiabatic_radio = Gtk.RadioButton.new_with_label_from_widget(
            self.isothermal_radio, "Adiabatic")
        self.adiabatic_radio.set_tooltip_text("No heat exchange with environment - temperature rises due to hydration heat")
        thermal_mode_box.pack_start(self.adiabatic_radio, False, False, 0)
        
        self.temperature_profile_radio = Gtk.RadioButton.new_with_label_from_widget(
            self.isothermal_radio, "Temperature Profile")
        self.temperature_profile_radio.set_tooltip_text("Use custom temperature profile during simulation")
        thermal_mode_box.pack_start(self.temperature_profile_radio, False, False, 0)
        
        # Set default to isothermal
        self.isothermal_radio.set_active(True)
        
        vbox.pack_start(thermal_mode_box, False, False, 0)
        
        # Temperature profile selection
        profile_grid = Gtk.Grid()
        profile_grid.set_row_spacing(10)
        profile_grid.set_column_spacing(10)
        profile_grid.set_margin_left(15)
        
        profile_label = Gtk.Label("Temperature Profile:")
        profile_label.set_halign(Gtk.Align.START)
        profile_label.set_tooltip_text("Temperature variation during hydration simulation")
        profile_grid.attach(profile_label, 0, 0, 1, 1)
        
        profile_selection_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        
        self.profile_combo = Gtk.ComboBoxText()
        self.profile_combo.append("custom", "Custom")
        
        # Add all profiles (predefined + custom)
        profiles = self.hydration_service.get_all_temperature_profiles()
        for name, profile in profiles.items():
            self.profile_combo.append(name.lower().replace(" ", "_"), name)
        
        self.profile_combo.set_active(0)
        self.profile_combo.set_tooltip_text("Select temperature profile for simulation")
        profile_selection_box.pack_start(self.profile_combo, True, True, 0)
        
        self.edit_profile_button = Gtk.Button(label="Edit")
        self.edit_profile_button.set_tooltip_text("Edit temperature profile")
        profile_selection_box.pack_start(self.edit_profile_button, False, False, 0)
        
        profile_grid.attach(profile_selection_box, 1, 0, 1, 1)
        
        vbox.pack_start(profile_grid, False, False, 0)
        
        # Profile summary
        self.profile_summary_label = Gtk.Label()
        self.profile_summary_label.set_halign(Gtk.Align.START)
        self.profile_summary_label.get_style_context().add_class("dim-label")
        self.profile_summary_label.set_margin_left(15)
        vbox.pack_start(self.profile_summary_label, False, False, 0)
        
        # Separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        vbox.pack_start(separator, False, False, 5)
        
        # Moisture conditions section
        moisture_label = Gtk.Label()
        moisture_label.set_markup('<span weight="bold">Moisture Conditions</span>')
        moisture_label.set_halign(Gtk.Align.START)
        vbox.pack_start(moisture_label, False, False, 0)
        
        # Moisture condition mode
        moisture_mode_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        moisture_mode_box.set_margin_left(15)
        
        self.saturated_radio = Gtk.RadioButton.new_with_label(None, "Saturated")
        self.saturated_radio.set_tooltip_text("Sample remains water-saturated throughout simulation")
        moisture_mode_box.pack_start(self.saturated_radio, False, False, 0)
        
        self.sealed_radio = Gtk.RadioButton.new_with_label_from_widget(
            self.saturated_radio, "Sealed")
        self.sealed_radio.set_tooltip_text("No moisture exchange - water content remains constant")
        moisture_mode_box.pack_start(self.sealed_radio, False, False, 0)
        
        # Set default to sealed
        self.sealed_radio.set_active(True)
        
        vbox.pack_start(moisture_mode_box, False, False, 0)
        
        
        frame.add(vbox)
        parent.pack_start(frame, False, False, 0)
    
    
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
        
        # Save 3D microstructure interval
        save_interval_label = Gtk.Label("Save 3D microstructure every")
        save_interval_label.set_halign(Gtk.Align.START)
        save_interval_label.set_tooltip_text("Save 3D microstructure snapshots at specified intervals")
        grid.attach(save_interval_label, 0, 0, 1, 1)
        
        # Create horizontal box for spinbox and "hours" label
        save_interval_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        
        self.save_interval_spin = Gtk.SpinButton.new_with_range(0.1, 168.0, 0.1)
        self.save_interval_spin.set_digits(1)
        self.save_interval_spin.set_value(72.0)
        self.save_interval_spin.set_tooltip_text("Time interval for saving 3D microstructure snapshots")
        save_interval_box.pack_start(self.save_interval_spin, False, False, 0)
        
        hours_label = Gtk.Label("hours")
        hours_label.set_halign(Gtk.Align.START)
        save_interval_box.pack_start(hours_label, False, False, 0)
        
        grid.attach(save_interval_box, 1, 0, 1, 1)
        
        # Movie frame frequency
        movie_label = Gtk.Label("Save movie frame every")
        movie_label.set_halign(Gtk.Align.START)
        movie_label.set_tooltip_text("Time interval for saving movie frames showing simulation progress")
        grid.attach(movie_label, 0, 1, 1, 1)
        
        # Create horizontal box for movie spinbox and "hours" label
        movie_interval_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        
        self.movie_freq_spin = Gtk.SpinButton.new_with_range(0.1, 168.0, 0.1)
        self.movie_freq_spin.set_digits(1)
        self.movie_freq_spin.set_value(72.0)
        self.movie_freq_spin.set_tooltip_text("Time interval for saving movie frames")
        movie_interval_box.pack_start(self.movie_freq_spin, False, False, 0)
        
        movie_hours_label = Gtk.Label("hours")
        movie_hours_label.set_halign(Gtk.Align.START)
        movie_interval_box.pack_start(movie_hours_label, False, False, 0)
        
        grid.attach(movie_interval_box, 1, 1, 1, 1)
        
        frame.add(grid)
        parent.pack_start(frame, False, False, 0)
    
    def _create_advanced_settings_section(self, parent: Gtk.Box) -> None:
        """Create advanced settings section with expandable controls."""
        # Use Gtk.Expander for collapsible section
        expander = Gtk.Expander(label="Advanced Settings")
        expander.set_tooltip_text("Advanced simulation parameters (normally not needed)")
        expander.get_style_context().add_class("card")
        expander.set_expanded(False)  # Collapsed by default
        
        # Main content box
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        content_box.set_margin_top(10)
        content_box.set_margin_bottom(15)
        content_box.set_margin_left(15)
        content_box.set_margin_right(15)
        
        # Simulation Control Section
        sim_label = Gtk.Label()
        sim_label.set_markup('<span weight="bold">Simulation Control</span>')
        sim_label.set_halign(Gtk.Align.START)
        content_box.pack_start(sim_label, False, False, 0)
        
        sim_grid = Gtk.Grid()
        sim_grid.set_row_spacing(8)
        sim_grid.set_column_spacing(10)
        sim_grid.set_margin_left(15)
        
        # Random Seed
        seed_label = Gtk.Label("Random Seed:")
        seed_label.set_halign(Gtk.Align.START)
        seed_label.set_tooltip_text("Negative integer for reproducible simulations")
        sim_grid.attach(seed_label, 0, 0, 1, 1)
        
        self.random_seed_spin = Gtk.SpinButton.new_with_range(-999999, -1, 1)
        self.random_seed_spin.set_value(-12345)
        self.random_seed_spin.set_tooltip_text("Random seed for simulation (negative integer)")
        sim_grid.attach(self.random_seed_spin, 1, 0, 1, 1)
        
        # C3A fraction
        c3a_label = Gtk.Label("Orth. C3A Fraction:")
        c3a_label.set_halign(Gtk.Align.START)
        c3a_label.set_tooltip_text("Fraction of orthorhombic C3A in cement (0.0-1.0)")
        sim_grid.attach(c3a_label, 0, 1, 1, 1)
        
        self.c3a_fraction_spin = Gtk.SpinButton.new_with_range(0.0, 1.0, 0.01)
        self.c3a_fraction_spin.set_digits(3)
        self.c3a_fraction_spin.set_value(0.0)
        self.c3a_fraction_spin.set_tooltip_text("Orthorhombic C3A fraction (default 0.0)")
        sim_grid.attach(self.c3a_fraction_spin, 1, 1, 1, 1)
        
        # CSH Seeds
        csh_label = Gtk.Label("CSH Seeds (cm⁻³):")
        csh_label.set_halign(Gtk.Align.START)
        csh_label.set_tooltip_text("Number of CSH nucleation seeds per cubic cm")
        sim_grid.attach(csh_label, 0, 2, 1, 1)
        
        self.csh_seeds_spin = Gtk.SpinButton.new_with_range(0.0, 1000.0, 0.1)
        self.csh_seeds_spin.set_digits(1)
        self.csh_seeds_spin.set_value(0.0)
        self.csh_seeds_spin.set_tooltip_text("CSH nucleation seeds (default 0.0 cm⁻³)")
        sim_grid.attach(self.csh_seeds_spin, 1, 2, 1, 1)
        
        
        content_box.pack_start(sim_grid, False, False, 0)
        
        # Activation Energies Section
        energy_label = Gtk.Label()
        energy_label.set_markup('<span weight="bold">Activation Energies (kJ/mol)</span>')
        energy_label.set_halign(Gtk.Align.START)
        content_box.pack_start(energy_label, False, False, 0)
        
        energy_grid = Gtk.Grid()
        energy_grid.set_row_spacing(8)
        energy_grid.set_column_spacing(10)
        energy_grid.set_margin_left(15)
        
        # Cement activation energy
        e_act_label = Gtk.Label("Cement E_act:")
        e_act_label.set_halign(Gtk.Align.START)
        energy_grid.attach(e_act_label, 0, 0, 1, 1)
        
        self.e_act_spin = Gtk.SpinButton.new_with_range(10.0, 100.0, 0.1)
        self.e_act_spin.set_digits(1)
        self.e_act_spin.set_value(40.0)
        self.e_act_spin.set_tooltip_text("Activation energy for cement hydration (default 40.0 kJ/mol)")
        energy_grid.attach(self.e_act_spin, 1, 0, 1, 1)
        
        # Pozzolan activation energy
        e_act_pozz_label = Gtk.Label("Pozzolan E_act:")
        e_act_pozz_label.set_halign(Gtk.Align.START)
        energy_grid.attach(e_act_pozz_label, 0, 1, 1, 1)
        
        self.e_act_pozz_spin = Gtk.SpinButton.new_with_range(10.0, 150.0, 0.1)
        self.e_act_pozz_spin.set_digits(1)
        self.e_act_pozz_spin.set_value(83.1)
        self.e_act_pozz_spin.set_tooltip_text("Activation energy for pozzolan reaction (default 83.1 kJ/mol)")
        energy_grid.attach(self.e_act_pozz_spin, 1, 1, 1, 1)
        
        # Slag activation energy
        e_act_slag_label = Gtk.Label("Slag E_act:")
        e_act_slag_label.set_halign(Gtk.Align.START)
        energy_grid.attach(e_act_slag_label, 0, 2, 1, 1)
        
        self.e_act_slag_spin = Gtk.SpinButton.new_with_range(10.0, 100.0, 0.1)
        self.e_act_slag_spin.set_digits(1)
        self.e_act_slag_spin.set_value(50.0)
        self.e_act_slag_spin.set_tooltip_text("Activation energy for slag reaction (default 50.0 kJ/mol)")
        energy_grid.attach(self.e_act_slag_spin, 1, 2, 1, 1)
        
        content_box.pack_start(energy_grid, False, False, 0)
        
        # Output Frequencies Section
        output_label = Gtk.Label()
        output_label.set_markup('<span weight="bold">Output Frequencies (hours)</span>')
        output_label.set_halign(Gtk.Align.START)
        content_box.pack_start(output_label, False, False, 0)
        
        output_grid = Gtk.Grid()
        output_grid.set_row_spacing(8)
        output_grid.set_column_spacing(10)
        output_grid.set_margin_left(15)
        
        # Burn time frequency
        burn_label = Gtk.Label("Burn Frequency:")
        burn_label.set_halign(Gtk.Align.START)
        output_grid.attach(burn_label, 0, 0, 1, 1)
        
        self.burn_freq_spin = Gtk.SpinButton.new_with_range(0.1, 24.0, 0.1)
        self.burn_freq_spin.set_digits(2)
        self.burn_freq_spin.set_value(1.0)
        self.burn_freq_spin.set_tooltip_text("Frequency for burning calculations (default 1.0 h)")
        output_grid.attach(self.burn_freq_spin, 1, 0, 1, 1)
        
        # Setting time frequency
        set_label = Gtk.Label("Setting Frequency:")
        set_label.set_halign(Gtk.Align.START)
        output_grid.attach(set_label, 0, 1, 1, 1)
        
        self.set_freq_spin = Gtk.SpinButton.new_with_range(0.1, 24.0, 0.1)
        self.set_freq_spin.set_digits(2)
        self.set_freq_spin.set_value(0.25)
        self.set_freq_spin.set_tooltip_text("Frequency for setting time calculations (default 0.25 h)")
        output_grid.attach(self.set_freq_spin, 1, 1, 1, 1)
        
        # Physical properties frequency
        phyd_label = Gtk.Label("Physical Props Frequency:")
        phyd_label.set_halign(Gtk.Align.START)
        output_grid.attach(phyd_label, 0, 2, 1, 1)
        
        self.phyd_freq_spin = Gtk.SpinButton.new_with_range(0.1, 24.0, 0.1)
        self.phyd_freq_spin.set_digits(2)
        self.phyd_freq_spin.set_value(2.0)
        self.phyd_freq_spin.set_tooltip_text("Frequency for physical properties calculations (default 2.0 h)")
        output_grid.attach(self.phyd_freq_spin, 1, 2, 1, 1)
        
        content_box.pack_start(output_grid, False, False, 0)
        
        # Phase Control Section
        phase_label = Gtk.Label()
        phase_label.set_markup('<span weight="bold">Phase Control</span>')
        phase_label.set_halign(Gtk.Align.START)
        content_box.pack_start(phase_label, False, False, 0)
        
        phase_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        phase_box.set_margin_left(15)
        
        self.csh2_flag_check = Gtk.CheckButton(label="Enable CSH Type 2")
        self.csh2_flag_check.set_active(True)
        self.csh2_flag_check.set_tooltip_text("Enable CSH Type 2 formation (default enabled)")
        phase_box.pack_start(self.csh2_flag_check, False, False, 0)
        
        self.ch_flag_check = Gtk.CheckButton(label="Enable CH Formation")
        self.ch_flag_check.set_active(True)
        self.ch_flag_check.set_tooltip_text("Enable calcium hydroxide formation (default enabled)")
        phase_box.pack_start(self.ch_flag_check, False, False, 0)
        
        self.ph_active_check = Gtk.CheckButton(label="Enable pH Calculations")
        self.ph_active_check.set_active(True)
        self.ph_active_check.set_tooltip_text("Enable pH calculations (default enabled)")
        phase_box.pack_start(self.ph_active_check, False, False, 0)
        
        self.ettringite_check = Gtk.CheckButton(label="Enable Ettringite Formation")
        self.ettringite_check.set_active(True)
        self.ettringite_check.set_tooltip_text("Enable ettringite formation during hydration")
        phase_box.pack_start(self.ettringite_check, False, False, 0)
        
        content_box.pack_start(phase_box, False, False, 0)
        
        
        # Database Parameters Section
        db_label = Gtk.Label()
        db_label.set_markup('<span weight="bold">Database Parameters (378 parameters)</span>')
        db_label.set_halign(Gtk.Align.START)
        content_box.pack_start(db_label, False, False, 0)
        
        # Parameters viewer with search
        params_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        params_box.set_margin_left(15)
        
        # Search entry
        search_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        
        search_label = Gtk.Label("Search:")
        search_label.set_halign(Gtk.Align.START)
        search_box.pack_start(search_label, False, False, 0)
        
        self.param_search_entry = Gtk.SearchEntry()
        self.param_search_entry.set_placeholder_text("Filter parameters...")
        self.param_search_entry.connect('search-changed', self._on_param_search_changed)
        search_box.pack_start(self.param_search_entry, True, True, 0)
        
        # Refresh button to reload from database
        refresh_params_btn = Gtk.Button(label="Refresh")
        refresh_params_btn.set_tooltip_text("Reload parameters from database")
        refresh_params_btn.connect('clicked', self._on_refresh_params_clicked)
        search_box.pack_start(refresh_params_btn, False, False, 0)
        
        params_box.pack_start(search_box, False, False, 0)
        
        # Scrolled window for parameters table
        params_scrolled = Gtk.ScrolledWindow()
        params_scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        params_scrolled.set_size_request(250, 300)  # Reduced width to allow narrower windows
        
        # TreeView for parameters
        self.params_store = Gtk.ListStore(str, str, str)  # name, value, type
        self.params_tree = Gtk.TreeView(model=self.params_store)
        self.params_tree.set_tooltip_text("Double-click to edit parameter values")
        
        # Name column
        name_renderer = Gtk.CellRendererText()
        name_column = Gtk.TreeViewColumn("Parameter Name", name_renderer, text=0)
        name_column.set_resizable(True)
        name_column.set_min_width(150)  # Reduced to allow narrower windows
        name_column.set_sort_column_id(0)
        self.params_tree.append_column(name_column)
        
        # Value column (editable)
        value_renderer = Gtk.CellRendererText()
        value_renderer.set_property("editable", True)
        value_renderer.connect("edited", self._on_param_value_edited)
        value_column = Gtk.TreeViewColumn("Value", value_renderer, text=1)
        value_column.set_resizable(True)
        value_column.set_min_width(100)
        value_column.set_sort_column_id(1)
        self.params_tree.append_column(value_column)
        
        # Type column
        type_renderer = Gtk.CellRendererText()
        type_column = Gtk.TreeViewColumn("Type", type_renderer, text=2)
        type_column.set_resizable(True)
        type_column.set_min_width(80)
        type_column.set_sort_column_id(2)
        self.params_tree.append_column(type_column)
        
        # Enable sorting
        self.params_store.set_sort_column_id(0, Gtk.SortType.ASCENDING)
        
        params_scrolled.add(self.params_tree)
        params_box.pack_start(params_scrolled, True, True, 0)
        
        # Export/Import buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        
        export_btn = create_button_with_icon("Export to CSV", "export", 16)
        export_btn.set_tooltip_text("Export parameters to CSV file")
        export_btn.connect('clicked', self._on_export_params_clicked)
        button_box.pack_start(export_btn, False, False, 0)
        
        import_btn = create_button_with_icon("Import from CSV", "folder--open", 16)
        import_btn.set_tooltip_text("Import parameters from CSV file")
        import_btn.connect('clicked', self._on_import_params_clicked)
        button_box.pack_start(import_btn, False, False, 0)
        
        reset_btn = create_button_with_icon("Reset to Defaults", "refresh", 16)
        reset_btn.set_tooltip_text("Reset all parameters to default values")
        reset_btn.connect('clicked', self._on_reset_params_clicked)
        button_box.pack_start(reset_btn, False, False, 0)
        
        params_box.pack_start(button_box, False, False, 0)
        
        content_box.pack_start(params_box, True, True, 0)
        
        # Store for tracking parameter changes
        self.modified_params = {}
        
        # Load initial parameters
        self._load_database_parameters()
        
        # Add content to expander
        expander.add(content_box)
        parent.pack_start(expander, False, False, 0)
    
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
        
        # Operation name input
        name_label = Gtk.Label("Operation Name:")
        name_label.set_halign(Gtk.Align.END)
        control_box.pack_start(name_label, False, False, 0)
        
        self.operation_name_entry = Gtk.Entry()
        self.operation_name_entry.set_placeholder_text("Enter operation name (optional)")
        self.operation_name_entry.set_width_chars(25)
        self.operation_name_entry.set_tooltip_text("Custom name for this hydration simulation (leave blank for auto-generated)")
        control_box.pack_start(self.operation_name_entry, False, False, 0)
        
        # Spacer between name and validation
        control_box.pack_start(Gtk.Box(), False, False, 10)
        
        # Save/Load buttons (following Mix Design pattern)
        save_load_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        save_load_box.get_style_context().add_class("linked")
        
        self.load_params_button = create_button_with_icon("Load", "folder--open", 16)
        self.load_params_button.set_tooltip_text("Load saved hydration parameters")
        save_load_box.pack_start(self.load_params_button, False, False, 0)
        
        self.save_params_button = create_button_with_icon("Save", "save", 16)
        self.save_params_button.get_style_context().add_class("suggested-action")
        self.save_params_button.set_tooltip_text("Save current hydration parameters")
        save_load_box.pack_start(self.save_params_button, False, False, 0)
        
        control_box.pack_start(save_load_box, False, False, 0)
        
        # Spacer
        control_box.pack_start(Gtk.Box(), False, False, 10)
        
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
        
        self.start_button = create_button_with_icon("Start Simulation", "play", 16)
        self.start_button.set_sensitive(False)
        button_box.pack_start(self.start_button, False, False, 0)
        
        self.pause_button = create_button_with_icon("Pause", "pause", 16)
        self.pause_button.set_sensitive(False)
        button_box.pack_start(self.pause_button, False, False, 0)
        
        self.stop_button = create_button_with_icon("Stop", "stop", 16)
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
        left_progress.set_size_request(200, -1)  # Reduced from 300 to allow narrower windows
        
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
        right_progress.set_size_request(200, -1)  # Reduced from 300 to allow narrower windows
        
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
        self.max_time_spin.connect('value-changed', self._on_parameter_changed)
        
        # Time calibration mode signals
        self.aging_time_radio.connect('toggled', self._on_aging_mode_changed)
        self.aging_calorimetry_radio.connect('toggled', self._on_aging_mode_changed)
        self.aging_shrinkage_radio.connect('toggled', self._on_aging_mode_changed)
        self.data_file_button.connect('file-set', self._on_parameter_changed)
        self.time_conversion_spin.connect('value-changed', self._on_parameter_changed)
        
        # Curing conditions signals
        self.initial_temp_spin.connect('value-changed', self._on_parameter_changed)
        self.isothermal_radio.connect('toggled', self._on_thermal_mode_changed)
        self.adiabatic_radio.connect('toggled', self._on_thermal_mode_changed)
        self.temperature_profile_radio.connect('toggled', self._on_thermal_mode_changed)
        self.saturated_radio.connect('toggled', self._on_parameter_changed)
        self.sealed_radio.connect('toggled', self._on_parameter_changed)
        
        # Microstructure selection signals
        self.microstructure_combo.connect('changed', self._on_microstructure_changed)
        self.refresh_button.connect('clicked', self._on_refresh_clicked)
        
        # Temperature profile signals
        self.profile_combo.connect('changed', self._on_profile_changed)
        self.edit_profile_button.connect('clicked', self._on_edit_profile_clicked)
        
        # Output settings signals
        self.save_interval_spin.connect('value-changed', self._on_parameter_changed)
        
        # Advanced settings signals
        self.random_seed_spin.connect('value-changed', self._on_parameter_changed)
        self.c3a_fraction_spin.connect('value-changed', self._on_parameter_changed)
        self.csh_seeds_spin.connect('value-changed', self._on_parameter_changed)
        self.alpha_max_spin.connect('value-changed', self._on_parameter_changed)
        self.e_act_spin.connect('value-changed', self._on_parameter_changed)
        self.e_act_pozz_spin.connect('value-changed', self._on_parameter_changed)
        self.e_act_slag_spin.connect('value-changed', self._on_parameter_changed)
        self.burn_freq_spin.connect('value-changed', self._on_parameter_changed)
        self.set_freq_spin.connect('value-changed', self._on_parameter_changed)
        self.phyd_freq_spin.connect('value-changed', self._on_parameter_changed)
        self.movie_freq_spin.connect('value-changed', self._on_parameter_changed)
        self.csh2_flag_check.connect('toggled', self._on_parameter_changed)
        self.ch_flag_check.connect('toggled', self._on_parameter_changed)
        self.ph_active_check.connect('toggled', self._on_parameter_changed)
        
        # Control signals
        self.save_params_button.connect('clicked', self._on_save_params_clicked)
        self.load_params_button.connect('clicked', self._on_load_params_clicked)
        self.validate_button.connect('clicked', self._on_validate_clicked)
        self.start_button.connect('clicked', self._on_start_clicked)
        self.pause_button.connect('clicked', self._on_pause_clicked)
        self.stop_button.connect('clicked', self._on_stop_clicked)
    
    def _load_default_parameters(self) -> None:
        """Load default parameters."""
        # Load default temperature profile (constant 25°C)
        profiles = self.hydration_service.get_all_temperature_profiles()
        self.current_temperature_profile = profiles.get("Constant 25°C")
        self.current_profile = self.current_temperature_profile  # Ensure consistency
        
        self._update_temperature_plot()
        self._update_profile_summary()
        self._update_status("Ready - configure parameters and click Validate")
    
    def _on_parameter_changed(self, widget) -> None:
        """Handle parameter change."""
        self._clear_validation()
    
    def _on_thermal_mode_changed(self, radio) -> None:
        """Handle thermal mode change."""
        if not radio.get_active():
            return
        
        # Enable/disable initial temperature based on thermal mode
        if self.temperature_profile_radio.get_active():
            # Temperature profile mode - disable initial temperature
            self.initial_temp_spin.set_sensitive(False)
            self.profile_combo.set_sensitive(True)
            self.edit_profile_button.set_sensitive(True)
        else:
            # Isothermal or adiabatic mode - enable initial temperature
            self.initial_temp_spin.set_sensitive(True)
            # Optionally disable profile controls (or leave enabled for reference)
            self.profile_combo.set_sensitive(False)
            self.edit_profile_button.set_sensitive(False)
        
        self._clear_validation()
    
    def _on_aging_mode_changed(self, radio) -> None:
        """Handle time calibration mode change."""
        if not radio.get_active():
            return
        
        # Show/hide appropriate parameter controls based on mode
        if self.aging_time_radio.get_active():
            # Knudsen parabolic mode - show time conversion factor, hide file chooser
            self.time_conversion_spin.get_parent().show()
            self.data_file_button.get_parent().hide()
            
        elif self.aging_calorimetry_radio.get_active():
            # Calorimetry mode - hide time conversion factor, show file chooser
            self.time_conversion_spin.get_parent().hide() 
            self.data_file_button.get_parent().show()
            self.data_file_label.set_text("Calorimetry Data File:")
            self.data_file_button.set_tooltip_text("Select isothermal microcalorimetry data file for calibration")
            
        elif self.aging_shrinkage_radio.get_active():
            # Chemical shrinkage mode - hide time conversion factor, show file chooser
            self.time_conversion_spin.get_parent().hide()
            self.data_file_button.get_parent().show()
            self.data_file_label.set_text("Shrinkage Data File:")
            self.data_file_button.set_tooltip_text("Select chemical shrinkage data file for calibration")
    
    def _on_profile_changed(self, combo) -> None:
        """Handle temperature profile selection change."""
        profile_id = combo.get_active_id()
        
        if profile_id and profile_id != "custom":
            profiles = self.hydration_service.get_all_temperature_profiles()
            profile_name = combo.get_active_text()
            
            if profile_name in profiles:
                self.current_temperature_profile = profiles[profile_name]
                self.current_profile = self.current_temperature_profile
                self._update_temperature_plot()
                self._update_profile_summary()
    
    def _on_microstructure_changed(self, combo) -> None:
        """Handle microstructure selection change."""
        microstructure_id = combo.get_active_id()
        
        if microstructure_id:
            # Store selected microstructure info
            self.selected_microstructure = {
                'operation_name': microstructure_id,
                'img_file': f"./Operations/{microstructure_id}/{microstructure_id}.img",
                'pimg_file': f"./Operations/{microstructure_id}/{microstructure_id}.pimg"
            }
            
            # Update info display
            self._update_microstructure_info()
            self._clear_validation()  # Parameters need re-validation with new microstructure
            
        else:
            self.selected_microstructure = None
            self.microstructure_info_label.set_text("No microstructure selected")
    
    def _on_refresh_clicked(self, button) -> None:
        """Handle refresh microstructure list button click."""
        self._refresh_microstructure_list()
        self._update_status("Microstructure list refreshed")
    
    def _on_edit_profile_clicked(self, button) -> None:
        """Handle edit temperature profile button click."""
        try:
            # Get current profile or create new one
            current_profile = self.current_temperature_profile
            if not current_profile:
                from app.services.hydration_service import TemperatureProfile, TemperaturePoint
                current_profile = TemperatureProfile(
                    name="Custom Profile",
                    description="User-defined temperature profile",
                    points=[TemperaturePoint(0.0, 25.0)]
                )
            
            # Open temperature profile editor dialog
            dialog = TemperatureProfileDialog(self.get_toplevel(), current_profile)
            
            while True:
                response = dialog.run()
                
                if response == Gtk.ResponseType.OK:
                    # Get the modified profile
                    modified_profile = dialog.get_profile()
                    
                    # Update current profile
                    self.current_temperature_profile = modified_profile
                    self.current_profile = self.current_temperature_profile
                    
                    # Update UI
                    self._update_temperature_plot()
                    self._update_profile_summary()
                    self._update_status("Temperature profile updated")
                    break
                    
                elif response == Gtk.ResponseType.ACCEPT:  # Save button
                    # Save profile to database
                    modified_profile = dialog.get_profile()
                    if self._save_temperature_profile(modified_profile):
                        # Continue dialog for more editing if desired
                        self._update_status(f"Temperature profile '{modified_profile.name}' saved to database")
                        continue
                    else:
                        # Save failed, continue dialog
                        continue
                else:
                    # Cancel or close
                    break
            
            dialog.destroy()
            
        except Exception as e:
            self.logger.error(f"Failed to open temperature profile editor: {e}")
            self._update_status(f"Error opening profile editor: {e}")
    
    def _save_temperature_profile(self, profile: TemperatureProfile) -> bool:
        """
        Save a temperature profile to the database and update UI.
        
        Args:
            profile: TemperatureProfile to save
            
        Returns:
            True if save successful, False otherwise
        """
        try:
            # Validate profile name
            if not profile.name or not profile.name.strip():
                self._show_error_dialog("Save Error", "Profile name cannot be empty")
                return False
            
            # Use direct database access for temperature profile saving
            from app.models.temperature_profile import TemperatureProfileDB
            from app.services.service_container import get_service_container
            
            container = get_service_container()
            
            with container.database_service.get_session() as session:
                # Check if profile already exists
                existing_profile = session.query(TemperatureProfileDB).filter(
                    TemperatureProfileDB.name == profile.name
                ).first()
                
                if existing_profile:
                    # Show confirmation dialog
                    dialog = Gtk.MessageDialog(
                        parent=self.get_toplevel(),
                        flags=Gtk.DialogFlags.MODAL,
                        message_type=Gtk.MessageType.QUESTION,
                        buttons=Gtk.ButtonsType.YES_NO,
                        text=f"Profile '{profile.name}' already exists. Overwrite?"
                    )
                    response = dialog.run()
                    dialog.destroy()
                    
                    if response != Gtk.ResponseType.YES:
                        return False
                    
                    # Update existing profile
                    existing_profile.description = profile.description
                    import json
                    existing_profile.points_json = json.dumps([{"time_hours": p.time_hours, "temperature_celsius": p.temperature_celsius} 
                                                             for p in profile.points])
                else:
                    # Create new profile
                    import json
                    new_profile = TemperatureProfileDB(
                        name=profile.name,
                        description=profile.description,
                        points_json=json.dumps([{"time_hours": p.time_hours, "temperature_celsius": p.temperature_celsius} 
                                              for p in profile.points])
                    )
                    session.add(new_profile)
                
                session.commit()
                
                # Refresh the dropdown menu
                self._refresh_profile_dropdown()
                self.logger.info(f"Saved temperature profile: {profile.name}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to save temperature profile: {e}")
            self._show_error_dialog("Save Error", f"Failed to save profile: {e}")
            return False
    
    def _refresh_profile_dropdown(self) -> None:
        """Refresh the temperature profile dropdown with latest profiles."""
        try:
            # Get all profiles (predefined + custom)
            all_profiles = self.hydration_service.get_all_temperature_profiles()
            
            # Clear and repopulate dropdown
            self.profile_combo.remove_all()
            
            # Add profiles with proper IDs for set_active_id to work
            for profile_name in sorted(all_profiles.keys()):
                profile_id = profile_name.lower().replace(" ", "_")
                self.profile_combo.append(profile_id, profile_name)
            
            # Set to current profile if it exists
            if self.current_temperature_profile and self.current_temperature_profile.name in all_profiles:
                profile_id = self.current_temperature_profile.name.lower().replace(" ", "_")
                self.profile_combo.set_active_id(profile_id)
            else:
                # Set to first item if current profile not found
                if len(all_profiles) > 0:
                    self.profile_combo.set_active(0)
                
        except Exception as e:
            self.logger.error(f"Failed to refresh profile dropdown: {e}", exc_info=True)
    
    def _show_error_dialog(self, title: str, message: str) -> None:
        """Show an error dialog."""
        dialog = Gtk.MessageDialog(
            parent=self.get_toplevel(),
            flags=Gtk.DialogFlags.MODAL,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=title
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()
    
    def _on_validate_clicked(self, button) -> None:
        """Handle validate parameters button click."""
        try:
            # Check microstructure selection first
            if not self.selected_microstructure:
                self._update_status("Please select a microstructure first")
                self.start_button.set_sensitive(False)
                return
            
            # Verify microstructure files exist
            img_file = self.selected_microstructure['img_file']
            pimg_file = self.selected_microstructure['pimg_file']
            
            if not os.path.exists(img_file):
                self._update_status(f"Microstructure image file not found: {os.path.basename(img_file)}")
                self.start_button.set_sensitive(False)
                return
            
            if not os.path.exists(pimg_file):
                self._update_status(f"Microstructure phase image file not found: {os.path.basename(pimg_file)}")
                self.start_button.set_sensitive(False)
                return
            
            # Get current parameters
            params = self._get_current_parameters()
            
            # Validate parameters
            validation = self.hydration_service.validate_hydration_parameters(params)
            
            # Estimate computation time (include microstructure info for size-based scaling)
            microstructure_info = None
            if self.selected_microstructure:
                print(f"DEBUG_MICRO: selected_microstructure keys: {list(self.selected_microstructure.keys())}")
                print(f"DEBUG_MICRO: selected_microstructure data: {self.selected_microstructure}")
                
                # Try to read actual cube size from the ASCII microstructure file
                actual_cubesize = 100  # default
                img_file = self.selected_microstructure.get('img_file')
                if img_file and os.path.exists(img_file):
                    try:
                        # Read cube size from ASCII header (X_Size, Y_Size, Z_Size lines)
                        with open(img_file, 'r') as f:
                            lines = f.readlines()[:10]  # Read first 10 lines to find size info
                            x_size = y_size = z_size = 100  # defaults
                            
                            for line in lines:
                                line = line.strip()
                                if line.startswith('X_Size:'):
                                    x_size = int(line.split(':')[1].strip())
                                elif line.startswith('Y_Size:'):
                                    y_size = int(line.split(':')[1].strip())
                                elif line.startswith('Z_Size:'):
                                    z_size = int(line.split(':')[1].strip())
                            
                            # Assume cubic (should all be same, but use max to be safe)
                            actual_cubesize = max(x_size, y_size, z_size)
                            print(f"DEBUG_MICRO: Read cube size from ASCII file: {x_size}x{y_size}x{z_size} -> {actual_cubesize}")
                    except Exception as e:
                        print(f"DEBUG_MICRO: Failed to read cube size from {img_file}: {e}")
                
                microstructure_info = {
                    'cubesize': actual_cubesize,
                    'voxel_count': actual_cubesize ** 3,
                    'name': self.selected_microstructure.get('operation_name', 'Unknown')
                }
                print(f"DEBUG_MICRO: microstructure_info created: {microstructure_info}")
            else:
                print("DEBUG_MICRO: No microstructure selected")
            estimate = self.hydration_service.estimate_simulation_time(params, microstructure_info)
            
            # Update displays
            self._update_validation_display(validation)
            self._update_estimate_display(estimate)
            
            # Enable start button if valid
            self.start_button.set_sensitive(validation['is_valid'])
            
            if validation['is_valid']:
                self.current_params = params
                
                # Perform in-memory parameter validation without creating files/folders
                try:
                    # Get all parameter settings for validation
                    curing_conditions = self.get_curing_conditions()
                    time_calibration_settings = self.get_time_calibration_settings()
                    advanced_settings = self.get_advanced_settings()
                    db_param_modifications = self.get_database_parameter_modifications()
                    max_time = self.max_time_spin.get_value()
                    
                    # Validate that we can load required data without file creation
                    from app.services.microstructure_hydration_bridge import MicrostructureHydrationBridge
                    bridge = MicrostructureHydrationBridge()
                    
                    # Check if microstructure metadata exists (validates microstructure compatibility)
                    try:
                        metadata = bridge.load_microstructure_metadata(self.selected_microstructure['operation_name'])
                        if not metadata:
                            raise ValueError(f"❌ CRITICAL DATA TRACKING ISSUE: No metadata found for microstructure: {self.selected_microstructure['operation_name']}\n\n" +
                                           "This means the microstructure operation was not properly linked to its mix design data.\n" +
                                           "This is a system bug - the MicrostructureOperation database record was not created.\n\n" +
                                           "Please recreate the microstructure operation to fix this issue.")
                    except Exception as e:
                        self.logger.error(f"❌ Metadata loading failed for {self.selected_microstructure['operation_name']}: {e}")
                        raise ValueError(f"❌ Cannot validate hydration parameters: Microstructure metadata missing.\n\n" +
                                       f"Operation: {self.selected_microstructure['operation_name']}\n" +
                                       f"Error: {str(e)}\n\n" +
                                       "This indicates the microstructure operation has incomplete data tracking.\n" +
                                       "Please recreate the microstructure operation.")
                    
                    # Validate parameter completeness (without file generation)
                    self._validate_parameter_completeness(curing_conditions, time_calibration_settings, 
                                                        advanced_settings, db_param_modifications)
                    
                    self._update_status("Parameters validated successfully - ready to start simulation")
                    self.logger.info("Parameter validation completed successfully (in-memory)")
                    
                except Exception as e:
                    self.logger.error(f"Parameter validation failed: {e}")
                    self._update_status(f"Parameter validation failed: {e}")
                
            else:
                self._update_status("Parameter validation failed - check errors")
            
            self.logger.info("Parameter validation completed")
            
        except Exception as e:
            self.logger.error(f"Validation failed: {e}")
            self._update_status(f"Validation error: {e}")
    
    def _on_start_clicked(self, button) -> None:
        """Handle start simulation button click."""
        try:
            # Validate microstructure selection
            selected_microstructure = self._get_selected_microstructure()
            if not selected_microstructure:
                self._update_status("Please select a microstructure first")
                return
            
            # Collect all UI settings
            curing_conditions = self._collect_curing_conditions()
            time_calibration = self._collect_time_calibration_settings()
            advanced_settings = self._collect_advanced_settings()
            db_modifications = self._collect_database_modifications()
            
            # Phase 3: Clean naming - use user-defined operation name directly
            operation_name = self.operation_name_entry.get_text().strip()
            if not operation_name:
                self._update_status("Please enter an operation name")
                return
            
            # Phase 3: Capture UI parameters for storage and reproducibility
            ui_parameters = self._capture_hydration_ui_parameters(
                operation_name, selected_microstructure, curing_conditions,
                time_calibration, advanced_settings, db_modifications
            )

            # Auto-save hydration configuration before execution
            self.logger.info("🚨 Starting hydration autosave process...")
            try:
                saved_hydration_id = self._auto_save_hydration_before_execution(
                    operation_name, selected_microstructure, curing_conditions,
                    time_calibration, advanced_settings, db_modifications, ui_parameters
                )
                if saved_hydration_id:
                    self.logger.info(f"✅ Hydration configuration auto-saved with ID: {saved_hydration_id}")
                    self._update_status("Hydration configuration auto-saved. Starting simulation...", "info", 2)
                else:
                    self.logger.warning("⚠️ Hydration autosave failed, but continuing with simulation")
            except Exception as e:
                self.logger.error(f"❌ Hydration autosave error: {e}")
                # Continue with simulation even if autosave fails

            # Phase 3: Create database operation with UI parameters and lineage
            parent_operation_id = self._find_microstructure_operation_id(selected_microstructure['name'])
            operation = self._create_hydration_operation(operation_name, ui_parameters, parent_operation_id)
            
            # Generate extended parameter file
            max_time = self.max_time_spin.get_value()
            param_file_path = self.bridge_service.generate_extended_parameter_file(
                operation_name=operation_name,
                microstructure_name=selected_microstructure['name'],
                curing_conditions=curing_conditions,
                time_calibration_settings=time_calibration,
                advanced_settings=advanced_settings,
                db_parameter_modifications=db_modifications,
                max_time_hours=max_time
            )
            
            # Start simulation using HydrationExecutorService
            executor = self.service_container.hydration_executor_service
            if executor.start_hydration_simulation(
                operation_name=operation_name,
                parameter_set_name="portland_cement_standard",
                progress_callback=self._on_simulation_progress,
                parameter_file_path=param_file_path,
                max_time_hours=max_time
            ):
                self.simulation_running = True
                self.current_operation_name = operation_name
                self.simulation_start_time = time.time()
                self.latest_progress = None
                self._update_simulation_controls(True)
                self._start_progress_updates()
                self._update_status(f"Simulation started: {operation_name}")
                self.logger.info(f"Hydration simulation started: {operation_name}")
                
                # Register the hydration process with operations panel for pause/resume support
                # Use a delayed registration with retry to ensure operation is loaded in operations panel
                from gi.repository import GLib
                GLib.timeout_add(1000, self._retry_registration, operation_name, executor, 0)
            else:
                self._update_status("Failed to start simulation")
            
        except Exception as e:
            self.logger.error(f"Failed to start simulation: {e}")
            self._update_status(f"Start error: {e}")
    
    def _get_selected_microstructure(self) -> Optional[Dict[str, Any]]:
        """Get the currently selected microstructure."""
        if hasattr(self, 'microstructure_combo') and self.microstructure_combo.get_active_text():
            microstructure_name = self.microstructure_combo.get_active_text()
            return {
                'name': microstructure_name,
                'path': f"./Operations/{microstructure_name}"
            }
        return None
    
    def _collect_curing_conditions(self) -> Dict[str, Any]:
        """Collect curing conditions from UI."""
        # Determine thermal mode
        if self.isothermal_radio.get_active():
            thermal_mode = 'isothermal'
        elif self.adiabatic_radio.get_active():
            thermal_mode = 'adiabatic'
        else:  # temperature_profile_radio.get_active()
            thermal_mode = 'temperature_profile'
        
        conditions = {
            'initial_temperature_celsius': self.initial_temp_spin.get_value(),
            'thermal_mode': thermal_mode,
            'moisture_mode': 'saturated' if self.saturated_radio.get_active() else 'sealed',
            'temperature_profile': self.profile_combo.get_active_text() or 'Custom'
        }
        
        # Add temperature profile data if using temperature profile mode
        if thermal_mode == 'temperature_profile' and self.current_temperature_profile:
            # Convert TemperatureProfile points to the format expected by bridge service
            profile_data = [(point.time_hours, point.temperature_celsius) 
                          for point in self.current_temperature_profile.points]
            conditions['temperature_profile_data'] = profile_data
            
        return conditions
    
    def _collect_time_calibration_settings(self) -> Dict[str, Any]:
        """Collect time calibration settings from UI."""
        settings = {}
        
        if self.aging_time_radio.get_active():
            settings['mode'] = 'knudsen'
            settings['time_conversion_factor'] = self.time_conversion_spin.get_value()
        elif self.aging_calorimetry_radio.get_active():
            settings['mode'] = 'calorimetry'
            settings['data_file'] = self.data_file_button.get_filename() or ""
        else:  # chemical shrinkage
            settings['mode'] = 'chemical_shrinkage'
            settings['data_file'] = self.data_file_button.get_filename() or ""
        
        return settings
    
    def _collect_advanced_settings(self) -> Dict[str, Any]:
        """Collect advanced settings from UI."""
        return {
            'random_seed': int(self.random_seed_spin.get_value()),
            'c3a_fraction': self.c3a_fraction_spin.get_value(),
            'csh_seeds': self.csh_seeds_spin.get_value(),
            'alpha_max': self.alpha_max_spin.get_value(),
            'e_act_cement': self.e_act_spin.get_value(),
            'e_act_pozzolan': self.e_act_pozz_spin.get_value(),
            'e_act_slag': self.e_act_slag_spin.get_value(),
            'burn_frequency': self.burn_freq_spin.get_value(),
            'setting_frequency': self.set_freq_spin.get_value(),
            'physical_frequency': self.phyd_freq_spin.get_value(),
            'movie_frequency': self.movie_freq_spin.get_value(),
            'save_interval_hours': self.save_interval_spin.get_value(),  # Output Settings
            'csh2_flag': 1 if self.csh2_flag_check.get_active() else 0,
            'ch_flag': 1 if self.ch_flag_check.get_active() else 0,
            'ph_active': 1 if self.ph_active_check.get_active() else 0
        }
    
    def _collect_database_modifications(self) -> Dict[str, Any]:
        """Collect database parameter modifications from UI."""
        if not hasattr(self, 'db_params_store'):
            return {}
        
        modifications = {}
        # Iterate through the TreeView store to find modified parameters
        def collect_row(model, path, iter, data):
            param_name = model.get_value(iter, 0)
            param_value = model.get_value(iter, 1)
            # You might want to track which ones were actually modified
            # For now, we'll collect all visible parameters
            modifications[param_name] = param_value
        
        self.db_params_store.foreach(collect_row, None)
        return modifications
    
    def _get_timestamp(self) -> str:
        """Get current timestamp for operation naming."""
        from datetime import datetime
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def _ensure_unique_operation_name(self, base_name: str) -> str:
        """Ensure operation name is unique by checking existing operations and folders."""
        # Sanitize the name (remove invalid characters for folder names)
        import re
        sanitized_name = re.sub(r'[<>:"/\\|?*]', '_', base_name)
        sanitized_name = sanitized_name.strip()
        
        # Check if the name already exists
        operations_dir = Path(__file__).parent.parent.parent.parent / "Operations"
        unique_name = sanitized_name
        counter = 1
        
        while True:
            # Check if folder exists
            if not (operations_dir / unique_name).exists():
                # Also check database for existing operations
                try:
                    with self.service_container.database_service.get_read_only_session() as session:
                        from app.models.operation import Operation
                        existing_op = session.query(Operation).filter_by(name=unique_name).first()
                        if not existing_op:
                            return unique_name
                except Exception:
                    # If database check fails, just use folder check
                    return unique_name
            
            # Name exists, try with counter
            unique_name = f"{sanitized_name}_{counter}"
            counter += 1
            
            # Safety limit to prevent infinite loop
            if counter > 1000:
                # Fall back to timestamp-based name
                return f"{sanitized_name}_{self._get_timestamp()}"
    
    def _on_simulation_progress(self, operation_name: str, progress_data) -> None:
        """Handle simulation progress updates."""
        if progress_data and operation_name == self.current_operation_name:
            # Store latest progress for UI updates
            self.latest_progress = progress_data
            
            # Handle both dict and HydrationProgress object formats
            if hasattr(progress_data, 'get'):  # Dictionary format
                cycle = progress_data.get('cycle', 0)
                time_hours = progress_data.get('time_hours', 0.0)
                doh = progress_data.get('degree_of_hydration', 0.0)
            else:  # HydrationProgress object format
                cycle = getattr(progress_data, 'cycle', 0)
                time_hours = getattr(progress_data, 'time_hours', 0.0)
                doh = getattr(progress_data, 'degree_of_hydration', 0.0)
            
            status_text = f"Cycle {cycle}, Time: {time_hours:.2f}h, DOH: {doh:.3f}"
            GLib.idle_add(self._update_status, status_text)
    
    def _on_pause_clicked(self, button) -> None:
        """Handle pause simulation button click."""
        # TODO: Implement pause functionality
        self._update_status("Pause functionality not yet implemented")
    
    def _on_stop_clicked(self, button) -> None:
        """Handle stop simulation button click."""
        try:
            if self.current_operation_name:
                executor = self.service_container.hydration_executor_service
                if executor.cancel_simulation(self.current_operation_name):
                    self.simulation_running = False
                    self.current_operation_name = None
                    self.simulation_start_time = None
                    self.latest_progress = None
                    self._update_simulation_controls(False)
                    self._stop_progress_updates()
                    self._update_status("Simulation stopped")
                    self.logger.info("Hydration simulation stopped")
                else:
                    self._update_status("Failed to stop simulation")
            else:
                self._update_status("No simulation running")
            
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
            total_cycles=2000,  # Default value since field removed
            time_step_hours=0.001,  # Default value since field removed
            max_simulation_time_hours=self.max_time_spin.get_value(),
            temperature_profile=self.current_temperature_profile or TemperatureProfile(
                "Default", "Default", [TemperaturePoint(0.0, 25.0)]
            ),
            aging_mode=aging_mode,
            convergence_tolerance=1e-6,  # Default value since disrealnew doesn't use convergence
            max_iterations_per_cycle=100,  # Default value since disrealnew doesn't use iterations
            save_interval_cycles=int(self.save_interval_spin.get_value()),
            save_intermediate_results=False  # Removed from UI
        )
    
    def _update_calculated_values(self) -> None:
        """Update calculated values display."""
        try:
            # Use default values since Total Cycles and Time Step fields were removed
            cycles = 2000  # Default total cycles
            time_step = 0.001  # Default time step
            
            total_time = cycles * time_step
            
            if total_time < 1:
                time_text = f"{total_time * 60:.1f} minutes"
            elif total_time < 24:
                time_text = f"{total_time:.1f} hours"
            else:
                days = total_time / 24
                time_text = f"{days:.1f} days"
            
            # calc_time_label removed from UI
            
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
        if not self.simulation_running or not self.current_operation_name:
            return True  # Continue timeout
        
        # Calculate elapsed time
        elapsed_seconds = 0
        if self.simulation_start_time:
            elapsed_seconds = time.time() - self.simulation_start_time
            elapsed_h = int(elapsed_seconds // 3600)
            elapsed_m = int((elapsed_seconds % 3600) // 60)
            elapsed_s = int(elapsed_seconds % 60)
            self.elapsed_time_label.set_text(f"{elapsed_h:02d}:{elapsed_m:02d}:{elapsed_s:02d}")
        
        # Use latest progress from HydrationExecutorService
        progress = self.latest_progress
        if progress:
            # Handle both dict and object formats
            if hasattr(progress, 'get'):  # Dictionary format
                cycle = progress.get('cycle', 0)
                max_cycles = progress.get('max_cycles', 2000)
                time_hours = progress.get('time_hours', 0.0)
                doh = progress.get('degree_of_hydration', 0.0)
                temperature = progress.get('temperature_celsius', 25.0)
                ph = progress.get('ph', 12.5)
                heat_cumulative = progress.get('heat_cumulative', 0.0)
                percent_complete = progress.get('percent_complete', 0.0)
            else:  # HydrationProgress object format
                cycle = getattr(progress, 'cycle', 0)
                max_cycles = getattr(progress, 'max_cycles', 2000)
                time_hours = getattr(progress, 'time_hours', 0.0)
                doh = getattr(progress, 'degree_of_hydration', 0.0)
                temperature = getattr(progress, 'temperature_celsius', 25.0)
                ph = getattr(progress, 'ph', 12.5)
                heat_cumulative = getattr(progress, 'heat_cumulative', 0.0)
                percent_complete = getattr(progress, 'percent_complete', 0.0)
            
            # Update progress bar - use time-based calculation for accuracy
            if percent_complete > 0:
                # Use the calculated percent_complete from HydrationExecutorService
                progress_fraction = percent_complete / 100.0
                self.overall_progress.set_fraction(progress_fraction)
                self.overall_progress.set_text(f"{percent_complete:.1f}%")
            else:
                # Fallback: calculate from time vs max_time (more accurate than cycles)
                max_time_hours = self.max_time_spin.get_value() if hasattr(self, 'max_time_spin') else 168.0
                if time_hours > 0 and max_time_hours > 0:
                    progress_percentage = min((time_hours / max_time_hours) * 100.0, 100.0)
                    progress_fraction = progress_percentage / 100.0
                    self.overall_progress.set_fraction(progress_fraction)
                    self.overall_progress.set_text(f"{progress_percentage:.1f}%")
                else:
                    self.overall_progress.set_fraction(0.0)
                    self.overall_progress.set_text("0.0%")
            
            # Update operation label
            self.operation_label.set_text(f"Running simulation - Cycle {cycle}/{max_cycles}")
            
            # Use remaining time from progress data (time-based, not cycle-based)
            try:
                # Debug: Print what we have in latest_progress
                if self.latest_progress:
                    print(f"DEBUG: latest_progress exists, estimated_time_remaining = {getattr(self.latest_progress, 'estimated_time_remaining', 'NOT FOUND')}")
                else:
                    print("DEBUG: latest_progress is None")
                
                if (self.latest_progress and 
                    hasattr(self.latest_progress, 'estimated_time_remaining') and 
                    self.latest_progress.estimated_time_remaining is not None):
                    
                    remaining_hours = float(self.latest_progress.estimated_time_remaining)
                    print(f"DEBUG: Using time-based remaining time: {remaining_hours} hours")
                    if remaining_hours > 0:
                        remaining_seconds_total = remaining_hours * 3600
                        remaining_h = int(remaining_seconds_total // 3600)
                        remaining_m = int((remaining_seconds_total % 3600) // 60)
                        remaining_s = int(remaining_seconds_total % 60)
                        print(f"DEBUG: Conversion: {remaining_hours}h -> {remaining_seconds_total:.1f}s -> {remaining_h:02d}:{remaining_m:02d}:{remaining_s:02d}")
                        self.remaining_time_label.set_text(f"{remaining_h:02d}:{remaining_m:02d}:{remaining_s:02d}")
                    else:
                        print(f"DEBUG: remaining_hours <= 0, showing 00:00:00")
                        self.remaining_time_label.set_text("00:00:00")
                else:
                    # Fallback to cycle-based calculation if progress data is not available
                    print(f"DEBUG: Using cycle-based fallback calculation")
                    if cycle > 0 and elapsed_seconds > 0:
                        cycles_per_second = cycle / elapsed_seconds
                        remaining_cycles = max_cycles - cycle
                        remaining_seconds = remaining_cycles / cycles_per_second if cycles_per_second > 0 else 0
                        print(f"DEBUG: Cycle-based: {remaining_cycles} remaining cycles, {cycles_per_second:.2f} cycles/s, {remaining_seconds:.0f} seconds remaining")
                        if remaining_seconds > 0:
                            remaining_h = int(remaining_seconds // 3600)
                            remaining_m = int((remaining_seconds % 3600) // 60)
                            remaining_s = int(remaining_seconds % 60)
                            self.remaining_time_label.set_text(f"{remaining_h:02d}:{remaining_m:02d}:{remaining_s:02d}")
                        else:
                            self.remaining_time_label.set_text("--:--:--")
                    else:
                        self.remaining_time_label.set_text("--:--:--")
            except Exception as e:
                # Log error and fallback to showing unknown time
                print(f"Error calculating remaining time: {e}")
                self.remaining_time_label.set_text("--:--:--")
            
            # Update rate using cycles if available
            if cycle > 0 and elapsed_seconds > 0:
                cycles_per_second = cycle / elapsed_seconds
                self.rate_label.set_text(f"{cycles_per_second:.2f} cycles/s")
            else:
                self.rate_label.set_text("-- cycles/s")
            
            # Update hydration metrics
            self.doh_value_label.set_text(f"{doh:.3f}")
            # Convert heat from kJ/kg to J/g (divide by 1000)
            heat_j_per_g = heat_cumulative / 1000.0 if heat_cumulative > 0 else 0.0
            self.heat_value_label.set_text(f"{heat_j_per_g:.1f}")
            # Chemical shrinkage - estimate based on degree of hydration
            # Typical value: 0.063 mL/g of cement at full hydration
            chemical_shrinkage = doh * 0.063 if doh > 0 else 0.0
            self.shrinkage_value_label.set_text(f"{chemical_shrinkage:.3f}")
        else:
            # No progress data yet, show initial state
            self.overall_progress.set_fraction(0.0)
            self.overall_progress.set_text("0.0%")
            self.operation_label.set_text("Starting simulation...")
            self.remaining_time_label.set_text("--:--:--")
            self.rate_label.set_text("-- cycles/s")
            
            # Reset hydration metrics to initial values
            self.doh_value_label.set_text("0.000")
            self.heat_value_label.set_text("0.0")
            self.shrinkage_value_label.set_text("0.000")
        
        # Check if simulation process is still running
        executor = self.service_container.hydration_executor_service
        if self.current_operation_name not in executor.active_simulations:
            # Simulation has finished
            self.simulation_running = False
            self._update_simulation_controls(False)
            self._stop_progress_updates()
            self._update_status("Simulation completed")
            
            # Final update with last known values
            if progress:
                self.operation_label.set_text("Simulation completed")
                self.remaining_time_label.set_text("00:00:00")
                self.rate_label.set_text("-- cycles/s")
            
            return False  # Stop timeout
        
        return True  # Continue timeout
    
    
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
    
    def _refresh_microstructure_list(self) -> None:
        """Refresh the list of available microstructures from Operations folder."""
        try:
            # Clear current list
            self.microstructure_combo.remove_all()
            
            # Add empty option
            self.microstructure_combo.append("", "-- Select Microstructure --")
            
            # Scan Operations folder for microstructures
            operations_dir = "./Operations"
            if not os.path.exists(operations_dir):
                self.logger.warning("Operations folder not found")
                self.microstructure_combo.set_active(0)
                return
            
            microstructures = []
            
            for operation_name in os.listdir(operations_dir):
                operation_path = os.path.join(operations_dir, operation_name)
                
                # Skip if not a directory
                if not os.path.isdir(operation_path):
                    continue
                
                # Check for required microstructure files
                img_file = os.path.join(operation_path, f"{operation_name}.img")
                pimg_file = os.path.join(operation_path, f"{operation_name}.pimg")
                
                if os.path.exists(img_file) and os.path.exists(pimg_file):
                    # Get file modification time for sorting
                    mod_time = os.path.getmtime(img_file)
                    microstructures.append((operation_name, mod_time))
            
            # Sort by modification time (newest first)
            microstructures.sort(key=lambda x: x[1], reverse=True)
            
            # Add to combo box
            for operation_name, _ in microstructures:
                self.microstructure_combo.append(operation_name, operation_name)
            
            self.microstructure_combo.set_active(0)  # Select the default empty option
            
            self.logger.info(f"Found {len(microstructures)} microstructures")
            
        except Exception as e:
            self.logger.error(f"Failed to refresh microstructure list: {e}")
    
    def _update_microstructure_info(self) -> None:
        """Update microstructure info display."""
        if not self.selected_microstructure:
            self.microstructure_info_label.set_text("No microstructure selected")
            return
        
        try:
            operation_name = self.selected_microstructure['operation_name']
            img_file = self.selected_microstructure['img_file']
            
            # Get file info
            if os.path.exists(img_file):
                stat = os.stat(img_file)
                file_size = stat.st_size
                mod_time = stat.st_mtime
                
                # Format size
                if file_size > 1024 * 1024:
                    size_str = f"{file_size / (1024 * 1024):.1f} MB"
                elif file_size > 1024:
                    size_str = f"{file_size / 1024:.1f} KB"
                else:
                    size_str = f"{file_size} bytes"
                
                # Format date
                import time
                date_str = time.strftime("%Y-%m-%d %H:%M", time.localtime(mod_time))
                
                info_text = f"Operation: {operation_name} | Size: {size_str} | Modified: {date_str}"
            else:
                info_text = f"Operation: {operation_name} | File not found"
            
            self.microstructure_info_label.set_text(info_text)
            
        except Exception as e:
            self.logger.error(f"Failed to update microstructure info: {e}")
            self.microstructure_info_label.set_text("Error reading microstructure info")
    
    def _update_status(self, message: str) -> None:
        """Update status message."""
        self.status_label.set_text(message)
        self.logger.debug(f"Status: {message}")
    
    def get_hydration_parameters(self) -> Optional[HydrationParameters]:
        """Get validated hydration parameters."""
        return self.current_params
    
    def get_selected_microstructure(self) -> Optional[Dict[str, str]]:
        """Get selected microstructure information."""
        return self.selected_microstructure
    
    def get_curing_conditions(self) -> Dict[str, Any]:
        """Get curing conditions from UI."""
        # Determine thermal mode
        if self.isothermal_radio.get_active():
            thermal_mode = 'isothermal'
        elif self.adiabatic_radio.get_active():
            thermal_mode = 'adiabatic'
        else:  # temperature_profile_radio.get_active()
            thermal_mode = 'temperature_profile'
            
        return {
            'initial_temperature_celsius': self.initial_temp_spin.get_value(),
            'thermal_mode': thermal_mode,
            'moisture_mode': 'saturated' if self.saturated_radio.get_active() else 'sealed'
        }
    
    def get_time_calibration_settings(self) -> Dict[str, Any]:
        """Get time calibration settings from UI."""
        # Get calibration mode
        if self.aging_time_radio.get_active():
            calibration_mode = 'knudsen_parabolic'
            calibration_value = self.time_conversion_spin.get_value()
        elif self.aging_calorimetry_radio.get_active():
            calibration_mode = 'calorimetry'
            calibration_value = self.data_file_button.get_filename()  # Path to calorimetry data file
        else:
            calibration_mode = 'chemical_shrinkage'
            calibration_value = self.data_file_button.get_filename()  # Path to shrinkage data file
        
        return {
            'calibration_mode': calibration_mode,
            'calibration_value': calibration_value,
            'time_conversion_factor': self.time_conversion_spin.get_value()
        }
    
    def get_advanced_settings(self) -> Dict[str, Any]:
        """Get advanced settings from UI."""
        return {
            # Simulation Control
            'random_seed': int(self.random_seed_spin.get_value()),
            'c3a_fraction': self.c3a_fraction_spin.get_value(),
            'csh_seeds': self.csh_seeds_spin.get_value(),
            'alpha_max': self.alpha_max_spin.get_value(),
            
            # Activation Energies
            'e_act_cement': self.e_act_spin.get_value(),
            'e_act_pozzolan': self.e_act_pozz_spin.get_value(),
            'e_act_slag': self.e_act_slag_spin.get_value(),
            
            # Output Frequencies
            'burn_frequency': self.burn_freq_spin.get_value(),
            'setting_frequency': self.set_freq_spin.get_value(),
            'physical_frequency': self.phyd_freq_spin.get_value(),
            'movie_frequency': self.movie_freq_spin.get_value(),
            
            # Phase Control
            'csh2_flag': 1 if self.csh2_flag_check.get_active() else 0,
            'ch_flag': 1 if self.ch_flag_check.get_active() else 0,
            'ph_active': 1 if self.ph_active_check.get_active() else 0
        }
    
    def set_curing_conditions(self, conditions: Dict[str, Any]) -> None:
        """Set curing conditions in UI."""
        try:
            if 'initial_temperature_celsius' in conditions:
                self.initial_temp_spin.set_value(conditions['initial_temperature_celsius'])
            
            if 'thermal_mode' in conditions:
                if conditions['thermal_mode'] == 'isothermal':
                    self.isothermal_radio.set_active(True)
                elif conditions['thermal_mode'] == 'adiabatic':
                    self.adiabatic_radio.set_active(True)
                else:  # temperature_profile
                    self.temperature_profile_radio.set_active(True)
            
            if 'moisture_mode' in conditions:
                if conditions['moisture_mode'] == 'saturated':
                    self.saturated_radio.set_active(True)
                else:
                    self.sealed_radio.set_active(True)
            
            self.logger.info("Curing conditions loaded")
            
        except Exception as e:
            self.logger.error(f"Failed to set curing conditions: {e}")
            self._update_status(f"Error loading curing conditions: {e}")
    
    def set_hydration_parameters(self, params: HydrationParameters) -> None:
        """Set hydration parameters in UI."""
        try:
            # Note: Total cycles and timestep fields were removed from UI
            self.max_time_spin.set_value(params.max_simulation_time_hours)
            self.save_interval_spin.set_value(params.save_interval_cycles)
            # save_intermediate_check removed from UI
            
            # Set aging mode
            if params.aging_mode == AgingMode.TIME:
                self.aging_time_radio.set_active(True)
            elif params.aging_mode == AgingMode.CALORIMETRY:
                self.aging_calorimetry_radio.set_active(True)
            else:
                self.aging_shrinkage_radio.set_active(True)
            
            # Set temperature profile
            self.current_temperature_profile = params.temperature_profile
            self.current_profile = self.current_temperature_profile
            self._update_temperature_plot()
            self._update_profile_summary()
            
            self._clear_validation()
            self.logger.info("Hydration parameters loaded")
            
        except Exception as e:
            self.logger.error(f"Failed to set hydration parameters: {e}")
            self._update_status(f"Error loading parameters: {e}")
    
    def _load_database_parameters(self) -> None:
        """Load all parameters from database and populate the tree view."""
        try:
            from app.services.hydration_parameters_service import HydrationParametersService
            
            # Get hydration parameters service
            hydration_service = HydrationParametersService(self.service_container.database_service)
            
            # Load default parameter set
            params = hydration_service.get_parameter_set("portland_cement_standard")
            if not params or not params.parameters:
                self._update_status("No database parameters found")
                return
            
            # Clear existing data
            self.params_store.clear()
            self.modified_params.clear()
            
            # Populate tree view
            for param_name, param_value in params.parameters.items():
                # Determine parameter type
                param_type = "string"
                if isinstance(param_value, (int, float)):
                    if isinstance(param_value, int):
                        param_type = "integer" 
                    else:
                        param_type = "float"
                elif isinstance(param_value, bool):
                    param_type = "boolean"
                
                # Add to tree store
                self.params_store.append([param_name, str(param_value), param_type])
            
            self.logger.info(f"Loaded {len(params.parameters)} parameters from database")
            
        except Exception as e:
            self.logger.error(f"Failed to load database parameters: {e}")
            self._update_status(f"Error loading database parameters: {e}")
    
    def _on_param_search_changed(self, search_entry) -> None:
        """Handle parameter search/filter."""
        search_text = search_entry.get_text().lower()
        
        # Create filter model
        filter_model = self.params_store.filter_new()
        filter_model.set_visible_func(self._param_filter_func, search_text)
        
        # Update tree view with filtered model
        self.params_tree.set_model(filter_model)
    
    def _param_filter_func(self, model, iter, search_text) -> bool:
        """Filter function for parameter search."""
        if not search_text:
            return True
        
        param_name = model[iter][0].lower()
        param_value = model[iter][1].lower()
        
        return search_text in param_name or search_text in param_value
    
    def _on_param_value_edited(self, renderer, path, new_text) -> None:
        """Handle parameter value editing."""
        try:
            # Get the current model (might be filtered)
            current_model = self.params_tree.get_model()
            iter = current_model.get_iter(path)
            
            param_name = current_model[iter][0]
            param_type = current_model[iter][2]
            old_value = current_model[iter][1]
            
            # Validate new value based on type
            validated_value = self._validate_param_value(new_text, param_type)
            if validated_value is None:
                self._update_status(f"Invalid {param_type} value: {new_text}")
                return
            
            # Update model
            current_model[iter][1] = str(validated_value)
            
            # Track modification
            self.modified_params[param_name] = validated_value
            
            self.logger.info(f"Parameter {param_name} changed from {old_value} to {validated_value}")
            self._update_status(f"Modified parameter: {param_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to edit parameter: {e}")
            self._update_status(f"Error editing parameter: {e}")
    
    def _validate_param_value(self, value_str: str, param_type: str):
        """Validate parameter value based on its type."""
        try:
            if param_type == "integer":
                return int(value_str)
            elif param_type == "float":
                return float(value_str)
            elif param_type == "boolean":
                if value_str.lower() in ['true', '1', 'yes', 'on']:
                    return True
                elif value_str.lower() in ['false', '0', 'no', 'off']:
                    return False
                else:
                    return None
            else:  # string
                return value_str
        except ValueError:
            return None
    
    def _on_refresh_params_clicked(self, button) -> None:
        """Handle refresh parameters button click."""
        self._load_database_parameters()
        self._update_status("Parameters refreshed from database")
    
    def _on_export_params_clicked(self, button) -> None:
        """Handle export parameters to CSV."""
        try:
            dialog = Gtk.FileChooserDialog(
                title="Export Parameters to CSV",
                parent=self.get_toplevel(),
                action=Gtk.FileChooserAction.SAVE
            )
            dialog.add_buttons(
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_SAVE, Gtk.ResponseType.OK
            )
            
            # Add CSV filter
            filter_csv = Gtk.FileFilter()
            filter_csv.set_name("CSV files")
            filter_csv.add_pattern("*.csv")
            dialog.add_filter(filter_csv)
            
            # Set default filename
            dialog.set_current_name("hydration_parameters.csv")
            
            response = dialog.run()
            if response == Gtk.ResponseType.OK:
                filename = dialog.get_filename()
                
                # Export all parameters to CSV
                with open(filename, 'w', newline='') as csvfile:
                    import csv
                    writer = csv.writer(csvfile)
                    writer.writerow(['Parameter Name', 'Value', 'Type'])  # Header
                    
                    # Iterate through all parameters in store
                    def export_row(model, path, iter, writer):
                        param_name = model[iter][0]
                        param_value = model[iter][1]
                        param_type = model[iter][2]
                        writer.writerow([param_name, param_value, param_type])
                        return False
                    
                    self.params_store.foreach(export_row, writer)
                
                self._update_status(f"Parameters exported to: {filename}")
                self.logger.info(f"Exported parameters to {filename}")
            
            dialog.destroy()
            
        except Exception as e:
            self.logger.error(f"Failed to export parameters: {e}")
            self._update_status(f"Error exporting parameters: {e}")
    
    def _on_import_params_clicked(self, button) -> None:
        """Handle import parameters from CSV."""
        try:
            dialog = Gtk.FileChooserDialog(
                title="Import Parameters from CSV", 
                parent=self.get_toplevel(),
                action=Gtk.FileChooserAction.OPEN
            )
            dialog.add_buttons(
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OPEN, Gtk.ResponseType.OK
            )
            
            # Add CSV filter
            filter_csv = Gtk.FileFilter()
            filter_csv.set_name("CSV files")
            filter_csv.add_pattern("*.csv")
            dialog.add_filter(filter_csv)
            
            response = dialog.run()
            if response == Gtk.ResponseType.OK:
                filename = dialog.get_filename()
                
                # Import parameters from CSV
                import csv
                imported_count = 0
                
                with open(filename, 'r') as csvfile:
                    reader = csv.reader(csvfile)
                    header = next(reader, None)  # Skip header
                    
                    for row in reader:
                        if len(row) >= 2:
                            param_name = row[0]
                            param_value = row[1]
                            param_type = row[2] if len(row) > 2 else "string"
                            
                            # Validate and convert value
                            validated_value = self._validate_param_value(param_value, param_type)
                            if validated_value is not None:
                                # Update parameter in tree store
                                def update_param(model, path, iter, data):
                                    param_name, validated_value = data
                                    if model[iter][0] == param_name:
                                        model[iter][1] = str(validated_value)
                                        self.modified_params[param_name] = validated_value
                                        return True
                                    return False
                                
                                self.params_store.foreach(update_param, (param_name, validated_value))
                                imported_count += 1
                
                self._update_status(f"Imported {imported_count} parameters from: {filename}")
                self.logger.info(f"Imported {imported_count} parameters from {filename}")
            
            dialog.destroy()
            
        except Exception as e:
            self.logger.error(f"Failed to import parameters: {e}")
            self._update_status(f"Error importing parameters: {e}")
    
    def _on_reset_params_clicked(self, button) -> None:
        """Handle reset parameters to defaults."""
        try:
            # Confirmation dialog
            dialog = Gtk.MessageDialog(
                parent=self.get_toplevel(),
                flags=0,
                message_type=Gtk.MessageType.QUESTION,
                buttons=Gtk.ButtonsType.YES_NO,
                text="Reset all parameters to defaults?"
            )
            dialog.format_secondary_text(
                "This will discard all parameter modifications and reload defaults from the database."
            )
            
            response = dialog.run()
            dialog.destroy()
            
            if response == Gtk.ResponseType.YES:
                self._load_database_parameters()
                self._update_status("Parameters reset to defaults")
                
        except Exception as e:
            self.logger.error(f"Failed to reset parameters: {e}")
            self._update_status(f"Error resetting parameters: {e}")
    
    def get_database_parameter_modifications(self) -> Dict[str, Any]:
        """Get any modifications made to database parameters."""
        return self.modified_params.copy()
    
    def _on_save_params_clicked(self, button) -> None:
        """Handle save parameters button click."""
        try:
            self._show_save_parameters_dialog()
        except Exception as e:
            self.logger.error(f"Error saving hydration parameters: {e}")
            dialog = Gtk.MessageDialog(
                self.get_toplevel(),
                Gtk.DialogFlags.MODAL,
                Gtk.MessageType.ERROR,
                Gtk.ButtonsType.OK,
                f"Failed to save parameters: {e}"
            )
            dialog.run()
            dialog.destroy()
    
    def _on_load_params_clicked(self, button) -> None:
        """Handle load parameters button click."""
        try:
            self._show_load_parameters_dialog()
        except Exception as e:
            self.logger.error(f"Error loading hydration parameters: {e}")
            dialog = Gtk.MessageDialog(
                self.get_toplevel(),
                Gtk.DialogFlags.MODAL,
                Gtk.MessageType.ERROR,
                Gtk.ButtonsType.OK,
                f"Failed to load parameters: {e}"
            )
            dialog.run()
            dialog.destroy()
    
    def _extract_current_parameters(self) -> Dict[str, Any]:
        """Extract current hydration parameters from UI controls."""
        # Core simulation parameters
        max_time_hours = self.max_time_spin.get_value()
        
        # Curing conditions
        curing_conditions = {
            "temperature_profile": {
                "name": self.current_profile.name if self.current_profile else "constant_25c",
                "description": self.current_profile.description if self.current_profile else "Constant 25°C",
                "points": [{"time_hours": p.time_hours, "temperature_celsius": p.temperature_celsius} 
                          for p in (self.current_profile.points if self.current_profile else [])]
            },
        }
        
        # Time calibration settings
        time_calibration = {
            "time_conversion_factor": self.time_conversion_spin.get_value(),
        }
        
        # Advanced settings
        advanced_settings = {
            "c3a_fraction": self.c3a_fraction_spin.get_value(),
            "ettringite_formation": self.ettringite_check.get_active(),
            "csh2_formation": self.csh2_flag_check.get_active(),
            "ch_formation": self.ch_flag_check.get_active(),
            "ph_computation": self.ph_active_check.get_active(),
            "random_seed": self.random_seed_spin.get_value_as_int()
        }
        
        # Database modifications (custom parameter overrides)
        db_modifications = self.get_database_parameter_modifications()
        
        return {
            "max_time_hours": max_time_hours,
            "curing_conditions": curing_conditions,
            "time_calibration": time_calibration,
            "advanced_settings": advanced_settings,
            "db_modifications": db_modifications
        }
    
    def _show_save_parameters_dialog(self) -> None:
        """Show dialog to save current hydration parameters."""
        dialog = Gtk.Dialog(
            title="Save Hydration Parameters",
            parent=self.get_toplevel(),
            flags=Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_SAVE, Gtk.ResponseType.OK
        )
        dialog.set_default_size(400, 300)
        
        content_area = dialog.get_content_area()
        content_area.set_spacing(10)
        content_area.set_margin_left(20)
        content_area.set_margin_right(20)
        content_area.set_margin_top(20)
        content_area.set_margin_bottom(20)
        
        # Name entry
        name_label = Gtk.Label("Parameter Set Name:")
        name_label.set_halign(Gtk.Align.START)
        content_area.pack_start(name_label, False, False, 0)
        
        name_entry = Gtk.Entry()
        name_entry.set_placeholder_text("Enter a name for this parameter set")
        content_area.pack_start(name_entry, False, False, 0)
        
        # Description entry
        desc_label = Gtk.Label("Description (optional):")
        desc_label.set_halign(Gtk.Align.START)
        content_area.pack_start(desc_label, False, False, 0)
        
        desc_buffer = Gtk.TextBuffer()
        desc_view = Gtk.TextView()
        desc_view.set_buffer(desc_buffer)
        desc_view.set_wrap_mode(Gtk.WrapMode.WORD)
        desc_scrolled = Gtk.ScrolledWindow()
        desc_scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        desc_scrolled.add(desc_view)
        desc_scrolled.set_size_request(-1, 80)
        content_area.pack_start(desc_scrolled, False, False, 0)
        
        # Notes entry
        notes_label = Gtk.Label("Notes (optional):")
        notes_label.set_halign(Gtk.Align.START)
        content_area.pack_start(notes_label, False, False, 0)
        
        notes_buffer = Gtk.TextBuffer()
        notes_view = Gtk.TextView()
        notes_view.set_buffer(notes_buffer)
        notes_view.set_wrap_mode(Gtk.WrapMode.WORD)
        notes_scrolled = Gtk.ScrolledWindow()
        notes_scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        notes_scrolled.add(notes_view)
        notes_scrolled.set_size_request(-1, 60)
        content_area.pack_start(notes_scrolled, False, False, 0)
        
        # Template checkbox
        template_check = Gtk.CheckButton("Save as template")
        template_check.set_tooltip_text("Templates appear at the top of the parameter list for easy access")
        content_area.pack_start(template_check, False, False, 0)
        
        dialog.show_all()
        
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            name = name_entry.get_text().strip()
            if not name:
                error_dialog = Gtk.MessageDialog(
                    dialog,
                    Gtk.DialogFlags.MODAL,
                    Gtk.MessageType.ERROR,
                    Gtk.ButtonsType.OK,
                    "Please enter a name for the parameter set."
                )
                error_dialog.run()
                error_dialog.destroy()
                dialog.destroy()
                return
            
            description = desc_buffer.get_text(desc_buffer.get_start_iter(), desc_buffer.get_end_iter(), False)
            notes = notes_buffer.get_text(notes_buffer.get_start_iter(), notes_buffer.get_end_iter(), False)
            is_template = template_check.get_active()
            
            dialog.destroy()
            
            # Save the parameters
            self._save_current_parameters(name, description, notes, is_template)
        else:
            dialog.destroy()
    
    def _save_current_parameters(self, name: str, description: str, notes: str, is_template: bool) -> None:
        """Save current hydration parameters to database."""
        try:
            # Get service container and parameter set service
            container = get_service_container()
            param_service = HydrationParameterSetService(container.database_service)
            
            # Extract current parameters
            params = self._extract_current_parameters()
            
            # Create parameter set data
            param_set_data = HydrationParameterSetCreate(
                name=name,
                description=description if description else None,
                max_time_hours=params["max_time_hours"],
                curing_conditions=params["curing_conditions"],
                time_calibration=params["time_calibration"],
                advanced_settings=params["advanced_settings"],
                db_modifications=params["db_modifications"],
                notes=notes if notes else None,
                is_template=is_template
            )
            
            # Save to database
            saved_params = param_service.create(param_set_data)
            
            # Show success message
            success_dialog = Gtk.MessageDialog(
                self.get_toplevel(),
                Gtk.DialogFlags.MODAL,
                Gtk.MessageType.INFO,
                Gtk.ButtonsType.OK,
                f"Hydration parameters '{name}' saved successfully!"
            )
            success_dialog.run()
            success_dialog.destroy()
            
            self.logger.info(f"Saved hydration parameter set: {name} (ID: {saved_params.id})")
            
        except Exception as e:
            self.logger.error(f"Failed to save hydration parameters: {e}")
            error_dialog = Gtk.MessageDialog(
                self.get_toplevel(),
                Gtk.DialogFlags.MODAL,
                Gtk.MessageType.ERROR,
                Gtk.ButtonsType.OK,
                f"Failed to save parameters: {e}"
            )
            error_dialog.run()
            error_dialog.destroy()
    
    def _show_load_parameters_dialog(self) -> None:
        """Show dialog to load saved hydration operations."""
        try:
            # Get service container and saved hydration service
            from app.services.saved_hydration_service import SavedHydrationOperationService
            saved_hydration_service = SavedHydrationOperationService(self.service_container.database_service)

            # Get all saved hydration operations
            saved_hydrations = saved_hydration_service.get_all()

            if not saved_hydrations:
                info_dialog = Gtk.MessageDialog(
                    self.get_toplevel(),
                    Gtk.DialogFlags.MODAL,
                    Gtk.MessageType.INFO,
                    Gtk.ButtonsType.OK,
                    "No saved hydration operations found. Complete a hydration operation first to enable loading."
                )
                info_dialog.run()
                info_dialog.destroy()
                return

            dialog = Gtk.Dialog(
                title="Load Hydration Operation",
                parent=self.get_toplevel(),
                flags=Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT
            )
            dialog.add_buttons(
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OPEN, Gtk.ResponseType.OK
            )
            dialog.set_default_size(700, 450)

            content_area = dialog.get_content_area()
            content_area.set_spacing(10)
            content_area.set_margin_left(20)
            content_area.set_margin_right(20)
            content_area.set_margin_top(20)
            content_area.set_margin_bottom(20)

            # Create list view
            liststore = Gtk.ListStore(int, str, str, str, str, bool)  # id, name, description, source_microstructure, created_at, is_template

            for saved_hydration in saved_hydrations:
                liststore.append([
                    saved_hydration.id,
                    saved_hydration.name,
                    saved_hydration.description or "",
                    saved_hydration.source_microstructure_name or "Unknown",
                    saved_hydration.created_at.strftime("%Y-%m-%d %H:%M"),
                    saved_hydration.is_template
                ])
            
            tree_view = Gtk.TreeView(model=liststore)
            tree_view.set_headers_visible(True)

            # Name column
            name_renderer = Gtk.CellRendererText()
            name_column = Gtk.TreeViewColumn("Name", name_renderer, text=1)
            name_column.set_expand(True)
            tree_view.append_column(name_column)

            # Description column
            desc_renderer = Gtk.CellRendererText()
            desc_column = Gtk.TreeViewColumn("Description", desc_renderer, text=2)
            desc_column.set_expand(True)
            tree_view.append_column(desc_column)

            # Source Microstructure column
            source_renderer = Gtk.CellRendererText()
            source_column = Gtk.TreeViewColumn("Source Microstructure", source_renderer, text=3)
            source_column.set_expand(True)
            tree_view.append_column(source_column)

            # Created column
            created_renderer = Gtk.CellRendererText()
            created_column = Gtk.TreeViewColumn("Created", created_renderer, text=4)
            tree_view.append_column(created_column)

            # Template column
            template_renderer = Gtk.CellRendererToggle()
            template_column = Gtk.TreeViewColumn("Template", template_renderer, active=5)
            tree_view.append_column(template_column)
            
            # Scrolled window
            scrolled = Gtk.ScrolledWindow()
            scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
            scrolled.add(tree_view)
            content_area.pack_start(scrolled, True, True, 0)
            
            dialog.show_all()
            
            response = dialog.run()
            
            if response == Gtk.ResponseType.OK:
                selection = tree_view.get_selection()
                model, tree_iter = selection.get_selected()
                
                if tree_iter is not None:
                    saved_hydration_id = model[tree_iter][0]
                    dialog.destroy()

                    # Load the selected saved hydration operation
                    self._load_saved_hydration_operation(saved_hydration_id)

                    # Show success message like Mix Design panel does
                    success_dialog = Gtk.MessageDialog(
                        self.get_toplevel(),
                        Gtk.DialogFlags.MODAL,
                        Gtk.MessageType.INFO,
                        Gtk.ButtonsType.OK,
                        f"Hydration operation loaded successfully!"
                    )
                    success_dialog.run()
                    success_dialog.destroy()
                else:
                    error_dialog = Gtk.MessageDialog(
                        dialog,
                        Gtk.DialogFlags.MODAL,
                        Gtk.MessageType.ERROR,
                        Gtk.ButtonsType.OK,
                        "Please select a parameter set to load."
                    )
                    error_dialog.run()
                    error_dialog.destroy()
                    dialog.destroy()
            else:
                dialog.destroy()
                
        except Exception as e:
            self.logger.error(f"Failed to show load parameters dialog: {e}")
            error_dialog = Gtk.MessageDialog(
                self.get_toplevel(),
                Gtk.DialogFlags.MODAL,
                Gtk.MessageType.ERROR,
                Gtk.ButtonsType.OK,
                f"Failed to load parameters: {e}"
            )
            error_dialog.run()
            error_dialog.destroy()
    
    def _load_parameter_set(self, param_set_id: int) -> None:
        """Load a specific parameter set and restore UI controls."""
        try:
            # Get service container and parameter set service
            container = get_service_container()
            param_service = HydrationParameterSetService(container.database_service)
            
            # Get parameter set from database
            param_set = param_service.get_by_id(param_set_id)
            if not param_set:
                raise ValueError(f"Parameter set with ID {param_set_id} not found")
            
            # Restore UI controls from saved parameters
            self._restore_parameters_to_ui(param_set)
            
            # Show success message
            success_dialog = Gtk.MessageDialog(
                self.get_toplevel(),
                Gtk.DialogFlags.MODAL,
                Gtk.MessageType.INFO,
                Gtk.ButtonsType.OK,
                f"Hydration parameters '{param_set.name}' loaded successfully!"
            )
            success_dialog.run()
            success_dialog.destroy()
            
            self.logger.info(f"Loaded hydration parameter set: {param_set.name} (ID: {param_set.id})")
            
        except Exception as e:
            self.logger.error(f"Failed to load parameter set {param_set_id}: {e}")
            error_dialog = Gtk.MessageDialog(
                self.get_toplevel(),
                Gtk.DialogFlags.MODAL,
                Gtk.MessageType.ERROR,
                Gtk.ButtonsType.OK,
                f"Failed to load parameters: {e}"
            )
            error_dialog.run()
            error_dialog.destroy()
    
    def _restore_parameters_to_ui(self, param_set) -> None:
        """Restore hydration parameters from database to UI controls."""
        try:
            # Core simulation parameters
            self.max_time_spin.set_value(param_set.max_time_hours)
            
            # Restore curing conditions
            if param_set.curing_conditions:
                curing = param_set.curing_conditions
                
                
                # Temperature profile
                if "temperature_profile" in curing:
                    profile_data = curing["temperature_profile"]
                    points = []
                    for point_data in profile_data.get("points", []):
                        points.append(TemperaturePoint(
                            point_data["time_hours"],
                            point_data["temperature_celsius"]
                        ))
                    
                    self.current_profile = TemperatureProfile(
                        name=profile_data.get("name", "Custom"),
                        description=profile_data.get("description", "Restored profile"),
                        points=points
                    )
                    self._update_profile_display()
            
            # Restore time calibration
            if param_set.time_calibration:
                time_cal = param_set.time_calibration
                if "time_conversion_factor" in time_cal:
                    self.time_conversion_spin.set_value(time_cal["time_conversion_factor"])
            
            # Restore advanced settings
            if param_set.advanced_settings:
                advanced = param_set.advanced_settings
                if "c3a_fraction" in advanced:
                    self.c3a_fraction_spin.set_value(advanced["c3a_fraction"])
                if "ettringite_formation" in advanced:
                    self.ettringite_check.set_active(advanced["ettringite_formation"])
                if "csh2_formation" in advanced:
                    self.csh2_flag_check.set_active(advanced["csh2_formation"])
                if "ch_formation" in advanced:
                    self.ch_flag_check.set_active(advanced["ch_formation"])
                if "ph_computation" in advanced:
                    self.ph_active_check.set_active(advanced["ph_computation"])
                if "random_seed" in advanced:
                    self.random_seed_spin.set_value(advanced["random_seed"])
            
            # Restore database modifications
            if param_set.db_modifications:
                self.modified_params.clear()
                self.modified_params.update(param_set.db_modifications)
                self._refresh_database_parameters_display()
            
            self.logger.info(f"Successfully restored parameters from: {param_set.name}")
            
        except Exception as e:
            self.logger.error(f"Failed to restore parameters to UI: {e}")
            raise
    
    def cleanup(self) -> None:
        """Cleanup resources when panel is destroyed."""
        self._stop_progress_updates()
        self.hydration_service.remove_progress_callback(self._on_simulation_progress)
    
    # Phase 3: Clean Naming and Lineage Methods
    
    def _capture_hydration_ui_parameters(self, operation_name: str, selected_microstructure: Dict[str, Any],
                                       curing_conditions: Dict[str, Any], time_calibration: Dict[str, Any],
                                       advanced_settings: Dict[str, Any], db_modifications: Dict[str, Any]) -> Dict[str, Any]:
        """Capture all hydration UI parameters for storage and reproducibility."""
        from datetime import datetime
        
        # Core operation info
        ui_params = {
            'operation_name': operation_name,
            'operation_type': 'hydration',
            'source_microstructure': selected_microstructure,
            'captured_at': datetime.utcnow().isoformat(),
        }
        
        # Simulation parameters
        ui_params.update({
            'max_simulation_time_hours': self.max_time_spin.get_value(),
            'target_degree_of_hydration': 0.8,  # Default value
            'random_seed': advanced_settings.get('random_seed', -1),
        })
        
        # Curing conditions
        ui_params['curing_conditions'] = curing_conditions.copy()
        
        # Time calibration
        ui_params['time_calibration'] = time_calibration.copy()
        
        # Advanced settings
        ui_params['advanced_settings'] = advanced_settings.copy()
        
        # Database parameter modifications
        ui_params['database_modifications'] = db_modifications.copy()
        
        # Temperature profile (if using one)
        if hasattr(self, 'current_profile') and self.current_profile:
            ui_params['temperature_profile'] = {
                'name': self.current_profile.name,
                'description': self.current_profile.description,
                'points': [{'time_hours': p.time_hours, 'temperature_celsius': p.temperature_celsius} 
                          for p in self.current_profile.points]
            }
        
        return ui_params
    
    def _find_microstructure_operation_id(self, microstructure_name: str) -> Optional[int]:
        """Find the database ID of the parent microstructure operation."""
        try:
            from app.models.operation import Operation, OperationType
            
            with self.service_container.database_service.get_session() as session:
                # Look for microstructure operation with matching name
                # Fix: Check for both possible operation types
                parent_op = session.query(Operation).filter(
                    Operation.name == microstructure_name,
                    Operation.operation_type.in_(['MICROSTRUCTURE', 'microstructure_generation'])
                ).first()
                
                if parent_op:
                    self.logger.info(f"✅ Found parent microstructure operation: {microstructure_name} (ID: {parent_op.id}, Type: {parent_op.operation_type})")
                    return parent_op.id
                else:
                    self.logger.error(f"❌ Parent microstructure operation not found: {microstructure_name}")
                    # Log what operations we do have for debugging
                    all_ops = session.query(Operation).filter(Operation.name == microstructure_name).all()
                    if all_ops:
                        for op in all_ops:
                            self.logger.info(f"   Found operation {microstructure_name} with type: {op.operation_type}")
                    return None
        except Exception as e:
            self.logger.error(f"Error finding parent microstructure operation: {e}")
            return None
    
    def _create_hydration_operation(self, operation_name: str, ui_parameters: Dict[str, Any], 
                                  parent_operation_id: Optional[int]) -> 'Operation':
        """Create hydration operation in database with UI parameters and lineage."""
        try:
            from app.models.operation import Operation, OperationType, OperationStatus
            import json
            
            with self.service_container.database_service.get_session() as session:
                # Create the general operation record
                operation = Operation(
                    name=operation_name,
                    operation_type=OperationType.HYDRATION.value,
                    status=OperationStatus.QUEUED.value,
                    stored_ui_parameters=json.dumps(ui_parameters),  # Convert to JSON string
                    parent_operation_id=parent_operation_id  # Phase 3: Lineage tracking
                )
                
                session.add(operation)
                session.commit()
                
                self.logger.info(f"✅ Created hydration operation: {operation_name} (ID: {operation.id})")
                if parent_operation_id:
                    self.logger.info(f"✅ Linked to parent microstructure operation ID: {parent_operation_id}")
                else:
                    self.logger.warning(f"⚠️  No parent operation linkage for {operation_name}")
                
                return operation
                
        except Exception as e:
            self.logger.error(f"Error creating hydration operation: {e}")
            raise
    
    def _register_hydration_with_operations_panel(self, operation_name: str, executor) -> None:
        """Register the hydration process with operations panel for pause/resume support."""
        try:
            # Get the operations panel from main window
            operations_panel = getattr(self.main_window, 'operations_panel', None)
            if not operations_panel:
                self.logger.error("PAUSE DEBUG: Operations panel not available for process registration")
                return
            
            self.logger.info(f"PAUSE DEBUG: Starting registration for {operation_name}")
            
            # Get the active simulation info from executor
            if operation_name not in executor.active_simulations:
                self.logger.error(f"PAUSE DEBUG: No active simulation found for {operation_name}")
                return
                
            simulation_info = executor.active_simulations[operation_name]
            process = simulation_info.get('process')
            operation_dir = simulation_info.get('operation_dir')
            
            if not process:
                self.logger.error(f"PAUSE DEBUG: No process found for {operation_name}")
                return
            
            self.logger.info(f"PAUSE DEBUG: Found process with PID {process.pid} for {operation_name}")
            
            # Force operations panel to refresh from database to get new operation
            self.logger.info(f"PAUSE DEBUG: Forcing operations panel to reload from database")
            operations_panel._safe_load_operations_from_database()
            
            # Find the operation in the operations panel by name
            for op_id, operation in operations_panel.operations.items():
                if operation.name == operation_name:
                    # Update the operation with process information for pause/resume support
                    self.logger.info(f"PAUSE DEBUG: Found matching operation! Updating with process info...")
                    operation.process = process
                    operation.pid = process.pid
                    operation.working_directory = str(operation_dir) if operation_dir else None
                    
                    self.logger.info(f"PAUSE DEBUG: Successfully registered hydration process (PID: {process.pid}) with operations panel for {operation_name}")
                    return
            
            self.logger.error(f"PAUSE DEBUG: Operation {operation_name} not found in operations panel!")
            self.logger.error(f"PAUSE DEBUG: Available operations: {[op.name for op in operations_panel.operations.values()]}")
                
        except Exception as e:
            self.logger.error(f"PAUSE DEBUG: Error registering hydration process: {e}")
            import traceback
            self.logger.error(f"PAUSE DEBUG: Traceback: {traceback.format_exc()}")
    
    def _retry_registration(self, operation_name: str, executor, attempt: int = 0) -> bool:
        """Retry registration with backoff. Returns False to stop GLib timeout."""
        MAX_ATTEMPTS = 10
        
        if attempt >= MAX_ATTEMPTS:
            self.logger.error(f"PAUSE DEBUG: Registration failed after {MAX_ATTEMPTS} attempts for {operation_name}")
            return False  # Stop retrying
        
        try:
            # Try the registration
            self._register_hydration_with_operations_panel(operation_name, executor)
            
            # Check if it worked by looking for the process in operations panel
            operations_panel = getattr(self.main_window, 'operations_panel', None)
            if operations_panel:
                for op_id, operation in operations_panel.operations.items():
                    if operation.name == operation_name and operation.process is not None:
                        self.logger.info(f"PAUSE DEBUG: Registration successful on attempt {attempt + 1}")
                        return False  # Stop retrying
            
            # Registration didn't work, try again
            self.logger.info(f"PAUSE DEBUG: Registration attempt {attempt + 1}/{MAX_ATTEMPTS} failed, will retry...")
            from gi.repository import GLib
            GLib.timeout_add(1000, self._retry_registration, operation_name, executor, attempt + 1)
            return False  # Stop this timeout, next one is scheduled
            
        except Exception as e:
            self.logger.error(f"PAUSE DEBUG: Registration attempt {attempt + 1} error: {e}")
            from gi.repository import GLib
            GLib.timeout_add(1000, self._retry_registration, operation_name, executor, attempt + 1)
            return False  # Stop this timeout, next one is scheduled
    
    def _validate_parameter_completeness(self, curing_conditions: dict, time_calibration_settings: dict,
                                       advanced_settings: dict, db_param_modifications: dict) -> None:
        """Validate that all required parameters are present and valid for hydration simulation.
        
        This performs in-memory validation without creating files or folders.
        """
        # Validate curing conditions
        if not curing_conditions:
            raise ValueError("Curing conditions are required")
        
        required_curing_keys = ['initial_temperature_celsius', 'thermal_mode', 'moisture_mode']
        for key in required_curing_keys:
            if key not in curing_conditions:
                raise ValueError(f"Missing required curing condition: {key}")
        
        # Validate temperature range
        temp = curing_conditions.get('initial_temperature_celsius', 0)
        if not (0 <= temp <= 100):
            raise ValueError(f"Temperature must be between 0-100°C, got {temp}")
        
        # Validate time calibration settings
        if time_calibration_settings and 'time_conversion_factor' in time_calibration_settings:
            factor = time_calibration_settings['time_conversion_factor']
            # Allow much smaller values for Knudsen parabolic law (units: h⁻²)
            # Default is 0.00045, so range should accommodate scientific values
            if not (0.00001 <= factor <= 100.0):
                raise ValueError(f"Time conversion factor must be between 0.00001-100.0, got {factor}")
        
        # Validate advanced settings ranges
        if advanced_settings:
            if 'c3a_fraction' in advanced_settings:
                c3a = advanced_settings['c3a_fraction']
                if not (0.0 <= c3a <= 0.3):
                    raise ValueError(f"C3A fraction must be between 0.0-0.3, got {c3a}")
        
        # Validate database parameter modifications
        if db_param_modifications:
            for param_name, value in db_param_modifications.items():
                if not isinstance(value, (int, float)):
                    raise ValueError(f"Parameter modification values must be numeric, got {type(value)} for {param_name}")
                if not (0.01 <= value <= 100.0):
                    raise ValueError(f"Parameter modification values must be between 0.01-100.0, got {value} for {param_name}")
        
        self.logger.info("Parameter completeness validation passed")

    def _auto_save_hydration_before_execution(self, operation_name: str, selected_microstructure: Dict[str, Any],
                                            curing_conditions: Dict[str, Any], time_calibration: Dict[str, Any],
                                            advanced_settings: Dict[str, Any], db_modifications: Dict[str, Any],
                                            ui_parameters: Dict[str, Any]) -> Optional[int]:
        """
        Auto-save hydration configuration before execution.
        Similar to mix design autosave functionality.
        Returns the saved hydration operation ID if successful.
        """
        try:
            from datetime import datetime

            # Prepare hydration configuration for autosave
            max_time = self.max_time_spin.get_value()

            # Get temperature profile data
            temperature_profile = {}
            if hasattr(self, 'temperature_profile_combo'):
                profile_name = self.temperature_profile_combo.get_active_text()
                if profile_name and profile_name != "Select profile...":
                    temperature_profile = {
                        'name': profile_name,
                        'data': getattr(self, 'current_temperature_profile_data', {})
                    }

            hydration_config = {
                'operation_name': operation_name,
                'source_microstructure': selected_microstructure,
                'max_time_hours': max_time,
                'curing_conditions': curing_conditions,
                'time_calibration': time_calibration,
                'advanced_settings': advanced_settings,
                'temperature_profile': temperature_profile,
                'database_modifications': db_modifications,
                'ui_parameters': ui_parameters,
                'timestamp': datetime.now().isoformat()
            }

            # Use the saved hydration service for autosave
            from app.services.saved_hydration_service import SavedHydrationOperationService
            saved_hydration_service = SavedHydrationOperationService(self.service_container.database_service)

            saved_hydration_id = saved_hydration_service.auto_save_before_execution(hydration_config)

            if saved_hydration_id:
                self.logger.info(f"✅ Hydration auto-saved with ID: {saved_hydration_id}")
                return saved_hydration_id
            else:
                self.logger.warning("⚠️ Hydration autosave returned None")
                return None

        except Exception as e:
            self.logger.error(f"❌ Hydration autosave failed: {e}")
            import traceback
            self.logger.error(f"Full autosave traceback: {traceback.format_exc()}")
            return None

    def _load_saved_hydration_operation(self, saved_hydration_id: int) -> None:
        """Load a complete saved hydration operation and restore all UI settings."""
        try:
            from app.services.saved_hydration_service import SavedHydrationOperationService
            saved_hydration_service = SavedHydrationOperationService(self.service_container.database_service)

            # Get saved hydration operation from database
            saved_hydration = saved_hydration_service.get_by_id(saved_hydration_id)
            if not saved_hydration:
                raise ValueError(f"Saved hydration operation with ID {saved_hydration_id} not found")

            # Restore operation name
            self.operation_name_entry.set_text(saved_hydration.name)

            # Restore max time
            self.max_time_spin.set_value(saved_hydration.max_time_hours)

            # Restore source microstructure selection if possible
            # Note: This would require finding the microstructure in the list
            # For now, we'll just show the name but user may need to reselect
            self.logger.info(f"Loading hydration operation based on source microstructure: {saved_hydration.source_microstructure_name}")

            # Restore UI parameters if available
            if saved_hydration.ui_parameters:
                ui_params = saved_hydration.ui_parameters
                self._restore_ui_from_parameters(ui_params)

            # Restore curing conditions
            if saved_hydration.curing_conditions:
                self._restore_curing_conditions(saved_hydration.curing_conditions)

            # Restore time calibration
            if saved_hydration.time_calibration:
                self._restore_time_calibration(saved_hydration.time_calibration)

            # Restore advanced settings
            if saved_hydration.advanced_settings:
                self._restore_advanced_settings(saved_hydration.advanced_settings)

            # Restore database modifications
            if saved_hydration.database_modifications:
                self._restore_database_modifications(saved_hydration.database_modifications)

            # Show success message
            self._update_status(f"Loaded hydration operation: {saved_hydration.name}")
            self.logger.info(f"✅ Successfully loaded saved hydration operation: {saved_hydration.name}")

        except Exception as e:
            self.logger.error(f"Failed to load saved hydration operation: {e}")
            error_dialog = Gtk.MessageDialog(
                self.get_toplevel(),
                Gtk.DialogFlags.MODAL,
                Gtk.MessageType.ERROR,
                Gtk.ButtonsType.OK,
                f"Failed to load hydration operation: {e}"
            )
            error_dialog.run()
            error_dialog.destroy()

    def _restore_ui_from_parameters(self, ui_params: Dict[str, Any]) -> None:
        """Restore UI controls from saved parameters."""
        try:
            self.logger.info(f"Restoring UI from saved parameters...")

            # Restore operation name (if not already set)
            if 'operation_name' in ui_params:
                self.operation_name_entry.set_text(ui_params['operation_name'])

            # Restore curing conditions
            if 'curing_conditions' in ui_params:
                self._restore_curing_conditions(ui_params['curing_conditions'])

            # Restore time calibration
            if 'time_calibration' in ui_params:
                self._restore_time_calibration(ui_params['time_calibration'])

            # Restore advanced settings
            if 'advanced_settings' in ui_params:
                self._restore_advanced_settings(ui_params['advanced_settings'])

            # Restore database modifications
            if 'database_modifications' in ui_params:
                self._restore_database_modifications(ui_params['database_modifications'])

            self.logger.info("✅ UI restoration completed successfully")

        except Exception as e:
            self.logger.error(f"Error restoring UI from parameters: {e}")
            import traceback
            self.logger.error(f"Full restore traceback: {traceback.format_exc()}")

    def _restore_curing_conditions(self, curing_conditions: Dict[str, Any]) -> None:
        """Restore curing conditions UI controls."""
        try:
            self.logger.debug("Restoring curing conditions...")

            # Restore initial temperature
            if 'initial_temperature_celsius' in curing_conditions:
                self.initial_temp_spin.set_value(curing_conditions['initial_temperature_celsius'])

            # Restore thermal mode
            if 'thermal_mode' in curing_conditions:
                thermal_mode = curing_conditions['thermal_mode']
                if thermal_mode == 'isothermal':
                    self.isothermal_radio.set_active(True)
                elif thermal_mode == 'adiabatic':
                    self.adiabatic_radio.set_active(True)
                elif thermal_mode == 'temperature_profile':
                    self.temperature_profile_radio.set_active(True)

            # Restore moisture mode
            if 'moisture_mode' in curing_conditions:
                moisture_mode = curing_conditions['moisture_mode']
                if moisture_mode == 'saturated':
                    self.saturated_radio.set_active(True)
                else:  # sealed
                    self.sealed_radio.set_active(True)

            # Restore temperature profile if present
            if 'temperature_profile' in curing_conditions:
                profile_data = curing_conditions['temperature_profile']
                if profile_data and 'points' in profile_data:
                    points = []
                    for point_data in profile_data['points']:
                        points.append(TemperaturePoint(
                            point_data['time_hours'],
                            point_data['temperature_celsius']
                        ))

                    self.current_profile = TemperatureProfile(
                        name=profile_data.get('name', 'Restored Profile'),
                        description=profile_data.get('description', 'Restored from saved operation'),
                        points=points
                    )
                    self._update_profile_display()
                    self.logger.debug(f"Restored temperature profile: {self.current_profile.name}")

            # Also check for temperature profile data in alternate format
            elif 'temperature_profile_data' in curing_conditions:
                profile_data = curing_conditions['temperature_profile_data']
                if profile_data:
                    points = []
                    for time_hours, temp_celsius in profile_data:
                        points.append(TemperaturePoint(time_hours, temp_celsius))

                    self.current_profile = TemperatureProfile(
                        name='Restored Profile',
                        description='Restored from saved operation',
                        points=points
                    )
                    self._update_profile_display()

            self.logger.debug("Curing conditions restored successfully")

        except Exception as e:
            self.logger.error(f"Error restoring curing conditions: {e}")

    def _restore_time_calibration(self, time_calibration: Dict[str, Any]) -> None:
        """Restore time calibration UI controls."""
        try:
            self.logger.debug("Restoring time calibration...")

            # Restore time conversion factor
            if 'time_conversion_factor' in time_calibration:
                factor = time_calibration['time_conversion_factor']
                self.time_conversion_spin.set_value(factor)
                self.logger.debug(f"Restored time conversion factor: {factor}")

        except Exception as e:
            self.logger.error(f"Error restoring time calibration: {e}")

    def _restore_advanced_settings(self, advanced_settings: Dict[str, Any]) -> None:
        """Restore advanced settings UI controls."""
        try:
            self.logger.debug("Restoring advanced settings...")

            # Restore C3A fraction
            if 'c3a_fraction' in advanced_settings:
                self.c3a_fraction_spin.set_value(advanced_settings['c3a_fraction'])

            # Restore CSH seeds
            if 'csh_seeds' in advanced_settings:
                self.csh_seeds_spin.set_value(advanced_settings['csh_seeds'])

            # Restore alpha max
            if 'alpha_max' in advanced_settings:
                self.alpha_max_spin.set_value(advanced_settings['alpha_max'])

            # Restore activation energies
            if 'e_act_cement' in advanced_settings:
                self.e_act_spin.set_value(advanced_settings['e_act_cement'])

            if 'e_act_pozzolan' in advanced_settings:
                self.e_act_pozz_spin.set_value(advanced_settings['e_act_pozzolan'])

            if 'e_act_slag' in advanced_settings:
                self.e_act_slag_spin.set_value(advanced_settings['e_act_slag'])

            # Restore output frequencies
            if 'burn_frequency' in advanced_settings:
                self.burn_freq_spin.set_value(advanced_settings['burn_frequency'])

            if 'setting_frequency' in advanced_settings:
                self.set_freq_spin.set_value(advanced_settings['setting_frequency'])

            if 'physical_frequency' in advanced_settings:
                self.phyd_freq_spin.set_value(advanced_settings['physical_frequency'])

            if 'movie_frequency' in advanced_settings:
                self.movie_freq_spin.set_value(advanced_settings['movie_frequency'])

            # Restore output settings
            if 'save_interval_hours' in advanced_settings:
                self.save_interval_spin.set_value(advanced_settings['save_interval_hours'])

            # Restore formation flags (converting from int to bool if needed)
            if 'csh2_flag' in advanced_settings:
                self.csh2_flag_check.set_active(bool(advanced_settings['csh2_flag']))
            elif 'csh2_formation' in advanced_settings:
                self.csh2_flag_check.set_active(advanced_settings['csh2_formation'])

            if 'ch_flag' in advanced_settings:
                self.ch_flag_check.set_active(bool(advanced_settings['ch_flag']))
            elif 'ch_formation' in advanced_settings:
                self.ch_flag_check.set_active(advanced_settings['ch_formation'])

            if 'ph_active' in advanced_settings:
                self.ph_active_check.set_active(bool(advanced_settings['ph_active']))
            elif 'ph_computation' in advanced_settings:
                self.ph_active_check.set_active(advanced_settings['ph_computation'])

            # Restore ettringite formation
            if 'ettringite_formation' in advanced_settings:
                self.ettringite_check.set_active(advanced_settings['ettringite_formation'])

            # Restore random seed
            if 'random_seed' in advanced_settings:
                self.random_seed_spin.set_value(advanced_settings['random_seed'])

            self.logger.debug("Advanced settings restored successfully")

        except Exception as e:
            self.logger.error(f"Error restoring advanced settings: {e}")

    def _restore_database_modifications(self, database_modifications: Dict[str, Any]) -> None:
        """Restore database modifications UI controls."""
        try:
            self.logger.debug("Restoring database modifications...")

            # Clear existing modifications first
            if hasattr(self, 'database_params_store'):
                self.database_params_store.clear()

            # Restore each database parameter modification
            for param_name, new_value in database_modifications.items():
                if hasattr(self, 'database_params_store'):
                    # Add parameter to the store for display
                    iter_obj = self.database_params_store.append()
                    self.database_params_store.set(iter_obj, 0, param_name)
                    self.database_params_store.set(iter_obj, 1, str(new_value))
                    self.database_params_store.set(iter_obj, 2, "")  # Original value (to be looked up)

            self.logger.debug(f"Restored {len(database_modifications)} database parameter modifications")

        except Exception as e:
            self.logger.error(f"Error restoring database modifications: {e}")
#!/usr/bin/env python3
"""
Aggregate Management Panel for VCCTL

Provides comprehensive aggregate management interface with grading curves, 
blending calculations, and sieve analysis tools.
"""

import gi
import logging
import json
import csv
from typing import TYPE_CHECKING, Optional, Dict, Any, List, Tuple
from pathlib import Path
from decimal import Decimal

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, Pango, Gdk
from app.utils.icon_utils import create_icon_image

if TYPE_CHECKING:
    from app.windows.main_window import VCCTLMainWindow

from app.services.service_container import get_service_container
from app.widgets import GradingCurveWidget


class AggregateType:
    """Aggregate type classifications."""
    COARSE = "coarse"
    FINE = "fine"
    COMBINED = "combined"


class AggregatePanel(Gtk.Box):
    """Aggregate management panel with advanced grading and blending capabilities."""
    
    def __init__(self, main_window: 'VCCTLMainWindow'):
        """Initialize the aggregate panel."""
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        self.main_window = main_window
        self.logger = logging.getLogger('VCCTL.AggregatePanel')
        self.service_container = get_service_container()
        
        # Panel state
        self.current_aggregate = None
        self.blend_components = []
        self.combined_grading = []
        
        # Setup UI
        self._setup_ui()
        self._connect_signals()
        
        # Load initial data
        self._load_aggregate_data()
        
        self.logger.info("Aggregate panel initialized")
    
    def _setup_ui(self) -> None:
        """Setup the aggregate panel UI."""
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
        title_label.set_markup('<span size="large" weight="bold">Aggregate & Grading Management</span>')
        title_label.set_halign(Gtk.Align.START)
        title_box.pack_start(title_label, False, False, 0)
        
        # Mode selection
        mode_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        mode_label = Gtk.Label("Mode:")
        self.mode_combo = Gtk.ComboBoxText()
        self.mode_combo.append("single", "Single Aggregate")
        self.mode_combo.append("blending", "Aggregate Blending")
        self.mode_combo.append("analysis", "Sieve Analysis")
        self.mode_combo.set_active(0)
        mode_box.pack_start(mode_label, False, False, 0)
        mode_box.pack_start(self.mode_combo, False, False, 0)
        title_box.pack_end(mode_box, False, False, 0)
        
        header_box.pack_start(title_box, False, False, 0)
        
        # Description
        desc_label = Gtk.Label()
        desc_label.set_markup('<span size="small">Design and analyze aggregate grading curves with blending calculations</span>')
        desc_label.set_halign(Gtk.Align.START)
        header_box.pack_start(desc_label, False, False, 0)
        
        # Aggregate selection and type controls
        controls_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        # Aggregate selection
        agg_select_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        agg_label = Gtk.Label("Aggregate:")
        agg_label.set_size_request(80, -1)
        self.aggregate_combo = Gtk.ComboBoxText()
        self.aggregate_combo.set_size_request(200, -1)
        agg_select_box.pack_start(agg_label, False, False, 0)
        agg_select_box.pack_start(self.aggregate_combo, False, False, 0)
        controls_box.pack_start(agg_select_box, False, False, 0)
        
        # Aggregate type
        type_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        type_label = Gtk.Label("Type:")
        self.type_combo = Gtk.ComboBoxText()
        self.type_combo.append(AggregateType.COARSE, "Coarse")
        self.type_combo.append(AggregateType.FINE, "Fine")
        self.type_combo.append(AggregateType.COMBINED, "Combined")
        self.type_combo.set_active(0)
        type_box.pack_start(type_label, False, False, 0)
        type_box.pack_start(self.type_combo, False, False, 0)
        controls_box.pack_start(type_box, False, False, 0)
        
        # Action buttons
        action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        action_box.get_style_context().add_class("linked")
        
        self.new_button = Gtk.Button(label="New")
        new_icon = create_icon_image("add-alt", 16)
        self.new_button.set_image(new_icon)
        self.new_button.set_always_show_image(True)
        action_box.pack_start(self.new_button, False, False, 0)
        
        self.save_button = Gtk.Button(label="Save")
        save_icon = create_icon_image("save", 16)
        self.save_button.set_image(save_icon)
        self.save_button.set_always_show_image(True)
        self.save_button.get_style_context().add_class("suggested-action")
        action_box.pack_start(self.save_button, False, False, 0)
        
        self.export_button = Gtk.Button(label="Export")
        export_icon = create_icon_image("export", 16)
        self.export_button.set_image(export_icon)
        self.export_button.set_always_show_image(True)
        action_box.pack_start(self.export_button, False, False, 0)
        
        controls_box.pack_end(action_box, False, False, 0)
        
        header_box.pack_start(controls_box, False, False, 0)
        
        self.pack_start(header_box, False, False, 0)
    
    def _create_content_area(self) -> None:
        """Create the main content area."""
        # Create notebook for different modes
        self.content_notebook = Gtk.Notebook()
        self.content_notebook.set_show_tabs(False)  # Controlled by mode combo
        self.content_notebook.set_show_border(False)
        
        # Single aggregate mode
        self._create_single_aggregate_page()
        
        # Blending mode
        self._create_blending_page()
        
        # Analysis mode  
        self._create_analysis_page()
        
        self.pack_start(self.content_notebook, True, True, 0)
    
    def _create_single_aggregate_page(self) -> None:
        """Create the single aggregate editing page."""
        page_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        page_box.set_margin_top(10)
        page_box.set_margin_bottom(10)
        page_box.set_margin_left(10)
        page_box.set_margin_right(10)
        
        # Left side: Grading curve widget
        left_frame = Gtk.Frame(label="Grading Curve")
        left_frame.set_size_request(250, -1)  # Further reduced to allow narrower windows
        
        # TEMPORARILY DISABLE GRADING CURVE WIDGET TO ELIMINATE INFINITE SURFACE SIZE WARNINGS
        # self.grading_widget = GradingCurveWidget()
        # self.grading_widget.connect('curve-changed', self._on_grading_changed)
        # left_frame.add(self.grading_widget)
        
        # Create placeholder for grading curve widget
        placeholder_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        placeholder_label = Gtk.Label()
        placeholder_label.set_markup('<span size="large">Grading Curve Widget</span>')
        placeholder_label.set_halign(Gtk.Align.CENTER)
        placeholder_box.pack_start(placeholder_label, True, True, 0)
        
        enable_button = Gtk.Button(label="Enable Grading Curve Widget")
        enable_button.set_tooltip_text("Click to enable the grading curve widget")
        placeholder_box.pack_start(enable_button, False, False, 0)
        
        left_frame.add(placeholder_box)
        self.grading_widget = None  # Store reference for later activation
        
        page_box.pack_start(left_frame, True, True, 0)
        
        # Right side: Properties and calculations
        right_frame = Gtk.Frame(label="Aggregate Properties")
        right_frame.set_size_request(250, -1)  # Reduced to allow narrower windows
        self._create_properties_section(right_frame)
        
        page_box.pack_start(right_frame, False, False, 0)
        
        self.content_notebook.append_page(page_box, Gtk.Label("Single"))
    
    def _create_blending_page(self) -> None:
        """Create the aggregate blending page."""
        blending_paned = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL)
        blending_paned.set_margin_top(10)
        blending_paned.set_margin_bottom(10)
        blending_paned.set_margin_left(10)
        blending_paned.set_margin_right(10)
        
        # Top: Blend components
        top_frame = Gtk.Frame(label="Blend Components")
        self._create_blend_components_section(top_frame)
        blending_paned.pack1(top_frame, False, False)
        
        # Bottom: Combined grading result
        bottom_frame = Gtk.Frame(label="Combined Grading Curve")
        # TEMPORARILY DISABLE COMBINED GRADING CURVE WIDGET TO ELIMINATE INFINITE SURFACE SIZE WARNINGS
        # self.combined_grading_widget = GradingCurveWidget()
        # bottom_frame.add(self.combined_grading_widget)
        
        # Create placeholder for combined grading curve widget
        combined_placeholder_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        combined_placeholder_label = Gtk.Label()
        combined_placeholder_label.set_markup('<span size="large">Combined Grading Curve Widget</span>')
        combined_placeholder_label.set_halign(Gtk.Align.CENTER)
        combined_placeholder_box.pack_start(combined_placeholder_label, True, True, 0)
        
        combined_enable_button = Gtk.Button(label="Enable Combined Grading Widget")
        combined_enable_button.set_tooltip_text("Click to enable the combined grading curve widget")
        combined_placeholder_box.pack_start(combined_enable_button, False, False, 0)
        
        bottom_frame.add(combined_placeholder_box)
        self.combined_grading_widget = None  # Store reference for later activation
        blending_paned.pack2(bottom_frame, True, False)
        
        self.content_notebook.append_page(blending_paned, Gtk.Label("Blending"))
    
    def _create_analysis_page(self) -> None:
        """Create the sieve analysis page."""
        analysis_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        analysis_box.set_margin_top(10)
        analysis_box.set_margin_bottom(10)
        analysis_box.set_margin_left(10)
        analysis_box.set_margin_right(10)
        
        # Left: Analysis tools
        left_frame = Gtk.Frame(label="Analysis Tools")
        left_frame.set_size_request(250, -1)  # Reduced to allow narrower windows
        self._create_analysis_tools(left_frame)
        analysis_box.pack_start(left_frame, False, False, 0)
        
        # Right: Results
        right_frame = Gtk.Frame(label="Analysis Results")
        self._create_analysis_results(right_frame)
        analysis_box.pack_start(right_frame, True, True, 0)
        
        self.content_notebook.append_page(analysis_box, Gtk.Label("Analysis"))
    
    def _create_properties_section(self, parent: Gtk.Frame) -> None:
        """Create the aggregate properties section."""
        props_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        props_box.set_margin_top(10)
        props_box.set_margin_bottom(10)
        props_box.set_margin_left(10)
        props_box.set_margin_right(10)
        
        # Basic properties
        basic_frame = Gtk.Frame(label="Basic Properties")
        basic_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        basic_box.set_margin_top(10)
        basic_box.set_margin_bottom(10)
        basic_box.set_margin_left(10)
        basic_box.set_margin_right(10)
        
        # Properties grid
        props_grid = Gtk.Grid()
        props_grid.set_row_spacing(5)
        props_grid.set_column_spacing(10)
        
        # Specific gravity
        sg_label = Gtk.Label("Specific Gravity:")
        sg_label.set_halign(Gtk.Align.END)
        self.sg_spin = Gtk.SpinButton.new_with_range(2.0, 4.0, 0.01)
        self.sg_spin.set_value(2.65)
        self.sg_spin.set_digits(3)
        props_grid.attach(sg_label, 0, 0, 1, 1)
        props_grid.attach(self.sg_spin, 1, 0, 1, 1)
        
        # Absorption
        abs_label = Gtk.Label("Absorption (%):")
        abs_label.set_halign(Gtk.Align.END)
        self.abs_spin = Gtk.SpinButton.new_with_range(0.0, 10.0, 0.1)
        self.abs_spin.set_value(1.5)
        self.abs_spin.set_digits(1)
        props_grid.attach(abs_label, 0, 1, 1, 1)
        props_grid.attach(self.abs_spin, 1, 1, 1, 1)
        
        # Bulk density
        bd_label = Gtk.Label("Bulk Density (kg/m³):")
        bd_label.set_halign(Gtk.Align.END)
        self.bd_spin = Gtk.SpinButton.new_with_range(1000, 2000, 10)
        self.bd_spin.set_value(1600)
        props_grid.attach(bd_label, 0, 2, 1, 1)
        props_grid.attach(self.bd_spin, 1, 2, 1, 1)
        
        basic_box.pack_start(props_grid, False, False, 0)
        basic_frame.add(basic_box)
        props_box.pack_start(basic_frame, False, False, 0)
        
        # Gradation parameters
        grad_frame = Gtk.Frame(label="Gradation Parameters")
        grad_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        grad_box.set_margin_top(10)
        grad_box.set_margin_bottom(10)
        grad_box.set_margin_left(10)
        grad_box.set_margin_right(10)
        
        self.grad_params_grid = Gtk.Grid()
        self.grad_params_grid.set_row_spacing(5)
        self.grad_params_grid.set_column_spacing(10)
        
        # Initialize parameter labels
        self._create_gradation_parameter_labels()
        
        grad_box.pack_start(self.grad_params_grid, False, False, 0)
        grad_frame.add(grad_box)
        props_box.pack_start(grad_frame, False, False, 0)
        
        # Classification
        class_frame = Gtk.Frame(label="Classification")
        class_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        class_box.set_margin_top(10)
        class_box.set_margin_bottom(10)
        class_box.set_margin_left(10)
        class_box.set_margin_right(10)
        
        self.classification_label = Gtk.Label()
        self.classification_label.set_markup('<span size="small">Classification will appear here</span>')
        self.classification_label.set_line_wrap(True)
        self.classification_label.set_max_width_chars(30)
        class_box.pack_start(self.classification_label, False, False, 0)
        
        class_frame.add(class_box)
        props_box.pack_start(class_frame, True, True, 0)
        
        parent.add(props_box)
    
    def _create_gradation_parameter_labels(self) -> None:
        """Create gradation parameter display labels."""
        parameters = [
            ("D10:", "d10"),
            ("D30:", "d30"),
            ("D60:", "d60"),
            ("Cu:", "cu"),
            ("Cc:", "cc"),
            ("Fineness Modulus:", "fm")
        ]
        
        self.grad_param_labels = {}
        
        for i, (label_text, key) in enumerate(parameters):
            label = Gtk.Label(label_text)
            label.set_halign(Gtk.Align.END)
            label.get_style_context().add_class("dim-label")
            self.grad_params_grid.attach(label, 0, i, 1, 1)
            
            value_label = Gtk.Label("—")
            value_label.set_halign(Gtk.Align.START)
            self.grad_param_labels[key] = value_label
            self.grad_params_grid.attach(value_label, 1, i, 1, 1)
    
    def _create_blend_components_section(self, parent: Gtk.Frame) -> None:
        """Create the blend components section."""
        blend_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        blend_box.set_margin_top(10)
        blend_box.set_margin_bottom(10)
        blend_box.set_margin_left(10)
        blend_box.set_margin_right(10)
        
        # Controls
        controls_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        add_component_button = Gtk.Button(label="Add Component")
        add_icon = create_icon_image("add", 16)
        add_component_button.set_image(add_icon)
        add_component_button.set_always_show_image(True)
        add_component_button.connect('clicked', self._on_add_blend_component)
        controls_box.pack_start(add_component_button, False, False, 0)
        
        calculate_blend_button = Gtk.Button(label="Calculate Blend")
        calc_icon = create_icon_image("calculator", 16)
        calculate_blend_button.set_image(calc_icon)
        calculate_blend_button.set_always_show_image(True)
        calculate_blend_button.connect('clicked', self._on_calculate_blend)
        controls_box.pack_start(calculate_blend_button, False, False, 0)
        
        normalize_button = Gtk.Button(label="Normalize")
        normalize_button.set_tooltip_text("Normalize proportions to sum to 100%")
        normalize_button.connect('clicked', self._on_normalize_blend)
        controls_box.pack_start(normalize_button, False, False, 0)
        
        blend_box.pack_start(controls_box, False, False, 0)
        
        # Component list
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_size_request(-1, 200)
        
        self.blend_components_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        scrolled.add(self.blend_components_box)
        
        blend_box.pack_start(scrolled, True, True, 0)
        
        parent.add(blend_box)
    
    def _create_analysis_tools(self, parent: Gtk.Frame) -> None:
        """Create the analysis tools section."""
        tools_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        tools_box.set_margin_top(10)
        tools_box.set_margin_bottom(10)
        tools_box.set_margin_left(10)
        tools_box.set_margin_right(10)
        
        # Import/Export tools
        io_frame = Gtk.Frame(label="Import/Export")
        io_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        io_box.set_margin_top(10)
        io_box.set_margin_bottom(10)
        io_box.set_margin_left(10)
        io_box.set_margin_right(10)
        
        import_csv_button = Gtk.Button(label="Import CSV")
        import_csv_button.connect('clicked', self._on_import_csv)
        io_box.pack_start(import_csv_button, False, False, 0)
        
        export_csv_button = Gtk.Button(label="Export CSV")
        export_csv_button.connect('clicked', self._on_export_csv)
        io_box.pack_start(export_csv_button, False, False, 0)
        
        io_frame.add(io_box)
        tools_box.pack_start(io_frame, False, False, 0)
        
        # Curve fitting tools
        fitting_frame = Gtk.Frame(label="Curve Fitting")
        fitting_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        fitting_box.set_margin_top(10)
        fitting_box.set_margin_bottom(10)
        fitting_box.set_margin_left(10)
        fitting_box.set_margin_right(10)
        
        self.fitting_combo = Gtk.ComboBoxText()
        self.fitting_combo.append("rosin_rammler", "Rosin-Rammler")
        self.fitting_combo.append("gates_gaudin", "Gates-Gaudin-Schumann")
        self.fitting_combo.append("polynomial", "Polynomial")
        self.fitting_combo.set_active(0)
        fitting_box.pack_start(self.fitting_combo, False, False, 0)
        
        fit_curve_button = Gtk.Button(label="Fit Curve")
        fit_curve_button.connect('clicked', self._on_fit_curve)
        fitting_box.pack_start(fit_curve_button, False, False, 0)
        
        fitting_frame.add(fitting_box)
        tools_box.pack_start(fitting_frame, False, False, 0)
        
        parent.add(tools_box)
    
    def _create_analysis_results(self, parent: Gtk.Frame) -> None:
        """Create the analysis results section."""
        results_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        results_box.set_margin_top(10)
        results_box.set_margin_bottom(10)
        results_box.set_margin_left(10)
        results_box.set_margin_right(10)
        
        # Results text view
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        
        self.results_textview = Gtk.TextView()
        self.results_textview.set_editable(False)
        self.results_textview.set_wrap_mode(Gtk.WrapMode.WORD)
        scrolled.add(self.results_textview)
        
        results_box.pack_start(scrolled, True, True, 0)
        
        parent.add(results_box)
    
    def _create_status_area(self) -> None:
        """Create the status area."""
        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        status_box.set_margin_top(10)
        status_box.set_margin_bottom(10)
        status_box.set_margin_left(15)
        status_box.set_margin_right(15)
        
        # Status label
        self.status_label = Gtk.Label()
        self.status_label.set_markup('<span size="small">Ready for aggregate analysis</span>')
        self.status_label.set_halign(Gtk.Align.START)
        status_box.pack_start(self.status_label, True, True, 0)
        
        self.pack_start(status_box, False, False, 0)
    
    def _load_aggregate_data(self) -> None:
        """Load available aggregate data."""
        try:
            aggregate_service = self.service_container.aggregate_service
            aggregates = aggregate_service.get_all()
            
            # Clear existing items
            self.aggregate_combo.remove_all()
            
            # Add aggregates to combo
            for aggregate in aggregates:
                self.aggregate_combo.append(str(aggregate.id), aggregate.name)
            
            # Set first as active if available
            if aggregates:
                self.aggregate_combo.set_active(0)
                self._load_aggregate_grading(aggregates[0])
            
            self.logger.info(f"Loaded {len(aggregates)} aggregates")
            
        except Exception as e:
            self.logger.error(f"Failed to load aggregate data: {e}")
            self.main_window.update_status(f"Error loading aggregates: {e}", "error", 5)
    
    def _load_aggregate_grading(self, aggregate) -> None:
        """Load grading data for an aggregate."""
        try:
            # TODO: Load actual grading data from aggregate
            # For now, create sample data
            sample_grading = [
                (25.0, 100.0), (19.0, 95.0), (12.5, 85.0), (9.5, 75.0),
                (4.75, 40.0), (2.36, 25.0), (1.18, 15.0), (0.60, 8.0),
                (0.30, 4.0), (0.15, 2.0), (0.075, 1.0)
            ]
            
            self.grading_widget.set_grading_data(sample_grading)
            self._update_gradation_parameters()
            
        except Exception as e:
            self.logger.error(f"Failed to load aggregate grading: {e}")
    
    def _connect_signals(self) -> None:
        """Connect widget signals."""
        # Header controls
        self.mode_combo.connect('changed', self._on_mode_changed)
        self.aggregate_combo.connect('changed', self._on_aggregate_changed)
        self.type_combo.connect('changed', self._on_type_changed)
        
        # Action buttons
        self.new_button.connect('clicked', self._on_new_clicked)
        self.save_button.connect('clicked', self._on_save_clicked)
        self.export_button.connect('clicked', self._on_export_clicked)
        
        # Property changes
        self.sg_spin.connect('value-changed', self._on_property_changed)
        self.abs_spin.connect('value-changed', self._on_property_changed)
        self.bd_spin.connect('value-changed', self._on_property_changed)
    
    # Signal handlers
    def _on_mode_changed(self, combo) -> None:
        """Handle mode change."""
        mode = combo.get_active_id()
        
        if mode == "single":
            self.content_notebook.set_current_page(0)
        elif mode == "blending":
            self.content_notebook.set_current_page(1)
        elif mode == "analysis":
            self.content_notebook.set_current_page(2)
    
    def _on_aggregate_changed(self, combo) -> None:
        """Handle aggregate selection change."""
        aggregate_id = combo.get_active_id()
        if aggregate_id:
            try:
                aggregate_service = self.service_container.aggregate_service
                aggregate = aggregate_service.get_by_id(int(aggregate_id))
                self.current_aggregate = aggregate
                self._load_aggregate_grading(aggregate)
            except Exception as e:
                self.logger.error(f"Failed to load aggregate: {e}")
    
    def _on_type_changed(self, combo) -> None:
        """Handle aggregate type change."""
        agg_type = combo.get_active_id()
        # Update UI based on type (e.g., filter available sieves)
        self.logger.debug(f"Aggregate type changed to: {agg_type}")
    
    def _on_grading_changed(self, widget) -> None:
        """Handle grading curve change."""
        self._update_gradation_parameters()
        self._update_classification()
    
    def _on_property_changed(self, widget) -> None:
        """Handle property change."""
        # Update calculations based on property changes
        pass
    
    def _on_new_clicked(self, button) -> None:
        """Handle new aggregate button click."""
        # Clear current data
        self.grading_widget.set_grading_data([])
        self.current_aggregate = None
        self.status_label.set_markup('<span size="small">New aggregate - enter grading data</span>')
    
    def _on_save_clicked(self, button) -> None:
        """Handle save button click."""
        # TODO: Implement aggregate saving
        self.main_window.update_status("Aggregate saving will be implemented", "info", 3)
    
    def _on_export_clicked(self, button) -> None:
        """Handle export button click."""
        self._export_grading_data()
    
    def _on_add_blend_component(self, button) -> None:
        """Handle add blend component."""
        self._add_blend_component_row()
    
    def _on_calculate_blend(self, button) -> None:
        """Handle calculate blend."""
        self._calculate_combined_grading()
    
    def _on_normalize_blend(self, button) -> None:
        """Handle normalize blend proportions."""
        self._normalize_blend_proportions()
    
    def _on_import_csv(self, button) -> None:
        """Handle import CSV."""
        self._import_grading_csv()
    
    def _on_export_csv(self, button) -> None:
        """Handle export CSV."""
        self._export_grading_csv()
    
    def _on_fit_curve(self, button) -> None:
        """Handle curve fitting."""
        fitting_type = self.fitting_combo.get_active_id()
        self._fit_grading_curve(fitting_type)
    
    # Helper methods
    def _update_gradation_parameters(self) -> None:
        """Update gradation parameters display."""
        try:
            grading_data = self.grading_widget.get_grading_data()
            if not grading_data:
                # Clear parameters
                for label in self.grad_param_labels.values():
                    label.set_text("—")
                return
            
            # Calculate parameters using the grading widget method
            params = self.grading_widget.get_gradation_parameters()
            
            # Update labels
            self.grad_param_labels['d10'].set_text(f"{params.get('D10', 0):.3f} mm" if 'D10' in params else "—")
            self.grad_param_labels['d30'].set_text(f"{params.get('D30', 0):.3f} mm" if 'D30' in params else "—")
            self.grad_param_labels['d60'].set_text(f"{params.get('D60', 0):.3f} mm" if 'D60' in params else "—")
            self.grad_param_labels['cu'].set_text(f"{params.get('Cu', 0):.2f}" if 'Cu' in params else "—")
            self.grad_param_labels['cc'].set_text(f"{params.get('Cc', 0):.2f}" if 'Cc' in params else "—")
            
            # Calculate fineness modulus
            fm = self._calculate_fineness_modulus(grading_data)
            self.grad_param_labels['fm'].set_text(f"{fm:.2f}" if fm else "—")
            
        except Exception as e:
            self.logger.error(f"Failed to update gradation parameters: {e}")
    
    def _calculate_fineness_modulus(self, grading_data: List[Tuple[float, float]]) -> Optional[float]:
        """Calculate fineness modulus."""
        try:
            # Standard sieves for fineness modulus (mm)
            fm_sieves = [9.5, 4.75, 2.36, 1.18, 0.60, 0.30, 0.15]
            
            # Calculate cumulative retained percentages
            total_retained = 0.0
            
            for sieve_size in fm_sieves:
                # Find percent passing at this sieve size
                percent_passing = 0.0
                for i in range(len(grading_data) - 1):
                    size1, percent1 = grading_data[i]
                    size2, percent2 = grading_data[i + 1]
                    
                    if size2 <= sieve_size <= size1:
                        # Interpolate
                        if size1 != size2:
                            percent_passing = percent1 + (percent2 - percent1) * (sieve_size - size1) / (size2 - size1)
                        else:
                            percent_passing = percent1
                        break
                
                # Add cumulative retained
                percent_retained = 100.0 - percent_passing
                total_retained += percent_retained
            
            # Fineness modulus is sum of cumulative retained divided by 100
            return total_retained / 100.0
            
        except Exception as e:
            self.logger.error(f"Failed to calculate fineness modulus: {e}")
            return None
    
    def _update_classification(self) -> None:
        """Update aggregate classification."""
        try:
            grading_data = self.grading_widget.get_grading_data()
            if not grading_data:
                self.classification_label.set_markup('<span size="small">No data for classification</span>')
                return
            
            # Get gradation parameters
            params = self.grading_widget.get_gradation_parameters()
            
            # Basic classification logic
            classification_text = ""
            
            # Uniformity classification
            cu = params.get('Cu', 0)
            if cu > 4:
                classification_text += "Well graded\n"
            elif cu < 2:
                classification_text += "Uniformly graded\n"
            else:
                classification_text += "Poorly graded\n"
            
            # Size classification
            d60 = params.get('D60', 0)
            if d60 > 4.75:
                classification_text += "Coarse aggregate\n"
            elif d60 > 0.075:
                classification_text += "Fine aggregate\n"
            else:
                classification_text += "Fines\n"
            
            # Gradation quality
            cc = params.get('Cc', 0)
            if 1 <= cc <= 3 and cu > 4:
                classification_text += "Good gradation"
            else:
                classification_text += "Gap graded or uniform"
            
            self.classification_label.set_markup(f'<span size="small">{classification_text}</span>')
            
        except Exception as e:
            self.logger.error(f"Failed to update classification: {e}")
    
    def _add_blend_component_row(self) -> None:
        """Add a new blend component row."""
        row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        row_box.set_margin_top(2)
        row_box.set_margin_bottom(2)
        
        # Aggregate selection
        agg_combo = Gtk.ComboBoxText()
        agg_combo.set_size_request(150, -1)
        
        # Load aggregates into combo
        try:
            aggregates = self.service_container.aggregate_service.get_all()
            for aggregate in aggregates:
                agg_combo.append(str(aggregate.id), aggregate.name)
        except Exception as e:
            self.logger.warning(f"Failed to load aggregates for blend: {e}")
        
        row_box.pack_start(agg_combo, False, False, 0)
        
        # Proportion
        prop_spin = Gtk.SpinButton.new_with_range(0.0, 100.0, 1.0)
        prop_spin.set_value(25.0)
        prop_spin.set_size_request(80, -1)
        row_box.pack_start(prop_spin, False, False, 0)
        
        # Percentage label
        percent_label = Gtk.Label("%")
        row_box.pack_start(percent_label, False, False, 0)
        
        # Remove button
        remove_button = Gtk.Button()
        remove_icon = create_icon_image("subtract", 16)
        remove_button.set_image(remove_icon)
        remove_button.set_relief(Gtk.ReliefStyle.NONE)
        
        # Connect remove signal
        remove_button.connect('clicked', lambda b: self.blend_components_box.remove(row_box))
        
        row_box.pack_start(remove_button, False, False, 0)
        
        # Add to components box
        self.blend_components_box.pack_start(row_box, False, False, 0)
        row_box.show_all()
    
    def _calculate_combined_grading(self) -> None:
        """Calculate combined grading from blend components."""
        try:
            # Get component data
            components = []
            for row_box in self.blend_components_box.get_children():
                children = row_box.get_children()
                if len(children) >= 3:
                    agg_combo = children[0]
                    prop_spin = children[1]
                    
                    agg_id = agg_combo.get_active_id()
                    proportion = prop_spin.get_value() / 100.0
                    
                    if agg_id and proportion > 0:
                        components.append((int(agg_id), proportion))
            
            if not components:
                self.main_window.update_status("No blend components defined", "warning", 3)
                return
            
            # Calculate combined grading
            combined_grading = self._blend_gradings(components)
            
            # Update combined grading widget
            self.combined_grading_widget.set_grading_data(combined_grading)
            
            self.main_window.update_status("Combined grading calculated successfully", "success", 3)
            
        except Exception as e:
            self.logger.error(f"Failed to calculate combined grading: {e}")
            self.main_window.update_status(f"Blend calculation failed: {e}", "error", 5)
    
    def _blend_gradings(self, components: List[Tuple[int, float]]) -> List[Tuple[float, float]]:
        """Blend multiple aggregate gradings."""
        try:
            # Get grading data for each component
            component_gradings = []
            
            for agg_id, proportion in components:
                try:
                    # Get aggregate from service
                    aggregate = self.service_container.aggregate_service.get_by_id(agg_id)
                    
                    # TODO: Get actual grading data from aggregate
                    # For now, create sample grading based on aggregate type
                    if "coarse" in aggregate.name.lower():
                        # Coarse aggregate grading
                        sample_grading = [
                            (25.0, 100.0), (19.0, 95.0), (12.5, 80.0), (9.5, 60.0),
                            (4.75, 15.0), (2.36, 5.0), (1.18, 2.0), (0.60, 1.0),
                            (0.30, 0.5), (0.15, 0.0), (0.075, 0.0)
                        ]
                    else:
                        # Fine aggregate grading
                        sample_grading = [
                            (25.0, 100.0), (19.0, 100.0), (12.5, 100.0), (9.5, 100.0),
                            (4.75, 95.0), (2.36, 80.0), (1.18, 65.0), (0.60, 45.0),
                            (0.30, 25.0), (0.15, 10.0), (0.075, 3.0)
                        ]
                    
                    component_gradings.append((sample_grading, proportion))
                    
                except Exception as e:
                    self.logger.warning(f"Failed to get grading for aggregate {agg_id}: {e}")
                    continue
            
            if not component_gradings:
                return []
            
            # Use the grading widget's blending method
            blended_grading = self.grading_widget.blend_gradings(component_gradings)
            
            return blended_grading
            
        except Exception as e:
            self.logger.error(f"Grading blending failed: {e}")
            return []
    
    def _normalize_blend_proportions(self) -> None:
        """Normalize blend proportions to sum to 100%."""
        try:
            # Get all proportion values
            total_proportion = 0.0
            prop_spins = []
            
            for row_box in self.blend_components_box.get_children():
                children = row_box.get_children()
                if len(children) >= 2:
                    prop_spin = children[1]
                    prop_spins.append(prop_spin)
                    total_proportion += prop_spin.get_value()
            
            if total_proportion == 0:
                return
            
            # Normalize each proportion
            for prop_spin in prop_spins:
                current_value = prop_spin.get_value()
                normalized_value = (current_value / total_proportion) * 100.0
                prop_spin.set_value(normalized_value)
            
            self.main_window.update_status("Blend proportions normalized", "success", 3)
            
        except Exception as e:
            self.logger.error(f"Failed to normalize blend proportions: {e}")
    
    def _import_grading_csv(self) -> None:
        """Import grading data from CSV file."""
        try:
            # Create file chooser dialog
            dialog = Gtk.FileChooserDialog(
                title="Import Grading Data",
                transient_for=self.main_window,
                action=Gtk.FileChooserAction.OPEN
            )
            dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
            dialog.add_button("Open", Gtk.ResponseType.OK)
            
            # Add file filter
            csv_filter = Gtk.FileFilter()
            csv_filter.set_name("CSV files")
            csv_filter.add_pattern("*.csv")
            dialog.add_filter(csv_filter)
            
            response = dialog.run()
            
            if response == Gtk.ResponseType.OK:
                file_path = dialog.get_filename()
                
                # Read CSV file
                grading_data = []
                with open(file_path, 'r', newline='') as csvfile:
                    reader = csv.reader(csvfile)
                    
                    # Skip header if present
                    first_row = next(reader, None)
                    if first_row and not self._is_numeric_row(first_row):
                        pass  # Skip header
                    else:
                        # First row is data, process it
                        if first_row and self._is_numeric_row(first_row):
                            size = float(first_row[0])
                            percent = float(first_row[1])
                            grading_data.append((size, percent))
                    
                    # Read remaining rows
                    for row in reader:
                        if len(row) >= 2 and self._is_numeric_row(row):
                            try:
                                size = float(row[0])
                                percent = float(row[1])
                                grading_data.append((size, percent))
                            except ValueError:
                                continue
                
                if grading_data:
                    # Sort by size (descending)
                    grading_data.sort(reverse=True)
                    
                    # Update grading widget
                    self.grading_widget.set_grading_data(grading_data)
                    self._update_gradation_parameters()
                    
                    self.main_window.update_status(f"Imported {len(grading_data)} data points from CSV", "success", 3)
                else:
                    self.main_window.update_status("No valid grading data found in CSV file", "warning", 3)
            
            dialog.destroy()
            
        except Exception as e:
            self.logger.error(f"CSV import failed: {e}")
            self.main_window.update_status(f"CSV import failed: {e}", "error", 5)
    
    def _export_grading_csv(self) -> None:
        """Export grading data to CSV file."""
        try:
            grading_data = self.grading_widget.get_grading_data()
            if not grading_data:
                self.main_window.update_status("No grading data to export", "warning", 3)
                return
            
            # Create file chooser dialog
            dialog = Gtk.FileChooserDialog(
                title="Export Grading Data",
                transient_for=self.main_window,
                action=Gtk.FileChooserAction.SAVE
            )
            dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
            dialog.add_button("Save", Gtk.ResponseType.OK)
            
            # Add file filter
            csv_filter = Gtk.FileFilter()
            csv_filter.set_name("CSV files")
            csv_filter.add_pattern("*.csv")
            dialog.add_filter(csv_filter)
            
            # Set default filename
            dialog.set_current_name("grading_data.csv")
            
            response = dialog.run()
            
            if response == Gtk.ResponseType.OK:
                file_path = dialog.get_filename()
                
                # Ensure .csv extension
                if not file_path.endswith('.csv'):
                    file_path += '.csv'
                
                # Write CSV file
                with open(file_path, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(['Sieve Size (mm)', 'Percent Passing'])
                    
                    for size, percent in grading_data:
                        writer.writerow([size, percent])
                
                self.main_window.update_status(f"Grading data exported to {file_path}", "success", 3)
            
            dialog.destroy()
            
        except Exception as e:
            self.logger.error(f"CSV export failed: {e}")
            self.main_window.update_status(f"CSV export failed: {e}", "error", 5)
    
    def _is_numeric_row(self, row: List[str]) -> bool:
        """Check if a CSV row contains numeric data."""
        if len(row) < 2:
            return False
        
        try:
            float(row[0])
            float(row[1])
            return True
        except ValueError:
            return False
    
    def _export_grading_data(self) -> None:
        """Export current grading data."""
        try:
            grading_data = self.grading_widget.get_grading_data()
            if not grading_data:
                self.main_window.update_status("No grading data to export", "warning", 3)
                return
            
            # Create export dialog
            dialog = Gtk.FileChooserDialog(
                title="Export Grading Data",
                transient_for=self.main_window,
                action=Gtk.FileChooserAction.SAVE
            )
            dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
            dialog.add_button("Save", Gtk.ResponseType.OK)
            
            # Add file filters
            csv_filter = Gtk.FileFilter()
            csv_filter.set_name("CSV files")
            csv_filter.add_pattern("*.csv")
            dialog.add_filter(csv_filter)
            
            json_filter = Gtk.FileFilter()
            json_filter.set_name("JSON files")
            json_filter.add_pattern("*.json")
            dialog.add_filter(json_filter)
            
            response = dialog.run()
            
            if response == Gtk.ResponseType.OK:
                file_path = dialog.get_filename()
                
                if file_path.endswith('.csv'):
                    self._export_to_csv(file_path, grading_data)
                else:
                    self._export_to_json(file_path, grading_data)
                
                self.main_window.update_status(f"Grading data exported to {file_path}", "success", 3)
            
            dialog.destroy()
            
        except Exception as e:
            self.logger.error(f"Failed to export grading data: {e}")
            self.main_window.update_status(f"Export failed: {e}", "error", 5)
    
    def _export_to_csv(self, file_path: str, grading_data: List[Tuple[float, float]]) -> None:
        """Export grading data to CSV."""
        with open(file_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Sieve Size (mm)', 'Percent Passing'])
            for size, percent in grading_data:
                writer.writerow([size, percent])
    
    def _export_to_json(self, file_path: str, grading_data: List[Tuple[float, float]]) -> None:
        """Export grading data to JSON."""
        data = {
            'grading_data': [{'size_mm': size, 'percent_passing': percent} for size, percent in grading_data],
            'parameters': self.grading_widget.get_gradation_parameters()
        }
        
        with open(file_path, 'w') as jsonfile:
            json.dump(data, jsonfile, indent=2)
    
    def _fit_grading_curve(self, fitting_type: str) -> None:
        """Fit a curve to the current grading data."""
        try:
            # Get current grading data from active widget
            if self.content_notebook.get_current_page() == 0:  # Single aggregate mode
                grading_widget = self.grading_widget
            else:
                self.main_window.update_status("Curve fitting only available in single aggregate mode", "warning", 3)
                return
            
            # Perform curve fitting
            result = grading_widget.fit_curve(fitting_type)
            
            if result:
                # Update results display
                results_text = f"Curve Fitting Results ({fitting_type}):\n\n"
                
                if 'parameters' in result:
                    results_text += "Parameters:\n"
                    for param, value in result['parameters'].items():
                        if isinstance(value, (int, float)):
                            results_text += f"  {param}: {value:.4f}\n"
                        else:
                            results_text += f"  {param}: {value}\n"
                    results_text += "\n"
                
                if 'r_squared' in result:
                    results_text += f"R-squared: {result['r_squared']:.4f}\n"
                    quality = "Excellent" if result['r_squared'] > 0.95 else \
                            "Good" if result['r_squared'] > 0.90 else \
                            "Fair" if result['r_squared'] > 0.80 else "Poor"
                    results_text += f"Fit Quality: {quality}\n"
                
                # Update results display
                self.results_textview.get_buffer().set_text(results_text)
                
                # Update gradation parameters
                self._update_gradation_parameters()
                
                self.main_window.update_status(f"Curve fitted successfully using {fitting_type}", "success", 3)
            else:
                self.main_window.update_status(f"Curve fitting failed - insufficient data or missing dependencies", "error", 5)
                
        except Exception as e:
            self.logger.error(f"Curve fitting failed: {e}")
            self.main_window.update_status(f"Curve fitting error: {e}", "error", 5)
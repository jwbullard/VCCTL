#!/usr/bin/env python3
"""
Unified PSD Widget

A reusable widget for displaying and editing particle size distributions
across all material types. Supports mathematical models and discrete data
with automatic conversion and table display.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject
import json
from typing import Dict, Any, Optional, List, Tuple, Callable

from app.services.psd_service import PSDService, PSDParameters, PSDType, DiscreteDistribution
import logging


class UnifiedPSDWidget(Gtk.Box):
    """
    Unified PSD widget for all material types.
    
    Features:
    - Mathematical model selection (Rosin-Rammler, log-normal, Fuller-Thompson)
    - Parameter input fields for each model type
    - Automatic conversion to discrete points
    - Editable table display of discrete data
    - CSV import/export functionality
    - Real-time preview and validation
    """
    
    def __init__(self, material_type: str = 'generic'):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        
        self.material_type = material_type
        self.logger = logging.getLogger(__name__)
        self.psd_service = PSDService()
        
        # Current PSD state
        self.current_parameters: Optional[PSDParameters] = None
        self.current_distribution: Optional[DiscreteDistribution] = None
        
        # Callbacks
        self.on_psd_changed: Optional[Callable] = None
        
        # Update tracking
        self._pending_update_id = None
        
        # UI components
        self.mode_combo: Optional[Gtk.ComboBoxText] = None
        self.parameter_stack: Optional[Gtk.Stack] = None
        self.table_store: Optional[Gtk.ListStore] = None
        self.table_view: Optional[Gtk.TreeView] = None
        self.summary_label: Optional[Gtk.Label] = None
        
        # Parameter input widgets
        self.rosin_rammler_widgets = {}
        self.log_normal_widgets = {}
        self.fuller_widgets = {}
        
        self._create_ui()
        self._setup_default_parameters()
    
    def _create_ui(self):
        """Create the complete UI for the PSD widget."""
        # Main container
        main_frame = Gtk.Frame()
        main_frame.set_label("Particle Size Distribution")
        main_frame.set_label_align(0.02, 0.5)
        
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        content_box.set_margin_left(10)
        content_box.set_margin_right(10)
        content_box.set_margin_top(10)
        content_box.set_margin_bottom(10)
        
        # Model selection
        self._create_mode_selection(content_box)
        
        # Parameter input stack
        self._create_parameter_stack(content_box)
        
        # Action buttons
        self._create_action_buttons(content_box)
        
        # Data table
        self._create_data_table(content_box)
        
        # Summary information
        self._create_summary(content_box)
        
        main_frame.add(content_box)
        self.pack_start(main_frame, True, True, 0)
    
    def _create_mode_selection(self, parent: Gtk.Box):
        """Create PSD model selection dropdown."""
        mode_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        mode_label = Gtk.Label("PSD Model:")
        mode_label.set_halign(Gtk.Align.START)
        mode_box.pack_start(mode_label, False, False, 0)
        
        self.mode_combo = Gtk.ComboBoxText()
        self.mode_combo.append("rosin_rammler", "Rosin-Rammler")
        self.mode_combo.append("log_normal", "Log-Normal")
        self.mode_combo.append("fuller", "Fuller-Thompson")
        self.mode_combo.append("custom", "Custom Points")
        # Don't set default here - will be set in _setup_default_parameters()
        self.mode_combo.connect('changed', self._on_mode_changed)
        
        mode_box.pack_start(self.mode_combo, False, False, 0)
        
        # Help button
        help_button = Gtk.Button.new_from_icon_name("help-about", Gtk.IconSize.BUTTON)
        help_button.set_tooltip_text("Show help for PSD models")
        help_button.connect('clicked', self._show_help)
        mode_box.pack_end(help_button, False, False, 0)
        
        parent.pack_start(mode_box, False, False, 0)
    
    def _create_parameter_stack(self, parent: Gtk.Box):
        """Create parameter input stack for different models."""
        self.parameter_stack = Gtk.Stack()
        self.parameter_stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        
        # Rosin-Rammler parameters
        self._create_rosin_rammler_params()
        
        # Log-normal parameters
        self._create_log_normal_params()
        
        # Fuller-Thompson parameters
        self._create_fuller_params()
        
        # Custom points (placeholder)
        custom_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        custom_label = Gtk.Label("Custom discrete points will be shown in the table below.")
        custom_label.set_markup("<i>Custom discrete points will be shown in the table below.</i>")
        custom_box.pack_start(custom_label, False, False, 0)
        self.parameter_stack.add_named(custom_box, "custom")
        
        parent.pack_start(self.parameter_stack, False, False, 0)
    
    def _create_rosin_rammler_params(self):
        """Create Rosin-Rammler parameter inputs."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        
        # Description
        desc_label = Gtk.Label()
        desc_label.set_markup("<i>Rosin-Rammler: R = 1 - exp(-(d/d₅₀)ⁿ)</i>")
        desc_label.set_halign(Gtk.Align.START)
        box.pack_start(desc_label, False, False, 0)
        
        # Parameter grid
        grid = Gtk.Grid()
        grid.set_column_spacing(10)
        grid.set_row_spacing(5)
        
        # D50 parameter
        d50_label = Gtk.Label("D₅₀ (μm):")
        d50_label.set_halign(Gtk.Align.END)
        d50_spin = Gtk.SpinButton.new_with_range(0.1, 100.0, 0.1)
        d50_spin.set_digits(1)
        d50_spin.set_value(15.0)
        d50_spin.connect('value-changed', self._on_parameter_changed)
        
        grid.attach(d50_label, 0, 0, 1, 1)
        grid.attach(d50_spin, 1, 0, 1, 1)
        
        # N parameter
        n_label = Gtk.Label("n:")
        n_label.set_halign(Gtk.Align.END)
        n_spin = Gtk.SpinButton.new_with_range(0.1, 5.0, 0.1)
        n_spin.set_digits(1)
        n_spin.set_value(1.4)
        n_spin.connect('value-changed', self._on_parameter_changed)
        
        grid.attach(n_label, 0, 1, 1, 1)
        grid.attach(n_spin, 1, 1, 1, 1)
        
        # Dmax parameter
        dmax_label = Gtk.Label("D_max (μm):")
        dmax_label.set_halign(Gtk.Align.END)
        dmax_spin = Gtk.SpinButton.new_with_range(1.0, 200.0, 1.0)
        dmax_spin.set_digits(0)
        dmax_spin.set_value(75.0)
        dmax_spin.connect('value-changed', self._on_parameter_changed)
        
        grid.attach(dmax_label, 0, 2, 1, 1)
        grid.attach(dmax_spin, 1, 2, 1, 1)
        
        self.rosin_rammler_widgets = {
            'd50': d50_spin,
            'n': n_spin,
            'dmax': dmax_spin
        }
        
        box.pack_start(grid, False, False, 0)
        self.parameter_stack.add_named(box, "rosin_rammler")
    
    def _create_log_normal_params(self):
        """Create log-normal parameter inputs."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        
        # Description
        desc_label = Gtk.Label()
        desc_label.set_markup("<i>Log-Normal distribution with median and standard deviation</i>")
        desc_label.set_halign(Gtk.Align.START)
        box.pack_start(desc_label, False, False, 0)
        
        # Parameter grid
        grid = Gtk.Grid()
        grid.set_column_spacing(10)
        grid.set_row_spacing(5)
        
        # Median parameter
        median_label = Gtk.Label("Median (μm):")
        median_label.set_halign(Gtk.Align.END)
        median_spin = Gtk.SpinButton.new_with_range(0.1, 100.0, 0.1)
        median_spin.set_digits(1)
        median_spin.set_value(10.0)
        median_spin.connect('value-changed', self._on_parameter_changed)
        
        grid.attach(median_label, 0, 0, 1, 1)
        grid.attach(median_spin, 1, 0, 1, 1)
        
        # Sigma parameter
        sigma_label = Gtk.Label("Std Dev:")
        sigma_label.set_halign(Gtk.Align.END)
        sigma_spin = Gtk.SpinButton.new_with_range(0.1, 10.0, 0.1)
        sigma_spin.set_digits(1)
        sigma_spin.set_value(2.0)
        sigma_spin.connect('value-changed', self._on_parameter_changed)
        
        grid.attach(sigma_label, 0, 1, 1, 1)
        grid.attach(sigma_spin, 1, 1, 1, 1)
        
        self.log_normal_widgets = {
            'median': median_spin,
            'sigma': sigma_spin
        }
        
        box.pack_start(grid, False, False, 0)
        self.parameter_stack.add_named(box, "log_normal")
    
    def _create_fuller_params(self):
        """Create Fuller-Thompson parameter inputs."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        
        # Description
        desc_label = Gtk.Label()
        desc_label.set_markup("<i>Fuller-Thompson: P = (d/D_max)^n</i>")
        desc_label.set_halign(Gtk.Align.START)
        box.pack_start(desc_label, False, False, 0)
        
        # Parameter grid
        grid = Gtk.Grid()
        grid.set_column_spacing(10)
        grid.set_row_spacing(5)
        
        # Exponent parameter
        exp_label = Gtk.Label("Exponent:")
        exp_label.set_halign(Gtk.Align.END)
        exp_spin = Gtk.SpinButton.new_with_range(0.1, 2.0, 0.1)
        exp_spin.set_digits(1)
        exp_spin.set_value(0.5)
        exp_spin.connect('value-changed', self._on_parameter_changed)
        
        grid.attach(exp_label, 0, 0, 1, 1)
        grid.attach(exp_spin, 1, 0, 1, 1)
        
        # Dmax parameter
        dmax_label = Gtk.Label("D_max (μm):")
        dmax_label.set_halign(Gtk.Align.END)
        dmax_spin = Gtk.SpinButton.new_with_range(1.0, 200.0, 1.0)
        dmax_spin.set_digits(0)
        dmax_spin.set_value(75.0)
        dmax_spin.connect('value-changed', self._on_parameter_changed)
        
        grid.attach(dmax_label, 0, 1, 1, 1)
        grid.attach(dmax_spin, 1, 1, 1, 1)
        
        self.fuller_widgets = {
            'exponent': exp_spin,
            'dmax': dmax_spin
        }
        
        box.pack_start(grid, False, False, 0)
        self.parameter_stack.add_named(box, "fuller")
    
    def _create_action_buttons(self, parent: Gtk.Box):
        """Create action buttons for PSD operations."""
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        
        # Generate/Update button
        generate_button = Gtk.Button("Generate Table")
        generate_button.set_tooltip_text("Generate discrete points from mathematical model")
        generate_button.connect('clicked', self._on_generate_clicked)
        button_box.pack_start(generate_button, False, False, 0)
        
        # Import CSV button
        import_button = Gtk.Button("Import CSV")
        import_button.set_tooltip_text("Import PSD data from CSV file")
        import_button.connect('clicked', self._on_import_csv)
        button_box.pack_start(import_button, False, False, 0)
        
        # Export CSV button
        export_button = Gtk.Button("Export CSV")
        export_button.set_tooltip_text("Export current PSD data to CSV file")
        export_button.connect('clicked', self._on_export_csv)
        button_box.pack_start(export_button, False, False, 0)
        
        parent.pack_start(button_box, False, False, 0)
    
    def _create_data_table(self, parent: Gtk.Box):
        """Create editable data table for discrete PSD points."""
        table_frame = Gtk.Frame()
        table_frame.set_label("Discrete PSD Data (Editable)")
        
        # Create table store: diameter, mass_fraction, percentage
        self.table_store = Gtk.ListStore(float, float, str)
        
        # Create tree view
        self.table_view = Gtk.TreeView(model=self.table_store)
        self.table_view.set_headers_visible(True)
        
        # Diameter column (editable)
        diameter_renderer = Gtk.CellRendererText()
        diameter_renderer.set_property("editable", True)
        diameter_renderer.connect("edited", self._on_diameter_edited)
        diameter_column = Gtk.TreeViewColumn("Diameter (μm)", diameter_renderer, text=0)
        diameter_column.set_min_width(100)
        self.table_view.append_column(diameter_column)
        
        # Mass fraction column (editable)
        fraction_renderer = Gtk.CellRendererText()
        fraction_renderer.set_property("editable", True)
        fraction_renderer.connect("edited", self._on_fraction_edited)
        fraction_column = Gtk.TreeViewColumn("Mass Fraction", fraction_renderer, text=1)
        fraction_column.set_min_width(100)
        self.table_view.append_column(fraction_column)
        
        # Percentage column (read-only)
        percentage_renderer = Gtk.CellRendererText()
        percentage_column = Gtk.TreeViewColumn("Percentage", percentage_renderer, text=2)
        percentage_column.set_min_width(100)
        self.table_view.append_column(percentage_column)
        
        # Scrolled window for table
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(200)
        scrolled.add(self.table_view)
        
        # Table button box
        table_button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        
        add_button = Gtk.Button("Add Point")
        add_button.connect('clicked', self._on_add_point)
        table_button_box.pack_start(add_button, False, False, 0)
        
        remove_button = Gtk.Button("Remove Point")
        remove_button.connect('clicked', self._on_remove_point)
        table_button_box.pack_start(remove_button, False, False, 0)
        
        normalize_button = Gtk.Button("Normalize")
        normalize_button.set_tooltip_text("Normalize mass fractions to sum to 1.0")
        normalize_button.connect('clicked', self._on_normalize)
        table_button_box.pack_end(normalize_button, False, False, 0)
        
        # Assemble table section
        table_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        table_box.pack_start(scrolled, True, True, 0)
        table_box.pack_start(table_button_box, False, False, 0)
        
        table_frame.add(table_box)
        parent.pack_start(table_frame, True, True, 0)
    
    def _create_summary(self, parent: Gtk.Box):
        """Create summary information display."""
        self.summary_label = Gtk.Label()
        self.summary_label.set_halign(Gtk.Align.START)
        self.summary_label.set_markup("<i>No PSD data loaded</i>")
        parent.pack_start(self.summary_label, False, False, 0)
    
    def _setup_default_parameters(self):
        """Setup default parameters based on material type."""
        # Set material-specific defaults and modes
        if self.material_type == 'fly_ash':
            # Fly ash typically uses log-normal
            mode = "log_normal"
            self.mode_combo.set_active_id(mode)
            self.parameter_stack.set_visible_child_name(mode)  # Ensure stack is updated
            self.log_normal_widgets['median'].set_value(5.0)
            self.log_normal_widgets['sigma'].set_value(2.0)
        elif self.material_type == 'slag':
            # Slag typically uses log-normal
            mode = "log_normal"
            self.mode_combo.set_active_id(mode)
            self.parameter_stack.set_visible_child_name(mode)  # Ensure stack is updated
            self.log_normal_widgets['median'].set_value(15.0)
            self.log_normal_widgets['sigma'].set_value(1.4)
        elif self.material_type == 'cement':
            # Cement typically uses Rosin-Rammler
            mode = "rosin_rammler"
            self.mode_combo.set_active_id(mode)
            self.parameter_stack.set_visible_child_name(mode)  # Ensure stack is updated
            self.rosin_rammler_widgets['d50'].set_value(20.0)
            self.rosin_rammler_widgets['n'].set_value(1.2)
        else:
            # Generic defaults use log-normal
            mode = "log_normal"
            self.mode_combo.set_active_id(mode)
            self.parameter_stack.set_visible_child_name(mode)  # Ensure stack is updated
            self.log_normal_widgets['median'].set_value(10.0)
            self.log_normal_widgets['sigma'].set_value(2.0)
        
        # Generate initial table
        self._on_generate_clicked(None)
    
    def _on_mode_changed(self, combo: Gtk.ComboBoxText):
        """Handle PSD model selection change."""
        model_id = combo.get_active_id()
        self.parameter_stack.set_visible_child_name(model_id)
        
        # Auto-generate table for mathematical models (immediate for mode changes)
        if model_id != 'custom':
            # Cancel any pending delayed update
            if self._pending_update_id:
                GObject.source_remove(self._pending_update_id)
                self._pending_update_id = None
            # Generate immediately for mode changes
            self._on_generate_clicked(None)
    
    def _on_parameter_changed(self, widget):
        """Handle parameter value changes."""
        # Cancel any pending update
        if self._pending_update_id:
            GObject.source_remove(self._pending_update_id)
        
        # For D_max and n parameters, use immediate update to fix consistency issues
        # These parameters have direct visual impact that users expect immediately
        param_name = "unknown"
        
        # Check all parameter widget dictionaries to identify the changed parameter
        if hasattr(self, 'rosin_rammler_widgets'):
            for name, w in self.rosin_rammler_widgets.items():
                if w == widget:
                    param_name = name
                    break
        
        if param_name == "unknown" and hasattr(self, 'log_normal_widgets'):
            for name, w in self.log_normal_widgets.items():
                if w == widget:
                    param_name = name
                    break
        
        if param_name == "unknown" and hasattr(self, 'fuller_widgets'):
            for name, w in self.fuller_widgets.items():
                if w == widget:
                    param_name = name
                    break
        
        # Critical parameters that need immediate updates for user responsiveness
        critical_params = ['dmax', 'n', 'median', 'sigma', 'exponent']
        
        if param_name in critical_params:
            # Immediate update for critical parameters
            self._on_generate_clicked(None)
        else:
            # Delayed update for less critical parameters to avoid excessive updates
            self._pending_update_id = GObject.timeout_add(150, self._delayed_generate)  # Reduced delay
    
    def _delayed_generate(self):
        """Delayed table generation to avoid excessive updates."""
        self._pending_update_id = None
        self._on_generate_clicked(None)
        return False  # Don't repeat
    
    def _on_generate_clicked(self, button):
        """Generate discrete points from current mathematical model."""
        try:
            model_id = self.mode_combo.get_active_id()
            
            if model_id == "rosin_rammler":
                params = PSDParameters(
                    psd_type=PSDType.ROSIN_RAMMLER,
                    d50=self.rosin_rammler_widgets['d50'].get_value(),
                    n=self.rosin_rammler_widgets['n'].get_value(),
                    dmax=self.rosin_rammler_widgets['dmax'].get_value()
                )
            elif model_id == "log_normal":
                params = PSDParameters(
                    psd_type=PSDType.LOG_NORMAL,
                    median=self.log_normal_widgets['median'].get_value(),
                    sigma=self.log_normal_widgets['sigma'].get_value()
                )
            elif model_id == "fuller":
                params = PSDParameters(
                    psd_type=PSDType.FULLER_THOMPSON,
                    exponent=self.fuller_widgets['exponent'].get_value(),
                    dmax=self.fuller_widgets['dmax'].get_value()
                )
            else:
                return  # Custom mode - don't auto-generate
            
            # Convert to discrete distribution
            distribution = self.psd_service.convert_to_discrete(params)
            
            # Update table
            self._update_table_from_distribution(distribution)
            
            # Store current state
            self.current_parameters = params
            self.current_distribution = distribution
            
            # Notify listeners
            if self.on_psd_changed:
                self.on_psd_changed()
                
        except Exception as e:
            self.logger.error(f"Failed to generate PSD: {e}")
            self._show_error(f"Failed to generate PSD: {e}")
    
    def _update_table_from_distribution(self, distribution: DiscreteDistribution):
        """Update table display from discrete distribution."""
        self.table_store.clear()
        
        for diameter, mass_fraction in distribution.points:
            percentage = f"{mass_fraction * 100:.2f}%"
            self.table_store.append([diameter, mass_fraction, percentage])
        
        self._update_summary(distribution)
    
    def _update_summary(self, distribution: DiscreteDistribution):
        """Update summary information display."""
        num_points = len(distribution.points)
        total_fraction = sum(distribution.mass_fractions)
        d50 = distribution.d50
        
        summary_text = f"<b>{num_points} points</b>, Total: {total_fraction:.4f}, D₅₀: {d50:.1f} μm"
        self.summary_label.set_markup(summary_text)
    
    def _on_diameter_edited(self, renderer, path, new_text):
        """Handle diameter cell editing."""
        try:
            new_diameter = float(new_text)
            if new_diameter <= 0:
                raise ValueError("Diameter must be positive")
            
            tree_iter = self.table_store.get_iter(path)
            old_diameter = self.table_store.get_value(tree_iter, 0)
            
            self.table_store.set_value(tree_iter, 0, new_diameter)
            self._recalculate_percentages()
            self._notify_table_changed()
            
        except ValueError as e:
            self._show_error(f"Invalid diameter: {e}")
    
    def _on_fraction_edited(self, renderer, path, new_text):
        """Handle mass fraction cell editing."""
        try:
            new_fraction = float(new_text)
            if new_fraction < 0:
                raise ValueError("Mass fraction must be non-negative")
            
            tree_iter = self.table_store.get_iter(path)
            self.table_store.set_value(tree_iter, 1, new_fraction)
            self._recalculate_percentages()
            self._notify_table_changed()
            
        except ValueError as e:
            self._show_error(f"Invalid mass fraction: {e}")
    
    def _recalculate_percentages(self):
        """Recalculate percentage column after data changes."""
        tree_iter = self.table_store.get_iter_first()
        while tree_iter:
            mass_fraction = self.table_store.get_value(tree_iter, 1)
            percentage = f"{mass_fraction * 100:.2f}%"
            self.table_store.set_value(tree_iter, 2, percentage)
            tree_iter = self.table_store.iter_next(tree_iter)
    
    def _on_add_point(self, button):
        """Add new point to table."""
        # Add at median diameter or reasonable default
        if self.table_store.iter_n_children(None) > 0:
            # Find good insertion point
            new_diameter = 10.0  # Default
        else:
            new_diameter = 10.0
        
        self.table_store.append([new_diameter, 0.0, "0.00%"])
        self._notify_table_changed()
    
    def _on_remove_point(self, button):
        """Remove selected point from table."""
        selection = self.table_view.get_selection()
        model, tree_iter = selection.get_selected()
        
        if tree_iter:
            model.remove(tree_iter)
            self._recalculate_percentages()
            self._notify_table_changed()
    
    def _on_normalize(self, button):
        """Normalize mass fractions to sum to 1.0."""
        # Calculate total
        total = 0.0
        tree_iter = self.table_store.get_iter_first()
        while tree_iter:
            fraction = self.table_store.get_value(tree_iter, 1)
            total += fraction
            tree_iter = self.table_store.iter_next(tree_iter)
        
        if total > 0:
            # Normalize
            tree_iter = self.table_store.get_iter_first()
            while tree_iter:
                fraction = self.table_store.get_value(tree_iter, 1)
                normalized = fraction / total
                self.table_store.set_value(tree_iter, 1, normalized)
                tree_iter = self.table_store.iter_next(tree_iter)
            
            self._recalculate_percentages()
            # Don't call _notify_table_changed() for normalize - it switches to custom mode
            # Instead just update the summary and notify listeners
            self._update_table_summary_only()
            if self.on_psd_changed:
                self.on_psd_changed()
    
    def _update_table_summary_only(self):
        """Update summary without changing mode or distribution."""
        if not self.table_store:
            return
            
        # Count points and calculate total
        num_points = self.table_store.iter_n_children(None)
        total_fraction = 0.0
        max_diameter = 0.0
        
        tree_iter = self.table_store.get_iter_first()
        while tree_iter:
            diameter = self.table_store.get_value(tree_iter, 0)
            fraction = self.table_store.get_value(tree_iter, 1)
            total_fraction += fraction
            max_diameter = max(max_diameter, diameter)
            tree_iter = self.table_store.iter_next(tree_iter)
        
        # Calculate approximate D50 from table data
        d50 = max_diameter / 2.0  # Simple approximation
        
        summary_text = f"<b>{num_points} points</b>, Total: {total_fraction:.4f}, D₅₀: {d50:.1f} μm"
        self.summary_label.set_markup(summary_text)
    
    def _notify_table_changed(self):
        """Notify that table data has changed."""
        # Update current distribution from table
        points = []
        tree_iter = self.table_store.get_iter_first()
        while tree_iter:
            diameter = self.table_store.get_value(tree_iter, 0)
            fraction = self.table_store.get_value(tree_iter, 1)
            points.append((diameter, fraction))
            tree_iter = self.table_store.iter_next(tree_iter)
        
        if points:
            try:
                self.current_distribution = self.psd_service._process_custom_points(points)
                self._update_summary(self.current_distribution)
                
                # Switch to custom mode
                self.mode_combo.set_active_id("custom")
                
                # Notify listeners
                if self.on_psd_changed:
                    self.on_psd_changed()
                    
            except Exception as e:
                self.logger.error(f"Failed to update distribution: {e}")
    
    def _on_import_csv(self, button):
        """Import PSD data from CSV file."""
        dialog = Gtk.FileChooserDialog(
            title="Import PSD Data",
            parent=self.get_toplevel(),
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )
        
        # Add CSV filter
        csv_filter = Gtk.FileFilter()
        csv_filter.set_name("CSV files")
        csv_filter.add_pattern("*.csv")
        dialog.add_filter(csv_filter)
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            distribution = self.psd_service.import_from_csv(filename)
            
            if distribution:
                self._update_table_from_distribution(distribution)
                self.current_distribution = distribution
                self.mode_combo.set_active_id("custom")
                
                if self.on_psd_changed:
                    self.on_psd_changed()
            else:
                self._show_error("Failed to import CSV file")
        
        dialog.destroy()
    
    def _on_export_csv(self, button):
        """Export current PSD data to CSV file."""
        if not self.current_distribution:
            self._show_error("No PSD data to export")
            return
        
        dialog = Gtk.FileChooserDialog(
            title="Export PSD Data",
            parent=self.get_toplevel(),
            action=Gtk.FileChooserAction.SAVE
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_SAVE, Gtk.ResponseType.OK
        )
        
        # Set default filename
        dialog.set_current_name(f"{self.material_type}_psd.csv")
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            success = self.psd_service.export_to_csv(self.current_distribution, filename)
            
            if not success:
                self._show_error("Failed to export CSV file")
        
        dialog.destroy()
    
    def _show_help(self, button):
        """Show help dialog for PSD models."""
        dialog = Gtk.MessageDialog(
            parent=self.get_toplevel(),
            flags=Gtk.DialogFlags.MODAL,
            type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            message_format="PSD Model Help"
        )
        
        help_text = """
<b>Rosin-Rammler:</b> R = 1 - exp(-(d/d₅₀)ⁿ)
- d₅₀: Characteristic diameter where 63.2% passes
- n: Distribution parameter (higher = narrower)

<b>Log-Normal:</b> Normal distribution of log(diameter)
- Median: D₅₀ value
- Std Dev: Distribution spread

<b>Fuller-Thompson:</b> P = (d/D_max)ⁿ
- Exponent: Usually 0.5 for ideal packing
- D_max: Maximum particle size

<b>Custom:</b> Direct input of discrete points
- Edit table cells directly
- Import from CSV files

<b>Diameter Bins:</b> Integer-centered ranges
- (0-1.5], (1.5-2.5], (2.5-3.5], etc.
- Optimized for genmic.c compatibility
"""
        
        dialog.format_secondary_markup(help_text)
        dialog.run()
        dialog.destroy()
    
    def _show_error(self, message: str):
        """Show error message dialog."""
        dialog = Gtk.MessageDialog(
            parent=self.get_toplevel(),
            flags=Gtk.DialogFlags.MODAL,
            type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            message_format="Error"
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()
    
    # Public interface methods
    
    def load_from_material_data(self, material_data: Dict[str, Any]):
        """Load PSD parameters from material data dictionary."""
        try:
            params = self.psd_service.parse_psd_from_material(material_data)
            
            # Set UI state based on parameters
            if params.psd_type == PSDType.ROSIN_RAMMLER:
                self.mode_combo.set_active_id("rosin_rammler")
                self.parameter_stack.set_visible_child_name("rosin_rammler")
                if params.d50:
                    self.rosin_rammler_widgets['d50'].set_value(params.d50)
                if params.n:
                    self.rosin_rammler_widgets['n'].set_value(params.n)
                if params.dmax:
                    self.rosin_rammler_widgets['dmax'].set_value(params.dmax)
            
            elif params.psd_type == PSDType.LOG_NORMAL:
                self.mode_combo.set_active_id("log_normal")
                self.parameter_stack.set_visible_child_name("log_normal")
                if params.median:
                    self.log_normal_widgets['median'].set_value(params.median)
                if params.sigma:
                    self.log_normal_widgets['sigma'].set_value(params.sigma)
            
            elif params.psd_type == PSDType.FULLER_THOMPSON:
                self.mode_combo.set_active_id("fuller")
                self.parameter_stack.set_visible_child_name("fuller")
                if params.exponent:
                    self.fuller_widgets['exponent'].set_value(params.exponent)
                if params.dmax:
                    self.fuller_widgets['dmax'].set_value(params.dmax)
            
            elif params.psd_type == PSDType.CUSTOM and params.custom_points:
                self.mode_combo.set_active_id("custom")
                self.parameter_stack.set_visible_child_name("custom")
                distribution = self.psd_service._process_custom_points(params.custom_points)
                self._update_table_from_distribution(distribution)
                self.current_distribution = distribution
                return
            
            # Generate distribution for mathematical models
            distribution = self.psd_service.convert_to_discrete(params)
            self._update_table_from_distribution(distribution)
            
            self.current_parameters = params
            self.current_distribution = distribution
            
        except Exception as e:
            self.logger.error(f"Failed to load PSD from material data: {e}")
    
    def get_material_data_dict(self) -> Dict[str, Any]:
        """Get current PSD state as material data dictionary."""
        data = {}
        
        model_id = self.mode_combo.get_active_id()
        data['psd_mode'] = model_id
        
        if model_id == "rosin_rammler":
            data['psd_d50'] = self.rosin_rammler_widgets['d50'].get_value()
            data['psd_n'] = self.rosin_rammler_widgets['n'].get_value()
            data['psd_dmax'] = self.rosin_rammler_widgets['dmax'].get_value()
        
        elif model_id == "log_normal":
            data['psd_median'] = self.log_normal_widgets['median'].get_value()
            data['psd_spread'] = self.log_normal_widgets['sigma'].get_value()
        
        elif model_id == "fuller":
            data['psd_exponent'] = self.fuller_widgets['exponent'].get_value()
            data['psd_dmax'] = self.fuller_widgets['dmax'].get_value()
        
        # Always include custom points (current table state)
        if self.current_distribution:
            data['psd_custom_points'] = json.dumps(self.current_distribution.points)
        
        return data
    
    def get_discrete_distribution(self) -> Optional[DiscreteDistribution]:
        """Get current discrete distribution."""
        return self.current_distribution
    
    def set_change_callback(self, callback: Callable):
        """Set callback function to be called when PSD data changes."""
        self.on_psd_changed = callback
#!/usr/bin/env python3
"""
Grading Curve Widget for VCCTL

Provides a widget for displaying and editing particle size distribution curves.
"""

import gi
import logging
import math
from typing import List, Tuple, Optional, Dict, Any

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, Gdk, Pango, cairo

# Standard sieve sizes (mm)
STANDARD_SIEVES = [
    (75.0, "75 mm"),
    (63.0, "63 mm"),
    (50.0, "50 mm"),
    (37.5, "37.5 mm"),
    (25.0, "25 mm"),
    (19.0, "19 mm"),
    (12.5, "12.5 mm"),
    (9.5, "9.5 mm"),
    (4.75, "No. 4"),
    (2.36, "No. 8"),
    (1.18, "No. 16"),
    (0.60, "No. 30"),
    (0.30, "No. 50"),
    (0.15, "No. 100"),
    (0.075, "No. 200")
]


class GradingCurveWidget(Gtk.Box):
    """Widget for displaying and editing particle size distribution curves."""
    
    # Custom signals
    __gsignals__ = {
        'curve-changed': (GObject.SignalFlags.RUN_FIRST, None, ()),
    }
    
    def __init__(self):
        """Initialize the grading curve widget."""
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        
        self.logger = logging.getLogger('VCCTL.GradingCurveWidget')
        
        # Grading data: list of (size_mm, percent_passing)
        self.grading_data = []
        
        # UI state
        self.plot_width = 400
        self.plot_height = 300
        self.margin = 40
        
        # Setup UI
        self._setup_ui()
        self._setup_default_data()
        
        self.logger.debug("Grading curve widget initialized")
    
    def _setup_ui(self) -> None:
        """Setup the widget UI."""
        # Create toolbar
        self._create_toolbar()
        
        # Create main content area
        main_paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        
        # Left side: sieve analysis table
        left_frame = Gtk.Frame(label="Sieve Analysis")
        left_frame.set_size_request(300, -1)
        self._create_sieve_table(left_frame)
        main_paned.pack1(left_frame, False, False)
        
        # Right side: grading curve plot
        right_frame = Gtk.Frame(label="Grading Curve")
        right_frame.set_size_request(450, -1)
        self._create_plot_area(right_frame)
        main_paned.pack2(right_frame, True, False)
        
        self.pack_start(main_paned, True, True, 0)
    
    def _create_toolbar(self) -> None:
        """Create the toolbar with controls."""
        toolbar_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        toolbar_box.set_margin_top(5)
        toolbar_box.set_margin_bottom(5)
        toolbar_box.set_margin_left(10)
        toolbar_box.set_margin_right(10)
        
        # Preset curves
        preset_label = Gtk.Label("Preset:")
        toolbar_box.pack_start(preset_label, False, False, 0)
        
        self.preset_combo = Gtk.ComboBoxText()
        self.preset_combo.append("custom", "Custom")
        self.preset_combo.append("well_graded", "Well Graded")
        self.preset_combo.append("gap_graded", "Gap Graded")
        self.preset_combo.append("uniform", "Uniform")
        self.preset_combo.set_active(0)
        self.preset_combo.connect('changed', self._on_preset_changed)
        toolbar_box.pack_start(self.preset_combo, False, False, 0)
        
        # Aggregate type
        type_label = Gtk.Label("Type:")
        toolbar_box.pack_start(type_label, False, False, 0)
        
        self.type_combo = Gtk.ComboBoxText()
        self.type_combo.append("combined", "Combined")
        self.type_combo.append("coarse", "Coarse")
        self.type_combo.append("fine", "Fine")
        self.type_combo.set_active(0)
        self.type_combo.connect('changed', self._on_type_changed)
        toolbar_box.pack_start(self.type_combo, False, False, 0)
        
        # Control buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        button_box.get_style_context().add_class("linked")
        
        normalize_button = Gtk.Button(label="Normalize")
        normalize_button.set_tooltip_text("Ensure curve is monotonic and normalized")
        normalize_button.connect('clicked', self._on_normalize_clicked)
        button_box.pack_start(normalize_button, False, False, 0)
        
        smooth_button = Gtk.Button(label="Smooth")
        smooth_button.set_tooltip_text("Smooth the grading curve")
        smooth_button.connect('clicked', self._on_smooth_clicked)
        button_box.pack_start(smooth_button, False, False, 0)
        
        toolbar_box.pack_end(button_box, False, False, 0)
        
        self.pack_start(toolbar_box, False, False, 0)
    
    def _create_sieve_table(self, parent: Gtk.Frame) -> None:
        """Create the sieve analysis table."""
        table_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        table_box.set_margin_top(10)
        table_box.set_margin_bottom(10)
        table_box.set_margin_left(10)
        table_box.set_margin_right(10)
        
        # Table headers
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        
        size_header = Gtk.Label("Sieve Size")
        size_header.set_size_request(120, -1)
        size_header.get_style_context().add_class("dim-label")
        header_box.pack_start(size_header, False, False, 0)
        
        passing_header = Gtk.Label("% Passing")
        passing_header.set_size_request(80, -1)
        passing_header.get_style_context().add_class("dim-label")
        header_box.pack_start(passing_header, False, False, 0)
        
        table_box.pack_start(header_box, False, False, 0)
        
        # Separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        table_box.pack_start(separator, False, False, 0)
        
        # Scrolled window for sieve entries
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_size_request(-1, 250)
        
        # Sieve entries container
        self.sieve_entries_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        scrolled.add(self.sieve_entries_box)
        
        table_box.pack_start(scrolled, True, True, 0)
        
        parent.add(table_box)
        
        # Create sieve entry rows
        self._create_sieve_entries()
    
    def _create_sieve_entries(self) -> None:
        """Create sieve entry rows."""
        self.sieve_entries = []
        
        for size_mm, size_label in STANDARD_SIEVES:
            entry_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
            entry_box.set_margin_top(1)
            entry_box.set_margin_bottom(1)
            
            # Size label
            size_label_widget = Gtk.Label(size_label)
            size_label_widget.set_size_request(120, -1)
            size_label_widget.set_halign(Gtk.Align.START)
            entry_box.pack_start(size_label_widget, False, False, 0)
            
            # Passing percentage entry
            passing_spin = Gtk.SpinButton.new_with_range(0.0, 100.0, 0.1)
            passing_spin.set_digits(1)
            passing_spin.set_size_request(80, -1)
            passing_spin.connect('value-changed', self._on_sieve_value_changed)
            entry_box.pack_start(passing_spin, False, False, 0)
            
            self.sieve_entries_box.pack_start(entry_box, False, False, 0)
            
            # Store entry data
            entry_data = {
                'size_mm': size_mm,
                'size_label': size_label,
                'box': entry_box,
                'spin': passing_spin
            }
            self.sieve_entries.append(entry_data)
    
    def _create_plot_area(self, parent: Gtk.Frame) -> None:
        """Create the grading curve plot area."""
        plot_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        plot_box.set_margin_top(10)
        plot_box.set_margin_bottom(10)
        plot_box.set_margin_left(10)
        plot_box.set_margin_right(10)
        
        # Drawing area for the plot
        self.drawing_area = Gtk.DrawingArea()
        # Ensure minimum valid size with safety bounds to prevent infinite surface size errors
        safe_width = max(100, min(self.plot_width, 800))  # Clamp between 100-800
        safe_height = max(100, min(self.plot_height, 600))  # Clamp between 100-600
        self.drawing_area.set_size_request(safe_width, safe_height)
        self.drawing_area.connect('draw', self._on_draw_plot)
        
        plot_box.pack_start(self.drawing_area, True, True, 0)
        
        # Plot controls
        controls_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        # Grid toggle
        self.show_grid_check = Gtk.CheckButton(label="Show Grid")
        self.show_grid_check.set_active(True)
        self.show_grid_check.connect('toggled', self._on_show_grid_toggled)
        controls_box.pack_start(self.show_grid_check, False, False, 0)
        
        # Log scale toggle
        self.log_scale_check = Gtk.CheckButton(label="Log Scale")
        self.log_scale_check.set_active(True)
        self.log_scale_check.connect('toggled', self._on_log_scale_toggled)
        controls_box.pack_start(self.log_scale_check, False, False, 0)
        
        plot_box.pack_start(controls_box, False, False, 0)
        
        parent.add(plot_box)
    
    def _setup_default_data(self) -> None:
        """Setup default grading data."""
        # Default well-graded curve
        default_data = [
            (75.0, 100.0),
            (50.0, 95.0),
            (25.0, 85.0),
            (19.0, 75.0),
            (12.5, 65.0),
            (9.5, 55.0),
            (4.75, 40.0),
            (2.36, 30.0),
            (1.18, 22.0),
            (0.60, 16.0),
            (0.30, 10.0),
            (0.15, 6.0),
            (0.075, 3.0)
        ]
        
        self.set_grading_data(default_data)
    
    def set_grading_data(self, data: List[Tuple[float, float]]) -> None:
        """Set the grading data and update the UI."""
        self.grading_data = data.copy()
        
        # Update sieve entries
        for entry in self.sieve_entries:
            size_mm = entry['size_mm']
            spin = entry['spin']
            
            # Find matching data point
            percent_passing = 0.0
            for data_size, data_percent in self.grading_data:
                if abs(data_size - size_mm) < 0.01:
                    percent_passing = data_percent
                    break
            
            spin.set_value(percent_passing)
        
        # Redraw plot
        self.drawing_area.queue_draw()
    
    def get_grading_data(self) -> List[Tuple[float, float]]:
        """Get the current grading data."""
        return self.grading_data.copy()
    
    def _update_grading_from_sieves(self) -> None:
        """Update grading data from sieve entries."""
        self.grading_data.clear()
        
        for entry in self.sieve_entries:
            size_mm = entry['size_mm']
            percent_passing = entry['spin'].get_value()
            
            if percent_passing > 0:  # Only include non-zero values
                self.grading_data.append((size_mm, percent_passing))
        
        # Sort by size (largest first)
        self.grading_data.sort(reverse=True)
        
        # Emit signal
        self.emit('curve-changed')
    
    def _on_sieve_value_changed(self, spin) -> None:
        """Handle sieve value change."""
        self._update_grading_from_sieves()
        self.drawing_area.queue_draw()
    
    def _on_preset_changed(self, combo) -> None:
        """Handle preset selection change."""
        preset = combo.get_active_id()
        
        if preset == "well_graded":
            data = [
                (75.0, 100.0), (50.0, 95.0), (25.0, 85.0), (19.0, 75.0),
                (12.5, 65.0), (9.5, 55.0), (4.75, 40.0), (2.36, 30.0),
                (1.18, 22.0), (0.60, 16.0), (0.30, 10.0), (0.15, 6.0), (0.075, 3.0)
            ]
        elif preset == "gap_graded":
            data = [
                (75.0, 100.0), (25.0, 90.0), (19.0, 85.0), (12.5, 80.0),
                (9.5, 40.0), (4.75, 35.0), (2.36, 30.0), (0.30, 8.0), (0.075, 2.0)
            ]
        elif preset == "uniform":
            data = [
                (25.0, 100.0), (19.0, 95.0), (12.5, 85.0), (9.5, 60.0),
                (4.75, 15.0), (2.36, 5.0), (0.075, 0.0)
            ]
        else:
            return  # Custom - don't change
        
        self.set_grading_data(data)
    
    def _on_type_changed(self, combo) -> None:
        """Handle aggregate type change."""
        # This could be used to filter available sieves or apply type-specific presets
        pass
    
    def _on_normalize_clicked(self, button) -> None:
        """Handle normalize button click."""
        if not self.grading_data:
            return
        
        # Sort data by size
        self.grading_data.sort(reverse=True)
        
        # Ensure monotonic decrease (larger sizes have higher % passing)
        for i in range(1, len(self.grading_data)):
            if self.grading_data[i][1] > self.grading_data[i-1][1]:
                # Fix by setting to previous value
                size = self.grading_data[i][0]
                percent = self.grading_data[i-1][1]
                self.grading_data[i] = (size, percent)
        
        # Update UI
        self.set_grading_data(self.grading_data)
        self.emit('curve-changed')
    
    def _on_smooth_clicked(self, button) -> None:
        """Handle smooth button click."""
        if len(self.grading_data) < 3:
            return
        
        # Simple smoothing: average with neighbors
        smoothed_data = []
        for i, (size, percent) in enumerate(self.grading_data):
            if i == 0 or i == len(self.grading_data) - 1:
                # Keep endpoints unchanged
                smoothed_data.append((size, percent))
            else:
                # Average with neighbors
                prev_percent = self.grading_data[i-1][1]
                next_percent = self.grading_data[i+1][1]
                smoothed_percent = (prev_percent + percent + next_percent) / 3.0
                smoothed_data.append((size, smoothed_percent))
        
        self.set_grading_data(smoothed_data)
        self.emit('curve-changed')
    
    def _on_show_grid_toggled(self, check) -> None:
        """Handle show grid toggle."""
        self.drawing_area.queue_draw()
    
    def _on_log_scale_toggled(self, check) -> None:
        """Handle log scale toggle."""
        self.drawing_area.queue_draw()
    
    def _on_draw_plot(self, widget, cr) -> bool:
        """Draw the grading curve plot."""
        try:
            # Get drawing area size
            allocation = widget.get_allocation()
            width = allocation.width
            height = allocation.height
            
            # Ensure we have valid dimensions - CRITICAL fix for infinite surface size errors
            if width <= 0 or height <= 0 or width > 32767 or height > 32767:
                self.logger.warning(f"Invalid drawing area size: {width}x{height}, skipping draw")
                return True  # Return True to prevent further rendering attempts
            
            # Additional safety check for extremely large values that could cause infinite surface errors
            if width > 10000 or height > 10000:
                self.logger.warning(f"Unexpectedly large drawing area: {width}x{height}, using safe defaults")
                width = min(width, 800)
                height = min(height, 600)
            
            # Clear background
            cr.set_source_rgb(1.0, 1.0, 1.0)
            cr.rectangle(0, 0, width, height)
            cr.fill()
            
            # Calculate plot area with safety checks
            plot_x = self.margin
            plot_y = self.margin
            plot_width = max(10, width - 2 * self.margin)  # Minimum 10px width
            plot_height = max(10, height - 2 * self.margin)  # Minimum 10px height
            
            # Draw plot border
            cr.set_source_rgb(0.0, 0.0, 0.0)
            cr.set_line_width(1.0)
            cr.rectangle(plot_x, plot_y, plot_width, plot_height)
            cr.stroke()
            
            # Draw grid if enabled
            if self.show_grid_check.get_active():
                self._draw_grid(cr, plot_x, plot_y, plot_width, plot_height)
            
            # Draw axes
            self._draw_axes(cr, plot_x, plot_y, plot_width, plot_height)
            
            # Draw grading curve
            if self.grading_data:
                self._draw_curve(cr, plot_x, plot_y, plot_width, plot_height)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to draw grading plot: {e}")
            return False
    
    def _draw_grid(self, cr, plot_x, plot_y, plot_width, plot_height) -> None:
        """Draw grid lines."""
        cr.set_source_rgba(0.8, 0.8, 0.8, 0.5)
        cr.set_line_width(0.5)
        
        # Vertical grid lines (percentage)
        for percent in [10, 20, 30, 40, 50, 60, 70, 80, 90]:
            x = plot_x + (percent / 100.0) * plot_width
            cr.move_to(x, plot_y)
            cr.line_to(x, plot_y + plot_height)
            cr.stroke()
        
        # Horizontal grid lines (size)
        if self.log_scale_check.get_active():
            # Log scale grid
            for size in [0.1, 1.0, 10.0]:
                if size <= 75.0:
                    y = self._size_to_y(size, plot_y, plot_height)
                    cr.move_to(plot_x, y)
                    cr.line_to(plot_x + plot_width, y)
                    cr.stroke()
        else:
            # Linear scale grid
            for size in [10, 20, 30, 40, 50, 60, 70]:
                if size <= 75.0:
                    y = self._size_to_y(size, plot_y, plot_height)
                    cr.move_to(plot_x, y)
                    cr.line_to(plot_x + plot_width, y)
                    cr.stroke()
    
    def _draw_axes(self, cr, plot_x, plot_y, plot_width, plot_height) -> None:
        """Draw axis labels."""
        cr.set_source_rgb(0.0, 0.0, 0.0)
        cr.set_font_size(10)
        
        # X-axis labels (percentage)
        for percent in [0, 20, 40, 60, 80, 100]:
            x = plot_x + (percent / 100.0) * plot_width
            cr.move_to(x - 8, plot_y + plot_height + 15)
            cr.show_text(f"{percent}%")
        
        # Y-axis labels (size)
        sizes = [0.075, 0.3, 1.18, 4.75, 19.0, 75.0] if self.log_scale_check.get_active() else [0, 15, 30, 45, 60, 75]
        for size in sizes:
            y = self._size_to_y(size, plot_y, plot_height)
            cr.move_to(plot_x - 25, y + 3)
            cr.show_text(f"{size}")
    
    def _draw_curve(self, cr, plot_x, plot_y, plot_width, plot_height) -> None:
        """Draw the grading curve."""
        if len(self.grading_data) < 2:
            return
        
        cr.set_source_rgb(0.2, 0.4, 0.8)
        cr.set_line_width(2.0)
        
        # Convert first point
        first_size, first_percent = self.grading_data[0]
        x = plot_x + (first_percent / 100.0) * plot_width
        y = self._size_to_y(first_size, plot_y, plot_height)
        cr.move_to(x, y)
        
        # Draw line to each subsequent point
        for size, percent in self.grading_data[1:]:
            x = plot_x + (percent / 100.0) * plot_width
            y = self._size_to_y(size, plot_y, plot_height)
            cr.line_to(x, y)
        
        cr.stroke()
        
        # Draw data points
        cr.set_source_rgb(0.8, 0.2, 0.2)
        for size, percent in self.grading_data:
            x = plot_x + (percent / 100.0) * plot_width
            y = self._size_to_y(size, plot_y, plot_height)
            cr.arc(x, y, 3.0, 0, 2 * math.pi)
            cr.fill()
    
    def _size_to_y(self, size, plot_y, plot_height) -> float:
        """Convert particle size to Y coordinate."""
        if self.log_scale_check.get_active():
            # Log scale (0.075 to 75.0 mm)
            if size <= 0:
                size = 0.075
            log_size = math.log10(size)
            log_min = math.log10(0.075)
            log_max = math.log10(75.0)
            ratio = (log_size - log_min) / (log_max - log_min)
        else:
            # Linear scale
            ratio = size / 75.0
        
        # Invert Y axis (larger sizes at top)
        return plot_y + plot_height * (1.0 - ratio)
    
    def get_gradation_parameters(self) -> Dict[str, float]:
        """Calculate gradation parameters from the curve."""
        if not self.grading_data:
            return {}
        
        # Sort data by size
        sorted_data = sorted(self.grading_data, key=lambda x: x[0])
        
        parameters = {}
        
        # Find D10, D30, D60 (sizes at 10%, 30%, 60% passing)
        for d_percent, param_name in [(10, 'D10'), (30, 'D30'), (60, 'D60')]:
            # Interpolate to find size at this percentage
            for i in range(len(sorted_data) - 1):
                size1, percent1 = sorted_data[i]
                size2, percent2 = sorted_data[i + 1]
                
                if percent1 <= d_percent <= percent2:
                    # Linear interpolation
                    if percent2 != percent1:
                        size = size1 + (size2 - size1) * (d_percent - percent1) / (percent2 - percent1)
                        parameters[param_name] = size
                    break
        
        # Calculate uniformity coefficient (Cu) and coefficient of gradation (Cc)
        if 'D10' in parameters and 'D60' in parameters and parameters['D10'] > 0:
            parameters['Cu'] = parameters['D60'] / parameters['D10']
            
            if 'D30' in parameters:
                parameters['Cc'] = (parameters['D30'] ** 2) / (parameters['D10'] * parameters['D60'])
        
        return parameters
    
    def fit_curve(self, fitting_type: str) -> Dict[str, Any]:
        """Fit a mathematical curve to the grading data."""
        if not self.grading_data or len(self.grading_data) < 3:
            return {}
        
        try:
            if fitting_type == "rosin_rammler":
                return self._fit_rosin_rammler()
            elif fitting_type == "gates_gaudin":
                return self._fit_gates_gaudin()
            elif fitting_type == "polynomial":
                return self._fit_polynomial()
            else:
                return {}
        
        except Exception as e:
            self.logger.error(f"Curve fitting failed: {e}")
            return {}
    
    def _fit_rosin_rammler(self) -> Dict[str, Any]:
        """Fit Rosin-Rammler distribution: R = exp(-(x/x_c)^n)"""
        try:
            import numpy as np
            from scipy.optimize import curve_fit
            
            # Extract data
            sizes = np.array([size for size, _ in self.grading_data])
            retained = np.array([100 - percent for _, percent in self.grading_data])
            
            # Remove zero values for log fitting
            mask = retained > 0
            sizes = sizes[mask]
            retained = retained[mask]
            
            if len(sizes) < 3:
                return {}
            
            # Rosin-Rammler function
            def rosin_rammler(x, x_c, n):
                return 100 * (1 - np.exp(-(x / x_c) ** n))
            
            # Initial guess
            x_c_guess = np.median(sizes)
            n_guess = 1.0
            
            # Fit curve
            popt, pcov = curve_fit(rosin_rammler, sizes, 100 - retained, 
                                 p0=[x_c_guess, n_guess], maxfev=2000)
            
            x_c, n = popt
            
            # Generate fitted curve
            size_range = np.logspace(np.log10(min(sizes)), np.log10(max(sizes)), 50)
            fitted_percent = rosin_rammler(size_range, x_c, n)
            
            # Update grading data with fitted curve
            fitted_data = [(size, percent) for size, percent in zip(size_range, fitted_percent)]
            self.set_grading_data(fitted_data)
            
            return {
                'type': 'rosin_rammler',
                'parameters': {'x_c': x_c, 'n': n},
                'r_squared': self._calculate_r_squared(sizes, 100 - retained, 
                                                     rosin_rammler(sizes, x_c, n))
            }
            
        except ImportError:
            self.logger.warning("NumPy/SciPy not available for curve fitting")
            return {}
        except Exception as e:
            self.logger.error(f"Rosin-Rammler fitting failed: {e}")
            return {}
    
    def _fit_gates_gaudin(self) -> Dict[str, Any]:
        """Fit Gates-Gaudin-Schumann distribution: P = (x/k)^m"""
        try:
            import numpy as np
            from scipy.optimize import curve_fit
            
            # Extract data
            sizes = np.array([size for size, _ in self.grading_data])
            percent_passing = np.array([percent for _, percent in self.grading_data])
            
            # Remove zero values
            mask = (sizes > 0) & (percent_passing > 0) & (percent_passing < 100)
            sizes = sizes[mask]
            percent_passing = percent_passing[mask]
            
            if len(sizes) < 3:
                return {}
            
            # Gates-Gaudin-Schumann function
            def gates_gaudin(x, k, m):
                return 100 * (x / k) ** m
            
            # Initial guess
            k_guess = max(sizes)
            m_guess = 0.5
            
            # Fit curve
            popt, pcov = curve_fit(gates_gaudin, sizes, percent_passing, 
                                 p0=[k_guess, m_guess], maxfev=2000)
            
            k, m = popt
            
            # Generate fitted curve
            size_range = np.linspace(min(sizes), max(sizes), 50)
            fitted_percent = np.clip(gates_gaudin(size_range, k, m), 0, 100)
            
            # Update grading data with fitted curve
            fitted_data = [(size, percent) for size, percent in zip(size_range, fitted_percent)]
            self.set_grading_data(fitted_data)
            
            return {
                'type': 'gates_gaudin',
                'parameters': {'k': k, 'm': m},
                'r_squared': self._calculate_r_squared(sizes, percent_passing, 
                                                     gates_gaudin(sizes, k, m))
            }
            
        except ImportError:
            self.logger.warning("NumPy/SciPy not available for curve fitting")
            return {}
        except Exception as e:
            self.logger.error(f"Gates-Gaudin fitting failed: {e}")
            return {}
    
    def _fit_polynomial(self, degree: int = 3) -> Dict[str, Any]:
        """Fit polynomial curve to grading data."""
        try:
            import numpy as np
            
            # Extract data
            sizes = np.array([math.log10(size) for size, _ in self.grading_data if size > 0])
            percent_passing = np.array([percent for size, percent in self.grading_data if size > 0])
            
            if len(sizes) < degree + 1:
                return {}
            
            # Fit polynomial
            coeffs = np.polyfit(sizes, percent_passing, degree)
            
            # Generate fitted curve
            size_range = np.logspace(np.min(sizes), np.max(sizes), 50)
            log_size_range = np.log10(size_range)
            fitted_percent = np.polyval(coeffs, log_size_range)
            fitted_percent = np.clip(fitted_percent, 0, 100)
            
            # Update grading data with fitted curve
            fitted_data = [(size, percent) for size, percent in zip(size_range, fitted_percent)]
            self.set_grading_data(fitted_data)
            
            # Calculate R-squared
            predicted = np.polyval(coeffs, sizes)
            r_squared = self._calculate_r_squared(percent_passing, predicted, predicted)
            
            return {
                'type': 'polynomial',
                'parameters': {'coefficients': coeffs.tolist(), 'degree': degree},
                'r_squared': r_squared
            }
            
        except ImportError:
            self.logger.warning("NumPy not available for polynomial fitting")
            return {}
        except Exception as e:
            self.logger.error(f"Polynomial fitting failed: {e}")
            return {}
    
    def _calculate_r_squared(self, y_actual, y_predicted, y_fitted) -> float:
        """Calculate R-squared value for curve fit."""
        try:
            import numpy as np
            
            y_actual = np.array(y_actual)
            y_fitted = np.array(y_fitted)
            
            # Calculate R-squared
            ss_res = np.sum((y_actual - y_fitted) ** 2)
            ss_tot = np.sum((y_actual - np.mean(y_actual)) ** 2)
            
            if ss_tot == 0:
                return 1.0
            
            r_squared = 1 - (ss_res / ss_tot)
            return float(np.clip(r_squared, 0, 1))
            
        except Exception:
            return 0.0
    
    def blend_gradings(self, component_gradings: List[Tuple[List[Tuple[float, float]], float]]) -> List[Tuple[float, float]]:
        """Blend multiple grading curves with specified proportions."""
        try:
            if not component_gradings:
                return []
            
            # Get all unique sieve sizes
            all_sizes = set()
            for grading, _ in component_gradings:
                for size, _ in grading:
                    all_sizes.add(size)
            
            # Sort sizes in descending order
            sorted_sizes = sorted(all_sizes, reverse=True)
            
            # Calculate blended grading
            blended_grading = []
            
            for target_size in sorted_sizes:
                total_weighted_passing = 0.0
                total_weight = 0.0
                
                for grading, proportion in component_gradings:
                    if proportion <= 0:
                        continue
                    
                    # Interpolate percent passing at target size
                    percent_passing = self._interpolate_percent_passing(grading, target_size)
                    
                    total_weighted_passing += percent_passing * proportion
                    total_weight += proportion
                
                if total_weight > 0:
                    blended_percent = total_weighted_passing / total_weight
                    blended_grading.append((target_size, blended_percent))
            
            return blended_grading
            
        except Exception as e:
            self.logger.error(f"Grading blending failed: {e}")
            return []
    
    def _interpolate_percent_passing(self, grading: List[Tuple[float, float]], target_size: float) -> float:
        """Interpolate percent passing at a target sieve size."""
        if not grading:
            return 0.0
        
        # Sort grading by size (descending)
        sorted_grading = sorted(grading, key=lambda x: x[0], reverse=True)
        
        # Check if target size is outside the range
        if target_size >= sorted_grading[0][0]:
            return sorted_grading[0][1]  # Largest size
        
        if target_size <= sorted_grading[-1][0]:
            return sorted_grading[-1][1]  # Smallest size
        
        # Find adjacent points for interpolation
        for i in range(len(sorted_grading) - 1):
            size1, percent1 = sorted_grading[i]
            size2, percent2 = sorted_grading[i + 1]
            
            if size2 <= target_size <= size1:
                # Linear interpolation
                if size1 != size2:
                    ratio = (target_size - size2) / (size1 - size2)
                    return percent2 + ratio * (percent1 - percent2)
                else:
                    return percent1
        
        return 0.0
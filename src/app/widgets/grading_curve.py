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

# Import Phase 1 services for template functionality
from app.services.grading_service import GradingService
from app.services.service_container import get_service_container
from app.models.grading import GradingType
from app.utils.grading_file_utils import grading_file_manager

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
        
        # Initialize grading service for template functionality
        try:
            service_container = get_service_container()
            self.grading_service = GradingService(service_container.database_service)
        except Exception as e:
            self.logger.warning(f"Failed to initialize grading service: {e}")
            self.grading_service = None
        
        # Grading data: list of (size_mm, percent_retained)
        self.grading_data = []
        
        # Template state
        self.current_template_name = None
        self.available_templates = []
        self._updating_template_selection = False  # Prevent recursive calls
        
        # UI state
        self.plot_width = 400
        self.plot_height = 300
        self.margin = 40
        
        # Setup UI
        self._setup_ui()
        self._setup_default_data()
        self._load_available_templates()
        
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
        
        # Template buttons
        template_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        template_box.get_style_context().add_class("linked")
        
        # Load template dropdown
        self.load_template_combo = Gtk.ComboBoxText()
        self.load_template_combo.set_tooltip_text("Load from saved grading template")
        self.load_template_combo.connect('changed', self._on_load_template_changed)
        template_box.pack_start(self.load_template_combo, False, False, 0)
        
        # Save template button
        self.save_template_button = Gtk.Button(label="Save As Template...")
        self.save_template_button.set_tooltip_text("Save current grading as reusable template")
        self.save_template_button.connect('clicked', self._on_save_template_clicked)
        template_box.pack_start(self.save_template_button, False, False, 0)
        
        toolbar_box.pack_end(template_box, False, False, 0)
        
        # Add separator
        separator1 = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        toolbar_box.pack_end(separator1, False, False, 0)
        
        # Import/Export buttons
        io_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        io_box.get_style_context().add_class("linked")
        
        # Import button
        import_button = Gtk.Button(label="Import...")
        import_button.set_tooltip_text("Import grading curve from .gdg file")
        import_button.connect('clicked', self._on_import_clicked)
        io_box.pack_start(import_button, False, False, 0)
        
        # Export button
        export_button = Gtk.Button(label="Export...")
        export_button.set_tooltip_text("Export grading curve to .gdg file")
        export_button.connect('clicked', self._on_export_clicked)
        io_box.pack_start(export_button, False, False, 0)
        
        toolbar_box.pack_end(io_box, False, False, 0)
        
        # Add separator
        separator2 = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        toolbar_box.pack_end(separator2, False, False, 0)
        
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
        
        passing_header = Gtk.Label("% Retained")
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
            
            # Retained percentage entry
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
        
        # Update sieve entries with more flexible matching
        for entry in self.sieve_entries:
            size_mm = entry['size_mm']
            spin = entry['spin']
            
            # Find matching data point with flexible tolerance
            percent_passing = 0.0
            best_match = None
            best_diff = float('inf')
            
            for data_size, data_percent in self.grading_data:
                # Try exact match first
                if abs(data_size - size_mm) < 0.001:
                    percent_passing = data_percent
                    break
                
                # Track closest match as backup
                diff = abs(data_size - size_mm)
                if diff < best_diff and diff < (size_mm * 0.1):  # Within 10% of sieve size
                    best_diff = diff
                    best_match = data_percent
            
            # If no exact match, use closest match if reasonable
            if percent_passing == 0.0 and best_match is not None:
                percent_passing = best_match
            
            # Block signals while setting value to prevent recursive calls
            spin.handler_block_by_func(self._on_sieve_value_changed)
            spin.set_value(percent_passing)
            spin.handler_unblock_by_func(self._on_sieve_value_changed)
        
        # Redraw plot
        self.drawing_area.queue_draw()
        
        # Try to find and select matching template (only if not already updating)
        if not self._updating_template_selection:
            self._select_matching_template()
    
    def get_grading_data(self) -> List[Tuple[float, float]]:
        """Get the current grading data."""
        return self.grading_data.copy()
    
    def load_from_grading_template(self, grading) -> bool:
        """Load grading data from a Grading model template.
        
        Args:
            grading: Grading model instance with sieve data
            
        Returns:
            bool: True if loaded successfully, False otherwise
        """
        try:
            if not grading:
                return False
                
            # Get sieve data from the grading model
            sieve_data = grading.get_sieve_data()
            if not sieve_data:
                self.logger.warning(f"No sieve data found in template: {grading.name}")
                return False
            
            # Convert to grading data format [(size_mm, percent_passing), ...]
            template_data = []
            for point in sieve_data:
                size_mm = float(point['sieve_size'])
                percent_passing = float(point['percent_passing'])
                template_data.append((size_mm, percent_passing))
            
            # Load the data
            self.set_grading_data(template_data)
            
            # Update template selection if template dropdown exists
            self._update_template_selection(grading.name)
            
            self.logger.info(f"Loaded grading template: {grading.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load grading template {getattr(grading, 'name', 'Unknown')}: {e}")
            return False
    
    def save_as_template(self, name: str, grading_type: GradingType, description: str = "") -> bool:
        """Save current grading data as a new template.
        
        Args:
            name: Template name
            grading_type: Type of grading (FINE or COARSE)
            description: Optional description
            
        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            if not self.grading_service:
                self.logger.error("Grading service not available")
                return False
                
            if not self.grading_data:
                self.logger.warning("No grading data to save")
                return False
            
            # Convert grading data to sieve data format
            sieve_data = []
            for size_mm, percent_passing in self.grading_data:
                sieve_data.append({
                    'sieve_size': size_mm,
                    'percent_passing': percent_passing
                })
            
            # Create new grading template
            grading = self.grading_service.create_grading(
                name=name,
                grading_type=grading_type,
                description=description,
                sieve_data=sieve_data,
                is_standard=False  # User-created templates are not standard
            )
            
            if grading:
                # Refresh available templates
                self._load_available_templates()
                self._update_template_selection(name)
                self.logger.info(f"Saved grading template: {name}")
                return True
            else:
                self.logger.error(f"Failed to create grading template: {name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to save template {name}: {e}")
            return False
    
    def _update_template_selection(self, template_name: str) -> None:
        """Update template dropdown selection to show the specified template."""
        if hasattr(self, 'load_template_combo'):
            # For ComboBoxText, we can use set_active_id with the template name directly
            try:
                self.load_template_combo.set_active_id(template_name)
                self.current_template_name = template_name
                self.logger.debug(f"Selected template in dropdown: {template_name}")
            except Exception as e:
                self.logger.warning(f"Could not select template {template_name} in dropdown: {e}")
                # Fallback: try to find it manually
                model = self.load_template_combo.get_model()
                if model:
                    for i in range(len(model)):
                        iter = model.get_iter([i])
                        template_id = model.get_value(iter, 0)  # ID is in column 0
                        if template_id == template_name:
                            self.load_template_combo.set_active_iter(iter)
                            self.current_template_name = template_name
                            break
    
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
        
        # Add axis titles
        cr.set_font_size(11)
        # X-axis title
        cr.move_to(plot_x + plot_width/2 - 40, plot_y + plot_height + 35)
        cr.show_text("Mass % Retained")
        # Y-axis title (rotated)
        cr.save()
        cr.move_to(plot_x - 35, plot_y + plot_height/2)
        cr.rotate(-math.pi/2)
        cr.show_text("Sieve Size (mm)")
        cr.restore()
    
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
    
    # Template Management Methods
    def _select_matching_template(self) -> None:
        """Find and select the template that matches current grading data."""
        if not self.grading_data or not self.available_templates or self._updating_template_selection:
            return
        
        # Set flag to prevent recursive calls
        self._updating_template_selection = True
        
        # Convert current data to comparable format
        current_points = sorted(self.grading_data, key=lambda x: x[0], reverse=True)
        
        for template in self.available_templates:
            sieve_data = template.get_sieve_data()
            if not sieve_data:
                continue
                
            # Convert template data to same format
            template_points = sorted(
                [(point['sieve_size'], point['percent_passing']) for point in sieve_data],
                key=lambda x: x[0], reverse=True
            )
            
            # Check if they match (with small tolerance for floating point)
            if len(current_points) == len(template_points):
                match = True
                for (curr_size, curr_percent), (tmpl_size, tmpl_percent) in zip(current_points, template_points):
                    if abs(curr_size - tmpl_size) > 0.001 or abs(curr_percent - tmpl_percent) > 0.1:
                        match = False
                        break
                
                if match:
                    # Found matching template - select it in the dropdown
                    self.current_template_name = template.name
                    # Block signal to prevent triggering load
                    self.load_template_combo.handler_block_by_func(self._on_load_template_changed)
                    self.load_template_combo.set_active_id(template.name)
                    self.load_template_combo.handler_unblock_by_func(self._on_load_template_changed)
                    self.logger.info(f"Selected matching template: {template.name}")
                    # Clear flag and return
                    self._updating_template_selection = False
                    return
        
        # No matching template found - clear selection
        self.current_template_name = None
        self.load_template_combo.handler_block_by_func(self._on_load_template_changed)
        self.load_template_combo.set_active_id("")
        self.load_template_combo.handler_unblock_by_func(self._on_load_template_changed)
        
        # Always clear the flag
        self._updating_template_selection = False
    
    def _load_available_templates(self) -> None:
        """Load available grading templates into the combo box."""
        if not self.grading_service:
            return
            
        try:
            # Remember current selection before clearing
            preserve_selection = self.current_template_name
            self.logger.info(f"_load_available_templates: Starting with current_template_name='{self.current_template_name}'")
            self.logger.info(f"_load_available_templates: preserve_selection='{preserve_selection}'")
            
            # Clear current templates
            self.load_template_combo.remove_all()
            self.available_templates.clear()
            
            # Add "Select template..." placeholder
            self.load_template_combo.append("", "Select template...")
            
            # Get available templates - force fresh query with no caching
            # This ensures we see recently committed templates
            all_gradings = self.grading_service.get_all_gradings_by_type()
            
            self.logger.info(f"_load_available_templates: Found {len(all_gradings)} total gradings from database")
            
            for grading in all_gradings:
                # Only include templates with actual sieve data
                if grading.has_grading_data:
                    self.logger.info(f"  Grading '{grading.name}' has data, adding to list")
                    
                    template_id = grading.name  # Keep ID as just the name
                    template_label = f"{grading.name}"
                    
                    # Add type indicator
                    if grading.type:
                        template_label += f" ({grading.type.value})"
                    
                    # Add standard indicator
                    if grading.is_system_grading:
                        template_label += " [Standard]"
                    
                    self.logger.info(f"  Adding to combo: id='{template_id}', label='{template_label}'")
                    # DEBUG: Log what we're about to append
                    self.logger.info(f"  About to call append({template_id}, {template_label})")
                    self.load_template_combo.append(template_id, template_label)
                    
                    # DEBUG: Immediately verify what was stored
                    model = self.load_template_combo.get_model()
                    if model and len(model) > 0:
                        last_iter = model.get_iter(len(model) - 1)
                        stored_id = model.get_value(last_iter, 0)  # ID column
                        stored_text = model.get_value(last_iter, 1)  # Text column
                        self.logger.info(f"  Verified stored: id='{stored_id}', text='{stored_text}'")
                    self.available_templates.append(grading)
                else:
                    self.logger.info(f"  Grading '{grading.name}' has NO data, skipping")
            
            # Log available templates for debugging
            self.logger.info(f"_load_available_templates: Available templates: {[g.name for g in self.available_templates]}")
            self.logger.info(f"_load_available_templates: Looking for: '{preserve_selection}'")
            
            # Restore previous selection or set to placeholder  
            if preserve_selection and preserve_selection in [g.name for g in self.available_templates]:
                self.logger.info(f"_load_available_templates: Template '{preserve_selection}' found in available templates")
                
                # Debug: Check what's actually in the combo box model
                model = self.load_template_combo.get_model()
                if model:
                    model_items = []
                    for i in range(model.iter_n_children(None)):
                        iter = model.get_iter([i])
                        row_id = model.get_value(iter, 0)
                        row_text = model.get_value(iter, 1)
                        model_items.append(f"[{i}]: id='{row_id}', text='{row_text}'")
                    
                    self.logger.info(f"_load_available_templates: Combo box has {len(model_items)} items: {model_items}")
                    
                    # Look for our template - need to match against stored ID which includes type info
                    found_index = -1
                    preserve_grading = None
                    
                    # Find the grading object for the preserve_selection
                    for grading in self.available_templates:
                        if grading.name == preserve_selection:
                            preserve_grading = grading
                            break
                    
                    if preserve_grading:
                        # Construct the expected stored ID (same logic as when we append)
                        expected_id = preserve_grading.name
                        expected_label = f"{preserve_grading.name}"
                        if preserve_grading.type:
                            expected_label += f" ({preserve_grading.type.value})"
                        if preserve_grading.is_system_grading:
                            expected_label += " [Standard]"
                        
                        self.logger.info(f"Looking for template with expected_id='{expected_id}' or stored_id_match='{expected_label}'")
                        
                        # Search for match - try both the intended ID and what might actually be stored
                        for i in range(model.iter_n_children(None)):
                            iter = model.get_iter([i])
                            row_id = model.get_value(iter, 0)
                            row_text = model.get_value(iter, 1)
                            
                            # Try multiple matching strategies
                            if (row_id == expected_id or  # ID should be plain name
                                row_id == expected_label or  # But might be full label
                                row_text == preserve_selection):  # Or match by text
                                found_index = i
                                self.logger.info(f"Found '{preserve_selection}' at index {i} (matched via row_id='{row_id}', row_text='{row_text}')")
                                break
                    else:
                        self.logger.warning(f"Could not find grading object for '{preserve_selection}'")
                    
                    if found_index == -1:
                        self.logger.error(f"Template '{preserve_selection}' NOT found in combo box model despite being in available_templates list!")
                else:
                    self.logger.error("No combo box model found!")
                
                if found_index >= 0:
                    # Block signal to prevent handler from interfering
                    self.load_template_combo.handler_block_by_func(self._on_load_template_changed)
                    
                    # Use set_active with the index
                    self.load_template_combo.set_active(found_index)
                    self.current_template_name = preserve_selection
                    
                    # Process pending GTK events to ensure the UI updates
                    while Gtk.events_pending():
                        Gtk.main_iteration_do(False)
                    
                    # Unblock signal
                    self.load_template_combo.handler_unblock_by_func(self._on_load_template_changed)
                    
                    # Verify it worked
                    active_index = self.load_template_combo.get_active()
                    active_id = self.load_template_combo.get_active_id()
                    active_text = self.load_template_combo.get_active_text()
                    self.logger.info(f"After setting index {found_index}: active_index={active_index}, id='{active_id}', text='{active_text}'")
                else:
                    self.logger.warning(f"Could not find '{preserve_selection}' in combo box model")
                    self.load_template_combo.set_active(0)
                    # DON'T reset current_template_name = None here - keep it for retries
            else:
                self.logger.info(f"_load_available_templates: No preserved selection or template not found. preserve_selection='{preserve_selection}', available={[g.name for g in self.available_templates]}")
                self.load_template_combo.set_active(0)  # Set to "Select template..." at index 0
                if not preserve_selection:
                    self.current_template_name = None
            
            self.logger.debug(f"Loaded {len(self.available_templates)} grading templates")
            
        except Exception as e:
            self.logger.error(f"Failed to load available templates: {e}")
    
    def get_current_template_name(self) -> Optional[str]:
        """Get the currently selected template name, if any."""
        return self.current_template_name
    
    def _on_load_template_changed(self, combo: Gtk.ComboBoxText) -> None:
        """Handle template selection from dropdown."""
        template_name = combo.get_active_id()
        
        if not template_name or template_name == "" or self._updating_template_selection:
            return
        
        # If user re-selects the same template, allow it (useful for refreshing)
        if template_name == self.current_template_name:
            self.logger.info(f"Re-selecting current template: {template_name}")
            # Continue to load it again
        
        try:
            # Find the selected grading
            selected_grading = None
            for grading in self.available_templates:
                if grading.name == template_name:
                    selected_grading = grading
                    break
            
            if not selected_grading:
                self.logger.warning(f"Template not found: {template_name}")
                return
            
            # Load the grading data
            sieve_data = selected_grading.get_sieve_data()
            if sieve_data:
                # Convert to widget format: [(size_mm, percent_passing), ...]
                grading_points = [(point['sieve_size'], point['percent_passing']) 
                                for point in sieve_data]
                
                # Set the data
                self.set_grading_data(grading_points)
                self.current_template_name = template_name
                
                # Update UI
                self.preset_combo.set_active_id("custom")
                
                # Emit change signal
                self.emit('curve-changed')
                
                self.logger.info(f"Loaded template: {template_name} ({len(grading_points)} points)")
            else:
                self.logger.warning(f"No sieve data in template: {template_name}")
                
        except Exception as e:
            self.logger.error(f"Failed to load template {template_name}: {e}")
            # On error, clear the template state but don't reset selection
            # This prevents partial state issues
            self.current_template_name = None
            
        # Note: No finally block - we want to keep the selection visible 
        # to show users which template is currently loaded
    
    def _on_save_template_clicked(self, button: Gtk.Button) -> None:
        """Handle save template button click."""
        if not self.grading_service:
            self._show_error("Service Unavailable", "Grading service not available")
            return
        
        if not self.grading_data or len(self.grading_data) < 2:
            self._show_error("Insufficient Data", "At least 2 sieve points required to save template")
            return
        
        # Show save dialog
        self._show_save_template_dialog()
    
    def _show_save_template_dialog(self) -> None:
        """Show dialog to save current grading as template."""
        # Get parent window
        parent = self.get_toplevel()
        if not isinstance(parent, Gtk.Window):
            parent = None
        
        dialog = Gtk.Dialog(
            title="Save Grading Template",
            parent=parent,
            flags=Gtk.DialogFlags.MODAL
        )
        
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_SAVE, Gtk.ResponseType.OK
        )
        
        # Dialog content
        content_area = dialog.get_content_area()
        content_area.set_spacing(10)
        content_area.set_margin_left(20)
        content_area.set_margin_right(20)
        content_area.set_margin_top(10)
        content_area.set_margin_bottom(10)
        
        # Info label
        info_text = f"Save current grading curve as reusable template\n"
        info_text += f"Current curve has {len(self.grading_data)} sieve points"
        info_label = Gtk.Label(info_text)
        content_area.pack_start(info_label, False, False, 0)
        
        # Input grid
        grid = Gtk.Grid()
        grid.set_column_spacing(10)
        grid.set_row_spacing(5)
        content_area.pack_start(grid, False, False, 0)
        
        # Name entry
        grid.attach(Gtk.Label("Name:"), 0, 0, 1, 1)
        name_entry = Gtk.Entry()
        name_entry.set_size_request(250, -1)
        name_entry.set_text(f"Grading_{len(self.grading_data)}_points")
        name_entry.select_region(0, -1)  # Select all
        grid.attach(name_entry, 1, 0, 1, 1)
        
        # Type combo
        grid.attach(Gtk.Label("Type:"), 0, 1, 1, 1)
        type_combo = Gtk.ComboBoxText()
        type_combo.append("FINE", "Fine Aggregate")
        type_combo.append("COARSE", "Coarse Aggregate")
        
        # Try to guess type from current data
        if self.grading_data:
            max_size = max(point[0] for point in self.grading_data)
            if max_size > 12.5:  # Coarse if largest size > 12.5mm
                type_combo.set_active_id("COARSE")
            else:
                type_combo.set_active_id("FINE")
        else:
            type_combo.set_active_id("FINE")
        
        grid.attach(type_combo, 1, 1, 1, 1)
        
        # Description entry
        grid.attach(Gtk.Label("Description:"), 0, 2, 1, 1)
        desc_entry = Gtk.Entry()
        desc_entry.set_text(f"Grading template with {len(self.grading_data)} sieve points")
        grid.attach(desc_entry, 1, 2, 1, 1)
        
        content_area.show_all()
        
        # Run dialog
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            try:
                # Get values
                name = name_entry.get_text().strip()
                grading_type = type_combo.get_active_id()
                description = desc_entry.get_text().strip()
                
                if not name:
                    raise ValueError("Template name is required")
                
                # Convert grading data to service format
                sieve_data = [{'sieve_size': point[0], 'percent_passing': point[1]} 
                             for point in self.grading_data]
                
                # Save template
                saved_grading = self.grading_service.save_grading_with_sieve_data(
                    name, grading_type, sieve_data, description
                )
                
                # Update current template name BEFORE refreshing
                self.current_template_name = name
                self.logger.debug(f"Set current_template_name to: {name}")
                
                # Force a small delay to ensure database commit is visible
                # This is a workaround for SQLAlchemy session isolation
                import time
                time.sleep(0.1)
                
                # Refresh templates and verify the new template appears and is selected
                # Sometimes there's a timing issue with database/UI sync
                max_retries = 3
                template_found = False
                
                for retry in range(max_retries):
                    self.logger.debug(f"Template refresh attempt {retry + 1}/{max_retries}")
                    
                    # Load templates - this will also set the selection via preserve_selection
                    self._load_available_templates()
                    
                    # Verify the template is selected
                    active_id = self.load_template_combo.get_active_id()
                    active_text = self.load_template_combo.get_active_text()
                    self.logger.info(f"After refresh {retry + 1}: active_id='{active_id}', active_text='{active_text}'")
                    
                    if active_id == name:
                        self.logger.info(f"Template '{name}' successfully selected")
                        template_found = True
                        break
                    else:
                        self.logger.warning(f"Template '{name}' not selected, retrying...")
                        # Small delay before retry
                        import time
                        time.sleep(0.1)
                
                if not template_found:
                    # Last resort: try to manually set the selection
                    self.logger.warning(f"Auto-selection failed after {max_retries} attempts, trying manual selection")
                    
                    # Check if template exists in combo box
                    model = self.load_template_combo.get_model()
                    if model:
                        for i in range(model.iter_n_children(None)):
                            iter = model.get_iter([i])
                            row_id = model.get_value(iter, 0)
                            if row_id == name:
                                self.load_template_combo.set_active(i)
                                final_id = self.load_template_combo.get_active_id()
                                self.logger.info(f"Manual selection: set index {i}, active_id is now '{final_id}'")
                                template_found = True
                                break
                
                if not template_found:
                    self.logger.error(f"Failed to select template '{name}' after all attempts")
                
                # Show success
                self._show_info("Template Saved", f"Grading template '{name}' saved successfully")
                
                self.logger.info(f"Saved grading template: {name}")
                
            except Exception as e:
                self.logger.error(f"Failed to save template: {e}")
                self._show_error("Save Failed", str(e))
        
        dialog.destroy()
    
    def _show_info(self, title: str, message: str) -> None:
        """Show info dialog."""
        parent = self.get_toplevel()
        if not isinstance(parent, Gtk.Window):
            parent = None
            
        dialog = Gtk.MessageDialog(
            parent=parent,
            flags=Gtk.DialogFlags.MODAL,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=title
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()
    
    def _show_error(self, title: str, message: str) -> None:
        """Show error dialog."""
        parent = self.get_toplevel()
        if not isinstance(parent, Gtk.Window):
            parent = None
            
        dialog = Gtk.MessageDialog(
            parent=parent,
            flags=Gtk.DialogFlags.MODAL,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=title
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()
    
    def refresh_templates(self) -> None:
        """Public method to refresh available templates (useful after external changes)."""
        self._load_available_templates()
    
    # Import/Export Methods
    def _on_import_clicked(self, button: Gtk.Button) -> None:
        """Handle import button click."""
        # File chooser for import
        parent = self.get_toplevel()
        if not isinstance(parent, Gtk.Window):
            parent = None
            
        dialog = Gtk.FileChooserDialog(
            title="Import Grading Curve",
            parent=parent,
            action=Gtk.FileChooserAction.OPEN
        )
        
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )
        
        # Add file filters
        filter_gdg = Gtk.FileFilter()
        filter_gdg.set_name("Grading files (*.gdg)")
        filter_gdg.add_pattern("*.gdg")
        dialog.add_filter(filter_gdg)
        
        filter_csv = Gtk.FileFilter()
        filter_csv.set_name("CSV files (*.csv)")
        filter_csv.add_pattern("*.csv")
        dialog.add_filter(filter_csv)
        
        filter_all = Gtk.FileFilter()
        filter_all.set_name("All files (*)")
        filter_all.add_pattern("*")
        dialog.add_filter(filter_all)
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            try:
                self._import_grading_file(filename)
                
            except Exception as e:
                self.logger.error(f"Failed to import grading file: {e}")
                self._show_error("Import Failed", str(e))
        
        dialog.destroy()
    
    def _import_grading_file(self, filename: str) -> None:
        """Import grading data from file."""
        import os
        
        file_ext = os.path.splitext(filename)[1].lower()
        
        if file_ext == '.gdg':
            # Use Phase 1 grading file manager
            sieve_data = grading_file_manager.read_gdg_file(filename)
            
            # Convert to widget format
            grading_points = [(point['sieve_size'], point['percent_passing']) 
                            for point in sieve_data]
            
        elif file_ext == '.csv':
            # Handle CSV format
            grading_points = self._import_csv_file(filename)
            
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")
        
        if grading_points:
            # Load the imported data
            self.set_grading_data(grading_points)
            self.current_template_name = None  # Clear template name since it's imported
            
            # Update UI
            self.preset_combo.set_active_id("custom")
            
            # Emit change signal
            self.emit('curve-changed')
            
            # Show success
            base_name = os.path.basename(filename)
            self._show_info("Import Successful", f"Imported {len(grading_points)} sieve points from {base_name}")
            
            self.logger.info(f"Imported grading from {filename} ({len(grading_points)} points)")
    
    def _import_csv_file(self, filename: str) -> List[Tuple[float, float]]:
        """Import grading data from CSV file."""
        import csv
        
        grading_points = []
        
        with open(filename, 'r', encoding='utf-8') as f:
            # Try to detect if file has headers
            sample = f.read(1024)
            f.seek(0)
            
            sniffer = csv.Sniffer()
            has_header = sniffer.has_header(sample)
            
            reader = csv.reader(f)
            
            if has_header:
                next(reader)  # Skip header row
            
            for row_num, row in enumerate(reader, 1):
                if len(row) < 2:
                    continue
                
                try:
                    # Expect: sieve_size, percent_passing
                    size = float(row[0].strip())
                    percent = float(row[1].strip())
                    
                    # Validation
                    if size < 0:
                        self.logger.warning(f"Invalid sieve size at row {row_num}: {size}")
                        continue
                    
                    if percent < 0 or percent > 100:
                        self.logger.warning(f"Invalid percent retained at row {row_num}: {percent}")
                        continue
                    
                    grading_points.append((size, percent))
                    
                except (ValueError, IndexError) as e:
                    self.logger.warning(f"Could not parse row {row_num}: {row} ({e})")
                    continue
        
        if not grading_points:
            raise ValueError("No valid sieve data found in CSV file")
        
        return grading_points
    
    def _on_export_clicked(self, button: Gtk.Button) -> None:
        """Handle export button click."""
        if not self.grading_data or len(self.grading_data) < 2:
            self._show_error("Insufficient Data", "At least 2 sieve points required to export")
            return
        
        # File chooser for export location
        parent = self.get_toplevel()
        if not isinstance(parent, Gtk.Window):
            parent = None
            
        dialog = Gtk.FileChooserDialog(
            title="Export Grading Curve",
            parent=parent,
            action=Gtk.FileChooserAction.SAVE
        )
        
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_SAVE, Gtk.ResponseType.OK
        )
        
        # Add file filters
        filter_gdg = Gtk.FileFilter()
        filter_gdg.set_name("Grading files (*.gdg)")
        filter_gdg.add_pattern("*.gdg")
        dialog.add_filter(filter_gdg)
        
        filter_csv = Gtk.FileFilter()
        filter_csv.set_name("CSV files (*.csv)")
        filter_csv.add_pattern("*.csv")
        dialog.add_filter(filter_csv)
        
        # Set default filename
        if self.current_template_name:
            default_name = f"{self.current_template_name}.gdg"
        else:
            default_name = f"grading_{len(self.grading_data)}_points.gdg"
        
        dialog.set_current_name(default_name)
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            try:
                self._export_grading_file(filename)
                
            except Exception as e:
                self.logger.error(f"Failed to export grading file: {e}")
                self._show_error("Export Failed", str(e))
        
        dialog.destroy()
    
    def _export_grading_file(self, filename: str) -> None:
        """Export grading data to file."""
        import os
        
        file_ext = os.path.splitext(filename)[1].lower()
        
        if file_ext == '.gdg':
            # Use Phase 1 grading file manager
            # Convert to service format
            sieve_data = [{'sieve_size': point[0], 'percent_passing': point[1]} 
                         for point in self.grading_data]
            
            # Write to file
            file_dir = os.path.dirname(filename)
            file_base = os.path.splitext(os.path.basename(filename))[0]
            
            created_path = grading_file_manager.write_gdg_file(
                file_dir, file_base, sieve_data, 
                self.type_combo.get_active_id() if hasattr(self, 'type_combo') else None
            )
            
        elif file_ext == '.csv':
            # Export as CSV
            self._export_csv_file(filename)
            created_path = filename
            
        else:
            # Default to .gdg format
            filename = os.path.splitext(filename)[0] + '.gdg'
            sieve_data = [{'sieve_size': point[0], 'percent_passing': point[1]} 
                         for point in self.grading_data]
            
            file_dir = os.path.dirname(filename)
            file_base = os.path.splitext(os.path.basename(filename))[0]
            
            created_path = grading_file_manager.write_gdg_file(
                file_dir, file_base, sieve_data,
                self.type_combo.get_active_id() if hasattr(self, 'type_combo') else None
            )
        
        # Show success
        base_name = os.path.basename(created_path)
        self._show_info("Export Successful", f"Exported {len(self.grading_data)} sieve points to {base_name}")
        
        self.logger.info(f"Exported grading to {created_path} ({len(self.grading_data)} points)")
    
    def _export_csv_file(self, filename: str) -> None:
        """Export grading data to CSV file."""
        import csv
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow(['Sieve Size (mm)', 'Percent Retained (%)'])
            
            # Write data (sorted by size, largest first)
            sorted_data = sorted(self.grading_data, key=lambda x: x[0], reverse=True)
            for size, percent in sorted_data:
                writer.writerow([f"{size:.3f}", f"{percent:.1f}"])
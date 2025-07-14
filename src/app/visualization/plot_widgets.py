#!/usr/bin/env python3
"""
Custom Plot Widgets for VCCTL

Specialized plot widgets for different types of VCCTL data visualization.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
import logging

from .plot_manager import PlotManager
from .plot_types import PlotType, PlotStyle, get_plot_config


class CustomPlotWidget(Gtk.Box):
    """
    Base class for custom plot widgets.
    
    Provides common functionality for specialized plot widgets.
    """
    
    __gsignals__ = {
        'data-changed': (GObject.SIGNAL_RUN_FIRST, None, ()),
        'plot-updated': (GObject.SIGNAL_RUN_FIRST, None, ()),
        'export-requested': (GObject.SIGNAL_RUN_FIRST, None, (str,)),
    }
    
    def __init__(self, plot_manager: PlotManager, plot_type: PlotType):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        
        self.plot_manager = plot_manager
        self.plot_type = plot_type
        self.logger = logging.getLogger(f'VCCTL.{self.__class__.__name__}')
        
        # Create plot widget
        self.plot_widget = self.plot_manager.create_plot_widget(plot_type)
        
        # Create control panel
        self.control_panel = self._create_control_panel()
        
        # Layout
        if self.control_panel:
            self.pack_start(self.control_panel, False, False, 0)
        self.pack_start(self.plot_widget, True, True, 0)
        
        # Data storage
        self.data = None
        
        self.show_all()
    
    def _create_control_panel(self) -> Optional[Gtk.Widget]:
        """Create control panel for plot customization. Override in subclasses."""
        return None
    
    def update_plot(self) -> bool:
        """Update plot with current data. Override in subclasses."""
        return False
    
    def set_data(self, data: Any):
        """Set plot data."""
        self.data = data
        self.emit('data-changed')
        return self.update_plot()
    
    def export_plot(self, file_path: str, format_type: str = 'png') -> bool:
        """Export plot to file."""
        success = self.plot_manager.export_plot(self.plot_widget, file_path, format_type)
        if success:
            self.emit('export-requested', file_path)
        return success
    
    def clear_plot(self):
        """Clear the plot."""
        self.plot_manager.clear_plot(self.plot_widget)
        self.data = None


class HydrationPlotWidget(CustomPlotWidget):
    """
    Specialized widget for hydration curve plots.
    
    Features:
    - Multiple hydration curves
    - Temperature effects
    - Time scale controls
    - Degree of hydration analysis
    """
    
    def __init__(self, plot_manager: PlotManager):
        super().__init__(plot_manager, PlotType.HYDRATION_CURVE)
        
        # Hydration-specific settings
        self.show_degree_of_hydration = True
        self.show_heat_evolution = False
        self.time_scale = 'days'  # 'hours', 'days', 'weeks'
        
    def _create_control_panel(self) -> Gtk.Widget:
        """Create hydration plot control panel."""
        frame = Gtk.Frame(label="Hydration Plot Controls")
        frame.set_shadow_type(Gtk.ShadowType.IN)
        
        grid = Gtk.Grid()
        grid.set_margin_top(6)
        grid.set_margin_bottom(6)
        grid.set_margin_left(6)
        grid.set_margin_right(6)
        grid.set_row_spacing(6)
        grid.set_column_spacing(12)
        
        # Time scale selection
        time_scale_label = Gtk.Label("Time Scale:")
        time_scale_label.set_halign(Gtk.Align.START)
        
        time_scale_combo = Gtk.ComboBoxText()
        time_scale_combo.append_text("Hours")
        time_scale_combo.append_text("Days")
        time_scale_combo.append_text("Weeks")
        time_scale_combo.set_active(1)  # Default to days
        time_scale_combo.connect('changed', self._on_time_scale_changed)
        
        grid.attach(time_scale_label, 0, 0, 1, 1)
        grid.attach(time_scale_combo, 1, 0, 1, 1)
        
        # Display options
        degree_check = Gtk.CheckButton("Show Degree of Hydration")
        degree_check.set_active(True)
        degree_check.connect('toggled', self._on_degree_toggled)
        
        heat_check = Gtk.CheckButton("Show Heat Evolution")
        heat_check.set_active(False)
        heat_check.connect('toggled', self._on_heat_toggled)
        
        grid.attach(degree_check, 0, 1, 2, 1)
        grid.attach(heat_check, 0, 2, 2, 1)
        
        # Export button
        export_button = Gtk.Button("Export Plot")
        export_button.connect('clicked', self._on_export_clicked)
        grid.attach(export_button, 0, 3, 2, 1)
        
        frame.add(grid)
        return frame
    
    def _on_time_scale_changed(self, combo):
        """Handle time scale change."""
        scale_map = {0: 'hours', 1: 'days', 2: 'weeks'}
        self.time_scale = scale_map[combo.get_active()]
        self.update_plot()
    
    def _on_degree_toggled(self, check_button):
        """Handle degree of hydration display toggle."""
        self.show_degree_of_hydration = check_button.get_active()
        self.update_plot()
    
    def _on_heat_toggled(self, check_button):
        """Handle heat evolution display toggle."""
        self.show_heat_evolution = check_button.get_active()
        self.update_plot()
    
    def _on_export_clicked(self, button):
        """Handle export button click."""
        dialog = Gtk.FileChooserDialog(
            title="Export Hydration Plot",
            parent=self.get_toplevel(),
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
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            file_path = dialog.get_filename()
            if file_path:
                # Determine format from extension
                format_type = file_path.split('.')[-1].lower()
                self.export_plot(file_path, format_type)
        
        dialog.destroy()
    
    def update_plot(self) -> bool:
        """Update hydration plot with current data."""
        if not self.data:
            return False
        
        try:
            # Convert time scale if needed
            time_data = self.data['time']
            if self.time_scale == 'hours':
                time_data = time_data * 24
            elif self.time_scale == 'weeks':
                time_data = time_data / 7
            
            # Plot degree of hydration if enabled
            if self.show_degree_of_hydration and 'degree_of_hydration' in self.data:
                self.plot_manager.plot_hydration_curve(
                    self.plot_widget,
                    time_data,
                    self.data['degree_of_hydration'],
                    label="Degree of Hydration",
                    color='blue'
                )
            
            # Add heat evolution if enabled and available
            if self.show_heat_evolution and 'heat_evolution' in self.data:
                # This would require a secondary y-axis
                pass
            
            self.emit('plot-updated')
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update hydration plot: {e}")
            return False


class ParticleSizeDistributionWidget(CustomPlotWidget):
    """
    Specialized widget for particle size distribution plots.
    
    Features:
    - Multiple gradation curves
    - Specification limits
    - D-values calculation
    - Fineness modulus display
    """
    
    def __init__(self, plot_manager: PlotManager):
        super().__init__(plot_manager, PlotType.PARTICLE_SIZE_DISTRIBUTION)
        
        # PSD-specific settings
        self.show_specification_limits = True
        self.show_d_values = True
        self.log_scale = True
        
    def _create_control_panel(self) -> Gtk.Widget:
        """Create PSD plot control panel."""
        frame = Gtk.Frame(label="Particle Size Distribution Controls")
        frame.set_shadow_type(Gtk.ShadowType.IN)
        
        grid = Gtk.Grid()
        grid.set_margin_top(6)
        grid.set_margin_bottom(6)
        grid.set_margin_left(6)
        grid.set_margin_right(6)
        grid.set_row_spacing(6)
        grid.set_column_spacing(12)
        
        # Display options
        spec_check = Gtk.CheckButton("Show Specification Limits")
        spec_check.set_active(True)
        spec_check.connect('toggled', self._on_spec_toggled)
        
        d_values_check = Gtk.CheckButton("Show D-Values")
        d_values_check.set_active(True)
        d_values_check.connect('toggled', self._on_d_values_toggled)
        
        log_scale_check = Gtk.CheckButton("Logarithmic X-Scale")
        log_scale_check.set_active(True)
        log_scale_check.connect('toggled', self._on_log_scale_toggled)
        
        grid.attach(spec_check, 0, 0, 2, 1)
        grid.attach(d_values_check, 0, 1, 2, 1)
        grid.attach(log_scale_check, 0, 2, 2, 1)
        
        # Statistics display
        stats_frame = Gtk.Frame(label="Statistics")
        stats_grid = Gtk.Grid()
        stats_grid.set_margin_top(6)
        stats_grid.set_margin_bottom(6)
        stats_grid.set_margin_left(6)
        stats_grid.set_margin_right(6)
        stats_grid.set_row_spacing(3)
        stats_grid.set_column_spacing(6)
        
        self.d10_label = Gtk.Label("D10: -")
        self.d50_label = Gtk.Label("D50: -")
        self.d90_label = Gtk.Label("D90: -")
        self.fineness_label = Gtk.Label("Fineness Modulus: -")
        
        stats_grid.attach(self.d10_label, 0, 0, 1, 1)
        stats_grid.attach(self.d50_label, 1, 0, 1, 1)
        stats_grid.attach(self.d90_label, 0, 1, 1, 1)
        stats_grid.attach(self.fineness_label, 1, 1, 1, 1)
        
        stats_frame.add(stats_grid)
        grid.attach(stats_frame, 0, 3, 2, 1)
        
        # Export button
        export_button = Gtk.Button("Export Plot")
        export_button.connect('clicked', self._on_export_clicked)
        grid.attach(export_button, 0, 4, 2, 1)
        
        frame.add(grid)
        return frame
    
    def _on_spec_toggled(self, check_button):
        """Handle specification limits display toggle."""
        self.show_specification_limits = check_button.get_active()
        self.update_plot()
    
    def _on_d_values_toggled(self, check_button):
        """Handle D-values display toggle."""
        self.show_d_values = check_button.get_active()
        self.update_plot()
    
    def _on_log_scale_toggled(self, check_button):
        """Handle log scale toggle."""
        self.log_scale = check_button.get_active()
        self.update_plot()
    
    def _on_export_clicked(self, button):
        """Handle export button click."""
        dialog = Gtk.FileChooserDialog(
            title="Export PSD Plot",
            parent=self.get_toplevel(),
            action=Gtk.FileChooserAction.SAVE
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_SAVE, Gtk.ResponseType.OK
        )
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            file_path = dialog.get_filename()
            if file_path:
                format_type = file_path.split('.')[-1].lower()
                self.export_plot(file_path, format_type)
        
        dialog.destroy()
    
    def _calculate_d_values(self, sizes, passing):
        """Calculate D10, D50, D90 values."""
        d_values = {}
        
        try:
            # Interpolate to find D-values
            d_values['d10'] = np.interp(10, passing, sizes)
            d_values['d50'] = np.interp(50, passing, sizes)
            d_values['d90'] = np.interp(90, passing, sizes)
            
            # Calculate fineness modulus (for aggregates)
            standard_sieves = [0.15, 0.3, 0.6, 1.18, 2.36, 4.75]  # mm
            cumulative_retained = []
            
            for sieve_size in standard_sieves:
                sieve_size_um = sieve_size * 1000  # Convert to μm
                retained = 100 - np.interp(sieve_size_um, sizes, passing)
                cumulative_retained.append(retained)
            
            d_values['fineness_modulus'] = sum(cumulative_retained) / 100
            
        except Exception as e:
            self.logger.error(f"Failed to calculate D-values: {e}")
            d_values = {'d10': 0, 'd50': 0, 'd90': 0, 'fineness_modulus': 0}
        
        return d_values
    
    def _update_statistics(self, sizes, passing):
        """Update statistics display."""
        d_values = self._calculate_d_values(sizes, passing)
        
        self.d10_label.set_text(f"D10: {d_values['d10']:.1f} μm")
        self.d50_label.set_text(f"D50: {d_values['d50']:.1f} μm")
        self.d90_label.set_text(f"D90: {d_values['d90']:.1f} μm")
        self.fineness_label.set_text(f"FM: {d_values['fineness_modulus']:.2f}")
    
    def update_plot(self) -> bool:
        """Update PSD plot with current data."""
        if not self.data:
            return False
        
        try:
            sizes = self.data['sizes']
            passing = self.data['passing']
            
            # Update statistics
            self._update_statistics(sizes, passing)
            
            # Plot main curve
            if self.log_scale:
                success = self.plot_manager.plot_particle_size_distribution(
                    self.plot_widget, sizes, passing,
                    label="Particle Size Distribution",
                    color='red'
                )
            else:
                # Would need to modify plot_manager for linear scale
                success = self.plot_manager.plot_particle_size_distribution(
                    self.plot_widget, sizes, passing,
                    label="Particle Size Distribution",
                    color='red'
                )
            
            # Add specification limits if enabled
            if self.show_specification_limits and 'spec_limits' in self.data:
                # Add specification limit curves
                pass
            
            self.emit('plot-updated')
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to update PSD plot: {e}")
            return False


class MicrostructurePlotWidget(CustomPlotWidget):
    """
    Specialized widget for microstructure visualization.
    
    Features:
    - 2D microstructure images
    - Phase coloring
    - Measurement tools
    - Statistics display
    """
    
    def __init__(self, plot_manager: PlotManager):
        super().__init__(plot_manager, PlotType.MICROSTRUCTURE_2D)
        
        # Microstructure-specific settings
        self.show_scale_bar = True
        self.color_map = 'viridis'
        self.show_phase_legend = True
        
    def _create_control_panel(self) -> Gtk.Widget:
        """Create microstructure plot control panel."""
        frame = Gtk.Frame(label="Microstructure Display Controls")
        frame.set_shadow_type(Gtk.ShadowType.IN)
        
        grid = Gtk.Grid()
        grid.set_margin_top(6)
        grid.set_margin_bottom(6)
        grid.set_margin_left(6)
        grid.set_margin_right(6)
        grid.set_row_spacing(6)
        grid.set_column_spacing(12)
        
        # Color map selection
        colormap_label = Gtk.Label("Color Map:")
        colormap_label.set_halign(Gtk.Align.START)
        
        colormap_combo = Gtk.ComboBoxText()
        colormaps = ['viridis', 'plasma', 'inferno', 'magma', 'jet', 'rainbow']
        for cmap in colormaps:
            colormap_combo.append_text(cmap)
        colormap_combo.set_active(0)
        colormap_combo.connect('changed', self._on_colormap_changed)
        
        grid.attach(colormap_label, 0, 0, 1, 1)
        grid.attach(colormap_combo, 1, 0, 1, 1)
        
        # Display options
        scale_check = Gtk.CheckButton("Show Scale Bar")
        scale_check.set_active(True)
        scale_check.connect('toggled', self._on_scale_toggled)
        
        legend_check = Gtk.CheckButton("Show Phase Legend")
        legend_check.set_active(True)
        legend_check.connect('toggled', self._on_legend_toggled)
        
        grid.attach(scale_check, 0, 1, 2, 1)
        grid.attach(legend_check, 0, 2, 2, 1)
        
        # Export button
        export_button = Gtk.Button("Export Image")
        export_button.connect('clicked', self._on_export_clicked)
        grid.attach(export_button, 0, 3, 2, 1)
        
        frame.add(grid)
        return frame
    
    def _on_colormap_changed(self, combo):
        """Handle colormap change."""
        colormaps = ['viridis', 'plasma', 'inferno', 'magma', 'jet', 'rainbow']
        self.color_map = colormaps[combo.get_active()]
        self.update_plot()
    
    def _on_scale_toggled(self, check_button):
        """Handle scale bar display toggle."""
        self.show_scale_bar = check_button.get_active()
        self.update_plot()
    
    def _on_legend_toggled(self, check_button):
        """Handle legend display toggle."""
        self.show_phase_legend = check_button.get_active()
        self.update_plot()
    
    def _on_export_clicked(self, button):
        """Handle export button click."""
        dialog = Gtk.FileChooserDialog(
            title="Export Microstructure Image",
            parent=self.get_toplevel(),
            action=Gtk.FileChooserAction.SAVE
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_SAVE, Gtk.ResponseType.OK
        )
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            file_path = dialog.get_filename()
            if file_path:
                format_type = file_path.split('.')[-1].lower()
                self.export_plot(file_path, format_type)
        
        dialog.destroy()
    
    def update_plot(self) -> bool:
        """Update microstructure plot with current data."""
        if not self.data:
            return False
        
        try:
            image_data = self.data['image']
            extent = self.data.get('extent')
            
            success = self.plot_manager.plot_2d_microstructure(
                self.plot_widget,
                image_data,
                extent=extent,
                cmap=self.color_map,
                colorbar=self.show_phase_legend
            )
            
            self.emit('plot-updated')
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to update microstructure plot: {e}")
            return False
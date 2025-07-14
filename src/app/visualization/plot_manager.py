#!/usr/bin/env python3
"""
Plot Manager for VCCTL Visualization

Central manager for all plotting functionality including matplotlib integration
with GTK3 and plot coordination.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject

import matplotlib
matplotlib.use('GTK3Agg')  # Use GTK3 backend for matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg as FigureCanvas
from matplotlib.backends.backend_gtk3 import NavigationToolbar2GTK3 as NavigationToolbar
from matplotlib.figure import Figure

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple, Callable
import logging
from pathlib import Path

from .plot_types import PlotType, PlotStyle, PlotConfiguration, get_plot_config, apply_plot_style
from .plot_export import PlotExporter


class PlotManager(GObject.Object):
    """
    Central manager for VCCTL plotting system.
    
    Features:
    - Matplotlib integration with GTK3
    - Multiple plot types and styles
    - Interactive controls
    - Export functionality
    - Plot management and coordination
    """
    
    __gsignals__ = {
        'plot-created': (GObject.SIGNAL_RUN_FIRST, None, (object,)),
        'plot-updated': (GObject.SIGNAL_RUN_FIRST, None, (object,)),
        'plot-exported': (GObject.SIGNAL_RUN_FIRST, None, (str,)),
    }
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.logger = logging.getLogger('VCCTL.PlotManager')
        
        # Plot storage
        self.plots = {}  # plot_id -> plot_info
        self.active_plots = {}  # widget -> plot_id
        
        # Plot exporter
        self.exporter = PlotExporter()
        
        # Default settings
        self.default_style = PlotStyle.SCIENTIFIC
        self.default_dpi = 100
        
        # Configure matplotlib for GTK3
        self._configure_matplotlib()
        
        self.logger.info("PlotManager initialized")
    
    def _configure_matplotlib(self):
        """Configure matplotlib for optimal GTK3 integration."""
        # Set backend
        matplotlib.use('GTK3Agg')
        
        # Configure default settings
        plt.rcParams['figure.dpi'] = self.default_dpi
        plt.rcParams['savefig.dpi'] = 300
        plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Helvetica', 'Arial']
        plt.rcParams['mathtext.fontset'] = 'dejavusans'
        
        # Enable interactive features
        plt.rcParams['figure.autolayout'] = True
        
        self.logger.debug("Matplotlib configured for GTK3")
    
    def create_plot_widget(self, plot_type: PlotType, parent_container: Gtk.Container = None) -> Gtk.Widget:
        """
        Create a new plot widget for the specified plot type.
        
        Args:
            plot_type: Type of plot to create
            parent_container: Parent container (optional)
            
        Returns:
            GTK widget containing the plot
        """
        plot_id = f"{plot_type.value}_{len(self.plots)}"
        config = get_plot_config(plot_type)
        
        # Create matplotlib figure and canvas
        figure = Figure(figsize=(8, 6), dpi=self.default_dpi)
        canvas = FigureCanvas(figure)
        canvas.set_size_request(600, 400)
        
        # Create navigation toolbar
        toolbar = NavigationToolbar(canvas)
        
        # Create container widget
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        vbox.pack_start(toolbar, False, False, 0)
        vbox.pack_start(canvas, True, True, 0)
        
        # Store plot information
        plot_info = {
            'id': plot_id,
            'type': plot_type,
            'config': config,
            'figure': figure,
            'canvas': canvas,
            'toolbar': toolbar,
            'widget': vbox,
            'axes': None,
            'data': None,
        }
        
        self.plots[plot_id] = plot_info
        self.active_plots[vbox] = plot_id
        
        # Add to parent if specified
        if parent_container:
            parent_container.add(vbox)
        
        self.emit('plot-created', plot_info)
        self.logger.debug(f"Created plot widget: {plot_id}")
        
        return vbox
    
    def get_plot_info(self, widget_or_id) -> Optional[Dict[str, Any]]:
        """Get plot information by widget or plot ID."""
        if isinstance(widget_or_id, str):
            return self.plots.get(widget_or_id)
        else:
            plot_id = self.active_plots.get(widget_or_id)
            return self.plots.get(plot_id) if plot_id else None
    
    def plot_hydration_curve(self, widget: Gtk.Widget, time_data: np.ndarray, 
                           hydration_data: np.ndarray, **kwargs) -> bool:
        """
        Plot hydration curve data.
        
        Args:
            widget: Plot widget
            time_data: Time values (days)
            hydration_data: Degree of hydration values
            **kwargs: Additional plot parameters
            
        Returns:
            Success status
        """
        plot_info = self.get_plot_info(widget)
        if not plot_info:
            return False
        
        try:
            figure = plot_info['figure']
            figure.clear()
            ax = figure.add_subplot(111)
            
            # Apply style
            apply_plot_style(ax, self.default_style)
            
            # Plot data
            line_style = kwargs.get('line_style', '-')
            color = kwargs.get('color', 'blue')
            label = kwargs.get('label', 'Hydration Progress')
            
            ax.plot(time_data, hydration_data, line_style, color=color, label=label, linewidth=2)
            
            # Configure plot
            config = plot_info['config']
            ax.set_xlabel(config.x_label)
            ax.set_ylabel(config.y_label)
            ax.set_title(config.title)
            
            if config.legend and label:
                ax.legend()
            
            if config.grid:
                ax.grid(True, alpha=0.3)
            
            # Set reasonable limits
            ax.set_xlim(0, max(time_data) * 1.05)
            ax.set_ylim(0, 1.05)
            
            # Store data
            plot_info['data'] = {
                'time': time_data,
                'hydration': hydration_data,
                'type': 'hydration_curve'
            }
            plot_info['axes'] = ax
            
            # Refresh canvas
            plot_info['canvas'].draw()
            
            self.emit('plot-updated', plot_info)
            self.logger.debug("Hydration curve plotted successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to plot hydration curve: {e}")
            return False
    
    def plot_particle_size_distribution(self, widget: Gtk.Widget, 
                                      size_data: np.ndarray, passing_data: np.ndarray,
                                      **kwargs) -> bool:
        """
        Plot particle size distribution.
        
        Args:
            widget: Plot widget
            size_data: Particle sizes (μm)
            passing_data: Cumulative passing (%)
            **kwargs: Additional plot parameters
            
        Returns:
            Success status
        """
        plot_info = self.get_plot_info(widget)
        if not plot_info:
            return False
        
        try:
            figure = plot_info['figure']
            figure.clear()
            ax = figure.add_subplot(111)
            
            # Apply style
            apply_plot_style(ax, self.default_style)
            
            # Plot data
            line_style = kwargs.get('line_style', '-')
            color = kwargs.get('color', 'red')
            label = kwargs.get('label', 'Particle Size Distribution')
            
            ax.semilogx(size_data, passing_data, line_style, color=color, label=label, linewidth=2)
            
            # Configure plot
            config = plot_info['config']
            ax.set_xlabel(config.x_label)
            ax.set_ylabel(config.y_label)
            ax.set_title(config.title)
            
            if config.legend and label:
                ax.legend()
            
            if config.grid:
                ax.grid(True, alpha=0.3)
            
            # Set reasonable limits
            ax.set_xlim(min(size_data) * 0.9, max(size_data) * 1.1)
            ax.set_ylim(0, 105)
            
            # Store data
            plot_info['data'] = {
                'size': size_data,
                'passing': passing_data,
                'type': 'particle_size_distribution'
            }
            plot_info['axes'] = ax
            
            # Refresh canvas
            plot_info['canvas'].draw()
            
            self.emit('plot-updated', plot_info)
            self.logger.debug("Particle size distribution plotted successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to plot particle size distribution: {e}")
            return False
    
    def plot_multiple_series(self, widget: Gtk.Widget, data_series: List[Dict[str, Any]],
                           plot_type: PlotType, **kwargs) -> bool:
        """
        Plot multiple data series on the same plot.
        
        Args:
            widget: Plot widget
            data_series: List of data series, each containing x, y, and metadata
            plot_type: Type of plot
            **kwargs: Additional plot parameters
            
        Returns:
            Success status
        """
        plot_info = self.get_plot_info(widget)
        if not plot_info:
            return False
        
        try:
            figure = plot_info['figure']
            figure.clear()
            ax = figure.add_subplot(111)
            
            # Apply style
            apply_plot_style(ax, self.default_style)
            
            # Plot each series
            colors = plt.cm.tab10(np.linspace(0, 1, len(data_series)))
            
            for i, series in enumerate(data_series):
                x_data = series['x']
                y_data = series['y']
                label = series.get('label', f'Series {i+1}')
                line_style = series.get('line_style', '-')
                color = series.get('color', colors[i])
                
                ax.plot(x_data, y_data, line_style, color=color, label=label, linewidth=2)
            
            # Configure plot based on type
            config = get_plot_config(plot_type)
            ax.set_xlabel(config.x_label)
            ax.set_ylabel(config.y_label)
            ax.set_title(config.title)
            
            if config.legend:
                ax.legend()
            
            if config.grid:
                ax.grid(True, alpha=0.3)
            
            # Store data
            plot_info['data'] = {
                'series': data_series,
                'type': f'multiple_{plot_type.value}'
            }
            plot_info['axes'] = ax
            
            # Refresh canvas
            plot_info['canvas'].draw()
            
            self.emit('plot-updated', plot_info)
            self.logger.debug(f"Multiple series plot created for {plot_type.value}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to plot multiple series: {e}")
            return False
    
    def plot_2d_microstructure(self, widget: Gtk.Widget, image_data: np.ndarray,
                             extent: Tuple[float, float, float, float] = None,
                             **kwargs) -> bool:
        """
        Plot 2D microstructure image.
        
        Args:
            widget: Plot widget
            image_data: 2D array representing microstructure
            extent: (left, right, bottom, top) extent in μm
            **kwargs: Additional plot parameters
            
        Returns:
            Success status
        """
        plot_info = self.get_plot_info(widget)
        if not plot_info:
            return False
        
        try:
            figure = plot_info['figure']
            figure.clear()
            ax = figure.add_subplot(111)
            
            # Apply style
            apply_plot_style(ax, self.default_style)
            
            # Plot image
            cmap = kwargs.get('cmap', 'viridis')
            interpolation = kwargs.get('interpolation', 'nearest')
            
            if extent:
                im = ax.imshow(image_data, cmap=cmap, interpolation=interpolation, 
                             extent=extent, origin='lower')
            else:
                im = ax.imshow(image_data, cmap=cmap, interpolation=interpolation, 
                             origin='lower')
            
            # Add colorbar
            if kwargs.get('colorbar', True):
                figure.colorbar(im, ax=ax, label=kwargs.get('colorbar_label', 'Phase'))
            
            # Configure plot
            config = plot_info['config']
            ax.set_xlabel(config.x_label)
            ax.set_ylabel(config.y_label)
            ax.set_title(config.title)
            ax.set_aspect('equal')
            
            # Store data
            plot_info['data'] = {
                'image': image_data,
                'extent': extent,
                'type': 'microstructure_2d'
            }
            plot_info['axes'] = ax
            
            # Refresh canvas
            plot_info['canvas'].draw()
            
            self.emit('plot-updated', plot_info)
            self.logger.debug("2D microstructure plotted successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to plot 2D microstructure: {e}")
            return False
    
    def export_plot(self, widget: Gtk.Widget, file_path: str, format_type: str = 'png',
                   dpi: int = 300) -> bool:
        """
        Export plot to file.
        
        Args:
            widget: Plot widget
            file_path: Output file path
            format_type: Export format
            dpi: Resolution for raster formats
            
        Returns:
            Success status
        """
        plot_info = self.get_plot_info(widget)
        if not plot_info:
            return False
        
        try:
            figure = plot_info['figure']
            
            # Export using the plot exporter
            success = self.exporter.export_figure(figure, file_path, format_type, dpi)
            
            if success:
                self.emit('plot-exported', file_path)
                self.logger.info(f"Plot exported to: {file_path}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to export plot: {e}")
            return False
    
    def clear_plot(self, widget: Gtk.Widget) -> bool:
        """Clear a plot."""
        plot_info = self.get_plot_info(widget)
        if not plot_info:
            return False
        
        try:
            figure = plot_info['figure']
            figure.clear()
            plot_info['canvas'].draw()
            plot_info['data'] = None
            plot_info['axes'] = None
            
            self.logger.debug("Plot cleared")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to clear plot: {e}")
            return False
    
    def set_plot_style(self, style: PlotStyle):
        """Set default plot style."""
        self.default_style = style
        self.logger.debug(f"Plot style set to: {style.value}")
    
    def get_plot_data(self, widget: Gtk.Widget) -> Optional[Dict[str, Any]]:
        """Get plot data for analysis or export."""
        plot_info = self.get_plot_info(widget)
        return plot_info['data'] if plot_info else None
    
    def remove_plot(self, widget: Gtk.Widget) -> bool:
        """Remove plot from manager."""
        plot_id = self.active_plots.get(widget)
        if plot_id:
            del self.plots[plot_id]
            del self.active_plots[widget]
            self.logger.debug(f"Removed plot: {plot_id}")
            return True
        return False
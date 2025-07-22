#!/usr/bin/env python3
"""
3D Microstructure Visualization for VCCTL

Provides 3D visualization capabilities for cement microstructure data using
matplotlib's 3D plotting capabilities and optional OpenGL-based rendering.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject

import matplotlib
matplotlib.use('GTK3Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg as FigureCanvas
from matplotlib.backends.backend_gtk3 import NavigationToolbar2GTK3 as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib.colors import ListedColormap

import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Union
import logging
from pathlib import Path

from .plot_types import PlotType, PlotStyle, ExportFormat


class Microstructure3DViewer(Gtk.Box):
    """
    3D Microstructure Visualization Widget
    
    Features:
    - 3D voxel rendering
    - Phase-based coloring
    - Interactive rotation and zoom
    - Cross-sectional views
    - Animation capabilities
    - Export to various formats
    """
    
    __gsignals__ = {
        'data-loaded': (GObject.SIGNAL_RUN_FIRST, None, ()),
        'view-changed': (GObject.SIGNAL_RUN_FIRST, None, ()),
        'animation-frame': (GObject.SIGNAL_RUN_FIRST, None, (int,)),
    }
    
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        
        self.logger = logging.getLogger('VCCTL.Microstructure3DViewer')
        
        # 3D data storage
        self.voxel_data = None
        self.phase_mapping = {}
        self.voxel_size = (1.0, 1.0, 1.0)  # μm per voxel
        
        # Visualization settings
        self.current_view = 'isometric'
        self.show_axes = True
        self.show_colorbar = True
        self.alpha_value = 0.6  # More transparent for better visibility
        self.phase_colors = {}
        
        # Animation settings
        self.animation_active = False
        self.animation_speed = 50  # ms per frame
        
        # Create 3D plot
        self._create_3d_plot()
        
        # Create control panel
        self._create_control_panel()
        
        # Layout
        self.pack_start(self.control_panel, False, False, 0)
        self.pack_start(self.plot_container, True, True, 0)
        
        self.show_all()
    
    def _create_3d_plot(self):
        """Create 3D matplotlib plot."""
        # Create figure and 3D axes
        self.figure = Figure(figsize=(8, 8), dpi=100)
        self.ax = self.figure.add_subplot(111, projection='3d')
        
        # Create canvas and toolbar
        self.canvas = FigureCanvas(self.figure)
        self.canvas.set_size_request(600, 600)
        
        self.toolbar = NavigationToolbar(self.canvas)
        
        # Create container
        self.plot_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.plot_container.pack_start(self.toolbar, False, False, 0)
        self.plot_container.pack_start(self.canvas, True, True, 0)
        
        # Configure 3D plot
        self._configure_3d_plot()
    
    def _configure_3d_plot(self):
        """Configure 3D plot appearance."""
        self.ax.set_xlabel('X (μm)')
        self.ax.set_ylabel('Y (μm)')
        self.ax.set_zlabel('Z (μm)')
        self.ax.set_title('3D Microstructure Visualization')
        
        # Set equal aspect ratio
        self.ax.set_box_aspect([1,1,1])
        
        # Set viewing angle
        self.ax.view_init(elev=20, azim=45)
    
    def _create_control_panel(self):
        """Create 3D visualization control panel."""
        self.control_panel = Gtk.Frame(label="3D Visualization Controls")
        self.control_panel.set_shadow_type(Gtk.ShadowType.IN)
        
        grid = Gtk.Grid()
        grid.set_margin_top(6)
        grid.set_margin_bottom(6)
        grid.set_margin_left(6)
        grid.set_margin_right(6)
        grid.set_row_spacing(6)
        grid.set_column_spacing(12)
        
        # View controls
        view_label = Gtk.Label("View:")
        view_label.set_halign(Gtk.Align.START)
        
        view_combo = Gtk.ComboBoxText()
        view_options = ['Isometric', 'Front', 'Side', 'Top', 'Custom']
        for option in view_options:
            view_combo.append_text(option)
        view_combo.set_active(0)
        view_combo.connect('changed', self._on_view_changed)
        
        grid.attach(view_label, 0, 0, 1, 1)
        grid.attach(view_combo, 1, 0, 1, 1)
        
        # Alpha control
        alpha_label = Gtk.Label("Transparency:")
        alpha_label.set_halign(Gtk.Align.START)
        
        alpha_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0.1, 1.0, 0.1)
        alpha_scale.set_value(self.alpha_value)
        alpha_scale.set_hexpand(True)
        alpha_scale.connect('value-changed', self._on_alpha_changed)
        
        grid.attach(alpha_label, 0, 1, 1, 1)
        grid.attach(alpha_scale, 1, 1, 1, 1)
        
        # Display options
        axes_check = Gtk.CheckButton("Show Axes")
        axes_check.set_active(True)
        axes_check.connect('toggled', self._on_axes_toggled)
        
        colorbar_check = Gtk.CheckButton("Show Colorbar")
        colorbar_check.set_active(True)
        colorbar_check.connect('toggled', self._on_colorbar_toggled)
        
        grid.attach(axes_check, 0, 2, 1, 1)
        grid.attach(colorbar_check, 1, 2, 1, 1)
        
        # Cross-section controls
        cross_section_frame = Gtk.Frame(label="Cross-Sections")
        cross_grid = Gtk.Grid()
        cross_grid.set_margin_top(6)
        cross_grid.set_margin_bottom(6)
        cross_grid.set_margin_left(6)
        cross_grid.set_margin_right(6)
        cross_grid.set_row_spacing(3)
        cross_grid.set_column_spacing(6)
        
        # X-plane
        x_check = Gtk.CheckButton("X-Plane")
        x_check.connect('toggled', self._on_cross_section_toggled, 'x')
        x_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
        x_scale.set_value(50)
        x_scale.set_sensitive(False)
        x_scale.connect('value-changed', self._on_cross_section_moved, 'x')
        
        cross_grid.attach(x_check, 0, 0, 1, 1)
        cross_grid.attach(x_scale, 1, 0, 1, 1)
        
        # Y-plane
        y_check = Gtk.CheckButton("Y-Plane")
        y_check.connect('toggled', self._on_cross_section_toggled, 'y')
        y_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
        y_scale.set_value(50)
        y_scale.set_sensitive(False)
        y_scale.connect('value-changed', self._on_cross_section_moved, 'y')
        
        cross_grid.attach(y_check, 0, 1, 1, 1)
        cross_grid.attach(y_scale, 1, 1, 1, 1)
        
        # Z-plane
        z_check = Gtk.CheckButton("Z-Plane")
        z_check.connect('toggled', self._on_cross_section_toggled, 'z')
        z_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
        z_scale.set_value(50)
        z_scale.set_sensitive(False)
        z_scale.connect('value-changed', self._on_cross_section_moved, 'z')
        
        cross_grid.attach(z_check, 0, 2, 1, 1)
        cross_grid.attach(z_scale, 1, 2, 1, 1)
        
        cross_section_frame.add(cross_grid)
        grid.attach(cross_section_frame, 0, 3, 2, 1)
        
        # Animation controls
        animation_frame = Gtk.Frame(label="Animation")
        anim_grid = Gtk.Grid()
        anim_grid.set_margin_top(6)
        anim_grid.set_margin_bottom(6)
        anim_grid.set_margin_left(6)
        anim_grid.set_margin_right(6)
        anim_grid.set_row_spacing(3)
        anim_grid.set_column_spacing(6)
        
        self.play_button = Gtk.Button("Play Rotation")
        self.play_button.connect('clicked', self._on_play_clicked)
        
        speed_label = Gtk.Label("Speed:")
        speed_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 10, 200, 10)
        speed_scale.set_value(self.animation_speed)
        speed_scale.connect('value-changed', self._on_speed_changed)
        
        anim_grid.attach(self.play_button, 0, 0, 2, 1)
        anim_grid.attach(speed_label, 0, 1, 1, 1)
        anim_grid.attach(speed_scale, 1, 1, 1, 1)
        
        animation_frame.add(anim_grid)
        grid.attach(animation_frame, 0, 4, 2, 1)
        
        # Export button
        export_button = Gtk.Button("Export 3D View")
        export_button.connect('clicked', self._on_export_clicked)
        grid.attach(export_button, 0, 5, 2, 1)
        
        self.control_panel.add(grid)
        
        # Store widgets for later access
        self.cross_section_scales = {'x': x_scale, 'y': y_scale, 'z': z_scale}
        self.cross_section_checks = {'x': x_check, 'y': y_check, 'z': z_check}
    
    def load_voxel_data(self, voxel_data: np.ndarray, phase_mapping: Dict[int, str] = None,
                       voxel_size: Tuple[float, float, float] = (1.0, 1.0, 1.0)) -> bool:
        """
        Load 3D voxel data for visualization.
        
        Args:
            voxel_data: 3D numpy array with phase IDs
            phase_mapping: Dictionary mapping phase IDs to names
            voxel_size: Size of each voxel in μm (dx, dy, dz)
            
        Returns:
            Success status
        """
        try:
            self.voxel_data = voxel_data
            self.voxel_size = voxel_size
            
            if phase_mapping:
                self.phase_mapping = phase_mapping
            else:
                # Create default phase mapping
                unique_phases = np.unique(voxel_data)
                self.phase_mapping = {phase: f"Phase {phase}" for phase in unique_phases}
            
            # Generate default colors for phases
            self._generate_phase_colors()
            
            # Update cross-section scale ranges
            self._update_cross_section_ranges()
            
            # Render the visualization
            self.render_3d()
            
            self.emit('data-loaded')
            self.logger.info(f"Loaded 3D voxel data: {voxel_data.shape}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load voxel data: {e}")
            return False
    
    def _generate_phase_colors(self):
        """Generate colors for each phase."""
        phases = list(self.phase_mapping.keys())
        
        # Use a qualitative colormap
        if len(phases) <= 10:
            cmap = plt.cm.tab10
        elif len(phases) <= 20:
            cmap = plt.cm.tab20
        else:
            cmap = plt.cm.hsv
        
        self.phase_colors = {}
        for i, phase in enumerate(phases):
            self.phase_colors[phase] = cmap(i / len(phases))
    
    def _update_cross_section_ranges(self):
        """Update cross-section slider ranges based on data."""
        if self.voxel_data is None:
            return
        
        shape = self.voxel_data.shape
        
        self.cross_section_scales['x'].set_range(0, shape[0] - 1)
        self.cross_section_scales['x'].set_value(shape[0] // 2)
        
        self.cross_section_scales['y'].set_range(0, shape[1] - 1)
        self.cross_section_scales['y'].set_value(shape[1] // 2)
        
        self.cross_section_scales['z'].set_range(0, shape[2] - 1)
        self.cross_section_scales['z'].set_value(shape[2] // 2)
    
    def render_3d(self, use_subsampling: bool = True, subsample_factor: int = 2) -> bool:
        """
        Render 3D voxel visualization.
        
        Args:
            use_subsampling: Whether to subsample for performance
            subsample_factor: Subsampling factor
            
        Returns:
            Success status
        """
        if self.voxel_data is None:
            return False
        
        try:
            self.ax.clear()
            
            # Subsample for performance if needed
            if use_subsampling and self.voxel_data.size > 50**3:
                data = self.voxel_data[::subsample_factor, ::subsample_factor, ::subsample_factor]
                scale_factor = subsample_factor
            else:
                data = self.voxel_data
                scale_factor = 1
            
            # Create coordinates
            x_size, y_size, z_size = data.shape
            dx, dy, dz = self.voxel_size
            
            x = np.arange(x_size) * dx * scale_factor
            y = np.arange(y_size) * dy * scale_factor
            z = np.arange(z_size) * dz * scale_factor
            
            # Render each phase separately
            # Skip phase 0 (pores/air) to show internal solid structure clearly
            for phase_id, phase_name in self.phase_mapping.items():
                if phase_id not in self.phase_colors:
                    continue
                
                # Skip phase 0 (pores/air) for better internal visibility
                if phase_id == 0:
                    continue
                
                # Create boolean mask for this phase
                phase_mask = (data == phase_id)
                
                if not np.any(phase_mask):
                    continue
                
                # Get voxel positions
                xi, yi, zi = np.meshgrid(x, y, z, indexing='ij')
                
                # Plot voxels for this phase
                self.ax.scatter(
                    xi[phase_mask], yi[phase_mask], zi[phase_mask],
                    c=[self.phase_colors[phase_id]],
                    alpha=self.alpha_value,
                    s=20,  # Point size
                    label=phase_name
                )
            
            # Configure plot
            self._configure_3d_plot()
            
            # Set axis limits
            self.ax.set_xlim(0, x_size * dx * scale_factor)
            self.ax.set_ylim(0, y_size * dy * scale_factor)
            self.ax.set_zlim(0, z_size * dz * scale_factor)
            
            # Add legend if there are multiple phases - positioned outside plot area
            if len(self.phase_mapping) > 1:
                self.ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8, frameon=True)
            
            # Adjust layout to accommodate legend
            self.figure.tight_layout()
            
            # Refresh canvas
            self.canvas.draw()
            
            self.logger.debug("3D visualization rendered successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to render 3D visualization: {e}")
            return False
    
    def render_voxel_plot(self) -> bool:
        """
        Render using matplotlib's voxel plotting (alternative method).
        More suitable for smaller datasets.
        """
        if self.voxel_data is None:
            return False
        
        try:
            self.ax.clear()
            
            # For voxel plots, we need boolean arrays for each phase
            # Skip phase 0 (pores/air) to show internal solid structure clearly
            for phase_id, phase_name in self.phase_mapping.items():
                if phase_id not in self.phase_colors:
                    continue
                
                # Skip phase 0 (pores/air) for better internal visibility
                if phase_id == 0:
                    continue
                
                # Create boolean mask for this phase
                phase_voxels = (self.voxel_data == phase_id)
                
                if not np.any(phase_voxels):
                    continue
                
                # Plot voxels
                self.ax.voxels(
                    phase_voxels,
                    facecolors=self.phase_colors[phase_id],
                    alpha=self.alpha_value,
                    edgecolors='k',
                    linewidth=0.1
                )
            
            # Configure plot
            self._configure_3d_plot()
            
            # Refresh canvas
            self.canvas.draw()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to render voxel plot: {e}")
            return False
    
    def add_cross_section(self, axis: str, position: int) -> bool:
        """
        Add cross-sectional plane.
        
        Args:
            axis: 'x', 'y', or 'z'
            position: Position along the axis
            
        Returns:
            Success status
        """
        if self.voxel_data is None:
            return False
        
        try:
            # Extract cross-section data
            if axis == 'x':
                section = self.voxel_data[position, :, :]
                X, Y = np.meshgrid(
                    np.arange(section.shape[1]) * self.voxel_size[1],
                    np.arange(section.shape[0]) * self.voxel_size[2]
                )
                Z = np.full_like(X, position * self.voxel_size[0])
                
            elif axis == 'y':
                section = self.voxel_data[:, position, :]
                X, Y = np.meshgrid(
                    np.arange(section.shape[1]) * self.voxel_size[2],
                    np.arange(section.shape[0]) * self.voxel_size[0]
                )
                Z = np.full_like(X, position * self.voxel_size[1])
                X, Z = Z, X  # Swap for correct orientation
                
            elif axis == 'z':
                section = self.voxel_data[:, :, position]
                X, Y = np.meshgrid(
                    np.arange(section.shape[1]) * self.voxel_size[1],
                    np.arange(section.shape[0]) * self.voxel_size[0]
                )
                Z = np.full_like(X, position * self.voxel_size[2])
            
            else:
                return False
            
            # Plot surface
            self.ax.plot_surface(X, Y, Z, facecolors=plt.cm.viridis(section / np.max(section)),
                               alpha=0.7, shade=False)
            
            # Refresh canvas
            self.canvas.draw()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add cross-section: {e}")
            return False
    
    def export_3d_view(self, file_path: str, format_type: str = 'png', dpi: int = 300) -> bool:
        """Export current 3D view to file."""
        try:
            self.figure.savefig(file_path, format=format_type, dpi=dpi, bbox_inches='tight')
            self.logger.info(f"3D view exported to: {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to export 3D view: {e}")
            return False
    
    # Event handlers
    def _on_view_changed(self, combo):
        """Handle view change."""
        view_map = {
            0: (20, 45),    # Isometric
            1: (0, 0),      # Front
            2: (0, 90),     # Side
            3: (90, 0),     # Top
            4: None         # Custom (no change)
        }
        
        view_angles = view_map[combo.get_active()]
        if view_angles:
            self.ax.view_init(elev=view_angles[0], azim=view_angles[1])
            self.canvas.draw()
            self.emit('view-changed')
    
    def _on_alpha_changed(self, scale):
        """Handle transparency change."""
        self.alpha_value = scale.get_value()
        self.render_3d()
    
    def _on_axes_toggled(self, check_button):
        """Handle axes display toggle."""
        self.show_axes = check_button.get_active()
        self.ax.set_axis_on() if self.show_axes else self.ax.set_axis_off()
        self.canvas.draw()
    
    def _on_colorbar_toggled(self, check_button):
        """Handle colorbar display toggle."""
        self.show_colorbar = check_button.get_active()
        # Implementation depends on how colorbar is managed
        self.render_3d()
    
    def _on_cross_section_toggled(self, check_button, axis):
        """Handle cross-section toggle."""
        is_active = check_button.get_active()
        self.cross_section_scales[axis].set_sensitive(is_active)
        
        if is_active:
            position = int(self.cross_section_scales[axis].get_value())
            self.add_cross_section(axis, position)
        else:
            # Remove cross-section (would need to track and remove specific surfaces)
            self.render_3d()
    
    def _on_cross_section_moved(self, scale, axis):
        """Handle cross-section position change."""
        if self.cross_section_checks[axis].get_active():
            position = int(scale.get_value())
            self.add_cross_section(axis, position)
    
    def _on_play_clicked(self, button):
        """Handle animation play/pause."""
        if not self.animation_active:
            self.animation_active = True
            self.play_button.set_label("Pause")
            self._start_animation()
        else:
            self.animation_active = False
            self.play_button.set_label("Play Rotation")
    
    def _on_speed_changed(self, scale):
        """Handle animation speed change."""
        self.animation_speed = int(scale.get_value())
    
    def _on_export_clicked(self, button):
        """Handle export button click."""
        dialog = Gtk.FileChooserDialog(
            title="Export 3D View",
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
                format_type = file_path.split('.')[-1].lower()
                self.export_3d_view(file_path, format_type)
        
        dialog.destroy()
    
    def _start_animation(self):
        """Start rotation animation."""
        if not self.animation_active:
            return
        
        # Rotate view
        current_azim = self.ax.azim
        self.ax.view_init(azim=current_azim + 2)
        self.canvas.draw()
        
        # Schedule next frame
        GObject.timeout_add(self.animation_speed, self._start_animation)
        
        return False  # Don't repeat automatically
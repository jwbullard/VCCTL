#!/usr/bin/env python3
"""
PyVista-based 3D Strain Energy Visualization Dialog

Uses the same PyVista technology as microstructure visualization to display
3D strain energy data with professional volume rendering, heat maps, and
interactive 3D capabilities.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject

import numpy as np
import pyvista as pv
import logging
from pathlib import Path
from typing import Optional, Tuple
import matplotlib.cm as cm
from matplotlib.colors import Normalize

# Import the existing PyVista viewer as base
from app.visualization.pyvista_3d_viewer import PyVistaViewer3D


class PyVistaStrainViewer(Gtk.Dialog):
    """
    Dialog for viewing 3D elastic strain energy using PyVista volume rendering.

    Features:
    - Professional PyVista volume rendering
    - Multiple visualization modes (volume, isosurface, points)
    - Interactive 3D navigation
    - Heat map coloring with adjustable ranges
    - Cross-sectional views
    - Export capabilities
    """

    def __init__(self, parent_window, operation_name: str, img_file_path: Optional[str] = None):
        """
        Initialize the PyVista strain energy viewer dialog.

        Args:
            parent_window: Parent window
            operation_name: Name of the elastic operation
            img_file_path: Path to the energy.img file containing strain energy data
        """
        super().__init__(
            title=f"3D Strain Energy Visualization - {operation_name}",
            parent=parent_window,
            modal=False,
            destroy_with_parent=False
        )

        self.logger = logging.getLogger(__name__)
        self.operation_name = operation_name
        self.img_file_path = img_file_path

        # Data storage
        self.strain_data = None
        self.dimensions = None
        self.voxel_size = (1.0, 1.0, 1.0)  # μm per voxel

        # Visualization settings
        self.threshold_min = 0.0    # Minimum strain energy threshold
        self.threshold_max = 0.02   # Default to show low-energy bulk material
        self.colormap_name = 'hot'  # Colormap for strain energy
        self.rendering_mode = 'volume'  # 'volume', 'isosurface', 'points'

        # Setup dialog
        self.set_default_size(1400, 900)
        self.set_border_width(10)

        # Setup UI
        self._setup_ui()

        # Load data if path provided
        if self.img_file_path:
            self._load_strain_data(self.img_file_path)

        # Add close button
        self.add_button("Close", Gtk.ResponseType.CLOSE)

        self.show_all()

    def _setup_ui(self):
        """Setup the user interface."""
        content_area = self.get_content_area()

        # Main container
        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        content_area.pack_start(main_box, True, True, 0)

        # Left panel - Controls
        controls_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        controls_box.set_size_request(300, -1)
        main_box.pack_start(controls_box, False, False, 0)

        # Visualization settings frame
        vis_frame = Gtk.Frame(label="Visualization Settings")
        vis_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vis_box.set_margin_left(10)
        vis_box.set_margin_right(10)
        vis_box.set_margin_top(10)
        vis_box.set_margin_bottom(10)
        vis_frame.add(vis_box)
        controls_box.pack_start(vis_frame, False, False, 0)

        # Rendering mode selection
        mode_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        mode_label = Gtk.Label("Rendering:")
        mode_label.set_size_request(100, -1)
        mode_label.set_halign(Gtk.Align.START)
        self.mode_combo = Gtk.ComboBoxText()
        self.mode_combo.append_text("Volume Rendering")
        self.mode_combo.append_text("Isosurface")
        self.mode_combo.append_text("Point Cloud")
        self.mode_combo.set_active(0)  # Default to volume rendering
        self.mode_combo.connect('changed', self._on_mode_changed)
        mode_box.pack_start(mode_label, False, False, 0)
        mode_box.pack_start(self.mode_combo, True, True, 0)
        vis_box.pack_start(mode_box, False, False, 0)

        # Colormap selection
        cmap_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        cmap_label = Gtk.Label("Colormap:")
        cmap_label.set_size_request(100, -1)
        cmap_label.set_halign(Gtk.Align.START)
        self.cmap_combo = Gtk.ComboBoxText()
        for cmap in ['hot', 'viridis', 'plasma', 'inferno', 'magma', 'coolwarm', 'jet', 'turbo']:
            self.cmap_combo.append_text(cmap)
        self.cmap_combo.set_active(0)  # Default to 'hot'
        self.cmap_combo.connect('changed', self._on_colormap_changed)
        cmap_box.pack_start(cmap_label, False, False, 0)
        cmap_box.pack_start(self.cmap_combo, True, True, 0)
        vis_box.pack_start(cmap_box, False, False, 0)

        # Threshold controls frame
        thresh_frame = Gtk.Frame(label="Strain Energy Range")
        thresh_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        thresh_box.set_margin_left(10)
        thresh_box.set_margin_right(10)
        thresh_box.set_margin_top(10)
        thresh_box.set_margin_bottom(10)
        thresh_frame.add(thresh_box)
        controls_box.pack_start(thresh_frame, False, False, 0)

        # Min threshold
        min_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        min_label = Gtk.Label("Min:")
        min_label.set_size_request(100, -1)
        min_label.set_halign(Gtk.Align.START)
        self.min_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0.0, 1.0, 0.001)
        self.min_scale.set_value(0.0)
        self.min_scale.set_draw_value(True)
        self.min_scale.set_digits(3)  # Show 3 decimal places for fine control
        self.min_scale.connect('value-changed', self._on_threshold_changed)
        min_box.pack_start(min_label, False, False, 0)
        min_box.pack_start(self.min_scale, True, True, 0)
        thresh_box.pack_start(min_box, False, False, 0)

        # Max threshold
        max_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        max_label = Gtk.Label("Max:")
        max_label.set_size_request(100, -1)
        max_label.set_halign(Gtk.Align.START)
        self.max_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0.0, 1.0, 0.001)
        self.max_scale.set_value(0.02)  # Default to show low-energy bulk material
        self.max_scale.set_draw_value(True)
        self.max_scale.set_digits(3)  # Show 3 decimal places for fine control
        self.max_scale.connect('value-changed', self._on_threshold_changed)
        max_box.pack_start(max_label, False, False, 0)
        max_box.pack_start(self.max_scale, True, True, 0)
        thresh_box.pack_start(max_box, False, False, 0)

        # Preset buttons for common visualization ranges
        preset_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        preset_box.set_margin_top(10)

        bulk_button = Gtk.Button(label="Bulk Material (0-0.02)")
        bulk_button.connect('clicked', lambda b: self._set_preset_range(0.0, 0.02))
        preset_box.pack_start(bulk_button, True, True, 0)

        hotspots_button = Gtk.Button(label="High Energy Hotspots (0.1-1.0)")
        hotspots_button.connect('clicked', lambda b: self._set_preset_range(0.1, 1.0))
        preset_box.pack_start(hotspots_button, True, True, 0)

        full_button = Gtk.Button(label="Full Range (0-1.0)")
        full_button.connect('clicked', lambda b: self._set_preset_range(0.0, 1.0))
        preset_box.pack_start(full_button, True, True, 0)

        thresh_box.pack_start(preset_box, False, False, 0)

        # Statistics frame
        stats_frame = Gtk.Frame(label="Strain Energy Statistics")
        self.stats_label = Gtk.Label()
        self.stats_label.set_markup("<small>No data loaded</small>")
        self.stats_label.set_margin_left(10)
        self.stats_label.set_margin_right(10)
        self.stats_label.set_margin_top(10)
        self.stats_label.set_margin_bottom(10)
        self.stats_label.set_line_wrap(True)
        self.stats_label.set_halign(Gtk.Align.START)
        self.stats_label.set_valign(Gtk.Align.START)
        stats_frame.add(self.stats_label)
        controls_box.pack_start(stats_frame, False, False, 0)

        # Right panel - PyVista 3D Viewer
        viewer_frame = Gtk.Frame(label="3D Strain Energy Visualization")
        main_box.pack_start(viewer_frame, True, True, 0)

        # Create PyVista viewer
        self.pyvista_viewer = PyVistaViewer3D()
        viewer_frame.add(self.pyvista_viewer)

        # Show all widgets first, then customize
        self.pyvista_viewer.show_all()

        # Configure PyVista viewer for strain energy visualization (delayed)
        from gi.repository import GLib
        GLib.idle_add(self._customize_pyvista_viewer_for_strain_energy)

    def _customize_pyvista_viewer_for_strain_energy(self):
        """Customize PyVista viewer specifically for strain energy visualization."""
        try:
            # Hide unnecessary buttons by traversing the control panel
            if hasattr(self.pyvista_viewer, 'control_panel'):
                self._hide_buttons_by_label(self.pyvista_viewer.control_panel, [
                    "Phase Data",     # Issue 1: Phase Data button not needed
                    "Connectivity"    # Issue 1: Connectivity button not needed
                ])

            # Remove the rendering dropdown since we have our own (Issue 3)
            if hasattr(self.pyvista_viewer, 'mode_combo'):
                # Find and remove the rendering controls
                parent = self.pyvista_viewer.mode_combo.get_parent()
                if parent:
                    # Remove the rendering label and combo
                    items_to_remove = []
                    for child in parent.get_children():
                        if isinstance(child, Gtk.Label) and child.get_text() == "Rendering:":
                            items_to_remove.append(child)
                        elif child == self.pyvista_viewer.mode_combo:
                            items_to_remove.append(child)

                    for item in items_to_remove:
                        parent.remove(item)
                        self.logger.info(f"Removed rendering control: {type(item).__name__}")

                    if items_to_remove:
                        self.logger.info("Removed redundant rendering controls")

            # Remove "Measure:" label (not needed for strain energy)
            self._remove_labels_by_text(self.pyvista_viewer, ["Measure:", "Measure", "measure", "Distance"])

            # Fix cross-section functionality (Issue 2)
            # We need to properly connect to the existing cross-section system
            self._setup_cross_section_handlers()

            self.logger.info("Customized PyVista viewer for strain energy visualization")

        except Exception as e:
            self.logger.warning(f"Failed to customize PyVista viewer: {e}")
            import traceback
            self.logger.warning(traceback.format_exc())

    def _hide_buttons_by_label(self, container, button_labels):
        """Recursively remove buttons with specific labels."""
        try:
            children_to_remove = []

            for child in container.get_children():
                if isinstance(child, Gtk.Button):
                    if child.get_label() in button_labels:
                        children_to_remove.append((container, child))
                        self.logger.info(f"Found button to remove: {child.get_label()}")
                elif hasattr(child, 'get_children'):
                    # Recursively search child containers
                    self._hide_buttons_by_label(child, button_labels)

            # Remove buttons from their containers
            for parent, button in children_to_remove:
                parent.remove(button)
                self.logger.info(f"Removed button: {button.get_label()}")

        except Exception as e:
            self.logger.debug(f"Error removing buttons: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())

    def _remove_labels_by_text(self, container, label_texts):
        """Recursively remove labels with specific text."""
        try:
            labels_to_remove = []

            for child in container.get_children():
                if isinstance(child, Gtk.Label):
                    if child.get_text() in label_texts:
                        labels_to_remove.append((container, child))
                        self.logger.info(f"Found label to remove: {child.get_text()}")
                elif hasattr(child, 'get_children'):
                    # Recursively search child containers
                    self._remove_labels_by_text(child, label_texts)

            # Remove labels from their containers
            for parent, label in labels_to_remove:
                parent.remove(label)
                self.logger.info(f"Removed label: {label.get_text()}")

        except Exception as e:
            self.logger.debug(f"Error removing labels: {e}")

    def _setup_cross_section_handlers(self):
        """Set up proper cross-section functionality."""
        try:
            # Initialize cross-section state if not exists
            if not hasattr(self.pyvista_viewer, 'cross_section_enabled'):
                self.pyvista_viewer.cross_section_enabled = {'x': False, 'y': False, 'z': False}
                self.pyvista_viewer.cross_section_positions = {'x': 0.5, 'y': 0.5, 'z': 0.5}

            # Find and connect cross-section checkboxes
            checkboxes_found = self._find_and_connect_cross_section_checkboxes(self.pyvista_viewer)

            if checkboxes_found > 0:
                self.logger.info(f"Connected {checkboxes_found} cross-section checkboxes for strain energy viewer")
            else:
                self.logger.warning("No cross-section checkboxes found to connect")

        except Exception as e:
            self.logger.warning(f"Failed to setup cross-section handlers: {e}")

    def _find_and_connect_cross_section_checkboxes(self, container):
        """Find cross-section checkboxes and connect them to our handlers."""
        checkboxes_found = 0

        try:
            for child in container.get_children():
                if isinstance(child, Gtk.CheckButton):
                    label = child.get_label()
                    if label:
                        label_lower = label.lower()
                        axis = None

                        if 'x' in label_lower:
                            axis = 'x'
                        elif 'y' in label_lower:
                            axis = 'y'
                        elif 'z' in label_lower:
                            axis = 'z'

                        if axis:
                            # Disconnect existing handlers
                            try:
                                child.disconnect_by_func(lambda *args: None)
                            except:
                                pass

                            # Connect our custom handler
                            child.connect('toggled',
                                        lambda cb, ax=axis: self._handle_cross_section_toggle(ax, cb.get_active()))
                            checkboxes_found += 1
                            self.logger.info(f"Connected cross-section checkbox for {axis.upper()} axis")

                elif hasattr(child, 'get_children'):
                    # Recursively search child containers
                    checkboxes_found += self._find_and_connect_cross_section_checkboxes(child)

        except Exception as e:
            self.logger.debug(f"Error finding cross-section checkboxes: {e}")

        return checkboxes_found

    def _handle_cross_section_toggle(self, axis, enabled):
        """Handle cross-section checkbox toggles (Issue 2 fix)."""
        try:
            self.logger.info(f"Cross-section {axis.upper()}: {'enabled' if enabled else 'disabled'}")

            if hasattr(self.pyvista_viewer, 'cross_section_enabled'):
                self.pyvista_viewer.cross_section_enabled[axis] = enabled

                # Force re-render with cross-sections applied
                self._create_pyvista_volume()

        except Exception as e:
            self.logger.error(f"Failed to handle cross-section toggle for {axis}: {e}")

    def _apply_cross_sections(self, mesh):
        """Apply cross-sections to the mesh based on enabled axes."""
        try:
            result = mesh

            if hasattr(self.pyvista_viewer, 'cross_section_enabled') and \
               hasattr(self.pyvista_viewer, 'cross_section_positions'):

                for axis in ['x', 'y', 'z']:
                    if self.pyvista_viewer.cross_section_enabled.get(axis, False):
                        position = self.pyvista_viewer.cross_section_positions.get(axis, 0.5)

                        # Get bounds of the data
                        bounds = result.bounds
                        if axis == 'x':
                            clip_pos = bounds[0] + position * (bounds[1] - bounds[0])
                            normal = (1, 0, 0)
                        elif axis == 'y':
                            clip_pos = bounds[2] + position * (bounds[3] - bounds[2])
                            normal = (0, 1, 0)
                        else:  # z
                            clip_pos = bounds[4] + position * (bounds[5] - bounds[4])
                            normal = (0, 0, 1)

                        # Create clipping plane
                        origin = [clip_pos if i == ['x', 'y', 'z'].index(axis) else 0 for i in range(3)]
                        result = result.clip(normal=normal, origin=origin)

                        self.logger.info(f"Applied cross-section on {axis.upper()} axis at position {position:.2f}")

            return result

        except Exception as e:
            self.logger.error(f"Failed to apply cross-sections: {e}")
            return mesh  # Return original mesh if cross-sections fail

    def _load_strain_data(self, img_file_path: str) -> bool:
        """
        Load strain energy data from energy.img file.

        Args:
            img_file_path: Path to the energy.img file

        Returns:
            Success status
        """
        try:
            self.logger.info(f"Loading strain energy data from: {img_file_path}")

            # Read the .img file (same format as microstructure files)
            with open(img_file_path, 'r') as f:
                lines = f.readlines()

            # Parse header for dimensions (energy.img format)
            x_dim = y_dim = z_dim = None
            voxel_size = 1.0
            data_values = []

            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                # Parse header fields (energy.img format with colons)
                if line.startswith("X_Size:"):
                    try:
                        x_dim = int(line.split(":")[1].strip())
                    except:
                        pass
                elif line.startswith("Y_Size:"):
                    try:
                        y_dim = int(line.split(":")[1].strip())
                    except:
                        pass
                elif line.startswith("Z_Size:"):
                    try:
                        z_dim = int(line.split(":")[1].strip())
                    except:
                        pass
                elif line.startswith("Image_Resolution:"):
                    try:
                        voxel_size = float(line.split(":")[1].strip())
                    except:
                        pass
                elif line.startswith("Version:"):
                    # Skip version line
                    continue
                else:
                    # Try to parse as strain energy value
                    try:
                        value = float(line)
                        data_values.append(value)
                    except ValueError:
                        # Skip non-numeric lines
                        continue

            # Validate dimensions
            if x_dim is None or y_dim is None or z_dim is None:
                self.logger.error("Could not parse image dimensions from header")
                return False

            self.dimensions = (x_dim, y_dim, z_dim)
            self.voxel_size = (voxel_size, voxel_size, voxel_size)
            self.logger.info(f"Image dimensions: {x_dim} x {y_dim} x {z_dim}")
            self.logger.info(f"Voxel resolution: {voxel_size} μm")

            # Check data size
            expected_size = x_dim * y_dim * z_dim
            if len(data_values) != expected_size:
                self.logger.warning(f"Data size mismatch: expected {expected_size}, got {len(data_values)}")
                if len(data_values) < expected_size:
                    data_values.extend([0.0] * (expected_size - len(data_values)))
                else:
                    data_values = data_values[:expected_size]

            # Reshape data to 3D array (match energy.img format: X, Y, Z order)
            self.strain_data = np.array(data_values).reshape(x_dim, y_dim, z_dim)

            self.logger.info(f"Loaded {len(data_values)} strain energy values")
            self.logger.info(f"Data range: {np.min(self.strain_data):.2e} to {np.max(self.strain_data):.2e}")

            # Update statistics
            self._update_statistics()

            # Create PyVista volume and render
            self._create_pyvista_volume()

            self.logger.info(f"Successfully loaded strain energy data from {img_file_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error loading strain data: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _create_pyvista_volume(self):
        """Create PyVista volume from strain energy data."""
        if self.strain_data is None:
            self.logger.warning("No strain data available for volume creation")
            return

        try:
            self.logger.info(f"Creating PyVista volume from strain energy data: shape {self.strain_data.shape}")

            # Normalize strain energy data to 0-1 range for visualization
            data_min = np.min(self.strain_data)
            data_max = np.max(self.strain_data)
            self.logger.info(f"Data range: {data_min:.6f} to {data_max:.6f}")

            if data_max > data_min:
                normalized_data = (self.strain_data - data_min) / (data_max - data_min)
            else:
                normalized_data = np.zeros_like(self.strain_data)
                self.logger.warning("Data has no variation - all values are the same")

            # Apply thresholds
            threshold_min_val = data_min + self.threshold_min * (data_max - data_min)
            threshold_max_val = data_min + self.threshold_max * (data_max - data_min)
            self.logger.info(f"Applying thresholds: {threshold_min_val:.6f} to {threshold_max_val:.6f}")

            # Create mask for data within threshold range
            mask = (self.strain_data >= threshold_min_val) & (self.strain_data <= threshold_max_val)
            masked_points = np.sum(mask)
            self.logger.info(f"Points within threshold range: {masked_points} / {self.strain_data.size}")

            # Apply mask to normalized data
            masked_data = np.where(mask, normalized_data, 0.0)

            # Create PyVista structured grid (note: PyVista expects (nz+1, ny+1, nx+1) for dimensions)
            # But we'll use the actual data dimensions since it's point data
            grid = pv.ImageData(dimensions=self.strain_data.shape)
            grid.spacing = self.voxel_size
            grid.origin = (0, 0, 0)

            self.logger.info(f"Created PyVista grid: dimensions {grid.dimensions}, n_points {grid.n_points}")

            # Add strain energy data as scalars (flatten in C order for PyVista)
            flattened_data = masked_data.flatten(order='C')
            grid.point_data["strain_energy"] = flattened_data

            self.logger.info(f"Added strain energy data: {len(flattened_data)} values, range {np.min(flattened_data):.6f} to {np.max(flattened_data):.6f}")
            self.logger.info(f"Non-zero values: {np.count_nonzero(flattened_data)} / {len(flattened_data)}")

            # Create colormap
            colormap = cm.get_cmap(self.colormap_name)

            # Check if PyVista viewer and plotter are available
            if not hasattr(self.pyvista_viewer, 'plotter') or not self.pyvista_viewer.plotter:
                self.logger.error("PyVista plotter not available")
                return

            # Clear existing visualization
            self.pyvista_viewer.plotter.clear()
            self.logger.info("Cleared existing PyVista visualization")

            # Add volume based on rendering mode
            if self.rendering_mode == 'volume':
                self._add_volume_rendering(grid, colormap)
            elif self.rendering_mode == 'isosurface':
                self._add_isosurface_rendering(grid, colormap)
            elif self.rendering_mode == 'points':
                self._add_point_rendering(grid, colormap)

            # Update view
            self.pyvista_viewer.plotter.reset_camera()
            self.logger.info("Reset camera view")

            # CRITICAL: Trigger render and update the GTK image widget
            self.pyvista_viewer._force_render_update()
            self.logger.info("Triggered render and display update")

            self.logger.info("PyVista volume created successfully")

        except Exception as e:
            self.logger.error(f"Error creating PyVista volume: {e}")
            import traceback
            traceback.print_exc()

    def _add_volume_rendering(self, grid, colormap):
        """Add volume rendering to PyVista plotter."""
        try:
            self.logger.info("Adding volume rendering to PyVista plotter")

            # Get data statistics for dynamic thresholding
            strain_values = grid.point_data["strain_energy"]
            data_min = np.min(strain_values)
            data_max = np.max(strain_values)
            non_zero_count = np.count_nonzero(strain_values)

            self.logger.info(f"Volume data stats: min={data_min:.6f}, max={data_max:.6f}, non-zero={non_zero_count}/{len(strain_values)}")

            # Use a very small threshold (only remove true zeros)
            threshold_value = data_min + 1e-10 if data_min == 0 else data_min * 0.1
            threshold = grid.threshold(threshold_value, scalars="strain_energy")
            self.logger.info(f"Using threshold {threshold_value:.8f}, points remaining: {threshold.n_points}")

            # Apply cross-sections if enabled
            if hasattr(self.pyvista_viewer, 'cross_section_enabled'):
                threshold = self._apply_cross_sections(threshold)

            if threshold.n_points > 0:
                # Create isosurfaces at different strain energy levels for better visualization
                try:
                    # Get data range for isosurface levels
                    strain_values = threshold.point_data["strain_energy"]
                    data_min = np.min(strain_values)
                    data_max = np.max(strain_values)

                    # Create multiple isosurfaces at different strain energy levels
                    n_isosurfaces = 3
                    levels = np.linspace(data_min + 0.1 * (data_max - data_min),
                                       data_max - 0.1 * (data_max - data_min),
                                       n_isosurfaces)

                    self.logger.info(f"Creating {n_isosurfaces} isosurfaces at levels: {levels}")

                    for i, level in enumerate(levels):
                        # Create isosurface at this level
                        iso = threshold.contour([level], scalars="strain_energy")

                        if iso.n_points > 0:
                            # Add isosurface with transparency
                            opacity = 0.3 + 0.4 * (i / (n_isosurfaces - 1))  # Increasing opacity
                            color_val = level / data_max  # Normalized color

                            actor = self.pyvista_viewer.plotter.add_mesh(
                                iso,
                                scalars="strain_energy",
                                cmap=self.colormap_name,
                                opacity=opacity,
                                name=f"strain_iso_{i}",
                                show_scalar_bar=(i == n_isosurfaces - 1),  # Only show scalar bar for last one
                                scalar_bar_args={
                                    'title': 'Strain Energy',
                                    'n_labels': 5,
                                    'position_x': 0.85,
                                    'position_y': 0.1
                                } if i == n_isosurfaces - 1 else None
                            )
                            self.logger.info(f"Added isosurface {i} at level {level:.6f}: {iso.n_points} points")
                        else:
                            self.logger.warning(f"No points found for isosurface at level {level:.6f}")

                except Exception as e:
                    self.logger.warning(f"Isosurface creation failed: {e}, trying simple wireframe")

                    # Fallback: Simple wireframe of thresholded data
                    wireframe = threshold.extract_surface()
                    if wireframe.n_points > 0:
                        actor = self.pyvista_viewer.plotter.add_mesh(
                            wireframe,
                            scalars="strain_energy",
                            cmap=self.colormap_name,
                            style='wireframe',
                            opacity=0.8,
                            line_width=2,
                            name="strain_wireframe",
                            show_scalar_bar=True,
                            scalar_bar_args={
                                'title': 'Strain Energy',
                                'n_labels': 5,
                                'position_x': 0.85,
                                'position_y': 0.1
                            }
                        )
                        self.logger.info(f"Added wireframe mesh: {wireframe.n_points} points")
                    else:
                        self.logger.error("No surface could be extracted from strain data")
            else:
                self.logger.warning("No points remaining after thresholding - trying with all data")
                # Try without thresholding
                actor = self.pyvista_viewer.plotter.add_mesh(
                    grid,
                    scalars="strain_energy",
                    cmap=self.colormap_name,
                    opacity=0.5,
                    name="strain_volume",
                    show_scalar_bar=True,
                    scalar_bar_args={
                        'title': 'Strain Energy',
                        'n_labels': 5,
                        'position_x': 0.85,
                        'position_y': 0.1
                    }
                )
                self.logger.info(f"Added full grid mesh to plotter: {actor}")

        except Exception as e:
            self.logger.error(f"Error adding volume rendering: {e}")
            import traceback
            traceback.print_exc()

    def _add_isosurface_rendering(self, grid, colormap):
        """Add isosurface rendering to PyVista plotter."""
        try:
            if hasattr(self.pyvista_viewer, 'plotter') and self.pyvista_viewer.plotter:
                # Create isosurfaces at different strain energy levels
                iso_values = np.linspace(0.1, 0.9, 5)  # 5 isosurface levels

                for i, iso_val in enumerate(iso_values):
                    contour = grid.contour([iso_val], scalars="strain_energy")
                    if contour.n_points > 0:
                        color_val = colormap(iso_val)[:3]  # RGB without alpha
                        self.pyvista_viewer.plotter.add_mesh(
                            contour,
                            color=color_val,
                            opacity=0.7,
                            name=f"iso_{i}",
                            smooth_shading=True
                        )

        except Exception as e:
            self.logger.error(f"Error adding isosurface rendering: {e}")

    def _add_point_rendering(self, grid, colormap):
        """Add point cloud rendering to PyVista plotter."""
        try:
            if hasattr(self.pyvista_viewer, 'plotter') and self.pyvista_viewer.plotter:
                # Extract points with non-zero strain energy
                threshold = grid.threshold(0.001, scalars="strain_energy")

                if threshold.n_points > 0:
                    self.pyvista_viewer.plotter.add_mesh(
                        threshold,
                        scalars="strain_energy",
                        cmap=self.colormap_name,
                        point_size=3,
                        render_points_as_spheres=True,
                        name="strain_points",
                        show_scalar_bar=True,
                        scalar_bar_args={
                            'title': 'Strain Energy',
                            'n_labels': 5,
                            'position_x': 0.85,
                            'position_y': 0.1
                        }
                    )

        except Exception as e:
            self.logger.error(f"Error adding point rendering: {e}")

    def _update_statistics(self):
        """Update the statistics display."""
        if self.strain_data is None:
            return

        try:
            # Calculate statistics
            data_min = np.min(self.strain_data)
            data_max = np.max(self.strain_data)
            data_mean = np.mean(self.strain_data)
            data_std = np.std(self.strain_data)
            non_zero_count = np.count_nonzero(self.strain_data)
            total_count = self.strain_data.size

            # Format statistics text
            stats_text = f"""<small><b>Dataset Information:</b>
Dimensions: {self.dimensions[0]} × {self.dimensions[1]} × {self.dimensions[2]} voxels
Voxel Size: {self.voxel_size[0]:.2f} μm
Total Voxels: {total_count:,}
Non-zero Voxels: {non_zero_count:,} ({non_zero_count/total_count*100:.1f}%)

<b>Strain Energy Statistics:</b>
Minimum: {data_min:.2e}
Maximum: {data_max:.2e}
Mean: {data_mean:.2e}
Std Dev: {data_std:.2e}</small>"""

            self.stats_label.set_markup(stats_text)

        except Exception as e:
            self.logger.error(f"Error updating statistics: {e}")

    def _on_mode_changed(self, combo):
        """Handle rendering mode change."""
        active_text = combo.get_active_text()
        if "Volume" in active_text:
            self.rendering_mode = 'volume'
        elif "Isosurface" in active_text:
            self.rendering_mode = 'isosurface'
        elif "Point" in active_text:
            self.rendering_mode = 'points'

        self.logger.info(f"Rendering mode changed to: {self.rendering_mode}")
        self._create_pyvista_volume()

    def _on_colormap_changed(self, combo):
        """Handle colormap change."""
        self.colormap_name = combo.get_active_text()
        self.logger.info(f"Colormap changed to: {self.colormap_name}")
        self._create_pyvista_volume()

    def _on_threshold_changed(self, scale):
        """Handle threshold change."""
        self.threshold_min = self.min_scale.get_value()  # Already in 0-1 range
        self.threshold_max = self.max_scale.get_value()  # Already in 0-1 range
        self.logger.info(f"Thresholds changed: {self.threshold_min:.3f} - {self.threshold_max:.3f}")
        self._create_pyvista_volume()

    def _set_preset_range(self, min_val, max_val):
        """Set preset threshold range for common visualization modes."""
        self.min_scale.set_value(min_val)
        self.max_scale.set_value(max_val)
        self.threshold_min = min_val
        self.threshold_max = max_val
        self.logger.info(f"Set preset range: {min_val:.3f} - {max_val:.3f}")
        self._create_pyvista_volume()
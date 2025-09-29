#!/usr/bin/env python3
"""
Elastic Strain Energy 3D Visualization Dialog

Displays 3D visualization of elastic strain energy data from .img files
using heat map coloring and interactive 3D rendering.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject

import numpy as np
import matplotlib
matplotlib.use('GTK3Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg as FigureCanvas
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.cm as cm
from matplotlib.colors import Normalize, LinearSegmentedColormap
from matplotlib.colorbar import ColorbarBase
import logging
from pathlib import Path
from typing import Optional, Tuple


class ElasticStrainViewer(Gtk.Dialog):
    """
    Dialog for viewing 3D elastic strain energy visualization.

    Features:
    - 3D heat map visualization of strain energy
    - Interactive rotation and zoom
    - Color scale bar showing energy range
    - Cross-sectional views
    - Export capabilities
    """

    def __init__(self, parent_window, operation_name: str, img_file_path: Optional[str] = None):
        """
        Initialize the elastic strain viewer dialog.

        Args:
            parent_window: Parent window
            operation_name: Name of the elastic operation
            img_file_path: Path to the .img file containing strain energy data
        """
        super().__init__(
            title=f"3D Strain Energy Visualization - {operation_name}",
            parent=parent_window,
            modal=True
        )

        self.logger = logging.getLogger('VCCTL.ElasticStrainViewer')
        self.operation_name = operation_name
        self.img_file_path = img_file_path

        # Data storage
        self.strain_data = None
        self.dimensions = None
        self.voxel_size = (1.0, 1.0, 1.0)  # μm per voxel

        # Visualization settings
        self.colormap = 'hot'  # Good for energy visualization
        self.alpha = 0.8
        self.threshold_min = 0.0
        self.threshold_max = 1.0
        self.show_colorbar = True
        self.subsample_factor = 1  # Default to full resolution (no subsampling)

        # Setup dialog
        self.set_default_size(1200, 800)
        self.set_border_width(10)

        # Create UI
        self._setup_ui()

        # Load data if path provided
        if self.img_file_path:
            self.load_strain_data(self.img_file_path)

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

        # Colormap selection
        cmap_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        cmap_label = Gtk.Label("Colormap:")
        cmap_label.set_size_request(100, -1)
        cmap_label.set_halign(Gtk.Align.START)
        self.cmap_combo = Gtk.ComboBoxText()
        for cmap in ['hot', 'viridis', 'plasma', 'inferno', 'magma', 'coolwarm', 'jet', 'turbo']:
            self.cmap_combo.append_text(cmap)
        self.cmap_combo.set_active(0)
        self.cmap_combo.connect('changed', self._on_colormap_changed)
        cmap_box.pack_start(cmap_label, False, False, 0)
        cmap_box.pack_start(self.cmap_combo, True, True, 0)
        vis_box.pack_start(cmap_box, False, False, 0)

        # Alpha (transparency)
        alpha_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        alpha_label = Gtk.Label("Transparency:")
        alpha_label.set_size_request(100, -1)
        alpha_label.set_halign(Gtk.Align.START)
        self.alpha_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0.1, 1.0, 0.1)
        self.alpha_scale.set_value(self.alpha)
        self.alpha_scale.set_draw_value(True)
        self.alpha_scale.connect('value-changed', self._on_alpha_changed)
        alpha_box.pack_start(alpha_label, False, False, 0)
        alpha_box.pack_start(self.alpha_scale, True, True, 0)
        vis_box.pack_start(alpha_box, False, False, 0)

        # Threshold controls frame
        thresh_frame = Gtk.Frame(label="Energy Threshold")
        thresh_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        thresh_box.set_margin_left(10)
        thresh_box.set_margin_right(10)
        thresh_box.set_margin_top(10)
        thresh_box.set_margin_bottom(10)
        thresh_frame.add(thresh_box)
        controls_box.pack_start(thresh_frame, False, False, 0)

        # Min threshold
        min_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        min_label = Gtk.Label("Min (%):")
        min_label.set_size_request(100, -1)
        min_label.set_halign(Gtk.Align.START)
        self.min_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
        self.min_scale.set_value(0)
        self.min_scale.set_draw_value(True)
        self.min_scale.connect('value-changed', self._on_threshold_changed)
        min_box.pack_start(min_label, False, False, 0)
        min_box.pack_start(self.min_scale, True, True, 0)
        thresh_box.pack_start(min_box, False, False, 0)

        # Max threshold
        max_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        max_label = Gtk.Label("Max (%):")
        max_label.set_size_request(100, -1)
        max_label.set_halign(Gtk.Align.START)
        self.max_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
        self.max_scale.set_value(100)
        self.max_scale.set_draw_value(True)
        self.max_scale.connect('value-changed', self._on_threshold_changed)
        max_box.pack_start(max_label, False, False, 0)
        max_box.pack_start(self.max_scale, True, True, 0)
        thresh_box.pack_start(max_box, False, False, 0)

        # Performance settings frame
        perf_frame = Gtk.Frame(label="Performance Settings")
        perf_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        perf_box.set_margin_left(10)
        perf_box.set_margin_right(10)
        perf_box.set_margin_top(10)
        perf_box.set_margin_bottom(10)
        perf_frame.add(perf_box)
        controls_box.pack_start(perf_frame, False, False, 0)

        # Subsampling factor
        subsample_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        subsample_label = Gtk.Label("Subsampling:")
        subsample_label.set_size_request(100, -1)
        subsample_label.set_halign(Gtk.Align.START)
        self.subsample_combo = Gtk.ComboBoxText()
        self.subsample_combo.append_text("Full Resolution (1)")
        self.subsample_combo.append_text("Half Resolution (2)")
        self.subsample_combo.append_text("Quarter Resolution (4)")
        self.subsample_combo.set_active(0)  # Default to full resolution
        self.subsample_combo.connect('changed', self._on_subsample_changed)
        subsample_box.pack_start(subsample_label, False, False, 0)
        subsample_box.pack_start(self.subsample_combo, True, True, 0)
        perf_box.pack_start(subsample_box, False, False, 0)

        # Statistics frame
        stats_frame = Gtk.Frame(label="Strain Energy Statistics")
        self.stats_label = Gtk.Label()
        self.stats_label.set_markup("<small>No data loaded</small>")
        self.stats_label.set_margin_left(10)
        self.stats_label.set_margin_right(10)
        self.stats_label.set_margin_top(10)
        self.stats_label.set_margin_bottom(10)
        self.stats_label.set_halign(Gtk.Align.START)
        stats_frame.add(self.stats_label)
        controls_box.pack_start(stats_frame, False, False, 0)

        # Export button
        export_button = Gtk.Button("Export View")
        export_button.connect('clicked', self._on_export_clicked)
        controls_box.pack_start(export_button, False, False, 0)

        # Right panel - 3D visualization
        viz_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        main_box.pack_start(viz_box, True, True, 0)

        # Create matplotlib figure for 3D plot
        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.set_size_request(800, 600)

        # Add canvas to scrolled window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.add(self.canvas)
        viz_box.pack_start(scrolled, True, True, 0)

        # View controls
        view_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        view_box.set_margin_top(10)
        viz_box.pack_start(view_box, False, False, 0)

        view_label = Gtk.Label("View:")
        view_box.pack_start(view_label, False, False, 0)

        for view_name in ['Isometric', 'Top', 'Front', 'Side']:
            button = Gtk.Button(view_name)
            button.connect('clicked', self._on_view_changed, view_name.lower())
            view_box.pack_start(button, False, False, 0)

    def load_strain_data(self, img_file_path: str) -> bool:
        """
        Load strain energy data from .img file.

        Args:
            img_file_path: Path to the .img file

        Returns:
            Success status
        """
        try:
            path = Path(img_file_path)
            if not path.exists():
                self.logger.error(f"Image file not found: {img_file_path}")
                return False

            # Parse the header-based .img format
            x_dim = y_dim = z_dim = None
            data_values = []

            with open(path, 'r') as f:
                # Read header section
                line_count = 0
                for line in f:
                    line = line.strip()
                    line_count += 1

                    # Parse header fields
                    if line.startswith("X_Size:"):
                        x_dim = int(line.split(":")[1].strip())
                    elif line.startswith("Y_Size:"):
                        y_dim = int(line.split(":")[1].strip())
                    elif line.startswith("Z_Size:"):
                        z_dim = int(line.split(":")[1].strip())
                    elif line.startswith("Image_Resolution:"):
                        resolution = float(line.split(":")[1].strip())
                        self.voxel_size = (resolution, resolution, resolution)
                    else:
                        # Try to parse as strain energy data
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
            self.logger.info(f"Image dimensions: {x_dim} x {y_dim} x {z_dim}")
            self.logger.info(f"Voxel resolution: {self.voxel_size[0]} μm")

            # Check if this is summary data or full 3D voxel data
            expected_size = x_dim * y_dim * z_dim
            if len(data_values) != expected_size:
                self.logger.warning(f"Data size mismatch: expected {expected_size}, got {len(data_values)}")

                # Check if this looks like summary data (much smaller than expected)
                if len(data_values) < expected_size * 0.1:  # Less than 10% of expected size
                    self.logger.info(f"Detected summary data format: {len(data_values)} values instead of {expected_size}")
                    self.logger.info("This appears to be aggregated elastic data rather than per-voxel strain energy")

                    # Create a simple 1D visualization of the summary data
                    self.strain_data = np.array(data_values)
                    self.is_summary_data = True
                    self.dimensions = (len(data_values), 1, 1)  # Override dimensions for summary data

                    # Update statistics
                    self._update_statistics()

                    # Render summary visualization
                    self._render_summary_data()
                    return True
                else:
                    # Try to proceed with available data if size is close
                    if len(data_values) < expected_size:
                        self.logger.warning(f"Padding data with zeros to reach expected size")
                        data_values.extend([0.0] * (expected_size - len(data_values)))
                    else:
                        self.logger.warning(f"Truncating data to expected size")
                        data_values = data_values[:expected_size]

            # Reshape data to 3D array (Z, Y, X order)
            self.strain_data = np.array(data_values).reshape(z_dim, y_dim, x_dim)
            self.is_summary_data = False

            self.logger.info(f"Loaded {len(data_values)} strain energy values")
            self.logger.info(f"Data range: {np.min(self.strain_data):.2e} to {np.max(self.strain_data):.2e}")

            # Update statistics
            self._update_statistics()

            # Render the visualization
            self.render_3d()

            self.logger.info(f"Successfully loaded strain energy data from {img_file_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error loading strain data: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _update_statistics(self):
        """Update the statistics display."""
        if self.strain_data is None:
            return

        # Calculate statistics
        min_val = np.min(self.strain_data)
        max_val = np.max(self.strain_data)
        mean_val = np.mean(self.strain_data)
        std_val = np.std(self.strain_data)

        # Count voxels with strain energy above a small threshold (to avoid numerical noise)
        threshold = max_val * 0.001  # 0.1% of max value
        above_threshold = np.sum(self.strain_data > threshold)
        total = self.strain_data.size
        percent_significant = (above_threshold / total) * 100

        # Update label
        stats_text = f"""<small>
<b>Min:</b> {min_val:.2e}
<b>Max:</b> {max_val:.2e}
<b>Mean:</b> {mean_val:.2e}
<b>Std Dev:</b> {std_val:.2e}
<b>Total Voxels:</b> {total:,}
<b>Above 0.1% Max:</b> {above_threshold:,} ({percent_significant:.2f}%)
</small>"""
        self.stats_label.set_markup(stats_text)

    def render_3d(self):
        """Render the 3D strain energy visualization."""
        if self.strain_data is None:
            self.logger.warning("No strain data to render")
            return

        try:
            self.logger.info(f"Starting 3D render with data shape: {self.strain_data.shape}")
            self.figure.clear()

            # Create subplot with 3D projection
            ax = self.figure.add_subplot(111, projection='3d')

            # Subsample for performance if needed (only for very large datasets)
            data = self.strain_data
            # Only subsample if dataset is larger than 200^3 (8 million voxels) and subsample factor > 1
            if self.strain_data.size > 200**3 and self.subsample_factor > 1:
                data = self.strain_data[::self.subsample_factor,
                                       ::self.subsample_factor,
                                       ::self.subsample_factor]
                self.logger.info(f"Subsampled data from {self.strain_data.shape} to {data.shape} (factor: {self.subsample_factor})")
            else:
                self.logger.info(f"Using full resolution data: {data.shape}")

            # Create coordinate arrays (1-based indexing to match expected ranges)
            z_dim, y_dim, x_dim = data.shape
            self.logger.info(f"Data dimensions: X={x_dim} (1-{x_dim}), Y={y_dim} (1-{y_dim}), Z={z_dim} (1-{z_dim})")

            # Apply thresholds
            min_val = np.min(data)
            max_val = np.max(data)
            self.logger.info(f"Data range: {min_val:.2e} to {max_val:.2e}")

            # Calculate threshold values as percentiles of the data range
            thresh_min_pct = self.threshold_min  # 0-100
            thresh_max_pct = self.threshold_max  # 0-100

            # Convert percentiles to actual values
            if max_val > min_val:
                thresh_min = min_val + (max_val - min_val) * (thresh_min_pct / 100.0)
                thresh_max = min_val + (max_val - min_val) * (thresh_max_pct / 100.0)
            else:
                # Handle case where all values are the same
                thresh_min = min_val
                thresh_max = max_val

            self.logger.info(f"Threshold percentiles: {thresh_min_pct}% to {thresh_max_pct}%")
            self.logger.info(f"Threshold range: {thresh_min:.2e} to {thresh_max:.2e}")

            # Create mask for values within threshold
            mask = (data >= thresh_min) & (data <= thresh_max)

            # Get indices of masked voxels (in array coordinates)
            zi, yi, xi = np.where(mask)
            self.logger.info(f"Found {len(zi)} voxels within threshold range")

            # Convert to 1-based coordinates for visualization
            # Array indices: zi=z-dimension, yi=y-dimension, xi=x-dimension
            if len(zi) > 0:
                self.logger.info(f"Array coordinate ranges: X({np.min(xi)}-{np.max(xi)}), Y({np.min(yi)}-{np.max(yi)}), Z({np.min(zi)}-{np.max(zi)})")

            if len(zi) > 0:
                # Get strain values for color mapping
                strain_values = data[zi, yi, xi]

                # Normalize colors
                norm = Normalize(vmin=thresh_min, vmax=thresh_max)
                cmap = cm.get_cmap(self.colormap)
                colors = cmap(norm(strain_values))

                # Plot as scatter plot for better performance
                # Limit number of points if too many
                max_points = 50000
                if len(zi) > max_points:
                    # Random sampling
                    indices = np.random.choice(len(zi), max_points, replace=False)
                    xi = xi[indices]
                    yi = yi[indices]
                    zi = zi[indices]
                    colors = colors[indices]

                # Use 1-based coordinates for scatter plot
                x_vis = xi + 1
                y_vis = yi + 1
                z_vis = zi + 1

                scatter = ax.scatter(x_vis, y_vis, z_vis, c=colors,
                                   s=20, alpha=self.alpha,
                                   edgecolors='none')
                self.logger.info(f"Created scatter plot with {len(xi)} points")

                # Add colorbar
                if self.show_colorbar:
                    # Create a separate axis for colorbar
                    cbar_ax = self.figure.add_axes([0.88, 0.15, 0.03, 0.7])
                    cb = ColorbarBase(cbar_ax, cmap=cmap, norm=norm,
                                     orientation='vertical')
                    cb.set_label('Strain Energy', rotation=270, labelpad=20)

                    # Format tick labels in scientific notation
                    import matplotlib.ticker as ticker
                    cb.formatter = ticker.ScalarFormatter(useMathText=True)
                    cb.formatter.set_powerlimits((0, 0))
                    cb.update_ticks()

            # Set labels
            ax.set_xlabel('X (voxels)')
            ax.set_ylabel('Y (voxels)')
            ax.set_zlabel('Z (voxels)')
            ax.set_title(f'Elastic Strain Energy - {self.operation_name}')

            # Set proper axis limits to show 1-based coordinates matching expected dimensions
            # Original dimensions from the file header
            orig_x, orig_y, orig_z = self.dimensions
            ax.set_xlim(1, orig_x)
            ax.set_ylim(1, orig_y)
            ax.set_zlim(1, orig_z)

            self.logger.info(f"Set axis limits: X(1-{orig_x}), Y(1-{orig_y}), Z(1-{orig_z})")

            # Set aspect ratio based on original dimensions
            ax.set_box_aspect([orig_x, orig_y, orig_z])

            self.canvas.draw()

        except Exception as e:
            self.logger.error(f"Error rendering 3D visualization: {e}")
            import traceback
            traceback.print_exc()

    def _on_colormap_changed(self, combo):
        """Handle colormap change."""
        self.colormap = combo.get_active_text()
        self.render_3d()

    def _on_alpha_changed(self, scale):
        """Handle transparency change."""
        self.alpha = scale.get_value()
        self.render_3d()

    def _on_threshold_changed(self, scale):
        """Handle threshold change."""
        self.threshold_min = self.min_scale.get_value() / 100.0
        self.threshold_max = self.max_scale.get_value() / 100.0
        self.render_3d()

    def _on_subsample_changed(self, combo):
        """Handle subsampling factor change."""
        active_text = combo.get_active_text()
        if "Full Resolution (1)" in active_text:
            self.subsample_factor = 1
        elif "Half Resolution (2)" in active_text:
            self.subsample_factor = 2
        elif "Quarter Resolution (4)" in active_text:
            self.subsample_factor = 4

        self.logger.info(f"Subsampling factor changed to: {self.subsample_factor}")
        self.render_3d()

    def _on_view_changed(self, button, view):
        """Handle view angle change."""
        if self.strain_data is None:
            return

        ax = self.figure.get_axes()[0]
        if view == 'isometric':
            ax.view_init(elev=30, azim=45)
        elif view == 'top':
            ax.view_init(elev=90, azim=0)
        elif view == 'front':
            ax.view_init(elev=0, azim=0)
        elif view == 'side':
            ax.view_init(elev=0, azim=90)

        self.canvas.draw()

    def _on_export_clicked(self, button):
        """Handle export button click."""
        dialog = Gtk.FileChooserDialog(
            title="Export 3D View",
            parent=self,
            action=Gtk.FileChooserAction.SAVE
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_SAVE, Gtk.ResponseType.OK
        )
        dialog.set_current_name(f"{self.operation_name}_strain_energy.png")

        # Add file filters
        filter_png = Gtk.FileFilter()
        filter_png.set_name("PNG Image")
        filter_png.add_pattern("*.png")
        dialog.add_filter(filter_png)

        filter_pdf = Gtk.FileFilter()
        filter_pdf.set_name("PDF Document")
        filter_pdf.add_pattern("*.pdf")
        dialog.add_filter(filter_pdf)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            try:
                self.figure.savefig(filename, dpi=150, bbox_inches='tight')
                self.logger.info(f"Exported view to {filename}")
            except Exception as e:
                self.logger.error(f"Error exporting view: {e}")

        dialog.destroy()
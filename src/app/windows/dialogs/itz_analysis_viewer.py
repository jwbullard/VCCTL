#!/usr/bin/env python3
"""
ITZ Analysis Viewer Dialog

Displays ITZ (Interfacial Transition Zone) moduli analysis from ITZmoduli.csv file
with both tabular data and plotting capabilities.
"""

import gi
import logging
import csv
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Pango

try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg as FigureCanvas
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

class ITZAnalysisViewer(Gtk.Dialog):
    """Dialog for viewing ITZ elastic moduli analysis."""

    def __init__(self, parent, operation):
        """Initialize the ITZ analysis viewer."""
        super().__init__(
            title=f"ITZ Analysis - {operation.name}",
            parent=parent,
            flags=0
        )

        self.logger = logging.getLogger('VCCTL.ITZAnalysisViewer')
        self.operation = operation
        self.itz_data = []

        # Set dialog properties
        self.set_default_size(800, 600)
        self.set_resizable(True)

        # Add buttons
        self.add_button("Close", Gtk.ResponseType.CLOSE)
        if MATPLOTLIB_AVAILABLE:
            self.add_button("Export Plot", Gtk.ResponseType.ACCEPT)

        # Create UI
        self._setup_ui()

        # Load and display data
        self._load_itz_data()

    def _setup_ui(self):
        """Setup the dialog UI."""
        content_area = self.get_content_area()
        content_area.set_spacing(12)
        content_area.set_margin_top(12)
        content_area.set_margin_bottom(12)
        content_area.set_margin_left(12)
        content_area.set_margin_right(12)

        # Title
        title_label = Gtk.Label()
        title_label.set_markup(f"<b><big>Interfacial Transition Zone Analysis</big></b>")
        title_label.set_margin_bottom(12)
        content_area.pack_start(title_label, False, False, 0)

        # Create notebook for tabs
        self.notebook = Gtk.Notebook()

        # Data table tab
        self._create_data_tab()

        # Plot tab (if matplotlib available)
        if MATPLOTLIB_AVAILABLE:
            self._create_plot_tab()
        else:
            # Show message about matplotlib
            no_plot_label = Gtk.Label()
            no_plot_label.set_markup("<i>Matplotlib not available - plotting disabled</i>")
            self.notebook.append_page(no_plot_label, Gtk.Label("Plot (N/A)"))

        content_area.pack_start(self.notebook, True, True, 0)

        self.show_all()

    def _create_data_tab(self):
        """Create the data table tab."""
        # Create scrolled window for table
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_shadow_type(Gtk.ShadowType.IN)

        # Create tree view for displaying ITZ data
        self.treeview = Gtk.TreeView()
        self.treeview.set_grid_lines(Gtk.TreeViewGridLines.BOTH)

        # Create columns based on ITZ data format
        columns = [
            ("Distance (μm)", str, 100),
            ("Bulk Modulus (GPa)", str, 150),
            ("Shear Modulus (GPa)", str, 150),
            ("Young's Modulus (GPa)", str, 150),
            ("Poisson's Ratio", str, 120)
        ]

        for i, (title, col_type, width) in enumerate(columns):
            renderer = Gtk.CellRendererText()
            if i == 0:  # Distance column
                renderer.set_property("weight", Pango.Weight.BOLD)
            column = Gtk.TreeViewColumn(title, renderer, text=i)
            column.set_min_width(width)
            column.set_resizable(True)
            column.set_sort_column_id(i)
            self.treeview.append_column(column)

        # Create list store
        self.liststore = Gtk.ListStore(str, str, str, str, str)
        self.treeview.set_model(self.liststore)

        scrolled.add(self.treeview)

        # Add description
        data_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        desc_label = Gtk.Label()
        desc_label.set_markup("<i>Elastic moduli variation as a function of distance from aggregate surface</i>")
        desc_label.set_margin_bottom(6)
        data_box.pack_start(desc_label, False, False, 0)

        data_box.pack_start(scrolled, True, True, 0)

        self.notebook.append_page(data_box, Gtk.Label("Data Table"))

    def _create_plot_tab(self):
        """Create the plotting tab."""
        plot_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        # Controls
        controls_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        controls_box.set_margin_bottom(6)

        # Property selection
        prop_label = Gtk.Label("Property to plot:")
        controls_box.pack_start(prop_label, False, False, 0)

        self.property_combo = Gtk.ComboBoxText()
        self.property_combo.append_text("Bulk Modulus")
        self.property_combo.append_text("Shear Modulus")
        self.property_combo.append_text("Young's Modulus")
        self.property_combo.append_text("Poisson's Ratio")
        self.property_combo.set_active(2)  # Default to Young's modulus
        self.property_combo.connect("changed", self._on_property_changed)
        controls_box.pack_start(self.property_combo, False, False, 0)

        plot_box.pack_start(controls_box, False, False, 0)

        # Create matplotlib figure
        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        plot_box.pack_start(self.canvas, True, True, 0)

        self.notebook.append_page(plot_box, Gtk.Label("Plot"))

    def _load_itz_data(self):
        """Load ITZ data from CSV file."""
        try:
            # Find the ITZmoduli.csv file
            operation_dir = self._get_operation_directory()
            if not operation_dir:
                self._show_error("Could not find operation directory")
                return

            itz_file = Path(operation_dir) / "ITZmoduli.csv"
            if not itz_file.exists():
                self._show_error("ITZmoduli.csv file not found")
                return

            # Read and parse CSV data
            self.itz_data = self._parse_itz_csv(itz_file)

            # Populate the tree view
            self._populate_treeview()

            # Create initial plot if matplotlib available
            if MATPLOTLIB_AVAILABLE and self.itz_data:
                self._create_plot()

        except Exception as e:
            self.logger.error(f"Error loading ITZ data: {e}")
            self._show_error(f"Error loading data: {e}")

    def _get_operation_directory(self) -> Optional[str]:
        """Get the operation output directory."""
        try:
            # First check if operation has folder_path (from Results panel)
            if hasattr(self.operation, 'folder_path'):
                return self.operation.folder_path

            # Check if operation has output_directory (from database)
            if hasattr(self.operation, 'output_directory') and self.operation.output_directory:
                return self.operation.output_directory

            # Legacy fallback: scan filesystem for nested elastic operation
            if hasattr(self.operation, 'name') and self.operation.name.startswith('Elastic-'):
                # Get operations directory from service container
                from app.services.service_container import ServiceContainer
                service_container = ServiceContainer()
                operations_base = service_container.directories_service.get_operations_path()

                for parent_dir in operations_base.iterdir():
                    if parent_dir.is_dir():
                        elastic_path = parent_dir / self.operation.name
                        if elastic_path.exists():
                            return str(elastic_path)

            return None

        except Exception as e:
            self.logger.error(f"Error finding operation directory: {e}")
            return None

    def _parse_itz_csv(self, csv_file: Path) -> List[Dict[str, float]]:
        """Parse the ITZmoduli.csv file."""
        data = []

        try:
            with open(csv_file, 'r') as f:
                # First, try to detect if the file has headers
                first_line = f.readline().strip()
                f.seek(0)  # Reset to beginning

                # Check if first line contains headers (non-numeric first field)
                try:
                    float(first_line.split(',')[0])
                    has_headers = False
                    self.logger.info("ITZ CSV file detected without headers")
                except ValueError:
                    has_headers = True
                    self.logger.info("ITZ CSV file detected with headers")

                if has_headers:
                    # Use DictReader for files with headers
                    csv_reader = csv.DictReader(f)
                    for row in csv_reader:
                        try:
                            data_row = {
                                'distance': float(row['Distance (um)']),
                                'bulk_modulus': float(row['Bulk Modulus (GPa)']),
                                'shear_modulus': float(row['Shear Modulus (GPa)']),  # Removed the space
                                'youngs_modulus': float(row['Elastic Modulus (GPa)']),  # Changed name
                                'poissons_ratio': float(row['Poisson Ratio'])  # Match your file header
                            }
                            data.append(data_row)
                        except (ValueError, KeyError) as e:
                            self.logger.warning(f"Skipping invalid row: {row}, error: {e}")
                else:
                    # Use regular reader for files without headers (assume column order)
                    csv_reader = csv.reader(f)
                    for row_num, row in enumerate(csv_reader):
                        try:
                            if len(row) >= 5:
                                data_row = {
                                    'distance': float(row[0]),
                                    'bulk_modulus': float(row[1]),
                                    'shear_modulus': float(row[2]),
                                    'youngs_modulus': float(row[3]),
                                    'poissons_ratio': float(row[4])
                                }
                                data.append(data_row)
                            else:
                                self.logger.warning(f"Row {row_num + 1} has insufficient columns: {row}")
                        except (ValueError, IndexError) as e:
                            self.logger.warning(f"Skipping invalid row {row_num + 1}: {row}, error: {e}")

            self.logger.info(f"Successfully parsed {len(data)} rows from ITZ CSV file")
            return data

        except Exception as e:
            self.logger.error(f"Error parsing ITZ CSV file: {e}")
            return []

    def _populate_treeview(self):
        """Populate the tree view with ITZ data."""
        self.liststore.clear()

        for row in self.itz_data:
            self.liststore.append([
                f"{row['distance']:.1f}",
                f"{row['bulk_modulus']:.4f}",
                f"{row['shear_modulus']:.4f}",
                f"{row['youngs_modulus']:.4f}",
                f"{row['poissons_ratio']:.4f}"
            ])

    def _create_plot(self):
        """Create the matplotlib plot."""
        if not MATPLOTLIB_AVAILABLE or not self.itz_data:
            return

        # Clear previous plot
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        # Get selected property
        property_index = self.property_combo.get_active()
        property_names = ['bulk_modulus', 'shear_modulus', 'youngs_modulus', 'poissons_ratio']
        property_labels = ['Bulk Modulus (GPa)', 'Shear Modulus (GPa)', "Young's Modulus (GPa)", "Poisson's Ratio"]

        if property_index >= 0:
            property_key = property_names[property_index]
            property_label = property_labels[property_index]

            # Extract data
            distances = [row['distance'] for row in self.itz_data]
            values = [row[property_key] for row in self.itz_data]

            # Create main data plot
            ax.plot(distances, values, 'bo-', linewidth=2, markersize=6, label='Data')
            ax.set_xlabel('Distance from Aggregate Surface (μm)')
            ax.set_ylabel(property_label)
            ax.set_title(f'ITZ {property_label} vs Distance')
            ax.grid(True, alpha=0.3)

            # Calculate ITZ width (median cement particle size)
            itz_width = self._calculate_itz_width()
            self.logger.info(f"ITZ width calculated: {itz_width}")

            if itz_width is not None:
                self.logger.info(f"Adding ITZ width line at {itz_width:.2f} μm")
                # Add vertical dashed line at ITZ width
                ax.axvline(x=itz_width, color='green', linestyle='--', linewidth=2,
                          label=f'ITZ Width: {itz_width:.2f} μm')

                # Calculate average property values within and outside ITZ
                avg_within_itz, avg_outside_itz = self._calculate_property_averages(
                    distances, values, itz_width
                )

                if avg_within_itz is not None and avg_outside_itz is not None:
                    # Add horizontal dashed lines for averages
                    ax.axhline(y=avg_within_itz, color='orange', linestyle='--', linewidth=1.5,
                              alpha=0.7, label=f'Avg within ITZ: {avg_within_itz:.4f}')
                    ax.axhline(y=avg_outside_itz, color='purple', linestyle='--', linewidth=1.5,
                              alpha=0.7, label=f'Avg outside ITZ: {avg_outside_itz:.4f}')
                else:
                    self.logger.warning("ITZ width calculated but property averages could not be computed")
            else:
                self.logger.warning("ITZ width could not be calculated - cement_psd.csv may be missing")

            ax.legend(loc='best')

        self.figure.tight_layout()
        self.canvas.draw()

    def _calculate_itz_width(self) -> Optional[float]:
        """
        Calculate ITZ width as the median cement particle size from cement_psd.csv.
        Returns the 50th percentile particle diameter in micrometers.
        """
        try:
            # Find cement_psd.csv file in operation directory
            operation_dir = self._get_operation_directory()
            self.logger.info(f"ITZ width calculation: operation_dir = {operation_dir}")
            if not operation_dir:
                self.logger.warning("Could not find operation directory for cement PSD")
                return None

            # Look for cement_psd.csv in the operation directory
            cement_psd_file = Path(operation_dir) / "cement_psd.csv"
            self.logger.info(f"ITZ width calculation: looking for {cement_psd_file}")

            if not cement_psd_file.exists():
                # If not found in elastic operation directory, try parent hydration directory
                parent_dir = Path(operation_dir).parent
                cement_psd_file = parent_dir / "cement_psd.csv"
                self.logger.info(f"ITZ width calculation: not found, trying parent directory: {cement_psd_file}")

                if not cement_psd_file.exists():
                    self.logger.warning(f"cement_psd.csv not found in {operation_dir} or parent directory")
                    # List files in directory for debugging
                    try:
                        files = list(Path(operation_dir).glob("*"))
                        self.logger.info(f"Files in {operation_dir}: {[f.name for f in files]}")
                        parent_files = list(parent_dir.glob("*"))
                        self.logger.info(f"Files in parent {parent_dir}: {[f.name for f in parent_files]}")
                    except Exception as e:
                        self.logger.error(f"Error listing directory: {e}")
                    return None

            self.logger.info(f"Found cement_psd.csv at {cement_psd_file}")

            # Read PSD data
            diameters = []
            volume_fractions = []

            with open(cement_psd_file, 'r') as f:
                csv_reader = csv.reader(f)
                # Skip header if present
                first_line = next(csv_reader, None)
                if first_line:
                    try:
                        # Try to parse as numeric data
                        diameters.append(float(first_line[0]))
                        volume_fractions.append(float(first_line[1]))
                    except ValueError:
                        # First line was a header, skip it
                        pass

                # Read remaining data
                for row in csv_reader:
                    if len(row) >= 2:
                        try:
                            diameters.append(float(row[0]))
                            volume_fractions.append(float(row[1]))
                        except ValueError:
                            continue

            if not diameters or not volume_fractions:
                self.logger.warning("No valid PSD data found in cement_psd.csv")
                return None

            # Calculate cumulative volume fractions
            total_volume = sum(volume_fractions)
            if total_volume == 0:
                self.logger.warning("Total volume in PSD is zero")
                return None

            # Normalize volume fractions
            normalized_fractions = [vf / total_volume for vf in volume_fractions]

            # Calculate cumulative distribution
            cumulative = []
            cumsum = 0.0
            for vf in normalized_fractions:
                cumsum += vf
                cumulative.append(cumsum)

            # Find median (50th percentile) by interpolation
            median_diameter = None
            for i in range(len(cumulative) - 1):
                if cumulative[i] <= 0.5 <= cumulative[i + 1]:
                    # Linear interpolation between points
                    fraction = (0.5 - cumulative[i]) / (cumulative[i + 1] - cumulative[i])
                    median_diameter = diameters[i] + fraction * (diameters[i + 1] - diameters[i])
                    break

            # Handle edge cases
            if median_diameter is None:
                if cumulative[-1] < 0.5:
                    median_diameter = diameters[-1]
                elif cumulative[0] > 0.5:
                    median_diameter = diameters[0]
                else:
                    # Use simple average as fallback
                    median_diameter = sum(d * vf for d, vf in zip(diameters, normalized_fractions))

            self.logger.info(f"Calculated ITZ width (median cement particle size): {median_diameter:.2f} μm")
            return median_diameter

        except Exception as e:
            self.logger.error(f"Error calculating ITZ width from cement PSD: {e}")
            return None

    def _calculate_property_averages(self, distances: List[float], values: List[float],
                                    itz_width: float) -> Tuple[Optional[float], Optional[float]]:
        """
        Calculate average property values within and outside the ITZ.

        Args:
            distances: List of distance values from aggregate surface
            values: List of property values corresponding to distances
            itz_width: ITZ width threshold in micrometers

        Returns:
            Tuple of (average within ITZ, average outside ITZ)
        """
        try:
            if not distances or not values or len(distances) != len(values):
                return None, None

            # Separate data into within and outside ITZ
            within_itz_values = []
            outside_itz_values = []

            for dist, val in zip(distances, values):
                if dist <= itz_width:
                    within_itz_values.append(val)
                else:
                    outside_itz_values.append(val)

            # Calculate averages
            avg_within = np.mean(within_itz_values) if within_itz_values else None
            avg_outside = np.mean(outside_itz_values) if outside_itz_values else None

            if avg_within is not None:
                self.logger.info(f"Average within ITZ (≤{itz_width:.2f} μm): {avg_within:.4f}")
            if avg_outside is not None:
                self.logger.info(f"Average outside ITZ (>{itz_width:.2f} μm): {avg_outside:.4f}")

            return avg_within, avg_outside

        except Exception as e:
            self.logger.error(f"Error calculating property averages: {e}")
            return None, None

    def _on_property_changed(self, combo):
        """Handle property selection change."""
        if MATPLOTLIB_AVAILABLE:
            self._create_plot()

    def _show_error(self, message: str):
        """Show error message in the dialog."""
        error_label = Gtk.Label()
        error_label.set_markup(f"<b>Error:</b> {message}")
        error_label.set_halign(Gtk.Align.CENTER)
        error_label.set_margin_top(50)

        # Add to first tab
        if hasattr(self, 'notebook'):
            error_box = Gtk.Box()
            error_box.pack_start(error_label, True, True, 0)
            self.notebook.append_page(error_box, Gtk.Label("Error"))
        else:
            content_area = self.get_content_area()
            content_area.pack_start(error_label, True, True, 0)

        error_label.show()

    def run(self):
        """Run the dialog and handle export if requested."""
        response = super().run()

        if response == Gtk.ResponseType.ACCEPT and MATPLOTLIB_AVAILABLE:
            # Export plot
            self._export_plot()

        return response

    def _export_plot(self):
        """Export the current plot to file."""
        dialog = Gtk.FileChooserDialog(
            title="Export Plot",
            parent=self,
            action=Gtk.FileChooserAction.SAVE
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_SAVE, Gtk.ResponseType.OK
        )

        # Add file filters
        filter_png = Gtk.FileFilter()
        filter_png.set_name("PNG images")
        filter_png.add_pattern("*.png")
        dialog.add_filter(filter_png)

        filter_pdf = Gtk.FileFilter()
        filter_pdf.set_name("PDF files")
        filter_pdf.add_pattern("*.pdf")
        dialog.add_filter(filter_pdf)

        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            try:
                self.figure.savefig(filename, dpi=300, bbox_inches='tight')
                self.logger.info(f"Plot exported to {filename}")
            except Exception as e:
                self.logger.error(f"Error exporting plot: {e}")

        dialog.destroy()
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
            # Check for nested elastic operation (common case)
            if hasattr(self.operation, 'name') and self.operation.name.startswith('Elastic-'):
                operations_base = Path("Operations")
                for parent_dir in operations_base.iterdir():
                    if parent_dir.is_dir():
                        elastic_path = parent_dir / self.operation.name
                        if elastic_path.exists():
                            return str(elastic_path)

            # Check direct path
            direct_path = Path("Operations") / self.operation.name
            if direct_path.exists():
                return str(direct_path)

            return None

        except Exception as e:
            self.logger.error(f"Error finding operation directory: {e}")
            return None

    def _parse_itz_csv(self, csv_file: Path) -> List[Dict[str, float]]:
        """Parse the ITZmoduli.csv file."""
        data = []

        with open(csv_file, 'r') as f:
            csv_reader = csv.DictReader(f)
            for row in csv_reader:
                try:
                    data_row = {
                        'distance': float(row['Distance (um)']),
                        'bulk_modulus': float(row['Bulk Modulus (GPa)']),
                        'shear_modulus': float(row[' Shear Modulus (GPa)']),  # Note the space
                        'youngs_modulus': float(row['Young\'s Modulus (GPa)']),
                        'poissons_ratio': float(row['Poisson\'s ratio'])
                    }
                    data.append(data_row)
                except (ValueError, KeyError) as e:
                    self.logger.warning(f"Skipping invalid row: {row}, error: {e}")

        return data

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

            # Create plot
            ax.plot(distances, values, 'bo-', linewidth=2, markersize=6)
            ax.set_xlabel('Distance from Aggregate Surface (μm)')
            ax.set_ylabel(property_label)
            ax.set_title(f'ITZ {property_label} vs Distance')
            ax.grid(True, alpha=0.3)

            # Add trend line if we have enough points
            if len(distances) > 2:
                z = np.polyfit(distances, values, 1)
                p = np.poly1d(z)
                ax.plot(distances, p(distances), "r--", alpha=0.8,
                       label=f'Trend: y = {z[0]:.4f}x + {z[1]:.4f}')
                ax.legend()

        self.figure.tight_layout()
        self.canvas.draw()

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
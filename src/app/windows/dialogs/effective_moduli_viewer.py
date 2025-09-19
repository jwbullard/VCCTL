#!/usr/bin/env python3
"""
Effective Moduli Viewer Dialog

Displays the effective elastic moduli results from EffectiveModuli.csv file
in a table format with clear units and descriptions.
"""

import gi
import logging
import csv
from pathlib import Path
from typing import Dict, List, Tuple, Optional

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Pango

class EffectiveModuliViewer(Gtk.Dialog):
    """Dialog for viewing effective elastic moduli results."""

    def __init__(self, parent, operation):
        """Initialize the effective moduli viewer."""
        super().__init__(
            title=f"Effective Moduli Results - {operation.name}",
            parent=parent,
            flags=0
        )

        self.logger = logging.getLogger('VCCTL.EffectiveModuliViewer')
        self.operation = operation

        # Set dialog properties
        self.set_default_size(600, 400)
        self.set_resizable(True)

        # Add buttons
        self.add_button("Close", Gtk.ResponseType.CLOSE)

        # Create UI
        self._setup_ui()

        # Load and display data
        self._load_moduli_data()

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
        title_label.set_markup(f"<b><big>Effective Elastic Moduli</big></b>")
        title_label.set_margin_bottom(12)
        content_area.pack_start(title_label, False, False, 0)

        # Create scrolled window for table
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_shadow_type(Gtk.ShadowType.IN)

        # Create tree view for displaying moduli data
        self.treeview = Gtk.TreeView()
        self.treeview.set_grid_lines(Gtk.TreeViewGridLines.BOTH)

        # Create columns
        columns = [
            ("Property", str, 300),
            ("Value", str, 150),
            ("Units", str, 100)
        ]

        for i, (title, col_type, width) in enumerate(columns):
            renderer = Gtk.CellRendererText()
            if i == 0:  # Property name column
                renderer.set_property("weight", Pango.Weight.BOLD)
            column = Gtk.TreeViewColumn(title, renderer, text=i)
            column.set_min_width(width)
            column.set_resizable(True)
            column.set_sort_column_id(i)
            self.treeview.append_column(column)

        # Create list store
        self.liststore = Gtk.ListStore(str, str, str)
        self.treeview.set_model(self.liststore)

        scrolled.add(self.treeview)
        content_area.pack_start(scrolled, True, True, 0)

        # Notes section
        notes_frame = Gtk.Frame(label="Notes")
        notes_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        notes_box.set_margin_top(6)
        notes_box.set_margin_bottom(6)
        notes_box.set_margin_left(6)
        notes_box.set_margin_right(6)

        notes_text = [
            "• Paste properties are calculated from the cement matrix only",
            "• Concrete properties include aggregates and air voids",
            "• Values marked as 'nan' indicate insufficient data for calculation",
            "• All moduli are calculated using homogenization theory"
        ]

        for note in notes_text:
            note_label = Gtk.Label(note)
            note_label.set_halign(Gtk.Align.START)
            notes_box.pack_start(note_label, False, False, 0)

        notes_frame.add(notes_box)
        content_area.pack_start(notes_frame, False, False, 0)

        self.show_all()

    def _load_moduli_data(self):
        """Load effective moduli data from CSV file."""
        try:
            # Find the EffectiveModuli.csv file
            operation_dir = self._get_operation_directory()
            if not operation_dir:
                self._show_error("Could not find operation directory")
                return

            moduli_file = Path(operation_dir) / "EffectiveModuli.csv"
            if not moduli_file.exists():
                self._show_error("EffectiveModuli.csv file not found")
                return

            # Read and parse CSV data
            moduli_data = self._parse_moduli_csv(moduli_file)

            # Populate the tree view
            self._populate_treeview(moduli_data)

        except Exception as e:
            self.logger.error(f"Error loading moduli data: {e}")
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

    def _parse_moduli_csv(self, csv_file: Path) -> List[Tuple[str, str, str]]:
        """Parse the EffectiveModuli.csv file."""
        data = []

        with open(csv_file, 'r') as f:
            csv_reader = csv.reader(f)
            for row in csv_reader:
                if len(row) >= 3:
                    property_name = row[0].strip()
                    value = row[1].strip()
                    units = row[2].strip()

                    # Clean up property names for display
                    display_name = self._format_property_name(property_name)

                    # Format value for display
                    display_value = self._format_value(value)

                    data.append((display_name, display_value, units))

        return data

    def _format_property_name(self, name: str) -> str:
        """Format property name for display."""
        # Convert underscore-separated names to readable format
        name = name.replace('_', ' ').replace('frac', 'fraction')

        # Capitalize appropriately
        words = name.split()
        formatted_words = []

        for word in words:
            if word.lower() in ['youngs', 'poissons']:
                formatted_words.append(word.capitalize() + "'s")
            elif word.lower() == 'modulus':
                formatted_words.append('Modulus')
            elif word.lower() == 'vol':
                formatted_words.append('Volume')
            else:
                formatted_words.append(word.capitalize())

        return ' '.join(formatted_words)

    def _format_value(self, value: str) -> str:
        """Format value for display."""
        try:
            # Try to parse as float for better formatting
            float_val = float(value)
            if float_val != float_val:  # Check for NaN
                return "Not available"
            elif float_val == 0.0:
                return "0.000"
            else:
                return f"{float_val:.3f}"
        except ValueError:
            return value

    def _populate_treeview(self, data: List[Tuple[str, str, str]]):
        """Populate the tree view with moduli data."""
        self.liststore.clear()

        # Group data by material type
        paste_data = []
        concrete_data = []
        other_data = []

        for property_name, value, units in data:
            if 'paste' in property_name.lower():
                paste_data.append((property_name, value, units))
            elif 'concrete' in property_name.lower() or 'mortar' in property_name.lower():
                concrete_data.append((property_name, value, units))
            else:
                other_data.append((property_name, value, units))

        # Add paste section
        if paste_data:
            self.liststore.append(["PASTE PROPERTIES", "", ""])
            for item in paste_data:
                self.liststore.append(item)
            self.liststore.append(["", "", ""])  # Separator

        # Add concrete section
        if concrete_data:
            self.liststore.append(["CONCRETE PROPERTIES", "", ""])
            for item in concrete_data:
                self.liststore.append(item)
            self.liststore.append(["", "", ""])  # Separator

        # Add other properties
        if other_data:
            self.liststore.append(["OTHER PROPERTIES", "", ""])
            for item in other_data:
                self.liststore.append(item)

    def _show_error(self, message: str):
        """Show error message in the dialog."""
        error_label = Gtk.Label()
        error_label.set_markup(f"<b>Error:</b> {message}")
        error_label.set_halign(Gtk.Align.CENTER)
        error_label.set_margin_top(50)

        content_area = self.get_content_area()
        content_area.pack_start(error_label, True, True, 0)
        error_label.show()
#!/usr/bin/env python3
"""
Data Plotter Dialog

Interactive plotting dialog for visualizing CSV data from simulation results.
Allows users to select X and Y variables and create various types of plots.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg as FigureCanvas
from matplotlib.figure import Figure
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import logging


class DataPlotter(Gtk.Dialog):
    """Dialog for creating plots from CSV simulation data."""
    
    def __init__(self, parent=None, operation=None):
        super().__init__(
            title="Data Plotter - Simulation Results",
            transient_for=parent,
            flags=0
        )
        
        self.operation = operation
        self.logger = logging.getLogger(__name__)
        
        # Data storage
        self.csv_files: List[Tuple[str, str]] = []  # (filename, filepath)
        self.current_data: Optional[pd.DataFrame] = None
        self.current_columns: List[str] = []
        
        # UI components
        self.file_combo = None
        self.x_combo = None
        self.y_combo = None
        self.plot_type_combo = None
        self.figure = None
        self.canvas = None
        self.info_label = None
        
        # Dialog setup
        self.set_default_size(900, 600)
        self.set_modal(True)
        
        # Add standard dialog buttons
        self.add_button("Close", Gtk.ResponseType.CLOSE)
        
        # Initialize UI
        self._setup_ui()
        self._load_csv_files()
        
    def _setup_ui(self) -> None:
        """Set up the user interface."""
        content_area = self.get_content_area()
        content_area.set_spacing(10)
        content_area.set_margin_left(10)
        content_area.set_margin_right(10)
        content_area.set_margin_top(10)
        content_area.set_margin_bottom(10)
        
        # Create main layout - controls on left, plot on right
        main_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        content_area.pack_start(main_hbox, True, True, 0)
        
        # Create controls panel (left side)
        self._create_controls_panel(main_hbox)
        
        # Create plot area (right side)
        self._create_plot_area(main_hbox)
        
    def _create_controls_panel(self, parent: Gtk.Box) -> None:
        """Create the controls panel."""
        controls_frame = Gtk.Frame(label="Plot Controls")
        controls_frame.set_size_request(250, -1)
        parent.pack_start(controls_frame, False, False, 0)
        
        controls_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        controls_vbox.set_margin_left(10)
        controls_vbox.set_margin_right(10)
        controls_vbox.set_margin_top(10)
        controls_vbox.set_margin_bottom(10)
        controls_frame.add(controls_vbox)
        
        # Info label
        self.info_label = Gtk.Label()
        self.info_label.set_markup("<b>Select data to plot</b>")
        self.info_label.set_halign(Gtk.Align.START)
        controls_vbox.pack_start(self.info_label, False, False, 0)
        
        # File selection
        file_label = Gtk.Label("Data File:")
        file_label.set_halign(Gtk.Align.START)
        controls_vbox.pack_start(file_label, False, False, 0)
        
        self.file_combo = Gtk.ComboBoxText()
        self.file_combo.connect('changed', self._on_file_changed)
        controls_vbox.pack_start(self.file_combo, False, False, 0)
        
        # X-axis variable
        x_label = Gtk.Label("X-axis Variable:")
        x_label.set_halign(Gtk.Align.START)
        controls_vbox.pack_start(x_label, False, False, 0)
        
        self.x_combo = Gtk.ComboBoxText()
        self.x_combo.connect('changed', self._on_variable_changed)
        controls_vbox.pack_start(self.x_combo, False, False, 0)
        
        # Y-axis variable
        y_label = Gtk.Label("Y-axis Variable:")
        y_label.set_halign(Gtk.Align.START)
        controls_vbox.pack_start(y_label, False, False, 0)
        
        self.y_combo = Gtk.ComboBoxText()
        self.y_combo.connect('changed', self._on_variable_changed)
        controls_vbox.pack_start(self.y_combo, False, False, 0)
        
        # Plot type
        type_label = Gtk.Label("Plot Type:")
        type_label.set_halign(Gtk.Align.START)
        controls_vbox.pack_start(type_label, False, False, 0)
        
        self.plot_type_combo = Gtk.ComboBoxText()
        plot_types = ["Line Plot", "Scatter Plot", "Bar Plot", "Histogram (Y only)"]
        for plot_type in plot_types:
            self.plot_type_combo.append_text(plot_type)
        self.plot_type_combo.set_active(0)  # Default to line plot
        self.plot_type_combo.connect('changed', self._on_variable_changed)
        controls_vbox.pack_start(self.plot_type_combo, False, False, 0)
        
        # Action buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        controls_vbox.pack_start(button_box, False, False, 10)
        
        # Create plot button
        plot_button = Gtk.Button(label="Create Plot")
        plot_button.connect('clicked', self._on_create_plot_clicked)
        button_box.pack_start(plot_button, False, False, 0)
        
        # Clear plot button
        clear_button = Gtk.Button(label="Clear Plot")
        clear_button.connect('clicked', self._on_clear_plot_clicked)
        button_box.pack_start(clear_button, False, False, 0)
        
        # Export plot button
        export_button = Gtk.Button(label="Export Plot")
        export_button.connect('clicked', self._on_export_plot_clicked)
        button_box.pack_start(export_button, False, False, 0)
        
        # Data info section
        info_frame = Gtk.Frame(label="Data Info")
        controls_vbox.pack_start(info_frame, True, True, 0)
        
        self.data_info_label = Gtk.Label()
        self.data_info_label.set_halign(Gtk.Align.START)
        self.data_info_label.set_valign(Gtk.Align.START)
        self.data_info_label.set_line_wrap(True)
        info_frame.add(self.data_info_label)
        
    def _create_plot_area(self, parent: Gtk.Box) -> None:
        """Create the matplotlib plot area."""
        plot_frame = Gtk.Frame(label="Plot")
        parent.pack_start(plot_frame, True, True, 0)
        
        # Create matplotlib figure
        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.set_size_request(400, 300)
        
        plot_frame.add(self.canvas)
        
        # Initial empty plot
        ax = self.figure.add_subplot(111)
        ax.text(0.5, 0.5, 'Select data and click "Create Plot"', 
                horizontalalignment='center', verticalalignment='center',
                transform=ax.transAxes, fontsize=12)
        ax.set_xticks([])
        ax.set_yticks([])
        
    def _load_csv_files(self) -> None:
        """Load all CSV files from the operation directory."""
        try:
            if not self.operation or not self.operation.output_dir:
                self.logger.error("No operation or output directory specified")
                return
            
            output_path = Path(self.operation.output_dir)
            if not output_path.exists():
                self.logger.error(f"Output directory does not exist: {output_path}")
                return
            
            # Find all CSV files
            csv_files = list(output_path.glob("*.csv"))
            
            for csv_file in csv_files:
                self.csv_files.append((csv_file.name, str(csv_file)))
                self.file_combo.append_text(csv_file.name)
                self.logger.info(f"Found CSV file: {csv_file.name}")
            
            if self.csv_files:
                self.file_combo.set_active(0)  # Select first file
                self.info_label.set_markup(f"<b>Found {len(self.csv_files)} CSV files</b>")
            else:
                self.info_label.set_markup("<b>No CSV files found</b>")
                
        except Exception as e:
            self.logger.error(f"Error loading CSV files: {e}")
            
    def _on_file_changed(self, combo) -> None:
        """Handle file selection change."""
        try:
            selected_index = combo.get_active()
            if selected_index >= 0 and selected_index < len(self.csv_files):
                filename, filepath = self.csv_files[selected_index]
                self._load_csv_data(filepath)
                
        except Exception as e:
            self.logger.error(f"Error handling file change: {e}")
    
    def _load_csv_data(self, filepath: str) -> None:
        """Load CSV data and populate variable dropdowns."""
        try:
            # Load CSV data
            self.current_data = pd.read_csv(filepath)
            self.current_columns = list(self.current_data.columns)
            
            # Clear and populate variable dropdowns
            self.x_combo.remove_all()
            self.y_combo.remove_all()
            
            for column in self.current_columns:
                self.x_combo.append_text(column)
                self.y_combo.append_text(column)
            
            # Set reasonable defaults
            if len(self.current_columns) >= 2:
                self.x_combo.set_active(0)  # First column (often time)
                self.y_combo.set_active(1)  # Second column
            elif len(self.current_columns) == 1:
                self.x_combo.set_active(0)
                
            # Update data info
            rows, cols = self.current_data.shape
            self.data_info_label.set_text(
                f"Loaded {filepath.split('/')[-1]}\\n\\n"
                f"Rows: {rows:,}\\n"
                f"Columns: {cols}\\n\\n"
                f"Columns:\\n" + "\\n".join(f"• {col}" for col in self.current_columns[:10]) +
                (f"\\n... and {cols-10} more" if cols > 10 else "")
            )
            
            self.logger.info(f"Loaded CSV data: {rows} rows, {cols} columns")
            
        except Exception as e:
            self.logger.error(f"Error loading CSV data from {filepath}: {e}")
            # Show error dialog
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Data Loading Error"
            )
            dialog.format_secondary_text(f"Failed to load CSV data: {e}")
            dialog.run()
            dialog.destroy()
    
    def _on_variable_changed(self, combo) -> None:
        """Handle variable selection change."""
        # Could add preview or validation here if needed
        pass
    
    def _on_create_plot_clicked(self, button) -> None:
        """Handle create plot button click."""
        try:
            if self.current_data is None:
                self._show_error("No data loaded. Please select a CSV file first.")
                return
            
            x_index = self.x_combo.get_active()
            y_index = self.y_combo.get_active()
            plot_type_index = self.plot_type_combo.get_active()
            
            if x_index < 0:
                self._show_error("Please select an X-axis variable.")
                return
                
            if y_index < 0 and plot_type_index != 3:  # Histogram doesn't need Y
                self._show_error("Please select a Y-axis variable.")
                return
            
            # Get selected variables
            x_var = self.current_columns[x_index]
            y_var = self.current_columns[y_index] if y_index >= 0 else None
            
            # Clear previous plot
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            
            # Create plot based on type
            plot_types = ["Line Plot", "Scatter Plot", "Bar Plot", "Histogram (Y only)"]
            plot_type = plot_types[plot_type_index]
            
            x_data = self.current_data[x_var]
            
            if plot_type == "Line Plot" and y_var:
                y_data = self.current_data[y_var]
                ax.plot(x_data, y_data, linewidth=2)
                ax.set_ylabel(y_var)
                
            elif plot_type == "Scatter Plot" and y_var:
                y_data = self.current_data[y_var]
                ax.scatter(x_data, y_data, alpha=0.6)
                ax.set_ylabel(y_var)
                
            elif plot_type == "Bar Plot" and y_var:
                y_data = self.current_data[y_var]
                # For bar plots, limit data points to avoid overcrowding
                if len(x_data) > 50:
                    # Sample data
                    indices = np.linspace(0, len(x_data)-1, 50, dtype=int)
                    x_data = x_data.iloc[indices]
                    y_data = y_data.iloc[indices]
                ax.bar(range(len(x_data)), y_data)
                ax.set_xticks(range(0, len(x_data), max(1, len(x_data)//10)))
                ax.set_xticklabels([f"{x:.2f}" for i, x in enumerate(x_data) if i % max(1, len(x_data)//10) == 0], rotation=45)
                ax.set_ylabel(y_var)
                
            elif plot_type == "Histogram (Y only)":
                if y_var:
                    y_data = self.current_data[y_var]
                    ax.hist(y_data, bins=30, alpha=0.7, edgecolor='black')
                    ax.set_xlabel(y_var)
                    ax.set_ylabel("Frequency")
                else:
                    ax.hist(x_data, bins=30, alpha=0.7, edgecolor='black')
                    ax.set_xlabel(x_var)
                    ax.set_ylabel("Frequency")
            
            # Set labels and title
            if plot_type != "Histogram (Y only)":
                ax.set_xlabel(x_var)
            
            ax.set_title(f"{plot_type}: {y_var or x_var} vs {x_var}" if plot_type != "Histogram (Y only)" else f"Histogram: {y_var or x_var}")
            ax.grid(True, alpha=0.3)
            
            # Adjust layout and refresh
            self.figure.tight_layout()
            self.canvas.draw()
            
            self.logger.info(f"Created {plot_type}: {x_var} vs {y_var}")
            
        except Exception as e:
            self.logger.error(f"Error creating plot: {e}")
            self._show_error(f"Failed to create plot: {e}")
    
    def _on_clear_plot_clicked(self, button) -> None:
        """Handle clear plot button click."""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.text(0.5, 0.5, 'Select data and click "Create Plot"', 
                horizontalalignment='center', verticalalignment='center',
                transform=ax.transAxes, fontsize=12)
        ax.set_xticks([])
        ax.set_yticks([])
        self.canvas.draw()
    
    def _on_export_plot_clicked(self, button) -> None:
        """Handle export plot button click."""
        try:
            # Create file chooser dialog
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
            
            # Set default filename
            if self.operation:
                dialog.set_current_name(f"{self.operation.name}_plot.png")
            
            response = dialog.run()
            if response == Gtk.ResponseType.OK:
                filename = dialog.get_filename()
                self.figure.savefig(filename, dpi=300, bbox_inches='tight')
                self.logger.info(f"Plot exported to: {filename}")
                
                # Show success message
                success_dialog = Gtk.MessageDialog(
                    transient_for=self,
                    flags=0,
                    message_type=Gtk.MessageType.INFO,
                    buttons=Gtk.ButtonsType.OK,
                    text="Export Successful"
                )
                success_dialog.format_secondary_text(f"Plot saved to: {filename}")
                success_dialog.run()
                success_dialog.destroy()
            
            dialog.destroy()
            
        except Exception as e:
            self.logger.error(f"Error exporting plot: {e}")
            self._show_error(f"Failed to export plot: {e}")
    
    def _show_error(self, message: str) -> None:
        """Show error dialog."""
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text="Error"
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()


# Register the widget
GObject.type_register(DataPlotter)
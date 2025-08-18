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
        self.y_liststore = None
        self.y_treeview = None
        self.plot_type_combo = None
        self.figure = None
        self.canvas = None
        self.info_label = None
        
        # Dialog setup - larger default size to accommodate wider plots
        self.set_default_size(1200, 700)
        self.set_modal(True)
        
        # Add standard dialog buttons
        self.add_button("Close", Gtk.ResponseType.CLOSE)
        
        # Initialize UI
        self._setup_ui()
        self._load_csv_files()
        
        # Show all widgets
        self.show_all()
        
    def _setup_ui(self) -> None:
        """Set up the user interface."""
        content_area = self.get_content_area()
        content_area.set_spacing(10)
        content_area.set_margin_left(10)
        content_area.set_margin_right(10)
        content_area.set_margin_top(10)
        content_area.set_margin_bottom(10)
        
        # Create main layout using Paned widget for better control
        main_paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        main_paned.set_wide_handle(True)
        main_paned.set_position(280)  # Set initial position of divider
        content_area.pack_start(main_paned, True, True, 0)
        
        # Create controls panel (left side)
        self._create_controls_panel(main_paned)
        
        # Create plot area (right side)
        self._create_plot_area(main_paned)
        
    def _create_controls_panel(self, parent: Gtk.Paned) -> None:
        """Create the controls panel."""
        controls_frame = Gtk.Frame(label="Plot Controls")
        controls_frame.set_size_request(280, -1)  # Fixed width
        parent.pack1(controls_frame, False, False)  # pack1 = left side, no resize, no shrink
        
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
        
        # Y-axis variables (multi-select)
        y_label = Gtk.Label("Y-axis Variables:")
        y_label.set_halign(Gtk.Align.START)
        controls_vbox.pack_start(y_label, False, False, 0)
        
        # Create scrolled window for Y variables list
        y_scrolled = Gtk.ScrolledWindow()
        y_scrolled.set_size_request(-1, 120)
        y_scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        controls_vbox.pack_start(y_scrolled, False, False, 0)
        
        # Create list store and tree view for Y variables
        self.y_liststore = Gtk.ListStore(bool, str, str)  # selected, display_name, column_name
        self.y_treeview = Gtk.TreeView(model=self.y_liststore)
        
        # Add checkbox column
        checkbox_renderer = Gtk.CellRendererToggle()
        checkbox_renderer.connect("toggled", self._on_y_variable_toggled)
        checkbox_column = Gtk.TreeViewColumn("", checkbox_renderer, active=0)
        self.y_treeview.append_column(checkbox_column)
        
        # Add variable name column
        text_renderer = Gtk.CellRendererText()
        name_column = Gtk.TreeViewColumn("Variable", text_renderer, text=1)
        self.y_treeview.append_column(name_column)
        
        y_scrolled.add(self.y_treeview)
        
        # Add select/deselect all buttons
        y_button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        controls_vbox.pack_start(y_button_box, False, False, 0)
        
        select_all_button = Gtk.Button(label="Select All")
        select_all_button.connect('clicked', self._on_select_all_y_clicked)
        y_button_box.pack_start(select_all_button, True, True, 0)
        
        deselect_all_button = Gtk.Button(label="Deselect All")
        deselect_all_button.connect('clicked', self._on_deselect_all_y_clicked)
        y_button_box.pack_start(deselect_all_button, True, True, 0)
        
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
        
    def _create_plot_area(self, parent: Gtk.Paned) -> None:
        """Create the matplotlib plot area."""
        plot_frame = Gtk.Frame(label="Plot")
        parent.pack2(plot_frame, True, True)  # pack2 = right side, resize, shrink
        
        # Create matplotlib figure with larger initial size
        self.figure = Figure(figsize=(10, 7), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        # Set minimum size - Paned widget will handle expansion
        self.canvas.set_size_request(500, 400)
        
        plot_frame.add(self.canvas)
        
        # Initial empty plot
        ax = self.figure.add_subplot(111)
        ax.text(0.5, 0.5, 'Select data and click "Create Plot"', 
                horizontalalignment='center', verticalalignment='center',
                transform=ax.transAxes, fontsize=12)
        ax.set_xticks([])
        ax.set_yticks([])
        
        # Make sure canvas is visible
        self.canvas.show()
        
    def _load_csv_files(self) -> None:
        """Load all CSV files from the operation directory."""
        try:
            if not self.operation:
                self.logger.error("No operation specified")
                return
            
            # Get output directory from operation metadata
            output_dir = None
            if hasattr(self.operation, 'output_dir') and self.operation.output_dir:
                output_dir = self.operation.output_dir
            elif hasattr(self.operation, 'metadata') and self.operation.metadata:
                output_dir = self.operation.metadata.get('output_directory')
                if not output_dir:
                    output_dir = self.operation.metadata.get('output_dir')
            
            if not output_dir:
                # Try to construct from operation name
                project_root = Path(__file__).parent.parent.parent.parent
                operations_dir = project_root / "Operations"
                potential_folder = operations_dir / self.operation.name
                if potential_folder.exists():
                    output_dir = str(potential_folder)
            
            if not output_dir:
                self.logger.error("No output directory found for operation")
                return
            
            output_path = Path(output_dir)
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
            self.y_liststore.clear()
            
            for column in self.current_columns:
                self.x_combo.append_text(column)
                # Add to Y variables list (unselected by default)
                self.y_liststore.append([False, column, column])
            
            # Set reasonable defaults - prefer "time(h)" for X-axis
            time_column_index = -1
            for i, column in enumerate(self.current_columns):
                if column.lower() in ['time(h)', 'time', 'time_h', 'time_hours']:
                    time_column_index = i
                    break
            
            if time_column_index >= 0:
                # Found time column, use it as X-axis
                self.x_combo.set_active(time_column_index)
                # Select preferred Y variable (Alpha_mass first, then first non-time column)
                alpha_mass_selected = False
                for i, column in enumerate(self.current_columns):
                    if column == 'Alpha_mass':
                        iter_var = self.y_liststore.iter_nth_child(None, i)
                        if iter_var:
                            self.y_liststore.set_value(iter_var, 0, True)
                            alpha_mass_selected = True
                            break
                
                # If Alpha_mass not found, select first non-time column
                if not alpha_mass_selected:
                    for i, column in enumerate(self.current_columns):
                        if i != time_column_index:
                            iter_var = self.y_liststore.iter_nth_child(None, i)
                            if iter_var:
                                self.y_liststore.set_value(iter_var, 0, True)
                                break
            elif len(self.current_columns) >= 2:
                # Fall back to first column as X-axis
                self.x_combo.set_active(0)
                # Select Alpha_mass if available, otherwise second column
                alpha_mass_selected = False
                for i, column in enumerate(self.current_columns):
                    if column == 'Alpha_mass':
                        iter_var = self.y_liststore.iter_nth_child(None, i)
                        if iter_var:
                            self.y_liststore.set_value(iter_var, 0, True)
                            alpha_mass_selected = True
                            break
                
                if not alpha_mass_selected:
                    # Select second column as default Y variable
                    iter_second = self.y_liststore.iter_nth_child(None, 1)
                    if iter_second:
                        self.y_liststore.set_value(iter_second, 0, True)
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
    
    def _on_y_variable_toggled(self, renderer, path) -> None:
        """Handle Y variable checkbox toggle."""
        try:
            iter = self.y_liststore.get_iter(path)
            current_value = self.y_liststore.get_value(iter, 0)
            self.y_liststore.set_value(iter, 0, not current_value)
        except Exception as e:
            self.logger.error(f"Error toggling Y variable: {e}")
    
    def _on_select_all_y_clicked(self, button) -> None:
        """Select all Y variables."""
        try:
            iter = self.y_liststore.get_iter_first()
            while iter:
                self.y_liststore.set_value(iter, 0, True)
                iter = self.y_liststore.iter_next(iter)
        except Exception as e:
            self.logger.error(f"Error selecting all Y variables: {e}")
    
    def _on_deselect_all_y_clicked(self, button) -> None:
        """Deselect all Y variables."""
        try:
            iter = self.y_liststore.get_iter_first()
            while iter:
                self.y_liststore.set_value(iter, 0, False)
                iter = self.y_liststore.iter_next(iter)
        except Exception as e:
            self.logger.error(f"Error deselecting all Y variables: {e}")
    
    def _on_create_plot_clicked(self, button) -> None:
        """Handle create plot button click."""
        try:
            if self.current_data is None:
                self._show_error("No data loaded. Please select a CSV file first.")
                return
            
            x_index = self.x_combo.get_active()
            plot_type_index = self.plot_type_combo.get_active()
            
            if x_index < 0:
                self._show_error("Please select an X-axis variable.")
                return
            
            # Get selected Y variables
            selected_y_vars = self._get_selected_y_variables()
            
            if len(selected_y_vars) == 0 and plot_type_index != 3:  # Histogram doesn't need Y
                self._show_error("Please select at least one Y-axis variable.")
                return
            
            # Get selected variables
            x_var = self.current_columns[x_index]
            
            # Clear previous plot
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            
            # Create plot based on type
            plot_types = ["Line Plot", "Scatter Plot", "Bar Plot", "Histogram (Y only)"]
            plot_type = plot_types[plot_type_index]
            
            x_data = self.current_data[x_var]
            
            if plot_type == "Line Plot" and selected_y_vars:
                # Plot multiple lines with different colors
                colors = plt.cm.tab10(np.linspace(0, 1, len(selected_y_vars)))
                for i, y_var in enumerate(selected_y_vars):
                    y_data = self.current_data[y_var]
                    ax.plot(x_data, y_data, linewidth=2, color=colors[i], label=y_var)
                ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
                ax.set_ylabel("Value")
                
            elif plot_type == "Scatter Plot" and selected_y_vars:
                # Plot multiple scatter series with different colors
                colors = plt.cm.tab10(np.linspace(0, 1, len(selected_y_vars)))
                for i, y_var in enumerate(selected_y_vars):
                    y_data = self.current_data[y_var]
                    ax.scatter(x_data, y_data, alpha=0.6, color=colors[i], label=y_var)
                ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
                ax.set_ylabel("Value")
                
            elif plot_type == "Bar Plot" and selected_y_vars:
                # For multiple Y variables, create grouped bar plot
                if len(selected_y_vars) == 1:
                    y_var = selected_y_vars[0]
                    y_data = self.current_data[y_var]
                    # For bar plots, limit data points to avoid overcrowding
                    if len(x_data) > 50:
                        indices = np.linspace(0, len(x_data)-1, 50, dtype=int)
                        x_data = x_data.iloc[indices]
                        y_data = y_data.iloc[indices]
                    ax.bar(range(len(x_data)), y_data)
                    ax.set_xticks(range(0, len(x_data), max(1, len(x_data)//10)))
                    ax.set_xticklabels([f"{x:.2f}" for i, x in enumerate(x_data) if i % max(1, len(x_data)//10) == 0], rotation=45)
                    ax.set_ylabel(y_var)
                else:
                    # Multiple Y variables - grouped bars
                    n_vars = len(selected_y_vars)
                    bar_width = 0.8 / n_vars
                    x_positions = np.arange(min(len(x_data), 20))  # Limit to 20 data points for readability
                    
                    colors = plt.cm.tab10(np.linspace(0, 1, n_vars))
                    for i, y_var in enumerate(selected_y_vars):
                        y_data = self.current_data[y_var].iloc[:len(x_positions)]
                        ax.bar(x_positions + i * bar_width, y_data, bar_width, 
                              color=colors[i], label=y_var, alpha=0.8)
                    
                    ax.set_xticks(x_positions + bar_width * (n_vars - 1) / 2)
                    ax.set_xticklabels([f"{x:.2f}" for x in x_data.iloc[:len(x_positions)]], rotation=45)
                    ax.legend()
                    ax.set_ylabel("Value")
                
            elif plot_type == "Histogram (Y only)":
                if selected_y_vars:
                    # Plot multiple histograms with transparency
                    colors = plt.cm.tab10(np.linspace(0, 1, len(selected_y_vars)))
                    for i, y_var in enumerate(selected_y_vars):
                        y_data = self.current_data[y_var]
                        ax.hist(y_data, bins=30, alpha=0.5, edgecolor='black', 
                               color=colors[i], label=y_var)
                    ax.legend()
                    ax.set_xlabel("Value")
                    ax.set_ylabel("Frequency")
                else:
                    # Fall back to X variable histogram
                    ax.hist(x_data, bins=30, alpha=0.7, edgecolor='black')
                    ax.set_xlabel(x_var)
                    ax.set_ylabel("Frequency")
            
            # Set labels and title
            if plot_type != "Histogram (Y only)":
                ax.set_xlabel(x_var)
            
            # Create title based on number of Y variables
            if len(selected_y_vars) > 1:
                y_names = ", ".join(selected_y_vars[:3])
                if len(selected_y_vars) > 3:
                    y_names += f" (and {len(selected_y_vars) - 3} more)"
                title = f"{plot_type}: {y_names} vs {x_var}" if plot_type != "Histogram (Y only)" else f"Histogram: {y_names}"
            elif len(selected_y_vars) == 1:
                title = f"{plot_type}: {selected_y_vars[0]} vs {x_var}" if plot_type != "Histogram (Y only)" else f"Histogram: {selected_y_vars[0]}"
            else:
                title = f"Histogram: {x_var}"
            
            ax.set_title(title)
            ax.grid(True, alpha=0.3)
            
            # Adjust layout and refresh
            self.figure.tight_layout()
            self.canvas.draw()
            
            self.logger.info(f"Created {plot_type} with {len(selected_y_vars)} Y variables: {selected_y_vars}")
            
        except Exception as e:
            self.logger.error(f"Error creating plot: {e}")
            self._show_error(f"Failed to create plot: {e}")
    
    def _get_selected_y_variables(self) -> List[str]:
        """Get list of selected Y variables."""
        selected_vars = []
        try:
            iter = self.y_liststore.get_iter_first()
            while iter:
                if self.y_liststore.get_value(iter, 0):  # If selected
                    var_name = self.y_liststore.get_value(iter, 2)  # Column name
                    selected_vars.append(var_name)
                iter = self.y_liststore.iter_next(iter)
        except Exception as e:
            self.logger.error(f"Error getting selected Y variables: {e}")
        
        return selected_vars
    
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
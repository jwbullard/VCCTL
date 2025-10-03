#!/usr/bin/env python3
"""
Results Panel for VCCTL

Provides analysis and visualization of completed simulation results,
including 3D visualization, data plotting, and statistical analysis.
"""

import gi
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Optional, List, Dict, Any

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, Pango

if TYPE_CHECKING:
    from app.windows.main_window import VCCTLMainWindow

from app.services.service_container import get_service_container
from app.help.panel_help_button import create_panel_help_button


class ResultsPanel(Gtk.Box):
    """Results analysis and visualization panel."""
    
    def __init__(self, parent: 'VCCTLMainWindow'):
        """Initialize the results panel."""
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        
        self.parent = parent
        self.logger = logging.getLogger('VCCTL.ResultsPanel')
        self.service_container = get_service_container()
        
        # Currently selected operation for analysis
        self.selected_operation = None
        
        # Create the UI
        self._setup_ui()
        
        self.logger.info("Results panel initialized")
        
        # Load operations immediately on initialization
        GObject.timeout_add(100, self._initial_load)
    
    def _initial_load(self) -> bool:
        """Initial load of operations - called after UI setup is complete."""
        self.logger.info("Results panel: Performing initial load of operations")
        self._load_completed_operations()
        return False  # Don't repeat the timeout
    
    def _setup_ui(self) -> None:
        """Setup the results panel UI."""
        # Create header
        self._create_header()
        
        # Create operation selection area
        self._create_operation_selection()
        
        # Create separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.pack_start(separator, False, False, 10)
        
        # Create results analysis area
        self._create_results_area()
    
    def _create_header(self) -> None:
        """Create the panel header."""
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        header_box.set_margin_left(10)
        header_box.set_margin_right(10)
        header_box.set_margin_top(10)

        # Title
        title_label = Gtk.Label()
        title_label.set_markup('<span size="large"><b>Results Analysis</b></span>')
        title_label.set_halign(Gtk.Align.START)
        header_box.pack_start(title_label, False, False, 0)

        # Add context-specific help button
        help_button = create_panel_help_button('ResultsPanel', self.parent)
        header_box.pack_start(help_button, False, False, 5)

        # Spacer
        header_box.pack_start(Gtk.Box(), True, True, 0)
        
        # Refresh button
        self.refresh_button = Gtk.Button.new_with_label("Refresh")
        self.refresh_button.set_tooltip_text("Refresh the list of available results")
        self.refresh_button.connect('clicked', self._on_refresh_clicked)
        header_box.pack_start(self.refresh_button, False, False, 0)
        
        self.pack_start(header_box, False, False, 0)
    
    def _create_operation_selection(self) -> None:
        """Create the operation selection area."""
        selection_frame = Gtk.Frame(label="Select Operation for Analysis")
        selection_frame.set_margin_left(10)
        selection_frame.set_margin_right(10)
        
        selection_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        selection_box.set_margin_top(10)
        selection_box.set_margin_bottom(10)
        selection_box.set_margin_left(10)
        selection_box.set_margin_right(10)
        
        # Description
        desc_label = Gtk.Label()
        desc_label.set_markup('<i>Select a result folder from the list below to analyze its contents.</i>')
        desc_label.set_halign(Gtk.Align.START)
        selection_box.pack_start(desc_label, False, False, 0)
        
        # Operation list
        self._create_operation_list()
        selection_box.pack_start(self.operation_scrolled, True, True, 0)
        
        selection_frame.add(selection_box)
        self.pack_start(selection_frame, False, True, 0)
    
    def _create_operation_list(self) -> None:
        """Create the scrollable list of completed operations."""
        # Create list store: name, type, completion_date, operation_object
        self.operation_liststore = Gtk.ListStore(str, str, str, object)

        # Setup sorting for the list store
        self._setup_column_sorting()

        # Create tree view
        self.operation_treeview = Gtk.TreeView(model=self.operation_liststore)
        self.operation_treeview.set_headers_visible(True)
        self.operation_treeview.get_selection().set_mode(Gtk.SelectionMode.SINGLE)
        self.operation_treeview.get_selection().connect('changed', self._on_operation_selection_changed)
        
        # Name column
        name_renderer = Gtk.CellRendererText()
        name_column = Gtk.TreeViewColumn("Result Name", name_renderer, text=0)
        name_column.set_resizable(True)
        name_column.set_min_width(200)
        name_column.set_sort_column_id(0)  # Enable sorting by column 0
        name_column.set_clickable(True)
        self.operation_treeview.append_column(name_column)

        # Type column
        type_renderer = Gtk.CellRendererText()
        type_column = Gtk.TreeViewColumn("Type", type_renderer, text=1)
        type_column.set_resizable(True)
        type_column.set_min_width(120)
        type_column.set_sort_column_id(1)  # Enable sorting by column 1
        type_column.set_clickable(True)
        self.operation_treeview.append_column(type_column)

        # Completion date column
        date_renderer = Gtk.CellRendererText()
        date_column = Gtk.TreeViewColumn("Last Modified", date_renderer, text=2)
        date_column.set_resizable(True)
        date_column.set_min_width(120)
        date_column.set_sort_column_id(2)  # Enable sorting by column 2
        date_column.set_clickable(True)
        self.operation_treeview.append_column(date_column)
        
        # Scrolled window
        self.operation_scrolled = Gtk.ScrolledWindow()
        self.operation_scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.operation_scrolled.set_size_request(-1, 150)
        self.operation_scrolled.add(self.operation_treeview)

    def _setup_column_sorting(self) -> None:
        """Setup sorting functions for the operation list columns."""
        # Enable default sorting for name and type columns (string comparison)
        self.operation_liststore.set_sort_column_id(0, Gtk.SortType.ASCENDING)
        self.operation_liststore.set_sort_func(0, self._sort_by_name, None)
        self.operation_liststore.set_sort_func(1, self._sort_by_type, None)
        self.operation_liststore.set_sort_func(2, self._sort_by_date, None)

    def _sort_by_name(self, model, iter1, iter2, user_data):
        """Sort function for the name column."""
        name1 = model.get_value(iter1, 0).lower()
        name2 = model.get_value(iter2, 0).lower()
        if name1 < name2:
            return -1
        elif name1 > name2:
            return 1
        else:
            return 0

    def _sort_by_type(self, model, iter1, iter2, user_data):
        """Sort function for the type column."""
        type1 = model.get_value(iter1, 1).lower()
        type2 = model.get_value(iter2, 1).lower()
        if type1 < type2:
            return -1
        elif type1 > type2:
            return 1
        else:
            return 0

    def _sort_by_date(self, model, iter1, iter2, user_data):
        """Sort function for the date column."""
        import datetime

        date1_str = model.get_value(iter1, 2)
        date2_str = model.get_value(iter2, 2)

        # Parse date strings - handle different formats gracefully
        try:
            # Try to parse as ISO format first (YYYY-MM-DD HH:MM:SS)
            if ' ' in date1_str:
                date1 = datetime.datetime.strptime(date1_str, '%Y-%m-%d %H:%M:%S')
            else:
                date1 = datetime.datetime.strptime(date1_str, '%Y-%m-%d')
        except (ValueError, TypeError):
            try:
                # Try alternative formats
                date1 = datetime.datetime.strptime(date1_str, '%m/%d/%Y')
            except (ValueError, TypeError):
                # If parsing fails, use string comparison as fallback
                date1_str = str(date1_str)
                date2_str = str(date2_str)
                if date1_str < date2_str:
                    return -1
                elif date1_str > date2_str:
                    return 1
                else:
                    return 0

        try:
            if ' ' in date2_str:
                date2 = datetime.datetime.strptime(date2_str, '%Y-%m-%d %H:%M:%S')
            else:
                date2 = datetime.datetime.strptime(date2_str, '%Y-%m-%d')
        except (ValueError, TypeError):
            try:
                date2 = datetime.datetime.strptime(date2_str, '%m/%d/%Y')
            except (ValueError, TypeError):
                # Fallback to string comparison
                date1_str = str(date1_str)
                date2_str = str(date2_str)
                if date1_str < date2_str:
                    return -1
                elif date1_str > date2_str:
                    return 1
                else:
                    return 0

        # Compare parsed dates
        if date1 < date2:
            return -1
        elif date1 > date2:
            return 1
        else:
            return 0

    def _create_results_area(self) -> None:
        """Create the results analysis area."""
        self.results_frame = Gtk.Frame(label="Analysis Tools")
        self.results_frame.set_margin_left(10)
        self.results_frame.set_margin_right(10)
        self.results_frame.set_margin_bottom(10)
        
        self.results_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.results_box.set_margin_top(10)
        self.results_box.set_margin_bottom(10)
        self.results_box.set_margin_left(10)
        self.results_box.set_margin_right(10)
        
        # Initially show placeholder message
        self._show_no_selection_message()
        
        self.results_frame.add(self.results_box)
        self.pack_start(self.results_frame, True, True, 0)
    
    def _show_no_selection_message(self) -> None:
        """Show message when no operation is selected."""
        # Clear existing content
        for child in self.results_box.get_children():
            self.results_box.remove(child)
        
        # Add placeholder message
        placeholder_label = Gtk.Label()
        placeholder_label.set_markup(
            '<span size="large" style="italic">Select a result folder above to access analysis tools</span>'
        )
        placeholder_label.set_halign(Gtk.Align.CENTER)
        placeholder_label.set_valign(Gtk.Align.CENTER)
        self.results_box.pack_start(placeholder_label, True, True, 0)
        
        self.results_box.show_all()
    
    def _show_analysis_tools(self, operation) -> None:
        """Show analysis tools for the selected operation."""
        # Clear existing content
        for child in self.results_box.get_children():
            self.results_box.remove(child)
        
        # Operation info header
        info_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        info_label = Gtk.Label()
        info_label.set_markup(f'<b>Analyzing:</b> {operation.name}')
        info_label.set_halign(Gtk.Align.START)
        info_box.pack_start(info_label, False, False, 0)
        
        self.results_box.pack_start(info_box, False, False, 0)
        
        # Create buttons grid
        buttons_grid = Gtk.Grid()
        buttons_grid.set_row_spacing(10)
        buttons_grid.set_column_spacing(15)
        buttons_grid.set_halign(Gtk.Align.CENTER)
        
        button_col = 0  # Track column position for buttons

        # Check if this is an elastic operation to exclude certain buttons
        is_elastic = self._is_elastic_operation(operation)
        self.logger.info(f"Results panel: Operation '{operation.name}' is elastic operation: {is_elastic}")

        # 3D Visualization button (NOT for elastic operations)
        has_3d = self._has_3d_results(operation)
        self.logger.info(f"Results panel: Operation '{operation.name}' has 3D results: {has_3d}")
        if has_3d and not is_elastic:
            self.view_3d_button = Gtk.Button()
            self.view_3d_button.set_size_request(200, 60)

            button_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)

            icon_label = Gtk.Label()
            icon_label.set_markup('<span size="x-large">🎮</span>')
            button_box.pack_start(icon_label, False, False, 0)

            text_label = Gtk.Label()
            text_label.set_markup('<b>View 3D Results</b>')
            button_box.pack_start(text_label, False, False, 0)

            desc_label = Gtk.Label()
            desc_label.set_markup('<small>Interactive 3D microstructure\nevolution visualization</small>')
            desc_label.set_justify(Gtk.Justification.CENTER)
            button_box.pack_start(desc_label, False, False, 0)

            self.view_3d_button.add(button_box)
            self.view_3d_button.connect('clicked', self._on_view_3d_results_clicked)
            self.view_3d_button.set_tooltip_text("View 3D microstructure evolution from hydration simulation results")

            buttons_grid.attach(self.view_3d_button, button_col, 0, 1, 1)
            button_col += 1
        
        # Elastic Moduli Results buttons (for elastic operations)
        if is_elastic:
            # Effective Moduli Summary button
            has_effective_moduli = self._has_effective_moduli(operation)
            if has_effective_moduli:
                self.effective_moduli_button = Gtk.Button()
                self.effective_moduli_button.set_size_request(200, 60)

                button_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)

                icon_label = Gtk.Label()
                icon_label.set_markup('<span size="x-large">🔧</span>')
                button_box.pack_start(icon_label, False, False, 0)

                text_label = Gtk.Label()
                text_label.set_markup('<b>Effective Moduli</b>')
                button_box.pack_start(text_label, False, False, 0)

                desc_label = Gtk.Label()
                desc_label.set_markup('<small>View composite elastic\nmoduli summary</small>')
                desc_label.set_justify(Gtk.Justification.CENTER)
                button_box.pack_start(desc_label, False, False, 0)

                self.effective_moduli_button.add(button_box)
                self.effective_moduli_button.connect('clicked', self._on_effective_moduli_clicked)
                self.effective_moduli_button.set_tooltip_text("View effective elastic moduli for paste and concrete")

                buttons_grid.attach(self.effective_moduli_button, button_col, 0, 1, 1)
                button_col += 1

            # ITZ Analysis button
            has_itz_moduli = self._has_itz_moduli(operation)
            if has_itz_moduli:
                self.itz_analysis_button = Gtk.Button()
                self.itz_analysis_button.set_size_request(200, 60)

                button_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)

                icon_label = Gtk.Label()
                icon_label.set_markup('<span size="x-large">📈</span>')
                button_box.pack_start(icon_label, False, False, 0)

                text_label = Gtk.Label()
                text_label.set_markup('<b>ITZ Analysis</b>')
                button_box.pack_start(text_label, False, False, 0)

                desc_label = Gtk.Label()
                desc_label.set_markup('<small>Moduli vs distance\nfrom aggregate surface</small>')
                desc_label.set_justify(Gtk.Justification.CENTER)
                button_box.pack_start(desc_label, False, False, 0)

                self.itz_analysis_button.add(button_box)
                self.itz_analysis_button.connect('clicked', self._on_itz_analysis_clicked)
                self.itz_analysis_button.set_tooltip_text("Analyze elastic moduli variation in interfacial transition zone")

                buttons_grid.attach(self.itz_analysis_button, button_col, 0, 1, 1)
                button_col += 1

            # Strain Energy 3D Visualization button
            has_strain_energy = self._has_strain_energy(operation)
            if has_strain_energy:
                self.strain_energy_button = Gtk.Button()
                self.strain_energy_button.set_size_request(200, 60)

                button_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)

                icon_label = Gtk.Label()
                icon_label.set_markup('<span size="x-large">🔥</span>')
                button_box.pack_start(icon_label, False, False, 0)

                text_label = Gtk.Label()
                text_label.set_markup('<b>Strain Energy 3D</b>')
                button_box.pack_start(text_label, False, False, 0)

                desc_label = Gtk.Label()
                desc_label.set_markup('<small>3D heat map visualization\nof elastic strain energy</small>')
                desc_label.set_justify(Gtk.Justification.CENTER)
                button_box.pack_start(desc_label, False, False, 0)

                self.strain_energy_button.add(button_box)
                self.strain_energy_button.connect('clicked', self._on_strain_energy_clicked)
                self.strain_energy_button.set_tooltip_text("View 3D heat map of elastic strain energy distribution")

                buttons_grid.attach(self.strain_energy_button, button_col, 0, 1, 1)
                button_col += 1

        # Data Plotting button (NOT for elastic operations)
        has_csv = self._has_csv_data(operation)
        self.logger.info(f"Results panel: Operation '{operation.name}' has CSV data: {has_csv}")
        if has_csv and not is_elastic:
            self.plot_data_button = Gtk.Button()
            self.plot_data_button.set_size_request(200, 60)

            button_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)

            icon_label = Gtk.Label()
            icon_label.set_markup('<span size="x-large">📊</span>')
            button_box.pack_start(icon_label, False, False, 0)

            text_label = Gtk.Label()
            text_label.set_markup('<b>Plot Data</b>')
            button_box.pack_start(text_label, False, False, 0)

            desc_label = Gtk.Label()
            desc_label.set_markup('<small>Interactive plotting of\nsimulation data variables</small>')
            desc_label.set_justify(Gtk.Justification.CENTER)
            button_box.pack_start(desc_label, False, False, 0)

            self.plot_data_button.add(button_box)
            self.plot_data_button.connect('clicked', self._on_plot_data_clicked)
            self.plot_data_button.set_tooltip_text("Create plots from simulation data CSV files")

            buttons_grid.attach(self.plot_data_button, button_col, 0, 1, 1)
            button_col += 1
        
        self.results_box.pack_start(buttons_grid, False, False, 20)
        
        # Results summary (if available)
        self._add_results_summary(operation)
        
        self.results_box.show_all()
    
    def _add_results_summary(self, operation) -> None:
        """Add results summary information."""
        summary_frame = Gtk.Frame(label="Results Summary")
        summary_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        summary_box.set_margin_top(10)
        summary_box.set_margin_bottom(10)
        summary_box.set_margin_left(10)
        summary_box.set_margin_right(10)
        
        # Add summary information
        info_items = []
        
        # Check for 3D results
        if self._has_3d_results(operation):
            count_3d = self._count_3d_files(operation)
            info_items.append(f"3D Microstructures: {count_3d} files available")
        
        # Check for CSV data
        if self._has_csv_data(operation):
            count_csv = self._count_csv_files(operation)
            info_items.append(f"Data Files: {count_csv} CSV files for analysis")
        
        # Add operation details
        if hasattr(operation, 'end_time') and operation.end_time:
            completion_time = operation.end_time.strftime("%Y-%m-%d %H:%M:%S")
            info_items.append(f"Completed: {completion_time}")
        
        if hasattr(operation, 'progress'):
            progress_percent = int(operation.progress * 100) if operation.progress else 0
            info_items.append(f"Progress: {progress_percent}%")
        
        # Display information
        if info_items:
            for item in info_items:
                item_label = Gtk.Label(item)
                item_label.set_halign(Gtk.Align.START)
                summary_box.pack_start(item_label, False, False, 0)
        else:
            no_info_label = Gtk.Label("No detailed results information available")
            no_info_label.set_halign(Gtk.Align.START)
            summary_box.pack_start(no_info_label, False, False, 0)
        
        summary_frame.add(summary_box)
        self.results_box.pack_start(summary_frame, False, False, 0)
    
    def _get_operation_output_dir(self, operation) -> Optional[str]:
        """Get the output directory path for an operation."""
        try:
            if not operation or not operation.name:
                return None
            
            # Construct the path to Operations/{operation_name}
            project_root = Path(__file__).parent.parent.parent.parent
            output_dir = project_root / "Operations" / operation.name
            
            return str(output_dir)
            
        except Exception as e:
            self.logger.error(f"Error getting output directory for operation {operation.name}: {e}")
            return None
    
    def _has_3d_results(self, operation) -> bool:
        """Check if operation has 3D microstructure results (.img files)."""
        try:
            output_dir = self._get_operation_output_dir(operation)
            self.logger.info(f"Results panel: Checking 3D results for '{operation.name}' in directory: {output_dir}")
            
            if not output_dir:
                self.logger.info(f"Results panel: No output directory found for '{operation.name}'")
                return False
            
            output_path = Path(output_dir)
            if not output_path.exists():
                self.logger.info(f"Results panel: Output directory does not exist: {output_path}")
                return False
            
            # Look for any .img files (hydration time-series, final, or regular microstructures)
            hydration_img_files = list(output_path.glob("*.img.*h.*.*"))
            final_img_files = list(output_path.glob("HydrationOf_*.img.*.*"))
            regular_img_files = list(output_path.glob("*.img"))
            
            self.logger.info(f"Results panel: Found in '{operation.name}': {len(hydration_img_files)} hydration img files, {len(final_img_files)} final img files, {len(regular_img_files)} regular img files")
            
            return len(hydration_img_files) > 0 or len(final_img_files) > 0 or len(regular_img_files) > 0
            
        except Exception as e:
            self.logger.error(f"Error checking for 3D results: {e}")
            return False
    
    def _has_csv_data(self, operation) -> bool:
        """Check if operation has CSV data files for plotting."""
        try:
            output_dir = self._get_operation_output_dir(operation)
            self.logger.info(f"Results panel: Checking CSV data for '{operation.name}' in directory: {output_dir}")
            
            if not output_dir:
                self.logger.info(f"Results panel: No output directory found for '{operation.name}'")
                return False
            
            output_path = Path(output_dir)
            if not output_path.exists():
                self.logger.info(f"Results panel: Output directory does not exist: {output_path}")
                return False
            
            # Look for CSV files
            csv_files = list(output_path.glob("*.csv"))
            self.logger.info(f"Results panel: Found {len(csv_files)} CSV files in '{operation.name}'")
            
            return len(csv_files) > 0
            
        except Exception as e:
            self.logger.error(f"Error checking for CSV data: {e}")
            return False
    
    def _count_3d_files(self, operation) -> int:
        """Count the number of 3D result files."""
        try:
            output_dir = self._get_operation_output_dir(operation)
            if not output_dir:
                return 0
            
            output_path = Path(output_dir)
            if not output_path.exists():
                return 0
            
            hydration_img_files = list(output_path.glob("*.img.*h.*.*"))
            final_img_files = list(output_path.glob("HydrationOf_*.img.*.*"))
            regular_img_files = list(output_path.glob("*.img"))
            
            return len(hydration_img_files) + len(final_img_files) + len(regular_img_files)
            
        except Exception as e:
            self.logger.error(f"Error counting 3D files: {e}")
            return 0
    
    def _count_csv_files(self, operation) -> int:
        """Count the number of CSV data files."""
        try:
            output_dir = self._get_operation_output_dir(operation)
            if not output_dir:
                return 0
            
            output_path = Path(output_dir)
            if not output_path.exists():
                return 0
            
            csv_files = list(output_path.glob("*.csv"))
            return len(csv_files)
            
        except Exception as e:
            self.logger.error(f"Error counting CSV files: {e}")
            return 0
    
    def _get_operation_output_dir(self, result_obj) -> Optional[str]:
        """Get the output directory for a result object."""
        # For new result objects, use the folder_path directly
        if hasattr(result_obj, 'folder_path'):
            return result_obj.folder_path
        
        # Fallback for old operation objects (if any remain)
        if hasattr(result_obj, 'output_dir') and result_obj.output_dir:
            return result_obj.output_dir
        
        if hasattr(result_obj, 'metadata') and result_obj.metadata and 'output_directory' in result_obj.metadata:
            return result_obj.metadata['output_directory']
        
        # Try to construct from name
        project_root = Path(__file__).parent.parent.parent.parent.parent
        operations_dir = project_root / "Operations"
        potential_folder = operations_dir / result_obj.name
        if potential_folder.exists():
            return str(potential_folder)
        
        return None
    
    def _load_completed_operations(self) -> None:
        """Load results from Operations folder - focus on actual result folders, not operation status."""
        self.operation_liststore.clear()
        
        try:
            self.logger.info("Results panel: Starting to load results from Operations folder")
            
            # Load results directly from Operations folder
            # Go up from src/app/windows/panels/results_panel.py to project root
            project_root = Path(__file__).parent.parent.parent.parent.parent
            operations_dir = project_root / "Operations"
            
            if not operations_dir.exists():
                self.logger.warning(f"Results panel: Operations directory not found: {operations_dir}")
                return
            
            self.logger.info(f"Results panel: Scanning Operations directory: {operations_dir}")
            
            # Get all subdirectories in Operations folder - these are our results
            # Also scan for nested elastic operations (e.g., Operations/HY-Elk/Elastic-HY-Elk-657.89h/)
            all_result_folders = []

            for result_folder in operations_dir.iterdir():
                if not result_folder.is_dir():
                    continue

                # Add top-level operation folder
                all_result_folders.append(result_folder)

                # Check for nested elastic operations inside this folder
                for nested_folder in result_folder.iterdir():
                    if (nested_folder.is_dir() and
                        nested_folder.name.startswith('Elastic-')):
                        self.logger.info(f"Results panel: Found nested elastic operation: {nested_folder.name}")
                        all_result_folders.append(nested_folder)

            # Process all found result folders
            for result_folder in all_result_folders:
                result_name = result_folder.name
                self.logger.info(f"Results panel: Processing result folder: {result_name}")

                # Determine result type based on folder contents and name patterns
                result_type = self._determine_result_type(result_folder)
                
                # Get creation/modification date as completion date
                completion_date = "Unknown"
                try:
                    # Use the most recent modification time in the folder
                    latest_time = result_folder.stat().st_mtime
                    for file_path in result_folder.rglob("*"):
                        if file_path.is_file():
                            file_mtime = file_path.stat().st_mtime
                            if file_mtime > latest_time:
                                latest_time = file_mtime
                    
                    from datetime import datetime
                    completion_date = datetime.fromtimestamp(latest_time).strftime("%m/%d %H:%M")
                except Exception as e:
                    self.logger.warning(f"Could not determine completion date for {result_name}: {e}")
                
                # Create a result object compatible with existing dialog interfaces
                result_obj = type('Result', (), {
                    'name': result_name,
                    'folder_path': str(result_folder),
                    'type': result_type,
                    # For compatibility with HydrationResultsViewer
                    'output_dir': str(result_folder),
                    'metadata': {
                        'output_directory': str(result_folder),
                        'source': 'results_panel'
                    }
                })()
                
                # Add to list
                self.operation_liststore.append([
                    result_name,
                    result_type,
                    completion_date,
                    result_obj
                ])
                
                self.logger.info(f"Results panel: Added result '{result_name}' of type '{result_type}'")
            
            self.logger.info(f"Results panel: Loaded {len(self.operation_liststore)} results from Operations folder")
            
        except Exception as e:
            self.logger.error(f"Error loading results: {e}")
    
    def _determine_result_type(self, result_folder: Path) -> str:
        """Determine the type of result based on folder contents and naming."""
        try:
            folder_name = result_folder.name.lower()
            
            # Check folder contents
            files = list(result_folder.rglob("*"))
            file_names = [f.name.lower() for f in files if f.is_file()]
            
            self.logger.info(f"Results panel: Analyzing '{result_folder.name}' - found {len(file_names)} files")
            
            # First check: Elastic moduli operations
            if folder_name.startswith('elastic-') or 'elastic' in folder_name:
                # Check for elastic-specific files
                has_effective_moduli = any('effectivemoduli.csv' in fname for fname in file_names)
                has_itz_moduli = any('itzmoduli.csv' in fname for fname in file_names)
                has_elastic_progress = any('elastic_progress.json' in fname for fname in file_names)

                if has_effective_moduli or has_itz_moduli or has_elastic_progress:
                    self.logger.info(f"Results panel: '{result_folder.name}' classified as Elastic Moduli (files detected)")
                    return "Elastic Moduli"

            # Second check: Explicit hydration folder names
            if any(pattern in folder_name for pattern in ['hydration', 'hydrationsim']):
                self.logger.info(f"Results panel: '{result_folder.name}' classified as Hydration (folder name)")
                return "Hydration Simulation"
            
            # Check for specific hydration file patterns that indicate time-series simulation
            has_time_series_img = any(
                ('.img.' in fname and 'h.' in fname) or 'hydrationof' in fname.lower()
                for fname in file_names
            )
            
            has_csv_data = any('.csv' in fname for fname in file_names)
            has_img_files = any('.img' in fname for fname in file_names)
            
            self.logger.info(f"Results panel: '{result_folder.name}' - time_series_img: {has_time_series_img}, csv: {has_csv_data}, img: {has_img_files}")
            
            # Hydration simulation: Has time-series img files OR has both CSV and img files
            if has_time_series_img:
                self.logger.info(f"Results panel: '{result_folder.name}' classified as Hydration (time-series files)")
                return "Hydration Simulation"
            
            if has_csv_data and has_img_files:
                self.logger.info(f"Results panel: '{result_folder.name}' classified as Hydration (CSV + IMG files)")
                return "Hydration Simulation"
            
            # Microstructure generation: Has .img files but no time-series or CSV
            if has_img_files and not has_time_series_img and not has_csv_data:
                self.logger.info(f"Results panel: '{result_folder.name}' classified as Microstructure (IMG only)")
                return "Microstructure Generation"
            
            # Other analysis types
            if has_csv_data and not has_img_files:
                self.logger.info(f"Results panel: '{result_folder.name}' classified as Data Analysis (CSV only)")
                return "Data Analysis"
            
            # If no clear pattern, classify as unknown
            self.logger.info(f"Results panel: '{result_folder.name}' classified as Unknown")
            return "Unknown Analysis"
            
        except Exception as e:
            self.logger.error(f"Error determining result type for {result_folder}: {e}")
            return "Unknown"
    
    def _load_completed_operations_old(self) -> None:
        """OLD METHOD: Load completed operations from operations panel (kept for reference)."""
        self.operation_liststore.clear()
        
        try:
            self.logger.info("Results panel: Starting to load completed operations")
            
            # Load from Operations panel (combines JSON and database sources)
            if hasattr(self.parent, 'operations_panel'):
                self.logger.info("Results panel: Found operations_panel in parent")
                operations_panel = self.parent.operations_panel
                
                # Get all operations from operations panel
                all_operations = getattr(operations_panel, 'operations', {})
                self.logger.info(f"Results panel: Found {len(all_operations)} operations in Operations panel")
            else:
                self.logger.warning("Results panel: No operations_panel found in parent")
                return
            
            for operation_id, operation in all_operations.items():
                # Debug: Log operation status for troubleshooting
                op_status = "No status"
                if hasattr(operation, 'status'):
                    op_status = str(operation.status)
                self.logger.info(f"Results panel: Operation '{operation.name}': status = '{op_status}'")
                
                # Only include completed operations - check various status formats
                status_check = False
                if hasattr(operation, 'status'):
                    status_str = str(operation.status).lower()
                    # Check for various completion status formats
                    status_check = any(status in status_str for status in [
                        'completed', 'finished', 'complete', 'done', 'success'
                    ])
                
                if status_check:
                    # Format completion date
                    completion_date = "Unknown"
                    if hasattr(operation, 'end_time') and operation.end_time:
                        completion_date = operation.end_time.strftime("%m/%d %H:%M")
                    elif hasattr(operation, 'start_time') and operation.start_time:
                        completion_date = operation.start_time.strftime("%m/%d %H:%M")
                    
                    # Format operation type with better detection for hydration operations
                    op_type = "Unknown"
                    if hasattr(operation, 'operation_type'):
                        op_type_str = str(operation.operation_type).replace('OperationType.', '').replace('_', ' ').title()
                        # Special handling for hydration operations that might be misclassified
                        if 'hydration' in operation.name.lower() or 'hydrationsim' in operation.name.lower():
                            op_type = "Hydration Simulation"
                        else:
                            op_type = op_type_str
                    elif hasattr(operation, 'type'):
                        op_type_str = str(operation.type).replace('OperationType.', '').replace('_', ' ').title()
                        # Special handling for hydration operations that might be misclassified
                        if 'hydration' in operation.name.lower() or 'hydrationsim' in operation.name.lower():
                            op_type = "Hydration Simulation"
                        else:
                            op_type = op_type_str
                    
                    self.logger.info(f"Results panel: Operation '{operation.name}' classified as '{op_type}'")
                    
                    # Add to list
                    self.operation_liststore.append([
                        operation.name,
                        op_type,
                        completion_date,
                        operation
                    ])
                    self.logger.info(f"Results panel: Added completed operation '{operation.name}'")
            
            # Temporary debug: If no completed operations found, show all operations for debugging
            completed_count = len(self.operation_liststore)
            if completed_count == 0 and all_operations:
                self.logger.info(f"No completed operations found, showing all {len(all_operations)} operations for debugging")
                for operation_id, operation in all_operations.items():
                    # Format completion date
                    completion_date = "Unknown"
                    if hasattr(operation, 'end_time') and operation.end_time:
                        completion_date = operation.end_time.strftime("%m/%d %H:%M")
                    elif hasattr(operation, 'start_time') and operation.start_time:
                        completion_date = operation.start_time.strftime("%m/%d %H:%M")
                    
                    # Format operation type
                    op_type = "Unknown"
                    if hasattr(operation, 'operation_type'):
                        op_type = str(operation.operation_type).replace('OperationType.', '').replace('_', ' ').title()
                    elif hasattr(operation, 'type'):
                        op_type = str(operation.type).replace('OperationType.', '').replace('_', ' ').title()
                    
                    # Show status in name for debugging
                    debug_name = f"{operation.name} [{str(operation.status) if hasattr(operation, 'status') else 'No Status'}]"
                    
                    # Add to list
                    self.operation_liststore.append([
                        debug_name,
                        op_type,
                        completion_date,
                        operation
                    ])
            
            self.logger.info(f"Loaded {len(self.operation_liststore)} operations ({'completed' if completed_count > 0 else 'all for debugging'})")
            
        except Exception as e:
            self.logger.error(f"Error loading completed operations: {e}")
    
    def _on_refresh_clicked(self, button) -> None:
        """Handle refresh button click."""
        self._load_completed_operations()
    
    def _on_operation_selection_changed(self, selection) -> None:
        """Handle operation selection change."""
        model, tree_iter = selection.get_selected()
        if tree_iter is not None:
            # Get selected operation
            self.selected_operation = model[tree_iter][3]  # operation object
            self._show_analysis_tools(self.selected_operation)
        else:
            self.selected_operation = None
            self._show_no_selection_message()
    
    def _on_view_3d_results_clicked(self, button) -> None:
        """Handle View 3D Results button click."""
        if not self.selected_operation:
            self.logger.warning("No operation selected for 3D results viewing")
            return

        # Defensive: Check button is still valid
        if not button or not isinstance(button, Gtk.Button):
            self.logger.warning("Invalid button reference in _on_view_3d_results_clicked")
            return

        # Defensive: Check we have a valid parent window
        parent_window = self.get_toplevel()
        if not parent_window or not isinstance(parent_window, Gtk.Window):
            self.logger.error("Cannot open 3D viewer: invalid parent window")
            return

        try:
            # Get operation name safely (works for both dict and object)
            op_name = getattr(self.selected_operation, 'name', 'Unknown') if hasattr(self.selected_operation, 'name') else self.selected_operation.get('name', 'Unknown')
            self.logger.info(f"Opening 3D results viewer for operation: {op_name}")

            # Import here to avoid circular imports
            from app.windows.dialogs.hydration_results_viewer import HydrationResultsViewer

            # Create and show the 3D results viewer dialog
            viewer = HydrationResultsViewer(
                parent=parent_window,
                operation=self.selected_operation
            )

            # Defensive: Verify viewer was created successfully
            if not viewer:
                raise RuntimeError("Failed to create HydrationResultsViewer instance")

            viewer.show_all()
            self.logger.info("3D results viewer opened successfully")

        except ImportError as e:
            self.logger.error(f"Failed to import HydrationResultsViewer: {e}", exc_info=True)
            self._show_error_dialog("Import Error", f"Failed to load 3D visualization module: {e}")
        except Exception as e:
            self.logger.error(f"Error opening 3D results viewer: {e}", exc_info=True)
            self._show_error_dialog("Error Opening 3D Results", f"Failed to open 3D results viewer: {e}")
    
    def _on_plot_data_clicked(self, button) -> None:
        """Handle Plot Data button click."""
        if not self.selected_operation:
            return
        
        try:
            # Import here to avoid circular imports
            from app.windows.dialogs.data_plotter import DataPlotter
            
            # Create and show the data plotting dialog
            plotter = DataPlotter(
                parent=self.get_toplevel(),
                operation=self.selected_operation
            )
            plotter.run()
            plotter.destroy()
            
        except Exception as e:
            self.logger.error(f"Error opening data plotter: {e}")
            # Show error dialog
            dialog = Gtk.MessageDialog(
                transient_for=self.get_toplevel(),
                flags=0,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Error Opening Data Plotter"
            )
            dialog.format_secondary_text(f"Failed to open data plotter: {e}")
            dialog.run()
            dialog.destroy()

    def _on_effective_moduli_clicked(self, button) -> None:
        """Handle Effective Moduli button click."""
        if not self.selected_operation:
            return

        try:
            # Import here to avoid circular imports
            from app.windows.dialogs.effective_moduli_viewer import EffectiveModuliViewer

            # Create and show the effective moduli viewer dialog
            viewer = EffectiveModuliViewer(
                parent=self.get_toplevel(),
                operation=self.selected_operation
            )
            viewer.run()
            viewer.destroy()

        except Exception as e:
            self.logger.error(f"Error opening effective moduli viewer: {e}")
            # Show error dialog
            dialog = Gtk.MessageDialog(
                transient_for=self.get_toplevel(),
                flags=0,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Error Opening Effective Moduli Viewer"
            )
            dialog.format_secondary_text(f"Failed to open effective moduli viewer: {e}")
            dialog.run()
            dialog.destroy()

    def _on_itz_analysis_clicked(self, button) -> None:
        """Handle ITZ Analysis button click."""
        if not self.selected_operation:
            return

        try:
            # Import here to avoid circular imports
            from app.windows.dialogs.itz_analysis_viewer import ITZAnalysisViewer

            # Create and show the ITZ analysis viewer dialog
            viewer = ITZAnalysisViewer(
                parent=self.get_toplevel(),
                operation=self.selected_operation
            )
            viewer.run()
            viewer.destroy()

        except Exception as e:
            self.logger.error(f"Error opening ITZ analysis viewer: {e}")
            # Show error dialog
            dialog = Gtk.MessageDialog(
                transient_for=self.get_toplevel(),
                flags=0,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Error Opening ITZ Analysis Viewer"
            )
            dialog.format_secondary_text(f"Failed to open ITZ analysis viewer: {e}")
            dialog.run()
            dialog.destroy()

    def _on_strain_energy_clicked(self, button) -> None:
        """Handle Strain Energy 3D button click."""
        if not self.selected_operation:
            return

        try:
            # Import here to avoid circular imports - use PyVista-based viewer
            from app.windows.dialogs.pyvista_strain_viewer import PyVistaStrainViewer

            # Find the strain energy .img file using the same logic as detection
            operation_dir = self._get_operation_output_dir(self.selected_operation)
            if not operation_dir:
                raise Exception("Operation output directory not found")

            operation_dir_path = Path(operation_dir)
            strain_energy_file = None

            # Look for energy.img file (new naming convention after elastic.c fix)
            test_file = operation_dir_path / "energy.img"
            if test_file.exists():
                strain_energy_file = test_file
            else:
                # Fall back to old patterns for backward compatibility
                # Pattern 1: {operation_name}.img
                test_file = operation_dir_path / f"{self.selected_operation.name}.img"
                if test_file.exists():
                    strain_energy_file = test_file
                else:
                    # Pattern 2: Any Elastic-*.img file in the directory
                    for img_file in operation_dir_path.glob("Elastic-*.img"):
                        strain_energy_file = img_file
                        break

                    # Pattern 3: Check for any .img file that's not newcem.img
                    if not strain_energy_file:
                        for img_file in operation_dir_path.glob("*.img"):
                            if img_file.name != "newcem.img":
                                strain_energy_file = img_file
                                break

            if not strain_energy_file:
                raise Exception("No strain energy .img file found in operation directory")

            # Create and show the PyVista strain energy viewer dialog
            viewer = PyVistaStrainViewer(
                parent_window=self.get_toplevel(),
                operation_name=self.selected_operation.name,
                img_file_path=str(strain_energy_file)
            )
            viewer.run()
            viewer.destroy()

        except Exception as e:
            self.logger.error(f"Error opening strain energy viewer: {e}")
            # Show error dialog
            dialog = Gtk.MessageDialog(
                transient_for=self.get_toplevel(),
                flags=0,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Error Opening Strain Energy Viewer"
            )
            dialog.format_secondary_text(f"Failed to open strain energy viewer: {e}")
            dialog.run()
            dialog.destroy()

    def _is_elastic_operation(self, operation) -> bool:
        """Check if operation is an elastic moduli calculation."""
        if hasattr(operation, 'operation_type'):
            op_type_str = str(operation.operation_type)
            return 'ELASTIC' in op_type_str.upper()
        if hasattr(operation, 'type'):
            op_type_str = str(operation.type)
            return 'ELASTIC' in op_type_str.upper()
        # Check operation name as fallback
        return operation.name.startswith('Elastic-') if hasattr(operation, 'name') else False

    def _has_effective_moduli(self, operation) -> bool:
        """Check if operation has EffectiveModuli.csv file."""
        try:
            operation_dir = self._get_operation_output_dir(operation)
            if operation_dir:
                effective_moduli_file = Path(operation_dir) / "EffectiveModuli.csv"
                return effective_moduli_file.exists()
            return False
        except Exception:
            return False

    def _has_itz_moduli(self, operation) -> bool:
        """Check if operation has ITZmoduli.csv file."""
        try:
            operation_dir = self._get_operation_output_dir(operation)
            if operation_dir:
                itz_moduli_file = Path(operation_dir) / "ITZmoduli.csv"
                return itz_moduli_file.exists()
            return False
        except Exception:
            return False

    def _has_strain_energy(self, operation) -> bool:
        """Check if operation has strain energy .img file."""
        try:
            operation_dir = self._get_operation_output_dir(operation)
            if operation_dir:
                # Look for .img files that match the elastic operation pattern
                operation_dir_path = Path(operation_dir)

                # Check for energy.img file (new naming convention after elastic.c fix)
                energy_file = operation_dir_path / "energy.img"
                if energy_file.exists():
                    return True

                # Fall back to old patterns for backward compatibility
                # Pattern 1: {operation_name}.img
                strain_energy_file = operation_dir_path / f"{operation.name}.img"
                if strain_energy_file.exists():
                    return True

                # Pattern 2: Any Elastic-*.img file in the directory
                for img_file in operation_dir_path.glob("Elastic-*.img"):
                    return True

                # Pattern 3: Check for any .img file that's not newcem.img (microstructure)
                for img_file in operation_dir_path.glob("*.img"):
                    if img_file.name != "newcem.img":
                        return True

            return False
        except Exception:
            return False

    def refresh_operations_list(self) -> None:
        """Public method to refresh the operations list (called from Operations panel)."""
        self._load_completed_operations()
    
    def on_show(self) -> None:
        """Called when the Results tab is shown."""
        # Refresh the operations list when the tab becomes visible
        self._load_completed_operations()

    def _show_error_dialog(self, title: str, message: str) -> None:
        """Show a thread-safe error dialog to the user.

        Args:
            title: Dialog title
            message: Error message to display
        """
        try:
            # Get parent window safely
            parent = self.get_toplevel()
            if not parent or not isinstance(parent, Gtk.Window):
                self.logger.error(f"Cannot show error dialog '{title}': no valid parent window")
                return

            # Create and show error dialog
            dialog = Gtk.MessageDialog(
                transient_for=parent,
                flags=Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text=title
            )
            dialog.format_secondary_text(message)
            dialog.run()
            dialog.destroy()

        except Exception as e:
            # Last resort: log the error if we can't even show a dialog
            self.logger.error(f"Failed to show error dialog '{title}': {e}", exc_info=True)
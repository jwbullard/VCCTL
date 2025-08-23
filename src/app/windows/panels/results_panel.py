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
        self.operation_treeview.append_column(name_column)
        
        # Type column
        type_renderer = Gtk.CellRendererText()
        type_column = Gtk.TreeViewColumn("Type", type_renderer, text=1)
        type_column.set_resizable(True)
        type_column.set_min_width(120)
        self.operation_treeview.append_column(type_column)
        
        # Completion date column
        date_renderer = Gtk.CellRendererText()
        date_column = Gtk.TreeViewColumn("Last Modified", date_renderer, text=2)
        date_column.set_resizable(True)
        date_column.set_min_width(120)
        self.operation_treeview.append_column(date_column)
        
        # Scrolled window
        self.operation_scrolled = Gtk.ScrolledWindow()
        self.operation_scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.operation_scrolled.set_size_request(-1, 150)
        self.operation_scrolled.add(self.operation_treeview)
    
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
        
        # 3D Visualization button
        has_3d = self._has_3d_results(operation)
        self.logger.info(f"Results panel: Operation '{operation.name}' has 3D results: {has_3d}")
        if has_3d:
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
        
        # Data Plotting button
        has_csv = self._has_csv_data(operation)
        self.logger.info(f"Results panel: Operation '{operation.name}' has CSV data: {has_csv}")
        if has_csv:
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
            for result_folder in operations_dir.iterdir():
                if not result_folder.is_dir():
                    continue
                    
                result_name = result_folder.name
                self.logger.info(f"Results panel: Found result folder: {result_name}")
                
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
            
            # First check: Explicit hydration folder names
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
            return
        
        try:
            # Import here to avoid circular imports
            from app.windows.dialogs.hydration_results_viewer import HydrationResultsViewer
            
            # Create and show the 3D results viewer dialog
            viewer = HydrationResultsViewer(
                parent=self.get_toplevel(),
                operation=self.selected_operation
            )
            viewer.show_all()
            
        except Exception as e:
            self.logger.error(f"Error opening 3D results viewer: {e}")
            # Show error dialog
            dialog = Gtk.MessageDialog(
                transient_for=self.get_toplevel(),
                flags=0,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Error Opening 3D Results"
            )
            dialog.format_secondary_text(f"Failed to open 3D results viewer: {e}")
            dialog.run()
            dialog.destroy()
    
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
    
    def refresh_operations_list(self) -> None:
        """Public method to refresh the operations list (called from Operations panel)."""
        self._load_completed_operations()
    
    def on_show(self) -> None:
        """Called when the Results tab is shown."""
        # Refresh the operations list when the tab becomes visible
        self._load_completed_operations()
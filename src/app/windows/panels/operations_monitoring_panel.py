#!/usr/bin/env python3
"""
Operations Monitoring Panel for VCCTL

Provides real-time monitoring and management of simulation operations,
including progress tracking, resource usage, and operation controls.
"""

import gi
import json
import logging
import time
import threading
import subprocess
import signal
import os
import psutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, Pango, GLib

if TYPE_CHECKING:
    from app.windows.main_window import VCCTLMainWindow

from app.services.service_container import get_service_container


class OperationStatus(Enum):
    """Status of operations."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class OperationType(Enum):
    """Types of operations."""
    HYDRATION_SIMULATION = "hydration_simulation"
    MICROSTRUCTURE_GENERATION = "microstructure_generation"
    PROPERTY_CALCULATION = "property_calculation"
    DATA_ANALYSIS = "data_analysis"
    FILE_OPERATION = "file_operation"
    BATCH_OPERATION = "batch_operation"


@dataclass
class Operation:
    """Represents a single operation being monitored."""
    id: str
    name: str
    operation_type: OperationType
    status: OperationStatus = OperationStatus.PENDING
    progress: float = 0.0  # 0.0 to 1.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    paused_time: Optional[datetime] = None  # Time when operation was paused
    estimated_duration: Optional[timedelta] = None
    current_step: str = ""
    total_steps: int = 0
    completed_steps: int = 0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0  # MB
    disk_usage: float = 0.0  # MB
    error_message: Optional[str] = None
    log_entries: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Process control fields (not serialized)
    process: Optional[subprocess.Popen] = field(default=None, init=False)
    pid: Optional[int] = field(default=None, init=False)
    working_directory: Optional[str] = field(default=None, init=False)
    command_line: Optional[List[str]] = field(default=None, init=False)
    stdout_file: Optional[str] = field(default=None, init=False)
    stderr_file: Optional[str] = field(default=None, init=False)
    stdout_handle: Optional[object] = field(default=None, init=False)
    stderr_handle: Optional[object] = field(default=None, init=False)
    
    @property
    def duration(self) -> Optional[timedelta]:
        """Get operation duration (frozen when paused)."""
        if self.start_time:
            if self.status == OperationStatus.PAUSED and self.paused_time:
                # Return duration up to pause time
                return self.paused_time - self.start_time
            else:
                # Normal duration calculation
                end = self.end_time or datetime.now()
                return end - self.start_time
        return None
    
    @property
    def progress_percentage(self) -> float:
        """Get progress as percentage."""
        return self.progress * 100.0
    
    @property
    def estimated_time_remaining(self) -> Optional[timedelta]:
        """Estimate remaining time based on progress."""
        if self.progress > 0 and self.duration and self.status == OperationStatus.RUNNING:
            total_estimated = self.duration / self.progress
            return total_estimated - self.duration
        return None
    
    def is_process_running(self) -> bool:
        """Check if the underlying process is still running."""
        if self.process:
            poll_result = self.process.poll()
            return poll_result is None
        elif self.pid:
            try:
                # Check if process exists
                process = psutil.Process(self.pid)
                return process.is_running()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                return False
        return False
    
    def get_process_info(self) -> Optional[Dict[str, Any]]:
        """Get current process information (CPU, memory usage)."""
        if not self.is_process_running():
            return None
        
        try:
            if self.pid:
                process = psutil.Process(self.pid)
                return {
                    'cpu_percent': process.cpu_percent(),
                    'memory_mb': process.memory_info().rss / 1024 / 1024,
                    'status': process.status(),
                    'create_time': datetime.fromtimestamp(process.create_time())
                }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
        return None
    
    def pause_process(self) -> bool:
        """Pause the underlying process using OS signals."""
        if not self.is_process_running():
            return False
        
        try:
            if os.name == 'nt':  # Windows
                # Windows doesn't have SIGSTOP, would need more complex implementation
                return False
            else:  # Unix/Linux/macOS
                os.kill(self.pid, signal.SIGSTOP)
                return True
        except (OSError, ProcessLookupError):
            return False
    
    def resume_process(self) -> bool:
        """Resume the paused process using OS signals."""
        if not self.is_process_running():
            return False
        
        try:
            if os.name == 'nt':  # Windows
                # Windows doesn't have SIGCONT, would need more complex implementation
                return False
            else:  # Unix/Linux/macOS
                os.kill(self.pid, signal.SIGCONT)
                return True
        except (OSError, ProcessLookupError):
            return False
    
    def terminate_process(self) -> bool:
        """Terminate the underlying process."""
        if not self.is_process_running():
            return False
        
        try:
            if self.process:
                self.process.terminate()
                # Wait a bit for graceful termination
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Force kill if it doesn't terminate gracefully
                    self.process.kill()
                
                # Close output file handles when terminating
                self.close_output_files()
                return True
            elif self.pid:
                os.kill(self.pid, signal.SIGTERM)
                # Close output file handles when terminating
                self.close_output_files()
                return True
        except (OSError, ProcessLookupError):
            pass
        return False
    
    def close_output_files(self) -> None:
        """Close stdout/stderr file handles if they're open."""
        try:
            if self.stdout_handle and not self.stdout_handle.closed:
                self.stdout_handle.close()
        except Exception:
            pass  # Ignore close errors
        
        try:
            if self.stderr_handle and not self.stderr_handle.closed:
                self.stderr_handle.close()
        except Exception:
            pass  # Ignore close errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert operation to dictionary for JSON serialization."""
        data = asdict(self)
        
        # Remove process-related fields that shouldn't be serialized
        for field_name in ['process', 'pid', 'working_directory', 'command_line', 
                          'stdout_file', 'stderr_file', 'stdout_handle', 'stderr_handle']:
            data.pop(field_name, None)
        
        # Convert datetime objects to ISO strings
        if self.start_time:
            data['start_time'] = self.start_time.isoformat()
        if self.end_time:
            data['end_time'] = self.end_time.isoformat()
        if self.paused_time:
            data['paused_time'] = self.paused_time.isoformat()
        if self.estimated_duration:
            data['estimated_duration'] = self.estimated_duration.total_seconds()
        # Convert enums to strings
        data['operation_type'] = self.operation_type.value
        data['status'] = self.status.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Operation':
        """Create operation from dictionary (JSON deserialization)."""
        # Convert string datetime back to datetime objects
        if data.get('start_time'):
            data['start_time'] = datetime.fromisoformat(data['start_time'])
        if data.get('end_time'):
            data['end_time'] = datetime.fromisoformat(data['end_time'])
        if data.get('paused_time'):
            data['paused_time'] = datetime.fromisoformat(data['paused_time'])
        if data.get('estimated_duration'):
            data['estimated_duration'] = timedelta(seconds=data['estimated_duration'])
        # Convert strings back to enums
        data['operation_type'] = OperationType(data['operation_type'])
        data['status'] = OperationStatus(data['status'])
        return cls(**data)


@dataclass
class SystemResources:
    """System resource usage information."""
    cpu_usage: float = 0.0  # Percentage
    memory_usage: float = 0.0  # MB
    memory_total: float = 0.0  # MB
    disk_usage: float = 0.0  # MB
    disk_free: float = 0.0  # MB
    network_in: float = 0.0  # MB/s
    network_out: float = 0.0  # MB/s
    timestamp: datetime = field(default_factory=datetime.now)


class OperationsMonitoringPanel(Gtk.Box):
    """
    Operations monitoring panel for VCCTL.
    
    Features:
    - Real-time operation monitoring
    - Progress tracking and visualization
    - Resource usage monitoring
    - Operation control (start, stop, pause)
    - Operation history and logs
    - Performance metrics
    """
    
    def __init__(self, main_window: 'VCCTLMainWindow'):
        """Initialize the operations monitoring panel."""
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        self.main_window = main_window
        self.logger = logging.getLogger('VCCTL.OperationsMonitoringPanel')
        self.service_container = get_service_container()
        
        # Operation tracking
        self.operations: Dict[str, Operation] = {}
        self.operation_counter = 0
        self.system_resources = SystemResources()
        
        # Persistence
        self.operations_file = Path.cwd() / "config" / "operations_history.json"
        
        # Monitoring control
        self.monitoring_active = False
        self.update_interval = 1.0  # seconds
        self.monitor_thread: Optional[threading.Thread] = None
        self.last_ui_update = 0.0  # Track last UI update time
        self.ui_update_throttle = 0.2  # Minimum seconds between UI updates
        
        # UI components
        self.operations_store: Optional[Gtk.ListStore] = None
        self.operations_view: Optional[Gtk.TreeView] = None
        self.resource_charts: Dict[str, Any] = {}
        
        # Setup UI
        self._setup_ui()
        self._connect_signals()
        
        # Load saved operations
        self._load_operations_from_file()
        
        # Start monitoring
        self._start_monitoring()
        
        self.logger.info("Operations monitoring panel initialized")
    
    def _setup_ui(self) -> None:
        """Setup the panel UI."""
        # Create toolbar
        self._create_toolbar()
        
        # Create main content area
        self._create_content_area()
        
        # Create status bar
        self._create_status_bar()
    
    def _create_toolbar(self) -> None:
        """Create the operations toolbar."""
        toolbar = Gtk.Toolbar()
        toolbar.set_style(Gtk.ToolbarStyle.BOTH_HORIZ)
        
        # Start operation button
        self.start_button = Gtk.ToolButton()
        self.start_button.set_icon_name("media-playback-start")
        self.start_button.set_label("Start")
        self.start_button.set_tooltip_text("Launch a new microstructure generation or hydration simulation")
        self.start_button.connect('clicked', self._on_start_operation_clicked)
        toolbar.insert(self.start_button, -1)
        
        # Stop operation button
        self.stop_button = Gtk.ToolButton()
        self.stop_button.set_icon_name("media-playback-stop")
        self.stop_button.set_label("Stop")
        self.stop_button.set_tooltip_text("Terminate the selected running operation immediately")
        self.stop_button.connect('clicked', self._on_stop_operation_clicked)
        toolbar.insert(self.stop_button, -1)
        
        # Pause operation button
        self.pause_button = Gtk.ToolButton()
        self.pause_button.set_icon_name("media-playback-pause")
        self.pause_button.set_label("Pause")
        self.pause_button.set_tooltip_text("Pause running operations or resume paused operations")
        self.pause_button.connect('clicked', self._on_pause_operation_clicked)
        toolbar.insert(self.pause_button, -1)
        
        # Separator
        toolbar.insert(Gtk.SeparatorToolItem(), -1)
        
        # Clear completed button
        self.clear_button = Gtk.ToolButton()
        self.clear_button.set_icon_name("edit-clear")
        self.clear_button.set_label("Clear")
        self.clear_button.set_tooltip_text("Remove all completed, failed, and cancelled operations from the list")
        self.clear_button.connect('clicked', self._on_clear_completed_clicked)
        toolbar.insert(self.clear_button, -1)
        
        # Delete operation button
        self.delete_button = Gtk.ToolButton()
        self.delete_button.set_icon_name("edit-delete")
        self.delete_button.set_label("Delete")
        self.delete_button.set_tooltip_text("Permanently delete selected operation(s) and all their output files")
        self.delete_button.connect('clicked', self._on_delete_selected_operation_clicked)
        toolbar.insert(self.delete_button, -1)
        
        # Refresh button
        self.refresh_button = Gtk.ToolButton()
        self.refresh_button.set_icon_name("view-refresh")
        self.refresh_button.set_label("Refresh")
        self.refresh_button.set_tooltip_text("Update operation status and check for new operations in the Operations folder")
        self.refresh_button.connect('clicked', self._on_refresh_clicked)
        toolbar.insert(self.refresh_button, -1)
        
        # Separator
        toolbar.insert(Gtk.SeparatorToolItem(), -1)
        
        # View 3D Results button
        self.view_3d_button = Gtk.ToolButton()
        self.view_3d_button.set_icon_name("applications-graphics")
        self.view_3d_button.set_label("View 3D Results")
        self.view_3d_button.set_tooltip_text("View 3D microstructure evolution from hydration simulation results")
        self.view_3d_button.set_is_important(True)  # Force label to show
        self.view_3d_button.connect('clicked', self._on_view_3d_results_clicked)
        toolbar.insert(self.view_3d_button, -1)
        
        # Plot Data button
        self.plot_data_button = Gtk.ToolButton()
        self.plot_data_button.set_icon_name("applications-science")
        self.plot_data_button.set_label("Plot Data")
        self.plot_data_button.set_tooltip_text("Create plots from simulation data CSV files")
        self.plot_data_button.set_is_important(True)  # Force label to show
        self.plot_data_button.connect('clicked', self._on_plot_data_clicked)
        toolbar.insert(self.plot_data_button, -1)
        
        # Separator
        toolbar.insert(Gtk.SeparatorToolItem(), -1)
        
        # Settings button
        self.settings_button = Gtk.ToolButton()
        self.settings_button.set_icon_name("preferences-system")
        self.settings_button.set_label("Settings")
        self.settings_button.set_tooltip_text("Configure operation monitoring preferences and resource limits")
        self.settings_button.connect('clicked', self._on_settings_clicked)
        toolbar.insert(self.settings_button, -1)
        
        self.pack_start(toolbar, False, False, 0)
    
    def _update_button_sensitivity(self) -> None:
        """Update button sensitivity based on current operation status."""
        try:
            # Check if any operations are running
            has_running_operations = any(
                op.status == OperationStatus.RUNNING 
                for op in self.operations.values()
            )
            
            # Get selected operation
            selected_operation = self._get_selected_operation()
            has_selection = selected_operation is not None
            selected_is_running = (
                selected_operation and 
                selected_operation.status == OperationStatus.RUNNING
            ) if has_selection else False
            
            # Update button sensitivity
            # Start button: Always enabled
            self.start_button.set_sensitive(True)
            
            # Stop button: Only enabled if selected operation is running
            self.stop_button.set_sensitive(selected_is_running)
            
            # Pause button: Enabled if selected operation is running OR paused
            selected_is_paused = (
                selected_operation and 
                selected_operation.status == OperationStatus.PAUSED
            ) if has_selection else False
            self.pause_button.set_sensitive(selected_is_running or selected_is_paused)
            
            # Clear button: Enabled if there are completed operations
            has_completed = any(
                op.status in [OperationStatus.COMPLETED, OperationStatus.FAILED, OperationStatus.CANCELLED]
                for op in self.operations.values()
            )
            self.clear_button.set_sensitive(has_completed)
            
            # Delete button: Enabled if selection exists and selected operation is not running
            self.delete_button.set_sensitive(has_selection and not selected_is_running)
            
            # 3D Results button: Enabled if selected operation is a completed operation with 3D results
            selected_has_3d_results = False
            if has_selection and selected_operation:
                is_completed = selected_operation.status == OperationStatus.COMPLETED
                has_3d = self._has_3d_results(selected_operation)
                selected_has_3d_results = is_completed and has_3d
            self.view_3d_button.set_sensitive(selected_has_3d_results)
            
            # Plot Data button: Enabled if selected operation has CSV data
            selected_has_csv_data = (
                selected_operation and 
                selected_operation.status == OperationStatus.COMPLETED and
                self._has_csv_data(selected_operation)
            ) if has_selection else False
            self.plot_data_button.set_sensitive(selected_has_csv_data)
            
            # Refresh and Settings: Always enabled (should work even during running operations)
            self.refresh_button.set_sensitive(True)
            self.settings_button.set_sensitive(True)
            
        except Exception as e:
            self.logger.error(f"Error updating button sensitivity: {e}")
    
    def _create_content_area(self) -> None:
        """Create the main content area."""
        # Create paned layout - operations list on left, details on right
        main_paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        
        # Create operations list (left side)
        self._create_operations_list(main_paned)
        
        # Create details area (right side)
        self._create_details_area(main_paned)
        
        self.pack_start(main_paned, True, True, 0)
    
    def _create_operations_list(self, parent: Gtk.Paned) -> None:
        """Create the operations list view."""
        list_frame = Gtk.Frame(label="Active Operations")
        
        # Create list store: ID, Name, Type, Status, Progress, Duration, Actions
        self.operations_store = Gtk.ListStore(
            str,    # Operation ID
            str,    # Name
            str,    # Type
            str,    # Status
            float,  # Progress (0-100)
            str,    # Duration
            str,    # Current Step
            str     # Resource Usage
        )
        
        # Create tree view
        self.operations_view = Gtk.TreeView(model=self.operations_store)
        self.operations_view.set_rules_hint(True)
        self.operations_view.get_selection().set_mode(Gtk.SelectionMode.MULTIPLE)
        
        # Create columns
        columns = [
            ("Name", 1, 150),         # Column 1: Name
            ("Type", 2, 120),         # Column 2: Type  
            ("Status", 3, 80),        # Column 3: Status
            ("Progress", 4, 100),     # Column 4: Progress
            ("Duration", 5, 80),      # Column 5: Duration
            ("Current Step", 6, 150), # Column 6: Current Step
            ("Resources", 7, 100)     # Column 7: Resources
        ]
        
        for title, col_id, width in columns:
            if col_id == 4:  # Progress column
                column = Gtk.TreeViewColumn(title)
                progress_renderer = Gtk.CellRendererProgress()
                column.pack_start(progress_renderer, True)
                column.add_attribute(progress_renderer, "value", col_id)
                column.set_resizable(True)
                column.set_min_width(width)
            else:
                column = Gtk.TreeViewColumn(title)
                renderer = Gtk.CellRendererText()
                column.pack_start(renderer, True)
                column.add_attribute(renderer, "text", col_id)
                column.set_resizable(True)
                column.set_min_width(width)
            
            self.operations_view.append_column(column)
        
        # Add to scrolled window
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroll.add(self.operations_view)
        
        list_frame.add(scroll)
        parent.pack1(list_frame, True, True)  # Resizable
    
    def _create_details_area(self, parent: Gtk.Paned) -> None:
        """Create the operation details area."""
        details_frame = Gtk.Frame(label="Operation Details & System Monitoring")
        
        # Create notebook for different detail views
        self.details_notebook = Gtk.Notebook()
        
        # Operation Details tab
        self._create_operation_details_tab()
        
        # System Resources tab
        self._create_system_resources_tab()
        
        # Operation Logs tab
        self._create_operation_logs_tab()
        
        # Performance Metrics tab
        self._create_performance_metrics_tab()
        
        # Operations Files tab
        self._create_operations_files_tab()
        
        # Results Analysis Dashboard tab
        self._create_results_analysis_tab()
        
        details_frame.add(self.details_notebook)
        parent.pack2(details_frame, False, False)  # Fixed size
    
    def _create_operation_details_tab(self) -> None:
        """Create the operation details tab."""
        tab_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        tab_box.set_margin_left(10)
        tab_box.set_margin_right(10)
        tab_box.set_margin_top(10)
        tab_box.set_margin_bottom(10)
        
        # Operation info frame
        info_frame = Gtk.Frame(label="Operation Information")
        info_grid = Gtk.Grid()
        info_grid.set_column_spacing(10)
        info_grid.set_row_spacing(5)
        info_grid.set_margin_left(10)
        info_grid.set_margin_right(10)
        info_grid.set_margin_top(5)
        info_grid.set_margin_bottom(5)
        
        # Create labels for operation details
        labels = [
            ("Name:", "operation_name_value"),
            ("Type:", "operation_type_value"),
            ("Status:", "operation_status_value"),
            ("Started:", "operation_start_time_value"),
            ("Duration:", "operation_duration_value"),
            ("Estimated Remaining:", "operation_eta_value"),
            ("Current Step:", "operation_step_value"),
            ("Progress:", "operation_progress_value")
        ]
        
        for row, (label_text, value_attr) in enumerate(labels):
            label = Gtk.Label(label_text)
            label.set_halign(Gtk.Align.END)
            label.get_style_context().add_class("dim-label")
            info_grid.attach(label, 0, row, 1, 1)
            
            value_label = Gtk.Label("No operation selected")
            value_label.set_halign(Gtk.Align.START)
            setattr(self, value_attr, value_label)
            info_grid.attach(value_label, 1, row, 1, 1)
        
        info_frame.add(info_grid)
        tab_box.pack_start(info_frame, False, False, 0)
        
        # Progress visualization frame
        progress_frame = Gtk.Frame(label="Progress Visualization")
        progress_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        progress_box.set_margin_left(10)
        progress_box.set_margin_right(10)
        progress_box.set_margin_top(5)
        progress_box.set_margin_bottom(5)
        
        # Overall progress bar
        self.overall_progress = Gtk.ProgressBar()
        self.overall_progress.set_show_text(True)
        self.overall_progress.set_text("0%")
        progress_box.pack_start(self.overall_progress, False, False, 0)
        
        # Step progress
        self.step_progress_label = Gtk.Label("Step: Not started")
        self.step_progress_label.set_halign(Gtk.Align.START)
        progress_box.pack_start(self.step_progress_label, False, False, 0)
        
        self.step_progress = Gtk.ProgressBar()
        self.step_progress.set_show_text(True)
        self.step_progress.set_text("0/0")
        progress_box.pack_start(self.step_progress, False, False, 0)
        
        progress_frame.add(progress_box)
        tab_box.pack_start(progress_frame, False, False, 0)
        
        # Control buttons frame
        controls_frame = Gtk.Frame(label="Operation Controls")
        controls_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        controls_box.set_margin_left(10)
        controls_box.set_margin_right(10)
        controls_box.set_margin_top(5)
        controls_box.set_margin_bottom(5)
        
        self.control_pause_button = Gtk.Button(label="Pause")
        self.control_pause_button.connect('clicked', self._on_pause_operation_clicked)
        controls_box.pack_start(self.control_pause_button, False, False, 0)
        
        self.control_stop_button = Gtk.Button(label="Stop")
        self.control_stop_button.connect('clicked', self._on_stop_operation_clicked)
        controls_box.pack_start(self.control_stop_button, False, False, 0)
        
        self.control_priority_button = Gtk.Button(label="Set Priority")
        self.control_priority_button.connect('clicked', self._on_set_priority_clicked)
        controls_box.pack_start(self.control_priority_button, False, False, 0)
        
        controls_frame.add(controls_box)
        tab_box.pack_start(controls_frame, False, False, 0)
        
        self.details_notebook.append_page(tab_box, Gtk.Label("Operation Details"))
    
    def _create_system_resources_tab(self) -> None:
        """Create the system resources monitoring tab."""
        tab_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        tab_box.set_margin_left(10)
        tab_box.set_margin_right(10)
        tab_box.set_margin_top(10)
        tab_box.set_margin_bottom(10)
        
        # CPU usage frame
        cpu_frame = Gtk.Frame(label="CPU Usage")
        cpu_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        cpu_box.set_margin_left(10)
        cpu_box.set_margin_right(10)
        cpu_box.set_margin_top(5)
        cpu_box.set_margin_bottom(5)
        
        self.cpu_usage_label = Gtk.Label("CPU: 0%")
        self.cpu_usage_label.set_halign(Gtk.Align.START)
        cpu_box.pack_start(self.cpu_usage_label, False, False, 0)
        
        self.cpu_usage_bar = Gtk.ProgressBar()
        self.cpu_usage_bar.set_show_text(True)
        cpu_box.pack_start(self.cpu_usage_bar, False, False, 0)
        
        cpu_frame.add(cpu_box)
        tab_box.pack_start(cpu_frame, False, False, 0)
        
        # Memory usage frame
        memory_frame = Gtk.Frame(label="Memory Usage")
        memory_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        memory_box.set_margin_left(10)
        memory_box.set_margin_right(10)
        memory_box.set_margin_top(5)
        memory_box.set_margin_bottom(5)
        
        self.memory_usage_label = Gtk.Label("Memory: 0 MB / 0 MB")
        self.memory_usage_label.set_halign(Gtk.Align.START)
        memory_box.pack_start(self.memory_usage_label, False, False, 0)
        
        self.memory_usage_bar = Gtk.ProgressBar()
        self.memory_usage_bar.set_show_text(True)
        memory_box.pack_start(self.memory_usage_bar, False, False, 0)
        
        memory_frame.add(memory_box)
        tab_box.pack_start(memory_frame, False, False, 0)
        
        # Disk usage frame
        disk_frame = Gtk.Frame(label="Disk Usage")
        disk_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        disk_box.set_margin_left(10)
        disk_box.set_margin_right(10)
        disk_box.set_margin_top(5)
        disk_box.set_margin_bottom(5)
        
        self.disk_usage_label = Gtk.Label("Disk: 0 MB free")
        self.disk_usage_label.set_halign(Gtk.Align.START)
        disk_box.pack_start(self.disk_usage_label, False, False, 0)
        
        self.disk_usage_bar = Gtk.ProgressBar()
        self.disk_usage_bar.set_show_text(True)
        disk_box.pack_start(self.disk_usage_bar, False, False, 0)
        
        disk_frame.add(disk_box)
        tab_box.pack_start(disk_frame, False, False, 0)
        
        # Network usage frame
        network_frame = Gtk.Frame(label="Network Activity")
        network_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        network_box.set_margin_left(10)
        network_box.set_margin_right(10)
        network_box.set_margin_top(5)
        network_box.set_margin_bottom(5)
        
        self.network_in_label = Gtk.Label("Download: 0 MB/s")
        self.network_in_label.set_halign(Gtk.Align.START)
        network_box.pack_start(self.network_in_label, False, False, 0)
        
        self.network_out_label = Gtk.Label("Upload: 0 MB/s")
        self.network_out_label.set_halign(Gtk.Align.START)
        network_box.pack_start(self.network_out_label, False, False, 0)
        
        network_frame.add(network_box)
        tab_box.pack_start(network_frame, False, False, 0)
        
        self.details_notebook.append_page(tab_box, Gtk.Label("System Resources"))
    
    def _create_operation_logs_tab(self) -> None:
        """Create the operation logs tab."""
        tab_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        tab_box.set_margin_left(10)
        tab_box.set_margin_right(10)
        tab_box.set_margin_top(10)
        tab_box.set_margin_bottom(10)
        
        # Log controls
        controls_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        # Auto-scroll toggle
        self.auto_scroll_check = Gtk.CheckButton(label="Auto-scroll")
        self.auto_scroll_check.set_active(True)
        controls_box.pack_start(self.auto_scroll_check, False, False, 0)
        
        # Clear logs button
        clear_logs_button = Gtk.Button(label="Clear Logs")
        clear_logs_button.connect('clicked', self._on_clear_logs_clicked)
        controls_box.pack_start(clear_logs_button, False, False, 0)
        
        # Export logs button
        export_logs_button = Gtk.Button(label="Export Logs")
        export_logs_button.connect('clicked', self._on_export_logs_clicked)
        controls_box.pack_start(export_logs_button, False, False, 0)
        
        tab_box.pack_start(controls_box, False, False, 0)
        
        # Log viewer
        log_scroll = Gtk.ScrolledWindow()
        log_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        
        self.log_buffer = Gtk.TextBuffer()
        self.log_view = Gtk.TextView(buffer=self.log_buffer)
        self.log_view.set_editable(False)
        self.log_view.set_cursor_visible(False)
        
        # Set monospace font for logs
        font_desc = Pango.FontDescription("monospace 9")
        self.log_view.modify_font(font_desc)
        
        log_scroll.add(self.log_view)
        tab_box.pack_start(log_scroll, True, True, 0)
        
        self.details_notebook.append_page(tab_box, Gtk.Label("Operation Logs"))
    
    def _create_performance_metrics_tab(self) -> None:
        """Create the performance metrics tab."""
        tab_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        tab_box.set_margin_left(10)
        tab_box.set_margin_right(10)
        tab_box.set_margin_top(10)
        tab_box.set_margin_bottom(10)
        
        # Metrics summary frame
        summary_frame = Gtk.Frame(label="Performance Summary")
        summary_grid = Gtk.Grid()
        summary_grid.set_column_spacing(10)
        summary_grid.set_row_spacing(5)
        summary_grid.set_margin_left(10)
        summary_grid.set_margin_right(10)
        summary_grid.set_margin_top(5)
        summary_grid.set_margin_bottom(5)
        
        # Performance metrics
        metrics = [
            ("Operations Completed:", "metrics_completed_value"),
            ("Operations Failed:", "metrics_failed_value"),
            ("Average Duration:", "metrics_avg_duration_value"),
            ("Total Runtime:", "metrics_total_runtime_value"),
            ("Success Rate:", "metrics_success_rate_value"),
            ("Resource Efficiency:", "metrics_efficiency_value")
        ]
        
        for row, (label_text, value_attr) in enumerate(metrics):
            label = Gtk.Label(label_text)
            label.set_halign(Gtk.Align.END)
            label.get_style_context().add_class("dim-label")
            summary_grid.attach(label, 0, row, 1, 1)
            
            value_label = Gtk.Label("0")
            value_label.set_halign(Gtk.Align.START)
            setattr(self, value_attr, value_label)
            summary_grid.attach(value_label, 1, row, 1, 1)
        
        summary_frame.add(summary_grid)
        tab_box.pack_start(summary_frame, False, False, 0)
        
        # Operation history frame
        history_frame = Gtk.Frame(label="Recent Operations History")
        
        # Create history list store
        self.history_store = Gtk.ListStore(str, str, str, str, str)  # Name, Type, Status, Duration, Completed
        
        history_view = Gtk.TreeView(model=self.history_store)
        
        # Create columns
        for i, title in enumerate(["Operation", "Type", "Status", "Duration", "Completed"]):
            column = Gtk.TreeViewColumn(title)
            renderer = Gtk.CellRendererText()
            column.pack_start(renderer, True)
            column.add_attribute(renderer, "text", i)
            column.set_resizable(True)
            history_view.append_column(column)
        
        history_scroll = Gtk.ScrolledWindow()
        history_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        history_scroll.add(history_view)
        history_frame.add(history_scroll)
        
        tab_box.pack_start(history_frame, True, True, 0)
        
        self.details_notebook.append_page(tab_box, Gtk.Label("Performance"))
    
    def _create_operations_files_tab(self) -> None:
        """Create the operations files browser tab."""
        tab_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        tab_box.set_margin_left(10)
        tab_box.set_margin_right(10)
        tab_box.set_margin_top(10)
        tab_box.set_margin_bottom(10)
        
        # Toolbar for file operations
        toolbar = Gtk.Toolbar()
        toolbar.set_style(Gtk.ToolbarStyle.BOTH_HORIZ)
        
        # Refresh button
        refresh_button = Gtk.ToolButton()
        refresh_button.set_icon_name("view-refresh")
        refresh_button.set_label("Refresh")
        refresh_button.set_tooltip_text("Scan Operations directory for new files and updated operation results")
        refresh_button.connect('clicked', self._on_refresh_files_clicked)
        toolbar.insert(refresh_button, -1)
        
        # Open folder button
        open_folder_button = Gtk.ToolButton()
        open_folder_button.set_icon_name("folder-open")
        open_folder_button.set_label("Open Folder")
        open_folder_button.set_tooltip_text("Open the Operations directory in your system's file manager")
        open_folder_button.connect('clicked', self._on_open_operations_folder_clicked)
        toolbar.insert(open_folder_button, -1)
        
        # Separator
        toolbar.insert(Gtk.SeparatorToolItem(), -1)
        
        # Delete operation button
        delete_button = Gtk.ToolButton()
        delete_button.set_icon_name("edit-delete")
        delete_button.set_label("Delete")
        delete_button.set_tooltip_text("Permanently delete the selected operation folder and all its contents")
        delete_button.connect('clicked', self._on_delete_operation_clicked)
        toolbar.insert(delete_button, -1)
        
        tab_box.pack_start(toolbar, False, False, 0)
        
        # Create paned layout - file tree on left, file details on right
        files_paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        
        # File tree (left side)
        tree_frame = Gtk.Frame(label="Operations Directory")
        tree_scrolled = Gtk.ScrolledWindow()
        tree_scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        tree_scrolled.set_size_request(200, 400)  # Reduced width to allow narrower windows
        
        # Create file tree store: Name, Path, Type, Size, Modified
        self.files_store = Gtk.TreeStore(str, str, str, str, str)
        
        # Create tree view
        self.files_view = Gtk.TreeView(model=self.files_store)
        self.files_view.set_rules_hint(True)
        self.files_view.get_selection().set_mode(Gtk.SelectionMode.SINGLE)
        self.files_view.get_selection().connect('changed', self._on_file_selection_changed)
        
        # Name column
        name_column = Gtk.TreeViewColumn("Name")
        name_renderer = Gtk.CellRendererText()
        name_column.pack_start(name_renderer, True)
        name_column.add_attribute(name_renderer, "text", 0)
        name_column.set_expand(True)
        self.files_view.append_column(name_column)
        
        # Size column
        size_column = Gtk.TreeViewColumn("Size")
        size_renderer = Gtk.CellRendererText()
        size_column.pack_start(size_renderer, False)
        size_column.add_attribute(size_renderer, "text", 3)
        size_column.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
        size_column.set_fixed_width(80)
        self.files_view.append_column(size_column)
        
        # Modified column
        modified_column = Gtk.TreeViewColumn("Modified")
        modified_renderer = Gtk.CellRendererText()
        modified_column.pack_start(modified_renderer, False)
        modified_column.add_attribute(modified_renderer, "text", 4)
        modified_column.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
        modified_column.set_fixed_width(120)
        self.files_view.append_column(modified_column)
        
        tree_scrolled.add(self.files_view)
        tree_frame.add(tree_scrolled)
        files_paned.pack1(tree_frame, True, False)
        
        # File details (right side)
        details_frame = Gtk.Frame(label="File Details")
        details_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        details_box.set_margin_left(10)
        details_box.set_margin_right(10)
        details_box.set_margin_top(5)
        details_box.set_margin_bottom(5)
        
        # File info
        self.file_info_label = Gtk.Label("Select a file to view details")
        self.file_info_label.set_halign(Gtk.Align.START)
        self.file_info_label.set_line_wrap(True)
        details_box.pack_start(self.file_info_label, False, False, 0)
        
        # File preview area
        preview_scrolled = Gtk.ScrolledWindow()
        preview_scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        preview_scrolled.set_size_request(200, 300)  # Reduced width to allow narrower windows
        
        self.file_preview = Gtk.TextView()
        self.file_preview.set_editable(False)
        self.file_preview.set_cursor_visible(False)
        self.file_preview.set_wrap_mode(Gtk.WrapMode.WORD)
        preview_scrolled.add(self.file_preview)
        details_box.pack_start(preview_scrolled, True, True, 0)
        
        details_frame.add(details_box)
        files_paned.pack2(details_frame, False, False)
        
        tab_box.pack_start(files_paned, True, True, 0)
        
        # Add tab to notebook
        self.details_notebook.append_page(tab_box, Gtk.Label("Files"))
        
        # Load initial file tree
        self._load_operations_files()
    
    def _create_results_analysis_tab(self) -> None:
        """Create the results analysis dashboard tab."""
        tab_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        tab_box.set_margin_left(10)
        tab_box.set_margin_right(10)
        tab_box.set_margin_top(10)
        tab_box.set_margin_bottom(10)
        
        # Create main scrolled window for the dashboard
        main_scroll = Gtk.ScrolledWindow()
        main_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        
        # Create main content box inside scroll
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        content_box.set_margin_left(10)
        content_box.set_margin_right(10)
        content_box.set_margin_top(10)
        content_box.set_margin_bottom(10)
        
        # =====================================================================
        # Operation Outcome Summary Section
        # =====================================================================
        outcome_frame = Gtk.Frame(label="📊 Operation Outcome Summary")
        outcome_grid = Gtk.Grid()
        outcome_grid.set_column_spacing(20)
        outcome_grid.set_row_spacing(10)
        outcome_grid.set_margin_left(15)
        outcome_grid.set_margin_right(15)
        outcome_grid.set_margin_top(10)
        outcome_grid.set_margin_bottom(10)
        
        # Success/Failure metrics with progress bars
        outcome_metrics = [
            ("Total Operations:", "results_total_ops", "0"),
            ("Successful:", "results_success_count", "0"),
            ("Failed:", "results_failed_count", "0"),
            ("Success Rate:", "results_success_rate", "0%"),
            ("Most Recent:", "results_last_operation", "None"),
            ("Avg Duration:", "results_avg_duration", "00:00:00")
        ]
        
        for row, (label_text, attr_name, default_value) in enumerate(outcome_metrics):
            # Label
            label = Gtk.Label(label_text)
            label.set_halign(Gtk.Align.END)
            label.get_style_context().add_class("dim-label")
            outcome_grid.attach(label, 0, row, 1, 1)
            
            # Value
            value_label = Gtk.Label(default_value)
            value_label.set_halign(Gtk.Align.START)
            setattr(self, attr_name, value_label)
            outcome_grid.attach(value_label, 1, row, 1, 1)
            
            # Add progress bar for success rate
            if attr_name == "results_success_rate":
                self.results_success_progress = Gtk.ProgressBar()
                self.results_success_progress.set_show_text(False)
                self.results_success_progress.set_size_request(100, -1)
                outcome_grid.attach(self.results_success_progress, 2, row, 1, 1)
        
        outcome_frame.add(outcome_grid)
        content_box.pack_start(outcome_frame, False, False, 0)
        
        # =====================================================================
        # Result File Analysis Section  
        # =====================================================================
        files_frame = Gtk.Frame(label="📁 Generated Result Files Analysis")
        files_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        files_box.set_margin_left(15)
        files_box.set_margin_right(15)
        files_box.set_margin_top(10)
        files_box.set_margin_bottom(10)
        
        # File statistics
        files_stats_grid = Gtk.Grid()
        files_stats_grid.set_column_spacing(20)
        files_stats_grid.set_row_spacing(5)
        
        file_metrics = [
            ("Microstructure Files (.img):", "results_img_files", "0"),
            ("Parameter Files (.pimg):", "results_pimg_files", "0"),
            ("Input Files Generated:", "results_input_files", "0"),
            ("Total Data Size:", "results_total_size", "0 MB"),
            ("Largest Operation:", "results_largest_op", "None"),
            ("Storage Used:", "results_storage_used", "0 MB")
        ]
        
        for row, (label_text, attr_name, default_value) in enumerate(file_metrics):
            label = Gtk.Label(label_text)
            label.set_halign(Gtk.Align.END)
            label.get_style_context().add_class("dim-label")
            files_stats_grid.attach(label, 0, row, 1, 1)
            
            value_label = Gtk.Label(default_value)
            value_label.set_halign(Gtk.Align.START)
            setattr(self, attr_name, value_label)
            files_stats_grid.attach(value_label, 1, row, 1, 1)
        
        files_box.pack_start(files_stats_grid, False, False, 0)
        files_frame.add(files_box)
        content_box.pack_start(files_frame, False, False, 0)
        
        # =====================================================================
        # Performance Trends Section
        # =====================================================================
        trends_frame = Gtk.Frame(label="📈 Performance Trends & Patterns")
        trends_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        trends_box.set_margin_left(15)
        trends_box.set_margin_right(15)
        trends_box.set_margin_top(10)
        trends_box.set_margin_bottom(10)
        
        # Performance metrics
        trends_grid = Gtk.Grid()
        trends_grid.set_column_spacing(20)
        trends_grid.set_row_spacing(5)
        
        trend_metrics = [
            ("Fastest Operation:", "results_fastest_op", "None"),
            ("Slowest Operation:", "results_slowest_op", "None"),
            ("Recent Trend:", "results_recent_trend", "No pattern"),
            ("Failure Pattern:", "results_failure_pattern", "No pattern"),
            ("Peak Performance Time:", "results_peak_time", "Unknown"),
            ("Resource Efficiency:", "results_efficiency", "0%")
        ]
        
        for row, (label_text, attr_name, default_value) in enumerate(trend_metrics):
            label = Gtk.Label(label_text)
            label.set_halign(Gtk.Align.END)
            label.get_style_context().add_class("dim-label")
            trends_grid.attach(label, 0, row, 1, 1)
            
            value_label = Gtk.Label(default_value)
            value_label.set_halign(Gtk.Align.START)
            setattr(self, attr_name, value_label)
            trends_grid.attach(value_label, 1, row, 1, 1)
        
        trends_box.pack_start(trends_grid, False, False, 0)
        trends_frame.add(trends_box)
        content_box.pack_start(trends_frame, False, False, 0)
        
        # =====================================================================
        # Error Analysis Section
        # =====================================================================
        errors_frame = Gtk.Frame(label="🔍 Error Analysis & Troubleshooting")
        errors_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        errors_box.set_margin_left(15)
        errors_box.set_margin_right(15)
        errors_box.set_margin_top(10)
        errors_box.set_margin_bottom(10)
        
        # Error patterns
        self.results_error_text = Gtk.TextView()
        self.results_error_text.set_editable(False)
        self.results_error_text.set_cursor_visible(False)
        self.results_error_text.set_wrap_mode(Gtk.WrapMode.WORD)
        
        error_scroll = Gtk.ScrolledWindow()
        error_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        error_scroll.set_size_request(-1, 150)
        error_scroll.add(self.results_error_text)
        
        errors_box.pack_start(error_scroll, True, True, 0)
        errors_frame.add(errors_box)
        content_box.pack_start(errors_frame, True, True, 0)
        
        # =====================================================================
        # Quality Assessment Section  
        # =====================================================================
        quality_frame = Gtk.Frame(label="✅ Quality Assessment & Validation")
        quality_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        quality_box.set_margin_left(15)
        quality_box.set_margin_right(15)
        quality_box.set_margin_top(10)
        quality_box.set_margin_bottom(10)
        
        # Quality metrics
        quality_grid = Gtk.Grid()
        quality_grid.set_column_spacing(20)
        quality_grid.set_row_spacing(5)
        
        quality_metrics = [
            ("Valid Results:", "results_valid_count", "0"),
            ("Invalid Results:", "results_invalid_count", "0"),
            ("Validation Rate:", "results_validation_rate", "0%"),
            ("File Integrity:", "results_file_integrity", "Unknown"),
            ("Data Consistency:", "results_data_consistency", "Unknown"),
            ("Overall Quality:", "results_overall_quality", "Unknown")
        ]
        
        for row, (label_text, attr_name, default_value) in enumerate(quality_metrics):
            label = Gtk.Label(label_text)
            label.set_halign(Gtk.Align.END)
            label.get_style_context().add_class("dim-label")
            quality_grid.attach(label, 0, row, 1, 1)
            
            value_label = Gtk.Label(default_value)
            value_label.set_halign(Gtk.Align.START)
            setattr(self, attr_name, value_label)
            quality_grid.attach(value_label, 1, row, 1, 1)
        
        quality_box.pack_start(quality_grid, False, False, 0)
        quality_frame.add(quality_box)
        content_box.pack_start(quality_frame, False, False, 0)
        
        # =====================================================================
        # Dashboard Controls
        # =====================================================================
        controls_frame = Gtk.Frame(label="🔧 Dashboard Controls")
        controls_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        controls_box.set_margin_left(15)
        controls_box.set_margin_right(15)
        controls_box.set_margin_top(10)
        controls_box.set_margin_bottom(10)
        
        # Refresh analysis button
        refresh_analysis_btn = Gtk.Button(label="🔄 Refresh Analysis")
        refresh_analysis_btn.set_tooltip_text("Recalculate operation success rates, performance metrics, and quality assessments")
        refresh_analysis_btn.connect('clicked', self._on_refresh_analysis_clicked)
        controls_box.pack_start(refresh_analysis_btn, False, False, 0)
        
        # Export report button
        export_report_btn = Gtk.Button(label="📄 Export Report") 
        export_report_btn.set_tooltip_text("Generate and save a comprehensive operations analysis report to file")
        export_report_btn.connect('clicked', self._on_export_report_clicked)
        controls_box.pack_start(export_report_btn, False, False, 0)
        
        # Cleanup old results button
        cleanup_btn = Gtk.Button(label="🧹 Cleanup Old Results")
        cleanup_btn.set_tooltip_text("Archive or delete old operation files to free up disk space (with confirmation)")
        cleanup_btn.connect('clicked', self._on_cleanup_results_clicked)
        controls_box.pack_start(cleanup_btn, False, False, 0)
        
        # Validation check button
        validate_btn = Gtk.Button(label="🔍 Validate Results") 
        validate_btn.set_tooltip_text("Verify integrity and completeness of all operation result files")
        validate_btn.connect('clicked', self._on_validate_results_clicked)
        controls_box.pack_start(validate_btn, False, False, 0)
        
        controls_frame.add(controls_box)
        content_box.pack_start(controls_frame, False, False, 0)
        
        # Add content to scroll window
        main_scroll.add(content_box)
        tab_box.pack_start(main_scroll, True, True, 0)
        
        # Add tab to notebook
        self.details_notebook.append_page(tab_box, Gtk.Label("📊 Results Analysis"))
        
        # Initial analysis refresh
        self._refresh_results_analysis()
    
    def _create_status_bar(self) -> None:
        """Create the status bar."""
        self.status_bar = Gtk.Statusbar()
        self.status_context = self.status_bar.get_context_id("main")
        self.status_bar.push(self.status_context, "Monitoring active - 0 operations")
        self.pack_start(self.status_bar, False, False, 0)
    
    def _connect_signals(self) -> None:
        """Connect widget signals."""
        # Operations list selection
        if self.operations_view:
            selection = self.operations_view.get_selection()
            selection.connect('changed', self._on_operation_selection_changed)
    
    def _start_monitoring(self) -> None:
        """Start the monitoring thread."""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitor_thread.start()
            self.logger.info("Monitoring started")
    
    def _stop_monitoring(self) -> None:
        """Stop the monitoring thread."""
        if self.monitoring_active:
            self.monitoring_active = False
            if self.monitor_thread:
                self.monitor_thread.join(timeout=2.0)
            self.logger.info("Monitoring stopped")
    
    def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self.monitoring_active:
            try:
                # Update system resources
                self._update_system_resources()
                
                # Update operations
                self._update_operations()
                
                # Save operations periodically
                self._save_operations_periodically()
                
                # Throttle UI updates to reduce blinking
                current_time = time.time()
                if current_time - self.last_ui_update >= self.ui_update_throttle:
                    self.last_ui_update = current_time
                    GLib.idle_add(self._update_ui)
                
                # Sleep until next update
                time.sleep(self.update_interval)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(1.0)  # Brief pause on error
    
    def _update_system_resources(self) -> None:
        """Update system resource information."""
        try:
            import psutil
            
            # CPU usage
            self.system_resources.cpu_usage = psutil.cpu_percent(interval=None)
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.system_resources.memory_usage = memory.used / (1024 * 1024)  # MB
            self.system_resources.memory_total = memory.total / (1024 * 1024)  # MB
            
            # Disk usage
            disk = psutil.disk_usage('/')
            self.system_resources.disk_usage = disk.used / (1024 * 1024)  # MB
            self.system_resources.disk_free = disk.free / (1024 * 1024)  # MB
            
            # Network (simplified - would need more sophisticated tracking)
            self.system_resources.network_in = 0.0
            self.system_resources.network_out = 0.0
            
            self.system_resources.timestamp = datetime.now()
            
        except ImportError:
            # psutil not available, use dummy values
            self.system_resources.cpu_usage = 0.0
            self.system_resources.memory_usage = 0.0
            self.system_resources.memory_total = 1024.0
        except Exception as e:
            self.logger.warning(f"Failed to update system resources: {e}")
    
    def _update_operations(self) -> None:
        """Update operation status information by checking real processes."""
        current_time = datetime.now()
        
        # Periodically refresh operations from database 
        # More frequent updates if we have running operations, less frequent otherwise
        if not hasattr(self, '_last_db_refresh'):
            self._last_db_refresh = current_time
        
        # Check if we have any running operations
        has_running_ops = any(op.status in ['running', 'pending'] for op in self.operations.values())
        refresh_interval = 10 if has_running_ops else 30  # 10 seconds if running ops, 30 seconds otherwise
        
        time_since_refresh = (current_time - self._last_db_refresh).total_seconds()
        if time_since_refresh >= refresh_interval:
            self._refresh_operations_from_database()
            self._last_db_refresh = current_time
        
        # Update existing operations based on actual process status
        for operation in self.operations.values():
            # Skip process monitoring for database-sourced operations (they don't have process info)
            if hasattr(operation, 'metadata') and operation.metadata.get('source') == 'database':
                continue
                
            if operation.status in [OperationStatus.RUNNING, OperationStatus.PAUSED]:
                # Check if process is still running
                if not operation.is_process_running():
                    # Process has ended, determine if it completed successfully
                    self.logger.info(f"Process {operation.id} ({operation.name}) has ended")
                    
                    if operation.process and operation.process.returncode is not None:
                        return_code = operation.process.returncode
                        self.logger.info(f"Process {operation.id} exit code: {return_code}")
                        
                        if return_code == 0:
                            operation.status = OperationStatus.COMPLETED
                            operation.progress = 1.0
                            operation.current_step = "Process completed successfully"
                            self.logger.info(f"Process {operation.id} marked as COMPLETED")
                        else:
                            operation.status = OperationStatus.FAILED
                            operation.error_message = f"Process exited with code {return_code}"
                            operation.current_step = "Process failed"
                            self.logger.warning(f"Process {operation.id} marked as FAILED with code {return_code}")
                    else:
                        # Process ended without proper exit code tracking
                        self.logger.info(f"Process {operation.id} ended without return code - marking as completed")
                        operation.status = OperationStatus.COMPLETED
                        operation.progress = 1.0
                        operation.current_step = "Process completed"
                    
                    operation.end_time = current_time
                    operation.completed_steps = operation.total_steps
                    
                    # Close output file handles
                    operation.close_output_files()
                    
                    self._save_operations_to_file()
                    
                elif operation.status == OperationStatus.RUNNING:
                    # Update process resource usage for running operations
                    process_info = operation.get_process_info()
                    if process_info:
                        operation.cpu_usage = process_info['cpu_percent']
                        operation.memory_usage = process_info['memory_mb']
                    
                    # Update progress based on elapsed time (time-based estimation)
                    if operation.start_time and operation.estimated_duration:
                        elapsed = current_time - operation.start_time
                        # Progress based on estimated duration, capped at 95% until completion
                        time_progress = min(0.95, elapsed.total_seconds() / operation.estimated_duration.total_seconds())
                        operation.progress = max(operation.progress, time_progress)
                        
                        # Update step-based progress and current step description
                        if time_progress < 0.15:
                            step_desc = "Initializing simulation"
                            operation.completed_steps = 0
                        elif time_progress < 0.35:
                            step_desc = "Parsing input and setting up geometry"
                            operation.completed_steps = 1
                        elif time_progress < 0.85:
                            step_desc = "Generating 3D microstructure"
                            operation.completed_steps = 2
                        else:
                            step_desc = "Finalizing output files"
                            operation.completed_steps = 3
                            
                        # Combine step description with resource usage
                        if process_info:
                            operation.current_step = f"{step_desc} (CPU: {operation.cpu_usage:.1f}%, MEM: {operation.memory_usage:.0f}MB)"
                        else:
                            operation.current_step = f"{step_desc}..."
                            
                    elif operation.start_time:
                        # If no estimated duration, use a simple time-based progress (slower)
                        elapsed = current_time - operation.start_time
                        # Assume most operations take around 5 minutes, progress more slowly
                        time_progress = min(0.90, elapsed.total_seconds() / (5 * 60))
                        operation.progress = max(operation.progress, time_progress)
                        
                        # Simple step progression
                        if time_progress < 0.25:
                            step_desc = "Processing"
                            operation.completed_steps = 1
                        elif time_progress < 0.75:
                            step_desc = "Generating microstructure"
                            operation.completed_steps = 2
                        else:
                            step_desc = "Completing"
                            operation.completed_steps = 3
                            
                        # Combine step description with resource usage
                        if process_info:
                            operation.current_step = f"{step_desc} (CPU: {operation.cpu_usage:.1f}%, MEM: {operation.memory_usage:.0f}MB)"
                        else:
                            operation.current_step = f"{step_desc}..."
    
    def _update_ui(self) -> None:
        """Update the UI with current data."""
        try:
            # Update operations list
            self._update_operations_list()
            
            # Update button sensitivity based on current operations
            self._update_button_sensitivity()
            
            # Update system resources display
            self._update_system_resources_display()
            
            # Update performance metrics
            self._update_performance_metrics()
            
            # Update status bar
            active_ops = len([op for op in self.operations.values() 
                            if op.status in [OperationStatus.RUNNING, OperationStatus.PENDING]])
            self.status_bar.pop(self.status_context)
            self.status_bar.push(self.status_context, 
                               f"Monitoring active - {active_ops} active operations")
            
        except Exception as e:
            self.logger.error(f"Error updating UI: {e}")
    
    def _get_meaningful_operation_name(self, operation: Operation) -> str:
        """Extract meaningful operation name from metadata."""
        # Check if metadata contains output_dir with mix name
        if hasattr(operation, 'metadata') and isinstance(operation.metadata, dict):
            output_dir = operation.metadata.get('output_dir', '')
            if output_dir:
                # Extract mix name from path like "/Operations/NormalPaste10/"
                path_parts = Path(output_dir).parts
                if len(path_parts) >= 2 and path_parts[-2] == 'Operations':
                    mix_name = path_parts[-1]
                    if mix_name:
                        return f"{mix_name} Microstructure"
                elif len(path_parts) >= 1:
                    # Just take the last directory name
                    mix_name = path_parts[-1]
                    if mix_name and mix_name != 'Operations':
                        return f"{mix_name} Microstructure"
        
        # Fallback to original name
        return operation.name

    def _update_operations_list(self) -> None:
        """Update the operations list view efficiently without clearing."""
        if not self.operations_store:
            return
        
        # Build current operation data
        current_ops = {}
        for operation in self.operations.values():
            duration_str = ""
            if operation.duration:
                total_seconds = int(operation.duration.total_seconds())
                hours, remainder = divmod(total_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            
            resource_str = f"CPU: {operation.cpu_usage:.1f}% MEM: {operation.memory_usage:.0f}MB"
            
            # Get meaningful operation name from metadata
            meaningful_name = self._get_meaningful_operation_name(operation)
            
            current_ops[operation.id] = [
                operation.id,                                                    # Column 0: ID
                meaningful_name,                                                 # Column 1: Name  
                operation.operation_type.value.replace('_', ' ').title(),      # Column 2: Type
                operation.status.value.title(),                                # Column 3: Status
                operation.progress_percentage,                                  # Column 4: Progress
                duration_str,                                                   # Column 5: Duration
                operation.current_step,                                         # Column 6: Current Step
                resource_str                                                    # Column 7: Resources
            ]
        
        # Update existing rows and track which operations are in the store
        store_ops = set()
        tree_iter = self.operations_store.get_iter_first()
        
        while tree_iter:
            operation_id = self.operations_store.get_value(tree_iter, 0)
            store_ops.add(operation_id)
            
            if operation_id in current_ops:
                # Update existing row if values changed
                current_data = current_ops[operation_id]
                needs_update = False
                
                for col_idx in range(len(current_data)):
                    store_value = self.operations_store.get_value(tree_iter, col_idx)
                    if store_value != current_data[col_idx]:
                        needs_update = True
                        break
                
                if needs_update:
                    for col_idx, value in enumerate(current_data):
                        self.operations_store.set_value(tree_iter, col_idx, value)
                
                # Remove from current_ops since it's been processed
                del current_ops[operation_id]
            else:
                # Operation no longer exists, mark for removal
                next_iter = self.operations_store.iter_next(tree_iter)
                self.operations_store.remove(tree_iter)
                tree_iter = next_iter
                continue
            
            tree_iter = self.operations_store.iter_next(tree_iter)
        
        # Add new operations that weren't in the store
        for operation_data in current_ops.values():
            self.operations_store.append(operation_data)
    
    def _update_system_resources_display(self) -> None:
        """Update system resources display."""
        resources = self.system_resources
        
        # CPU
        self.cpu_usage_label.set_text(f"CPU: {resources.cpu_usage:.1f}%")
        self.cpu_usage_bar.set_fraction(resources.cpu_usage / 100.0)
        self.cpu_usage_bar.set_text(f"{resources.cpu_usage:.1f}%")
        
        # Memory
        if resources.memory_total > 0:
            memory_percent = (resources.memory_usage / resources.memory_total) * 100
            self.memory_usage_label.set_text(
                f"Memory: {resources.memory_usage:.0f} MB / {resources.memory_total:.0f} MB"
            )
            self.memory_usage_bar.set_fraction(memory_percent / 100.0)
            self.memory_usage_bar.set_text(f"{memory_percent:.1f}%")
        
        # Disk
        self.disk_usage_label.set_text(f"Disk: {resources.disk_free:.0f} MB free")
        if resources.disk_usage + resources.disk_free > 0:
            disk_percent = resources.disk_usage / (resources.disk_usage + resources.disk_free) * 100
            self.disk_usage_bar.set_fraction(disk_percent / 100.0)
            self.disk_usage_bar.set_text(f"{disk_percent:.1f}%")
        
        # Network
        self.network_in_label.set_text(f"Download: {resources.network_in:.2f} MB/s")
        self.network_out_label.set_text(f"Upload: {resources.network_out:.2f} MB/s")
    
    def _update_performance_metrics(self) -> None:
        """Update performance metrics display."""
        # Calculate metrics from operations
        total_ops = len(self.operations)
        completed_ops = len([op for op in self.operations.values() 
                           if op.status == OperationStatus.COMPLETED])
        failed_ops = len([op for op in self.operations.values() 
                        if op.status == OperationStatus.FAILED])
        
        # Calculate success rate
        success_rate = 0.0
        if total_ops > 0:
            success_rate = (completed_ops / total_ops) * 100
        
        # Calculate average duration for completed operations
        completed_durations = [op.duration for op in self.operations.values() 
                             if op.duration and op.status in [OperationStatus.COMPLETED, OperationStatus.FAILED]]
        
        avg_duration_str = "00:00:00"
        total_runtime_str = "00:00:00"
        
        if completed_durations:
            avg_duration = sum(completed_durations, timedelta()) / len(completed_durations)
            total_seconds = int(avg_duration.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            avg_duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            
            # Total runtime
            total_runtime = sum(completed_durations, timedelta())
            total_seconds = int(total_runtime.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            total_runtime_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
        # Calculate resource efficiency (simplified metric)
        efficiency = 0.0
        if completed_ops > 0:
            # Base efficiency on completion rate and average resource usage
            avg_cpu = sum(op.cpu_usage for op in self.operations.values() if op.cpu_usage > 0) / max(1, len([op for op in self.operations.values() if op.cpu_usage > 0]))
            efficiency = min(100.0, success_rate * (avg_cpu / 100.0) if avg_cpu > 0 else success_rate)
        
        # Update metric labels
        self.metrics_completed_value.set_text(str(completed_ops))
        self.metrics_failed_value.set_text(str(failed_ops))
        self.metrics_avg_duration_value.set_text(avg_duration_str)
        self.metrics_total_runtime_value.set_text(total_runtime_str)
        self.metrics_success_rate_value.set_text(f"{success_rate:.1f}%")
        self.metrics_efficiency_value.set_text(f"{efficiency:.1f}%")
        
        # Update operation history
        self._update_operation_history()
    
    def _update_operation_history(self) -> None:
        """Update the operation history list."""
        # Clear existing history
        self.history_store.clear()
        
        # Get completed and failed operations, sorted by end time
        finished_ops = [op for op in self.operations.values() 
                       if op.status in [OperationStatus.COMPLETED, OperationStatus.FAILED, OperationStatus.CANCELLED]]
        
        # Sort by end time (most recent first)
        finished_ops.sort(key=lambda op: op.end_time or datetime.min, reverse=True)
        
        # Add up to 20 most recent operations to history
        for operation in finished_ops[:20]:
            duration_str = "00:00:00"
            if operation.duration:
                total_seconds = int(operation.duration.total_seconds())
                hours, remainder = divmod(total_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            
            completed_str = "Never"
            if operation.end_time:
                completed_str = operation.end_time.strftime("%Y-%m-%d %H:%M:%S")
            
            self.history_store.append([
                operation.name,
                operation.operation_type.value.replace('_', ' ').title(),
                operation.status.value.title(),
                duration_str,
                completed_str
            ])
    
    # Event handlers
    
    def _on_operation_selection_changed(self, selection: Gtk.TreeSelection) -> None:
        """Handle operation selection change."""
        selected_operations = self._get_selected_operations()
        
        # Update button sensitivity based on new selection
        self._update_button_sensitivity()
        
        if len(selected_operations) == 1:
            # Single selection - show details for that operation
            self._update_operation_details(selected_operations[0])
        elif len(selected_operations) > 1:
            # Multiple selection - show summary information
            self._update_multiple_operation_details(selected_operations)
        else:
            # No selection - clear details
            self._clear_operation_details()
    
    def _update_operation_details(self, operation: Operation) -> None:
        """Update operation details display."""
        self.operation_name_value.set_text(operation.name)
        self.operation_type_value.set_text(operation.operation_type.value.replace('_', ' ').title())
        self.operation_status_value.set_text(operation.status.value.title())
        
        if operation.start_time:
            self.operation_start_time_value.set_text(operation.start_time.strftime("%Y-%m-%d %H:%M:%S"))
        else:
            self.operation_start_time_value.set_text("Not started")
        
        if operation.duration:
            self.operation_duration_value.set_text(str(operation.duration).split('.')[0])
        else:
            self.operation_duration_value.set_text("00:00:00")
        
        if operation.estimated_time_remaining:
            self.operation_eta_value.set_text(str(operation.estimated_time_remaining).split('.')[0])
        else:
            self.operation_eta_value.set_text("Unknown")
        
        self.operation_step_value.set_text(operation.current_step or "Not started")
        self.operation_progress_value.set_text(f"{operation.progress_percentage:.1f}%")
        
        # Update progress bars
        self.overall_progress.set_fraction(operation.progress)
        self.overall_progress.set_text(f"{operation.progress_percentage:.1f}%")
        
        if operation.total_steps > 0:
            step_fraction = operation.completed_steps / operation.total_steps
            self.step_progress.set_fraction(step_fraction)
            self.step_progress.set_text(f"{operation.completed_steps}/{operation.total_steps}")
        else:
            self.step_progress.set_fraction(0.0)
            self.step_progress.set_text("0/0")
    
    def _update_multiple_operation_details(self, operations: List[Operation]) -> None:
        """Update operation details display for multiple selected operations."""
        count = len(operations)
        
        # Show summary information
        self.operation_name_value.set_text(f"{count} operations selected")
        
        # Count by type
        type_counts = {}
        status_counts = {}
        for op in operations:
            op_type = op.operation_type.value.replace('_', ' ').title()
            type_counts[op_type] = type_counts.get(op_type, 0) + 1
            
            status = op.status.value.title()
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Show type summary
        type_summary = ", ".join(f"{count}x {type_name}" for type_name, count in type_counts.items())
        self.operation_type_value.set_text(type_summary)
        
        # Show status summary  
        status_summary = ", ".join(f"{count}x {status}" for status, count in status_counts.items())
        self.operation_status_value.set_text(status_summary)
        
        # Show average progress for running operations
        running_ops = [op for op in operations if op.status == OperationStatus.RUNNING]
        if running_ops:
            avg_progress = sum(op.progress for op in running_ops) / len(running_ops)
            self.overall_progress.set_fraction(avg_progress)
            self.overall_progress.set_text(f"Avg: {avg_progress * 100:.1f}%")
        else:
            self.overall_progress.set_fraction(0.0)
            self.overall_progress.set_text("N/A")
        
        # Clear step progress (not meaningful for multiple operations)
        self.step_progress.set_fraction(0.0)
        self.step_progress.set_text("Multiple")
        
        # Clear time fields
        self.operation_start_time_value.set_text("Various")
        self.operation_duration_value.set_text("Various")
        self.operation_eta_value.set_text("Various")
    
    def _clear_operation_details(self) -> None:
        """Clear operation details display when no operations are selected."""
        self.operation_name_value.set_text("No operation selected")
        self.operation_type_value.set_text("-")
        self.operation_status_value.set_text("-")
        self.operation_start_time_value.set_text("-")
        self.operation_duration_value.set_text("-")
        self.operation_eta_value.set_text("-")
        
        # Clear progress bars
        self.overall_progress.set_fraction(0.0)
        self.overall_progress.set_text("0%")
        self.step_progress.set_fraction(0.0)
        self.step_progress.set_text("0/0")
    
    def _on_start_operation_clicked(self, button: Gtk.Button) -> None:
        """Handle start operation button click."""
        # Show operation selection dialog
        self._show_start_operation_dialog()
    
    def _on_stop_operation_clicked(self, button: Gtk.Button) -> None:
        """Handle stop operation button click."""
        selected_operation = self._get_selected_operation()
        if selected_operation:
            self._stop_operation(selected_operation.id)
    
    def _on_pause_operation_clicked(self, button: Gtk.Button) -> None:
        """Handle pause operation button click."""
        selected_operation = self._get_selected_operation()
        if selected_operation:
            self._pause_operation(selected_operation.id)
    
    def _on_clear_completed_clicked(self, button: Gtk.Button) -> None:
        """Handle clear completed operations button click."""
        completed_ids = [
            op_id for op_id, op in self.operations.items()
            if op.status in [OperationStatus.COMPLETED, OperationStatus.FAILED, OperationStatus.CANCELLED]
        ]
        
        for op_id in completed_ids:
            del self.operations[op_id]
        
        self._update_operations_list()
    
    def _on_delete_selected_operation_clicked(self, button: Gtk.Button) -> None:
        """Handle delete selected operation(s) button click."""
        selected_operations = self._get_selected_operations()
        if not selected_operations:
            self._update_status("No operations selected for deletion")
            return
        
        # Check for running operations
        running_operations = [op for op in selected_operations if op.status == OperationStatus.RUNNING]
        if running_operations:
            running_names = [self._get_meaningful_operation_name(op) for op in running_operations]
            self._update_status(f"Cannot delete running operation(s): {', '.join(running_names)}. Stop them first.")
            return
        
        # Prepare confirmation dialog
        operation_count = len(selected_operations)
        if operation_count == 1:
            # Single operation - use existing detailed message
            meaningful_name = self._get_meaningful_operation_name(selected_operations[0])
            dialog_title = "Delete Operation?"
            dialog_text = f"Are you sure you want to delete the operation '{meaningful_name}'?"
        else:
            # Multiple operations - use bulk message
            operation_names = [self._get_meaningful_operation_name(op) for op in selected_operations]
            dialog_title = f"Delete {operation_count} Operations?"
            dialog_text = f"Are you sure you want to delete {operation_count} operations?\n\nOperations to delete:\n" + "\n".join(f"• {name}" for name in operation_names)
        
        # Show confirmation dialog
        dialog = Gtk.MessageDialog(
            transient_for=self.main_window,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.YES_NO,
            text=dialog_title
        )
        dialog.format_secondary_text(
            f"{dialog_text}\n\n"
            "This will permanently delete:\n"
            "• Operation(s) from database\n"
            "• Associated folder(s) and all files\n"
            "• Input files\n"
            "• Output files (.img, .pimg)\n"
            "• Log files\n"
            "• Correlation files\n\n"
            "This action cannot be undone."
        )
        
        response = dialog.run()
        dialog.destroy()
        
        if response == Gtk.ResponseType.YES:
            deleted_count = 0
            failed_count = 0
            
            for operation in selected_operations:
                try:
                    # Delete from operations dictionary
                    operation_id = operation.id
                    
                    # Get the operation folder path from metadata
                    output_dir = None
                    if hasattr(operation, 'metadata') and isinstance(operation.metadata, dict):
                        # Check both output_dir and output_directory keys
                        output_dir = operation.metadata.get('output_dir') or operation.metadata.get('output_directory', '')
                        operation_source = operation.metadata.get('source', '')
                        self.logger.info(f"DEBUG: Operation {operation.name} metadata: {operation.metadata}")
                        self.logger.info(f"DEBUG: output_dir={output_dir}, operation_source={operation_source}")
                    else:
                        operation_source = ''
                        self.logger.info(f"DEBUG: Operation {operation.name} has no metadata")
                    
                    # For database operations (hydration simulations), construct the folder path if not already set
                    if operation_source == 'database' and not output_dir:
                        # Operations folder is typically Operations/{operation_name}
                        # From panels/operations_monitoring_panel.py: parent = windows, parent = app, parent = src, parent = vcctl-gtk
                        project_root = Path(__file__).parent.parent.parent.parent.parent
                        operations_dir = project_root / "Operations"
                        potential_folder = operations_dir / operation.name
                        if potential_folder.exists():
                            output_dir = str(potential_folder)
                            self.logger.info(f"Found operation folder for {operation.name}: {output_dir}")
                    
                    # For database operations, also check if output_directory gives us a relative path to make absolute
                    if operation_source == 'database' and output_dir and not Path(output_dir).is_absolute():
                        # From panels/operations_monitoring_panel.py: parent = windows, parent = app, parent = src, parent = vcctl-gtk
                        project_root = Path(__file__).parent.parent.parent.parent.parent
                        output_dir = str(project_root / output_dir)
                        self.logger.info(f"Made absolute path for {operation.name}: {output_dir}")
                    
                    # Delete from database if it's a database-sourced operation (like hydration simulations)
                    if operation_source == 'database':
                        try:
                            operation_service = self.service_container.operation_service
                            operation_service.delete(operation.name)
                            self.logger.info(f"Deleted operation from database: {operation.name}")
                        except Exception as e:
                            self.logger.warning(f"Failed to delete operation from database: {operation.name}: {e}")
                    
                    # Delete the operation from memory
                    if operation_id in self.operations:
                        del self.operations[operation_id]
                    
                    # Delete the associated folder if it exists
                    if output_dir:
                        folder_path = Path(output_dir)
                        self.logger.info(f"DEBUG: Attempting to delete folder: {output_dir}")
                        self.logger.info(f"DEBUG: Folder exists: {folder_path.exists()}")
                        if folder_path.exists():
                            try:
                                import shutil
                                shutil.rmtree(output_dir)
                                self.logger.info(f"Successfully deleted operation folder: {output_dir}")
                            except Exception as delete_error:
                                self.logger.error(f"Failed to delete folder {output_dir}: {delete_error}")
                        else:
                            self.logger.warning(f"Operation folder not found: {output_dir}")
                    else:
                        self.logger.warning(f"No output directory found for operation: {operation.name}")
                    
                    deleted_count += 1
                    
                except Exception as e:
                    failed_count += 1
                    meaningful_name = self._get_meaningful_operation_name(operation)
                    self.logger.error(f"Error deleting operation '{meaningful_name}': {e}")
            
            # Save updated operations to file
            self._save_operations_to_file()
            
            # Refresh the UI
            self._update_operations_list()
            self._load_operations_files()  # Refresh file browser
            
            # Update status with results
            if failed_count == 0:
                if deleted_count == 1:
                    self._update_status(f"Operation deleted successfully")
                else:
                    self._update_status(f"{deleted_count} operations deleted successfully")
            else:
                self._update_status(f"{deleted_count} operations deleted, {failed_count} failed. Check logs for details.")
    
    def _on_refresh_clicked(self, button: Gtk.Button) -> None:
        """Handle refresh button click."""
        self._update_status("Refreshing operations and checking process status...")
        
        # Force a thorough update of all operations
        self._force_cleanup_stale_operations()
        
        # RELOAD OPERATIONS FROM ALL SOURCES (including filesystem scan)
        self.logger.info("=== REFRESH: Reloading operations from all sources ===")
        self._load_operations_from_file()
        
        self._update_operations()
        self._update_ui()
        
        # Count active operations for status feedback
        active_count = sum(1 for op in self.operations.values() 
                          if op.status in [OperationStatus.RUNNING, OperationStatus.PAUSED])
        
        self._update_status(f"Refresh complete. {active_count} active operations.")
    
    def _force_cleanup_stale_operations(self) -> None:
        """Force cleanup of stale operations by thoroughly checking process status."""
        self.logger.info("=== Starting force cleanup of stale operations ===")
        current_time = datetime.now()
        cleaned_count = 0
        
        for operation in list(self.operations.values()):
            # Skip cleanup for database-sourced operations (they don't have process info)
            if hasattr(operation, 'metadata') and operation.metadata.get('source') == 'database':
                continue
                
            # Check running/paused operations for stale processes
            if operation.status in [OperationStatus.RUNNING, OperationStatus.PAUSED]:
                self.logger.info(f"Checking running operation {operation.id}: {operation.name}")
                
                # Multiple checks to ensure process is truly dead
                is_running = False
                
                # ... (existing process check logic follows)
            
            # Also check failed operations that might have actually succeeded
            elif operation.status == OperationStatus.FAILED:
                self.logger.info(f"Checking failed operation {operation.id}: {operation.name}")
                
                # Verify if this "failed" operation actually completed successfully
                if self._verify_operation_completion_by_files(operation):
                    self.logger.info(f"  - Operation {operation.id} has success indicators - correcting status")
                    operation.status = OperationStatus.COMPLETED
                    operation.progress = 1.0
                    operation.current_step = "Process completed successfully (corrected)"
                    operation.error_message = None
                    if not operation.end_time:
                        operation.end_time = current_time
                    operation.completed_steps = operation.total_steps
                    self._add_log_entry(f"Corrected falsely failed operation: {operation.name}")
                    cleaned_count += 1
                else:
                    self.logger.info(f"  - Operation {operation.id} genuinely failed")
        
        # Continue with existing running/paused operation checks
        for operation in list(self.operations.values()):
            if operation.status in [OperationStatus.RUNNING, OperationStatus.PAUSED]:
                self.logger.info(f"Checking operation {operation.id}: {operation.name}")
                
                # Multiple checks to ensure process is truly dead
                is_running = False
                
                # Check 1: subprocess.Popen object
                if operation.process:
                    try:
                        return_code = operation.process.poll()
                        if return_code is None:
                            is_running = True
                            self.logger.info(f"  - Process object shows running (poll() returned None)")
                        else:
                            self.logger.info(f"  - Process object shows finished (return code: {return_code})")
                    except Exception as e:
                        self.logger.warning(f"  - Error checking process object: {e}")
                
                # Check 2: PID with psutil
                if operation.pid and not is_running:
                    try:
                        process = psutil.Process(operation.pid)
                        if process.is_running():
                            is_running = True
                            self.logger.info(f"  - PID {operation.pid} shows running via psutil")
                        else:
                            self.logger.info(f"  - PID {operation.pid} shows not running via psutil")
                    except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                        self.logger.info(f"  - PID {operation.pid} not found: {e}")
                
                # Check 3: System call (last resort)
                if operation.pid and not is_running:
                    try:
                        os.kill(operation.pid, 0)  # Signal 0 just checks if process exists
                        is_running = True
                        self.logger.info(f"  - PID {operation.pid} exists via os.kill(0)")
                    except (OSError, ProcessLookupError):
                        self.logger.info(f"  - PID {operation.pid} does not exist via os.kill(0)")
                
                # If process is definitely not running, mark as completed/failed
                if not is_running:
                    self.logger.info(f"  - Operation {operation.id} marked as stale - cleaning up")
                    
                    # Determine final status based on available information
                    if operation.process and hasattr(operation.process, 'returncode') and operation.process.returncode is not None:
                        if operation.process.returncode == 0:
                            operation.status = OperationStatus.COMPLETED
                            operation.progress = 1.0
                            operation.current_step = "Process completed successfully (cleanup)"
                        else:
                            operation.status = OperationStatus.FAILED
                            operation.error_message = f"Process exited with code {operation.process.returncode} (cleanup)"
                            operation.current_step = "Process failed (cleanup)"
                    else:
                        # Default to completed if we can't determine exit status
                        operation.status = OperationStatus.COMPLETED
                        operation.progress = 1.0
                        operation.current_step = "Process completed (cleanup - status unknown)"
                    
                    operation.end_time = current_time
                    operation.completed_steps = operation.total_steps
                    
                    # Close output file handles
                    operation.close_output_files()
                    
                    self._add_log_entry(f"Cleaned up stale operation: {operation.name}")
                    cleaned_count += 1
                else:
                    self.logger.info(f"  - Operation {operation.id} is legitimately running")
        
        if cleaned_count > 0:
            self.logger.info(f"Force cleanup completed: {cleaned_count} stale operations cleaned")
            self._save_operations_to_file()  # Save changes
        else:
            self.logger.info("Force cleanup completed: no stale operations found")
    
    def _verify_operation_completion_by_files(self, operation: Operation) -> bool:
        """
        Verify if an operation actually completed by checking its output files.
        Returns True if operation should be marked as completed.
        """
        if not operation.working_directory:
            return False
        
        working_dir = Path(operation.working_directory)
        if not working_dir.exists():
            return False
        
        # Check for common genmic output files that indicate successful completion
        success_indicators = [
            f"{working_dir.name}.img",      # Main microstructure file
            f"{working_dir.name}.pimg",     # Particle ID file
            f"{working_dir.name}.img.struct"  # Structure file
        ]
        
        success_count = 0
        for indicator in success_indicators:
            file_path = working_dir / indicator
            if file_path.exists() and file_path.stat().st_size > 0:
                success_count += 1
        
        # If at least 2 of the 3 key output files exist, consider it successful
        return success_count >= 2
    
    def _on_settings_clicked(self, button: Gtk.Button) -> None:
        """Handle settings button click."""
        # TODO: Show monitoring settings dialog
        self._update_status("Monitoring settings not yet implemented")
    
    def _on_set_priority_clicked(self, button: Gtk.Button) -> None:
        """Handle set priority button click."""
        # TODO: Show priority setting dialog
        self._update_status("Priority setting not yet implemented")
    
    def _on_clear_logs_clicked(self, button: Gtk.Button) -> None:
        """Handle clear logs button click."""
        self.log_buffer.set_text("")
    
    def _on_export_logs_clicked(self, button: Gtk.Button) -> None:
        """Handle export logs button click."""
        # TODO: Show export dialog
        self._update_status("Log export not yet implemented")
    
    # Utility methods
    
    def _get_selected_operation(self) -> Optional[Operation]:
        """Get the currently selected operation (first one if multiple selected)."""
        if not self.operations_view:
            return None
        
        selection = self.operations_view.get_selection()
        model, selected_rows = selection.get_selected_rows()
        
        if selected_rows:
            # Get the first selected operation
            first_path = selected_rows[0]
            treeiter = model.get_iter(first_path)
            if treeiter:
                operation_id = model[treeiter][0]
                return self.operations.get(operation_id)
        return None
    
    def _get_selected_operations(self) -> List[Operation]:
        """Get all currently selected operations."""
        if not self.operations_view:
            return []
        
        selection = self.operations_view.get_selection()
        model, selected_rows = selection.get_selected_rows()
        selected_operations = []
        
        for path in selected_rows:
            treeiter = model.get_iter(path)
            if treeiter:
                operation_id = model[treeiter][0]
                operation = self.operations.get(operation_id)
                if operation:
                    selected_operations.append(operation)
        
        return selected_operations
    
    def _show_start_operation_dialog(self) -> None:
        """Show dialog to start a new operation."""
        dialog = Gtk.Dialog(
            title="Start New Operation",
            parent=self.main_window,
            flags=Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT
        )
        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        dialog.add_button("Start", Gtk.ResponseType.OK)
        
        content_area = dialog.get_content_area()
        
        # Operation type selection
        type_label = Gtk.Label("Operation Type:")
        type_label.set_halign(Gtk.Align.START)
        content_area.pack_start(type_label, False, False, 5)
        
        type_combo = Gtk.ComboBoxText()
        for op_type in OperationType:
            type_combo.append_text(op_type.value.replace('_', ' ').title())
        type_combo.set_active(0)
        content_area.pack_start(type_combo, False, False, 5)
        
        # Operation name
        name_label = Gtk.Label("Operation Name:")
        name_label.set_halign(Gtk.Align.START)
        content_area.pack_start(name_label, False, False, 5)
        
        name_entry = Gtk.Entry()
        name_entry.set_text("New Operation")
        content_area.pack_start(name_entry, False, False, 5)
        
        dialog.show_all()
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            operation_type = list(OperationType)[type_combo.get_active()]
            operation_name = name_entry.get_text()
            self._create_sample_operation(operation_name, operation_type)
        
        dialog.destroy()
    
    def _create_sample_operation(self, name: str, operation_type: OperationType) -> None:
        """Create a sample operation for demonstration."""
        self.operation_counter += 1
        operation_id = f"op_{self.operation_counter:04d}"
        
        operation = Operation(
            id=operation_id,
            name=name,
            operation_type=operation_type,
            status=OperationStatus.RUNNING,
            start_time=datetime.now(),
            total_steps=10,
            completed_steps=0,
            current_step="Initializing..."
        )
        
        self.operations[operation_id] = operation
        self._add_log_entry(f"Started operation: {name}")
        self._update_operations_list()
    
    def _stop_operation(self, operation_id: str) -> None:
        """Stop an operation by terminating the underlying process."""
        operation = self.operations.get(operation_id)
        if operation and operation.status in [OperationStatus.RUNNING, OperationStatus.PAUSED]:
            # Try to terminate the actual process
            if operation.terminate_process():
                operation.status = OperationStatus.CANCELLED
                operation.end_time = datetime.now()
                self._add_log_entry(f"Successfully terminated process for operation: {operation.name}")
            else:
                # Process might have already ended, just update status
                operation.status = OperationStatus.CANCELLED
                operation.end_time = datetime.now()
                self._add_log_entry(f"Operation marked as stopped: {operation.name} (process may have already ended)")
            
            self._update_operations_list()
    
    def _pause_operation(self, operation_id: str) -> None:
        """Pause or resume an operation using real process control."""
        operation = self.operations.get(operation_id)
        if operation:
            if operation.status == OperationStatus.RUNNING:
                # Pause the actual process
                if operation.pause_process():
                    operation.status = OperationStatus.PAUSED
                    operation.paused_time = datetime.now()  # Record when paused
                    self._add_log_entry(f"Successfully paused process for operation: {operation.name}")
                else:
                    self._add_log_entry(f"Failed to pause process for operation: {operation.name} (process may have ended)")
                self._update_operations_list()
                
            elif operation.status == OperationStatus.PAUSED:
                # Resume the actual process
                if operation.resume_process():
                    operation.status = OperationStatus.RUNNING
                    # Adjust start_time to account for paused duration
                    if operation.paused_time and operation.start_time:
                        paused_duration = datetime.now() - operation.paused_time
                        operation.start_time = operation.start_time + paused_duration
                    operation.paused_time = None  # Clear paused time
                    self._add_log_entry(f"Successfully resumed process for operation: {operation.name}")
                else:
                    self._add_log_entry(f"Failed to resume process for operation: {operation.name} (process may have ended)")
                self._update_operations_list()
    
    def _add_log_entry(self, message: str) -> None:
        """Add an entry to the operation log."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        # Add to log buffer
        end_iter = self.log_buffer.get_end_iter()
        self.log_buffer.insert(end_iter, log_entry)
        
        # Auto-scroll if enabled
        if self.auto_scroll_check.get_active():
            mark = self.log_buffer.get_insert()
            self.log_view.scroll_to_mark(mark, 0.0, False, 0.0, 0.0)
    
    # =========================================================================
    # Public API Methods for Operation Management
    # =========================================================================
    
    def register_operation(self, name: str, operation_type: OperationType, 
                          total_steps: int = 0, estimated_duration: Optional[timedelta] = None,
                          metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Register a new operation with the monitoring system.
        
        Args:
            name: Human-readable operation name
            operation_type: Type of operation
            total_steps: Total number of steps (for step-based progress)
            estimated_duration: Estimated time to completion
            metadata: Additional operation metadata
            
        Returns:
            operation_id: Unique identifier for the operation
        """
        self.operation_counter += 1
        operation_id = f"op_{self.operation_counter:04d}"
        
        operation = Operation(
            id=operation_id,
            name=name,
            operation_type=operation_type,
            status=OperationStatus.PENDING,
            total_steps=total_steps,
            estimated_duration=estimated_duration,
            metadata=metadata or {}
        )
        
        self.operations[operation_id] = operation
        self._add_log_entry(f"Registered operation: {name}")
        self._update_operations_list()
        
        return operation_id
    
    def start_real_process_operation(self, name: str, operation_type: OperationType, 
                                    command: List[str], working_dir: str, 
                                    input_data: Optional[str] = None) -> str:
        """
        Start a real process operation.
        
        Args:
            name: Human-readable name for the operation
            operation_type: Type of operation
            command: Command line as list of strings
            working_dir: Working directory for the process
            input_data: Optional stdin data for the process
            
        Returns:
            Operation ID
        """
        operation_id = f"proc_{int(time.time() * 1000)}"
        
        try:
            # Create output files in the working directory
            stdout_file = os.path.join(working_dir, f"{operation_id}_stdout.txt")
            stderr_file = os.path.join(working_dir, f"{operation_id}_stderr.txt")
            
            # Open output files
            stdout_handle = open(stdout_file, 'w', encoding='utf-8', buffering=1)
            stderr_handle = open(stderr_file, 'w', encoding='utf-8', buffering=1)
            
            # Start the actual process with file redirection
            process = subprocess.Popen(
                command,
                cwd=working_dir,
                stdin=subprocess.PIPE if input_data else None,
                stdout=stdout_handle,
                stderr=stderr_handle,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Send input data if provided
            if input_data:
                process.stdin.write(input_data)
                process.stdin.close()
            
            # Create operation with process information
            operation = Operation(
                id=operation_id,
                name=name,
                operation_type=operation_type,
                status=OperationStatus.RUNNING,
                start_time=datetime.now(),
                progress=0.05,  # Start with 5% to show immediate feedback
                current_step="Process started",
                total_steps=4,  # Typical genmic phases: Init, Parse, Generate, Finalize
                estimated_duration=timedelta(minutes=3)  # Reasonable default estimate
            )
            
            # Set process information
            operation.process = process
            operation.pid = process.pid
            operation.working_directory = working_dir
            operation.command_line = command
            operation.stdout_file = stdout_file
            operation.stderr_file = stderr_file
            operation.stdout_handle = stdout_handle
            operation.stderr_handle = stderr_handle
            
            self.operations[operation_id] = operation
            self._add_log_entry(f"Started real process operation: {name} (PID: {process.pid})")
            self._add_log_entry(f"Command: {' '.join(command)}")
            self._add_log_entry(f"Working directory: {working_dir}")
            self._add_log_entry(f"Stdout redirected to: {os.path.basename(stdout_file)}")
            self._add_log_entry(f"Stderr redirected to: {os.path.basename(stderr_file)}")
            self._update_operations_list()
            
            return operation_id
            
        except Exception as e:
            # Clean up file handles if they were opened
            try:
                if 'stdout_handle' in locals() and stdout_handle:
                    stdout_handle.close()
            except:
                pass
            try:
                if 'stderr_handle' in locals() and stderr_handle:
                    stderr_handle.close()
            except:
                pass
            
            self.logger.error(f"Failed to start process operation {name}: {e}")
            self._add_log_entry(f"Failed to start operation {name}: {str(e)}")
            return ""

    def start_operation(self, operation_id: str, current_step: str = "Starting...") -> bool:
        """
        Start a registered operation.
        
        Args:
            operation_id: Operation identifier
            current_step: Description of current step
            
        Returns:
            True if operation was started successfully
        """
        operation = self.operations.get(operation_id)
        if operation and operation.status == OperationStatus.PENDING:
            operation.status = OperationStatus.RUNNING
            operation.start_time = datetime.now()
            operation.current_step = current_step
            
            self._add_log_entry(f"Started operation: {operation.name}")
            self._update_operations_list()
            return True
        return False
    
    def update_operation_progress(self, operation_id: str, progress: float, 
                                current_step: str = "", completed_steps: int = 0) -> bool:
        """
        Update operation progress.
        
        Args:
            operation_id: Operation identifier
            progress: Progress value (0.0 to 1.0)
            current_step: Description of current step
            completed_steps: Number of completed steps
            
        Returns:
            True if operation was updated successfully
        """
        operation = self.operations.get(operation_id)
        if operation and operation.status == OperationStatus.RUNNING:
            operation.progress = max(0.0, min(1.0, progress))
            if current_step:
                operation.current_step = current_step
            if completed_steps > 0:
                operation.completed_steps = completed_steps
            
            self._update_operations_list()
            return True
        return False
    
    def complete_operation(self, operation_id: str, success: bool = True, 
                          error_message: Optional[str] = None) -> bool:
        """
        Mark an operation as completed.
        
        Args:
            operation_id: Operation identifier
            success: Whether operation completed successfully
            error_message: Error message if operation failed
            
        Returns:
            True if operation was completed successfully
        """
        operation = self.operations.get(operation_id)
        if operation and operation.status in [OperationStatus.RUNNING, OperationStatus.PAUSED]:
            operation.status = OperationStatus.COMPLETED if success else OperationStatus.FAILED
            operation.end_time = datetime.now()
            operation.progress = 1.0
            operation.error_message = error_message
            
            status_text = "completed successfully" if success else "failed"
            self._add_log_entry(f"Operation {status_text}: {operation.name}")
            if error_message:
                self._add_log_entry(f"Error: {error_message}")
                
            self._update_operations_list()
            self._save_operations_to_file()  # Save when operation completes
            return True
        return False
    
    def cancel_operation(self, operation_id: str) -> bool:
        """
        Cancel a running operation.
        
        Args:
            operation_id: Operation identifier
            
        Returns:
            True if operation was cancelled successfully
        """
        operation = self.operations.get(operation_id)
        if operation and operation.status in [OperationStatus.RUNNING, OperationStatus.PAUSED, OperationStatus.PENDING]:
            operation.status = OperationStatus.CANCELLED
            operation.end_time = datetime.now()
            
            self._add_log_entry(f"Cancelled operation: {operation.name}")
            self._update_operations_list()
            self._save_operations_to_file()  # Save when operation cancelled
            return True
        return False
    
    def get_operation(self, operation_id: str) -> Optional[Operation]:
        """
        Get operation by ID.
        
        Args:
            operation_id: Operation identifier
            
        Returns:
            Operation object or None if not found
        """
        return self.operations.get(operation_id)
    
    def get_active_operations(self) -> List[Operation]:
        """
        Get all active (running or paused) operations.
        
        Returns:
            List of active operations
        """
        return [op for op in self.operations.values() 
                if op.status in [OperationStatus.RUNNING, OperationStatus.PAUSED]]
    
    def _update_status(self, message: str) -> None:
        """Update status bar message."""
        self.status_bar.pop(self.status_context)
        self.status_bar.push(self.status_context, message)
    
    # Operations Files Browser Methods
    
    def _load_operations_files(self) -> None:
        """Load the Operations directory structure into the file tree."""
        self.logger.info("=== Starting _load_operations_files ===")
        
        # Get the Operations directory path using absolute path from project root
        # Don't rely on current working directory since genmic changes it
        # Path: src/app/windows/panels/operations_monitoring_panel.py -> go up 5 levels to project root
        project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
        operations_dir = project_root / "Operations"
        self.logger.info(f"Project root: {project_root}")
        self.logger.info(f"Operations directory: {operations_dir}")
        self.logger.info(f"Operations directory exists: {operations_dir.exists()}")
        
        if not operations_dir.exists():
            self.files_store.clear()
            self.files_store.append(None, ["No Operations directory found", "", "info", "", ""])
            return
        
        # Build the new tree data first, then replace the store content
        new_tree_data = []
        
        # Add retry logic and better error handling for running operations
        max_retries = 3
        success = False
        
        for attempt in range(max_retries):
            try:
                self.logger.info(f"Attempt {attempt + 1}: scanning operations directory")
                all_items = list(operations_dir.iterdir())
                self.logger.info(f"Found {len(all_items)} total items in Operations directory")
                
                operation_dirs = sorted([
                    d for d in all_items 
                    if d.is_dir() and not d.name.startswith('.') and d.name not in ['__pycache__', 'Thumbs.db']
                ])
                self.logger.info(f"Found {len(operation_dirs)} operation directories: {[d.name for d in operation_dirs]}")
                
                # Successfully got directory list, now build tree data
                for op_dir in operation_dirs:
                    self.logger.info(f"Building data for operation directory: {op_dir.name}")
                    op_data = self._build_operation_folder_data(op_dir)
                    if op_data:
                        new_tree_data.append(op_data)
                        self.logger.info(f"Successfully built data for {op_dir.name} with {len(op_data['files'])} files")
                    else:
                        self.logger.warning(f"Failed to build data for {op_dir.name}")
                
                success = True
                self.logger.info(f"Successfully gathered data for {len(new_tree_data)} operations")
                break  # Success, exit retry loop
                
            except (PermissionError, OSError, FileNotFoundError) as e:
                self.logger.warning(f"File access error on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    # Wait a bit before retrying
                    import time
                    time.sleep(0.1)
            except Exception as e:
                self.logger.error(f"Unexpected error loading operation directories: {e}")
                break
        
        # Now update the display - clear and rebuild
        try:
            self.logger.info("=== Updating display ===")
            self.files_store.clear()
            
            # Add root Operations folder
            root_iter = self.files_store.append(None, ["Operations", str(operations_dir), "folder", "", ""])
            
            if success and new_tree_data:
                self.logger.info(f"Adding {len(new_tree_data)} operations to display")
                # Add all the operation folders we successfully gathered
                for op_data in new_tree_data:
                    self._add_operation_folder_from_data(root_iter, op_data)
            else:
                self.logger.warning(f"Failed to load operations: success={success}, data_count={len(new_tree_data)}")
                # Failed to load after retries
                self.files_store.append(root_iter, [
                    "⚠️ Files temporarily unavailable (operation running?)", 
                    "", "warning", "", ""
                ])
            
            # Expand the root by default
            self.files_view.expand_row(self.files_store.get_path(root_iter), False)
            self.logger.info("=== Display update complete ===\n")
            
        except Exception as e:
            self.logger.error(f"Error updating files display: {e}")
            self.files_store.clear()
            self.files_store.append(None, [f"Error loading files: {e}", "", "error", "", ""])
    
    def _build_operation_folder_data(self, op_dir: Path) -> dict:
        """Build operation folder data structure without adding to tree store."""
        try:
            # Get folder info with error handling for running operations
            try:
                stat_info = op_dir.stat()
                modified_time = datetime.fromtimestamp(stat_info.st_mtime).strftime("%Y-%m-%d %H:%M")
            except (PermissionError, OSError, FileNotFoundError):
                # Folder access issues, likely due to running operation
                modified_time = "Accessing..."
            
            folder_data = {
                'name': op_dir.name,
                'path': str(op_dir),
                'type': 'folder',
                'size': '',
                'modified': modified_time,
                'files': []
            }
            
            # Add files in the operation directory with retry logic
            max_retries = 2
            for attempt in range(max_retries):
                try:
                    files = sorted(op_dir.iterdir())
                    for file_path in files:
                        if file_path.is_file():
                            file_data = self._build_file_data(file_path)
                            if file_data:
                                folder_data['files'].append(file_data)
                    break  # Success, exit retry loop
                    
                except (PermissionError, OSError, FileNotFoundError) as e:
                    if attempt == max_retries - 1:
                        # Final attempt failed - add warning indicator
                        folder_data['files'].append({
                            'name': "⚠️ Files temporarily inaccessible",
                            'path': "",
                            'type': 'warning',
                            'size': "",
                            'modified': ""
                        })
                    else:
                        # Brief pause before retry
                        import time
                        time.sleep(0.05)
                except Exception as e:
                    self.logger.error(f"Error loading files in {op_dir}: {e}")
                    folder_data['files'].append({
                        'name': f"Error loading files: {e}",
                        'path': "",
                        'type': 'error',
                        'size': "",
                        'modified': ""
                    })
                    break
            
            return folder_data
            
        except Exception as e:
            self.logger.error(f"Error building operation folder data for {op_dir}: {e}")
            return None
    
    def _build_file_data(self, file_path: Path) -> dict:
        """Build file data structure without adding to tree store."""
        try:
            # Handle file access issues gracefully for running operations
            try:
                stat_info = file_path.stat()
                file_size = self._format_file_size(stat_info.st_size)
                modified_time = datetime.fromtimestamp(stat_info.st_mtime).strftime("%Y-%m-%d %H:%M")
            except (PermissionError, OSError, FileNotFoundError):
                # File is being written to or temporarily inaccessible
                file_size = "..."
                modified_time = "Writing..."
            
            # Determine file type for icon
            file_type = self._get_file_type(file_path)
            
            return {
                'name': file_path.name,
                'path': str(file_path),
                'type': file_type,
                'size': file_size,
                'modified': modified_time
            }
            
        except Exception as e:
            # Log error but don't prevent the overall refresh from working
            self.logger.debug(f"Skipping file {file_path.name}: {e}")
            return None
    
    def _add_operation_folder_from_data(self, parent_iter, op_data: dict) -> None:
        """Add an operation folder to the tree from pre-built data."""
        try:
            # Add operation folder
            folder_iter = self.files_store.append(parent_iter, [
                op_data['name'],
                op_data['path'],
                op_data['type'],
                op_data['size'],
                op_data['modified']
            ])
            
            # Add files
            for file_data in op_data['files']:
                self.files_store.append(folder_iter, [
                    file_data['name'],
                    file_data['path'],
                    file_data['type'],
                    file_data['size'],
                    file_data['modified']
                ])
                
        except Exception as e:
            self.logger.error(f"Error adding operation folder from data: {e}")
    
    def _add_operation_folder(self, parent_iter, op_dir: Path) -> None:
        """Add an operation folder and its files to the tree."""
        try:
            # Get folder info with error handling for running operations
            try:
                stat_info = op_dir.stat()
                modified_time = datetime.fromtimestamp(stat_info.st_mtime).strftime("%Y-%m-%d %H:%M")
            except (PermissionError, OSError, FileNotFoundError):
                # Folder access issues, likely due to running operation
                modified_time = "Accessing..."
            
            # Add operation folder
            folder_iter = self.files_store.append(parent_iter, [
                op_dir.name,
                str(op_dir),
                "folder", 
                "",
                modified_time
            ])
            
            # Add files in the operation directory with retry logic
            max_retries = 2
            for attempt in range(max_retries):
                try:
                    files = sorted(op_dir.iterdir())
                    for file_path in files:
                        if file_path.is_file():
                            self._add_file_item(folder_iter, file_path)
                    break  # Success, exit retry loop
                    
                except (PermissionError, OSError, FileNotFoundError) as e:
                    if attempt == max_retries - 1:
                        # Final attempt failed
                        self.files_store.append(folder_iter, [
                            "⚠️ Files temporarily inaccessible", 
                            "", "warning", "", ""
                        ])
                    else:
                        # Brief pause before retry
                        import time
                        time.sleep(0.05)
                except Exception as e:
                    self.logger.error(f"Error loading files in {op_dir}: {e}")
                    self.files_store.append(folder_iter, [f"Error loading files: {e}", "", "error", "", ""])
                    break
                
        except Exception as e:
            self.logger.error(f"Error adding operation folder {op_dir}: {e}")
    
    def _add_file_item(self, parent_iter, file_path: Path) -> None:
        """Add a file item to the tree."""
        try:
            # Handle file access issues gracefully for running operations
            try:
                stat_info = file_path.stat()
                file_size = self._format_file_size(stat_info.st_size)
                modified_time = datetime.fromtimestamp(stat_info.st_mtime).strftime("%Y-%m-%d %H:%M")
            except (PermissionError, OSError, FileNotFoundError):
                # File is being written to or temporarily inaccessible
                file_size = "..."
                modified_time = "Writing..."
            
            # Determine file type for icon
            file_type = self._get_file_type(file_path)
            
            self.files_store.append(parent_iter, [
                file_path.name,
                str(file_path),
                file_type,
                file_size,
                modified_time
            ])
            
        except Exception as e:
            # Log error but don't prevent the overall refresh from working
            self.logger.debug(f"Skipping file {file_path.name}: {e}")
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
    
    def _get_file_type(self, file_path: Path) -> str:
        """Determine file type based on extension."""
        suffix = file_path.suffix.lower()
        if suffix in ['.txt', '.log']:
            return 'text'
        elif suffix in ['.img', '.pimg']:
            return 'image'
        elif suffix in ['.c3s', '.c3a', '.c4f', '.alu', '.sil', '.k2o', '.n2o']:
            return 'data'
        elif suffix in ['.dat']:
            return 'binary'
        else:
            return 'file'
    
    # Event handlers for file browser
    
    def _on_refresh_files_clicked(self, button) -> None:
        """Handle refresh files button click."""
        self.logger.info("=== Files tab refresh button clicked ===")
        self._load_operations_files()
        self._update_status("Operations files refreshed")
    
    def _on_open_operations_folder_clicked(self, button) -> None:
        """Handle open operations folder button click."""
        try:
            operations_dir = Path.cwd() / "Operations"
            if operations_dir.exists():
                # Open in file manager (works on macOS, Linux, Windows)
                import subprocess
                import sys
                
                if sys.platform == "darwin":  # macOS
                    subprocess.run(["open", str(operations_dir)])
                elif sys.platform.startswith("linux"):  # Linux
                    subprocess.run(["xdg-open", str(operations_dir)])
                elif sys.platform == "win32":  # Windows
                    subprocess.run(["explorer", str(operations_dir)])
                    
                self._update_status(f"Opened Operations folder: {operations_dir}")
            else:
                self._update_status("Operations folder does not exist")
                
        except Exception as e:
            self.logger.error(f"Failed to open Operations folder: {e}")
            self._update_status(f"Error opening folder: {e}")
    
    def _on_delete_operation_clicked(self, button) -> None:
        """Handle delete operation button click."""
        selection = self.files_view.get_selection()
        model, tree_iter = selection.get_selected()
        
        if tree_iter:
            file_path = model.get_value(tree_iter, 1)  # Path is in column 1
            file_name = model.get_value(tree_iter, 0)  # Name is in column 0
            file_type = model.get_value(tree_iter, 2)  # Type is in column 2
            
            if file_type == "folder" and "Operations" in file_path:
                # Show confirmation dialog
                dialog = Gtk.MessageDialog(
                    transient_for=self.main_window,
                    message_type=Gtk.MessageType.WARNING,
                    buttons=Gtk.ButtonsType.YES_NO,
                    text="Delete Operation Folder?"
                )
                dialog.format_secondary_text(
                    f"Are you sure you want to delete the operation folder '{file_name}'?\n\n"
                    "This will permanently delete all files including:\n"
                    "• Input files\n"
                    "• Output files (.img, .pimg)\n"
                    "• Log files\n"
                    "• Correlation files\n\n"
                    "This action cannot be undone."
                )
                
                response = dialog.run()
                dialog.destroy()
                
                if response == Gtk.ResponseType.YES:
                    try:
                        import shutil
                        shutil.rmtree(file_path)
                        self._load_operations_files()  # Refresh the tree
                        self._update_status(f"Deleted operation folder: {file_name}")
                    except Exception as e:
                        self.logger.error(f"Failed to delete operation folder: {e}")
                        self._update_status(f"Error deleting folder: {e}")
            else:
                self._update_status("Please select an operation folder to delete")
        else:
            self._update_status("No operation selected")
    
    def _on_file_selection_changed(self, selection) -> None:
        """Handle file selection change in the tree view."""
        model, tree_iter = selection.get_selected()
        
        if tree_iter:
            file_path = model.get_value(tree_iter, 1)  # Path is in column 1
            file_name = model.get_value(tree_iter, 0)  # Name is in column 0
            file_type = model.get_value(tree_iter, 2)  # Type is in column 2
            file_size = model.get_value(tree_iter, 3)  # Size is in column 3
            file_modified = model.get_value(tree_iter, 4)  # Modified is in column 4
            
            # Update file info
            if file_type == "folder":
                self.file_info_label.set_text(f"Folder: {file_name}\nPath: {file_path}\nModified: {file_modified}")
                self._clear_file_preview()
            else:
                self.file_info_label.set_text(
                    f"File: {file_name}\n"
                    f"Type: {file_type}\n"
                    f"Size: {file_size}\n" 
                    f"Modified: {file_modified}\n"
                    f"Path: {file_path}"
                )
                self._load_file_preview(file_path, file_type)
        else:
            self.file_info_label.set_text("Select a file to view details")
            self._clear_file_preview()
    
    def _load_file_preview(self, file_path: str, file_type: str) -> None:
        """Load file preview in the text view."""
        try:
            path = Path(file_path)
            if not path.exists():
                self._set_preview_text("File not found")
                return
            
            # Only preview text files and logs
            if file_type in ['text', 'data'] or path.suffix.lower() in ['.txt', '.log', '.dat']:
                try:
                    # Try to read as text (limit to 10KB for performance)
                    max_size = 10 * 1024  # 10KB
                    if path.stat().st_size > max_size:
                        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read(max_size)
                        content += f"\n\n[File truncated - showing first {max_size} bytes]"
                    else:
                        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                    
                    self._set_preview_text(content)
                    
                except UnicodeDecodeError:
                    # Try as binary file
                    with open(path, 'rb') as f:
                        data = f.read(min(1024, path.stat().st_size))
                    hex_content = ' '.join(f'{b:02x}' for b in data)
                    self._set_preview_text(f"Binary file (hex preview):\n{hex_content}")
                    
            elif file_type == 'image':
                self._set_preview_text(f"Microstructure image file: {path.name}\n\nThis is a binary image file generated by genmic.\nUse the 3D Visualization tool to view the microstructure.")
            else:
                self._set_preview_text(f"Binary file: {path.name}\n\nFile type: {file_type}\nUse appropriate tools to view this file.")
                
        except Exception as e:
            self.logger.error(f"Error loading file preview: {e}")
            self._set_preview_text(f"Error loading file: {e}")
    
    def _set_preview_text(self, text: str) -> None:
        """Set text in the preview area."""
        buffer = self.file_preview.get_buffer()
        buffer.set_text(text)
    
    def _clear_file_preview(self) -> None:
        """Clear the file preview area."""
        buffer = self.file_preview.get_buffer()
        buffer.set_text("")
    
    # =========================================================================
    # Results Analysis Dashboard Methods
    # =========================================================================
    
    def _refresh_results_analysis(self) -> None:
        """Refresh all results analysis data."""
        try:
            # Throttle dashboard refresh to prevent excessive performance impact
            import time
            current_time = time.time()
            if not hasattr(self, '_last_dashboard_refresh'):
                self._last_dashboard_refresh = 0
            
            # Only refresh if more than 30 seconds have passed since last refresh
            if current_time - self._last_dashboard_refresh < 30:
                self.logger.debug("Skipping dashboard refresh - throttled")
                return
            
            self._last_dashboard_refresh = current_time
            self.logger.info("Refreshing results analysis dashboard...")
            
            # Get operations data from saved history  
            operations_data = self._load_operations_data()
            
            # Analyze operation outcomes
            self._analyze_operation_outcomes(operations_data)
            
            # Analyze result files
            self._analyze_result_files()
            
            # Analyze performance trends
            self._analyze_performance_trends(operations_data)
            
            # Analyze error patterns
            self._analyze_error_patterns(operations_data)
            
            # Assess quality metrics
            self._assess_quality_metrics()
            
            self.logger.info("Results analysis dashboard refresh completed")
            
        except Exception as e:
            self.logger.error(f"Error refreshing results analysis: {e}")
            self._set_error_analysis(f"Error refreshing analysis: {e}")
    
    def _load_operations_data(self) -> Dict[str, Any]:
        """Load operations data from history file."""
        try:
            if self.operations_file.exists():
                with open(self.operations_file, 'r') as f:
                    return json.load(f)
            return {'operations': {}}
        except Exception as e:
            self.logger.error(f"Error loading operations data: {e}")
            return {'operations': {}}
    
    def _analyze_operation_outcomes(self, operations_data: Dict[str, Any]) -> None:
        """Analyze operation success/failure patterns."""
        operations = operations_data.get('operations', {})
        
        # Count outcomes
        total_ops = len(operations)
        successful_ops = 0
        failed_ops = 0
        last_operation = "None"
        durations = []
        
        for op_id, op_data in operations.items():
            status = op_data.get('status', 'unknown')
            
            if status == 'completed':
                successful_ops += 1
            elif status == 'failed':
                failed_ops += 1
            
            # Track durations
            start_time = op_data.get('start_time')
            end_time = op_data.get('end_time')
            if start_time and end_time:
                try:
                    start_dt = datetime.fromisoformat(start_time)
                    end_dt = datetime.fromisoformat(end_time)
                    duration = (end_dt - start_dt).total_seconds()
                    durations.append(duration)
                except:
                    pass
            
            # Find most recent operation
            if end_time:
                last_operation = op_data.get('name', op_id)
        
        # Calculate metrics
        success_rate = (successful_ops / total_ops * 100) if total_ops > 0 else 0
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        # Format average duration
        hours, remainder = divmod(int(avg_duration), 3600)
        minutes, seconds = divmod(remainder, 60)
        avg_duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
        # Update UI
        self.results_total_ops.set_text(str(total_ops))
        self.results_success_count.set_text(str(successful_ops))
        self.results_failed_count.set_text(str(failed_ops))
        self.results_success_rate.set_text(f"{success_rate:.1f}%")
        self.results_last_operation.set_text(last_operation)
        self.results_avg_duration.set_text(avg_duration_str)
        
        # Update progress bar
        self.results_success_progress.set_fraction(success_rate / 100.0)
    
    def _analyze_result_files(self) -> None:
        """Analyze generated result files in Operations directory."""
        try:
            operations_dir = Path.cwd() / "Operations"
            
            if not operations_dir.exists():
                # No operations directory
                self.results_img_files.set_text("0")
                self.results_pimg_files.set_text("0")
                self.results_input_files.set_text("0")
                self.results_total_size.set_text("0 MB")
                self.results_largest_op.set_text("None")
                self.results_storage_used.set_text("0 MB")
                return
            
            # Count files and sizes
            img_files = 0
            pimg_files = 0
            input_files = 0
            total_size = 0
            largest_op = "None"
            largest_size = 0
            
            for op_dir in operations_dir.iterdir():
                if op_dir.is_dir() and not op_dir.name.startswith('.') and op_dir.name not in ['__pycache__', 'Thumbs.db']:
                    op_size = 0
                    for file_path in op_dir.rglob('*'):
                        if file_path.is_file():
                            file_size = file_path.stat().st_size
                            total_size += file_size
                            op_size += file_size
                            
                            # Count file types
                            suffix = file_path.suffix.lower()
                            if suffix == '.img':
                                img_files += 1
                            elif suffix == '.pimg':
                                pimg_files += 1
                            elif file_path.name.startswith('genmic_input'):
                                input_files += 1
                    
                    # Track largest operation
                    if op_size > largest_size:
                        largest_size = op_size
                        largest_op = op_dir.name
            
            # Format sizes
            total_mb = total_size / (1024 * 1024)
            
            # Update UI
            self.results_img_files.set_text(str(img_files))
            self.results_pimg_files.set_text(str(pimg_files))
            self.results_input_files.set_text(str(input_files))
            self.results_total_size.set_text(f"{total_mb:.1f} MB")
            self.results_largest_op.set_text(largest_op)
            self.results_storage_used.set_text(f"{total_mb:.1f} MB")
            
        except Exception as e:
            self.logger.error(f"Error analyzing result files: {e}")
            self._set_all_file_metrics_error()
    
    def _analyze_performance_trends(self, operations_data: Dict[str, Any]) -> None:
        """Analyze performance trends and patterns."""
        operations = operations_data.get('operations', {})
        
        if not operations:
            self._set_all_trend_metrics_none()
            return
        
        # Calculate performance metrics
        durations = []
        recent_ops = []
        failure_times = []
        
        for op_id, op_data in operations.items():
            start_time = op_data.get('start_time')
            end_time = op_data.get('end_time')
            status = op_data.get('status')
            
            if start_time and end_time:
                try:
                    start_dt = datetime.fromisoformat(start_time)
                    end_dt = datetime.fromisoformat(end_time)
                    duration = (end_dt - start_dt).total_seconds()
                    
                    durations.append({
                        'name': op_data.get('name', op_id),
                        'duration': duration,
                        'start_time': start_dt,
                        'status': status
                    })
                    
                    # Track recent operations (last 24 hours)
                    if (datetime.now() - end_dt).days == 0:
                        recent_ops.append({'name': op_data.get('name', op_id), 'status': status})
                    
                    # Track failure times
                    if status == 'failed':
                        failure_times.append(start_dt.hour)
                        
                except Exception as e:
                    self.logger.warning(f"Error parsing operation times for {op_id}: {e}")
        
        # Find fastest and slowest operations
        if durations:
            fastest = min(durations, key=lambda x: x['duration'])
            slowest = max(durations, key=lambda x: x['duration'])
            
            # Format durations
            def format_duration(seconds):
                hours, remainder = divmod(int(seconds), 3600)
                minutes, secs = divmod(remainder, 60)
                return f"{hours:02d}:{minutes:02d}:{secs:02d}"
            
            fastest_str = f"{fastest['name']} ({format_duration(fastest['duration'])})"
            slowest_str = f"{slowest['name']} ({format_duration(slowest['duration'])})"
        else:
            fastest_str = "None"
            slowest_str = "None"
        
        # Analyze recent trend
        recent_trend = "No recent operations"
        if recent_ops:
            recent_successes = len([op for op in recent_ops if op['status'] == 'completed'])
            recent_total = len(recent_ops)
            if recent_total > 0:
                recent_rate = (recent_successes / recent_total) * 100
                if recent_rate >= 80:
                    recent_trend = f"Excellent ({recent_rate:.0f}% success)"
                elif recent_rate >= 60:
                    recent_trend = f"Good ({recent_rate:.0f}% success)"
                else:
                    recent_trend = f"Poor ({recent_rate:.0f}% success)"
        
        # Analyze failure patterns
        failure_pattern = "No failures detected" 
        if failure_times:
            # Find most common failure hour
            from collections import Counter
            hour_counts = Counter(failure_times)
            if hour_counts:
                most_common_hour = hour_counts.most_common(1)[0][0]
                failure_pattern = f"Most failures around {most_common_hour:02d}:00"
        
        # Peak performance time (simplified analysis)
        peak_time = "Analysis needed"
        if durations:
            # Group by hour and find fastest average
            hourly_performance = {}
            for op in durations:
                hour = op['start_time'].hour
                if hour not in hourly_performance:
                    hourly_performance[hour] = []
                hourly_performance[hour].append(op['duration'])
            
            if hourly_performance:
                # Find hour with best average performance
                best_hour = min(hourly_performance.keys(), 
                              key=lambda h: sum(hourly_performance[h]) / len(hourly_performance[h]))
                peak_time = f"{best_hour:02d}:00 - {best_hour+1:02d}:00"
        
        # Calculate efficiency (simplified)
        efficiency = 0.0
        if durations:
            successful_durations = [op['duration'] for op in durations if op['status'] == 'completed']
            if successful_durations:
                avg_successful = sum(successful_durations) / len(successful_durations)
                # Efficiency based on speed (faster = more efficient)
                # Assume 300 seconds (5 min) as baseline for 100% efficiency
                efficiency = min(100.0, (300.0 / avg_successful) * 100) if avg_successful > 0 else 0.0
        
        # Update UI
        self.results_fastest_op.set_text(fastest_str)
        self.results_slowest_op.set_text(slowest_str)
        self.results_recent_trend.set_text(recent_trend)
        self.results_failure_pattern.set_text(failure_pattern)
        self.results_peak_time.set_text(peak_time)
        self.results_efficiency.set_text(f"{efficiency:.1f}%")
    
    def _analyze_error_patterns(self, operations_data: Dict[str, Any]) -> None:
        """Analyze error patterns and provide troubleshooting insights."""
        operations = operations_data.get('operations', {})
        
        error_analysis = []
        error_messages = []
        error_counts = {}
        
        # Collect error information
        for op_id, op_data in operations.items():
            if op_data.get('status') == 'failed':
                error_msg = op_data.get('error_message', 'Unknown error')
                error_messages.append(error_msg)
                
                # Count error types
                if 'genmic execution failed' in error_msg:
                    error_counts['genmic_execution'] = error_counts.get('genmic_execution', 0) + 1
                elif 'no output files created' in error_msg:
                    error_counts['no_output'] = error_counts.get('no_output', 0) + 1
                elif 'exit code: 1' in error_msg:
                    error_counts['exit_code_1'] = error_counts.get('exit_code_1', 0) + 1
                else:
                    error_counts['other'] = error_counts.get('other', 0) + 1
        
        if not error_messages:
            error_analysis.append("✅ No errors detected in operation history.")
            error_analysis.append("")
            error_analysis.append("All operations completed successfully or are still running.")
        else:
            error_analysis.append(f"🚨 ERROR ANALYSIS - {len(error_messages)} failed operations detected")
            error_analysis.append("=" * 60)
            error_analysis.append("")
            
            # Most common errors
            if error_counts:
                error_analysis.append("📊 ERROR FREQUENCY:")
                for error_type, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True):
                    if error_type == 'genmic_execution':
                        error_analysis.append(f"   • genmic execution failures: {count}")
                    elif error_type == 'no_output':
                        error_analysis.append(f"   • No output files generated: {count}")
                    elif error_type == 'exit_code_1':
                        error_analysis.append(f"   • Process exit errors: {count}")
                    else:
                        error_analysis.append(f"   • Other errors: {count}")
                error_analysis.append("")
            
            # Troubleshooting recommendations
            error_analysis.append("🔧 TROUBLESHOOTING RECOMMENDATIONS:")
            error_analysis.append("")
            
            if error_counts.get('genmic_execution', 0) > 0:
                error_analysis.append("1. GENMIC EXECUTION ISSUES:")
                error_analysis.append("   • Check that genmic binary exists and is executable")
                error_analysis.append("   • Verify input file format and syntax")  
                error_analysis.append("   • Check available memory and disk space")
                error_analysis.append("   • Review system resource limits")
                error_analysis.append("")
            
            if error_counts.get('no_output', 0) > 0:
                error_analysis.append("2. NO OUTPUT FILES GENERATED:")
                error_analysis.append("   • Verify Operations directory permissions")
                error_analysis.append("   • Check disk space in output directory")
                error_analysis.append("   • Review genmic input parameters")
                error_analysis.append("   • Check for corrupted input data")
                error_analysis.append("")
            
            if error_counts.get('exit_code_1', 0) > 0:
                error_analysis.append("3. PROCESS EXIT ERRORS:")
                error_analysis.append("   • Review input file syntax and parameters")
                error_analysis.append("   • Check for missing correlation files")
                error_analysis.append("   • Verify cement phase fraction data integrity")
                error_analysis.append("   • Consider reducing system size if memory limited")
                error_analysis.append("")
            
            # Recent error messages
            error_analysis.append("📋 RECENT ERROR MESSAGES:")
            for i, msg in enumerate(error_messages[-5:], 1):  # Last 5 errors
                error_analysis.append(f"{i}. {msg}")
        
        # Update error analysis display
        error_text = "\n".join(error_analysis)
        buffer = self.results_error_text.get_buffer()
        buffer.set_text(error_text)
    
    def _assess_quality_metrics(self) -> None:
        """Assess quality of generated results."""
        try:
            operations_dir = Path.cwd() / "Operations"
            
            if not operations_dir.exists():
                self._set_all_quality_metrics_unknown()
                return
            
            # Quality assessment metrics
            valid_results = 0
            invalid_results = 0
            total_operations = 0
            file_integrity_issues = 0
            data_consistency_issues = 0
            
            for op_dir in operations_dir.iterdir():
                if op_dir.is_dir() and not op_dir.name.startswith('.') and op_dir.name not in ['__pycache__', 'Thumbs.db']:
                    total_operations += 1
                    op_valid = True
                    
                    # Check for required output files
                    img_files = list(op_dir.glob('*.img'))
                    pimg_files = list(op_dir.glob('*.pimg'))
                    input_files = list(op_dir.glob('genmic_input_*.txt'))
                    
                    # Basic validation checks
                    if not img_files and not pimg_files:
                        # No output files - likely failed operation
                        invalid_results += 1
                        op_valid = False
                    else:
                        # Check file integrity (basic size checks)
                        for img_file in img_files:
                            if img_file.stat().st_size < 1000:  # Very small files likely corrupted
                                file_integrity_issues += 1
                                op_valid = False
                        
                        # Check input file exists and has content
                        if input_files:
                            for input_file in input_files:
                                if input_file.stat().st_size < 100:  # Very small input files
                                    data_consistency_issues += 1
                        else:
                            data_consistency_issues += 1  # Missing input file
                    
                    if op_valid:
                        valid_results += 1
            
            # Calculate metrics
            validation_rate = (valid_results / total_operations * 100) if total_operations > 0 else 0
            
            # Assess file integrity
            if file_integrity_issues == 0:
                file_integrity = "Excellent - No issues detected"
            elif file_integrity_issues <= 2:
                file_integrity = f"Good - {file_integrity_issues} minor issues"
            else:
                file_integrity = f"Poor - {file_integrity_issues} issues detected"
            
            # Assess data consistency  
            if data_consistency_issues == 0:
                data_consistency = "Excellent - All files consistent"
            elif data_consistency_issues <= 2:
                data_consistency = f"Good - {data_consistency_issues} minor issues"
            else:
                data_consistency = f"Poor - {data_consistency_issues} issues detected"
            
            # Overall quality assessment
            if validation_rate >= 90 and file_integrity_issues == 0 and data_consistency_issues == 0:
                overall_quality = "Excellent ⭐⭐⭐"
            elif validation_rate >= 75 and file_integrity_issues <= 2 and data_consistency_issues <= 2:
                overall_quality = "Good ⭐⭐"
            elif validation_rate >= 50:
                overall_quality = "Fair ⭐"
            else:
                overall_quality = "Poor - Needs attention"
            
            # Update UI
            self.results_valid_count.set_text(str(valid_results))
            self.results_invalid_count.set_text(str(invalid_results))
            self.results_validation_rate.set_text(f"{validation_rate:.1f}%")
            self.results_file_integrity.set_text(file_integrity)
            self.results_data_consistency.set_text(data_consistency)
            self.results_overall_quality.set_text(overall_quality)
            
        except Exception as e:
            self.logger.error(f"Error assessing quality metrics: {e}")
            self._set_all_quality_metrics_error()
    
    def _set_error_analysis(self, error_message: str) -> None:
        """Set error message in analysis display."""
        buffer = self.results_error_text.get_buffer()
        buffer.set_text(f"❌ Error performing analysis:\n\n{error_message}")
    
    def _set_all_file_metrics_error(self) -> None:
        """Set error state for all file metrics."""
        self.results_img_files.set_text("Error")
        self.results_pimg_files.set_text("Error")
        self.results_input_files.set_text("Error")
        self.results_total_size.set_text("Error")
        self.results_largest_op.set_text("Error")
        self.results_storage_used.set_text("Error")
    
    def _set_all_trend_metrics_none(self) -> None:
        """Set 'None' state for all trend metrics."""
        self.results_fastest_op.set_text("None")
        self.results_slowest_op.set_text("None")
        self.results_recent_trend.set_text("No operations")
        self.results_failure_pattern.set_text("No data")
        self.results_peak_time.set_text("Unknown")
        self.results_efficiency.set_text("0%")
    
    def _set_all_quality_metrics_unknown(self) -> None:
        """Set 'Unknown' state for all quality metrics.""" 
        self.results_valid_count.set_text("0")
        self.results_invalid_count.set_text("0")
        self.results_validation_rate.set_text("0%")
        self.results_file_integrity.set_text("No operations directory")
        self.results_data_consistency.set_text("No operations directory")
        self.results_overall_quality.set_text("No data available")
    
    def _set_all_quality_metrics_error(self) -> None:
        """Set error state for all quality metrics."""
        self.results_valid_count.set_text("Error")
        self.results_invalid_count.set_text("Error")
        self.results_validation_rate.set_text("Error")
        self.results_file_integrity.set_text("Error")
        self.results_data_consistency.set_text("Error")
        self.results_overall_quality.set_text("Error")
    
    # Results Analysis Event Handlers
    
    def _on_refresh_analysis_clicked(self, button: Gtk.Button) -> None:
        """Handle refresh analysis button click."""
        self._refresh_results_analysis()
        self._update_status("Results analysis refreshed")
    
    def _on_export_report_clicked(self, button: Gtk.Button) -> None:
        """Handle export report button click."""
        try:
            # Create report content
            report_lines = []
            report_lines.append("VCCTL Operations Results Analysis Report")
            report_lines.append("=" * 50)
            report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            report_lines.append("")
            
            # Operation outcomes
            report_lines.append("OPERATION OUTCOMES:")
            report_lines.append(f"  Total Operations: {self.results_total_ops.get_text()}")
            report_lines.append(f"  Successful: {self.results_success_count.get_text()}")
            report_lines.append(f"  Failed: {self.results_failed_count.get_text()}")
            report_lines.append(f"  Success Rate: {self.results_success_rate.get_text()}")
            report_lines.append(f"  Average Duration: {self.results_avg_duration.get_text()}")
            report_lines.append("")
            
            # File analysis
            report_lines.append("RESULT FILES:")
            report_lines.append(f"  Microstructure Files: {self.results_img_files.get_text()}")
            report_lines.append(f"  Parameter Files: {self.results_pimg_files.get_text()}")
            report_lines.append(f"  Input Files: {self.results_input_files.get_text()}")
            report_lines.append(f"  Total Size: {self.results_total_size.get_text()}")
            report_lines.append("")
            
            # Performance trends
            report_lines.append("PERFORMANCE TRENDS:")
            report_lines.append(f"  Fastest Operation: {self.results_fastest_op.get_text()}")
            report_lines.append(f"  Slowest Operation: {self.results_slowest_op.get_text()}")
            report_lines.append(f"  Recent Trend: {self.results_recent_trend.get_text()}")
            report_lines.append(f"  Efficiency: {self.results_efficiency.get_text()}")
            report_lines.append("")
            
            # Quality assessment
            report_lines.append("QUALITY ASSESSMENT:")
            report_lines.append(f"  Valid Results: {self.results_valid_count.get_text()}")
            report_lines.append(f"  Validation Rate: {self.results_validation_rate.get_text()}")
            report_lines.append(f"  File Integrity: {self.results_file_integrity.get_text()}")
            report_lines.append(f"  Overall Quality: {self.results_overall_quality.get_text()}")
            report_lines.append("")
            
            # Error analysis
            buffer = self.results_error_text.get_buffer()
            start_iter = buffer.get_start_iter()
            end_iter = buffer.get_end_iter()
            error_text = buffer.get_text(start_iter, end_iter, False)
            
            report_lines.append("ERROR ANALYSIS:")
            report_lines.extend(error_text.split('\n'))
            
            # Show save dialog
            dialog = Gtk.FileChooserDialog(
                title="Export Results Analysis Report",
                parent=self.main_window,
                action=Gtk.FileChooserAction.SAVE
            )
            dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
            dialog.add_button("Save", Gtk.ResponseType.OK)
            
            # Set default filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dialog.set_current_name(f"vcctl_results_analysis_{timestamp}.txt")
            
            response = dialog.run()
            if response == Gtk.ResponseType.OK:
                filename = dialog.get_filename()
                with open(filename, 'w') as f:
                    f.write('\n'.join(report_lines))
                self._update_status(f"Report exported to: {filename}")
            
            dialog.destroy()
            
        except Exception as e:
            self.logger.error(f"Error exporting report: {e}")
            self._update_status(f"Error exporting report: {e}")
    
    def _on_cleanup_results_clicked(self, button: Gtk.Button) -> None:
        """Handle cleanup old results button click."""
        # Show confirmation dialog
        dialog = Gtk.MessageDialog(
            transient_for=self.main_window,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Cleanup Old Operation Results?"
        )
        dialog.format_secondary_text(
            "This will permanently delete:\n"
            "• Failed operation folders and files\n"
            "• Operations older than 30 days\n"
            "• Temporary and log files\n\n"
            "This action cannot be undone."
        )
        
        response = dialog.run()
        dialog.destroy()
        
        if response == Gtk.ResponseType.YES:
            try:
                operations_dir = Path.cwd() / "Operations"
                if not operations_dir.exists():
                    self._update_status("No Operations directory found")
                    return
                
                deleted_count = 0
                freed_space = 0
                cutoff_date = datetime.now() - timedelta(days=30)
                
                for op_dir in operations_dir.iterdir():
                    if op_dir.is_dir():
                        should_delete = False
                        
                        # Check if operation is old
                        mod_time = datetime.fromtimestamp(op_dir.stat().st_mtime)
                        if mod_time < cutoff_date:
                            should_delete = True
                        
                        # Check if operation failed (no output files)
                        img_files = list(op_dir.glob('*.img'))
                        pimg_files = list(op_dir.glob('*.pimg'))
                        if not img_files and not pimg_files:
                            should_delete = True
                        
                        if should_delete:
                            # Calculate size before deletion
                            dir_size = sum(f.stat().st_size for f in op_dir.rglob('*') if f.is_file())
                            freed_space += dir_size
                            
                            # Delete directory
                            import shutil
                            shutil.rmtree(op_dir)
                            deleted_count += 1
                
                freed_mb = freed_space / (1024 * 1024)
                self._update_status(f"Cleanup completed: {deleted_count} operations deleted, {freed_mb:.1f} MB freed")
                
                # Refresh analysis after cleanup
                self._refresh_results_analysis()
                
            except Exception as e:
                self.logger.error(f"Error during cleanup: {e}")
                self._update_status(f"Error during cleanup: {e}")
    
    def _on_validate_results_clicked(self, button: Gtk.Button) -> None:
        """Handle validate results button click."""
        try:
            self._update_status("Running results validation...")
            
            # Force refresh quality assessment
            self._assess_quality_metrics()
            
            # Update analysis
            self._refresh_results_analysis()
            
            self._update_status("Results validation completed")
            
        except Exception as e:
            self.logger.error(f"Error during validation: {e}")
            self._update_status(f"Error during validation: {e}")

    def cleanup(self) -> None:
        """Cleanup resources."""
        self.logger.info("Starting operations monitoring panel cleanup...")
        try:
            self._stop_monitoring()
            self._save_operations_to_file()  # Save operations before cleanup
            self.logger.info(f"Operations monitoring panel cleanup completed - saved {len(self.operations)} operations")
        except Exception as e:
            self.logger.error(f"Error during operations panel cleanup: {e}")
    
    def save_operations_now(self) -> None:
        """Manually save operations immediately."""
        self._save_operations_to_file()
    
    def _save_operations_to_file(self) -> None:
        """Save operations to JSON file."""
        try:
            self.logger.info(f"Attempting to save {len(self.operations)} operations to {self.operations_file}")
            
            # Ensure config directory exists
            self.operations_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert operations to serializable format
            operations_data = {
                'operations': {op_id: op.to_dict() for op_id, op in self.operations.items()},
                'operation_counter': self.operation_counter,
                'saved_at': datetime.now().isoformat()
            }
            
            # Write to file
            with open(self.operations_file, 'w') as f:
                json.dump(operations_data, f, indent=2)
            
            self.logger.info(f"Successfully saved {len(self.operations)} operations to {self.operations_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save operations to file: {e}", exc_info=True)
    
    def _load_operations_from_file(self) -> None:
        """Load operations from JSON file and database."""
        # First load from file (existing operations)
        try:
            self.logger.info(f"Attempting to load operations from {self.operations_file}")
            
            if self.operations_file.exists():
                with open(self.operations_file, 'r') as f:
                    data = json.load(f)
                
                self.logger.info(f"Found operations file with {len(data.get('operations', {}))} operations")
                
                # Load operations from file
                operations_data = data.get('operations', {})
                for op_id, op_data in operations_data.items():
                    try:
                        operation = Operation.from_dict(op_data)
                        self.operations[op_id] = operation
                    except Exception as e:
                        self.logger.warning(f"Failed to load operation {op_id}: {e}")
                
                # Restore operation counter
                self.operation_counter = data.get('operation_counter', 0)
                
                self.logger.info(f"Successfully loaded {len(self.operations)} operations from file")
            else:
                self.logger.info("No operations history file found")
            
        except Exception as e:
            self.logger.error(f"Failed to load operations from file: {e}", exc_info=True)
        
        # Then load from database (recent operations like hydration simulations)
        try:
            self.logger.info("Loading operations from database...")
            operation_service = self.service_container.operation_service
            
            # Get all operations from database
            db_operations = operation_service.get_all()
            self.logger.info(f"Found {len(db_operations)} operations in database")
            
            # Convert database operations to UI operations
            for db_op in db_operations:
                try:
                    ui_operation = self._convert_db_operation_to_ui_operation(db_op)
                    
                    # Only add if not already loaded from file
                    if ui_operation.id not in self.operations:
                        self.operations[ui_operation.id] = ui_operation
                        self.logger.info(f"Added database operation: {ui_operation.name} (type: {ui_operation.operation_type}, status: {ui_operation.status})")
                    else:
                        # Update status if the database version is more recent
                        existing = self.operations[ui_operation.id]
                        # Use start time for comparison since Operation model doesn't have 'updated' field
                        db_time = db_op.start or db_op.queue
                        existing_time = existing.start_time
                        if db_time and existing_time and db_time > existing_time:
                            existing.status = ui_operation.status
                            existing.progress = ui_operation.progress
                            existing.end_time = ui_operation.end_time
                            self.logger.debug(f"Updated operation status: {ui_operation.name} -> {ui_operation.status.value}")
                        else:
                            # Just update the status to be safe
                            existing.status = ui_operation.status
                            existing.progress = ui_operation.progress
                            existing.end_time = ui_operation.end_time
                            
                except Exception as e:
                    self.logger.warning(f"Failed to convert database operation {db_op.name}: {e}")
            
            self.logger.info(f"Total operations loaded: {len(self.operations)}")
            
        except Exception as e:
            self.logger.error(f"Failed to load operations from database: {e}", exc_info=True)
        
        # Finally scan Operations directory for filesystem operations (microstructures)
        try:
            self.logger.info("Scanning Operations directory for filesystem operations...")
            operations_dir = Path(__file__).parent.parent.parent.parent.parent / "Operations"
            
            if operations_dir.exists():
                added_count = 0
                for operation_folder in operations_dir.iterdir():
                    if operation_folder.is_dir():
                        operation_name = operation_folder.name
                        
                        # Skip if already loaded from file or database
                        existing_ops = [op.name for op in self.operations.values()]
                        if operation_name in existing_ops:
                            continue
                        
                        # Check if this looks like a microstructure operation
                        img_files = list(operation_folder.glob("*.img"))
                        pimg_files = list(operation_folder.glob("*.pimg"))
                        genmic_files = list(operation_folder.glob("genmic_input_*.txt"))
                        
                        if img_files or pimg_files or genmic_files:
                            # Create operation from filesystem data
                            operation_id = f"fs_{operation_name}"
                            
                            # Determine operation type
                            if any(f.name.endswith('.h.') for f in operation_folder.glob("*.img.*")):
                                op_type = OperationType.HYDRATION_SIMULATION
                            else:
                                op_type = OperationType.MICROSTRUCTURE_GENERATION
                            
                            # Get modification time
                            mod_time = datetime.fromtimestamp(operation_folder.stat().st_mtime)
                            
                            # Create operation object  
                            operation = Operation(
                                id=operation_id,
                                name=operation_name,
                                operation_type=op_type,
                                status=OperationStatus.COMPLETED,  # Use proper enum
                                progress=100.0,
                                start_time=mod_time,
                                end_time=mod_time,
                                metadata={
                                    'source': 'filesystem',
                                    'output_directory': str(operation_folder),
                                    'img_files': len(img_files),
                                    'pimg_files': len(pimg_files)
                                }
                            )
                            
                            self.operations[operation_id] = operation
                            added_count += 1
                
                self.logger.info(f"Filesystem scan complete. Added {added_count} operations. Total: {len(self.operations)}")
            else:
                self.logger.warning("Operations directory not found")
                
        except Exception as e:
            self.logger.error(f"Failed to scan Operations directory: {e}", exc_info=True)
        
        # Update UI with all loaded operations
        if self.operations:
            self._update_operations_list()
            self._update_performance_metrics()
            # Refresh results analysis with loaded data
            try:
                self._refresh_results_analysis()
            except Exception as e:
                self.logger.warning(f"Error refreshing results analysis on load: {e}")
    
    def _convert_db_operation_to_ui_operation(self, db_op) -> Operation:
        """Convert database Operation to UI Operation format."""
        from app.models.operation import OperationStatus as DBOperationStatus, OperationType as DBOperationType
        
        # Map database status to UI status
        status_mapping = {
            DBOperationStatus.QUEUED.value: OperationStatus.PENDING,
            DBOperationStatus.RUNNING.value: OperationStatus.RUNNING,  
            DBOperationStatus.FINISHED.value: OperationStatus.COMPLETED,
            DBOperationStatus.ERROR.value: OperationStatus.FAILED,
            DBOperationStatus.CANCELLED.value: OperationStatus.CANCELLED,
        }
        
        # Map database type to UI type
        type_mapping = {
            DBOperationType.HYDRATION.value: OperationType.HYDRATION_SIMULATION,
            DBOperationType.MICROSTRUCTURE.value: OperationType.MICROSTRUCTURE_GENERATION,
            DBOperationType.ANALYSIS.value: OperationType.PROPERTY_CALCULATION,
            DBOperationType.EXPORT.value: OperationType.FILE_OPERATION,
            DBOperationType.IMPORT.value: OperationType.FILE_OPERATION,
        }
        
        # Convert status and type
        ui_status = status_mapping.get(db_op.status, OperationStatus.PENDING)
        ui_type = type_mapping.get(db_op.type, OperationType.BATCH_OPERATION)
        
        # Calculate progress (simplified - can be enhanced)
        progress = 0.0
        if ui_status == OperationStatus.COMPLETED:
            progress = 1.0
        elif ui_status == OperationStatus.RUNNING:
            progress = 0.5  # Rough estimate
        
        # Create UI operation
        return Operation(
            id=db_op.name,  # Use name as ID
            name=db_op.name,
            operation_type=ui_type,
            status=ui_status,
            progress=progress,
            start_time=db_op.start,
            end_time=db_op.finish,
            paused_time=None,
            estimated_duration=None,
            current_step="",
            total_steps=0,
            completed_steps=0,
            cpu_usage=0.0,
            memory_usage=0.0,
            disk_usage=0.0,
            error_message=None,  # Operation model doesn't have error_message field
            log_entries=[],
            metadata={"source": "database", "output_directory": f"Operations/{db_op.name}"}
        )
    
    def _refresh_operations_from_database(self) -> None:
        """Refresh operations from database to pick up new operations."""
        try:
            self.logger.debug("Refreshing operations from database...")
            operation_service = self.service_container.operation_service
            
            # Get all operations from database
            db_operations = operation_service.get_all()
            
            # Convert database operations to UI operations
            new_operations_count = 0
            for db_op in db_operations:
                try:
                    ui_operation = self._convert_db_operation_to_ui_operation(db_op)
                    
                    # Only add if not already loaded
                    if ui_operation.id not in self.operations:
                        self.operations[ui_operation.id] = ui_operation
                        new_operations_count += 1
                        self.logger.info(f"Added new database operation: {ui_operation.name}")
                    else:
                        # Update status of existing operations from database
                        existing = self.operations[ui_operation.id]
                        status_changed = False
                        
                        # Compare status (handle both enum and string values)
                        existing_status = existing.status.value if hasattr(existing.status, 'value') else str(existing.status)
                        new_status = ui_operation.status.value if hasattr(ui_operation.status, 'value') else str(ui_operation.status)
                        
                        if existing_status != new_status:
                            existing.status = ui_operation.status
                            existing.progress = ui_operation.progress
                            existing.end_time = ui_operation.end_time
                            status_changed = True
                            self.logger.info(f"Updated operation status: {ui_operation.name} -> {new_status}")
                        
                        # Also check if progress or end_time changed without status change
                        if not status_changed and (existing.progress != ui_operation.progress or existing.end_time != ui_operation.end_time):
                            existing.progress = ui_operation.progress
                            existing.end_time = ui_operation.end_time
                            self.logger.debug(f"Updated operation details: {ui_operation.name}")
                            
                except Exception as e:
                    self.logger.warning(f"Failed to convert database operation {db_op.name}: {e}")
            
            if new_operations_count > 0:
                self.logger.info(f"Added {new_operations_count} new operations from database")
                # Trigger UI update for new operations
                GLib.idle_add(self._update_operations_list)
                
        except Exception as e:
            self.logger.error(f"Failed to refresh operations from database: {e}")
    
    def _save_operations_periodically(self) -> None:
        """Save operations periodically (called from monitoring loop)."""
        # Save every 5 minutes or when operations change significantly
        if hasattr(self, '_last_save_time'):
            time_since_save = time.time() - self._last_save_time
            if time_since_save < 300:  # 5 minutes
                return
        
        # Check if there are completed operations since last save
        completed_ops = [op for op in self.operations.values() 
                        if op.status in [OperationStatus.COMPLETED, OperationStatus.FAILED, OperationStatus.CANCELLED]]
        
        if completed_ops:
            self._save_operations_to_file()
            self._last_save_time = time.time()
            
            # Also refresh results analysis when operations complete
            try:
                self._refresh_results_analysis()
            except Exception as e:
                self.logger.warning(f"Error refreshing results analysis: {e}")

    def _has_3d_results(self, operation) -> bool:
        """Check if operation has 3D microstructure results (.img files)."""
        try:
            # Check for output_dir in metadata or try to construct from operation name
            output_dir = None
            if hasattr(operation, 'output_dir') and operation.output_dir:
                output_dir = operation.output_dir
            elif hasattr(operation, 'metadata') and operation.metadata and 'output_directory' in operation.metadata:
                output_dir = operation.metadata['output_directory']
            else:
                # Try to construct from operation name
                project_root = Path(__file__).parent.parent.parent.parent.parent
                operations_dir = project_root / "Operations"
                potential_folder = operations_dir / operation.name
                if potential_folder.exists():
                    output_dir = str(potential_folder)
            
            if not output_dir:
                return False
            
            output_path = Path(output_dir)
            if not output_path.exists():
                return False
            
            # Look for any .img files (both hydration time-series and regular microstructures)
            # Time-series hydration files (*.img.XXXh.XX.XXX)
            hydration_img_files = list(output_path.glob("*.img.*h.*.*"))
            
            # Final hydrated microstructures (HydrationOf_*.img.*.*)
            final_img_files = list(output_path.glob("HydrationOf_*.img.*.*"))
            
            # Regular microstructure files (*.img)
            regular_img_files = list(output_path.glob("*.img"))
            
            # Return true if any .img files exist
            return len(hydration_img_files) > 0 or len(final_img_files) > 0 or len(regular_img_files) > 0
            
        except Exception as e:
            self.logger.error(f"Error checking for 3D results: {e}")
            return False
    
    def _has_csv_data(self, operation) -> bool:
        """Check if operation has CSV data files for plotting."""
        try:
            # Check for output_dir in metadata or try to construct from operation name
            output_dir = None
            if hasattr(operation, 'output_dir') and operation.output_dir:
                output_dir = operation.output_dir
            elif hasattr(operation, 'metadata') and operation.metadata and 'output_directory' in operation.metadata:
                output_dir = operation.metadata['output_directory']
            else:
                # Try to construct from operation name
                project_root = Path(__file__).parent.parent.parent.parent
                operations_dir = project_root / "Operations"
                potential_folder = operations_dir / operation.name
                if potential_folder.exists():
                    output_dir = str(potential_folder)
            
            if not output_dir:
                return False
            
            output_path = Path(output_dir)
            if not output_path.exists():
                return False
            
            # Look for CSV files (data tables from simulations)
            csv_files = list(output_path.glob("*.csv"))
            
            return len(csv_files) > 0
            
        except Exception as e:
            self.logger.error(f"Error checking for CSV data: {e}")
            return False

    def _on_view_3d_results_clicked(self, button) -> None:
        """Handle View 3D Results button click."""
        selected_operation = self._get_selected_operation()
        if not selected_operation:
            return
        
        try:
            # Import here to avoid circular imports
            from app.windows.dialogs.hydration_results_viewer import HydrationResultsViewer
            
            # Create and show the 3D results viewer dialog
            viewer = HydrationResultsViewer(
                parent=self.get_toplevel(),
                operation=selected_operation
            )
            viewer.run()
            viewer.destroy()
            
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
        selected_operation = self._get_selected_operation()
        if not selected_operation:
            return
        
        try:
            # Import here to avoid circular imports
            from app.windows.dialogs.data_plotter import DataPlotter
            
            # Create and show the data plotting dialog
            plotter = DataPlotter(
                parent=self.get_toplevel(),
                operation=selected_operation
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


# Register the widget
GObject.type_register(OperationsMonitoringPanel)
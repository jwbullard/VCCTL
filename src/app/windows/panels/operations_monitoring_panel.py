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
    
    @property
    def duration(self) -> Optional[timedelta]:
        """Get operation duration."""
        if self.start_time:
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
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert operation to dictionary for JSON serialization."""
        data = asdict(self)
        # Convert datetime objects to ISO strings
        if self.start_time:
            data['start_time'] = self.start_time.isoformat()
        if self.end_time:
            data['end_time'] = self.end_time.isoformat()
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
        start_button = Gtk.ToolButton()
        start_button.set_icon_name("media-playback-start")
        start_button.set_label("Start")
        start_button.set_tooltip_text("Start new operation")
        start_button.connect('clicked', self._on_start_operation_clicked)
        toolbar.insert(start_button, -1)
        
        # Stop operation button
        stop_button = Gtk.ToolButton()
        stop_button.set_icon_name("media-playback-stop")
        stop_button.set_label("Stop")
        stop_button.set_tooltip_text("Stop selected operation")
        stop_button.connect('clicked', self._on_stop_operation_clicked)
        toolbar.insert(stop_button, -1)
        
        # Pause operation button
        pause_button = Gtk.ToolButton()
        pause_button.set_icon_name("media-playback-pause")
        pause_button.set_label("Pause")
        pause_button.set_tooltip_text("Pause selected operation")
        pause_button.connect('clicked', self._on_pause_operation_clicked)
        toolbar.insert(pause_button, -1)
        
        # Separator
        toolbar.insert(Gtk.SeparatorToolItem(), -1)
        
        # Clear completed button
        clear_button = Gtk.ToolButton()
        clear_button.set_icon_name("edit-clear")
        clear_button.set_label("Clear")
        clear_button.set_tooltip_text("Clear completed operations")
        clear_button.connect('clicked', self._on_clear_completed_clicked)
        toolbar.insert(clear_button, -1)
        
        # Refresh button
        refresh_button = Gtk.ToolButton()
        refresh_button.set_icon_name("view-refresh")
        refresh_button.set_label("Refresh")
        refresh_button.set_tooltip_text("Refresh operation status")
        refresh_button.connect('clicked', self._on_refresh_clicked)
        toolbar.insert(refresh_button, -1)
        
        # Separator
        toolbar.insert(Gtk.SeparatorToolItem(), -1)
        
        # Settings button
        settings_button = Gtk.ToolButton()
        settings_button.set_icon_name("preferences-system")
        settings_button.set_label("Settings")
        settings_button.set_tooltip_text("Monitoring settings")
        settings_button.connect('clicked', self._on_settings_clicked)
        toolbar.insert(settings_button, -1)
        
        self.pack_start(toolbar, False, False, 0)
    
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
        self.operations_view.get_selection().set_mode(Gtk.SelectionMode.SINGLE)
        
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
        refresh_button.set_tooltip_text("Refresh Operations directory")
        refresh_button.connect('clicked', self._on_refresh_files_clicked)
        toolbar.insert(refresh_button, -1)
        
        # Open folder button
        open_folder_button = Gtk.ToolButton()
        open_folder_button.set_icon_name("folder-open")
        open_folder_button.set_label("Open Folder")
        open_folder_button.set_tooltip_text("Open Operations directory in file manager")
        open_folder_button.connect('clicked', self._on_open_operations_folder_clicked)
        toolbar.insert(open_folder_button, -1)
        
        # Separator
        toolbar.insert(Gtk.SeparatorToolItem(), -1)
        
        # Delete operation button
        delete_button = Gtk.ToolButton()
        delete_button.set_icon_name("edit-delete")
        delete_button.set_label("Delete")
        delete_button.set_tooltip_text("Delete selected operation folder")
        delete_button.connect('clicked', self._on_delete_operation_clicked)
        toolbar.insert(delete_button, -1)
        
        tab_box.pack_start(toolbar, False, False, 0)
        
        # Create paned layout - file tree on left, file details on right
        files_paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        
        # File tree (left side)
        tree_frame = Gtk.Frame(label="Operations Directory")
        tree_scrolled = Gtk.ScrolledWindow()
        tree_scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        tree_scrolled.set_size_request(300, 400)
        
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
        preview_scrolled.set_size_request(300, 300)
        
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
        """Update operation status information."""
        # In a real implementation, this would query the actual operation services
        # For now, we'll simulate some operations for demonstration
        
        current_time = datetime.now()
        
        # Update existing operations
        for operation in self.operations.values():
            if operation.status == OperationStatus.RUNNING:
                # Simulate progress
                if operation.progress < 1.0:
                    operation.progress = min(1.0, operation.progress + 0.01)
                    operation.current_step = f"Processing step {operation.completed_steps + 1}"
                
                # Simulate completion
                if operation.progress >= 1.0:
                    operation.status = OperationStatus.COMPLETED
                    operation.end_time = current_time
                    operation.completed_steps = operation.total_steps
                    # Save immediately when operation completes
                    self._save_operations_to_file()
    
    def _update_ui(self) -> None:
        """Update the UI with current data."""
        try:
            # Update operations list
            self._update_operations_list()
            
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
            
            current_ops[operation.id] = [
                operation.id,                                                    # Column 0: ID
                operation.name,                                                  # Column 1: Name  
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
        model, treeiter = selection.get_selected()
        if treeiter:
            operation_id = model[treeiter][0]
            operation = self.operations.get(operation_id)
            if operation:
                self._update_operation_details(operation)
    
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
    
    def _on_refresh_clicked(self, button: Gtk.Button) -> None:
        """Handle refresh button click."""
        self._update_operations()
        self._update_ui()
    
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
        """Get the currently selected operation."""
        if not self.operations_view:
            return None
        
        selection = self.operations_view.get_selection()
        model, treeiter = selection.get_selected()
        if treeiter:
            operation_id = model[treeiter][0]
            return self.operations.get(operation_id)
        return None
    
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
        """Stop an operation."""
        operation = self.operations.get(operation_id)
        if operation and operation.status == OperationStatus.RUNNING:
            operation.status = OperationStatus.CANCELLED
            operation.end_time = datetime.now()
            self._add_log_entry(f"Stopped operation: {operation.name}")
            self._update_operations_list()
    
    def _pause_operation(self, operation_id: str) -> None:
        """Pause an operation."""
        operation = self.operations.get(operation_id)
        if operation and operation.status == OperationStatus.RUNNING:
            operation.status = OperationStatus.PAUSED
            self._add_log_entry(f"Paused operation: {operation.name}")
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
        try:
            self.files_store.clear()
            
            # Get the Operations directory path
            operations_dir = Path.cwd() / "Operations"
            
            if not operations_dir.exists():
                # Add a message that Operations directory doesn't exist
                self.files_store.append(None, ["No Operations directory found", "", "info", "", ""])
                return
            
            # Add root Operations folder
            root_iter = self.files_store.append(None, ["Operations", str(operations_dir), "folder", "", ""])
            
            # Load operation directories
            try:
                operation_dirs = sorted([d for d in operations_dir.iterdir() if d.is_dir()])
                for op_dir in operation_dirs:
                    self._add_operation_folder(root_iter, op_dir)
                    
                # Expand the root by default
                self.files_view.expand_row(self.files_store.get_path(root_iter), False)
                
            except Exception as e:
                self.logger.error(f"Error loading operation directories: {e}")
                self.files_store.append(root_iter, [f"Error: {e}", "", "error", "", ""])
                
        except Exception as e:
            self.logger.error(f"Error loading operations files: {e}")
            self.files_store.append(None, [f"Error loading files: {e}", "", "error", "", ""])
    
    def _add_operation_folder(self, parent_iter, op_dir: Path) -> None:
        """Add an operation folder and its files to the tree."""
        try:
            # Get folder info
            stat_info = op_dir.stat()
            modified_time = datetime.fromtimestamp(stat_info.st_mtime).strftime("%Y-%m-%d %H:%M")
            
            # Add operation folder
            folder_iter = self.files_store.append(parent_iter, [
                op_dir.name,
                str(op_dir),
                "folder", 
                "",
                modified_time
            ])
            
            # Add files in the operation directory
            try:
                files = sorted(op_dir.iterdir())
                for file_path in files:
                    if file_path.is_file():
                        self._add_file_item(folder_iter, file_path)
                        
            except Exception as e:
                self.logger.error(f"Error loading files in {op_dir}: {e}")
                self.files_store.append(folder_iter, [f"Error loading files: {e}", "", "error", "", ""])
                
        except Exception as e:
            self.logger.error(f"Error adding operation folder {op_dir}: {e}")
    
    def _add_file_item(self, parent_iter, file_path: Path) -> None:
        """Add a file item to the tree."""
        try:
            stat_info = file_path.stat()
            file_size = self._format_file_size(stat_info.st_size)
            modified_time = datetime.fromtimestamp(stat_info.st_mtime).strftime("%Y-%m-%d %H:%M")
            
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
            self.logger.error(f"Error adding file {file_path}: {e}")
    
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
        """Load operations from JSON file."""
        try:
            self.logger.info(f"Attempting to load operations from {self.operations_file}")
            
            if not self.operations_file.exists():
                self.logger.info("No operations history file found - starting fresh")
                return
            
            with open(self.operations_file, 'r') as f:
                data = json.load(f)
            
            self.logger.info(f"Found operations file with {len(data.get('operations', {}))} operations")
            
            # Load operations
            operations_data = data.get('operations', {})
            for op_id, op_data in operations_data.items():
                try:
                    operation = Operation.from_dict(op_data)
                    self.operations[op_id] = operation
                except Exception as e:
                    self.logger.warning(f"Failed to load operation {op_id}: {e}")
            
            # Restore operation counter
            self.operation_counter = data.get('operation_counter', 0)
            
            self.logger.info(f"Successfully loaded {len(self.operations)} operations from {self.operations_file}")
            
            # Update UI with loaded operations
            if self.operations:
                self._update_operations_list()
                self._update_performance_metrics()
            
        except Exception as e:
            self.logger.error(f"Failed to load operations from file: {e}", exc_info=True)
    
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


# Register the widget
GObject.type_register(OperationsMonitoringPanel)
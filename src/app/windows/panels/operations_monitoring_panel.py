#!/usr/bin/env python3
"""
Operations Monitoring Panel for VCCTL

Provides real-time monitoring and management of simulation operations,
including progress tracking, resource usage, and operation controls.
"""

import gi
import logging
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
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
        
        # Monitoring control
        self.monitoring_active = False
        self.update_interval = 1.0  # seconds
        self.monitor_thread: Optional[threading.Thread] = None
        
        # UI components
        self.operations_store: Optional[Gtk.ListStore] = None
        self.operations_view: Optional[Gtk.TreeView] = None
        self.resource_charts: Dict[str, Any] = {}
        
        # Setup UI
        self._setup_ui()
        self._connect_signals()
        
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
            ("Name", 0, 150),
            ("Type", 1, 120),
            ("Status", 2, 80),
            ("Progress", 3, 100),
            ("Duration", 4, 80),
            ("Current Step", 5, 150),
            ("Resources", 6, 100)
        ]
        
        for title, col_id, width in columns:
            if col_id == 3:  # Progress column
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
                
                # Update UI
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
    
    def _update_ui(self) -> None:
        """Update the UI with current data."""
        try:
            # Update operations list
            self._update_operations_list()
            
            # Update system resources display
            self._update_system_resources_display()
            
            # Update status bar
            active_ops = len([op for op in self.operations.values() 
                            if op.status in [OperationStatus.RUNNING, OperationStatus.PENDING]])
            self.status_bar.pop(self.status_context)
            self.status_bar.push(self.status_context, 
                               f"Monitoring active - {active_ops} active operations")
            
        except Exception as e:
            self.logger.error(f"Error updating UI: {e}")
    
    def _update_operations_list(self) -> None:
        """Update the operations list view."""
        if not self.operations_store:
            return
        
        # Clear and rebuild the store
        self.operations_store.clear()
        
        for operation in self.operations.values():
            duration_str = ""
            if operation.duration:
                total_seconds = int(operation.duration.total_seconds())
                hours, remainder = divmod(total_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            
            resource_str = f"CPU: {operation.cpu_usage:.1f}% MEM: {operation.memory_usage:.0f}MB"
            
            self.operations_store.append([
                operation.id,
                operation.name,
                operation.operation_type.value.replace('_', ' ').title(),
                operation.status.value.title(),
                operation.progress_percentage,
                duration_str,
                operation.current_step,
                resource_str
            ])
    
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
    
    def _update_status(self, message: str) -> None:
        """Update status bar message."""
        self.status_bar.pop(self.status_context)
        self.status_bar.push(self.status_context, message)
    
    def cleanup(self) -> None:
        """Cleanup resources."""
        self._stop_monitoring()
        self.logger.info("Operations monitoring panel cleanup completed")


# Register the widget
GObject.type_register(OperationsMonitoringPanel)
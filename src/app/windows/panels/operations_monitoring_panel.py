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
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import Gtk, GObject, Pango, GLib, GdkPixbuf

if TYPE_CHECKING:
    from app.windows.main_window import VCCTLMainWindow

from app.services.service_container import get_service_container
from app.utils.icon_utils import set_tool_button_custom_icon, create_button_with_icon
from app.help.panel_help_button import create_panel_help_button


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
    ELASTIC_MODULI_CALCULATION = "elastic_moduli_calculation"
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
    
    def pause_process(self) -> bool:
        """Pause the operation's process using SIGSTOP signal."""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"PAUSE DEBUG: pause_process called for {self.name}")
        logger.info(f"PAUSE DEBUG: self.process = {self.process}")
        logger.info(f"PAUSE DEBUG: self.pid = {self.pid}")
        
        try:
            if self.process and self.process.poll() is None:
                # Process is still running, pause it
                logger.info(f"PAUSE DEBUG: Using process object to send SIGSTOP")
                self.process.send_signal(signal.SIGSTOP)
                logger.info(f"PAUSE DEBUG: SIGSTOP sent successfully via process object")
                return True
            elif self.pid:
                # Try using stored PID
                logger.info(f"PAUSE DEBUG: Using PID {self.pid} to send SIGSTOP")
                os.kill(self.pid, signal.SIGSTOP)
                logger.info(f"PAUSE DEBUG: SIGSTOP sent successfully via PID")
                return True
            else:
                logger.error(f"PAUSE DEBUG: No process or PID available!")
        except (ProcessLookupError, PermissionError, OSError) as e:
            # Process may have ended or we don't have permission
            logger.error(f"PAUSE DEBUG: Exception while pausing: {e}")
            return False
        logger.error(f"PAUSE DEBUG: Reached end of pause_process without sending signal")
        return False
    
    def resume_process(self) -> bool:
        """Resume the operation's process using SIGCONT signal."""
        try:
            if self.process and self.process.poll() is None:
                # Process is still running (paused), resume it
                self.process.send_signal(signal.SIGCONT)
                return True
            elif self.pid:
                # Try using stored PID
                os.kill(self.pid, signal.SIGCONT)
                return True
        except (ProcessLookupError, PermissionError, OSError) as e:
            # Process may have ended or we don't have permission
            return False
        return False
    
    @property
    def duration(self) -> Optional[timedelta]:
        """Get operation duration (frozen when paused)."""
        if self.start_time:
            if self.status == OperationStatus.PAUSED and self.paused_time:
                # Return duration up to pause time
                return self.paused_time - self.start_time
            else:
                # Normal duration calculation - ensure timezone consistency
                end = self.end_time
                if end is None:
                    # For running operations, detect if start_time is likely UTC stored as naive
                    from datetime import timezone
                    
                    # Check if start_time appears to be UTC stored as naive (common pattern)
                    # If start_time is more than 2 hours ahead of local time, it's probably UTC stored as naive
                    local_now = datetime.now()
                    if self.start_time.tzinfo is None:
                        time_diff_hours = (self.start_time - local_now).total_seconds() / 3600
                        if time_diff_hours > 2:  # start_time is significantly ahead of local time
                            # start_time is probably UTC stored as naive, so use UTC now
                            end = datetime.now(timezone.utc).replace(tzinfo=None)  # Make it naive too
                        else:
                            # start_time is likely local time stored as naive
                            end = local_now
                    else:
                        # start_time is timezone-aware, use timezone-aware now
                        end = datetime.now(timezone.utc)
                
                # Final timezone consistency check (both should now be compatible)
                if self.start_time.tzinfo is not None and end.tzinfo is None:
                    # start_time is timezone-aware, end is naive - make end timezone-aware
                    from datetime import timezone
                    end = end.replace(tzinfo=timezone.utc)
                elif self.start_time.tzinfo is None and end.tzinfo is not None:
                    # start_time is naive, end is timezone-aware - make both naive
                    end = end.replace(tzinfo=None)
                
                duration = end - self.start_time
                
                # Debug negative durations
                if duration.total_seconds() < 0:
                    print(f"NEGATIVE DURATION DEBUG: {self.name}")
                    print(f"  Start time: {self.start_time} (tzinfo: {self.start_time.tzinfo})")
                    print(f"  End time: {end} (tzinfo: {end.tzinfo})")
                    print(f"  Original end_time: {self.end_time}")
                    print(f"  Duration: {duration}")
                
                return duration
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
    
    def parse_genmic_progress(self, output_line: str) -> bool:
        """Parse genmic progress updates from stdout/stderr line. Returns True if progress was updated."""
        try:
            if not output_line.startswith("GENMIC_PROGRESS:"):
                return False
            
            # Parse: GENMIC_PROGRESS: stage=particle_placement progress=0.30 message=Placed 3000 particles
            content = output_line.replace("GENMIC_PROGRESS:", "").strip()
            
            # Extract key=value pairs
            progress_data = {}
            parts = content.split()
            for part in parts:
                if "=" in part and not part.startswith("message="):
                    key, value = part.split("=", 1)
                    progress_data[key] = value
            
            # Handle message separately (may contain spaces)
            if "message=" in content:
                message_start = content.find("message=") + 8
                progress_data["message"] = content[message_start:].strip()
            
            # Update operation progress
            if "progress" in progress_data:
                try:
                    new_progress = float(progress_data["progress"])
                    # Only update if progress value is reasonable (0.0 to 1.0 range)
                    # Ignore astronomical values that seem to be particle counts, not percentages
                    if 0.0 <= new_progress <= 1.0:
                        self.progress = new_progress
                        # Progress update successful - no need to log every update
                        pass
                    else:
                        # Invalid progress values are silently ignored
                        pass
                except ValueError:
                    pass
            
            # Update stage and message
            if "stage" in progress_data:
                self.current_step = progress_data.get("message", f"Stage: {progress_data['stage']}")
                
                # Special handling for completion
                if progress_data["stage"] == "complete":
                    self.status = OperationStatus.COMPLETED
                    self.progress = 1.0
                    self.end_time = datetime.utcnow()
                    self.completed_steps = self.total_steps
                    return True
            
            return True
            
        except Exception as e:
            # If parsing fails, don't crash - just log and continue
            import logging
            logger = logging.getLogger(f'VCCTL.{self.__class__.__name__}')
            logger.warning(f"Error parsing genmic progress: {e}")
            return False
    
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
        # Manual serialization to avoid thread lock pickle issues
        data = {
            'id': self.id,
            'name': self.name,
            'operation_type': self.operation_type.value,
            'status': self.status.value,
            'progress': self.progress,
            'current_step': self.current_step,
            'total_steps': self.total_steps,
            'completed_steps': self.completed_steps,
            'cpu_usage': self.cpu_usage,
            'memory_usage': self.memory_usage,
            'disk_usage': self.disk_usage,
            'error_message': self.error_message,
            'metadata': self.metadata.copy() if self.metadata else {}
        }
        
        # Convert datetime objects to ISO strings
        if self.start_time:
            data['start_time'] = self.start_time.isoformat()
        else:
            data['start_time'] = None
            
        if self.end_time:
            data['end_time'] = self.end_time.isoformat()
        else:
            data['end_time'] = None
            
        if self.paused_time:
            data['paused_time'] = self.paused_time.isoformat()
        else:
            data['paused_time'] = None
            
        if self.estimated_duration:
            data['estimated_duration'] = self.estimated_duration.total_seconds()
        else:
            data['estimated_duration'] = None
            
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
        
        # Database-only persistence (JSON file no longer used)
        
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
        self._load_operations_from_database()
        
        # Start monitoring
        self._start_monitoring()
        
        # Initialize operation details tracking
        self._currently_displayed_operation = None

        # SIMPLE SOLUTION: Direct progress file reader every 5 seconds
        from gi.repository import GLib
        self._progress_timeout_id = GLib.timeout_add_seconds(5, self._simple_progress_update)

        self.logger.info("Operations monitoring panel initialized")

    def _create_header(self) -> None:
        """Create the panel header."""
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        header_box.set_margin_top(10)
        header_box.set_margin_bottom(5)
        header_box.set_margin_left(10)
        header_box.set_margin_right(10)

        # Title
        title_label = Gtk.Label()
        title_label.set_markup('<span size="large" weight="bold">Operations Monitoring</span>')
        title_label.set_halign(Gtk.Align.START)
        header_box.pack_start(title_label, False, False, 0)

        # Add context-specific help button
        help_button = create_panel_help_button('OperationsMonitoringPanel', self.main_window)
        header_box.pack_start(help_button, False, False, 5)

        # Spacer
        header_box.pack_start(Gtk.Box(), True, True, 0)

        self.pack_start(header_box, False, False, 0)

    def _setup_ui(self) -> None:
        """Setup the panel UI."""
        # Create header
        self._create_header()

        # Create toolbar
        self._create_toolbar()

        # Create main content area
        self._create_content_area()
        
        # Create status bar
        self._create_status_bar()
    
    def _create_toolbar(self) -> None:
        """Create the operations toolbar with custom SVG icons."""
        toolbar = Gtk.Toolbar()
        toolbar.set_style(Gtk.ToolbarStyle.BOTH_HORIZ)
        
        # Start operation button
        self.start_button = Gtk.ToolButton()
        self.start_button.set_icon_name("play")
        set_tool_button_custom_icon(self.start_button, "play", 24)
        self.start_button.set_label("Start")
        self.start_button.set_tooltip_text("Launch a new microstructure generation or hydration simulation")
        self.start_button.connect('clicked', self._on_start_operation_clicked)
        toolbar.insert(self.start_button, -1)
        
        # Stop operation button
        self.stop_button = Gtk.ToolButton()
        self.stop_button.set_icon_name("stop")
        set_tool_button_custom_icon(self.stop_button, "stop", 24)
        self.stop_button.set_label("Stop")
        self.stop_button.set_tooltip_text("Terminate the selected running operation immediately")
        self.stop_button.connect('clicked', self._on_stop_operation_clicked)
        toolbar.insert(self.stop_button, -1)
        
        # Pause operation button
        self.pause_button = Gtk.ToolButton()
        self.pause_button.set_icon_name("pause")
        set_tool_button_custom_icon(self.pause_button, "pause", 24)
        self.pause_button.set_label("Pause")
        self.pause_button.set_tooltip_text("Pause running operations or resume paused operations")
        self.pause_button.connect('clicked', self._on_pause_operation_clicked)
        toolbar.insert(self.pause_button, -1)
        
        # Separator
        toolbar.insert(Gtk.SeparatorToolItem(), -1)
        
        # Clear completed button
        self.clear_button = Gtk.ToolButton()
        self.clear_button.set_icon_name("erase")
        set_tool_button_custom_icon(self.clear_button, "edit-clear", 24)
        self.clear_button.set_label("Clear")
        self.clear_button.set_tooltip_text("Remove all completed, failed, and cancelled operations from the list")
        self.clear_button.connect('clicked', self._on_clear_completed_clicked)
        toolbar.insert(self.clear_button, -1)
        
        # Delete operation button
        self.delete_button = Gtk.ToolButton()
        self.delete_button.set_icon_name("trash-can")
        set_tool_button_custom_icon(self.delete_button, "trash-can", 24)
        self.delete_button.set_label("Delete")
        self.delete_button.set_tooltip_text("Permanently delete selected operation(s) and all their output files")
        self.delete_button.connect('clicked', self._on_delete_selected_operation_clicked)
        toolbar.insert(self.delete_button, -1)
        
        # Refresh button
        self.refresh_button = Gtk.ToolButton()
        self.refresh_button.set_icon_name("refresh")
        set_tool_button_custom_icon(self.refresh_button, "refresh", 24)
        self.refresh_button.set_label("Refresh")
        self.refresh_button.set_tooltip_text("Update operation status and check for new operations in the Operations folder")
        self.refresh_button.connect('clicked', self._on_refresh_clicked)
        toolbar.insert(self.refresh_button, -1)
        
        # Clean Duplicates button
        self.clean_duplicates_button = Gtk.ToolButton()
        self.clean_duplicates_button.set_icon_name("erase")
        set_tool_button_custom_icon(self.clean_duplicates_button, "edit-clear", 24)
        self.clean_duplicates_button.set_label("Clean Duplicates")
        self.clean_duplicates_button.set_tooltip_text("Remove duplicate operations from the list")
        self.clean_duplicates_button.set_is_important(True)  # Force label to show
        self.clean_duplicates_button.connect('clicked', self._on_clean_duplicates_clicked)
        toolbar.insert(self.clean_duplicates_button, -1)

        # Sync with Filesystem button
        self.sync_filesystem_button = Gtk.ToolButton()
        self.sync_filesystem_button.set_icon_name("folder-sync")
        set_tool_button_custom_icon(self.sync_filesystem_button, "view-refresh", 24)
        self.sync_filesystem_button.set_label("Sync with Filesystem")
        self.sync_filesystem_button.set_tooltip_text("Remove database records for operations with no folders, and clean up orphaned folders")
        self.sync_filesystem_button.set_is_important(True)  # Force label to show
        self.sync_filesystem_button.connect('clicked', self._on_sync_filesystem_clicked)
        toolbar.insert(self.sync_filesystem_button, -1)

        # Note: View 3D Results and Plot Data buttons moved to dedicated Results panel

        # Separator
        toolbar.insert(Gtk.SeparatorToolItem(), -1)
        
        # Settings button
        self.settings_button = Gtk.ToolButton()
        self.settings_button.set_icon_name("settings")
        set_tool_button_custom_icon(self.settings_button, "settings", 24)
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
            
            # Note: 3D Results and Plot Data functionality moved to dedicated Results panel
            
            # Refresh, Clean Duplicates, Sync Filesystem, and Settings: Always enabled
            self.refresh_button.set_sensitive(True)
            self.clean_duplicates_button.set_sensitive(True)
            self.sync_filesystem_button.set_sensitive(True)
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
        list_frame = Gtk.Frame(label="Operation Status")
        
        # Create list store: ID, Name, Type, Status, Progress, Duration, Started, Resources
        self.operations_store = Gtk.ListStore(
            str,    # Operation ID
            str,    # Name
            str,    # Type
            str,    # Status
            float,  # Progress (0-100)
            str,    # Duration
            str,    # Started (date/time)
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
            ("Started", 6, 120),      # Column 6: Started (date/time)
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
            
            # Make column sortable by clicking on header
            column.set_clickable(True)
            column.set_sort_column_id(col_id)
            
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
        
        # System Resources tab - HIDDEN to free up horizontal space
        # self._create_system_resources_tab()
        
        # Operation Logs tab
        self._create_operation_logs_tab()
        
        # Performance Metrics tab - HIDDEN to free up horizontal space
        # self._create_performance_metrics_tab()
        
        # Operations Files tab - HIDDEN (functionality available in main Files tab)
        # self._create_operations_files_tab()
        
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
        
        # Note: Step progress removed to avoid duplicate information with Current Step field above
        
        progress_frame.add(progress_box)
        tab_box.pack_start(progress_frame, False, False, 0)
        
        # Control buttons frame
        controls_frame = Gtk.Frame(label="Operation Controls")
        controls_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        controls_box.set_margin_left(10)
        controls_box.set_margin_right(10)
        controls_box.set_margin_top(5)
        controls_box.set_margin_bottom(5)
        
        self.control_pause_button = create_button_with_icon("Pause", "pause", 16)
        self.control_pause_button.connect('clicked', self._on_pause_operation_clicked)
        controls_box.pack_start(self.control_pause_button, False, False, 0)
        
        self.control_stop_button = create_button_with_icon("Stop", "stop", 16)
        self.control_stop_button.connect('clicked', self._on_stop_operation_clicked)
        controls_box.pack_start(self.control_stop_button, False, False, 0)
        
        # Set Priority button hidden - functionality not implemented
        # self.control_priority_button = Gtk.Button(label="Set Priority")
        # self.control_priority_button.connect('clicked', self._on_set_priority_clicked)
        # controls_box.pack_start(self.control_priority_button, False, False, 0)
        
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
        clear_logs_button = create_button_with_icon("Clear Logs", "erase", 16)
        clear_logs_button.connect('clicked', self._on_clear_logs_clicked)
        controls_box.pack_start(clear_logs_button, False, False, 0)
        
        # Export logs button
        export_logs_button = create_button_with_icon("Export Logs", "export", 16)
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
        
        # Refresh button - use Carbon icon
        refresh_button = Gtk.ToolButton()
        refresh_icon = self._load_carbon_icon("restart", 32)
        if refresh_icon:
            # Scale down to toolbar size (24px)
            scaled_icon = refresh_icon.scale_simple(24, 24, GdkPixbuf.InterpType.BILINEAR)
            refresh_button.set_icon_widget(Gtk.Image.new_from_pixbuf(scaled_icon))
        else:
            refresh_button.set_icon_name("view-refresh")  # Fallback to GTK icon
        refresh_button.set_label("Refresh")
        refresh_button.set_tooltip_text("Scan Operations directory for new files and updated operation results")
        refresh_button.connect('clicked', self._on_refresh_files_clicked)
        toolbar.insert(refresh_button, -1)
        
        # Open folder button - use Carbon icon
        open_folder_button = Gtk.ToolButton()
        folder_icon = self._load_carbon_icon("folder--open", 32)
        if folder_icon:
            # Scale down to toolbar size (24px)
            scaled_icon = folder_icon.scale_simple(24, 24, GdkPixbuf.InterpType.BILINEAR)
            open_folder_button.set_icon_widget(Gtk.Image.new_from_pixbuf(scaled_icon))
        else:
            open_folder_button.set_icon_name("folder")  # Fallback to GTK icon
        open_folder_button.set_label("Open Folder")
        open_folder_button.set_tooltip_text("Open the Operations directory in your system's file manager")
        open_folder_button.connect('clicked', self._on_open_operations_folder_clicked)
        toolbar.insert(open_folder_button, -1)
        
        # Separator
        toolbar.insert(Gtk.SeparatorToolItem(), -1)
        
        # Delete operation button - use Carbon icon
        delete_button = Gtk.ToolButton()
        delete_icon = self._load_carbon_icon("trash-can", 32)
        if delete_icon:
            # Scale down to toolbar size (24px)
            scaled_icon = delete_icon.scale_simple(24, 24, GdkPixbuf.InterpType.BILINEAR)
            delete_button.set_icon_widget(Gtk.Image.new_from_pixbuf(scaled_icon))
        else:
            delete_button.set_icon_name("edit-delete")  # Fallback to GTK icon
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
        
        # Create file tree store: Icon, Name, Path, Type, Size, Modified
        self.files_store = Gtk.TreeStore(GdkPixbuf.Pixbuf, str, str, str, str, str)
        
        # Create tree view
        self.files_view = Gtk.TreeView(model=self.files_store)
        self.files_view.set_rules_hint(True)
        self.files_view.get_selection().set_mode(Gtk.SelectionMode.SINGLE)
        self.files_view.get_selection().connect('changed', self._on_file_selection_changed)
        
        # Name column with icon
        name_column = Gtk.TreeViewColumn("Name")
        
        # Add icon renderer
        icon_renderer = Gtk.CellRendererPixbuf()
        name_column.pack_start(icon_renderer, False)
        name_column.add_attribute(icon_renderer, "pixbuf", 0)
        
        # Add text renderer
        name_renderer = Gtk.CellRendererText()
        name_column.pack_start(name_renderer, True)
        name_column.add_attribute(name_renderer, "text", 1)
        name_column.set_expand(True)
        self.files_view.append_column(name_column)
        
        # Size column
        size_column = Gtk.TreeViewColumn("Size")
        size_renderer = Gtk.CellRendererText()
        size_column.pack_start(size_renderer, False)
        size_column.add_attribute(size_renderer, "text", 4)  # Updated column index
        size_column.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
        size_column.set_fixed_width(80)
        self.files_view.append_column(size_column)
        
        # Modified column
        modified_column = Gtk.TreeViewColumn("Modified")
        modified_renderer = Gtk.CellRendererText()
        modified_column.pack_start(modified_renderer, False)
        modified_column.add_attribute(modified_renderer, "text", 5)  # Updated column index
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
        refresh_analysis_btn = create_button_with_icon("Refresh Analysis", "refresh", 16)
        refresh_analysis_btn.set_tooltip_text("Recalculate operation success rates, performance metrics, and quality assessments")
        refresh_analysis_btn.connect('clicked', self._on_refresh_analysis_clicked)
        controls_box.pack_start(refresh_analysis_btn, False, False, 0)
        
        # Export report button
        export_report_btn = create_button_with_icon("Export Report", "export", 16)
        export_report_btn.set_tooltip_text("Generate and save a comprehensive operations analysis report to file")
        export_report_btn.connect('clicked', self._on_export_report_clicked)
        controls_box.pack_start(export_report_btn, False, False, 0)
        
        # Cleanup old results button
        cleanup_btn = create_button_with_icon("Cleanup Old Results", "erase", 16)
        cleanup_btn.set_tooltip_text("Archive or delete old operation files to free up disk space (with confirmation)")
        cleanup_btn.connect('clicked', self._on_cleanup_results_clicked)
        controls_box.pack_start(cleanup_btn, False, False, 0)
        
        # Validation check button
        validate_btn = create_button_with_icon("Validate Results", "information", 16)
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
        from gi.repository import GLib

        # Cancel GLib progress update timeout
        if hasattr(self, '_progress_timeout_id') and self._progress_timeout_id:
            GLib.source_remove(self._progress_timeout_id)
            self._progress_timeout_id = None
            self.logger.info("Cancelled progress update timeout")

        if self.monitoring_active:
            self.monitoring_active = False
            if self.monitor_thread:
                # Reduce timeout to 0.5 seconds for faster shutdown
                self.monitor_thread.join(timeout=0.5)
                if self.monitor_thread.is_alive():
                    self.logger.warning("Monitoring thread did not terminate in time, continuing shutdown")
            self.logger.info("Monitoring stopped")
    
    def _monitoring_loop(self) -> None:
        """Main monitoring loop with robust error handling and detailed logging."""
        loop_iteration = 0
        last_operation_count = 0
        last_running_count = 0
        
        self.logger.info("Monitoring loop started")
        
        while self.monitoring_active:
            try:
                loop_iteration += 1
                current_time = time.time()
                
                # Log periodic status to detect if monitoring is stuck
                if loop_iteration % 30 == 1:  # Every 30 seconds
                    running_ops = sum(1 for op in self.operations.values() 
                                     if op.status in [OperationStatus.RUNNING, OperationStatus.PAUSED])
                    self.logger.info(f"Monitoring loop iteration {loop_iteration}: {len(self.operations)} total operations, {running_ops} running")
                
                # Update system resources with error isolation
                try:
                    self._update_system_resources()
                except Exception as e:
                    self.logger.warning(f"System resources update failed: {e}")
                
                # Update operations - CRITICAL SECTION with detailed error handling
                try:
                    operations_before = len(self.operations)
                    running_before = sum(1 for op in self.operations.values() 
                                        if op.status in [OperationStatus.RUNNING, OperationStatus.PAUSED])
                    
                    self._update_operations()
                    
                    operations_after = len(self.operations)
                    running_after = sum(1 for op in self.operations.values() 
                                       if op.status in [OperationStatus.RUNNING, OperationStatus.PAUSED])
                    
                    # Log significant changes
                    if running_after != running_before or (loop_iteration % 60 == 1):
                        self.logger.info(f"Operations update: {running_before}→{running_after} running, {operations_before}→{operations_after} total")
                        
                        # Log details of running operations
                        for op in self.operations.values():
                            if op.status in [OperationStatus.RUNNING, OperationStatus.PAUSED]:
                                self.logger.debug(f"  Running: {op.name} ({op.progress:.1%}) - {op.current_step}")
                    
                except Exception as e:
                    self.logger.error(f"CRITICAL: Operations update failed: {e}", exc_info=True)
                
                # Operations are saved directly to database in _update_operation_in_database()
                # No need for periodic file saving since we use database-only approach
                
                # Throttle UI updates to reduce blinking
                if current_time - self.last_ui_update >= self.ui_update_throttle:
                    self.last_ui_update = current_time
                    try:
                        GLib.idle_add(self._update_ui)
                    except Exception as e:
                        self.logger.warning(f"UI update scheduling failed: {e}")
                
                # Sleep until next update
                time.sleep(self.update_interval)
                
            except Exception as e:
                self.logger.error(f"CRITICAL: Monitoring loop iteration {loop_iteration} failed: {e}", exc_info=True)
                time.sleep(2.0)  # Longer pause on critical error to prevent spam
                
                # Recovery attempt - try to reload operations if monitoring is broken
                if loop_iteration % 10 == 0:  # Every 10 failures
                    try:
                        self.logger.info("Attempting recovery - reloading operations from database")
                        self._load_operations_from_database()
                    except Exception as recovery_e:
                        self.logger.error(f"Recovery attempt failed: {recovery_e}")
        
        self.logger.info("Monitoring loop ended")
    
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
            
            self.system_resources.timestamp = datetime.utcnow()
            
        except ImportError:
            # psutil not available, use dummy values
            self.system_resources.cpu_usage = 0.0
            self.system_resources.memory_usage = 0.0
            self.system_resources.memory_total = 1024.0
        except Exception as e:
            self.logger.warning(f"Failed to update system resources: {e}")
    
    def _update_operations(self) -> None:
        """Update operation status information by checking real processes."""
        current_time = datetime.utcnow()
        
        # Periodically refresh operations from database 
        # More frequent updates if we have running operations, less frequent otherwise
        if not hasattr(self, '_last_db_refresh'):
            self._last_db_refresh = current_time
        
        # Check if we have any running operations
        has_running_ops = any(op.status in [OperationStatus.RUNNING, OperationStatus.PENDING] for op in self.operations.values())
        refresh_interval = 10 if has_running_ops else 30  # 10 seconds if running ops, 30 seconds otherwise
        
        time_since_refresh = (current_time - self._last_db_refresh).total_seconds()
        if time_since_refresh >= refresh_interval:
            # Use thread-safe database refresh to avoid crashes
            try:
                self._safe_load_operations_from_database()
                self._last_db_refresh = current_time
            except Exception as e:
                self.logger.error(f"Database refresh failed safely: {e}")
                self._last_db_refresh = current_time  # Still update to prevent constant retries
        
        # Update existing operations based on actual process status
        for operation in self.operations.values():
            # Skip process monitoring for database-sourced operations that don't have process handles AND no stdout files
            # BUT still allow UI updates for running operations (they need duration/progress updates)
            is_database_sourced = hasattr(operation, 'metadata') and operation.metadata.get('source') == 'database'
            has_process_handle = hasattr(operation, 'process') and operation.process is not None
            
            # For database-sourced operations, check if they have files to monitor
            can_monitor_progress = False
            if is_database_sourced:
                self.logger.debug(f"Checking monitoring capability for database operation: {operation.name}, type: {operation.operation_type}")
                if operation.operation_type == OperationType.MICROSTRUCTURE_GENERATION:
                    # Check if stdout files exist for this operation
                    try:
                        import glob
                        import os
                        operation_name = operation.name
                        if operation_name.endswith(" Microstructure"):
                            base_name = operation_name.replace(" Microstructure", "")
                            # Phase 2: Clean naming - operation name is already clean, use as-is
                            folder_name = base_name
                        else:
                            # For non-microstructure operations, use name as-is
                            folder_name = operation_name

                            operations_dir = os.path.join("Operations", folder_name)
                            if os.path.exists(operations_dir):
                                # Check for both stdout files and progress files
                                stdout_files = glob.glob(os.path.join(operations_dir, "proc_*_stdout.txt"))
                                progress_file = os.path.join(operations_dir, "genmic_progress.txt")

                                if stdout_files or os.path.exists(progress_file):
                                    can_monitor_progress = True
                    except Exception as e:
                        pass
                elif operation.operation_type == OperationType.ELASTIC_MODULI_CALCULATION:
                    # Elastic operations should always be monitored for progress updates
                    can_monitor_progress = True
                    self.logger.debug(f"Elastic operation {operation.name} will be monitored for progress")
                elif operation.operation_type == OperationType.HYDRATION_SIMULATION:
                    # Hydration operations should always be monitored for progress updates
                    can_monitor_progress = True
                    self.logger.debug(f"Hydration operation {operation.name} will be monitored for progress")

            # Only skip if database-sourced AND no process handle AND no progress monitoring capability
            if is_database_sourced and not has_process_handle and not can_monitor_progress:
                self.logger.debug(f"Skipping monitoring for {operation.name}: db_sourced={is_database_sourced}, has_process={has_process_handle}, can_monitor={can_monitor_progress}")
                continue
            else:
                self.logger.debug(f"Will monitor {operation.name}: db_sourced={is_database_sourced}, has_process={has_process_handle}, can_monitor={can_monitor_progress}")
                
            if operation.status in [OperationStatus.RUNNING, OperationStatus.PAUSED]:
                # Note: Progress parsing is now handled by operation-specific methods below
                # (_update_microstructure_progress, _update_hydration_progress, _update_elastic_progress)
                # So we don't need to call _parse_operation_stdout here anymore

                # Check if process is still running (unless already marked complete by progress parser)
                if operation.status == OperationStatus.COMPLETED:
                    # Already completed by progress parser, skip further processing
                    continue
                    
                if not operation.is_process_running():
                    # Process has ended, determine if it completed successfully
                    self.logger.info(f"Process {operation.id} ({operation.name}) has ended")
                    
                    if operation.process and operation.process.returncode is not None:
                        return_code = operation.process.returncode
                        self.logger.info(f"Process {operation.id} exit code: {return_code}")

                        if return_code == 0:
                            # For microstructure operations, verify output files exist before marking complete
                            # (This is a fallback in case genmic doesn't send progress messages)
                            self.logger.info(f"Attempting to verify completion for {operation.name} (type: {operation.operation_type})")
                            verification_result = self._verify_operation_completion(operation)
                            self.logger.info(f"Verification result for {operation.name}: {verification_result}")

                            if verification_result:
                                operation.status = OperationStatus.COMPLETED
                                operation.progress = 1.0
                                operation.current_step = "Process completed successfully (verified by output files)"
                                self.logger.info(f"Process {operation.id} marked as COMPLETED via file verification (fallback)")
                            else:
                                # Process returned 0 but output files don't exist yet - keep running
                                self.logger.info(f"Process {operation.id} returned 0 but output files not ready - continuing to monitor")
                                continue
                        else:
                            self.logger.warning(f"Process {operation.id} ({operation.name}) exited with non-zero code: {return_code}")
                            self.logger.warning(f"Operation working_directory: {getattr(operation, 'working_directory', 'NOT SET')}")
                            # Before marking as failed, check if files actually exist (genmic might return non-zero but still succeed)
                            if operation.operation_type == OperationType.MICROSTRUCTURE_GENERATION:
                                verification_result = self._verify_operation_completion(operation)
                                self.logger.warning(f"File verification despite non-zero exit: {verification_result}")
                                if verification_result:
                                    self.logger.warning(f"Files exist despite non-zero exit code - marking as COMPLETED anyway")
                                    operation.status = OperationStatus.COMPLETED
                                    operation.progress = 1.0
                                    operation.current_step = "Process completed (files verified despite non-zero exit)"
                                else:
                                    operation.status = OperationStatus.FAILED
                                    operation.error_message = f"Process exited with code {return_code}"
                                    operation.current_step = "Process failed"
                            else:
                                operation.status = OperationStatus.FAILED
                                operation.error_message = f"Process exited with code {return_code}"
                                operation.current_step = "Process failed"
                                self.logger.warning(f"Process {operation.id} marked as FAILED with code {return_code}")
                    else:
                        # Process ended without proper exit code tracking - verify completion
                        if self._verify_operation_completion(operation):
                            self.logger.info(f"Process {operation.id} ended without return code - verified complete")
                            operation.status = OperationStatus.COMPLETED
                            operation.progress = 1.0
                            operation.current_step = "Process completed"
                        else:
                            self.logger.info(f"Process {operation.id} ended without return code - output files not ready, continuing monitor")
                            continue
                    
                    operation.end_time = current_time
                    operation.completed_steps = operation.total_steps
                    
                    # Close output file handles
                    operation.close_output_files()
                    
                    self._update_operation_in_database(operation)
                    
                elif operation.status == OperationStatus.RUNNING:
                    # Update process resource usage for running operations
                    process_info = operation.get_process_info()
                    if process_info:
                        operation.cpu_usage = process_info['cpu_percent']
                        operation.memory_usage = process_info['memory_mb']
                    
                    # Update progress based on operation type - All operations use JSON progress tracking
                    self.logger.debug(f"Updating progress for {operation.name}, type: {operation.operation_type}, status: {operation.status}")
                    if operation.operation_type == OperationType.MICROSTRUCTURE_GENERATION:
                        # Microstructure operations use genmic progress messages from stdout
                        self.logger.debug(f"Calling _update_microstructure_progress for {operation.name}")
                        self._update_microstructure_progress(operation)
                    elif operation.operation_type == OperationType.ELASTIC_MODULI_CALCULATION:
                        # Elastic operations use elastic_progress.json files
                        self.logger.debug(f"Calling _update_elastic_progress for {operation.name}")
                        self._update_elastic_progress(operation)
                    elif operation.operation_type == OperationType.HYDRATION_SIMULATION:
                        # Hydration operations use progress.json files
                        self._update_hydration_progress(operation)
                    else:
                        # Other operation types use generic JSON progress monitoring
                        self._update_generic_progress(operation)
        
        # Synchronize with active hydration simulations to get detailed progress
        self._sync_with_active_hydration_simulations()
    
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

    def _verify_operation_completion(self, operation) -> bool:
        """Verify that an operation has actually completed by checking for expected output files."""
        try:
            # For microstructure operations, check for expected output files
            if operation.operation_type == OperationType.MICROSTRUCTURE_GENERATION:
                # Use working directory from operation
                import os
                output_dir = operation.working_directory if hasattr(operation, 'working_directory') and operation.working_directory else None

                if not output_dir:
                    # Fallback: try to get operation directory
                    output_dir = self._get_operation_directory(operation)

                if not output_dir or not os.path.exists(output_dir):
                    self.logger.info(f"Output directory for {operation.name} not found - operation not complete")
                    return False

                self.logger.info(f"Verifying microstructure completion in: {output_dir}")

                # Check for expected output files (.img and .pimg)
                # Files are named with the operation name
                operation_name = operation.name
                img_file = os.path.join(output_dir, f"{operation_name}.img")
                pimg_file = os.path.join(output_dir, f"{operation_name}.pimg")

                img_exists = os.path.exists(img_file)
                pimg_exists = os.path.exists(pimg_file)

                if img_exists and pimg_exists:
                    self.logger.info(f"Operation {operation.name} verified complete - output files exist")
                    return True
                else:
                    self.logger.info(f"Operation {operation.name} not complete - img:{img_exists}, pimg:{pimg_exists}")
                    return False
            
            # For hydration operations, check for actual completion indicators
            elif operation.operation_type == OperationType.HYDRATION_SIMULATION:
                # Hydration operations should only be considered complete if they reach their target time
                # or if there are specific completion files
                operation_dir = self._get_operation_directory(operation)
                if operation_dir:
                    import os
                    import json

                    # Check if there's a progress.json with completion status
                    progress_file = os.path.join(operation_dir, "progress.json")
                    if os.path.exists(progress_file):
                        try:
                            with open(progress_file, 'r') as f:
                                content = f.read().strip()
                                if content.startswith("json "):
                                    content = content[5:]
                                data = json.loads(content)

                                # Get current time and target time to determine completion
                                current_time = data.get('time_hours', 0)

                                # Get target time from stored parameters
                                target_time = None
                                if hasattr(operation, 'stored_ui_parameters') and operation.stored_ui_parameters:
                                    try:
                                        params = json.loads(operation.stored_ui_parameters) if isinstance(operation.stored_ui_parameters, str) else operation.stored_ui_parameters
                                        target_time = params.get('max_time', None)
                                    except:
                                        pass

                                if not target_time:
                                    target_time = 168.0  # Default 7 days

                                # Only consider complete if we've reached at least 95% of target time
                                if current_time >= (target_time * 0.95):
                                    self.logger.info(f"Hydration operation {operation.name} verified complete - reached {current_time:.2f}h of {target_time:.2f}h target")
                                    return True
                                else:
                                    self.logger.info(f"Hydration operation {operation.name} not complete - only {current_time:.2f}h of {target_time:.2f}h target")
                                    return False
                        except Exception as e:
                            self.logger.warning(f"Error reading hydration progress for completion check: {e}")
                            return False

                # If no progress file or other issues, don't assume completion
                self.logger.info(f"Hydration operation {operation.name} - no completion indicators found")
                return False

            # For other operation types, assume completion based on process exit
            return True
            
        except Exception as e:
            self.logger.error(f"Error verifying operation completion: {e}")
            # If verification fails, fall back to assuming completion
            return True

    def _parse_operation_stdout(self, operation) -> None:
        """Parse stdout output from running operation for progress updates."""
        try:
            # Only parse stdout for microstructure operations
            if operation.operation_type == OperationType.MICROSTRUCTURE_GENERATION:
                
                # Try to find stdout file if not already available
                stdout_path = None
                if hasattr(operation, 'stdout_file') and operation.stdout_file:
                    stdout_path = operation.stdout_file
                else:
                    # For database-loaded operations, find the process stdout file with GENMIC_PROGRESS messages
                    operation_name = operation.name
                    if operation_name.endswith(" Microstructure"):
                        base_name = operation_name.replace(" Microstructure", "")
                        
                        # Phase 2: Clean naming - operation name is already clean, use as-is
                        folder_name = base_name
                    else:
                        # For non-microstructure operations, use name as-is
                        folder_name = operation_name
                        
                        # Look for genmic_progress.txt file (single-line, always same name)
                        import os
                        operations_dir = os.path.join("Operations", folder_name)
                        if os.path.exists(operations_dir):
                            progress_file = os.path.join(operations_dir, "genmic_progress.txt")
                            if os.path.exists(progress_file):
                                stdout_path = progress_file
                                self.logger.info(f"Found genmic progress file: {progress_file}")
                            else:
                                self.logger.info(f"No genmic_progress.txt file found in {operations_dir}")
                        else:
                            self.logger.info(f"Operations directory not found: {operations_dir}")
                
                if not stdout_path:
                    return
                
                # Read simple progress file (single line, overwritten each time)
                try:
                    self.logger.info(f"Reading simple progress file: {stdout_path}")
                    with open(stdout_path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        self.logger.info(f"Progress file content: {repr(content)}")
                        
                        if content:
                            # Parse simple format: "PROGRESS: 0.65 Distributing cement phases..."
                            if self._parse_simple_progress(operation, content):
                                # Progress was updated, log it
                                self.logger.info(f"Updated progress for {operation.name}: {operation.progress:.1%} - {operation.current_step}")
                                
                                # Update database for any progress change
                                self._update_operation_in_database(operation)
                                
                                # If operation was marked complete, close output files
                                if operation.status == OperationStatus.COMPLETED:
                                    self.logger.info(f"Operation {operation.name} completed via progress file")
                                    operation.close_output_files()
                        
                except (IOError, OSError) as e:
                    # File might not exist yet or be locked, that's okay
                    pass
                    
        except Exception as e:
            self.logger.error(f"Error parsing stdout for operation {operation.id}: {e}")
    
    def _parse_simple_progress(self, operation, content: str) -> bool:
        """Parse simple progress format: 'PROGRESS: 0.65 Distributing cement phases...'"""
        try:
            if not content.startswith("PROGRESS:"):
                return False
            
            # Remove "PROGRESS: " prefix
            data = content[9:].strip()
            
            # Split into progress and message
            parts = data.split(' ', 1)
            if len(parts) < 2:
                return False
            
            progress_str, message = parts[0], parts[1]
            
            try:
                progress = float(progress_str)
                
                # Update operation
                old_progress = operation.progress
                operation.progress = progress
                operation.current_step = message
                
                # Check for completion
                if progress >= 1.0:
                    operation.status = OperationStatus.COMPLETED
                    operation.end_time = datetime.utcnow()
                    operation.completed_steps = operation.total_steps
                
                # Return True if progress changed
                return abs(progress - old_progress) > 0.001
                
            except ValueError:
                self.logger.warning(f"Invalid progress value: {progress_str}")
                return False
            
        except Exception as e:
            self.logger.warning(f"Error parsing simple progress: {e}")
            return False

    def _update_elastic_progress(self, operation) -> None:
        """Update progress for elastic moduli calculations using JSON progress file."""
        try:
            # Import the elastic progress parser
            from app.services.elastic_progress_parser import ElasticProgressParser

            if not hasattr(self, '_elastic_parser'):
                self._elastic_parser = ElasticProgressParser()

            # Determine operation directory
            operation_dir = self._get_operation_directory(operation)
            self.logger.debug(f"DEBUG Elastic Progress: Operation '{operation.name}' directory: {operation_dir}")

            if not operation_dir:
                self.logger.debug(f"DEBUG Elastic Progress: No directory found for operation '{operation.name}'")
                return

            # Monitor progress file
            progress = self._elastic_parser.monitor_progress_file(operation_dir, operation.name)
            self.logger.debug(f"DEBUG Elastic Progress: Parsed progress for '{operation.name}': {progress}")

            if progress:
                # Update operation progress
                old_progress = operation.progress
                old_step = operation.current_step
                operation.progress = progress.percent_complete / 100.0

                # Update current step description with detailed information
                if progress.is_complete:
                    operation.current_step = f"Elastic calculation complete - {progress.cycle}/{progress.max_cycle} cycles (100%)"
                else:
                    # Show quantitative convergence progress rather than just cycle count
                    if hasattr(progress, 'gradient') and progress.gradient > 0:
                        operation.current_step = f"Computing elastic moduli - {progress.percent_complete:.1f}% converged (cycle {progress.cycle}/{progress.max_cycle}, gradient: {progress.gradient:.2f})"
                    else:
                        operation.current_step = f"Computing elastic moduli - {progress.percent_complete:.1f}% converged (cycle {progress.cycle}/{progress.max_cycle})"

                # Update completed steps based on progress
                if operation.total_steps > 0:
                    operation.completed_steps = int(operation.progress * operation.total_steps)

                # Only update database if progress or step actually changed (avoid excessive DB writes)
                progress_changed = abs(operation.progress - old_progress) > 0.001  # 0.1% threshold
                step_changed = operation.current_step != old_step

                if progress_changed or step_changed:
                    self.logger.info(f"Updated elastic progress for {operation.name}: {progress.percent_complete:.1f}% (was {old_progress*100:.1f}%)")
                    self.logger.info(f"Current step updated to: {operation.current_step}")

                    # Update database only when necessary
                    self._update_operation_in_database(operation)
                else:
                    self.logger.debug(f"No significant change in progress for {operation.name}, skipping database update")
            else:
                self.logger.info(f"DEBUG Elastic Progress: No progress data found for '{operation.name}'")

        except Exception as e:
            self.logger.error(f"Error updating elastic progress for {operation.name}: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")

    def _update_microstructure_progress(self, operation) -> None:
        """Update progress for microstructure generation using JSON progress files."""
        try:
            # Determine operation directory
            operation_dir = self._get_operation_directory(operation)
            self.logger.debug(f"DEBUG Microstructure Progress: Operation '{operation.name}' directory: {operation_dir}")

            if not operation_dir:
                self.logger.debug(f"DEBUG Microstructure Progress: No directory found for operation '{operation.name}'")
                return

            # Look for genmic_progress.json file (new JSON format from genmic -j flag)
            import os
            import json
            progress_file = os.path.join(operation_dir, "genmic_progress.json")

            self.logger.debug(f"DEBUG Microstructure Progress: Looking for {progress_file}")

            if os.path.exists(progress_file):
                self.logger.debug(f"DEBUG Microstructure Progress: Found progress file")
                try:
                    # Check if file has content before trying to read (prevents read errors on empty files)
                    if os.path.getsize(progress_file) == 0:
                        self.logger.debug(f"DEBUG Microstructure Progress: Skipping empty file")
                        return

                    with open(progress_file, 'r') as f:
                        content = f.read().strip()
                        if not content:
                            self.logger.debug(f"DEBUG Microstructure Progress: Skipping file with no content")
                            return

                    self.logger.debug(f"DEBUG Microstructure Progress: Raw content: {content[:200]}")

                    # Handle "json " prefix format
                    if content.startswith("json "):
                        json_content = content[5:]  # Remove "json " prefix
                    else:
                        json_content = content

                    data = json.loads(json_content)
                    self.logger.debug(f"DEBUG Microstructure Progress: Parsed JSON data: {data}")

                    # Extract progress information from genmic format
                    if 'percent_complete' in data and 'step' in data:
                        old_progress = operation.progress
                        old_step = operation.current_step

                        progress = data['percent_complete'] / 100.0
                        step_description = data['step']

                        operation.progress = progress
                        operation.current_step = f"Microstructure: {step_description}"

                        # Update completed steps based on progress
                        if operation.total_steps > 0:
                            operation.completed_steps = int(operation.progress * operation.total_steps)

                        # Check for completion
                        if progress >= 1.0:
                            from datetime import datetime
                            operation.status = OperationStatus.COMPLETED
                            operation.end_time = datetime.utcnow()
                            operation.current_step = "Microstructure generation complete"

                        # Only update database if progress or step actually changed
                        progress_changed = abs(operation.progress - old_progress) > 0.001
                        step_changed = operation.current_step != old_step

                        if progress_changed or step_changed:
                            self.logger.info(f"Updated microstructure progress for {operation.name}: {progress*100:.1f}% - {step_description}")
                            self._update_operation_in_database(operation)
                        else:
                            self.logger.debug(f"No significant change in microstructure progress for {operation.name}")

                except (json.JSONDecodeError, KeyError) as e:
                    self.logger.debug(f"Could not parse microstructure progress JSON: {e}")
                    # Don't fall back to old format if JSON exists but has parse errors
                    # This prevents oscillation between old and new progress values
            else:
                # Only fall back to old format if JSON file truly doesn't exist
                # Check if we should use old format (no JSON file but has old progress file)
                import os
                old_progress_file = os.path.join(operation_dir, "genmic_progress.txt")
                if os.path.exists(old_progress_file):
                    self.logger.debug(f"No genmic_progress.json found, using old text format for {operation.name}")
                    self._parse_operation_stdout(operation)
                else:
                    self.logger.debug(f"No progress files found for {operation.name}")

        except Exception as e:
            self.logger.error(f"Error updating microstructure progress for {operation.name}: {e}")

    def _update_hydration_progress(self, operation) -> None:
        """Update progress for hydration simulation using progress.json files."""
        try:
            # Determine operation directory
            operation_dir = self._get_operation_directory(operation)
            if not operation_dir:
                return

            # Look for progress.json file
            import os
            import json
            progress_file = os.path.join(operation_dir, "progress.json")

            if os.path.exists(progress_file):
                try:
                    # Check if file has content before trying to read
                    if os.path.getsize(progress_file) == 0:
                        return  # Skip empty files

                    with open(progress_file, 'r') as f:
                        content = f.read().strip()
                        if not content:
                            return  # Skip files with only whitespace

                        # Handle "json " prefix format if present
                        if content.startswith("json "):
                            content = content[5:]

                        data = json.loads(content)
                except (OSError, IOError, json.JSONDecodeError) as read_error:
                    # File might be being written to, or corrupted, just skip this update
                    self.logger.debug(f"Skipping hydration progress read for {operation.name}: {read_error}")
                    return

                # Extract progress information from hydration progress.json format
                if 'time_hours' in data:
                    current_time = data['time_hours']
                    cycle = data.get('cycle', 0)
                    doh = data.get('degree_of_hydration', 0.0)

                    # Get target time from operation parameters (max_time)
                    target_time = None
                    if hasattr(operation, 'stored_ui_parameters') and operation.stored_ui_parameters:
                        try:
                            import json
                            params = json.loads(operation.stored_ui_parameters) if isinstance(operation.stored_ui_parameters, str) else operation.stored_ui_parameters
                            target_time = params.get('max_time', None)
                        except:
                            pass

                    # Fallback to default simulation time if not available
                    if not target_time:
                        target_time = 168.0  # Default 7 days

                    # Calculate progress based on time
                    if target_time > 0:
                        progress = min(1.0, current_time / target_time)
                        operation.progress = progress

                        # Update current step description with hydration-specific info
                        if progress >= 1.0:
                            operation.current_step = f"Hydration complete - Cycle {cycle}, DOH: {doh:.3f}"
                        else:
                            operation.current_step = f"Cycle {cycle}, Time: {current_time:.2f}h of {target_time:.2f}h, DOH: {doh:.3f}"

                        # Update completed steps based on progress
                        if operation.total_steps > 0:
                            operation.completed_steps = int(operation.progress * operation.total_steps)

                        self.logger.debug(f"Updated hydration progress for {operation.name}: {progress*100:.1f}% (cycle {cycle}, time {current_time:.2f}h/{target_time:.2f}h)")

        except Exception as e:
            self.logger.error(f"Error updating hydration progress for {operation.name}: {e}")

    def _update_generic_progress(self, operation) -> None:
        """Update progress for generic operations using JSON progress files."""
        try:
            # Determine operation directory
            operation_dir = self._get_operation_directory(operation)
            if not operation_dir:
                return

            # Look for common progress file names
            import os
            import json

            progress_files = ["progress.json", "operation_progress.json", "status.json"]

            for progress_filename in progress_files:
                progress_file = os.path.join(operation_dir, progress_filename)

                if os.path.exists(progress_file):
                    try:
                        with open(progress_file, 'r') as f:
                            data = json.load(f)

                        # Try to extract progress from common field names
                        progress = None
                        current_step = None

                        # Common progress field names
                        for progress_field in ['progress', 'percent_complete', 'completion']:
                            if progress_field in data:
                                progress = float(data[progress_field])
                                if progress > 1.0:  # Convert percentage to fraction
                                    progress /= 100.0
                                break

                        # Common step field names
                        for step_field in ['current_step', 'status', 'message', 'description']:
                            if step_field in data:
                                current_step = str(data[step_field])
                                break

                        # Update operation if we found progress information
                        if progress is not None:
                            operation.progress = min(1.0, max(0.0, progress))

                            if current_step:
                                operation.current_step = current_step
                            else:
                                operation.current_step = f"Processing ({progress*100:.1f}% complete)"

                            # Update completed steps based on progress
                            if operation.total_steps > 0:
                                operation.completed_steps = int(operation.progress * operation.total_steps)

                            self.logger.debug(f"Updated generic progress for {operation.name}: {progress*100:.1f}%")
                            break

                    except (json.JSONDecodeError, ValueError, KeyError) as e:
                        self.logger.debug(f"Could not parse progress from {progress_filename}: {e}")
                        continue

        except Exception as e:
            self.logger.error(f"Error updating generic progress for {operation.name}: {e}")

    def _get_operation_directory(self, operation) -> Optional[str]:
        """Get the directory path for an operation."""
        try:
            operation_name = operation.name
            import os

            # Get Operations directory using directories service (not hardcoded path)
            operations_base = self.service_container.directories_service.get_operations_path()

            # First, try to find the operation directory regardless of source
            # Check if it's a nested elastic operation
            if operation_name.startswith('Elastic-'):
                # Look for nested structure: Operations/HydrationName/ElasticName/
                for parent_dir in os.listdir(operations_base):
                    parent_path = os.path.join(operations_base, parent_dir)
                    if os.path.isdir(parent_path):
                        elastic_path = os.path.join(parent_path, operation_name)
                        if os.path.exists(elastic_path):
                            self.logger.debug(f"Found nested elastic directory: {elastic_path}")
                            return elastic_path

            # Check direct operation directory
            direct_path = os.path.join(operations_base, operation_name)
            if os.path.exists(direct_path):
                self.logger.debug(f"Found direct operation directory: {direct_path}")
                return direct_path

            # For process operations, try working directory if available
            # Check both 'working_directory' (correct) and 'working_dir' (legacy) for compatibility
            if hasattr(operation, 'process'):
                if hasattr(operation, 'working_directory'):
                    wd = operation.working_directory
                    if os.path.exists(wd):
                        self.logger.debug(f"Using process working_directory: {wd}")
                        return wd

                if hasattr(operation, 'working_dir'):
                    wd = operation.working_dir
                    if os.path.exists(wd):
                        self.logger.debug(f"Using process working_dir: {wd}")
                        return wd

            # Try metadata directory if available
            if hasattr(operation, 'metadata') and operation.metadata.get('output_directory'):
                meta_dir = operation.metadata['output_directory']
                if os.path.exists(meta_dir):
                    self.logger.debug(f"Using metadata directory: {meta_dir}")
                    return meta_dir

            self.logger.debug(f"No directory found for operation {operation_name}")
            return None

        except Exception as e:
            self.logger.error(f"Error getting operation directory for {operation.name}: {e}")
            return None

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
            
            # Format start time for display
            start_time_str = ""
            if operation.start_time:
                start_time_str = operation.start_time.strftime("%m/%d %H:%M")
            else:
                start_time_str = "Not started"
            
            # Get meaningful operation name from metadata
            meaningful_name = self._get_meaningful_operation_name(operation)
            
            current_ops[operation.id] = [
                operation.id,                                                    # Column 0: ID
                meaningful_name,                                                 # Column 1: Name  
                operation.operation_type.value.replace('_', ' ').title(),      # Column 2: Type
                operation.status.value.title(),                                # Column 3: Status
                operation.progress_percentage,                                  # Column 4: Progress
                duration_str,                                                   # Column 5: Duration
                start_time_str,                                                 # Column 6: Started (date/time)
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
        # Skip if System Resources tab is hidden/not initialized
        if not hasattr(self, 'cpu_usage_label'):
            return

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

        # Update metric labels (skip if Performance tab is hidden/not initialized)
        if not hasattr(self, 'metrics_completed_value'):
            return

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
        
        # Enhanced current step display with better fallbacks
        self.logger.info(f"STEP_DEBUG: Operation {operation.name}, current_step='{operation.current_step}', status={operation.status}")
        if operation.current_step:
            self.logger.info(f"STEP_DEBUG: Setting step text to: '{operation.current_step}'")
            self.operation_step_value.set_text(operation.current_step)
        elif operation.status == OperationStatus.RUNNING:
            if operation.operation_type == OperationType.HYDRATION_SIMULATION:
                # For running hydration simulations, show a more informative message
                if operation.start_time:
                    elapsed = datetime.utcnow() - operation.start_time
                    elapsed_hours = elapsed.total_seconds() / 3600.0
                    
                    # Check if this is a real active simulation by looking at the hydration service
                    try:
                        hydration_service = self.service_container.hydration_executor_service
                        active_sims = hydration_service.active_simulations
                        sim_name = operation.name
                        
                        self.logger.info(f"DEBUG: Checking active simulations for '{sim_name}'")
                        self.logger.info(f"DEBUG: Active simulations: {list(active_sims.keys())}")
                        
                        # Try to find matching simulation with flexible naming
                        matching_sim_info = None
                        for active_sim_name, sim_info in active_sims.items():
                            self.logger.info(f"DEBUG: Comparing '{sim_name}' with active sim '{active_sim_name}'")
                            if (sim_name == active_sim_name or 
                                sim_name in active_sim_name or 
                                active_sim_name in sim_name):
                                matching_sim_info = sim_info
                                self.logger.info(f"DEBUG: Found matching simulation: {active_sim_name}")
                                break
                        
                        if matching_sim_info and 'progress' in matching_sim_info:
                            progress_data = matching_sim_info['progress']
                            self.logger.info(f"DEBUG: Progress data type: {type(progress_data)}")
                            if hasattr(progress_data, 'cycle') and hasattr(progress_data, 'time_hours'):
                                cycle = progress_data.cycle
                                time_h = progress_data.time_hours
                                doh = getattr(progress_data, 'degree_of_hydration', 0.0)
                                step_text = f"Cycle {cycle}, Time: {time_h:.2f}h, DOH: {doh:.3f}"
                                self.logger.info(f"DEBUG: Setting step text to: {step_text}")
                                self.operation_step_value.set_text(step_text)
                            else:
                                fallback_text = f"Hydration simulation running ({elapsed_hours:.1f}h elapsed)"
                                self.logger.info(f"DEBUG: No cycle/time data, using fallback: {fallback_text}")
                                self.operation_step_value.set_text(fallback_text)
                        else:
                            fallback_text = f"Hydration simulation running ({elapsed_hours:.1f}h elapsed)"
                            self.logger.info(f"DEBUG: No matching simulation found, using fallback: {fallback_text}")
                            self.operation_step_value.set_text(fallback_text)
                    except Exception as e:
                        self.logger.error(f"Error checking active simulations for step display: {e}")
                        fallback_text = f"Hydration simulation running ({elapsed_hours:.1f}h elapsed)"
                        self.operation_step_value.set_text(fallback_text)
                else:
                    self.operation_step_value.set_text("Hydration simulation in progress")
            else:
                self.operation_step_value.set_text("Operation in progress")
        elif operation.status == OperationStatus.COMPLETED:
            self.operation_step_value.set_text("Process completed")
        elif operation.status == OperationStatus.FAILED:
            self.operation_step_value.set_text("Operation failed")
        elif operation.status == OperationStatus.CANCELLED:
            self.operation_step_value.set_text("Operation cancelled")
        elif operation.status == OperationStatus.PENDING:
            # Show actual step if available, otherwise default queued message
            if operation.current_step and operation.current_step.strip():
                self.operation_step_value.set_text(operation.current_step)
            else:
                self.operation_step_value.set_text("Queued for execution")
        else:
            self.operation_step_value.set_text("Not started")
        
        # Store the currently displayed operation for periodic updates
        self._currently_displayed_operation = operation
        
        # Force immediate UI update for step status as backup
        if operation.status == OperationStatus.RUNNING and operation.current_step:
            from gi.repository import GLib
            def force_step_update():
                try:
                    self.operation_step_value.set_text(operation.current_step)
                    self.logger.info(f"FORCE_UPDATE: Set step to '{operation.current_step}'")
                    return False  # Don't repeat
                except Exception as e:
                    self.logger.error(f"FORCE_UPDATE error: {e}")
                    return False
            GLib.timeout_add(100, force_step_update)  # Update after 100ms
        self.operation_progress_value.set_text(f"{operation.progress_percentage:.1f}%")
        
        # Update progress bars
        self.overall_progress.set_fraction(operation.progress)
        
        # Note: Step progress updates removed - information now shown in Current Step field above
        self.overall_progress.set_text(f"{operation.progress_percentage:.1f}%")
    
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
                    
                    # Always try to find the standard Operations folder regardless of metadata
                    # This ensures orphaned folders get cleaned up even if metadata is missing/incorrect
                    operations_dir = self.service_container.directories_service.get_operations_path()
                    standard_folder = operations_dir / operation.name
                    
                    # Use the metadata output_dir if available and valid, otherwise use standard location
                    if output_dir and Path(output_dir).exists():
                        # Use existing metadata path
                        self.logger.info(f"Using metadata output_dir for {operation.name}: {output_dir}")
                    elif standard_folder.exists():
                        # Use standard Operations folder location
                        output_dir = str(standard_folder)
                        self.logger.info(f"Using standard Operations folder for {operation.name}: {output_dir}")
                    else:
                        # Try to make relative paths absolute
                        if output_dir and not Path(output_dir).is_absolute():
                            absolute_path = operations_dir / output_dir
                            if absolute_path.exists():
                                output_dir = str(absolute_path)
                                self.logger.info(f"Made relative path absolute for {operation.name}: {output_dir}")
                            else:
                                self.logger.warning(f"Neither metadata path nor standard folder exists for {operation.name}")
                                output_dir = None
                        else:
                            self.logger.warning(f"No valid folder path found for operation {operation.name}")
                            output_dir = None
                    
                    # Always try to delete from database (operations may exist in both JSON and database)
                    try:
                        operation_service = self.service_container.operation_service
                        operation_service.delete(operation.name)
                        self.logger.info(f"Deleted operation from database: {operation.name}")
                    except Exception as e:
                        # This is expected if operation was not in database (e.g., file-based only)
                        self.logger.debug(f"Operation not found in database (expected for file-based operations): {operation.name}: {e}")
                    
                    # Delete the operation from memory
                    if operation_id in self.operations:
                        del self.operations[operation_id]
                    
                    # Delete the associated folder if it exists
                    if output_dir:
                        folder_path = Path(output_dir)
                        self.logger.info(f"🗑️ DELETION DEBUG: Attempting to delete folder: {output_dir}")
                        self.logger.info(f"🗑️ DELETION DEBUG: Folder path object: {folder_path}")
                        self.logger.info(f"🗑️ DELETION DEBUG: Is absolute path: {folder_path.is_absolute()}")
                        self.logger.info(f"🗑️ DELETION DEBUG: Folder exists: {folder_path.exists()}")
                        self.logger.info(f"🗑️ DELETION DEBUG: Resolved path: {folder_path.resolve()}")
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
            
            # DISABLED: Automatic cleanup is dangerous - use "Sync with Filesystem" instead
            # Clean up any orphaned folders after deletion
            # self._cleanup_orphaned_folders()

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
        self._update_status("Refreshing operations from database...")
        
        # Smart refresh: preserve running operations, reload others from database
        self._smart_refresh_from_database()
        
        # Update UI
        self._update_ui()
        
        # Count active operations for status feedback
        active_count = sum(1 for op in self.operations.values() 
                          if op.status in [OperationStatus.RUNNING, OperationStatus.PAUSED])
        
        self._update_status(f"Refresh complete. {active_count} active operations.")
    
    def _on_clean_duplicates_clicked(self, button: Gtk.Button) -> None:
        """Handle clean duplicates button click."""
        self._update_status("Cleaning duplicate operations...")
        
        # Count operations before cleanup
        operations_before = len(self.operations)
        
        # Force validation to remove duplicates
        self._validate_operations_data()
        
        # Update UI to reflect changes
        self._update_ui()
        
        # Report results
        operations_after = len(self.operations)
        removed_count = operations_before - operations_after
        
        if removed_count > 0:
            self._update_status(f"Cleaned {removed_count} duplicate operations. {operations_after} operations remaining.")
        else:
            self._update_status("No duplicate operations found.")

    def _on_sync_filesystem_clicked(self, button: Gtk.Button) -> None:
        """Sync database with filesystem - remove orphaned database records and folders."""
        try:
            self._update_status("Analyzing database and filesystem...")

            # Get Operations directory
            operations_dir = self.service_container.directories_service.get_operations_path()
            if not operations_dir.exists():
                self._update_status(f"Operations directory not found: {operations_dir}")
                return

            # Get all database operations
            operation_service = self.service_container.operation_service
            db_operations = operation_service.get_all()
            db_operation_names = {op.name for op in db_operations}

            # DIAGNOSTIC: Log database operation names
            self.logger.info(f"=== SYNC DIAGNOSTIC ===")
            self.logger.info(f"Operations directory: {operations_dir}")
            self.logger.info(f"Database operations ({len(db_operation_names)}): {sorted(db_operation_names)}")

            # Get all folders in Operations directory
            folder_names = set()
            special_folders = {'grading_files', 'microstructure_metadata', '.git', '__pycache__', 'particle_shape_set', 'aggregate'}
            for item in operations_dir.iterdir():
                if item.is_dir() and item.name not in special_folders:
                    folder_names.add(item.name)

            # DIAGNOSTIC: Log filesystem folders
            self.logger.info(f"Filesystem folders ({len(folder_names)}): {sorted(folder_names)}")

            # Find mismatches
            orphaned_db_records = db_operation_names - folder_names  # In database but no folder
            orphaned_folders = folder_names - db_operation_names  # Folder exists but no database record

            # DIAGNOSTIC: Log mismatches
            self.logger.info(f"Orphaned DB records ({len(orphaned_db_records)}): {sorted(orphaned_db_records)}")
            self.logger.info(f"Orphaned folders ({len(orphaned_folders)}): {sorted(orphaned_folders)}")
            self.logger.info(f"=== END SYNC DIAGNOSTIC ===")
            print(f"=== SYNC DIAGNOSTIC ===")
            print(f"Database operations ({len(db_operation_names)}): {sorted(db_operation_names)}")
            print(f"Filesystem folders ({len(folder_names)}): {sorted(folder_names)}")
            print(f"Orphaned DB records ({len(orphaned_db_records)}): {sorted(orphaned_db_records)}")
            print(f"Orphaned folders ({len(orphaned_folders)}): {sorted(orphaned_folders)}")
            print(f"=== END SYNC DIAGNOSTIC ===")

            # Show confirmation dialog with details
            total_issues = len(orphaned_db_records) + len(orphaned_folders)
            if total_issues == 0:
                self._update_status("Database and filesystem are in sync!")
                return

            dialog_text = f"Found {total_issues} mismatches between database and filesystem:\n\n"

            if orphaned_db_records:
                dialog_text += f"**{len(orphaned_db_records)} Orphaned Database Records** (will be deleted):\n"
                for name in sorted(list(orphaned_db_records)[:10]):  # Show first 10
                    dialog_text += f"  • {name}\n"
                if len(orphaned_db_records) > 10:
                    dialog_text += f"  ... and {len(orphaned_db_records) - 10} more\n"
                dialog_text += "\n"

            if orphaned_folders:
                dialog_text += f"**{len(orphaned_folders)} Orphaned Folders** (will be imported to database):\n"
                for name in sorted(list(orphaned_folders)[:10]):  # Show first 10
                    dialog_text += f"  • {name}\n"
                if len(orphaned_folders) > 10:
                    dialog_text += f"  ... and {len(orphaned_folders) - 10} more\n"

            dialog = Gtk.MessageDialog(
                transient_for=self.main_window,
                message_type=Gtk.MessageType.QUESTION,
                buttons=Gtk.ButtonsType.YES_NO,
                text="Sync Database with Filesystem?"
            )
            dialog.format_secondary_text(dialog_text)

            response = dialog.run()
            dialog.destroy()

            if response == Gtk.ResponseType.YES:
                # Delete orphaned database records
                deleted_count = 0
                for op_name in orphaned_db_records:
                    try:
                        operation_service.delete(op_name)
                        # Also remove from memory
                        for op_id, op in list(self.operations.items()):
                            if op.name == op_name:
                                del self.operations[op_id]
                                break
                        deleted_count += 1
                        self.logger.info(f"Deleted orphaned database record: {op_name}")
                    except Exception as e:
                        self.logger.error(f"Failed to delete database record {op_name}: {e}")

                # Import orphaned folders as new operations
                imported_count = 0
                for folder_name in orphaned_folders:
                    try:
                        folder_path = operations_dir / folder_name

                        # Infer operation type from folder name
                        if folder_name.startswith("HydrationOf-") or folder_name.startswith("Hydration"):
                            op_type = "Hydration Simulation"
                        elif folder_name.startswith("Elastic-"):
                            op_type = "Elastic Moduli Calculation"
                        elif folder_name.endswith("-ElMod"):
                            op_type = "Elastic Moduli Calculation"
                        else:
                            op_type = "Microstructure Generation"

                        # Create basic database record
                        from app.models.operation import Operation as OperationModel
                        new_op = OperationModel(
                            name=folder_name,
                            operation_type=op_type,
                            status="completed",  # Assume completed since folder exists
                            output_directory=str(folder_path)
                        )
                        operation_service.save(new_op)
                        imported_count += 1
                        self.logger.info(f"Imported folder as operation: {folder_name}")
                    except Exception as e:
                        self.logger.error(f"Failed to import folder {folder_name}: {e}")

                # Refresh from database to show new operations
                self._smart_refresh_from_database()
                self._update_ui()

                # Report results
                if imported_count > 0:
                    self._update_status(
                        f"Sync complete! Removed {deleted_count} orphaned database records. "
                        f"Imported {imported_count} folders as operations."
                    )
                else:
                    self._update_status(f"Sync complete! Removed {deleted_count} orphaned database records.")
            else:
                self._update_status("Sync cancelled.")

        except Exception as e:
            self.logger.error(f"Error during filesystem sync: {e}")
            self._update_status(f"Error during sync: {e}")



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
            start_time=datetime.utcnow(),
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
                operation.end_time = datetime.utcnow()
                self._add_log_entry(f"Successfully terminated process for operation: {operation.name}")
            else:
                # Process might have already ended, just update status
                operation.status = OperationStatus.CANCELLED
                operation.end_time = datetime.utcnow()
                self._add_log_entry(f"Operation marked as stopped: {operation.name} (process may have already ended)")
            
            self._update_operations_list()
    
    def _pause_operation(self, operation_id: str) -> None:
        """Pause or resume an operation using real process control."""
        operation = self.operations.get(operation_id)
        if operation:
            self.logger.info(f"PAUSE DEBUG: Attempting to pause/resume operation {operation_id}: {operation.name}")
            self.logger.info(f"PAUSE DEBUG: Operation status: {operation.status}")
            self.logger.info(f"PAUSE DEBUG: Operation has process: {operation.process is not None}")
            self.logger.info(f"PAUSE DEBUG: Operation has pid: {operation.pid}")
            
            if operation.status == OperationStatus.RUNNING:
                # Pause the actual process
                self.logger.info(f"PAUSE DEBUG: Calling pause_process() for {operation.name}")
                if operation.pause_process():
                    operation.status = OperationStatus.PAUSED
                    operation.paused_time = datetime.utcnow()  # Record when paused
                    self._add_log_entry(f"Successfully paused process for operation: {operation.name}")
                    self.logger.info(f"PAUSE DEBUG: Successfully paused {operation.name}")
                else:
                    self._add_log_entry(f"Failed to pause process for operation: {operation.name} (process may have ended)")
                    self.logger.error(f"PAUSE DEBUG: Failed to pause {operation.name}")
                self._update_operations_list()
                
            elif operation.status == OperationStatus.PAUSED:
                # Resume the actual process
                if operation.resume_process():
                    operation.status = OperationStatus.RUNNING
                    # Adjust start_time to account for paused duration
                    if operation.paused_time and operation.start_time:
                        paused_duration = datetime.utcnow() - operation.paused_time
                        operation.start_time = operation.start_time + paused_duration
                    operation.paused_time = None  # Clear paused time
                    self._add_log_entry(f"Successfully resumed process for operation: {operation.name}")
                else:
                    self._add_log_entry(f"Failed to resume process for operation: {operation.name} (process may have ended)")
                self._update_operations_list()
    
    def _add_log_entry(self, message: str) -> None:
        """Add an entry to the operation log."""
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
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
            Database Operation ID (not process ID)
        """
        # Create database operation record FIRST to get the real operation ID
        try:
            # Convert UI enum to database enum
            from app.models.operation import OperationStatus as DBOperationStatus
            
            db_operation = self.service_container.operation_service.create_operation(
                name=name,
                operation_type=operation_type.value,
                notes=f"Process starting in {working_dir}"
            )
            # Use the database operation ID as the operation_id
            operation_id = str(db_operation.id)
            self.logger.info(f"Created database operation: {name} with ID {operation_id}")
        except Exception as e:
            self.logger.error(f"Failed to create database operation: {e}")
            self.logger.error(f"Exception type: {type(e).__name__}")
            self.logger.error(f"Exception details: {str(e)}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            # Fallback to process ID if database fails
            operation_id = f"proc_{int(time.time() * 1000)}"
        
        try:
            # Create process-specific identifier for output files
            process_id = f"proc_{int(time.time() * 1000)}"
            stdout_file = os.path.join(working_dir, f"{process_id}_stdout.txt")
            stderr_file = os.path.join(working_dir, f"{process_id}_stderr.txt")
            
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
                start_time=datetime.utcnow(),
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
            
            # Update database operation with process information
            try:
                # Try the correct method name from the main operation service
                if hasattr(self.service_container.operation_service, 'update_status'):
                    # Main operation service uses update_status with name, not ID
                    self.service_container.operation_service.update_status(
                        name=name,
                        status=DBOperationStatus.RUNNING,
                        progress=operation.progress,
                        current_step=operation.current_step
                    )
                elif hasattr(self.service_container.operation_service, 'update_operation_status'):
                    # Alternative operation service uses update_operation_status with ID
                    self.service_container.operation_service.update_operation_status(
                        operation_id=int(operation_id),
                        status=DBOperationStatus.RUNNING.value,
                        progress=operation.progress,
                        current_step=operation.current_step
                    )
                else:
                    self.logger.warning("No suitable update method found on operation service")
                self.logger.info(f"Updated database operation {operation_id} with process info: PID {process.pid}")
            except Exception as e:
                self.logger.error(f"Failed to update database operation {operation_id}: {e}")
            
            self._add_log_entry(f"Started operation: {name} (DB ID: {operation_id}, PID: {process.pid})")
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
            operation.start_time = datetime.utcnow()
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
            operation.end_time = datetime.utcnow()
            operation.progress = 1.0
            operation.error_message = error_message
            
            status_text = "completed successfully" if success else "failed"
            self._add_log_entry(f"Operation {status_text}: {operation.name}")
            if error_message:
                self._add_log_entry(f"Error: {error_message}")
                
            self._update_operations_list()
            # Database automatically updated through operation monitoring
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
            operation.end_time = datetime.utcnow()
            
            self._add_log_entry(f"Cancelled operation: {operation.name}")
            self._update_operations_list()
            # Database automatically updated through operation monitoring
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
            icon = self._get_file_icon("warning")
            self.files_store.append(None, [icon, "No Operations directory found", "", "info", "", ""])
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
            folder_icon = self._get_file_icon("folder")
            root_iter = self.files_store.append(None, [folder_icon, "Operations", str(operations_dir), "folder", "", ""])
            
            if success and new_tree_data:
                self.logger.info(f"Adding {len(new_tree_data)} operations to display")
                # Add all the operation folders we successfully gathered
                for op_data in new_tree_data:
                    self._add_operation_folder_from_data(root_iter, op_data)
            else:
                self.logger.warning(f"Failed to load operations: success={success}, data_count={len(new_tree_data)}")
                # Failed to load after retries
                warning_icon = self._get_file_icon("warning")
                self.files_store.append(root_iter, [
                    warning_icon, "⚠️ Files temporarily unavailable (operation running?)", 
                    "", "warning", "", ""
                ])
            
            # Expand the root by default
            self.files_view.expand_row(self.files_store.get_path(root_iter), False)
            self.logger.info("=== Display update complete ===\n")
            
        except Exception as e:
            self.logger.error(f"Error updating files display: {e}")
            self.files_store.clear()
            error_icon = self._get_file_icon("error")
            self.files_store.append(None, [error_icon, f"Error loading files: {e}", "", "error", "", ""])
    
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
            folder_icon = self._get_file_icon(op_data['type'])
            folder_iter = self.files_store.append(parent_iter, [
                folder_icon,
                op_data['name'],
                op_data['path'],
                op_data['type'],
                op_data['size'],
                op_data['modified']
            ])
            
            # Add files
            for file_data in op_data['files']:
                file_icon = self._get_file_icon(file_data['type'], Path(file_data['path']) if file_data['path'] else None)
                self.files_store.append(folder_iter, [
                    file_icon,
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
            folder_icon = self._get_file_icon("folder")
            folder_iter = self.files_store.append(parent_iter, [
                folder_icon,
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
                        warning_icon = self._get_file_icon("warning")
                        self.files_store.append(folder_iter, [
                            warning_icon, "⚠️ Files temporarily inaccessible", 
                            "", "warning", "", ""
                        ])
                    else:
                        # Brief pause before retry
                        import time
                        time.sleep(0.05)
                except Exception as e:
                    self.logger.error(f"Error loading files in {op_dir}: {e}")
                    error_icon = self._get_file_icon("error")
                    self.files_store.append(folder_iter, [error_icon, f"Error loading files: {e}", "", "error", "", ""])
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
            
            file_icon = self._get_file_icon(file_type, file_path)
            self.files_store.append(parent_iter, [
                file_icon,
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
    
    def _get_file_icon(self, file_type: str, file_path: Path = None) -> GdkPixbuf.Pixbuf:
        """Get appropriate icon for file type using GTK theme icons."""
        try:
            icon_theme = Gtk.IconTheme.get_default()
            
            # Use only icons that are confirmed to be available
            if file_type == 'folder':
                icon_name = 'folder'
            else:
                # All other file types use text-x-generic (universally available)
                icon_name = 'text-x-generic'
            
            # Try to load the icon
            if icon_theme.has_icon(icon_name):
                pixbuf = icon_theme.load_icon(icon_name, 16, Gtk.IconLookupFlags.FORCE_SIZE)
                return pixbuf
                
            # Fallback - try the most basic icons
            fallback_icons = ['folder', 'text-x-generic']
            for fallback_name in fallback_icons:
                if icon_theme.has_icon(fallback_name):
                    pixbuf = icon_theme.load_icon(fallback_name, 16, Gtk.IconLookupFlags.FORCE_SIZE)
                    return pixbuf
                    
        except Exception as e:
            self.logger.warning(f"Failed to load icon for {file_type}: {e}")
        
        # Return None if all else fails - no icon will be displayed
        return None
    
    def _load_carbon_icon(self, icon_name: str, size: int = 32) -> GdkPixbuf.Pixbuf:
        """Load a Carbon icon from the icons directory."""
        from pathlib import Path
        
        try:
            # Build path to Carbon icon - use current working directory as project root
            # This is more reliable than calculating from __file__
            project_root = Path.cwd()
            icon_path = project_root / "icons" / "carbon" / str(size) / f"{icon_name}.svg"
            
            self.logger.info(f"Attempting to load Carbon icon: {icon_name} from {icon_path}")
            
            if icon_path.exists():
                # Load SVG and scale to desired size
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                    str(icon_path), size, size, True
                )
                self.logger.info(f"Successfully loaded Carbon icon: {icon_name} ({pixbuf.get_width()}x{pixbuf.get_height()})")
                return pixbuf
            else:
                self.logger.warning(f"Carbon icon not found: {icon_path}")
                
        except Exception as e:
            self.logger.error(f"Failed to load Carbon icon {icon_name}: {e}")
        
        return None
    
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
        self.logger.info(f"🗑️ FILE TREE DEBUG: Delete button clicked")
        selection = self.files_view.get_selection()
        model, tree_iter = selection.get_selected()
        self.logger.info(f"🗑️ FILE TREE DEBUG: Selection - model: {model is not None}, tree_iter: {tree_iter is not None}")
        
        if tree_iter:
            file_name = model.get_value(tree_iter, 1)  # Name is in column 1
            file_path = model.get_value(tree_iter, 2)  # Path is in column 2  
            file_type = model.get_value(tree_iter, 3)  # Type is in column 3
            
            self.logger.info(f"🗑️ FILE TREE DEBUG: Selected item - name: '{file_name}', path: '{file_path}', type: '{file_type}'")
            self.logger.info(f"🗑️ FILE TREE DEBUG: Type check - file_type == 'folder': {file_type == 'folder'}")
            self.logger.info(f"🗑️ FILE TREE DEBUG: Path check - 'Operations' in file_path: {'Operations' in file_path}")
            self.logger.info(f"🗑️ FILE TREE DEBUG: Combined condition: {file_type == 'folder' and 'Operations' in file_path}")
            
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
                        self.logger.info(f"🗑️ FILE TREE DELETION: Attempting to delete folder: {file_path}")
                        self.logger.info(f"🗑️ FILE TREE DELETION: Folder exists: {os.path.exists(file_path)}")
                        shutil.rmtree(file_path)
                        self._load_operations_files()  # Refresh the tree
                        self.logger.info(f"🗑️ FILE TREE DELETION: Successfully deleted folder: {file_path}")
                        self._update_status(f"Deleted operation folder: {file_name}")
                    except Exception as e:
                        self.logger.error(f"Failed to delete operation folder: {e}")
                        self._update_status(f"Error deleting folder: {e}")
            else:
                self.logger.info(f"🗑️ FILE TREE DEBUG: Selection failed conditions - not deleting")
                self._update_status("Please select an operation folder to delete")
        else:
            self.logger.info(f"🗑️ FILE TREE DEBUG: No tree_iter - no selection found")
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
        """Load operations data from database (database-only approach)."""
        try:
            # Convert current in-memory operations to format expected by analysis methods
            operations_dict = {}
            for op_id, operation in self.operations.items():
                operations_dict[op_id] = {
                    'name': operation.name,
                    'status': operation.status.value,
                    'progress': operation.progress,
                    'start_time': operation.start_time.isoformat() if operation.start_time else None,
                    'end_time': operation.end_time.isoformat() if operation.end_time else None
                }
            return {'operations': operations_dict}
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
                    if (datetime.utcnow() - end_dt).days == 0:
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
            report_lines.append(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
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
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
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
                cutoff_date = datetime.utcnow() - timedelta(days=30)
                
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

    def _cleanup_orphaned_folders(self) -> None:
        """Remove operation folders that don't have corresponding database records."""
        try:
            # Get all database operation names
            operation_service = self.service_container.operation_service
            db_operations = operation_service.get_all()
            db_operation_names = {op.name for op in db_operations}

            # Get Operations directory using directories service (not hardcoded path)
            operations_dir = self.service_container.directories_service.get_operations_path()
            
            if not operations_dir.exists():
                return
                
            orphaned_folders = []
            for item in operations_dir.iterdir():
                if item.is_dir():
                    folder_name = item.name
                    # Skip special folders
                    if folder_name in ['grading_files', '.git', '__pycache__']:
                        continue
                    # Check if folder has a corresponding database operation
                    if folder_name not in db_operation_names:
                        orphaned_folders.append(item)
            
            # Remove orphaned folders
            removed_count = 0
            for folder in orphaned_folders:
                try:
                    import shutil
                    shutil.rmtree(folder)
                    self.logger.info(f"🗑️ CLEANUP: Removed orphaned folder: {folder.name}")
                    removed_count += 1
                except Exception as e:
                    self.logger.error(f"🗑️ CLEANUP: Failed to remove orphaned folder {folder.name}: {e}")
            
            if removed_count > 0:
                self.logger.info(f"🗑️ CLEANUP: Removed {removed_count} orphaned operation folders")
                
        except Exception as e:
            self.logger.error(f"Error during orphaned folder cleanup: {e}")
    
    def cleanup(self) -> None:
        """Cleanup resources."""
        self.logger.info("Starting operations monitoring panel cleanup...")
        try:
            self._stop_monitoring()
            # Database automatically updated through operation monitoring
            self.logger.info(f"Operations monitoring panel cleanup completed - saved {len(self.operations)} operations")
        except Exception as e:
            self.logger.error(f"Error during operations panel cleanup: {e}")
    
    
    
    def _smart_refresh_from_database(self) -> None:
        """Smart refresh: preserve running operations, reload others from database."""
        try:
            self.logger.info("Smart refresh: preserving running operations...")
            
            # Save running/paused operations with their current progress
            running_operations = {
                op_id: op for op_id, op in self.operations.items() 
                if op.status in [OperationStatus.RUNNING, OperationStatus.PAUSED]
            }
            
            # Create a set of running operation names to avoid duplicates
            running_operation_names = {op.name for op in running_operations.values()}
            
            self.logger.info(f"Preserving {len(running_operations)} running operations: {list(running_operation_names)}")
            
            # Get all operations from database
            with self.service_container.database_service.get_read_only_session() as session:
                from app.models.operation import Operation as DBOperation
                db_operations = session.query(DBOperation).all()

            self.logger.info(f"Found {len(db_operations)} operations in database")
            print(f"=== SMART REFRESH DIAGNOSTIC ===")
            print(f"Database operations found: {len(db_operations)}")
            print(f"Operation names: {[db_op.name for db_op in db_operations]}")
            print(f"Running operations to preserve: {list(running_operation_names)}")
            
            # Instead of clearing all, only remove non-running operations to preserve process handles
            non_running_ids = [
                op_id for op_id, op in self.operations.items() 
                if op.status not in [OperationStatus.RUNNING, OperationStatus.PAUSED]
            ]
            
            # Remove only non-running operations (keeps process handles for running ones)
            for op_id in non_running_ids:
                del self.operations[op_id]
            
            # Convert database operations to UI operations, but skip those that are running
            db_loaded_count = 0
            db_skipped_count = 0
            
            for db_op in db_operations:
                try:
                    # For operations running in-memory, update their status from database while preserving process handles
                    if db_op.name in running_operation_names:
                        self.logger.debug(f"Updating status for running operation from DB: {db_op.name}")
                        # Find the in-memory operation
                        in_memory_op = None
                        for op in running_operations.values():
                            if op.name == db_op.name:
                                in_memory_op = op
                                break
                        
                        if in_memory_op:
                            # Update status, progress, and step from database while keeping process handle
                            if db_op.status == 'COMPLETED':
                                in_memory_op.status = OperationStatus.COMPLETED
                                in_memory_op.progress = getattr(db_op, 'progress', 1.0)
                                in_memory_op.current_step = getattr(db_op, 'current_step', 'Process completed')
                                self.logger.info(f"Updated running operation {db_op.name} to COMPLETED from database")
                            elif db_op.status == 'FAILED':
                                in_memory_op.status = OperationStatus.FAILED
                                in_memory_op.progress = getattr(db_op, 'progress', 0.0)
                                in_memory_op.current_step = getattr(db_op, 'current_step', 'Process failed')
                                self.logger.info(f"Updated running operation {db_op.name} to FAILED from database")
                            else:
                                # Update progress for still-running operations
                                in_memory_op.progress = getattr(db_op, 'progress', in_memory_op.progress)
                                in_memory_op.current_step = getattr(db_op, 'current_step', in_memory_op.current_step)
                        
                        db_skipped_count += 1
                        continue
                    
                    ui_operation = self._convert_db_operation_to_ui_operation(db_op)
                    self.operations[ui_operation.id] = ui_operation
                    self.logger.debug(f"Loaded from DB: {ui_operation.name} ({ui_operation.operation_type.value}, {ui_operation.status.value})")
                    db_loaded_count += 1
                except Exception as e:
                    self.logger.warning(f"Failed to convert database operation {db_op.name}: {e}")
                    print(f"ERROR converting DB operation '{db_op.name}': {e}")
            
            # Running operations are already preserved in self.operations with process handles intact
            self.logger.info(f"Running operations already preserved with process handles: {len(running_operations)} operations")

            self.logger.info(f"Smart refresh complete: {len(self.operations)} total operations ({db_loaded_count} from DB, {len(running_operations)} running preserved, {db_skipped_count} duplicates avoided)")
            print(f"Smart refresh results:")
            print(f"  - Loaded from DB: {db_loaded_count} operations")
            print(f"  - Preserved running: {len(running_operations)} operations")
            print(f"  - Total in memory: {len(self.operations)} operations")
            print(f"  - Operation names in memory: {[op.name for op in self.operations.values()]}")
            print(f"=== END SMART REFRESH DIAGNOSTIC ===")
            
        except Exception as e:
            self.logger.error(f"Failed to perform smart refresh from database: {e}", exc_info=True)

    def _load_operations_from_database(self) -> None:
        """Load all operations from database (single source of truth) with robust error handling."""
        try:
            self.logger.info("Loading all operations from database...")
            
            # IMPORTANT: Preserve process references for running operations before clearing
            # This is critical for pause/resume functionality to work
            preserved_processes = {}
            for op_id, operation in self.operations.items():
                if operation.process is not None or operation.pid is not None:
                    preserved_processes[operation.name] = {
                        'process': operation.process,
                        'pid': operation.pid,
                        'working_directory': operation.working_directory
                    }
                    self.logger.debug(f"Preserving process info for {operation.name}: PID={operation.pid}")
            
            # Clear existing operations
            self.operations.clear()
            
            # Get all operations from database with retry logic
            db_operations = []
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    with self.service_container.database_service.get_read_only_session() as session:
                        from app.models.operation import Operation as DBOperation
                        db_operations = session.query(DBOperation).all()
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    self.logger.warning(f"Database query attempt {attempt + 1} failed, retrying: {e}")
                    import time
                    time.sleep(0.5)
            
            self.logger.info(f"Found {len(db_operations)} operations in database")
            
            # Convert database operations to UI operations
            successful_conversions = 0
            failed_conversions = 0
            
            for db_op in db_operations:
                try:
                    ui_operation = self._convert_db_operation_to_ui_operation(db_op)
                    self.operations[ui_operation.id] = ui_operation
                    
                    # CRITICAL: Restore preserved process references for running operations
                    # This enables pause/resume functionality for hydration operations
                    if ui_operation.name in preserved_processes:
                        preserved = preserved_processes[ui_operation.name]
                        ui_operation.process = preserved['process']
                        ui_operation.pid = preserved['pid']
                        ui_operation.working_directory = preserved['working_directory']
                        self.logger.debug(f"Restored process info for {ui_operation.name}: PID={ui_operation.pid}")
                    
                    successful_conversions += 1
                    self.logger.debug(f"Loaded: {ui_operation.name} ({ui_operation.operation_type.value}, {ui_operation.status.value})")
                except Exception as e:
                    failed_conversions += 1
                    self.logger.warning(f"Failed to convert database operation {db_op.name}: {e}")
            
            self.logger.info(f"Successfully loaded {successful_conversions} operations from database ({failed_conversions} failed)")
            
            # Force UI update after loading - CRITICAL for fixing empty panel issue
            from gi.repository import GLib
            GLib.idle_add(self._update_operations_list)
            
            # Also update the UI immediately if we're on the main thread
            try:
                self._update_operations_list()
            except Exception as e:
                self.logger.debug(f"Direct UI update failed (expected if not on main thread): {e}")
            
        except Exception as e:
            self.logger.error(f"CRITICAL: Failed to load operations from database: {e}", exc_info=True)
            # Even on failure, ensure UI is updated with empty state
            from gi.repository import GLib
            GLib.idle_add(self._update_operations_list)
    
    def _convert_db_status_to_ui_status(self, db_status: str) -> OperationStatus:
        """Convert database status string to UI OperationStatus enum."""
        status_mapping = {
            'QUEUED': OperationStatus.PENDING,
            'RUNNING': OperationStatus.RUNNING,  
            'COMPLETED': OperationStatus.COMPLETED,
            'FAILED': OperationStatus.FAILED,
            'CANCELLED': OperationStatus.CANCELLED,
        }
        return status_mapping.get(db_status, OperationStatus.PENDING)
    
    def _safe_load_operations_from_database(self) -> None:
        """Thread-safe database refresh that only loads NEW operations without clearing existing ones."""
        try:
            # Get database operations without clearing in-memory operations
            db_operations = []
            max_retries = 3
            
            for attempt in range(max_retries):
                try:
                    with self.service_container.database_service.get_read_only_session() as session:
                        from app.models.operation import Operation as DBOperation
                        db_operations = session.query(DBOperation).all()
                        break
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    self.logger.warning(f"Database query attempt {attempt + 1} failed, retrying: {e}")
                    import time
                    time.sleep(0.1)
            
            # Add new operations and update existing ones from database
            new_operations = []
            updated_operations = []
            
            for db_op in db_operations:
                # Check if we already have this operation
                existing_op_found = None
                for existing_id, existing_op in self.operations.items():
                    if (hasattr(existing_op, 'name') and existing_op.name == db_op.name) or \
                       (existing_id == str(db_op.id)):
                        existing_op_found = existing_op
                        break
                
                if existing_op_found is None:
                    # This is a new operation - add it
                    try:
                        ui_operation = self._convert_db_operation_to_ui_operation(db_op)
                        self.operations[ui_operation.id] = ui_operation
                        new_operations.append(ui_operation.name)
                        self.logger.info(f"Added new operation from database: {ui_operation.name}")
                    except Exception as e:
                        self.logger.warning(f"Failed to add new operation {db_op.name}: {e}")
                else:
                    # This operation exists - update its database-stored progress/status
                    try:
                        # Only update database fields, preserve process handles
                        if hasattr(db_op, 'progress') and db_op.progress is not None:
                            if existing_op_found.progress != db_op.progress:
                                existing_op_found.progress = db_op.progress
                                updated_operations.append(db_op.name)
                        
                        if hasattr(db_op, 'current_step') and db_op.current_step:
                            existing_op_found.current_step = db_op.current_step
                        
                        # Update status if it changed in database
                        db_status = self._convert_db_status_to_ui_status(db_op.status)
                        if existing_op_found.status != db_status:
                            existing_op_found.status = db_status
                            if db_status == OperationStatus.COMPLETED and not existing_op_found.end_time:
                                existing_op_found.end_time = getattr(db_op, 'completed_at', datetime.utcnow())
                            
                    except Exception as e:
                        self.logger.warning(f"Failed to update existing operation {db_op.name}: {e}")
            
            if new_operations or updated_operations:
                # Update UI if we added new operations or updated existing ones
                from gi.repository import GLib
                GLib.idle_add(self._update_operations_list)
                
                if new_operations:
                    self.logger.info(f"Added {len(new_operations)} new operations from database")
                if updated_operations:
                    self.logger.info(f"Updated {len(updated_operations)} existing operations from database: {updated_operations}")
            
        except Exception as e:
            self.logger.warning(f"Safe database refresh failed: {e}")
            # Don't crash - just log and continue
    
    def _simple_progress_update(self) -> bool:
        """SIMPLE SOLUTION: Directly read progress files and update operations every 5 seconds."""
        try:
            operations_dir = Path("Operations")
            if not operations_dir.exists():
                return True  # Continue timer
            
            # Check each operation folder for progress files
            for op_folder in operations_dir.iterdir():
                if not op_folder.is_dir():
                    continue

                # Try JSON file first (new format), then fall back to text
                json_progress_file = op_folder / "genmic_progress.json"
                txt_progress_file = op_folder / "genmic_progress.txt"

                progress_val = None
                message = None

                # Prefer JSON format
                if json_progress_file.exists():
                    try:
                        import json
                        content = json_progress_file.read_text().strip()
                        # Handle "json " prefix format
                        if content.startswith("json "):
                            content = content[5:]
                        data = json.loads(content)
                        if 'percent_complete' in data and 'step' in data:
                            progress_val = data['percent_complete'] / 100.0
                            message = data['step']
                    except (json.JSONDecodeError, KeyError) as e:
                        self.logger.debug(f"Failed to parse JSON progress for {op_folder.name}: {e}")

                # Only use text format if JSON doesn't exist or failed
                if progress_val is None and txt_progress_file.exists():
                    try:
                        content = txt_progress_file.read_text().strip()
                        if content.startswith("PROGRESS:"):
                            # Parse: "PROGRESS: 0.65 Distributing phases"
                            data = content[9:].strip()  # Remove "PROGRESS: "
                            parts = data.split(' ', 1)
                            if len(parts) >= 2:
                                progress_val = float(parts[0])
                                message = parts[1]
                    except Exception as e:
                        self.logger.debug(f"Failed to parse text progress for {op_folder.name}: {e}")

                # Skip if no progress data found
                if progress_val is None or message is None:
                    continue

                try:
                    
                    # Phase 2: Use clean operation naming without genmic_input_ prefix
                    # Find matching operation
                    operation_name = op_folder.name
                    matching_op = None
                    
                    for op in self.operations.values():
                        if op.name == operation_name:
                            matching_op = op
                            break
                    
                    if matching_op:
                        # Update progress directly
                        old_progress = matching_op.progress
                        matching_op.progress = progress_val
                        matching_op.current_step = message
                        
                        # Mark as completed if progress >= 1.0
                        if progress_val >= 1.0 and matching_op.status != OperationStatus.COMPLETED:
                            matching_op.status = OperationStatus.COMPLETED
                            matching_op.end_time = datetime.utcnow()
                        
                        # Update operation details if this operation is currently displayed (ALWAYS)
                        if self._currently_displayed_operation:
                            self.logger.debug(f"DETAIL CHECK: Currently displayed: {self._currently_displayed_operation.id}, Updated: {matching_op.id}")
                            if self._currently_displayed_operation.id == matching_op.id:
                                self.logger.debug(f"DETAIL UPDATE: Updating details for {matching_op.id}")
                                self._update_operation_details(matching_op)
                            else:
                                self.logger.debug(f"DETAIL SKIP: IDs don't match - displayed: {self._currently_displayed_operation.id}, updated: {matching_op.id}")
                        else:
                            self.logger.debug("DETAIL SKIP: No operation currently displayed")
                        
                        # Log progress change
                        if abs(progress_val - old_progress) > 0.01:
                            self.logger.info(f"SIMPLE UPDATE: {operation_name} -> {progress_val:.1%} - {message}")
                        
                        # Schedule UI update on main thread (thread-safe)
                        from gi.repository import GLib
                        GLib.idle_add(self._update_operations_list)

                        # Database update is thread-safe
                        self._update_operation_in_database(matching_op)
                
                except Exception as e:
                    self.logger.warning(f"Simple progress update failed for {op_folder.name}: {e}")
                    
        except Exception as e:
            self.logger.error(f"Simple progress update failed: {e}")
        
        return True  # Continue timer
    
    def _update_operation_in_database(self, operation: 'Operation') -> None:
        """Update an operation's status in the database using the operation service."""
        try:
            # Convert UI status enum to database status enum
            from app.models.operation import OperationStatus as DBOperationStatus
            
            ui_to_db_status_mapping = {
                OperationStatus.PENDING: DBOperationStatus.QUEUED,
                OperationStatus.RUNNING: DBOperationStatus.RUNNING,
                OperationStatus.COMPLETED: DBOperationStatus.COMPLETED,
                OperationStatus.FAILED: DBOperationStatus.FAILED,
                OperationStatus.CANCELLED: DBOperationStatus.CANCELLED,
                OperationStatus.PAUSED: DBOperationStatus.RUNNING,  # Map paused to running in DB
            }
            
            db_status = ui_to_db_status_mapping.get(operation.status, DBOperationStatus.QUEUED)
            
            # Use the operation service's update method
            success = self.service_container.operation_service.update_status(
                name=operation.name,
                status=db_status,
                progress=operation.progress,
                current_step=operation.current_step
            )
            
            if success:
                self.logger.debug(f"Updated database operation: {operation.name} -> {operation.status.value}")
            else:
                self.logger.warning(f"Failed to update operation in database: {operation.name}")
                    
        except Exception as e:
            self.logger.error(f"Failed to update operation in database: {operation.name}: {e}")
        self._sync_with_active_hydration_simulations()
        
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
        
        # Map database status to UI status (using string values)
        status_mapping = {
            'QUEUED': OperationStatus.PENDING,
            'RUNNING': OperationStatus.RUNNING,  
            'COMPLETED': OperationStatus.COMPLETED,
            'FAILED': OperationStatus.FAILED,
            'CANCELLED': OperationStatus.CANCELLED,
        }
        
        # Map database type to UI type (handle both uppercase and lowercase formats)
        type_mapping = {
            'HYDRATION': OperationType.HYDRATION_SIMULATION,
            'MICROSTRUCTURE': OperationType.MICROSTRUCTURE_GENERATION,
            'ELASTIC_MODULI': OperationType.ELASTIC_MODULI_CALCULATION,
            'ANALYSIS': OperationType.PROPERTY_CALCULATION,
            'EXPORT': OperationType.FILE_OPERATION,
            'IMPORT': OperationType.FILE_OPERATION,
            # Handle lowercase variants
            'hydration': OperationType.HYDRATION_SIMULATION,
            'microstructure': OperationType.MICROSTRUCTURE_GENERATION,
            'microstructure_generation': OperationType.MICROSTRUCTURE_GENERATION,
            'hydration_simulation': OperationType.HYDRATION_SIMULATION,
            'elastic_moduli': OperationType.ELASTIC_MODULI_CALCULATION,
            'elastic_moduli_calculation': OperationType.ELASTIC_MODULI_CALCULATION,
            'analysis': OperationType.PROPERTY_CALCULATION,
        }
        
        # Convert status and type
        ui_status = status_mapping.get(db_op.status, OperationStatus.PENDING)
        ui_type = type_mapping.get(db_op.operation_type, OperationType.BATCH_OPERATION)
        
        # Calculate progress and default current step
        progress = 0.0
        current_step = ""

        if ui_status == OperationStatus.COMPLETED:
            progress = 1.0
            current_step = "Process completed"
        elif ui_status == OperationStatus.RUNNING:
            # Use a small initial progress for running operations to indicate they've started
            progress = 0.05  # 5% - indicates process has started
            # Set a meaningful default step for running operations
            if ui_type == OperationType.HYDRATION_SIMULATION:
                current_step = "Hydration simulation in progress..."
            elif ui_type == OperationType.ELASTIC_MODULI_CALCULATION:
                current_step = "Process started"  # This will be updated by JSON progress tracking
            else:
                current_step = "Operation in progress..."
        elif ui_status == OperationStatus.PENDING:
            # Use actual current_step if available, otherwise default message
            current_step = db_op.current_step if (db_op.current_step and db_op.current_step.strip()) else "Queued for execution"
        elif ui_status == OperationStatus.FAILED:
            current_step = "Operation failed"
        elif ui_status == OperationStatus.CANCELLED:
            current_step = "Operation cancelled"
        
        # Fix timezone-aware datetime issues that cause negative durations
        start_time = db_op.started_at
        end_time = db_op.completed_at
        
        # Ensure times are timezone-naive (but DO NOT modify valid historical timestamps)
        if start_time:
            # If start_time is timezone-aware, convert to naive
            if start_time.tzinfo is not None:
                start_time = start_time.replace(tzinfo=None)
            # DO NOT modify historical timestamps - they are valid even if old
            # The original logic incorrectly detected valid past times as "future" times
            # and overwrote them with current time, corrupting completed operation timestamps
        
        if end_time and end_time.tzinfo is not None:
            end_time = end_time.replace(tzinfo=None)
        
        # Create UI operation
        return Operation(
            id=db_op.name,  # Use name as ID
            name=db_op.name,
            operation_type=ui_type,
            status=ui_status,
            progress=progress,
            start_time=start_time,
            end_time=end_time,
            paused_time=None,
            estimated_duration=None,
            current_step=current_step,
            total_steps=0,
            completed_steps=0,
            cpu_usage=0.0,
            memory_usage=0.0,
            disk_usage=0.0,
            error_message=None,  # Operation model doesn't have error_message field
            log_entries=[],
            metadata={"source": "database", "output_directory": f"Operations/{db_op.name}"}
        )

    # MOVED TO RESULTS PANEL: The following methods have been moved to the dedicated Results panel
    # to separate operation monitoring from results analysis functionality:
    # - _has_3d_results()
    # - _has_csv_data()
    # - _on_view_3d_results_clicked()
    # - _on_plot_data_clicked()

    # REMOVED: _on_view_3d_results_clicked() and _on_plot_data_clicked() methods
    # These have been moved to the dedicated Results panel for better separation of concerns

    def _sync_with_active_hydration_simulations(self) -> None:
        """Synchronize operations panel with active hydration simulations."""
        try:
            # Get hydration executor service
            hydration_service = self.service_container.hydration_executor_service
            
            # Get active simulations info (access the full dictionary)
            active_sims = hydration_service.active_simulations
            
            if active_sims:
                self.logger.debug(f"Found {len(active_sims)} active hydration simulations: {list(active_sims.keys())}")
            
            for sim_name, sim_info in active_sims.items():
                # Find corresponding operation in our list
                matching_op = None
                self.logger.debug(f"Looking for operation matching simulation '{sim_name}'")
                
                for op_id, operation in self.operations.items():
                    self.logger.debug(f"  Checking operation: name='{operation.name}', type={operation.operation_type}, status={operation.status}")
                    # Check for exact name match or if operation name contains simulation name
                    name_match = (operation.name == sim_name or 
                                sim_name in operation.name or 
                                operation.name in sim_name)
                    
                    if (name_match and 
                        operation.operation_type == OperationType.HYDRATION_SIMULATION and
                        operation.status == OperationStatus.RUNNING):
                        matching_op = operation
                        self.logger.debug(f"  ✓ Found matching operation: {operation.name}")
                        break
                
                if matching_op:
                    # Update operation with latest simulation progress
                    progress_data = sim_info.get('progress')
                    self.logger.debug(f"Found matching operation for '{sim_name}', progress_data: {type(progress_data)}")
                    if progress_data:
                        # Update progress percentage
                        if hasattr(progress_data, 'percent_complete'):
                            matching_op.progress = progress_data.percent_complete / 100.0
                        
                        # Update current step with detailed information
                        if hasattr(progress_data, 'cycle') and hasattr(progress_data, 'time_hours'):
                            cycle = progress_data.cycle
                            time_h = progress_data.time_hours
                            doh = getattr(progress_data, 'degree_of_hydration', 0.0)
                            matching_op.current_step = f"Cycle {cycle}, Time: {time_h:.2f}h, DOH: {doh:.3f}"
                        else:
                            matching_op.current_step = "Hydration simulation in progress..."
                        
                        # Update estimated remaining time
                        if hasattr(progress_data, 'estimated_time_remaining'):
                            remaining_hours = progress_data.estimated_time_remaining
                            if remaining_hours and remaining_hours > 0:
                                matching_op.estimated_duration = timedelta(hours=remaining_hours)
                        
                        self.logger.debug(f"Synchronized hydration operation {sim_name}: {matching_op.progress:.1%} complete, step: {matching_op.current_step}")
                else:
                    self.logger.warning(f"No matching operation found for active simulation '{sim_name}'")
                    self.logger.debug(f"Available operations: {[(op.name, op.operation_type, op.status) for op in self.operations.values()]}")
                        
        except Exception as e:
            self.logger.error(f"Error syncing with active hydration simulations: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")

    def _validate_operations_data(self) -> None:
        """Validate and fix operations data consistency to prevent display glitches."""
        try:
            self.logger.debug("Validating operations data consistency...")
            changes_made = False
            
            for operation_id, operation in self.operations.items():
                # Fix progress values for completed operations
                if operation.status == OperationStatus.COMPLETED and operation.progress != 1.0:
                    old_progress = operation.progress
                    operation.progress = 1.0
                    self.logger.info(f"Fixed completed operation progress: {operation.name} ({old_progress} -> 1.0)")
                    changes_made = True
                
                # Fix progress values for failed/cancelled operations
                if operation.status in [OperationStatus.FAILED, OperationStatus.CANCELLED] and operation.progress > 1.0:
                    old_progress = operation.progress
                    operation.progress = min(operation.progress / 100.0, 1.0) if operation.progress > 1.0 else operation.progress
                    self.logger.info(f"Fixed failed/cancelled operation progress: {operation.name} ({old_progress} -> {operation.progress})")
                    changes_made = True
                
                # Ensure running operations don't exceed 100% progress
                if operation.status == OperationStatus.RUNNING and operation.progress > 1.0:
                    old_progress = operation.progress
                    operation.progress = min(operation.progress / 100.0, 0.99)  # Cap at 99% for running
                    self.logger.info(f"Fixed running operation progress: {operation.name} ({old_progress} -> {operation.progress})")
                    changes_made = True
                
                # Fix pending operations with non-zero progress
                if operation.status == OperationStatus.PENDING and operation.progress > 0.0:
                    old_progress = operation.progress
                    operation.progress = 0.0
                    self.logger.info(f"Fixed pending operation progress: {operation.name} ({old_progress} -> 0.0)")
                    changes_made = True
            
            # Enhanced duplicate detection and removal
            self.logger.debug(f"Starting duplicate detection on {len(self.operations)} operations")
            
            # Group operations by name+type to find all instances
            operation_groups = {}  # (name, operation_type) -> [operation_ids]
            
            for operation_id, operation in self.operations.items():
                key = (operation.name, operation.operation_type)
                if key not in operation_groups:
                    operation_groups[key] = []
                operation_groups[key].append(operation_id)
            
            # Find and resolve duplicates
            duplicates_to_remove = []
            
            for key, operation_ids in operation_groups.items():
                if len(operation_ids) > 1:
                    name, op_type = key
                    self.logger.warning(f"Found {len(operation_ids)} duplicate operations for '{name}' ({op_type.value})")
                    
                    # Sort by preference: database > newer start_time > alphabetical ID
                    operations_with_ids = [(op_id, self.operations[op_id]) for op_id in operation_ids]
                    
                    def sort_key(item):
                        op_id, operation = item
                        # Primary: database source (lower number = higher priority)
                        source_priority = 0 if (hasattr(operation, 'metadata') and 
                                              operation.metadata and 
                                              operation.metadata.get('source') == 'database') else 1
                        # Secondary: newer start time (negative for descending order)
                        time_priority = -(operation.start_time.timestamp() if operation.start_time else 0)
                        # Tertiary: operation ID for consistency
                        return (source_priority, time_priority, op_id)
                    
                    sorted_ops = sorted(operations_with_ids, key=sort_key)
                    
                    # Keep the first (highest priority) operation, remove the rest
                    keep_id, keep_op = sorted_ops[0]
                    for op_id, operation in sorted_ops[1:]:
                        duplicates_to_remove.append(op_id)
                        source = getattr(operation, 'metadata', {}).get('source', 'unknown') if hasattr(operation, 'metadata') else 'unknown'
                        self.logger.info(f"Marking duplicate for removal: {operation.name} (ID: {op_id}, source: {source})")
                    
                    keep_source = getattr(keep_op, 'metadata', {}).get('source', 'unknown') if hasattr(keep_op, 'metadata') else 'unknown'
                    self.logger.info(f"Keeping operation: {keep_op.name} (ID: {keep_id}, source: {keep_source})")
            
            # Also check for operations with similar names (handles filesystem vs database naming)
            name_similarity_groups = {}  # normalized_name -> [operation_ids]
            
            for operation_id, operation in self.operations.items():
                # Normalize the name by removing common prefixes/suffixes
                normalized_name = operation.name
                if normalized_name.startswith('fs_'):
                    normalized_name = normalized_name[3:]  # Remove 'fs_' prefix
                if normalized_name.startswith('HydrationSim_'):
                    # Extract the base name part for hydration simulations
                    base_name = normalized_name.replace('HydrationSim_', '')
                    # If it has a timestamp, remove it to match filesystem names
                    if '_202508' in base_name:  # Assuming 2025/08 format
                        base_name = base_name.split('_202508')[0]
                    normalized_name = base_name
                
                if normalized_name not in name_similarity_groups:
                    name_similarity_groups[normalized_name] = []
                name_similarity_groups[normalized_name].append(operation_id)
            
            # Find operations that should be considered duplicates based on similar names
            for normalized_name, operation_ids in name_similarity_groups.items():
                if len(operation_ids) > 1:
                    # Check if these operations have different types (hydration vs microstructure)
                    types_in_group = set()
                    for op_id in operation_ids:
                        if op_id in self.operations:  # Make sure it hasn't been removed already
                            types_in_group.add(self.operations[op_id].operation_type)
                    
                    # Only merge if they have the same operation type
                    if len(types_in_group) == 1:
                        op_type = list(types_in_group)[0]
                        self.logger.warning(f"Found {len(operation_ids)} similar operations for base name '{normalized_name}' ({op_type.value})")
                        
                        # Use the same sorting logic as above
                        similar_ops = [(op_id, self.operations[op_id]) for op_id in operation_ids if op_id in self.operations]
                        
                        if len(similar_ops) > 1:
                            def sort_key(item):
                                op_id, operation = item
                                source_priority = 0 if (hasattr(operation, 'metadata') and 
                                                      operation.metadata and 
                                                      operation.metadata.get('source') == 'database') else 1
                                time_priority = -(operation.start_time.timestamp() if operation.start_time else 0)
                                return (source_priority, time_priority, op_id)
                            
                            sorted_similar = sorted(similar_ops, key=sort_key)
                            
                            # Keep the first, remove the rest
                            keep_id, keep_op = sorted_similar[0]
                            for op_id, operation in sorted_similar[1:]:
                                if op_id not in duplicates_to_remove:  # Don't double-add
                                    duplicates_to_remove.append(op_id)
                                    source = getattr(operation, 'metadata', {}).get('source', 'unknown') if hasattr(operation, 'metadata') else 'unknown'
                                    self.logger.info(f"Marking similar operation for removal: {operation.name} (ID: {op_id}, source: {source})")
            
            # Remove duplicate operations
            for duplicate_id in duplicates_to_remove:
                if duplicate_id in self.operations:
                    removed_op = self.operations.pop(duplicate_id)
                    self.logger.info(f"Removed duplicate operation: {removed_op.name}")
                    changes_made = True
            
            if changes_made:
                # Save the cleaned data
                self._save_operations_to_file()
                # Update the UI
                GLib.idle_add(self._update_operations_list)
                self.logger.info("Operations data validation completed with changes - UI updated")
            else:
                self.logger.debug("Operations data validation completed - no changes needed")
                
        except Exception as e:
            self.logger.error(f"Error during operations data validation: {e}")


# Register the widget
GObject.type_register(OperationsMonitoringPanel)
"""
Async Operations Utility for VCCTL GTK Application
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, GObject

import asyncio
import threading
import queue
import logging
from typing import Callable, Any, Optional, Dict
from dataclasses import dataclass
from enum import Enum


class OperationStatus(Enum):
    """Operation status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class OperationResult:
    """Result of an async operation"""
    status: OperationStatus
    result: Any = None
    error: Optional[Exception] = None
    progress: int = 0
    message: str = ""


class AsyncOperationManager:
    """Manages async operations with UI responsiveness"""
    
    def __init__(self):
        self.operations: Dict[str, OperationResult] = {}
        self.cancel_events: Dict[str, threading.Event] = {}
        self.logger = logging.getLogger(__name__)
        
    def run_async_operation(self, 
                           operation_id: str,
                           operation_func: Callable,
                           success_callback: Optional[Callable] = None,
                           error_callback: Optional[Callable] = None,
                           progress_callback: Optional[Callable] = None,
                           *args, **kwargs) -> str:
        """
        Run an operation asynchronously with progress tracking
        
        Args:
            operation_id: Unique identifier for the operation
            operation_func: Function to execute
            success_callback: Called on successful completion
            error_callback: Called on error
            progress_callback: Called on progress updates
            *args, **kwargs: Arguments for operation_func
            
        Returns:
            Operation ID
        """
        
        # Initialize operation tracking
        self.operations[operation_id] = OperationResult(
            status=OperationStatus.PENDING,
            progress=0,
            message="Starting operation..."
        )
        
        # Create cancel event
        cancel_event = threading.Event()
        self.cancel_events[operation_id] = cancel_event
        
        # Create progress updater
        def update_progress(progress: int, message: str = ""):
            if cancel_event.is_set():
                return
            
            self.operations[operation_id].progress = progress
            self.operations[operation_id].message = message
            
            if progress_callback:
                GLib.idle_add(progress_callback, progress, message)
        
        # Run operation in thread
        def run_operation():
            try:
                self.operations[operation_id].status = OperationStatus.RUNNING
                
                # Execute operation with progress updates
                if hasattr(operation_func, '__code__') and 'progress_callback' in operation_func.__code__.co_varnames:
                    result = operation_func(*args, progress_callback=update_progress, **kwargs)
                else:
                    result = operation_func(*args, **kwargs)
                
                if cancel_event.is_set():
                    self.operations[operation_id].status = OperationStatus.CANCELLED
                    self.operations[operation_id].message = "Operation cancelled"
                    return
                
                # Operation completed successfully
                self.operations[operation_id].status = OperationStatus.COMPLETED
                self.operations[operation_id].result = result
                self.operations[operation_id].progress = 100
                self.operations[operation_id].message = "Operation completed successfully"
                
                if success_callback:
                    GLib.idle_add(success_callback, result)
                    
            except Exception as e:
                self.logger.error(f"Operation {operation_id} failed: {e}")
                
                self.operations[operation_id].status = OperationStatus.FAILED
                self.operations[operation_id].error = e
                self.operations[operation_id].message = f"Operation failed: {str(e)}"
                
                if error_callback:
                    GLib.idle_add(error_callback, e)
            
            finally:
                # Clean up
                if operation_id in self.cancel_events:
                    del self.cancel_events[operation_id]
        
        # Start operation in background thread
        thread = threading.Thread(target=run_operation, daemon=True)
        thread.start()
        
        return operation_id
    
    def cancel_operation(self, operation_id: str) -> bool:
        """Cancel a running operation"""
        if operation_id in self.cancel_events:
            self.cancel_events[operation_id].set()
            return True
        return False
    
    def get_operation_status(self, operation_id: str) -> Optional[OperationResult]:
        """Get status of an operation"""
        return self.operations.get(operation_id)
    
    def get_all_operations(self) -> Dict[str, OperationResult]:
        """Get all operations"""
        return self.operations.copy()
    
    def clear_completed_operations(self):
        """Clear completed operations"""
        completed_ops = [
            op_id for op_id, result in self.operations.items()
            if result.status in [OperationStatus.COMPLETED, OperationStatus.FAILED, OperationStatus.CANCELLED]
        ]
        
        for op_id in completed_ops:
            del self.operations[op_id]


class LoadingDialog(Gtk.Dialog):
    """Dialog for showing loading progress"""
    
    def __init__(self, parent, title="Loading...", message="Please wait..."):
        super().__init__(title, parent, 0)
        
        self.set_modal(True)
        self.set_default_size(400, 150)
        self.set_resizable(False)
        
        # Create content
        content_area = self.get_content_area()
        content_area.set_spacing(10)
        content_area.set_margin_top(20)
        content_area.set_margin_bottom(20)
        content_area.set_margin_left(20)
        content_area.set_margin_right(20)
        
        # Message label
        self.message_label = Gtk.Label(message)
        self.message_label.set_line_wrap(True)
        content_area.pack_start(self.message_label, False, False, 0)
        
        # Progress bar
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_show_text(True)
        content_area.pack_start(self.progress_bar, False, False, 0)
        
        # Cancel button
        self.cancel_button = Gtk.Button("Cancel")
        self.cancel_button.connect("clicked", self._on_cancel_clicked)
        content_area.pack_start(self.cancel_button, False, False, 0)
        
        self.operation_id = None
        self.async_manager = None
        
    def set_operation(self, operation_id: str, async_manager: AsyncOperationManager):
        """Set the operation to track"""
        self.operation_id = operation_id
        self.async_manager = async_manager
        
        # Start progress monitoring
        GLib.timeout_add(100, self._update_progress)
    
    def _update_progress(self):
        """Update progress bar"""
        if not self.operation_id or not self.async_manager:
            return False
        
        result = self.async_manager.get_operation_status(self.operation_id)
        if not result:
            return False
        
        # Update progress
        self.progress_bar.set_fraction(result.progress / 100.0)
        self.progress_bar.set_text(f"{result.progress}%")
        
        # Update message
        if result.message:
            self.message_label.set_text(result.message)
        
        # Check if operation is done
        if result.status in [OperationStatus.COMPLETED, OperationStatus.FAILED, OperationStatus.CANCELLED]:
            self.response(Gtk.ResponseType.OK)
            return False
        
        return True
    
    def _on_cancel_clicked(self, button):
        """Handle cancel button click"""
        if self.operation_id and self.async_manager:
            self.async_manager.cancel_operation(self.operation_id)
        self.response(Gtk.ResponseType.CANCEL)


class AsyncUIHelper:
    """Helper class for async UI operations"""
    
    @staticmethod
    def show_loading_dialog(parent, title, message, operation_func, *args, **kwargs):
        """Show loading dialog for an async operation"""
        async_manager = AsyncOperationManager()
        
        # Create loading dialog
        dialog = LoadingDialog(parent, title, message)
        
        operation_id = f"ui_operation_{id(operation_func)}"
        
        # Result container
        result_container = {'result': None, 'error': None}
        
        def success_callback(result):
            result_container['result'] = result
            dialog.response(Gtk.ResponseType.OK)
        
        def error_callback(error):
            result_container['error'] = error
            dialog.response(Gtk.ResponseType.OK)
        
        # Start operation
        async_manager.run_async_operation(
            operation_id,
            operation_func,
            success_callback,
            error_callback,
            None,  # progress_callback handled by dialog
            *args,
            **kwargs
        )
        
        dialog.set_operation(operation_id, async_manager)
        dialog.show_all()
        
        response = dialog.run()
        dialog.destroy()
        
        if result_container['error']:
            raise result_container['error']
        
        return result_container['result']
    
    @staticmethod
    def run_with_spinner(widget, operation_func, *args, **kwargs):
        """Run operation with spinner overlay"""
        # Create spinner
        spinner = Gtk.Spinner()
        spinner.set_size_request(32, 32)
        spinner.start()
        
        # Create overlay
        overlay = Gtk.Overlay()
        overlay.add(widget)
        overlay.add_overlay(spinner)
        
        # Replace widget temporarily
        parent = widget.get_parent()
        if parent:
            parent.remove(widget)
            parent.add(overlay)
        
        async_manager = AsyncOperationManager()
        operation_id = f"spinner_operation_{id(operation_func)}"
        
        def success_callback(result):
            spinner.stop()
            if parent:
                parent.remove(overlay)
                parent.add(widget)
        
        def error_callback(error):
            spinner.stop()
            if parent:
                parent.remove(overlay)
                parent.add(widget)
        
        # Start operation
        async_manager.run_async_operation(
            operation_id,
            operation_func,
            success_callback,
            error_callback,
            None,
            *args,
            **kwargs
        )
        
        overlay.show_all()
    
    @staticmethod
    def debounce(func, delay=500):
        """Debounce function calls"""
        def debounced(*args, **kwargs):
            def call_func():
                func(*args, **kwargs)
                return False
            
            if hasattr(debounced, 'timeout_id'):
                GLib.source_remove(debounced.timeout_id)
            
            debounced.timeout_id = GLib.timeout_add(delay, call_func)
        
        return debounced
    
    @staticmethod
    def throttle(func, delay=100):
        """Throttle function calls"""
        def throttled(*args, **kwargs):
            if not hasattr(throttled, 'last_call'):
                throttled.last_call = 0
            
            current_time = GLib.get_monotonic_time() / 1000  # Convert to milliseconds
            
            if current_time - throttled.last_call >= delay:
                throttled.last_call = current_time
                func(*args, **kwargs)
        
        return throttled


# Global async manager instance
async_manager = AsyncOperationManager()
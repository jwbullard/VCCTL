#!/usr/bin/env python3
"""
Comprehensive Error Handling Framework for VCCTL

Provides centralized error handling, logging, and user notification
capabilities across all application components.
"""

import logging
import traceback
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import json

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib


class ErrorSeverity(Enum):
    """Error severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for classification."""
    DATABASE = "database"
    FILE_OPERATION = "file_operation"
    VALIDATION = "validation"
    SERVICE = "service"
    UI = "ui"
    NETWORK = "network"
    PERMISSION = "permission"
    CONFIGURATION = "configuration"
    SIMULATION = "simulation"
    UNKNOWN = "unknown"


@dataclass
class ErrorInfo:
    """Detailed error information."""
    id: str
    timestamp: datetime
    severity: ErrorSeverity
    category: ErrorCategory
    message: str
    details: Optional[str] = None
    traceback: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    user_notified: bool = False
    resolved: bool = False
    resolution_notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'severity': self.severity.value,
            'category': self.category.value,
            'message': self.message,
            'details': self.details,
            'traceback': self.traceback,
            'context': self.context,
            'user_notified': self.user_notified,
            'resolved': self.resolved,
            'resolution_notes': self.resolution_notes
        }


class ErrorHandler:
    """
    Centralized error handling system for VCCTL.
    
    Features:
    - Error classification and severity assessment
    - User-friendly error messages
    - Error logging and persistence
    - Automatic error reporting
    - Recovery suggestions
    """
    
    def __init__(self, main_window=None):
        """Initialize error handler."""
        self.logger = logging.getLogger('VCCTL.ErrorHandler')
        self.main_window = main_window
        
        # Error tracking
        self.errors: Dict[str, ErrorInfo] = {}
        self.error_counter = 0
        self._lock = threading.Lock()
        
        # Error callbacks
        self.error_callbacks: List[Callable[[ErrorInfo], None]] = []
        
        # User message mapping
        self.user_messages = {
            ErrorCategory.DATABASE: {
                ErrorSeverity.ERROR: "Database connection error. Please check your database settings.",
                ErrorSeverity.CRITICAL: "Critical database error. The application may not function properly."
            },
            ErrorCategory.FILE_OPERATION: {
                ErrorSeverity.WARNING: "File operation warning. Some files may not be accessible.",
                ErrorSeverity.ERROR: "File operation failed. Please check file permissions and disk space."
            },
            ErrorCategory.VALIDATION: {
                ErrorSeverity.WARNING: "Validation warning. Please review your input data.",
                ErrorSeverity.ERROR: "Validation failed. Please correct the highlighted issues."
            },
            ErrorCategory.SERVICE: {
                ErrorSeverity.ERROR: "Service error. Some features may be temporarily unavailable.",
                ErrorSeverity.CRITICAL: "Critical service error. Please restart the application."
            },
            ErrorCategory.UI: {
                ErrorSeverity.ERROR: "User interface error. Please try the operation again."
            },
            ErrorCategory.NETWORK: {
                ErrorSeverity.ERROR: "Network error. Please check your internet connection."
            },
            ErrorCategory.PERMISSION: {
                ErrorSeverity.ERROR: "Permission denied. Please check file and directory permissions."
            },
            ErrorCategory.CONFIGURATION: {
                ErrorSeverity.ERROR: "Configuration error. Please check your settings.",
                ErrorSeverity.CRITICAL: "Critical configuration error. Default settings will be used."
            },
            ErrorCategory.SIMULATION: {
                ErrorSeverity.ERROR: "Simulation error. Please check your input parameters.",
                ErrorSeverity.CRITICAL: "Critical simulation error. The operation has been aborted."
            }
        }
        
        # Recovery suggestions
        self.recovery_suggestions = {
            ErrorCategory.DATABASE: [
                "Check database connection settings",
                "Restart the database service",
                "Verify database permissions"
            ],
            ErrorCategory.FILE_OPERATION: [
                "Check file and directory permissions",
                "Verify available disk space",
                "Close other applications using the files"
            ],
            ErrorCategory.VALIDATION: [
                "Review input data for correct format",
                "Check for required fields",
                "Verify data ranges and constraints"
            ],
            ErrorCategory.SERVICE: [
                "Restart the application",
                "Check system resources",
                "Update the application"
            ],
            ErrorCategory.NETWORK: [
                "Check internet connection",
                "Verify firewall settings",
                "Try again in a few minutes"
            ],
            ErrorCategory.CONFIGURATION: [
                "Reset to default settings",
                "Check configuration file syntax",
                "Restore from backup"
            ]
        }
    
    def handle_error(self, 
                    exception: Union[Exception, str],
                    severity: ErrorSeverity = ErrorSeverity.ERROR,
                    category: ErrorCategory = ErrorCategory.UNKNOWN,
                    context: Optional[Dict[str, Any]] = None,
                    user_message: Optional[str] = None,
                    show_dialog: bool = True) -> str:
        """
        Handle an error with comprehensive logging and user notification.
        
        Args:
            exception: Exception instance or error message string
            severity: Error severity level
            category: Error category for classification
            context: Additional context information
            user_message: Custom user-friendly message
            show_dialog: Whether to show error dialog to user
            
        Returns:
            Error ID for tracking
        """
        with self._lock:
            self.error_counter += 1
            error_id = f"err_{self.error_counter:06d}"
        
        # Extract error information
        if isinstance(exception, Exception):
            message = str(exception)
            error_traceback = traceback.format_exc()
        else:
            message = str(exception)
            error_traceback = None
        
        # Create error info
        error_info = ErrorInfo(
            id=error_id,
            timestamp=datetime.now(),
            severity=severity,
            category=category,
            message=message,
            traceback=error_traceback,
            context=context or {}
        )
        
        # Store error
        self.errors[error_id] = error_info
        
        # Log error
        self._log_error(error_info)
        
        # Determine user message
        if not user_message:
            user_message = self._get_user_message(category, severity, message)
        
        error_info.details = user_message
        
        # Notify user if requested
        if show_dialog and self.main_window:
            GLib.idle_add(self._show_error_dialog, error_info)
            error_info.user_notified = True
        
        # Notify callbacks
        for callback in self.error_callbacks:
            try:
                callback(error_info)
            except Exception as e:
                self.logger.warning(f"Error callback failed: {e}")
        
        return error_id
    
    def handle_warning(self,
                      message: str,
                      category: ErrorCategory = ErrorCategory.UNKNOWN,
                      context: Optional[Dict[str, Any]] = None,
                      show_notification: bool = True) -> str:
        """Handle a warning message."""
        return self.handle_error(
            exception=message,
            severity=ErrorSeverity.WARNING,
            category=category,
            context=context,
            show_dialog=show_notification
        )
    
    def handle_info(self,
                   message: str,
                   category: ErrorCategory = ErrorCategory.UNKNOWN,
                   context: Optional[Dict[str, Any]] = None) -> str:
        """Handle an informational message."""
        return self.handle_error(
            exception=message,
            severity=ErrorSeverity.INFO,
            category=category,
            context=context,
            show_dialog=False
        )
    
    def handle_critical_error(self,
                             exception: Union[Exception, str],
                             category: ErrorCategory = ErrorCategory.UNKNOWN,
                             context: Optional[Dict[str, Any]] = None,
                             user_message: Optional[str] = None) -> str:
        """Handle a critical error that may require application shutdown."""
        error_id = self.handle_error(
            exception=exception,
            severity=ErrorSeverity.CRITICAL,
            category=category,
            context=context,
            user_message=user_message,
            show_dialog=True
        )
        
        # For critical errors, also log to console
        print(f"CRITICAL ERROR [{error_id}]: {exception}")
        
        return error_id
    
    def resolve_error(self, error_id: str, resolution_notes: str = "") -> bool:
        """Mark an error as resolved."""
        if error_id in self.errors:
            self.errors[error_id].resolved = True
            self.errors[error_id].resolution_notes = resolution_notes
            self.logger.info(f"Error {error_id} resolved: {resolution_notes}")
            return True
        return False
    
    def get_error(self, error_id: str) -> Optional[ErrorInfo]:
        """Get error information by ID."""
        return self.errors.get(error_id)
    
    def get_errors_by_category(self, category: ErrorCategory) -> List[ErrorInfo]:
        """Get all errors in a specific category."""
        return [error for error in self.errors.values() if error.category == category]
    
    def get_unresolved_errors(self) -> List[ErrorInfo]:
        """Get all unresolved errors."""
        return [error for error in self.errors.values() if not error.resolved]
    
    def clear_resolved_errors(self) -> int:
        """Clear all resolved errors and return count cleared."""
        resolved_ids = [error_id for error_id, error in self.errors.items() if error.resolved]
        for error_id in resolved_ids:
            del self.errors[error_id]
        
        self.logger.info(f"Cleared {len(resolved_ids)} resolved errors")
        return len(resolved_ids)
    
    def add_error_callback(self, callback: Callable[[ErrorInfo], None]) -> None:
        """Add a callback to be notified of new errors."""
        self.error_callbacks.append(callback)
    
    def remove_error_callback(self, callback: Callable[[ErrorInfo], None]) -> None:
        """Remove an error callback."""
        if callback in self.error_callbacks:
            self.error_callbacks.remove(callback)
    
    def export_errors(self, output_file: Path, include_resolved: bool = False) -> None:
        """Export error log to file."""
        try:
            errors_to_export = []
            for error in self.errors.values():
                if include_resolved or not error.resolved:
                    errors_to_export.append(error.to_dict())
            
            export_data = {
                'export_timestamp': datetime.now().isoformat(),
                'total_errors': len(errors_to_export),
                'errors': errors_to_export
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            self.logger.info(f"Exported {len(errors_to_export)} errors to {output_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to export errors: {e}")
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics."""
        stats = {
            'total_errors': len(self.errors),
            'by_severity': {},
            'by_category': {},
            'resolved_count': 0,
            'unresolved_count': 0
        }
        
        for error in self.errors.values():
            # Count by severity
            severity = error.severity.value
            stats['by_severity'][severity] = stats['by_severity'].get(severity, 0) + 1
            
            # Count by category
            category = error.category.value
            stats['by_category'][category] = stats['by_category'].get(category, 0) + 1
            
            # Count resolved/unresolved
            if error.resolved:
                stats['resolved_count'] += 1
            else:
                stats['unresolved_count'] += 1
        
        return stats
    
    def _log_error(self, error_info: ErrorInfo) -> None:
        """Log error to the logging system."""
        log_level = {
            ErrorSeverity.INFO: logging.INFO,
            ErrorSeverity.WARNING: logging.WARNING,
            ErrorSeverity.ERROR: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL
        }.get(error_info.severity, logging.ERROR)
        
        log_message = f"[{error_info.id}] {error_info.category.value.upper()}: {error_info.message}"
        
        if error_info.context:
            log_message += f" | Context: {error_info.context}"
        
        self.logger.log(log_level, log_message)
        
        if error_info.traceback and error_info.severity in [ErrorSeverity.ERROR, ErrorSeverity.CRITICAL]:
            self.logger.debug(f"Traceback for {error_info.id}:\n{error_info.traceback}")
    
    def _get_user_message(self, category: ErrorCategory, severity: ErrorSeverity, technical_message: str) -> str:
        """Generate user-friendly error message."""
        # Try to get predefined message
        if category in self.user_messages and severity in self.user_messages[category]:
            base_message = self.user_messages[category][severity]
        else:
            base_message = "An error occurred. Please try again or contact support."
        
        # Add recovery suggestions if available
        suggestions = self.recovery_suggestions.get(category, [])
        if suggestions:
            suggestion_text = "\n\nSuggested solutions:\n" + "\n".join(f"• {s}" for s in suggestions[:3])
            base_message += suggestion_text
        
        return base_message
    
    def _show_error_dialog(self, error_info: ErrorInfo) -> bool:
        """Show error dialog to user (GTK main thread only)."""
        try:
            if not self.main_window:
                return False
            
            # Determine dialog type based on severity
            message_type = {
                ErrorSeverity.INFO: Gtk.MessageType.INFO,
                ErrorSeverity.WARNING: Gtk.MessageType.WARNING,
                ErrorSeverity.ERROR: Gtk.MessageType.ERROR,
                ErrorSeverity.CRITICAL: Gtk.MessageType.ERROR
            }.get(error_info.severity, Gtk.MessageType.ERROR)
            
            dialog = Gtk.MessageDialog(
                transient_for=self.main_window,
                flags=Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                message_type=message_type,
                buttons=Gtk.ButtonsType.OK,
                text=f"{error_info.category.value.replace('_', ' ').title()} {error_info.severity.value.title()}"
            )
            
            dialog.format_secondary_text(error_info.details or error_info.message)
            
            # Add details button for technical info
            if error_info.traceback or error_info.context:
                dialog.add_button("Details", Gtk.ResponseType.HELP)
            
            response = dialog.run()
            
            # Handle details request
            if response == Gtk.ResponseType.HELP:
                self._show_error_details_dialog(error_info)
            
            dialog.destroy()
            return False  # Don't repeat
            
        except Exception as e:
            # Fallback logging if dialog fails
            self.logger.error(f"Failed to show error dialog: {e}")
            print(f"ERROR: {error_info.message}")
            return False
    
    def _show_error_details_dialog(self, error_info: ErrorInfo) -> None:
        """Show detailed error information dialog."""
        try:
            dialog = Gtk.Dialog(
                title=f"Error Details - {error_info.id}",
                parent=self.main_window,
                flags=Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT
            )
            dialog.add_button("Close", Gtk.ResponseType.CLOSE)
            dialog.set_default_size(600, 400)
            
            content_area = dialog.get_content_area()
            
            # Create notebook for different detail sections
            notebook = Gtk.Notebook()
            
            # General info tab
            info_scroll = Gtk.ScrolledWindow()
            info_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
            
            info_text = f"""Error ID: {error_info.id}
Timestamp: {error_info.timestamp}
Severity: {error_info.severity.value}
Category: {error_info.category.value}
Message: {error_info.message}

Context:
{json.dumps(error_info.context, indent=2) if error_info.context else 'None'}"""
            
            info_label = Gtk.Label(info_text)
            info_label.set_selectable(True)
            info_label.set_halign(Gtk.Align.START)
            info_label.set_valign(Gtk.Align.START)
            info_scroll.add(info_label)
            
            notebook.append_page(info_scroll, Gtk.Label("General"))
            
            # Traceback tab
            if error_info.traceback:
                traceback_scroll = Gtk.ScrolledWindow()
                traceback_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
                
                traceback_label = Gtk.Label(error_info.traceback)
                traceback_label.set_selectable(True)
                traceback_label.set_halign(Gtk.Align.START)
                traceback_label.set_valign(Gtk.Align.START)
                traceback_scroll.add(traceback_label)
                
                notebook.append_page(traceback_scroll, Gtk.Label("Traceback"))
            
            content_area.pack_start(notebook, True, True, 0)
            dialog.show_all()
            dialog.run()
            dialog.destroy()
            
        except Exception as e:
            self.logger.error(f"Failed to show error details dialog: {e}")


# Global error handler instance
_global_error_handler: Optional[ErrorHandler] = None


def get_error_handler(main_window=None) -> ErrorHandler:
    """Get the global error handler instance."""
    global _global_error_handler
    
    if _global_error_handler is None:
        _global_error_handler = ErrorHandler(main_window)
    elif main_window and not _global_error_handler.main_window:
        _global_error_handler.main_window = main_window
    
    return _global_error_handler


def handle_error(exception: Union[Exception, str],
                severity: ErrorSeverity = ErrorSeverity.ERROR,
                category: ErrorCategory = ErrorCategory.UNKNOWN,
                context: Optional[Dict[str, Any]] = None,
                user_message: Optional[str] = None,
                show_dialog: bool = True) -> str:
    """Convenience function for handling errors."""
    return get_error_handler().handle_error(
        exception=exception,
        severity=severity,
        category=category,
        context=context,
        user_message=user_message,
        show_dialog=show_dialog
    )


def handle_warning(message: str,
                  category: ErrorCategory = ErrorCategory.UNKNOWN,
                  context: Optional[Dict[str, Any]] = None,
                  show_notification: bool = True) -> str:
    """Convenience function for handling warnings."""
    return get_error_handler().handle_warning(
        message=message,
        category=category,
        context=context,
        show_notification=show_notification
    )


def handle_critical_error(exception: Union[Exception, str],
                         category: ErrorCategory = ErrorCategory.UNKNOWN,
                         context: Optional[Dict[str, Any]] = None,
                         user_message: Optional[str] = None) -> str:
    """Convenience function for handling critical errors."""
    return get_error_handler().handle_critical_error(
        exception=exception,
        category=category,
        context=context,
        user_message=user_message
    )


# Decorator for automatic error handling
def error_handler(category: ErrorCategory = ErrorCategory.UNKNOWN,
                 severity: ErrorSeverity = ErrorSeverity.ERROR,
                 show_dialog: bool = True,
                 return_on_error: Any = None):
    """
    Decorator for automatic error handling in functions.
    
    Args:
        category: Error category
        severity: Error severity
        show_dialog: Whether to show error dialog
        return_on_error: Value to return if error occurs
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                handle_error(
                    exception=e,
                    severity=severity,
                    category=category,
                    context={'function': func.__name__, 'args': str(args), 'kwargs': str(kwargs)},
                    show_dialog=show_dialog
                )
                return return_on_error
        return wrapper
    return decorator
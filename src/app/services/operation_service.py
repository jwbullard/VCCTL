#!/usr/bin/env python3
"""
Operation Service for VCCTL

Manages simulation operations, their lifecycle, and execution tracking.
"""

import asyncio
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Callable, Set
from concurrent.futures import ThreadPoolExecutor, Future
from dataclasses import dataclass, field
from queue import Queue, PriorityQueue
import uuid

from .base_service import BaseService, ServiceError, NotFoundError, AlreadyExistsError
from ..models.operation import Operation, OperationCreate, OperationUpdate, OperationStatus, OperationType
from ..database.service import DatabaseService


@dataclass
class OperationProgress:
    """Progress information for an operation."""
    operation_name: str
    progress: float  # 0.0 to 1.0
    message: str = ""
    current_step: str = ""
    total_steps: int = 0
    current_step_number: int = 0
    estimated_time_remaining: Optional[float] = None  # seconds
    
    @property
    def percentage(self) -> int:
        """Get progress as percentage (0-100)."""
        return int(self.progress * 100)


@dataclass
class ResourceLimits:
    """Resource limits for operation execution."""
    max_concurrent_operations: int = 4
    max_memory_mb: int = 2048
    max_cpu_percent: int = 80
    max_disk_io_mb_per_sec: int = 100


@dataclass 
class OperationQueueItem:
    """Item in the operation execution queue."""
    priority: int
    operation_name: str
    queued_time: datetime = field(default_factory=datetime.utcnow)
    
    def __lt__(self, other):
        """Support priority queue ordering."""
        if self.priority != other.priority:
            return self.priority < other.priority
        return self.queued_time < other.queued_time


class OperationExecutor:
    """Executes operations with progress tracking and resource management."""
    
    def __init__(self, resource_limits: ResourceLimits):
        """Initialize operation executor."""
        self.resource_limits = resource_limits
        self.logger = logging.getLogger('VCCTL.Services.OperationExecutor')
        self._running_operations: Dict[str, Future] = {}
        self._operation_progress: Dict[str, OperationProgress] = {}
        self._executor = ThreadPoolExecutor(max_workers=resource_limits.max_concurrent_operations)
        self._shutdown = threading.Event()
    
    def can_start_operation(self) -> bool:
        """Check if we can start a new operation given resource constraints."""
        current_operations = len(self._running_operations)
        return current_operations < self.resource_limits.max_concurrent_operations
    
    def start_operation(self, operation: Operation, operation_func: Callable, 
                       progress_callback: Optional[Callable[[OperationProgress], None]] = None) -> Future:
        """
        Start executing an operation.
        
        Args:
            operation: Operation to execute
            operation_func: Function to execute the operation
            progress_callback: Optional callback for progress updates
            
        Returns:
            Future representing the operation execution
        """
        if operation.name in self._running_operations:
            raise ServiceError(f"Operation {operation.name} is already running")
        
        if not self.can_start_operation():
            raise ServiceError("Cannot start operation: resource limits exceeded")
        
        # Initialize progress tracking
        progress = OperationProgress(
            operation_name=operation.name,
            progress=0.0,
            message="Starting operation..."
        )
        self._operation_progress[operation.name] = progress
        
        # Submit operation for execution
        future = self._executor.submit(
            self._execute_operation_with_tracking,
            operation, operation_func, progress_callback
        )
        
        self._running_operations[operation.name] = future
        
        # Set up completion callback
        future.add_done_callback(lambda f: self._on_operation_complete(operation.name, f))
        
        self.logger.info(f"Started operation: {operation.name}")
        return future
    
    def cancel_operation(self, operation_name: str) -> bool:
        """
        Cancel a running operation.
        
        Args:
            operation_name: Name of operation to cancel
            
        Returns:
            True if operation was cancelled, False if not found or already finished
        """
        if operation_name not in self._running_operations:
            return False
        
        future = self._running_operations[operation_name]
        cancelled = future.cancel()
        
        if cancelled:
            self.logger.info(f"Cancelled operation: {operation_name}")
            # Update progress to indicate cancellation
            if operation_name in self._operation_progress:
                progress = self._operation_progress[operation_name]
                progress.message = "Operation cancelled"
        
        return cancelled
    
    def get_operation_progress(self, operation_name: str) -> Optional[OperationProgress]:
        """Get current progress for an operation."""
        return self._operation_progress.get(operation_name)
    
    def get_running_operations(self) -> List[str]:
        """Get list of currently running operation names."""
        return list(self._running_operations.keys())
    
    def shutdown(self, wait: bool = True):
        """Shutdown the executor."""
        self._shutdown.set()
        self._executor.shutdown(wait=wait)
        self.logger.info("Operation executor shutdown")
    
    def _execute_operation_with_tracking(self, operation: Operation, operation_func: Callable,
                                       progress_callback: Optional[Callable[[OperationProgress], None]]):
        """Execute operation with progress tracking."""
        operation_name = operation.name
        
        try:
            # Create progress update function
            def update_progress(progress: float, message: str = "", **kwargs):
                if operation_name in self._operation_progress:
                    op_progress = self._operation_progress[operation_name]
                    op_progress.progress = progress
                    op_progress.message = message
                    
                    # Update additional fields if provided
                    for key, value in kwargs.items():
                        if hasattr(op_progress, key):
                            setattr(op_progress, key, value)
                    
                    if progress_callback:
                        progress_callback(op_progress)
            
            # Execute the operation
            result = operation_func(operation, update_progress)
            
            # Mark as completed
            update_progress(1.0, "Operation completed successfully")
            return result
            
        except Exception as e:
            # Mark as failed
            if operation_name in self._operation_progress:
                progress = self._operation_progress[operation_name]
                progress.message = f"Operation failed: {str(e)}"
            raise
    
    def _on_operation_complete(self, operation_name: str, future: Future):
        """Handle operation completion."""
        # Remove from running operations
        if operation_name in self._running_operations:
            del self._running_operations[operation_name]
        
        # Keep progress for a while for status queries
        # In production, this might be moved to persistent storage
        if future.cancelled():
            self.logger.info(f"Operation cancelled: {operation_name}")
        elif future.exception():
            self.logger.error(f"Operation failed: {operation_name} - {future.exception()}")
        else:
            self.logger.info(f"Operation completed: {operation_name}")


class OperationService(BaseService[Operation, OperationCreate, OperationUpdate]):
    """Service for managing simulation operations and their execution."""
    
    def __init__(self, db_service: DatabaseService, resource_limits: Optional[ResourceLimits] = None):
        """Initialize operation service."""
        super().__init__(Operation, db_service)
        self.resource_limits = resource_limits or ResourceLimits()
        self.executor = OperationExecutor(self.resource_limits)
        self.operation_queue = PriorityQueue()
        self._progress_callbacks: Dict[str, List[Callable]] = {}
        self._operation_registry: Dict[str, Callable] = {}
        self._queue_processor_running = False
        self._queue_thread: Optional[threading.Thread] = None
        
        # Start queue processor
        self._start_queue_processor()
        
        self.logger.info("Operation service initialized")
    
    def register_operation_handler(self, operation_type: str, handler: Callable):
        """
        Register a handler function for a specific operation type.
        
        Args:
            operation_type: Type of operation (e.g., 'HYDRATION', 'MICROSTRUCTURE')
            handler: Function to execute operations of this type
        """
        self._operation_registry[operation_type] = handler
        self.logger.debug(f"Registered handler for operation type: {operation_type}")
    
    def create_operation(self, create_data: OperationCreate) -> Operation:
        """Create a new operation."""
        try:
            # Check if operation already exists
            existing = self.get_by_name(create_data.name)
            if existing:
                raise AlreadyExistsError(f"Operation '{create_data.name}' already exists")
        except NotFoundError:
            pass  # This is expected
        
        # Create operation
        operation = Operation(
            name=create_data.name,
            type=create_data.type,
            depends_on_operation_name=create_data.depends_on_operation_name,
            notes=create_data.notes
        )
        
        # Set state data if provided
        if create_data.state_data:
            operation.state_data = create_data.state_data
        
        # Mark as queued
        operation.mark_queued()
        
        # Save to database
        created_operation = self.create(operation)
        
        self.logger.info(f"Created operation: {created_operation.name}")
        return created_operation
    
    def queue_operation(self, operation_name: str, priority: int = 5) -> bool:
        """
        Queue an operation for execution.
        
        Args:
            operation_name: Name of operation to queue
            priority: Priority (lower number = higher priority)
            
        Returns:
            True if operation was queued
        """
        try:
            operation = self.get_by_name(operation_name)
            if not operation:
                raise NotFoundError(f"Operation '{operation_name}' not found")
            
            if operation.is_running:
                raise ServiceError(f"Operation '{operation_name}' is already running")
            
            # Add to queue
            queue_item = OperationQueueItem(
                priority=priority,
                operation_name=operation_name
            )
            self.operation_queue.put(queue_item)
            
            # Update operation status
            operation.mark_queued()
            self.update(operation_name, operation)
            
            self.logger.info(f"Queued operation: {operation_name} (priority: {priority})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to queue operation {operation_name}: {e}")
            raise ServiceError(f"Failed to queue operation: {e}")
    
    def start_operation(self, operation_name: str) -> bool:
        """
        Start executing an operation immediately (bypass queue).
        
        Args:
            operation_name: Name of operation to start
            
        Returns:
            True if operation was started
        """
        try:
            operation = self.get_by_name(operation_name)
            if not operation:
                raise NotFoundError(f"Operation '{operation_name}' not found")
            
            if operation.is_running:
                raise ServiceError(f"Operation '{operation_name}' is already running")
            
            # Check if we have a handler for this operation type
            handler = self._operation_registry.get(operation.type)
            if not handler:
                raise ServiceError(f"No handler registered for operation type: {operation.type}")
            
            # Check dependencies
            if operation.has_dependency:
                dependency = self.get_by_name(operation.depends_on_operation_name)
                if dependency and not dependency.is_finished:
                    raise ServiceError(f"Dependency operation '{dependency.name}' has not finished")
            
            # Update status and start
            operation.mark_started()
            self.update(operation_name, operation)
            
            # Start execution
            progress_callback = self._get_progress_callback(operation_name)
            future = self.executor.start_operation(operation, handler, progress_callback)
            
            # Set up completion handling
            future.add_done_callback(lambda f: self._handle_operation_completion(operation_name, f))
            
            self.logger.info(f"Started operation: {operation_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start operation {operation_name}: {e}")
            # Mark operation as error if it was marked as started
            try:
                operation = self.get_by_name(operation_name)
                if operation and operation.is_running:
                    operation.mark_error(str(e))
                    self.update(operation_name, operation)
            except:
                pass
            raise ServiceError(f"Failed to start operation: {e}")
    
    def cancel_operation(self, operation_name: str) -> bool:
        """
        Cancel a running or queued operation.
        
        Args:
            operation_name: Name of operation to cancel
            
        Returns:
            True if operation was cancelled
        """
        try:
            operation = self.get_by_name(operation_name)
            if not operation:
                raise NotFoundError(f"Operation '{operation_name}' not found")
            
            if operation.is_finished:
                self.logger.warning(f"Cannot cancel finished operation: {operation_name}")
                return False
            
            # Try to cancel if running
            cancelled = False
            if operation.is_running:
                cancelled = self.executor.cancel_operation(operation_name)
            
            # Remove from queue if queued
            if operation.is_queued:
                cancelled = True  # We'll mark it as cancelled in the database
            
            if cancelled:
                operation.mark_cancelled()
                self.update(operation_name, operation)
                self.logger.info(f"Cancelled operation: {operation_name}")
            
            return cancelled
            
        except Exception as e:
            self.logger.error(f"Failed to cancel operation {operation_name}: {e}")
            raise ServiceError(f"Failed to cancel operation: {e}")
    
    def get_operation_progress(self, operation_name: str) -> Optional[OperationProgress]:
        """Get current progress for an operation."""
        # Try to get from executor first (for running operations)
        progress = self.executor.get_operation_progress(operation_name)
        if progress:
            return progress
        
        # For non-running operations, create progress from database state
        try:
            operation = self.get_by_name(operation_name)
            if operation:
                if operation.is_finished:
                    progress_value = 1.0
                    message = "Completed" if operation.status == OperationStatus.FINISHED.value else "Failed"
                elif operation.is_queued:
                    progress_value = 0.0
                    message = "Queued"
                else:
                    progress_value = operation.calculate_progress_estimate() or 0.0
                    message = f"Status: {operation.status}"
                
                return OperationProgress(
                    operation_name=operation_name,
                    progress=progress_value,
                    message=message
                )
        except:
            pass
        
        return None
    
    def get_running_operations(self) -> List[Operation]:
        """Get all currently running operations."""
        try:
            return self.get_by_status(OperationStatus.RUNNING.value)
        except Exception as e:
            self.logger.error(f"Failed to get running operations: {e}")
            return []
    
    def get_queued_operations(self) -> List[Operation]:
        """Get all queued operations."""
        try:
            return self.get_by_status(OperationStatus.QUEUED.value)
        except Exception as e:
            self.logger.error(f"Failed to get queued operations: {e}")
            return []
    
    def get_by_status(self, status: str) -> List[Operation]:
        """Get operations by status."""
        try:
            with self.db_service.get_session() as session:
                operations = session.query(Operation).filter_by(status=status).all()
                return operations
        except Exception as e:
            self.logger.error(f"Failed to get operations by status {status}: {e}")
            raise ServiceError(f"Failed to get operations by status: {e}")
    
    def get_operation_statistics(self) -> Dict[str, Any]:
        """Get operation statistics."""
        try:
            with self.db_service.get_session() as session:
                total_operations = session.query(Operation).count()
                
                # Count by status
                status_counts = {}
                for status in OperationStatus:
                    count = session.query(Operation).filter_by(status=status.value).count()
                    status_counts[status.value.lower()] = count
                
                # Count by type
                type_counts = {}
                for op_type in OperationType:
                    count = session.query(Operation).filter_by(type=op_type.value).count()
                    type_counts[op_type.value.lower()] = count
                
                # Calculate average duration for completed operations
                completed_ops = session.query(Operation).filter_by(status=OperationStatus.FINISHED.value).all()
                avg_duration = 0.0
                if completed_ops:
                    durations = [op.duration for op in completed_ops if op.duration]
                    if durations:
                        avg_duration = sum(durations) / len(durations)
                
                return {
                    'total_operations': total_operations,
                    'status_counts': status_counts,
                    'type_counts': type_counts,
                    'average_duration_seconds': avg_duration,
                    'currently_running': len(self.executor.get_running_operations()),
                    'queue_size': self.operation_queue.qsize()
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get operation statistics: {e}")
            raise ServiceError(f"Failed to get operation statistics: {e}")
    
    def cleanup_old_operations(self, days_old: int = 30) -> int:
        """
        Clean up old completed operations.
        
        Args:
            days_old: Remove operations older than this many days
            
        Returns:
            Number of operations removed
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            with self.db_service.get_session() as session:
                old_operations = session.query(Operation).filter(
                    Operation.finish < cutoff_date,
                    Operation.status.in_([OperationStatus.FINISHED.value, OperationStatus.ERROR.value])
                ).all()
                
                count = len(old_operations)
                for operation in old_operations:
                    session.delete(operation)
                
                self.logger.info(f"Cleaned up {count} old operations")
                return count
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup old operations: {e}")
            raise ServiceError(f"Failed to cleanup old operations: {e}")
    
    def add_progress_callback(self, operation_name: str, callback: Callable[[OperationProgress], None]):
        """Add a progress callback for an operation."""
        if operation_name not in self._progress_callbacks:
            self._progress_callbacks[operation_name] = []
        self._progress_callbacks[operation_name].append(callback)
    
    def remove_progress_callback(self, operation_name: str, callback: Callable[[OperationProgress], None]):
        """Remove a progress callback for an operation."""
        if operation_name in self._progress_callbacks:
            try:
                self._progress_callbacks[operation_name].remove(callback)
                if not self._progress_callbacks[operation_name]:
                    del self._progress_callbacks[operation_name]
            except ValueError:
                pass
    
    def shutdown(self):
        """Shutdown the operation service."""
        self._queue_processor_running = False
        if self._queue_thread:
            self._queue_thread.join(timeout=5.0)
        self.executor.shutdown(wait=True)
        self.logger.info("Operation service shutdown")
    
    def _start_queue_processor(self):
        """Start the queue processor thread."""
        self._queue_processor_running = True
        self._queue_thread = threading.Thread(target=self._process_queue, daemon=True)
        self._queue_thread.start()
        self.logger.debug("Queue processor started")
    
    def _process_queue(self):
        """Process the operation queue."""
        while self._queue_processor_running:
            try:
                # Check if we can start new operations
                if not self.executor.can_start_operation():
                    time.sleep(1)
                    continue
                
                # Get next operation from queue (with timeout)
                try:
                    queue_item = self.operation_queue.get(timeout=1)
                except:
                    continue  # Timeout, check shutdown flag
                
                # Try to start the operation
                try:
                    self.start_operation(queue_item.operation_name)
                except Exception as e:
                    self.logger.error(f"Failed to start queued operation {queue_item.operation_name}: {e}")
                    # Mark operation as error
                    try:
                        operation = self.get_by_name(queue_item.operation_name)
                        if operation:
                            operation.mark_error(str(e))
                            self.update(queue_item.operation_name, operation)
                    except:
                        pass
                
                self.operation_queue.task_done()
                
            except Exception as e:
                self.logger.error(f"Error in queue processor: {e}")
                time.sleep(1)
        
        self.logger.debug("Queue processor stopped")
    
    def _get_progress_callback(self, operation_name: str) -> Optional[Callable]:
        """Get combined progress callback for an operation."""
        callbacks = self._progress_callbacks.get(operation_name, [])
        if not callbacks:
            return None
        
        def combined_callback(progress: OperationProgress):
            for callback in callbacks:
                try:
                    callback(progress)
                except Exception as e:
                    self.logger.error(f"Progress callback failed for {operation_name}: {e}")
        
        return combined_callback
    
    def _handle_operation_completion(self, operation_name: str, future: Future):
        """Handle operation completion."""
        try:
            operation = self.get_by_name(operation_name)
            if not operation:
                return
            
            if future.cancelled():
                operation.mark_cancelled()
            elif future.exception():
                operation.mark_error(str(future.exception()))
            else:
                operation.mark_finished()
            
            self.update(operation_name, operation)
            
        except Exception as e:
            self.logger.error(f"Failed to handle completion for operation {operation_name}: {e}")
    
    def get_by_name(self, name: str) -> Optional[Operation]:
        """Get operation by name."""
        try:
            with self.db_service.get_session() as session:
                return session.query(Operation).filter_by(name=name).first()
        except Exception as e:
            self.logger.error(f"Failed to get operation by name {name}: {e}")
            return None
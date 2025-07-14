#!/usr/bin/env python3
"""
Batch File Operations for VCCTL

Provides utilities for performing batch file operations with progress tracking,
error handling, and rollback capabilities.
"""

import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import shutil
import json


class BatchOperationType(Enum):
    """Types of batch operations."""
    COPY = "copy"
    MOVE = "move"
    DELETE = "delete"
    RENAME = "rename"
    CONVERT = "convert"
    VALIDATE = "validate"


class OperationStatus(Enum):
    """Status of individual operations."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class BatchOperation:
    """Represents a single operation in a batch."""
    operation_type: BatchOperationType
    source_path: Path
    target_path: Optional[Path] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    status: OperationStatus = OperationStatus.PENDING
    error_message: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    
    @property
    def duration(self) -> Optional[float]:
        """Get operation duration in seconds."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None
    
    @property
    def is_completed(self) -> bool:
        """Check if operation is completed successfully."""
        return self.status == OperationStatus.COMPLETED
    
    @property
    def is_failed(self) -> bool:
        """Check if operation failed."""
        return self.status == OperationStatus.FAILED


@dataclass
class BatchProgress:
    """Progress information for batch operations."""
    total_operations: int
    completed_operations: int
    failed_operations: int
    skipped_operations: int
    current_operation: Optional[BatchOperation] = None
    start_time: Optional[float] = None
    estimated_completion_time: Optional[float] = None
    
    @property
    def progress_fraction(self) -> float:
        """Get progress as fraction between 0 and 1."""
        if self.total_operations == 0:
            return 0.0
        processed = self.completed_operations + self.failed_operations + self.skipped_operations
        return min(1.0, processed / self.total_operations)
    
    @property
    def progress_percentage(self) -> float:
        """Get progress as percentage."""
        return self.progress_fraction * 100.0
    
    @property
    def success_rate(self) -> float:
        """Get success rate as percentage."""
        processed = self.completed_operations + self.failed_operations + self.skipped_operations
        if processed == 0:
            return 0.0
        return (self.completed_operations / processed) * 100.0


class BatchFileOperationManager:
    """
    Manager for batch file operations with progress tracking and rollback.
    
    Features:
    - Parallel execution with configurable thread pool
    - Progress callbacks and cancellation
    - Rollback capability for failed operations
    - Detailed logging and error reporting
    - Resume functionality for interrupted operations
    """
    
    def __init__(self, max_workers: Optional[int] = None):
        """Initialize the batch operation manager."""
        self.max_workers = max_workers or min(32, 4 + 4)
        self.logger = logging.getLogger('VCCTL.BatchFileOperations')
        
        # Operation state
        self.operations: List[BatchOperation] = []
        self.progress = BatchProgress(0, 0, 0, 0)
        self.is_running = False
        self.is_cancelled = False
        
        # Callbacks
        self.progress_callbacks: List[Callable[[BatchProgress], None]] = []
        self.operation_callbacks: List[Callable[[BatchOperation], None]] = []
        
        # Rollback tracking
        self.rollback_info: List[Dict[str, Any]] = []
        
        # Thread management
        self.executor: Optional[ThreadPoolExecutor] = None
        self.cancel_event = threading.Event()
    
    def add_copy_operations(self, source_target_pairs: List[Tuple[Path, Path]],
                          overwrite: bool = False) -> None:
        """Add copy operations to the batch."""
        for source, target in source_target_pairs:
            operation = BatchOperation(
                operation_type=BatchOperationType.COPY,
                source_path=source,
                target_path=target,
                parameters={'overwrite': overwrite}
            )
            self.operations.append(operation)
    
    def add_move_operations(self, source_target_pairs: List[Tuple[Path, Path]],
                          overwrite: bool = False) -> None:
        """Add move operations to the batch."""
        for source, target in source_target_pairs:
            operation = BatchOperation(
                operation_type=BatchOperationType.MOVE,
                source_path=source,
                target_path=target,
                parameters={'overwrite': overwrite}
            )
            self.operations.append(operation)
    
    def add_delete_operations(self, file_paths: List[Path],
                            move_to_trash: bool = True) -> None:
        """Add delete operations to the batch."""
        for file_path in file_paths:
            operation = BatchOperation(
                operation_type=BatchOperationType.DELETE,
                source_path=file_path,
                parameters={'move_to_trash': move_to_trash}
            )
            self.operations.append(operation)
    
    def add_rename_operations(self, rename_pairs: List[Tuple[Path, str]]) -> None:
        """Add rename operations to the batch."""
        for source, new_name in rename_pairs:
            target = source.parent / new_name
            operation = BatchOperation(
                operation_type=BatchOperationType.RENAME,
                source_path=source,
                target_path=target
            )
            self.operations.append(operation)
    
    def add_validation_operations(self, file_paths: List[Path],
                                validation_params: Dict[str, Any] = None) -> None:
        """Add validation operations to the batch."""
        params = validation_params or {}
        for file_path in file_paths:
            operation = BatchOperation(
                operation_type=BatchOperationType.VALIDATE,
                source_path=file_path,
                parameters=params
            )
            self.operations.append(operation)
    
    def add_conversion_operations(self, conversions: List[Tuple[Path, Path, str]]) -> None:
        """Add format conversion operations to the batch."""
        for source, target, target_format in conversions:
            operation = BatchOperation(
                operation_type=BatchOperationType.CONVERT,
                source_path=source,
                target_path=target,
                parameters={'target_format': target_format}
            )
            self.operations.append(operation)
    
    def add_progress_callback(self, callback: Callable[[BatchProgress], None]) -> None:
        """Add a progress update callback."""
        self.progress_callbacks.append(callback)
    
    def add_operation_callback(self, callback: Callable[[BatchOperation], None]) -> None:
        """Add an operation completion callback."""
        self.operation_callbacks.append(callback)
    
    def execute_batch(self, parallel: bool = True, 
                     continue_on_error: bool = True) -> BatchProgress:
        """
        Execute all operations in the batch.
        
        Args:
            parallel: Whether to execute operations in parallel
            continue_on_error: Whether to continue after individual failures
            
        Returns:
            Final BatchProgress with results
        """
        if self.is_running:
            raise RuntimeError("Batch operation already running")
        
        if not self.operations:
            self.logger.warning("No operations to execute")
            return self.progress
        
        self.is_running = True
        self.is_cancelled = False
        self.cancel_event.clear()
        
        # Initialize progress
        self.progress = BatchProgress(
            total_operations=len(self.operations),
            completed_operations=0,
            failed_operations=0,
            skipped_operations=0,
            start_time=time.time()
        )
        
        self.logger.info(f"Starting batch execution of {len(self.operations)} operations")
        
        try:
            if parallel:
                self._execute_parallel(continue_on_error)
            else:
                self._execute_sequential(continue_on_error)
        finally:
            self.is_running = False
            
            # Final progress update
            self._update_progress()
            
            # Log summary
            self.logger.info(
                f"Batch execution completed: {self.progress.completed_operations} successful, "
                f"{self.progress.failed_operations} failed, {self.progress.skipped_operations} skipped"
            )
        
        return self.progress
    
    def _execute_parallel(self, continue_on_error: bool) -> None:
        """Execute operations in parallel."""
        with ThreadPoolExecutor(max_workers=self.max_workers) as self.executor:
            # Submit all operations
            future_to_operation = {
                self.executor.submit(self._execute_operation, op): op
                for op in self.operations
            }
            
            # Process completed operations
            for future in as_completed(future_to_operation):
                if self.cancel_event.is_set():
                    break
                
                operation = future_to_operation[future]
                
                try:
                    future.result()  # This will raise any exception from the operation
                except Exception as e:
                    self.logger.error(f"Operation failed: {e}")
                    if not continue_on_error:
                        self.cancel_event.set()
                        break
                
                self._update_progress()
    
    def _execute_sequential(self, continue_on_error: bool) -> None:
        """Execute operations sequentially."""
        for operation in self.operations:
            if self.cancel_event.is_set():
                operation.status = OperationStatus.SKIPPED
                self.progress.skipped_operations += 1
                continue
            
            try:
                self._execute_operation(operation)
            except Exception as e:
                self.logger.error(f"Operation failed: {e}")
                if not continue_on_error:
                    # Mark remaining operations as skipped
                    for remaining_op in self.operations[self.operations.index(operation) + 1:]:
                        remaining_op.status = OperationStatus.SKIPPED
                        self.progress.skipped_operations += 1
                    break
            
            self._update_progress()
    
    def _execute_operation(self, operation: BatchOperation) -> None:
        """Execute a single operation."""
        if self.cancel_event.is_set():
            operation.status = OperationStatus.SKIPPED
            return
        
        operation.status = OperationStatus.RUNNING
        operation.start_time = time.time()
        self.progress.current_operation = operation
        
        try:
            if operation.operation_type == BatchOperationType.COPY:
                self._execute_copy(operation)
            elif operation.operation_type == BatchOperationType.MOVE:
                self._execute_move(operation)
            elif operation.operation_type == BatchOperationType.DELETE:
                self._execute_delete(operation)
            elif operation.operation_type == BatchOperationType.RENAME:
                self._execute_rename(operation)
            elif operation.operation_type == BatchOperationType.VALIDATE:
                self._execute_validate(operation)
            elif operation.operation_type == BatchOperationType.CONVERT:
                self._execute_convert(operation)
            else:
                raise ValueError(f"Unknown operation type: {operation.operation_type}")
            
            operation.status = OperationStatus.COMPLETED
            self.progress.completed_operations += 1
            
        except Exception as e:
            operation.status = OperationStatus.FAILED
            operation.error_message = str(e)
            self.progress.failed_operations += 1
            raise
        
        finally:
            operation.end_time = time.time()
            
            # Notify operation callbacks
            for callback in self.operation_callbacks:
                try:
                    callback(operation)
                except Exception as e:
                    self.logger.warning(f"Operation callback failed: {e}")
    
    def _execute_copy(self, operation: BatchOperation) -> None:
        """Execute a copy operation."""
        source = operation.source_path
        target = operation.target_path
        overwrite = operation.parameters.get('overwrite', False)
        
        if not source.exists():
            raise FileNotFoundError(f"Source file not found: {source}")
        
        if target.exists() and not overwrite:
            raise FileExistsError(f"Target file exists: {target}")
        
        # Create target directory if needed
        target.parent.mkdir(parents=True, exist_ok=True)
        
        if source.is_dir():
            if target.exists() and overwrite:
                shutil.rmtree(target)
            shutil.copytree(source, target)
        else:
            shutil.copy2(source, target)
        
        # Store rollback info
        self.rollback_info.append({
            'operation': 'copy',
            'target': target,
            'action': 'delete'
        })
    
    def _execute_move(self, operation: BatchOperation) -> None:
        """Execute a move operation."""
        source = operation.source_path
        target = operation.target_path
        overwrite = operation.parameters.get('overwrite', False)
        
        if not source.exists():
            raise FileNotFoundError(f"Source file not found: {source}")
        
        if target.exists() and not overwrite:
            raise FileExistsError(f"Target file exists: {target}")
        
        # Create target directory if needed
        target.parent.mkdir(parents=True, exist_ok=True)
        
        # Store rollback info before moving
        self.rollback_info.append({
            'operation': 'move',
            'source': source,
            'target': target,
            'action': 'restore'
        })
        
        if target.exists() and overwrite:
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()
        
        shutil.move(str(source), str(target))
    
    def _execute_delete(self, operation: BatchOperation) -> None:
        """Execute a delete operation."""
        source = operation.source_path
        move_to_trash = operation.parameters.get('move_to_trash', True)
        
        if not source.exists():
            raise FileNotFoundError(f"Source file not found: {source}")
        
        if move_to_trash:
            # Try to move to system trash (simplified implementation)
            trash_dir = Path.home() / ".local/share/Trash/files"
            if not trash_dir.exists():
                trash_dir.mkdir(parents=True, exist_ok=True)
            
            trash_target = trash_dir / source.name
            counter = 1
            while trash_target.exists():
                stem = source.stem
                suffix = source.suffix
                trash_target = trash_dir / f"{stem}_{counter}{suffix}"
                counter += 1
            
            shutil.move(str(source), str(trash_target))
            
            # Store rollback info
            self.rollback_info.append({
                'operation': 'delete',
                'source': source,
                'trash_location': trash_target,
                'action': 'restore_from_trash'
            })
        else:
            # Backup before permanent deletion
            backup_data = None
            if source.is_file() and source.stat().st_size < 1024 * 1024:  # Backup small files
                try:
                    backup_data = source.read_bytes()
                except:
                    pass
            
            if source.is_dir():
                shutil.rmtree(source)
            else:
                source.unlink()
            
            # Store rollback info
            self.rollback_info.append({
                'operation': 'delete',
                'source': source,
                'backup_data': backup_data,
                'action': 'restore_from_backup'
            })
    
    def _execute_rename(self, operation: BatchOperation) -> None:
        """Execute a rename operation."""
        source = operation.source_path
        target = operation.target_path
        
        if not source.exists():
            raise FileNotFoundError(f"Source file not found: {source}")
        
        if target.exists():
            raise FileExistsError(f"Target file exists: {target}")
        
        # Store rollback info
        self.rollback_info.append({
            'operation': 'rename',
            'source': source,
            'target': target,
            'action': 'rename_back'
        })
        
        source.rename(target)
    
    def _execute_validate(self, operation: BatchOperation) -> None:
        """Execute a validation operation."""
        source = operation.source_path
        
        if not source.exists():
            raise FileNotFoundError(f"Source file not found: {source}")
        
        # Use the enhanced file format validator
        from .file_format_validator import EnhancedFileFormatValidator
        
        validator = EnhancedFileFormatValidator()
        file_result, schema_result = validator.validate_material_file(source)
        
        # Store validation results in operation parameters
        operation.parameters['file_validation'] = file_result
        operation.parameters['schema_validation'] = schema_result
        operation.parameters['is_valid'] = file_result.is_valid and schema_result.is_valid
        
        if not operation.parameters['is_valid']:
            errors = []
            if file_result.errors:
                errors.extend(file_result.errors)
            if schema_result.errors:
                errors.extend([issue.message for issue in schema_result.errors])
            
            if errors:
                raise ValueError(f"Validation failed: {'; '.join(errors[:3])}")
    
    def _execute_convert(self, operation: BatchOperation) -> None:
        """Execute a format conversion operation."""
        source = operation.source_path
        target = operation.target_path
        target_format = operation.parameters.get('target_format', 'json')
        
        if not source.exists():
            raise FileNotFoundError(f"Source file not found: {source}")
        
        # Parse source file
        from .file_format_validator import EnhancedFileFormatValidator
        
        validator = EnhancedFileFormatValidator()
        
        # Detect source format
        source_type = None
        if source.suffix.lower() == '.json':
            source_type = 'application/json'
        elif source.suffix.lower() == '.csv':
            source_type = 'text/csv'
        elif source.suffix.lower() == '.xml':
            source_type = 'application/xml'
        
        if not source_type:
            raise ValueError(f"Unsupported source format: {source.suffix}")
        
        # Parse source data
        data = validator._parse_file_content(source, source_type)
        
        # Create target directory if needed
        target.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to target format
        if target_format.lower() == 'json':
            with open(target, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        elif target_format.lower() == 'csv':
            import csv
            with open(target, 'w', newline='', encoding='utf-8') as f:
                if data:
                    writer = csv.DictWriter(f, fieldnames=data.keys())
                    writer.writeheader()
                    writer.writerow(data)
        elif target_format.lower() == 'xml':
            import xml.etree.ElementTree as ET
            root = ET.Element('material')
            for key, value in data.items():
                element = ET.SubElement(root, key)
                element.text = str(value)
            
            tree = ET.ElementTree(root)
            tree.write(target, encoding='utf-8', xml_declaration=True)
        else:
            raise ValueError(f"Unsupported target format: {target_format}")
        
        # Store rollback info
        self.rollback_info.append({
            'operation': 'convert',
            'target': target,
            'action': 'delete'
        })
    
    def _update_progress(self) -> None:
        """Update progress and notify callbacks."""
        # Estimate completion time
        if self.progress.start_time:
            elapsed = time.time() - self.progress.start_time
            if self.progress.progress_fraction > 0:
                estimated_total = elapsed / self.progress.progress_fraction
                self.progress.estimated_completion_time = self.progress.start_time + estimated_total
        
        # Notify progress callbacks
        for callback in self.progress_callbacks:
            try:
                callback(self.progress)
            except Exception as e:
                self.logger.warning(f"Progress callback failed: {e}")
    
    def cancel_batch(self) -> None:
        """Cancel the running batch operation."""
        if self.is_running:
            self.is_cancelled = True
            self.cancel_event.set()
            
            if self.executor:
                self.executor.shutdown(wait=False)
            
            self.logger.info("Batch operation cancelled")
    
    def rollback_operations(self) -> int:
        """
        Rollback completed operations.
        
        Returns:
            Number of operations successfully rolled back
        """
        if self.is_running:
            raise RuntimeError("Cannot rollback while batch is running")
        
        rollback_count = 0
        
        # Process rollback info in reverse order
        for rollback_info in reversed(self.rollback_info):
            try:
                action = rollback_info['action']
                
                if action == 'delete':
                    # Remove created file/directory
                    target = rollback_info['target']
                    if target.exists():
                        if target.is_dir():
                            shutil.rmtree(target)
                        else:
                            target.unlink()
                
                elif action == 'restore':
                    # Move file back to original location
                    source = rollback_info['source']
                    target = rollback_info['target']
                    if target.exists():
                        shutil.move(str(target), str(source))
                
                elif action == 'restore_from_trash':
                    # Restore from trash
                    source = rollback_info['source']
                    trash_location = rollback_info['trash_location']
                    if trash_location.exists():
                        shutil.move(str(trash_location), str(source))
                
                elif action == 'restore_from_backup':
                    # Restore from backup data
                    source = rollback_info['source']
                    backup_data = rollback_info.get('backup_data')
                    if backup_data:
                        source.write_bytes(backup_data)
                
                elif action == 'rename_back':
                    # Rename back to original
                    source = rollback_info['source']
                    target = rollback_info['target']
                    if target.exists():
                        target.rename(source)
                
                rollback_count += 1
                
            except Exception as e:
                self.logger.error(f"Rollback failed for {rollback_info}: {e}")
        
        self.logger.info(f"Rolled back {rollback_count} operations")
        return rollback_count
    
    def clear_operations(self) -> None:
        """Clear all operations and reset state."""
        if self.is_running:
            raise RuntimeError("Cannot clear operations while batch is running")
        
        self.operations.clear()
        self.rollback_info.clear()
        self.progress = BatchProgress(0, 0, 0, 0)
    
    def get_operation_summary(self) -> Dict[str, Any]:
        """Get a summary of all operations and their status."""
        summary = {
            'total_operations': len(self.operations),
            'by_type': {},
            'by_status': {},
            'total_duration': 0.0,
            'failed_operations': []
        }
        
        for operation in self.operations:
            # Count by type
            op_type = operation.operation_type.value
            summary['by_type'][op_type] = summary['by_type'].get(op_type, 0) + 1
            
            # Count by status
            status = operation.status.value
            summary['by_status'][status] = summary['by_status'].get(status, 0) + 1
            
            # Add duration
            if operation.duration:
                summary['total_duration'] += operation.duration
            
            # Collect failed operations
            if operation.status == OperationStatus.FAILED:
                summary['failed_operations'].append({
                    'type': op_type,
                    'source': str(operation.source_path),
                    'target': str(operation.target_path) if operation.target_path else None,
                    'error': operation.error_message
                })
        
        return summary
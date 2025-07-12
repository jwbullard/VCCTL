#!/usr/bin/env python3
"""
File Operations Utilities for VCCTL

Provides optimized file I/O operations and utilities.
"""

import asyncio
import logging
import mimetypes
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Any, Callable, Union, BinaryIO
import hashlib
import json


@dataclass
class FileWriteTask:
    """Represents a file write task for parallel execution."""
    path: Path
    data_supplier: Callable[[], bytes]
    
    def __post_init__(self):
        """Validate the task after initialization."""
        if self.path is None:
            raise ValueError("Path cannot be None")
        if self.data_supplier is None:
            raise ValueError("Data supplier cannot be None")


@dataclass
class FileValidationResult:
    """Result of file validation."""
    is_valid: bool
    file_type: Optional[str] = None
    size_bytes: int = 0
    errors: List[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        """Initialize empty lists if None."""
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


class OptimizedFileWriter:
    """Optimized file writer for high-performance I/O operations."""
    
    # Buffer size optimized for modern SSDs
    OPTIMAL_BUFFER_SIZE = 32768  # 32KB
    SIMPLE_WRITE_THRESHOLD = 8192  # 8KB
    
    @staticmethod
    def write_file(path: Path, data: bytes, create_parents: bool = True) -> None:
        """
        Write data to a file with optimized performance.
        
        Args:
            path: Target file path
            data: Data to write
            create_parents: Whether to create parent directories
            
        Raises:
            IOError: If write operation fails
        """
        if create_parents:
            path.parent.mkdir(parents=True, exist_ok=True)
        
        # Use simple write for small files
        if len(data) < OptimizedFileWriter.SIMPLE_WRITE_THRESHOLD:
            path.write_bytes(data)
            return
        
        # Use optimized write for larger files
        OptimizedFileWriter._write_with_buffer(path, data)
    
    @staticmethod
    def _write_with_buffer(path: Path, data: bytes) -> None:
        """Write large files using buffered I/O."""
        with open(path, 'wb', buffering=OptimizedFileWriter.OPTIMAL_BUFFER_SIZE) as file:
            bytes_written = 0
            data_length = len(data)
            
            while bytes_written < data_length:
                chunk_size = min(
                    OptimizedFileWriter.OPTIMAL_BUFFER_SIZE,
                    data_length - bytes_written
                )
                
                chunk = data[bytes_written:bytes_written + chunk_size]
                file.write(chunk)
                bytes_written += chunk_size


class ParallelFileWriter:
    """Handles parallel file write operations for improved performance."""
    
    def __init__(self, max_workers: Optional[int] = None):
        """
        Initialize parallel file writer.
        
        Args:
            max_workers: Maximum number of worker threads
        """
        self.max_workers = max_workers or min(32, (4) + 4)
        self.logger = logging.getLogger('VCCTL.Utils.FileOperations')
    
    def write_files(self, tasks: List[FileWriteTask]) -> None:
        """
        Write multiple files in parallel.
        
        Args:
            tasks: List of file write tasks
            
        Raises:
            IOError: If any write operation fails
        """
        if not tasks:
            return
        
        self.logger.debug(f"Starting parallel write of {len(tasks)} files")
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_task = {
                executor.submit(self._execute_task, task): task
                for task in tasks
            }
            
            # Wait for completion and handle errors
            errors = []
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    future.result()
                    self.logger.debug(f"Successfully wrote file: {task.path}")
                except Exception as e:
                    error_msg = f"Failed to write file {task.path}: {e}"
                    self.logger.error(error_msg)
                    errors.append(error_msg)
            
            if errors:
                raise IOError(f"Failed to write {len(errors)} files: {'; '.join(errors)}")
        
        self.logger.info(f"Successfully wrote {len(tasks)} files in parallel")
    
    def _execute_task(self, task: FileWriteTask) -> None:
        """Execute a single file write task."""
        try:
            data = task.data_supplier()
            if data is not None:
                OptimizedFileWriter.write_file(task.path, data)
        except Exception as e:
            raise IOError(f"Task execution failed for {task.path}: {e}")


class FileValidator:
    """Validates files and their content."""
    
    # Common file type mappings
    SUPPORTED_FORMATS = {
        '.csv': 'text/csv',
        '.json': 'application/json',
        '.xml': 'application/xml',
        '.txt': 'text/plain',
        '.dat': 'application/octet-stream',
        '.bin': 'application/octet-stream',
        '.img': 'application/octet-stream'
    }
    
    def __init__(self):
        """Initialize file validator."""
        self.logger = logging.getLogger('VCCTL.Utils.FileValidator')
    
    def validate_file(self, file_path: Path, expected_format: Optional[str] = None,
                     max_size_mb: Optional[float] = None) -> FileValidationResult:
        """
        Validate a file's existence, format, and size.
        
        Args:
            file_path: Path to the file to validate
            expected_format: Expected file format (MIME type or extension)
            max_size_mb: Maximum allowed file size in MB
            
        Returns:
            FileValidationResult with validation details
        """
        result = FileValidationResult(is_valid=True)
        
        # Check if file exists
        if not file_path.exists():
            result.is_valid = False
            result.errors.append(f"File does not exist: {file_path}")
            return result
        
        # Check if it's actually a file
        if not file_path.is_file():
            result.is_valid = False
            result.errors.append(f"Path is not a file: {file_path}")
            return result
        
        try:
            # Get file size
            result.size_bytes = file_path.stat().st_size
            size_mb = result.size_bytes / (1024 * 1024)
            
            # Check file size
            if max_size_mb and size_mb > max_size_mb:
                result.is_valid = False
                result.errors.append(f"File too large: {size_mb:.1f}MB > {max_size_mb}MB")
            
            # Detect file type
            result.file_type = self._detect_file_type(file_path)
            
            # Validate format if specified
            if expected_format:
                if not self._is_format_match(result.file_type, expected_format):
                    result.warnings.append(
                        f"File type mismatch: detected {result.file_type}, expected {expected_format}"
                    )
            
            # Additional content validation
            self._validate_content(file_path, result)
            
        except Exception as e:
            result.is_valid = False
            result.errors.append(f"Validation error: {e}")
            self.logger.error(f"File validation failed for {file_path}: {e}")
        
        return result
    
    def _detect_file_type(self, file_path: Path) -> str:
        """Detect file type using extension and content."""
        # First try by extension
        extension = file_path.suffix.lower()
        if extension in self.SUPPORTED_FORMATS:
            return self.SUPPORTED_FORMATS[extension]
        
        # Fallback to mimetypes module
        mime_type, _ = mimetypes.guess_type(str(file_path))
        return mime_type or 'application/octet-stream'
    
    def _is_format_match(self, detected_type: str, expected_format: str) -> bool:
        """Check if detected type matches expected format."""
        if detected_type == expected_format:
            return True
        
        # Handle extension format (e.g., '.csv' vs 'text/csv')
        if expected_format.startswith('.'):
            return detected_type == self.SUPPORTED_FORMATS.get(expected_format)
        
        return False
    
    def _validate_content(self, file_path: Path, result: FileValidationResult) -> None:
        """Perform content-specific validation."""
        try:
            # For JSON files, try to parse
            if result.file_type == 'application/json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    json.load(f)
            
            # For text files, check encoding
            elif result.file_type and result.file_type.startswith('text/'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    f.read(1024)  # Read first 1KB to check encoding
            
        except UnicodeDecodeError:
            result.warnings.append("File may not be UTF-8 encoded")
        except json.JSONDecodeError:
            result.warnings.append("Invalid JSON format")
        except Exception:
            # Don't fail validation for content issues
            pass


class FileImportExport:
    """Handles file import/export operations for materials and data."""
    
    def __init__(self, directories_service):
        """
        Initialize file import/export handler.
        
        Args:
            directories_service: Service for directory management
        """
        self.directories_service = directories_service
        self.validator = FileValidator()
        self.logger = logging.getLogger('VCCTL.Utils.FileImportExport')
    
    def import_material_file(self, source_path: Path, material_name: str,
                           material_type: str) -> Path:
        """
        Import a material file to the materials directory.
        
        Args:
            source_path: Source file path
            material_name: Name of the material
            material_type: Type of material (cement, flyash, slag, etc.)
            
        Returns:
            Path to the imported file
            
        Raises:
            ValueError: If validation fails
            IOError: If import fails
        """
        # Validate source file
        validation_result = self.validator.validate_file(source_path, max_size_mb=100)
        if not validation_result.is_valid:
            raise ValueError(f"File validation failed: {'; '.join(validation_result.errors)}")
        
        # Determine target path
        materials_dir = self.directories_service.get_materials_dir()
        type_dir = materials_dir / material_type
        type_dir.mkdir(parents=True, exist_ok=True)
        
        # Create safe filename
        safe_name = self.directories_service._sanitize_filename(material_name)
        target_path = type_dir / f"{safe_name}{source_path.suffix}"
        
        # Handle filename conflicts
        counter = 1
        original_target = target_path
        while target_path.exists():
            stem = original_target.stem
            suffix = original_target.suffix
            target_path = original_target.parent / f"{stem}_{counter}{suffix}"
            counter += 1
        
        try:
            # Copy file
            shutil.copy2(source_path, target_path)
            self.logger.info(f"Imported material file: {source_path} -> {target_path}")
            return target_path
        except Exception as e:
            self.logger.error(f"Failed to import material file: {e}")
            raise IOError(f"Import failed: {e}")
    
    def export_material_file(self, material_data: bytes, material_name: str,
                           export_path: Path, file_format: str = 'json') -> None:
        """
        Export material data to a file.
        
        Args:
            material_data: Material data to export
            material_name: Name of the material
            export_path: Target export path
            file_format: Export format ('json', 'csv', 'xml')
            
        Raises:
            IOError: If export fails
        """
        try:
            # Ensure export directory exists
            export_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write data
            OptimizedFileWriter.write_file(export_path, material_data)
            
            self.logger.info(f"Exported material '{material_name}' to {export_path}")
        except Exception as e:
            self.logger.error(f"Failed to export material '{material_name}': {e}")
            raise IOError(f"Export failed: {e}")
    
    def batch_import_materials(self, source_dir: Path, material_type: str,
                              progress_callback: Optional[Callable[[int, int], None]] = None) -> List[Path]:
        """
        Import multiple material files from a directory.
        
        Args:
            source_dir: Source directory containing material files
            material_type: Type of materials to import
            progress_callback: Optional callback for progress updates (current, total)
            
        Returns:
            List of imported file paths
            
        Raises:
            ValueError: If source directory doesn't exist
        """
        if not source_dir.exists() or not source_dir.is_dir():
            raise ValueError(f"Source directory does not exist: {source_dir}")
        
        # Find all importable files
        supported_extensions = {'.json', '.csv', '.txt', '.dat', '.xml'}
        source_files = [
            f for f in source_dir.rglob('*')
            if f.is_file() and f.suffix.lower() in supported_extensions
        ]
        
        imported_files = []
        total_files = len(source_files)
        
        for i, source_file in enumerate(source_files):
            try:
                material_name = source_file.stem
                imported_path = self.import_material_file(source_file, material_name, material_type)
                imported_files.append(imported_path)
                
                if progress_callback:
                    progress_callback(i + 1, total_files)
                    
            except Exception as e:
                self.logger.warning(f"Failed to import {source_file}: {e}")
        
        self.logger.info(f"Batch import completed: {len(imported_files)}/{total_files} files imported")
        return imported_files
    
    def calculate_file_hash(self, file_path: Path, algorithm: str = 'sha256') -> str:
        """
        Calculate hash of a file for integrity checking.
        
        Args:
            file_path: Path to the file
            algorithm: Hash algorithm ('md5', 'sha256', 'sha512')
            
        Returns:
            Hexadecimal hash string
        """
        hash_obj = hashlib.new(algorithm)
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hash_obj.update(chunk)
        
        return hash_obj.hexdigest()
    
    def verify_file_integrity(self, file_path: Path, expected_hash: str,
                             algorithm: str = 'sha256') -> bool:
        """
        Verify file integrity using hash comparison.
        
        Args:
            file_path: Path to the file to verify
            expected_hash: Expected hash value
            algorithm: Hash algorithm used
            
        Returns:
            True if file integrity is verified
        """
        try:
            actual_hash = self.calculate_file_hash(file_path, algorithm)
            return actual_hash.lower() == expected_hash.lower()
        except Exception as e:
            self.logger.error(f"Failed to verify file integrity for {file_path}: {e}")
            return False


class ProgressTracker:
    """Tracks progress for long-running file operations."""
    
    def __init__(self, total_items: int, callback: Optional[Callable[[int, int, str], None]] = None):
        """
        Initialize progress tracker.
        
        Args:
            total_items: Total number of items to process
            callback: Optional callback function (current, total, status)
        """
        self.total_items = total_items
        self.current_item = 0
        self.callback = callback
        self.start_time = None
        self.status = "Starting..."
    
    def start(self) -> None:
        """Start progress tracking."""
        import time
        self.start_time = time.time()
        self.update_status("Starting...")
    
    def update(self, increment: int = 1, status: str = "") -> None:
        """
        Update progress.
        
        Args:
            increment: Number of items completed
            status: Status message
        """
        self.current_item += increment
        if status:
            self.status = status
        
        if self.callback:
            self.callback(self.current_item, self.total_items, self.status)
    
    def finish(self, status: str = "Completed") -> None:
        """Mark progress as finished."""
        self.current_item = self.total_items
        self.status = status
        
        if self.callback:
            self.callback(self.current_item, self.total_items, self.status)
    
    def get_elapsed_time(self) -> float:
        """Get elapsed time in seconds."""
        if self.start_time is None:
            return 0
        
        import time
        return time.time() - self.start_time
    
    def get_eta(self) -> float:
        """Get estimated time to completion in seconds."""
        if self.current_item == 0 or self.start_time is None:
            return 0
        
        elapsed = self.get_elapsed_time()
        items_per_second = self.current_item / elapsed
        remaining_items = self.total_items - self.current_item
        
        return remaining_items / items_per_second if items_per_second > 0 else 0
    
    def update_status(self, status: str) -> None:
        """Update just the status message."""
        self.status = status
        if self.callback:
            self.callback(self.current_item, self.total_items, self.status)
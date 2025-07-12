#!/usr/bin/env python3
"""
Directories Service for VCCTL

Manages directory operations and path handling for simulations and operations.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any
from ..config.config_manager import ConfigManager


class DirectoriesService:
    """Service for managing application directories and operation paths."""
    
    def __init__(self, config_manager: ConfigManager):
        """Initialize directories service with configuration manager."""
        self.config_manager = config_manager
        self.logger = logging.getLogger('VCCTL.Services.Directories')
        self._ensure_base_directories()
    
    def _ensure_base_directories(self) -> None:
        """Ensure all base directories exist."""
        try:
            directories_config = self.config_manager.get_directories_config()
            directories_config.create_directories()
            self.logger.info("Base directories ensured")
        except Exception as e:
            self.logger.error(f"Failed to create base directories: {e}")
            raise
    
    def get_operation_dir(self, operation_name: str) -> Path:
        """
        Get the directory path for a specific operation, creating it if necessary.
        
        Args:
            operation_name: Name of the operation
            
        Returns:
            Path to the operation directory
            
        Raises:
            RuntimeError: If directory cannot be created
        """
        if not operation_name or not operation_name.strip():
            raise ValueError("Operation name cannot be empty")
        
        # Sanitize operation name for filesystem
        safe_name = self._sanitize_filename(operation_name)
        
        directories_config = self.config_manager.get_directories_config()
        operation_path = directories_config.operations_path / safe_name
        
        try:
            operation_path.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"Operation directory ensured: {operation_path}")
            return operation_path
        except Exception as e:
            self.logger.error(f"Failed to create operation directory {operation_path}: {e}")
            raise RuntimeError(f"Failed to create operation directory: {e}")
    
    def get_operation_file_path(self, operation_name: str, filename: str) -> Path:
        """
        Get the full path for a file within an operation directory.
        
        Args:
            operation_name: Name of the operation
            filename: Name of the file
            
        Returns:
            Full path to the file
        """
        if not filename or not filename.strip():
            raise ValueError("Filename cannot be empty")
        
        operation_dir = self.get_operation_dir(operation_name)
        safe_filename = self._sanitize_filename(filename)
        return operation_dir / safe_filename
    
    def get_materials_dir(self) -> Path:
        """Get the materials directory path."""
        directories_config = self.config_manager.get_directories_config()
        return directories_config.materials_path
    
    def get_temp_dir(self) -> Path:
        """Get the temporary directory path."""
        directories_config = self.config_manager.get_directories_config()
        return directories_config.temp_path
    
    def get_database_dir(self) -> Path:
        """Get the database directory path."""
        directories_config = self.config_manager.get_directories_config()
        return directories_config.database_path
    
    def get_logs_dir(self) -> Path:
        """Get the logs directory path."""
        directories_config = self.config_manager.get_directories_config()
        return directories_config.logs_path
    
    def get_bin_dir(self) -> Path:
        """Get the bin directory path."""
        directories_config = self.config_manager.get_directories_config()
        return directories_config.bin_path
    
    def get_data_dir(self) -> Path:
        """Get the data directory path."""
        directories_config = self.config_manager.get_directories_config()
        return directories_config.data_path
    
    def get_aggregate_dir(self) -> Path:
        """Get the aggregate directory path."""
        directories_config = self.config_manager.get_directories_config()
        return directories_config.aggregate_path
    
    def get_particle_shape_set_dir(self) -> Path:
        """Get the particle shape set directory path."""
        directories_config = self.config_manager.get_directories_config()
        return directories_config.particle_shape_set_path
    
    def create_temp_file(self, prefix: str = "vcctl_", suffix: str = ".tmp") -> Path:
        """
        Create a temporary file and return its path.
        
        Args:
            prefix: Prefix for the temporary file name
            suffix: Suffix for the temporary file name
            
        Returns:
            Path to the created temporary file
        """
        import tempfile
        temp_dir = self.get_temp_dir()
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Create temporary file in our temp directory
        with tempfile.NamedTemporaryFile(
            prefix=prefix,
            suffix=suffix,
            dir=temp_dir,
            delete=False
        ) as tmp_file:
            temp_path = Path(tmp_file.name)
        
        self.logger.debug(f"Created temporary file: {temp_path}")
        return temp_path
    
    def cleanup_temp_files(self, max_age_hours: int = 24) -> int:
        """
        Clean up old temporary files.
        
        Args:
            max_age_hours: Maximum age of files to keep in hours
            
        Returns:
            Number of files removed
        """
        import time
        
        temp_dir = self.get_temp_dir()
        if not temp_dir.exists():
            return 0
        
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        files_removed = 0
        
        try:
            for temp_file in temp_dir.rglob("*"):
                if temp_file.is_file():
                    try:
                        file_age = current_time - temp_file.stat().st_mtime
                        if file_age > max_age_seconds:
                            temp_file.unlink()
                            files_removed += 1
                            self.logger.debug(f"Removed old temp file: {temp_file}")
                    except Exception as e:
                        self.logger.warning(f"Failed to remove temp file {temp_file}: {e}")
        except Exception as e:
            self.logger.error(f"Error during temp file cleanup: {e}")
        
        if files_removed > 0:
            self.logger.info(f"Cleaned up {files_removed} temporary files")
        
        return files_removed
    
    def get_directory_info(self) -> Dict[str, Any]:
        """Get information about all application directories."""
        directories_config = self.config_manager.get_directories_config()
        return directories_config.get_directory_info()
    
    def validate_directory_structure(self) -> Dict[str, Any]:
        """Validate the directory structure and permissions."""
        directories_config = self.config_manager.get_directories_config()
        return directories_config.validate()
    
    def get_relative_path(self, absolute_path: Path) -> Path:
        """Get a path relative to the application directory."""
        directories_config = self.config_manager.get_directories_config()
        return directories_config.get_relative_path(absolute_path)
    
    def resolve_path(self, path_str: str) -> Path:
        """Resolve a path string relative to the application directory."""
        directories_config = self.config_manager.get_directories_config()
        return directories_config.resolve_path(path_str)
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize a filename by removing/replacing invalid characters.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename safe for filesystem use
        """
        import re
        
        # Remove or replace invalid characters
        # Windows invalid characters: < > : " | ? * and ASCII 0-31
        invalid_chars = r'[<>:"|?*\x00-\x1f]'
        sanitized = re.sub(invalid_chars, '_', filename)
        
        # Remove leading/trailing dots and spaces
        sanitized = sanitized.strip('. ')
        
        # Ensure filename is not empty after sanitization
        if not sanitized:
            sanitized = "unnamed"
        
        # Limit length to reasonable filesystem limits
        if len(sanitized) > 200:
            name_part = sanitized[:190]
            extension_part = sanitized[-10:] if '.' in sanitized[-10:] else ""
            sanitized = name_part + extension_part
        
        return sanitized
    
    def ensure_directory(self, directory_path: Path) -> None:
        """
        Ensure a directory exists, creating it if necessary.
        
        Args:
            directory_path: Path to the directory to ensure
            
        Raises:
            RuntimeError: If directory cannot be created
        """
        try:
            directory_path.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"Directory ensured: {directory_path}")
        except Exception as e:
            self.logger.error(f"Failed to create directory {directory_path}: {e}")
            raise RuntimeError(f"Failed to create directory: {e}")
    
    def is_safe_path(self, path: Path, base_path: Optional[Path] = None) -> bool:
        """
        Check if a path is safe (within allowed directories).
        
        Args:
            path: Path to check
            base_path: Base path to restrict to (defaults to app directory)
            
        Returns:
            True if path is safe, False otherwise
        """
        if base_path is None:
            directories_config = self.config_manager.get_directories_config()
            base_path = directories_config.app_directory
        
        try:
            # Resolve both paths to handle symlinks and relative components
            resolved_path = path.resolve()
            resolved_base = base_path.resolve()
            
            # Check if path is within base path
            resolved_path.relative_to(resolved_base)
            return True
        except (ValueError, OSError):
            return False
    
    def get_disk_usage(self, path: Optional[Path] = None) -> Dict[str, float]:
        """
        Get disk usage information for a path.
        
        Args:
            path: Path to check (defaults to app directory)
            
        Returns:
            Dictionary with total, used, and free space in GB
        """
        if path is None:
            directories_config = self.config_manager.get_directories_config()
            path = directories_config.app_directory
        
        try:
            import shutil
            total, used, free = shutil.disk_usage(path)
            
            # Convert to GB
            return {
                'total_gb': total / (1024**3),
                'used_gb': used / (1024**3),
                'free_gb': free / (1024**3),
                'usage_percent': (used / total) * 100 if total > 0 else 0
            }
        except Exception as e:
            self.logger.error(f"Failed to get disk usage for {path}: {e}")
            return {'total_gb': 0, 'used_gb': 0, 'free_gb': 0, 'usage_percent': 0}
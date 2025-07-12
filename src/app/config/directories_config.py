#!/usr/bin/env python3
"""
Directories Configuration for VCCTL

Manages directory structure and paths for the application.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any


@dataclass
class DirectoriesConfig:
    """Configuration for application directory structure."""
    
    # Base application directory
    app_directory: Path
    
    # Subdirectories (relative to app_directory)
    bin_directory: str = "bin"
    data_directory: str = "data"
    usr_directory: str = "usr"
    operations_directory: str = "operations"
    database_directory: str = "database"
    particle_shape_set_directory: str = "particle_shape_set"
    aggregate_directory: str = "aggregate"
    materials_directory: str = "materials"
    temp_directory: str = "temp"
    logs_directory: str = "logs"
    
    @classmethod
    def create_default(cls, app_directory: Path) -> 'DirectoriesConfig':
        """Create default directories configuration."""
        return cls(
            app_directory=app_directory,
            bin_directory="bin",
            data_directory="data",
            usr_directory="usr",
            operations_directory="operations",
            database_directory="database",
            particle_shape_set_directory="particle_shape_set",
            aggregate_directory="aggregate",
            materials_directory="materials",
            temp_directory="temp",
            logs_directory="logs"
        )
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], app_directory: Path) -> 'DirectoriesConfig':
        """Create directories configuration from dictionary."""
        return cls(
            app_directory=app_directory,
            bin_directory=data.get('bin_directory', 'bin'),
            data_directory=data.get('data_directory', 'data'),
            usr_directory=data.get('usr_directory', 'usr'),
            operations_directory=data.get('operations_directory', 'operations'),
            database_directory=data.get('database_directory', 'database'),
            particle_shape_set_directory=data.get('particle_shape_set_directory', 'particle_shape_set'),
            aggregate_directory=data.get('aggregate_directory', 'aggregate'),
            materials_directory=data.get('materials_directory', 'materials'),
            temp_directory=data.get('temp_directory', 'temp'),
            logs_directory=data.get('logs_directory', 'logs')
        )
    
    # Property methods to get full paths
    @property
    def bin_path(self) -> Path:
        """Get full path to bin directory."""
        return self.app_directory / self.bin_directory
    
    @property
    def data_path(self) -> Path:
        """Get full path to data directory."""
        return self.app_directory / self.data_directory
    
    @property
    def usr_path(self) -> Path:
        """Get full path to usr directory."""
        return self.app_directory / self.usr_directory
    
    @property
    def operations_path(self) -> Path:
        """Get full path to operations directory."""
        return self.app_directory / self.operations_directory
    
    @property
    def database_path(self) -> Path:
        """Get full path to database directory."""
        return self.app_directory / self.database_directory
    
    @property
    def particle_shape_set_path(self) -> Path:
        """Get full path to particle shape set directory."""
        return self.app_directory / self.particle_shape_set_directory
    
    @property
    def aggregate_path(self) -> Path:
        """Get full path to aggregate directory."""
        return self.app_directory / self.aggregate_directory
    
    @property
    def materials_path(self) -> Path:
        """Get full path to materials directory."""
        return self.app_directory / self.materials_directory
    
    @property
    def temp_path(self) -> Path:
        """Get full path to temp directory."""
        return self.app_directory / self.temp_directory
    
    @property
    def logs_path(self) -> Path:
        """Get full path to logs directory."""
        return self.app_directory / self.logs_directory
    
    def get_all_directories(self) -> Dict[str, Path]:
        """Get all directory paths as a dictionary."""
        return {
            'app': self.app_directory,
            'bin': self.bin_path,
            'data': self.data_path,
            'usr': self.usr_path,
            'operations': self.operations_path,
            'database': self.database_path,
            'particle_shape_set': self.particle_shape_set_path,
            'aggregate': self.aggregate_path,
            'materials': self.materials_path,
            'temp': self.temp_path,
            'logs': self.logs_path
        }
    
    def create_directories(self) -> None:
        """Create all configured directories."""
        directories = self.get_all_directories()
        
        for name, path in directories.items():
            try:
                path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                raise RuntimeError(f"Failed to create {name} directory {path}: {e}")
    
    def validate(self) -> Dict[str, Any]:
        """Validate directories configuration."""
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Check if app directory exists or can be created
        try:
            if not self.app_directory.exists():
                # Try to create it
                self.app_directory.mkdir(parents=True, exist_ok=True)
                validation_result['warnings'].append(f"Created app directory: {self.app_directory}")
        except Exception as e:
            validation_result['errors'].append(f"Cannot create app directory {self.app_directory}: {e}")
            validation_result['is_valid'] = False
            return validation_result
        
        # Check if app directory is writable
        import os
        if not os.access(self.app_directory, os.W_OK):
            validation_result['errors'].append(f"App directory is not writable: {self.app_directory}")
            validation_result['is_valid'] = False
        
        # Validate directory names (no invalid characters)
        invalid_chars = '<>:"|?*'
        directory_names = [
            self.bin_directory, self.data_directory, self.usr_directory,
            self.operations_directory, self.database_directory,
            self.particle_shape_set_directory, self.aggregate_directory,
            self.materials_directory, self.temp_directory, self.logs_directory
        ]
        
        for dir_name in directory_names:
            if any(char in dir_name for char in invalid_chars):
                validation_result['errors'].append(f"Directory name contains invalid characters: {dir_name}")
                validation_result['is_valid'] = False
        
        # Check for directory name conflicts (no duplicate names)
        if len(set(directory_names)) != len(directory_names):
            validation_result['errors'].append("Duplicate directory names found")
            validation_result['is_valid'] = False
        
        # Check available disk space
        try:
            import shutil
            total, used, free = shutil.disk_usage(self.app_directory)
            free_gb = free / (1024**3)
            
            if free_gb < 1.0:
                validation_result['warnings'].append(f"Low disk space: {free_gb:.1f} GB available")
            elif free_gb < 0.1:
                validation_result['errors'].append(f"Insufficient disk space: {free_gb:.1f} GB available")
                validation_result['is_valid'] = False
        except Exception:
            validation_result['warnings'].append("Could not check available disk space")
        
        return validation_result
    
    def get_directory_info(self) -> Dict[str, Any]:
        """Get information about all directories."""
        directories = self.get_all_directories()
        info = {}
        
        for name, path in directories.items():
            try:
                exists = path.exists()
                is_dir = path.is_dir() if exists else False
                is_writable = False
                size_mb = 0
                file_count = 0
                
                if exists and is_dir:
                    import os
                    is_writable = os.access(path, os.W_OK)
                    
                    # Calculate directory size and file count
                    try:
                        total_size = 0
                        total_files = 0
                        for dirpath, dirnames, filenames in os.walk(path):
                            total_files += len(filenames)
                            for filename in filenames:
                                filepath = os.path.join(dirpath, filename)
                                try:
                                    total_size += os.path.getsize(filepath)
                                except (OSError, FileNotFoundError):
                                    pass
                        
                        size_mb = total_size / (1024 * 1024)
                        file_count = total_files
                    except Exception:
                        pass
                
                info[name] = {
                    'path': str(path),
                    'exists': exists,
                    'is_directory': is_dir,
                    'is_writable': is_writable,
                    'size_mb': round(size_mb, 2),
                    'file_count': file_count
                }
            except Exception as e:
                info[name] = {
                    'path': str(path),
                    'error': str(e)
                }
        
        return info
    
    def cleanup_temp_directory(self) -> int:
        """Clean up temporary directory and return number of files removed."""
        if not self.temp_path.exists():
            return 0
        
        files_removed = 0
        try:
            import shutil
            for item in self.temp_path.iterdir():
                try:
                    if item.is_file():
                        item.unlink()
                        files_removed += 1
                    elif item.is_dir():
                        shutil.rmtree(item)
                        files_removed += 1
                except Exception:
                    pass  # Continue with other files
        except Exception:
            pass
        
        return files_removed
    
    def get_relative_path(self, absolute_path: Path) -> Path:
        """Get path relative to app directory if possible."""
        try:
            return absolute_path.relative_to(self.app_directory)
        except ValueError:
            # Path is not under app directory
            return absolute_path
    
    def resolve_path(self, path_str: str) -> Path:
        """Resolve a path string, treating relative paths as relative to app directory."""
        path = Path(path_str)
        if path.is_absolute():
            return path
        else:
            return self.app_directory / path
#!/usr/bin/env python3
"""
User Configuration for VCCTL

Manages user-specific settings and preferences.
"""

import platform
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List


@dataclass
class UserConfig:
    """User-specific configuration settings."""
    
    # Core directories
    app_directory: Path = field(default_factory=Path)
    
    # User preferences
    particle_shape_sets: List[str] = field(default_factory=list)
    recent_projects: List[str] = field(default_factory=list)
    max_recent_projects: int = 10
    
    # User interface preferences
    auto_save_enabled: bool = True
    auto_save_interval: int = 300  # seconds
    confirm_destructive_actions: bool = True
    show_welcome_dialog: bool = True
    
    # Performance preferences
    max_worker_threads: int = 4
    memory_limit_mb: int = 4096
    cache_enabled: bool = True
    
    @classmethod
    def create_default(cls, config_dir: Path) -> 'UserConfig':
        """Create default user configuration."""
        # Determine default app directory based on platform
        app_dir = cls._get_default_app_directory()
        
        return cls(
            app_directory=app_dir,
            particle_shape_sets=["sphere", "ellipsoid"],
            recent_projects=[],
            max_recent_projects=10,
            auto_save_enabled=True,
            auto_save_interval=300,
            confirm_destructive_actions=True,
            show_welcome_dialog=True,
            max_worker_threads=cls._get_default_thread_count(),
            memory_limit_mb=4096,
            cache_enabled=True
        )
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], config_dir: Path) -> 'UserConfig':
        """Create user configuration from dictionary."""
        # Convert app_directory string to Path if needed
        app_dir = data.get('app_directory')
        if app_dir:
            app_dir = Path(app_dir).expanduser()
        else:
            app_dir = cls._get_default_app_directory()
        
        # Convert recent_projects strings to list
        recent_projects = data.get('recent_projects', [])
        if isinstance(recent_projects, str):
            recent_projects = [recent_projects]
        
        return cls(
            app_directory=app_dir,
            particle_shape_sets=data.get('particle_shape_sets', ["sphere", "ellipsoid"]),
            recent_projects=recent_projects,
            max_recent_projects=data.get('max_recent_projects', 10),
            auto_save_enabled=data.get('auto_save_enabled', True),
            auto_save_interval=data.get('auto_save_interval', 300),
            confirm_destructive_actions=data.get('confirm_destructive_actions', True),
            show_welcome_dialog=data.get('show_welcome_dialog', True),
            max_worker_threads=data.get('max_worker_threads', cls._get_default_thread_count()),
            memory_limit_mb=data.get('memory_limit_mb', 4096),
            cache_enabled=data.get('cache_enabled', True)
        )
    
    @staticmethod
    def _get_default_app_directory() -> Path:
        """Get default application directory as current working directory."""
        # Use current working directory as the default app directory
        # This makes the application portable and relative to where it's run from
        return Path.cwd()
    
    @staticmethod
    def _get_default_thread_count() -> int:
        """Get default thread count based on system capabilities."""
        import os
        try:
            # Use number of CPU cores, capped at 8 for reasonable default
            return min(os.cpu_count() or 4, 8)
        except:
            return 4
    
    def add_recent_project(self, project_path: str) -> None:
        """Add a project to the recent projects list."""
        # Remove if already exists
        if project_path in self.recent_projects:
            self.recent_projects.remove(project_path)
        
        # Add to front of list
        self.recent_projects.insert(0, project_path)
        
        # Trim to max length
        if len(self.recent_projects) > self.max_recent_projects:
            self.recent_projects = self.recent_projects[:self.max_recent_projects]
    
    def remove_recent_project(self, project_path: str) -> None:
        """Remove a project from the recent projects list."""
        if project_path in self.recent_projects:
            self.recent_projects.remove(project_path)
    
    def clear_recent_projects(self) -> None:
        """Clear all recent projects."""
        self.recent_projects.clear()
    
    def add_particle_shape_set(self, shape_set: str) -> None:
        """Add a particle shape set if not already present."""
        if shape_set not in self.particle_shape_sets:
            self.particle_shape_sets.append(shape_set)
    
    def remove_particle_shape_set(self, shape_set: str) -> None:
        """Remove a particle shape set."""
        if shape_set in self.particle_shape_sets:
            self.particle_shape_sets.remove(shape_set)
    
    def validate(self) -> Dict[str, Any]:
        """Validate user configuration."""
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Validate app directory
        try:
            if not self.app_directory.parent.exists():
                validation_result['warnings'].append(
                    f"Parent directory of app directory does not exist: {self.app_directory.parent}"
                )
        except Exception as e:
            validation_result['errors'].append(f"Invalid app directory path: {e}")
            validation_result['is_valid'] = False
        
        # Validate numeric values
        if self.max_recent_projects < 0:
            validation_result['errors'].append("max_recent_projects must be non-negative")
            validation_result['is_valid'] = False
        
        if self.auto_save_interval < 30:
            validation_result['warnings'].append("Auto-save interval less than 30 seconds may impact performance")
        
        if self.max_worker_threads < 1:
            validation_result['errors'].append("max_worker_threads must be at least 1")
            validation_result['is_valid'] = False
        elif self.max_worker_threads > 32:
            validation_result['warnings'].append("Very high thread count may impact performance")
        
        if self.memory_limit_mb < 512:
            validation_result['warnings'].append("Low memory limit may cause performance issues")
        elif self.memory_limit_mb > 32768:
            validation_result['warnings'].append("Very high memory limit may not be available")
        
        # Validate recent projects
        valid_recent_projects = []
        for project_path in self.recent_projects:
            if Path(project_path).exists():
                valid_recent_projects.append(project_path)
            else:
                validation_result['warnings'].append(f"Recent project not found: {project_path}")
        
        if len(valid_recent_projects) != len(self.recent_projects):
            self.recent_projects = valid_recent_projects
        
        return validation_result
    
    def ensure_directories_exist(self) -> None:
        """Ensure that the app directory exists."""
        try:
            self.app_directory.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise RuntimeError(f"Failed to create app directory {self.app_directory}: {e}")
    
    def get_memory_limit_bytes(self) -> int:
        """Get memory limit in bytes."""
        return self.memory_limit_mb * 1024 * 1024
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information relevant to user configuration."""
        import psutil
        import os
        
        try:
            memory_info = psutil.virtual_memory()
            
            return {
                'platform': platform.system(),
                'architecture': platform.architecture()[0],
                'cpu_count': os.cpu_count(),
                'total_memory_mb': memory_info.total // (1024 * 1024),
                'available_memory_mb': memory_info.available // (1024 * 1024),
                'app_directory_exists': self.app_directory.exists(),
                'app_directory_writable': os.access(self.app_directory.parent, os.W_OK)
            }
        except ImportError:
            # psutil not available, return basic info
            return {
                'platform': platform.system(),
                'architecture': platform.architecture()[0],
                'cpu_count': os.cpu_count(),
                'app_directory_exists': self.app_directory.exists()
            }
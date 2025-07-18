#!/usr/bin/env python3
"""
Configuration Manager for VCCTL

Provides centralized configuration management with YAML support,
environment-specific configurations, and runtime updates.
"""

import logging
import os
import platform
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Type, TypeVar
from dataclasses import asdict

from app.config.user_config import UserConfig
from app.config.directories_config import DirectoriesConfig
from app.config.materials_config import MaterialsConfig
from app.config.simulation_config import SimulationConfig
from app.config.ui_config import UIConfig
from app.config.logging_config import LoggingConfig

T = TypeVar('T')


class ConfigurationError(Exception):
    """Raised when configuration operations fail."""
    pass


class ConfigManager:
    """
    Central configuration manager for the VCCTL application.
    
    Handles loading, saving, and validating configuration from YAML files
    with support for environment-specific overrides and runtime updates.
    """
    
    def __init__(self):
        self.logger = logging.getLogger('VCCTL.ConfigManager')
        
        # Configuration instances
        self._user_config: Optional[UserConfig] = None
        self._directories_config: Optional[DirectoriesConfig] = None
        self._materials_config: Optional[MaterialsConfig] = None
        self._simulation_config: Optional[SimulationConfig] = None
        self._ui_config: Optional[UIConfig] = None
        self._logging_config: Optional[LoggingConfig] = None
        
        # Configuration file paths
        self._config_dir = self._get_platform_config_dir()
        self._main_config_file = self._config_dir / "config.yml"
        self._user_preferences_file = self._config_dir / "preferences.yml"
        
        # Ensure config directory exists
        self._config_dir.mkdir(parents=True, exist_ok=True)
        
        # Load configurations
        self._load_configurations()
    
    def _get_platform_config_dir(self) -> Path:
        """Get configuration directory relative to application directory."""
        # Use a config subdirectory relative to the current working directory
        # This makes the application portable and self-contained
        return Path.cwd() / "config"
    
    def _load_configurations(self) -> None:
        """Load all configuration sections."""
        try:
            # Load main configuration file
            main_config = self._load_config_file(self._main_config_file, self._get_default_config())
            
            # Load user preferences (if exists)
            user_prefs = {}
            if self._user_preferences_file.exists():
                user_prefs = self._load_config_file(self._user_preferences_file, {})
            
            # Merge configurations with user preferences taking precedence
            merged_config = self._merge_configs(main_config, user_prefs)
            
            # Create configuration instances
            self._user_config = UserConfig.from_dict(
                merged_config.get('user', {}), 
                self._config_dir
            )
            self._directories_config = DirectoriesConfig.from_dict(
                merged_config.get('directories', {}), 
                self._user_config.app_directory
            )
            self._materials_config = MaterialsConfig.from_dict(
                merged_config.get('materials', {})
            )
            self._simulation_config = SimulationConfig.from_dict(
                merged_config.get('simulation', {})
            )
            self._ui_config = UIConfig.from_dict(
                merged_config.get('ui', {})
            )
            self._logging_config = LoggingConfig.from_dict(
                merged_config.get('logging', {})
            )
            
            self.logger.info(f"Configuration loaded from {self._config_dir}")
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            # Fall back to defaults
            self._create_default_configurations()
    
    def _load_config_file(self, file_path: Path, default: Dict[str, Any]) -> Dict[str, Any]:
        """Load configuration from a YAML file."""
        if not file_path.exists():
            self.logger.info(f"Configuration file {file_path} not found, using defaults")
            return default
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
            
            # Validate configuration structure
            self._validate_config_structure(config)
            
            return config
            
        except yaml.YAMLError as e:
            self.logger.error(f"YAML parsing error in {file_path}: {e}")
            raise ConfigurationError(f"Invalid YAML in configuration file: {e}")
        except Exception as e:
            self.logger.error(f"Failed to load config file {file_path}: {e}")
            raise ConfigurationError(f"Failed to load configuration: {e}")
    
    def _validate_config_structure(self, config: Dict[str, Any]) -> None:
        """Validate configuration structure."""
        # Basic structure validation
        if not isinstance(config, dict):
            raise ConfigurationError("Configuration must be a dictionary")
        
        # Validate section types
        expected_sections = {
            'user': dict,
            'directories': dict,
            'materials': dict,
            'simulation': dict,
            'ui': dict,
            'logging': dict
        }
        
        for section, expected_type in expected_sections.items():
            if section in config and not isinstance(config[section], expected_type):
                raise ConfigurationError(f"Configuration section '{section}' must be {expected_type.__name__}")
    
    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge configuration dictionaries."""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _create_default_configurations(self) -> None:
        """Create default configuration instances."""
        self._user_config = UserConfig.create_default(self._config_dir)
        self._directories_config = DirectoriesConfig.create_default(self._user_config.app_directory)
        self._materials_config = MaterialsConfig.create_default()
        self._simulation_config = SimulationConfig.create_default()
        self._ui_config = UIConfig.create_default()
        self._logging_config = LoggingConfig.create_default()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration structure."""
        return {
            'user': {},
            'directories': {},
            'materials': {},
            'simulation': {},
            'ui': {},
            'logging': {}
        }
    
    # Property accessors for configuration sections
    @property
    def user(self) -> UserConfig:
        """Get user configuration."""
        if self._user_config is None:
            self._user_config = UserConfig.create_default(self._config_dir)
        return self._user_config
    
    @property
    def directories(self) -> DirectoriesConfig:
        """Get directories configuration."""
        if self._directories_config is None:
            self._directories_config = DirectoriesConfig.create_default(self.user.app_directory)
        return self._directories_config
    
    @property
    def materials(self) -> MaterialsConfig:
        """Get materials configuration."""
        if self._materials_config is None:
            self._materials_config = MaterialsConfig.create_default()
        return self._materials_config
    
    @property
    def simulation(self) -> SimulationConfig:
        """Get simulation configuration."""
        if self._simulation_config is None:
            self._simulation_config = SimulationConfig.create_default()
        return self._simulation_config
    
    @property
    def ui(self) -> UIConfig:
        """Get UI configuration."""
        if self._ui_config is None:
            self._ui_config = UIConfig.create_default()
        return self._ui_config
    
    @property
    def logging_config(self) -> LoggingConfig:
        """Get logging configuration."""
        if self._logging_config is None:
            self._logging_config = LoggingConfig.create_default()
        return self._logging_config
    
    # Configuration persistence methods
    def save_configuration(self) -> None:
        """Save current configuration to files."""
        try:
            # Prepare main configuration
            main_config = {
                'user': asdict(self.user),
                'directories': asdict(self.directories),
                'materials': asdict(self.materials),
                'simulation': asdict(self.simulation),
                'logging': asdict(self.logging_config)
            }
            
            # Prepare user preferences (UI settings)
            user_prefs = {
                'ui': asdict(self.ui)
            }
            
            # Save main configuration
            self._save_config_file(self._main_config_file, main_config)
            
            # Save user preferences
            self._save_config_file(self._user_preferences_file, user_prefs)
            
            self.logger.info("Configuration saved successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
            raise ConfigurationError(f"Failed to save configuration: {e}")
    
    def _save_config_file(self, file_path: Path, config: Dict[str, Any]) -> None:
        """Save configuration to a YAML file."""
        try:
            # Ensure directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, indent=2, sort_keys=True)
                
        except Exception as e:
            self.logger.error(f"Failed to save config file {file_path}: {e}")
            raise ConfigurationError(f"Failed to save configuration file: {e}")
    
    def reload_configuration(self) -> None:
        """Reload configuration from files."""
        self.logger.info("Reloading configuration")
        self._load_configurations()
    
    def update_user_preference(self, section: str, key: str, value: Any) -> None:
        """Update a user preference at runtime."""
        try:
            if section == 'ui':
                setattr(self.ui, key, value)
            elif section == 'user':
                setattr(self.user, key, value)
            elif section == 'simulation':
                setattr(self.simulation, key, value)
            else:
                raise ConfigurationError(f"Unknown configuration section: {section}")
            
            self.logger.debug(f"Updated preference {section}.{key} = {value}")
            
        except AttributeError:
            raise ConfigurationError(f"Unknown preference key: {section}.{key}")
        except Exception as e:
            self.logger.error(f"Failed to update preference {section}.{key}: {e}")
            raise ConfigurationError(f"Failed to update preference: {e}")
    
    def get_preference(self, section: str, key: str, default: Any = None) -> Any:
        """Get a user preference value."""
        try:
            if section == 'ui':
                return getattr(self.ui, key, default)
            elif section == 'user':
                return getattr(self.user, key, default)
            elif section == 'simulation':
                return getattr(self.simulation, key, default)
            else:
                return default
                
        except AttributeError:
            return default
    
    def validate_configuration(self) -> Dict[str, Any]:
        """Validate current configuration and return validation results."""
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': []
        }
        
        try:
            # Validate user configuration
            user_validation = self.user.validate()
            if not user_validation['is_valid']:
                validation_result['errors'].extend(user_validation['errors'])
                validation_result['is_valid'] = False
            validation_result['warnings'].extend(user_validation.get('warnings', []))
            
            # Validate directories configuration
            dirs_validation = self.directories.validate()
            if not dirs_validation['is_valid']:
                validation_result['errors'].extend(dirs_validation['errors'])
                validation_result['is_valid'] = False
            validation_result['warnings'].extend(dirs_validation.get('warnings', []))
            
            # Validate materials configuration
            materials_validation = self.materials.validate()
            if not materials_validation['is_valid']:
                validation_result['errors'].extend(materials_validation['errors'])
                validation_result['is_valid'] = False
            validation_result['warnings'].extend(materials_validation.get('warnings', []))
            
            # Validate simulation configuration
            sim_validation = self.simulation.validate()
            if not sim_validation['is_valid']:
                validation_result['errors'].extend(sim_validation['errors'])
                validation_result['is_valid'] = False
            validation_result['warnings'].extend(sim_validation.get('warnings', []))
            
            return validation_result
            
        except Exception as e:
            self.logger.error(f"Configuration validation failed: {e}")
            validation_result['is_valid'] = False
            validation_result['errors'].append(f"Validation error: {e}")
            return validation_result
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get a summary of current configuration."""
        return {
            'config_directory': str(self._config_dir),
            'platform': platform.system(),
            'app_directory': str(self.user.app_directory),
            'database_path': str(self.directories.database_directory),
            'materials_count': len(self.materials.get_all_materials()),
            'ui_theme': self.ui.theme,
            'log_level': self.logging_config.level
        }
    
    def export_configuration(self, export_path: Path) -> None:
        """Export current configuration to a file."""
        try:
            config_data = {
                'user': asdict(self.user),
                'directories': asdict(self.directories),
                'materials': asdict(self.materials),
                'simulation': asdict(self.simulation),
                'ui': asdict(self.ui),
                'logging': asdict(self.logging_config),
                'metadata': {
                    'export_timestamp': str(Path().cwd()),
                    'platform': platform.system(),
                    'vcctl_version': '10.0.0'  # Would come from app info
                }
            }
            
            self._save_config_file(export_path, config_data)
            self.logger.info(f"Configuration exported to {export_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to export configuration: {e}")
            raise ConfigurationError(f"Failed to export configuration: {e}")
    
    def import_configuration(self, import_path: Path) -> None:
        """Import configuration from a file."""
        try:
            imported_config = self._load_config_file(import_path, {})
            
            # Update configurations (excluding metadata)
            for section in ['user', 'directories', 'materials', 'simulation', 'ui', 'logging']:
                if section in imported_config:
                    section_data = imported_config[section]
                    
                    if section == 'user':
                        self._user_config = UserConfig.from_dict(section_data, self._config_dir)
                    elif section == 'directories':
                        self._directories_config = DirectoriesConfig.from_dict(section_data, self.user.app_directory)
                    elif section == 'materials':
                        self._materials_config = MaterialsConfig.from_dict(section_data)
                    elif section == 'simulation':
                        self._simulation_config = SimulationConfig.from_dict(section_data)
                    elif section == 'ui':
                        self._ui_config = UIConfig.from_dict(section_data)
                    elif section == 'logging':
                        self._logging_config = LoggingConfig.from_dict(section_data)
            
            # Save the imported configuration
            self.save_configuration()
            
            self.logger.info(f"Configuration imported from {import_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to import configuration: {e}")
            raise ConfigurationError(f"Failed to import configuration: {e}")
    
    # Window state management methods
    def get_window_state(self) -> Dict[str, Any]:
        """Get current window state settings."""
        return self.ui.get_window_geometry()
    
    def set_window_state(self, window_state: Dict[str, Any]) -> None:
        """Set window state settings."""
        width = window_state.get('width', 1200)
        height = window_state.get('height', 800)
        x = window_state.get('x', -1)
        y = window_state.get('y', -1)
        maximized = window_state.get('maximized', False)
        
        self.ui.set_window_geometry(width, height, x, y, maximized)
    
    def save(self) -> None:
        """Save current configuration (alias for save_configuration)."""
        self.save_configuration()


# Global configuration manager instance
config_manager = ConfigManager()
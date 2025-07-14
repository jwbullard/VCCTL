"""
Plugin Descriptor for VCCTL GTK Application
"""

import yaml
from typing import Dict, Any, List, Optional
from pathlib import Path


class PluginDescriptor:
    """Describes a plugin's metadata and configuration"""
    
    def __init__(self, descriptor_path: Path):
        self.descriptor_path = descriptor_path
        self.plugin_dir = descriptor_path.parent
        self._data = {}
        self._load_descriptor()
    
    def _load_descriptor(self):
        """Load plugin descriptor from YAML file"""
        try:
            with open(self.descriptor_path, 'r') as f:
                self._data = yaml.safe_load(f)
        except Exception as e:
            raise ValueError(f"Failed to load plugin descriptor: {e}")
    
    @property
    def name(self) -> str:
        """Plugin name"""
        return self._data.get('name', '')
    
    @property
    def version(self) -> str:
        """Plugin version"""
        return self._data.get('version', '0.0.0')
    
    @property
    def description(self) -> str:
        """Plugin description"""
        return self._data.get('description', '')
    
    @property
    def author(self) -> str:
        """Plugin author"""
        return self._data.get('author', '')
    
    @property
    def main_class(self) -> str:
        """Main plugin class"""
        return self._data.get('main_class', '')
    
    @property
    def module_name(self) -> str:
        """Main plugin module"""
        return self._data.get('module_name', '')
    
    @property
    def min_vcctl_version(self) -> str:
        """Minimum VCCTL version required"""
        return self._data.get('min_vcctl_version', '0.0.0')
    
    @property
    def max_vcctl_version(self) -> Optional[str]:
        """Maximum VCCTL version supported"""
        return self._data.get('max_vcctl_version')
    
    @property
    def dependencies(self) -> List[str]:
        """Plugin dependencies"""
        return self._data.get('dependencies', [])
    
    @property
    def python_dependencies(self) -> List[str]:
        """Python package dependencies"""
        return self._data.get('python_dependencies', [])
    
    @property
    def properties(self) -> Dict[str, Any]:
        """Plugin properties"""
        return self._data.get('properties', {})
    
    @property
    def enabled(self) -> bool:
        """Whether plugin is enabled"""
        return self._data.get('enabled', True)
    
    @property
    def ui_components(self) -> Dict[str, Any]:
        """UI components provided by plugin"""
        return self._data.get('ui_components', {})
    
    @property
    def operation_handlers(self) -> Dict[str, Any]:
        """Operation handlers provided by plugin"""
        return self._data.get('operation_handlers', {})
    
    @property
    def configuration_schema(self) -> Optional[Dict[str, Any]]:
        """Configuration schema for plugin"""
        return self._data.get('configuration_schema')
    
    def set_enabled(self, enabled: bool):
        """Set plugin enabled state"""
        self._data['enabled'] = enabled
        self._save_descriptor()
    
    def _save_descriptor(self):
        """Save descriptor back to file"""
        try:
            with open(self.descriptor_path, 'w') as f:
                yaml.dump(self._data, f, default_flow_style=False)
        except Exception as e:
            raise ValueError(f"Failed to save plugin descriptor: {e}")
    
    def validate(self) -> List[str]:
        """Validate plugin descriptor and return list of errors"""
        errors = []
        
        if not self.name:
            errors.append("Plugin name is required")
        
        if not self.version:
            errors.append("Plugin version is required")
        
        if not self.main_class and not self.module_name:
            errors.append("Either main_class or module_name is required")
        
        if not self.plugin_dir.exists():
            errors.append(f"Plugin directory does not exist: {self.plugin_dir}")
        
        return errors
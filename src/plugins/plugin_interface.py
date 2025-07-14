"""
Plugin Interface for VCCTL GTK Application
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class PluginInterface(ABC):
    """Base interface that all VCCTL plugins must implement"""
    
    @abstractmethod
    def get_name(self) -> str:
        """Return the plugin name"""
        pass
    
    @abstractmethod
    def get_version(self) -> str:
        """Return the plugin version"""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """Return the plugin description"""
        pass
    
    @abstractmethod
    def get_author(self) -> str:
        """Return the plugin author"""
        pass
    
    @abstractmethod
    def initialize(self, context: 'PluginContext') -> None:
        """Initialize the plugin with the given context"""
        pass
    
    @abstractmethod
    def destroy(self) -> None:
        """Clean up plugin resources"""
        pass
    
    @abstractmethod
    def is_compatible(self, vcctl_version: str) -> bool:
        """Check if plugin is compatible with VCCTL version"""
        pass
    
    def get_metadata(self) -> Dict[str, Any]:
        """Return additional plugin metadata"""
        return {}
    
    def get_dependencies(self) -> list:
        """Return list of plugin dependencies"""
        return []
    
    def get_ui_components(self) -> Dict[str, Any]:
        """Return UI components provided by this plugin"""
        return {}
    
    def get_operation_handlers(self) -> Dict[str, Any]:
        """Return operation handlers provided by this plugin"""
        return {}
    
    def get_configuration_schema(self) -> Optional[Dict[str, Any]]:
        """Return configuration schema for this plugin"""
        return None
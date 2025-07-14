"""
Plugin Context for VCCTL GTK Application
"""

from typing import Any, Dict, Optional


class PluginContext:
    """Context object providing access to VCCTL services and resources"""
    
    def __init__(self, service_container, config_manager, main_window):
        self._service_container = service_container
        self._config_manager = config_manager
        self._main_window = main_window
        self._plugin_data = {}
    
    @property
    def service_container(self):
        """Get the VCCTL service container"""
        return self._service_container
    
    @property
    def config_manager(self):
        """Get the configuration manager"""
        return self._config_manager
    
    @property
    def main_window(self):
        """Get the main GTK window"""
        return self._main_window
    
    def get_service(self, service_name: str) -> Any:
        """Get a service by name from the service container"""
        return getattr(self._service_container, service_name, None)
    
    def get_config(self, section: str, key: str = None) -> Any:
        """Get configuration value"""
        if key:
            return self._config_manager.get_config(section, key)
        return self._config_manager.get_section(section)
    
    def set_config(self, section: str, key: str, value: Any) -> None:
        """Set configuration value"""
        self._config_manager.set_config(section, key, value)
    
    def get_plugin_data(self, plugin_name: str, key: str = None) -> Any:
        """Get plugin-specific data"""
        if plugin_name not in self._plugin_data:
            self._plugin_data[plugin_name] = {}
        
        if key:
            return self._plugin_data[plugin_name].get(key)
        return self._plugin_data[plugin_name]
    
    def set_plugin_data(self, plugin_name: str, key: str, value: Any) -> None:
        """Set plugin-specific data"""
        if plugin_name not in self._plugin_data:
            self._plugin_data[plugin_name] = {}
        self._plugin_data[plugin_name][key] = value
    
    def add_menu_item(self, menu_path: str, callback, label: str = None) -> None:
        """Add menu item to the main window"""
        if hasattr(self._main_window, 'add_plugin_menu_item'):
            self._main_window.add_plugin_menu_item(menu_path, callback, label)
    
    def add_toolbar_button(self, button_id: str, callback, label: str, icon: str = None) -> None:
        """Add toolbar button to the main window"""
        if hasattr(self._main_window, 'add_plugin_toolbar_button'):
            self._main_window.add_plugin_toolbar_button(button_id, callback, label, icon)
    
    def add_panel(self, panel_id: str, panel_widget, title: str) -> None:
        """Add a new panel to the main window"""
        if hasattr(self._main_window, 'add_plugin_panel'):
            self._main_window.add_plugin_panel(panel_id, panel_widget, title)
    
    def show_message(self, message: str, message_type: str = 'info') -> None:
        """Show a message dialog"""
        if hasattr(self._main_window, 'show_plugin_message'):
            self._main_window.show_plugin_message(message, message_type)
"""
Plugin Manager for VCCTL GTK Application
"""

import os
import sys
import importlib
import importlib.util
from typing import Dict, List, Optional, Type
from pathlib import Path
import logging

from .plugin_interface import PluginInterface
from .plugin_descriptor import PluginDescriptor
from .plugin_context import PluginContext


class PluginManager:
    """Manages plugin discovery, loading, and lifecycle"""
    
    def __init__(self, plugin_dirs: List[Path], service_container, config_manager, main_window):
        self.plugin_dirs = plugin_dirs
        self.service_container = service_container
        self.config_manager = config_manager
        self.main_window = main_window
        
        self._loaded_plugins: Dict[str, PluginInterface] = {}
        self._plugin_descriptors: Dict[str, PluginDescriptor] = {}
        self._plugin_modules: Dict[str, any] = {}
        self._context = PluginContext(service_container, config_manager, main_window)
        
        self.logger = logging.getLogger(__name__)
    
    def discover_plugins(self) -> List[PluginDescriptor]:
        """Discover all available plugins"""
        discovered = []
        
        for plugin_dir in self.plugin_dirs:
            if not plugin_dir.exists():
                continue
                
            for item in plugin_dir.iterdir():
                if item.is_dir():
                    descriptor_path = item / "plugin.yml"
                    if descriptor_path.exists():
                        try:
                            descriptor = PluginDescriptor(descriptor_path)
                            errors = descriptor.validate()
                            if errors:
                                self.logger.error(f"Plugin validation failed for {item.name}: {errors}")
                                continue
                            
                            discovered.append(descriptor)
                            self._plugin_descriptors[descriptor.name] = descriptor
                        except Exception as e:
                            self.logger.error(f"Failed to load plugin descriptor from {descriptor_path}: {e}")
        
        return discovered
    
    def load_plugin(self, plugin_name: str) -> bool:
        """Load a specific plugin"""
        if plugin_name in self._loaded_plugins:
            self.logger.warning(f"Plugin {plugin_name} is already loaded")
            return True
        
        descriptor = self._plugin_descriptors.get(plugin_name)
        if not descriptor:
            self.logger.error(f"Plugin descriptor not found for {plugin_name}")
            return False
        
        if not descriptor.enabled:
            self.logger.info(f"Plugin {plugin_name} is disabled")
            return False
        
        try:
            # Check dependencies
            if not self._check_dependencies(descriptor):
                return False
            
            # Load the plugin module
            plugin_module = self._load_plugin_module(descriptor)
            if not plugin_module:
                return False
            
            # Instantiate the plugin
            plugin_instance = self._instantiate_plugin(descriptor, plugin_module)
            if not plugin_instance:
                return False
            
            # Initialize the plugin
            plugin_instance.initialize(self._context)
            
            # Register the plugin
            self._loaded_plugins[plugin_name] = plugin_instance
            self._plugin_modules[plugin_name] = plugin_module
            
            self.logger.info(f"Successfully loaded plugin: {plugin_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load plugin {plugin_name}: {e}")
            return False
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a specific plugin"""
        if plugin_name not in self._loaded_plugins:
            self.logger.warning(f"Plugin {plugin_name} is not loaded")
            return True
        
        try:
            plugin = self._loaded_plugins[plugin_name]
            plugin.destroy()
            
            del self._loaded_plugins[plugin_name]
            del self._plugin_modules[plugin_name]
            
            self.logger.info(f"Successfully unloaded plugin: {plugin_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to unload plugin {plugin_name}: {e}")
            return False
    
    def reload_plugin(self, plugin_name: str) -> bool:
        """Reload a specific plugin"""
        if plugin_name in self._loaded_plugins:
            if not self.unload_plugin(plugin_name):
                return False
        
        # Reload the descriptor
        descriptor = self._plugin_descriptors.get(plugin_name)
        if descriptor:
            try:
                descriptor._load_descriptor()
            except Exception as e:
                self.logger.error(f"Failed to reload descriptor for {plugin_name}: {e}")
                return False
        
        return self.load_plugin(plugin_name)
    
    def load_all_plugins(self) -> Dict[str, bool]:
        """Load all discovered plugins"""
        results = {}
        
        # Sort plugins by dependencies
        sorted_plugins = self._sort_plugins_by_dependencies()
        
        for plugin_name in sorted_plugins:
            results[plugin_name] = self.load_plugin(plugin_name)
        
        return results
    
    def get_plugin(self, plugin_name: str) -> Optional[PluginInterface]:
        """Get a loaded plugin by name"""
        return self._loaded_plugins.get(plugin_name)
    
    def get_all_plugins(self) -> Dict[str, PluginInterface]:
        """Get all loaded plugins"""
        return self._loaded_plugins.copy()
    
    def get_plugin_descriptor(self, plugin_name: str) -> Optional[PluginDescriptor]:
        """Get plugin descriptor by name"""
        return self._plugin_descriptors.get(plugin_name)
    
    def get_all_descriptors(self) -> Dict[str, PluginDescriptor]:
        """Get all plugin descriptors"""
        return self._plugin_descriptors.copy()
    
    def enable_plugin(self, plugin_name: str) -> bool:
        """Enable a plugin"""
        descriptor = self._plugin_descriptors.get(plugin_name)
        if not descriptor:
            return False
        
        descriptor.set_enabled(True)
        return True
    
    def disable_plugin(self, plugin_name: str) -> bool:
        """Disable a plugin"""
        descriptor = self._plugin_descriptors.get(plugin_name)
        if not descriptor:
            return False
        
        # Unload if currently loaded
        if plugin_name in self._loaded_plugins:
            self.unload_plugin(plugin_name)
        
        descriptor.set_enabled(False)
        return True
    
    def _check_dependencies(self, descriptor: PluginDescriptor) -> bool:
        """Check if plugin dependencies are satisfied"""
        for dep in descriptor.dependencies:
            if dep not in self._loaded_plugins:
                self.logger.error(f"Dependency {dep} not loaded for plugin {descriptor.name}")
                return False
        return True
    
    def _load_plugin_module(self, descriptor: PluginDescriptor):
        """Load the plugin module"""
        plugin_path = descriptor.plugin_dir
        
        # Add plugin directory to Python path
        if str(plugin_path) not in sys.path:
            sys.path.insert(0, str(plugin_path))
        
        try:
            if descriptor.module_name:
                module_name = descriptor.module_name
            else:
                module_name = "plugin"
            
            # Try to import the module
            module_path = plugin_path / f"{module_name}.py"
            if not module_path.exists():
                self.logger.error(f"Plugin module not found: {module_path}")
                return None
            
            spec = importlib.util.spec_from_file_location(f"{descriptor.name}.{module_name}", module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            return module
            
        except Exception as e:
            self.logger.error(f"Failed to load plugin module for {descriptor.name}: {e}")
            return None
    
    def _instantiate_plugin(self, descriptor: PluginDescriptor, module) -> Optional[PluginInterface]:
        """Instantiate the plugin class"""
        try:
            if descriptor.main_class:
                plugin_class = getattr(module, descriptor.main_class)
            else:
                # Look for a class that implements PluginInterface
                plugin_class = None
                for name in dir(module):
                    obj = getattr(module, name)
                    if (isinstance(obj, type) and 
                        issubclass(obj, PluginInterface) and 
                        obj != PluginInterface):
                        plugin_class = obj
                        break
                
                if not plugin_class:
                    self.logger.error(f"No plugin class found in module for {descriptor.name}")
                    return None
            
            return plugin_class()
            
        except Exception as e:
            self.logger.error(f"Failed to instantiate plugin {descriptor.name}: {e}")
            return None
    
    def _sort_plugins_by_dependencies(self) -> List[str]:
        """Sort plugins by their dependencies"""
        sorted_plugins = []
        visited = set()
        temp_visited = set()
        
        def visit(plugin_name: str):
            if plugin_name in temp_visited:
                self.logger.error(f"Circular dependency detected involving {plugin_name}")
                return
            
            if plugin_name in visited:
                return
            
            temp_visited.add(plugin_name)
            
            descriptor = self._plugin_descriptors.get(plugin_name)
            if descriptor:
                for dep in descriptor.dependencies:
                    if dep in self._plugin_descriptors:
                        visit(dep)
            
            temp_visited.remove(plugin_name)
            visited.add(plugin_name)
            sorted_plugins.append(plugin_name)
        
        for plugin_name in self._plugin_descriptors:
            if plugin_name not in visited:
                visit(plugin_name)
        
        return sorted_plugins
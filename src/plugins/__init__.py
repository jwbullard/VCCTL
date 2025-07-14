"""
VCCTL Plugin Framework

This module provides the core plugin architecture for VCCTL GTK application.
"""

from .plugin_interface import PluginInterface
from .plugin_manager import PluginManager
from .plugin_descriptor import PluginDescriptor
from .plugin_context import PluginContext

__all__ = ['PluginInterface', 'PluginManager', 'PluginDescriptor', 'PluginContext']
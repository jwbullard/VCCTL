"""
Plugin Security and Sandboxing for VCCTL GTK Application
"""

import os
import sys
import types
import importlib
from typing import Set, List, Dict, Any, Optional
import logging


class PluginSecurity:
    """Security manager for plugin sandboxing"""
    
    # Restricted modules that plugins cannot import
    RESTRICTED_MODULES = {
        'os',
        'sys', 
        'subprocess',
        'shutil',
        'importlib',
        'builtins',
        'ctypes',
        'marshal',
        'pickle',
        'dill',
        'eval',
        'exec',
        'compile',
        '__import__'
    }
    
    # Allowed modules that plugins can safely import
    ALLOWED_MODULES = {
        'json',
        'yaml',
        'csv',
        'xml',
        'sqlite3',
        'datetime',
        'time',
        'math',
        'random',
        'collections',
        'itertools',
        'functools',
        'operator',
        're',
        'string',
        'uuid',
        'base64',
        'hashlib',
        'pathlib',
        'typing',
        'logging',
        'gi.repository.Gtk',
        'gi.repository.GLib',
        'gi.repository.Gdk',
        'numpy',
        'scipy',
        'matplotlib',
        'pandas'
    }
    
    # File system operations that are restricted
    RESTRICTED_FS_OPERATIONS = {
        'remove',
        'unlink', 
        'rmdir',
        'removedirs',
        'rmtree',
        'system',
        'popen',
        'spawn',
        'exec'
    }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._original_import = None
        self._plugin_permissions: Dict[str, Set[str]] = {}
    
    def set_plugin_permissions(self, plugin_name: str, permissions: Set[str]):
        """Set permissions for a specific plugin"""
        self._plugin_permissions[plugin_name] = permissions
    
    def get_plugin_permissions(self, plugin_name: str) -> Set[str]:
        """Get permissions for a specific plugin"""
        return self._plugin_permissions.get(plugin_name, set())
    
    def create_sandbox(self, plugin_name: str) -> Dict[str, Any]:
        """Create a sandboxed environment for a plugin"""
        sandbox = {
            '__builtins__': self._create_restricted_builtins(),
            '__name__': f'plugin_{plugin_name}',
            '__file__': f'<plugin_{plugin_name}>',
            '__package__': None,
            '__cached__': None,
            '__spec__': None,
            '__loader__': None,
            '__annotations__': {},
        }
        
        # Add safe imports
        sandbox['__import__'] = self._create_safe_import(plugin_name)
        
        return sandbox
    
    def _create_restricted_builtins(self) -> Dict[str, Any]:
        """Create restricted built-in functions"""
        safe_builtins = {}
        
        # Copy safe built-ins
        for name in dir(__builtins__):
            if name.startswith('_'):
                continue
            
            if name in ['eval', 'exec', 'compile', '__import__', 'open', 'input']:
                continue
            
            obj = getattr(__builtins__, name)
            if callable(obj) and not name.startswith('_'):
                safe_builtins[name] = obj
        
        # Add restricted open function
        safe_builtins['open'] = self._create_safe_open()
        
        return safe_builtins
    
    def _create_safe_open(self):
        """Create a safe version of open() that restricts file access"""
        def safe_open(file, mode='r', **kwargs):
            # Convert to Path for easier manipulation
            from pathlib import Path
            path = Path(file)
            
            # Only allow access to plugin directories and tmp
            allowed_dirs = [
                Path.home() / '.vcctl' / 'plugins',
                Path('/tmp'),
                Path('/var/tmp'),
                Path.cwd() / 'plugins',
                Path.cwd() / 'data',
                Path.cwd() / 'output'
            ]
            
            # Check if path is within allowed directories
            try:
                resolved_path = path.resolve()
                allowed = any(
                    str(resolved_path).startswith(str(allowed_dir.resolve()))
                    for allowed_dir in allowed_dirs
                )
                
                if not allowed:
                    raise PermissionError(f"Access denied to file: {file}")
                
                # Restrict write modes to specific directories
                if 'w' in mode or 'a' in mode:
                    write_dirs = [
                        Path.home() / '.vcctl' / 'plugins',
                        Path('/tmp'),
                        Path('/var/tmp'),
                        Path.cwd() / 'output'
                    ]
                    
                    write_allowed = any(
                        str(resolved_path).startswith(str(write_dir.resolve()))
                        for write_dir in write_dirs
                    )
                    
                    if not write_allowed:
                        raise PermissionError(f"Write access denied to file: {file}")
                
                return open(file, mode, **kwargs)
                
            except Exception as e:
                raise PermissionError(f"File access error: {e}")
        
        return safe_open
    
    def _create_safe_import(self, plugin_name: str):
        """Create a safe import function that restricts module access"""
        def safe_import(name, globals=None, locals=None, fromlist=(), level=0):
            # Check if module is explicitly restricted
            if name in self.RESTRICTED_MODULES:
                raise ImportError(f"Module '{name}' is restricted for security reasons")
            
            # Check if module is in allowed list
            if name not in self.ALLOWED_MODULES:
                # Check if it's a plugin-specific module
                if not name.startswith(f'plugin_{plugin_name}'):
                    self.logger.warning(f"Plugin {plugin_name} attempted to import restricted module: {name}")
                    raise ImportError(f"Module '{name}' is not allowed for plugins")
            
            # Check plugin permissions
            permissions = self.get_plugin_permissions(plugin_name)
            if f'import_{name}' not in permissions and name not in self.ALLOWED_MODULES:
                raise ImportError(f"Plugin {plugin_name} does not have permission to import '{name}'")
            
            return importlib.__import__(name, globals, locals, fromlist, level)
        
        return safe_import
    
    def validate_plugin_code(self, plugin_name: str, code: str) -> List[str]:
        """Validate plugin code for security issues"""
        violations = []
        
        # Check for restricted imports
        for module in self.RESTRICTED_MODULES:
            if f'import {module}' in code or f'from {module}' in code:
                violations.append(f"Restricted import: {module}")
        
        # Check for dangerous function calls
        dangerous_calls = [
            'eval(',
            'exec(',
            'compile(',
            '__import__(',
            'open(',
            'file(',
            'input(',
            'raw_input('
        ]
        
        for call in dangerous_calls:
            if call in code:
                violations.append(f"Dangerous function call: {call}")
        
        # Check for file system operations
        for op in self.RESTRICTED_FS_OPERATIONS:
            if f'.{op}(' in code or f' {op}(' in code:
                violations.append(f"Restricted file system operation: {op}")
        
        return violations
    
    def execute_in_sandbox(self, plugin_name: str, code: str, sandbox: Dict[str, Any]) -> Any:
        """Execute code in a sandboxed environment"""
        # Validate code first
        violations = self.validate_plugin_code(plugin_name, code)
        if violations:
            raise SecurityError(f"Security violations detected: {violations}")
        
        # Compile and execute in sandbox
        try:
            compiled_code = compile(code, f'<plugin_{plugin_name}>', 'exec')
            exec(compiled_code, sandbox)
            return sandbox
        except Exception as e:
            raise SecurityError(f"Execution error in sandbox: {e}")
    
    def monitor_plugin_activity(self, plugin_name: str) -> Dict[str, Any]:
        """Monitor plugin activity for security violations"""
        # This would be implemented with more sophisticated monitoring
        # For now, return basic info
        return {
            'plugin_name': plugin_name,
            'permissions': self.get_plugin_permissions(plugin_name),
            'violations': [],
            'last_activity': None
        }


class SecurityError(Exception):
    """Exception raised for security violations"""
    pass


class PluginPermission:
    """Represents a plugin permission"""
    
    def __init__(self, name: str, description: str, level: str = 'medium'):
        self.name = name
        self.description = description
        self.level = level  # 'low', 'medium', 'high'
    
    def __str__(self):
        return f"{self.name} ({self.level}): {self.description}"


# Default permissions
DEFAULT_PERMISSIONS = {
    'read_config': PluginPermission('read_config', 'Read configuration files', 'low'),
    'write_config': PluginPermission('write_config', 'Write configuration files', 'medium'),
    'read_data': PluginPermission('read_data', 'Read data files', 'low'),
    'write_data': PluginPermission('write_data', 'Write data files', 'medium'),
    'ui_access': PluginPermission('ui_access', 'Access UI components', 'low'),
    'ui_modify': PluginPermission('ui_modify', 'Modify UI components', 'medium'),
    'network_access': PluginPermission('network_access', 'Access network resources', 'high'),
    'system_info': PluginPermission('system_info', 'Access system information', 'medium'),
    'execute_commands': PluginPermission('execute_commands', 'Execute system commands', 'high'),
}
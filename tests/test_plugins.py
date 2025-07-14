"""
Unit tests for VCCTL Plugin System
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import yaml

import sys
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from plugins.plugin_interface import PluginInterface
from plugins.plugin_descriptor import PluginDescriptor
from plugins.plugin_manager import PluginManager
from plugins.plugin_context import PluginContext
from plugins.plugin_security import PluginSecurity, SecurityError


class TestPluginInterface(unittest.TestCase):
    """Test plugin interface"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.plugin = MockPlugin()
    
    def test_plugin_interface_methods(self):
        """Test that plugin interface methods work correctly"""
        self.assertEqual(self.plugin.get_name(), "Mock Plugin")
        self.assertEqual(self.plugin.get_version(), "1.0.0")
        self.assertEqual(self.plugin.get_description(), "Mock plugin for testing")
        self.assertEqual(self.plugin.get_author(), "Test Author")
        self.assertTrue(self.plugin.is_compatible("1.0.0"))
        self.assertFalse(self.plugin.is_compatible("0.9.0"))
        
        # Test initialization and destruction
        context = Mock()
        self.plugin.initialize(context)
        self.assertTrue(self.plugin.initialized)
        
        self.plugin.destroy()
        self.assertFalse(self.plugin.initialized)


class TestPluginDescriptor(unittest.TestCase):
    """Test plugin descriptor"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.plugin_dir = self.temp_dir / "test_plugin"
        self.plugin_dir.mkdir()
        
        # Create test plugin descriptor
        self.descriptor_data = {
            "name": "Test Plugin",
            "version": "1.0.0",
            "description": "Test plugin description",
            "author": "Test Author",
            "main_class": "TestPlugin",
            "min_vcctl_version": "1.0.0",
            "dependencies": ["dep1", "dep2"],
            "enabled": True
        }
        
        self.descriptor_path = self.plugin_dir / "plugin.yml"
        with open(self.descriptor_path, 'w') as f:
            yaml.dump(self.descriptor_data, f)
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir)
    
    def test_load_descriptor(self):
        """Test loading plugin descriptor"""
        descriptor = PluginDescriptor(self.descriptor_path)
        
        self.assertEqual(descriptor.name, "Test Plugin")
        self.assertEqual(descriptor.version, "1.0.0")
        self.assertEqual(descriptor.description, "Test plugin description")
        self.assertEqual(descriptor.author, "Test Author")
        self.assertEqual(descriptor.main_class, "TestPlugin")
        self.assertEqual(descriptor.min_vcctl_version, "1.0.0")
        self.assertEqual(descriptor.dependencies, ["dep1", "dep2"])
        self.assertTrue(descriptor.enabled)
    
    def test_validate_descriptor(self):
        """Test descriptor validation"""
        descriptor = PluginDescriptor(self.descriptor_path)
        errors = descriptor.validate()
        self.assertEqual(len(errors), 0)
        
        # Test invalid descriptor
        invalid_data = {"version": "1.0.0"}  # Missing required fields
        with open(self.descriptor_path, 'w') as f:
            yaml.dump(invalid_data, f)
        
        descriptor = PluginDescriptor(self.descriptor_path)
        errors = descriptor.validate()
        self.assertGreater(len(errors), 0)
    
    def test_set_enabled(self):
        """Test setting enabled state"""
        descriptor = PluginDescriptor(self.descriptor_path)
        
        descriptor.set_enabled(False)
        self.assertFalse(descriptor.enabled)
        
        # Reload and verify persistence
        descriptor2 = PluginDescriptor(self.descriptor_path)
        self.assertFalse(descriptor2.enabled)


class TestPluginManager(unittest.TestCase):
    """Test plugin manager"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.plugin_dir = self.temp_dir / "plugins"
        self.plugin_dir.mkdir()
        
        # Create mock service container and context
        self.service_container = Mock()
        self.config_manager = Mock()
        self.main_window = Mock()
        
        self.plugin_manager = PluginManager(
            [self.plugin_dir],
            self.service_container,
            self.config_manager,
            self.main_window
        )
        
        # Create test plugin
        self._create_test_plugin()
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir)
    
    def _create_test_plugin(self):
        """Create a test plugin"""
        plugin_path = self.plugin_dir / "test_plugin"
        plugin_path.mkdir()
        
        # Create plugin descriptor
        descriptor_data = {
            "name": "Test Plugin",
            "version": "1.0.0",
            "description": "Test plugin",
            "author": "Test Author",
            "main_class": "TestPlugin",
            "min_vcctl_version": "1.0.0",
            "enabled": True
        }
        
        with open(plugin_path / "plugin.yml", 'w') as f:
            yaml.dump(descriptor_data, f)
        
        # Create plugin module
        plugin_code = """
from plugins.plugin_interface import PluginInterface

class TestPlugin(PluginInterface):
    def __init__(self):
        self.initialized = False
    
    def get_name(self):
        return "Test Plugin"
    
    def get_version(self):
        return "1.0.0"
    
    def get_description(self):
        return "Test plugin"
    
    def get_author(self):
        return "Test Author"
    
    def initialize(self, context):
        self.initialized = True
    
    def destroy(self):
        self.initialized = False
    
    def is_compatible(self, vcctl_version):
        return True
"""
        
        with open(plugin_path / "plugin.py", 'w') as f:
            f.write(plugin_code)
    
    def test_discover_plugins(self):
        """Test plugin discovery"""
        discovered = self.plugin_manager.discover_plugins()
        self.assertEqual(len(discovered), 1)
        self.assertEqual(discovered[0].name, "Test Plugin")
    
    def test_load_plugin(self):
        """Test plugin loading"""
        self.plugin_manager.discover_plugins()
        
        with patch('sys.path'), patch('importlib.util.spec_from_file_location'), \
             patch('importlib.util.module_from_spec'):
            
            # Mock the module loading
            mock_module = Mock()
            mock_plugin_class = Mock()
            mock_plugin_instance = Mock()
            mock_plugin_instance.get_name.return_value = "Test Plugin"
            mock_plugin_class.return_value = mock_plugin_instance
            mock_module.TestPlugin = mock_plugin_class
            
            with patch('importlib.util.spec_from_file_location') as mock_spec_from_file:
                mock_spec = Mock()
                mock_spec.loader = Mock()
                mock_spec_from_file.return_value = mock_spec
                
                with patch('importlib.util.module_from_spec', return_value=mock_module):
                    success = self.plugin_manager.load_plugin("Test Plugin")
                    self.assertTrue(success)
                    
                    # Verify plugin is loaded
                    plugin = self.plugin_manager.get_plugin("Test Plugin")
                    self.assertIsNotNone(plugin)
    
    def test_unload_plugin(self):
        """Test plugin unloading"""
        # First load a plugin
        self.plugin_manager.discover_plugins()
        self.plugin_manager._loaded_plugins["Test Plugin"] = Mock()
        
        success = self.plugin_manager.unload_plugin("Test Plugin")
        self.assertTrue(success)
        
        # Verify plugin is unloaded
        plugin = self.plugin_manager.get_plugin("Test Plugin")
        self.assertIsNone(plugin)
    
    def test_enable_disable_plugin(self):
        """Test enabling and disabling plugins"""
        self.plugin_manager.discover_plugins()
        
        # Test disable
        success = self.plugin_manager.disable_plugin("Test Plugin")
        self.assertTrue(success)
        
        descriptor = self.plugin_manager.get_plugin_descriptor("Test Plugin")
        self.assertFalse(descriptor.enabled)
        
        # Test enable
        success = self.plugin_manager.enable_plugin("Test Plugin")
        self.assertTrue(success)
        
        descriptor = self.plugin_manager.get_plugin_descriptor("Test Plugin")
        self.assertTrue(descriptor.enabled)


class TestPluginContext(unittest.TestCase):
    """Test plugin context"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.service_container = Mock()
        self.config_manager = Mock()
        self.main_window = Mock()
        
        self.context = PluginContext(
            self.service_container,
            self.config_manager,
            self.main_window
        )
    
    def test_service_access(self):
        """Test service access through context"""
        self.assertEqual(self.context.service_container, self.service_container)
        self.assertEqual(self.context.config_manager, self.config_manager)
        self.assertEqual(self.context.main_window, self.main_window)
    
    def test_get_service(self):
        """Test getting service by name"""
        mock_service = Mock()
        self.service_container.test_service = mock_service
        
        service = self.context.get_service("test_service")
        self.assertEqual(service, mock_service)
    
    def test_config_operations(self):
        """Test configuration operations"""
        self.config_manager.get_config.return_value = "test_value"
        
        value = self.context.get_config("test_section", "test_key")
        self.assertEqual(value, "test_value")
        
        self.context.set_config("test_section", "test_key", "new_value")
        self.config_manager.set_config.assert_called_with("test_section", "test_key", "new_value")
    
    def test_plugin_data_operations(self):
        """Test plugin data operations"""
        plugin_name = "test_plugin"
        
        # Test setting and getting plugin data
        self.context.set_plugin_data(plugin_name, "test_key", "test_value")
        value = self.context.get_plugin_data(plugin_name, "test_key")
        self.assertEqual(value, "test_value")
        
        # Test getting all plugin data
        all_data = self.context.get_plugin_data(plugin_name)
        self.assertEqual(all_data, {"test_key": "test_value"})
    
    def test_ui_operations(self):
        """Test UI operations"""
        self.main_window.add_plugin_menu_item = Mock()
        self.main_window.add_plugin_toolbar_button = Mock()
        self.main_window.add_plugin_panel = Mock()
        
        # Test adding menu item
        self.context.add_menu_item("File/Test", Mock(), "Test")
        self.main_window.add_plugin_menu_item.assert_called_once()
        
        # Test adding toolbar button
        self.context.add_toolbar_button("test_btn", Mock(), "Test", "icon")
        self.main_window.add_plugin_toolbar_button.assert_called_once()
        
        # Test adding panel
        self.context.add_panel("test_panel", Mock(), "Test Panel")
        self.main_window.add_plugin_panel.assert_called_once()


class TestPluginSecurity(unittest.TestCase):
    """Test plugin security"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.security = PluginSecurity()
    
    def test_plugin_permissions(self):
        """Test plugin permission management"""
        plugin_name = "test_plugin"
        permissions = {"read_config", "write_data"}
        
        self.security.set_plugin_permissions(plugin_name, permissions)
        retrieved = self.security.get_plugin_permissions(plugin_name)
        self.assertEqual(retrieved, permissions)
    
    def test_code_validation(self):
        """Test code validation"""
        plugin_name = "test_plugin"
        
        # Test safe code
        safe_code = "import json\ndata = {'key': 'value'}"
        violations = self.security.validate_plugin_code(plugin_name, safe_code)
        self.assertEqual(len(violations), 0)
        
        # Test unsafe code
        unsafe_code = "import os\nos.system('rm -rf /')"
        violations = self.security.validate_plugin_code(plugin_name, unsafe_code)
        self.assertGreater(len(violations), 0)
    
    def test_sandbox_creation(self):
        """Test sandbox creation"""
        plugin_name = "test_plugin"
        sandbox = self.security.create_sandbox(plugin_name)
        
        self.assertIn('__builtins__', sandbox)
        self.assertIn('__import__', sandbox)
        self.assertEqual(sandbox['__name__'], f'plugin_{plugin_name}')
    
    def test_execute_in_sandbox(self):
        """Test code execution in sandbox"""
        plugin_name = "test_plugin"
        sandbox = self.security.create_sandbox(plugin_name)
        
        # Test safe execution
        safe_code = "result = 2 + 2"
        result_sandbox = self.security.execute_in_sandbox(plugin_name, safe_code, sandbox)
        self.assertEqual(result_sandbox['result'], 4)
        
        # Test unsafe execution
        unsafe_code = "import os"
        with self.assertRaises(SecurityError):
            self.security.execute_in_sandbox(plugin_name, unsafe_code, sandbox)


class MockPlugin(PluginInterface):
    """Mock plugin for testing"""
    
    def __init__(self):
        self.initialized = False
    
    def get_name(self):
        return "Mock Plugin"
    
    def get_version(self):
        return "1.0.0"
    
    def get_description(self):
        return "Mock plugin for testing"
    
    def get_author(self):
        return "Test Author"
    
    def initialize(self, context):
        self.initialized = True
    
    def destroy(self):
        self.initialized = False
    
    def is_compatible(self, vcctl_version):
        return vcctl_version >= "1.0.0"


if __name__ == '__main__':
    unittest.main()
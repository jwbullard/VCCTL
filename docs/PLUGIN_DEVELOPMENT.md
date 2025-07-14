# VCCTL Plugin Development Guide

## Overview

The VCCTL Plugin Architecture allows developers to extend the functionality of the VCCTL (Virtual Cement and Concrete Testing Laboratory) application through a secure, modular plugin system. This guide provides comprehensive documentation for creating, testing, and deploying plugins.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Plugin Architecture](#plugin-architecture)
3. [Plugin Structure](#plugin-structure)
4. [Plugin Interface](#plugin-interface)
5. [Plugin Context](#plugin-context)
6. [Security Model](#security-model)
7. [UI Integration](#ui-integration)
8. [Configuration Management](#configuration-management)
9. [Testing Plugins](#testing-plugins)
10. [Deployment](#deployment)
11. [Examples](#examples)
12. [Best Practices](#best-practices)
13. [Troubleshooting](#troubleshooting)

## Getting Started

### Prerequisites

- Python 3.8+
- GTK 3.0+
- VCCTL application installed
- Basic understanding of Python and GTK

### Development Environment Setup

1. Clone the VCCTL repository
2. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```
3. Set up your plugin development directory:
   ```bash
   mkdir ~/.vcctl/plugins/my_plugin
   cd ~/.vcctl/plugins/my_plugin
   ```

## Plugin Architecture

The VCCTL plugin system is based on a modular architecture with the following components:

### Core Components

- **PluginInterface**: Base interface all plugins must implement
- **PluginManager**: Manages plugin discovery, loading, and lifecycle
- **PluginContext**: Provides access to VCCTL services and resources
- **PluginSecurity**: Handles security sandboxing and permissions
- **PluginDescriptor**: Metadata and configuration for plugins

### Plugin Lifecycle

1. **Discovery**: Plugin directories are scanned for `plugin.yml` files
2. **Validation**: Plugin descriptors are validated for correctness
3. **Loading**: Plugin modules are loaded and classes instantiated
4. **Initialization**: Plugins are initialized with context and resources
5. **Execution**: Plugins provide functionality through handlers and UI
6. **Destruction**: Plugins are cleaned up when unloaded

## Plugin Structure

Each plugin must follow this directory structure:

```
my_plugin/
├── plugin.yml          # Plugin descriptor (required)
├── plugin.py           # Main plugin module (required)
├── __init__.py         # Python package initialization (optional)
├── ui/                 # UI components (optional)
│   ├── dialogs.py
│   └── panels.py
├── resources/          # Resources (optional)
│   ├── icons/
│   └── data/
├── tests/              # Unit tests (recommended)
│   └── test_plugin.py
└── README.md           # Plugin documentation (recommended)
```

### Plugin Descriptor (plugin.yml)

The `plugin.yml` file contains metadata and configuration for your plugin:

```yaml
name: "My Plugin"
version: "1.0.0"
description: "Description of what the plugin does"
author: "Your Name"
main_class: "MyPlugin"
module_name: "plugin"
min_vcctl_version: "1.0.0"
max_vcctl_version: "2.0.0"
dependencies: []
python_dependencies: ["numpy", "pandas"]
enabled: true

properties:
  setting1: "default_value"
  setting2: 42

ui_components:
  menu_items:
    - path: "Tools/My Plugin..."
      callback: "show_dialog"
  toolbar_buttons:
    - id: "my_button"
      label: "My Button"
      icon: "my-icon"
      callback: "handle_click"

operation_handlers:
  my_operation: "handle_my_operation"

configuration_schema:
  type: object
  properties:
    setting1:
      type: string
    setting2:
      type: integer
```

## Plugin Interface

All plugins must implement the `PluginInterface` abstract base class:

```python
from plugins.plugin_interface import PluginInterface
from plugins.plugin_context import PluginContext

class MyPlugin(PluginInterface):
    def __init__(self):
        self.context = None
    
    def get_name(self) -> str:
        return "My Plugin"
    
    def get_version(self) -> str:
        return "1.0.0"
    
    def get_description(self) -> str:
        return "My plugin description"
    
    def get_author(self) -> str:
        return "Your Name"
    
    def initialize(self, context: PluginContext) -> None:
        self.context = context
        # Initialize plugin resources
        self.setup_ui()
        self.register_handlers()
    
    def destroy(self) -> None:
        # Clean up resources
        pass
    
    def is_compatible(self, vcctl_version: str) -> bool:
        return vcctl_version >= "1.0.0"
    
    def get_metadata(self) -> dict:
        return {
            "category": "analysis",
            "keywords": ["analysis", "data"],
            "license": "MIT"
        }
```

### Required Methods

- `get_name()`: Return plugin name
- `get_version()`: Return plugin version
- `get_description()`: Return plugin description
- `get_author()`: Return plugin author
- `initialize(context)`: Initialize plugin with context
- `destroy()`: Clean up plugin resources
- `is_compatible(vcctl_version)`: Check version compatibility

### Optional Methods

- `get_metadata()`: Return additional metadata
- `get_dependencies()`: Return plugin dependencies
- `get_ui_components()`: Return UI components
- `get_operation_handlers()`: Return operation handlers
- `get_configuration_schema()`: Return config schema

## Plugin Context

The `PluginContext` provides access to VCCTL services and resources:

```python
def initialize(self, context: PluginContext) -> None:
    self.context = context
    
    # Access services
    cement_service = context.get_service("cement_service")
    
    # Configuration management
    value = context.get_config("my_section", "my_key")
    context.set_config("my_section", "my_key", "new_value")
    
    # Plugin data storage
    context.set_plugin_data("my_plugin", "cache", {})
    cache = context.get_plugin_data("my_plugin", "cache")
    
    # UI integration
    context.add_menu_item("Tools/My Tool", self.show_dialog)
    context.add_toolbar_button("my_btn", self.handle_click, "My Button")
    context.add_panel("my_panel", self.create_panel(), "My Panel")
    
    # Show messages
    context.show_message("Plugin loaded successfully", "info")
```

## Security Model

The plugin system implements a comprehensive security model:

### Permissions

Plugins must declare required permissions:

```python
def get_required_permissions(self) -> set:
    return {
        'read_config',
        'write_data',
        'ui_access',
        'network_access'
    }
```

### Sandboxing

Plugins run in a restricted environment:

- Limited module imports
- Restricted file system access
- No system command execution
- Safe built-in functions only

### Code Validation

Plugin code is validated for security violations:

```python
# Restricted imports
import os          # ERROR: Restricted module
import subprocess  # ERROR: Restricted module

# Safe imports
import json        # OK
import yaml        # OK
import numpy       # OK
```

## UI Integration

### Menu Items

Add menu items to the main application:

```python
def initialize(self, context: PluginContext) -> None:
    context.add_menu_item(
        "Tools/My Analysis",
        self.show_analysis_dialog,
        "My Analysis Tool"
    )
```

### Toolbar Buttons

Add buttons to the toolbar:

```python
def initialize(self, context: PluginContext) -> None:
    context.add_toolbar_button(
        "analysis_btn",
        self.run_analysis,
        "Run Analysis",
        "analyze-icon"
    )
```

### Custom Panels

Create custom panels for the main window:

```python
def initialize(self, context: PluginContext) -> None:
    panel = self.create_analysis_panel()
    context.add_panel("analysis", panel, "Analysis")

def create_analysis_panel(self):
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk
    
    panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    label = Gtk.Label("Analysis Panel")
    panel.pack_start(label, False, False, 0)
    return panel
```

### Dialogs

Create custom dialogs:

```python
def show_dialog(self, *args):
    dialog = Gtk.Dialog(
        "My Dialog",
        self.context.main_window,
        0,
        (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
         Gtk.STOCK_OK, Gtk.ResponseType.OK)
    )
    
    content = dialog.get_content_area()
    label = Gtk.Label("Dialog content")
    content.pack_start(label, True, True, 0)
    
    dialog.show_all()
    response = dialog.run()
    dialog.destroy()
```

## Configuration Management

### Plugin Configuration

Define configuration schema in `plugin.yml`:

```yaml
configuration_schema:
  type: object
  properties:
    output_format:
      type: string
      enum: ["csv", "json", "xml"]
      default: "csv"
    max_iterations:
      type: integer
      minimum: 1
      maximum: 1000
      default: 100
    enable_logging:
      type: boolean
      default: true
```

### Accessing Configuration

```python
def get_output_format(self):
    return self.context.get_config("my_plugin", "output_format")

def set_output_format(self, format):
    self.context.set_config("my_plugin", "output_format", format)
```

## Testing Plugins

### Unit Tests

Create unit tests for your plugin:

```python
import unittest
from unittest.mock import Mock
from my_plugin.plugin import MyPlugin

class TestMyPlugin(unittest.TestCase):
    def setUp(self):
        self.plugin = MyPlugin()
        self.context = Mock()
    
    def test_plugin_info(self):
        self.assertEqual(self.plugin.get_name(), "My Plugin")
        self.assertEqual(self.plugin.get_version(), "1.0.0")
    
    def test_initialization(self):
        self.plugin.initialize(self.context)
        self.assertIsNotNone(self.plugin.context)
    
    def test_compatibility(self):
        self.assertTrue(self.plugin.is_compatible("1.0.0"))
        self.assertFalse(self.plugin.is_compatible("0.9.0"))
```

### Integration Tests

Test plugin integration with VCCTL:

```python
def test_plugin_loading(self):
    # Test plugin can be loaded by plugin manager
    manager = PluginManager([plugin_dir], service_container, config_manager, main_window)
    manager.discover_plugins()
    success = manager.load_plugin("My Plugin")
    self.assertTrue(success)
```

## Deployment

### Plugin Packaging

Create a plugin package:

```bash
# Create plugin archive
cd ~/.vcctl/plugins
zip -r my_plugin.zip my_plugin/
```

### Installation

Users can install plugins through:

1. **Plugin Manager UI**: Tools → Plugin Manager → Install Plugin
2. **Manual Installation**: Copy plugin directory to `~/.vcctl/plugins/`
3. **Command Line**: `vcctl plugin install my_plugin.zip`

## Examples

### Data Export Plugin

```python
class DataExportPlugin(PluginInterface):
    def get_name(self):
        return "Data Export"
    
    def initialize(self, context):
        self.context = context
        context.add_menu_item("File/Export Data", self.export_data)
    
    def export_data(self, *args):
        # Get data from application
        data = self.context.get_service("data_service").get_current_data()
        
        # Export to CSV
        import csv
        with open("export.csv", "w") as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        
        self.context.show_message("Data exported successfully", "info")
```

### Analysis Plugin

```python
class AnalysisPlugin(PluginInterface):
    def get_name(self):
        return "Custom Analysis"
    
    def initialize(self, context):
        self.context = context
        context.add_toolbar_button("analyze", self.run_analysis, "Analyze")
    
    def run_analysis(self, *args):
        # Get material data
        material_service = self.context.get_service("material_service")
        materials = material_service.get_all_materials()
        
        # Perform analysis
        results = self.analyze_materials(materials)
        
        # Display results
        self.show_results(results)
    
    def analyze_materials(self, materials):
        # Custom analysis logic
        return {"total_materials": len(materials)}
```

## Best Practices

### Code Organization

1. **Modular Design**: Split functionality into logical modules
2. **Clear Structure**: Follow the recommended directory structure
3. **Documentation**: Document all public methods and classes
4. **Error Handling**: Implement proper error handling and logging

### Performance

1. **Lazy Loading**: Load resources only when needed
2. **Efficient Algorithms**: Use efficient data structures and algorithms
3. **Memory Management**: Clean up resources in `destroy()` method
4. **Asynchronous Operations**: Use async/await for long-running tasks

### Security

1. **Minimal Permissions**: Request only necessary permissions
2. **Input Validation**: Validate all user inputs
3. **Safe Dependencies**: Use only trusted Python packages
4. **Secure File Operations**: Restrict file access to allowed directories

### User Experience

1. **Consistent UI**: Follow GTK design guidelines
2. **Helpful Messages**: Provide clear error messages and feedback
3. **Progressive Disclosure**: Show advanced options only when needed
4. **Keyboard Shortcuts**: Implement keyboard shortcuts for common actions

## Troubleshooting

### Common Issues

**Plugin Not Loading**
- Check `plugin.yml` syntax
- Verify all required fields are present
- Check Python syntax in plugin module
- Review plugin logs for errors

**Permission Denied**
- Check plugin permissions in configuration
- Verify file access permissions
- Review security sandbox restrictions

**UI Not Appearing**
- Check GTK version compatibility
- Verify UI component registration
- Check for widget initialization errors

**Configuration Issues**
- Validate configuration schema
- Check configuration file syntax
- Verify configuration section names

### Debugging

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.debug("Debug message")
```

### Getting Help

1. Check the VCCTL documentation
2. Review example plugins
3. Post questions on the VCCTL forums
4. Submit bug reports to GitHub

## API Reference

### PluginInterface Methods

```python
# Required methods
def get_name(self) -> str
def get_version(self) -> str
def get_description(self) -> str
def get_author(self) -> str
def initialize(self, context: PluginContext) -> None
def destroy(self) -> None
def is_compatible(self, vcctl_version: str) -> bool

# Optional methods
def get_metadata(self) -> Dict[str, Any]
def get_dependencies(self) -> List[str]
def get_ui_components(self) -> Dict[str, Any]
def get_operation_handlers(self) -> Dict[str, Any]
def get_configuration_schema(self) -> Dict[str, Any]
```

### PluginContext Methods

```python
# Service access
def get_service(self, service_name: str) -> Any

# Configuration
def get_config(self, section: str, key: str = None) -> Any
def set_config(self, section: str, key: str, value: Any) -> None

# Plugin data
def get_plugin_data(self, plugin_name: str, key: str = None) -> Any
def set_plugin_data(self, plugin_name: str, key: str, value: Any) -> None

# UI integration
def add_menu_item(self, menu_path: str, callback, label: str = None) -> None
def add_toolbar_button(self, button_id: str, callback, label: str, icon: str = None) -> None
def add_panel(self, panel_id: str, panel_widget, title: str) -> None
def show_message(self, message: str, message_type: str = 'info') -> None
```

## Version History

- **1.0.0**: Initial plugin architecture implementation
- **1.1.0**: Added security sandboxing and permissions
- **1.2.0**: Enhanced UI integration capabilities
- **1.3.0**: Added configuration management and validation

## License

This plugin development guide is released under the MIT License. Plugin developers are free to use any license for their individual plugins.
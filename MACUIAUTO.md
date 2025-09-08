# PyAtom/ATOMac and macOS UI Automation Guide

**Summary of macOS UI automation options for testing GTK applications**

Generated: September 7, 2025

---

## What PyAtom/ATOMac Does

**PyAtom/ATOMac** is a Python library for automated testing on macOS that provides programmatic access to GUI applications through Apple's **Accessibility API**. It allows you to:

- **Control native macOS applications** written in Cocoa/AppKit frameworks  
- **Find UI elements** by accessibility attributes (buttons, text fields, menus, etc.)
- **Simulate user interactions** (clicks, typing, window manipulation)
- **Read application state** (text content, window titles, element properties)
- **Navigate UI hierarchies** with search methods and recursive queries
- **Write cross-platform tests** (compatible with LDTP for Linux/Windows)

## Key Features

- **Fast and direct API access** - No screenshot/image recognition needed
- **Rich search capabilities** - Find elements by role, title, description, etc.
- **Attribute read/write** - Get and set most accessibility properties
- **Bundle ID integration** - Target applications by their bundle identifiers
- **Hierarchical navigation** - Search direct children or recursive descendants

## System Requirements

- **macOS** (tested on 10.6-10.8, should work on modern versions including Sequoia)
- **Xcode** installed for compilation
- **Accessibility enabled**: System Preferences → Security & Privacy → Privacy → Accessibility → Enable for your terminal/Python

**Important**: You must enable accessibility access for your terminal or Python environment, otherwise you'll get `ErrorAPIDisabled` exceptions.

## Installation Options

### Original PyAtom/ATOMac (Legacy)
```bash
pip install pyatomac  # Version 2.0.7 (last updated 2013)
```

**Status**: Outdated, Python 2 era, not recommended for new projects

### Modern Alternatives (Recommended for 2024)

#### Option 1: Atomacos (Python 3 Fork)
```bash
pip install atomacos
```
- **Status**: Active Python 3 compatible fork
- **Recommended**: Best maintained option
- **Docs**: https://daveenguyen.github.io/atomacos/

#### Option 2: MacUIAuto (Latest)  
```bash
pip install macuiauto  # Released August 2024
```
- **Status**: Newest alternative released in 2024
- **Note**: Less documentation available

## Basic Usage Example

```python
import atomac  # or: import atomacos as atomac

# Get application by bundle ID
app = atomac.getAppRefByBundleId('com.yourcompany.vcctl')

# Find windows
windows = app.windows()
main_window = windows[0]

# Find UI elements
buttons = main_window.buttons()
material_button = main_window.findFirst('AXButton', title='Materials')

# Interact with elements
material_button.click()

# Get text content
text_field = main_window.findFirst('AXTextField')
current_text = text_field.value
text_field.setValue('new text')
```

## Search Methods

- **Direct children**: `windows()`, `buttons()`, `textFields()`
- **Recursive search**: `windowsR()`, `buttonsR()`, `textFieldsR()`
- **Find by criteria**: `findFirst()`, `findFirstR()` with accessibility attributes

## Accessibility Attributes

Common attributes you can search by and modify:
- `title` - Button text, window titles
- `value` - Text field contents, slider values  
- `role` - UI element type (AXButton, AXTextField, etc.)
- `enabled` - Whether element is interactive
- `focused` - Which element has focus

## Learning Resources

### Documentation
- **Atomacos Docs**: https://daveenguyen.github.io/atomacos/
- **PyPI Package**: https://pypi.org/project/pyatomac/

### GitHub Repositories
- **Original**: https://github.com/pyatom/pyatom
- **Python 3 Fork**: https://github.com/daveenguyen/atomacos  
- **Usage Examples**: https://github.com/vijayanandrp/Mac-OSX-App-UI-Automation-Testing

### Community Support
- **Stack Overflow**: Search "pyatom" tag for common issues and solutions
- **Tutorial**: "Simple Automation using Python - Atomac in Mac OS X" blog post

## GTK Application Considerations

**Important for VCCTL**: Since your application uses GTK rather than native Cocoa frameworks:

### Potential Limitations
- **Accessibility support**: GTK accessibility on macOS may be limited compared to native apps
- **Element detection**: Some GTK widgets might not expose standard accessibility attributes
- **Bundle ID**: GTK apps may not have proper bundle identifiers

### Testing Strategy
1. **Start with simple tests**: Try detecting your application window first
2. **Check accessibility**: Verify GTK widgets are discoverable through accessibility API
3. **Fallback options**: If ATOMac doesn't work well, consider PyAutoGUI as alternative

## Recommendation for VCCTL

For testing your GTK-based VCCTL application on macOS Sequoia:

1. **Primary choice**: Try **`atomacos`** first (most mature, Python 3 compatible)
2. **Alternative**: If atomacos has GTK compatibility issues, try **`macuiauto`** 
3. **Fallback**: If accessibility approach fails, consider PyAutoGUI for image-based automation

## Quick Start Command

```bash
# Install the recommended option
pip install atomacos

# Enable accessibility (required!)
# System Preferences → Security & Privacy → Privacy → Accessibility → Add Terminal/Python
```

---

**Next Steps**: Install atomacos and test basic application detection with your VCCTL GTK application to verify compatibility before building full automation scripts.
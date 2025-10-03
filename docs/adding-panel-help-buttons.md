# Adding Context-Specific Help Buttons to Panels

## Overview

This guide explains how to add context-specific help buttons to VCCTL panel headers. These buttons open the relevant documentation section in the user's browser when clicked.

## What's Already Complete

✅ **Help buttons added to:**
- Materials Panel (`materials_panel.py`)
- Mix Design Panel (`mix_design_panel.py`)
- Hydration Panel (`hydration_panel.py`)

## Remaining Panels to Update

The following panels still need help buttons added:

1. **Elastic Moduli Panel** (`elastic_moduli_panel.py`)
2. **Results Panel** (`results_panel.py`)
3. **Operations Monitoring Panel** (`operations_monitoring_panel.py`)
4. **Microstructure Panel** (`microstructure_panel.py`)
5. **File Management Panel** (`file_management_panel.py`)
6. **Aggregate Panel** (`aggregate_panel.py`)

## Implementation Steps

### Step 1: Add Import Statement

At the top of the panel file, add this import after the existing `app.utils.icon_utils` import:

```python
from app.help.panel_help_button import create_panel_help_button
```

**Example location in file:**
```python
from app.utils.icon_utils import create_icon_image
from app.help.panel_help_button import create_panel_help_button  # <-- Add this line
```

### Step 2: Add Help Button to Header

Find the section where the panel title is created (usually in `_create_header()` method). Look for code like:

```python
title_label = Gtk.Label()
title_label.set_markup('<span size="large" weight="bold">Panel Name</span>')
title_label.set_halign(Gtk.Align.START)
title_box.pack_start(title_label, False, False, 0)
```

**Add these lines immediately after the title label:**

```python
# Add context-specific help button
help_button = create_panel_help_button('PanelClassName', self.main_window)
title_box.pack_start(help_button, False, False, 5)

header_box.pack_start(title_box, False, False, 0)
```

**Important:** Make sure the `header_box.pack_start(title_box, ...)` line exists after adding the help button. This line adds the title_box (containing both title and help button) to the header_box.

Replace `'PanelClassName'` with the actual class name of the panel (see table below).

## Panel Class Name Reference

| Panel File | Class Name | Documentation URL (already mapped) |
|------------|------------|-----------------------------------|
| `elastic_moduli_panel.py` | `ElasticModuliPanel` | `user-guide/elastic-calculations/index.html` |
| `results_panel.py` | `ResultsPanel` | `user-guide/results-visualization/index.html` |
| `operations_monitoring_panel.py` | `OperationsMonitoringPanel` | `user-guide/operations-monitoring/index.html` |
| `microstructure_panel.py` | `MicrostructurePanel` | `user-guide/mix-design/index.html` |
| `file_management_panel.py` | `FileManagementPanel` | `getting-started/index.html` |
| `aggregate_panel.py` | `AggregatePanel` | `user-guide/materials-management/index.html` |

## Complete Example: Elastic Moduli Panel

### Before:
```python
# In elastic_moduli_panel.py

from app.utils.icon_utils import create_icon_image

# ... other code ...

def _create_header(self):
    """Create panel header."""
    header_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)

    title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

    title_label = Gtk.Label()
    title_label.set_markup('<span size="large" weight="bold">Elastic Moduli Calculation</span>')
    title_label.set_halign(Gtk.Align.START)
    title_box.pack_start(title_label, False, False, 0)

    # ... rest of header code ...
```

### After:
```python
# In elastic_moduli_panel.py

from app.utils.icon_utils import create_icon_image
from app.help.panel_help_button import create_panel_help_button  # <-- ADDED

# ... other code ...

def _create_header(self):
    """Create panel header."""
    header_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)

    title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

    title_label = Gtk.Label()
    title_label.set_markup('<span size="large" weight="bold">Elastic Moduli Calculation</span>')
    title_label.set_halign(Gtk.Align.START)
    title_box.pack_start(title_label, False, False, 0)

    # Add context-specific help button                              # <-- ADDED
    help_button = create_panel_help_button('ElasticModuliPanel', self.main_window)  # <-- ADDED
    title_box.pack_start(help_button, False, False, 5)            # <-- ADDED

    header_box.pack_start(title_box, False, False, 0)             # <-- ADDED (IMPORTANT!)

    # ... rest of header code ...
```

## Quick Reference for Each Panel

### 1. Elastic Moduli Panel

**File:** `src/app/windows/panels/elastic_moduli_panel.py`

**Import to add:**
```python
from app.help.panel_help_button import create_panel_help_button
```

**Code to add after title label:**
```python
# Add context-specific help button
help_button = create_panel_help_button('ElasticModuliPanel', self.main_window)
title_box.pack_start(help_button, False, False, 5)

header_box.pack_start(title_box, False, False, 0)  # IMPORTANT: Add title_box to header_box
```

---

### 2. Results Panel

**File:** `src/app/windows/panels/results_panel.py`

**Import to add:**
```python
from app.help.panel_help_button import create_panel_help_button
```

**Code to add after title label:**
```python
# Add context-specific help button
help_button = create_panel_help_button('ResultsPanel', self.main_window)
title_box.pack_start(help_button, False, False, 5)

header_box.pack_start(title_box, False, False, 0)  # IMPORTANT: Add title_box to header_box
```

---

### 3. Operations Monitoring Panel

**File:** `src/app/windows/panels/operations_monitoring_panel.py`

**Import to add:**
```python
from app.help.panel_help_button import create_panel_help_button
```

**Code to add after title label:**
```python
# Add context-specific help button
help_button = create_panel_help_button('OperationsMonitoringPanel', self.main_window)
title_box.pack_start(help_button, False, False, 5)

header_box.pack_start(title_box, False, False, 0)  # IMPORTANT: Add title_box to header_box
```

---

### 4. Microstructure Panel

**File:** `src/app/windows/panels/microstructure_panel.py`

**Import to add:**
```python
from app.help.panel_help_button import create_panel_help_button
```

**Code to add after title label:**
```python
# Add context-specific help button
help_button = create_panel_help_button('MicrostructurePanel', self.main_window)
title_box.pack_start(help_button, False, False, 5)

header_box.pack_start(title_box, False, False, 0)  # IMPORTANT: Add title_box to header_box
```

---

### 5. File Management Panel

**File:** `src/app/windows/panels/file_management_panel.py`

**Import to add:**
```python
from app.help.panel_help_button import create_panel_help_button
```

**Code to add after title label:**
```python
# Add context-specific help button
help_button = create_panel_help_button('FileManagementPanel', self.main_window)
title_box.pack_start(help_button, False, False, 5)

header_box.pack_start(title_box, False, False, 0)  # IMPORTANT: Add title_box to header_box
```

---

### 6. Aggregate Panel

**File:** `src/app/windows/panels/aggregate_panel.py`

**Import to add:**
```python
from app.help.panel_help_button import create_panel_help_button
```

**Code to add after title label:**
```python
# Add context-specific help button
help_button = create_panel_help_button('AggregatePanel', self.main_window)
title_box.pack_start(help_button, False, False, 5)

header_box.pack_start(title_box, False, False, 0)  # IMPORTANT: Add title_box to header_box
```

---

## Testing

After adding help buttons to a panel:

1. Start VCCTL: `./run_vcctl.sh`
2. Navigate to the panel you modified
3. Look for a small "?" icon button next to the panel title
4. Click the help button
5. Verify it opens the correct documentation page in your browser

## Troubleshooting

### Help button doesn't appear
- Check that you imported `create_panel_help_button` correctly
- Verify you're using the exact panel class name (case-sensitive)
- Make sure `self.main_window` is available in the scope

### Wrong documentation page opens
- Verify the panel class name matches exactly (see reference table)
- Check `src/app/help/panel_help_button.py` for the correct URL mapping

### Import error
- Ensure `src/app/help/panel_help_button.py` exists
- Check that the import path is correct relative to the panel file

## Additional Notes

- The help button uses the `help-about` icon (GTK standard icon)
- Button has no relief (flat appearance) to blend with header
- Tooltip shows "Open [Panel Name] documentation"
- All documentation URLs are pre-mapped in `panel_help_button.py`

## Related Files

- **Help button widget:** `src/app/help/panel_help_button.py`
- **Documentation viewer:** `src/app/help/documentation_viewer.py`
- **Built documentation:** `vcctl-docs/site/`

## Future Additions

If you create a new panel in the future:

1. Add entry to `PANEL_DOCUMENTATION_MAP` in `src/app/help/panel_help_button.py`:
   ```python
   'YourNewPanel': 'path/to/documentation/index.html',
   ```

2. Add entry to `_get_panel_display_name()` in same file:
   ```python
   'YourNewPanel': 'Your Panel Display Name',
   ```

3. Follow the steps above to add the help button to your panel's header

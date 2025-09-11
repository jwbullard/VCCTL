#!/usr/bin/env python3
"""Test shape loading logic to verify it works correctly."""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

# Create a test combo box
combo = Gtk.ComboBoxText()

# Add test items (simulating what microstructure_service does)
test_shapes = {
    "sphere": "Spherical particles",
    "cement140": "Cement140 particles",
    "sacci425": "Sacci425 particles",
    "cement141": "Cement141 particles",
}

for shape_id, shape_desc in test_shapes.items():
    combo.append(shape_id, shape_desc)

# Test 1: Verify we can find items by ID
print("Test 1: Finding items by ID")
for test_id in ["sacci425", "cement140", "sphere"]:
    found = False
    for i in range(combo.get_model().iter_n_children(None)):
        combo.set_active(i)
        active_id = combo.get_active_id()
        print(f"  Index {i}: active_id='{active_id}'")
        if active_id == test_id:
            found = True
            print(f"  ✓ Found '{test_id}' at index {i}")
            break
    if not found:
        print(f"  ✗ Could not find '{test_id}'")

# Test 2: Check what get_active_id returns after setting
print("\nTest 2: Checking get_active_id after append")
combo.set_active(0)
print(f"  After set_active(0): get_active_id() = '{combo.get_active_id()}'")
combo.set_active(2)
print(f"  After set_active(2): get_active_id() = '{combo.get_active_id()}'")

print("\nTest complete!")
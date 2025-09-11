#!/usr/bin/env python3
"""Test aggregate shape loading to see if there's something special about them."""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

# Test with aggregate shapes
combo = Gtk.ComboBoxText()

# First add "sphere" as aggregates always have this
combo.append("sphere", "Spherical particles")

# Add some test aggregate shapes
test_aggregates = [
    "MA117A-4-fine",
    "LS-coarse",
    "MA106A-1-fine",
    "AZ-coarse"
]

for agg_id in test_aggregates:
    # Simulate what the service does
    combo.append(agg_id, f"{agg_id.title()} aggregate")

print(f"Total items in combo: {combo.get_model().iter_n_children(None)}")

# Test finding aggregates
for test_id in ["MA117A-4-fine", "LS-coarse"]:
    print(f"\nLooking for: '{test_id}'")
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
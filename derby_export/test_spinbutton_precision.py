#!/usr/bin/env python3
"""
Test SpinButton precision for cement136 values
"""

import gi
gi.require_version('Gtk', '3.0')
from Gtk import SpinButton

# Create spin buttons like in the dialog
def test_spinbutton_precision():
    print("Testing GTK SpinButton precision with cement136 values")
    
    # Raw database values for cement136 (as fractions 0-1)
    raw_values = {
        'C3S': 0.652971876768900,
        'C2S': 0.187900705359230,
        'C3A': 0.045234252794746,
        'C4AF': 0.113893165077123,
        'K2SO4': 0.0,
        'Na2SO4': 0.0
    }
    
    print("\nConverting to percentages and setting in SpinButtons:")
    
    spins = {}
    total_from_spins = 0.0
    
    for phase, fraction in raw_values.items():
        # Convert to percentage as done in the dialog
        percentage = float(fraction) * 100.0 if fraction else 0.0
        
        # Create spin button as configured in dialog
        spin = SpinButton.new_with_range(0.0, 100.0, 0.1)
        spin.set_digits(1)  # This is the key setting
        spin.set_value(percentage)
        
        spins[phase] = spin
        
        # Get the value back from the spin button
        displayed_value = spin.get_value()
        total_from_spins += displayed_value
        
        print(f"{phase}: {fraction:.15f} -> {percentage:.15f}% -> SpinButton: {displayed_value:.1f}%")
    
    print(f"\nTotal from SpinButton values: {total_from_spins:.1f}%")
    
    # Also test the direct calculation method
    print(f"\nDirect calculation check:")
    direct_total = sum(float(frac) * 100.0 for frac in raw_values.values() if frac)
    print(f"Direct total: {direct_total:.15f}%")
    print(f"Direct total rounded: {direct_total:.1f}%")

if __name__ == "__main__":
    test_spinbutton_precision()
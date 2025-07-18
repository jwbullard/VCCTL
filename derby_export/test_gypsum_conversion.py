#!/usr/bin/env python3
"""
Test script to verify gypsum mass/volume fraction bidirectional conversion logic.
"""

# Gypsum component specific gravities (g/cm³)
GYPSUM_SPECIFIC_GRAVITIES = {
    'dihyd': 2.32,   # Dihydrate (CaSO4·2H2O)
    'hemihyd': 2.74, # Hemihydrate (CaSO4·0.5H2O)
    'anhyd': 2.61    # Anhydrite (CaSO4)
}

def mass_to_volume_conversion(mass_fraction, gypsum_type, cement_bulk_sg=3.15):
    """Convert mass fraction to volume fraction."""
    sg_gypsum = GYPSUM_SPECIFIC_GRAVITIES[gypsum_type]
    volume_fraction = (mass_fraction / sg_gypsum) * cement_bulk_sg
    return volume_fraction

def volume_to_mass_conversion(volume_fraction, gypsum_type, cement_bulk_sg=3.15):
    """Convert volume fraction to mass fraction."""
    sg_gypsum = GYPSUM_SPECIFIC_GRAVITIES[gypsum_type]
    mass_fraction = (volume_fraction / cement_bulk_sg) * sg_gypsum
    return mass_fraction

def test_bidirectional_conversion():
    """Test that mass->volume->mass and volume->mass->volume are consistent."""
    
    print("Testing bidirectional gypsum fraction conversion...")
    print(f"Using cement bulk SG: 3.15")
    print(f"Gypsum SGs: {GYPSUM_SPECIFIC_GRAVITIES}")
    print()
    
    # Test with some known values from cement151
    test_cases = [
        ('dihyd', 0.013),    # cement151 dihydrate
        ('hemihyd', 0.032),  # cement151 hemihydrate  
        ('anhyd', 0.001),    # cement151 anhydrite
        ('dihyd', 0.0434),   # cement115 dihydrate
        ('hemihyd', 0.046),  # cement16130 hemihydrate
        ('anhyd', 0.098),    # cement133 anhydrite
    ]
    
    print("Testing mass -> volume -> mass conversion:")
    for gypsum_type, original_mass in test_cases:
        # Mass to volume
        volume_frac = mass_to_volume_conversion(original_mass, gypsum_type)
        
        # Volume back to mass
        converted_mass = volume_to_mass_conversion(volume_frac, gypsum_type)
        
        # Check if we get back the original value
        error = abs(original_mass - converted_mass)
        
        print(f"  {gypsum_type:7s}: {original_mass:.4f} -> {volume_frac:.4f} -> {converted_mass:.4f} (error: {error:.6f})")
    
    print()
    print("Testing volume -> mass -> volume conversion:")
    
    # Test starting with volume fractions
    test_volume_cases = [
        ('dihyd', 0.0177),   # cement151 calculated volume
        ('hemihyd', 0.0368), # cement151 calculated volume
        ('anhyd', 0.0012),   # cement151 calculated volume
    ]
    
    for gypsum_type, original_volume in test_volume_cases:
        # Volume to mass
        mass_frac = volume_to_mass_conversion(original_volume, gypsum_type)
        
        # Mass back to volume
        converted_volume = mass_to_volume_conversion(mass_frac, gypsum_type)
        
        # Check if we get back the original value
        error = abs(original_volume - converted_volume)
        
        print(f"  {gypsum_type:7s}: {original_volume:.4f} -> {mass_frac:.4f} -> {converted_volume:.4f} (error: {error:.6f})")

if __name__ == "__main__":
    test_bidirectional_conversion()
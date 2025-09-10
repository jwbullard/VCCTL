#!/usr/bin/env python3
"""
Test script for Mass Fraction Converter Service

Validates all conversion functions using TestMortar-01 data as a test case.
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from app.services.mass_fraction_converter import MassFractionConverter, Component, MaterialType

def test_mass_fraction_converter():
    """Test the mass fraction converter with TestMortar-01 data."""
    
    print("🧪 Testing Mass Fraction Converter")
    print("=" * 50)
    
    # Create converter instance
    converter = MassFractionConverter()
    
    # Test data from TestMortar-01 (corrupted data that sums to 1.133333)
    test_components = [
        Component(
            material_name="cement140",
            material_type=MaterialType.CEMENT,
            mass_fraction=0.31,  # Type 3 (corrupted)
            specific_gravity=3.15
        ),
        Component(
            material_name="NormalLimestone", 
            material_type=MaterialType.LIMESTONE,
            mass_fraction=0.023333333333333334,  # Type 3 (corrupted)
            specific_gravity=3.15
        ),
        Component(
            material_name="MA114F-3-fine",
            material_type=MaterialType.AGGREGATE, 
            mass_fraction=0.6666666666666666,  # Type 3 (corrupted)
            specific_gravity=2.65
        ),
        Component(
            material_name="Water",
            material_type=MaterialType.WATER,
            mass_fraction=0.13333333333333333,  # Type 3 (corrupted) 
            specific_gravity=1.0
        )
    ]
    
    # Verify the test data is corrupted (sums > 1.0)
    total_input = sum(c.mass_fraction for c in test_components)
    print(f"✅ Input data validation:")
    print(f"   Total mass fractions: {total_input:.6f} (should be corrupted)")
    print(f"   Expected: 1.133333 (corrupted TestMortar-01 data)")
    print()
    
    # Test 1: Normalize to Type 3
    print("🔧 Test 1: Normalize to Type 3")
    normalized_components = converter.normalize_to_type3(test_components)
    
    total_normalized = sum(c.mass_fraction for c in normalized_components)
    print(f"   Normalized total: {total_normalized:.6f}")
    print(f"   Expected: 1.000000")
    
    if abs(total_normalized - 1.0) < 1e-6:
        print("   ✅ PASS: Type 3 normalization successful")
    else:
        print("   ❌ FAIL: Type 3 normalization failed")
        return False
    
    print()
    
    # Test 2: Type 3 → Type 2 conversion
    print("🔧 Test 2: Type 3 → Type 2 Mass Fractions")
    type2_mass = converter.type3_to_type2_mass_fractions(normalized_components)
    
    type2_total = sum(type2_mass.values())
    print(f"   Type 2 total: {type2_total:.6f}")
    print(f"   Expected: 1.000000")
    print(f"   Components: {len(type2_mass)} (should be binder only)")
    
    for name, frac in type2_mass.items():
        print(f"     {name}: {frac:.6f}")
    
    if abs(type2_total - 1.0) < 1e-6 and len(type2_mass) == 3:  # cement, limestone, water
        print("   ✅ PASS: Type 2 conversion successful")
    else:
        print("   ❌ FAIL: Type 2 conversion failed")
        return False
    
    print()
    
    # Test 3: Type 2 → Type 1 conversion  
    print("🔧 Test 3: Type 2 → Type 1 Mass Fractions")
    type1_mass = converter.type2_to_type1_mass_fractions(normalized_components, type2_mass)
    
    type1_total = sum(type1_mass.values())
    print(f"   Type 1 total: {type1_total:.6f}")
    print(f"   Expected: 1.000000")
    print(f"   Components: {len(type1_mass)} (should be powders only)")
    
    for name, frac in type1_mass.items():
        print(f"     {name}: {frac:.6f}")
    
    if abs(type1_total - 1.0) < 1e-6 and len(type1_mass) == 2:  # cement, limestone only
        print("   ✅ PASS: Type 1 conversion successful")
    else:
        print("   ❌ FAIL: Type 1 conversion failed")
        return False
    
    print()
    
    # Test 4: Mass → Volume conversions
    print("🔧 Test 4: Mass → Volume Fraction Conversions")
    
    # Type 2 volume fractions (binder)
    binder_components = [c for c in normalized_components if c.is_powder or c.is_water]
    type2_volume = converter.mass_to_volume_fractions(type2_mass, binder_components)
    
    type2_vol_total = sum(type2_volume.values())
    print(f"   Type 2 volume total: {type2_vol_total:.6f}")
    
    for name, frac in type2_volume.items():
        print(f"     {name}: {frac:.6f}")
    
    # Type 1 volume fractions (powders)
    powder_components = [c for c in normalized_components if c.is_powder]
    type1_volume = converter.mass_to_volume_fractions(type1_mass, powder_components)
    
    type1_vol_total = sum(type1_volume.values())
    print(f"   Type 1 volume total: {type1_vol_total:.6f}")
    
    for name, frac in type1_volume.items():
        print(f"     {name}: {frac:.6f}")
    
    if abs(type2_vol_total - 1.0) < 1e-6 and abs(type1_vol_total - 1.0) < 1e-6:
        print("   ✅ PASS: Volume fraction conversions successful")
    else:
        print("   ❌ FAIL: Volume fraction conversions failed")
        return False
    
    print()
    
    # Test 5: Full genmic.c conversion
    print("🔧 Test 5: Complete genmic.c Conversion")
    genmic_type2, genmic_type1 = converter.convert_for_genmic(normalized_components)
    
    if not genmic_type2 or not genmic_type1:
        print("   ❌ FAIL: genmic conversion returned empty results")
        return False
    
    solid_frac = genmic_type2['binder_solid_volume_fraction'] 
    water_frac = genmic_type2['binder_water_volume_fraction']
    powder_fracs = genmic_type1['powder_volume_fractions']
    
    print(f"   Binder solid volume fraction: {solid_frac:.6f}")
    print(f"   Binder water volume fraction: {water_frac:.6f}")
    print(f"   Total (solid + water): {solid_frac + water_frac:.6f}")
    print(f"   Powder components: {len(powder_fracs)}")
    
    powder_total = sum(powder_fracs.values())
    print(f"   Powder volume fractions total: {powder_total:.6f}")
    
    for name, frac in powder_fracs.items():
        print(f"     {name}: {frac:.6f}")
    
    # Validation
    genmic_valid = (
        abs((solid_frac + water_frac) - 1.0) < 1e-6 and
        abs(powder_total - 1.0) < 1e-6
    )
    
    if genmic_valid:
        print("   ✅ PASS: genmic.c conversion successful")
    else:
        print("   ❌ FAIL: genmic.c conversion failed")
        return False
    
    print()
    
    # Test 6: Validation functions
    print("🔧 Test 6: Validation Functions")
    
    # Test corrupted data validation
    is_valid, error = converter.validate_mass_fractions(test_components, "Type 3")
    print(f"   Corrupted data validation: {'PASS' if not is_valid else 'FAIL'}")
    print(f"   Error message: {error}")
    
    # Test normalized data validation
    is_valid, error = converter.validate_mass_fractions(normalized_components, "Type 3")
    print(f"   Normalized data validation: {'PASS' if is_valid else 'FAIL'}")
    print(f"   Result: {error}")
    
    print()
    print("🎉 All Mass Fraction Converter tests PASSED!")
    return True

if __name__ == "__main__":
    try:
        success = test_mass_fraction_converter()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
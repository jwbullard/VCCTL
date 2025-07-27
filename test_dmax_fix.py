#!/usr/bin/env python3
"""
Test D_max Fix with Logarithmic Binning

Verify that D_max parameter correctly limits diameter range
with the new logarithmic binning system.
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from app.services.psd_service import PSDService, PSDParameters, PSDType

def test_dmax_fix():
    """Test that D_max parameter works correctly with logarithmic bins."""
    print("🔧 Testing D_max Fix with Logarithmic Binning")
    print("=" * 50)
    
    service = PSDService()
    
    # Test different D_max values with Rosin-Rammler
    test_cases = [
        ("D_max = 20 μm", 20.0),
        ("D_max = 40 μm", 40.0),
        ("D_max = 60 μm", 60.0),  # Jeff's specific case
    ]
    
    for test_name, dmax_value in test_cases:
        print(f"\n🎯 {test_name}")
        print("-" * 30)
        
        params = PSDParameters(
            psd_type=PSDType.ROSIN_RAMMLER,
            d50=15.0,
            n=1.4,
            dmax=dmax_value
        )
        
        distribution = service.convert_to_discrete(params)
        
        max_diameter_in_table = max(distribution.diameters)
        num_bins = len(distribution.points)
        
        print(f"Expected max: {dmax_value} μm")
        print(f"Actual max:   {max_diameter_in_table} μm")
        print(f"Number of bins: {num_bins}")
        
        if max_diameter_in_table == dmax_value:
            print("✅ PASS: D_max correctly limits table")
        else:
            print("❌ FAIL: D_max not working correctly")
        
        # Show last few bins
        print("Last 3 bins:")
        for diameter, mass_fraction in distribution.points[-3:]:
            percentage = mass_fraction * 100
            print(f"  {diameter:3.0f} μm: {percentage:5.2f}%")
    
    # Test the logarithmic bins generation directly
    print(f"\n\n🔍 Direct Logarithmic Bins Test:")
    print("-" * 40)
    
    for dmax in [20, 40, 60]:
        bins = service._generate_logarithmic_bins(dmax)
        max_bin = max(bins)
        print(f"D_max = {dmax:2.0f} → Bins: {bins}")
        print(f"           Max bin: {max_bin} (should be {dmax})")
        if max_bin == dmax:
            print(f"           ✅ Correct")
        else:
            print(f"           ❌ Wrong!")
        print()

if __name__ == "__main__":
    test_dmax_fix()
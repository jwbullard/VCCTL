#!/usr/bin/env python3
"""
Test D_max Parameter Behavior

This script tests that D_max parameter correctly limits the diameter range
in the generated table.
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from app.services.psd_service import PSDService, PSDParameters, PSDType

def test_dmax_behavior():
    """Test that D_max parameter correctly limits diameter range."""
    print("🧪 Testing D_max Parameter Behavior")
    print("=" * 50)
    
    service = PSDService()
    
    # Test Rosin-Rammler with different D_max values
    test_cases = [
        ("D_max = 20 μm", 20.0),
        ("D_max = 40 μm", 40.0),
        ("D_max = 60 μm", 60.0),
    ]
    
    for test_name, dmax_value in test_cases:
        print(f"\n🔍 TEST: {test_name}")
        print(f"   Rosin-Rammler: d50=15.0, n=1.4, dmax={dmax_value}")
        
        params = PSDParameters(
            psd_type=PSDType.ROSIN_RAMMLER,
            d50=15.0,
            n=1.4,
            dmax=dmax_value
        )
        
        distribution = service.convert_to_discrete(params)
        
        max_diameter = max(distribution.diameters)
        num_bins = len(distribution.points)
        
        print(f"   ✅ Generated {num_bins} bins")
        print(f"   ✅ Maximum diameter in table: {max_diameter} μm")
        print(f"   ✅ Expected maximum: {dmax_value} μm")
        
        if max_diameter <= dmax_value:
            print(f"   ✅ PASS: Table respects D_max limit")
        else:
            print(f"   ❌ FAIL: Table exceeds D_max limit!")
        
        # Show last few bins
        print(f"   Last 3 bins:")
        for diameter, mass_fraction in distribution.points[-3:]:
            percentage = mass_fraction * 100
            print(f"      {diameter:3.0f} μm: {percentage:5.2f}%")
    
    # Test log-normal (should use default max_diameter = 75)
    print(f"\n🔍 TEST: Log-Normal (no D_max specified)")
    print(f"   Log-Normal: median=10.0, sigma=2.0")
    
    params = PSDParameters(
        psd_type=PSDType.LOG_NORMAL,
        median=10.0,
        sigma=2.0
    )
    
    distribution = service.convert_to_discrete(params)
    max_diameter = max(distribution.diameters)
    num_bins = len(distribution.points)
    
    print(f"   ✅ Generated {num_bins} bins")
    print(f"   ✅ Maximum diameter: {max_diameter} μm")
    print(f"   ✅ Uses default max_diameter = {service.max_diameter} μm")
    
    # Test Fuller-Thompson with D_max
    print(f"\n🔍 TEST: Fuller-Thompson with D_max = 30 μm")
    print(f"   Fuller-Thompson: exponent=0.5, dmax=30.0")
    
    params = PSDParameters(
        psd_type=PSDType.FULLER_THOMPSON,
        exponent=0.5,
        dmax=30.0
    )
    
    distribution = service.convert_to_discrete(params)
    max_diameter = max(distribution.diameters)
    num_bins = len(distribution.points)
    
    print(f"   ✅ Generated {num_bins} bins")
    print(f"   ✅ Maximum diameter: {max_diameter} μm")
    print(f"   ✅ Expected maximum: 30.0 μm")
    
    if max_diameter <= 30.0:
        print(f"   ✅ PASS: Fuller-Thompson respects D_max")
    else:
        print(f"   ❌ FAIL: Fuller-Thompson exceeds D_max!")
    
    print(f"\n🎯 SUMMARY:")
    print(f"   ✅ D_max parameter should limit the maximum diameter in the table")
    print(f"   ✅ When you set D_max=60 in UI, table should only go up to 60 μm")
    print(f"   ✅ Generate Table button should respect current D_max value")
    print(f"   ✅ Integer-centered bins work with any D_max value")

if __name__ == "__main__":
    test_dmax_behavior()
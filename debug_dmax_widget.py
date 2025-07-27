#!/usr/bin/env python3
"""
Debug D_max Widget Issue

Simple test to reproduce and debug the D_max issue in the widget.
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from app.widgets.unified_psd_widget import UnifiedPSDWidget
from app.services.psd_service import PSDService, PSDParameters, PSDType

def debug_dmax_issue():
    """Debug the D_max issue step by step."""
    print("🔍 Debugging D_max Widget Issue")
    print("=" * 40)
    
    # Test 1: Direct service call (this works)
    print("\n1. DIRECT SERVICE TEST (should work):")
    service = PSDService()
    params = PSDParameters(
        psd_type=PSDType.ROSIN_RAMMLER,
        d50=15.0,
        n=1.4,
        dmax=60.0
    )
    distribution = service.convert_to_discrete(params)
    max_diameter = max(distribution.diameters)
    print(f"   Service result: max diameter = {max_diameter} (expected: 60)")
    
    # Test 2: Widget parameter extraction (simulate what widget does)
    print("\n2. WIDGET SIMULATION TEST:")
    
    # Simulate widget getting values (these would come from spin buttons)
    widget_d50 = 15.0
    widget_n = 1.4  
    widget_dmax = 60.0
    
    print(f"   Widget values: d50={widget_d50}, n={widget_n}, dmax={widget_dmax}")
    
    # Create parameters exactly like widget does
    widget_params = PSDParameters(
        psd_type=PSDType.ROSIN_RAMMLER,
        d50=widget_d50,
        n=widget_n,
        dmax=widget_dmax
    )
    
    widget_distribution = service.convert_to_discrete(widget_params)
    widget_max_diameter = max(widget_distribution.diameters)
    print(f"   Widget result: max diameter = {widget_max_diameter} (expected: 60)")
    
    # Test 3: Check if logarithmic bins are being generated correctly
    print("\n3. LOGARITHMIC BINS TEST:")
    bins = service._generate_logarithmic_bins(60.0)
    print(f"   Generated bins: {bins}")
    print(f"   Max bin: {max(bins)} (expected: 60)")
    
    # Test 4: Show the full distribution
    print("\n4. FULL DISTRIBUTION (first and last few bins):")
    for i, (diameter, mass_fraction) in enumerate(widget_distribution.points):
        if i < 3 or i >= len(widget_distribution.points) - 3:
            percentage = mass_fraction * 100
            print(f"   {diameter:3.0f} μm: {percentage:5.2f}%")
        elif i == 3:
            print("   ...")
    
    # Check if the issue is in the widget UI update
    print(f"\n5. SUMMARY:")
    print(f"   Total bins: {len(widget_distribution.points)}")
    print(f"   Max diameter: {widget_max_diameter}")
    print(f"   Expected max: 60")
    
    if widget_max_diameter == 60:
        print("   ✅ D_max is working correctly!")
        print("   🤔 Issue might be in widget table display update")
    else:
        print("   ❌ D_max is not working!")
        print("   🔧 Issue is in the service layer")

if __name__ == "__main__":
    debug_dmax_issue()
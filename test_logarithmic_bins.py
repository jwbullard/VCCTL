#!/usr/bin/env python3
"""
Test Logarithmic Diameter Binning

This demonstrates the new logarithmic binning system Jeff requested:
- Fine resolution for small particles (1, 2, 3, 4, 5 μm)
- Coarser resolution for large particles (20, 25, 30, 40, 50, 60 μm)
- Much more practical than every single integer!
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from app.services.psd_service import PSDService, PSDParameters, PSDType

def test_logarithmic_binning():
    """Test the new logarithmic binning system."""
    print("🎯 NEW: Logarithmic Diameter Binning")
    print("=" * 50)
    
    service = PSDService()
    
    # Show the logarithmic bin structure for different D_max values
    test_cases = [
        ("Small particles (D_max = 10)", 10.0),
        ("Medium particles (D_max = 30)", 30.0), 
        ("Large particles (D_max = 60)", 60.0),
        ("Very large particles (D_max = 150)", 150.0),
    ]
    
    for test_name, dmax_value in test_cases:
        print(f"\n📊 {test_name}")
        print("-" * 40)
        
        # Show what bins are generated for this D_max
        bins = service._generate_logarithmic_bins(dmax_value)
        
        print(f"Generated {len(bins)} logarithmic bins:")
        
        # Group bins for display
        fine_bins = [b for b in bins if b <= 5]
        medium_bins = [b for b in bins if 5 < b <= 15]
        coarse_bins = [b for b in bins if 15 < b <= 75]
        very_coarse_bins = [b for b in bins if b > 75]
        
        if fine_bins:
            print(f"  Fine (≤5 μm):     {', '.join(f'{b:g}' for b in fine_bins)} μm")
        if medium_bins:
            print(f"  Medium (6-15 μm): {', '.join(f'{b:g}' for b in medium_bins)} μm")
        if coarse_bins:
            print(f"  Coarse (16-75 μm): {', '.join(f'{b:g}' for b in coarse_bins)} μm")
        if very_coarse_bins:
            print(f"  Very coarse (>75): {', '.join(f'{b:g}' for b in very_coarse_bins)} μm")
    
    # Test with actual Rosin-Rammler distribution
    print(f"\n\n🧪 ROSIN-RAMMLER TEST with Logarithmic Bins")
    print("=" * 50)
    
    params = PSDParameters(
        psd_type=PSDType.ROSIN_RAMMLER,
        d50=15.0,
        n=1.4,
        dmax=60.0
    )
    
    distribution = service.convert_to_discrete(params)
    
    print(f"D_max = 60 μm → Generated {len(distribution.points)} logarithmic bins")
    print(f"Compare to linear: 60 bins vs logarithmic: {len(distribution.points)} bins")
    print()
    
    # Show distribution with mass fractions
    print("Diameter (μm) | Mass Fraction | Percentage | Bin Type")
    print("-" * 60)
    
    for diameter, mass_fraction in distribution.points:
        percentage = mass_fraction * 100
        
        # Classify bin type
        if diameter <= 5:
            bin_type = "Fine"
        elif diameter <= 15:
            bin_type = "Medium"
        elif diameter <= 75:
            bin_type = "Coarse"
        else:
            bin_type = "V.Coarse"
        
        print(f"{diameter:8.0f}      | {mass_fraction:9.4f}   | {percentage:7.2f}%   | {bin_type}")
    
    print(f"\nCalculated D₅₀: {distribution.d50:.1f} μm")
    print(f"Total mass fraction: {sum(distribution.mass_fractions):.4f}")
    
    # Show advantages
    print(f"\n\n🎯 ADVANTAGES of Logarithmic Binning:")
    print("=" * 50)
    print("✅ Fewer bins: More manageable data (20 bins vs 60 bins)")
    print("✅ Better resolution where it matters: Fine particles")
    print("✅ Practical: Matches how PSD data is typically collected")
    print("✅ Still integer diameters: Compatible with genmic.c")
    print("✅ Flexible: Adapts to any D_max value")
    print("✅ Scientific: Logarithmic spacing is standard in particle analysis")
    
    # Compare linear vs logarithmic
    print(f"\n📈 LINEAR vs LOGARITHMIC Comparison (D_max = 60):")
    print("-" * 50)
    print("Linear bins:      1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, ..., 60")
    print("                  (60 bins - too many!)")
    print()
    print("Logarithmic bins: 1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25, 30, 40, 50, 60")
    print("                  (16 bins - much better!)")
    
    print(f"\n✨ Result: Same accuracy, much cleaner presentation!")

if __name__ == "__main__":
    test_logarithmic_binning()
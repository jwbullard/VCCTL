#!/usr/bin/env python3
"""
Simple test for one-voxel bias calculation using basic Python only.
"""

import math
from typing import List, Tuple

def generate_log_spaced_diameters(min_d: float, max_d: float, num_points: int) -> List[float]:
    """Generate logarithmically spaced diameters."""
    log_min = math.log10(min_d)
    log_max = math.log10(max_d)
    step = (log_max - log_min) / (num_points - 1)
    
    diameters = []
    for i in range(num_points):
        log_d = log_min + i * step
        diameters.append(10 ** log_d)
    
    return diameters

def rosin_rammler_psd(diameters: List[float], d50: float, n: float) -> List[float]:
    """Generate Rosin-Rammler mass fractions."""
    # R = 1 - exp(-(d/d50)^n)
    cumulative = [1 - math.exp(-((d / d50) ** n)) for d in diameters]
    
    # Convert to differential
    mass_fractions = [cumulative[0]]
    for i in range(1, len(cumulative)):
        mass_fractions.append(cumulative[i] - cumulative[i-1])
    
    # Normalize
    total = sum(mass_fractions)
    return [f / total for f in mass_fractions]

def calculate_one_voxel_bias(diameters: List[float], mass_fractions: List[float]) -> float:
    """Calculate one-voxel bias."""
    if len(diameters) < 2:
        return 1.0
    
    # Use first two diameters as d0, d1
    d0 = diameters[0]
    d1 = diameters[1] 
    cutoff = (d0 + d1) / 2.0
    
    # Find cutoff index
    upperbin = len(diameters) - 1
    for i, diameter in enumerate(diameters):
        if diameter > cutoff:
            upperbin = i
            break
    
    if upperbin <= 1:
        return 1.0
    
    # Build cumulative distribution
    cumulative = [mass_fractions[0]]
    for i in range(1, upperbin + 1):
        cumulative.append(cumulative[-1] + mass_fractions[i])
    
    # Normalize up to cutoff
    cutoff_cumulative = cumulative[upperbin]
    if cutoff_cumulative <= 0:
        return 1.0
    
    normalized_cumulative = [c / cutoff_cumulative for c in cumulative]
    
    # Volume density function
    vdist = [0.0]
    for i in range(1, upperbin + 1):
        vdist.append(normalized_cumulative[i] - normalized_cumulative[i-1])
    
    # Integration kernel for numerator
    kernel = [0.0]
    for i in range(1, upperbin + 1):
        kernel.append(vdist[i] * d0 / diameters[i])
    
    # Trapezoidal integration - numerator
    bias_numerator = 0.0
    for i in range(1, upperbin + 1):
        diameter_diff = diameters[i] - diameters[i-1]
        bias_numerator += 0.5 * diameter_diff * (kernel[i-1] + kernel[i])
    
    # Integration kernel for denominator
    kernel_denom = [0.0] + vdist[1:]
    
    # Trapezoidal integration - denominator
    denominator = 0.0
    for i in range(1, upperbin + 1):
        diameter_diff = diameters[i] - diameters[i-1]
        denominator += 0.5 * diameter_diff * (kernel_denom[i-1] + kernel_denom[i])
    
    # Final bias
    if denominator > 0:
        bias = bias_numerator / denominator
    else:
        bias = 1.0
    
    return bias

def test_cement_materials():
    """Test with typical cement phase materials."""
    print("One-Voxel Bias Calculation - Cement Phases")
    print("=" * 50)
    
    materials = [
        {
            'phase_id': 1,
            'name': 'C3S',
            'volume_fraction': 0.35,
            'd50': 15.0,
            'n': 1.1
        },
        {
            'phase_id': 2,
            'name': 'C2S', 
            'volume_fraction': 0.20,
            'd50': 18.0,
            'n': 1.0
        },
        {
            'phase_id': 3,
            'name': 'C3A',
            'volume_fraction': 0.08,
            'd50': 12.0,
            'n': 1.2
        },
        {
            'phase_id': 4,
            'name': 'C4AF',
            'volume_fraction': 0.12,
            'd50': 14.0,
            'n': 1.1
        }
    ]
    
    parameter_lines = []
    
    for material in materials:
        print(f"\nMaterial: {material['name']} (Phase {material['phase_id']})")
        print(f"  Volume Fraction: {material['volume_fraction']:.3f}")
        print(f"  PSD: Rosin-Rammler (d50={material['d50']:.1f}μm, n={material['n']:.1f})")
        
        # Generate PSD
        diameters = generate_log_spaced_diameters(0.5, 75.0, 20)
        mass_fractions = rosin_rammler_psd(diameters, material['d50'], material['n'])
        
        # Calculate D50 from discrete data
        cumulative = 0
        d50_calculated = diameters[-1]
        for i, (d, f) in enumerate(zip(diameters, mass_fractions)):
            cumulative += f
            if cumulative >= 0.5:
                d50_calculated = d
                break
        
        print(f"  Discrete D50: {d50_calculated:.2f}μm (target: {material['d50']:.1f}μm)")
        
        # Calculate bias
        bias = calculate_one_voxel_bias(diameters, mass_fractions)
        print(f"  Bias Value: {bias:.10f}")
        
        # Create parameter line
        line = f"Onevoxelbias,{material['phase_id']},{bias:.10f}"
        parameter_lines.append(line)
        print(f"  Parameter: {line}")
    
    print(f"\n" + "=" * 50)
    print("EXTENDED PARAMETER FILE LINES")
    print("=" * 50)
    
    for line in parameter_lines:
        print(line)
    
    # Show integration with existing test file
    print(f"\n" + "=" * 50) 
    print("INTEGRATION WITH EXISTING EXTENDED PARAMETER FILE")
    print("=" * 50)
    
    extended_params_file = "./test_extended_params.csv"
    if os.path.exists(extended_params_file):
        print(f"✅ Found existing extended parameter file: {extended_params_file}")
        
        # Read existing file
        with open(extended_params_file, 'r') as f:
            lines = f.readlines()
        
        print(f"📄 Current file has {len(lines)} lines")
        print("Adding calculated Onevoxelbias parameters...")
        
        # Create new file with bias parameters
        output_file = "./test_extended_params_with_bias.csv"
        with open(output_file, 'w') as f:
            # Write existing parameters
            for line in lines:
                f.write(line)
            
            # Add bias parameters
            for param_line in parameter_lines:
                f.write(param_line + '\n')
        
        print(f"💾 Updated parameter file: {output_file}")
        print(f"📊 New file has {len(lines) + len(parameter_lines)} lines")
        
        # Test with disrealnew.c
        print(f"\n🔧 Ready for testing with disrealnew.c:")
        print(f"   Command: PYTHONPATH=src ./vcctl-clean-env/bin/python -c \"")
        print(f"   # Test with updated parameter file")
        print(f"   ./backend/bin/disrealnew --workdir=./scratch/HydrationTest \\")
        print(f"                         --parameters={output_file} \\")
        print(f"                         --json\"")
        
    else:
        print(f"⚠️  Extended parameter file not found: {extended_params_file}")
        print("Create the file first by running the hydration parameter setup")
    
    return parameter_lines

if __name__ == "__main__":
    import os
    test_cement_materials()
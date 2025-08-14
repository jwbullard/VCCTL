#!/usr/bin/env python3
"""
Debug the one-voxel bias calculation to understand why all values are 1.0.
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

def debug_bias_calculation(diameters: List[float], mass_fractions: List[float], material_name: str) -> float:
    """Debug version of bias calculation with detailed output."""
    print(f"\n=== DEBUG BIAS CALCULATION: {material_name} ===")
    print(f"Input diameters: {len(diameters)} points")
    print(f"Range: {min(diameters):.3f} - {max(diameters):.1f} μm")
    
    if len(diameters) < 2:
        print("ERROR: Less than 2 diameter points!")
        return 1.0
    
    # Show first few points
    print("First 5 PSD points:")
    for i in range(min(5, len(diameters))):
        print(f"  {diameters[i]:.3f} μm: {mass_fractions[i]:.6f}")
    
    # Use first two diameters as d0, d1
    d0 = diameters[0]
    d1 = diameters[1] 
    cutoff = (d0 + d1) / 2.0
    
    print(f"Quantized diameters: d0={d0:.3f}μm, d1={d1:.3f}μm")
    print(f"Cutoff diameter: {cutoff:.3f}μm")
    
    # Find cutoff index
    upperbin = len(diameters) - 1
    cutoff_found = False
    for i, diameter in enumerate(diameters):
        if diameter > cutoff:
            upperbin = i
            cutoff_found = True
            print(f"Cutoff reached at bin {i}: {diameter:.3f}μm > {cutoff:.3f}μm")
            break
    
    if not cutoff_found:
        print(f"Cutoff NOT reached - all diameters <= {cutoff:.3f}μm")
        print(f"Using upperbin = {upperbin}")
    
    if upperbin <= 1:
        print(f"WARNING: upperbin={upperbin} <= 1, returning bias=1.0")
        return 1.0
    
    # Build cumulative distribution
    print(f"Building cumulative distribution up to bin {upperbin}")
    cumulative = [mass_fractions[0]]
    for i in range(1, upperbin + 1):
        cumulative.append(cumulative[-1] + mass_fractions[i])
    
    cutoff_cumulative = cumulative[upperbin]
    print(f"Cumulative mass up to cutoff: {cutoff_cumulative:.6f}")
    
    if cutoff_cumulative <= 0:
        print("ERROR: Zero cumulative mass at cutoff!")
        return 1.0
    
    # Normalize up to cutoff
    normalized_cumulative = [c / cutoff_cumulative for c in cumulative]
    print(f"Normalized cumulative at cutoff: {normalized_cumulative[upperbin]:.6f}")
    
    # Volume density function
    vdist = [0.0]
    for i in range(1, upperbin + 1):
        vd = normalized_cumulative[i] - normalized_cumulative[i-1]
        vdist.append(vd)
        if i <= 3:  # Show first few
            print(f"  vdist[{i}] = {vd:.6f}")
    
    # Integration kernel for numerator
    print("Integration kernel (first few):")
    kernel = [0.0]
    for i in range(1, upperbin + 1):
        k = vdist[i] * d0 / diameters[i]
        kernel.append(k)
        if i <= 3:
            print(f"  kernel[{i}] = vdist[{i}]({vdist[i]:.6f}) * d0({d0:.3f}) / d[{i}]({diameters[i]:.3f}) = {k:.6f}")
    
    # Trapezoidal integration - numerator
    bias_numerator = 0.0
    print("Trapezoidal integration - numerator:")
    for i in range(1, min(4, upperbin + 1)):  # Show first few
        diameter_diff = diameters[i] - diameters[i-1]
        contribution = 0.5 * diameter_diff * (kernel[i-1] + kernel[i])
        bias_numerator += contribution
        print(f"  bin {i}: dd={diameter_diff:.3f} * 0.5 * ({kernel[i-1]:.6f} + {kernel[i]:.6f}) = {contribution:.6f}")
    
    # Complete numerator calculation
    for i in range(4, upperbin + 1):
        diameter_diff = diameters[i] - diameters[i-1]
        bias_numerator += 0.5 * diameter_diff * (kernel[i-1] + kernel[i])
    
    print(f"Total numerator: {bias_numerator:.6f}")
    
    # Integration kernel for denominator
    kernel_denom = [0.0] + vdist[1:]
    
    # Trapezoidal integration - denominator
    denominator = 0.0
    for i in range(1, upperbin + 1):
        diameter_diff = diameters[i] - diameters[i-1]
        denominator += 0.5 * diameter_diff * (kernel_denom[i-1] + kernel_denom[i])
    
    print(f"Denominator: {denominator:.6f}")
    
    # Final bias
    if denominator > 0:
        bias = bias_numerator / denominator
        print(f"Final bias: {bias_numerator:.6f} / {denominator:.6f} = {bias:.6f}")
    else:
        bias = 1.0
        print("ERROR: Zero denominator, returning bias=1.0")
    
    return bias

def test_fine_material():
    """Test with a very fine material that should definitely have bias != 1.0"""
    print("Testing with SILICA FUME (should have bias << 1.0)")
    
    # Silica fume: median = 0.15 μm, very fine
    # Use diameters from 0.05 to 5.0 μm to capture the fine range
    diameters = generate_log_spaced_diameters(0.05, 5.0, 25)
    
    # Simple log-normal approximation for silica fume
    median = 0.15
    sigma = 1.8
    
    # Generate mass fractions manually
    mass_fractions = []
    for diameter in diameters:
        # Simple log-normal probability density approximation
        if diameter > 0:
            log_d = math.log(diameter)
            log_median = math.log(median)
            exponent = -0.5 * ((log_d - log_median) / sigma) ** 2
            pdf = math.exp(exponent) / (diameter * sigma * math.sqrt(2 * math.pi))
        else:
            pdf = 0
        mass_fractions.append(pdf)
    
    # Normalize
    total = sum(mass_fractions)
    mass_fractions = [f / total for f in mass_fractions]
    
    # Debug calculation
    bias = debug_bias_calculation(diameters, mass_fractions, "Silica_Fume")
    
    print(f"\n*** RESULT: Silica fume bias = {bias:.6f} ***")
    if abs(bias - 1.0) < 0.001:
        print("❌ PROBLEM: Bias is essentially 1.0 - algorithm issue!")
    else:
        print("✅ Bias is different from 1.0 - algorithm working")
    
    return bias

def test_coarse_material():
    """Test with coarse material for comparison."""
    print("\n" + "="*60)
    print("Testing with COARSE CEMENT (should have bias closer to 1.0)")
    
    # Coarse cement: d50 = 25 μm
    diameters = generate_log_spaced_diameters(1.0, 100.0, 20)
    mass_fractions = rosin_rammler_psd(diameters, 25.0, 1.1)
    
    bias = debug_bias_calculation(diameters, mass_fractions, "Coarse_Cement")
    
    print(f"\n*** RESULT: Coarse cement bias = {bias:.6f} ***")
    
    return bias

if __name__ == "__main__":
    print("ONE-VOXEL BIAS DEBUG SESSION")
    print("="*60)
    
    fine_bias = test_fine_material()
    coarse_bias = test_coarse_material()
    
    print(f"\n" + "="*60)
    print("SUMMARY:")
    print(f"Silica fume bias:  {fine_bias:.6f}")
    print(f"Coarse cement bias: {coarse_bias:.6f}")
    
    if abs(fine_bias - 1.0) < 0.001 and abs(coarse_bias - 1.0) < 0.001:
        print("❌ ALGORITHM ISSUE: Both materials have bias ≈ 1.0")
        print("   This suggests a problem in the calculation logic")
    elif fine_bias < coarse_bias:
        print("✅ EXPECTED BEHAVIOR: Fine material has lower bias")
    else:
        print("⚠️  UNEXPECTED: Coarse material has lower bias")
#!/usr/bin/env python3
"""
Test one-voxel bias calculation with correct quantized diameters.
"""

import math
from typing import List

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

def calculate_bias_with_quantized(diameters: List[float], mass_fractions: List[float], 
                                 quantized_diameters: List[float], material_name: str) -> float:
    """Calculate bias with proper quantized diameters."""
    print(f"\n=== {material_name} ===")
    print(f"PSD range: {min(diameters):.3f} - {max(diameters):.1f} μm")
    print(f"Quantized diameters: {quantized_diameters[:5]}... (showing first 5)")
    
    if len(quantized_diameters) < 2:
        return 1.0
    
    d0 = quantized_diameters[0] 
    d1 = quantized_diameters[1]
    cutoff = (d0 + d1) / 2.0
    
    print(f"d0={d0:.1f}μm, d1={d1:.1f}μm, cutoff={cutoff:.1f}μm")
    
    # Find cutoff index in PSD
    upperbin = len(diameters) - 1
    particles_below_cutoff = 0.0
    
    for i, diameter in enumerate(diameters):
        if diameter <= cutoff:
            particles_below_cutoff += mass_fractions[i]
        if diameter > cutoff:
            upperbin = i
            break
    
    print(f"Particles below cutoff: {particles_below_cutoff:.3f} ({particles_below_cutoff*100:.1f}%)")
    print(f"Cutoff reached at bin {upperbin}: {diameters[upperbin]:.3f}μm")
    
    if upperbin <= 1:
        print("WARNING: upperbin <= 1, returning 1.0")
        return 1.0
    
    # Build cumulative distribution up to cutoff
    cumulative = [mass_fractions[0]]
    for i in range(1, upperbin + 1):
        cumulative.append(cumulative[-1] + mass_fractions[i])
    
    cutoff_cumulative = cumulative[upperbin]
    if cutoff_cumulative <= 0:
        return 1.0
    
    # Normalize up to cutoff
    normalized_cumulative = [c / cutoff_cumulative for c in cumulative]
    
    # Volume density function
    vdist = [0.0]
    for i in range(1, upperbin + 1):
        vdist.append(normalized_cumulative[i] - normalized_cumulative[i-1])
    
    # Integration kernel
    kernel = [0.0]
    for i in range(1, upperbin + 1):
        kernel.append(vdist[i] * d0 / diameters[i])
    
    # Trapezoidal integration - numerator
    bias_numerator = 0.0
    for i in range(1, upperbin + 1):
        diameter_diff = diameters[i] - diameters[i-1]
        bias_numerator += 0.5 * diameter_diff * (kernel[i-1] + kernel[i])
    
    # Trapezoidal integration - denominator
    kernel_denom = [0.0] + vdist[1:]
    denominator = 0.0
    for i in range(1, upperbin + 1):
        diameter_diff = diameters[i] - diameters[i-1]
        denominator += 0.5 * diameter_diff * (kernel_denom[i-1] + kernel_denom[i])
    
    # Final bias
    if denominator > 0:
        bias = bias_numerator / denominator
        print(f"Bias calculation: {bias_numerator:.6f} / {denominator:.6f} = {bias:.6f}")
    else:
        bias = 1.0
        print("Zero denominator, returning 1.0")
    
    return bias

def test_with_realistic_quantized():
    """Test with realistic quantized diameters as used in microstructure generation."""
    
    # Typical quantized diameters used in VCCTL microstructure generation
    # These represent the discrete size classes that genmic.c uses
    quantized_diameters = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0, 12.0, 15.0, 
                          20.0, 25.0, 30.0, 40.0, 50.0, 60.0, 75.0]
    
    print("Testing with realistic quantized diameters:")
    print(f"Quantized: {quantized_diameters}")
    print("="*60)
    
    # Test 1: Silica fume (very fine - should have low bias)
    print("\n1. SILICA FUME (very fine particles)")
    sf_diameters = generate_log_spaced_diameters(0.05, 5.0, 30)
    
    # Log-normal distribution centered at 0.15 μm
    sf_fractions = []
    median = 0.15
    sigma = 1.8
    
    for d in sf_diameters:
        if d > 0:
            log_d = math.log(d)
            log_median = math.log(median)
            exponent = -0.5 * ((log_d - log_median) / sigma) ** 2
            pdf = math.exp(exponent)
        else:
            pdf = 0
        sf_fractions.append(pdf)
    
    total = sum(sf_fractions)
    sf_fractions = [f/total for f in sf_fractions]
    
    sf_bias = calculate_bias_with_quantized(sf_diameters, sf_fractions, quantized_diameters, "Silica Fume")
    
    # Test 2: Cement (medium size - should have moderate bias)
    print("\n2. CEMENT C3S (medium particles)")
    cement_diameters = generate_log_spaced_diameters(0.5, 75.0, 25)
    
    # Rosin-Rammler for cement
    d50 = 15.0
    n = 1.1
    cement_cumulative = [1 - math.exp(-((d / d50) ** n)) for d in cement_diameters]
    cement_fractions = [cement_cumulative[0]]
    for i in range(1, len(cement_cumulative)):
        cement_fractions.append(cement_cumulative[i] - cement_cumulative[i-1])
    
    total = sum(cement_fractions)
    cement_fractions = [f/total for f in cement_fractions]
    
    cement_bias = calculate_bias_with_quantized(cement_diameters, cement_fractions, quantized_diameters, "Cement C3S")
    
    # Test 3: Coarse aggregate (large particles - should have bias close to 1.0)
    print("\n3. COARSE AGGREGATE (large particles)")
    agg_diameters = generate_log_spaced_diameters(100.0, 2000.0, 20)
    
    # Fuller curve for aggregate
    max_size = 2000.0
    agg_cumulative = [(d/max_size)**0.5 for d in agg_diameters]
    agg_fractions = [agg_cumulative[0]]
    for i in range(1, len(agg_cumulative)):
        agg_fractions.append(agg_cumulative[i] - agg_cumulative[i-1])
    
    total = sum(agg_fractions)
    agg_fractions = [f/total for f in agg_fractions]
    
    agg_bias = calculate_bias_with_quantized(agg_diameters, agg_fractions, quantized_diameters, "Coarse Aggregate")
    
    # Summary
    print("\n" + "="*60)
    print("RESULTS SUMMARY:")
    print(f"Silica fume bias:     {sf_bias:.6f}")
    print(f"Cement C3S bias:      {cement_bias:.6f}")  
    print(f"Coarse aggregate bias: {agg_bias:.6f}")
    
    print(f"\nExpected pattern: Silica fume << Cement < Coarse aggregate")
    if sf_bias < cement_bias < agg_bias:
        print("✅ CORRECT: Fine materials have lower bias (react faster)")
    elif sf_bias < 1.0:
        print("✅ WORKING: Silica fume bias < 1.0 (algorithm functioning)")
    else:
        print("❌ ISSUE: All biases still close to 1.0")
    
    # Generate corrected parameter lines
    print(f"\n" + "="*60)
    print("CORRECTED PARAMETER LINES:")
    print(f"Onevoxelbias,8,{sf_bias:.10f}  # Silica fume")
    print(f"Onevoxelbias,1,{cement_bias:.10f}  # Cement C3S")
    print(f"Onevoxelbias,32,{agg_bias:.10f} # Coarse aggregate")
    
    return [sf_bias, cement_bias, agg_bias]

if __name__ == "__main__":
    test_with_realistic_quantized()
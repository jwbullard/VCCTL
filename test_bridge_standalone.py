#!/usr/bin/env python3
"""
Standalone test for microstructure-hydration integration.
Demonstrates one-voxel bias calculation without full dependencies.
"""

import os
import json
import math
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum

class PSDType(Enum):
    ROSIN_RAMMLER = "rosin_rammler"
    LOG_NORMAL = "log_normal"
    FULLER_THOMPSON = "fuller_thompson"

@dataclass
class MaterialInfo:
    """Material information for bias calculation."""
    phase_id: int
    name: str
    volume_fraction: float
    psd_type: PSDType
    psd_params: Dict[str, float]

def generate_discrete_psd(psd_type: PSDType, params: Dict[str, float], 
                         num_points: int = 20) -> Tuple[List[float], List[float]]:
    """Generate discrete PSD from parameters."""
    import numpy as np
    
    min_diameter = 0.25
    max_diameter = params.get('dmax', 75.0)
    
    # Create logarithmic diameter bins
    diameters = np.logspace(np.log10(min_diameter), np.log10(max_diameter), num_points)
    
    if psd_type == PSDType.ROSIN_RAMMLER:
        d50 = params.get('d50', 10.0)
        n = params.get('n', 1.1)
        
        # Rosin-Rammler cumulative: R = 1 - exp(-(d/d50)^n)
        cumulative = 1 - np.exp(-((diameters / d50) ** n))
        mass_fractions = np.diff(np.concatenate([[0], cumulative]))
        
    elif psd_type == PSDType.LOG_NORMAL:
        median = params.get('median', 10.0)
        sigma = params.get('sigma', 2.0)
        
        mu = np.log(median)
        
        # Calculate mass fractions using log-normal distribution
        mass_fractions = []
        for i, diameter in enumerate(diameters):
            if i == 0:
                lower = 0
                upper = (diameters[0] + diameters[1]) / 2 if len(diameters) > 1 else diameters[0] * 1.5
            elif i == len(diameters) - 1:
                lower = (diameters[i-1] + diameters[i]) / 2
                upper = float('inf')
            else:
                lower = (diameters[i-1] + diameters[i]) / 2
                upper = (diameters[i] + diameters[i+1]) / 2
            
            # Log-normal CDF approximation
            def log_normal_cdf(x, mu, sigma):
                if x <= 0:
                    return 0.0
                z = (np.log(x) - mu) / (sigma * np.sqrt(2))
                return 0.5 * (1 + math.erf(z))
            
            prob_lower = log_normal_cdf(lower, mu, sigma) if lower > 0 else 0
            prob_upper = log_normal_cdf(upper, mu, sigma) if upper != float('inf') else 1
            
            mass_fraction = prob_upper - prob_lower
            mass_fractions.append(mass_fraction)
        
        mass_fractions = np.array(mass_fractions)
        
    elif psd_type == PSDType.FULLER_THOMPSON:
        exponent = params.get('exponent', 0.5)
        
        # Fuller-Thompson: P = (d/dmax)^exponent
        cumulative = (diameters / max_diameter) ** exponent
        mass_fractions = np.diff(np.concatenate([[0], cumulative]))
        
    else:
        # Default uniform distribution
        mass_fractions = np.ones(len(diameters)) / len(diameters)
    
    # Normalize
    mass_fractions = mass_fractions / np.sum(mass_fractions)
    
    return diameters.tolist(), mass_fractions.tolist()

def calculate_one_voxel_bias(diameters: List[float], mass_fractions: List[float]) -> float:
    """Calculate one-voxel bias using OneVoxelBias.java algorithm."""
    if len(diameters) < 2:
        return 1.0
    
    # Get quantized diameters (use smallest discrete diameters as d0, d1)
    sorted_unique = sorted(set(diameters))
    d0 = sorted_unique[0]
    d1 = sorted_unique[1] if len(sorted_unique) > 1 else d0 * 1.5
    
    # Calculate cutoff
    cutoff = (d0 + d1) / 2.0
    
    # Find cutoff index
    upperbin = len(diameters) - 1
    for i, diameter in enumerate(diameters):
        if diameter > cutoff:
            upperbin = i
            break
    
    bias = 1.0
    
    if upperbin > 1:
        # Build cumulative distribution
        cumulative = [0.0] * len(mass_fractions)
        cumulative[0] = mass_fractions[0]
        
        for i in range(1, upperbin + 1):
            cumulative[i] = cumulative[i-1] + mass_fractions[i]
        
        # Normalize up to cutoff
        cutoff_cumulative = cumulative[upperbin]
        if cutoff_cumulative > 0:
            for i in range(upperbin + 1):
                cumulative[i] /= cutoff_cumulative
        
        # Volume density function
        vdist = [0.0] * (upperbin + 1)
        for i in range(1, upperbin + 1):
            vdist[i] = cumulative[i] - cumulative[i-1]
        vdist[0] = 0.0
        
        # Integration kernel
        kernel = [0.0] * (upperbin + 1)
        for i in range(1, upperbin + 1):
            kernel[i] = vdist[i] * d0 / diameters[i]
        
        # Trapezoidal integration - numerator
        bias = 0.0
        for i in range(1, upperbin + 1):
            diameter_diff = diameters[i] - diameters[i-1]
            bias += 0.5 * diameter_diff * (kernel[i-1] + kernel[i])
        
        # Trapezoidal integration - denominator
        for i in range(1, upperbin + 1):
            kernel[i] = vdist[i]
        
        denom = 0.0
        for i in range(1, upperbin + 1):
            diameter_diff = diameters[i] - diameters[i-1]
            denom += 0.5 * diameter_diff * (kernel[i-1] + kernel[i])
        
        # Final calculation
        if denom > 0:
            bias /= denom
    
    return bias

def create_test_materials() -> List[MaterialInfo]:
    """Create test materials based on typical concrete mix."""
    return [
        MaterialInfo(
            phase_id=1,
            name="C3S",
            volume_fraction=0.25,
            psd_type=PSDType.ROSIN_RAMMLER,
            psd_params={'d50': 15.0, 'n': 1.1, 'dmax': 75.0}
        ),
        MaterialInfo(
            phase_id=2, 
            name="C2S",
            volume_fraction=0.15,
            psd_type=PSDType.ROSIN_RAMMLER,
            psd_params={'d50': 18.0, 'n': 1.0, 'dmax': 75.0}
        ),
        MaterialInfo(
            phase_id=8,
            name="Silica_Fume", 
            volume_fraction=0.025,
            psd_type=PSDType.LOG_NORMAL,
            psd_params={'median': 0.15, 'sigma': 1.5, 'dmax': 5.0}
        ),
        MaterialInfo(
            phase_id=9,
            name="Fly_Ash",
            volume_fraction=0.029,
            psd_type=PSDType.ROSIN_RAMMLER,
            psd_params={'d50': 18.0, 'n': 0.9, 'dmax': 100.0}
        ),
        MaterialInfo(
            phase_id=32,
            name="Fine_Aggregate",
            volume_fraction=0.058,
            psd_type=PSDType.FULLER_THOMPSON,
            psd_params={'exponent': 0.5, 'dmax': 600.0}
        )
    ]

def main():
    """Test one-voxel bias calculation workflow."""
    print("Microstructure-Hydration Integration Test")
    print("=" * 50)
    
    # Create test materials
    materials = create_test_materials()
    
    print(f"Testing with {len(materials)} materials:")
    for material in materials:
        print(f"  • {material.name} (Phase {material.phase_id}): {material.volume_fraction:.3f} volume fraction")
    print()
    
    # Calculate bias for each material
    parameter_lines = []
    
    print("One-Voxel Bias Calculations:")
    print("-" * 40)
    
    for material in materials:
        print(f"\nMaterial: {material.name} (Phase {material.phase_id})")
        print(f"  PSD Type: {material.psd_type.value}")
        print(f"  Parameters: {material.psd_params}")
        print(f"  Volume Fraction: {material.volume_fraction:.6f}")
        
        # Generate discrete PSD
        diameters, mass_fractions = generate_discrete_psd(
            material.psd_type, material.psd_params, 25
        )
        
        print(f"  Discrete PSD: {len(diameters)} points")
        print(f"  Diameter range: {min(diameters):.3f} - {max(diameters):.1f} μm")
        
        # Calculate median diameter
        cumulative = 0
        median_d = diameters[-1]
        for i, (d, f) in enumerate(zip(diameters, mass_fractions)):
            cumulative += f
            if cumulative >= 0.5:
                median_d = d
                break
        print(f"  D50: {median_d:.3f} μm")
        
        # Calculate one-voxel bias
        bias = calculate_one_voxel_bias(diameters, mass_fractions)
        print(f"  Bias Value: {bias:.10f}")
        
        # Generate parameter line
        parameter_line = f"Onevoxelbias,{material.phase_id},{bias:.10f}"
        parameter_lines.append(parameter_line)
        print(f"  Parameter: {parameter_line}")
    
    print(f"\n" + "=" * 50)
    print("EXTENDED PARAMETER FILE LINES")
    print("=" * 50)
    
    for line in parameter_lines:
        print(line)
    
    # Save to file
    os.makedirs("./scratch", exist_ok=True)
    output_file = "./scratch/calculated_onevoxelbias_parameters.txt"
    
    with open(output_file, 'w') as f:
        f.write("# One-voxel bias parameters calculated from material PSDs\n")
        f.write("# Format: Onevoxelbias,phase_id,bias_value\n")
        f.write("# Generated by VCCTL Microstructure-Hydration Bridge\n\n")
        
        for line in parameter_lines:
            f.write(line + '\n')
    
    print(f"\n💾 Parameters saved to: {output_file}")
    
    print(f"\n🔗 Integration Summary:")
    print("1. ✅ Material PSD parameters → Discrete distributions")  
    print("2. ✅ Discrete PSDs → One-voxel bias calculations")
    print("3. ✅ Bias values → Extended parameter file format")
    print("4. 🔄 Next: Integrate with disrealnew.c extended parameter file")
    
    return parameter_lines

if __name__ == "__main__":
    main()
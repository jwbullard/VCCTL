#!/usr/bin/env python3
"""
Standalone test script for one-voxel bias calculation.
Implements the core algorithm without full VCCTL dependencies.
"""

import os
import math
from typing import List, Tuple
from dataclasses import dataclass

@dataclass
class MaterialData:
    """Material data extracted from microstructure input file."""
    phase_id: int
    volume_fraction: float
    diameters: List[float]
    mass_fractions: List[float]

def parse_microstructure_input(microstructure_path: str) -> List[MaterialData]:
    """Parse MyMix01.img.in file to extract material data."""
    input_file = os.path.join(microstructure_path, f"{os.path.basename(microstructure_path)}.img.in")
    
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    with open(input_file, 'r') as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
    
    materials = []
    line_idx = 6  # Skip header lines
    
    # Read number of materials
    num_materials = int(lines[line_idx])
    line_idx += 1
    
    print(f"Found {num_materials} materials")
    
    for material_idx in range(num_materials):
        # Read material header
        phase_id = int(lines[line_idx])
        line_idx += 1
        volume_fraction = float(lines[line_idx])
        line_idx += 1
        num_size_classes = int(lines[line_idx])
        line_idx += 1
        
        print(f"Material {material_idx}: Phase {phase_id}, Volume {volume_fraction:.6f}, {num_size_classes} size classes")
        
        # Read PSD data
        diameters = []
        mass_fractions = []
        
        for _ in range(num_size_classes):
            diameter = float(lines[line_idx])
            line_idx += 1
            mass_fraction = float(lines[line_idx]) 
            line_idx += 1
            
            diameters.append(diameter)
            mass_fractions.append(mass_fraction)
        
        materials.append(MaterialData(phase_id, volume_fraction, diameters, mass_fractions))
    
    return materials

def calculate_one_voxel_bias(diameters: List[float], mass_fractions: List[float]) -> float:
    """
    Calculate one-voxel bias using the OneVoxelBias.java algorithm.
    
    Args:
        diameters: Raw diameter values (μm)
        mass_fractions: Mass fractions for each diameter
    
    Returns:
        Bias value
    """
    if len(diameters) < 2:
        return 1.0
    
    # Use first two diameters as quantized diameters d0, d1
    sorted_unique_diameters = sorted(set(diameters))
    d0 = sorted_unique_diameters[0]
    d1 = sorted_unique_diameters[1] if len(sorted_unique_diameters) > 1 else d0 * 1.5
    
    # Calculate cutoff diameter
    cutoff = (d0 + d1) / 2.0
    
    print(f"    d0={d0:.3f}μm, d1={d1:.3f}μm, cutoff={cutoff:.3f}μm")
    
    # Find where cutoff is reached
    cutoff_reached = False
    upperbin = 0
    
    for i, diameter in enumerate(diameters):
        if diameter > cutoff:
            cutoff_reached = True
            upperbin = i
            break
    
    if not cutoff_reached:
        upperbin = len(diameters) - 1
    
    print(f"    Cutoff reached at bin {upperbin} (diameter {diameters[upperbin]:.3f}μm)")
    
    bias = 1.0
    
    if upperbin > 1:
        # Calculate cumulative PSD
        cumpsd = [0.0] * len(mass_fractions)
        cumpsd[0] = mass_fractions[0]
        
        for i in range(1, upperbin + 1):
            cumpsd[i] = cumpsd[i-1] + mass_fractions[i]
        
        # Normalize cumulative PSD up to cutoff
        cutoff_cumulative = cumpsd[upperbin]
        if cutoff_cumulative > 0:
            for i in range(upperbin + 1):
                cumpsd[i] /= cutoff_cumulative
        
        # Calculate volume density function
        vdist = [0.0] * (upperbin + 1)
        for i in range(1, upperbin + 1):
            vdist[i] = cumpsd[i] - cumpsd[i-1]
        vdist[0] = 0.0
        
        # Calculate integration kernel
        kernel = [0.0] * (upperbin + 1)
        kernel[0] = 0.0
        for i in range(1, upperbin + 1):
            kernel[i] = vdist[i] * d0 / diameters[i]
        
        # Apply trapezoidal rule for numerator
        bias = 0.0
        for i in range(1, upperbin + 1):
            diameter_diff = diameters[i] - diameters[i-1]
            bias += 0.5 * diameter_diff * (kernel[i-1] + kernel[i])
        
        # Calculate denominator
        for i in range(1, upperbin + 1):
            kernel[i] = vdist[i]
        
        denom = 0.0
        for i in range(1, upperbin + 1):
            diameter_diff = diameters[i] - diameters[i-1] 
            denom += 0.5 * diameter_diff * (kernel[i-1] + kernel[i])
        
        # Final bias calculation
        if denom > 0:
            bias /= denom
        else:
            bias = 1.0
        
        print(f"    Numerator: {bias * denom:.6f}, Denominator: {denom:.6f}")
    
    return bias

def get_material_name(phase_id: int) -> str:
    """Get material name from phase ID."""
    names = {
        0: "Pore", 1: "C3S", 2: "C2S", 3: "C3A", 4: "C4AF", 
        5: "Gypsum", 6: "Hemihydrate", 7: "Anhydrite", 
        8: "Silica_Fume", 9: "Fly_Ash", 10: "Slag",
        32: "Fine_Aggregate", 33: "Coarse_Aggregate"
    }
    return names.get(phase_id, f"Phase_{phase_id}")

def main():
    """Test one-voxel bias calculation with MyMix01."""
    microstructure_path = "./scratch/MyMix01"
    
    print("One-Voxel Bias Calculation Test")
    print("=" * 50)
    
    try:
        # Parse microstructure input
        materials = parse_microstructure_input(microstructure_path)
        
        print("\nBias Calculation Results:")
        print("-" * 30)
        
        parameter_lines = []
        
        for material in materials:
            material_name = get_material_name(material.phase_id)
            print(f"Phase {material.phase_id}: {material_name}")
            print(f"  Volume Fraction: {material.volume_fraction:.6f}")
            print(f"  Size Classes: {len(material.diameters)}")
            
            # Calculate bias
            bias = calculate_one_voxel_bias(material.diameters, material.mass_fractions)
            print(f"  Bias Value: {bias:.10f}")
            
            # Generate parameter line (skip pore phase)
            if material.phase_id != 0:
                line = f"Onevoxelbias,{material.phase_id},{bias:.10f}"
                parameter_lines.append(line)
                print(f"  Parameter: {line}")
            
            print()
        
        print("Extended Parameter File Lines:")
        print("-" * 30)
        for line in parameter_lines:
            print(line)
        
        # Save to file
        with open("./scratch/onevoxelbias_parameters.txt", "w") as f:
            for line in parameter_lines:
                f.write(line + "\n")
        
        print(f"\nParameters saved to: ./scratch/onevoxelbias_parameters.txt")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
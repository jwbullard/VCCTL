#!/usr/bin/env python3
"""
Generate corrected one-voxel bias parameters for the extended parameter file.
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
    cumulative = [1 - math.exp(-((d / d50) ** n)) for d in diameters]
    mass_fractions = [cumulative[0]]
    for i in range(1, len(cumulative)):
        mass_fractions.append(cumulative[i] - cumulative[i-1])
    total = sum(mass_fractions)
    return [f / total for f in mass_fractions]

def log_normal_psd(diameters: List[float], median: float, sigma: float) -> List[float]:
    """Generate log-normal mass fractions."""
    fractions = []
    for d in diameters:
        if d > 0:
            log_d = math.log(d)
            log_median = math.log(median)
            exponent = -0.5 * ((log_d - log_median) / sigma) ** 2
            pdf = math.exp(exponent)
        else:
            pdf = 0
        fractions.append(pdf)
    total = sum(fractions)
    return [f/total for f in fractions]

def calculate_bias_correct(diameters: List[float], mass_fractions: List[float], 
                          quantized_diameters: List[float]) -> float:
    """Calculate one-voxel bias with correct algorithm."""
    if len(quantized_diameters) < 2:
        return 1.0
    
    d0 = quantized_diameters[0] 
    d1 = quantized_diameters[1]
    cutoff = (d0 + d1) / 2.0
    
    # Find cutoff index
    upperbin = len(diameters) - 1
    for i, diameter in enumerate(diameters):
        if diameter > cutoff:
            upperbin = i
            break
    
    if upperbin <= 1:
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
        return bias_numerator / denominator
    else:
        return 1.0

def generate_cement_phases_bias():
    """Generate bias parameters for typical cement phases."""
    
    # Standard quantized diameters for VCCTL microstructure generation
    quantized_diameters = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0, 12.0, 15.0, 
                          20.0, 25.0, 30.0, 40.0, 50.0, 60.0, 75.0]
    
    materials = [
        {
            'phase_id': 1,
            'name': 'C3S',
            'psd_type': 'rosin_rammler',
            'd50': 15.0,
            'n': 1.1,
            'diameter_range': (0.5, 75.0)
        },
        {
            'phase_id': 2, 
            'name': 'C2S',
            'psd_type': 'rosin_rammler',
            'd50': 18.0,
            'n': 1.0,
            'diameter_range': (0.5, 75.0)
        },
        {
            'phase_id': 3,
            'name': 'C3A',
            'psd_type': 'rosin_rammler',
            'd50': 12.0,
            'n': 1.2,
            'diameter_range': (0.5, 75.0)
        },
        {
            'phase_id': 4,
            'name': 'C4AF',
            'psd_type': 'rosin_rammler', 
            'd50': 14.0,
            'n': 1.1,
            'diameter_range': (0.5, 75.0)
        },
        {
            'phase_id': 8,
            'name': 'Silica_Fume',
            'psd_type': 'log_normal',
            'median': 0.15,
            'sigma': 1.8,
            'diameter_range': (0.05, 5.0)
        },
        {
            'phase_id': 9,
            'name': 'Fly_Ash',
            'psd_type': 'rosin_rammler',
            'd50': 18.0,
            'n': 0.9,
            'diameter_range': (0.5, 100.0)
        }
    ]
    
    print("Generating One-Voxel Bias Parameters for Cement Phases")
    print("=" * 60)
    print(f"Quantized diameters: {quantized_diameters[:5]}...{quantized_diameters[-2:]}")
    print(f"Cutoff diameter: {(quantized_diameters[0] + quantized_diameters[1])/2:.1f} μm")
    print()
    
    parameter_lines = []
    
    for material in materials:
        print(f"{material['name']} (Phase {material['phase_id']}):")
        
        # Generate PSD
        min_d, max_d = material['diameter_range']
        diameters = generate_log_spaced_diameters(min_d, max_d, 30)
        
        if material['psd_type'] == 'rosin_rammler':
            mass_fractions = rosin_rammler_psd(diameters, material['d50'], material['n'])
            print(f"  PSD: Rosin-Rammler (d50={material['d50']:.1f}μm, n={material['n']:.1f})")
        elif material['psd_type'] == 'log_normal':
            mass_fractions = log_normal_psd(diameters, material['median'], material['sigma'])
            print(f"  PSD: Log-normal (median={material['median']:.2f}μm, σ={material['sigma']:.1f})")
        
        # Calculate fraction below cutoff
        cutoff = (quantized_diameters[0] + quantized_diameters[1]) / 2.0
        below_cutoff = sum(f for d, f in zip(diameters, mass_fractions) if d <= cutoff)
        
        # Calculate bias
        bias = calculate_bias_correct(diameters, mass_fractions, quantized_diameters)
        
        print(f"  Range: {min(diameters):.3f} - {max(diameters):.1f} μm")
        print(f"  Below cutoff: {below_cutoff:.3f} ({below_cutoff*100:.1f}%)")
        print(f"  Bias: {bias:.6f}")
        
        # Generate parameter line
        line = f"Onevoxelbias,{material['phase_id']},{bias:.10f}"
        parameter_lines.append(line)
        print(f"  Parameter: {line}")
        print()
    
    return parameter_lines

def update_extended_parameter_file():
    """Update the extended parameter file with corrected bias values."""
    
    # Generate corrected bias parameters
    parameter_lines = generate_cement_phases_bias()
    
    print("=" * 60)
    print("UPDATING EXTENDED PARAMETER FILE")
    print("=" * 60)
    
    # Read existing file without bias parameters
    input_file = "test_extended_params.csv"
    output_file = "test_extended_params_corrected_bias.csv"
    
    try:
        with open(input_file, 'r') as f:
            lines = f.readlines()
        
        # Remove any existing Onevoxelbias lines
        filtered_lines = [line for line in lines if not line.startswith('Onevoxelbias,')]
        
        print(f"✅ Read {len(lines)} lines from {input_file}")
        print(f"📝 Removed {len(lines) - len(filtered_lines)} existing Onevoxelbias lines")
        
        # Write updated file
        with open(output_file, 'w') as f:
            # Write existing parameters
            for line in filtered_lines:
                f.write(line)
            
            # Add corrected bias parameters  
            for param_line in parameter_lines:
                f.write(param_line + '\n')
        
        print(f"💾 Saved corrected file: {output_file}")
        print(f"📊 Total lines: {len(filtered_lines) + len(parameter_lines)}")
        
        # Copy to working directory for testing
        import shutil
        shutil.copy(output_file, "./scratch/HydrationTest/")
        print(f"📂 Copied to: ./scratch/HydrationTest/{output_file}")
        
        print(f"\n🧪 Ready for testing:")
        print(f"cd ./scratch/HydrationTest")
        print(f"../../backend/bin/disrealnew --workdir=./ --parameters={output_file} --json=progress.json")
        
        return True
        
    except FileNotFoundError:
        print(f"❌ File not found: {input_file}")
        print("Please run the hydration parameter setup first")
        return False

if __name__ == "__main__":
    update_extended_parameter_file()
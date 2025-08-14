#!/usr/bin/env python3
"""
Test script for Microstructure-Hydration Bridge Service.
Demonstrates the complete data flow from microstructure creation to hydration parameters.
"""

import sys
import os
import json
sys.path.insert(0, 'src')

from app.services.microstructure_hydration_bridge import MicrostructureHydrationBridge

def create_sample_materials_data():
    """Create sample materials data as would come from the Microstructure Tool UI."""
    return [
        {
            'name': 'cement140',
            'material_type': 'cement',
            'volume_fraction': 0.3355,  # From MyMix01.img.in
            'mass_fraction': 0.423,
            'specific_gravity': 3.15,
            'psd_mode': 'rosin_rammler',
            'psd_d50': 12.5,
            'psd_n': 1.1,
            'psd_dmax': 75.0
        },
        {
            'name': 'silica_fume',
            'material_type': 'silica_fume', 
            'volume_fraction': 0.024963,
            'mass_fraction': 0.032,
            'specific_gravity': 2.20,
            'psd_mode': 'log_normal',
            'psd_median': 0.15,  # Very fine silica fume
            'psd_spread': 1.5
        },
        {
            'name': 'fly_ash_class_f',
            'material_type': 'fly_ash',
            'volume_fraction': 0.0289194,
            'mass_fraction': 0.045,
            'specific_gravity': 2.38,
            'psd_mode': 'rosin_rammler',
            'psd_d50': 18.0,
            'psd_n': 0.9,
            'psd_dmax': 100.0
        },
        {
            'name': 'fine_aggregate',
            'material_type': 'aggregate',
            'volume_fraction': 0.058,
            'mass_fraction': 0.15,
            'specific_gravity': 2.65,
            'psd_mode': 'fuller_thompson',
            'psd_exponent': 0.5,
            'psd_dmax': 600.0  # Fine aggregate max
        }
    ]

def test_complete_workflow():
    """Test the complete microstructure-to-hydration workflow."""
    print("Microstructure-Hydration Bridge Service Test")
    print("=" * 60)
    
    # Initialize bridge service
    bridge = MicrostructureHydrationBridge()
    
    # Step 1: Simulate microstructure creation
    operation_name = "TestMix_20250811"
    microstructure_file = "./scratch/TestMix_20250811/TestMix_20250811.img" 
    system_size = 100
    resolution = 1.0
    materials_data = create_sample_materials_data()
    
    print(f"Step 1: Storing microstructure metadata")
    print(f"  Operation: {operation_name}")
    print(f"  System size: {system_size}³ voxels")
    print(f"  Resolution: {resolution} μm/voxel")
    print(f"  Materials: {len(materials_data)}")
    
    for i, material in enumerate(materials_data):
        print(f"    {i+1}. {material['name']} ({material['material_type']})")
        print(f"       Volume fraction: {material['volume_fraction']:.6f}")
        if 'psd_d50' in material:
            print(f"       PSD: {material['psd_mode']} (d50={material['psd_d50']:.1f}μm)")
        elif 'psd_median' in material:
            print(f"       PSD: {material['psd_mode']} (median={material['psd_median']:.2f}μm)")
        else:
            print(f"       PSD: {material['psd_mode']}")
    
    # Store metadata
    success = bridge.store_microstructure_metadata(
        operation_name, microstructure_file, system_size, resolution, materials_data
    )
    
    if not success:
        print("❌ Failed to store metadata")
        return
    
    print("✅ Metadata stored successfully")
    print()
    
    # Step 2: List available microstructures
    print("Step 2: Available microstructures with metadata")
    microstructures = bridge.list_available_microstructures() 
    for ms in microstructures:
        summary = bridge.get_microstructure_summary(ms)
        if summary:
            print(f"  • {ms}: {summary['num_materials']} materials, {summary['system_size']}³ voxels")
    print()
    
    # Step 3: Calculate one-voxel bias parameters
    print("Step 3: Calculating one-voxel bias parameters")
    parameter_lines = bridge.calculate_onevoxelbias_for_microstructure(operation_name)
    
    if parameter_lines:
        print("✅ One-voxel bias calculation successful")
        print()
        print("Extended Parameter File Lines:")
        print("-" * 40)
        for line in parameter_lines:
            print(line)
        
        # Save to file for use in hydration simulation
        output_file = f"./scratch/{operation_name}_onevoxelbias.txt"
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w') as f:
            for line in parameter_lines:
                f.write(line + '\n')
        
        print(f"\n💾 Parameters saved to: {output_file}")
        
    else:
        print("❌ One-voxel bias calculation failed")
    
    print()
    
    # Step 4: Show how this integrates with extended parameter file
    print("Step 4: Integration with Extended Parameter File")
    print("These lines would be appended to the hydration parameter file:")
    print()
    
    # Load existing hydration parameters 
    base_params_file = "./parameters.csv"
    if os.path.exists(base_params_file):
        with open(base_params_file, 'r') as f:
            base_lines = [line.strip() for line in f.readlines()[:10]]  # First 10 lines
        
        print("Hydration parameters (first 10 lines):")
        for line in base_lines:
            print(f"  {line}")
        print("  ...")
        print("  # 378 total hydration parameters")
        print()
        
        print("Microstructure UI parameters would be added:")
        ui_params = [
            "Iseed,-12345",
            "Micdir,./scratch/TestMix_20250811/",
            f"Fileroot,{os.path.basename(microstructure_file)}",
            "Temp_0,25.0"
        ]
        for line in ui_params:
            print(f"  {line}")
        print("  # ... other UI parameters")
        print()
        
        print("One-voxel bias parameters (calculated from materials):")
        for line in parameter_lines:
            print(f"  {line}")
        
        print("\n🔗 Complete integration: Database → PSD → Bias → Extended Parameters → disrealnew.c")
    
    return parameter_lines

def test_individual_material_bias():
    """Test bias calculation for individual materials."""
    print("\nIndividual Material Bias Testing")
    print("=" * 40)
    
    bridge = MicrostructureHydrationBridge()
    materials = create_sample_materials_data()
    
    for material in materials:
        print(f"\nMaterial: {material['name']} ({material['material_type']})")
        
        # Convert to PSD parameters
        psd_params = bridge._extract_psd_parameters(material)
        psd_obj = bridge._dict_to_psd_parameters(psd_params)
        
        # Convert to discrete distribution
        discrete_psd = bridge.psd_service.convert_to_discrete(psd_obj, 20)
        
        print(f"  PSD Type: {psd_obj.psd_type.value}")
        print(f"  Discrete points: {len(discrete_psd.diameters)}")
        print(f"  Diameter range: {min(discrete_psd.diameters):.3f} - {max(discrete_psd.diameters):.1f} μm")
        print(f"  D50: {discrete_psd.d50:.3f} μm")
        
        # Show first few PSD points
        print("  PSD points (first 5):")
        for i in range(min(5, len(discrete_psd.diameters))):
            d = discrete_psd.diameters[i]
            f = discrete_psd.mass_fractions[i]
            print(f"    {d:.2f} μm: {f:.4f} ({f*100:.2f}%)")

if __name__ == "__main__":
    try:
        parameter_lines = test_complete_workflow()
        test_individual_material_bias()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
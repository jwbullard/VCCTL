#!/usr/bin/env python3
"""Test script for one-voxel bias calculation service."""

import sys
import os
sys.path.insert(0, 'src')

from app.services.one_voxel_bias_service import OneVoxelBiasService

def test_mymix01_bias():
    """Test bias calculation for MyMix01 microstructure."""
    service = OneVoxelBiasService()
    
    microstructure_path = "./scratch/MyMix01"
    
    print("Testing One-Voxel Bias Calculation")
    print("=" * 50)
    print(f"Microstructure: {microstructure_path}")
    print()
    
    try:
        # Calculate bias for all materials
        bias_results = service.calculate_bias_for_microstructure(microstructure_path)
        
        print("Bias Calculation Results:")
        print("-" * 30)
        
        for result in bias_results:
            print(f"Phase {result.phase_id}: {result.material_name}")
            print(f"  Volume Fraction: {result.volume_fraction:.6f}")
            print(f"  Quantized Diameters: d0={result.d0:.3f}μm, d1={result.d1:.3f}μm")
            print(f"  Cutoff: {result.cutoff_diameter:.3f}μm")
            print(f"  Bias Value: {result.bias_value:.10f}")
            print()
        
        # Generate parameter lines
        print("Extended Parameter File Lines:")
        print("-" * 30)
        parameter_lines = service.generate_onevoxelbias_parameters(bias_results)
        
        for line in parameter_lines:
            print(line)
        
        # Export summary
        summary_file = "./scratch/MyMix01_bias_summary.txt"
        service.export_bias_summary(bias_results, summary_file)
        print(f"\nBias summary exported to: {summary_file}")
        
        return parameter_lines
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    test_mymix01_bias()
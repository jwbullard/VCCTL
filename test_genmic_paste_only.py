#!/usr/bin/env python3
"""
Test genmic input generation for paste-only calculations.
Create two identical mixes except for air volume fraction to verify 
that genmic input files are identical (since genmic simulates paste only).
"""

import sys
import os
import tempfile
import shutil

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def create_test_genmic_files():
    """Create two genmic input files with different air content to test paste-only simulation."""
    
    print("=== GENMIC PASTE-ONLY TEST ===")
    print("Creating two genmic input files:")
    print("1. Cement=1kg, W/B=0.4, Fine agg=0kg, Coarse agg=0kg, Air=0.0")
    print("2. Cement=1kg, W/B=0.4, Fine agg=0kg, Coarse agg=0kg, Air=0.05") 
    print("Expected: Files should be IDENTICAL (genmic simulates paste only)")
    print()
    
    try:
        # Import after path setup
        from app.services.service_container import ServiceContainer
        from app.windows.panels.mix_design_panel import MixDesignPanel
        from app.services.mix_service import MixComponent, MixDesign
        from app.models.material_types import MaterialType
        import gi
        gi.require_version('Gtk', '3.0')
        from gi.repository import Gtk
        
        # Create service container
        service_container = ServiceContainer()
        
        # Create a mock main window for the panel
        class MockMainWindow:
            def __init__(self):
                self.service_container = ServiceContainer()
                
            def update_status(self, message, status_type="info", timeout=3):
                print(f"Status: {message}")
        
        main_window = MockMainWindow()
        
        # Create mix design panel
        mix_panel = MixDesignPanel(main_window)
        
        # Test parameters - same for both tests except air content
        test_params_base = {
            'random_seed': -12345,
            'system_size_x': 100,
            'system_size_y': 100, 
            'system_size_z': 100,
            'resolution': 1.0,
            'cement_shape_set': 'cement140',
            'water_binder_ratio': 0.4,
            'flocculation_enabled': False,
            'dispersion_factor': 0
        }
        
        # Create mix design components for both tests
        cement_component = MixComponent(
            material_name='cement140',
            material_type=MaterialType.CEMENT,
            mass_fraction=0.714286,  # 1kg out of 1.4kg total paste mass
            specific_gravity=3.15
        )
        
        mix_design = MixDesign(
            name='TestPaste',
            components=[cement_component],
            water_binder_ratio=0.4,
            total_water_content=0.285714,  # 0.4kg out of 1.4kg total paste mass
            air_content=0.0  # Will be updated for second test
        )
        
        # Test 1: Air volume fraction = 0.0
        print("Generating input file 1 (air=0.0)...")
        test1_params = test_params_base.copy()
        test1_params['air_content'] = 0.0
        
        mix_design.air_content = 0.0
        input_file_1 = mix_panel._generate_genmic_input_file(mix_design, test1_params)
        
        # Test 2: Air volume fraction = 0.05
        print("Generating input file 2 (air=0.05)...")
        test2_params = test_params_base.copy()
        test2_params['air_content'] = 0.05
        
        mix_design.air_content = 0.05
        input_file_2 = mix_panel._generate_genmic_input_file(mix_design, test2_params)
        
        # Write files for comparison
        with open('genmic_input_air_0.0.txt', 'w') as f:
            f.write(input_file_1)
        
        with open('genmic_input_air_0.05.txt', 'w') as f:
            f.write(input_file_2)
        
        print(f"Files created:")
        print(f"- genmic_input_air_0.0.txt ({len(input_file_1.split())} lines)")
        print(f"- genmic_input_air_0.05.txt ({len(input_file_2.split())} lines)")
        print()
        
        # Compare files
        lines_1 = input_file_1.strip().split('\n')
        lines_2 = input_file_2.strip().split('\n')
        
        print("=== COMPARISON RESULTS ===")
        if input_file_1.strip() == input_file_2.strip():
            print("✅ SUCCESS: Files are IDENTICAL!")
            print("genmic paste-only simulation is working correctly.")
        else:
            print("❌ FAILURE: Files are DIFFERENT!")
            print(f"File 1 has {len(lines_1)} lines")
            print(f"File 2 has {len(lines_2)} lines")
            
            # Show differences
            for i, (line1, line2) in enumerate(zip(lines_1, lines_2)):
                if line1 != line2:
                    print(f"Difference at line {i+1}:")
                    print(f"  Air=0.0:  '{line1}'")
                    print(f"  Air=0.05: '{line2}'")
        
        print()
        print("=== FILE CONTENTS (first 20 lines) ===")
        print("genmic_input_air_0.0.txt:")
        for i, line in enumerate(lines_1[:20]):
            print(f"{i+1:2d}: {line}")
        
        if len(lines_1) > 20:
            print(f"... ({len(lines_1)-20} more lines)")
            
    except Exception as e:
        print(f"❌ Error creating test files: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_test_genmic_files()
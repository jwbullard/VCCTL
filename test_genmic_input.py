#!/usr/bin/env python3
"""
Test genmic input file generation with cement phase fractions
"""

import sys
import os
sys.path.append('/Users/jwbullard/Library/CloudStorage/OneDrive-TexasA&MUniversity/Documents/Projects/Modeling/VCCTL-THAMES-SPRING/vcctl-gtk/src')

from app.models.mix_design import MixDesign, MixComponent
from app.models.mix_design import MaterialType
from app.windows.panels.mix_design_panel import MixDesignPanel
from app.database.service import DatabaseService

def test_genmic_generation():
    """Test genmic input file generation with cement140."""
    
    # Create a mock mix design with cement140
    mix_design = MixDesign(
        name="TestMix-Cement140",
        components=[
            MixComponent(
                material_type=MaterialType.CEMENT,
                material_name="cement140",
                mass_kg=400.0
            ),
            MixComponent(
                material_type=MaterialType.WATER,
                material_name="water",
                mass_kg=160.0
            )
        ],
        water_binder_ratio=0.4,
        air_content=0.02
    )
    
    # Create mock panel to use its methods
    class MockPanel:
        def __init__(self):
            pass
        
        def _generate_genmic_input(self, mix_design, params):
            from app.windows.panels.mix_design_panel import MixDesignPanel
            panel = MixDesignPanel(None)
            return panel._generate_genmic_input(mix_design, params)
    
    mock_panel = MockPanel()
    
    # Parameters for genmic
    params = {
        'random_seed': -1123,
        'system_size': 100,
        'resolution': 1.0,
        'flocculation_enabled': False,
        'flocculation_degree': 0.0
    }
    
    try:
        # Generate input
        input_content = mock_panel._generate_genmic_input(mix_design, params)
        
        print("Generated genmic input file content:")
        print("=" * 50)
        
        lines = input_content.strip().split('\n')
        for i, line in enumerate(lines, 1):
            print(f"{i:3d}: {line}")
        
        # Check for cement phase fractions (should be lines after correlation path)
        print("\n" + "=" * 50)
        print("Analysis of cement phase fraction lines:")
        
        correlation_line_found = False
        phase_lines = []
        for i, line in enumerate(lines):
            if correlation_line_found and len(phase_lines) < 12:
                try:
                    value = float(line)
                    phase_lines.append((i+1, value))
                except ValueError:
                    break
            elif line.endswith("TestMix-Cement140"):
                correlation_line_found = True
                print(f"Correlation path found at line {i+1}: {line}")
        
        if len(phase_lines) == 12:
            print("\nCement phase fractions (volume, surface for each phase):")
            phases = ['C3S', 'C2S', 'C3A', 'C4AF', 'K2SO4', 'NA2SO4']
            for i, phase in enumerate(phases):
                vol_line, vol_val = phase_lines[i*2]
                surf_line, surf_val = phase_lines[i*2 + 1]
                print(f"{phase:>6} - Line {vol_line:3d}: {vol_val:.6f} (vol), Line {surf_line:3d}: {surf_val:.6f} (surf)")
        else:
            print(f"ERROR: Expected 12 phase fraction lines, found {len(phase_lines)}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_genmic_generation()
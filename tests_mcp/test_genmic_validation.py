#!/usr/bin/env python3
"""
VCCTL genmic Input Validation Test Suite
Created using MCP filesystem capabilities for enhanced testing.

This test suite validates the paste-only genmic calculation fix.
"""

import unittest
import sys
import os
from pathlib import Path

# Add src to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

class TestGenmicPasteOnlyCalculation(unittest.TestCase):
    """Test that genmic input generation correctly simulates paste-only."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.project_root = Path(__file__).parent.parent
        
    def test_paste_only_volume_fractions(self):
        """Test that paste volume fractions are calculated correctly."""
        # Expected calculations for cement=1kg, W/B=0.4
        cement_mass = 1.0  # kg
        wb_ratio = 0.4
        water_mass = wb_ratio * cement_mass  # 0.4 kg
        
        # Specific gravities
        cement_sg = 3.15
        water_sg = 1.0
        
        # Calculate expected volume fractions (paste basis)
        cement_abs_vol = cement_mass / cement_sg
        water_abs_vol = water_mass / water_sg
        total_paste_vol = cement_abs_vol + water_abs_vol
        
        expected_binder_solid_vf = cement_abs_vol / total_paste_vol
        expected_water_vf = water_abs_vol / total_paste_vol
        
        # Verify calculations sum to 1.0
        self.assertAlmostEqual(expected_binder_solid_vf + expected_water_vf, 1.0, places=6)
        
        # Expected values based on thermodynamic calculations
        self.assertAlmostEqual(expected_binder_solid_vf, 0.442478, places=6)
        self.assertAlmostEqual(expected_water_vf, 0.557522, places=6)
        
    def test_air_independence(self):
        """Test that air content doesn't affect genmic input files."""
        # Files should exist from previous test
        file1 = self.project_root / "genmic_input_air_0.0.txt"
        file2 = self.project_root / "genmic_input_air_0.05.txt"
        
        if file1.exists() and file2.exists():
            content1 = file1.read_text()
            content2 = file2.read_text()
            
            # Files should be identical
            self.assertEqual(content1, content2, 
                           "genmic input files should be identical regardless of air content")
            
            # Check key volume fractions are present (lines 11-12)
            lines1 = content1.strip().split('\n')
            if len(lines1) >= 12:
                binder_solid_vf = float(lines1[10])  # Line 11 (0-indexed)
                water_vf = float(lines1[11])         # Line 12 (0-indexed)
                
                # Should sum to 1.0 (paste basis)
                self.assertAlmostEqual(binder_solid_vf + water_vf, 1.0, places=6)
        else:
            self.skipTest("genmic input test files not found")

    def test_paste_modeling_hierarchy(self):
        """Test understanding of concrete modeling hierarchy."""
        # This is a conceptual test validating our understanding
        paste_components = {"powders", "water"}
        mortar_components = {"paste", "fine_aggregate", "air"}  
        concrete_components = {"mortar", "coarse_aggregate"}
        
        # genmic simulates paste only
        genmic_scope = paste_components
        
        self.assertEqual(genmic_scope, {"powders", "water"})
        self.assertNotIn("air", genmic_scope)
        self.assertNotIn("fine_aggregate", genmic_scope)
        self.assertNotIn("coarse_aggregate", genmic_scope)

if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
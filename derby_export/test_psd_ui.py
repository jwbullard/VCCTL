#!/usr/bin/env python3
"""
Test the updated PSD UI display
"""

from pathlib import Path
import sys

# Add the src directory to Python path
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from app.database.config import DatabaseConfig
from app.database.service import DatabaseService
from app.services.cement_service import CementService

def test_psd_data_display():
    """Test that PSD data can be loaded for UI display."""
    
    db_config = DatabaseConfig("vcctl.db")
    db_service = DatabaseService(db_config)
    cement_service = CementService(db_service)
    
    # Get a cement with PSD data
    cement = cement_service.get_by_name('cement151')
    
    if cement:
        print(f"Testing PSD data display for {cement.name}")
        print("=" * 50)
        
        # Simulate what the UI would do
        material_data = cement.to_dict()
        
        print(f"PSD mode: {material_data.get('psd_mode', 'None')}")
        print(f"PSD custom points available: {'Yes' if material_data.get('psd_custom_points') else 'No'}")
        
        if material_data.get('psd_custom_points'):
            import json
            try:
                psd_points = json.loads(material_data['psd_custom_points'])
                print(f"Number of PSD points: {len(psd_points)}")
                print(f"First 5 points:")
                for i, (diameter, mass_fraction) in enumerate(psd_points[:5]):
                    print(f"  {i+1}. Diameter: {diameter:.3f} μm, Mass fraction: {mass_fraction:.6f}")
                    
                print(f"Last 5 points:")
                for i, (diameter, mass_fraction) in enumerate(psd_points[-5:], len(psd_points)-4):
                    print(f"  {i}. Diameter: {diameter:.3f} μm, Mass fraction: {mass_fraction:.6f}")
                    
                total_mass = sum(point[1] for point in psd_points)
                print(f"\nTotal mass fraction: {total_mass:.6f}")
                
                # Test UI formatting
                print(f"\nUI Formatting examples:")
                for diameter, mass_fraction in psd_points[:3]:
                    if mass_fraction < 0.001:
                        fraction_str = f'{mass_fraction:.2e}'
                    else:
                        fraction_str = f'{mass_fraction:.6f}'
                    print(f"  Diameter: {diameter:.3f} μm → Mass fraction: {fraction_str}")
                
            except Exception as e:
                print(f"Error parsing PSD data: {e}")
    else:
        print("Cement151 not found")

if __name__ == "__main__":
    test_psd_data_display()
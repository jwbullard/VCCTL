#!/usr/bin/env python3
"""
Debug PSD data loading logic
"""

from pathlib import Path
import sys
import json

# Add the src directory to Python path
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from app.database.config import DatabaseConfig
from app.database.service import DatabaseService
from app.services.cement_service import CementService

def debug_psd_loading():
    """Debug the PSD data loading logic step by step."""
    
    db_config = DatabaseConfig("vcctl.db")
    db_service = DatabaseService(db_config)
    cement_service = CementService(db_service)
    
    # Get cement141
    cement = cement_service.get_by_name('cement141')
    material_data = cement.to_dict()
    
    print("🔍 Debugging PSD data loading for cement141")
    print("=" * 50)
    
    # Step 1: Check material_data exists
    print(f"1. material_data exists: {bool(material_data)}")
    
    # Step 2: Check psd_custom_points exists
    psd_points_json = material_data.get('psd_custom_points')
    print(f"2. psd_custom_points exists: {bool(psd_points_json)}")
    print(f"   psd_custom_points length: {len(psd_points_json) if psd_points_json else 0}")
    
    if psd_points_json:
        # Step 3: Try JSON parsing
        try:
            psd_points = json.loads(psd_points_json)
            print(f"3. JSON parsing successful: {len(psd_points)} points")
            print(f"   First point: {psd_points[0]}")
            print(f"   Data type check: {type(psd_points[0])}, {type(psd_points[0][0])}, {type(psd_points[0][1])}")
            
            # Step 4: Test iteration
            print(f"4. Testing iteration:")
            count = 0
            for diameter, mass_fraction in psd_points[:3]:
                print(f"   Point {count+1}: diameter={diameter} ({type(diameter)}), mass_fraction={mass_fraction} ({type(mass_fraction)})")
                # Test float conversion
                float_diameter = float(diameter)
                float_mass_fraction = float(mass_fraction)
                print(f"   Converted: diameter={float_diameter}, mass_fraction={float_mass_fraction}")
                count += 1
                
            # Step 5: Test total calculation
            total_mass = sum(point[1] for point in psd_points)
            print(f"5. Total mass calculation: {total_mass:.6f}")
            
            # Step 6: Test markup strings
            summary_markup = f'<small>{len(psd_points)} data points, Total mass fraction: {total_mass:.6f}</small>'
            desc_markup = '<i>Experimental particle size distribution data</i>'
            print(f"6. Markup strings:")
            print(f"   Summary: {summary_markup}")
            print(f"   Description: {desc_markup}")
            
            print("✅ All steps completed successfully!")
            
        except Exception as e:
            print(f"❌ Error in step 3 (JSON parsing): {e}")
            import traceback
            traceback.print_exc()
    else:
        print("❌ No psd_custom_points data found")
        
    # Also check if UI components might have naming issues
    print(f"\n🔧 Additional checks:")
    print(f"   psd_mode from data: {material_data.get('psd_mode')}")

if __name__ == "__main__":
    debug_psd_loading()
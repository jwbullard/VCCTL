#!/usr/bin/env python3
"""Debug script to simulate exact UI flow for Filler save"""

import sys
import traceback
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
src_path = project_root / 'src'
sys.path.insert(0, str(src_path))

def debug_ui_flow():
    print("=== Debugging UI Flow for Filler Save ===")
    
    try:
        from app.services.service_container import get_service_container
        from app.models.filler import FillerCreate
        
        service_container = get_service_container()
        
        # Simulate exact UI flow
        material_type = 'filler'
        print(f"Material type: {material_type}")
        
        # Step 1: Get service (like UI does)
        service_mapping = {
            'cement': service_container.cement_service,
            'aggregate': service_container.aggregate_service,
            'fly_ash': service_container.fly_ash_service,
            'slag': service_container.slag_service,
            'filler': service_container.filler_service,
            'silica_fume': service_container.silica_fume_service,
            'limestone': service_container.limestone_service
        }
        service = service_mapping.get(material_type)
        print(f"✅ Got service: {type(service)}")
        
        # Step 2: Create data (like UI does)
        data = {
            'name': 'UITestFiller',
            'specific_gravity': 2.8,
            'blaine_fineness': 400.0,
            'description': 'Test from UI flow simulation'
        }
        
        create_data = FillerCreate(**data)
        print(f"✅ Created FillerCreate object: {create_data.name}")
        
        # Step 3: Call create (like UI does)
        print("Attempting service.create()...")
        created_material = service.create(create_data)
        print(f"✅ Create successful: {type(created_material)}")
        
        # Step 4: Try the exact getattr calls from UI (line 920)
        print("Testing getattr calls from UI...")
        
        try:
            name_value = getattr(created_material, 'name', None)
            print(f"  name attribute: {name_value}")
        except Exception as e:
            print(f"  ❌ Error getting 'name': {e}")
        
        try:
            display_name_value = getattr(created_material, 'display_name', None)
            print(f"  display_name attribute: {display_name_value}")
        except Exception as e:
            print(f"  ❌ Error getting 'display_name': {e}")
        
        try:
            # This is the exact line from UI
            final_name = getattr(created_material, 'name', getattr(created_material, 'display_name', 'unknown'))
            print(f"  ✅ Final name value: {final_name}")
        except Exception as e:
            print(f"  ❌ Error in nested getattr: {e}")
            print(f"  Error type: {type(e)}")
            traceback.print_exc()
        
        # Step 5: Check if created_material has any None attributes that might cause iteration
        print("\nChecking all attributes for None values that might be iterated:")
        for attr_name in dir(created_material):
            if not attr_name.startswith('_'):
                try:
                    value = getattr(created_material, attr_name)
                    if value is None:
                        print(f"  {attr_name}: None")
                    elif hasattr(value, '__iter__') and not isinstance(value, (str, bytes)):
                        print(f"  {attr_name}: iterable - {type(value)}")
                except Exception as e:
                    print(f"  {attr_name}: Error accessing - {e}")
    
    except Exception as e:
        print(f"❌ Flow failed: {e}")
        print(f"Error type: {type(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    debug_ui_flow()
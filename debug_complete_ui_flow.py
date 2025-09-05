#!/usr/bin/env python3
"""Debug script to simulate complete UI dialog flow for Filler save"""

import sys
import traceback
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
src_path = project_root / 'src'
sys.path.insert(0, str(src_path))

def debug_complete_ui_flow():
    print("=== Debugging Complete UI Dialog Flow ===")
    
    try:
        # Import everything we need
        from app.services.service_container import get_service_container
        from app.models.filler import FillerCreate
        
        service_container = get_service_container()
        
        # Step 1: Simulate getting the service like the dialog does
        print("Step 1: Getting service...")
        material_type = 'filler'
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
        print(f"✅ Service: {service}")
        
        # Step 2: Create test data
        print("Step 2: Creating test data...")
        data = {
            'name': f'CompleteFlowTest',
            'specific_gravity': 2.75,
            'description': 'Complete flow test'
        }
        create_data = FillerCreate(**data)
        print(f"✅ FillerCreate: {create_data.name}")
        
        # Step 3: Call create (this should work based on previous tests)
        print("Step 3: Calling service.create()...")
        created_material = service.create(create_data)
        print(f"✅ Created: {type(created_material)}")
        
        # Step 4: Simulate the success logging (line 920 in material_dialog.py)
        print("Step 4: Testing success logging...")
        try:
            log_message = f"Created {material_type}: {getattr(created_material, 'name', getattr(created_material, 'display_name', 'unknown'))}"
            print(f"✅ Log message: {log_message}")
        except Exception as e:
            print(f"❌ Success logging failed: {e}")
            traceback.print_exc()
        
        # Step 5: Simulate status update (line 924)
        print("Step 5: Testing status update simulation...")
        try:
            action = "created"  # not edit mode
            status_message = f"Material {action} successfully"
            print(f"✅ Status message: {status_message}")
        except Exception as e:
            print(f"❌ Status update failed: {e}")
            traceback.print_exc()
        
        # Step 6: Simulate refresh_material_lists (line 928) - this is likely where the error occurs
        print("Step 6: Testing refresh_material_lists simulation...")
        try:
            # We can't create a full main window, but we can test the mix_service part
            mix_service = service_container.mix_service
            
            # This is what refresh_material_lists calls
            print("  Testing _load_material_lists logic...")
            from app.models.material_types import MaterialType
            
            material_lists = {}
            for material_type_enum in MaterialType:
                print(f"    Processing {material_type_enum.name}...")
                try:
                    materials = mix_service.get_compatible_materials(material_type_enum)
                    material_lists[material_type_enum] = materials
                    print(f"      ✅ {material_type_enum.name}: {len(materials) if materials else 0} materials")
                except Exception as e:
                    print(f"      ❌ {material_type_enum.name} failed: {e}")
                    traceback.print_exc()
                    raise
            
            print("✅ refresh_material_lists simulation completed")
            
        except Exception as e:
            print(f"❌ refresh_material_lists simulation failed: {e}")
            if "'NoneType' object is not iterable" in str(e):
                print("🎯 FOUND THE NONETYPE ERROR!")
            traceback.print_exc()
        
        print("\n=== Complete Flow Test Summary ===")
        print("If this test passes but you still get errors in the UI,")
        print("the issue might be in the actual GTK dialog components")
        print("or in some other UI-specific code path.")
    
    except Exception as e:
        print(f"❌ Complete flow test failed: {e}")
        if "'NoneType' object is not iterable" in str(e):
            print("🎯 FOUND THE NONETYPE ERROR!")
        traceback.print_exc()

if __name__ == "__main__":
    debug_complete_ui_flow()
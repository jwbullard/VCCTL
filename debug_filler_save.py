#!/usr/bin/env python3
"""Debug script to trace the NoneType error in Filler save"""

import sys
import traceback
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
src_path = project_root / 'src'
sys.path.insert(0, str(src_path))

def debug_filler_save():
    print("=== Debugging Filler Save Error ===")
    
    try:
        from app.services.service_container import get_service_container
        from app.models.filler import FillerCreate
        
        service_container = get_service_container()
        filler_service = service_container.filler_service
        
        print("✅ Service container and filler_service obtained")
        print(f"   FillerService type: {type(filler_service)}")
        
        # Test data similar to what UI might send
        test_data = FillerCreate(
            name="DebugFiller",
            specific_gravity=2.65,
            blaine_fineness=350.0,
            description="Debug test filler"
        )
        
        print("✅ FillerCreate object created successfully")
        print(f"   Data: name={test_data.name}, sg={test_data.specific_gravity}")
        
        # Try to call the create method step by step
        print("\n--- Attempting create operation ---")
        
        # Step 1: Check if filler exists
        print("Step 1: Checking if filler exists...")
        existing = filler_service.get_by_name(test_data.name)
        print(f"   Existing filler: {existing}")
        
        if existing:
            print("   Filler exists, trying different name...")
            test_data.name = "DebugFiller2"
            existing = filler_service.get_by_name(test_data.name)
            print(f"   New name check: {existing}")
        
        # Step 2: Try the create operation
        print("Step 2: Attempting create...")
        try:
            result = filler_service.create(test_data)
            print(f"✅ Create successful! Result: {result}")
            print(f"   Result type: {type(result)}")
            print(f"   Result name: {result.name}")
            
        except Exception as create_error:
            print(f"❌ Create failed with error: {create_error}")
            print(f"   Error type: {type(create_error)}")
            traceback.print_exc()
            
            # Try to see what line caused the error
            tb = traceback.format_exc()
            if "'NoneType' object is not iterable" in tb:
                print("\n🔍 Found the NoneType error! Full traceback:")
                print(tb)
    
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    debug_filler_save()
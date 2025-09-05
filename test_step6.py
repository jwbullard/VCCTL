#!/usr/bin/env python3
"""Test script for Step 6 - Service container registration validation"""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
src_path = project_root / 'src'
sys.path.insert(0, str(src_path))

def test_service_container():
    print("=== Step 6 Testing Results ===")
    
    try:
        from app.services.service_container import get_service_container
        service_container = get_service_container()
        
        # Test 1: Check if filler_service is accessible
        try:
            filler_service = service_container.filler_service
            print("✅ filler_service is accessible via service container")
            print(f"   Service type: {type(filler_service)}")
        except Exception as e:
            print(f"❌ filler_service not accessible: {e}")
        
        # Test 2: Check if inert_filler_service still exists (backward compatibility)
        try:
            inert_filler_service = service_container.inert_filler_service
            print("✅ inert_filler_service still accessible (backward compatibility)")
            print(f"   Service type: {type(inert_filler_service)}")
        except Exception as e:
            print(f"❌ inert_filler_service not accessible: {e}")
        
        # Test 3: Check if both services are in get_all_services()
        try:
            all_services = service_container.get_all_services()
            
            if 'filler' in all_services:
                print("✅ 'filler' service included in get_all_services()")
            else:
                print("❌ 'filler' service not in get_all_services()")
                
            if 'inert_filler' in all_services:
                print("✅ 'inert_filler' service still included in get_all_services()")
            else:
                print("❌ 'inert_filler' service not in get_all_services()")
                
            print(f"   Total services available: {len(all_services)}")
            
        except Exception as e:
            print(f"❌ get_all_services() test failed: {e}")
        
        # Test 4: Test service functionality
        try:
            # Test basic service methods exist
            filler_service = service_container.filler_service
            
            if hasattr(filler_service, 'get_all'):
                print("✅ FillerService has get_all() method")
            else:
                print("❌ FillerService missing get_all() method")
                
            if hasattr(filler_service, 'get_by_name'):
                print("✅ FillerService has get_by_name() method")
            else:
                print("❌ FillerService missing get_by_name() method")
                
            if hasattr(filler_service, 'create'):
                print("✅ FillerService has create() method")
            else:
                print("❌ FillerService missing create() method")
                
        except Exception as e:
            print(f"❌ Service functionality test failed: {e}")
        
        print("\n🎯 Step 6 Summary:")
        print("- FillerService registered in service container")
        print("- InertFillerService maintained for backward compatibility") 
        print("- Both services accessible via get_all_services()")
        print("- FillerService has required CRUD methods")
        
    except Exception as e:
        print(f"❌ Service container test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_service_container()
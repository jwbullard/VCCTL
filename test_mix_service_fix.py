#!/usr/bin/env python3
"""Test script to verify mix service fix"""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
src_path = project_root / 'src'
sys.path.insert(0, str(src_path))

def test_mix_service_fix():
    print("=== Testing Mix Service Filler Support ===")
    
    try:
        from app.services.service_container import get_service_container
        from app.models.material_types import MaterialType
        
        service_container = get_service_container()
        mix_service = service_container.mix_service
        
        print("✅ Services obtained")
        
        # Test getting compatible materials for FILLER
        try:
            filler_materials = mix_service.get_compatible_materials(MaterialType.FILLER)
            print(f"✅ FILLER materials query successful: {filler_materials}")
            print(f"   Found {len(filler_materials)} filler materials")
        except Exception as e:
            print(f"❌ FILLER materials query failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Test getting compatible materials for INERT_FILLER (should still work)
        try:
            inert_filler_materials = mix_service.get_compatible_materials(MaterialType.INERT_FILLER)
            print(f"✅ INERT_FILLER materials query successful: {len(inert_filler_materials)} materials")
        except Exception as e:
            print(f"❌ INERT_FILLER materials query failed: {e}")
        
        # Test refresh_material_lists flow
        print("\n--- Testing Material Lists Refresh ---")
        print("Available MaterialType enum values:")
        for material_type in MaterialType:
            try:
                materials = mix_service.get_compatible_materials(material_type)
                print(f"  {material_type.name}: {len(materials) if materials else 0} materials")
            except Exception as e:
                print(f"  {material_type.name}: ERROR - {e}")
    
    except Exception as e:
        print(f"❌ Test setup failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_mix_service_fix()
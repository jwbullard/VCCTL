#!/usr/bin/env python3
"""
Test the exact Create Mix flow to identify where it fails.
"""

import sys
import os
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_create_mix_validation_flow():
    """Test the exact validation flow that happens when Create Mix is clicked."""
    
    print("🔍 Testing Create Mix Validation Flow...")
    
    try:
        # Step 1: Import required modules
        print("1. Testing imports...")
        from app.services.service_container import get_service_container
        from app.services.mix_service import MixService, MixComponent, MixDesign
        from app.models.material_types import MaterialType
        print("   ✅ Imports successful")
        
        # Step 2: Create service container
        print("2. Creating service container...")
        container = get_service_container()
        mix_service = container.mix_service
        print("   ✅ Service container and mix service obtained")
        
        # Step 3: Test mix name validation (simulate empty mix name)
        print("3. Testing mix name validation...")
        
        # This simulates what _validate_mix_name() does
        mix_name = ""  # Simulate empty mix name
        if not mix_name or not mix_name.strip():
            print("   ⚠️  Empty mix name detected (this would cause immediate failure)")
            mix_name = "TestMix"  # Use default
            
        print(f"   ✅ Mix name validation: '{mix_name}'")
        
        # Step 4: Test creating mix design from UI (simulate minimal valid mix)
        print("4. Testing mix design creation...")
        
        # Create a minimal valid mix design that should pass validation
        test_mix = MixDesign(
            name=mix_name,
            components=[
                MixComponent(
                    material_name="cement140",
                    material_type=MaterialType.CEMENT,
                    mass_fraction=1.0,  # 100% cement to pass validation
                    volume_fraction=0.315,  # Reasonable volume fraction
                    specific_gravity=3.15
                )
            ],
            water_binder_ratio=0.5,
            total_water_content=0.2,
            air_content=0.02
        )
        print("   ✅ Mix design object created")
        
        # Step 5: Test mix validation (this is where it might fail)
        print("5. Testing mix validation...")
        validation_result = mix_service.validate_mix_design(test_mix)
        print(f"   📋 Validation result: {validation_result}")
        
        if validation_result['is_valid']:
            print("   ✅ Mix validation passed")
        else:
            print(f"   ❌ Mix validation failed: {validation_result['errors']}")
            print("   This could be why Create Mix fails immediately!")
            
        # Step 6: Test operation folder creation logic
        print("6. Testing operation folder creation...")
        operations_dir = Path("Operations")
        clean_name = "".join(c for c in mix_name if c.isalnum() or c in ['_', '-'])
        operation_folder = operations_dir / clean_name
        print(f"   📁 Would create folder: {operation_folder}")
        
        if operations_dir.exists():
            print("   ✅ Operations directory exists")
        else:
            print("   ⚠️  Operations directory missing")
            
        # Step 7: Test genmic binary existence
        print("7. Testing genmic binary...")
        genmic_path = Path("backend/bin/genmic")
        if genmic_path.exists():
            print(f"   ✅ genmic binary exists: {genmic_path}")
        else:
            print(f"   ❌ genmic binary missing: {genmic_path}")
            print("   This could cause Create Mix to fail!")
            
        print("\n🎯 Create Mix Flow Analysis:")
        print("   If validation fails, that's likely the immediate failure cause")
        print("   If genmic binary is missing, that would also cause failure")
        print("   Check if any of these match what you see in the UI")
        
    except Exception as e:
        print(f"❌ Error in create mix flow: {e}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
        print("   This exception could be the cause of immediate failure!")

if __name__ == "__main__":
    test_create_mix_validation_flow()
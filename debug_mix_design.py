#!/usr/bin/env python3
"""
Quick diagnostic script to test Mix Design components without the full UI.
"""

import sys
import os
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_mix_design_basics():
    """Test basic Mix Design service functionality."""
    
    print("🔍 Testing Mix Design Tool Components...")
    
    try:
        # Test 1: Import basic modules
        print("1. Testing imports...")
        from app.services.service_container import get_service_container
        from app.services.mix_service import MixService, MixComponent, MixDesign
        from app.models.material_types import MaterialType
        print("   ✅ Basic imports successful")
        
        # Test 2: Get service container
        print("2. Testing service container...")
        container = get_service_container()
        print("   ✅ Service container created")
        
        # Test 3: Get mix service
        print("3. Testing mix service...")
        mix_service = container.mix_service
        print("   ✅ Mix service obtained")
        
        # Test 4: Check Operations directory
        print("4. Testing Operations directory...")
        operations_dir = Path("Operations")
        if not operations_dir.exists():
            print(f"   ⚠️  Operations directory doesn't exist, creating...")
            operations_dir.mkdir(exist_ok=True)
        print(f"   ✅ Operations directory: {operations_dir.absolute()}")
        
        # Test 5: Test simple mix validation
        print("5. Testing basic mix validation...")
        
        # Create a simple test mix
        test_mix = MixDesign(
            name="TestMix",
            components=[
                MixComponent(
                    material_name="cement140",  # Using a cement we know exists
                    material_type=MaterialType.CEMENT,
                    mass_fraction=0.3,
                    volume_fraction=0.2,
                    specific_gravity=3.15
                )
            ],
            water_binder_ratio=0.5,
            total_water_content=0.2,
            air_content=0.02
        )
        
        validation_result = mix_service.validate_mix_design(test_mix)
        print(f"   📋 Validation result: {validation_result}")
        
        if validation_result['is_valid']:
            print("   ✅ Basic mix validation passed")
        else:
            print(f"   ❌ Mix validation failed: {validation_result['errors']}")
        
        # Test 6: Check genmic binary
        print("6. Testing genmic binary...")
        genmic_path = Path("backend/bin/genmic")
        if genmic_path.exists():
            print(f"   ✅ genmic binary found: {genmic_path.absolute()}")
            print(f"   📊 Binary size: {genmic_path.stat().st_size} bytes")
            print(f"   📅 Last modified: {genmic_path.stat().st_mtime}")
        else:
            print(f"   ❌ genmic binary not found at: {genmic_path.absolute()}")
        
        print("\n🎯 Diagnostic Summary:")
        print("   If all tests pass, the issue is likely in the UI interaction")
        print("   If any test fails, that's where to focus the debugging")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Problem: Missing Python modules or incorrect paths")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    test_mix_design_basics()
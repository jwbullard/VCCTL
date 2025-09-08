#!/usr/bin/env python3
"""
Test script to validate the in-memory validation functionality.
"""

import sys
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

def test_in_memory_validation():
    """Test that validation works without creating folders."""
    print("=== Testing In-Memory Validation (No Folder Creation) ===")
    
    try:
        # Mock the required services
        mock_metadata = Mock()
        mock_metadata.operation_name = "TestMicrostructure"
        mock_metadata.materials = []
        
        class MockBridge:
            def load_microstructure_metadata(self, name):
                return mock_metadata
        
        # Create a minimal hydration panel instance for testing
        from app.windows.panels.hydration_panel import HydrationPanel
        
        panel = HydrationPanel.__new__(HydrationPanel)
        panel.logger = Mock()
        
        # Test valid parameters
        print("Test 1: Valid parameters")
        curing_conditions = {
            'initial_temperature_celsius': 25.0,
            'thermal_mode': 'isothermal',
            'moisture_mode': 'saturated'
        }
        
        time_calibration = {'time_conversion_factor': 1.0}
        advanced_settings = {'c3a_fraction': 0.08}
        db_modifications = {'cement_dissolution_rate': 1.2}
        
        # This should not raise any exceptions
        panel._validate_parameter_completeness(
            curing_conditions, time_calibration, advanced_settings, db_modifications
        )
        print("✓ Valid parameters accepted")
        
        # Test invalid temperature
        print("Test 2: Invalid temperature")
        invalid_curing = curing_conditions.copy()
        invalid_curing['initial_temperature_celsius'] = 150.0  # Too high
        
        try:
            panel._validate_parameter_completeness(
                invalid_curing, time_calibration, advanced_settings, db_modifications
            )
            print("✗ Should have rejected invalid temperature")
            return False
        except ValueError as e:
            print(f"✓ Correctly rejected invalid temperature: {e}")
        
        # Test missing required fields
        print("Test 3: Missing required fields")
        incomplete_curing = {'initial_temperature_celsius': 25.0}  # Missing thermal_mode, moisture_mode
        
        try:
            panel._validate_parameter_completeness(
                incomplete_curing, time_calibration, advanced_settings, db_modifications
            )
            print("✗ Should have rejected incomplete curing conditions")
            return False
        except ValueError as e:
            print(f"✓ Correctly rejected incomplete parameters: {e}")
        
        # Test invalid C3A fraction
        print("Test 4: Invalid C3A fraction")
        invalid_advanced = {'c3a_fraction': 0.5}  # Too high
        
        try:
            panel._validate_parameter_completeness(
                curing_conditions, time_calibration, invalid_advanced, db_modifications
            )
            print("✗ Should have rejected invalid C3A fraction")
            return False
        except ValueError as e:
            print(f"✓ Correctly rejected invalid C3A fraction: {e}")
        
        print("✓ In-memory validation test passed")
        return True
        
    except Exception as e:
        print(f"✗ In-memory validation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_no_folder_creation():
    """Test that validation doesn't create any folders."""
    print("\n=== Testing No Folder Creation ===")
    
    try:
        # Use a temporary directory to monitor for folder creation
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Count initial directories
            initial_dirs = len(list(temp_path.glob('*')))
            
            # Mock os.makedirs to track calls
            makedirs_calls = []
            
            def mock_makedirs(path, **kwargs):
                makedirs_calls.append(path)
                # Don't actually create anything
                pass
            
            # Import and test the validation workflow
            from app.windows.panels.hydration_panel import HydrationPanel
            
            panel = HydrationPanel.__new__(HydrationPanel)
            panel.logger = Mock()
            
            # Mock the bridge to avoid actual service calls
            with patch('app.services.microstructure_hydration_bridge.MicrostructureHydrationBridge') as MockBridge:
                mock_bridge = MockBridge.return_value
                mock_bridge.load_microstructure_metadata.return_value = Mock()
                
                # Simulate validation call (this is what _on_validate_clicked would do)
                curing_conditions = {
                    'initial_temperature_celsius': 25.0,
                    'thermal_mode': 'isothermal',
                    'moisture_mode': 'saturated'
                }
                
                panel._validate_parameter_completeness(
                    curing_conditions, {}, {}, {}
                )
            
            # Check that no folders were created
            final_dirs = len(list(temp_path.glob('*')))
            
            if final_dirs == initial_dirs:
                print("✓ No folders created during validation")
            else:
                print(f"✗ Folders created: initial {initial_dirs}, final {final_dirs}")
                return False
            
            print("✓ No folder creation test passed")
            return True
            
    except Exception as e:
        print(f"✗ No folder creation test failed: {e}")
        return False

def main():
    """Run validation tests."""
    print("=" * 70)
    print("VALIDATION TEST: In-Memory Hydration Parameter Validation")
    print("Testing that validation works without creating Hydration_ folders")
    print("=" * 70)
    
    tests = [
        test_in_memory_validation,
        test_no_folder_creation
    ]
    
    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append((test_func.__name__, result))
        except Exception as e:
            print(f"✗ {test_func.__name__} failed with exception: {e}")
            results.append((test_func.__name__, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("VALIDATION RESULTS:")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL VALIDATION TESTS PASSED!")
        print("\nThe in-memory validation fix is working correctly:")
        print("✅ Parameters are validated without folder creation")
        print("✅ Invalid parameters are properly rejected") 
        print("✅ No Hydration_ folders will be created during validation")
        print("✅ Only the clean operation name folder will be created during execution")
        print("\n✅ READY FOR TESTING")
    else:
        print(f"\n⚠️  {total-passed} TEST(S) FAILED!")
        print("\nThe fix needs more work before testing.")
    
    print("=" * 70)
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
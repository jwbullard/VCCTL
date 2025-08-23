#!/usr/bin/env python3
"""
Debug UI workflow for custom hydration naming.
"""

import sys
import os
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_ui_workflow():
    """Test the exact UI workflow that fails."""
    
    print("🔍 Testing UI Workflow for Custom Hydration Names...")
    
    try:
        # List available microstructures (what the UI dropdown would show)
        print(f"\n📂 Scanning Operations folder for microstructures...")
        
        operations_dir = "./Operations"
        microstructures = []
        
        for operation_name in os.listdir(operations_dir):
            operation_path = os.path.join(operations_dir, operation_name)
            
            # Skip if not a directory
            if not os.path.isdir(operation_path):
                continue
            
            # Check for required microstructure files
            img_file = os.path.join(operation_path, f"{operation_name}.img")
            pimg_file = os.path.join(operation_path, f"{operation_name}.pimg")
            
            if os.path.exists(img_file) and os.path.exists(pimg_file):
                # Get file modification time for sorting
                mod_time = os.path.getmtime(img_file)
                microstructures.append((operation_name, mod_time))
        
        # Sort by modification time (newest first)
        microstructures.sort(key=lambda x: x[1], reverse=True)
        
        print(f"✅ Found {len(microstructures)} valid microstructures:")
        for i, (name, _) in enumerate(microstructures[:5]):  # Show top 5
            print(f"   {i+1}. {name}")
        
        if not microstructures:
            print("❌ No valid microstructures found! This explains the issue.")
            return
        
        # Test with the first available microstructure
        test_microstructure = microstructures[0][0]
        print(f"\n🧪 Testing with microstructure: {test_microstructure}")
        
        # Test custom name scenarios
        test_cases = [
            ("", "auto-generated"),  # Empty name (works)
            ("MyCustomTest", "custom name"),  # Custom name (fails in UI)
            ("AnotherCustomTest", "another custom name"),
        ]
        
        from app.services.service_container import get_service_container
        from app.services.microstructure_hydration_bridge import MicrostructureHydrationBridge
        
        service_container = get_service_container()
        bridge_service = MicrostructureHydrationBridge()
        
        for custom_name, description in test_cases:
            print(f"\n🔬 Testing {description}: '{custom_name}'")
            
            # Simulate the UI naming logic
            if custom_name:
                # Custom name provided
                import re
                operation_name = re.sub(r'[<>:"/\\|?*]', '_', custom_name).strip()
            else:
                # Auto-generate name
                import time
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                operation_name = f"HydrationSim_{test_microstructure}_{timestamp}"
            
            print(f"   Operation name: {operation_name}")
            
            # Test parameter file generation
            try:
                curing_conditions = {
                    'initial_temperature_celsius': 25.0,
                    'thermal_mode': 'isothermal',
                    'moisture_mode': 'saturated',
                    'temperature_profile': 'Custom'
                }
                
                param_file_path = bridge_service.generate_extended_parameter_file(
                    operation_name=operation_name,
                    microstructure_name=test_microstructure,
                    curing_conditions=curing_conditions,
                    max_time_hours=168.0
                )
                print(f"   ✅ Parameter file: {param_file_path}")
                
                # Test simulation start
                executor = service_container.hydration_executor_service
                result = executor.start_hydration_simulation(
                    operation_name=operation_name,
                    parameter_set_name="portland_cement_standard",
                    progress_callback=None,
                    parameter_file_path=param_file_path,
                    max_time_hours=168.0
                )
                
                print(f"   🎯 Simulation start: {'✅ SUCCESS' if result else '❌ FAILED'}")
                
                if result and operation_name in executor.active_simulations:
                    print(f"   🏃 Active simulation found")
                    # Cancel the test simulation to avoid clutter
                    executor.cancel_simulation(operation_name)
                    print(f"   🛑 Test simulation cancelled")
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
                import traceback
                print(f"   Traceback: {traceback.format_exc()}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    test_ui_workflow()
#!/usr/bin/env python3
"""
Debug custom hydration operation naming issue.
"""

import sys
import os
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_custom_name_processing():
    """Test the custom name processing logic."""
    
    print("🔍 Testing Custom Hydration Operation Name Processing...")
    
    try:
        # Import necessary components
        from app.services.service_container import get_service_container
        from app.services.microstructure_hydration_bridge import MicrostructureHydrationBridge
        
        # Get services
        service_container = get_service_container()
        bridge_service = MicrostructureHydrationBridge()
        
        # Test parameters
        test_custom_name = "MyCustomHydrationTest"
        test_microstructure = "Cem140Quartz07"  # Use an existing microstructure
        
        print(f"\n📝 Testing with custom name: '{test_custom_name}'")
        print(f"📝 Using microstructure: '{test_microstructure}'")
        
        # Test the name sanitization logic first
        import re
        sanitized_name = re.sub(r'[<>:"/\\|?*]', '_', test_custom_name)
        sanitized_name = sanitized_name.strip()
        print(f"✅ Sanitized name: '{sanitized_name}'")
        
        # Check if operation directory would exist
        operations_dir = Path("./Operations")
        potential_operation_dir = operations_dir / sanitized_name
        print(f"📁 Would create directory: {potential_operation_dir}")
        print(f"📁 Directory exists: {potential_operation_dir.exists()}")
        
        # Check database for existing operations
        try:
            with service_container.database_service.get_read_only_session() as session:
                from app.models.operation import Operation
                existing_op = session.query(Operation).filter_by(name=sanitized_name).first()
                print(f"🗃️ Operation exists in database: {existing_op is not None}")
                if existing_op:
                    print(f"   Existing operation: {existing_op.name} (status: {existing_op.status})")
        except Exception as e:
            print(f"❌ Database check failed: {e}")
        
        # Test extended parameter file generation
        print(f"\n🔧 Testing parameter file generation...")
        
        # Basic curing conditions for test
        curing_conditions = {
            'initial_temperature_celsius': 25.0,
            'thermal_mode': 'isothermal',
            'moisture_mode': 'saturated',
            'temperature_profile': 'Custom'
        }
        
        # Test parameter file generation
        try:
            param_file_path = bridge_service.generate_extended_parameter_file(
                operation_name=sanitized_name,
                microstructure_name=test_microstructure,
                curing_conditions=curing_conditions,
                max_time_hours=168.0
            )
            print(f"✅ Parameter file generated: {param_file_path}")
            
            # Check if file actually exists
            if os.path.exists(param_file_path):
                print(f"✅ Parameter file exists on disk: {param_file_path}")
                
                # Check file size
                file_size = os.path.getsize(param_file_path)
                print(f"📊 Parameter file size: {file_size} bytes")
                
            else:
                print(f"❌ Parameter file not found on disk: {param_file_path}")
                
        except Exception as e:
            print(f"❌ Parameter file generation failed: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
        
        # Test HydrationExecutorService start simulation
        print(f"\n🚀 Testing HydrationExecutorService start simulation...")
        
        try:
            executor = service_container.hydration_executor_service
            
            # Test the start_hydration_simulation method
            result = executor.start_hydration_simulation(
                operation_name=sanitized_name,
                parameter_set_name="portland_cement_standard",
                progress_callback=None,
                parameter_file_path=param_file_path if 'param_file_path' in locals() else None,
                max_time_hours=168.0
            )
            
            print(f"🎯 Simulation start result: {result}")
            
            if result:
                print(f"✅ SUCCESS: Custom name hydration operation started successfully!")
                
                # Check if operation is in active simulations
                if sanitized_name in executor.active_simulations:
                    print(f"✅ Operation found in active simulations")
                    sim_info = executor.active_simulations[sanitized_name]
                    print(f"   Process: {sim_info.get('process')}")
                    print(f"   Start time: {sim_info.get('start_time')}")
                else:
                    print(f"❌ Operation not found in active simulations")
            else:
                print(f"❌ FAILURE: Custom name hydration operation failed to start")
                
        except Exception as e:
            print(f"❌ HydrationExecutorService test failed: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    test_custom_name_processing()
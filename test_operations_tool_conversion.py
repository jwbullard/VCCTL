#!/usr/bin/env python3
"""
Test the Operations Tool's actual _convert_db_operation_to_ui_operation method
"""

import sys
import os
sys.path.insert(0, 'src')

def test_operations_tool_conversion():
    """Test the Operations Tool's database conversion method."""
    try:
        from app.services.service_container import get_service_container
        from app.windows.panels.operations_monitoring_panel import OperationsMonitoringPanel
        
        print("=== TESTING OPERATIONS TOOL CONVERSION METHOD ===")
        
        # Create a minimal Operations Tool instance to test the conversion method
        # We'll create a minimal mock main_window for testing
        class MockMainWindow:
            pass
        
        mock_window = MockMainWindow()
        
        # Create Operations Tool panel
        ops_panel = OperationsMonitoringPanel(mock_window)
        
        # Get operations from database
        container = get_service_container()
        operation_service = container.operation_service
        db_operations = operation_service.get_all()
        
        print(f"Found {len(db_operations)} operations in database")
        
        # Test the actual conversion method
        print("\nTesting actual _convert_db_operation_to_ui_operation method:")
        
        for db_op in db_operations:
            print(f"\nConverting: {db_op.name}")
            print(f"  DB Type: {db_op.type}")
            print(f"  DB Status: {db_op.status}")
            
            try:
                ui_operation = ops_panel._convert_db_operation_to_ui_operation(db_op)
                
                print(f"  ✅ Conversion successful!")
                print(f"  UI ID: {ui_operation.id}")
                print(f"  UI Name: {ui_operation.name}")
                print(f"  UI Type: {ui_operation.operation_type.value}")
                print(f"  UI Status: {ui_operation.status.value}")
                print(f"  UI Progress: {ui_operation.progress}")
                print(f"  UI Start Time: {ui_operation.start_time}")
                print(f"  UI End Time: {ui_operation.end_time}")
                
            except Exception as e:
                print(f"  ❌ Conversion failed: {e}")
                import traceback
                traceback.print_exc()
        
        print("\n=== TESTING COMPLETE DATABASE LOADING PROCESS ===")
        
        # Test the full loading process 
        try:
            # Clear existing operations
            ops_panel.operations = {}
            
            # Call the actual loading method
            ops_panel._load_operations_from_file()
            
            print(f"Total operations loaded: {len(ops_panel.operations)}")
            
            for op_id, operation in ops_panel.operations.items():
                print(f"- {operation.name}: {operation.operation_type.value} ({operation.status.value})")
                
            if len(ops_panel.operations) >= len(db_operations):
                print("✅ Operations Tool successfully loaded database operations!")
            else:
                print("❌ Operations Tool failed to load all database operations")
                
        except Exception as e:
            print(f"❌ Error in full loading process: {e}")
            import traceback
            traceback.print_exc()
        
    except Exception as e:
        print(f"❌ Error testing operations tool conversion: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_operations_tool_conversion()
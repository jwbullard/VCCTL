#!/usr/bin/env python3
"""
Test the Operations Tool database loading functionality
"""

import sys
import os
sys.path.insert(0, 'src')

def test_operations_tool_loading():
    """Test if Operations Tool can load operations from database."""
    try:
        from app.services.service_container import get_service_container
        from app.windows.panels.operations_monitoring_panel import OperationsMonitoringPanel
        
        print("=== TESTING OPERATIONS TOOL DATABASE LOADING ===")
        
        # Test the conversion function directly
        container = get_service_container()
        operation_service = container.operation_service
        
        # Get operations from database
        db_operations = operation_service.get_all()
        print(f"Found {len(db_operations)} operations in database")
        
        # Test the conversion logic manually (without creating full UI)
        print("\nTesting database to UI conversion:")
        
        for db_op in db_operations:
            print(f"\nDatabase operation: {db_op.name}")
            print(f"  DB Type: {db_op.type}")
            print(f"  DB Status: {db_op.status}")
            
            # Simulate the conversion logic from operations_monitoring_panel.py
            from app.models.operation import OperationStatus as DBOperationStatus, OperationType as DBOperationType
            from app.windows.panels.operations_monitoring_panel import OperationStatus as UIOperationStatus, OperationType as UIOperationType
            
            # Map database status to UI status
            status_mapping = {
                DBOperationStatus.QUEUED.value: UIOperationStatus.PENDING,
                DBOperationStatus.RUNNING.value: UIOperationStatus.RUNNING,  
                DBOperationStatus.FINISHED.value: UIOperationStatus.COMPLETED,
                DBOperationStatus.ERROR.value: UIOperationStatus.FAILED,
                DBOperationStatus.CANCELLED.value: UIOperationStatus.CANCELLED,
            }
            
            # Map database type to UI type
            type_mapping = {
                DBOperationType.HYDRATION.value: UIOperationType.HYDRATION_SIMULATION,
                DBOperationType.MICROSTRUCTURE.value: UIOperationType.MICROSTRUCTURE_GENERATION,
                DBOperationType.ANALYSIS.value: UIOperationType.PROPERTY_CALCULATION,
                DBOperationType.EXPORT.value: UIOperationType.FILE_OPERATION,
                DBOperationType.IMPORT.value: UIOperationType.FILE_OPERATION,
            }
            
            ui_status = status_mapping.get(db_op.status, UIOperationStatus.PENDING)
            ui_type = type_mapping.get(db_op.type, UIOperationType.BATCH_OPERATION)
            
            print(f"  Converted UI Type: {ui_type.value}")
            print(f"  Converted UI Status: {ui_status.value}")
            
            # Calculate progress
            progress = 0.0
            if ui_status == UIOperationStatus.COMPLETED:
                progress = 1.0
            elif ui_status == UIOperationStatus.RUNNING:
                progress = 0.5
            
            print(f"  Calculated Progress: {progress}")
            
        print("\n✅ Database to UI conversion test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error testing operations tool loading: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_operations_tool_loading()
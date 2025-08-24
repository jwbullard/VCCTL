#!/usr/bin/env python3
"""
Test script to debug operation status mapping issues.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from app.services.service_container import get_service_container
from app.models.operation import OperationStatus, OperationType as DBOperationType

def test_status_mapping():
    """Test operation status creation and mapping."""
    print("🧪 Testing Operation Status Mapping")
    print("=" * 50)
    
    try:
        container = get_service_container()
        
        # Test creating operation with RUNNING status
        test_name = "StatusTestOperation"
        
        # Clean up any existing test operation first
        container.operation_service.delete(test_name)
        
        print("1. Creating operation with RUNNING status...")
        db_operation = container.operation_service.create_operation(
            name=test_name,
            operation_type=DBOperationType.MICROSTRUCTURE.value,
            status=OperationStatus.RUNNING,
            progress=0.25,
            current_step="Testing status mapping",
            notes="Test operation for status mapping"
        )
        
        print(f"   ✅ Created: {db_operation.name}")
        print(f"   ✅ Status in DB: {db_operation.status}")
        print(f"   ✅ Progress in DB: {db_operation.progress}")
        print(f"   ✅ Current Step in DB: {db_operation.current_step}")
        
        print("\n2. Reading operation back from database...")
        retrieved_op = container.operation_service.get_by_name(test_name)
        if retrieved_op:
            print(f"   ✅ Retrieved: {retrieved_op.name}")
            print(f"   ✅ Status from DB: {retrieved_op.status}")
            print(f"   ✅ Progress from DB: {retrieved_op.progress}")
            print(f"   ✅ Current Step from DB: {retrieved_op.current_step}")
        else:
            print("   ❌ Operation not found!")
            
        print("\n3. Testing UI conversion...")
        # Test the conversion that happens in operations panel
        from app.windows.panels.operations_monitoring_panel import OperationStatus as UIOperationStatus
        
        # Simulate the conversion logic (this is the actual mapping from the panel)
        status_mapping = {
            'QUEUED': UIOperationStatus.PENDING,
            'RUNNING': UIOperationStatus.RUNNING,  
            'COMPLETED': UIOperationStatus.COMPLETED,
            'FAILED': UIOperationStatus.FAILED,
            'CANCELLED': UIOperationStatus.CANCELLED,
        }
        
        ui_status = status_mapping.get(retrieved_op.status, UIOperationStatus.PENDING)
        print(f"   ✅ UI Status Conversion: {retrieved_op.status} → {ui_status.value}")
        
        # Test current step handling
        if ui_status == UIOperationStatus.PENDING:
            step_display = retrieved_op.current_step if (retrieved_op.current_step and retrieved_op.current_step.strip()) else "Queued for execution"
        elif ui_status == UIOperationStatus.RUNNING:
            step_display = retrieved_op.current_step or "Operation in progress..."
        else:
            step_display = retrieved_op.current_step or "Unknown"
            
        print(f"   ✅ Step Display: '{step_display}'")
        
        print("\n🎯 DIAGNOSIS:")
        print("=" * 50)
        if retrieved_op.status == 'RUNNING' and ui_status == UIOperationStatus.RUNNING:
            print("✅ Status mapping working correctly")
            print("✅ Operations should show as RUNNING, not PENDING")
        else:
            print(f"❌ Status mapping issue:")
            print(f"   DB Status: {retrieved_op.status}")
            print(f"   UI Status: {ui_status.value}")
            
        if step_display and step_display != "Queued for execution":
            print("✅ Progress display working correctly") 
            print(f"✅ Should show: '{step_display}'")
        else:
            print("❌ Progress display issue - showing generic queued message")
            
        # Clean up
        container.operation_service.delete(test_name)
        print("\n🧹 Test operation cleaned up")
        
    except Exception as e:
        print(f"❌ Error testing status mapping: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_status_mapping()
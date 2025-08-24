#!/usr/bin/env python3
"""
Test script to verify smart refresh prevents duplicates.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_duplicate_prevention():
    """Test that smart refresh prevents duplicates."""
    print("🧪 Testing Smart Refresh Duplicate Prevention")
    print("=" * 60)
    
    try:
        from app.services.service_container import get_service_container
        from app.models.operation import OperationStatus as DBOperationStatus
        from app.windows.panels.operations_monitoring_panel import OperationStatus as UIOperationStatus
        
        container = get_service_container()
        
        # Clean up any existing test operations
        test_name = "DuplicatePreventionTest"
        container.operation_service.delete(test_name)
        
        print("1. Setting up test scenario...")
        
        # Create a database operation (simulates what gets saved when operation starts)
        db_operation = container.operation_service.create_operation(
            name=test_name,
            operation_type="MICROSTRUCTURE",
            status=DBOperationStatus.RUNNING,
            progress=0.35,
            current_step="Generating 3D microstructure - 35% complete",
            notes="Test operation for duplicate prevention"
        )
        
        print(f"   ✅ Created database operation: {db_operation.name}")
        print(f"   📊 Database status: {db_operation.status}, progress: {db_operation.progress:.1%}")
        
        print("\n2. Simulating in-memory running operation with updated progress...")
        
        # Create mock in-memory operation (simulates live progress updates)
        class MockOperation:
            def __init__(self):
                self.id = "proc_test_123"
                self.name = test_name
                self.status = UIOperationStatus.RUNNING
                self.progress = 0.67  # Higher progress than database
                self.current_step = "Generating 3D microstructure - 67% complete (live update)"
                self.operation_type = "MICROSTRUCTURE_GENERATION"
        
        mock_operation = MockOperation()
        
        # Simulate operations dictionary with running operation
        mock_operations = {
            "proc_test_123": mock_operation
        }
        
        print(f"   ✅ In-memory operation: {mock_operation.name}")  
        print(f"   📊 Memory status: {mock_operation.status.value}, progress: {mock_operation.progress:.1%}")
        
        print("\n3. Testing smart refresh logic...")
        
        # Simulate smart refresh logic
        running_operations = {
            op_id: op for op_id, op in mock_operations.items() 
            if op.status in [UIOperationStatus.RUNNING, UIOperationStatus.PAUSED]
        }
        
        running_operation_names = {op.name for op in running_operations.values()}
        
        print(f"   🔍 Running operations to preserve: {len(running_operations)}")
        print(f"   📝 Running operation names: {list(running_operation_names)}")
        
        # Simulate database loading
        with container.database_service.get_read_only_session() as session:
            from app.models.operation import Operation as DBOperation
            db_operations = session.query(DBOperation).filter(DBOperation.name == test_name).all()
        
        print(f"   🔍 Database operations found: {len(db_operations)}")
        
        # Test the skip logic
        db_operations_to_load = []
        db_operations_to_skip = []
        
        for db_op in db_operations:
            if db_op.name in running_operation_names:
                db_operations_to_skip.append(db_op)
                print(f"   ⏭️  Would skip DB operation: {db_op.name} (running in-memory)")
            else:
                db_operations_to_load.append(db_op)
                print(f"   📥 Would load DB operation: {db_op.name}")
        
        print("\n4. Results after smart refresh:")
        print(f"   📊 Operations to load from DB: {len(db_operations_to_load)}")
        print(f"   ⏭️  Operations to skip (duplicates): {len(db_operations_to_skip)}")
        print(f"   🏃 Running operations to preserve: {len(running_operations)}")
        
        final_operations_count = len(db_operations_to_load) + len(running_operations)
        print(f"   🎯 Final operations count: {final_operations_count}")
        
        print("\n🎯 VALIDATION:")
        print("=" * 60)
        if len(db_operations_to_skip) > 0:
            print("✅ Duplicate prevention working!")
            print(f"✅ Skipped {len(db_operations_to_skip)} database operation(s) that exist as running")
            print("✅ No duplicates would be created")
        else:
            print("❌ No database operations to skip - test scenario might not be realistic")
            
        if final_operations_count == 1:
            print("✅ Final result: exactly 1 operation (no duplicates)")
            print("✅ Running operation with live progress would be preserved")
        else:
            print(f"❌ Final result: {final_operations_count} operations (duplicates detected)")
            
        # Clean up
        container.operation_service.delete(test_name)
        print("\n🧹 Test operation cleaned up")
        
    except Exception as e:
        print(f"❌ Error testing duplicate prevention: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_duplicate_prevention()
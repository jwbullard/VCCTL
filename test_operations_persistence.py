#!/usr/bin/env python3
"""
Test script to verify operations persistence works correctly.
"""

import sys
import logging
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.append('src')

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(name)s - %(message)s')

from app.windows.panels.operations_monitoring_panel import (
    Operation, OperationType, OperationStatus, OperationsMonitoringPanel
)

def test_operation_serialization():
    """Test that operations can be serialized and deserialized."""
    print("Testing operation serialization...")
    
    # Create a test operation
    operation = Operation(
        id="test_001",
        name="Test Microstructure Generation",
        operation_type=OperationType.MICROSTRUCTURE_GENERATION,
        status=OperationStatus.COMPLETED,
        start_time=datetime.now(),
        end_time=datetime.now(),
        progress=1.0,
        current_step="Completed successfully",
        total_steps=10,
        completed_steps=10
    )
    
    # Test serialization
    op_dict = operation.to_dict()
    print(f"✅ Serialized operation: {op_dict['name']}")
    
    # Test deserialization
    restored_op = Operation.from_dict(op_dict)
    print(f"✅ Deserialized operation: {restored_op.name}")
    
    # Verify data integrity
    assert restored_op.name == operation.name
    assert restored_op.status == operation.status
    assert restored_op.operation_type == operation.operation_type
    print("✅ Operation serialization working correctly")
    
    return operation

def test_file_persistence():
    """Test that operations can be saved to and loaded from file."""
    print("\nTesting file persistence...")
    
    # Create a mock main window class for testing
    class MockMainWindow:
        pass
    
    # Create operations panel
    main_window = MockMainWindow()
    panel = OperationsMonitoringPanel(main_window)
    
    # Add a test operation
    operation = Operation(
        id="test_persistence_001",
        name="Test Persistence Operation",
        operation_type=OperationType.PROPERTY_CALCULATION,
        status=OperationStatus.COMPLETED,
        start_time=datetime.now(),
        end_time=datetime.now(),
        progress=1.0
    )
    
    panel.operations["test_persistence_001"] = operation
    panel.operation_counter = 1
    
    print(f"Created operation: {operation.name}")
    
    # Test saving
    panel._save_operations_to_file()
    print("✅ Saved operations to file")
    
    # Clear operations
    panel.operations.clear()
    panel.operation_counter = 0
    print("Cleared operations from memory")
    
    # Test loading
    panel._load_operations_from_file()
    print("✅ Loaded operations from file")
    
    # Verify the operation was restored
    if "test_persistence_001" in panel.operations:
        restored_op = panel.operations["test_persistence_001"]
        print(f"✅ Restored operation: {restored_op.name}")
        assert restored_op.name == operation.name
        assert restored_op.status == operation.status
        print("✅ File persistence working correctly")
    else:
        print("❌ Operation was not restored from file")
        return False
    
    # Cleanup
    panel.cleanup()
    return True

if __name__ == "__main__":
    print("🧪 Testing Operations Persistence System\n")
    
    try:
        test_operation_serialization()
        success = test_file_persistence()
        
        if success:
            print("\n🎉 All persistence tests passed!")
            print("\nThe persistence system should now work correctly.")
            print("Try:")
            print("1. Start VCCTL and create some operations using the 'Start' button")
            print("2. Let them complete")
            print("3. Close VCCTL")
            print("4. Restart VCCTL - operations should be preserved!")
        else:
            print("\n❌ Some tests failed - persistence may not work correctly")
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
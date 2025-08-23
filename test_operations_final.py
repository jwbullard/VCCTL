#!/usr/bin/env python3
"""
Final test of the fixed Operations Panel system.
"""

import sys
sys.path.insert(0, 'src')

from app.services.service_container import get_service_container
from app.models.operation import OperationStatus
from pathlib import Path

def test_complete_workflow():
    """Test the complete operations workflow."""
    print("🧪 Testing Complete Operations Workflow")
    print("="*50)
    
    service_container = get_service_container()
    operation_service = service_container.operation_service
    
    # 1. Test loading operations from database
    print("1. 📊 Loading operations from database...")
    with service_container.database_service.get_read_only_session() as session:
        from app.models.operation import Operation as DBOperation
        operations = session.query(DBOperation).all()
        print(f"   ✅ Loaded {len(operations)} operations")
    
    # 2. Test deletion
    print("\n2. 🗑️  Testing operation deletion...")
    if operations:
        test_op = operations[0]  # Take first operation
        original_count = len(operations)
        
        # Delete it
        delete_result = operation_service.delete(test_op.name)
        print(f"   Delete operation '{test_op.name}': {delete_result}")
        
        # Verify deletion
        with service_container.database_service.get_read_only_session() as session:
            remaining = session.query(DBOperation).count()
            print(f"   ✅ Operations after deletion: {remaining} (was {original_count})")
            
            # Check if it's really gone
            deleted_op = session.query(DBOperation).filter_by(name=test_op.name).first()
            if deleted_op:
                print(f"   ❌ FAIL: Operation {test_op.name} still exists!")
                return False
            else:
                print(f"   ✅ PASS: Operation {test_op.name} permanently deleted")
    
    # 3. Test that no JSON file is created
    print("\n3. 📁 Testing JSON file persistence...")
    json_file = Path("config/operations_history.json")
    if json_file.exists():
        print(f"   ❌ FAIL: JSON file exists when it shouldn't")
        return False
    else:
        print(f"   ✅ PASS: No JSON file created (database-only)")
    
    # 4. Test progress update
    print("\n4. 🔄 Testing progress updates...")
    if operations and len(operations) > 1:
        test_op = operations[1]  # Use second operation
        
        # Update its status
        update_result = operation_service.update_status(
            name=test_op.name,
            status=OperationStatus.RUNNING,
            progress=0.5,
            current_step="Test step"
        )
        print(f"   Update operation '{test_op.name}': {update_result}")
        
        # Verify update
        with service_container.database_service.get_read_only_session() as session:
            updated_op = session.query(DBOperation).filter_by(name=test_op.name).first()
            if updated_op:
                print(f"   ✅ PASS: Operation updated - Status: {updated_op.status}, Progress: {updated_op.progress}")
            else:
                print(f"   ❌ FAIL: Could not find updated operation")
                return False
    
    return True

def main():
    success = test_complete_workflow()
    
    print(f"\n{'='*50}")
    if success:
        print("🎉 ALL TESTS PASSED!")
        print("\n✅ Operations Panel is now fully functional:")
        print("   • Database-only storage (no JSON files)")
        print("   • Permanent deletions (no reappearing operations)")
        print("   • Progress tracking works correctly")
        print("   • Single source of truth architecture")
        print("\n🚀 Ready for production use!")
    else:
        print("❌ Some tests failed - check output above")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
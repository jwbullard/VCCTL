#!/usr/bin/env python3
"""
Migrate the single missing operation from JSON to database.
"""

import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, 'src')

def migrate_missing_operation():
    """Migrate the genmic_input_Cem140Quartz03_copy Microstructure operation."""
    
    # Load JSON operations
    operations_file = Path.cwd() / "config" / "operations_history.json"
    
    with open(operations_file, 'r') as f:
        data = json.load(f)
    
    # Find the missing operation
    missing_op_data = None
    for op_data in data.get('operations', {}).values():
        if op_data['name'] == 'genmic_input_Cem140Quartz03_copy Microstructure':
            missing_op_data = op_data
            break
    
    if not missing_op_data:
        print(f"❌ Missing operation not found in JSON")
        return False
    
    print(f"📋 Found missing operation: {missing_op_data['name']}")
    print(f"   Status: {missing_op_data['status']}")
    print(f"   Type: {missing_op_data['operation_type']}")
    print(f"   Start: {missing_op_data['start_time']}")
    print(f"   End: {missing_op_data.get('end_time', 'N/A')}")
    
    try:
        from app.database.service import DatabaseService
        from app.models.operation import Operation as DBOperation
        
        # Map UI operation to database operation
        db_type_map = {
            'microstructure_generation': 'MICROSTRUCTURE',
            'hydration_simulation': 'HYDRATION'
        }
        
        db_status_map = {
            'completed': 'COMPLETED',
            'failed': 'FAILED',
            'cancelled': 'CANCELLED',
            'running': 'RUNNING',
            'pending': 'QUEUED'
        }
        
        # Parse timestamps
        start_time = datetime.fromisoformat(missing_op_data['start_time'])
        end_time = None
        if missing_op_data.get('end_time'):
            end_time = datetime.fromisoformat(missing_op_data['end_time'])
        
        # Create database operation
        db_operation = DBOperation(
            name=missing_op_data['name'],
            operation_type=db_type_map.get(missing_op_data['operation_type'], 'MICROSTRUCTURE'),
            status=db_status_map.get(missing_op_data['status'], 'COMPLETED'),
            queued_at=start_time,
            started_at=start_time,
            completed_at=end_time,
            progress=missing_op_data.get('progress', 1.0)
        )
        
        # Save to database
        db_service = DatabaseService()
        with db_service.get_session() as session:
            session.add(db_operation)
            session.commit()
            print(f"✅ Migrated operation to database successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Error migrating operation: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print(f"🔧 Migrating Missing Operation")
    print(f"{'='*40}")
    
    success = migrate_missing_operation()
    
    if success:
        print(f"\n✅ Migration completed successfully!")
        print(f"Now run finalize_database_migration.py to verify")
    else:
        print(f"\n❌ Migration failed")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
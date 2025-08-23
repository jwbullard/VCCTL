#!/usr/bin/env python3
"""
Simple database operations check.
"""

import sys
sys.path.insert(0, 'src')

from app.database.service import DatabaseService
from app.models.operation import Operation as DBOperation

def main():
    try:
        db_service = DatabaseService()
        
        with db_service.get_session() as session:
            db_operations = session.query(DBOperation).all()
            print(f"✅ Found {len(db_operations)} database operations:")
            
            for db_op in db_operations:
                print(f"   • {db_op.name}")
                print(f"     - Type: {db_op.operation_type}")
                print(f"     - Status: {db_op.status}")
                print(f"     - Queued: {db_op.queued_at}")
                print(f"     - Started: {db_op.started_at}")
                print(f"     - Completed: {db_op.completed_at}")
                print()
        
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main()
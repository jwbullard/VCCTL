#!/usr/bin/env python3
"""
Debug script to check operations in the database
"""

import sys
import os
sys.path.insert(0, 'src')

def debug_operations_database():
    """Check what operations exist in the database."""
    try:
        from app.services.service_container import get_service_container
        
        print("=== OPERATIONS DATABASE DEBUG ===")
        container = get_service_container()
        operation_service = container.operation_service
        
        print(f"Service container: {container}")
        print(f"Operation service: {operation_service}")
        
        # Get all operations
        operations = operation_service.get_all()
        print(f"\nTotal operations in database: {len(operations)}")
        
        if operations:
            print("\nOperations found:")
            for i, op in enumerate(operations, 1):
                print(f"{i}. Name: {op.name}")
                print(f"   Type: {op.type}")
                print(f"   Status: {op.status}")
                print(f"   Queue: {op.queue}")
                print(f"   Start: {op.start}")
                print(f"   Finish: {op.finish}")
                print(f"   Duration: {op.duration}s" if op.duration else "   Duration: N/A")
                print(f"   Notes: {op.notes}")
                print()
        else:
            print("No operations found in database")
            
        # Check database connection
        with container.database_service.get_session() as session:
            from app.models.operation import Operation
            count = session.query(Operation).count()
            print(f"Direct database query count: {count}")
            
            if count > 0:
                # Get recent operations
                recent_ops = session.query(Operation).order_by(Operation.start.desc()).limit(5).all()
                print(f"\nRecent operations (direct query):")
                for op in recent_ops:
                    print(f"- {op.name} ({op.type}) - {op.status} - Start: {op.start}")
                    
    except Exception as e:
        print(f"Error debugging operations database: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_operations_database()
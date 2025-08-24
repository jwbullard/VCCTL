#!/usr/bin/env python3

import sys
sys.path.append('src')

from datetime import datetime

def fix_yap14_manually():
    """Manually update YAP14 to completed status to test if UI will show it correctly."""
    
    try:
        from app.services.service_container import get_service_container
        container = get_service_container()
        
        print("=== MANUALLY FIXING YAP14 ===")
        
        with container.database_service.get_session() as session:
            from app.models.operation import Operation as DBOperation
            
            # Find YAP14 operation
            yap14 = session.query(DBOperation).filter_by(name='genmic_input_YAP14 Microstructure').first()
            
            if yap14:
                print(f"Found YAP14: Status={yap14.status}, Progress={yap14.progress}")
                
                # Update it to completed
                yap14.status = 'COMPLETED'
                yap14.progress = 1.0
                yap14.current_step = 'Generation complete'
                yap14.completed_at = datetime.now()
                
                session.commit()
                print("✅ Updated YAP14 to COMPLETED with 100% progress")
                print("Now test the Operations Panel to see if it shows as completed")
                
            else:
                print("❌ YAP14 operation not found in database")
                
                # List all operations
                all_ops = session.query(DBOperation).all()
                print(f"Found {len(all_ops)} operations:")
                for op in all_ops:
                    print(f"  - {op.name}: {op.status} ({op.progress})")
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_yap14_manually()
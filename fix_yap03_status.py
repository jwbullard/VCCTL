#!/usr/bin/env python3
"""
Directly update YAP03 status in database to COMPLETED and see if UI reflects it.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def fix_yap03_status():
    """Directly fix YAP03 status in database."""
    print("🔧 Directly Updating YAP03 Status to COMPLETED")
    print("=" * 50)
    
    try:
        from app.services.service_container import get_service_container
        container = get_service_container()
        
        print("1. Finding YAP03 operation...")
        
        with container.database_service.get_session() as session:
            from app.models.operation import Operation as DBOperation
            yap03 = session.query(DBOperation).filter(
                DBOperation.name == 'genmic_input_YAP03 Microstructure'
            ).first()
            
            if not yap03:
                print("❌ YAP03 operation not found in database")
                return
            
            print(f"   Found YAP03: {yap03.name}")
            print(f"   Current status: {yap03.status}")
            print(f"   Current progress: {getattr(yap03, 'progress', 'N/A')}")
            print(f"   Current step: {getattr(yap03, 'current_step', 'N/A')}")
            
            print("\\n2. Updating YAP03 to COMPLETED...")
            
            # Update the operation based on stdout file analysis
            yap03.status = 'COMPLETED'
            yap03.progress = 1.0
            yap03.current_step = 'Generation complete'
            
            # Set completion time if not already set
            if not getattr(yap03, 'completed_at', None):
                yap03.completed_at = datetime.utcnow()
                
            # Commit the changes
            session.commit()
            
            print(f"   ✅ Updated YAP03 status to: {yap03.status}")
            print(f"   ✅ Updated YAP03 progress to: {yap03.progress}")
            print(f"   ✅ Updated YAP03 step to: {yap03.current_step}")
            print(f"   ✅ Set completion time to: {yap03.completed_at}")
            
        print("\\n3. Verifying update...")
        
        with container.database_service.get_read_only_session() as session:
            yap03_updated = session.query(DBOperation).filter(
                DBOperation.name == 'genmic_input_YAP03 Microstructure'
            ).first()
            
            if yap03_updated:
                print(f"   Database status: {yap03_updated.status}")
                print(f"   Database progress: {getattr(yap03_updated, 'progress', 'N/A')}")
                print(f"   Database step: {getattr(yap03_updated, 'current_step', 'N/A')}")
                
                if yap03_updated.status == 'COMPLETED':
                    print("   ✅ Database update confirmed - YAP03 now shows as COMPLETED")
                else:
                    print("   ❌ Database update failed - still shows old status")
            else:
                print("   ❌ Could not find YAP03 after update")
        
        print("\\n🎯 RESULT:")
        print("✅ YAP03 status manually updated in database")
        print("📋 Next: Check Operations Panel UI to see if it shows COMPLETED")
        print("📋 If UI shows COMPLETED: monitoring loop was the problem")
        print("📋 If UI still shows RUNNING: UI refresh logic has issues")
        
    except Exception as e:
        print(f"❌ Error updating YAP03 status: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_yap03_status()
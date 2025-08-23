#!/usr/bin/env python3
"""
Fix stale operations that are marked as RUNNING but have actually completed.
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def fix_stale_operations():
    """Fix operations that are marked as RUNNING but have actually completed."""
    
    print("🔧 Fixing Stale Operations...")
    
    try:
        from app.services.service_container import get_service_container
        from app.models.operation import Operation, OperationStatus
        
        container = get_service_container()
        
        with container.database_service.get_session() as session:
            # Find all RUNNING operations
            running_ops = session.query(Operation).filter_by(status=OperationStatus.RUNNING.value).all()
            
            print(f"📊 Found {len(running_ops)} operations marked as RUNNING")
            
            for op in running_ops:
                print(f"\n🔍 Checking operation: {op.name}")
                
                # Check if operation directory exists
                operation_dir = Path(f"./Operations/{op.name}")
                if not operation_dir.exists():
                    print(f"   ❌ Operation directory not found: {operation_dir}")
                    continue
                
                # Check for completion indicators
                is_completed = False
                completion_reason = ""
                
                # Check for hydration completion files
                final_csv = operation_dir / f"HydrationOf_{op.name.split('_')[0] if '_' in op.name else op.name}.csv"
                if not final_csv.exists():
                    # Try different naming patterns
                    csv_files = list(operation_dir.glob("HydrationOf_*.csv"))
                    if csv_files:
                        final_csv = csv_files[0]
                
                if final_csv.exists():
                    is_completed = True
                    completion_reason = f"Found final CSV: {final_csv.name}"
                
                # Check for final .img files
                if not is_completed:
                    final_img_files = list(operation_dir.glob("HydrationOf_*.img.*"))
                    if final_img_files:
                        is_completed = True
                        completion_reason = f"Found final IMG files: {len(final_img_files)} files"
                
                # Check disrealnew log for completion
                if not is_completed:
                    log_file = operation_dir / "disrealnew.log"
                    if log_file.exists():
                        try:
                            with open(log_file, 'r') as f:
                                log_content = f.read()
                                if "PROGRAM COMPLETED" in log_content or "Normal termination" in log_content:
                                    is_completed = True
                                    completion_reason = "Found completion message in disrealnew.log"
                        except Exception as e:
                            print(f"   ⚠️ Could not read log file: {e}")
                
                # Check progress.json for completion
                if not is_completed:
                    progress_file = operation_dir / "progress.json"
                    if progress_file.exists():
                        try:
                            import json
                            with open(progress_file, 'r') as f:
                                progress_data = json.load(f)
                                if progress_data.get('status') == 'completed' or progress_data.get('progress', 0) >= 1.0:
                                    is_completed = True
                                    completion_reason = "Found completion in progress.json"
                        except Exception as e:
                            print(f"   ⚠️ Could not read progress file: {e}")
                
                if is_completed:
                    print(f"   ✅ Operation completed: {completion_reason}")
                    
                    # Update database status
                    op.status = OperationStatus.COMPLETED.value
                    op.progress = 1.0
                    if not op.completed_at:
                        op.completed_at = datetime.utcnow()
                    
                    session.commit()
                    print(f"   ✅ Database updated: {op.name} → COMPLETED")
                    
                else:
                    print(f"   ❓ No clear completion indicator found")
                    
                    # Check if operation has been running for a very long time (> 24 hours)
                    if op.started_at:
                        time_running = datetime.utcnow() - op.started_at
                        if time_running.total_seconds() > 24 * 3600:  # 24 hours
                            print(f"   ⏰ Operation has been running for {time_running}, marking as FAILED")
                            op.status = OperationStatus.FAILED.value
                            op.error_message = f"Operation timed out after {time_running}"
                            op.completed_at = datetime.utcnow()
                            session.commit()
                            print(f"   ✅ Database updated: {op.name} → FAILED (timeout)")
            
            print(f"\n🎯 Stale operations fix completed!")
            
    except Exception as e:
        print(f"❌ Fix failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    fix_stale_operations()
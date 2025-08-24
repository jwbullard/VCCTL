#!/usr/bin/env python3
"""
Debug the REAL monitoring system as it runs in the actual application.
This will show us what's happening vs what should be happening.
"""

import sys
import time
import threading
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def debug_real_monitoring():
    """Debug what's actually happening in the monitoring system."""
    print("🔍 DEBUGGING REAL MONITORING SYSTEM")
    print("=" * 60)
    
    try:
        from app.services.service_container import get_service_container
        container = get_service_container()
        
        print("1. Check what operations exist in database RIGHT NOW...")
        with container.database_service.get_read_only_session() as session:
            from app.models.operation import Operation as DBOperation
            operations = session.query(DBOperation).all()
            
            print(f"   Total operations in database: {len(operations)}")
            
            for op in operations:
                status = getattr(op, 'status', 'NO_STATUS')
                progress = getattr(op, 'progress', 'NO_PROGRESS')
                print(f"   {op.name}: Status={status}, Progress={progress}")
                
                # If running, check if stdout file exists and has completion
                if status == 'RUNNING':
                    print(f"     RUNNING OPERATION FOUND: {op.name}")
                    
                    # Extract folder name
                    if op.name.endswith(" Microstructure"):
                        base_name = op.name.replace(" Microstructure", "")
                        if base_name.startswith("genmic_input_"):
                            folder_name = base_name.replace("genmic_input_", "")
                        else:
                            folder_name = base_name
                        
                        ops_dir = Path("Operations") / folder_name
                        print(f"     Checking folder: {ops_dir}")
                        print(f"     Folder exists: {ops_dir.exists()}")
                        
                        if ops_dir.exists():
                            stdout_files = list(ops_dir.glob("proc_*_stdout.txt"))
                            print(f"     Stdout files: {stdout_files}")
                            
                            if stdout_files:
                                stdout_file = stdout_files[0]
                                content = stdout_file.read_text()
                                print(f"     Stdout content: {repr(content)}")
                                
                                if "stage=complete progress=1.00" in content:
                                    print(f"     ❌ PROBLEM: Operation is COMPLETE in stdout but RUNNING in database!")
                                else:
                                    print(f"     ✅ Operation still actually running")
        
        print("\\n2. Test if monitoring system components work manually...")
        
        # Import the actual panel class
        from app.windows.panels.operations_monitoring_panel import OperationsMonitoringPanel
        
        # Create panel like the real app does
        print("   Creating Operations Panel...")
        panel = OperationsMonitoringPanel(None)
        
        print(f"   Panel created successfully: {panel is not None}")
        print(f"   Monitoring active: {panel.monitoring_active}")
        print(f"   Monitor thread alive: {panel.monitor_thread.is_alive() if panel.monitor_thread else False}")
        print(f"   Operations loaded: {len(panel.operations)}")
        
        # Find any running operations in panel
        running_ops = [op for op in panel.operations.values() if op.status.value == 'running']
        print(f"   Running operations in panel: {len(running_ops)}")
        
        for op in running_ops:
            print(f"     {op.name}: {op.progress:.3f}")
        
        if running_ops:
            print("\\n3. Test manual stdout parsing on RUNNING operation...")
            test_op = running_ops[0]
            old_progress = test_op.progress
            old_status = test_op.status.value
            
            print(f"   Before parsing: Status={old_status}, Progress={old_progress:.3f}")
            
            try:
                panel._parse_operation_stdout(test_op)
                print(f"   After parsing: Status={test_op.status.value}, Progress={test_op.progress:.3f}")
                print(f"   Step: {test_op.current_step}")
                
                if test_op.status.value != old_status or test_op.progress != old_progress:
                    print("   ✅ PARSING WORKS - operation was updated")
                    
                    # Test database update
                    panel._update_operation_in_database(test_op)
                    print("   Database update called")
                    
                    # Verify in database
                    with container.database_service.get_read_only_session() as session:
                        db_op = session.query(DBOperation).filter(
                            DBOperation.name == test_op.name
                        ).first()
                        if db_op:
                            print(f"   Database now shows: Status={db_op.status}, Progress={getattr(db_op, 'progress', 'N/A')}")
                else:
                    print("   ❌ PARSING DID NOTHING - no changes detected")
                    
            except Exception as e:
                print(f"   ❌ PARSING FAILED: {e}")
                import traceback
                traceback.print_exc()
        
        else:
            print("   No running operations to test parsing on")
        
        print("\\n4. Check if monitoring thread is actually calling the parsing...")
        print("   This requires examining the monitoring loop directly...")
        
        # Let's see what the monitoring thread is actually doing
        if panel.monitor_thread and panel.monitor_thread.is_alive():
            print("   Monitoring thread is alive")
            print("   Waiting 5 seconds to see if thread processes anything...")
            
            # Capture any log output
            import logging
            logging.basicConfig(level=logging.DEBUG)
            
            time.sleep(5)
            
            print("   Check operations again after 5 seconds...")
            for op in running_ops:
                print(f"     {op.name}: Status={op.status.value}, Progress={op.progress:.3f}")
        
        panel._stop_monitoring()
        print("\\n✅ Diagnostic complete")
        
    except Exception as e:
        print(f"❌ Error in diagnostics: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_real_monitoring()
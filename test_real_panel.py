#!/usr/bin/env python3
"""
Test the actual Operations Panel as it would run in the real application.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_real_operations_panel():
    """Test the Operations Panel exactly as it runs in the real app."""
    print("🔍 Testing Real Operations Panel Behavior")
    print("=" * 50)
    
    try:
        from app.services.service_container import get_service_container
        from app.windows.panels.operations_monitoring_panel import OperationsMonitoringPanel
        
        container = get_service_container()
        
        print("1. Creating Operations Panel (like real app)...")
        panel = OperationsMonitoringPanel(None)  # None for main_window
        
        print(f"   Panel created: {panel is not None}")
        print(f"   Has logger: {hasattr(panel, 'logger')}")
        print(f"   Has operations: {hasattr(panel, 'operations')}")
        print(f"   Operations count: {len(panel.operations)}")
        print(f"   Monitoring active: {panel.monitoring_active}")
        print(f"   Monitor thread alive: {panel.monitor_thread.is_alive() if panel.monitor_thread else False}")
        
        print("\\n2. Finding RUNNING operations...")
        running_ops = [op for op in panel.operations.values() if op.status.value == 'running']
        print(f"   Found {len(running_ops)} running operations")
        
        for op in running_ops:
            print(f"   {op.name}: {op.status.value} {op.progress:.3f} - {op.current_step}")
            
            print(f"\\n3. Testing manual stdout parsing for {op.name}...")
            old_progress = op.progress
            old_status = op.status.value
            old_step = op.current_step
            
            try:
                panel._parse_operation_stdout(op)
                print(f"   Before: Status={old_status}, Progress={old_progress:.3f}, Step='{old_step}'")
                print(f"   After:  Status={op.status.value}, Progress={op.progress:.3f}, Step='{op.current_step}'")
                
                if op.progress != old_progress or op.status.value != old_status:
                    print(f"   ✅ PARSING WORKED - operation updated!")
                    
                    # Check if database was updated
                    print(f"\\n4. Checking if database was updated...")
                    with container.database_service.get_read_only_session() as session:
                        from app.models.operation import Operation as DBOperation
                        db_op = session.query(DBOperation).filter(
                            DBOperation.name == op.name
                        ).first()
                        
                        if db_op:
                            print(f"   DB Status: {db_op.status}")
                            print(f"   DB Progress: {getattr(db_op, 'progress', 'N/A')}")
                            print(f"   DB Step: {getattr(db_op, 'current_step', 'N/A')}")
                            
                            if db_op.status != 'RUNNING' and old_status == 'running':
                                print(f"   ✅ DATABASE UPDATED - status changed!")
                            else:
                                print(f"   ❌ Database not updated yet")
                        else:
                            print(f"   ❌ Operation not found in database")
                else:
                    print(f"   ❌ PARSING DID NOTHING - no changes detected")
                    
            except Exception as e:
                print(f"   ❌ PARSING ERROR: {e}")
                import traceback
                traceback.print_exc()
        
        print("\\n5. Testing monitoring loop status...")
        if panel.monitor_thread:
            print(f"   Thread alive: {panel.monitor_thread.is_alive()}")
            print(f"   Thread name: {panel.monitor_thread.name}")
            print(f"   Thread daemon: {panel.monitor_thread.daemon}")
        else:
            print(f"   ❌ No monitor thread!")
        
        # Stop monitoring cleanly
        panel._stop_monitoring()
        print("\\n✅ Test completed")
        
    except Exception as e:
        print(f"❌ Error testing real panel: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_real_operations_panel()
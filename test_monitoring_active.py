#!/usr/bin/env python3
"""
Test if the monitoring system is actually running by checking if it processes the YAP03 operation.
"""

import sys
import os
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_monitoring_active():
    """Test if monitoring is actually processing operations."""
    print("🔍 Testing If Monitoring System Is Actually Running")
    print("=" * 60)
    
    try:
        from app.services.service_container import get_service_container
        container = get_service_container()
        
        print("1. Check YAP03 current database state...")
        
        with container.database_service.get_read_only_session() as session:
            from app.models.operation import Operation as DBOperation
            yap03 = session.query(DBOperation).filter(DBOperation.name == 'genmic_input_YAP03 Microstructure').first()
            
            if yap03:
                print(f"   YAP03 Status: {yap03.status}")
                print(f"   YAP03 Progress: {getattr(yap03, 'progress', 'N/A')}")
                print(f"   YAP03 Step: {getattr(yap03, 'current_step', 'N/A')}")
                initial_progress = getattr(yap03, 'progress', 0.0)
            else:
                print("   ❌ YAP03 operation not found in database")
                return
        
        print("\\n2. Simulate what Operations Panel should do...")
        
        # Create an Operations Panel instance to test monitoring
        from app.windows.panels.operations_monitoring_panel import OperationsMonitoringPanel
        
        # This would normally be created by the GUI, but we can test the logic
        print("   Creating Operations Panel instance...")
        
        panel = OperationsMonitoringPanel(container)
        
        print(f"   Monitoring active: {panel.monitoring_active}")
        print(f"   Update interval: {panel.update_interval}")
        print(f"   Operations count: {len(panel.operations)}")
        
        # Find YAP03 in operations
        yap03_op = None
        for op in panel.operations.values():
            if "YAP03" in op.name:
                yap03_op = op
                break
        
        if yap03_op:
            print(f"   Found YAP03 in operations: {yap03_op.name}")
            print(f"   Status: {yap03_op.status.value}")
            print(f"   Progress: {yap03_op.progress}")
            print(f"   Step: {yap03_op.current_step}")
        else:
            print("   ❌ YAP03 not found in operations")
            return
        
        print("\\n3. Manually trigger stdout parsing...")
        
        # Manually call the stdout parsing to see if it works
        initial_status = yap03_op.status
        initial_progress = yap03_op.progress
        
        print("   Calling _parse_operation_stdout manually...")
        panel._parse_operation_stdout(yap03_op)
        
        print(f"   After parsing:")
        print(f"     Status: {initial_status.value} → {yap03_op.status.value}")
        print(f"     Progress: {initial_progress} → {yap03_op.progress}")
        print(f"     Step: {yap03_op.current_step}")
        
        if yap03_op.status.value == 'completed':
            print("   ✅ Manual parsing worked - operation marked complete")
            
            # Check if database was updated
            print("\\n4. Check if database was updated...")
            
            with container.database_service.get_read_only_session() as session:
                yap03_updated = session.query(DBOperation).filter(DBOperation.name == 'genmic_input_YAP03 Microstructure').first()
                
                if yap03_updated:
                    print(f"   Database Status: {yap03_updated.status}")
                    print(f"   Database Progress: {getattr(yap03_updated, 'progress', 'N/A')}")
                    
                    if yap03_updated.status == 'COMPLETED':
                        print("   ✅ Database was updated - operation marked complete in DB")
                    else:
                        print("   ❌ Database was NOT updated - still shows old status")
                        print("   Problem: _update_operation_in_database() not working")
        else:
            print("   ❌ Manual parsing failed - operation not marked complete")
            print("   Problem: stdout parsing logic has issues")
        
        print("\\n5. Check monitoring thread...")
        
        if panel.monitor_thread:
            print(f"   Monitor thread alive: {panel.monitor_thread.is_alive()}")
        else:
            print("   ❌ No monitor thread found")
        
        # Stop monitoring
        panel._stop_monitoring()
        
        print("\\n🎯 DIAGNOSIS:")
        print("=" * 60)
        
        if yap03_op and yap03_op.status.value == 'completed':
            print("✅ Stdout parsing works when called manually")
            print("❓ Problem: monitoring loop not calling this logic frequently enough")
            print("❓ OR: monitoring loop not running at all")
        else:
            print("❌ Stdout parsing doesn't work even when called manually")
            print("❓ Problem: logic issues in _parse_operation_stdout() method")
        
    except Exception as e:
        print(f"❌ Error testing monitoring: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_monitoring_active()
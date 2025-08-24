#!/usr/bin/env python3
"""
Test if the monitoring thread is actually running.
"""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_monitoring_thread():
    """Test if monitoring thread is running and working."""
    print("🔍 Testing Monitoring Thread Actual Status")
    print("=" * 50)
    
    try:
        from app.services.service_container import get_service_container
        from app.windows.panels.operations_monitoring_panel import OperationsMonitoringPanel
        
        container = get_service_container()
        
        print("1. Creating Operations Panel...")
        panel = OperationsMonitoringPanel(None)  # Don't need main window for this test
        
        print(f"   Monitoring active: {panel.monitoring_active}")
        print(f"   Monitor thread exists: {panel.monitor_thread is not None}")
        
        if panel.monitor_thread:
            print(f"   Monitor thread alive: {panel.monitor_thread.is_alive()}")
            print(f"   Monitor thread name: {panel.monitor_thread.name}")
            print(f"   Monitor thread daemon: {panel.monitor_thread.daemon}")
        
        print("\\n2. Wait a few seconds and check thread status...")
        time.sleep(3)
        
        if panel.monitor_thread:
            print(f"   Monitor thread still alive: {panel.monitor_thread.is_alive()}")
        
        print("\\n3. Check operations loaded...")
        print(f"   Operations count: {len(panel.operations)}")
        for op_id, op in panel.operations.items():
            print(f"     {op.name}: {op.status.value} ({op.progress:.3f})")
        
        print("\\n4. Test manual monitoring call...")
        try:
            panel._update_operations()
            print("   ✅ Manual _update_operations() succeeded")
        except Exception as e:
            print(f"   ❌ Manual _update_operations() failed: {e}")
            import traceback
            traceback.print_exc()
        
        print("\\n5. Check for running operations that should be monitored...")
        running_ops = [op for op in panel.operations.values() 
                      if op.status.value in ['running', 'paused']]
        print(f"   Running operations: {len(running_ops)}")
        
        for op in running_ops:
            print(f"   {op.name}:")
            print(f"     Status: {op.status.value}")
            print(f"     Progress: {op.progress}")
            print(f"     Step: {op.current_step}")
            print(f"     Has metadata: {hasattr(op, 'metadata')}")
            if hasattr(op, 'metadata'):
                print(f"     Source: {op.metadata.get('source', 'unknown')}")
        
        # Let monitoring run for a few more seconds
        print("\\n6. Let monitoring run for 5 seconds...")
        time.sleep(5)
        
        print("\\n7. Check if any operations changed...")
        for op in running_ops:
            print(f"   {op.name}: {op.status.value} ({op.progress:.3f}) - {op.current_step}")
        
        # Stop monitoring cleanly
        panel._stop_monitoring()
        print("\\n✅ Test completed - monitoring stopped")
        
    except Exception as e:
        print(f"❌ Error testing monitoring thread: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_monitoring_thread()
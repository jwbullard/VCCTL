#!/usr/bin/env python3
"""
Debug what the monitoring loop is actually doing.
"""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def debug_monitoring_loop():
    """Debug the monitoring loop behavior."""
    print("🔍 Debugging Monitoring Loop Behavior")
    print("=" * 50)
    
    from app.services.service_container import get_service_container
    from app.windows.panels.operations_monitoring_panel import OperationsMonitoringPanel
    
    container = get_service_container()
    panel = OperationsMonitoringPanel(None)
    
    print(f"Monitoring active: {panel.monitoring_active}")
    print(f"Thread alive: {panel.monitor_thread.is_alive() if panel.monitor_thread else False}")
    print(f"Update interval: {panel.update_interval} seconds")
    
    # Find YAP13
    yap13 = None
    for op in panel.operations.values():
        if 'YAP13' in op.name:
            yap13 = op
            break
    
    if not yap13:
        print("❌ YAP13 not found")
        return
    
    print(f"\\nYAP13 initial state:")
    print(f"  Status: {yap13.status.value}")
    print(f"  Progress: {yap13.progress:.3f}")
    print(f"  Step: '{yap13.current_step}'")
    print(f"  Has process: {hasattr(yap13, 'process') and yap13.process is not None}")
    print(f"  Has metadata: {hasattr(yap13, 'metadata')}")
    if hasattr(yap13, 'metadata'):
        print(f"  Metadata source: {yap13.metadata.get('source', 'unknown')}")
    
    print(f"\\nWaiting 5 seconds to see if monitoring loop updates YAP13...")
    initial_progress = yap13.progress
    initial_step = yap13.current_step
    
    # Wait and check if monitoring updates the operation
    for i in range(5):
        time.sleep(1)
        print(f"  Second {i+1}: Progress={yap13.progress:.3f}, Step='{yap13.current_step}'")
        
        if yap13.progress != initial_progress or yap13.current_step != initial_step:
            print("  ✅ Monitoring loop IS updating YAP13!")
            break
    else:
        print("  ❌ Monitoring loop is NOT updating YAP13")
    
    print(f"\\nFinal YAP13 state:")
    print(f"  Status: {yap13.status.value}")
    print(f"  Progress: {yap13.progress:.3f}")
    print(f"  Step: '{yap13.current_step}'")
    
    # Check if it's being skipped by monitoring logic
    print(f"\\nChecking monitoring skip conditions...")
    
    # Check the same conditions as _update_operations
    is_database_sourced = hasattr(yap13, 'metadata') and yap13.metadata.get('source') == 'database'
    has_process_handle = hasattr(yap13, 'process') and yap13.process is not None
    
    print(f"  Database sourced: {is_database_sourced}")
    print(f"  Has process handle: {has_process_handle}")
    
    # Check stdout file monitoring eligibility
    can_monitor_stdout = False
    if is_database_sourced and yap13.operation_type.value == 'microstructure_generation':
        try:
            import os
            import glob
            operation_name = yap13.name
            if operation_name.endswith(" Microstructure"):
                base_name = operation_name.replace(" Microstructure", "")
                if base_name.startswith("genmic_input_"):
                    folder_name = base_name.replace("genmic_input_", "")
                else:
                    folder_name = base_name
                
                operations_dir = os.path.join("Operations", folder_name)
                if os.path.exists(operations_dir):
                    progress_file = os.path.join(operations_dir, "genmic_progress.txt")
                    if os.path.exists(progress_file):
                        can_monitor_stdout = True
                        print(f"  Progress file exists: {progress_file}")
        except Exception as e:
            print(f"  Error checking stdout: {e}")
    
    print(f"  Can monitor stdout: {can_monitor_stdout}")
    
    # Final skip logic check
    should_skip = is_database_sourced and not has_process_handle and not can_monitor_stdout
    print(f"  Should be skipped by monitoring: {should_skip}")
    
    if should_skip:
        print("\\n❌ YAP13 IS BEING SKIPPED by monitoring loop!")
        print("   This is why progress isn't updating automatically.")
    else:
        print("\\n✅ YAP13 should be processed by monitoring loop")
        print("   There might be another issue preventing updates.")
    
    panel._stop_monitoring()

if __name__ == "__main__":
    debug_monitoring_loop()
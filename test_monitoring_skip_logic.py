#!/usr/bin/env python3
"""
Test the exact monitoring skip logic to see if YAP03 is being processed.
"""

import sys
import os
import glob
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_monitoring_skip_logic():
    """Test the monitoring skip logic for YAP03."""
    print("🔍 Testing Monitoring Skip Logic for YAP03")
    print("=" * 50)
    
    try:
        from app.windows.panels.operations_monitoring_panel import Operation, OperationType, OperationStatus
        
        # Create YAP03 operation exactly as it would be loaded from database
        operation = Operation(
            id="genmic_input_YAP03 Microstructure",
            name="genmic_input_YAP03 Microstructure",
            operation_type=OperationType.MICROSTRUCTURE_GENERATION,
            status=OperationStatus.RUNNING,
            progress=0.05,
            current_step="Process started",
            metadata={"source": "database"}
        )
        
        print(f"Operation: {operation.name}")
        print(f"Status: {operation.status.value}")
        print(f"Type: {operation.operation_type.value}")
        
        print("\nTesting skip logic step by step...")
        
        # Step 1: Check if database sourced
        is_database_sourced = hasattr(operation, 'metadata') and operation.metadata.get('source') == 'database'
        print(f"1. Is database sourced: {is_database_sourced}")
        
        # Step 2: Check if has process handle
        has_process_handle = hasattr(operation, 'process') and operation.process is not None
        print(f"2. Has process handle: {has_process_handle}")
        
        # Step 3: Check if can monitor stdout (this is the critical test)
        can_monitor_stdout = False
        if is_database_sourced and operation.operation_type == OperationType.MICROSTRUCTURE_GENERATION:
            print("3. Testing stdout file detection...")
            try:
                operation_name = operation.name
                print(f"   Operation name: {operation_name}")
                
                if operation_name.endswith(" Microstructure"):
                    base_name = operation_name.replace(" Microstructure", "")
                    print(f"   Base name: {base_name}")
                    
                    if base_name.startswith("genmic_input_"):
                        folder_name = base_name.replace("genmic_input_", "")
                    else:
                        folder_name = base_name
                    
                    print(f"   Folder name: {folder_name}")
                    
                    operations_dir = os.path.join("Operations", folder_name)
                    print(f"   Operations dir: {operations_dir}")
                    print(f"   Directory exists: {os.path.exists(operations_dir)}")
                    
                    if os.path.exists(operations_dir):
                        stdout_files = glob.glob(os.path.join(operations_dir, "proc_*_stdout.txt"))
                        print(f"   Stdout files found: {len(stdout_files)}")
                        
                        if stdout_files:
                            can_monitor_stdout = True
                            for f in stdout_files:
                                print(f"     - {os.path.basename(f)}")
                        else:
                            print("     ❌ No proc_*_stdout.txt files found")
                    else:
                        print("     ❌ Operations directory does not exist")
                        
            except Exception as e:
                print(f"   ❌ Error in stdout detection: {e}")
        
        print(f"3. Can monitor stdout: {can_monitor_stdout}")
        
        # Step 4: Final skip decision
        should_skip = is_database_sourced and not has_process_handle and not can_monitor_stdout
        
        print(f"\nFinal skip logic:")
        print(f"  Database sourced: {is_database_sourced}")
        print(f"  No process handle: {not has_process_handle}")
        print(f"  Cannot monitor stdout: {not can_monitor_stdout}")
        print(f"  Should skip (AND of above): {should_skip}")
        
        print(f"\n🎯 RESULT:")
        if should_skip:
            print("❌ YAP03 WILL BE SKIPPED - this explains why progress isn't updating")
            print("   Problem: stdout file detection logic is not working")
        else:
            print("✅ YAP03 WILL NOT BE SKIPPED - monitoring should process it")
            print("   Problem: monitoring loop is not running or not updating database")
        
        # If not skipped, test if the status check would let it be processed
        if not should_skip:
            print(f"\n4. Testing status check...")
            if operation.status in [OperationStatus.RUNNING, OperationStatus.PAUSED]:
                print("✅ Status check passes - operation would be processed")
            else:
                print(f"❌ Status check fails - status {operation.status.value} not in [RUNNING, PAUSED]")
        
    except Exception as e:
        print(f"❌ Error testing skip logic: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_monitoring_skip_logic()
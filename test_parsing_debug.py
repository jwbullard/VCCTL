#!/usr/bin/env python3
"""
Debug exactly what happens during _parse_operation_stdout.
"""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def debug_parsing():
    """Debug _parse_operation_stdout step by step."""
    print("🔍 Debugging _parse_operation_stdout Method")
    print("=" * 50)
    
    # Set up detailed logging
    logging.basicConfig(level=logging.DEBUG, format='%(name)s - %(levelname)s - %(message)s')
    
    try:
        from app.services.service_container import get_service_container
        from app.windows.panels.operations_monitoring_panel import OperationsMonitoringPanel, OperationType
        
        container = get_service_container()
        panel = OperationsMonitoringPanel(None)
        
        print("1. Finding RUNNING operation...")
        running_ops = [op for op in panel.operations.values() if op.status.value == 'running']
        
        if not running_ops:
            print("❌ No running operations found!")
            return
        
        operation = running_ops[0]
        print(f"   Found: {operation.name}")
        print(f"   Type: {operation.operation_type}")
        print(f"   Status: {operation.status.value}")
        print(f"   Progress: {operation.progress}")
        
        print("\\n2. Checking operation type condition...")
        is_microstructure = operation.operation_type == OperationType.MICROSTRUCTURE_GENERATION
        print(f"   Is MICROSTRUCTURE_GENERATION: {is_microstructure}")
        print(f"   Operation type value: {operation.operation_type.value}")
        print(f"   Expected: {OperationType.MICROSTRUCTURE_GENERATION.value}")
        
        if not is_microstructure:
            print("❌ Operation type check failed!")
            return
        
        print("\\n3. Checking name parsing...")
        operation_name = operation.name
        print(f"   Operation name: '{operation_name}'")
        
        ends_with_microstructure = operation_name.endswith(" Microstructure")
        print(f"   Ends with ' Microstructure': {ends_with_microstructure}")
        
        if ends_with_microstructure:
            base_name = operation_name.replace(" Microstructure", "")
            print(f"   Base name: '{base_name}'")
            
            if base_name.startswith("genmic_input_"):
                folder_name = base_name.replace("genmic_input_", "")
                print(f"   Folder name: '{folder_name}'")
            else:
                folder_name = base_name
                print(f"   Folder name (no prefix): '{folder_name}'")
        else:
            print("❌ Name doesn't end with ' Microstructure'!")
            return
        
        print("\\n4. Checking file path...")
        import os
        operations_dir = os.path.join("Operations", folder_name)
        progress_file = os.path.join(operations_dir, "genmic_progress.txt")
        
        print(f"   Operations dir: '{operations_dir}'")
        print(f"   Progress file: '{progress_file}'")
        print(f"   Dir exists: {os.path.exists(operations_dir)}")
        print(f"   File exists: {os.path.exists(progress_file)}")
        
        if not os.path.exists(progress_file):
            print("❌ Progress file doesn't exist!")
            return
        
        print("\\n5. Reading file content...")
        try:
            with open(progress_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                print(f"   Raw content: {repr(content)}")
                print(f"   Content length: {len(content)}")
                print(f"   Content: '{content}'")
        except Exception as e:
            print(f"❌ Error reading file: {e}")
            return
        
        print("\\n6. Testing _parse_simple_progress...")
        old_progress = operation.progress
        old_status = operation.status.value
        old_step = operation.current_step
        
        try:
            result = panel._parse_simple_progress(operation, content)
            print(f"   Parse result: {result}")
            print(f"   Before: Status={old_status}, Progress={old_progress:.3f}, Step='{old_step}'")
            print(f"   After:  Status={operation.status.value}, Progress={operation.progress:.3f}, Step='{operation.current_step}'")
            
            if result:
                print("✅ _parse_simple_progress worked!")
            else:
                print("❌ _parse_simple_progress returned False")
                
        except Exception as e:
            print(f"❌ Error in _parse_simple_progress: {e}")
            import traceback
            traceback.print_exc()
        
        print("\\n7. Now testing full _parse_operation_stdout...")
        
        # Reset operation to test full method
        operation.progress = old_progress
        operation.status = panel.operations[operation.id].status  # Reset from original
        operation.current_step = old_step
        
        try:
            panel._parse_operation_stdout(operation)
            print(f"   After full method: Status={operation.status.value}, Progress={operation.progress:.3f}")
        except Exception as e:
            print(f"❌ Error in _parse_operation_stdout: {e}")
            import traceback
            traceback.print_exc()
        
        panel._stop_monitoring()
        
    except Exception as e:
        print(f"❌ Error in debug: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_parsing()
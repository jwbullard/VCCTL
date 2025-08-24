#!/usr/bin/env python3
"""
Debug script to test stdout parsing logic step by step and find where it's failing.
"""

import sys
import os
import glob
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def debug_stdout_parsing():
    """Debug the stdout parsing logic step by step."""
    print("🔍 Debugging STDOUT Progress Parsing Step-by-Step")
    print("=" * 60)
    
    try:
        from app.windows.panels.operations_monitoring_panel import Operation, OperationType, OperationStatus
        
        print("1. Create test operation (YAP03)...")
        
        # Create the exact operation that should be running
        operation = Operation(
            id="genmic_input_YAP03 Microstructure",
            name="genmic_input_YAP03 Microstructure",
            operation_type=OperationType.MICROSTRUCTURE_GENERATION,
            status=OperationStatus.RUNNING,
            progress=0.05,  # Current database state
            current_step="Process started",
            metadata={"source": "database"}
        )
        
        print(f"   Initial status: {operation.status.value}")
        print(f"   Initial progress: {operation.progress}")
        print(f"   Initial step: {operation.current_step}")
        
        print("\\n2. Test stdout file detection...")
        
        # Simulate _parse_operation_stdout logic exactly
        stdout_path = None
        
        if hasattr(operation, 'stdout_file') and operation.stdout_file:
            stdout_path = operation.stdout_file
            print(f"   Using operation.stdout_file: {stdout_path}")
        else:
            print("   Reconstructing stdout file path...")
            operation_name = operation.name
            if operation_name.endswith(" Microstructure"):
                base_name = operation_name.replace(" Microstructure", "")
                print(f"   Base name: {base_name}")
                
                # Remove "genmic_input_" prefix if present to get actual folder name
                if base_name.startswith("genmic_input_"):
                    folder_name = base_name.replace("genmic_input_", "")
                else:
                    folder_name = base_name
                
                print(f"   Folder name: {folder_name}")
                
                # Look for process stdout file with GENMIC_PROGRESS messages
                operations_dir = os.path.join("Operations", folder_name)
                print(f"   Operations dir: {operations_dir}")
                print(f"   Directory exists: {os.path.exists(operations_dir)}")
                
                if os.path.exists(operations_dir):
                    # Find proc_*_stdout.txt files in the folder
                    stdout_files = glob.glob(os.path.join(operations_dir, "proc_*_stdout.txt"))
                    print(f"   Stdout files found: {len(stdout_files)}")
                    
                    if stdout_files:
                        # Use the most recent stdout file
                        stdout_path = max(stdout_files, key=os.path.getctime)
                        print(f"   Selected stdout path: {stdout_path}")
                    else:
                        print("   ❌ No process stdout files found")
                else:
                    print("   ❌ Operations directory not found")
        
        if not stdout_path:
            print("   ❌ CRITICAL: No stdout path found - monitoring will fail")
            return
        
        print("\\n3. Test file reading...")
        
        if not hasattr(operation, '_stdout_position'):
            operation._stdout_position = 0
        
        print(f"   Initial file position: {operation._stdout_position}")
        
        try:
            with open(stdout_path, 'r', encoding='utf-8') as f:
                f.seek(operation._stdout_position)
                new_content = f.read()
                operation._stdout_position = f.tell()
                
                print(f"   Content length: {len(new_content)} characters")
                print(f"   New file position: {operation._stdout_position}")
                print(f"   Content preview: {new_content[:200]}...")
                
                print("\\n4. Test line processing...")
                
                lines = new_content.strip().split('\\n')
                print(f"   Total lines: {len(lines)}")
                
                progress_updates = 0
                for i, line in enumerate(lines, 1):
                    if line.strip():
                        print(f"   Line {i}: {line}")
                        
                        initial_status = operation.status
                        initial_progress = operation.progress
                        initial_step = operation.current_step
                        
                        # This is the critical call
                        result = operation.parse_genmic_progress(line.strip())
                        
                        if result:
                            progress_updates += 1
                            print(f"     ✅ Progress updated:")
                            print(f"       Status: {initial_status.value} → {operation.status.value}")
                            print(f"       Progress: {initial_progress:.3f} → {operation.progress:.3f}")
                            print(f"       Step: '{initial_step}' → '{operation.current_step}'")
                            
                            # Check if completed
                            if operation.status == OperationStatus.COMPLETED:
                                print(f"     🎯 OPERATION MARKED AS COMPLETED!")
                                break
                        else:
                            print(f"     ❌ No progress update from this line")
                
                print(f"\\n   Final operation state:")
                print(f"     Status: {operation.status.value}")
                print(f"     Progress: {operation.progress:.3f}")
                print(f"     Step: {operation.current_step}")
                print(f"     Total progress updates: {progress_updates}")
                
        except (IOError, OSError) as e:
            print(f"   ❌ Error reading stdout file: {e}")
        
        print("\\n🎯 DIAGNOSIS:")
        print("=" * 60)
        
        if operation.status == OperationStatus.COMPLETED:
            print("✅ Stdout parsing WORKS - operation should be marked complete")
            print("❓ Problem likely: monitoring loop not calling this logic")
            print("❓ OR: database updates not being saved")
        else:
            print("❌ Stdout parsing FAILED - progress messages not processed correctly")
            print("❓ Problem: parse_genmic_progress() method has issues")
        
        print("\\nNext steps:")
        print("• If parsing works: Check monitoring loop execution")
        print("• If parsing fails: Check parse_genmic_progress() method")
        
    except Exception as e:
        print(f"❌ Error debugging stdout parsing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_stdout_parsing()
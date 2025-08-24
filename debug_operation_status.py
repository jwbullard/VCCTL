#!/usr/bin/env python3
"""
Debug script to check the actual status of operations in the database and understand
why progress monitoring isn't working.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def debug_operation_status():
    """Debug the current operation status and monitoring setup."""
    print("🔍 Debugging Operation Status & Progress Monitoring")
    print("=" * 60)
    
    try:
        from app.services.service_container import get_service_container
        container = get_service_container()
        
        print("1. Checking database operations...")
        
        with container.database_service.get_read_only_session() as session:
            from app.models.operation import Operation as DBOperation
            db_operations = session.query(DBOperation).all()
            
            print(f"   Total operations in database: {len(db_operations)}")
            
            for db_op in db_operations:
                print(f"\\n   Operation: {db_op.name}")
                print(f"     Type: {db_op.operation_type}")
                print(f"     Status: {db_op.status}")
                print(f"     Progress: {getattr(db_op, 'progress', 'N/A')}")
                print(f"     Current Step: {getattr(db_op, 'current_step', 'N/A')}")
                print(f"     Started: {getattr(db_op, 'started_at', 'N/A')}")
                print(f"     Completed: {getattr(db_op, 'completed_at', 'N/A')}")
        
        print("\\n2. Checking for RUNNING operations...")
        
        with container.database_service.get_read_only_session() as session:
            running_ops = session.query(DBOperation).filter(DBOperation.status == 'RUNNING').all()
            
            print(f"   RUNNING operations: {len(running_ops)}")
            
            for op in running_ops:
                print(f"     - {op.name} (type: {op.operation_type})")
                
                # Check if this operation has stdout files
                import os, glob
                if "Microstructure" in op.name:
                    base_name = op.name.replace(" Microstructure", "")
                    if base_name.startswith("genmic_input_"):
                        folder_name = base_name.replace("genmic_input_", "")
                    else:
                        folder_name = base_name
                    
                    operations_dir = os.path.join("Operations", folder_name)
                    print(f"       Expected folder: {operations_dir}")
                    print(f"       Folder exists: {os.path.exists(operations_dir)}")
                    
                    if os.path.exists(operations_dir):
                        stdout_files = glob.glob(os.path.join(operations_dir, "proc_*_stdout.txt"))
                        print(f"       Stdout files: {len(stdout_files)}")
                        
                        for stdout_file in stdout_files:
                            print(f"         - {os.path.basename(stdout_file)}")
                            
                            # Check if file has recent content
                            try:
                                stat = os.stat(stdout_file)
                                from datetime import datetime
                                mtime = datetime.fromtimestamp(stat.st_mtime)
                                size = stat.st_size
                                print(f"           Modified: {mtime}, Size: {size} bytes")
                                
                                # Check for GENMIC_PROGRESS messages
                                with open(stdout_file, 'r') as f:
                                    content = f.read()
                                    progress_lines = [line for line in content.split('\\n') if 'GENMIC_PROGRESS' in line]
                                    print(f"           GENMIC_PROGRESS messages: {len(progress_lines)}")
                                    
                                    if progress_lines:
                                        print(f"           First: {progress_lines[0][:80]}...")
                                        print(f"           Last: {progress_lines[-1][:80]}...")
                                    
                            except Exception as e:
                                print(f"           Error reading file: {e}")
        
        print("\\n3. Testing Operations Panel logic...")
        
        # Simulate what Operations Panel does
        from app.windows.panels.operations_monitoring_panel import OperationsMonitoringPanel, Operation, OperationType, OperationStatus
        
        # This would be how the Operations Panel loads operations
        print("   Simulating Operations Panel database loading...")
        
        # Convert database operations to UI operations (same as Operations Panel does)
        ui_operations = {}
        with container.database_service.get_read_only_session() as session:
            db_operations = session.query(DBOperation).all()
            
            for db_op in db_operations:
                try:
                    # Simulate _convert_db_operation_to_ui_operation
                    status_mapping = {
                        'QUEUED': OperationStatus.PENDING,
                        'RUNNING': OperationStatus.RUNNING,  
                        'COMPLETED': OperationStatus.COMPLETED,
                        'FAILED': OperationStatus.FAILED,
                        'CANCELLED': OperationStatus.CANCELLED,
                    }
                    
                    type_mapping = {
                        'HYDRATION': OperationType.HYDRATION_SIMULATION,
                        'MICROSTRUCTURE': OperationType.MICROSTRUCTURE_GENERATION,
                    }
                    
                    ui_status = status_mapping.get(db_op.status, OperationStatus.PENDING)
                    ui_type = type_mapping.get(db_op.operation_type, OperationType.BATCH_OPERATION)
                    
                    ui_operation = Operation(
                        id=db_op.name,
                        name=db_op.name,
                        operation_type=ui_type,
                        status=ui_status,
                        progress=1.0 if ui_status == OperationStatus.COMPLETED else 0.0,
                        metadata={"source": "database"}
                    )
                    
                    ui_operations[ui_operation.id] = ui_operation
                    print(f"     UI Operation: {ui_operation.name} -> {ui_status.value}")
                    
                except Exception as e:
                    print(f"     Error converting {db_op.name}: {e}")
        
        print("\\n4. Testing monitoring logic...")
        
        for operation in ui_operations.values():
            if operation.status == OperationStatus.RUNNING:
                print(f"   Testing monitoring for: {operation.name}")
                
                is_database_sourced = hasattr(operation, 'metadata') and operation.metadata.get('source') == 'database'
                has_process_handle = hasattr(operation, 'process') and operation.process is not None
                
                print(f"     Database sourced: {is_database_sourced}")
                print(f"     Has process handle: {has_process_handle}")
                
                # Test stdout monitoring logic
                if operation.operation_type == OperationType.MICROSTRUCTURE_GENERATION:
                    can_monitor_stdout = False
                    try:
                        operation_name = operation.name
                        if operation_name.endswith(" Microstructure"):
                            base_name = operation_name.replace(" Microstructure", "")
                            if base_name.startswith("genmic_input_"):
                                folder_name = base_name.replace("genmic_input_", "")
                            else:
                                folder_name = base_name
                            
                            operations_dir = os.path.join("Operations", folder_name)
                            if os.path.exists(operations_dir):
                                stdout_files = glob.glob(os.path.join(operations_dir, "proc_*_stdout.txt"))
                                if stdout_files:
                                    can_monitor_stdout = True
                    except Exception as e:
                        print(f"     Error checking stdout files: {e}")
                    
                    print(f"     Can monitor stdout: {can_monitor_stdout}")
                    
                    should_skip = is_database_sourced and not has_process_handle and not can_monitor_stdout
                    print(f"     Should skip monitoring: {should_skip}")
                    
                    if not should_skip:
                        print("     ✅ Operation WILL be monitored")
                    else:
                        print("     ❌ Operation will be SKIPPED from monitoring")
        
        print("\\n🎯 DIAGNOSIS SUMMARY:")
        print("=" * 60)
        print("• Check above for RUNNING operations and their file status")
        print("• Look for operations that should be monitored but aren't")
        print("• Verify GENMIC_PROGRESS messages exist in stdout files")
        print("• Confirm Operations Panel monitoring logic is correct")
        
    except Exception as e:
        print(f"❌ Error debugging operation status: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_operation_status()
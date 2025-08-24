#!/usr/bin/env python3
"""
Debug exactly what happens with YAP03 in the monitoring loop.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def debug_yap03_monitoring():
    """Debug YAP03 operation handling in monitoring loop."""
    print("🔍 Debugging YAP03 Monitoring Logic")
    print("=" * 50)
    
    try:
        from app.services.service_container import get_service_container
        from app.windows.panels.operations_monitoring_panel import OperationStatus, OperationType
        container = get_service_container()
        
        print("1. Check YAP03 database state...")
        with container.database_service.get_read_only_session() as session:
            from app.models.operation import Operation as DBOperation
            yap03 = session.query(DBOperation).filter(
                DBOperation.name == 'genmic_input_YAP03 Microstructure'
            ).first()
            
            if not yap03:
                print("❌ YAP03 not found in database")
                return
            
            print(f"   Database Status: {yap03.status}")
            print(f"   Database Progress: {getattr(yap03, 'progress', 'N/A')}")
        
        print("\n2. Simulate monitoring loop conditions...")
        
        # Create mock operation like in monitoring loop
        from app.windows.panels.operations_monitoring_panel import Operation
        
        # Convert database operation to UI operation (like the panel does)
        operation = Operation(
            id=yap03.name,
            name=yap03.name,
            operation_type=OperationType.MICROSTRUCTURE_GENERATION,
            status=OperationStatus.COMPLETED if yap03.status == 'COMPLETED' else OperationStatus.RUNNING,
            progress=getattr(yap03, 'progress', 0.0),
            current_step=getattr(yap03, 'current_step', 'Unknown'),
            metadata={'source': 'database'}
        )
        
        print(f"   UI Operation Status: {operation.status.value}")
        print(f"   UI Operation Progress: {operation.progress}")
        
        print("\n3. Test monitoring skip logic...")
        is_database_sourced = hasattr(operation, 'metadata') and operation.metadata.get('source') == 'database'
        has_process_handle = hasattr(operation, 'process') and operation.process is not None
        
        # Test stdout file detection
        can_monitor_stdout = False
        if is_database_sourced and operation.operation_type == OperationType.MICROSTRUCTURE_GENERATION:
            try:
                import glob
                import os
                operation_name = operation.name
                if operation_name.endswith(" Microstructure"):
                    base_name = operation_name.replace(" Microstructure", "")
                    if base_name.startswith("genmic_input_"):
                        folder_name = base_name.replace("genmic_input_", "")
                    else:
                        folder_name = base_name
                    
                    operations_dir = os.path.join("Operations", folder_name)
                    stdout_files = []
                    if os.path.exists(operations_dir):
                        stdout_files = glob.glob(os.path.join(operations_dir, "proc_*_stdout.txt"))
                        if stdout_files:
                            can_monitor_stdout = True
                    
                    print(f"   Operations dir: {operations_dir}")
                    print(f"   Directory exists: {os.path.exists(operations_dir)}")
                    print(f"   Stdout files: {stdout_files}")
                            
            except Exception as e:
                print(f"   Error in stdout detection: {e}")
        
        print(f"   Database sourced: {is_database_sourced}")
        print(f"   Has process handle: {has_process_handle}")
        print(f"   Can monitor stdout: {can_monitor_stdout}")
        
        # Check skip logic
        should_skip = is_database_sourced and not has_process_handle and not can_monitor_stdout
        print(f"   Should skip: {should_skip}")
        
        print("\n4. Test status condition...")
        status_allows_monitoring = operation.status in [OperationStatus.RUNNING, OperationStatus.PAUSED]
        print(f"   Status allows monitoring (RUNNING/PAUSED): {status_allows_monitoring}")
        
        print(f"\n🎯 MONITORING DECISION:")
        if should_skip:
            print("❌ Operation WILL BE SKIPPED from monitoring")
            print("   Reason: Database sourced + No process handle + Cannot monitor stdout")
        elif not status_allows_monitoring:
            print("❌ Operation WILL BE SKIPPED from monitoring") 
            print(f"   Reason: Status is {operation.status.value}, not RUNNING or PAUSED")
        else:
            print("✅ Operation WILL BE MONITORED")
            print("   It would call _parse_operation_stdout()")
            
        print(f"\n📋 CONCLUSION:")
        if yap03.status == 'COMPLETED':
            print("✅ YAP03 is already COMPLETED in database")
            print("   This is correct - monitoring worked and marked it complete")
            print("   The issue was that UI wasn't loading database state on startup")
        else:
            print("❌ YAP03 is still RUNNING in database")
            print("   This means monitoring loop is not processing stdout correctly")
    
    except Exception as e:
        print(f"❌ Error debugging YAP03: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_yap03_monitoring()
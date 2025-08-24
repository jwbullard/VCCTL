#!/usr/bin/env python3
"""
Test YAP04 monitoring - why isn't the database being updated?
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_yap04_monitoring():
    """Test YAP04 monitoring to see why progress isn't updating."""
    print("🔍 Testing YAP04 Monitoring - Database Update Issue")
    print("=" * 60)
    
    try:
        from app.services.service_container import get_service_container
        from app.windows.panels.operations_monitoring_panel import OperationsMonitoringPanel, OperationStatus, OperationType
        
        container = get_service_container()
        
        print("1. Check YAP04 current database state...")
        with container.database_service.get_read_only_session() as session:
            from app.models.operation import Operation as DBOperation
            yap04 = session.query(DBOperation).filter(
                DBOperation.name == 'genmic_input_YAP04 Microstructure'
            ).first()
            
            if not yap04:
                print("❌ YAP04 not found in database")
                return
            
            print(f"   Database Status: {yap04.status}")
            print(f"   Database Progress: {getattr(yap04, 'progress', 'N/A')}")
            print(f"   Database Step: {getattr(yap04, 'current_step', 'N/A')}")
        
        print("\\n2. Test stdout file parsing manually...")
        stdout_path = "Operations/YAP04/proc_1755984875925_stdout.txt"
        with open(stdout_path, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"   Stdout content: {repr(content)}")
        
        print("\\n3. Create Operations Panel and test parsing...")
        panel = OperationsMonitoringPanel(container)
        
        # Create YAP04 operation like it would exist in panel
        from app.windows.panels.operations_monitoring_panel import Operation
        operation = Operation(
            id="genmic_input_YAP04 Microstructure",
            name="genmic_input_YAP04 Microstructure", 
            operation_type=OperationType.MICROSTRUCTURE_GENERATION,
            status=OperationStatus.RUNNING,
            progress=0.05,
            current_step="Process started",
            metadata={"source": "database"}
        )
        
        print(f"   Before parsing - Status: {operation.status.value}, Progress: {operation.progress}")
        
        print("\\n4. Call _parse_operation_stdout manually...")
        try:
            panel._parse_operation_stdout(operation)
            print(f"   After parsing - Status: {operation.status.value}, Progress: {operation.progress}")
            print(f"   After parsing - Step: {operation.current_step}")
        except Exception as e:
            print(f"   ❌ Error in _parse_operation_stdout: {e}")
            import traceback
            traceback.print_exc()
        
        print("\\n5. Check if database was updated...")
        with container.database_service.get_read_only_session() as session:
            yap04_updated = session.query(DBOperation).filter(
                DBOperation.name == 'genmic_input_YAP04 Microstructure'
            ).first()
            
            if yap04_updated:
                print(f"   Database Status: {yap04_updated.status}")
                print(f"   Database Progress: {getattr(yap04_updated, 'progress', 'N/A')}")
                print(f"   Database Step: {getattr(yap04_updated, 'current_step', 'N/A')}")
            else:
                print("   ❌ YAP04 not found after parsing")
        
        print("\\n6. Test database update manually...")
        try:
            panel._update_operation_in_database(operation)
            print("   ✅ Manual database update called successfully")
        except Exception as e:
            print(f"   ❌ Error in _update_operation_in_database: {e}")
            import traceback
            traceback.print_exc()
        
        print("\\n7. Final database check...")
        with container.database_service.get_read_only_session() as session:
            yap04_final = session.query(DBOperation).filter(
                DBOperation.name == 'genmic_input_YAP04 Microstructure'
            ).first()
            
            if yap04_final:
                print(f"   Final Database Status: {yap04_final.status}")
                print(f"   Final Database Progress: {getattr(yap04_final, 'progress', 'N/A')}")
                print(f"   Final Database Step: {getattr(yap04_final, 'current_step', 'N/A')}")
                
                if yap04_final.status == 'COMPLETED':
                    print("   ✅ SUCCESS: Database updated to COMPLETED!")
                else:
                    print("   ❌ FAILED: Database still not updated")
            else:
                print("   ❌ YAP04 not found in final check")
        
    except Exception as e:
        print(f"❌ Error testing YAP04: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_yap04_monitoring()
#!/usr/bin/env python3
"""
Test the complete monitoring system to verify it works for new operations.
"""

import sys
import time
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_full_monitoring():
    """Test complete monitoring system for new operations."""
    print("🔍 Testing Complete Monitoring System")
    print("=" * 50)
    
    try:
        from app.services.service_container import get_service_container
        from app.windows.panels.operations_monitoring_panel import OperationsMonitoringPanel
        from app.models.operation import Operation as DBOperation
        
        container = get_service_container()
        
        print("1. Create a test RUNNING operation in database...")
        with container.database_service.get_session() as session:
            # Create a new test operation that's RUNNING
            test_operation = DBOperation(
                name='genmic_input_TestMonitoring Microstructure',
                type='MICROSTRUCTURE',
                status='RUNNING', 
                progress=0.05,
                current_step='Process started',
                start_time=datetime.now()
            )
            
            # Delete any existing test operation first
            existing = session.query(DBOperation).filter(
                DBOperation.name == 'genmic_input_TestMonitoring Microstructure'
            ).first()
            if existing:
                session.delete(existing)
            
            session.add(test_operation)
            session.commit()
            
            print(f"   Created test operation: {test_operation.name}")
            print(f"   Status: {test_operation.status}")
            print(f"   Progress: {test_operation.progress}")
        
        print("\\n2. Create Operations Panel and load operations...")
        panel = OperationsMonitoringPanel(None)
        
        print(f"   Total operations loaded: {len(panel.operations)}")
        
        # Find our test operation
        test_op = None
        for op in panel.operations.values():
            if op.name == 'genmic_input_TestMonitoring Microstructure':
                test_op = op
                break
        
        if test_op:
            print(f"   Found test operation: {test_op.name}")
            print(f"   UI Status: {test_op.status.value}")
            print(f"   UI Progress: {test_op.progress}")
        else:
            print("   ❌ Test operation not found in UI")
            return
        
        print("\\n3. Create mock stdout file with completion...")
        import os
        test_dir = Path("Operations/TestMonitoring")
        test_dir.mkdir(exist_ok=True)
        
        stdout_file = test_dir / "proc_test_stdout.txt"
        stdout_file.write_text(
            "GENMIC_PROGRESS: stage=initialization progress=0.05 message=System size configured\\n"
            "GENMIC_PROGRESS: stage=particle_placement progress=0.10 message=Placing particles\\n"
            "GENMIC_PROGRESS: stage=correlation_analysis progress=0.65 message=Distributing phases\\n"
            "GENMIC_PROGRESS: stage=output_generation progress=0.85 message=Writing output files\\n"
            "GENMIC_PROGRESS: stage=complete progress=1.00 message=Generation complete\\n"
        )
        
        print(f"   Created stdout file: {stdout_file}")
        
        print("\\n4. Test manual stdout parsing...")
        old_status = test_op.status.value
        old_progress = test_op.progress
        
        panel._parse_operation_stdout(test_op)
        
        print(f"   Status: {old_status} → {test_op.status.value}")
        print(f"   Progress: {old_progress} → {test_op.progress}")
        print(f"   Step: {test_op.current_step}")
        
        if test_op.status.value == 'completed' and test_op.progress == 1.0:
            print("   ✅ Stdout parsing works correctly")
        else:
            print("   ❌ Stdout parsing failed")
        
        print("\\n5. Test database update...")
        panel._update_operation_in_database(test_op)
        
        # Check database
        with container.database_service.get_read_only_session() as session:
            db_op = session.query(DBOperation).filter(
                DBOperation.name == 'genmic_input_TestMonitoring Microstructure'
            ).first()
            
            if db_op:
                print(f"   Database Status: {db_op.status}")
                print(f"   Database Progress: {getattr(db_op, 'progress', 'N/A')}")
                
                if db_op.status == 'COMPLETED':
                    print("   ✅ Database update works correctly")
                else:
                    print("   ❌ Database update failed")
            else:
                print("   ❌ Test operation not found in database")
        
        print("\\n6. Test monitoring thread processing...")
        print("   Monitoring thread alive:", panel.monitor_thread.is_alive())
        
        # Reset test operation to RUNNING and let monitoring process it
        with container.database_service.get_session() as session:
            db_op = session.query(DBOperation).filter(
                DBOperation.name == 'genmic_input_TestMonitoring Microstructure'
            ).first()
            if db_op:
                db_op.status = 'RUNNING'
                db_op.progress = 0.05
                session.commit()
        
        # Reload operations in panel
        panel._load_operations_from_database()
        
        # Wait for monitoring thread to process
        print("   Waiting 3 seconds for monitoring thread...")
        time.sleep(3)
        
        # Check if monitoring updated it
        with container.database_service.get_read_only_session() as session:
            db_op = session.query(DBOperation).filter(
                DBOperation.name == 'genmic_input_TestMonitoring Microstructure'
            ).first()
            
            if db_op:
                print(f"   Final Database Status: {db_op.status}")
                print(f"   Final Database Progress: {getattr(db_op, 'progress', 'N/A')}")
                
                if db_op.status == 'COMPLETED':
                    print("   ✅ MONITORING THREAD WORKS! Auto-detected completion")
                else:
                    print("   ❌ Monitoring thread did not auto-detect completion")
            
        print("\\n7. Cleanup...")
        # Clean up test operation and files
        with container.database_service.get_session() as session:
            db_op = session.query(DBOperation).filter(
                DBOperation.name == 'genmic_input_TestMonitoring Microstructure'
            ).first()
            if db_op:
                session.delete(db_op)
                session.commit()
        
        # Remove test files
        if test_dir.exists():
            import shutil
            shutil.rmtree(test_dir)
        
        # Stop monitoring
        panel._stop_monitoring()
        
        print("✅ Test completed successfully")
        
    except Exception as e:
        print(f"❌ Error in full monitoring test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_full_monitoring()
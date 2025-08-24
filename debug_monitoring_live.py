#!/usr/bin/env python3
"""
Real-time monitoring diagnostic - shows exactly what's happening.
Run this while your microstructure operation is running.
"""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def monitor_live():
    """Monitor the system live to see exactly what's happening."""
    print("🔍 LIVE MONITORING DIAGNOSTIC")
    print("=" * 60)
    print("This will show you what's happening in real-time.")
    print("Start your microstructure operation, then run this script.")
    print("Press Ctrl+C to stop monitoring.")
    print()
    
    from app.services.service_container import get_service_container
    container = get_service_container()
    
    iteration = 0
    
    try:
        while True:
            iteration += 1
            print(f"\\n--- Check {iteration} ({time.strftime('%H:%M:%S')}) ---")
            
            # 1. Check what operations are RUNNING in database
            running_ops = []
            with container.database_service.get_read_only_session() as session:
                from app.models.operation import Operation as DBOperation
                db_operations = session.query(DBOperation).filter(
                    DBOperation.status == 'RUNNING'
                ).all()
                
                for op in db_operations:
                    running_ops.append({
                        'name': op.name,
                        'status': op.status,
                        'progress': getattr(op, 'progress', 'N/A'),
                        'step': getattr(op, 'current_step', 'N/A')
                    })
            
            print(f"1. RUNNING operations in database: {len(running_ops)}")
            for op in running_ops:
                print(f"   {op['name']}: {op['status']} {op['progress']:.3f} - {op['step']}")
            
            # 2. Check for progress files
            progress_files = list(Path("Operations").rglob("genmic_progress.txt"))
            print(f"\\n2. Progress files found: {len(progress_files)}")
            
            for pf in progress_files:
                try:
                    content = pf.read_text().strip()
                    print(f"   {pf}: '{content}'")
                except Exception as e:
                    print(f"   {pf}: ERROR reading - {e}")
            
            # 3. Check what Operations Panel would show
            try:
                from app.windows.panels.operations_monitoring_panel import OperationsMonitoringPanel
                
                # Don't create monitoring thread
                panel = OperationsMonitoringPanel.__new__(OperationsMonitoringPanel)
                panel.service_container = container
                panel.operations = {}
                panel.monitoring_active = False
                panel.monitor_thread = None
                
                # Load operations like the panel does
                panel._load_operations_from_database()
                
                running_in_ui = [op for op in panel.operations.values() if op.status.value == 'running']
                
                print(f"\\n3. Operations Panel would show {len(running_in_ui)} RUNNING:")
                for op in running_in_ui:
                    print(f"   {op.name}: {op.status.value} {op.progress:.3f} - {op.current_step}")
                
            except Exception as e:
                print(f"\\n3. ERROR checking Operations Panel: {e}")
            
            # 4. Test manual progress parsing
            if running_ops and progress_files:
                print("\\n4. Testing progress parsing manually...")
                
                # Find matching operation and file
                for op_data in running_ops:
                    op_name = op_data['name']
                    # Extract folder name
                    if op_name.endswith(" Microstructure"):
                        base_name = op_name.replace(" Microstructure", "")
                        if base_name.startswith("genmic_input_"):
                            folder_name = base_name.replace("genmic_input_", "")
                        else:
                            folder_name = base_name
                        
                        expected_file = Path("Operations") / folder_name / "genmic_progress.txt"
                        
                        if expected_file.exists():
                            content = expected_file.read_text().strip()
                            print(f"   {folder_name}: file='{content}'")
                            
                            # Test parsing
                            if content.startswith("PROGRESS:"):
                                try:
                                    data = content[9:].strip()
                                    parts = data.split(' ', 1)
                                    if len(parts) >= 2:
                                        progress = float(parts[0])
                                        message = parts[1]
                                        print(f"   → Parsed: progress={progress}, message='{message}'")
                                        
                                        if progress >= 1.0:
                                            print(f"   → SHOULD BE COMPLETED!")
                                        else:
                                            print(f"   → Should show {progress*100:.1f}% progress")
                                    else:
                                        print(f"   → Parse error: not enough parts")
                                except Exception as e:
                                    print(f"   → Parse error: {e}")
                            else:
                                print(f"   → Wrong format: doesn't start with PROGRESS:")
            
            print("\\n" + "="*60)
            
            time.sleep(3)  # Check every 3 seconds
            
    except KeyboardInterrupt:
        print("\\n\\nMonitoring stopped by user.")
        print("\\nSUMMARY:")
        print("- Did you see any RUNNING operations in the database?")  
        print("- Did you see any genmic_progress.txt files with content?")
        print("- Did the Operations Panel show the same status as database?")
        print("- Did manual parsing work correctly?")

if __name__ == "__main__":
    monitor_live()
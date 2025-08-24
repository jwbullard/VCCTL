#!/usr/bin/env python3
"""
Test the new single-line progress file system.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_simple_progress_system():
    """Test the complete simple progress file workflow."""
    print("🔍 Testing Simple Progress File System")
    print("=" * 50)
    
    try:
        from app.windows.panels.operations_monitoring_panel import OperationsMonitoringPanel, Operation, OperationType, OperationStatus
        from app.services.service_container import get_service_container
        
        container = get_service_container()
        
        print("1. Create test progress file...")
        test_dir = Path("Operations/TestSimpleProgress")
        test_dir.mkdir(exist_ok=True)
        
        progress_file = test_dir / "progress.txt"
        
        # Write initial progress
        progress_file.write_text("PROGRESS: 0.30 Adding particles...")
        print(f"   Created: {progress_file}")
        print(f"   Content: {progress_file.read_text()}")
        
        print("\\n2. Create test operation...")
        operation = Operation(
            id="genmic_input_TestSimpleProgress Microstructure",
            name="genmic_input_TestSimpleProgress Microstructure",
            operation_type=OperationType.MICROSTRUCTURE_GENERATION,
            status=OperationStatus.RUNNING,
            progress=0.05,
            current_step="Started"
        )
        
        print(f"   Before: Status={operation.status.value}, Progress={operation.progress:.2f}")
        
        print("\\n3. Create Operations Panel and test parsing...")
        panel = OperationsMonitoringPanel(None)
        
        # Test the new simple progress parsing
        result = panel._parse_simple_progress(operation, "PROGRESS: 0.30 Adding particles...")
        print(f"   Parse result: {result}")
        print(f"   After parse: Status={operation.status.value}, Progress={operation.progress:.2f}")
        print(f"   Step: {operation.current_step}")
        
        print("\\n4. Test completion parsing...")
        result = panel._parse_simple_progress(operation, "PROGRESS: 1.00 Microstructure generation complete")
        print(f"   Completion parse result: {result}")
        print(f"   After completion: Status={operation.status.value}, Progress={operation.progress:.2f}")
        print(f"   Step: {operation.current_step}")
        
        print("\\n5. Test full file-based parsing...")
        
        # Update progress file to completion
        progress_file.write_text("PROGRESS: 1.00 Microstructure generation complete")
        
        # Reset operation
        operation.status = OperationStatus.RUNNING
        operation.progress = 0.65
        operation.current_step = "In progress"
        
        print(f"   Reset to: Status={operation.status.value}, Progress={operation.progress:.2f}")
        
        # Test file parsing
        panel._parse_operation_stdout(operation)
        print(f"   After file parse: Status={operation.status.value}, Progress={operation.progress:.2f}")
        print(f"   Step: {operation.current_step}")
        
        print("\\n6. Cleanup...")
        # Remove test files
        if test_dir.exists():
            import shutil
            shutil.rmtree(test_dir)
        
        panel._stop_monitoring()
        
        if operation.status == OperationStatus.COMPLETED and operation.progress == 1.0:
            print("\\n✅ SUCCESS: Simple progress file system works!")
            print("   ✅ Parses progress correctly")
            print("   ✅ Detects completion automatically")
            print("   ✅ Updates operation status")
        else:
            print("\\n❌ FAILED: Simple progress system not working")
        
    except Exception as e:
        print(f"❌ Error testing simple progress: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple_progress_system()
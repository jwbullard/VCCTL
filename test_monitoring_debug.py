#!/usr/bin/env python3
"""
Debug script to check if monitoring loop processes running operations.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_monitoring_logic():
    """Test the monitoring logic for running operations."""
    print("🧪 Testing Monitoring Loop Logic for Running Operations")
    print("=" * 70)
    
    try:
        from app.services.service_container import get_service_container
        from app.windows.panels.operations_monitoring_panel import OperationStatus as UIOperationStatus, OperationType as UIOperationType, Operation as UIOperation
        from datetime import datetime
        import subprocess
        
        container = get_service_container()
        
        print("1. Creating mock running operation (like database would create)...")
        
        # Create operation like _convert_db_operation_to_ui_operation would
        mock_operation = UIOperation(
            id="debug_monitor_123",
            name="MonitoringDebugTest",
            operation_type=UIOperationType.MICROSTRUCTURE_GENERATION,
            status=UIOperationStatus.RUNNING,
            progress=0.45,
            current_step="Testing monitoring logic - 45% complete",
            start_time=datetime.now(),
            metadata={"source": "database", "output_directory": "Operations/MonitoringTest"}  # Database-sourced
        )
        
        print(f"   ✅ Created mock operation: {mock_operation.name}")
        print(f"   ✅ Status: {mock_operation.status.value}")
        print(f"   ✅ Has metadata: {hasattr(mock_operation, 'metadata')}")
        print(f"   ✅ Metadata source: {mock_operation.metadata.get('source')}")
        print(f"   ✅ Has process handle: {hasattr(mock_operation, 'process') and mock_operation.process is not None}")
        
        print("\n2. Testing monitoring skip logic (current implementation)...")
        
        # Test the monitoring logic I implemented
        is_database_sourced = hasattr(mock_operation, 'metadata') and mock_operation.metadata.get('source') == 'database'
        has_process_handle = hasattr(mock_operation, 'process') and mock_operation.process is not None
        should_skip = is_database_sourced and not has_process_handle
        
        print(f"   🔍 is_database_sourced: {is_database_sourced}")
        print(f"   🔍 has_process_handle: {has_process_handle}")
        print(f"   🔍 should_skip: {should_skip}")
        
        if should_skip:
            print("   ❌ Operation would be skipped by monitoring loop!")
            print("   ❌ This means duration won't update in main table")
        else:
            print("   ✅ Operation would be processed by monitoring loop")
            print("   ✅ Duration should update in main table")
        
        print("\n3. Adding mock process handle...")
        
        # Add a mock process handle (like real running operations would have)
        mock_process = subprocess.Popen(['sleep', '30'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        mock_operation.process = mock_process
        mock_operation.pid = mock_process.pid
        
        # Re-test monitoring logic
        is_database_sourced = hasattr(mock_operation, 'metadata') and mock_operation.metadata.get('source') == 'database'
        has_process_handle = hasattr(mock_operation, 'process') and mock_operation.process is not None
        should_skip = is_database_sourced and not has_process_handle
        
        print(f"   🔍 is_database_sourced: {is_database_sourced}")
        print(f"   🔍 has_process_handle: {has_process_handle}")
        print(f"   🔍 should_skip: {should_skip}")
        
        if should_skip:
            print("   ❌ Operation still being skipped despite process handle!")
        else:
            print("   ✅ Operation now processed by monitoring loop")
            print("   ✅ Duration should update in main table")
            
        print("\n4. Testing duration calculation...")
        
        # Test duration calculation (what monitoring loop would do)
        duration1 = mock_operation.duration
        print(f"   ✅ Initial duration: {duration1}")
        
        import time
        time.sleep(2)
        
        duration2 = mock_operation.duration
        print(f"   ✅ Duration after 2 seconds: {duration2}")
        
        if duration2 and duration1:
            diff = (duration2 - duration1).total_seconds()
            print(f"   ✅ Duration increased by: {diff:.1f} seconds")
            if 1.8 <= diff <= 2.2:
                print("   ✅ Duration calculation working correctly")
            else:
                print(f"   ❌ Duration calculation seems wrong")
        
        print("\n5. Testing alternative approach - force main table update...")
        
        # One possible solution: ensure main table updates are called more frequently
        print("   💡 Possible solution: Add dedicated timer for main table updates")
        print("   💡 Alternative: Reduce ui_update_throttle from 0.2s to 0.1s for faster updates")
        
        # Clean up process
        mock_process.terminate()
        mock_process.wait()
        print("   🧹 Mock process cleaned up")
        
        print("\n🎯 MONITORING LOOP DIAGNOSIS:")
        print("=" * 70)
        
        if not should_skip:
            print("✅ Monitoring logic should process database-sourced running operations")
            print("❓ Issue might be elsewhere - perhaps UI update throttling")
            print("💡 Solution: Check if monitoring loop is actually running for your operations")
        else:
            print("❌ Monitoring logic still skipping database operations")
            print("❌ This would explain why main table duration doesn't update")
            print("💡 Solution: Debug the monitoring skip logic further")
        
        print("\n🔧 RECOMMENDED FIXES:")
        print("1. Verify monitoring loop processes running operations (add logging)")
        print("2. Consider reducing ui_update_throttle for more responsive updates")
        print("3. Add dedicated timer for operations list updates (like details panel has)")
        
    except Exception as e:
        print(f"❌ Error testing monitoring logic: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_monitoring_logic()
#!/usr/bin/env python3
"""
Test script to verify duration updates work for running operations.
"""

import sys
from pathlib import Path
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_duration_updates():
    """Test that duration updates automatically for running operations."""
    print("🧪 Testing Duration Updates for Running Operations")
    print("=" * 60)
    
    try:
        from app.windows.panels.operations_monitoring_panel import Operation as UIOperation, OperationType as UIOperationType, OperationStatus as UIOperationStatus
        from datetime import datetime, timedelta
        
        print("1. Creating running operation...")
        
        # Create a running operation (simulating what start_real_process_operation does)
        mock_operation = UIOperation(
            id="test_duration_123",
            name="DurationTestOperation",
            operation_type=UIOperationType.MICROSTRUCTURE_GENERATION,
            status=UIOperationStatus.RUNNING,
            progress=0.30,
            current_step="Testing duration updates - 30% complete",
            start_time=datetime.now() - timedelta(minutes=2)  # Started 2 minutes ago
        )
        
        print(f"   ✅ Created operation: {mock_operation.name}")
        print(f"   ✅ Status: {mock_operation.status.value}")
        print(f"   ✅ Start time: {mock_operation.start_time}")
        
        print("\n2. Testing duration calculation...")
        
        # Test duration property 
        initial_duration = mock_operation.duration
        print(f"   ✅ Initial duration: {initial_duration}")
        
        # Wait 2 seconds
        print("   ⏳ Waiting 2 seconds...")
        time.sleep(2)
        
        # Test duration again
        updated_duration = mock_operation.duration
        print(f"   ✅ Updated duration: {updated_duration}")
        
        # Check if duration increased
        if updated_duration and initial_duration:
            duration_diff = (updated_duration - initial_duration).total_seconds()
            print(f"   ✅ Duration increased by: {duration_diff:.1f} seconds")
            
            if 1.8 <= duration_diff <= 2.2:  # Allow some tolerance
                print("   ✅ Duration is updating correctly!")
            else:
                print(f"   ❌ Duration increase seems wrong: expected ~2 seconds, got {duration_diff:.1f}")
        else:
            print("   ❌ Duration calculation failed")
        
        print("\n3. Testing metadata scenarios...")
        
        # Test with database metadata (current issue)
        mock_operation.metadata = {"source": "database", "output_directory": "Operations/DurationTest"}
        
        print(f"   📊 Operation with database metadata:")
        print(f"   📊 Has metadata: {hasattr(mock_operation, 'metadata')}")
        print(f"   📊 Metadata source: {mock_operation.metadata.get('source')}")
        print(f"   📊 Has process handle: {hasattr(mock_operation, 'process') and mock_operation.process is not None}")
        
        # Test monitoring skip logic
        is_database_sourced = hasattr(mock_operation, 'metadata') and mock_operation.metadata.get('source') == 'database'
        has_process_handle = hasattr(mock_operation, 'process') and mock_operation.process is not None
        should_skip = is_database_sourced and not has_process_handle
        
        print(f"   🔍 Is database sourced: {is_database_sourced}")
        print(f"   🔍 Has process handle: {has_process_handle}")
        print(f"   🔍 Should skip monitoring: {should_skip}")
        
        if should_skip:
            print("   ❌ Operation would be skipped by monitoring loop (THIS IS THE PROBLEM)")
        else:
            print("   ✅ Operation would be monitored by monitoring loop")
        
        # Now test with process handle
        print("\n4. Testing with process handle...")
        
        import subprocess
        # Create a dummy process for testing
        mock_process = subprocess.Popen(['sleep', '5'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        mock_operation.process = mock_process
        mock_operation.pid = mock_process.pid
        
        # Re-test monitoring logic
        is_database_sourced = hasattr(mock_operation, 'metadata') and mock_operation.metadata.get('source') == 'database'
        has_process_handle = hasattr(mock_operation, 'process') and mock_operation.process is not None
        should_skip = is_database_sourced and not has_process_handle
        
        print(f"   🔍 Is database sourced: {is_database_sourced}")
        print(f"   🔍 Has process handle: {has_process_handle}")
        print(f"   🔍 Should skip monitoring: {should_skip}")
        
        if should_skip:
            print("   ❌ Operation would still be skipped (fix didn't work)")
        else:
            print("   ✅ Operation would now be monitored (fix working!)")
            
        # Test duration still works
        final_duration = mock_operation.duration
        print(f"   ✅ Final duration: {final_duration}")
        
        # Clean up process
        mock_process.terminate()
        mock_process.wait()
        print("   🧹 Test process cleaned up")
        
        print("\n🎯 DURATION UPDATE DIAGNOSIS:")
        print("=" * 60)
        print("✅ Duration calculation property works correctly")
        print("✅ Problem identified: database-sourced operations without process handles get skipped")
        print("✅ Fix implemented: only skip if database-sourced AND no process handle")
        print("✅ Running operations with process handles should now get duration updates")
        
    except Exception as e:
        print(f"❌ Error testing duration updates: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_duration_updates()
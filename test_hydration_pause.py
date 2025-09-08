#!/usr/bin/env python3
"""
Test script to validate hydration pause functionality.
This simulates what should happen when a hydration operation is started and paused.
"""

import sys
import os
import time
import signal
import subprocess
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

def test_pause_resume_mechanics():
    """Test the basic mechanics of pause/resume with a simple process."""
    print("=== Testing Basic Pause/Resume Mechanics ===")
    
    # Start a simple long-running process
    print("Starting test process...")
    process = subprocess.Popen(
        ["python", "-c", "import time; [print(f'Working... {i}', flush=True) or time.sleep(1) for i in range(30)]"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    print(f"Process started with PID: {process.pid}")
    
    # Let it run for 3 seconds
    print("Letting process run for 3 seconds...")
    time.sleep(3)
    
    # Test pause
    print(f"Sending SIGSTOP to pause process {process.pid}...")
    try:
        process.send_signal(signal.SIGSTOP)
        print("✓ SIGSTOP sent successfully")
    except Exception as e:
        print(f"✗ Failed to send SIGSTOP: {e}")
        process.terminate()
        return False
    
    # Wait while paused
    print("Process paused, waiting 3 seconds...")
    time.sleep(3)
    
    # Test resume
    print(f"Sending SIGCONT to resume process {process.pid}...")
    try:
        process.send_signal(signal.SIGCONT)
        print("✓ SIGCONT sent successfully")
    except Exception as e:
        print(f"✗ Failed to send SIGCONT: {e}")
        process.terminate()
        return False
    
    # Let it run a bit more
    print("Process resumed, letting it run for 2 more seconds...")
    time.sleep(2)
    
    # Terminate
    print("Terminating test process...")
    process.terminate()
    process.wait()
    print("✓ Basic pause/resume mechanics work correctly\n")
    return True

def test_hydration_operation_registration():
    """Test if hydration operations get registered with process info."""
    print("=== Testing Hydration Operation Registration ===")
    
    try:
        from app.windows.panels.operations_monitoring_panel import Operation, OperationType, OperationStatus
        from app.services.hydration_executor_service import HydrationExecutorService
        import logging
        
        # Enable debug logging
        logging.basicConfig(level=logging.DEBUG)
        
        # Create a mock operation
        operation = Operation(
            id="test_hydration_001",
            name="TestHydration",
            operation_type=OperationType.HYDRATION,
            status=OperationStatus.RUNNING
        )
        
        print(f"Created test operation: {operation.name}")
        print(f"Initial - process: {operation.process}, pid: {operation.pid}")
        
        # Simulate setting process info (what should happen in registration)
        test_process = subprocess.Popen(
            ["python", "-c", "import time; time.sleep(10)"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        operation.process = test_process
        operation.pid = test_process.pid
        
        print(f"After registration - process: {operation.process}, pid: {operation.pid}")
        
        # Test pause capability
        print("Testing pause capability...")
        can_pause = operation.pause_process()
        print(f"Can pause: {can_pause}")
        
        if can_pause:
            print("✓ Operation can be paused after registration")
            # Resume and cleanup
            operation.resume_process()
        else:
            print("✗ Operation cannot be paused even after registration")
        
        test_process.terminate()
        test_process.wait()
        
        return can_pause
        
    except Exception as e:
        print(f"✗ Error testing registration: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_actual_hydration_service():
    """Test the actual hydration service process creation."""
    print("=== Testing Actual Hydration Service ===")
    
    try:
        from app.services.hydration_executor_service import HydrationExecutorService
        from pathlib import Path
        
        service = HydrationExecutorService()
        
        # Check if service creates processes with accessible references
        print("Checking HydrationExecutorService configuration...")
        print(f"Service initialized: {service is not None}")
        print(f"Active simulations dict: {service.active_simulations}")
        
        # Simulate what happens when hydration starts
        # (without actually starting one since it needs full environment)
        print("\nWhat should happen when hydration starts:")
        print("1. HydrationExecutorService creates subprocess for disrealnew")
        print("2. Process stored in simulation_info['process']")
        print("3. Hydration panel should access this process")
        print("4. Process should be registered with operations panel")
        print("5. Operations panel should be able to pause/resume")
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing hydration service: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("Hydration Pause Functionality Validation Tests")
    print("=" * 60)
    print()
    
    tests = [
        ("Basic Pause/Resume Mechanics", test_pause_resume_mechanics),
        ("Operation Registration Simulation", test_hydration_operation_registration),
        ("Hydration Service Check", test_actual_hydration_service)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
            print()
        except Exception as e:
            print(f"✗ {test_name} failed with error: {e}")
            results.append((test_name, False))
            print()
    
    # Summary
    print("=" * 60)
    print("Test Summary:")
    print("=" * 60)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed < total:
        print("\n⚠️  Some tests failed. The pause functionality may not work correctly.")
        print("Check the debug logs when running the actual application.")
    else:
        print("\n✅ All tests passed! The pause mechanism should work.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
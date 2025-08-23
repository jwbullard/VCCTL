#!/usr/bin/env python3
"""
Test simulating genmic stdout output to verify parsing works.
"""

import sys
import os
import time
from pathlib import Path
from datetime import datetime

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_stdout_simulation():
    """Test simulating genmic stdout with progress messages."""
    
    print("🔍 Testing Stdout Progress Simulation...")
    
    try:
        # Create a temporary stdout file
        test_stdout_file = Path("test_genmic_stdout.txt")
        
        # Simulate genmic progress messages being written to stdout
        progress_messages = [
            "GENMIC_PROGRESS: stage=initialization progress=0.05 message=System size configured",
            "GENMIC_PROGRESS: stage=particle_placement progress=0.10 message=Starting particle placement",
            "GENMIC_PROGRESS: stage=particle_placement progress=0.35 message=Placed 5000 particles",
            "GENMIC_PROGRESS: stage=correlation_analysis progress=0.65 message=Analyzing phase correlations",
            "GENMIC_PROGRESS: stage=output_generation progress=0.85 message=Writing output files",
            "GENMIC_PROGRESS: stage=complete progress=1.00 message=Generation complete"
        ]
        
        # Import the Operation class
        from app.windows.panels.operations_monitoring_panel import Operation, OperationType, OperationStatus
        
        # Create a test operation
        operation = Operation(
            id="test_stdout",
            name="Test Microstructure",
            operation_type=OperationType.MICROSTRUCTURE_GENERATION,
            status=OperationStatus.RUNNING
        )
        
        # Set stdout file path
        operation.stdout_file = str(test_stdout_file)
        operation._stdout_position = 0
        
        print(f"\nSimulating genmic progress output to: {test_stdout_file}")
        
        # Simulate writing progress messages to stdout file
        with open(test_stdout_file, 'w') as f:
            for i, message in enumerate(progress_messages, 1):
                print(f"\n{i}. Writing: {message}")
                f.write(message + "\n")
                f.flush()  # Ensure immediate write
                
                # Simulate the UI parsing this new content
                try:
                    with open(test_stdout_file, 'r') as read_f:
                        read_f.seek(operation._stdout_position)
                        new_content = read_f.read()
                        operation._stdout_position = read_f.tell()
                        
                        # Process new lines
                        for line in new_content.strip().split('\n'):
                            if line.strip():
                                if operation.parse_genmic_progress(line.strip()):
                                    print(f"   ✅ Parsed: {operation.progress:.1%} - {operation.current_step}")
                                    if operation.status == OperationStatus.COMPLETED:
                                        print(f"   🏁 Operation marked as COMPLETED!")
                                        break
                except Exception as e:
                    print(f"   ❌ Error parsing: {e}")
                
                time.sleep(0.5)  # Simulate time between progress updates
        
        # Cleanup
        test_stdout_file.unlink()
        
        print(f"\n🎯 Final Result:")
        print(f"   Progress: {operation.progress:.1%}")
        print(f"   Status: {operation.status.value}")
        print(f"   Step: {operation.current_step}")
        
        if operation.status == OperationStatus.COMPLETED and operation.progress == 1.0:
            print(f"   🎉 SUCCESS: Stdout parsing simulation works!")
        else:
            print(f"   ⚠️  Issue: Expected completed status with 100% progress")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    test_stdout_simulation()
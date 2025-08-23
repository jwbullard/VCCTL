#!/usr/bin/env python3
"""
Test the genmic progress parsing functionality.
"""

import sys
import os
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_progress_parsing():
    """Test genmic progress message parsing."""
    
    print("🔍 Testing Genmic Progress Parsing...")
    
    try:
        # Import the Operation class
        from app.windows.panels.operations_monitoring_panel import Operation, OperationType, OperationStatus
        
        # Create a test operation
        operation = Operation(
            id="test_genmic",
            name="Test Microstructure",
            operation_type=OperationType.MICROSTRUCTURE_GENERATION,
            status=OperationStatus.RUNNING
        )
        
        # Test various progress messages
        test_messages = [
            "GENMIC_PROGRESS: stage=initialization progress=0.05 message=System size configured",
            "GENMIC_PROGRESS: stage=particle_placement progress=0.10 message=Starting particle placement",
            "GENMIC_PROGRESS: stage=particle_placement progress=0.35 message=Placed 5000 particles",
            "GENMIC_PROGRESS: stage=correlation_analysis progress=0.65 message=Analyzing phase correlations",
            "GENMIC_PROGRESS: stage=output_generation progress=0.85 message=Writing output files",
            "GENMIC_PROGRESS: stage=output_generation progress=0.90 message=Microstructure file written",
            "GENMIC_PROGRESS: stage=output_generation progress=0.95 message=Particle ID file written",
            "GENMIC_PROGRESS: stage=complete progress=1.00 message=Generation complete"
        ]
        
        print("\nTesting progress message parsing:")
        for i, message in enumerate(test_messages, 1):
            print(f"\n{i}. Testing: {message}")
            
            result = operation.parse_genmic_progress(message)
            
            if result:
                print(f"   ✅ Parsed successfully")
                print(f"   📊 Progress: {operation.progress:.1%}")
                print(f"   📝 Step: {operation.current_step}")
                print(f"   🎯 Status: {operation.status.value}")
                
                if operation.status == OperationStatus.COMPLETED:
                    print(f"   🏁 Operation marked as COMPLETED!")
                    break
            else:
                print(f"   ❌ Failed to parse")
        
        # Test invalid message
        print(f"\n9. Testing invalid message:")
        invalid_msg = "Some random genmic output without progress"
        result = operation.parse_genmic_progress(invalid_msg)
        if not result:
            print(f"   ✅ Correctly ignored non-progress message")
        else:
            print(f"   ❌ Incorrectly parsed non-progress message")
        
        print(f"\n🎯 Test Summary:")
        print(f"   Final progress: {operation.progress:.1%}")
        print(f"   Final step: {operation.current_step}")
        print(f"   Final status: {operation.status.value}")
        
        if operation.status == OperationStatus.COMPLETED and operation.progress == 1.0:
            print(f"   🎉 SUCCESS: Progress parsing works correctly!")
        else:
            print(f"   ⚠️  Issue: Expected completed status with 100% progress")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    test_progress_parsing()
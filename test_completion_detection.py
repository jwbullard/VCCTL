#!/usr/bin/env python3
"""
Test the improved completion detection logic.
"""

import sys
import os
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_completion_detection():
    """Test completion detection for various operation types."""
    
    print("🔍 Testing Completion Detection Logic...")
    
    try:
        from app.services.service_container import get_service_container
        
        container = get_service_container()
        executor = container.hydration_executor_service
        
        # Test operations
        test_operations = [
            "c140q07-early",  # Custom name (completed)
            "MyCustomHydrationTest",  # Custom name (completed) 
            "HydrationSim_Cem140Quartz07_20250821_205203",  # Auto-generated (completed)
        ]
        
        for operation_name in test_operations:
            print(f"\n🧪 Testing operation: {operation_name}")
            
            # Check if operation directory exists
            operation_dir = Path(f"./Operations/{operation_name}")
            if not operation_dir.exists():
                print(f"   ❌ Directory not found: {operation_dir}")
                continue
            
            # Test the completion detection
            try:
                is_completed = executor._check_simulation_completion(operation_name)
                print(f"   🎯 Completion detected: {'✅ YES' if is_completed else '❌ NO'}")
                
                # Show what files were found
                hydration_csv_files = list(operation_dir.glob("HydrationOf_*.csv"))
                img_files = list(operation_dir.glob("*.img"))
                progress_files = list(operation_dir.glob("progress.json"))
                
                print(f"   📄 CSV files: {[f.name for f in hydration_csv_files]}")
                print(f"   🖼️ IMG files: {[f.name for f in img_files[:3]]}{'...' if len(img_files) > 3 else ''}")
                print(f"   📊 Progress file: {'✅' if progress_files else '❌'}")
                
            except Exception as e:
                print(f"   ❌ Error testing completion: {e}")
                import traceback
                print(f"   Traceback: {traceback.format_exc()}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    test_completion_detection()
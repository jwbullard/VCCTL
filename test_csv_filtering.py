#!/usr/bin/env python3
"""
Test CSV file filtering logic for data plotter.
"""

import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_csv_filtering():
    """Test CSV file filtering and prioritization."""
    
    print("🔍 Testing CSV File Filtering...")
    
    # Test with a real hydration operation directory
    test_operation = "c140q07-early"
    output_path = Path(f"./Operations/{test_operation}")
    
    if not output_path.exists():
        print(f"❌ Test directory not found: {output_path}")
        return
    
    print(f"📂 Testing with operation: {test_operation}")
    
    # Find all CSV files
    csv_files = list(output_path.glob("*.csv"))
    print(f"📊 Total CSV files found: {len(csv_files)}")
    for csv_file in csv_files:
        print(f"   - {csv_file.name}")
    
    # Apply filtering logic
    filtered_csv_files = []
    for csv_file in csv_files:
        filename = csv_file.name
        
        # Skip extended parameter files (input data, not results)
        if "_extended_parameters.csv" in filename:
            print(f"   🚫 Skipping extended parameter file: {filename}")
            continue
        
        # Skip time_history.csv (not useful for plotting)
        if filename == "time_history.csv":
            print(f"   🚫 Skipping time_history file: {filename}")
            continue
        
        filtered_csv_files.append(csv_file)
    
    print(f"\n✅ Filtered CSV files: {len(filtered_csv_files)}")
    
    # Apply sorting to prioritize HydrationOf_*.csv files
    def sort_priority(csv_file):
        filename = csv_file.name
        if filename.startswith("HydrationOf_") and filename.endswith(".csv"):
            return (0, filename)  # Highest priority
        else:
            return (1, filename)  # Lower priority
    
    filtered_csv_files.sort(key=sort_priority)
    
    print(f"📋 Final dropdown order:")
    for i, csv_file in enumerate(filtered_csv_files, 1):
        priority = "🥇" if csv_file.name.startswith("HydrationOf_") else "🥈"
        print(f"   {i}. {priority} {csv_file.name}")
    
    # Test with multiple operations
    test_operations = ["HydrationSim_Cem140Quartz07_20250821_205203", "HydrationSim_Cem140Blend_20250820_132554"]
    
    for operation in test_operations:
        op_path = Path(f"./Operations/{operation}")
        if op_path.exists():
            print(f"\n📂 Testing with operation: {operation}")
            csv_files = list(op_path.glob("*.csv"))
            filtered_count = 0
            for csv_file in csv_files:
                filename = csv_file.name
                if "_extended_parameters.csv" not in filename and filename != "time_history.csv":
                    filtered_count += 1
            print(f"   📊 {len(csv_files)} total → {filtered_count} filtered CSV files")

if __name__ == "__main__":
    test_csv_filtering()
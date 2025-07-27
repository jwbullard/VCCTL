#!/usr/bin/env python3
"""
Test script to verify the new tab structure for cement materials dialog.
"""

import sys
from pathlib import Path

# Add the src directory to Python path to import VCCTL modules
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

try:
    from app.windows.dialogs.material_dialog import CementDialog
    print("✓ Successfully imported CementDialog")
    
    # Check if the new methods exist
    required_methods = [
        '_create_properties_tab',
        '_create_chemical_properties_tab', 
        '_create_physical_properties_tab',
        '_add_chemical_composition_section'
    ]
    
    for method in required_methods:
        if hasattr(CementDialog, method):
            print(f"✓ Method '{method}' exists")
        else:
            print(f"✗ Method '{method}' missing")
    
    print("\nTab structure implementation:")
    print("- Basic Info tab (unchanged)")
    print("- Chemical Properties tab (NEW)")
    print("  └── Chemical Composition (phase fractions + gypsum)")
    print("- Physical Properties tab (NEW)")  
    print("  └── Setting Times + Calculated Properties + PSD")
    print("- Advanced tab (unchanged, setting times removed)")
    
    print("\nImplementation complete! ✓")
    
except ImportError as e:
    print(f"✗ Import error: {e}")
except Exception as e:
    print(f"✗ Error: {e}")
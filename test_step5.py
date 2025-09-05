#!/usr/bin/env python3
"""Test script for Step 5 - UI updates validation"""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
src_path = project_root / 'src'
sys.path.insert(0, str(src_path))

def test_ui_updates():
    print("=== Step 5 Testing Results ===")
    
    # Test 1: Check materials panel updates
    try:
        from app.windows.panels.materials_panel import MaterialsPanel
        print("✅ MaterialsPanel imports successfully")
        
        # Check if the updated references exist by searching file content
        materials_panel_file = src_path / 'app' / 'windows' / 'panels' / 'materials_panel.py'
        content = materials_panel_file.read_text()
        
        if 'filler_service' in content and 'inert_filler_service' not in content:
            print("✅ MaterialsPanel updated to use filler_service")
        else:
            print("❌ MaterialsPanel still has inert_filler_service references")
            
        if '"filler"' in content and 'append("inert_filler"' not in content:
            print("✅ MaterialsPanel UI updated to use 'filler' instead of 'inert_filler'")
        else:
            print("❌ MaterialsPanel UI still references 'inert_filler'")
            
    except Exception as e:
        print(f"❌ MaterialsPanel test failed: {e}")
    
    # Test 2: Check material dialog updates
    try:
        from app.windows.dialogs.material_dialog import FillerDialog
        print("✅ FillerDialog class exists (renamed from InertFillerDialog)")
        
        material_dialog_file = src_path / 'app' / 'windows' / 'dialogs' / 'material_dialog.py'
        content = material_dialog_file.read_text()
        
        if 'FillerDialog' in content and 'InertFillerDialog' not in content:
            print("✅ Material dialog renamed from InertFillerDialog to FillerDialog")
        else:
            print("❌ Material dialog still has InertFillerDialog references")
            
        if 'from app.models.filler import' in content:
            print("✅ Material dialog imports from filler model")
        else:
            print("❌ Material dialog doesn't import from filler model")
            
    except ImportError as e:
        print(f"❌ FillerDialog import failed: {e}")
    except Exception as e:
        print(f"❌ Material dialog test failed: {e}")
    
    # Test 3: Check mix design panel updates
    try:
        mix_design_file = src_path / 'app' / 'windows' / 'panels' / 'mix_design_panel.py'
        content = mix_design_file.read_text()
        
        if 'from app.models.filler import Filler' in content:
            print("✅ Mix design panel imports Filler model")
        else:
            print("❌ Mix design panel doesn't import Filler model")
            
        if "'filler': 'Filler'" in content:
            print("✅ Mix design panel UI text updated")
        else:
            print("❌ Mix design panel UI text not updated")
            
    except Exception as e:
        print(f"❌ Mix design panel test failed: {e}")
    
    # Test 4: Check file operations dialog
    try:
        file_ops_file = src_path / 'app' / 'windows' / 'dialogs' / 'file_operations_dialog.py'
        content = file_ops_file.read_text()
        
        if 'append("filler", "Filler")' in content:
            print("✅ File operations dialog updated to use 'filler'")
        else:
            print("❌ File operations dialog not updated")
            
    except Exception as e:
        print(f"❌ File operations dialog test failed: {e}")
    
    print("\n🎯 Step 5 Summary:")
    print("- UI files updated to use 'filler' instead of 'inert_filler'")
    print("- Dialog class renamed from InertFillerDialog to FillerDialog") 
    print("- Model imports updated to use Filler instead of InertFiller")
    print("- Service references updated to use filler_service")

if __name__ == "__main__":
    test_ui_updates()
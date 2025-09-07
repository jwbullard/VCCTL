#!/usr/bin/env python3
"""
Comprehensive UI-to-Database persistence test for limestone, silica fume, and slag.
Traces complete data flow: UI form → dialog save → service call → database write
"""

import logging
import sys
import os
sys.path.insert(0, '/Users/jwbullard/Software/vcctl-gtk/src')

from app.database.service import DatabaseService
from app.services.limestone_service import LimestoneService
from app.services.silica_fume_service import SilicaFumeService
from app.services.slag_service import SlagService
from app.models.limestone import LimestoneUpdate
from app.models.silica_fume import SilicaFumeUpdate
from app.models.slag import SlagUpdate

# Configure logging to see all service calls
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_ui_persistence_flow():
    """Test complete UI persistence flow for all three materials"""
    
    # Initialize services
    db_service = DatabaseService()
    limestone_service = LimestoneService(db_service)
    silica_fume_service = SilicaFumeService(db_service)
    slag_service = SlagService(db_service)
    
    print("=== COMPREHENSIVE UI PERSISTENCE TEST ===\n")
    
    # Test 1: Limestone Update with PSD + Name
    print("1. TESTING LIMESTONE UPDATE (ID-based)")
    try:
        limestones = limestone_service.get_all()
        if not limestones:
            print("   ❌ No limestone materials found")
        else:
            limestone = limestones[0]
            print(f"   📋 Original: {limestone.name} (ID: {limestone.id})")
            print(f"   📋 PSD ID: {limestone.psd_data_id}")
            
            # Simulate UI form data with name change + PSD data
            update_data = LimestoneUpdate(
                name="TEST_Limestone_Name_Change",
                specific_gravity=2.75,
                psd_mode="rosin_rammler",
                psd_d50=25.0,
                psd_n=1.2,
                psd_dmax=200.0
            )
            
            print(f"   🔄 Updating with: {update_data.model_dump()}")
            updated = limestone_service.update(limestone.id, update_data)
            print(f"   ✅ Updated: {updated.name} (ID: {updated.id})")
            print(f"   ✅ PSD ID: {updated.psd_data_id}")
            if updated.psd_data:
                print(f"   ✅ PSD Mode: {updated.psd_data.psd_mode}")
                print(f"   ✅ PSD D50: {updated.psd_data.psd_d50}")
    
    except Exception as e:
        print(f"   ❌ Limestone update failed: {e}")
    
    print()
    
    # Test 2: Silica Fume Update with PSD + Name  
    print("2. TESTING SILICA FUME UPDATE (ID-based)")
    try:
        silica_fumes = silica_fume_service.get_all()
        if not silica_fumes:
            print("   ❌ No silica fume materials found")
        else:
            silica_fume = silica_fumes[0]
            print(f"   📋 Original: {silica_fume.name} (ID: {silica_fume.id})")
            print(f"   📋 PSD ID: {silica_fume.psd_data_id}")
            
            # Simulate UI form data with name change + PSD data
            update_data = SilicaFumeUpdate(
                name="TEST_SilicaFume_Name_Change",
                specific_gravity=2.25,
                psd_mode="log_normal", 
                psd_d50=0.15,
                psd_n=1.8,
                psd_dmax=10.0
            )
            
            print(f"   🔄 Updating with: {update_data.model_dump()}")
            updated = silica_fume_service.update(silica_fume.id, update_data)
            print(f"   ✅ Updated: {updated.name} (ID: {updated.id})")
            print(f"   ✅ PSD ID: {updated.psd_data_id}")
            if updated.psd_data:
                print(f"   ✅ PSD Mode: {updated.psd_data.psd_mode}")
                print(f"   ✅ PSD D50: {updated.psd_data.psd_d50}")
    
    except Exception as e:
        print(f"   ❌ Silica fume update failed: {e}")
    
    print()
    
    # Test 3: Slag Update with PSD + Name
    print("3. TESTING SLAG UPDATE (ID-based)")
    try:
        slags = slag_service.get_all()
        if not slags:
            print("   ❌ No slag materials found")
        else:
            slag = slags[0]
            print(f"   📋 Original: {slag.name} (ID: {slag.id})")
            print(f"   📋 PSD ID: {slag.psd_data_id}")
            
            # Check if SlagUpdate has name field
            slag_update_fields = SlagUpdate.model_fields.keys()
            print(f"   📋 SlagUpdate fields: {list(slag_update_fields)}")
            
            # Create update data based on available fields
            update_kwargs = {
                "specific_gravity": 2.95,
                "psd_mode": "fuller", 
                "psd_d50": 30.0,
                "psd_n": 0.5,
                "psd_dmax": 150.0
            }
            
            # Add name only if it's in the model
            if 'name' in slag_update_fields:
                update_kwargs['name'] = "TEST_Slag_Name_Change"
                print("   📋 Name field available in SlagUpdate")
            else:
                print("   ⚠️ Name field NOT available in SlagUpdate")
            
            update_data = SlagUpdate(**update_kwargs)
            
            print(f"   🔄 Updating with: {update_data.model_dump()}")
            updated = slag_service.update(slag.id, update_data)
            print(f"   ✅ Updated: {updated.name} (ID: {updated.id})")
            print(f"   ✅ PSD ID: {updated.psd_data_id}")
            if updated.psd_data:
                print(f"   ✅ PSD Mode: {updated.psd_data.psd_mode}")
                print(f"   ✅ PSD D50: {updated.psd_data.psd_data.psd_d50 if hasattr(updated.psd_data, 'psd_d50') else 'N/A'}")
    
    except Exception as e:
        print(f"   ❌ Slag update failed: {e}")
    
    print()
    
    # Test 4: Check how UI dialog calls these services
    print("4. CHECKING UI DIALOG INTEGRATION")
    
    # Examine the material dialog save workflow
    dialog_file = '/Users/jwbullard/Software/vcctl-gtk/src/app/windows/dialogs/material_dialog.py'
    if os.path.exists(dialog_file):
        print("   📋 Examining MaterialDialog save workflow...")
        
        # Look for the save method patterns
        with open(dialog_file, 'r') as f:
            content = f.read()
            
        # Find save methods for each material type
        for material in ['limestone', 'silica_fume', 'slag']:
            method_name = f'_save_{material}'
            if method_name in content:
                print(f"   ✅ Found {method_name} method")
                
                # Extract the method
                start = content.find(f'def {method_name}')
                if start != -1:
                    # Find the end of the method (next method or class end)
                    lines = content[start:].split('\n')
                    method_lines = []
                    indent_level = None
                    
                    for line in lines:
                        if line.strip().startswith('def ') and method_lines:
                            # Hit the next method
                            break
                        if line.strip() == '' or line.startswith(' ' * 4):
                            method_lines.append(line)
                        elif method_lines:
                            # End of method
                            break
                    
                    method_code = '\n'.join(method_lines[:10])  # First 10 lines
                    print(f"      Method start:\n{method_code}")
            else:
                print(f"   ❌ No {method_name} method found")
    else:
        print("   ❌ MaterialDialog file not found")

if __name__ == "__main__":
    test_ui_persistence_flow()
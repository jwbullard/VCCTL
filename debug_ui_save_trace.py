#!/usr/bin/env python3
"""
UI Save Trace Debug - Monkey patch dialog save methods to trace exact data flow
"""

import logging
import sys
import os
sys.path.insert(0, '/Users/jwbullard/Software/vcctl-gtk/src')

from app.database.service import DatabaseService
from app.services.limestone_service import LimestoneService
from app.services.silica_fume_service import SilicaFumeService
from app.services.slag_service import SlagService

# Configure debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_update_data_validation():
    """Test that update data is being constructed correctly"""
    
    # Initialize services
    db_service = DatabaseService()
    limestone_service = LimestoneService(db_service)
    silica_fume_service = SilicaFumeService(db_service)
    slag_service = SlagService(db_service)
    
    print("=== UI UPDATE DATA VALIDATION TEST ===\n")
    
    # Test 1: Create Update objects directly with PSD data
    print("1. TESTING UPDATE MODEL CONSTRUCTION")
    
    # Test LimestoneUpdate with PSD fields
    print("   Testing LimestoneUpdate with PSD fields...")
    try:
        from app.models.limestone import LimestoneUpdate
        
        # Simulate exact data that UI should be sending
        ui_data = {
            'name': 'Test_Limestone_UI_Data',
            'specific_gravity': 2.75,
            'caco3_content': 95.0,
            'activation_energy': 100.0,
            'psd_mode': 'rosin_rammler',
            'psd_d50': 25.0,
            'psd_n': 1.2,
            'psd_dmax': 200.0,
            'description': 'Test description',
            'source': 'Test source',
            'notes': 'Test notes'
        }
        
        print(f"   📋 UI data: {ui_data}")
        
        # Create LimestoneUpdate object
        limestone_update = LimestoneUpdate(**ui_data)
        print(f"   ✅ LimestoneUpdate created: {limestone_update.model_dump()}")
        
        # Test that service can handle this data
        limestones = limestone_service.get_all()
        if limestones:
            limestone_id = limestones[0].id
            print(f"   📋 Testing update on limestone ID: {limestone_id}")
            
            # This should work if both UI data collection and service are correct
            updated = limestone_service.update(limestone_id, limestone_update)
            print(f"   ✅ Service update successful: {updated.name}")
            print(f"   ✅ PSD Mode: {updated.psd_data.psd_mode if updated.psd_data else 'None'}")
        
    except Exception as e:
        print(f"   ❌ LimestoneUpdate test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    
    # Test SilicaFumeUpdate with PSD fields
    print("   Testing SilicaFumeUpdate with PSD fields...")
    try:
        from app.models.silica_fume import SilicaFumeUpdate
        
        # Simulate exact data that UI should be sending  
        ui_data = {
            'name': 'Test_SilicaFume_UI_Data',
            'specific_gravity': 2.25,
            'silica_content': 92.0,
            'specific_surface_area': 20000.0,
            'psd_mode': 'log_normal',
            'psd_d50': 0.15,
            'psd_n': 1.8,
            'psd_dmax': 10.0,
            'description': 'Test description',
            'source': 'Test source',
            'notes': 'Test notes'
        }
        
        print(f"   📋 UI data: {ui_data}")
        
        # Create SilicaFumeUpdate object
        silica_fume_update = SilicaFumeUpdate(**ui_data)
        print(f"   ✅ SilicaFumeUpdate created: {silica_fume_update.model_dump()}")
        
        # Test that service can handle this data
        silica_fumes = silica_fume_service.get_all()
        if silica_fumes:
            silica_fume_id = silica_fumes[0].id
            print(f"   📋 Testing update on silica fume ID: {silica_fume_id}")
            
            # This should work if both UI data collection and service are correct
            updated = silica_fume_service.update(silica_fume_id, silica_fume_update)
            print(f"   ✅ Service update successful: {updated.name}")
            print(f"   ✅ PSD Mode: {updated.psd_data.psd_mode if updated.psd_data else 'None'}")
        
    except Exception as e:
        print(f"   ❌ SilicaFumeUpdate test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    
    # Test SlagUpdate with PSD fields
    print("   Testing SlagUpdate with PSD fields...")
    try:
        from app.models.slag import SlagUpdate
        
        # Check what fields SlagUpdate actually has
        slag_fields = list(SlagUpdate.model_fields.keys())
        print(f"   📋 SlagUpdate available fields: {slag_fields}")
        
        # Simulate exact data that UI should be sending (without name since it's not in SlagUpdate)
        ui_data = {
            'specific_gravity': 2.95,
            'glass_content': 95.0,
            'psd_mode': 'fuller',
            'psd_d50': 30.0,
            'psd_n': 0.5,
            'psd_dmax': 150.0,
            'sio2_content': 35.0,
            'cao_content': 40.0,
            'al2o3_content': 15.0,
            'mgo_content': 8.0,
            'fe2o3_content': 1.0,
            'so3_content': 1.0,
            'description': 'Test description',
            'source': 'Test source', 
            'notes': 'Test notes'
        }
        
        print(f"   📋 UI data: {ui_data}")
        
        # Create SlagUpdate object
        slag_update = SlagUpdate(**ui_data)
        print(f"   ✅ SlagUpdate created: {slag_update.model_dump()}")
        
        # Test that service can handle this data
        slags = slag_service.get_all()
        if slags:
            slag_id = slags[0].id
            print(f"   📋 Testing update on slag ID: {slag_id}")
            
            # This should work if both UI data collection and service are correct
            updated = slag_service.update(slag_id, slag_update)
            print(f"   ✅ Service update successful: {updated.name}")
            print(f"   ✅ PSD Mode: {updated.psd_data.psd_mode if updated.psd_data else 'None'}")
        
    except Exception as e:
        print(f"   ❌ SlagUpdate test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    
    # Test 2: Check if the issue is in the UI → Service data flow
    print("2. TESTING POTENTIAL UI → SERVICE DATA ISSUES")
    
    # Let's see what happens if we call the service with missing fields
    print("   Testing incomplete PSD data...")
    try:
        from app.models.limestone import LimestoneUpdate
        
        incomplete_data = {
            'name': 'Incomplete_Test',
            'specific_gravity': 2.75,
            'psd_mode': 'rosin_rammler',  # Only one PSD field
            # Missing psd_d50, psd_n, psd_dmax
        }
        
        incomplete_update = LimestoneUpdate(**incomplete_data)
        print(f"   📋 Incomplete update data: {incomplete_update.model_dump()}")
        
        limestones = limestone_service.get_all()
        if limestones:
            limestone_id = limestones[0].id
            updated = limestone_service.update(limestone_id, incomplete_update)
            print(f"   ✅ Incomplete data handled: {updated.name}")
            print(f"   ✅ PSD Mode: {updated.psd_data.psd_mode if updated.psd_data else 'None'}")
        
    except Exception as e:
        print(f"   ❌ Incomplete data test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_update_data_validation()
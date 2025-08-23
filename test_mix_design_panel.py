#!/usr/bin/env python3
"""
Test Mix Design Panel initialization to identify where it might be failing.
"""

import sys
import os
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_mix_design_panel_creation():
    """Test creating the Mix Design panel components to find the failure point."""
    
    print("🔍 Testing Mix Design Panel Creation...")
    
    try:
        # Test 1: Import required modules
        print("1. Testing imports...")
        from app.services.service_container import get_service_container
        print("   ✅ Service container import successful")
        
        # Test 2: Create service container
        print("2. Creating service container...")
        container = get_service_container()
        print("   ✅ Service container created")
        
        # Test 3: Get required services
        print("3. Getting required services...")
        mix_service = container.mix_service
        cement_service = container.cement_service
        aggregate_service = container.aggregate_service
        print("   ✅ Services obtained")
        
        # Test 4: Test panel imports
        print("4. Testing panel imports...")
        # Don't import the full panel yet, just test the service imports
        from app.services.mix_service import MixService, MixComponent, MixDesign
        from app.models.material_types import MaterialType
        print("   ✅ Panel-related imports successful")
        
        # Test 5: Test materials loading 
        print("5. Testing material loading...")
        with container.database_service.get_read_only_session() as session:
            # Test loading some materials that Mix Design panel needs
            from app.models.cement import Cement
            cements = session.query(Cement).limit(3).all()
            print(f"   ✅ Found {len(cements)} cements in database")
            
            from app.models.aggregate import Aggregate  
            aggregates = session.query(Aggregate).limit(3).all()
            print(f"   ✅ Found {len(aggregates)} aggregates in database")
        
        # Test 6: Test simple panel creation (without GUI)
        print("6. Testing panel creation...")
        # We'll import the panel but won't instantiate it with a real parent
        # This tests if there are import-time errors
        from app.windows.panels.mix_design_panel import MixDesignPanel
        print("   ✅ Mix Design Panel class imported successfully")
        
        print("\n🎯 Panel Creation Test Summary:")
        print("   All core components can be imported and initialized")
        print("   The issue is likely in the UI interaction or during actual panel instantiation")
        print("   Next step: Check if launching the VCCTL app with virtual env works")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Problem: Missing Python modules")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    test_mix_design_panel_creation()
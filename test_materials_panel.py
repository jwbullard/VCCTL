#!/usr/bin/env python3
"""
Test Materials Panel Functionality

This script tests the materials panel components without requiring the full GUI to run.
"""

import sys
import os
from pathlib import Path

# Add the src directory to the Python path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

def test_materials_services():
    """Test the materials services work correctly."""
    print("🔧 Testing Materials Services")
    print("=" * 50)
    
    try:
        from app.services.service_container import get_service_container
        from app.models.cement import CementCreate
        
        # Get services
        services = get_service_container()
        cement_service = services.cement_service
        
        print(f"✓ Service container initialized")
        print(f"✓ Cement service available: {cement_service.__class__.__name__}")
        
        # Test creating a cement
        test_cement = CementCreate(
            name='Portland Cement Type I',
            c3s_mass_fraction=0.55,
            c2s_mass_fraction=0.20,
            c3a_mass_fraction=0.08,
            c4af_mass_fraction=0.12,
            specific_gravity=3.15,
            description='Standard Portland cement for testing'
        )
        
        created = cement_service.create(test_cement)
        print(f"✓ Created cement: {created.name}")
        
        # Test retrieving cements
        all_cements = cement_service.get_all()
        print(f"✓ Retrieved {len(all_cements)} cements from database")
        
        # Test other services
        try:
            fly_ash_service = services.fly_ash_service
            aggregate_service = services.aggregate_service
            slag_service = services.slag_service
            inert_filler_service = services.inert_filler_service
            
            print(f"✓ All material services available:")
            print(f"  - Fly Ash Service: {fly_ash_service.__class__.__name__}")
            print(f"  - Aggregate Service: {aggregate_service.__class__.__name__}")
            print(f"  - Slag Service: {slag_service.__class__.__name__}")
            print(f"  - Inert Filler Service: {inert_filler_service.__class__.__name__}")
            
        except Exception as e:
            print(f"⚠️  Some services not available: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing materials services: {e}")
        return False

def test_material_models():
    """Test that material models work correctly."""
    print("\n🧪 Testing Material Models")
    print("=" * 50)
    
    try:
        from app.models.cement import CementCreate, CementResponse
        from app.models.fly_ash import FlyAshCreate, FlyAshResponse
        from app.models.slag import SlagCreate, SlagResponse
        from app.models.aggregate import AggregateCreate, AggregateResponse
        from app.models.inert_filler import InertFillerCreate, InertFillerResponse
        
        print("✓ All material models imported successfully:")
        
        # Test cement model validation
        cement_data = CementCreate(
            name='Test Cement',
            c3s_mass_fraction=0.55,
            c2s_mass_fraction=0.20,
            c3a_mass_fraction=0.08,
            c4af_mass_fraction=0.12,
            specific_gravity=3.15
        )
        print(f"  - Cement model validation: ✓ {cement_data.name}")
        
        # Test fly ash model validation
        fly_ash_data = FlyAshCreate(
            name='Test Fly Ash',
            specific_gravity=2.2,
            aluminosilicate_glass_fraction=0.75
        )
        print(f"  - Fly Ash model validation: ✓ {fly_ash_data.name}")
        
        # Test slag model validation
        slag_data = SlagCreate(
            name='Test Slag',
            specific_gravity=2.9,
            cao_mass_fraction=0.40,
            sio2_mass_fraction=0.35
        )
        print(f"  - Slag model validation: ✓ {slag_data.name}")
        
        # Test aggregate model validation  
        aggregate_data = AggregateCreate(
            display_name='Test Aggregate',
            name='Test Aggregate',
            type=2,  # 2 = fine aggregate
            specific_gravity=2.65
        )
        print(f"  - Aggregate model validation: ✓ {aggregate_data.name}")
        
        # Test inert filler model validation
        filler_data = InertFillerCreate(
            name='Test Filler',
            specific_gravity=2.7
        )
        print(f"  - Inert Filler model validation: ✓ {filler_data.name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing material models: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_material_dialog_classes():
    """Test that material dialog classes can be imported."""
    print("\n📱 Testing Material Dialog Classes")
    print("=" * 50)
    
    try:
        from app.windows.dialogs.material_dialog import (
            MaterialDialogBase,
            CementDialog,
            AggregateDialog,
            FlyAshDialog,
            SlagDialog,
            InertFillerDialog,
            create_material_dialog
        )
        
        print("✓ All material dialog classes imported successfully:")
        print(f"  - Base Dialog: {MaterialDialogBase.__name__}")
        print(f"  - Cement Dialog: {CementDialog.__name__}")
        print(f"  - Aggregate Dialog: {AggregateDialog.__name__}")
        print(f"  - Fly Ash Dialog: {FlyAshDialog.__name__}")
        print(f"  - Slag Dialog: {SlagDialog.__name__}")
        print(f"  - Inert Filler Dialog: {InertFillerDialog.__name__}")
        print(f"  - Dialog Factory: {create_material_dialog.__name__}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error importing dialog classes: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_widget_imports():
    """Test that widget classes can be imported."""
    print("\n🔧 Testing Widget Classes")
    print("=" * 50)
    
    try:
        from app.widgets.material_table import MaterialTable, MaterialTableColumn
        from app.widgets.grading_curve import GradingCurveWidget
        from app.widgets.file_browser import FileBrowserWidget
        
        print("✓ All widget classes imported successfully:")
        print(f"  - Material Table: {MaterialTable.__name__}")
        print(f"  - Material Table Columns: {MaterialTableColumn.__name__}")
        print(f"  - Grading Curve Widget: {GradingCurveWidget.__name__}")
        print(f"  - File Browser Widget: {FileBrowserWidget.__name__}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error importing widget classes: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_materials_panel_import():
    """Test that the materials panel can be imported."""
    print("\n📋 Testing Materials Panel")
    print("=" * 50)
    
    try:
        from app.windows.panels.materials_panel import MaterialsPanel
        
        print("✓ Materials Panel imported successfully:")
        print(f"  - Panel Class: {MaterialsPanel.__name__}")
        
        # Check if the class has the expected methods
        expected_methods = [
            '_setup_ui', '_create_header', '_create_content_area', 
            '_load_initial_data', '_on_add_material_clicked',
            '_show_material_dialog', 'refresh_data'
        ]
        
        missing_methods = []
        for method in expected_methods:
            if not hasattr(MaterialsPanel, method):
                missing_methods.append(method)
        
        if missing_methods:
            print(f"⚠️  Missing methods: {missing_methods}")
        else:
            print("✓ All expected methods present")
        
        return len(missing_methods) == 0
        
    except Exception as e:
        print(f"❌ Error importing materials panel: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all materials panel tests."""
    print("🧪 VCCTL Materials Panel Tests")
    print("=" * 60)
    
    tests = [
        test_materials_services,
        test_material_models,
        test_material_dialog_classes,
        test_widget_imports,
        test_materials_panel_import
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("✅ All tests passed! Materials panel is ready.")
        print("\nNext steps:")
        print("1. Fix GTK3 library issues for GUI testing")
        print("2. Test materials panel in full application")
        print("3. Complete remaining UI polish")
    else:
        print("❌ Some tests failed. Check the output above for details.")
    
    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
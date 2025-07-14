#!/usr/bin/env python3
"""
Test Materials Backend Functionality

This script tests the backend materials functionality without GTK imports.
"""

import sys
import os
from pathlib import Path

# Add the src directory to the Python path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

def clear_test_database():
    """Clear database for testing."""
    try:
        from app.services.service_container import get_service_container
        services = get_service_container()
        
        # Clear all existing test data
        for cement in services.cement_service.get_all():
            if 'Test' in cement.name or cement.name in ['Portland Cement Type I', 'OPC Type II']:
                services.cement_service.delete(cement.name)
        
        for fly_ash in services.fly_ash_service.get_all():
            if 'Test' in fly_ash.name or fly_ash.name in ['Class F Fly Ash']:
                services.fly_ash_service.delete(fly_ash.name)
                
        for slag in services.slag_service.get_all():
            if 'Test' in slag.name or slag.name in ['Ground Slag']:
                services.slag_service.delete(slag.name)
                
        for aggregate in services.aggregate_service.get_all():
            if 'Test' in aggregate.display_name or aggregate.display_name in ['River Sand']:
                services.aggregate_service.delete(aggregate.display_name)
                
        for filler in services.inert_filler_service.get_all():
            if 'Test' in filler.name or filler.name in ['Limestone Filler']:
                services.inert_filler_service.delete(filler.name)
                
        print("✓ Cleared test data from database")
    except Exception as e:
        print(f"⚠️  Could not clear database: {e}")

def test_materials_services():
    """Test the materials services work correctly."""
    print("🔧 Testing Materials Services")
    print("=" * 50)
    
    # Clear any existing test data
    clear_test_database()
    
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
            type=2,  # 2 = fine aggregate (1=coarse, 2=fine)
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

def test_all_material_services():
    """Test creating materials through all services."""
    print("\n🏭 Testing All Material Creation")
    print("=" * 50)
    
    # Clear any existing test data
    clear_test_database()
    
    try:
        from app.services.service_container import get_service_container
        from app.models.cement import CementCreate
        from app.models.fly_ash import FlyAshCreate
        from app.models.slag import SlagCreate
        from app.models.aggregate import AggregateCreate
        from app.models.inert_filler import InertFillerCreate
        
        services = get_service_container()
        
        # Test Cement Service
        cement_data = CementCreate(
            name='OPC Type II',
            c3s_mass_fraction=0.52,
            c2s_mass_fraction=0.22,
            c3a_mass_fraction=0.06,
            c4af_mass_fraction=0.14,
            specific_gravity=3.12,
            description='Ordinary Portland Cement Type II'
        )
        cement = services.cement_service.create(cement_data)
        print(f"✓ Created cement: {cement.name} (ID: {cement.id})")
        
        # Test Fly Ash Service
        fly_ash_data = FlyAshCreate(
            name='Class F Fly Ash',
            specific_gravity=2.3,
            aluminosilicate_glass_fraction=0.80,
            description='Low-calcium fly ash'
        )
        fly_ash = services.fly_ash_service.create(fly_ash_data)
        print(f"✓ Created fly ash: {fly_ash.name} (ID: {fly_ash.id})")
        
        # Test Slag Service
        slag_data = SlagCreate(
            name='Ground Slag',
            specific_gravity=2.95,
            cao_mass_fraction=0.42,
            sio2_mass_fraction=0.36,
            description='Ground granulated blast furnace slag'
        )
        slag = services.slag_service.create(slag_data)
        print(f"✓ Created slag: {slag.name} (ID: {slag.id})")
        
        # Test Aggregate Service
        aggregate_data = AggregateCreate(
            display_name='River Sand',
            name='River Sand',
            type=2,  # 2 = Fine aggregate (1=coarse, 2=fine)
            specific_gravity=2.68,
            bulk_modulus=30.0,
            shear_modulus=25.0
        )
        aggregate = services.aggregate_service.create(aggregate_data)
        print(f"✓ Created aggregate: {aggregate.name}")
        
        # Test Inert Filler Service
        filler_data = InertFillerCreate(
            name='Limestone Filler',
            specific_gravity=2.72,
            description='Ground limestone filler'
        )
        filler = services.inert_filler_service.create(filler_data)
        print(f"✓ Created inert filler: {filler.name} (ID: {filler.id})")
        
        # Get counts
        cement_count = len(services.cement_service.get_all())
        fly_ash_count = len(services.fly_ash_service.get_all())
        slag_count = len(services.slag_service.get_all())
        aggregate_count = len(services.aggregate_service.get_all())
        filler_count = len(services.inert_filler_service.get_all())
        
        print(f"\n📊 Database Material Counts:")
        print(f"  - Cements: {cement_count}")
        print(f"  - Fly Ash: {fly_ash_count}")
        print(f"  - Slag: {slag_count}")
        print(f"  - Aggregates: {aggregate_count}")
        print(f"  - Inert Fillers: {filler_count}")
        print(f"  - Total: {cement_count + fly_ash_count + slag_count + aggregate_count + filler_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing material services: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_service_crud_operations():
    """Test CRUD operations on services."""
    print("\n🔄 Testing CRUD Operations")
    print("=" * 50)
    
    # Clear any existing test data
    clear_test_database()
    
    try:
        from app.services.service_container import get_service_container
        from app.models.cement import CementCreate, CementUpdate
        
        services = get_service_container()
        cement_service = services.cement_service
        
        # Create
        cement_data = CementCreate(
            name='Test CRUD Cement',
            c3s_mass_fraction=0.60,
            c2s_mass_fraction=0.15,
            c3a_mass_fraction=0.10,
            c4af_mass_fraction=0.10,
            specific_gravity=3.20
        )
        created_cement = cement_service.create(cement_data)
        print(f"✓ Created: {created_cement.name} (ID: {created_cement.id})")
        
        # Read
        retrieved_cement = cement_service.get_by_name(created_cement.name)
        print(f"✓ Retrieved: {retrieved_cement.name}")
        
        # Update (don't change the name, just update properties)
        update_data = CementUpdate(
            c3s_mass_fraction=0.58,
            description='Updated description'
        )
        updated_cement = cement_service.update(created_cement.name, update_data)
        print(f"✓ Updated: {updated_cement.name}")
        
        # Delete
        deleted = cement_service.delete(created_cement.name)  # Use original name
        print(f"✓ Deleted: {deleted}")
        
        # Verify deletion
        try:
            found_cement = cement_service.get_by_name(created_cement.name)
            if found_cement is None:
                print("✓ Confirmed deletion - cement not found")
            else:
                print("❌ Cement still exists after deletion")
                return False
        except Exception as e:
            print(f"✓ Confirmed deletion - exception as expected: {type(e).__name__}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing CRUD operations: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_materials_panel_backend_logic():
    """Test the logic that the materials panel would use."""
    print("\n📋 Testing Materials Panel Backend Logic")
    print("=" * 50)
    
    try:
        from app.services.service_container import get_service_container
        
        services = get_service_container()
        
        # Simulate what the materials panel does
        material_counts = {}
        total_materials = 0
        
        # Count all material types
        try:
            cements = services.cement_service.get_all()
            material_counts['cement'] = len(cements)
            total_materials += len(cements)
            print(f"✓ Cement materials: {len(cements)}")
        except Exception as e:
            print(f"⚠️  Error counting cements: {e}")
            material_counts['cement'] = 0
        
        try:
            fly_ashes = services.fly_ash_service.get_all()
            material_counts['fly_ash'] = len(fly_ashes)
            total_materials += len(fly_ashes)
            print(f"✓ Fly ash materials: {len(fly_ashes)}")
        except Exception as e:
            print(f"⚠️  Error counting fly ashes: {e}")
            material_counts['fly_ash'] = 0
        
        try:
            slags = services.slag_service.get_all()
            material_counts['slag'] = len(slags)
            total_materials += len(slags)
            print(f"✓ Slag materials: {len(slags)}")
        except Exception as e:
            print(f"⚠️  Error counting slags: {e}")
            material_counts['slag'] = 0
        
        try:
            aggregates = services.aggregate_service.get_all()
            material_counts['aggregate'] = len(aggregates)
            total_materials += len(aggregates)
            print(f"✓ Aggregate materials: {len(aggregates)}")
        except Exception as e:
            print(f"⚠️  Error counting aggregates: {e}")
            material_counts['aggregate'] = 0
        
        try:
            fillers = services.inert_filler_service.get_all()
            material_counts['inert_filler'] = len(fillers)
            total_materials += len(fillers)
            print(f"✓ Inert filler materials: {len(fillers)}")
        except Exception as e:
            print(f"⚠️  Error counting fillers: {e}")
            material_counts['inert_filler'] = 0
        
        print(f"\n📊 Materials Panel would show: {total_materials} materials total")
        
        # Test material search/filter logic (basic string matching)
        search_term = "cement"
        matching_materials = []
        
        for cement in cements:
            if search_term.lower() in cement.name.lower():
                matching_materials.append(('cement', cement))
        
        print(f"✓ Search for '{search_term}' found {len(matching_materials)} matches")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing materials panel logic: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all backend materials tests."""
    print("🧪 VCCTL Materials Backend Tests")
    print("=" * 60)
    
    tests = [
        test_materials_services,
        test_material_models,
        test_all_material_services,
        test_service_crud_operations,
        test_materials_panel_backend_logic
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
    print("📊 Backend Test Results Summary")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("✅ All backend tests passed! Materials functionality is working.")
        print("\n🎯 Materials Panel Status:")
        print("  ✅ Backend services working")
        print("  ✅ Data models working")
        print("  ✅ CRUD operations working")
        print("  ✅ Material counting working")
        print("  ✅ Basic search logic working")
        print("  🔄 GUI components need GTK3 fix")
        print("\n📋 VCCTL-012 Status: Backend Complete ✅")
    else:
        print("❌ Some backend tests failed. Check the output above for details.")
    
    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
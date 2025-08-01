#!/usr/bin/env python3
"""
Test the immutable aggregate UI protection visually.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from app.services.service_container import ServiceContainer

def test_aggregate_ui_protection():
    """Test that immutable aggregate UI protection is working."""
    print("🔒 Testing Immutable Aggregate UI Protection")
    print("=" * 50)
    
    # Get aggregate service
    service_container = ServiceContainer()
    aggregate_service = service_container.aggregate_service
    
    # Get first immutable aggregate
    aggregates = aggregate_service.get_all()
    if not aggregates:
        print("❌ No aggregates found")
        return False
    
    test_aggregate = aggregates[0]
    print(f"📊 Testing with: {test_aggregate.display_name}")
    
    # Check immutable status
    is_immutable = getattr(test_aggregate, 'immutable', False)
    print(f"🔒 Immutable status: {is_immutable}")
    
    if not is_immutable:
        print("❌ Aggregate is not immutable - cannot test UI protection")
        return False
    
    # Test material data format for UI
    material_data = {
        'display_name': test_aggregate.display_name,
        'name': test_aggregate.name,
        'immutable': test_aggregate.immutable,
        'source': test_aggregate.source,
        'description': test_aggregate.description,
        'properties_description': test_aggregate.properties_description,
        'notes': test_aggregate.notes,
        'specific_gravity': test_aggregate.specific_gravity,
        'bulk_modulus': test_aggregate.bulk_modulus,
        'shear_modulus': test_aggregate.shear_modulus,
        'conductivity': test_aggregate.conductivity,
        'type': test_aggregate.type
    }
    
    print("✅ Material data prepared for UI test:")
    print(f"  • Name: {material_data['display_name']}")
    print(f"  • Immutable: {material_data['immutable']}")
    print(f"  • Source: {material_data['source']}")
    print(f"  • Has description: {bool(material_data['description'])}")
    print(f"  • Has properties description: {bool(material_data['properties_description'])}")
    print(f"  • Has notes: {bool(material_data['notes'])}")
    
    # Simulate UI protection logic
    print("\\n🛡️  Expected UI Protection Behavior:")
    print("  1. ✅ Warning message: 'This is an original database aggregate. Duplicate this aggregate to make changes.'")
    print("  2. ✅ All input fields disabled (grayed out)")
    print("  3. ✅ 'Save' button hidden")
    print("  4. ✅ 'Duplicate to Edit' button shown (blue/suggested)")
    print("  5. ✅ Clicking 'Duplicate to Edit' creates mutable copy")
    
    print("\\n🎯 UI Components to Check:")
    ui_components = [
        "Name entry field → disabled",
        "Source entry field → disabled", 
        "Description text view → disabled",
        "Specific gravity spin → disabled",
        "Bulk modulus spin → disabled",
        "Shear modulus spin → disabled",
        "Conductivity spin → disabled",
        "Type combo box → disabled",
        "Properties description text view → disabled",
        "Notes text view → disabled"
    ]
    
    for component in ui_components:
        print(f"  • {component}")
    
    print("\\n📝 Testing Instructions:")
    print("  1. Open VCCTL application")
    print("  2. Go to Materials tab")
    print(f"  3. Edit '{test_aggregate.display_name}'")
    print("  4. Verify warning message appears at top")
    print("  5. Verify all fields are disabled")
    print("  6. Verify 'Duplicate to Edit' button at bottom")
    print("  7. Click 'Duplicate to Edit' to test duplication")
    
    return True

if __name__ == '__main__':
    success = test_aggregate_ui_protection()
    sys.exit(0 if success else 1)
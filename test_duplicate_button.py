#!/usr/bin/env python3
"""
Test the duplicate button functionality directly.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from app.services.service_container import ServiceContainer

def test_duplicate_functionality():
    """Test the duplicate functionality directly."""
    print("🔄 Testing Duplicate Button Functionality")
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
    
    # Simulate the duplication logic
    try:
        print("\\n🔧 Testing duplication logic...")
        
        # Step 1: Create new name
        original_name = test_aggregate.display_name
        new_name = f"{original_name}_copy"
        counter = 1
        final_name = new_name
        
        print(f"Original name: {original_name}")
        print(f"Proposed name: {new_name}")
        
        # Step 2: Check for conflicts
        while aggregate_service.get_by_name(final_name):
            counter += 1
            final_name = f"{new_name}_{counter}"
            print(f"Conflict found, trying: {final_name}")
        
        print(f"✅ Final name: {final_name}")
        
        # Step 3: Prepare data
        duplicate_data = {
            'display_name': final_name,
            'name': final_name,
            'source': test_aggregate.source,
            'description': test_aggregate.description,
            'properties_description': getattr(test_aggregate, 'properties_description', ''),
            'notes': test_aggregate.notes,
            'specific_gravity': test_aggregate.specific_gravity,
            'bulk_modulus': test_aggregate.bulk_modulus,
            'shear_modulus': test_aggregate.shear_modulus,
            'conductivity': test_aggregate.conductivity,
            'type': test_aggregate.type,
            'immutable': False  # Make it editable
        }
        
        print("\\n📋 Duplicate data prepared:")
        for key, value in duplicate_data.items():
            print(f"  • {key}: {repr(value)[:50]}{'...' if len(str(value)) > 50 else ''}")
        
        # Step 4: Test creation (but don't actually create)
        from app.models.aggregate import AggregateCreate
        create_data = AggregateCreate(**duplicate_data)
        print("\\n✅ AggregateCreate validation passed")
        
        # Ask if we should actually create the duplicate for testing
        response = input("\\n❓ Create test duplicate? (y/N): ").strip().lower()
        if response == 'y':
            print("Creating duplicate...")
            created_aggregate = aggregate_service.create(create_data)
            print(f"✅ Successfully created: {created_aggregate.display_name}")
            print(f"   Immutable: {created_aggregate.immutable}")
            
            # Clean up - delete the test duplicate
            cleanup = input("Delete test duplicate? (Y/n): ").strip().lower()
            if cleanup != 'n':
                aggregate_service.delete(created_aggregate.display_name)
                print("✅ Test duplicate cleaned up")
        else:
            print("✅ Duplication logic validated (no actual creation)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in duplication logic: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_duplicate_functionality()
    sys.exit(0 if success else 1)
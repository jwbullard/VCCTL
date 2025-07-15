#!/usr/bin/env python3
"""Test script to verify material loading fix."""

import sys
sys.path.insert(0, 'src')

from app.services.service_container import get_service_container

# Get service container
service_container = get_service_container()

# Test cement materials
print("=== CEMENT MATERIALS ===")
cement_service = service_container.cement_service
cements = cement_service.get_all()
for cement in cements:
    material_data = {
        'id': cement.name,  # Fixed: use name as ID
        'name': cement.name,
        'type': 'cement',
        'specific_gravity': cement.specific_gravity,
    }
    print(f"✓ {material_data}")

# Test aggregate materials  
print("\n=== AGGREGATE MATERIALS ===")
aggregate_service = service_container.aggregate_service
aggregates = aggregate_service.get_all()
for aggregate in aggregates:
    material_data = {
        'id': aggregate.display_name,  # Fixed: use display_name as ID
        'name': aggregate.name,
        'type': 'aggregate',
        'specific_gravity': aggregate.specific_gravity,
    }
    print(f"✓ {material_data}")

print(f"\n✓ Total materials that should appear in UI: {len(cements) + len(aggregates)}")
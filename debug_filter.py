#!/usr/bin/env python3
"""Debug script to test material filtering."""

import sys
sys.path.insert(0, 'src')

# Test the materials data that would be created
from app.services.service_container import get_service_container

service_container = get_service_container()

# Create materials list exactly like the UI does
materials = []

# Load cement materials
cement_service = service_container.cement_service
cements = cement_service.get_all()
for cement in cements:
    materials.append({
        'id': cement.name,
        'name': cement.name,
        'type': 'cement',
        'specific_gravity': cement.specific_gravity,
        'created_date': cement.created_at.strftime('%Y-%m-%d') if cement.created_at else '',
        'modified_date': cement.updated_at.strftime('%Y-%m-%d') if cement.updated_at else '',
        'description': cement.description or '',
        'data': cement
    })

# Load aggregate materials  
aggregate_service = service_container.aggregate_service
aggregates = aggregate_service.get_all()
for aggregate in aggregates:
    materials.append({
        'id': aggregate.display_name,
        'name': aggregate.name,
        'type': 'aggregate',
        'specific_gravity': aggregate.specific_gravity,
        'created_date': aggregate.created_at.strftime('%Y-%m-%d') if aggregate.created_at else '',
        'modified_date': aggregate.updated_at.strftime('%Y-%m-%d') if aggregate.updated_at else '',
        'description': getattr(aggregate, 'description', '') or '',
        'data': aggregate
    })

print(f"Total materials created: {len(materials)}")
print("\nMaterials data:")
for i, material in enumerate(materials):
    print(f"{i}: {material['name']} - type: '{material['type']}' - sg: {material['specific_gravity']}")

print("\n=== Testing Filter Logic ===")
# Test cement filter
type_filter = 'cement'
cement_matches = [m for m in materials if m['type'] == type_filter]
print(f"Materials matching 'cement' filter: {len(cement_matches)}")
for m in cement_matches:
    print(f"  ✓ {m['name']}")

# Test aggregate filter  
type_filter = 'aggregate'
aggregate_matches = [m for m in materials if m['type'] == type_filter]
print(f"Materials matching 'aggregate' filter: {len(aggregate_matches)}")
for m in aggregate_matches:
    print(f"  ✓ {m['name']}")
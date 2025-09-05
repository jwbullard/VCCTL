#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, '/Users/jwbullard/Software/vcctl-gtk/src')

try:
    from app.services.service_container import get_service_container
    from app.models.silica_fume import SilicaFumeCreate, SilicaFumeUpdate
    
    # Test silica fume duplication workflow
    container = get_service_container()
    service = container.silica_fume_service
    
    # Get existing silica fume
    silica_fumes = service.get_all() 
    print(f"Found {len(silica_fumes)} silica fumes")
    
    if silica_fumes:
        original = silica_fumes[0]
        print(f"Original: {original.name}")
        print(f"  silica_content: {getattr(original, 'silica_content', 'MISSING')}")
        print(f"  surface_area: {getattr(original, 'surface_area', 'MISSING')}")
        print(f"  silica_fume_fraction: {getattr(original, 'silica_fume_fraction', 'MISSING')}")
        
        # Create duplicate data (simulating the duplication process)
        duplicate_data = {
            'name': 'Test_Duplicate_SF',
            'specific_gravity': getattr(original, 'specific_gravity', 2.22),
            'silica_content': getattr(original, 'silica_content', 92.0),
            'surface_area': getattr(original, 'surface_area', 20000.0),  
            'silica_fume_fraction': getattr(original, 'silica_fume_fraction', 1.0),
            'description': getattr(original, 'description', ''),
            'source': getattr(original, 'source', ''),
            'notes': getattr(original, 'notes', ''),
        }
        
        print(f"Duplicate data: {duplicate_data}")
        
        # Create the duplicate
        create_model = SilicaFumeCreate(**duplicate_data)
        new_sf = service.create(create_model)
        print(f"Created duplicate: {new_sf.name}")
        
        # Now test updating the duplicate (simulating editing)
        update_data = SilicaFumeUpdate(
            silica_content=95.0,  # Modified value
            surface_area=25000.0  # Modified value
        )
        
        updated_sf = service.update(new_sf.id, update_data)
        print(f"Updated duplicate: silica_content={updated_sf.silica_content}, surface_area={updated_sf.surface_area}")
        
        # Clean up
        service.delete(new_sf.name)
        print("Test successful!")
        
except Exception as e:
    print(f"Error during test: {e}")
    import traceback
    traceback.print_exc()

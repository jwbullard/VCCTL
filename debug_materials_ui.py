#!/usr/bin/env python3
"""Debug script to test material loading in UI components."""

import sys
import os
sys.path.insert(0, 'src')

import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('MaterialsDebug')

try:
    # Test service container initialization
    from app.services.service_container import ServiceContainer, get_service_container
    
    print("1. Testing service container...")
    service_container = get_service_container()
    print(f"   Service container: {service_container}")
    
    # Test cement service
    print("2. Testing cement service...")
    cement_service = service_container.cement_service
    print(f"   Cement service: {cement_service}")
    
    # Test get_all method
    print("3. Testing cement service get_all()...")
    cements = cement_service.get_all()
    print(f"   Found {len(cements)} cements:")
    for cement in cements:
        print(f"   - {cement.name} (ID: {cement.id})")
    
    # Test database service directly
    print("4. Testing database service...")
    db_service = service_container.db_service
    print(f"   Database service: {db_service}")
    print(f"   Database exists: {db_service.config.database_exists()}")
    print(f"   Database size: {db_service.config.get_database_size()} bytes")
    
    print("\n✓ All tests passed - materials should be visible in UI")
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
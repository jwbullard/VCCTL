#!/usr/bin/env python3
"""Test script for Step 4 - Model imports validation"""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
src_path = project_root / 'src'
sys.path.insert(0, str(src_path))

try:
    from app.models import get_all_models, InertFiller, Filler, FillerCreate
    
    print("=== Step 4 Testing Results ===")
    
    # Test 1: Count all models
    all_models = get_all_models()
    print(f"✅ Total models available: {len(all_models)}")
    
    # Test 2: Verify InertFiller exists
    print(f"✅ InertFiller model accessible: {InertFiller}")
    
    # Test 3: Verify Filler exists  
    print(f"✅ Filler model accessible: {Filler}")
    
    # Test 4: Verify Pydantic schemas
    test_filler = FillerCreate(name="TestFiller", specific_gravity=2.5)
    print(f"✅ FillerCreate validation works: {test_filler.name}")
    
    print("\n🎉 Step 4: All tests passed! Models working correctly.")
    
except Exception as e:
    print(f"❌ Step 4 failed: {e}")
    import traceback
    traceback.print_exc()
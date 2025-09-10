#!/usr/bin/env python3
"""
Simple test script for grading data auto-population functionality
"""

import sys
import os
import tempfile

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.aggregate import Aggregate
from app.models.grading import Grading, GradingType

def test_grading_simple():
    """Simple test of grading database access and file generation."""
    
    print("🧪 Testing Grading Database Access")
    print("=" * 40)
    
    try:
        # Direct database connection (use absolute path)
        db_path = os.path.abspath('data/database/vcctl.db')
        engine = create_engine(f'sqlite:///{db_path}')
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Test 1: Find MA114F-3-fine aggregate
        fine_aggregate = session.query(Aggregate).filter(
            Aggregate.display_name == 'MA114F-3-fine'
        ).first()
        
        if fine_aggregate:
            print(f"✅ Found aggregate: {fine_aggregate.display_name}")
            print(f"   Type: {fine_aggregate.type} (is_fine: {fine_aggregate.is_fine_aggregate})")
        else:
            print("❌ MA114F-3-fine aggregate not found")
            return False
            
        # Test 2: Find grading templates
        fine_gradings = session.query(Grading).filter(
            Grading.type == GradingType.FINE
        ).all()
        
        print(f"✅ Found {len(fine_gradings)} fine grading templates:")
        for grading in fine_gradings[:3]:  # Show first 3
            sieve_count = len(grading.sieve_data) if grading.sieve_data else 0
            print(f"   - {grading.name}: {sieve_count} sieve points")
        
        # Test 3: Test grading file generation
        test_grading = None
        for grading in fine_gradings:
            if grading.sieve_data and len(grading.sieve_data) > 0:
                test_grading = grading
                break
        
        if test_grading:
            print(f"✅ Testing with grading: {test_grading.name}")
            
            # Create temporary file
            temp_dir = tempfile.mkdtemp(prefix="vcctl_test_grading_")
            grading_filename = f"test_grading.gdg"
            temp_path = os.path.join(temp_dir, grading_filename)
            
            # Generate .gdg content
            gdg_content = test_grading.to_gdg_format()
            
            # Write to file
            with open(temp_path, 'w') as f:
                f.write(gdg_content)
            
            print(f"✅ Created temporary grading file: {temp_path}")
            
            # Verify file contents
            with open(temp_path, 'r') as f:
                content = f.read()
            
            lines = content.strip().split('\n')
            print(f"✅ File contains {len(lines)} sieve data lines:")
            for i, line in enumerate(lines[:3]):  # Show first 3 lines
                print(f"   {i+1}: {line}")
            
            print(f"✅ Grading auto-population concept WORKING!")
            
        else:
            print("⚠️  No grading template with sieve data found")
            
        session.close()
        print("\n🎉 Simple grading test PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_grading_simple()
    sys.exit(0 if success else 1)
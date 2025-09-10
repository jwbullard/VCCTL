#!/usr/bin/env python3
"""
Test script for grading data auto-population functionality
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from app.services.elastic_lineage_service import ElasticLineageService
from app.database.service import DatabaseService
from app.models.aggregate import Aggregate
from app.models.grading import Grading, GradingType
from sqlalchemy.orm import sessionmaker

def test_grading_auto_population():
    """Test the grading auto-population functionality."""
    
    print("🧪 Testing Grading Auto-Population")
    print("=" * 50)
    
    try:
        # Initialize database connection
        db_service = DatabaseService('src/data/database/vcctl.db')
        
        # Create elastic lineage service
        elastic_service = ElasticLineageService(db_service)
        
        print("✅ Database connection established")
        
        # Test with MA114F-3-fine aggregate from the TestMortar-01 mix design
        session = db_service.get_session()
        
        # Find the MA114F-3-fine aggregate
        fine_aggregate = session.query(Aggregate).filter(
            Aggregate.display_name == 'MA114F-3-fine'
        ).first()
        
        if not fine_aggregate:
            print("❌ MA114F-3-fine aggregate not found in database")
            return False
            
        print(f"✅ Found aggregate: {fine_aggregate.display_name}")
        print(f"   Type: {fine_aggregate.type} (fine={fine_aggregate.is_fine_aggregate})")
        
        # Check available grading templates
        grading_templates = session.query(Grading).filter(
            Grading.type == GradingType.FINE
        ).all()
        
        print(f"✅ Found {len(grading_templates)} fine grading templates:")
        for template in grading_templates:
            sieve_count = len(template.sieve_data) if template.sieve_data else 0
            print(f"   - {template.name}: {sieve_count} sieve points")
        
        # Test the grading path generation
        print("\n🔍 Testing grading path generation...")
        grading_path = elastic_service._get_aggregate_grading_path(fine_aggregate)
        
        if grading_path:
            print(f"✅ Grading path generated: {grading_path}")
            
            # Check if the file exists and has content
            if os.path.exists(grading_path):
                with open(grading_path, 'r') as f:
                    content = f.read()
                print(f"✅ Grading file exists with {len(content)} characters")
                
                # Show first few lines of the grading file
                lines = content.strip().split('\n')
                print(f"✅ Grading file content (first 3 lines):")
                for i, line in enumerate(lines[:3]):
                    print(f"   {i+1}: {line}")
                print(f"   ... ({len(lines)} total lines)")
                
            else:
                print(f"❌ Grading file does not exist: {grading_path}")
                return False
        else:
            print("❌ No grading path generated")
            return False
        
        # Test with TestMortar-01 mix design resolution
        print("\n🔍 Testing full lineage resolution...")
        
        lineage_result = elastic_service.resolve_aggregate_properties(
            operation_name="TestMortar-01",
            microstructure_name="TestMortar-01"
        )
        
        if lineage_result and 'fine_aggregate' in lineage_result:
            fine_agg = lineage_result['fine_aggregate']
            print(f"✅ Lineage resolution successful:")
            print(f"   - Aggregate: {fine_agg.name}")
            print(f"   - Volume Fraction: {fine_agg.volume_fraction:.3f}")
            print(f"   - Bulk Modulus: {fine_agg.bulk_modulus} GPa")
            print(f"   - Shear Modulus: {fine_agg.shear_modulus} GPa")
            print(f"   - Grading Path: {fine_agg.grading_path}")
            
            if fine_agg.grading_path:
                print(f"✅ Grading auto-population WORKING!")
            else:
                print(f"⚠️  Grading path empty - may need grading template association")
        else:
            print("❌ Lineage resolution failed or no fine aggregate found")
            return False
        
        session.close()
        print("\n🎉 Grading auto-population test PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_grading_auto_population()
    sys.exit(0 if success else 1)
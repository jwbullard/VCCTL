#!/usr/bin/env python3
"""
Test script for grading template persistence functionality

Validates database schema updates and model integration.
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.models.mix_design import MixDesign, MixDesignCreate, MixDesignUpdate, MixDesignResponse

def test_grading_template_persistence():
    """Test grading template persistence functionality."""
    
    print("🧪 Testing Grading Template Persistence")
    print("=" * 50)
    
    # Test 1: Database Schema Verification
    print("🔧 Test 1: Database Schema Verification")
    
    db_path = 'src/data/database/vcctl.db'
    engine = create_engine(f'sqlite:///{db_path}')
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Check table structure
        result = session.execute(text("PRAGMA table_info(mix_design)"))
        columns = {row[1]: row[2] for row in result}
        
        required_fields = ['fine_aggregate_grading_template', 'coarse_aggregate_grading_template']
        found_fields = [field for field in required_fields if field in columns]
        
        if len(found_fields) == len(required_fields):
            print("   ✅ Database schema includes grading template fields")
            for field in found_fields:
                print(f"     - {field}: {columns[field]}")
        else:
            print(f"   ❌ Missing grading template fields: {set(required_fields) - set(found_fields)}")
            return False
        
        print()
        
        # Test 2: SQLAlchemy Model Verification
        print("🔧 Test 2: SQLAlchemy Model Verification")
        
        # Check if the model attributes exist
        model_attrs = dir(MixDesign)
        model_grading_fields = [attr for attr in model_attrs if 'grading_template' in attr]
        
        if len(model_grading_fields) == 2:
            print("   ✅ SQLAlchemy model includes grading template attributes")
            for field in model_grading_fields:
                print(f"     - {field}")
        else:
            print(f"   ❌ SQLAlchemy model missing grading template attributes")
            return False
            
        print()
        
        # Test 3: Pydantic Model Verification
        print("🔧 Test 3: Pydantic Model Verification")
        
        # Test Create model
        create_fields = MixDesignCreate.__fields__.keys()
        create_grading_fields = [f for f in create_fields if 'grading_template' in f]
        
        # Test Update model  
        update_fields = MixDesignUpdate.__fields__.keys()
        update_grading_fields = [f for f in update_fields if 'grading_template' in f]
        
        # Test Response model
        response_fields = MixDesignResponse.__fields__.keys()
        response_grading_fields = [f for f in response_fields if 'grading_template' in f]
        
        all_models_valid = all([
            len(create_grading_fields) == 2,
            len(update_grading_fields) == 2, 
            len(response_grading_fields) == 2
        ])
        
        if all_models_valid:
            print("   ✅ All Pydantic models include grading template fields")
            print(f"     - MixDesignCreate: {create_grading_fields}")
            print(f"     - MixDesignUpdate: {update_grading_fields}")
            print(f"     - MixDesignResponse: {response_grading_fields}")
        else:
            print("   ❌ Pydantic models missing grading template fields")
            return False
            
        print()
        
        # Test 4: Database Operations
        print("🔧 Test 4: Database Write/Read Operations")
        
        # Find a mix design with aggregates for testing
        result = session.execute(text('''
            SELECT id, name, fine_aggregate_name, coarse_aggregate_name 
            FROM mix_design 
            WHERE (fine_aggregate_name IS NOT NULL AND fine_aggregate_mass > 0)
               OR (coarse_aggregate_name IS NOT NULL AND coarse_aggregate_mass > 0)
            LIMIT 1
        '''))
        
        test_mix = result.fetchone()
        if not test_mix:
            print("   ⚠️  No mix designs with aggregates found for testing")
            return True
        
        mix_id, mix_name, fine_agg, coarse_agg = test_mix
        print(f"   Testing with: {mix_name} (ID: {mix_id})")
        print(f"   Fine aggregate: {fine_agg}")
        print(f"   Coarse aggregate: {coarse_agg}")
        
        # Test writing grading template associations
        test_templates = {}
        if fine_agg:
            test_templates['fine_aggregate_grading_template'] = 'AFineGrading'
        if coarse_agg:
            test_templates['coarse_aggregate_grading_template'] = 'ASTM #67 Stone'
        
        if test_templates:
            # Build UPDATE query dynamically
            set_clauses = []
            params = {'mix_id': mix_id}
            
            for field, value in test_templates.items():
                set_clauses.append(f"{field} = :{field}")
                params[field] = value
            
            update_sql = f"UPDATE mix_design SET {', '.join(set_clauses)} WHERE id = :mix_id"
            
            session.execute(text(update_sql), params)
            session.commit()
            
            # Test reading back the values
            select_fields = ', '.join(test_templates.keys())
            read_sql = f"SELECT {select_fields} FROM mix_design WHERE id = :mix_id"
            result = session.execute(text(read_sql), {'mix_id': mix_id})
            row = result.fetchone()
            
            if row:
                all_match = True
                for i, (field, expected_value) in enumerate(test_templates.items()):
                    actual_value = row[i]
                    match = actual_value == expected_value
                    print(f"   {field}: {actual_value} {'✅' if match else '❌'}")
                    if not match:
                        all_match = False
                
                if all_match:
                    print("   ✅ Database write/read operations successful")
                else:
                    print("   ❌ Database operations failed - values don't match")
                    return False
            else:
                print("   ❌ Failed to read back grading template values")
                return False
            
            # Cleanup - reset to NULL
            cleanup_clauses = [f"{field} = NULL" for field in test_templates.keys()]
            cleanup_sql = f"UPDATE mix_design SET {', '.join(cleanup_clauses)} WHERE id = :mix_id"
            session.execute(text(cleanup_sql), {'mix_id': mix_id})
            session.commit()
            print("   ✅ Test cleanup completed")
        
        print()
        
        # Test 5: Model Integration Test
        print("🔧 Test 5: SQLAlchemy Model Integration")
        
        # Try to query using SQLAlchemy ORM
        mix_design = session.query(MixDesign).filter(MixDesign.id == mix_id).first()
        if mix_design:
            # Try to access the new attributes
            fine_template = getattr(mix_design, 'fine_aggregate_grading_template', 'MISSING')
            coarse_template = getattr(mix_design, 'coarse_aggregate_grading_template', 'MISSING')
            
            if fine_template != 'MISSING' and coarse_template != 'MISSING':
                print("   ✅ SQLAlchemy ORM can access grading template attributes")
                print(f"     - fine_aggregate_grading_template: {fine_template}")
                print(f"     - coarse_aggregate_grading_template: {coarse_template}")
            else:
                print("   ❌ SQLAlchemy ORM cannot access grading template attributes")
                return False
        else:
            print("   ❌ Failed to query mix design via ORM")
            return False
        
        print()
        print("🎉 All grading template persistence tests PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        session.close()

if __name__ == "__main__":
    try:
        success = test_grading_template_persistence()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Test script failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
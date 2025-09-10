#!/usr/bin/env python3
"""
Database Migration: Add Grading Template Persistence

Adds grading template fields to mix_design table to persist template associations.
"""

import sys
import os
import shutil
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

def create_backup(db_path):
    """Create backup of database before making changes."""
    backup_path = f"{db_path}.backup_grading_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(db_path, backup_path)
    print(f"✅ Database backup created: {backup_path}")
    return backup_path

def add_grading_template_fields():
    """Add grading template fields to mix_design table."""
    
    print("🔧 Database Migration: Add Grading Template Persistence")
    print("=" * 65)
    
    db_path = 'src/data/database/vcctl.db'
    
    # Create database backup
    backup_path = create_backup(db_path)
    
    # Connect to database
    engine = create_engine(f'sqlite:///{db_path}')
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        print("📊 Checking current table structure...")
        
        # Check if columns already exist
        result = session.execute(text("PRAGMA table_info(mix_design)"))
        columns = {row[1]: row[2] for row in result}
        
        existing_grading_fields = []
        if 'fine_aggregate_grading_template' in columns:
            existing_grading_fields.append('fine_aggregate_grading_template')
        if 'coarse_aggregate_grading_template' in columns:
            existing_grading_fields.append('coarse_aggregate_grading_template')
        
        if existing_grading_fields:
            print(f"⚠️  Grading template fields already exist: {existing_grading_fields}")
            print("   No migration needed.")
            return True
        
        print("➕ Adding grading template fields...")
        
        # Add fine aggregate grading template field
        session.execute(text('''
            ALTER TABLE mix_design 
            ADD COLUMN fine_aggregate_grading_template VARCHAR(64) DEFAULT NULL
        '''))
        
        print("   ✅ Added fine_aggregate_grading_template field")
        
        # Add coarse aggregate grading template field
        session.execute(text('''
            ALTER TABLE mix_design 
            ADD COLUMN coarse_aggregate_grading_template VARCHAR(64) DEFAULT NULL
        '''))
        
        print("   ✅ Added coarse_aggregate_grading_template field")
        
        # Commit the changes
        session.commit()
        
        print()
        print("✅ Migration completed successfully!")
        
        # Verify the changes
        print("🔍 Verifying new table structure...")
        result = session.execute(text("PRAGMA table_info(mix_design)"))
        grading_fields = []
        
        for row in result:
            column_name = row[1]
            if 'grading_template' in column_name:
                grading_fields.append(column_name)
        
        if len(grading_fields) == 2:
            print("   ✅ Both grading template fields added successfully")
            for field in grading_fields:
                print(f"     - {field}")
        else:
            print(f"   ⚠️  Expected 2 grading fields, found {len(grading_fields)}")
            return False
        
        # Test writing and reading a template association
        print()
        print("🧪 Testing template association...")
        
        # Find a mix design with fine aggregate for testing
        result = session.execute(text('''
            SELECT id, name 
            FROM mix_design 
            WHERE fine_aggregate_name IS NOT NULL 
            AND fine_aggregate_mass > 0
            LIMIT 1
        '''))
        
        test_mix = result.fetchone()
        if test_mix:
            mix_id, mix_name = test_mix
            
            # Set a test grading template
            session.execute(text('''
                UPDATE mix_design 
                SET fine_aggregate_grading_template = 'AFineGrading'
                WHERE id = :mix_id
            '''), {'mix_id': mix_id})
            
            session.commit()
            
            # Verify the assignment
            result = session.execute(text('''
                SELECT fine_aggregate_grading_template 
                FROM mix_design 
                WHERE id = :mix_id
            '''), {'mix_id': mix_id})
            
            template_name = result.scalar()
            if template_name == 'AFineGrading':
                print(f"   ✅ Test successful: {mix_name} → AFineGrading")
                
                # Clear the test value
                session.execute(text('''
                    UPDATE mix_design 
                    SET fine_aggregate_grading_template = NULL
                    WHERE id = :mix_id
                '''), {'mix_id': mix_id})
                session.commit()
                
                print(f"   ✅ Test cleanup completed")
            else:
                print(f"   ❌ Test failed: expected 'AFineGrading', got '{template_name}'")
                return False
        else:
            print("   ⚠️  No mix designs with fine aggregate found for testing")
        
        print()
        print("🎉 Grading template persistence migration completed successfully!")
        print(f"   Database backup: {backup_path}")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        session.rollback()
        
        print("   Attempting to restore from backup...")
        try:
            session.close()
            shutil.copy2(backup_path, db_path)
            print(f"   ✅ Database restored from backup: {backup_path}")
        except Exception as restore_error:
            print(f"   ❌ Failed to restore backup: {restore_error}")
        
        return False
        
    finally:
        session.close()

def verify_migration():
    """Verify the migration was successful."""
    
    print()
    print("🔍 Final verification...")
    
    db_path = 'src/data/database/vcctl.db'
    engine = create_engine(f'sqlite:///{db_path}')
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Check table structure
        result = session.execute(text("PRAGMA table_info(mix_design)"))
        columns = [row[1] for row in result]
        
        required_fields = ['fine_aggregate_grading_template', 'coarse_aggregate_grading_template']
        found_fields = [field for field in required_fields if field in columns]
        
        if len(found_fields) == len(required_fields):
            print("   ✅ All grading template fields present in database")
            
            # Count mix designs that could benefit from template associations
            result = session.execute(text('''
                SELECT COUNT(*) 
                FROM mix_design 
                WHERE (fine_aggregate_name IS NOT NULL AND fine_aggregate_mass > 0)
                   OR (coarse_aggregate_name IS NOT NULL AND coarse_aggregate_mass > 0)
            '''))
            
            aggregate_mixes = result.scalar()
            print(f"   📊 {aggregate_mixes} mix designs can now store grading template associations")
            
            return True
        else:
            print(f"   ❌ Missing grading template fields: {set(required_fields) - set(found_fields)}")
            return False
            
    except Exception as e:
        print(f"   ❌ Verification failed: {e}")
        return False
        
    finally:
        session.close()

if __name__ == "__main__":
    try:
        # Run the migration
        success = add_grading_template_fields()
        
        if success:
            # Verify the migration
            verify_success = verify_migration()
            sys.exit(0 if verify_success else 1)
        else:
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Script failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
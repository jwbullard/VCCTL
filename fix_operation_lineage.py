#!/usr/bin/env python3
"""
Fix Operation Lineage Tracking

Identifies and fixes missing parent_operation_id linkages for hydration operations
that should be linked to their source microstructure operations.
"""

import sys
import os
import json
import shutil
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

def create_backup(db_path):
    """Create backup of database before making changes."""
    backup_path = f"{db_path}.backup_lineage_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(db_path, backup_path)
    print(f"✅ Database backup created: {backup_path}")
    return backup_path

def analyze_lineage_issues():
    """Analyze lineage tracking issues in the operations table."""
    
    print("🔍 Operation Lineage Analysis")
    print("=" * 50)
    
    db_path = 'data/database/vcctl.db'
    
    # Create database backup
    backup_path = create_backup(db_path)
    
    # Connect to database
    engine = create_engine(f'sqlite:///{db_path}')
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Find all orphan hydration operations
        result = session.execute(text('''
            SELECT id, name, operation_type, parent_operation_id, stored_ui_parameters, created_at
            FROM operations 
            WHERE operation_type = 'HYDRATION' AND parent_operation_id IS NULL
            ORDER BY created_at DESC
        '''))
        
        orphan_hydrations = result.fetchall()
        
        print(f"📊 Found {len(orphan_hydrations)} orphan hydration operations:")
        print()
        
        fixes = []
        
        for row in orphan_hydrations:
            hydration_id, hydration_name, op_type, parent_id, ui_params_json, created = row
            
            print(f"🔧 Analyzing: {hydration_name} (ID: {hydration_id})")
            print(f"   Created: {created}")
            
            # Try to extract source microstructure from stored UI parameters
            source_microstructure_name = None
            if ui_params_json:
                try:
                    ui_params = json.loads(ui_params_json)
                    source_info = ui_params.get('source_microstructure', {})
                    if isinstance(source_info, dict):
                        source_microstructure_name = source_info.get('name')
                    elif isinstance(source_info, str):
                        source_microstructure_name = source_info
                    print(f"   Source microstructure from UI params: {source_microstructure_name}")
                except Exception as e:
                    print(f"   ⚠️  Could not parse UI parameters: {e}")
            
            # Find potential parent microstructure operations
            if source_microstructure_name:
                result2 = session.execute(text('''
                    SELECT id, name, created_at
                    FROM operations 
                    WHERE operation_type = 'microstructure_generation' 
                      AND name = :source_name
                      AND created_at < :hydration_created
                    ORDER BY created_at DESC
                    LIMIT 1
                '''), {
                    'source_name': source_microstructure_name,
                    'hydration_created': created
                })
                
                potential_parent = result2.fetchone()
                if potential_parent:
                    parent_id, parent_name, parent_created = potential_parent
                    print(f"   ✅ Found parent: {parent_name} (ID: {parent_id}) created {parent_created}")
                    
                    fixes.append({
                        'hydration_id': hydration_id,
                        'hydration_name': hydration_name, 
                        'parent_id': parent_id,
                        'parent_name': parent_name
                    })
                else:
                    print(f"   ❌ No matching microstructure operation found for '{source_microstructure_name}'")
            else:
                print(f"   ❌ Could not determine source microstructure name")
            
            print()
        
        # Show summary
        print("📋 Lineage Fix Summary:")
        print(f"   Orphan hydrations found: {len(orphan_hydrations)}")
        print(f"   Fixable linkages: {len(fixes)}")
        print()
        
        if fixes:
            print("🔧 Proposed Fixes:")
            for fix in fixes:
                print(f"   {fix['hydration_name']} → {fix['parent_name']}")
            
            # Apply fixes
            print("\n⚠️  Applying lineage fixes...")
            
            for fix in fixes:
                session.execute(text('''
                    UPDATE operations 
                    SET parent_operation_id = :parent_id,
                        updated_at = datetime('now')
                    WHERE id = :hydration_id
                '''), {
                    'parent_id': fix['parent_id'],
                    'hydration_id': fix['hydration_id']
                })
                
                print(f"   ✅ Fixed: {fix['hydration_name']} linked to {fix['parent_name']}")
            
            session.commit()
            print("\n🎉 All lineage fixes applied successfully!")
        else:
            print("   No automatic fixes possible with current data")
        
        # Verify fixes
        print("\n🔍 Verification - Remaining Orphan Hydrations:")
        result = session.execute(text('''
            SELECT COUNT(*) FROM operations 
            WHERE operation_type = 'HYDRATION' AND parent_operation_id IS NULL
        '''))
        
        remaining_orphans = result.scalar()
        
        if remaining_orphans == 0:
            print("   ✅ All hydration operations now have proper parent linkage!")
            return True
        else:
            print(f"   ⚠️  {remaining_orphans} hydration operations still orphaned")
            
            # Show remaining orphans
            result = session.execute(text('''
                SELECT name FROM operations 
                WHERE operation_type = 'HYDRATION' AND parent_operation_id IS NULL
            '''))
            
            for row in result.fetchall():
                print(f"     - {row[0]}")
            
            return False
        
    except Exception as e:
        print(f"❌ Lineage analysis failed: {e}")
        session.rollback()
        return False
        
    finally:
        session.close()

if __name__ == "__main__":
    try:
        success = analyze_lineage_issues()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Script failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
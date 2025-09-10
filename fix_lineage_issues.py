#!/usr/bin/env python3
"""
Fix Operation Lineage Issues

Identifies and fixes missing parent_operation_id linkages for hydration operations.
"""

import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

def fix_lineage_issues():
    """Fix lineage tracking issues."""
    
    print("🔍 Fixing Operation Lineage Issues")
    print("=" * 50)
    
    engine = create_engine('sqlite:///data/database/vcctl.db')
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Find orphan hydration operations
        result = session.execute(text('''
            SELECT id, name, stored_ui_parameters, created_at
            FROM operations 
            WHERE operation_type = 'HYDRATION' AND parent_operation_id IS NULL
            ORDER BY created_at DESC
        '''))
        
        orphans = result.fetchall()
        print(f"📊 Found {len(orphans)} orphan hydration operations")
        
        fixes = []
        
        for hydration_id, hydration_name, ui_params_json, created in orphans:
            print(f"\n🔧 Analyzing: {hydration_name} (ID: {hydration_id})")
            
            # Extract source microstructure from UI parameters
            source_name = None
            if ui_params_json:
                try:
                    ui_params = json.loads(ui_params_json)
                    source_info = ui_params.get('source_microstructure', {})
                    if isinstance(source_info, dict):
                        source_name = source_info.get('name')
                    print(f"   Source from UI params: {source_name}")
                except:
                    print("   Could not parse UI parameters")
            
            # Find matching microstructure operation
            if source_name:
                result2 = session.execute(text('''
                    SELECT id, name, created_at
                    FROM operations 
                    WHERE operation_type = 'microstructure_generation' 
                      AND name = :source_name
                      AND created_at < :hydration_created
                    ORDER BY created_at DESC
                    LIMIT 1
                '''), {'source_name': source_name, 'hydration_created': created})
                
                parent = result2.fetchone()
                if parent:
                    parent_id, parent_name, parent_created = parent
                    print(f"   ✅ Found parent: {parent_name} (ID: {parent_id})")
                    fixes.append({
                        'hydration_id': hydration_id,
                        'hydration_name': hydration_name,
                        'parent_id': parent_id,
                        'parent_name': parent_name
                    })
                else:
                    print(f"   ❌ No matching parent found for '{source_name}'")
        
        print(f"\n📋 Fixes to apply: {len(fixes)}")
        
        if fixes:
            for fix in fixes:
                print(f"   {fix['hydration_name']} → {fix['parent_name']}")
                
                # Apply the fix
                session.execute(text('''
                    UPDATE operations 
                    SET parent_operation_id = :parent_id,
                        updated_at = datetime('now')
                    WHERE id = :hydration_id
                '''), {
                    'parent_id': fix['parent_id'],
                    'hydration_id': fix['hydration_id']
                })
            
            session.commit()
            print("\n✅ All lineage fixes applied!")
            
            # Verify
            result = session.execute(text('''
                SELECT COUNT(*) FROM operations 
                WHERE operation_type = 'HYDRATION' AND parent_operation_id IS NULL
            '''))
            
            remaining = result.scalar()
            print(f"📊 Remaining orphan hydrations: {remaining}")
            
            return remaining == 0
        else:
            print("   No fixes needed")
            return True
            
    except Exception as e:
        print(f"❌ Fix failed: {e}")
        session.rollback()
        return False
        
    finally:
        session.close()

if __name__ == "__main__":
    success = fix_lineage_issues()
    sys.exit(0 if success else 1)
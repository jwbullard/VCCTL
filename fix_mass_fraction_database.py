#!/usr/bin/env python3
"""
Database Mass Fraction Normalization Fix

Safely fixes all mix designs with corrupted mass fractions (don't sum to 1.0).
Creates backup before making any changes.
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
from app.services.mass_fraction_converter import MassFractionConverter, Component, MaterialType

def create_backup(db_path):
    """Create backup of database before making changes."""
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(db_path, backup_path)
    print(f"✅ Database backup created: {backup_path}")
    return backup_path

def get_material_type(material_type_str):
    """Convert material type string to MaterialType enum."""
    type_mapping = {
        'cement': MaterialType.CEMENT,
        'fly_ash': MaterialType.FLY_ASH,
        'slag': MaterialType.SLAG,
        'filler': MaterialType.FILLER,
        'silica_fume': MaterialType.SILICA_FUME,
        'limestone': MaterialType.LIMESTONE,
        'water': MaterialType.WATER,
        'aggregate': MaterialType.AGGREGATE
    }
    return type_mapping.get(material_type_str, MaterialType.CEMENT)

def analyze_and_fix_mix_designs():
    """Analyze and fix all corrupted mix designs."""
    
    print("🔧 Database Mass Fraction Normalization Fix")
    print("=" * 60)
    
    db_path = 'src/data/database/vcctl.db'
    
    # Create database backup
    backup_path = create_backup(db_path)
    
    # Connect to database
    engine = create_engine(f'sqlite:///{db_path}')
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Initialize converter
    converter = MassFractionConverter()
    
    try:
        # Get all mix designs
        result = session.execute(text('''
            SELECT id, name, components, created_at
            FROM mix_design 
            ORDER BY created_at DESC
        '''))
        
        all_designs = result.fetchall()
        problems = []
        fixes = []
        
        print(f"📊 Analyzing {len(all_designs)} mix designs...")
        print()
        
        for row in all_designs:
            mix_id, name, components_json, created = row
            
            if not components_json:
                print(f"⚠️  Skipping {name} (ID: {mix_id}) - No components data")
                continue
            
            try:
                components_data = json.loads(components_json)
                total_mass = sum(comp.get('mass_fraction', 0) for comp in components_data)
                
                # Check if mass fractions are corrupted (tolerance for floating point)
                tolerance = 0.001
                if abs(total_mass - 1.0) > tolerance:
                    problems.append({
                        'id': mix_id,
                        'name': name, 
                        'total_mass': total_mass,
                        'components_data': components_data,
                        'created': created
                    })
                    print(f"❌ CORRUPTED: {name} (ID: {mix_id}) - Total mass: {total_mass:.6f}")
                else:
                    print(f"✅ OK: {name} (ID: {mix_id}) - Total mass: {total_mass:.6f}")
                    
            except Exception as e:
                print(f"⚠️  ERROR parsing {name} (ID: {mix_id}): {e}")
                continue
        
        print()
        print(f"📋 Analysis Results:")
        print(f"   Total mix designs: {len(all_designs)}")
        print(f"   Corrupted designs: {len(problems)}")
        print(f"   Healthy designs: {len(all_designs) - len(problems)}")
        print()
        
        if not problems:
            print("🎉 No corrupted mix designs found - database is healthy!")
            return True
        
        # Proceed with fixing (automated for script execution)
        print(f"⚠️  Found {len(problems)} corrupted mix designs that need fixing.")
        print(f"   Database backup created: {backup_path}")
        print("   Proceeding with automated fix...")
        print()
        
        print()
        print("🔧 Fixing corrupted mix designs...")
        print()
        
        # Fix each corrupted design
        for problem in problems:
            mix_id = problem['id']
            name = problem['name']
            components_data = problem['components_data']
            original_total = problem['total_mass']
            
            print(f"🔧 Fixing {name} (ID: {mix_id})...")
            
            try:
                # Convert to Component objects
                components = []
                for comp_data in components_data:
                    material_type = get_material_type(comp_data.get('material_type', 'cement'))
                    component = Component(
                        material_name=comp_data.get('material_name', 'Unknown'),
                        material_type=material_type,
                        mass_fraction=comp_data.get('mass_fraction', 0.0),
                        specific_gravity=comp_data.get('specific_gravity', 1.0)
                    )
                    components.append(component)
                
                # Normalize to Type 3
                normalized_components = converter.normalize_to_type3(components)
                
                if not normalized_components:
                    print(f"   ❌ Failed to normalize {name}")
                    continue
                
                # Validate normalization
                is_valid, error = converter.validate_mass_fractions(normalized_components, "Type 3")
                if not is_valid:
                    print(f"   ❌ Validation failed for {name}: {error}")
                    continue
                
                # Convert back to JSON format
                fixed_components_data = []
                for comp in normalized_components:
                    fixed_comp = {
                        'material_name': comp.material_name,
                        'material_type': comp.material_type.value,
                        'mass_fraction': comp.mass_fraction,
                        'volume_fraction': comp.mass_fraction / comp.specific_gravity,
                        'specific_gravity': comp.specific_gravity
                    }
                    fixed_components_data.append(fixed_comp)
                
                fixed_components_json = json.dumps(fixed_components_data)
                
                # Update database
                session.execute(text('''
                    UPDATE mix_design 
                    SET components = :components,
                        updated_at = datetime('now')
                    WHERE id = :mix_id
                '''), {
                    'components': fixed_components_json,
                    'mix_id': mix_id
                })
                
                # Verify the fix
                new_total = sum(comp.mass_fraction for comp in normalized_components)
                print(f"   ✅ Fixed: {original_total:.6f} → {new_total:.6f}")
                
                fixes.append({
                    'id': mix_id,
                    'name': name,
                    'original_total': original_total,
                    'fixed_total': new_total
                })
                
            except Exception as e:
                print(f"   ❌ Failed to fix {name}: {e}")
                continue
        
        # Commit all changes
        session.commit()
        
        print()
        print(f"🎉 Mass fraction normalization complete!")
        print(f"   Successfully fixed: {len(fixes)} mix designs")
        print(f"   Database backup: {backup_path}")
        print()
        
        # Summary of fixes
        if fixes:
            print("📋 Summary of fixes:")
            for fix in fixes:
                print(f"   {fix['name']}: {fix['original_total']:.6f} → {fix['fixed_total']:.6f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database fix failed: {e}")
        session.rollback()
        return False
        
    finally:
        session.close()

def verify_fixes():
    """Verify that all fixes were applied correctly."""
    
    print()
    print("🔍 Verifying fixes...")
    
    db_path = 'src/data/database/vcctl.db'
    engine = create_engine(f'sqlite:///{db_path}')
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        result = session.execute(text('''
            SELECT id, name, components
            FROM mix_design 
            ORDER BY updated_at DESC
        '''))
        
        all_designs = result.fetchall()
        corrupted_count = 0
        
        for row in all_designs:
            mix_id, name, components_json = row
            
            if not components_json:
                continue
            
            try:
                components_data = json.loads(components_json)
                total_mass = sum(comp.get('mass_fraction', 0) for comp in components_data)
                
                if abs(total_mass - 1.0) > 0.001:
                    print(f"   ❌ Still corrupted: {name} (ID: {mix_id}) - Total: {total_mass:.6f}")
                    corrupted_count += 1
                    
            except Exception as e:
                print(f"   ⚠️  Error verifying {name}: {e}")
        
        if corrupted_count == 0:
            print("   ✅ All mix designs now have properly normalized mass fractions!")
        else:
            print(f"   ⚠️  {corrupted_count} mix designs still have issues")
            
        return corrupted_count == 0
        
    finally:
        session.close()

if __name__ == "__main__":
    try:
        # Fix the database
        success = analyze_and_fix_mix_designs()
        
        if success:
            # Verify the fixes
            verify_success = verify_fixes()
            sys.exit(0 if verify_success else 1)
        else:
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Script failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
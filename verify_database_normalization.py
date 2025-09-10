#!/usr/bin/env python3
"""
Verify Database Mass Fraction Normalization

Quick check to verify that previously corrupted mix designs
now have properly normalized mass fractions.
"""

import sys
import os
import json

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

def verify_normalized_mix_designs():
    """Verify that database mix designs have normalized mass fractions."""
    
    print("🔍 Verifying Database Mass Fraction Normalization")
    print("=" * 60)
    
    db_path = 'src/data/database/vcctl.db'
    engine = create_engine(f'sqlite:///{db_path}')
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Get mix designs that were previously problematic
        test_designs = ['TestConc-01', 'TestMortar-01', 'BigElephantInTheRoom']
        
        for design_name in test_designs:
            print(f"\n📊 Checking {design_name}...")
            
            result = session.execute(text('''
                SELECT id, name, components, updated_at
                FROM mix_design 
                WHERE name = :name
                LIMIT 1
            '''), {'name': design_name})
            
            row = result.fetchone()
            if not row:
                print(f"   ⚠️  Mix design '{design_name}' not found in database")
                continue
                
            mix_id, name, components_json, updated = row
            
            if not components_json:
                print(f"   ⚠️  No components data for {name}")
                continue
            
            try:
                components_data = json.loads(components_json)
                mass_fractions = [comp.get('mass_fraction', 0.0) for comp in components_data]
                total_mass_fraction = sum(mass_fractions)
                
                print(f"   Components: {len(components_data)}")
                print(f"   Mass fractions: {[f'{mf:.6f}' for mf in mass_fractions]}")
                print(f"   Total: {total_mass_fraction:.6f}")
                print(f"   Last updated: {updated}")
                
                tolerance = 0.001
                if abs(total_mass_fraction - 1.0) < tolerance:
                    print(f"   ✅ NORMALIZED: {name} mass fractions sum correctly to 1.0")
                else:
                    print(f"   ❌ STILL CORRUPTED: {name} sums to {total_mass_fraction:.6f}")
                    
            except Exception as e:
                print(f"   ❌ Error parsing components for {name}: {e}")
        
        # Check overall database health
        print(f"\n🏥 Overall Database Health Check...")
        
        result = session.execute(text('''
            SELECT COUNT(*) FROM mix_design WHERE components IS NOT NULL
        '''))
        total_designs = result.scalar()
        
        # Count designs with corrupted mass fractions  
        result = session.execute(text('''
            SELECT id, name, components
            FROM mix_design 
            WHERE components IS NOT NULL
        '''))
        
        all_designs = result.fetchall()
        corrupted_count = 0
        
        for row in all_designs:
            mix_id, name, components_json = row
            try:
                components_data = json.loads(components_json)
                total_mass = sum(comp.get('mass_fraction', 0) for comp in components_data)
                if abs(total_mass - 1.0) > 0.001:
                    corrupted_count += 1
            except:
                corrupted_count += 1
        
        healthy_count = total_designs - corrupted_count
        health_percentage = (healthy_count / total_designs * 100) if total_designs > 0 else 0
        
        print(f"   Total mix designs: {total_designs}")
        print(f"   Healthy designs: {healthy_count}")
        print(f"   Corrupted designs: {corrupted_count}")
        print(f"   Health percentage: {health_percentage:.1f}%")
        
        if corrupted_count == 0:
            print("   ✅ DATABASE FULLY NORMALIZED: All mix designs have proper mass fractions!")
            return True
        else:
            print(f"   ⚠️  {corrupted_count} designs still need normalization")
            return False
        
    finally:
        session.close()

if __name__ == "__main__":
    try:
        success = verify_normalized_mix_designs()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
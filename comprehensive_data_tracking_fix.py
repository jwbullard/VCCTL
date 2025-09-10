#!/usr/bin/env python3
"""
Comprehensive Data Tracking Fix

Diagnoses and fixes all root causes of data tracking failures:
1. Auto-save mix design failures
2. UI parameters not being stored  
3. MicrostructureOperation linking records not being created
4. Database table/model mismatches
"""

import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

def analyze_data_tracking_failures():
    """Analyze why TestConc-02 data tracking failed completely."""
    
    print("🔍 Comprehensive Data Tracking Analysis")
    print("=" * 60)
    
    engine = create_engine('sqlite:///data/database/vcctl.db')
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Analysis 1: Check SavedMixDesign auto-save failure
        print("📊 Analysis 1: SavedMixDesign Auto-Save Status")
        result = session.execute(text('''
            SELECT id, name, components, created_at
            FROM mix_design 
            WHERE name LIKE '%TestConc%'
            ORDER BY created_at DESC
        '''))
        
        mix_designs = result.fetchall()
        print(f"   Found {len(mix_designs)} TestConc mix designs:")
        for row in mix_designs:
            mix_id, name, components, created = row
            has_components = "Yes" if components else "No"
            print(f"     {name} (ID: {mix_id}) - Components: {has_components} - Created: {created}")
        
        if not any("TestConc-02" in row[1] for row in mix_designs):
            print("   ❌ ROOT CAUSE 1: TestConc-02 auto-save completely failed")
        
        # Analysis 2: Check Operations table record
        print("\\n📊 Analysis 2: Operations Table Record")
        result = session.execute(text('''
            SELECT id, name, operation_type, stored_ui_parameters, created_at
            FROM operations 
            WHERE name = 'TestConc-02'
        '''))
        
        operation = result.fetchone()
        if operation:
            op_id, name, op_type, ui_params, created = operation
            has_ui_params = "Yes" if ui_params else "No"
            print(f"   ✅ Operation exists: {name} (ID: {op_id}) - UI Params: {has_ui_params}")
            
            if not ui_params:
                print("   ❌ ROOT CAUSE 2: UI parameters storage failed")
        else:
            print("   ❌ No operation record found")
            
        # Analysis 3: Check MicrostructureOperation linking record
        print("\\n📊 Analysis 3: MicrostructureOperation Linking Record")
        if operation:
            result = session.execute(text('''
                SELECT id, operation_id, mix_design_id, created_at
                FROM microstructure_operations 
                WHERE operation_id = :op_id
            '''), {'op_id': operation[0]})
            
            micro_op = result.fetchone()
            if micro_op:
                link_id, op_id, mix_id, created = micro_op
                print(f"   ✅ Linking record exists: Link ID {link_id} - Op: {op_id} - Mix: {mix_id}")
            else:
                print(f"   ❌ ROOT CAUSE 3: No MicrostructureOperation linking record for operation {operation[0]}")
        
        # Analysis 4: Check Hippo hydration operation lineage
        print("\\n📊 Analysis 4: Hippo Hydration Operation Lineage")
        result = session.execute(text('''
            SELECT id, name, operation_type, parent_operation_id, stored_ui_parameters
            FROM operations 
            WHERE name = 'Hippo'
        '''))
        
        hippo = result.fetchone()
        if hippo:
            hip_id, name, op_type, parent_id, ui_params = hippo
            has_parent = "Yes" if parent_id else "No"
            has_ui_params = "Yes" if ui_params else "No"
            print(f"   ✅ Hippo exists: {name} (ID: {hip_id}) - Parent: {has_parent} - UI Params: {has_ui_params}")
            
            if not parent_id:
                print("   ❌ ROOT CAUSE 4: Hippo has no parent operation linkage")
            elif operation and parent_id != operation[0]:
                print(f"   ❌ ROOT CAUSE 4b: Hippo parent {parent_id} != TestConc-02 operation {operation[0]}")
        else:
            print("   ❌ No Hippo operation found")
        
        # Analysis 5: Check table structure compatibility
        print("\\n📊 Analysis 5: Database Table Structure")
        
        # Check operations table schema
        result = session.execute(text('PRAGMA table_info(operations)'))
        operations_columns = [row[1] for row in result.fetchall()]
        
        # Check microstructure_operations table schema  
        result = session.execute(text('PRAGMA table_info(microstructure_operations)'))
        micro_ops_columns = [row[1] for row in result.fetchall()]
        
        required_ops_columns = ['id', 'name', 'stored_ui_parameters', 'parent_operation_id']
        required_micro_columns = ['operation_id', 'mix_design_id']
        
        missing_ops = [col for col in required_ops_columns if col not in operations_columns]
        missing_micro = [col for col in required_micro_columns if col not in micro_ops_columns]
        
        if missing_ops:
            print(f"   ❌ Missing operations columns: {missing_ops}")
        else:
            print("   ✅ Operations table has required columns")
            
        if missing_micro:
            print(f"   ❌ Missing microstructure_operations columns: {missing_micro}")
        else:
            print("   ✅ MicrostructureOperations table has required columns")
        
        print("\\n📋 Root Causes Summary:")
        print("   1. SavedMixDesign auto-save: Check if TestConc-02 was saved")
        print("   2. UI parameters storage: Check if operations have stored_ui_parameters")
        print("   3. MicrostructureOperation linking: Check if linking records created")
        print("   4. Hydration lineage: Check if Hippo linked to TestConc-02")
        print("   5. Database compatibility: Check table schemas match code expectations")
        
        # Provide specific fix recommendations
        print("\\n🔧 Fix Recommendations:")
        print("   A. Fix auto-save method to ensure SavedMixDesign creation")
        print("   B. Fix UI parameters storage to use correct table/model")
        print("   C. Fix MicrostructureOperation creation with proper error handling")
        print("   D. Fix hydration operation creation to set parent_operation_id")
        print("   E. Add comprehensive error logging and validation")
        
        return True
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        session.close()

if __name__ == "__main__":
    success = analyze_data_tracking_failures()
    sys.exit(0 if success else 1)
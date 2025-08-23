#!/usr/bin/env python3
"""
Check current operations state before migration.
"""

import json
from pathlib import Path
from datetime import datetime


def check_json_operations():
    """Check operations in JSON file."""
    operations_file = Path.cwd() / "config" / "operations_history.json"
    
    print(f"📄 JSON Operations File: {operations_file}")
    
    if not operations_file.exists():
        print(f"   ❌ No JSON file found")
        return {}
    
    try:
        with open(operations_file, 'r') as f:
            data = json.load(f)
        
        operations_data = data.get('operations', {})
        deleted_names = data.get('deleted_operation_names', [])
        
        print(f"   ✅ Found {len(operations_data)} operations")
        print(f"   🗑️  Found {len(deleted_names)} deleted operation names")
        
        for op_id, op_data in list(operations_data.items())[:5]:  # Show first 5
            print(f"      • {op_data.get('name', 'Unknown')} ({op_data.get('status', 'Unknown')})")
        
        if len(operations_data) > 5:
            print(f"      ... and {len(operations_data) - 5} more")
        
        return operations_data
        
    except Exception as e:
        print(f"   ❌ Error reading JSON: {e}")
        return {}


def check_filesystem_operations():
    """Check operations in filesystem."""
    operations_dir = Path.cwd() / "Operations"
    
    print(f"\n📁 Operations Directory: {operations_dir}")
    
    if not operations_dir.exists():
        print(f"   ❌ No Operations directory found")
        return []
    
    try:
        folders = [d for d in operations_dir.iterdir() if d.is_dir()]
        print(f"   ✅ Found {len(folders)} operation folders")
        
        for folder in folders[:10]:  # Show first 10
            # Check folder contents
            files = list(folder.iterdir())
            has_img = any(f.name.endswith('.img') for f in files)
            has_csv = any(f.name.endswith('.csv') for f in files)
            has_prm = any('hydration_parameters.prm' in f.name for f in files)
            
            folder_type = "Unknown"
            if has_prm:
                folder_type = "Hydration"
            elif has_img:
                folder_type = "Microstructure"
            
            print(f"      • {folder.name} ({folder_type}, {len(files)} files)")
        
        if len(folders) > 10:
            print(f"      ... and {len(folders) - 10} more")
        
        return folders
        
    except Exception as e:
        print(f"   ❌ Error reading filesystem: {e}")
        return []


def check_database_operations():
    """Try to check database operations."""
    print(f"\n🗃️  Database Operations:")
    
    try:
        # Try a simple database check without full service container
        import sys
        sys.path.insert(0, 'src')
        
        from app.database.service import DatabaseService
        from app.models.operation import Operation as DBOperation
        
        db_service = DatabaseService()
        
        with db_service.get_session() as session:
            db_operations = session.query(DBOperation).all()
            print(f"   ✅ Found {len(db_operations)} database operations")
            
            for db_op in db_operations[:5]:  # Show first 5
                print(f"      • {db_op.name} ({db_op.type.value}, {db_op.status.value})")
            
            if len(db_operations) > 5:
                print(f"      ... and {len(db_operations) - 5} more")
        
        return db_operations
        
    except Exception as e:
        print(f"   ❌ Error checking database: {e}")
        return []


def main():
    """Check current state of operations data."""
    print(f"🔍 Checking Current Operations State")
    print(f"{'='*50}")
    
    json_ops = check_json_operations()
    filesystem_ops = check_filesystem_operations()
    database_ops = check_database_operations()
    
    print(f"\n📊 Summary:")
    print(f"   JSON operations: {len(json_ops)}")
    print(f"   Filesystem folders: {len(filesystem_ops)}")
    print(f"   Database operations: {len(database_ops)}")
    
    print(f"\n🎯 Migration Strategy:")
    if len(json_ops) > 0:
        print(f"   • Need to migrate {len(json_ops)} JSON operations to database")
    if len(filesystem_ops) > len(database_ops):
        print(f"   • May need to create database records for filesystem-only operations")
    if len(database_ops) > 0:
        print(f"   • {len(database_ops)} operations already in database")
    
    return True


if __name__ == "__main__":
    main()
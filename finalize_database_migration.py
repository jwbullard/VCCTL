#!/usr/bin/env python3
"""
Finalize Database Migration
Since most operations are already in the database, this script just:
1. Creates backup of JSON file
2. Verifies database has all important operations
3. Identifies any missing operations that need manual attention
"""

import sys
import json
import shutil
from pathlib import Path
from datetime import datetime

sys.path.insert(0, 'src')

def create_backup():
    """Create backup of JSON file."""
    operations_file = Path.cwd() / "config" / "operations_history.json"
    backup_file = Path.cwd() / "config" / f"operations_history_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    if operations_file.exists():
        shutil.copy2(operations_file, backup_file)
        print(f"✅ Created backup: {backup_file}")
        return backup_file
    else:
        print(f"ℹ️  No JSON file to backup")
        return None

def compare_operations():
    """Compare JSON vs Database operations."""
    # Load JSON operations
    operations_file = Path.cwd() / "config" / "operations_history.json"
    json_operations = {}
    
    if operations_file.exists():
        with open(operations_file, 'r') as f:
            data = json.load(f)
        json_operations = {op_data['name']: op_data for op_data in data.get('operations', {}).values()}
    
    # Load database operations
    try:
        from app.database.service import DatabaseService
        from app.models.operation import Operation as DBOperation
        
        db_service = DatabaseService()
        with db_service.get_session() as session:
            db_operations = session.query(DBOperation).all()
            db_names = {db_op.name for db_op in db_operations}
    except Exception as e:
        print(f"❌ Error accessing database: {e}")
        return False
    
    print(f"📊 Comparison Results:")
    print(f"   JSON operations: {len(json_operations)}")
    print(f"   Database operations: {len(db_operations)}")
    
    # Find operations only in JSON
    json_names = set(json_operations.keys())
    only_in_json = json_names - db_names
    only_in_db = db_names - json_names
    in_both = json_names & db_names
    
    print(f"\n🔄 Overlap Analysis:")
    print(f"   In both JSON and DB: {len(in_both)}")
    print(f"   Only in JSON: {len(only_in_json)}")
    print(f"   Only in DB: {len(only_in_db)}")
    
    if only_in_json:
        print(f"\n⚠️  Operations only in JSON (may be lost):")
        for name in only_in_json:
            op = json_operations[name]
            print(f"      • {name} ({op.get('status', 'unknown')})")
    
    if only_in_db:
        print(f"\n✅ Operations only in DB (newer):")
        for name in sorted(only_in_db):
            print(f"      • {name}")
    
    # Check if any important operations would be lost
    important_missing = [name for name in only_in_json 
                        if json_operations[name].get('status') == 'completed']
    
    if important_missing:
        print(f"\n🚨 WARNING: {len(important_missing)} completed operations only in JSON!")
        print(f"   These would be lost if we remove JSON file:")
        for name in important_missing:
            print(f"      • {name}")
        return False
    else:
        print(f"\n✅ All important operations are in database")
        return True

def main():
    print(f"🔄 Finalizing Database Migration")
    print(f"{'='*50}")
    
    # Create backup
    backup_file = create_backup()
    
    # Compare data sources
    safe_to_migrate = compare_operations()
    
    if safe_to_migrate:
        print(f"\n🎉 Migration Assessment: SAFE TO PROCEED")
        print(f"✅ All important operations are in the database")
        print(f"✅ JSON file can be safely archived")
        print(f"✅ Operations panel can be simplified to database-only")
        
        print(f"\n🚀 Next Steps:")
        print(f"1. Test Operations panel to verify it works with current data")
        print(f"2. Simplify Operations panel code to remove JSON loading")
        print(f"3. Archive JSON file (backup created: {backup_file.name if backup_file else 'N/A'})")
    else:
        print(f"\n⚠️  Migration Assessment: NEEDS ATTENTION")
        print(f"❌ Some completed operations exist only in JSON")
        print(f"❌ Manual migration needed before simplifying code")
        
        print(f"\n🔧 Required Actions:")
        print(f"1. Manually migrate missing completed operations to database")
        print(f"2. Re-run this assessment")
        print(f"3. Then proceed with code simplification")
    
    return safe_to_migrate

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
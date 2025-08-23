#!/usr/bin/env python3
"""
Operations Migration Script
Migrate all operations from JSON file + filesystem to database-only storage.

This script:
1. Backs up existing JSON file
2. Loads operations from all current sources
3. Migrates them to database
4. Verifies migration success
5. Optionally removes old JSON file
"""

import sys
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Add src to path
sys.path.insert(0, 'src')

from app.services.service_container import get_service_container
from app.windows.panels.operations_monitoring_panel import Operation, OperationStatus, OperationType


class OperationsMigrator:
    """Handles migration of operations from JSON+filesystem to database."""
    
    def __init__(self):
        self.service_container = get_service_container()
        self.operation_service = self.service_container.operation_service
        self.operations_file = Path.cwd() / "config" / "operations_history.json"
        self.backup_file = Path.cwd() / "config" / f"operations_history_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.operations_dir = Path.cwd() / "Operations"
        
        print(f"📋 Operations Migration Tool")
        print(f"   JSON file: {self.operations_file}")
        print(f"   Backup will be: {self.backup_file}")
        print(f"   Operations folder: {self.operations_dir}")
    
    def create_backup(self) -> bool:
        """Create backup of existing JSON file."""
        try:
            if self.operations_file.exists():
                shutil.copy2(self.operations_file, self.backup_file)
                print(f"✅ Created backup: {self.backup_file}")
                return True
            else:
                print(f"ℹ️  No existing JSON file to backup")
                return True
        except Exception as e:
            print(f"❌ Failed to create backup: {e}")
            return False
    
    def load_json_operations(self) -> Dict[str, Operation]:
        """Load operations from JSON file."""
        operations = {}
        
        try:
            if not self.operations_file.exists():
                print(f"ℹ️  No JSON operations file found")
                return operations
            
            with open(self.operations_file, 'r') as f:
                data = json.load(f)
            
            operations_data = data.get('operations', {})
            print(f"📄 Found {len(operations_data)} operations in JSON file")
            
            for op_id, op_data in operations_data.items():
                try:
                    operation = Operation.from_dict(op_data)
                    operations[op_id] = operation
                    print(f"   ✅ Loaded: {operation.name} ({operation.status.value})")
                except Exception as e:
                    print(f"   ❌ Failed to load operation {op_id}: {e}")
            
            print(f"✅ Loaded {len(operations)} operations from JSON")
            return operations
            
        except Exception as e:
            print(f"❌ Error loading JSON operations: {e}")
            return {}
    
    def discover_filesystem_operations(self) -> Dict[str, Operation]:
        """Discover operations from filesystem that may not be in JSON."""
        operations = {}
        
        try:
            if not self.operations_dir.exists():
                print(f"ℹ️  No Operations directory found")
                return operations
            
            # Scan for operation folders
            operation_folders = [d for d in self.operations_dir.iterdir() if d.is_dir()]
            print(f"📁 Found {len(operation_folders)} folders in Operations directory")
            
            for folder in operation_folders:
                folder_name = folder.name
                
                # Try to determine operation type from files
                has_img_files = list(folder.glob("*.img"))
                has_pimg_files = list(folder.glob("*.pimg"))
                has_csv_files = list(folder.glob("*.csv"))
                has_prm_files = list(folder.glob("*_hydration_parameters.prm"))
                
                # Determine operation type
                if has_prm_files or "Hydration" in folder_name:
                    op_type = OperationType.HYDRATION
                elif has_img_files or has_pimg_files:
                    op_type = OperationType.MICROSTRUCTURE_GENERATION
                else:
                    op_type = OperationType.MICROSTRUCTURE_GENERATION  # Default
                
                # Determine status from completion
                if has_csv_files:
                    status = OperationStatus.COMPLETED
                elif any(f.name.startswith('proc_') and f.name.endswith('_stderr.txt') for f in folder.iterdir()):
                    # Has error files
                    status = OperationStatus.FAILED
                else:
                    status = OperationStatus.COMPLETED  # Assume completed if folder exists
                
                # Create filesystem-discovered operation
                operation_id = f"fs_{folder_name}"
                operation = Operation(
                    id=operation_id,
                    name=folder_name,
                    operation_type=op_type,
                    status=status,
                    progress=1.0 if status == OperationStatus.COMPLETED else 0.0,
                    start_time=datetime.fromtimestamp(folder.stat().st_ctime),
                    end_time=datetime.fromtimestamp(folder.stat().st_mtime) if status == OperationStatus.COMPLETED else None,
                    output_directory=str(folder),
                    metadata={"source": "filesystem", "discovered_during_migration": True}
                )
                
                operations[operation_id] = operation
                print(f"   📁 Discovered: {folder_name} ({op_type.value}, {status.value})")
            
            print(f"✅ Discovered {len(operations)} filesystem operations")
            return operations
            
        except Exception as e:
            print(f"❌ Error discovering filesystem operations: {e}")
            return {}
    
    def check_existing_database_operations(self) -> List:
        """Check what operations already exist in database."""
        try:
            with self.service_container.database_service.get_session() as session:
                from app.models.operation import Operation as DBOperation
                db_operations = session.query(DBOperation).all()
                print(f"🗃️  Found {len(db_operations)} existing operations in database:")
                for db_op in db_operations:
                    print(f"   📊 {db_op.name} ({db_op.type.value}, {db_op.status.value})")
                return db_operations
        except Exception as e:
            print(f"❌ Error checking database operations: {e}")
            return []
    
    def migrate_operation_to_database(self, operation: Operation) -> bool:
        """Migrate a single operation to database."""
        try:
            # Check if operation already exists in database
            existing = self.operation_service.get_by_name(operation.name)
            if existing:
                print(f"   ⏭️  Skipping {operation.name} - already in database")
                return True
            
            # Convert UI operation to database operation
            from app.models.operation import Operation as DBOperation, OperationStatus as DBStatus, OperationType as DBType
            
            # Map UI enums to DB enums
            db_status_map = {
                OperationStatus.PENDING: DBStatus.QUEUED,
                OperationStatus.RUNNING: DBStatus.RUNNING,
                OperationStatus.PAUSED: DBStatus.RUNNING,  # DB doesn't have PAUSED
                OperationStatus.COMPLETED: DBStatus.FINISHED,
                OperationStatus.FAILED: DBStatus.ERROR,
                OperationStatus.CANCELLED: DBStatus.ERROR
            }
            
            db_type_map = {
                OperationType.MICROSTRUCTURE_GENERATION: DBType.MICROSTRUCTURE,
                OperationType.HYDRATION_SIMULATION: DBType.HYDRATION,
                OperationType.ANALYSIS: DBType.MICROSTRUCTURE  # Default to microstructure
            }
            
            db_operation = DBOperation(
                name=operation.name,
                type=db_type_map.get(operation.operation_type, DBType.MICROSTRUCTURE),
                status=db_status_map.get(operation.status, DBStatus.FINISHED),
                queued_at=operation.start_time,
                started_at=operation.start_time,
                finished_at=operation.end_time,
                output_directory=operation.output_directory
            )
            
            # Save to database
            with self.service_container.database_service.get_session() as session:
                session.add(db_operation)
                session.commit()
                print(f"   ✅ Migrated: {operation.name}")
                return True
                
        except Exception as e:
            print(f"   ❌ Failed to migrate {operation.name}: {e}")
            return False
    
    def verify_migration(self, original_operations: Dict[str, Operation]) -> bool:
        """Verify that all operations were migrated successfully."""
        try:
            db_operations = self.check_existing_database_operations()
            db_names = {db_op.name for db_op in db_operations}
            original_names = {op.name for op in original_operations.values()}
            
            missing = original_names - db_names
            if missing:
                print(f"❌ Migration verification failed - missing operations: {missing}")
                return False
            
            print(f"✅ Migration verification passed - all {len(original_names)} operations in database")
            return True
            
        except Exception as e:
            print(f"❌ Verification error: {e}")
            return False
    
    def run_migration(self) -> bool:
        """Run the complete migration process."""
        print(f"\n🚀 Starting Operations Migration")
        print(f"{'='*50}")
        
        # Step 1: Create backup
        if not self.create_backup():
            return False
        
        # Step 2: Load existing data
        json_operations = self.load_json_operations()
        filesystem_operations = self.discover_filesystem_operations()
        
        # Combine all operations (JSON takes precedence over filesystem discoveries)
        all_operations = {}
        all_operations.update(filesystem_operations)  # Filesystem first
        all_operations.update(json_operations)        # JSON overrides filesystem
        
        print(f"\n📊 Migration Summary:")
        print(f"   JSON operations: {len(json_operations)}")
        print(f"   Filesystem operations: {len(filesystem_operations)}")
        print(f"   Total to migrate: {len(all_operations)}")
        
        if not all_operations:
            print(f"ℹ️  No operations to migrate")
            return True
        
        # Step 3: Check existing database state
        self.check_existing_database_operations()
        
        # Step 4: Migrate operations
        print(f"\n💾 Migrating operations to database...")
        success_count = 0
        for operation in all_operations.values():
            if self.migrate_operation_to_database(operation):
                success_count += 1
        
        print(f"\n📈 Migration Results:")
        print(f"   Successfully migrated: {success_count}/{len(all_operations)}")
        
        # Step 5: Verify migration
        if not self.verify_migration(all_operations):
            print(f"❌ Migration verification failed - check manually before removing JSON file")
            return False
        
        print(f"\n✅ Migration completed successfully!")
        print(f"   Backup created: {self.backup_file}")
        print(f"   All operations now in database")
        
        return True


def main():
    """Run the migration."""
    migrator = OperationsMigrator()
    success = migrator.run_migration()
    
    if success:
        print(f"\n🎉 Migration completed successfully!")
        print(f"Next steps:")
        print(f"1. Test the Operations panel to verify all operations appear")
        print(f"2. If everything works, the JSON file can be removed")
        print(f"3. Code cleanup can proceed to remove JSON loading logic")
    else:
        print(f"\n❌ Migration failed - check logs above")
        print(f"Your original data is safe in the backup file")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
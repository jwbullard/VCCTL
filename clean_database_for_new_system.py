#!/usr/bin/env python3
"""
Database Cleanup Script for New Operation System

This script will:
1. Delete all existing operations and related records
2. Reset auto-increment counters
3. Verify the database is ready for the new clean naming system
4. Preserve schema and migrations table
"""

import sqlite3
import logging
from pathlib import Path
from datetime import datetime

def setup_logging():
    """Setup logging for cleanup."""
    logger = logging.getLogger('DatabaseCleanup')
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
    logger.addHandler(handler)
    return logger

def backup_database(db_path):
    """Create a backup of the database before cleanup."""
    logger = logging.getLogger('DatabaseCleanup')
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = db_path.parent / f"vcctl_backup_{timestamp}.db"
    
    try:
        import shutil
        shutil.copy2(db_path, backup_path)
        logger.info(f"✓ Database backed up to: {backup_path}")
        return backup_path
    except Exception as e:
        logger.error(f"✗ Failed to create backup: {e}")
        return None

def analyze_current_state(conn):
    """Analyze current database state before cleanup."""
    logger = logging.getLogger('DatabaseCleanup')
    cursor = conn.cursor()
    
    logger.info("Analyzing current database state...")
    
    # Check operations
    cursor.execute("SELECT COUNT(*) FROM operations")
    op_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT name, operation_type FROM operations")
    operations = cursor.fetchall()
    
    # Check results
    cursor.execute("SELECT COUNT(*) FROM results")
    result_count = cursor.fetchone()[0]
    
    # Check hydration_operations
    cursor.execute("SELECT COUNT(*) FROM hydration_operations")
    hydration_count = cursor.fetchone()[0]
    
    # Check microstructure_operations
    cursor.execute("SELECT COUNT(*) FROM microstructure_operations")
    microstructure_count = cursor.fetchone()[0]
    
    logger.info(f"Current state:")
    logger.info(f"  - Operations: {op_count}")
    logger.info(f"  - Results: {result_count}")
    logger.info(f"  - Hydration operations: {hydration_count}")
    logger.info(f"  - Microstructure operations: {microstructure_count}")
    
    if operations:
        logger.info("Existing operations:")
        for name, op_type in operations:
            logger.info(f"  - {name} ({op_type})")
    
    return {
        'operations': op_count,
        'results': result_count,
        'hydration_operations': hydration_count,
        'microstructure_operations': microstructure_count
    }

def clean_database(conn):
    """Clean all operation-related data from database."""
    logger = logging.getLogger('DatabaseCleanup')
    cursor = conn.cursor()
    
    logger.info("Starting database cleanup...")
    
    try:
        # Disable foreign key constraints temporarily
        cursor.execute("PRAGMA foreign_keys = OFF")
        
        # Delete in reverse dependency order to avoid constraint issues
        
        # 1. Delete results (depends on operations)
        cursor.execute("DELETE FROM results")
        deleted_results = cursor.rowcount
        logger.info(f"✓ Deleted {deleted_results} result records")
        
        # 2. Delete hydration_operations (depends on operations)
        cursor.execute("DELETE FROM hydration_operations")
        deleted_hydration = cursor.rowcount
        logger.info(f"✓ Deleted {deleted_hydration} hydration operation records")
        
        # 3. Delete microstructure_operations (depends on operations)
        cursor.execute("DELETE FROM microstructure_operations")
        deleted_microstructure = cursor.rowcount
        logger.info(f"✓ Deleted {deleted_microstructure} microstructure operation records")
        
        # 4. Delete operations (main table)
        cursor.execute("DELETE FROM operations")
        deleted_operations = cursor.rowcount
        logger.info(f"✓ Deleted {deleted_operations} operation records")
        
        # Re-enable foreign key constraints
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Commit all deletions
        conn.commit()
        logger.info("✓ All deletions committed")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Cleanup failed: {e}")
        conn.rollback()
        return False

def reset_sequences(conn):
    """Reset auto-increment sequences for clean start."""
    logger = logging.getLogger('DatabaseCleanup')
    cursor = conn.cursor()
    
    logger.info("Resetting auto-increment sequences...")
    
    try:
        # Reset sequences for all operation-related tables
        tables_to_reset = [
            'operations',
            'results', 
            'hydration_operations',
            'microstructure_operations'
        ]
        
        for table in tables_to_reset:
            # SQLite uses sqlite_sequence to track auto-increment
            cursor.execute(f"DELETE FROM sqlite_sequence WHERE name = ?", (table,))
            logger.info(f"✓ Reset sequence for {table}")
        
        conn.commit()
        logger.info("✓ All sequences reset")
        return True
        
    except Exception as e:
        logger.error(f"✗ Sequence reset failed: {e}")
        return False

def verify_clean_state(conn):
    """Verify database is in clean state."""
    logger = logging.getLogger('DatabaseCleanup')
    cursor = conn.cursor()
    
    logger.info("Verifying clean database state...")
    
    # Check all tables are empty
    tables_to_check = [
        'operations',
        'results',
        'hydration_operations', 
        'microstructure_operations'
    ]
    
    all_clean = True
    
    for table in tables_to_check:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        
        if count == 0:
            logger.info(f"✓ {table}: clean (0 records)")
        else:
            logger.error(f"✗ {table}: not clean ({count} records remaining)")
            all_clean = False
    
    # Check that schema is intact
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    
    # Just check that our key operation tables are present
    key_tables = ['operations', 'results', 'hydration_operations', 'microstructure_operations']
    
    for table in key_tables:
        if table not in tables:
            logger.error(f"✗ Missing key table: {table}")
            all_clean = False
        else:
            logger.info(f"✓ Key table present: {table}")
    
    logger.info(f"✓ Database has {len(tables)} total tables")
    
    # Check that new Phase 1 fields exist
    cursor.execute("PRAGMA table_info(operations)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]
    
    phase1_fields = ['parent_operation_id', 'stored_ui_parameters']
    for field in phase1_fields:
        if field in column_names:
            logger.info(f"✓ Phase 1 field present: {field}")
        else:
            logger.error(f"✗ Phase 1 field missing: {field}")
            all_clean = False
    
    # Test insert capability
    try:
        from datetime import datetime
        now = datetime.now()
        cursor.execute("""
            INSERT INTO operations 
            (name, operation_type, status, queued_at, progress, created_at, updated_at, parent_operation_id, stored_ui_parameters)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ("test_clean_insert", "TEST", "QUEUED", now, 0.0, now, now, None, '{"test": true}'))
        
        cursor.execute("SELECT id FROM operations WHERE name = ?", ("test_clean_insert",))
        test_id = cursor.fetchone()[0]
        
        if test_id == 1:
            logger.info("✓ Auto-increment starting at 1")
        else:
            logger.warning(f"Auto-increment starting at {test_id} (expected 1)")
        
        # Clean up test record
        cursor.execute("DELETE FROM operations WHERE name = ?", ("test_clean_insert",))
        conn.commit()
        
        logger.info("✓ Insert/delete functionality working")
        
    except Exception as e:
        logger.error(f"✗ Insert test failed: {e}")
        all_clean = False
    
    return all_clean

def main():
    """Main cleanup function."""
    logger = setup_logging()
    
    logger.info("=" * 60)
    logger.info("Database Cleanup for New Operation System")
    logger.info("=" * 60)
    
    # Database path
    db_path = Path(__file__).parent / "src" / "data" / "database" / "vcctl.db"
    
    if not db_path.exists():
        logger.error(f"Database not found at: {db_path}")
        return False
    
    logger.info(f"Database location: {db_path}")
    
    # Step 1: Create backup
    logger.info("\n1. Creating database backup...")
    backup_path = backup_database(db_path)
    if not backup_path:
        logger.error("Cannot proceed without backup")
        return False
    
    # Step 2: Analyze current state
    logger.info("\n2. Analyzing current database state...")
    try:
        with sqlite3.connect(db_path) as conn:
            current_state = analyze_current_state(conn)
    except Exception as e:
        logger.error(f"Failed to analyze database: {e}")
        return False
    
    # Step 3: Clean database
    logger.info("\n3. Cleaning database...")
    try:
        with sqlite3.connect(db_path) as conn:
            if not clean_database(conn):
                logger.error("Database cleanup failed")
                return False
    except Exception as e:
        logger.error(f"Database cleanup error: {e}")
        return False
    
    # Step 4: Reset sequences
    logger.info("\n4. Resetting auto-increment sequences...")
    try:
        with sqlite3.connect(db_path) as conn:
            if not reset_sequences(conn):
                logger.error("Sequence reset failed")
                return False
    except Exception as e:
        logger.error(f"Sequence reset error: {e}")
        return False
    
    # Step 5: Verify clean state
    logger.info("\n5. Verifying clean database state...")
    try:
        with sqlite3.connect(db_path) as conn:
            if not verify_clean_state(conn):
                logger.error("Database verification failed")
                return False
    except Exception as e:
        logger.error(f"Database verification error: {e}")
        return False
    
    # Success!
    logger.info("\n" + "=" * 60)
    logger.info("🎉 DATABASE CLEANUP SUCCESSFUL!")
    logger.info("✓ All test operations deleted")
    logger.info("✓ Related records cleaned up")
    logger.info("✓ Auto-increment counters reset")
    logger.info("✓ Schema and Phase 1 enhancements preserved")
    logger.info("✓ Database ready for new operation system")
    logger.info(f"✓ Backup available at: {backup_path.name}")
    logger.info("=" * 60)
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
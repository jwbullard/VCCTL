#!/usr/bin/env python3
"""
Phase 1 Lineage Migration: Add parent_operation_id and stored_ui_parameters to operations table

This migration adds:
1. parent_operation_id - Foreign key for operation lineage tracking
2. stored_ui_parameters - JSON field for storing UI state when operation was launched
"""

import sqlite3
import logging
from pathlib import Path

def run_migration():
    """Run Phase 1 lineage migration."""
    logger = logging.getLogger('Phase1Migration')
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
    logger.addHandler(handler)
    
    # Database path
    db_path = Path(__file__).parent / "src" / "data" / "database" / "vcctl.db"
    
    if not db_path.exists():
        logger.error(f"Database not found at: {db_path}")
        return False
    
    logger.info(f"Starting Phase 1 migration on database: {db_path}")
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Check current schema
            logger.info("Checking current operations table schema...")
            cursor.execute("PRAGMA table_info(operations)")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            logger.info(f"Current columns: {column_names}")
            
            migrations_needed = []
            
            # Check if parent_operation_id exists
            if 'parent_operation_id' not in column_names:
                migrations_needed.append("parent_operation_id")
            else:
                logger.info("parent_operation_id already exists")
                
            # Check if stored_ui_parameters exists
            if 'stored_ui_parameters' not in column_names:
                migrations_needed.append("stored_ui_parameters")
            else:
                logger.info("stored_ui_parameters already exists")
            
            if not migrations_needed:
                logger.info("No migrations needed - all columns already exist")
                return True
            
            # Add missing columns
            for column in migrations_needed:
                if column == 'parent_operation_id':
                    logger.info("Adding parent_operation_id column...")
                    cursor.execute("""
                        ALTER TABLE operations 
                        ADD COLUMN parent_operation_id INTEGER 
                        REFERENCES operations(id)
                    """)
                    
                    # Create index for performance
                    cursor.execute("""
                        CREATE INDEX IF NOT EXISTS idx_operations_parent_id 
                        ON operations(parent_operation_id)
                    """)
                    
                elif column == 'stored_ui_parameters':
                    logger.info("Adding stored_ui_parameters column...")
                    cursor.execute("""
                        ALTER TABLE operations 
                        ADD COLUMN stored_ui_parameters TEXT
                    """)
            
            # Commit changes
            conn.commit()
            
            # Verify the migration
            logger.info("Verifying migration...")
            cursor.execute("PRAGMA table_info(operations)")
            new_columns = cursor.fetchall()
            new_column_names = [col[1] for col in new_columns]
            
            logger.info(f"Updated columns: {new_column_names}")
            
            # Check that our new columns exist
            success = True
            for column in ['parent_operation_id', 'stored_ui_parameters']:
                if column not in new_column_names:
                    logger.error(f"Migration failed: {column} not found after migration")
                    success = False
                else:
                    logger.info(f"✓ {column} successfully added")
            
            if success:
                logger.info("Phase 1 migration completed successfully!")
            else:
                logger.error("Phase 1 migration failed verification")
                
            return success
            
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False

def validate_migration():
    """Validate that the migration was successful."""
    logger = logging.getLogger('Phase1Validation')
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
    logger.addHandler(handler)
    
    db_path = Path(__file__).parent / "src" / "data" / "database" / "vcctl.db"
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            logger.info("Validating Phase 1 migration...")
            
            # Test 1: Check schema
            cursor.execute("PRAGMA table_info(operations)")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            required_columns = ['parent_operation_id', 'stored_ui_parameters']
            for column in required_columns:
                if column in column_names:
                    logger.info(f"✓ {column} exists in schema")
                else:
                    logger.error(f"✗ {column} missing from schema")
                    return False
            
            # Test 2: Check existing operations still work
            cursor.execute("SELECT COUNT(*) FROM operations")
            operation_count = cursor.fetchone()[0]
            logger.info(f"✓ Existing operations still accessible: {operation_count} operations")
            
            # Test 3: Test that new columns can handle NULL values
            cursor.execute("""
                SELECT id, parent_operation_id, stored_ui_parameters 
                FROM operations LIMIT 1
            """)
            result = cursor.fetchone()
            if result:
                op_id, parent_id, ui_params = result
                logger.info(f"✓ New columns accessible - Operation {op_id}: parent={parent_id}, ui_params={ui_params}")
                
                # Test updating with new fields
                cursor.execute("""
                    UPDATE operations 
                    SET stored_ui_parameters = ?
                    WHERE id = ?
                """, ('{"test": "validation"}', op_id))
                
                # Verify update
                cursor.execute("""
                    SELECT stored_ui_parameters 
                    FROM operations WHERE id = ?
                """, (op_id,))
                updated_result = cursor.fetchone()
                
                if updated_result and updated_result[0]:
                    logger.info(f"✓ Update test successful: {updated_result[0]}")
                    
                    # Reset to NULL
                    cursor.execute("""
                        UPDATE operations 
                        SET stored_ui_parameters = NULL
                        WHERE id = ?
                    """, (op_id,))
                    conn.commit()
                else:
                    logger.error("✗ Update test failed")
                    return False
            
            logger.info("✓ Phase 1 migration validation successful!")
            return True
            
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        return False

if __name__ == "__main__":
    # Run migration
    success = run_migration()
    
    if success:
        # Validate migration
        validate_migration()
    else:
        print("Migration failed, skipping validation")
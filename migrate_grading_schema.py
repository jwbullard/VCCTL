#!/usr/bin/env python3
"""
Grading Schema Migration Script

This script adds the new columns to the existing grading table to support
the enhanced grading data management system.

Usage: python migrate_grading_schema.py
"""

import logging
import sys
import sqlite3
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from app.database.service import DatabaseService


def setup_logging():
    """Setup logging for migration script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('grading_schema_migration.log')
        ]
    )


def migrate_grading_schema():
    """Add new columns to existing grading table."""
    logger = logging.getLogger(__name__)
    logger.info("Starting grading schema migration...")
    
    try:
        # Initialize database service
        db_service = DatabaseService()
        
        # Get the database file path from config
        db_path = db_service.config.db_path
        logger.info(f"Migrating database at: {db_path}")
        
        # Connect directly with sqlite3 for schema changes
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check current table schema
        cursor.execute("PRAGMA table_info(grading)")
        existing_columns = [row[1] for row in cursor.fetchall()]
        logger.info(f"Existing columns: {existing_columns}")
        
        # Define new columns to add
        new_columns = {
            'sieve_data': 'JSON',
            'description': 'TEXT',
            'aggregate_id': 'INTEGER',
            'is_standard': 'INTEGER DEFAULT 0',
            'created_at': 'DATETIME',
            'modified_at': 'DATETIME'
        }
        
        # Add missing columns
        for column_name, column_type in new_columns.items():
            if column_name not in existing_columns:
                try:
                    alter_sql = f"ALTER TABLE grading ADD COLUMN {column_name} {column_type}"
                    cursor.execute(alter_sql)
                    logger.info(f"✅ Added column: {column_name} ({column_type})")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" in str(e).lower():
                        logger.info(f"⚠️  Column {column_name} already exists")
                    else:
                        logger.error(f"Failed to add column {column_name}: {e}")
                        raise
            else:
                logger.info(f"✅ Column {column_name} already exists")
        
        # Commit changes
        conn.commit()
        
        # Verify final schema
        cursor.execute("PRAGMA table_info(grading)")
        final_columns = [row[1] for row in cursor.fetchall()]
        logger.info(f"Final columns: {final_columns}")
        
        conn.close()
        
        logger.info("✅ Schema migration completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Schema migration failed: {e}")
        return False


def verify_schema():
    """Verify the schema migration was successful."""
    logger = logging.getLogger(__name__)
    logger.info("Verifying schema migration...")
    
    try:
        # Test that we can query with new columns
        db_service = DatabaseService()
        
        with db_service.get_session() as session:
            # Try to access the enhanced grading model
            from app.models.grading import Grading
            
            # This should work now without column errors
            existing_gradings = session.query(Grading).all()
            logger.info(f"✅ Successfully queried {len(existing_gradings)} gradings with new schema")
            
            # Check if any gradings have the new fields
            for grading in existing_gradings:
                logger.info(f"  - {grading.name}: has_sieve_data={grading.sieve_data is not None}, "
                          f"is_standard={grading.is_standard}, created_at={grading.created_at}")
        
        return True
        
    except Exception as e:
        logger.error(f"Schema verification failed: {e}")
        return False


def main():
    """Main migration function."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("="*60)
    logger.info("VCCTL Grading Schema Migration")
    logger.info("="*60)
    
    # Run schema migration
    if not migrate_grading_schema():
        logger.error("Schema migration failed!")
        sys.exit(1)
    
    # Verify migration
    if not verify_schema():
        logger.error("Schema verification failed!")
        sys.exit(1)
    
    logger.info("="*60)
    logger.info("Schema migration completed successfully!")
    logger.info("You can now run: python migrate_grading_data.py")
    logger.info("="*60)


if __name__ == "__main__":
    main()
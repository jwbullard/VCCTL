#!/usr/bin/env python3
"""
Migration script to restructure grading table to use id as primary key
"""

import sqlite3
import os
import sys
from datetime import datetime

def migrate_grading_table():
    """Migrate grading table to use id as primary key instead of name."""

    # Database path
    db_path = "src/data/database/vcctl.db"
    backup_path = f"src/data/database/vcctl_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"

    if not os.path.exists(db_path):
        print(f"Database not found at: {db_path}")
        return

    print("Creating database backup...")
    # Create backup
    import shutil
    shutil.copy2(db_path, backup_path)
    print(f"✓ Backup created: {backup_path}")

    print("\nConnecting to database...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Begin transaction
        cursor.execute("BEGIN TRANSACTION;")

        print("\nStep 1: Checking current grading table structure...")
        cursor.execute("PRAGMA table_info(grading);")
        current_structure = cursor.fetchall()
        print("Current columns:")
        for col in current_structure:
            print(f"  {col[1]} {col[2]} {'PRIMARY KEY' if col[5] else ''}")

        print("\nStep 2: Creating new grading table with id as primary key...")
        # Create new table with proper structure
        cursor.execute("""
            CREATE TABLE grading_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(64) NOT NULL,
                type VARCHAR(6) NOT NULL,
                grading BLOB,
                max_diameter FLOAT,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                sieve_data JSON,
                description TEXT,
                aggregate_id INTEGER,
                is_standard INTEGER DEFAULT 0,
                modified_at DATETIME,
                UNIQUE(name, type)
            );
        """)

        print("\nStep 3: Checking for records with NULL or empty type values...")
        cursor.execute("SELECT COUNT(*) FROM grading WHERE type IS NULL OR type = '';")
        null_type_count = cursor.fetchone()[0]

        if null_type_count > 0:
            print(f"⚠️  Found {null_type_count} records with NULL/empty type values")
            cursor.execute("SELECT name, type FROM grading WHERE type IS NULL OR type = '';")
            null_records = cursor.fetchall()

            print("Records with NULL/empty type:")
            for record in null_records:
                print(f"  '{record[0]}' - type: '{record[1]}'")

            print("\nDeleting records with NULL/empty type values...")
            cursor.execute("DELETE FROM grading WHERE type IS NULL OR type = '';")
            print(f"✓ Deleted {null_type_count} invalid records")

        print("\nStep 4: Copying valid data from old table to new table...")
        cursor.execute("""
            INSERT INTO grading_new (
                name, type, grading, max_diameter, created_at, updated_at,
                sieve_data, description, aggregate_id, is_standard, modified_at
            )
            SELECT
                name, type, grading, max_diameter, created_at, updated_at,
                sieve_data, description, aggregate_id, is_standard, modified_at
            FROM grading
            WHERE type IS NOT NULL AND type != ''
            ORDER BY name;
        """)

        # Get count of migrated records
        cursor.execute("SELECT COUNT(*) FROM grading_new;")
        new_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM grading;")
        old_count = cursor.fetchone()[0]

        print(f"✓ Migrated {new_count} records (original: {old_count})")

        print("\nStep 4: Checking for foreign key references...")
        # Check if any tables reference grading by name
        # (This would need manual fixing if found)

        # Check common tables that might reference grading
        tables_to_check = ['mix_design', 'aggregate', 'operations']
        foreign_refs = []

        for table in tables_to_check:
            cursor.execute(f"PRAGMA table_info({table});")
            columns = cursor.fetchall()
            for col in columns:
                if 'grading' in col[1].lower():
                    foreign_refs.append(f"{table}.{col[1]}")

        if foreign_refs:
            print(f"⚠️  Found potential grading references: {foreign_refs}")
            print("   These may need manual updates after migration")
        else:
            print("✓ No obvious foreign key references found")

        print("\nStep 5: Replacing old table with new table...")
        # Drop old table and rename new one
        cursor.execute("DROP TABLE grading;")
        cursor.execute("ALTER TABLE grading_new RENAME TO grading;")

        print("\nStep 6: Creating indexes for performance...")
        cursor.execute("CREATE INDEX idx_grading_name_type ON grading(name, type);")
        cursor.execute("CREATE INDEX idx_grading_type ON grading(type);")

        print("\nStep 7: Verifying new table structure...")
        cursor.execute("PRAGMA table_info(grading);")
        new_structure = cursor.fetchall()
        print("New table structure:")
        for col in new_structure:
            pk_indicator = " (PRIMARY KEY)" if col[5] else ""
            print(f"  {col[1]} {col[2]}{pk_indicator}")

        # Verify we can query the new table
        cursor.execute("SELECT COUNT(*) FROM grading;")
        final_count = cursor.fetchone()[0]
        print(f"✓ Final record count: {final_count}")

        # Show sample of new IDs
        cursor.execute("SELECT id, name, type FROM grading ORDER BY id LIMIT 5;")
        samples = cursor.fetchall()
        if samples:
            print("\nSample records with new IDs:")
            for record in samples:
                print(f"  ID {record[0]}: {record[1]} ({record[2]})")

        # Commit transaction
        cursor.execute("COMMIT;")
        print("\n✓ Migration completed successfully!")

        print(f"\nSummary:")
        print(f"- Original records: {old_count}")
        print(f"- Migrated records: {final_count}")
        print(f"- Backup location: {backup_path}")
        print(f"- New primary key: id (INTEGER AUTOINCREMENT)")
        print(f"- Unique constraint: (name, type)")

    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        cursor.execute("ROLLBACK;")
        print("Changes rolled back")

        # Restore from backup
        print("Restoring from backup...")
        shutil.copy2(backup_path, db_path)
        print("✓ Database restored from backup")
        raise

    finally:
        conn.close()

if __name__ == "__main__":
    try:
        migrate_grading_table()
        print("\n🎉 Grading table migration completed successfully!")
        print("\nNext steps:")
        print("1. Test the application to ensure everything works")
        print("2. Update any code that references grading by name to use id")
        print("3. Remove backup file once you're confident the migration worked")

    except Exception as e:
        print(f"\n💥 Migration failed: {e}")
        print("The database has been restored from backup")
        sys.exit(1)
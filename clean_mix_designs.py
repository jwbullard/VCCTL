#!/usr/bin/env python3
"""
Script to delete all mix designs from the database for a fresh start
"""

import sqlite3
import os
import sys
from datetime import datetime

def clean_mix_designs():
    """Delete all mix designs from the database."""

    # Database path
    db_path = "src/data/database/vcctl.db"
    backup_path = f"src/data/database/vcctl_backup_mixdesign_cleanup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"

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

        print("\nStep 1: Checking current mix design count...")
        cursor.execute("SELECT COUNT(*) FROM mix_design;")
        total_count = cursor.fetchone()[0]
        print(f"Found {total_count} mix designs to delete")

        if total_count == 0:
            print("No mix designs to delete")
            return

        # Show some examples of what will be deleted
        cursor.execute("SELECT id, name FROM mix_design ORDER BY id LIMIT 10;")
        samples = cursor.fetchall()
        print("\nSample mix designs to be deleted:")
        for record in samples:
            print(f"  ID {record[0]}: {record[1]}")

        if total_count > 10:
            print(f"  ... and {total_count - 10} more")

        print("\nStep 2: Deleting all mix designs...")
        cursor.execute("DELETE FROM mix_design;")

        # Verify deletion
        cursor.execute("SELECT COUNT(*) FROM mix_design;")
        remaining_count = cursor.fetchone()[0]

        if remaining_count == 0:
            print(f"✓ Successfully deleted all {total_count} mix designs")
        else:
            print(f"⚠️  Warning: {remaining_count} mix designs remain")

        print("\nStep 3: Resetting auto-increment counter...")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name = 'mix_design';")
        print("✓ Auto-increment counter reset")

        # Commit transaction
        cursor.execute("COMMIT;")
        print("\n✓ Mix design cleanup completed successfully!")

        print(f"\nSummary:")
        print(f"- Deleted mix designs: {total_count}")
        print(f"- Remaining mix designs: {remaining_count}")
        print(f"- Backup location: {backup_path}")
        print(f"- Auto-increment reset: Yes")

    except Exception as e:
        print(f"\n✗ Cleanup failed: {e}")
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
        clean_mix_designs()
        print("\n🎉 Mix design cleanup completed successfully!")
        print("\nNext steps:")
        print("1. Test the application to ensure everything works")
        print("2. Create new mix designs with proper grading templates")
        print("3. Remove backup file once you're confident the cleanup worked")

    except Exception as e:
        print(f"\n💥 Cleanup failed: {e}")
        print("The database has been restored from backup")
        sys.exit(1)
#!/usr/bin/env python3
"""
Script to delete corrupted coarse grading templates from the database
"""

import sqlite3
import os

def delete_coarse_templates():
    """Delete corrupted coarse grading templates from the database."""

    # Database path
    db_path = "src/data/database/vcctl.db"

    if not os.path.exists(db_path):
        print(f"Database not found at: {db_path}")
        return

    print("Connecting to database...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("\nDeleting corrupted coarse grading templates...")

    # Templates to delete
    templates_to_delete = [
        ("ASTM #57 Stone", "COARSE"),
        ("ASTM #67 Stone", "COARSE"),
        ("standard_coarse_grading", "COARSE")
    ]

    deleted_count = 0
    for template_name, template_type in templates_to_delete:
        cursor.execute("SELECT name, type FROM grading WHERE name = ? AND type = ?",
                      (template_name, template_type))
        result = cursor.fetchone()

        if result:
            print(f"✓ Deleting: {template_name} ({template_type})")
            cursor.execute("DELETE FROM grading WHERE name = ? AND type = ?",
                         (template_name, template_type))
            deleted_count += 1
        else:
            print(f"✗ Not found: {template_name} ({template_type})")

    if deleted_count > 0:
        print(f"\nCommitting deletion of {deleted_count} templates...")
        conn.commit()
        print("✓ Database changes committed successfully")
    else:
        print("\nNo templates found to delete")

    conn.close()
    print(f"\nDeleted {deleted_count} coarse grading templates from database")

if __name__ == "__main__":
    delete_coarse_templates()
    print("\n✓ Coarse template cleanup completed successfully")
    print("\nYou can now create new coarse grading templates with:")
    print("- All 23 coarse aggregate sieve sizes")
    print("- Percent retained values (not cumulative passing)")
    print("- Proper data that will work with the elastic calculations")
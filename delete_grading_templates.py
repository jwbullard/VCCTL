#!/usr/bin/env python3
"""
Script to delete specific grading templates from the database
"""

import sqlite3
import os
import sys

def delete_grading_templates():
    """Delete specified grading templates from the database."""

    # Templates to delete: (name, type)
    templates_to_delete = [
        ("TestCoarseGdg", "COARSE"),
        ("Grading_15_points", "COARSE"),
        ("BokuNoHero", "COARSE"),
        ("AFineGrading", "FINE"),
        ("ASTM-C109", "FINE"),
        ("ASTM_C109", "FINE"),
        ("ASTMC109", "FINE"),
        ("ASTM_C33", "FINE"),
    ]

    # Database path
    db_path = "src/data/database/vcctl.db"

    if not os.path.exists(db_path):
        print(f"Database not found at: {db_path}")
        return

    print("Connecting to database...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("\nSearching for templates to delete...")

    deleted_count = 0
    for template_name, template_type in templates_to_delete:
        # Search for template by name and type
        cursor.execute("SELECT name, type FROM grading WHERE name = ? AND type = ?",
                      (template_name, template_type))
        result = cursor.fetchone()

        if result:
            name, type_val = result
            print(f"✓ Found and deleting: {name} ({type_val})")

            # Delete the template
            cursor.execute("DELETE FROM grading WHERE name = ? AND type = ?", (template_name, template_type))
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
    print(f"\nDeleted {deleted_count} grading templates from database")

if __name__ == "__main__":
    try:
        delete_grading_templates()
        print("\n✓ Template deletion completed successfully")
    except Exception as e:
        print(f"\n✗ Error deleting templates: {e}")
        sys.exit(1)
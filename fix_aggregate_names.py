#!/usr/bin/env python3
"""
Fix corrupted aggregate names in VCCTL database.

The aggregate table has corrupted 'name' fields containing massive hex strings
instead of readable names. This script fixes them by setting name = display_name.
"""

import sqlite3
import sys
from pathlib import Path

def fix_aggregate_names():
    """Fix corrupted aggregate names in the database."""
    db_path = Path("src/data/database/vcctl.db")
    
    if not db_path.exists():
        print(f"ERROR: Database not found at {db_path}")
        return False
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get current aggregate data
        print("Current aggregate data:")
        cursor.execute("SELECT display_name, LENGTH(name) as name_length FROM aggregate")
        aggregates = cursor.fetchall()
        
        for display_name, name_length in aggregates:
            print(f"  {display_name}: name field length = {name_length} characters")
        
        # Fix corrupted names by setting name = display_name
        print("\nFixing corrupted aggregate names...")
        cursor.execute("UPDATE aggregate SET name = display_name")
        rows_updated = cursor.rowcount
        
        # Verify the fix
        print(f"Updated {rows_updated} aggregate records")
        print("\nVerifying fixes:")
        cursor.execute("SELECT display_name, name FROM aggregate")
        fixed_aggregates = cursor.fetchall()
        
        for display_name, name in fixed_aggregates:
            status = "✓ FIXED" if name == display_name else "✗ STILL CORRUPTED"
            print(f"  {display_name} → {name} {status}")
        
        # Commit changes
        conn.commit()
        conn.close()
        
        print(f"\n✓ Successfully fixed {rows_updated} aggregate names")
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to fix aggregate names: {e}")
        return False

if __name__ == "__main__":
    print("=== VCCTL Aggregate Name Fix ===")
    success = fix_aggregate_names()
    sys.exit(0 if success else 1)
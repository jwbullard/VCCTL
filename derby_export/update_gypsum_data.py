#!/usr/bin/env python3
"""
Update gypsum mass fractions in the cement database from CSV file.

The CSV file contains:
- Column 1: cement name
- Column 2: dihydrate mass fraction (not percent)
- Column 3: hemihydrate mass fraction (not percent)  
- Column 4: anhydrite mass fraction (not percent)
"""

import csv
import sys
import os
from pathlib import Path

# Add the src directory to Python path to import VCCTL modules
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from app.database.service import DatabaseService
from app.services.cement_service import CementService
from app.models.cement import CementUpdate

def main():
    """Update gypsum mass fractions from CSV file."""
    
    # Initialize database and service
    db_service = DatabaseService()
    cement_service = CementService(db_service)
    
    # Read CSV file
    csv_file = Path(__file__).parent / "gypsumContents.csv"
    
    if not csv_file.exists():
        print(f"Error: CSV file not found: {csv_file}")
        return 1
    
    print(f"Reading gypsum data from: {csv_file}")
    
    updates_made = 0
    errors = 0
    
    with open(csv_file, 'r') as f:
        reader = csv.reader(f)
        
        for line_num, row in enumerate(reader, 1):
            # Skip empty lines
            if not row or not any(row):
                continue
                
            # Parse row
            if len(row) < 4:
                print(f"Warning: Line {line_num} has insufficient columns: {row}")
                continue
                
            cement_name = row[0].strip()
            
            # Skip empty cement names
            if not cement_name:
                continue
                
            try:
                dihyd_fraction = float(row[1]) if row[1].strip() else 0.0
                hemihyd_fraction = float(row[2]) if row[2].strip() else 0.0
                anhyd_fraction = float(row[3]) if row[3].strip() else 0.0
            except ValueError as e:
                print(f"Error: Line {line_num} has invalid number format: {e}")
                errors += 1
                continue
            
            # Validate fractions are reasonable
            if any(f < 0 or f > 1 for f in [dihyd_fraction, hemihyd_fraction, anhyd_fraction]):
                print(f"Error: Line {line_num} has invalid fractions (must be 0-1): {cement_name}")
                errors += 1
                continue
                
            total_gypsum = dihyd_fraction + hemihyd_fraction + anhyd_fraction
            if total_gypsum > 1.0:
                print(f"Error: Line {line_num} total gypsum fraction exceeds 1.0: {cement_name} (total: {total_gypsum})")
                errors += 1
                continue
            
            # Find cement in database
            try:
                cement = cement_service.get_by_name(cement_name)
                if not cement:
                    print(f"Warning: Cement '{cement_name}' not found in database (line {line_num})")
                    continue
                
                # Update gypsum fractions
                update_data = CementUpdate(
                    dihyd=dihyd_fraction,
                    hemihyd=hemihyd_fraction,
                    anhyd=anhyd_fraction
                )
                
                cement_service.update(cement.id, update_data)
                
                print(f"Updated {cement_name}: DIHYD={dihyd_fraction}, HEMIHYD={hemihyd_fraction}, ANHYD={anhyd_fraction}")
                updates_made += 1
                
            except Exception as e:
                print(f"Error updating cement '{cement_name}': {e}")
                errors += 1
    
    print(f"\nUpdate completed:")
    print(f"  Successfully updated: {updates_made} cements")
    print(f"  Errors encountered: {errors}")
    
    return 0 if errors == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
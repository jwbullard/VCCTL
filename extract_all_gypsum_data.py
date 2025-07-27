#!/usr/bin/env python3
"""
Extract gypsum fractions from all cements in Derby CSV and update SQLite database.
"""

import csv
import sqlite3
import sys
from pathlib import Path

def decode_hex_to_string(hex_string):
    """Decode hex string to readable text."""
    try:
        hex_clean = hex_string.strip()
        bytes_data = bytes.fromhex(hex_clean)
        return bytes_data.decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"Error decoding hex: {e}")
        return None

def parse_phase_data(decoded_text):
    """Parse decoded text to extract phase fractions."""
    lines = decoded_text.strip().split('\n')
    phase_data = []
    
    for line in lines:
        if line.strip():
            parts = line.split('\t')
            if len(parts) >= 2:
                try:
                    volume_frac = float(parts[0].strip())
                    mass_frac = float(parts[1].strip())
                    phase_data.append((volume_frac, mass_frac))
                except ValueError:
                    continue
    
    return phase_data

def extract_gypsum_fractions(phase_data):
    """Extract gypsum fractions from phase data."""
    gypsum_data = {
        'dihyd': 0.0,
        'hemihyd': 0.0,
        'anhyd': 0.0
    }
    
    # If we have more than 4 phases, assume additional phases are gypsum
    if len(phase_data) > 4:
        # Row 4 (index 4) = DIHYD (dihydrate)
        if len(phase_data) > 4:
            gypsum_data['dihyd'] = phase_data[4][1]  # Use mass fraction
        
        # Row 5 (index 5) = HEMIHYD (hemihydrate)
        if len(phase_data) > 5:
            gypsum_data['hemihyd'] = phase_data[5][1]  # Use mass fraction
        
        # Row 6 (index 6) = ANHYD (anhydrite) - if it exists
        if len(phase_data) > 6:
            gypsum_data['anhyd'] = phase_data[6][1]  # Use mass fraction
    
    return gypsum_data

def main():
    # Paths
    csv_path = Path("derby_export/cement.csv")
    db_path = Path("src/data/database/vcctl.db")
    
    if not csv_path.exists():
        print(f"CSV file not found: {csv_path}")
        sys.exit(1)
    
    if not db_path.exists():
        print(f"Database file not found: {db_path}")
        sys.exit(1)
    
    print(f"Reading Derby CSV file: {csv_path}")
    print(f"Updating SQLite database: {db_path}")
    
    # Connect to SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Increase CSV field size limit
    csv.field_size_limit(1000000)
    
    cement_updates = []
    
    # Read the CSV file
    with open(csv_path, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        
        row_count = 0
        
        for row in reader:
            row_count += 1
            
            if len(row) < 3:
                continue
            
            cement_name = row[0]
            hex_data = row[2]
            
            # Decode the hex data
            decoded_text = decode_hex_to_string(hex_data)
            if not decoded_text:
                continue
            
            # Parse phase data
            phase_data = parse_phase_data(decoded_text)
            if not phase_data:
                continue
            
            # Extract gypsum fractions
            gypsum_data = extract_gypsum_fractions(phase_data)
            
            print(f"\n{cement_name} ({len(phase_data)} phases):")
            print(f"  DIHYD: {gypsum_data['dihyd']:.6f}")
            print(f"  HEMIHYD: {gypsum_data['hemihyd']:.6f}")
            print(f"  ANHYD: {gypsum_data['anhyd']:.6f}")
            
            # Store for database update
            cement_updates.append((
                cement_name,
                gypsum_data['dihyd'],
                gypsum_data['hemihyd'],
                gypsum_data['anhyd']
            ))
    
    print(f"\nProcessed {row_count} rows, found {len(cement_updates)} cements")
    
    # Update database
    print("\nUpdating database...")
    updated_count = 0
    not_found_count = 0
    
    for cement_name, dihyd, hemihyd, anhyd in cement_updates:
        # Check if cement exists in database
        cursor.execute("SELECT name FROM cement WHERE name = ?", (cement_name,))
        if cursor.fetchone():
            # Update gypsum fractions
            cursor.execute("""
                UPDATE cement 
                SET dihyd = ?, hemihyd = ?, anhyd = ?
                WHERE name = ?
            """, (dihyd, hemihyd, anhyd, cement_name))
            updated_count += 1
            print(f"  Updated {cement_name}")
        else:
            not_found_count += 1
            print(f"  Cement not found in database: {cement_name}")
    
    # Commit changes
    conn.commit()
    
    print(f"\nDatabase update complete:")
    print(f"  Updated: {updated_count} cements")
    print(f"  Not found: {not_found_count} cements")
    
    # Verify updates
    print("\nVerifying updates...")
    cursor.execute("""
        SELECT name, dihyd, hemihyd, anhyd 
        FROM cement 
        WHERE dihyd > 0 OR hemihyd > 0 OR anhyd > 0
        ORDER BY name
    """)
    
    gypsum_cements = cursor.fetchall()
    print(f"Found {len(gypsum_cements)} cements with gypsum fractions:")
    for name, dihyd, hemihyd, anhyd in gypsum_cements:
        print(f"  {name}: DIHYD={dihyd:.6f}, HEMIHYD={hemihyd:.6f}, ANHYD={anhyd:.6f}")
    
    conn.close()
    print("\n✅ Gypsum data extraction complete!")

if __name__ == "__main__":
    main()
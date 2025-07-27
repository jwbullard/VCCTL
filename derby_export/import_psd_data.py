#!/usr/bin/env python3
"""
Import PSD data from Derby CSV export to SQLite database
"""

import csv
import binascii
import json
from pathlib import Path
import sys

# Add the src directory to Python path
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from app.database.config import DatabaseConfig
from app.database.service import DatabaseService
from app.services.cement_service import CementService

def decode_hex_psd_data(hex_data: str) -> list:
    """
    Decode hex-encoded PSD data into list of (diameter, mass_fraction) tuples.
    
    Args:
        hex_data: Hex-encoded string from CSV
        
    Returns:
        List of [diameter_um, mass_fraction] pairs
    """
    try:
        # Decode hex to ASCII
        decoded = binascii.unhexlify(hex_data).decode('utf-8')
        
        # Parse tab-separated values
        lines = decoded.strip().split('\n')
        psd_points = []
        
        for line in lines:
            if '\t' in line:
                parts = line.split('\t')
                if len(parts) >= 2:
                    try:
                        diameter = float(parts[0])
                        mass_fraction = float(parts[1])
                        psd_points.append([diameter, mass_fraction])
                    except ValueError:
                        continue
        
        return psd_points
        
    except Exception as e:
        print(f"Error decoding hex data: {e}")
        return []

def extract_psd_data_from_csv(csv_file: Path) -> dict:
    """
    Extract PSD data from Derby CSV export.
    
    Args:
        csv_file: Path to psd_data.csv file
        
    Returns:
        Dictionary mapping cement names to PSD data
    """
    psd_data = {}
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        
        for row in reader:
            if len(row) >= 4:
                name_field = row[0].strip('"')
                type_field = row[1].strip('"').strip()
                hex_data = row[2].strip('"')
                
                # Check if this is a PSD record
                if type_field == 'psd' and name_field.endswith(' psd'):
                    # Extract cement name (remove ' psd' suffix)
                    cement_name = name_field.replace(' psd', '')
                    
                    # Decode the PSD data
                    psd_points = decode_hex_psd_data(hex_data)
                    
                    if psd_points:
                        psd_data[cement_name] = psd_points
                        print(f"Extracted PSD data for {cement_name}: {len(psd_points)} points")
    
    return psd_data

def import_psd_to_database(psd_data: dict) -> None:
    """
    Import PSD data into SQLite database.
    
    Args:
        psd_data: Dictionary mapping cement names to PSD data
    """
    db_config = DatabaseConfig("vcctl.db")
    db_service = DatabaseService(db_config)
    cement_service = CementService(db_service)
    
    updated_count = 0
    not_found_count = 0
    
    for cement_name, psd_points in psd_data.items():
        # Find the cement in the database
        cement = cement_service.get_by_name(cement_name)
        
        if cement:
            try:
                # Convert PSD data to JSON string for storage
                psd_json = json.dumps(psd_points)
                
                # Update the cement with actual PSD data
                from app.models.cement import CementUpdate
                update_data = CementUpdate(
                    psd_custom_points=psd_json,
                    psd_mode='custom'  # Set mode to custom since we have actual curve data
                )
                
                cement_service.update(cement.id, update_data)
                updated_count += 1
                print(f"✅ Updated {cement_name} with {len(psd_points)} PSD points")
                
            except Exception as e:
                print(f"❌ Error updating {cement_name}: {e}")
        else:
            not_found_count += 1
            print(f"⚠️ Cement {cement_name} not found in database")
    
    print(f"\n📊 Import Summary:")
    print(f"   Successfully updated: {updated_count} cements")
    print(f"   Not found in database: {not_found_count} cements")
    print(f"   Total PSD datasets processed: {len(psd_data)}")

def main():
    """Main function to import PSD data."""
    print("🔄 Starting PSD data import from Derby CSV...")
    print("=" * 60)
    
    # Path to the CSV file
    csv_file = Path(__file__).parent / "psd_data.csv"
    
    if not csv_file.exists():
        print(f"❌ CSV file not found: {csv_file}")
        return
    
    # Extract PSD data from CSV
    print("📄 Extracting PSD data from CSV...")
    psd_data = extract_psd_data_from_csv(csv_file)
    
    if not psd_data:
        print("❌ No PSD data found in CSV file")
        return
    
    print(f"✅ Found PSD data for {len(psd_data)} cements")
    
    # Import to database
    print("\n💾 Importing PSD data to database...")
    import_psd_to_database(psd_data)
    
    print("\n✅ PSD data import completed!")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Fix Aggregate Import from Derby Data

This script properly imports the 6 experimental aggregates from the Derby database
that were missed during the original migration. It replaces the generic "Standard"
aggregates with the actual experimental data.

Original Derby Aggregates:
- Fine: MA106A-1-fine, MA107-6-fine, MA114F-3-fine  
- Coarse: MA106B-4-coarse, MA111-7-coarse, MA99BC-5-coarse
"""

import sys
import csv
import sqlite3
import binascii
import logging
from pathlib import Path
from datetime import datetime

# Increase CSV field size limit for large Derby binary data
csv.field_size_limit(sys.maxsize)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def decode_hex_field(hex_data: str) -> bytes:
    """Decode hex string to binary data."""
    if not hex_data or not hex_data.strip():
        return None
    try:
        # Remove quotes and whitespace
        cleaned_hex = hex_data.strip().strip('"')
        return binascii.unhexlify(cleaned_hex)
    except Exception as e:
        logger.warning(f"Failed to decode hex data: {e}")
        return None

def parse_aggregate_csv_row(row_data: list) -> dict:
    """Parse a single row from the Derby aggregate CSV export."""
    if len(row_data) < 11:
        logger.error(f"Insufficient columns in row: {len(row_data)}")
        return None
    
    # Derby column mapping from migrate_derby_data.py
    # ['DISPLAY_NAME', 'NAME', 'TYPE', 'SPECIFIC_GRAVITY', 'BULK_MODULUS', 
    #  'SHEAR_MODULUS', 'CONDUCTIVITY', 'IMAGE', 'TXT', 'INF', 'SHAPE_STATS']
    
    display_name = row_data[0].strip('"').strip()
    name_field = row_data[1].strip('"').strip() if len(row_data) > 1 else display_name
    
    # Determine aggregate type from name
    aggregate_type = 2 if 'fine' in display_name.lower() else 1  # 2=fine, 1=coarse
    
    # Parse specific gravity (default to 2.65 if not provided)
    try:
        specific_gravity = float(row_data[3].strip('"')) if len(row_data) > 3 and row_data[3].strip('"') else 2.65
    except (ValueError, IndexError):
        specific_gravity = 2.65
    
    # Parse mechanical properties
    try:
        bulk_modulus = float(row_data[4].strip('"')) if len(row_data) > 4 and row_data[4].strip('"') else None
    except (ValueError, IndexError):
        bulk_modulus = None
        
    try:
        shear_modulus = float(row_data[5].strip('"')) if len(row_data) > 5 and row_data[5].strip('"') else None
    except (ValueError, IndexError):
        shear_modulus = None
        
    try:
        conductivity = float(row_data[6].strip('"')) if len(row_data) > 6 and row_data[6].strip('"') else 0.0
    except (ValueError, IndexError):
        conductivity = 0.0
    
    # Decode binary fields
    image_data = decode_hex_field(row_data[7]) if len(row_data) > 7 else None
    txt_data = decode_hex_field(row_data[8]) if len(row_data) > 8 else None
    inf_data = decode_hex_field(row_data[9]) if len(row_data) > 9 else None
    shape_stats = decode_hex_field(row_data[10]) if len(row_data) > 10 else None
    
    return {
        'display_name': display_name,
        'name': name_field,
        'type': aggregate_type,
        'specific_gravity': specific_gravity,
        'bulk_modulus': bulk_modulus,
        'shear_modulus': shear_modulus,
        'conductivity': conductivity,
        'image': image_data,
        'txt': txt_data,
        'inf': inf_data,
        'shape_stats': shape_stats,
        'source': 'Derby Migration',
        'notes': f'Experimental aggregate data imported from original Derby database'
    }

def import_derby_aggregates(csv_file_path: Path, db_path: Path):
    """Import aggregates from Derby CSV export into SQLite database."""
    
    if not csv_file_path.exists():
        logger.error(f"CSV file not found: {csv_file_path}")
        return False
    
    if not db_path.exists():
        logger.error(f"Database not found: {db_path}")
        return False
    
    # Read CSV data
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)
            
        logger.info(f"Found {len(rows)} aggregate records in CSV")
        
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Clear existing generic aggregates
        logger.info("Removing existing generic aggregates...")
        cursor.execute("DELETE FROM aggregate WHERE display_name IN ('standard_coarse', 'standard_fine') OR display_name = '' OR display_name IS NULL")
        
        # Import Derby aggregates
        imported_count = 0
        for i, row in enumerate(rows):
            aggregate_data = parse_aggregate_csv_row(row)
            if not aggregate_data:
                logger.warning(f"Failed to parse row {i+1}")
                continue
                
            # Insert aggregate
            now = datetime.utcnow().isoformat()
            try:
                cursor.execute("""
                    INSERT INTO aggregate (
                        display_name, name, type, specific_gravity, bulk_modulus, 
                        shear_modulus, conductivity, image, txt, inf, shape_stats,
                        source, notes, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    aggregate_data['display_name'],
                    aggregate_data['name'], 
                    aggregate_data['type'],
                    aggregate_data['specific_gravity'],
                    aggregate_data['bulk_modulus'],
                    aggregate_data['shear_modulus'],
                    aggregate_data['conductivity'],
                    aggregate_data['image'],
                    aggregate_data['txt'],
                    aggregate_data['inf'],
                    aggregate_data['shape_stats'],
                    aggregate_data['source'],
                    aggregate_data['notes'],
                    now,
                    now
                ))
                
                imported_count += 1
                logger.info(f"Imported aggregate: {aggregate_data['display_name']} (type {aggregate_data['type']})")
                
            except sqlite3.Error as e:
                logger.error(f"Failed to insert aggregate {aggregate_data['display_name']}: {e}")
                continue
        
        # Commit changes
        conn.commit()
        conn.close()
        
        logger.info(f"Successfully imported {imported_count} aggregates from Derby data")
        return True
        
    except Exception as e:
        logger.error(f"Import failed: {e}")
        return False

def verify_import(db_path: Path):
    """Verify that aggregates were properly imported."""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all aggregates
    cursor.execute("SELECT display_name, name, type, specific_gravity, source FROM aggregate ORDER BY type, display_name")
    aggregates = cursor.fetchall()
    
    conn.close()
    
    logger.info(f"\nDatabase now contains {len(aggregates)} aggregates:")
    
    fine_count = 0
    coarse_count = 0
    
    for display_name, name, agg_type, sg, source in aggregates:
        type_str = "Fine" if agg_type == 2 else "Coarse"
        logger.info(f"  - {display_name} ({type_str}, SG={sg}, Source={source})")
        
        if agg_type == 2:
            fine_count += 1
        else:
            coarse_count += 1
    
    logger.info(f"\nSummary: {fine_count} fine aggregates, {coarse_count} coarse aggregates")
    
    # Check if we have the expected Derby aggregates
    expected_aggregates = [
        'MA106A-1-fine', 'MA107-6-fine', 'MA114F-3-fine',
        'MA106B-4-coarse', 'MA111-7-coarse', 'MA99BC-5-coarse'
    ]
    
    found_names = [display_name for display_name, _, _, _, _ in aggregates]
    
    missing = [name for name in expected_aggregates if name not in found_names]
    if missing:
        logger.warning(f"Missing expected aggregates: {missing}")
    else:
        logger.info("✓ All expected Derby aggregates found!")

def main():
    """Main execution function."""
    
    # Paths
    project_root = Path(__file__).parent
    csv_file = project_root / "derby_export" / "aggregate.csv"
    db_file = project_root / "src" / "data" / "database" / "vcctl.db"
    
    logger.info("VCCTL Derby Aggregate Import Fix")
    logger.info("=" * 50)
    logger.info(f"CSV file: {csv_file}")
    logger.info(f"Database: {db_file}")
    
    # Verify files exist
    if not csv_file.exists():
        logger.error(f"Derby aggregate CSV not found: {csv_file}")
        return 1
        
    if not db_file.exists():
        logger.error(f"SQLite database not found: {db_file}")
        return 1
    
    # Create backup
    backup_file = db_file.parent / f"vcctl_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    logger.info(f"Creating backup: {backup_file}")
    
    try:
        import shutil
        shutil.copy2(db_file, backup_file)
        logger.info("✓ Backup created successfully")
    except Exception as e:
        logger.error(f"Failed to create backup: {e}")
        return 1
    
    # Import aggregates
    logger.info("\nStarting aggregate import...")
    success = import_derby_aggregates(csv_file, db_file)
    
    if not success:
        logger.error("Import failed - restoring backup")
        try:
            shutil.copy2(backup_file, db_file)
            logger.info("✓ Database restored from backup")
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
        return 1
    
    # Verify results
    logger.info("\nVerifying import results...")
    verify_import(db_file)
    
    logger.info(f"\n✓ Aggregate import completed successfully!")
    logger.info(f"✓ Backup saved as: {backup_file}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
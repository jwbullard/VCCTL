#!/usr/bin/env python3
"""
PSD Normalization Migration Script

This script performs a comprehensive migration to normalize PSD data across all material types.
It migrates PSD fields from individual material tables to a unified psd_data table.

Migration Steps:
1. Create psd_data table
2. Backup existing PSD data from all material tables
3. Create PSD records for each material with PSD data
4. Add psd_data_id foreign key columns to material tables
5. Update material records to reference PSD data
6. Remove old PSD columns from material tables

Materials affected: cement, filler, silica_fume, limestone, fly_ash, slag
"""

import sys
import os
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

# Migration script runs standalone without VCCTL imports
# All necessary functionality is implemented directly


class PSDMigrationError(Exception):
    """Custom exception for migration errors."""
    pass


class PSDNormalizationMigration:
    """Handles PSD database normalization migration."""
    
    def __init__(self, database_path: str):
        """Initialize migration with database path."""
        self.database_path = database_path
        self.backup_path = f"{database_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.migration_log = []
        
        # Material tables and their PSD columns
        self.material_tables = {
            'cement': {
                'psd_columns': [
                    'psd', 'psd_custom_points', 'psd_mode', 'psd_d50', 'psd_n', 
                    'psd_dmax', 'psd_median', 'psd_spread', 'psd_exponent',
                    'diameter_percentile_10', 'diameter_percentile_50', 'diameter_percentile_90'
                ],
                'id_column': 'id',
                'name_column': 'name'
            },
            'filler': {
                'psd_columns': [
                    'psd', 'psd_custom_points', 'psd_mode', 'psd_d50', 'psd_n',
                    'psd_dmax', 'psd_median', 'psd_spread', 'psd_exponent',
                    'diameter_percentile_10', 'diameter_percentile_50', 'diameter_percentile_90'
                ],
                'id_column': 'id',
                'name_column': 'name'
            },
            'silica_fume': {
                'psd_columns': [
                    'psd', 'psd_custom_points', 'psd_mode', 'psd_d50', 'psd_n',
                    'psd_dmax', 'psd_median', 'psd_spread', 'psd_exponent',
                    'diameter_percentile_10', 'diameter_percentile_50', 'diameter_percentile_90'
                ],
                'id_column': 'id',
                'name_column': 'name'
            },
            'limestone': {
                'psd_columns': [
                    'psd', 'psd_custom_points', 'psd_mode', 'psd_d50', 'psd_n',
                    'psd_dmax', 'psd_median', 'psd_spread', 'psd_exponent',
                    'diameter_percentile_10', 'diameter_percentile_50', 'diameter_percentile_90'
                ],
                'id_column': 'id',
                'name_column': 'name'
            },
            'fly_ash': {
                'psd_columns': [
                    'psd', 'psd_custom_points', 'psd_mode', 'psd_d50', 'psd_n',
                    'psd_dmax', 'psd_median', 'psd_spread', 'psd_exponent',
                    'diameter_percentile_10', 'diameter_percentile_50', 'diameter_percentile_90'
                ],
                'id_column': 'id',
                'name_column': 'name'
            },
            'slag': {
                'psd_columns': [
                    'psd', 'psd_custom_points', 'psd_mode', 'psd_d50', 'psd_n',
                    'psd_dmax', 'psd_median', 'psd_spread', 'psd_exponent',
                    'diameter_percentile_10', 'diameter_percentile_50', 'diameter_percentile_90'
                ],
                'id_column': 'id',
                'name_column': 'name'
            }
        }

    def log(self, message: str) -> None:
        """Log migration message."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {message}"
        print(log_entry)
        self.migration_log.append(log_entry)

    def backup_database(self) -> None:
        """Create database backup before migration."""
        self.log("Creating database backup...")
        try:
            import shutil
            shutil.copy2(self.database_path, self.backup_path)
            self.log(f"Database backed up to: {self.backup_path}")
        except Exception as e:
            raise PSDMigrationError(f"Failed to backup database: {e}")

    def create_psd_data_table(self, conn: sqlite3.Connection) -> None:
        """Create the psd_data table."""
        self.log("Creating psd_data table...")
        
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS psd_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            psd_reference VARCHAR(64) DEFAULT 'default',
            psd_custom_points TEXT,
            psd_mode VARCHAR(64) DEFAULT 'log_normal',
            psd_d50 REAL CHECK (psd_d50 >= 0 AND psd_d50 <= 1000),
            psd_n REAL CHECK (psd_n >= 0 AND psd_n <= 10),
            psd_dmax REAL CHECK (psd_dmax >= 0 AND psd_dmax <= 1000),
            psd_median REAL CHECK (psd_median >= 0 AND psd_median <= 1000),
            psd_spread REAL CHECK (psd_spread >= 0 AND psd_spread <= 10),
            psd_exponent REAL CHECK (psd_exponent >= 0 AND psd_exponent <= 2),
            diameter_percentile_10 REAL CHECK (diameter_percentile_10 >= 0 AND diameter_percentile_10 <= 1000),
            diameter_percentile_50 REAL CHECK (diameter_percentile_50 >= 0 AND diameter_percentile_50 <= 1000),
            diameter_percentile_90 REAL CHECK (diameter_percentile_90 >= 0 AND diameter_percentile_90 <= 1000),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        conn.execute(create_table_sql)
        conn.commit()
        self.log("psd_data table created successfully")

    def extract_psd_data_from_materials(self, conn: sqlite3.Connection) -> Dict[str, List[Dict[str, Any]]]:
        """Extract PSD data from all material tables."""
        self.log("Extracting PSD data from material tables...")
        
        extracted_data = {}
        
        for table_name, config in self.material_tables.items():
            self.log(f"Processing {table_name} table...")
            
            # Check if table exists
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name=?
            """, (table_name,))
            
            if not cursor.fetchone():
                self.log(f"Table {table_name} does not exist, skipping...")
                continue
            
            # Get table structure to see which PSD columns exist
            cursor = conn.execute(f"PRAGMA table_info({table_name})")
            existing_columns = [row[1] for row in cursor.fetchall()]
            
            # Filter PSD columns to only those that exist
            available_psd_columns = [col for col in config['psd_columns'] if col in existing_columns]
            
            if not available_psd_columns:
                self.log(f"No PSD columns found in {table_name}, skipping...")
                extracted_data[table_name] = []
                continue
            
            # Build query to extract PSD data
            columns_str = ', '.join([config['id_column'], config['name_column']] + available_psd_columns)
            query = f"SELECT {columns_str} FROM {table_name}"
            
            cursor = conn.execute(query)
            rows = cursor.fetchall()
            
            # Convert to dictionaries
            column_names = [config['id_column'], config['name_column']] + available_psd_columns
            material_data = []
            
            for row in rows:
                row_dict = dict(zip(column_names, row))
                
                # Only include records that have at least some PSD data
                has_psd_data = any(row_dict.get(col) is not None for col in available_psd_columns)
                
                if has_psd_data:
                    material_data.append(row_dict)
            
            extracted_data[table_name] = material_data
            self.log(f"Extracted {len(material_data)} records with PSD data from {table_name}")
        
        return extracted_data

    def create_psd_records(self, conn: sqlite3.Connection, extracted_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Dict[int, int]]:
        """Create PSD records and return mapping of material_id -> psd_data_id."""
        self.log("Creating PSD records...")
        
        material_psd_mapping = {}
        
        for table_name, records in extracted_data.items():
            material_psd_mapping[table_name] = {}
            
            for record in records:
                material_id = record[self.material_tables[table_name]['id_column']]
                material_name = record[self.material_tables[table_name]['name_column']]
                
                # Create PSD reference name
                psd_reference = record.get('psd') or f"{table_name}_{material_name}_{material_id}"
                
                # Build PSD data insert
                psd_data = {
                    'psd_reference': psd_reference,
                    'psd_custom_points': record.get('psd_custom_points'),
                    'psd_mode': record.get('psd_mode') or 'log_normal',
                    'psd_d50': record.get('psd_d50'),
                    'psd_n': record.get('psd_n'),
                    'psd_dmax': record.get('psd_dmax'),
                    'psd_median': record.get('psd_median'),
                    'psd_spread': record.get('psd_spread'),
                    'psd_exponent': record.get('psd_exponent'),
                    'diameter_percentile_10': record.get('diameter_percentile_10'),
                    'diameter_percentile_50': record.get('diameter_percentile_50'),
                    'diameter_percentile_90': record.get('diameter_percentile_90')
                }
                
                # Remove None values
                psd_data = {k: v for k, v in psd_data.items() if v is not None}
                
                if psd_data:
                    # Insert PSD record
                    columns = ', '.join(psd_data.keys())
                    placeholders = ', '.join(['?' for _ in psd_data])
                    
                    cursor = conn.execute(
                        f"INSERT INTO psd_data ({columns}) VALUES ({placeholders})",
                        list(psd_data.values())
                    )
                    
                    psd_data_id = cursor.lastrowid
                    material_psd_mapping[table_name][material_id] = psd_data_id
                    
                    self.log(f"Created PSD record {psd_data_id} for {table_name}.{material_id}")
        
        conn.commit()
        return material_psd_mapping

    def add_foreign_key_columns(self, conn: sqlite3.Connection) -> None:
        """Add psd_data_id foreign key columns to material tables."""
        self.log("Adding psd_data_id foreign key columns...")
        
        for table_name in self.material_tables.keys():
            # Check if table exists
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name=?
            """, (table_name,))
            
            if not cursor.fetchone():
                continue
            
            # Check if column already exists
            cursor = conn.execute(f"PRAGMA table_info({table_name})")
            existing_columns = [row[1] for row in cursor.fetchall()]
            
            if 'psd_data_id' not in existing_columns:
                conn.execute(f"ALTER TABLE {table_name} ADD COLUMN psd_data_id INTEGER")
                self.log(f"Added psd_data_id column to {table_name}")
        
        conn.commit()

    def update_material_foreign_keys(self, conn: sqlite3.Connection, material_psd_mapping: Dict[str, Dict[int, int]]) -> None:
        """Update material records to reference PSD data."""
        self.log("Updating material foreign key references...")
        
        for table_name, mapping in material_psd_mapping.items():
            for material_id, psd_data_id in mapping.items():
                conn.execute(
                    f"UPDATE {table_name} SET psd_data_id = ? WHERE id = ?",
                    (psd_data_id, material_id)
                )
                self.log(f"Updated {table_name}.{material_id} -> psd_data.{psd_data_id}")
        
        conn.commit()

    def remove_psd_columns(self, conn: sqlite3.Connection) -> None:
        """Remove PSD columns from material tables."""
        self.log("Removing PSD columns from material tables...")
        
        for table_name, config in self.material_tables.items():
            # Check if table exists
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name=?
            """, (table_name,))
            
            if not cursor.fetchone():
                continue
            
            # Get current table structure
            cursor = conn.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            # Filter out PSD columns
            remaining_columns = []
            for col in columns:
                col_name = col[1]
                if col_name not in config['psd_columns']:
                    remaining_columns.append(col)
            
            if len(remaining_columns) < len(columns):
                # Need to recreate table without PSD columns
                self.log(f"Recreating {table_name} without PSD columns...")
                
                # Create column definitions for new table
                new_columns = []
                for col in remaining_columns:
                    col_def = f"{col[1]} {col[2]}"
                    if col[3]:  # NOT NULL
                        col_def += " NOT NULL"
                    if col[4] is not None:  # Default value
                        col_def += f" DEFAULT {col[4]}"
                    if col[5]:  # Primary key
                        col_def += " PRIMARY KEY"
                    new_columns.append(col_def)
                
                column_names = [col[1] for col in remaining_columns]
                columns_str = ', '.join(column_names)
                new_table_sql = f"CREATE TABLE {table_name}_new ({', '.join(new_columns)})"
                
                # Create new table
                conn.execute(new_table_sql)
                
                # Copy data
                conn.execute(f"INSERT INTO {table_name}_new ({columns_str}) SELECT {columns_str} FROM {table_name}")
                
                # Drop old table and rename new one
                conn.execute(f"DROP TABLE {table_name}")
                conn.execute(f"ALTER TABLE {table_name}_new RENAME TO {table_name}")
                
                self.log(f"Recreated {table_name} without {len(columns) - len(remaining_columns)} PSD columns")
        
        conn.commit()

    def save_migration_log(self) -> None:
        """Save migration log to file."""
        log_path = f"{self.database_path}_migration_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(log_path, 'w') as f:
            f.write('\n'.join(self.migration_log))
        self.log(f"Migration log saved to: {log_path}")

    def run_migration(self) -> None:
        """Run the complete PSD normalization migration."""
        self.log("Starting PSD normalization migration...")
        
        try:
            # Backup database
            self.backup_database()
            
            # Connect to database
            conn = sqlite3.connect(self.database_path)
            conn.execute("PRAGMA foreign_keys = ON")
            
            try:
                # Step 1: Create psd_data table
                self.create_psd_data_table(conn)
                
                # Step 2: Extract PSD data from material tables
                extracted_data = self.extract_psd_data_from_materials(conn)
                
                # Step 3: Create PSD records
                material_psd_mapping = self.create_psd_records(conn, extracted_data)
                
                # Step 4: Add foreign key columns
                self.add_foreign_key_columns(conn)
                
                # Step 5: Update foreign key references
                self.update_material_foreign_keys(conn, material_psd_mapping)
                
                # Step 6: Remove old PSD columns
                self.remove_psd_columns(conn)
                
                self.log("PSD normalization migration completed successfully!")
                
            finally:
                conn.close()
                
        except Exception as e:
            self.log(f"Migration failed: {e}")
            raise PSDMigrationError(f"Migration failed: {e}")
        
        finally:
            self.save_migration_log()


def main():
    """Main migration function."""
    if len(sys.argv) != 2:
        print("Usage: python psd_normalization_migration.py <database_path>")
        sys.exit(1)
    
    database_path = sys.argv[1]
    
    if not os.path.exists(database_path):
        print(f"Database file not found: {database_path}")
        sys.exit(1)
    
    migration = PSDNormalizationMigration(database_path)
    
    try:
        migration.run_migration()
        print("\nMigration completed successfully!")
        print(f"Database backup: {migration.backup_path}")
    except PSDMigrationError as e:
        print(f"\nMigration failed: {e}")
        print(f"Database backup available at: {migration.backup_path}")
        sys.exit(1)


if __name__ == "__main__":
    main()
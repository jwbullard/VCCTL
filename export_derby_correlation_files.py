#!/usr/bin/env python3
"""
Improved Derby Database Export Script for VCCTL Correlation Files

This script exports correlation files (.c3a, .c4f, .sil, .alu, .c3s) from Derby database
with proper binary data handling to fix the missing correlation data issue.

Author: Claude and Jeff Bullard
Date: July 22, 2025
"""

import os
import sys
import jaydebeapi
import csv
import logging
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('derby_export.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DerbyCorrelationExporter:
    """Export correlation files from Derby database with proper binary handling."""
    
    def __init__(self, derby_path: str, output_dir: str = "derby_export_fixed"):
        self.derby_path = derby_path
        self.output_dir = output_dir
        self.connection = None
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Derby driver path - adjust if needed
        self.derby_jar = os.path.join(os.path.dirname(derby_path), "db-derby-10.6.2.1-bin", "lib", "derby.jar")
        if not os.path.exists(self.derby_jar):
            # Try alternative path
            self.derby_jar = os.path.join(os.getcwd(), "db-derby-10.6.2.1-bin", "lib", "derby.jar")
    
    def connect(self):
        """Connect to Derby database."""
        try:
            logger.info(f"Connecting to Derby database: {self.derby_path}")
            logger.info(f"Using Derby JAR: {self.derby_jar}")
            
            # Connect to Derby database
            self.connection = jaydebeapi.connect(
                "org.apache.derby.jdbc.EmbeddedDriver",
                f"jdbc:derby:{self.derby_path};create=false",
                {"user": "", "password": ""},
                self.derby_jar
            )
            logger.info("Successfully connected to Derby database")
            
        except Exception as e:
            logger.error(f"Failed to connect to Derby database: {e}")
            raise
    
    def disconnect(self):
        """Disconnect from Derby database."""
        if self.connection:
            try:
                self.connection.close()
                logger.info("Disconnected from Derby database")
            except Exception as e:
                logger.error(f"Error disconnecting: {e}")
    
    def export_cement_correlation_files(self):
        """Export correlation files for all cement materials."""
        try:
            cursor = self.connection.cursor()
            
            # First get just the cement names
            cursor.execute("SELECT name FROM cement ORDER BY name")
            cement_names = [row[0] for row in cursor.fetchall()]
            
            logger.info(f"Found {len(cement_names)} cement records")
            
            # Track statistics
            stats = {
                'total_cements': len(cement_names),
                'c3a_files': 0,
                'c4f_files': 0,
                'sil_files': 0,
                'alu_files': 0,
                'c3s_files': 0,
                'empty_c3a': 0,
                'empty_c4f': 0
            }
            
            # Process each cement individually to handle BLOB objects properly
            for name in cement_names:
                logger.info(f"Processing cement: {name}")
                
                # Get correlation data for this specific cement
                cursor.execute("SELECT c3a, c4f, sil, alu, c3s FROM cement WHERE name = ?", [name])
                row = cursor.fetchone()
                if row is None:
                    logger.warning(f"No data found for cement: {name}")
                    continue
                
                c3a_blob, c4f_blob, sil_blob, alu_blob, c3s_blob = row
                
                # Export each correlation file type
                if c3a_blob is not None:
                    try:
                        # Handle Derby BLOB objects
                        if hasattr(c3a_blob, 'getBinaryStream'):
                            # It's a Derby BLOB - read the bytes
                            blob_stream = c3a_blob.getBinaryStream()
                            c3a_bytes = blob_stream.readAllBytes()
                            blob_stream.close()
                        elif isinstance(c3a_blob, bytes):
                            c3a_bytes = c3a_blob
                        else:
                            # Fallback - try to convert to bytes
                            c3a_bytes = bytes(c3a_blob)
                        
                        if len(c3a_bytes) > 10:  # Only export if substantial data
                            c3a_path = os.path.join(self.output_dir, f"{name}.c3a")
                            with open(c3a_path, 'wb') as f:
                                f.write(c3a_bytes)
                            stats['c3a_files'] += 1
                            logger.info(f"  Exported C3A correlation: {len(c3a_bytes)} bytes")
                        else:
                            stats['empty_c3a'] += 1
                            logger.warning(f"  C3A correlation too small: {len(c3a_bytes)} bytes")
                    except Exception as e:
                        logger.error(f"  Failed to export C3A for {name}: {e}")
                        stats['empty_c3a'] += 1
                
                if c4f_blob is not None:
                    try:
                        # Handle Derby BLOB objects
                        if hasattr(c4f_blob, 'getBinaryStream'):
                            blob_stream = c4f_blob.getBinaryStream()
                            c4f_bytes = blob_stream.readAllBytes()
                            blob_stream.close()
                        elif isinstance(c4f_blob, bytes):
                            c4f_bytes = c4f_blob
                        else:
                            c4f_bytes = bytes(c4f_blob)
                        
                        if len(c4f_bytes) > 10:  # Only export if substantial data
                            c4f_path = os.path.join(self.output_dir, f"{name}.c4f")
                            with open(c4f_path, 'wb') as f:
                                f.write(c4f_bytes)
                            stats['c4f_files'] += 1
                            logger.info(f"  Exported C4F correlation: {len(c4f_bytes)} bytes")
                        else:
                            stats['empty_c4f'] += 1
                            logger.warning(f"  C4F correlation too small: {len(c4f_bytes)} bytes")
                    except Exception as e:
                        logger.error(f"  Failed to export C4F for {name}: {e}")
                        stats['empty_c4f'] += 1
                
                # Export other correlation files (SIL, ALU, C3S)
                for corr_blob, extension, stat_key in [
                    (sil_blob, 'sil', 'sil_files'),
                    (alu_blob, 'alu', 'alu_files'),
                    (c3s_blob, 'c3s', 'c3s_files')
                ]:
                    if corr_blob is not None:
                        try:
                            # Handle Derby BLOB objects
                            if hasattr(corr_blob, 'getBinaryStream'):
                                blob_stream = corr_blob.getBinaryStream()
                                corr_bytes = blob_stream.readAllBytes()
                                blob_stream.close()
                            elif isinstance(corr_blob, bytes):
                                corr_bytes = corr_blob
                            else:
                                corr_bytes = bytes(corr_blob)
                            
                            if len(corr_bytes) > 10:
                                corr_path = os.path.join(self.output_dir, f"{name}.{extension}")
                                with open(corr_path, 'wb') as f:
                                    f.write(corr_bytes)
                                stats[stat_key] += 1
                                logger.info(f"  Exported {extension.upper()} correlation: {len(corr_bytes)} bytes")
                        except Exception as e:
                            logger.error(f"  Failed to export {extension.upper()} for {name}: {e}")
            
            # Print statistics
            logger.info("\n" + "="*50)
            logger.info("EXPORT STATISTICS")
            logger.info("="*50)
            logger.info(f"Total cement materials: {stats['total_cements']}")
            logger.info(f"C3A files exported: {stats['c3a_files']}")
            logger.info(f"C4F files exported: {stats['c4f_files']}")
            logger.info(f"SIL files exported: {stats['sil_files']}")
            logger.info(f"ALU files exported: {stats['alu_files']}")
            logger.info(f"C3S files exported: {stats['c3s_files']}")
            logger.info(f"Empty/missing C3A: {stats['empty_c3a']}")
            logger.info(f"Empty/missing C4F: {stats['empty_c4f']}")
            
            missing_c3a_or_c4f = stats['empty_c3a'] + stats['empty_c4f'] - stats['total_cements'] + stats['c3a_files'] + stats['c4f_files']
            cements_with_c3a_or_c4f = stats['c3a_files'] + stats['c4f_files']
            logger.info(f"Cements with C3A or C4F data: {cements_with_c3a_or_c4f}")
            
            cursor.close()
            return stats
            
        except Exception as e:
            logger.error(f"Failed to export correlation files: {e}")
            raise
    
    def create_import_script(self, stats: Dict[str, int]):
        """Create a Python script to import the exported correlation files."""
        script_content = f'''#!/usr/bin/env python3
"""
Import correlation files into SQLite database

Generated automatically by Derby export script.
Run this after successful Derby export to update SQLite database.

Statistics from Derby export:
- Total cement materials: {stats['total_cements']}
- C3A files exported: {stats['c3a_files']}
- C4F files exported: {stats['c4f_files']}
- SIL files exported: {stats['sil_files']}
- ALU files exported: {stats['alu_files']}
- C3S files exported: {stats['c3s_files']}
"""

import os
import sys
sys.path.append('/Users/jwbullard/Library/CloudStorage/OneDrive-TexasA&MUniversity/Documents/Projects/Modeling/VCCTL-THAMES-SPRING/vcctl-gtk/src')

from app.database.service import DatabaseService
from app.database.models import Cement
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def import_correlation_files():
    """Import correlation files from Derby export into SQLite database."""
    
    # Initialize database service
    db_service = DatabaseService()
    
    export_dir = "{self.output_dir}"
    imported_count = 0
    
    try:
        with db_service.get_session() as session:
            # Get all cement materials
            cements = session.query(Cement).all()
            logger.info(f"Found {{len(cements)}} cement materials in SQLite database")
            
            for cement in cements:
                cement_name = cement.name
                logger.info(f"Processing cement: {{cement_name}}")
                
                # Check for C3A correlation file
                c3a_path = os.path.join(export_dir, f"{{cement_name}}.c3a")
                if os.path.exists(c3a_path):
                    try:
                        with open(c3a_path, 'rb') as f:
                            cement.c3a_correlation = f.read()
                        logger.info(f"  Updated C3A correlation ({{len(cement.c3a_correlation)}} bytes)")
                        imported_count += 1
                    except Exception as e:
                        logger.error(f"  Failed to import C3A: {{e}}")
                
                # Check for C4F correlation file
                c4f_path = os.path.join(export_dir, f"{{cement_name}}.c4f")
                if os.path.exists(c4f_path):
                    try:
                        with open(c4f_path, 'rb') as f:
                            cement.c4f_correlation = f.read()
                        logger.info(f"  Updated C4F correlation ({{len(cement.c4f_correlation)}} bytes)")
                        imported_count += 1
                    except Exception as e:
                        logger.error(f"  Failed to import C4F: {{e}}")
                
                # Import other correlation files
                for extension, attr_name in [
                    ('sil', 'sil_correlation'),
                    ('alu', 'alu_correlation'),
                    ('c3s', 'c3s_correlation')
                ]:
                    corr_path = os.path.join(export_dir, f"{{cement_name}}.{{extension}}")
                    if os.path.exists(corr_path):
                        try:
                            with open(corr_path, 'rb') as f:
                                setattr(cement, attr_name, f.read())
                            corr_data = getattr(cement, attr_name)
                            logger.info(f"  Updated {{extension.upper()}} correlation ({{len(corr_data)}} bytes)")
                            imported_count += 1
                        except Exception as e:
                            logger.error(f"  Failed to import {{extension.upper()}}: {{e}}")
            
            # Commit all changes
            session.commit()
            logger.info(f"\\nSuccessfully imported {{imported_count}} correlation files")
            
    except Exception as e:
        logger.error(f"Import failed: {{e}}")
        raise

if __name__ == "__main__":
    import_correlation_files()
'''
        
        script_path = os.path.join(self.output_dir, "import_correlation_files.py")
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        logger.info(f"Created import script: {script_path}")
        return script_path

def main():
    """Main execution function."""
    
    # Derby database path - adjust as needed
    derby_path = "/Users/jwbullard/Library/CloudStorage/OneDrive-TexasA&MUniversity/Documents/Projects/Modeling/VCCTL-THAMES-SPRING/vcctl-gtk/derby_original_database/vcctl_cement"
    
    if not os.path.exists(derby_path):
        logger.error(f"Derby database not found: {derby_path}")
        logger.info("Please update the derby_path variable in this script")
        return 1
    
    exporter = DerbyCorrelationExporter(derby_path)
    
    try:
        # Connect to Derby
        exporter.connect()
        
        # Export correlation files
        logger.info("Starting correlation file export...")
        stats = exporter.export_cement_correlation_files()
        
        # Create import script
        import_script = exporter.create_import_script(stats)
        
        logger.info(f"\\nExport completed successfully!")
        logger.info(f"Correlation files saved to: {exporter.output_dir}")
        logger.info(f"Import script created: {import_script}")
        logger.info("\\nNext steps:")
        logger.info(f"1. Review exported files in {exporter.output_dir}")
        logger.info(f"2. Run the import script: python {import_script}")
        logger.info("3. Test with cement152 or another cement to verify fix")
        
        return 0
        
    except Exception as e:
        logger.error(f"Export failed: {e}")
        return 1
        
    finally:
        exporter.disconnect()

if __name__ == "__main__":
    sys.exit(main())
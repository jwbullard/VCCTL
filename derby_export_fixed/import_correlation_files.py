#!/usr/bin/env python3
"""
Import correlation files into SQLite database

Generated automatically by Derby export script.
Run this after successful Derby export to update SQLite database.

Statistics from Derby export:
- Total cement materials: 36
- C3A files exported: 24
- C4F files exported: 12
- SIL files exported: 36
- ALU files exported: 9
- C3S files exported: 36
"""

import os
import sys
sys.path.append('/Users/jwbullard/Library/CloudStorage/OneDrive-TexasA&MUniversity/Documents/Projects/Modeling/VCCTL-THAMES-SPRING/vcctl-gtk/src')

from app.database.service import DatabaseService
from app.models.cement import Cement
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def import_correlation_files():
    """Import correlation files from Derby export into SQLite database."""
    
    # Initialize database service
    db_service = DatabaseService()
    
    export_dir = "derby_export_fixed"
    imported_count = 0
    
    try:
        with db_service.get_session() as session:
            # Get all cement materials
            cements = session.query(Cement).all()
            logger.info(f"Found {len(cements)} cement materials in SQLite database")
            
            for cement in cements:
                cement_name = cement.name
                logger.info(f"Processing cement: {cement_name}")
                
                # Check for C3A correlation file
                c3a_path = os.path.join(export_dir, f"{cement_name}.c3a")
                if os.path.exists(c3a_path):
                    try:
                        with open(c3a_path, 'rb') as f:
                            cement.c3a_correlation = f.read()
                        logger.info(f"  Updated C3A correlation ({len(cement.c3a_correlation)} bytes)")
                        imported_count += 1
                    except Exception as e:
                        logger.error(f"  Failed to import C3A: {e}")
                
                # Check for C4F correlation file
                c4f_path = os.path.join(export_dir, f"{cement_name}.c4f")
                if os.path.exists(c4f_path):
                    try:
                        with open(c4f_path, 'rb') as f:
                            cement.c4f_correlation = f.read()
                        logger.info(f"  Updated C4F correlation ({len(cement.c4f_correlation)} bytes)")
                        imported_count += 1
                    except Exception as e:
                        logger.error(f"  Failed to import C4F: {e}")
                
                # Import other correlation files
                for extension, attr_name in [
                    ('sil', 'sil_correlation'),
                    ('alu', 'alu_correlation'),
                    ('c3s', 'c3s_correlation')
                ]:
                    corr_path = os.path.join(export_dir, f"{cement_name}.{extension}")
                    if os.path.exists(corr_path):
                        try:
                            with open(corr_path, 'rb') as f:
                                setattr(cement, attr_name, f.read())
                            corr_data = getattr(cement, attr_name)
                            logger.info(f"  Updated {extension.upper()} correlation ({len(corr_data)} bytes)")
                            imported_count += 1
                        except Exception as e:
                            logger.error(f"  Failed to import {extension.upper()}: {e}")
            
            # Commit all changes
            session.commit()
            logger.info(f"\nSuccessfully imported {imported_count} correlation files")
            
    except Exception as e:
        logger.error(f"Import failed: {e}")
        raise

if __name__ == "__main__":
    import_correlation_files()

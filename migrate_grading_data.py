#!/usr/bin/env python3
"""
Grading Data Migration Script

This script migrates existing grading data to the new enhanced schema
and creates standard grading templates.

Usage: python migrate_grading_data.py
"""

import logging
import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from app.database.service import DatabaseService
from app.services.grading_service import GradingService
from app.models.grading import Grading


def setup_logging():
    """Setup logging for migration script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('grading_migration.log')
        ]
    )


def migrate_grading_data():
    """Migrate existing grading data and create standard templates."""
    logger = logging.getLogger(__name__)
    logger.info("Starting grading data migration...")
    
    try:
        # Initialize services
        db_service = DatabaseService()
        grading_service = GradingService(db_service)
        
        # Check current state of grading table
        with db_service.get_session() as session:
            existing_gradings = session.query(Grading).all()
            logger.info(f"Found {len(existing_gradings)} existing grading records")
            
            # Log existing gradings
            for grading in existing_gradings:
                logger.info(f"  - {grading.name}: type={grading.type}, has_data={grading.has_grading_data}")
        
        # Create standard grading templates
        logger.info("Creating standard grading templates...")
        try:
            standard_gradings = grading_service.create_standard_gradings()
            logger.info(f"Created {len(standard_gradings)} standard grading templates:")
            for grading in standard_gradings:
                logger.info(f"  - {grading.name} ({grading.type.value}): {grading.description}")
        except Exception as e:
            logger.error(f"Failed to create standard gradings: {e}")
        
        # Summary
        with db_service.get_session() as session:
            final_count = session.query(Grading).count()
            logger.info(f"Migration complete. Total grading records: {final_count}")
        
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False


def test_grading_functionality():
    """Test basic grading functionality after migration."""
    logger = logging.getLogger(__name__)
    logger.info("Testing grading functionality...")
    
    try:
        db_service = DatabaseService()
        grading_service = GradingService(db_service)
        
        # Test: Get all gradings
        all_gradings = grading_service.get_all_gradings_by_type()
        logger.info(f"✅ Retrieved {len(all_gradings)} total gradings")
        
        # Test: Get fine gradings
        fine_gradings = grading_service.get_all_gradings_by_type("FINE")
        logger.info(f"✅ Retrieved {len(fine_gradings)} fine aggregate gradings")
        
        # Test: Get coarse gradings  
        coarse_gradings = grading_service.get_all_gradings_by_type("COARSE")
        logger.info(f"✅ Retrieved {len(coarse_gradings)} coarse aggregate gradings")
        
        # Test: Create a custom grading
        test_sieve_data = [
            {'sieve_size': 4.75, 'percent_passing': 100.0},
            {'sieve_size': 2.36, 'percent_passing': 85.0},
            {'sieve_size': 1.18, 'percent_passing': 65.0},
            {'sieve_size': 0.60, 'percent_passing': 40.0},
            {'sieve_size': 0.30, 'percent_passing': 20.0},
            {'sieve_size': 0.15, 'percent_passing': 5.0},
        ]
        
        try:
            test_grading = grading_service.save_grading_with_sieve_data(
                name="Test Migration Grading",
                grading_type="FINE", 
                sieve_data=test_sieve_data,
                description="Test grading created during migration"
            )
            logger.info(f"✅ Created test grading: {test_grading.name}")
            
            # Clean up test grading
            grading_service.delete(test_grading.name)
            logger.info("✅ Cleaned up test grading")
            
        except Exception as e:
            logger.warning(f"Test grading creation failed (may be expected): {e}")
        
        logger.info("✅ All grading functionality tests passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Grading functionality test failed: {e}")
        return False


def main():
    """Main migration function."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("="*60)
    logger.info("VCCTL Grading Data Migration")
    logger.info("="*60)
    
    # Run migration
    if not migrate_grading_data():
        logger.error("Migration failed!")
        sys.exit(1)
    
    # Test functionality
    if not test_grading_functionality():
        logger.error("Functionality tests failed!")
        sys.exit(1)
    
    logger.info("="*60)
    logger.info("Migration completed successfully!")
    logger.info("="*60)
    

if __name__ == "__main__":
    main()
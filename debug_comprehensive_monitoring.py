#!/usr/bin/env python3

import sys
import os
sys.path.append('src')

import logging
from datetime import datetime
from pathlib import Path
import time

# Set up detailed logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_actual_monitoring_state():
    """Test the actual state of the Operations Panel monitoring system."""
    
    logger.info("=== COMPREHENSIVE MONITORING DIAGNOSTIC ===")
    
    try:
        # Import the service container to get actual running state
        from app.services.service_container import get_service_container
        container = get_service_container()
        
        # Check database operations
        logger.info("\n1. DATABASE STATE:")
        with container.database_service.get_read_only_session() as session:
            from app.models.operation import Operation as DBOperation
            db_ops = session.query(DBOperation).all()
            logger.info(f"Total database operations: {len(db_ops)}")
            
            for db_op in db_ops:
                logger.info(f"  DB Op: {db_op.name} | Status: {db_op.status} | Progress: {getattr(db_op, 'progress', 'N/A')}")
        
        # Check if we can create an Operations Panel
        logger.info("\n2. OPERATIONS PANEL STATE:")
        try:
            from app.windows.panels.operations_monitoring_panel import OperationsMonitoringPanel
            # Can't actually create the panel without GTK, but we can check class methods
            logger.info(f"OperationsMonitoringPanel class exists: {OperationsMonitoringPanel is not None}")
            logger.info(f"Has _parse_simple_progress: {hasattr(OperationsMonitoringPanel, '_parse_simple_progress')}")
            logger.info(f"Has _monitoring_loop: {hasattr(OperationsMonitoringPanel, '_monitoring_loop')}")
        except Exception as e:
            logger.error(f"Cannot import OperationsMonitoringPanel: {e}")
        
        # Check progress files on disk
        logger.info("\n3. PROGRESS FILES STATE:")
        operations_dir = Path("Operations")
        if operations_dir.exists():
            for op_folder in operations_dir.iterdir():
                if op_folder.is_dir():
                    progress_file = op_folder / "genmic_progress.txt"
                    if progress_file.exists():
                        try:
                            with open(progress_file, 'r') as f:
                                content = f.read().strip()
                            logger.info(f"  {op_folder.name}: {repr(content)}")
                        except Exception as e:
                            logger.error(f"  {op_folder.name}: Error reading - {e}")
                    else:
                        logger.info(f"  {op_folder.name}: No progress file")
        
        logger.info("\n4. ANALYSIS:")
        logger.info("The issue is likely one of:")
        logger.info("A) Monitoring loop not running at all")
        logger.info("B) Operations not loaded into memory correctly")
        logger.info("C) _parse_operation_stdout not being called")
        logger.info("D) Progress updates not being saved to database")
        logger.info("E) UI not refreshing from database")
        
    except Exception as e:
        logger.error(f"Diagnostic failed: {e}")
        import traceback
        traceback.print_exc()

def create_monitoring_test():
    """Create a simple test that mimics what the monitoring loop should do."""
    logger.info("\n=== MONITORING LOOP SIMULATION ===")
    
    try:
        # Test the exact logic from _parse_simple_progress
        progress_file = Path("Operations/YAP14/genmic_progress.txt")
        
        if progress_file.exists():
            with open(progress_file, 'r') as f:
                content = f.read().strip()
            logger.info(f"Progress file content: {repr(content)}")
            
            # Simulate the _parse_simple_progress logic
            if content.startswith("PROGRESS:"):
                data = content[9:].strip()
                parts = data.split(' ', 1)
                
                if len(parts) >= 2:
                    progress_str, message = parts[0], parts[1]
                    try:
                        progress = float(progress_str)
                        logger.info(f"✅ Would update operation to: {progress * 100:.1f}% - '{message}'")
                        
                        if progress >= 1.0:
                            logger.info("✅ Would mark operation as COMPLETED")
                        else:
                            logger.info(f"✅ Would mark operation as RUNNING at {progress * 100:.1f}%")
                            
                    except ValueError as e:
                        logger.error(f"❌ Cannot parse progress: {e}")
                else:
                    logger.error("❌ Cannot split progress data")
            else:
                logger.error("❌ Content doesn't start with PROGRESS:")
        else:
            logger.error("❌ Progress file doesn't exist")
            
    except Exception as e:
        logger.error(f"Monitoring simulation failed: {e}")

if __name__ == "__main__":
    test_actual_monitoring_state()
    create_monitoring_test()
    
    logger.info("\n=== NEXT STEPS ===")
    logger.info("1. Run this diagnostic")
    logger.info("2. Start VCCTL application")
    logger.info("3. Check if Operations Panel actually loads any operations")
    logger.info("4. Start a new microstructure operation")
    logger.info("5. Check if monitoring loop log messages appear")
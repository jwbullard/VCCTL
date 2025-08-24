#!/usr/bin/env python3

import sys
import os
sys.path.append('src')

from pathlib import Path
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_progress_file_parsing():
    """Test the exact logic used in operations monitoring panel."""
    
    # Test the YAP14 progress file
    operations_dir = Path("Operations")
    yap14_dir = operations_dir / "YAP14"
    progress_file = yap14_dir / "genmic_progress.txt"
    
    logger.info(f"Testing progress file: {progress_file}")
    logger.info(f"File exists: {progress_file.exists()}")
    
    if progress_file.exists():
        try:
            with open(progress_file, 'r') as f:
                content = f.read().strip()
                logger.info(f"Progress file content: {repr(content)}")
                
                # Test the parsing logic from _parse_simple_progress
                if content.startswith("PROGRESS:"):
                    logger.info("✅ Content starts with PROGRESS:")
                    
                    # Remove "PROGRESS: " prefix
                    data = content[9:].strip()
                    logger.info(f"After removing prefix: {repr(data)}")
                    
                    # Split into progress and message
                    parts = data.split(' ', 1)
                    logger.info(f"Split parts: {parts}")
                    
                    if len(parts) >= 2:
                        progress_str, message = parts[0], parts[1]
                        logger.info(f"Progress string: {repr(progress_str)}")
                        logger.info(f"Message: {repr(message)}")
                        
                        try:
                            progress = float(progress_str)
                            logger.info(f"✅ Parsed progress: {progress}")
                            logger.info(f"✅ Progress as percentage: {progress * 100:.1f}%")
                            
                            if progress >= 1.0:
                                logger.info("✅ Operation should be marked as COMPLETED")
                            else:
                                logger.info(f"✅ Operation should be marked as RUNNING at {progress * 100:.1f}%")
                                
                        except ValueError as e:
                            logger.error(f"❌ Failed to parse progress as float: {e}")
                    else:
                        logger.error("❌ Could not split content into progress and message")
                else:
                    logger.error("❌ Content does not start with 'PROGRESS:'")
                    
        except Exception as e:
            logger.error(f"❌ Error reading progress file: {e}")
    else:
        logger.error("❌ Progress file does not exist")

def test_file_detection_logic():
    """Test the file detection logic from _parse_operation_stdout."""
    
    logger.info("\n=== Testing File Detection Logic ===")
    
    # Simulate the folder detection logic
    operations_dir = Path("Operations")
    folder_name = "YAP14"
    
    # This is the exact logic from the monitoring panel
    if operations_dir.exists():
        progress_file = operations_dir / folder_name / "genmic_progress.txt"
        logger.info(f"Looking for progress file: {progress_file}")
        logger.info(f"Progress file exists: {progress_file.exists()}")
        
        if progress_file.exists():
            stdout_path = str(progress_file)
            logger.info(f"✅ Would use stdout_path: {stdout_path}")
        else:
            logger.error("❌ Progress file not found")
    else:
        logger.error("❌ Operations directory not found")

if __name__ == "__main__":
    logger.info("=== DEBUGGING OPERATIONS MONITORING ===")
    test_progress_file_parsing()
    test_file_detection_logic()
    logger.info("=== END DEBUG ===")
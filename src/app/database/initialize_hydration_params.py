#!/usr/bin/env python3
"""
Hydration Parameters Initialization for VCCTL

Initializes the hydration_parameters table with default parameter set
from the default.prm file.
"""

import os
import sys
import logging
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database.service import DatabaseService
from app.models.hydration_parameters import HydrationParameters
from app.services.service_container import get_service_container


def initialize_hydration_parameters(database_service: DatabaseService = None):
    """
    Initialize hydration parameters table with portland_cement_standard.
    
    Args:
        database_service: Optional database service. If None, uses service container.
    """
    logger = logging.getLogger('VCCTL.HydrationInit')
    
    try:
        # Get database service
        if database_service is None:
            container = get_service_container()
            database_service = container.database_service
        
        # Path to parameters.csv file
        project_root = Path(__file__).parent.parent.parent.parent
        default_prm_path = project_root / "parameters.csv"
        
        if not default_prm_path.exists():
            raise FileNotFoundError(f"Default parameters file not found: {default_prm_path}")
        
        logger.info(f"Loading hydration parameters from: {default_prm_path}")
        
        # Check if portland_cement_standard already exists
        with database_service.get_read_only_session() as session:
            existing_params = session.query(HydrationParameters).filter_by(
                name="portland_cement_standard"
            ).first()
            
            if existing_params:
                logger.info("portland_cement_standard parameters already exist. Skipping initialization.")
                return existing_params
        
        # Create new parameter set from .prm file
        logger.info("Creating portland_cement_standard parameter set...")
        hydration_params = HydrationParameters.create_from_prm_file(
            name="portland_cement_standard",
            filepath=str(default_prm_path),
            description="Default Portland cement hydration parameters for VCCTL simulations"
        )
        
        # Save to database
        with database_service.get_session() as session:
            session.add(hydration_params)
            session.commit()
            logger.info(f"Saved hydration parameters: {hydration_params.parameter_count} parameters loaded")
        
        logger.info("✅ Hydration parameters initialization complete")
        return hydration_params
        
    except Exception as e:
        logger.error(f"Failed to initialize hydration parameters: {e}")
        raise


def main():
    """Main entry point for standalone initialization."""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger('VCCTL.HydrationInit')
    logger.info("Starting hydration parameters initialization...")
    
    try:
        # Initialize parameters
        params = initialize_hydration_parameters()
        logger.info(f"Successfully initialized hydration parameters: {params.name}")
        
    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
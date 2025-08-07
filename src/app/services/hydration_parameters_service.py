#!/usr/bin/env python3
"""
Hydration Parameters Service for VCCTL

Handles hydration parameter operations including database queries
and file export to Operations directories.
"""

import os
import logging
from pathlib import Path
from typing import Optional, List

from app.models.hydration_parameters import HydrationParameters
from app.database.service import DatabaseService


class HydrationParametersService:
    """Service for managing hydration parameters."""
    
    def __init__(self, database_service: DatabaseService):
        """Initialize the hydration parameters service."""
        self.database_service = database_service
        self.logger = logging.getLogger('VCCTL.HydrationParametersService')
    
    def get_parameter_set(self, name: str) -> Optional[HydrationParameters]:
        """
        Get a parameter set by name.
        
        Args:
            name: Name of the parameter set
            
        Returns:
            HydrationParameters instance or None if not found
        """
        try:
            with self.database_service.get_read_only_session() as session:
                return session.query(HydrationParameters).filter_by(name=name).first()
        except Exception as e:
            self.logger.error(f"Failed to get parameter set '{name}': {e}")
            raise
    
    def get_all_parameter_sets(self) -> List[HydrationParameters]:
        """
        Get all available parameter sets.
        
        Returns:
            List of all HydrationParameters instances
        """
        try:
            with self.database_service.get_read_only_session() as session:
                return session.query(HydrationParameters).all()
        except Exception as e:
            self.logger.error(f"Failed to get all parameter sets: {e}")
            raise
    
    def create_parameter_set(self, name: str, prm_file_path: str, description: str = None) -> HydrationParameters:
        """
        Create a new parameter set from a .prm file.
        
        Args:
            name: Name for the parameter set
            prm_file_path: Path to the .prm file to read
            description: Optional description
            
        Returns:
            Created HydrationParameters instance
        """
        try:
            # Create parameter set from file
            hydration_params = HydrationParameters.create_from_prm_file(
                name=name,
                filepath=prm_file_path,
                description=description
            )
            
            # Save to database
            with self.database_service.get_session() as session:
                session.add(hydration_params)
                # Commit is handled automatically by get_session()
                self.logger.info(f"Created parameter set '{name}' with {hydration_params.parameter_count} parameters")
            
            return hydration_params
            
        except Exception as e:
            self.logger.error(f"Failed to create parameter set '{name}': {e}")
            raise
    
    def export_to_operation_directory(self, operation_name: str, parameter_set_name: str = "portland_cement_standard") -> str:
        """
        Export parameter set to an operation directory.
        
        Args:
            operation_name: Name of the operation
            parameter_set_name: Name of the parameter set to export
            
        Returns:
            Path to the created parameter file
        """
        try:
            # Get the parameter set
            params = self.get_parameter_set(parameter_set_name)
            if not params:
                raise ValueError(f"Parameter set '{parameter_set_name}' not found")
            
            # Create operation directory if it doesn't exist
            project_root = Path(__file__).parent.parent.parent.parent
            operations_dir = project_root / "Operations" / operation_name
            operations_dir.mkdir(parents=True, exist_ok=True)
            
            # Create parameter file path
            param_filename = f"{operation_name}_hydration_parameters.prm"
            param_filepath = operations_dir / param_filename
            
            self.logger.info(f"Exporting parameters to: {param_filepath}")
            
            # Export parameters to file
            params.export_to_file(str(param_filepath))
            
            self.logger.info(f"Successfully exported {params.parameter_count} parameters to {param_filepath}")
            return str(param_filepath)
            
        except Exception as e:
            self.logger.error(f"Failed to export parameters for operation '{operation_name}': {e}")
            raise
    
    def update_parameter_set(self, name: str, new_parameters: dict) -> HydrationParameters:
        """
        Update an existing parameter set.
        
        Args:
            name: Name of the parameter set to update
            new_parameters: Dictionary of parameters to update
            
        Returns:
            Updated HydrationParameters instance
        """
        try:
            with self.database_service.get_session() as session:
                params = session.query(HydrationParameters).filter_by(name=name).first()
                if not params:
                    raise ValueError(f"Parameter set '{name}' not found")
                
                params.update_parameters(new_parameters)
                # Commit is handled automatically by get_session()
                self.logger.info(f"Updated parameter set '{name}'")
                
                return params
                
        except Exception as e:
            self.logger.error(f"Failed to update parameter set '{name}': {e}")
            raise
    
    def delete_parameter_set(self, name: str) -> bool:
        """
        Delete a parameter set.
        
        Args:
            name: Name of the parameter set to delete
            
        Returns:
            True if deleted, False if not found
        """
        try:
            with self.database_service.get_session() as session:
                params = session.query(HydrationParameters).filter_by(name=name).first()
                if not params:
                    return False
                
                session.delete(params)
                # Commit is handled automatically by get_session()
                self.logger.info(f"Deleted parameter set '{name}'")
                
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to delete parameter set '{name}': {e}")
            raise
    
    def get_parameter_count(self, name: str) -> int:
        """
        Get the number of parameters in a parameter set.
        
        Args:
            name: Name of the parameter set
            
        Returns:
            Number of parameters
        """
        params = self.get_parameter_set(name)
        return params.parameter_count if params else 0
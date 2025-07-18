#!/usr/bin/env python3
"""
Cement Service for VCCTL

Provides business logic for cement material management.
Converted from Java Spring service to Python.
"""

import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.service import DatabaseService
from app.models.cement import Cement, CementCreate, CementUpdate, CementResponse
from app.services.base_service import BaseService, ServiceError, NotFoundError, AlreadyExistsError


class CementService(BaseService[Cement, CementCreate, CementUpdate]):
    """
    Service for managing cement materials.
    
    Provides CRUD operations, validation, and file operations
    for cement materials in the VCCTL system.
    """
    
    def __init__(self, db_service: DatabaseService):
        super().__init__(Cement, db_service)
        self.logger = logging.getLogger('VCCTL.CementService')
        self.default_alkali_file = 'lowalkali'
    
    def get_all(self) -> List[Cement]:
        """Get all cement materials."""
        try:
            with self.db_service.get_read_only_session() as session:
                # Order by id (new primary key) instead of name
                return session.query(Cement).order_by(Cement.id).all()
        except Exception as e:
            self.logger.error(f"Failed to get all cements: {e}")
            raise ServiceError(f"Failed to retrieve cements: {e}")
    
    def get_by_name(self, name: str) -> Optional[Cement]:
        """Get cement by name."""
        try:
            with self.db_service.get_read_only_session() as session:
                return session.query(Cement).filter_by(name=name).first()
        except Exception as e:
            self.logger.error(f"Failed to get cement {name}: {e}")
            raise ServiceError(f"Failed to retrieve cement: {e}")
    
    def create(self, cement_data: CementCreate) -> Cement:
        """Create a new cement material."""
        try:
            with self.db_service.get_session() as session:
                # Check if cement already exists
                existing = session.query(Cement).filter_by(name=cement_data.name).first()
                if existing:
                    raise AlreadyExistsError(f"Cement '{cement_data.name}' already exists")
                
                # Create cement with defaults
                cement_dict = cement_data.dict(exclude_unset=True)
                
                # Set default alkali file if not provided
                if not cement_dict.get('alkali_file'):
                    cement_dict['alkali_file'] = self.default_alkali_file
                
                cement = Cement(**cement_dict)
                
                # Validate cement properties
                self._validate_cement(cement)
                
                session.add(cement)
                session.flush()  # Flush to get any database errors
                
                self.logger.info(f"Created cement: {cement.name}")
                return cement
                
        except AlreadyExistsError:
            raise
        except IntegrityError as e:
            self.logger.error(f"Database integrity error creating cement: {e}")
            raise ServiceError(f"Cement creation failed: invalid data")
        except Exception as e:
            self.logger.error(f"Failed to create cement: {e}")
            raise ServiceError(f"Failed to create cement: {e}")
    
    def update(self, cement_id: int, cement_data: CementUpdate) -> Cement:
        """Update an existing cement material."""
        try:
            with self.db_service.get_session() as session:
                cement = session.query(Cement).filter_by(id=cement_id).first()
                if not cement:
                    raise NotFoundError(f"Cement with ID '{cement_id}' not found")
                
                # Update fields
                update_dict = cement_data.dict(exclude_unset=True)
                for field, value in update_dict.items():
                    setattr(cement, field, value)
                
                # Validate updated cement
                self._validate_cement(cement)
                
                session.flush()  # Flush to get any database errors
                
                self.logger.info(f"Updated cement: {cement.name}")
                return cement
                
        except NotFoundError:
            raise
        except IntegrityError as e:
            self.logger.error(f"Database integrity error updating cement: {e}")
            raise ServiceError(f"Cement update failed: invalid data")
        except Exception as e:
            self.logger.error(f"Failed to update cement {cement_id}: {e}")
            raise ServiceError(f"Failed to update cement: {e}")
    
    def delete(self, name: str) -> bool:
        """Delete a cement material."""
        try:
            with self.db_service.get_session() as session:
                cement = session.query(Cement).filter_by(name=name).first()
                if not cement:
                    raise NotFoundError(f"Cement '{name}' not found")
                
                session.delete(cement)
                
                self.logger.info(f"Deleted cement: {name}")
                return True
                
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to delete cement {name}: {e}")
            raise ServiceError(f"Failed to delete cement: {e}")
    
    def save_as(self, original_name: str, new_name: str) -> Cement:
        """
        Save an existing cement with a new name (copy operation).
        
        Args:
            original_name: Name of the cement to copy
            new_name: New name for the copy
            
        Returns:
            The newly created cement copy
        """
        try:
            with self.db_service.get_session() as session:
                # Get original cement
                original = session.query(Cement).filter_by(name=original_name).first()
                if not original:
                    raise NotFoundError(f"Cement '{original_name}' not found")
                
                # Check if new name already exists
                existing = session.query(Cement).filter_by(name=new_name).first()
                if existing:
                    raise AlreadyExistsError(f"Cement '{new_name}' already exists")
                
                # Create copy
                cement_dict = original.to_dict()
                cement_dict['name'] = new_name
                cement_dict.pop('id', None)  # Remove auto-generated fields
                cement_dict.pop('created_at', None)
                cement_dict.pop('updated_at', None)
                
                new_cement = Cement(**cement_dict)
                session.add(new_cement)
                session.flush()
                
                self.logger.info(f"Copied cement '{original_name}' to '{new_name}'")
                return new_cement
                
        except (NotFoundError, AlreadyExistsError):
            raise
        except Exception as e:
            self.logger.error(f"Failed to save cement as {new_name}: {e}")
            raise ServiceError(f"Failed to copy cement: {e}")
    
    def write_correlation_files(self, cement_name: str, operation_directory: Path) -> List[Path]:
        """
        Write cement correlation files for simulation operations.
        
        Args:
            cement_name: Name of the cement
            operation_directory: Directory to write files to
            
        Returns:
            List of file paths that were written
        """
        try:
            cement = self.get_by_name(cement_name)
            if not cement:
                raise NotFoundError(f"Cement '{cement_name}' not found")
            
            return self._write_files_from_cement(cement, operation_directory)
            
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to write correlation files for {cement_name}: {e}")
            raise ServiceError(f"Failed to write correlation files: {e}")
    
    def _write_files_from_cement(self, cement: Cement, operation_directory: Path) -> List[Path]:
        """Write binary data files from cement to operation directory."""
        operation_directory.mkdir(parents=True, exist_ok=True)
        written_files = []
        
        # Define file mappings (file_suffix -> binary_data_attribute)
        file_mappings = {
            '.sil': 'sil',
            '.c3s': 'c3s',
            '.c4f': 'c4f',
            '.c3a': 'c3a',
            '.n2o': 'n2o',
            '.k2o': 'k2o',
            '.alu': 'alu'
        }
        
        for suffix, attr_name in file_mappings.items():
            binary_data = getattr(cement, attr_name)
            if binary_data:
                file_path = operation_directory / f"{cement.name}{suffix}"
                try:
                    with open(file_path, 'wb') as f:
                        f.write(binary_data)
                    written_files.append(file_path)
                    self.logger.debug(f"Wrote {file_path}")
                except Exception as e:
                    self.logger.warning(f"Failed to write {file_path}: {e}")
        
        self.logger.info(f"Wrote {len(written_files)} correlation files for cement {cement.name}")
        return written_files
    
    def _validate_cement(self, cement: Cement) -> None:
        """Validate cement properties."""
        # Validate gypsum fractions
        if not cement.validate_gypsum_fractions():
            raise ServiceError("Invalid gypsum fractions: values must be between 0 and 1, and total cannot exceed 1.0")
        
        # Validate required fields
        if not cement.name or not cement.name.strip():
            raise ServiceError("Cement name is required")
        
        # Additional business logic validation can be added here
    
    def get_cements_with_phase_data(self) -> List[Cement]:
        """Get all cements that have phase composition data."""
        try:
            with self.db_service.get_read_only_session() as session:
                return [cement for cement in session.query(Cement).all() 
                       if cement.has_phase_data]
        except Exception as e:
            self.logger.error(f"Failed to get cements with phase data: {e}")
            raise ServiceError(f"Failed to retrieve cements with phase data: {e}")
    
    def get_cements_with_gypsum_data(self) -> List[Cement]:
        """Get all cements that have gypsum fraction data."""
        try:
            with self.db_service.get_read_only_session() as session:
                return [cement for cement in session.query(Cement).all() 
                       if cement.has_gypsum_data]
        except Exception as e:
            self.logger.error(f"Failed to get cements with gypsum data: {e}")
            raise ServiceError(f"Failed to retrieve cements with gypsum data: {e}")
    
    def search_cements(self, query: str, limit: Optional[int] = None) -> List[Cement]:
        """
        Search cements by name or PSD.
        
        Args:
            query: Search query string
            limit: Maximum number of results to return
            
        Returns:
            List of matching cements
        """
        try:
            with self.db_service.get_read_only_session() as session:
                search_query = session.query(Cement).filter(
                    (Cement.name.contains(query)) | 
                    (Cement.psd.contains(query) if query else False)
                ).order_by(Cement.name)
                
                if limit:
                    search_query = search_query.limit(limit)
                
                return search_query.all()
                
        except Exception as e:
            self.logger.error(f"Failed to search cements: {e}")
            raise ServiceError(f"Failed to search cements: {e}")
    
    def get_cement_statistics(self) -> Dict[str, Any]:
        """Get statistics about cement materials."""
        try:
            with self.db_service.get_read_only_session() as session:
                total_count = session.query(Cement).count()
                with_phase_data = len([c for c in session.query(Cement).all() if c.has_phase_data])
                with_gypsum_data = len([c for c in session.query(Cement).all() if c.has_gypsum_data])
                
                # Get unique PSD types
                unique_psds = session.query(Cement.psd).distinct().filter(Cement.psd.isnot(None)).count()
                
                # Get unique alkali files
                unique_alkali = session.query(Cement.alkali_file).distinct().filter(Cement.alkali_file.isnot(None)).count()
                
                return {
                    'total_cements': total_count,
                    'with_phase_data': with_phase_data,
                    'with_gypsum_data': with_gypsum_data,
                    'unique_psd_types': unique_psds,
                    'unique_alkali_files': unique_alkali,
                    'percentage_with_phase_data': (with_phase_data / total_count * 100) if total_count > 0 else 0,
                    'percentage_with_gypsum_data': (with_gypsum_data / total_count * 100) if total_count > 0 else 0
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get cement statistics: {e}")
            raise ServiceError(f"Failed to get cement statistics: {e}")
#!/usr/bin/env python3
"""
PSD Data Service for VCCTL

Service layer for managing Particle Size Distribution data.
Provides CRUD operations and validation for the unified PSD model.
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.psd_data import PSDData, PSDDataCreate, PSDDataUpdate, PSDDataResponse
from app.services.base_service import BaseService


class PSDDataService(BaseService):
    """Service for managing PSD data operations."""
    
    def __init__(self, database_service):
        """Initialize PSD data service."""
        super().__init__(PSDData, database_service)
        self.database_service = database_service
    
    def _to_response(self, db_psd: PSDData) -> PSDDataResponse:
        """Convert database model to response model."""
        response_dict = {
            'id': db_psd.id,
            'psd_reference': db_psd.psd_reference,
            'psd_custom_points': db_psd.psd_custom_points,
            'psd_mode': db_psd.psd_mode,
            'psd_d50': db_psd.psd_d50,
            'psd_n': db_psd.psd_n,
            'psd_dmax': db_psd.psd_dmax,
            'psd_median': db_psd.psd_median,
            'psd_spread': db_psd.psd_spread,
            'psd_exponent': db_psd.psd_exponent,
            'diameter_percentile_10': db_psd.diameter_percentile_10,
            'diameter_percentile_50': db_psd.diameter_percentile_50,
            'diameter_percentile_90': db_psd.diameter_percentile_90,
            'created_at': str(db_psd.created_at) if db_psd.created_at else '',
            'updated_at': str(db_psd.updated_at) if db_psd.updated_at else ''
        }
        return PSDDataResponse(**response_dict)
    
    def create_psd_data(self, psd_data: PSDDataCreate) -> Optional[PSDDataResponse]:
        """Create new PSD data record."""
        try:
            with self.database_service.get_session() as session:
                # Create new PSD data instance
                db_psd = PSDData(**psd_data.model_dump())
                
                # Validate consistency before saving
                if not db_psd.validate_consistency():
                    self.logger.warning(f"PSD data consistency validation failed for mode: {db_psd.psd_mode}")
                
                session.add(db_psd)
                session.commit()
                session.refresh(db_psd)
                
                self.logger.info(f"Created PSD data: {db_psd.id} ({db_psd.psd_mode})")
                return self._to_response(db_psd)
                
        except SQLAlchemyError as e:
            self.logger.error(f"Database error creating PSD data: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error creating PSD data: {e}")
            return None
    
    def get_psd_data(self, psd_id: int) -> Optional[PSDDataResponse]:
        """Get PSD data by ID."""
        try:
            with self.database_service.get_read_only_session() as session:
                db_psd = session.query(PSDData).filter(PSDData.id == psd_id).first()
                
                if db_psd:
                    return self._to_response(db_psd)
                return None
                
        except SQLAlchemyError as e:
            self.logger.error(f"Database error fetching PSD data {psd_id}: {e}")
            return None
    
    def update_psd_data(self, psd_id: int, psd_update: PSDDataUpdate) -> Optional[PSDDataResponse]:
        """Update existing PSD data."""
        try:
            with self.database_service.get_session() as session:
                db_psd = session.query(PSDData).filter(PSDData.id == psd_id).first()
                
                if not db_psd:
                    self.logger.warning(f"PSD data not found: {psd_id}")
                    return None
                
                # Update fields
                update_data = psd_update.model_dump(exclude_unset=True)
                for field, value in update_data.items():
                    setattr(db_psd, field, value)
                
                # Validate consistency after update
                if not db_psd.validate_consistency():
                    self.logger.warning(f"PSD data consistency validation failed after update: {psd_id}")
                
                session.commit()
                session.refresh(db_psd)
                
                self.logger.info(f"Updated PSD data: {psd_id}")
                return self._to_response(db_psd)
                
        except SQLAlchemyError as e:
            self.logger.error(f"Database error updating PSD data {psd_id}: {e}")
            return None
    
    def delete_psd_data(self, psd_id: int) -> bool:
        """Delete PSD data by ID."""
        try:
            with self.database_service.get_session() as session:
                db_psd = session.query(PSDData).filter(PSDData.id == psd_id).first()
                
                if not db_psd:
                    self.logger.warning(f"PSD data not found for deletion: {psd_id}")
                    return False
                
                session.delete(db_psd)
                session.commit()
                
                self.logger.info(f"Deleted PSD data: {psd_id}")
                return True
                
        except SQLAlchemyError as e:
            self.logger.error(f"Database error deleting PSD data {psd_id}: {e}")
            return False
    
    def create_default_psd_for_material(self, material_type: str) -> Optional[PSDDataResponse]:
        """Create default PSD data for a specific material type."""
        # Default PSD configurations by material type
        defaults = {
            'cement': PSDDataCreate(
                psd_reference='cement_default',
                psd_mode='log_normal',
                psd_median=10.0,
                psd_spread=2.0
            ),
            'filler': PSDDataCreate(
                psd_reference='filler_default',
                psd_mode='log_normal',
                psd_median=5.0,
                psd_spread=2.0,
                diameter_percentile_10=1.0,
                diameter_percentile_50=5.0,
                diameter_percentile_90=20.0
            ),
            'fly_ash': PSDDataCreate(
                psd_reference='fly_ash_default',
                psd_mode='rosin_rammler',
                psd_d50=15.0,
                psd_n=1.5,
                psd_dmax=100.0
            ),
            'limestone': PSDDataCreate(
                psd_reference='limestone_default',
                psd_mode='log_normal',
                psd_median=5.0,
                psd_spread=2.0
            ),
            'silica_fume': PSDDataCreate(
                psd_reference='silica_fume_default',
                psd_mode='log_normal',
                psd_median=0.5,
                psd_spread=1.5,
                diameter_percentile_10=0.1,
                diameter_percentile_50=0.5,
                diameter_percentile_90=2.0
            ),
            'slag': PSDDataCreate(
                psd_reference='slag_default',
                psd_mode='rosin_rammler',
                psd_d50=15.0,
                psd_n=1.4,
                psd_dmax=75.0
            )
        }
        
        psd_config = defaults.get(material_type, defaults['cement'])  # Default to cement if unknown
        return self.create_psd_data(psd_config)
    
    def copy_psd_data(self, source_psd_id: int) -> Optional[PSDDataResponse]:
        """Create a copy of existing PSD data."""
        source_psd = self.get_psd_data(source_psd_id)
        if not source_psd:
            return None
        
        # Create new PSD data excluding id and timestamps
        psd_dict = source_psd.model_dump(exclude={'id', 'created_at', 'updated_at'})
        psd_create = PSDDataCreate(**psd_dict)
        
        return self.create_psd_data(psd_create)
    
    def get_psd_summary(self, psd_id: int) -> str:
        """Get a human-readable summary of PSD configuration."""
        try:
            with self.database_service.get_read_only_session() as session:
                db_psd = session.query(PSDData).filter(PSDData.id == psd_id).first()
                
                if db_psd:
                    return db_psd.get_distribution_summary()
                return "PSD not found"
                
        except Exception as e:
            self.logger.error(f"Error getting PSD summary for {psd_id}: {e}")
            return "Error loading PSD"
    
    # Implement abstract methods from BaseService
    def get_all(self) -> List[PSDData]:
        """Get all PSD data records."""
        try:
            with self.database_service.get_read_only_session() as session:
                return session.query(PSDData).all()
        except Exception as e:
            self.logger.error(f"Error fetching all PSD data: {e}")
            return []
    
    def get_by_name(self, name: str) -> Optional[PSDData]:
        """Get PSD data by reference name."""
        try:
            with self.database_service.get_read_only_session() as session:
                return session.query(PSDData).filter(
                    PSDData.psd_reference == name
                ).first()
        except Exception as e:
            self.logger.error(f"Error fetching PSD data by name {name}: {e}")
            return None
    
    def create(self, create_data: PSDDataCreate) -> Optional[PSDData]:
        """Create a new PSD data record (alias for create_psd_data)."""
        return self.create_psd_data(create_data)
    
    def update(self, name: str, update_data: PSDDataUpdate) -> Optional[PSDData]:
        """Update PSD data by reference name."""
        try:
            with self.database_service.get_session() as session:
                db_psd = session.query(PSDData).filter(
                    PSDData.psd_reference == name
                ).first()
                
                if not db_psd:
                    self.logger.warning(f"PSD data not found by name: {name}")
                    return None
                
                # Update fields
                update_dict = update_data.model_dump(exclude_unset=True)
                for field, value in update_dict.items():
                    setattr(db_psd, field, value)
                
                session.commit()
                session.refresh(db_psd)
                return db_psd
                
        except Exception as e:
            self.logger.error(f"Error updating PSD data by name {name}: {e}")
            return None
    
    def delete(self, name: str) -> bool:
        """Delete PSD data by reference name."""
        try:
            with self.database_service.get_session() as session:
                db_psd = session.query(PSDData).filter(
                    PSDData.psd_reference == name
                ).first()
                
                if not db_psd:
                    self.logger.warning(f"PSD data not found for deletion by name: {name}")
                    return False
                
                session.delete(db_psd)
                session.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"Error deleting PSD data by name {name}: {e}")
            return False
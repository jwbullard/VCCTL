#!/usr/bin/env python3
"""
Fly Ash Service for VCCTL

Provides business logic for fly ash material management.
Converted from Java Spring service to Python.
"""

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from app.database.service import DatabaseService
from app.models.fly_ash import FlyAsh, FlyAshCreate, FlyAshUpdate, FlyAshResponse
from app.services.base_service import BaseService, ServiceError, NotFoundError, AlreadyExistsError, ValidationError


class FlyAshService(BaseService[FlyAsh, FlyAshCreate, FlyAshUpdate]):
    """
    Service for managing fly ash materials.
    
    Provides CRUD operations, validation, and specialized calculations
    for fly ash materials in the VCCTL system.
    """
    
    def __init__(self, db_service: DatabaseService):
        super().__init__(FlyAsh, db_service)
        self.logger = logging.getLogger('VCCTL.FlyAshService')
        self.default_psd = 'cement141'
        self.default_specific_gravity = 2.77
    
    def get_all(self) -> List[FlyAsh]:
        """Get all fly ash materials with eagerly loaded PSD relationships."""
        try:
            with self.db_service.get_read_only_session() as session:
                return session.query(FlyAsh).options(joinedload(FlyAsh.psd_data)).order_by(FlyAsh.name).all()
        except Exception as e:
            self.logger.error(f"Failed to get all fly ash materials: {e}")
            raise ServiceError(f"Failed to retrieve fly ash materials: {e}")
    
    def get_by_name(self, name: str) -> Optional[FlyAsh]:
        """Get fly ash by name with eagerly loaded PSD relationship."""
        try:
            with self.db_service.get_read_only_session() as session:
                return session.query(FlyAsh).options(joinedload(FlyAsh.psd_data)).filter_by(name=name).first()
        except Exception as e:
            self.logger.error(f"Failed to get fly ash {name}: {e}")
            raise ServiceError(f"Failed to retrieve fly ash: {e}")
    
    def create(self, fly_ash_data: FlyAshCreate) -> FlyAsh:
        """Create a new fly ash material."""
        try:
            # Validate data
            if not fly_ash_data.name or not fly_ash_data.name.strip():
                raise ValidationError("Fly ash name is required")
            
            # Check if already exists
            existing = self.get_by_name(fly_ash_data.name)
            if existing:
                raise AlreadyExistsError(f"Fly ash '{fly_ash_data.name}' already exists")
            
            # Create new fly ash
            with self.db_service.get_session() as session:
                # Extract PSD fields from create data if present
                create_dict = fly_ash_data.model_dump(exclude_unset=True)
                psd_fields = ['psd_mode', 'psd_d50', 'psd_n', 'psd_dmax', 'psd_median', 
                             'psd_spread', 'psd_exponent', 'psd_custom_points']
                psd_data = {}
                
                # Separate PSD fields from fly ash fields
                for field in list(create_dict.keys()):
                    if field in psd_fields:
                        psd_data[field] = create_dict.pop(field)
                
                # Create fly ash
                fly_ash = FlyAsh(**create_dict)
                
                # Handle PSD data if any PSD fields were provided
                if psd_data:
                    from app.models.psd_data import PSDData
                    new_psd = PSDData(**psd_data)
                    session.add(new_psd)
                    session.flush()  # Get the ID
                    fly_ash.psd_data = new_psd
                    fly_ash.psd_data_id = new_psd.id
                
                session.add(fly_ash)
                session.commit()
                session.refresh(fly_ash)
                
                self.logger.info(f"Created fly ash: {fly_ash.name}")
                return fly_ash
                
        except (AlreadyExistsError, ValidationError):
            raise
        except IntegrityError as e:
            self.logger.error(f"Database integrity error creating fly ash: {e}")
            raise AlreadyExistsError(f"Fly ash '{fly_ash_data.name}' already exists")
        except Exception as e:
            self.logger.error(f"Failed to create fly ash: {e}")
            raise ServiceError(f"Failed to create fly ash: {e}")
    
    def update(self, fly_ash_id: int, update_data: FlyAshUpdate) -> FlyAsh:
        """Update an existing fly ash material."""
        try:
            with self.db_service.get_session() as session:
                fly_ash = session.query(FlyAsh).options(joinedload(FlyAsh.psd_data)).filter_by(id=fly_ash_id).first()
                
                if not fly_ash:
                    raise NotFoundError(f"Fly ash with ID '{fly_ash_id}' not found")
                
                # Extract PSD fields from update data if present
                update_dict = update_data.model_dump(exclude_unset=True)
                psd_fields = ['psd_mode', 'psd_d50', 'psd_n', 'psd_dmax', 'psd_median', 
                             'psd_spread', 'psd_exponent', 'psd_custom_points']
                psd_data = {}
                
                # Separate PSD fields from fly ash fields
                for field in list(update_dict.keys()):
                    if field in psd_fields:
                        psd_data[field] = update_dict.pop(field)
                
                # Handle PSD data if any PSD fields were provided
                if psd_data:
                    from app.models.psd_data import PSDData
                    
                    if fly_ash.psd_data_id and fly_ash.psd_data:
                        # Update existing PSD data
                        for field, value in psd_data.items():
                            setattr(fly_ash.psd_data, field, value)
                    else:
                        # Create new PSD data
                        new_psd = PSDData(**psd_data)
                        session.add(new_psd)
                        session.flush()  # Get the ID
                        fly_ash.psd_data = new_psd
                        fly_ash.psd_data_id = new_psd.id
                
                # Update remaining fly ash fields
                for field, value in update_dict.items():
                    if hasattr(fly_ash, field):
                        setattr(fly_ash, field, value)
                
                session.commit()
                session.refresh(fly_ash)
                
                self.logger.info(f"Updated fly ash: {fly_ash.name}")
                return fly_ash
                
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to update fly ash {fly_ash_id}: {e}")
            raise ServiceError(f"Failed to update fly ash: {e}")
    
    def delete(self, name: str) -> bool:
        """Delete a fly ash material."""
        try:
            with self.db_service.get_session() as session:
                fly_ash = session.query(FlyAsh).filter_by(name=name).first()
                
                if not fly_ash:
                    raise NotFoundError(f"Fly ash '{name}' not found")
                
                session.delete(fly_ash)
                session.commit()
                
                self.logger.info(f"Deleted fly ash: {name}")
                return True
                
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to delete fly ash {name}: {e}")
            raise ServiceError(f"Failed to delete fly ash: {e}")
    
    def duplicate(self, source_name: str, new_name: str, description: Optional[str] = None) -> FlyAsh:
        """Duplicate an existing fly ash with a new name."""
        try:
            # Get source fly ash
            source = self.get_by_name(source_name)
            if not source:
                raise NotFoundError(f"Source fly ash '{source_name}' not found")
            
            # Check if new name already exists
            if self.get_by_name(new_name):
                raise AlreadyExistsError(f"Fly ash '{new_name}' already exists")
            
            # Create duplicate
            create_data = FlyAshCreate(
                name=new_name,
                specific_gravity=source.specific_gravity,
                distribute_phases_by=source.distribute_phases_by,
                aluminosilicate_glass_fraction=source.aluminosilicate_glass_fraction,
                calcium_aluminum_disilicate_fraction=source.calcium_aluminum_disilicate_fraction,
                tricalcium_aluminate_fraction=source.tricalcium_aluminate_fraction,
                calcium_chloride_fraction=source.calcium_chloride_fraction,
                silica_fraction=source.silica_fraction,
                anhydrate_fraction=source.anhydrate_fraction,
                activation_energy=source.activation_energy,
                description=description or f"Copy of {source.name}"
            )
            
            return self.create(create_data)
            
        except (NotFoundError, AlreadyExistsError):
            raise
        except Exception as e:
            self.logger.error(f"Failed to duplicate fly ash {source_name}: {e}")
            raise ServiceError(f"Failed to duplicate fly ash: {e}")
    
    def validate_composition(self, fly_ash: FlyAsh) -> Dict[str, Any]:
        """Validate fly ash composition and return analysis."""
        try:
            analysis = {
                'is_valid': True,
                'warnings': [],
                'errors': [],
                'total_phase_fraction': fly_ash.total_phase_fraction,
                'has_complete_data': fly_ash.has_complete_phase_data
            }
            
            # Check phase fractions
            if not fly_ash.has_complete_phase_data:
                analysis['warnings'].append("Incomplete phase fraction data")
            elif fly_ash.total_phase_fraction and fly_ash.total_phase_fraction > 1.0:
                analysis['errors'].append("Total phase fractions exceed 1.0")
                analysis['is_valid'] = False
            
            # Check specific gravity
            if fly_ash.specific_gravity is None:
                analysis['warnings'].append("No specific gravity data")
            elif fly_ash.specific_gravity <= 0:
                analysis['errors'].append("Specific gravity must be positive")
                analysis['is_valid'] = False
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Failed to validate fly ash composition: {e}")
            raise ServiceError(f"Failed to validate composition: {e}")
    
    def get_names(self) -> List[str]:
        """Get list of all fly ash names."""
        try:
            with self.db_service.get_read_only_session() as session:
                return [name[0] for name in session.query(FlyAsh.name).order_by(FlyAsh.name).all()]
        except Exception as e:
            self.logger.error(f"Failed to get fly ash names: {e}")
            raise ServiceError(f"Failed to retrieve fly ash names: {e}")
    
    def search(self, query: str) -> List[FlyAsh]:
        """Search fly ash materials by name or description."""
        try:
            with self.db_service.get_read_only_session() as session:
                search_pattern = f"%{query}%"
                return session.query(FlyAsh).filter(
                    (FlyAsh.name.ilike(search_pattern)) |
                    (FlyAsh.description.ilike(search_pattern))
                ).order_by(FlyAsh.name).all()
        except Exception as e:
            self.logger.error(f"Failed to search fly ash materials: {e}")
            raise ServiceError(f"Failed to search fly ash materials: {e}")
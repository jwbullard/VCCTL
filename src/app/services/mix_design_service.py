#!/usr/bin/env python3
"""
Mix Design Service for VCCTL

Provides business logic for mix design management and CRUD operations.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from datetime import datetime

from app.database.service import DatabaseService
from app.models.mix_design import MixDesign, MixDesignCreate, MixDesignUpdate, MixDesignResponse, MixDesignComponentData, MixDesignPropertiesData
from app.services.base_service import BaseService, ServiceError, NotFoundError, AlreadyExistsError, ValidationError


class MixDesignService(BaseService[MixDesign, MixDesignCreate, MixDesignUpdate]):
    """
    Service for managing mix designs.
    
    Provides CRUD operations, validation, and business logic
    for concrete mix designs in the VCCTL system.
    """
    
    def __init__(self, db_service: DatabaseService):
        super().__init__(MixDesign, db_service)
        self.logger = logging.getLogger('VCCTL.MixDesignService')
    
    def get_all(self) -> List[MixDesign]:
        """Get all mix designs ordered by creation date (newest first)."""
        try:
            with self.db_service.get_read_only_session() as session:
                return session.query(MixDesign).order_by(MixDesign.created_at.desc()).all()
        except Exception as e:
            self.logger.error(f"Failed to get all mix designs: {e}")
            raise ServiceError(f"Failed to retrieve mix designs: {e}")
    
    def get_templates(self) -> List[MixDesign]:
        """Get all template mix designs."""
        try:
            with self.db_service.get_read_only_session() as session:
                return session.query(MixDesign).filter(
                    MixDesign.is_template == True
                ).order_by(MixDesign.name).all()
        except Exception as e:
            self.logger.error(f"Failed to get template mix designs: {e}")
            raise ServiceError(f"Failed to retrieve template mix designs: {e}")
    
    def get_by_id(self, mix_design_id: int) -> Optional[MixDesign]:
        """Get a mix design by ID."""
        try:
            with self.db_service.get_read_only_session() as session:
                return session.query(MixDesign).filter(MixDesign.id == mix_design_id).first()
        except Exception as e:
            self.logger.error(f"Failed to get mix design by ID {mix_design_id}: {e}")
            raise ServiceError(f"Failed to retrieve mix design: {e}")
    
    def get_by_name(self, name: str) -> Optional[MixDesign]:
        """Get a mix design by name."""
        try:
            with self.db_service.get_read_only_session() as session:
                return session.query(MixDesign).filter(MixDesign.name == name).first()
        except Exception as e:
            self.logger.error(f"Failed to get mix design by name '{name}': {e}")
            raise ServiceError(f"Failed to retrieve mix design: {e}")
    
    def create(self, mix_design_data: MixDesignCreate) -> MixDesign:
        """Create a new mix design."""
        try:
            # Convert components and properties to JSON format
            components_json = [comp.model_dump() for comp in mix_design_data.components]
            properties_json = mix_design_data.calculated_properties.model_dump() if mix_design_data.calculated_properties else {}
            
            # Create database object
            mix_design = MixDesign(
                name=mix_design_data.name,
                description=mix_design_data.description,
                water_binder_ratio=mix_design_data.water_binder_ratio,
                total_water_content=mix_design_data.total_water_content,
                air_content=mix_design_data.air_content,
                water_volume_fraction=mix_design_data.water_volume_fraction,
                air_volume_fraction=mix_design_data.air_volume_fraction,
                system_size=mix_design_data.system_size,
                random_seed=mix_design_data.random_seed,
                cement_shape_set=mix_design_data.cement_shape_set,
                aggregate_shape_set=mix_design_data.aggregate_shape_set,
                components=components_json,
                calculated_properties=properties_json,
                notes=mix_design_data.notes,
                is_template=mix_design_data.is_template,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            with self.db_service.get_session() as session:
                session.add(mix_design)
                session.commit()
                session.refresh(mix_design)
                
            self.logger.info(f"Created mix design: {mix_design.name}")
            return mix_design
            
        except IntegrityError as e:
            self.logger.error(f"Mix design name already exists: {mix_design_data.name}")
            raise AlreadyExistsError(f"Mix design '{mix_design_data.name}' already exists")
        except Exception as e:
            self.logger.error(f"Failed to create mix design: {e}")
            raise ServiceError(f"Failed to create mix design: {e}")
    
    
    def duplicate(self, mix_design_id: int, new_name: str, make_template: bool = False) -> MixDesign:
        """Duplicate an existing mix design with a new name."""
        try:
            # Get the original mix design
            original = self.get_by_id(mix_design_id)
            if not original:
                raise NotFoundError(f"Mix design with ID {mix_design_id} not found")
            
            # Create duplicate data
            duplicate_data = MixDesignCreate(
                name=new_name,
                description=f"Copy of {original.name}" + (f" - {original.description}" if original.description else ""),
                water_binder_ratio=original.water_binder_ratio,
                total_water_content=original.total_water_content,
                air_content=original.air_content,
                water_volume_fraction=original.water_volume_fraction,
                air_volume_fraction=original.air_volume_fraction,
                system_size=original.system_size,
                random_seed=original.random_seed,
                cement_shape_set=original.cement_shape_set,
                aggregate_shape_set=original.aggregate_shape_set,
                components=[MixDesignComponentData(**comp) for comp in original.components],
                calculated_properties=MixDesignPropertiesData(**original.calculated_properties) if original.calculated_properties else None,
                notes=original.notes,
                is_template=make_template
            )
            
            # Create the duplicate
            duplicate = self.create(duplicate_data)
            self.logger.info(f"Duplicated mix design '{original.name}' as '{new_name}'")
            return duplicate
            
        except (NotFoundError, AlreadyExistsError):
            raise
        except Exception as e:
            self.logger.error(f"Failed to duplicate mix design: {e}")
            raise ServiceError(f"Failed to duplicate mix design: {e}")
    
    def generate_unique_name(self, base_name: str) -> str:
        """Generate a unique name based on the base name."""
        try:
            existing_names = {mix.name for mix in self.get_all()}
            
            if base_name not in existing_names:
                return base_name
            
            # Try numbered variations
            counter = 1
            while True:
                candidate = f"{base_name}_copy_{counter}" if counter > 1 else f"{base_name}_copy"
                if candidate not in existing_names:
                    return candidate
                counter += 1
                
                # Safety limit
                if counter > 1000:
                    import uuid
                    return f"{base_name}_{uuid.uuid4().hex[:8]}"
                    
        except Exception as e:
            self.logger.error(f"Failed to generate unique name: {e}")
            import uuid
            return f"{base_name}_{uuid.uuid4().hex[:8]}"
    
    def search(self, query: str) -> List[MixDesign]:
        """Search mix designs by name and description."""
        try:
            with self.db_service.get_read_only_session() as session:
                search_pattern = f"%{query}%"
                return session.query(MixDesign).filter(
                    (MixDesign.name.ilike(search_pattern)) |
                    (MixDesign.description.ilike(search_pattern)) |
                    (MixDesign.notes.ilike(search_pattern))
                ).order_by(MixDesign.updated_at.desc()).all()
        except Exception as e:
            self.logger.error(f"Failed to search mix designs: {e}")
            raise ServiceError(f"Failed to search mix designs: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about mix designs."""
        try:
            with self.db_service.get_read_only_session() as session:
                total_count = session.query(MixDesign).count()
                template_count = session.query(MixDesign).filter(MixDesign.is_template == True).count()
                
                # Get most recent mix design
                recent = session.query(MixDesign).order_by(MixDesign.updated_at.desc()).first()
                
                return {
                    'total_mix_designs': total_count,
                    'template_mix_designs': template_count,
                    'custom_mix_designs': total_count - template_count,
                    'most_recent': recent.name if recent else None,
                    'most_recent_date': recent.updated_at if recent else None
                }
        except Exception as e:
            self.logger.error(f"Failed to get mix design statistics: {e}")
            return {
                'total_mix_designs': 0,
                'template_mix_designs': 0,
                'custom_mix_designs': 0,
                'most_recent': None,
                'most_recent_date': None
            }
    
    def update(self, name: str, update_data: MixDesignUpdate) -> MixDesign:
        """Update a mix design by name (required by BaseService abstract method)."""
        mix_design = self.get_by_name(name)
        if not mix_design:
            raise NotFoundError(f"Mix design '{name}' not found")
        return self.update_by_id(mix_design.id, update_data)
    
    def update_by_id(self, mix_design_id: int, update_data: MixDesignUpdate) -> MixDesign:
        """Update an existing mix design by ID."""
        try:
            with self.db_service.get_session() as session:
                mix_design = session.query(MixDesign).filter(MixDesign.id == mix_design_id).first()
                if not mix_design:
                    raise NotFoundError(f"Mix design with ID {mix_design_id} not found")
                
                # Update fields if provided
                update_dict = update_data.model_dump(exclude_unset=True)
                
                # Handle special JSON fields
                if 'components' in update_dict:
                    components_json = [comp.model_dump() if hasattr(comp, 'model_dump') else comp 
                                     for comp in update_dict['components']]
                    update_dict['components'] = components_json
                
                if 'calculated_properties' in update_dict and update_dict['calculated_properties']:
                    properties_json = (update_dict['calculated_properties'].model_dump() 
                                     if hasattr(update_dict['calculated_properties'], 'model_dump') 
                                     else update_dict['calculated_properties'])
                    update_dict['calculated_properties'] = properties_json
                
                # Update timestamp
                update_dict['updated_at'] = datetime.utcnow()
                
                # Apply updates
                for key, value in update_dict.items():
                    setattr(mix_design, key, value)
                
                session.commit()
                session.refresh(mix_design)
                
            self.logger.info(f"Updated mix design: {mix_design.name}")
            return mix_design
            
        except NotFoundError:
            raise
        except IntegrityError as e:
            self.logger.error(f"Mix design name conflict during update: {e}")
            raise AlreadyExistsError(f"Mix design name already exists")
        except Exception as e:
            self.logger.error(f"Failed to update mix design: {e}")
            raise ServiceError(f"Failed to update mix design: {e}")
    
    def delete(self, name: str) -> bool:
        """Delete a mix design by name (required by BaseService abstract method)."""
        mix_design = self.get_by_name(name)
        if not mix_design:
            raise NotFoundError(f"Mix design '{name}' not found")
        return self.delete_by_id(mix_design.id)
    
    def delete_by_id(self, mix_design_id: int) -> bool:
        """Delete a mix design by ID."""
        try:
            with self.db_service.get_session() as session:
                mix_design = session.query(MixDesign).filter(MixDesign.id == mix_design_id).first()
                if not mix_design:
                    raise NotFoundError(f"Mix design with ID {mix_design_id} not found")
                
                name = mix_design.name  # Store name for logging
                session.delete(mix_design)
                session.commit()
                
            self.logger.info(f"Deleted mix design: {name}")
            return True
            
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to delete mix design: {e}")
            raise ServiceError(f"Failed to delete mix design: {e}")
    
    def to_response(self, mix_design: MixDesign) -> MixDesignResponse:
        """Convert a MixDesign model to response format."""
        try:
            # Convert JSON components back to Pydantic models
            components = [MixDesignComponentData(**comp) for comp in mix_design.components]
            properties = (MixDesignPropertiesData(**mix_design.calculated_properties) 
                         if mix_design.calculated_properties else None)
            
            return MixDesignResponse(
                id=mix_design.id,
                name=mix_design.name,
                description=mix_design.description,
                created_at=mix_design.created_at,
                updated_at=mix_design.updated_at,
                water_binder_ratio=mix_design.water_binder_ratio,
                total_water_content=mix_design.total_water_content,
                air_content=mix_design.air_content,
                water_volume_fraction=mix_design.water_volume_fraction,
                air_volume_fraction=mix_design.air_volume_fraction,
                system_size=mix_design.system_size,
                random_seed=mix_design.random_seed,
                cement_shape_set=mix_design.cement_shape_set,
                aggregate_shape_set=mix_design.aggregate_shape_set,
                components=components,
                calculated_properties=properties,
                notes=mix_design.notes,
                is_template=mix_design.is_template
            )
        except Exception as e:
            self.logger.error(f"Failed to convert mix design to response: {e}")
            raise ServiceError(f"Failed to convert mix design: {e}")
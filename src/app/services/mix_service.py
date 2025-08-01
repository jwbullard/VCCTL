#!/usr/bin/env python3
"""
Mix Service for VCCTL

Provides business logic for concrete mix design and composition calculations.
Converted from Java Spring service to Python.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.exc import IntegrityError
from dataclasses import dataclass
from enum import Enum

from app.database.service import DatabaseService
from app.models.cement import Cement
from app.models.fly_ash import FlyAsh
from app.models.slag import Slag
from app.models.inert_filler import InertFiller
from app.models.silica_fume import SilicaFume
from app.models.limestone import Limestone
from app.models.aggregate import Aggregate
from app.models.grading import Grading
from app.services.base_service import BaseService, ServiceError, NotFoundError, ValidationError


class MaterialType(Enum):
    """Material type enumeration for mix design."""
    CEMENT = "cement"
    FLY_ASH = "fly_ash"
    SLAG = "slag"
    INERT_FILLER = "inert_filler"
    SILICA_FUME = "silica_fume"
    LIMESTONE = "limestone"
    AGGREGATE = "aggregate"
    WATER = "water"


@dataclass
class MixComponent:
    """Represents a component in a concrete mix."""
    material_name: str
    material_type: MaterialType
    mass_fraction: float = 0.0
    volume_fraction: float = 0.0
    specific_gravity: float = 0.0
    
    def __post_init__(self):
        """Validate component data after initialization."""
        if self.mass_fraction < 0 or self.mass_fraction > 1:
            raise ValueError("Mass fraction must be between 0 and 1")
        if self.volume_fraction < 0 or self.volume_fraction > 1:
            raise ValueError("Volume fraction must be between 0 and 1")
        if self.specific_gravity < 0:
            raise ValueError("Specific gravity must be positive")


@dataclass
class MixDesign:
    """Represents a complete concrete mix design."""
    name: str
    components: List[MixComponent]
    water_binder_ratio: float = 0.0
    total_water_content: float = 0.0
    air_content: float = 0.0
    water_volume_fraction: float = 0.0
    air_volume_fraction: float = 0.0
    
    def __post_init__(self):
        """Validate mix design data after initialization."""
        if self.water_binder_ratio < 0 or self.water_binder_ratio > 2.0:
            raise ValueError("Water-binder ratio must be between 0 and 2.0")
        if self.air_content < 0 or self.air_content > 0.15:
            raise ValueError("Air content must be between 0 and 0.15 (volume fraction)")


class MixService:
    """
    Service for managing concrete mix designs.
    
    Provides composition calculations, water-binder ratio calculations,
    and mix validation for the VCCTL system.
    """
    
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
        self.logger = logging.getLogger('VCCTL.MixService')
        
        # Standard specific gravities for calculations
        self.default_specific_gravities = {
            MaterialType.CEMENT: 3.15,
            MaterialType.FLY_ASH: 2.77,
            MaterialType.SLAG: 2.87,
            MaterialType.INERT_FILLER: 3.0,
            MaterialType.SILICA_FUME: 2.22,
            MaterialType.LIMESTONE: 2.71,
            MaterialType.AGGREGATE: 2.65,
            MaterialType.WATER: 1.0
        }
    
    def create_mix_design(self, mix_data: Dict[str, Any]) -> MixDesign:
        """Create a new mix design from input data."""
        try:
            mix_name = mix_data.get('name', '')
            if not mix_name:
                raise ValidationError("Mix name is required")
            
            components = []
            total_mass_fraction = 0.0
            
            # Process each component in the mix
            for component_data in mix_data.get('components', []):
                component = self._create_mix_component(component_data)
                components.append(component)
                total_mass_fraction += component.mass_fraction
            
            # Validate total mass fractions
            if abs(total_mass_fraction - 1.0) > 0.001:
                raise ValidationError(f"Total mass fractions must sum to 1.0, got {total_mass_fraction}")
            
            # Calculate water-binder ratio
            water_binder_ratio = mix_data.get('water_binder_ratio', 0.0)
            total_water_content = mix_data.get('total_water_content', 0.0)
            air_content = mix_data.get('air_content', 0.0)
            
            mix_design = MixDesign(
                name=mix_name,
                components=components,
                water_binder_ratio=water_binder_ratio,
                total_water_content=total_water_content,
                air_content=air_content
            )
            
            # Calculate volume fractions
            self._calculate_volume_fractions(mix_design)
            
            self.logger.info(f"Created mix design: {mix_name}")
            return mix_design
            
        except Exception as e:
            self.logger.error(f"Failed to create mix design: {e}")
            raise ServiceError(f"Failed to create mix design: {e}")
    
    def _create_mix_component(self, component_data: Dict[str, Any]) -> MixComponent:
        """Create a mix component from data."""
        material_name = component_data.get('material_name', '')
        material_type_str = component_data.get('material_type', '')
        
        try:
            material_type = MaterialType(material_type_str)
        except ValueError:
            raise ValidationError(f"Invalid material type: {material_type_str}")
        
        mass_fraction = component_data.get('mass_fraction', 0.0)
        
        # Get specific gravity from material or use default
        specific_gravity = component_data.get('specific_gravity')
        if specific_gravity is None:
            specific_gravity = self._get_material_specific_gravity(material_name, material_type)
        
        return MixComponent(
            material_name=material_name,
            material_type=material_type,
            mass_fraction=mass_fraction,
            specific_gravity=specific_gravity
        )
    
    def _get_material_specific_gravity(self, material_name: str, material_type: MaterialType) -> float:
        """Get specific gravity for a material from the database."""
        try:
            with self.db_service.get_read_only_session() as session:
                if material_type == MaterialType.CEMENT:
                    material = session.query(Cement).filter_by(name=material_name).first()
                elif material_type == MaterialType.FLY_ASH:
                    material = session.query(FlyAsh).filter_by(name=material_name).first()
                elif material_type == MaterialType.SLAG:
                    material = session.query(Slag).filter_by(name=material_name).first()
                elif material_type == MaterialType.INERT_FILLER:
                    material = session.query(InertFiller).filter_by(name=material_name).first()
                elif material_type == MaterialType.SILICA_FUME:
                    material = session.query(SilicaFume).filter_by(name=material_name).first()
                elif material_type == MaterialType.LIMESTONE:
                    material = session.query(Limestone).filter_by(name=material_name).first()
                elif material_type == MaterialType.AGGREGATE:
                    material = session.query(Aggregate).filter_by(name=material_name).first()
                else:
                    material = None
                
                if material and hasattr(material, 'specific_gravity') and material.specific_gravity:
                    return material.specific_gravity
                else:
                    # Use default specific gravity for material type
                    return self.default_specific_gravities.get(material_type, 2.65)
                    
        except Exception as e:
            self.logger.warning(f"Failed to get specific gravity for {material_name}: {e}")
            return self.default_specific_gravities.get(material_type, 2.65)
    
    def _calculate_volume_fractions(self, mix_design: MixDesign) -> None:
        """Calculate volume fractions from mass fractions and specific gravities."""
        try:
            # Calculate absolute volumes (mass_fraction / specific_gravity)
            absolute_volumes = []
            
            for component in mix_design.components:
                if component.specific_gravity > 0:
                    absolute_volume = component.mass_fraction / component.specific_gravity
                else:
                    absolute_volume = 0.0
                absolute_volumes.append(absolute_volume)
            
            # Calculate water absolute volume (water SG = 1.0)
            water_absolute_volume = mix_design.total_water_content / 1.0
            
            # Calculate total solid volume (all materials + water)
            total_solid_volume = sum(absolute_volumes) + water_absolute_volume
            
            # Air content is a volume fraction of total concrete volume
            # Total concrete volume = solid volume / (1 - air_volume_fraction)
            air_volume_fraction = mix_design.air_content
            if air_volume_fraction < 1.0 and air_volume_fraction >= 0:
                total_concrete_volume = total_solid_volume / (1.0 - air_volume_fraction)
            else:
                total_concrete_volume = total_solid_volume
            
            # Calculate volume fractions relative to total concrete volume
            if total_concrete_volume > 0:
                for i, component in enumerate(mix_design.components):
                    component.volume_fraction = absolute_volumes[i] / total_concrete_volume
                
                # Store volume fractions - all should sum to 1.0
                mix_design.water_volume_fraction = water_absolute_volume / total_concrete_volume
                mix_design.air_volume_fraction = air_volume_fraction
                
                # Verify the calculation sums to 1.0
                total_calc = sum(comp.volume_fraction for comp in mix_design.components) + mix_design.water_volume_fraction + mix_design.air_volume_fraction
                self.logger.debug(f"Volume fraction calculation check: {total_calc:.6f} (should be ~1.0)")
                
            else:
                # Fallback for edge case
                for component in mix_design.components:
                    component.volume_fraction = 0.0
                mix_design.water_volume_fraction = 0.0
                mix_design.air_volume_fraction = 0.0
            
        except Exception as e:
            self.logger.error(f"Failed to calculate volume fractions: {e}")
            raise ServiceError(f"Volume fraction calculation failed: {e}")
    
    def calculate_water_binder_ratio(self, mix_design: MixDesign) -> float:
        """Calculate water-binder ratio for a mix design (water mass / powder mass)."""
        try:
            # Calculate total powder mass fraction (cement, fly ash, slag, inert filler)
            powder_types = {MaterialType.CEMENT, MaterialType.FLY_ASH, MaterialType.SLAG, MaterialType.INERT_FILLER, MaterialType.SILICA_FUME, MaterialType.LIMESTONE}
            total_powder_fraction = sum(
                comp.mass_fraction for comp in mix_design.components 
                if comp.material_type in powder_types
            )
            
            if total_powder_fraction == 0:
                raise ValidationError("No powder materials found in mix")
            
            # Calculate water-binder ratio (water mass / powder mass)
            water_binder_ratio = mix_design.total_water_content / total_powder_fraction
            
            mix_design.water_binder_ratio = water_binder_ratio
            return water_binder_ratio
            
        except Exception as e:
            self.logger.error(f"Failed to calculate water-binder ratio: {e}")
            raise ServiceError(f"Water-binder ratio calculation failed: {e}")
    
    def validate_mix_design(self, mix_design: MixDesign) -> Dict[str, Any]:
        """Validate a mix design and return validation results."""
        validation_result = {
            'is_valid': True,
            'warnings': [],
            'errors': [],
            'recommendations': []
        }
        
        try:
            # Check total mass fractions (components + water should sum to 1.0)
            component_mass_total = sum(comp.mass_fraction for comp in mix_design.components)
            water_mass_fraction = mix_design.total_water_content  # This is a mass fraction
            total_mass = component_mass_total + water_mass_fraction
            
            if abs(total_mass - 1.0) > 0.001:
                validation_result['errors'].append(f"Mass fractions sum to {total_mass:.3f}, should be 1.0")
                validation_result['is_valid'] = False
            
            # Check water-binder ratio
            if mix_design.water_binder_ratio < 0.25:
                validation_result['warnings'].append("Very low water-binder ratio may cause workability issues")
            elif mix_design.water_binder_ratio > 0.65:
                validation_result['warnings'].append("High water-binder ratio may reduce strength and durability")
            
            # Check air content (volume fraction)
            if mix_design.air_content > 0.10:
                validation_result['warnings'].append("High air content (>10% volume fraction) may significantly reduce strength")
            
            # Check powder content
            powder_types = {MaterialType.CEMENT, MaterialType.FLY_ASH, MaterialType.SLAG, MaterialType.INERT_FILLER, MaterialType.SILICA_FUME, MaterialType.LIMESTONE}
            total_powder = sum(
                comp.mass_fraction for comp in mix_design.components 
                if comp.material_type in powder_types
            )
            
            # Check binder content (powder + water)
            total_binder = total_powder + mix_design.total_water_content
            
            if total_powder < 0.10:
                validation_result['errors'].append("Insufficient powder content (<10%)")
                validation_result['is_valid'] = False
            elif total_binder > 0.50:
                validation_result['warnings'].append("Very high binder content (>50%) may be uneconomical")
            
            # Check aggregate content
            aggregate_components = [comp for comp in mix_design.components 
                                 if comp.material_type == MaterialType.AGGREGATE]
            total_aggregate = sum(comp.mass_fraction for comp in aggregate_components)
            
            if total_aggregate < 0.40:
                validation_result['warnings'].append("Low aggregate content may affect economy and shrinkage")
            
            # Check for cement in mix
            cement_components = [comp for comp in mix_design.components 
                               if comp.material_type == MaterialType.CEMENT]
            if not cement_components:
                validation_result['errors'].append("No cement found in mix - cement is required for hydration")
                validation_result['is_valid'] = False
            
            # Recommendations based on mix composition
            scm_fraction = sum(
                comp.mass_fraction for comp in mix_design.components 
                if comp.material_type in {MaterialType.FLY_ASH, MaterialType.SLAG}
            )
            
            if scm_fraction > 0.50:
                validation_result['warnings'].append("High SCM replacement (>50%) may affect early strength")
            elif scm_fraction > 0 and scm_fraction < 0.15:
                validation_result['recommendations'].append("Consider increasing SCM content for improved sustainability")
            
            return validation_result
            
        except Exception as e:
            self.logger.error(f"Failed to validate mix design: {e}")
            validation_result['errors'].append(f"Validation failed: {e}")
            validation_result['is_valid'] = False
            return validation_result
    
    
    def calculate_mix_properties(self, mix_design: MixDesign) -> Dict[str, Any]:
        """Calculate derived properties of a mix design."""
        try:
            properties = {}
            
            # Calculate weighted average specific gravity for all components
            total_weighted_sg = sum(
                comp.mass_fraction * comp.specific_gravity 
                for comp in mix_design.components
            )
            properties['weighted_average_specific_gravity'] = total_weighted_sg
            
            # Calculate powder-specific properties
            powder_types = {MaterialType.CEMENT, MaterialType.FLY_ASH, MaterialType.SLAG, MaterialType.INERT_FILLER, MaterialType.SILICA_FUME, MaterialType.LIMESTONE}
            powder_components = [comp for comp in mix_design.components if comp.material_type in powder_types]
            
            # Calculate mass-weighted average specific gravity of powder components
            if powder_components:
                total_powder_mass_fraction = sum(comp.mass_fraction for comp in powder_components)
                powder_weighted_sg = sum(
                    comp.mass_fraction * comp.specific_gravity for comp in powder_components
                ) / total_powder_mass_fraction if total_powder_mass_fraction > 0 else 3.15
                properties['powder_specific_gravity'] = powder_weighted_sg
            else:
                properties['powder_specific_gravity'] = 3.15
            
            # Calculate volume fractions (this also sets water_volume_fraction and air_volume_fraction)
            self._calculate_volume_fractions(mix_design)
            
            # Add volume properties
            properties['water_volume_fraction'] = getattr(mix_design, 'water_volume_fraction', 0.0)
            properties['air_volume_fraction'] = getattr(mix_design, 'air_volume_fraction', 0.0)
            
            # Calculate total volume fractions for different phases
            powder_volume_fraction = sum(comp.volume_fraction for comp in powder_components)
            properties['powder_volume_fraction'] = powder_volume_fraction
            properties['paste_volume_fraction'] = powder_volume_fraction + properties['water_volume_fraction']
            
            # Calculate powder mass composition
            total_powder_mass = sum(comp.mass_fraction for comp in powder_components)
            
            # Calculate binder composition (powder + water)
            total_binder_mass = total_powder_mass + mix_design.total_water_content
            
            properties['total_powder_fraction'] = total_powder_mass
            properties['total_binder_fraction'] = total_binder_mass
            properties['water_binder_ratio'] = mix_design.water_binder_ratio
            
            # Calculate SCM replacement ratio (SCM mass / total powder mass)
            scm_mass = sum(
                comp.mass_fraction for comp in mix_design.components 
                if comp.material_type in {MaterialType.FLY_ASH, MaterialType.SLAG}
            )
            
            if total_powder_mass > 0:
                properties['scm_replacement_ratio'] = scm_mass / total_powder_mass
            else:
                properties['scm_replacement_ratio'] = 0.0
            
            # Calculate aggregate volume fraction (which is what users expect to see)
            aggregate_components = [comp for comp in mix_design.components if comp.material_type == MaterialType.AGGREGATE]
            aggregate_volume_fraction = sum(comp.volume_fraction for comp in aggregate_components)
            
            # Debug logging
            self.logger.debug(f"Found {len(aggregate_components)} aggregate components")
            for comp in aggregate_components:
                self.logger.debug(f"  {comp.material_name}: mass_fraction={comp.mass_fraction:.3f}, volume_fraction={comp.volume_fraction:.3f}, sg={comp.specific_gravity:.3f}")
            self.logger.debug(f"Total aggregate volume fraction: {aggregate_volume_fraction:.3f}")
            
            properties['total_aggregate_fraction'] = aggregate_volume_fraction
            
            # Calculate void ratio (simplified)
            total_solid_volume = sum(comp.volume_fraction for comp in mix_design.components)
            void_ratio = (1.0 - total_solid_volume) / total_solid_volume if total_solid_volume > 0 else 0
            properties['void_ratio'] = void_ratio
            
            return properties
            
        except Exception as e:
            self.logger.error(f"Failed to calculate mix properties: {e}")
            raise ServiceError(f"Mix properties calculation failed: {e}")
    
    def optimize_water_content(self, mix_design: MixDesign, target_w_b_ratio: float) -> float:
        """Optimize water content to achieve target water-binder ratio (water mass / powder mass)."""
        try:
            # Calculate total powder mass fraction
            powder_types = {MaterialType.CEMENT, MaterialType.FLY_ASH, MaterialType.SLAG, MaterialType.INERT_FILLER, MaterialType.SILICA_FUME, MaterialType.LIMESTONE}
            total_powder_fraction = sum(
                comp.mass_fraction for comp in mix_design.components 
                if comp.material_type in powder_types
            )
            
            if total_powder_fraction == 0:
                raise ValidationError("No powder materials found in mix")
            
            # Calculate required water content (water mass / powder mass = target ratio)
            required_water_content = target_w_b_ratio * total_powder_fraction
            
            # Update mix design
            mix_design.total_water_content = required_water_content
            mix_design.water_binder_ratio = target_w_b_ratio
            
            self.logger.info(f"Optimized water content to {required_water_content:.3f} for w/b ratio {target_w_b_ratio}")
            return required_water_content
            
        except Exception as e:
            self.logger.error(f"Failed to optimize water content: {e}")
            raise ServiceError(f"Water content optimization failed: {e}")
    
    def get_compatible_materials(self, material_type: MaterialType) -> List[str]:
        """Get list of available materials of a specific type."""
        try:
            with self.db_service.get_read_only_session() as session:
                if material_type == MaterialType.CEMENT:
                    materials = session.query(Cement.name).all()
                elif material_type == MaterialType.FLY_ASH:
                    materials = session.query(FlyAsh.name).all()
                elif material_type == MaterialType.SLAG:
                    materials = session.query(Slag.name).all()
                elif material_type == MaterialType.INERT_FILLER:
                    materials = session.query(InertFiller.name).all()
                elif material_type == MaterialType.SILICA_FUME:
                    materials = session.query(SilicaFume.name).all()
                elif material_type == MaterialType.LIMESTONE:
                    materials = session.query(Limestone.name).all()
                elif material_type == MaterialType.AGGREGATE:
                    materials = session.query(Aggregate.display_name).all()
                else:
                    return []
                
                # For aggregates, return display_name; for others, return name
                if material_type == MaterialType.AGGREGATE:
                    return [material.display_name for material in materials]
                else:
                    return [material.name for material in materials]
                
        except Exception as e:
            self.logger.error(f"Failed to get compatible materials for {material_type}: {e}")
            raise ServiceError(f"Failed to retrieve materials: {e}")
    
    def get_fine_aggregates(self) -> List[str]:
        """Get list of fine aggregates (type = 2)."""
        try:
            with self.db_service.get_read_only_session() as session:
                fine_aggregates = session.query(Aggregate.display_name).filter(Aggregate.type == 2).all()
                return [agg.display_name for agg in fine_aggregates]
                
        except Exception as e:
            self.logger.error(f"Failed to get fine aggregates: {e}")
            raise ServiceError(f"Failed to retrieve fine aggregates: {e}")
    
    def get_coarse_aggregates(self) -> List[str]:
        """Get list of coarse aggregates (type = 1)."""
        try:
            with self.db_service.get_read_only_session() as session:
                coarse_aggregates = session.query(Aggregate.display_name).filter(Aggregate.type == 1).all()
                return [agg.display_name for agg in coarse_aggregates]
                
        except Exception as e:
            self.logger.error(f"Failed to get coarse aggregates: {e}")
            raise ServiceError(f"Failed to retrieve coarse aggregates: {e}")
    
    def compare_mix_designs(self, mix1: MixDesign, mix2: MixDesign) -> Dict[str, Any]:
        """Compare two mix designs and return differences."""
        try:
            comparison = {
                'mix1_name': mix1.name,
                'mix2_name': mix2.name,
                'differences': [],
                'similarities': [],
                'recommendations': []
            }
            
            # Compare water-binder ratios
            wb_diff = abs(mix1.water_binder_ratio - mix2.water_binder_ratio)
            if wb_diff > 0.05:
                comparison['differences'].append(
                    f"W/B ratio: {mix1.name}={mix1.water_binder_ratio:.3f}, "
                    f"{mix2.name}={mix2.water_binder_ratio:.3f}"
                )
            else:
                comparison['similarities'].append("Similar water-binder ratios")
            
            # Compare component counts
            if len(mix1.components) != len(mix2.components):
                comparison['differences'].append(
                    f"Component count: {mix1.name}={len(mix1.components)}, "
                    f"{mix2.name}={len(mix2.components)}"
                )
            
            # Compare binder content
            mix1_props = self.calculate_mix_properties(mix1)
            mix2_props = self.calculate_mix_properties(mix2)
            
            binder_diff = abs(mix1_props['total_binder_fraction'] - mix2_props['total_binder_fraction'])
            if binder_diff > 0.05:
                comparison['differences'].append(
                    f"Binder content: {mix1.name}={mix1_props['total_binder_fraction']:.3f}, "
                    f"{mix2.name}={mix2_props['total_binder_fraction']:.3f}"
                )
            
            return comparison
            
        except Exception as e:
            self.logger.error(f"Failed to compare mix designs: {e}")
            raise ServiceError(f"Mix design comparison failed: {e}")
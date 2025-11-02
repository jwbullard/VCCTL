#!/usr/bin/env python3
"""
Centralized Mix Design Validation

Single source of truth for all mix design validation logic.
Used by Pydantic models, service layer, and UI components.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from app.models.material_types import MaterialType


@dataclass
class ValidationResult:
    """Result of validation with specific error/warning details."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    recommendations: List[str]


@dataclass
class ComponentData:
    """Normalized component data for validation."""
    material_name: str
    material_type: str
    mass_fraction: float
    volume_fraction: float
    specific_gravity: float


class MixDesignValidator:
    """
    Centralized validation logic for mix designs.
    
    This class contains all validation rules and is used by:
    - Pydantic models (data structure validation)
    - Service layer (business logic validation)  
    - UI components (real-time validation)
    """
    
    # Engineering constraints
    MIN_WATER_BINDER_RATIO = 0.25
    MAX_WATER_BINDER_RATIO = 0.65
    MAX_AIR_CONTENT = 0.10
    MIN_POWDER_CONTENT = 0.10
    MAX_BINDER_CONTENT = 0.50
    MASS_FRACTION_TOLERANCE = 0.001
    
    # Powder material types
    POWDER_TYPES = {
        MaterialType.CEMENT, 
        MaterialType.FLY_ASH, 
        MaterialType.SLAG, 
        MaterialType.FILLER, 
        MaterialType.SILICA_FUME, 
        MaterialType.LIMESTONE
    }
    
    @classmethod
    def validate_complete_mix_design(
        cls,
        components: List[ComponentData],
        water_binder_ratio: float,
        air_content: float = 0.0,
        total_water_content: float = 0.0
    ) -> ValidationResult:
        """
        Complete validation of mix design.
        
        Args:
            components: List of mix components
            water_binder_ratio: W/B ratio
            air_content: Air content (volume fraction)
            total_water_content: Water mass fraction relative to solids
            
        Returns:
            ValidationResult with all validation outcomes
        """
        result = ValidationResult(
            is_valid=True,
            errors=[],
            warnings=[],
            recommendations=[]
        )
        
        # Validate components
        cls._validate_mass_fractions(components, result)
        cls._validate_component_uniqueness(components, result)
        cls._validate_powder_content(components, result)
        cls._validate_aggregate_content(components, result)
        
        # Validate mix parameters
        cls._validate_water_binder_ratio(water_binder_ratio, result)
        cls._validate_air_content(air_content, result)
        cls._validate_water_content(total_water_content, result)
        cls._validate_binder_content(components, total_water_content, result)
        
        return result
    
    @classmethod
    def _validate_mass_fractions(
        cls, 
        components: List[ComponentData], 
        result: ValidationResult
    ) -> None:
        """Validate that all component mass fractions sum to 1.0 (Type 3 logic)."""
        if not components:
            result.errors.append("Mix design must have at least one component")
            result.is_valid = False
            return
        
        # Type 3 mass fractions: ALL components including water sum to 1.0
        total_mass_fraction = sum(c.mass_fraction for c in components)
        if abs(total_mass_fraction - 1.0) > cls.MASS_FRACTION_TOLERANCE:
            result.errors.append(
                f"All component mass fractions sum to {total_mass_fraction:.3f}, should be 1.0"
            )
            result.is_valid = False
        
        # Separate water components for additional validation
        water_components = [c for c in components if c.material_type == 'water']
        
        # Validate water component (max 1, non-negative)
        if len(water_components) > 1:
            result.errors.append("Mix design cannot have more than one water component")
            result.is_valid = False
        
        if water_components and water_components[0].mass_fraction < 0:
            result.errors.append("Water mass fraction cannot be negative")
            result.is_valid = False
    
    @classmethod
    def _validate_component_uniqueness(
        cls, 
        components: List[ComponentData], 
        result: ValidationResult
    ) -> None:
        """Validate no duplicate material names."""
        material_names = [c.material_name for c in components]
        if len(material_names) != len(set(material_names)):
            result.errors.append("Mix design cannot have duplicate material names")
            result.is_valid = False
    
    @classmethod
    def _validate_powder_content(
        cls, 
        components: List[ComponentData], 
        result: ValidationResult
    ) -> None:
        """Validate powder content is adequate."""
        # Convert string material types to enum for comparison
        powder_components = []
        for comp in components:
            try:
                material_type = MaterialType(comp.material_type)
                if material_type in cls.POWDER_TYPES:
                    powder_components.append(comp)
            except ValueError:
                # Handle string material types that don't match enum
                if comp.material_type.upper() in [mt.value.upper() for mt in cls.POWDER_TYPES]:
                    powder_components.append(comp)
        
        total_powder = sum(c.mass_fraction for c in powder_components)
        
        if total_powder < cls.MIN_POWDER_CONTENT:
            result.errors.append(f"Insufficient powder content ({total_powder:.1%} < {cls.MIN_POWDER_CONTENT:.1%})")
            result.is_valid = False
    
    @classmethod
    def _validate_aggregate_content(
        cls, 
        components: List[ComponentData], 
        result: ValidationResult
    ) -> None:
        """Validate aggregate content."""
        aggregate_components = [c for c in components if c.material_type == 'aggregate']
        total_aggregate = sum(c.mass_fraction for c in aggregate_components)
        
        # This is informational - no hard constraints on aggregate content
        if total_aggregate > 0.8:
            result.warnings.append(f"Very high aggregate content ({total_aggregate:.1%})")
    
    @classmethod
    def _validate_water_binder_ratio(
        cls, 
        water_binder_ratio: float, 
        result: ValidationResult
    ) -> None:
        """Validate water-binder ratio is in acceptable range."""
        if water_binder_ratio < cls.MIN_WATER_BINDER_RATIO:
            result.warnings.append(
                f"Very low water-binder ratio ({water_binder_ratio:.3f}) may cause workability issues"
            )
        elif water_binder_ratio > cls.MAX_WATER_BINDER_RATIO:
            result.warnings.append(
                f"High water-binder ratio ({water_binder_ratio:.3f}) may reduce strength and durability"
            )
    
    @classmethod
    def _validate_air_content(
        cls, 
        air_content: float, 
        result: ValidationResult
    ) -> None:
        """Validate air content."""
        if air_content > cls.MAX_AIR_CONTENT:
            result.warnings.append(
                f"High air content ({air_content:.1%}) may significantly reduce strength"
            )
    
    @classmethod
    def _validate_water_content(
        cls, 
        total_water_content: float, 
        result: ValidationResult
    ) -> None:
        """Validate water content."""
        if total_water_content < 0:
            result.errors.append("Water content cannot be negative")
            result.is_valid = False
    
    @classmethod
    def _validate_binder_content(
        cls, 
        components: List[ComponentData], 
        total_water_content: float, 
        result: ValidationResult
    ) -> None:
        """Validate total binder content."""
        # Calculate powder content
        powder_components = []
        for comp in components:
            try:
                material_type = MaterialType(comp.material_type)
                if material_type in cls.POWDER_TYPES:
                    powder_components.append(comp)
            except ValueError:
                if comp.material_type.upper() in [mt.value.upper() for mt in cls.POWDER_TYPES]:
                    powder_components.append(comp)
        
        total_powder = sum(c.mass_fraction for c in powder_components)

        # Convert both powder and water from solids-basis to total-mass-basis for binder calculation
        # Formula: (powder + water) / (1 + water) gives fraction of total mass that is binder
        total_binder = (total_powder + total_water_content) / (1.0 + total_water_content) if (1.0 + total_water_content) > 0 else 0.0
        
        if total_binder > cls.MAX_BINDER_CONTENT:
            result.warnings.append(
                f"Very high binder content ({total_binder:.1%}) may be uneconomical"
            )
    
    @classmethod
    def validate_mass_fractions_only(
        cls, 
        components: List[ComponentData]
    ) -> Tuple[bool, str]:
        """
        Quick validation of just mass fractions (for real-time UI feedback).
        
        Returns:
            (is_valid, error_message)
        """
        if not components:
            return False, "No components defined"
        
        # Type 3 mass fractions: ALL components including water sum to 1.0
        total_mass_fraction = sum(c.mass_fraction for c in components)
        
        if abs(total_mass_fraction - 1.0) > cls.MASS_FRACTION_TOLERANCE:
            return False, f"All components sum to {total_mass_fraction:.3f}, should be 1.0"
        
        return True, ""
    
    @classmethod
    def validate_component_uniqueness_only(
        cls, 
        components: List[ComponentData]
    ) -> Tuple[bool, str]:
        """
        Quick validation of component name uniqueness.
        
        Returns:
            (is_valid, error_message)
        """
        material_names = [c.material_name for c in components]
        if len(material_names) != len(set(material_names)):
            return False, "Duplicate material names not allowed"
        
        return True, ""
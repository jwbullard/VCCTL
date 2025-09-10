#!/usr/bin/env python3
"""
Mass Fraction Conversion Service for VCCTL

Handles conversion between different mass fraction types:
- Type 1: Binder Solids Mass Fractions (powders only, sum to 1.0)
- Type 2: Concrete Binder Mass Fractions (powders + water, sum to 1.0) 
- Type 3: Concrete Mass Fractions (all components including aggregates, sum to 1.0)

Also provides volume fraction conversions for genmic.c input generation.
"""

import logging
from typing import List, Dict, Tuple, Any, Optional
from dataclasses import dataclass
from enum import Enum

class MaterialType(Enum):
    """Material type enumeration."""
    CEMENT = "cement"
    FLY_ASH = "fly_ash" 
    SLAG = "slag"
    FILLER = "filler"
    SILICA_FUME = "silica_fume"
    LIMESTONE = "limestone"
    WATER = "water"
    AGGREGATE = "aggregate"

@dataclass 
class Component:
    """Material component with properties."""
    material_name: str
    material_type: MaterialType
    mass_fraction: float  # Type 3 by default (stored in database)
    specific_gravity: float
    
    @property
    def is_powder(self) -> bool:
        """Check if component is a powder material."""
        return self.material_type in {
            MaterialType.CEMENT, MaterialType.FLY_ASH, MaterialType.SLAG,
            MaterialType.FILLER, MaterialType.SILICA_FUME, MaterialType.LIMESTONE
        }
    
    @property 
    def is_water(self) -> bool:
        """Check if component is water."""
        return self.material_type == MaterialType.WATER
        
    @property
    def is_aggregate(self) -> bool:
        """Check if component is aggregate."""
        return self.material_type == MaterialType.AGGREGATE

class MassFractionConverter:
    """
    Service for converting between different mass fraction types.
    
    Key principles:
    - Database stores Type 3 mass fractions (all components sum to 1.0)
    - genmic.c requires Type 2 and Type 1 volume fractions
    - All conversions maintain mass conservation
    """
    
    def __init__(self):
        self.logger = logging.getLogger('VCCTL.MassFractionConverter')
    
    def type3_to_type2_mass_fractions(self, components: List[Component]) -> Dict[str, float]:
        """
        Convert Type 3 to Type 2 mass fractions.
        
        Type 3: All components (powders + water + aggregates) sum to 1.0
        Type 2: Binder components (powders + water) sum to 1.0
        
        Args:
            components: List of components with Type 3 mass fractions
            
        Returns:
            Dict mapping component names to Type 2 mass fractions
        """
        try:
            # Extract binder components (powders + water)
            binder_components = [c for c in components if c.is_powder or c.is_water]
            
            if not binder_components:
                self.logger.warning("No binder components found")
                return {}
            
            # Calculate total binder mass fraction (Type 3 basis)
            total_binder_mass_fraction = sum(c.mass_fraction for c in binder_components)
            
            if total_binder_mass_fraction <= 0:
                self.logger.error("Total binder mass fraction is zero or negative")
                return {}
            
            # Convert to Type 2 (normalize to sum = 1.0)
            type2_fractions = {}
            for comp in binder_components:
                type2_fractions[comp.material_name] = comp.mass_fraction / total_binder_mass_fraction
            
            # Validation
            total_type2 = sum(type2_fractions.values())
            if abs(total_type2 - 1.0) > 1e-6:
                self.logger.error(f"Type 2 mass fractions sum to {total_type2:.6f}, expected 1.0")
                return {}
            
            self.logger.info(f"Converted {len(binder_components)} components to Type 2 mass fractions")
            return type2_fractions
            
        except Exception as e:
            self.logger.error(f"Failed to convert Type 3 to Type 2 mass fractions: {e}")
            return {}
    
    def type2_to_type1_mass_fractions(self, components: List[Component], type2_fractions: Dict[str, float]) -> Dict[str, float]:
        """
        Convert Type 2 to Type 1 mass fractions.
        
        Type 2: Binder components (powders + water) sum to 1.0
        Type 1: Powder components only sum to 1.0 (exclude water)
        
        Args:
            components: List of components 
            type2_fractions: Type 2 mass fractions from previous conversion
            
        Returns:
            Dict mapping powder component names to Type 1 mass fractions
        """
        try:
            # Extract powder components only
            powder_components = [c for c in components if c.is_powder]
            
            if not powder_components:
                self.logger.warning("No powder components found")
                return {}
            
            # Calculate total powder mass fraction (Type 2 basis) 
            total_powder_mass_fraction = sum(
                type2_fractions.get(c.material_name, 0) for c in powder_components
            )
            
            if total_powder_mass_fraction <= 0:
                self.logger.error("Total powder mass fraction is zero or negative")
                return {}
            
            # Convert to Type 1 (normalize powders to sum = 1.0)
            type1_fractions = {}
            for comp in powder_components:
                type2_frac = type2_fractions.get(comp.material_name, 0)
                type1_fractions[comp.material_name] = type2_frac / total_powder_mass_fraction
            
            # Validation
            total_type1 = sum(type1_fractions.values())
            if abs(total_type1 - 1.0) > 1e-6:
                self.logger.error(f"Type 1 mass fractions sum to {total_type1:.6f}, expected 1.0")
                return {}
            
            self.logger.info(f"Converted {len(powder_components)} powder components to Type 1 mass fractions")
            return type1_fractions
            
        except Exception as e:
            self.logger.error(f"Failed to convert Type 2 to Type 1 mass fractions: {e}")
            return {}
    
    def mass_to_volume_fractions(self, mass_fractions: Dict[str, float], 
                                components: List[Component]) -> Dict[str, float]:
        """
        Convert mass fractions to volume fractions using specific gravities.
        
        Args:
            mass_fractions: Mass fractions for components
            components: Components with specific gravity data
            
        Returns:
            Dict mapping component names to volume fractions (normalized to sum = 1.0)
        """
        try:
            # Create lookup for specific gravities
            sg_lookup = {c.material_name: c.specific_gravity for c in components}
            
            # Calculate volumes (mass / specific_gravity)
            volumes = {}
            total_volume = 0.0
            
            for name, mass_frac in mass_fractions.items():
                if name not in sg_lookup:
                    self.logger.error(f"No specific gravity found for component: {name}")
                    continue
                
                volume = mass_frac / sg_lookup[name]
                volumes[name] = volume
                total_volume += volume
            
            if total_volume <= 0:
                self.logger.error("Total volume is zero or negative")
                return {}
            
            # Normalize to sum = 1.0
            volume_fractions = {name: vol / total_volume for name, vol in volumes.items()}
            
            # Validation
            total_vol_frac = sum(volume_fractions.values())
            if abs(total_vol_frac - 1.0) > 1e-6:
                self.logger.error(f"Volume fractions sum to {total_vol_frac:.6f}, expected 1.0")
                return {}
            
            self.logger.info(f"Converted {len(mass_fractions)} components to volume fractions")
            return volume_fractions
            
        except Exception as e:
            self.logger.error(f"Failed to convert mass to volume fractions: {e}")
            return {}
    
    def convert_for_genmic(self, components: List[Component]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Convert Type 3 components to genmic.c input format.
        
        Returns both Type 2 and Type 1 volume fractions as required by genmic.c:
        1. Type 2 volume fractions: binder_solid_volume + binder_water_volume = 1.0
        2. Type 1 volume fractions: individual powder volumes sum = 1.0
        
        Args:
            components: List of components with Type 3 mass fractions
            
        Returns:
            Tuple of (type2_volume_fractions, type1_volume_fractions)
        """
        try:
            # Step 1: Type 3 → Type 2 mass fractions
            type2_mass = self.type3_to_type2_mass_fractions(components)
            if not type2_mass:
                return {}, {}
            
            # Step 2: Type 2 mass → Type 2 volume fractions  
            binder_components = [c for c in components if c.is_powder or c.is_water]
            type2_volume = self.mass_to_volume_fractions(type2_mass, binder_components)
            if not type2_volume:
                return {}, {}
            
            # Step 3: Type 2 → Type 1 mass fractions
            type1_mass = self.type2_to_type1_mass_fractions(components, type2_mass)
            if not type1_mass:
                return {}, {}
            
            # Step 4: Type 1 mass → Type 1 volume fractions
            powder_components = [c for c in components if c.is_powder]
            type1_volume = self.mass_to_volume_fractions(type1_mass, powder_components)
            if not type1_volume:
                return {}, {}
            
            # Format for genmic.c consumption
            genmic_type2 = {
                'binder_solid_volume_fraction': sum(
                    type2_volume[c.material_name] for c in powder_components 
                    if c.material_name in type2_volume
                ),
                'binder_water_volume_fraction': sum(
                    type2_volume[c.material_name] for c in components 
                    if c.is_water and c.material_name in type2_volume
                )
            }
            
            genmic_type1 = {
                'powder_volume_fractions': type1_volume
            }
            
            # Validation
            type2_total = genmic_type2['binder_solid_volume_fraction'] + genmic_type2['binder_water_volume_fraction']
            type1_total = sum(type1_volume.values())
            
            if abs(type2_total - 1.0) > 1e-6:
                self.logger.error(f"genmic Type 2 volumes sum to {type2_total:.6f}, expected 1.0")
                return {}, {}
                
            if abs(type1_total - 1.0) > 1e-6:
                self.logger.error(f"genmic Type 1 volumes sum to {type1_total:.6f}, expected 1.0")
                return {}, {}
            
            self.logger.info("Successfully converted components for genmic.c input")
            self.logger.info(f"Type 2: Solid={genmic_type2['binder_solid_volume_fraction']:.6f}, Water={genmic_type2['binder_water_volume_fraction']:.6f}")
            self.logger.info(f"Type 1: {len(type1_volume)} powder components")
            
            return genmic_type2, genmic_type1
            
        except Exception as e:
            self.logger.error(f"Failed to convert components for genmic.c: {e}")
            return {}, {}
    
    def normalize_to_type3(self, components: List[Component]) -> List[Component]:
        """
        Normalize components to proper Type 3 mass fractions (sum = 1.0).
        
        This fixes corrupted mix designs where mass fractions don't sum to 1.0.
        
        Args:
            components: List of components with potentially incorrect mass fractions
            
        Returns:
            List of components with corrected Type 3 mass fractions
        """
        try:
            if not components:
                self.logger.warning("No components to normalize")
                return []
            
            # Calculate current total
            total_mass_fraction = sum(c.mass_fraction for c in components)
            
            if total_mass_fraction <= 0:
                self.logger.error("Total mass fraction is zero or negative - cannot normalize")
                return components
            
            # Normalize each component
            normalized_components = []
            for comp in components:
                normalized_mass_fraction = comp.mass_fraction / total_mass_fraction
                normalized_comp = Component(
                    material_name=comp.material_name,
                    material_type=comp.material_type,
                    mass_fraction=normalized_mass_fraction,
                    specific_gravity=comp.specific_gravity
                )
                normalized_components.append(normalized_comp)
            
            # Validation
            new_total = sum(c.mass_fraction for c in normalized_components)
            if abs(new_total - 1.0) > 1e-6:
                self.logger.error(f"Normalization failed: sum = {new_total:.6f}")
                return components
            
            self.logger.info(f"Normalized {len(components)} components from {total_mass_fraction:.6f} to 1.0")
            return normalized_components
            
        except Exception as e:
            self.logger.error(f"Failed to normalize components to Type 3: {e}")
            return components

    def validate_mass_fractions(self, components: List[Component], 
                               fraction_type: str = "Type 3") -> Tuple[bool, str]:
        """
        Validate mass fractions for a given type.
        
        Args:
            components: List of components to validate
            fraction_type: Type of fractions being validated ("Type 1", "Type 2", "Type 3")
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if not components:
                return False, "No components provided"
            
            total_mass_fraction = sum(c.mass_fraction for c in components)
            tolerance = 1e-6
            
            if abs(total_mass_fraction - 1.0) > tolerance:
                return False, f"{fraction_type} mass fractions sum to {total_mass_fraction:.6f}, expected 1.0"
            
            # Check individual fractions are reasonable
            for comp in components:
                if comp.mass_fraction < 0:
                    return False, f"Negative mass fraction for {comp.material_name}: {comp.mass_fraction}"
                if comp.mass_fraction > 1.0:
                    return False, f"Mass fraction > 1.0 for {comp.material_name}: {comp.mass_fraction}"
                if comp.specific_gravity <= 0:
                    return False, f"Invalid specific gravity for {comp.material_name}: {comp.specific_gravity}"
            
            return True, "Validation passed"
            
        except Exception as e:
            return False, f"Validation error: {e}"
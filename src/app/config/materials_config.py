#!/usr/bin/env python3
"""
Materials Configuration for VCCTL

Manages default material properties and constants.
"""

from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class MaterialsConfig:
    """Configuration for material properties and defaults."""
    
    # Water properties
    water_density: float = 0.997  # g/cm³ at 25°C
    water_specific_gravity: float = 1.0
    
    # Cement properties (default values)
    cement_default_specific_gravity: float = 3.2
    cement_default_fineness: float = 370.0  # m²/kg
    cement_default_psd: str = "cement141"
    
    # Supplementary cementitious materials
    fly_ash_default_specific_gravity: float = 2.77
    slag_default_specific_gravity: float = 2.87
    silica_fume_default_specific_gravity: float = 2.2
    
    # Inert fillers
    inert_filler_default_specific_gravity: float = 3.0
    limestone_specific_gravity: float = 2.71
    quartz_specific_gravity: float = 2.65
    
    # Aggregate properties
    fine_aggregate_default_specific_gravity: float = 2.65
    coarse_aggregate_default_specific_gravity: float = 2.70
    aggregate_absorption_default: float = 1.0  # %
    
    # Hydration products
    ch_specific_gravity: float = 2.24  # Calcium hydroxide
    csh_specific_gravity: float = 2.1  # C-S-H gel
    ettringite_specific_gravity: float = 1.78
    monosulfate_specific_gravity: float = 2.02
    
    # Physical constants
    air_density: float = 0.001225  # g/cm³ at 20°C, 1 atm
    
    # Chemical composition limits (for validation)
    cement_composition_limits: Dict[str, tuple] = field(default_factory=lambda: {
        'c3s': (0.0, 0.8),      # Tricalcium silicate
        'c2s': (0.0, 0.4),      # Dicalcium silicate
        'c3a': (0.0, 0.15),     # Tricalcium aluminate
        'c4af': (0.0, 0.2),     # Tetracalcium aluminoferrite
        'gypsum': (0.0, 0.1),   # Gypsum content
        'so3': (0.0, 0.04),     # Sulfur trioxide
        'alkalis': (0.0, 0.01)  # Na₂O equivalent
    })
    
    # Particle size distribution limits
    psd_limits: Dict[str, tuple] = field(default_factory=lambda: {
        'cement_d10': (1.0, 5.0),      # μm
        'cement_d50': (10.0, 30.0),    # μm
        'cement_d90': (30.0, 100.0),   # μm
        'fly_ash_d50': (5.0, 50.0),    # μm
        'slag_d50': (8.0, 45.0)        # μm
    })
    
    @classmethod
    def create_default(cls) -> 'MaterialsConfig':
        """Create default materials configuration."""
        return cls()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MaterialsConfig':
        """Create materials configuration from dictionary."""
        return cls(
            water_density=data.get('water_density', 0.997),
            water_specific_gravity=data.get('water_specific_gravity', 1.0),
            cement_default_specific_gravity=data.get('cement_default_specific_gravity', 3.2),
            cement_default_fineness=data.get('cement_default_fineness', 370.0),
            cement_default_psd=data.get('cement_default_psd', 'cement141'),
            fly_ash_default_specific_gravity=data.get('fly_ash_default_specific_gravity', 2.77),
            slag_default_specific_gravity=data.get('slag_default_specific_gravity', 2.87),
            silica_fume_default_specific_gravity=data.get('silica_fume_default_specific_gravity', 2.2),
            inert_filler_default_specific_gravity=data.get('inert_filler_default_specific_gravity', 3.0),
            limestone_specific_gravity=data.get('limestone_specific_gravity', 2.71),
            quartz_specific_gravity=data.get('quartz_specific_gravity', 2.65),
            fine_aggregate_default_specific_gravity=data.get('fine_aggregate_default_specific_gravity', 2.65),
            coarse_aggregate_default_specific_gravity=data.get('coarse_aggregate_default_specific_gravity', 2.70),
            aggregate_absorption_default=data.get('aggregate_absorption_default', 1.0),
            ch_specific_gravity=data.get('ch_specific_gravity', 2.24),
            csh_specific_gravity=data.get('csh_specific_gravity', 2.1),
            ettringite_specific_gravity=data.get('ettringite_specific_gravity', 1.78),
            monosulfate_specific_gravity=data.get('monosulfate_specific_gravity', 2.02),
            air_density=data.get('air_density', 0.001225),
            cement_composition_limits=data.get('cement_composition_limits', {
                'c3s': (0.0, 0.8), 'c2s': (0.0, 0.4), 'c3a': (0.0, 0.15),
                'c4af': (0.0, 0.2), 'gypsum': (0.0, 0.1), 'so3': (0.0, 0.04),
                'alkalis': (0.0, 0.01)
            }),
            psd_limits=data.get('psd_limits', {
                'cement_d10': (1.0, 5.0), 'cement_d50': (10.0, 30.0),
                'cement_d90': (30.0, 100.0), 'fly_ash_d50': (5.0, 50.0),
                'slag_d50': (8.0, 45.0)
            })
        )
    
    def get_material_specific_gravity(self, material_type: str, material_name: str = None) -> float:
        """Get specific gravity for a material type."""
        material_type = material_type.lower()
        
        specific_gravities = {
            'cement': self.cement_default_specific_gravity,
            'fly_ash': self.fly_ash_default_specific_gravity,
            'slag': self.slag_default_specific_gravity,
            'silica_fume': self.silica_fume_default_specific_gravity,
            'inert_filler': self.inert_filler_default_specific_gravity,
            'limestone': self.limestone_specific_gravity,
            'quartz': self.quartz_specific_gravity,
            'fine_aggregate': self.fine_aggregate_default_specific_gravity,
            'coarse_aggregate': self.coarse_aggregate_default_specific_gravity,
            'water': self.water_specific_gravity,
            'ch': self.ch_specific_gravity,
            'csh': self.csh_specific_gravity,
            'ettringite': self.ettringite_specific_gravity,
            'monosulfate': self.monosulfate_specific_gravity
        }
        
        # Check for material name specific overrides
        if material_name:
            name_lower = material_name.lower()
            if 'limestone' in name_lower:
                return self.limestone_specific_gravity
            elif 'quartz' in name_lower:
                return self.quartz_specific_gravity
        
        return specific_gravities.get(material_type, 2.65)  # Default to aggregate SG
    
    def get_all_materials(self) -> Dict[str, Dict[str, Any]]:
        """Get all material properties as a dictionary."""
        return {
            'water': {
                'density': self.water_density,
                'specific_gravity': self.water_specific_gravity
            },
            'cement': {
                'specific_gravity': self.cement_default_specific_gravity,
                'fineness': self.cement_default_fineness,
                'psd': self.cement_default_psd
            },
            'fly_ash': {
                'specific_gravity': self.fly_ash_default_specific_gravity
            },
            'slag': {
                'specific_gravity': self.slag_default_specific_gravity
            },
            'silica_fume': {
                'specific_gravity': self.silica_fume_default_specific_gravity
            },
            'inert_filler': {
                'specific_gravity': self.inert_filler_default_specific_gravity
            },
            'limestone': {
                'specific_gravity': self.limestone_specific_gravity
            },
            'quartz': {
                'specific_gravity': self.quartz_specific_gravity
            },
            'fine_aggregate': {
                'specific_gravity': self.fine_aggregate_default_specific_gravity,
                'absorption': self.aggregate_absorption_default
            },
            'coarse_aggregate': {
                'specific_gravity': self.coarse_aggregate_default_specific_gravity,
                'absorption': self.aggregate_absorption_default
            },
            'hydration_products': {
                'ch': {'specific_gravity': self.ch_specific_gravity},
                'csh': {'specific_gravity': self.csh_specific_gravity},
                'ettringite': {'specific_gravity': self.ettringite_specific_gravity},
                'monosulfate': {'specific_gravity': self.monosulfate_specific_gravity}
            }
        }
    
    def validate_cement_composition(self, composition: Dict[str, float]) -> Dict[str, Any]:
        """Validate cement composition against limits."""
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Check individual component limits
        for component, value in composition.items():
            if component in self.cement_composition_limits:
                min_val, max_val = self.cement_composition_limits[component]
                if not (min_val <= value <= max_val):
                    validation_result['errors'].append(
                        f"{component} ({value:.3f}) outside valid range [{min_val:.3f}, {max_val:.3f}]"
                    )
                    validation_result['is_valid'] = False
        
        # Check total clinker phases
        clinker_phases = ['c3s', 'c2s', 'c3a', 'c4af']
        total_clinker = sum(composition.get(phase, 0) for phase in clinker_phases)
        
        if total_clinker > 1.0:
            validation_result['errors'].append(f"Total clinker phases ({total_clinker:.3f}) exceed 100%")
            validation_result['is_valid'] = False
        elif total_clinker < 0.85:
            validation_result['warnings'].append(f"Low total clinker content ({total_clinker:.1%})")
        
        # Check C3A + C4AF ratio for sulfate resistance
        c3a = composition.get('c3a', 0)
        c4af = composition.get('c4af', 0)
        if c3a + c4af > 0.2:
            validation_result['warnings'].append("High C3A + C4AF content may reduce sulfate resistance")
        
        return validation_result
    
    def validate_particle_size_distribution(self, material_type: str, 
                                          d10: float, d50: float, d90: float) -> Dict[str, Any]:
        """Validate particle size distribution parameters."""
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Check logical order
        if not (d10 <= d50 <= d90):
            validation_result['errors'].append("Particle sizes must satisfy: D10 ≤ D50 ≤ D90")
            validation_result['is_valid'] = False
            return validation_result
        
        # Check against material-specific limits
        material_type = material_type.lower()
        
        if material_type == 'cement':
            d10_limits = self.psd_limits.get('cement_d10', (1.0, 5.0))
            d50_limits = self.psd_limits.get('cement_d50', (10.0, 30.0))
            d90_limits = self.psd_limits.get('cement_d90', (30.0, 100.0))
            
            if not (d10_limits[0] <= d10 <= d10_limits[1]):
                validation_result['warnings'].append(f"Cement D10 ({d10:.1f}μm) outside typical range")
            if not (d50_limits[0] <= d50 <= d50_limits[1]):
                validation_result['warnings'].append(f"Cement D50 ({d50:.1f}μm) outside typical range")
            if not (d90_limits[0] <= d90 <= d90_limits[1]):
                validation_result['warnings'].append(f"Cement D90 ({d90:.1f}μm) outside typical range")
        
        elif material_type == 'fly_ash':
            d50_limits = self.psd_limits.get('fly_ash_d50', (5.0, 50.0))
            if not (d50_limits[0] <= d50 <= d50_limits[1]):
                validation_result['warnings'].append(f"Fly ash D50 ({d50:.1f}μm) outside typical range")
        
        elif material_type == 'slag':
            d50_limits = self.psd_limits.get('slag_d50', (8.0, 45.0))
            if not (d50_limits[0] <= d50 <= d50_limits[1]):
                validation_result['warnings'].append(f"Slag D50 ({d50:.1f}μm) outside typical range")
        
        # Check uniformity
        uniformity = d90 / d10 if d10 > 0 else float('inf')
        if uniformity > 10:
            validation_result['warnings'].append(f"High uniformity coefficient ({uniformity:.1f}) indicates wide size distribution")
        elif uniformity < 2:
            validation_result['warnings'].append(f"Low uniformity coefficient ({uniformity:.1f}) indicates narrow size distribution")
        
        return validation_result
    
    def validate(self) -> Dict[str, Any]:
        """Validate materials configuration."""
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Validate specific gravities
        sg_properties = [
            ('water_specific_gravity', self.water_specific_gravity, 0.99, 1.01),
            ('cement_default_specific_gravity', self.cement_default_specific_gravity, 2.8, 3.5),
            ('fly_ash_default_specific_gravity', self.fly_ash_default_specific_gravity, 2.0, 3.0),
            ('slag_default_specific_gravity', self.slag_default_specific_gravity, 2.5, 3.2),
            ('fine_aggregate_default_specific_gravity', self.fine_aggregate_default_specific_gravity, 2.3, 3.0),
            ('coarse_aggregate_default_specific_gravity', self.coarse_aggregate_default_specific_gravity, 2.3, 3.0)
        ]
        
        for prop_name, value, min_val, max_val in sg_properties:
            if not (min_val <= value <= max_val):
                validation_result['errors'].append(
                    f"{prop_name} ({value:.3f}) outside reasonable range [{min_val:.3f}, {max_val:.3f}]"
                )
                validation_result['is_valid'] = False
        
        # Validate densities
        if not (0.99 <= self.water_density <= 1.01):
            validation_result['errors'].append(f"Water density ({self.water_density:.3f}) outside valid range")
            validation_result['is_valid'] = False
        
        # Validate fineness
        if not (200 <= self.cement_default_fineness <= 600):
            validation_result['warnings'].append(
                f"Cement fineness ({self.cement_default_fineness:.0f} m²/kg) outside typical range [200, 600]"
            )
        
        # Validate absorption
        if not (0.1 <= self.aggregate_absorption_default <= 5.0):
            validation_result['warnings'].append(
                f"Aggregate absorption ({self.aggregate_absorption_default:.1f}%) outside typical range [0.1, 5.0]"
            )
        
        return validation_result
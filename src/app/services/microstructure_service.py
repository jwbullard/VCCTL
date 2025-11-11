#!/usr/bin/env python3
"""
Microstructure Service for VCCTL

Provides business logic for 3D microstructure generation and parameter management.
Converted from Java Spring service to Python.
"""

import logging
import math
import os
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np

from app.database.service import DatabaseService
from app.services.base_service import ServiceError, ValidationError


class PhaseType(Enum):
    """Phase types in VCCTL microstructure."""
    # Clinker phases
    C3S = "C3S"              # Tricalcium silicate
    C2S = "C2S"              # Dicalcium silicate  
    C3A = "C3A"              # Tricalcium aluminate
    C4AF = "C4AF"            # Tetracalcium aluminoferrite
    
    # Hydration products
    CH = "CH"                # Calcium hydroxide (Portlandite)
    CSH = "C-S-H"           # Calcium silicate hydrate
    ETTRINGITE = "AFt"       # Ettringite
    MONOSULFATE = "AFm"      # Monosulfate
    
    # Supplementary materials
    FLYASH = "FA"            # Fly ash
    SLAG = "SG"              # Slag
    SILICA_FUME = "SF"       # Silica fume
    
    # Aggregates and fillers
    AGGREGATE = "AGG"        # Aggregate
    FILLER = "INERT"   # Filler
    
    # Pores and water
    WATER = "WATER"          # Capillary water
    PORE = "PORE"           # Capillary pore
    AIR = "AIR"             # Air void


@dataclass
class PhaseProperties:
    """Properties of a phase in the microstructure."""
    phase_type: PhaseType
    volume_fraction: float = 0.0
    specific_gravity: float = 0.0
    color_rgb: Tuple[int, int, int] = (128, 128, 128)
    
    def __post_init__(self):
        """Validate phase properties."""
        if not (0 <= self.volume_fraction <= 1):
            raise ValueError("Volume fraction must be between 0 and 1")
        if self.specific_gravity < 0:
            raise ValueError("Specific gravity must be non-negative")


@dataclass
class MicrostructureParams:
    """Parameters for microstructure generation."""
    system_size: int = 100           # Voxels per dimension
    resolution: float = 1.0          # Micrometers per voxel
    water_binder_ratio: float = 0.4  # Water to binder ratio
    aggregate_volume_fraction: float = 0.7  # Aggregate volume fraction
    air_content: float = 0.05        # Air content fraction
    
    # Particle shape parameters
    cement_shape_set: str = "sphere"
    aggregate_shape_set: str = "sphere"
    
    # Flocculation parameters
    flocculation_enabled: bool = False
    flocculation_degree: float = 0.0
    
    def __post_init__(self):
        """Validate microstructure parameters."""
        if self.system_size <= 0 or self.system_size > 1000:
            raise ValueError("System size must be between 1 and 1000 voxels")
        if self.resolution <= 0 or self.resolution > 100:
            raise ValueError("Resolution must be between 0 and 100 micrometers")
        if not (0 <= self.water_binder_ratio <= 2.0):
            raise ValueError("Water-binder ratio must be between 0 and 2.0")
        if not (0 <= self.aggregate_volume_fraction <= 1.0):
            raise ValueError("Aggregate volume fraction must be between 0 and 1.0")
        if not (0 <= self.air_content <= 0.2):
            raise ValueError("Air content must be between 0 and 20%")


@dataclass
class ParticleSizeDistribution:
    """Particle size distribution data."""
    diameters: List[float]      # Particle diameters in micrometers
    mass_fractions: List[float] # Mass fraction for each size class
    
    def __post_init__(self):
        """Validate PSD data."""
        if len(self.diameters) != len(self.mass_fractions):
            raise ValueError("Diameters and mass fractions must have same length")
        if abs(sum(self.mass_fractions) - 1.0) > 0.001:
            raise ValueError("Mass fractions must sum to 1.0")
        if any(d <= 0 for d in self.diameters):
            raise ValueError("All diameters must be positive")
        if any(f < 0 for f in self.mass_fractions):
            raise ValueError("All mass fractions must be non-negative")


class MicrostructureService:
    """
    Service for managing 3D microstructure generation and parameters.
    
    Provides microstructure parameter validation, phase volume calculations,
    and 3D structure generation support for the VCCTL system.
    """
    
    def __init__(self, db_service: DatabaseService, config_manager=None):
        self.db_service = db_service
        self.config_manager = config_manager
        self.logger = logging.getLogger('VCCTL.MicrostructureService')

        # Default phase properties
        self.default_phase_properties = self._initialize_default_phases()

        # Base paths for particle shape set and aggregate data
        if config_manager:
            self.particle_shape_base_path = str(config_manager.directories.particle_shape_set_path)
            self.aggregate_shape_base_path = str(config_manager.directories.aggregate_path)
        else:
            # Fallback for tests
            self.particle_shape_base_path = os.path.join(os.getcwd(), "particle_shape_set")
            self.aggregate_shape_base_path = os.path.join(os.getcwd(), "aggregate")

        # Lazy loading - don't load shape sets until first access
        self._shape_sets = None
        self._aggregate_shapes = None
    
    def _load_particle_shape_sets(self) -> Dict[str, str]:
        """Load available particle shape sets from particle_shape_set directory."""
        shape_sets = {}
        
        # Always include spherical - it's mathematical, doesn't need files
        shape_sets["sphere"] = "Spherical particles"

        # Dynamically discover all directories in particle_shape_set
        if os.path.exists(self.particle_shape_base_path):
            try:
                for item in os.listdir(self.particle_shape_base_path):
                    item_path = os.path.join(self.particle_shape_base_path, item)
                    if os.path.isdir(item_path):
                        # Use the folder name as both ID and description
                        shape_sets[item] = f"{item.title()} particles"
                        self.logger.info(f"Found particle shape set: {item}")
            except Exception as e:
                self.logger.error(f"Failed to scan particle_shape_set directory: {e}")
        else:
            self.logger.warning(f"Particle shape set directory not found: {self.particle_shape_base_path}")

        return shape_sets
    
    def get_particle_shape_set_path(self, shape_set_name: str) -> Optional[str]:
        """Get the full path to a particle shape set directory."""
        if shape_set_name not in self.shape_sets:
            return None
        
        # Sphere is mathematical and doesn't need file paths
        if shape_set_name == "sphere":
            return None
            
        shape_path = os.path.join(self.particle_shape_base_path, shape_set_name)
        if os.path.exists(shape_path) and os.path.isdir(shape_path):
            return shape_path
        
        return None
    
    def get_particle_shape_files(self, shape_set_name: str) -> List[str]:
        """Get list of particle shape data files for a given shape set."""
        shape_path = self.get_particle_shape_set_path(shape_set_name)
        if not shape_path:
            return []
        
        try:
            files = []
            for filename in os.listdir(shape_path):
                if filename.endswith('.dat'):
                    files.append(os.path.join(shape_path, filename))
            return sorted(files)
        except Exception as e:
            self.logger.error(f"Failed to read particle shape files for {shape_set_name}: {e}")
            return []
    
    def is_mathematical_shape_set(self, shape_set_name: str) -> bool:
        """Check if a shape set is mathematical (doesn't require data files)."""
        return shape_set_name == "sphere"
    
    def _load_aggregate_shapes(self) -> Dict[str, str]:
        """Load available aggregate shapes from aggregate directory."""
        aggregate_shapes = {}

        # Always include spherical - it's mathematical, doesn't need files
        aggregate_shapes["sphere"] = "Spherical particles"

        # Dynamically discover all directories in aggregate
        if os.path.exists(self.aggregate_shape_base_path):
            try:
                for item in os.listdir(self.aggregate_shape_base_path):
                    item_path = os.path.join(self.aggregate_shape_base_path, item)
                    if os.path.isdir(item_path):
                        # Use the folder name as both ID and description
                        aggregate_shapes[item] = f"{item.title()} aggregate"
                        self.logger.info(f"Found aggregate shape: {item}")
            except Exception as e:
                self.logger.error(f"Failed to scan aggregate directory: {e}")
        else:
            self.logger.warning(f"Aggregate directory not found: {self.aggregate_shape_base_path}")

        return aggregate_shapes
    
    def get_aggregate_shape_path(self, shape_name: str) -> Optional[str]:
        """Get the full path to an aggregate shape directory."""
        if shape_name not in self.aggregate_shapes:
            return None
        
        # Sphere is mathematical and doesn't need file paths
        if shape_name == "sphere":
            return None
            
        shape_path = os.path.join(self.aggregate_shape_base_path, shape_name)
        if os.path.exists(shape_path) and os.path.isdir(shape_path):
            return shape_path
        
        return None
    
    def get_aggregate_shape_files(self, shape_name: str) -> List[str]:
        """Get list of aggregate shape data files for a given shape."""
        shape_path = self.get_aggregate_shape_path(shape_name)
        if not shape_path:
            return []
        
        try:
            files = []
            for filename in os.listdir(shape_path):
                if filename.endswith('.dat'):
                    files.append(os.path.join(shape_path, filename))
            return sorted(files)
        except Exception as e:
            self.logger.error(f"Failed to read aggregate shape files for {shape_name}: {e}")
            return []
    
    def is_mathematical_aggregate_shape(self, shape_name: str) -> bool:
        """Check if an aggregate shape is mathematical (doesn't require data files)."""
        return shape_name == "sphere"
    
    def get_supported_aggregate_shapes(self) -> Dict[str, str]:
        """Get list of supported aggregate shapes."""
        return self.aggregate_shapes.copy()
    
    def get_fine_aggregate_shapes(self) -> Dict[str, str]:
        """Get list of fine aggregate shapes (containing 'fine' in name or general shapes)."""
        fine_shapes = {}
        
        # Always include sphere for fine aggregates
        fine_shapes["sphere"] = "Spherical particles"
        
        # Include shapes with 'fine' in the name
        for shape_id, shape_desc in self.aggregate_shapes.items():
            if 'fine' in shape_id.lower():
                fine_shapes[shape_id] = shape_desc
        
        # Include general shapes that don't specify fine/coarse
        general_shapes = ['Ottawa-sand', 'SiamSand', 'Cubic', 'spheres']
        for shape_id, shape_desc in self.aggregate_shapes.items():
            if shape_id in general_shapes:
                fine_shapes[shape_id] = shape_desc
        
        return fine_shapes
    
    def get_coarse_aggregate_shapes(self) -> Dict[str, str]:
        """Get list of coarse aggregate shapes (containing 'coarse' in name or general shapes)."""
        coarse_shapes = {}
        
        # Always include sphere for coarse aggregates
        coarse_shapes["sphere"] = "Spherical particles"
        
        # Include shapes with 'coarse' in the name
        for shape_id, shape_desc in self.aggregate_shapes.items():
            if 'coarse' in shape_id.lower():
                coarse_shapes[shape_id] = shape_desc
        
        # Include general shapes that don't specify fine/coarse
        general_shapes = ['FDOT-57', 'Cubic', 'spheres', 'Slab']
        for shape_id, shape_desc in self.aggregate_shapes.items():
            if shape_id in general_shapes:
                coarse_shapes[shape_id] = shape_desc
        
        return coarse_shapes

    def _initialize_default_phases(self) -> Dict[PhaseType, PhaseProperties]:
        """Initialize default phase properties."""
        return {
            PhaseType.C3S: PhaseProperties(PhaseType.C3S, 0.0, 3.15, (255, 0, 0)),      # Red
            PhaseType.C2S: PhaseProperties(PhaseType.C2S, 0.0, 3.28, (0, 255, 0)),      # Green  
            PhaseType.C3A: PhaseProperties(PhaseType.C3A, 0.0, 3.04, (0, 0, 255)),      # Blue
            PhaseType.C4AF: PhaseProperties(PhaseType.C4AF, 0.0, 3.73, (255, 255, 0)),  # Yellow
            PhaseType.CH: PhaseProperties(PhaseType.CH, 0.0, 2.24, (255, 0, 255)),      # Magenta
            PhaseType.CSH: PhaseProperties(PhaseType.CSH, 0.0, 2.1, (0, 255, 255)),     # Cyan
            PhaseType.ETTRINGITE: PhaseProperties(PhaseType.ETTRINGITE, 0.0, 1.78, (128, 0, 128)), # Purple
            PhaseType.FLYASH: PhaseProperties(PhaseType.FLYASH, 0.0, 2.77, (255, 128, 0)),  # Orange
            PhaseType.SLAG: PhaseProperties(PhaseType.SLAG, 0.0, 2.87, (128, 255, 0)),   # Light green
            PhaseType.AGGREGATE: PhaseProperties(PhaseType.AGGREGATE, 0.0, 2.65, (64, 64, 64)), # Dark gray
            PhaseType.WATER: PhaseProperties(PhaseType.WATER, 0.0, 1.0, (0, 0, 128)),    # Dark blue
            PhaseType.PORE: PhaseProperties(PhaseType.PORE, 0.0, 0.0, (0, 0, 0)),        # Black
            PhaseType.AIR: PhaseProperties(PhaseType.AIR, 0.0, 0.0, (255, 255, 255))     # White
        }
    
    def create_microstructure_parameters(self, params_data: Dict[str, Any]) -> MicrostructureParams:
        """Create and validate microstructure parameters."""
        try:
            params = MicrostructureParams(
                system_size=params_data.get('system_size', 100),
                resolution=params_data.get('resolution', 1.0),
                water_binder_ratio=params_data.get('water_binder_ratio', 0.4),
                aggregate_volume_fraction=params_data.get('aggregate_volume_fraction', 0.7),
                air_content=params_data.get('air_content', 0.05),
                cement_shape_set=params_data.get('cement_shape_set', 'sphere'),
                aggregate_shape_set=params_data.get('aggregate_shape_set', 'sphere'),
                flocculation_enabled=params_data.get('flocculation_enabled', False),
                flocculation_degree=params_data.get('flocculation_degree', 0.0)
            )
            
            # Validate shape sets
            self._validate_shape_sets(params)
            
            self.logger.info(f"Created microstructure parameters: {params.system_size}³ voxels")
            return params
            
        except Exception as e:
            self.logger.error(f"Failed to create microstructure parameters: {e}")
            raise ServiceError(f"Failed to create microstructure parameters: {e}")
    
    def _validate_shape_sets(self, params: MicrostructureParams) -> None:
        """Validate shape set parameters."""
        if params.cement_shape_set not in self.shape_sets:
            raise ValidationError(f"Invalid cement shape set: {params.cement_shape_set}")
        
        if params.aggregate_shape_set not in self.shape_sets:
            raise ValidationError(f"Invalid aggregate shape set: {params.aggregate_shape_set}")
        
        if params.flocculation_enabled and not (0 <= params.flocculation_degree <= 1):
            raise ValidationError("Flocculation degree must be between 0 and 1")
    
    def calculate_phase_volumes(self, mix_components: List[Dict[str, Any]], 
                              params: MicrostructureParams) -> Dict[PhaseType, float]:
        """Calculate phase volume fractions from mix components."""
        try:
            phase_volumes = {}
            total_solid_volume = 0.0
            
            # Calculate volumes for each material component
            for component in mix_components:
                material_type = component.get('material_type', '')
                mass_fraction = component.get('mass_fraction', 0.0)
                specific_gravity = component.get('specific_gravity', 2.65)
                
                # Convert mass fraction to volume fraction
                volume_fraction = mass_fraction / specific_gravity
                total_solid_volume += volume_fraction
                
                # Map material type to phase type
                phase_type = self._map_material_to_phase(material_type)
                if phase_type:
                    phase_volumes[phase_type] = phase_volumes.get(phase_type, 0.0) + volume_fraction
            
            # Normalize solid phase volumes
            if total_solid_volume > 0:
                solid_scale_factor = (1.0 - params.air_content) / total_solid_volume
                for phase_type in phase_volumes:
                    phase_volumes[phase_type] *= solid_scale_factor
            
            # Add water phase
            water_volume = self._calculate_water_volume(mix_components, params)
            phase_volumes[PhaseType.WATER] = water_volume
            
            # Add air phase
            phase_volumes[PhaseType.AIR] = params.air_content
            
            # Calculate remaining pore space
            total_volume = sum(phase_volumes.values())
            if total_volume < 1.0:
                phase_volumes[PhaseType.PORE] = 1.0 - total_volume
            
            self._validate_phase_volumes(phase_volumes)
            
            return phase_volumes
            
        except Exception as e:
            self.logger.error(f"Failed to calculate phase volumes: {e}")
            raise ServiceError(f"Phase volume calculation failed: {e}")
    
    def _map_material_to_phase(self, material_type: str) -> Optional[PhaseType]:
        """Map material type string to phase type."""
        mapping = {
            'cement': PhaseType.C3S,      # Simplified - real cement has multiple phases
            'fly_ash': PhaseType.FLYASH,
            'slag': PhaseType.SLAG,
            'silica_fume': PhaseType.SILICA_FUME,
            'aggregate': PhaseType.AGGREGATE,
            'filler': PhaseType.FILLER
        }
        return mapping.get(material_type.lower())
    
    def _calculate_water_volume(self, mix_components: List[Dict[str, Any]], 
                               params: MicrostructureParams) -> float:
        """Calculate water volume fraction."""
        # Find total binder mass
        binder_types = {'cement', 'fly_ash', 'slag', 'silica_fume'}
        total_binder_mass = sum(
            comp.get('mass_fraction', 0.0) 
            for comp in mix_components 
            if comp.get('material_type', '').lower() in binder_types
        )
        
        # Calculate water mass and convert to volume
        water_mass = params.water_binder_ratio * total_binder_mass
        water_volume = water_mass / 1.0  # Specific gravity of water = 1.0
        
        return water_volume
    
    def _validate_phase_volumes(self, phase_volumes: Dict[PhaseType, float]) -> None:
        """Validate calculated phase volumes."""
        total_volume = sum(phase_volumes.values())
        
        if abs(total_volume - 1.0) > 0.001:
            raise ValidationError(f"Total phase volumes must sum to 1.0, got {total_volume:.6f}")
        
        for phase_type, volume in phase_volumes.items():
            if volume < 0:
                raise ValidationError(f"Phase {phase_type.value} has negative volume: {volume}")
            if volume > 1:
                raise ValidationError(f"Phase {phase_type.value} volume exceeds 1.0: {volume}")
    
    def generate_particle_size_distribution(self, mean_diameter: float, 
                                           std_deviation: float, 
                                           num_size_classes: int = 20) -> ParticleSizeDistribution:
        """Generate log-normal particle size distribution."""
        try:
            if mean_diameter <= 0:
                raise ValidationError("Mean diameter must be positive")
            if std_deviation <= 0:
                raise ValidationError("Standard deviation must be positive")
            if num_size_classes < 2:
                raise ValidationError("Number of size classes must be at least 2")
            
            # Generate diameter range (log-normal distribution)
            log_mean = math.log(mean_diameter)
            log_std = math.log(1 + std_deviation / mean_diameter)
            
            # Create size class boundaries
            min_log_d = log_mean - 3 * log_std
            max_log_d = log_mean + 3 * log_std
            
            log_diameters = np.linspace(min_log_d, max_log_d, num_size_classes)
            diameters = [math.exp(log_d) for log_d in log_diameters]
            
            # Calculate mass fractions for log-normal distribution
            mass_fractions = []
            for i, diameter in enumerate(diameters):
                if i == 0:
                    lower_bound = -float('inf')
                else:
                    lower_bound = (log_diameters[i-1] + log_diameters[i]) / 2
                
                if i == len(diameters) - 1:
                    upper_bound = float('inf')
                else:
                    upper_bound = (log_diameters[i] + log_diameters[i+1]) / 2
                
                # Calculate cumulative probability
                prob_lower = self._log_normal_cdf(lower_bound, log_mean, log_std)
                prob_upper = self._log_normal_cdf(upper_bound, log_mean, log_std)
                
                mass_fraction = prob_upper - prob_lower
                mass_fractions.append(mass_fraction)
            
            # Normalize mass fractions
            total_mass = sum(mass_fractions)
            if total_mass > 0:
                mass_fractions = [f / total_mass for f in mass_fractions]
            
            psd = ParticleSizeDistribution(diameters, mass_fractions)
            
            self.logger.info(f"Generated PSD with {num_size_classes} size classes")
            return psd
            
        except Exception as e:
            self.logger.error(f"Failed to generate particle size distribution: {e}")
            raise ServiceError(f"PSD generation failed: {e}")
    
    def _log_normal_cdf(self, x: float, mu: float, sigma: float) -> float:
        """Calculate cumulative distribution function for log-normal distribution."""
        if x == -float('inf'):
            return 0.0
        if x == float('inf'):
            return 1.0
        
        # Use error function for normal CDF
        z = (x - mu) / (sigma * math.sqrt(2))
        return 0.5 * (1 + math.erf(z))
    
    def calculate_system_volume(self, params: MicrostructureParams) -> Dict[str, float]:
        """Calculate system volume information."""
        try:
            total_voxels = params.system_size ** 3
            voxel_volume_um3 = params.resolution ** 3
            total_volume_um3 = total_voxels * voxel_volume_um3
            
            # Convert to different units
            total_volume_mm3 = total_volume_um3 / 1e9
            total_volume_cm3 = total_volume_mm3 / 1e3
            
            return {
                'total_voxels': total_voxels,
                'voxel_volume_um3': voxel_volume_um3,
                'total_volume_um3': total_volume_um3,
                'total_volume_mm3': total_volume_mm3,
                'total_volume_cm3': total_volume_cm3,
                'system_size_um': params.system_size * params.resolution
            }
            
        except Exception as e:
            self.logger.error(f"Failed to calculate system volume: {e}")
            raise ServiceError(f"System volume calculation failed: {e}")
    
    def validate_microstructure_feasibility(self, params: MicrostructureParams, 
                                          phase_volumes: Dict[PhaseType, float]) -> Dict[str, Any]:
        """Validate that microstructure parameters are feasible."""
        validation_result = {
            'is_feasible': True,
            'warnings': [],
            'errors': [],
            'recommendations': []
        }
        
        try:
            # Check system size vs resolution
            system_size_um = params.system_size * params.resolution
            if system_size_um < 50:
                validation_result['warnings'].append("Very small system size (<50 μm) may not be representative")
            elif system_size_um > 1000:
                validation_result['warnings'].append("Large system size (>1000 μm) will require significant computation")
            
            # Check resolution vs particle sizes
            if params.resolution > 5.0:
                validation_result['warnings'].append("Coarse resolution (>5 μm) may miss fine details")
            elif params.resolution < 0.1:
                validation_result['warnings'].append("Very fine resolution (<0.1 μm) will be computationally expensive")
            
            # Check phase volume reasonableness
            aggregate_volume = phase_volumes.get(PhaseType.AGGREGATE, 0.0)
            if aggregate_volume > 0.8:
                validation_result['warnings'].append("Very high aggregate content (>80%) may be difficult to achieve")
            elif aggregate_volume < 0.3:
                validation_result['warnings'].append("Low aggregate content (<30%) may affect concrete properties")
            
            # Check air content
            air_volume = phase_volumes.get(PhaseType.AIR, 0.0)
            if air_volume > 0.1:
                validation_result['warnings'].append("High air content (>10%) will significantly affect strength")
            
            # Check water content
            water_volume = phase_volumes.get(PhaseType.WATER, 0.0)
            if water_volume < 0.1:
                validation_result['warnings'].append("Very low water content may cause hydration issues")
            elif water_volume > 0.3:
                validation_result['warnings'].append("High water content may cause segregation")
            
            # Check computational requirements
            total_voxels = params.system_size ** 3
            if total_voxels > 500**3:
                validation_result['warnings'].append("Large system (>125M voxels) will require significant memory")
            
            return validation_result
            
        except Exception as e:
            self.logger.error(f"Failed to validate microstructure feasibility: {e}")
            validation_result['errors'].append(f"Validation failed: {e}")
            validation_result['is_feasible'] = False
            return validation_result
    
    @property
    def shape_sets(self) -> Dict[str, str]:
        """Get shape sets with lazy loading."""
        if self._shape_sets is None:
            # Ensure bundled data is copied before loading
            if self.config_manager:
                from app.services.service_container import service_container
                service_container.directories_service.copy_bundled_data_if_needed()

            self._shape_sets = self._load_particle_shape_sets()
        return self._shape_sets

    @property
    def aggregate_shapes(self) -> Dict[str, str]:
        """Get aggregate shapes with lazy loading."""
        if self._aggregate_shapes is None:
            # Ensure bundled data is copied before loading
            if self.config_manager:
                from app.services.service_container import service_container
                service_container.directories_service.copy_bundled_data_if_needed()

            self._aggregate_shapes = self._load_aggregate_shapes()
        return self._aggregate_shapes

    def get_supported_shape_sets(self) -> Dict[str, str]:
        """Get list of supported particle shape sets."""
        return self.shape_sets.copy()

    def refresh_shape_sets(self) -> None:
        """Refresh particle and aggregate shape sets from disk.

        Call this after extraction completes to reload the available shape sets.
        """
        self.logger.info("Refreshing particle and aggregate shape sets from disk")
        self._shape_sets = None
        self._aggregate_shapes = None
        # Force reload by accessing properties
        _ = self.shape_sets
        _ = self.aggregate_shapes
        self.logger.info(f"Shape sets refreshed: {len(self._shape_sets)} particle sets, {len(self._aggregate_shapes)} aggregate sets")

    def get_default_phase_properties(self) -> Dict[PhaseType, PhaseProperties]:
        """Get default phase properties."""
        return self.default_phase_properties.copy()
    
    def estimate_computation_time(self, params: MicrostructureParams) -> Dict[str, float]:
        """Estimate computation time for microstructure generation."""
        try:
            total_voxels = params.system_size ** 3
            
            # Empirical time estimates (in seconds)
            # These are rough estimates and would need calibration
            base_time_per_million_voxels = 60  # 1 minute per million voxels
            
            estimated_time_seconds = (total_voxels / 1e6) * base_time_per_million_voxels
            
            # Adjustments for complexity
            if params.flocculation_enabled:
                estimated_time_seconds *= 1.5  # Flocculation increases complexity
            
            if params.resolution < 0.5:
                estimated_time_seconds *= 2.0  # Fine resolution is slower
            
            return {
                'estimated_time_seconds': estimated_time_seconds,
                'estimated_time_minutes': estimated_time_seconds / 60,
                'estimated_time_hours': estimated_time_seconds / 3600,
                'total_voxels': total_voxels,
                'complexity_factors': {
                    'flocculation': params.flocculation_enabled,
                    'fine_resolution': params.resolution < 0.5
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to estimate computation time: {e}")
            raise ServiceError(f"Computation time estimation failed: {e}")
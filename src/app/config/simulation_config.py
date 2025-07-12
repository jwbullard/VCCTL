#!/usr/bin/env python3
"""
Simulation Configuration for VCCTL

Manages simulation parameters and default settings.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List


@dataclass
class SimulationConfig:
    """Configuration for simulation parameters and defaults."""
    
    # Hydration simulation
    default_hydration_cycles: int = 2000
    max_hydration_cycles: int = 100000
    default_temperature: float = 25.0  # Celsius
    default_water_binder_ratio: float = 0.4
    
    # Microstructure generation
    default_system_size: int = 100  # voxels per dimension
    max_system_size: int = 1000
    default_resolution: float = 1.0  # micrometers per voxel
    min_resolution: float = 0.1
    max_resolution: float = 10.0
    
    # Aggregate parameters
    default_aggregate_volume_fraction: float = 0.7
    max_aggregate_volume_fraction: float = 0.85
    default_maximum_aggregate_size: float = 25.0  # mm
    
    # Air content
    default_air_content: float = 0.05  # 5%
    max_air_content: float = 0.15  # 15%
    
    # Particle shape sets
    available_particle_shapes: List[str] = field(default_factory=lambda: [
        "sphere", "ellipsoid", "irregular", "angular"
    ])
    default_cement_shape: str = "sphere"
    default_aggregate_shape: str = "sphere"
    
    # Flocculation parameters
    flocculation_enabled: bool = False
    default_flocculation_degree: float = 0.0
    max_flocculation_degree: float = 1.0
    
    # Elasticity calculations
    elasticity_enabled: bool = True
    default_youngs_modulus_cement: float = 20000.0  # MPa
    default_youngs_modulus_aggregate: float = 70000.0  # MPa
    default_poissons_ratio_cement: float = 0.25
    default_poissons_ratio_aggregate: float = 0.20
    
    # Transport properties
    transport_enabled: bool = True
    default_diffusivity_water: float = 2.3e-9  # m²/s
    default_permeability: float = 1e-18  # m²
    
    # Convergence criteria
    hydration_convergence_tolerance: float = 1e-6
    elastic_convergence_tolerance: float = 1e-8
    max_iterations: int = 1000
    
    # Performance settings
    parallel_processing_enabled: bool = True
    max_worker_threads: int = 4
    memory_limit_per_simulation: int = 2048  # MB
    checkpoint_interval: int = 100  # cycles
    
    # Output settings
    save_intermediate_results: bool = False
    output_format: str = "hdf5"  # or "csv", "json"
    compression_enabled: bool = True
    
    @classmethod
    def create_default(cls) -> 'SimulationConfig':
        """Create default simulation configuration."""
        return cls()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SimulationConfig':
        """Create simulation configuration from dictionary."""
        return cls(
            default_hydration_cycles=data.get('default_hydration_cycles', 2000),
            max_hydration_cycles=data.get('max_hydration_cycles', 100000),
            default_temperature=data.get('default_temperature', 25.0),
            default_water_binder_ratio=data.get('default_water_binder_ratio', 0.4),
            default_system_size=data.get('default_system_size', 100),
            max_system_size=data.get('max_system_size', 1000),
            default_resolution=data.get('default_resolution', 1.0),
            min_resolution=data.get('min_resolution', 0.1),
            max_resolution=data.get('max_resolution', 10.0),
            default_aggregate_volume_fraction=data.get('default_aggregate_volume_fraction', 0.7),
            max_aggregate_volume_fraction=data.get('max_aggregate_volume_fraction', 0.85),
            default_maximum_aggregate_size=data.get('default_maximum_aggregate_size', 25.0),
            default_air_content=data.get('default_air_content', 0.05),
            max_air_content=data.get('max_air_content', 0.15),
            available_particle_shapes=data.get('available_particle_shapes', 
                                            ["sphere", "ellipsoid", "irregular", "angular"]),
            default_cement_shape=data.get('default_cement_shape', "sphere"),
            default_aggregate_shape=data.get('default_aggregate_shape', "sphere"),
            flocculation_enabled=data.get('flocculation_enabled', False),
            default_flocculation_degree=data.get('default_flocculation_degree', 0.0),
            max_flocculation_degree=data.get('max_flocculation_degree', 1.0),
            elasticity_enabled=data.get('elasticity_enabled', True),
            default_youngs_modulus_cement=data.get('default_youngs_modulus_cement', 20000.0),
            default_youngs_modulus_aggregate=data.get('default_youngs_modulus_aggregate', 70000.0),
            default_poissons_ratio_cement=data.get('default_poissons_ratio_cement', 0.25),
            default_poissons_ratio_aggregate=data.get('default_poissons_ratio_aggregate', 0.20),
            transport_enabled=data.get('transport_enabled', True),
            default_diffusivity_water=data.get('default_diffusivity_water', 2.3e-9),
            default_permeability=data.get('default_permeability', 1e-18),
            hydration_convergence_tolerance=data.get('hydration_convergence_tolerance', 1e-6),
            elastic_convergence_tolerance=data.get('elastic_convergence_tolerance', 1e-8),
            max_iterations=data.get('max_iterations', 1000),
            parallel_processing_enabled=data.get('parallel_processing_enabled', True),
            max_worker_threads=data.get('max_worker_threads', 4),
            memory_limit_per_simulation=data.get('memory_limit_per_simulation', 2048),
            checkpoint_interval=data.get('checkpoint_interval', 100),
            save_intermediate_results=data.get('save_intermediate_results', False),
            output_format=data.get('output_format', "hdf5"),
            compression_enabled=data.get('compression_enabled', True)
        )
    
    def get_hydration_parameters(self) -> Dict[str, Any]:
        """Get hydration simulation parameters."""
        return {
            'cycles': self.default_hydration_cycles,
            'temperature': self.default_temperature,
            'water_binder_ratio': self.default_water_binder_ratio,
            'convergence_tolerance': self.hydration_convergence_tolerance,
            'checkpoint_interval': self.checkpoint_interval
        }
    
    def get_microstructure_parameters(self) -> Dict[str, Any]:
        """Get microstructure generation parameters."""
        return {
            'system_size': self.default_system_size,
            'resolution': self.default_resolution,
            'aggregate_volume_fraction': self.default_aggregate_volume_fraction,
            'air_content': self.default_air_content,
            'cement_shape': self.default_cement_shape,
            'aggregate_shape': self.default_aggregate_shape,
            'flocculation_enabled': self.flocculation_enabled,
            'flocculation_degree': self.default_flocculation_degree
        }
    
    def get_elasticity_parameters(self) -> Dict[str, Any]:
        """Get elasticity calculation parameters."""
        return {
            'enabled': self.elasticity_enabled,
            'youngs_modulus_cement': self.default_youngs_modulus_cement,
            'youngs_modulus_aggregate': self.default_youngs_modulus_aggregate,
            'poissons_ratio_cement': self.default_poissons_ratio_cement,
            'poissons_ratio_aggregate': self.default_poissons_ratio_aggregate,
            'convergence_tolerance': self.elastic_convergence_tolerance,
            'max_iterations': self.max_iterations
        }
    
    def get_transport_parameters(self) -> Dict[str, Any]:
        """Get transport property parameters."""
        return {
            'enabled': self.transport_enabled,
            'diffusivity_water': self.default_diffusivity_water,
            'permeability': self.default_permeability
        }
    
    def get_performance_parameters(self) -> Dict[str, Any]:
        """Get performance and computational parameters."""
        return {
            'parallel_processing': self.parallel_processing_enabled,
            'max_threads': self.max_worker_threads,
            'memory_limit_mb': self.memory_limit_per_simulation,
            'checkpoint_interval': self.checkpoint_interval
        }
    
    def estimate_computation_time(self, system_size: int, cycles: int) -> Dict[str, float]:
        """Estimate computation time for given parameters."""
        # Empirical time estimation (would need calibration with real data)
        voxels = system_size ** 3
        
        # Base time per million voxels per 100 cycles (in seconds)
        base_time_per_mvoxel_per_100cycles = 30
        
        # Scale by voxels and cycles
        estimated_seconds = (voxels / 1e6) * (cycles / 100) * base_time_per_mvoxel_per_100cycles
        
        # Adjust for parallel processing
        if self.parallel_processing_enabled and self.max_worker_threads > 1:
            parallel_efficiency = min(0.8, 0.6 + 0.05 * self.max_worker_threads)
            estimated_seconds = estimated_seconds / (self.max_worker_threads * parallel_efficiency)
        
        return {
            'estimated_seconds': estimated_seconds,
            'estimated_minutes': estimated_seconds / 60,
            'estimated_hours': estimated_seconds / 3600,
            'total_voxels': voxels,
            'cycles': cycles,
            'parallel_speedup': self.max_worker_threads if self.parallel_processing_enabled else 1
        }
    
    def estimate_memory_usage(self, system_size: int) -> Dict[str, float]:
        """Estimate memory usage for given system size."""
        voxels = system_size ** 3
        
        # Estimate bytes per voxel (typical for microstructure data)
        bytes_per_voxel = 8  # Phase ID + properties
        
        # Base memory usage
        base_memory_bytes = voxels * bytes_per_voxel
        
        # Additional memory for calculation arrays (typically 2-3x base)
        total_memory_bytes = base_memory_bytes * 3
        
        # Convert to MB and GB
        memory_mb = total_memory_bytes / (1024 * 1024)
        memory_gb = memory_mb / 1024
        
        return {
            'estimated_mb': memory_mb,
            'estimated_gb': memory_gb,
            'voxels': voxels,
            'bytes_per_voxel': bytes_per_voxel,
            'within_limit': memory_mb <= self.memory_limit_per_simulation
        }
    
    def get_recommended_parameters(self, target_computation_time_hours: float = 1.0) -> Dict[str, Any]:
        """Get recommended parameters for target computation time."""
        # Work backwards from target time to find suitable parameters
        recommendations = {}
        
        # Start with default system size and adjust
        for size in [50, 100, 150, 200, 250]:
            time_est = self.estimate_computation_time(size, self.default_hydration_cycles)
            memory_est = self.estimate_memory_usage(size)
            
            if (time_est['estimated_hours'] <= target_computation_time_hours and 
                memory_est['within_limit']):
                recommendations = {
                    'system_size': size,
                    'cycles': self.default_hydration_cycles,
                    'resolution': self.default_resolution,
                    'estimated_time_hours': time_est['estimated_hours'],
                    'estimated_memory_mb': memory_est['estimated_mb'],
                    'total_voxels': time_est['total_voxels']
                }
        
        if not recommendations:
            # Fall back to smallest feasible parameters
            recommendations = {
                'system_size': 50,
                'cycles': min(self.default_hydration_cycles, 1000),
                'resolution': 2.0,  # Coarser resolution
                'note': 'Reduced parameters to meet time/memory constraints'
            }
        
        return recommendations
    
    def validate(self) -> Dict[str, Any]:
        """Validate simulation configuration."""
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Validate hydration parameters
        if not (100 <= self.default_hydration_cycles <= self.max_hydration_cycles):
            validation_result['errors'].append(
                f"Default hydration cycles ({self.default_hydration_cycles}) outside valid range"
            )
            validation_result['is_valid'] = False
        
        if not (0 <= self.default_temperature <= 100):
            validation_result['errors'].append(
                f"Temperature ({self.default_temperature}°C) outside reasonable range [0, 100]"
            )
            validation_result['is_valid'] = False
        
        if not (0.2 <= self.default_water_binder_ratio <= 1.0):
            validation_result['warnings'].append(
                f"Water-binder ratio ({self.default_water_binder_ratio}) outside typical range [0.2, 1.0]"
            )
        
        # Validate microstructure parameters
        if not (10 <= self.default_system_size <= self.max_system_size):
            validation_result['errors'].append(
                f"System size ({self.default_system_size}) outside valid range"
            )
            validation_result['is_valid'] = False
        
        if not (self.min_resolution <= self.default_resolution <= self.max_resolution):
            validation_result['errors'].append(
                f"Resolution ({self.default_resolution}) outside valid range"
            )
            validation_result['is_valid'] = False
        
        if not (0.3 <= self.default_aggregate_volume_fraction <= self.max_aggregate_volume_fraction):
            validation_result['warnings'].append(
                f"Aggregate volume fraction ({self.default_aggregate_volume_fraction}) outside typical range"
            )
        
        if not (0 <= self.default_air_content <= self.max_air_content):
            validation_result['errors'].append(
                f"Air content ({self.default_air_content}) outside valid range"
            )
            validation_result['is_valid'] = False
        
        # Validate particle shapes
        if self.default_cement_shape not in self.available_particle_shapes:
            validation_result['errors'].append(
                f"Default cement shape '{self.default_cement_shape}' not in available shapes"
            )
            validation_result['is_valid'] = False
        
        if self.default_aggregate_shape not in self.available_particle_shapes:
            validation_result['errors'].append(
                f"Default aggregate shape '{self.default_aggregate_shape}' not in available shapes"
            )
            validation_result['is_valid'] = False
        
        # Validate material properties
        if self.default_youngs_modulus_cement <= 0:
            validation_result['errors'].append("Young's modulus for cement must be positive")
            validation_result['is_valid'] = False
        
        if not (0 <= self.default_poissons_ratio_cement < 0.5):
            validation_result['errors'].append("Poisson's ratio for cement must be in range [0, 0.5)")
            validation_result['is_valid'] = False
        
        # Validate performance parameters
        if self.max_worker_threads < 1:
            validation_result['errors'].append("Max worker threads must be at least 1")
            validation_result['is_valid'] = False
        elif self.max_worker_threads > 32:
            validation_result['warnings'].append("Very high thread count may not improve performance")
        
        if self.memory_limit_per_simulation < 512:
            validation_result['warnings'].append("Low memory limit may cause simulation failures")
        
        # Validate convergence criteria
        if self.hydration_convergence_tolerance <= 0:
            validation_result['errors'].append("Hydration convergence tolerance must be positive")
            validation_result['is_valid'] = False
        
        if self.max_iterations < 100:
            validation_result['warnings'].append("Low iteration limit may prevent convergence")
        
        return validation_result
#!/usr/bin/env python3
"""
Hydration Service for VCCTL

Provides business logic for cement hydration simulation, temperature profiles,
aging modes, and simulation progress tracking.
"""

import logging
import math
import time
from typing import List, Optional, Dict, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import threading

from app.database.service import DatabaseService
from app.services.base_service import ServiceError, ValidationError


class AgingMode(Enum):
    """Aging mode for hydration simulation."""
    TIME = "time"
    CALORIMETRY = "calorimetry"
    CHEMICAL_SHRINKAGE = "chemical_shrinkage"


class SimulationStatus(Enum):
    """Status of hydration simulation."""
    INITIALIZED = "initialized"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TemperaturePoint:
    """Temperature point in a temperature profile."""
    time_hours: float
    temperature_celsius: float
    
    def __post_init__(self):
        """Validate temperature point."""
        if self.time_hours < 0:
            raise ValueError("Time must be non-negative")
        if not (-20 <= self.temperature_celsius <= 100):
            raise ValueError("Temperature must be between -20°C and 100°C")


@dataclass
class TemperatureProfile:
    """Temperature profile for hydration simulation."""
    name: str
    description: str = ""
    points: List[TemperaturePoint] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate temperature profile."""
        if not self.points:
            raise ValueError("Temperature profile must have at least one point")
        
        # Sort points by time
        self.points.sort(key=lambda p: p.time_hours)
        
        # Check for duplicate times
        times = [p.time_hours for p in self.points]
        if len(times) != len(set(times)):
            raise ValueError("Temperature profile cannot have duplicate time points")
    
    def get_temperature_at_time(self, time_hours: float) -> float:
        """Get temperature at specified time using linear interpolation."""
        if not self.points:
            return 25.0  # Default temperature
        
        # Before first point
        if time_hours <= self.points[0].time_hours:
            return self.points[0].temperature_celsius
        
        # After last point
        if time_hours >= self.points[-1].time_hours:
            return self.points[-1].temperature_celsius
        
        # Find interpolation interval
        for i in range(len(self.points) - 1):
            t1, temp1 = self.points[i].time_hours, self.points[i].temperature_celsius
            t2, temp2 = self.points[i + 1].time_hours, self.points[i + 1].temperature_celsius
            
            if t1 <= time_hours <= t2:
                # Linear interpolation
                if t2 == t1:
                    return temp1
                ratio = (time_hours - t1) / (t2 - t1)
                return temp1 + ratio * (temp2 - temp1)
        
        return self.points[-1].temperature_celsius


@dataclass
class HydrationParameters:
    """Parameters for hydration simulation."""
    # Time and cycles
    total_cycles: int = 2000
    time_step_hours: float = 0.001
    max_simulation_time_hours: float = 168.0  # 7 days
    
    # Temperature
    temperature_profile: TemperatureProfile = field(default_factory=lambda: 
        TemperatureProfile("Constant", "Constant temperature", 
                         [TemperaturePoint(0.0, 25.0)]))
    
    # Aging mode
    aging_mode: AgingMode = AgingMode.TIME
    
    # Convergence criteria
    convergence_tolerance: float = 1e-6
    max_iterations_per_cycle: int = 100
    
    # Output settings
    save_interval_cycles: int = 100
    save_intermediate_results: bool = False
    
    def __post_init__(self):
        """Validate hydration parameters."""
        if self.total_cycles <= 0:
            raise ValueError("Total cycles must be positive")
        if self.time_step_hours <= 0:
            raise ValueError("Time step must be positive")
        if self.max_simulation_time_hours <= 0:
            raise ValueError("Maximum simulation time must be positive")
        if self.convergence_tolerance <= 0:
            raise ValueError("Convergence tolerance must be positive")
        if self.max_iterations_per_cycle <= 0:
            raise ValueError("Max iterations per cycle must be positive")
        if self.save_interval_cycles <= 0:
            raise ValueError("Save interval must be positive")


@dataclass
class SimulationProgress:
    """Progress information for running simulation."""
    current_cycle: int = 0
    total_cycles: int = 0
    current_time_hours: float = 0.0
    elapsed_real_time_seconds: float = 0.0
    estimated_remaining_seconds: float = 0.0
    status: SimulationStatus = SimulationStatus.INITIALIZED
    
    # Hydration metrics
    degree_of_hydration: float = 0.0
    heat_released_j_per_g: float = 0.0
    chemical_shrinkage: float = 0.0
    
    # Performance metrics
    cycles_per_second: float = 0.0
    memory_usage_mb: float = 0.0
    
    # Status messages
    current_operation: str = ""
    last_error: str = ""
    
    @property
    def progress_fraction(self) -> float:
        """Get progress as fraction between 0 and 1."""
        if self.total_cycles <= 0:
            return 0.0
        return min(1.0, self.current_cycle / self.total_cycles)
    
    @property
    def progress_percentage(self) -> float:
        """Get progress as percentage."""
        return self.progress_fraction * 100.0


class HydrationService:
    """
    Service for managing cement hydration simulations.
    
    Provides hydration parameter management, temperature profiles,
    simulation progress tracking, and results analysis.
    """
    
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
        self.logger = logging.getLogger('VCCTL.HydrationService')
        
        # Simulation state
        self._current_simulation: Optional[SimulationProgress] = None
        self._simulation_thread: Optional[threading.Thread] = None
        self._simulation_stop_event = threading.Event()
        self._progress_callbacks: List[Callable[[SimulationProgress], None]] = []
        
        # Predefined temperature profiles
        self._predefined_profiles = self._create_predefined_profiles()
        
        self.logger.info("Hydration service initialized")
    
    def _create_predefined_profiles(self) -> Dict[str, TemperatureProfile]:
        """Create predefined temperature profiles."""
        profiles = {}
        
        # Constant temperature profiles
        for temp in [20, 23, 25, 30, 35, 40]:
            name = f"Constant {temp}°C"
            profiles[name] = TemperatureProfile(
                name=name,
                description=f"Constant temperature at {temp}°C",
                points=[TemperaturePoint(0.0, temp)]
            )
        
        # ASTM C1074 standard curing
        profiles["ASTM C1074"] = TemperatureProfile(
            name="ASTM C1074",
            description="ASTM C1074 standard temperature rise",
            points=[
                TemperaturePoint(0.0, 23.0),
                TemperaturePoint(4.0, 35.0),
                TemperaturePoint(8.0, 50.0),
                TemperaturePoint(24.0, 60.0),
                TemperaturePoint(48.0, 55.0),
                TemperaturePoint(72.0, 45.0),
                TemperaturePoint(168.0, 23.0)
            ]
        )
        
        # Adiabatic temperature rise
        profiles["Adiabatic"] = TemperatureProfile(
            name="Adiabatic",
            description="Adiabatic temperature rise simulation",
            points=[
                TemperaturePoint(0.0, 23.0),
                TemperaturePoint(0.5, 30.0),
                TemperaturePoint(1.0, 40.0),
                TemperaturePoint(2.0, 55.0),
                TemperaturePoint(6.0, 70.0),
                TemperaturePoint(12.0, 75.0),
                TemperaturePoint(24.0, 78.0),
                TemperaturePoint(168.0, 80.0)
            ]
        )
        
        # Cold weather curing
        profiles["Cold Weather"] = TemperatureProfile(
            name="Cold Weather",
            description="Cold weather curing profile",
            points=[
                TemperaturePoint(0.0, 5.0),
                TemperaturePoint(2.0, 8.0),
                TemperaturePoint(6.0, 12.0),
                TemperaturePoint(24.0, 15.0),
                TemperaturePoint(168.0, 18.0)
            ]
        )
        
        # High temperature mass concrete
        profiles["Mass Concrete"] = TemperatureProfile(
            name="Mass Concrete",
            description="Mass concrete temperature profile",
            points=[
                TemperaturePoint(0.0, 23.0),
                TemperaturePoint(1.0, 35.0),
                TemperaturePoint(6.0, 65.0),
                TemperaturePoint(24.0, 85.0),
                TemperaturePoint(72.0, 75.0),
                TemperaturePoint(168.0, 50.0),
                TemperaturePoint(336.0, 35.0)
            ]
        )
        
        return profiles
    
    def get_predefined_temperature_profiles(self) -> Dict[str, TemperatureProfile]:
        """Get predefined temperature profiles."""
        return self._predefined_profiles.copy()
    
    def get_temperature_profile_service(self):
        """Get temperature profile service for database operations."""
        try:
            from app.services.temperature_profile_service import TemperatureProfileService
            return TemperatureProfileService(self.db_service)
        except Exception as e:
            self.logger.error(f"Failed to get temperature profile service: {e}")
            return None
    
    def get_all_temperature_profiles(self) -> Dict[str, TemperatureProfile]:
        """Get all temperature profiles (predefined + custom from database)."""
        try:
            profiles = self._predefined_profiles.copy()
            
            # Add custom profiles from database
            profile_service = self.get_temperature_profile_service()
            if profile_service:
                profile_list = profile_service.list_profiles()
                for profile_info in profile_list:
                    if not profile_info['is_predefined']:  # Only add custom profiles
                        profile = profile_service.get_profile(profile_info['name'])
                        if profile:
                            profiles[profile.name] = profile
            
            return profiles
        except Exception as e:
            self.logger.error(f"Failed to get all temperature profiles: {e}")
            return self._predefined_profiles.copy()
    
    def create_temperature_profile(self, name: str, description: str, 
                                 points: List[Tuple[float, float]]) -> TemperatureProfile:
        """Create a custom temperature profile."""
        try:
            temp_points = [TemperaturePoint(time_h, temp_c) for time_h, temp_c in points]
            profile = TemperatureProfile(name, description, temp_points)
            
            self.logger.info(f"Created temperature profile: {name}")
            return profile
            
        except Exception as e:
            self.logger.error(f"Failed to create temperature profile: {e}")
            raise ServiceError(f"Temperature profile creation failed: {e}")
    
    def validate_hydration_parameters(self, params: HydrationParameters) -> Dict[str, Any]:
        """Validate hydration parameters."""
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'recommendations': []
        }
        
        try:
            # Validate cycles and timing
            if params.total_cycles < 100:
                validation_result['warnings'].append("Very few cycles may not show full hydration")
            elif params.total_cycles > 50000:
                validation_result['warnings'].append("Many cycles will require significant computation time")
            
            if params.time_step_hours > 0.1:
                validation_result['warnings'].append("Large time step may reduce accuracy")
            elif params.time_step_hours < 0.0001:
                validation_result['warnings'].append("Very small time step will increase computation time")
            
            # Validate temperature profile
            max_temp = max(p.temperature_celsius for p in params.temperature_profile.points)
            min_temp = min(p.temperature_celsius for p in params.temperature_profile.points)
            
            if max_temp > 80:
                validation_result['warnings'].append(f"High temperature ({max_temp}°C) may cause unrealistic hydration")
            
            if min_temp < 0:
                validation_result['warnings'].append("Sub-zero temperatures will stop hydration")
            
            if max_temp - min_temp > 50:
                validation_result['warnings'].append("Large temperature variation may cause thermal stress")
            
            # Validate convergence criteria
            if params.convergence_tolerance > 1e-3:
                validation_result['warnings'].append("Loose convergence tolerance may reduce accuracy")
            elif params.convergence_tolerance < 1e-9:
                validation_result['warnings'].append("Very tight convergence may slow simulation")
            
            if params.max_iterations_per_cycle < 50:
                validation_result['warnings'].append("Low iteration limit may prevent convergence")
            
            # Estimate computation requirements (without microstructure info in validation)
            estimated_time = self.estimate_simulation_time(params)
            if estimated_time['estimated_hours'] > 24:
                validation_result['warnings'].append(f"Long simulation time (~{estimated_time['estimated_hours']:.1f} hours)")
            
            return validation_result
            
        except Exception as e:
            validation_result['errors'].append(f"Validation failed: {e}")
            validation_result['is_valid'] = False
            return validation_result
    
    def estimate_simulation_time(self, params: HydrationParameters, microstructure_info: Optional[Dict] = None) -> Dict[str, float]:
        """Estimate simulation computation time using baseline approach."""
        try:
            print(f"DEBUG_EST: Starting baseline estimation with microstructure_info={microstructure_info}")
            
            # Baseline: 3 minutes for 100³ microstructure with 168 hours max time
            baseline_minutes = 3.0
            baseline_cube_size = 100.0
            baseline_max_time_hours = 168.0
            
            # Get microstructure size
            cube_size = 100.0  # Default
            if microstructure_info and 'cubesize' in microstructure_info:
                cube_size = float(microstructure_info['cubesize'])
                print(f"DEBUG_EST: Using cube size from microstructure_info: {cube_size}")
            
            # Get max time (try both parameter locations)
            max_time_hours = baseline_max_time_hours
            if hasattr(params, 'max_time_hours'):
                max_time_hours = params.max_time_hours
            elif hasattr(params, 'max_simulation_time_hours'):
                max_time_hours = params.max_simulation_time_hours
            print(f"DEBUG_EST: Using max time: {max_time_hours} hours")
            
            # Calculate scaling factors
            size_factor = (cube_size / baseline_cube_size) ** 2.2
            time_duration_factor = (max_time_hours / baseline_max_time_hours) ** 0.5
            
            # Calculate final estimate
            estimated_minutes = baseline_minutes * size_factor * time_duration_factor
            estimated_seconds = estimated_minutes * 60.0
            
            print(f"DEBUG_EST: Baseline calculation:")
            print(f"  Cube size: {cube_size} (factor: {size_factor:.3f})")
            print(f"  Max time: {max_time_hours}h (factor: {time_duration_factor:.3f})")
            print(f"  Final estimate: {estimated_minutes:.1f} minutes")
            
            return {
                'estimated_seconds': estimated_seconds,
                'estimated_minutes': estimated_minutes,
                'estimated_hours': estimated_seconds / 3600,
                'cycles': params.total_cycles,
                'complexity_factors': {
                    'microstructure_size': size_factor,
                    'time_duration': time_duration_factor,
                    'cube_size': cube_size,
                    'max_time_hours': max_time_hours
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to estimate simulation time: {e}")
            raise ServiceError(f"Time estimation failed: {e}")
    
    def start_simulation(self, params: HydrationParameters, 
                        microstructure_data: Dict[str, Any]) -> bool:
        """Start hydration simulation."""
        try:
            if self.is_simulation_running():
                raise ServiceError("Simulation is already running")
            
            # Validate parameters
            validation = self.validate_hydration_parameters(params)
            if not validation['is_valid']:
                raise ValidationError(f"Invalid parameters: {validation['errors']}")
            
            # Initialize simulation progress
            self._current_simulation = SimulationProgress(
                total_cycles=params.total_cycles,
                status=SimulationStatus.INITIALIZED,
                current_operation="Initializing simulation"
            )
            
            # Start simulation in background thread
            self._simulation_stop_event.clear()
            self._simulation_thread = threading.Thread(
                target=self._run_simulation,
                args=(params, microstructure_data),
                daemon=True
            )
            self._simulation_thread.start()
            
            self.logger.info(f"Started hydration simulation with {params.total_cycles} cycles")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start simulation: {e}")
            if self._current_simulation:
                self._current_simulation.status = SimulationStatus.FAILED
                self._current_simulation.last_error = str(e)
            raise ServiceError(f"Simulation start failed: {e}")
    
    def _run_simulation(self, params: HydrationParameters, microstructure_data: Dict[str, Any]) -> None:
        """Run the actual simulation (called in background thread)."""
        try:
            if not self._current_simulation:
                return
            
            start_time = time.time()
            self._current_simulation.status = SimulationStatus.RUNNING
            self._current_simulation.current_operation = "Running hydration simulation"
            
            for cycle in range(1, params.total_cycles + 1):
                if self._simulation_stop_event.is_set():
                    self._current_simulation.status = SimulationStatus.CANCELLED
                    break
                
                # Update progress
                self._current_simulation.current_cycle = cycle
                self._current_simulation.current_time_hours = cycle * params.time_step_hours
                self._current_simulation.elapsed_real_time_seconds = time.time() - start_time
                
                # Calculate performance metrics
                if self._current_simulation.elapsed_real_time_seconds > 0:
                    self._current_simulation.cycles_per_second = cycle / self._current_simulation.elapsed_real_time_seconds
                    remaining_cycles = params.total_cycles - cycle
                    self._current_simulation.estimated_remaining_seconds = remaining_cycles / self._current_simulation.cycles_per_second
                
                # Get temperature at current time
                current_temp = params.temperature_profile.get_temperature_at_time(
                    self._current_simulation.current_time_hours
                )
                
                # Simulate hydration step (placeholder for actual hydration calculations)
                self._simulate_hydration_step(cycle, current_temp, params)
                
                # Notify progress callbacks
                for callback in self._progress_callbacks:
                    try:
                        callback(self._current_simulation)
                    except Exception as e:
                        self.logger.warning(f"Progress callback failed: {e}")
                
                # Small delay to prevent UI freezing
                time.sleep(0.001)
            
            # Complete simulation
            if self._current_simulation.status == SimulationStatus.RUNNING:
                self._current_simulation.status = SimulationStatus.COMPLETED
                self._current_simulation.current_operation = "Simulation completed"
                self.logger.info("Hydration simulation completed successfully")
            
        except Exception as e:
            self.logger.error(f"Simulation failed: {e}")
            if self._current_simulation:
                self._current_simulation.status = SimulationStatus.FAILED
                self._current_simulation.last_error = str(e)
    
    def _simulate_hydration_step(self, cycle: int, temperature: float, params: HydrationParameters) -> None:
        """Simulate one hydration step (placeholder for actual hydration physics)."""
        if not self._current_simulation:
            return
        
        # Simplified hydration model for demonstration
        time_hours = self._current_simulation.current_time_hours
        
        # Degree of hydration (simplified exponential model)
        alpha_max = 0.85  # Maximum degree of hydration
        k = 0.1 * math.exp((temperature - 25) / 10)  # Temperature-dependent rate constant
        alpha = alpha_max * (1 - math.exp(-k * math.sqrt(time_hours)))
        self._current_simulation.degree_of_hydration = min(alpha, alpha_max)
        
        # Heat release (simplified model)
        heat_total = 350.0  # J/g total heat of hydration for cement
        self._current_simulation.heat_released_j_per_g = heat_total * self._current_simulation.degree_of_hydration
        
        # Chemical shrinkage (simplified model)
        shrinkage_total = 0.06  # Total chemical shrinkage
        self._current_simulation.chemical_shrinkage = shrinkage_total * self._current_simulation.degree_of_hydration
        
        # Update memory usage (estimated)
        self._current_simulation.memory_usage_mb = 100 + cycle * 0.01
    
    def stop_simulation(self) -> bool:
        """Stop the running simulation."""
        try:
            if not self.is_simulation_running():
                return False
            
            self._simulation_stop_event.set()
            
            if self._simulation_thread and self._simulation_thread.is_alive():
                self._simulation_thread.join(timeout=5.0)
            
            if self._current_simulation:
                self._current_simulation.status = SimulationStatus.CANCELLED
                self._current_simulation.current_operation = "Simulation cancelled"
            
            self.logger.info("Hydration simulation stopped")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop simulation: {e}")
            return False
    
    def pause_simulation(self) -> bool:
        """Pause the running simulation."""
        # TODO: Implement pause functionality
        self.logger.warning("Simulation pause not yet implemented")
        return False
    
    def resume_simulation(self) -> bool:
        """Resume a paused simulation."""
        # TODO: Implement resume functionality
        self.logger.warning("Simulation resume not yet implemented")
        return False
    
    def is_simulation_running(self) -> bool:
        """Check if simulation is currently running."""
        return (self._current_simulation is not None and 
                self._current_simulation.status == SimulationStatus.RUNNING and
                self._simulation_thread is not None and 
                self._simulation_thread.is_alive())
    
    def get_simulation_progress(self) -> Optional[SimulationProgress]:
        """Get current simulation progress."""
        return self._current_simulation
    
    def add_progress_callback(self, callback: Callable[[SimulationProgress], None]) -> None:
        """Add a callback to be called on simulation progress updates."""
        self._progress_callbacks.append(callback)
    
    def remove_progress_callback(self, callback: Callable[[SimulationProgress], None]) -> None:
        """Remove a progress callback."""
        if callback in self._progress_callbacks:
            self._progress_callbacks.remove(callback)
    
    def get_simulation_results(self) -> Optional[Dict[str, Any]]:
        """Get results from completed simulation."""
        if not self._current_simulation or self._current_simulation.status != SimulationStatus.COMPLETED:
            return None
        
        return {
            'final_degree_of_hydration': self._current_simulation.degree_of_hydration,
            'total_heat_released': self._current_simulation.heat_released_j_per_g,
            'chemical_shrinkage': self._current_simulation.chemical_shrinkage,
            'simulation_time_hours': self._current_simulation.current_time_hours,
            'computation_time_seconds': self._current_simulation.elapsed_real_time_seconds,
            'total_cycles': self._current_simulation.total_cycles,
            'performance': {
                'cycles_per_second': self._current_simulation.cycles_per_second,
                'peak_memory_mb': self._current_simulation.memory_usage_mb
            }
        }
    
    def export_simulation_data(self, filepath: str, format: str = 'json') -> bool:
        """Export simulation results to file."""
        try:
            results = self.get_simulation_results()
            if not results:
                raise ServiceError("No simulation results available")
            
            if format.lower() == 'json':
                import json
                with open(filepath, 'w') as f:
                    json.dump(results, f, indent=2)
            elif format.lower() == 'csv':
                import csv
                with open(filepath, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Parameter', 'Value'])
                    for key, value in results.items():
                        if isinstance(value, dict):
                            for subkey, subvalue in value.items():
                                writer.writerow([f"{key}.{subkey}", subvalue])
                        else:
                            writer.writerow([key, value])
            else:
                raise ServiceError(f"Unsupported export format: {format}")
            
            self.logger.info(f"Simulation data exported to {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export simulation data: {e}")
            raise ServiceError(f"Export failed: {e}")
#!/usr/bin/env python3
"""
Hydration Executor Service for VCCTL

Manages execution of disrealnew hydration simulations including:
- Process lifecycle management (start, monitor, cancel, cleanup)
- Progress monitoring and parsing (current format + future JSON format)
- Real-time output capture and logging
- Operation directory management
- Parameter file preparation
"""

import os
import sys
import json
import time
import logging
import subprocess
import threading
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime
from enum import Enum

from app.models.operation import Operation, OperationStatus, OperationType
from app.services.hydration_parameters_service import HydrationParametersService
from app.database.service import DatabaseService


class HydrationSimulationStatus(str, Enum):
    """Status of hydration simulation execution."""
    PREPARING = "PREPARING"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    ERROR = "ERROR"


class HydrationProgress:
    """Container for hydration simulation progress information."""
    
    def __init__(self):
        self.cycle: int = 0
        self.time_hours: float = 0.0
        self.degree_of_hydration: float = 0.0
        self.temperature_celsius: float = 25.0
        self.ph: float = 12.0
        self.water_left: float = 1.0
        self.heat_cumulative: float = 0.0
        self.percent_complete: float = 0.0
        self.estimated_time_remaining: float = 0.0
        self.cycles_per_second: float = 0.0
        self.phase_counts: Dict[str, int] = {}
        self.last_update: datetime = datetime.now()
        
        # Simulation parameters
        self.max_cycles: int = 50000
        self.target_alpha: float = 0.8
        self.end_time_hours: float = 168.0
        self.cubesize: int = 100
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert progress to dictionary format."""
        return {
            'cycle': self.cycle,
            'time_hours': self.time_hours,
            'degree_of_hydration': self.degree_of_hydration,
            'temperature_celsius': self.temperature_celsius,
            'ph': self.ph,
            'water_left': self.water_left,
            'heat_cumulative': self.heat_cumulative,
            'percent_complete': self.percent_complete,
            'estimated_time_remaining': self.estimated_time_remaining,
            'cycles_per_second': self.cycles_per_second,
            'phase_counts': self.phase_counts,
            'last_update': self.last_update.isoformat(),
            'max_cycles': self.max_cycles,
            'target_alpha': self.target_alpha,
            'end_time_hours': self.end_time_hours,
            'cubesize': self.cubesize
        }


class HydrationExecutorService:
    """Service for executing and monitoring hydration simulations."""
    
    def __init__(self, database_service: DatabaseService, 
                 hydration_params_service: HydrationParametersService):
        """Initialize the hydration executor service."""
        self.database_service = database_service
        self.hydration_params_service = hydration_params_service
        self.logger = logging.getLogger('VCCTL.HydrationExecutor')
        
        # Process management
        self.active_simulations: Dict[str, Dict[str, Any]] = {}  # operation_name -> simulation info
        self.progress_callbacks: Dict[str, List[Callable]] = {}  # operation_name -> callback list
        
        # Paths
        self.project_root = Path(__file__).parent.parent.parent.parent
        self.disrealnew_binary = self.project_root / "backend" / "bin" / "disrealnew"
        
        # Configuration
        self.progress_update_interval = 15.0  # seconds
        self.json_progress_support = True  # Will be True when your I/O improvements are ready
        
    def start_hydration_simulation(self, operation_name: str, 
                                 parameter_set_name: str = "portland_cement_standard",
                                 progress_callback: Optional[Callable] = None,
                                 parameter_file_path: Optional[str] = None) -> bool:
        """
        Start a hydration simulation for the given operation.
        
        Args:
            operation_name: Name of the operation
            parameter_set_name: Name of parameter set to use
            progress_callback: Optional callback for progress updates
            parameter_file_path: Optional path to extended parameter file (overrides parameter_set_name)
            
        Returns:
            True if simulation started successfully, False otherwise
        """
        try:
            self.logger.info(f"Starting hydration simulation for operation: {operation_name}")
            
            # Check if simulation is already running
            if operation_name in self.active_simulations:
                self.logger.warning(f"Simulation already running for operation: {operation_name}")
                return False
            
            # Prepare operation directory and files
            if not self._prepare_simulation_environment(operation_name, parameter_set_name, parameter_file_path):
                return False
            
            # Update operation status in database
            self._update_operation_status(operation_name, OperationStatus.RUNNING)
            
            # Start the simulation process
            simulation_info = self._start_disrealnew_process(operation_name, parameter_file_path)
            if not simulation_info:
                self._update_operation_status(operation_name, OperationStatus.ERROR)
                return False
            
            # Register simulation and start monitoring
            self.active_simulations[operation_name] = simulation_info
            if progress_callback:
                self._add_progress_callback(operation_name, progress_callback)
            
            # Start monitoring thread
            monitor_thread = threading.Thread(
                target=self._monitor_simulation,
                args=(operation_name,),
                daemon=True
            )
            monitor_thread.start()
            simulation_info['monitor_thread'] = monitor_thread
            
            self.logger.info(f"Hydration simulation started successfully: {operation_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start hydration simulation '{operation_name}': {e}")
            self._update_operation_status(operation_name, OperationStatus.ERROR)
            return False
    
    def cancel_simulation(self, operation_name: str) -> bool:
        """
        Cancel a running hydration simulation.
        
        Args:
            operation_name: Name of the operation to cancel
            
        Returns:
            True if cancelled successfully, False otherwise
        """
        try:
            if operation_name not in self.active_simulations:
                self.logger.warning(f"No active simulation found for operation: {operation_name}")
                return False
            
            simulation_info = self.active_simulations[operation_name]
            process = simulation_info.get('process')
            
            if process and process.poll() is None:  # Process is still running
                self.logger.info(f"Terminating hydration simulation: {operation_name}")
                process.terminate()
                
                # Give it a moment to terminate gracefully
                time.sleep(2.0)
                
                # Force kill if still running
                if process.poll() is None:
                    process.kill()
                    self.logger.warning(f"Force killed simulation process: {operation_name}")
            
            # Update status and cleanup
            simulation_info['status'] = HydrationSimulationStatus.CANCELLED
            self._update_operation_status(operation_name, OperationStatus.CANCELLED)
            
            self.logger.info(f"Hydration simulation cancelled: {operation_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to cancel simulation '{operation_name}': {e}")
            return False
    
    def get_simulation_status(self, operation_name: str) -> Optional[HydrationSimulationStatus]:
        """Get the current status of a simulation."""
        if operation_name in self.active_simulations:
            return self.active_simulations[operation_name].get('status', HydrationSimulationStatus.ERROR)
        return None
    
    def get_simulation_progress(self, operation_name: str) -> Optional[HydrationProgress]:
        """Get the current progress of a simulation."""
        if operation_name in self.active_simulations:
            return self.active_simulations[operation_name].get('progress')
        return None
    
    def _prepare_simulation_environment(self, operation_name: str, parameter_set_name: str, parameter_file_path: Optional[str] = None) -> bool:
        """
        Prepare the simulation environment including directories and parameter files.
        
        Args:
            operation_name: Name of the operation
            parameter_set_name: Name of parameter set to use
            
        Returns:
            True if preparation successful, False otherwise
        """
        try:
            # Use custom parameter file if provided, otherwise export from database
            if parameter_file_path:
                param_file = Path(parameter_file_path)
                if not param_file.exists():
                    raise FileNotFoundError(f"Custom parameter file not found: {parameter_file_path}")
            else:
                # Export hydration parameters to operation directory
                param_file = self.hydration_params_service.export_to_operation_directory(
                    operation_name, parameter_set_name
                )
            
            # Verify disrealnew binary exists
            if not self.disrealnew_binary.exists():
                raise FileNotFoundError(f"disrealnew binary not found: {self.disrealnew_binary}")
            
            # Create additional required directories/files if needed
            operation_dir = self.project_root / "Operations" / operation_name
            
            # Prepare log files
            stdout_log = operation_dir / f"{operation_name}_hydration_stdout.log"
            stderr_log = operation_dir / f"{operation_name}_hydration_stderr.log"
            
            self.logger.info(f"Environment prepared for operation: {operation_name}")
            self.logger.info(f"  Parameter file: {param_file}")
            self.logger.info(f"  Working directory: {operation_dir}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to prepare simulation environment for '{operation_name}': {e}")
            return False
    
    def _start_disrealnew_process(self, operation_name: str, parameter_file_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Start the disrealnew process.
        
        Args:
            operation_name: Name of the operation
            
        Returns:
            Simulation info dictionary or None if failed
        """
        try:
            operation_dir = self.project_root / "Operations" / operation_name
            if parameter_file_path:
                # Use absolute path for the parameter file
                param_file = Path(parameter_file_path).resolve()
            else:
                param_file = operation_dir / f"{operation_name}_hydration_parameters.prm"
            
            # Prepare command
            if self.json_progress_support:
                # Future improved I/O interface - use relative paths to avoid path issues
                cmd = [
                    str(self.disrealnew_binary),
                    "--workdir", ".",
                    "--json", "progress.json",
                    "--quiet",
                    "--parameters", param_file.name
                ]
            else:
                # Current interface - interactive mode with stdin redirection
                cmd = [str(self.disrealnew_binary), "-v"]
            
            # Prepare log files
            stdout_log = operation_dir / f"{operation_name}_hydration_stdout.log"
            stderr_log = operation_dir / f"{operation_name}_hydration_stderr.log"
            
            # Start process
            self.logger.info(f"Starting disrealnew process: {' '.join(cmd)}")
            
            if self.json_progress_support:
                # Future: Direct command-line execution
                process = subprocess.Popen(
                    cmd,
                    cwd=str(operation_dir),
                    stdout=open(stdout_log, 'w'),
                    stderr=open(stderr_log, 'w'),
                    text=True
                )
                progress_file_path = str(operation_dir / "progress.json")
            else:
                # Current: Interactive mode with parameter file input via stdin
                process = subprocess.Popen(
                    cmd,
                    cwd=str(operation_dir),
                    stdin=subprocess.PIPE,
                    stdout=open(stdout_log, 'w'),
                    stderr=open(stderr_log, 'w'),
                    text=True
                )
                
                # Send parameter file name to stdin
                process.stdin.write(f"{param_file.name}\\n")
                process.stdin.flush()
                process.stdin.close()  # Close stdin after sending parameter file name
                
                progress_file_path = None
            
            # Create simulation info
            progress = HydrationProgress()
            simulation_info = {
                'process': process,
                'status': HydrationSimulationStatus.STARTING,
                'progress': progress,
                'start_time': datetime.now(),
                'operation_dir': operation_dir,
                'stdout_log': stdout_log,
                'stderr_log': stderr_log,
                'progress_file': progress_file_path,
                'last_progress_check': time.time()
            }
            
            return simulation_info
            
        except Exception as e:
            self.logger.error(f"Failed to start disrealnew process for '{operation_name}': {e}")
            return None
    
    def _monitor_simulation(self, operation_name: str):
        """
        Monitor a running simulation in a background thread.
        
        Args:
            operation_name: Name of the operation to monitor
        """
        self.logger.info(f"Starting simulation monitoring for: {operation_name}")
        
        try:
            simulation_info = self.active_simulations[operation_name]
            process = simulation_info['process']
            
            while operation_name in self.active_simulations:
                # Check if process is still running
                return_code = process.poll()
                
                if return_code is not None:
                    # Process has finished
                    if return_code == 0:
                        simulation_info['status'] = HydrationSimulationStatus.COMPLETED
                        self._update_operation_status(operation_name, OperationStatus.FINISHED)
                        self.logger.info(f"Simulation completed successfully: {operation_name}")
                    else:
                        simulation_info['status'] = HydrationSimulationStatus.ERROR
                        self._update_operation_status(operation_name, OperationStatus.ERROR)
                        self.logger.error(f"Simulation failed with return code {return_code}: {operation_name}")
                    
                    # Final progress update
                    self._update_progress(operation_name)
                    
                    # Cleanup
                    self._cleanup_simulation(operation_name)
                    break
                
                # Update progress
                simulation_info['status'] = HydrationSimulationStatus.RUNNING
                self._update_progress(operation_name)
                
                # Sleep before next check
                time.sleep(self.progress_update_interval)
                
        except Exception as e:
            self.logger.error(f"Error monitoring simulation '{operation_name}': {e}")
            if operation_name in self.active_simulations:
                self.active_simulations[operation_name]['status'] = HydrationSimulationStatus.ERROR
                self._update_operation_status(operation_name, OperationStatus.ERROR)
        
        self.logger.info(f"Simulation monitoring ended for: {operation_name}")
    
    def _update_progress(self, operation_name: str):
        """Update progress information for a simulation."""
        try:
            simulation_info = self.active_simulations[operation_name]
            
            if simulation_info.get('progress_file') and Path(simulation_info['progress_file']).exists():
                # Future: Parse JSON progress file
                self._parse_json_progress(operation_name, simulation_info['progress_file'])
            else:
                # Current: Parse stdout log file
                self._parse_stdout_progress(operation_name, simulation_info['stdout_log'])
            
            # Notify progress callbacks
            self._notify_progress_callbacks(operation_name)
            
        except Exception as e:
            self.logger.error(f"Error updating progress for '{operation_name}': {e}")
    
    def _parse_json_progress(self, operation_name: str, progress_file_path: str):
        """Parse progress from JSON file (future implementation)."""
        try:
            with open(progress_file_path, 'r') as f:
                data = json.load(f)
            
            simulation_info = self.active_simulations[operation_name]
            progress = simulation_info['progress']
            
            # Update progress from JSON
            current_state = data.get('current_state', {})
            progress.cycle = current_state.get('cycle', 0)
            progress.time_hours = current_state.get('time_hours', 0.0)
            progress.degree_of_hydration = current_state.get('degree_of_hydration', 0.0)
            progress.temperature_celsius = current_state.get('temperature_celsius', 25.0)
            progress.ph = current_state.get('ph', 12.0)
            progress.water_left = current_state.get('water_left', 1.0)
            progress.heat_cumulative = current_state.get('heat_cumulative_kJ_per_kg', 0.0)
            
            progress_info = data.get('progress', {})
            progress.percent_complete = progress_info.get('percent_complete', 0.0)
            progress.estimated_time_remaining = progress_info.get('estimated_time_remaining_hours', 0.0)
            progress.cycles_per_second = progress_info.get('cycles_per_second', 0.0)
            
            progress.phase_counts = data.get('phase_counts', {})
            progress.last_update = datetime.now()
            
            # Update simulation parameters
            sim_info = data.get('simulation_info', {})
            progress.cubesize = sim_info.get('cubesize', progress.cubesize)
            progress.max_cycles = sim_info.get('max_cycles', progress.max_cycles)
            progress.target_alpha = sim_info.get('target_alpha', progress.target_alpha)
            progress.end_time_hours = sim_info.get('end_time_hours', progress.end_time_hours)
            
        except Exception as e:
            self.logger.error(f"Error parsing JSON progress for '{operation_name}': {e}")
    
    def _parse_stdout_progress(self, operation_name: str, stdout_log_path: Path):
        """Parse progress from stdout log file (current implementation)."""
        try:
            if not stdout_log_path.exists():
                return
            
            # Read last few lines of stdout log to extract progress information
            # This is a simplified implementation - you would need to parse actual disrealnew output
            simulation_info = self.active_simulations[operation_name]
            progress = simulation_info['progress']
            
            # Update timestamp
            progress.last_update = datetime.now()
            
            # Estimate progress based on time elapsed (simplified)
            start_time = simulation_info['start_time']
            elapsed_minutes = (datetime.now() - start_time).total_seconds() / 60.0
            
            # Very rough progress estimation (you'll improve this based on actual output parsing)
            estimated_total_minutes = 120.0  # 2 hours typical
            progress.percent_complete = min((elapsed_minutes / estimated_total_minutes) * 100.0, 95.0)
            
            # TODO: Parse actual output for real progress values
            # This would involve parsing lines like:
            # "Cycle 1000, time = 5.2 h, Alpha = 0.15, Temperature = 25.3 C"
            
        except Exception as e:
            self.logger.error(f"Error parsing stdout progress for '{operation_name}': {e}")
    
    def _notify_progress_callbacks(self, operation_name: str):
        """Notify all registered progress callbacks."""
        try:
            if operation_name in self.progress_callbacks:
                simulation_info = self.active_simulations[operation_name]
                progress = simulation_info['progress']
                
                for callback in self.progress_callbacks[operation_name]:
                    try:
                        callback(operation_name, progress)
                    except Exception as e:
                        self.logger.error(f"Error in progress callback for '{operation_name}': {e}")
        except Exception as e:
            self.logger.error(f"Error notifying progress callbacks for '{operation_name}': {e}")
    
    def _add_progress_callback(self, operation_name: str, callback: Callable):
        """Add a progress callback for an operation."""
        if operation_name not in self.progress_callbacks:
            self.progress_callbacks[operation_name] = []
        self.progress_callbacks[operation_name].append(callback)
    
    def _update_operation_status(self, operation_name: str, status: OperationStatus):
        """Update operation status in database."""
        try:
            with self.database_service.get_session() as session:
                operation = session.query(Operation).filter_by(name=operation_name).first()
                if operation:
                    operation.status = status.value
                    if status == OperationStatus.RUNNING:
                        operation.mark_started()
                    elif status == OperationStatus.FINISHED:
                        operation.mark_finished()
                    elif status == OperationStatus.ERROR:
                        operation.mark_error("Hydration simulation failed")
                    elif status == OperationStatus.CANCELLED:
                        operation.mark_cancelled()
        except Exception as e:
            self.logger.error(f"Error updating operation status for '{operation_name}': {e}")
    
    def _cleanup_simulation(self, operation_name: str):
        """Clean up simulation resources."""
        try:
            if operation_name in self.active_simulations:
                simulation_info = self.active_simulations[operation_name]
                
                # Close any open file handles
                process = simulation_info.get('process')
                if process:
                    if process.stdout:
                        process.stdout.close()
                    if process.stderr:
                        process.stderr.close()
                
                # Remove from active simulations
                del self.active_simulations[operation_name]
                
                # Clean up progress callbacks
                if operation_name in self.progress_callbacks:
                    del self.progress_callbacks[operation_name]
                
                self.logger.info(f"Cleaned up simulation resources for: {operation_name}")
                
        except Exception as e:
            self.logger.error(f"Error cleaning up simulation '{operation_name}': {e}")
    
    def get_active_simulations(self) -> List[str]:
        """Get list of currently active simulation operation names."""
        return list(self.active_simulations.keys())
    
    def is_simulation_active(self, operation_name: str) -> bool:
        """Check if a simulation is currently active."""
        return operation_name in self.active_simulations
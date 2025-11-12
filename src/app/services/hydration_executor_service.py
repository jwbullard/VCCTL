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

from sqlalchemy import text

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

        # Get service container for configured directories
        from app.services.service_container import get_service_container
        service_container = get_service_container()
        self.operations_dir = service_container.directories_service.get_operations_path()

        # Paths
        # Detect if running in PyInstaller bundle
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            # Running in PyInstaller bundle
            self.project_root = Path(sys._MEIPASS)
        else:
            # Running in development
            self.project_root = Path(__file__).parent.parent.parent.parent

        # Platform-specific executable name
        disrealnew_exe = 'disrealnew.exe' if sys.platform == 'win32' else 'disrealnew'
        self.disrealnew_binary = self.project_root / "backend" / "bin" / disrealnew_exe

        # Configuration
        self.progress_update_interval = 15.0  # seconds
        self.json_progress_support = True  # Will be True when your I/O improvements are ready
        
    def start_hydration_simulation(self, operation_name: str, 
                                 parameter_set_name: str = "portland_cement_standard",
                                 progress_callback: Optional[Callable] = None,
                                 parameter_file_path: Optional[str] = None,
                                 max_time_hours: float = 168.0) -> bool:
        """
        Start a hydration simulation for the given operation.
        
        Args:
            operation_name: Name of the operation
            parameter_set_name: Name of parameter set to use
            progress_callback: Optional callback for progress updates
            parameter_file_path: Optional path to extended parameter file (overrides parameter_set_name)
            max_time_hours: Maximum simulation time in hours for progress calculation
            
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
            simulation_info = self._start_disrealnew_process(operation_name, parameter_file_path, max_time_hours)
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
            operation_dir = self.operations_dir / operation_name

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
    
    def _start_disrealnew_process(self, operation_name: str, parameter_file_path: Optional[str] = None, max_time_hours: float = 168.0) -> Optional[Dict[str, Any]]:
        """
        Start the disrealnew process.
        
        Args:
            operation_name: Name of the operation
            
        Returns:
            Simulation info dictionary or None if failed
        """
        try:
            operation_dir = self.operations_dir / operation_name
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
                popen_kwargs = {
                    'cwd': str(operation_dir),
                    'stdout': open(stdout_log, 'w'),
                    'stderr': open(stderr_log, 'w'),
                    'text': True
                }
                # Hide console window on Windows
                if sys.platform == 'win32':
                    popen_kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW

                process = subprocess.Popen(cmd, **popen_kwargs)
                progress_file_path = str(operation_dir / "progress.json")
            else:
                # Current: Interactive mode with parameter file input via stdin
                popen_kwargs = {
                    'cwd': str(operation_dir),
                    'stdin': subprocess.PIPE,
                    'stdout': open(stdout_log, 'w'),
                    'stderr': open(stderr_log, 'w'),
                    'text': True
                }
                # Hide console window on Windows
                if sys.platform == 'win32':
                    popen_kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW

                process = subprocess.Popen(cmd, **popen_kwargs)
                
                # Send parameter file name to stdin
                process.stdin.write(f"{param_file.name}\\n")
                process.stdin.flush()
                process.stdin.close()  # Close stdin after sending parameter file name
                
                progress_file_path = None
            
            # Create simulation info
            progress = HydrationProgress()
            progress.end_time_hours = max_time_hours  # Set from user input, not hardcoded default
            simulation_info = {
                'process': process,
                'status': HydrationSimulationStatus.STARTING,
                'progress': progress,
                'start_time': datetime.now(),
                'operation_dir': operation_dir,
                'stdout_log': stdout_log,
                'stderr_log': stderr_log,
                'progress_file': progress_file_path,
                'last_progress_check': time.time(),
                'max_time_hours': max_time_hours
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
                    # Process has finished - check if simulation completed successfully by examining output files
                    simulation_completed = self._check_simulation_completion(operation_name)
                    
                    if simulation_completed:
                        # Simulation completed successfully (verified by output files)
                        simulation_info['status'] = HydrationSimulationStatus.COMPLETED
                        self._update_operation_status(operation_name, OperationStatus.COMPLETED)
                        if return_code == 0:
                            self.logger.info(f"Simulation completed successfully: {operation_name}")
                        else:
                            self.logger.info(f"Simulation completed successfully despite cleanup error (exit code {return_code}): {operation_name}")
                    else:
                        # Simulation failed (no valid output files found)
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
            
            # Try JSON progress file first (most accurate)
            progress_json = Path(simulation_info['operation_dir']) / "progress.json"
            if progress_json.exists():
                self._parse_json_progress(operation_name, str(progress_json))
            else:
                # Fallback: Parse stdout log file for PROGRESS lines (updated disrealnew.c)
                self._parse_stdout_progress(operation_name, simulation_info['stdout_log'])
            
            # Notify progress callbacks
            self._notify_progress_callbacks(operation_name)
            
        except Exception as e:
            self.logger.error(f"Error updating progress for '{operation_name}': {e}")
    
    def _parse_json_progress(self, operation_name: str, progress_file_path: str):
        """Parse progress from JSON file (current implementation)."""
        try:
            with open(progress_file_path, 'r') as f:
                content = f.read().strip()
                # Handle the "json " prefix if present
                if content.startswith('json '):
                    content = content[5:]
                data = json.loads(content)
            
            simulation_info = self.active_simulations[operation_name]
            progress = simulation_info['progress']
            
            # Update progress from JSON
            # Format: {"cycle": 1220, "time_hours": 668.68, "degree_of_hydration": 0.71, "timestamp": "2025-08-14T14:25:03.434Z"}
            progress.cycle = data.get('cycle', 0)
            progress.time_hours = data.get('time_hours', 0.0)
            progress.degree_of_hydration = data.get('degree_of_hydration', 0.0)
            progress.temperature_celsius = data.get('temperature_celsius', 25.0)
            progress.ph = data.get('ph', 12.0)
            
            # Calculate percentage based on simulation time (most accurate)
            # Use time-based progress since users set max_time_hours as the primary stopping condition
            # Note: alpha and cycles often complete before the time limit, causing premature 100% display
            time_progress = 0.0
            if progress.end_time_hours > 0:
                time_progress = (progress.time_hours / progress.end_time_hours) * 100.0

            # Cap at 99% to account for final I/O phase (~2 min after reaching time limit)
            # Progress will reach 100% only when operation status changes to COMPLETED
            progress.percent_complete = min(time_progress, 99.0)
            
            # Calculate remaining time based on wall-clock time and progress
            # Note: progress.time_hours is simulation time (hydration process time)
            # We need to estimate wall-clock remaining time based on actual elapsed time
            if progress.percent_complete > 0 and progress.percent_complete < 100.0:
                # Calculate wall-clock elapsed time
                start_time = simulation_info.get('start_time', datetime.now())
                elapsed_real_seconds = (datetime.now() - start_time).total_seconds()
                
                self.logger.debug(f"DEBUG_TIME_JSON: percent_complete={progress.percent_complete:.2f}%, elapsed_real_seconds={elapsed_real_seconds:.1f}")
                
                # Estimate remaining wall-clock time based on progress
                if elapsed_real_seconds > 10:  # Reduced threshold for faster feedback
                    estimated_total_seconds = elapsed_real_seconds * (100.0 / progress.percent_complete)
                    remaining_seconds = max(estimated_total_seconds - elapsed_real_seconds, 0)
                    progress.estimated_time_remaining = remaining_seconds / 3600.0  # Convert to hours
                    self.logger.debug(f"DEBUG_TIME_JSON: estimated_total_seconds={estimated_total_seconds:.1f}, remaining_seconds={remaining_seconds:.1f}, remaining_hours={progress.estimated_time_remaining:.3f}")
                else:
                    progress.estimated_time_remaining = 0.0  # Too early to estimate
                    self.logger.debug(f"DEBUG_TIME_JSON: Too early to estimate (< 10 seconds)")
            else:
                progress.estimated_time_remaining = 0.0
                self.logger.debug(f"DEBUG_TIME_JSON: Not estimating - percent_complete={progress.percent_complete:.2f}%")
            
            # Estimate heat released
            progress.heat_cumulative = progress.degree_of_hydration * 500.0
            
            progress.last_update = datetime.now()
            
            self.logger.debug(f"JSON progress parsed for '{operation_name}': Cycle={progress.cycle}, Time={progress.time_hours:.2f}h, DOH={progress.degree_of_hydration:.3f}")
            
        except Exception as e:
            self.logger.error(f"Error parsing JSON progress for '{operation_name}': {e}")
    
    def _parse_stdout_progress(self, operation_name: str, stdout_log_path: Path):
        """Parse progress from stdout log file (updated disrealnew implementation)."""
        try:
            if not stdout_log_path.exists():
                return
            
            simulation_info = self.active_simulations[operation_name]
            progress = simulation_info['progress']
            
            # Update timestamp
            progress.last_update = datetime.now()
            
            # Read the last 20 lines of the stdout log file to find latest PROGRESS line
            with open(stdout_log_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                
            # Look for the most recent PROGRESS line
            # Format: PROGRESS: Cycle=1224/2444 Time=673.078125 DOH=0.710882 Temp=25.000000 pH=13.351768
            latest_progress_line = None
            for line in reversed(lines[-20:]):
                if line.strip().startswith('PROGRESS:'):
                    latest_progress_line = line.strip()
                    break
            
            if latest_progress_line:
                import re
                
                # Parse cycle information: Cycle=1224/2444
                cycle_match = re.search(r'Cycle=(\d+)/(\d+)', latest_progress_line)
                if cycle_match:
                    current_cycle = int(cycle_match.group(1))
                    total_cycles = int(cycle_match.group(2))
                    progress.cycle = current_cycle
                    progress.max_cycles = total_cycles
                
                # Parse time: Time=673.078125
                time_match = re.search(r'Time=([\d.]+)', latest_progress_line)
                if time_match:
                    progress.time_hours = float(time_match.group(1))
                
                # Parse degree of hydration: DOH=0.710882
                doh_match = re.search(r'DOH=([\d.]+)', latest_progress_line)
                if doh_match:
                    progress.degree_of_hydration = float(doh_match.group(1))
                
                # Parse temperature: Temp=25.000000
                temp_match = re.search(r'Temp=([\d.]+)', latest_progress_line)
                if temp_match:
                    progress.temperature_celsius = float(temp_match.group(1))
                
                # Parse pH: pH=13.351768
                ph_match = re.search(r'pH=([\d.]+)', latest_progress_line)
                if ph_match:
                    progress.ph = float(ph_match.group(1))
                
                # Calculate percentage based on simulation time (most accurate)
                # Use time-based progress since users set max_time_hours as the primary stopping condition
                # Note: alpha and cycles often complete before the time limit, causing premature 100% display
                time_progress = 0.0
                if progress.end_time_hours > 0:
                    time_progress = (progress.time_hours / progress.end_time_hours) * 100.0

                # Cap at 99% to account for final I/O phase (~2 min after reaching time limit)
                # Progress will reach 100% only when operation status changes to COMPLETED
                progress.percent_complete = min(time_progress, 99.0)
                
                # Calculate remaining time based on wall-clock time and progress
                # Note: progress.time_hours is simulation time (hydration process time)
                # We need to estimate wall-clock remaining time based on actual elapsed time
                if progress.percent_complete > 0 and progress.percent_complete < 100.0:
                    # Calculate wall-clock elapsed time
                    start_time = simulation_info.get('start_time', datetime.now())
                    elapsed_real_seconds = (datetime.now() - start_time).total_seconds()
                    
                    self.logger.debug(f"DEBUG_TIME: percent_complete={progress.percent_complete:.2f}%, elapsed_real_seconds={elapsed_real_seconds:.1f}")
                    
                    # Estimate remaining wall-clock time based on progress
                    if elapsed_real_seconds > 10:  # Reduced threshold for faster feedback
                        estimated_total_seconds = elapsed_real_seconds * (100.0 / progress.percent_complete)
                        remaining_seconds = max(estimated_total_seconds - elapsed_real_seconds, 0)
                        progress.estimated_time_remaining = remaining_seconds / 3600.0  # Convert to hours
                        self.logger.debug(f"DEBUG_TIME: estimated_total_seconds={estimated_total_seconds:.1f}, remaining_seconds={remaining_seconds:.1f}, remaining_hours={progress.estimated_time_remaining:.3f}")
                    else:
                        progress.estimated_time_remaining = 0.0  # Too early to estimate
                        self.logger.debug(f"DEBUG_TIME: Too early to estimate (< 10 seconds)")
                else:
                    progress.estimated_time_remaining = 0.0
                    self.logger.debug(f"DEBUG_TIME: Not estimating - percent_complete={progress.percent_complete:.2f}%")
                
                # Estimate heat released (simplified calculation)
                # Typical portland cement releases ~500 kJ/kg at full hydration
                progress.heat_cumulative = progress.degree_of_hydration * 500.0
                
                self.logger.debug(f"Progress parsed for '{operation_name}': Cycle={progress.cycle}/{progress.max_cycles}, Time={progress.time_hours:.2f}h, DOH={progress.degree_of_hydration:.3f}")
            else:
                # Fallback to time-based estimation if no PROGRESS line found
                start_time = simulation_info['start_time']
                elapsed_minutes = (datetime.now() - start_time).total_seconds() / 60.0
                estimated_total_minutes = 120.0  # 2 hours typical
                progress.percent_complete = min((elapsed_minutes / estimated_total_minutes) * 100.0, 95.0)
                self.logger.debug(f"No PROGRESS line found for '{operation_name}', using time-based estimate: {progress.percent_complete:.1f}%")
            
        except Exception as e:
            self.logger.error(f"Error parsing stdout progress for '{operation_name}': {e}")
            # Fallback to basic time estimation on error
            try:
                simulation_info = self.active_simulations[operation_name]
                progress = simulation_info['progress']
                start_time = simulation_info['start_time']
                elapsed_minutes = (datetime.now() - start_time).total_seconds() / 60.0
                estimated_total_minutes = 120.0
                progress.percent_complete = min((elapsed_minutes / estimated_total_minutes) * 100.0, 95.0)
            except:
                pass
    
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
    
    def _check_simulation_completion(self, operation_name: str) -> bool:
        """
        Check if simulation completed successfully by examining output files.
        
        Args:
            operation_name: Name of the operation
            
        Returns:
            True if simulation completed successfully, False otherwise
        """
        try:
            operation_dir = self.operations_dir / operation_name

            # Check for key output files that indicate successful completion
            # Try to detect the actual microstructure name from the files in the directory
            microstructure_name = None
            
            # Method 1: Look for existing HydrationOf_*.csv files to determine the microstructure name
            hydration_csv_files = list(operation_dir.glob("HydrationOf_*.csv"))
            if hydration_csv_files:
                # Extract microstructure name from the CSV filename
                csv_filename = hydration_csv_files[0].stem  # e.g., "HydrationOf_Cem140Quartz07"
                microstructure_name = csv_filename.replace("HydrationOf_", "")
                self.logger.debug(f"Detected microstructure name from CSV: {microstructure_name}")
            
            # Method 2: If no CSV yet, look for .img files (microstructure files)
            if not microstructure_name:
                img_files = list(operation_dir.glob("*.img"))
                if img_files:
                    # Use the base name of the .img file (e.g., "Cem140Quartz07.img" -> "Cem140Quartz07")
                    microstructure_name = img_files[0].stem
                    self.logger.debug(f"Detected microstructure name from IMG: {microstructure_name}")
            
            # Method 3: Fallback for auto-generated names (legacy support)
            if not microstructure_name and operation_name.startswith('HydrationSim_'):
                # Remove "HydrationSim_" prefix and timestamp suffix to get microstructure name
                temp_name = operation_name.replace('HydrationSim_', '')
                # Find the microstructure name by removing the timestamp (format: _YYYYMMDD_HHMMSS)
                import re
                microstructure_name = re.sub(r'_\d{8}_\d{6}$', '', temp_name)
                self.logger.debug(f"Detected microstructure name from operation name: {microstructure_name}")
            
            # Method 4: Final fallback - use operation name
            if not microstructure_name:
                microstructure_name = operation_name
                self.logger.debug(f"Using operation name as microstructure name: {microstructure_name}")
                
            expected_files = [
                f"HydrationOf_{microstructure_name}.csv",  # Main data file
                f"HydrationOf_{microstructure_name}.mov",  # Movie file
                "progress.json"  # Progress file
            ]
            
            files_found = 0
            for expected_file in expected_files:
                file_path = operation_dir / expected_file
                if file_path.exists() and file_path.stat().st_size > 0:
                    files_found += 1
                    self.logger.debug(f"Found output file: {expected_file}")
            
            # Consider successful if at least 2 out of 3 expected files exist with content
            completion_successful = files_found >= 2
            
            if completion_successful:
                self.logger.info(f"Simulation completion verified by output files: {operation_name}")
            else:
                self.logger.warning(f"Simulation completion could not be verified: {operation_name} (found {files_found}/3 files)")
                
            return completion_successful
            
        except Exception as e:
            self.logger.error(f"Error checking simulation completion for '{operation_name}': {e}")
            return False
    
    def _update_operation_status(self, operation_name: str, status: OperationStatus):
        """Update operation status in database."""
        try:
            with self.database_service.get_session() as session:
                operation = session.query(Operation).filter_by(name=operation_name).first()

                # Create operation if it doesn't exist
                if not operation:
                    self.logger.info(f"Creating new operation: {operation_name}")
                    operation = Operation(
                        name=operation_name,
                        operation_type=OperationType.HYDRATION.value,
                        notes=f"Hydration simulation started at {datetime.now().isoformat()}"
                    )
                    session.add(operation)
                    session.flush()  # Ensure operation gets an ID

                # Update status
                operation.status = status.value
                if status == OperationStatus.RUNNING:
                    operation.mark_started()
                elif status == OperationStatus.COMPLETED:
                    operation.mark_completed()
                elif status == OperationStatus.ERROR:
                    operation.mark_error("Hydration simulation failed")
                elif status == OperationStatus.CANCELLED:
                    operation.mark_cancelled()

                session.commit()

                # Force SQLite WAL checkpoint after marking operation completed
                # This ensures changes are immediately visible to other connections
                if status == OperationStatus.COMPLETED:
                    try:
                        session.execute(text("PRAGMA wal_checkpoint(PASSIVE)"))
                        session.commit()
                        self.logger.info(f"WAL checkpoint completed for operation: {operation_name}")
                    except Exception as checkpoint_error:
                        self.logger.warning(f"WAL checkpoint failed (non-critical): {checkpoint_error}")

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
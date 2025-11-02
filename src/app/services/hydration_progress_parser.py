#!/usr/bin/env python3
"""
Hydration Progress Parser for VCCTL

Handles parsing of hydration simulation progress from various sources:
- Current disrealnew stdout output (text parsing)
- Future JSON progress files (structured parsing)
- Real-time output monitoring and extraction
"""

import re
import json
import logging
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from pathlib import Path

from app.services.hydration_executor_service import HydrationProgress


class HydrationProgressParser:
    """Parser for hydration simulation progress information."""
    
    def __init__(self):
        self.logger = logging.getLogger('VCCTL.HydrationProgressParser')
        
        # Regex patterns for parsing current disrealnew stdout
        self.cycle_pattern = re.compile(r'cycle[:\s]*(\d+)', re.IGNORECASE)
        self.time_pattern = re.compile(r'time[:\s]*=?\s*([0-9.]+)\s*h', re.IGNORECASE)
        self.alpha_pattern = re.compile(r'alpha[:\s]*=?\s*([0-9.]+)', re.IGNORECASE)
        self.temp_pattern = re.compile(r'temperature[:\s]*=?\s*([0-9.]+)\s*c', re.IGNORECASE)
        self.ph_pattern = re.compile(r'ph[:\s]*=?\s*([0-9.]+)', re.IGNORECASE)
        self.water_pattern = re.compile(r'water[_\s]*left[:\s]*=?\s*([0-9.]+)', re.IGNORECASE)
        self.heat_pattern = re.compile(r'heat[:\s]*=?\s*([0-9.]+)', re.IGNORECASE)
        
        # Phase count patterns
        self.phase_patterns = {
            'csh': re.compile(r'csh[_\s]*count[:\s]*=?\s*(\d+)', re.IGNORECASE),
            'ch': re.compile(r'ch[_\s]*count[:\s]*=?\s*(\d+)', re.IGNORECASE),
            'ettringite': re.compile(r'ettr[_\s]*count[:\s]*=?\s*(\d+)', re.IGNORECASE),
            'porosity': re.compile(r'pore[_\s]*count[:\s]*=?\s*(\d+)', re.IGNORECASE),
        }
    
    def parse_json_progress(self, json_file_path: str) -> Optional[HydrationProgress]:
        """
        Parse progress from JSON file (future implementation).
        
        Args:
            json_file_path: Path to JSON progress file
            
        Returns:
            HydrationProgress object or None if parsing failed
        """
        try:
            json_path = Path(json_file_path)
            if not json_path.exists():
                return None
            
            with open(json_path, 'r') as f:
                data = json.load(f)
            
            progress = HydrationProgress()
            
            # Parse simulation info
            sim_info = data.get('simulation_info', {})
            progress.cubesize = sim_info.get('cubesize', progress.cubesize)
            progress.max_cycles = sim_info.get('max_cycles', progress.max_cycles)
            progress.target_alpha = sim_info.get('target_alpha', progress.target_alpha)
            progress.end_time_hours = sim_info.get('end_time_hours', progress.end_time_hours)
            
            # Parse current state
            current_state = data.get('current_state', {})
            progress.cycle = current_state.get('cycle', 0)
            progress.time_hours = current_state.get('time_hours', 0.0)
            progress.degree_of_hydration = current_state.get('degree_of_hydration', 0.0)
            progress.temperature_celsius = current_state.get('temperature_celsius', 25.0)
            progress.ph = current_state.get('ph', 12.0)
            progress.water_left = current_state.get('water_left', 1.0)
            progress.heat_cumulative = current_state.get('heat_cumulative_kJ_per_kg', 0.0)
            
            # Parse progress metrics
            progress_info = data.get('progress', {})
            progress.percent_complete = progress_info.get('percent_complete', 0.0)
            progress.estimated_time_remaining = progress_info.get('estimated_time_remaining_hours', 0.0)
            progress.cycles_per_second = progress_info.get('cycles_per_second', 0.0)
            
            # Parse phase counts
            progress.phase_counts = data.get('phase_counts', {})
            
            # Parse timestamp
            timestamp_str = data.get('timestamp')
            if timestamp_str:
                try:
                    progress.last_update = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                except:
                    progress.last_update = datetime.now()
            else:
                progress.last_update = datetime.now()
            
            return progress
            
        except Exception as e:
            self.logger.error(f"Error parsing JSON progress from '{json_file_path}': {e}")
            return None
    
    def parse_stdout_progress(self, stdout_file_path: str, 
                            previous_progress: Optional[HydrationProgress] = None) -> Optional[HydrationProgress]:
        """
        Parse progress from stdout log file (current implementation).
        
        Args:
            stdout_file_path: Path to stdout log file
            previous_progress: Previous progress state for comparison
            
        Returns:
            HydrationProgress object or None if parsing failed
        """
        try:
            stdout_path = Path(stdout_file_path)
            if not stdout_path.exists():
                return None
            
            progress = previous_progress or HydrationProgress()
            
            # Read the last portion of the file for latest progress
            with open(stdout_path, 'r') as f:
                # Read last 100 lines to find latest progress information
                lines = self._tail_file(f, 100)
            
            # Parse lines for progress information
            latest_values = self._extract_latest_values(lines)
            
            # Update progress with extracted values
            if latest_values:
                progress.cycle = latest_values.get('cycle', progress.cycle)
                progress.time_hours = latest_values.get('time_hours', progress.time_hours)
                progress.degree_of_hydration = latest_values.get('degree_of_hydration', progress.degree_of_hydration)
                progress.temperature_celsius = latest_values.get('temperature_celsius', progress.temperature_celsius)
                progress.ph = latest_values.get('ph', progress.ph)
                progress.water_left = latest_values.get('water_left', progress.water_left)
                progress.heat_cumulative = latest_values.get('heat_cumulative', progress.heat_cumulative)
                
                # Update phase counts if found
                phase_counts = latest_values.get('phase_counts', {})
                if phase_counts:
                    progress.phase_counts.update(phase_counts)
                
                # Calculate progress percentage based on simulation time (primary metric)
                # Note: We use time_progress as the primary indicator because:
                #   - Users set max_time_hours as the stopping condition
                #   - alpha (degree of hydration) often reaches target before time limit
                #   - cycles are internal iteration steps not meaningful to users
                if progress.end_time_hours > 0:
                    time_progress = (progress.time_hours / progress.end_time_hours) * 100.0
                else:
                    time_progress = 0.0

                # Cap at 99% to account for final I/O phase (~2 min after reaching time limit)
                # Progress will reach 100% only when operation status changes to COMPLETED
                progress.percent_complete = min(time_progress, 99.0)
                
                # Estimate cycles per second
                if previous_progress and previous_progress.cycle > 0:
                    time_diff = (datetime.now() - previous_progress.last_update).total_seconds()
                    if time_diff > 0:
                        cycle_diff = progress.cycle - previous_progress.cycle
                        progress.cycles_per_second = cycle_diff / time_diff
                
                # Estimate time remaining
                if progress.cycles_per_second > 0 and progress.percent_complete < 100.0:
                    remaining_cycles = progress.max_cycles - progress.cycle
                    remaining_seconds = remaining_cycles / progress.cycles_per_second
                    progress.estimated_time_remaining = remaining_seconds / 3600.0  # Convert to hours
                
                progress.last_update = datetime.now()
            
            return progress
            
        except Exception as e:
            self.logger.error(f"Error parsing stdout progress from '{stdout_file_path}': {e}")
            return None
    
    def _tail_file(self, file_obj, num_lines: int) -> List[str]:
        """Read last N lines from a file efficiently."""
        try:
            # Move to end of file
            file_obj.seek(0, 2)
            file_size = file_obj.tell()
            
            if file_size == 0:
                return []
            
            # Read chunks backwards to find last N lines
            lines = []
            buffer_size = 8192
            position = file_size
            
            while len(lines) < num_lines and position > 0:
                # Calculate chunk size
                chunk_size = min(buffer_size, position)
                position -= chunk_size
                
                # Read chunk
                file_obj.seek(position)
                chunk = file_obj.read(chunk_size)
                
                # Split into lines and prepend to our list
                chunk_lines = chunk.split('\n')
                if position > 0:
                    # First line might be incomplete, combine with previous
                    if lines:
                        lines[0] = chunk_lines[-1] + lines[0]
                        chunk_lines = chunk_lines[:-1]
                
                lines = chunk_lines + lines
            
            # Return last num_lines, removing empty lines
            return [line for line in lines[-num_lines:] if line.strip()]
            
        except Exception as e:
            self.logger.error(f"Error reading tail of file: {e}")
            return []
    
    def _extract_latest_values(self, lines: List[str]) -> Dict[str, Any]:
        """
        Extract the latest progress values from output lines.
        
        Args:
            lines: List of output lines to parse
            
        Returns:
            Dictionary of extracted values
        """
        values = {}
        phase_counts = {}
        
        # Parse lines in reverse order to get latest values first
        for line in reversed(lines):
            line_lower = line.lower()
            
            # Skip if line contains common non-progress indicators
            if any(skip in line_lower for skip in ['error', 'warning', 'debug', 'enter', 'file']):
                continue
            
            # Extract cycle number
            if 'cycle' not in values:
                match = self.cycle_pattern.search(line)
                if match:
                    try:
                        values['cycle'] = int(match.group(1))
                    except ValueError:
                        pass
            
            # Extract time
            if 'time_hours' not in values:
                match = self.time_pattern.search(line)
                if match:
                    try:
                        values['time_hours'] = float(match.group(1))
                    except ValueError:
                        pass
            
            # Extract degree of hydration (alpha)
            if 'degree_of_hydration' not in values:
                match = self.alpha_pattern.search(line)
                if match:
                    try:
                        values['degree_of_hydration'] = float(match.group(1))
                    except ValueError:
                        pass
            
            # Extract temperature
            if 'temperature_celsius' not in values:
                match = self.temp_pattern.search(line)
                if match:
                    try:
                        values['temperature_celsius'] = float(match.group(1))
                    except ValueError:
                        pass
            
            # Extract pH
            if 'ph' not in values:
                match = self.ph_pattern.search(line)
                if match:
                    try:
                        values['ph'] = float(match.group(1))
                    except ValueError:
                        pass
            
            # Extract water left
            if 'water_left' not in values:
                match = self.water_pattern.search(line)
                if match:
                    try:
                        values['water_left'] = float(match.group(1))
                    except ValueError:
                        pass
            
            # Extract heat
            if 'heat_cumulative' not in values:
                match = self.heat_pattern.search(line)
                if match:
                    try:
                        values['heat_cumulative'] = float(match.group(1))
                    except ValueError:
                        pass
            
            # Extract phase counts
            for phase_name, pattern in self.phase_patterns.items():
                if phase_name not in phase_counts:
                    match = pattern.search(line)
                    if match:
                        try:
                            phase_counts[phase_name] = int(match.group(1))
                        except ValueError:
                            pass
        
        # Add phase counts if any were found
        if phase_counts:
            values['phase_counts'] = phase_counts
        
        return values
    
    def parse_simulation_parameters(self, param_file_path: str) -> Dict[str, Any]:
        """
        Parse simulation parameters from parameter file.
        
        Args:
            param_file_path: Path to parameter file
            
        Returns:
            Dictionary of simulation parameters
        """
        try:
            param_path = Path(param_file_path)
            if not param_path.exists():
                return {}
            
            parameters = {}
            
            with open(param_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        param_name = parts[0].strip()
                        param_value = parts[1].strip()
                        
                        # Try to convert to appropriate type
                        try:
                            if '.' in param_value:
                                parameters[param_name] = float(param_value)
                            else:
                                parameters[param_name] = int(param_value)
                        except ValueError:
                            parameters[param_name] = param_value
            
            return parameters
            
        except Exception as e:
            self.logger.error(f"Error parsing simulation parameters from '{param_file_path}': {e}")
            return {}
    
    def estimate_completion_time(self, progress: HydrationProgress, 
                               simulation_start_time: datetime) -> Optional[datetime]:
        """
        Estimate when the simulation will complete.
        
        Args:
            progress: Current progress information
            simulation_start_time: When the simulation started
            
        Returns:
            Estimated completion time or None if cannot estimate
        """
        try:
            if progress.percent_complete <= 0 or progress.percent_complete >= 100:
                return None
            
            elapsed_time = datetime.now() - simulation_start_time
            elapsed_seconds = elapsed_time.total_seconds()
            
            # Calculate time per percent complete
            time_per_percent = elapsed_seconds / progress.percent_complete
            
            # Calculate remaining time
            remaining_percent = 100.0 - progress.percent_complete
            remaining_seconds = time_per_percent * remaining_percent
            
            # Return estimated completion time
            return datetime.now() + datetime.timedelta(seconds=remaining_seconds)
            
        except Exception as e:
            self.logger.error(f"Error estimating completion time: {e}")
            return None
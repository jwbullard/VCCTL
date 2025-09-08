#!/usr/bin/env python3
"""
Grading File Management Utilities for VCCTL

Provides utilities for managing grading curve files (.gdg format) including:
- Reading and writing .gdg files
- Converting between formats
- File path management for operations
- Integration with Operations folder structure
"""

import logging
import os
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
import json


class GradingFileManager:
    """Manages grading curve files and their storage."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def write_gdg_file(self, operation_path: str, filename: str, 
                      sieve_data: List[Dict[str, float]], 
                      aggregate_type: str = None) -> str:
        """
        Write grading curve data to a .gdg file.
        
        Args:
            operation_path: Path to operation directory (Operations/{operation_name}/)
            filename: Name for the .gdg file (without extension)
            sieve_data: List of {'sieve_size': float, 'percent_passing': float}
            aggregate_type: Optional type info for file header
            
        Returns:
            Full path to created file
            
        Raises:
            IOError: If file cannot be written
        """
        try:
            # Ensure operation directory exists
            op_dir = Path(operation_path)
            op_dir.mkdir(parents=True, exist_ok=True)
            
            # Construct full file path
            gdg_filename = f"{filename}.gdg"
            full_path = op_dir / gdg_filename
            
            # Sort sieve data by size (largest first - standard format)
            sorted_data = sorted(sieve_data, key=lambda x: x['sieve_size'], reverse=True)
            
            # Write file content
            with open(full_path, 'w', encoding='utf-8') as f:
                # Optional header comment
                if aggregate_type:
                    f.write(f"# Grading curve for {aggregate_type} aggregate\n")
                    f.write(f"# Format: sieve_size_mm\tpercent_passing\n")
                
                # Write sieve data (tab-delimited)
                for point in sorted_data:
                    size = point['sieve_size']
                    percent = point['percent_passing']
                    f.write(f"{size:.3f}\t{percent:.1f}\n")
            
            self.logger.info(f"Created grading file: {full_path}")
            return str(full_path)
            
        except Exception as e:
            self.logger.error(f"Failed to write grading file {filename}: {e}")
            raise IOError(f"Could not write grading file: {e}")
    
    def read_gdg_file(self, file_path: str) -> List[Dict[str, float]]:
        """
        Read grading curve data from a .gdg file.
        
        Args:
            file_path: Path to the .gdg file
            
        Returns:
            List of {'sieve_size': float, 'percent_passing': float}
            
        Raises:
            IOError: If file cannot be read
            ValueError: If file format is invalid
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                raise IOError(f"Grading file not found: {file_path}")
            
            sieve_data = []
            
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue
                    
                    # Parse tab-delimited data
                    parts = line.split('\t')
                    if len(parts) < 2:
                        self.logger.warning(f"Invalid line {line_num} in {file_path}: {line}")
                        continue
                    
                    try:
                        size = float(parts[0])
                        percent = float(parts[1])
                        
                        # Basic validation
                        if size < 0 or percent < 0 or percent > 100:
                            self.logger.warning(f"Invalid values at line {line_num}: size={size}, percent={percent}")
                            continue
                        
                        sieve_data.append({
                            'sieve_size': size,
                            'percent_passing': percent
                        })
                        
                    except ValueError as e:
                        self.logger.warning(f"Could not parse line {line_num} in {file_path}: {line} ({e})")
                        continue
            
            if not sieve_data:
                raise ValueError(f"No valid sieve data found in {file_path}")
            
            self.logger.info(f"Read {len(sieve_data)} sieve points from {file_path}")
            return sieve_data
            
        except Exception as e:
            self.logger.error(f"Failed to read grading file {file_path}: {e}")
            raise
    
    def create_operation_grading_files(self, operation_name: str, 
                                     fine_grading_data: List[Dict[str, float]] = None,
                                     coarse_grading_data: List[Dict[str, float]] = None) -> Dict[str, str]:
        """
        Create grading files for an operation in the Operations directory.
        
        Args:
            operation_name: Name of the operation (used for folder)
            fine_grading_data: Optional fine aggregate grading data
            coarse_grading_data: Optional coarse aggregate grading data
            
        Returns:
            Dict with file paths: {'fine_grading_file': path, 'coarse_grading_file': path}
        """
        try:
            # Get project root and construct operation path
            project_root = Path(__file__).parent.parent.parent.parent
            operation_path = project_root / "Operations" / operation_name
            
            created_files = {}
            
            # Create fine aggregate grading file
            if fine_grading_data:
                fine_file = self.write_gdg_file(
                    operation_path=str(operation_path),
                    filename=f"{operation_name}_fine_grading",
                    sieve_data=fine_grading_data,
                    aggregate_type="fine"
                )
                created_files['fine_grading_file'] = fine_file
            
            # Create coarse aggregate grading file
            if coarse_grading_data:
                coarse_file = self.write_gdg_file(
                    operation_path=str(operation_path),
                    filename=f"{operation_name}_coarse_grading",
                    sieve_data=coarse_grading_data,
                    aggregate_type="coarse"
                )
                created_files['coarse_grading_file'] = coarse_file
            
            self.logger.info(f"Created {len(created_files)} grading files for operation: {operation_name}")
            return created_files
            
        except Exception as e:
            self.logger.error(f"Failed to create grading files for operation {operation_name}: {e}")
            raise
    
    def get_operation_grading_files(self, operation_name: str) -> Dict[str, Optional[str]]:
        """
        Find existing grading files for an operation.
        
        Args:
            operation_name: Name of the operation
            
        Returns:
            Dict with file paths or None: {'fine_grading_file': path, 'coarse_grading_file': path}
        """
        try:
            project_root = Path(__file__).parent.parent.parent.parent
            operation_path = project_root / "Operations" / operation_name
            
            result = {
                'fine_grading_file': None,
                'coarse_grading_file': None
            }
            
            if not operation_path.exists():
                return result
            
            # Look for grading files
            grading_files = list(operation_path.glob("*.gdg"))
            
            for gdg_file in grading_files:
                filename = gdg_file.stem.lower()
                
                # Check if it's a fine aggregate grading file
                if 'fine' in filename:
                    result['fine_grading_file'] = str(gdg_file)
                # Check if it's a coarse aggregate grading file
                elif 'coarse' in filename:
                    result['coarse_grading_file'] = str(gdg_file)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to find grading files for operation {operation_name}: {e}")
            return {'fine_grading_file': None, 'coarse_grading_file': None}
    
    def convert_grading_to_relative_paths(self, grading_files: Dict[str, str], 
                                        operation_name: str) -> Dict[str, str]:
        """
        Convert absolute grading file paths to relative paths for storage.
        
        Args:
            grading_files: Dict with absolute file paths
            operation_name: Name of the operation
            
        Returns:
            Dict with relative file paths from Operations directory
        """
        try:
            relative_paths = {}
            
            for key, abs_path in grading_files.items():
                if abs_path:
                    # Convert to relative path: Operations/{operation_name}/filename.gdg
                    path_obj = Path(abs_path)
                    relative_path = f"Operations/{operation_name}/{path_obj.name}"
                    relative_paths[key] = relative_path
                else:
                    relative_paths[key] = None
            
            return relative_paths
            
        except Exception as e:
            self.logger.error(f"Failed to convert paths to relative: {e}")
            return grading_files
    
    def resolve_relative_grading_paths(self, relative_paths: Dict[str, str]) -> Dict[str, str]:
        """
        Resolve relative grading file paths to absolute paths.
        
        Args:
            relative_paths: Dict with relative paths from project root
            
        Returns:
            Dict with absolute file paths
        """
        try:
            project_root = Path(__file__).parent.parent.parent.parent
            absolute_paths = {}
            
            for key, rel_path in relative_paths.items():
                if rel_path:
                    abs_path = project_root / rel_path
                    absolute_paths[key] = str(abs_path) if abs_path.exists() else None
                else:
                    absolute_paths[key] = None
            
            return absolute_paths
            
        except Exception as e:
            self.logger.error(f"Failed to resolve relative paths: {e}")
            return relative_paths
    
    def validate_grading_file(self, file_path: str) -> Tuple[bool, List[str]]:
        """
        Validate a grading file format and content.
        
        Args:
            file_path: Path to the grading file
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        try:
            file_path = Path(file_path)
            
            # Check if file exists
            if not file_path.exists():
                errors.append(f"File not found: {file_path}")
                return False, errors
            
            # Check file extension
            if file_path.suffix.lower() != '.gdg':
                errors.append(f"Expected .gdg extension, found: {file_path.suffix}")
            
            # Try to read and validate content
            try:
                sieve_data = self.read_gdg_file(str(file_path))
                
                if len(sieve_data) < 2:
                    errors.append("Grading file should have at least 2 sieve sizes")
                
                # Check for reasonable sieve size range
                sizes = [point['sieve_size'] for point in sieve_data]
                if max(sizes) - min(sizes) < 1.0:
                    errors.append("Sieve size range seems too small")
                
                # Check that percent passing generally decreases
                sorted_data = sorted(sieve_data, key=lambda x: x['sieve_size'], reverse=True)
                for i in range(1, len(sorted_data)):
                    if sorted_data[i]['percent_passing'] > sorted_data[i-1]['percent_passing'] + 10:
                        errors.append(f"Unusual trend: {sorted_data[i-1]['sieve_size']}mm to {sorted_data[i]['sieve_size']}mm")
                        break
                
            except Exception as e:
                errors.append(f"Could not parse file content: {e}")
            
        except Exception as e:
            errors.append(f"Validation error: {e}")
        
        return len(errors) == 0, errors


# Global instance for convenience
grading_file_manager = GradingFileManager()
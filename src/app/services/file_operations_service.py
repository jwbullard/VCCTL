#!/usr/bin/env python3
"""
File Operations Service for VCCTL

High-level service for file operations, import/export, and simulation file generation.
"""

import logging
import json
import csv
from io import StringIO
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable, Union, BinaryIO
from dataclasses import asdict

from .base_service import BaseService
from .directories_service import DirectoriesService
from ..utils.file_operations import (
    FileImportExport, FileValidator, ParallelFileWriter, 
    FileWriteTask, ProgressTracker, OptimizedFileWriter
)
from ..models.cement import Cement
from ..models.fly_ash import FlyAsh
from ..models.slag import Slag
from ..models.aggregate import Aggregate
from ..models.inert_filler import InertFiller


class FileOperationsService:
    """Service for file operations, import/export, and simulation file generation."""
    
    def __init__(self, directories_service: DirectoriesService):
        """
        Initialize file operations service.
        
        Args:
            directories_service: Service for directory management
        """
        self.directories_service = directories_service
        self.file_importer = FileImportExport(directories_service)
        self.validator = FileValidator()
        self.parallel_writer = ParallelFileWriter()
        self.logger = logging.getLogger('VCCTL.Services.FileOperations')
    
    # Material Import/Export Operations
    
    def import_material_from_file(self, file_path: Path, material_type: str) -> Dict[str, Any]:
        """
        Import material data from a file.
        
        Args:
            file_path: Path to the material file
            material_type: Type of material (cement, flyash, slag, etc.)
            
        Returns:
            Dictionary containing material data
            
        Raises:
            ValueError: If file validation or parsing fails
            IOError: If file cannot be read
        """
        # Validate file
        validation_result = self.validator.validate_file(file_path, max_size_mb=50)
        if not validation_result.is_valid:
            raise ValueError(f"File validation failed: {'; '.join(validation_result.errors)}")
        
        try:
            # Determine file format and parse
            if file_path.suffix.lower() == '.json':
                return self._import_json_material(file_path)
            elif file_path.suffix.lower() == '.csv':
                return self._import_csv_material(file_path, material_type)
            elif file_path.suffix.lower() == '.xml':
                return self._import_xml_material(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_path.suffix}")
                
        except Exception as e:
            self.logger.error(f"Failed to import material from {file_path}: {e}")
            raise
    
    def export_material_to_file(self, material_data: Dict[str, Any], 
                               export_path: Path, file_format: str = 'json') -> None:
        """
        Export material data to a file.
        
        Args:
            material_data: Material data to export
            export_path: Target export path
            file_format: Export format ('json', 'csv', 'xml')
            
        Raises:
            ValueError: If format is unsupported
            IOError: If export fails
        """
        try:
            if file_format.lower() == 'json':
                data = json.dumps(material_data, indent=2).encode('utf-8')
            elif file_format.lower() == 'csv':
                data = self._export_csv_material(material_data)
            elif file_format.lower() == 'xml':
                data = self._export_xml_material(material_data)
            else:
                raise ValueError(f"Unsupported export format: {file_format}")
            
            self.file_importer.export_material_file(
                data, material_data.get('name', 'unnamed'), export_path, file_format
            )
            
        except Exception as e:
            self.logger.error(f"Failed to export material to {export_path}: {e}")
            raise
    
    def batch_import_materials(self, source_dir: Path, material_type: str,
                              progress_callback: Optional[Callable[[int, int], None]] = None) -> List[Dict[str, Any]]:
        """
        Import multiple materials from a directory.
        
        Args:
            source_dir: Source directory containing material files
            material_type: Type of materials to import
            progress_callback: Optional progress callback (current, total)
            
        Returns:
            List of imported material data dictionaries
        """
        imported_materials = []
        
        try:
            # Find all supported files
            supported_extensions = {'.json', '.csv', '.xml'}
            material_files = [
                f for f in source_dir.rglob('*')
                if f.is_file() and f.suffix.lower() in supported_extensions
            ]
            
            total_files = len(material_files)
            self.logger.info(f"Starting batch import of {total_files} {material_type} files")
            
            for i, file_path in enumerate(material_files):
                try:
                    material_data = self.import_material_from_file(file_path, material_type)
                    imported_materials.append(material_data)
                    
                    if progress_callback:
                        progress_callback(i + 1, total_files)
                        
                except Exception as e:
                    self.logger.warning(f"Failed to import {file_path}: {e}")
            
            self.logger.info(f"Batch import completed: {len(imported_materials)}/{total_files} materials imported")
            
        except Exception as e:
            self.logger.error(f"Batch import failed: {e}")
            raise
        
        return imported_materials
    
    def batch_export_materials(self, materials_data: List[Dict[str, Any]], 
                              export_dir: Path, file_format: str = 'json',
                              progress_callback: Optional[Callable[[int, int], None]] = None) -> List[Path]:
        """
        Export multiple materials to files.
        
        Args:
            materials_data: List of material data dictionaries
            export_dir: Target export directory
            file_format: Export format
            progress_callback: Optional progress callback
            
        Returns:
            List of exported file paths
        """
        export_dir.mkdir(parents=True, exist_ok=True)
        exported_files = []
        
        try:
            total_materials = len(materials_data)
            self.logger.info(f"Starting batch export of {total_materials} materials")
            
            for i, material_data in enumerate(materials_data):
                try:
                    material_name = material_data.get('name', f'material_{i}')
                    safe_name = self.directories_service._sanitize_filename(material_name)
                    
                    file_extension = {'json': '.json', 'csv': '.csv', 'xml': '.xml'}[file_format]
                    export_path = export_dir / f"{safe_name}{file_extension}"
                    
                    self.export_material_to_file(material_data, export_path, file_format)
                    exported_files.append(export_path)
                    
                    if progress_callback:
                        progress_callback(i + 1, total_materials)
                        
                except Exception as e:
                    self.logger.warning(f"Failed to export material {material_data.get('name', 'unknown')}: {e}")
            
            self.logger.info(f"Batch export completed: {len(exported_files)}/{total_materials} materials exported")
            
        except Exception as e:
            self.logger.error(f"Batch export failed: {e}")
            raise
        
        return exported_files
    
    # Simulation File Generation
    
    def generate_cement_correlation_files(self, cement: Cement, operation_name: str) -> List[Path]:
        """
        Generate correlation files for cement in an operation directory.
        
        Args:
            cement: Cement model instance
            operation_name: Name of the operation
            
        Returns:
            List of generated file paths
        """
        operation_dir = self.directories_service.get_operation_dir(operation_name)
        
        # Define file write tasks based on cement properties
        tasks = []
        generated_files = []
        
        # Create tasks for each cement property file
        file_mappings = [
            ('sil', cement.sil),
            ('c3s', cement.c3s),
            ('c4f', cement.c4f),
            ('c3a', cement.c3a),
            ('n2o', cement.n2o),
            ('k2o', cement.k2o),
            ('alu', cement.alu)
        ]
        
        for suffix, data in file_mappings:
            if data is not None:
                file_path = operation_dir / f"{cement.name}.{suffix}"
                tasks.append(FileWriteTask(file_path, lambda d=data: d))
                generated_files.append(file_path)
        
        try:
            # Write files in parallel
            self.parallel_writer.write_files(tasks)
            self.logger.info(f"Generated {len(generated_files)} cement correlation files for {cement.name}")
            
        except Exception as e:
            self.logger.error(f"Failed to generate cement correlation files: {e}")
            raise
        
        return generated_files
    
    def generate_mix_input_files(self, mix_data: Dict[str, Any], operation_name: str) -> List[Path]:
        """
        Generate input files for mix design simulation.
        
        Args:
            mix_data: Mix design data
            operation_name: Name of the operation
            
        Returns:
            List of generated file paths
        """
        operation_dir = self.directories_service.get_operation_dir(operation_name)
        generated_files = []
        
        try:
            # Generate main mix parameters file
            mix_params_path = operation_dir / "mix_params.json"
            mix_params_data = json.dumps(mix_data, indent=2).encode('utf-8')
            OptimizedFileWriter.write_file(mix_params_path, mix_params_data)
            generated_files.append(mix_params_path)
            
            # Generate individual component files if needed
            if 'water_binder_ratio' in mix_data:
                wb_ratio_path = operation_dir / "wb_ratio.txt"
                wb_data = str(mix_data['water_binder_ratio']).encode('utf-8')
                OptimizedFileWriter.write_file(wb_ratio_path, wb_data)
                generated_files.append(wb_ratio_path)
            
            # Generate aggregate grading files
            if 'aggregates' in mix_data:
                for i, aggregate in enumerate(mix_data['aggregates']):
                    agg_path = operation_dir / f"aggregate_{i}_grading.csv"
                    agg_data = self._generate_aggregate_grading_csv(aggregate)
                    OptimizedFileWriter.write_file(agg_path, agg_data.encode('utf-8'))
                    generated_files.append(agg_path)
            
            self.logger.info(f"Generated {len(generated_files)} mix input files for operation {operation_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to generate mix input files: {e}")
            raise
        
        return generated_files
    
    def generate_microstructure_input_files(self, microstructure_params: Dict[str, Any], 
                                          operation_name: str) -> List[Path]:
        """
        Generate input files for microstructure generation.
        
        Args:
            microstructure_params: Microstructure parameters
            operation_name: Name of the operation
            
        Returns:
            List of generated file paths
        """
        operation_dir = self.directories_service.get_operation_dir(operation_name)
        generated_files = []
        
        try:
            # Generate main microstructure input file
            micro_input_path = operation_dir / "microstructure.in"
            micro_input_data = self._generate_microstructure_input(microstructure_params)
            OptimizedFileWriter.write_file(micro_input_path, micro_input_data.encode('utf-8'))
            generated_files.append(micro_input_path)
            
            # Generate particle shape set files if specified
            if 'particle_shape_sets' in microstructure_params:
                for shape_set in microstructure_params['particle_shape_sets']:
                    shape_path = operation_dir / f"shape_{shape_set['name']}.dat"
                    shape_data = self._generate_particle_shape_data(shape_set)
                    OptimizedFileWriter.write_file(shape_path, shape_data)
                    generated_files.append(shape_path)
            
            self.logger.info(f"Generated {len(generated_files)} microstructure input files")
            
        except Exception as e:
            self.logger.error(f"Failed to generate microstructure input files: {e}")
            raise
        
        return generated_files
    
    # File Validation and Utilities
    
    def validate_simulation_files(self, operation_name: str) -> Dict[str, Any]:
        """
        Validate all files in an operation directory.
        
        Args:
            operation_name: Name of the operation
            
        Returns:
            Validation results dictionary
        """
        operation_dir = self.directories_service.get_operation_dir(operation_name)
        validation_results = {
            'is_valid': True,
            'files_checked': 0,
            'files_valid': 0,
            'errors': [],
            'warnings': []
        }
        
        try:
            for file_path in operation_dir.rglob('*'):
                if file_path.is_file():
                    validation_results['files_checked'] += 1
                    
                    # Validate individual file
                    file_result = self.validator.validate_file(file_path, max_size_mb=1000)
                    
                    if file_result.is_valid:
                        validation_results['files_valid'] += 1
                    else:
                        validation_results['is_valid'] = False
                        validation_results['errors'].extend([
                            f"{file_path.name}: {error}" for error in file_result.errors
                        ])
                    
                    validation_results['warnings'].extend([
                        f"{file_path.name}: {warning}" for warning in file_result.warnings
                    ])
            
            self.logger.info(f"Validated {validation_results['files_checked']} files in operation {operation_name}")
            
        except Exception as e:
            validation_results['is_valid'] = False
            validation_results['errors'].append(f"Validation failed: {e}")
            self.logger.error(f"File validation failed for operation {operation_name}: {e}")
        
        return validation_results
    
    def cleanup_operation_files(self, operation_name: str, 
                               keep_inputs: bool = True, keep_outputs: bool = False) -> int:
        """
        Clean up files in an operation directory.
        
        Args:
            operation_name: Name of the operation
            keep_inputs: Whether to keep input files
            keep_outputs: Whether to keep output files
            
        Returns:
            Number of files removed
        """
        operation_dir = self.directories_service.get_operation_dir(operation_name)
        files_removed = 0
        
        try:
            for file_path in operation_dir.rglob('*'):
                if file_path.is_file():
                    should_remove = False
                    
                    # Determine if file should be removed based on type
                    if file_path.suffix.lower() in {'.tmp', '.log', '.cache'}:
                        should_remove = True
                    elif not keep_inputs and file_path.suffix.lower() in {'.in', '.json', '.csv'}:
                        should_remove = True
                    elif not keep_outputs and file_path.suffix.lower() in {'.out', '.dat', '.img'}:
                        should_remove = True
                    
                    if should_remove:
                        try:
                            file_path.unlink()
                            files_removed += 1
                        except Exception as e:
                            self.logger.warning(f"Failed to remove {file_path}: {e}")
            
            self.logger.info(f"Cleaned up {files_removed} files from operation {operation_name}")
            
        except Exception as e:
            self.logger.error(f"Cleanup failed for operation {operation_name}: {e}")
        
        return files_removed
    
    # Private helper methods
    
    def _import_json_material(self, file_path: Path) -> Dict[str, Any]:
        """Import material from JSON file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _import_csv_material(self, file_path: Path, material_type: str) -> Dict[str, Any]:
        """Import material from CSV file."""
        material_data = {'type': material_type}
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert numeric values
                for key, value in row.items():
                    try:
                        if '.' in value:
                            material_data[key] = float(value)
                        else:
                            material_data[key] = int(value)
                    except (ValueError, TypeError):
                        material_data[key] = value
                break  # Take first row for single material
        
        return material_data
    
    def _import_xml_material(self, file_path: Path) -> Dict[str, Any]:
        """Import material from XML file."""
        # Basic XML parsing - would need proper XML library for production
        import xml.etree.ElementTree as ET
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        material_data = {}
        for element in root:
            if element.text:
                try:
                    material_data[element.tag] = float(element.text)
                except ValueError:
                    material_data[element.tag] = element.text
        
        return material_data
    
    def _export_csv_material(self, material_data: Dict[str, Any]) -> bytes:
        """Export material to CSV format."""
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(material_data.keys())
        # Write data
        writer.writerow(material_data.values())
        
        return output.getvalue().encode('utf-8')
    
    def _export_xml_material(self, material_data: Dict[str, Any]) -> bytes:
        """Export material to XML format."""
        import xml.etree.ElementTree as ET
        
        root = ET.Element('material')
        for key, value in material_data.items():
            element = ET.SubElement(root, key)
            element.text = str(value)
        
        return ET.tostring(root, encoding='utf-8', xml_declaration=True)
    
    def _generate_aggregate_grading_csv(self, aggregate_data: Dict[str, Any]) -> str:
        """Generate CSV data for aggregate grading."""
        output = StringIO()
        writer = csv.writer(output)
        
        writer.writerow(['Sieve_Size_mm', 'Percent_Passing'])
        
        if 'grading' in aggregate_data:
            for size, percent in aggregate_data['grading'].items():
                writer.writerow([size, percent])
        
        return output.getvalue()
    
    def _generate_microstructure_input(self, params: Dict[str, Any]) -> str:
        """Generate microstructure input file content."""
        lines = []
        
        # System dimensions
        if 'system_size' in params:
            lines.append(f"SYSTEMSIZE {params['system_size']}")
        
        if 'resolution' in params:
            lines.append(f"RESOLUTION {params['resolution']}")
        
        # Random seed
        if 'random_seed' in params:
            lines.append(f"RANDSEED {params['random_seed']}")
        
        # Flocculation parameters
        if 'flocculation' in params:
            floc = params['flocculation']
            lines.append(f"FLOCCULATION {floc.get('enable', 0)}")
            if floc.get('enable'):
                lines.append(f"FLOCPROB {floc.get('probability', 0.5)}")
        
        return '\n'.join(lines) + '\n'
    
    def _generate_particle_shape_data(self, shape_set: Dict[str, Any]) -> bytes:
        """Generate binary particle shape data."""
        # This would generate actual binary shape data in production
        # For now, return placeholder binary data
        return b'\x00' * 1024  # Placeholder binary data
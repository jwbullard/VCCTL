#!/usr/bin/env python3
"""
Elastic Input File Generator

Generates properly formatted input files for the elastic.c program based on:
- Resolved lineage data from ElasticLineageService
- Selected hydrated microstructure
- Relative path resolution
- ITZ detection logic

Creates input file that responds to all elastic.c interactive prompts.
"""

import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.services.elastic_lineage_service import ElasticLineageService, HydratedMicrostructure, AggregateProperties
from app.models.elastic_moduli_operation import ElasticModuliOperation


class ElasticInputGenerator:
    """Service for generating elastic.c input files from resolved operation data."""
    
    def __init__(self, lineage_service: ElasticLineageService):
        self.lineage_service = lineage_service
        self.logger = logging.getLogger(__name__)
    
    def generate_input_file(
        self,
        operation: ElasticModuliOperation,
        selected_microstructure: HydratedMicrostructure,
        output_directory: str
    ) -> str:
        """
        Generate complete elastic.c input file.
        
        Args:
            operation: Elastic moduli operation with all parameters
            selected_microstructure: Selected hydrated microstructure
            output_directory: Directory to create input file (elastic operation directory)
            
        Returns:
            Path to generated input file
        """
        # Resolve lineage data
        lineage = self.lineage_service.resolve_lineage_chain(operation.hydration_operation_id, output_directory)
        
        # Create output directory
        output_path = Path(output_directory)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Generate input file content
        input_lines = self._generate_input_responses(
            operation, 
            selected_microstructure,
            lineage,
            output_directory
        )
        
        # Write input file
        input_file_path = output_path / "elastic_input.txt"
        with open(input_file_path, 'w') as f:
            f.write('\n'.join(input_lines) + '\n')
        
        # Also create a human-readable summary
        summary_file_path = output_path / "elastic_input_summary.txt" 
        self._write_input_summary(summary_file_path, operation, selected_microstructure, lineage)
        
        self.logger.info(f"Generated elastic input file: {input_file_path}")
        return str(input_file_path)
    
    def _generate_input_responses(
        self,
        operation: ElasticModuliOperation,
        selected_microstructure: HydratedMicrostructure,
        lineage: Dict[str, Any],
        output_directory: str
    ) -> List[str]:
        """Generate list of input responses for elastic.c prompts."""
        
        responses = []
        
        # Convert paths to relative from output directory
        microstructure_path = self.lineage_service.convert_to_relative_path(
            selected_microstructure.file_path, output_directory
        )
        pimg_path = self.lineage_service.convert_to_relative_path(
            selected_microstructure.pimg_path, output_directory
        )
        
        # Get aggregate properties
        aggregate_props = lineage.get('aggregate_properties', {})
        fine_agg = aggregate_props.get('fine_aggregate')
        coarse_agg = aggregate_props.get('coarse_aggregate')
        
        # Get volume fractions
        volume_fractions = lineage.get('volume_fractions', {})
        
        # Response 1: "Enter full path and name of file with input microstructure:"
        responses.append(microstructure_path)
        
        # Response 2: "Enter whether to break connections between anhydrous cement particles (1) or not (0):"
        # Always 1 according to elastic.c logic (line 215: Sever = 1;)
        responses.append("1")
        
        # Response 3: "ITZ Calculation? (1 for Yes, 0 for No):"
        has_itz = self.lineage_service.get_itz_detection(aggregate_props)
        responses.append("1" if has_itz else "0")
        
        # Response 4: "Enter name of folder to output data files (Include final separator in path):"
        responses.append("./")  # Current directory (operation directory)
        
        # Response 5: "Enter name of file with particle ids"
        responses.append(pimg_path)
        
        # If ITZ calculation is enabled, add aggregate data
        if has_itz:
            # Fine aggregate data (up to NUMFINESOURCES=2)
            if fine_agg:
                # "Enter volume fraction of fine aggregate 1:"
                responses.append(str(fine_agg.volume_fraction))
                
                # Additional fine aggregate prompts based on elastic.c logic
                responses.append(fine_agg.name)  # Aggregate name/description
                responses.append(str(fine_agg.bulk_modulus))   # Bulk modulus (GPa)
                responses.append(str(fine_agg.shear_modulus))  # Shear modulus (GPa)
                
                # Grading file path (relative)
                if fine_agg.grading_path:
                    grading_relative = self.lineage_service.convert_to_relative_path(
                        fine_agg.grading_path, output_directory
                    )
                    responses.append(grading_relative)
                else:
                    responses.append("")  # No grading file
            else:
                responses.append("0.0")  # No fine aggregate
            
            # Second fine aggregate (usually not used)
            responses.append("0.0")
            
            # Coarse aggregate data (up to NUMCOARSESOURCES=2)
            if coarse_agg:
                # "Enter volume fraction of coarse aggregate 1:"
                responses.append(str(coarse_agg.volume_fraction))
                
                # Additional coarse aggregate prompts
                responses.append(coarse_agg.name)  # Aggregate name/description
                responses.append(str(coarse_agg.bulk_modulus))   # Bulk modulus (GPa)
                responses.append(str(coarse_agg.shear_modulus))  # Shear modulus (GPa)
                
                # Grading file path
                if coarse_agg.grading_path:
                    grading_relative = self.lineage_service.convert_to_relative_path(
                        coarse_agg.grading_path, output_directory
                    )
                    responses.append(grading_relative)
                else:
                    responses.append("")  # No grading file
            else:
                responses.append("0.0")  # No coarse aggregate
            
            # Second coarse aggregate (usually not used)
            responses.append("0.0")
            
            # "Enter the volume fraction of air:"
            air_fraction = volume_fractions.get('air_volume_fraction', 0.0)
            responses.append(str(air_fraction))
        
        self.logger.info(f"Generated {len(responses)} input responses for elastic.c")
        return responses
    
    def _write_input_summary(
        self,
        summary_file_path: Path,
        operation: ElasticModuliOperation,
        selected_microstructure: HydratedMicrostructure,
        lineage: Dict[str, Any]
    ):
        """Write human-readable summary of input parameters."""
        
        with open(summary_file_path, 'w') as f:
            f.write(f"Elastic Moduli Calculation Input Summary\n")
            f.write(f"========================================\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Operation: {operation.name}\n\n")
            
            f.write(f"Lineage Chain:\n")
            hydration_op = lineage.get('hydration_operation')
            microstructure_op = lineage.get('microstructure_operation')
            
            if microstructure_op:
                f.write(f"  Microstructure: {microstructure_op.name}\n")
            if hydration_op:
                f.write(f"  Hydration: {hydration_op.name}\n")
            f.write(f"  Elastic: {operation.name}\n\n")
            
            f.write(f"Selected Microstructure:\n")
            f.write(f"  File: {selected_microstructure.file_path}\n")
            f.write(f"  Time: {selected_microstructure.time_label}\n")
            f.write(f"  Final: {selected_microstructure.is_final}\n\n")
            
            # Aggregate properties
            aggregate_props = lineage.get('aggregate_properties', {})
            fine_agg = aggregate_props.get('fine_aggregate')
            coarse_agg = aggregate_props.get('coarse_aggregate')
            
            f.write(f"Aggregate Properties:\n")
            if fine_agg:
                f.write(f"  Fine Aggregate: {fine_agg.name}\n")
                f.write(f"    Volume Fraction: {fine_agg.volume_fraction:.4f}\n")
                f.write(f"    Bulk Modulus: {fine_agg.bulk_modulus:.1f} GPa\n")
                f.write(f"    Shear Modulus: {fine_agg.shear_modulus:.1f} GPa\n")
            else:
                f.write(f"  Fine Aggregate: None\n")
            
            if coarse_agg:
                f.write(f"  Coarse Aggregate: {coarse_agg.name}\n")
                f.write(f"    Volume Fraction: {coarse_agg.volume_fraction:.4f}\n")
                f.write(f"    Bulk Modulus: {coarse_agg.bulk_modulus:.1f} GPa\n")
                f.write(f"    Shear Modulus: {coarse_agg.shear_modulus:.1f} GPa\n")
            else:
                f.write(f"  Coarse Aggregate: None\n")
            
            # Volume fractions
            volume_fractions = lineage.get('volume_fractions', {})
            f.write(f"\nVolume Fractions:\n")
            f.write(f"  Fine Aggregate: {volume_fractions.get('fine_aggregate_volume_fraction', 0.0):.4f}\n")
            f.write(f"  Coarse Aggregate: {volume_fractions.get('coarse_aggregate_volume_fraction', 0.0):.4f}\n")
            f.write(f"  Air: {volume_fractions.get('air_volume_fraction', 0.0):.4f}\n")
            
            total_vf = sum(volume_fractions.values())
            f.write(f"  Total: {total_vf:.4f}\n")
            
            # ITZ calculation
            has_itz = self.lineage_service.get_itz_detection(aggregate_props)
            f.write(f"\nITZ Calculation: {'Enabled' if has_itz else 'Disabled'}\n")
            
            # Mix design data
            mix_design_data = lineage.get('mix_design_data', {})
            f.write(f"\nMix Design Summary:\n")
            f.write(f"  Fine Aggregate Name: {mix_design_data.get('fine_aggregate_name', 'None')}\n")
            f.write(f"  Coarse Aggregate Name: {mix_design_data.get('coarse_aggregate_name', 'None')}\n")
            f.write(f"  W/B Ratio: {mix_design_data.get('water_binder_ratio', 'Unknown')}\n")
            f.write(f"  Air Content: {mix_design_data.get('air_volume_fraction', 0.0):.3f}\n")
    
    def validate_input_completeness(
        self,
        operation: ElasticModuliOperation,
        selected_microstructure: HydratedMicrostructure
    ) -> List[str]:
        """
        Validate that all necessary data is available for input generation.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Validate microstructure file exists
        microstructure_path = Path(selected_microstructure.file_path)
        if not microstructure_path.exists():
            errors.append(f"Microstructure file not found: {selected_microstructure.file_path}")
        
        # Validate PIMG file exists
        pimg_path = Path(selected_microstructure.pimg_path)
        if not pimg_path.exists():
            errors.append(f"PIMG file not found: {selected_microstructure.pimg_path}")
        
        # Validate operation has hydration reference
        if not operation.hydration_operation_id:
            errors.append("Operation must reference a hydration operation")
        
        # Validate lineage completeness
        try:
            lineage = self.lineage_service.resolve_lineage_chain(operation.hydration_operation_id)
            lineage_errors = self.lineage_service.validate_lineage_completeness(lineage)
            errors.extend(lineage_errors)
        except Exception as e:
            errors.append(f"Error resolving lineage chain: {str(e)}")
        
        return errors
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

        # Copy cement PSD file to hydration operation directory (parent of elastic)
        self._copy_cement_psd_file(lineage, output_directory)

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
        
        # If ITZ calculation is enabled, add concrete (concelas) data
        if has_itz:
            # Response 6 (concelas function): "Enter fully resolved name of cement PSD file:"
            # Find cement PSD file in the source microstructure operation folder
            cement_psd_path = self._find_cement_psd_file(lineage, output_directory)
            responses.append(cement_psd_path)

            # Fine aggregate data (only one source supported)
            # Always output all four values regardless of volume fraction
            if fine_agg:
                # "Enter volume fraction of fine aggregate:"
                responses.append(str(fine_agg.volume_fraction))

                # Grading file path - elastic.c now always reads this
                if fine_agg.grading_path:
                    # The grading_path is already relative to the operation directory
                    responses.append(fine_agg.grading_path)
                else:
                    responses.append("./dummy.gdg")  # Placeholder file path

                # Bulk and shear modulus - elastic.c now always reads these
                responses.append(str(fine_agg.bulk_modulus))   # Bulk modulus (GPa)
                responses.append(str(fine_agg.shear_modulus))  # Shear modulus (GPa)
            else:
                # No fine aggregate - still provide all four values
                responses.append("0.0")           # Volume fraction = 0
                responses.append("./dummy.gdg")   # Placeholder grading file
                responses.append("30.0")          # Default bulk modulus
                responses.append("18.0")          # Default shear modulus
            
            # Coarse aggregate data (only one source supported)
            # Always output all four values regardless of volume fraction
            if coarse_agg:
                # "Enter volume fraction of coarse aggregate:"
                responses.append(str(coarse_agg.volume_fraction))

                # Grading file path - elastic.c now always reads this
                if coarse_agg.grading_path:
                    # The grading_path is already relative to the operation directory
                    responses.append(coarse_agg.grading_path)
                else:
                    responses.append("./dummy.gdg")  # Placeholder file path

                # Bulk and shear modulus - elastic.c now always reads these
                responses.append(str(coarse_agg.bulk_modulus))   # Bulk modulus (GPa)
                responses.append(str(coarse_agg.shear_modulus))  # Shear modulus (GPa)
            else:
                # No coarse aggregate - still provide all four values
                responses.append("0.0")           # Volume fraction = 0
                responses.append("./dummy.gdg")   # Placeholder grading file
                responses.append("36.7")          # Default bulk modulus
                responses.append("22.0")          # Default shear modulus
            
            # "Enter the volume fraction of air:"
            air_fraction = volume_fractions.get('air_volume_fraction', 0.0)
            responses.append(str(air_fraction))
        
        self.logger.info(f"Generated {len(responses)} input responses for elastic.c")
        return responses

    def _find_cement_psd_file(self, lineage: Dict[str, Any], elastic_output_directory: str) -> str:
        """Find cement PSD file in the parent hydration operation directory."""
        try:
            from pathlib import Path
            elastic_dir = Path(elastic_output_directory)
            hydration_dir = elastic_dir.parent  # Go up one level to hydration directory

            # Look for cement PSD file in the hydration directory
            cement_psd_file = hydration_dir / "cement_psd.csv"

            # Check if it exists in the hydration directory
            if cement_psd_file.exists():
                # Return relative path from elastic directory to cement PSD file (up one level)
                relative_path = "../cement_psd.csv"
                self.logger.info(f"Found cement PSD file in hydration directory: {relative_path}")
                return relative_path
            else:
                # If not found, try to find it from microstructure operation
                microstructure_name = lineage.get('microstructure_operation_name')
                if microstructure_name:
                    project_root = hydration_dir.parent  # Go up to Operations directory
                    microstructure_folder = project_root / microstructure_name
                    source_cement_psd_file = microstructure_folder / "cement_psd.csv"

                    if source_cement_psd_file.exists():
                        # Create relative path from elastic directory to microstructure cement PSD file
                        relative_path = self.lineage_service.convert_to_relative_path(
                            str(source_cement_psd_file), elastic_output_directory
                        )
                        self.logger.warning(f"Cement PSD not in hydration dir, using microstructure path: {relative_path}")
                        return relative_path

                self.logger.warning("Cement PSD file not found, using default path")
                return "../cement_psd.csv"  # Reference parent directory even if file doesn't exist yet

        except Exception as e:
            self.logger.error(f"Error finding cement PSD file: {e}")
            return "../cement_psd.csv"  # Reference parent directory as default

    def _copy_cement_psd_file(self, lineage: Dict[str, Any], elastic_output_directory: str) -> str:
        """Copy cement PSD file from microstructure operation to hydration operation directory."""
        try:
            # Get the microstructure operation name from lineage
            microstructure_name = lineage.get('microstructure_operation_name')
            if not microstructure_name:
                self.logger.warning("No microstructure operation name in lineage")
                # Create in hydration directory, not elastic directory
                hydration_dir = Path(elastic_output_directory).parent
                return self._create_default_cement_psd_file(str(hydration_dir))

            # Construct path to microstructure operation folder
            elastic_dir = Path(elastic_output_directory)
            hydration_dir = elastic_dir.parent  # Go up one level to hydration directory
            project_root = hydration_dir.parent  # Go up to Operations directory
            microstructure_folder = project_root / microstructure_name
            source_cement_psd_file = microstructure_folder / "cement_psd.csv"

            # Destination path in HYDRATION operation directory (one level up from elastic)
            dest_cement_psd_file = hydration_dir / "cement_psd.csv"

            # Only copy if it doesn't already exist in the hydration directory
            if not dest_cement_psd_file.exists():
                if source_cement_psd_file.exists():
                    # Copy the file
                    import shutil
                    shutil.copy2(source_cement_psd_file, dest_cement_psd_file)
                    self.logger.info(f"Copied cement PSD file from {source_cement_psd_file} to {dest_cement_psd_file}")
                else:
                    self.logger.warning(f"Source cement PSD file not found at {source_cement_psd_file}")
                    self._create_default_cement_psd_file(str(hydration_dir))
            else:
                self.logger.info(f"Cement PSD file already exists in hydration directory: {dest_cement_psd_file}")

            return str(dest_cement_psd_file)

        except Exception as e:
            self.logger.error(f"Error copying cement PSD file: {e}")
            hydration_dir = Path(elastic_output_directory).parent
            return self._create_default_cement_psd_file(str(hydration_dir))

    def _create_default_cement_psd_file(self, output_directory: str) -> str:
        """Create a default cement PSD file in the specified directory (usually hydration directory)."""
        try:
            output_dir = Path(output_directory)
            dest_cement_psd_file = output_dir / "cement_psd.csv"

            # Generate default cement PSD data (typical Portland cement distribution)
            default_psd_data = [
                (1.0, 0.05),    # Very fine particles
                (2.0, 0.08),
                (4.0, 0.12),
                (8.0, 0.15),
                (16.0, 0.20),
                (32.0, 0.18),
                (45.0, 0.12),
                (63.0, 0.08),
                (90.0, 0.02)    # Coarser particles
            ]

            # Write PSD file in required CSV format
            with open(dest_cement_psd_file, 'w') as f:
                # Write CSV header as required by elastic.c
                f.write("Diameter_micrometers,Volume_Fraction\n")

                # Write data in comma-delimited format
                for diameter_um, volume_fraction in default_psd_data:
                    f.write(f"{diameter_um:.3f},{volume_fraction:.6f}\n")

            self.logger.info(f"Created default cement PSD file: {dest_cement_psd_file}")
            return str(dest_cement_psd_file)

        except Exception as e:
            self.logger.error(f"Error creating default cement PSD file: {e}")
            raise

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
#!/usr/bin/env python3
"""
Elastic Moduli Lineage Resolution Service

Handles complete lineage tracking for elastic moduli operations:
Elastic → Hydration → Microstructure → Mix Design → Aggregate Properties

Provides services for:
- Tracing operation lineage chains
- Extracting aggregate properties from database
- Resolving volume fractions from mix design components
- Finding hydrated microstructures with time steps
- Converting file paths to relative paths
"""

import logging
import os
import re
import glob
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.operation import Operation, OperationStatus, OperationType
from app.models.mix_design import MixDesign
from app.models.aggregate import Aggregate
from app.services.service_container import ServiceContainer


class HydratedMicrostructure:
    """Represents a hydrated microstructure file with time information."""
    
    def __init__(self, file_path: str, time_label: str, is_final: bool = False):
        self.file_path = file_path
        self.time_label = time_label
        self.is_final = is_final
        self.pimg_path = file_path.replace('.img', '.pimg')
    
    def __repr__(self):
        return f"<HydratedMicrostructure(time='{self.time_label}', final={self.is_final})>"


class AggregateProperties:
    """Represents aggregate mechanical and physical properties."""
    
    def __init__(self, name: str, bulk_modulus: float, shear_modulus: float, 
                 volume_fraction: float, grading_path: str = None):
        self.name = name
        self.bulk_modulus = bulk_modulus
        self.shear_modulus = shear_modulus
        self.volume_fraction = volume_fraction
        self.grading_path = grading_path or ""
    
    def __repr__(self):
        return f"<AggregateProperties(name='{self.name}', bulk={self.bulk_modulus}, shear={self.shear_modulus}, vf={self.volume_fraction})>"


class ElasticLineageService:
    """Service for resolving elastic moduli operation lineage and dependencies."""
    
    def __init__(self, service_container: ServiceContainer):
        self.service_container = service_container
        self.database_service = service_container.database_service
        self.logger = logging.getLogger(__name__)
        
        # Get operations directory from config or default
        project_root = Path(__file__).parent.parent.parent.parent
        self.operations_dir = project_root / "Operations"
    
    def resolve_lineage_chain(self, hydration_operation_id: int) -> Dict[str, Any]:
        """
        Resolve complete lineage chain from hydration operation.
        
        Returns dictionary with:
        - hydration_operation: Hydration Operation object
        - microstructure_operation: Parent Microstructure Operation object  
        - mix_design_data: Mix design parameters from stored UI parameters
        - aggregate_properties: Resolved fine/coarse aggregate properties
        - volume_fractions: Calculated volume fractions
        """
        with self.database_service.get_session() as session:
            # 1. Get hydration operation
            hydration_op = session.query(Operation).filter_by(id=hydration_operation_id).first()
            if not hydration_op:
                raise ValueError(f"Hydration operation {hydration_operation_id} not found")
            
            if hydration_op.operation_type != OperationType.HYDRATION.value:
                raise ValueError(f"Operation {hydration_operation_id} is not a hydration operation")
            
            # 2. Get source microstructure operation (with legacy support)
            microstructure_op = None
            microstructure_name = None
            
            # First try: Use parent_operation_id linkage (Phase 3+ operations)
            if hydration_op.parent_operation_id:
                microstructure_op = session.query(Operation).filter_by(
                    id=hydration_op.parent_operation_id
                ).first()
                
                if microstructure_op and microstructure_op.operation_type != OperationType.MICROSTRUCTURE.value:
                    raise ValueError(f"Parent operation is not a microstructure operation")
            
            # Second try: Use stored UI parameters for legacy operations
            if not microstructure_op and hydration_op.stored_ui_parameters:
                ui_params = hydration_op.stored_ui_parameters
                if 'source_microstructure' in ui_params:
                    source_info = ui_params['source_microstructure']
                    if isinstance(source_info, dict) and 'name' in source_info:
                        microstructure_name = source_info['name']
                        # Find microstructure operation by name (support both old and new operation types)
                        microstructure_op = session.query(Operation).filter(
                            Operation.name == microstructure_name,
                            Operation.operation_type.in_([OperationType.MICROSTRUCTURE.value, "microstructure_generation"])
                        ).first()
                        
                        self.logger.info(f"Found microstructure operation via UI parameters: {microstructure_name}")
            
            if not microstructure_op:
                error_msg = f"Parent microstructure operation not found for hydration {hydration_operation_id}"
                if microstructure_name:
                    error_msg += f" (looking for '{microstructure_name}')"
                raise ValueError(error_msg)
            
            # 3. Extract mix design data from linked SavedMixDesign record
            mix_design_data = self._get_mix_design_data_from_microstructure_operation(session, microstructure_op)
            
            # 4. Resolve aggregate properties from mix design
            aggregate_properties = self._resolve_aggregate_properties(session, mix_design_data)
            
            # 5. Calculate volume fractions from mix design components
            volume_fractions = self._calculate_volume_fractions(mix_design_data)
            
            lineage = {
                'hydration_operation': hydration_op,
                'microstructure_operation': microstructure_op,
                'mix_design_data': mix_design_data,
                'aggregate_properties': aggregate_properties,
                'volume_fractions': volume_fractions
            }
            
            self.logger.info(f"Resolved lineage chain for hydration operation {hydration_operation_id}")
            return lineage
    
    def _resolve_aggregate_properties(self, session: Session, mix_design_data: Dict[str, Any]) -> Dict[str, Optional[AggregateProperties]]:
        """Resolve aggregate properties from mix design data and database."""
        properties = {
            'fine_aggregate': None,
            'coarse_aggregate': None
        }
        
        # Extract aggregate names from mix design
        fine_agg_name = mix_design_data.get('fine_aggregate_name')
        coarse_agg_name = mix_design_data.get('coarse_aggregate_name')
        
        # Extract volume fractions from components or direct fields
        volume_fractions = self._calculate_volume_fractions(mix_design_data)
        
        # Resolve fine aggregate
        fine_vf = volume_fractions.get('fine_aggregate_volume_fraction', 0.0)
        fine_mass = mix_design_data.get('fine_aggregate_mass', 0.0)
        
        if fine_agg_name and (fine_vf > 0.0 or fine_mass > 0.0):
            fine_agg = session.query(Aggregate).filter(
                (Aggregate.display_name == fine_agg_name) | 
                (Aggregate.name == fine_agg_name)
            ).first()
            
            if fine_agg:
                properties['fine_aggregate'] = AggregateProperties(
                    name=fine_agg.display_name or fine_agg.name,
                    bulk_modulus=fine_agg.bulk_modulus or 30.0,  # Default GPa
                    shear_modulus=fine_agg.shear_modulus or 18.0,
                    volume_fraction=fine_vf,
                    grading_path=self._get_aggregate_grading_path(fine_agg)
                )
                self.logger.info(f"Resolved fine aggregate: {fine_agg.display_name} (VF: {fine_vf:.3f})")
            else:
                self.logger.warning(f"Fine aggregate '{fine_agg_name}' not found in database")
        
        # Resolve coarse aggregate
        coarse_vf = volume_fractions.get('coarse_aggregate_volume_fraction', 0.0)
        coarse_mass = mix_design_data.get('coarse_aggregate_mass', 0.0)
        
        if coarse_agg_name and (coarse_vf > 0.0 or coarse_mass > 0.0):
            coarse_agg = session.query(Aggregate).filter(
                (Aggregate.display_name == coarse_agg_name) | 
                (Aggregate.name == coarse_agg_name)
            ).first()
            
            if coarse_agg:
                properties['coarse_aggregate'] = AggregateProperties(
                    name=coarse_agg.display_name or coarse_agg.name,
                    bulk_modulus=coarse_agg.bulk_modulus or 36.7,  # Default GPa
                    shear_modulus=coarse_agg.shear_modulus or 22.0,
                    volume_fraction=coarse_vf,
                    grading_path=self._get_aggregate_grading_path(coarse_agg)
                )
                self.logger.info(f"Resolved coarse aggregate: {coarse_agg.display_name} (VF: {coarse_vf:.3f})")
            else:
                self.logger.warning(f"Coarse aggregate '{coarse_agg_name}' not found in database")
        
        return properties
    
    def _get_aggregate_grading_path(self, aggregate: Aggregate) -> str:
        """Get grading file path for aggregate by creating temporary .gdg file from database templates."""
        try:
            # Import grading model
            from app.models.grading import Grading, GradingType
            
            # Determine aggregate type for grading template selection
            agg_type_str = "fine" if aggregate.is_fine_aggregate else "coarse"
            grading_type = GradingType.FINE if aggregate.is_fine_aggregate else GradingType.COARSE
            
            self.logger.info(f"🔍 Looking for {agg_type_str} grading template for aggregate: {aggregate.display_name}")
            self.logger.info(f"🔍 Aggregate ID: {aggregate.id}, Type: {aggregate.type}")
            
            # Get database session properly
            with self.database_service.get_session() as session:
                # Try to find a grading template by aggregate ID first
                grading = session.query(Grading).filter(
                    Grading.aggregate_id == aggregate.id
                ).first()
                self.logger.info(f"🔍 Step 1 - By aggregate ID: {'Found' if grading else 'Not found'}")
                
                if not grading:
                    # Try to find a standard grading template by type
                    grading = session.query(Grading).filter(
                        Grading.type == grading_type,
                        Grading.is_standard == 1
                    ).first()
                    self.logger.info(f"🔍 Step 2 - Standard template: {'Found' if grading else 'Not found'}")
                    
                if not grading:
                    # Try to find ANY grading template of the correct type
                    grading = session.query(Grading).filter(
                        Grading.type == grading_type
                    ).first()
                    self.logger.info(f"🔍 Step 3 - Any template: {'Found' if grading else 'Not found'}")
                
                # Session will auto-close when we exit this block, so get the data we need
                if grading and grading.sieve_data:
                    grading_name = grading.name
                    grading_sieve_data = grading.sieve_data  # Copy the data before session closes
                    self.logger.info(f"🔍 Found grading: {grading_name} (sieve_data: Yes)")
                else:
                    grading_name = None
                    grading_sieve_data = None
            
            if not grading_name or not grading_sieve_data:
                self.logger.warning(f"No grading template found for {agg_type_str} aggregate: {aggregate.display_name}")
                return ""
            
            # Create grading file in operation directory where elastic.c can find it
            import os
            
            # Put grading file in the same directory as other elastic moduli inputs
            # This will be refined in Phase 3 to use the specific operation folder
            # For now, use a pattern that will work: ./Operations/{HydrationName}/
            grading_filename = f"{aggregate.display_name}_{agg_type_str}_grading.gdg"
            
            # For Phase 2, put it in a location that will be accessible to elastic.c
            # This should be in the same directory as other operation files
            temp_grading_path = f"./{grading_filename}"  # Relative to operation working directory
            
            # Create the actual file in the operations base directory for now
            # Phase 3 will move this to the specific operation folder
            actual_file_path = self.operations_dir / grading_filename
            
            # Convert sieve data to .gdg format manually (since we can't call grading.to_gdg_format())
            lines = []
            # Sort by sieve size (largest first for standard format)
            sorted_points = sorted(grading_sieve_data, key=lambda x: x[0], reverse=True)
            
            for point in sorted_points:
                size_mm = point[0]
                percent_passing = point[1]
                lines.append(f"{size_mm}\t{percent_passing}")
            
            gdg_content = '\n'.join(lines)
            
            # Write to file in operations directory
            with open(actual_file_path, 'w') as f:
                f.write(gdg_content)
            
            self.logger.info(f"Created grading file for {aggregate.display_name}: {actual_file_path}")
            self.logger.debug(f"Grading template used: {grading_name} with {len(grading_sieve_data)} sieve points")
            
            return temp_grading_path
            
        except Exception as e:
            self.logger.error(f"Failed to create grading file for aggregate {aggregate.display_name}: {e}")
            return ""
    
    def _calculate_volume_fractions(self, mix_design_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate volume fractions from mix design components."""
        volume_fractions = {
            'fine_aggregate_volume_fraction': 0.0,
            'coarse_aggregate_volume_fraction': 0.0,
            'air_volume_fraction': 0.0
        }
        
        # Try to get from direct fields first
        volume_fractions['air_volume_fraction'] = mix_design_data.get('air_volume_fraction', 0.0)
        
        # Extract from components JSON if available
        components = mix_design_data.get('components', [])
        if isinstance(components, list):
            for component in components:
                if not isinstance(component, dict):
                    continue
                    
                material_type = component.get('material_type', '').lower()
                material_name = component.get('material_name', '').lower()
                volume_fraction = component.get('volume_fraction', 0.0)
                
                # Check if it's an aggregate by material_type
                if material_type == 'aggregate':
                    # Determine if it's fine or coarse by name
                    if 'fine' in material_name:
                        volume_fractions['fine_aggregate_volume_fraction'] += volume_fraction
                    elif 'coarse' in material_name:
                        volume_fractions['coarse_aggregate_volume_fraction'] += volume_fraction
                    else:
                        # Default to fine if not specified
                        volume_fractions['fine_aggregate_volume_fraction'] += volume_fraction
                elif 'air' in material_type:
                    volume_fractions['air_volume_fraction'] += volume_fraction
        
        # Also try calculated properties
        calculated_props = mix_design_data.get('calculated_properties', {})
        if isinstance(calculated_props, dict):
            for key, value in calculated_props.items():
                if key in volume_fractions and isinstance(value, (int, float)):
                    volume_fractions[key] = max(volume_fractions[key], value)
        
        # Try direct aggregate mass fields (convert to approximate volume fractions)
        fine_mass = mix_design_data.get('fine_aggregate_mass', 0.0)
        coarse_mass = mix_design_data.get('coarse_aggregate_mass', 0.0)
        
        if fine_mass > 0 and volume_fractions['fine_aggregate_volume_fraction'] == 0.0:
            # Rough approximation using typical aggregate density
            volume_fractions['fine_aggregate_volume_fraction'] = fine_mass / 2650.0  # kg/m³
        
        if coarse_mass > 0 and volume_fractions['coarse_aggregate_volume_fraction'] == 0.0:
            volume_fractions['coarse_aggregate_volume_fraction'] = coarse_mass / 2650.0
        
        return volume_fractions
    
    def discover_hydrated_microstructures(self, hydration_operation: Operation) -> List[HydratedMicrostructure]:
        """
        Discover all available hydrated microstructures from hydration operation directory.
        
        Returns list sorted with final microstructure first.
        """
        hydration_dir = self.operations_dir / hydration_operation.name
        
        if not hydration_dir.exists():
            self.logger.warning(f"Hydration directory not found: {hydration_dir}")
            return []
        
        # Resolve lineage to find the original microstructure operation
        try:
            lineage = self.resolve_lineage_chain(hydration_operation.id)
            microstructure_operation = lineage.get('microstructure_operation')
            if not microstructure_operation:
                self.logger.warning(f"No microstructure operation found in lineage for {hydration_operation.name}")
                return []
            
            # Find the original .pimg file in the microstructure operation's directory
            original_microstructure_dir = self.operations_dir / microstructure_operation.name
            original_pimg_path = original_microstructure_dir / f"{microstructure_operation.name}.pimg"
            
            if not original_pimg_path.exists():
                self.logger.warning(f"Original .pimg file not found: {original_pimg_path}")
                return []
            
            self.logger.info(f"Using original .pimg file: {original_pimg_path}")
            
        except Exception as e:
            self.logger.error(f"Error resolving lineage for {hydration_operation.name}: {e}")
            return []
        
        # Find all hydrated .img files in the directory
        # Pattern 1: Standard hydration output (e.g., HydrationOf_[NAME].img.25.100)  
        # Pattern 2: Time-step outputs (e.g., [NAME].img.332.05h.25.100)
        all_files = list(hydration_dir.glob("*"))
        
        img_files = []
        for file_path in all_files:
            filename = file_path.name
            # Include hydrated microstructures but exclude original microstructure
            # Pattern: filename.img.123.45h.XX.100 (where XX can be 23, 25, etc.)
            if (filename.count('.') >= 3 and 
                'h.' in filename and 
                filename.endswith('.100') and
                '.img.' in filename):
                img_files.append(file_path)
            # Also include HydrationOf_* files
            elif filename.startswith('HydrationOf_') and '.img.' in filename:
                img_files.append(file_path)
        
        microstructures = []
        # Final microstructure patterns (be flexible about system size)
        final_patterns = []
        
        # Add patterns based on found files that start with "HydrationOf_"
        hydrationof_files = [f for f in img_files if f.name.startswith("HydrationOf_")]
        if hydrationof_files:
            # The "HydrationOf_" files are typically the final outputs
            for hof_file in hydrationof_files:
                final_patterns.append(hof_file.name)
        
        # If no HydrationOf_ files, use fallback patterns
        if not final_patterns:
            # Look for patterns like HydrationOf_{operation}.img.{size}.100
            final_patterns = [
                f"HydrationOf_{hydration_operation.name}.img.25.100",
                f"HydrationOf_{hydration_operation.name}.img.23.100",
                f"HydrationOf_{hydration_operation.name}.img.50.100"
            ]
        
        for img_file in img_files:
            filename = img_file.name
            
            # Determine if this is the final microstructure
            is_final = any(filename == pattern for pattern in final_patterns)
            # Also check if this looks like the final time step (highest time value)
            if not is_final and 'h.25.100' in filename:
                # This is a time-step file, we'll determine the final one after processing all files
                pass
            
            # Extract time label from filename
            time_label = self._extract_time_label(filename, hydration_operation.name, is_final)
            
            # Use the original .pimg file found through lineage resolution
            microstructure = HydratedMicrostructure(
                file_path=str(img_file),
                time_label=time_label,
                is_final=is_final
            )
            # Use the original .pimg file for all hydrated microstructures
            microstructure.pimg_path = str(original_pimg_path)
            microstructures.append(microstructure)
        
        # Sort with final first, then by time
        microstructures.sort(key=lambda x: (not x.is_final, x.time_label))
        
        self.logger.info(f"Found {len(microstructures)} hydrated microstructures for {hydration_operation.name}")
        return microstructures
    
    def _extract_time_label(self, filename: str, operation_name: str, is_final: bool) -> str:
        """Extract time label from microstructure filename."""
        if is_final:
            return "Final"
        
        # Remove operation name prefix to get time suffix
        if filename.startswith(operation_name):
            suffix = filename[len(operation_name):]
            # Remove .img extension
            suffix = suffix.replace('.img', '')
            
            # Parse common patterns
            if suffix.startswith('_'):
                suffix = suffix[1:]  # Remove leading underscore
                
                # Pattern: "028days" -> "28 days"
                days_match = re.match(r'(\d+)days?', suffix)
                if days_match:
                    days = int(days_match.group(1))
                    return f"{days} days"
                
                # Pattern: "001hours" -> "1 hours"  
                hours_match = re.match(r'(\d+)hours?', suffix)
                if hours_match:
                    hours = int(hours_match.group(1))
                    return f"{hours} hours"
                
                # Pattern: "1year" -> "1 year"
                year_match = re.match(r'(\d+)years?', suffix)
                if year_match:
                    years = int(year_match.group(1))
                    return f"{years} year{'s' if years != 1 else ''}"
                
                # Return cleaned suffix if no pattern matches
                return suffix.replace('_', ' ').title()
        
        # Fallback to filename without extension
        return filename.replace('.img', '')
    
    def convert_to_relative_path(self, absolute_path: str, elastic_operation_dir: str) -> str:
        """
        Convert absolute file path to relative path from elastic operation directory.
        
        Args:
            absolute_path: Absolute path to file
            elastic_operation_dir: Absolute path to elastic operation directory
            
        Returns:
            Relative path from elastic operation directory
        """
        try:
            abs_path = Path(absolute_path).resolve()
            op_dir = Path(elastic_operation_dir).resolve()
            
            relative_path = os.path.relpath(abs_path, op_dir)
            
            self.logger.debug(f"Converted path: {absolute_path} -> {relative_path}")
            return relative_path
            
        except Exception as e:
            self.logger.error(f"Error converting path to relative: {e}")
            return absolute_path
    
    def get_itz_detection(self, aggregate_properties: Dict[str, Optional[AggregateProperties]]) -> bool:
        """
        Determine if ITZ calculations should be performed based on aggregate presence.
        
        Args:
            aggregate_properties: Dictionary with fine_aggregate and coarse_aggregate
            
        Returns:
            True if ITZ calculations should be performed
        """
        has_aggregates = (
            aggregate_properties.get('fine_aggregate') is not None or 
            aggregate_properties.get('coarse_aggregate') is not None
        )
        
        self.logger.info(f"ITZ detection: {has_aggregates}")
        return has_aggregates
    
    def validate_lineage_completeness(self, lineage: Dict[str, Any]) -> List[str]:
        """
        Validate that lineage contains all necessary data for elastic calculation.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        if not lineage.get('hydration_operation'):
            errors.append("Hydration operation not found")
        
        if not lineage.get('microstructure_operation'):
            errors.append("Parent microstructure operation not found")
        
        mix_design_data = lineage.get('mix_design_data', {})
        if not mix_design_data:
            errors.append("Mix design data not found in microstructure operation")
        
        aggregate_props = lineage.get('aggregate_properties', {})
        volume_fractions = lineage.get('volume_fractions', {})
        
        # Check if we have meaningful volume fractions
        total_volume = (
            volume_fractions.get('fine_aggregate_volume_fraction', 0.0) +
            volume_fractions.get('coarse_aggregate_volume_fraction', 0.0) +
            volume_fractions.get('air_volume_fraction', 0.0)
        )
        
        if total_volume > 1.0:
            errors.append(f"Total volume fractions exceed 1.0: {total_volume:.3f}")
        
        return errors
    
    def _get_mix_design_data_from_microstructure_operation(self, session, microstructure_op) -> Dict[str, Any]:
        """
        Get mix design data from linked SavedMixDesign record.
        
        Args:
            session: Database session
            microstructure_op: Microstructure Operation object
            
        Returns:
            Dictionary with mix design data in expected format
        """
        try:
            # Import required models
            from app.models.microstructure_operation import MicrostructureOperation
            from app.services.mix_design_service import MixDesignService
            
            # Find MicrostructureOperation record
            micro_op = session.query(MicrostructureOperation).filter_by(operation_id=microstructure_op.id).first()
            
            if not micro_op or not micro_op.mix_design_id:
                self.logger.warning(f"No MicrostructureOperation or mix_design_id for operation {microstructure_op.name}")
                return {}
            
            # Get SavedMixDesign via MixDesignService
            mix_design_service = MixDesignService(self.database_service)
            mix_design = mix_design_service.get_by_id(micro_op.mix_design_id)
            
            if not mix_design:
                self.logger.warning(f"SavedMixDesign not found for ID {micro_op.mix_design_id}")
                return {}
            
            # Convert SavedMixDesign to expected format
            mix_design_data = {
                'name': mix_design.name,
                'water_binder_ratio': mix_design.water_binder_ratio,
                'total_water_content': mix_design.total_water_content,
                'air_content': mix_design.air_content,
                'air_volume_fraction': mix_design.air_volume_fraction,
                'water_volume_fraction': mix_design.water_volume_fraction,
                'system_size_x': mix_design.system_size_x,
                'system_size_y': mix_design.system_size_y,
                'system_size_z': mix_design.system_size_z,
                
                # Convert components to expected format (list for volume fraction calculation)
                'components': [],
                
                # Aggregate data
                'fine_aggregate_name': mix_design.fine_aggregate_name,
                'fine_aggregate_mass': mix_design.fine_aggregate_mass,
                'coarse_aggregate_name': mix_design.coarse_aggregate_name,
                'coarse_aggregate_mass': mix_design.coarse_aggregate_mass,
            }
            
            # Convert components to list format for volume fraction calculation
            if hasattr(mix_design, 'components') and mix_design.components:
                for component in mix_design.components:
                    if isinstance(component, dict):
                        # Component is already a dict
                        mix_design_data['components'].append(component)
                    else:
                        # Component is a Pydantic model object
                        mix_design_data['components'].append({
                            'material_name': getattr(component, 'material_name', ''),
                            'material_type': getattr(component, 'material_type', ''),
                            'mass_fraction': getattr(component, 'mass_fraction', 0.0),
                            'volume_fraction': getattr(component, 'volume_fraction', 0.0),
                            'specific_gravity': getattr(component, 'specific_gravity', 1.0),
                        })
            
            self.logger.info(f"Successfully loaded mix design data for {mix_design.name}: {len(mix_design_data['components'])} components")
            return mix_design_data
            
        except Exception as e:
            self.logger.error(f"Error loading mix design data from microstructure operation: {e}")
            return {}
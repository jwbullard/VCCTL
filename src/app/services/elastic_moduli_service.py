#!/usr/bin/env python3
"""
Elastic Moduli Service

Handles elastic moduli operation management including:
- Input file generation for C elastic moduli calculation programs
- Parameter validation and processing
- Operation lifecycle management
- Integration with hydration operations

Based on legacy Java implementation from ConcreteMeasurementsForm.java
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.elastic_moduli_operation import ElasticModuliOperation
from app.models.operation import Operation, OperationStatus, OperationType
from app.models.mix_design import MixDesign
from app.models.aggregate import Aggregate
from app.services.service_container import ServiceContainer
from app.services.microstructure_hydration_bridge import MicrostructureHydrationBridge, MicrostructureMetadata


class ElasticModuliService:
    """Service for managing elastic moduli operations."""
    
    def __init__(self, service_container: ServiceContainer):
        self.service_container = service_container
        self.database_service = service_container.database_service
        self.bridge = MicrostructureHydrationBridge()
        self.logger = logging.getLogger(__name__)
        
    def create_operation(
        self,
        name: str,
        hydration_operation_id: int,
        description: str = "",
        **kwargs
    ) -> ElasticModuliOperation:
        """Create a new elastic moduli operation."""
        with self.database_service.get_session() as session:
            # Validate that hydration operation exists and is completed
            hydration_op = session.query(Operation).filter_by(id=hydration_operation_id).first()
            if not hydration_op:
                raise ValueError(f"Hydration operation {hydration_operation_id} not found")
            
            if hydration_op.status != OperationStatus.COMPLETED.value:
                raise ValueError(f"Hydration operation {hydration_operation_id} is not completed")
            
            if hydration_op.operation_type != OperationType.HYDRATION.value:
                raise ValueError(f"Operation {hydration_operation_id} is not a hydration operation")
            
            # Create the elastic moduli operation
            operation = ElasticModuliOperation(
                name=name,
                description=description,
                hydration_operation_id=hydration_operation_id,
                **kwargs
            )
            
            session.add(operation)
            session.commit()
            session.refresh(operation)
            
            self.logger.info(f"Created elastic moduli operation: {name}")
            return operation
    
    def generate_elastic_input_file(
        self,
        operation: ElasticModuliOperation,
        output_directory: str
    ) -> str:
        """
        Generate elastic.in input file for C elastic moduli calculation program.
        
        Based on generateElasticInputForUser() from ConcreteMeasurementsForm.java
        
        Args:
            operation: The elastic moduli operation
            output_directory: Directory to create the input file in
            
        Returns:
            Path to the generated elastic.in file
        """
        output_path = Path(output_directory)
        output_path.mkdir(parents=True, exist_ok=True)
        
        elastic_input_file = output_path / "elastic.in"
        
        # Get hydration operation details
        with self.database_service.get_session() as session:
            hydration_operation = session.query(Operation).filter_by(
                id=operation.hydration_operation_id
            ).first()
            
            if not hydration_operation:
                raise ValueError(f"Hydration operation {operation.hydration_operation_id} not found")
        
        # Generate input file content
        input_content = self._generate_elastic_input_content(operation, hydration_operation)
        
        # Write the file
        with open(elastic_input_file, 'w') as f:
            f.write(input_content)
        
        self.logger.info(f"Generated elastic input file: {elastic_input_file}")
        return str(elastic_input_file)
    
    def _generate_elastic_input_content(
        self,
        operation: ElasticModuliOperation,
        hydration_operation: Operation
    ) -> str:
        """Generate the content for the elastic.in input file."""
        
        lines = []
        
        # Image filename (from hydration operation)
        if operation.image_filename:
            lines.append(operation.image_filename)
        else:
            # Default to hydration operation name + .img
            lines.append(f"{hydration_operation.name}.img")
        
        # Early age connection (always 1 according to Java code)
        lines.append(str(operation.early_age_connection or 1))
        
        # ITZ flag (1 if has_itz is True, 0 otherwise)
        lines.append("1" if operation.has_itz else "0")
        
        # Output directory
        lines.append(operation.output_directory or ".")
        
        # Pimg file path (if available)
        if operation.pimg_file_path:
            lines.append(operation.pimg_file_path)
        else:
            lines.append("")
        
        # Fine aggregate properties
        if operation.has_fine_aggregate:
            lines.append("1")  # Has fine aggregate flag
            lines.append(str(operation.fine_aggregate_volume_fraction or 0.0))
            lines.append(operation.fine_aggregate_grading_path or "")
            lines.append(str(operation.fine_aggregate_bulk_modulus or 0.0))
            lines.append(str(operation.fine_aggregate_shear_modulus or 0.0))
        else:
            lines.append("0")  # No fine aggregate
            lines.append("0.0")
            lines.append("")
            lines.append("0.0")
            lines.append("0.0")
        
        # Coarse aggregate properties
        if operation.has_coarse_aggregate:
            lines.append("1")  # Has coarse aggregate flag
            lines.append(str(operation.coarse_aggregate_volume_fraction or 0.0))
            lines.append(operation.coarse_aggregate_grading_path or "")
            lines.append(str(operation.coarse_aggregate_bulk_modulus or 0.0))
            lines.append(str(operation.coarse_aggregate_shear_modulus or 0.0))
        else:
            lines.append("0")  # No coarse aggregate
            lines.append("0.0")
            lines.append("")
            lines.append("0.0")
            lines.append("0.0")
        
        # Air volume fraction
        lines.append(str(operation.air_volume_fraction or 0.0))
        
        return "\n".join(lines) + "\n"
    
    def get_all_operations(self) -> List[ElasticModuliOperation]:
        """Get all elastic moduli operations."""
        with self.database_service.get_session() as session:
            return session.query(ElasticModuliOperation).all()
    
    def get_operation_by_id(self, operation_id: int) -> Optional[ElasticModuliOperation]:
        """Get an elastic moduli operation by ID."""
        with self.database_service.get_session() as session:
            return session.query(ElasticModuliOperation).filter_by(id=operation_id).first()
    
    def get_operation_by_name(self, name: str) -> Optional[ElasticModuliOperation]:
        """Get an elastic moduli operation by name."""
        with self.database_service.get_session() as session:
            return session.query(ElasticModuliOperation).filter_by(name=name).first()
    
    def get_operations_for_hydration(self, hydration_operation_id: int) -> List[ElasticModuliOperation]:
        """Get all elastic moduli operations for a specific hydration operation."""
        with self.database_service.get_session() as session:
            return session.query(ElasticModuliOperation).filter_by(
                hydration_operation_id=hydration_operation_id
            ).all()
    
    def update_operation(
        self,
        operation_id: int,
        **kwargs
    ) -> Optional[ElasticModuliOperation]:
        """Update an elastic moduli operation."""
        with self.database_service.get_session() as session:
            operation = session.query(ElasticModuliOperation).filter_by(id=operation_id).first()
            if not operation:
                return None
            
            # Update fields
            for key, value in kwargs.items():
                if hasattr(operation, key):
                    setattr(operation, key, value)
            
            operation.updated_at = datetime.utcnow()
            session.commit()
            session.refresh(operation)
            
            self.logger.info(f"Updated elastic moduli operation {operation_id}")
            return operation
    
    def delete_operation(self, operation_id: int) -> bool:
        """Delete an elastic moduli operation."""
        with self.database_service.get_session() as session:
            operation = session.query(ElasticModuliOperation).filter_by(id=operation_id).first()
            if not operation:
                return False
            
            session.delete(operation)
            session.commit()
            
            self.logger.info(f"Deleted elastic moduli operation {operation_id}")
            return True
    
    def get_available_hydration_operations(self) -> List[Operation]:
        """Get all completed hydration operations available for elastic moduli calculations."""
        with self.database_service.get_session() as session:
            return session.query(Operation).filter(
                Operation.operation_type == OperationType.HYDRATION.value,
                Operation.status == OperationStatus.COMPLETED.value
            ).all()
    
    def populate_operation_from_hydration(
        self,
        operation: ElasticModuliOperation,
        hydration_operation: Operation
    ) -> ElasticModuliOperation:
        """
        Populate elastic moduli operation parameters from the associated hydration operation.
        
        This method extracts relevant information from the hydration operation's mix design
        to auto-populate aggregate properties and other parameters.
        """
        with self.database_service.get_session() as session:
            # Try to find the mix design associated with the hydration operation
            # This would require additional relationships or metadata storage
            # For now, we'll set basic defaults
            
            if not operation.image_filename:
                operation.image_filename = f"{hydration_operation.name}.img"
            
            if not operation.output_directory:
                # Default to Operations directory structure
                project_root = Path(__file__).parent.parent.parent.parent
                operations_dir = project_root / "Operations" / f"Elastic_{hydration_operation.name}"
                operation.output_directory = str(operations_dir)
            
            if not operation.pimg_file_path:
                # Look for .pimg file in hydration operation directory
                hydration_dir = Path(__file__).parent.parent.parent.parent / "Operations" / hydration_operation.name
                pimg_files = list(hydration_dir.glob("*.pimg"))
                if pimg_files:
                    operation.pimg_file_path = str(pimg_files[0])
            
            self.logger.info(f"Populated operation parameters from hydration operation {hydration_operation.name}")
            return operation
    
    def populate_operation_from_microstructure(
        self,
        operation: ElasticModuliOperation,
        hydration_operation: Operation
    ) -> ElasticModuliOperation:
        """
        Populate elastic moduli operation parameters from microstructure metadata.
        
        This extracts aggregate properties, air content, and mechanical properties
        that were defined during microstructure creation, eliminating the need for
        the user to re-enter this information.
        """
        try:
            # Load microstructure metadata
            metadata = self.bridge.load_microstructure_metadata(hydration_operation.name)
            
            if not metadata:
                self.logger.warning(f"No microstructure metadata found for {hydration_operation.name}")
                return operation
            
            # Extract aggregate information from materials
            fine_aggregates = []
            coarse_aggregates = []
            air_volume_fraction = 0.0
            
            for material in metadata.materials:
                material_type = material.material_type.lower()
                
                if material_type in ['aggregate', 'fine_aggregate']:
                    # Determine if fine or coarse based on size or name
                    if self._is_fine_aggregate(material):
                        fine_aggregates.append(material)
                    else:
                        coarse_aggregates.append(material)
                elif material_type == 'air':
                    air_volume_fraction += material.volume_fraction
            
            # Set air content
            operation.air_volume_fraction = air_volume_fraction
            
            # Set fine aggregate properties (take first one per user requirement: max 1)
            if fine_aggregates:
                fine_agg = fine_aggregates[0]  # Take first fine aggregate
                operation.has_fine_aggregate = True
                operation.fine_aggregate_volume_fraction = fine_agg.volume_fraction
                operation.fine_aggregate_display_name = fine_agg.material_name
                
                # Get aggregate mechanical properties from database
                fine_props = self._get_aggregate_mechanical_properties(fine_agg.material_name)
                if fine_props:
                    operation.fine_aggregate_bulk_modulus = fine_props.get('bulk_modulus', 37.0)
                    operation.fine_aggregate_shear_modulus = fine_props.get('shear_modulus', 44.0)
                    operation.fine_aggregate_grading_path = fine_props.get('grading_path', '')
                else:
                    # Default values for quartz aggregate
                    operation.fine_aggregate_bulk_modulus = 37.0
                    operation.fine_aggregate_shear_modulus = 44.0
                
                self.logger.info(f"Set fine aggregate: {fine_agg.material_name} (VF: {fine_agg.volume_fraction:.3f})")
            
            # Set coarse aggregate properties (take first one per user requirement: max 1)
            if coarse_aggregates:
                coarse_agg = coarse_aggregates[0]  # Take first coarse aggregate  
                operation.has_coarse_aggregate = True
                operation.coarse_aggregate_volume_fraction = coarse_agg.volume_fraction
                operation.coarse_aggregate_display_name = coarse_agg.material_name
                
                # Get aggregate mechanical properties from database
                coarse_props = self._get_aggregate_mechanical_properties(coarse_agg.material_name)
                if coarse_props:
                    operation.coarse_aggregate_bulk_modulus = coarse_props.get('bulk_modulus', 37.0)
                    operation.coarse_aggregate_shear_modulus = coarse_props.get('shear_modulus', 44.0)
                    operation.coarse_aggregate_grading_path = coarse_props.get('grading_path', '')
                else:
                    # Default values for quartz aggregate
                    operation.coarse_aggregate_bulk_modulus = 37.0
                    operation.coarse_aggregate_shear_modulus = 44.0
                
                self.logger.info(f"Set coarse aggregate: {coarse_agg.material_name} (VF: {coarse_agg.volume_fraction:.3f})")
            
            # Set ITZ flag based on presence of aggregates
            operation.has_itz = (len(fine_aggregates) + len(coarse_aggregates)) > 0
            
            self.logger.info(f"Populated aggregate properties from microstructure metadata: "
                           f"Fine: {len(fine_aggregates)}, Coarse: {len(coarse_aggregates)}, "
                           f"Air: {air_volume_fraction:.3f}, ITZ: {operation.has_itz}")
            
        except Exception as e:
            self.logger.error(f"Error populating from microstructure metadata: {e}")
            # Continue without microstructure data - user can fill manually
        
        return operation
    
    def _is_fine_aggregate(self, material) -> bool:
        """Determine if aggregate material is fine or coarse based on name or properties."""
        material_name = material.material_name.lower()
        
        # Check name patterns
        fine_patterns = ['fine', 'sand', 'fa_']
        coarse_patterns = ['coarse', 'gravel', 'rock', 'ca_']
        
        for pattern in fine_patterns:
            if pattern in material_name:
                return True
                
        for pattern in coarse_patterns:
            if pattern in material_name:
                return False
        
        # If no clear pattern, consider fine if smaller size
        # This could be enhanced by looking at PSD parameters
        psd_params = material.psd_parameters
        if 'mean_diameter' in psd_params:
            mean_diameter = psd_params['mean_diameter']
            return mean_diameter < 4.75  # Standard sieve #4 (4.75mm) separation
        
        # Default to fine if uncertain
        return True
    
    def _get_aggregate_mechanical_properties(self, aggregate_name: str) -> Optional[Dict[str, Any]]:
        """Get mechanical properties for an aggregate from the database."""
        try:
            with self.database_service.get_session() as session:
                # Query the aggregate table for mechanical properties
                from app.models.aggregate import Aggregate
                aggregate = session.query(Aggregate).filter(
                    Aggregate.name == aggregate_name
                ).first()
                
                if aggregate:
                    # Extract mechanical properties if available
                    # Note: These field names might need adjustment based on actual Aggregate model
                    properties = {}
                    
                    # Check for mechanical properties in the aggregate model
                    if hasattr(aggregate, 'bulk_modulus') and aggregate.bulk_modulus:
                        properties['bulk_modulus'] = aggregate.bulk_modulus
                    if hasattr(aggregate, 'shear_modulus') and aggregate.shear_modulus:
                        properties['shear_modulus'] = aggregate.shear_modulus
                    if hasattr(aggregate, 'grading_file') and aggregate.grading_file:
                        properties['grading_path'] = aggregate.grading_file
                    
                    return properties if properties else None
                    
        except Exception as e:
            self.logger.warning(f"Could not retrieve aggregate properties for {aggregate_name}: {e}")
            
        return None
    
    def validate_operation_parameters(self, operation: ElasticModuliOperation) -> List[str]:
        """
        Validate elastic moduli operation parameters.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        if not operation.name or not operation.name.strip():
            errors.append("Operation name is required")
        
        if not operation.hydration_operation_id:
            errors.append("Hydration operation ID is required")
        
        if not operation.image_filename:
            errors.append("Image filename is required")
        
        # Validate aggregate properties if aggregates are present
        if operation.has_fine_aggregate:
            if operation.fine_aggregate_volume_fraction is None or operation.fine_aggregate_volume_fraction <= 0:
                errors.append("Fine aggregate volume fraction must be greater than 0")
            
            if operation.fine_aggregate_bulk_modulus is None or operation.fine_aggregate_bulk_modulus <= 0:
                errors.append("Fine aggregate bulk modulus must be greater than 0")
            
            if operation.fine_aggregate_shear_modulus is None or operation.fine_aggregate_shear_modulus <= 0:
                errors.append("Fine aggregate shear modulus must be greater than 0")
        
        if operation.has_coarse_aggregate:
            if operation.coarse_aggregate_volume_fraction is None or operation.coarse_aggregate_volume_fraction <= 0:
                errors.append("Coarse aggregate volume fraction must be greater than 0")
            
            if operation.coarse_aggregate_bulk_modulus is None or operation.coarse_aggregate_bulk_modulus <= 0:
                errors.append("Coarse aggregate bulk modulus must be greater than 0")
            
            if operation.coarse_aggregate_shear_modulus is None or operation.coarse_aggregate_shear_modulus <= 0:
                errors.append("Coarse aggregate shear modulus must be greater than 0")
        
        # Validate volume fractions sum
        total_aggregate_volume = 0.0
        if operation.has_fine_aggregate and operation.fine_aggregate_volume_fraction:
            total_aggregate_volume += operation.fine_aggregate_volume_fraction
        if operation.has_coarse_aggregate and operation.coarse_aggregate_volume_fraction:
            total_aggregate_volume += operation.coarse_aggregate_volume_fraction
        if operation.air_volume_fraction:
            total_aggregate_volume += operation.air_volume_fraction
        
        if total_aggregate_volume > 1.0:
            errors.append(f"Total volume fractions exceed 1.0: {total_aggregate_volume:.3f}")
        
        return errors
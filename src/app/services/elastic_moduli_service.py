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
from app.services.elastic_lineage_service import ElasticLineageService, HydratedMicrostructure
from app.services.elastic_input_generator import ElasticInputGenerator


class ElasticModuliService:
    """Service for managing elastic moduli operations."""
    
    def __init__(self, service_container: ServiceContainer):
        self.service_container = service_container
        self.database_service = service_container.database_service
        self.bridge = MicrostructureHydrationBridge()
        self.logger = logging.getLogger(__name__)
        
        # Initialize new services for Phase 1 implementation
        self.lineage_service = ElasticLineageService(service_container)
        self.input_generator = ElasticInputGenerator(self.lineage_service)
        
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
        selected_microstructure: HydratedMicrostructure,
        output_directory: str
    ) -> str:
        """
        Generate elastic.c input file using new Phase 1 lineage-aware system.
        
        Args:
            operation: The elastic moduli operation
            selected_microstructure: Selected hydrated microstructure with time info
            output_directory: Directory to create the input file in
            
        Returns:
            Path to the generated elastic_input.txt file
        """
        return self.input_generator.generate_input_file(
            operation, selected_microstructure, output_directory
        )
    
    def create_operation_with_lineage(
        self,
        name: str,
        hydration_operation_id: int,
        description: str = "",
        image_filename: Optional[str] = None,
        pimg_file_path: Optional[str] = None
    ) -> Tuple[ElasticModuliOperation, Dict[str, Any]]:
        """
        Create elastic moduli operation with complete lineage resolution.
        
        Returns both the operation and resolved lineage data for UI display.
        
        Args:
            name: Operation name
            hydration_operation_id: Source hydration operation ID
            description: Optional description
            
        Returns:
            Tuple of (operation, lineage_data)
        """
        # Resolve lineage chain first to validate completeness
        lineage = self.lineage_service.resolve_lineage_chain(hydration_operation_id)
        
        # Validate lineage completeness
        validation_errors = self.lineage_service.validate_lineage_completeness(lineage)
        if validation_errors:
            raise ValueError(f"Lineage validation failed: {'; '.join(validation_errors)}")
        
        # Create the operation with database integration
        with self.database_service.get_session() as session:
            # Check if an Operation with this name already exists and clean it up
            existing_op = session.query(Operation).filter_by(
                name=name,
                operation_type=OperationType.ELASTIC_MODULI.value
            ).first()
            if existing_op:
                # Delete the existing operation record
                session.delete(existing_op)
                session.commit()
                self.logger.info(f"Deleted existing Operation with name '{name}' to allow reuse")

            # Create base Operation record for tracking
            base_operation = Operation(
                name=name,
                operation_type=OperationType.ELASTIC_MODULI.value,
                status=OperationStatus.QUEUED.value,
                parent_operation_id=hydration_operation_id,
                stored_ui_parameters={
                    'operation_name': name,
                    'description': description,
                    'hydration_operation_id': hydration_operation_id,
                    'lineage_resolved': True
                }
            )
            
            session.add(base_operation)
            session.commit()
            session.refresh(base_operation)
            
            # Create ElasticModuliOperation with pre-populated lineage data
            # Set default output directory nested inside hydration operation folder
            operations_dir = self.service_container.directories_service.get_operations_path()

            # Get hydration operation name for proper nesting
            hydration_op = session.query(Operation).filter_by(id=hydration_operation_id).first()
            if hydration_op and hydration_op.name:
                # Nest elastic operation inside hydration folder
                default_output_dir = str(operations_dir / hydration_op.name / name)
            else:
                # Fallback to flat structure
                default_output_dir = str(operations_dir / name)

            # Check if an ElasticModuliOperation with this name already exists
            existing_elastic = session.query(ElasticModuliOperation).filter_by(name=name).first()
            if existing_elastic:
                # Delete the existing record to allow reuse of the name
                session.delete(existing_elastic)
                session.commit()
                self.logger.info(f"Deleted existing ElasticModuliOperation with name '{name}' to allow reuse")

            elastic_operation = ElasticModuliOperation(
                name=name,
                description=description,
                hydration_operation_id=hydration_operation_id,
                image_filename=image_filename or "microstructure.img",  # Provide default if not specified
                pimg_file_path=pimg_file_path,
                output_directory=default_output_dir,  # Set required output directory
                early_age_connection=1,  # Default value for required field
                has_itz=True  # Default value - can be overridden later
            )
            
            # Populate from lineage data
            self._populate_from_lineage(elastic_operation, lineage)
            
            session.add(elastic_operation)
            session.commit()
            session.refresh(elastic_operation)
            
            self.logger.info(f"Created elastic moduli operation with lineage: {name}")
            return elastic_operation, lineage
    
    def discover_hydrated_microstructures(self, hydration_operation_id: int) -> List[HydratedMicrostructure]:
        """
        Discover available hydrated microstructures for selection.
        
        Args:
            hydration_operation_id: ID of the hydration operation
            
        Returns:
            List of available hydrated microstructures sorted with final first
        """
        with self.database_service.get_session() as session:
            hydration_op = session.query(Operation).filter_by(id=hydration_operation_id).first()
            if not hydration_op:
                raise ValueError(f"Hydration operation {hydration_operation_id} not found")
            
            return self.lineage_service.discover_hydrated_microstructures(hydration_op)
    
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
        return self.input_generator.validate_input_completeness(operation, selected_microstructure)
    
    def _populate_from_lineage(self, operation: ElasticModuliOperation, lineage: Dict[str, Any]):
        """
        Populate operation parameters from resolved lineage data.
        
        Args:
            operation: ElasticModuliOperation to populate
            lineage: Resolved lineage data from ElasticLineageService
        """
        aggregate_props = lineage.get('aggregate_properties', {})
        volume_fractions = lineage.get('volume_fractions', {})
        
        # Set aggregate properties
        fine_agg = aggregate_props.get('fine_aggregate')
        if fine_agg:
            operation.has_fine_aggregate = True
            operation.fine_aggregate_volume_fraction = fine_agg.volume_fraction
            operation.fine_aggregate_bulk_modulus = fine_agg.bulk_modulus
            operation.fine_aggregate_shear_modulus = fine_agg.shear_modulus
            operation.fine_aggregate_display_name = fine_agg.name
            operation.fine_aggregate_grading_path = fine_agg.grading_path
        
        coarse_agg = aggregate_props.get('coarse_aggregate')
        if coarse_agg:
            operation.has_coarse_aggregate = True
            operation.coarse_aggregate_volume_fraction = coarse_agg.volume_fraction
            operation.coarse_aggregate_bulk_modulus = coarse_agg.bulk_modulus
            operation.coarse_aggregate_shear_modulus = coarse_agg.shear_modulus
            operation.coarse_aggregate_display_name = coarse_agg.name
            operation.coarse_aggregate_grading_path = coarse_agg.grading_path
        
        # Set volume fractions
        operation.air_volume_fraction = volume_fractions.get('air_volume_fraction', 0.0)
        
        # Set ITZ calculation flag
        operation.has_itz = self.lineage_service.get_itz_detection(aggregate_props)
        
        self.logger.info(f"Populated operation from lineage - ITZ: {operation.has_itz}, "
                        f"Fine Agg: {operation.has_fine_aggregate}, Coarse Agg: {operation.has_coarse_aggregate}")
    
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
            # Debug: Log what we're looking for
            self.logger.info(f"DEBUG: Looking for operations with type='{OperationType.HYDRATION.value}' and status='{OperationStatus.COMPLETED.value}'")

            # Debug: Check what's actually in the database
            all_ops = session.query(Operation).all()
            self.logger.info(f"DEBUG: Found {len(all_ops)} total operations:")
            for op in all_ops:
                self.logger.info(f"  ID {op.id}: {op.name} - type='{op.operation_type}', status='{op.status}'")

            # Get the filtered results
            results = session.query(Operation).filter(
                Operation.operation_type == OperationType.HYDRATION.value,
                Operation.status == OperationStatus.COMPLETED.value
            ).all()

            self.logger.info(f"DEBUG: Found {len(results)} matching hydration operations")
            return results
    
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
                # Default to Operations directory structure - nest inside hydration operation folder
                operations_base = self.service_container.directories_service.get_operations_path()
                if operation.name:
                    # Nest elastic operation inside hydration folder
                    operations_dir = operations_base / hydration_operation.name / operation.name
                else:
                    # If no name yet, use placeholder (actual directory will be created by panel)
                    operations_dir = operations_base / hydration_operation.name / "elastic_pending"
                operation.output_directory = str(operations_dir)

            if not operation.pimg_file_path:
                # Look for .pimg file in hydration operation directory
                operations_base = self.service_container.directories_service.get_operations_path()
                hydration_dir = operations_base / hydration_operation.name
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
#!/usr/bin/env python3
"""
Operation Lineage Service

Provides operation lineage tracing for complete automation of Elastic Moduli
calculations. Traces hydration operations back to source microstructure operations
to extract all required aggregate and air specifications.

This service achieves the 85-90% automation goal by eliminating the need for users
to re-enter information they already specified during microstructure creation.
"""

from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.orm import Session
from app.models import (
    Operation, OperationType,
    HydrationOperation, MicrostructureOperation,
    MixDesign, Aggregate
)
class OperationLineageService:
    """Service for tracing operation lineage and extracting specifications."""
    
    def __init__(self, db_session: Session):
        self.session = db_session
        import logging
        self.logger = logging.getLogger(__name__)
    
    def trace_hydration_to_microstructure(self, hydration_operation_id: int) -> Optional[Dict[str, Any]]:
        """
        Trace a hydration operation back to its source microstructure and extract
        all specifications needed for elastic moduli calculations.
        
        Args:
            hydration_operation_id: ID of the hydration operation
            
        Returns:
            Dictionary containing:
            - air_volume_fraction: float
            - fine_aggregates: List[dict] with volume_fraction, material_name, properties
            - coarse_aggregates: List[dict] with volume_fraction, material_name, properties
            - microstructure_operation_id: int (for reference)
            - mix_design_id: int (for reference)
        """
        try:
            # Get the hydration operation detail
            hydration_op = self.session.query(Operation).filter_by(id=hydration_operation_id).first()
            if not hydration_op or hydration_op.operation_type not in ['HYDRATION', 'hydration']:
                self.logger.error(f"No hydration operation found with ID {hydration_operation_id}")
                return None
            
            hydration_detail = self.session.query(HydrationOperation).filter_by(
                operation_id=hydration_operation_id
            ).first()
            
            if not hydration_detail:
                self.logger.error(f"No hydration operation detail found for ID {hydration_operation_id}")
                return None
            
            # Get the source microstructure operation
            source_micro_op_id = hydration_detail.microstructure_operation_id
            micro_detail = self.session.query(MicrostructureOperation).filter_by(
                operation_id=source_micro_op_id
            ).first()
            
            if not micro_detail:
                self.logger.error(f"No source microstructure operation found for hydration ID {hydration_operation_id}")
                return None
            
            # Get the mix design with all specifications
            mix_design = micro_detail.mix_design
            if not mix_design:
                self.logger.error(f"No mix design found for microstructure operation ID {source_micro_op_id}")
                return None
            
            # Extract aggregate specifications
            specifications = {
                'air_volume_fraction': mix_design.air_volume_fraction,
                'fine_aggregates': [],
                'coarse_aggregates': [],
                'microstructure_operation_id': source_micro_op_id,
                'mix_design_id': mix_design.id,
                'hydration_operation_name': hydration_op.name,
                'microstructure_operation_name': micro_detail.operation.name if micro_detail.operation else 'Unknown',
                'mix_design_name': mix_design.name
            }
            
            # Process aggregate components
            if mix_design.components:
                for component in mix_design.components:
                    if component.get('material_type') == 'aggregate':
                        # Get detailed aggregate properties from database
                        agg_spec = self._get_aggregate_specification(component)
                        
                        # Classify as fine or coarse aggregate
                        if self._is_fine_aggregate(component):
                            specifications['fine_aggregates'].append(agg_spec)
                        else:
                            specifications['coarse_aggregates'].append(agg_spec)
            
            self.logger.info(f"Successfully traced lineage for hydration operation {hydration_op.name}")
            return specifications
            
        except Exception as e:
            self.logger.error(f"Error tracing lineage for hydration operation {hydration_operation_id}: {e}")
            return None
    
    def get_all_aggregate_specifications(self, hydration_operation_id: int) -> Dict[str, Any]:
        """
        Get complete aggregate specifications for elastic moduli automation.
        
        This method provides all the data needed to auto-populate the Elastic Moduli
        panel fields, achieving the 85-90% automation goal.
        
        Returns:
            Dictionary with keys ready for UI population:
            - has_fine_aggregate: bool
            - fine_aggregate_volume_fraction: float
            - fine_aggregate_display_name: str
            - fine_aggregate_bulk_modulus: float
            - fine_aggregate_shear_modulus: float
            - has_coarse_aggregate: bool  
            - coarse_aggregate_volume_fraction: float
            - coarse_aggregate_display_name: str
            - coarse_aggregate_bulk_modulus: float
            - coarse_aggregate_shear_modulus: float
            - air_volume_fraction: float
            - has_itz: bool (True if aggregates present)
        """
        specs = self.trace_hydration_to_microstructure(hydration_operation_id)
        if not specs:
            return {}
        
        # Format for direct UI population
        ui_specs = {
            'air_volume_fraction': specs['air_volume_fraction'],
            'has_itz': len(specs['fine_aggregates']) > 0 or len(specs['coarse_aggregates']) > 0,
            'source_info': {
                'microstructure_operation_name': specs['microstructure_operation_name'],
                'mix_design_name': specs['mix_design_name']
            }
        }
        
        # Fine aggregate (take the first if multiple)
        if specs['fine_aggregates']:
            fine_agg = specs['fine_aggregates'][0]  # Use dominant fine aggregate
            ui_specs.update({
                'has_fine_aggregate': True,
                'fine_aggregate_volume_fraction': fine_agg['volume_fraction'],
                'fine_aggregate_display_name': fine_agg['display_name'],
                'fine_aggregate_bulk_modulus': fine_agg['bulk_modulus'],
                'fine_aggregate_shear_modulus': fine_agg['shear_modulus']
            })
        else:
            ui_specs.update({
                'has_fine_aggregate': False,
                'fine_aggregate_volume_fraction': 0.0,
                'fine_aggregate_display_name': '',
                'fine_aggregate_bulk_modulus': 0.0,
                'fine_aggregate_shear_modulus': 0.0
            })
        
        # Coarse aggregate (take the first if multiple)  
        if specs['coarse_aggregates']:
            coarse_agg = specs['coarse_aggregates'][0]  # Use dominant coarse aggregate
            ui_specs.update({
                'has_coarse_aggregate': True,
                'coarse_aggregate_volume_fraction': coarse_agg['volume_fraction'],
                'coarse_aggregate_display_name': coarse_agg['display_name'],
                'coarse_aggregate_bulk_modulus': coarse_agg['bulk_modulus'],
                'coarse_aggregate_shear_modulus': coarse_agg['shear_modulus']
            })
        else:
            ui_specs.update({
                'has_coarse_aggregate': False,
                'coarse_aggregate_volume_fraction': 0.0,
                'coarse_aggregate_display_name': '',
                'coarse_aggregate_bulk_modulus': 0.0,
                'coarse_aggregate_shear_modulus': 0.0
            })
        
        return ui_specs
    
    def _get_aggregate_specification(self, component: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed aggregate specification including mechanical properties."""
        material_name = component.get('material_name', '')
        
        # Look up aggregate in materials database
        aggregate = self.session.query(Aggregate).filter_by(name=material_name).first()
        
        if aggregate:
            return {
                'material_name': aggregate.name,
                'display_name': aggregate.display_name or aggregate.name,
                'volume_fraction': component.get('volume_fraction', 0.0),
                'mass_fraction': component.get('mass_fraction', 0.0),
                'specific_gravity': component.get('specific_gravity', aggregate.specific_gravity),
                'bulk_modulus': aggregate.bulk_modulus or 40.0,  # GPa, default for typical aggregate
                'shear_modulus': aggregate.shear_modulus or 25.0,  # GPa, default for typical aggregate
                'description': aggregate.description,
                'aggregate_type': self._classify_aggregate_type(aggregate)
            }
        else:
            # Default properties if aggregate not found in database
            return {
                'material_name': material_name,
                'display_name': material_name,
                'volume_fraction': component.get('volume_fraction', 0.0),
                'mass_fraction': component.get('mass_fraction', 0.0), 
                'specific_gravity': component.get('specific_gravity', 2.65),
                'bulk_modulus': 40.0,  # GPa, typical aggregate
                'shear_modulus': 25.0,  # GPa, typical aggregate
                'description': 'Aggregate from mix design',
                'aggregate_type': 'unknown'
            }
    
    def _is_fine_aggregate(self, component: Dict[str, Any]) -> bool:
        """Determine if an aggregate component is fine or coarse."""
        material_name = component.get('material_name', '').lower()
        
        # Classification based on name patterns
        fine_indicators = ['fine', 'sand', 'f-', 'f_']
        coarse_indicators = ['coarse', 'stone', 'c-', 'c_', 'gravel']
        
        # Check for explicit fine indicators
        if any(indicator in material_name for indicator in fine_indicators):
            return True
            
        # Check for explicit coarse indicators
        if any(indicator in material_name for indicator in coarse_indicators):
            return False
        
        # Look up in database for more accurate classification
        aggregate = self.session.query(Aggregate).filter_by(
            name=component.get('material_name')
        ).first()
        
        if aggregate and hasattr(aggregate, 'aggregate_type'):
            return aggregate.aggregate_type in ['fine', 'sand']
        
        # Default: smaller volume fractions tend to be fine aggregates
        volume_fraction = component.get('volume_fraction', 0.0)
        return volume_fraction < 0.2  # Threshold-based classification
    
    def _classify_aggregate_type(self, aggregate: Aggregate) -> str:
        """Classify aggregate type from database record."""
        if hasattr(aggregate, 'aggregate_type') and aggregate.aggregate_type:
            return aggregate.aggregate_type
        
        # Classify based on name
        name = aggregate.name.lower()
        if any(indicator in name for indicator in ['fine', 'sand']):
            return 'fine'
        elif any(indicator in name for indicator in ['coarse', 'stone', 'gravel']):
            return 'coarse'
        
        return 'unknown'
    
    def get_available_hydration_operations(self) -> List[Tuple[int, str, str]]:
        """
        Get list of hydration operations available for elastic moduli calculations.
        
        Returns:
            List of tuples: (operation_id, operation_name, status)
        """
        try:
            hydration_ops = self.session.query(Operation).filter(
                Operation.operation_type.in_(['HYDRATION', 'hydration'])
            ).all()
            
            return [(op.id, op.name, op.status) for op in hydration_ops]
            
        except Exception as e:
            self.logger.error(f"Error getting available hydration operations: {e}")
            return []
    
    def validate_operation_for_elastic_moduli(self, hydration_operation_id: int) -> Dict[str, Any]:
        """
        Validate that a hydration operation has all data needed for elastic moduli calculation.
        
        Returns:
            Dictionary with validation results:
            - is_valid: bool
            - missing_data: List[str] (what's missing)
            - warnings: List[str] (potential issues)
            - specifications: Dict (if valid)
        """
        validation = {
            'is_valid': False,
            'missing_data': [],
            'warnings': [],
            'specifications': {}
        }
        
        # Check if operation exists and is completed
        hydration_op = self.session.query(Operation).filter_by(id=hydration_operation_id).first()
        if not hydration_op:
            validation['missing_data'].append('Hydration operation not found')
            return validation
        
        if hydration_op.status != 'COMPLETED':
            validation['warnings'].append(f'Hydration operation status is {hydration_op.status}, not COMPLETED')
        
        # Get specifications
        specs = self.get_all_aggregate_specifications(hydration_operation_id)
        if not specs:
            validation['missing_data'].append('Could not trace operation lineage')
            return validation
        
        validation['specifications'] = specs
        
        # Check for required data
        if specs.get('air_volume_fraction', 0) <= 0:
            validation['warnings'].append('Air volume fraction is zero or missing')
        
        if not specs.get('has_fine_aggregate') and not specs.get('has_coarse_aggregate'):
            validation['warnings'].append('No aggregates found in microstructure')
        
        # Validation passes if we got specifications
        validation['is_valid'] = True
        
        return validation
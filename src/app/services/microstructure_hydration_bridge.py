#!/usr/bin/env python3
"""
Microstructure-Hydration Bridge Service

Handles data exchange between Microstructure Tool and Hydration Tool,
specifically for one-voxel bias parameter generation.
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

from app.services.one_voxel_bias_service import OneVoxelBiasService, OneVoxelBiasResult
from app.services.psd_service import PSDService, PSDParameters, DiscreteDistribution, PSDType


@dataclass
class MicrostructureMaterialInfo:
    """Information about a material used in microstructure generation."""
    phase_id: int
    material_name: str
    material_type: str  # 'cement', 'fly_ash', 'slag', etc.
    volume_fraction: float
    mass_fraction: float
    specific_gravity: float
    psd_parameters: Dict[str, Any]  # Original PSD parameters from database
    
    
@dataclass 
class MicrostructureMetadata:
    """Complete metadata for a microstructure generation."""
    operation_name: str
    microstructure_file: str  # Path to .img file
    system_size: int
    resolution: float  # μm per voxel
    materials: List[MicrostructureMaterialInfo]
    generation_timestamp: str
    

class MicrostructureHydrationBridge:
    """
    Service for data exchange between Microstructure and Hydration tools.
    
    Responsibilities:
    1. Store microstructure material metadata during generation
    2. Retrieve metadata for hydration parameter calculation  
    3. Calculate one-voxel bias from original PSD data
    4. Generate extended parameter file entries
    """
    
    def __init__(self, db_service=None):
        self.logger = logging.getLogger(__name__)
        self.db_service = db_service
        self.psd_service = PSDService()
        self.bias_service = OneVoxelBiasService()
        
        # Metadata storage directory
        self.metadata_dir = os.path.join(os.getcwd(), "microstructure_metadata")
        os.makedirs(self.metadata_dir, exist_ok=True)
    
    def store_microstructure_metadata(self, operation_name: str, 
                                    microstructure_file: str,
                                    system_size: int,
                                    resolution: float,
                                    materials_data: List[Dict[str, Any]]) -> bool:
        """
        Store microstructure metadata for later hydration use.
        
        Args:
            operation_name: Name of microstructure operation
            microstructure_file: Path to generated .img file
            system_size: System size in voxels
            resolution: Resolution in μm per voxel
            materials_data: List of material data from UI/database
            
        Returns:
            Success status
        """
        try:
            # Convert materials data to structured format
            materials = []
            phase_id = 1  # Start from 1 (0 is typically pore)
            
            for material_data in materials_data:
                material_info = MicrostructureMaterialInfo(
                    phase_id=phase_id,
                    material_name=material_data.get('name', f'Material_{phase_id}'),
                    material_type=material_data.get('material_type', 'unknown'),
                    volume_fraction=material_data.get('volume_fraction', 0.0),
                    mass_fraction=material_data.get('mass_fraction', 0.0), 
                    specific_gravity=material_data.get('specific_gravity', 2.65),
                    psd_parameters=self._extract_psd_parameters(material_data)
                )
                materials.append(material_info)
                phase_id += 1
            
            # Create metadata structure
            metadata = MicrostructureMetadata(
                operation_name=operation_name,
                microstructure_file=microstructure_file,
                system_size=system_size,
                resolution=resolution,
                materials=materials,
                generation_timestamp=datetime.utcnow().isoformat()
            )
            
            # Save to JSON file
            metadata_file = os.path.join(self.metadata_dir, f"{operation_name}_metadata.json")
            with open(metadata_file, 'w') as f:
                json.dump(asdict(metadata), f, indent=2)
            
            self.logger.info(f"Stored microstructure metadata: {metadata_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to store microstructure metadata: {e}")
            return False
    
    def load_microstructure_metadata(self, operation_name: str) -> Optional[MicrostructureMetadata]:
        """Load microstructure metadata from storage."""
        try:
            metadata_file = os.path.join(self.metadata_dir, f"{operation_name}_metadata.json")
            
            if not os.path.exists(metadata_file):
                self.logger.warning(f"Metadata file not found: {metadata_file}")
                return None
            
            with open(metadata_file, 'r') as f:
                data = json.load(f)
            
            # Convert back to dataclass
            materials = []
            for material_data in data['materials']:
                material = MicrostructureMaterialInfo(**material_data)
                materials.append(material)
            
            metadata = MicrostructureMetadata(
                operation_name=data['operation_name'],
                microstructure_file=data['microstructure_file'],
                system_size=data['system_size'],
                resolution=data['resolution'],
                materials=materials,
                generation_timestamp=data['generation_timestamp']
            )
            
            return metadata
            
        except Exception as e:
            self.logger.error(f"Failed to load microstructure metadata: {e}")
            return None
    
    def calculate_onevoxelbias_for_microstructure(self, operation_name: str) -> List[str]:
        """
        Calculate one-voxel bias parameters for a microstructure.
        
        Args:
            operation_name: Name of microstructure operation
            
        Returns:
            List of parameter lines for extended parameter file
        """
        try:
            # Load metadata
            metadata = self.load_microstructure_metadata(operation_name)
            if not metadata:
                raise ValueError(f"No metadata found for microstructure: {operation_name}")
            
            # Calculate bias for each material
            bias_results = []
            
            for material in metadata.materials:
                # Convert PSD parameters to discrete distribution
                psd_params = self._dict_to_psd_parameters(material.psd_parameters)
                discrete_psd = self.psd_service.convert_to_discrete(psd_params)
                
                # Calculate quantized diameters (use smallest discrete diameters)
                sorted_diameters = sorted(set(discrete_psd.diameters))
                quantized_diameters = sorted_diameters[:10]  # Use first 10
                
                # Calculate bias using the discrete PSD
                bias_result = self._calculate_material_bias(
                    material, discrete_psd, quantized_diameters
                )
                bias_results.append(bias_result)
            
            # Generate parameter lines
            parameter_lines = self.bias_service.generate_onevoxelbias_parameters(bias_results)
            
            self.logger.info(f"Calculated one-voxel bias for {len(bias_results)} materials")
            return parameter_lines
            
        except Exception as e:
            self.logger.error(f"Failed to calculate one-voxel bias: {e}")
            return []
    
    def _extract_psd_parameters(self, material_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract PSD parameters from material data."""
        psd_params = {}
        
        # Extract all PSD-related fields
        psd_fields = [
            'psd_mode', 'psd_d50', 'psd_n', 'psd_dmax', 'psd_exponent',
            'psd_custom_points', 'psd_median', 'psd_spread'
        ]
        
        for field in psd_fields:
            if field in material_data and material_data[field] is not None:
                psd_params[field] = material_data[field]
        
        return psd_params
    
    def _dict_to_psd_parameters(self, psd_dict: Dict[str, Any]) -> PSDParameters:
        """Convert dictionary to PSDParameters object."""
        psd_mode = psd_dict.get('psd_mode', 'log_normal')
        
        # Map string to enum
        psd_type_map = {
            'rosin_rammler': PSDType.ROSIN_RAMMLER,
            'log_normal': PSDType.LOG_NORMAL,
            'fuller_thompson': PSDType.FULLER_THOMPSON,
            'fuller': PSDType.FULLER_THOMPSON,
            'custom': PSDType.CUSTOM
        }
        
        psd_type = psd_type_map.get(psd_mode, PSDType.LOG_NORMAL)
        
        # Parse custom points if present
        custom_points = None
        if psd_dict.get('psd_custom_points'):
            try:
                import json
                points_data = json.loads(psd_dict['psd_custom_points'])
                custom_points = [(p[0], p[1]) for p in points_data]
            except:
                custom_points = None
        
        return PSDParameters(
            psd_type=psd_type,
            d50=psd_dict.get('psd_d50'),
            n=psd_dict.get('psd_n'),
            dmax=psd_dict.get('psd_dmax'),
            median=psd_dict.get('psd_median'),
            sigma=psd_dict.get('psd_spread'),
            exponent=psd_dict.get('psd_exponent'),
            custom_points=custom_points
        )
    
    def _calculate_material_bias(self, material: MicrostructureMaterialInfo,
                               discrete_psd: DiscreteDistribution,
                               quantized_diameters: List[float]) -> OneVoxelBiasResult:
        """Calculate bias for a single material."""
        if len(quantized_diameters) < 2:
            # Fallback quantized diameters
            quantized_diameters = [1.0, 2.0]
        
        d0 = quantized_diameters[0]
        d1 = quantized_diameters[1]
        cutoff = (d0 + d1) / 2.0
        
        # Find cutoff index
        cutoff_reached = False
        upperbin = 0
        
        for i, diameter in enumerate(discrete_psd.diameters):
            if diameter > cutoff:
                cutoff_reached = True
                upperbin = i
                break
        
        if not cutoff_reached:
            upperbin = len(discrete_psd.diameters) - 1
        
        # Calculate bias using OneVoxelBias algorithm
        bias = 1.0
        
        if upperbin > 1:
            # Build cumulative distribution
            cumulative = [0.0] * len(discrete_psd.mass_fractions)
            cumulative[0] = discrete_psd.mass_fractions[0]
            
            for i in range(1, upperbin + 1):
                cumulative[i] = cumulative[i-1] + discrete_psd.mass_fractions[i]
            
            # Normalize up to cutoff
            cutoff_cumulative = cumulative[upperbin]
            if cutoff_cumulative > 0:
                for i in range(upperbin + 1):
                    cumulative[i] /= cutoff_cumulative
            
            # Volume density function
            vdist = [0.0] * (upperbin + 1)
            for i in range(1, upperbin + 1):
                vdist[i] = cumulative[i] - cumulative[i-1]
            vdist[0] = 0.0
            
            # Integration kernel
            kernel = [0.0] * (upperbin + 1)
            for i in range(1, upperbin + 1):
                kernel[i] = vdist[i] * d0 / discrete_psd.diameters[i]
            
            # Trapezoidal integration - numerator
            bias = 0.0
            for i in range(1, upperbin + 1):
                diameter_diff = discrete_psd.diameters[i] - discrete_psd.diameters[i-1]
                bias += 0.5 * diameter_diff * (kernel[i-1] + kernel[i])
            
            # Trapezoidal integration - denominator
            for i in range(1, upperbin + 1):
                kernel[i] = vdist[i]
            
            denom = 0.0
            for i in range(1, upperbin + 1):
                diameter_diff = discrete_psd.diameters[i] - discrete_psd.diameters[i-1]
                denom += 0.5 * diameter_diff * (kernel[i-1] + kernel[i])
            
            # Final calculation
            if denom > 0:
                bias /= denom
        
        return OneVoxelBiasResult(
            phase_id=material.phase_id,
            material_name=material.material_name,
            bias_value=bias,
            volume_fraction=material.volume_fraction,
            d0=d0,
            d1=d1,
            cutoff_diameter=cutoff
        )
    
    def list_available_microstructures(self) -> List[str]:
        """List available microstructures with metadata."""
        try:
            if not os.path.exists(self.metadata_dir):
                return []
            
            microstructures = []
            for filename in os.listdir(self.metadata_dir):
                if filename.endswith('_metadata.json'):
                    operation_name = filename.replace('_metadata.json', '')
                    microstructures.append(operation_name)
            
            return sorted(microstructures)
            
        except Exception as e:
            self.logger.error(f"Failed to list microstructures: {e}")
            return []
    
    def get_microstructure_summary(self, operation_name: str) -> Optional[Dict[str, Any]]:
        """Get summary information about a microstructure."""
        metadata = self.load_microstructure_metadata(operation_name)
        if not metadata:
            return None
        
        return {
            'operation_name': metadata.operation_name,
            'microstructure_file': metadata.microstructure_file,
            'system_size': metadata.system_size,
            'resolution': metadata.resolution,
            'num_materials': len(metadata.materials),
            'materials': [
                {
                    'phase_id': m.phase_id,
                    'name': m.material_name,
                    'type': m.material_type,
                    'volume_fraction': m.volume_fraction
                }
                for m in metadata.materials
            ],
            'generation_timestamp': metadata.generation_timestamp
        }
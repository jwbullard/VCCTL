#!/usr/bin/env python3
"""
One-Voxel Bias Service for VCCTL

Calculates one-voxel bias parameters for hydration simulation based on 
material particle size distributions used in microstructure generation.

Ported from OneVoxelBias.java (nist.bfrl.vcctl.operation.sample.OnePixelBias)
"""

import os
import math
import logging
import json
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass

from app.services.psd_service import PSDService, PSDParameters, DiscreteDistribution


@dataclass 
class MaterialPSDData:
    """PSD data for a material phase."""
    phase_id: int
    material_name: str
    volume_fraction: float
    diameters: List[float]      # Particle diameters (μm)  
    mass_fractions: List[float] # Mass fractions
    quantized_diameters: List[float]  # Quantized diameter bounds


@dataclass
class OneVoxelBiasResult:
    """Result of one-voxel bias calculation."""
    phase_id: int
    material_name: str
    bias_value: float
    volume_fraction: float
    d0: float  # Smallest quantized diameter
    d1: float  # Second smallest quantized diameter
    cutoff_diameter: float  # (d0 + d1) / 2


class OneVoxelBiasService:
    """
    Service for calculating one-voxel bias parameters.
    
    Implements the algorithm from OneVoxelBias.java that calculates
    bias correction factors for each material phase based on their
    particle size distributions and quantized diameters.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.psd_service = PSDService()
        
        # PI/6 factor from original Java code
        self.factor = math.pi / 6.0
        
    def calculate_bias_for_microstructure(self, microstructure_path: str) -> List[OneVoxelBiasResult]:
        """
        Calculate one-voxel bias for all materials in a microstructure.
        
        Args:
            microstructure_path: Path to microstructure directory (e.g., ./scratch/MyMix01/)
            
        Returns:
            List of bias results for each material phase
        """
        try:
            # Parse microstructure input file to get material data
            material_data = self._parse_microstructure_input(microstructure_path)
            
            # Calculate bias for each material
            bias_results = []
            for material in material_data:
                try:
                    bias_result = self._calculate_bias_for_material(material)
                    bias_results.append(bias_result)
                    self.logger.info(f"Calculated bias for {material.material_name} (phase {material.phase_id}): {bias_result.bias_value:.6f}")
                except Exception as e:
                    self.logger.error(f"Failed to calculate bias for {material.material_name}: {e}")
                    # Create fallback result
                    bias_results.append(OneVoxelBiasResult(
                        phase_id=material.phase_id,
                        material_name=material.material_name,
                        bias_value=1.0,  # Default bias
                        volume_fraction=material.volume_fraction,
                        d0=1.0,
                        d1=2.0,
                        cutoff_diameter=1.5
                    ))
            
            return bias_results
            
        except Exception as e:
            self.logger.error(f"Failed to calculate bias for microstructure: {e}")
            raise
    
    def _parse_microstructure_input(self, microstructure_path: str) -> List[MaterialPSDData]:
        """Parse microstructure input file to extract material and PSD data."""
        input_file = os.path.join(microstructure_path, f"{os.path.basename(microstructure_path)}.img.in")
        
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Microstructure input file not found: {input_file}")
        
        materials = []
        
        with open(input_file, 'r') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
        
        try:
            # Parse file format based on MyMix01.img.in structure
            line_idx = 0
            
            # Skip header lines (random seed, flags, dimensions, etc.)
            line_idx += 6  # Lines 1-6: random seed, flags, dimensions, resolution
            
            # Read number of materials
            num_materials = int(lines[line_idx])
            line_idx += 1
            
            for material_idx in range(num_materials):
                # Read material header: phase_id, volume_fraction, num_size_classes
                phase_id = int(lines[line_idx])
                line_idx += 1
                volume_fraction = float(lines[line_idx]) 
                line_idx += 1
                num_size_classes = int(lines[line_idx])
                line_idx += 1
                
                # Read PSD data: diameter, mass_fraction pairs
                diameters = []
                mass_fractions = []
                
                for _ in range(num_size_classes):
                    diameter = float(lines[line_idx])
                    line_idx += 1
                    mass_fraction = float(lines[line_idx])
                    line_idx += 1
                    
                    diameters.append(diameter)
                    mass_fractions.append(mass_fraction)
                
                # Generate quantized diameters from discrete PSD
                # Use the smallest diameters as quantized bounds
                sorted_diameters = sorted(set(diameters))
                quantized_diameters = sorted_diameters[:10]  # Use first 10 unique diameters
                
                # Determine material name from phase ID
                material_name = self._get_material_name_from_phase_id(phase_id)
                
                materials.append(MaterialPSDData(
                    phase_id=phase_id,
                    material_name=material_name,
                    volume_fraction=volume_fraction,
                    diameters=diameters,
                    mass_fractions=mass_fractions,
                    quantized_diameters=quantized_diameters
                ))
            
            return materials
            
        except (ValueError, IndexError) as e:
            raise ValueError(f"Failed to parse microstructure input file: {e}")
    
    def _get_material_name_from_phase_id(self, phase_id: int) -> str:
        """Map phase ID to material name."""
        # Based on typical VCCTL phase mappings
        phase_names = {
            0: "Pore",
            1: "C3S", 
            2: "C2S",
            3: "C3A",
            4: "C4AF", 
            5: "Gypsum",
            6: "Hemihydrate",
            7: "Anhydrite",
            8: "Silica_Fume",
            9: "Fly_Ash",
            10: "Slag", 
            32: "Fine_Aggregate",
            33: "Coarse_Aggregate"
        }
        
        return phase_names.get(phase_id, f"Phase_{phase_id}")
    
    def _calculate_bias_for_material(self, material: MaterialPSDData) -> OneVoxelBiasResult:
        """
        Calculate one-voxel bias for a single material.
        
        Implements the algorithm from OneVoxelBias.java:
        1. Get quantized diameters d0 and d1 (smallest two)
        2. Calculate cutoff diameter = (d0 + d1) / 2
        3. Build cumulative PSD up to cutoff
        4. Calculate volume density function
        5. Apply trapezoidal integration with kernel
        """
        if len(material.quantized_diameters) < 2:
            raise ValueError(f"Need at least 2 quantized diameters, got {len(material.quantized_diameters)}")
        
        # Get d0 and d1 (smallest quantized diameters)
        d0 = material.quantized_diameters[0] 
        d1 = material.quantized_diameters[1]
        
        # Calculate one-pixel cutoff diameter
        cutoff_diameter = (d0 + d1) / 2.0
        
        # Find index where cutoff is reached
        cutoff_reached = False
        upperbin = 0
        
        for i, diameter in enumerate(material.diameters):
            if diameter > cutoff_diameter:
                cutoff_reached = True
                upperbin = i
                break
        
        if not cutoff_reached:
            upperbin = len(material.diameters) - 1
        
        # Calculate cumulative PSD up to cutoff
        cumulative = [0.0] * len(material.mass_fractions)
        cumulative[0] = material.mass_fractions[0]
        
        for i in range(1, upperbin + 1):
            cumulative[i] = cumulative[i-1] + material.mass_fractions[i]
        
        # Default bias value
        bias = 1.0
        
        if upperbin > 1:
            # Normalize cumulative PSD for diameters up to cutoff
            cutoff_cumulative = cumulative[upperbin]
            if cutoff_cumulative > 0:
                for i in range(upperbin + 1):
                    cumulative[i] /= cutoff_cumulative
            
            # Calculate volume density function 
            vdist = [0.0] * (upperbin + 1)
            for i in range(1, upperbin + 1):
                vdist[i] = cumulative[i] - cumulative[i-1]
            vdist[0] = 0.0
            
            # Calculate integration kernel
            kernel = [0.0] * (upperbin + 1)
            kernel[0] = 0.0
            for i in range(1, upperbin + 1):
                kernel[i] = vdist[i] * d0 / material.diameters[i]
            
            # Apply trapezoidal rule for numerator
            bias = 0.0
            for i in range(1, upperbin + 1):
                diameter_diff = material.diameters[i] - material.diameters[i-1]
                bias += 0.5 * diameter_diff * (kernel[i-1] + kernel[i])
            
            # Calculate denominator (integral of vdist)
            for i in range(1, upperbin + 1):
                kernel[i] = vdist[i]
            
            denom = 0.0
            for i in range(1, upperbin + 1):
                diameter_diff = material.diameters[i] - material.diameters[i-1]
                denom += 0.5 * diameter_diff * (kernel[i-1] + kernel[i])
            
            # Final bias calculation
            if denom > 0:
                bias /= denom
            else:
                bias = 1.0
        
        return OneVoxelBiasResult(
            phase_id=material.phase_id,
            material_name=material.material_name,
            bias_value=bias,
            volume_fraction=material.volume_fraction,
            d0=d0,
            d1=d1,
            cutoff_diameter=cutoff_diameter
        )
    
    def generate_onevoxelbias_parameters(self, bias_results: List[OneVoxelBiasResult]) -> List[str]:
        """
        Generate Onevoxelbias parameter lines for disrealnew extended parameter file.
        
        Returns:
            List of parameter lines in format: "Onevoxelbias,phase_id,bias_value"
        """
        parameter_lines = []
        
        for result in bias_results:
            # Skip pore phase (usually phase 0)
            if result.phase_id == 0:
                continue
                
            # Format: Onevoxelbias,phase_id,bias_value
            line = f"Onevoxelbias,{result.phase_id},{result.bias_value:.10f}"
            parameter_lines.append(line)
        
        return parameter_lines
    
    def export_bias_summary(self, bias_results: List[OneVoxelBiasResult], output_file: str) -> bool:
        """Export bias calculation summary to file."""
        try:
            with open(output_file, 'w') as f:
                f.write("One-Voxel Bias Calculation Summary\n")
                f.write("=====================================\n\n")
                
                for result in bias_results:
                    f.write(f"Material: {result.material_name} (Phase {result.phase_id})\n")
                    f.write(f"Volume Fraction: {result.volume_fraction:.6f}\n")
                    f.write(f"Quantized Diameters: d0={result.d0:.3f}μm, d1={result.d1:.3f}μm\n") 
                    f.write(f"Cutoff Diameter: {result.cutoff_diameter:.3f}μm\n")
                    f.write(f"Bias Value: {result.bias_value:.10f}\n")
                    f.write(f"Parameter Line: Onevoxelbias,{result.phase_id},{result.bias_value:.10f}\n")
                    f.write("-" * 50 + "\n\n")
            
            self.logger.info(f"Exported bias summary to {output_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export bias summary: {e}")
            return False
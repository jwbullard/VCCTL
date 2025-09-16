"""
Elastic Results Parser Service

Parses elastic moduli calculation output files and extracts key results
for visualization and analysis.
"""

import os
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ElasticModuliResults:
    """Container for elastic moduli calculation results."""
    
    # Effective moduli (main results)
    bulk_modulus: Optional[float] = None
    shear_modulus: Optional[float] = None
    youngs_modulus: Optional[float] = None
    poissons_ratio: Optional[float] = None
    
    # Additional elastic properties
    compressive_strength: Optional[float] = None
    tensile_strength: Optional[float] = None
    
    # Phase contributions
    phase_contributions: Optional[Dict[str, Dict[str, float]]] = None
    
    # ITZ properties (if present)
    itz_bulk_modulus: Optional[float] = None
    itz_shear_modulus: Optional[float] = None
    itz_properties: Optional[Dict[str, float]] = None
    
    # Metadata
    operation_name: str = ""
    calculation_time: Optional[datetime] = None
    system_size: Optional[Tuple[int, int, int]] = None
    volume_fractions: Optional[Dict[str, float]] = None
    
    # File paths
    effective_moduli_file: Optional[str] = None
    phase_contributions_file: Optional[str] = None
    itz_moduli_file: Optional[str] = None


class ElasticResultsParser:
    """Parser for elastic moduli calculation output files."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def parse_operation_results(self, operation_folder: str) -> Optional[ElasticModuliResults]:
        """
        Parse all elastic results from an operation folder.
        
        Args:
            operation_folder: Path to operation folder containing output files
            
        Returns:
            ElasticModuliResults object with parsed data, or None if parsing fails
        """
        try:
            operation_path = Path(operation_folder)
            if not operation_path.exists():
                self.logger.error(f"Operation folder does not exist: {operation_folder}")
                return None
            
            results = ElasticModuliResults()
            results.operation_name = operation_path.name
            
            # Look for output files
            effective_moduli_file = operation_path / "EffectiveModuli.dat"
            phase_contributions_file = operation_path / "PhaseContributions.dat"
            itz_moduli_file = operation_path / "ITZmoduli.dat"
            
            # Parse main effective moduli file
            if effective_moduli_file.exists():
                results.effective_moduli_file = str(effective_moduli_file)
                self._parse_effective_moduli(effective_moduli_file, results)
            else:
                self.logger.warning(f"EffectiveModuli.dat not found in {operation_folder}")
            
            # Parse phase contributions file
            if phase_contributions_file.exists():
                results.phase_contributions_file = str(phase_contributions_file)
                self._parse_phase_contributions(phase_contributions_file, results)
            
            # Parse ITZ moduli file if present
            if itz_moduli_file.exists():
                results.itz_moduli_file = str(itz_moduli_file)
                self._parse_itz_moduli(itz_moduli_file, results)
            
            # Try to extract metadata from other files or logs
            self._extract_metadata(operation_path, results)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error parsing elastic results from {operation_folder}: {e}")
            return None
    
    def _parse_effective_moduli(self, file_path: Path, results: ElasticModuliResults) -> None:
        """Parse the EffectiveModuli.dat file."""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Parse bulk modulus
            bulk_match = re.search(r'Bulk\s+modulus\s*[=:]\s*([\d.e\-+]+)', content, re.IGNORECASE)
            if bulk_match:
                results.bulk_modulus = float(bulk_match.group(1))
            
            # Parse shear modulus
            shear_match = re.search(r'Shear\s+modulus\s*[=:]\s*([\d.e\-+]+)', content, re.IGNORECASE)
            if shear_match:
                results.shear_modulus = float(shear_match.group(1))
            
            # Parse Young's modulus
            youngs_match = re.search(r'Young\'?s?\s+modulus\s*[=:]\s*([\d.e\-+]+)', content, re.IGNORECASE)
            if youngs_match:
                results.youngs_modulus = float(youngs_match.group(1))
            
            # Parse Poisson's ratio
            poisson_match = re.search(r'Poisson\'?s?\s+ratio\s*[=:]\s*([\d.e\-+]+)', content, re.IGNORECASE)
            if poisson_match:
                results.poissons_ratio = float(poisson_match.group(1))
            
            # Parse compressive strength if present
            comp_strength_match = re.search(r'Compressive\s+strength\s*[=:]\s*([\d.e\-+]+)', content, re.IGNORECASE)
            if comp_strength_match:
                results.compressive_strength = float(comp_strength_match.group(1))
            
            # Parse tensile strength if present
            tensile_strength_match = re.search(r'Tensile\s+strength\s*[=:]\s*([\d.e\-+]+)', content, re.IGNORECASE)
            if tensile_strength_match:
                results.tensile_strength = float(tensile_strength_match.group(1))
            
            self.logger.info(f"Parsed effective moduli: K={results.bulk_modulus}, G={results.shear_modulus}")
            
        except Exception as e:
            self.logger.error(f"Error parsing effective moduli file {file_path}: {e}")
    
    def _parse_phase_contributions(self, file_path: Path, results: ElasticModuliResults) -> None:
        """Parse the PhaseContributions.dat file."""
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            phase_data = {}
            volume_fractions = {}
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Look for phase contribution patterns
                # Example: "Phase 1 (C3S): Volume fraction = 0.35, Bulk modulus contribution = 15.2"
                phase_match = re.search(r'Phase\s+(\d+)\s*\(([^)]+)\):\s*Volume\s+fraction\s*=\s*([\d.e\-+]+)', line, re.IGNORECASE)
                if phase_match:
                    phase_num = phase_match.group(1)
                    phase_name = phase_match.group(2).strip()
                    volume_fraction = float(phase_match.group(3))
                    
                    if phase_name not in phase_data:
                        phase_data[phase_name] = {}
                    
                    volume_fractions[phase_name] = volume_fraction
                
                # Look for modulus contributions
                bulk_contrib_match = re.search(r'Bulk\s+modulus\s+contribution\s*=\s*([\d.e\-+]+)', line, re.IGNORECASE)
                if bulk_contrib_match and phase_name:
                    phase_data[phase_name]['bulk_contribution'] = float(bulk_contrib_match.group(1))
                
                shear_contrib_match = re.search(r'Shear\s+modulus\s+contribution\s*=\s*([\d.e\-+]+)', line, re.IGNORECASE)
                if shear_contrib_match and phase_name:
                    phase_data[phase_name]['shear_contribution'] = float(shear_contrib_match.group(1))
            
            results.phase_contributions = phase_data
            results.volume_fractions = volume_fractions
            
            self.logger.info(f"Parsed contributions for {len(phase_data)} phases")
            
        except Exception as e:
            self.logger.error(f"Error parsing phase contributions file {file_path}: {e}")
    
    def _parse_itz_moduli(self, file_path: Path, results: ElasticModuliResults) -> None:
        """Parse the ITZmoduli.dat file."""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Parse ITZ bulk modulus
            itz_bulk_match = re.search(r'ITZ\s+bulk\s+modulus\s*[=:]\s*([\d.e\-+]+)', content, re.IGNORECASE)
            if itz_bulk_match:
                results.itz_bulk_modulus = float(itz_bulk_match.group(1))
            
            # Parse ITZ shear modulus
            itz_shear_match = re.search(r'ITZ\s+shear\s+modulus\s*[=:]\s*([\d.e\-+]+)', content, re.IGNORECASE)
            if itz_shear_match:
                results.itz_shear_modulus = float(itz_shear_match.group(1))
            
            # Parse additional ITZ properties
            itz_properties = {}
            
            # Look for layer-by-layer ITZ data
            layer_matches = re.findall(r'Layer\s+(\d+):\s+K\s*=\s*([\d.e\-+]+),\s+G\s*=\s*([\d.e\-+]+)', content, re.IGNORECASE)
            if layer_matches:
                itz_properties['layer_data'] = []
                for layer_num, k_val, g_val in layer_matches:
                    itz_properties['layer_data'].append({
                        'layer': int(layer_num),
                        'bulk_modulus': float(k_val),
                        'shear_modulus': float(g_val)
                    })
            
            results.itz_properties = itz_properties
            
            self.logger.info(f"Parsed ITZ moduli: K={results.itz_bulk_modulus}, G={results.itz_shear_modulus}")
            
        except Exception as e:
            self.logger.error(f"Error parsing ITZ moduli file {file_path}: {e}")
    
    def _extract_metadata(self, operation_path: Path, results: ElasticModuliResults) -> None:
        """Extract metadata from log files or other sources."""
        try:
            # Look for log files or stdout files
            log_files = list(operation_path.glob("*stdout.txt")) + list(operation_path.glob("*.log"))
            
            for log_file in log_files[:1]:  # Check first log file
                try:
                    with open(log_file, 'r') as f:
                        content = f.read()
                    
                    # Extract system size
                    size_match = re.search(r'System\s+size:\s*(\d+)\s*x\s*(\d+)\s*x\s*(\d+)', content, re.IGNORECASE)
                    if size_match:
                        results.system_size = (int(size_match.group(1)), 
                                             int(size_match.group(2)), 
                                             int(size_match.group(3)))
                    
                    # Extract calculation time from timestamps
                    time_matches = re.findall(r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})', content)
                    if time_matches:
                        try:
                            results.calculation_time = datetime.strptime(time_matches[0], '%Y-%m-%d %H:%M:%S')
                        except:
                            pass
                    
                except Exception as e:
                    self.logger.warning(f"Could not extract metadata from {log_file}: {e}")
            
        except Exception as e:
            self.logger.warning(f"Error extracting metadata: {e}")
    
    def get_summary_string(self, results: ElasticModuliResults) -> str:
        """Generate a human-readable summary of the results."""
        summary_lines = []
        
        summary_lines.append(f"Elastic Moduli Results for {results.operation_name}")
        summary_lines.append("=" * 50)
        
        if results.bulk_modulus is not None:
            summary_lines.append(f"Bulk Modulus (K): {results.bulk_modulus:.2f} GPa")
        
        if results.shear_modulus is not None:
            summary_lines.append(f"Shear Modulus (G): {results.shear_modulus:.2f} GPa")
        
        if results.youngs_modulus is not None:
            summary_lines.append(f"Young's Modulus (E): {results.youngs_modulus:.2f} GPa")
        
        if results.poissons_ratio is not None:
            summary_lines.append(f"Poisson's Ratio (ν): {results.poissons_ratio:.3f}")
        
        if results.compressive_strength is not None:
            summary_lines.append(f"Compressive Strength: {results.compressive_strength:.2f} MPa")
        
        if results.system_size:
            summary_lines.append(f"System Size: {results.system_size[0]} × {results.system_size[1]} × {results.system_size[2]}")
        
        if results.volume_fractions:
            summary_lines.append("\nPhase Volume Fractions:")
            for phase, fraction in results.volume_fractions.items():
                summary_lines.append(f"  {phase}: {fraction:.3f}")
        
        if results.itz_bulk_modulus is not None:
            summary_lines.append(f"\nITZ Bulk Modulus: {results.itz_bulk_modulus:.2f} GPa")
        
        if results.itz_shear_modulus is not None:
            summary_lines.append(f"ITZ Shear Modulus: {results.itz_shear_modulus:.2f} GPa")
        
        return "\n".join(summary_lines)


def create_elastic_results_parser() -> ElasticResultsParser:
    """Factory function to create an ElasticResultsParser instance."""
    return ElasticResultsParser()
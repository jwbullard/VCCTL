#!/usr/bin/env python3
"""
Particle Size Distribution (PSD) Service

Unified service for handling particle size distributions across all material types.
Supports mathematical models (Rosin-Rammler, log-normal) and discrete data,
with automatic conversion to discrete points for display and genmic.c compatibility.
"""

import json
import math
import logging
import numpy as np
from typing import List, Tuple, Dict, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum


class PSDType(Enum):
    """Supported PSD model types."""
    ROSIN_RAMMLER = "rosin_rammler"
    LOG_NORMAL = "log_normal" 
    FULLER_THOMPSON = "fuller_thompson"
    CUSTOM = "custom"


@dataclass
class PSDParameters:
    """Parameters for mathematical PSD models."""
    psd_type: PSDType
    
    # Rosin-Rammler parameters
    d50: Optional[float] = None  # Characteristic diameter (μm)
    n: Optional[float] = None    # Distribution parameter
    dmax: Optional[float] = None # Maximum diameter (μm)
    
    # Log-normal parameters
    median: Optional[float] = None  # Median diameter (μm)
    sigma: Optional[float] = None   # Standard deviation
    
    # Fuller-Thompson parameters
    exponent: Optional[float] = None  # Fuller exponent (typically 0.5)
    
    # Custom discrete points
    custom_points: Optional[List[Tuple[float, float]]] = None  # [(diameter, mass_fraction), ...]


@dataclass
class DiscreteDistribution:
    """Discrete particle size distribution."""
    diameters: List[float]      # Diameter values (μm)
    mass_fractions: List[float] # Mass fractions (sum to 1.0)
    
    def __post_init__(self):
        """Validate discrete distribution data."""
        if len(self.diameters) != len(self.mass_fractions):
            raise ValueError("Diameters and mass fractions must have same length")
        
        if any(d <= 0 for d in self.diameters):
            raise ValueError("All diameters must be positive")
        
        if any(f < 0 for f in self.mass_fractions):
            raise ValueError("All mass fractions must be non-negative")
        
        total = sum(self.mass_fractions)
        if abs(total - 1.0) > 0.001:
            # Auto-normalize if close to 1.0
            if abs(total) > 0.001:
                self.mass_fractions = [f / total for f in self.mass_fractions]
    
    @property
    def points(self) -> List[Tuple[float, float]]:
        """Get as list of (diameter, mass_fraction) tuples."""
        return list(zip(self.diameters, self.mass_fractions))
    
    @property
    def d50(self) -> float:
        """Calculate D50 (median diameter) from discrete data."""
        cumulative = np.cumsum(self.mass_fractions)
        # Find where cumulative fraction crosses 0.5
        for i, cum_frac in enumerate(cumulative):
            if cum_frac >= 0.5:
                if i == 0:
                    return self.diameters[0]
                # Linear interpolation
                prev_cum = cumulative[i-1] if i > 0 else 0
                t = (0.5 - prev_cum) / (cum_frac - prev_cum)
                return self.diameters[i-1] + t * (self.diameters[i] - self.diameters[i-1])
        return self.diameters[-1]  # Fallback


class PSDService:
    """Service for particle size distribution operations."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Standard diameter range for conversions (μm)
        self.min_diameter = 0.25
        self.max_diameter = 75.0
        self.default_points = 30
        
        # Integer-centered binning parameters
        self.use_integer_bins = True     # Use integer-centered diameter bins
        self.use_logarithmic_bins = True # Use logarithmic spacing instead of linear
        self.bin_width = 1.0             # Width of each bin (μm) - for linear spacing
    
    def convert_to_discrete(self, params: PSDParameters, num_points: int = None) -> DiscreteDistribution:
        """Convert any PSD model to discrete distribution."""
        num_points = num_points or self.default_points
        
        try:
            if params.psd_type == PSDType.ROSIN_RAMMLER:
                return self._convert_rosin_rammler(params.d50, params.n, params.dmax, num_points)
            
            elif params.psd_type == PSDType.LOG_NORMAL:
                return self._convert_log_normal(params.median, params.sigma, num_points)
            
            elif params.psd_type == PSDType.FULLER_THOMPSON:
                return self._convert_fuller_thompson(params.exponent, params.dmax, num_points)
            
            elif params.psd_type == PSDType.CUSTOM:
                if not params.custom_points:
                    return self._generate_default_distribution()
                return self._process_custom_points(params.custom_points)
            
            else:
                self.logger.warning(f"Unknown PSD type: {params.psd_type}")
                return self._generate_default_distribution()
                
        except Exception as e:
            self.logger.error(f"Failed to convert PSD to discrete: {e}")
            return self._generate_default_distribution()
    
    def _convert_rosin_rammler(self, d50: float, n: float, dmax: float = None, num_points: int = 30) -> DiscreteDistribution:
        """Convert Rosin-Rammler parameters to discrete distribution."""
        if not d50 or not n or d50 <= 0 or n <= 0:
            raise ValueError("Invalid Rosin-Rammler parameters")
        
        if self.use_integer_bins:
            return self._convert_rosin_rammler_integer_bins(d50, n, dmax)
        
        # Legacy logarithmic binning (kept for compatibility)
        max_diameter = dmax if dmax else self.max_diameter
        diameters = np.logspace(np.log10(self.min_diameter), np.log10(max_diameter), num_points)
        
        # Rosin-Rammler cumulative distribution: R = 1 - exp(-(d/d50)^n)
        cumulative = 1 - np.exp(-((diameters / d50) ** n))
        
        # Convert cumulative to differential (mass fractions)
        mass_fractions = np.diff(np.concatenate([[0], cumulative]))
        
        # Ensure we have the right number of points
        if len(mass_fractions) < len(diameters):
            mass_fractions = np.append(mass_fractions, 0)
        
        # Normalize to sum to 1.0
        mass_fractions = mass_fractions / np.sum(mass_fractions)
        
        return DiscreteDistribution(diameters.tolist(), mass_fractions.tolist())
    
    def _convert_rosin_rammler_integer_bins(self, d50: float, n: float, dmax: float = None) -> DiscreteDistribution:
        """Convert Rosin-Rammler to integer-centered bins: (0-1.5], (1.5-2.5], (2.5-3.5], etc."""
        max_diameter = dmax if dmax else self.max_diameter
        
        # Create diameter bins (logarithmic or linear)
        if self.use_logarithmic_bins:
            bin_centers = self._generate_logarithmic_bins(max_diameter)
        else:
            # Linear spacing: 1, 2, 3, 4, ... up to max_diameter
            max_bin_center = int(max_diameter)
            bin_centers = list(range(1, max_bin_center + 1))
        
        # Calculate bin boundaries: (0-1.5], (1.5-2.5], (2.5-3.5], etc.
        bin_boundaries = []
        for center in bin_centers:
            lower = center - 0.5 if center > 1 else 0.0
            upper = center + 0.5
            bin_boundaries.append((lower, upper))
        
        # Calculate mass fraction for each bin using Rosin-Rammler
        mass_fractions = []
        for lower, upper in bin_boundaries:
            # Rosin-Rammler cumulative: R = 1 - exp(-(d/d50)^n)
            cum_lower = 1 - np.exp(-((lower / d50) ** n)) if lower > 0 else 0.0
            cum_upper = 1 - np.exp(-((upper / d50) ** n))
            
            # Mass fraction is difference in cumulative
            mass_fraction = cum_upper - cum_lower
            mass_fractions.append(mass_fraction)
        
        # Normalize to sum to 1.0
        total = sum(mass_fractions)
        if total > 0:
            mass_fractions = [f / total for f in mass_fractions]
        
        return DiscreteDistribution(bin_centers, mass_fractions)
    
    def _generate_logarithmic_bins(self, max_diameter: float) -> List[float]:
        """Generate logarithmically-spaced diameter bins up to max_diameter."""
        # Create approximately logarithmic diameter bins
        # Fine resolution at small sizes, coarser at large sizes
        bins = []
        
        # Fine bins: 1, 2, 3, 4, 5 μm (1 μm steps)
        for d in range(1, 6):
            if d <= max_diameter:
                bins.append(float(d))
        
        # Medium bins: 6, 8, 10, 12, 15 μm (2-3 μm steps)  
        medium_bins = [6, 8, 10, 12, 15]
        for d in medium_bins:
            if d <= max_diameter:
                bins.append(float(d))
        
        # Coarse bins: 20, 25, 30, 40, 50, 60, 75 μm (5-15 μm steps)
        coarse_bins = [20, 25, 30, 40, 50, 60, 75]
        for d in coarse_bins:
            if d <= max_diameter:
                bins.append(float(d))
        
        # Very coarse bins for large max_diameter: 100, 125, 150, 200
        if max_diameter > 75:
            very_coarse_bins = [100, 125, 150, 200]
            for d in very_coarse_bins:
                if d <= max_diameter:
                    bins.append(float(d))
        
        # Ensure we don't exceed max_diameter and have reasonable coverage
        bins = [d for d in bins if d <= max_diameter]
        
        # If max_diameter is not in our predefined list, add it
        if bins and bins[-1] < max_diameter:
            bins.append(float(max_diameter))
        elif not bins:  # Fallback for very small max_diameter
            bins = [float(max_diameter)]
        
        return bins
    
    def _convert_log_normal(self, median: float, sigma: float, num_points: int = 30) -> DiscreteDistribution:
        """Convert log-normal parameters to discrete distribution."""
        if not median or not sigma or median <= 0 or sigma <= 0:
            raise ValueError("Invalid log-normal parameters")
        
        if self.use_integer_bins:
            return self._convert_log_normal_integer_bins(median, sigma)
        
        # Legacy logarithmic binning (kept for compatibility)
        diameters = np.logspace(np.log10(self.min_diameter), np.log10(self.max_diameter), num_points)
        
        # Log-normal parameters
        mu = np.log(median)
        
        # Calculate probability density for each diameter bin
        mass_fractions = []
        for i, diameter in enumerate(diameters):
            if i == 0:
                lower_bound = 0
                upper_bound = (diameters[0] + diameters[1]) / 2 if len(diameters) > 1 else diameters[0] * 1.5
            elif i == len(diameters) - 1:
                lower_bound = (diameters[i-1] + diameters[i]) / 2
                upper_bound = float('inf')
            else:
                lower_bound = (diameters[i-1] + diameters[i]) / 2
                upper_bound = (diameters[i] + diameters[i+1]) / 2
            
            # Calculate cumulative probabilities
            prob_lower = self._log_normal_cdf(lower_bound, mu, sigma) if lower_bound > 0 else 0
            prob_upper = self._log_normal_cdf(upper_bound, mu, sigma) if upper_bound != float('inf') else 1
            
            mass_fraction = prob_upper - prob_lower
            mass_fractions.append(mass_fraction)
        
        # Normalize
        total = sum(mass_fractions)
        if total > 0:
            mass_fractions = [f / total for f in mass_fractions]
        
        return DiscreteDistribution(diameters.tolist(), mass_fractions)
    
    def _convert_log_normal_integer_bins(self, median: float, sigma: float) -> DiscreteDistribution:
        """Convert log-normal to logarithmically-spaced diameter bins."""
        max_diameter = self.max_diameter
        
        # Create diameter bins (logarithmic or linear)
        if self.use_logarithmic_bins:
            bin_centers = self._generate_logarithmic_bins(max_diameter)
        else:
            # Linear spacing: 1, 2, 3, 4, ... up to max_diameter
            max_bin_center = int(max_diameter)
            bin_centers = list(range(1, max_bin_center + 1))
        
        # Log-normal parameters
        mu = np.log(median)
        
        # Calculate mass fraction for each bin
        mass_fractions = []
        for i, center in enumerate(bin_centers):
            # Calculate bin boundaries based on logarithmic spacing
            if i == 0:
                lower = 0.0
                upper = (center + bin_centers[i+1]) / 2 if i+1 < len(bin_centers) else center + 0.5
            elif i == len(bin_centers) - 1:
                lower = (bin_centers[i-1] + center) / 2
                upper = center + 0.5
            else:
                lower = (bin_centers[i-1] + center) / 2
                upper = (center + bin_centers[i+1]) / 2
            
            # Calculate cumulative probabilities using log-normal CDF
            prob_lower = self._log_normal_cdf(lower, mu, sigma) if lower > 0 else 0
            prob_upper = self._log_normal_cdf(upper, mu, sigma)
            
            mass_fraction = prob_upper - prob_lower
            mass_fractions.append(mass_fraction)
        
        # Normalize
        total = sum(mass_fractions)
        if total > 0:
            mass_fractions = [f / total for f in mass_fractions]
        
        return DiscreteDistribution(bin_centers, mass_fractions)
    
    def _convert_fuller_thompson(self, exponent: float = 0.5, dmax: float = None, num_points: int = 30) -> DiscreteDistribution:
        """Convert Fuller-Thompson curve to discrete distribution."""
        if not exponent or exponent <= 0:
            exponent = 0.5  # Standard Fuller curve
        
        if self.use_integer_bins:
            return self._convert_fuller_thompson_integer_bins(exponent, dmax)
        
        # Legacy logarithmic binning (kept for compatibility)
        max_diameter = dmax if dmax else self.max_diameter
        diameters = np.logspace(np.log10(self.min_diameter), np.log10(max_diameter), num_points)
        
        # Fuller-Thompson: P = (d/dmax)^exponent where P is cumulative passing
        cumulative = (diameters / max_diameter) ** exponent
        
        # Convert cumulative to differential
        mass_fractions = np.diff(np.concatenate([[0], cumulative]))
        
        # Ensure we have the right number of points
        if len(mass_fractions) < len(diameters):
            mass_fractions = np.append(mass_fractions, 0)
        
        # Normalize
        mass_fractions = mass_fractions / np.sum(mass_fractions)
        
        return DiscreteDistribution(diameters.tolist(), mass_fractions.tolist())
    
    def _convert_fuller_thompson_integer_bins(self, exponent: float, dmax: float = None) -> DiscreteDistribution:
        """Convert Fuller-Thompson to logarithmically-spaced diameter bins."""
        max_diameter = dmax if dmax else self.max_diameter
        
        # Create diameter bins (logarithmic or linear)
        if self.use_logarithmic_bins:
            bin_centers = self._generate_logarithmic_bins(max_diameter)
        else:
            # Linear spacing: 1, 2, 3, 4, ... up to max_diameter
            max_bin_center = int(max_diameter)
            bin_centers = list(range(1, max_bin_center + 1))
        
        # Calculate mass fraction for each bin using Fuller-Thompson
        mass_fractions = []
        for i, center in enumerate(bin_centers):
            # Calculate bin boundaries based on logarithmic spacing
            if i == 0:
                lower = 0.0
                upper = (center + bin_centers[i+1]) / 2 if i+1 < len(bin_centers) else center + 0.5
            elif i == len(bin_centers) - 1:
                lower = (bin_centers[i-1] + center) / 2
                upper = center + 0.5
            else:
                lower = (bin_centers[i-1] + center) / 2
                upper = (center + bin_centers[i+1]) / 2
            
            # Fuller-Thompson cumulative: P = (d/dmax)^exponent
            cum_lower = (lower / max_diameter) ** exponent if lower > 0 else 0.0
            cum_upper = (upper / max_diameter) ** exponent
            
            # Mass fraction is difference in cumulative
            mass_fraction = cum_upper - cum_lower
            mass_fractions.append(mass_fraction)
        
        # Normalize to sum to 1.0
        total = sum(mass_fractions)
        if total > 0:
            mass_fractions = [f / total for f in mass_fractions]
        
        return DiscreteDistribution(bin_centers, mass_fractions)
    
    def _process_custom_points(self, custom_points: List[Tuple[float, float]]) -> DiscreteDistribution:
        """Process custom discrete points."""
        if not custom_points:
            return self._generate_default_distribution()
        
        # Sort by diameter
        sorted_points = sorted(custom_points, key=lambda x: x[0])
        diameters, mass_fractions = zip(*sorted_points)
        
        return DiscreteDistribution(list(diameters), list(mass_fractions))
    
    def _log_normal_cdf(self, x: float, mu: float, sigma: float) -> float:
        """Calculate cumulative distribution function for log-normal distribution."""
        if x <= 0:
            return 0.0
        
        # Use error function for normal CDF of log(x)
        z = (np.log(x) - mu) / (sigma * np.sqrt(2))
        return 0.5 * (1 + math.erf(z))
    
    def _generate_default_distribution(self) -> DiscreteDistribution:
        """Generate a default distribution for fallback cases."""
        # Simple uniform distribution across standard range
        diameters = np.logspace(np.log10(self.min_diameter), np.log10(self.max_diameter), 10).tolist()
        mass_fractions = [0.1] * 10  # Equal mass fractions
        
        return DiscreteDistribution(diameters, mass_fractions)
    
    def bin_for_genmic(self, distribution: DiscreteDistribution) -> List[Tuple[int, float]]:
        """Bin discrete distribution for genmic.c compatibility (integer diameters)."""
        try:
            # Round diameters to integers and combine fractions for same diameters
            binned_data = {}
            
            for diameter, mass_fraction in distribution.points:
                int_diameter = max(1, round(diameter))  # Minimum 1 μm
                if int_diameter in binned_data:
                    binned_data[int_diameter] += mass_fraction
                else:
                    binned_data[int_diameter] = mass_fraction
            
            # Sort by diameter and normalize
            sorted_bins = sorted(binned_data.items())
            total_mass = sum(mass for _, mass in sorted_bins)
            
            if total_mass > 0:
                normalized_bins = [(diameter, mass / total_mass) for diameter, mass in sorted_bins]
            else:
                # Fallback: single bin at 10 μm
                normalized_bins = [(10, 1.0)]
            
            return normalized_bins
            
        except Exception as e:
            self.logger.error(f"Failed to bin PSD for genmic: {e}")
            return [(10, 1.0)]  # Fallback
    
    def parse_psd_from_material(self, material_data: Dict[str, Any]) -> PSDParameters:
        """Parse PSD parameters from material data dictionary."""
        try:
            # Check for PSD data object (newer materials using relationships)
            psd_data_obj = material_data.get('psd_data')
            if psd_data_obj:
                psd_mode = getattr(psd_data_obj, 'psd_mode', None)
                if psd_mode == 'rosin_rammler':
                    return PSDParameters(
                        psd_type=PSDType.ROSIN_RAMMLER,
                        d50=getattr(psd_data_obj, 'psd_d50', None),
                        n=getattr(psd_data_obj, 'psd_n', None),
                        dmax=getattr(psd_data_obj, 'psd_dmax', None)
                    )
                elif psd_mode == 'log_normal':
                    return PSDParameters(
                        psd_type=PSDType.LOG_NORMAL,
                        median=getattr(psd_data_obj, 'psd_median', 10.0),
                        sigma=getattr(psd_data_obj, 'psd_spread', 2.0)
                    )
                elif psd_mode == 'fuller':
                    return PSDParameters(
                        psd_type=PSDType.FULLER_THOMPSON,
                        exponent=getattr(psd_data_obj, 'psd_exponent', None),
                        dmax=getattr(psd_data_obj, 'psd_dmax', None)
                    )
                elif psd_mode == 'custom':
                    custom_data = getattr(psd_data_obj, 'psd_custom_points', None)
                    custom_points = None
                    if custom_data:
                        try:
                            points_data = json.loads(custom_data)
                            custom_points = [(p[0], p[1]) for p in points_data]
                        except (json.JSONDecodeError, IndexError, KeyError) as e:
                            self.logger.warning(f"Failed to parse custom PSD points from psd_data: {e}")
                    
                    return PSDParameters(
                        psd_type=PSDType.CUSTOM,
                        custom_points=custom_points
                    )
            
            # Check for existing PSD mode (cement materials - flat fields)
            psd_mode = material_data.get('psd_mode')
            
            if psd_mode == 'rosin_rammler':
                return PSDParameters(
                    psd_type=PSDType.ROSIN_RAMMLER,
                    d50=material_data.get('psd_d50'),
                    n=material_data.get('psd_n'),
                    dmax=material_data.get('psd_dmax')
                )
            
            elif psd_mode == 'fuller':
                return PSDParameters(
                    psd_type=PSDType.FULLER_THOMPSON,
                    exponent=material_data.get('psd_exponent'),
                    dmax=material_data.get('psd_dmax')
                )
            
            elif psd_mode == 'custom':
                custom_points_json = material_data.get('psd_custom_points')
                custom_points = None
                if custom_points_json:
                    try:
                        points_data = json.loads(custom_points_json)
                        custom_points = [(p[0], p[1]) for p in points_data]
                    except (json.JSONDecodeError, IndexError, KeyError) as e:
                        self.logger.warning(f"Failed to parse custom PSD points: {e}")
                
                return PSDParameters(
                    psd_type=PSDType.CUSTOM,
                    custom_points=custom_points
                )
            
            # Check for simple median/spread parameters (other materials)
            elif material_data.get('psd_median') and material_data.get('psd_spread'):
                return PSDParameters(
                    psd_type=PSDType.LOG_NORMAL,
                    median=material_data.get('psd_median'),
                    sigma=material_data.get('psd_spread')
                )
            
            else:
                # Default to log-normal with reasonable defaults
                return PSDParameters(
                    psd_type=PSDType.LOG_NORMAL,
                    median=10.0,  # 10 μm default
                    sigma=2.0     # Default spread
                )
                
        except Exception as e:
            self.logger.error(f"Failed to parse PSD from material: {e}")
            return PSDParameters(psd_type=PSDType.LOG_NORMAL, median=10.0, sigma=2.0)
    
    def create_table_data(self, distribution: DiscreteDistribution) -> List[List[str]]:
        """Create table data for GTK TreeView display."""
        table_data = []
        
        for diameter, mass_fraction in distribution.points:
            table_data.append([
                f"{diameter:.2f}",           # Diameter (μm)
                f"{mass_fraction:.4f}",      # Mass fraction
                f"{mass_fraction * 100:.2f}" # Percentage
            ])
        
        return table_data
    
    def export_to_csv(self, distribution: DiscreteDistribution, filename: str) -> bool:
        """Export distribution to CSV file."""
        try:
            import csv
            
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Diameter (μm)', 'Mass Fraction', 'Percentage'])
                
                for diameter, mass_fraction in distribution.points:
                    writer.writerow([diameter, mass_fraction, mass_fraction * 100])
            
            self.logger.info(f"Exported PSD to {filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export PSD to CSV: {e}")
            return False
    
    def import_from_csv(self, filename: str) -> Optional[DiscreteDistribution]:
        """Import distribution from CSV file."""
        try:
            import csv
            
            points = []
            with open(filename, 'r') as csvfile:
                reader = csv.reader(csvfile)
                next(reader)  # Skip header
                
                for row in reader:
                    if len(row) >= 2:
                        diameter = float(row[0])
                        mass_fraction = float(row[1])
                        points.append((diameter, mass_fraction))
            
            if not points:
                raise ValueError("No valid data points found in CSV")
            
            return self._process_custom_points(points)
            
        except Exception as e:
            self.logger.error(f"Failed to import PSD from CSV: {e}")
            return None
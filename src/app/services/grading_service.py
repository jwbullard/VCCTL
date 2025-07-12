#!/usr/bin/env python3
"""
Grading Service for VCCTL

Provides business logic for particle size distribution and sieve analysis management.
Converted from Java Spring service to Python.
"""

import logging
import io
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.exc import IntegrityError
from dataclasses import dataclass
from enum import Enum

from app.database.service import DatabaseService
from app.models.grading import Grading, GradingCreate, GradingUpdate, GradingResponse
from app.models.aggregate_sieve import AggregateSieve
from app.services.base_service import BaseService, ServiceError, NotFoundError, AlreadyExistsError, ValidationError


class SieveStandard(Enum):
    """Standard sieve series."""
    ASTM = "ASTM"           # ASTM C136/C117
    ISO = "ISO"             # ISO 3310
    BS = "BS"               # British Standard


class GradationType(Enum):
    """Grading curve types."""
    FINE = "FINE"           # Fine aggregate (sand)
    COARSE = "COARSE"       # Coarse aggregate (gravel)


@dataclass
class SieveAnalysisResult:
    """Result of sieve analysis calculations."""
    sieve_size_mm: float
    mass_retained_g: float = 0.0
    mass_retained_percent: float = 0.0
    cumulative_retained_percent: float = 0.0
    cumulative_passing_percent: float = 0.0
    
    def __post_init__(self):
        """Validate sieve analysis data."""
        if self.sieve_size_mm <= 0:
            raise ValueError("Sieve size must be positive")
        if self.mass_retained_g < 0:
            raise ValueError("Mass retained cannot be negative")


@dataclass
class GradingCurveData:
    """Complete grading curve data structure."""
    name: str
    grading_type: GradationType
    sieves: List[SieveAnalysisResult]
    total_sample_mass: float = 0.0
    fineness_modulus: float = 0.0
    max_particle_size: float = 0.0
    
    def __post_init__(self):
        """Calculate derived properties."""
        if self.sieves:
            self.max_particle_size = max(s.sieve_size_mm for s in self.sieves)
            self.total_sample_mass = sum(s.mass_retained_g for s in self.sieves)
            self._calculate_fineness_modulus()
    
    def _calculate_fineness_modulus(self):
        """Calculate fineness modulus from sieve data."""
        # Standard sieves for fineness modulus calculation (mm)
        fm_sieves = [0.15, 0.30, 0.60, 1.18, 2.36, 4.75, 9.50, 19.0, 37.5]
        
        cumulative_retained_sum = 0.0
        for fm_sieve in fm_sieves:
            # Find the closest sieve in our data
            closest_sieve = min(
                self.sieves,
                key=lambda s: abs(s.sieve_size_mm - fm_sieve),
                default=None
            )
            
            # Use cumulative retained if sieve is close enough
            if closest_sieve and abs(closest_sieve.sieve_size_mm - fm_sieve) / fm_sieve < 0.15:
                cumulative_retained_sum += closest_sieve.cumulative_retained_percent
        
        self.fineness_modulus = cumulative_retained_sum / 100.0


class GradingService(BaseService[Grading, GradingCreate, GradingUpdate]):
    """
    Service for managing particle size distributions and sieve analysis.
    
    Provides CRUD operations, sieve analysis calculations, and grading curve
    generation for the VCCTL system.
    """
    
    def __init__(self, db_service: DatabaseService):
        super().__init__(Grading, db_service)
        self.logger = logging.getLogger('VCCTL.GradingService')
        
        # Standard sieve sizes (mm) for different standards
        self.standard_sieves = {
            SieveStandard.ASTM: [
                0.075, 0.15, 0.30, 0.60, 1.18, 2.36, 4.75, 9.50, 
                12.5, 19.0, 25.0, 37.5, 50.0, 63.0, 75.0
            ],
            SieveStandard.ISO: [
                0.063, 0.125, 0.25, 0.50, 1.0, 2.0, 4.0, 8.0,
                16.0, 31.5, 63.0
            ]
        }
    
    def get_all(self) -> List[Grading]:
        """Get all grading curves."""
        try:
            with self.db_service.get_read_only_session() as session:
                return session.query(Grading).order_by(Grading.name).all()
        except Exception as e:
            self.logger.error(f"Failed to get all grading curves: {e}")
            raise ServiceError(f"Failed to retrieve grading curves: {e}")
    
    def get_by_name(self, name: str) -> Optional[Grading]:
        """Get grading curve by name."""
        try:
            with self.db_service.get_read_only_session() as session:
                return session.query(Grading).filter_by(name=name).first()
        except Exception as e:
            self.logger.error(f"Failed to get grading curve {name}: {e}")
            raise ServiceError(f"Failed to retrieve grading curve: {e}")
    
    def get_by_type(self, grading_type: GradationType) -> List[Grading]:
        """Get grading curves by type."""
        try:
            with self.db_service.get_read_only_session() as session:
                return session.query(Grading).filter_by(type=grading_type.value).order_by(Grading.name).all()
        except Exception as e:
            self.logger.error(f"Failed to get grading curves by type {grading_type}: {e}")
            raise ServiceError(f"Failed to retrieve grading curves by type: {e}")
    
    def create(self, grading_data: GradingCreate) -> Grading:
        """Create a new grading curve."""
        try:
            with self.db_service.get_session() as session:
                # Check if grading already exists
                existing = session.query(Grading).filter_by(name=grading_data.name).first()
                if existing:
                    raise AlreadyExistsError(f"Grading curve '{grading_data.name}' already exists")
                
                grading = Grading(**grading_data.dict(exclude_unset=True))
                
                # Validate grading properties
                self._validate_grading(grading)
                
                session.add(grading)
                session.flush()  # Flush to get any database errors
                
                self.logger.info(f"Created grading curve: {grading.name}")
                return grading
                
        except AlreadyExistsError:
            raise
        except IntegrityError as e:
            self.logger.error(f"Database integrity error creating grading curve: {e}")
            raise ServiceError(f"Grading creation failed: invalid data")
        except Exception as e:
            self.logger.error(f"Failed to create grading curve: {e}")
            raise ServiceError(f"Failed to create grading curve: {e}")
    
    def update(self, name: str, grading_data: GradingUpdate) -> Grading:
        """Update an existing grading curve."""
        try:
            with self.db_service.get_session() as session:
                grading = session.query(Grading).filter_by(name=name).first()
                if not grading:
                    raise NotFoundError(f"Grading curve '{name}' not found")
                
                # Update fields
                update_dict = grading_data.dict(exclude_unset=True)
                for field, value in update_dict.items():
                    setattr(grading, field, value)
                
                # Validate updated grading
                self._validate_grading(grading)
                
                session.flush()  # Flush to get any database errors
                
                self.logger.info(f"Updated grading curve: {grading.name}")
                return grading
                
        except NotFoundError:
            raise
        except IntegrityError as e:
            self.logger.error(f"Database integrity error updating grading curve: {e}")
            raise ServiceError(f"Grading update failed: invalid data")
        except Exception as e:
            self.logger.error(f"Failed to update grading curve {name}: {e}")
            raise ServiceError(f"Failed to update grading curve: {e}")
    
    def delete(self, name: str) -> bool:
        """Delete a grading curve."""
        try:
            with self.db_service.get_session() as session:
                grading = session.query(Grading).filter_by(name=name).first()
                if not grading:
                    raise NotFoundError(f"Grading curve '{name}' not found")
                
                session.delete(grading)
                
                self.logger.info(f"Deleted grading curve: {name}")
                return True
                
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to delete grading curve {name}: {e}")
            raise ServiceError(f"Failed to delete grading curve: {e}")
    
    def _validate_grading(self, grading: Grading) -> None:
        """Validate grading curve properties."""
        # Validate required fields
        if not grading.name or not grading.name.strip():
            raise ValidationError("Grading name is required")
        
        # Validate type
        if grading.type not in [gt.value for gt in GradationType]:
            raise ValidationError(f"Invalid grading type: {grading.type}")
        
        # Validate max diameter
        if grading.max_diameter is not None and grading.max_diameter <= 0:
            raise ValidationError("Maximum diameter must be positive")
        
        # Validate grading data if present
        if grading.grading:
            try:
                grading_curve = self.parse_grading_data(grading.grading)
                self._validate_grading_curve_data(grading_curve)
            except Exception as e:
                raise ValidationError(f"Invalid grading data: {e}")
    
    def parse_grading_data(self, grading_bytes: bytes) -> GradingCurveData:
        """Parse binary grading data into structured format."""
        try:
            # Convert bytes to string
            grading_text = grading_bytes.decode('utf-8')
            
            # Parse tab-separated data
            lines = grading_text.strip().split('\n')
            
            # First line should be header: "Sieve\tDiam\tMass_frac"
            if not lines or 'Sieve' not in lines[0]:
                raise ValidationError("Invalid grading data format - missing header")
            
            sieves = []
            total_mass_fraction = 0.0
            
            for i, line in enumerate(lines[1:], 1):
                parts = line.strip().split('\t')
                if len(parts) < 3:
                    continue  # Skip incomplete lines
                
                try:
                    sieve_label = parts[0]
                    diameter_mm = float(parts[1])
                    mass_fraction = float(parts[2])
                    
                    # Convert mass fraction to mass retained for this sieve
                    mass_retained_g = mass_fraction * 1000  # Assume 1kg sample
                    mass_retained_percent = mass_fraction * 100
                    
                    sieve_result = SieveAnalysisResult(
                        sieve_size_mm=diameter_mm,
                        mass_retained_g=mass_retained_g,
                        mass_retained_percent=mass_retained_percent
                    )
                    
                    sieves.append(sieve_result)
                    total_mass_fraction += mass_fraction
                    
                except (ValueError, IndexError) as e:
                    self.logger.warning(f"Skipping invalid grading line {i}: {line} ({e})")
                    continue
            
            if not sieves:
                raise ValidationError("No valid sieve data found")
            
            # Sort sieves by size (largest first)
            sieves.sort(key=lambda s: s.sieve_size_mm, reverse=True)
            
            # Calculate cumulative values
            self._calculate_cumulative_values(sieves)
            
            # Determine grading type based on maximum size
            max_size = max(s.sieve_size_mm for s in sieves)
            grading_type = GradationType.COARSE if max_size > 4.75 else GradationType.FINE
            
            grading_curve = GradingCurveData(
                name="parsed_grading",
                grading_type=grading_type,
                sieves=sieves
            )
            
            return grading_curve
            
        except Exception as e:
            self.logger.error(f"Failed to parse grading data: {e}")
            raise ServiceError(f"Grading data parsing failed: {e}")
    
    def _calculate_cumulative_values(self, sieves: List[SieveAnalysisResult]) -> None:
        """Calculate cumulative retained and passing percentages."""
        cumulative_retained = 0.0
        
        for sieve in sieves:
            cumulative_retained += sieve.mass_retained_percent
            sieve.cumulative_retained_percent = cumulative_retained
            sieve.cumulative_passing_percent = 100.0 - cumulative_retained
    
    def _validate_grading_curve_data(self, grading_curve: GradingCurveData) -> None:
        """Validate grading curve data consistency."""
        if not grading_curve.sieves:
            raise ValidationError("Grading curve must have at least one sieve")
        
        # Check that cumulative passing decreases monotonically
        sorted_sieves = sorted(grading_curve.sieves, key=lambda s: s.sieve_size_mm, reverse=True)
        for i in range(1, len(sorted_sieves)):
            current_passing = sorted_sieves[i].cumulative_passing_percent
            previous_passing = sorted_sieves[i-1].cumulative_passing_percent
            
            if current_passing > previous_passing + 0.1:  # Allow small tolerance
                raise ValidationError(
                    f"Cumulative passing must decrease with sieve size: "
                    f"{sorted_sieves[i-1].sieve_size_mm}mm -> {sorted_sieves[i].sieve_size_mm}mm"
                )
        
        # Check final cumulative retained is approximately 100%
        final_retained = sorted_sieves[-1].cumulative_retained_percent
        if abs(final_retained - 100.0) > 5.0:  # Allow 5% tolerance
            raise ValidationError(f"Final cumulative retained should be ~100%, got {final_retained:.1f}%")
    
    def create_grading_from_sieve_analysis(self, name: str, grading_type: GradationType,
                                         sieve_results: List[SieveAnalysisResult]) -> Grading:
        """Create grading curve from sieve analysis results."""
        try:
            # Sort sieves by size (largest first)
            sorted_sieves = sorted(sieve_results, key=lambda s: s.sieve_size_mm, reverse=True)
            
            # Calculate cumulative values
            self._calculate_cumulative_values(sorted_sieves)
            
            # Create grading curve data
            grading_curve = GradingCurveData(
                name=name,
                grading_type=grading_type,
                sieves=sorted_sieves
            )
            
            # Validate the curve
            self._validate_grading_curve_data(grading_curve)
            
            # Convert to binary format
            grading_bytes = self._serialize_grading_data(grading_curve)
            
            # Create grading entity
            grading_create = GradingCreate(
                name=name,
                type=grading_type.value,
                grading=grading_bytes,
                max_diameter=grading_curve.max_particle_size
            )
            
            grading = self.create(grading_create)
            
            self.logger.info(f"Created grading from sieve analysis: {name}")
            return grading
            
        except Exception as e:
            self.logger.error(f"Failed to create grading from sieve analysis: {e}")
            raise ServiceError(f"Failed to create grading from sieve analysis: {e}")
    
    def _serialize_grading_data(self, grading_curve: GradingCurveData) -> bytes:
        """Serialize grading curve data to binary format."""
        try:
            # Create tab-separated text format
            output = io.StringIO()
            output.write("Sieve\tDiam\tMass_frac\n")
            
            for sieve in grading_curve.sieves:
                mass_fraction = sieve.mass_retained_percent / 100.0
                output.write(f"{sieve.sieve_size_mm:.3f}\t{sieve.sieve_size_mm:.3f}\t{mass_fraction:.6f}\n")
            
            grading_text = output.getvalue()
            return grading_text.encode('utf-8')
            
        except Exception as e:
            self.logger.error(f"Failed to serialize grading data: {e}")
            raise ServiceError(f"Grading serialization failed: {e}")
    
    def interpolate_grading_at_size(self, grading_name: str, target_size_mm: float) -> float:
        """Interpolate percent passing at a specific sieve size."""
        try:
            grading = self.get_by_name(grading_name)
            if not grading or not grading.grading:
                raise NotFoundError(f"Grading curve '{grading_name}' not found or has no data")
            
            grading_curve = self.parse_grading_data(grading.grading)
            
            # Sort sieves by size
            sorted_sieves = sorted(grading_curve.sieves, key=lambda s: s.sieve_size_mm)
            
            # Find bounding sieves
            for i in range(len(sorted_sieves) - 1):
                sieve1 = sorted_sieves[i]
                sieve2 = sorted_sieves[i + 1]
                
                if sieve1.sieve_size_mm <= target_size_mm <= sieve2.sieve_size_mm:
                    # Linear interpolation
                    size_ratio = (target_size_mm - sieve1.sieve_size_mm) / (sieve2.sieve_size_mm - sieve1.sieve_size_mm)
                    passing1 = sieve1.cumulative_passing_percent
                    passing2 = sieve2.cumulative_passing_percent
                    
                    interpolated_passing = passing1 + size_ratio * (passing2 - passing1)
                    return interpolated_passing
            
            # If target size is outside range, return boundary values
            if target_size_mm < sorted_sieves[0].sieve_size_mm:
                return sorted_sieves[0].cumulative_passing_percent
            else:
                return sorted_sieves[-1].cumulative_passing_percent
                
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to interpolate grading at size {target_size_mm}: {e}")
            raise ServiceError(f"Grading interpolation failed: {e}")
    
    def get_standard_sieves(self, standard: SieveStandard = SieveStandard.ASTM) -> List[float]:
        """Get standard sieve sizes for a given standard."""
        return self.standard_sieves.get(standard, []).copy()
    
    def calculate_grading_compliance(self, grading_name: str, 
                                   specification_limits: Dict[float, Tuple[float, float]]) -> Dict[str, Any]:
        """Check grading compliance against specification limits."""
        try:
            compliance_result = {
                'is_compliant': True,
                'violations': [],
                'warnings': [],
                'compliance_score': 0.0
            }
            
            total_checks = len(specification_limits)
            passed_checks = 0
            
            for sieve_size, (min_passing, max_passing) in specification_limits.items():
                actual_passing = self.interpolate_grading_at_size(grading_name, sieve_size)
                
                if min_passing <= actual_passing <= max_passing:
                    passed_checks += 1
                else:
                    compliance_result['is_compliant'] = False
                    violation = {
                        'sieve_size_mm': sieve_size,
                        'actual_passing': actual_passing,
                        'min_required': min_passing,
                        'max_allowed': max_passing
                    }
                    compliance_result['violations'].append(violation)
                
                # Check for warnings (within 5% of limits)
                if actual_passing < min_passing + 5 or actual_passing > max_passing - 5:
                    warning = {
                        'sieve_size_mm': sieve_size,
                        'actual_passing': actual_passing,
                        'message': 'Close to specification limit'
                    }
                    compliance_result['warnings'].append(warning)
            
            compliance_result['compliance_score'] = (passed_checks / total_checks * 100) if total_checks > 0 else 0
            
            return compliance_result
            
        except Exception as e:
            self.logger.error(f"Failed to calculate grading compliance: {e}")
            raise ServiceError(f"Grading compliance calculation failed: {e}")
    
    def get_grading_statistics(self) -> Dict[str, Any]:
        """Get statistics about grading curves."""
        try:
            with self.db_service.get_read_only_session() as session:
                total_count = session.query(Grading).count()
                
                if total_count == 0:
                    return {'total_gradings': 0}
                
                gradings = session.query(Grading).all()
                
                # Count by type
                fine_count = len([g for g in gradings if g.type == GradationType.FINE.value])
                coarse_count = len([g for g in gradings if g.type == GradationType.COARSE.value])
                
                # Calculate max diameter statistics
                max_diameters = [g.max_diameter for g in gradings if g.max_diameter is not None]
                avg_max_diameter = sum(max_diameters) / len(max_diameters) if max_diameters else 0
                
                # Count gradings with data
                with_grading_data = len([g for g in gradings if g.grading is not None])
                
                return {
                    'total_gradings': total_count,
                    'fine_gradings': fine_count,
                    'coarse_gradings': coarse_count,
                    'with_grading_data': with_grading_data,
                    'percentage_with_data': (with_grading_data / total_count * 100) if total_count > 0 else 0,
                    'average_max_diameter': round(avg_max_diameter, 2) if avg_max_diameter else None
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get grading statistics: {e}")
            raise ServiceError(f"Failed to get grading statistics: {e}")
    
    def search_gradings(self, query: str, grading_type: Optional[GradationType] = None,
                       limit: Optional[int] = None) -> List[Grading]:
        """Search grading curves by name with optional type filter."""
        try:
            with self.db_service.get_read_only_session() as session:
                search_query = session.query(Grading).filter(
                    Grading.name.contains(query)
                )
                
                if grading_type:
                    search_query = search_query.filter(Grading.type == grading_type.value)
                
                search_query = search_query.order_by(Grading.name)
                
                if limit:
                    search_query = search_query.limit(limit)
                
                return search_query.all()
                
        except Exception as e:
            self.logger.error(f"Failed to search grading curves: {e}")
            raise ServiceError(f"Failed to search grading curves: {e}")
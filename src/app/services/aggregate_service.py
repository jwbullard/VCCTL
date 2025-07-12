#!/usr/bin/env python3
"""
Aggregate Service for VCCTL

Provides business logic for aggregate material management and grading calculations.
Converted from Java Spring service to Python.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.exc import IntegrityError
from dataclasses import dataclass
from enum import Enum

from app.database.service import DatabaseService
from app.models.aggregate import Aggregate, AggregateCreate, AggregateUpdate, AggregateResponse
from app.models.grading import Grading
from app.models.aggregate_sieve import AggregateSieve
from app.services.base_service import BaseService, ServiceError, NotFoundError, AlreadyExistsError, ValidationError


class AggregateType(Enum):
    """Aggregate type enumeration."""
    FINE = "FINE"
    COARSE = "COARSE"


@dataclass
class SieveData:
    """Represents data for a single sieve in aggregate grading."""
    label: str
    diameter_mm: float
    mass_fraction_retained: float = 0.0
    mass_fraction_passing: float = 0.0
    
    def __post_init__(self):
        """Validate sieve data after initialization."""
        if self.diameter_mm <= 0:
            raise ValueError("Sieve diameter must be positive")
        if not (0 <= self.mass_fraction_retained <= 1):
            raise ValueError("Mass fraction retained must be between 0 and 1")
        if not (0 <= self.mass_fraction_passing <= 1):
            raise ValueError("Mass fraction passing must be between 0 and 1")


@dataclass
class GradingCurve:
    """Represents a complete grading curve for an aggregate."""
    name: str
    aggregate_type: AggregateType
    sieves: List[SieveData]
    max_diameter: float = 0.0
    fineness_modulus: float = 0.0
    
    def __post_init__(self):
        """Calculate derived properties after initialization."""
        if self.sieves:
            self.max_diameter = max(sieve.diameter_mm for sieve in self.sieves)
            self._calculate_fineness_modulus()
    
    def _calculate_fineness_modulus(self):
        """Calculate fineness modulus from grading curve."""
        # Standard sieves for fineness modulus (in mm)
        standard_sieves = [0.15, 0.30, 0.60, 1.18, 2.36, 4.75, 9.50, 19.0, 37.5]
        
        cumulative_retained = 0.0
        for sieve_size in standard_sieves:
            # Find closest sieve in our data
            closest_sieve = min(
                self.sieves,
                key=lambda s: abs(s.diameter_mm - sieve_size),
                default=None
            )
            
            if closest_sieve and abs(closest_sieve.diameter_mm - sieve_size) < sieve_size * 0.1:
                cumulative_retained += closest_sieve.mass_fraction_retained * 100
        
        self.fineness_modulus = cumulative_retained / 100.0


class AggregateService(BaseService[Aggregate, AggregateCreate, AggregateUpdate]):
    """
    Service for managing aggregate materials and their grading properties.
    
    Provides CRUD operations, grading curve management, and particle size
    distribution calculations for the VCCTL system.
    """
    
    def __init__(self, db_service: DatabaseService):
        super().__init__(Aggregate, db_service)
        self.logger = logging.getLogger('VCCTL.AggregateService')
        
        # Standard specific gravities by type
        self.default_specific_gravities = {
            AggregateType.FINE: 2.65,
            AggregateType.COARSE: 2.70
        }
    
    def get_all(self) -> List[Aggregate]:
        """Get all aggregate materials."""
        try:
            with self.db_service.get_read_only_session() as session:
                return session.query(Aggregate).order_by(Aggregate.name).all()
        except Exception as e:
            self.logger.error(f"Failed to get all aggregates: {e}")
            raise ServiceError(f"Failed to retrieve aggregates: {e}")
    
    def get_by_name(self, name: str) -> Optional[Aggregate]:
        """Get aggregate by name."""
        try:
            with self.db_service.get_read_only_session() as session:
                return session.query(Aggregate).filter_by(name=name).first()
        except Exception as e:
            self.logger.error(f"Failed to get aggregate {name}: {e}")
            raise ServiceError(f"Failed to retrieve aggregate: {e}")
    
    def get_by_type(self, aggregate_type: AggregateType) -> List[Aggregate]:
        """Get aggregates by type (fine or coarse)."""
        try:
            type_value = 0 if aggregate_type == AggregateType.FINE else 1
            with self.db_service.get_read_only_session() as session:
                return session.query(Aggregate).filter_by(type=type_value).order_by(Aggregate.name).all()
        except Exception as e:
            self.logger.error(f"Failed to get aggregates by type {aggregate_type}: {e}")
            raise ServiceError(f"Failed to retrieve aggregates by type: {e}")
    
    def create(self, aggregate_data: AggregateCreate) -> Aggregate:
        """Create a new aggregate material."""
        try:
            with self.db_service.get_session() as session:
                # Check if aggregate already exists
                existing = session.query(Aggregate).filter_by(name=aggregate_data.name).first()
                if existing:
                    raise AlreadyExistsError(f"Aggregate '{aggregate_data.name}' already exists")
                
                # Create aggregate with defaults
                aggregate_dict = aggregate_data.dict(exclude_unset=True)
                
                # Set default specific gravity if not provided
                if 'specific_gravity' not in aggregate_dict:
                    agg_type = AggregateType.FINE if aggregate_dict.get('type', 0) == 0 else AggregateType.COARSE
                    aggregate_dict['specific_gravity'] = self.default_specific_gravities[agg_type]
                
                aggregate = Aggregate(**aggregate_dict)
                
                # Validate aggregate properties
                self._validate_aggregate(aggregate)
                
                session.add(aggregate)
                session.flush()  # Flush to get any database errors
                
                self.logger.info(f"Created aggregate: {aggregate.name}")
                return aggregate
                
        except AlreadyExistsError:
            raise
        except IntegrityError as e:
            self.logger.error(f"Database integrity error creating aggregate: {e}")
            raise ServiceError(f"Aggregate creation failed: invalid data")
        except Exception as e:
            self.logger.error(f"Failed to create aggregate: {e}")
            raise ServiceError(f"Failed to create aggregate: {e}")
    
    def update(self, name: str, aggregate_data: AggregateUpdate) -> Aggregate:
        """Update an existing aggregate material."""
        try:
            with self.db_service.get_session() as session:
                aggregate = session.query(Aggregate).filter_by(name=name).first()
                if not aggregate:
                    raise NotFoundError(f"Aggregate '{name}' not found")
                
                # Update fields
                update_dict = aggregate_data.dict(exclude_unset=True)
                for field, value in update_dict.items():
                    setattr(aggregate, field, value)
                
                # Validate updated aggregate
                self._validate_aggregate(aggregate)
                
                session.flush()  # Flush to get any database errors
                
                self.logger.info(f"Updated aggregate: {aggregate.name}")
                return aggregate
                
        except NotFoundError:
            raise
        except IntegrityError as e:
            self.logger.error(f"Database integrity error updating aggregate: {e}")
            raise ServiceError(f"Aggregate update failed: invalid data")
        except Exception as e:
            self.logger.error(f"Failed to update aggregate {name}: {e}")
            raise ServiceError(f"Failed to update aggregate: {e}")
    
    def delete(self, name: str) -> bool:
        """Delete an aggregate material."""
        try:
            with self.db_service.get_session() as session:
                aggregate = session.query(Aggregate).filter_by(name=name).first()
                if not aggregate:
                    raise NotFoundError(f"Aggregate '{name}' not found")
                
                session.delete(aggregate)
                
                self.logger.info(f"Deleted aggregate: {name}")
                return True
                
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to delete aggregate {name}: {e}")
            raise ServiceError(f"Failed to delete aggregate: {e}")
    
    def _validate_aggregate(self, aggregate: Aggregate) -> None:
        """Validate aggregate properties."""
        # Validate required fields
        if not aggregate.name or not aggregate.name.strip():
            raise ValidationError("Aggregate name is required")
        
        # Validate type
        if aggregate.type not in [0, 1]:  # 0=FINE, 1=COARSE
            raise ValidationError("Aggregate type must be 0 (FINE) or 1 (COARSE)")
        
        # Validate specific gravity
        if aggregate.specific_gravity is not None:
            if aggregate.specific_gravity <= 0 or aggregate.specific_gravity > 5.0:
                raise ValidationError("Specific gravity must be positive and reasonable (<5.0)")
        
        # Validate mechanical properties if provided
        if aggregate.bulk_modulus is not None and aggregate.bulk_modulus < 0:
            raise ValidationError("Bulk modulus cannot be negative")
        
        if aggregate.shear_modulus is not None and aggregate.shear_modulus < 0:
            raise ValidationError("Shear modulus cannot be negative")
        
        if aggregate.conductivity is not None and aggregate.conductivity < 0:
            raise ValidationError("Conductivity cannot be negative")
    
    def create_grading_curve(self, aggregate_name: str, grading_name: str, 
                           sieve_data: List[Dict[str, Any]]) -> GradingCurve:
        """Create a grading curve for an aggregate."""
        try:
            # Get the aggregate
            aggregate = self.get_by_name(aggregate_name)
            if not aggregate:
                raise NotFoundError(f"Aggregate '{aggregate_name}' not found")
            
            # Determine aggregate type
            agg_type = AggregateType.FINE if aggregate.type == 0 else AggregateType.COARSE
            
            # Process sieve data
            sieves = []
            for sieve_info in sieve_data:
                sieve = SieveData(
                    label=sieve_info['label'],
                    diameter_mm=sieve_info['diameter_mm'],
                    mass_fraction_retained=sieve_info.get('mass_fraction_retained', 0.0),
                    mass_fraction_passing=sieve_info.get('mass_fraction_passing', 0.0)
                )
                sieves.append(sieve)
            
            # Sort sieves by diameter (largest to smallest)
            sieves.sort(key=lambda s: s.diameter_mm, reverse=True)
            
            # Calculate cumulative passing fractions
            self._calculate_cumulative_passing(sieves)
            
            # Create grading curve
            grading_curve = GradingCurve(
                name=grading_name,
                aggregate_type=agg_type,
                sieves=sieves
            )
            
            # Validate grading curve
            self._validate_grading_curve(grading_curve)
            
            self.logger.info(f"Created grading curve '{grading_name}' for aggregate '{aggregate_name}'")
            return grading_curve
            
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Failed to create grading curve: {e}")
            raise ServiceError(f"Failed to create grading curve: {e}")
    
    def _calculate_cumulative_passing(self, sieves: List[SieveData]) -> None:
        """Calculate cumulative passing fractions from retained fractions."""
        # Sort by diameter (largest to smallest)
        sieves.sort(key=lambda s: s.diameter_mm, reverse=True)
        
        cumulative_retained = 0.0
        for sieve in sieves:
            cumulative_retained += sieve.mass_fraction_retained
            sieve.mass_fraction_passing = 1.0 - cumulative_retained
            
            # Ensure passing fraction is not negative
            sieve.mass_fraction_passing = max(0.0, sieve.mass_fraction_passing)
    
    def _validate_grading_curve(self, grading_curve: GradingCurve) -> None:
        """Validate a grading curve."""
        if not grading_curve.sieves:
            raise ValidationError("Grading curve must have at least one sieve")
        
        # Check that retained fractions sum to approximately 1.0
        total_retained = sum(sieve.mass_fraction_retained for sieve in grading_curve.sieves)
        if abs(total_retained - 1.0) > 0.05:  # Allow 5% tolerance
            raise ValidationError(f"Total retained fractions should sum to 1.0, got {total_retained:.3f}")
        
        # Check that passing fractions are monotonically decreasing
        sorted_sieves = sorted(grading_curve.sieves, key=lambda s: s.diameter_mm, reverse=True)
        for i in range(1, len(sorted_sieves)):
            if sorted_sieves[i].mass_fraction_passing > sorted_sieves[i-1].mass_fraction_passing:
                raise ValidationError("Passing fractions must decrease with decreasing sieve size")
    
    def calculate_particle_size_statistics(self, grading_curve: GradingCurve) -> Dict[str, float]:
        """Calculate particle size statistics from grading curve."""
        try:
            if not grading_curve.sieves:
                return {}
            
            # Sort sieves by diameter
            sorted_sieves = sorted(grading_curve.sieves, key=lambda s: s.diameter_mm)
            
            # Calculate D10, D30, D50, D60 (particle sizes at 10%, 30%, 50%, 60% passing)
            percentiles = [0.10, 0.30, 0.50, 0.60]
            d_values = {}
            
            for percentile in percentiles:
                d_value = self._interpolate_diameter_at_passing(sorted_sieves, percentile)
                d_values[f"D{int(percentile*100)}"] = d_value
            
            # Calculate uniformity coefficient (Cu = D60/D10)
            cu = d_values["D60"] / d_values["D10"] if d_values["D10"] > 0 else 0
            
            # Calculate coefficient of curvature (Cc = (D30)²/(D10*D60))
            cc = (d_values["D30"]**2) / (d_values["D10"] * d_values["D60"]) if (d_values["D10"] * d_values["D60"]) > 0 else 0
            
            statistics = {
                **d_values,
                "uniformity_coefficient": cu,
                "coefficient_of_curvature": cc,
                "fineness_modulus": grading_curve.fineness_modulus,
                "max_diameter": grading_curve.max_diameter
            }
            
            return statistics
            
        except Exception as e:
            self.logger.error(f"Failed to calculate particle size statistics: {e}")
            raise ServiceError(f"Failed to calculate statistics: {e}")
    
    def _interpolate_diameter_at_passing(self, sorted_sieves: List[SieveData], target_passing: float) -> float:
        """Interpolate diameter at specific passing percentage."""
        # Find the two sieves that bracket the target passing percentage
        for i in range(len(sorted_sieves) - 1):
            sieve1 = sorted_sieves[i]
            sieve2 = sorted_sieves[i + 1]
            
            if sieve1.mass_fraction_passing >= target_passing >= sieve2.mass_fraction_passing:
                # Linear interpolation between the two points
                if sieve1.mass_fraction_passing == sieve2.mass_fraction_passing:
                    return sieve1.diameter_mm
                
                t = (target_passing - sieve2.mass_fraction_passing) / (sieve1.mass_fraction_passing - sieve2.mass_fraction_passing)
                return sieve2.diameter_mm + t * (sieve1.diameter_mm - sieve2.diameter_mm)
        
        # If not found, return boundary values
        if target_passing > sorted_sieves[0].mass_fraction_passing:
            return sorted_sieves[0].diameter_mm
        else:
            return sorted_sieves[-1].diameter_mm
    
    def get_aggregate_statistics(self) -> Dict[str, Any]:
        """Get statistics about aggregate materials."""
        try:
            with self.db_service.get_read_only_session() as session:
                total_count = session.query(Aggregate).count()
                
                if total_count == 0:
                    return {'total_aggregates': 0}
                
                aggregates = session.query(Aggregate).all()
                
                # Count by type
                fine_count = len([a for a in aggregates if a.type == 0])
                coarse_count = len([a for a in aggregates if a.type == 1])
                
                # Calculate specific gravity statistics
                specific_gravities = [a.specific_gravity for a in aggregates if a.specific_gravity is not None]
                avg_specific_gravity = sum(specific_gravities) / len(specific_gravities) if specific_gravities else 0
                min_specific_gravity = min(specific_gravities) if specific_gravities else 0
                max_specific_gravity = max(specific_gravities) if specific_gravities else 0
                
                # Count aggregates with mechanical properties
                with_bulk_modulus = len([a for a in aggregates if a.bulk_modulus is not None])
                with_shear_modulus = len([a for a in aggregates if a.shear_modulus is not None])
                
                return {
                    'total_aggregates': total_count,
                    'fine_aggregates': fine_count,
                    'coarse_aggregates': coarse_count,
                    'average_specific_gravity': round(avg_specific_gravity, 3) if avg_specific_gravity else None,
                    'min_specific_gravity': min_specific_gravity,
                    'max_specific_gravity': max_specific_gravity,
                    'with_bulk_modulus': with_bulk_modulus,
                    'with_shear_modulus': with_shear_modulus,
                    'percentage_with_mechanical_properties': (with_bulk_modulus / total_count * 100) if total_count > 0 else 0
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get aggregate statistics: {e}")
            raise ServiceError(f"Failed to get aggregate statistics: {e}")
    
    def search_aggregates(self, query: str, aggregate_type: Optional[AggregateType] = None, 
                         limit: Optional[int] = None) -> List[Aggregate]:
        """Search aggregates by name with optional type filter."""
        try:
            with self.db_service.get_read_only_session() as session:
                search_query = session.query(Aggregate).filter(
                    Aggregate.name.contains(query)
                )
                
                if aggregate_type:
                    type_value = 0 if aggregate_type == AggregateType.FINE else 1
                    search_query = search_query.filter(Aggregate.type == type_value)
                
                search_query = search_query.order_by(Aggregate.name)
                
                if limit:
                    search_query = search_query.limit(limit)
                
                return search_query.all()
                
        except Exception as e:
            self.logger.error(f"Failed to search aggregates: {e}")
            raise ServiceError(f"Failed to search aggregates: {e}")
    
    def validate_for_concrete_mix(self, aggregate_name: str, grading_curve: Optional[GradingCurve] = None) -> Dict[str, Any]:
        """Validate aggregate suitability for concrete mix design."""
        try:
            aggregate = self.get_by_name(aggregate_name)
            if not aggregate:
                raise NotFoundError(f"Aggregate '{aggregate_name}' not found")
            
            validation_result = {
                'is_suitable': True,
                'warnings': [],
                'recommendations': [],
                'suitability_score': 0.0
            }
            
            score = 100.0  # Start with perfect score
            
            # Check specific gravity
            if aggregate.specific_gravity:
                if aggregate.specific_gravity < 2.3 or aggregate.specific_gravity > 3.0:
                    validation_result['warnings'].append("Specific gravity outside typical range (2.3-3.0)")
                    score -= 10
            else:
                validation_result['warnings'].append("No specific gravity data available")
                score -= 5
            
            # Check mechanical properties
            if aggregate.bulk_modulus is None or aggregate.shear_modulus is None:
                validation_result['warnings'].append("Incomplete mechanical property data")
                score -= 5
            
            # Validate grading curve if provided
            if grading_curve:
                try:
                    self._validate_grading_curve(grading_curve)
                    stats = self.calculate_particle_size_statistics(grading_curve)
                    
                    # Check fineness modulus for fine aggregates
                    if aggregate.type == 0:  # Fine aggregate
                        fm = stats.get('fineness_modulus', 0)
                        if fm < 2.3 or fm > 3.1:
                            validation_result['warnings'].append(f"Fineness modulus ({fm:.2f}) outside recommended range (2.3-3.1)")
                            score -= 15
                    
                    # Check uniformity coefficient
                    cu = stats.get('uniformity_coefficient', 0)
                    if cu < 4:
                        validation_result['warnings'].append("Low uniformity coefficient - may indicate poor gradation")
                        score -= 10
                    elif cu > 15:
                        validation_result['warnings'].append("High uniformity coefficient - may indicate gap gradation")
                        score -= 5
                    
                except ValidationError as ve:
                    validation_result['warnings'].append(f"Grading curve validation failed: {ve}")
                    score -= 20
            
            validation_result['suitability_score'] = max(0.0, min(100.0, score))
            
            if score < 60:
                validation_result['is_suitable'] = False
            
            return validation_result
            
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to validate aggregate for concrete mix: {e}")
            raise ServiceError(f"Failed to validate aggregate: {e}")
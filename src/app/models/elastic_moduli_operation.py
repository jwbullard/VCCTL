#!/usr/bin/env python3
"""
Elastic Moduli Operation Model

Database model for elastic moduli calculations that take hydrated microstructures
as input and calculate mechanical properties.
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Dict, Any, Optional

from app.database.base import Base
from app.models.operation import Operation


class ElasticModuliOperation(Base):
    """Database model for elastic moduli operations."""
    
    __tablename__ = 'elastic_moduli_operations'
    
    # Primary key
    id = Column(Integer, primary_key=True)
    
    # Basic operation information
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Dependencies - requires a completed hydration operation
    hydration_operation_id = Column(Integer, ForeignKey('operations.id'), nullable=False)
    hydration_operation = relationship("Operation", foreign_keys=[hydration_operation_id])
    
    # Input parameters
    image_filename = Column(String(255), nullable=False)  # Hydrated microstructure image
    early_age_connection = Column(Integer, default=1)     # Always 1 according to Java code
    has_itz = Column(Boolean, default=False)              # ITZ (aggregate present)
    output_directory = Column(String(500), nullable=False)
    pimg_file_path = Column(String(500))                  # Path to .pimg file
    
    # Aggregate properties (simplified to max 1 fine + 1 coarse)
    # Fine aggregate
    has_fine_aggregate = Column(Boolean, default=False)
    fine_aggregate_volume_fraction = Column(Float)
    fine_aggregate_grading_path = Column(String(500))
    fine_aggregate_bulk_modulus = Column(Float)
    fine_aggregate_shear_modulus = Column(Float)
    fine_aggregate_display_name = Column(String(255))
    
    # Coarse aggregate  
    has_coarse_aggregate = Column(Boolean, default=False)
    coarse_aggregate_volume_fraction = Column(Float)
    coarse_aggregate_grading_path = Column(String(500))
    coarse_aggregate_bulk_modulus = Column(Float)
    coarse_aggregate_shear_modulus = Column(Float)
    coarse_aggregate_display_name = Column(String(255))
    
    # Air content
    air_volume_fraction = Column(Float, default=0.0)
    
    # Execution tracking
    status = Column(String(50), default='pending')  # pending, running, completed, failed
    progress = Column(Float, default=0.0)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    error_message = Column(Text)
    
    # Generated files tracking
    input_file_path = Column(String(500))        # elastic.in
    output_file_path = Column(String(500))       # elastic.out
    effective_moduli_file = Column(String(500))  # EffectiveModuli.dat
    phase_contributions_file = Column(String(500))  # PhaseContributions.dat
    itz_moduli_file = Column(String(500))        # ITZModuli.dat
    concrete_moduli_file = Column(String(500))   # Concrete.dat
    
    def __init__(self, **kwargs):
        """Initialize an elastic moduli operation."""
        super().__init__(**kwargs)
        if not self.created_at:
            self.created_at = datetime.utcnow()
        if not self.updated_at:
            self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'hydration_operation_id': self.hydration_operation_id,
            'image_filename': self.image_filename,
            'early_age_connection': self.early_age_connection,
            'has_itz': self.has_itz,
            'output_directory': self.output_directory,
            'pimg_file_path': self.pimg_file_path,
            'has_fine_aggregate': self.has_fine_aggregate,
            'fine_aggregate_volume_fraction': self.fine_aggregate_volume_fraction,
            'fine_aggregate_grading_path': self.fine_aggregate_grading_path,
            'fine_aggregate_bulk_modulus': self.fine_aggregate_bulk_modulus,
            'fine_aggregate_shear_modulus': self.fine_aggregate_shear_modulus,
            'fine_aggregate_display_name': self.fine_aggregate_display_name,
            'has_coarse_aggregate': self.has_coarse_aggregate,
            'coarse_aggregate_volume_fraction': self.coarse_aggregate_volume_fraction,
            'coarse_aggregate_grading_path': self.coarse_aggregate_grading_path,
            'coarse_aggregate_bulk_modulus': self.coarse_aggregate_bulk_modulus,
            'coarse_aggregate_shear_modulus': self.coarse_aggregate_shear_modulus,
            'coarse_aggregate_display_name': self.coarse_aggregate_display_name,
            'air_volume_fraction': self.air_volume_fraction,
            'status': self.status,
            'progress': self.progress,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'error_message': self.error_message,
            'input_file_path': self.input_file_path,
            'output_file_path': self.output_file_path,
            'effective_moduli_file': self.effective_moduli_file,
            'phase_contributions_file': self.phase_contributions_file,
            'itz_moduli_file': self.itz_moduli_file,
            'concrete_moduli_file': self.concrete_moduli_file
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ElasticModuliOperation':
        """Create instance from dictionary."""
        # Handle datetime fields
        for field in ['created_at', 'updated_at', 'start_time', 'end_time']:
            if field in data and data[field]:
                if isinstance(data[field], str):
                    data[field] = datetime.fromisoformat(data[field])
        
        return cls(**data)
    
    def get_expected_output_files(self) -> Dict[str, str]:
        """Get expected output file names for this operation."""
        base_name = self.name.replace(' ', '_')
        return {
            'input_file': f'{base_name}_elastic.in',
            'output_file': f'{base_name}_elastic.out', 
            'effective_moduli': f'{base_name}_EffectiveModuli.dat',
            'phase_contributions': f'{base_name}_PhaseContributions.dat',
            'itz_moduli': f'{base_name}_ITZModuli.dat',
            'concrete_moduli': f'{base_name}_Concrete.dat'
        }
    
    def update_progress(self, progress: float, status: Optional[str] = None):
        """Update operation progress."""
        self.progress = max(0.0, min(1.0, progress))
        if status:
            self.status = status
        self.updated_at = datetime.utcnow()
        
        # Set timing
        if status == 'running' and not self.start_time:
            self.start_time = datetime.utcnow()
        elif status in ['completed', 'failed'] and not self.end_time:
            self.end_time = datetime.utcnow()
    
    def mark_completed(self):
        """Mark operation as completed."""
        self.status = 'completed'
        self.progress = 1.0
        self.end_time = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def mark_failed(self, error_message: str):
        """Mark operation as failed with error message."""
        self.status = 'failed'
        self.error_message = error_message
        self.end_time = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def __repr__(self):
        return f"<ElasticModuliOperation(id={self.id}, name='{self.name}', status='{self.status}')>"
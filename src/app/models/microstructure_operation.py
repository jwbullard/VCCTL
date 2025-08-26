#!/usr/bin/env python3
"""
Microstructure Operation Model

Database model for microstructure generation operations that stores ALL user input data
for complete traceability and lineage tracking.
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Dict, Any, Optional

from app.database.base import Base


class MicrostructureOperation(Base):
    """Database model for microstructure generation operations with complete input storage."""
    
    __tablename__ = 'microstructure_operations'
    
    # Primary key
    id = Column(Integer, primary_key=True)
    
    # Foreign key to general operation (one-to-one relationship)
    operation_id = Column(Integer, ForeignKey('operations.id'), unique=True, nullable=False)
    operation = relationship("Operation", foreign_keys=[operation_id])
    
    # Foreign key to mix design (stores component specifications)
    mix_design_id = Column(Integer, ForeignKey('mix_design.id'), nullable=False)
    mix_design = relationship("MixDesign", foreign_keys=[mix_design_id])
    
    # Basic operation information
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # System dimensions (can be different for X, Y, Z)
    system_size_x = Column(Integer, nullable=False, default=100)
    system_size_y = Column(Integer, nullable=False, default=100)  
    system_size_z = Column(Integer, nullable=False, default=100)
    system_size = Column(Integer, nullable=False, default=100)  # Backward compatibility
    
    # Resolution for microstructure generation (micrometers per voxel)
    resolution = Column(Float, nullable=False, default=1.0)
    
    # Random seed for reproducibility
    random_seed = Column(Integer, nullable=False, default=-1)
    
    # Particle shape settings
    cement_shape_set = Column(String(64), nullable=True, default="spherical")
    fine_aggregate_shape_set = Column(String(64), nullable=True, default="spherical")
    coarse_aggregate_shape_set = Column(String(64), nullable=True, default="spherical") 
    aggregate_shape_set = Column(String(64), nullable=True, default="spherical")  # Backward compatibility
    
    # Flocculation parameters
    flocculation_enabled = Column(Boolean, nullable=False, default=False)
    flocculation_degree = Column(Float, nullable=False, default=0.0)
    
    # Dispersion parameters  
    dispersion_factor = Column(Integer, nullable=False, default=0)
    
    # genmic-specific parameters
    genmic_mode = Column(Integer, nullable=False, default=2)  # Usually 2 for 3D
    particle_shape_directory = Column(String(500), nullable=True, default="../../particle_shape_set/")
    
    # Output file specifications
    output_img_filename = Column(String(255), nullable=False)  # .img file
    output_pimg_filename = Column(String(255), nullable=False)  # .pimg file  
    output_directory = Column(String(500), nullable=False)
    
    # Execution tracking
    status = Column(String(50), default='pending')  # pending, running, completed, failed
    progress = Column(Float, default=0.0)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    error_message = Column(Text)
    
    # Generated files tracking
    genmic_input_file = Column(String(500))    # genmic_input_*.txt
    genmic_progress_file = Column(String(500)) # genmic_progress.txt
    stdout_log_file = Column(String(500))      # proc_*_stdout.txt
    stderr_log_file = Column(String(500))      # proc_*_stderr.txt
    
    def __init__(self, **kwargs):
        """Initialize a microstructure operation."""
        super().__init__(**kwargs)
        if not self.created_at:
            self.created_at = datetime.utcnow()
        if not self.updated_at:
            self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'id': self.id,
            'operation_id': self.operation_id,
            'mix_design_id': self.mix_design_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'system_size_x': self.system_size_x,
            'system_size_y': self.system_size_y,
            'system_size_z': self.system_size_z,
            'system_size': self.system_size,
            'resolution': self.resolution,
            'random_seed': self.random_seed,
            'cement_shape_set': self.cement_shape_set,
            'fine_aggregate_shape_set': self.fine_aggregate_shape_set,
            'coarse_aggregate_shape_set': self.coarse_aggregate_shape_set,
            'aggregate_shape_set': self.aggregate_shape_set,
            'flocculation_enabled': self.flocculation_enabled,
            'flocculation_degree': self.flocculation_degree,
            'dispersion_factor': self.dispersion_factor,
            'genmic_mode': self.genmic_mode,
            'particle_shape_directory': self.particle_shape_directory,
            'output_img_filename': self.output_img_filename,
            'output_pimg_filename': self.output_pimg_filename,
            'output_directory': self.output_directory,
            'status': self.status,
            'progress': self.progress,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'error_message': self.error_message,
            'genmic_input_file': self.genmic_input_file,
            'genmic_progress_file': self.genmic_progress_file,
            'stdout_log_file': self.stdout_log_file,
            'stderr_log_file': self.stderr_log_file
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MicrostructureOperation':
        """Create instance from dictionary."""
        # Handle datetime fields
        for field in ['created_at', 'updated_at', 'start_time', 'end_time']:
            if field in data and data[field]:
                if isinstance(data[field], str):
                    data[field] = datetime.fromisoformat(data[field])
        
        return cls(**data)
    
    def get_expected_output_files(self) -> Dict[str, str]:
        """Get expected output file names for this operation."""
        return {
            'img_file': self.output_img_filename,
            'pimg_file': self.output_pimg_filename,
            'genmic_input': f'genmic_input_{self.operation.name.replace(" Microstructure", "")}.txt',
            'genmic_progress': 'genmic_progress.txt',
            'stdout_log': f'proc_{self.operation.name}_stdout.txt',
            'stderr_log': f'proc_{self.operation.name}_stderr.txt'
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
    
    @property
    def aggregate_specifications(self) -> Dict[str, Any]:
        """Get aggregate specifications from linked mix design."""
        if not self.mix_design:
            return {}
            
        specs = {
            'air_volume_fraction': self.mix_design.air_volume_fraction,
            'fine_aggregates': [],
            'coarse_aggregates': []
        }
        
        # Extract aggregate components from mix design
        if self.mix_design.components:
            for component in self.mix_design.components:
                if component.get('material_type') == 'aggregate':
                    # Classify as fine or coarse based on material name or other criteria
                    material_name = component.get('material_name', '').lower()
                    agg_spec = {
                        'material_name': component.get('material_name'),
                        'volume_fraction': component.get('volume_fraction', 0.0),
                        'mass_fraction': component.get('mass_fraction', 0.0),
                        'specific_gravity': component.get('specific_gravity', 2.65)
                    }
                    
                    # Simple classification: if name contains 'fine' or 'sand', it's fine aggregate
                    if 'fine' in material_name or 'sand' in material_name:
                        specs['fine_aggregates'].append(agg_spec)
                    else:
                        specs['coarse_aggregates'].append(agg_spec)
        
        return specs
    
    def __repr__(self):
        return f"<MicrostructureOperation(id={self.id}, operation='{self.operation.name if self.operation else None}', status='{self.status}')>"
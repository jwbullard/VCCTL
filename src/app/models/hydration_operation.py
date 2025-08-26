#!/usr/bin/env python3
"""
Hydration Operation Model

Database model for hydration simulation operations that stores ALL user input data
for complete traceability and lineage tracking.
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Dict, Any, Optional

from app.database.base import Base


class HydrationOperation(Base):
    """Database model for hydration simulation operations with complete input storage."""
    
    __tablename__ = 'hydration_operations'
    
    # Primary key
    id = Column(Integer, primary_key=True)
    
    # Foreign key to general operation (one-to-one relationship)
    operation_id = Column(Integer, ForeignKey('operations.id'), unique=True, nullable=False)
    operation = relationship("Operation", foreign_keys=[operation_id])
    
    # Foreign key to source microstructure operation (lineage tracking)
    microstructure_operation_id = Column(Integer, ForeignKey('operations.id'), nullable=False)
    source_microstructure_operation = relationship("Operation", foreign_keys=[microstructure_operation_id])
    
    # Foreign key to hydration parameters
    hydration_parameter_set_id = Column(Integer, ForeignKey('hydration_parameter_sets.id'), nullable=False)
    hydration_parameter_set = relationship("HydrationParameterSet", foreign_keys=[hydration_parameter_set_id])
    
    # Foreign key to temperature profile
    temperature_profile_id = Column(Integer, ForeignKey('temperature_profiles.id'), nullable=True)
    temperature_profile = relationship("TemperatureProfileDB", foreign_keys=[temperature_profile_id])
    
    # Basic operation information
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Input microstructure files
    input_img_file = Column(String(500), nullable=False)  # Source .img file
    input_pimg_file = Column(String(500), nullable=False)  # Source .pimg file
    microstructure_directory = Column(String(500), nullable=False)  # Source directory
    
    # Simulation parameters
    max_simulation_time = Column(Float, nullable=False, default=168.0)  # hours
    target_degree_of_hydration = Column(Float, nullable=False, default=0.8)  # 0.0-1.0
    random_seed = Column(Integer, nullable=False, default=-1)
    
    # disrealnew-specific parameters
    working_directory = Column(String(500), nullable=False)
    output_base_name = Column(String(255), nullable=False)  # Base name for output files
    
    # Advanced hydration settings
    c3a_fraction = Column(Float, nullable=False, default=0.0)  # Orthorhombic C3A fraction
    aging_mode = Column(Integer, nullable=False, default=0)  # 0=normal, 1=early age
    auto_stop_enabled = Column(Boolean, nullable=False, default=True)
    ch_flag_enabled = Column(Boolean, nullable=False, default=True)  # CH precipitation
    csh2_flag_enabled = Column(Boolean, nullable=False, default=True)  # CSH2 formation
    ettringite_enabled = Column(Boolean, nullable=False, default=True)  # Ettringite formation
    ph_active = Column(Boolean, nullable=False, default=True)  # pH tracking
    dissolution_bias = Column(Float, nullable=False, default=1.0)  # Dissolution bias factor
    growth_probability = Column(Float, nullable=False, default=1.0)  # Growth probability
    time_conversion_factor = Column(Float, nullable=False, default=1.0)  # Time scaling
    
    # Temperature settings
    use_temperature_profile = Column(Boolean, nullable=False, default=False)
    constant_temperature = Column(Float, nullable=False, default=25.0)  # Celsius
    
    # Output settings
    output_time_frequency = Column(Integer, nullable=False, default=50)  # Cycles between outputs
    save_time_history = Column(Boolean, nullable=False, default=True)
    save_phase_evolution = Column(Boolean, nullable=False, default=True)
    save_microstructure_snapshots = Column(Boolean, nullable=False, default=True)
    
    # Execution tracking
    status = Column(String(50), default='pending')  # pending, running, completed, failed
    progress = Column(Float, default=0.0)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    error_message = Column(Text)
    
    # Generated files tracking
    extended_parameter_file = Column(String(500))    # *_extended_parameters.csv
    alkali_char_file = Column(String(500))           # alkalichar.dat
    slag_char_file = Column(String(500))             # slagchar.dat
    alkaliflyash_file = Column(String(500))          # alkaliflyash.dat (if applicable)
    progress_json_file = Column(String(500))         # progress.json
    time_history_file = Column(String(500))          # time_history.csv
    final_csv_file = Column(String(500))             # HydrationOf_*.csv
    final_img_file = Column(String(500))             # HydrationOf_*.img.*.*
    final_phr_file = Column(String(500))             # HydrationOf_*.phr.*.*
    final_poredist_file = Column(String(500))        # HydrationOf_*.img.*.*.poredist
    
    def __init__(self, **kwargs):
        """Initialize a hydration operation."""
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
            'microstructure_operation_id': self.microstructure_operation_id,
            'hydration_parameter_set_id': self.hydration_parameter_set_id,
            'temperature_profile_id': self.temperature_profile_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'input_img_file': self.input_img_file,
            'input_pimg_file': self.input_pimg_file,
            'microstructure_directory': self.microstructure_directory,
            'max_simulation_time': self.max_simulation_time,
            'target_degree_of_hydration': self.target_degree_of_hydration,
            'random_seed': self.random_seed,
            'working_directory': self.working_directory,
            'output_base_name': self.output_base_name,
            'c3a_fraction': self.c3a_fraction,
            'aging_mode': self.aging_mode,
            'auto_stop_enabled': self.auto_stop_enabled,
            'ch_flag_enabled': self.ch_flag_enabled,
            'csh2_flag_enabled': self.csh2_flag_enabled,
            'ettringite_enabled': self.ettringite_enabled,
            'ph_active': self.ph_active,
            'dissolution_bias': self.dissolution_bias,
            'growth_probability': self.growth_probability,
            'time_conversion_factor': self.time_conversion_factor,
            'use_temperature_profile': self.use_temperature_profile,
            'constant_temperature': self.constant_temperature,
            'output_time_frequency': self.output_time_frequency,
            'save_time_history': self.save_time_history,
            'save_phase_evolution': self.save_phase_evolution,
            'save_microstructure_snapshots': self.save_microstructure_snapshots,
            'status': self.status,
            'progress': self.progress,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'error_message': self.error_message,
            'extended_parameter_file': self.extended_parameter_file,
            'alkali_char_file': self.alkali_char_file,
            'slag_char_file': self.slag_char_file,
            'alkaliflyash_file': self.alkaliflyash_file,
            'progress_json_file': self.progress_json_file,
            'time_history_file': self.time_history_file,
            'final_csv_file': self.final_csv_file,
            'final_img_file': self.final_img_file,
            'final_phr_file': self.final_phr_file,
            'final_poredist_file': self.final_poredist_file
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HydrationOperation':
        """Create instance from dictionary."""
        # Handle datetime fields
        for field in ['created_at', 'updated_at', 'start_time', 'end_time']:
            if field in data and data[field]:
                if isinstance(data[field], str):
                    data[field] = datetime.fromisoformat(data[field])
        
        return cls(**data)
    
    def get_expected_output_files(self) -> Dict[str, str]:
        """Get expected output file names for this operation."""
        base_name = self.output_base_name
        return {
            'extended_parameters': f'{base_name}_extended_parameters.csv',
            'alkali_char': 'alkalichar.dat',
            'slag_char': 'slagchar.dat',
            'alkaliflyash': 'alkaliflyash.dat',
            'progress_json': 'progress.json',
            'time_history': 'time_history.csv',
            'final_csv': f'HydrationOf_{base_name}.csv',
            'final_img': f'HydrationOf_{base_name}.img.25.100',
            'final_phr': f'HydrationOf_{base_name}.phr.25.100',
            'final_poredist': f'HydrationOf_{base_name}.img.25.100.poredist'
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
    
    def get_source_aggregate_specifications(self) -> Dict[str, Any]:
        """Get aggregate specifications from source microstructure operation."""
        # This will be implemented once we have the microstructure operation relationship
        # For now, return empty dict as placeholder
        return {
            'air_volume_fraction': 0.0,
            'fine_aggregates': [],
            'coarse_aggregates': []
        }
    
    @property
    def estimated_duration_hours(self) -> float:
        """Estimate hydration simulation duration based on parameters."""
        # Simple estimation based on max simulation time and complexity
        # This can be refined based on historical data
        base_hours = self.max_simulation_time / 168.0  # Normalize to 1 week baseline
        complexity_factor = 1.0
        
        # Factor in advanced settings that increase computation time
        if self.ettringite_enabled:
            complexity_factor *= 1.2
        if self.ch_flag_enabled:
            complexity_factor *= 1.1
        if self.csh2_flag_enabled:
            complexity_factor *= 1.1
        
        return base_hours * complexity_factor * 3.0  # 3 hours baseline for 1 week simulation
    
    def __repr__(self):
        return f"<HydrationOperation(id={self.id}, operation='{self.operation.name if self.operation else None}', status='{self.status}')>"
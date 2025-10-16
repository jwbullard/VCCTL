#!/usr/bin/env python3
"""
Operation and Result Models for VCCTL

Clean database models with proper foreign key relationships:
- Operation: Tracks process lifecycle (queued → running → completed/failed)
- Result: Tracks analysis-ready outputs with link back to originating operation
"""

from typing import Optional
from datetime import datetime
import enum
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship

from app.database.base import Base


class OperationStatus(str, enum.Enum):
    """Operation lifecycle status."""
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ERROR = "ERROR"  # Alias for FAILED (for backward compatibility)
    CANCELLED = "CANCELLED"


class OperationType(str, enum.Enum):
    """Types of operations."""
    MICROSTRUCTURE = "MICROSTRUCTURE"
    HYDRATION = "HYDRATION"
    ELASTIC_MODULI = "ELASTIC_MODULI"
    ANALYSIS = "ANALYSIS"


class ResultType(str, enum.Enum):
    """Types of results for analysis."""
    MICROSTRUCTURE_GENERATION = "MICROSTRUCTURE_GENERATION"
    HYDRATION_SIMULATION = "HYDRATION_SIMULATION"
    ELASTIC_MODULI_CALCULATION = "ELASTIC_MODULI_CALCULATION"
    DATA_ANALYSIS = "DATA_ANALYSIS"


class Operation(Base):
    """
    Operation model for tracking process lifecycle.
    
    Represents a single operation (microstructure generation, hydration simulation, etc.)
    from queued → running → completed/failed with timing and progress tracking.
    """
    
    __tablename__ = 'operations'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Basic operation info
    name = Column(String(255), unique=True, nullable=False, index=True)
    operation_type = Column(String(50), nullable=False)  # OperationType enum
    status = Column(String(50), nullable=False, default=OperationStatus.QUEUED.value)  # OperationStatus enum
    
    # Timing information
    queued_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Progress tracking
    progress = Column(Float, default=0.0, nullable=False)  # 0.0 to 1.0
    current_step = Column(String(255), nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    
    # Metadata
    notes = Column(Text, nullable=True)
    
    # Lineage tracking
    parent_operation_id = Column(Integer, ForeignKey('operations.id'), nullable=True, index=True)
    parent_operation = relationship("Operation", remote_side=[id], back_populates="child_operations")
    child_operations = relationship("Operation", back_populates="parent_operation", cascade="all, delete-orphan")
    
    # UI parameter storage for reproducibility
    stored_ui_parameters = Column(JSON, nullable=True)
    
    # Relationship to result (one-to-one)
    result = relationship("Result", back_populates="operation", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Operation(id={self.id}, name='{self.name}', type='{self.operation_type}', status='{self.status}')>"
    
    @property
    def duration(self) -> Optional[float]:
        """Calculate operation duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    @property
    def queue_time(self) -> Optional[float]:
        """Calculate time spent in queue in seconds."""
        if self.queued_at and self.started_at:
            return (self.started_at - self.queued_at).total_seconds()
        return None
    
    @property
    def is_active(self) -> bool:
        """Check if operation is currently active (queued or running)."""
        return self.status in [OperationStatus.QUEUED.value, OperationStatus.RUNNING.value]
    
    @property
    def is_completed(self) -> bool:
        """Check if operation has finished (successfully or with error)."""
        return self.status in [OperationStatus.COMPLETED.value, OperationStatus.FAILED.value, OperationStatus.CANCELLED.value]
    
    def mark_started(self):
        """Mark operation as started."""
        self.status = OperationStatus.RUNNING.value
        self.started_at = datetime.utcnow()
    
    def mark_completed(self):
        """Mark operation as completed successfully."""
        self.status = OperationStatus.COMPLETED.value
        self.completed_at = datetime.utcnow()
        self.progress = 1.0
    
    def mark_failed(self, error_message: str = None):
        """Mark operation as failed."""
        self.status = OperationStatus.FAILED.value
        self.completed_at = datetime.utcnow()
        if error_message:
            self.error_message = error_message

    def mark_error(self, error_message: str = None):
        """Mark operation as failed (alias for backward compatibility)."""
        self.status = OperationStatus.ERROR.value
        self.completed_at = datetime.utcnow()
        if error_message:
            self.error_message = error_message

    def mark_cancelled(self):
        """Mark operation as cancelled."""
        self.status = OperationStatus.CANCELLED.value
        self.completed_at = datetime.utcnow()


class Result(Base):
    """
    Result model for tracking analysis-ready outputs.
    
    Represents the output files and analysis capabilities from a completed operation.
    Always linked to an originating Operation.
    """
    
    __tablename__ = 'results'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign key to operation (one-to-one relationship)
    operation_id = Column(Integer, ForeignKey('operations.id'), unique=True, nullable=False)
    
    # Result information
    result_type = Column(String(50), nullable=False)  # ResultType enum
    folder_path = Column(String(500), nullable=False)  # Path to result folder
    
    # Timing
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Analysis capabilities (computed from folder contents)
    has_3d_data = Column(String(10), default="false", nullable=False)  # "true"/"false" for GTK compatibility
    has_csv_data = Column(String(10), default="false", nullable=False)  # "true"/"false" for GTK compatibility
    
    # Metadata
    file_count = Column(Integer, default=0, nullable=False)
    total_size_mb = Column(Float, default=0.0, nullable=False)
    
    # Back reference to operation
    operation = relationship("Operation", back_populates="result")
    
    def __repr__(self) -> str:
        return f"<Result(id={self.id}, operation='{self.operation.name if self.operation else None}', type='{self.result_type}')>"
    
    @property
    def can_view_3d(self) -> bool:
        """Check if result supports 3D visualization."""
        return self.has_3d_data == "true"
    
    @property
    def can_plot_data(self) -> bool:
        """Check if result supports data plotting."""
        return self.has_csv_data == "true"
    
    @property 
    def analysis_capabilities(self) -> list:
        """Get list of available analysis capabilities."""
        capabilities = []
        if self.can_view_3d:
            capabilities.append("3D Visualization")
        if self.can_plot_data:
            capabilities.append("Data Plotting")
        return capabilities
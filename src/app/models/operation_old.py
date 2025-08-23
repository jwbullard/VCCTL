#!/usr/bin/env python3
"""
Operation Model for VCCTL

Represents simulation operations and their tracking.
Converted from Java JPA entity to SQLAlchemy model.
"""

from typing import Optional, Dict, Any
from datetime import datetime
import json
from sqlalchemy import Column, String, LargeBinary, DateTime, ForeignKey
from pydantic import BaseModel, Field, field_validator, model_validator
import enum

from app.database.base import Base


class OperationStatus(str, enum.Enum):
    """Enumeration for operation status."""
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    FINISHED = "FINISHED"
    ERROR = "ERROR"
    CANCELLED = "CANCELLED"


class OperationType(str, enum.Enum):
    """Enumeration for operation types."""
    HYDRATION = "HYDRATION"
    MICROSTRUCTURE = "MICROSTRUCTURE"
    ANALYSIS = "ANALYSIS"
    EXPORT = "EXPORT"
    IMPORT = "IMPORT"


class Operation(Base):
    """
    Operation model representing simulation operations and their lifecycle.
    
    Tracks operation status, timing, dependencies, and state information
    for various types of VCCTL operations.
    """
    
    __tablename__ = 'operation'
    
    # Override base model id with string primary key
    id = None
    
    # Primary key - operation name (unique identifier)
    name = Column(String(64), primary_key=True, nullable=False, unique=True)
    
    # Operation type
    type = Column(String(24), nullable=True, doc="Type of operation")
    
    # Operation state (binary data)
    state = Column(LargeBinary, nullable=True, doc="Serialized operation state")
    
    # Timing information
    queue = Column(DateTime, nullable=True, doc="Time when operation was queued")
    start = Column(DateTime, nullable=True, doc="Time when operation started")
    finish = Column(DateTime, nullable=True, doc="Time when operation finished")
    
    # Status and dependencies
    status = Column(String(9), nullable=True, doc="Current operation status")
    depends_on_operation_name = Column(String(64), nullable=True,
                                     doc="Name of operation this depends on")
    
    # Notes and additional information
    notes = Column(String, nullable=True, doc="Operation notes and comments")
    
    def __repr__(self) -> str:
        """String representation of the operation."""
        return f"<Operation(name='{self.name}', type='{self.type}', status='{self.status}')>"
    
    @property
    def duration(self) -> Optional[float]:
        """Calculate operation duration in seconds."""
        if self.start and self.finish:
            return (self.finish - self.start).total_seconds()
        return None
    
    @property
    def queue_time(self) -> Optional[float]:
        """Calculate time spent in queue in seconds."""
        if self.queue and self.start:
            return (self.start - self.queue).total_seconds()
        return None
    
    @property
    def is_running(self) -> bool:
        """Check if operation is currently running."""
        return self.status == OperationStatus.RUNNING.value
    
    @property
    def is_finished(self) -> bool:
        """Check if operation has finished (successfully or with error)."""
        return self.status in [OperationStatus.FINISHED.value, OperationStatus.ERROR.value]
    
    @property
    def is_queued(self) -> bool:
        """Check if operation is queued."""
        return self.status == OperationStatus.QUEUED.value
    
    @property
    def has_dependency(self) -> bool:
        """Check if operation depends on another operation."""
        return self.depends_on_operation_name is not None
    
    @property
    def state_data(self) -> Optional[Dict[str, Any]]:
        """Get operation state as dictionary."""
        if self.state:
            try:
                # Assume state is JSON-encoded data
                return json.loads(self.state.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                # If not JSON, return as raw data indicator
                return {'raw_data': f'<binary_data:{len(self.state)}_bytes>'}
        return None
    
    @state_data.setter
    def state_data(self, value: Dict[str, Any]):
        """Set operation state from dictionary."""
        if value:
            try:
                self.state = json.dumps(value).encode('utf-8')
            except (TypeError, ValueError):
                # If can't serialize, store as string representation
                self.state = str(value).encode('utf-8')
        else:
            self.state = None
    
    def mark_queued(self):
        """Mark operation as queued."""
        self.status = OperationStatus.QUEUED.value
        self.queue = datetime.utcnow()
    
    def mark_started(self):
        """Mark operation as started."""
        self.status = OperationStatus.RUNNING.value
        self.start = datetime.utcnow()
    
    def mark_finished(self):
        """Mark operation as finished successfully."""
        self.status = OperationStatus.FINISHED.value
        self.finish = datetime.utcnow()
    
    def mark_error(self, error_message: str = None):
        """Mark operation as finished with error."""
        self.status = OperationStatus.ERROR.value
        self.finish = datetime.utcnow()
        if error_message:
            if self.notes:
                self.notes += f"\nError: {error_message}"
            else:
                self.notes = f"Error: {error_message}"
    
    def mark_cancelled(self):
        """Mark operation as cancelled."""
        self.status = OperationStatus.CANCELLED.value
        if not self.finish:
            self.finish = datetime.utcnow()
    
    def calculate_progress_estimate(self) -> Optional[float]:
        """
        Calculate progress estimate based on timing and type.
        
        Returns progress as a float between 0.0 and 1.0, or None if can't estimate.
        """
        if not self.is_running or not self.start:
            return None
        
        # This is a simplified progress estimation
        # In a real implementation, this would be more sophisticated
        # and based on actual operation metrics
        
        elapsed = (datetime.utcnow() - self.start).total_seconds()
        
        # Rough estimates based on operation type (in seconds)
        typical_durations = {
            OperationType.MICROSTRUCTURE.value: 300,  # 5 minutes
            OperationType.HYDRATION.value: 600,       # 10 minutes
            OperationType.ANALYSIS.value: 120,        # 2 minutes
            OperationType.EXPORT.value: 60,           # 1 minute
            OperationType.IMPORT.value: 60,           # 1 minute
        }
        
        expected_duration = typical_durations.get(self.type, 300)
        progress = min(elapsed / expected_duration, 0.95)  # Cap at 95% until actually finished
        
        return progress


class OperationCreate(BaseModel):
    """Pydantic model for creating operation instances."""
    
    name: str = Field(..., max_length=64, description="Operation name (unique identifier)")
    type: Optional[str] = Field(None, max_length=24, description="Operation type")
    depends_on_operation_name: Optional[str] = Field(None, max_length=64,
                                                   description="Dependency operation name")
    notes: Optional[str] = Field(None, description="Operation notes")
    state_data: Optional[Dict[str, Any]] = Field(None, description="Operation state data")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate operation name."""
        if not v or not v.strip():
            raise ValueError('Operation name cannot be empty')
        return v.strip()


class OperationUpdate(BaseModel):
    """Pydantic model for updating operation instances."""
    
    type: Optional[str] = Field(None, max_length=24, description="Operation type")
    status: Optional[str] = Field(None, max_length=9, description="Operation status")
    depends_on_operation_name: Optional[str] = Field(None, max_length=64,
                                                   description="Dependency operation name")
    notes: Optional[str] = Field(None, description="Operation notes")
    state_data: Optional[Dict[str, Any]] = Field(None, description="Operation state data")


class OperationResponse(BaseModel):
    """Pydantic model for operation API responses."""
    
    name: str
    type: Optional[str]
    status: Optional[str]
    queue: Optional[str]
    start: Optional[str]
    finish: Optional[str]
    depends_on_operation_name: Optional[str]
    notes: Optional[str]
    duration: Optional[float]
    queue_time: Optional[float]
    is_running: bool
    is_finished: bool
    is_queued: bool
    has_dependency: bool
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True
#!/usr/bin/env python3
"""
Test script for new Operation and Result models.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import SQLAlchemy directly
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import enum

Base = declarative_base()

class OperationStatus(str, enum.Enum):
    """Operation lifecycle status."""
    QUEUED = "QUEUED"
    RUNNING = "RUNNING" 
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class OperationType(str, enum.Enum):
    """Types of operations."""
    MICROSTRUCTURE = "MICROSTRUCTURE"
    HYDRATION = "HYDRATION"
    ANALYSIS = "ANALYSIS"

class ResultType(str, enum.Enum):
    """Types of results for analysis."""
    MICROSTRUCTURE_GENERATION = "MICROSTRUCTURE_GENERATION"
    HYDRATION_SIMULATION = "HYDRATION_SIMULATION"
    DATA_ANALYSIS = "DATA_ANALYSIS"

class Operation(Base):
    __tablename__ = 'operations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    operation_type = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False, default=OperationStatus.QUEUED.value)
    queued_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    progress = Column(Float, default=0.0, nullable=False)
    current_step = Column(String(255), nullable=True)
    error_message = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    
    result = relationship("Result", back_populates="operation", uselist=False, cascade="all, delete-orphan")

class Result(Base):
    __tablename__ = 'results'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    operation_id = Column(Integer, ForeignKey('operations.id'), unique=True, nullable=False)
    result_type = Column(String(50), nullable=False)
    folder_path = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    has_3d_data = Column(String(10), default="false", nullable=False)
    has_csv_data = Column(String(10), default="false", nullable=False)
    file_count = Column(Integer, default=0, nullable=False)
    total_size_mb = Column(Float, default=0.0, nullable=False)
    
    operation = relationship("Operation", back_populates="result")

def test_models():
    """Test the new models."""
    print("Testing new Operation and Result models...")
    
    # Create in-memory database
    engine = create_engine('sqlite:///:memory:', echo=True)
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Create test operation
    operation = Operation(
        name="test_operation_1",
        operation_type=OperationType.MICROSTRUCTURE.value,
        status=OperationStatus.QUEUED.value,
        progress=0.0,
        current_step="Initializing..."
    )
    
    session.add(operation)
    session.commit()
    
    # Create test result
    result = Result(
        operation_id=operation.id,
        result_type=ResultType.MICROSTRUCTURE_GENERATION.value,
        folder_path="/path/to/results",
        has_3d_data="true",
        has_csv_data="false",
        file_count=5,
        total_size_mb=15.5
    )
    
    session.add(result)
    session.commit()
    
    # Test queries
    operations = session.query(Operation).all()
    results = session.query(Result).all()
    
    print(f"✅ Created {len(operations)} operations and {len(results)} results")
    
    # Test relationship
    operation = session.query(Operation).first()
    result = session.query(Result).first()
    
    print(f"✅ Operation: {operation.name} (ID: {operation.id})")
    print(f"✅ Result: {result.result_type} -> Operation: {result.operation.name}")
    print(f"✅ Operation has result: {operation.result is not None}")
    
    session.close()
    print("✅ Database models test successful!")

if __name__ == "__main__":
    test_models()
#!/usr/bin/env python3
"""
Demonstration of the new Operation ↔ Result architecture.

This shows how the panels will work with the new database models.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Minimal imports to avoid circular dependencies
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import enum

Base = declarative_base()

class OperationStatus(str, enum.Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING" 
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class OperationType(str, enum.Enum):
    MICROSTRUCTURE = "MICROSTRUCTURE"
    HYDRATION = "HYDRATION"
    ANALYSIS = "ANALYSIS"

class ResultType(str, enum.Enum):
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

def create_sample_data(session):
    """Create sample operations and results."""
    print("Creating sample data...")
    
    # Create microstructure operations
    mic_op1 = Operation(
        name="CemotcBox",
        operation_type=OperationType.MICROSTRUCTURE.value,
        status=OperationStatus.COMPLETED.value,
        progress=1.0,
        queued_at=datetime(2025, 8, 15, 10, 0),
        started_at=datetime(2025, 8, 15, 10, 1),
        completed_at=datetime(2025, 8, 15, 10, 15),
        current_step="Generation complete"
    )
    
    mic_op2 = Operation(
        name="Cem116Mix",
        operation_type=OperationType.MICROSTRUCTURE.value,
        status=OperationStatus.COMPLETED.value,
        progress=1.0,
        queued_at=datetime(2025, 8, 16, 14, 30),
        started_at=datetime(2025, 8, 16, 14, 31),
        completed_at=datetime(2025, 8, 16, 14, 45),
        current_step="Generation complete"
    )
    
    # Create hydration operations
    hyd_op1 = Operation(
        name="HydrationSim_CemotcBox_20250817_120000",
        operation_type=OperationType.HYDRATION.value,
        status=OperationStatus.COMPLETED.value,
        progress=1.0,
        queued_at=datetime(2025, 8, 17, 12, 0),
        started_at=datetime(2025, 8, 17, 12, 1),
        completed_at=datetime(2025, 8, 17, 15, 30),
        current_step="Simulation complete"
    )
    
    hyd_op2 = Operation(
        name="HydrationSim_Cem116Mix_20250818_090000",
        operation_type=OperationType.HYDRATION.value,
        status=OperationStatus.RUNNING.value,
        progress=0.65,
        queued_at=datetime(2025, 8, 18, 9, 0),
        started_at=datetime(2025, 8, 18, 9, 1),
        current_step="Cycle 6500/10000 - DOH: 0.45"
    )
    
    session.add_all([mic_op1, mic_op2, hyd_op1, hyd_op2])
    session.commit()
    
    # Create results for completed operations
    mic_result1 = Result(
        operation_id=mic_op1.id,
        result_type=ResultType.MICROSTRUCTURE_GENERATION.value,
        folder_path="Operations/CemotcBox",
        has_3d_data="true",
        has_csv_data="false",
        file_count=8,
        total_size_mb=45.2
    )
    
    mic_result2 = Result(
        operation_id=mic_op2.id,
        result_type=ResultType.MICROSTRUCTURE_GENERATION.value,
        folder_path="Operations/Cem116Mix",
        has_3d_data="true",
        has_csv_data="false",
        file_count=6,
        total_size_mb=32.1
    )
    
    hyd_result1 = Result(
        operation_id=hyd_op1.id,
        result_type=ResultType.HYDRATION_SIMULATION.value,
        folder_path="Operations/HydrationSim_CemotcBox_20250817_120000",
        has_3d_data="true",
        has_csv_data="true",
        file_count=25,
        total_size_mb=156.8
    )
    
    session.add_all([mic_result1, mic_result2, hyd_result1])
    session.commit()
    
    print(f"✅ Created {session.query(Operation).count()} operations")
    print(f"✅ Created {session.query(Result).count()} results")

def demonstrate_operations_panel(session):
    """Demonstrate Operations Panel logic."""
    print("\n" + "="*50)
    print("OPERATIONS PANEL - Process Lifecycle Management")
    print("="*50)
    
    operations = session.query(Operation).order_by(Operation.queued_at.desc()).all()
    
    print(f"Total Operations: {len(operations)}")
    print("\nOperation List:")
    print("-" * 80)
    print(f"{'Name':<35} {'Type':<15} {'Status':<12} {'Progress':<10} {'Duration'}")
    print("-" * 80)
    
    for op in operations:
        if op.completed_at and op.started_at:
            duration = (op.completed_at - op.started_at).total_seconds() / 60
            duration_str = f"{duration:.1f}m"
        elif op.started_at:
            duration = (datetime.utcnow() - op.started_at).total_seconds() / 60
            duration_str = f"{duration:.1f}m (running)"
        else:
            duration_str = "Queued"
        
        progress_str = f"{op.progress*100:.1f}%"
        
        print(f"{op.name:<35} {op.operation_type:<15} {op.status:<12} {progress_str:<10} {duration_str}")
    
    # Show active operations
    active_ops = [op for op in operations if op.status in [OperationStatus.QUEUED.value, OperationStatus.RUNNING.value]]
    completed_ops = [op for op in operations if op.status in [OperationStatus.COMPLETED.value, OperationStatus.FAILED.value]]
    
    print(f"\n📊 Summary: {len(active_ops)} active, {len(completed_ops)} completed")

def demonstrate_results_panel(session):
    """Demonstrate Results Panel logic."""
    print("\n" + "="*50)
    print("RESULTS PANEL - Analysis-Ready Outputs")
    print("="*50)
    
    results = session.query(Result).order_by(Result.created_at.desc()).all()
    
    print(f"Total Results: {len(results)}")
    print("\nResults List:")
    print("-" * 90)
    print(f"{'Operation Name':<35} {'Type':<25} {'3D':<5} {'CSV':<5} {'Files':<7} {'Size'}")
    print("-" * 90)
    
    for result in results:
        size_str = f"{result.total_size_mb:.1f}MB"
        print(f"{result.operation.name:<35} {result.result_type:<25} {result.has_3d_data:<5} {result.has_csv_data:<5} {result.file_count:<7} {size_str}")
    
    # Show analysis capabilities
    results_with_3d = [r for r in results if r.has_3d_data == "true"]
    results_with_csv = [r for r in results if r.has_csv_data == "true"]
    
    print(f"\n🔬 Analysis capabilities: {len(results_with_3d)} with 3D visualization, {len(results_with_csv)} with data plotting")

def demonstrate_architecture():
    """Demonstrate the complete new architecture."""
    print("🚀 VCCTL New Architecture Demonstration")
    print("="*60)
    
    # Create in-memory database
    engine = create_engine('sqlite:///:memory:', echo=False)
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Create sample data
    create_sample_data(session)
    
    # Demonstrate panels
    demonstrate_operations_panel(session)
    demonstrate_results_panel(session)
    
    print("\n" + "="*60)
    print("✅ ARCHITECTURE BENEFITS")
    print("="*60)
    print("• Clean separation: Operations = process lifecycle, Results = analysis")
    print("• Simple queries: No JSON files, filesystem scanning, or validation")
    print("• Referential integrity: FK constraints maintain consistency")
    print("• No duplicates: Database constraints prevent duplicate operations")
    print("• Efficient: Direct database queries instead of complex filtering")
    print("• Scalable: Proper relational design supports growth")
    
    session.close()

if __name__ == "__main__":
    demonstrate_architecture()
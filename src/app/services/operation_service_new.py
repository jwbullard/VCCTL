#!/usr/bin/env python3
"""
New Operation Service for VCCTL

Simple service for managing Operation and Result models using the new database schema.
"""

import logging
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from .base_service import BaseService
from ..models.operation import Operation, Result, OperationStatus, OperationType, ResultType
from ..database.service import DatabaseService


class OperationServiceNew:
    """Service for managing operations and results."""
    
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
        self.logger = logging.getLogger(__name__)
    
    # Operation methods
    def create_operation(self, name: str, operation_type: str, notes: str = None) -> Operation:
        """Create a new operation."""
        with self.db_service.get_session() as session:
            operation = Operation(
                name=name,
                operation_type=operation_type,
                status=OperationStatus.QUEUED.value,
                progress=0.0,
                notes=notes,
                queued_at=datetime.utcnow()
            )
            session.add(operation)
            session.commit()
            session.refresh(operation)
            return operation
    
    def get_all_operations(self) -> List[Operation]:
        """Get all operations."""
        with self.db_service.get_read_only_session() as session:
            return session.query(Operation).order_by(Operation.queued_at.desc()).all()
    
    def get_operation_by_id(self, operation_id: int) -> Optional[Operation]:
        """Get operation by ID."""
        with self.db_service.get_read_only_session() as session:
            return session.query(Operation).filter(Operation.id == operation_id).first()
    
    def get_operation_by_name(self, name: str) -> Optional[Operation]:
        """Get operation by name."""
        with self.db_service.get_read_only_session() as session:
            return session.query(Operation).filter(Operation.name == name).first()
    
    def update_operation_status(self, operation_id: int, status: str, 
                              progress: float = None, current_step: str = None, 
                              error_message: str = None) -> bool:
        """Update operation status and progress."""
        try:
            with self.db_service.get_session() as session:
                operation = session.query(Operation).filter(Operation.id == operation_id).first()
                if not operation:
                    return False
                
                operation.status = status
                if progress is not None:
                    operation.progress = progress
                if current_step is not None:
                    operation.current_step = current_step
                if error_message is not None:
                    operation.error_message = error_message
                
                # Update timing
                if status == OperationStatus.RUNNING.value and not operation.started_at:
                    operation.started_at = datetime.utcnow()
                elif status in [OperationStatus.COMPLETED.value, OperationStatus.FAILED.value, OperationStatus.CANCELLED.value]:
                    operation.completed_at = datetime.utcnow()
                    if status == OperationStatus.COMPLETED.value:
                        operation.progress = 1.0
                
                session.commit()
                return True
        except Exception as e:
            self.logger.error(f"Failed to update operation {operation_id}: {e}")
            return False
    
    def delete_operation(self, operation_id: int) -> bool:
        """Delete operation and its result."""
        try:
            with self.db_service.get_session() as session:
                operation = session.query(Operation).filter(Operation.id == operation_id).first()
                if operation:
                    session.delete(operation)  # Cascade will delete result too
                    session.commit()
                    return True
                return False
        except Exception as e:
            self.logger.error(f"Failed to delete operation {operation_id}: {e}")
            return False
    
    # Result methods
    def create_result(self, operation_id: int, result_type: str, folder_path: str,
                     has_3d_data: bool = False, has_csv_data: bool = False,
                     file_count: int = 0, total_size_mb: float = 0.0) -> Result:
        """Create a result for an operation."""
        with self.db_service.get_session() as session:
            result = Result(
                operation_id=operation_id,
                result_type=result_type,
                folder_path=folder_path,
                has_3d_data="true" if has_3d_data else "false",
                has_csv_data="true" if has_csv_data else "false",
                file_count=file_count,
                total_size_mb=total_size_mb,
                created_at=datetime.utcnow()
            )
            session.add(result)
            session.commit()
            session.refresh(result)
            return result
    
    def get_all_results(self) -> List[Result]:
        """Get all results."""
        with self.db_service.get_read_only_session() as session:
            return session.query(Result).order_by(Result.created_at.desc()).all()
    
    def get_result_by_operation_id(self, operation_id: int) -> Optional[Result]:
        """Get result by operation ID."""
        with self.db_service.get_read_only_session() as session:
            return session.query(Result).filter(Result.operation_id == operation_id).first()
    
    def update_result_capabilities(self, result_id: int, has_3d_data: bool = None,
                                 has_csv_data: bool = None, file_count: int = None,
                                 total_size_mb: float = None) -> bool:
        """Update result analysis capabilities."""
        try:
            with self.db_service.get_session() as session:
                result = session.query(Result).filter(Result.id == result_id).first()
                if not result:
                    return False
                
                if has_3d_data is not None:
                    result.has_3d_data = "true" if has_3d_data else "false"
                if has_csv_data is not None:
                    result.has_csv_data = "true" if has_csv_data else "false"
                if file_count is not None:
                    result.file_count = file_count
                if total_size_mb is not None:
                    result.total_size_mb = total_size_mb
                
                session.commit()
                return True
        except Exception as e:
            self.logger.error(f"Failed to update result {result_id}: {e}")
            return False
    
    def scan_result_folder(self, result_id: int) -> bool:
        """Scan result folder to update capabilities automatically."""
        try:
            with self.db_service.get_session() as session:
                result = session.query(Result).filter(Result.id == result_id).first()
                if not result:
                    return False
                
                from pathlib import Path
                folder_path = Path(result.folder_path)
                
                if not folder_path.exists():
                    return False
                
                # Check for 3D data (IMG files)
                img_files = list(folder_path.glob("*.img")) + list(folder_path.glob("*.pimg"))
                has_3d_data = len(img_files) > 0
                
                # Check for CSV data
                csv_files = list(folder_path.glob("*.csv"))
                has_csv_data = len(csv_files) > 0
                
                # Count files and calculate size
                all_files = list(folder_path.glob("*"))
                file_count = len([f for f in all_files if f.is_file()])
                total_size_mb = sum(f.stat().st_size for f in all_files if f.is_file()) / (1024 * 1024)
                
                # Update result
                result.has_3d_data = "true" if has_3d_data else "false"
                result.has_csv_data = "true" if has_csv_data else "false"
                result.file_count = file_count
                result.total_size_mb = total_size_mb
                
                session.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to scan result folder {result_id}: {e}")
            return False
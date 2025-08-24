#!/usr/bin/env python3
"""
Simple Operation Service for VCCTL

Replacement for the complex OperationService that works with the new database models.
"""

import logging
from typing import List, Optional
from datetime import datetime

from ..models.operation import Operation, OperationStatus, OperationType
from ..database.service import DatabaseService


class OperationService:
    """Simple service for managing operations - provides basic methods for panels."""
    
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
        self.logger = logging.getLogger(__name__)
    
    def get_all(self) -> List[Operation]:
        """Get all operations."""
        with self.db_service.get_read_only_session() as session:
            return session.query(Operation).order_by(Operation.queued_at.desc()).all()
    
    def get_by_name(self, name: str) -> Optional[Operation]:
        """Get operation by name."""
        with self.db_service.get_read_only_session() as session:
            return session.query(Operation).filter(Operation.name == name).first()
    
    def create_operation(self, name: str, operation_type: str, notes: str = None, status: OperationStatus = None, progress: float = 0.0, current_step: str = None) -> Operation:
        """Create a new operation with specified status."""
        if status is None:
            status = OperationStatus.QUEUED
            
        with self.db_service.get_session() as session:
            operation = Operation(
                name=name,
                operation_type=operation_type,
                status=status.value,
                progress=progress,
                current_step=current_step,
                notes=notes,
                queued_at=datetime.utcnow()
            )
            
            # Set started_at timestamp if creating with RUNNING status
            if status == OperationStatus.RUNNING:
                operation.started_at = datetime.utcnow()
            
            session.add(operation)
            session.commit()
            session.refresh(operation)
            self.logger.info(f"Created operation: {operation.name} with status {status.value}")
            return operation
    
    def delete(self, name: str) -> bool:
        """Delete operation by name."""
        try:
            with self.db_service.get_session() as session:
                operation = session.query(Operation).filter(Operation.name == name).first()
                if operation:
                    session.delete(operation)
                    session.commit()
                    self.logger.info(f"Deleted operation: {name}")
                    return True
                else:
                    self.logger.warning(f"Operation not found for deletion: {name}")
                    return False
        except Exception as e:
            self.logger.error(f"Error deleting operation {name}: {e}")
            return False
    
    def update_status(self, name: str, status: OperationStatus, progress: float = None, current_step: str = None) -> bool:
        """Update operation status and progress."""
        try:
            with self.db_service.get_session() as session:
                operation = session.query(Operation).filter(Operation.name == name).first()
                if operation:
                    operation.status = status.value
                    if progress is not None:
                        operation.progress = progress
                    if current_step is not None:
                        operation.current_step = current_step
                    if status in [OperationStatus.COMPLETED, OperationStatus.FAILED, OperationStatus.CANCELLED]:
                        operation.completed_at = datetime.utcnow()
                    session.commit()
                    self.logger.debug(f"Updated operation {name}: status={status.value}, progress={progress}")
                    return True
                else:
                    self.logger.warning(f"Operation not found for update: {name}")
                    return False
        except Exception as e:
            self.logger.error(f"Error updating operation {name}: {e}")
            return False
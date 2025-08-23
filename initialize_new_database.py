#!/usr/bin/env python3
"""
Initialize fresh database with new Operation and Result models.
This script creates the new clean database schema.
"""

import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from app.database.service import DatabaseService
from app.models import Operation, Result
from app.database.base import Base

def initialize_database():
    """Create fresh database with new schema."""
    print("Initializing fresh database with new Operation and Result models...")
    
    # Create database service
    db_service = DatabaseService()
    
    # Create all tables
    print("Creating database tables...")
    Base.metadata.create_all(bind=db_service.engine)
    
    print("Database initialization complete!")
    print(f"Database location: {db_service.database_url}")
    
    # Test database connection
    with db_service.get_session() as session:
        # Check if tables exist
        operation_count = session.query(Operation).count()
        result_count = session.query(Result).count()
        print(f"Operations table: {operation_count} records")
        print(f"Results table: {result_count} records")
    
    print("Database is ready for use!")

if __name__ == "__main__":
    initialize_database()
#!/usr/bin/env python3
"""
Reset Database for VCCTL

This script drops and recreates the database with the updated schema.
Run this when model changes require new database columns.
"""

import sys
import os
from pathlib import Path

# Add the src directory to the Python path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

def reset_database():
    """Reset the database with new schema."""
    print("🔄 Resetting VCCTL Database")
    print("=" * 50)
    
    try:
        from app.database.service import DatabaseService
        from app.database.base import Base
        from app.database.config import default_config
        
        # Initialize database service
        db_service = DatabaseService(default_config)
        
        print(f"📁 Database URL: {default_config.database_url}")
        
        # Drop all existing tables
        print("🗑️  Dropping existing tables...")
        Base.metadata.drop_all(bind=db_service.engine)
        print("✓ All tables dropped")
        
        # Create all tables with new schema
        print("🏗️  Creating tables with new schema...")
        db_service.create_all_tables()
        print("✓ All tables created")
        
        # Initialize the database
        print("🚀 Initializing database...")
        db_service.initialize_database(create_tables=False)  # Tables already created
        print("✓ Database initialized")
        
        print("\n✅ Database reset complete!")
        print("📊 Ready for testing with updated cement model")
        
        return True
        
    except Exception as e:
        print(f"❌ Error resetting database: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = reset_database()
    sys.exit(0 if success else 1)
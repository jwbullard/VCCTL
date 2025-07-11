#!/usr/bin/env python3
"""
Database Service Test Script

Tests the database service functionality without requiring GTK.
"""

import sys
import os
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


def test_database_imports():
    """Test database module imports."""
    print("Testing database imports...")
    
    try:
        from app.database import (
            DatabaseConfig, default_config, Base, BaseModel,
            DatabaseService, database_service, MigrationManager
        )
        print("✓ All database imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False


def test_database_config():
    """Test database configuration."""
    print("\nTesting database configuration...")
    
    try:
        from app.database import DatabaseConfig, default_config
        
        # Test default config
        print(f"✓ Default database URL: {default_config.database_url}")
        print(f"✓ Database path: {default_config.db_path}")
        print(f"✓ Database exists: {default_config.database_exists()}")
        
        # Test custom config
        custom_config = DatabaseConfig("test.db")
        print(f"✓ Custom config created: {custom_config.database_url}")
        
        return True
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False


def test_database_service():
    """Test database service functionality."""
    print("\nTesting database service...")
    
    try:
        from app.database import database_service, create_migration_manager
        
        # Test service initialization
        print(f"✓ Database service initialized")
        
        # Test health check
        health = database_service.health_check()
        print(f"✓ Health check completed: {health['status']}")
        
        # Test migration manager
        migration_manager = create_migration_manager()
        version_info = migration_manager.check_database_version()
        print(f"✓ Database version check: {version_info}")
        
        return True
    except Exception as e:
        print(f"✗ Database service test failed: {e}")
        return False


def test_database_operations():
    """Test basic database operations."""
    print("\nTesting database operations...")
    
    try:
        from app.database import database_service, create_migration_manager
        
        # Initialize database
        migration_manager = create_migration_manager()
        migration_manager.upgrade_database()
        print("✓ Database initialized/upgraded")
        
        # Test connection
        with database_service.get_read_only_session() as session:
            from sqlalchemy import text
            result = session.execute(text("SELECT 1"))
            assert result.fetchone()[0] == 1
        print("✓ Database connection test passed")
        
        # Test table info
        table_info = database_service.get_table_info()
        print(f"✓ Found {len(table_info)} tables in database")
        
        return True
    except Exception as e:
        print(f"✗ Database operations test failed: {e}")
        return False


def test_base_model():
    """Test base model functionality."""
    print("\nTesting base model...")
    
    try:
        from app.database import Base, BaseModel
        from sqlalchemy import Column, String
        
        # Create a test model
        class TestModel(Base):
            __tablename__ = 'test_model'
            name = Column(String(100), nullable=False)
        
        # Test model creation
        test_instance = TestModel(name="Test Item")
        print(f"✓ Test model created: {test_instance}")
        
        # Test to_dict functionality
        data_dict = test_instance.to_dict()
        print(f"✓ Model to_dict: {list(data_dict.keys())}")
        
        return True
    except Exception as e:
        print(f"✗ Base model test failed: {e}")
        return False


def cleanup_test_database():
    """Clean up test database."""
    try:
        from app.database import default_config
        if default_config.database_exists():
            default_config.db_path.unlink()
            print("✓ Test database cleaned up")
    except Exception as e:
        print(f"Warning: Could not clean up test database: {e}")


def main():
    """Run all database tests."""
    print("VCCTL Database Service Tests")
    print("=" * 50)
    
    success = True
    
    # Run tests
    success &= test_database_imports()
    success &= test_database_config()
    success &= test_database_service()
    success &= test_base_model()
    success &= test_database_operations()
    
    print("\n" + "=" * 50)
    if success:
        print("✓ All database tests passed!")
        print("\nDatabase service is ready for use.")
    else:
        print("✗ Some tests failed!")
        return 1
    
    # Optional cleanup
    cleanup_test_database()
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
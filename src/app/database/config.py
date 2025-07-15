#!/usr/bin/env python3
"""
Database Configuration for VCCTL

Provides database configuration settings and connection parameters.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from app.resources.app_info import DATABASE_DIR


class DatabaseConfig:
    """Database configuration settings."""
    
    def __init__(self, db_name: str = "vcctl.db"):
        """Initialize database configuration."""
        self.db_name = db_name
        self.db_path = DATABASE_DIR / db_name
        
        # Ensure database directory exists
        DATABASE_DIR.mkdir(parents=True, exist_ok=True)
    
    @property
    def database_url(self) -> str:
        """Get the SQLite database URL."""
        return f"sqlite:///{self.db_path}"
    
    @property
    def engine_config(self) -> Dict[str, Any]:
        """Get SQLAlchemy engine configuration."""
        return {
            "url": self.database_url,
            "echo": False,  # Set to True for SQL logging
            "pool_pre_ping": True,
            "pool_recycle": 3600,  # Recycle connections after 1 hour
            "connect_args": {
                "timeout": 30,
                "check_same_thread": False,  # Allow multiple threads
                "isolation_level": None,  # Use autocommit mode
            }
        }
    
    @property
    def session_config(self) -> Dict[str, Any]:
        """Get SQLAlchemy session configuration."""
        return {
            "autocommit": False,
            "autoflush": False,
            "expire_on_commit": False
        }
    
    def database_exists(self) -> bool:
        """Check if the database file exists."""
        return self.db_path.exists()
    
    def get_database_size(self) -> int:
        """Get the database file size in bytes."""
        if self.database_exists():
            return self.db_path.stat().st_size
        return 0
    
    def backup_database(self, backup_path: Path = None) -> Path:
        """Create a backup of the database."""
        if backup_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = DATABASE_DIR / f"vcctl_backup_{timestamp}.db"
        
        if self.database_exists():
            import shutil
            shutil.copy2(self.db_path, backup_path)
            return backup_path
        else:
            raise FileNotFoundError("Database file does not exist")


# Default configuration instance
default_config = DatabaseConfig()


def get_database_config() -> DatabaseConfig:
    """Get the default database configuration instance."""
    return default_config
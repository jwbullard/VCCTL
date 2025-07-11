#!/usr/bin/env python3
"""
Database Service for VCCTL

Provides database connection management, session handling, and database operations.
"""

import logging
from contextlib import contextmanager
from typing import Generator, Optional, Any, Dict, List
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.config import DatabaseConfig, default_config
from app.database.base import Base, SessionLocal


class DatabaseService:
    """Main database service for VCCTL application."""
    
    def __init__(self, config: DatabaseConfig = None):
        """Initialize the database service."""
        self.config = config or default_config
        self.logger = logging.getLogger('VCCTL.Database')
        
        self._engine: Optional[Engine] = None
        self._sessionmaker: Optional[sessionmaker] = None
        self._is_initialized = False
        
        self.logger.info(f"Database service initialized with: {self.config.database_url}")
    
    @property
    def engine(self) -> Engine:
        """Get the SQLAlchemy engine, creating it if necessary."""
        if self._engine is None:
            self._create_engine()
        return self._engine
    
    @property
    def sessionmaker(self) -> sessionmaker:
        """Get the session maker, creating it if necessary."""
        if self._sessionmaker is None:
            self._create_sessionmaker()
        return self._sessionmaker
    
    def _create_engine(self) -> None:
        """Create the SQLAlchemy engine."""
        try:
            engine_config = self.config.engine_config.copy()
            url = engine_config.pop('url')
            
            # Add SQLite-specific configuration
            if 'sqlite' in url:
                engine_config['poolclass'] = StaticPool
                # Remove pool_size and max_overflow for SQLite with StaticPool
                engine_config.pop('pool_size', None)
                engine_config.pop('max_overflow', None)
            
            self._engine = create_engine(url, **engine_config)
            
            # Configure SQLite for better performance and reliability
            if 'sqlite' in url:
                self._configure_sqlite()
            
            self.logger.info("Database engine created successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to create database engine: {e}")
            raise
    
    def _configure_sqlite(self) -> None:
        """Configure SQLite-specific settings."""
        @event.listens_for(self._engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            # Enable foreign key constraints
            cursor.execute("PRAGMA foreign_keys=ON")
            # Set journal mode to WAL for better concurrency
            cursor.execute("PRAGMA journal_mode=WAL")
            # Set synchronous mode for better performance
            cursor.execute("PRAGMA synchronous=NORMAL")
            # Set cache size (in KB)
            cursor.execute("PRAGMA cache_size=10000")
            # Set temp store to memory
            cursor.execute("PRAGMA temp_store=MEMORY")
            cursor.close()
    
    def _create_sessionmaker(self) -> None:
        """Create the session maker."""
        try:
            session_config = self.config.session_config
            self._sessionmaker = sessionmaker(bind=self.engine, **session_config)
            
            # Update the global SessionLocal
            SessionLocal.configure(bind=self.engine, **session_config)
            
            self.logger.info("Session maker created successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to create session maker: {e}")
            raise
    
    def initialize_database(self, create_tables: bool = True) -> None:
        """Initialize the database, optionally creating tables."""
        try:
            if create_tables:
                self.create_all_tables()
            
            self._is_initialized = True
            self.logger.info("Database initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise
    
    def create_all_tables(self) -> None:
        """Create all tables defined in the models."""
        try:
            Base.metadata.create_all(bind=self.engine)
            self.logger.info("All database tables created successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to create tables: {e}")
            raise
    
    def drop_all_tables(self) -> None:
        """Drop all tables (use with caution!)."""
        try:
            Base.metadata.drop_all(bind=self.engine)
            self.logger.warning("All database tables dropped")
            
        except Exception as e:
            self.logger.error(f"Failed to drop tables: {e}")
            raise
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get a database session with automatic cleanup."""
        if not self._is_initialized:
            self.initialize_database()
        
        session = self.sessionmaker()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            self.logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    @contextmanager
    def get_read_only_session(self) -> Generator[Session, None, None]:
        """Get a read-only database session."""
        if not self._is_initialized:
            self.initialize_database()
        
        session = self.sessionmaker()
        try:
            yield session
        except Exception as e:
            self.logger.error(f"Database read session error: {e}")
            raise
        finally:
            session.close()
    
    def execute_sql(self, sql: str, parameters: Dict[str, Any] = None) -> Any:
        """Execute raw SQL query."""
        try:
            with self.get_session() as session:
                result = session.execute(text(sql), parameters or {})
                return result.fetchall()
        except Exception as e:
            self.logger.error(f"Failed to execute SQL: {e}")
            raise
    
    def health_check(self) -> Dict[str, Any]:
        """Perform database health check."""
        health_info = {
            'status': 'unknown',
            'database_exists': False,
            'database_size': 0,
            'tables_count': 0,
            'connection_test': False,
            'error': None
        }
        
        try:
            # Check if database file exists
            health_info['database_exists'] = self.config.database_exists()
            health_info['database_size'] = self.config.get_database_size()
            
            # Test database connection
            with self.get_read_only_session() as session:
                # Try a simple query
                result = session.execute(text("SELECT 1"))
                result.fetchone()
                health_info['connection_test'] = True
                
                # Count tables
                if 'sqlite' in self.config.database_url:
                    result = session.execute(text(
                        "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
                    ))
                    health_info['tables_count'] = result.scalar()
            
            health_info['status'] = 'healthy'
            
        except Exception as e:
            health_info['status'] = 'unhealthy'
            health_info['error'] = str(e)
            self.logger.error(f"Database health check failed: {e}")
        
        return health_info
    
    def get_table_info(self) -> List[Dict[str, Any]]:
        """Get information about all tables in the database."""
        try:
            with self.get_read_only_session() as session:
                if 'sqlite' in self.config.database_url:
                    result = session.execute(text("""
                        SELECT name, sql 
                        FROM sqlite_master 
                        WHERE type='table' 
                        ORDER BY name
                    """))
                    
                    tables = []
                    for row in result:
                        table_name = row[0]
                        # Get row count
                        count_result = session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                        row_count = count_result.scalar()
                        
                        tables.append({
                            'name': table_name,
                            'sql': row[1],
                            'row_count': row_count
                        })
                    
                    return tables
                else:
                    # For other databases, implement appropriate queries
                    return []
                    
        except Exception as e:
            self.logger.error(f"Failed to get table info: {e}")
            return []
    
    def backup_database(self, backup_path: str = None) -> str:
        """Create a backup of the database."""
        try:
            backup_path = self.config.backup_database(backup_path)
            self.logger.info(f"Database backed up to: {backup_path}")
            return str(backup_path)
        except Exception as e:
            self.logger.error(f"Failed to backup database: {e}")
            raise
    
    def close(self) -> None:
        """Close the database service and cleanup resources."""
        try:
            if self._engine:
                self._engine.dispose()
                self._engine = None
            
            self._sessionmaker = None
            self._is_initialized = False
            
            self.logger.info("Database service closed")
            
        except Exception as e:
            self.logger.error(f"Error closing database service: {e}")


# Global database service instance
database_service = DatabaseService()
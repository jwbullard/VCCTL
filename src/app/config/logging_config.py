#!/usr/bin/env python3
"""
Logging Configuration for VCCTL

Manages logging settings and configuration.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List
import logging


@dataclass
class LoggingConfig:
    """Configuration for application logging."""
    
    # Basic logging settings
    level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"
    
    # File logging
    log_to_file: bool = True
    log_file: str = "vcctl.log"
    max_file_size: int = 10  # MB
    backup_count: int = 5
    
    # Console logging
    log_to_console: bool = True
    console_level: str = "INFO"
    
    # Logger settings for different modules
    logger_levels: Dict[str, str] = field(default_factory=lambda: {
        'VCCTL': 'INFO',
        'VCCTL.Database': 'WARNING',
        'VCCTL.Services': 'INFO',
        'VCCTL.UI': 'INFO',
        'VCCTL.Config': 'INFO'
    })
    
    # Performance logging
    performance_logging: bool = False
    log_sql_queries: bool = False
    log_function_timing: bool = False
    
    @classmethod
    def create_default(cls) -> 'LoggingConfig':
        """Create default logging configuration."""
        return cls()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LoggingConfig':
        """Create logging configuration from dictionary."""
        return cls(
            level=data.get('level', 'INFO'),
            format=data.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
            date_format=data.get('date_format', '%Y-%m-%d %H:%M:%S'),
            log_to_file=data.get('log_to_file', True),
            log_file=data.get('log_file', 'vcctl.log'),
            max_file_size=data.get('max_file_size', 10),
            backup_count=data.get('backup_count', 5),
            log_to_console=data.get('log_to_console', True),
            console_level=data.get('console_level', 'INFO'),
            logger_levels=data.get('logger_levels', {
                'VCCTL': 'INFO', 'VCCTL.Database': 'WARNING',
                'VCCTL.Services': 'INFO', 'VCCTL.UI': 'INFO', 'VCCTL.Config': 'INFO'
            }),
            performance_logging=data.get('performance_logging', False),
            log_sql_queries=data.get('log_sql_queries', False),
            log_function_timing=data.get('log_function_timing', False)
        )
    
    def validate(self) -> Dict[str, Any]:
        """Validate logging configuration."""
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': []
        }
        
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        
        if self.level not in valid_levels:
            validation_result['errors'].append(f"Invalid log level '{self.level}'")
            validation_result['is_valid'] = False
        
        if self.console_level not in valid_levels:
            validation_result['errors'].append(f"Invalid console log level '{self.console_level}'")
            validation_result['is_valid'] = False
        
        return validation_result
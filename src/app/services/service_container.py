#!/usr/bin/env python3
"""
Service Container for VCCTL

Provides centralized service management and dependency injection.
"""

import logging
from typing import Optional

from app.database.service import DatabaseService, database_service
from app.services.cement_service import CementService
from app.services.fly_ash_service import FlyAshService
from app.services.slag_service import SlagService
from app.services.inert_filler_service import InertFillerService
from app.services.silica_fume_service import SilicaFumeService
from app.services.limestone_service import LimestoneService
from app.services.mix_service import MixService
from app.services.aggregate_service import AggregateService
from app.services.microstructure_service import MicrostructureService
from app.services.hydration_service import HydrationService
from app.services.grading_service import GradingService
from app.services.directories_service import DirectoriesService
from app.services.file_operations_service import FileOperationsService
from app.services.operation_service import OperationService
from app.services.export_service import ExportService
from app.config.config_manager import ConfigManager


class ServiceContainer:
    """
    Container for managing all VCCTL services.
    
    Provides centralized access to services and manages their dependencies.
    Implements singleton pattern to ensure consistent service instances.
    """
    
    _instance: Optional['ServiceContainer'] = None
    
    def __new__(cls, db_service: DatabaseService = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, db_service: DatabaseService = None):
        if hasattr(self, '_initialized'):
            return
        
        self.logger = logging.getLogger('VCCTL.ServiceContainer')
        self.db_service = db_service or database_service
        self.database_service = self.db_service  # Alias for compatibility
        
        # Initialize configuration and core services
        self._config_manager = None
        self._directories_service = None
        self._file_operations_service = None
        self._export_service = None
        self._operation_service = None
        
        # Initialize business logic services
        self._cement_service = None
        self._fly_ash_service = None
        self._slag_service = None
        self._inert_filler_service = None
        self._silica_fume_service = None
        self._limestone_service = None
        self._mix_service = None
        self._aggregate_service = None
        self._microstructure_service = None
        self._hydration_service = None
        self._grading_service = None
        
        self._initialized = True
        self.logger.info("Service container initialized")
    
    @property
    def config_manager(self) -> ConfigManager:
        """Get configuration manager instance."""
        if self._config_manager is None:
            self._config_manager = ConfigManager()
            self.logger.debug("Configuration manager created")
        return self._config_manager
    
    @property
    def directories_service(self) -> DirectoriesService:
        """Get directories service instance."""
        if self._directories_service is None:
            self._directories_service = DirectoriesService(self.config_manager)
            self.logger.debug("Directories service created")
        return self._directories_service
    
    @property
    def file_operations_service(self) -> FileOperationsService:
        """Get file operations service instance."""
        if self._file_operations_service is None:
            self._file_operations_service = FileOperationsService(self.directories_service)
            self.logger.debug("File operations service created")
        return self._file_operations_service
    
    @property
    def export_service(self) -> ExportService:
        """Get export service instance."""
        if self._export_service is None:
            self._export_service = ExportService(self.file_operations_service)
            self.logger.debug("Export service created")
        return self._export_service
    
    @property
    def operation_service(self) -> OperationService:
        """Get operation service instance."""
        if self._operation_service is None:
            self._operation_service = OperationService(self.db_service)
            # Register operation handlers
            from app.utils.operation_handlers import OPERATION_HANDLERS
            for op_type, handler in OPERATION_HANDLERS.items():
                self._operation_service.register_operation_handler(op_type, handler.execute)
            self.logger.debug("Operation service created")
        return self._operation_service
    
    @property
    def cement_service(self) -> CementService:
        """Get cement service instance."""
        if self._cement_service is None:
            self._cement_service = CementService(self.db_service)
            self.logger.debug("Cement service created")
        return self._cement_service
    
    @property
    def fly_ash_service(self) -> FlyAshService:
        """Get fly ash service instance."""
        if self._fly_ash_service is None:
            self._fly_ash_service = FlyAshService(self.db_service)
            self.logger.debug("Fly ash service created")
        return self._fly_ash_service
    
    @property
    def slag_service(self) -> SlagService:
        """Get slag service instance."""
        if self._slag_service is None:
            self._slag_service = SlagService(self.db_service)
            self.logger.debug("Slag service created")
        return self._slag_service
    
    @property
    def inert_filler_service(self) -> InertFillerService:
        """Get inert filler service instance."""
        if self._inert_filler_service is None:
            self._inert_filler_service = InertFillerService(self.db_service)
            self.logger.debug("Inert filler service created")
        return self._inert_filler_service
    
    @property
    def silica_fume_service(self) -> SilicaFumeService:
        """Get silica fume service instance."""
        if self._silica_fume_service is None:
            self._silica_fume_service = SilicaFumeService(self.db_service)
            self.logger.debug("Silica fume service created")
        return self._silica_fume_service
    
    @property
    def limestone_service(self) -> LimestoneService:
        """Get limestone service instance."""
        if self._limestone_service is None:
            self._limestone_service = LimestoneService(self.db_service)
            self.logger.debug("Limestone service created")
        return self._limestone_service
    
    @property
    def mix_service(self) -> MixService:
        """Get mix service instance."""
        if self._mix_service is None:
            self._mix_service = MixService(self.db_service)
            self.logger.debug("Mix service created")
        return self._mix_service
    
    @property
    def aggregate_service(self) -> AggregateService:
        """Get aggregate service instance."""
        if self._aggregate_service is None:
            self._aggregate_service = AggregateService(self.db_service)
            self.logger.debug("Aggregate service created")
        return self._aggregate_service
    
    @property
    def microstructure_service(self) -> MicrostructureService:
        """Get microstructure service instance."""
        if self._microstructure_service is None:
            self._microstructure_service = MicrostructureService(self.db_service)
            self.logger.debug("Microstructure service created")
        return self._microstructure_service
    
    @property
    def hydration_service(self) -> HydrationService:
        """Get hydration service instance."""
        if self._hydration_service is None:
            self._hydration_service = HydrationService(self.db_service)
            self.logger.debug("Hydration service created")
        return self._hydration_service
    
    @property
    def grading_service(self) -> GradingService:
        """Get grading service instance."""
        if self._grading_service is None:
            self._grading_service = GradingService(self.db_service)
            self.logger.debug("Grading service created")
        return self._grading_service
    
    def get_all_services(self) -> dict:
        """Get all available services."""
        return {
            'config_manager': self.config_manager,
            'directories': self.directories_service,
            'file_operations': self.file_operations_service,
            'export': self.export_service,
            'operation': self.operation_service,
            'cement': self.cement_service,
            'fly_ash': self.fly_ash_service,
            'slag': self.slag_service,
            'inert_filler': self.inert_filler_service,
            'silica_fume': self.silica_fume_service,
            'limestone': self.limestone_service,
            'mix': self.mix_service,
            'aggregate': self.aggregate_service,
            'microstructure': self.microstructure_service,
            'grading': self.grading_service
        }
    
    def health_check(self) -> dict:
        """Perform health check on all services."""
        health_status = {
            'container_status': 'healthy',
            'database_status': 'unknown',
            'services': {}
        }
        
        try:
            # Check database health
            db_health = self.db_service.health_check()
            health_status['database_status'] = db_health['status']
            
            # Check each service
            services = self.get_all_services()
            for service_name, service in services.items():
                try:
                    count = service.get_count()
                    health_status['services'][service_name] = {
                        'status': 'healthy',
                        'record_count': count
                    }
                except Exception as e:
                    health_status['services'][service_name] = {
                        'status': 'unhealthy',
                        'error': str(e)
                    }
            
            # Determine overall status
            if health_status['database_status'] != 'healthy':
                health_status['container_status'] = 'unhealthy'
            elif any(s['status'] != 'healthy' for s in health_status['services'].values()):
                health_status['container_status'] = 'degraded'
                
        except Exception as e:
            health_status['container_status'] = 'unhealthy'
            health_status['error'] = str(e)
            self.logger.error(f"Service container health check failed: {e}")
        
        return health_status
    
    def get_statistics(self) -> dict:
        """Get statistics from all services."""
        stats = {
            'summary': {},
            'details': {}
        }
        
        try:
            services = self.get_all_services()
            total_materials = 0
            
            for service_name, service in services.items():
                try:
                    service_stats = getattr(service, f'get_{service_name.replace("_", "_")}_statistics', None)
                    if service_stats:
                        service_data = service_stats()
                        stats['details'][service_name] = service_data
                        
                        # Extract total count for summary
                        total_key = f'total_{service_name.replace("_", "_")}'
                        if total_key in service_data:
                            total_materials += service_data[total_key]
                    else:
                        # Fallback to basic count
                        count = service.get_count()
                        stats['details'][service_name] = {'total': count}
                        total_materials += count
                        
                except Exception as e:
                    stats['details'][service_name] = {'error': str(e)}
                    self.logger.warning(f"Failed to get statistics for {service_name}: {e}")
            
            stats['summary']['total_materials'] = total_materials
            stats['summary']['service_count'] = len(services)
            
        except Exception as e:
            stats['error'] = str(e)
            self.logger.error(f"Failed to get service statistics: {e}")
        
        return stats
    
    def reset_services(self):
        """Reset all service instances (useful for testing)."""
        self._config_manager = None
        self._directories_service = None
        self._file_operations_service = None
        self._export_service = None
        self._operation_service = None
        self._cement_service = None
        self._fly_ash_service = None
        self._slag_service = None
        self._inert_filler_service = None
        self._mix_service = None
        self._aggregate_service = None
        self._microstructure_service = None
        self._grading_service = None
        self.logger.info("All service instances reset")


# Global service container instance
service_container = ServiceContainer()


def get_service_container(db_service: DatabaseService = None) -> ServiceContainer:
    """Get the global service container instance."""
    if db_service:
        return ServiceContainer(db_service)
    return service_container
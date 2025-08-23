#!/usr/bin/env python3
"""
VCCTL Window Panels

Contains UI panels for different application sections.
"""

from .materials_panel import MaterialsPanel
from .mix_design_panel import MixDesignPanel
from .aggregate_panel import AggregatePanel
from .microstructure_panel import MicrostructurePanel
from .hydration_panel import HydrationPanel
from .elastic_moduli_panel import ElasticModuliPanel
from .file_management_panel import FileManagementPanel
from .operations_monitoring_panel import OperationsMonitoringPanel
from .results_panel import ResultsPanel

__all__ = [
    'MaterialsPanel',
    'MixDesignPanel', 
    'AggregatePanel',
    'MicrostructurePanel',
    'HydrationPanel',
    'ElasticModuliPanel',
    'FileManagementPanel',
    'OperationsMonitoringPanel',
    'ResultsPanel'
]
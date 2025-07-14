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
from .file_management_panel import FileManagementPanel
from .operations_monitoring_panel import OperationsMonitoringPanel

__all__ = [
    'MaterialsPanel',
    'MixDesignPanel', 
    'AggregatePanel',
    'MicrostructurePanel',
    'HydrationPanel',
    'FileManagementPanel',
    'OperationsMonitoringPanel'
]
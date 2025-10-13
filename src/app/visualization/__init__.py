#!/usr/bin/env python3
"""
VCCTL Visualization Module

Provides comprehensive data visualization capabilities including:
- 2D plotting with matplotlib
- 3D microstructure visualization
- Interactive plot controls
- Export functionality
"""

from .plot_manager import PlotManager
from .plot_widgets import (
    HydrationPlotWidget,
    ParticleSizeDistributionWidget,
    MicrostructurePlotWidget,
    CustomPlotWidget
)
from .plot_types import PlotType, PlotStyle, ExportFormat
from .visualization_3d import Microstructure3DViewer
from .plot_export import PlotExporter

# Optional PyVista import - 3D visualization features may not be available
try:
    from .pyvista_3d_viewer import PyVistaViewer3D
    PYVISTA_AVAILABLE = True
except ImportError:
    PyVistaViewer3D = None
    PYVISTA_AVAILABLE = False

__all__ = [
    'PlotManager',
    'HydrationPlotWidget',
    'ParticleSizeDistributionWidget',
    'MicrostructurePlotWidget',
    'CustomPlotWidget',
    'PlotType',
    'PlotStyle',
    'ExportFormat',
    'Microstructure3DViewer',
    'PyVistaViewer3D',
    'PlotExporter',
    'PYVISTA_AVAILABLE'
]

def create_visualization_manager(main_window):
    """Create and configure the visualization system."""
    plot_manager = PlotManager(main_window)
    plot_exporter = PlotExporter()
    
    return plot_manager, plot_exporter
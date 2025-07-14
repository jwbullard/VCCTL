#!/usr/bin/env python3
"""
Plot types and configuration for VCCTL visualization
"""

from enum import Enum
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


class PlotType(Enum):
    """Types of plots available in VCCTL."""
    HYDRATION_CURVE = "hydration_curve"
    PARTICLE_SIZE_DISTRIBUTION = "particle_size_distribution"
    MICROSTRUCTURE_2D = "microstructure_2d"
    MICROSTRUCTURE_3D = "microstructure_3d"
    DEGREE_OF_HYDRATION = "degree_of_hydration"
    POROSITY_EVOLUTION = "porosity_evolution"
    STRENGTH_DEVELOPMENT = "strength_development"
    HEAT_EVOLUTION = "heat_evolution"
    PHASE_COMPOSITION = "phase_composition"
    CUSTOM = "custom"


class PlotStyle(Enum):
    """Plot styling options."""
    SCIENTIFIC = "scientific"
    PRESENTATION = "presentation"
    PUBLICATION = "publication"
    DARK_MODE = "dark_mode"
    COLORBLIND_FRIENDLY = "colorblind_friendly"


class ExportFormat(Enum):
    """Supported export formats."""
    PNG = "png"
    PDF = "pdf"
    SVG = "svg"
    EPS = "eps"
    JPEG = "jpeg"
    TIFF = "tiff"
    CSV = "csv"
    EXCEL = "xlsx"


@dataclass
class PlotConfiguration:
    """Configuration for a plot."""
    plot_type: PlotType
    title: str
    x_label: str
    y_label: str
    style: PlotStyle = PlotStyle.SCIENTIFIC
    grid: bool = True
    legend: bool = True
    interactive: bool = True
    export_formats: List[ExportFormat] = None
    custom_settings: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.export_formats is None:
            self.export_formats = [ExportFormat.PNG, ExportFormat.PDF]
        if self.custom_settings is None:
            self.custom_settings = {}


class PlotThemes:
    """Predefined plot themes."""
    
    SCIENTIFIC = {
        'figure.figsize': (8, 6),
        'font.size': 12,
        'axes.labelsize': 12,
        'axes.titlesize': 14,
        'xtick.labelsize': 10,
        'ytick.labelsize': 10,
        'legend.fontsize': 10,
        'lines.linewidth': 2,
        'axes.grid': True,
        'grid.alpha': 0.3,
        'axes.spines.top': False,
        'axes.spines.right': False,
    }
    
    PRESENTATION = {
        'figure.figsize': (10, 7),
        'font.size': 14,
        'axes.labelsize': 16,
        'axes.titlesize': 18,
        'xtick.labelsize': 12,
        'ytick.labelsize': 12,
        'legend.fontsize': 12,
        'lines.linewidth': 3,
        'axes.grid': True,
        'grid.alpha': 0.3,
    }
    
    PUBLICATION = {
        'figure.figsize': (6, 4),
        'font.size': 10,
        'font.family': 'serif',
        'axes.labelsize': 11,
        'axes.titlesize': 12,
        'xtick.labelsize': 9,
        'ytick.labelsize': 9,
        'legend.fontsize': 9,
        'lines.linewidth': 1.5,
        'axes.grid': False,
        'axes.spines.top': False,
        'axes.spines.right': False,
    }
    
    DARK_MODE = {
        'figure.figsize': (8, 6),
        'figure.facecolor': '#2E3440',
        'axes.facecolor': '#3B4252',
        'axes.edgecolor': '#D8DEE9',
        'axes.labelcolor': '#E5E9F0',
        'text.color': '#E5E9F0',
        'xtick.color': '#E5E9F0',
        'ytick.color': '#E5E9F0',
        'grid.color': '#4C566A',
        'lines.linewidth': 2,
    }
    
    COLORBLIND_FRIENDLY = {
        'figure.figsize': (8, 6),
        'axes.prop_cycle': 'cycler("color", ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"])',
        'lines.linewidth': 2,
        'lines.markersize': 8,
    }


def get_plot_config(plot_type: PlotType) -> PlotConfiguration:
    """Get default configuration for a plot type."""
    
    configs = {
        PlotType.HYDRATION_CURVE: PlotConfiguration(
            plot_type=PlotType.HYDRATION_CURVE,
            title="Cement Hydration Progress",
            x_label="Time (days)",
            y_label="Degree of Hydration"
        ),
        
        PlotType.PARTICLE_SIZE_DISTRIBUTION: PlotConfiguration(
            plot_type=PlotType.PARTICLE_SIZE_DISTRIBUTION,
            title="Particle Size Distribution", 
            x_label="Particle Size (μm)",
            y_label="Cumulative Passing (%)"
        ),
        
        PlotType.MICROSTRUCTURE_2D: PlotConfiguration(
            plot_type=PlotType.MICROSTRUCTURE_2D,
            title="2D Microstructure",
            x_label="X Position (μm)",
            y_label="Y Position (μm)"
        ),
        
        PlotType.DEGREE_OF_HYDRATION: PlotConfiguration(
            plot_type=PlotType.DEGREE_OF_HYDRATION,
            title="Degree of Hydration vs Time",
            x_label="Time (days)",
            y_label="Degree of Hydration (-)"
        ),
        
        PlotType.POROSITY_EVOLUTION: PlotConfiguration(
            plot_type=PlotType.POROSITY_EVOLUTION,
            title="Porosity Evolution",
            x_label="Time (days)",
            y_label="Porosity (-)"
        ),
        
        PlotType.STRENGTH_DEVELOPMENT: PlotConfiguration(
            plot_type=PlotType.STRENGTH_DEVELOPMENT,
            title="Strength Development",
            x_label="Time (days)",
            y_label="Compressive Strength (MPa)"
        ),
        
        PlotType.HEAT_EVOLUTION: PlotConfiguration(
            plot_type=PlotType.HEAT_EVOLUTION,
            title="Heat of Hydration",
            x_label="Time (hours)",
            y_label="Heat Evolution Rate (J/g/h)"
        ),
        
        PlotType.PHASE_COMPOSITION: PlotConfiguration(
            plot_type=PlotType.PHASE_COMPOSITION,
            title="Phase Composition",
            x_label="Time (days)",
            y_label="Phase Volume Fraction"
        ),
    }
    
    return configs.get(plot_type, PlotConfiguration(
        plot_type=PlotType.CUSTOM,
        title="Custom Plot",
        x_label="X Axis",
        y_label="Y Axis"
    ))


def apply_plot_style(ax, style: PlotStyle):
    """Apply a plot style to matplotlib axes."""
    import matplotlib.pyplot as plt
    
    if style == PlotStyle.SCIENTIFIC:
        plt.rcParams.update(PlotThemes.SCIENTIFIC)
    elif style == PlotStyle.PRESENTATION:
        plt.rcParams.update(PlotThemes.PRESENTATION)
    elif style == PlotStyle.PUBLICATION:
        plt.rcParams.update(PlotThemes.PUBLICATION)
    elif style == PlotStyle.DARK_MODE:
        plt.rcParams.update(PlotThemes.DARK_MODE)
    elif style == PlotStyle.COLORBLIND_FRIENDLY:
        plt.rcParams.update(PlotThemes.COLORBLIND_FRIENDLY)
    
    # Apply grid settings
    if style != PlotStyle.PUBLICATION:
        ax.grid(True, alpha=0.3)
    
    # Apply spine settings for cleaner look
    if style in [PlotStyle.SCIENTIFIC, PlotStyle.PUBLICATION]:
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
"""
Elastic Results Visualizer

Creates visualizations for elastic moduli calculation results including
charts, graphs, and property displays.
"""

import logging
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from .elastic_results_parser import ElasticModuliResults


class ElasticResultsVisualizer:
    """Creates visualizations for elastic moduli results."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.figure_size = (10, 8)
        
    def create_moduli_summary_chart(self, results: ElasticModuliResults) -> Optional[Figure]:
        """
        Create a bar chart summarizing the main elastic moduli.
        
        Args:
            results: ElasticModuliResults object with parsed data
            
        Returns:
            matplotlib Figure object or None if creation fails
        """
        try:
            fig, ax = plt.subplots(figsize=self.figure_size)
            
            # Prepare data for bar chart
            moduli_names = []
            moduli_values = []
            
            if results.bulk_modulus is not None:
                moduli_names.append('Bulk Modulus\n(K)')
                moduli_values.append(results.bulk_modulus)
            
            if results.shear_modulus is not None:
                moduli_names.append('Shear Modulus\n(G)')
                moduli_values.append(results.shear_modulus)
            
            if results.youngs_modulus is not None:
                moduli_names.append("Young's Modulus\n(E)")
                moduli_values.append(results.youngs_modulus)
            
            if not moduli_values:
                self.logger.warning("No moduli data available for visualization")
                return None
            
            # Create bar chart
            colors = ['#2E86AB', '#A23B72', '#F18F01']
            bars = ax.bar(moduli_names, moduli_values, color=colors[:len(moduli_values)])
            
            # Customize chart
            ax.set_ylabel('Modulus (GPa)', fontsize=12)
            ax.set_title(f'Elastic Moduli Summary - {results.operation_name}', fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3, axis='y')
            
            # Add value labels on bars
            for i, (bar, value) in enumerate(zip(bars, moduli_values)):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                       f'{value:.2f}', ha='center', va='bottom', fontweight='bold')
            
            # Add Poisson's ratio as text if available
            if results.poissons_ratio is not None:
                ax.text(0.02, 0.98, f"Poisson's Ratio (ν): {results.poissons_ratio:.3f}", 
                       transform=ax.transAxes, verticalalignment='top',
                       bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
            
            plt.tight_layout()
            return fig
            
        except Exception as e:
            self.logger.error(f"Error creating moduli summary chart: {e}")
            return None
    
    def create_phase_contributions_chart(self, results: ElasticModuliResults) -> Optional[Figure]:
        """
        Create visualization of phase contributions to elastic properties.
        
        Args:
            results: ElasticModuliResults object with phase data
            
        Returns:
            matplotlib Figure object or None if creation fails
        """
        try:
            if not results.phase_contributions or not results.volume_fractions:
                self.logger.warning("No phase contribution data available for visualization")
                return None
            
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
            
            # Volume fractions pie chart
            phases = list(results.volume_fractions.keys())
            fractions = list(results.volume_fractions.values())
            
            # Generate colors
            colors = plt.cm.Set3(np.linspace(0, 1, len(phases)))
            
            wedges, texts, autotexts = ax1.pie(fractions, labels=phases, colors=colors, 
                                              autopct='%1.1f%%', startangle=90)
            ax1.set_title('Phase Volume Fractions', fontsize=12, fontweight='bold')
            
            # Make percentage text bold
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
            
            # Phase contributions bar chart
            if results.phase_contributions:
                phases_with_data = []
                bulk_contributions = []
                shear_contributions = []
                
                for phase, contrib_data in results.phase_contributions.items():
                    if 'bulk_contribution' in contrib_data or 'shear_contribution' in contrib_data:
                        phases_with_data.append(phase)
                        bulk_contributions.append(contrib_data.get('bulk_contribution', 0))
                        shear_contributions.append(contrib_data.get('shear_contribution', 0))
                
                if phases_with_data:
                    x = np.arange(len(phases_with_data))
                    width = 0.35
                    
                    bars1 = ax2.bar(x - width/2, bulk_contributions, width, label='Bulk Modulus', 
                                   color='#2E86AB', alpha=0.8)
                    bars2 = ax2.bar(x + width/2, shear_contributions, width, label='Shear Modulus', 
                                   color='#A23B72', alpha=0.8)
                    
                    ax2.set_xlabel('Phase', fontsize=11)
                    ax2.set_ylabel('Contribution (GPa)', fontsize=11)
                    ax2.set_title('Phase Contributions to Moduli', fontsize=12, fontweight='bold')
                    ax2.set_xticks(x)
                    ax2.set_xticklabels(phases_with_data, rotation=45, ha='right')
                    ax2.legend()
                    ax2.grid(True, alpha=0.3, axis='y')
                    
                    # Add value labels on bars
                    for bars in [bars1, bars2]:
                        for bar in bars:
                            height = bar.get_height()
                            if height > 0:
                                ax2.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                                        f'{height:.1f}', ha='center', va='bottom', fontsize=9)
            
            plt.tight_layout()
            return fig
            
        except Exception as e:
            self.logger.error(f"Error creating phase contributions chart: {e}")
            return None
    
    def create_itz_properties_chart(self, results: ElasticModuliResults) -> Optional[Figure]:
        """
        Create visualization of ITZ properties if available.
        
        Args:
            results: ElasticModuliResults object with ITZ data
            
        Returns:
            matplotlib Figure object or None if creation fails
        """
        try:
            if not results.itz_properties or 'layer_data' not in results.itz_properties:
                # Create simple ITZ summary if we have bulk data
                if results.itz_bulk_modulus is not None or results.itz_shear_modulus is not None:
                    return self._create_simple_itz_chart(results)
                else:
                    self.logger.warning("No ITZ property data available for visualization")
                    return None
            
            fig, ax = plt.subplots(figsize=self.figure_size)
            
            layer_data = results.itz_properties['layer_data']
            layers = [item['layer'] for item in layer_data]
            bulk_moduli = [item['bulk_modulus'] for item in layer_data]
            shear_moduli = [item['shear_modulus'] for item in layer_data]
            
            # Create line plot for layer-by-layer ITZ properties
            ax.plot(layers, bulk_moduli, 'o-', color='#2E86AB', linewidth=2, 
                   markersize=6, label='Bulk Modulus (K)')
            ax.plot(layers, shear_moduli, 's-', color='#A23B72', linewidth=2, 
                   markersize=6, label='Shear Modulus (G)')
            
            ax.set_xlabel('ITZ Layer', fontsize=12)
            ax.set_ylabel('Modulus (GPa)', fontsize=12)
            ax.set_title(f'ITZ Properties by Layer - {results.operation_name}', 
                        fontsize=14, fontweight='bold')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            # Add overall ITZ values as horizontal lines if available
            if results.itz_bulk_modulus is not None:
                ax.axhline(y=results.itz_bulk_modulus, color='#2E86AB', 
                          linestyle='--', alpha=0.7, label=f'Average ITZ K: {results.itz_bulk_modulus:.2f}')
            
            if results.itz_shear_modulus is not None:
                ax.axhline(y=results.itz_shear_modulus, color='#A23B72', 
                          linestyle='--', alpha=0.7, label=f'Average ITZ G: {results.itz_shear_modulus:.2f}')
            
            plt.tight_layout()
            return fig
            
        except Exception as e:
            self.logger.error(f"Error creating ITZ properties chart: {e}")
            return None
    
    def _create_simple_itz_chart(self, results: ElasticModuliResults) -> Optional[Figure]:
        """Create a simple ITZ summary chart."""
        try:
            fig, ax = plt.subplots(figsize=(8, 6))
            
            values = []
            labels = []
            
            if results.itz_bulk_modulus is not None:
                values.append(results.itz_bulk_modulus)
                labels.append('ITZ Bulk\nModulus')
            
            if results.itz_shear_modulus is not None:
                values.append(results.itz_shear_modulus)
                labels.append('ITZ Shear\nModulus')
            
            if values:
                colors = ['#2E86AB', '#A23B72']
                bars = ax.bar(labels, values, color=colors[:len(values)])
                
                ax.set_ylabel('Modulus (GPa)', fontsize=12)
                ax.set_title(f'ITZ Properties Summary - {results.operation_name}', 
                            fontsize=14, fontweight='bold')
                ax.grid(True, alpha=0.3, axis='y')
                
                # Add value labels on bars
                for bar, value in zip(bars, values):
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                           f'{value:.2f}', ha='center', va='bottom', fontweight='bold')
            
            plt.tight_layout()
            return fig
            
        except Exception as e:
            self.logger.error(f"Error creating simple ITZ chart: {e}")
            return None
    
    def create_comparison_chart(self, results_list: List[ElasticModuliResults]) -> Optional[Figure]:
        """
        Create comparison chart for multiple elastic results.
        
        Args:
            results_list: List of ElasticModuliResults objects to compare
            
        Returns:
            matplotlib Figure object or None if creation fails
        """
        try:
            if len(results_list) < 2:
                self.logger.warning("Need at least 2 results for comparison")
                return None
            
            fig, ax = plt.subplots(figsize=(12, 8))
            
            operation_names = [result.operation_name for result in results_list]
            bulk_moduli = [result.bulk_modulus for result in results_list]
            shear_moduli = [result.shear_modulus for result in results_list]
            
            x = np.arange(len(operation_names))
            width = 0.35
            
            bars1 = ax.bar(x - width/2, bulk_moduli, width, label='Bulk Modulus (K)', 
                          color='#2E86AB', alpha=0.8)
            bars2 = ax.bar(x + width/2, shear_moduli, width, label='Shear Modulus (G)', 
                          color='#A23B72', alpha=0.8)
            
            ax.set_xlabel('Operation', fontsize=12)
            ax.set_ylabel('Modulus (GPa)', fontsize=12)
            ax.set_title('Elastic Moduli Comparison', fontsize=14, fontweight='bold')
            ax.set_xticks(x)
            ax.set_xticklabels(operation_names, rotation=45, ha='right')
            ax.legend()
            ax.grid(True, alpha=0.3, axis='y')
            
            # Add value labels on bars
            for bars in [bars1, bars2]:
                for bar in bars:
                    height = bar.get_height()
                    if height is not None and height > 0:
                        ax.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                               f'{height:.1f}', ha='center', va='bottom', fontsize=9)
            
            plt.tight_layout()
            return fig
            
        except Exception as e:
            self.logger.error(f"Error creating comparison chart: {e}")
            return None
    
    def create_gtk_widget(self, figure: Figure) -> Gtk.Widget:
        """
        Create a GTK widget containing the matplotlib figure.
        
        Args:
            figure: matplotlib Figure object
            
        Returns:
            GTK widget containing the figure
        """
        try:
            canvas = FigureCanvas(figure)
            canvas.set_size_request(800, 600)
            
            # Create scrolled window
            scrolled = Gtk.ScrolledWindow()
            scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
            scrolled.add(canvas)
            
            return scrolled
            
        except Exception as e:
            self.logger.error(f"Error creating GTK widget: {e}")
            return Gtk.Label("Error creating visualization")


def create_elastic_results_visualizer() -> ElasticResultsVisualizer:
    """Factory function to create an ElasticResultsVisualizer instance."""
    return ElasticResultsVisualizer()
#!/usr/bin/env python3
"""
Plot Export Functionality for VCCTL

Handles exporting plots to various formats including raster and vector formats,
as well as data export capabilities.
"""

import matplotlib.pyplot as plt
import matplotlib.backends.backend_pdf as pdf_backend
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import logging
import json

from .plot_types import ExportFormat


class PlotExporter:
    """
    Handles exporting plots and data to various formats.
    
    Features:
    - Multiple raster formats (PNG, JPEG, TIFF)
    - Vector formats (PDF, SVG, EPS)
    - Data export (CSV, Excel, JSON)
    - High-resolution export
    - Batch export capabilities
    """
    
    def __init__(self):
        self.logger = logging.getLogger('VCCTL.PlotExporter')
        
        # Default export settings
        self.default_dpi = 300
        self.default_quality = 95  # For JPEG
        self.default_transparency = True  # For PNG
        
        # Supported formats
        self.raster_formats = {'png', 'jpg', 'jpeg', 'tiff', 'tif'}
        self.vector_formats = {'pdf', 'svg', 'eps', 'ps'}
        self.data_formats = {'csv', 'xlsx', 'json', 'txt'}
    
    def export_figure(self, figure, file_path: str, format_type: str = None,
                     dpi: int = None, **kwargs) -> bool:
        """
        Export matplotlib figure to file.
        
        Args:
            figure: Matplotlib figure object
            file_path: Output file path
            format_type: Export format (auto-detected if None)
            dpi: Resolution for raster formats
            **kwargs: Additional export parameters
            
        Returns:
            Success status
        """
        try:
            file_path = Path(file_path)
            
            # Auto-detect format from extension
            if format_type is None:
                format_type = file_path.suffix.lower().lstrip('.')
            
            # Validate format
            if not self._is_supported_format(format_type):
                self.logger.error(f"Unsupported format: {format_type}")
                return False
            
            # Set DPI
            if dpi is None:
                dpi = self.default_dpi
            
            # Prepare export parameters
            export_params = self._get_export_params(format_type, dpi, **kwargs)
            
            # Export figure
            figure.savefig(str(file_path), **export_params)
            
            self.logger.info(f"Figure exported to: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export figure: {e}")
            return False
    
    def export_plot_data(self, plot_data: Dict[str, Any], file_path: str,
                        format_type: str = None) -> bool:
        """
        Export plot data to file.
        
        Args:
            plot_data: Plot data dictionary
            file_path: Output file path
            format_type: Export format
            
        Returns:
            Success status
        """
        try:
            file_path = Path(file_path)
            
            # Auto-detect format from extension
            if format_type is None:
                format_type = file_path.suffix.lower().lstrip('.')
            
            # Validate data format
            if format_type not in self.data_formats:
                self.logger.error(f"Unsupported data format: {format_type}")
                return False
            
            # Export based on format
            if format_type == 'csv':
                return self._export_csv(plot_data, file_path)
            elif format_type == 'xlsx':
                return self._export_excel(plot_data, file_path)
            elif format_type == 'json':
                return self._export_json(plot_data, file_path)
            elif format_type == 'txt':
                return self._export_text(plot_data, file_path)
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to export plot data: {e}")
            return False
    
    def batch_export(self, figures: List[tuple], output_dir: str,
                    formats: List[str] = None, **kwargs) -> Dict[str, bool]:
        """
        Export multiple figures in batch.
        
        Args:
            figures: List of (figure, filename) tuples
            output_dir: Output directory
            formats: List of formats to export
            **kwargs: Export parameters
            
        Returns:
            Dictionary of export results
        """
        if formats is None:
            formats = ['png', 'pdf']
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        results = {}
        
        for figure, filename in figures:
            for format_type in formats:
                file_path = output_dir / f"{filename}.{format_type}"
                success = self.export_figure(figure, str(file_path), format_type, **kwargs)
                results[str(file_path)] = success
        
        return results
    
    def create_publication_figure(self, figure, title: str = None,
                                caption: str = None) -> plt.Figure:
        """
        Create publication-ready figure with proper formatting.
        
        Args:
            figure: Source figure
            title: Figure title
            caption: Figure caption
            
        Returns:
            Publication-ready figure
        """
        # Create new figure with publication settings
        pub_fig = plt.figure(figsize=(6, 4), dpi=300)
        
        # Copy axes from source figure
        source_axes = figure.get_axes()
        if source_axes:
            ax = source_axes[0]
            
            # Create new axes with same data
            new_ax = pub_fig.add_subplot(111)
            
            # Copy plot elements
            for line in ax.get_lines():
                new_ax.plot(line.get_xdata(), line.get_ydata(),
                          color=line.get_color(), linewidth=line.get_linewidth(),
                          linestyle=line.get_linestyle(), label=line.get_label())
            
            # Copy formatting
            new_ax.set_xlabel(ax.get_xlabel())
            new_ax.set_ylabel(ax.get_ylabel())
            new_ax.set_xlim(ax.get_xlim())
            new_ax.set_ylim(ax.get_ylim())
            
            if title:
                new_ax.set_title(title)
            
            # Publication formatting
            new_ax.grid(True, alpha=0.3)
            new_ax.spines['top'].set_visible(False)
            new_ax.spines['right'].set_visible(False)
            
            if ax.get_legend():
                new_ax.legend()
        
        plt.tight_layout()
        return pub_fig
    
    def _is_supported_format(self, format_type: str) -> bool:
        """Check if format is supported."""
        format_type = format_type.lower()
        return (format_type in self.raster_formats or 
                format_type in self.vector_formats or
                format_type in self.data_formats)
    
    def _get_export_params(self, format_type: str, dpi: int, **kwargs) -> Dict[str, Any]:
        """Get export parameters for specific format."""
        params = {
            'dpi': dpi,
            'bbox_inches': 'tight',
            'pad_inches': 0.1,
        }
        
        format_type = format_type.lower()
        
        if format_type == 'png':
            params.update({
                'transparent': kwargs.get('transparent', self.default_transparency),
                'facecolor': kwargs.get('facecolor', 'white'),
            })
        
        elif format_type in ['jpg', 'jpeg']:
            params.update({
                'quality': kwargs.get('quality', self.default_quality),
                'facecolor': kwargs.get('facecolor', 'white'),
            })
        
        elif format_type == 'pdf':
            params.update({
                'facecolor': kwargs.get('facecolor', 'white'),
                'metadata': kwargs.get('metadata', {
                    'Title': 'VCCTL Plot',
                    'Author': 'VCCTL',
                    'Creator': 'VCCTL Scientific Software',
                })
            })
        
        elif format_type == 'svg':
            params.update({
                'facecolor': kwargs.get('facecolor', 'white'),
                'metadata': kwargs.get('metadata', {})
            })
        
        elif format_type in ['eps', 'ps']:
            params.update({
                'facecolor': kwargs.get('facecolor', 'white'),
            })
        
        return params
    
    def _export_csv(self, plot_data: Dict[str, Any], file_path: Path) -> bool:
        """Export data to CSV format."""
        try:
            # Convert plot data to DataFrame
            df = self._plot_data_to_dataframe(plot_data)
            
            # Export to CSV
            df.to_csv(file_path, index=False)
            
            self.logger.info(f"Data exported to CSV: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export CSV: {e}")
            return False
    
    def _export_excel(self, plot_data: Dict[str, Any], file_path: Path) -> bool:
        """Export data to Excel format."""
        try:
            # Convert plot data to DataFrame
            df = self._plot_data_to_dataframe(plot_data)
            
            # Export to Excel with formatting
            with pd.ExcelWriter(file_path, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='Plot Data', index=False)
                
                # Get workbook and worksheet
                workbook = writer.book
                worksheet = writer.sheets['Plot Data']
                
                # Add formatting
                header_format = workbook.add_format({
                    'bold': True,
                    'text_wrap': True,
                    'valign': 'top',
                    'fg_color': '#D7E4BC',
                    'border': 1
                })
                
                # Apply header formatting
                for col_num, column_name in enumerate(df.columns):
                    worksheet.write(0, col_num, column_name, header_format)
                    
                # Auto-adjust column widths
                for col_num, column_name in enumerate(df.columns):
                    column_width = max(len(column_name), df[column_name].astype(str).str.len().max())
                    worksheet.set_column(col_num, col_num, min(column_width + 2, 30))
            
            self.logger.info(f"Data exported to Excel: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export Excel: {e}")
            return False
    
    def _export_json(self, plot_data: Dict[str, Any], file_path: Path) -> bool:
        """Export data to JSON format."""
        try:
            # Convert numpy arrays to lists for JSON serialization
            json_data = self._prepare_data_for_json(plot_data)
            
            # Export to JSON with pretty formatting
            with open(file_path, 'w') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Data exported to JSON: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export JSON: {e}")
            return False
    
    def _export_text(self, plot_data: Dict[str, Any], file_path: Path) -> bool:
        """Export data to text format."""
        try:
            with open(file_path, 'w') as f:
                f.write("VCCTL Plot Data Export\n")
                f.write("=" * 30 + "\n\n")
                
                # Write metadata
                if 'type' in plot_data:
                    f.write(f"Plot Type: {plot_data['type']}\n")
                if 'timestamp' in plot_data:
                    f.write(f"Export Time: {plot_data['timestamp']}\n")
                
                f.write("\nData:\n")
                f.write("-" * 20 + "\n")
                
                # Write data based on type
                plot_type = plot_data.get('type', '')
                
                if 'hydration' in plot_type:
                    self._write_hydration_data(f, plot_data)
                elif 'particle_size' in plot_type:
                    self._write_psd_data(f, plot_data)
                else:
                    self._write_generic_data(f, plot_data)
            
            self.logger.info(f"Data exported to text: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export text: {e}")
            return False
    
    def _plot_data_to_dataframe(self, plot_data: Dict[str, Any]) -> pd.DataFrame:
        """Convert plot data to pandas DataFrame."""
        plot_type = plot_data.get('type', '')
        
        if 'hydration' in plot_type:
            return pd.DataFrame({
                'Time (days)': plot_data.get('time', []),
                'Degree of Hydration': plot_data.get('hydration', [])
            })
        
        elif 'particle_size' in plot_type:
            return pd.DataFrame({
                'Particle Size (μm)': plot_data.get('size', []),
                'Cumulative Passing (%)': plot_data.get('passing', [])
            })
        
        elif 'series' in plot_data:
            # Multiple series data
            df_data = {}
            for i, series in enumerate(plot_data['series']):
                label = series.get('label', f'Series {i+1}')
                df_data[f'{label}_X'] = series.get('x', [])
                df_data[f'{label}_Y'] = series.get('y', [])
            
            return pd.DataFrame(df_data)
        
        else:
            # Generic data
            return pd.DataFrame(plot_data)
    
    def _prepare_data_for_json(self, data: Any) -> Any:
        """Prepare data for JSON serialization."""
        if isinstance(data, dict):
            return {key: self._prepare_data_for_json(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._prepare_data_for_json(item) for item in data]
        elif isinstance(data, np.ndarray):
            return data.tolist()
        elif isinstance(data, np.generic):
            return data.item()
        else:
            return data
    
    def _write_hydration_data(self, f, plot_data: Dict[str, Any]):
        """Write hydration data to text file."""
        time_data = plot_data.get('time', [])
        hydration_data = plot_data.get('hydration', [])
        
        f.write("Time (days)\tDegree of Hydration\n")
        for t, h in zip(time_data, hydration_data):
            f.write(f"{t:.3f}\t{h:.6f}\n")
    
    def _write_psd_data(self, f, plot_data: Dict[str, Any]):
        """Write particle size distribution data to text file."""
        size_data = plot_data.get('size', [])
        passing_data = plot_data.get('passing', [])
        
        f.write("Particle Size (μm)\tCumulative Passing (%)\n")
        for s, p in zip(size_data, passing_data):
            f.write(f"{s:.3f}\t{p:.2f}\n")
    
    def _write_generic_data(self, f, plot_data: Dict[str, Any]):
        """Write generic data to text file."""
        for key, value in plot_data.items():
            if key == 'type':
                continue
            
            f.write(f"{key}: ")
            if isinstance(value, (list, np.ndarray)):
                f.write(f"[{len(value)} values]\n")
                for i, v in enumerate(value[:10]):  # Show first 10 values
                    f.write(f"  {i}: {v}\n")
                if len(value) > 10:
                    f.write(f"  ... and {len(value) - 10} more values\n")
            else:
                f.write(f"{value}\n")
            f.write("\n")
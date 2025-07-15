"""
Material Analyzer Plugin for VCCTL
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg as FigureCanvas
from matplotlib.figure import Figure
from pathlib import Path
from typing import Dict, Any, List
import json

import sys
sys.path.append(str(Path(__file__).parent.parent.parent / 'src'))

from plugins.plugin_interface import PluginInterface
from plugins.plugin_context import PluginContext


class MaterialAnalyzerPlugin(PluginInterface):
    """Plugin for analyzing material properties"""
    
    def __init__(self):
        self.context = None
        self.analysis_panel = None
    
    def get_name(self) -> str:
        return "Material Analyzer"
    
    def get_version(self) -> str:
        return "10.0.0"
    
    def get_description(self) -> str:
        return "Plugin for analyzing material properties and generating reports"
    
    def get_author(self) -> str:
        return "VCCTL Team"
    
    def initialize(self, context: PluginContext) -> None:
        """Initialize the plugin"""
        self.context = context
        
        # Add menu item
        self.context.add_menu_item(
            "Tools/Material Analysis...",
            self.show_analysis_dialog,
            "Material Analysis"
        )
        
        # Add analysis panel
        self.analysis_panel = MaterialAnalysisPanel(self)
        self.context.add_panel(
            "material_analysis",
            self.analysis_panel,
            "Material Analysis"
        )
        
        print(f"[{self.get_name()}] Plugin initialized successfully")
    
    def destroy(self) -> None:
        """Clean up plugin resources"""
        if self.analysis_panel:
            self.analysis_panel.destroy()
        print(f"[{self.get_name()}] Plugin destroyed")
    
    def is_compatible(self, vcctl_version: str) -> bool:
        """Check if plugin is compatible with VCCTL version"""
        return vcctl_version >= "10.0.0"
    
    def get_metadata(self) -> Dict[str, Any]:
        """Return additional plugin metadata"""
        return {
            "category": "analysis",
            "keywords": ["material", "analysis", "properties", "report"],
            "license": "MIT"
        }
    
    def get_operation_handlers(self) -> Dict[str, Any]:
        """Return operation handlers provided by this plugin"""
        return {
            "analyze_material": self.handle_material_analysis,
            "generate_report": self.handle_report_generation
        }
    
    def show_analysis_dialog(self, *args):
        """Show the analysis dialog"""
        dialog = AnalysisDialog(self.context.main_window, self)
        dialog.show_all()
    
    def handle_material_analysis(self, operation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle material analysis operation"""
        try:
            material_id = operation_data.get("material_id")
            analysis_type = operation_data.get("analysis_type", "particle_size_distribution")
            
            # Get material data (placeholder)
            material_data = self._get_material_data(material_id)
            
            # Perform analysis
            if analysis_type == "particle_size_distribution":
                results = self._analyze_particle_size_distribution(material_data)
            elif analysis_type == "chemical_composition":
                results = self._analyze_chemical_composition(material_data)
            elif analysis_type == "phase_analysis":
                results = self._analyze_phase_composition(material_data)
            else:
                raise ValueError(f"Unknown analysis type: {analysis_type}")
            
            return {
                "success": True,
                "material_id": material_id,
                "analysis_type": analysis_type,
                "results": results
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def handle_report_generation(self, operation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle report generation operation"""
        try:
            analysis_results = operation_data.get("analysis_results", {})
            report_format = operation_data.get("format", "html")
            output_path = operation_data.get("output_path")
            
            report_content = self._generate_report(analysis_results, report_format)
            
            if output_path:
                with open(output_path, 'w') as f:
                    f.write(report_content)
            
            return {
                "success": True,
                "report_content": report_content,
                "output_path": output_path
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _get_material_data(self, material_id: str) -> Dict[str, Any]:
        """Get material data (placeholder implementation)"""
        return {
            "id": material_id,
            "name": f"Material {material_id}",
            "type": "cement",
            "particle_sizes": np.random.lognormal(3, 0.5, 1000),
            "chemical_composition": {
                "SiO2": 21.5,
                "Al2O3": 4.8,
                "Fe2O3": 3.2,
                "CaO": 64.1,
                "MgO": 1.9,
                "SO3": 2.1,
                "K2O": 0.8,
                "Na2O": 0.2
            },
            "phases": {
                "C3S": 55.0,
                "C2S": 18.0,
                "C3A": 8.0,
                "C4AF": 10.0,
                "Gypsum": 5.0,
                "Other": 4.0
            }
        }
    
    def _analyze_particle_size_distribution(self, material_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze particle size distribution"""
        particle_sizes = material_data.get("particle_sizes", [])
        
        if len(particle_sizes) == 0:
            return {"error": "No particle size data available"}
        
        # Calculate statistics
        d10 = np.percentile(particle_sizes, 10)
        d50 = np.percentile(particle_sizes, 50)
        d90 = np.percentile(particle_sizes, 90)
        mean_size = np.mean(particle_sizes)
        std_size = np.std(particle_sizes)
        
        # Calculate specific surface area (simplified Blaine estimate)
        specific_surface = 3000 / mean_size  # cm²/g
        
        return {
            "d10": float(d10),
            "d50": float(d50),
            "d90": float(d90),
            "mean_size": float(mean_size),
            "std_size": float(std_size),
            "specific_surface": float(specific_surface),
            "particle_count": len(particle_sizes)
        }
    
    def _analyze_chemical_composition(self, material_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze chemical composition"""
        composition = material_data.get("chemical_composition", {})
        
        if not composition:
            return {"error": "No chemical composition data available"}
        
        # Calculate key ratios
        sio2 = composition.get("SiO2", 0)
        al2o3 = composition.get("Al2O3", 0)
        fe2o3 = composition.get("Fe2O3", 0)
        cao = composition.get("CaO", 0)
        
        silica_ratio = sio2 / (al2o3 + fe2o3) if (al2o3 + fe2o3) > 0 else 0
        alumina_ratio = al2o3 / fe2o3 if fe2o3 > 0 else 0
        lime_saturation = cao / (2.8 * sio2 + 1.18 * al2o3 + 0.65 * fe2o3) if sio2 > 0 else 0
        
        return {
            "composition": composition,
            "silica_ratio": float(silica_ratio),
            "alumina_ratio": float(alumina_ratio),
            "lime_saturation": float(lime_saturation),
            "total_percentage": sum(composition.values())
        }
    
    def _analyze_phase_composition(self, material_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze phase composition"""
        phases = material_data.get("phases", {})
        
        if not phases:
            return {"error": "No phase composition data available"}
        
        # Calculate phase ratios
        c3s = phases.get("C3S", 0)
        c2s = phases.get("C2S", 0)
        c3a = phases.get("C3A", 0)
        c4af = phases.get("C4AF", 0)
        
        silicate_content = c3s + c2s
        aluminate_content = c3a + c4af
        hydraulic_ratio = silicate_content / aluminate_content if aluminate_content > 0 else 0
        
        return {
            "phases": phases,
            "silicate_content": float(silicate_content),
            "aluminate_content": float(aluminate_content),
            "hydraulic_ratio": float(hydraulic_ratio),
            "total_percentage": sum(phases.values())
        }
    
    def _generate_report(self, analysis_results: Dict[str, Any], format_type: str) -> str:
        """Generate analysis report"""
        if format_type == "html":
            return self._generate_html_report(analysis_results)
        elif format_type == "json":
            return json.dumps(analysis_results, indent=2)
        else:
            return str(analysis_results)
    
    def _generate_html_report(self, analysis_results: Dict[str, Any]) -> str:
        """Generate HTML report"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Material Analysis Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                table { border-collapse: collapse; width: 100%; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
                .header { color: #333; }
            </style>
        </head>
        <body>
            <h1 class="header">Material Analysis Report</h1>
        """
        
        for analysis_type, results in analysis_results.items():
            html += f"<h2>{analysis_type.replace('_', ' ').title()}</h2>"
            html += "<table>"
            
            for key, value in results.items():
                if isinstance(value, dict):
                    html += f"<tr><th colspan='2'>{key}</th></tr>"
                    for sub_key, sub_value in value.items():
                        html += f"<tr><td>{sub_key}</td><td>{sub_value}</td></tr>"
                else:
                    html += f"<tr><td>{key}</td><td>{value}</td></tr>"
            
            html += "</table><br>"
        
        html += "</body></html>"
        return html


class MaterialAnalysisPanel(Gtk.Box):
    """Material analysis panel widget"""
    
    def __init__(self, plugin):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.plugin = plugin
        self.set_margin_top(10)
        self.set_margin_bottom(10)
        self.set_margin_left(10)
        self.set_margin_right(10)
        
        self._create_ui()
    
    def _create_ui(self):
        """Create the panel UI"""
        # Title
        title_label = Gtk.Label()
        title_label.set_markup("<b>Material Analysis</b>")
        title_label.set_halign(Gtk.Align.START)
        self.pack_start(title_label, False, False, 0)
        
        # Material selection
        material_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        material_label = Gtk.Label("Material:")
        material_box.pack_start(material_label, False, False, 0)
        
        self.material_combo = Gtk.ComboBoxText()
        self.material_combo.append_text("Sample Material 1")
        self.material_combo.append_text("Sample Material 2")
        self.material_combo.append_text("Sample Material 3")
        self.material_combo.set_active(0)
        material_box.pack_start(self.material_combo, True, True, 0)
        
        self.pack_start(material_box, False, False, 0)
        
        # Analysis type selection
        analysis_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        analysis_label = Gtk.Label("Analysis Type:")
        analysis_box.pack_start(analysis_label, False, False, 0)
        
        self.analysis_combo = Gtk.ComboBoxText()
        self.analysis_combo.append_text("Particle Size Distribution")
        self.analysis_combo.append_text("Chemical Composition")
        self.analysis_combo.append_text("Phase Analysis")
        self.analysis_combo.set_active(0)
        analysis_box.pack_start(self.analysis_combo, True, True, 0)
        
        self.pack_start(analysis_box, False, False, 0)
        
        # Analyze button
        analyze_button = Gtk.Button("Analyze Material")
        analyze_button.connect("clicked", self._on_analyze_clicked)
        self.pack_start(analyze_button, False, False, 0)
        
        # Results area
        results_frame = Gtk.Frame()
        results_frame.set_label("Analysis Results")
        
        self.results_textview = Gtk.TextView()
        self.results_textview.set_editable(False)
        
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.add(self.results_textview)
        
        results_frame.add(scrolled)
        self.pack_start(results_frame, True, True, 0)
    
    def _on_analyze_clicked(self, button):
        """Handle analyze button click"""
        material_name = self.material_combo.get_active_text()
        analysis_type = self.analysis_combo.get_active_text()
        
        # Map display names to internal names
        analysis_map = {
            "Particle Size Distribution": "particle_size_distribution",
            "Chemical Composition": "chemical_composition",
            "Phase Analysis": "phase_analysis"
        }
        
        analysis_type_internal = analysis_map.get(analysis_type, "particle_size_distribution")
        
        # Perform analysis
        operation_data = {
            "material_id": material_name,
            "analysis_type": analysis_type_internal
        }
        
        result = self.plugin.handle_material_analysis(operation_data)
        
        # Display results
        if result.get("success"):
            results_text = self._format_results(result.get("results", {}))
        else:
            results_text = f"Analysis failed: {result.get('error', 'Unknown error')}"
        
        buffer = self.results_textview.get_buffer()
        buffer.set_text(results_text)
    
    def _format_results(self, results: Dict[str, Any]) -> str:
        """Format analysis results for display"""
        formatted = ""
        
        for key, value in results.items():
            if isinstance(value, dict):
                formatted += f"{key.replace('_', ' ').title()}:\n"
                for sub_key, sub_value in value.items():
                    formatted += f"  {sub_key}: {sub_value}\n"
            else:
                formatted += f"{key.replace('_', ' ').title()}: {value}\n"
        
        return formatted


class AnalysisDialog(Gtk.Dialog):
    """Material analysis dialog"""
    
    def __init__(self, parent_window, plugin):
        super().__init__("Material Analysis", parent_window, 0,
                         (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                          Gtk.STOCK_OK, Gtk.ResponseType.OK))
        
        self.plugin = plugin
        self.set_default_size(500, 400)
        self.set_modal(True)
        
        self._create_ui()
    
    def _create_ui(self):
        """Create the dialog UI"""
        content_area = self.get_content_area()
        content_area.set_spacing(10)
        content_area.set_margin_top(10)
        content_area.set_margin_bottom(10)
        content_area.set_margin_left(10)
        content_area.set_margin_right(10)
        
        # Add analysis panel
        self.analysis_panel = MaterialAnalysisPanel(self.plugin)
        content_area.pack_start(self.analysis_panel, True, True, 0)
        
        # Connect response
        self.connect("response", self._on_response)
    
    def _on_response(self, dialog, response_id):
        """Handle dialog response"""
        self.destroy()
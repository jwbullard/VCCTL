"""
Example Data Export Plugin for VCCTL
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

import json
import csv
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List

import sys
sys.path.append(str(Path(__file__).parent.parent.parent / 'src'))

from plugins.plugin_interface import PluginInterface
from plugins.plugin_context import PluginContext


class DataExportPlugin(PluginInterface):
    """Example plugin that demonstrates data export functionality"""
    
    def __init__(self):
        self.context = None
        self.export_dialog = None
    
    def get_name(self) -> str:
        return "Data Export Plugin"
    
    def get_version(self) -> str:
        return "10.0.0"
    
    def get_description(self) -> str:
        return "Example plugin that demonstrates data export functionality"
    
    def get_author(self) -> str:
        return "VCCTL Team"
    
    def initialize(self, context: PluginContext) -> None:
        """Initialize the plugin"""
        self.context = context
        
        # Add menu item
        self.context.add_menu_item(
            "File/Export/Advanced Export...",
            self.show_export_dialog,
            "Advanced Export"
        )
        
        # Add toolbar button
        self.context.add_toolbar_button(
            "export_data",
            self.quick_export,
            "Export Data",
            "document-save"
        )
        
        print(f"[{self.get_name()}] Plugin initialized successfully")
    
    def destroy(self) -> None:
        """Clean up plugin resources"""
        if self.export_dialog:
            self.export_dialog.destroy()
        print(f"[{self.get_name()}] Plugin destroyed")
    
    def is_compatible(self, vcctl_version: str) -> bool:
        """Check if plugin is compatible with VCCTL version"""
        # Simple version check - in real implementation, use proper version parsing
        return vcctl_version >= "10.0.0"
    
    def get_metadata(self) -> Dict[str, Any]:
        """Return additional plugin metadata"""
        return {
            "category": "data_processing",
            "keywords": ["export", "data", "csv", "excel", "json"],
            "license": "MIT",
            "homepage": "https://github.com/vcctl/plugins"
        }
    
    def get_operation_handlers(self) -> Dict[str, Any]:
        """Return operation handlers provided by this plugin"""
        return {
            "export_data": self.handle_export_operation
        }
    
    def show_export_dialog(self, *args):
        """Show the export dialog"""
        if self.export_dialog:
            self.export_dialog.present()
            return
        
        self.export_dialog = ExportDialog(self.context.main_window, self)
        self.export_dialog.show_all()
    
    def quick_export(self, *args):
        """Quick export with default settings"""
        try:
            # Get current data (placeholder - would get from actual data source)
            data = self._get_current_data()
            
            # Export to default format
            default_format = self.context.get_config("plugins.data_export", "default_format") or "csv"
            output_path = Path.home() / "vcctl_export" / f"data.{default_format}"
            output_path.parent.mkdir(exist_ok=True)
            
            if self._export_data(data, output_path, default_format):
                self.context.show_message(f"Data exported to {output_path}", "info")
            else:
                self.context.show_message("Export failed", "error")
                
        except Exception as e:
            self.context.show_message(f"Export error: {e}", "error")
    
    def handle_export_operation(self, operation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle export operation"""
        try:
            data = operation_data.get("data", [])
            format_type = operation_data.get("format", "csv")
            output_path = Path(operation_data.get("output_path", "export.csv"))
            
            success = self._export_data(data, output_path, format_type)
            
            return {
                "success": success,
                "output_path": str(output_path),
                "format": format_type,
                "record_count": len(data) if data else 0
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _get_current_data(self) -> List[Dict[str, Any]]:
        """Get current data for export (placeholder implementation)"""
        # In a real implementation, this would get data from the application
        return [
            {"id": 1, "name": "Sample Mix 1", "water_cement_ratio": 0.45, "strength": 25.5},
            {"id": 2, "name": "Sample Mix 2", "water_cement_ratio": 0.40, "strength": 28.2},
            {"id": 3, "name": "Sample Mix 3", "water_cement_ratio": 0.50, "strength": 22.8},
        ]
    
    def _export_data(self, data: List[Dict[str, Any]], output_path: Path, format_type: str) -> bool:
        """Export data to specified format"""
        try:
            if format_type == "csv":
                return self._export_csv(data, output_path)
            elif format_type == "xlsx":
                return self._export_xlsx(data, output_path)
            elif format_type == "json":
                return self._export_json(data, output_path)
            else:
                raise ValueError(f"Unsupported format: {format_type}")
                
        except Exception as e:
            print(f"Export error: {e}")
            return False
    
    def _export_csv(self, data: List[Dict[str, Any]], output_path: Path) -> bool:
        """Export data to CSV format"""
        if not data:
            return False
        
        with open(output_path, 'w', newline='') as csvfile:
            fieldnames = data[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        
        return True
    
    def _export_xlsx(self, data: List[Dict[str, Any]], output_path: Path) -> bool:
        """Export data to Excel format"""
        if not data:
            return False
        
        df = pd.DataFrame(data)
        df.to_excel(output_path, index=False)
        return True
    
    def _export_json(self, data: List[Dict[str, Any]], output_path: Path) -> bool:
        """Export data to JSON format"""
        with open(output_path, 'w') as jsonfile:
            json.dump(data, jsonfile, indent=2)
        
        return True


class ExportDialog(Gtk.Dialog):
    """Export configuration dialog"""
    
    def __init__(self, parent_window, plugin):
        super().__init__("Data Export", parent_window, 0,
                         (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                          Gtk.STOCK_OK, Gtk.ResponseType.OK))
        
        self.plugin = plugin
        self.set_default_size(400, 300)
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
        
        # Format selection
        format_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        format_label = Gtk.Label("Export Format:")
        format_box.pack_start(format_label, False, False, 0)
        
        self.format_combo = Gtk.ComboBoxText()
        self.format_combo.append_text("CSV")
        self.format_combo.append_text("Excel (XLSX)")
        self.format_combo.append_text("JSON")
        self.format_combo.set_active(0)
        format_box.pack_start(self.format_combo, True, True, 0)
        
        content_area.pack_start(format_box, False, False, 0)
        
        # Output file selection
        file_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        file_label = Gtk.Label("Output File:")
        file_box.pack_start(file_label, False, False, 0)
        
        self.file_entry = Gtk.Entry()
        self.file_entry.set_text(str(Path.home() / "vcctl_export.csv"))
        file_box.pack_start(self.file_entry, True, True, 0)
        
        browse_button = Gtk.Button("Browse...")
        browse_button.connect("clicked", self._on_browse_clicked)
        file_box.pack_start(browse_button, False, False, 0)
        
        content_area.pack_start(file_box, False, False, 0)
        
        # Options
        options_frame = Gtk.Frame()
        options_frame.set_label("Options")
        options_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        options_box.set_margin_top(10)
        options_box.set_margin_bottom(10)
        options_box.set_margin_left(10)
        options_box.set_margin_right(10)
        
        self.include_metadata_check = Gtk.CheckButton("Include metadata")
        self.include_metadata_check.set_active(True)
        options_box.pack_start(self.include_metadata_check, False, False, 0)
        
        self.include_timestamp_check = Gtk.CheckButton("Include timestamp")
        self.include_timestamp_check.set_active(True)
        options_box.pack_start(self.include_timestamp_check, False, False, 0)
        
        options_frame.add(options_box)
        content_area.pack_start(options_frame, False, False, 0)
        
        # Connect response
        self.connect("response", self._on_response)
    
    def _on_browse_clicked(self, button):
        """Handle browse button click"""
        dialog = Gtk.FileChooserDialog(
            "Select Output File",
            self,
            Gtk.FileChooserAction.SAVE,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_SAVE, Gtk.ResponseType.OK)
        )
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            self.file_entry.set_text(filename)
        
        dialog.destroy()
    
    def _on_response(self, dialog, response_id):
        """Handle dialog response"""
        if response_id == Gtk.ResponseType.OK:
            # Get selected options
            format_text = self.format_combo.get_active_text()
            format_map = {
                "CSV": "csv",
                "Excel (XLSX)": "xlsx",
                "JSON": "json"
            }
            format_type = format_map.get(format_text, "csv")
            
            output_path = Path(self.file_entry.get_text())
            
            # Perform export
            try:
                data = self.plugin._get_current_data()
                success = self.plugin._export_data(data, output_path, format_type)
                
                if success:
                    self.plugin.context.show_message(f"Data exported successfully to {output_path}", "info")
                else:
                    self.plugin.context.show_message("Export failed", "error")
                    
            except Exception as e:
                self.plugin.context.show_message(f"Export error: {e}", "error")
        
        self.destroy()
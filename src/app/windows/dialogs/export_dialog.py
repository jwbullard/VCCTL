#!/usr/bin/env python3
"""
Export Dialog for VCCTL

Provides comprehensive export options including PDF reports, Excel spreadsheets,
JSON/XML data export, custom templates, and batch operations.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, GLib

import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
import threading

from app.services.service_container import get_service_container
from app.services.export_service import ExportFormat


class ExportDialog(Gtk.Dialog):
    """
    Advanced export dialog with multiple format options and templates.
    """
    
    __gsignals__ = {
        'export-started': (GObject.SIGNAL_RUN_FIRST, None, ()),
        'export-completed': (GObject.SIGNAL_RUN_FIRST, None, (bool, str)),
        'export-progress': (GObject.SIGNAL_RUN_FIRST, None, (int,)),
    }
    
    def __init__(self, parent, project_data: Dict[str, Any]):
        super().__init__(
            title="Export Project Data",
            parent=parent,
            flags=Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT
        )
        
        self.project_data = project_data
        self.logger = logging.getLogger('VCCTL.ExportDialog')
        self.service_container = get_service_container()
        self.export_service = self.service_container.export_service
        
        # Export settings
        self.selected_formats = []
        self.selected_template = 'comprehensive'
        self.output_directory = Path.home() / 'VCCTL_Exports'
        self.include_plots = True
        self.include_charts = True
        
        # Setup dialog
        self.set_default_size(600, 500)
        self.set_resizable(True)
        
        # Add buttons
        self.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
        self.export_button = self.add_button("Export", Gtk.ResponseType.OK)
        self.export_button.get_style_context().add_class(Gtk.STYLE_CLASS_SUGGESTED_ACTION)
        
        # Create UI
        self._create_ui()
        self._connect_signals()
        
        # Update UI state
        self._update_export_button_state()
        
        self.show_all()
    
    def _create_ui(self):
        """Create dialog UI."""
        content_area = self.get_content_area()
        content_area.set_spacing(12)
        content_area.set_margin_top(12)
        content_area.set_margin_bottom(12)
        content_area.set_margin_left(12)
        content_area.set_margin_right(12)
        
        # Main container
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content_area.pack_start(main_box, True, True, 0)
        
        # Title
        title_label = Gtk.Label()
        title_label.set_markup("<b>Export Project Data</b>")
        title_label.set_halign(Gtk.Align.START)
        main_box.pack_start(title_label, False, False, 0)
        
        # Create sections
        self._create_format_selection(main_box)
        self._create_template_selection(main_box)
        self._create_output_selection(main_box)
        self._create_options_selection(main_box)
        self._create_progress_section(main_box)
    
    def _create_format_selection(self, parent):
        """Create format selection section."""
        frame = Gtk.Frame(label="Export Formats")
        frame.set_label_align(0.02, 0.5)
        parent.pack_start(frame, False, False, 0)
        
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox.set_margin_top(12)
        vbox.set_margin_bottom(12)
        vbox.set_margin_left(12)
        vbox.set_margin_right(12)
        frame.add(vbox)
        
        # Format checkboxes
        self.format_checks = {}
        
        formats = [
            (ExportFormat.PDF, "PDF Report", "Comprehensive PDF report with formatted layout"),
            (ExportFormat.EXCEL, "Excel Spreadsheet", "Multi-sheet Excel workbook with charts"),
            (ExportFormat.JSON, "JSON Data", "Machine-readable JSON format"),
            (ExportFormat.XML, "XML Data", "Structured XML format"),
            (ExportFormat.ZIP, "Complete Archive", "ZIP file containing all formats")
        ]
        
        for format_type, label, description in formats:
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            
            check = Gtk.CheckButton(label)
            check.set_tooltip_text(description)
            check.connect('toggled', self._on_format_toggled, format_type)
            self.format_checks[format_type] = check
            
            hbox.pack_start(check, False, False, 0)
            
            desc_label = Gtk.Label(description)
            desc_label.set_halign(Gtk.Align.START)
            desc_label.get_style_context().add_class(Gtk.STYLE_CLASS_DIM_LABEL)
            hbox.pack_start(desc_label, True, True, 0)
            
            vbox.pack_start(hbox, False, False, 0)
        
        # Select all / none buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        button_box.set_halign(Gtk.Align.END)
        
        select_all_btn = Gtk.Button("Select All")
        select_all_btn.connect('clicked', self._on_select_all_formats)
        button_box.pack_start(select_all_btn, False, False, 0)
        
        select_none_btn = Gtk.Button("Select None")
        select_none_btn.connect('clicked', self._on_select_none_formats)
        button_box.pack_start(select_none_btn, False, False, 0)
        
        vbox.pack_start(button_box, False, False, 0)
        
        # Default selection
        self.format_checks[ExportFormat.PDF].set_active(True)
        self.format_checks[ExportFormat.EXCEL].set_active(True)
    
    def _create_template_selection(self, parent):
        """Create template selection section."""
        frame = Gtk.Frame(label="Report Template")
        frame.set_label_align(0.02, 0.5)
        parent.pack_start(frame, False, False, 0)
        
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox.set_margin_top(12)
        vbox.set_margin_bottom(12)
        vbox.set_margin_left(12)
        vbox.set_margin_right(12)
        frame.add(vbox)
        
        # Template description
        desc_label = Gtk.Label("Choose a report template that determines which sections to include:")
        desc_label.set_halign(Gtk.Align.START)
        desc_label.set_line_wrap(True)
        vbox.pack_start(desc_label, False, False, 0)
        
        # Template combo
        self.template_combo = Gtk.ComboBoxText()
        
        templates = self.export_service.get_available_templates()
        for template_key, template in templates.items():
            self.template_combo.append(template_key, f"{template.name} - {template.description}")
        
        self.template_combo.set_active_id('comprehensive')
        self.template_combo.connect('changed', self._on_template_changed)
        
        vbox.pack_start(self.template_combo, False, False, 0)
        
        # Template details
        self.template_details = Gtk.Label()
        self.template_details.set_halign(Gtk.Align.START)
        self.template_details.set_line_wrap(True)
        self.template_details.get_style_context().add_class(Gtk.STYLE_CLASS_DIM_LABEL)
        vbox.pack_start(self.template_details, False, False, 0)
        
        self._update_template_details()
    
    def _create_output_selection(self, parent):
        """Create output directory selection."""
        frame = Gtk.Frame(label="Output Location")
        frame.set_label_align(0.02, 0.5)
        parent.pack_start(frame, False, False, 0)
        
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox.set_margin_top(12)
        vbox.set_margin_bottom(12)
        vbox.set_margin_left(12)
        vbox.set_margin_right(12)
        frame.add(vbox)
        
        # Directory chooser
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        
        self.dir_entry = Gtk.Entry()
        self.dir_entry.set_text(str(self.output_directory))
        self.dir_entry.set_hexpand(True)
        hbox.pack_start(self.dir_entry, True, True, 0)
        
        browse_btn = Gtk.Button("Browse...")
        browse_btn.connect('clicked', self._on_browse_output_directory)
        hbox.pack_start(browse_btn, False, False, 0)
        
        vbox.pack_start(hbox, False, False, 0)
        
        # File naming
        naming_label = Gtk.Label("Files will be named based on the project name:")
        naming_label.set_halign(Gtk.Align.START)
        naming_label.get_style_context().add_class(Gtk.STYLE_CLASS_DIM_LABEL)
        vbox.pack_start(naming_label, False, False, 0)
        
        project_name = self.project_data.get('project_name', 'vcctl_project').replace(' ', '_')
        example_label = Gtk.Label(f"Example: {project_name}.pdf, {project_name}.xlsx")
        example_label.set_halign(Gtk.Align.START)
        example_label.get_style_context().add_class(Gtk.STYLE_CLASS_DIM_LABEL)
        vbox.pack_start(example_label, False, False, 0)
    
    def _create_options_selection(self, parent):
        """Create export options."""
        frame = Gtk.Frame(label="Export Options")
        frame.set_label_align(0.02, 0.5)
        parent.pack_start(frame, False, False, 0)
        
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox.set_margin_top(12)
        vbox.set_margin_bottom(12)
        vbox.set_margin_left(12)
        vbox.set_margin_right(12)
        frame.add(vbox)
        
        # Include plots
        self.plots_check = Gtk.CheckButton("Include plots and visualizations")
        self.plots_check.set_active(True)
        self.plots_check.set_tooltip_text("Include generated plots in PDF reports")
        vbox.pack_start(self.plots_check, False, False, 0)
        
        # Include charts in Excel
        self.charts_check = Gtk.CheckButton("Include charts in Excel")
        self.charts_check.set_active(True)
        self.charts_check.set_tooltip_text("Generate charts in Excel spreadsheets")
        vbox.pack_start(self.charts_check, False, False, 0)
        
        # Open after export
        self.open_check = Gtk.CheckButton("Open output directory after export")
        self.open_check.set_active(True)
        vbox.pack_start(self.open_check, False, False, 0)
    
    def _create_progress_section(self, parent):
        """Create progress section."""
        self.progress_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        parent.pack_start(self.progress_box, False, False, 0)
        
        # Progress bar
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_show_text(True)
        self.progress_bar.set_no_show_all(True)
        self.progress_box.pack_start(self.progress_bar, False, False, 0)
        
        # Status label
        self.status_label = Gtk.Label()
        self.status_label.set_halign(Gtk.Align.START)
        self.status_label.set_no_show_all(True)
        self.progress_box.pack_start(self.status_label, False, False, 0)
    
    def _connect_signals(self):
        """Connect dialog signals."""
        self.connect('response', self._on_response)
        self.dir_entry.connect('changed', self._on_output_directory_changed)
    
    def _on_format_toggled(self, check_button, format_type):
        """Handle format checkbox toggle."""
        if check_button.get_active():
            if format_type not in self.selected_formats:
                self.selected_formats.append(format_type)
        else:
            if format_type in self.selected_formats:
                self.selected_formats.remove(format_type)
        
        self._update_export_button_state()
    
    def _on_select_all_formats(self, button):
        """Select all export formats."""
        for check in self.format_checks.values():
            check.set_active(True)
    
    def _on_select_none_formats(self, button):
        """Deselect all export formats."""
        for check in self.format_checks.values():
            check.set_active(False)
    
    def _on_template_changed(self, combo):
        """Handle template selection change."""
        self.selected_template = combo.get_active_id()
        self._update_template_details()
    
    def _update_template_details(self):
        """Update template details display."""
        templates = self.export_service.get_available_templates()
        if self.selected_template in templates:
            template = templates[self.selected_template]
            sections_text = ", ".join(template.sections)
            self.template_details.set_text(f"Sections: {sections_text}")
    
    def _on_browse_output_directory(self, button):
        """Handle output directory browse."""
        dialog = Gtk.FileChooserDialog(
            title="Select Output Directory",
            parent=self,
            action=Gtk.FileChooserAction.SELECT_FOLDER
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )
        
        dialog.set_current_folder(str(self.output_directory))
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.output_directory = Path(dialog.get_filename())
            self.dir_entry.set_text(str(self.output_directory))
        
        dialog.destroy()
    
    def _on_output_directory_changed(self, entry):
        """Handle output directory text change."""
        self.output_directory = Path(entry.get_text())
        self._update_export_button_state()
    
    def _update_export_button_state(self):
        """Update export button sensitivity."""
        can_export = (len(self.selected_formats) > 0 and 
                     self.output_directory and 
                     len(str(self.output_directory).strip()) > 0)
        self.export_button.set_sensitive(can_export)
    
    def _on_response(self, dialog, response_id):
        """Handle dialog response."""
        if response_id == Gtk.ResponseType.OK:
            self._start_export()
        else:
            self.destroy()
    
    def _start_export(self):
        """Start the export process."""
        # Update options
        self.include_plots = self.plots_check.get_active()
        self.include_charts = self.charts_check.get_active()
        
        # Show progress
        self.progress_bar.show()
        self.status_label.show()
        self.status_label.set_text("Starting export...")
        
        # Disable export button
        self.export_button.set_sensitive(False)
        
        # Emit signal
        self.emit('export-started')
        
        # Start export in background thread
        thread = threading.Thread(target=self._perform_export, daemon=True)
        thread.start()
    
    def _perform_export(self):
        """Perform export in background thread."""
        try:
            # Update progress
            GLib.idle_add(self._update_progress, 10, "Preparing data...")
            
            # Ensure output directory exists
            self.output_directory.mkdir(parents=True, exist_ok=True)
            
            # Update progress
            GLib.idle_add(self._update_progress, 20, "Exporting data...")
            
            # Perform batch export
            results = self.export_service.batch_export(
                self.project_data,
                self.output_directory,
                self.selected_formats,
                self.selected_template
            )
            
            # Update progress
            GLib.idle_add(self._update_progress, 90, "Finalizing...")
            
            # Check results
            success_count = sum(1 for success in results.values() if success)
            total_count = len(results)
            
            success = success_count == total_count
            message = f"Exported {success_count}/{total_count} formats successfully"
            
            if not success:
                failed_formats = [fmt for fmt, result in results.items() if not result]
                message += f". Failed: {', '.join(failed_formats)}"
            
            # Complete
            GLib.idle_add(self._complete_export, success, message)
            
        except Exception as e:
            error_msg = f"Export failed: {str(e)}"
            self.logger.error(error_msg)
            GLib.idle_add(self._complete_export, False, error_msg)
    
    def _update_progress(self, percentage: int, status: str):
        """Update progress display."""
        self.progress_bar.set_fraction(percentage / 100.0)
        self.progress_bar.set_text(f"{percentage}%")
        self.status_label.set_text(status)
        self.emit('export-progress', percentage)
    
    def _complete_export(self, success: bool, message: str):
        """Complete export process."""
        self.progress_bar.set_fraction(1.0)
        self.progress_bar.set_text("100%")
        self.status_label.set_text(message)
        
        # Emit completion signal
        self.emit('export-completed', success, message)
        
        # Show completion message
        if success:
            dialog = Gtk.MessageDialog(
                parent=self,
                flags=Gtk.DialogFlags.MODAL,
                type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                message_format="Export Completed Successfully"
            )
            dialog.format_secondary_text(
                f"{message}\n\nFiles exported to: {self.output_directory}"
            )
        else:
            dialog = Gtk.MessageDialog(
                parent=self,
                flags=Gtk.DialogFlags.MODAL,
                type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                message_format="Export Failed"
            )
            dialog.format_secondary_text(message)
        
        dialog.run()
        dialog.destroy()
        
        # Open output directory if requested
        if success and self.open_check.get_active():
            self._open_output_directory()
        
        # Close dialog
        self.destroy()
    
    def _open_output_directory(self):
        """Open output directory in file manager."""
        try:
            import subprocess
            import platform
            
            system = platform.system()
            if system == "Darwin":  # macOS
                subprocess.run(["open", str(self.output_directory)])
            elif system == "Windows":
                subprocess.run(["explorer", str(self.output_directory)])
            else:  # Linux
                subprocess.run(["xdg-open", str(self.output_directory)])
                
        except Exception as e:
            self.logger.warning(f"Could not open output directory: {e}")


def show_export_dialog(parent, project_data: Dict[str, Any]) -> ExportDialog:
    """
    Show export dialog.
    
    Args:
        parent: Parent window
        project_data: Project data to export
        
    Returns:
        Export dialog instance
    """
    dialog = ExportDialog(parent, project_data)
    return dialog
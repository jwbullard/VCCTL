#!/usr/bin/env python3
"""
File Operations Dialog for VCCTL

Provides dialogs for import/export operations with progress tracking,
format selection, and batch processing capabilities.
"""

import gi
import logging
import threading
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Dict, List, Callable, Any, Tuple
from enum import Enum
import time

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, GLib, Pango

if TYPE_CHECKING:
    from app.windows.main_window import VCCTLMainWindow

from app.services.service_container import get_service_container


class OperationType(Enum):
    """Type of file operation."""
    IMPORT = "import"
    EXPORT = "export"
    BATCH_IMPORT = "batch_import"
    BATCH_EXPORT = "batch_export"


class FileFormat(Enum):
    """Supported file formats."""
    JSON = ("json", "JSON Files", "*.json")
    CSV = ("csv", "CSV Files", "*.csv")
    XML = ("xml", "XML Files", "*.xml")
    ALL = ("all", "All Supported", "*.json;*.csv;*.xml")


class FileOperationDialog(Gtk.Dialog):
    """
    Dialog for file import/export operations with progress tracking.
    
    Features:
    - Format selection
    - Progress tracking with cancellation
    - Batch operations
    - Validation and error reporting
    - Preview capabilities
    """
    
    def __init__(self, main_window: 'VCCTLMainWindow', operation_type: OperationType,
                 title: str = None, initial_directory: Path = None):
        """Initialize the file operation dialog."""
        
        if title is None:
            title = f"File {operation_type.value.title()}"
        
        super().__init__(
            title=title,
            transient_for=main_window,
            flags=Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT
        )
        
        self.main_window = main_window
        self.operation_type = operation_type
        self.logger = logging.getLogger('VCCTL.FileOperationDialog')
        self.service_container = get_service_container()
        self.file_ops_service = self.service_container.file_operations_service
        
        # Dialog state
        self.initial_directory = initial_directory or Path.home()
        self.selected_files = []
        self.selected_format = FileFormat.JSON
        self.operation_thread = None
        self.operation_cancelled = False
        self.results = None
        
        # Progress tracking
        self.progress_callback = None
        self.completion_callback = None
        
        # Setup dialog
        self._setup_dialog()
        self._setup_ui()
        self._connect_signals()
        
        self.logger.info(f"File operation dialog initialized: {operation_type.value}")
    
    def _setup_dialog(self) -> None:
        """Setup dialog properties and buttons."""
        self.set_default_size(600, 500)
        self.set_resizable(True)
        
        # Add buttons based on operation type
        if self.operation_type in [OperationType.IMPORT, OperationType.BATCH_IMPORT]:
            self.add_button("Cancel", Gtk.ResponseType.CANCEL)
            self.import_button = self.add_button("Import", Gtk.ResponseType.OK)
            self.import_button.set_sensitive(False)
            self.set_default_response(Gtk.ResponseType.OK)
        else:
            self.add_button("Cancel", Gtk.ResponseType.CANCEL)
            self.export_button = self.add_button("Export", Gtk.ResponseType.OK)
            self.export_button.set_sensitive(False)
            self.set_default_response(Gtk.ResponseType.OK)
    
    def _setup_ui(self) -> None:
        """Setup the dialog UI."""
        content_area = self.get_content_area()
        content_area.set_spacing(10)
        content_area.set_margin_left(10)
        content_area.set_margin_right(10)
        content_area.set_margin_top(10)
        content_area.set_margin_bottom(10)
        
        # Create main notebook for different pages
        self.notebook = Gtk.Notebook()
        content_area.pack_start(self.notebook, True, True, 0)
        
        # Create pages
        self._create_file_selection_page()
        self._create_options_page()
        self._create_progress_page()
        
        # Initially show file selection page
        self.notebook.set_current_page(0)
    
    def _create_file_selection_page(self) -> None:
        """Create the file selection page."""
        page_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        page_box.set_margin_left(10)
        page_box.set_margin_right(10)
        page_box.set_margin_top(10)
        page_box.set_margin_bottom(10)
        
        # Title
        if self.operation_type in [OperationType.IMPORT, OperationType.BATCH_IMPORT]:
            title_text = "Select files to import"
        else:
            title_text = "Select export location"
        
        title_label = Gtk.Label()
        title_label.set_markup(f'<span size="large" weight="bold">{title_text}</span>')
        title_label.set_halign(Gtk.Align.START)
        page_box.pack_start(title_label, False, False, 0)
        
        # File chooser
        if self.operation_type == OperationType.BATCH_IMPORT:
            self.file_chooser = Gtk.FileChooserWidget(action=Gtk.FileChooserAction.SELECT_FOLDER)
        elif self.operation_type in [OperationType.IMPORT]:
            self.file_chooser = Gtk.FileChooserWidget(action=Gtk.FileChooserAction.OPEN)
            self.file_chooser.set_select_multiple(True)
        elif self.operation_type == OperationType.BATCH_EXPORT:
            self.file_chooser = Gtk.FileChooserWidget(action=Gtk.FileChooserAction.SELECT_FOLDER)
        else:  # Single export
            self.file_chooser = Gtk.FileChooserWidget(action=Gtk.FileChooserAction.SAVE)
        
        # Setup file filters
        self._setup_file_filters()
        
        # Set initial directory
        self.file_chooser.set_current_folder(str(self.initial_directory))
        
        page_box.pack_start(self.file_chooser, True, True, 0)
        
        # File info area
        self._create_file_info_area(page_box)
        
        self.notebook.append_page(page_box, Gtk.Label("Files"))
    
    def _create_options_page(self) -> None:
        """Create the options page."""
        page_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        page_box.set_margin_left(10)
        page_box.set_margin_right(10)
        page_box.set_margin_top(10)
        page_box.set_margin_bottom(10)
        
        # Title
        title_label = Gtk.Label()
        title_label.set_markup('<span size="large" weight="bold">Operation Options</span>')
        title_label.set_halign(Gtk.Align.START)
        page_box.pack_start(title_label, False, False, 0)
        
        # Format selection
        self._create_format_selection(page_box)
        
        # Additional options based on operation type
        if self.operation_type in [OperationType.BATCH_IMPORT, OperationType.BATCH_EXPORT]:
            self._create_batch_options(page_box)
        
        if self.operation_type in [OperationType.IMPORT, OperationType.BATCH_IMPORT]:
            self._create_import_options(page_box)
        else:
            self._create_export_options(page_box)
        
        self.notebook.append_page(page_box, Gtk.Label("Options"))
    
    def _create_progress_page(self) -> None:
        """Create the progress tracking page."""
        page_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        page_box.set_margin_left(10)
        page_box.set_margin_right(10)
        page_box.set_margin_top(10)
        page_box.set_margin_bottom(10)
        
        # Title
        title_label = Gtk.Label()
        title_label.set_markup('<span size="large" weight="bold">Operation Progress</span>')
        title_label.set_halign(Gtk.Align.START)
        page_box.pack_start(title_label, False, False, 0)
        
        # Progress bar
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_show_text(True)
        self.progress_bar.set_text("Ready")
        page_box.pack_start(self.progress_bar, False, False, 0)
        
        # Status label
        self.status_label = Gtk.Label("Click Import/Export to begin operation")
        self.status_label.set_halign(Gtk.Align.START)
        self.status_label.set_line_wrap(True)
        page_box.pack_start(self.status_label, False, False, 0)
        
        # Results area (scrolled text view)
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_shadow_type(Gtk.ShadowType.IN)
        
        self.results_buffer = Gtk.TextBuffer()
        self.results_view = Gtk.TextView(buffer=self.results_buffer)
        self.results_view.set_editable(False)
        self.results_view.set_cursor_visible(False)
        scrolled.add(self.results_view)
        
        page_box.pack_start(scrolled, True, True, 0)
        
        # Cancel button (for during operation)
        self.cancel_button = Gtk.Button(label="Cancel Operation")
        self.cancel_button.connect('clicked', self._on_cancel_operation)
        self.cancel_button.set_sensitive(False)
        page_box.pack_start(self.cancel_button, False, False, 0)
        
        self.notebook.append_page(page_box, Gtk.Label("Progress"))
    
    def _create_file_info_area(self, parent: Gtk.Box) -> None:
        """Create file information display area."""
        info_frame = Gtk.Frame(label="Selection Information")
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        info_box.set_margin_left(10)
        info_box.set_margin_right(10)
        info_box.set_margin_top(5)
        info_box.set_margin_bottom(5)
        
        self.selection_info_label = Gtk.Label("No files selected")
        self.selection_info_label.set_halign(Gtk.Align.START)
        info_box.pack_start(self.selection_info_label, False, False, 0)
        
        # Preview area (for single file selection)
        self.preview_expander = Gtk.Expander(label="File Preview")
        self.preview_text = Gtk.TextView()
        self.preview_text.set_editable(False)
        preview_scroll = Gtk.ScrolledWindow()
        preview_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        preview_scroll.add(self.preview_text)
        preview_scroll.set_size_request(-1, 150)
        self.preview_expander.add(preview_scroll)
        info_box.pack_start(self.preview_expander, False, False, 0)
        
        info_frame.add(info_box)
        parent.pack_start(info_frame, False, False, 0)
    
    def _create_format_selection(self, parent: Gtk.Box) -> None:
        """Create format selection controls."""
        format_frame = Gtk.Frame(label="File Format")
        format_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        format_box.set_margin_left(10)
        format_box.set_margin_right(10)
        format_box.set_margin_top(5)
        format_box.set_margin_bottom(5)
        
        # Format radio buttons
        self.format_buttons = {}
        first_button = None
        
        for fmt in [FileFormat.JSON, FileFormat.CSV, FileFormat.XML]:
            if first_button is None:
                button = Gtk.RadioButton(label=fmt.value[1])
                first_button = button
            else:
                button = Gtk.RadioButton.new_from_widget(first_button)
                button.set_label(fmt.value[1])
            
            button.connect('toggled', self._on_format_changed, fmt)
            self.format_buttons[fmt] = button
            format_box.pack_start(button, False, False, 0)
        
        # Set default selection
        self.format_buttons[FileFormat.JSON].set_active(True)
        
        format_frame.add(format_box)
        parent.pack_start(format_frame, False, False, 0)
    
    def _create_batch_options(self, parent: Gtk.Box) -> None:
        """Create batch operation options."""
        batch_frame = Gtk.Frame(label="Batch Options")
        batch_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        batch_box.set_margin_left(10)
        batch_box.set_margin_right(10)
        batch_box.set_margin_top(5)
        batch_box.set_margin_bottom(5)
        
        # Recursive directory processing
        self.recursive_check = Gtk.CheckButton(label="Process subdirectories recursively")
        self.recursive_check.set_active(True)
        batch_box.pack_start(self.recursive_check, False, False, 0)
        
        # Skip errors option
        self.skip_errors_check = Gtk.CheckButton(label="Skip files with errors and continue")
        self.skip_errors_check.set_active(True)
        batch_box.pack_start(self.skip_errors_check, False, False, 0)
        
        # Overwrite existing files
        if self.operation_type == OperationType.BATCH_EXPORT:
            self.overwrite_check = Gtk.CheckButton(label="Overwrite existing files")
            self.overwrite_check.set_active(False)
            batch_box.pack_start(self.overwrite_check, False, False, 0)
        
        batch_frame.add(batch_box)
        parent.pack_start(batch_frame, False, False, 0)
    
    def _create_import_options(self, parent: Gtk.Box) -> None:
        """Create import-specific options."""
        import_frame = Gtk.Frame(label="Import Options")
        import_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        import_box.set_margin_left(10)
        import_box.set_margin_right(10)
        import_box.set_margin_top(5)
        import_box.set_margin_bottom(5)
        
        # Material type selection (for imports)
        type_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        type_label = Gtk.Label("Material Type:")
        type_box.pack_start(type_label, False, False, 0)
        
        self.material_type_combo = Gtk.ComboBoxText()
        self.material_type_combo.append("cement", "Cement")
        self.material_type_combo.append("flyash", "Fly Ash")
        self.material_type_combo.append("slag", "Slag")
        self.material_type_combo.append("aggregate", "Aggregate")
        self.material_type_combo.append("inert_filler", "Inert Filler")
        self.material_type_combo.set_active(0)
        type_box.pack_start(self.material_type_combo, True, True, 0)
        
        import_box.pack_start(type_box, False, False, 0)
        
        # Validation options
        self.validate_check = Gtk.CheckButton(label="Validate imported data")
        self.validate_check.set_active(True)
        import_box.pack_start(self.validate_check, False, False, 0)
        
        # Update existing records
        self.update_existing_check = Gtk.CheckButton(label="Update existing records with same name")
        self.update_existing_check.set_active(False)
        import_box.pack_start(self.update_existing_check, False, False, 0)
        
        import_frame.add(import_box)
        parent.pack_start(import_frame, False, False, 0)
    
    def _create_export_options(self, parent: Gtk.Box) -> None:
        """Create export-specific options."""
        export_frame = Gtk.Frame(label="Export Options")
        export_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        export_box.set_margin_left(10)
        export_box.set_margin_right(10)
        export_box.set_margin_top(5)
        export_box.set_margin_bottom(5)
        
        # Include metadata
        self.include_metadata_check = Gtk.CheckButton(label="Include metadata in export")
        self.include_metadata_check.set_active(True)
        export_box.pack_start(self.include_metadata_check, False, False, 0)
        
        # Pretty formatting (for JSON)
        self.pretty_format_check = Gtk.CheckButton(label="Use pretty formatting (JSON)")
        self.pretty_format_check.set_active(True)
        export_box.pack_start(self.pretty_format_check, False, False, 0)
        
        export_frame.add(export_box)
        parent.pack_start(export_frame, False, False, 0)
    
    def _setup_file_filters(self) -> None:
        """Setup file filters for the file chooser."""
        # Create filters for each format
        for fmt in FileFormat:
            if fmt == FileFormat.ALL:
                continue
            
            filter = Gtk.FileFilter()
            filter.set_name(fmt.value[1])
            filter.add_pattern(fmt.value[2])
            self.file_chooser.add_filter(filter)
        
        # Add "All Files" filter
        all_filter = Gtk.FileFilter()
        all_filter.set_name("All Files")
        all_filter.add_pattern("*")
        self.file_chooser.add_filter(all_filter)
    
    def _connect_signals(self) -> None:
        """Connect dialog signals."""
        # File chooser signals
        self.file_chooser.connect('selection-changed', self._on_file_selection_changed)
        self.file_chooser.connect('file-activated', self._on_file_activated)
        
        # Dialog response
        self.connect('response', self._on_dialog_response)
    
    def _on_file_selection_changed(self, chooser: Gtk.FileChooserWidget) -> None:
        """Handle file selection change."""
        if self.operation_type in [OperationType.IMPORT]:
            filenames = chooser.get_filenames()
            self.selected_files = [Path(f) for f in filenames] if filenames else []
        elif self.operation_type in [OperationType.BATCH_IMPORT, OperationType.BATCH_EXPORT]:
            folder = chooser.get_filename()
            self.selected_files = [Path(folder)] if folder else []
        else:  # Single export
            filename = chooser.get_filename()
            self.selected_files = [Path(filename)] if filename else []
        
        self._update_selection_info()
        self._update_button_sensitivity()
        self._update_preview()
    
    def _on_file_activated(self, chooser: Gtk.FileChooserWidget) -> None:
        """Handle file double-click."""
        if self.selected_files:
            self.response(Gtk.ResponseType.OK)
    
    def _on_format_changed(self, button: Gtk.RadioButton, format: FileFormat) -> None:
        """Handle format selection change."""
        if button.get_active():
            self.selected_format = format
            self._update_file_filters()
    
    def _on_dialog_response(self, dialog: Gtk.Dialog, response_id: int) -> None:
        """Handle dialog response."""
        if response_id == Gtk.ResponseType.OK:
            self._start_operation()
        elif response_id == Gtk.ResponseType.CANCEL:
            if self.operation_thread and self.operation_thread.is_alive():
                self._cancel_operation()
            else:
                self.destroy()
    
    def _on_cancel_operation(self, button: Gtk.Button) -> None:
        """Handle operation cancellation."""
        self._cancel_operation()
    
    def _update_selection_info(self) -> None:
        """Update selection information display."""
        if not self.selected_files:
            self.selection_info_label.set_text("No files selected")
            return
        
        if self.operation_type in [OperationType.BATCH_IMPORT, OperationType.BATCH_EXPORT]:
            directory = self.selected_files[0]
            if directory.is_dir():
                # Count supported files in directory
                file_count = self._count_files_in_directory(directory)
                self.selection_info_label.set_text(
                    f"Directory: {directory.name}\n"
                    f"Contains {file_count} supported files"
                )
            else:
                self.selection_info_label.set_text("Invalid directory selection")
        else:
            if len(self.selected_files) == 1:
                file = self.selected_files[0]
                try:
                    stat = file.stat()
                    size_mb = stat.st_size / (1024 * 1024)
                    self.selection_info_label.set_text(
                        f"File: {file.name}\n"
                        f"Size: {size_mb:.2f} MB"
                    )
                except:
                    self.selection_info_label.set_text(f"File: {file.name}")
            else:
                total_size = 0
                for file in self.selected_files:
                    try:
                        total_size += file.stat().st_size
                    except:
                        pass
                
                size_mb = total_size / (1024 * 1024)
                self.selection_info_label.set_text(
                    f"{len(self.selected_files)} files selected\n"
                    f"Total size: {size_mb:.2f} MB"
                )
    
    def _update_button_sensitivity(self) -> None:
        """Update OK button sensitivity based on selection."""
        has_selection = bool(self.selected_files)
        
        if hasattr(self, 'import_button'):
            self.import_button.set_sensitive(has_selection)
        if hasattr(self, 'export_button'):
            self.export_button.set_sensitive(has_selection)
    
    def _update_preview(self) -> None:
        """Update file preview if applicable."""
        if (len(self.selected_files) == 1 and 
            self.operation_type in [OperationType.IMPORT] and
            self.selected_files[0].is_file()):
            
            file_path = self.selected_files[0]
            try:
                # Read first few lines for preview
                if file_path.suffix.lower() in ['.json', '.csv', '.xml', '.txt']:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        preview_text = f.read(1024)  # First 1KB
                    
                    buffer = self.preview_text.get_buffer()
                    buffer.set_text(preview_text)
                    self.preview_expander.set_expanded(True)
                else:
                    buffer = self.preview_text.get_buffer()
                    buffer.set_text("Binary file - no preview available")
                    self.preview_expander.set_expanded(False)
            except Exception as e:
                buffer = self.preview_text.get_buffer()
                buffer.set_text(f"Error reading file: {e}")
                self.preview_expander.set_expanded(False)
        else:
            self.preview_expander.set_expanded(False)
    
    def _update_file_filters(self) -> None:
        """Update file chooser filters based on selected format."""
        # This could update the active filter based on format selection
        pass
    
    def _count_files_in_directory(self, directory: Path) -> int:
        """Count supported files in directory."""
        count = 0
        try:
            pattern = "*"
            if self.selected_format != FileFormat.ALL:
                pattern = self.selected_format.value[2]
            
            for file in directory.rglob(pattern) if self.recursive_check.get_active() else directory.glob(pattern):
                if file.is_file():
                    count += 1
        except:
            pass
        
        return count
    
    def _start_operation(self) -> None:
        """Start the file operation in a background thread."""
        if not self.selected_files:
            return
        
        # Switch to progress page
        self.notebook.set_current_page(2)
        
        # Reset progress
        self.progress_bar.set_fraction(0.0)
        self.progress_bar.set_text("Starting operation...")
        self.status_label.set_text("Initializing...")
        self.results_buffer.set_text("")
        
        # Enable cancel button, disable OK button
        self.cancel_button.set_sensitive(True)
        if hasattr(self, 'import_button'):
            self.import_button.set_sensitive(False)
        if hasattr(self, 'export_button'):
            self.export_button.set_sensitive(False)
        
        # Start operation thread
        self.operation_cancelled = False
        self.operation_thread = threading.Thread(target=self._run_operation, daemon=True)
        self.operation_thread.start()
    
    def _run_operation(self) -> None:
        """Run the actual file operation (called in background thread)."""
        try:
            if self.operation_type == OperationType.IMPORT:
                self._run_import()
            elif self.operation_type == OperationType.BATCH_IMPORT:
                self._run_batch_import()
            elif self.operation_type == OperationType.EXPORT:
                self._run_export()
            elif self.operation_type == OperationType.BATCH_EXPORT:
                self._run_batch_export()
        except Exception as e:
            self.logger.error(f"Operation failed: {e}")
            GLib.idle_add(self._update_status, f"Operation failed: {e}")
            GLib.idle_add(self._operation_completed, False)
    
    def _run_import(self) -> None:
        """Run single file import."""
        results = []
        total_files = len(self.selected_files)
        
        for i, file_path in enumerate(self.selected_files):
            if self.operation_cancelled:
                break
            
            GLib.idle_add(self._update_progress, (i + 1) / total_files, f"Importing {file_path.name}")
            
            try:
                material_type = self.material_type_combo.get_active_id()
                material_data = self.file_ops_service.import_material_from_file(file_path, material_type)
                results.append(f"✓ Imported: {file_path.name}")
                GLib.idle_add(self._append_result, f"✓ Imported: {file_path.name}\n")
            except Exception as e:
                error_msg = f"✗ Failed: {file_path.name} - {e}"
                results.append(error_msg)
                GLib.idle_add(self._append_result, f"{error_msg}\n")
        
        self.results = results
        GLib.idle_add(self._operation_completed, not self.operation_cancelled)
    
    def _run_batch_import(self) -> None:
        """Run batch import from directory."""
        if not self.selected_files or not self.selected_files[0].is_dir():
            GLib.idle_add(self._operation_completed, False)
            return
        
        source_dir = self.selected_files[0]
        material_type = self.material_type_combo.get_active_id()
        
        def progress_callback(current, total):
            if not self.operation_cancelled:
                GLib.idle_add(self._update_progress, current / total, f"Processing {current}/{total} files")
        
        try:
            results = self.file_ops_service.batch_import_materials(
                source_dir, material_type, progress_callback
            )
            
            # Update results display
            for result in results:
                if not self.operation_cancelled:
                    GLib.idle_add(self._append_result, f"✓ Imported material\n")
            
            self.results = results
            GLib.idle_add(self._operation_completed, not self.operation_cancelled)
            
        except Exception as e:
            GLib.idle_add(self._update_status, f"Batch import failed: {e}")
            GLib.idle_add(self._operation_completed, False)
    
    def _run_export(self) -> None:
        """Run single file export."""
        # This would need material data passed in or selected
        # For now, just simulate the operation
        GLib.idle_add(self._update_progress, 1.0, "Export completed")
        GLib.idle_add(self._append_result, "Export operation not fully implemented\n")
        GLib.idle_add(self._operation_completed, True)
    
    def _run_batch_export(self) -> None:
        """Run batch export to directory."""
        # This would need material data passed in or selected
        # For now, just simulate the operation
        GLib.idle_add(self._update_progress, 1.0, "Batch export completed")
        GLib.idle_add(self._append_result, "Batch export operation not fully implemented\n")
        GLib.idle_add(self._operation_completed, True)
    
    def _update_progress(self, fraction: float, text: str) -> None:
        """Update progress bar (called from main thread)."""
        self.progress_bar.set_fraction(fraction)
        self.progress_bar.set_text(text)
    
    def _update_status(self, status: str) -> None:
        """Update status label (called from main thread)."""
        self.status_label.set_text(status)
    
    def _append_result(self, text: str) -> None:
        """Append text to results display (called from main thread)."""
        end_iter = self.results_buffer.get_end_iter()
        self.results_buffer.insert(end_iter, text)
        
        # Scroll to end
        mark = self.results_buffer.get_insert()
        self.results_view.scroll_mark_onscreen(mark)
    
    def _operation_completed(self, success: bool) -> None:
        """Handle operation completion (called from main thread)."""
        self.cancel_button.set_sensitive(False)
        
        if success:
            self.progress_bar.set_text("Operation completed successfully")
            self.status_label.set_text("Operation completed successfully")
            
            # Add close button
            self.add_button("Close", Gtk.ResponseType.CLOSE)
        else:
            self.progress_bar.set_text("Operation failed or cancelled")
            self.status_label.set_text("Operation failed or cancelled")
            
            # Re-enable operation button
            if hasattr(self, 'import_button'):
                self.import_button.set_sensitive(True)
            if hasattr(self, 'export_button'):
                self.export_button.set_sensitive(True)
    
    def _cancel_operation(self) -> None:
        """Cancel the running operation."""
        self.operation_cancelled = True
        self.cancel_button.set_sensitive(False)
        self._update_status("Cancelling operation...")
    
    def get_results(self) -> Optional[Any]:
        """Get operation results."""
        return self.results


def show_import_dialog(main_window: 'VCCTLMainWindow', 
                      initial_directory: Path = None) -> Optional[List[Dict[str, Any]]]:
    """Show import dialog and return results."""
    dialog = FileOperationDialog(main_window, OperationType.IMPORT, 
                                "Import Materials", initial_directory)
    dialog.show_all()
    
    response = dialog.run()
    results = dialog.get_results() if response == Gtk.ResponseType.OK else None
    
    dialog.destroy()
    return results


def show_batch_import_dialog(main_window: 'VCCTLMainWindow',
                           initial_directory: Path = None) -> Optional[List[Dict[str, Any]]]:
    """Show batch import dialog and return results."""
    dialog = FileOperationDialog(main_window, OperationType.BATCH_IMPORT,
                                "Batch Import Materials", initial_directory)
    dialog.show_all()
    
    response = dialog.run()
    results = dialog.get_results() if response == Gtk.ResponseType.OK else None
    
    dialog.destroy()
    return results


def show_export_dialog(main_window: 'VCCTLMainWindow',
                      initial_directory: Path = None) -> Optional[Path]:
    """Show export dialog and return selected path."""
    dialog = FileOperationDialog(main_window, OperationType.EXPORT,
                                "Export Material", initial_directory)
    dialog.show_all()
    
    response = dialog.run()
    results = dialog.selected_files[0] if (response == Gtk.ResponseType.OK and 
                                          dialog.selected_files) else None
    
    dialog.destroy()
    return results


def show_batch_export_dialog(main_window: 'VCCTLMainWindow',
                            initial_directory: Path = None) -> Optional[Path]:
    """Show batch export dialog and return selected directory."""
    dialog = FileOperationDialog(main_window, OperationType.BATCH_EXPORT,
                                "Batch Export Materials", initial_directory)
    dialog.show_all()
    
    response = dialog.run()
    results = dialog.selected_files[0] if (response == Gtk.ResponseType.OK and 
                                          dialog.selected_files) else None
    
    dialog.destroy()
    return results
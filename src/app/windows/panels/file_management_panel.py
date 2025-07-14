#!/usr/bin/env python3
"""
File Management Panel for VCCTL

Provides a comprehensive file management interface integrating the file browser,
import/export dialogs, batch operations, and file history.
"""

import gi
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Optional, List, Dict, Any

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, Pango

if TYPE_CHECKING:
    from app.windows.main_window import VCCTLMainWindow

from app.services.service_container import get_service_container
from app.widgets.file_browser import FileBrowserWidget
from app.windows.dialogs import (
    show_import_dialog, show_batch_import_dialog,
    show_export_dialog, show_batch_export_dialog
)
from app.utils.batch_file_operations import BatchFileOperationManager, BatchOperationType
from app.utils.file_history import FileHistoryManager, ChangeType


class FileManagementPanel(Gtk.Box):
    """
    File management panel providing comprehensive file operations.
    
    Features:
    - File browser with project navigation
    - Import/export operations with progress
    - Batch file operations
    - File history and versioning
    - Validation and format conversion
    """
    
    def __init__(self, main_window: 'VCCTLMainWindow'):
        """Initialize the file management panel."""
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        self.main_window = main_window
        self.logger = logging.getLogger('VCCTL.FileManagementPanel')
        self.service_container = get_service_container()
        
        # Initialize managers
        self._init_managers()
        
        # Setup UI
        self._setup_ui()
        self._connect_signals()
        
        self.logger.info("File management panel initialized")
    
    def _init_managers(self) -> None:
        """Initialize file operation managers."""
        # Get project directories
        try:
            config = self.service_container.config_manager
            data_dir = Path(config.directories.data_directory)
            
            # Initialize batch operation manager
            self.batch_manager = BatchFileOperationManager()
            
            # Initialize file history manager
            history_dir = data_dir / "history"
            self.history_manager = FileHistoryManager(
                history_directory=history_dir,
                max_versions=10,
                max_age_days=30,
                max_total_size_mb=100
            )
            
        except Exception as e:
            self.logger.error(f"Failed to initialize managers: {e}")
            # Use fallback directories
            self.batch_manager = BatchFileOperationManager()
            self.history_manager = FileHistoryManager(Path.home() / ".vcctl" / "history")
    
    def _setup_ui(self) -> None:
        """Setup the panel UI."""
        # Create toolbar
        self._create_toolbar()
        
        # Create main content area with paned layout
        self._create_content_area()
        
        # Create status bar
        self._create_status_bar()
    
    def _create_toolbar(self) -> None:
        """Create the file operations toolbar."""
        toolbar = Gtk.Toolbar()
        toolbar.set_style(Gtk.ToolbarStyle.BOTH_HORIZ)
        
        # Import operations
        import_button = Gtk.ToolButton()
        import_button.set_icon_name("document-open")
        import_button.set_label("Import")
        import_button.set_tooltip_text("Import material files")
        import_button.connect('clicked', self._on_import_clicked)
        toolbar.insert(import_button, -1)
        
        batch_import_button = Gtk.ToolButton()
        batch_import_button.set_icon_name("document-open-recent")
        batch_import_button.set_label("Batch Import")
        batch_import_button.set_tooltip_text("Import multiple files from directory")
        batch_import_button.connect('clicked', self._on_batch_import_clicked)
        toolbar.insert(batch_import_button, -1)
        
        # Separator
        toolbar.insert(Gtk.SeparatorToolItem(), -1)
        
        # Export operations
        export_button = Gtk.ToolButton()
        export_button.set_icon_name("document-save")
        export_button.set_label("Export")
        export_button.set_tooltip_text("Export selected material")
        export_button.connect('clicked', self._on_export_clicked)
        toolbar.insert(export_button, -1)
        
        batch_export_button = Gtk.ToolButton()
        batch_export_button.set_icon_name("document-save-as")
        batch_export_button.set_label("Batch Export")
        batch_export_button.set_tooltip_text("Export multiple materials")
        batch_export_button.connect('clicked', self._on_batch_export_clicked)
        toolbar.insert(batch_export_button, -1)
        
        # Separator
        toolbar.insert(Gtk.SeparatorToolItem(), -1)
        
        # File operations
        validate_button = Gtk.ToolButton()
        validate_button.set_icon_name("dialog-question")
        validate_button.set_label("Validate")
        validate_button.set_tooltip_text("Validate selected files")
        validate_button.connect('clicked', self._on_validate_clicked)
        toolbar.insert(validate_button, -1)
        
        convert_button = Gtk.ToolButton()
        convert_button.set_icon_name("document-properties")
        convert_button.set_label("Convert")
        convert_button.set_tooltip_text("Convert file formats")
        convert_button.connect('clicked', self._on_convert_clicked)
        toolbar.insert(convert_button, -1)
        
        # Separator
        toolbar.insert(Gtk.SeparatorToolItem(), -1)
        
        # History operations
        history_button = Gtk.ToolButton()
        history_button.set_icon_name("document-open-recent")
        history_button.set_label("History")
        history_button.set_tooltip_text("View file history")
        history_button.connect('clicked', self._on_history_clicked)
        toolbar.insert(history_button, -1)
        
        cleanup_button = Gtk.ToolButton()
        cleanup_button.set_icon_name("edit-clear")
        cleanup_button.set_label("Cleanup")
        cleanup_button.set_tooltip_text("Clean up old file versions")
        cleanup_button.connect('clicked', self._on_cleanup_clicked)
        toolbar.insert(cleanup_button, -1)
        
        self.pack_start(toolbar, False, False, 0)
    
    def _create_content_area(self) -> None:
        """Create the main content area."""
        # Create horizontal paned layout
        paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        
        # Create file browser (left side)
        self._create_file_browser(paned)
        
        # Create details area (right side)
        self._create_details_area(paned)
        
        self.pack_start(paned, True, True, 0)
    
    def _create_file_browser(self, parent: Gtk.Paned) -> None:
        """Create the file browser area."""
        browser_frame = Gtk.Frame(label="Project Files")
        
        # Create file browser widget
        try:
            config = self.service_container.config_manager
            initial_dir = Path(config.directories.data_directory)
        except:
            initial_dir = Path.home()
        
        self.file_browser = FileBrowserWidget(self.main_window, show_hidden=False)
        self.file_browser.set_directory(initial_dir)
        
        browser_frame.add(self.file_browser)
        parent.pack1(browser_frame, True, True)  # Resizable
    
    def _create_details_area(self, parent: Gtk.Paned) -> None:
        """Create the file details and operations area."""
        details_frame = Gtk.Frame(label="File Details & Operations")
        
        details_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        details_box.set_margin_left(10)
        details_box.set_margin_right(10)
        details_box.set_margin_top(10)
        details_box.set_margin_bottom(10)
        
        # File information area
        self._create_file_info_area(details_box)
        
        # Operations notebook
        self._create_operations_notebook(details_box)
        
        details_frame.add(details_box)
        parent.pack2(details_frame, False, False)  # Fixed size
    
    def _create_file_info_area(self, parent: Gtk.Box) -> None:
        """Create file information display area."""
        info_frame = Gtk.Frame(label="Selected File Information")
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        info_box.set_margin_left(10)
        info_box.set_margin_right(10)
        info_box.set_margin_top(5)
        info_box.set_margin_bottom(5)
        
        # File details
        self.file_name_label = Gtk.Label("No file selected")
        self.file_name_label.set_halign(Gtk.Align.START)
        self.file_name_label.set_markup('<b>No file selected</b>')
        info_box.pack_start(self.file_name_label, False, False, 0)
        
        self.file_details_label = Gtk.Label("")
        self.file_details_label.set_halign(Gtk.Align.START)
        self.file_details_label.set_line_wrap(True)
        info_box.pack_start(self.file_details_label, False, False, 0)
        
        # File preview
        preview_scroll = Gtk.ScrolledWindow()
        preview_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        preview_scroll.set_size_request(-1, 150)
        
        self.file_preview = Gtk.TextView()
        self.file_preview.set_editable(False)
        self.file_preview.set_cursor_visible(False)
        preview_scroll.add(self.file_preview)
        
        info_box.pack_start(preview_scroll, True, True, 0)
        
        info_frame.add(info_box)
        parent.pack_start(info_frame, False, False, 0)
    
    def _create_operations_notebook(self, parent: Gtk.Box) -> None:
        """Create the operations notebook."""
        self.operations_notebook = Gtk.Notebook()
        
        # Batch Operations tab
        self._create_batch_operations_tab()
        
        # File History tab
        self._create_file_history_tab()
        
        # Validation Results tab
        self._create_validation_tab()
        
        parent.pack_start(self.operations_notebook, True, True, 0)
    
    def _create_batch_operations_tab(self) -> None:
        """Create the batch operations tab."""
        tab_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        tab_box.set_margin_left(10)
        tab_box.set_margin_right(10)
        tab_box.set_margin_top(10)
        tab_box.set_margin_bottom(10)
        
        # Operations list
        operations_frame = Gtk.Frame(label="Batch Operations Queue")
        
        # Create list store for operations
        self.operations_store = Gtk.ListStore(str, str, str, str)  # Type, Source, Target, Status
        
        operations_view = Gtk.TreeView(model=self.operations_store)
        
        # Create columns
        for i, title in enumerate(["Type", "Source", "Target", "Status"]):
            column = Gtk.TreeViewColumn(title)
            renderer = Gtk.CellRendererText()
            column.pack_start(renderer, True)
            column.add_attribute(renderer, "text", i)
            column.set_resizable(True)
            operations_view.append_column(column)
        
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroll.add(operations_view)
        operations_frame.add(scroll)
        
        tab_box.pack_start(operations_frame, True, True, 0)
        
        # Operations controls
        controls_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        clear_button = Gtk.Button(label="Clear Queue")
        clear_button.connect('clicked', self._on_clear_operations_clicked)
        controls_box.pack_start(clear_button, False, False, 0)
        
        execute_button = Gtk.Button(label="Execute Batch")
        execute_button.connect('clicked', self._on_execute_batch_clicked)
        controls_box.pack_start(execute_button, False, False, 0)
        
        tab_box.pack_start(controls_box, False, False, 0)
        
        # Progress bar
        self.batch_progress = Gtk.ProgressBar()
        self.batch_progress.set_show_text(True)
        self.batch_progress.set_text("Ready")
        tab_box.pack_start(self.batch_progress, False, False, 0)
        
        self.operations_notebook.append_page(tab_box, Gtk.Label("Batch Operations"))
    
    def _create_file_history_tab(self) -> None:
        """Create the file history tab."""
        tab_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        tab_box.set_margin_left(10)
        tab_box.set_margin_right(10)
        tab_box.set_margin_top(10)
        tab_box.set_margin_bottom(10)
        
        # History list
        history_frame = Gtk.Frame(label="File Version History")
        
        # Create list store for history
        self.history_store = Gtk.ListStore(str, str, str, str, str)  # Version, Date, Type, Comment, Size
        
        history_view = Gtk.TreeView(model=self.history_store)
        
        # Create columns
        for i, title in enumerate(["Version", "Date", "Change", "Comment", "Size"]):
            column = Gtk.TreeViewColumn(title)
            renderer = Gtk.CellRendererText()
            column.pack_start(renderer, True)
            column.add_attribute(renderer, "text", i)
            column.set_resizable(True)
            history_view.append_column(column)
        
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroll.add(history_view)
        history_frame.add(scroll)
        
        tab_box.pack_start(history_frame, True, True, 0)
        
        # History controls
        controls_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        restore_button = Gtk.Button(label="Restore Version")
        restore_button.connect('clicked', self._on_restore_version_clicked)
        controls_box.pack_start(restore_button, False, False, 0)
        
        compare_button = Gtk.Button(label="Compare Versions")
        compare_button.connect('clicked', self._on_compare_versions_clicked)
        controls_box.pack_start(compare_button, False, False, 0)
        
        tab_box.pack_start(controls_box, False, False, 0)
        
        self.operations_notebook.append_page(tab_box, Gtk.Label("File History"))
    
    def _create_validation_tab(self) -> None:
        """Create the validation results tab."""
        tab_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        tab_box.set_margin_left(10)
        tab_box.set_margin_right(10)
        tab_box.set_margin_top(10)
        tab_box.set_margin_bottom(10)
        
        # Validation results
        validation_frame = Gtk.Frame(label="Validation Results")
        
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        
        self.validation_buffer = Gtk.TextBuffer()
        self.validation_view = Gtk.TextView(buffer=self.validation_buffer)
        self.validation_view.set_editable(False)
        self.validation_view.set_cursor_visible(False)
        scroll.add(self.validation_view)
        
        validation_frame.add(scroll)
        tab_box.pack_start(validation_frame, True, True, 0)
        
        self.operations_notebook.append_page(tab_box, Gtk.Label("Validation"))
    
    def _create_status_bar(self) -> None:
        """Create the status bar."""
        self.status_bar = Gtk.Statusbar()
        self.status_context = self.status_bar.get_context_id("main")
        self.status_bar.push(self.status_context, "Ready")
        self.pack_start(self.status_bar, False, False, 0)
    
    def _connect_signals(self) -> None:
        """Connect widget signals."""
        # File browser signals
        self.file_browser.connect('file-selected', self._on_file_selected)
        self.file_browser.connect('files-selected', self._on_files_selected)
        self.file_browser.connect('file-activated', self._on_file_activated)
    
    def _update_status(self, message: str) -> None:
        """Update status bar message."""
        self.status_bar.pop(self.status_context)
        self.status_bar.push(self.status_context, message)
    
    def _update_file_info(self, file_path: Optional[Path]) -> None:
        """Update the file information display."""
        if not file_path:
            self.file_name_label.set_markup('<b>No file selected</b>')
            self.file_details_label.set_text("")
            self.file_preview.get_buffer().set_text("")
            return
        
        try:
            # Update file name
            self.file_name_label.set_markup(f'<b>{file_path.name}</b>')
            
            # Update file details
            if file_path.exists():
                stat = file_path.stat()
                size_mb = stat.st_size / (1024 * 1024)
                import datetime
                mod_time = datetime.datetime.fromtimestamp(stat.st_mtime)
                
                details = f"Path: {file_path}\n"
                details += f"Size: {size_mb:.2f} MB\n"
                details += f"Modified: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}"
                
                self.file_details_label.set_text(details)
                
                # Update preview
                self._update_file_preview(file_path)
            else:
                self.file_details_label.set_text("File does not exist")
                self.file_preview.get_buffer().set_text("")
                
        except Exception as e:
            self.logger.error(f"Failed to update file info: {e}")
            self.file_details_label.set_text(f"Error: {e}")
    
    def _update_file_preview(self, file_path: Path) -> None:
        """Update the file preview."""
        try:
            if file_path.suffix.lower() in ['.json', '.csv', '.xml', '.txt']:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read(2048)  # First 2KB
                self.file_preview.get_buffer().set_text(content)
            else:
                self.file_preview.get_buffer().set_text("Binary file - no preview available")
        except Exception as e:
            self.file_preview.get_buffer().set_text(f"Error reading file: {e}")
    
    def _update_file_history(self, file_path: Optional[Path]) -> None:
        """Update the file history display."""
        self.history_store.clear()
        
        if not file_path:
            return
        
        try:
            history = self.history_manager.get_file_history(file_path)
            if not history:
                return
            
            for version in history.versions:
                date_str = version.datetime.strftime('%Y-%m-%d %H:%M')
                size_str = f"{version.file_size} bytes"
                
                self.history_store.append([
                    version.version_id[:12] + "...",  # Truncated version ID
                    date_str,
                    version.change_type.value,
                    version.comment or "",
                    size_str
                ])
                
        except Exception as e:
            self.logger.error(f"Failed to update file history: {e}")
    
    # Event handlers
    
    def _on_file_selected(self, widget: FileBrowserWidget, file_path: str) -> None:
        """Handle file selection."""
        file_path = Path(file_path)
        self._update_file_info(file_path)
        self._update_file_history(file_path)
    
    def _on_files_selected(self, widget: FileBrowserWidget, file_paths: List[Path]) -> None:
        """Handle multiple file selection."""
        if len(file_paths) == 1:
            self._update_file_info(file_paths[0])
        else:
            self.file_name_label.set_markup(f'<b>{len(file_paths)} files selected</b>')
            total_size = sum(f.stat().st_size for f in file_paths if f.exists())
            size_mb = total_size / (1024 * 1024)
            self.file_details_label.set_text(f"Total size: {size_mb:.2f} MB")
            self.file_preview.get_buffer().set_text("")
    
    def _on_file_activated(self, widget: FileBrowserWidget, file_path: str) -> None:
        """Handle file activation (double-click)."""
        # For now, just show import dialog for material files
        file_path = Path(file_path)
        if file_path.suffix.lower() in ['.json', '.csv', '.xml']:
            self._import_single_file(file_path)
    
    def _on_import_clicked(self, button: Gtk.Button) -> None:
        """Handle import button click."""
        results = show_import_dialog(self.main_window)
        if results:
            self._update_status(f"Imported {len(results)} materials")
    
    def _on_batch_import_clicked(self, button: Gtk.Button) -> None:
        """Handle batch import button click."""
        results = show_batch_import_dialog(self.main_window)
        if results:
            self._update_status(f"Batch imported {len(results)} materials")
    
    def _on_export_clicked(self, button: Gtk.Button) -> None:
        """Handle export button click."""
        result = show_export_dialog(self.main_window)
        if result:
            self._update_status(f"Exported to {result}")
    
    def _on_batch_export_clicked(self, button: Gtk.Button) -> None:
        """Handle batch export button click."""
        result = show_batch_export_dialog(self.main_window)
        if result:
            self._update_status(f"Batch exported to {result}")
    
    def _on_validate_clicked(self, button: Gtk.Button) -> None:
        """Handle validate button click."""
        selected_files = self.file_browser.get_selected_files()
        if not selected_files:
            self._update_status("No files selected for validation")
            return
        
        # Add validation operations to batch
        self.batch_manager.add_validation_operations(selected_files)
        self._update_operations_list()
        self._update_status(f"Added {len(selected_files)} files to validation queue")
    
    def _on_convert_clicked(self, button: Gtk.Button) -> None:
        """Handle convert button click."""
        # TODO: Implement format conversion dialog
        self._update_status("Format conversion not yet implemented")
    
    def _on_history_clicked(self, button: Gtk.Button) -> None:
        """Handle history button click."""
        self.operations_notebook.set_current_page(1)  # Switch to history tab
    
    def _on_cleanup_clicked(self, button: Gtk.Button) -> None:
        """Handle cleanup button click."""
        stats = self.history_manager.cleanup_history()
        message = f"Cleanup completed: {stats['versions_removed']} versions removed"
        self._update_status(message)
    
    def _on_clear_operations_clicked(self, button: Gtk.Button) -> None:
        """Handle clear operations button click."""
        self.batch_manager.clear_operations()
        self._update_operations_list()
        self._update_status("Operations queue cleared")
    
    def _on_execute_batch_clicked(self, button: Gtk.Button) -> None:
        """Handle execute batch button click."""
        if not self.batch_manager.operations:
            self._update_status("No operations in queue")
            return
        
        # Set up progress callback
        def progress_callback(progress):
            from gi.repository import GLib
            GLib.idle_add(self._update_batch_progress, progress)
        
        self.batch_manager.add_progress_callback(progress_callback)
        
        # Execute in background thread
        import threading
        def execute():
            result = self.batch_manager.execute_batch(parallel=True, continue_on_error=True)
            from gi.repository import GLib
            GLib.idle_add(self._batch_completed, result)
        
        thread = threading.Thread(target=execute, daemon=True)
        thread.start()
        
        self._update_status("Executing batch operations...")
    
    def _on_restore_version_clicked(self, button: Gtk.Button) -> None:
        """Handle restore version button click."""
        # TODO: Implement version restoration
        self._update_status("Version restoration not yet implemented")
    
    def _on_compare_versions_clicked(self, button: Gtk.Button) -> None:
        """Handle compare versions button click."""
        # TODO: Implement version comparison
        self._update_status("Version comparison not yet implemented")
    
    def _update_operations_list(self) -> None:
        """Update the operations list display."""
        self.operations_store.clear()
        
        for operation in self.batch_manager.operations:
            self.operations_store.append([
                operation.operation_type.value,
                str(operation.source_path),
                str(operation.target_path) if operation.target_path else "",
                operation.status.value
            ])
    
    def _update_batch_progress(self, progress) -> None:
        """Update batch operation progress."""
        self.batch_progress.set_fraction(progress.progress_fraction)
        self.batch_progress.set_text(f"{progress.progress_percentage:.1f}%")
        
        if progress.current_operation:
            self._update_status(f"Processing: {progress.current_operation.source_path.name}")
    
    def _batch_completed(self, result) -> None:
        """Handle batch operation completion."""
        message = (f"Batch completed: {result.completed_operations} successful, "
                  f"{result.failed_operations} failed")
        self._update_status(message)
        
        self.batch_progress.set_fraction(1.0)
        self.batch_progress.set_text("Completed")
        
        # Update operations list to show final status
        self._update_operations_list()
    
    def _import_single_file(self, file_path: Path) -> None:
        """Import a single file directly."""
        try:
            # Track file in history
            self.history_manager.track_file(file_path, ChangeType.MODIFIED, "Imported via file manager")
            
            # Use file operations service to import
            material_type = "cement"  # Default, should be detected or prompted
            material_data = self.service_container.file_operations_service.import_material_from_file(
                file_path, material_type
            )
            
            self._update_status(f"Imported: {file_path.name}")
            
        except Exception as e:
            self.logger.error(f"Failed to import {file_path}: {e}")
            self._update_status(f"Import failed: {e}")


# Register the widget
GObject.type_register(FileManagementPanel)
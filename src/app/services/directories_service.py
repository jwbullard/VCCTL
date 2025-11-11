#!/usr/bin/env python3
"""
Directories Service for VCCTL

Manages directory operations and path handling for simulations and operations.
"""

import logging
import sys
import shutil
from pathlib import Path
from typing import Optional, Dict, Any
from ..config.config_manager import ConfigManager


class DirectoriesService:
    """Service for managing application directories and operation paths."""

    # Class variable to track if extraction dialog has been shown
    _extraction_started = False

    def __init__(self, config_manager: ConfigManager):
        """Initialize directories service with configuration manager."""
        self.config_manager = config_manager
        self.logger = logging.getLogger('VCCTL.Services.Directories')
        self._ensure_base_directories()
    
    def _ensure_base_directories(self) -> None:
        """Ensure all base directories exist."""
        try:
            directories_config = self.config_manager.directories
            directories_config.create_directories()
            self.logger.info("Base directories ensured")

            # Copy bundled data on first run
            self.copy_bundled_data_if_needed()
        except Exception as e:
            self.logger.error(f"Failed to create base directories: {e}")
            raise

    def copy_bundled_data_if_needed(self) -> None:
        """
        Public method to copy bundled data to user directory.
        Can be called after config changes to ensure data is populated.
        """
        self._copy_bundled_data_if_needed()

    def _copy_bundled_data_if_needed(self) -> None:
        """Extract bundled compressed particle_shape_set and aggregate data to user directory on first run."""
        import tarfile
        import threading
        try:
            # Check if running from PyInstaller bundle
            if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
                bundled_base = Path(sys._MEIPASS) / "data"
            else:
                # Running in development - data is in project root
                return  # Don't extract in development mode

            directories_config = self.config_manager.directories

            # Extract particle_shape_set if not exists or empty
            particle_shape_dest = directories_config.particle_shape_set_path
            particle_shape_archive = bundled_base / "particle_shape_set.tar.gz"

            # Check aggregate too
            aggregate_dest = directories_config.aggregate_path
            aggregate_archive = bundled_base / "aggregate.tar.gz"

            self.logger.info(f"Checking extraction needs:")
            self.logger.info(f"  particle_shape_archive exists: {particle_shape_archive.exists()}")
            self.logger.info(f"  particle_shape_dest: {particle_shape_dest}")
            self.logger.info(f"  aggregate_archive exists: {aggregate_archive.exists()}")
            self.logger.info(f"  aggregate_dest: {aggregate_dest}")

            # Determine if we need to show the first-launch dialog
            needs_particle_extract = False
            needs_aggregate_extract = False

            if particle_shape_archive.exists():
                if not particle_shape_dest.exists():
                    needs_particle_extract = True
                else:
                    try:
                        needs_particle_extract = not any(particle_shape_dest.iterdir())
                    except Exception:
                        needs_particle_extract = True

            if aggregate_archive.exists():
                if not aggregate_dest.exists():
                    needs_aggregate_extract = True
                else:
                    try:
                        needs_aggregate_extract = not any(aggregate_dest.iterdir())
                    except Exception:
                        needs_aggregate_extract = True

            self.logger.info(f"Extraction decision: particle={needs_particle_extract}, aggregate={needs_aggregate_extract}")

            # Show dialog if extraction is needed (only once)
            dialog = None
            if needs_particle_extract or needs_aggregate_extract:
                # Check if extraction already started by another instance
                # (only matters if data actually needs extraction)
                if DirectoriesService._extraction_started:
                    self.logger.info("Extraction already started by another instance, waiting for it to complete")
                    # Don't show another dialog, but also don't extract again
                    # Just return and let the other instance finish
                    return

                # Mark extraction as started
                DirectoriesService._extraction_started = True
                self.logger.info(f"Starting first-launch extraction (particle_extract={needs_particle_extract}, aggregate_extract={needs_aggregate_extract})")

                dialog = self._show_first_launch_dialog()

                # Run extraction in background thread
                def extract_in_background():
                    try:
                        self.logger.info("Starting background extraction thread")
                        # Extract particle shapes
                        if particle_shape_archive.exists() and needs_particle_extract:
                            self.logger.info(f"Extracting particle shape sets from {particle_shape_archive} to {particle_shape_dest.parent}")
                            from gi.repository import GLib
                            if dialog:
                                GLib.idle_add(self._update_dialog_message, dialog, "Extracting particle shape sets...\n(This may take up to 60 seconds)")
                            particle_shape_dest.parent.mkdir(parents=True, exist_ok=True)
                            self.logger.info(f"Created directory: {particle_shape_dest.parent}")
                            with tarfile.open(particle_shape_archive, 'r:gz') as tar:
                                tar.extractall(path=particle_shape_dest.parent)
                            self.logger.info("Particle shape sets extracted successfully")

                        # Extract aggregate (code continues below...)
                        self._extract_aggregate_in_background(aggregate_archive, aggregate_dest, needs_aggregate_extract, dialog, bundled_base)

                        self.logger.info("Extraction complete, refreshing shape sets and closing dialog")

                        # Refresh microstructure service shape sets after extraction
                        try:
                            from app.services.service_container import service_container
                            GLib.idle_add(self._refresh_shape_sets_after_extraction, service_container)
                        except Exception as e:
                            self.logger.error(f"Failed to refresh shape sets after extraction: {e}")

                        # Close dialog when done
                        if dialog:
                            GLib.idle_add(self._close_dialog, dialog)

                    except Exception as e:
                        self.logger.error(f"Failed to extract bundled data: {e}")
                        import traceback
                        self.logger.error(traceback.format_exc())
                        if dialog:
                            from gi.repository import GLib
                            GLib.idle_add(self._close_dialog, dialog)

                # Start background thread (NOT daemon so it completes even if main thread continues)
                thread = threading.Thread(target=extract_in_background, daemon=False)
                thread.start()

                # Return immediately - extraction continues in background
                return

            # No extraction needed - continue with normal flow
            if particle_shape_archive.exists():
                if needs_particle_extract:
                    self.logger.info(f"Extracting particle shape sets from {particle_shape_archive} to {particle_shape_dest.parent}")
                    particle_shape_dest.parent.mkdir(parents=True, exist_ok=True)
                    with tarfile.open(particle_shape_archive, 'r:gz') as tar:
                        tar.extractall(path=particle_shape_dest.parent)
                    self.logger.info("Particle shape sets extracted successfully")
                else:
                    self.logger.debug("Particle shape sets already exist, skipping extraction")
            else:
                # Fall back to uncompressed directory (for backwards compatibility or development)
                particle_shape_src = bundled_base / "particle_shape_set"
                if particle_shape_src.exists():
                    needs_copy = False
                    if not particle_shape_dest.exists():
                        needs_copy = True
                    else:
                        try:
                            needs_copy = not any(particle_shape_dest.iterdir())
                        except Exception:
                            needs_copy = True

                    if needs_copy:
                        self.logger.info(f"Copying particle shape sets from {particle_shape_src} to {particle_shape_dest}")
                        particle_shape_dest.mkdir(parents=True, exist_ok=True)
                        shutil.copytree(particle_shape_src, particle_shape_dest, dirs_exist_ok=True)
                        self.logger.info("Particle shape sets copied successfully")

            # Extract aggregate if not exists or empty
            # Try compressed archive first, fall back to uncompressed directory
            if aggregate_archive.exists():
                if needs_aggregate_extract:
                    self.logger.info(f"Extracting aggregate shapes from {aggregate_archive} to {aggregate_dest.parent}")
                    if dialog:
                        self._update_dialog_message(dialog, "Extracting aggregate shapes...\n(This may take up to 30 seconds)")
                    aggregate_dest.parent.mkdir(parents=True, exist_ok=True)
                    with tarfile.open(aggregate_archive, 'r:gz') as tar:
                        tar.extractall(path=aggregate_dest.parent)
                    self.logger.info("Aggregate shapes extracted successfully")
                else:
                    self.logger.debug("Aggregate shapes already exist, skipping extraction")
            else:
                # Fall back to uncompressed directory (for backwards compatibility)
                aggregate_src = bundled_base / "aggregate"
                if aggregate_src.exists():
                    needs_copy = False
                    if not aggregate_dest.exists():
                        needs_copy = True
                    else:
                        try:
                            needs_copy = not any(aggregate_dest.iterdir())
                        except Exception:
                            needs_copy = True

                    if needs_copy:
                        self.logger.info(f"Copying aggregate shapes from {aggregate_src} to {aggregate_dest}")
                        aggregate_dest.mkdir(parents=True, exist_ok=True)
                        shutil.copytree(aggregate_src, aggregate_dest, dirs_exist_ok=True)
                        self.logger.info("Aggregate shapes copied successfully")

            # Close the dialog if it was shown
            if dialog:
                self._close_dialog(dialog)

        except Exception as e:
            self.logger.warning(f"Failed to extract bundled data (non-critical): {e}")
            import traceback
            self.logger.warning(traceback.format_exc())
            # Close dialog on error too
            if 'dialog' in locals() and dialog:
                self._close_dialog(dialog)

    def _extract_aggregate_in_background(self, aggregate_archive, aggregate_dest, needs_aggregate_extract, dialog, bundled_base):
        """Helper method to extract aggregate data in background thread."""
        import tarfile
        from gi.repository import GLib

        if aggregate_archive.exists() and needs_aggregate_extract:
            self.logger.info(f"Extracting aggregate shapes from {aggregate_archive} to {aggregate_dest.parent}")
            if dialog:
                GLib.idle_add(self._update_dialog_message, dialog, "Extracting aggregate shapes...\n(This may take up to 30 seconds)")
            aggregate_dest.parent.mkdir(parents=True, exist_ok=True)
            with tarfile.open(aggregate_archive, 'r:gz') as tar:
                tar.extractall(path=aggregate_dest.parent)
            self.logger.info("Aggregate shapes extracted successfully")
        elif not aggregate_archive.exists():
            # Fall back to uncompressed directory
            aggregate_src = bundled_base / "aggregate"
            if aggregate_src.exists() and needs_aggregate_extract:
                self.logger.info(f"Copying aggregate shapes from {aggregate_src} to {aggregate_dest}")
                aggregate_dest.mkdir(parents=True, exist_ok=True)
                shutil.copytree(aggregate_src, aggregate_dest, dirs_exist_ok=True)
                self.logger.info("Aggregate shapes copied successfully")

    def _show_first_launch_dialog(self):
        """Show a dialog informing user about first-launch data extraction."""
        try:
            from gi.repository import Gtk, GLib

            # Create a simple dialog
            dialog = Gtk.Window(title="VCCTL - First Launch")
            dialog.set_border_width(20)
            dialog.set_default_size(400, 150)
            dialog.set_position(Gtk.WindowPosition.CENTER)
            dialog.set_resizable(False)
            dialog.set_decorated(True)

            # Create a vertical box for content
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
            dialog.add(vbox)

            # Title label
            title_label = Gtk.Label()
            title_label.set_markup("<b>Welcome to VCCTL</b>")
            vbox.pack_start(title_label, False, False, 0)

            # Message label (will be updated during extraction)
            message_label = Gtk.Label()
            message_label.set_text("Preparing application data for first launch...\nThis may take up to 60 seconds.")
            message_label.set_line_wrap(True)
            message_label.set_justify(Gtk.Justification.CENTER)
            vbox.pack_start(message_label, False, False, 0)

            # Add a spinner
            spinner = Gtk.Spinner()
            spinner.start()
            vbox.pack_start(spinner, False, False, 0)

            # Store message label for updates
            dialog.message_label = message_label

            # Show the dialog
            dialog.show_all()

            # Process pending GTK events to ensure dialog is visible
            while Gtk.events_pending():
                Gtk.main_iteration()

            return dialog

        except Exception as e:
            self.logger.warning(f"Failed to show first-launch dialog: {e}")
            return None

    def _update_dialog_message(self, dialog, message: str):
        """Update the message in the first-launch dialog."""
        try:
            if dialog and hasattr(dialog, 'message_label'):
                from gi.repository import Gtk
                dialog.message_label.set_text(message)
                # Process pending GTK events to update display
                while Gtk.events_pending():
                    Gtk.main_iteration()
        except Exception as e:
            self.logger.warning(f"Failed to update dialog message: {e}")

    def _close_dialog(self, dialog):
        """Close the first-launch dialog."""
        try:
            if dialog:
                from gi.repository import Gtk
                dialog.destroy()
                # Process pending GTK events
                while Gtk.events_pending():
                    Gtk.main_iteration()
        except Exception as e:
            self.logger.warning(f"Failed to close dialog: {e}")

    def _refresh_shape_sets_after_extraction(self, service_container):
        """Refresh shape sets in microstructure service after extraction completes.

        Called in main GTK thread via GLib.idle_add after background extraction finishes.
        """
        try:
            self.logger.info("Refreshing microstructure service shape sets after extraction")

            # Refresh service cache
            if hasattr(service_container, 'microstructure_service') and service_container.microstructure_service:
                service_container.microstructure_service.refresh_shape_sets()
                self.logger.info("Shape sets cache refreshed in service")
            else:
                self.logger.warning("Microstructure service not available for refresh")

            # Refresh UI dropdowns in Mix Design panel
            try:
                # Access the main window through GTK application
                from gi.repository import Gtk
                app = Gtk.Application.get_default()
                if app and hasattr(app, 'main_window') and app.main_window:
                    main_window = app.main_window
                    if hasattr(main_window, 'panels') and 'mix_design' in main_window.panels:
                        mix_panel = main_window.panels['mix_design']
                        if hasattr(mix_panel, 'refresh_shape_sets'):
                            mix_panel.refresh_shape_sets()
                            self.logger.info("Mix Design panel dropdowns refreshed")
                        else:
                            self.logger.debug("Mix Design panel does not have refresh_shape_sets method")
                    else:
                        self.logger.debug("Mix Design panel not yet created or not in panels dict")
                else:
                    self.logger.debug("Main window not yet available for UI refresh")
            except Exception as ui_error:
                self.logger.warning(f"Failed to refresh UI dropdowns (non-critical): {ui_error}")

        except Exception as e:
            self.logger.error(f"Failed to refresh shape sets: {e}")
            import traceback
            self.logger.error(traceback.format_exc())

    def get_operation_dir(self, operation_name: str) -> Path:
        """
        Get the directory path for a specific operation, creating it if necessary.
        
        Args:
            operation_name: Name of the operation
            
        Returns:
            Path to the operation directory
            
        Raises:
            RuntimeError: If directory cannot be created
        """
        if not operation_name or not operation_name.strip():
            raise ValueError("Operation name cannot be empty")
        
        # Sanitize operation name for filesystem
        safe_name = self._sanitize_filename(operation_name)
        
        directories_config = self.config_manager.directories
        operation_path = directories_config.operations_path / safe_name
        
        try:
            operation_path.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"Operation directory ensured: {operation_path}")
            return operation_path
        except Exception as e:
            self.logger.error(f"Failed to create operation directory {operation_path}: {e}")
            raise RuntimeError(f"Failed to create operation directory: {e}")
    
    def get_operation_file_path(self, operation_name: str, filename: str) -> Path:
        """
        Get the full path for a file within an operation directory.
        
        Args:
            operation_name: Name of the operation
            filename: Name of the file
            
        Returns:
            Full path to the file
        """
        if not filename or not filename.strip():
            raise ValueError("Filename cannot be empty")
        
        operation_dir = self.get_operation_dir(operation_name)
        safe_filename = self._sanitize_filename(filename)
        return operation_dir / safe_filename
    
    def get_materials_dir(self) -> Path:
        """Get the materials directory path."""
        directories_config = self.config_manager.directories
        return directories_config.materials_path
    
    def get_temp_dir(self) -> Path:
        """Get the temporary directory path."""
        directories_config = self.config_manager.directories
        return directories_config.temp_path
    
    def get_database_dir(self) -> Path:
        """Get the database directory path."""
        directories_config = self.config_manager.directories
        return directories_config.database_path
    
    def get_logs_dir(self) -> Path:
        """Get the logs directory path."""
        directories_config = self.config_manager.directories
        return directories_config.logs_path
    
    def get_bin_dir(self) -> Path:
        """Get the bin directory path."""
        directories_config = self.config_manager.directories
        return directories_config.bin_path
    
    def get_data_dir(self) -> Path:
        """Get the data directory path."""
        directories_config = self.config_manager.directories
        return directories_config.data_path
    
    def get_aggregate_dir(self) -> Path:
        """Get the aggregate directory path."""
        directories_config = self.config_manager.directories
        return directories_config.aggregate_path

    def get_particle_shape_set_dir(self) -> Path:
        """Get the particle shape set directory path."""
        directories_config = self.config_manager.directories
        return directories_config.particle_shape_set_path

    def get_operations_path(self) -> Path:
        """Get the operations directory path."""
        directories_config = self.config_manager.directories
        return directories_config.operations_path
    
    def create_temp_file(self, prefix: str = "vcctl_", suffix: str = ".tmp") -> Path:
        """
        Create a temporary file and return its path.
        
        Args:
            prefix: Prefix for the temporary file name
            suffix: Suffix for the temporary file name
            
        Returns:
            Path to the created temporary file
        """
        import tempfile
        temp_dir = self.get_temp_dir()
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Create temporary file in our temp directory
        with tempfile.NamedTemporaryFile(
            prefix=prefix,
            suffix=suffix,
            dir=temp_dir,
            delete=False
        ) as tmp_file:
            temp_path = Path(tmp_file.name)
        
        self.logger.debug(f"Created temporary file: {temp_path}")
        return temp_path
    
    def cleanup_temp_files(self, max_age_hours: int = 24) -> int:
        """
        Clean up old temporary files.
        
        Args:
            max_age_hours: Maximum age of files to keep in hours
            
        Returns:
            Number of files removed
        """
        import time
        
        temp_dir = self.get_temp_dir()
        if not temp_dir.exists():
            return 0
        
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        files_removed = 0
        
        try:
            for temp_file in temp_dir.rglob("*"):
                if temp_file.is_file():
                    try:
                        file_age = current_time - temp_file.stat().st_mtime
                        if file_age > max_age_seconds:
                            temp_file.unlink()
                            files_removed += 1
                            self.logger.debug(f"Removed old temp file: {temp_file}")
                    except Exception as e:
                        self.logger.warning(f"Failed to remove temp file {temp_file}: {e}")
        except Exception as e:
            self.logger.error(f"Error during temp file cleanup: {e}")
        
        if files_removed > 0:
            self.logger.info(f"Cleaned up {files_removed} temporary files")
        
        return files_removed
    
    def get_directory_info(self) -> Dict[str, Any]:
        """Get information about all application directories."""
        directories_config = self.config_manager.directories
        return directories_config.get_directory_info()
    
    def validate_directory_structure(self) -> Dict[str, Any]:
        """Validate the directory structure and permissions."""
        directories_config = self.config_manager.directories
        return directories_config.validate()
    
    def get_relative_path(self, absolute_path: Path) -> Path:
        """Get a path relative to the application directory."""
        directories_config = self.config_manager.directories
        return directories_config.get_relative_path(absolute_path)
    
    def resolve_path(self, path_str: str) -> Path:
        """Resolve a path string relative to the application directory."""
        directories_config = self.config_manager.directories
        return directories_config.resolve_path(path_str)
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize a filename by removing/replacing invalid characters.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename safe for filesystem use
        """
        import re
        
        # Remove or replace invalid characters
        # Windows invalid characters: < > : " | ? * and ASCII 0-31
        invalid_chars = r'[<>:"|?*\x00-\x1f]'
        sanitized = re.sub(invalid_chars, '_', filename)
        
        # Remove leading/trailing dots and spaces
        sanitized = sanitized.strip('. ')
        
        # Ensure filename is not empty after sanitization
        if not sanitized:
            sanitized = "unnamed"
        
        # Limit length to reasonable filesystem limits
        if len(sanitized) > 200:
            name_part = sanitized[:190]
            extension_part = sanitized[-10:] if '.' in sanitized[-10:] else ""
            sanitized = name_part + extension_part
        
        return sanitized
    
    def ensure_directory(self, directory_path: Path) -> None:
        """
        Ensure a directory exists, creating it if necessary.
        
        Args:
            directory_path: Path to the directory to ensure
            
        Raises:
            RuntimeError: If directory cannot be created
        """
        try:
            directory_path.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"Directory ensured: {directory_path}")
        except Exception as e:
            self.logger.error(f"Failed to create directory {directory_path}: {e}")
            raise RuntimeError(f"Failed to create directory: {e}")
    
    def is_safe_path(self, path: Path, base_path: Optional[Path] = None) -> bool:
        """
        Check if a path is safe (within allowed directories).
        
        Args:
            path: Path to check
            base_path: Base path to restrict to (defaults to app directory)
            
        Returns:
            True if path is safe, False otherwise
        """
        if base_path is None:
            directories_config = self.config_manager.directories
            base_path = directories_config.app_directory
        
        try:
            # Resolve both paths to handle symlinks and relative components
            resolved_path = path.resolve()
            resolved_base = base_path.resolve()
            
            # Check if path is within base path
            resolved_path.relative_to(resolved_base)
            return True
        except (ValueError, OSError):
            return False
    
    def get_disk_usage(self, path: Optional[Path] = None) -> Dict[str, float]:
        """
        Get disk usage information for a path.
        
        Args:
            path: Path to check (defaults to app directory)
            
        Returns:
            Dictionary with total, used, and free space in GB
        """
        if path is None:
            directories_config = self.config_manager.directories
            path = directories_config.app_directory
        
        try:
            import shutil
            total, used, free = shutil.disk_usage(path)
            
            # Convert to GB
            return {
                'total_gb': total / (1024**3),
                'used_gb': used / (1024**3),
                'free_gb': free / (1024**3),
                'usage_percent': (used / total) * 100 if total > 0 else 0
            }
        except Exception as e:
            self.logger.error(f"Failed to get disk usage for {path}: {e}")
            return {'total_gb': 0, 'used_gb': 0, 'free_gb': 0, 'usage_percent': 0}
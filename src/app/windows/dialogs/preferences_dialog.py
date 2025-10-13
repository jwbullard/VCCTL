#!/usr/bin/env python3
"""
Preferences Dialog for VCCTL

Allows users to configure application settings including project directory location.
"""

import gi
import logging
from pathlib import Path

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


class PreferencesDialog(Gtk.Dialog):
    """Dialog for editing application preferences."""

    def __init__(self, parent, config_manager):
        """Initialize the preferences dialog."""
        super().__init__(
            title="Preferences",
            parent=parent,
            flags=0
        )

        self.logger = logging.getLogger('VCCTL.PreferencesDialog')
        self.config_manager = config_manager

        # Store original values for cancel
        self.original_app_directory = str(config_manager.user.app_directory)

        # Dialog setup
        self.set_default_size(600, 400)
        self.set_border_width(10)

        # Add buttons
        self.add_button("Cancel", Gtk.ResponseType.CANCEL)
        self.add_button("Apply", Gtk.ResponseType.APPLY)
        self.add_button("OK", Gtk.ResponseType.OK)

        # Create UI
        self._setup_ui()

        # Load current settings
        self._load_settings()

    def _setup_ui(self):
        """Setup the preferences UI."""
        content_area = self.get_content_area()
        content_area.set_spacing(10)

        # Create notebook for different preference categories
        notebook = Gtk.Notebook()
        notebook.set_border_width(10)
        content_area.pack_start(notebook, True, True, 0)

        # General preferences page
        general_page = self._create_general_page()
        notebook.append_page(general_page, Gtk.Label(label="General"))

        # Performance preferences page
        performance_page = self._create_performance_page()
        notebook.append_page(performance_page, Gtk.Label(label="Performance"))

        self.show_all()

    def _create_general_page(self):
        """Create the general preferences page."""
        grid = Gtk.Grid()
        grid.set_column_spacing(10)
        grid.set_row_spacing(10)
        grid.set_margin_top(20)
        grid.set_margin_bottom(20)
        grid.set_margin_left(20)
        grid.set_margin_right(20)

        row = 0

        # Project Directory setting
        label = Gtk.Label(label="Project Directory:")
        label.set_halign(Gtk.Align.END)
        grid.attach(label, 0, row, 1, 1)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        self.project_dir_entry = Gtk.Entry()
        self.project_dir_entry.set_editable(False)
        self.project_dir_entry.set_hexpand(True)
        hbox.pack_start(self.project_dir_entry, True, True, 0)

        browse_button = Gtk.Button(label="Browse...")
        browse_button.connect("clicked", self._on_browse_project_dir)
        hbox.pack_start(browse_button, False, False, 0)

        reset_button = Gtk.Button(label="Reset to Default")
        reset_button.connect("clicked", self._on_reset_project_dir)
        hbox.pack_start(reset_button, False, False, 0)

        grid.attach(hbox, 1, row, 2, 1)
        row += 1

        # Info label
        info_label = Gtk.Label()
        info_label.set_markup('<span size="small" foreground="gray">This is where your operations, database, and project data will be stored.</span>')
        info_label.set_halign(Gtk.Align.START)
        info_label.set_line_wrap(True)
        grid.attach(info_label, 1, row, 2, 1)
        row += 1

        # Warning label
        warning_label = Gtk.Label()
        warning_label.set_markup('<span size="small" foreground="orange"><b>Note:</b> Changing this directory will require restarting the application.</span>')
        warning_label.set_halign(Gtk.Align.START)
        warning_label.set_line_wrap(True)
        grid.attach(warning_label, 1, row, 2, 1)
        row += 1

        # Separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        grid.attach(separator, 0, row, 3, 1)
        row += 1

        # Auto-save setting
        self.auto_save_check = Gtk.CheckButton(label="Enable auto-save")
        grid.attach(self.auto_save_check, 0, row, 3, 1)
        row += 1

        # Confirm destructive actions
        self.confirm_actions_check = Gtk.CheckButton(label="Confirm before destructive actions")
        grid.attach(self.confirm_actions_check, 0, row, 3, 1)
        row += 1

        return grid

    def _create_performance_page(self):
        """Create the performance preferences page."""
        grid = Gtk.Grid()
        grid.set_column_spacing(10)
        grid.set_row_spacing(10)
        grid.set_margin_top(20)
        grid.set_margin_bottom(20)
        grid.set_margin_left(20)
        grid.set_margin_right(20)

        row = 0

        # Worker threads
        label = Gtk.Label(label="Maximum Worker Threads:")
        label.set_halign(Gtk.Align.END)
        grid.attach(label, 0, row, 1, 1)

        self.threads_spin = Gtk.SpinButton()
        self.threads_spin.set_range(1, 32)
        self.threads_spin.set_increments(1, 4)
        self.threads_spin.set_digits(0)
        grid.attach(self.threads_spin, 1, row, 1, 1)
        row += 1

        # Memory limit
        label = Gtk.Label(label="Memory Limit (MB):")
        label.set_halign(Gtk.Align.END)
        grid.attach(label, 0, row, 1, 1)

        self.memory_spin = Gtk.SpinButton()
        self.memory_spin.set_range(512, 65536)
        self.memory_spin.set_increments(512, 2048)
        self.memory_spin.set_digits(0)
        grid.attach(self.memory_spin, 1, row, 1, 1)
        row += 1

        # Cache enabled
        self.cache_check = Gtk.CheckButton(label="Enable caching")
        grid.attach(self.cache_check, 0, row, 2, 1)
        row += 1

        return grid

    def _load_settings(self):
        """Load current settings into the UI."""
        # General settings
        self.project_dir_entry.set_text(str(self.config_manager.user.app_directory))
        self.auto_save_check.set_active(self.config_manager.user.auto_save_enabled)
        self.confirm_actions_check.set_active(self.config_manager.user.confirm_destructive_actions)

        # Performance settings
        self.threads_spin.set_value(self.config_manager.user.max_worker_threads)
        self.memory_spin.set_value(self.config_manager.user.memory_limit_mb)
        self.cache_check.set_active(self.config_manager.user.cache_enabled)

    def _on_browse_project_dir(self, button):
        """Handle browse button click for project directory."""
        dialog = Gtk.FileChooserDialog(
            title="Select Project Directory",
            parent=self,
            action=Gtk.FileChooserAction.SELECT_FOLDER
        )
        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        dialog.add_button("Select", Gtk.ResponseType.OK)

        # Set current directory
        current_dir = self.project_dir_entry.get_text()
        if current_dir:
            dialog.set_current_folder(current_dir)

        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            selected_dir = dialog.get_filename()
            self.project_dir_entry.set_text(selected_dir)

        dialog.destroy()

    def _on_reset_project_dir(self, button):
        """Reset project directory to default."""
        from app.config.user_config import UserConfig
        default_dir = UserConfig._get_default_app_directory()
        self.project_dir_entry.set_text(str(default_dir))

    def apply_settings(self):
        """Apply the settings from the dialog."""
        # Update configuration
        new_path = Path(self.project_dir_entry.get_text())

        # Update both user and directories config
        self.config_manager.user.app_directory = new_path
        self.config_manager.directories.app_directory = new_path

        self.config_manager.user.auto_save_enabled = self.auto_save_check.get_active()
        self.config_manager.user.confirm_destructive_actions = self.confirm_actions_check.get_active()
        self.config_manager.user.max_worker_threads = int(self.threads_spin.get_value())
        self.config_manager.user.memory_limit_mb = int(self.memory_spin.get_value())
        self.config_manager.user.cache_enabled = self.cache_check.get_active()

        # Save to file
        try:
            self.config_manager.save_configuration()
            self.logger.info("Preferences saved successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save preferences: {e}")

            # Show error dialog
            error_dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Failed to Save Preferences"
            )
            error_dialog.format_secondary_text(f"Error: {str(e)}")
            error_dialog.run()
            error_dialog.destroy()
            return False

    def has_changed(self):
        """Check if settings have changed."""
        return self.project_dir_entry.get_text() != self.original_app_directory

    def run_dialog(self):
        """Run the dialog and handle responses."""
        while True:
            response = self.run()

            if response == Gtk.ResponseType.APPLY:
                # Apply without closing
                if self.apply_settings():
                    if self.has_changed():
                        # Show restart warning
                        warning = Gtk.MessageDialog(
                            transient_for=self,
                            flags=0,
                            message_type=Gtk.MessageType.INFO,
                            buttons=Gtk.ButtonsType.OK,
                            text="Restart Required"
                        )
                        warning.format_secondary_text(
                            "Project directory has changed. Please restart the application for changes to take effect."
                        )
                        warning.run()
                        warning.destroy()
                continue

            elif response == Gtk.ResponseType.OK:
                # Apply and close
                if self.apply_settings():
                    if self.has_changed():
                        # Show restart warning
                        warning = Gtk.MessageDialog(
                            transient_for=self,
                            flags=0,
                            message_type=Gtk.MessageType.INFO,
                            buttons=Gtk.ButtonsType.OK,
                            text="Restart Required"
                        )
                        warning.format_secondary_text(
                            "Project directory has changed. Please restart the application for changes to take effect."
                        )
                        warning.run()
                        warning.destroy()
                break

            else:  # Cancel
                break

        self.destroy()

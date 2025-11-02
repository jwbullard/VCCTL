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
        # Note: app_directory is now fixed per platform, not user-configurable

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
        self.auto_save_check.set_active(self.config_manager.user.auto_save_enabled)
        self.confirm_actions_check.set_active(self.config_manager.user.confirm_destructive_actions)

        # Performance settings
        self.threads_spin.set_value(self.config_manager.user.max_worker_threads)
        self.memory_spin.set_value(self.config_manager.user.memory_limit_mb)
        self.cache_check.set_active(self.config_manager.user.cache_enabled)


    def apply_settings(self):
        """Apply the settings from the dialog."""
        # Update configuration
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
        # Since app_directory is now fixed, just return False
        # (settings can still be saved, but no restart warning needed)
        return False

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

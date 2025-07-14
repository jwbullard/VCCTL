"""
Plugin Configuration UI for VCCTL GTK Application
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Gdk

import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

from .plugin_manager import PluginManager
from .plugin_descriptor import PluginDescriptor
from .plugin_security import DEFAULT_PERMISSIONS


class PluginConfigDialog(Gtk.Dialog):
    """Plugin configuration dialog"""
    
    def __init__(self, parent_window, plugin_manager: PluginManager):
        super().__init__("Plugin Configuration", parent_window, 0,
                         (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                          Gtk.STOCK_OK, Gtk.ResponseType.OK))
        
        self.plugin_manager = plugin_manager
        self.logger = logging.getLogger(__name__)
        
        self.set_default_size(800, 600)
        self.set_modal(True)
        self.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)
        
        self._create_ui()
        self._populate_plugins()
    
    def _create_ui(self):
        """Create the UI components"""
        content_area = self.get_content_area()
        
        # Create main paned window
        paned = Gtk.HPaned()
        content_area.pack_start(paned, True, True, 0)
        
        # Left panel - Plugin list
        self._create_plugin_list(paned)
        
        # Right panel - Plugin details
        self._create_plugin_details(paned)
        
        # Bottom panel - Actions
        self._create_action_buttons(content_area)
    
    def _create_plugin_list(self, paned):
        """Create the plugin list view"""
        left_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        left_box.set_size_request(300, -1)
        
        # Title
        title_label = Gtk.Label()
        title_label.set_markup("<b>Available Plugins</b>")
        title_label.set_halign(Gtk.Align.START)
        left_box.pack_start(title_label, False, False, 0)
        
        # Plugin list
        self.plugin_store = Gtk.ListStore(bool, str, str, str, str)  # enabled, name, version, author, status
        self.plugin_tree = Gtk.TreeView(self.plugin_store)
        
        # Enabled column
        enabled_renderer = Gtk.CellRendererToggle()
        enabled_renderer.connect("toggled", self._on_plugin_toggled)
        enabled_column = Gtk.TreeViewColumn("Enabled", enabled_renderer, active=0)
        self.plugin_tree.append_column(enabled_column)
        
        # Name column
        name_renderer = Gtk.CellRendererText()
        name_column = Gtk.TreeViewColumn("Name", name_renderer, text=1)
        name_column.set_sort_column_id(1)
        self.plugin_tree.append_column(name_column)
        
        # Version column
        version_renderer = Gtk.CellRendererText()
        version_column = Gtk.TreeViewColumn("Version", version_renderer, text=2)
        self.plugin_tree.append_column(version_column)
        
        # Status column
        status_renderer = Gtk.CellRendererText()
        status_column = Gtk.TreeViewColumn("Status", status_renderer, text=4)
        self.plugin_tree.append_column(status_column)
        
        # Selection
        selection = self.plugin_tree.get_selection()
        selection.connect("changed", self._on_plugin_selected)
        
        # Scrolled window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.add(self.plugin_tree)
        left_box.pack_start(scrolled, True, True, 0)
        
        paned.add1(left_box)
    
    def _create_plugin_details(self, paned):
        """Create the plugin details view"""
        right_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        right_box.set_margin_left(10)
        
        # Plugin info
        self.info_frame = Gtk.Frame()
        self.info_frame.set_label("Plugin Information")
        self._create_info_section()
        right_box.pack_start(self.info_frame, False, False, 0)
        
        # Plugin permissions
        self.permissions_frame = Gtk.Frame()
        self.permissions_frame.set_label("Permissions")
        self._create_permissions_section()
        right_box.pack_start(self.permissions_frame, False, False, 0)
        
        # Plugin configuration
        self.config_frame = Gtk.Frame()
        self.config_frame.set_label("Configuration")
        self._create_config_section()
        right_box.pack_start(self.config_frame, True, True, 0)
        
        paned.add2(right_box)
    
    def _create_info_section(self):
        """Create plugin information section"""
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        info_box.set_margin_top(10)
        info_box.set_margin_bottom(10)
        info_box.set_margin_left(10)
        info_box.set_margin_right(10)
        
        # Name
        self.name_label = Gtk.Label()
        self.name_label.set_halign(Gtk.Align.START)
        info_box.pack_start(self.name_label, False, False, 0)
        
        # Version
        self.version_label = Gtk.Label()
        self.version_label.set_halign(Gtk.Align.START)
        info_box.pack_start(self.version_label, False, False, 0)
        
        # Author
        self.author_label = Gtk.Label()
        self.author_label.set_halign(Gtk.Align.START)
        info_box.pack_start(self.author_label, False, False, 0)
        
        # Description
        self.description_label = Gtk.Label()
        self.description_label.set_halign(Gtk.Align.START)
        self.description_label.set_line_wrap(True)
        info_box.pack_start(self.description_label, False, False, 0)
        
        # Dependencies
        self.dependencies_label = Gtk.Label()
        self.dependencies_label.set_halign(Gtk.Align.START)
        self.dependencies_label.set_line_wrap(True)
        info_box.pack_start(self.dependencies_label, False, False, 0)
        
        self.info_frame.add(info_box)
    
    def _create_permissions_section(self):
        """Create permissions section"""
        permissions_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        permissions_box.set_margin_top(10)
        permissions_box.set_margin_bottom(10)
        permissions_box.set_margin_left(10)
        permissions_box.set_margin_right(10)
        
        # Permissions list
        self.permissions_store = Gtk.ListStore(bool, str, str, str)  # granted, name, description, level
        self.permissions_tree = Gtk.TreeView(self.permissions_store)
        
        # Granted column
        granted_renderer = Gtk.CellRendererToggle()
        granted_renderer.connect("toggled", self._on_permission_toggled)
        granted_column = Gtk.TreeViewColumn("Granted", granted_renderer, active=0)
        self.permissions_tree.append_column(granted_column)
        
        # Permission name column
        name_renderer = Gtk.CellRendererText()
        name_column = Gtk.TreeViewColumn("Permission", name_renderer, text=1)
        self.permissions_tree.append_column(name_column)
        
        # Level column
        level_renderer = Gtk.CellRendererText()
        level_column = Gtk.TreeViewColumn("Level", level_renderer, text=3)
        self.permissions_tree.append_column(level_column)
        
        # Scrolled window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.add(self.permissions_tree)
        scrolled.set_size_request(-1, 150)
        permissions_box.pack_start(scrolled, True, True, 0)
        
        self.permissions_frame.add(permissions_box)
    
    def _create_config_section(self):
        """Create configuration section"""
        config_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        config_box.set_margin_top(10)
        config_box.set_margin_bottom(10)
        config_box.set_margin_left(10)
        config_box.set_margin_right(10)
        
        # Configuration editor
        self.config_scrolled = Gtk.ScrolledWindow()
        self.config_scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        
        self.config_textview = Gtk.TextView()
        self.config_textview.set_editable(True)
        self.config_scrolled.add(self.config_textview)
        
        config_box.pack_start(self.config_scrolled, True, True, 0)
        
        self.config_frame.add(config_box)
    
    def _create_action_buttons(self, content_area):
        """Create action buttons"""
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        button_box.set_margin_top(10)
        
        # Reload button
        self.reload_button = Gtk.Button(label="Reload Plugin")
        self.reload_button.connect("clicked", self._on_reload_clicked)
        self.reload_button.set_sensitive(False)
        button_box.pack_start(self.reload_button, False, False, 0)
        
        # Install button
        self.install_button = Gtk.Button(label="Install Plugin...")
        self.install_button.connect("clicked", self._on_install_clicked)
        button_box.pack_start(self.install_button, False, False, 0)
        
        # Remove button
        self.remove_button = Gtk.Button(label="Remove Plugin")
        self.remove_button.connect("clicked", self._on_remove_clicked)
        self.remove_button.set_sensitive(False)
        button_box.pack_start(self.remove_button, False, False, 0)
        
        content_area.pack_start(button_box, False, False, 0)
    
    def _populate_plugins(self):
        """Populate the plugin list"""
        self.plugin_store.clear()
        
        descriptors = self.plugin_manager.get_all_descriptors()
        for name, descriptor in descriptors.items():
            plugin = self.plugin_manager.get_plugin(name)
            status = "Loaded" if plugin else "Available"
            
            self.plugin_store.append([
                descriptor.enabled,
                descriptor.name,
                descriptor.version,
                descriptor.author,
                status
            ])
    
    def _on_plugin_toggled(self, renderer, path):
        """Handle plugin enabled/disabled toggle"""
        iter = self.plugin_store.get_iter(path)
        enabled = self.plugin_store.get_value(iter, 0)
        plugin_name = self.plugin_store.get_value(iter, 1)
        
        if enabled:
            self.plugin_manager.disable_plugin(plugin_name)
        else:
            self.plugin_manager.enable_plugin(plugin_name)
        
        self.plugin_store.set_value(iter, 0, not enabled)
        self._populate_plugins()
    
    def _on_plugin_selected(self, selection):
        """Handle plugin selection"""
        model, iter = selection.get_selected()
        if iter:
            plugin_name = model.get_value(iter, 1)
            self._show_plugin_details(plugin_name)
            self.reload_button.set_sensitive(True)
            self.remove_button.set_sensitive(True)
        else:
            self._clear_plugin_details()
            self.reload_button.set_sensitive(False)
            self.remove_button.set_sensitive(False)
    
    def _show_plugin_details(self, plugin_name: str):
        """Show details for selected plugin"""
        descriptor = self.plugin_manager.get_plugin_descriptor(plugin_name)
        if not descriptor:
            return
        
        # Update info labels
        self.name_label.set_markup(f"<b>Name:</b> {descriptor.name}")
        self.version_label.set_markup(f"<b>Version:</b> {descriptor.version}")
        self.author_label.set_markup(f"<b>Author:</b> {descriptor.author}")
        self.description_label.set_markup(f"<b>Description:</b> {descriptor.description}")
        
        deps = ", ".join(descriptor.dependencies) if descriptor.dependencies else "None"
        self.dependencies_label.set_markup(f"<b>Dependencies:</b> {deps}")
        
        # Update permissions
        self._populate_permissions(plugin_name)
        
        # Update configuration
        self._populate_configuration(descriptor)
    
    def _populate_permissions(self, plugin_name: str):
        """Populate permissions for plugin"""
        self.permissions_store.clear()
        
        granted_permissions = self.plugin_manager.service_container.plugin_security.get_plugin_permissions(plugin_name)
        
        for perm_name, permission in DEFAULT_PERMISSIONS.items():
            granted = perm_name in granted_permissions
            self.permissions_store.append([
                granted,
                permission.name,
                permission.description,
                permission.level
            ])
    
    def _populate_configuration(self, descriptor: PluginDescriptor):
        """Populate configuration for plugin"""
        config_buffer = self.config_textview.get_buffer()
        
        # Load plugin configuration
        config_text = ""
        if descriptor.properties:
            import yaml
            config_text = yaml.dump(descriptor.properties, default_flow_style=False)
        
        config_buffer.set_text(config_text)
    
    def _clear_plugin_details(self):
        """Clear plugin details"""
        self.name_label.set_text("")
        self.version_label.set_text("")
        self.author_label.set_text("")
        self.description_label.set_text("")
        self.dependencies_label.set_text("")
        self.permissions_store.clear()
        self.config_textview.get_buffer().set_text("")
    
    def _on_permission_toggled(self, renderer, path):
        """Handle permission toggle"""
        iter = self.permissions_store.get_iter(path)
        granted = self.permissions_store.get_value(iter, 0)
        permission_name = self.permissions_store.get_value(iter, 1)
        
        # Get selected plugin
        selection = self.plugin_tree.get_selection()
        model, plugin_iter = selection.get_selected()
        if plugin_iter:
            plugin_name = model.get_value(plugin_iter, 1)
            
            # Update permission
            current_permissions = self.plugin_manager.service_container.plugin_security.get_plugin_permissions(plugin_name)
            if granted:
                current_permissions.discard(permission_name)
            else:
                current_permissions.add(permission_name)
            
            self.plugin_manager.service_container.plugin_security.set_plugin_permissions(plugin_name, current_permissions)
            self.permissions_store.set_value(iter, 0, not granted)
    
    def _on_reload_clicked(self, button):
        """Handle reload button click"""
        selection = self.plugin_tree.get_selection()
        model, iter = selection.get_selected()
        if iter:
            plugin_name = model.get_value(iter, 1)
            success = self.plugin_manager.reload_plugin(plugin_name)
            
            if success:
                self._show_message("Plugin reloaded successfully", "info")
            else:
                self._show_message("Failed to reload plugin", "error")
            
            self._populate_plugins()
    
    def _on_install_clicked(self, button):
        """Handle install button click"""
        dialog = Gtk.FileChooserDialog(
            "Select Plugin Archive",
            self,
            Gtk.FileChooserAction.OPEN,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        )
        
        # Add filters
        filter_zip = Gtk.FileFilter()
        filter_zip.set_name("Plugin Archives (*.zip)")
        filter_zip.add_pattern("*.zip")
        dialog.add_filter(filter_zip)
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            self._install_plugin(filename)
        
        dialog.destroy()
    
    def _on_remove_clicked(self, button):
        """Handle remove button click"""
        selection = self.plugin_tree.get_selection()
        model, iter = selection.get_selected()
        if iter:
            plugin_name = model.get_value(iter, 1)
            
            dialog = Gtk.MessageDialog(
                self,
                Gtk.DialogFlags.MODAL,
                Gtk.MessageType.WARNING,
                Gtk.ButtonsType.YES_NO,
                f"Are you sure you want to remove plugin '{plugin_name}'?"
            )
            
            response = dialog.run()
            if response == Gtk.ResponseType.YES:
                self._remove_plugin(plugin_name)
            
            dialog.destroy()
    
    def _install_plugin(self, filename: str):
        """Install plugin from file"""
        try:
            import zipfile
            import tempfile
            
            with tempfile.TemporaryDirectory() as temp_dir:
                # Extract plugin
                with zipfile.ZipFile(filename, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                
                # Find plugin.yml
                plugin_yml = None
                for root, dirs, files in os.walk(temp_dir):
                    if 'plugin.yml' in files:
                        plugin_yml = Path(root) / 'plugin.yml'
                        break
                
                if not plugin_yml:
                    self._show_message("Invalid plugin archive: plugin.yml not found", "error")
                    return
                
                # Load descriptor
                descriptor = PluginDescriptor(plugin_yml)
                
                # Copy to plugins directory
                plugin_dir = Path.home() / '.vcctl' / 'plugins' / descriptor.name
                plugin_dir.mkdir(parents=True, exist_ok=True)
                
                import shutil
                shutil.copytree(plugin_yml.parent, plugin_dir, dirs_exist_ok=True)
                
                # Refresh plugin list
                self.plugin_manager.discover_plugins()
                self._populate_plugins()
                
                self._show_message(f"Plugin '{descriptor.name}' installed successfully", "info")
                
        except Exception as e:
            self._show_message(f"Failed to install plugin: {e}", "error")
    
    def _remove_plugin(self, plugin_name: str):
        """Remove plugin"""
        try:
            # Unload plugin first
            self.plugin_manager.unload_plugin(plugin_name)
            
            # Remove plugin directory
            descriptor = self.plugin_manager.get_plugin_descriptor(plugin_name)
            if descriptor:
                import shutil
                shutil.rmtree(descriptor.plugin_dir)
            
            # Refresh plugin list
            self.plugin_manager.discover_plugins()
            self._populate_plugins()
            
            self._show_message(f"Plugin '{plugin_name}' removed successfully", "info")
            
        except Exception as e:
            self._show_message(f"Failed to remove plugin: {e}", "error")
    
    def _show_message(self, message: str, message_type: str):
        """Show message dialog"""
        if message_type == "error":
            msg_type = Gtk.MessageType.ERROR
        elif message_type == "warning":
            msg_type = Gtk.MessageType.WARNING
        else:
            msg_type = Gtk.MessageType.INFO
        
        dialog = Gtk.MessageDialog(
            self,
            Gtk.DialogFlags.MODAL,
            msg_type,
            Gtk.ButtonsType.OK,
            message
        )
        dialog.run()
        dialog.destroy()
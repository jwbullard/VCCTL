#!/usr/bin/env python3
"""
VCCTL Keyboard Shortcuts Manager

Provides comprehensive keyboard navigation and shortcuts for VCCTL application.
Implements accessibility standards and scientific software conventions.
"""

import gi
import logging
from typing import Dict, Optional, Callable, List, Tuple, Any
from dataclasses import dataclass
from enum import Enum

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GObject


class ShortcutCategory(Enum):
    """Categories of keyboard shortcuts."""
    FILE = "file"
    EDIT = "edit"
    VIEW = "view"
    NAVIGATION = "navigation"
    OPERATION = "operation"
    HELP = "help"


@dataclass
class KeyboardShortcut:
    """Represents a keyboard shortcut."""
    key: str
    modifiers: Gdk.ModifierType
    callback: Callable
    description: str
    category: ShortcutCategory
    context: Optional[str] = None  # Widget context where shortcut is active
    enabled: bool = True


class KeyboardManager(GObject.Object):
    """
    Manages keyboard shortcuts and navigation for VCCTL.
    
    Features:
    - Application-wide keyboard shortcuts
    - Context-sensitive shortcuts
    - Accessibility navigation
    - Customizable key bindings
    - Help system integration
    """
    
    __gsignals__ = {
        'shortcut-activated': (GObject.SignalFlags.RUN_FIRST, None, (str, str)),
    }
    
    def __init__(self, main_window: Gtk.ApplicationWindow):
        super().__init__()
        self.logger = logging.getLogger('VCCTL.KeyboardManager')
        self.main_window = main_window
        
        # Shortcut registry
        self.shortcuts: Dict[str, KeyboardShortcut] = {}
        self.accelerator_group = Gtk.AccelGroup()
        
        # Add accelerator group to main window
        self.main_window.add_accel_group(self.accelerator_group)
        
        # Setup default shortcuts
        self._setup_default_shortcuts()
        
        # Connect keyboard events
        self.main_window.connect('key-press-event', self._on_key_press)
        
        self.logger.info("Keyboard manager initialized")
    
    def _setup_default_shortcuts(self) -> None:
        """Setup default VCCTL keyboard shortcuts."""
        
        # File operations
        self.register_shortcut(
            'file_new', 'n', Gdk.ModifierType.CONTROL_MASK,
            self._on_file_new, "New project", ShortcutCategory.FILE
        )
        
        self.register_shortcut(
            'file_open', 'o', Gdk.ModifierType.CONTROL_MASK,
            self._on_file_open, "Open project", ShortcutCategory.FILE
        )
        
        self.register_shortcut(
            'file_save', 's', Gdk.ModifierType.CONTROL_MASK,
            self._on_file_save, "Save project", ShortcutCategory.FILE
        )
        
        self.register_shortcut(
            'file_save_as', 's', Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.SHIFT_MASK,
            self._on_file_save_as, "Save project as...", ShortcutCategory.FILE
        )
        
        # Edit operations
        self.register_shortcut(
            'edit_copy', 'c', Gdk.ModifierType.CONTROL_MASK,
            self._on_edit_copy, "Copy", ShortcutCategory.EDIT
        )
        
        self.register_shortcut(
            'edit_paste', 'v', Gdk.ModifierType.CONTROL_MASK,
            self._on_edit_paste, "Paste", ShortcutCategory.EDIT
        )
        
        self.register_shortcut(
            'edit_undo', 'z', Gdk.ModifierType.CONTROL_MASK,
            self._on_edit_undo, "Undo", ShortcutCategory.EDIT
        )
        
        self.register_shortcut(
            'edit_redo', 'y', Gdk.ModifierType.CONTROL_MASK,
            self._on_edit_redo, "Redo", ShortcutCategory.EDIT
        )
        
        # View operations
        self.register_shortcut(
            'view_zoom_in', 'plus', Gdk.ModifierType.CONTROL_MASK,
            self._on_view_zoom_in, "Zoom in", ShortcutCategory.VIEW
        )
        
        self.register_shortcut(
            'view_zoom_out', 'minus', Gdk.ModifierType.CONTROL_MASK,
            self._on_view_zoom_out, "Zoom out", ShortcutCategory.VIEW
        )
        
        self.register_shortcut(
            'view_zoom_reset', '0', Gdk.ModifierType.CONTROL_MASK,
            self._on_view_zoom_reset, "Reset zoom", ShortcutCategory.VIEW
        )
        
        # Navigation
        self.register_shortcut(
            'nav_materials', '1', Gdk.ModifierType.CONTROL_MASK,
            self._on_nav_materials, "Go to Materials panel", ShortcutCategory.NAVIGATION
        )
        
        self.register_shortcut(
            'nav_mix_design', '2', Gdk.ModifierType.CONTROL_MASK,
            self._on_nav_mix_design, "Go to Mix Design panel", ShortcutCategory.NAVIGATION
        )
        
        self.register_shortcut(
            'nav_microstructure', '3', Gdk.ModifierType.CONTROL_MASK,
            self._on_nav_microstructure, "Go to Microstructure panel", ShortcutCategory.NAVIGATION
        )
        
        self.register_shortcut(
            'nav_hydration', '4', Gdk.ModifierType.CONTROL_MASK,
            self._on_nav_hydration, "Go to Hydration panel", ShortcutCategory.NAVIGATION
        )
        
        self.register_shortcut(
            'nav_operations', '5', Gdk.ModifierType.CONTROL_MASK,
            self._on_nav_operations, "Go to Operations panel", ShortcutCategory.NAVIGATION
        )
        
        # Help
        self.register_shortcut(
            'help_show', 'F1', Gdk.ModifierType(0),
            self._on_show_help, "Show help", ShortcutCategory.HELP
        )
        
        self.register_shortcut(
            'help_shortcuts', 'question', Gdk.ModifierType.CONTROL_MASK,
            self._on_show_shortcuts, "Show keyboard shortcuts", ShortcutCategory.HELP
        )
        
        # Accessibility shortcuts
        self.register_shortcut(
            'accessibility_toggle', 'a', Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.SHIFT_MASK,
            self._on_toggle_accessibility, "Toggle accessibility mode", ShortcutCategory.VIEW
        )
        
        self.register_shortcut(
            'high_contrast_toggle', 'h', Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.SHIFT_MASK,
            self._on_toggle_high_contrast, "Toggle high contrast", ShortcutCategory.VIEW
        )
        
        self.register_shortcut(
            'file_import', 'i', Gdk.ModifierType.CONTROL_MASK,
            self._on_file_import, "Import data", ShortcutCategory.FILE
        )
        
        self.register_shortcut(
            'file_export', 'e', Gdk.ModifierType.CONTROL_MASK,
            self._on_file_export, "Export data", ShortcutCategory.FILE
        )
        
        self.register_shortcut(
            'file_quit', 'q', Gdk.ModifierType.CONTROL_MASK,
            self._on_file_quit, "Quit application", ShortcutCategory.FILE
        )
        
        # Edit operations
        self.register_shortcut(
            'edit_undo', 'z', Gdk.ModifierType.CONTROL_MASK,
            self._on_edit_undo, "Undo", ShortcutCategory.EDIT
        )
        
        self.register_shortcut(
            'edit_redo', 'y', Gdk.ModifierType.CONTROL_MASK,
            self._on_edit_redo, "Redo", ShortcutCategory.EDIT
        )
        
        self.register_shortcut(
            'edit_cut', 'x', Gdk.ModifierType.CONTROL_MASK,
            self._on_edit_cut, "Cut", ShortcutCategory.EDIT
        )
        
        self.register_shortcut(
            'edit_copy', 'c', Gdk.ModifierType.CONTROL_MASK,
            self._on_edit_copy, "Copy", ShortcutCategory.EDIT
        )
        
        self.register_shortcut(
            'edit_paste', 'v', Gdk.ModifierType.CONTROL_MASK,
            self._on_edit_paste, "Paste", ShortcutCategory.EDIT
        )
        
        self.register_shortcut(
            'edit_select_all', 'a', Gdk.ModifierType.CONTROL_MASK,
            self._on_edit_select_all, "Select all", ShortcutCategory.EDIT
        )
        
        self.register_shortcut(
            'edit_find', 'f', Gdk.ModifierType.CONTROL_MASK,
            self._on_edit_find, "Find", ShortcutCategory.EDIT
        )
        
        self.register_shortcut(
            'edit_preferences', 'comma', Gdk.ModifierType.CONTROL_MASK,
            self._on_edit_preferences, "Preferences", ShortcutCategory.EDIT
        )
        
        # View operations
        self.register_shortcut(
            'view_zoom_in', 'plus', Gdk.ModifierType.CONTROL_MASK,
            self._on_view_zoom_in, "Zoom in", ShortcutCategory.VIEW
        )
        
        self.register_shortcut(
            'view_zoom_out', 'minus', Gdk.ModifierType.CONTROL_MASK,
            self._on_view_zoom_out, "Zoom out", ShortcutCategory.VIEW
        )
        
        self.register_shortcut(
            'view_zoom_reset', '0', Gdk.ModifierType.CONTROL_MASK,
            self._on_view_zoom_reset, "Reset zoom", ShortcutCategory.VIEW
        )
        
        self.register_shortcut(
            'view_fullscreen', 'F11', Gdk.ModifierType(0),
            self._on_view_fullscreen, "Toggle fullscreen", ShortcutCategory.VIEW
        )
        
        self.register_shortcut(
            'view_refresh', 'F5', Gdk.ModifierType(0),
            self._on_view_refresh, "Refresh view", ShortcutCategory.VIEW
        )
        
        # Navigation shortcuts
        self.register_shortcut(
            'nav_next_tab', 'Tab', Gdk.ModifierType.CONTROL_MASK,
            self._on_nav_next_tab, "Next tab", ShortcutCategory.NAVIGATION
        )
        
        self.register_shortcut(
            'nav_prev_tab', 'Tab', Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.SHIFT_MASK,
            self._on_nav_prev_tab, "Previous tab", ShortcutCategory.NAVIGATION
        )
        
        self.register_shortcut(
            'nav_materials', '1', Gdk.ModifierType.CONTROL_MASK,
            self._on_nav_materials, "Materials panel", ShortcutCategory.NAVIGATION
        )
        
        self.register_shortcut(
            'nav_mix_design', '2', Gdk.ModifierType.CONTROL_MASK,
            self._on_nav_mix_design, "Mix design panel", ShortcutCategory.NAVIGATION
        )
        
        self.register_shortcut(
            'nav_microstructure', '3', Gdk.ModifierType.CONTROL_MASK,
            self._on_nav_microstructure, "Microstructure panel", ShortcutCategory.NAVIGATION
        )
        
        self.register_shortcut(
            'nav_hydration', '4', Gdk.ModifierType.CONTROL_MASK,
            self._on_nav_hydration, "Hydration panel", ShortcutCategory.NAVIGATION
        )
        
        self.register_shortcut(
            'nav_file_management', '5', Gdk.ModifierType.CONTROL_MASK,
            self._on_nav_file_management, "File management panel", ShortcutCategory.NAVIGATION
        )
        
        self.register_shortcut(
            'nav_operations', '6', Gdk.ModifierType.CONTROL_MASK,
            self._on_nav_operations, "Operations monitoring panel", ShortcutCategory.NAVIGATION
        )
        
        # Operation shortcuts
        self.register_shortcut(
            'op_run_simulation', 'F9', Gdk.ModifierType(0),
            self._on_op_run_simulation, "Run simulation", ShortcutCategory.OPERATION
        )
        
        self.register_shortcut(
            'op_stop_simulation', 'F10', Gdk.ModifierType(0),
            self._on_op_stop_simulation, "Stop simulation", ShortcutCategory.OPERATION
        )
        
        self.register_shortcut(
            'op_pause_simulation', 'F8', Gdk.ModifierType(0),
            self._on_op_pause_simulation, "Pause simulation", ShortcutCategory.OPERATION
        )
        
        # Help shortcuts
        self.register_shortcut(
            'help_shortcuts', 'F1', Gdk.ModifierType(0),
            self._on_help_shortcuts, "Show keyboard shortcuts", ShortcutCategory.HELP
        )
        
        self.register_shortcut(
            'help_about', 'F1', Gdk.ModifierType.SHIFT_MASK,
            self._on_help_about, "About VCCTL", ShortcutCategory.HELP
        )
        
        self.register_shortcut(
            'help_documentation', 'F12', Gdk.ModifierType(0),
            self._on_help_documentation, "Documentation", ShortcutCategory.HELP
        )
    
    def register_shortcut(self, 
                         name: str,
                         key: str, 
                         modifiers: Gdk.ModifierType,
                         callback: Callable,
                         description: str,
                         category: ShortcutCategory,
                         context: Optional[str] = None) -> None:
        """Register a keyboard shortcut."""
        try:
            # Parse key
            keyval = Gdk.keyval_from_name(key)
            if keyval == Gdk.KEY_VoidSymbol:
                self.logger.warning(f"Invalid key name: {key}")
                return
            
            # Create shortcut
            shortcut = KeyboardShortcut(
                key=key,
                modifiers=modifiers,
                callback=callback,
                description=description,
                category=category,
                context=context
            )
            
            # Store shortcut
            self.shortcuts[name] = shortcut
            
            # Add to accelerator group
            self.accelerator_group.connect(
                keyval, modifiers, Gtk.AccelFlags.VISIBLE,
                lambda *args: self._execute_shortcut(name)
            )
            
            self.logger.debug(f"Registered shortcut: {name} ({key})")
            
        except Exception as e:
            self.logger.error(f"Failed to register shortcut {name}: {e}")
    
    def unregister_shortcut(self, name: str) -> None:
        """Unregister a keyboard shortcut."""
        if name in self.shortcuts:
            shortcut = self.shortcuts[name]
            keyval = Gdk.keyval_from_name(shortcut.key)
            
            # Remove from accelerator group
            self.accelerator_group.disconnect_key(keyval, shortcut.modifiers)
            
            # Remove from registry
            del self.shortcuts[name]
            
            self.logger.debug(f"Unregistered shortcut: {name}")
    
    def enable_shortcut(self, name: str) -> None:
        """Enable a keyboard shortcut."""
        if name in self.shortcuts:
            self.shortcuts[name].enabled = True
    
    def disable_shortcut(self, name: str) -> None:
        """Disable a keyboard shortcut."""
        if name in self.shortcuts:
            self.shortcuts[name].enabled = False
    
    def get_shortcuts_by_category(self, category: ShortcutCategory) -> List[KeyboardShortcut]:
        """Get all shortcuts in a category."""
        return [shortcut for shortcut in self.shortcuts.values() 
                if shortcut.category == category]
    
    def get_all_shortcuts(self) -> Dict[str, KeyboardShortcut]:
        """Get all registered shortcuts."""
        return self.shortcuts.copy()
    
    def _execute_shortcut(self, name: str) -> bool:
        """Execute a keyboard shortcut."""
        if name not in self.shortcuts:
            return False
        
        shortcut = self.shortcuts[name]
        
        if not shortcut.enabled:
            return False
        
        try:
            # Check context if specified
            if shortcut.context:
                focused_widget = self.main_window.get_focus()
                if not self._widget_matches_context(focused_widget, shortcut.context):
                    return False
            
            # Execute callback
            result = shortcut.callback()
            
            # Emit signal
            self.emit('shortcut-activated', name, shortcut.description)
            
            self.logger.debug(f"Executed shortcut: {name}")
            return result if result is not None else True
            
        except Exception as e:
            self.logger.error(f"Error executing shortcut {name}: {e}")
            return False
    
    def _widget_matches_context(self, widget: Optional[Gtk.Widget], context: str) -> bool:
        """Check if widget matches the specified context."""
        if not widget:
            return False
        
        # Simple context matching - can be extended
        widget_name = widget.__class__.__name__.lower()
        return context.lower() in widget_name
    
    def _on_key_press(self, widget: Gtk.Widget, event: Gdk.EventKey) -> bool:
        """Handle key press events for custom shortcuts."""
        # This is handled by the accelerator group, but can be extended
        # for context-sensitive shortcuts
        return False
    
    def show_shortcuts_dialog(self) -> None:
        """Show keyboard shortcuts help dialog."""
        dialog = Gtk.Dialog(
            title="Keyboard Shortcuts",
            parent=self.main_window,
            flags=Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT
        )
        dialog.add_button("Close", Gtk.ResponseType.CLOSE)
        dialog.set_default_size(600, 500)
        
        content_area = dialog.get_content_area()
        
        # Create notebook for different categories
        notebook = Gtk.Notebook()
        
        for category in ShortcutCategory:
            shortcuts = self.get_shortcuts_by_category(category)
            if not shortcuts:
                continue
            
            # Create scrolled window for category
            scrolled = Gtk.ScrolledWindow()
            scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
            
            # Create list store
            store = Gtk.ListStore(str, str)  # Shortcut, Description
            
            for shortcut in shortcuts:
                shortcut_text = self._format_shortcut_text(shortcut)
                store.append([shortcut_text, shortcut.description])
            
            # Create tree view
            treeview = Gtk.TreeView(model=store)
            
            # Add columns
            shortcut_column = Gtk.TreeViewColumn("Shortcut")
            shortcut_renderer = Gtk.CellRendererText()
            shortcut_renderer.set_property("font", "monospace")
            shortcut_column.pack_start(shortcut_renderer, True)
            shortcut_column.add_attribute(shortcut_renderer, "text", 0)
            treeview.append_column(shortcut_column)
            
            desc_column = Gtk.TreeViewColumn("Description")
            desc_renderer = Gtk.CellRendererText()
            desc_column.pack_start(desc_renderer, True)
            desc_column.add_attribute(desc_renderer, "text", 1)
            treeview.append_column(desc_column)
            
            scrolled.add(treeview)
            
            # Add to notebook
            label = Gtk.Label(category.value.replace('_', ' ').title())
            notebook.append_page(scrolled, label)
        
        content_area.pack_start(notebook, True, True, 0)
        dialog.show_all()
        dialog.run()
        dialog.destroy()
    
    def _format_shortcut_text(self, shortcut: KeyboardShortcut) -> str:
        """Format shortcut for display."""
        parts = []
        
        if shortcut.modifiers & Gdk.ModifierType.CONTROL_MASK:
            parts.append("Ctrl")
        if shortcut.modifiers & Gdk.ModifierType.SHIFT_MASK:
            parts.append("Shift")
        if shortcut.modifiers & Gdk.ModifierType.MOD1_MASK:  # Alt
            parts.append("Alt")
        
        # Format key name
        key_name = shortcut.key
        if key_name.startswith("F") and key_name[1:].isdigit():
            # Function key
            parts.append(key_name)
        elif key_name == "Tab":
            parts.append("Tab")
        elif key_name == "Return":
            parts.append("Enter")
        elif key_name == "space":
            parts.append("Space")
        elif key_name == "comma":
            parts.append(",")
        elif key_name == "plus":
            parts.append("+")
        elif key_name == "minus":
            parts.append("-")
        else:
            parts.append(key_name.upper())
        
        return " + ".join(parts)
    
    # Default shortcut handlers
    
    def _on_file_new(self) -> None:
        """Handle file new shortcut."""
        self.logger.info("File new shortcut activated")
        # Implementation depends on main window structure
    
    def _on_file_open(self) -> None:
        """Handle file open shortcut."""
        self.logger.info("File open shortcut activated")
    
    def _on_file_save(self) -> None:
        """Handle file save shortcut."""
        self.logger.info("File save shortcut activated")
    
    def _on_file_save_as(self) -> None:
        """Handle file save as shortcut."""
        self.logger.info("File save as shortcut activated")
    
    def _on_file_import(self) -> None:
        """Handle file import shortcut."""
        self.logger.info("File import shortcut activated")
    
    def _on_file_export(self) -> None:
        """Handle file export shortcut."""
        self.logger.info("File export shortcut activated")
    
    def _on_file_quit(self) -> None:
        """Handle file quit shortcut."""
        self.main_window.close()
    
    def _on_edit_undo(self) -> None:
        """Handle edit undo shortcut."""
        self.logger.info("Edit undo shortcut activated")
    
    def _on_edit_redo(self) -> None:
        """Handle edit redo shortcut."""
        self.logger.info("Edit redo shortcut activated")
    
    def _on_edit_cut(self) -> None:
        """Handle edit cut shortcut."""
        self.logger.info("Edit cut shortcut activated")
    
    def _on_edit_copy(self) -> None:
        """Handle edit copy shortcut."""
        self.logger.info("Edit copy shortcut activated")
    
    def _on_edit_paste(self) -> None:
        """Handle edit paste shortcut."""
        self.logger.info("Edit paste shortcut activated")
    
    def _on_edit_select_all(self) -> None:
        """Handle edit select all shortcut."""
        self.logger.info("Edit select all shortcut activated")
    
    def _on_edit_find(self) -> None:
        """Handle edit find shortcut."""
        self.logger.info("Edit find shortcut activated")
    
    def _on_edit_preferences(self) -> None:
        """Handle edit preferences shortcut."""
        self.logger.info("Edit preferences shortcut activated")
    
    def _on_view_zoom_in(self) -> None:
        """Handle view zoom in shortcut."""
        self.logger.info("View zoom in shortcut activated")
    
    def _on_view_zoom_out(self) -> None:
        """Handle view zoom out shortcut."""
        self.logger.info("View zoom out shortcut activated")
    
    def _on_view_zoom_reset(self) -> None:
        """Handle view zoom reset shortcut."""
        self.logger.info("View zoom reset shortcut activated")
    
    def _on_view_fullscreen(self) -> None:
        """Handle view fullscreen shortcut."""
        if self.main_window.is_maximized():
            self.main_window.unmaximize()
        else:
            self.main_window.maximize()
    
    def _on_view_refresh(self) -> None:
        """Handle view refresh shortcut."""
        self.logger.info("View refresh shortcut activated")
    
    def _on_nav_next_tab(self) -> None:
        """Handle navigation next tab shortcut."""
        self.logger.info("Navigation next tab shortcut activated")
    
    def _on_nav_prev_tab(self) -> None:
        """Handle navigation previous tab shortcut."""
        self.logger.info("Navigation previous tab shortcut activated")
    
    def _on_nav_materials(self) -> None:
        """Handle navigation to materials panel."""
        self.logger.info("Navigation to materials panel")
    
    def _on_nav_mix_design(self) -> None:
        """Handle navigation to mix design panel."""
        self.logger.info("Navigation to mix design panel")
    
    def _on_nav_microstructure(self) -> None:
        """Handle navigation to microstructure panel."""
        self.logger.info("Navigation to microstructure panel")
    
    def _on_nav_hydration(self) -> None:
        """Handle navigation to hydration panel."""
        self.logger.info("Navigation to hydration panel")
    
    def _on_nav_file_management(self) -> None:
        """Handle navigation to file management panel."""
        self.logger.info("Navigation to file management panel")
    
    def _on_nav_operations(self) -> None:
        """Handle navigation to operations panel."""
        self.logger.info("Navigation to operations panel")
    
    def _on_op_run_simulation(self) -> None:
        """Handle run simulation shortcut."""
        self.logger.info("Run simulation shortcut activated")
    
    def _on_op_stop_simulation(self) -> None:
        """Handle stop simulation shortcut."""
        self.logger.info("Stop simulation shortcut activated")
    
    def _on_op_pause_simulation(self) -> None:
        """Handle pause simulation shortcut."""
        self.logger.info("Pause simulation shortcut activated")
    
    def _on_help_shortcuts(self) -> None:
        """Handle help shortcuts shortcut."""
        self.show_shortcuts_dialog()
    
    def _on_help_about(self) -> None:
        """Handle help about shortcut."""
        self.logger.info("Help about shortcut activated")
    
    def _on_help_documentation(self) -> None:
        """Handle help documentation shortcut."""
        self.logger.info("Help documentation shortcut activated")
    
    def _on_show_help(self) -> None:
        """Handle show help shortcut."""
        self.logger.info("Show help shortcut activated")
    
    def _on_show_shortcuts(self) -> None:
        """Handle show shortcuts shortcut."""
        self.show_shortcuts_dialog()
    
    def _on_toggle_accessibility(self) -> None:
        """Handle toggle accessibility mode shortcut."""
        self.logger.info("Toggle accessibility mode shortcut activated")
    
    def _on_toggle_high_contrast(self) -> None:
        """Handle toggle high contrast shortcut."""
        self.logger.info("Toggle high contrast shortcut activated")


def create_keyboard_manager(main_window: Gtk.ApplicationWindow) -> KeyboardManager:
    """Create and configure keyboard manager."""
    return KeyboardManager(main_window)
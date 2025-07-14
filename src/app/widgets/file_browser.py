#!/usr/bin/env python3
"""
File Browser Widget for VCCTL

Provides a comprehensive file browser widget for managing project files,
with support for file operations, filtering, and context menus.
"""

import gi
import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Dict, List, Callable, Any
from enum import Enum

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GObject, Gio, GdkPixbuf, Pango

if TYPE_CHECKING:
    from app.windows.main_window import VCCTLMainWindow

from app.services.service_container import get_service_container


class FileType(Enum):
    """File type classification for browser."""
    DIRECTORY = "directory"
    JSON = "json"
    CSV = "csv"
    XML = "xml"
    TEXT = "text"
    BINARY = "binary"
    IMAGE = "image"
    UNKNOWN = "unknown"


class FileBrowserWidget(Gtk.Box):
    """
    File browser widget for VCCTL project file management.
    
    Features:
    - Tree view of directory structure
    - File type icons and classification
    - Context menus for file operations
    - Drag and drop support
    - File filtering and search
    - Multiple selection support
    """
    
    # Define custom signals
    __gsignals__ = {
        'file-selected': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        'file-activated': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        'files-selected': (GObject.SignalFlags.RUN_FIRST, None, (object,)),
        'directory-changed': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
    }
    
    def __init__(self, main_window: 'VCCTLMainWindow', show_hidden: bool = False):
        """Initialize the file browser widget."""
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        self.main_window = main_window
        self.logger = logging.getLogger('VCCTL.FileBrowser')
        self.service_container = get_service_container()
        self.show_hidden = show_hidden
        
        # Current directory and selection state
        self.current_directory = Path.home()
        self.selected_files = []
        self.file_filters = []
        
        # File operation callbacks
        self.operation_callbacks = {}
        
        # Setup UI components
        self._setup_ui()
        self._setup_file_store()
        self._setup_tree_view()
        self._setup_context_menu()
        self._connect_signals()
        
        # Load initial directory
        self.refresh_directory()
        
        self.logger.info("File browser widget initialized")
    
    def _setup_ui(self) -> None:
        """Setup the main UI layout."""
        # Create toolbar
        self._create_toolbar()
        
        # Create main content area
        self._create_content_area()
        
        # Create status bar
        self._create_status_area()
    
    def _create_toolbar(self) -> None:
        """Create the toolbar with navigation and actions."""
        toolbar = Gtk.Toolbar()
        toolbar.set_style(Gtk.ToolbarStyle.BOTH_HORIZ)
        
        # Back button
        self.back_button = Gtk.ToolButton()
        self.back_button.set_icon_name("go-previous")
        self.back_button.set_label("Back")
        self.back_button.set_tooltip_text("Go back to parent directory")
        self.back_button.connect('clicked', self._on_back_clicked)
        toolbar.insert(self.back_button, -1)
        
        # Up button
        self.up_button = Gtk.ToolButton()
        self.up_button.set_icon_name("go-up")
        self.up_button.set_label("Up")
        self.up_button.set_tooltip_text("Go to parent directory")
        self.up_button.connect('clicked', self._on_up_clicked)
        toolbar.insert(self.up_button, -1)
        
        # Home button
        home_button = Gtk.ToolButton()
        home_button.set_icon_name("go-home")
        home_button.set_label("Home")
        home_button.set_tooltip_text("Go to home directory")
        home_button.connect('clicked', self._on_home_clicked)
        toolbar.insert(home_button, -1)
        
        # Separator
        toolbar.insert(Gtk.SeparatorToolItem(), -1)
        
        # Refresh button
        refresh_button = Gtk.ToolButton()
        refresh_button.set_icon_name("view-refresh")
        refresh_button.set_label("Refresh")
        refresh_button.set_tooltip_text("Refresh current directory")
        refresh_button.connect('clicked', self._on_refresh_clicked)
        toolbar.insert(refresh_button, -1)
        
        # Create directory button
        create_dir_button = Gtk.ToolButton()
        create_dir_button.set_icon_name("folder-new")
        create_dir_button.set_label("New Folder")
        create_dir_button.set_tooltip_text("Create new directory")
        create_dir_button.connect('clicked', self._on_create_directory_clicked)
        toolbar.insert(create_dir_button, -1)
        
        # Separator
        toolbar.insert(Gtk.SeparatorToolItem(), -1)
        
        # View options
        view_button = Gtk.MenuToolButton()
        view_button.set_icon_name("preferences-desktop")
        view_button.set_label("View")
        view_button.set_tooltip_text("View options")
        
        # Create view menu
        view_menu = Gtk.Menu()
        
        # Show hidden files toggle
        self.show_hidden_item = Gtk.CheckMenuItem(label="Show Hidden Files")
        self.show_hidden_item.set_active(self.show_hidden)
        self.show_hidden_item.connect('toggled', self._on_show_hidden_toggled)
        view_menu.append(self.show_hidden_item)
        
        view_menu.show_all()
        view_button.set_menu(view_menu)
        toolbar.insert(view_button, -1)
        
        self.pack_start(toolbar, False, False, 0)
        
        # Path bar
        self._create_path_bar()
    
    def _create_path_bar(self) -> None:
        """Create the path navigation bar."""
        path_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        path_box.set_margin_left(10)
        path_box.set_margin_right(10)
        path_box.set_margin_top(5)
        path_box.set_margin_bottom(5)
        
        # Path label
        path_label = Gtk.Label("Location:")
        path_box.pack_start(path_label, False, False, 0)
        
        # Path entry
        self.path_entry = Gtk.Entry()
        self.path_entry.set_text(str(self.current_directory))
        self.path_entry.connect('activate', self._on_path_entry_activate)
        path_box.pack_start(self.path_entry, True, True, 0)
        
        # Browse button
        browse_button = Gtk.Button()
        browse_button.set_image(Gtk.Image.new_from_icon_name("folder-open", Gtk.IconSize.BUTTON))
        browse_button.set_tooltip_text("Browse for directory")
        browse_button.connect('clicked', self._on_browse_clicked)
        path_box.pack_start(browse_button, False, False, 0)
        
        self.pack_start(path_box, False, False, 0)
    
    def _create_content_area(self) -> None:
        """Create the main content area with tree view."""
        # Create scrolled window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_shadow_type(Gtk.ShadowType.IN)
        
        # Store and tree view will be created separately
        self.scrolled_window = scrolled
        self.pack_start(scrolled, True, True, 0)
    
    def _create_status_area(self) -> None:
        """Create the status bar."""
        self.status_bar = Gtk.Statusbar()
        self.status_context_id = self.status_bar.get_context_id("main")
        self.status_bar.push(self.status_context_id, "Ready")
        self.pack_start(self.status_bar, False, False, 0)
    
    def _setup_file_store(self) -> None:
        """Setup the file list store."""
        # Columns: icon, name, size, modified, type, full_path
        self.file_store = Gtk.ListStore(
            GdkPixbuf.Pixbuf,  # Icon
            str,               # Name
            str,               # Size
            str,               # Modified
            str,               # Type
            str,               # Full path
            bool               # Is directory
        )
        
        # Create filter model for search/filtering
        self.file_filter = self.file_store.filter_new()
        self.file_filter.set_visible_func(self._filter_func)
        
        # Create sort model
        self.file_sort = Gtk.TreeModelSort(model=self.file_filter)
        self.file_sort.set_sort_func(1, self._sort_func, None)
    
    def _setup_tree_view(self) -> None:
        """Setup the tree view for file display."""
        self.tree_view = Gtk.TreeView(model=self.file_sort)
        self.tree_view.set_enable_search(True)
        self.tree_view.set_search_column(1)  # Search by name
        self.tree_view.set_rubber_banding(True)
        
        # Allow multiple selection
        selection = self.tree_view.get_selection()
        selection.set_mode(Gtk.SelectionMode.MULTIPLE)
        
        # Create columns
        self._create_tree_columns()
        
        # Add to scrolled window
        self.scrolled_window.add(self.tree_view)
    
    def _create_tree_columns(self) -> None:
        """Create columns for the tree view."""
        # Icon + Name column
        column = Gtk.TreeViewColumn("Name")
        
        # Icon renderer
        icon_renderer = Gtk.CellRendererPixbuf()
        column.pack_start(icon_renderer, False)
        column.add_attribute(icon_renderer, "pixbuf", 0)
        
        # Name renderer
        name_renderer = Gtk.CellRendererText()
        name_renderer.set_property("ellipsize", Pango.EllipsizeMode.END)
        column.pack_start(name_renderer, True)
        column.add_attribute(name_renderer, "text", 1)
        
        column.set_sort_column_id(1)
        column.set_resizable(True)
        column.set_expand(True)
        self.tree_view.append_column(column)
        
        # Size column
        size_column = Gtk.TreeViewColumn("Size")
        size_renderer = Gtk.CellRendererText()
        size_column.pack_start(size_renderer, False)
        size_column.add_attribute(size_renderer, "text", 2)
        size_column.set_sort_column_id(2)
        size_column.set_resizable(True)
        self.tree_view.append_column(size_column)
        
        # Modified column
        modified_column = Gtk.TreeViewColumn("Modified")
        modified_renderer = Gtk.CellRendererText()
        modified_column.pack_start(modified_renderer, False)
        modified_column.add_attribute(modified_renderer, "text", 3)
        modified_column.set_sort_column_id(3)
        modified_column.set_resizable(True)
        self.tree_view.append_column(modified_column)
        
        # Type column
        type_column = Gtk.TreeViewColumn("Type")
        type_renderer = Gtk.CellRendererText()
        type_column.pack_start(type_renderer, False)
        type_column.add_attribute(type_renderer, "text", 4)
        type_column.set_sort_column_id(4)
        type_column.set_resizable(True)
        self.tree_view.append_column(type_column)
    
    def _setup_context_menu(self) -> None:
        """Setup context menu for file operations."""
        self.context_menu = Gtk.Menu()
        
        # Open
        open_item = Gtk.MenuItem(label="Open")
        open_item.connect('activate', self._on_context_open)
        self.context_menu.append(open_item)
        
        # Open with
        open_with_item = Gtk.MenuItem(label="Open With...")
        open_with_item.connect('activate', self._on_context_open_with)
        self.context_menu.append(open_with_item)
        
        # Separator
        self.context_menu.append(Gtk.SeparatorMenuItem())
        
        # Copy
        copy_item = Gtk.MenuItem(label="Copy")
        copy_item.connect('activate', self._on_context_copy)
        self.context_menu.append(copy_item)
        
        # Cut
        cut_item = Gtk.MenuItem(label="Cut")
        cut_item.connect('activate', self._on_context_cut)
        self.context_menu.append(cut_item)
        
        # Paste
        self.paste_item = Gtk.MenuItem(label="Paste")
        self.paste_item.connect('activate', self._on_context_paste)
        self.paste_item.set_sensitive(False)
        self.context_menu.append(self.paste_item)
        
        # Separator
        self.context_menu.append(Gtk.SeparatorMenuItem())
        
        # Rename
        rename_item = Gtk.MenuItem(label="Rename")
        rename_item.connect('activate', self._on_context_rename)
        self.context_menu.append(rename_item)
        
        # Delete
        delete_item = Gtk.MenuItem(label="Delete")
        delete_item.connect('activate', self._on_context_delete)
        self.context_menu.append(delete_item)
        
        # Separator
        self.context_menu.append(Gtk.SeparatorMenuItem())
        
        # Properties
        properties_item = Gtk.MenuItem(label="Properties")
        properties_item.connect('activate', self._on_context_properties)
        self.context_menu.append(properties_item)
        
        self.context_menu.show_all()
    
    def _connect_signals(self) -> None:
        """Connect widget signals."""
        # Tree view signals
        self.tree_view.connect('row-activated', self._on_row_activated)
        self.tree_view.connect('button-press-event', self._on_button_press)
        self.tree_view.connect('key-press-event', self._on_key_press)
        
        # Selection changed
        selection = self.tree_view.get_selection()
        selection.connect('changed', self._on_selection_changed)
    
    def _get_file_icon(self, file_path: Path, file_type: FileType) -> GdkPixbuf.Pixbuf:
        """Get appropriate icon for file type."""
        try:
            icon_theme = Gtk.IconTheme.get_default()
            icon_size = 16
            
            if file_type == FileType.DIRECTORY:
                icon_name = "folder"
            elif file_type == FileType.JSON:
                icon_name = "text-x-script"
            elif file_type == FileType.CSV:
                icon_name = "x-office-spreadsheet"
            elif file_type == FileType.XML:
                icon_name = "text-xml"
            elif file_type == FileType.TEXT:
                icon_name = "text-x-generic"
            elif file_type == FileType.IMAGE:
                icon_name = "image-x-generic"
            elif file_type == FileType.BINARY:
                icon_name = "application-octet-stream"
            else:
                icon_name = "text-x-generic"
            
            return icon_theme.load_icon(icon_name, icon_size, 0)
            
        except Exception as e:
            self.logger.warning(f"Failed to load icon for {file_path}: {e}")
            # Return default icon
            try:
                return icon_theme.load_icon("text-x-generic", 16, 0)
            except:
                return None
    
    def _classify_file_type(self, file_path: Path) -> FileType:
        """Classify file type based on extension and content."""
        if file_path.is_dir():
            return FileType.DIRECTORY
        
        suffix = file_path.suffix.lower()
        
        if suffix == '.json':
            return FileType.JSON
        elif suffix in ['.csv', '.tsv']:
            return FileType.CSV
        elif suffix in ['.xml', '.xsd']:
            return FileType.XML
        elif suffix in ['.txt', '.log', '.md', '.rst']:
            return FileType.TEXT
        elif suffix in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg']:
            return FileType.IMAGE
        elif suffix in ['.dat', '.bin', '.img']:
            return FileType.BINARY
        else:
            return FileType.UNKNOWN
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format."""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        if i == 0:
            return f"{int(size_bytes)} {size_names[i]}"
        else:
            return f"{size_bytes:.1f} {size_names[i]}"
    
    def _format_modification_time(self, mtime: float) -> str:
        """Format modification time."""
        import datetime
        dt = datetime.datetime.fromtimestamp(mtime)
        return dt.strftime("%Y-%m-%d %H:%M")
    
    def _filter_func(self, model, iter, data) -> bool:
        """Filter function for file display."""
        if not self.file_filters:
            return True
        
        file_path = model.get_value(iter, 5)  # Full path column
        file_name = model.get_value(iter, 1)  # Name column
        
        # Always show directories
        if model.get_value(iter, 6):  # Is directory column
            return True
        
        # Apply filters
        for filter_func in self.file_filters:
            if not filter_func(file_path, file_name):
                return False
        
        return True
    
    def _sort_func(self, model, iter1, iter2, user_data) -> int:
        """Custom sort function - directories first, then alphabetical."""
        is_dir1 = model.get_value(iter1, 6)
        is_dir2 = model.get_value(iter2, 6)
        
        # Directories come first
        if is_dir1 and not is_dir2:
            return -1
        elif not is_dir1 and is_dir2:
            return 1
        
        # Both same type, sort alphabetically
        name1 = model.get_value(iter1, 1).lower()
        name2 = model.get_value(iter2, 1).lower()
        
        if name1 < name2:
            return -1
        elif name1 > name2:
            return 1
        else:
            return 0
    
    def refresh_directory(self) -> None:
        """Refresh the current directory listing."""
        try:
            self.file_store.clear()
            
            if not self.current_directory.exists():
                self.logger.warning(f"Directory does not exist: {self.current_directory}")
                return
            
            # Update path entry
            self.path_entry.set_text(str(self.current_directory))
            
            # Update button states
            self.back_button.set_sensitive(self.current_directory != Path.home())
            self.up_button.set_sensitive(self.current_directory.parent != self.current_directory)
            
            file_count = 0
            dir_count = 0
            
            # Load directory contents
            try:
                for item in self.current_directory.iterdir():
                    # Skip hidden files if not showing them
                    if not self.show_hidden and item.name.startswith('.'):
                        continue
                    
                    try:
                        stat = item.stat()
                        file_type = self._classify_file_type(item)
                        icon = self._get_file_icon(item, file_type)
                        
                        if item.is_dir():
                            size_str = "—"
                            type_str = "Directory"
                            dir_count += 1
                        else:
                            size_str = self._format_file_size(stat.st_size)
                            type_str = file_type.value.title()
                            file_count += 1
                        
                        modified_str = self._format_modification_time(stat.st_mtime)
                        
                        self.file_store.append([
                            icon,
                            item.name,
                            size_str,
                            modified_str,
                            type_str,
                            str(item),
                            item.is_dir()
                        ])
                        
                    except (OSError, PermissionError) as e:
                        self.logger.warning(f"Cannot access {item}: {e}")
            
            except PermissionError as e:
                self.logger.error(f"Permission denied accessing directory: {e}")
                self.update_status(f"Permission denied: {self.current_directory}")
                return
            
            # Update status
            total_items = file_count + dir_count
            status_msg = f"{total_items} items ({dir_count} folders, {file_count} files)"
            self.update_status(status_msg)
            
            # Emit directory changed signal
            self.emit('directory-changed', str(self.current_directory))
            
        except Exception as e:
            self.logger.error(f"Failed to refresh directory: {e}")
            self.update_status(f"Error: {e}")
    
    def update_status(self, message: str) -> None:
        """Update status bar message."""
        self.status_bar.pop(self.status_context_id)
        self.status_bar.push(self.status_context_id, message)
    
    def set_directory(self, directory: Path) -> None:
        """Set current directory and refresh."""
        if directory.exists() and directory.is_dir():
            self.current_directory = directory
            self.refresh_directory()
        else:
            self.logger.warning(f"Invalid directory: {directory}")
    
    def get_selected_files(self) -> List[Path]:
        """Get list of currently selected file paths."""
        selection = self.tree_view.get_selection()
        model, paths = selection.get_selected_rows()
        
        selected_files = []
        for path in paths:
            iter = model.get_iter(path)
            file_path = model.get_value(iter, 5)  # Full path column
            selected_files.append(Path(file_path))
        
        return selected_files
    
    def add_file_filter(self, filter_func: Callable[[str, str], bool]) -> None:
        """Add a file filter function."""
        self.file_filters.append(filter_func)
        self.file_filter.refilter()
    
    def clear_file_filters(self) -> None:
        """Clear all file filters."""
        self.file_filters.clear()
        self.file_filter.refilter()
    
    # Event handlers
    
    def _on_back_clicked(self, button: Gtk.Button) -> None:
        """Handle back button click."""
        # For now, just go up one level (could implement history later)
        self._on_up_clicked(button)
    
    def _on_up_clicked(self, button: Gtk.Button) -> None:
        """Handle up button click."""
        parent = self.current_directory.parent
        if parent != self.current_directory:
            self.set_directory(parent)
    
    def _on_home_clicked(self, button: Gtk.Button) -> None:
        """Handle home button click."""
        self.set_directory(Path.home())
    
    def _on_refresh_clicked(self, button: Gtk.Button) -> None:
        """Handle refresh button click."""
        self.refresh_directory()
    
    def _on_create_directory_clicked(self, button: Gtk.Button) -> None:
        """Handle create directory button click."""
        dialog = Gtk.MessageDialog(
            transient_for=self.main_window,
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.OK_CANCEL,
            text="Create New Directory"
        )
        dialog.format_secondary_text("Enter the name for the new directory:")
        
        entry = Gtk.Entry()
        entry.set_text("New Folder")
        entry.set_activates_default(True)
        dialog.get_content_area().add(entry)
        dialog.get_content_area().show_all()
        dialog.set_default_response(Gtk.ResponseType.OK)
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            dir_name = entry.get_text().strip()
            if dir_name:
                try:
                    new_dir = self.current_directory / dir_name
                    new_dir.mkdir(exist_ok=False)
                    self.refresh_directory()
                except FileExistsError:
                    self.update_status(f"Directory '{dir_name}' already exists")
                except Exception as e:
                    self.update_status(f"Failed to create directory: {e}")
        
        dialog.destroy()
    
    def _on_show_hidden_toggled(self, item: Gtk.CheckMenuItem) -> None:
        """Handle show hidden files toggle."""
        self.show_hidden = item.get_active()
        self.refresh_directory()
    
    def _on_path_entry_activate(self, entry: Gtk.Entry) -> None:
        """Handle path entry activation."""
        path_text = entry.get_text().strip()
        try:
            new_path = Path(path_text).expanduser()
            self.set_directory(new_path)
        except Exception as e:
            self.update_status(f"Invalid path: {e}")
            entry.set_text(str(self.current_directory))
    
    def _on_browse_clicked(self, button: Gtk.Button) -> None:
        """Handle browse button click."""
        dialog = Gtk.FileChooserDialog(
            title="Select Directory",
            parent=self.main_window,
            action=Gtk.FileChooserAction.SELECT_FOLDER
        )
        dialog.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
        dialog.add_button(Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        dialog.set_current_folder(str(self.current_directory))
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            selected_dir = dialog.get_filename()
            self.set_directory(Path(selected_dir))
        
        dialog.destroy()
    
    def _on_row_activated(self, tree_view: Gtk.TreeView, path: Gtk.TreePath, column: Gtk.TreeViewColumn) -> None:
        """Handle row double-click/activation."""
        model = tree_view.get_model()
        iter = model.get_iter(path)
        file_path = Path(model.get_value(iter, 5))
        is_directory = model.get_value(iter, 6)
        
        if is_directory:
            self.set_directory(file_path)
        else:
            self.emit('file-activated', str(file_path))
    
    def _on_button_press(self, widget: Gtk.Widget, event: Gdk.EventButton) -> bool:
        """Handle button press events."""
        if event.button == 3:  # Right click
            # Show context menu
            self.context_menu.popup_at_pointer(event)
            return True
        return False
    
    def _on_key_press(self, widget: Gtk.Widget, event: Gdk.EventKey) -> bool:
        """Handle key press events."""
        if event.keyval == Gdk.KEY_Delete:
            self._on_context_delete(None)
            return True
        elif event.keyval == Gdk.KEY_F2:
            self._on_context_rename(None)
            return True
        elif event.keyval == Gdk.KEY_F5:
            self.refresh_directory()
            return True
        return False
    
    def _on_selection_changed(self, selection: Gtk.TreeSelection) -> None:
        """Handle selection change."""
        selected_files = self.get_selected_files()
        self.selected_files = selected_files
        
        if len(selected_files) == 1:
            self.emit('file-selected', str(selected_files[0]))
        
        self.emit('files-selected', selected_files)
    
    # Context menu handlers
    
    def _on_context_open(self, item: Gtk.MenuItem) -> None:
        """Handle context menu open."""
        selected_files = self.get_selected_files()
        if selected_files:
            file_path = selected_files[0]
            if file_path.is_dir():
                self.set_directory(file_path)
            else:
                self.emit('file-activated', str(file_path))
    
    def _on_context_open_with(self, item: Gtk.MenuItem) -> None:
        """Handle context menu open with."""
        # TODO: Implement open with dialog
        self.update_status("Open with functionality not yet implemented")
    
    def _on_context_copy(self, item: Gtk.MenuItem) -> None:
        """Handle context menu copy."""
        # TODO: Implement copy to clipboard
        self.update_status("Copy functionality not yet implemented")
    
    def _on_context_cut(self, item: Gtk.MenuItem) -> None:
        """Handle context menu cut."""
        # TODO: Implement cut to clipboard
        self.update_status("Cut functionality not yet implemented")
    
    def _on_context_paste(self, item: Gtk.MenuItem) -> None:
        """Handle context menu paste."""
        # TODO: Implement paste from clipboard
        self.update_status("Paste functionality not yet implemented")
    
    def _on_context_rename(self, item: Gtk.MenuItem) -> None:
        """Handle context menu rename."""
        selected_files = self.get_selected_files()
        if len(selected_files) == 1:
            file_path = selected_files[0]
            
            dialog = Gtk.MessageDialog(
                transient_for=self.main_window,
                flags=0,
                message_type=Gtk.MessageType.QUESTION,
                buttons=Gtk.ButtonsType.OK_CANCEL,
                text="Rename File"
            )
            dialog.format_secondary_text(f"Enter new name for '{file_path.name}':")
            
            entry = Gtk.Entry()
            entry.set_text(file_path.name)
            entry.set_activates_default(True)
            dialog.get_content_area().add(entry)
            dialog.get_content_area().show_all()
            dialog.set_default_response(Gtk.ResponseType.OK)
            
            response = dialog.run()
            if response == Gtk.ResponseType.OK:
                new_name = entry.get_text().strip()
                if new_name and new_name != file_path.name:
                    try:
                        new_path = file_path.parent / new_name
                        file_path.rename(new_path)
                        self.refresh_directory()
                    except Exception as e:
                        self.update_status(f"Failed to rename: {e}")
            
            dialog.destroy()
    
    def _on_context_delete(self, item: Gtk.MenuItem) -> None:
        """Handle context menu delete."""
        selected_files = self.get_selected_files()
        if not selected_files:
            return
        
        # Confirm deletion
        if len(selected_files) == 1:
            message = f"Delete '{selected_files[0].name}'?"
        else:
            message = f"Delete {len(selected_files)} selected items?"
        
        dialog = Gtk.MessageDialog(
            transient_for=self.main_window,
            flags=0,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Confirm Deletion"
        )
        dialog.format_secondary_text(message)
        
        response = dialog.run()
        if response == Gtk.ResponseType.YES:
            errors = []
            for file_path in selected_files:
                try:
                    if file_path.is_dir():
                        import shutil
                        shutil.rmtree(file_path)
                    else:
                        file_path.unlink()
                except Exception as e:
                    errors.append(f"{file_path.name}: {e}")
            
            if errors:
                self.update_status(f"Deletion errors: {'; '.join(errors[:3])}")
            else:
                self.update_status(f"Deleted {len(selected_files)} items")
            
            self.refresh_directory()
        
        dialog.destroy()
    
    def _on_context_properties(self, item: Gtk.MenuItem) -> None:
        """Handle context menu properties."""
        selected_files = self.get_selected_files()
        if selected_files:
            # TODO: Implement properties dialog
            self.update_status("Properties dialog not yet implemented")


# Register the widget as a GObject type
GObject.type_register(FileBrowserWidget)
#!/usr/bin/env python3
"""
Help Dialog

Provides the main help dialog window with navigation and content display.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, Pango, GdkPixbuf
from app.utils.icon_utils import create_icon_image
from pathlib import Path
from typing import Dict, List, Optional, Any
import re

from .help_manager import HelpManager, HelpSection, HelpTopic


class HelpDialog(Gtk.Dialog):
    """
    Main help dialog window.
    
    Features:
    - Tree navigation of help sections and topics
    - Content viewer with markdown-like formatting
    - Search functionality
    - Bookmarks and history
    - Print support
    """
    
    def __init__(self, parent_window, help_manager: HelpManager):
        super().__init__(
            title="VCCTL Help",
            transient_for=parent_window,
            modal=False,
            destroy_with_parent=False
        )
        
        self.help_manager = help_manager
        self.current_topic = None
        
        self.set_default_size(900, 700)
        self.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)
        
        self._setup_ui()
        self._connect_signals()
        self._load_initial_content()
    
    def _setup_ui(self):
        """Setup the dialog UI."""
        # Create main layout
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.get_content_area().add(main_box)
        
        # Create toolbar
        self._create_toolbar(main_box)
        
        # Create main content area
        content_paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        content_paned.set_position(300)
        main_box.pack_start(content_paned, True, True, 0)
        
        # Create navigation panel
        self._create_navigation_panel(content_paned)
        
        # Create content panel
        self._create_content_panel(content_paned)
        
        # Create status bar
        self._create_status_bar(main_box)
        
        # Add dialog buttons
        self.add_button("Close", Gtk.ResponseType.CLOSE)
        
        # Setup CSS styling
        self._apply_styling()
    
    def _create_toolbar(self, parent):
        """Create the help toolbar."""
        toolbar = Gtk.Toolbar()
        toolbar.set_style(Gtk.ToolbarStyle.BOTH_HORIZ)
        parent.pack_start(toolbar, False, False, 0)
        
        # Back button
        self.back_button = Gtk.ToolButton()
        self.back_button.set_icon_name("arrow--left")
        self.back_button.set_label("Back")
        self.back_button.set_tooltip_text("Go to previous topic")
        self.back_button.set_sensitive(False)
        toolbar.insert(self.back_button, -1)
        
        # Forward button
        self.forward_button = Gtk.ToolButton()
        self.forward_button.set_icon_name("arrow--right")
        self.forward_button.set_label("Forward")
        self.forward_button.set_tooltip_text("Go to next topic")
        self.forward_button.set_sensitive(False)
        toolbar.insert(self.forward_button, -1)
        
        # Separator
        separator = Gtk.SeparatorToolItem()
        toolbar.insert(separator, -1)
        
        # Home button
        self.home_button = Gtk.ToolButton()
        self.home_button.set_icon_name("home")
        self.home_button.set_label("Home")
        self.home_button.set_tooltip_text("Go to overview")
        toolbar.insert(self.home_button, -1)
        
        # Search entry
        search_item = Gtk.ToolItem()
        search_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        search_item.add(search_box)
        
        search_label = Gtk.Label("Search:")
        search_box.pack_start(search_label, False, False, 0)
        
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_size_request(200, -1)
        self.search_entry.set_placeholder_text("Search help topics...")
        search_box.pack_start(self.search_entry, False, False, 0)
        
        search_button = Gtk.Button()
        search_button.set_image(create_icon_image("search", 16))
        search_button.set_tooltip_text("Search help topics")
        search_box.pack_start(search_button, False, False, 0)
        
        toolbar.insert(search_item, -1)
        
        # Flexible space
        spacer = Gtk.SeparatorToolItem()
        spacer.set_expand(True)
        spacer.set_draw(False)
        toolbar.insert(spacer, -1)
        
        # Print button
        self.print_button = Gtk.ToolButton()
        self.print_button.set_icon_name("printer")
        self.print_button.set_label("Print")
        self.print_button.set_tooltip_text("Print current topic")
        toolbar.insert(self.print_button, -1)
        
        # Store references
        self.toolbar = toolbar
        self.search_button = search_button
    
    def _create_navigation_panel(self, parent):
        """Create the navigation tree panel."""
        nav_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        parent.pack1(nav_box, False, False)
        
        # Navigation header
        nav_header = Gtk.Label()
        nav_header.set_markup("<b>Contents</b>")
        nav_header.set_halign(Gtk.Align.START)
        nav_box.pack_start(nav_header, False, False, 0)
        
        # Create notebook for different views
        self.nav_notebook = Gtk.Notebook()
        nav_box.pack_start(self.nav_notebook, True, True, 0)
        
        # Contents tab
        self._create_contents_tab()
        
        # Search results tab
        self._create_search_tab()
        
        # Bookmarks tab
        self._create_bookmarks_tab()
        
        # History tab  
        self._create_history_tab()
    
    def _create_contents_tab(self):
        """Create the contents tree view."""
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        
        # Create tree model
        self.contents_store = Gtk.TreeStore(str, str, str)  # title, id, type
        
        # Create tree view
        self.contents_tree = Gtk.TreeView(model=self.contents_store)
        self.contents_tree.set_headers_visible(False)
        
        # Add column
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Contents", renderer, text=0)
        self.contents_tree.append_column(column)
        
        scrolled.add(self.contents_tree)
        
        # Add to notebook
        self.nav_notebook.append_page(scrolled, Gtk.Label("Contents"))
        
        # Populate contents
        self._populate_contents_tree()
    
    def _create_search_tab(self):
        """Create the search results view."""
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        
        # Create list model
        self.search_store = Gtk.ListStore(str, str, str)  # title, topic_id, snippet
        
        # Create tree view
        self.search_tree = Gtk.TreeView(model=self.search_store)
        
        # Title column
        title_renderer = Gtk.CellRendererText()
        title_column = Gtk.TreeViewColumn("Topic", title_renderer, text=0)
        title_column.set_expand(True)
        self.search_tree.append_column(title_column)
        
        scrolled.add(self.search_tree)
        
        # Add to notebook
        self.nav_notebook.append_page(scrolled, Gtk.Label("Search"))
    
    def _create_bookmarks_tab(self):
        """Create the bookmarks view."""
        bookmarks_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        
        # Bookmarks toolbar
        bookmarks_toolbar = Gtk.Toolbar()
        bookmarks_toolbar.set_style(Gtk.ToolbarStyle.ICONS)
        bookmarks_toolbar.set_icon_size(Gtk.IconSize.SMALL_TOOLBAR)
        
        add_bookmark_button = Gtk.ToolButton()
        add_bookmark_button.set_icon_name("bookmark--add")
        add_bookmark_button.set_tooltip_text("Add current topic to bookmarks")
        bookmarks_toolbar.insert(add_bookmark_button, -1)
        
        remove_bookmark_button = Gtk.ToolButton()
        remove_bookmark_button.set_icon_name("subtract")
        remove_bookmark_button.set_tooltip_text("Remove selected bookmark")
        bookmarks_toolbar.insert(remove_bookmark_button, -1)
        
        bookmarks_box.pack_start(bookmarks_toolbar, False, False, 0)
        
        # Bookmarks list
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        
        self.bookmarks_store = Gtk.ListStore(str, str)  # title, topic_id
        self.bookmarks_tree = Gtk.TreeView(model=self.bookmarks_store)
        self.bookmarks_tree.set_headers_visible(False)
        
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Bookmarks", renderer, text=0)
        self.bookmarks_tree.append_column(column)
        
        scrolled.add(self.bookmarks_tree)
        bookmarks_box.pack_start(scrolled, True, True, 0)
        
        # Add to notebook
        self.nav_notebook.append_page(bookmarks_box, Gtk.Label("Bookmarks"))
        
        # Store references
        self.add_bookmark_button = add_bookmark_button
        self.remove_bookmark_button = remove_bookmark_button
    
    def _create_history_tab(self):
        """Create the history view."""
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        
        self.history_store = Gtk.ListStore(str, str)  # title, topic_id
        self.history_tree = Gtk.TreeView(model=self.history_store)
        self.history_tree.set_headers_visible(False)
        
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Recent Topics", renderer, text=0)
        self.history_tree.append_column(column)
        
        scrolled.add(self.history_tree)
        
        # Add to notebook
        self.nav_notebook.append_page(scrolled, Gtk.Label("History"))
    
    def _create_content_panel(self, parent):
        """Create the content display panel."""
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        parent.pack2(content_box, True, False)
        
        # Content header
        self.content_header = Gtk.Label()
        self.content_header.set_halign(Gtk.Align.START)
        self.content_header.set_margin_bottom(6)
        content_box.pack_start(self.content_header, False, False, 0)
        
        # Content view
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        
        self.content_view = Gtk.TextView()
        self.content_view.set_editable(False)
        self.content_view.set_cursor_visible(False)
        self.content_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.content_view.set_left_margin(12)
        self.content_view.set_right_margin(12)
        
        self.content_buffer = self.content_view.get_buffer()
        
        scrolled.add(self.content_view)
        content_box.pack_start(scrolled, True, True, 0)
        
        # Setup text formatting
        self._setup_text_formatting()
    
    def _create_status_bar(self, parent):
        """Create the status bar."""
        self.status_bar = Gtk.Statusbar()
        self.status_context = self.status_bar.get_context_id("help")
        parent.pack_start(self.status_bar, False, False, 0)
    
    def _setup_text_formatting(self):
        """Setup text buffer formatting tags."""
        # Create text tags for formatting
        self.text_tags = {}
        
        # Heading 1
        tag = self.content_buffer.create_tag("h1")
        tag.set_property("size-points", 18)
        tag.set_property("weight", Pango.Weight.BOLD)
        tag.set_property("pixels-above-lines", 12)
        tag.set_property("pixels-below-lines", 6)
        self.text_tags["h1"] = tag
        
        # Heading 2
        tag = self.content_buffer.create_tag("h2")
        tag.set_property("size-points", 14)
        tag.set_property("weight", Pango.Weight.BOLD)
        tag.set_property("pixels-above-lines", 10)
        tag.set_property("pixels-below-lines", 4)
        self.text_tags["h2"] = tag
        
        # Heading 3
        tag = self.content_buffer.create_tag("h3")
        tag.set_property("size-points", 12)
        tag.set_property("weight", Pango.Weight.BOLD)
        tag.set_property("pixels-above-lines", 8)
        tag.set_property("pixels-below-lines", 4)
        self.text_tags["h3"] = tag
        
        # Bold text
        tag = self.content_buffer.create_tag("bold")
        tag.set_property("weight", Pango.Weight.BOLD)
        self.text_tags["bold"] = tag
        
        # Italic text
        tag = self.content_buffer.create_tag("italic")
        tag.set_property("style", Pango.Style.ITALIC)
        self.text_tags["italic"] = tag
        
        # Code text
        tag = self.content_buffer.create_tag("code")
        tag.set_property("family", "monospace")
        tag.set_property("background", "#f5f5f5")
        tag.set_property("pixels-above-lines", 2)
        tag.set_property("pixels-below-lines", 2)
        self.text_tags["code"] = tag
        
        # List item
        tag = self.content_buffer.create_tag("list")
        tag.set_property("left-margin", 24)
        tag.set_property("pixels-above-lines", 2)
        self.text_tags["list"] = tag
        
        # Table header
        tag = self.content_buffer.create_tag("table_header")
        tag.set_property("weight", Pango.Weight.BOLD)
        tag.set_property("background", "#e6e6e6")
        self.text_tags["table_header"] = tag
    
    def _apply_styling(self):
        """Apply CSS styling to the dialog."""
        css_provider = Gtk.CssProvider()
        css_data = """
        .help-dialog {
            background-color: #ffffff;
        }
        
        .help-content {
            padding: 12px;
            background-color: #ffffff;
        }
        
        .help-navigation {
            background-color: #f8f8f8;
            border-right: 1px solid #d0d0d0;
        }
        
        .help-toolbar {
            background: linear-gradient(to bottom, #f0f0f0, #e0e0e0);
            border-bottom: 1px solid #c0c0c0;
        }
        """
        
        css_provider.load_from_data(css_data.encode('utf-8'))
        
        context = self.get_style_context()
        context.add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    
    def _connect_signals(self):
        """Connect UI signals."""
        # Toolbar buttons
        self.back_button.connect("clicked", self._on_back_clicked)
        self.forward_button.connect("clicked", self._on_forward_clicked)
        self.home_button.connect("clicked", self._on_home_clicked)
        self.print_button.connect("clicked", self._on_print_clicked)
        
        # Search
        self.search_entry.connect("activate", self._on_search_activated)
        self.search_button.connect("clicked", self._on_search_clicked)
        
        # Navigation trees
        self.contents_tree.connect("row-activated", self._on_contents_activated)
        self.search_tree.connect("row-activated", self._on_search_activated)
        self.bookmarks_tree.connect("row-activated", self._on_bookmark_activated)
        self.history_tree.connect("row-activated", self._on_history_activated)
        
        # Bookmarks
        self.add_bookmark_button.connect("clicked", self._on_add_bookmark_clicked)
        self.remove_bookmark_button.connect("clicked", self._on_remove_bookmark_clicked)
        
        # Help manager signals
        self.help_manager.connect("help-requested", self._on_help_requested)
    
    def _populate_contents_tree(self):
        """Populate the contents tree with sections and topics."""
        self.contents_store.clear()
        
        for section in self.help_manager.sections.values():
            section_iter = self.contents_store.append(None, [section.title, section.section_id, "section"])
            
            for topic in section.topics.values():
                self.contents_store.append(section_iter, [topic.title, topic.topic_id, "topic"])
    
    def _load_initial_content(self):
        """Load initial help content."""
        self.show_topic("overview")
    
    def show_topic(self, topic_id: str):
        """Show a specific help topic."""
        topic = self.help_manager.get_topic(topic_id)
        if not topic:
            return
        
        self.current_topic = topic
        
        # Update header
        self.content_header.set_markup(f"<span size='large' weight='bold'>{topic.title}</span>")
        
        # Update content
        self._display_topic_content(topic)
        
        # Update navigation
        self._update_navigation_selection(topic_id)
        
        # Add to history
        self.help_manager.add_to_history(topic_id)
        self._update_history_view()
        
        # Update status
        section = self.help_manager.get_section(topic.parent_section)
        section_title = section.title if section else "Help"
        self.status_bar.push(self.status_context, f"{section_title} → {topic.title}")
        
        # Emit signal
        self.help_manager.emit('topic-viewed', topic_id)
    
    def _display_topic_content(self, topic: HelpTopic):
        """Display topic content with formatting."""
        self.content_buffer.set_text("")
        
        # Parse and format content
        lines = topic.content.strip().split('\n')
        
        start_iter = self.content_buffer.get_start_iter()
        
        for line in lines:
            line = line.rstrip()
            
            # Skip empty lines at start
            if not line and self.content_buffer.get_char_count() == 0:
                continue
            
            if line.startswith('# '):
                # Heading 1
                text = line[2:].strip()
                self._insert_formatted_text(text + '\n', 'h1')
            elif line.startswith('## '):
                # Heading 2
                text = line[3:].strip()
                self._insert_formatted_text(text + '\n', 'h2')
            elif line.startswith('### '):
                # Heading 3
                text = line[4:].strip()
                self._insert_formatted_text(text + '\n', 'h3')
            elif line.startswith('- '):
                # List item
                text = line[2:].strip()
                self._insert_formatted_text(f"• {text}\n", 'list')
            elif line.startswith('| '):
                # Table row
                self._format_table_row(line)
            elif line.strip() == '':
                # Empty line
                self._insert_formatted_text('\n', None)
            else:
                # Regular paragraph
                formatted_line = self._format_inline_text(line)
                self._insert_formatted_text(formatted_line + '\n', None)
    
    def _insert_formatted_text(self, text: str, tag_name: str = None):
        """Insert formatted text into the buffer."""
        end_iter = self.content_buffer.get_end_iter()
        
        if tag_name and tag_name in self.text_tags:
            self.content_buffer.insert_with_tags(end_iter, text, self.text_tags[tag_name])
        else:
            self.content_buffer.insert(end_iter, text)
    
    def _format_inline_text(self, text: str) -> str:
        """Format inline text elements."""
        # Simple formatting - could be expanded
        text = re.sub(r'\*\*(.*?)\*\*', r'\\1', text)  # Bold (simplified)
        text = re.sub(r'\*(.*?)\*', r'\\1', text)      # Italic (simplified)
        text = re.sub(r'`(.*?)`', r'\\1', text)        # Code (simplified)
        
        return text
    
    def _format_table_row(self, line: str):
        """Format a table row."""
        cells = [cell.strip() for cell in line.split('|')[1:-1]]
        
        # Simple table formatting
        row_text = ' | '.join(cells) + '\n'
        
        # Check if it's a header row (contains dashes)
        if any('---' in cell for cell in cells):
            self._insert_formatted_text(row_text, 'table_header')
        else:
            self._insert_formatted_text(row_text, None)
    
    def _update_navigation_selection(self, topic_id: str):
        """Update navigation tree selection."""
        model = self.contents_store
        
        def find_topic(model, path, iter, data):
            if model.get_value(iter, 1) == topic_id:
                self.contents_tree.get_selection().select_iter(iter)
                self.contents_tree.scroll_to_cell(path, None, False, 0, 0)
                return True
            return False
        
        model.foreach(find_topic, None)
    
    def _update_history_view(self):
        """Update the history view."""
        self.history_store.clear()
        
        recent_topics = self.help_manager.get_recent_topics(20)
        for topic in recent_topics:
            self.history_store.append([topic.title, topic.topic_id])
    
    def _update_bookmarks_view(self):
        """Update the bookmarks view."""
        self.bookmarks_store.clear()
        
        for topic_id in self.help_manager.bookmarks:
            topic = self.help_manager.get_topic(topic_id)
            if topic:
                self.bookmarks_store.append([topic.title, topic.topic_id])
    
    def search_topics(self, query: str):
        """Search for topics and display results."""
        if not query.strip():
            return
        
        results = self.help_manager.search_topics(query)
        
        self.search_store.clear()
        
        for topic in results:
            # Create snippet
            content_lower = topic.content.lower()
            query_lower = query.lower()
            
            start_pos = content_lower.find(query_lower)
            if start_pos >= 0:
                start = max(0, start_pos - 50)
                end = min(len(topic.content), start_pos + len(query) + 50)
                snippet = topic.content[start:end].replace('\n', ' ')
                if start > 0:
                    snippet = "..." + snippet
                if end < len(topic.content):
                    snippet = snippet + "..."
            else:
                snippet = topic.content[:100].replace('\n', ' ') + "..."
            
            self.search_store.append([topic.title, topic.topic_id, snippet])
        
        # Switch to search tab
        self.nav_notebook.set_current_page(1)
        
        # Update status
        count = len(results)
        self.status_bar.push(self.status_context, f"Found {count} topic{'s' if count != 1 else ''} for '{query}'")
    
    # Signal handlers
    
    def _on_back_clicked(self, button):
        """Handle back button click."""
        # Simple implementation - could be enhanced with proper history
        pass
    
    def _on_forward_clicked(self, button):
        """Handle forward button click."""
        # Simple implementation - could be enhanced with proper history
        pass
    
    def _on_home_clicked(self, button):
        """Handle home button click."""
        self.show_topic("overview")
    
    def _on_print_clicked(self, button):
        """Handle print button click."""
        if self.current_topic:
            self._print_topic(self.current_topic)
    
    def _on_search_activated(self, entry):
        """Handle search entry activation."""
        query = entry.get_text()
        self.search_topics(query)
    
    def _on_search_clicked(self, button):
        """Handle search button click."""
        query = self.search_entry.get_text()
        self.search_topics(query)
    
    def _on_contents_activated(self, tree_view, path, column):
        """Handle contents tree activation."""
        model = tree_view.get_model()
        iter = model.get_iter(path)
        item_type = model.get_value(iter, 2)
        item_id = model.get_value(iter, 1)
        
        if item_type == "topic":
            self.show_topic(item_id)
    
    def _on_search_activated(self, tree_view, path, column):
        """Handle search results activation."""
        model = tree_view.get_model()
        iter = model.get_iter(path)
        topic_id = model.get_value(iter, 1)
        self.show_topic(topic_id)
    
    def _on_bookmark_activated(self, tree_view, path, column):
        """Handle bookmark activation."""
        model = tree_view.get_model()
        iter = model.get_iter(path)
        topic_id = model.get_value(iter, 1)
        self.show_topic(topic_id)
    
    def _on_history_activated(self, tree_view, path, column):
        """Handle history activation."""
        model = tree_view.get_model()
        iter = model.get_iter(path)
        topic_id = model.get_value(iter, 1)
        self.show_topic(topic_id)
    
    def _on_add_bookmark_clicked(self, button):
        """Handle add bookmark button click."""
        if self.current_topic:
            self.help_manager.add_bookmark(self.current_topic.topic_id)
            self._update_bookmarks_view()
            self.status_bar.push(self.status_context, f"Added '{self.current_topic.title}' to bookmarks")
    
    def _on_remove_bookmark_clicked(self, button):
        """Handle remove bookmark button click."""
        selection = self.bookmarks_tree.get_selection()
        model, iter = selection.get_selected()
        
        if iter:
            topic_id = model.get_value(iter, 1)
            topic_title = model.get_value(iter, 0)
            
            self.help_manager.remove_bookmark(topic_id)
            self._update_bookmarks_view()
            self.status_bar.push(self.status_context, f"Removed '{topic_title}' from bookmarks")
    
    def _on_help_requested(self, help_manager, topic_id):
        """Handle help requested signal."""
        self.show_topic(topic_id)
        self.present()
    
    def _print_topic(self, topic: HelpTopic):
        """Print the current topic."""
        # Simple print implementation
        print_operation = Gtk.PrintOperation()
        
        def begin_print(operation, context):
            operation.set_n_pages(1)
        
        def draw_page(operation, context, page_nr):
            if page_nr == 0:
                cr = context.get_cairo_context()
                
                # Set up font
                cr.select_font_face("Arial", 0, 0)
                cr.set_font_size(12)
                
                # Print title
                cr.move_to(50, 50)
                cr.show_text(f"VCCTL Help: {topic.title}")
                
                # Print content (simplified)
                y_pos = 80
                for line in topic.content.split('\n')[:50]:  # Limit lines
                    if line.strip():
                        cr.move_to(50, y_pos)
                        cr.show_text(line[:80])  # Limit line length
                        y_pos += 15
        
        print_operation.connect("begin-print", begin_print)
        print_operation.connect("draw-page", draw_page)
        
        result = print_operation.run(Gtk.PrintOperationAction.PRINT_DIALOG, self)
        
        if result == Gtk.PrintOperationResult.APPLY:
            self.status_bar.push(self.status_context, f"Printed '{topic.title}'")
    
    def show_contextual_help(self, context: str):
        """Show contextual help for a specific UI context."""
        topic = self.help_manager.get_contextual_help(context)
        if topic:
            self.show_topic(topic.topic_id)
            self.present()
        else:
            self.show_topic("overview")
            self.present()
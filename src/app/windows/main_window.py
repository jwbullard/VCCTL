#!/usr/bin/env python3
"""
VCCTL Main Window

The primary application window for the VCCTL GTK3 desktop application.
"""

import gi
import logging
from typing import TYPE_CHECKING

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk

if TYPE_CHECKING:
    from app.application import VCCTLApplication


class VCCTLMainWindow(Gtk.ApplicationWindow):
    """Main application window for VCCTL."""
    
    def __init__(self, app: 'VCCTLApplication'):
        """Initialize the main window."""
        super().__init__(application=app)
        
        self.app = app
        self.logger = logging.getLogger('VCCTL.MainWindow')
        
        # Window properties
        self.set_title("VCCTL - Virtual Cement and Concrete Testing Laboratory")
        self.set_default_size(1200, 800)
        self.set_position(Gtk.WindowPosition.CENTER)
        
        # Setup the UI
        self._setup_ui()
        
        # Connect signals
        self.connect('delete-event', self._on_delete_event)
        self.connect('destroy', self._on_destroy)
        
        # Load window state
        self._load_window_state()
        
        self.logger.info("Main window initialized")
    
    def _setup_ui(self) -> None:
        """Setup the main window UI components."""
        # Create main vertical box
        main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(main_vbox)
        
        # Create header bar
        self._create_header_bar()
        
        # Create main content area
        self._create_content_area(main_vbox)
        
        # Create status bar
        self._create_status_bar(main_vbox)
        
        # Show all widgets
        self.show_all()
    
    def _create_header_bar(self) -> None:
        """Create and setup the header bar."""
        self.header_bar = Gtk.HeaderBar()
        self.header_bar.set_show_close_button(True)
        self.header_bar.set_title("VCCTL")
        self.header_bar.set_subtitle("Virtual Cement and Concrete Testing Laboratory")
        
        # Add menu button to header bar
        menu_button = Gtk.MenuButton()
        menu_button.set_image(Gtk.Image.new_from_icon_name("open-menu-symbolic", Gtk.IconSize.BUTTON))
        menu_button.set_tooltip_text("Application Menu")
        self.header_bar.pack_end(menu_button)
        
        # Create application menu
        self._create_app_menu(menu_button)
        
        # Set as titlebar
        self.set_titlebar(self.header_bar)
    
    def _create_app_menu(self, menu_button: Gtk.MenuButton) -> None:
        """Create the application menu."""
        menu = Gtk.Menu()
        
        # About menu item
        about_item = Gtk.MenuItem(label="About VCCTL")
        about_item.connect('activate', self._on_about_clicked)
        menu.append(about_item)
        
        # Separator
        menu.append(Gtk.SeparatorMenuItem())
        
        # Preferences menu item
        prefs_item = Gtk.MenuItem(label="Preferences")
        prefs_item.connect('activate', self._on_preferences_clicked)
        menu.append(prefs_item)
        
        # Separator
        menu.append(Gtk.SeparatorMenuItem())
        
        # Quit menu item
        quit_item = Gtk.MenuItem(label="Quit")
        quit_item.connect('activate', self._on_quit_clicked)
        menu.append(quit_item)
        
        menu.show_all()
        menu_button.set_popup(menu)
    
    def _create_content_area(self, main_vbox: Gtk.Box) -> None:
        """Create the main content area."""
        # Create a notebook for tabbed interface (placeholder for now)
        self.notebook = Gtk.Notebook()
        self.notebook.set_show_tabs(True)
        self.notebook.set_show_border(True)
        
        # Add a welcome tab as placeholder
        welcome_label = Gtk.Label()
        welcome_label.set_markup("""
<span size="large"><b>Welcome to VCCTL</b></span>

<span size="medium">Virtual Cement and Concrete Testing Laboratory</span>

This is the GTK3 desktop version of VCCTL developed by 
NIST's Building and Fire Research Laboratory.

<b>Features:</b>
• Materials Management
• Mix Design
• Microstructure Generation
• Simulation Control
• Data Visualization

<i>Application is being developed...</i>
        """)
        welcome_label.set_justify(Gtk.Justification.CENTER)
        welcome_label.set_line_wrap(True)
        welcome_label.set_margin_top(50)
        welcome_label.set_margin_bottom(50)
        welcome_label.set_margin_left(50)
        welcome_label.set_margin_right(50)
        
        # Add welcome tab
        self.notebook.append_page(welcome_label, Gtk.Label(label="Home"))
        
        # Pack notebook into main container
        main_vbox.pack_start(self.notebook, True, True, 0)
    
    def _create_status_bar(self, main_vbox: Gtk.Box) -> None:
        """Create the status bar."""
        self.status_bar = Gtk.Statusbar()
        self.status_context_id = self.status_bar.get_context_id("main")
        
        # Add some initial status
        self.status_bar.push(self.status_context_id, "Ready")
        
        # Add NIST logo placeholder or text to the right side
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        hbox.pack_start(self.status_bar, True, True, 0)
        
        # NIST attribution
        nist_label = Gtk.Label(label="NIST BFRL")
        nist_label.set_margin_right(10)
        hbox.pack_end(nist_label, False, False, 0)
        
        main_vbox.pack_end(hbox, False, False, 0)
    
    def _load_window_state(self) -> None:
        """Load saved window state (size, position, etc.)."""
        # TODO: Implement window state persistence
        # For now, just set reasonable defaults
        pass
    
    def _save_window_state(self) -> None:
        """Save current window state."""
        # TODO: Implement window state persistence
        pass
    
    def _on_delete_event(self, widget: Gtk.Widget, event: Gdk.Event) -> bool:
        """Handle window delete event."""
        self.logger.info("Main window delete event")
        
        # Save window state before closing
        self._save_window_state()
        
        # Let the application handle the quit
        self.app.quit_application()
        
        # Return True to prevent default handler
        return True
    
    def _on_destroy(self, widget: Gtk.Widget) -> None:
        """Handle window destroy event."""
        self.logger.info("Main window destroyed")
    
    def _on_about_clicked(self, widget: Gtk.Widget) -> None:
        """Show the about dialog."""
        about_dialog = Gtk.AboutDialog()
        about_dialog.set_transient_for(self)
        about_dialog.set_modal(True)
        
        about_dialog.set_program_name("VCCTL")
        about_dialog.set_version(self.app.app_version)
        about_dialog.set_comments("Virtual Cement and Concrete Testing Laboratory")
        about_dialog.set_website("https://vcctl.nist.gov/")
        about_dialog.set_website_label("VCCTL Website")
        
        about_dialog.set_copyright("NIST Building and Fire Research Laboratory")
        about_dialog.set_license_type(Gtk.License.CUSTOM)
        about_dialog.set_license("""
This software was developed by NIST employees and is not subject to copyright 
protection in the United States. This software may be subject to foreign copyright.
        """)
        
        about_dialog.set_authors([
            "NIST Building and Fire Research Laboratory",
            "VCCTL Development Team"
        ])
        
        about_dialog.run()
        about_dialog.destroy()
    
    def _on_preferences_clicked(self, widget: Gtk.Widget) -> None:
        """Show the preferences dialog."""
        # TODO: Implement preferences dialog
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Preferences"
        )
        dialog.format_secondary_text("Preferences dialog will be implemented in a future version.")
        dialog.run()
        dialog.destroy()
    
    def _on_quit_clicked(self, widget: Gtk.Widget) -> None:
        """Handle quit menu item."""
        self.app.quit_application()
    
    def update_status(self, message: str) -> None:
        """Update the status bar message."""
        self.status_bar.pop(self.status_context_id)
        self.status_bar.push(self.status_context_id, message)
    
    def cleanup(self) -> None:
        """Cleanup resources before window is destroyed."""
        self.logger.info("Cleaning up main window resources")
        
        # Save window state
        self._save_window_state()
        
        # TODO: Cleanup any other resources
#!/usr/bin/env python3
"""
VCCTL GTK3 Application Main Class

Virtual Cement and Concrete Testing Laboratory
Main application class that manages the GTK application lifecycle.
"""

import gi
import sys
import logging
import argparse
from typing import Optional

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio, GLib

from app.windows.main_window import VCCTLMainWindow


class VCCTLApplication(Gtk.Application):
    """Main VCCTL GTK3 Application class."""
    
    def __init__(self):
        """Initialize the VCCTL application."""
        super().__init__(
            application_id='gov.nist.vcctl.gtk',
            flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE
        )
        
        # Application metadata
        self.app_name = "VCCTL"
        self.app_title = "Virtual Cement and Concrete Testing Laboratory"
        self.app_version = "1.0.0"
        self.app_description = "Desktop application for cement and concrete materials modeling"
        
        # Main window reference
        self.main_window: Optional[VCCTLMainWindow] = None
        
        # Setup logging
        self._setup_logging()
        
        # Connect application signals
        self.connect('activate', self._on_activate)
        self.connect('startup', self._on_startup)
        self.connect('shutdown', self._on_shutdown)
        self.connect('command-line', self._on_command_line)
        
        self.logger.info(f"VCCTL Application {self.app_version} initialized")
    
    def _setup_logging(self) -> None:
        """Setup application logging."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                # TODO: Add file handler when we have a logs directory
            ]
        )
        self.logger = logging.getLogger('VCCTL')
    
    def _on_startup(self, app: Gtk.Application) -> None:
        """Called once when the application starts."""
        self.logger.info("Application startup")
        
        # Set application properties
        GLib.set_application_name(self.app_name)
        GLib.set_prgname('vcctl-gtk')
        
        # Setup application menu (if needed)
        self._setup_app_menu()
        
        # Load application resources
        self._load_resources()
    
    def _on_activate(self, app: Gtk.Application) -> None:
        """Called when the application is activated (launched)."""
        self.logger.info("Application activated")
        
        if self.main_window is None:
            # Create the main window
            self.main_window = VCCTLMainWindow(self)
            self.add_window(self.main_window)
        
        # Present the main window
        self.main_window.present()
    
    def _on_shutdown(self, app: Gtk.Application) -> None:
        """Called when the application is shutting down."""
        self.logger.info("Application shutdown")
        
        # Cleanup resources
        if self.main_window:
            self.main_window.cleanup()
    
    def _on_command_line(self, app: Gtk.Application, command_line: Gio.ApplicationCommandLine) -> int:
        """Handle command line arguments."""
        args = command_line.get_arguments()
        
        # Parse command line arguments
        parser = self._create_argument_parser()
        try:
            parsed_args = parser.parse_args(args[1:])  # Skip program name
            
            # Handle version request
            if hasattr(parsed_args, 'version') and parsed_args.version:
                print(f"{self.app_name} {self.app_version}")
                return 0
            
            # Handle verbose logging
            if hasattr(parsed_args, 'verbose') and parsed_args.verbose:
                logging.getLogger().setLevel(logging.DEBUG)
                self.logger.debug("Verbose logging enabled")
            
            # Activate the application
            self.activate()
            
        except SystemExit as e:
            return e.code if e.code is not None else 0
        except Exception as e:
            self.logger.error(f"Error parsing command line: {e}")
            return 1
        
        return 0
    
    def _create_argument_parser(self) -> argparse.ArgumentParser:
        """Create command line argument parser."""
        parser = argparse.ArgumentParser(
            prog='vcctl-gtk',
            description=self.app_description,
            epilog=f"VCCTL {self.app_version} - NIST Building and Fire Research Laboratory"
        )
        
        parser.add_argument(
            '--version', '-v',
            action='store_true',
            help='Show application version'
        )
        
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose logging'
        )
        
        parser.add_argument(
            '--debug',
            action='store_true',
            help='Enable debug mode'
        )
        
        return parser
    
    def _setup_app_menu(self) -> None:
        """Setup the application menu."""
        # This is where we would add application-wide menu items
        # For now, we'll keep it simple
        pass
    
    def _load_resources(self) -> None:
        """Load application resources like icons, CSS, etc."""
        try:
            # TODO: Load application icon when we have resources
            # TODO: Load CSS themes when we have styling
            self.logger.debug("Resources loaded successfully")
        except Exception as e:
            self.logger.warning(f"Could not load some resources: {e}")
    
    def get_main_window(self) -> Optional[VCCTLMainWindow]:
        """Get the main application window."""
        return self.main_window
    
    def quit_application(self) -> None:
        """Quit the application gracefully."""
        self.logger.info("Quitting application")
        
        # Close all windows
        for window in self.get_windows():
            window.close()
        
        # Quit the application
        self.quit()
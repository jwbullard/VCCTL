#!/usr/bin/env python3
"""
Documentation Viewer

Opens the built MkDocs documentation in the user's default web browser.
Falls back to simple dialog if documentation files are not found.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
from pathlib import Path
import webbrowser
import threading
import http.server
import socketserver
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class DocumentationViewer:
    """
    Manages viewing of MkDocs documentation.

    Provides multiple methods for viewing documentation:
    1. Opens local HTTP server and launches browser
    2. Opens file:// URLs directly in browser
    3. Falls back to error dialog if docs not found
    """

    def __init__(self, docs_path: Optional[Path] = None):
        """
        Initialize documentation viewer.

        Args:
            docs_path: Path to built documentation (site/ directory)
                      If None, will search standard locations
        """
        self.docs_path = docs_path
        self.server = None
        self.server_thread = None
        self.port = 8765  # Default port for local docs server

        if self.docs_path is None:
            self.docs_path = self._find_documentation()

    def _find_documentation(self) -> Optional[Path]:
        """
        Find built documentation in standard locations.

        Returns:
            Path to site/ directory or None if not found
        """
        # Try relative to current file
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent.parent.parent

        # Standard location: vcctl-docs/site/
        docs_site = project_root / "vcctl-docs" / "site"
        if docs_site.exists() and docs_site.is_dir():
            logger.info(f"Found documentation at: {docs_site}")
            return docs_site

        # Try installed location (for packaged app)
        import sys
        if getattr(sys, 'frozen', False):
            # Running in PyInstaller bundle
            bundle_dir = Path(sys._MEIPASS)
            packaged_docs = bundle_dir / "docs" / "site"
            if packaged_docs.exists():
                logger.info(f"Found packaged documentation at: {packaged_docs}")
                return packaged_docs

        logger.warning("Documentation not found in standard locations")
        return None

    def open_documentation(self, page: str = "index.html", parent_window: Optional[Gtk.Window] = None):
        """
        Open documentation in user's default browser.

        Args:
            page: Specific page to open (e.g., "user-guide/elastic-calculations/index.html")
            parent_window: Parent window for error dialogs
        """
        if self.docs_path is None or not self.docs_path.exists():
            self._show_documentation_not_found_dialog(parent_window)
            return

        # Construct full path to requested page
        page_path = self.docs_path / page
        if not page_path.exists():
            # Fall back to index if specific page not found
            logger.warning(f"Requested page not found: {page}, falling back to index")
            page_path = self.docs_path / "index.html"

        if not page_path.exists():
            self._show_documentation_not_found_dialog(parent_window)
            return

        # Open in browser using file:// URL
        url = page_path.as_uri()
        logger.info(f"Opening documentation: {url}")

        try:
            webbrowser.open(url)
        except Exception as e:
            logger.error(f"Failed to open documentation in browser: {e}")
            self._show_browser_error_dialog(parent_window, str(e))

    def open_user_guide(self, section: str = None, parent_window: Optional[Gtk.Window] = None):
        """
        Open specific user guide section.

        Args:
            section: Section name (e.g., "elastic-calculations", "materials-management")
            parent_window: Parent window for error dialogs
        """
        if section:
            page = f"user-guide/{section}/index.html"
        else:
            page = "user-guide/materials-management/index.html"  # Default to first section

        self.open_documentation(page, parent_window)

    def open_getting_started(self, parent_window: Optional[Gtk.Window] = None):
        """Open Getting Started guide."""
        self.open_documentation("getting-started/index.html", parent_window)

    def open_reference(self, topic: str = None, parent_window: Optional[Gtk.Window] = None):
        """
        Open reference documentation.

        Args:
            topic: Reference topic (e.g., "api", "file-formats")
            parent_window: Parent window for error dialogs
        """
        if topic:
            page = f"reference/{topic}/index.html"
        else:
            page = "reference/overview/index.html"

        self.open_documentation(page, parent_window)

    def start_local_server(self) -> bool:
        """
        Start local HTTP server for documentation.

        Alternative method for serving documentation locally.
        Useful if file:// URLs have issues with some browsers.

        Returns:
            True if server started successfully
        """
        if self.docs_path is None or not self.docs_path.exists():
            logger.error("Cannot start server: documentation not found")
            return False

        if self.server is not None:
            logger.info("Documentation server already running")
            return True

        try:
            # Create HTTP server
            handler = http.server.SimpleHTTPRequestHandler

            # Change to docs directory
            import os
            original_dir = os.getcwd()
            os.chdir(self.docs_path)

            # Find available port
            port = self.port
            while port < self.port + 10:
                try:
                    self.server = socketserver.TCPServer(("127.0.0.1", port), handler)
                    self.port = port
                    break
                except OSError:
                    port += 1

            if self.server is None:
                logger.error("Could not find available port for documentation server")
                os.chdir(original_dir)
                return False

            # Start server in background thread
            self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.server_thread.start()

            logger.info(f"Documentation server started on port {self.port}")
            return True

        except Exception as e:
            logger.error(f"Failed to start documentation server: {e}")
            return False

    def stop_local_server(self):
        """Stop local HTTP server if running."""
        if self.server is not None:
            logger.info("Stopping documentation server")
            self.server.shutdown()
            self.server.server_close()
            self.server = None
            self.server_thread = None

    def open_documentation_via_server(self, page: str = "index.html", parent_window: Optional[Gtk.Window] = None):
        """
        Open documentation via local HTTP server.

        Args:
            page: Specific page to open
            parent_window: Parent window for error dialogs
        """
        if not self.start_local_server():
            self._show_server_error_dialog(parent_window)
            return

        url = f"http://127.0.0.1:{self.port}/{page}"
        logger.info(f"Opening documentation via server: {url}")

        try:
            webbrowser.open(url)
        except Exception as e:
            logger.error(f"Failed to open documentation in browser: {e}")
            self._show_browser_error_dialog(parent_window, str(e))

    def _show_documentation_not_found_dialog(self, parent_window: Optional[Gtk.Window]):
        """Show error dialog when documentation is not found."""
        dialog = Gtk.MessageDialog(
            transient_for=parent_window,
            modal=True,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text="Documentation Not Found"
        )
        dialog.format_secondary_text(
            "The VCCTL documentation could not be found.\n\n"
            "Please ensure the documentation has been built:\n"
            "  cd vcctl-docs\n"
            "  mkdocs build\n\n"
            "Or visit the online documentation at:\n"
            "https://vcctl.readthedocs.io/"
        )
        dialog.run()
        dialog.destroy()

    def _show_browser_error_dialog(self, parent_window: Optional[Gtk.Window], error_message: str):
        """Show error dialog when browser fails to open."""
        dialog = Gtk.MessageDialog(
            transient_for=parent_window,
            modal=True,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text="Failed to Open Browser"
        )
        dialog.format_secondary_text(
            f"Could not open documentation in your default browser.\n\n"
            f"Error: {error_message}\n\n"
            f"Documentation location:\n{self.docs_path}"
        )
        dialog.run()
        dialog.destroy()

    def _show_server_error_dialog(self, parent_window: Optional[Gtk.Window]):
        """Show error dialog when local server fails to start."""
        dialog = Gtk.MessageDialog(
            transient_for=parent_window,
            modal=True,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text="Failed to Start Documentation Server"
        )
        dialog.format_secondary_text(
            "Could not start local HTTP server for documentation.\n\n"
            "The documentation viewer will attempt to open files directly."
        )
        dialog.run()
        dialog.destroy()


# Singleton instance
_documentation_viewer = None


def get_documentation_viewer() -> DocumentationViewer:
    """
    Get singleton documentation viewer instance.

    Returns:
        DocumentationViewer instance
    """
    global _documentation_viewer
    if _documentation_viewer is None:
        _documentation_viewer = DocumentationViewer()
    return _documentation_viewer

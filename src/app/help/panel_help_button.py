#!/usr/bin/env python3
"""
Panel Help Button

Reusable help button widget that opens context-specific documentation for each panel.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from typing import Optional
import logging

from app.utils.icon_utils import create_icon_image
from app.help.documentation_viewer import get_documentation_viewer

logger = logging.getLogger(__name__)


# Mapping of panel class names to their documentation URLs
PANEL_DOCUMENTATION_MAP = {
    'MaterialsPanel': 'user-guide/materials-management/index.html',
    'MixDesignPanel': 'user-guide/mix-design/index.html',
    'MicrostructurePanel': 'user-guide/mix-design/index.html',  # Microstructure is part of mix design
    'HydrationPanel': 'user-guide/hydration-simulation/index.html',
    'ElasticModuliPanel': 'user-guide/elastic-calculations/index.html',
    'ResultsPanel': 'user-guide/results-visualization/index.html',
    'OperationsMonitoringPanel': 'user-guide/operations-monitoring/index.html',
    'FileManagementPanel': 'getting-started/index.html',  # File management covered in getting started
    'AggregatePanel': 'user-guide/materials-management/index.html',  # Aggregates part of materials
}


def create_panel_help_button(panel_name: str, parent_window: Optional[Gtk.Window] = None) -> Gtk.Button:
    """
    Create a context-specific help button for a panel.

    Args:
        panel_name: Name of the panel class (e.g., 'MaterialsPanel')
        parent_window: Parent window for error dialogs

    Returns:
        Configured help button
    """
    button = Gtk.Button()
    button.set_relief(Gtk.ReliefStyle.NONE)
    button.set_can_focus(False)

    # Create help icon
    help_icon = create_icon_image("help-about", 16)
    button.set_image(help_icon)

    # Set tooltip
    panel_display_name = _get_panel_display_name(panel_name)
    button.set_tooltip_text(f"Open {panel_display_name} documentation")

    # Connect click handler
    button.connect('clicked', lambda w: _on_help_button_clicked(panel_name, parent_window))

    # Add CSS class for styling
    button.get_style_context().add_class('panel-help-button')

    return button


def _get_panel_display_name(panel_name: str) -> str:
    """
    Get user-friendly display name for a panel.

    Args:
        panel_name: Panel class name

    Returns:
        Display name for UI
    """
    display_names = {
        'MaterialsPanel': 'Materials Management',
        'MixDesignPanel': 'Mix Design',
        'MicrostructurePanel': 'Microstructure Generation',
        'HydrationPanel': 'Hydration Simulation',
        'ElasticModuliPanel': 'Elastic Calculations',
        'ResultsPanel': 'Results Visualization',
        'OperationsMonitoringPanel': 'Operations Monitoring',
        'FileManagementPanel': 'File Management',
        'AggregatePanel': 'Aggregate Management',
    }

    return display_names.get(panel_name, panel_name.replace('Panel', ''))


def _on_help_button_clicked(panel_name: str, parent_window: Optional[Gtk.Window]):
    """
    Handle help button click - open context-specific documentation.

    Args:
        panel_name: Panel class name
        parent_window: Parent window for error dialogs
    """
    # Get documentation URL for this panel
    doc_url = PANEL_DOCUMENTATION_MAP.get(panel_name)

    if not doc_url:
        logger.warning(f"No documentation URL mapped for panel: {panel_name}")
        # Fall back to main documentation index
        doc_url = "index.html"

    # Open documentation
    doc_viewer = get_documentation_viewer()
    doc_viewer.open_documentation(doc_url, parent_window)

    logger.info(f"Opened documentation for {panel_name}: {doc_url}")


def get_panel_documentation_url(panel_name: str) -> Optional[str]:
    """
    Get documentation URL for a specific panel.

    Args:
        panel_name: Panel class name

    Returns:
        Documentation URL or None if not found
    """
    return PANEL_DOCUMENTATION_MAP.get(panel_name)


def add_help_button_to_header(title_box: Gtk.Box, panel_name: str, parent_window: Optional[Gtk.Window] = None):
    """
    Convenience function to add help button to a panel's title box.

    Args:
        title_box: The horizontal box containing the panel title
        panel_name: Panel class name
        parent_window: Parent window for error dialogs
    """
    help_button = create_panel_help_button(panel_name, parent_window)
    title_box.pack_end(help_button, False, False, 0)
    logger.debug(f"Added help button to {panel_name} header")

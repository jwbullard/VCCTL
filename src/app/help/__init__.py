"""
VCCTL Help System

Provides comprehensive help and documentation system for VCCTL application.
"""

from .help_manager import HelpManager, HelpSection, HelpTopic
from .help_dialog import HelpDialog
from .tooltip_manager import TooltipManager

__all__ = [
    'HelpManager',
    'HelpSection', 
    'HelpTopic',
    'HelpDialog',
    'TooltipManager'
]

def create_help_system(main_window):
    """Create and configure the complete help system."""
    help_manager = HelpManager()
    tooltip_manager = TooltipManager()
    
    return help_manager, tooltip_manager
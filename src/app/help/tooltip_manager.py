#!/usr/bin/env python3
"""
Tooltip Manager

Manages contextual tooltips throughout the VCCTL application.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, Gdk
from typing import Dict, List, Optional, Any, Callable
from enum import Enum


class TooltipType(Enum):
    """Types of tooltips."""
    SIMPLE = "simple"
    RICH = "rich"
    CONTEXTUAL = "contextual"
    HELP = "help"


class TooltipInfo:
    """Information for a tooltip."""
    
    def __init__(self, text: str, tooltip_type: TooltipType = TooltipType.SIMPLE,
                 title: str = None, details: str = None, help_topic: str = None):
        self.text = text
        self.tooltip_type = tooltip_type
        self.title = title
        self.details = details
        self.help_topic = help_topic
        self.custom_widget = None


class TooltipManager(GObject.Object):
    """
    Manages tooltips for VCCTL application.
    
    Features:
    - Simple text tooltips
    - Rich tooltips with formatting
    - Contextual help tooltips
    - Dynamic tooltip content
    - Tooltip customization
    """
    
    def __init__(self):
        super().__init__()
        self.tooltips = {}
        self.custom_tooltips = {}
        self.tooltip_providers = {}
        
        self._initialize_default_tooltips()
    
    def _initialize_default_tooltips(self):
        """Initialize default tooltips for common UI elements."""
        
        # Materials panel tooltips
        self.register_tooltip(
            "materials_new_cement_button",
            TooltipInfo(
                "Create New Cement Material",
                TooltipType.CONTEXTUAL,
                title="New Cement",
                details="Click to create a new cement material with chemical composition and physical properties.",
                help_topic="cement_materials"
            )
        )
        
        self.register_tooltip(
            "materials_new_aggregate_button", 
            TooltipInfo(
                "Create New Aggregate Material",
                TooltipType.CONTEXTUAL,
                title="New Aggregate",
                details="Click to create a new fine or coarse aggregate with gradation and physical properties.",
                help_topic="aggregate_materials"
            )
        )
        
        self.register_tooltip(
            "materials_import_button",
            TooltipInfo(
                "Import Materials from File",
                TooltipType.CONTEXTUAL,
                title="Import Materials",
                details="Import material definitions from JSON, CSV, or XML files.",
                help_topic="material_import"
            )
        )
        
        self.register_tooltip(
            "materials_export_button",
            TooltipInfo(
                "Export Selected Materials",
                TooltipType.CONTEXTUAL,
                title="Export Materials", 
                details="Export selected materials to files in various formats.",
                help_topic="material_export"
            )
        )
        
        # Mix design panel tooltips
        self.register_tooltip(
            "mix_design_new_button",
            TooltipInfo(
                "Create New Mix Design",
                TooltipType.CONTEXTUAL,
                title="New Mix Design",
                details="Create a new concrete mix design with specified materials and proportions.",
                help_topic="concrete_mix_design"
            )
        )
        
        self.register_tooltip(
            "mix_design_water_cement_ratio",
            TooltipInfo(
                "Water-Cement Ratio (W/C)",
                TooltipType.RICH,
                title="Water-Cement Ratio",
                details="Controls strength and durability. Lower W/C ratio typically gives higher strength but may reduce workability."
            )
        )
        
        self.register_tooltip(
            "mix_design_cement_content",
            TooltipInfo(
                "Cement Content (kg/m³)",
                TooltipType.RICH,
                title="Cement Content",
                details="Amount of cement per cubic meter of concrete. Typical range: 250-500 kg/m³ depending on application."
            )
        )
        
        self.register_tooltip(
            "mix_design_slump_target",
            TooltipInfo(
                "Target Slump (mm)",
                TooltipType.RICH,
                title="Slump Target",
                details="Measure of workability. Higher slump = more fluid concrete. Typical range: 50-200 mm."
            )
        )
        
        # Simulation panel tooltips
        self.register_tooltip(
            "simulation_microstructure_size",
            TooltipInfo(
                "Microstructure System Size",
                TooltipType.RICH,
                title="System Size",
                details="Size of the 3D microstructure in micrometers. Larger systems are more representative but require more memory and time."
            )
        )
        
        self.register_tooltip(
            "simulation_temperature",
            TooltipInfo(
                "Curing Temperature (°C)",
                TooltipType.RICH,
                title="Temperature",
                details="Temperature affects hydration rate. Higher temperature accelerates hydration but may affect final properties."
            )
        )
        
        self.register_tooltip(
            "simulation_time",
            TooltipInfo(
                "Simulation Time (days)",
                TooltipType.RICH,
                title="Simulation Duration",
                details="Duration to simulate hydration. 28 days is standard for strength development studies."
            )
        )
        
        # Property fields tooltips
        self.register_tooltip(
            "cement_sio2_field",
            TooltipInfo(
                "Silicon Dioxide (SiO₂) Content",
                TooltipType.RICH,
                title="SiO₂ Content (%)",
                details="Primary constituent of cement. Typical range: 18-25%. Affects strength development and heat of hydration."
            )
        )
        
        self.register_tooltip(
            "cement_cao_field",
            TooltipInfo(
                "Calcium Oxide (CaO) Content", 
                TooltipType.RICH,
                title="CaO Content (%)",
                details="Major cement constituent. Typical range: 60-67%. Higher CaO generally increases early strength."
            )
        )
        
        self.register_tooltip(
            "cement_al2o3_field",
            TooltipInfo(
                "Aluminum Oxide (Al₂O₃) Content",
                TooltipType.RICH,
                title="Al₂O₃ Content (%)",
                details="Affects early hydration and heat generation. Typical range: 3-8%."
            )
        )
        
        self.register_tooltip(
            "cement_fe2o3_field",
            TooltipInfo(
                "Iron Oxide (Fe₂O₃) Content",
                TooltipType.RICH,
                title="Fe₂O₃ Content (%)",
                details="Contributes to cement color and affects hydration. Typical range: 1-5%."
            )
        )
        
        self.register_tooltip(
            "cement_blaine_field",
            TooltipInfo(
                "Blaine Fineness (cm²/g)",
                TooltipType.RICH,
                title="Blaine Fineness",
                details="Measure of cement particle fineness. Higher fineness increases early strength and heat generation. Typical range: 250-400 cm²/g."
            )
        )
        
        # Status and progress tooltips
        self.register_tooltip(
            "status_simulation_progress",
            TooltipInfo(
                "Simulation Progress",
                TooltipType.SIMPLE,
                details="Shows current simulation progress and estimated time remaining."
            )
        )
        
        # Error and validation tooltips
        self.register_tooltip(
            "validation_error_icon",
            TooltipInfo(
                "Validation Error",
                TooltipType.CONTEXTUAL,
                title="Input Validation",
                details="This field contains invalid data. Hover over the field for details.",
                help_topic="common_issues"
            )
        )
    
    def register_tooltip(self, widget_id: str, tooltip_info: TooltipInfo):
        """Register a tooltip for a widget."""
        self.tooltips[widget_id] = tooltip_info
    
    def register_tooltip_provider(self, widget_id: str, provider: Callable[[], str]):
        """Register a dynamic tooltip provider."""
        self.tooltip_providers[widget_id] = provider
    
    def apply_tooltip(self, widget: Gtk.Widget, widget_id: str):
        """Apply tooltip to a widget."""
        if widget_id in self.tooltips:
            tooltip_info = self.tooltips[widget_id]
            
            if tooltip_info.tooltip_type == TooltipType.SIMPLE:
                widget.set_tooltip_text(tooltip_info.text)
            
            elif tooltip_info.tooltip_type == TooltipType.RICH:
                widget.set_has_tooltip(True)
                widget.connect("query-tooltip", self._on_rich_tooltip_query, tooltip_info)
            
            elif tooltip_info.tooltip_type == TooltipType.CONTEXTUAL:
                widget.set_has_tooltip(True)
                widget.connect("query-tooltip", self._on_contextual_tooltip_query, tooltip_info)
            
            elif tooltip_info.tooltip_type == TooltipType.HELP:
                widget.set_has_tooltip(True)
                widget.connect("query-tooltip", self._on_help_tooltip_query, tooltip_info)
        
        elif widget_id in self.tooltip_providers:
            widget.set_has_tooltip(True)
            widget.connect("query-tooltip", self._on_dynamic_tooltip_query, widget_id)
    
    def apply_tooltips_to_container(self, container: Gtk.Container, prefix: str = ""):
        """Apply tooltips to all widgets in a container."""
        def apply_to_child(child):
            # Get widget name or generate ID
            widget_name = child.get_name()
            if widget_name and widget_name != "GtkWidget":
                widget_id = f"{prefix}{widget_name}" if prefix else widget_name
                self.apply_tooltip(child, widget_id)
            
            # Apply to children recursively
            if isinstance(child, Gtk.Container):
                child.foreach(apply_to_child)
        
        container.foreach(apply_to_child)
    
    def create_validation_tooltip(self, field_name: str, error_message: str) -> TooltipInfo:
        """Create a validation error tooltip."""
        return TooltipInfo(
            f"Validation Error: {error_message}",
            TooltipType.CONTEXTUAL,
            title=f"Invalid {field_name}",
            details=error_message,
            help_topic="common_issues"
        )
    
    def create_property_tooltip(self, property_name: str, description: str, 
                              typical_range: str = None, units: str = None) -> TooltipInfo:
        """Create a property field tooltip."""
        title = property_name
        if units:
            title += f" ({units})"
        
        details = description
        if typical_range:
            details += f"\nTypical range: {typical_range}"
        
        return TooltipInfo(
            title,
            TooltipType.RICH,
            title=title,
            details=details
        )
    
    def update_dynamic_tooltip(self, widget_id: str, text: str):
        """Update dynamic tooltip text."""
        if widget_id in self.custom_tooltips:
            widget = self.custom_tooltips[widget_id]
            widget.set_tooltip_text(text)
    
    # Tooltip query handlers
    
    def _on_rich_tooltip_query(self, widget, x, y, keyboard_mode, tooltip, tooltip_info):
        """Handle rich tooltip query."""
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        
        # Title
        if tooltip_info.title:
            title_label = Gtk.Label()
            title_label.set_markup(f"<b>{tooltip_info.title}</b>")
            title_label.set_halign(Gtk.Align.START)
            vbox.pack_start(title_label, False, False, 0)
        
        # Main text
        if tooltip_info.text:
            text_label = Gtk.Label(tooltip_info.text)
            text_label.set_halign(Gtk.Align.START)
            text_label.set_line_wrap(True)
            text_label.set_max_width_chars(50)
            vbox.pack_start(text_label, False, False, 0)
        
        # Details
        if tooltip_info.details:
            details_label = Gtk.Label()
            details_label.set_markup(f"<small>{tooltip_info.details}</small>")
            details_label.set_halign(Gtk.Align.START)
            details_label.set_line_wrap(True)
            details_label.set_max_width_chars(50)
            vbox.pack_start(details_label, False, False, 0)
        
        vbox.show_all()
        tooltip.set_custom(vbox)
        return True
    
    def _on_contextual_tooltip_query(self, widget, x, y, keyboard_mode, tooltip, tooltip_info):
        """Handle contextual tooltip query."""
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        
        # Icon
        icon = Gtk.Image.new_from_icon_name("help-contents", Gtk.IconSize.LARGE_TOOLBAR)
        hbox.pack_start(icon, False, False, 0)
        
        # Content
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        
        # Title
        if tooltip_info.title:
            title_label = Gtk.Label()
            title_label.set_markup(f"<b>{tooltip_info.title}</b>")
            title_label.set_halign(Gtk.Align.START)
            vbox.pack_start(title_label, False, False, 0)
        
        # Main text
        if tooltip_info.text:
            text_label = Gtk.Label(tooltip_info.text)
            text_label.set_halign(Gtk.Align.START)
            vbox.pack_start(text_label, False, False, 0)
        
        # Details
        if tooltip_info.details:
            details_label = Gtk.Label()
            details_label.set_markup(f"<small>{tooltip_info.details}</small>")
            details_label.set_halign(Gtk.Align.START)
            details_label.set_line_wrap(True)
            details_label.set_max_width_chars(40)
            vbox.pack_start(details_label, False, False, 0)
        
        # Help link
        if tooltip_info.help_topic:
            help_label = Gtk.Label()
            help_label.set_markup("<small><i>Press F1 for detailed help</i></small>")
            help_label.set_halign(Gtk.Align.START)
            vbox.pack_start(help_label, False, False, 0)
        
        hbox.pack_start(vbox, True, True, 0)
        
        hbox.show_all()
        tooltip.set_custom(hbox)
        return True
    
    def _on_help_tooltip_query(self, widget, x, y, keyboard_mode, tooltip, tooltip_info):
        """Handle help tooltip query."""
        # Similar to contextual but with help-specific styling
        return self._on_contextual_tooltip_query(widget, x, y, keyboard_mode, tooltip, tooltip_info)
    
    def _on_dynamic_tooltip_query(self, widget, x, y, keyboard_mode, tooltip, widget_id):
        """Handle dynamic tooltip query."""
        if widget_id in self.tooltip_providers:
            provider = self.tooltip_providers[widget_id]
            text = provider()
            
            if text:
                tooltip.set_text(text)
                return True
        
        return False
    
    def add_field_validation_tooltip(self, entry: Gtk.Entry, field_name: str):
        """Add validation tooltip to an entry field."""
        def on_validation_tooltip_query(widget, x, y, keyboard_mode, tooltip):
            # Get current validation state
            style_context = widget.get_style_context()
            
            if style_context.has_class("error"):
                # Show error tooltip
                error_text = widget.get_tooltip_text() or "Invalid input"
                
                hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
                
                # Error icon
                icon = Gtk.Image.new_from_icon_name("dialog-error", Gtk.IconSize.LARGE_TOOLBAR)
                hbox.pack_start(icon, False, False, 0)
                
                # Error message
                vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
                
                title_label = Gtk.Label()
                title_label.set_markup(f"<b>Invalid {field_name}</b>")
                title_label.set_halign(Gtk.Align.START)
                vbox.pack_start(title_label, False, False, 0)
                
                error_label = Gtk.Label(error_text)
                error_label.set_halign(Gtk.Align.START)
                error_label.set_line_wrap(True)
                error_label.set_max_width_chars(40)
                vbox.pack_start(error_label, False, False, 0)
                
                hbox.pack_start(vbox, True, True, 0)
                
                hbox.show_all()
                tooltip.set_custom(hbox)
                return True
            
            return False
        
        entry.set_has_tooltip(True)
        entry.connect("query-tooltip", on_validation_tooltip_query)
    
    def set_field_error(self, entry: Gtk.Entry, error_message: str):
        """Set field error state with tooltip."""
        style_context = entry.get_style_context()
        style_context.add_class("error")
        entry.set_tooltip_text(error_message)
    
    def clear_field_error(self, entry: Gtk.Entry):
        """Clear field error state."""
        style_context = entry.get_style_context()
        style_context.remove_class("error")
        entry.set_tooltip_text("")
    
    def create_info_tooltip_widget(self, text: str, help_topic: str = None) -> Gtk.Widget:
        """Create an info icon with tooltip."""
        info_button = Gtk.Button()
        info_button.set_image(Gtk.Image.new_from_icon_name("dialog-information", Gtk.IconSize.BUTTON))
        info_button.set_relief(Gtk.ReliefStyle.NONE)
        info_button.set_can_focus(False)
        
        tooltip_info = TooltipInfo(
            text,
            TooltipType.CONTEXTUAL if help_topic else TooltipType.RICH,
            help_topic=help_topic
        )
        
        info_button.set_has_tooltip(True)
        info_button.connect("query-tooltip", self._on_contextual_tooltip_query, tooltip_info)
        
        return info_button
    
    def create_help_tooltip_widget(self, help_topic: str) -> Gtk.Widget:
        """Create a help icon with contextual help."""
        help_button = Gtk.Button()
        help_button.set_image(Gtk.Image.new_from_icon_name("help-contents", Gtk.IconSize.BUTTON))
        help_button.set_relief(Gtk.ReliefStyle.NONE)
        help_button.set_can_focus(False)
        
        tooltip_info = TooltipInfo(
            "Click for detailed help",
            TooltipType.HELP,
            title="Get Help",
            details="Click to open detailed help for this topic",
            help_topic=help_topic
        )
        
        help_button.set_has_tooltip(True)
        help_button.connect("query-tooltip", self._on_help_tooltip_query, tooltip_info)
        
        # Connect click to show help
        def on_help_clicked(button):
            # Emit signal to show help - would be connected to help system
            print(f"Show help for topic: {help_topic}")
        
        help_button.connect("clicked", on_help_clicked)
        
        return help_button
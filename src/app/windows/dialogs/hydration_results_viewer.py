#!/usr/bin/env python3
"""
Hydration Results Viewer Dialog

3D visualization dialog for viewing time-series microstructure evolution 
from hydration simulation results. Uses the existing PyVista viewer to 
display initial and hydrated microstructures with time controls.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject

import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import logging
import re

# Import the existing PyVista 3D viewer
from app.visualization.pyvista_3d_viewer import PyVistaViewer3D


class HydrationResultsViewer(Gtk.Dialog):
    """Dialog for viewing 3D microstructure evolution from hydration simulation."""
    
    def __init__(self, parent=None, operation=None):
        super().__init__(
            title="Hydration Results - 3D Microstructure Evolution",
            transient_for=parent,
            flags=0
        )
        
        self.operation = operation
        self.logger = logging.getLogger(__name__)
        
        # Time-series data
        self.microstructure_files: List[Tuple[float, str]] = []  # (time_hours, filepath)
        self.current_time_index = 0
        
        # UI components
        self.pyvista_viewer = None
        self.time_slider = None
        self.time_label = None
        self.info_label = None
        
        # Dialog setup
        self.set_default_size(1000, 700)
        self.set_modal(True)
        
        # Add standard dialog buttons
        self.add_button("Close", Gtk.ResponseType.CLOSE)
        
        # Initialize UI
        self._setup_ui()
        self._load_microstructure_files()
        self._load_initial_microstructure()
        
    def _setup_ui(self) -> None:
        """Set up the user interface."""
        content_area = self.get_content_area()
        content_area.set_spacing(10)
        content_area.set_margin_left(10)
        content_area.set_margin_right(10)
        content_area.set_margin_top(10)
        content_area.set_margin_bottom(10)
        
        # Create main layout - 3D viewer on top, controls below
        main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        content_area.pack_start(main_vbox, True, True, 0)
        
        # Info label at top
        self.info_label = Gtk.Label()
        self.info_label.set_markup("<b>Hydration Simulation Results</b>")
        self.info_label.set_halign(Gtk.Align.START)
        main_vbox.pack_start(self.info_label, False, False, 0)
        
        # Create 3D viewer frame
        viewer_frame = Gtk.Frame(label="3D Microstructure Evolution")
        viewer_frame.set_size_request(-1, 500)
        main_vbox.pack_start(viewer_frame, True, True, 0)
        
        # Add PyVista viewer
        self.pyvista_viewer = PyVistaViewer3D()
        viewer_frame.add(self.pyvista_viewer)
        
        # Create time controls frame
        controls_frame = Gtk.Frame(label="Time Controls")
        main_vbox.pack_start(controls_frame, False, False, 0)
        
        # Time controls layout
        controls_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        controls_vbox.set_margin_left(10)
        controls_vbox.set_margin_right(10)
        controls_vbox.set_margin_top(5)
        controls_vbox.set_margin_bottom(10)
        controls_frame.add(controls_vbox)
        
        # Time display label
        self.time_label = Gtk.Label()
        self.time_label.set_markup("<b>Time: 0.0 hours</b>")
        self.time_label.set_halign(Gtk.Align.CENTER)
        controls_vbox.pack_start(self.time_label, False, False, 0)
        
        # Time slider
        self.time_slider = Gtk.Scale.new_with_range(
            orientation=Gtk.Orientation.HORIZONTAL,
            min=0,
            max=100,  # Will be updated when files are loaded
            step=1
        )
        self.time_slider.set_hexpand(True)
        self.time_slider.set_value(0)
        self.time_slider.connect('value-changed', self._on_time_changed)
        controls_vbox.pack_start(self.time_slider, False, False, 5)
        
        # Time navigation buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        button_box.set_halign(Gtk.Align.CENTER)
        controls_vbox.pack_start(button_box, False, False, 5)
        
        # Previous button
        prev_button = Gtk.Button(label="← Previous")
        prev_button.connect('clicked', self._on_previous_clicked)
        button_box.pack_start(prev_button, False, False, 0)
        
        # Next button
        next_button = Gtk.Button(label="Next →")
        next_button.connect('clicked', self._on_next_clicked)
        button_box.pack_start(next_button, False, False, 0)
        
        # Export view button
        export_button = Gtk.Button(label="Export View")
        export_button.connect('clicked', self._on_export_clicked)
        button_box.pack_start(export_button, False, False, 0)
        
    def _load_microstructure_files(self) -> None:
        """Load and sort all time-series microstructure files."""
        try:
            if not self.operation or not self.operation.output_dir:
                self.logger.error("No operation or output directory specified")
                return
            
            output_path = Path(self.operation.output_dir)
            if not output_path.exists():
                self.logger.error(f"Output directory does not exist: {output_path}")
                return
            
            # Find initial microstructure (original .img file)
            initial_files = list(output_path.glob("*.img"))
            initial_files = [f for f in initial_files if not any(x in f.name for x in ['.h.', 'HydrationOf_'])]
            
            if initial_files:
                self.microstructure_files.append((0.0, str(initial_files[0])))
                self.logger.info(f"Found initial microstructure: {initial_files[0].name}")
            
            # Find time-series files (pattern: *.img.XXX.XXh.XX.XXX)
            time_files = list(output_path.glob("*.img.*h.*.*"))
            
            for file_path in time_files:
                # Extract time from filename using regex
                match = re.search(r'\.(\d+\.?\d*)h\.', file_path.name)
                if match:
                    time_hours = float(match.group(1))
                    self.microstructure_files.append((time_hours, str(file_path)))
                    self.logger.info(f"Found time-series file: {file_path.name} at {time_hours}h")
            
            # Find final hydrated microstructure
            final_files = list(output_path.glob("HydrationOf_*.img.*.*"))
            if final_files:
                # Try to get the final time from CSV data or use a large number
                final_time = 999999.0  # Large number to place at end
                self.microstructure_files.append((final_time, str(final_files[0])))
                self.logger.info(f"Found final microstructure: {final_files[0].name}")
            
            # Sort by time
            self.microstructure_files.sort(key=lambda x: x[0])
            
            # Update slider range
            if len(self.microstructure_files) > 1:
                self.time_slider.set_range(0, len(self.microstructure_files) - 1)
                self.time_slider.set_increments(1, 1)
            
            self.logger.info(f"Loaded {len(self.microstructure_files)} microstructure files")
            
            # Update info label
            if self.microstructure_files:
                self.info_label.set_markup(
                    f"<b>Operation:</b> {self.operation.name}\n"
                    f"<b>Microstructures:</b> {len(self.microstructure_files)} time points"
                )
            
        except Exception as e:
            self.logger.error(f"Error loading microstructure files: {e}")
            
    def _load_initial_microstructure(self) -> None:
        """Load the initial microstructure in the 3D viewer."""
        if not self.microstructure_files:
            self.logger.warning("No microstructure files available")
            return
        
        try:
            # Load the first microstructure (time=0)
            self.current_time_index = 0
            time_hours, file_path = self.microstructure_files[0]
            
            # Use the existing PyVista viewer's load method
            if self.pyvista_viewer:
                self.pyvista_viewer.load_microstructure_file(file_path)
                self._update_time_display()
                
        except Exception as e:
            self.logger.error(f"Error loading initial microstructure: {e}")
    
    def _on_time_changed(self, slider) -> None:
        """Handle time slider value change."""
        try:
            new_index = int(slider.get_value())
            if 0 <= new_index < len(self.microstructure_files):
                self.current_time_index = new_index
                self._load_microstructure_at_index(new_index)
                
        except Exception as e:
            self.logger.error(f"Error handling time change: {e}")
    
    def _on_previous_clicked(self, button) -> None:
        """Handle previous button click."""
        if self.current_time_index > 0:
            self.current_time_index -= 1
            self.time_slider.set_value(self.current_time_index)
            self._load_microstructure_at_index(self.current_time_index)
    
    def _on_next_clicked(self, button) -> None:
        """Handle next button click."""
        if self.current_time_index < len(self.microstructure_files) - 1:
            self.current_time_index += 1
            self.time_slider.set_value(self.current_time_index)
            self._load_microstructure_at_index(self.current_time_index)
    
    def _load_microstructure_at_index(self, index: int) -> None:
        """Load microstructure at specified time index."""
        try:
            if 0 <= index < len(self.microstructure_files):
                time_hours, file_path = self.microstructure_files[index]
                
                # Load in PyVista viewer
                if self.pyvista_viewer:
                    self.pyvista_viewer.load_microstructure_file(file_path)
                    self._update_time_display()
                    
        except Exception as e:
            self.logger.error(f"Error loading microstructure at index {index}: {e}")
    
    def _update_time_display(self) -> None:
        """Update the time display label."""
        if 0 <= self.current_time_index < len(self.microstructure_files):
            time_hours, file_path = self.microstructure_files[self.current_time_index]
            
            if time_hours >= 999999:  # Final microstructure
                time_text = "Final Hydrated State"
            else:
                time_text = f"{time_hours:.2f} hours"
            
            self.time_label.set_markup(f"<b>Time: {time_text}</b>")
    
    def _on_export_clicked(self, button) -> None:
        """Handle export view button click."""
        try:
            if self.pyvista_viewer:
                # Use the PyVista viewer's export functionality
                self.pyvista_viewer._save_screenshot()
                
        except Exception as e:
            self.logger.error(f"Error exporting view: {e}")
            # Show error dialog
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Export Error"
            )
            dialog.format_secondary_text(f"Failed to export view: {e}")
            dialog.run()
            dialog.destroy()


# Register the widget
GObject.type_register(HydrationResultsViewer)
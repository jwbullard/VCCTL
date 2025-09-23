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
        
        # Cache colors to avoid re-reading CSV file every time
        self.cached_phase_mapping = None
        self.cached_phase_colors = None
        
        # Cache microstructure data for fast time navigation
        self.cached_voxel_data: Dict[int, np.ndarray] = {}  # index -> voxel_data
        self.cached_phase_meshes: Dict[int, Any] = {}  # index -> pre-built phase meshes
        self.preloading_complete = False
        
        # Cleanup flag to prevent double cleanup
        self.cleanup_performed = False
        
        # Track when dialog was hidden for automatic memory cleanup
        self.hidden_time = None
        self.auto_cleanup_timer = None
        
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
        
        # Connect cleanup handlers to prevent segfault
        self.connect('delete-event', self._on_delete_event)
        self.connect('response', self._on_response)
        
        # Initialize UI
        self._setup_ui()
        self._load_microstructure_files()
    
    def show_all(self):
        """Override show_all to cancel auto cleanup timer when dialog becomes visible."""
        self._cancel_auto_cleanup_timer()
        super().show_all()
        
        # Only load if not already loaded
        if not hasattr(self, '_initial_loaded') or not self._initial_loaded:
            self._load_initial_microstructure()
            # Start preloading other microstructures in background
            self._start_preloading()
            self._initial_loaded = True
        
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
        
        # Make sure the viewer is shown
        self.pyvista_viewer.show_all()
        
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
        
        # Export view button - REMOVED (non-functional, working version available in PyVista viewer)
        # export_button = Gtk.Button(label="Export View")
        # export_button.connect('clicked', self._on_export_clicked)
        # button_box.pack_start(export_button, False, False, 0)
        
    def _load_microstructure_files(self) -> None:
        """Load and sort all time-series microstructure files."""
        try:
            if not self.operation:
                self.logger.error("No operation specified")
                return
            
            # Get output directory from operation metadata
            output_dir = None
            if hasattr(self.operation, 'output_dir') and self.operation.output_dir:
                output_dir = self.operation.output_dir
            elif hasattr(self.operation, 'metadata') and self.operation.metadata:
                output_dir = self.operation.metadata.get('output_directory')
                if not output_dir:
                    output_dir = self.operation.metadata.get('output_dir')
            
            if not output_dir:
                # Try to construct from operation name
                project_root = Path(__file__).parent.parent.parent.parent
                operations_dir = project_root / "Operations"
                potential_folder = operations_dir / self.operation.name
                if potential_folder.exists():
                    output_dir = str(potential_folder)
            
            if not output_dir:
                self.logger.error("No output directory found for operation")
                return
            
            output_path = Path(output_dir)
            if not output_path.exists():
                self.logger.error(f"Output directory does not exist: {output_path}")
                return
            
            # Find initial microstructure (original .img file)
            initial_files = list(output_path.glob("*.img"))
            initial_files = [f for f in initial_files if not any(x in f.name for x in ['.h.', 'HydrationOf_'])]
            
            if initial_files:
                self.microstructure_files.append((0.0, str(initial_files[0])))
                self.logger.info(f"Found initial microstructure: {initial_files[0].name}")
            
            # Find time-series files (pattern: *.img.XXX.XXh.XX.XXX) - exclude .poredist files
            time_files = list(output_path.glob("*.img.*h.*.*"))
            time_files = [f for f in time_files if not f.name.endswith('.poredist')]
            
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
                    f"<b>Microstructures:</b> {len(self.microstructure_files)} time points\n"
                    f"<b>Status:</b> <span color='orange'>Preloading data...</span>"
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
            
            # Read microstructure file and load into PyVista viewer
            if self.pyvista_viewer:
                voxel_data = self._read_microstructure_file(file_path)
                if voxel_data is not None:
                    # VCCTL phase mapping with official colors - fresh read
                    phase_mapping, phase_colors = self._get_vcctl_phase_mapping()
                    self.logger.info(f"Loading {len(phase_colors)} colors from colors.csv for initial load")
                    
                    # Debug: log what phases and colors we actually loaded
                    for phase_id, phase_name in phase_mapping.items():
                        if phase_id in phase_colors:
                            color = phase_colors[phase_id]
                            self.logger.info(f"Phase {phase_id}: {phase_name} = RGB({color[0]*255:.0f}, {color[1]*255:.0f}, {color[2]*255:.0f})")
                    
                    # Clear any existing phase colors in PyVista viewer
                    if hasattr(self.pyvista_viewer, 'phase_colors'):
                        self.pyvista_viewer.phase_colors.clear()
                    
                    # Pre-set colors in PyVista viewer before loading data
                    for phase_id, rgb_color in phase_colors.items():
                        r = int(rgb_color[0] * 255)
                        g = int(rgb_color[1] * 255) 
                        b = int(rgb_color[2] * 255)
                        hex_color = f"#{r:02x}{g:02x}{b:02x}"
                        if hasattr(self.pyvista_viewer, 'set_phase_color'):
                            self.pyvista_viewer.set_phase_color(phase_id, hex_color)
                            self.logger.debug(f"Set PyVista color for phase {phase_id}: {hex_color}")
                    
                    self.logger.info(f"Loading voxel data into PyVista viewer...")
                    success = self.pyvista_viewer.load_voxel_data(voxel_data, phase_mapping)
                    self.logger.info(f"PyVista load_voxel_data returned: {success}")
                    self._update_time_display()
                else:
                    self.logger.error("Failed to read microstructure file data")
                
        except Exception as e:
            self.logger.error(f"Error loading initial microstructure: {e}")
    
    def _start_preloading(self) -> None:
        """Start background preloading of all microstructure data."""
        try:
            import threading
            
            if len(self.microstructure_files) > 1:
                self.logger.info(f"Starting background preloading of {len(self.microstructure_files)} microstructures...")
                
                # Start preloading in background thread
                preload_thread = threading.Thread(target=self._preload_all_microstructures, daemon=True)
                preload_thread.start()
            else:
                self.preloading_complete = True
                # For single microstructures, update status immediately
                self._update_preloading_status_complete()
                
        except Exception as e:
            self.logger.error(f"Error starting preloading: {e}")
    
    def _preload_all_microstructures(self) -> None:
        """Background thread to preload all microstructure data."""
        try:
            # Cache the first one (already loaded) 
            if self.current_time_index == 0 and len(self.microstructure_files) > 0:
                time_hours, file_path = self.microstructure_files[0]
                if file_path not in [str(fp) for _, fp in self.microstructure_files if _ in self.cached_voxel_data]:
                    voxel_data = self._read_microstructure_file(file_path)
                    if voxel_data is not None:
                        self.cached_voxel_data[0] = voxel_data
            
            # Preload remaining microstructures
            for index, (time_hours, file_path) in enumerate(self.microstructure_files):
                if index == self.current_time_index:
                    continue  # Skip currently loaded one
                    
                self.logger.info(f"Preloading microstructure {index + 1}/{len(self.microstructure_files)}: {time_hours}h")
                voxel_data = self._read_microstructure_file(file_path)
                
                if voxel_data is not None:
                    self.cached_voxel_data[index] = voxel_data
                else:
                    self.logger.warning(f"Failed to preload microstructure at index {index}")
            
            self.preloading_complete = True
            self.logger.info(f"Preloading complete! Cached {len(self.cached_voxel_data)} microstructures")
            
            # Update UI status on main thread
            from gi.repository import GLib
            GLib.idle_add(self._update_preloading_status_complete)
            
        except Exception as e:
            self.logger.error(f"Error during preloading: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
    
    def _update_preloading_status_complete(self) -> bool:
        """Update UI to show preloading is complete (called on main thread)."""
        try:
            if self.info_label and self.operation:
                self.info_label.set_markup(
                    f"<b>Operation:</b> {self.operation.name}\n"
                    f"<b>Microstructures:</b> {len(self.microstructure_files)} time points\n"
                    f"<b>Status:</b> <span color='green'>Ready - All data cached</span>\n"
                    f"<i>Note: 3D visualization rebuilding takes ~2 seconds per time point</i>"
                )
        except Exception as e:
            self.logger.error(f"Error updating preloading status: {e}")
        
        return False  # Don't repeat this idle callback
    
    def _read_microstructure_file(self, file_path: str) -> Optional[np.ndarray]:
        """Read a VCCTL microstructure file and return voxel data."""
        try:
            from pathlib import Path
            
            file_path = Path(file_path)
            self.logger.info(f"Reading microstructure file: {file_path}")
            
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            # Parse header to get dimensions
            x_size = y_size = z_size = None
            header_end = 0
            
            for i, line in enumerate(lines):
                line = line.strip()
                if line.startswith('X_Size:'):
                    x_size = int(line.split(':')[1].strip())
                elif line.startswith('Y_Size:'):
                    y_size = int(line.split(':')[1].strip())
                elif line.startswith('Z_Size:'):
                    z_size = int(line.split(':')[1].strip())
                elif line.startswith('Image_Resolution:'):
                    # This is typically the last header line
                    header_end = i + 1
                    break
                    
            if not all([x_size, y_size, z_size]):
                self.logger.error(f"Could not parse dimensions from {file_path}")
                return None
                
            # Read voxel data (skip header lines)
            data_lines = lines[header_end:]
            
            # Parse the voxel data - each line can contain multiple integers
            voxel_data = []
            for line_num, line in enumerate(data_lines):
                line = line.strip()
                if line and not line.startswith('#'):  # Skip comments and empty lines
                    try:
                        # Split line and convert to integers
                        values = [int(x) for x in line.split()]
                        voxel_data.extend(values)
                    except ValueError as e:
                        self.logger.warning(f"Could not parse line {header_end + line_num + 1}: {line[:50]}... Error: {e}")
                        continue
            
            # Reshape to 3D array
            total_voxels = x_size * y_size * z_size
            self.logger.info(f"Expected {total_voxels} voxels, got {len(voxel_data)} values")
            
            if len(voxel_data) >= total_voxels:
                voxel_array = np.array(voxel_data[:total_voxels]).reshape((z_size, y_size, x_size))
                self.logger.info(f"Successfully loaded microstructure: {x_size}x{y_size}x{z_size}")
                self.logger.info(f"Unique phases in data: {np.unique(voxel_array)}")
                return voxel_array
            else:
                self.logger.error(f"Insufficient data: got {len(voxel_data)}, expected {total_voxels}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error reading microstructure file {file_path}: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None
    
    def _get_vcctl_phase_mapping(self, use_cache: bool = True) -> Tuple[Dict[int, str], Dict[int, Tuple[float, float, float]]]:
        """Get VCCTL phase mapping and colors from colors.csv."""
        try:
            # Return cached colors if available and requested
            if use_cache and self.cached_phase_mapping is not None and self.cached_phase_colors is not None:
                return self.cached_phase_mapping, self.cached_phase_colors
            
            # Import pandas here to avoid dependency issues
            import pandas as pd
            
            # Get path to colors.csv - it's in the project root
            colors_file = Path(__file__).parent.parent.parent.parent.parent / "colors" / "colors.csv"
            
            if not colors_file.exists():
                self.logger.warning(f"Colors file not found: {colors_file}")
                return self._get_default_phase_mapping()
            
            # Read colors CSV - skip malformed header and use manual parsing
            with open(colors_file, 'r') as f:
                lines = f.readlines()
            
            phase_mapping = {}
            phase_colors = {}
            
            for line_num, line in enumerate(lines):
                line = line.strip()
                if not line or line.startswith('Phase,id') or line.startswith('#'):
                    continue
                    
                try:
                    # Split by comma and clean up values
                    parts = [part.strip() for part in line.split(',')]
                    if len(parts) < 4:
                        continue
                        
                    phase_id = int(parts[0])
                    phase_name = parts[1] if parts[1] else f"Phase_{phase_id}"
                    
                    # Handle RGB values - fix common typos
                    red_str = parts[2].replace('o', '0')  # Fix 'o' -> '0' typo
                    green_str = parts[3].replace('.', ',') if '.' in parts[3] and ',' not in parts[3] else parts[3]
                    blue_str = parts[4] if len(parts) > 4 else '0'
                    
                    # Parse RGB values
                    red = float(red_str.split(',')[0]) if ',' in red_str else float(red_str)
                    green = float(green_str.split(',')[-1]) if ',' in green_str else float(green_str)
                    blue = float(blue_str)
                    
                    # Normalize RGB (0-255) to (0-1) for PyVista
                    red_norm = red / 255.0
                    green_norm = green / 255.0
                    blue_norm = blue / 255.0
                    
                    phase_mapping[phase_id] = phase_name
                    phase_colors[phase_id] = (red_norm, green_norm, blue_norm)
                    
                    self.logger.debug(f"Loaded phase {phase_id}: {phase_name} = RGB({red}, {green}, {blue})")
                    
                except (ValueError, TypeError, IndexError) as e:
                    self.logger.warning(f"Skipping invalid line {line_num + 1} in colors.csv: '{line}' - Error: {e}")
            
            self.logger.info(f"Loaded {len(phase_mapping)} VCCTL phase colors")
            
            # Cache the results for future use
            self.cached_phase_mapping = phase_mapping
            self.cached_phase_colors = phase_colors
            
            return phase_mapping, phase_colors
            
        except Exception as e:
            self.logger.error(f"Error loading VCCTL colors: {e}")
            return self._get_default_phase_mapping()
    
    def _get_default_phase_mapping(self) -> Tuple[Dict[int, str], Dict[int, Tuple[float, float, float]]]:
        """Fallback phase mapping with default colors."""
        phase_mapping = {
            0: "Porosity",
            1: "C3S", 
            2: "C2S",
            3: "C3A",
            4: "C4AF",
            7: "Gypsum",
            8: "Hemihydrate",
            9: "Anhydrite",
            19: "Portlandite",
            20: "CSH",
            22: "AFt",
            24: "AFm"
        }
        
        # Default colors (basic scheme)
        phase_colors = {
            0: (0.1, 0.1, 0.1),    # Dark grey for pores
            1: (0.16, 0.16, 0.82), # Blue for C3S
            2: (0.55, 0.31, 0.07), # Brown for C2S  
            3: (0.7, 0.7, 0.7),    # Grey for C3A
            4: (1.0, 1.0, 1.0),    # White for C4AF
            7: (1.0, 1.0, 0.0),    # Yellow for Gypsum
            8: (1.0, 0.94, 0.34),  # Light yellow
            9: (1.0, 1.0, 0.5),    # Pale yellow
            19: (0.03, 0.28, 0.56), # Blue for Portlandite
            20: (0.96, 0.87, 0.7),  # Beige for CSH
            22: (0.5, 0.0, 1.0),    # Purple for AFt
            24: (0.96, 0.27, 0.8)   # Pink for AFm
        }
        
        return phase_mapping, phase_colors
    
    def _apply_vcctl_colors(self, phase_colors: Dict[int, Tuple[float, float, float]]) -> None:
        """Apply VCCTL colors to the PyVista viewer."""
        try:
            # Convert RGB tuples to hex strings and apply to PyVista viewer
            for phase_id, rgb_color in phase_colors.items():
                # Convert normalized RGB (0-1) to 8-bit RGB (0-255) and then to hex
                r = int(rgb_color[0] * 255)
                g = int(rgb_color[1] * 255) 
                b = int(rgb_color[2] * 255)
                hex_color = f"#{r:02x}{g:02x}{b:02x}"
                
                # Use PyVista viewer's set_phase_color method
                if hasattr(self.pyvista_viewer, 'set_phase_color'):
                    self.pyvista_viewer.set_phase_color(phase_id, hex_color)
                    self.logger.debug(f"Applied VCCTL color {hex_color} to phase {phase_id}")
            
            # Don't call _create_phase_meshes() as it can hang - colors will be applied on next load
            self.logger.info(f"Set {len(phase_colors)} VCCTL phase colors for future use")
                    
        except Exception as e:
            self.logger.warning(f"Could not apply VCCTL colors: {e}")
            import traceback
            self.logger.warning(traceback.format_exc())
    
    def _load_microstructure_at_index(self, index: int) -> None:
        """Load microstructure at specific time index."""
        try:
            if 0 <= index < len(self.microstructure_files):
                time_hours, file_path = self.microstructure_files[index]
                self.logger.info(f"_load_microstructure_at_index({index}): Loading {file_path} at {time_hours}h")
                
                # Get microstructure data (cached if available, otherwise read from file)
                voxel_data = None
                if index in self.cached_voxel_data:
                    voxel_data = self.cached_voxel_data[index]
                    self.logger.info(f"Using cached voxel data for index {index}")
                else:
                    self.logger.info(f"Reading voxel data from file for index {index}")
                    voxel_data = self._read_microstructure_file(file_path)
                    # Cache it for future use
                    if voxel_data is not None:
                        self.cached_voxel_data[index] = voxel_data
                
                if voxel_data is not None and self.pyvista_viewer:
                    # Use cached phase mapping and colors for speed
                    phase_mapping, phase_colors = self._get_vcctl_phase_mapping(use_cache=True)
                    
                    # Update time display immediately to show user we're responding
                    self.current_time_index = index
                    self._update_time_display_with_status("Loading 3D visualization...")
                    
                    self.logger.info(f"Calling PyVista load_voxel_data for index {index}...")
                    success = self.pyvista_viewer.load_voxel_data(voxel_data, phase_mapping)
                    self.logger.info(f"PyVista load_voxel_data returned: {success}")
                    
                    # Update display again to remove loading status
                    self._update_time_display()
                    self.logger.info(f"Successfully loaded microstructure at index {index}")
                else:
                    if voxel_data is None:
                        self.logger.error(f"Failed to read voxel data for index {index}")
                    if not self.pyvista_viewer:
                        self.logger.error(f"PyVista viewer is None for index {index}")
            else:
                self.logger.error(f"Index {index} out of range (0-{len(self.microstructure_files)-1})")
                    
        except Exception as e:
            self.logger.error(f"Error loading microstructure at index {index}: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
    
    def _on_time_changed(self, slider) -> None:
        """Handle time slider value change."""
        try:
            new_index = int(slider.get_value())
            self.logger.info(f"Time slider changed to index {new_index} (was {self.current_time_index})")
            
            if 0 <= new_index < len(self.microstructure_files):
                if new_index != self.current_time_index:  # Only load if actually changed
                    self.current_time_index = new_index
                    time_hours, file_path = self.microstructure_files[new_index]
                    self.logger.info(f"Loading microstructure at {time_hours}h: {file_path}")
                    self._load_microstructure_at_index(new_index)
                else:
                    self.logger.debug(f"Time slider at same index {new_index}, skipping reload")
            else:
                self.logger.warning(f"Time slider index {new_index} out of range (0-{len(self.microstructure_files)-1})")
                
        except Exception as e:
            self.logger.error(f"Error handling time change: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
    
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
    
    
    def _update_time_display(self) -> None:
        """Update the time display label."""
        if 0 <= self.current_time_index < len(self.microstructure_files):
            time_hours, file_path = self.microstructure_files[self.current_time_index]
            
            if time_hours >= 999999:  # Final microstructure
                time_text = "Final Hydrated State"
            else:
                time_text = f"{time_hours:.2f} hours"
            
            self.time_label.set_markup(f"<b>Time: {time_text}</b>")
    
    def _update_time_display_with_status(self, status: str) -> None:
        """Update the time display label with a status message."""
        if 0 <= self.current_time_index < len(self.microstructure_files):
            time_hours, file_path = self.microstructure_files[self.current_time_index]
            
            if time_hours >= 999999:  # Final microstructure
                time_text = "Final Hydrated State"
            else:
                time_text = f"{time_hours:.2f} hours"
            
            self.time_label.set_markup(f"<b>Time: {time_text}</b> - <span color='orange'>{status}</span>")
    
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
    
    def _on_delete_event(self, widget, event):
        """Handle window close event - hide instead of destroy to avoid PyVista segfault."""
        try:
            self.logger.info("Window close requested - hiding dialog instead of destroying")
            self.hide()
            self._start_auto_cleanup_timer()
            # Return True to prevent default destroy behavior
            return True
        except Exception as e:
            self.logger.error(f"Error in delete event handler: {e}")
            # If hiding fails, allow destruction to prevent hanging
            return False
    
    def _on_response(self, dialog, response_id):
        """Handle dialog response (Close button clicked)."""
        if response_id == Gtk.ResponseType.CLOSE:
            self.logger.info("Close button clicked - hiding dialog instead of destroying")
            self.hide()
            self._start_auto_cleanup_timer()
            # Don't let default response handling proceed to avoid destruction
    
    def _cleanup_pyvista(self):
        """Clean up PyVista viewer to prevent segfaults."""
        # Prevent double cleanup
        if self.cleanup_performed:
            self.logger.info("PyVista cleanup already performed, skipping")
            return
            
        try:
            self.cleanup_performed = True
            self.logger.info("Starting PyVista cleanup...")
            
            # First disable all UI interactions to prevent further calls to PyVista
            if hasattr(self, 'time_slider') and self.time_slider:
                self.time_slider.set_sensitive(False)
            
            # Clear cached data first to free memory
            if hasattr(self, 'cached_voxel_data'):
                self.cached_voxel_data.clear()
            if hasattr(self, 'cached_phase_meshes'):
                self.cached_phase_meshes.clear()
            
            # Now try to cleanup PyVista safely with minimum operations
            if hasattr(self, 'pyvista_viewer') and self.pyvista_viewer:
                try:
                    # Try to clear any active plots/meshes first
                    if hasattr(self.pyvista_viewer, 'plotter') and self.pyvista_viewer.plotter:
                        self.pyvista_viewer.plotter.clear()
                    
                    # Try to call cleanup if it exists  
                    if hasattr(self.pyvista_viewer, 'cleanup'):
                        self.pyvista_viewer.cleanup()
                        
                except Exception as cleanup_error:
                    # Don't let PyVista cleanup errors stop us
                    self.logger.warning(f"PyVista cleanup method failed (continuing anyway): {cleanup_error}")
                
                # Clear reference regardless of cleanup success/failure
                self.pyvista_viewer = None
                self.logger.info("PyVista viewer reference cleared")
            
            self.logger.info("PyVista cleanup completed")
                
        except Exception as e:
            # If cleanup fails, just log it and continue - don't let it crash the app
            self.logger.warning(f"Error during PyVista cleanup (ignoring): {e}")
            # Still mark as performed to prevent retry
            self.cleanup_performed = True
    
    def _start_auto_cleanup_timer(self):
        """Start timer for automatic memory cleanup of hidden dialogs."""
        try:
            import time
            from gi.repository import GLib
            
            self.hidden_time = time.time()
            
            # Cancel existing timer if any
            if self.auto_cleanup_timer:
                GLib.source_remove(self.auto_cleanup_timer)
            
            # Start timer for 5 minutes (300 seconds)
            self.auto_cleanup_timer = GLib.timeout_add_seconds(
                300,  # 5 minutes
                self._auto_cleanup_memory
            )
            
            self.logger.info("Started automatic memory cleanup timer (5 minutes)")
            
        except Exception as e:
            self.logger.warning(f"Failed to start auto cleanup timer: {e}")
    
    def _auto_cleanup_memory(self):
        """Automatically clean up memory from hidden dialogs (safe cleanup only)."""
        try:
            self.logger.info("Starting automatic memory cleanup for hidden dialog...")
            
            # Only clear cached data - this is safe and frees the most memory
            cache_cleared = False
            
            if hasattr(self, 'cached_voxel_data') and self.cached_voxel_data:
                data_count = len(self.cached_voxel_data)
                self.cached_voxel_data.clear()
                self.logger.info(f"Cleared {data_count} cached voxel datasets")
                cache_cleared = True
            
            if hasattr(self, 'cached_phase_meshes') and self.cached_phase_meshes:
                mesh_count = len(self.cached_phase_meshes)
                self.cached_phase_meshes.clear()
                self.logger.info(f"Cleared {mesh_count} cached phase meshes")
                cache_cleared = True
            
            if cache_cleared:
                self.logger.info("Automatic memory cleanup completed - cached data cleared")
            else:
                self.logger.info("Automatic memory cleanup - no cached data to clear")
            
            # Clear the timer reference
            self.auto_cleanup_timer = None
            
            # Return False to stop the timer from repeating
            return False
            
        except Exception as e:
            self.logger.warning(f"Error during automatic memory cleanup: {e}")
            # Clear timer reference even if cleanup failed
            self.auto_cleanup_timer = None
            return False
    
    def _cancel_auto_cleanup_timer(self):
        """Cancel the automatic cleanup timer if dialog is shown again."""
        try:
            if self.auto_cleanup_timer:
                from gi.repository import GLib
                GLib.source_remove(self.auto_cleanup_timer)
                self.auto_cleanup_timer = None
                self.logger.info("Cancelled automatic memory cleanup timer")
        except Exception as e:
            self.logger.warning(f"Error cancelling auto cleanup timer: {e}")
    


# Register the widget
GObject.type_register(HydrationResultsViewer)
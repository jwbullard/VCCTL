#!/usr/bin/env python3
"""
PyVista-based 3D Microstructure Viewer for VCCTL

High-quality 3D visualization using PyVista/VTK for Ovito-style rendering
with professional lighting, materials, and interaction capabilities.
"""

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import Gtk, GObject, Gdk, GdkPixbuf

import pyvista as pv
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Union
import logging
from pathlib import Path
import io
import PIL.Image

# Configure PyVista for headless rendering (no Qt required)
pv.set_plot_theme("default")  # Default theme with better lighting
pv.global_theme.window_size = [800, 600] 
pv.global_theme.font.size = 10
pv.global_theme.background = 'white'  # Keep white background

# Try to start virtual display for headless rendering (Linux/CI only)
try:
    pv.start_xvfb()
except Exception:
    # On macOS/Windows, headless rendering works without xvfb
    pass


class PyVistaViewer3D(Gtk.Box):
    """
    PyVista-based 3D Microstructure Viewer
    
    Features:
    - High-quality volume rendering
    - Professional lighting and materials  
    - Advanced interaction (rotate, zoom, pan)
    - Isosurface generation
    - Cross-sectional views
    - Multiple rendering modes
    - Export capabilities
    """
    
    __gsignals__ = {
        'data-loaded': (GObject.SIGNAL_RUN_FIRST, None, ()),
        'view-changed': (GObject.SIGNAL_RUN_FIRST, None, ()),
        'rendering-mode-changed': (GObject.SIGNAL_RUN_FIRST, None, (str,)),
    }
    
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        
        self.logger = logging.getLogger('VCCTL.PyVistaViewer3D')
        
        # 3D data storage
        self.voxel_data = None
        self.phase_mapping = {}
        self.voxel_size = (1.0, 1.0, 1.0)  # μm per voxel
        self.mesh_objects = {}  # Store VTK mesh objects for each phase
        
        # Visualization settings
        self.rendering_mode = 'volume'  # 'volume', 'isosurface', 'points', 'wireframe'  
        # Standard VCCTL phase colors (from colors.csv)
        self.phase_colors = {
            0: '#191919',   # Porosity (dark gray)
            1: '#2A2AD2',   # C3S (blue)
            2: '#8B4F13',   # C2S (brown)
            3: '#B2B2B2',   # C3A (light gray)
            4: '#FDFDFD',   # C4AF (white)
            5: '#FF0000',   # K2SO4 (red)
            6: '#FF1400',   # Na2SO4 (red-orange)
            7: '#FFFF00',   # Gypsum (yellow)
            8: '#FFF056',   # Hemihydrate (light yellow)
            9: '#FFFF80',   # Anhydrite (pale yellow)
            10: '#28AD4B',  # Silica fume (green)
            12: '#FF69B4',  # Slag (hot pink)
            18: '#DDA0DD',  # Fly ash (plum)
            30: '#F0E68C',  # Silica fume alternate (khaki)
            100: '#D3D3D3'  # Aggregate (light gray)
        }
        self.phase_opacity = {}  # Per-phase opacity control
        self.show_phase = {}     # Per-phase visibility control
        
        # Lighting and camera settings
        self.diffuse_coefficient = 0.8  # Higher diffuse for better contrast
        self.specular_coefficient = 0.3  # Higher specular for more shine
        self.specular_power = 20
        
        # Cross-section settings
        self.cross_section_enabled = {'x': False, 'y': False, 'z': False}
        self.cross_section_positions = {'x': 0.5, 'y': 0.5, 'z': 0.5}  # As fractions of volume
        self.volume_bounds = None  # Will be set when data is loaded
        
        # Create PyVista plotter widget
        self._create_pyvista_widget()
        
        # Create control panel
        self._create_control_panel()
        
        # Create phase control panel (initially hidden)
        self._create_phase_control_panel()
        
        # Create main content area with overlay capability
        self.main_content = Gtk.Overlay()
        
        # Create vertical box for controls and image
        main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        main_vbox.pack_start(self.control_panel, False, False, 0)
        main_vbox.pack_start(self.plotter_widget, True, True, 0)
        
        # Add main content to overlay
        self.main_content.add(main_vbox)
        
        # Add phase control panel as overlay (positioned on left side)
        self.main_content.add_overlay(self.phase_control_panel)
        self.main_content.set_overlay_pass_through(self.phase_control_panel, False)
        
        # Position phase control panel on the left side
        self.phase_control_panel.set_halign(Gtk.Align.START)
        self.phase_control_panel.set_valign(Gtk.Align.START)
        self.phase_control_panel.set_margin_top(80)  # More space below control buttons
        
        # Layout
        self.pack_start(self.main_content, True, True, 0)
        
        self.show_all()
        
        self.logger.info("PyVista 3D viewer initialized")
    
    def _create_pyvista_widget(self):
        """Create PyVista widget using headless rendering."""
        try:
            # Create headless PyVista plotter
            self.plotter = pv.Plotter(
                off_screen=True,  # Headless rendering
                window_size=[1200, 900],  # Even larger viewing window to fill available space
                lighting='three_lights'  # Professional 3-point lighting
            )
            
            # Configure plotter
            self.plotter.background_color = 'white'
            self.plotter.enable_depth_peeling(number_of_peels=10)  # Better transparency
            self.plotter.enable_anti_aliasing('ssaa')  # Smooth edges
            
            # Ensure proper lighting setup
            self.plotter.remove_all_lights()  # Clear any default lights
            self.plotter.add_light(pv.Light(position=(1, 1, 1), focal_point=(0, 0, 0), color='white', intensity=0.8))
            self.plotter.add_light(pv.Light(position=(-1, -1, 1), focal_point=(0, 0, 0), color='white', intensity=0.4))
            self.plotter.add_light(pv.Light(position=(0, 0, -1), focal_point=(0, 0, 0), color='white', intensity=0.2))
            
            # Create GTK image widget to display rendered images
            self.image_widget = Gtk.Image()
            # Remove fixed size constraint to allow expansion
            self.image_widget.set_hexpand(True)
            self.image_widget.set_vexpand(True)
            self.image_widget.set_halign(Gtk.Align.CENTER)
            self.image_widget.set_valign(Gtk.Align.CENTER)
            
            # Create scrolled window for the image
            scrolled = Gtk.ScrolledWindow()
            scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
            scrolled.set_hexpand(True)
            scrolled.set_vexpand(True)
            scrolled.add(self.image_widget)
            
            # Create main widget container
            self.plotter_widget = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            self.plotter_widget.pack_start(scrolled, True, True, 0)
            
            # Add status label
            self.render_status = Gtk.Label("PyVista 3D Viewer Ready")
            self.render_status.set_halign(Gtk.Align.CENTER)
            self.plotter_widget.pack_start(self.render_status, False, False, 5)
            
            self.logger.info("PyVista headless plotter created successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to create PyVista widget: {e}")
            # Fallback to placeholder
            self.plotter_widget = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            error_label = Gtk.Label(f"PyVista initialization failed:\n{e}")
            error_label.set_justify(Gtk.Justification.CENTER)
            self.plotter_widget.pack_start(error_label, True, True, 0)
    
    def _create_control_panel(self):
        """Create control panel with PyVista-specific options."""
        self.control_panel = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.control_panel.set_margin_left(10)
        self.control_panel.set_margin_right(10)
        self.control_panel.set_margin_top(5)
        self.control_panel.set_margin_bottom(5)
        
        # Rendering mode selection
        mode_label = Gtk.Label("Rendering:")
        self.control_panel.pack_start(mode_label, False, False, 0)
        
        self.mode_combo = Gtk.ComboBoxText()
        self.mode_combo.append("volume", "Volume Rendering")
        self.mode_combo.append("isosurface", "Isosurface")
        self.mode_combo.append("points", "Point Cloud")
        self.mode_combo.append("wireframe", "Wireframe")
        self.mode_combo.set_active_id("volume")
        self.mode_combo.connect('changed', self._on_rendering_mode_changed)
        self.control_panel.pack_start(self.mode_combo, False, False, 0)
        
        # Separator
        separator1 = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        self.control_panel.pack_start(separator1, False, False, 5)
        
        
        # View controls
        view_label = Gtk.Label("View:")
        self.control_panel.pack_start(view_label, False, False, 0)
        
        # Preset views
        iso_button = Gtk.Button("Isometric")
        iso_button.connect('clicked', lambda b: self._set_camera_view('isometric'))
        self.control_panel.pack_start(iso_button, False, False, 0)
        
        xy_button = Gtk.Button("XY")
        xy_button.connect('clicked', lambda b: self._set_camera_view('xy'))
        self.control_panel.pack_start(xy_button, False, False, 0)
        
        xz_button = Gtk.Button("XZ") 
        xz_button.connect('clicked', lambda b: self._set_camera_view('xz'))
        self.control_panel.pack_start(xz_button, False, False, 0)
        
        yz_button = Gtk.Button("YZ")
        yz_button.connect('clicked', lambda b: self._set_camera_view('yz'))
        self.control_panel.pack_start(yz_button, False, False, 0)
        
        # Separator
        separator3 = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        self.control_panel.pack_start(separator3, False, False, 5)
        
        # Export button
        export_button = Gtk.Button("Export View")
        export_button.connect('clicked', self._on_export_clicked)
        self.control_panel.pack_start(export_button, False, False, 0)
        
        # Reset button
        # Interactive controls
        separator4 = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        self.control_panel.pack_start(separator4, False, False, 5)
        
        interact_label = Gtk.Label("Rotate:")
        self.control_panel.pack_start(interact_label, False, False, 0)
        
        # Rotation buttons
        rotate_left = Gtk.Button("◀")
        rotate_left.set_tooltip_text("Rotate left")
        rotate_left.connect('clicked', self._on_rotate_left_clicked)
        self.control_panel.pack_start(rotate_left, False, False, 0)
        
        rotate_right = Gtk.Button("▶")
        rotate_right.set_tooltip_text("Rotate right")
        rotate_right.connect('clicked', self._on_rotate_right_clicked)
        self.control_panel.pack_start(rotate_right, False, False, 0)
        
        rotate_up = Gtk.Button("▲")
        rotate_up.set_tooltip_text("Rotate up")
        rotate_up.connect('clicked', self._on_rotate_up_clicked)
        self.control_panel.pack_start(rotate_up, False, False, 0)
        
        rotate_down = Gtk.Button("▼")
        rotate_down.set_tooltip_text("Rotate down")
        rotate_down.connect('clicked', self._on_rotate_down_clicked)
        self.control_panel.pack_start(rotate_down, False, False, 0)
        
        # Zoom controls
        zoom_in = Gtk.Button("Zoom+")
        zoom_in.connect('clicked', self._on_zoom_in_clicked)
        self.control_panel.pack_start(zoom_in, False, False, 0)
        
        zoom_out = Gtk.Button("Zoom-")
        zoom_out.connect('clicked', self._on_zoom_out_clicked)
        self.control_panel.pack_start(zoom_out, False, False, 0)
        
        # Separator
        separator3 = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        self.control_panel.pack_start(separator3, False, False, 5)
        
        # Cross-section controls - create a vertical section
        cross_section_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        
        cross_section_label = Gtk.Label("Cross-Sections:")
        cross_section_vbox.pack_start(cross_section_label, False, False, 0)
        
        # Create checkbox row
        checkbox_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        
        # X cutting plane
        x_cut_check = Gtk.CheckButton("X")
        x_cut_check.set_tooltip_text("Enable YZ plane cutting")
        x_cut_check.connect('toggled', lambda btn: self._on_cross_section_toggled('x', btn))
        checkbox_row.pack_start(x_cut_check, False, False, 0)
        
        # Y cutting plane
        y_cut_check = Gtk.CheckButton("Y")
        y_cut_check.set_tooltip_text("Enable XZ plane cutting")
        y_cut_check.connect('toggled', lambda btn: self._on_cross_section_toggled('y', btn))
        checkbox_row.pack_start(y_cut_check, False, False, 0)
        
        # Z cutting plane
        z_cut_check = Gtk.CheckButton("Z")
        z_cut_check.set_tooltip_text("Enable XY plane cutting")
        z_cut_check.connect('toggled', lambda btn: self._on_cross_section_toggled('z', btn))
        checkbox_row.pack_start(z_cut_check, False, False, 0)
        
        cross_section_vbox.pack_start(checkbox_row, False, False, 0)
        
        # Create slider row
        slider_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        
        # X spin box
        x_cut_spin = Gtk.SpinButton(adjustment=Gtk.Adjustment(0.5, 0.0, 1.0, 0.01, 0.1, 0.0), digits=3)
        x_cut_spin.set_size_request(80, -1)
        x_cut_spin.set_tooltip_text("X cutting plane position (0.0 to 1.0)")
        x_cut_spin.set_sensitive(False)  # Initially disabled
        x_cut_spin.connect('value-changed', lambda spin: self._on_cross_section_position_changed('x', spin))
        slider_row.pack_start(x_cut_spin, False, False, 0)
        
        # Y spin box  
        y_cut_spin = Gtk.SpinButton(adjustment=Gtk.Adjustment(0.5, 0.0, 1.0, 0.01, 0.1, 0.0), digits=3)
        y_cut_spin.set_size_request(80, -1)
        y_cut_spin.set_tooltip_text("Y cutting plane position (0.0 to 1.0)")
        y_cut_spin.set_sensitive(False)  # Initially disabled
        y_cut_spin.connect('value-changed', lambda spin: self._on_cross_section_position_changed('y', spin))
        slider_row.pack_start(y_cut_spin, False, False, 0)
        
        # Z spin box
        z_cut_spin = Gtk.SpinButton(adjustment=Gtk.Adjustment(0.5, 0.0, 1.0, 0.01, 0.1, 0.0), digits=3)
        z_cut_spin.set_size_request(80, -1)
        z_cut_spin.set_tooltip_text("Z cutting plane position (0.0 to 1.0)")
        z_cut_spin.set_sensitive(False)  # Initially disabled
        z_cut_spin.connect('value-changed', lambda spin: self._on_cross_section_position_changed('z', spin))
        slider_row.pack_start(z_cut_spin, False, False, 0)
        
        cross_section_vbox.pack_start(slider_row, False, False, 0)
        
        # Add the cross-section controls to main panel  
        self.control_panel.pack_start(cross_section_vbox, False, False, 0)
        
        # Store references to controls
        self.cross_section_controls = {
            'x': (x_cut_check, x_cut_spin),
            'y': (y_cut_check, y_cut_spin),
            'z': (z_cut_check, z_cut_spin)
        }
        
        # Reset cuts button
        reset_cuts_button = Gtk.Button("Reset Cuts")
        reset_cuts_button.set_tooltip_text("Remove all cross-sections")
        reset_cuts_button.connect('clicked', self._on_reset_cuts_clicked)
        self.control_panel.pack_start(reset_cuts_button, False, False, 0)
        
        # Separator
        separator4 = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        self.control_panel.pack_start(separator4, False, False, 5)
        
        # Reset view button
        reset_button = Gtk.Button("Reset View")
        reset_button.connect('clicked', self._on_reset_view_clicked)
        self.control_panel.pack_start(reset_button, False, False, 0)
    
    def _create_phase_control_panel(self):
        """Create phase control panel for color customization."""
        self.phase_control_panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.phase_control_panel.set_margin_left(10)
        self.phase_control_panel.set_margin_right(10)
        self.phase_control_panel.set_margin_top(5)
        self.phase_control_panel.set_margin_bottom(5)
        
        # Add background styling for overlay visibility
        self.phase_control_panel.get_style_context().add_class("phase-control-overlay")
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(b"""
            .phase-control-overlay {
                background-color: rgba(255, 255, 255, 0.95);
                border: 1px solid #cccccc;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
            }
        """)
        Gtk.StyleContext.add_provider_for_screen(
            self.phase_control_panel.get_screen(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        
        # Phase controls header
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        phase_header = Gtk.Label("Phase Controls:")
        phase_header.set_markup("<b>Phase Controls:</b>")
        header_box.pack_start(phase_header, False, False, 0)
        
        # Toggle button to show/hide phase controls
        self.phase_toggle = Gtk.ToggleButton("Show Phase Controls")
        self.phase_toggle.connect('toggled', self._on_phase_controls_toggled)
        header_box.pack_end(self.phase_toggle, False, False, 0)
        
        self.phase_control_panel.pack_start(header_box, False, False, 0)
        
        # Scrolled window for phase controls (initially hidden)
        self.phase_scroll = Gtk.ScrolledWindow()
        self.phase_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.phase_scroll.set_size_request(-1, 400)  # Increased height for more vertical space
        self.phase_scroll.set_no_show_all(True)  # Initially hidden
        self.phase_scroll.hide()  # Explicitly hide initially
        
        # Container for phase control widgets
        self.phase_controls_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.phase_scroll.add(self.phase_controls_box)
        
        self.phase_control_panel.pack_start(self.phase_scroll, True, True, 0)
        
        # Store phase control widgets
        self.phase_widgets = {}
    
    def _on_phase_controls_toggled(self, toggle_button):
        """Handle phase controls visibility toggle."""
        try:
            if toggle_button.get_active():
                # Override no_show_all and make visible
                self.phase_scroll.set_no_show_all(False)
                self.phase_scroll.show_all()
                toggle_button.set_label("Hide Phase Controls")
                # Update phase controls if data is loaded
                if hasattr(self, 'voxel_data') and self.voxel_data is not None:
                    self._update_phase_controls()
                    self.logger.info("Phase controls panel opened with data")
                else:
                    # Create placeholder message if no data
                    placeholder = Gtk.Label("Load microstructure data to customize phase colors")
                    placeholder.set_margin_top(10)
                    placeholder.set_margin_bottom(10)
                    self.phase_controls_box.pack_start(placeholder, False, False, 0)
                    placeholder.show()
                    self.logger.info("Phase controls opened (no data loaded yet)")
            else:
                self.phase_scroll.hide()
                self.phase_scroll.set_no_show_all(True)
                toggle_button.set_label("Show Phase Controls")
                self.logger.info("Phase controls panel hidden")
        except Exception as e:
            self.logger.error(f"Failed to toggle phase controls: {e}")
    
    def _update_phase_controls(self):
        """Update phase control widgets based on loaded data."""
        if not hasattr(self, 'voxel_data') or self.voxel_data is None:
            return
        
        # Clear existing controls
        for child in self.phase_controls_box.get_children():
            self.phase_controls_box.remove(child)
        self.phase_widgets.clear()
        
        # Create controls for each phase
        unique_phases = np.unique(self.voxel_data)
        for phase_id in sorted(unique_phases):
            phase_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            
            # Phase name
            phase_name = self.phase_mapping.get(phase_id, f"Phase {phase_id}")
            name_label = Gtk.Label(f"{phase_name}:")
            name_label.set_size_request(120, -1)
            phase_box.pack_start(name_label, False, False, 0)
            
            # Color button
            current_color = self.phase_colors.get(phase_id, '#808080')
            color_button = Gtk.ColorButton()
            rgba = Gdk.RGBA()
            rgba.parse(current_color)
            color_button.set_rgba(rgba)
            color_button.connect('color-set', self._on_phase_color_changed, phase_id)
            phase_box.pack_start(color_button, False, False, 0)
            
            # Visibility checkbox
            visible_check = Gtk.CheckButton("Visible")
            visible_check.set_active(self.show_phase.get(phase_id, True))
            visible_check.connect('toggled', self._on_phase_visibility_changed, phase_id)
            phase_box.pack_start(visible_check, False, False, 0)
            
            # Opacity scale
            opacity_label = Gtk.Label("Opacity:")
            phase_box.pack_start(opacity_label, False, False, 0)
            
            opacity_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0.0, 1.0, 0.1)
            opacity_scale.set_value(self.phase_opacity.get(phase_id, 0.8))
            opacity_scale.set_size_request(100, -1)
            opacity_scale.connect('value-changed', self._on_phase_opacity_changed, phase_id)
            phase_box.pack_start(opacity_scale, False, False, 0)
            
            self.phase_controls_box.pack_start(phase_box, False, False, 0)
            
            # Store widgets
            self.phase_widgets[phase_id] = {
                'color_button': color_button,
                'visible_check': visible_check,
                'opacity_scale': opacity_scale
            }
        
        self.phase_controls_box.show_all()
    
    def _on_phase_color_changed(self, color_button, phase_id):
        """Handle phase color change."""
        rgba = color_button.get_rgba()
        hex_color = f"#{int(rgba.red*255):02x}{int(rgba.green*255):02x}{int(rgba.blue*255):02x}"
        self.set_phase_color(phase_id, hex_color)
        self.logger.info(f"Changed phase {phase_id} color to {hex_color}")
    
    def _on_phase_visibility_changed(self, checkbox, phase_id):
        """Handle phase visibility change."""
        visible = checkbox.get_active()
        self.set_phase_visibility(phase_id, visible)
        self.logger.info(f"Set phase {phase_id} visibility to {visible}")
    
    def _on_phase_opacity_changed(self, scale, phase_id):
        """Handle phase opacity change."""
        opacity = scale.get_value()
        self.set_phase_opacity(phase_id, opacity)
        self.logger.info(f"Set phase {phase_id} opacity to {opacity:.2f}")
    
    def load_voxel_data(self, voxel_data: np.ndarray, phase_mapping: Dict[int, str] = None, 
                       voxel_size: Tuple[float, float, float] = (1.0, 1.0, 1.0)) -> bool:
        """
        Load 3D voxel data for visualization.
        
        Args:
            voxel_data: 3D numpy array with phase IDs
            phase_mapping: Dictionary mapping phase IDs to names
            voxel_size: Size of each voxel in micrometers (x, y, z)
            
        Returns:
            True if data loaded successfully, False otherwise
        """
        try:
            self.voxel_data = voxel_data.copy()
            self.phase_mapping = phase_mapping or {}
            self.voxel_size = voxel_size
            
            # Set volume bounds for cross-section calculations
            shape = voxel_data.shape
            self.volume_bounds = [
                0, shape[0] * voxel_size[0],  # X min, max
                0, shape[1] * voxel_size[1],  # Y min, max  
                0, shape[2] * voxel_size[2]   # Z min, max
            ]
            
            # Initialize phase visibility and opacity
            unique_phases = np.unique(voxel_data)
            for phase_id in unique_phases:
                if phase_id not in self.show_phase:
                    self.show_phase[phase_id] = True
                if phase_id not in self.phase_opacity:
                    self.phase_opacity[phase_id] = 0.8 if phase_id != 0 else 0.1  # Pores more transparent
            
            # Create VTK meshes for each phase
            self._create_phase_meshes()
            
            # Update visualization  
            self._update_visualization()
            
            # Update phase controls if panel is visible
            if hasattr(self, 'phase_toggle') and self.phase_toggle.get_active():
                self._update_phase_controls()
            
            self.emit('data-loaded')
            self.logger.info(f"Loaded voxel data: {voxel_data.shape}, {len(unique_phases)} phases")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load voxel data: {e}")
            return False
    
    def _create_phase_meshes(self):
        """Create VTK mesh objects for each phase."""
        if self.voxel_data is None:
            return
        
        self.mesh_objects = {}
        unique_phases = np.unique(self.voxel_data)
        
        for phase_id in unique_phases:
            try:
                # Create binary mask for this phase
                phase_mask = (self.voxel_data == phase_id).astype(np.uint8)
                
                # Create structured grid
                grid = pv.ImageData(dimensions=phase_mask.shape)
                grid.spacing = self.voxel_size  # Set physical spacing
                grid.point_data['phase'] = phase_mask.flatten(order='F')
                
                # Store mesh object
                self.mesh_objects[phase_id] = grid
                
                self.logger.debug(f"Created mesh for phase {phase_id}: {np.sum(phase_mask)} voxels")
                
            except Exception as e:
                self.logger.error(f"Failed to create mesh for phase {phase_id}: {e}")
    
    def _update_visualization(self):
        """Update the 3D visualization based on current settings."""
        if not hasattr(self, 'plotter') or self.voxel_data is None:
            return
        
        try:
            # Clear existing plots
            self.plotter.clear()
            
            # Add each phase based on rendering mode
            for phase_id, mesh in self.mesh_objects.items():
                if not self.show_phase.get(phase_id, True):
                    continue
                
                color = self.phase_colors.get(phase_id, '#808080')
                opacity = self.phase_opacity.get(phase_id, 0.8)
                phase_name = self.phase_mapping.get(phase_id, f"Phase {phase_id}")
                
                if self.rendering_mode == 'volume':
                    self._add_volume_rendering(mesh, phase_id, color, opacity, phase_name)
                elif self.rendering_mode == 'isosurface':
                    self._add_isosurface_rendering(mesh, phase_id, color, opacity, phase_name)
                elif self.rendering_mode == 'points':
                    self._add_point_rendering(mesh, phase_id, color, phase_name)
                elif self.rendering_mode == 'wireframe':
                    self._add_wireframe_rendering(mesh, phase_id, color, phase_name)
            
            
            # Reset camera if first visualization
            self.plotter.reset_camera()
            
            # Render to image and update GTK widget
            self._render_to_gtk()
            
            self.logger.debug(f"Updated visualization with {len(self.mesh_objects)} phases")
            
        except Exception as e:
            self.logger.error(f"Failed to update visualization: {e}")
    
    def _simple_render_update(self):
        """Simple render update - just take a new screenshot."""
        try:
            self.logger.info("=== Simple render update - taking new screenshot ===")
            
            if not hasattr(self, 'plotter') or self.plotter is None:
                self.logger.warning("No plotter available")
                return
            
            # Take a fresh screenshot with current camera position
            self._render_to_gtk()
            
            self.logger.info("=== Simple render update completed ===")
                
        except Exception as e:
            self.logger.error(f"Simple render update failed: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
    
    def _force_render_update(self):
        """Force immediate render update without regenerating visualization."""
        try:
            self.logger.debug("Forcing render update (camera/view change only)")
            
            # Check if plotter has content to render
            if not hasattr(self, 'plotter') or self.plotter is None:
                self.logger.warning("No plotter available for render update")
                return
                
            # Force plotter to render the current scene with new camera position
            try:
                # Make sure the plotter renders the current state
                self.plotter.render()  # Force internal render
            except Exception as e:
                self.logger.debug(f"Plotter render failed: {e}")
            
            # Render current scene to image
            self._render_to_gtk()
            
            # Force GTK to update display immediately
            if hasattr(self, 'image_widget'):
                self.image_widget.queue_draw()
                # Force immediate GTK update
                while Gtk.events_pending():
                    Gtk.main_iteration()
                    
        except Exception as e:
            self.logger.error(f"Failed to force render update: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
    
    def _render_to_gtk(self):
        """Render PyVista scene to GTK image widget."""
        try:
            self.logger.info(">>> Starting render to GTK")
            
            # Check if we have a valid plotter
            if not hasattr(self, 'plotter') or self.plotter is None:
                self.logger.warning("No plotter available for GTK render")
                return
            
            # Simple screenshot with minimal parameters
            try:
                self.logger.info(">>> Taking screenshot...")
                image_array = self.plotter.screenshot(return_img=True, transparent_background=False)
                self.logger.info(f">>> Screenshot result: {image_array.shape if image_array is not None else 'None'}")
            except Exception as e:
                self.logger.error(f"Screenshot failed: {e}")
                return
            
            if image_array is None or image_array.size == 0:
                self.logger.warning("Empty image array from screenshot")
                return
            
            # Convert to GTK display
            try:
                self.logger.info(">>> Converting to GTK display...")
                # Convert numpy array to PIL Image
                pil_image = PIL.Image.fromarray(image_array)
                
                # Convert PIL image to GdkPixbuf
                buffer = io.BytesIO()
                pil_image.save(buffer, format='PNG')
                buffer.seek(0)
                
                # Load into GdkPixbuf
                loader = GdkPixbuf.PixbufLoader.new()
                loader.write(buffer.getvalue())
                loader.close()
                pixbuf = loader.get_pixbuf()
                
                # Update GTK image widget
                if hasattr(self, 'image_widget') and pixbuf:
                    self.logger.info(">>> Updating GTK image widget...")
                    self.image_widget.set_from_pixbuf(pixbuf)
                    # Force immediate GTK update
                    self.image_widget.queue_draw()
                    while Gtk.events_pending():
                        Gtk.main_iteration_do(False)
                    self.logger.info(">>> GTK image widget updated and display refreshed")
                else:
                    self.logger.warning(f">>> No image widget ({hasattr(self, 'image_widget')}) or pixbuf ({pixbuf is not None if 'pixbuf' in locals() else 'undefined'}) for update")
                    
            except Exception as e:
                self.logger.error(f"GTK update failed: {e}")
                import traceback
                self.logger.error(traceback.format_exc())
                return
                
            if hasattr(self, 'render_status'):
                self.render_status.set_text(f"Rendered: {self.rendering_mode} mode")
            
            self.logger.info(">>> Render to GTK completed successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to render to GTK: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            if hasattr(self, 'render_status'):
                self.render_status.set_text("Render failed")
    
    def _add_volume_rendering(self, mesh, phase_id, color, opacity, name):
        """Add volume rendering for a phase."""
        try:
            # Create contour/isosurface at threshold 0.5
            contour = mesh.contour([0.5], scalars='phase')
            if contour.n_points > 0:
                self.plotter.add_mesh(
                    contour,
                    color=color,
                    opacity=opacity,
                    name=f"phase_{phase_id}",
                    label=name,
                    smooth_shading=True,
                    show_edges=False
                )
        except Exception as e:
            self.logger.warning(f"Volume rendering failed for phase {phase_id}: {e}")
    
    def _add_point_rendering(self, mesh, phase_id, color, name):
        """Add point cloud rendering for a phase."""
        try:
            # Extract points where phase exists
            threshold = mesh.threshold(0.5, scalars='phase')
            if threshold.n_points > 0:
                # Apply cross-sections if enabled
                threshold = self._apply_cross_sections(threshold, phase_id)
                
                if threshold.n_points > 0:  # Check if mesh still has points after cutting
                    self.plotter.add_mesh(
                        threshold,
                        color=color,
                        name=f"phase_{phase_id}",
                        label=name,
                        render_points_as_spheres=True,
                        point_size=2.0
                    )
        except Exception as e:
            self.logger.warning(f"Point rendering failed for phase {phase_id}: {e}")
    
    def _add_wireframe_rendering(self, mesh, phase_id, color, name):
        """Add wireframe rendering for a phase."""
        try:
            contour = mesh.contour([0.5], scalars='phase')
            if contour.n_points > 0:
                # Apply cross-sections if enabled
                contour = self._apply_cross_sections(contour, phase_id)
                
                if contour.n_points > 0:  # Check if mesh still has points after cutting  
                    self.plotter.add_mesh(
                        contour,
                        color=color,
                        name=f"phase_{phase_id}",
                        label=name,
                        style='wireframe',
                        line_width=1.0
                    )
        except Exception as e:
            self.logger.warning(f"Wireframe rendering failed for phase {phase_id}: {e}")
    
    def _add_volume_rendering(self, mesh, phase_id, color, opacity, name):
        """Add volume rendering with enhanced depth and contrast."""
        try:
            contour = mesh.contour([0.5], scalars='phase')
            if contour.n_points > 0:
                # Apply cross-sections if enabled
                contour = self._apply_cross_sections(contour, phase_id)
                
                if contour.n_points > 0:  # Check if mesh still has points after cutting
                    # Enhanced volume rendering for better depth perception
                    self.plotter.add_mesh(
                        contour,
                        color=color,
                        opacity=opacity,
                        name=f"phase_{phase_id}",
                        label=name,
                        smooth_shading=True,
                        show_edges=False,
                        specular=0.8,  # Higher specular for more shine
                        specular_power=30,  # Sharper highlights
                        ambient=0.1,  # Very low ambient for more dramatic shadows
                        diffuse=0.9,   # Higher diffuse for stronger contrast
                        metallic=0.3,  # Add metallic quality
                        roughness=0.2  # Lower roughness for more reflective surface
                    )
        except Exception as e:
            self.logger.warning(f"Volume rendering failed for phase {phase_id}: {e}")
    
    def _add_isosurface_rendering(self, mesh, phase_id, color, opacity, name):
        """Add isosurface rendering with professional quality settings."""
        try:
            contour = mesh.contour([0.5], scalars='phase')
            if contour.n_points > 0:
                # Apply cross-sections if enabled
                contour = self._apply_cross_sections(contour, phase_id)
                
                if contour.n_points > 0:  # Check if mesh still has points after cutting
                    # Professional quality rendering with proper lighting
                    self.plotter.add_mesh(
                        contour,
                        color=color,
                        opacity=opacity,
                        name=f"phase_{phase_id}",
                        label=name,
                        smooth_shading=True,
                        show_edges=True,
                        edge_color='black',
                        line_width=0.3,
                        specular=0.4,
                        ambient=0.3,
                        diffuse=0.7
                    )
        except Exception as e:
            self.logger.warning(f"Isosurface rendering failed for phase {phase_id}: {e}")
    
    def _on_cross_section_toggled(self, axis: str, button: Gtk.CheckButton):
        """Handle cross-section checkbox toggle."""
        try:
            enabled = button.get_active()
            self.cross_section_enabled[axis] = enabled
            
            # Enable/disable the corresponding spin box
            checkbox, spin_box = self.cross_section_controls[axis]
            spin_box.set_sensitive(enabled)
            
            self.logger.info(f"Cross-section {axis.upper()} {'enabled' if enabled else 'disabled'}")
            self._update_visualization()
        except Exception as e:
            self.logger.error(f"Failed to toggle cross-section {axis}: {e}")
    
    def _on_cross_section_position_changed(self, axis: str, spin_box: Gtk.SpinButton):
        """Handle cross-section position spin box change."""
        try:
            self.cross_section_positions[axis] = spin_box.get_value()
            if self.cross_section_enabled[axis]:  # Only update if this axis is enabled
                self.logger.debug(f"Cross-section {axis.upper()} position: {spin_box.get_value():.3f}")
                self._update_visualization()
        except Exception as e:
            self.logger.error(f"Failed to update cross-section {axis} position: {e}")
    
    def _on_reset_cuts_clicked(self, button: Gtk.Button):
        """Reset all cross-sections."""
        try:
            # Disable all cross-sections
            for axis in ['x', 'y', 'z']:
                self.cross_section_enabled[axis] = False
                checkbox, spin_box = self.cross_section_controls[axis]
                checkbox.set_active(False)
                spin_box.set_value(0.5)
                
            self.logger.info("All cross-sections reset")
            self._update_visualization()
        except Exception as e:
            self.logger.error(f"Failed to reset cross-sections: {e}")
    
    def _apply_cross_sections(self, mesh, phase_id: int):
        """Apply cross-section cuts to a mesh."""
        if not any(self.cross_section_enabled.values()) or self.volume_bounds is None:
            return mesh
            
        try:
            # Clean the mesh first to avoid object array issues
            cut_mesh = mesh.clean()
            bounds = self.volume_bounds
            
            # Apply each enabled cutting plane using box clipping instead of plane clipping
            if self.cross_section_enabled['x']:
                # YZ plane cut (normal along X axis) - use box clipping
                x_pos = bounds[0] + (bounds[1] - bounds[0]) * self.cross_section_positions['x']
                # Create a box that keeps everything from x_pos to the end
                box_bounds = [x_pos, bounds[1], bounds[2], bounds[3], bounds[4], bounds[5]]
                cut_mesh = cut_mesh.clip_box(box_bounds, invert=False)
                self.logger.debug(f"X cut at position {x_pos:.1f}")
                
            if self.cross_section_enabled['y']:
                # XZ plane cut (normal along Y axis)  
                y_pos = bounds[2] + (bounds[3] - bounds[2]) * self.cross_section_positions['y']
                # Get current bounds of the mesh (may have changed from X cut)
                current_bounds = cut_mesh.bounds
                box_bounds = [current_bounds[0], current_bounds[1], y_pos, bounds[3], current_bounds[4], current_bounds[5]]
                cut_mesh = cut_mesh.clip_box(box_bounds, invert=False)
                self.logger.debug(f"Y cut at position {y_pos:.1f}")
                
            if self.cross_section_enabled['z']:
                # XY plane cut (normal along Z axis)
                z_pos = bounds[4] + (bounds[5] - bounds[4]) * self.cross_section_positions['z']
                # Get current bounds of the mesh (may have changed from X/Y cuts)
                current_bounds = cut_mesh.bounds
                box_bounds = [current_bounds[0], current_bounds[1], current_bounds[2], current_bounds[3], z_pos, bounds[5]]
                cut_mesh = cut_mesh.clip_box(box_bounds, invert=False)
                self.logger.debug(f"Z cut at position {z_pos:.1f}")
                
            return cut_mesh
            
        except Exception as e:
            self.logger.warning(f"Cross-section failed for phase {phase_id}: {e}")
            return mesh
    
    def _set_camera_view(self, view_type: str):
        """Set camera to predefined view."""
        if not hasattr(self, 'plotter') or self.plotter is None:
            self.logger.warning("Plotter not initialized")
            return
        
        try:
            view_success = False
            
            # Try PyVista built-in view methods first
            try:
                if view_type == 'isometric':
                    self.plotter.view_isometric()
                elif view_type == 'xy':
                    self.plotter.view_xy()
                elif view_type == 'xz':
                    self.plotter.view_xz()
                elif view_type == 'yz':
                    self.plotter.view_yz()
                view_success = True
            except Exception as e:
                self.logger.debug(f"Built-in view method failed: {e}")
            
            # Fallback: manual camera positioning
            if not view_success:
                try:
                    camera = None
                    if hasattr(self.plotter, 'camera') and self.plotter.camera is not None:
                        camera = self.plotter.camera
                    elif len(self.plotter.renderers) > 0:
                        camera = self.plotter.renderers[0].GetActiveCamera()
                    
                    if camera:
                        if view_type == 'isometric':
                            if hasattr(camera, 'azimuth'):
                                camera.azimuth = 45
                                camera.elevation = 20
                            else:
                                camera.SetPosition(1, 1, 1)
                                camera.SetViewUp(0, 0, 1)
                        # Add other view types as needed
                        view_success = True
                except Exception as e:
                    self.logger.debug(f"Manual camera positioning failed: {e}")
            
            if view_success:
                # Force immediate screenshot update
                self._simple_render_update()
                self.emit('view-changed')
                self.logger.info(f"Set camera view: {view_type}")
            else:
                self.logger.warning(f"Failed to set view: {view_type}")
            
        except Exception as e:
            self.logger.error(f"Failed to set camera view {view_type}: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
    
    def _rotate_camera(self, direction: str, angle: float = 15.0):
        """Rotate camera in specified direction."""
        if not hasattr(self, 'plotter') or self.plotter is None:
            self.logger.warning("Plotter not initialized for rotation")
            return
        
        try:
            # Try multiple camera access methods
            camera = None
            if hasattr(self.plotter, 'camera') and self.plotter.camera is not None:
                camera = self.plotter.camera
            elif hasattr(self.plotter, 'renderer') and self.plotter.renderer is not None:
                camera = self.plotter.renderer.GetActiveCamera()
            elif len(self.plotter.renderers) > 0:
                camera = self.plotter.renderers[0].GetActiveCamera()
            
            if camera is None:
                self.logger.warning("Camera not available for rotation")
                return
            
            # Apply rotation based on camera type
            if hasattr(camera, 'azimuth') and hasattr(camera, 'elevation'):
                # PyVista camera
                if direction == 'left':
                    camera.azimuth += angle
                elif direction == 'right':
                    camera.azimuth -= angle  
                elif direction == 'up':
                    camera.elevation += angle
                elif direction == 'down':
                    camera.elevation -= angle
            else:
                # VTK camera - use different methods
                if direction == 'left':
                    camera.Azimuth(angle)
                elif direction == 'right':
                    camera.Azimuth(-angle)
                elif direction == 'up':
                    camera.Elevation(angle)
                elif direction == 'down':
                    camera.Elevation(-angle)
            
            # Force camera update to take effect
            try:
                self.logger.info(f">>> Forcing camera update after {direction} rotation")
                if hasattr(camera, 'Modified'):
                    camera.Modified()  # Mark camera as modified
                    self.logger.info(">>> Camera marked as modified")
                # Update renderer
                for renderer in self.plotter.renderers:
                    if hasattr(renderer, 'ResetCameraClippingRange'):
                        renderer.ResetCameraClippingRange()
                        self.logger.info(">>> Renderer camera clipping range reset")
                # Force plotter to know something changed
                if hasattr(self.plotter, 'render'):
                    self.plotter.render()
                    self.logger.info(">>> Plotter render() called")
            except Exception as e:
                self.logger.warning(f"Camera update failed: {e}")
            
            # Force immediate screenshot update
            self._simple_render_update()
            self.logger.info(f"Rotated camera {direction} by {angle}°")
            
        except Exception as e:
            self.logger.error(f"Failed to rotate camera {direction}: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
    
    def _zoom_camera(self, factor: float):
        """Zoom camera by specified factor."""
        if not hasattr(self, 'plotter') or self.plotter is None:
            self.logger.warning("Plotter not initialized for zoom")
            return
        
        try:
            # Try multiple camera access methods
            camera = None
            if hasattr(self.plotter, 'camera') and self.plotter.camera is not None:
                camera = self.plotter.camera
            elif hasattr(self.plotter, 'renderer') and self.plotter.renderer is not None:
                camera = self.plotter.renderer.GetActiveCamera()
            elif len(self.plotter.renderers) > 0:
                camera = self.plotter.renderers[0].GetActiveCamera()
            
            if camera is None:
                self.logger.warning("Camera not available for zoom")
                return
            
            # Apply zoom
            if hasattr(camera, 'zoom'):
                camera.zoom(factor)
            elif hasattr(camera, 'Zoom'):
                camera.Zoom(factor)
            else:
                self.logger.warning("Camera zoom method not found")
                return
            
            # Force camera update to take effect for zoom
            try:
                self.logger.info(f">>> Forcing camera update after zoom factor {factor}")
                if hasattr(camera, 'Modified'):
                    camera.Modified()  # Mark camera as modified
                    self.logger.info(">>> Camera marked as modified")
                # Update renderer
                for renderer in self.plotter.renderers:
                    if hasattr(renderer, 'ResetCameraClippingRange'):
                        renderer.ResetCameraClippingRange()
                        self.logger.info(">>> Renderer camera clipping range reset")
                # Force plotter to know something changed
                if hasattr(self.plotter, 'render'):
                    self.plotter.render()
                    self.logger.info(">>> Plotter render() called")
            except Exception as e:
                self.logger.warning(f"Camera zoom update failed: {e}")
            
            # Force immediate screenshot update
            self._simple_render_update()
            self.logger.info(f"Zoomed camera by factor {factor}")
            
        except Exception as e:
            self.logger.error(f"Failed to zoom camera: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
    
    # Signal handlers
    def _on_rendering_mode_changed(self, combo):
        """Handle rendering mode change."""
        new_mode = combo.get_active_id()
        if new_mode != self.rendering_mode:
            self.rendering_mode = new_mode
            self._update_visualization()
            self.emit('rendering-mode-changed', new_mode)
            self.logger.info(f"Rendering mode changed to: {new_mode}")
    
    
    def _on_export_clicked(self, button):
        """Handle export button click."""
        dialog = Gtk.FileChooserDialog(
            title="Export 3D View",
            parent=self.get_toplevel(),
            action=Gtk.FileChooserAction.SAVE
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_SAVE, Gtk.ResponseType.OK
        )
        
        # Add file filters
        filter_png = Gtk.FileFilter()
        filter_png.set_name("PNG Images")
        filter_png.add_pattern("*.png")
        dialog.add_filter(filter_png)
        
        filter_jpg = Gtk.FileFilter()
        filter_jpg.set_name("JPEG Images")
        filter_jpg.add_pattern("*.jpg")
        dialog.add_filter(filter_jpg)
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK and hasattr(self, 'plotter'):
            try:
                filename = dialog.get_filename()
                self.plotter.screenshot(filename, transparent_background=True)
                self.logger.info(f"3D view exported to: {filename}")
            except Exception as e:
                self.logger.error(f"Failed to export 3D view: {e}")
        
        dialog.destroy()
    
    # Button click handlers with event isolation
    def _on_rotate_left_clicked(self, button):
        """Handle rotate left button click."""
        try:
            self.logger.info("Rotate left button clicked - starting camera operation")
            self._rotate_camera('left')
            self.logger.info("Rotate left completed")
            return True  # Stop event propagation
        except Exception as e:
            self.logger.error(f"Rotate left failed: {e}")
            return True
    
    def _on_rotate_right_clicked(self, button):
        """Handle rotate right button click."""
        try:
            self.logger.debug("Rotate right button clicked")
            self._rotate_camera('right')
            return True  # Stop event propagation
        except Exception as e:
            self.logger.error(f"Rotate right failed: {e}")
            return True
    
    def _on_rotate_up_clicked(self, button):
        """Handle rotate up button click."""
        try:
            self.logger.debug("Rotate up button clicked")
            self._rotate_camera('up')
            return True  # Stop event propagation
        except Exception as e:
            self.logger.error(f"Rotate up failed: {e}")
            return True
    
    def _on_rotate_down_clicked(self, button):
        """Handle rotate down button click."""
        try:
            self.logger.debug("Rotate down button clicked")
            self._rotate_camera('down')
            return True  # Stop event propagation
        except Exception as e:
            self.logger.error(f"Rotate down failed: {e}")
            return True
    
    def _on_zoom_in_clicked(self, button):
        """Handle zoom in button click."""
        try:
            self.logger.debug("Zoom in button clicked")
            self._zoom_camera(1.25)  # Factor > 1.0 zooms in (makes objects larger)
            return True  # Stop event propagation
        except Exception as e:
            self.logger.error(f"Zoom in failed: {e}")
            return True
    
    def _on_zoom_out_clicked(self, button):
        """Handle zoom out button click."""
        try:
            self.logger.debug("Zoom out button clicked")
            self._zoom_camera(0.8)  # Factor < 1.0 zooms out (makes objects smaller)
            return True  # Stop event propagation
        except Exception as e:
            self.logger.error(f"Zoom out failed: {e}")
            return True
    
    def _on_reset_view_clicked(self, button):
        """Handle reset view button click."""
        try:
            self.logger.info(">>> Reset view button clicked")
            self._on_reset_view(button)
            return True  # Stop event propagation
        except Exception as e:
            self.logger.error(f"Reset view failed: {e}")
            return True
    
    def _on_reset_view(self, button):
        """Handle reset view button."""
        if not hasattr(self, 'plotter') or self.plotter is None:
            self.logger.warning("Plotter not initialized for reset")
            return
            
        try:
            # Comprehensive camera reset to default isometric view
            reset_success = False
            self.logger.info(">>> Attempting complete camera reset (zoom + orientation)...")
            
            # Method 1: Force isometric view reset
            try:
                self.logger.info(">>> Setting isometric view with reset camera")
                # First reset camera to defaults
                if hasattr(self.plotter, 'reset_camera'):
                    self.plotter.reset_camera()
                # Then force isometric orientation
                self.plotter.view_isometric()
                reset_success = True
                self.logger.info(">>> Isometric view reset succeeded")
            except Exception as e:
                self.logger.info(f">>> Isometric reset failed: {e}")
            
            # Method 2: Manual camera positioning reset
            if not reset_success:
                try:
                    self.logger.info(">>> Trying manual camera positioning")
                    camera = None
                    if hasattr(self.plotter, 'camera') and self.plotter.camera is not None:
                        camera = self.plotter.camera
                        self.logger.info(">>> Got camera from plotter.camera")
                    elif len(self.plotter.renderers) > 0:
                        camera = self.plotter.renderers[0].GetActiveCamera()
                        self.logger.info(">>> Got camera from renderer")
                    
                    if camera:
                        # Complete reset: position, orientation, and zoom
                        if hasattr(camera, 'azimuth') and hasattr(camera, 'elevation'):
                            self.logger.info(">>> Resetting PyVista camera position and orientation")
                            camera.azimuth = 45
                            camera.elevation = 20
                            # Reset zoom by setting distance
                            if hasattr(camera, 'distance'):
                                camera.distance = None  # Auto-calculate
                        else:
                            # VTK camera complete reset
                            self.logger.info(">>> Resetting VTK camera position, orientation and zoom")
                            # Reset to default isometric position
                            data_bounds = None
                            if hasattr(self, 'voxel_data') and self.voxel_data is not None:
                                # Calculate appropriate camera distance based on data size
                                shape = self.voxel_data.shape
                                max_dim = max(shape) * max(self.voxel_size)
                                distance = max_dim * 2  # Good viewing distance
                            else:
                                distance = 100  # Default distance
                            
                            camera.SetPosition(distance, distance, distance)
                            camera.SetViewUp(0, 0, 1)
                            camera.SetFocalPoint(0, 0, 0)
                            
                        # Force camera update
                        if hasattr(camera, 'Modified'):
                            camera.Modified()
                        
                        reset_success = True
                        self.logger.info(">>> Manual camera reset succeeded")
                    else:
                        self.logger.warning(">>> No camera found for manual reset")
                except Exception as e:
                    self.logger.info(f">>> Manual camera reset failed: {e}")
            
            # Method 3: Re-initialize view
            if not reset_success:
                try:
                    self.logger.info(">>> Trying view reset to isometric")
                    self._set_camera_view('isometric')
                    reset_success = True
                    self.logger.info(">>> View reset succeeded")
                except Exception as e:
                    self.logger.info(f">>> View reset failed: {e}")
            
            if reset_success:
                # Force immediate screenshot update
                self._simple_render_update()
                self.emit('view-changed')
                self.logger.info("View reset to default")
            else:
                self.logger.warning("All reset methods failed")
                
        except Exception as e:
            self.logger.error(f"Failed to reset view: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
    
    def set_phase_visibility(self, phase_id: int, visible: bool):
        """Set visibility of a specific phase."""
        self.show_phase[phase_id] = visible
        self._update_visualization()
    
    def set_phase_opacity(self, phase_id: int, opacity: float):
        """Set opacity of a specific phase."""
        self.phase_opacity[phase_id] = max(0.0, min(1.0, opacity))
        self._update_visualization()
    
    def set_phase_color(self, phase_id: int, color: str):
        """Set color of a specific phase."""
        self.phase_colors[phase_id] = color
        self._update_visualization()
    
    def get_phase_info(self) -> Dict[int, Dict[str, Any]]:
        """Get information about all phases."""
        if self.voxel_data is None:
            return {}
        
        info = {}
        unique_phases = np.unique(self.voxel_data)
        
        for phase_id in unique_phases:
            voxel_count = np.sum(self.voxel_data == phase_id)
            volume = voxel_count * np.prod(self.voxel_size)  # μm³
            
            info[phase_id] = {
                'name': self.phase_mapping.get(phase_id, f"Phase {phase_id}"),
                'voxel_count': voxel_count,
                'volume_um3': volume,
                'volume_fraction': voxel_count / self.voxel_data.size,
                'color': self.phase_colors.get(phase_id, '#808080'),
                'opacity': self.phase_opacity.get(phase_id, 0.8),
                'visible': self.show_phase.get(phase_id, True)
            }
        
        return info
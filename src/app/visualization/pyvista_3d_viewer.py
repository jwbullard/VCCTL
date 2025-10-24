#!/usr/bin/env python3
"""
VTK-based 3D Microstructure Viewer for VCCTL

High-quality 3D visualization using VTK directly for cross-platform compatibility
with professional lighting, materials, and interaction capabilities.

Note: This was previously PyVista-based but was rewritten to use VTK directly
due to PyVista 0.36.0 initialization bugs on Windows MSYS2 environment.
See Session 10 documentation in CLAUDE.md for details.
"""

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import Gtk, GObject, Gdk, GdkPixbuf, Pango

# Import only the specific VTK modules we need (avoid loading Qt modules)
import numpy as np
try:
    # Import specific VTK modules instead of the whole vtk package
    from vtkmodules.vtkRenderingCore import (
        vtkRenderer, vtkRenderWindow, vtkCamera, vtkActor, vtkPolyDataMapper, vtkLight
    )
    from vtkmodules.vtkRenderingAnnotation import vtkAxesActor
    from vtkmodules.vtkCommonCore import vtkObject, VTK_UNSIGNED_CHAR
    from vtkmodules.vtkCommonDataModel import vtkImageData, vtkDataObject, vtkPlane
    from vtkmodules.vtkFiltersCore import vtkContourFilter, vtkClipPolyData, vtkThreshold, vtkGlyph3D
    from vtkmodules.vtkFiltersGeneral import vtkVertexGlyphFilter
    from vtkmodules.vtkFiltersSources import vtkCubeSource
    from vtkmodules.vtkRenderingCore import vtkWindowToImageFilter
    from vtkmodules.util import numpy_support
    import vtkmodules.vtkInteractionStyle  # Needed for interactor
    import vtkmodules.vtkRenderingOpenGL2  # Needed for OpenGL rendering
    VTK_AVAILABLE = True
except ImportError as e:
    print(f"WARNING: VTK modules import failed: {e}")
    VTK_AVAILABLE = False
from typing import Dict, List, Optional, Any, Tuple, Union
import logging
from pathlib import Path
import io
import PIL.Image

# Configure VTK for better memory management and reduced warnings
if VTK_AVAILABLE:
    vtkObject.SetGlobalWarningDisplay(0)  # Reduce VTK warnings


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
        
        # Camera view tracking
        self.current_view_type = 'isometric'  # Track current camera view
        
        # Measurement system
        self.measurement_mode = None  # 'distance', 'volume', 'connectivity', 'surface_area'
        self.measurement_results = {}  # Store measurement results
        self.measurement_widgets = []  # Active measurement widgets
        self.phase_statistics = {}  # Cached phase statistics
        
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
            11: '#EEAEEE',  # Inert Filler (plum)
            12: '#FFA500',  # Slag (orange)
            13: '#FFC041',  # Aggregate (gold)
            14: '#FFA500',  # ASG (orange)
            15: '#000080',  # CAS2 (navy)
            16: '#1A641A',  # Silica(am) (dark green)
            17: '#404040',  # FA-C3A (dark gray)
            18: '#404040',  # Generic Flyash (dark gray)
            19: '#07488E',  # Portlandite (dark blue)
            20: '#F5DEB3',  # CSH (wheat)
            21: '#969600',  # C3AH6 (olive)
            22: '#7F00FF',  # AFt (violet)
            23: '#7F00FF',  # AFt-Fe (violet)
            24: '#F446CB',  # AFm (orchid)
            25: '#408080',  # FH3 (teal)
            26: '#AEEDDE',  # Pozzolanic CSH (pale turquoise)
            27: '#80FA80',  # Slag CSH (pale green)
            28: '#FFAA80',  # CaCl2 (peach)
            29: '#FF00FF',  # Friedel Salt (magenta)
            30: '#404000',  # Straetlingite (dark olive)
            31: '#FFFF00',  # Secondary Gypsum (yellow)
            32: '#FFFF00',  # Absorbed Gypsum (yellow)
            33: '#00CC00',  # CACO3 (green)
            34: '#FAC6DC',  # AFmc (pink)
            35: '#1A671A',  # Brucite (dark green)
            36: '#80FF00',  # Free lime (lime green)
            37: '#B2B2B2',  # Orth. C3A (light gray)
            55: '#000000',  # Void (black)
            100: '#D3D3D3'  # Legacy aggregate (light gray)
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
        """Create VTK widget using headless rendering."""
        try:
            # Create VTK render window for headless rendering
            self.render_window = vtkRenderWindow()
            self.render_window.SetOffScreenRendering(1)  # Headless rendering
            self.render_window.SetSize(1200, 900)  # Larger viewing window
            self.render_window.SetMultiSamples(0)  # Anti-aliasing

            # Create VTK renderer
            self.renderer = vtkRenderer()
            self.renderer.SetBackground(1.0, 1.0, 1.0)  # White background
            self.render_window.AddRenderer(self.renderer)

            # Enable depth peeling for better transparency rendering
            self.renderer.SetUseDepthPeeling(1)
            self.renderer.SetMaximumNumberOfPeels(10)
            self.renderer.SetOcclusionRatio(0.1)

            # Setup professional 3-point lighting
            self.renderer.RemoveAllLights()  # Clear default lights

            # Key light (main light source)
            key_light = vtkLight()
            key_light.SetPosition(1, 1, 1)
            key_light.SetFocalPoint(0, 0, 0)
            key_light.SetColor(1.0, 1.0, 1.0)
            key_light.SetIntensity(0.8)
            self.renderer.AddLight(key_light)

            # Fill light (softer, from opposite side)
            fill_light = vtkLight()
            fill_light.SetPosition(-1, -1, 1)
            fill_light.SetFocalPoint(0, 0, 0)
            fill_light.SetColor(1.0, 1.0, 1.0)
            fill_light.SetIntensity(0.4)
            self.renderer.AddLight(fill_light)

            # Back light (rim lighting)
            back_light = vtkLight()
            back_light.SetPosition(0, 0, -1)
            back_light.SetFocalPoint(0, 0, 0)
            back_light.SetColor(1.0, 1.0, 1.0)
            back_light.SetIntensity(0.2)
            self.renderer.AddLight(back_light)

            # Create camera
            self.camera = vtkCamera()
            self.renderer.SetActiveCamera(self.camera)

            # Add coordinate axes
            axes = vtkAxesActor()
            axes.SetTotalLength(50, 50, 50)  # Length of axes in voxels
            axes.SetShaftType(0)  # Cylinder shaft
            axes.SetCylinderRadius(0.02)  # Thinner axes
            self.renderer.AddActor(axes)

            # Store reference to window-to-image filter for screenshot capture
            self.window_to_image_filter = vtkWindowToImageFilter()
            self.window_to_image_filter.SetInput(self.render_window)
            self.window_to_image_filter.SetInputBufferTypeToRGB()
            self.window_to_image_filter.ReadFrontBufferOff()  # Read from back buffer

            # Create GTK image widget to display rendered images
            self.image_widget = Gtk.Image()
            # Remove fixed size constraint to allow expansion
            self.image_widget.set_hexpand(True)
            self.image_widget.set_vexpand(True)
            self.image_widget.set_halign(Gtk.Align.CENTER)
            self.image_widget.set_valign(Gtk.Align.CENTER)

            # Enable mouse events for distance measurement
            self.image_widget.add_events(Gdk.EventMask.BUTTON_PRESS_MASK |
                                       Gdk.EventMask.BUTTON_RELEASE_MASK |
                                       Gdk.EventMask.POINTER_MOTION_MASK)
            self.image_widget.set_can_focus(True)

            # Wrap image widget in EventBox to capture mouse events
            self.image_eventbox = Gtk.EventBox()
            self.image_eventbox.add(self.image_widget)
            self.image_eventbox.add_events(Gdk.EventMask.BUTTON_PRESS_MASK |
                                         Gdk.EventMask.BUTTON_RELEASE_MASK |
                                         Gdk.EventMask.POINTER_MOTION_MASK)
            self.image_eventbox.set_can_focus(True)

            # Create scrolled window for the image
            scrolled = Gtk.ScrolledWindow()
            scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
            scrolled.set_hexpand(True)
            scrolled.set_vexpand(True)
            scrolled.add(self.image_eventbox)

            # Create main widget container
            self.plotter_widget = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            self.plotter_widget.pack_start(scrolled, True, True, 0)

            # Add status label
            self.render_status = Gtk.Label("VTK 3D Viewer Ready")
            self.render_status.set_halign(Gtk.Align.CENTER)
            self.plotter_widget.pack_start(self.render_status, False, False, 5)

            self.logger.info("VTK headless renderer created successfully")

        except Exception as e:
            self.logger.error(f"Failed to create VTK widget: {e}")
            # Fallback to placeholder
            self.plotter_widget = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            error_label = Gtk.Label(f"VTK initialization failed:\n{e}")
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
        self.mode_combo.append("points", "Pixel Art")
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
        # Make left/right arrows larger to match up/down arrows
        left_label = rotate_left.get_child()
        left_label.set_markup('<span font="16">◀</span>')
        self.control_panel.pack_start(rotate_left, False, False, 0)

        rotate_right = Gtk.Button("▶")
        rotate_right.set_tooltip_text("Rotate right")
        rotate_right.connect('clicked', self._on_rotate_right_clicked)
        # Make left/right arrows larger to match up/down arrows
        right_label = rotate_right.get_child()
        right_label.set_markup('<span font="16">▶</span>')
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
        
        # Memory cleanup button
        cleanup_button = Gtk.Button("Cleanup Memory")
        cleanup_button.set_tooltip_text("Force aggressive memory cleanup")
        cleanup_button.connect('clicked', self._on_cleanup_memory_clicked)
        self.control_panel.pack_start(cleanup_button, False, False, 0)
        
        # Separator before measurement tools
        separator_measure = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        self.control_panel.pack_start(separator_measure, False, False, 5)
        
        # Measurement tools section (grouped at far right)
        measure_label = Gtk.Label("Measure:")
        self.control_panel.pack_start(measure_label, False, False, 0)
        
        # Distance measurement button (hidden - not working as expected)
        # distance_button = Gtk.Button("Distance")
        # distance_button.set_tooltip_text("Measure distances between points")
        # distance_button.connect('clicked', self._on_distance_measure_clicked)
        # self.control_panel.pack_start(distance_button, False, False, 0)
        
        # Phase data analysis button
        volume_button = Gtk.Button("Phase Data")
        volume_button.set_tooltip_text("Analyze phase volumes, surface areas and statistics") 
        volume_button.connect('clicked', self._on_volume_analyze_clicked)
        self.control_panel.pack_start(volume_button, False, False, 0)
        
        # Connectivity analysis button
        connectivity_button = Gtk.Button("Connectivity")
        connectivity_button.set_tooltip_text("Analyze phase connectivity and percolation")
        connectivity_button.connect('clicked', self._on_connectivity_analyze_clicked)
        self.control_panel.pack_start(connectivity_button, False, False, 0)
    
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
            
            # Opacity spin box
            opacity_label = Gtk.Label("Opacity:")
            phase_box.pack_start(opacity_label, False, False, 0)
            
            # Create adjustment for opacity (0-100% range)
            opacity_adjustment = Gtk.Adjustment(
                value=self.phase_opacity.get(phase_id, 0.8) * 100,  # Convert 0.0-1.0 to 0-100
                lower=0.0,
                upper=100.0,
                step_increment=5.0,
                page_increment=10.0,
                page_size=0.0
            )
            
            opacity_spin = Gtk.SpinButton()
            opacity_spin.set_adjustment(opacity_adjustment)
            opacity_spin.set_digits(0)  # No decimal places
            opacity_spin.set_size_request(80, -1)
            opacity_spin.connect('value-changed', self._on_phase_opacity_changed, phase_id)
            phase_box.pack_start(opacity_spin, False, False, 0)
            
            # Add percentage label with extra spacing
            percent_label = Gtk.Label("%")
            phase_box.pack_start(percent_label, False, False, 10)  # Added 10px right margin
            
            self.phase_controls_box.pack_start(phase_box, False, False, 0)
            
            # Store widgets
            self.phase_widgets[phase_id] = {
                'color_button': color_button,
                'visible_check': visible_check,
                'opacity_spin': opacity_spin
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
    
    def _on_phase_opacity_changed(self, spin_button, phase_id):
        """Handle phase opacity change."""
        opacity_percentage = spin_button.get_value()
        opacity = opacity_percentage / 100.0  # Convert percentage to 0.0-1.0 range
        self.set_phase_opacity(phase_id, opacity)
        self.logger.info(f"Set phase {phase_id} opacity to {opacity:.2f} ({opacity_percentage:.0f}%)")
    
    def load_voxel_data(self, voxel_data: np.ndarray, phase_mapping: Dict[int, str] = None,
                       voxel_size: Tuple[float, float, float] = (1.0, 1.0, 1.0),
                       source_file_path: str = None) -> bool:
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
            # Defensive: Validate input data
            if voxel_data is None:
                self.logger.error("Cannot load voxel data: voxel_data is None")
                return False

            if not isinstance(voxel_data, np.ndarray):
                self.logger.error(f"Cannot load voxel data: expected numpy array, got {type(voxel_data)}")
                return False

            if voxel_data.ndim != 3:
                self.logger.error(f"Cannot load voxel data: expected 3D array, got {voxel_data.ndim}D array")
                return False

            if voxel_data.size == 0:
                self.logger.error("Cannot load voxel data: array is empty")
                return False

            # Defensive: Validate voxel size
            if not voxel_size or len(voxel_size) != 3:
                self.logger.warning(f"Invalid voxel_size {voxel_size}, using default (1.0, 1.0, 1.0)")
                voxel_size = (1.0, 1.0, 1.0)

            if any(v <= 0 for v in voxel_size):
                self.logger.warning(f"Invalid voxel_size values {voxel_size}, using default (1.0, 1.0, 1.0)")
                voxel_size = (1.0, 1.0, 1.0)

            self.logger.info(f"Loading voxel data: shape={voxel_data.shape}, dtype={voxel_data.dtype}, size={voxel_data.nbytes/1024/1024:.2f} MB")

            # Cleanup any existing data first to prevent memory leaks
            if hasattr(self, 'voxel_data') and self.voxel_data is not None:
                self.logger.info("Cleaning up previous voxel data...")
                self._cleanup_previous_data()

            self.voxel_data = voxel_data.copy()
            self.phase_mapping = phase_mapping or {}
            self.voxel_size = voxel_size
            self.source_file_path = source_file_path  # Store source file path for saving results
            
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

        except MemoryError as e:
            self.logger.error(f"Out of memory loading voxel data: {e}", exc_info=True)
            # Try to clean up to free memory
            self._cleanup_previous_data()
            return False
        except Exception as e:
            self.logger.error(f"Failed to load voxel data: {e}", exc_info=True)
            # Try to clean up on failure
            try:
                self._cleanup_previous_data()
            except:
                pass
            return False
    
    def _create_phase_meshes(self):
        """Create VTK mesh objects for each phase."""
        if self.voxel_data is None:
            return

        # Clear existing mesh objects to prevent memory leaks
        if hasattr(self, 'mesh_objects'):
            for mesh in self.mesh_objects.values():
                try:
                    # VTK objects don't have 'clear' method, just delete them
                    del mesh
                except:
                    pass

        self.mesh_objects = {}

        # Force garbage collection to free VTK memory
        import gc
        gc.collect()
        unique_phases = np.unique(self.voxel_data)

        for phase_id in unique_phases:
            try:
                # Create binary mask for this phase
                phase_mask = (self.voxel_data == phase_id).astype(np.uint8)

                # Create VTK ImageData (structured grid)
                grid = vtkImageData()

                # Set dimensions (number of points in each direction)
                grid.SetDimensions(phase_mask.shape[0], phase_mask.shape[1], phase_mask.shape[2])

                # Set spacing (physical size of voxels)
                grid.SetSpacing(self.voxel_size[0], self.voxel_size[1], self.voxel_size[2])

                # Set origin
                grid.SetOrigin(0.0, 0.0, 0.0)

                # Convert numpy array to VTK array
                vtk_data_array = numpy_support.numpy_to_vtk(
                    num_array=phase_mask.flatten(order='C'),  # Flatten in C-order
                    deep=True,  # Make a copy
                    array_type=VTK_UNSIGNED_CHAR
                )
                vtk_data_array.SetName('phase')

                # Add scalar data to grid
                grid.GetPointData().SetScalars(vtk_data_array)

                # Store mesh object
                self.mesh_objects[phase_id] = grid

                self.logger.debug(f"Created mesh for phase {phase_id}: {np.sum(phase_mask)} voxels")

            except Exception as e:
                self.logger.error(f"Failed to create mesh for phase {phase_id}: {e}")
    
    def _update_visualization(self):
        """Update the 3D visualization based on current settings."""
        if not hasattr(self, 'renderer') or self.voxel_data is None:
            return

        try:
            # Clear existing actors from renderer
            self.renderer.RemoveAllViewProps()

            # Force garbage collection to prevent memory leaks
            import gc
            gc.collect()

            # Add coordinate axes for spatial reference
            self._add_coordinate_axes()

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

            # Reset camera to fit all actors
            self.renderer.ResetCamera()

            # Render to image and update GTK widget
            self._render_to_gtk()

            self.logger.debug(f"Updated visualization with {len(self.mesh_objects)} phases")

        except Exception as e:
            self.logger.error(f"Failed to update visualization: {e}")
    
    def _simple_render_update(self):
        """Simple render update - just take a new screenshot."""
        try:
            self.logger.info("=== Simple render update - taking new screenshot ===")
            
            if not hasattr(self, 'plotter') or self.renderer is None:
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
            if not hasattr(self, 'plotter') or self.renderer is None:
                self.logger.warning("No plotter available for render update")
                return
                
            # Force plotter to render the current scene with new camera position
            try:
                # Make sure the plotter renders the current state
                self.renderer.render()  # Force internal render
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
        """Render VTK scene to GTK image widget (optimized for performance)."""
        try:
            # Check if we have a valid render window
            if not hasattr(self, 'render_window') or self.render_window is None:
                return

            # Render the scene
            try:
                self.render_window.Render()

                # Capture screenshot using window-to-image filter
                self.window_to_image_filter.Modified()  # Force update
                self.window_to_image_filter.Update()

                # Get the output image
                vtk_image = self.window_to_image_filter.GetOutput()

                # Get image dimensions
                dims = vtk_image.GetDimensions()
                width, height = dims[0], dims[1]

                # Convert VTK image to numpy array
                vtk_array = vtk_image.GetPointData().GetScalars()
                components = vtk_array.GetNumberOfComponents()
                image_array = numpy_support.vtk_to_numpy(vtk_array)

                # Reshape to image dimensions (height, width, components)
                # VTK stores data bottom-to-top, so flip it
                image_array = image_array.reshape(height, width, components)
                image_array = np.flipud(image_array)  # Flip vertically

            except Exception as e:
                self.logger.error(f"VTK render failed: {e}")
                return

            if image_array is None or image_array.size == 0:
                return

            # Convert to GTK display (optimized: direct numpy to GdkPixbuf)
            try:
                # Create GdkPixbuf directly from numpy array (much faster than PIL→PNG→GdkPixbuf)
                # GdkPixbuf expects RGB data in row-major order
                if components == 3:
                    # Already RGB
                    rgb_data = image_array.tobytes()
                elif components == 4:
                    # RGBA - extract RGB only
                    rgb_data = image_array[:, :, :3].tobytes()
                else:
                    self.logger.warning(f"Unexpected number of components: {components}")
                    return

                # Create pixbuf from raw RGB data
                pixbuf = GdkPixbuf.Pixbuf.new_from_data(
                    rgb_data,
                    GdkPixbuf.Colorspace.RGB,
                    False,  # has_alpha
                    8,  # bits_per_sample
                    width,
                    height,
                    width * 3  # rowstride (bytes per row)
                )

                # Update GTK image widget
                if hasattr(self, 'image_widget') and pixbuf:
                    self.image_widget.set_from_pixbuf(pixbuf)
                    self.image_widget.queue_draw()

                # Clean up
                pixbuf = None

            except Exception as e:
                self.logger.error(f"GTK update failed: {e}")
                return
            finally:
                # Force cleanup of screenshot array
                if 'image_array' in locals():
                    image_array = None
                import gc
                gc.collect()

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
        """Add voxel cube rendering (Minecraft style) using VTK."""
        try:
            # Use threshold filter to extract points where phase exists (value > 0.5)
            threshold = vtkThreshold()
            threshold.SetInputData(mesh)
            threshold.SetInputArrayToProcess(0, 0, 0, vtkDataObject.FIELD_ASSOCIATION_POINTS, 'phase')
            threshold.SetLowerThreshold(0.5)
            threshold.SetUpperThreshold(1.5)  # Allow for values slightly above 1.0
            threshold.Update()

            threshold_output = threshold.GetOutput()

            if threshold_output.GetNumberOfPoints() > 0:
                # Convert to polydata with vertex glyphs
                vertex_filter = vtkVertexGlyphFilter()
                vertex_filter.SetInputData(threshold_output)
                vertex_filter.Update()

                vertices = vertex_filter.GetOutput()

                # Apply cross-section clipping if enabled
                if any(self.cross_section_enabled.values()) and self.volume_bounds is not None:
                    vertices = self._apply_cross_sections_vtk(vertices)

                if vertices.GetNumberOfPoints() > 0:
                    # Create cube source for voxel representation
                    cube_source = vtkCubeSource()

                    # Scale cubes to match voxel size (slightly smaller to show gaps)
                    voxel_scale = min(self.voxel_size) * 0.9  # 90% of voxel size for visual separation
                    cube_source.SetXLength(voxel_scale)
                    cube_source.SetYLength(voxel_scale)
                    cube_source.SetZLength(voxel_scale)

                    # Use Glyph3D to place cubes at each point
                    glyph = vtkGlyph3D()
                    glyph.SetInputData(vertices)
                    glyph.SetSourceConnection(cube_source.GetOutputPort())
                    glyph.SetScaleModeToDataScalingOff()  # Don't scale by data
                    glyph.Update()

                    # Create mapper
                    mapper = vtkPolyDataMapper()
                    mapper.SetInputConnection(glyph.GetOutputPort())
                    mapper.ScalarVisibilityOff()

                    # Create actor
                    actor = vtkActor()
                    actor.SetMapper(mapper)

                    # Convert hex color to RGB (0-1 range)
                    color_str = color.lstrip('#')
                    r = int(color_str[0:2], 16) / 255.0
                    g = int(color_str[2:4], 16) / 255.0
                    b = int(color_str[4:6], 16) / 255.0

                    # Set actor properties - solid cubes
                    property = actor.GetProperty()
                    property.SetColor(r, g, b)
                    property.SetOpacity(1.0)

                    # Optional: Add slight edge visibility for better voxel definition
                    property.EdgeVisibilityOn()
                    property.SetEdgeColor(r * 0.7, g * 0.7, b * 0.7)  # Darker edges
                    property.SetLineWidth(0.5)

                    # Add actor to renderer
                    self.renderer.AddActor(actor)

                    self.logger.debug(f"Added voxel cube rendering for phase {phase_id}: {vertices.GetNumberOfPoints()} cubes")

        except Exception as e:
            self.logger.warning(f"Point rendering failed for phase {phase_id}: {e}")

    def _add_point_rendering_old(self, mesh, phase_id, color, name):
        """OLD PyVista version - Add point cloud rendering for a phase."""
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
        """Add wireframe rendering using VTK."""
        try:
            # Create contour filter to extract isosurface at threshold 0.5
            contour_filter = vtkContourFilter()
            contour_filter.SetInputData(mesh)
            contour_filter.SetValue(0, 0.5)  # Contour at value 0.5
            contour_filter.SetInputArrayToProcess(0, 0, 0, vtkDataObject.FIELD_ASSOCIATION_POINTS, 'phase')
            contour_filter.Update()

            contour = contour_filter.GetOutput()

            # Apply cross-section clipping if enabled
            contour = self._apply_cross_sections_vtk(contour)

            # Check if contour has any points
            if contour.GetNumberOfPoints() > 0:
                # Create mapper
                mapper = vtkPolyDataMapper()
                mapper.SetInputData(contour)
                mapper.ScalarVisibilityOff()  # Use actor color, not scalar data

                # Create actor
                actor = vtkActor()
                actor.SetMapper(mapper)

                # Convert hex color to RGB (0-1 range)
                color_str = color.lstrip('#')
                r = int(color_str[0:2], 16) / 255.0
                g = int(color_str[2:4], 16) / 255.0
                b = int(color_str[4:6], 16) / 255.0

                # Set actor properties - wireframe mode shows only edges
                property = actor.GetProperty()
                property.SetColor(r, g, b)

                # Wireframe-specific: show only wireframe, no surface
                property.SetRepresentationToWireframe()
                property.SetLineWidth(1.0)
                property.SetOpacity(1.0)  # Full opacity for wireframe

                # Add actor to renderer
                self.renderer.AddActor(actor)

                self.logger.debug(f"Added wireframe rendering for phase {phase_id}: {contour.GetNumberOfPoints()} points")

        except Exception as e:
            self.logger.warning(f"Wireframe rendering failed for phase {phase_id}: {e}")

    def _add_wireframe_rendering_old(self, mesh, phase_id, color, name):
        """OLD PyVista version - Add wireframe rendering for a phase."""
        try:
            contour = mesh.contour([0.5], scalars='phase')
            # PyVista 0.36.0 bug workaround: Initialize _textures attribute if missing
            if not hasattr(contour, '_textures'):
                contour._textures = {}
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
        """Add volume rendering with enhanced depth and contrast using VTK."""
        try:
            # Create contour filter to extract isosurface at threshold 0.5
            contour_filter = vtkContourFilter()
            contour_filter.SetInputData(mesh)
            contour_filter.SetValue(0, 0.5)  # Contour at value 0.5
            contour_filter.SetInputArrayToProcess(0, 0, 0, vtkDataObject.FIELD_ASSOCIATION_POINTS, 'phase')
            contour_filter.Update()

            contour = contour_filter.GetOutput()

            # Apply cross-section clipping if enabled
            contour = self._apply_cross_sections_vtk(contour)

            # Check if contour has any points
            if contour.GetNumberOfPoints() > 0:
                # Create mapper
                mapper = vtkPolyDataMapper()
                mapper.SetInputData(contour)
                mapper.ScalarVisibilityOff()  # Use actor color, not scalar data

                # Create actor
                actor = vtkActor()
                actor.SetMapper(mapper)

                # Convert hex color to RGB (0-1 range)
                color_str = color.lstrip('#')
                r = int(color_str[0:2], 16) / 255.0
                g = int(color_str[2:4], 16) / 255.0
                b = int(color_str[4:6], 16) / 255.0

                # Set actor properties
                property = actor.GetProperty()
                property.SetColor(r, g, b)
                property.SetOpacity(opacity)

                # Enable smooth shading
                property.SetInterpolationToPhong()

                # Set lighting parameters for good visibility
                property.SetSpecular(0.5)  # Moderate specular for some shine
                property.SetSpecularPower(20)  # Moderate highlights
                property.SetAmbient(0.2)  # Low ambient for contrast
                property.SetDiffuse(0.8)  # High diffuse for good visibility

                # Add actor to renderer
                self.renderer.AddActor(actor)

                self.logger.debug(f"Added volume rendering for phase {phase_id}: {contour.GetNumberOfPoints()} points")

        except Exception as e:
            self.logger.warning(f"Volume rendering failed for phase {phase_id}: {e}")
    
    def _add_isosurface_rendering(self, mesh, phase_id, color, opacity, name):
        """Add isosurface rendering with edge display using VTK."""
        try:
            # Create contour filter to extract isosurface at threshold 0.5
            contour_filter = vtkContourFilter()
            contour_filter.SetInputData(mesh)
            contour_filter.SetValue(0, 0.5)  # Contour at value 0.5
            contour_filter.SetInputArrayToProcess(0, 0, 0, vtkDataObject.FIELD_ASSOCIATION_POINTS, 'phase')
            contour_filter.Update()

            contour = contour_filter.GetOutput()

            # Apply cross-section clipping if enabled
            contour = self._apply_cross_sections_vtk(contour)

            # Check if contour has any points
            if contour.GetNumberOfPoints() > 0:
                # Create mapper
                mapper = vtkPolyDataMapper()
                mapper.SetInputData(contour)
                mapper.ScalarVisibilityOff()  # Use actor color, not scalar data

                # Create actor
                actor = vtkActor()
                actor.SetMapper(mapper)

                # Convert hex color to RGB (0-1 range)
                color_str = color.lstrip('#')
                r = int(color_str[0:2], 16) / 255.0
                g = int(color_str[2:4], 16) / 255.0
                b = int(color_str[4:6], 16) / 255.0

                # Set actor properties - isosurface mode shows edges
                property = actor.GetProperty()
                property.SetColor(r, g, b)
                property.SetOpacity(opacity)

                # Enable smooth shading
                property.SetInterpolationToPhong()

                # Isosurface-specific: show edges with black lines
                property.EdgeVisibilityOn()
                property.SetEdgeColor(0, 0, 0)  # Black edges
                property.SetLineWidth(0.3)

                # Set lighting parameters for good visibility
                property.SetSpecular(0.4)
                property.SetSpecularPower(20)
                property.SetAmbient(0.3)
                property.SetDiffuse(0.7)

                # Add actor to renderer
                self.renderer.AddActor(actor)

                self.logger.debug(f"Added isosurface rendering for phase {phase_id}: {contour.GetNumberOfPoints()} points")

        except Exception as e:
            self.logger.warning(f"Isosurface rendering failed for phase {phase_id}: {e}")

    def _add_isosurface_rendering_old(self, mesh, phase_id, color, opacity, name):
        """OLD PyVista version - Add isosurface rendering with professional quality settings."""
        try:
            contour = mesh.contour([0.5], scalars='phase')
            # PyVista 0.36.0 bug workaround: Initialize _textures attribute if missing
            if not hasattr(contour, '_textures'):
                contour._textures = {}
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
    
    def _apply_cross_sections_vtk(self, polydata):
        """Apply cross-section cuts to VTK PolyData using clipping planes."""
        if not any(self.cross_section_enabled.values()) or self.volume_bounds is None:
            return polydata

        try:
            clipped = polydata
            bounds = self.volume_bounds

            # Apply each enabled cutting plane
            if self.cross_section_enabled['x']:
                # YZ plane cut (normal along X axis)
                x_pos = bounds[0] + (bounds[1] - bounds[0]) * self.cross_section_positions['x']
                plane = vtkPlane()
                plane.SetOrigin(x_pos, 0, 0)
                plane.SetNormal(1, 0, 0)  # Normal points in +X direction

                clipper = vtkClipPolyData()
                clipper.SetInputData(clipped)
                clipper.SetClipFunction(plane)
                clipper.InsideOutOff()  # Keep the side in the direction of the normal
                clipper.Update()
                clipped = clipper.GetOutput()
                self.logger.debug(f"X cut at position {x_pos:.1f}")

            if self.cross_section_enabled['y']:
                # XZ plane cut (normal along Y axis)
                y_pos = bounds[2] + (bounds[3] - bounds[2]) * self.cross_section_positions['y']
                plane = vtkPlane()
                plane.SetOrigin(0, y_pos, 0)
                plane.SetNormal(0, 1, 0)  # Normal points in +Y direction

                clipper = vtkClipPolyData()
                clipper.SetInputData(clipped)
                clipper.SetClipFunction(plane)
                clipper.InsideOutOff()
                clipper.Update()
                clipped = clipper.GetOutput()
                self.logger.debug(f"Y cut at position {y_pos:.1f}")

            if self.cross_section_enabled['z']:
                # XY plane cut (normal along Z axis)
                z_pos = bounds[4] + (bounds[5] - bounds[4]) * self.cross_section_positions['z']
                plane = vtkPlane()
                plane.SetOrigin(0, 0, z_pos)
                plane.SetNormal(0, 0, 1)  # Normal points in +Z direction

                clipper = vtkClipPolyData()
                clipper.SetInputData(clipped)
                clipper.SetClipFunction(plane)
                clipper.InsideOutOff()
                clipper.Update()
                clipped = clipper.GetOutput()
                self.logger.debug(f"Z cut at position {z_pos:.1f}")

            return clipped

        except Exception as e:
            self.logger.warning(f"VTK cross-section failed: {e}")
            return polydata

    def _apply_cross_sections(self, mesh, phase_id: int):
        """Apply cross-section cuts to a mesh (PyVista version - legacy)."""
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
                # Track current view type
                self.current_view_type = view_type
                
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
    
    def _is_orthographic_view(self):
        """Check if current view is orthographic (XY, XZ, YZ) rather than isometric."""
        return self.current_view_type in ['xy', 'xz', 'yz']
    
    def _project_to_front_surface(self, point, bounds):
        """Project measurement point to the front surface of microstructure in orthographic views."""
        try:
            if not hasattr(self, 'voxel_data') or self.voxel_data is None:
                self.logger.warning("No voxel data available for surface projection")
                return point
            
            projected_point = point.copy()
            
            # Determine which axis to project along based on current view
            if self.current_view_type == 'xy':
                # XY view: looking down Z axis, project to maximum Z (front surface)
                projected_point[2] = bounds[5]  # Max Z bound
                self.logger.info(f"XY view: projecting to front Z surface at {bounds[5]}")
                
            elif self.current_view_type == 'xz':
                # XZ view: looking down Y axis, project to maximum Y (front surface)  
                projected_point[1] = bounds[3]  # Max Y bound
                self.logger.info(f"XZ view: projecting to front Y surface at {bounds[3]}")
                
            elif self.current_view_type == 'yz':
                # YZ view: looking down X axis, project to maximum X (front surface)
                projected_point[0] = bounds[1]  # Max X bound  
                self.logger.info(f"YZ view: projecting to front X surface at {bounds[1]}")
            
            self.logger.info(f"Surface projection: {point} -> {projected_point}")
            return projected_point
            
        except Exception as e:
            self.logger.error(f"Error in surface projection: {e}")
            return point  # Return original point on error
    
    def _rotate_camera(self, direction: str, angle: float = 15.0):
        """Rotate camera in specified direction."""
        # Check for VTK-direct renderer first, then fallback to PyVista plotter
        if hasattr(self, 'renderer') and self.renderer is not None:
            # VTK-direct path
            camera = self.camera
            if direction == 'left':
                camera.Azimuth(angle)
            elif direction == 'right':
                camera.Azimuth(-angle)
            elif direction == 'up':
                camera.Elevation(angle)
            elif direction == 'down':
                camera.Elevation(-angle)

            self.renderer.ResetCameraClippingRange()
            self._render_to_gtk()  # Update display
            self.logger.info(f"Rotated camera {direction} by {angle}°")
            return

        # PyVista plotter fallback (legacy code)
        if not hasattr(self, 'plotter') or self.plotter is None:
            self.logger.warning("Neither renderer nor plotter initialized for rotation")
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
        # Check for VTK-direct renderer first, then fallback to PyVista plotter
        if hasattr(self, 'renderer') and self.renderer is not None:
            # VTK-direct path
            self.camera.Zoom(factor)
            self.renderer.ResetCameraClippingRange()
            self._render_to_gtk()  # Update display
            self.logger.info(f"Zoomed camera by factor {factor}")
            return

        # PyVista plotter fallback (legacy code)
        if not hasattr(self, 'plotter') or self.plotter is None:
            self.logger.warning("Neither renderer nor plotter initialized for zoom")
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
    
    def _add_coordinate_axes(self):
        """Add coordinate axes to the visualization for spatial reference."""
        try:
            # TODO: Add VTK axes widget for spatial reference
            # For minimal prototype, skip coordinate axes
            # Can be added later using vtkAxesActor or vtkCubeAxesActor
            pass
        except Exception as e:
            self.logger.debug(f"Failed to add coordinate axes: {e}")
            
            # Get the bounds of the microstructure data to position axes appropriately
            if hasattr(self, 'voxel_data') and self.voxel_data is not None:
                x_size, y_size, z_size = self.voxel_data.shape
                
                # Position axes outside the microstructure bounds
                # Place axes in lower-left-front corner, outside the volume
                axis_length = min(x_size, y_size, z_size) * 0.2  # 20% of smallest dimension
                
                # Position axes outside the microstructure volume
                axis_origin_x = -axis_length * 0.5  # Offset from left edge
                axis_origin_y = -axis_length * 0.5  # Offset from front edge  
                axis_origin_z = -axis_length * 0.5  # Offset from bottom edge
                
                # Create axes using PyVista's built-in axes actor first
                try:
                    # Method 1: Try to use add_axes with proper positioning
                    if hasattr(self.plotter, 'add_axes'):
                        axes_actor = self.plotter.add_axes(
                            line_width=4,
                            x_color='red',
                            y_color='green',
                            z_color='blue',
                            xlabel='X (μm)',
                            ylabel='Y (μm)', 
                            zlabel='Z (μm)'
                        )
                        self.logger.debug("Added coordinate axes using add_axes")
                        return
                except Exception as e:
                    self.logger.debug(f"add_axes failed: {e}")
                
                # Method 2: Manual axes creation using line plots positioned outside volume
                try:
                    import pyvista as pv
                    import numpy as np
                    
                    # X-axis (red) - from origin to positive X
                    x_start = [axis_origin_x, axis_origin_y, axis_origin_z]
                    x_end = [axis_origin_x + axis_length, axis_origin_y, axis_origin_z]
                    x_line = pv.Line(x_start, x_end)
                    self.plotter.add_mesh(x_line, color='red', line_width=6, name='x_axis')
                    
                    # Y-axis (green) - from origin to positive Y
                    y_start = [axis_origin_x, axis_origin_y, axis_origin_z]
                    y_end = [axis_origin_x, axis_origin_y + axis_length, axis_origin_z] 
                    y_line = pv.Line(y_start, y_end)
                    self.plotter.add_mesh(y_line, color='green', line_width=6, name='y_axis')
                    
                    # Z-axis (blue) - from origin to positive Z
                    z_start = [axis_origin_x, axis_origin_y, axis_origin_z]
                    z_end = [axis_origin_x, axis_origin_y, axis_origin_z + axis_length]
                    z_line = pv.Line(z_start, z_end)
                    self.plotter.add_mesh(z_line, color='blue', line_width=6, name='z_axis')
                    
                    # Add axis labels at the ends of the axes
                    try:
                        # X label (red)
                        self.plotter.add_text('X', 
                                            position=(axis_origin_x + axis_length * 1.2, axis_origin_y, axis_origin_z),
                                            color='red', font_size=14, name='x_label')
                        # Y label (green)
                        self.plotter.add_text('Y', 
                                            position=(axis_origin_x, axis_origin_y + axis_length * 1.2, axis_origin_z),
                                            color='green', font_size=14, name='y_label')
                        # Z label (blue)
                        self.plotter.add_text('Z', 
                                            position=(axis_origin_x, axis_origin_y, axis_origin_z + axis_length * 1.2),
                                            color='blue', font_size=14, name='z_label')
                    except Exception as e:
                        self.logger.debug(f"Adding axis labels failed: {e}")
                    
                    self.logger.debug(f"Added coordinate axes outside microstructure bounds at ({axis_origin_x:.1f}, {axis_origin_y:.1f}, {axis_origin_z:.1f})")
                    
                except Exception as e:
                    self.logger.debug(f"Manual axes creation failed: {e}")
                    
        except Exception as e:
            self.logger.warning(f"Failed to add coordinate axes: {e}")
    
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
    
    def _on_cleanup_memory_clicked(self, button):
        """Handle memory cleanup button click."""
        try:
            self.logger.info("Manual memory cleanup triggered")
            
            # Perform safe cleanup (don't destroy plotter)
            self._clear_measurement_widgets()
            
            # Clear plotter content safely
            if hasattr(self, 'plotter') and self.plotter is not None:
                try:
                    self.plotter.clear()
                except:
                    pass
            
            # Force multiple rounds of garbage collection
            import gc
            for i in range(5):
                collected = gc.collect()
                self.logger.debug(f"GC round {i+1}: collected {collected} objects")
            
            # Re-render current data if available
            if hasattr(self, 'voxel_data') and self.voxel_data is not None:
                self._update_visualization()
            
            self.logger.info("Manual memory cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup memory: {e}")
    
    def _on_reset_view(self, button):
        """Handle reset view button."""
        # Check for VTK-direct renderer first
        if hasattr(self, 'renderer') and self.renderer is not None:
            # VTK-direct path - reset to isometric view
            if hasattr(self, 'voxel_data') and self.voxel_data is not None:
                shape = self.voxel_data.shape
                max_dim = max(shape) * max(self.voxel_size)
                distance = max_dim * 2
            else:
                distance = 200

            self.camera.SetPosition(distance, distance, distance)
            self.camera.SetViewUp(0, 0, 1)
            self.camera.SetFocalPoint(0, 0, 0)
            self.renderer.ResetCamera()
            self._render_to_gtk()
            self.logger.info("View reset to default isometric")
            return

        # PyVista plotter fallback (legacy code)
        if not hasattr(self, 'plotter') or self.plotter is None:
            self.logger.warning("Neither renderer nor plotter initialized for reset")
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
    
    # =========================================================================
    # Measurement and Analysis Methods
    # =========================================================================
    
    def _on_distance_measure_clicked(self, button):
        """Handle distance measurement button click."""
        try:
            self.logger.info("Activating distance measurement tool")
            self._activate_distance_measurement()
        except Exception as e:
            self.logger.error(f"Failed to activate distance measurement: {e}")
    
    def _on_volume_analyze_clicked(self, button):
        """Handle volume and surface area analysis button click."""
        try:
            self.logger.info("Starting volume and surface area analysis")
            self._perform_volume_analysis()
        except Exception as e:
            self.logger.error(f"Failed to perform volume and surface area analysis: {e}")
    
    def _on_connectivity_analyze_clicked(self, button):
        """Handle connectivity analysis button click."""
        import threading
        from gi.repository import GLib

        # Create and show progress dialog
        progress_dialog = Gtk.MessageDialog(
            transient_for=self.get_toplevel(),
            flags=Gtk.DialogFlags.MODAL,
            type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.NONE,
            message_format="Connectivity Analysis in Progress"
        )
        progress_dialog.format_secondary_text(
            "Analyzing phase connectivity and percolation...\n\n"
            "This may take 30-60 seconds for large microstructures.\n"
            "Please wait..."
        )
        progress_dialog.show()

        # Process GTK events to ensure dialog is displayed
        while Gtk.events_pending():
            Gtk.main_iteration()

        def run_analysis():
            """Run connectivity analysis in background thread."""
            try:
                self.logger.info("Starting connectivity analysis")
                self._perform_connectivity_analysis()
                # Close dialog on success
                GLib.idle_add(progress_dialog.destroy)
            except Exception as e:
                self.logger.error(f"Failed to perform connectivity analysis: {e}")
                # Close dialog and show error
                GLib.idle_add(progress_dialog.destroy)
                GLib.idle_add(self._show_connectivity_error, str(e))

        # Run analysis in background thread to prevent UI freeze
        analysis_thread = threading.Thread(target=run_analysis, daemon=True)
        analysis_thread.start()

    def _show_connectivity_error(self, error_message):
        """Show connectivity analysis error dialog."""
        error_dialog = Gtk.MessageDialog(
            transient_for=self.get_toplevel(),
            flags=Gtk.DialogFlags.MODAL,
            type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            message_format="Connectivity Analysis Failed"
        )
        error_dialog.format_secondary_text(
            f"An error occurred during connectivity analysis:\n\n{error_message}"
        )
        error_dialog.run()
        error_dialog.destroy()

    def _activate_distance_measurement(self):
        """Activate interactive distance measurement using point picking."""
        if not hasattr(self, 'plotter') or self.plotter is None:
            self.logger.warning("No plotter available for distance measurement")
            return
        
        try:
            # Clear any existing measurement widgets
            self._clear_measurement_widgets()
            
            # Initialize distance measurement state
            self.distance_points = []
            self.distance_actors = []
            
            # Show instruction dialog
            self._show_distance_instructions()
            
            # Enable point picking for distance measurement
            self._enable_distance_point_picking()
            
        except Exception as e:
            self.logger.error(f"Failed to activate distance measurement: {e}")
    
    def _show_distance_instructions(self):
        """Show instructions for interactive distance measurement."""
        instruction_dialog = Gtk.MessageDialog(
            parent=self.get_toplevel(),
            flags=Gtk.DialogFlags.MODAL,
            type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            message_format="Interactive Distance Measurement"
        )
        
        instruction_text = """Click on two points in the 3D view to measure distance.

Instructions:
1. Click the first point on the microstructure
2. Click the second point on the microstructure
3. The distance will be calculated and displayed

• Left-click to select points
• Right-click to cancel measurement
• ESC key to exit measurement mode"""
        
        instruction_dialog.format_secondary_text(instruction_text)
        instruction_dialog.run()
        instruction_dialog.destroy()
    
    def _enable_distance_point_picking(self):
        """Enable interactive point picking using GTK mouse events."""
        try:
            # Check if image eventbox is available
            if not hasattr(self, 'image_eventbox') or self.image_eventbox is None:
                self.logger.warning("No image eventbox available for distance measurement")
                return
            
            # Check if current view is orthographic (not isometric)
            if not self._is_orthographic_view():
                dialog = Gtk.MessageDialog(
                    parent=None,
                    flags=Gtk.DialogFlags.MODAL,
                    type=Gtk.MessageType.WARNING,
                    buttons=Gtk.ButtonsType.OK,
                    message_format="Distance measurement is only available in orthographic views (XY, XZ, YZ). Please switch to an orthographic view first."
                )
                dialog.run()
                dialog.destroy()
                return
            
            # Initialize distance measurement state
            self.distance_measurement_active = True
            self.distance_points = []
            self.distance_click_count = 0
            
            # Add mouse click event handler to the image eventbox
            self.distance_click_handler_id = self.image_eventbox.connect('button-press-event', self._on_image_clicked_for_distance)
            
            # Change cursor to crosshair to indicate measurement mode
            cursor = Gdk.Cursor.new_for_display(Gdk.Display.get_default(), Gdk.CursorType.CROSSHAIR)
            
            # Set cursor on the eventbox window
            if self.image_eventbox.get_window():
                self.image_eventbox.get_window().set_cursor(cursor)
            
            self.logger.info("Distance measurement mouse clicking enabled")
            
        except Exception as e:
            self.logger.error(f"Failed to enable distance measurement: {e}")
    
    def _on_image_clicked_for_distance(self, widget, event):
        """Handle mouse clicks on the image for distance measurement."""
        try:
            self.logger.info(f"Mouse click detected: button={event.button} at ({event.x}, {event.y})")
            
            if not getattr(self, 'distance_measurement_active', False):
                self.logger.info("Distance measurement not active, ignoring click")
                return False
            
            if event.button != 1:  # Only handle left clicks
                self.logger.info(f"Ignoring non-left click (button {event.button})")
                return False
            
            # Get click coordinates relative to the image widget
            click_x = event.x
            click_y = event.y
            
            # Get image widget allocation to understand scaling
            allocation = widget.get_allocation()
            widget_width = allocation.width
            widget_height = allocation.height
            
            # Get the actual rendered image size from plotter
            plotter_width, plotter_height = self.plotter.window_size
            
            self.logger.info(f"GTK widget click: ({click_x}, {click_y}), widget size: {widget_width}x{widget_height}")
            self.logger.info(f"PyVista plotter size: {plotter_width}x{plotter_height}")
            
            # Calculate aspect ratios
            widget_aspect = widget_width / widget_height if widget_height > 0 else 1.0
            plotter_aspect = plotter_width / plotter_height if plotter_height > 0 else 1.0
            
            self.logger.info(f"Aspect ratios - widget: {widget_aspect:.3f}, plotter: {plotter_aspect:.3f}")
            
            # Convert widget coordinates to normalized coordinates [0,1]
            norm_x = click_x / widget_width if widget_width > 0 else 0.5
            norm_y = click_y / widget_height if widget_height > 0 else 0.5
            
            # Account for aspect ratio differences and image centering
            if widget_aspect > plotter_aspect:
                # Widget is wider than plotter - image is letterboxed horizontally
                image_width_in_widget = widget_height * plotter_aspect
                x_offset = (widget_width - image_width_in_widget) / 2
                if click_x < x_offset or click_x > (widget_width - x_offset):
                    self.logger.warning("Click outside image area (horizontal letterbox)")
                    return False
                norm_x = (click_x - x_offset) / image_width_in_widget
            else:
                # Widget is taller than plotter - image is letterboxed vertically  
                image_height_in_widget = widget_width / plotter_aspect
                y_offset = (widget_height - image_height_in_widget) / 2
                if click_y < y_offset or click_y > (widget_height - y_offset):
                    self.logger.warning("Click outside image area (vertical letterbox)")
                    return False
                norm_y = (click_y - y_offset) / image_height_in_widget
            
            # Convert to plotter coordinates
            plotter_x = norm_x * plotter_width
            plotter_y = (1.0 - norm_y) * plotter_height  # Flip Y coordinate for PyVista
            
            self.logger.info(f"Normalized coords: ({norm_x:.3f}, {norm_y:.3f})")
            self.logger.info(f"Plotter coords: ({plotter_x:.1f}, {plotter_y:.1f})")
            
            # Convert 2D screen coordinates to 3D world coordinates using camera
            world_point = self._screen_to_world_coordinates(plotter_x, plotter_y)
            
            if world_point is not None:
                self._on_distance_point_picked(world_point)
            
            return True  # Event handled
            
        except Exception as e:
            self.logger.error(f"Error handling image click for distance: {e}")
            return False
    
    def _screen_to_world_coordinates(self, screen_x, screen_y):
        """Convert 2D screen coordinates to 3D world coordinates."""
        try:
            self.logger.info(f"Converting screen coords ({screen_x}, {screen_y}) to world coordinates")
            
            # Get dataset bounds
            if not hasattr(self, 'voxel_data') or self.voxel_data is None:
                self.logger.warning("No voxel data available for coordinate conversion")
                return None
            
            # Get plotter bounds
            try:
                bounds = self.plotter.bounds
                if not bounds or len(bounds) < 6:
                    self.logger.warning("No valid bounds available from plotter")
                    return None
            except Exception as e:
                self.logger.warning(f"Could not get plotter bounds: {e}")
                return None
            
            # Normalize screen coordinates to [0, 1] range first, then to [-1, 1]
            width, height = self.plotter.window_size
            norm_x = screen_x / width if width > 0 else 0.5
            norm_y = screen_y / height if height > 0 else 0.5
            
            # Convert to normalized device coordinates [-1, 1]
            ndc_x = (2.0 * norm_x) - 1.0  
            ndc_y = (2.0 * norm_y) - 1.0
            
            self.logger.info(f"Normalized coords: ({ndc_x}, {ndc_y}), bounds: {bounds}")
            
            # Calculate center point and ranges of the dataset
            center_x = (bounds[0] + bounds[1]) / 2
            center_y = (bounds[2] + bounds[3]) / 2  
            center_z = (bounds[4] + bounds[5]) / 2
            
            x_range = bounds[1] - bounds[0]
            y_range = bounds[3] - bounds[2]
            
            # Try ray-casting approach using camera perspective
            try:
                # Get camera parameters using correct PyVista API
                camera = self.plotter.camera
                cam_pos = np.array(camera.position)
                cam_focal = np.array(camera.focal_point)
                
                # Use GetViewUp() method instead of view_up property
                try:
                    if hasattr(camera, 'GetViewUp'):
                        cam_viewup = np.array(camera.GetViewUp())
                    elif hasattr(camera, 'view_up'):
                        cam_viewup = np.array(camera.view_up)
                    else:
                        # Default view up vector
                        cam_viewup = np.array([0, 0, 1])
                        self.logger.warning("Using default view up vector [0,0,1]")
                except Exception as viewup_error:
                    self.logger.warning(f"Could not get view up vector: {viewup_error}")
                    cam_viewup = np.array([0, 0, 1])  # Default
                
                self.logger.info(f"Camera position: {cam_pos}")
                self.logger.info(f"Camera focal point: {cam_focal}")
                
                # Calculate view direction
                view_dir = cam_focal - cam_pos
                view_dir = view_dir / np.linalg.norm(view_dir)
                
                # Calculate right and up vectors for the camera
                right_vec = np.cross(view_dir, cam_viewup)
                right_vec = right_vec / np.linalg.norm(right_vec)
                up_vec = np.cross(right_vec, view_dir)
                up_vec = up_vec / np.linalg.norm(up_vec)
                
                # Scale factor based on dataset size and camera distance
                dataset_diag = np.sqrt((bounds[1] - bounds[0])**2 + 
                                     (bounds[3] - bounds[2])**2 + 
                                     (bounds[5] - bounds[4])**2)
                scale = dataset_diag * 0.3  # Adjust scale for better accuracy
                
                # Calculate world position based on NDC coordinates
                # Project screen coordinates relative to camera focal point
                offset_x = ndc_x * scale * right_vec
                offset_y = ndc_y * scale * up_vec
                
                # Start from camera focal point and add offsets
                world_point = cam_focal + offset_x + offset_y
                
                self.logger.info(f"Ray-cast world point: {world_point}")
                
                # Clamp to dataset bounds
                world_point[0] = np.clip(world_point[0], bounds[0], bounds[1])
                world_point[1] = np.clip(world_point[1], bounds[2], bounds[3])
                world_point[2] = np.clip(world_point[2], bounds[4], bounds[5])
                
                # For orthographic views, project to front surface of microstructure
                if self._is_orthographic_view():
                    world_point = self._project_to_front_surface(world_point, bounds)
                
                self.logger.info(f"Final world point: {world_point}")
                return world_point
                
            except Exception as ray_error:
                self.logger.warning(f"Ray casting failed: {ray_error}")
                
                # Fallback to simple screen mapping with larger scale
                scale_factor = 0.8  # Use 80% of the range from center
                world_x = center_x + (ndc_x * x_range * scale_factor)
                world_y = center_y + (ndc_y * y_range * scale_factor)
                world_z = center_z
                
                world_point = np.array([world_x, world_y, world_z])
                
                # For orthographic views, project to front surface of microstructure
                if self._is_orthographic_view():
                    world_point = self._project_to_front_surface(world_point, bounds)
                
                self.logger.info(f"Final fallback world point: {world_point}")
                return world_point
            
        except Exception as e:
            self.logger.error(f"Error converting screen to world coordinates: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return None
    
    def _on_distance_point_picked(self, point):
        """Handle point picking for distance measurement."""
        try:
            if point is None:
                self.logger.warning("Point is None, cannot add distance point")
                return
            
            self.logger.info(f"Adding distance point {len(self.distance_points) + 1}: {point}")
            
            # Add point to our list
            self.distance_points.append(point)
            self.distance_click_count += 1
            
            # Add visual marker for the point (scale radius based on voxel size)
            voxel_size = self.voxel_size[0] if hasattr(self, 'voxel_size') else 1.0
            sphere_radius = max(voxel_size * 2, 0.5)  # Minimum 0.5μm radius
            
            self.logger.info(f"Creating sphere at {point} with radius {sphere_radius}")
            sphere = pv.Sphere(radius=sphere_radius, center=point)
            color = 'red' if len(self.distance_points) == 1 else 'blue'
            
            try:
                actor = self.plotter.add_mesh(sphere, color=color, opacity=0.8)
                
                if not hasattr(self, 'distance_actors'):
                    self.distance_actors = []
                self.distance_actors.append(actor)
                
                self.logger.info(f"Successfully added {color} sphere for distance point {len(self.distance_points)}")
                
            except Exception as sphere_error:
                self.logger.error(f"Failed to add sphere to plotter: {sphere_error}")
            
            # Update the render to show the new sphere
            try:
                self._render_to_gtk()
                self.logger.info("GTK display updated with new distance marker")
            except Exception as display_error:
                self.logger.error(f"Failed to update GTK display: {display_error}")
            
            # If we have two points, calculate distance
            if len(self.distance_points) == 2:
                self.logger.info("Two points collected, calculating distance")
                self._calculate_and_display_distance()
                self._finish_distance_measurement()
            else:
                self.logger.info(f"Point {len(self.distance_points)} of 2 collected, waiting for second point")
            
        except Exception as e:
            self.logger.error(f"Error handling distance point pick: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
    
    def _calculate_and_display_distance(self):
        """Calculate and display distance between two picked points."""
        try:
            if len(self.distance_points) != 2:
                return
            
            point1, point2 = self.distance_points
            
            # Calculate Euclidean distance in world coordinates
            distance_world = np.linalg.norm(np.array(point2) - np.array(point1))
            
            # Convert to micrometers (world coordinates are already in physical units)
            distance_um = distance_world
            
            # Also convert to voxel coordinates for reference
            voxel_size = self.voxel_size[0] if hasattr(self, 'voxel_size') else 1.0
            distance_voxels = distance_um / voxel_size
            
            # Add line between points with maximum visibility
            line = pv.Line(point1, point2)
            
            # Create a thick tube for maximum visibility
            voxel_size = self.voxel_size[0] if hasattr(self, 'voxel_size') else 1.0
            tube_radius = max(voxel_size * 1.0, 0.8)  # Even thicker tube radius
            tube = line.tube(radius=tube_radius, n_sides=12)  # More sides for smoother appearance
            
            self.logger.info(f"Creating tube with radius {tube_radius} for distance line")
            
            line_actor = self.plotter.add_mesh(
                tube, 
                color='yellow',  # Even brighter color 
                opacity=1.0,     # Fully opaque
                lighting=True,   # Enable lighting for better visibility
                show_edges=False, # No edge lines
                smooth_shading=True
            )
            
            # Set actor priority to render on top
            try:
                if hasattr(line_actor, 'GetProperty'):
                    # Make it render in front of volume
                    line_actor.GetProperty().SetOpacity(1.0)
                    # Enable depth testing but bias toward front
                    if hasattr(line_actor.GetMapper(), 'SetResolveCoincidentTopologyToPolygonOffset'):
                        line_actor.GetMapper().SetResolveCoincidentTopologyToPolygonOffset()
            except Exception as prop_error:
                self.logger.warning(f"Could not set line actor properties: {prop_error}")
            
            # Store the line actor so it can be cleaned up later
            if not hasattr(self, 'distance_actors'):
                self.distance_actors = []
            self.distance_actors.append(line_actor)
            
            self.logger.info(f"Added green line between points: {point1} -> {point2}")
            
            # Update display to show the line
            try:
                self._render_to_gtk()
                self.logger.info("GTK display updated with distance line")
            except Exception as display_error:
                self.logger.error(f"Failed to update GTK display with line: {display_error}")
            
            # Show result
            self._show_interactive_distance_result(point1, point2, distance_voxels, distance_um)
            
        except Exception as e:
            self.logger.error(f"Failed to calculate picked point distance: {e}")
    
    def _finish_distance_measurement(self):
        """Clean up distance measurement mode."""
        try:
            # Disable distance measurement mode
            self.distance_measurement_active = False
            
            # Remove the mouse click event handler
            if hasattr(self, 'distance_click_handler_id') and hasattr(self, 'image_eventbox'):
                try:
                    self.image_eventbox.disconnect(self.distance_click_handler_id)
                    delattr(self, 'distance_click_handler_id')
                except:
                    pass
            
            # Reset cursor to normal
            if hasattr(self, 'image_eventbox') and self.image_eventbox.get_window():
                cursor = Gdk.Cursor.new_for_display(Gdk.Display.get_default(), Gdk.CursorType.ARROW)
                self.image_eventbox.get_window().set_cursor(cursor)
            
            # Reset measurement state (but keep distance_actors for visual feedback)
            self.distance_points = []
            self.distance_click_count = 0
            
            self.logger.info("Distance measurement completed")
            
        except Exception as e:
            self.logger.error(f"Error finishing distance measurement: {e}")
    
    def _show_interactive_distance_result(self, point1, point2, distance_voxels, distance_um):
        """Show interactive distance measurement result."""
        result_dialog = Gtk.MessageDialog(
            parent=self.get_toplevel(),
            flags=Gtk.DialogFlags.MODAL,
            type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            message_format="Distance Measurement Result"
        )
        
        result_text = f"""Point A: ({point1[0]:.1f}, {point1[1]:.1f}, {point1[2]:.1f}) μm
Point B: ({point2[0]:.1f}, {point2[1]:.1f}, {point2[2]:.1f}) μm

Distance: {distance_um:.2f} μm
Distance: {distance_voxels:.1f} voxels

Visual indicators:
• Red sphere: First point
• Blue sphere: Second point  
• Green line: Distance measurement"""
        
        result_dialog.format_secondary_text(result_text)
        result_dialog.run()
        result_dialog.destroy()
        
        self.logger.info(f"Interactive distance measured: {distance_um:.2f} μm ({distance_voxels:.1f} voxels)")
        
    def _show_distance_result(self, ax, ay, az, bx, by, bz, distance_voxels, distance_um):
        """Show distance measurement result (legacy method for manual input)."""
        result_dialog = Gtk.MessageDialog(
            parent=self.get_toplevel(),
            flags=Gtk.DialogFlags.MODAL,
            type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            message_format="Distance Measurement Result"
        )
        
        result_text = f"""Point A: ({ax:.0f}, {ay:.0f}, {az:.0f}) voxels
Point B: ({bx:.0f}, {by:.0f}, {bz:.0f}) voxels

Distance: {distance_voxels:.2f} voxels
Distance: {distance_um:.2f} μm"""
        
        result_dialog.format_secondary_text(result_text)
        result_dialog.run()
        result_dialog.destroy()
        
        self.logger.info(f"Measured distance: {distance_um:.2f} μm ({distance_voxels:.2f} voxels)")
    
    def _perform_volume_analysis(self):
        """Perform comprehensive volume and surface area analysis using C stat3d program."""
        if self.voxel_data is None:
            self.logger.warning("No voxel data available for volume and surface area analysis")
            return
        
        try:
            self.logger.info("=== ATTEMPTING C STAT3D INTEGRATION ===")
            # Use C stat3d program for accurate volume and surface area analysis
            raw_output = self._run_stat3d_analysis_raw()
            self.logger.info(f"stat3d returned {len(raw_output)} characters of output")
            self.logger.info(f"stat3d output preview: {raw_output[:200]}...")
            
            # Display raw output directly (preserves UTF-8 formatting)
            self._show_raw_analysis_results(raw_output, "Volume & Surface Area Analysis Results")
            
            self.logger.info("Volume and surface area analysis completed using C stat3d program")
            
        except Exception as e:
            self.logger.error(f"=== C STAT3D FAILED - FALLING BACK ===")
            self.logger.error(f"Volume and surface area analysis failed: {e}")
            import traceback
            self.logger.error(f"Full traceback: {traceback.format_exc()}")
            # Fallback to Python implementation if C program fails
            try:
                self.logger.info("Falling back to Python implementation...")
                phase_stats = self._calculate_phase_statistics()
                self._show_volume_analysis_results(phase_stats)
            except Exception as fallback_e:
                self.logger.error(f"Python fallback also failed: {fallback_e}")
    
    def _perform_connectivity_analysis(self):
        """Perform connectivity analysis using efficient Python implementation."""
        from gi.repository import GLib

        if self.voxel_data is None:
            self.logger.warning("No voxel data available for connectivity analysis")
            return

        try:
            # Use Python implementation with scipy (more memory-efficient than C version)
            self.logger.info("Using Python connectivity analysis with periodic boundary conditions...")
            connectivity_results = self._python_connectivity_fallback()
            # Use GLib.idle_add for thread-safe UI updates
            GLib.idle_add(self._show_connectivity_analysis_results, connectivity_results)
            self.logger.info("Connectivity analysis completed successfully")

        except ImportError as e:
            self.logger.error(f"scipy not available for connectivity analysis: {e}")
            # Try C perc3d program as fallback
            try:
                self.logger.info("Falling back to C perc3d program...")
                raw_output = self._run_perc3d_analysis_raw()
                # Use GLib.idle_add for thread-safe UI updates
                GLib.idle_add(self._show_raw_analysis_results, raw_output, "Connectivity Analysis Results")
                self.logger.info("Connectivity analysis completed using C perc3d program")
            except Exception as fallback_e:
                self.logger.error(f"C perc3d fallback also failed: {fallback_e}")
                raise  # Re-raise to be caught by outer exception handler
        except Exception as e:
            self.logger.error(f"Connectivity analysis failed: {e}")
            raise  # Re-raise to be caught by button click handler

    def _python_connectivity_fallback(self):
        """Python fallback for connectivity analysis."""
        from scipy import ndimage
        connectivity_results = {}
        unique_phases = np.unique(self.voxel_data)
        
        self.logger.info("Starting connectivity analysis with periodic boundary conditions...")
        
        for phase_id in unique_phases:
            if phase_id == 0:  # Skip porosity for connectivity analysis
                continue
            
            try:
                # Create binary mask for this phase
                phase_mask = (self.voxel_data == phase_id).astype(np.uint8)
                
                # Use memory-efficient periodic connectivity analysis
                labeled_original, num_components = self._periodic_connectivity_analysis(phase_mask)
                
                if num_components == 0:
                    connectivity_results[phase_id] = {
                        'phase_name': self.phase_mapping.get(phase_id, f"Phase {phase_id}"),
                        'total_components': 0,
                        'component_volumes': [],
                        'largest_component_volume': 0,
                        'total_phase_volume': 0,
                        'percolation_ratio': 0,
                        'percolates_x': False,
                        'percolates_y': False,
                        'percolates_z': False,
                        'fully_percolated': False
                    }
                    continue
                
                # Analyze directional percolation for each component
                percolation_results = self._analyze_directional_percolation(
                    labeled_original, num_components, phase_mask.shape
                )
                
                # Calculate volumes
                voxel_volume = np.prod(self.voxel_size)  # μm³ per voxel
                component_volumes = []
                component_voxel_counts = []
                
                for component_id in range(1, num_components + 1):
                    component_voxels = np.sum(labeled_original == component_id)
                    component_volume = component_voxels * voxel_volume
                    component_volumes.append(component_volume)
                    component_voxel_counts.append(component_voxels)
                
                # Sort by volume (largest first)
                sorted_indices = np.argsort(component_volumes)[::-1]
                component_volumes = [component_volumes[i] for i in sorted_indices]
                component_voxel_counts = [component_voxel_counts[i] for i in sorted_indices]
                
                total_phase_volume = sum(component_volumes)
                largest_component_volume = max(component_volumes) if component_volumes else 0
                percolation_ratio = largest_component_volume / total_phase_volume if total_phase_volume > 0 else 0
                
                connectivity_results[phase_id] = {
                    'phase_name': self.phase_mapping.get(phase_id, f"Phase {phase_id}"),
                    'total_components': num_components,
                    'component_volumes': component_volumes,
                    'component_voxel_counts': component_voxel_counts,
                    'largest_component_volume': largest_component_volume,
                    'total_phase_volume': total_phase_volume,
                    'percolation_ratio': percolation_ratio,
                    'percolates_x': percolation_results['percolates_x'],
                    'percolates_y': percolation_results['percolates_y'],
                    'percolates_z': percolation_results['percolates_z'],
                    'fully_percolated': percolation_results['fully_percolated'],
                    'percolating_components': percolation_results['percolating_components']
                }
                
                perc_status = "✓ PERCOLATED" if percolation_results['fully_percolated'] else "✗ Not Percolated"
                self.logger.info(f"Phase {phase_id}: {num_components} components, {perc_status}")
                
            except Exception as e:
                self.logger.error(f"Connectivity analysis failed for phase {phase_id}: {e}")
                connectivity_results[phase_id] = {
                    'phase_name': self.phase_mapping.get(phase_id, f"Phase {phase_id}"),
                    'error': str(e)
                }
        
        return connectivity_results
    
    def _periodic_connectivity_analysis(self, phase_mask):
        """Memory-efficient periodic connectivity analysis using iterative boundary matching."""
        from scipy import ndimage
        
        # Start with standard connectivity analysis on original array
        labeled_array, num_components = ndimage.label(
            phase_mask, 
            structure=ndimage.generate_binary_structure(3, 1)
        )
        
        if num_components <= 1:
            return labeled_array, num_components
        
        # Create component equivalence mapping for periodic boundaries
        nz, ny, nx = phase_mask.shape
        component_map = list(range(num_components + 1))  # component_map[i] = final_component_id
        
        # Check and merge components across X boundaries (left-right)
        self._merge_periodic_boundaries(labeled_array, component_map, 
                                      labeled_array[:, :, 0], labeled_array[:, :, nx-1])
        
        # Check and merge components across Y boundaries (front-back)  
        self._merge_periodic_boundaries(labeled_array, component_map,
                                      labeled_array[:, 0, :], labeled_array[:, ny-1, :])
        
        # Check and merge components across Z boundaries (bottom-top)
        self._merge_periodic_boundaries(labeled_array, component_map,
                                      labeled_array[0, :, :], labeled_array[nz-1, :, :])
        
        # Apply the component mapping to merge connected components (vectorized)
        final_labeled = np.zeros_like(labeled_array)
        unique_components = set()

        # Vectorized approach: create mapping lookup array
        max_component = np.max(labeled_array)
        component_lookup = np.zeros(max_component + 1, dtype=labeled_array.dtype)

        # Build lookup table for component mapping
        for comp_id in range(1, max_component + 1):
            final_comp = self._find_root_component(component_map, comp_id)
            component_lookup[comp_id] = final_comp
            if final_comp > 0:
                unique_components.add(final_comp)

        # Apply mapping using vectorized indexing (much faster than nested loops)
        mask = labeled_array > 0
        final_labeled[mask] = component_lookup[labeled_array[mask]]

        # Renumber components to be sequential (vectorized)
        component_renumber_array = np.zeros(max_component + 1, dtype=labeled_array.dtype)
        for i, comp in enumerate(sorted(unique_components), start=1):
            component_renumber_array[comp] = i

        # Apply renumbering using vectorized indexing
        mask = final_labeled > 0
        final_labeled[mask] = component_renumber_array[final_labeled[mask]]

        final_num_components = len(unique_components)
        self.logger.info(f"Periodic connectivity: {num_components} → {final_num_components} components")
        
        return final_labeled, final_num_components
    
    def _merge_periodic_boundaries(self, labeled_array, component_map, boundary1, boundary2):
        """Merge components that connect across periodic boundaries."""
        # Find all unique component pairs that touch opposite boundaries
        components1 = set(boundary1[boundary1 > 0])
        components2 = set(boundary2[boundary2 > 0]) 
        
        # Check for direct adjacency across boundary
        flat1 = boundary1.flatten()
        flat2 = boundary2.flatten()
        
        for i in range(len(flat1)):
            if flat1[i] > 0 and flat2[i] > 0:
                # These components should be merged
                comp1 = flat1[i]
                comp2 = flat2[i]
                if comp1 != comp2:
                    self._union_components(component_map, comp1, comp2)
    
    def _union_components(self, component_map, comp1, comp2):
        """Union-find operation to merge two components."""
        root1 = self._find_root_component(component_map, comp1)
        root2 = self._find_root_component(component_map, comp2)
        
        if root1 != root2:
            # Always point the higher ID to the lower ID to maintain consistency
            if root1 < root2:
                component_map[root2] = root1
            else:
                component_map[root1] = root2
    
    def _find_root_component(self, component_map, component):
        """Find root component with path compression."""
        if component_map[component] != component:
            component_map[component] = self._find_root_component(component_map, component_map[component])
        return component_map[component]
    
    def _analyze_directional_percolation(self, labeled_array, num_components, shape):
        """Analyze directional percolation for each component with periodic boundaries (optimized)."""
        nz, ny, nx = shape

        percolates_x = False
        percolates_y = False
        percolates_z = False
        percolating_components = []

        # Extract boundary slices once (much faster than creating full component masks)
        left_boundary = labeled_array[:, :, 0]
        right_boundary = labeled_array[:, :, nx-1]
        front_boundary = labeled_array[:, 0, :]
        back_boundary = labeled_array[:, ny-1, :]
        bottom_boundary = labeled_array[0, :, :]
        top_boundary = labeled_array[nz-1, :, :]

        # Find unique components on each boundary (vectorized)
        left_components = set(np.unique(left_boundary[left_boundary > 0]))
        right_components = set(np.unique(right_boundary[right_boundary > 0]))
        front_components = set(np.unique(front_boundary[front_boundary > 0]))
        back_components = set(np.unique(back_boundary[back_boundary > 0]))
        bottom_components = set(np.unique(bottom_boundary[bottom_boundary > 0]))
        top_components = set(np.unique(top_boundary[top_boundary > 0]))

        # Check percolation by set intersection (extremely fast)
        x_percolating = left_components & right_components
        y_percolating = front_components & back_components
        z_percolating = bottom_components & top_components

        # Update global percolation status
        percolates_x = len(x_percolating) > 0
        percolates_y = len(y_percolating) > 0
        percolates_z = len(z_percolating) > 0

        # Build percolating components list (only for components that actually percolate)
        all_percolating = x_percolating | y_percolating | z_percolating
        for component_id in all_percolating:
            x_perc = component_id in x_percolating
            y_perc = component_id in y_percolating
            z_perc = component_id in z_percolating

            percolating_components.append({
                'component_id': int(component_id),
                'x_percolates': x_perc,
                'y_percolates': y_perc,
                'z_percolates': z_perc,
                'fully_percolates': x_perc and y_perc and z_perc
            })

        # Phase is fully percolated if it percolates in ALL three directions
        fully_percolated = percolates_x and percolates_y and percolates_z

        return {
            'percolates_x': percolates_x,
            'percolates_y': percolates_y,
            'percolates_z': percolates_z,
            'fully_percolated': fully_percolated,
            'percolating_components': percolating_components
        }
    
    def _calculate_phase_statistics(self):
        """Calculate comprehensive statistics for all phases including volume and surface area."""
        if self.voxel_data is None:
            return {}
        
        stats = {}
        unique_phases = np.unique(self.voxel_data)
        total_voxels = self.voxel_data.size
        voxel_volume = np.prod(self.voxel_size)  # μm³ per voxel
        voxel_face_area = min(self.voxel_size[0] * self.voxel_size[1],
                             self.voxel_size[0] * self.voxel_size[2],
                             self.voxel_size[1] * self.voxel_size[2])  # μm² per face (smallest face)
        
        self.logger.info("Calculating phase statistics including surface areas...")
        
        for phase_id in unique_phases:
            phase_mask = (self.voxel_data == phase_id)
            voxel_count = np.sum(phase_mask)
            
            # Calculate surface area using interface detection
            surface_area = self._calculate_phase_surface_area(phase_mask, phase_id)
            
            stats[phase_id] = {
                'phase_name': self.phase_mapping.get(phase_id, f"Phase {phase_id}"),
                'voxel_count': int(voxel_count),
                'volume_um3': float(voxel_count * voxel_volume),
                'volume_fraction': float(voxel_count / total_voxels),
                'volume_percentage': float(voxel_count / total_voxels * 100),
                'surface_area_um2': surface_area,
                'specific_surface_area': surface_area / max(voxel_count * voxel_volume, 1e-10),  # μm²/μm³ = μm⁻¹
                'color': self.phase_colors.get(phase_id, '#808080')
            }
            
            self.logger.info(f"Phase {phase_id}: Volume={stats[phase_id]['volume_um3']:.2f} μm³, "
                           f"Surface Area={surface_area:.2f} μm²")
        
        return stats
    
    def _calculate_phase_surface_area(self, phase_mask, phase_id):
        """Calculate surface area of a phase by counting interface voxel faces."""
        try:
            # Calculate voxel face areas
            face_area_xy = self.voxel_size[0] * self.voxel_size[1]  # μm²
            face_area_xz = self.voxel_size[0] * self.voxel_size[2]  # μm²
            face_area_yz = self.voxel_size[1] * self.voxel_size[2]  # μm²
            
            total_surface_area = 0.0
            
            # Get 3D shape
            nz, ny, nx = self.voxel_data.shape
            
            # For each voxel that belongs to this phase, check its 6 neighbors
            # and count exposed faces (interfaces with other phases or boundaries)
            for z in range(nz):
                for y in range(ny):
                    for x in range(nx):
                        if not phase_mask[z, y, x]:
                            continue  # Skip voxels not in this phase
                        
                        # Check 6 neighboring directions and count exposed faces
                        neighbors = [
                            # (dz, dy, dx, face_area)
                            (-1, 0, 0, face_area_xy),  # Top face
                            (1, 0, 0, face_area_xy),   # Bottom face
                            (0, -1, 0, face_area_xz),  # Front face
                            (0, 1, 0, face_area_xz),   # Back face
                            (0, 0, -1, face_area_yz),  # Left face
                            (0, 0, 1, face_area_yz)    # Right face
                        ]
                        
                        for dz, dy, dx, face_area in neighbors:
                            nz_pos, ny_pos, nx_pos = z + dz, y + dy, x + dx
                            
                            # Check if neighbor is outside bounds (boundary) or different phase
                            is_boundary = (nz_pos < 0 or nz_pos >= nz or 
                                         ny_pos < 0 or ny_pos >= ny or 
                                         nx_pos < 0 or nx_pos >= nx)
                            
                            is_different_phase = (not is_boundary and 
                                                self.voxel_data[nz_pos, ny_pos, nx_pos] != phase_id)
                            
                            if is_boundary or is_different_phase:
                                total_surface_area += face_area
            
            self.logger.info(f"Phase {phase_id} surface area calculation: {total_surface_area:.2f} μm²")
            return total_surface_area
            
        except Exception as e:
            self.logger.error(f"Error calculating surface area for phase {phase_id}: {e}")
            return 0.0
    
    def _clear_measurement_widgets(self):
        """Clear all active measurement widgets and prevent memory leaks."""
        try:
            # Clear measurement widgets from plotter
            for widget in self.measurement_widgets:
                try:
                    if hasattr(widget, 'clear'):
                        widget.clear()
                    if hasattr(widget, 'delete'):
                        widget.delete()
                except:
                    pass
            
            self.measurement_widgets.clear()
            self.measurement_mode = None
            
            # Clear distance measurement actors (spheres, lines)
            if hasattr(self, 'distance_actors'):
                for actor in self.distance_actors:
                    try:
                        if hasattr(self, 'plotter') and self.plotter is not None:
                            self.plotter.remove_actor(actor, render=False)
                    except:
                        pass
                self.distance_actors.clear()
            
            # Clear distance measurement state
            if hasattr(self, 'distance_points'):
                self.distance_points.clear()
            
            # Remove measurement text and other actors from plotter
            if hasattr(self, 'plotter') and self.plotter is not None:
                try:
                    # Try to remove measurement text
                    self.plotter.remove_actor('distance_measurement', render=False)
                    # Remove any measurement-related actors
                    self.plotter.remove_actor('measurement_sphere_1', render=False)
                    self.plotter.remove_actor('measurement_sphere_2', render=False)
                    self.plotter.remove_actor('measurement_line', render=False)
                except:
                    pass
            
            # Disable any active picking
            try:
                if hasattr(self, 'plotter') and self.plotter is not None:
                    self.plotter.disable_picking()
            except:
                pass
            
        except Exception as e:
            self.logger.debug(f"Error clearing measurement widgets: {e}")
    
    def cleanup(self):
        """Aggressively clean up PyVista/VTK resources to prevent memory leaks."""
        try:
            self.logger.info("Performing aggressive PyVista cleanup...")
            
            # Clear measurement widgets and actors first
            self._clear_measurement_widgets()
            
            # Clear all plotter content aggressively
            if hasattr(self, 'plotter') and self.plotter is not None:
                try:
                    # Clear all types of widgets that can hold references
                    self.plotter.clear_actors()
                    self.plotter.clear_box_widgets()
                    self.plotter.clear_button_widgets()
                    self.plotter.clear_camera3d_widgets()
                    self.plotter.clear_camera_widgets()
                    self.plotter.clear_line_widgets()
                    self.plotter.clear_logo_widgets()
                    self.plotter.clear_measure_widgets()
                    self.plotter.clear_plane_widgets()
                    self.plotter.clear_radio_button_widgets()
                    self.plotter.clear_slider_widgets()
                    self.plotter.clear_sphere_widgets()
                    self.plotter.clear_spline_widgets()
                    
                    # Clear the main plotter
                    self.plotter.clear()
                    
                    # Close the plotter
                    self.plotter.close()
                    
                    # Explicitly delete the plotter reference
                    del self.plotter
                    self.plotter = None
                    
                except Exception as e:
                    self.logger.warning(f"Error during plotter cleanup: {e}")
            
            # Clear mesh objects with explicit VTK cleanup
            if hasattr(self, 'mesh_objects'):
                for mesh_id, mesh in self.mesh_objects.items():
                    try:
                        # Clear VTK data arrays
                        if hasattr(mesh, 'point_data'):
                            mesh.point_data.clear()
                        if hasattr(mesh, 'cell_data'):
                            mesh.cell_data.clear()
                        if hasattr(mesh, 'field_data'):
                            mesh.field_data.clear()
                        
                        # Delete the mesh
                        del mesh
                        
                    except Exception as e:
                        self.logger.debug(f"Error cleaning mesh {mesh_id}: {e}")
                
                self.mesh_objects.clear()
            
            # Clear voxel data to free numpy arrays
            if hasattr(self, 'voxel_data'):
                try:
                    del self.voxel_data
                    self.voxel_data = None
                except:
                    pass
            
            # Clear phase statistics cache
            if hasattr(self, 'phase_statistics'):
                self.phase_statistics.clear()
            
            # Multiple rounds of garbage collection for VTK objects
            import gc
            for _ in range(3):
                gc.collect()
            
            # Try to trigger VTK garbage collection if available
            try:
                import vtk
                vtkObject.GlobalWarningDisplayOff()  # Reduce VTK warnings
            except:
                pass
            
            self.logger.info("Aggressive PyVista cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during aggressive PyVista cleanup: {e}")
    
    def _destroy_current_plotter(self):
        """Completely destroy current plotter to prevent memory leaks."""
        try:
            if hasattr(self, 'plotter') and self.plotter is not None:
                self.logger.debug("Destroying current plotter...")
                
                # Clear all widgets and actors
                try:
                    self.plotter.clear_actors()
                    self.plotter.clear_box_widgets()
                    self.plotter.clear_button_widgets()
                    self.plotter.clear_camera3d_widgets()
                    self.plotter.clear_camera_widgets()
                    self.plotter.clear_line_widgets()
                    self.plotter.clear_logo_widgets()
                    self.plotter.clear_measure_widgets()
                    self.plotter.clear_plane_widgets()
                    self.plotter.clear_radio_button_widgets()
                    self.plotter.clear_slider_widgets()
                    self.plotter.clear_sphere_widgets()
                    self.plotter.clear_spline_widgets()
                    self.plotter.clear()
                except:
                    pass
                
                # Close and delete plotter
                try:
                    self.plotter.close()
                    del self.plotter
                    self.plotter = None
                except:
                    pass
                
        except Exception as e:
            self.logger.debug(f"Error destroying plotter: {e}")

    def _create_fresh_plotter(self):
        """Create a completely fresh plotter with proper configuration."""
        try:
            self.logger.debug("Creating fresh plotter...")
            
            # Create new headless PyVista plotter
            self.plotter = pv.Plotter(
                off_screen=True,
                window_size=(800, 600),
                notebook=False
            )
            
            # Configure plotter
            self.plotter.background_color = 'white'
            self.plotter.enable_depth_peeling(number_of_peels=10)  # Better transparency

            # Enable anti-aliasing (API changed between PyVista versions)
            try:
                self.plotter.enable_anti_aliasing()  # New API (PyVista >= 0.43.0)
            except TypeError:
                # Fallback for older PyVista versions that require an argument
                self.plotter.enable_anti_aliasing('ssaa')  # Old API (PyVista < 0.43.0)
            
            # Set up professional lighting
            self.plotter.remove_all_lights()  # Clear any default lights
            self.plotter.add_light(pv.Light(position=(1, 1, 1), focal_point=(0, 0, 0), color='white', intensity=0.8))
            self.plotter.add_light(pv.Light(position=(-1, -1, 1), focal_point=(0, 0, 0), color='white', intensity=0.4))
            self.plotter.add_light(pv.Light(position=(0, 0, -1), focal_point=(0, 0, 0), color='white', intensity=0.2))
            
        except Exception as e:
            self.logger.error(f"Failed to create fresh plotter: {e}")
            raise
    
    def _render_current_data(self):
        """Render current data without recreating plotter."""
        if not hasattr(self, 'plotter') or self.plotter is None or self.voxel_data is None:
            return
        
        try:
            # Add coordinate axes for spatial reference
            self._add_coordinate_axes()
            
            # Add each phase based on rendering mode
            for phase_id, mesh in self.mesh_objects.items():
                if not self.show_phase.get(phase_id, True):
                    continue  # Skip hidden phases
                
                opacity = self.phase_opacity.get(phase_id, 1.0)
                color = self.phase_colors.get(phase_id, '#808080')
                
                if self.rendering_mode == 'volume':
                    self._render_volume_phase(mesh, phase_id, color, opacity)
                elif self.rendering_mode == 'isosurface':
                    self._render_isosurface_phase(mesh, phase_id, color, opacity)
                elif self.rendering_mode == 'points':
                    self._render_points_phase(mesh, phase_id, color, opacity)
                elif self.rendering_mode == 'wireframe':
                    self._render_wireframe_phase(mesh, phase_id, color, opacity)
            
            # Update camera if needed
            try:
                self.plotter.reset_camera()
            except:
                pass
            
            # Update render status
            self._update_render_status()
            
        except Exception as e:
            self.logger.error(f"Error rendering current data: {e}")
    
    def _cleanup_previous_data(self):
        """Clean up previous data to prevent memory accumulation."""
        try:
            # Clear measurement state
            self._clear_measurement_widgets()
            
            # Clear mesh objects safely
            if hasattr(self, 'mesh_objects'):
                for mesh in self.mesh_objects.values():
                    try:
                        if hasattr(mesh, 'point_data'):
                            mesh.point_data.clear()
                        if hasattr(mesh, 'cell_data'):
                            mesh.cell_data.clear()
                        del mesh
                    except:
                        pass
                self.mesh_objects.clear()
            
            # Clear plotter content safely (don't destroy plotter)
            if hasattr(self, 'plotter') and self.plotter is not None:
                try:
                    self.plotter.clear()
                except:
                    pass
            
            # Clear cached statistics
            if hasattr(self, 'phase_statistics'):
                self.phase_statistics.clear()
            
            # Clear old voxel data
            if hasattr(self, 'voxel_data'):
                del self.voxel_data
                self.voxel_data = None
            
            # Force garbage collection
            import gc
            gc.collect()
            
        except Exception as e:
            self.logger.debug(f"Error during previous data cleanup: {e}")
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        try:
            self.cleanup()
        except:
            pass
    
    def _show_volume_analysis_results(self, phase_stats):
        """Show volume and surface area analysis results in a dialog."""
        dialog = Gtk.Dialog(
            title="Volume & Surface Area Analysis Results",
            parent=self.get_toplevel(),
            flags=Gtk.DialogFlags.MODAL
        )
        dialog.add_button("Close", Gtk.ResponseType.OK)
        dialog.set_default_size(600, 500)
        
        # Create scrolled window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        # Create text view for results
        text_view = Gtk.TextView()
        text_view.set_editable(False)
        text_view.set_wrap_mode(Gtk.WrapMode.WORD)
        
        # Format results text
        results_text = "MICROSTRUCTURE VOLUME & SURFACE AREA ANALYSIS\n"
        results_text += "=" * 60 + "\n\n"
        
        total_volume = sum(stats['volume_um3'] for stats in phase_stats.values())
        total_surface_area = sum(stats.get('surface_area_um2', 0) for stats in phase_stats.values())
        
        results_text += f"Total Volume: {total_volume:.2f} μm³\n"
        results_text += f"Total Surface Area: {total_surface_area:.2f} μm²\n"
        results_text += f"Total Voxels: {sum(stats['voxel_count'] for stats in phase_stats.values())}\n"
        results_text += f"Voxel Size: {self.voxel_size[0]:.3f} × {self.voxel_size[1]:.3f} × {self.voxel_size[2]:.3f} μm³\n\n"
        
        results_text += "PHASE BREAKDOWN:\n"
        results_text += "-" * 40 + "\n"
        
        for phase_id, stats in sorted(phase_stats.items()):
            results_text += f"\n{stats['phase_name']} (Phase {phase_id}):\n"
            results_text += f"  Volume: {stats['volume_um3']:.2f} μm³\n"
            results_text += f"  Surface Area: {stats.get('surface_area_um2', 0):.2f} μm²\n"
            results_text += f"  Specific Surface Area: {stats.get('specific_surface_area', 0):.3f} μm⁻¹\n"
            results_text += f"  Voxel Count: {stats['voxel_count']:,}\n"
            results_text += f"  Volume Fraction: {stats['volume_fraction']:.4f}\n"
            results_text += f"  Volume Percentage: {stats['volume_percentage']:.2f}%\n"
        
        # Set text content
        text_buffer = text_view.get_buffer()
        text_buffer.set_text(results_text)
        
        scrolled.add(text_view)
        dialog.get_content_area().pack_start(scrolled, True, True, 0)
        
        dialog.show_all()
        dialog.run()
        dialog.destroy()
    
    def _show_connectivity_analysis_results(self, connectivity_results):
        """Show connectivity analysis results in a dialog."""
        dialog = Gtk.Dialog(
            title="Connectivity Analysis Results", 
            parent=self.get_toplevel(),
            flags=Gtk.DialogFlags.MODAL
        )
        dialog.add_button("Close", Gtk.ResponseType.OK)
        dialog.set_default_size(500, 400)
        
        # Create scrolled window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        # Create text view for results
        text_view = Gtk.TextView()
        text_view.set_editable(False)
        text_view.set_wrap_mode(Gtk.WrapMode.WORD)
        
        # Format results text
        results_text = "MICROSTRUCTURE CONNECTIVITY ANALYSIS\n"
        results_text += "=" * 70 + "\n\n"
        results_text += "PERIODIC BOUNDARY CONDITIONS: Enabled\n"
        results_text += "DIRECTIONAL PERCOLATION: Phase must connect all three pairs of opposite boundaries\n"
        results_text += "PERCOLATION CRITERIA: X-direction AND Y-direction AND Z-direction\n\n"
        results_text += "Percolation Ratio: Fraction of phase volume in largest connected component\n"
        results_text += "(Higher values indicate better connectivity within components)\n\n"
        
        for phase_id, results in sorted(connectivity_results.items()):
            if 'error' in results:
                results_text += f"{results['phase_name']} (Phase {phase_id}):\n"
                results_text += f"  Error: {results['error']}\n\n"
                continue
            
            results_text += f"{results['phase_name']} (Phase {phase_id}):\n"
            results_text += f"  Connected Components: {results['total_components']}\n"
            results_text += f"  Total Phase Volume: {results.get('total_phase_volume', 0):.2f} μm³\n"
            results_text += f"  Largest Component Volume: {results['largest_component_volume']:.2f} μm³\n"
            results_text += f"  Percolation Ratio: {results['percolation_ratio']:.3f}\n"
            
            # Add directional percolation information
            if 'fully_percolated' in results:
                results_text += f"\n  DIRECTIONAL PERCOLATION ANALYSIS:\n"
                x_status = "✓" if results.get('percolates_x', False) else "✗"
                y_status = "✓" if results.get('percolates_y', False) else "✗"
                z_status = "✓" if results.get('percolates_z', False) else "✗"
                
                results_text += f"    X-direction (left ↔ right): {x_status}\n"
                results_text += f"    Y-direction (front ↔ back): {y_status}\n"
                results_text += f"    Z-direction (bottom ↔ top): {z_status}\n"
                
                if results.get('fully_percolated', False):
                    results_text += f"    OVERALL STATUS: ✓ PERCOLATED (connects all boundaries)\n"
                else:
                    results_text += f"    OVERALL STATUS: ✗ NOT PERCOLATED (missing connections)\n"
            
            # Interpret percolation ratio
            perc_ratio = results['percolation_ratio']
            if perc_ratio > 0.8:
                interp = "(Excellent component connectivity)"
            elif perc_ratio > 0.5:
                interp = "(Good component connectivity)"
            elif perc_ratio > 0.2:
                interp = "(Moderate component connectivity)"
            else:
                interp = "(Poor component connectivity/fragmented)"
            results_text += f"\n  Component Analysis: {interp}\n"
            
            if results['total_components'] <= 10:
                results_text += "  Component Volumes (largest first):\n"
                for i, (vol, voxels) in enumerate(zip(results['component_volumes'], results.get('component_voxel_counts', []))):
                    results_text += f"    Component {i+1}: {vol:.2f} μm³ ({voxels} voxels)\n"
            else:
                results_text += f"  Top 5 Components (of {results['total_components']} total):\n"
                for i in range(min(5, len(results['component_volumes']))):
                    vol = results['component_volumes'][i]
                    voxels = results.get('component_voxel_counts', [0])[i] if i < len(results.get('component_voxel_counts', [])) else 0
                    results_text += f"    Component {i+1}: {vol:.2f} μm³ ({voxels} voxels)\n"
            
            results_text += "\n"
        
        # Set text content
        text_buffer = text_view.get_buffer()
        text_buffer.set_text(results_text)
        
        scrolled.add(text_view)
        dialog.get_content_area().pack_start(scrolled, True, True, 0)
        
        dialog.show_all()
        dialog.run()
        dialog.destroy()

    def _show_raw_analysis_results(self, raw_output, title):
        """Show raw C program output directly in a dialog."""
        dialog = Gtk.Dialog(
            title=title,
            parent=self.get_toplevel(),
            flags=Gtk.DialogFlags.MODAL
        )
        dialog.add_button("Close", Gtk.ResponseType.OK)
        dialog.set_default_size(700, 600)
        
        # Create scrolled window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        # Create text view for results
        text_view = Gtk.TextView()
        text_view.set_editable(False)
        text_view.set_wrap_mode(Gtk.WrapMode.WORD)
        
        # Use monospace font to preserve formatting
        font_desc = Pango.FontDescription.from_string("monospace 11")
        text_view.modify_font(font_desc)
        
        # Set raw output content
        text_buffer = text_view.get_buffer()
        text_buffer.set_text(raw_output)
        
        scrolled.add(text_view)
        dialog.get_content_area().pack_start(scrolled, True, True, 0)
        
        dialog.show_all()
        dialog.run()
        dialog.destroy()

    def _run_stat3d_analysis_raw(self):
        """Run the C stat3d program and return raw output."""
        import subprocess
        import tempfile
        import os
        import sys

        # Create temporary input file and permanent output file in source directory
        temp_input = tempfile.NamedTemporaryFile(mode='w', suffix='.img', delete=False)
        temp_input.close()
        
        # Create output file in same directory as source microstructure file
        if self.source_file_path:
            base_name = os.path.splitext(self.source_file_path)[0]
            output_file = f"{base_name}_PhaseData.txt"
        else:
            # Fallback to temporary file if no source path
            temp_output = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
            temp_output.close()
            output_file = temp_output.name
        
        try:
            # Write voxel data in VCCTL format
            with open(temp_input.name, 'w') as f:
                # Write proper VCCTL header format
                f.write("Version: 7.0\n")
                f.write(f"X_Size: {self.voxel_data.shape[0]}\n")
                f.write(f"Y_Size: {self.voxel_data.shape[1]}\n")
                f.write(f"Z_Size: {self.voxel_data.shape[2]}\n")
                # Use first element of voxel_size tuple for VCCTL resolution
                resolution = self.voxel_size[0] if isinstance(self.voxel_size, (tuple, list)) else self.voxel_size
                f.write(f"Image_Resolution: {resolution:.2f}\n")
                
                # Write voxel data
                for z in range(self.voxel_data.shape[2]):
                    for y in range(self.voxel_data.shape[1]):
                        for x in range(self.voxel_data.shape[0]):
                            f.write(f"{int(self.voxel_data[x, y, z])}\n")
            
            # Get path to stat3d executable - use absolute path from project root
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

            # Platform-specific executable name
            stat3d_exe = 'stat3d.exe' if sys.platform == 'win32' else 'stat3d'
            stat3d_path = os.path.join(project_root, 'backend', 'bin', stat3d_exe)

            # Run stat3d program with input and output files
            cmd = [stat3d_path, temp_input.name, output_file]
            self.logger.info(f"Executing: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                self.logger.error(f"stat3d execution details:")
                self.logger.error(f"  Command: {' '.join(cmd)}")
                self.logger.error(f"  Input file: {temp_input.name} (exists: {os.path.exists(temp_input.name)})")
                self.logger.error(f"  Output file: {output_file} (exists: {os.path.exists(output_file)})")
                self.logger.error(f"  Return code: {result.returncode}")
                self.logger.error(f"  stdout: {result.stdout}")
                self.logger.error(f"  stderr: {result.stderr}")
                raise RuntimeError(f"stat3d failed with return code {result.returncode}: {result.stderr}")
            
            # Read the output file with UTF-8 encoding
            if not os.path.exists(output_file):
                raise RuntimeError(f"stat3d completed but output file not found: {output_file}")
                
            with open(output_file, 'r', encoding='utf-8', errors='replace') as f:
                raw_output = f.read()
            
            self.logger.info(f"Read {len(raw_output)} characters from output file")
            return raw_output
            
        finally:
            # Clean up temporary input file only (keep permanent output file)
            try:
                os.unlink(temp_input.name)
                # Only delete output file if it's a temporary file
                if not self.source_file_path and 'temp_output' in locals():
                    os.unlink(output_file)
            except:
                pass

    def _run_perc3d_analysis_raw(self):
        """Run the C perc3d program and return raw output."""
        import subprocess
        import tempfile
        import os
        import sys

        # Create temporary input file and permanent output file in source directory
        temp_input = tempfile.NamedTemporaryFile(mode='w', suffix='.img', delete=False)
        temp_input.close()
        
        # Create output file in same directory as source microstructure file
        if self.source_file_path:
            base_name = os.path.splitext(self.source_file_path)[0]
            output_file = f"{base_name}_Connectivity.txt"
        else:
            # Fallback to temporary file if no source path
            temp_output = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
            temp_output.close()
            output_file = temp_output.name
        
        try:
            # Write voxel data in VCCTL format
            with open(temp_input.name, 'w') as f:
                # Write proper VCCTL header format
                f.write("Version: 7.0\n")
                f.write(f"X_Size: {self.voxel_data.shape[0]}\n")
                f.write(f"Y_Size: {self.voxel_data.shape[1]}\n")
                f.write(f"Z_Size: {self.voxel_data.shape[2]}\n")
                # Use first element of voxel_size tuple for VCCTL resolution
                resolution = self.voxel_size[0] if isinstance(self.voxel_size, (tuple, list)) else self.voxel_size
                f.write(f"Image_Resolution: {resolution:.2f}\n")
                
                # Write voxel data
                for z in range(self.voxel_data.shape[2]):
                    for y in range(self.voxel_data.shape[1]):
                        for x in range(self.voxel_data.shape[0]):
                            f.write(f"{int(self.voxel_data[x, y, z])}\n")
            
            # Get path to perc3d executable
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

            # Platform-specific executable name
            perc3d_exe = 'perc3d.exe' if sys.platform == 'win32' else 'perc3d'
            perc3d_path = os.path.join(project_root, 'backend', 'bin', perc3d_exe)

            # Run perc3d program with command line arguments
            cmd = [perc3d_path, temp_input.name, output_file]
            self.logger.info(f"Executing: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                self.logger.error(f"perc3d execution details:")
                self.logger.error(f"  Command: {' '.join(cmd)}")
                self.logger.error(f"  Input file: {temp_input.name} (exists: {os.path.exists(temp_input.name)})")
                self.logger.error(f"  Output file: {output_file} (exists: {os.path.exists(output_file)})")
                self.logger.error(f"  Return code: {result.returncode}")
                self.logger.error(f"  stdout: {result.stdout}")
                self.logger.error(f"  stderr: {result.stderr}")
                raise RuntimeError(f"perc3d failed with return code {result.returncode}: {result.stderr}")
            
            # Read the output file with UTF-8 encoding
            if not os.path.exists(output_file):
                raise RuntimeError(f"perc3d completed but output file not found: {output_file}")
                
            with open(output_file, 'r', encoding='utf-8', errors='replace') as f:
                raw_output = f.read()
            
            self.logger.info(f"Read {len(raw_output)} characters from perc3d output file")
            return raw_output
            
        finally:
            # Clean up temporary input file only (keep permanent output file)
            try:
                os.unlink(temp_input.name)
                # Only delete output file if it's a temporary file
                if not self.source_file_path and 'temp_output' in locals():
                    os.unlink(output_file)
            except:
                pass

    def _run_stat3d_analysis(self):
        """Run the C stat3d program for volume and surface area analysis."""
        import subprocess
        import tempfile
        import os
        import sys
        import re


        # Create temporary input and output files
        temp_input = tempfile.NamedTemporaryFile(mode='w', suffix='.img', delete=False)
        temp_output = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
        temp_input.close()
        temp_output.close()
        
        try:
            # Write voxel data in VCCTL format
            with open(temp_input.name, 'w') as f:
                # Write proper VCCTL header format
                f.write("Version: 7.0\n")
                f.write(f"X_Size: {self.voxel_data.shape[0]}\n")
                f.write(f"Y_Size: {self.voxel_data.shape[1]}\n")
                f.write(f"Z_Size: {self.voxel_data.shape[2]}\n")
                # Use first element of voxel_size tuple for VCCTL resolution
                resolution = self.voxel_size[0] if isinstance(self.voxel_size, (tuple, list)) else self.voxel_size
                f.write(f"Image_Resolution: {resolution:.2f}\n")
                
                # Write voxel data
                for z in range(self.voxel_data.shape[2]):
                    for y in range(self.voxel_data.shape[1]):
                        for x in range(self.voxel_data.shape[0]):
                            f.write(f"{int(self.voxel_data[x, y, z])}\n")
            
            # Get path to stat3d executable - use absolute path from project root
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

            # Platform-specific executable name
            stat3d_exe = 'stat3d.exe' if sys.platform == 'win32' else 'stat3d'
            stat3d_path = os.path.join(project_root, 'backend', 'bin', stat3d_exe)

            # Run stat3d program with command line arguments
            cmd = [stat3d_path, temp_input.name]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                raise RuntimeError(f"stat3d failed with return code {result.returncode}: {result.stderr}")
            
            # Return raw stdout output
            return result.stdout
            
        finally:
            # Clean up temporary files
            try:
                os.unlink(temp_input.name)
                os.unlink(temp_output.name)
            except:
                pass

    def _parse_stat3d_output(self, output_file):
        """Parse stat3d output file and return phase statistics."""
        phase_stats = {}
        
        try:
            # Explicitly use UTF-8 encoding for cross-platform compatibility
            with open(output_file, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            # Parse phase data using regex patterns
            phase_pattern = r'Phase\s+(\d+):\s*Volume:\s*([\d.]+)\s*Surface\s*Area:\s*([\d.]+)'
            matches = re.findall(phase_pattern, content)
            
            for match in matches:
                phase_id = int(match[0])
                volume = float(match[1])
                surface_area = float(match[2])
                
                phase_name = self.phase_mapping.get(phase_id, f"Phase {phase_id}")
                
                phase_stats[phase_id] = {
                    'phase_name': phase_name,
                    'volume_um3': volume,
                    'surface_area_um2': surface_area,
                    'voxel_count': int(volume / (self.voxel_size ** 3))
                }
        
        except Exception as e:
            self.logger.error(f"Failed to parse stat3d output: {e}")
            raise
        
        return phase_stats

    def _run_perc3d_analysis(self):
        """Run the C perc3d program for connectivity analysis."""
        import subprocess
        import tempfile
        import os
        import sys

        # Create temporary input and output files
        temp_input = tempfile.NamedTemporaryFile(mode='w', suffix='.img', delete=False)
        temp_output = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
        temp_input.close()
        temp_output.close()
        
        try:
            # Write voxel data in VCCTL format
            with open(temp_input.name, 'w') as f:
                # Write proper VCCTL header format
                f.write("Version: 7.0\n")
                f.write(f"X_Size: {self.voxel_data.shape[0]}\n")
                f.write(f"Y_Size: {self.voxel_data.shape[1]}\n")
                f.write(f"Z_Size: {self.voxel_data.shape[2]}\n")
                # Use first element of voxel_size tuple for VCCTL resolution
                resolution = self.voxel_size[0] if isinstance(self.voxel_size, (tuple, list)) else self.voxel_size
                f.write(f"Image_Resolution: {resolution:.2f}\n")
                
                # Write voxel data
                for z in range(self.voxel_data.shape[2]):
                    for y in range(self.voxel_data.shape[1]):
                        for x in range(self.voxel_data.shape[0]):
                            f.write(f"{int(self.voxel_data[x, y, z])}\n")
            
            # Get path to perc3d executable
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

            # Platform-specific executable name
            perc3d_exe = 'perc3d.exe' if sys.platform == 'win32' else 'perc3d'
            perc3d_path = os.path.join(project_root, 'backend', 'bin', perc3d_exe)

            # Run perc3d program with command line arguments
            cmd = [perc3d_path, temp_input.name]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                raise RuntimeError(f"perc3d failed with return code {result.returncode}: {result.stderr}")
            
            # Return raw stdout output
            return result.stdout
            
        finally:
            # Clean up temporary files
            try:
                os.unlink(temp_input.name)
                os.unlink(temp_output.name)
            except:
                pass

    def _parse_perc3d_output(self, output_file):
        """Parse perc3d output file and return connectivity results."""
        import re
        connectivity_results = {}
        
        try:
            # Explicitly use UTF-8 encoding for cross-platform compatibility
            with open(output_file, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            # Parse connectivity data for each phase
            phase_sections = re.split(r'Phase\s+(\d+):', content)[1:]  # Skip header
            
            for i in range(0, len(phase_sections), 2):
                if i + 1 >= len(phase_sections):
                    break
                    
                phase_id = int(phase_sections[i])
                phase_data = phase_sections[i + 1]
                
                # Extract connectivity metrics
                components_match = re.search(r'Components:\s*(\d+)', phase_data)
                percolation_match = re.search(r'Percolation:\s*(\w+)', phase_data)
                x_perc_match = re.search(r'X-direction:\s*(\w+)', phase_data)
                y_perc_match = re.search(r'Y-direction:\s*(\w+)', phase_data)
                z_perc_match = re.search(r'Z-direction:\s*(\w+)', phase_data)
                
                phase_name = self.phase_mapping.get(phase_id, f"Phase {phase_id}")
                
                connectivity_results[phase_id] = {
                    'phase_name': phase_name,
                    'total_components': int(components_match.group(1)) if components_match else 0,
                    'fully_percolated': percolation_match.group(1).lower() == 'yes' if percolation_match else False,
                    'percolates_x': x_perc_match.group(1).lower() == 'yes' if x_perc_match else False,
                    'percolates_y': y_perc_match.group(1).lower() == 'yes' if y_perc_match else False,
                    'percolates_z': z_perc_match.group(1).lower() == 'yes' if z_perc_match else False,
                    'percolation_ratio': 0.0,  # Will be calculated from components
                    'component_volumes': [],
                    'component_voxel_counts': []
                }
        
        except Exception as e:
            self.logger.error(f"Failed to parse perc3d output: {e}")
            raise
        
        return connectivity_results
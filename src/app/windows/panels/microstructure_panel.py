#!/usr/bin/env python3
"""
Microstructure Preview Panel for VCCTL

Provides 3D microstructure visualization and preview functionality.
Parameters are now configured in the Mix Design tool.
"""

import gi
import logging
import random
from typing import TYPE_CHECKING, Optional, Dict, Any, List, Tuple
from decimal import Decimal

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, Pango, Gdk, cairo

if TYPE_CHECKING:
    from app.windows.main_window import VCCTLMainWindow

from app.services.service_container import get_service_container
from app.services.microstructure_service import MicrostructureParams, PhaseType
from app.visualization import create_visualization_manager, Microstructure3DViewer, PyVistaViewer3D


class MicrostructurePanel(Gtk.Box):
    """Microstructure preview panel with 3D visualization controls."""
    
    def __init__(self, main_window: 'VCCTLMainWindow'):
        """Initialize the microstructure panel."""
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        self.main_window = main_window
        self.logger = logging.getLogger('VCCTL.MicrostructurePanel')
        self.service_container = get_service_container()
        self.microstructure_service = self.service_container.microstructure_service
        
        # Initialize visualization manager
        self.plot_manager, self.plot_exporter = create_visualization_manager(main_window)
        self.microstructure_3d_viewer = None
        self.pyvista_3d_viewer = None
        self.current_viewer_type = 'matplotlib'  # 'matplotlib' or 'pyvista'
        
        # Panel state
        self.current_params = None
        self.validation_result = None
        self.computation_estimate = None
        
        # Setup UI
        self._setup_ui()
        self._connect_signals()
        
        # Load default parameters
        self._load_default_parameters()
        
        self.logger.info("Microstructure panel initialized")
    
    def _on_enable_3d_viewer(self, button: Gtk.Button) -> None:
        """Enable 3D viewer on demand based on selected viewer type."""
        try:
            self.current_viewer_type = self.viewer_type_combo.get_active_id()
            
            if self.current_viewer_type == 'pyvista':
                if self.pyvista_3d_viewer is None:
                    # Create PyVista viewer
                    self.pyvista_3d_viewer = PyVistaViewer3D()
                    self._replace_viewer_placeholder(self.pyvista_3d_viewer)
                    self.logger.info("PyVista 3D viewer enabled successfully")
                    button.set_label("PyVista Viewer Active")
                    
            else:  # matplotlib
                if self.microstructure_3d_viewer is None:
                    # Create matplotlib viewer
                    self.microstructure_3d_viewer = Microstructure3DViewer()
                    self._replace_viewer_placeholder(self.microstructure_3d_viewer)
                    self.logger.info("Matplotlib 3D viewer enabled successfully")
                    button.set_label("Matplotlib Viewer Active")
            
            button.set_sensitive(False)
            self.viewer_type_combo.set_sensitive(False)  # Lock viewer type once enabled
            
        except Exception as e:
            self.logger.error(f"Failed to enable {self.current_viewer_type} viewer: {e}")
            button.set_label(f"{self.current_viewer_type.title()} Viewer Error")
            button.set_sensitive(False)
    
    def _replace_viewer_placeholder(self, viewer_widget):
        """Replace the placeholder with the actual viewer widget."""
        parent = self.viewer_placeholder.get_parent()
        parent.remove(self.viewer_placeholder)
        parent.pack_start(viewer_widget, True, True, 0)
        viewer_widget.show_all()
    
    def _on_viewer_type_changed(self, combo):
        """Handle viewer type change (only works before enabling)."""
        # This just updates the selection - actual change happens when Enable is clicked
        selected_type = combo.get_active_id()
        self.logger.debug(f"Viewer type selected: {selected_type}")
        
        # Update Generate Preview button visibility based on viewer type
        if hasattr(self, 'preview_button'):
            if selected_type == 'pyvista':
                # PyVista loads data automatically, no Generate Preview needed
                self.preview_button.set_visible(False)
                self.preview_button.set_no_show_all(True)
            else:
                # Matplotlib viewer needs Generate Preview button
                self.preview_button.set_visible(True)
                self.preview_button.set_no_show_all(False)
    
    def _get_active_viewer(self):
        """Get the currently active 3D viewer."""
        if self.current_viewer_type == 'pyvista' and self.pyvista_3d_viewer is not None:
            return self.pyvista_3d_viewer
        elif self.current_viewer_type == 'matplotlib' and self.microstructure_3d_viewer is not None:
            return self.microstructure_3d_viewer
        return None
    
    def _setup_ui(self) -> None:
        """Setup the microstructure panel UI."""
        # Create header
        self._create_header()
        
        # Create main content area
        self._create_content_area()
    
    def _create_header(self) -> None:
        """Create the panel header."""
        header_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        header_box.set_margin_top(10)
        header_box.set_margin_bottom(10)
        header_box.set_margin_left(15)
        header_box.set_margin_right(15)
        
        # Title and controls
        title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        title_label = Gtk.Label()
        title_label.set_markup('<span size="large" weight="bold">Microstructure Preview</span>')
        title_label.set_halign(Gtk.Align.START)
        title_box.pack_start(title_label, False, False, 0)
        
        
        header_box.pack_start(title_box, False, False, 0)
        
        # Description
        desc_label = Gtk.Label()
        desc_label.set_markup('<span size="small">Generate and visualize 3D microstructures using parameters configured in the Mix Design tool.</span>')
        desc_label.set_halign(Gtk.Align.START)
        desc_label.get_style_context().add_class("dim-label")
        header_box.pack_start(desc_label, False, False, 0)
        
        self.pack_start(header_box, False, False, 0)
        
        # Separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.pack_start(separator, False, False, 0)
    
    def _create_content_area(self) -> None:
        """Create the main content area with preview controls only."""
        # Create scrolled window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_hexpand(True)
        scrolled.set_vexpand(True)
        
        # Main content box - centered single column
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        content_box.set_margin_top(15)
        content_box.set_margin_bottom(15)
        content_box.set_margin_left(15)
        content_box.set_margin_right(15)
        
        
        # Preview section - now takes full width
        self._create_preview_section(content_box)
        
        scrolled.add(content_box)
        self.pack_start(scrolled, True, True, 0)
    
    def _create_preview_section(self, parent: Gtk.Box) -> None:
        """Create microstructure preview section."""
        frame = Gtk.Frame(label="Microstructure Preview")
        frame.get_style_context().add_class("card")
        
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_top(15)
        vbox.set_margin_bottom(15)
        vbox.set_margin_left(15)
        vbox.set_margin_right(15)
        
        # TEMPORARILY DISABLE 3D VIEWER TO ELIMINATE INFINITE SURFACE SIZE WARNINGS
        # The matplotlib GTK3Agg backend is causing surface creation issues during initialization
        
        # Create placeholder for 3D viewer instead of actual widget
        viewer_placeholder = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        viewer_placeholder.set_size_request(300, 250)
        
        # Add informational label
        info_label = Gtk.Label()
        info_label.set_markup('<span size="large">3D Microstructure Viewer</span>')
        info_label.set_halign(Gtk.Align.CENTER)
        viewer_placeholder.pack_start(info_label, False, False, 0)
        
        # Add viewer type selection
        viewer_type_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        viewer_type_box.set_halign(Gtk.Align.CENTER)
        
        viewer_type_label = Gtk.Label("Viewer Type:")
        viewer_type_box.pack_start(viewer_type_label, False, False, 0)
        
        self.viewer_type_combo = Gtk.ComboBoxText()
        self.viewer_type_combo.append("matplotlib", "Matplotlib (Interactive)")
        self.viewer_type_combo.append("pyvista", "PyVista (High Quality)")
        self.viewer_type_combo.set_active_id("pyvista")  # Default to PyVista
        self.viewer_type_combo.connect('changed', self._on_viewer_type_changed)
        viewer_type_box.pack_start(self.viewer_type_combo, False, False, 0)
        
        viewer_placeholder.pack_start(viewer_type_box, False, False, 5)
        
        # Add status message
        status_label = Gtk.Label()
        status_label.set_markup('<span size="small" color="#666666">Choose viewer type and click Enable to initialize 3D visualization</span>')
        status_label.set_halign(Gtk.Align.CENTER)
        status_label.set_line_wrap(True)
        viewer_placeholder.pack_start(status_label, True, True, 0)
        
        # Add enable button for on-demand loading
        enable_button = Gtk.Button(label="Enable 3D Viewer")
        enable_button.set_tooltip_text("Click to initialize selected 3D viewer")
        enable_button.connect('clicked', self._on_enable_3d_viewer)
        enable_button.set_halign(Gtk.Align.CENTER)
        viewer_placeholder.pack_start(enable_button, False, False, 0)
        
        vbox.pack_start(viewer_placeholder, True, True, 0)
        self.viewer_placeholder = viewer_placeholder
        self.microstructure_3d_viewer = None  # Will be created on demand
        
        # Preview controls
        preview_controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        
        self.load_img_button = Gtk.Button(label="Load .img File")
        self.load_img_button.set_tooltip_text("Load genmic.c output file (.img)")
        preview_controls.pack_start(self.load_img_button, True, True, 0)
        
        self.preview_button = Gtk.Button(label="Generate Preview")
        self.preview_button.set_tooltip_text("Generate 3D microstructure preview")
        # Initially hidden since PyVista is default and loads data automatically
        self.preview_button.set_visible(False)
        self.preview_button.set_no_show_all(True)  # Prevent show_all() from making it visible
        preview_controls.pack_start(self.preview_button, True, True, 0)
        
        self.export_preview_button = Gtk.Button(label="Export")
        self.export_preview_button.set_tooltip_text("Export preview as image")
        self.export_preview_button.set_sensitive(False)
        preview_controls.pack_start(self.export_preview_button, False, False, 0)
        
        vbox.pack_start(preview_controls, False, False, 0)
        
        frame.add(vbox)
        parent.pack_start(frame, True, True, 0)
    
    
    def _connect_signals(self) -> None:
        """Connect UI signals."""
        # Preview signals only - parameters are now in Mix Design
        self.load_img_button.connect('clicked', self._on_load_img_clicked)
        self.preview_button.connect('clicked', self._on_preview_clicked)
        self.export_preview_button.connect('clicked', self._on_export_preview_clicked)
        
        # Update button visibility based on default viewer selection
        self._on_viewer_type_changed(self.viewer_type_combo)
    
    def _load_default_parameters(self) -> None:
        """Load default parameters - simplified for preview-only mode."""
        self._update_status("Ready - parameters configured in Mix Design tool")
    
    def _on_parameter_changed(self, widget) -> None:
        """Handle parameter change."""
        self._update_calculated_values()
        self._clear_validation()
    
    def _on_flocculation_toggled(self, check) -> None:
        """Handle flocculation enable/disable."""
        enabled = check.get_active()
        self.flocculation_spin.set_sensitive(enabled)
        
        if not enabled:
            self.flocculation_spin.set_value(0.0)
        
        self._on_parameter_changed(check)
    
    def _on_preset_changed(self, combo) -> None:
        """Handle preset selection change."""
        preset = combo.get_active_id()
        
        if preset == "coarse":
            self.system_size_spin.set_value(50)
            self.resolution_spin.set_value(2.0)
        elif preset == "medium":
            self.system_size_spin.set_value(100)
            self.resolution_spin.set_value(1.0)
        elif preset == "fine":
            self.system_size_spin.set_value(200)
            self.resolution_spin.set_value(0.5)
        elif preset == "ultra_fine":
            self.system_size_spin.set_value(400)
            self.resolution_spin.set_value(0.25)
        # Custom - don't change values
    
    def _on_validate_clicked(self, button) -> None:
        """Handle validate button click."""
        try:
            # Get current parameters
            params = self._get_current_parameters()
            
            # Validate parameters
            validation_result = self.microstructure_service.validate_microstructure_feasibility(
                params, {}  # Empty phase volumes for now
            )
            
            # Estimate computation
            computation_estimate = self.microstructure_service.estimate_computation_time(params)
            
            # Update displays
            self._update_validation_display(validation_result)
            self._update_computation_display(computation_estimate)
            
            self.validation_result = validation_result
            self.computation_estimate = computation_estimate
            self.current_params = params
            
            self.logger.info("Parameter validation completed")
            
        except Exception as e:
            self.logger.error(f"Validation failed: {e}")
            self._update_status(f"Validation error: {e}")
    
    def _on_reset_clicked(self, button) -> None:
        """Handle reset button click - no longer used in preview-only mode."""
        self._update_status("Parameters are configured in Mix Design tool")
    
    def _on_generate_seed_clicked(self, button) -> None:
        """Handle generate seed button click - no longer used in preview-only mode."""
        self._update_status("Random seed is configured in Mix Design tool")
    
    def _get_current_parameters(self) -> MicrostructureParams:
        """Get current parameter values - using defaults for preview-only mode."""
        return MicrostructureParams(
            system_size=100,  # Default preview size
            resolution=1.0,   # Default resolution
            water_binder_ratio=0.4,  # Default W/B ratio
            aggregate_volume_fraction=0.0,  # No aggregates in preview
            air_content=0.05,  # Default air content
            cement_shape_set="sphere",  # Default shape
            aggregate_shape_set="sphere",  # Default shape
            flocculation_enabled=False,  # Default no flocculation
            flocculation_degree=0.0  # Default degree
        )
    
    def _update_calculated_values(self) -> None:
        """Update calculated values display."""
        try:
            system_size = self.system_size_spin.get_value()
            resolution = self.resolution_spin.get_value()
            
            # Physical size
            physical_size = system_size * resolution
            self.calc_size_label.set_text(f"{physical_size:.1f}")
            
            # Total voxels
            total_voxels = int(system_size ** 3)
            self.total_voxels_label.set_text(f"{total_voxels:,}")
            
        except Exception as e:
            self.logger.error(f"Failed to update calculated values: {e}")
    
    def _update_validation_display(self, validation_result: Dict[str, Any]) -> None:
        """Update validation display."""
        buffer = self.validation_text.get_buffer()
        buffer.set_text("")
        
        if validation_result['is_feasible']:
            buffer.insert_at_cursor("✓ Parameters are feasible\n\n")
        else:
            buffer.insert_at_cursor("✗ Parameters have issues\n\n")
        
        if validation_result['errors']:
            buffer.insert_at_cursor("ERRORS:\n")
            for error in validation_result['errors']:
                buffer.insert_at_cursor(f"• {error}\n")
            buffer.insert_at_cursor("\n")
        
        if validation_result['warnings']:
            buffer.insert_at_cursor("WARNINGS:\n")
            for warning in validation_result['warnings']:
                buffer.insert_at_cursor(f"• {warning}\n")
            buffer.insert_at_cursor("\n")
        
        if validation_result['recommendations']:
            buffer.insert_at_cursor("RECOMMENDATIONS:\n")
            for rec in validation_result['recommendations']:
                buffer.insert_at_cursor(f"• {rec}\n")
    
    def _update_computation_display(self, computation_estimate: Dict[str, Any]) -> None:
        """Update computation estimate display."""
        total_voxels = computation_estimate.get('total_voxels', 0)
        time_hours = computation_estimate.get('estimated_time_hours', 0)
        
        # Estimate memory usage (rough approximation)
        memory_mb = total_voxels * 4 / (1024 * 1024)  # 4 bytes per voxel
        
        self.memory_label.set_text(f"Memory: ~{memory_mb:.1f} MB")
        
        if time_hours < 1:
            time_minutes = computation_estimate.get('estimated_time_minutes', 0)
            self.time_label.set_text(f"Time: ~{time_minutes:.1f} minutes")
        else:
            self.time_label.set_text(f"Time: ~{time_hours:.1f} hours")
        
        factors = computation_estimate.get('complexity_factors', {})
        complexity_text = "Complexity: "
        if factors.get('flocculation'):
            complexity_text += "Flocculation "
        if factors.get('fine_resolution'):
            complexity_text += "Fine-res "
        if not any(factors.values()):
            complexity_text += "Standard"
        
        self.complexity_label.set_text(complexity_text)
    
    def _clear_validation(self) -> None:
        """Clear validation displays."""
        buffer = self.validation_text.get_buffer()
        buffer.set_text("Click Validate to check parameters")
        
        self.memory_label.set_text("Memory: -")
        self.time_label.set_text("Time: -")
        self.complexity_label.set_text("Complexity: -")
        
        self.validation_result = None
        self.computation_estimate = None
    
    def _update_status(self, message: str) -> None:
        """Update status message."""
        self.logger.debug(f"Status: {message}")
        # Could add status bar here if needed
    
    def get_microstructure_parameters(self) -> Optional[MicrostructureParams]:
        """Get validated microstructure parameters."""
        if self.current_params and self.validation_result and self.validation_result['is_feasible']:
            return self.current_params
        return None
    
    def set_microstructure_parameters(self, params: MicrostructureParams) -> None:
        """Set microstructure parameters in UI."""
        try:
            self.system_size_spin.set_value(params.system_size)
            self.resolution_spin.set_value(params.resolution)
            self.wb_ratio_spin.set_value(params.water_binder_ratio)
            self.agg_volume_spin.set_value(params.aggregate_volume_fraction)
            self.air_content_spin.set_value(params.air_content)
            
            # Set shape sets
            cement_id = params.cement_shape_set
            agg_id = params.aggregate_shape_set
            
            # Find and set active items
            for i in range(self.cement_shape_combo.get_model().iter_n_children(None)):
                if self.cement_shape_combo.get_model().get_value(self.cement_shape_combo.get_model().get_iter_from_string(str(i)), 0) == cement_id:
                    self.cement_shape_combo.set_active(i)
                    break
            
            for i in range(self.agg_shape_combo.get_model().iter_n_children(None)):
                if self.agg_shape_combo.get_model().get_value(self.agg_shape_combo.get_model().get_iter_from_string(str(i)), 0) == agg_id:
                    self.agg_shape_combo.set_active(i)
                    break
            
            self.flocculation_check.set_active(params.flocculation_enabled)
            self.flocculation_spin.set_value(params.flocculation_degree)
            
            self.preset_combo.set_active(0)  # Custom
            self._clear_validation()
            
            self.logger.info("Microstructure parameters loaded")
            
        except Exception as e:
            self.logger.error(f"Failed to set microstructure parameters: {e}")
            self._update_status(f"Error loading parameters: {e}")
    
    def _on_preview_clicked(self, button) -> None:
        """Handle preview generation button click."""
        try:
            # Validate parameters first
            params = self._get_current_parameters()
            
            # Generate sample 3D microstructure data for preview
            voxel_data = self._generate_sample_microstructure(params)
            
            # Create phase mapping
            phase_mapping = {
                0: "Void/Pore",
                1: "C3S",
                2: "C2S", 
                3: "C3A",
                4: "C4AF",
                5: "Gypsum",
                6: "C-S-H",
                7: "CH"
            }
            
            # Load data into 3D viewer
            active_viewer = self._get_active_viewer()
            success = False
            if active_viewer:
                voxel_size = (params.resolution, params.resolution, params.resolution)
                success = active_viewer.load_voxel_data(
                    voxel_data, phase_mapping, voxel_size
                )
            
            if success:
                self.export_preview_button.set_sensitive(True)
                self._update_status("3D preview generated successfully")
                self.logger.info("3D microstructure preview generated")
            else:
                self._update_status("Failed to generate 3D preview")
            
        except Exception as e:
            self.logger.error(f"Preview generation failed: {e}")
            self._update_status(f"Preview generation error: {e}")
    
    def _generate_sample_microstructure(self, params: MicrostructureParams) -> 'np.ndarray':
        """Generate sample microstructure data for preview."""
        import numpy as np
        
        # Use smaller dimensions for preview (max 50x50x50)
        preview_size = min(50, max(10, int(params.system_size / params.resolution / 4)))
        
        # Create random microstructure with realistic phase distributions
        voxel_data = np.zeros((preview_size, preview_size, preview_size), dtype=int)
        
        # Generate phases based on typical cement paste composition
        total_voxels = preview_size ** 3
        
        # Approximate phase volume fractions for cement paste
        phase_fractions = {
            0: 0.15,  # Pores
            1: 0.20,  # C3S (remaining)
            2: 0.10,  # C2S (remaining)
            3: 0.05,  # C3A (remaining)
            4: 0.03,  # C4AF (remaining)
            5: 0.02,  # Gypsum (remaining)
            6: 0.35,  # C-S-H (hydration product)
            7: 0.10   # CH (hydration product)
        }
        
        # Assign phases randomly but with clustering
        np.random.seed(42)  # For reproducible previews
        
        for phase_id, fraction in phase_fractions.items():
            n_voxels = int(total_voxels * fraction)
            
            if phase_id == 0:  # Pores - create connected pore structure
                # Create some connected pore channels
                for _ in range(n_voxels // 10):
                    start_x = np.random.randint(0, preview_size)
                    start_y = np.random.randint(0, preview_size) 
                    start_z = np.random.randint(0, preview_size)
                    
                    # Create small connected region
                    for _ in range(10):
                        if (0 <= start_x < preview_size and 
                            0 <= start_y < preview_size and 
                            0 <= start_z < preview_size):
                            voxel_data[start_x, start_y, start_z] = phase_id
                            
                            # Move to adjacent voxel
                            start_x += np.random.randint(-1, 2)
                            start_y += np.random.randint(-1, 2)
                            start_z += np.random.randint(-1, 2)
            else:
                # Create clusters for other phases
                remaining = n_voxels
                while remaining > 0:
                    # Find empty voxel
                    attempts = 0
                    while attempts < 100:
                        x = np.random.randint(0, preview_size)
                        y = np.random.randint(0, preview_size)
                        z = np.random.randint(0, preview_size)
                        
                        if voxel_data[x, y, z] == 0:
                            break
                        attempts += 1
                    
                    if attempts >= 100:
                        break
                    
                    # Create cluster
                    cluster_size = min(remaining, np.random.randint(1, 8))
                    for _ in range(cluster_size):
                        if (0 <= x < preview_size and 
                            0 <= y < preview_size and 
                            0 <= z < preview_size and
                            voxel_data[x, y, z] == 0):
                            voxel_data[x, y, z] = phase_id
                            remaining -= 1
                            
                            # Move to adjacent voxel for cluster growth
                            x += np.random.randint(-1, 2)
                            y += np.random.randint(-1, 2) 
                            z += np.random.randint(-1, 2)
        
        return voxel_data
    
    def _on_load_img_clicked(self, button) -> None:
        """Handle load .img file button click."""
        try:
            # Try native file chooser first (often better folder control)
            try:
                dialog = Gtk.FileChooserNative.new(
                    title="Load Microstructure .img File",
                    parent=self.main_window,
                    action=Gtk.FileChooserAction.OPEN,
                    accept_label="_Open",
                    cancel_label="_Cancel"
                )
                using_native = True
            except (AttributeError, TypeError):
                # Fallback to standard dialog if FileChooserNative not available
                dialog = Gtk.FileChooserDialog(
                    title="Load Microstructure .img File", 
                    parent=self.main_window,
                    action=Gtk.FileChooserAction.OPEN
                )
                dialog.add_buttons(
                    Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                    Gtk.STOCK_OPEN, Gtk.ResponseType.OK
                )
                using_native = False
                
            # Configure dialog settings
            dialog.set_select_multiple(False)
            dialog.set_show_hidden(False)
            
            # Add file filter for .img files
            filter_img = Gtk.FileFilter()
            filter_img.set_name("VCCTL Microstructure Files (*.img)")
            filter_img.add_pattern("*.img")
            dialog.add_filter(filter_img)
            
            filter_all = Gtk.FileFilter()
            filter_all.set_name("All Files")
            filter_all.add_pattern("*")
            dialog.add_filter(filter_all)
            
            # Set initial directory to Operations folder where generated .img files are located  
            import os
            
            operations_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "Operations")
            if os.path.exists(operations_path):
                # Set current folder - this should work better with native chooser
                dialog.set_current_folder(operations_path)
                
                # Add as shortcut only for non-native dialogs (native doesn't support this)
                if not using_native:
                    try:
                        dialog.add_shortcut_folder(operations_path)
                    except:
                        pass
            
            response = dialog.run()
            if response == Gtk.ResponseType.OK:
                filename = dialog.get_filename()
                self._load_img_file(filename)
            
            dialog.destroy()
            
        except Exception as e:
            self.logger.error(f"File dialog failed: {e}")
            self._update_status(f"File selection error: {e}")

    def _load_img_file(self, filepath: str) -> None:
        """Load and display a .img microstructure file."""
        try:
            import numpy as np
            import os
            
            self._update_status(f"Loading {os.path.basename(filepath)}...")
            
            # Read the .img file (text format from genmic.c)
            with open(filepath, 'r') as f:
                # Parse header information
                lines = f.readlines()
                
                # Find dimensions from header
                x_size = y_size = z_size = resolution = None
                data_start_line = 0
                
                for i, line in enumerate(lines):
                    line = line.strip()
                    if line.startswith('X_Size:'):
                        x_size = int(line.split(':')[1].strip())
                    elif line.startswith('Y_Size:'):
                        y_size = int(line.split(':')[1].strip())
                    elif line.startswith('Z_Size:'):
                        z_size = int(line.split(':')[1].strip())
                    elif line.startswith('Image_Resolution:'):
                        resolution = float(line.split(':')[1].strip())
                    elif line.isdigit():  # First voxel data line (phase ID at position 0,0,0)
                        data_start_line = i
                        break
                
                if None in (x_size, y_size, z_size):
                    raise ValueError("Could not parse dimensions from .img file header")
                
                self.logger.info(f"Loading microstructure: {x_size}x{y_size}x{z_size} voxels, resolution: {resolution}")
                
                # Read voxel data (text format, one value per line)
                voxel_values = []
                for line in lines[data_start_line:]:
                    line = line.strip()
                    if line.isdigit():
                        voxel_values.append(int(line))
                
                expected_size = x_size * y_size * z_size
                if len(voxel_values) != expected_size:
                    self.logger.warning(f"Expected {expected_size} voxels, got {len(voxel_values)}")
                    # Pad with zeros if needed
                    while len(voxel_values) < expected_size:
                        voxel_values.append(0)
                    # Truncate if too long
                    voxel_values = voxel_values[:expected_size]
                
                # Convert to numpy array and reshape
                voxel_data = np.array(voxel_values, dtype=np.uint8)
                
                # Reshape assuming C-order (standard numpy order: Z varies fastest)
                # Since current file is 100x100x100, ordering doesn't affect visualization
                voxel_data = voxel_data.reshape((x_size, y_size, z_size))
                
                self.logger.info(f"Reshaped voxel data to: {voxel_data.shape}")
                
                # Determine unique phases
                unique_phases = np.unique(voxel_data)
                self.logger.info(f"Found phases: {unique_phases}")
                
                # Create phase mapping (phase ID -> color)
                phase_colors = {}
                phase_names = {}
                
                # Standard VCCTL phase mappings (from colors.csv)
                standard_phases = {
                    0: ("#191919", "Porosity"),
                    1: ("#2A2AD2", "C3S"),
                    2: ("#8B4F13", "C2S"),
                    3: ("#B2B2B2", "C3A"),
                    4: ("#FDFDFD", "C4AF"),
                    5: ("#FF0000", "K2SO4"),
                    6: ("#FF1400", "Na2SO4"),
                    7: ("#FFFF00", "Gypsum"),
                    8: ("#FFF056", "Hemihydrate"),
                    9: ("#FFFF80", "Anhydrite"),
                    10: ("#28AD4B", "Sfume"),
                    11: ("#6464FF", "Inert Filler"),
                    12: ("#FFA500", "Slag"),
                    13: ("#FFC041", "Fly Ash"),
                    16: ("#1A641A", "Brucite"),
                    17: ("#00C8C8", "Hydrotalcite"),
                    19: ("#07488E", "Portlandite"),
                    20: ("#F5DEB3", "CSH"),
                    22: ("#7F00FF", "AFt"),
                    24: ("#F446CB", "AFm"),
                    33: ("#00CC00", "CACO3"),
                    34: ("#FAC6DC", "AFmc"),
                    55: ("#000000", "Void")
                }
                
                for phase_id in unique_phases:
                    if phase_id in standard_phases:
                        color, name = standard_phases[phase_id]
                    else:
                        # Generate color for unknown phases (avoid overflow)
                        phase_id_int = int(phase_id)
                        r = (phase_id_int * 50) % 256
                        g = (phase_id_int * 100) % 256
                        b = (phase_id_int * 150) % 256
                        color = f"#{r:02x}{g:02x}{b:02x}"
                        name = f"Phase {phase_id}"
                    
                    phase_colors[int(phase_id)] = color
                    phase_names[int(phase_id)] = name
                
                # Display in 3D viewer using correct method
                active_viewer = self._get_active_viewer()
                if active_viewer:
                    success = active_viewer.load_voxel_data(
                        voxel_data,
                        phase_names,
                        (1.0, 1.0, 1.0)  # voxel size
                    )
                else:
                    success = False
                
                if success:
                    self.export_preview_button.set_sensitive(True)
                    
                    # Count voxels per phase
                    phase_counts = []
                    pore_count = 0
                    for phase_id, name in phase_names.items():
                        count = np.sum(voxel_data == phase_id)
                        if phase_id == 0:
                            pore_count = count
                        else:
                            phase_counts.append(f"{name} ({count} voxels)")
                    
                    phase_info = ", ".join(phase_counts)
                    status_msg = f"Loaded {os.path.basename(filepath)} - Size: {x_size}×{y_size}×{z_size}"
                    if pore_count > 0:
                        status_msg += f" - {pore_count} pores hidden"
                    if phase_counts:
                        status_msg += f" - Solid phases: {phase_info}"
                    
                    self._update_status(status_msg)
                    self.logger.info(f"Successfully loaded microstructure from {filepath}")
                else:
                    self._update_status("Failed to display loaded microstructure")
                    
        except Exception as e:
            self.logger.error(f"Failed to load .img file {filepath}: {e}")
            self._update_status(f"Failed to load file: {e}")
    
    def _on_export_preview_clicked(self, button) -> None:
        """Handle preview export button click."""
        try:
            # Create file chooser dialog
            dialog = Gtk.FileChooserDialog(
                title="Export 3D Microstructure Preview",
                parent=self.main_window,
                action=Gtk.FileChooserAction.SAVE
            )
            dialog.add_buttons(
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_SAVE, Gtk.ResponseType.OK
            )
            
            # Add file filters
            for name, pattern in [("PNG Images", "*.png"), ("PDF Files", "*.pdf"), ("SVG Files", "*.svg")]:
                filter_type = Gtk.FileFilter()
                filter_type.set_name(name)
                filter_type.add_pattern(pattern)
                dialog.add_filter(filter_type)
            
            dialog.set_current_name("microstructure_preview.png")
            
            response = dialog.run()
            if response == Gtk.ResponseType.OK:
                filename = dialog.get_filename()
                active_viewer = self._get_active_viewer()
                if active_viewer:
                    format_type = filename.split('.')[-1].lower()
                    # Both viewers have export_3d_view method, but PyVista uses screenshot
                    if hasattr(active_viewer, 'export_3d_view'):
                        success = active_viewer.export_3d_view(filename, format_type)
                    elif hasattr(active_viewer, 'plotter'):
                        # PyVista viewer - use screenshot method
                        try:
                            active_viewer.plotter.screenshot(filename, transparent_background=True)
                            success = True
                        except Exception as e:
                            self.logger.error(f"PyVista export failed: {e}")
                            success = False
                    else:
                        success = False
                    
                    if success:
                        self._update_status(f"3D preview exported to {filename}")
                    else:
                        self._update_status("Failed to export 3D preview")
                else:
                    self._update_status("No 3D preview available to export")
            
            dialog.destroy()
            
        except Exception as e:
            self.logger.error(f"Preview export failed: {e}")
            self._update_status(f"Export error: {e}")
    

#!/usr/bin/env python3
"""
Elastic Moduli Panel for VCCTL

Provides interface for configuring and running elastic moduli calculations on hydrated microstructures.
This is the third stage in the VCCTL workflow: Microstructure → Hydration → Elastic Moduli
"""

import gi
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Dict, Any, List

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, Pango

if TYPE_CHECKING:
    from app.windows.main_window import VCCTLMainWindow

from app.services.service_container import get_service_container
from app.services.elastic_moduli_service import ElasticModuliService
from app.models.elastic_moduli_operation import ElasticModuliOperation
from app.models.operation import Operation, OperationStatus, OperationType
from app.utils.icon_utils import create_button_with_icon


class ElasticModuliPanel(Gtk.Box):
    """Main panel for elastic moduli calculations."""
    
    def __init__(self, main_window: 'VCCTLMainWindow'):
        """Initialize the elastic moduli panel."""
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        self.main_window = main_window
        self.logger = logging.getLogger('VCCTL.ElasticModuliPanel')
        self.service_container = get_service_container()
        self.elastic_moduli_service = ElasticModuliService(self.service_container)
        
        # Panel state
        self.current_operation = None
        self.available_hydration_operations = []
        
        # UI components
        self.hydration_combo = None
        self.operation_name_entry = None
        self.image_filename_entry = None
        self.output_dir_entry = None
        self.pimg_file_entry = None
        self.has_itz_check = None
        self.air_volume_spin = None
        
        # Fine aggregate controls
        self.fine_agg_check = None
        self.fine_volume_spin = None
        self.fine_grading_entry = None
        self.fine_bulk_spin = None
        self.fine_shear_spin = None
        
        # Coarse aggregate controls
        self.coarse_agg_check = None
        self.coarse_volume_spin = None
        self.coarse_grading_entry = None
        self.coarse_bulk_spin = None
        self.coarse_shear_spin = None
        
        # Setup UI
        self._setup_ui()
        
        # Load initial data
        self._load_available_hydration_operations()
        
        self.logger.info("Elastic Moduli panel initialized")
    
    def _setup_ui(self) -> None:
        """Setup the main UI components."""
        # Create header
        self._create_header()
        
        # Create main content area with scrolling
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(400)
        
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        content_box.set_margin_top(15)
        content_box.set_margin_bottom(15)
        content_box.set_margin_left(20)
        content_box.set_margin_right(20)
        
        # Create input sections
        self._create_operation_settings(content_box)
        self._create_microstructure_settings(content_box)
        self._create_aggregate_settings(content_box)
        self._create_air_settings(content_box)
        self._create_action_buttons(content_box)
        
        scrolled.add(content_box)
        self.pack_start(scrolled, True, True, 0)
    
    def _create_header(self) -> None:
        """Create the panel header."""
        header_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        header_box.set_margin_top(15)
        header_box.set_margin_bottom(10)
        header_box.set_margin_left(20)
        header_box.set_margin_right(20)
        
        # Title
        title_label = Gtk.Label()
        title_label.set_markup('<span size="large" weight="bold">Elastic Moduli Calculations</span>')
        title_label.set_halign(Gtk.Align.START)
        header_box.pack_start(title_label, False, False, 0)
        
        # Description
        desc_label = Gtk.Label()
        desc_label.set_markup('<span size="small">Calculate mechanical properties from hydrated microstructures</span>')
        desc_label.set_halign(Gtk.Align.START)
        desc_label.set_line_wrap(True)
        header_box.pack_start(desc_label, False, False, 0)
        
        # Separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        header_box.pack_start(separator, False, False, 5)
        
        self.pack_start(header_box, False, False, 0)
    
    def _create_operation_settings(self, parent: Gtk.Box) -> None:
        """Create operation configuration section."""
        frame = Gtk.Frame(label="Operation Settings")
        frame.set_label_align(0.02, 0.5)
        
        grid = Gtk.Grid()
        grid.set_row_spacing(10)
        grid.set_column_spacing(15)
        grid.set_margin_top(15)
        grid.set_margin_bottom(15)
        grid.set_margin_left(15)
        grid.set_margin_right(15)
        
        row = 0
        
        # Hydration operation selection
        label = Gtk.Label("Source Hydration Operation:")
        label.set_halign(Gtk.Align.START)
        label.set_tooltip_text("Select the completed hydration operation to use as input")
        grid.attach(label, 0, row, 1, 1)
        
        self.hydration_combo = Gtk.ComboBoxText()
        self.hydration_combo.set_tooltip_text("Choose from completed hydration operations")
        self.hydration_combo.connect("changed", self._on_hydration_selection_changed)
        grid.attach(self.hydration_combo, 1, row, 2, 1)
        
        row += 1
        
        # Operation name
        label = Gtk.Label("Operation Name:")
        label.set_halign(Gtk.Align.START)
        grid.attach(label, 0, row, 1, 1)
        
        self.operation_name_entry = Gtk.Entry()
        self.operation_name_entry.set_placeholder_text("e.g., ElasticModuli_MyMix01")
        self.operation_name_entry.set_tooltip_text("Unique name for this elastic moduli calculation")
        grid.attach(self.operation_name_entry, 1, row, 2, 1)
        
        frame.add(grid)
        parent.pack_start(frame, False, False, 0)
    
    def _create_microstructure_settings(self, parent: Gtk.Box) -> None:
        """Create microstructure file settings section."""
        frame = Gtk.Frame(label="Microstructure Settings")
        frame.set_label_align(0.02, 0.5)
        
        grid = Gtk.Grid()
        grid.set_row_spacing(10)
        grid.set_column_spacing(15)
        grid.set_margin_top(15)
        grid.set_margin_bottom(15)
        grid.set_margin_left(15)
        grid.set_margin_right(15)
        
        row = 0
        
        # Image filename
        label = Gtk.Label("Image Filename:")
        label.set_halign(Gtk.Align.START)
        grid.attach(label, 0, row, 1, 1)
        
        self.image_filename_entry = Gtk.Entry()
        self.image_filename_entry.set_placeholder_text("e.g., MyMix01.img")
        self.image_filename_entry.set_tooltip_text("Hydrated microstructure image file")
        grid.attach(self.image_filename_entry, 1, row, 2, 1)
        
        row += 1
        
        # Output directory
        label = Gtk.Label("Output Directory:")
        label.set_halign(Gtk.Align.START)
        grid.attach(label, 0, row, 1, 1)
        
        dir_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        
        self.output_dir_entry = Gtk.Entry()
        self.output_dir_entry.set_placeholder_text("Directory for output files")
        dir_box.pack_start(self.output_dir_entry, True, True, 0)
        
        browse_button = Gtk.Button("Browse...")
        browse_button.connect("clicked", self._on_browse_output_dir)
        dir_box.pack_start(browse_button, False, False, 0)
        
        grid.attach(dir_box, 1, row, 2, 1)
        
        row += 1
        
        # Pimg file path
        label = Gtk.Label("Pimg File Path:")
        label.set_halign(Gtk.Align.START)
        grid.attach(label, 0, row, 1, 1)
        
        pimg_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        
        self.pimg_file_entry = Gtk.Entry()
        self.pimg_file_entry.set_placeholder_text("Optional .pimg file")
        pimg_box.pack_start(self.pimg_file_entry, True, True, 0)
        
        browse_pimg_button = Gtk.Button("Browse...")
        browse_pimg_button.connect("clicked", self._on_browse_pimg_file)
        pimg_box.pack_start(browse_pimg_button, False, False, 0)
        
        grid.attach(pimg_box, 1, row, 2, 1)
        
        row += 1
        
        # ITZ flag
        self.has_itz_check = Gtk.CheckButton("Include ITZ (Interfacial Transition Zone)")
        self.has_itz_check.set_tooltip_text("Include ITZ calculations for aggregate interfaces")
        grid.attach(self.has_itz_check, 0, row, 3, 1)
        
        frame.add(grid)
        parent.pack_start(frame, False, False, 0)
    
    def _create_aggregate_settings(self, parent: Gtk.Box) -> None:
        """Create aggregate properties section."""
        frame = Gtk.Frame(label="Aggregate Properties")
        frame.set_label_align(0.02, 0.5)
        
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        main_box.set_margin_top(15)
        main_box.set_margin_bottom(15)
        main_box.set_margin_left(15)
        main_box.set_margin_right(15)
        
        # Fine aggregate section
        fine_frame = Gtk.Frame(label="Fine Aggregate")
        fine_frame.set_label_align(0.02, 0.5)
        fine_grid = self._create_aggregate_grid("fine")
        fine_frame.add(fine_grid)
        main_box.pack_start(fine_frame, False, False, 0)
        
        # Coarse aggregate section
        coarse_frame = Gtk.Frame(label="Coarse Aggregate")
        coarse_frame.set_label_align(0.02, 0.5)
        coarse_grid = self._create_aggregate_grid("coarse")
        coarse_frame.add(coarse_grid)
        main_box.pack_start(coarse_frame, False, False, 0)
        
        frame.add(main_box)
        parent.pack_start(frame, False, False, 0)
    
    def _create_aggregate_grid(self, agg_type: str) -> Gtk.Grid:
        """Create aggregate property grid for fine or coarse aggregate."""
        grid = Gtk.Grid()
        grid.set_row_spacing(10)
        grid.set_column_spacing(15)
        grid.set_margin_top(10)
        grid.set_margin_bottom(10)
        grid.set_margin_left(10)
        grid.set_margin_right(10)
        
        row = 0
        
        # Enable checkbox
        if agg_type == "fine":
            self.fine_agg_check = Gtk.CheckButton(f"Include {agg_type} aggregate")
            self.fine_agg_check.connect("toggled", self._on_fine_aggregate_toggled)
            check_widget = self.fine_agg_check
        else:
            self.coarse_agg_check = Gtk.CheckButton(f"Include {agg_type} aggregate")
            self.coarse_agg_check.connect("toggled", self._on_coarse_aggregate_toggled)
            check_widget = self.coarse_agg_check
        
        grid.attach(check_widget, 0, row, 3, 1)
        row += 1
        
        # Volume fraction
        label = Gtk.Label("Volume Fraction:")
        label.set_halign(Gtk.Align.START)
        grid.attach(label, 0, row, 1, 1)
        
        if agg_type == "fine":
            self.fine_volume_spin = Gtk.SpinButton.new_with_range(0.0, 1.0, 0.01)
            self.fine_volume_spin.set_digits(3)
            self.fine_volume_spin.set_value(0.0)
            self.fine_volume_spin.set_tooltip_text("Volume fraction of fine aggregate (0.0-1.0)")
            spin_widget = self.fine_volume_spin
        else:
            self.coarse_volume_spin = Gtk.SpinButton.new_with_range(0.0, 1.0, 0.01)
            self.coarse_volume_spin.set_digits(3)
            self.coarse_volume_spin.set_value(0.0)
            self.coarse_volume_spin.set_tooltip_text("Volume fraction of coarse aggregate (0.0-1.0)")
            spin_widget = self.coarse_volume_spin
        
        grid.attach(spin_widget, 1, row, 2, 1)
        row += 1
        
        # Grading path
        label = Gtk.Label("Grading Path:")
        label.set_halign(Gtk.Align.START)
        grid.attach(label, 0, row, 1, 1)
        
        grading_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        
        if agg_type == "fine":
            self.fine_grading_entry = Gtk.Entry()
            self.fine_grading_entry.set_placeholder_text("Path to grading file")
            grading_box.pack_start(self.fine_grading_entry, True, True, 0)
            entry_widget = self.fine_grading_entry
        else:
            self.coarse_grading_entry = Gtk.Entry()
            self.coarse_grading_entry.set_placeholder_text("Path to grading file")
            grading_box.pack_start(self.coarse_grading_entry, True, True, 0)
            entry_widget = self.coarse_grading_entry
        
        browse_button = Gtk.Button("Browse...")
        browse_button.connect("clicked", self._on_browse_grading_file, agg_type)
        grading_box.pack_start(browse_button, False, False, 0)
        
        grid.attach(grading_box, 1, row, 2, 1)
        row += 1
        
        # Bulk modulus
        label = Gtk.Label("Bulk Modulus (GPa):")
        label.set_halign(Gtk.Align.START)
        grid.attach(label, 0, row, 1, 1)
        
        if agg_type == "fine":
            self.fine_bulk_spin = Gtk.SpinButton.new_with_range(0.0, 1000.0, 0.1)
            self.fine_bulk_spin.set_digits(2)
            self.fine_bulk_spin.set_value(37.0)  # Typical quartz value
            self.fine_bulk_spin.set_tooltip_text("Bulk modulus in GPa (typical: quartz ~37)")
            spin_widget = self.fine_bulk_spin
        else:
            self.coarse_bulk_spin = Gtk.SpinButton.new_with_range(0.0, 1000.0, 0.1)
            self.coarse_bulk_spin.set_digits(2)
            self.coarse_bulk_spin.set_value(37.0)
            self.coarse_bulk_spin.set_tooltip_text("Bulk modulus in GPa (typical: quartz ~37)")
            spin_widget = self.coarse_bulk_spin
        
        grid.attach(spin_widget, 1, row, 2, 1)
        row += 1
        
        # Shear modulus
        label = Gtk.Label("Shear Modulus (GPa):")
        label.set_halign(Gtk.Align.START)
        grid.attach(label, 0, row, 1, 1)
        
        if agg_type == "fine":
            self.fine_shear_spin = Gtk.SpinButton.new_with_range(0.0, 1000.0, 0.1)
            self.fine_shear_spin.set_digits(2)
            self.fine_shear_spin.set_value(44.0)  # Typical quartz value
            self.fine_shear_spin.set_tooltip_text("Shear modulus in GPa (typical: quartz ~44)")
            spin_widget = self.fine_shear_spin
        else:
            self.coarse_shear_spin = Gtk.SpinButton.new_with_range(0.0, 1000.0, 0.1)
            self.coarse_shear_spin.set_digits(2)
            self.coarse_shear_spin.set_value(44.0)
            self.coarse_shear_spin.set_tooltip_text("Shear modulus in GPa (typical: quartz ~44)")
            spin_widget = self.coarse_shear_spin
        
        grid.attach(spin_widget, 1, row, 2, 1)
        
        # Initially disable all controls except checkbox
        self._set_aggregate_controls_sensitive(agg_type, False)
        
        return grid
    
    def _create_air_settings(self, parent: Gtk.Box) -> None:
        """Create air content settings section."""
        frame = Gtk.Frame(label="Air Content")
        frame.set_label_align(0.02, 0.5)
        
        grid = Gtk.Grid()
        grid.set_row_spacing(10)
        grid.set_column_spacing(15)
        grid.set_margin_top(15)
        grid.set_margin_bottom(15)
        grid.set_margin_left(15)
        grid.set_margin_right(15)
        
        # Air volume fraction
        label = Gtk.Label("Air Volume Fraction:")
        label.set_halign(Gtk.Align.START)
        grid.attach(label, 0, 0, 1, 1)
        
        self.air_volume_spin = Gtk.SpinButton.new_with_range(0.0, 0.5, 0.001)
        self.air_volume_spin.set_digits(3)
        self.air_volume_spin.set_value(0.0)
        self.air_volume_spin.set_tooltip_text("Volume fraction of air/porosity (0.0-0.5)")
        grid.attach(self.air_volume_spin, 1, 0, 1, 1)
        
        frame.add(grid)
        parent.pack_start(frame, False, False, 0)
    
    def _create_action_buttons(self, parent: Gtk.Box) -> None:
        """Create action buttons section."""
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        button_box.set_halign(Gtk.Align.CENTER)
        button_box.set_margin_top(20)
        
        # Generate Input File button
        generate_button = create_button_with_icon("Generate Input File", "save")
        generate_button.connect("clicked", self._on_generate_input_file)
        generate_button.set_tooltip_text("Generate elastic.in input file for calculation")
        button_box.pack_start(generate_button, False, False, 0)
        
        # Start Calculation button
        start_button = create_button_with_icon("Start Calculation", "play")
        start_button.connect("clicked", self._on_start_calculation)
        start_button.set_tooltip_text("Start elastic moduli calculation")
        button_box.pack_start(start_button, False, False, 0)
        
        # Clear Form button
        clear_button = create_button_with_icon("Clear Form", "erase")
        clear_button.connect("clicked", self._on_clear_form)
        clear_button.set_tooltip_text("Reset all form fields")
        button_box.pack_start(clear_button, False, False, 0)
        
        parent.pack_start(button_box, False, False, 0)
    
    def _load_available_hydration_operations(self) -> None:
        """Load available completed hydration operations."""
        try:
            self.available_hydration_operations = self.elastic_moduli_service.get_available_hydration_operations()
            
            # Clear and populate combo box
            self.hydration_combo.remove_all()
            for operation in self.available_hydration_operations:
                display_text = f"{operation.name} ({operation.completed_at.strftime('%m/%d %H:%M') if operation.completed_at else 'Unknown'})"
                self.hydration_combo.append(str(operation.id), display_text)
            
            if not self.available_hydration_operations:
                self.hydration_combo.append("", "No completed hydration operations found")
                self.hydration_combo.set_sensitive(False)
            
        except Exception as e:
            self.logger.error(f"Error loading hydration operations: {e}")
            self.hydration_combo.append("", "Error loading operations")
            self.hydration_combo.set_sensitive(False)
    
    def _on_hydration_selection_changed(self, combo: Gtk.ComboBoxText) -> None:
        """Handle hydration operation selection change."""
        active_id = combo.get_active_id()
        if not active_id or active_id == "":
            return
        
        try:
            hydration_id = int(active_id)
            hydration_operation = next(
                (op for op in self.available_hydration_operations if op.id == hydration_id),
                None
            )
            
            if hydration_operation:
                self._populate_fields_from_hydration(hydration_operation)
                
        except Exception as e:
            self.logger.error(f"Error handling hydration selection: {e}")
    
    def _populate_fields_from_hydration(self, hydration_operation: Operation) -> None:
        """Populate form fields based on selected hydration operation."""
        # Set operation name (Phase 3: Clean naming without auto-prefixes)
        # User can override this with their own clean name
        operation_name = ""  # Let user provide their own clean name
        self.operation_name_entry.set_text(operation_name)
        
        # Set image filename
        image_filename = f"{hydration_operation.name}.img"
        self.image_filename_entry.set_text(image_filename)
        
        # Set output directory
        project_root = Path(__file__).parent.parent.parent.parent
        output_dir = project_root / "Operations" / f"Elastic_{hydration_operation.name}"
        self.output_dir_entry.set_text(str(output_dir))
        
        # Find .pimg file in MICROSTRUCTURE directory (not hydration)
        # The pimg file is created during microstructure generation
        microstructure_name = self._get_parent_microstructure_name(hydration_operation)
        if microstructure_name:
            microstructure_dir = project_root / "Operations" / microstructure_name
            if microstructure_dir.exists():
                pimg_files = list(microstructure_dir.glob("*.pimg"))
                if pimg_files:
                    self.pimg_file_entry.set_text(str(pimg_files[0]))
                    self.logger.info(f"Found pimg file in microstructure directory: {pimg_files[0]}")
                else:
                    self.logger.warning(f"No .pimg file found in microstructure directory: {microstructure_dir}")
            else:
                self.logger.warning(f"Microstructure directory not found: {microstructure_dir}")
        else:
            self.logger.warning(f"Could not determine parent microstructure for hydration operation: {hydration_operation.name}")
        
        # **NEW**: Auto-populate aggregate properties from microstructure metadata
        try:
            # Create a temporary operation object to populate from microstructure data
            temp_operation = ElasticModuliOperation(
                name=operation_name,
                hydration_operation_id=hydration_operation.id,
                image_filename=image_filename,
                output_directory=str(output_dir)
            )
            
            # Use the service to populate aggregate data from microstructure metadata
            populated_operation = self.elastic_moduli_service.populate_operation_from_microstructure(
                temp_operation, hydration_operation
            )
            
            # Update UI fields with the populated data
            self._update_ui_from_operation(populated_operation)
            
            self.logger.info(f"Auto-populated aggregate properties from microstructure metadata")
            
        except Exception as e:
            self.logger.warning(f"Could not auto-populate from microstructure metadata: {e}")
            # Continue without auto-population - user can fill manually
    
    def _update_ui_from_operation(self, operation: ElasticModuliOperation) -> None:
        """Update UI fields with values from an ElasticModuliOperation object."""
        # Update ITZ checkbox
        self.has_itz_check.set_active(operation.has_itz or False)
        
        # Update air content
        self.air_volume_spin.set_value(operation.air_volume_fraction or 0.0)
        
        # Update fine aggregate properties
        if operation.has_fine_aggregate:
            self.fine_agg_check.set_active(True)
            self._set_aggregate_controls_sensitive("fine", True)
            
            if operation.fine_aggregate_volume_fraction is not None:
                self.fine_volume_spin.set_value(operation.fine_aggregate_volume_fraction)
            if operation.fine_aggregate_grading_path:
                self.fine_grading_entry.set_text(operation.fine_aggregate_grading_path)
            if operation.fine_aggregate_bulk_modulus is not None:
                self.fine_bulk_spin.set_value(operation.fine_aggregate_bulk_modulus)
            if operation.fine_aggregate_shear_modulus is not None:
                self.fine_shear_spin.set_value(operation.fine_aggregate_shear_modulus)
                
            self.logger.info(f"Updated fine aggregate UI: {operation.fine_aggregate_display_name} "
                           f"(VF: {operation.fine_aggregate_volume_fraction:.3f})")
        else:
            self.fine_agg_check.set_active(False)
            self._set_aggregate_controls_sensitive("fine", False)
        
        # Update coarse aggregate properties
        if operation.has_coarse_aggregate:
            self.coarse_agg_check.set_active(True)
            self._set_aggregate_controls_sensitive("coarse", True)
            
            if operation.coarse_aggregate_volume_fraction is not None:
                self.coarse_volume_spin.set_value(operation.coarse_aggregate_volume_fraction)
            if operation.coarse_aggregate_grading_path:
                self.coarse_grading_entry.set_text(operation.coarse_aggregate_grading_path)
            if operation.coarse_aggregate_bulk_modulus is not None:
                self.coarse_bulk_spin.set_value(operation.coarse_aggregate_bulk_modulus)
            if operation.coarse_aggregate_shear_modulus is not None:
                self.coarse_shear_spin.set_value(operation.coarse_aggregate_shear_modulus)
                
            self.logger.info(f"Updated coarse aggregate UI: {operation.coarse_aggregate_display_name} "
                           f"(VF: {operation.coarse_aggregate_volume_fraction:.3f})")
        else:
            self.coarse_agg_check.set_active(False)
            self._set_aggregate_controls_sensitive("coarse", False)
        
        # Show a user-friendly message about what was auto-populated
        populated_items = []
        if operation.has_fine_aggregate:
            populated_items.append(f"fine aggregate ({operation.fine_aggregate_display_name})")
        if operation.has_coarse_aggregate:
            populated_items.append(f"coarse aggregate ({operation.coarse_aggregate_display_name})")
        if operation.air_volume_fraction and operation.air_volume_fraction > 0:
            populated_items.append(f"air content ({operation.air_volume_fraction:.1%})")
        if operation.has_itz:
            populated_items.append("ITZ calculations")
            
        if populated_items:
            message = f"Auto-populated from microstructure: {', '.join(populated_items)}"
            self.logger.info(message)
            # You could show this message to the user via a temporary info bar or status message
    
    def _set_aggregate_controls_sensitive(self, agg_type: str, sensitive: bool) -> None:
        """Enable/disable aggregate controls based on checkbox state."""
        if agg_type == "fine":
            controls = [self.fine_volume_spin, self.fine_grading_entry, 
                       self.fine_bulk_spin, self.fine_shear_spin]
        else:
            controls = [self.coarse_volume_spin, self.coarse_grading_entry,
                       self.coarse_bulk_spin, self.coarse_shear_spin]
        
        for control in controls:
            if control:
                control.set_sensitive(sensitive)
    
    def _on_fine_aggregate_toggled(self, checkbox: Gtk.CheckButton) -> None:
        """Handle fine aggregate checkbox toggle."""
        self._set_aggregate_controls_sensitive("fine", checkbox.get_active())
    
    def _on_coarse_aggregate_toggled(self, checkbox: Gtk.CheckButton) -> None:
        """Handle coarse aggregate checkbox toggle."""
        self._set_aggregate_controls_sensitive("coarse", checkbox.get_active())
    
    def _on_browse_output_dir(self, button: Gtk.Button) -> None:
        """Handle output directory browse button."""
        dialog = Gtk.FileChooserDialog(
            title="Select Output Directory",
            parent=self.main_window,
            action=Gtk.FileChooserAction.SELECT_FOLDER
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_SELECT, Gtk.ResponseType.OK
        )
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.output_dir_entry.set_text(dialog.get_filename())
        
        dialog.destroy()
    
    def _on_browse_pimg_file(self, button: Gtk.Button) -> None:
        """Handle pimg file browse button."""
        dialog = Gtk.FileChooserDialog(
            title="Select Pimg File",
            parent=self.main_window,
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )
        
        # Add file filter
        file_filter = Gtk.FileFilter()
        file_filter.set_name("Pimg files")
        file_filter.add_pattern("*.pimg")
        dialog.add_filter(file_filter)
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.pimg_file_entry.set_text(dialog.get_filename())
        
        dialog.destroy()
    
    def _on_browse_grading_file(self, button: Gtk.Button, agg_type: str) -> None:
        """Handle grading file browse button."""
        dialog = Gtk.FileChooserDialog(
            title=f"Select {agg_type.title()} Aggregate Grading File",
            parent=self.main_window,
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            if agg_type == "fine":
                self.fine_grading_entry.set_text(filename)
            else:
                self.coarse_grading_entry.set_text(filename)
        
        dialog.destroy()
    
    def _on_generate_input_file(self, button: Gtk.Button) -> None:
        """Handle generate input file button."""
        try:
            operation = self._create_operation_from_form()
            if not operation:
                return
            
            # Generate input file
            output_dir = self.output_dir_entry.get_text().strip()
            if not output_dir:
                self._show_error_dialog("Output directory is required")
                return
            
            input_file_path = self.elastic_moduli_service.generate_elastic_input_file(
                operation, output_dir
            )
            
            self._show_info_dialog(f"Input file generated successfully:\n{input_file_path}")
            
        except Exception as e:
            self.logger.error(f"Error generating input file: {e}")
            self._show_error_dialog(f"Failed to generate input file:\n{str(e)}")
    
    def _on_start_calculation(self, button: Gtk.Button) -> None:
        """Handle start calculation button with Phase 3 clean naming and lineage."""
        try:
            # Phase 3: Clean naming validation
            operation_name = self.operation_name_entry.get_text().strip()
            if not operation_name:
                self._show_error_dialog("Please enter an operation name")
                return
            
            # Validate form and create operation object
            operation = self._create_operation_from_form()
            if not operation:
                return
            
            # Phase 3: Capture all UI parameters for reproducibility
            ui_parameters = self._capture_elastic_ui_parameters()
            
            # Phase 3: Find parent hydration operation for lineage
            hydration_id = self.hydration_combo.get_active_id()
            parent_operation_id = int(hydration_id) if hydration_id else None
            
            # Phase 3: Create general Operation with lineage and UI parameters
            general_operation = self._create_elastic_operation(
                operation_name, ui_parameters, parent_operation_id
            )
            
            # Create specific ElasticModuliOperation linked to general operation
            saved_operation = self.elastic_moduli_service.create_operation(
                name=operation_name,
                hydration_operation_id=operation.hydration_operation_id,
                description=operation.description,
                general_operation_id=general_operation.id if general_operation else None,
                **operation.to_dict()
            )
            
            self._show_info_dialog(f"Elastic moduli operation '{operation_name}' created successfully.\nCheck the Operations Tool to monitor progress.")
            self.logger.info(f"Phase 3: Created elastic operation '{operation_name}' with lineage to hydration operation {parent_operation_id}")
            
        except Exception as e:
            self.logger.error(f"Error starting calculation: {e}")
            self._show_error_dialog(f"Failed to start calculation:\n{str(e)}")
    
    def _on_clear_form(self, button: Gtk.Button) -> None:
        """Handle clear form button."""
        # Reset all form fields
        self.hydration_combo.set_active(-1)
        self.operation_name_entry.set_text("")
        self.image_filename_entry.set_text("")
        self.output_dir_entry.set_text("")
        self.pimg_file_entry.set_text("")
        self.has_itz_check.set_active(False)
        self.air_volume_spin.set_value(0.0)
        
        # Reset aggregate controls
        self.fine_agg_check.set_active(False)
        self.fine_volume_spin.set_value(0.0)
        self.fine_grading_entry.set_text("")
        self.fine_bulk_spin.set_value(37.0)
        self.fine_shear_spin.set_value(44.0)
        
        self.coarse_agg_check.set_active(False)
        self.coarse_volume_spin.set_value(0.0)
        self.coarse_grading_entry.set_text("")
        self.coarse_bulk_spin.set_value(37.0)
        self.coarse_shear_spin.set_value(44.0)
        
        # Disable aggregate controls
        self._set_aggregate_controls_sensitive("fine", False)
        self._set_aggregate_controls_sensitive("coarse", False)
    
    def _create_operation_from_form(self) -> Optional[ElasticModuliOperation]:
        """Create ElasticModuliOperation from form data."""
        # Validate required fields
        errors = []
        
        hydration_id = self.hydration_combo.get_active_id()
        if not hydration_id or hydration_id == "":
            errors.append("Please select a hydration operation")
        
        operation_name = self.operation_name_entry.get_text().strip()
        if not operation_name:
            errors.append("Operation name is required")
        
        image_filename = self.image_filename_entry.get_text().strip()
        if not image_filename:
            errors.append("Image filename is required")
        
        output_directory = self.output_dir_entry.get_text().strip()
        if not output_directory:
            errors.append("Output directory is required")
        
        if errors:
            self._show_error_dialog("Please fix the following errors:\n\n" + "\n".join(f"• {error}" for error in errors))
            return None
        
        # Create operation object
        operation = ElasticModuliOperation(
            name=operation_name,
            hydration_operation_id=int(hydration_id),
            image_filename=image_filename,
            early_age_connection=1,
            has_itz=self.has_itz_check.get_active(),
            output_directory=output_directory,
            pimg_file_path=self.pimg_file_entry.get_text().strip() or None,
            
            # Fine aggregate
            has_fine_aggregate=self.fine_agg_check.get_active(),
            fine_aggregate_volume_fraction=self.fine_volume_spin.get_value() if self.fine_agg_check.get_active() else None,
            fine_aggregate_grading_path=self.fine_grading_entry.get_text().strip() or None if self.fine_agg_check.get_active() else None,
            fine_aggregate_bulk_modulus=self.fine_bulk_spin.get_value() if self.fine_agg_check.get_active() else None,
            fine_aggregate_shear_modulus=self.fine_shear_spin.get_value() if self.fine_agg_check.get_active() else None,
            
            # Coarse aggregate
            has_coarse_aggregate=self.coarse_agg_check.get_active(),
            coarse_aggregate_volume_fraction=self.coarse_volume_spin.get_value() if self.coarse_agg_check.get_active() else None,
            coarse_aggregate_grading_path=self.coarse_grading_entry.get_text().strip() or None if self.coarse_agg_check.get_active() else None,
            coarse_aggregate_bulk_modulus=self.coarse_bulk_spin.get_value() if self.coarse_agg_check.get_active() else None,
            coarse_aggregate_shear_modulus=self.coarse_shear_spin.get_value() if self.coarse_agg_check.get_active() else None,
            
            # Air content
            air_volume_fraction=self.air_volume_spin.get_value()
        )
        
        # Validate the operation
        validation_errors = self.elastic_moduli_service.validate_operation_parameters(operation)
        if validation_errors:
            self._show_error_dialog("Validation errors:\n\n" + "\n".join(f"• {error}" for error in validation_errors))
            return None
        
        return operation
    
    def _show_error_dialog(self, message: str) -> None:
        """Show error dialog."""
        dialog = Gtk.MessageDialog(
            parent=self.main_window,
            flags=Gtk.DialogFlags.MODAL,
            type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            message_format=message
        )
        dialog.run()
        dialog.destroy()
    
    def _show_info_dialog(self, message: str) -> None:
        """Show information dialog."""
        dialog = Gtk.MessageDialog(
            parent=self.main_window,
            flags=Gtk.DialogFlags.MODAL,
            type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            message_format=message
        )
        dialog.run()
        dialog.destroy()
    
    def refresh(self) -> None:
        """Refresh the panel data."""
        self._load_available_hydration_operations()
    
    def get_panel_name(self) -> str:
        """Get the panel name for tab display."""
        return "Elastic Moduli"
    
    # Phase 3: Clean Naming and Lineage Methods
    
    def _capture_elastic_ui_parameters(self) -> Dict[str, Any]:
        """Capture all UI parameters for storage with operation (Phase 3)."""
        try:
            # Get selected hydration operation details
            hydration_id = self.hydration_combo.get_active_id()
            hydration_name = ""
            if hydration_id:
                model = self.hydration_combo.get_model()
                iter = self.hydration_combo.get_active_iter()
                if iter:
                    hydration_name = model.get_value(iter, 1)  # Get operation name from combo
            
            ui_params = {
                # Basic operation information
                'operation_name': self.operation_name_entry.get_text().strip(),
                'hydration_operation_id': hydration_id,
                'hydration_operation_name': hydration_name,
                
                # File settings
                'image_filename': self.image_filename_entry.get_text().strip(),
                'output_directory': self.output_dir_entry.get_text().strip(),
                'pimg_file_path': self.pimg_file_entry.get_text().strip(),
                
                # Microstructure settings
                'has_itz': self.has_itz_check.get_active(),
                'air_volume_fraction': self.air_volume_spin.get_value(),
                
                # Fine aggregate settings
                'has_fine_aggregate': self.fine_agg_check.get_active(),
                'fine_aggregate_settings': {
                    'volume_fraction': self.fine_volume_spin.get_value(),
                    'grading_file': self.fine_grading_entry.get_text().strip(),
                    'bulk_modulus': self.fine_bulk_spin.get_value(),
                    'shear_modulus': self.fine_shear_spin.get_value()
                } if self.fine_agg_check.get_active() else None,
                
                # Coarse aggregate settings
                'has_coarse_aggregate': self.coarse_agg_check.get_active(),
                'coarse_aggregate_settings': {
                    'volume_fraction': self.coarse_volume_spin.get_value(),
                    'grading_file': self.coarse_grading_entry.get_text().strip(),
                    'bulk_modulus': self.coarse_bulk_spin.get_value(),
                    'shear_modulus': self.coarse_shear_spin.get_value()
                } if self.coarse_agg_check.get_active() else None,
                
                # Metadata
                'timestamp': datetime.now().isoformat(),
                'panel_version': '1.0'
            }
            
            return ui_params
            
        except Exception as e:
            self.logger.error(f"Error capturing UI parameters: {e}")
            return {}
    
    def _create_elastic_operation(self, operation_name: str, ui_parameters: Dict[str, Any], 
                                 parent_operation_id: Optional[int]) -> Optional['Operation']:
        """Create elastic moduli operation in database with UI parameters and lineage (Phase 3)."""
        try:
            from app.database.service import DatabaseService
            from app.models.operation import Operation, OperationType, OperationStatus
            
            db_service = DatabaseService()
            with db_service.get_session() as session:
                # Create the general operation record with Phase 3 features
                operation = Operation(
                    name=operation_name,  # Clean user-defined name
                    operation_type=OperationType.ELASTIC_MODULI.value,
                    status=OperationStatus.QUEUED.value,
                    stored_ui_parameters=ui_parameters,  # Complete UI state for reproducibility
                    parent_operation_id=parent_operation_id  # Phase 3: Lineage to hydration operation
                )
                
                session.add(operation)
                session.commit()
                session.refresh(operation)
                
                self.logger.info(f"Phase 3: Created elastic operation: {operation_name} (ID: {operation.id})")
                if parent_operation_id:
                    self.logger.info(f"Phase 3: Linked to parent hydration operation ID: {parent_operation_id}")
                
                return operation
                
        except Exception as e:
            self.logger.error(f"Error creating elastic operation: {e}")
            return None
    
    def _get_parent_microstructure_name(self, hydration_operation: Operation) -> Optional[str]:
        """Get the parent microstructure operation name through lineage chain."""
        try:
            from app.database.service import DatabaseService
            from app.models.operation import Operation, OperationType
            
            db_service = DatabaseService()
            with db_service.get_session() as session:
                # Get the parent of the hydration operation (should be microstructure)
                if hydration_operation.parent_operation_id:
                    parent_op = session.query(Operation).filter_by(
                        id=hydration_operation.parent_operation_id
                    ).first()
                    
                    if parent_op and parent_op.operation_type == OperationType.MICROSTRUCTURE.value:
                        return parent_op.name
                    else:
                        self.logger.warning(f"Parent operation {hydration_operation.parent_operation_id} is not a microstructure operation")
                else:
                    # Fallback: Try to extract from stored UI parameters if available
                    if hydration_operation.stored_ui_parameters:
                        params = hydration_operation.stored_ui_parameters
                        if 'source_microstructure' in params:
                            return params['source_microstructure'].get('name')
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting parent microstructure name: {e}")
            return None
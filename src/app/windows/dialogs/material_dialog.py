#!/usr/bin/env python3
"""
Material Dialog for VCCTL

Provides dialogs for adding and editing materials of different types.
"""

import gi
import logging
from typing import TYPE_CHECKING, Optional, Dict, Any, List, Callable
from abc import ABC, abstractmethod

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, Pango

if TYPE_CHECKING:
    from app.windows.main_window import VCCTLMainWindow

from app.services.service_container import get_service_container


# Create a compatible metaclass that inherits from both GTK and ABC metaclasses
class MaterialDialogMeta(type(Gtk.Dialog), type(ABC)):
    pass


class MaterialDialogBase(Gtk.Dialog, ABC, metaclass=MaterialDialogMeta):
    """Base class for material dialogs."""
    
    def __init__(self, parent: 'VCCTLMainWindow', material_type: str, material_data: Optional[Dict[str, Any]] = None):
        """Initialize the material dialog."""
        self.material_type = material_type
        self.material_data = material_data
        self.is_edit_mode = material_data is not None
        
        title = f"{'Edit' if self.is_edit_mode else 'Add'} {material_type.title().replace('_', ' ')}"
        super().__init__(title=title, transient_for=parent, flags=0)
        
        self.parent_window = parent
        self.logger = logging.getLogger(f'VCCTL.MaterialDialog.{material_type}')
        self.service_container = get_service_container()
        
        # Dialog configuration
        self.set_default_size(600, 500)
        self.set_resizable(True)
        self.set_modal(True)
        
        # Validation state
        self.validation_errors = {}
        self.validation_warnings = {}
        
        # Setup UI
        self._setup_dialog()
        self._setup_ui()
        self._connect_signals()
        
        # Load data if editing
        if self.is_edit_mode:
            self._load_material_data()
        
        self.logger.debug(f"Material dialog initialized for {material_type}")
    
    def _setup_dialog(self) -> None:
        """Setup dialog buttons and basic configuration."""
        # Add dialog buttons
        self.add_button("Cancel", Gtk.ResponseType.CANCEL)
        self.save_button = self.add_button("Save", Gtk.ResponseType.OK)
        self.save_button.get_style_context().add_class("suggested-action")
        
        # Set default response
        self.set_default_response(Gtk.ResponseType.OK)
    
    def _setup_ui(self) -> None:
        """Setup the dialog UI."""
        content_area = self.get_content_area()
        content_area.set_spacing(0)
        
        # Create notebook for organizing form sections
        self.notebook = Gtk.Notebook()
        self.notebook.set_show_tabs(True)
        self.notebook.set_show_border(False)
        
        # Create form sections
        self._create_basic_info_tab()
        self._create_properties_tab()
        self._create_advanced_tab()
        
        content_area.pack_start(self.notebook, True, True, 0)
        
        # Create validation message area
        self._create_validation_area(content_area)
        
        content_area.show_all()
    
    def _create_basic_info_tab(self) -> None:
        """Create the basic information tab."""
        # Scrolled window for form
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        # Form container
        form_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        form_box.set_margin_top(20)
        form_box.set_margin_bottom(20)
        form_box.set_margin_left(20)
        form_box.set_margin_right(20)
        
        # Material identification section
        id_frame = Gtk.Frame(label="Material Identification")
        id_grid = Gtk.Grid()
        id_grid.set_margin_top(10)
        id_grid.set_margin_bottom(10)
        id_grid.set_margin_left(15)
        id_grid.set_margin_right(15)
        id_grid.set_row_spacing(10)
        id_grid.set_column_spacing(15)
        
        # Name field
        name_label = Gtk.Label("Name:")
        name_label.set_halign(Gtk.Align.END)
        name_label.get_style_context().add_class("form-label")
        self.name_entry = Gtk.Entry()
        self.name_entry.set_placeholder_text("Enter material name...")
        self.name_entry.set_hexpand(True)
        
        id_grid.attach(name_label, 0, 0, 1, 1)
        id_grid.attach(self.name_entry, 1, 0, 2, 1)
        
        # Description field
        desc_label = Gtk.Label("Description:")
        desc_label.set_halign(Gtk.Align.END)
        desc_label.set_valign(Gtk.Align.START)
        desc_label.get_style_context().add_class("form-label")
        
        desc_scrolled = Gtk.ScrolledWindow()
        desc_scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        desc_scrolled.set_size_request(-1, 80)
        
        self.description_textview = Gtk.TextView()
        self.description_textview.set_wrap_mode(Gtk.WrapMode.WORD)
        self.description_buffer = self.description_textview.get_buffer()
        self.description_buffer.set_text("Enter material description...")
        desc_scrolled.add(self.description_textview)
        
        id_grid.attach(desc_label, 0, 1, 1, 1)
        id_grid.attach(desc_scrolled, 1, 1, 2, 1)
        
        # Source field
        source_label = Gtk.Label("Source:")
        source_label.set_halign(Gtk.Align.END)
        source_label.get_style_context().add_class("form-label")
        self.source_entry = Gtk.Entry()
        self.source_entry.set_placeholder_text("Supplier, manufacturer, or origin...")
        
        id_grid.attach(source_label, 0, 2, 1, 1)
        id_grid.attach(self.source_entry, 1, 2, 2, 1)
        
        id_frame.add(id_grid)
        form_box.pack_start(id_frame, False, False, 0)
        
        # Physical properties section
        props_frame = Gtk.Frame(label="Physical Properties")
        props_grid = Gtk.Grid()
        props_grid.set_margin_top(10)
        props_grid.set_margin_bottom(10)
        props_grid.set_margin_left(15)
        props_grid.set_margin_right(15)
        props_grid.set_row_spacing(10)
        props_grid.set_column_spacing(15)
        
        # Specific gravity
        sg_label = Gtk.Label("Specific Gravity:")
        sg_label.set_halign(Gtk.Align.END)
        sg_label.get_style_context().add_class("form-label")
        
        self.specific_gravity_spin = Gtk.SpinButton.new_with_range(1.0, 5.0, 0.01)
        self.specific_gravity_spin.set_digits(3)
        self.specific_gravity_spin.set_value(2.65)  # Default for cement
        
        sg_unit_label = Gtk.Label("g/cm³")
        sg_unit_label.get_style_context().add_class("dim-label")
        
        props_grid.attach(sg_label, 0, 0, 1, 1)
        props_grid.attach(self.specific_gravity_spin, 1, 0, 1, 1)
        props_grid.attach(sg_unit_label, 2, 0, 1, 1)
        
        # Add material-specific fields
        self._add_material_specific_fields(props_grid, 1)
        
        props_frame.add(props_grid)
        form_box.pack_start(props_frame, False, False, 0)
        
        scrolled.add(form_box)
        self.notebook.append_page(scrolled, Gtk.Label("Basic Info"))
    
    @abstractmethod
    def _add_material_specific_fields(self, grid: Gtk.Grid, start_row: int) -> int:
        """Add material-specific fields to the basic properties grid.
        
        Args:
            grid: Grid to add fields to
            start_row: Starting row number
            
        Returns:
            Next available row number
        """
        pass
    
    def _create_properties_tab(self) -> None:
        """Create the properties tab."""
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        # Properties container
        props_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        props_box.set_margin_top(20)
        props_box.set_margin_bottom(20)
        props_box.set_margin_left(20)
        props_box.set_margin_right(20)
        
        # Add material-specific property sections
        self._add_property_sections(props_box)
        
        scrolled.add(props_box)
        self.notebook.append_page(scrolled, Gtk.Label("Properties"))
    
    @abstractmethod
    def _add_property_sections(self, container: Gtk.Box) -> None:
        """Add material-specific property sections.
        
        Args:
            container: Container to add sections to
        """
        pass
    
    def _create_advanced_tab(self) -> None:
        """Create the advanced properties tab."""
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        # Advanced container
        advanced_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        advanced_box.set_margin_top(20)
        advanced_box.set_margin_bottom(20)
        advanced_box.set_margin_left(20)
        advanced_box.set_margin_right(20)
        
        # Metadata section
        meta_frame = Gtk.Frame(label="Metadata")
        meta_grid = Gtk.Grid()
        meta_grid.set_margin_top(10)
        meta_grid.set_margin_bottom(10)
        meta_grid.set_margin_left(15)
        meta_grid.set_margin_right(15)
        meta_grid.set_row_spacing(10)
        meta_grid.set_column_spacing(15)
        
        # Notes field
        notes_label = Gtk.Label("Notes:")
        notes_label.set_halign(Gtk.Align.END)
        notes_label.set_valign(Gtk.Align.START)
        notes_label.get_style_context().add_class("form-label")
        
        notes_scrolled = Gtk.ScrolledWindow()
        notes_scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        notes_scrolled.set_size_request(-1, 120)
        
        self.notes_textview = Gtk.TextView()
        self.notes_textview.set_wrap_mode(Gtk.WrapMode.WORD)
        self.notes_buffer = self.notes_textview.get_buffer()
        notes_scrolled.add(self.notes_textview)
        
        meta_grid.attach(notes_label, 0, 0, 1, 1)
        meta_grid.attach(notes_scrolled, 1, 0, 2, 1)
        
        meta_frame.add(meta_grid)
        advanced_box.pack_start(meta_frame, False, False, 0)
        
        # Add material-specific advanced sections
        self._add_advanced_sections(advanced_box)
        
        scrolled.add(advanced_box)
        self.notebook.append_page(scrolled, Gtk.Label("Advanced"))
    
    @abstractmethod
    def _add_advanced_sections(self, container: Gtk.Box) -> None:
        """Add material-specific advanced sections.
        
        Args:
            container: Container to add sections to
        """
        pass
    
    def _create_validation_area(self, content_area: Gtk.Box) -> None:
        """Create validation message area."""
        # Validation revealer
        self.validation_revealer = Gtk.Revealer()
        self.validation_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)
        
        # Validation info bar
        self.validation_infobar = Gtk.InfoBar()
        self.validation_infobar.set_show_close_button(True)
        
        # Validation content
        validation_content = self.validation_infobar.get_content_area()
        
        self.validation_icon = Gtk.Image()
        validation_content.pack_start(self.validation_icon, False, False, 0)
        
        self.validation_label = Gtk.Label()
        self.validation_label.set_line_wrap(True)
        self.validation_label.set_max_width_chars(60)
        validation_content.pack_start(self.validation_label, True, True, 0)
        
        self.validation_revealer.add(self.validation_infobar)
        content_area.pack_start(self.validation_revealer, False, False, 0)
        
        # Connect close signal
        self.validation_infobar.connect('response', lambda w, r: self.validation_revealer.set_reveal_child(False))
    
    def _connect_signals(self) -> None:
        """Connect dialog signals."""
        # Dialog response
        self.connect('response', self._on_response)
        
        # Validation triggers
        self.name_entry.connect('changed', self._on_field_changed)
        self.specific_gravity_spin.connect('value-changed', self._on_field_changed)
        self.description_buffer.connect('changed', self._on_field_changed)
        
        # Connect material-specific signals
        self._connect_material_signals()
    
    @abstractmethod
    def _connect_material_signals(self) -> None:
        """Connect material-specific signals."""
        pass
    
    def _load_material_data(self) -> None:
        """Load material data into form fields."""
        if not self.material_data:
            return
        
        try:
            # Load basic fields
            self.name_entry.set_text(self.material_data.get('name', ''))
            
            description = self.material_data.get('description', '')
            if description:
                self.description_buffer.set_text(description)
            
            source = self.material_data.get('source', '')
            if source:
                self.source_entry.set_text(source)
            
            specific_gravity = self.material_data.get('specific_gravity', 2.65)
            self.specific_gravity_spin.set_value(float(specific_gravity))
            
            notes = self.material_data.get('notes', '')
            if notes:
                self.notes_buffer.set_text(notes)
            
            # Load material-specific data
            self._load_material_specific_data()
            
        except Exception as e:
            self.logger.error(f"Failed to load material data: {e}")
    
    @abstractmethod
    def _load_material_specific_data(self) -> None:
        """Load material-specific data into form fields."""
        pass
    
    def _on_field_changed(self, widget) -> None:
        """Handle field change events."""
        # Clear previous validation for this field
        field_name = getattr(widget, 'field_name', None)
        if field_name and field_name in self.validation_errors:
            del self.validation_errors[field_name]
        
        # Validate the field
        self._validate_field(widget)
        
        # Update validation display
        self._update_validation_display()
    
    def _validate_field(self, widget) -> None:
        """Validate a specific field."""
        if widget == self.name_entry:
            self._validate_name()
        elif widget == self.specific_gravity_spin:
            self._validate_specific_gravity()
        
        # Validate material-specific fields
        self._validate_material_specific_field(widget)
    
    def _validate_name(self) -> None:
        """Validate the name field."""
        name = self.name_entry.get_text().strip()
        
        if not name:
            self.validation_errors['name'] = "Material name is required"
        elif len(name) < 2:
            self.validation_errors['name'] = "Material name must be at least 2 characters"
        elif len(name) > 100:
            self.validation_errors['name'] = "Material name cannot exceed 100 characters"
        else:
            # Check for duplicate names (if not in edit mode or name changed)
            if not self.is_edit_mode or name != self.material_data.get('name', ''):
                if self._check_name_exists(name):
                    self.validation_errors['name'] = f"A {self.material_type} named '{name}' already exists"
    
    def _validate_specific_gravity(self) -> None:
        """Validate the specific gravity field."""
        sg = self.specific_gravity_spin.get_value()
        
        if sg <= 0:
            self.validation_errors['specific_gravity'] = "Specific gravity must be positive"
        elif sg < 1.0:
            self.validation_warnings['specific_gravity'] = "Specific gravity less than 1.0 is unusual"
        elif sg > 5.0:
            self.validation_warnings['specific_gravity'] = "Specific gravity greater than 5.0 is unusual"
    
    @abstractmethod
    def _validate_material_specific_field(self, widget) -> None:
        """Validate material-specific fields."""
        pass
    
    def _check_name_exists(self, name: str) -> bool:
        """Check if a material with the given name already exists."""
        try:
            service = self._get_material_service()
            if service:
                existing = service.get_by_name(name)
                return existing is not None
        except Exception as e:
            self.logger.warning(f"Could not check for existing material name: {e}")
        return False
    
    def _get_material_service(self):
        """Get the appropriate service for this material type."""
        service_mapping = {
            'cement': self.service_container.cement_service,
            'aggregate': self.service_container.aggregate_service,
            'fly_ash': self.service_container.fly_ash_service,
            'slag': self.service_container.slag_service,
            'inert_filler': self.service_container.inert_filler_service
        }
        return service_mapping.get(self.material_type)
    
    def _update_validation_display(self) -> None:
        """Update the validation message display."""
        # Determine if there are errors or warnings
        has_errors = bool(self.validation_errors)
        has_warnings = bool(self.validation_warnings)
        
        if has_errors or has_warnings:
            # Show validation messages
            if has_errors:
                self.validation_infobar.set_message_type(Gtk.MessageType.ERROR)
                self.validation_icon.set_from_icon_name("dialog-error", Gtk.IconSize.BUTTON)
                
                # Show first error
                first_error = next(iter(self.validation_errors.values()))
                self.validation_label.set_text(f"Error: {first_error}")
                
                # Disable save button
                self.save_button.set_sensitive(False)
                
            elif has_warnings:
                self.validation_infobar.set_message_type(Gtk.MessageType.WARNING)
                self.validation_icon.set_from_icon_name("dialog-warning", Gtk.IconSize.BUTTON)
                
                # Show first warning
                first_warning = next(iter(self.validation_warnings.values()))
                self.validation_label.set_text(f"Warning: {first_warning}")
                
                # Keep save button enabled for warnings
                self.save_button.set_sensitive(True)
            
            self.validation_revealer.set_reveal_child(True)
        else:
            # Hide validation messages
            self.validation_revealer.set_reveal_child(False)
            self.save_button.set_sensitive(True)
    
    def _validate_all(self) -> bool:
        """Validate all form fields."""
        self.validation_errors.clear()
        self.validation_warnings.clear()
        
        # Validate basic fields
        self._validate_name()
        self._validate_specific_gravity()
        
        # Validate material-specific fields
        self._validate_all_material_fields()
        
        # Update display
        self._update_validation_display()
        
        return not bool(self.validation_errors)
    
    @abstractmethod
    def _validate_all_material_fields(self) -> None:
        """Validate all material-specific fields."""
        pass
    
    def _collect_form_data(self) -> Dict[str, Any]:
        """Collect all form data into a dictionary."""
        # Get text from description buffer
        desc_start = self.description_buffer.get_start_iter()
        desc_end = self.description_buffer.get_end_iter()
        description = self.description_buffer.get_text(desc_start, desc_end, False)
        
        # Get text from notes buffer
        notes_start = self.notes_buffer.get_start_iter()
        notes_end = self.notes_buffer.get_end_iter()
        notes = self.notes_buffer.get_text(notes_start, notes_end, False)
        
        data = {
            'name': self.name_entry.get_text().strip(),
            'description': description.strip() if description.strip() else None,
            'source': self.source_entry.get_text().strip() if self.source_entry.get_text().strip() else None,
            'specific_gravity': self.specific_gravity_spin.get_value(),
            'notes': notes.strip() if notes.strip() else None
        }
        
        # Add material-specific data
        material_data = self._collect_material_specific_data()
        data.update(material_data)
        
        return data
    
    @abstractmethod
    def _collect_material_specific_data(self) -> Dict[str, Any]:
        """Collect material-specific form data."""
        pass
    
    def _save_material(self) -> bool:
        """Save the material data."""
        try:
            # Validate all fields
            if not self._validate_all():
                return False
            
            # Collect form data
            data = self._collect_form_data()
            
            # Get service
            service = self._get_material_service()
            if not service:
                raise Exception(f"No service available for {self.material_type}")
            
            if self.is_edit_mode:
                # Update existing material
                material_id = self.material_data['id']
                updated_material = service.update(material_id, data)
                self.logger.info(f"Updated {self.material_type}: {updated_material.name}")
            else:
                # Create new material
                created_material = service.create(data)
                self.logger.info(f"Created {self.material_type}: {created_material.name}")
            
            # Show success message
            action = "updated" if self.is_edit_mode else "created"
            self.parent_window.update_status(f"Material {action} successfully", "success", 3)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save material: {e}")
            
            # Show error in validation area
            self.validation_errors['save'] = str(e)
            self._update_validation_display()
            
            return False
    
    def _on_response(self, widget: Gtk.Dialog, response_id: int) -> None:
        """Handle dialog response."""
        if response_id == Gtk.ResponseType.OK:
            # Try to save
            if self._save_material():
                # Close dialog on successful save
                self.destroy()
            # Stay open if save failed
        else:
            # Cancel or close
            self.destroy()


class CementDialog(MaterialDialogBase):
    """Dialog for cement materials."""
    
    def __init__(self, parent: 'VCCTLMainWindow', material_data: Optional[Dict[str, Any]] = None):
        super().__init__(parent, "cement", material_data)
    
    def _add_material_specific_fields(self, grid: Gtk.Grid, start_row: int) -> int:
        """Add cement-specific fields."""
        row = start_row
        
        # Blaine fineness
        blaine_label = Gtk.Label("Blaine Fineness:")
        blaine_label.set_halign(Gtk.Align.END)
        blaine_label.get_style_context().add_class("form-label")
        
        self.blaine_spin = Gtk.SpinButton.new_with_range(200, 600, 1)
        self.blaine_spin.set_value(350)  # Default value
        
        blaine_unit_label = Gtk.Label("m²/kg")
        blaine_unit_label.get_style_context().add_class("dim-label")
        
        grid.attach(blaine_label, 0, row, 1, 1)
        grid.attach(self.blaine_spin, 1, row, 1, 1)
        grid.attach(blaine_unit_label, 2, row, 1, 1)
        row += 1
        
        return row
    
    def _add_property_sections(self, container: Gtk.Box) -> None:
        """Add cement-specific property sections."""
        # Chemical composition section
        comp_frame = Gtk.Frame(label="Chemical Composition (%)")
        comp_grid = Gtk.Grid()
        comp_grid.set_margin_top(10)
        comp_grid.set_margin_bottom(10)
        comp_grid.set_margin_left(15)
        comp_grid.set_margin_right(15)
        comp_grid.set_row_spacing(10)
        comp_grid.set_column_spacing(15)
        
        # Phase composition with enhanced layout
        phases = [
            ("C₃S:", "c3s", 50.0, "Tricalcium silicate - main binding phase"),
            ("C₂S:", "c2s", 25.0, "Dicalcium silicate - slow hydrating phase"),
            ("C₃A:", "c3a", 8.0, "Tricalcium aluminate - rapid hydrating"),
            ("C₄AF:", "c4af", 10.0, "Tetracalcium aluminoferrite - moderate hydrating")
        ]
        
        self.phase_spins = {}
        for i, (label_text, phase_key, default_value, tooltip) in enumerate(phases):
            label = Gtk.Label(label_text)
            label.set_halign(Gtk.Align.END)
            label.get_style_context().add_class("form-label")
            label.set_tooltip_text(tooltip)
            
            spin = Gtk.SpinButton.new_with_range(0.0, 100.0, 0.1)
            spin.set_digits(1)
            spin.set_value(default_value)
            spin.set_tooltip_text(tooltip)
            
            unit_label = Gtk.Label("%")
            unit_label.get_style_context().add_class("dim-label")
            
            comp_grid.attach(label, 0, i, 1, 1)
            comp_grid.attach(spin, 1, i, 1, 1)
            comp_grid.attach(unit_label, 2, i, 1, 1)
            
            self.phase_spins[phase_key] = spin
        
        # Add sum display
        sum_label = Gtk.Label("Total:")
        sum_label.set_halign(Gtk.Align.END)
        sum_label.get_style_context().add_class("form-label")
        sum_label.set_markup("<b>Total:</b>")
        
        self.sum_display = Gtk.Label("93.0")
        self.sum_display.set_halign(Gtk.Align.START)
        self.sum_display.get_style_context().add_class("sum-display")
        
        sum_unit_label = Gtk.Label("%")
        sum_unit_label.get_style_context().add_class("dim-label")
        
        comp_grid.attach(sum_label, 0, len(phases), 1, 1)
        comp_grid.attach(self.sum_display, 1, len(phases), 1, 1)
        comp_grid.attach(sum_unit_label, 2, len(phases), 1, 1)
        
        comp_frame.add(comp_grid)
        container.pack_start(comp_frame, False, False, 0)
        
        # Physical properties section
        self._add_physical_properties_section(container)
        
        # Particle size distribution section
        self._add_psd_section(container)
        
    def _add_physical_properties_section(self, container: Gtk.Box) -> None:
        """Add physical properties calculation section."""
        phys_frame = Gtk.Frame(label="Physical Properties")
        phys_grid = Gtk.Grid()
        phys_grid.set_margin_top(10)
        phys_grid.set_margin_bottom(10)
        phys_grid.set_margin_left(15)
        phys_grid.set_margin_right(15)
        phys_grid.set_row_spacing(10)
        phys_grid.set_column_spacing(15)
        
        # Density calculation display
        density_label = Gtk.Label("Calculated Density:")
        density_label.set_halign(Gtk.Align.END)
        density_label.get_style_context().add_class("form-label")
        
        self.density_display = Gtk.Label("3.15")
        self.density_display.set_halign(Gtk.Align.START)
        self.density_display.get_style_context().add_class("calculated-value")
        
        density_unit_label = Gtk.Label("g/cm³")
        density_unit_label.get_style_context().add_class("dim-label")
        
        phys_grid.attach(density_label, 0, 0, 1, 1)
        phys_grid.attach(self.density_display, 1, 0, 1, 1)
        phys_grid.attach(density_unit_label, 2, 0, 1, 1)
        
        # Heat of hydration estimate
        heat_label = Gtk.Label("Heat of Hydration:")
        heat_label.set_halign(Gtk.Align.END)
        heat_label.get_style_context().add_class("form-label")
        
        self.heat_display = Gtk.Label("380")
        self.heat_display.set_halign(Gtk.Align.START)
        self.heat_display.get_style_context().add_class("calculated-value")
        
        heat_unit_label = Gtk.Label("J/g")
        heat_unit_label.get_style_context().add_class("dim-label")
        
        phys_grid.attach(heat_label, 0, 1, 1, 1)
        phys_grid.attach(self.heat_display, 1, 1, 1, 1)
        phys_grid.attach(heat_unit_label, 2, 1, 1, 1)
        
        phys_frame.add(phys_grid)
        container.pack_start(phys_frame, False, False, 0)
        
    def _add_psd_section(self, container: Gtk.Box) -> None:
        """Add particle size distribution section."""
        psd_frame = Gtk.Frame(label="Particle Size Distribution")
        psd_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        psd_box.set_margin_top(10)
        psd_box.set_margin_bottom(10)
        psd_box.set_margin_left(15)
        psd_box.set_margin_right(15)
        
        # PSD mode selection
        mode_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        mode_label = Gtk.Label("Distribution:")
        mode_label.set_halign(Gtk.Align.END)
        mode_label.get_style_context().add_class("form-label")
        mode_box.pack_start(mode_label, False, False, 0)
        
        self.psd_mode_combo = Gtk.ComboBoxText()
        self.psd_mode_combo.append("rosin_rammler", "Rosin-Rammler")
        self.psd_mode_combo.append("fuller", "Fuller-Thompson")
        self.psd_mode_combo.append("custom", "Custom Points")
        self.psd_mode_combo.set_active(0)
        mode_box.pack_start(self.psd_mode_combo, True, True, 0)
        
        psd_box.pack_start(mode_box, False, False, 0)
        
        # Create notebook for different PSD input methods
        self.psd_notebook = Gtk.Notebook()
        self.psd_notebook.set_show_tabs(False)  # We'll control this with the combo
        
        # Rosin-Rammler parameters
        self._create_rosin_rammler_tab()
        
        # Fuller-Thompson parameters  
        self._create_fuller_tab()
        
        # Custom points
        self._create_custom_psd_tab()
        
        psd_box.pack_start(self.psd_notebook, True, True, 0)
        
        # Connect mode change signal
        self.psd_mode_combo.connect('changed', self._on_psd_mode_changed)
        
        psd_frame.add(psd_box)
        container.pack_start(psd_frame, True, True, 0)
        
    def _create_rosin_rammler_tab(self) -> None:
        """Create Rosin-Rammler distribution parameters tab."""
        rr_grid = Gtk.Grid()
        rr_grid.set_row_spacing(10)
        rr_grid.set_column_spacing(15)
        rr_grid.set_margin_top(10)
        rr_grid.set_margin_bottom(10)
        
        # Mean diameter (D50)
        d50_label = Gtk.Label("D₅₀ (median):")
        d50_label.set_halign(Gtk.Align.END)
        d50_label.get_style_context().add_class("form-label")
        
        self.d50_spin = Gtk.SpinButton.new_with_range(1.0, 100.0, 0.1)
        self.d50_spin.set_digits(1)
        self.d50_spin.set_value(15.0)  # Typical for cement
        
        d50_unit = Gtk.Label("μm")
        d50_unit.get_style_context().add_class("dim-label")
        
        rr_grid.attach(d50_label, 0, 0, 1, 1)
        rr_grid.attach(self.d50_spin, 1, 0, 1, 1)
        rr_grid.attach(d50_unit, 2, 0, 1, 1)
        
        # Distribution uniformity (n)
        n_label = Gtk.Label("Uniformity (n):")
        n_label.set_halign(Gtk.Align.END)
        n_label.get_style_context().add_class("form-label")
        
        self.n_spin = Gtk.SpinButton.new_with_range(0.5, 5.0, 0.1)
        self.n_spin.set_digits(2)
        self.n_spin.set_value(1.1)  # Typical for cement
        
        n_unit = Gtk.Label("(dimensionless)")
        n_unit.get_style_context().add_class("dim-label")
        
        rr_grid.attach(n_label, 0, 1, 1, 1)
        rr_grid.attach(self.n_spin, 1, 1, 1, 1)
        rr_grid.attach(n_unit, 2, 1, 1, 1)
        
        self.psd_notebook.append_page(rr_grid, Gtk.Label("Rosin-Rammler"))
        
    def _create_fuller_tab(self) -> None:
        """Create Fuller-Thompson distribution parameters tab."""
        fuller_grid = Gtk.Grid()
        fuller_grid.set_row_spacing(10)
        fuller_grid.set_column_spacing(15)
        fuller_grid.set_margin_top(10)
        fuller_grid.set_margin_bottom(10)
        
        # Maximum size
        dmax_label = Gtk.Label("Maximum size:")
        dmax_label.set_halign(Gtk.Align.END)
        dmax_label.get_style_context().add_class("form-label")
        
        self.dmax_spin = Gtk.SpinButton.new_with_range(10.0, 200.0, 1.0)
        self.dmax_spin.set_value(100.0)
        
        dmax_unit = Gtk.Label("μm")
        dmax_unit.get_style_context().add_class("dim-label")
        
        fuller_grid.attach(dmax_label, 0, 0, 1, 1)
        fuller_grid.attach(self.dmax_spin, 1, 0, 1, 1)
        fuller_grid.attach(dmax_unit, 2, 0, 1, 1)
        
        # Exponent
        exp_label = Gtk.Label("Exponent:")
        exp_label.set_halign(Gtk.Align.END)
        exp_label.get_style_context().add_class("form-label")
        
        self.exp_spin = Gtk.SpinButton.new_with_range(0.1, 1.0, 0.05)
        self.exp_spin.set_digits(2)
        self.exp_spin.set_value(0.5)  # Fuller curve
        
        exp_unit = Gtk.Label("(0.5 = Fuller)")
        exp_unit.get_style_context().add_class("dim-label")
        
        fuller_grid.attach(exp_label, 0, 1, 1, 1)
        fuller_grid.attach(self.exp_spin, 1, 1, 1, 1)
        fuller_grid.attach(exp_unit, 2, 1, 1, 1)
        
        self.psd_notebook.append_page(fuller_grid, Gtk.Label("Fuller"))
        
    def _create_custom_psd_tab(self) -> None:
        """Create custom PSD points tab."""
        custom_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        
        # Description
        desc_label = Gtk.Label()
        desc_label.set_markup('<i>Define custom particle size distribution points</i>')
        desc_label.set_halign(Gtk.Align.START)
        custom_box.pack_start(desc_label, False, False, 0)
        
        # Scrolled window for points table
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_size_request(-1, 150)
        
        # Create list store for PSD points (Size μm, Cumulative %)
        self.psd_store = Gtk.ListStore(float, float)  # size, cumulative_percent
        
        # Add some default points
        default_points = [
            (1.0, 5.0),
            (5.0, 20.0),
            (10.0, 40.0),
            (20.0, 65.0),
            (50.0, 90.0),
            (100.0, 99.0)
        ]
        
        for size, percent in default_points:
            self.psd_store.append([size, percent])
        
        # Create tree view
        self.psd_tree = Gtk.TreeView(model=self.psd_store)
        self.psd_tree.set_reorderable(True)
        
        # Size column
        size_renderer = Gtk.CellRendererText()
        size_renderer.set_property("editable", True)
        size_renderer.connect("edited", self._on_psd_size_edited)
        size_column = Gtk.TreeViewColumn("Size (μm)", size_renderer, text=0)
        size_column.set_resizable(True)
        self.psd_tree.append_column(size_column)
        
        # Cumulative % column
        percent_renderer = Gtk.CellRendererText()
        percent_renderer.set_property("editable", True)
        percent_renderer.connect("edited", self._on_psd_percent_edited)
        percent_column = Gtk.TreeViewColumn("Cumulative %", percent_renderer, text=1)
        percent_column.set_resizable(True)
        self.psd_tree.append_column(percent_column)
        
        scrolled.add(self.psd_tree)
        custom_box.pack_start(scrolled, True, True, 0)
        
        # Buttons for add/remove points
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        
        add_button = Gtk.Button(label="Add Point")
        add_button.connect('clicked', self._on_add_psd_point)
        button_box.pack_start(add_button, False, False, 0)
        
        remove_button = Gtk.Button(label="Remove Point")
        remove_button.connect('clicked', self._on_remove_psd_point)
        button_box.pack_start(remove_button, False, False, 0)
        
        custom_box.pack_start(button_box, False, False, 0)
        
        self.psd_notebook.append_page(custom_box, Gtk.Label("Custom"))
        
    def _on_psd_mode_changed(self, combo: Gtk.ComboBoxText) -> None:
        """Handle PSD mode change."""
        mode = combo.get_active_id()
        if mode == "rosin_rammler":
            self.psd_notebook.set_current_page(0)
        elif mode == "fuller":
            self.psd_notebook.set_current_page(1)
        elif mode == "custom":
            self.psd_notebook.set_current_page(2)
            
    def _on_psd_size_edited(self, renderer, path, new_text):
        """Handle editing of PSD size value."""
        try:
            value = float(new_text)
            if value > 0:
                self.psd_store[path][0] = value
        except ValueError:
            pass
            
    def _on_psd_percent_edited(self, renderer, path, new_text):
        """Handle editing of PSD cumulative percent value."""
        try:
            value = float(new_text)
            if 0 <= value <= 100:
                self.psd_store[path][1] = value
        except ValueError:
            pass
            
    def _on_add_psd_point(self, button):
        """Add a new PSD point."""
        self.psd_store.append([10.0, 50.0])
        
    def _on_remove_psd_point(self, button):
        """Remove selected PSD point."""
        selection = self.psd_tree.get_selection()
        model, treeiter = selection.get_selected()
        if treeiter:
            model.remove(treeiter)
    
    def _add_advanced_sections(self, container: Gtk.Box) -> None:
        """Add cement-specific advanced sections."""
        # Cement library/templates section
        self._add_cement_library_section(container)
        
        # Additional properties section
        self._add_additional_properties_section(container)
        
    def _add_cement_library_section(self, container: Gtk.Box) -> None:
        """Add cement library/template section."""
        lib_frame = Gtk.Frame(label="Cement Library & Templates")
        lib_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        lib_box.set_margin_top(10)
        lib_box.set_margin_bottom(10)
        lib_box.set_margin_left(15)
        lib_box.set_margin_right(15)
        
        # Description
        desc_label = Gtk.Label()
        desc_label.set_markup('<i>Load standard cement compositions from library</i>')
        desc_label.set_halign(Gtk.Align.START)
        lib_box.pack_start(desc_label, False, False, 0)
        
        # Template selection
        template_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        template_label = Gtk.Label("Template:")
        template_label.set_halign(Gtk.Align.END)
        template_label.get_style_context().add_class("form-label")
        template_box.pack_start(template_label, False, False, 0)
        
        # Create combo box with cement templates
        self.template_combo = Gtk.ComboBoxText()
        self.template_combo.append("", "Select a template...")
        
        # Define common cement types with typical compositions
        self.cement_templates = {
            "type_i": {
                "name": "Type I (Ordinary Portland)",
                "c3s": 55.0, "c2s": 19.0, "c3a": 10.0, "c4af": 7.0,
                "blaine": 350, "specific_gravity": 3.15
            },
            "type_ii": {
                "name": "Type II (Moderate Sulfate Resistance)",
                "c3s": 51.0, "c2s": 24.0, "c3a": 6.0, "c4af": 11.0,
                "blaine": 370, "specific_gravity": 3.16
            },
            "type_iii": {
                "name": "Type III (High Early Strength)",
                "c3s": 56.0, "c2s": 16.0, "c3a": 12.0, "c4af": 8.0,
                "blaine": 540, "specific_gravity": 3.15
            },
            "type_iv": {
                "name": "Type IV (Low Heat)",
                "c3s": 28.0, "c2s": 49.0, "c3a": 4.0, "c4af": 12.0,
                "blaine": 330, "specific_gravity": 3.13
            },
            "type_v": {
                "name": "Type V (High Sulfate Resistance)",
                "c3s": 38.0, "c2s": 43.0, "c3a": 4.0, "c4af": 9.0,
                "blaine": 380, "specific_gravity": 3.14
            },
            "white": {
                "name": "White Portland Cement",
                "c3s": 70.0, "c2s": 12.0, "c3a": 12.0, "c4af": 1.0,
                "blaine": 420, "specific_gravity": 3.12
            }
        }
        
        for key, template in self.cement_templates.items():
            self.template_combo.append(key, template["name"])
        
        template_box.pack_start(self.template_combo, True, True, 0)
        
        # Load template button
        load_button = Gtk.Button(label="Load Template")
        load_button.connect('clicked', self._on_load_template_clicked)
        template_box.pack_start(load_button, False, False, 0)
        
        lib_box.pack_start(template_box, False, False, 0)
        
        # Save as template section
        save_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        save_label = Gtk.Label("Save current:")
        save_label.get_style_context().add_class("form-label")
        save_box.pack_start(save_label, False, False, 0)
        
        save_button = Gtk.Button(label="Save as Template")
        save_button.connect('clicked', self._on_save_template_clicked)
        save_box.pack_start(save_button, False, False, 0)
        
        lib_box.pack_start(save_box, False, False, 0)
        
        lib_frame.add(lib_box)
        container.pack_start(lib_frame, False, False, 0)
        
    def _add_additional_properties_section(self, container: Gtk.Box) -> None:
        """Add additional cement properties section."""
        props_frame = Gtk.Frame(label="Additional Properties")
        props_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        props_box.set_margin_top(10)
        props_box.set_margin_bottom(10)
        props_box.set_margin_left(15)
        props_box.set_margin_right(15)
        
        # Setting time inputs
        setting_grid = Gtk.Grid()
        setting_grid.set_row_spacing(10)
        setting_grid.set_column_spacing(15)
        
        # Initial setting time
        initial_label = Gtk.Label("Initial Set:")
        initial_label.set_halign(Gtk.Align.END)
        initial_label.get_style_context().add_class("form-label")
        
        self.initial_set_spin = Gtk.SpinButton.new_with_range(30, 600, 5)
        self.initial_set_spin.set_value(120)  # Default 2 hours
        
        initial_unit = Gtk.Label("minutes")
        initial_unit.get_style_context().add_class("dim-label")
        
        setting_grid.attach(initial_label, 0, 0, 1, 1)
        setting_grid.attach(self.initial_set_spin, 1, 0, 1, 1)
        setting_grid.attach(initial_unit, 2, 0, 1, 1)
        
        # Final setting time
        final_label = Gtk.Label("Final Set:")
        final_label.set_halign(Gtk.Align.END)
        final_label.get_style_context().add_class("form-label")
        
        self.final_set_spin = Gtk.SpinButton.new_with_range(60, 1440, 10)
        self.final_set_spin.set_value(360)  # Default 6 hours
        
        final_unit = Gtk.Label("minutes")
        final_unit.get_style_context().add_class("dim-label")
        
        setting_grid.attach(final_label, 0, 1, 1, 1)
        setting_grid.attach(self.final_set_spin, 1, 1, 1, 1)
        setting_grid.attach(final_unit, 2, 1, 1, 1)
        
        props_box.pack_start(setting_grid, False, False, 0)
        props_frame.add(props_box)
        container.pack_start(props_frame, False, False, 0)
        
    def _on_load_template_clicked(self, button: Gtk.Button) -> None:
        """Handle load template button click."""
        template_id = self.template_combo.get_active_id()
        if not template_id or template_id == "":
            return
            
        template = self.cement_templates.get(template_id)
        if not template:
            return
            
        try:
            # Load phase composition
            for phase_key, spin in self.phase_spins.items():
                value = template.get(phase_key, 0.0)
                spin.set_value(value)
            
            # Load other properties
            if 'blaine' in template:
                self.blaine_spin.set_value(template['blaine'])
            
            if 'specific_gravity' in template:
                self.specific_gravity_spin.set_value(template['specific_gravity'])
            
            # Update calculations
            self._update_calculations()
            
            # Show success message
            self.parent_window.update_status(f"Loaded template: {template['name']}", "success", 3)
            
        except Exception as e:
            self.logger.error(f"Error loading template: {e}")
            self.parent_window.update_status("Error loading template", "error", 3)
    
    def _on_save_template_clicked(self, button: Gtk.Button) -> None:
        """Handle save template button click."""
        # This would open a dialog to save current composition as a custom template
        # For now, just show a placeholder message
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Save Template"
        )
        dialog.format_secondary_text("Custom template saving will be implemented in a future version.")
        dialog.run()
        dialog.destroy()
    
    def _connect_material_signals(self) -> None:
        """Connect cement-specific signals."""
        for spin in self.phase_spins.values():
            spin.connect('value-changed', self._on_field_changed)
    
    def _load_material_specific_data(self) -> None:
        """Load cement-specific data."""
        if not self.material_data:
            # For new materials, update calculations with default values
            self._update_calculations()
            return
        
        # Load Blaine fineness
        blaine = self.material_data.get('blaine_fineness', 350)
        self.blaine_spin.set_value(float(blaine))
        
        # Load phase composition
        for phase_key, spin in self.phase_spins.items():
            value = self.material_data.get(phase_key, 0.0)
            spin.set_value(float(value))
        
        # Load setting times
        initial_set = self.material_data.get('initial_set_time', 120)
        self.initial_set_spin.set_value(float(initial_set))
        
        final_set = self.material_data.get('final_set_time', 360)
        self.final_set_spin.set_value(float(final_set))
        
        # Load PSD data
        psd_mode = self.material_data.get('psd_mode', 'rosin_rammler')
        
        # Set PSD mode
        if psd_mode == "rosin_rammler":
            self.psd_mode_combo.set_active_id("rosin_rammler")
            d50 = self.material_data.get('psd_d50', 15.0)
            self.d50_spin.set_value(float(d50))
            n = self.material_data.get('psd_n', 1.1)
            self.n_spin.set_value(float(n))
        elif psd_mode == "fuller":
            self.psd_mode_combo.set_active_id("fuller")
            dmax = self.material_data.get('psd_dmax', 100.0)
            self.dmax_spin.set_value(float(dmax))
            exp = self.material_data.get('psd_exponent', 0.5)
            self.exp_spin.set_value(float(exp))
        elif psd_mode == "custom":
            self.psd_mode_combo.set_active_id("custom")
            custom_points = self.material_data.get('psd_custom_points', [])
            if custom_points:
                # Clear existing points
                self.psd_store.clear()
                # Load custom points
                for point in custom_points:
                    self.psd_store.append([point['size'], point['cumulative']])
        
        # Update calculations after loading data
        self._update_calculations()
    
    def _validate_material_specific_field(self, widget) -> None:
        """Validate cement-specific fields."""
        if widget in self.phase_spins.values():
            self._validate_phase_composition()
            self._update_calculations()
    
    def _validate_all_material_fields(self) -> None:
        """Validate all cement-specific fields."""
        self._validate_phase_composition()
        self._update_calculations()
    
    def _validate_phase_composition(self) -> None:
        """Validate that phase composition adds up correctly."""
        total = sum(spin.get_value() for spin in self.phase_spins.values())
        
        # Update sum display
        self.sum_display.set_text(f"{total:.1f}")
        
        # Color coding for sum display
        if abs(total - 100.0) <= 0.01:
            # Perfect sum - green
            self.sum_display.set_markup(f'<span color="green"><b>{total:.1f}</b></span>')
        elif abs(total - 100.0) <= 0.1:
            # Close to 100 - orange/warning
            self.sum_display.set_markup(f'<span color="orange"><b>{total:.1f}</b></span>')
        else:
            # Too far from 100 - red/error
            self.sum_display.set_markup(f'<span color="red"><b>{total:.1f}</b></span>')
        
        # Validation messages
        if abs(total - 100.0) > 0.1:
            self.validation_errors['phases'] = f"Phase composition must sum to 100% (currently {total:.1f}%)"
        elif abs(total - 100.0) > 0.01:
            self.validation_warnings['phases'] = f"Phase composition sums to {total:.1f}% (should be exactly 100%)"
        else:
            # Clear any existing phase validation errors/warnings
            self.validation_errors.pop('phases', None)
            self.validation_warnings.pop('phases', None)
    
    def _update_calculations(self) -> None:
        """Update calculated values based on current inputs."""
        try:
            # Get current phase values
            c3s = self.phase_spins['c3s'].get_value()
            c2s = self.phase_spins['c2s'].get_value()
            c3a = self.phase_spins['c3a'].get_value()
            c4af = self.phase_spins['c4af'].get_value()
            
            # Calculate theoretical density based on phase composition
            # Typical densities: C3S=3.15, C2S=3.28, C3A=3.03, C4AF=3.73 g/cm³
            phase_densities = {
                'c3s': 3.15,
                'c2s': 3.28,
                'c3a': 3.03,
                'c4af': 3.73
            }
            
            total_phases = c3s + c2s + c3a + c4af
            if total_phases > 0:
                # Weighted average density
                calculated_density = (
                    c3s * phase_densities['c3s'] +
                    c2s * phase_densities['c2s'] +
                    c3a * phase_densities['c3a'] +
                    c4af * phase_densities['c4af']
                ) / total_phases
                
                self.density_display.set_text(f"{calculated_density:.3f}")
            else:
                self.density_display.set_text("—")
            
            # Calculate estimated heat of hydration
            # Typical values: C3S=500, C2S=260, C3A=1340, C4AF=420 J/g
            heat_values = {
                'c3s': 500,
                'c2s': 260,
                'c3a': 1340,
                'c4af': 420
            }
            
            if total_phases > 0:
                calculated_heat = (
                    c3s * heat_values['c3s'] +
                    c2s * heat_values['c2s'] +
                    c3a * heat_values['c3a'] +
                    c4af * heat_values['c4af']
                ) / total_phases
                
                self.heat_display.set_text(f"{calculated_heat:.0f}")
            else:
                self.heat_display.set_text("—")
                
        except Exception as e:
            self.logger.warning(f"Error updating calculations: {e}")
            self.density_display.set_text("Error")
            self.heat_display.set_text("Error")
    
    def _collect_material_specific_data(self) -> Dict[str, Any]:
        """Collect cement-specific data."""
        data = {
            'blaine_fineness': self.blaine_spin.get_value(),
            'initial_set_time': self.initial_set_spin.get_value(),
            'final_set_time': self.final_set_spin.get_value()
        }
        
        # Add phase composition (convert to model field names)
        phase_mapping = {
            'c3s': 'c3s_mass_fraction',
            'c2s': 'c2s_mass_fraction', 
            'c3a': 'c3a_mass_fraction',
            'c4af': 'c4af_mass_fraction'
        }
        for phase_key, spin in self.phase_spins.items():
            model_field = phase_mapping.get(phase_key, phase_key)
            # Convert percentage to fraction (0-1 range)
            data[model_field] = spin.get_value() / 100.0
        
        # Add PSD data
        psd_mode = self.psd_mode_combo.get_active_id()
        data['psd_mode'] = psd_mode
        
        if psd_mode == "rosin_rammler":
            data['psd_d50'] = self.d50_spin.get_value()
            data['psd_n'] = self.n_spin.get_value()
        elif psd_mode == "fuller":
            data['psd_dmax'] = self.dmax_spin.get_value()
            data['psd_exponent'] = self.exp_spin.get_value()
        elif psd_mode == "custom":
            # Collect custom PSD points
            psd_points = []
            for row in self.psd_store:
                psd_points.append({'size': row[0], 'cumulative': row[1]})
            data['psd_custom_points'] = psd_points
        
        return data


# Additional material dialog classes would be implemented similarly
class AggregateDialog(MaterialDialogBase):
    """Dialog for aggregate materials."""
    
    def __init__(self, parent: 'VCCTLMainWindow', material_data: Optional[Dict[str, Any]] = None):
        super().__init__(parent, "aggregate", material_data)
    
    def _add_material_specific_fields(self, grid: Gtk.Grid, start_row: int) -> int:
        # Placeholder - implement aggregate-specific fields
        return start_row
    
    def _add_property_sections(self, container: Gtk.Box) -> None:
        # Placeholder - implement aggregate properties
        placeholder = Gtk.Label("Aggregate properties will be implemented")
        placeholder.get_style_context().add_class("dim-label")
        container.pack_start(placeholder, True, True, 0)
    
    def _add_advanced_sections(self, container: Gtk.Box) -> None:
        # Placeholder
        pass
    
    def _connect_material_signals(self) -> None:
        # Placeholder
        pass
    
    def _load_material_specific_data(self) -> None:
        # Placeholder
        pass
    
    def _validate_material_specific_field(self, widget) -> None:
        # Placeholder
        pass
    
    def _validate_all_material_fields(self) -> None:
        # Placeholder
        pass
    
    def _collect_material_specific_data(self) -> Dict[str, Any]:
        return {}


class FlyAshDialog(MaterialDialogBase):
    """Dialog for fly ash materials."""
    
    def __init__(self, parent: 'VCCTLMainWindow', material_data: Optional[Dict[str, Any]] = None):
        super().__init__(parent, "fly_ash", material_data)
    
    def _add_material_specific_fields(self, grid: Gtk.Grid, start_row: int) -> int:
        """Add fly ash-specific fields."""
        row = start_row
        
        # Loss on ignition (LOI)
        loi_label = Gtk.Label("Loss on Ignition:")
        loi_label.set_halign(Gtk.Align.END)
        loi_label.get_style_context().add_class("form-label")
        loi_label.set_tooltip_text("Unburned carbon content")
        
        self.loi_spin = Gtk.SpinButton.new_with_range(0.0, 20.0, 0.1)
        self.loi_spin.set_digits(2)
        self.loi_spin.set_value(3.0)  # Typical value
        self.loi_spin.set_tooltip_text("Typically 1-6% for Class F, 0-3% for Class C")
        
        loi_unit_label = Gtk.Label("%")
        loi_unit_label.get_style_context().add_class("dim-label")
        
        grid.attach(loi_label, 0, row, 1, 1)
        grid.attach(self.loi_spin, 1, row, 1, 1)
        grid.attach(loi_unit_label, 2, row, 1, 1)
        row += 1
        
        # Fineness (45μm sieve retention)
        fineness_label = Gtk.Label("Fineness (45μm):")
        fineness_label.set_halign(Gtk.Align.END)
        fineness_label.get_style_context().add_class("form-label")
        fineness_label.set_tooltip_text("Percent retained on 45μm sieve")
        
        self.fineness_spin = Gtk.SpinButton.new_with_range(0.0, 50.0, 0.5)
        self.fineness_spin.set_digits(1)
        self.fineness_spin.set_value(20.0)  # Typical value
        
        fineness_unit_label = Gtk.Label("% retained")
        fineness_unit_label.get_style_context().add_class("dim-label")
        
        grid.attach(fineness_label, 0, row, 1, 1)
        grid.attach(self.fineness_spin, 1, row, 1, 1)
        grid.attach(fineness_unit_label, 2, row, 1, 1)
        row += 1
        
        return row
    
    def _add_property_sections(self, container: Gtk.Box) -> None:
        """Add fly ash-specific property sections."""
        # Chemical composition section
        self._add_chemical_composition_section(container)
        
        # Alkali characteristics section
        self._add_alkali_characteristics_section(container)
        
        # Classification section
        self._add_classification_section(container)
        
    def _add_chemical_composition_section(self, container: Gtk.Box) -> None:
        """Add chemical composition section for fly ash."""
        comp_frame = Gtk.Frame(label="Chemical Composition (%)")
        comp_grid = Gtk.Grid()
        comp_grid.set_margin_top(10)
        comp_grid.set_margin_bottom(10)
        comp_grid.set_margin_left(15)
        comp_grid.set_margin_right(15)
        comp_grid.set_row_spacing(10)
        comp_grid.set_column_spacing(15)
        
        # Major oxides for fly ash
        oxides = [
            ("SiO₂:", "sio2", 52.0, "Silicon dioxide"),
            ("Al₂O₃:", "al2o3", 23.0, "Aluminum oxide"),
            ("Fe₂O₃:", "fe2o3", 11.0, "Iron oxide"),
            ("CaO:", "cao", 5.0, "Calcium oxide"),
            ("MgO:", "mgo", 2.0, "Magnesium oxide"),
            ("SO₃:", "so3", 1.0, "Sulfur trioxide")
        ]
        
        self.oxide_spins = {}
        for i, (label_text, oxide_key, default_value, tooltip) in enumerate(oxides):
            label = Gtk.Label(label_text)
            label.set_halign(Gtk.Align.END)
            label.get_style_context().add_class("form-label")
            label.set_tooltip_text(tooltip)
            
            spin = Gtk.SpinButton.new_with_range(0.0, 100.0, 0.1)
            spin.set_digits(1)
            spin.set_value(default_value)
            spin.set_tooltip_text(tooltip)
            
            unit_label = Gtk.Label("%")
            unit_label.get_style_context().add_class("dim-label")
            
            row = i // 2
            col = (i % 2) * 3
            
            comp_grid.attach(label, col, row, 1, 1)
            comp_grid.attach(spin, col + 1, row, 1, 1)
            comp_grid.attach(unit_label, col + 2, row, 1, 1)
            
            self.oxide_spins[oxide_key] = spin
        
        comp_frame.add(comp_grid)
        container.pack_start(comp_frame, False, False, 0)
        
    def _add_alkali_characteristics_section(self, container: Gtk.Box) -> None:
        """Add alkali characteristics section."""
        alkali_frame = Gtk.Frame(label="Alkali Characteristics")
        alkali_grid = Gtk.Grid()
        alkali_grid.set_margin_top(10)
        alkali_grid.set_margin_bottom(10)
        alkali_grid.set_margin_left(15)
        alkali_grid.set_margin_right(15)
        alkali_grid.set_row_spacing(10)
        alkali_grid.set_column_spacing(15)
        
        # Na2O equivalent
        na2o_label = Gtk.Label("Na₂O:")
        na2o_label.set_halign(Gtk.Align.END)
        na2o_label.get_style_context().add_class("form-label")
        
        self.na2o_spin = Gtk.SpinButton.new_with_range(0.0, 10.0, 0.01)
        self.na2o_spin.set_digits(2)
        self.na2o_spin.set_value(1.2)
        
        na2o_unit = Gtk.Label("%")
        na2o_unit.get_style_context().add_class("dim-label")
        
        alkali_grid.attach(na2o_label, 0, 0, 1, 1)
        alkali_grid.attach(self.na2o_spin, 1, 0, 1, 1)
        alkali_grid.attach(na2o_unit, 2, 0, 1, 1)
        
        # K2O
        k2o_label = Gtk.Label("K₂O:")
        k2o_label.set_halign(Gtk.Align.END)
        k2o_label.get_style_context().add_class("form-label")
        
        self.k2o_spin = Gtk.SpinButton.new_with_range(0.0, 10.0, 0.01)
        self.k2o_spin.set_digits(2)
        self.k2o_spin.set_value(2.1)
        
        k2o_unit = Gtk.Label("%")
        k2o_unit.get_style_context().add_class("dim-label")
        
        alkali_grid.attach(k2o_label, 0, 1, 1, 1)
        alkali_grid.attach(self.k2o_spin, 1, 1, 1, 1)
        alkali_grid.attach(k2o_unit, 2, 1, 1, 1)
        
        # Calculated Na2O equivalent
        equiv_label = Gtk.Label("Na₂O Equivalent:")
        equiv_label.set_halign(Gtk.Align.END)
        equiv_label.get_style_context().add_class("form-label")
        equiv_label.set_markup("<b>Na₂O Equivalent:</b>")
        
        self.na2o_equiv_display = Gtk.Label("2.58")
        self.na2o_equiv_display.set_halign(Gtk.Align.START)
        self.na2o_equiv_display.get_style_context().add_class("calculated-value")
        
        equiv_unit = Gtk.Label("%")
        equiv_unit.get_style_context().add_class("dim-label")
        
        alkali_grid.attach(equiv_label, 0, 2, 1, 1)
        alkali_grid.attach(self.na2o_equiv_display, 1, 2, 1, 1)
        alkali_grid.attach(equiv_unit, 2, 2, 1, 1)
        
        alkali_frame.add(alkali_grid)
        container.pack_start(alkali_frame, False, False, 0)
        
    def _add_classification_section(self, container: Gtk.Box) -> None:
        """Add classification section."""
        class_frame = Gtk.Frame(label="Classification")
        class_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        class_box.set_margin_top(10)
        class_box.set_margin_bottom(10)
        class_box.set_margin_left(15)
        class_box.set_margin_right(15)
        
        # ASTM Class selection
        class_grid = Gtk.Grid()
        class_grid.set_row_spacing(10)
        class_grid.set_column_spacing(15)
        
        astm_label = Gtk.Label("ASTM Class:")
        astm_label.set_halign(Gtk.Align.END)
        astm_label.get_style_context().add_class("form-label")
        
        self.astm_combo = Gtk.ComboBoxText()
        self.astm_combo.append("class_f", "Class F (Low Calcium)")
        self.astm_combo.append("class_c", "Class C (High Calcium)")
        self.astm_combo.append("class_n", "Class N (Natural Pozzolan)")
        self.astm_combo.set_active(0)
        
        class_grid.attach(astm_label, 0, 0, 1, 1)
        class_grid.attach(self.astm_combo, 1, 0, 2, 1)
        
        # Activity index
        activity_label = Gtk.Label("Activity Index:")
        activity_label.set_halign(Gtk.Align.END)
        activity_label.get_style_context().add_class("form-label")
        
        self.activity_spin = Gtk.SpinButton.new_with_range(50.0, 120.0, 1.0)
        self.activity_spin.set_value(85.0)
        
        activity_unit = Gtk.Label("% at 28 days")
        activity_unit.get_style_context().add_class("dim-label")
        
        class_grid.attach(activity_label, 0, 1, 1, 1)
        class_grid.attach(self.activity_spin, 1, 1, 1, 1)
        class_grid.attach(activity_unit, 2, 1, 1, 1)
        
        class_box.pack_start(class_grid, False, False, 0)
        
        # Automatic classification display
        auto_class_label = Gtk.Label()
        auto_class_label.set_markup('<i>Classification will be automatically determined based on composition</i>')
        auto_class_label.set_halign(Gtk.Align.START)
        class_box.pack_start(auto_class_label, False, False, 0)
        
        class_frame.add(class_box)
        container.pack_start(class_frame, False, False, 0)
    
    def _add_advanced_sections(self, container: Gtk.Box) -> None:
        """Add fly ash-specific advanced sections."""
        # Performance properties
        perf_frame = Gtk.Frame(label="Performance Properties")
        perf_grid = Gtk.Grid()
        perf_grid.set_margin_top(10)
        perf_grid.set_margin_bottom(10)
        perf_grid.set_margin_left(15)
        perf_grid.set_margin_right(15)
        perf_grid.set_row_spacing(10)
        perf_grid.set_column_spacing(15)
        
        # Pozzolanic activity
        pozz_label = Gtk.Label("Pozzolanic Activity:")
        pozz_label.set_halign(Gtk.Align.END)
        pozz_label.get_style_context().add_class("form-label")
        
        self.pozz_combo = Gtk.ComboBoxText()
        self.pozz_combo.append("high", "High")
        self.pozz_combo.append("moderate", "Moderate")
        self.pozz_combo.append("low", "Low")
        self.pozz_combo.set_active(0)
        
        perf_grid.attach(pozz_label, 0, 0, 1, 1)
        perf_grid.attach(self.pozz_combo, 1, 0, 2, 1)
        
        perf_frame.add(perf_grid)
        container.pack_start(perf_frame, False, False, 0)
    
    def _connect_material_signals(self) -> None:
        """Connect fly ash-specific signals."""
        # Connect oxide spin buttons
        for spin in self.oxide_spins.values():
            spin.connect('value-changed', self._on_field_changed)
        
        # Connect alkali spins
        self.na2o_spin.connect('value-changed', self._on_alkali_changed)
        self.k2o_spin.connect('value-changed', self._on_alkali_changed)
        
        # Connect other fields
        self.loi_spin.connect('value-changed', self._on_field_changed)
        self.fineness_spin.connect('value-changed', self._on_field_changed)
        self.activity_spin.connect('value-changed', self._on_field_changed)
    
    def _on_alkali_changed(self, widget) -> None:
        """Handle alkali field changes."""
        self._update_alkali_calculations()
        self._on_field_changed(widget)
    
    def _update_alkali_calculations(self) -> None:
        """Update alkali calculations."""
        try:
            na2o = self.na2o_spin.get_value()
            k2o = self.k2o_spin.get_value()
            
            # Na2O equivalent = Na2O + 0.658 * K2O
            na2o_equiv = na2o + 0.658 * k2o
            self.na2o_equiv_display.set_text(f"{na2o_equiv:.2f}")
            
        except Exception as e:
            self.logger.warning(f"Error updating alkali calculations: {e}")
            self.na2o_equiv_display.set_text("Error")
    
    def _load_material_specific_data(self) -> None:
        """Load fly ash-specific data."""
        if not self.material_data:
            self._update_alkali_calculations()
            return
        
        # Load basic fields
        self.loi_spin.set_value(float(self.material_data.get('loi', 3.0)))
        self.fineness_spin.set_value(float(self.material_data.get('fineness_45um', 20.0)))
        
        # Load oxide composition
        for oxide_key, spin in self.oxide_spins.items():
            value = self.material_data.get(oxide_key, 0.0)
            spin.set_value(float(value))
        
        # Load alkali values
        self.na2o_spin.set_value(float(self.material_data.get('na2o', 1.2)))
        self.k2o_spin.set_value(float(self.material_data.get('k2o', 2.1)))
        
        # Load classification
        astm_class = self.material_data.get('astm_class', 'class_f')
        self.astm_combo.set_active_id(astm_class)
        
        self.activity_spin.set_value(float(self.material_data.get('activity_index', 85.0)))
        
        pozz_activity = self.material_data.get('pozzolanic_activity', 'high')
        self.pozz_combo.set_active_id(pozz_activity)
        
        # Update calculations
        self._update_alkali_calculations()
    
    def _validate_material_specific_field(self, widget) -> None:
        """Validate fly ash-specific fields."""
        self._validate_fly_ash_composition()
    
    def _validate_all_material_fields(self) -> None:
        """Validate all fly ash-specific fields."""
        self._validate_fly_ash_composition()
    
    def _validate_fly_ash_composition(self) -> None:
        """Validate fly ash composition requirements."""
        try:
            # Check major oxide sum (SiO2 + Al2O3 + Fe2O3)
            sio2 = self.oxide_spins['sio2'].get_value()
            al2o3 = self.oxide_spins['al2o3'].get_value()
            fe2o3 = self.oxide_spins['fe2o3'].get_value()
            
            major_sum = sio2 + al2o3 + fe2o3
            
            # ASTM requirements for Class F: ≥ 70%, Class C: ≥ 50%
            astm_class = self.astm_combo.get_active_id()
            min_required = 70.0 if astm_class == 'class_f' else 50.0
            
            if major_sum < min_required:
                self.validation_errors['major_oxides'] = f"SiO₂+Al₂O₃+Fe₂O₃ must be ≥{min_required}% for {astm_class.replace('_', ' ').title()} (currently {major_sum:.1f}%)"
            else:
                self.validation_errors.pop('major_oxides', None)
            
            # Check SO3 content
            so3 = self.oxide_spins['so3'].get_value()
            if so3 > 5.0:
                self.validation_warnings['so3'] = f"SO₃ content ({so3:.1f}%) exceeds typical limit of 5%"
            else:
                self.validation_warnings.pop('so3', None)
            
            # Check LOI
            loi = self.loi_spin.get_value()
            max_loi = 6.0 if astm_class == 'class_f' else 3.0
            if loi > max_loi:
                self.validation_errors['loi'] = f"Loss on ignition ({loi:.1f}%) exceeds {max_loi}% limit for {astm_class.replace('_', ' ').title()}"
            else:
                self.validation_errors.pop('loi', None)
                
        except Exception as e:
            self.logger.warning(f"Error validating fly ash composition: {e}")
    
    def _collect_material_specific_data(self) -> Dict[str, Any]:
        """Collect fly ash-specific data."""
        data = {
            'loi': self.loi_spin.get_value(),
            'fineness_45um': self.fineness_spin.get_value(),
            'na2o': self.na2o_spin.get_value(),
            'k2o': self.k2o_spin.get_value(),
            'astm_class': self.astm_combo.get_active_id(),
            'activity_index': self.activity_spin.get_value(),
            'pozzolanic_activity': self.pozz_combo.get_active_id()
        }
        
        # Add oxide composition
        for oxide_key, spin in self.oxide_spins.items():
            data[oxide_key] = spin.get_value()
        
        return data


class SlagDialog(MaterialDialogBase):
    """Dialog for managing slag (GGBS) materials."""
    
    def __init__(self, parent: 'VCCTLMainWindow', material_data: Optional[Dict[str, Any]] = None):
        """Initialize the slag dialog."""
        super().__init__(parent, 'slag', material_data)
        
        # Slag-specific UI components
        self.oxide_spins = {}
        self.cao_sio2_display = None
        self.mgo_al2o3_display = None
        self.activity_spin = None
        self.glass_content_spin = None
        self.reaction_params = {}
    
    def _add_material_specific_fields(self, grid: Gtk.Grid, start_row: int) -> int:
        """Add slag-specific fields to the basic info grid."""
        row = start_row
        
        # Glass content
        glass_label = Gtk.Label("Glass Content (%):")
        glass_label.set_halign(Gtk.Align.END)
        glass_label.get_style_context().add_class("form-label")
        
        self.glass_content_spin = Gtk.SpinButton.new_with_range(85.0, 100.0, 0.1)
        self.glass_content_spin.set_value(95.0)
        self.glass_content_spin.set_digits(1)
        
        grid.attach(glass_label, 0, row, 1, 1)
        grid.attach(self.glass_content_spin, 1, row, 1, 1)
        row += 1
        
        # Activity index
        activity_label = Gtk.Label("Activity Index (%):")
        activity_label.set_halign(Gtk.Align.END)
        activity_label.get_style_context().add_class("form-label")
        
        self.activity_spin = Gtk.SpinButton.new_with_range(50.0, 150.0, 0.1)
        self.activity_spin.set_value(95.0)
        self.activity_spin.set_digits(1)
        
        activity_info = Gtk.Image()
        activity_info.set_from_icon_name("dialog-information", Gtk.IconSize.BUTTON)
        activity_info.set_tooltip_text("Hydraulic activity relative to portland cement")
        
        activity_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        activity_box.pack_start(self.activity_spin, False, False, 0)
        activity_box.pack_start(activity_info, False, False, 0)
        
        grid.attach(activity_label, 0, row, 1, 1)
        grid.attach(activity_box, 1, row, 1, 1)
        row += 1
        
        return row
    
    def _add_property_sections(self, container: Gtk.Box) -> None:
        """Add slag-specific property sections."""
        # Chemical composition section
        self._add_chemical_composition_section(container)
        
        # Ratio characteristics section
        self._add_ratio_characteristics_section(container)
        
        # Reaction parameters section
        self._add_reaction_parameters_section(container)
    
    def _add_chemical_composition_section(self, container: Gtk.Box) -> None:
        """Add chemical composition section for slag."""
        comp_frame = Gtk.Frame(label="Chemical Composition")
        comp_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        comp_box.set_margin_top(10)
        comp_box.set_margin_bottom(10)
        comp_box.set_margin_left(15)
        comp_box.set_margin_right(15)
        
        # Major oxides grid
        comp_grid = Gtk.Grid()
        comp_grid.set_row_spacing(10)
        comp_grid.set_column_spacing(15)
        comp_grid.set_column_homogeneous(True)
        
        # Major oxides for slag
        oxides = [
            ('sio2', 'SiO₂', 35.0, 40.0, '%'),
            ('cao', 'CaO', 38.0, 45.0, '%'),
            ('al2o3', 'Al₂O₃', 8.0, 15.0, '%'),
            ('mgo', 'MgO', 6.0, 12.0, '%'),
            ('fe2o3', 'Fe₂O₃', 0.3, 2.0, '%'),
            ('so3', 'SO₃', 0.0, 3.0, '%')
        ]
        
        for i, (key, formula, min_val, max_val, unit) in enumerate(oxides):
            row = i // 3
            col = (i % 3) * 3
            
            # Label
            label = Gtk.Label(f"{formula}:")
            label.set_halign(Gtk.Align.END)
            label.get_style_context().add_class("form-label")
            comp_grid.attach(label, col, row, 1, 1)
            
            # Spin button
            spin = Gtk.SpinButton.new_with_range(0.0, 100.0, 0.1)
            spin.set_value((min_val + max_val) / 2)
            spin.set_digits(2)
            self.oxide_spins[key] = spin
            comp_grid.attach(spin, col + 1, row, 1, 1)
            
            # Unit label
            unit_label = Gtk.Label(unit)
            unit_label.set_halign(Gtk.Align.START)
            unit_label.get_style_context().add_class("dim-label")
            comp_grid.attach(unit_label, col + 2, row, 1, 1)
        
        comp_box.pack_start(comp_grid, False, False, 0)
        comp_frame.add(comp_box)
        container.pack_start(comp_frame, False, False, 0)
    
    def _add_ratio_characteristics_section(self, container: Gtk.Box) -> None:
        """Add ratio characteristics section."""
        ratio_frame = Gtk.Frame(label="Ratio Characteristics")
        ratio_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        ratio_box.set_margin_top(10)
        ratio_box.set_margin_bottom(10)
        ratio_box.set_margin_left(15)
        ratio_box.set_margin_right(15)
        
        # Ratios grid
        ratio_grid = Gtk.Grid()
        ratio_grid.set_row_spacing(10)
        ratio_grid.set_column_spacing(15)
        
        # CaO/SiO2 ratio
        cao_sio2_label = Gtk.Label("CaO/SiO₂ Ratio:")
        cao_sio2_label.set_halign(Gtk.Align.END)
        cao_sio2_label.get_style_context().add_class("form-label")
        
        self.cao_sio2_display = Gtk.Entry()
        self.cao_sio2_display.set_editable(False)
        self.cao_sio2_display.set_text("1.20")
        self.cao_sio2_display.get_style_context().add_class("calculated-field")
        
        cao_info = Gtk.Image()
        cao_info.set_from_icon_name("dialog-information", Gtk.IconSize.BUTTON)
        cao_info.set_tooltip_text("Calculated automatically. Higher ratios indicate more hydraulic activity.")
        
        cao_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        cao_box.pack_start(self.cao_sio2_display, True, True, 0)
        cao_box.pack_start(cao_info, False, False, 0)
        
        ratio_grid.attach(cao_sio2_label, 0, 0, 1, 1)
        ratio_grid.attach(cao_box, 1, 0, 2, 1)
        
        # MgO/Al2O3 ratio
        mgo_al2o3_label = Gtk.Label("MgO/Al₂O₃ Ratio:")
        mgo_al2o3_label.set_halign(Gtk.Align.END)
        mgo_al2o3_label.get_style_context().add_class("form-label")
        
        self.mgo_al2o3_display = Gtk.Entry()
        self.mgo_al2o3_display.set_editable(False)
        self.mgo_al2o3_display.set_text("0.75")
        self.mgo_al2o3_display.get_style_context().add_class("calculated-field")
        
        mgo_info = Gtk.Image()
        mgo_info.set_from_icon_name("dialog-information", Gtk.IconSize.BUTTON)
        mgo_info.set_tooltip_text("Calculated automatically. Affects slag reactivity and durability.")
        
        mgo_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        mgo_box.pack_start(self.mgo_al2o3_display, True, True, 0)
        mgo_box.pack_start(mgo_info, False, False, 0)
        
        ratio_grid.attach(mgo_al2o3_label, 0, 1, 1, 1)
        ratio_grid.attach(mgo_box, 1, 1, 2, 1)
        
        ratio_box.pack_start(ratio_grid, False, False, 0)
        ratio_frame.add(ratio_box)
        container.pack_start(ratio_frame, False, False, 0)
    
    def _add_reaction_parameters_section(self, container: Gtk.Box) -> None:
        """Add reaction parameters section."""
        reaction_frame = Gtk.Frame(label="Reaction Parameters")
        reaction_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        reaction_box.set_margin_top(10)
        reaction_box.set_margin_bottom(10)
        reaction_box.set_margin_left(15)
        reaction_box.set_margin_right(15)
        
        # Parameters grid
        param_grid = Gtk.Grid()
        param_grid.set_row_spacing(10)
        param_grid.set_column_spacing(15)
        
        # Activation energy
        activation_label = Gtk.Label("Activation Energy (J/mol):")
        activation_label.set_halign(Gtk.Align.END)
        activation_label.get_style_context().add_class("form-label")
        
        activation_spin = Gtk.SpinButton.new_with_range(40000, 80000, 100)
        activation_spin.set_value(54000)
        activation_spin.set_digits(0)
        self.reaction_params['activation_energy'] = activation_spin
        
        param_grid.attach(activation_label, 0, 0, 1, 1)
        param_grid.attach(activation_spin, 1, 0, 1, 1)
        
        # Reactivity factor
        reactivity_label = Gtk.Label("Reactivity Factor:")
        reactivity_label.set_halign(Gtk.Align.END)
        reactivity_label.get_style_context().add_class("form-label")
        
        reactivity_spin = Gtk.SpinButton.new_with_range(0.1, 2.0, 0.01)
        reactivity_spin.set_value(1.0)
        reactivity_spin.set_digits(2)
        self.reaction_params['reactivity_factor'] = reactivity_spin
        
        param_grid.attach(reactivity_label, 0, 1, 1, 1)
        param_grid.attach(reactivity_spin, 1, 1, 1, 1)
        
        # Hydration rate constant
        rate_label = Gtk.Label("Rate Constant (1/s):")
        rate_label.set_halign(Gtk.Align.END)
        rate_label.get_style_context().add_class("form-label")
        
        rate_spin = Gtk.SpinButton.new_with_range(1e-8, 1e-4, 1e-9)
        rate_spin.set_value(1e-6)
        rate_spin.set_digits(9)
        self.reaction_params['rate_constant'] = rate_spin
        
        param_grid.attach(rate_label, 0, 2, 1, 1)
        param_grid.attach(rate_spin, 1, 2, 1, 1)
        
        reaction_box.pack_start(param_grid, False, False, 0)
        reaction_frame.add(reaction_box)
        container.pack_start(reaction_frame, False, False, 0)
    
    def _add_advanced_sections(self, container: Gtk.Box) -> None:
        """Add slag-specific advanced sections."""
        # Performance characteristics
        perf_frame = Gtk.Frame(label="Performance Characteristics")
        perf_grid = Gtk.Grid()
        perf_grid.set_margin_top(10)
        perf_grid.set_margin_bottom(10)
        perf_grid.set_margin_left(15)
        perf_grid.set_margin_right(15)
        perf_grid.set_row_spacing(10)
        perf_grid.set_column_spacing(15)
        
        # Durability factor
        durability_label = Gtk.Label("Durability Factor:")
        durability_label.set_halign(Gtk.Align.END)
        durability_label.get_style_context().add_class("form-label")
        
        self.durability_combo = Gtk.ComboBoxText()
        self.durability_combo.append("excellent", "Excellent")
        self.durability_combo.append("good", "Good") 
        self.durability_combo.append("fair", "Fair")
        self.durability_combo.set_active(1)
        
        perf_grid.attach(durability_label, 0, 0, 1, 1)
        perf_grid.attach(self.durability_combo, 1, 0, 1, 1)
        
        perf_frame.add(perf_grid)
        container.pack_start(perf_frame, False, False, 0)
    
    def _connect_material_signals(self) -> None:
        """Connect slag-specific signals."""
        # Connect oxide spin buttons for ratio calculations
        for spin in self.oxide_spins.values():
            spin.connect('value-changed', self._on_composition_changed)
        
        # Connect other fields
        self.glass_content_spin.connect('value-changed', self._on_field_changed)
        self.activity_spin.connect('value-changed', self._on_field_changed)
        
        # Connect reaction parameter fields
        for spin in self.reaction_params.values():
            spin.connect('value-changed', self._on_field_changed)
    
    def _on_composition_changed(self, widget) -> None:
        """Handle composition field changes."""
        self._update_ratio_calculations()
        self._on_field_changed(widget)
    
    def _update_ratio_calculations(self) -> None:
        """Update ratio calculations."""
        try:
            cao = self.oxide_spins['cao'].get_value()
            sio2 = self.oxide_spins['sio2'].get_value()
            mgo = self.oxide_spins['mgo'].get_value()
            al2o3 = self.oxide_spins['al2o3'].get_value()
            
            # CaO/SiO2 ratio
            if sio2 > 0:
                cao_sio2_ratio = cao / sio2
                self.cao_sio2_display.set_text(f"{cao_sio2_ratio:.3f}")
            else:
                self.cao_sio2_display.set_text("N/A")
            
            # MgO/Al2O3 ratio
            if al2o3 > 0:
                mgo_al2o3_ratio = mgo / al2o3
                self.mgo_al2o3_display.set_text(f"{mgo_al2o3_ratio:.3f}")
            else:
                self.mgo_al2o3_display.set_text("N/A")
                
        except Exception as e:
            self.logger.warning(f"Error updating ratio calculations: {e}")
            self.cao_sio2_display.set_text("Error")
            self.mgo_al2o3_display.set_text("Error")
    
    def _load_material_specific_data(self) -> None:
        """Load slag-specific data."""
        if not self.material_data:
            self._update_ratio_calculations()
            return
        
        # Load basic fields
        self.glass_content_spin.set_value(float(self.material_data.get('glass_content', 95.0)))
        self.activity_spin.set_value(float(self.material_data.get('activity_index', 95.0)))
        
        # Load oxide composition
        for oxide_key, spin in self.oxide_spins.items():
            value = self.material_data.get(oxide_key, 0.0)
            spin.set_value(float(value))
        
        # Load reaction parameters
        reaction_data = self.material_data.get('reaction_parameters', {})
        for param_key, spin in self.reaction_params.items():
            value = reaction_data.get(param_key, spin.get_value())
            spin.set_value(float(value))
        
        # Load durability factor
        durability = self.material_data.get('durability_factor', 'good')
        self.durability_combo.set_active_id(durability)
        
        # Update calculations
        self._update_ratio_calculations()
    
    def _validate_material_specific_field(self, widget) -> None:
        """Validate slag-specific fields."""
        self._validate_slag_composition()
    
    def _validate_all_material_fields(self) -> None:
        """Validate all slag-specific fields."""
        self._validate_slag_composition()
    
    def _validate_slag_composition(self) -> None:
        """Validate slag composition requirements."""
        try:
            # Check CaO/SiO2 ratio
            cao = self.oxide_spins['cao'].get_value()
            sio2 = self.oxide_spins['sio2'].get_value()
            
            if sio2 > 0:
                cao_sio2_ratio = cao / sio2
                if cao_sio2_ratio < 1.0:
                    self.validation_warnings['cao_sio2'] = f"CaO/SiO₂ ratio ({cao_sio2_ratio:.2f}) is low for good hydraulicity (typically >1.0)"
                else:
                    self.validation_warnings.pop('cao_sio2', None)
            
            # Check glass content
            glass_content = self.glass_content_spin.get_value()
            if glass_content < 90.0:
                self.validation_warnings['glass_content'] = f"Glass content ({glass_content:.1f}%) is low (typically >90%)"
            else:
                self.validation_warnings.pop('glass_content', None)
            
            # Check MgO content
            mgo = self.oxide_spins['mgo'].get_value()
            if mgo > 18.0:
                self.validation_errors['mgo'] = f"MgO content ({mgo:.1f}%) exceeds typical limit of 18%"
            else:
                self.validation_errors.pop('mgo', None)
                
        except Exception as e:
            self.logger.warning(f"Error validating slag composition: {e}")
    
    def _collect_material_specific_data(self) -> Dict[str, Any]:
        """Collect slag-specific data."""
        data = {
            'glass_content': self.glass_content_spin.get_value(),
            'activity_index': self.activity_spin.get_value(),
            'durability_factor': self.durability_combo.get_active_id()
        }
        
        # Add oxide composition
        for oxide_key, spin in self.oxide_spins.items():
            data[oxide_key] = spin.get_value()
        
        # Add reaction parameters
        reaction_params = {}
        for param_key, spin in self.reaction_params.items():
            reaction_params[param_key] = spin.get_value()
        data['reaction_parameters'] = reaction_params
        
        return data


class InertFillerDialog(MaterialDialogBase):
    """Dialog for managing inert filler materials."""
    
    def __init__(self, parent: 'VCCTLMainWindow', material_data: Optional[Dict[str, Any]] = None):
        """Initialize the inert filler dialog."""
        super().__init__(parent, 'inert_filler', material_data)
        
        # Inert filler-specific UI components
        self.filler_type_combo = None
        self.psd_median_spin = None
        self.psd_spread_spin = None
        self.specific_surface_spin = None
        self.color_combo = None
        self.absorption_spin = None
    
    def _add_material_specific_fields(self, grid: Gtk.Grid, start_row: int) -> int:
        """Add inert filler-specific fields to the basic info grid."""
        row = start_row
        
        # Filler type
        type_label = Gtk.Label("Filler Type:")
        type_label.set_halign(Gtk.Align.END)
        type_label.get_style_context().add_class("form-label")
        
        self.filler_type_combo = Gtk.ComboBoxText()
        self.filler_type_combo.append("limestone", "Limestone Powder")
        self.filler_type_combo.append("quartz", "Quartz Powder")
        self.filler_type_combo.append("glass", "Glass Powder")
        self.filler_type_combo.append("other", "Other")
        self.filler_type_combo.set_active(0)
        
        grid.attach(type_label, 0, row, 1, 1)
        grid.attach(self.filler_type_combo, 1, row, 1, 1)
        row += 1
        
        # Specific surface area
        surface_label = Gtk.Label("Specific Surface (m²/g):")
        surface_label.set_halign(Gtk.Align.END)
        surface_label.get_style_context().add_class("form-label")
        
        self.specific_surface_spin = Gtk.SpinButton.new_with_range(0.1, 50.0, 0.1)
        self.specific_surface_spin.set_value(1.0)
        self.specific_surface_spin.set_digits(2)
        
        surface_info = Gtk.Image()
        surface_info.set_from_icon_name("dialog-information", Gtk.IconSize.BUTTON)
        surface_info.set_tooltip_text("Blaine specific surface area")
        
        surface_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        surface_box.pack_start(self.specific_surface_spin, False, False, 0)
        surface_box.pack_start(surface_info, False, False, 0)
        
        grid.attach(surface_label, 0, row, 1, 1)
        grid.attach(surface_box, 1, row, 1, 1)
        row += 1
        
        return row
    
    def _add_property_sections(self, container: Gtk.Box) -> None:
        """Add inert filler-specific property sections."""
        # Physical properties section
        self._add_physical_properties_section(container)
        
        # Particle size distribution section
        self._add_psd_section(container)
    
    def _add_physical_properties_section(self, container: Gtk.Box) -> None:
        """Add physical properties section for inert filler."""
        props_frame = Gtk.Frame(label="Physical Properties")
        props_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        props_box.set_margin_top(10)
        props_box.set_margin_bottom(10)
        props_box.set_margin_left(15)
        props_box.set_margin_right(15)
        
        # Properties grid
        props_grid = Gtk.Grid()
        props_grid.set_row_spacing(10)
        props_grid.set_column_spacing(15)
        
        # Water absorption
        absorption_label = Gtk.Label("Water Absorption (%):")
        absorption_label.set_halign(Gtk.Align.END)
        absorption_label.get_style_context().add_class("form-label")
        
        self.absorption_spin = Gtk.SpinButton.new_with_range(0.0, 5.0, 0.01)
        self.absorption_spin.set_value(0.1)
        self.absorption_spin.set_digits(2)
        
        props_grid.attach(absorption_label, 0, 0, 1, 1)
        props_grid.attach(self.absorption_spin, 1, 0, 1, 1)
        
        # Color
        color_label = Gtk.Label("Color:")
        color_label.set_halign(Gtk.Align.END)
        color_label.get_style_context().add_class("form-label")
        
        self.color_combo = Gtk.ComboBoxText()
        self.color_combo.append("white", "White")
        self.color_combo.append("gray", "Gray")
        self.color_combo.append("beige", "Beige")
        self.color_combo.append("other", "Other")
        self.color_combo.set_active(0)
        
        props_grid.attach(color_label, 0, 1, 1, 1)
        props_grid.attach(self.color_combo, 1, 1, 1, 1)
        
        props_box.pack_start(props_grid, False, False, 0)
        props_frame.add(props_box)
        container.pack_start(props_frame, False, False, 0)
    
    def _add_psd_section(self, container: Gtk.Box) -> None:
        """Add particle size distribution section."""
        psd_frame = Gtk.Frame(label="Particle Size Distribution")
        psd_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        psd_box.set_margin_top(10)
        psd_box.set_margin_bottom(10)
        psd_box.set_margin_left(15)
        psd_box.set_margin_right(15)
        
        # PSD grid
        psd_grid = Gtk.Grid()
        psd_grid.set_row_spacing(10)
        psd_grid.set_column_spacing(15)
        
        # Median particle size
        median_label = Gtk.Label("Median Size (μm):")
        median_label.set_halign(Gtk.Align.END)
        median_label.get_style_context().add_class("form-label")
        
        self.psd_median_spin = Gtk.SpinButton.new_with_range(0.1, 100.0, 0.1)
        self.psd_median_spin.set_value(5.0)
        self.psd_median_spin.set_digits(1)
        
        psd_grid.attach(median_label, 0, 0, 1, 1)
        psd_grid.attach(self.psd_median_spin, 1, 0, 1, 1)
        
        # Size distribution spread
        spread_label = Gtk.Label("Distribution Spread:")
        spread_label.set_halign(Gtk.Align.END)
        spread_label.get_style_context().add_class("form-label")
        
        self.psd_spread_spin = Gtk.SpinButton.new_with_range(1.1, 5.0, 0.1)
        self.psd_spread_spin.set_value(2.0)
        self.psd_spread_spin.set_digits(1)
        
        spread_info = Gtk.Image()
        spread_info.set_from_icon_name("dialog-information", Gtk.IconSize.BUTTON)
        spread_info.set_tooltip_text("Log-normal distribution parameter (sigma)")
        
        spread_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        spread_box.pack_start(self.psd_spread_spin, False, False, 0)
        spread_box.pack_start(spread_info, False, False, 0)
        
        psd_grid.attach(spread_label, 0, 1, 1, 1)
        psd_grid.attach(spread_box, 1, 1, 1, 1)
        
        psd_box.pack_start(psd_grid, False, False, 0)
        
        # PSD summary
        summary_label = Gtk.Label()
        summary_label.set_markup('<i>Particle size distribution will be modeled as log-normal</i>')
        summary_label.set_halign(Gtk.Align.START)
        psd_box.pack_start(summary_label, False, False, 0)
        
        psd_frame.add(psd_box)
        container.pack_start(psd_frame, False, False, 0)
    
    def _add_advanced_sections(self, container: Gtk.Box) -> None:
        """Add inert filler-specific advanced sections."""
        # Chemical inertness section
        inert_frame = Gtk.Frame(label="Chemical Properties")
        inert_grid = Gtk.Grid()
        inert_grid.set_margin_top(10)
        inert_grid.set_margin_bottom(10)
        inert_grid.set_margin_left(15)
        inert_grid.set_margin_right(15)
        inert_grid.set_row_spacing(10)
        inert_grid.set_column_spacing(15)
        
        # Reactivity
        reactivity_label = Gtk.Label("Chemical Reactivity:")
        reactivity_label.set_halign(Gtk.Align.END)
        reactivity_label.get_style_context().add_class("form-label")
        
        self.reactivity_combo = Gtk.ComboBoxText()
        self.reactivity_combo.append("inert", "Inert")
        self.reactivity_combo.append("minimal", "Minimal")
        self.reactivity_combo.append("slight", "Slight")
        self.reactivity_combo.set_active(0)
        
        inert_grid.attach(reactivity_label, 0, 0, 1, 1)
        inert_grid.attach(self.reactivity_combo, 1, 0, 1, 1)
        
        inert_frame.add(inert_grid)
        container.pack_start(inert_frame, False, False, 0)
    
    def _connect_material_signals(self) -> None:
        """Connect inert filler-specific signals."""
        # Connect all spin buttons
        self.specific_surface_spin.connect('value-changed', self._on_field_changed)
        self.psd_median_spin.connect('value-changed', self._on_field_changed)
        self.psd_spread_spin.connect('value-changed', self._on_field_changed)
        self.absorption_spin.connect('value-changed', self._on_field_changed)
        
        # Connect combo boxes
        self.filler_type_combo.connect('changed', self._on_field_changed)
        self.color_combo.connect('changed', self._on_field_changed)
    
    def _load_material_specific_data(self) -> None:
        """Load inert filler-specific data."""
        if not self.material_data:
            return
        
        # Load basic fields
        filler_type = self.material_data.get('filler_type', 'limestone')
        self.filler_type_combo.set_active_id(filler_type)
        
        self.specific_surface_spin.set_value(float(self.material_data.get('specific_surface', 1.0)))
        self.absorption_spin.set_value(float(self.material_data.get('water_absorption', 0.1)))
        
        # Load PSD parameters
        self.psd_median_spin.set_value(float(self.material_data.get('psd_median', 5.0)))
        self.psd_spread_spin.set_value(float(self.material_data.get('psd_spread', 2.0)))
        
        # Load appearance
        color = self.material_data.get('color', 'white')
        self.color_combo.set_active_id(color)
        
        # Load reactivity
        reactivity = self.material_data.get('reactivity', 'inert')
        self.reactivity_combo.set_active_id(reactivity)
    
    def _validate_material_specific_field(self, widget) -> None:
        """Validate inert filler-specific fields."""
        self._validate_inert_filler_properties()
    
    def _validate_all_material_fields(self) -> None:
        """Validate all inert filler-specific fields."""
        self._validate_inert_filler_properties()
    
    def _validate_inert_filler_properties(self) -> None:
        """Validate inert filler properties."""
        try:
            # Check PSD parameters
            median = self.psd_median_spin.get_value()
            spread = self.psd_spread_spin.get_value()
            
            if median < 0.5:
                self.validation_warnings['psd_median'] = f"Very fine median size ({median:.1f} μm) may affect workability"
            else:
                self.validation_warnings.pop('psd_median', None)
            
            if spread > 3.0:
                self.validation_warnings['psd_spread'] = f"Wide size distribution (spread={spread:.1f}) may affect packing"
            else:
                self.validation_warnings.pop('psd_spread', None)
            
            # Check specific surface
            surface = self.specific_surface_spin.get_value()
            if surface > 20.0:
                self.validation_warnings['specific_surface'] = f"Very high specific surface ({surface:.1f} m²/g) may increase water demand"
            else:
                self.validation_warnings.pop('specific_surface', None)
                
        except Exception as e:
            self.logger.warning(f"Error validating inert filler properties: {e}")
    
    def _collect_material_specific_data(self) -> Dict[str, Any]:
        """Collect inert filler-specific data."""
        data = {
            'filler_type': self.filler_type_combo.get_active_id(),
            'specific_surface': self.specific_surface_spin.get_value(),
            'water_absorption': self.absorption_spin.get_value(),
            'psd_median': self.psd_median_spin.get_value(),
            'psd_spread': self.psd_spread_spin.get_value(),
            'color': self.color_combo.get_active_id(),
            'reactivity': self.reactivity_combo.get_active_id()
        }
        
        return data


# Factory function for creating material dialogs
def create_material_dialog(parent: 'VCCTLMainWindow', material_type: str, material_data: Optional[Dict[str, Any]] = None) -> MaterialDialogBase:
    """Create a material dialog for the specified type."""
    dialog_classes = {
        'cement': CementDialog,
        'aggregate': AggregateDialog,
        'fly_ash': FlyAshDialog,
        'slag': SlagDialog,
        'inert_filler': InertFillerDialog,
        # Add other material types as needed
    }
    
    dialog_class = dialog_classes.get(material_type, MaterialDialogBase)
    
    # For unsupported types, create a generic dialog by subclassing
    if dialog_class == MaterialDialogBase:
        class GenericMaterialDialog(MaterialDialogBase):
            def _add_material_specific_fields(self, grid, start_row):
                return start_row
            def _add_property_sections(self, container):
                placeholder = Gtk.Label(f"{material_type} properties will be implemented")
                placeholder.get_style_context().add_class("dim-label")
                container.pack_start(placeholder, True, True, 0)
            def _add_advanced_sections(self, container):
                pass
            def _connect_material_signals(self):
                pass
            def _load_material_specific_data(self):
                pass
            def _validate_material_specific_field(self, widget):
                pass
            def _validate_all_material_fields(self):
                pass
            def _collect_material_specific_data(self):
                return {}
        
        return GenericMaterialDialog(parent, material_type, material_data)
    
    return dialog_class(parent, material_data)
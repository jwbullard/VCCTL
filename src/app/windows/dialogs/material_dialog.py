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
        print(f"DEBUG: MaterialDialogBase.__init__ called with material_type='{material_type}', material_data={material_data}")
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
        
        # Load data (for both editing and new materials)
        self._load_material_data()
        
        # Check immutable status AFTER all UI is set up (only for edit mode)
        if self.is_edit_mode:
            self._check_and_handle_immutable()
        
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
        
        # Enable name editing for cement materials (now uses integer ID as primary key)
        # Only disable for aggregates which still use display_name as primary key
        if self.is_edit_mode and self.material_type == 'aggregate':
            self.name_entry.set_sensitive(False)
            self.name_entry.set_tooltip_text("Aggregate display name cannot be changed (it's the primary key)")
        elif self.is_edit_mode:
            self.name_entry.set_tooltip_text("You can rename this material")
        
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
        notes_scrolled.set_size_request(400, 120)  # Set minimum width to 400px
        notes_scrolled.set_hexpand(True)  # Allow horizontal expansion
        
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
        print(f"DEBUG: _load_material_data called, material_data={self.material_data}")
        if not self.material_data:
            # Even for new materials, call material-specific data loading
            # to set up defaults
            print("DEBUG: Calling _load_material_specific_data for new material")
            self._load_material_specific_data()
            return
        
        try:
            # Load basic fields - handle different primary key fields
            if self.material_type == 'aggregate':
                # Aggregates use display_name as primary key
                name = self.material_data.get('display_name', '')
            else:
                # Most materials use name as primary key
                name = self.material_data.get('name', '')
            self.name_entry.set_text(name)
            
            description = self.material_data.get('description', '')
            if description:
                # Decode hex-encoded description if needed
                decoded_description = self._decode_description_if_hex(description)
                self.description_buffer.set_text(decoded_description)
            
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
            
            # Trigger validation after loading data
            self._validate_all()
            
        except Exception as e:
            self.logger.error(f"Failed to load material data: {e}")
    
    @abstractmethod
    def _load_material_specific_data(self) -> None:
        """Load material-specific data into form fields."""
        pass
    
    def _on_field_changed(self, widget) -> None:
        """Handle field change events."""
        # Clear previous validation errors for this field
        if widget == self.name_entry:
            self.validation_errors.pop('name', None)
        elif widget == self.specific_gravity_spin:
            self.validation_errors.pop('specific_gravity', None)
        
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
        
        # Always clear name validation errors first
        self.validation_errors.pop('name', None)
        
        if not name:
            self.validation_errors['name'] = "Material name is required"
        elif len(name) < 2:
            self.validation_errors['name'] = "Material name must be at least 2 characters"
        elif len(name) > 100:
            self.validation_errors['name'] = "Material name cannot exceed 100 characters"
        else:
            # Check for duplicate names (if not in edit mode or name changed)
            if self.material_type == 'aggregate':
                original_name = self.material_data.get('display_name', '') if self.material_data else ''
            else:
                original_name = self.material_data.get('name', '') if self.material_data else ''
            
            if not self.is_edit_mode or name != original_name:
                if self._check_name_exists(name):
                    self.validation_errors['name'] = f"A {self.material_type} named '{name}' already exists"
                # If name doesn't exist, error was already cleared above
            # If same name as original, error was already cleared above
    
    def _validate_specific_gravity(self) -> None:
        """Validate the specific gravity field."""
        sg = self.specific_gravity_spin.get_value()
        
        # Always clear specific gravity validation errors and warnings first
        self.validation_errors.pop('specific_gravity', None)
        self.validation_warnings.pop('specific_gravity', None)
        
        if sg <= 0:
            self.validation_errors['specific_gravity'] = "Specific gravity must be positive"
        elif sg < 1.0:
            self.validation_warnings['specific_gravity'] = "Specific gravity less than 1.0 is unusual"
        elif sg > 5.0:
            self.validation_warnings['specific_gravity'] = "Specific gravity greater than 5.0 is unusual"
        # If sg is valid (1.0 <= sg <= 5.0), errors and warnings were already cleared above
    
    @abstractmethod
    def _validate_material_specific_field(self, widget) -> None:
        """Validate material-specific fields."""
        pass
    
    def _check_name_exists(self, name: str) -> bool:
        """Check if a material with the given name already exists."""
        try:
            service = self._get_material_service()
            if service:
                if self.material_type == 'aggregate':
                    # For aggregates, check by display_name (primary key)
                    with service.db_service.get_read_only_session() as session:
                        existing = session.query(service.model).filter_by(display_name=name).first()
                        return existing is not None
                else:
                    # For cement materials, check by name
                    existing = service.get_by_name(name)
                    if existing is not None:
                        # If in edit mode, ignore if it's the same material being edited
                        if self.is_edit_mode and existing.id == self.material_data.get('id'):
                            return False
                        return True
                    return False
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
            'inert_filler': self.service_container.inert_filler_service,
            'silica_fume': self.service_container.silica_fume_service,
            'limestone': self.service_container.limestone_service
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
    
    def _check_and_handle_immutable(self) -> None:
        """Check if cement is immutable and handle UI accordingly."""
        if not self.material_data or self.material_type != 'cement':
            return
            
        is_immutable = self.material_data.get('immutable', False)
        
        if is_immutable:
            self._disable_all_inputs()
            self._show_immutable_message()
            self._replace_save_with_duplicate_button()
        else:
            self._enable_all_inputs()
            self._hide_immutable_message()
    
    def _disable_all_inputs(self) -> None:
        """Disable all input fields for immutable cements."""
        # Disable basic fields
        self.name_entry.set_sensitive(False)
        self.source_entry.set_sensitive(False)
        self.specific_gravity_spin.set_sensitive(False)
        
        # Disable text views
        self.description_textview.set_sensitive(False)
        self.notes_textview.set_sensitive(False)
        
        # Disable all spin buttons in phase composition
        if hasattr(self, 'phase_spins'):
            for spin in self.phase_spins.values():
                spin.set_sensitive(False)
        
        if hasattr(self, 'phase_volume_spins'):
            for spin in self.phase_volume_spins.values():
                spin.set_sensitive(False)
                
        if hasattr(self, 'phase_surface_spins'):
            for spin in self.phase_surface_spins.values():
                spin.set_sensitive(False)
        
        # Disable gypsum fields
        if hasattr(self, 'dihyd_spin'):
            self.dihyd_spin.set_sensitive(False)
        if hasattr(self, 'hemihyd_spin'):
            self.hemihyd_spin.set_sensitive(False)
        if hasattr(self, 'anhyd_spin'):
            self.anhyd_spin.set_sensitive(False)
        if hasattr(self, 'dihyd_volume_spin'):
            self.dihyd_volume_spin.set_sensitive(False)
        if hasattr(self, 'hemihyd_volume_spin'):
            self.hemihyd_volume_spin.set_sensitive(False)
        if hasattr(self, 'anhyd_volume_spin'):
            self.anhyd_volume_spin.set_sensitive(False)
        
        # Disable PSD fields
        if hasattr(self, 'psd_mode_combo'):
            self.psd_mode_combo.set_sensitive(False)
        if hasattr(self, 'psd_tree'):
            self.psd_tree.set_sensitive(False)
        
        # Disable all PSD parameter spins
        psd_spins = ['psd_d50_spin', 'psd_n_spin', 'psd_dmax_spin', 'psd_exponent_spin']
        for spin_name in psd_spins:
            if hasattr(self, spin_name):
                getattr(self, spin_name).set_sensitive(False)
    
    def _enable_all_inputs(self) -> None:
        """Enable all input fields for mutable cements."""
        # Enable basic fields
        self.name_entry.set_sensitive(True)
        self.source_entry.set_sensitive(True)
        self.specific_gravity_spin.set_sensitive(True)
        
        # Enable text views
        self.description_textview.set_sensitive(True)
        self.notes_textview.set_sensitive(True)
        
        # Enable all spin buttons in phase composition
        if hasattr(self, 'phase_spins'):
            for spin in self.phase_spins.values():
                spin.set_sensitive(True)
        
        if hasattr(self, 'phase_volume_spins'):
            for spin in self.phase_volume_spins.values():
                spin.set_sensitive(True)
                
        if hasattr(self, 'phase_surface_spins'):
            for spin in self.phase_surface_spins.values():
                spin.set_sensitive(True)
        
        # Enable gypsum fields
        if hasattr(self, 'dihyd_spin'):
            self.dihyd_spin.set_sensitive(True)
        if hasattr(self, 'hemihyd_spin'):
            self.hemihyd_spin.set_sensitive(True)
        if hasattr(self, 'anhyd_spin'):
            self.anhyd_spin.set_sensitive(True)
        if hasattr(self, 'dihyd_volume_spin'):
            self.dihyd_volume_spin.set_sensitive(True)
        if hasattr(self, 'hemihyd_volume_spin'):
            self.hemihyd_volume_spin.set_sensitive(True)
        if hasattr(self, 'anhyd_volume_spin'):
            self.anhyd_volume_spin.set_sensitive(True)
        
        # Enable PSD fields
        if hasattr(self, 'psd_mode_combo'):
            self.psd_mode_combo.set_sensitive(True)
        if hasattr(self, 'psd_tree'):
            self.psd_tree.set_sensitive(True)
        
        # Enable all PSD parameter spins
        psd_spins = ['psd_d50_spin', 'psd_n_spin', 'psd_dmax_spin', 'psd_exponent_spin']
        for spin_name in psd_spins:
            if hasattr(self, spin_name):
                getattr(self, spin_name).set_sensitive(True)
    
    def _show_immutable_message(self) -> None:
        """Show message that cement is read-only."""
        if not hasattr(self, 'immutable_message_bar'):
            # Create info bar
            self.immutable_message_bar = Gtk.InfoBar()
            self.immutable_message_bar.set_message_type(Gtk.MessageType.INFO)
            
            # Add message
            message_label = Gtk.Label()
            message_label.set_markup('<b>This is an original database cement.</b> Duplicate this cement to make changes.')
            message_label.set_halign(Gtk.Align.START)
            
            content_area = self.immutable_message_bar.get_content_area()
            content_area.add(message_label)
            
            # Insert at top of dialog content
            content_box = self.get_content_area()
            content_box.pack_start(self.immutable_message_bar, False, False, 0)
            content_box.reorder_child(self.immutable_message_bar, 0)
            
        self.immutable_message_bar.show_all()
    
    def _hide_immutable_message(self) -> None:
        """Hide the immutable message bar."""
        if hasattr(self, 'immutable_message_bar'):
            self.immutable_message_bar.hide()
    
    def _replace_save_with_duplicate_button(self) -> None:
        """Replace Save button with Duplicate to Edit button."""
        self.save_button.hide()
        
        if not hasattr(self, 'duplicate_button'):
            # Create duplicate button
            self.duplicate_button = self.add_button('Duplicate to Edit', Gtk.ResponseType.APPLY)
            self.duplicate_button.get_style_context().add_class('suggested-action')
            
        self.duplicate_button.show()
        self.set_default_response(Gtk.ResponseType.APPLY)
    
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
        
        name = self.name_entry.get_text().strip()
        
        # Collect ALL form data for both create and edit modes
        # The main difference is how we handle the primary key field
        if self.material_type == 'aggregate':
            if self.is_edit_mode:
                # For aggregate updates, don't include display_name (it's the primary key)
                data = {
                    'name': name,
                    'specific_gravity': self.specific_gravity_spin.get_value(),
                    'source': self.source_entry.get_text().strip() if self.source_entry.get_text().strip() else None,
                    'notes': notes.strip() if notes.strip() else None
                }
            else:
                # For new aggregates, include both name and display_name
                data = {
                    'display_name': name,
                    'name': name,  # Also set name field for aggregates
                    'description': description.strip() if description.strip() else None,
                    'source': self.source_entry.get_text().strip() if self.source_entry.get_text().strip() else None,
                    'specific_gravity': self.specific_gravity_spin.get_value(),
                    'notes': notes.strip() if notes.strip() else None
                }
        else:
            # For cement materials
            if self.is_edit_mode:
                # For cement updates, include name (now editable since using integer ID primary key)
                data = {
                    'name': name,
                    'description': description.strip() if description.strip() else None,
                    'specific_gravity': self.specific_gravity_spin.get_value(),
                    'source': self.source_entry.get_text().strip() if self.source_entry.get_text().strip() else None,
                    'notes': notes.strip() if notes.strip() else None
                }
            else:
                # For new materials, include name
                data = {
                    'name': name,
                    'description': description.strip() if description.strip() else None,
                    'source': self.source_entry.get_text().strip() if self.source_entry.get_text().strip() else None,
                    'specific_gravity': self.specific_gravity_spin.get_value(),
                    'notes': notes.strip() if notes.strip() else None
                }
        
        # Add material-specific data (phase fractions, Blaine fineness, etc.)
        material_data = self._collect_material_specific_data()
        data.update(material_data)
        
        return data
    
    def _decode_description_if_hex(self, description: str) -> str:
        """Decode description from hex if it appears to be hex-encoded."""
        try:
            if not description or not description.strip():
                return ""
            
            desc_clean = description.strip()
            
            # Remove any whitespace for hex validation
            hex_only = ''.join(desc_clean.split())
            
            # Check if it looks like hex (even length, only hex characters)
            if (len(hex_only) % 2 == 0 and 
                len(hex_only) > 10 and  # Must be reasonably long
                all(c in '0123456789abcdefABCDEF' for c in hex_only)):
                
                try:
                    import binascii
                    decoded_bytes = binascii.unhexlify(hex_only)
                    decoded_text = decoded_bytes.decode('utf-8', errors='ignore')
                    # Keep the original line breaks for proper formatting
                    return decoded_text if decoded_text else description
                except Exception:
                    return description
            
            return description
        except Exception:
            return description or ""
    
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
                # Update existing material using correct primary key
                if self.material_type == 'aggregate':
                    # For aggregates, use display_name as the primary key
                    material_id = self.material_data['display_name']
                elif self.material_type in ['inert_filler', 'limestone', 'silica_fume', 'fly_ash', 'slag']:
                    # For materials with name-based primary keys, use name
                    material_id = self.material_data['name']
                else:
                    # For cement materials, use integer ID as the primary key
                    material_id = self.material_data['id']
                
                # Convert data to appropriate model format
                if self.material_type == 'cement':
                    from app.models.cement import CementUpdate
                    update_data = CementUpdate(**data)
                elif self.material_type == 'aggregate':
                    from app.models.aggregate import AggregateUpdate
                    update_data = AggregateUpdate(**data)
                elif self.material_type == 'silica_fume':
                    from app.models.silica_fume import SilicaFumeUpdate
                    update_data = SilicaFumeUpdate(**data)
                elif self.material_type == 'limestone':
                    from app.models.limestone import LimestoneUpdate
                    update_data = LimestoneUpdate(**data)
                elif self.material_type == 'inert_filler':
                    from app.models.inert_filler import InertFillerUpdate
                    update_data = InertFillerUpdate(**data)
                elif self.material_type == 'fly_ash':
                    from app.models.fly_ash import FlyAshUpdate
                    update_data = FlyAshUpdate(**data)
                elif self.material_type == 'slag':
                    from app.models.slag import SlagUpdate
                    update_data = SlagUpdate(**data)
                else:
                    update_data = data
                
                updated_material = service.update(material_id, update_data)
                self.logger.info(f"Updated {self.material_type}: {getattr(updated_material, 'name', getattr(updated_material, 'display_name', 'unknown'))}")
            else:
                # Create new material
                if self.material_type == 'cement':
                    from app.models.cement import CementCreate
                    create_data = CementCreate(**data)
                elif self.material_type == 'aggregate':
                    from app.models.aggregate import AggregateCreate
                    create_data = AggregateCreate(**data)
                elif self.material_type == 'silica_fume':
                    from app.models.silica_fume import SilicaFumeCreate
                    create_data = SilicaFumeCreate(**data)
                elif self.material_type == 'limestone':
                    from app.models.limestone import LimestoneCreate
                    create_data = LimestoneCreate(**data)
                elif self.material_type == 'inert_filler':
                    from app.models.inert_filler import InertFillerCreate
                    create_data = InertFillerCreate(**data)
                elif self.material_type == 'fly_ash':
                    from app.models.fly_ash import FlyAshCreate
                    create_data = FlyAshCreate(**data)
                elif self.material_type == 'slag':
                    from app.models.slag import SlagCreate
                    create_data = SlagCreate(**data)
                else:
                    create_data = data
                
                created_material = service.create(create_data)
                self.logger.info(f"Created {self.material_type}: {getattr(created_material, 'name', getattr(created_material, 'display_name', 'unknown'))}")
            
            # Show success message
            action = "updated" if self.is_edit_mode else "created"
            self.parent_window.update_status(f"Material {action} successfully", "success", 3)
            
            # Refresh Mix Design panel material lists if it exists
            if hasattr(self.parent_window, 'mix_design_panel'):
                self.parent_window.mix_design_panel.refresh_material_lists()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save material: {e}")
            
            # Show error in validation area
            self.validation_errors['save'] = str(e)
            self._update_validation_display()
            
            return False
    
    def _duplicate_material(self) -> bool:
        """Duplicate the current immutable material as a mutable copy."""
        if not self.material_data or self.material_type != 'cement':
            return False
            
        try:
            # Create a copy of current material data
            original_name = self.material_data.get('name', 'cement')
            new_name = f"{original_name}_copy"
            
            # Check if the name already exists and find a unique name
            counter = 1
            final_name = new_name
            
            # Get cement service for checking duplicates
            cement_service = self.service_container.get_cement_service()
            while cement_service.get_by_name(final_name):
                counter += 1
                final_name = f"{new_name}_{counter}"
            
            # Collect all current form data (including PSD data)
            duplicate_data = self._collect_form_data()
            
            # Override key fields for the duplicate
            duplicate_data['name'] = final_name
            duplicate_data['immutable'] = False  # New copy is mutable
            
            # Remove the ID field if present (for new cement)
            if 'id' in duplicate_data:
                del duplicate_data['id']
            
            # Create the duplicate cement
            from app.models.cement import CementCreate
            
            # Create new cement
            create_data = CementCreate(**duplicate_data)
            new_cement = cement_service.create(create_data)
            
            # Show success message with option to edit
            dialog = Gtk.MessageDialog(
                transient_for=self.get_toplevel(),
                flags=0,
                message_type=Gtk.MessageType.QUESTION,
                buttons=Gtk.ButtonsType.YES_NO,
                text="Cement Duplicated Successfully"
            )
            dialog.format_secondary_text(
                f"Created '{final_name}' as a mutable copy.\\n\\n"
                "Would you like to open the new cement for editing?"
            )
            
            response = dialog.run()
            dialog.destroy()
            
            if response == Gtk.ResponseType.YES:
                # Open new dialog for editing the duplicate
                from app.windows.dialogs.material_dialog import CementDialog
                
                edit_dialog = CementDialog(
                    self.parent_window,
                    new_cement.to_dict()
                )
                
                edit_response = edit_dialog.run()
                edit_dialog.destroy()
                
                # If user saved the new cement, refresh the original caller
                if edit_response == Gtk.ResponseType.OK:
                    # Emit signal to refresh materials list if possible
                    pass
            
            return True
            
        except Exception as e:
            # Show error message
            dialog = Gtk.MessageDialog(
                transient_for=self.get_toplevel(),
                flags=0,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Error Duplicating Cement"
            )
            dialog.format_secondary_text(f"Failed to duplicate cement: {str(e)}")
            dialog.run()
            dialog.destroy()
            
        return False
    
    def _on_response(self, widget: Gtk.Dialog, response_id: int) -> None:
        """Handle dialog response."""
        if response_id == Gtk.ResponseType.OK:
            # Try to save
            if self._save_material():
                # Don't destroy here - let the dialog.run() return naturally
                # This allows the caller to receive the OK response and refresh the UI
                return
            else:
                # Prevent dialog from closing by stopping the response
                self.stop_emission_by_name('response')
        elif response_id == Gtk.ResponseType.APPLY:
            # Handle duplicate button click
            if self._duplicate_material():
                # Close dialog after successful duplication
                return
            else:
                # Prevent dialog from closing if duplication failed
                self.stop_emission_by_name('response')


class CementDialog(MaterialDialogBase):
    """Dialog for cement materials."""
    
    # Phase specific gravities (g/cm³)
    PHASE_SPECIFIC_GRAVITIES = {
        'c3s': 3.15,     # Tricalcium silicate
        'c2s': 3.28,     # Dicalcium silicate
        'c3a': 3.04,     # Tricalcium aluminate
        'c4af': 3.73,    # Tetracalcium aluminoferrite
        'k2so4': 2.66,   # Potassium sulfate
        'na2so4': 2.68   # Sodium sulfate
    }
    
    # Gypsum component specific gravities (g/cm³)
    GYPSUM_SPECIFIC_GRAVITIES = {
        'dihyd': 2.32,   # Dihydrate (CaSO4·2H2O)
        'hemihyd': 2.74, # Hemihydrate (CaSO4·0.5H2O)
        'anhyd': 2.61    # Anhydrite (CaSO4)
    }
    
    def __init__(self, parent: 'VCCTLMainWindow', material_data: Optional[Dict[str, Any]] = None):
        print(f"DEBUG: CementDialog.__init__ called with material_data={material_data}")
        self._updating_fractions = False  # Flag to prevent recursive updates
        super().__init__(parent, "cement", material_data)
    
    def _create_properties_tab(self) -> None:
        """Override to create separate Chemical and Physical properties tabs for cement."""
        # Create Chemical Properties tab
        self._create_chemical_properties_tab()
        
        # Create Physical Properties tab  
        self._create_physical_properties_tab()
    
    def _create_chemical_properties_tab(self) -> None:
        """Create the chemical properties tab."""
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        # Chemical properties container
        chem_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        chem_box.set_margin_top(20)
        chem_box.set_margin_bottom(20)
        chem_box.set_margin_left(20)
        chem_box.set_margin_right(20)
        
        # Add chemical composition sections
        self._add_chemical_composition_section(chem_box)
        
        scrolled.add(chem_box)
        self.notebook.append_page(scrolled, Gtk.Label("Chemical Properties"))
    
    def _create_physical_properties_tab(self) -> None:
        """Create the physical properties tab."""
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        # Physical properties container
        phys_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        phys_box.set_margin_top(20)
        phys_box.set_margin_bottom(20)
        phys_box.set_margin_left(20)
        phys_box.set_margin_right(20)
        
        # Add physical property sections
        self._add_physical_properties_section(phys_box)
        self._add_psd_section(phys_box)
        
        scrolled.add(phys_box)
        self.notebook.append_page(scrolled, Gtk.Label("Physical Properties"))
    
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
    
    def _add_chemical_composition_section(self, container: Gtk.Box) -> None:
        """Add chemical composition section with phase fractions and gypsum components."""
        # Chemical composition section
        comp_frame = Gtk.Frame(label="Chemical Composition (%)")
        comp_grid = Gtk.Grid()
        comp_grid.set_margin_top(10)
        comp_grid.set_margin_bottom(10)
        comp_grid.set_margin_left(15)
        comp_grid.set_margin_right(15)
        comp_grid.set_row_spacing(10)
        comp_grid.set_column_spacing(15)
        
        # Header row
        comp_label = Gtk.Label("Phase")
        comp_label.set_halign(Gtk.Align.CENTER)
        comp_label.get_style_context().add_class("form-label")
        comp_label.set_markup("<b>Phase</b>")
        
        mass_header = Gtk.Label("Mass %")
        mass_header.set_halign(Gtk.Align.CENTER)
        mass_header.get_style_context().add_class("form-label")
        mass_header.set_markup("<b>Mass %</b>")
        
        volume_header = Gtk.Label("Volume %")
        volume_header.set_halign(Gtk.Align.CENTER)
        volume_header.get_style_context().add_class("form-label")
        volume_header.set_markup("<b>Volume %</b>")
        
        surface_header = Gtk.Label("Surface %")
        surface_header.set_halign(Gtk.Align.CENTER)
        surface_header.get_style_context().add_class("form-label")
        surface_header.set_markup("<b>Surface %</b>")
        
        comp_grid.attach(comp_label, 0, 0, 1, 1)
        comp_grid.attach(mass_header, 1, 0, 1, 1)
        comp_grid.attach(volume_header, 2, 0, 1, 1)
        comp_grid.attach(surface_header, 3, 0, 1, 1)
        
        # Phase composition with 3 columns
        phases = [
            ("C₃S:", "c3s", 50.0, "Tricalcium silicate - main binding phase"),
            ("C₂S:", "c2s", 25.0, "Dicalcium silicate - slow hydrating phase"),
            ("C₃A:", "c3a", 8.0, "Tricalcium aluminate - rapid hydrating"),
            ("C₄AF:", "c4af", 10.0, "Tetracalcium aluminoferrite - moderate hydrating"),
            ("K₂SO₄:", "k2so4", 0.0, "Potassium sulfate"),
            ("Na₂SO₄:", "na2so4", 0.0, "Sodium sulfate")
        ]
        
        self.phase_spins = {}
        for i, (label_text, phase_key, default_value, tooltip) in enumerate(phases):
            row = i + 1  # Offset by 1 for header row
            
            # Phase label
            label = Gtk.Label(label_text)
            label.set_halign(Gtk.Align.END)
            label.get_style_context().add_class("form-label")
            label.set_tooltip_text(tooltip)
            
            # Mass fraction spin button
            mass_spin = Gtk.SpinButton.new_with_range(0.0, 100.0, 0.01)
            mass_spin.set_digits(2)
            mass_spin.set_value(default_value)
            mass_spin.set_tooltip_text(f"{tooltip} - Mass fraction")
            
            # Volume fraction spin button (enabled for user input)
            volume_spin = Gtk.SpinButton.new_with_range(0.0, 100.0, 0.01)
            volume_spin.set_digits(2)
            volume_spin.set_value(0.0)
            volume_spin.set_tooltip_text(f"{tooltip} - Volume fraction")
            
            # Surface area spin button (enabled for user input)
            surface_spin = Gtk.SpinButton.new_with_range(0.0, 100.0, 0.01)
            surface_spin.set_digits(2)
            surface_spin.set_value(0.0)
            surface_spin.set_tooltip_text(f"{tooltip} - Surface area fraction")
            
            comp_grid.attach(label, 0, row, 1, 1)
            comp_grid.attach(mass_spin, 1, row, 1, 1)
            comp_grid.attach(volume_spin, 2, row, 1, 1)
            comp_grid.attach(surface_spin, 3, row, 1, 1)
            
            # Store references to all spin buttons
            self.phase_spins[phase_key] = mass_spin
            # Store volume and surface spin buttons
            if not hasattr(self, 'phase_volume_spins'):
                self.phase_volume_spins = {}
            if not hasattr(self, 'phase_surface_spins'):
                self.phase_surface_spins = {}
            self.phase_volume_spins[phase_key] = volume_spin
            self.phase_surface_spins[phase_key] = surface_spin
            
            # Connect signal handlers for bidirectional updates
            mass_spin.connect('value-changed', self._on_mass_fraction_changed, phase_key)
            volume_spin.connect('value-changed', self._on_volume_fraction_changed, phase_key)
            surface_spin.connect('value-changed', self._on_surface_fraction_changed, phase_key)
        
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
        
        # Add total row with proper offset (header + phases + 1 for spacing)
        total_row = len(phases) + 1 + 1  # phases + 1 for header + 1 for spacing
        comp_grid.attach(sum_label, 0, total_row, 1, 1)
        comp_grid.attach(self.sum_display, 1, total_row, 1, 1)
        comp_grid.attach(sum_unit_label, 2, total_row, 1, 1)
        
        # Add gypsum mass fractions after total row
        gypsum_row = total_row + 2  # Skip one row for spacing
        
        # Dihydrate gypsum (DIHYD)
        dihyd_label = Gtk.Label("Dihydrate Gypsum:")
        dihyd_label.set_halign(Gtk.Align.END)
        dihyd_label.get_style_context().add_class("form-label")
        
        self.dihyd_spin = Gtk.SpinButton.new_with_range(0, 100, 0.1)
        self.dihyd_spin.set_value(0.0)
        self.dihyd_spin.set_digits(3)
        
        self.dihyd_volume_spin = Gtk.SpinButton.new_with_range(0, 100, 0.1)
        self.dihyd_volume_spin.set_value(0.0)
        self.dihyd_volume_spin.set_digits(3)
        
        dihyd_mass_unit_label = Gtk.Label("% mass")
        dihyd_mass_unit_label.get_style_context().add_class("dim-label")
        
        dihyd_vol_unit_label = Gtk.Label("% vol")
        dihyd_vol_unit_label.get_style_context().add_class("dim-label")
        
        comp_grid.attach(dihyd_label, 0, gypsum_row, 1, 1)
        comp_grid.attach(self.dihyd_spin, 1, gypsum_row, 1, 1)
        comp_grid.attach(self.dihyd_volume_spin, 2, gypsum_row, 1, 1)
        comp_grid.attach(dihyd_mass_unit_label, 3, gypsum_row, 1, 1)
        comp_grid.attach(dihyd_vol_unit_label, 4, gypsum_row, 1, 1)
        gypsum_row += 1
        
        # Hemihydrate gypsum (HEMIHYD)
        hemihyd_label = Gtk.Label("Hemihydrate Gypsum:")
        hemihyd_label.set_halign(Gtk.Align.END)
        hemihyd_label.get_style_context().add_class("form-label")
        
        self.hemihyd_spin = Gtk.SpinButton.new_with_range(0, 100, 0.1)
        self.hemihyd_spin.set_value(0.0)
        self.hemihyd_spin.set_digits(3)
        
        self.hemihyd_volume_spin = Gtk.SpinButton.new_with_range(0, 100, 0.1)
        self.hemihyd_volume_spin.set_value(0.0)
        self.hemihyd_volume_spin.set_digits(3)
        
        hemihyd_mass_unit_label = Gtk.Label("% mass")
        hemihyd_mass_unit_label.get_style_context().add_class("dim-label")
        
        hemihyd_vol_unit_label = Gtk.Label("% vol")
        hemihyd_vol_unit_label.get_style_context().add_class("dim-label")
        
        comp_grid.attach(hemihyd_label, 0, gypsum_row, 1, 1)
        comp_grid.attach(self.hemihyd_spin, 1, gypsum_row, 1, 1)
        comp_grid.attach(self.hemihyd_volume_spin, 2, gypsum_row, 1, 1)
        comp_grid.attach(hemihyd_mass_unit_label, 3, gypsum_row, 1, 1)
        comp_grid.attach(hemihyd_vol_unit_label, 4, gypsum_row, 1, 1)
        gypsum_row += 1
        
        # Anhydrite gypsum (ANHYD)
        anhyd_label = Gtk.Label("Anhydrite Gypsum:")
        anhyd_label.set_halign(Gtk.Align.END)
        anhyd_label.get_style_context().add_class("form-label")
        
        self.anhyd_spin = Gtk.SpinButton.new_with_range(0, 100, 0.1)
        self.anhyd_spin.set_value(0.0)
        self.anhyd_spin.set_digits(3)
        
        self.anhyd_volume_spin = Gtk.SpinButton.new_with_range(0, 100, 0.1)
        self.anhyd_volume_spin.set_value(0.0)
        self.anhyd_volume_spin.set_digits(3)
        
        anhyd_mass_unit_label = Gtk.Label("% mass")
        anhyd_mass_unit_label.get_style_context().add_class("dim-label")
        
        anhyd_vol_unit_label = Gtk.Label("% vol")
        anhyd_vol_unit_label.get_style_context().add_class("dim-label")
        
        comp_grid.attach(anhyd_label, 0, gypsum_row, 1, 1)
        comp_grid.attach(self.anhyd_spin, 1, gypsum_row, 1, 1)
        comp_grid.attach(self.anhyd_volume_spin, 2, gypsum_row, 1, 1)
        comp_grid.attach(anhyd_mass_unit_label, 3, gypsum_row, 1, 1)
        comp_grid.attach(anhyd_vol_unit_label, 4, gypsum_row, 1, 1)
        
        comp_frame.add(comp_grid)
        container.pack_start(comp_frame, False, False, 0)
        
    def _add_physical_properties_section(self, container: Gtk.Box) -> None:
        """Add physical properties section including setting times and calculations."""
        # Physical properties frame
        phys_frame = Gtk.Frame(label="Physical Properties")
        phys_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        phys_box.set_margin_top(10)
        phys_box.set_margin_bottom(10)
        phys_box.set_margin_left(15)
        phys_box.set_margin_right(15)
        
        # Setting times section removed per user request
        
        # Calculated properties section
        calc_grid = Gtk.Grid()
        calc_grid.set_row_spacing(10)
        calc_grid.set_column_spacing(15)
        
        # Density calculation display
        density_label = Gtk.Label("Calculated Density:")
        density_label.set_halign(Gtk.Align.END)
        density_label.get_style_context().add_class("form-label")
        
        self.density_display = Gtk.Label("3.15")
        self.density_display.set_halign(Gtk.Align.START)
        self.density_display.get_style_context().add_class("calculated-value")
        
        density_unit_label = Gtk.Label("g/cm³")
        density_unit_label.get_style_context().add_class("dim-label")
        
        calc_grid.attach(density_label, 0, 0, 1, 1)
        calc_grid.attach(self.density_display, 1, 0, 1, 1)
        calc_grid.attach(density_unit_label, 2, 0, 1, 1)
        
        # Heat of hydration removed per user request
        
        phys_box.pack_start(calc_grid, False, False, 0)
        
        phys_frame.add(phys_box)
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
        
        # Description with data source info
        self.psd_desc_label = Gtk.Label()
        self.psd_desc_label.set_markup('<i>Particle size distribution data</i>')
        self.psd_desc_label.set_halign(Gtk.Align.START)
        custom_box.pack_start(self.psd_desc_label, False, False, 0)
        
        # Summary information
        self.psd_summary_label = Gtk.Label()
        self.psd_summary_label.set_halign(Gtk.Align.START)
        self.psd_summary_label.get_style_context().add_class('dim-label')
        custom_box.pack_start(self.psd_summary_label, False, False, 0)
        
        # Scrolled window for points table
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_size_request(-1, 150)
        
        # Create list store for PSD points (Size μm, Mass Fraction)
        self.psd_store = Gtk.ListStore(float, float)  # diameter_um, mass_fraction
        
        # Data will be loaded from database in _load_psd_data()
        
        # Create tree view
        self.psd_tree = Gtk.TreeView(model=self.psd_store)
        self.psd_tree.set_reorderable(True)
        
        # Size column (editable)
        size_renderer = Gtk.CellRendererText()
        size_renderer.set_property('editable', True)
        size_renderer.connect('edited', self._on_psd_size_edited)
        size_column = Gtk.TreeViewColumn("Diameter (μm)", size_renderer, text=0)
        size_column.set_resizable(True)
        size_column.set_cell_data_func(size_renderer, self._format_diameter_cell, None)
        self.psd_tree.append_column(size_column)
        
        # Mass fraction column (editable)
        fraction_renderer = Gtk.CellRendererText()
        fraction_renderer.set_property('editable', True)
        fraction_renderer.connect('edited', self._on_psd_percent_edited)
        fraction_column = Gtk.TreeViewColumn("Mass Fraction", fraction_renderer, text=1)
        fraction_column.set_resizable(True)
        fraction_column.set_cell_data_func(fraction_renderer, self._format_fraction_cell, None)
        self.psd_tree.append_column(fraction_column)
        
        scrolled.add(self.psd_tree)
        custom_box.pack_start(scrolled, True, True, 0)
        
        # Button row for add/remove/save
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        button_box.set_halign(Gtk.Align.START)
        
        # Add point button
        add_button = Gtk.Button.new_with_label("Add Point")
        add_button.connect('clicked', self._on_add_psd_point)
        button_box.pack_start(add_button, False, False, 0)
        
        # Remove point button
        remove_button = Gtk.Button.new_with_label("Remove Point")
        remove_button.connect('clicked', self._on_remove_psd_point)
        button_box.pack_start(remove_button, False, False, 0)
        
        # Import CSV button
        import_button = Gtk.Button.new_with_label("Import CSV")
        import_button.connect('clicked', self._on_import_csv_psd)
        import_button.set_tooltip_text("Import PSD data from CSV file (diameter_um, mass_fraction)")
        button_box.pack_start(import_button, False, False, 0)
        
        # Note: PSD data is now saved with the main Save button
        
        custom_box.pack_start(button_box, False, False, 0)
        
        # Note about data source
        note_label = Gtk.Label()
        note_label.set_markup('<i><small>Experimental data - click in table cells to edit values or use "Import CSV" button</small></i>')
        note_label.set_halign(Gtk.Align.START)
        note_label.get_style_context().add_class('dim-label')
        custom_box.pack_start(note_label, False, False, 0)
        
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
            
    def _format_diameter_cell(self, column, cell, model, tree_iter, data):
        """Format diameter cell with 3 decimal places."""
        diameter = model[tree_iter][0]
        cell.set_property('text', f'{diameter:.3f}')
    
    def _format_fraction_cell(self, column, cell, model, tree_iter, data):
        """Format mass fraction cell with scientific notation."""
        fraction = model[tree_iter][1]
        if fraction < 0.001:
            cell.set_property('text', f'{fraction:.2e}')
        else:
            cell.set_property('text', f'{fraction:.6f}')
    
    def _load_psd_data(self, set_mode=True) -> None:
        """Load PSD data from material data into the tree view."""
        if not self.material_data:
            return
            
        # Clear existing data
        self.psd_store.clear()
        
        # Check if we have custom PSD points
        psd_points_json = self.material_data.get('psd_custom_points')
        
        if psd_points_json:
            try:
                import json
                psd_points = json.loads(psd_points_json)
                
                # Add points to store
                for diameter, mass_fraction in psd_points:
                    self.psd_store.append([float(diameter), float(mass_fraction)])
                
                # Update summary label
                total_mass = sum(point[1] for point in psd_points)
                
                # Check if labels exist before setting
                if hasattr(self, 'psd_summary_label'):
                    self.psd_summary_label.set_markup(
                        f'<small>{len(psd_points)} data points, Total mass fraction: {total_mass:.6f}</small>'
                    )
                
                # Update description
                if hasattr(self, 'psd_desc_label'):
                    self.psd_desc_label.set_markup(
                        '<i>Experimental particle size distribution data</i>'
                    )
                
                # Only set mode to custom if requested (when auto-detecting)
                if set_mode and hasattr(self, 'psd_mode_combo'):
                    self.psd_mode_combo.set_active_id('custom')
                
            except (json.JSONDecodeError, ValueError, TypeError) as e:
                print(f'Error loading PSD data: {e}')
                self._load_default_psd_data()
        else:
            if set_mode:
                self._load_default_psd_data()
    
    def _load_default_psd_data(self) -> None:
        """Load default PSD data when no experimental data is available."""
        # Update labels for no data case
        self.psd_summary_label.set_markup(
            '<small>No experimental PSD data available</small>'
        )
        self.psd_desc_label.set_markup(
            '<i>No particle size distribution data found</i>'
        )
        
        # Set mode to Rosin-Rammler as default
        self.psd_mode_combo.set_active_id('rosin_rammler')
            
    def _on_psd_size_edited(self, renderer, path, new_text):
        """Handle editing of PSD size value."""
        try:
            value = float(new_text)
            if value > 0:
                self.psd_store[path][0] = value
        except ValueError:
            pass
            
    def _on_psd_percent_edited(self, renderer, path, new_text):
        """Handle editing of PSD mass fraction value."""
        try:
            value = float(new_text)
            if 0 <= value <= 1.0:  # Mass fractions should be 0-1
                self.psd_store[path][1] = value
                self._update_psd_summary()
        except ValueError:
            pass
            
    def _on_add_psd_point(self, button):
        """Add a new PSD point."""
        # Add a reasonable default point (10 μm, small mass fraction)
        self.psd_store.append([10.0, 0.001])
        self._update_psd_summary()
        
    def _on_remove_psd_point(self, button):
        """Remove selected PSD point."""
        selection = self.psd_tree.get_selection()
        model, treeiter = selection.get_selected()
        if treeiter:
            model.remove(treeiter)
            self._update_psd_summary()
    
    def _on_import_csv_psd(self, button):
        """Import PSD data from CSV file."""
        dialog = Gtk.FileChooserDialog(
            title="Import PSD Data from CSV",
            parent=self,
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
        dialog.add_button(Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        
        # Add CSV file filter
        csv_filter = Gtk.FileFilter()
        csv_filter.set_name("CSV Files")
        csv_filter.add_pattern("*.csv")
        csv_filter.add_mime_type("text/csv")
        dialog.add_filter(csv_filter)
        
        # Add all files filter
        all_filter = Gtk.FileFilter()
        all_filter.set_name("All Files")
        all_filter.add_pattern("*")
        dialog.add_filter(all_filter)
        
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            try:
                self._load_csv_psd_data(filename)
            except Exception as e:
                error_dialog = Gtk.MessageDialog(
                    transient_for=self,
                    flags=0,
                    message_type=Gtk.MessageType.ERROR,
                    buttons=Gtk.ButtonsType.OK,
                    text="Error importing CSV file"
                )
                error_dialog.format_secondary_text(f"Could not import PSD data: {e}")
                error_dialog.run()
                error_dialog.destroy()
        
        dialog.destroy()
    
    def _load_csv_psd_data(self, filename):
        """Load PSD data from CSV file."""
        import csv
        
        # Clear existing data
        self.psd_store.clear()
        
        with open(filename, 'r', encoding='utf-8') as file:
            # Try to detect if file has headers
            sample = file.read(1024)
            file.seek(0)
            
            # Simple heuristic: if first line contains non-numeric data, skip it
            first_line = file.readline().strip()
            file.seek(0)
            
            has_header = False
            try:
                # Try to parse first line as numbers
                parts = first_line.replace(',', ' ').split()
                if len(parts) >= 2:
                    float(parts[0])
                    float(parts[1])
            except (ValueError, IndexError):
                has_header = True
            
            # Parse CSV data
            reader = csv.reader(file)
            if has_header:
                next(reader)  # Skip header row
            
            loaded_points = []
            for row_num, row in enumerate(reader, start=1):
                if len(row) < 2:
                    continue  # Skip incomplete rows
                
                try:
                    # Support flexible column ordering
                    # Try diameter, mass_fraction first
                    diameter = float(row[0])
                    mass_fraction = float(row[1])
                    
                    # Validate data ranges
                    if diameter <= 0:
                        self.logger.warning(f"Invalid diameter {diameter} on row {row_num}, skipping")
                        continue
                    
                    if not (0 <= mass_fraction <= 1):
                        # Try to handle percentage format (0-100%) by converting to fraction
                        if 0 <= mass_fraction <= 100:
                            mass_fraction = mass_fraction / 100.0
                        else:
                            self.logger.warning(f"Invalid mass fraction {mass_fraction} on row {row_num}, skipping")
                            continue
                    
                    loaded_points.append((diameter, mass_fraction))
                    
                except (ValueError, IndexError) as e:
                    self.logger.warning(f"Could not parse row {row_num}: {row}, error: {e}")
                    continue
            
            if not loaded_points:
                raise ValueError("No valid PSD data points found in CSV file")
            
            # Sort by diameter (ascending)
            loaded_points.sort(key=lambda x: x[0])
            
            # Add points to store
            for diameter, mass_fraction in loaded_points:
                self.psd_store.append([diameter, mass_fraction])
            
            # Update summary and switch to custom tab
            self._update_psd_summary()
            
            # Update description to indicate data source
            self.psd_desc_label.set_markup(f'<i>Imported from: {filename.split("/")[-1]}</i>')
            
            # Switch to custom PSD mode to show the imported data
            self.psd_mode_combo.set_active_id('custom')
            
            # Show success message
            self.parent_window.update_status(f"Imported {len(loaded_points)} PSD data points from CSV", "success", 3)
            
            self.logger.info(f"Successfully imported {len(loaded_points)} PSD points from {filename}")
    
    def _update_psd_summary(self):
        """Update the PSD summary label with current data."""
        if not hasattr(self, 'psd_summary_label'):
            return
            
        # Count points and calculate total mass fraction
        num_points = len(self.psd_store)
        total_mass = 0.0
        
        for row in self.psd_store:
            total_mass += row[1]  # Mass fraction is column 1
        
        # Update summary
        self.psd_summary_label.set_markup(
            f'<small>{num_points} data points, Total mass fraction: {total_mass:.6f}</small>'
        )
        
        # Update description
        if hasattr(self, 'psd_desc_label'):
            if num_points > 0:
                self.psd_desc_label.set_markup(
                    '<i>Particle size distribution data (edited)</i>'
                )
            else:
                self.psd_desc_label.set_markup(
                    '<i>No particle size distribution data</i>'
                )
    
    def _on_save_psd_data(self, button):
        """Save edited PSD data to the database."""
        if not self.material_data or not hasattr(self, 'psd_store'):
            return
            
        try:
            # Extract data from store
            psd_points = []
            for row in self.psd_store:
                diameter = float(row[0])
                mass_fraction = float(row[1])
                psd_points.append([diameter, mass_fraction])
            
            # Convert to JSON
            import json
            psd_json = json.dumps(psd_points)
            
            # Update material data
            self.material_data['psd_custom_points'] = psd_json
            self.material_data['psd_mode'] = 'custom'
            
            # Save to database if we have cement service and ID
            if hasattr(self, 'cement_service') and 'id' in self.material_data:
                from app.models.cement import CementUpdate
                
                update_data = CementUpdate(
                    psd_custom_points=psd_json,
                    psd_mode='custom'
                )
                
                self.cement_service.update(self.material_data['id'], update_data)
                
                # Show success message
                dialog = Gtk.MessageDialog(
                    transient_for=self.get_toplevel(),
                    flags=0,
                    message_type=Gtk.MessageType.INFO,
                    buttons=Gtk.ButtonsType.OK,
                    text="PSD Data Saved"
                )
                dialog.format_secondary_text(
                    f"Successfully saved {len(psd_points)} PSD data points to the database."
                )
                dialog.run()
                dialog.destroy()
                
        except Exception as e:
            # Show error message
            dialog = Gtk.MessageDialog(
                transient_for=self.get_toplevel(),
                flags=0,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Error Saving PSD Data"
            )
            dialog.format_secondary_text(f"Failed to save PSD data: {str(e)}")
            dialog.run()
            dialog.destroy()
    
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
        # Note: Setting times moved to Physical Properties tab
        # This section can be used for future additional properties if needed
        pass
        
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
        for spin in self.phase_volume_spins.values():
            spin.connect('value-changed', self._on_field_changed)
        for spin in self.phase_surface_spins.values():
            spin.connect('value-changed', self._on_field_changed)
        
        # Connect gypsum mass and volume fraction signals for bidirectional conversion
        self.dihyd_spin.connect('value-changed', self._on_gypsum_mass_changed, 'dihyd')
        self.hemihyd_spin.connect('value-changed', self._on_gypsum_mass_changed, 'hemihyd')
        self.anhyd_spin.connect('value-changed', self._on_gypsum_mass_changed, 'anhyd')
        
        self.dihyd_volume_spin.connect('value-changed', self._on_gypsum_volume_changed, 'dihyd')
        self.hemihyd_volume_spin.connect('value-changed', self._on_gypsum_volume_changed, 'hemihyd')
        self.anhyd_volume_spin.connect('value-changed', self._on_gypsum_volume_changed, 'anhyd')
    
    def _load_material_specific_data(self) -> None:
        """Load cement-specific data."""
        print(f"DEBUG: CementDialog._load_material_specific_data called, material_data = {self.material_data}")
        if not self.material_data:
            print("DEBUG: No material_data, setting defaults for new cement")
            # For new materials, set default phase fraction values
            self._set_default_phase_fractions()
            # Update calculations with default values
            self._update_calculations()
            return
        else:
            print("DEBUG: Loading existing cement material data")
        
        # Load Blaine fineness
        blaine = self.material_data.get('blaine_fineness', 350)
        self.blaine_spin.set_value(float(blaine))
        
        # Load gypsum mass fractions (convert from fraction to percentage)
        dihyd = self.material_data.get('dihyd', 0.0)
        self.dihyd_spin.set_value(float(dihyd) * 100.0 if dihyd else 0.0)
        
        hemihyd = self.material_data.get('hemihyd', 0.0)
        self.hemihyd_spin.set_value(float(hemihyd) * 100.0 if hemihyd else 0.0)
        
        anhyd = self.material_data.get('anhyd', 0.0)
        self.anhyd_spin.set_value(float(anhyd) * 100.0 if anhyd else 0.0)
        
        # Load gypsum volume fractions (convert from fraction to percentage)
        dihyd_vol = self.material_data.get('dihyd_volume_fraction', 0.0)
        self.dihyd_volume_spin.set_value(float(dihyd_vol) * 100.0 if dihyd_vol else 0.0)
        
        hemihyd_vol = self.material_data.get('hemihyd_volume_fraction', 0.0)
        self.hemihyd_volume_spin.set_value(float(hemihyd_vol) * 100.0 if hemihyd_vol else 0.0)
        
        anhyd_vol = self.material_data.get('anhyd_volume_fraction', 0.0)
        self.anhyd_volume_spin.set_value(float(anhyd_vol) * 100.0 if anhyd_vol else 0.0)
        
        # Load phase composition
        phase_mapping = {
            'c3s': 'c3s_mass_fraction',
            'c2s': 'c2s_mass_fraction',
            'c3a': 'c3a_mass_fraction',
            'c4af': 'c4af_mass_fraction',
            'k2so4': 'k2so4_mass_fraction',
            'na2so4': 'na2so4_mass_fraction'
        }
        volume_mapping = {
            'c3s': 'c3s_volume_fraction',
            'c2s': 'c2s_volume_fraction',
            'c3a': 'c3a_volume_fraction',
            'c4af': 'c4af_volume_fraction',
            'k2so4': 'k2so4_volume_fraction',
            'na2so4': 'na2so4_volume_fraction'
        }
        surface_mapping = {
            'c3s': 'c3s_surface_fraction',
            'c2s': 'c2s_surface_fraction',
            'c3a': 'c3a_surface_fraction',
            'c4af': 'c4af_surface_fraction',
            'k2so4': 'k2so4_surface_fraction',
            'na2so4': 'na2so4_surface_fraction'
        }
        
        # Mass fractions
        for phase_key, spin in self.phase_spins.items():
            # Convert phase key to database field name
            db_field = phase_mapping.get(phase_key, phase_key)
            value = self.material_data.get(db_field, 0.0)
            # Convert fraction (0-1) to percentage (0-100) for display
            percentage_value = float(value) * 100.0 if value else 0.0
            spin.set_value(percentage_value)
        
        # Volume fractions
        for phase_key, spin in self.phase_volume_spins.items():
            db_field = volume_mapping.get(phase_key, phase_key)
            value = self.material_data.get(db_field, 0.0)
            percentage_value = float(value) * 100.0 if value else 0.0
            spin.set_value(percentage_value)
        
        # Surface fractions
        for phase_key, spin in self.phase_surface_spins.items():
            db_field = surface_mapping.get(phase_key, phase_key)
            value = self.material_data.get(db_field, 0.0)
            percentage_value = float(value) * 100.0 if value else 0.0
            spin.set_value(percentage_value)
        
        # Setting times loading removed per user request
        
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
            # Load actual PSD data using our new method (don't override mode)
            self._load_psd_data(set_mode=False)
        
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
    
    def _set_default_phase_fractions(self) -> None:
        """Set default phase fraction values for new cement materials."""
        # Debug: Check if widgets exist
        print(f"DEBUG: Setting default phase fractions for new cement")
        
        # Temporarily block signal handlers to prevent recursive updates during setup
        self._updating_fractions = True
        
        try:
            # Set typical cement phase composition (percentages, normalized to 100%)
            default_phases = {
                'c3s': 58.51,    # Alite (55/94 * 100)
                'c2s': 21.28,    # Belite (20/94 * 100)
                'c3a': 8.51,     # Aluminate (8/94 * 100)
                'c4af': 10.64,   # Ferrite (10/94 * 100)
                'k2so4': 0.53,   # Potassium sulfate (0.5/94 * 100)
                'na2so4': 0.53   # Sodium sulfate (0.5/94 * 100)
            }
            
            # Set mass fractions first
            for phase_key, percentage in default_phases.items():
                if phase_key in self.phase_spins:
                    print(f"DEBUG: Setting {phase_key} mass fraction to {percentage}%")
                    self.phase_spins[phase_key].set_value(percentage)
                    print(f"DEBUG: {phase_key} mass fraction after set: {self.phase_spins[phase_key].get_value()}%")
                else:
                    print(f"DEBUG: {phase_key} not found in phase_spins")
            
            # Calculate and set corresponding volume fractions using specific gravities
            specific_gravities = {
                'c3s': 3.15,
                'c2s': 3.28, 
                'c3a': 3.03,
                'c4af': 3.73,
                'k2so4': 2.66,
                'na2so4': 2.68
            }
            
            # Calculate total weighted volume for normalization
            total_weighted_volume = sum(
                (default_phases[phase] / 100.0) / specific_gravities[phase]
                for phase in default_phases
            )
            
            # Set volume fractions (normalized)
            for phase_key, percentage in default_phases.items():
                if phase_key in self.phase_volume_spins:
                    mass_fraction = percentage / 100.0
                    sg = specific_gravities[phase_key]
                    volume_fraction = (mass_fraction / sg) / total_weighted_volume
                    volume_percentage = volume_fraction * 100.0
                    print(f"DEBUG: Setting {phase_key} volume fraction to {volume_percentage:.2f}%")
                    self.phase_volume_spins[phase_key].set_value(volume_percentage)
                    print(f"DEBUG: {phase_key} volume fraction after set: {self.phase_volume_spins[phase_key].get_value():.2f}%")
                else:
                    print(f"DEBUG: {phase_key} not found in phase_volume_spins")
            
            # Set default surface fractions (equal to volume fractions as starting point)  
            for phase_key in default_phases:
                if phase_key in self.phase_surface_spins:
                    volume_percentage = self.phase_volume_spins[phase_key].get_value()
                    self.phase_surface_spins[phase_key].set_value(volume_percentage)
            
            # Set default gypsum values (small amounts)
            print(f"DEBUG: Setting gypsum mass fractions")
            self.dihyd_spin.set_value(2.0)      # 2% dihydrate
            print(f"DEBUG: dihyd mass after set: {self.dihyd_spin.get_value()}%")
            self.hemihyd_spin.set_value(1.0)    # 1% hemihydrate  
            print(f"DEBUG: hemihyd mass after set: {self.hemihyd_spin.get_value()}%")
            self.anhyd_spin.set_value(0.5)      # 0.5% anhydrite
            print(f"DEBUG: anhyd mass after set: {self.anhyd_spin.get_value()}%")
            
            # Calculate corresponding gypsum volume fractions
            cement_bulk_sg = 3.15  # Typical cement specific gravity
            gypsum_sgs = {'dihyd': 2.32, 'hemihyd': 2.74, 'anhyd': 2.61}
            gypsum_masses = {'dihyd': 2.0, 'hemihyd': 1.0, 'anhyd': 0.5}
            
            for gypsum_type, mass_percent in gypsum_masses.items():
                mass_fraction = mass_percent / 100.0
                sg_gypsum = gypsum_sgs[gypsum_type]
                volume_fraction = (mass_fraction / sg_gypsum) * cement_bulk_sg
                volume_percent = volume_fraction * 100.0
                
                if gypsum_type == 'dihyd':
                    self.dihyd_volume_spin.set_value(volume_percent)
                elif gypsum_type == 'hemihyd':
                    self.hemihyd_volume_spin.set_value(volume_percent)
                elif gypsum_type == 'anhyd':
                    self.anhyd_volume_spin.set_value(volume_percent)
        
        finally:
            # Re-enable signal handlers
            self._updating_fractions = False
            print("DEBUG: Default values set, signal handlers re-enabled")
            
            # Force update all displays
            self._validate_phase_composition()
            self._update_calculations()
    
    def _validate_phase_composition(self) -> None:
        """Validate that phase composition adds up correctly."""
        total = sum(spin.get_value() for spin in self.phase_spins.values())
        
        # Update sum display
        self.sum_display.set_text(f"{total:.2f}")
        
        # Color coding for sum display
        if abs(total - 100.0) <= 0.01:
            # Perfect sum - green
            self.sum_display.set_markup(f'<span color="green"><b>{total:.2f}</b></span>')
        elif abs(total - 100.0) <= 0.1:
            # Close to 100 - orange/warning
            self.sum_display.set_markup(f'<span color="orange"><b>{total:.2f}</b></span>')
        else:
            # Too far from 100 - red/error
            self.sum_display.set_markup(f'<span color="red"><b>{total:.2f}</b></span>')
        
        # Validation messages - be more lenient with phase composition
        if total == 0.0:
            # No phase data entered - this is acceptable
            self.validation_errors.pop('phases', None)
            self.validation_warnings.pop('phases', None)
        elif abs(total - 100.0) > 5.0:
            # Only error if very far from 100%
            self.validation_errors['phases'] = f"Phase composition sum ({total:.2f}%) is very different from 100%"
        elif abs(total - 100.0) > 1.0:
            # Warning if moderately off
            self.validation_errors.pop('phases', None)  # Clear any errors
            self.validation_warnings['phases'] = f"Phase composition sums to {total:.2f}% (typically close to 100%)"
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
            
            # Heat of hydration calculation removed per user request
                
        except Exception as e:
            self.logger.warning(f"Error updating calculations: {e}")
            self.density_display.set_text("Error")
    
    def _collect_material_specific_data(self) -> Dict[str, Any]:
        """Collect cement-specific data."""
        data = {
            'blaine_fineness': self.blaine_spin.get_value(),
            # Setting times removed per user request
            # Gypsum mass fractions (convert from percentage to fraction)
            'dihyd': self.dihyd_spin.get_value() / 100.0,
            'hemihyd': self.hemihyd_spin.get_value() / 100.0,
            'anhyd': self.anhyd_spin.get_value() / 100.0,
            # Gypsum volume fractions (convert from percentage to fraction)
            'dihyd_volume_fraction': self.dihyd_volume_spin.get_value() / 100.0,
            'hemihyd_volume_fraction': self.hemihyd_volume_spin.get_value() / 100.0,
            'anhyd_volume_fraction': self.anhyd_volume_spin.get_value() / 100.0
        }
        
        # Add phase composition (convert to model field names)
        phase_mapping = {
            'c3s': 'c3s_mass_fraction',
            'c2s': 'c2s_mass_fraction', 
            'c3a': 'c3a_mass_fraction',
            'c4af': 'c4af_mass_fraction',
            'k2so4': 'k2so4_mass_fraction',
            'na2so4': 'na2so4_mass_fraction'
        }
        volume_mapping = {
            'c3s': 'c3s_volume_fraction',
            'c2s': 'c2s_volume_fraction', 
            'c3a': 'c3a_volume_fraction',
            'c4af': 'c4af_volume_fraction',
            'k2so4': 'k2so4_volume_fraction',
            'na2so4': 'na2so4_volume_fraction'
        }
        surface_mapping = {
            'c3s': 'c3s_surface_fraction',
            'c2s': 'c2s_surface_fraction', 
            'c3a': 'c3a_surface_fraction',
            'c4af': 'c4af_surface_fraction',
            'k2so4': 'k2so4_surface_fraction',
            'na2so4': 'na2so4_surface_fraction'
        }
        
        # Mass fractions
        for phase_key, spin in self.phase_spins.items():
            model_field = phase_mapping.get(phase_key, phase_key)
            # Convert percentage to fraction (0-1 range)
            data[model_field] = spin.get_value() / 100.0
        
        # Volume fractions
        for phase_key, spin in self.phase_volume_spins.items():
            model_field = volume_mapping.get(phase_key, phase_key)
            # Convert percentage to fraction (0-1 range)
            data[model_field] = spin.get_value() / 100.0
        
        # Surface fractions
        for phase_key, spin in self.phase_surface_spins.items():
            model_field = surface_mapping.get(phase_key, phase_key)
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
            # Collect custom PSD points and convert to JSON string
            psd_points = []
            for row in self.psd_store:
                # Use [diameter, mass_fraction] format to match imported data
                psd_points.append([float(row[0]), float(row[1])])
            
            # Normalize mass fractions to sum to 1.0 before saving
            if psd_points:
                total_mass = sum(point[1] for point in psd_points)
                if total_mass > 0:
                    # Normalize each mass fraction
                    for point in psd_points:
                        point[1] = point[1] / total_mass
            
            import json
            data['psd_custom_points'] = json.dumps(psd_points) if psd_points else None
        
        return data
    
    def _on_mass_fraction_changed(self, mass_spin: Gtk.SpinButton, phase_key: str) -> None:
        """Handle mass fraction changes and update volume fraction."""
        if self._updating_fractions:
            return
        
        self._updating_fractions = True
        try:
            # Get the current mass fraction (as percentage)
            mass_percent = mass_spin.get_value()
            mass_fraction = mass_percent / 100.0
            
            # Get specific gravity for this phase
            sg = self.PHASE_SPECIFIC_GRAVITIES.get(phase_key, 1.0)
            
            # Calculate volume fraction from mass fraction
            # volume_fraction = mass_fraction / specific_gravity
            # But we need to normalize considering other phases
            
            # Get all current mass fractions to calculate total weighted volume
            total_weighted_volume = 0.0
            all_mass_fractions = {}
            
            for pk, spin in self.phase_spins.items():
                if pk == phase_key:
                    all_mass_fractions[pk] = mass_fraction
                else:
                    all_mass_fractions[pk] = spin.get_value() / 100.0
                
                if all_mass_fractions[pk] > 0:
                    phase_sg = self.PHASE_SPECIFIC_GRAVITIES.get(pk, 1.0)
                    total_weighted_volume += all_mass_fractions[pk] / phase_sg
            
            # Calculate volume fraction for the current phase
            volume_spin = self.phase_volume_spins.get(phase_key)
            if volume_spin:
                if abs(mass_fraction) < 1e-10:  # Use tolerance for floating-point comparison
                    # If mass fraction is zero, volume fraction must also be zero
                    volume_spin.set_value(0.0)
                elif total_weighted_volume > 0:
                    volume_fraction = (mass_fraction / sg) / total_weighted_volume
                    volume_percent = volume_fraction * 100.0
                    volume_spin.set_value(volume_percent)
            
            # Enforce constraint: if mass fraction is zero, surface fraction must be zero
            surface_spin = self.phase_surface_spins.get(phase_key)
            if surface_spin:
                if abs(mass_fraction) < 1e-10:  # Use tolerance for floating-point comparison
                    # Set surface fraction to zero first
                    surface_spin.set_value(0.0)
                    # Then normalize remaining surface fractions to 100%
                    self._normalize_surface_fractions(exclude_phase=phase_key)
                else:
                    # When mass fraction changes to non-zero, normalize surface fractions
                    self._normalize_surface_fractions(exclude_phase=None)
        
        finally:
            self._updating_fractions = False
    
    def _on_volume_fraction_changed(self, volume_spin: Gtk.SpinButton, phase_key: str) -> None:
        """Handle volume fraction changes and update mass fraction."""
        if self._updating_fractions:
            return
        
        self._updating_fractions = True
        try:
            # Get the current volume fraction (as percentage)
            volume_percent = volume_spin.get_value()
            volume_fraction = volume_percent / 100.0
            
            # Get specific gravity for this phase
            sg = self.PHASE_SPECIFIC_GRAVITIES.get(phase_key, 1.0)
            
            # Get all current volume fractions to calculate total weighted mass
            total_weighted_mass = 0.0
            all_volume_fractions = {}
            
            for pk, spin in self.phase_volume_spins.items():
                if pk == phase_key:
                    all_volume_fractions[pk] = volume_fraction
                else:
                    all_volume_fractions[pk] = spin.get_value() / 100.0
                
                if all_volume_fractions[pk] > 0:
                    phase_sg = self.PHASE_SPECIFIC_GRAVITIES.get(pk, 1.0)
                    total_weighted_mass += all_volume_fractions[pk] * phase_sg
            
            # Calculate mass fraction for the current phase
            mass_spin = self.phase_spins.get(phase_key)
            if mass_spin:
                if abs(volume_fraction) < 1e-10:  # Use tolerance for floating-point comparison
                    # If volume fraction is zero, mass fraction must also be zero
                    mass_spin.set_value(0.0)
                elif total_weighted_mass > 0:
                    mass_fraction = (volume_fraction * sg) / total_weighted_mass
                    mass_percent = mass_fraction * 100.0
                    mass_spin.set_value(mass_percent)
            
            # Normalize surface fractions when volume fraction changes
            surface_spin = self.phase_surface_spins.get(phase_key)
            if surface_spin:
                if abs(volume_fraction) < 1e-10:  # Use tolerance for floating-point comparison
                    # Set surface fraction to zero first
                    surface_spin.set_value(0.0)
                    # Then normalize remaining surface fractions to 100%
                    self._normalize_surface_fractions(exclude_phase=phase_key)
                else:
                    # When volume fraction changes to non-zero, normalize surface fractions
                    self._normalize_surface_fractions(exclude_phase=None)
        
        finally:
            self._updating_fractions = False
    
    def _on_surface_fraction_changed(self, surface_spin: Gtk.SpinButton, phase_key: str) -> None:
        """Handle surface fraction changes and normalize to 100%."""
        if self._updating_fractions:
            return
        
        self._updating_fractions = True
        try:
            # Get current surface fraction
            current_surface_percent = surface_spin.get_value()
            
            # Check constraint: if mass fraction is zero, surface fraction must be zero
            mass_spin = self.phase_spins.get(phase_key)
            if mass_spin and mass_spin.get_value() == 0:
                surface_spin.set_value(0.0)
                current_surface_percent = 0.0
            
            # Normalize all surface fractions to 100%
            self._normalize_surface_fractions(exclude_phase=phase_key)
        
        finally:
            self._updating_fractions = False
    
    def _normalize_surface_fractions(self, exclude_phase: Optional[str] = None) -> None:
        """Normalize surface fractions to sum to 100%."""
        # Get all current surface fractions
        surface_values = {}
        total_surface = 0.0
        
        for phase_key, spin in self.phase_surface_spins.items():
            value = spin.get_value()
            surface_values[phase_key] = value
            total_surface += value
        
        # Only normalize if we have non-zero values and they don't already sum to 100%
        if total_surface > 0 and abs(total_surface - 100.0) > 0.01:  # Small tolerance for floating point
            # Calculate normalization factor
            normalization_factor = 100.0 / total_surface
            
            # Temporarily block signals to prevent cascade updates
            was_updating = self._updating_fractions
            self._updating_fractions = True
            
            try:
                # Apply normalization to all phases
                for phase_key, spin in self.phase_surface_spins.items():
                    if phase_key != exclude_phase:  # Don't normalize the phase that was just changed
                        old_value = surface_values[phase_key]
                        normalized_value = old_value * normalization_factor
                        spin.set_value(normalized_value)
            finally:
                # Restore the original updating state
                self._updating_fractions = was_updating
    
    def _on_gypsum_mass_changed(self, mass_spin: Gtk.SpinButton, gypsum_type: str) -> None:
        """Handle gypsum mass fraction changes and update volume fraction."""
        if self._updating_fractions:
            return
        
        self._updating_fractions = True
        try:
            # Get the current mass fraction (as percentage)
            mass_percent = mass_spin.get_value()
            mass_fraction = mass_percent / 100.0
            
            # Get specific gravity for this gypsum component
            sg_gypsum = self.GYPSUM_SPECIFIC_GRAVITIES.get(gypsum_type, 1.0)
            
            # Get cement bulk specific gravity
            cement_bulk_sg = self.specific_gravity_spin.get_value()
            
            # Calculate volume fraction using the correct formula:
            # volume_fraction = (mass_fraction / component_SG) * cement_bulk_SG
            volume_fraction = (mass_fraction / sg_gypsum) * cement_bulk_sg
            volume_percent = volume_fraction * 100.0
            
            # Update the corresponding volume spin button
            if gypsum_type == 'dihyd':
                self.dihyd_volume_spin.set_value(volume_percent)
            elif gypsum_type == 'hemihyd':
                self.hemihyd_volume_spin.set_value(volume_percent)
            elif gypsum_type == 'anhyd':
                self.anhyd_volume_spin.set_value(volume_percent)
        
        finally:
            self._updating_fractions = False
    
    def _on_gypsum_volume_changed(self, volume_spin: Gtk.SpinButton, gypsum_type: str) -> None:
        """Handle gypsum volume fraction changes and update mass fraction."""
        if self._updating_fractions:
            return
        
        self._updating_fractions = True
        try:
            # Get the current volume fraction (as percentage)
            volume_percent = volume_spin.get_value()
            volume_fraction = volume_percent / 100.0
            
            # Get specific gravity for this gypsum component
            sg_gypsum = self.GYPSUM_SPECIFIC_GRAVITIES.get(gypsum_type, 1.0)
            
            # Get cement bulk specific gravity
            cement_bulk_sg = self.specific_gravity_spin.get_value()
            
            # Calculate mass fraction using the inverse formula:
            # mass_fraction = (volume_fraction / cement_bulk_SG) * component_SG
            mass_fraction = (volume_fraction / cement_bulk_sg) * sg_gypsum
            mass_percent = mass_fraction * 100.0
            
            # Update the corresponding mass spin button
            if gypsum_type == 'dihyd':
                self.dihyd_spin.set_value(mass_percent)
            elif gypsum_type == 'hemihyd':
                self.hemihyd_spin.set_value(mass_percent)
            elif gypsum_type == 'anhyd':
                self.anhyd_spin.set_value(mass_percent)
        
        finally:
            self._updating_fractions = False


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
        self.psd_container = None
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
        
        # Particle size distribution section
        self._add_psd_section(container)
        
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
            # For new materials, just update the summary to show log-normal mode
            self._update_psd_summary_label()
            return
        
        # Load basic fields
        self.loi_spin.set_value(float(self.material_data.get('loi', 3.0)))
        self.fineness_spin.set_value(float(self.material_data.get('fineness_45um', 20.0)))
        
        # Load oxide composition - map database field names to UI keys
        oxide_field_mapping = {
            'sio2': 'sio2_content',
            'cao': 'cao_content', 
            'al2o3': 'al2o3_content',
            'mgo': 'mgo_content',
            'fe2o3': 'fe2o3_content',
            'so3': 'so3_content'
        }
        for oxide_key, spin in self.oxide_spins.items():
            database_field = oxide_field_mapping.get(oxide_key, oxide_key)
            value = self.material_data.get(database_field, 0.0)
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
        
        # Load custom PSD data if available
        psd_custom_points = self.material_data.get('psd_custom_points')
        if psd_custom_points:
            try:
                import json
                psd_data = json.loads(psd_custom_points)
                # Convert from dict format back to tuple format
                self.imported_psd_data = [(point['diameter'], point['mass_fraction']) for point in psd_data]
                # Create and show the editable table
                self._create_psd_data_table()
                # Update summary to show loaded data
                self._update_psd_summary_label()
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                self.logger.warning(f"Could not load custom PSD data: {e}")
                # Clear invalid data
                self.material_data['psd_custom_points'] = None
                # Update summary to show log-normal mode
                self._update_psd_summary_label()
        else:
            # No existing PSD data, update summary to show log-normal mode
            self._update_psd_summary_label()
        
        # Load PSD parameters
        if hasattr(self, 'psd_median_spin'):
            self.psd_median_spin.set_value(float(self.material_data.get('psd_median', 5.0)))
        if hasattr(self, 'psd_stdev_spin'):
            self.psd_stdev_spin.set_value(float(self.material_data.get('psd_stdev', 0.5)))
        
        # Update calculations and summary
        self._update_alkali_calculations()
        self._update_psd_summary_label()
    
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
        data = {}
        
        # NOTE: The following fields don't exist in the current FlyAsh model:
        # loi, fineness_45um, na2o, k2o, astm_class, activity_index, pozzolanic_activity
        # These would need to be added to the model if we want to save them
        
        # Add oxide composition - map UI keys to database field names
        oxide_field_mapping = {
            'sio2': 'sio2_content',
            'cao': 'cao_content', 
            'al2o3': 'al2o3_content',
            'mgo': 'mgo_content',
            'fe2o3': 'fe2o3_content',
            'so3': 'so3_content'
        }
        for oxide_key, spin in self.oxide_spins.items():
            database_field = oxide_field_mapping.get(oxide_key, oxide_key)
            data[database_field] = spin.get_value()
        
        # Add PSD parameters if they exist (these do exist in the model)
        if hasattr(self, 'psd_median_spin') and self.psd_median_spin:
            data['psd_median'] = self.psd_median_spin.get_value()
        if hasattr(self, 'psd_spread_spin') and self.psd_spread_spin:
            data['psd_spread'] = self.psd_spread_spin.get_value()
        
        # Include imported PSD data if available (store as JSON)
        if hasattr(self, 'imported_psd_data') and self.imported_psd_data:
            import json
            # Convert list of tuples to list of dicts for JSON storage
            psd_points = [{"diameter": d, "mass_fraction": mf} for d, mf in self.imported_psd_data]
            data['psd_custom_points'] = json.dumps(psd_points)
        
        return data
    
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
        
        # Add section header for log-normal parameters
        lognormal_header = Gtk.Label()
        lognormal_header.set_markup('<b>Option 1: Log-Normal Distribution Parameters</b>')
        lognormal_header.set_halign(Gtk.Align.START)
        lognormal_header.set_margin_top(5)
        psd_box.pack_start(lognormal_header, False, False, 0)
        
        psd_box.pack_start(psd_grid, False, False, 0)
        
        # Add separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        separator.set_margin_top(15)
        separator.set_margin_bottom(10)
        psd_box.pack_start(separator, False, False, 0)
        
        # CSV Import section with header
        csv_header = Gtk.Label()
        csv_header.set_markup('<b>Option 2: Import Experimental Data</b>')
        csv_header.set_halign(Gtk.Align.START)
        psd_box.pack_start(csv_header, False, False, 0)
        
        csv_desc = Gtk.Label()
        csv_desc.set_markup('<i>Upload a CSV file with experimental particle size measurements</i>')
        csv_desc.set_halign(Gtk.Align.START)
        csv_desc.get_style_context().add_class("dim-label")
        csv_desc.set_margin_bottom(5)
        psd_box.pack_start(csv_desc, False, False, 0)
        
        # CSV Import button
        import_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        import_box.set_halign(Gtk.Align.START)
        
        import_button = Gtk.Button.new_with_label("Import CSV Data")
        import_button.connect('clicked', self._on_import_csv_psd_simple)
        import_button.set_tooltip_text("Import experimental PSD data from CSV file (diameter_um, mass_fraction)")
        import_box.pack_start(import_button, False, False, 0)
        
        psd_box.pack_start(import_box, False, False, 0)
        
        # PSD summary (will be updated dynamically)
        self.psd_summary_label = Gtk.Label()
        self.psd_summary_label.set_halign(Gtk.Align.START)
        self.psd_summary_label.set_margin_top(10)
        psd_box.pack_start(self.psd_summary_label, False, False, 0)
        
        # Store reference to psd_box for table insertion
        self.psd_container = psd_box
        
        psd_frame.add(psd_box)
        container.pack_start(psd_frame, False, False, 0)
    
    def _update_psd_summary_label(self):
        """Update the PSD summary label based on current data state."""
        if hasattr(self, 'imported_psd_data') and self.imported_psd_data:
            # Show CSV import status
            self.psd_summary_label.set_markup(
                f'<i><b>Using Option 2:</b> {len(self.imported_psd_data)} experimental data points imported - Click table cells to edit</i>'
            )
        else:
            # Show log-normal status
            self.psd_summary_label.set_markup(
                '<i><b>Using Option 1:</b> Particle size distribution will be modeled as log-normal</i>'
            )
    
    def _on_import_csv_psd_simple(self, button):
        """Import PSD data from CSV file for simple material types."""
        dialog = Gtk.FileChooserDialog(
            title="Import PSD Data from CSV",
            parent=self,
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
        dialog.add_button(Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        
        # Add CSV file filter
        csv_filter = Gtk.FileFilter()
        csv_filter.set_name("CSV Files")
        csv_filter.add_pattern("*.csv")
        csv_filter.add_mime_type("text/csv")
        dialog.add_filter(csv_filter)
        
        # Add all files filter
        all_filter = Gtk.FileFilter()
        all_filter.set_name("All Files")
        all_filter.add_pattern("*")
        dialog.add_filter(all_filter)
        
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            try:
                self._load_csv_psd_data_simple(filename)
            except Exception as e:
                error_dialog = Gtk.MessageDialog(
                    transient_for=self,
                    flags=0,
                    message_type=Gtk.MessageType.ERROR,
                    buttons=Gtk.ButtonsType.OK,
                    text="Error importing CSV file"
                )
                error_dialog.format_secondary_text(f"Could not import PSD data: {e}")
                error_dialog.run()
                error_dialog.destroy()
        
        dialog.destroy()
    
    def _load_csv_psd_data_simple(self, filename):
        """Load PSD data from CSV file for simple material types."""
        import csv
        
        with open(filename, 'r', encoding='utf-8') as file:
            # Try to detect if file has headers
            first_line = file.readline().strip()
            file.seek(0)
            
            has_header = False
            try:
                # Try to parse first line as numbers
                parts = first_line.replace(',', ' ').split()
                if len(parts) >= 2:
                    float(parts[0])
                    float(parts[1])
            except (ValueError, IndexError):
                has_header = True
            
            # Parse CSV data
            reader = csv.reader(file)
            if has_header:
                next(reader)  # Skip header row
            
            loaded_points = []
            for row_num, row in enumerate(reader, start=1):
                if len(row) < 2:
                    continue  # Skip incomplete rows
                
                try:
                    diameter = float(row[0])
                    mass_fraction = float(row[1])
                    
                    # Validate data ranges
                    if diameter <= 0:
                        self.logger.warning(f"Invalid diameter {diameter} on row {row_num}, skipping")
                        continue
                    
                    if not (0 <= mass_fraction <= 1):
                        # Try to handle percentage format (0-100%) by converting to fraction
                        if 0 <= mass_fraction <= 100:
                            mass_fraction = mass_fraction / 100.0
                        else:
                            self.logger.warning(f"Invalid mass fraction {mass_fraction} on row {row_num}, skipping")
                            continue
                    
                    loaded_points.append((diameter, mass_fraction))
                    
                except (ValueError, IndexError) as e:
                    self.logger.warning(f"Could not parse row {row_num}: {row}, error: {e}")
                    continue
            
            if not loaded_points:
                raise ValueError("No valid PSD data points found in CSV file")
            
            # Sort by diameter (ascending)
            loaded_points.sort(key=lambda x: x[0])
            
            # Store the imported PSD data for later use
            self.imported_psd_data = loaded_points
            
            # Create and show an editable table for the imported data
            self._create_psd_data_table()
            
            # Update summary label to show imported data info
            self._update_psd_summary_label()
            
            # Show success message
            self.parent_window.update_status(f"Imported {len(loaded_points)} PSD data points from CSV", "success", 3)
            
            self.logger.info(f"Successfully imported {len(loaded_points)} PSD points from {filename}")
    
    def _create_psd_data_table(self):
        """Create an editable table to display and edit imported PSD data."""
        if not hasattr(self, 'imported_psd_data') or not self.imported_psd_data:
            return
        
        # If table already exists, remove it first
        if hasattr(self, 'psd_table_box'):
            self.psd_table_box.get_parent().remove(self.psd_table_box)
        
        # Create new table container
        self.psd_table_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        
        # Table label
        table_label = Gtk.Label()
        table_label.set_markup('<b>Imported PSD Data (Editable)</b>')
        table_label.set_halign(Gtk.Align.START)
        self.psd_table_box.pack_start(table_label, False, False, 0)
        
        # Scrolled window for the table
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.set_size_request(-1, 200)
        
        # Create list store for the data
        self.psd_data_store = Gtk.ListStore(float, float)  # diameter, mass_fraction
        
        # Populate with imported data
        for diameter, mass_fraction in self.imported_psd_data:
            self.psd_data_store.append([diameter, mass_fraction])
        
        # Create tree view
        tree_view = Gtk.TreeView(model=self.psd_data_store)
        tree_view.set_reorderable(True)
        
        # Diameter column (editable)
        diameter_renderer = Gtk.CellRendererText()
        diameter_renderer.set_property('editable', True)
        diameter_renderer.connect('edited', self._on_diameter_edited)
        diameter_column = Gtk.TreeViewColumn("Diameter (μm)", diameter_renderer, text=0)
        diameter_column.set_resizable(True)
        tree_view.append_column(diameter_column)
        
        # Mass fraction column (editable)
        fraction_renderer = Gtk.CellRendererText()
        fraction_renderer.set_property('editable', True)
        fraction_renderer.connect('edited', self._on_fraction_edited)
        fraction_column = Gtk.TreeViewColumn("Mass Fraction", fraction_renderer, text=1)
        fraction_column.set_resizable(True)
        tree_view.append_column(fraction_column)
        
        scrolled_window.add(tree_view)
        self.psd_table_box.pack_start(scrolled_window, True, True, 0)
        
        # Buttons for table operations
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        
        add_point_btn = Gtk.Button.new_with_label("Add Point")
        add_point_btn.connect('clicked', self._on_add_psd_data_point)
        button_box.pack_start(add_point_btn, False, False, 0)
        
        remove_point_btn = Gtk.Button.new_with_label("Remove Point")
        remove_point_btn.connect('clicked', self._on_remove_psd_data_point, tree_view)
        button_box.pack_start(remove_point_btn, False, False, 0)
        
        self.psd_table_box.pack_start(button_box, False, False, 0)
        
        # Insert the table box after the summary label
        parent_box = self.psd_summary_label.get_parent()
        children = parent_box.get_children()
        summary_index = children.index(self.psd_summary_label)
        parent_box.pack_start(self.psd_table_box, False, False, 0)
        parent_box.reorder_child(self.psd_table_box, summary_index + 1)
        
        # Show all new widgets
        self.psd_table_box.show_all()
    
    def _on_diameter_edited(self, renderer, path, new_text):
        """Handle editing of diameter values in PSD table."""
        try:
            value = float(new_text)
            if value > 0:
                self.psd_data_store[path][0] = value
                self._update_imported_psd_data()
        except ValueError:
            pass
    
    def _on_fraction_edited(self, renderer, path, new_text):
        """Handle editing of mass fraction values in PSD table."""
        try:
            value = float(new_text)
            if 0 <= value <= 1.0:
                self.psd_data_store[path][1] = value
                self._update_imported_psd_data()
        except ValueError:
            pass
    
    def _on_add_psd_data_point(self, button):
        """Add a new point to the PSD data table."""
        self.psd_data_store.append([1.0, 0.001])  # Default values
        self._update_imported_psd_data()
    
    def _on_remove_psd_data_point(self, button, tree_view):
        """Remove selected point from PSD data table."""
        selection = tree_view.get_selection()
        model, tree_iter = selection.get_selected()
        if tree_iter:
            model.remove(tree_iter)
            self._update_imported_psd_data()
    
    def _update_imported_psd_data(self):
        """Update the imported_psd_data list from the table store."""
        if hasattr(self, 'psd_data_store'):
            self.imported_psd_data = []
            for row in self.psd_data_store:
                self.imported_psd_data.append((float(row[0]), float(row[1])))
            
            # Sort by diameter
            self.imported_psd_data.sort(key=lambda x: x[0])


class SlagDialog(MaterialDialogBase):
    """Dialog for managing slag (GGBS) materials."""
    
    def __init__(self, parent: 'VCCTLMainWindow', material_data: Optional[Dict[str, Any]] = None):
        """Initialize the slag dialog."""
        # Initialize slag-specific UI components BEFORE calling parent constructor
        self.oxide_spins = {}
        self.cao_sio2_display = None
        self.mgo_al2o3_display = None
        self.activity_spin = None
        self.glass_content_spin = None
        self.reaction_params = {}
        self.psd_container = None
        
        super().__init__(parent, 'slag', material_data)
    
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
        
        # Particle size distribution section
        self._add_psd_section(container)
    
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
        
        # Default values that total 100% for new slag materials
        default_values = {
            'sio2': 35.0,
            'cao': 40.0,
            'al2o3': 12.0,
            'mgo': 8.0,
            'fe2o3': 1.0,
            'so3': 4.0
        }
        
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
            # Use specific default values for new materials that total 100%
            default_value = default_values.get(key, 0.0)
            spin.set_value(default_value)
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
        # No advanced sections currently needed for slag materials
        pass
    
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
        
        # For new materials, initialize default calculations now that UI is fully set up
        if not self.material_data:
            self._update_ratio_calculations()
            if hasattr(self, '_update_psd_summary_label'):
                self._update_psd_summary_label()
    
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
            # For new materials, skip initialization - UI may not be fully built yet
            return
        
        # Load basic fields
        self.glass_content_spin.set_value(float(self.material_data.get('glass_content', 95.0)))
        self.activity_spin.set_value(float(self.material_data.get('activity_index', 95.0)))
        
        # Load oxide composition - map database field names to UI keys
        oxide_field_mapping = {
            'sio2': 'sio2_content',
            'cao': 'cao_content', 
            'al2o3': 'al2o3_content',
            'mgo': 'mgo_content',
            'fe2o3': 'fe2o3_content',
            'so3': 'so3_content'
        }
        for oxide_key, spin in self.oxide_spins.items():
            database_field = oxide_field_mapping.get(oxide_key, oxide_key)
            value = self.material_data.get(database_field, 0.0)
            spin.set_value(float(value))
        
        # Load reaction parameters from flat fields
        for param_key, spin in self.reaction_params.items():
            value = self.material_data.get(param_key, spin.get_value())
            spin.set_value(float(value))
        
        
        # Load PSD parameters
        if hasattr(self, 'psd_median_spin'):
            self.psd_median_spin.set_value(float(self.material_data.get('psd_median', 5.0)))
        if hasattr(self, 'psd_spread_spin'):
            self.psd_spread_spin.set_value(float(self.material_data.get('psd_spread', 2.0)))
        
        # Load custom PSD data if available
        psd_custom_points = self.material_data.get('psd_custom_points')
        if psd_custom_points:
            try:
                import json
                psd_data = json.loads(psd_custom_points)
                # Convert from dict format back to tuple format
                self.imported_psd_data = [(point['diameter'], point['mass_fraction']) for point in psd_data]
                # Create and show the editable table
                self._create_psd_data_table()
                # Update summary to show loaded data
                self._update_psd_summary_label()
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                self.logger.warning(f"Could not load custom PSD data: {e}")
                # Clear invalid data
                self.material_data['psd_custom_points'] = None
                # Update summary to show log-normal mode
                self._update_psd_summary_label()
        else:
            # No existing PSD data, update summary to show log-normal mode
            self._update_psd_summary_label()
        
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
            'activity_index': self.activity_spin.get_value()
        }
        
        # Add oxide composition - map UI keys to database field names
        oxide_field_mapping = {
            'sio2': 'sio2_content',
            'cao': 'cao_content', 
            'al2o3': 'al2o3_content',
            'mgo': 'mgo_content',
            'fe2o3': 'fe2o3_content',
            'so3': 'so3_content'
        }
        for oxide_key, spin in self.oxide_spins.items():
            database_field = oxide_field_mapping.get(oxide_key, oxide_key)
            data[database_field] = spin.get_value()
        
        # Add reaction parameters as flat fields
        for param_key, spin in self.reaction_params.items():
            data[param_key] = spin.get_value()
        
        # Add PSD parameters if they exist
        if hasattr(self, 'psd_median_spin') and self.psd_median_spin:
            data['psd_median'] = self.psd_median_spin.get_value()
        if hasattr(self, 'psd_spread_spin') and self.psd_spread_spin:
            data['psd_spread'] = self.psd_spread_spin.get_value()
        
        # Include imported PSD data if available (store as JSON)
        if hasattr(self, 'imported_psd_data') and self.imported_psd_data:
            import json
            # Convert list of tuples to list of dicts for JSON storage
            psd_points = [{"diameter": d, "mass_fraction": mf} for d, mf in self.imported_psd_data]
            data['psd_custom_points'] = json.dumps(psd_points)
        
        return data
    
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
        
        # Add section header for log-normal parameters
        lognormal_header = Gtk.Label()
        lognormal_header.set_markup('<b>Option 1: Log-Normal Distribution Parameters</b>')
        lognormal_header.set_halign(Gtk.Align.START)
        lognormal_header.set_margin_top(5)
        psd_box.pack_start(lognormal_header, False, False, 0)
        
        psd_box.pack_start(psd_grid, False, False, 0)
        
        # Add separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        separator.set_margin_top(15)
        separator.set_margin_bottom(10)
        psd_box.pack_start(separator, False, False, 0)
        
        # CSV Import section with header
        csv_header = Gtk.Label()
        csv_header.set_markup('<b>Option 2: Import Experimental Data</b>')
        csv_header.set_halign(Gtk.Align.START)
        psd_box.pack_start(csv_header, False, False, 0)
        
        csv_desc = Gtk.Label()
        csv_desc.set_markup('<i>Upload a CSV file with experimental particle size measurements</i>')
        csv_desc.set_halign(Gtk.Align.START)
        csv_desc.get_style_context().add_class("dim-label")
        csv_desc.set_margin_bottom(5)
        psd_box.pack_start(csv_desc, False, False, 0)
        
        # CSV Import button
        import_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        import_box.set_halign(Gtk.Align.START)
        
        import_button = Gtk.Button.new_with_label("Import CSV Data")
        import_button.connect('clicked', self._on_import_csv_psd_simple)
        import_button.set_tooltip_text("Import experimental PSD data from CSV file (diameter_um, mass_fraction)")
        import_box.pack_start(import_button, False, False, 0)
        
        psd_box.pack_start(import_box, False, False, 0)
        
        # PSD summary (will be updated dynamically)
        self.psd_summary_label = Gtk.Label()
        self.psd_summary_label.set_halign(Gtk.Align.START)
        self.psd_summary_label.set_margin_top(10)
        psd_box.pack_start(self.psd_summary_label, False, False, 0)
        
        # Store reference to psd_box for table insertion
        self.psd_container = psd_box
        
        psd_frame.add(psd_box)
        container.pack_start(psd_frame, False, False, 0)
    
    def _update_psd_summary_label(self):
        """Update the PSD summary label based on current data state."""
        if hasattr(self, 'imported_psd_data') and self.imported_psd_data:
            # Show CSV import status
            self.psd_summary_label.set_markup(
                f'<i><b>Using Option 2:</b> {len(self.imported_psd_data)} experimental data points imported - Click table cells to edit</i>'
            )
        else:
            # Show log-normal status
            self.psd_summary_label.set_markup(
                '<i><b>Using Option 1:</b> Particle size distribution will be modeled as log-normal</i>'
            )
    
    def _on_import_csv_psd_simple(self, button):
        """Import PSD data from CSV file for simple material types."""
        dialog = Gtk.FileChooserDialog(
            title="Import PSD Data from CSV",
            parent=self,
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
        dialog.add_button(Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        
        # Add CSV file filter
        csv_filter = Gtk.FileFilter()
        csv_filter.set_name("CSV Files")
        csv_filter.add_pattern("*.csv")
        csv_filter.add_mime_type("text/csv")
        dialog.add_filter(csv_filter)
        
        # Add all files filter
        all_filter = Gtk.FileFilter()
        all_filter.set_name("All Files")
        all_filter.add_pattern("*")
        dialog.add_filter(all_filter)
        
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            try:
                self._load_csv_psd_data_simple(filename)
            except Exception as e:
                error_dialog = Gtk.MessageDialog(
                    transient_for=self,
                    flags=0,
                    message_type=Gtk.MessageType.ERROR,
                    buttons=Gtk.ButtonsType.OK,
                    text="Error importing CSV file"
                )
                error_dialog.format_secondary_text(f"Could not import PSD data: {e}")
                error_dialog.run()
                error_dialog.destroy()
        
        dialog.destroy()
    
    def _load_csv_psd_data_simple(self, filename):
        """Load PSD data from CSV file for simple material types."""
        import csv
        
        with open(filename, 'r', encoding='utf-8') as file:
            # Try to detect if file has headers
            first_line = file.readline().strip()
            file.seek(0)
            
            has_header = False
            try:
                # Try to parse first line as numbers
                parts = first_line.replace(',', ' ').split()
                if len(parts) >= 2:
                    float(parts[0])
                    float(parts[1])
            except (ValueError, IndexError):
                has_header = True
            
            # Parse CSV data
            reader = csv.reader(file)
            if has_header:
                next(reader)  # Skip header row
            
            loaded_points = []
            for row_num, row in enumerate(reader, start=1):
                if len(row) < 2:
                    continue  # Skip incomplete rows
                
                try:
                    diameter = float(row[0])
                    mass_fraction = float(row[1])
                    
                    # Validate data ranges
                    if diameter <= 0:
                        self.logger.warning(f"Invalid diameter {diameter} on row {row_num}, skipping")
                        continue
                    
                    if not (0 <= mass_fraction <= 1):
                        # Try to handle percentage format (0-100%) by converting to fraction
                        if 0 <= mass_fraction <= 100:
                            mass_fraction = mass_fraction / 100.0
                        else:
                            self.logger.warning(f"Invalid mass fraction {mass_fraction} on row {row_num}, skipping")
                            continue
                    
                    loaded_points.append((diameter, mass_fraction))
                    
                except (ValueError, IndexError) as e:
                    self.logger.warning(f"Could not parse row {row_num}: {row}, error: {e}")
                    continue
            
            if not loaded_points:
                raise ValueError("No valid PSD data points found in CSV file")
            
            # Sort by diameter (ascending)
            loaded_points.sort(key=lambda x: x[0])
            
            # Store the imported PSD data for later use
            self.imported_psd_data = loaded_points
            
            # Create and show an editable table for the imported data
            self._create_psd_data_table()
            
            # Update summary label to show imported data info
            self._update_psd_summary_label()
            
            # Show success message
            self.parent_window.update_status(f"Imported {len(loaded_points)} PSD data points from CSV", "success", 3)
            
            self.logger.info(f"Successfully imported {len(loaded_points)} PSD points from {filename}")
    
    def _create_psd_data_table(self):
        """Create an editable table to display and edit imported PSD data."""
        if not hasattr(self, 'imported_psd_data') or not self.imported_psd_data:
            return
        
        # If table already exists, remove it first
        if hasattr(self, 'psd_table_box'):
            self.psd_table_box.get_parent().remove(self.psd_table_box)
        
        # Create new table container
        self.psd_table_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        
        # Table header
        table_header = Gtk.Label()
        table_header.set_markup('<b>Imported PSD Data Points</b>')
        table_header.set_halign(Gtk.Align.START)
        self.psd_table_box.pack_start(table_header, False, False, 0)
        
        # Create data store
        self.psd_data_store = Gtk.ListStore(float, float)
        for diameter, mass_fraction in self.imported_psd_data:
            self.psd_data_store.append([diameter, mass_fraction])
        
        # Create tree view
        tree_view = Gtk.TreeView(model=self.psd_data_store)
        tree_view.set_size_request(-1, 200)
        
        # Diameter column (editable)
        diameter_renderer = Gtk.CellRendererText()
        diameter_renderer.set_property("editable", True)
        diameter_renderer.connect("edited", self._on_diameter_edited)
        diameter_column = Gtk.TreeViewColumn("Diameter (μm)", diameter_renderer, text=0)
        diameter_column.set_min_width(120)
        tree_view.append_column(diameter_column)
        
        # Mass fraction column (editable)
        fraction_renderer = Gtk.CellRendererText()
        fraction_renderer.set_property("editable", True)
        fraction_renderer.connect("edited", self._on_mass_fraction_edited)
        fraction_column = Gtk.TreeViewColumn("Mass Fraction", fraction_renderer, text=1)
        fraction_column.set_min_width(120)
        tree_view.append_column(fraction_column)
        
        # Scrolled window for table
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.add(tree_view)
        self.psd_table_box.pack_start(scrolled, True, True, 0)
        
        # Button box for add/remove
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        
        add_button = Gtk.Button.new_with_label("Add Point")
        add_button.connect('clicked', self._on_add_psd_point, tree_view)
        button_box.pack_start(add_button, False, False, 0)
        
        remove_button = Gtk.Button.new_with_label("Remove Selected")
        remove_button.connect('clicked', self._on_remove_psd_point, tree_view)
        button_box.pack_start(remove_button, False, False, 0)
        
        self.psd_table_box.pack_start(button_box, False, False, 0)
        
        # Add the table directly to the PSD container if available
        if hasattr(self, 'psd_container') and self.psd_container:
            self.psd_container.pack_start(self.psd_table_box, False, False, 5)
            self.psd_table_box.show_all()
            return
        
        # Fallback: Find the parent container and add the table
        for child in self.get_children():
            if isinstance(child, Gtk.Notebook):
                for i in range(child.get_n_pages()):
                    page = child.get_nth_page(i)
                    if isinstance(page, Gtk.ScrolledWindow):
                        viewport = page.get_child()
                        if isinstance(viewport, Gtk.Viewport):
                            container = viewport.get_child()
                            if isinstance(container, Gtk.Box):
                                container.pack_start(self.psd_table_box, False, False, 5)
                                self.psd_table_box.show_all()
                                return
    
    def _on_diameter_edited(self, renderer, path, new_text):
        """Handle diameter cell editing."""
        try:
            new_diameter = float(new_text)
            if new_diameter > 0:
                self.psd_data_store[path][0] = new_diameter
                self._update_imported_psd_data()
            else:
                self.logger.warning("Diameter must be positive")
        except ValueError:
            self.logger.warning(f"Invalid diameter value: {new_text}")
    
    def _on_mass_fraction_edited(self, renderer, path, new_text):
        """Handle mass fraction cell editing."""
        try:
            new_fraction = float(new_text)
            if 0 <= new_fraction <= 1:
                self.psd_data_store[path][1] = new_fraction
                self._update_imported_psd_data()
            else:
                self.logger.warning("Mass fraction must be between 0 and 1")
        except ValueError:
            self.logger.warning(f"Invalid mass fraction value: {new_text}")
    
    def _on_add_psd_point(self, button, tree_view):
        """Add new point to PSD data table."""
        self.psd_data_store.append([1.0, 0.0])
        self._update_imported_psd_data()
    
    def _on_remove_psd_point(self, button, tree_view):
        """Remove selected point from PSD data table."""
        selection = tree_view.get_selection()
        model, tree_iter = selection.get_selected()
        if tree_iter:
            model.remove(tree_iter)
            self._update_imported_psd_data()
    
    def _update_imported_psd_data(self):
        """Update the imported_psd_data list from the table store."""
        if hasattr(self, 'psd_data_store'):
            self.imported_psd_data = []
            for row in self.psd_data_store:
                self.imported_psd_data.append((float(row[0]), float(row[1])))
            
            # Sort by diameter
            self.imported_psd_data.sort(key=lambda x: x[0])


class InertFillerDialog(MaterialDialogBase):
    """Dialog for managing inert filler materials."""
    
    def __init__(self, parent: 'VCCTLMainWindow', material_data: Optional[Dict[str, Any]] = None):
        """Initialize the inert filler dialog."""
        self.psd_container = None
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
        
        # Connect signals after all widgets are created
        self._connect_material_signals()
    
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
        
        # Add section header for log-normal parameters
        lognormal_header = Gtk.Label()
        lognormal_header.set_markup('<b>Option 1: Log-Normal Distribution Parameters</b>')
        lognormal_header.set_halign(Gtk.Align.START)
        lognormal_header.set_margin_top(5)
        psd_box.pack_start(lognormal_header, False, False, 0)
        
        psd_box.pack_start(psd_grid, False, False, 0)
        
        # Add separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        separator.set_margin_top(15)
        separator.set_margin_bottom(10)
        psd_box.pack_start(separator, False, False, 0)
        
        # CSV Import section with header
        csv_header = Gtk.Label()
        csv_header.set_markup('<b>Option 2: Import Experimental Data</b>')
        csv_header.set_halign(Gtk.Align.START)
        psd_box.pack_start(csv_header, False, False, 0)
        
        csv_desc = Gtk.Label()
        csv_desc.set_markup('<i>Upload a CSV file with experimental particle size measurements</i>')
        csv_desc.set_halign(Gtk.Align.START)
        csv_desc.get_style_context().add_class("dim-label")
        csv_desc.set_margin_bottom(5)
        psd_box.pack_start(csv_desc, False, False, 0)
        
        # CSV Import button
        import_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        import_box.set_halign(Gtk.Align.START)
        
        import_button = Gtk.Button.new_with_label("Import CSV Data")
        import_button.connect('clicked', self._on_import_csv_psd_simple)
        import_button.set_tooltip_text("Import experimental PSD data from CSV file (diameter_um, mass_fraction)")
        import_box.pack_start(import_button, False, False, 0)
        
        psd_box.pack_start(import_box, False, False, 0)
        
        # PSD summary (will be updated dynamically)
        self.psd_summary_label = Gtk.Label()
        self.psd_summary_label.set_halign(Gtk.Align.START)
        self.psd_summary_label.set_margin_top(10)
        psd_box.pack_start(self.psd_summary_label, False, False, 0)
        
        # Store reference to psd_box for table insertion
        self.psd_container = psd_box
        
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
        # Avoid duplicate signal connections
        if hasattr(self, '_signals_connected') and self._signals_connected:
            return
        
        # Connect spin buttons only if they exist
        if hasattr(self, 'specific_surface_spin') and self.specific_surface_spin:
            self.specific_surface_spin.connect('value-changed', self._on_field_changed)
        if hasattr(self, 'psd_median_spin') and self.psd_median_spin:
            self.psd_median_spin.connect('value-changed', self._on_field_changed)
        if hasattr(self, 'psd_spread_spin') and self.psd_spread_spin:
            self.psd_spread_spin.connect('value-changed', self._on_field_changed)
        if hasattr(self, 'absorption_spin') and self.absorption_spin:
            self.absorption_spin.connect('value-changed', self._on_field_changed)
        
        # Connect combo boxes only if they exist
        if hasattr(self, 'filler_type_combo') and self.filler_type_combo:
            self.filler_type_combo.connect('changed', self._on_field_changed)
        if hasattr(self, 'color_combo') and self.color_combo:
            self.color_combo.connect('changed', self._on_field_changed)
        
        # Mark signals as connected
        self._signals_connected = True
    
    def _load_material_specific_data(self) -> None:
        """Load inert filler-specific data."""
        if not self.material_data:
            # For new materials, just update the summary to show log-normal mode
            self._update_psd_summary_label()
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
        
        # Load custom PSD data if available
        psd_custom_points = self.material_data.get('psd_custom_points')
        if psd_custom_points:
            try:
                import json
                psd_data = json.loads(psd_custom_points)
                # Convert from dict format back to tuple format
                self.imported_psd_data = [(point['diameter'], point['mass_fraction']) for point in psd_data]
                # Create and show the editable table
                self._create_psd_data_table()
                # Update summary to show loaded data
                self._update_psd_summary_label()
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                self.logger.warning(f"Could not load custom PSD data: {e}")
                # Clear invalid data
                self.material_data['psd_custom_points'] = None
                # Update summary to show log-normal mode
                self._update_psd_summary_label()
        else:
            # No existing PSD data, update summary to show log-normal mode
            self._update_psd_summary_label()
    
    def _validate_material_specific_field(self, widget) -> None:
        """Validate inert filler-specific fields."""
        self._validate_inert_filler_properties()
    
    def _validate_all_material_fields(self) -> None:
        """Validate all inert filler-specific fields."""
        self._validate_inert_filler_properties()
    
    def _validate_inert_filler_properties(self) -> None:
        """Validate inert filler properties."""
        try:
            # Check PSD parameters only if widgets exist
            if hasattr(self, 'psd_median_spin') and self.psd_median_spin:
                median = self.psd_median_spin.get_value()
                if median < 0.5:
                    self.validation_warnings['psd_median'] = f"Very fine median size ({median:.1f} μm) may affect workability"
                else:
                    self.validation_warnings.pop('psd_median', None)
            
            if hasattr(self, 'psd_spread_spin') and self.psd_spread_spin:
                spread = self.psd_spread_spin.get_value()
                if spread > 3.0:
                    self.validation_warnings['psd_spread'] = f"Wide size distribution (spread={spread:.1f}) may affect packing"
                else:
                    self.validation_warnings.pop('psd_spread', None)
            
            # Check specific surface only if widget exists
            if hasattr(self, 'specific_surface_spin') and self.specific_surface_spin:
                surface = self.specific_surface_spin.get_value()
                if surface > 20.0:
                    self.validation_warnings['specific_surface'] = f"Very high specific surface ({surface:.1f} m²/g) may increase water demand"
                else:
                    self.validation_warnings.pop('specific_surface', None)
                
        except Exception as e:
            self.logger.warning(f"Error validating inert filler properties: {e}")
    
    def _on_import_csv_psd_simple(self, button):
        """Import PSD data from CSV file for simple material types."""
        dialog = Gtk.FileChooserDialog(
            title="Import PSD Data from CSV",
            parent=self,
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
        dialog.add_button(Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        
        # Add CSV file filter
        csv_filter = Gtk.FileFilter()
        csv_filter.set_name("CSV Files")
        csv_filter.add_pattern("*.csv")
        csv_filter.add_mime_type("text/csv")
        dialog.add_filter(csv_filter)
        
        # Add all files filter
        all_filter = Gtk.FileFilter()
        all_filter.set_name("All Files")
        all_filter.add_pattern("*")
        dialog.add_filter(all_filter)
        
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            try:
                self._load_csv_psd_data_simple(filename)
            except Exception as e:
                error_dialog = Gtk.MessageDialog(
                    transient_for=self,
                    flags=0,
                    message_type=Gtk.MessageType.ERROR,
                    buttons=Gtk.ButtonsType.OK,
                    text="Error importing CSV file"
                )
                error_dialog.format_secondary_text(f"Could not import PSD data: {e}")
                error_dialog.run()
                error_dialog.destroy()
        
        dialog.destroy()
    
    def _load_csv_psd_data_simple(self, filename):
        """Load PSD data from CSV file for simple material types."""
        import csv
        
        with open(filename, 'r', encoding='utf-8') as file:
            # Try to detect if file has headers
            first_line = file.readline().strip()
            file.seek(0)
            
            has_header = False
            try:
                # Try to parse first line as numbers
                parts = first_line.replace(',', ' ').split()
                if len(parts) >= 2:
                    float(parts[0])
                    float(parts[1])
            except (ValueError, IndexError):
                has_header = True
            
            # Parse CSV data
            reader = csv.reader(file)
            if has_header:
                next(reader)  # Skip header row
            
            loaded_points = []
            for row_num, row in enumerate(reader, start=1):
                if len(row) < 2:
                    continue  # Skip incomplete rows
                
                try:
                    diameter = float(row[0])
                    mass_fraction = float(row[1])
                    
                    # Validate data ranges
                    if diameter <= 0:
                        self.logger.warning(f"Invalid diameter {diameter} on row {row_num}, skipping")
                        continue
                    
                    if not (0 <= mass_fraction <= 1):
                        # Try to handle percentage format (0-100%) by converting to fraction
                        if 0 <= mass_fraction <= 100:
                            mass_fraction = mass_fraction / 100.0
                        else:
                            self.logger.warning(f"Invalid mass fraction {mass_fraction} on row {row_num}, skipping")
                            continue
                    
                    loaded_points.append((diameter, mass_fraction))
                    
                except (ValueError, IndexError) as e:
                    self.logger.warning(f"Could not parse row {row_num}: {row}, error: {e}")
                    continue
            
            if not loaded_points:
                raise ValueError("No valid PSD data points found in CSV file")
            
            # Sort by diameter (ascending)
            loaded_points.sort(key=lambda x: x[0])
            
            # Store the imported PSD data for later use
            self.imported_psd_data = loaded_points
            
            # Create and show an editable table for the imported data
            self._create_psd_data_table()
            
            # Update summary label to show imported data info
            self._update_psd_summary_label()
            
            # Show success message
            self.parent_window.update_status(f"Imported {len(loaded_points)} PSD data points from CSV", "success", 3)
            
            self.logger.info(f"Successfully imported {len(loaded_points)} PSD points from {filename}")
    
    def _update_psd_summary_label(self):
        """Update the PSD summary label based on current data state."""
        if hasattr(self, 'imported_psd_data') and self.imported_psd_data:
            # Show CSV import status
            self.psd_summary_label.set_markup(
                f'<i><b>Using Option 2:</b> {len(self.imported_psd_data)} experimental data points imported - Click table cells to edit</i>'
            )
        else:
            # Show log-normal status
            self.psd_summary_label.set_markup(
                '<i><b>Using Option 1:</b> Particle size distribution will be modeled as log-normal</i>'
            )
    
    def _create_psd_data_table(self):
        """Create an editable table to display and edit imported PSD data."""
        if not hasattr(self, 'imported_psd_data') or not self.imported_psd_data:
            return
        
        # If table already exists, remove it first
        if hasattr(self, 'psd_table_box'):
            self.psd_table_box.get_parent().remove(self.psd_table_box)
        
        # Create new table container
        self.psd_table_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        
        # Table label
        table_label = Gtk.Label()
        table_label.set_markup('<b>Imported PSD Data (Editable)</b>')
        table_label.set_halign(Gtk.Align.START)
        self.psd_table_box.pack_start(table_label, False, False, 0)
        
        # Scrolled window for the table
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.set_size_request(-1, 200)
        
        # Create list store for the data
        self.psd_data_store = Gtk.ListStore(float, float)  # diameter, mass_fraction
        
        # Populate with imported data
        for diameter, mass_fraction in self.imported_psd_data:
            self.psd_data_store.append([diameter, mass_fraction])
        
        # Create tree view
        tree_view = Gtk.TreeView(model=self.psd_data_store)
        tree_view.set_reorderable(True)
        
        # Diameter column (editable)
        diameter_renderer = Gtk.CellRendererText()
        diameter_renderer.set_property('editable', True)
        diameter_renderer.connect('edited', self._on_diameter_edited)
        diameter_column = Gtk.TreeViewColumn("Diameter (μm)", diameter_renderer, text=0)
        diameter_column.set_resizable(True)
        tree_view.append_column(diameter_column)
        
        # Mass fraction column (editable)
        fraction_renderer = Gtk.CellRendererText()
        fraction_renderer.set_property('editable', True)
        fraction_renderer.connect('edited', self._on_fraction_edited)
        fraction_column = Gtk.TreeViewColumn("Mass Fraction", fraction_renderer, text=1)
        fraction_column.set_resizable(True)
        tree_view.append_column(fraction_column)
        
        scrolled_window.add(tree_view)
        self.psd_table_box.pack_start(scrolled_window, True, True, 0)
        
        # Buttons for table operations
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        
        add_point_btn = Gtk.Button.new_with_label("Add Point")
        add_point_btn.connect('clicked', self._on_add_psd_data_point)
        button_box.pack_start(add_point_btn, False, False, 0)
        
        remove_point_btn = Gtk.Button.new_with_label("Remove Point")
        remove_point_btn.connect('clicked', self._on_remove_psd_data_point, tree_view)
        button_box.pack_start(remove_point_btn, False, False, 0)
        
        self.psd_table_box.pack_start(button_box, False, False, 0)
        
        # Insert the table box after the summary label
        parent_box = self.psd_summary_label.get_parent()
        children = parent_box.get_children()
        summary_index = children.index(self.psd_summary_label)
        parent_box.pack_start(self.psd_table_box, False, False, 0)
        parent_box.reorder_child(self.psd_table_box, summary_index + 1)
        
        # Show all new widgets
        self.psd_table_box.show_all()
    
    def _on_diameter_edited(self, renderer, path, new_text):
        """Handle editing of diameter values in PSD table."""
        try:
            value = float(new_text)
            if value > 0:
                self.psd_data_store[path][0] = value
                self._update_imported_psd_data()
        except ValueError:
            pass
    
    def _on_fraction_edited(self, renderer, path, new_text):
        """Handle editing of mass fraction values in PSD table."""
        try:
            value = float(new_text)
            if 0 <= value <= 1.0:
                self.psd_data_store[path][1] = value
                self._update_imported_psd_data()
        except ValueError:
            pass
    
    def _on_add_psd_data_point(self, button):
        """Add a new point to the PSD data table."""
        self.psd_data_store.append([1.0, 0.001])  # Default values
        self._update_imported_psd_data()
    
    def _on_remove_psd_data_point(self, button, tree_view):
        """Remove selected point from PSD data table."""
        selection = tree_view.get_selection()
        model, tree_iter = selection.get_selected()
        if tree_iter:
            model.remove(tree_iter)
            self._update_imported_psd_data()
    
    def _update_imported_psd_data(self):
        """Update the imported_psd_data list from the table store."""
        if hasattr(self, 'psd_data_store'):
            self.imported_psd_data = []
            for row in self.psd_data_store:
                self.imported_psd_data.append((float(row[0]), float(row[1])))
            
            # Sort by diameter
            self.imported_psd_data.sort(key=lambda x: x[0])
    
    def _collect_material_specific_data(self) -> Dict[str, Any]:
        """Collect inert filler-specific data."""
        data = {}
        
        # NOTE: The InertFiller model only has these fields:
        # name, specific_gravity, psd, psd_custom_points, description, source, notes
        # UI fields like filler_type, specific_surface, water_absorption, psd_median, 
        # psd_spread, color, reactivity don't exist in the model and would need to be added
        
        # Include imported PSD data if available (store as JSON)
        if hasattr(self, 'imported_psd_data') and self.imported_psd_data:
            import json
            # Convert list of tuples to list of dicts for JSON storage
            psd_points = [{"diameter": d, "mass_fraction": mf} for d, mf in self.imported_psd_data]
            data['psd_custom_points'] = json.dumps(psd_points)
        
        return data


class SilicaFumeDialog(MaterialDialogBase):
    """Dialog for managing silica fume materials."""
    
    def __init__(self, parent: 'VCCTLMainWindow', material_data: Optional[Dict[str, Any]] = None):
        """Initialize the silica fume dialog."""
        self.psd_container = None
        super().__init__(parent, 'silica_fume', material_data)
        
        # Silica fume-specific UI components (minimal since it's single phase)
        self.silica_content_spin = None
        self.surface_area_spin = None
    
    def _add_material_specific_fields(self, grid: Gtk.Grid, start_row: int) -> int:
        """Add silica fume-specific fields to the basic info grid."""
        row = start_row
        
        # Silica content (typically 85-98%)
        silica_label = Gtk.Label("SiO2 Content (%):")
        silica_label.set_halign(Gtk.Align.END)
        silica_label.get_style_context().add_class("form-label")
        silica_label.set_tooltip_text("Silicon dioxide content (typically 85-98%)")
        
        self.silica_content_spin = Gtk.SpinButton.new_with_range(80.0, 100.0, 0.1)
        self.silica_content_spin.set_digits(1)
        self.silica_content_spin.set_value(92.0)  # Typical value
        self.silica_content_spin.set_tooltip_text("High-quality silica fume is typically >90% SiO2")
        
        grid.attach(silica_label, 0, row, 1, 1)
        grid.attach(self.silica_content_spin, 1, row, 1, 1)
        row += 1
        
        # Specific surface area (very high for silica fume)
        surface_label = Gtk.Label("Surface Area (m²/kg):")
        surface_label.set_halign(Gtk.Align.END)
        surface_label.get_style_context().add_class("form-label")
        surface_label.set_tooltip_text("Specific surface area (very high for silica fume)")
        
        self.surface_area_spin = Gtk.SpinButton.new_with_range(15000, 25000, 100)
        self.surface_area_spin.set_digits(0)
        self.surface_area_spin.set_value(20000)  # Typical value
        self.surface_area_spin.set_tooltip_text("Silica fume typically has 15,000-25,000 m²/kg")
        
        grid.attach(surface_label, 0, row, 1, 1)
        grid.attach(self.surface_area_spin, 1, row, 1, 1)
        row += 1
        
        return row
    
    def _add_property_sections(self, container: Gtk.Container) -> None:
        """Add silica fume-specific property sections."""
        # Single phase section for silica fume
        phase_frame = Gtk.Frame(label="Phase Properties")
        phase_grid = Gtk.Grid()
        phase_grid.set_row_spacing(10)
        phase_grid.set_column_spacing(15)
        phase_grid.set_margin_top(10)
        phase_grid.set_margin_bottom(10)
        phase_grid.set_margin_left(15)
        phase_grid.set_margin_right(15)
        
        # Single phase fraction (always 1.0 for silica fume)
        phase_label = Gtk.Label("Silica Fume Fraction:")
        phase_label.set_halign(Gtk.Align.END)
        phase_label.get_style_context().add_class("form-label")
        
        self.silica_fume_fraction_spin = Gtk.SpinButton.new_with_range(0.0, 1.0, 0.01)
        self.silica_fume_fraction_spin.set_digits(3)
        self.silica_fume_fraction_spin.set_value(1.0)
        self.silica_fume_fraction_spin.set_sensitive(False)  # Always 1.0
        self.silica_fume_fraction_spin.set_tooltip_text("Silica fume is treated as a single phase (always 1.0)")
        
        phase_grid.attach(phase_label, 0, 0, 1, 1)
        phase_grid.attach(self.silica_fume_fraction_spin, 1, 0, 1, 1)
        
        phase_frame.add(phase_grid)
        container.pack_start(phase_frame, False, False, 0)
        
        # Particle size distribution section
        self._add_psd_section(container)
    
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
        
        # Add section header for log-normal parameters
        lognormal_header = Gtk.Label()
        lognormal_header.set_markup('<b>Option 1: Log-Normal Distribution Parameters</b>')
        lognormal_header.set_halign(Gtk.Align.START)
        lognormal_header.set_margin_top(5)
        psd_box.pack_start(lognormal_header, False, False, 0)
        
        psd_box.pack_start(psd_grid, False, False, 0)
        
        # Add separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        separator.set_margin_top(15)
        separator.set_margin_bottom(10)
        psd_box.pack_start(separator, False, False, 0)
        
        # CSV Import section with header
        csv_header = Gtk.Label()
        csv_header.set_markup('<b>Option 2: Import Experimental Data</b>')
        csv_header.set_halign(Gtk.Align.START)
        psd_box.pack_start(csv_header, False, False, 0)
        
        csv_desc = Gtk.Label()
        csv_desc.set_markup('<i>Upload a CSV file with experimental particle size measurements</i>')
        csv_desc.set_halign(Gtk.Align.START)
        csv_desc.get_style_context().add_class("dim-label")
        csv_desc.set_margin_bottom(5)
        psd_box.pack_start(csv_desc, False, False, 0)
        
        # CSV Import button
        import_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        import_box.set_halign(Gtk.Align.START)
        
        import_button = Gtk.Button.new_with_label("Import CSV Data")
        import_button.connect('clicked', self._on_import_csv_psd_simple)
        import_button.set_tooltip_text("Import experimental PSD data from CSV file (diameter_um, mass_fraction)")
        import_box.pack_start(import_button, False, False, 0)
        
        psd_box.pack_start(import_box, False, False, 0)
        
        # PSD summary (will be updated dynamically)
        self.psd_summary_label = Gtk.Label()
        self.psd_summary_label.set_halign(Gtk.Align.START)
        self.psd_summary_label.set_margin_top(10)
        psd_box.pack_start(self.psd_summary_label, False, False, 0)
        
        # Store reference to psd_box for table insertion
        self.psd_container = psd_box
        
        psd_frame.add(psd_box)
        container.pack_start(psd_frame, False, False, 0)
    
    def _update_psd_summary_label(self):
        """Update the PSD summary label based on current data state."""
        if hasattr(self, 'imported_psd_data') and self.imported_psd_data:
            # Show CSV import status
            self.psd_summary_label.set_markup(
                f'<i><b>Using Option 2:</b> {len(self.imported_psd_data)} experimental data points imported - Click table cells to edit</i>'
            )
        else:
            # Show log-normal status
            self.psd_summary_label.set_markup(
                '<i><b>Using Option 1:</b> Particle size distribution will be modeled as log-normal</i>'
            )
    
    def _on_import_csv_psd_simple(self, button):
        """Import PSD data from CSV file for simple material types."""
        dialog = Gtk.FileChooserDialog(
            title="Import PSD Data from CSV",
            parent=self,
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
        dialog.add_button(Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        
        # Add CSV file filter
        csv_filter = Gtk.FileFilter()
        csv_filter.set_name("CSV Files")
        csv_filter.add_pattern("*.csv")
        csv_filter.add_mime_type("text/csv")
        dialog.add_filter(csv_filter)
        
        # Add all files filter
        all_filter = Gtk.FileFilter()
        all_filter.set_name("All Files")
        all_filter.add_pattern("*")
        dialog.add_filter(all_filter)
        
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            try:
                self._load_csv_psd_data_simple(filename)
            except Exception as e:
                error_dialog = Gtk.MessageDialog(
                    transient_for=self,
                    flags=0,
                    message_type=Gtk.MessageType.ERROR,
                    buttons=Gtk.ButtonsType.OK,
                    text="Error importing CSV file"
                )
                error_dialog.format_secondary_text(f"Could not import PSD data: {e}")
                error_dialog.run()
                error_dialog.destroy()
        
        dialog.destroy()
    
    def _load_csv_psd_data_simple(self, filename):
        """Load PSD data from CSV file for simple material types."""
        import csv
        
        with open(filename, 'r', encoding='utf-8') as file:
            # Try to detect if file has headers
            first_line = file.readline().strip()
            file.seek(0)
            
            has_header = False
            try:
                # Try to parse first line as numbers
                parts = first_line.replace(',', ' ').split()
                if len(parts) >= 2:
                    float(parts[0])
                    float(parts[1])
            except (ValueError, IndexError):
                has_header = True
            
            # Parse CSV data
            reader = csv.reader(file)
            if has_header:
                next(reader)  # Skip header row
            
            loaded_points = []
            for row_num, row in enumerate(reader, start=1):
                if len(row) < 2:
                    continue  # Skip incomplete rows
                
                try:
                    diameter = float(row[0])
                    mass_fraction = float(row[1])
                    
                    # Validate data ranges
                    if diameter <= 0:
                        self.logger.warning(f"Invalid diameter {diameter} on row {row_num}, skipping")
                        continue
                    
                    if not (0 <= mass_fraction <= 1):
                        # Try to handle percentage format (0-100%) by converting to fraction
                        if 0 <= mass_fraction <= 100:
                            mass_fraction = mass_fraction / 100.0
                        else:
                            self.logger.warning(f"Invalid mass fraction {mass_fraction} on row {row_num}, skipping")
                            continue
                    
                    loaded_points.append((diameter, mass_fraction))
                    
                except (ValueError, IndexError) as e:
                    self.logger.warning(f"Could not parse row {row_num}: {row}, error: {e}")
                    continue
            
            if not loaded_points:
                raise ValueError("No valid PSD data points found in CSV file")
            
            # Sort by diameter (ascending)
            loaded_points.sort(key=lambda x: x[0])
            
            # Store the imported PSD data for later use
            self.imported_psd_data = loaded_points
            
            # Create and show an editable table for the imported data
            self._create_psd_data_table()
            
            # Update summary label to show imported data info
            self._update_psd_summary_label()
            
            # Show success message
            self.parent_window.update_status(f"Imported {len(loaded_points)} PSD data points from CSV", "success", 3)
            
            self.logger.info(f"Successfully imported {len(loaded_points)} PSD points from {filename}")
    
    def _create_psd_data_table(self):
        """Create an editable table to display and edit imported PSD data."""
        if not hasattr(self, 'imported_psd_data') or not self.imported_psd_data:
            return
        
        # If table already exists, remove it first
        if hasattr(self, 'psd_table_box'):
            self.psd_table_box.get_parent().remove(self.psd_table_box)
        
        # Create new table container
        self.psd_table_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        
        # Table label
        table_label = Gtk.Label()
        table_label.set_markup('<b>Imported PSD Data (Editable)</b>')
        table_label.set_halign(Gtk.Align.START)
        self.psd_table_box.pack_start(table_label, False, False, 0)
        
        # Scrolled window for the table
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.set_size_request(-1, 200)
        
        # Create list store for the data
        self.psd_data_store = Gtk.ListStore(float, float)  # diameter, mass_fraction
        
        # Populate with imported data
        for diameter, mass_fraction in self.imported_psd_data:
            self.psd_data_store.append([diameter, mass_fraction])
        
        # Create tree view
        tree_view = Gtk.TreeView(model=self.psd_data_store)
        tree_view.set_reorderable(True)
        
        # Diameter column (editable)
        diameter_renderer = Gtk.CellRendererText()
        diameter_renderer.set_property('editable', True)
        diameter_renderer.connect('edited', self._on_diameter_edited)
        diameter_column = Gtk.TreeViewColumn("Diameter (μm)", diameter_renderer, text=0)
        diameter_column.set_resizable(True)
        tree_view.append_column(diameter_column)
        
        # Mass fraction column (editable)
        fraction_renderer = Gtk.CellRendererText()
        fraction_renderer.set_property('editable', True)
        fraction_renderer.connect('edited', self._on_fraction_edited)
        fraction_column = Gtk.TreeViewColumn("Mass Fraction", fraction_renderer, text=1)
        fraction_column.set_resizable(True)
        tree_view.append_column(fraction_column)
        
        scrolled_window.add(tree_view)
        self.psd_table_box.pack_start(scrolled_window, True, True, 0)
        
        # Buttons for table operations
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        
        add_point_btn = Gtk.Button.new_with_label("Add Point")
        add_point_btn.connect('clicked', self._on_add_psd_data_point)
        button_box.pack_start(add_point_btn, False, False, 0)
        
        remove_point_btn = Gtk.Button.new_with_label("Remove Point")
        remove_point_btn.connect('clicked', self._on_remove_psd_data_point, tree_view)
        button_box.pack_start(remove_point_btn, False, False, 0)
        
        self.psd_table_box.pack_start(button_box, False, False, 0)
        
        # Insert the table box after the summary label
        parent_box = self.psd_summary_label.get_parent()
        children = parent_box.get_children()
        summary_index = children.index(self.psd_summary_label)
        parent_box.pack_start(self.psd_table_box, False, False, 0)
        parent_box.reorder_child(self.psd_table_box, summary_index + 1)
        
        # Show all new widgets
        self.psd_table_box.show_all()
    
    def _on_diameter_edited(self, renderer, path, new_text):
        """Handle editing of diameter values in PSD table."""
        try:
            value = float(new_text)
            if value > 0:
                self.psd_data_store[path][0] = value
                self._update_imported_psd_data()
        except ValueError:
            pass
    
    def _on_fraction_edited(self, renderer, path, new_text):
        """Handle editing of mass fraction values in PSD table."""
        try:
            value = float(new_text)
            if 0 <= value <= 1.0:
                self.psd_data_store[path][1] = value
                self._update_imported_psd_data()
        except ValueError:
            pass
    
    def _on_add_psd_data_point(self, button):
        """Add a new point to the PSD data table."""
        self.psd_data_store.append([1.0, 0.001])  # Default values
        self._update_imported_psd_data()
    
    def _on_remove_psd_data_point(self, button, tree_view):
        """Remove selected point from PSD data table."""
        selection = tree_view.get_selection()
        model, tree_iter = selection.get_selected()
        if tree_iter:
            model.remove(tree_iter)
            self._update_imported_psd_data()
    
    def _update_imported_psd_data(self):
        """Update the imported_psd_data list from the table store."""
        if hasattr(self, 'psd_data_store'):
            self.imported_psd_data = []
            for row in self.psd_data_store:
                self.imported_psd_data.append((float(row[0]), float(row[1])))
            
            # Sort by diameter
            self.imported_psd_data.sort(key=lambda x: x[0])

    
    def _add_advanced_sections(self, container: Gtk.Box) -> None:
        """Add silica fume-specific advanced sections."""
        # Simple materials don't need advanced sections
        pass
    
    def _connect_material_signals(self) -> None:
        """Connect silica fume-specific signals."""
        # Connect value change signals if needed
        pass
    
    def _load_material_specific_data(self) -> None:
        """Load silica fume-specific data into form fields."""
        if not self.material_data:
            # For new materials, just update the summary to show log-normal mode
            self._update_psd_summary_label()
            return
        
        # Load silica fume specific fields
        if hasattr(self, 'silica_content_spin') and 'silica_content' in self.material_data:
            self.silica_content_spin.set_value(self.material_data['silica_content'])
        if hasattr(self, 'surface_area_spin') and 'surface_area' in self.material_data:
            self.surface_area_spin.set_value(self.material_data['surface_area'])
        
        # Load PSD parameters
        if hasattr(self, 'psd_median_spin'):
            self.psd_median_spin.set_value(float(self.material_data.get('psd_median', 5.0)))
        if hasattr(self, 'psd_spread_spin'):
            self.psd_spread_spin.set_value(float(self.material_data.get('psd_spread', 2.0)))
        
        # Load custom PSD data if available
        psd_custom_points = self.material_data.get('psd_custom_points')
        if psd_custom_points:
            try:
                import json
                psd_data = json.loads(psd_custom_points)
                # Convert from dict format back to tuple format
                self.imported_psd_data = [(point['diameter'], point['mass_fraction']) for point in psd_data]
                # Create and show the editable table
                self._create_psd_data_table()
                # Update summary to show loaded data
                self._update_psd_summary_label()
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                self.logger.warning(f"Could not load custom PSD data: {e}")
                # Clear invalid data
                self.material_data['psd_custom_points'] = None
                # Update summary to show log-normal mode
                self._update_psd_summary_label()
        else:
            # No existing PSD data, update summary to show log-normal mode
            self._update_psd_summary_label()
    
    def _validate_material_specific_field(self, widget) -> None:
        """Validate silica fume-specific fields."""
        # Add specific validation if needed
        pass
    
    def _validate_all_material_fields(self) -> None:
        """Validate all silica fume-specific fields."""
        # Add comprehensive validation if needed
        pass
    
    def _collect_material_specific_data(self) -> Dict[str, Any]:
        """Collect silica fume-specific form data."""
        data = {
            'silica_fume_fraction': 1.0,  # Always 1.0 for single phase
        }
        if hasattr(self, 'silica_content_spin') and self.silica_content_spin:
            data['silica_content'] = self.silica_content_spin.get_value()
        if hasattr(self, 'surface_area_spin') and self.surface_area_spin:
            data['surface_area'] = self.surface_area_spin.get_value()
        
        # Include PSD parameters
        if hasattr(self, 'psd_median_spin') and self.psd_median_spin:
            data['psd_median'] = self.psd_median_spin.get_value()
        if hasattr(self, 'psd_spread_spin') and self.psd_spread_spin:
            data['psd_spread'] = self.psd_spread_spin.get_value()
        
        # Include imported PSD data if available (store as JSON)
        if hasattr(self, 'imported_psd_data') and self.imported_psd_data:
            import json
            # Convert list of tuples to list of dicts for JSON storage
            psd_points = [{"diameter": d, "mass_fraction": mf} for d, mf in self.imported_psd_data]
            data['psd_custom_points'] = json.dumps(psd_points)
        
        return data


class LimestoneDialog(MaterialDialogBase):
    """Dialog for managing limestone materials."""
    
    def __init__(self, parent: 'VCCTLMainWindow', material_data: Optional[Dict[str, Any]] = None):
        """Initialize the limestone dialog."""
        self.psd_container = None
        super().__init__(parent, 'limestone', material_data)
        
        # Limestone-specific UI components (minimal since it's single phase)
        self.caco3_content_spin = None
    
    def _add_material_specific_fields(self, grid: Gtk.Grid, start_row: int) -> int:
        """Add limestone-specific fields to the basic info grid."""
        row = start_row
        
        # CaCO3 content (typically 95-99%)
        caco3_label = Gtk.Label("CaCO3 Content (%):")
        caco3_label.set_halign(Gtk.Align.END)
        caco3_label.get_style_context().add_class("form-label")
        caco3_label.set_tooltip_text("Calcium carbonate content (typically 95-99%)")
        
        self.caco3_content_spin = Gtk.SpinButton.new_with_range(85.0, 100.0, 0.1)
        self.caco3_content_spin.set_digits(1)
        self.caco3_content_spin.set_value(97.0)  # Typical value
        self.caco3_content_spin.set_tooltip_text("High-grade limestone is typically >95% CaCO3")
        
        grid.attach(caco3_label, 0, row, 1, 1)
        grid.attach(self.caco3_content_spin, 1, row, 1, 1)
        row += 1
        
        return row
    
    def _add_property_sections(self, container: Gtk.Container) -> None:
        """Add limestone-specific property sections."""
        # Single phase section for limestone
        phase_frame = Gtk.Frame(label="Phase Properties")
        phase_grid = Gtk.Grid()
        phase_grid.set_row_spacing(10)
        phase_grid.set_column_spacing(15)
        phase_grid.set_margin_top(10)
        phase_grid.set_margin_bottom(10)
        phase_grid.set_margin_left(15)
        phase_grid.set_margin_right(15)
        
        # Single phase fraction (always 1.0 for limestone)
        phase_label = Gtk.Label("Limestone Fraction:")
        phase_label.set_halign(Gtk.Align.END)
        phase_label.get_style_context().add_class("form-label")
        
        self.limestone_fraction_spin = Gtk.SpinButton.new_with_range(0.0, 1.0, 0.01)
        self.limestone_fraction_spin.set_digits(3)
        self.limestone_fraction_spin.set_value(1.0)
        self.limestone_fraction_spin.set_sensitive(False)  # Always 1.0
        self.limestone_fraction_spin.set_tooltip_text("Limestone is treated as a single phase (always 1.0)")
        
        phase_grid.attach(phase_label, 0, 0, 1, 1)
        phase_grid.attach(self.limestone_fraction_spin, 1, 0, 1, 1)
        
        phase_frame.add(phase_grid)
        container.pack_start(phase_frame, False, False, 0)
        
        # Particle size distribution section
        self._add_psd_section(container)
    
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
        
        # Add section header for log-normal parameters
        lognormal_header = Gtk.Label()
        lognormal_header.set_markup('<b>Option 1: Log-Normal Distribution Parameters</b>')
        lognormal_header.set_halign(Gtk.Align.START)
        lognormal_header.set_margin_top(5)
        psd_box.pack_start(lognormal_header, False, False, 0)
        
        psd_box.pack_start(psd_grid, False, False, 0)
        
        # Add separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        separator.set_margin_top(15)
        separator.set_margin_bottom(10)
        psd_box.pack_start(separator, False, False, 0)
        
        # CSV Import section with header
        csv_header = Gtk.Label()
        csv_header.set_markup('<b>Option 2: Import Experimental Data</b>')
        csv_header.set_halign(Gtk.Align.START)
        psd_box.pack_start(csv_header, False, False, 0)
        
        csv_desc = Gtk.Label()
        csv_desc.set_markup('<i>Upload a CSV file with experimental particle size measurements</i>')
        csv_desc.set_halign(Gtk.Align.START)
        csv_desc.get_style_context().add_class("dim-label")
        csv_desc.set_margin_bottom(5)
        psd_box.pack_start(csv_desc, False, False, 0)
        
        # CSV Import button
        import_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        import_box.set_halign(Gtk.Align.START)
        
        import_button = Gtk.Button.new_with_label("Import CSV Data")
        import_button.connect('clicked', self._on_import_csv_psd_simple)
        import_button.set_tooltip_text("Import experimental PSD data from CSV file (diameter_um, mass_fraction)")
        import_box.pack_start(import_button, False, False, 0)
        
        psd_box.pack_start(import_box, False, False, 0)
        
        # PSD summary (will be updated dynamically)
        self.psd_summary_label = Gtk.Label()
        self.psd_summary_label.set_halign(Gtk.Align.START)
        self.psd_summary_label.set_margin_top(10)
        psd_box.pack_start(self.psd_summary_label, False, False, 0)
        
        # Store reference to psd_box for table insertion
        self.psd_container = psd_box
        
        psd_frame.add(psd_box)
        container.pack_start(psd_frame, False, False, 0)
    
    def _update_psd_summary_label(self):
        """Update the PSD summary label based on current data state."""
        if hasattr(self, 'imported_psd_data') and self.imported_psd_data:
            # Show CSV import status
            self.psd_summary_label.set_markup(
                f'<i><b>Using Option 2:</b> {len(self.imported_psd_data)} experimental data points imported - Click table cells to edit</i>'
            )
        else:
            # Show log-normal status
            self.psd_summary_label.set_markup(
                '<i><b>Using Option 1:</b> Particle size distribution will be modeled as log-normal</i>'
            )
    
    def _on_import_csv_psd_simple(self, button):
        """Import PSD data from CSV file for simple material types."""
        dialog = Gtk.FileChooserDialog(
            title="Import PSD Data from CSV",
            parent=self,
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
        dialog.add_button(Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        
        # Add CSV file filter
        csv_filter = Gtk.FileFilter()
        csv_filter.set_name("CSV Files")
        csv_filter.add_pattern("*.csv")
        csv_filter.add_mime_type("text/csv")
        dialog.add_filter(csv_filter)
        
        # Add all files filter
        all_filter = Gtk.FileFilter()
        all_filter.set_name("All Files")
        all_filter.add_pattern("*")
        dialog.add_filter(all_filter)
        
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            try:
                self._load_csv_psd_data_simple(filename)
            except Exception as e:
                error_dialog = Gtk.MessageDialog(
                    transient_for=self,
                    flags=0,
                    message_type=Gtk.MessageType.ERROR,
                    buttons=Gtk.ButtonsType.OK,
                    text="Error importing CSV file"
                )
                error_dialog.format_secondary_text(f"Could not import PSD data: {e}")
                error_dialog.run()
                error_dialog.destroy()
        
        dialog.destroy()
    
    def _load_csv_psd_data_simple(self, filename):
        """Load PSD data from CSV file for simple material types."""
        import csv
        
        with open(filename, 'r', encoding='utf-8') as file:
            # Try to detect if file has headers
            first_line = file.readline().strip()
            file.seek(0)
            
            has_header = False
            try:
                # Try to parse first line as numbers
                parts = first_line.replace(',', ' ').split()
                if len(parts) >= 2:
                    float(parts[0])
                    float(parts[1])
            except (ValueError, IndexError):
                has_header = True
            
            # Parse CSV data
            reader = csv.reader(file)
            if has_header:
                next(reader)  # Skip header row
            
            loaded_points = []
            for row_num, row in enumerate(reader, start=1):
                if len(row) < 2:
                    continue  # Skip incomplete rows
                
                try:
                    diameter = float(row[0])
                    mass_fraction = float(row[1])
                    
                    # Validate data ranges
                    if diameter <= 0:
                        self.logger.warning(f"Invalid diameter {diameter} on row {row_num}, skipping")
                        continue
                    
                    if not (0 <= mass_fraction <= 1):
                        # Try to handle percentage format (0-100%) by converting to fraction
                        if 0 <= mass_fraction <= 100:
                            mass_fraction = mass_fraction / 100.0
                        else:
                            self.logger.warning(f"Invalid mass fraction {mass_fraction} on row {row_num}, skipping")
                            continue
                    
                    loaded_points.append((diameter, mass_fraction))
                    
                except (ValueError, IndexError) as e:
                    self.logger.warning(f"Could not parse row {row_num}: {row}, error: {e}")
                    continue
            
            if not loaded_points:
                raise ValueError("No valid PSD data points found in CSV file")
            
            # Sort by diameter (ascending)
            loaded_points.sort(key=lambda x: x[0])
            
            # Store the imported PSD data for later use
            self.imported_psd_data = loaded_points
            
            # Create and show an editable table for the imported data
            self._create_psd_data_table()
            
            # Update summary label to show imported data info
            self._update_psd_summary_label()
            
            # Show success message
            self.parent_window.update_status(f"Imported {len(loaded_points)} PSD data points from CSV", "success", 3)
            
            self.logger.info(f"Successfully imported {len(loaded_points)} PSD points from {filename}")
    
    def _create_psd_data_table(self):
        """Create an editable table to display and edit imported PSD data."""
        if not hasattr(self, 'imported_psd_data') or not self.imported_psd_data:
            return
        
        # If table already exists, remove it first
        if hasattr(self, 'psd_table_box'):
            self.psd_table_box.get_parent().remove(self.psd_table_box)
        
        # Create new table container
        self.psd_table_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        
        # Table label
        table_label = Gtk.Label()
        table_label.set_markup('<b>Imported PSD Data (Editable)</b>')
        table_label.set_halign(Gtk.Align.START)
        self.psd_table_box.pack_start(table_label, False, False, 0)
        
        # Scrolled window for the table
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.set_size_request(-1, 200)
        
        # Create list store for the data
        self.psd_data_store = Gtk.ListStore(float, float)  # diameter, mass_fraction
        
        # Populate with imported data
        for diameter, mass_fraction in self.imported_psd_data:
            self.psd_data_store.append([diameter, mass_fraction])
        
        # Create tree view
        tree_view = Gtk.TreeView(model=self.psd_data_store)
        tree_view.set_reorderable(True)
        
        # Diameter column (editable)
        diameter_renderer = Gtk.CellRendererText()
        diameter_renderer.set_property('editable', True)
        diameter_renderer.connect('edited', self._on_diameter_edited)
        diameter_column = Gtk.TreeViewColumn("Diameter (μm)", diameter_renderer, text=0)
        diameter_column.set_resizable(True)
        tree_view.append_column(diameter_column)
        
        # Mass fraction column (editable)
        fraction_renderer = Gtk.CellRendererText()
        fraction_renderer.set_property('editable', True)
        fraction_renderer.connect('edited', self._on_fraction_edited)
        fraction_column = Gtk.TreeViewColumn("Mass Fraction", fraction_renderer, text=1)
        fraction_column.set_resizable(True)
        tree_view.append_column(fraction_column)
        
        scrolled_window.add(tree_view)
        self.psd_table_box.pack_start(scrolled_window, True, True, 0)
        
        # Buttons for table operations
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        
        add_point_btn = Gtk.Button.new_with_label("Add Point")
        add_point_btn.connect('clicked', self._on_add_psd_data_point)
        button_box.pack_start(add_point_btn, False, False, 0)
        
        remove_point_btn = Gtk.Button.new_with_label("Remove Point")
        remove_point_btn.connect('clicked', self._on_remove_psd_data_point, tree_view)
        button_box.pack_start(remove_point_btn, False, False, 0)
        
        self.psd_table_box.pack_start(button_box, False, False, 0)
        
        # Insert the table box after the summary label
        parent_box = self.psd_summary_label.get_parent()
        children = parent_box.get_children()
        summary_index = children.index(self.psd_summary_label)
        parent_box.pack_start(self.psd_table_box, False, False, 0)
        parent_box.reorder_child(self.psd_table_box, summary_index + 1)
        
        # Show all new widgets
        self.psd_table_box.show_all()
    
    def _on_diameter_edited(self, renderer, path, new_text):
        """Handle editing of diameter values in PSD table."""
        try:
            value = float(new_text)
            if value > 0:
                self.psd_data_store[path][0] = value
                self._update_imported_psd_data()
        except ValueError:
            pass
    
    def _on_fraction_edited(self, renderer, path, new_text):
        """Handle editing of mass fraction values in PSD table."""
        try:
            value = float(new_text)
            if 0 <= value <= 1.0:
                self.psd_data_store[path][1] = value
                self._update_imported_psd_data()
        except ValueError:
            pass
    
    def _on_add_psd_data_point(self, button):
        """Add a new point to the PSD data table."""
        self.psd_data_store.append([1.0, 0.001])  # Default values
        self._update_imported_psd_data()
    
    def _on_remove_psd_data_point(self, button, tree_view):
        """Remove selected point from PSD data table."""
        selection = tree_view.get_selection()
        model, tree_iter = selection.get_selected()
        if tree_iter:
            model.remove(tree_iter)
            self._update_imported_psd_data()
    
    def _update_imported_psd_data(self):
        """Update the imported_psd_data list from the table store."""
        if hasattr(self, 'psd_data_store'):
            self.imported_psd_data = []
            for row in self.psd_data_store:
                self.imported_psd_data.append((float(row[0]), float(row[1])))
            
            # Sort by diameter
            self.imported_psd_data.sort(key=lambda x: x[0])

    
    def _add_advanced_sections(self, container: Gtk.Box) -> None:
        """Add limestone-specific advanced sections."""
        # Simple materials don't need advanced sections
        pass
    
    def _connect_material_signals(self) -> None:
        """Connect limestone-specific signals."""
        # Connect value change signals if needed
        pass
    
    def _load_material_specific_data(self) -> None:
        """Load limestone-specific data into form fields."""
        if not self.material_data:
            # For new materials, just update the summary to show log-normal mode
            self._update_psd_summary_label()
            return
        
        # Load limestone specific fields
        if hasattr(self, 'caco3_content_spin') and 'caco3_content' in self.material_data:
            self.caco3_content_spin.set_value(self.material_data['caco3_content'])
        if hasattr(self, 'hardness_spin') and 'hardness' in self.material_data:
            self.hardness_spin.set_value(self.material_data['hardness'])
        
        # Load PSD parameters
        if hasattr(self, 'psd_median_spin'):
            self.psd_median_spin.set_value(float(self.material_data.get('psd_median', 5.0)))
        if hasattr(self, 'psd_spread_spin'):
            self.psd_spread_spin.set_value(float(self.material_data.get('psd_spread', 2.0)))
        
        # Load custom PSD data if available
        psd_custom_points = self.material_data.get('psd_custom_points')
        if psd_custom_points:
            try:
                import json
                psd_data = json.loads(psd_custom_points)
                # Convert from dict format back to tuple format
                self.imported_psd_data = [(point['diameter'], point['mass_fraction']) for point in psd_data]
                # Create and show the editable table
                self._create_psd_data_table()
                # Update summary to show loaded data
                self._update_psd_summary_label()
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                self.logger.warning(f"Could not load custom PSD data: {e}")
                # Clear invalid data
                self.material_data['psd_custom_points'] = None
                # Update summary to show log-normal mode
                self._update_psd_summary_label()
        else:
            # No existing PSD data, update summary to show log-normal mode
            self._update_psd_summary_label()
    
    def _validate_material_specific_field(self, widget) -> None:
        """Validate limestone-specific fields."""
        # Add specific validation if needed
        pass
    
    def _validate_all_material_fields(self) -> None:
        """Validate all limestone-specific fields."""
        # Add comprehensive validation if needed
        pass
    
    def _collect_material_specific_data(self) -> Dict[str, Any]:
        """Collect limestone-specific form data."""
        data = {
            'limestone_fraction': 1.0,  # Always 1.0 for single phase
        }
        if hasattr(self, 'caco3_content_spin') and self.caco3_content_spin:
            data['caco3_content'] = self.caco3_content_spin.get_value()
        if hasattr(self, 'hardness_spin') and self.hardness_spin:
            data['hardness'] = self.hardness_spin.get_value()
        
        # Include PSD parameters
        if hasattr(self, 'psd_median_spin') and self.psd_median_spin:
            data['psd_median'] = self.psd_median_spin.get_value()
        if hasattr(self, 'psd_spread_spin') and self.psd_spread_spin:
            data['psd_spread'] = self.psd_spread_spin.get_value()
        
        # Include imported PSD data if available (store as JSON)
        if hasattr(self, 'imported_psd_data') and self.imported_psd_data:
            import json
            # Convert list of tuples to list of dicts for JSON storage
            psd_points = [{"diameter": d, "mass_fraction": mf} for d, mf in self.imported_psd_data]
            data['psd_custom_points'] = json.dumps(psd_points)
        
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
        'silica_fume': SilicaFumeDialog,
        'limestone': LimestoneDialog,
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
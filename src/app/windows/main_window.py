#!/usr/bin/env python3
"""
VCCTL Main Window

The primary application window for the VCCTL GTK3 desktop application.
"""

import gi
import logging
import time
from datetime import datetime
from typing import TYPE_CHECKING, Optional, Dict, Any
import json
from pathlib import Path

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GObject

if TYPE_CHECKING:
    from app.application import VCCTLApplication

from app.services.service_container import get_service_container
from app.windows.panels import MaterialsPanel, MixDesignPanel, MicrostructurePanel, HydrationPanel, FileManagementPanel, OperationsMonitoringPanel
from app.utils.error_handling import get_error_handler, ErrorCategory, ErrorSeverity
from app.utils.performance_monitor import get_performance_monitor, profile_function
from app.ui import create_ui_polish_manager, UIPolishManager
from app.help import create_help_system, HelpManager, HelpDialog, TooltipManager


class VCCTLMainWindow(Gtk.ApplicationWindow):
    """Main application window for VCCTL."""
    
    def __init__(self, app: 'VCCTLApplication'):
        """Initialize the main window."""
        super().__init__(application=app)
        
        self.app = app
        self.logger = logging.getLogger('VCCTL.MainWindow')
        
        # Initialize error handling and performance monitoring
        self.error_handler = get_error_handler(self)
        self.performance_monitor = get_performance_monitor()
        self.performance_monitor.start_monitoring()
        
        # Initialize UI polish manager (theming, accessibility, keyboard shortcuts, responsive layout)
        self.ui_polish_manager = create_ui_polish_manager(self)
        
        # Initialize help system
        self.help_manager, self.tooltip_manager = create_help_system(self)
        self.help_dialog = None
        
        # Panel references for UI polish integration
        self.panels = {}
        
        # Window properties
        self.set_title("VCCTL - Virtual Cement and Concrete Testing Laboratory")
        self.set_default_size(1200, 800)
        self.set_position(Gtk.WindowPosition.CENTER)
        
        try:
            # Setup the UI
            self._setup_ui()
            
            # Connect signals
            self.connect('delete-event', self._on_delete_event)
            self.connect('destroy', self._on_destroy)
            
            # Load window state
            self._load_window_state()
            
            self.logger.info("Main window initialized")
            
        except Exception as e:
            self.error_handler.handle_critical_error(
                e, 
                ErrorCategory.UI, 
                context={'component': 'main_window', 'phase': 'initialization'},
                user_message="Failed to initialize the main window. The application may not function properly."
            )
    
    def _setup_ui(self) -> None:
        """Setup the main window UI components."""
        # Create main vertical box
        main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(main_vbox)
        
        # Create header bar
        self._create_header_bar()
        
        # Create main content area
        self._create_content_area(main_vbox)
        
        # Create status bar
        self._create_status_bar(main_vbox)
        
        # Setup help system integration
        self._setup_help_system_integration()
        
        # Show all widgets
        self.show_all()
    
    def _create_header_bar(self) -> None:
        """Create and setup the header bar."""
        self.header_bar = Gtk.HeaderBar()
        self.header_bar.set_show_close_button(True)
        self.header_bar.set_title("VCCTL")
        self.header_bar.set_subtitle("Virtual Cement and Concrete Testing Laboratory")
        
        # Add menu button to header bar
        menu_button = Gtk.MenuButton()
        menu_button.set_image(Gtk.Image.new_from_icon_name("open-menu-symbolic", Gtk.IconSize.BUTTON))
        menu_button.set_tooltip_text("Application Menu")
        self.header_bar.pack_end(menu_button)
        
        # Create application menu
        self._create_app_menu(menu_button)
        
        # Set as titlebar
        self.set_titlebar(self.header_bar)
    
    def _create_app_menu(self, menu_button: Gtk.MenuButton) -> None:
        """Create the application menu."""
        menu = Gtk.Menu()
        
        # File section
        file_section = Gtk.MenuItem(label="File")
        file_submenu = Gtk.Menu()
        
        new_project_item = Gtk.MenuItem(label="New Project")
        new_project_item.connect('activate', self._on_new_project_clicked)
        file_submenu.append(new_project_item)
        
        open_project_item = Gtk.MenuItem(label="Open Project")
        open_project_item.connect('activate', self._on_open_project_clicked)
        file_submenu.append(open_project_item)
        
        file_submenu.append(Gtk.SeparatorMenuItem())
        
        import_item = Gtk.MenuItem(label="Import Data")
        import_item.connect('activate', self._on_import_clicked)
        file_submenu.append(import_item)
        
        export_item = Gtk.MenuItem(label="Export Data")
        export_item.connect('activate', self._on_export_clicked)
        file_submenu.append(export_item)
        
        file_section.set_submenu(file_submenu)
        menu.append(file_section)
        
        # Tools section
        tools_section = Gtk.MenuItem(label="Tools")
        tools_submenu = Gtk.Menu()
        
        materials_item = Gtk.MenuItem(label="Materials Manager")
        materials_item.connect('activate', lambda w: self.switch_to_tab("materials"))
        tools_submenu.append(materials_item)
        
        mix_design_item = Gtk.MenuItem(label="Mix Designer")
        mix_design_item.connect('activate', lambda w: self.switch_to_tab("mix_design"))
        tools_submenu.append(mix_design_item)
        
        microstructure_item = Gtk.MenuItem(label="Microstructure Parameters")
        microstructure_item.connect('activate', lambda w: self.switch_to_tab("microstructure"))
        tools_submenu.append(microstructure_item)
        
        hydration_item = Gtk.MenuItem(label="Hydration Simulation")
        hydration_item.connect('activate', lambda w: self.switch_to_tab("hydration"))
        tools_submenu.append(hydration_item)
        
        file_manager_item = Gtk.MenuItem(label="File Manager")
        file_manager_item.connect('activate', lambda w: self.switch_to_tab("files"))
        tools_submenu.append(file_manager_item)
        
        operations_item = Gtk.MenuItem(label="Operation Manager")
        operations_item.connect('activate', lambda w: self.switch_to_tab("operations"))
        tools_submenu.append(operations_item)
        
        tools_submenu.append(Gtk.SeparatorMenuItem())
        
        service_status_item = Gtk.MenuItem(label="Service Status")
        service_status_item.connect('activate', self._on_service_status_clicked)
        tools_submenu.append(service_status_item)
        
        tools_section.set_submenu(tools_submenu)
        menu.append(tools_section)
        
        # View section
        view_section = Gtk.MenuItem(label="View")
        view_submenu = Gtk.Menu()
        
        home_item = Gtk.MenuItem(label="Home")
        home_item.connect('activate', lambda w: self.switch_to_tab("home"))
        view_submenu.append(home_item)
        
        results_item = Gtk.MenuItem(label="Results")
        results_item.connect('activate', lambda w: self.switch_to_tab("results"))
        view_submenu.append(results_item)
        
        view_submenu.append(Gtk.SeparatorMenuItem())
        
        fullscreen_item = Gtk.MenuItem(label="Fullscreen")
        fullscreen_item.connect('activate', self._on_fullscreen_clicked)
        view_submenu.append(fullscreen_item)
        
        view_section.set_submenu(view_submenu)
        menu.append(view_section)
        
        # Separator
        menu.append(Gtk.SeparatorMenuItem())
        
        # Preferences menu item
        prefs_item = Gtk.MenuItem(label="Preferences")
        prefs_item.connect('activate', self._on_preferences_clicked)
        menu.append(prefs_item)
        
        # Help section
        help_section = Gtk.MenuItem(label="Help")
        help_submenu = Gtk.Menu()
        
        help_contents_item = Gtk.MenuItem(label="Help Contents")
        help_contents_item.connect('activate', self._on_help_contents_clicked)
        help_submenu.append(help_contents_item)
        
        getting_started_item = Gtk.MenuItem(label="Getting Started")
        getting_started_item.connect('activate', self._on_getting_started_clicked)
        help_submenu.append(getting_started_item)
        
        user_guide_item = Gtk.MenuItem(label="User Guide")
        user_guide_item.connect('activate', self._on_user_guide_clicked)
        help_submenu.append(user_guide_item)
        
        help_submenu.append(Gtk.SeparatorMenuItem())
        
        troubleshooting_item = Gtk.MenuItem(label="Troubleshooting")
        troubleshooting_item.connect('activate', self._on_troubleshooting_clicked)
        help_submenu.append(troubleshooting_item)
        
        examples_item = Gtk.MenuItem(label="Examples")
        examples_item.connect('activate', self._on_examples_clicked)
        help_submenu.append(examples_item)
        
        help_submenu.append(Gtk.SeparatorMenuItem())
        
        about_item = Gtk.MenuItem(label="About VCCTL")
        about_item.connect('activate', self._on_about_clicked)
        help_submenu.append(about_item)
        
        help_section.set_submenu(help_submenu)
        menu.append(help_section)
        
        # Separator
        menu.append(Gtk.SeparatorMenuItem())
        
        # Quit menu item
        quit_item = Gtk.MenuItem(label="Quit")
        quit_item.connect('activate', self._on_quit_clicked)
        menu.append(quit_item)
        
        menu.show_all()
        menu_button.set_popup(menu)
    
    def _create_content_area(self, main_vbox: Gtk.Box) -> None:
        """Create the main content area."""
        # Create a notebook for tabbed interface
        self.notebook = Gtk.Notebook()
        self.notebook.set_show_tabs(True)
        self.notebook.set_show_border(True)
        self.notebook.set_scrollable(True)
        self.notebook.set_tab_pos(Gtk.PositionType.TOP)
        
        # Connect notebook signals
        self.notebook.connect('switch-page', self._on_tab_switched)
        
        # Create tab pages
        self._create_home_tab()
        self._create_materials_tab()
        self._create_mix_design_tab()
        self._create_microstructure_tab()
        self._create_hydration_tab()
        self._create_file_management_tab()
        self._create_operations_tab()
        self._create_results_tab()
        
        # Pack notebook into main container
        main_vbox.pack_start(self.notebook, True, True, 0)
        
        # Set initial tab
        self.notebook.set_current_page(0)
    
    def _create_status_bar(self, main_vbox: Gtk.Box) -> None:
        """Create the status bar."""
        # Create main status bar container
        status_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        status_container.set_name("status-container")
        
        # Main status bar
        self.status_bar = Gtk.Statusbar()
        self.status_context_id = self.status_bar.get_context_id("main")
        self.progress_context_id = self.status_bar.get_context_id("progress")
        
        # Add initial status
        self.status_bar.push(self.status_context_id, "Ready")
        status_container.pack_start(self.status_bar, True, True, 0)
        
        # Progress bar (initially hidden)
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_size_request(150, -1)
        self.progress_bar.set_show_text(True)
        self.progress_bar.set_no_show_all(True)  # Hidden by default
        status_container.pack_start(self.progress_bar, False, False, 5)
        
        # Status icon (for showing status types)
        self.status_icon = Gtk.Image()
        self.status_icon.set_from_icon_name("dialog-information", Gtk.IconSize.SMALL_TOOLBAR)
        self.status_icon.set_no_show_all(True)  # Hidden by default
        status_container.pack_start(self.status_icon, False, False, 5)
        
        # Service status indicator
        self.service_status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self._create_service_indicators()
        status_container.pack_start(self.service_status_box, False, False, 10)
        
        # Separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        status_container.pack_start(separator, False, False, 5)
        
        # NIST attribution
        nist_label = Gtk.Label(label="NIST BFRL")
        nist_label.set_margin_right(10)
        nist_label.set_tooltip_text("National Institute of Standards and Technology\nBuilding and Fire Research Laboratory")
        status_container.pack_end(nist_label, False, False, 0)
        
        # Version info
        version_label = Gtk.Label(label=f"v{self.app.app_version}")
        version_label.set_margin_right(10)
        version_label.get_style_context().add_class("dim-label")
        status_container.pack_end(version_label, False, False, 0)
        
        main_vbox.pack_end(status_container, False, False, 0)
    
    def _load_window_state(self) -> None:
        """Load saved window state (size, position, etc.)."""
        try:
            service_container = get_service_container()
            config_manager = service_container.config_manager
            
            # Get window state from config
            window_state = config_manager.get_window_state()
            
            if window_state:
                # Set window size
                width = window_state.get('width', 1200)
                height = window_state.get('height', 800)
                self.set_default_size(width, height)
                
                # Set window position
                x = window_state.get('x')
                y = window_state.get('y')
                if x is not None and y is not None:
                    self.move(x, y)
                
                # Set maximized state
                if window_state.get('maximized', False):
                    self.maximize()
                
                self.logger.debug(f"Loaded window state: {window_state}")
        except Exception as e:
            self.logger.warning(f"Could not load window state: {e}")
            # Use defaults
            self.set_default_size(1200, 800)
    
    def _save_window_state(self) -> None:
        """Save current window state."""
        try:
            service_container = get_service_container()
            config_manager = service_container.config_manager
            
            # Get current window properties
            width, height = self.get_size()
            x, y = self.get_position()
            maximized = self.is_maximized()
            
            window_state = {
                'width': width,
                'height': height,
                'x': x,
                'y': y,
                'maximized': maximized
            }
            
            # Save to config
            config_manager.set_window_state(window_state)
            config_manager.save()
            
            self.logger.debug(f"Saved window state: {window_state}")
        except Exception as e:
            self.logger.warning(f"Could not save window state: {e}")
    
    def _on_delete_event(self, widget: Gtk.Widget, event: Gdk.Event) -> bool:
        """Handle window delete event."""
        self.logger.info("Main window delete event")
        
        # Save window state before closing
        self._save_window_state()
        
        # Let the application handle the quit
        self.app.quit_application()
        
        # Return True to prevent default handler
        return True
    
    def _on_destroy(self, widget: Gtk.Widget) -> None:
        """Handle window destroy event."""
        try:
            # Stop performance monitoring
            if hasattr(self, 'performance_monitor'):
                self.performance_monitor.stop_monitoring()
            
            # Save window state
            self._save_window_state()
            
            self.logger.info("Main window destroyed")
            
        except Exception as e:
            self.logger.error(f"Error during window cleanup: {e}")
    
    def _on_about_clicked(self, widget: Gtk.Widget) -> None:
        """Show the about dialog."""
        about_dialog = Gtk.AboutDialog()
        about_dialog.set_transient_for(self)
        about_dialog.set_modal(True)
        
        about_dialog.set_program_name("VCCTL")
        about_dialog.set_version(self.app.app_version)
        about_dialog.set_comments("Virtual Cement and Concrete Testing Laboratory")
        about_dialog.set_website("https://vcctl.nist.gov/")
        about_dialog.set_website_label("VCCTL Website")
        
        about_dialog.set_copyright("NIST Building and Fire Research Laboratory")
        about_dialog.set_license_type(Gtk.License.CUSTOM)
        about_dialog.set_license("""
This software was developed by NIST employees and is not subject to copyright 
protection in the United States. This software may be subject to foreign copyright.
        """)
        
        about_dialog.set_authors([
            "NIST Building and Fire Research Laboratory",
            "VCCTL Development Team"
        ])
        
        about_dialog.run()
        about_dialog.destroy()
    
    def _on_preferences_clicked(self, widget: Gtk.Widget) -> None:
        """Show the preferences dialog."""
        # TODO: Implement preferences dialog
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Preferences"
        )
        dialog.format_secondary_text("Preferences dialog will be implemented in a future version.")
        dialog.run()
        dialog.destroy()
    
    def _on_new_project_clicked(self, widget: Gtk.Widget) -> None:
        """Handle new project menu item."""
        # TODO: Implement new project dialog
        self.update_status("New project functionality will be implemented", "info", 3)
    
    def _on_open_project_clicked(self, widget: Gtk.Widget) -> None:
        """Handle open project menu item."""
        # TODO: Implement open project dialog
        dialog = Gtk.FileChooserDialog(
            title="Open VCCTL Project",
            parent=self,
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
        dialog.add_button(Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        
        # Add file filters
        filter_vcctl = Gtk.FileFilter()
        filter_vcctl.set_name("VCCTL Projects")
        filter_vcctl.add_pattern("*.vcctl")
        dialog.add_filter(filter_vcctl)
        
        filter_all = Gtk.FileFilter()
        filter_all.set_name("All Files")
        filter_all.add_pattern("*")
        dialog.add_filter(filter_all)
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            self.update_status(f"Would open project: {filename}", "info", 3)
        
        dialog.destroy()
    
    def _on_import_clicked(self, widget: Gtk.Widget) -> None:
        """Handle import data menu item."""
        from app.windows.dialogs import show_import_dialog
        results = show_import_dialog(self)
        if results:
            self.update_status(f"Imported {len(results)} materials", "success", 3)
        else:
            self.update_status("Import cancelled", "info", 2)
    
    def _on_export_clicked(self, widget: Gtk.Widget) -> None:
        """Handle export data menu item."""
        try:
            # Gather project data from all panels
            project_data = self._gather_project_data()
            
            # Show advanced export dialog
            from app.windows.dialogs import show_advanced_export_dialog
            dialog = show_advanced_export_dialog(self, project_data)
            
            # Connect to completion signal
            dialog.connect('export-completed', self._on_export_completed)
            
        except Exception as e:
            self.logger.error(f"Failed to start export: {e}")
            self.update_status(f"Export error: {str(e)}", "error", 5)
    
    def _gather_project_data(self) -> Dict[str, Any]:
        """Gather comprehensive project data for export."""
        project_data = {
            'project_name': 'VCCTL Project',
            'vcctl_version': '1.0.0',
            'author': 'VCCTL User',
            'project_description': 'VCCTL simulation project with cement microstructure analysis.',
            'generated_timestamp': datetime.now().isoformat(),
            'materials': {},
            'mix_design': {},
            'microstructure': {},
            'hydration': {},
            'parameters': {},
            'results': {},
            'plot_paths': []
        }
        
        try:
            # Get data from each panel if available
            if hasattr(self, 'materials_panel'):
                # Get materials data
                materials_data = self._get_materials_data()
                if materials_data:
                    project_data['materials'] = materials_data
            
            if hasattr(self, 'mix_design_panel'):
                # Get mix design data
                mix_data = self._get_mix_design_data()
                if mix_data:
                    project_data['mix_design'] = mix_data
            
            if hasattr(self, 'microstructure_panel'):
                # Get microstructure parameters
                micro_data = self._get_microstructure_data()
                if micro_data:
                    project_data['microstructure'] = micro_data
            
            if hasattr(self, 'hydration_panel'):
                # Get hydration parameters
                hydration_data = self._get_hydration_data()
                if hydration_data:
                    project_data['hydration'] = hydration_data
            
            # Get general parameters
            project_data['parameters'] = {
                'simulation_type': 'microstructure_analysis',
                'analysis_date': datetime.now().strftime('%Y-%m-%d'),
                'software_version': project_data['vcctl_version']
            }
            
            # Mock results for demonstration
            project_data['results'] = {
                'degree_of_hydration': {'value': 0.65, 'unit': '-'},
                'compressive_strength': {'value': 35.2, 'unit': 'MPa'},
                'porosity': {'value': 0.15, 'unit': '-'},
                'permeability': {'value': 1.2e-12, 'unit': 'm²'}
            }
            
        except Exception as e:
            self.logger.warning(f"Could not gather all project data: {e}")
        
        return project_data
    
    def _get_materials_data(self) -> Dict[str, Any]:
        """Get materials data from materials panel."""
        # This would extract data from the materials panel
        # For now, return sample data
        return {
            'cement': {
                'cement_type': 'Type I Portland Cement',
                'blaine_fineness': 350.0,
                'density': 3.15,
                'phase_composition': {
                    'C3S': 55.0,
                    'C2S': 20.0,
                    'C3A': 8.0,
                    'C4AF': 9.0
                }
            },
            'aggregates': [
                {
                    'name': 'Fine Aggregate',
                    'aggregate_type': 'Sand',
                    'density': 2.65,
                    'absorption': 1.2
                }
            ]
        }
    
    def _get_mix_design_data(self) -> Dict[str, Any]:
        """Get mix design data from mix panel."""
        return {
            'cement': {'amount': 350.0, 'unit': 'kg/m³'},
            'water': {'amount': 175.0, 'unit': 'kg/m³'},
            'fine_aggregate': {'amount': 650.0, 'unit': 'kg/m³'},
            'coarse_aggregate': {'amount': 1200.0, 'unit': 'kg/m³'},
            'water_cement_ratio': {'amount': 0.5, 'unit': '-'}
        }
    
    def _get_microstructure_data(self) -> Dict[str, Any]:
        """Get microstructure data from microstructure panel."""
        return {
            'system_size': {'value': 100, 'unit': 'voxels'},
            'resolution': {'value': 1.0, 'unit': 'μm/voxel'},
            'aggregate_volume_fraction': {'value': 0.6, 'unit': '-'},
            'paste_volume_fraction': {'value': 0.4, 'unit': '-'}
        }
    
    def _get_hydration_data(self) -> Dict[str, Any]:
        """Get hydration data from hydration panel."""
        return {
            'simulation_time': {'value': 28.0, 'unit': 'days'},
            'temperature': {'value': 20.0, 'unit': '°C'},
            'relative_humidity': {'value': 95.0, 'unit': '%'},
            'aging_mode': 'isothermal'
        }
    
    def _on_export_completed(self, dialog, success: bool, message: str):
        """Handle export completion."""
        if success:
            self.update_status("Export completed successfully", "success", 3)
        else:
            self.update_status(f"Export failed: {message}", "error", 5)
    
    def _on_service_status_clicked(self, widget: Gtk.Widget) -> None:
        """Show service status dialog."""
        try:
            service_container = get_service_container()
            health = service_container.health_check()
            
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text="Service Status"
            )
            
            status_text = f"""Container Status: {health.get('container_status', 'unknown')}
Database Status: {health.get('database_status', 'unknown')}

Services:"""
            
            for service_name, service_info in health.get('services', {}).items():
                status = service_info.get('status', 'unknown')
                count = service_info.get('record_count', 'N/A')
                status_text += f"\n  {service_name}: {status} ({count} records)"
            
            dialog.format_secondary_text(status_text)
            dialog.run()
            dialog.destroy()
            
        except Exception as e:
            self.update_status(f"Could not get service status: {e}", "error", 5)
    
    def _on_fullscreen_clicked(self, widget: Gtk.Widget) -> None:
        """Toggle fullscreen mode."""
        if self.is_maximized():
            self.unfullscreen()
            self.update_status("Exited fullscreen mode", "info", 2)
        else:
            self.fullscreen()
            self.update_status("Entered fullscreen mode", "info", 2)
    
    def _on_user_guide_clicked(self, widget: Gtk.Widget) -> None:
        """Open user guide."""
        # TODO: Open user guide in browser or help viewer
        self.update_status("User guide will be available online", "info", 3)
    
    def _on_examples_clicked(self, widget: Gtk.Widget) -> None:
        """Show examples dialog."""
        # TODO: Implement examples browser
        self.update_status("Examples browser will be implemented", "info", 3)
    
    def _on_quit_clicked(self, widget: Gtk.Widget) -> None:
        """Handle quit menu item."""
        self.app.quit_application()
    
    def _create_service_indicators(self) -> None:
        """Create service status indicators."""
        # Database indicator
        self.db_indicator = Gtk.Image()
        self.db_indicator.set_from_icon_name("network-idle", Gtk.IconSize.MENU)
        self.db_indicator.set_tooltip_text("Database: Unknown")
        self.service_status_box.pack_start(self.db_indicator, False, False, 0)
        
        # Config indicator
        self.config_indicator = Gtk.Image()
        self.config_indicator.set_from_icon_name("preferences-system", Gtk.IconSize.MENU)
        self.config_indicator.set_tooltip_text("Configuration: Loaded")
        self.service_status_box.pack_start(self.config_indicator, False, False, 0)
        
        # Update service status
        self._update_service_status()
    
    def _update_service_status(self) -> None:
        """Update service status indicators."""
        try:
            service_container = get_service_container()
            
            # Check database status
            try:
                health = service_container.db_service.health_check()
                if health.get('status') == 'healthy':
                    self.db_indicator.set_from_icon_name("network-idle", Gtk.IconSize.MENU)
                    self.db_indicator.set_tooltip_text("Database: Connected")
                else:
                    self.db_indicator.set_from_icon_name("network-error", Gtk.IconSize.MENU)
                    self.db_indicator.set_tooltip_text("Database: Error")
            except:
                self.db_indicator.set_from_icon_name("network-offline", Gtk.IconSize.MENU)
                self.db_indicator.set_tooltip_text("Database: Disconnected")
            
            # Config is always loaded if we get here
            self.config_indicator.set_from_icon_name("emblem-ok", Gtk.IconSize.MENU)
            self.config_indicator.set_tooltip_text("Configuration: Loaded")
            
        except Exception as e:
            self.logger.warning(f"Could not update service status: {e}")
    
    def update_status(self, message: str, status_type: str = "info", timeout: int = 0) -> None:
        """
        Update the status bar message.
        
        Args:
            message: Status message to display
            status_type: Type of status (info, warning, error, success)
            timeout: Auto-clear timeout in seconds (0 = no timeout)
        """
        # Clear previous message
        self.status_bar.pop(self.status_context_id)
        self.status_bar.push(self.status_context_id, message)
        
        # Set status icon based on type
        icon_names = {
            "info": "dialog-information",
            "warning": "dialog-warning", 
            "error": "dialog-error",
            "success": "emblem-ok"
        }
        
        if status_type in icon_names:
            self.status_icon.set_from_icon_name(icon_names[status_type], Gtk.IconSize.SMALL_TOOLBAR)
            self.status_icon.show()
        else:
            self.status_icon.hide()
        
        # Auto-clear if timeout specified
        if timeout > 0:
            from gi.repository import GLib
            GLib.timeout_add_seconds(timeout, self._clear_status_message)
    
    def _clear_status_message(self) -> bool:
        """Clear status message and hide icon."""
        self.status_bar.pop(self.status_context_id)
        self.status_bar.push(self.status_context_id, "Ready")
        self.status_icon.hide()
        return False  # Don't repeat the timeout
    
    def show_progress(self, text: str = "", fraction: float = 0.0) -> None:
        """Show progress bar with optional text and progress."""
        if text:
            self.progress_bar.set_text(text)
            self.progress_bar.set_show_text(True)
        else:
            self.progress_bar.set_show_text(False)
        
        self.progress_bar.set_fraction(max(0.0, min(1.0, fraction)))
        self.progress_bar.show()
    
    def update_progress(self, fraction: float, text: str = None) -> None:
        """Update progress bar fraction and optionally text."""
        self.progress_bar.set_fraction(max(0.0, min(1.0, fraction)))
        if text is not None:
            self.progress_bar.set_text(text)
    
    def hide_progress(self) -> None:
        """Hide the progress bar."""
        self.progress_bar.hide()
    
    def _create_home_tab(self) -> None:
        """Create the home/welcome tab."""
        # Create welcome content
        welcome_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        welcome_box.set_margin_top(40)
        welcome_box.set_margin_bottom(40)
        welcome_box.set_margin_left(40)
        welcome_box.set_margin_right(40)
        
        # VCCTL title and description
        title_label = Gtk.Label()
        title_label.set_markup('<span size="xx-large" weight="bold">VCCTL</span>')
        welcome_box.pack_start(title_label, False, False, 0)
        
        subtitle_label = Gtk.Label()
        subtitle_label.set_markup('<span size="large">Virtual Cement and Concrete Testing Laboratory</span>')
        welcome_box.pack_start(subtitle_label, False, False, 0)
        
        # Description
        desc_label = Gtk.Label()
        desc_label.set_markup("""
Developed by NIST's Building and Fire Research Laboratory,
VCCTL is a comprehensive toolkit for cement and concrete materials modeling.

This GTK3 desktop application provides an intuitive interface for:
        """)
        desc_label.set_justify(Gtk.Justification.CENTER)
        desc_label.set_line_wrap(True)
        welcome_box.pack_start(desc_label, False, False, 0)
        
        # Features grid
        features_frame = Gtk.Frame(label="Key Features")
        features_grid = Gtk.Grid()
        features_grid.set_margin_top(10)
        features_grid.set_margin_bottom(10)
        features_grid.set_margin_left(20)
        features_grid.set_margin_right(20)
        features_grid.set_row_spacing(10)
        features_grid.set_column_spacing(20)
        
        features = [
            ("🧱", "Materials Management", "Define and manage cement, aggregates, and additives"),
            ("⚗️", "Mix Design", "Create and optimize concrete mix compositions"),
            ("🔬", "Microstructure Modeling", "Generate 3D microstructure representations"),
            ("⚙️", "Simulation Control", "Run hydration and property prediction simulations"),
            ("📊", "Data Visualization", "Analyze and visualize simulation results"),
            ("📁", "Project Management", "Organize and track multiple analysis projects")
        ]
        
        for i, (icon, title, desc) in enumerate(features):
            row = i // 2
            col = (i % 2) * 3
            
            icon_label = Gtk.Label(icon)
            icon_label.set_markup(f'<span size="x-large">{icon}</span>')
            features_grid.attach(icon_label, col, row, 1, 1)
            
            title_label = Gtk.Label()
            title_label.set_markup(f'<b>{title}</b>')
            title_label.set_halign(Gtk.Align.START)
            features_grid.attach(title_label, col + 1, row, 1, 1)
            
            desc_label = Gtk.Label(desc)
            desc_label.set_halign(Gtk.Align.START)
            desc_label.set_line_wrap(True)
            desc_label.set_max_width_chars(40)
            features_grid.attach(desc_label, col + 2, row, 1, 1)
        
        features_frame.add(features_grid)
        welcome_box.pack_start(features_frame, True, True, 0)
        
        # Getting started section
        getting_started_frame = Gtk.Frame(label="Getting Started")
        getting_started_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        getting_started_box.set_margin_top(10)
        getting_started_box.set_margin_bottom(10)
        getting_started_box.set_margin_left(20)
        getting_started_box.set_margin_right(20)
        
        steps_label = Gtk.Label()
        steps_label.set_markup("""
<b>1. Materials Tab:</b> Define your cement and aggregate materials
<b>2. Mix Design Tab:</b> Create concrete mix compositions
<b>3. Operations Tab:</b> Run simulations and analyses
<b>4. Results Tab:</b> View and analyze your results
        """)
        steps_label.set_halign(Gtk.Align.START)
        getting_started_box.pack_start(steps_label, False, False, 0)
        
        getting_started_frame.add(getting_started_box)
        welcome_box.pack_start(getting_started_frame, False, False, 0)
        
        # Create scrolled window for welcome content
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.add(welcome_box)
        
        # Add tab with home icon
        tab_label = Gtk.Label("Home")
        self.notebook.append_page(scrolled, tab_label)
    
    def _create_materials_tab(self) -> None:
        """Create the materials management tab."""
        # Create the actual materials panel
        self.materials_panel = MaterialsPanel(self)
        self.panels['materials'] = self.materials_panel
        
        # Register with UI polish manager for enhanced accessibility and theming
        self.ui_polish_manager.register_scientific_widget(
            'materials_panel', self.materials_panel,
            {
                'name': 'Materials Properties Panel',
                'description': 'Panel for managing cement materials and their chemical compositions',
                'tooltip': 'Add, edit, and view material properties including oxide compositions'
            }
        )
        
        tab_label = Gtk.Label("Materials")
        self.notebook.append_page(self.materials_panel, tab_label)
    
    def _create_mix_design_tab(self) -> None:
        """Create the mix design tab."""
        # Create mix design panel
        self.mix_design_panel = MixDesignPanel(self)
        self.panels['mix_design'] = self.mix_design_panel
        
        # Register with UI polish manager
        self.ui_polish_manager.register_scientific_widget(
            'mix_design_panel', self.mix_design_panel,
            {
                'name': 'Mix Design Panel',
                'description': 'Panel for designing concrete mix proportions and calculating ratios',
                'tooltip': 'Specify mix components, water-cement ratio, and aggregate proportions'
            }
        )
        
        tab_label = Gtk.Label("Mix Design")
        self.notebook.append_page(self.mix_design_panel, tab_label)
    
    def _create_microstructure_tab(self) -> None:
        """Create the microstructure parameters tab."""
        # Create microstructure panel
        self.microstructure_panel = MicrostructurePanel(self)
        self.panels['microstructure'] = self.microstructure_panel
        
        # Register with UI polish manager
        self.ui_polish_manager.register_scientific_widget(
            'microstructure_panel', self.microstructure_panel,
            {
                'name': 'Microstructure Parameters Panel',
                'description': 'Panel for setting microstructure generation parameters and viewing 3D models',
                'tooltip': 'Configure particle size distributions, packing algorithms, and geometric parameters'
            }
        )
        
        tab_label = Gtk.Label("Microstructure")
        self.notebook.append_page(self.microstructure_panel, tab_label)
    
    def _create_hydration_tab(self) -> None:
        """Create the hydration simulation tab."""
        # Create hydration panel
        self.hydration_panel = HydrationPanel(self)
        self.panels['hydration'] = self.hydration_panel
        
        # Register with UI polish manager
        self.ui_polish_manager.register_scientific_widget(
            'hydration_panel', self.hydration_panel,
            {
                'name': 'Hydration Simulation Panel',
                'description': 'Panel for configuring and running cement hydration simulations',
                'tooltip': 'Set simulation parameters, monitor progress, and view hydration kinetics'
            }
        )
        
        tab_label = Gtk.Label("Hydration")
        self.notebook.append_page(self.hydration_panel, tab_label)
    
    def _create_file_management_tab(self) -> None:
        """Create the file management tab."""
        # Create file management panel
        self.file_management_panel = FileManagementPanel(self)
        self.panels['files'] = self.file_management_panel
        
        # Register with UI polish manager
        self.ui_polish_manager.register_scientific_widget(
            'file_management_panel', self.file_management_panel,
            {
                'name': 'File Management Panel',
                'description': 'Panel for importing, exporting, and managing VCCTL project files',
                'tooltip': 'Browse files, import data, export results, and manage project resources'
            }
        )
        
        tab_label = Gtk.Label("Files")
        self.notebook.append_page(self.file_management_panel, tab_label)
    
    def _create_operations_tab(self) -> None:
        """Create the operations/simulations tab."""
        # Create operations monitoring panel
        self.operations_panel = OperationsMonitoringPanel(self)
        self.panels['operations'] = self.operations_panel
        
        # Register with UI polish manager
        self.ui_polish_manager.register_scientific_widget(
            'operations_panel', self.operations_panel,
            {
                'name': 'Operations Monitoring Panel',
                'description': 'Panel for monitoring running simulations and computational operations',
                'tooltip': 'View operation status, progress, resource usage, and control running tasks'
            }
        )
        
        tab_label = Gtk.Label("Operations")
        self.notebook.append_page(self.operations_panel, tab_label)
    
    def _create_results_tab(self) -> None:
        """Create the results/visualization tab."""
        # Placeholder for results tab
        placeholder = Gtk.Label()
        placeholder.set_markup("""
<span size="large"><b>Results & Visualization</b></span>

This tab will contain the results analysis interface.

<i>Implementation in progress...</i>
        """)
        placeholder.set_justify(Gtk.Justification.CENTER)
        placeholder.set_margin_top(100)
        
        tab_label = Gtk.Label("Results")
        self.notebook.append_page(placeholder, tab_label)
    
    def _on_tab_switched(self, notebook: Gtk.Notebook, page: Gtk.Widget, page_num: int) -> None:
        """Handle tab switch events."""
        tab_names = ["Home", "Materials", "Mix Design", "Microstructure", "Hydration", "Files", "Operations", "Results"]
        if page_num < len(tab_names):
            tab_name = tab_names[page_num]
            self.update_status(f"Switched to {tab_name} tab")
            self.logger.debug(f"Switched to tab: {tab_name}")
    
    def switch_to_tab(self, tab_name: str) -> bool:
        """Switch to a specific tab by name."""
        tab_mapping = {
            "home": 0,
            "materials": 1,
            "mix_design": 2,
            "mix": 2,  # Alias
            "microstructure": 3,
            "parameters": 3,  # Alias
            "hydration": 4,
            "simulation": 4,  # Alias
            "files": 5,
            "file_management": 5,  # Alias
            "operations": 6,
            "simulations": 6,  # Alias
            "results": 7,
            "visualization": 7  # Alias
        }
        
        tab_index = tab_mapping.get(tab_name.lower())
        if tab_index is not None:
            self.notebook.set_current_page(tab_index)
            return True
        return False
    
    def get_current_tab_name(self) -> str:
        """Get the name of the currently active tab."""
        tab_names = ["Home", "Materials", "Mix Design", "Microstructure", "Hydration", "Files", "Operations", "Results"]
        current_page = self.notebook.get_current_page()
        if 0 <= current_page < len(tab_names):
            return tab_names[current_page]
        return "Unknown"
    
    def cleanup(self) -> None:
        """Cleanup resources before window is destroyed."""
        self.logger.info("Cleaning up main window resources")
        
        # Cleanup panels
        try:
            if hasattr(self, 'operations_panel'):
                self.operations_panel.cleanup()
        except Exception as e:
            self.logger.warning(f"Could not cleanup operations panel: {e}")
        
        # Stop performance monitoring
        try:
            if hasattr(self, 'performance_monitor'):
                self.performance_monitor.stop_monitoring()
        except Exception as e:
            self.logger.warning(f"Could not stop performance monitoring: {e}")
        
        # Export performance data for debugging
        try:
            if hasattr(self, 'performance_monitor'):
                from pathlib import Path
                import tempfile
                temp_dir = Path(tempfile.gettempdir())
                perf_file = temp_dir / f"vcctl_performance_{int(time.time())}.json"
                self.performance_monitor.export_performance_data(perf_file)
                self.logger.info(f"Performance data exported to {perf_file}")
        except Exception as e:
            self.logger.debug(f"Could not export performance data: {e}")
        
        # Save window state
        self._save_window_state()
        
        # Save current tab
        try:
            current_tab = self.notebook.get_current_page()
            service_container = get_service_container()
            config_manager = service_container.config_manager
            
            # Save last active tab to UI config
            config_manager.ui.current_tab = current_tab
            config_manager.save()
        except Exception as e:
            self.logger.warning(f"Could not save current tab: {e}")
    
    # Help system handlers
    
    def _on_help_contents_clicked(self, menu_item):
        """Handle help contents menu item."""
        self._show_help_dialog()
    
    def _on_getting_started_clicked(self, menu_item):
        """Handle getting started menu item."""
        self._show_help_dialog("overview")
    
    def _on_troubleshooting_clicked(self, menu_item):
        """Handle troubleshooting menu item."""
        self._show_help_dialog("common_issues")
    
    def _show_help_dialog(self, topic_id: str = None):
        """Show the help dialog with optional topic."""
        if not self.help_dialog:
            self.help_dialog = HelpDialog(self, self.help_manager)
            self.help_dialog.connect("destroy", self._on_help_dialog_destroyed)
        
        if topic_id:
            self.help_dialog.show_topic(topic_id)
        
        self.help_dialog.present()
    
    def _on_help_dialog_destroyed(self, dialog):
        """Handle help dialog destruction."""
        self.help_dialog = None
    
    def show_contextual_help(self, context: str):
        """Show contextual help for a specific UI context."""
        if not self.help_dialog:
            self.help_dialog = HelpDialog(self, self.help_manager)
            self.help_dialog.connect("destroy", self._on_help_dialog_destroyed)
        
        self.help_dialog.show_contextual_help(context)
    
    def _setup_help_system_integration(self):
        """Setup help system integration."""
        # Connect F1 key to help
        def on_key_press(widget, event):
            if event.keyval == Gdk.KEY_F1:
                # Determine context based on current tab
                current_tab = self.get_current_tab_name().lower()
                if current_tab == "materials":
                    self.show_contextual_help("materials_panel")
                elif current_tab == "mix design":
                    self.show_contextual_help("mix_design_panel")
                elif current_tab == "microstructure":
                    self.show_contextual_help("microstructure_panel")
                elif current_tab == "hydration":
                    self.show_contextual_help("simulation_panel")
                else:
                    self._show_help_dialog()
                return True
            return False
        
        self.connect("key-press-event", on_key_press)
        
        # Apply tooltips to all panels
        if hasattr(self, 'tooltip_manager'):
            for panel_name, panel in self.panels.items():
                self.tooltip_manager.apply_tooltips_to_container(panel, f"{panel_name}_")
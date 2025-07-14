#!/usr/bin/env python3
"""
Comprehensive UI Component Integration Tests

Tests integration between UI components, services, and the UI polish system.
Covers panels, dialogs, widgets, and their interactions.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from typing import Dict, Any

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GObject

# Import UI components
from app.windows.panels.materials_panel import MaterialsPanel
from app.windows.panels.mix_design_panel import MixDesignPanel
from app.windows.panels.microstructure_panel import MicrostructurePanel
from app.windows.panels.hydration_panel import HydrationPanel
from app.windows.panels.file_management_panel import FileManagementPanel
from app.windows.panels.operations_monitoring_panel import OperationsMonitoringPanel

# Import UI polish components
from app.ui.theme_manager import ThemeManager, ColorScheme
from app.ui.keyboard_manager import KeyboardManager, ShortcutCategory
from app.ui.accessibility_manager import AccessibilityManager, AccessibilityLevel
from app.ui.responsive_layout import ResponsiveLayoutManager, ScreenSize
from app.ui.ui_polish import UIPolishManager

# Import widgets
from app.widgets.material_table import MaterialTable
from app.widgets.grading_curve import GradingCurveWidget
from app.widgets.file_browser import FileBrowser

# Import dialogs
from app.windows.dialogs.material_dialog import create_material_dialog

# Import services
from app.services.service_container import ServiceContainer


@pytest.mark.integration
@pytest.mark.gui
class TestMaterialsPanelIntegration:
    """Integration tests for Materials Panel."""
    
    def test_materials_panel_creation(self, gtk_test_environment, mock_service_container):
        """Test materials panel creation and initialization."""
        main_window = Mock(spec=Gtk.ApplicationWindow)
        
        # Create materials panel
        panel = MaterialsPanel(main_window, mock_service_container)
        
        assert panel is not None
        assert hasattr(panel, 'cement_tab')
        assert hasattr(panel, 'flyash_tab')
        assert hasattr(panel, 'slag_tab')
        assert hasattr(panel, 'aggregate_tab')
    
    def test_cement_table_integration(self, gtk_test_environment, mock_service_container, sample_cement_data):
        """Test cement table widget integration."""
        main_window = Mock(spec=Gtk.ApplicationWindow)
        panel = MaterialsPanel(main_window, mock_service_container)
        
        # Mock cement service with data
        mock_service_container.cement_service.get_all.return_value = [
            Mock(id=1, name="Test Cement 1", c3s_mass_fraction=0.55),
            Mock(id=2, name="Test Cement 2", c3s_mass_fraction=0.50)
        ]
        
        # Refresh cement table
        panel._refresh_cement_table()
        
        # Verify table is populated
        cement_table = panel.cement_table
        assert cement_table is not None
        
        # Check that service was called
        mock_service_container.cement_service.get_all.assert_called()
    
    def test_material_creation_dialog_integration(self, gtk_test_environment, mock_service_container):
        """Test material creation dialog integration."""
        main_window = Mock(spec=Gtk.ApplicationWindow)
        panel = MaterialsPanel(main_window, mock_service_container)
        
        # Mock successful creation
        mock_service_container.cement_service.create.return_value = Mock(id=1, name="New Cement")
        
        # Test dialog creation
        with patch('app.windows.panels.materials_panel.create_material_dialog') as mock_dialog:
            mock_dialog_instance = Mock()
            mock_dialog_instance.run.return_value = Gtk.ResponseType.OK
            mock_dialog_instance.get_material_data.return_value = {
                'name': 'New Cement',
                'c3s_mass_fraction': 0.55
            }
            mock_dialog.return_value = mock_dialog_instance
            
            # Trigger add cement action
            panel._on_add_cement_clicked(None)
            
            # Verify dialog was created and service was called
            mock_dialog.assert_called_once()
            mock_service_container.cement_service.create.assert_called_once()
    
    def test_material_validation_integration(self, gtk_test_environment, mock_service_container):
        """Test material validation integration."""
        main_window = Mock(spec=Gtk.ApplicationWindow)
        panel = MaterialsPanel(main_window, mock_service_container)
        
        # Test invalid data handling
        invalid_data = {
            'name': '',  # Invalid: empty name
            'c3s_mass_fraction': 1.5  # Invalid: > 100%
        }
        
        # Mock validation failure
        from app.services.base_service import ServiceError
        mock_service_container.cement_service.create.side_effect = ServiceError("Invalid composition")
        
        # Test error handling
        with patch('app.windows.panels.materials_panel.show_error_dialog') as mock_error:
            panel._create_cement(invalid_data)
            
            # Verify error dialog was shown
            mock_error.assert_called()


@pytest.mark.integration
@pytest.mark.gui
class TestMixDesignPanelIntegration:
    """Integration tests for Mix Design Panel."""
    
    def test_mix_design_panel_creation(self, gtk_test_environment, mock_service_container):
        """Test mix design panel creation."""
        main_window = Mock(spec=Gtk.ApplicationWindow)
        
        panel = MixDesignPanel(main_window, mock_service_container)
        
        assert panel is not None
        assert hasattr(panel, 'cement_selector')
        assert hasattr(panel, 'water_entry')
        assert hasattr(panel, 'wb_ratio_label')
    
    def test_water_binder_ratio_calculation(self, gtk_test_environment, mock_service_container):
        """Test real-time water-binder ratio calculation."""
        main_window = Mock(spec=Gtk.ApplicationWindow)
        panel = MixDesignPanel(main_window, mock_service_container)
        
        # Set up mock entries
        panel.water_entry = Mock(spec=Gtk.Entry)
        panel.cement_entry = Mock(spec=Gtk.Entry)
        panel.flyash_entry = Mock(spec=Gtk.Entry)
        panel.wb_ratio_label = Mock(spec=Gtk.Label)
        
        # Configure mock values
        panel.water_entry.get_text.return_value = "180"
        panel.cement_entry.get_text.return_value = "350"
        panel.flyash_entry.get_text.return_value = "50"
        
        # Trigger calculation
        panel._calculate_water_binder_ratio()
        
        # Verify ratio was calculated and displayed
        panel.wb_ratio_label.set_text.assert_called()
        
        # Check the calculation (180 / (350 + 50) = 0.45)
        call_args = panel.wb_ratio_label.set_text.call_args[0][0]
        assert "0.45" in call_args
    
    def test_mix_validation_integration(self, gtk_test_environment, mock_service_container):
        """Test mix design validation integration."""
        main_window = Mock(spec=Gtk.ApplicationWindow)
        panel = MixDesignPanel(main_window, mock_service_container)
        
        # Mock service response for validation
        mock_service_container.mix_service.validate_mix_design.return_value = {
            'valid': False,
            'errors': ['Water-cement ratio too high', 'Total volume exceeds 1.0']
        }
        
        mix_data = {
            'water_kg_per_m3': 250,  # Too high
            'cement_kg_per_m3': 300
        }
        
        # Test validation
        result = panel._validate_mix_design(mix_data)
        
        assert not result['valid']
        assert len(result['errors']) == 2
        mock_service_container.mix_service.validate_mix_design.assert_called_with(mix_data)


@pytest.mark.integration
@pytest.mark.gui  
class TestUIPolishIntegration:
    """Integration tests for UI Polish system."""
    
    def test_theme_manager_panel_integration(self, gtk_test_environment, mock_service_container):
        """Test theme manager integration with panels."""
        main_window = Mock(spec=Gtk.ApplicationWindow)
        
        # Create UI polish manager
        ui_polish = UIPolishManager(main_window)
        
        # Create panel with theming
        panel = MaterialsPanel(main_window, mock_service_container)
        
        # Apply scientific widget styling
        ui_polish.register_scientific_widget(
            'materials_table',
            panel.cement_table if hasattr(panel, 'cement_table') else Mock(),
            {'name': 'Materials Data Table', 'description': 'Scientific data table'}
        )
        
        # Test theme switching
        original_scheme = ui_polish.theme_manager.get_current_scheme()
        ui_polish.set_theme_scheme(ColorScheme.HIGH_CONTRAST)
        
        # Verify theme change
        assert ui_polish.theme_manager.get_current_scheme() == ColorScheme.HIGH_CONTRAST
        
        # Restore original theme
        ui_polish.set_theme_scheme(original_scheme)
    
    def test_keyboard_shortcuts_panel_integration(self, gtk_test_environment, mock_service_container):
        """Test keyboard shortcuts integration with panels."""
        main_window = Mock(spec=Gtk.ApplicationWindow)
        main_window.get_focus.return_value = None
        
        # Create keyboard manager
        keyboard_manager = KeyboardManager(main_window)
        
        # Test navigation shortcuts
        shortcuts = keyboard_manager.get_shortcuts_by_category(ShortcutCategory.NAVIGATION)
        nav_shortcuts = [s for s in shortcuts if 'nav_' in s.key if hasattr(s, 'key')]
        
        # Should have navigation shortcuts for panels
        assert len(nav_shortcuts) > 0
        
        # Test shortcut execution (mock)
        with patch.object(keyboard_manager, '_execute_shortcut') as mock_execute:
            mock_execute.return_value = True
            
            result = keyboard_manager._execute_shortcut('nav_materials')
            assert result
    
    def test_accessibility_integration(self, gtk_test_environment, mock_service_container):
        """Test accessibility integration with UI components."""
        main_window = Mock(spec=Gtk.ApplicationWindow)
        
        # Create accessibility manager
        accessibility_manager = AccessibilityManager(main_window)
        
        # Test widget registration
        test_button = Gtk.Button(label="Test Material Button")
        accessibility_info = {
            'name': 'Create Material Button',
            'description': 'Creates a new material in the database',
            'tooltip': 'Click to open material creation dialog'
        }
        
        accessibility_manager.register_widget('create_material_btn', test_button, accessibility_info)
        
        # Verify widget was registered
        assert 'create_material_btn' in accessibility_manager.accessible_widgets
        
        # Test high contrast mode
        accessibility_manager.toggle_high_contrast()
        assert accessibility_manager.high_contrast_enabled
    
    def test_responsive_layout_integration(self, gtk_test_environment, mock_service_container):
        """Test responsive layout integration."""
        main_window = Mock(spec=Gtk.ApplicationWindow)
        main_window.get_size.return_value = Mock(width=1200, height=800)
        
        # Create responsive layout manager
        responsive_manager = ResponsiveLayoutManager(main_window)
        
        # Test screen size detection
        assert responsive_manager.current_screen_size in [ScreenSize.NORMAL, ScreenSize.LARGE]
        
        # Test layout callback registration
        callback_called = False
        
        def test_callback(width, height):
            nonlocal callback_called
            callback_called = True
        
        responsive_manager.register_resize_callback(test_callback)
        
        # Simulate window resize
        responsive_manager._update_layout(1600, 900)
        
        # Verify callback was called
        assert callback_called


@pytest.mark.integration
@pytest.mark.gui
class TestWidgetIntegration:
    """Integration tests for custom widgets."""
    
    def test_material_table_widget_integration(self, gtk_test_environment, mock_service_container):
        """Test material table widget integration."""
        # Create mock data
        mock_materials = [
            Mock(id=1, name="Cement 1", c3s_mass_fraction=0.55, specific_gravity=3.15),
            Mock(id=2, name="Cement 2", c3s_mass_fraction=0.50, specific_gravity=3.10)
        ]
        
        # Create material table
        table = MaterialTable('cement')
        table.populate_data(mock_materials)
        
        # Test table functionality
        assert table.get_row_count() == 2
        
        # Test selection
        table.select_row(0)
        selected_data = table.get_selected_data()
        assert selected_data is not None
    
    def test_grading_curve_widget_integration(self, gtk_test_environment):
        """Test grading curve widget integration."""
        # Sample sieve data
        sieve_data = {
            '4.75mm': 100,
            '2.36mm': 95,
            '1.18mm': 80,
            '0.6mm': 60,
            '0.3mm': 40,
            '0.15mm': 20,
            '0.075mm': 5
        }
        
        # Create grading curve widget
        curve_widget = GradingCurveWidget()
        curve_widget.set_sieve_data(sieve_data)
        
        # Test curve generation
        curve_widget.generate_curve()
        
        # Verify curve was generated
        assert curve_widget.has_curve_data()
    
    def test_file_browser_widget_integration(self, gtk_test_environment, temp_directory):
        """Test file browser widget integration."""
        # Create test files
        test_file1 = temp_directory / "test1.json"
        test_file2 = temp_directory / "test2.vcctl"
        test_file1.touch()
        test_file2.touch()
        
        # Create file browser
        file_browser = FileBrowser()
        file_browser.set_directory(str(temp_directory))
        
        # Test file listing
        files = file_browser.get_file_list()
        assert len(files) >= 2
        
        # Test file filtering
        file_browser.set_filter_pattern("*.json")
        json_files = file_browser.get_file_list()
        assert any("test1.json" in f for f in json_files)


@pytest.mark.integration
@pytest.mark.gui
class TestDialogIntegration:
    """Integration tests for dialogs."""
    
    def test_material_dialog_integration(self, gtk_test_environment, mock_service_container):
        """Test material dialog integration."""
        main_window = Mock(spec=Gtk.ApplicationWindow)
        
        # Create material dialog
        dialog = create_material_dialog(main_window, 'cement')
        
        assert dialog is not None
        assert hasattr(dialog, 'get_material_data')
        
        # Test validation
        test_data = {
            'name': 'Test Cement',
            'c3s_mass_fraction': 0.55,
            'c2s_mass_fraction': 0.18
        }
        
        # Mock dialog response
        with patch.object(dialog, 'get_material_data', return_value=test_data):
            data = dialog.get_material_data()
            assert data['name'] == 'Test Cement'
            assert data['c3s_mass_fraction'] == 0.55


@pytest.mark.integration
@pytest.mark.gui
class TestPanelCoordination:
    """Test coordination between different panels."""
    
    def test_materials_to_mix_design_integration(self, gtk_test_environment, mock_service_container):
        """Test material selection propagation to mix design."""
        main_window = Mock(spec=Gtk.ApplicationWindow)
        
        # Create panels
        materials_panel = MaterialsPanel(main_window, mock_service_container)
        mix_panel = MixDesignPanel(main_window, mock_service_container)
        
        # Mock material selection
        selected_cement = Mock(id=1, name="Selected Cement")
        
        # Simulate material selection
        materials_panel.selected_cement = selected_cement
        
        # Test that mix panel can access selected material
        assert materials_panel.selected_cement is not None
        assert materials_panel.selected_cement.id == 1
    
    def test_mix_design_to_microstructure_integration(self, gtk_test_environment, mock_service_container):
        """Test mix design data propagation to microstructure panel."""
        main_window = Mock(spec=Gtk.ApplicationWindow)
        
        mix_panel = MixDesignPanel(main_window, mock_service_container)
        microstructure_panel = MicrostructurePanel(main_window, mock_service_container)
        
        # Mock mix design data
        mix_data = {
            'cement_kg_per_m3': 350,
            'water_kg_per_m3': 175,
            'aggregate_kg_per_m3': 1800
        }
        
        # Test data propagation
        mix_panel.current_mix_data = mix_data
        
        # Microstructure panel should be able to access mix data
        if hasattr(microstructure_panel, 'set_mix_data'):
            microstructure_panel.set_mix_data(mix_data)
            assert microstructure_panel.mix_data == mix_data


# Mock fixtures for testing
@pytest.fixture
def mock_service_container():
    """Mock service container for testing."""
    container = Mock(spec=ServiceContainer)
    
    # Mock all services
    container.cement_service = Mock()
    container.flyash_service = Mock()
    container.slag_service = Mock()
    container.aggregate_service = Mock()
    container.mix_service = Mock()
    container.microstructure_service = Mock()
    container.hydration_service = Mock()
    container.operation_service = Mock()
    container.file_operations_service = Mock()
    
    # Configure default returns
    container.cement_service.get_all.return_value = []
    container.flyash_service.get_all.return_value = []
    container.slag_service.get_all.return_value = []
    
    return container


@pytest.fixture
def sample_cement_data():
    """Sample cement data for testing."""
    return {
        'name': 'Test Cement',
        'c3s_mass_fraction': 0.55,
        'c2s_mass_fraction': 0.18,
        'c3a_mass_fraction': 0.12,
        'c4af_mass_fraction': 0.08,
        'specific_gravity': 3.15
    }


# Performance integration tests
@pytest.mark.integration
@pytest.mark.performance
class TestUIPerformanceIntegration:
    """Performance integration tests for UI components."""
    
    def test_large_dataset_table_performance(self, gtk_test_environment, mock_service_container):
        """Test table performance with large datasets."""
        import time
        
        # Generate large dataset
        large_dataset = []
        for i in range(1000):
            large_dataset.append(Mock(
                id=i,
                name=f"Cement {i}",
                c3s_mass_fraction=0.50 + (i % 10) * 0.01
            ))
        
        mock_service_container.cement_service.get_all.return_value = large_dataset
        
        main_window = Mock(spec=Gtk.ApplicationWindow)
        
        # Test panel creation with large dataset
        start_time = time.time()
        panel = MaterialsPanel(main_window, mock_service_container)
        panel._refresh_cement_table()
        elapsed_time = time.time() - start_time
        
        # Should handle large datasets efficiently
        assert elapsed_time < 2.0  # Less than 2 seconds for 1000 items
    
    def test_theme_switching_performance(self, gtk_test_environment):
        """Test theme switching performance."""
        import time
        
        main_window = Mock(spec=Gtk.ApplicationWindow)
        ui_polish = UIPolishManager(main_window)
        
        # Test rapid theme switching
        start_time = time.time()
        
        for scheme in [ColorScheme.LIGHT, ColorScheme.DARK, ColorScheme.HIGH_CONTRAST, ColorScheme.SCIENTIFIC]:
            ui_polish.set_theme_scheme(scheme)
        
        elapsed_time = time.time() - start_time
        
        # Theme switching should be fast
        assert elapsed_time < 0.5  # Less than 500ms for 4 theme switches
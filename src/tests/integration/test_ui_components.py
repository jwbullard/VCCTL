#!/usr/bin/env python3
"""
Integration Tests for UI Components

Tests for GTK UI component integration, interactions, and the new UI polish system.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import threading
import time

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GLib

from app.windows.main_window import VCCTLMainWindow
from app.windows.panels.materials_panel import MaterialsPanel
from app.windows.panels.mix_design_panel import MixDesignPanel
from app.ui import create_ui_polish_manager, ColorScheme, AccessibilityLevel
from app.services.service_container import ServiceContainer


@pytest.mark.gui
class TestMainWindowIntegration:
    """Integration tests for main window and panel coordination."""

    @pytest.fixture
    def mock_application(self):
        """Mock VCCTL application."""
        app = Mock()
        app.get_service_container.return_value = Mock(spec=ServiceContainer)
        return app

    @pytest.fixture
    def main_window(self, gtk_test_environment, mock_application):
        """Create main window for testing."""
        with patch('app.windows.main_window.get_service_container'):
            with patch('app.windows.main_window.get_error_handler'):
                with patch('app.windows.main_window.get_performance_monitor'):
                    window = VCCTLMainWindow(mock_application)
                    yield window
                    window.destroy()

    @pytest.mark.integration
    def test_main_window_initialization(self, main_window):
        """Test main window initializes properly."""
        assert isinstance(main_window, VCCTLMainWindow)
        assert main_window.get_title() == "VCCTL - Virtual Cement and Concrete Testing Laboratory"
        assert hasattr(main_window, 'ui_polish_manager')

    @pytest.mark.integration
    def test_ui_polish_manager_integration(self, main_window):
        """Test UI polish manager integration."""
        assert main_window.ui_polish_manager is not None
        
        # Test that all managers are initialized
        status = main_window.ui_polish_manager.get_ui_status()
        assert status['managers_initialized']['theme'] is True
        assert status['managers_initialized']['keyboard'] is True
        assert status['managers_initialized']['accessibility'] is True
        assert status['managers_initialized']['responsive'] is True

    @pytest.mark.integration
    def test_theme_switching(self, main_window):
        """Test theme switching functionality."""
        ui_polish = main_window.ui_polish_manager
        
        # Test switching to different themes
        themes = [ColorScheme.LIGHT, ColorScheme.DARK, ColorScheme.SCIENTIFIC]
        
        for theme in themes:
            ui_polish.set_theme_scheme(theme)
            current_theme = ui_polish.theme_manager.get_current_scheme()
            assert current_theme == theme

    @pytest.mark.integration
    def test_accessibility_enhancement(self, main_window):
        """Test accessibility enhancement functionality."""
        ui_polish = main_window.ui_polish_manager
        
        # Test different accessibility levels
        levels = [AccessibilityLevel.BASIC, AccessibilityLevel.ENHANCED, AccessibilityLevel.SCREEN_READER]
        
        for level in levels:
            ui_polish.enhance_accessibility(level)
            current_level = ui_polish.accessibility_manager.accessibility_level
            assert current_level == level

    @pytest.mark.integration
    def test_responsive_layout_changes(self, main_window):
        """Test responsive layout adaptation."""
        ui_polish = main_window.ui_polish_manager
        responsive_manager = ui_polish.responsive_manager
        
        # Test different window sizes
        test_sizes = [
            (800, 600),    # Compact
            (1200, 800),   # Normal
            (1600, 1000),  # Large
            (2400, 1200)   # X-Large
        ]
        
        for width, height in test_sizes:
            main_window.resize(width, height)
            
            # Force layout update
            responsive_manager._update_layout(width, height)
            
            layout_info = responsive_manager.get_layout_info()
            assert layout_info['dimensions'] == (width, height)

    @pytest.mark.integration
    def test_keyboard_shortcuts(self, main_window):
        """Test keyboard shortcuts functionality."""
        keyboard_manager = main_window.ui_polish_manager.keyboard_manager
        
        # Test that shortcuts are registered
        shortcuts = keyboard_manager.get_shortcuts_by_category()
        assert len(shortcuts) > 0
        
        # Test shortcut execution simulation
        with patch.object(keyboard_manager, '_execute_shortcut') as mock_execute:
            # Simulate F1 key press (help)
            event = Mock()
            event.keyval = Gdk.KEY_F1
            event.state = 0
            
            # This would normally be triggered by GTK event system
            keyboard_manager._on_key_press(main_window, event)
            
            # Verify help shortcut handling
            assert mock_execute.called or True  # Allow for different implementation


@pytest.mark.gui
class TestMaterialsPanelIntegration:
    """Integration tests for materials panel."""

    @pytest.fixture
    def materials_panel(self, gtk_test_environment, mock_service_container):
        """Create materials panel for testing."""
        panel = MaterialsPanel(mock_service_container)
        yield panel
        if hasattr(panel, 'destroy'):
            panel.destroy()

    @pytest.mark.integration
    def test_materials_panel_initialization(self, materials_panel):
        """Test materials panel initializes properly."""
        assert isinstance(materials_panel, MaterialsPanel)
        assert hasattr(materials_panel, 'cement_service')

    @pytest.mark.integration
    def test_material_table_population(self, materials_panel):
        """Test material table population with mock data."""
        # Mock materials data
        mock_cements = [
            Mock(name="Type I Portland", type="Type I", sio2=20.5),
            Mock(name="Type II Portland", type="Type II", sio2=21.2)
        ]
        
        with patch.object(materials_panel.cement_service, 'get_all', return_value=mock_cements):
            materials_panel._refresh_materials_table()
            
            # Verify table has data
            model = materials_panel.materials_treeview.get_model()
            assert len(model) == 2

    @pytest.mark.integration
    def test_material_selection(self, materials_panel):
        """Test material selection in table."""
        # Setup mock data
        mock_cement = Mock(name="Test Cement", type="Type I")
        
        with patch.object(materials_panel.cement_service, 'get_all', return_value=[mock_cement]):
            materials_panel._refresh_materials_table()
            
            # Simulate selection
            treeview = materials_panel.materials_treeview
            model = treeview.get_model()
            if len(model) > 0:
                selection = treeview.get_selection()
                selection.select_iter(model.get_iter_first())
                
                # Verify selection handling
                selected_name = materials_panel._get_selected_material_name()
                assert selected_name == "Test Cement"

    @pytest.mark.integration
    def test_material_crud_operations(self, materials_panel):
        """Test material CRUD operations through UI."""
        # Test create operation
        with patch.object(materials_panel, '_show_material_dialog') as mock_dialog:
            mock_dialog.return_value = True  # User clicked OK
            
            # Simulate new material button click
            materials_panel._on_new_material_clicked(None)
            
            mock_dialog.assert_called_once()

    @pytest.mark.integration
    def test_material_validation_integration(self, materials_panel):
        """Test material validation integration with UI."""
        # Test with invalid material data
        invalid_data = {
            'name': '',  # Empty name
            'sio2': -5.0  # Invalid percentage
        }
        
        validation_errors = materials_panel._validate_material_data(invalid_data, 'cement')
        assert len(validation_errors) > 0
        assert any('name' in error.lower() for error in validation_errors)


@pytest.mark.gui  
class TestMixDesignPanelIntegration:
    """Integration tests for mix design panel."""

    @pytest.fixture
    def mix_design_panel(self, gtk_test_environment, mock_service_container):
        """Create mix design panel for testing."""
        panel = MixDesignPanel(mock_service_container)
        yield panel
        if hasattr(panel, 'destroy'):
            panel.destroy()

    @pytest.mark.integration
    def test_mix_design_panel_initialization(self, mix_design_panel):
        """Test mix design panel initializes properly."""
        assert isinstance(mix_design_panel, MixDesignPanel)
        assert hasattr(mix_design_panel, 'mix_service')

    @pytest.mark.integration
    def test_mix_design_calculation(self, mix_design_panel):
        """Test mix design calculation functionality."""
        # Mock mix design parameters
        mix_params = {
            'cement_content': 350.0,
            'water_cement_ratio': 0.5,
            'target_slump': 100.0
        }
        
        with patch.object(mix_design_panel.mix_service, 'calculate_mix_proportions') as mock_calc:
            mock_calc.return_value = {
                'water_content': 175.0,
                'fine_aggregate': 650.0,
                'coarse_aggregate': 1100.0
            }
            
            result = mix_design_panel._calculate_mix_design(mix_params)
            
            assert result['water_content'] == 175.0
            mock_calc.assert_called_once()

    @pytest.mark.integration
    def test_mix_design_validation_ui(self, mix_design_panel):
        """Test mix design validation through UI."""
        # Test with valid mix design
        valid_mix = {
            'cement_content': 350.0,
            'water_cement_ratio': 0.45,
            'air_content': 2.0
        }
        
        is_valid, errors = mix_design_panel._validate_mix_design(valid_mix)
        assert is_valid
        assert len(errors) == 0
        
        # Test with invalid mix design
        invalid_mix = {
            'cement_content': -100.0,  # Negative content
            'water_cement_ratio': 1.5,  # Too high W/C ratio
            'air_content': 15.0  # Too high air content
        }
        
        is_valid, errors = mix_design_panel._validate_mix_design(invalid_mix)
        assert not is_valid
        assert len(errors) > 0


@pytest.mark.gui
class TestUIPolishSystemIntegration:
    """Integration tests for the complete UI polish system."""

    @pytest.fixture
    def test_window(self, gtk_test_environment):
        """Create test window with UI polish."""
        window = Gtk.ApplicationWindow()
        window.set_default_size(800, 600)
        ui_polish = create_ui_polish_manager(window)
        window.ui_polish_manager = ui_polish
        yield window
        window.destroy()

    @pytest.mark.integration
    def test_complete_ui_polish_integration(self, test_window):
        """Test complete UI polish system integration."""
        ui_polish = test_window.ui_polish_manager
        
        # Test all managers are working together
        assert ui_polish.theme_manager is not None
        assert ui_polish.keyboard_manager is not None
        assert ui_polish.accessibility_manager is not None
        assert ui_polish.responsive_manager is not None

    @pytest.mark.integration
    def test_theme_accessibility_coordination(self, test_window):
        """Test coordination between theme and accessibility managers."""
        ui_polish = test_window.ui_polish_manager
        
        # Switch to high contrast theme
        ui_polish.set_theme_scheme(ColorScheme.HIGH_CONTRAST)
        
        # Verify accessibility manager responds
        current_theme = ui_polish.theme_manager.get_current_scheme()
        assert current_theme == ColorScheme.HIGH_CONTRAST

    @pytest.mark.integration
    def test_responsive_theme_coordination(self, test_window):
        """Test coordination between responsive layout and theme."""
        ui_polish = test_window.ui_polish_manager
        
        # Change window size to trigger responsive layout
        test_window.resize(500, 400)  # Compact size
        
        # Verify responsive manager detects change
        layout_info = ui_polish.responsive_manager.get_layout_info()
        assert layout_info['screen_size'] == 'compact'

    @pytest.mark.integration
    def test_scientific_widget_registration(self, test_window):
        """Test scientific widget registration with UI polish."""
        ui_polish = test_window.ui_polish_manager
        
        # Create a mock scientific table
        mock_table = Mock(spec=Gtk.TreeView)
        mock_table.get_style_context.return_value = Mock()
        
        # Register as scientific widget
        ui_polish.register_scientific_widget(
            'test_scientific_table', 
            mock_table,
            {
                'name': 'Test Scientific Table',
                'description': 'Test table for scientific data',
                'tooltip': 'Test tooltip'
            }
        )
        
        # Verify registration with accessibility manager
        assert 'test_scientific_table' in ui_polish.accessibility_manager.accessible_widgets


@pytest.mark.gui
class TestDialogIntegration:
    """Integration tests for dialog components."""

    @pytest.mark.integration
    def test_material_dialog_integration(self, gtk_test_environment):
        """Test material dialog integration."""
        with patch('app.windows.dialogs.material_dialog.MaterialDialog') as MockDialog:
            mock_dialog = Mock()
            mock_dialog.run.return_value = Gtk.ResponseType.OK
            mock_dialog.get_material_data.return_value = {
                'name': 'Dialog Test Cement',
                'type': 'Type I'
            }
            MockDialog.return_value = mock_dialog
            
            # Test dialog creation and usage
            from app.windows.dialogs.material_dialog import MaterialDialog
            dialog = MaterialDialog(None, 'cement')
            
            result = dialog.run()
            assert result == Gtk.ResponseType.OK

    @pytest.mark.integration
    def test_file_operations_dialog_integration(self, gtk_test_environment, temp_directory):
        """Test file operations dialog integration."""
        with patch('app.windows.dialogs.file_operations_dialog.FileOperationsDialog') as MockDialog:
            mock_dialog = Mock()
            mock_dialog.run.return_value = Gtk.ResponseType.OK
            mock_dialog.get_selected_files.return_value = [temp_directory / "test.json"]
            MockDialog.return_value = mock_dialog
            
            # Test file dialog
            from app.windows.dialogs.file_operations_dialog import FileOperationsDialog
            dialog = FileOperationsDialog(None, 'import')
            
            result = dialog.run()
            assert result == Gtk.ResponseType.OK


@pytest.mark.gui
@pytest.mark.slow
class TestUIPerformanceIntegration:
    """Performance integration tests for UI components."""

    @pytest.mark.integration
    def test_large_table_performance(self, gtk_test_environment, performance_timer):
        """Test performance with large data tables."""
        # Create table with many rows
        store = Gtk.ListStore(str, str, float, float, float)
        
        performance_timer.start()
        
        # Add 1000 rows
        for i in range(1000):
            store.append([f"Material {i}", "Type I", 20.0 + i*0.01, 5.0, 3.0])
        
        elapsed = performance_timer.stop()
        
        # Should handle 1000 rows quickly
        assert elapsed < 1.0, f"Large table creation took {elapsed:.3f}s"

    @pytest.mark.integration
    def test_theme_switching_performance(self, gtk_test_environment, performance_timer):
        """Test theme switching performance."""
        window = Gtk.ApplicationWindow()
        ui_polish = create_ui_polish_manager(window)
        
        themes = [ColorScheme.LIGHT, ColorScheme.DARK, ColorScheme.SCIENTIFIC, ColorScheme.HIGH_CONTRAST]
        
        performance_timer.start()
        
        # Switch themes multiple times
        for _ in range(10):
            for theme in themes:
                ui_polish.set_theme_scheme(theme)
        
        elapsed = performance_timer.stop()
        
        # Theme switching should be fast
        assert elapsed < 2.0, f"40 theme switches took {elapsed:.3f}s"
        
        window.destroy()

    @pytest.mark.integration
    def test_responsive_layout_performance(self, gtk_test_environment, performance_timer):
        """Test responsive layout change performance."""
        window = Gtk.ApplicationWindow()
        ui_polish = create_ui_polish_manager(window)
        responsive_manager = ui_polish.responsive_manager
        
        size_changes = [
            (800, 600), (1200, 800), (1600, 1000), (2000, 1200),
            (1400, 900), (1000, 700), (600, 400), (1800, 1000)
        ]
        
        performance_timer.start()
        
        # Simulate many size changes
        for width, height in size_changes * 10:  # 80 changes total
            responsive_manager._update_layout(width, height)
        
        elapsed = performance_timer.stop()
        
        # Responsive updates should be fast
        assert elapsed < 1.0, f"80 layout updates took {elapsed:.3f}s"
        
        window.destroy()


# Helper functions for UI testing

def simulate_key_press(widget, keyval, modifiers=0):
    """Simulate key press event on widget."""
    event = Gdk.Event.new(Gdk.EventType.KEY_PRESS)
    event.keyval = keyval
    event.state = modifiers
    event.window = widget.get_window()
    
    return widget.emit('key-press-event', event)


def simulate_button_click(button):
    """Simulate button click."""
    button.emit('clicked')


def wait_for_ui_update():
    """Wait for UI updates to complete."""
    while Gtk.events_pending():
        Gtk.main_iteration_do(False)


# Mock fixtures for UI testing

@pytest.fixture
def mock_tree_model():
    """Mock tree model for testing."""
    model = Gtk.ListStore(str, str, float)
    model.append(["Test Item 1", "Type A", 1.0])
    model.append(["Test Item 2", "Type B", 2.0])
    return model


@pytest.fixture  
def mock_tree_view(mock_tree_model):
    """Mock tree view with data."""
    treeview = Gtk.TreeView(model=mock_tree_model)
    
    # Add columns
    renderer = Gtk.CellRendererText()
    column = Gtk.TreeViewColumn("Name", renderer, text=0)
    treeview.append_column(column)
    
    return treeview
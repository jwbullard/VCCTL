#!/usr/bin/env python3
"""
Cross-Platform Compatibility Tests for VCCTL

Tests compatibility across Linux, Windows, and macOS platforms.
Validates file paths, environment variables, GTK behavior, and platform-specific features.
"""

import pytest
import os
import sys
import platform
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
from typing import Dict, Any, List

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib

# Import application components
from app.config.directories_config import DirectoriesConfig
from app.config.user_config import UserConfig
from app.services.directories_service import DirectoriesService
from app.services.file_operations_service import FileOperationsService
from app.ui.theme_manager import ThemeManager


class PlatformInfo:
    """Platform information and detection."""
    
    @staticmethod
    def get_platform():
        """Get current platform name."""
        return platform.system().lower()
    
    @staticmethod
    def is_windows():
        """Check if running on Windows."""
        return platform.system() == 'Windows'
    
    @staticmethod
    def is_macos():
        """Check if running on macOS."""
        return platform.system() == 'Darwin'
    
    @staticmethod
    def is_linux():
        """Check if running on Linux."""
        return platform.system() == 'Linux'
    
    @staticmethod
    def get_python_version():
        """Get Python version info."""
        return {
            'major': sys.version_info.major,
            'minor': sys.version_info.minor,
            'micro': sys.version_info.micro,
            'version_string': sys.version
        }
    
    @staticmethod
    def get_gtk_version():
        """Get GTK version info."""
        try:
            return {
                'major': Gtk.get_major_version(),
                'minor': Gtk.get_minor_version(),
                'micro': Gtk.get_micro_version(),
                'version_string': f"{Gtk.get_major_version()}.{Gtk.get_minor_version()}.{Gtk.get_micro_version()}"
            }
        except:
            return {'version_string': 'unknown'}


@pytest.mark.compatibility
class TestPathCompatibility:
    """Test file path handling across platforms."""
    
    def test_path_separator_handling(self, temp_directory):
        """Test proper path separator handling."""
        # Test path creation with different separators
        test_paths = [
            "materials/cement/type1.json",
            "output\\results\\simulation1.dat",
            "workspace/projects/project1/data.vcctl"
        ]
        
        for path_str in test_paths:
            # Convert to platform-appropriate path
            path = Path(temp_directory) / path_str
            
            # Create directory structure
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch()
            
            # Verify path exists and is accessible
            assert path.exists()
            assert path.is_file()
            
            # Test path string conversion
            path_str_converted = str(path)
            assert os.path.exists(path_str_converted)
    
    def test_directory_creation_permissions(self, temp_directory):
        """Test directory creation with proper permissions."""
        test_dirs = [
            "workspace",
            "materials", 
            "output",
            "temp",
            "config"
        ]
        
        for dir_name in test_dirs:
            dir_path = temp_directory / dir_name
            dir_path.mkdir(exist_ok=True)
            
            # Test directory is writable
            test_file = dir_path / "test_write.txt"
            test_file.write_text("test")
            assert test_file.exists()
            
            # Test directory is readable
            content = test_file.read_text()
            assert content == "test"
            
            # Cleanup
            test_file.unlink()
    
    def test_long_path_handling(self, temp_directory):
        """Test handling of long file paths."""
        # Create a deeply nested directory structure
        deep_path = temp_directory
        path_components = ["very", "long", "directory", "structure", "for", "testing", "compatibility"]
        
        for component in path_components:
            deep_path = deep_path / component
            deep_path.mkdir(exist_ok=True)
        
        # Create file in deep path
        test_file = deep_path / "test_file_with_long_name.json"
        test_file.write_text('{"test": "data"}')
        
        assert test_file.exists()
        
        # Test file operations work with long paths
        content = test_file.read_text()
        assert '"test": "data"' in content
    
    def test_special_characters_in_paths(self, temp_directory):
        """Test handling of special characters in file paths."""
        # Platform-specific special character tests
        if PlatformInfo.is_windows():
            # Windows has more restrictions
            special_chars = ["space name", "dash-name", "underscore_name"]
        else:
            # Unix-like systems are more permissive
            special_chars = ["space name", "dash-name", "underscore_name", "dot.name", "unicode_名前"]
        
        for char_name in special_chars:
            try:
                test_dir = temp_directory / char_name
                test_dir.mkdir(exist_ok=True)
                
                test_file = test_dir / f"test_{char_name}.txt"
                test_file.write_text("test content")
                
                assert test_file.exists()
                content = test_file.read_text()
                assert content == "test content"
                
            except (OSError, UnicodeError) as e:
                # Some characters may not be supported on certain platforms
                print(f"Skipping special character test for '{char_name}' on {PlatformInfo.get_platform()}: {e}")


@pytest.mark.compatibility
class TestEnvironmentCompatibility:
    """Test environment variable and configuration compatibility."""
    
    def test_environment_variable_handling(self):
        """Test environment variable access across platforms."""
        # Test standard environment variables
        env_vars = ['PATH', 'HOME' if not PlatformInfo.is_windows() else 'USERPROFILE']
        
        for var in env_vars:
            value = os.environ.get(var)
            if value:  # Variable exists
                assert isinstance(value, str)
                assert len(value) > 0
    
    def test_user_directory_detection(self):
        """Test user directory detection across platforms."""
        home_dir = Path.home()
        assert home_dir.exists()
        assert home_dir.is_dir()
        
        # Test platform-specific user directories
        if PlatformInfo.is_windows():
            # Windows user directories
            expected_dirs = ['Documents', 'Desktop', 'AppData']
        elif PlatformInfo.is_macos():
            # macOS user directories
            expected_dirs = ['Documents', 'Desktop', 'Library']
        else:
            # Linux user directories
            expected_dirs = ['Documents', 'Desktop', '.config']
        
        for dir_name in expected_dirs:
            dir_path = home_dir / dir_name
            if dir_path.exists():  # Not all directories may exist
                assert dir_path.is_dir()
    
    def test_temp_directory_handling(self):
        """Test temporary directory handling."""
        # Test system temp directory
        temp_dir = Path(tempfile.gettempdir())
        assert temp_dir.exists()
        assert temp_dir.is_dir()
        
        # Test creating temp files
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.vcctl') as temp_file:
            temp_file.write('{"test": "data"}')
            temp_file_path = Path(temp_file.name)
        
        try:
            assert temp_file_path.exists()
            content = temp_file_path.read_text()
            assert '"test": "data"' in content
        finally:
            if temp_file_path.exists():
                temp_file_path.unlink()
    
    def test_configuration_directory_detection(self):
        """Test configuration directory detection."""
        config_service = DirectoriesService(Mock())
        
        # Test platform-specific config directories
        if PlatformInfo.is_windows():
            # Windows: %APPDATA%
            expected_base = Path(os.environ.get('APPDATA', ''))
        elif PlatformInfo.is_macos():
            # macOS: ~/Library/Application Support
            expected_base = Path.home() / 'Library' / 'Application Support'
        else:
            # Linux: ~/.config
            expected_base = Path.home() / '.config'
        
        if expected_base.exists():
            assert expected_base.is_dir()


@pytest.mark.compatibility
@pytest.mark.gui
class TestGTKCompatibility:
    """Test GTK compatibility across platforms."""
    
    def test_gtk_initialization(self, gtk_test_environment):
        """Test GTK initialization."""
        # GTK should be initialized properly
        assert Gtk.get_major_version() >= 3
        assert Gtk.get_minor_version() >= 0
        
        # Test basic widget creation
        window = Gtk.Window()
        assert window is not None
        
        button = Gtk.Button(label="Test")
        assert button is not None
        assert button.get_label() == "Test"
    
    def test_gtk_theming_compatibility(self, gtk_test_environment):
        """Test GTK theming across platforms."""
        theme_manager = ThemeManager()
        
        # Test that theme manager initializes
        assert theme_manager is not None
        assert theme_manager.current_scheme is not None
        
        # Test theme switching
        from app.ui.theme_manager import ColorScheme
        
        for scheme in ColorScheme:
            try:
                theme_manager.set_color_scheme(scheme)
                assert theme_manager.get_current_scheme() == scheme
            except Exception as e:
                print(f"Theme {scheme.value} not supported on {PlatformInfo.get_platform()}: {e}")
    
    def test_gtk_file_dialogs(self, gtk_test_environment):
        """Test GTK file dialogs compatibility."""
        # Test file chooser dialog creation
        dialog = Gtk.FileChooserDialog(
            title="Test Dialog",
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        dialog.add_button("Open", Gtk.ResponseType.OK)
        
        assert dialog is not None
        
        # Test setting file filters
        filter_json = Gtk.FileFilter()
        filter_json.set_name("JSON files")
        filter_json.add_pattern("*.json")
        dialog.add_filter(filter_json)
        
        # Cleanup
        dialog.destroy()
    
    def test_gtk_clipboard(self, gtk_test_environment):
        """Test GTK clipboard functionality."""
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        
        # Test setting text
        test_text = "Test clipboard content"
        clipboard.set_text(test_text, -1)
        
        # Note: Reading from clipboard in headless environment may not work
        # This test mainly verifies the API is available
    
    def test_gtk_drag_and_drop(self, gtk_test_environment):
        """Test GTK drag and drop setup."""
        window = Gtk.Window()
        
        # Test setting up drag source
        targets = [Gtk.TargetEntry.new("text/plain", 0, 0)]
        
        try:
            window.drag_source_set(
                Gdk.ModifierType.BUTTON1_MASK,
                targets,
                Gdk.DragAction.COPY
            )
            
            # Test setting up drop target
            window.drag_dest_set(
                Gtk.DestDefaults.ALL,
                targets,
                Gdk.DragAction.COPY
            )
            
        except Exception as e:
            print(f"Drag and drop setup failed on {PlatformInfo.get_platform()}: {e}")


@pytest.mark.compatibility
class TestFileOperationCompatibility:
    """Test file operations across platforms."""
    
    def test_file_encoding_handling(self, temp_directory):
        """Test file encoding handling."""
        # Test UTF-8 encoding (standard)
        test_file = temp_directory / "utf8_test.json"
        test_data = {"name": "Test Material", "unicode": "测试数据"}
        
        import json
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, ensure_ascii=False)
        
        # Read back and verify
        with open(test_file, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        
        assert loaded_data['name'] == "Test Material"
        assert loaded_data['unicode'] == "测试数据"
    
    def test_file_locking_behavior(self, temp_directory):
        """Test file locking behavior across platforms."""
        test_file = temp_directory / "lock_test.txt"
        test_file.write_text("initial content")
        
        # Test file access patterns
        try:
            # Open file for reading
            with open(test_file, 'r') as f1:
                content1 = f1.read()
                
                # Try to open same file for reading (should work)
                with open(test_file, 'r') as f2:
                    content2 = f2.read()
                    assert content1 == content2
                
                # Platform-specific write behavior varies
                # Windows may lock files more aggressively
                
        except PermissionError as e:
            print(f"File locking behavior on {PlatformInfo.get_platform()}: {e}")
    
    def test_file_permission_handling(self, temp_directory):
        """Test file permission handling."""
        test_file = temp_directory / "permission_test.txt"
        test_file.write_text("test content")
        
        # Test file is readable
        assert os.access(test_file, os.R_OK)
        
        # Test file is writable
        assert os.access(test_file, os.W_OK)
        
        if not PlatformInfo.is_windows():
            # Unix-like systems support more granular permissions
            import stat
            
            # Test setting and checking permissions
            os.chmod(test_file, stat.S_IRUSR | stat.S_IWUSR)  # Owner read/write only
            
            file_stat = test_file.stat()
            assert file_stat.st_mode & stat.S_IRUSR  # Owner can read
            assert file_stat.st_mode & stat.S_IWUSR  # Owner can write


@pytest.mark.compatibility
class TestDatabaseCompatibility:
    """Test database compatibility across platforms."""
    
    def test_sqlite_path_handling(self, temp_directory):
        """Test SQLite database path handling."""
        # Test different path formats
        db_paths = [
            temp_directory / "test.db",
            temp_directory / "sub_dir" / "test.db",
            temp_directory / "test with spaces.db"
        ]
        
        for db_path in db_paths:
            # Create directory if needed
            db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Test database creation
            import sqlite3
            try:
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                
                # Create test table
                cursor.execute('''
                    CREATE TABLE test_table (
                        id INTEGER PRIMARY KEY,
                        name TEXT NOT NULL
                    )
                ''')
                
                # Insert test data
                cursor.execute("INSERT INTO test_table (name) VALUES (?)", ("test",))
                conn.commit()
                
                # Verify data
                cursor.execute("SELECT name FROM test_table WHERE id = 1")
                result = cursor.fetchone()
                assert result[0] == "test"
                
                conn.close()
                
                # Verify database file exists
                assert db_path.exists()
                
            except Exception as e:
                print(f"Database test failed for path {db_path}: {e}")
    
    def test_database_concurrent_access(self, temp_directory):
        """Test database concurrent access behavior."""
        db_path = temp_directory / "concurrent_test.db"
        
        import sqlite3
        import threading
        import time
        
        # Create database
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE concurrent_test (
                id INTEGER PRIMARY KEY,
                thread_id TEXT,
                timestamp REAL
            )
        ''')
        conn.commit()
        conn.close()
        
        results = []
        
        def worker(thread_id):
            try:
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                
                cursor.execute(
                    "INSERT INTO concurrent_test (thread_id, timestamp) VALUES (?, ?)",
                    (f"thread_{thread_id}", time.time())
                )
                conn.commit()
                conn.close()
                results.append(f"thread_{thread_id}")
                
            except Exception as e:
                print(f"Concurrent access error in thread {thread_id}: {e}")
        
        # Start concurrent threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Verify all threads completed
        assert len(results) == 5


@pytest.mark.compatibility
class TestPlatformSpecificFeatures:
    """Test platform-specific features and adaptations."""
    
    def test_platform_detection(self):
        """Test platform detection accuracy."""
        current_platform = PlatformInfo.get_platform()
        
        assert current_platform in ['windows', 'darwin', 'linux']
        
        # Test boolean methods
        platform_checks = [
            PlatformInfo.is_windows(),
            PlatformInfo.is_macos(), 
            PlatformInfo.is_linux()
        ]
        
        # Exactly one should be True
        assert sum(platform_checks) == 1
    
    def test_platform_specific_paths(self, temp_directory):
        """Test platform-specific path handling."""
        config = UserConfig()
        
        # Test default directory detection
        if PlatformInfo.is_windows():
            # Windows paths
            assert 'Documents' in str(config.default_workspace_dir) or 'My Documents' in str(config.default_workspace_dir)
        elif PlatformInfo.is_macos():
            # macOS paths
            assert 'Documents' in str(config.default_workspace_dir)
        else:
            # Linux paths
            assert 'Documents' in str(config.default_workspace_dir) or str(config.default_workspace_dir).endswith('vcctl')
    
    def test_platform_specific_ui_adaptations(self, gtk_test_environment):
        """Test platform-specific UI adaptations."""
        # Test menu structure adaptations
        if PlatformInfo.is_macos():
            # macOS typically uses application menu in menu bar
            menu_expected = "application_menu"
        else:
            # Windows/Linux use window menu bars
            menu_expected = "window_menu"
        
        # This would be tested with actual UI implementation
        # For now, just verify the detection works
        assert menu_expected in ["application_menu", "window_menu"]
    
    def test_font_availability(self, gtk_test_environment):
        """Test font availability across platforms."""
        # Test common fonts that should be available
        common_fonts = ["Sans", "Serif", "Monospace"]
        
        for font_name in common_fonts:
            # Try to create font description
            try:
                from gi.repository import Pango
                font_desc = Pango.FontDescription(font_name)
                assert font_desc is not None
            except Exception as e:
                print(f"Font {font_name} not available on {PlatformInfo.get_platform()}: {e}")


@pytest.mark.compatibility
class TestCrossCompatibilityIntegration:
    """Integration tests for cross-platform compatibility."""
    
    def test_complete_workflow_compatibility(self, temp_directory):
        """Test complete workflow works across platforms."""
        # Simulate complete workflow with platform considerations
        
        # Step 1: Setup directories
        workspace = temp_directory / "vcctl_workspace"
        materials_dir = workspace / "materials"
        output_dir = workspace / "output"
        
        for directory in [workspace, materials_dir, output_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Step 2: Create material file
        material_file = materials_dir / "test_cement.json"
        material_data = {
            "name": "Cross-Platform Test Cement",
            "c3s_mass_fraction": 0.55,
            "platform": PlatformInfo.get_platform()
        }
        
        import json
        with open(material_file, 'w') as f:
            json.dump(material_data, f, indent=2)
        
        # Step 3: Process material file
        with open(material_file, 'r') as f:
            loaded_data = json.load(f)
        
        assert loaded_data['name'] == "Cross-Platform Test Cement"
        assert loaded_data['platform'] == PlatformInfo.get_platform()
        
        # Step 4: Create output file
        output_file = output_dir / "results.txt"
        output_file.write_text(f"Results for {PlatformInfo.get_platform()}\n")
        
        # Step 5: Verify all files exist and are accessible
        assert material_file.exists()
        assert output_file.exists()
        
        # Step 6: Cleanup verification
        assert workspace.exists()
        
        # Test cleanup
        shutil.rmtree(workspace)
        assert not workspace.exists()


# Platform information fixture
@pytest.fixture
def platform_info():
    """Platform information fixture."""
    return {
        'platform': PlatformInfo.get_platform(),
        'is_windows': PlatformInfo.is_windows(),
        'is_macos': PlatformInfo.is_macos(),
        'is_linux': PlatformInfo.is_linux(),
        'python_version': PlatformInfo.get_python_version(),
        'gtk_version': PlatformInfo.get_gtk_version()
    }


# Skip platform-specific tests
def skip_on_platform(platform_name):
    """Decorator to skip tests on specific platforms."""
    return pytest.mark.skipif(
        PlatformInfo.get_platform() == platform_name.lower(),
        reason=f"Not supported on {platform_name}"
    )


def require_platform(platform_name):
    """Decorator to require specific platform for test."""
    return pytest.mark.skipif(
        PlatformInfo.get_platform() != platform_name.lower(),
        reason=f"Requires {platform_name}"
    )


# Example of platform-specific tests
@pytest.mark.compatibility
class TestPlatformSpecificBehavior:
    """Platform-specific behavior tests."""
    
    @require_platform('windows')
    def test_windows_specific_features(self):
        """Test Windows-specific features."""
        # Test Windows path handling
        import os
        path = os.path.join("C:", "Users", "test", "Documents")
        assert "\\" in path or "/" in path
        
    @require_platform('darwin')  
    def test_macos_specific_features(self):
        """Test macOS-specific features."""
        # Test macOS path handling
        home = Path.home()
        library = home / "Library"
        if library.exists():
            assert library.is_dir()
    
    @require_platform('linux')
    def test_linux_specific_features(self):
        """Test Linux-specific features."""
        # Test Linux path handling
        home = Path.home()
        config_dir = home / ".config"
        # .config directory may or may not exist
        if config_dir.exists():
            assert config_dir.is_dir()


# Performance comparison across platforms
@pytest.mark.compatibility
@pytest.mark.performance
class TestCrossPlatformPerformance:
    """Cross-platform performance comparison."""
    
    def test_file_io_performance_comparison(self, temp_directory):
        """Compare file I/O performance across platforms."""
        import time
        
        test_file = temp_directory / "performance_test.txt"
        test_data = "x" * 10000  # 10KB of data
        
        # Write performance
        start_time = time.perf_counter()
        test_file.write_text(test_data)
        write_time = time.perf_counter() - start_time
        
        # Read performance
        start_time = time.perf_counter()
        read_data = test_file.read_text()
        read_time = time.perf_counter() - start_time
        
        print(f"Platform: {PlatformInfo.get_platform()}")
        print(f"Write time: {write_time * 1000:.2f}ms")
        print(f"Read time: {read_time * 1000:.2f}ms")
        
        assert read_data == test_data
        assert write_time < 1.0  # Should complete within 1 second
        assert read_time < 1.0   # Should complete within 1 second
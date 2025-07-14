#!/usr/bin/env python3
"""
VCCTL Test Configuration and Fixtures

Global pytest configuration and shared fixtures for VCCTL testing suite.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from typing import Generator, Any, Dict
from unittest.mock import Mock, patch
import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk

# Import application modules
from app.config.config_manager import ConfigManager
from app.database.service import DatabaseService
from app.services.service_container import ServiceContainer
from app.utils.error_handling import ErrorHandler


# Test environment setup
os.environ['VCCTL_TEST_MODE'] = '1'
os.environ['VCCTL_LOG_LEVEL'] = 'ERROR'  # Suppress logs during testing


@pytest.fixture(scope="session")
def gtk_test_environment():
    """Setup GTK test environment."""
    # Initialize GTK for testing (offscreen)
    if 'DISPLAY' not in os.environ:
        os.environ['DISPLAY'] = ':99'
    
    # Initialize GTK
    Gtk.init_check([])
    
    # Setup offscreen rendering for headless testing
    window = Gtk.OffscreenWindow()
    window.show()
    
    yield window
    
    # Cleanup
    window.destroy()


@pytest.fixture
def temp_directory() -> Generator[Path, None, None]:
    """Create temporary directory for testing."""
    temp_dir = Path(tempfile.mkdtemp(prefix="vcctl_test_"))
    try:
        yield temp_dir
    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)


@pytest.fixture
def test_database(temp_directory: Path) -> Generator[DatabaseService, None, None]:
    """Create test database."""
    db_path = temp_directory / "test_vcctl.db"
    
    # Create test database service
    db_service = DatabaseService(str(db_path))
    db_service.initialize()
    
    yield db_service
    
    # Cleanup
    db_service.close()


@pytest.fixture
def test_config(temp_directory: Path) -> Generator[ConfigManager, None, None]:
    """Create test configuration."""
    config_dir = temp_directory / "config"
    config_dir.mkdir()
    
    # Create test config manager with test directory
    config_manager = ConfigManager(config_dir)
    
    # Set test-specific configurations
    config_manager.user_config.workspace_dir = str(temp_directory / "workspace")
    config_manager.user_config.materials_dir = str(temp_directory / "materials") 
    config_manager.user_config.output_dir = str(temp_directory / "output")
    config_manager.user_config.temp_dir = str(temp_directory / "temp")
    
    # Create directories
    for dir_path in [
        config_manager.user_config.workspace_dir,
        config_manager.user_config.materials_dir,
        config_manager.user_config.output_dir,
        config_manager.user_config.temp_dir
    ]:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    yield config_manager


@pytest.fixture
def mock_service_container(test_config: ConfigManager, test_database: DatabaseService) -> Generator[ServiceContainer, None, None]:
    """Create mock service container for testing."""
    container = ServiceContainer()
    
    # Register test services
    container.register('config_manager', test_config)
    container.register('database_service', test_database)
    
    # Mock external services
    mock_hydration_service = Mock()
    mock_microstructure_service = Mock()
    
    container.register('hydration_service', mock_hydration_service)
    container.register('microstructure_service', mock_microstructure_service)
    
    yield container


@pytest.fixture
def sample_cement_data() -> Dict[str, Any]:
    """Sample cement data for testing."""
    return {
        'name': 'Test Cement Type I',
        'type': 'Type I',
        'sio2': 20.5,
        'al2o3': 5.2,
        'fe2o3': 3.1,
        'cao': 65.0,
        'mgo': 2.8,
        'so3': 2.4,
        'k2o': 0.5,
        'na2o': 0.2,
        'blaine_fineness': 350.0,
        'density': 3.15,
        'loss_on_ignition': 1.2
    }


@pytest.fixture
def sample_aggregate_data() -> Dict[str, Any]:
    """Sample aggregate data for testing."""
    return {
        'name': 'Test Fine Sand',
        'type': 'fine',
        'density': 2.65,
        'absorption': 1.2,
        'fineness_modulus': 2.8,
        'gradation': {
            'sieve_4_75mm': 100.0,
            'sieve_2_36mm': 95.0,
            'sieve_1_18mm': 85.0,
            'sieve_0_60mm': 65.0,
            'sieve_0_30mm': 35.0,
            'sieve_0_15mm': 15.0
        }
    }


@pytest.fixture
def sample_mix_design_data() -> Dict[str, Any]:
    """Sample mix design data for testing."""
    return {
        'name': 'Test Mix Design',
        'cement_content': 350.0,  # kg/m³
        'water_content': 175.0,   # kg/m³
        'water_cement_ratio': 0.5,
        'fine_aggregate': 650.0,  # kg/m³
        'coarse_aggregate': 1100.0,  # kg/m³
        'air_content': 2.0,       # %
        'slump': 100.0,           # mm
        'compressive_strength_28d': 35.0  # MPa
    }


@pytest.fixture 
def mock_gtk_widget():
    """Create mock GTK widget for testing."""
    widget = Mock(spec=Gtk.Widget)
    widget.get_style_context.return_value = Mock()
    widget.connect = Mock()
    widget.show_all = Mock()
    widget.hide = Mock()
    widget.destroy = Mock()
    return widget


@pytest.fixture
def mock_file_operations():
    """Mock file operations for testing."""
    with patch('app.utils.file_operations.FileOperations') as mock:
        mock_instance = Mock()
        mock.return_value = mock_instance
        
        # Setup common file operation mocks
        mock_instance.create_directory.return_value = True
        mock_instance.copy_file.return_value = True
        mock_instance.move_file.return_value = True
        mock_instance.delete_file.return_value = True
        mock_instance.validate_file_format.return_value = True
        
        yield mock_instance


@pytest.fixture
def performance_timer():
    """Performance timing utility for benchmarks."""
    import time
    
    class PerformanceTimer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.perf_counter()
        
        def stop(self):
            self.end_time = time.perf_counter()
            return self.elapsed
        
        @property
        def elapsed(self):
            if self.start_time is None or self.end_time is None:
                return None
            return self.end_time - self.start_time
    
    return PerformanceTimer()


@pytest.fixture(autouse=True)
def setup_test_logging():
    """Setup test logging configuration."""
    import logging
    
    # Suppress most logging during tests
    logging.getLogger('VCCTL').setLevel(logging.CRITICAL)
    logging.getLogger('SQLAlchemy').setLevel(logging.CRITICAL)
    logging.getLogger('matplotlib').setLevel(logging.CRITICAL)
    
    yield
    
    # Restore logging after test
    logging.getLogger('VCCTL').setLevel(logging.INFO)


# Custom assertions for VCCTL testing

def assert_valid_cement_composition(cement_data: Dict[str, float], tolerance: float = 0.1):
    """Assert that cement composition adds up to approximately 100%."""
    oxides = ['sio2', 'al2o3', 'fe2o3', 'cao', 'mgo', 'so3', 'k2o', 'na2o']
    total = sum(cement_data.get(oxide, 0.0) for oxide in oxides)
    
    assert abs(total - 100.0) <= tolerance, f"Cement composition totals {total}%, expected ~100%"


def assert_valid_mix_design(mix_data: Dict[str, float]):
    """Assert that mix design has valid proportions."""
    assert mix_data['water_cement_ratio'] > 0.2, "W/C ratio too low"
    assert mix_data['water_cement_ratio'] < 0.8, "W/C ratio too high"
    assert mix_data['air_content'] >= 0.0, "Air content cannot be negative"
    assert mix_data['air_content'] <= 10.0, "Air content too high"


def assert_file_exists_and_valid(file_path: Path, min_size: int = 0):
    """Assert that file exists and has minimum size."""
    assert file_path.exists(), f"File does not exist: {file_path}"
    assert file_path.is_file(), f"Path is not a file: {file_path}"
    assert file_path.stat().st_size >= min_size, f"File too small: {file_path}"


# Performance benchmarks

class PerformanceBenchmarks:
    """Performance benchmarks for VCCTL operations."""
    
    MAX_DATABASE_QUERY_TIME = 0.1      # 100ms
    MAX_UI_RESPONSE_TIME = 0.05        # 50ms
    MAX_FILE_OPERATION_TIME = 1.0      # 1 second
    MAX_CALCULATION_TIME = 5.0         # 5 seconds
    
    @staticmethod
    def assert_performance(elapsed_time: float, max_time: float, operation: str):
        """Assert that operation completed within time limit."""
        assert elapsed_time <= max_time, \
            f"{operation} took {elapsed_time:.3f}s, max allowed: {max_time:.3f}s"


# Test data generators

def generate_test_cement_data(variations: int = 1) -> Generator[Dict[str, Any], None, None]:
    """Generate multiple cement test data variations."""
    base_data = {
        'name': 'Test Cement',
        'type': 'Type I',
        'sio2': 20.5, 'al2o3': 5.2, 'fe2o3': 3.1, 'cao': 65.0,
        'mgo': 2.8, 'so3': 2.4, 'k2o': 0.5, 'na2o': 0.2,
        'blaine_fineness': 350.0, 'density': 3.15, 'loss_on_ignition': 1.2
    }
    
    for i in range(variations):
        data = base_data.copy()
        data['name'] = f"Test Cement {i+1}"
        # Add slight variations
        data['sio2'] += i * 0.5
        data['cao'] -= i * 0.5
        yield data


# Test markers for categorization

pytest_plugins = []

# Mark tests that require GTK
requires_gtk = pytest.mark.gui

# Mark slow tests
slow_test = pytest.mark.slow

# Mark tests that need database
requires_database = pytest.mark.database

# Mark tests that need filesystem
requires_filesystem = pytest.mark.filesystem
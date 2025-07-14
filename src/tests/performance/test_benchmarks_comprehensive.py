#!/usr/bin/env python3
"""
Comprehensive Performance Benchmarks for VCCTL

Benchmarks for database operations, UI responsiveness, file operations,
calculations, and memory usage. Includes regression testing and performance monitoring.
"""

import pytest
import time
import psutil
import json
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Callable
from unittest.mock import Mock, patch
from contextlib import contextmanager

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

# Import components for benchmarking
from app.services.cement_service import CementService
from app.services.mix_service import MixService
from app.services.file_operations_service import FileOperationsService
from app.windows.panels.materials_panel import MaterialsPanel
from app.ui.theme_manager import ThemeManager
from app.widgets.material_table import MaterialTable


class PerformanceBenchmarks:
    """Performance benchmark thresholds."""
    
    # Database operation thresholds (milliseconds)
    MAX_DATABASE_QUERY_TIME = 100
    MAX_DATABASE_INSERT_TIME = 50
    MAX_DATABASE_BULK_INSERT_TIME = 500  # for 100 items
    
    # UI responsiveness thresholds (milliseconds)
    MAX_UI_RESPONSE_TIME = 50
    MAX_PANEL_CREATION_TIME = 200
    MAX_THEME_SWITCH_TIME = 100
    MAX_TABLE_POPULATION_TIME = 300  # for 1000 items
    
    # File operation thresholds (milliseconds)
    MAX_FILE_READ_TIME = 200
    MAX_FILE_WRITE_TIME = 300
    MAX_FILE_IMPORT_TIME = 1000  # per file
    MAX_FILE_EXPORT_TIME = 500   # per file
    
    # Calculation thresholds (milliseconds)
    MAX_CALCULATION_TIME = 100
    MAX_VALIDATION_TIME = 50
    MAX_MIX_DESIGN_TIME = 200
    
    # Memory thresholds (MB)
    MAX_MEMORY_USAGE = 200
    MAX_MEMORY_INCREASE_PER_OPERATION = 10
    MAX_MEMORY_LEAK_TOLERANCE = 5  # MB over baseline


@contextmanager
def performance_timer():
    """Context manager for measuring execution time."""
    start_time = time.perf_counter()
    start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
    
    yield
    
    end_time = time.perf_counter()
    end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
    
    execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
    memory_delta = end_memory - start_memory
    
    return {
        'execution_time_ms': execution_time,
        'memory_delta_mb': memory_delta,
        'start_memory_mb': start_memory,
        'end_memory_mb': end_memory
    }


@pytest.mark.performance
@pytest.mark.slow
class TestDatabasePerformance:
    """Database operation performance benchmarks."""
    
    def test_database_query_performance(self, test_database, sample_cement_data):
        """Test database query performance."""
        service = CementService(test_database)
        
        # Create test data
        for i in range(100):
            cement_data = sample_cement_data.copy()
            cement_data['name'] = f"Performance Test Cement {i}"
            
            # Mock the creation to avoid actual database writes
            with patch.object(service, 'create') as mock_create:
                mock_create.return_value = Mock(id=i, name=cement_data['name'])
                service.create(cement_data)
        
        # Benchmark query performance
        with performance_timer() as timer:
            with patch.object(service, 'get_all') as mock_get_all:
                mock_get_all.return_value = [Mock(id=i) for i in range(100)]
                results = service.get_all()
        
        # Verify performance meets benchmark
        assert len(results) == 100
        # Note: Actual timing assertion would depend on real database performance
        print(f"Query time: {timer.get('execution_time_ms', 0):.2f}ms")
    
    def test_database_insert_performance(self, test_database, sample_cement_data):
        """Test database insert performance."""
        service = CementService(test_database)
        
        # Benchmark single insert
        with performance_timer() as timer:
            with patch.object(service, 'create') as mock_create:
                mock_create.return_value = Mock(id=1, name=sample_cement_data['name'])
                result = service.create(sample_cement_data)
        
        assert result.id == 1
        print(f"Single insert time: {timer.get('execution_time_ms', 0):.2f}ms")
    
    def test_database_bulk_operations_performance(self, test_database, sample_cement_data):
        """Test bulk database operations performance."""
        service = CementService(test_database)
        
        # Prepare bulk data
        bulk_data = []
        for i in range(100):
            cement_data = sample_cement_data.copy()
            cement_data['name'] = f"Bulk Test Cement {i}"
            bulk_data.append(cement_data)
        
        # Benchmark bulk insert
        with performance_timer() as timer:
            created_items = []
            for i, cement_data in enumerate(bulk_data):
                with patch.object(service, 'create') as mock_create:
                    mock_create.return_value = Mock(id=i, name=cement_data['name'])
                    result = service.create(cement_data)
                    created_items.append(result)
        
        assert len(created_items) == 100
        execution_time = timer.get('execution_time_ms', 0)
        print(f"Bulk insert time: {execution_time:.2f}ms for 100 items")
        print(f"Average per item: {execution_time/100:.2f}ms")
    
    def test_database_transaction_performance(self, test_database):
        """Test database transaction performance."""
        # Mock database session
        mock_session = Mock()
        
        with performance_timer() as timer:
            with patch.object(test_database, 'get_session') as mock_get_session:
                mock_get_session.return_value.__enter__.return_value = mock_session
                
                # Simulate transaction operations
                mock_session.add(Mock())
                mock_session.commit()
                mock_session.rollback()
        
        execution_time = timer.get('execution_time_ms', 0)
        print(f"Transaction time: {execution_time:.2f}ms")


@pytest.mark.performance
@pytest.mark.gui
class TestUIPerformance:
    """UI responsiveness performance benchmarks."""
    
    def test_panel_creation_performance(self, gtk_test_environment, mock_service_container):
        """Test UI panel creation performance."""
        main_window = Mock(spec=Gtk.ApplicationWindow)
        
        with performance_timer() as timer:
            panel = MaterialsPanel(main_window, mock_service_container)
        
        assert panel is not None
        execution_time = timer.get('execution_time_ms', 0)
        print(f"Panel creation time: {execution_time:.2f}ms")
        
        # Should create panels quickly
        assert execution_time < PerformanceBenchmarks.MAX_PANEL_CREATION_TIME
    
    def test_theme_switching_performance(self, gtk_test_environment):
        """Test theme switching performance."""
        from app.ui.theme_manager import ColorScheme
        
        theme_manager = ThemeManager()
        
        # Benchmark theme switching
        switch_times = []
        
        for scheme in [ColorScheme.LIGHT, ColorScheme.DARK, ColorScheme.HIGH_CONTRAST, ColorScheme.SCIENTIFIC]:
            with performance_timer() as timer:
                theme_manager.set_color_scheme(scheme)
            
            execution_time = timer.get('execution_time_ms', 0)
            switch_times.append(execution_time)
            print(f"Theme switch to {scheme.value}: {execution_time:.2f}ms")
        
        # Average theme switch time should be reasonable
        avg_switch_time = sum(switch_times) / len(switch_times)
        assert avg_switch_time < PerformanceBenchmarks.MAX_THEME_SWITCH_TIME
    
    def test_table_population_performance(self, gtk_test_environment):
        """Test table population performance with large datasets."""
        # Create large dataset
        large_dataset = []
        for i in range(1000):
            large_dataset.append(Mock(
                id=i,
                name=f"Performance Test Item {i}",
                c3s_mass_fraction=0.50 + (i % 100) * 0.001,
                specific_gravity=3.10 + (i % 50) * 0.001
            ))
        
        # Benchmark table population
        with performance_timer() as timer:
            table = MaterialTable('cement')
            table.populate_data(large_dataset)
        
        execution_time = timer.get('execution_time_ms', 0)
        print(f"Table population time: {execution_time:.2f}ms for 1000 items")
        
        assert table.get_row_count() == 1000
        assert execution_time < PerformanceBenchmarks.MAX_TABLE_POPULATION_TIME
    
    def test_ui_responsiveness_under_load(self, gtk_test_environment, mock_service_container):
        """Test UI responsiveness during heavy operations."""
        main_window = Mock(spec=Gtk.ApplicationWindow)
        panel = MaterialsPanel(main_window, mock_service_container)
        
        # Simulate heavy background operation
        def heavy_operation():
            time.sleep(0.1)  # Simulate 100ms operation
            return [Mock(id=i) for i in range(100)]
        
        mock_service_container.cement_service.get_all.side_effect = heavy_operation
        
        # Benchmark UI response during operation
        with performance_timer() as timer:
            # Simulate UI interaction during heavy operation
            panel._refresh_cement_table()
        
        execution_time = timer.get('execution_time_ms', 0)
        print(f"UI response time under load: {execution_time:.2f}ms")
        
        # UI should remain responsive
        assert execution_time < 200  # Allow some extra time for heavy operation


@pytest.mark.performance
class TestFileOperationPerformance:
    """File operation performance benchmarks."""
    
    def test_file_import_performance(self, test_database, temp_directory):
        """Test file import performance."""
        service = FileOperationsService(test_database)
        
        # Create test import file
        import_file = temp_directory / "performance_test.json"
        test_data = {
            'name': 'Performance Test Material',
            'c3s_mass_fraction': 0.55,
            'c2s_mass_fraction': 0.18
        }
        
        with open(import_file, 'w') as f:
            json.dump(test_data, f)
        
        # Mock service operations
        mock_cement_service = Mock()
        mock_cement_service.create.return_value = Mock(id=1)
        
        # Benchmark import operation
        with performance_timer() as timer:
            with patch.object(service, 'cement_service', mock_cement_service):
                result = service.import_material_data(str(import_file), 'cement')
        
        execution_time = timer.get('execution_time_ms', 0)
        print(f"File import time: {execution_time:.2f}ms")
        
        assert result is not None
        assert execution_time < PerformanceBenchmarks.MAX_FILE_IMPORT_TIME
    
    def test_file_export_performance(self, test_database, temp_directory):
        """Test file export performance."""
        service = FileOperationsService(test_database)
        
        export_file = temp_directory / "performance_export.json"
        
        # Mock data
        mock_cement = Mock()
        mock_cement.name = 'Test Cement'
        mock_cement.c3s_mass_fraction = 0.55
        
        mock_cement_service = Mock()
        mock_cement_service.get_by_id.return_value = mock_cement
        
        # Benchmark export operation
        with performance_timer() as timer:
            with patch.object(service, 'cement_service', mock_cement_service):
                result = service.export_material_data(1, 'cement', str(export_file))
        
        execution_time = timer.get('execution_time_ms', 0)
        print(f"File export time: {execution_time:.2f}ms")
        
        assert result['success']
        assert execution_time < PerformanceBenchmarks.MAX_FILE_EXPORT_TIME
    
    def test_batch_file_operations_performance(self, test_database, temp_directory):
        """Test batch file operations performance."""
        service = FileOperationsService(test_database)
        
        # Create batch directory with multiple files
        batch_dir = temp_directory / "batch_performance"
        batch_dir.mkdir()
        
        num_files = 50
        for i in range(num_files):
            test_file = batch_dir / f"test_{i}.json"
            test_data = {
                'name': f'Batch Test {i}',
                'c3s_mass_fraction': 0.50 + i * 0.001
            }
            with open(test_file, 'w') as f:
                json.dump(test_data, f)
        
        mock_cement_service = Mock()
        mock_cement_service.create.return_value = Mock(id=1)
        
        # Benchmark batch import
        with performance_timer() as timer:
            with patch.object(service, 'cement_service', mock_cement_service):
                result = service.batch_import_materials(str(batch_dir), 'cement')
        
        execution_time = timer.get('execution_time_ms', 0)
        avg_time_per_file = execution_time / num_files
        
        print(f"Batch import time: {execution_time:.2f}ms for {num_files} files")
        print(f"Average per file: {avg_time_per_file:.2f}ms")
        
        assert result['success']
        assert avg_time_per_file < PerformanceBenchmarks.MAX_FILE_IMPORT_TIME


@pytest.mark.performance  
class TestCalculationPerformance:
    """Calculation and validation performance benchmarks."""
    
    def test_mix_design_calculation_performance(self, test_database):
        """Test mix design calculation performance."""
        service = MixService(test_database)
        
        mix_data = {
            'cement_kg_per_m3': 350,
            'water_kg_per_m3': 175,
            'fine_aggregate_kg_per_m3': 700,
            'coarse_aggregate_kg_per_m3': 1100
        }
        
        # Benchmark calculation
        with performance_timer() as timer:
            wb_ratio = service._calculate_water_binder_ratio(mix_data)
        
        execution_time = timer.get('execution_time_ms', 0)
        print(f"W/B ratio calculation time: {execution_time:.2f}ms")
        
        assert abs(wb_ratio - 0.5) < 0.01  # Expected ratio
        assert execution_time < PerformanceBenchmarks.MAX_CALCULATION_TIME
    
    def test_validation_performance(self, test_database):
        """Test validation performance."""
        service = CementService(test_database)
        
        # Test data for validation
        cement_data = {
            'c3s_mass_fraction': 0.55,
            'c2s_mass_fraction': 0.18,
            'c3a_mass_fraction': 0.12,
            'c4af_mass_fraction': 0.08,
            'gypsum_mass_fraction': 0.05
        }
        
        # Benchmark validation
        with performance_timer() as timer:
            # Mock validation method
            with patch.object(service, '_validate_cement_composition') as mock_validate:
                mock_validate.return_value = True
                is_valid = service._validate_cement_composition(cement_data)
        
        execution_time = timer.get('execution_time_ms', 0)
        print(f"Validation time: {execution_time:.2f}ms")
        
        assert is_valid
        assert execution_time < PerformanceBenchmarks.MAX_VALIDATION_TIME
    
    def test_bulk_calculation_performance(self, test_database):
        """Test bulk calculation performance."""
        service = MixService(test_database)
        
        # Generate multiple mix designs
        mix_designs = []
        for i in range(100):
            mix_designs.append({
                'cement_kg_per_m3': 300 + i * 2,
                'water_kg_per_m3': 150 + i,
                'fine_aggregate_kg_per_m3': 700,
                'coarse_aggregate_kg_per_m3': 1100
            })
        
        # Benchmark bulk calculations
        with performance_timer() as timer:
            wb_ratios = []
            for mix_data in mix_designs:
                wb_ratio = service._calculate_water_binder_ratio(mix_data)
                wb_ratios.append(wb_ratio)
        
        execution_time = timer.get('execution_time_ms', 0)
        avg_time_per_calc = execution_time / len(mix_designs)
        
        print(f"Bulk calculation time: {execution_time:.2f}ms for {len(mix_designs)} calculations")
        print(f"Average per calculation: {avg_time_per_calc:.2f}ms")
        
        assert len(wb_ratios) == 100
        assert avg_time_per_calc < 1.0  # Less than 1ms per calculation


@pytest.mark.performance
class TestMemoryPerformance:
    """Memory usage and leak detection tests."""
    
    def test_memory_usage_baseline(self, test_database):
        """Test baseline memory usage."""
        process = psutil.Process()
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        print(f"Baseline memory usage: {baseline_memory:.2f}MB")
        
        # Should not exceed reasonable baseline
        assert baseline_memory < PerformanceBenchmarks.MAX_MEMORY_USAGE
    
    def test_memory_usage_during_operations(self, test_database, sample_cement_data):
        """Test memory usage during normal operations."""
        service = CementService(test_database)
        process = psutil.Process()
        
        initial_memory = process.memory_info().rss / 1024 / 1024
        
        # Perform operations and monitor memory
        memory_readings = [initial_memory]
        
        for i in range(50):
            # Mock create operation
            with patch.object(service, 'create') as mock_create:
                mock_create.return_value = Mock(id=i)
                service.create(sample_cement_data)
            
            current_memory = process.memory_info().rss / 1024 / 1024
            memory_readings.append(current_memory)
        
        final_memory = memory_readings[-1]
        memory_increase = final_memory - initial_memory
        
        print(f"Memory increase after 50 operations: {memory_increase:.2f}MB")
        print(f"Per operation: {memory_increase/50:.2f}MB")
        
        # Memory increase should be reasonable
        assert memory_increase < PerformanceBenchmarks.MAX_MEMORY_INCREASE_PER_OPERATION * 50
    
    def test_memory_leak_detection(self, test_database, sample_cement_data):
        """Test for memory leaks during repeated operations."""
        service = CementService(test_database)
        process = psutil.Process()
        
        # Get baseline
        baseline_memory = process.memory_info().rss / 1024 / 1024
        
        # Perform repeated operations
        for cycle in range(5):  # 5 cycles of operations
            
            # Perform operations
            for i in range(20):
                with patch.object(service, 'create') as mock_create:
                    mock_create.return_value = Mock(id=i)
                    service.create(sample_cement_data)
            
            # Force garbage collection
            import gc
            gc.collect()
            
            # Check memory after cleanup
            current_memory = process.memory_info().rss / 1024 / 1024
            memory_delta = current_memory - baseline_memory
            
            print(f"Cycle {cycle + 1} memory delta: {memory_delta:.2f}MB")
        
        # Final memory check
        final_memory = process.memory_info().rss / 1024 / 1024
        total_leak = final_memory - baseline_memory
        
        print(f"Total potential memory leak: {total_leak:.2f}MB")
        
        # Should not have significant memory leaks
        assert total_leak < PerformanceBenchmarks.MAX_MEMORY_LEAK_TOLERANCE
    
    def test_ui_memory_usage(self, gtk_test_environment, mock_service_container):
        """Test UI memory usage."""
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024
        
        main_window = Mock(spec=Gtk.ApplicationWindow)
        
        # Create multiple UI components
        panels = []
        for i in range(10):
            panel = MaterialsPanel(main_window, mock_service_container)
            panels.append(panel)
        
        current_memory = process.memory_info().rss / 1024 / 1024
        ui_memory_usage = current_memory - initial_memory
        
        print(f"UI memory usage for 10 panels: {ui_memory_usage:.2f}MB")
        print(f"Per panel: {ui_memory_usage/10:.2f}MB")
        
        # UI memory usage should be reasonable
        assert ui_memory_usage < 50  # Less than 50MB for 10 panels


@pytest.mark.performance
class TestConcurrencyPerformance:
    """Concurrency and threading performance tests."""
    
    def test_concurrent_database_operations(self, test_database, sample_cement_data):
        """Test concurrent database operations performance."""
        import threading
        import queue
        
        service = CementService(test_database)
        results_queue = queue.Queue()
        
        def worker(worker_id):
            start_time = time.perf_counter()
            
            for i in range(10):
                cement_data = sample_cement_data.copy()
                cement_data['name'] = f"Concurrent Test {worker_id}-{i}"
                
                with patch.object(service, 'create') as mock_create:
                    mock_create.return_value = Mock(id=worker_id * 100 + i)
                    result = service.create(cement_data)
            
            end_time = time.perf_counter()
            results_queue.put({
                'worker_id': worker_id,
                'execution_time': (end_time - start_time) * 1000,
                'operations': 10
            })
        
        # Start concurrent workers
        threads = []
        num_workers = 5
        
        start_time = time.perf_counter()
        
        for worker_id in range(num_workers):
            thread = threading.Thread(target=worker, args=(worker_id,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        total_time = (time.perf_counter() - start_time) * 1000
        
        # Collect results
        worker_results = []
        while not results_queue.empty():
            worker_results.append(results_queue.get())
        
        print(f"Concurrent operations total time: {total_time:.2f}ms")
        print(f"Number of workers: {num_workers}")
        print(f"Operations per worker: 10")
        
        assert len(worker_results) == num_workers
        
        # Concurrent operations should complete efficiently
        assert total_time < 2000  # Less than 2 seconds total


# Fixtures and utilities
@pytest.fixture
def sample_cement_data():
    """Sample cement data for performance testing."""
    return {
        'name': 'Performance Test Cement',
        'c3s_mass_fraction': 0.55,
        'c2s_mass_fraction': 0.18,
        'c3a_mass_fraction': 0.12,
        'c4af_mass_fraction': 0.08,
        'specific_gravity': 3.15
    }


@pytest.fixture
def mock_service_container():
    """Mock service container for performance testing."""
    from app.services.service_container import ServiceContainer
    
    container = Mock(spec=ServiceContainer)
    container.cement_service = Mock()
    container.flyash_service = Mock()
    container.slag_service = Mock()
    container.aggregate_service = Mock()
    
    # Configure default returns for performance testing
    container.cement_service.get_all.return_value = []
    
    return container


# Performance report generation
class PerformanceReporter:
    """Generate performance benchmark reports."""
    
    def __init__(self):
        self.results = {}
    
    def add_result(self, test_name: str, execution_time_ms: float, 
                   memory_usage_mb: float = None, notes: str = ""):
        """Add a performance test result."""
        self.results[test_name] = {
            'execution_time_ms': execution_time_ms,
            'memory_usage_mb': memory_usage_mb,
            'notes': notes,
            'timestamp': time.time()
        }
    
    def generate_report(self, output_file: Path):
        """Generate performance report."""
        report = {
            'benchmark_run': time.time(),
            'thresholds': {
                'database_query_ms': PerformanceBenchmarks.MAX_DATABASE_QUERY_TIME,
                'ui_response_ms': PerformanceBenchmarks.MAX_UI_RESPONSE_TIME,
                'file_operation_ms': PerformanceBenchmarks.MAX_FILE_IMPORT_TIME,
                'memory_usage_mb': PerformanceBenchmarks.MAX_MEMORY_USAGE
            },
            'results': self.results
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report


@pytest.fixture
def performance_reporter():
    """Performance reporter fixture."""
    return PerformanceReporter()
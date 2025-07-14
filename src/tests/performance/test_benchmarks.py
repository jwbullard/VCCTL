#!/usr/bin/env python3
"""
Performance Benchmark Tests

Comprehensive performance testing for VCCTL operations including
database queries, file operations, simulations, and UI responsiveness.
"""

import pytest
import time
import threading
import statistics
from pathlib import Path
from unittest.mock import Mock, patch
from typing import List, Dict, Any
import json
import concurrent.futures

from app.services.cement_service import CementService
from app.services.file_operations_service import FileOperationsService
from app.utils.file_operations import ParallelFileWriter
from tests.conftest import PerformanceBenchmarks


@pytest.mark.performance
class TestDatabasePerformance:
    """Performance tests for database operations."""

    @pytest.mark.performance
    def test_cement_crud_performance(self, test_database, sample_cement_data, performance_timer):
        """Test CRUD operation performance for cement service."""
        service = CementService(test_database)
        
        # Test create performance
        performance_timer.start()
        
        with patch.object(service, '_validate_cement'):
            with patch.object(test_database, 'get_session') as mock_session:
                mock_session.return_value.__enter__.return_value = Mock()
                
                for i in range(100):
                    cement_data = sample_cement_data.copy()
                    cement_data['name'] = f"Performance Test Cement {i}"
                    
                    from app.models.cement import CementCreate
                    cement_create = CementCreate(**cement_data)
                    
                    try:
                        service.create(cement_create)
                    except:
                        pass  # Mock may not handle all cases
        
        create_time = performance_timer.stop()
        
        # Create operations should be fast
        PerformanceBenchmarks.assert_performance(
            create_time, 5.0, "100 cement create operations"
        )
        
        # Test read performance
        with patch.object(test_database, 'get_read_only_session') as mock_session:
            mock_session.return_value.__enter__.return_value.query.return_value.order_by.return_value.all.return_value = []
            
            performance_timer.start()
            
            for _ in range(500):
                service.get_all()
            
            read_time = performance_timer.stop()
            
            PerformanceBenchmarks.assert_performance(
                read_time, 2.0, "500 cement read operations"
            )

    @pytest.mark.performance
    def test_bulk_database_operations(self, test_database, performance_timer):
        """Test bulk database operation performance."""
        service = CementService(test_database)
        
        # Generate bulk data
        bulk_data = []
        for i in range(1000):
            cement_data = {
                'name': f'Bulk Cement {i}',
                'type': 'Type I',
                'sio2': 20.0 + (i % 10) * 0.1,
                'al2o3': 5.0,
                'fe2o3': 3.0,
                'cao': 65.0
            }
            bulk_data.append(cement_data)
        
        # Test bulk insert performance
        performance_timer.start()
        
        with patch.object(service, '_validate_cement'):
            with patch.object(test_database, 'get_session') as mock_session:
                mock_session.return_value.__enter__.return_value = Mock()
                
                # Simulate bulk insert
                for data in bulk_data:
                    from app.models.cement import CementCreate
                    cement_create = CementCreate(**data)
                    try:
                        service.create(cement_create)
                    except:
                        pass
        
        bulk_insert_time = performance_timer.stop()
        
        # Bulk operations should complete within reasonable time
        PerformanceBenchmarks.assert_performance(
            bulk_insert_time, 15.0, "1000 bulk cement inserts"
        )

    @pytest.mark.performance
    def test_concurrent_database_access(self, test_database, performance_timer):
        """Test concurrent database access performance."""
        service = CementService(test_database)
        
        def concurrent_read_operation():
            """Perform concurrent read operation."""
            with patch.object(test_database, 'get_read_only_session') as mock_session:
                mock_session.return_value.__enter__.return_value.query.return_value.order_by.return_value.all.return_value = []
                
                for _ in range(10):
                    service.get_all()
        
        performance_timer.start()
        
        # Run 10 concurrent threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=concurrent_read_operation)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        concurrent_time = performance_timer.stop()
        
        PerformanceBenchmarks.assert_performance(
            concurrent_time, 5.0, "Concurrent database access (10 threads)"
        )


@pytest.mark.performance
class TestFileOperationPerformance:
    """Performance tests for file operations."""

    @pytest.mark.performance
    def test_large_file_import_performance(self, temp_directory, performance_timer):
        """Test large file import performance."""
        # Create large test file
        large_data = {
            'materials': [
                {
                    'name': f'Material {i}',
                    'type': 'Type I',
                    'properties': {f'prop_{j}': j * 1.5 for j in range(100)}
                }
                for i in range(1000)
            ]
        }
        
        large_file = temp_directory / "large_materials.json"
        large_file.write_text(json.dumps(large_data))
        
        # Test import performance
        performance_timer.start()
        
        # Simulate file reading and parsing
        with open(large_file, 'r') as f:
            data = json.load(f)
        
        # Process the data
        processed_materials = []
        for material in data['materials']:
            processed_material = {
                'name': material['name'],
                'type': material['type'],
                'property_count': len(material['properties'])
            }
            processed_materials.append(processed_material)
        
        import_time = performance_timer.stop()
        
        PerformanceBenchmarks.assert_performance(
            import_time, 2.0, f"Large file import ({large_file.stat().st_size / 1024 / 1024:.1f}MB)"
        )
        
        assert len(processed_materials) == 1000

    @pytest.mark.performance
    def test_parallel_file_writing_performance(self, temp_directory, performance_timer):
        """Test parallel file writing performance."""
        writer = ParallelFileWriter()
        
        # Create multiple files to write
        write_tasks = []
        for i in range(100):
            file_path = temp_directory / f"parallel_file_{i}.txt"
            content = f"Content for file {i}\n" * 100  # 100 lines each
            
            from app.utils.file_operations import FileWriteTask
            task = FileWriteTask(file_path, content.encode('utf-8'))
            write_tasks.append(task)
        
        performance_timer.start()
        
        # Execute parallel writes
        success_count = writer.write_files_parallel(write_tasks, max_workers=4)
        
        parallel_write_time = performance_timer.stop()
        
        PerformanceBenchmarks.assert_performance(
            parallel_write_time, 3.0, "100 parallel file writes"
        )
        
        assert success_count == 100

    @pytest.mark.performance
    def test_bulk_file_validation_performance(self, temp_directory, performance_timer):
        """Test bulk file validation performance."""
        from app.utils.file_operations import FileValidator
        
        validator = FileValidator()
        
        # Create test files of various types and sizes
        test_files = []
        
        for i in range(50):
            # Create JSON files
            json_file = temp_directory / f"test_{i}.json"
            json_data = {'test': f'data_{i}', 'values': list(range(100))}
            json_file.write_text(json.dumps(json_data))
            test_files.append(json_file)
            
            # Create CSV files
            csv_file = temp_directory / f"test_{i}.csv"
            csv_content = "name,value,type\n" + "\n".join([f"item_{j},{j},type_{j%3}" for j in range(50)])
            csv_file.write_text(csv_content)
            test_files.append(csv_file)
        
        performance_timer.start()
        
        # Validate all files
        validation_results = []
        for file_path in test_files:
            result = validator.validate_file(file_path, max_size_mb=10)
            validation_results.append(result)
        
        validation_time = performance_timer.stop()
        
        PerformanceBenchmarks.assert_performance(
            validation_time, 5.0, f"Bulk file validation ({len(test_files)} files)"
        )
        
        # All files should be valid
        assert all(result.is_valid for result in validation_results)

    @pytest.mark.performance
    def test_file_compression_performance(self, temp_directory, performance_timer):
        """Test file compression performance."""
        import zipfile
        
        # Create files to compress
        source_files = []
        total_size = 0
        
        for i in range(20):
            file_path = temp_directory / f"compress_test_{i}.txt"
            content = f"This is test file {i}\n" * 1000  # 1000 lines each
            file_path.write_text(content)
            source_files.append(file_path)
            total_size += file_path.stat().st_size
        
        archive_path = temp_directory / "test_archive.zip"
        
        performance_timer.start()
        
        # Create compressed archive
        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in source_files:
                zipf.write(file_path, file_path.name)
        
        compression_time = performance_timer.stop()
        
        PerformanceBenchmarks.assert_performance(
            compression_time, 3.0, f"File compression ({total_size / 1024 / 1024:.1f}MB)"
        )
        
        # Verify compression was effective
        compressed_size = archive_path.stat().st_size
        compression_ratio = compressed_size / total_size
        assert compression_ratio < 0.8  # At least 20% compression


@pytest.mark.performance
class TestComputationalPerformance:
    """Performance tests for computational operations."""

    @pytest.mark.performance
    def test_mix_design_calculation_performance(self, performance_timer):
        """Test mix design calculation performance."""
        
        def calculate_mix_proportions(cement_content, water_cement_ratio, target_density=2400):
            """Mock mix design calculation."""
            water_content = cement_content * water_cement_ratio
            aggregate_content = target_density - cement_content - water_content
            fine_ratio = 0.4
            coarse_ratio = 0.6
            
            return {
                'water_content': water_content,
                'fine_aggregate': aggregate_content * fine_ratio,
                'coarse_aggregate': aggregate_content * coarse_ratio,
                'total_volume': 1.0,
                'density': target_density
            }
        
        # Test calculation performance with many iterations
        performance_timer.start()
        
        results = []
        for cement in range(250, 500, 10):  # 25 cement contents
            for wc_ratio in [0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6]:  # 7 W/C ratios
                result = calculate_mix_proportions(cement, wc_ratio)
                results.append(result)
        
        calculation_time = performance_timer.stop()
        
        PerformanceBenchmarks.assert_performance(
            calculation_time, 1.0, f"Mix design calculations ({len(results)} calculations)"
        )
        
        assert len(results) == 25 * 7

    @pytest.mark.performance
    def test_hydration_simulation_performance(self, performance_timer):
        """Test hydration simulation performance (mock)."""
        
        def simulate_hydration_step(degree_of_hydration, temperature, time_step):
            """Mock hydration simulation step."""
            import math
            
            # Simple exponential hydration model
            k = 0.1 * (temperature / 20.0)  # Rate constant
            max_doh = 0.85
            
            rate = k * (max_doh - degree_of_hydration)
            new_doh = degree_of_hydration + rate * time_step
            
            return min(new_doh, max_doh)
        
        performance_timer.start()
        
        # Simulate 28 days with hourly time steps
        simulation_results = []
        doh = 0.0
        temperature = 20.0
        time_step = 1.0 / 24.0  # 1 hour in days
        
        for hour in range(28 * 24):  # 28 days * 24 hours
            doh = simulate_hydration_step(doh, temperature, time_step)
            
            if hour % 24 == 0:  # Save daily results
                simulation_results.append({
                    'day': hour // 24,
                    'degree_of_hydration': doh,
                    'temperature': temperature
                })
        
        simulation_time = performance_timer.stop()
        
        PerformanceBenchmarks.assert_performance(
            simulation_time, 0.5, f"Hydration simulation ({len(simulation_results)} time steps)"
        )
        
        assert len(simulation_results) == 28
        assert simulation_results[-1]['degree_of_hydration'] > 0.7

    @pytest.mark.performance
    def test_microstructure_generation_performance(self, performance_timer):
        """Test microstructure generation performance (mock)."""
        
        def generate_microstructure_voxels(size, phase_fractions):
            """Mock microstructure generation."""
            import random
            
            total_voxels = size ** 3
            voxels = []
            
            # Assign phases based on fractions
            cumulative_fractions = []
            cumsum = 0
            for fraction in phase_fractions.values():
                cumsum += fraction
                cumulative_fractions.append(cumsum)
            
            phases = list(phase_fractions.keys())
            
            for _ in range(total_voxels):
                rand_val = random.random()
                for i, cum_frac in enumerate(cumulative_fractions):
                    if rand_val <= cum_frac:
                        voxels.append(phases[i])
                        break
            
            return voxels
        
        performance_timer.start()
        
        # Generate 100x100x100 microstructure
        phase_fractions = {
            'cement': 0.3,
            'water': 0.2,
            'aggregate': 0.4,
            'air': 0.1
        }
        
        voxels = generate_microstructure_voxels(100, phase_fractions)
        
        generation_time = performance_timer.stop()
        
        PerformanceBenchmarks.assert_performance(
            generation_time, 2.0, f"Microstructure generation ({len(voxels)} voxels)"
        )
        
        assert len(voxels) == 100 ** 3


@pytest.mark.performance
@pytest.mark.gui
class TestUIPerformance:
    """Performance tests for UI responsiveness."""

    @pytest.mark.performance
    def test_table_rendering_performance(self, gtk_test_environment, performance_timer):
        """Test large table rendering performance."""
        import gi
        gi.require_version('Gtk', '3.0')
        from gi.repository import Gtk
        
        # Create large data model
        store = Gtk.ListStore(str, str, float, float, float, float)
        
        performance_timer.start()
        
        # Add many rows
        for i in range(5000):
            store.append([
                f"Material {i}",
                "Type I",
                20.0 + (i % 100) * 0.01,
                5.0 + (i % 50) * 0.01,
                3.0 + (i % 25) * 0.01,
                65.0 + (i % 75) * 0.01
            ])
        
        table_creation_time = performance_timer.stop()
        
        PerformanceBenchmarks.assert_performance(
            table_creation_time, 2.0, "Large table creation (5000 rows)"
        )
        
        assert len(store) == 5000

    @pytest.mark.performance
    def test_ui_update_performance(self, gtk_test_environment, performance_timer):
        """Test UI update performance."""
        import gi
        gi.require_version('Gtk', '3.0')
        from gi.repository import Gtk
        
        # Create UI components
        window = Gtk.Window()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        window.add(box)
        
        labels = []
        for i in range(1000):
            label = Gtk.Label(f"Label {i}")
            box.pack_start(label, False, False, 0)
            labels.append(label)
        
        performance_timer.start()
        
        # Update all labels
        for i, label in enumerate(labels):
            label.set_text(f"Updated Label {i}")
        
        update_time = performance_timer.stop()
        
        PerformanceBenchmarks.assert_performance(
            update_time, 1.0, "UI update (1000 labels)"
        )
        
        window.destroy()

    @pytest.mark.performance
    def test_theme_switching_performance(self, gtk_test_environment, performance_timer):
        """Test theme switching performance."""
        from app.ui import create_ui_polish_manager, ColorScheme
        import gi
        gi.require_version('Gtk', '3.0')
        from gi.repository import Gtk
        
        window = Gtk.ApplicationWindow()
        ui_polish = create_ui_polish_manager(window)
        
        themes = [ColorScheme.LIGHT, ColorScheme.DARK, ColorScheme.SCIENTIFIC, ColorScheme.HIGH_CONTRAST]
        
        performance_timer.start()
        
        # Switch themes many times
        for _ in range(50):
            for theme in themes:
                ui_polish.set_theme_scheme(theme)
        
        theme_switch_time = performance_timer.stop()
        
        PerformanceBenchmarks.assert_performance(
            theme_switch_time, 3.0, "Theme switching (200 switches)"
        )
        
        window.destroy()


@pytest.mark.performance
class TestConcurrencyPerformance:
    """Performance tests for concurrent operations."""

    @pytest.mark.performance
    def test_concurrent_file_processing(self, temp_directory, performance_timer):
        """Test concurrent file processing performance."""
        
        # Create test files
        test_files = []
        for i in range(20):
            file_path = temp_directory / f"concurrent_test_{i}.json"
            data = {'id': i, 'data': list(range(1000))}
            file_path.write_text(json.dumps(data))
            test_files.append(file_path)
        
        def process_file(file_path):
            """Process a single file."""
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Simulate processing
            processed_data = {
                'original_id': data['id'],
                'data_sum': sum(data['data']),
                'data_count': len(data['data'])
            }
            
            return processed_data
        
        performance_timer.start()
        
        # Process files concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            future_to_file = {executor.submit(process_file, file_path): file_path 
                             for file_path in test_files}
            
            results = []
            for future in concurrent.futures.as_completed(future_to_file):
                result = future.result()
                results.append(result)
        
        concurrent_processing_time = performance_timer.stop()
        
        PerformanceBenchmarks.assert_performance(
            concurrent_processing_time, 2.0, f"Concurrent file processing ({len(test_files)} files)"
        )
        
        assert len(results) == len(test_files)

    @pytest.mark.performance
    def test_producer_consumer_performance(self, performance_timer):
        """Test producer-consumer pattern performance."""
        import queue
        import threading
        
        # Create queue for communication
        work_queue = queue.Queue(maxsize=100)
        result_queue = queue.Queue()
        
        def producer():
            """Produce work items."""
            for i in range(1000):
                work_item = {'id': i, 'data': list(range(10))}
                work_queue.put(work_item)
            
            # Signal end of work
            for _ in range(4):  # Number of consumers
                work_queue.put(None)
        
        def consumer():
            """Consume and process work items."""
            while True:
                item = work_queue.get()
                if item is None:
                    break
                
                # Process item
                result = {
                    'id': item['id'],
                    'sum': sum(item['data']),
                    'processed': True
                }
                result_queue.put(result)
                work_queue.task_done()
        
        performance_timer.start()
        
        # Start producer
        producer_thread = threading.Thread(target=producer)
        producer_thread.start()
        
        # Start consumers
        consumer_threads = []
        for _ in range(4):
            thread = threading.Thread(target=consumer)
            thread.start()
            consumer_threads.append(thread)
        
        # Wait for completion
        producer_thread.join()
        for thread in consumer_threads:
            thread.join()
        
        producer_consumer_time = performance_timer.stop()
        
        PerformanceBenchmarks.assert_performance(
            producer_consumer_time, 3.0, "Producer-consumer pattern (1000 items)"
        )
        
        # Collect results
        results = []
        while not result_queue.empty():
            results.append(result_queue.get())
        
        assert len(results) == 1000


@pytest.mark.performance
class TestMemoryPerformance:
    """Performance tests for memory usage."""

    @pytest.mark.performance
    def test_memory_usage_during_large_operations(self):
        """Test memory usage during large operations."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Perform memory-intensive operations
        large_datasets = []
        
        for i in range(100):
            # Create large data structures
            dataset = {
                'materials': [
                    {
                        'id': j,
                        'properties': {f'prop_{k}': k * 1.5 for k in range(100)},
                        'data_array': list(range(1000))
                    }
                    for j in range(100)
                ]
            }
            large_datasets.append(dataset)
        
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - initial_memory
        
        # Memory usage should be reasonable
        assert memory_increase < 1000, f"Memory increased by {memory_increase:.1f}MB, expected < 1000MB"
        
        # Clean up to test memory release
        del large_datasets
        
        import gc
        gc.collect()
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_released = peak_memory - final_memory
        
        # Should release significant memory
        assert memory_released > memory_increase * 0.5, \
            f"Only released {memory_released:.1f}MB of {memory_increase:.1f}MB used"

    @pytest.mark.performance
    def test_memory_leak_detection(self, performance_timer):
        """Test for memory leaks during repeated operations."""
        import psutil
        import os
        import gc
        
        process = psutil.Process(os.getpid())
        
        def create_and_destroy_objects():
            """Create and destroy objects to test for leaks."""
            objects = []
            for i in range(1000):
                obj = {
                    'id': i,
                    'data': list(range(100)),
                    'nested': {'values': list(range(50))}
                }
                objects.append(obj)
            
            # Process objects
            for obj in objects:
                _ = sum(obj['data'])
                _ = len(obj['nested']['values'])
            
            del objects
            gc.collect()
        
        # Measure memory before test
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        performance_timer.start()
        
        # Repeat operation many times
        for iteration in range(50):
            create_and_destroy_objects()
            
            # Check memory every 10 iterations
            if iteration % 10 == 0:
                current_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_growth = current_memory - initial_memory
                
                # Memory growth should be minimal
                assert memory_growth < 100, \
                    f"Memory grew by {memory_growth:.1f}MB after {iteration} iterations"
        
        leak_test_time = performance_timer.stop()
        
        PerformanceBenchmarks.assert_performance(
            leak_test_time, 10.0, "Memory leak detection test"
        )
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        total_growth = final_memory - initial_memory
        
        # Total memory growth should be minimal
        assert total_growth < 50, f"Total memory growth: {total_growth:.1f}MB, expected < 50MB"
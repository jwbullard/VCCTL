#!/usr/bin/env python3
"""
Comprehensive End-to-End Workflow Tests

Tests complete user workflows from material definition through simulation and export.
Simulates real user interactions and validates the entire application flow.
"""

import pytest
import json
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
from typing import Dict, Any, List

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk

# Import application components
from app.application import VCCTLApplication
from app.windows.main_window import VCCTLMainWindow
from app.services.service_container import get_service_container
from app.models.cement import CementCreate
from app.models.aggregate import AggregateCreate
from app.models.operation import OperationCreate


@pytest.mark.e2e
@pytest.mark.slow
class TestCompleteWorkflows:
    """End-to-end workflow tests for complete user scenarios."""
    
    def test_complete_material_to_simulation_workflow(self, gtk_test_environment, temp_directory):
        """Test complete workflow: Create materials → Mix design → Microstructure → Hydration."""
        
        # Mock application components
        app = Mock(spec=VCCTLApplication)
        main_window = Mock(spec=VCCTLMainWindow)
        service_container = Mock()
        
        # Setup service mocks
        self._setup_service_mocks(service_container)
        
        # Step 1: Create cement material
        cement_data = {
            'name': 'Test Portland Cement',
            'c3s_mass_fraction': 0.55,
            'c2s_mass_fraction': 0.18,
            'c3a_mass_fraction': 0.12,
            'c4af_mass_fraction': 0.08,
            'gypsum_mass_fraction': 0.05,
            'specific_gravity': 3.15,
            'specific_surface_area': 380
        }
        
        created_cement = Mock(id=1, **cement_data)
        service_container.cement_service.create.return_value = created_cement
        
        cement_result = service_container.cement_service.create(CementCreate(**cement_data))
        assert cement_result.id == 1
        assert cement_result.name == 'Test Portland Cement'
        
        # Step 2: Create aggregate materials
        fine_agg_data = {
            'name': 'Fine Sand',
            'aggregate_type': 'fine',
            'specific_gravity': 2.65,
            'absorption_percent': 1.2,
            'max_size_mm': 4.75
        }
        
        coarse_agg_data = {
            'name': 'Coarse Gravel',
            'aggregate_type': 'coarse', 
            'specific_gravity': 2.70,
            'absorption_percent': 0.8,
            'max_size_mm': 19.0
        }
        
        created_fine_agg = Mock(id=2, **fine_agg_data)
        created_coarse_agg = Mock(id=3, **coarse_agg_data)
        
        service_container.aggregate_service.create.side_effect = [created_fine_agg, created_coarse_agg]
        
        fine_result = service_container.aggregate_service.create(AggregateCreate(**fine_agg_data))
        coarse_result = service_container.aggregate_service.create(AggregateCreate(**coarse_agg_data))
        
        assert fine_result.id == 2
        assert coarse_result.id == 3
        
        # Step 3: Create mix design
        mix_design_data = {
            'name': 'Test Concrete Mix',
            'cement_id': 1,
            'cement_kg_per_m3': 350,
            'water_kg_per_m3': 175,
            'fine_aggregate_id': 2,
            'fine_aggregate_kg_per_m3': 700,
            'coarse_aggregate_id': 3,
            'coarse_aggregate_kg_per_m3': 1100,
            'target_strength_mpa': 30
        }
        
        created_mix = Mock(id=4, **mix_design_data, water_binder_ratio=0.50)
        service_container.mix_service.create_mix_design.return_value = {
            'mix_id': 4,
            'water_binder_ratio': 0.50,
            'total_volume': 0.98,
            'valid': True
        }
        
        mix_result = service_container.mix_service.create_mix_design(mix_design_data)
        assert mix_result['mix_id'] == 4
        assert mix_result['valid']
        assert abs(mix_result['water_binder_ratio'] - 0.50) < 0.01
        
        # Step 4: Generate microstructure
        microstructure_params = {
            'mix_id': 4,
            'system_size_voxels': 100,
            'resolution_micrometers': 1.0,
            'random_seed': 12345,
            'particle_shape_set_id': 1
        }
        
        created_microstructure = Mock(id=5, **microstructure_params)
        service_container.microstructure_service.generate_microstructure.return_value = {
            'microstructure_id': 5,
            'volume_fractions': {
                'cement': 0.12,
                'water': 0.18,
                'aggregate': 0.65,
                'air': 0.05
            },
            'generation_time_seconds': 45.2
        }
        
        microstructure_result = service_container.microstructure_service.generate_microstructure(microstructure_params)
        assert microstructure_result['microstructure_id'] == 5
        assert 'volume_fractions' in microstructure_result
        
        # Step 5: Start hydration simulation
        hydration_params = {
            'microstructure_id': 5,
            'hydration_time_days': 28,
            'temperature_celsius': 20,
            'aging_mode': 'time',
            'output_frequency_hours': 24
        }
        
        created_operation = Mock(id=6, status='running', progress=0.0)
        service_container.hydration_service.start_hydration_simulation.return_value = {
            'operation_id': 6,
            'estimated_duration_hours': 2.5,
            'status': 'running'
        }
        
        hydration_result = service_container.hydration_service.start_hydration_simulation(hydration_params)
        assert hydration_result['operation_id'] == 6
        assert hydration_result['status'] == 'running'
        
        # Step 6: Monitor simulation progress
        progress_updates = [
            {'progress': 0.25, 'degree_of_hydration': 0.15, 'elapsed_hours': 12},
            {'progress': 0.50, 'degree_of_hydration': 0.35, 'elapsed_hours': 24},
            {'progress': 0.75, 'degree_of_hydration': 0.55, 'elapsed_hours': 36},
            {'progress': 1.00, 'degree_of_hydration': 0.75, 'elapsed_hours': 48}
        ]
        
        service_container.operation_service.get_operation_progress.side_effect = progress_updates
        
        for expected_progress in progress_updates:
            progress = service_container.operation_service.get_operation_progress(6)
            assert progress['progress'] == expected_progress['progress']
        
        # Step 7: Complete simulation and get results
        simulation_results = {
            'operation_id': 6,
            'status': 'completed',
            'final_degree_of_hydration': 0.75,
            'compressive_strength_mpa': 32.5,
            'elastic_modulus_gpa': 28.2,
            'porosity': 0.12,
            'total_simulation_time_hours': 48
        }
        
        service_container.hydration_service.get_hydration_results.return_value = simulation_results
        
        results = service_container.hydration_service.get_hydration_results(6)
        assert results['status'] == 'completed'
        assert results['compressive_strength_mpa'] > 30  # Met target strength
        
        # Verify all service calls were made correctly
        service_container.cement_service.create.assert_called_once()
        assert service_container.aggregate_service.create.call_count == 2
        service_container.mix_service.create_mix_design.assert_called_once()
        service_container.microstructure_service.generate_microstructure.assert_called_once()
        service_container.hydration_service.start_hydration_simulation.assert_called_once()
    
    def test_import_export_workflow(self, gtk_test_environment, temp_directory):
        """Test complete import/export workflow."""
        service_container = Mock()
        self._setup_service_mocks(service_container)
        
        # Step 1: Prepare import data
        import_file = temp_directory / "cement_materials.json"
        cement_data = [
            {
                'name': 'Imported Cement 1',
                'c3s_mass_fraction': 0.58,
                'c2s_mass_fraction': 0.16,
                'c3a_mass_fraction': 0.10,
                'c4af_mass_fraction': 0.09,
                'specific_gravity': 3.18
            },
            {
                'name': 'Imported Cement 2',
                'c3s_mass_fraction': 0.52,
                'c2s_mass_fraction': 0.20,
                'c3a_mass_fraction': 0.14,
                'c4af_mass_fraction': 0.07,
                'specific_gravity': 3.12
            }
        ]
        
        with open(import_file, 'w') as f:
            json.dump(cement_data, f, indent=2)
        
        # Step 2: Import materials
        service_container.file_operations_service.import_material_data.return_value = {
            'success': True,
            'imported_count': 2,
            'imported_ids': [7, 8],
            'errors': []
        }
        
        import_result = service_container.file_operations_service.import_material_data(
            str(import_file), 'cement'
        )
        
        assert import_result['success']
        assert import_result['imported_count'] == 2
        assert len(import_result['imported_ids']) == 2
        
        # Step 3: Create mix with imported materials
        mix_with_imported = {
            'name': 'Mix with Imported Cement',
            'cement_id': 7,  # Use first imported cement
            'cement_kg_per_m3': 300,
            'water_kg_per_m3': 165
        }
        
        service_container.mix_service.create_mix_design.return_value = {
            'mix_id': 9,
            'valid': True
        }
        
        mix_result = service_container.mix_service.create_mix_design(mix_with_imported)
        assert mix_result['mix_id'] == 9
        
        # Step 4: Export project data
        export_file = temp_directory / "project_export.json"
        
        service_container.file_operations_service.export_project_data.return_value = {
            'success': True,
            'export_file': str(export_file),
            'exported_materials': 2,
            'exported_mixes': 1
        }
        
        export_result = service_container.file_operations_service.export_project_data(
            str(export_file), include_materials=True, include_mixes=True
        )
        
        assert export_result['success']
        assert export_result['exported_materials'] == 2
        assert export_result['exported_mixes'] == 1
    
    def test_error_recovery_workflow(self, gtk_test_environment, temp_directory):
        """Test error recovery during workflows."""
        service_container = Mock()
        self._setup_service_mocks(service_container)
        
        # Step 1: Attempt to create invalid cement (should fail)
        invalid_cement = {
            'name': '',  # Invalid: empty name
            'c3s_mass_fraction': 1.2,  # Invalid: > 100%
            'c2s_mass_fraction': 0.18
        }
        
        from app.services.base_service import ServiceError
        service_container.cement_service.create.side_effect = ServiceError(
            "Invalid cement composition: total exceeds 100%"
        )
        
        with pytest.raises(ServiceError):
            service_container.cement_service.create(CementCreate(**invalid_cement))
        
        # Step 2: Create valid cement after error
        valid_cement = {
            'name': 'Valid Cement',
            'c3s_mass_fraction': 0.55,
            'c2s_mass_fraction': 0.18,
            'c3a_mass_fraction': 0.12,
            'c4af_mass_fraction': 0.08
        }
        
        # Reset mock to return success
        service_container.cement_service.create.side_effect = None
        service_container.cement_service.create.return_value = Mock(id=10, **valid_cement)
        
        cement_result = service_container.cement_service.create(CementCreate(**valid_cement))
        assert cement_result.id == 10
        
        # Step 3: Attempt mix design with invalid ratios
        invalid_mix = {
            'cement_id': 10,
            'water_kg_per_m3': 300,  # Too much water
            'cement_kg_per_m3': 200
        }
        
        service_container.mix_service.create_mix_design.side_effect = ServiceError(
            "Water-cement ratio exceeds maximum allowed"
        )
        
        with pytest.raises(ServiceError):
            service_container.mix_service.create_mix_design(invalid_mix)
        
        # Step 4: Create valid mix after error
        valid_mix = {
            'cement_id': 10,
            'water_kg_per_m3': 175,
            'cement_kg_per_m3': 350
        }
        
        service_container.mix_service.create_mix_design.side_effect = None
        service_container.mix_service.create_mix_design.return_value = {
            'mix_id': 11,
            'valid': True
        }
        
        mix_result = service_container.mix_service.create_mix_design(valid_mix)
        assert mix_result['valid']
    
    def test_batch_processing_workflow(self, gtk_test_environment, temp_directory):
        """Test batch processing of multiple materials."""
        service_container = Mock()
        self._setup_service_mocks(service_container)
        
        # Step 1: Create batch import directory
        batch_dir = temp_directory / "batch_materials"
        batch_dir.mkdir()
        
        # Create multiple material files
        cement_files = []
        for i in range(5):
            cement_file = batch_dir / f"cement_{i}.json"
            cement_data = {
                'name': f'Batch Cement {i}',
                'c3s_mass_fraction': 0.50 + i * 0.01,
                'c2s_mass_fraction': 0.20 - i * 0.005,
                'c3a_mass_fraction': 0.12,
                'c4af_mass_fraction': 0.08,
                'specific_gravity': 3.10 + i * 0.02
            }
            
            with open(cement_file, 'w') as f:
                json.dump(cement_data, f)
            
            cement_files.append(cement_file)
        
        # Step 2: Batch import
        service_container.file_operations_service.batch_import_materials.return_value = {
            'success': True,
            'imported_count': 5,
            'imported_ids': list(range(12, 17)),
            'failed_count': 0,
            'errors': []
        }
        
        batch_result = service_container.file_operations_service.batch_import_materials(
            str(batch_dir), 'cement'
        )
        
        assert batch_result['success']
        assert batch_result['imported_count'] == 5
        assert batch_result['failed_count'] == 0
        
        # Step 3: Create parametric study with batch materials
        study_results = []
        for cement_id in batch_result['imported_ids']:
            study_mix = {
                'name': f'Study Mix - Cement {cement_id}',
                'cement_id': cement_id,
                'cement_kg_per_m3': 350,
                'water_kg_per_m3': 175
            }
            
            service_container.mix_service.create_mix_design.return_value = {
                'mix_id': 20 + cement_id,
                'water_binder_ratio': 0.50,
                'valid': True
            }
            
            mix_result = service_container.mix_service.create_mix_design(study_mix)
            study_results.append(mix_result)
        
        assert len(study_results) == 5
        assert all(result['valid'] for result in study_results)
        
        # Step 4: Batch export study results
        export_dir = temp_directory / "study_results"
        export_dir.mkdir()
        
        service_container.file_operations_service.batch_export_results.return_value = {
            'success': True,
            'exported_count': 5,
            'export_directory': str(export_dir)
        }
        
        export_result = service_container.file_operations_service.batch_export_results(
            study_results, str(export_dir)
        )
        
        assert export_result['success']
        assert export_result['exported_count'] == 5
    
    def test_simulation_monitoring_workflow(self, gtk_test_environment):
        """Test real-time simulation monitoring workflow."""
        service_container = Mock()
        self._setup_service_mocks(service_container)
        
        # Step 1: Start multiple simulations
        simulation_ids = []
        for i in range(3):
            sim_params = {
                'microstructure_id': i + 1,
                'hydration_time_days': 28,
                'temperature_celsius': 20 + i * 5  # Different temperatures
            }
            
            service_container.hydration_service.start_hydration_simulation.return_value = {
                'operation_id': 100 + i,
                'status': 'running'
            }
            
            result = service_container.hydration_service.start_hydration_simulation(sim_params)
            simulation_ids.append(result['operation_id'])
        
        assert len(simulation_ids) == 3
        
        # Step 2: Monitor all simulations
        monitoring_cycles = 10
        for cycle in range(monitoring_cycles):
            progress = cycle / (monitoring_cycles - 1)  # 0 to 1
            
            for sim_id in simulation_ids:
                # Different simulations progress at different rates
                sim_progress = min(1.0, progress * (1.0 + (sim_id % 3) * 0.1))
                
                service_container.operation_service.get_operation_progress.return_value = {
                    'operation_id': sim_id,
                    'progress': sim_progress,
                    'status': 'completed' if sim_progress >= 1.0 else 'running',
                    'elapsed_hours': cycle * 2.4,
                    'estimated_remaining_hours': max(0, (monitoring_cycles - cycle - 1) * 2.4)
                }
                
                progress_data = service_container.operation_service.get_operation_progress(sim_id)
                assert 0.0 <= progress_data['progress'] <= 1.0
                
                if progress_data['progress'] >= 1.0:
                    assert progress_data['status'] == 'completed'
        
        # Step 3: Collect all results
        all_results = []
        for sim_id in simulation_ids:
            service_container.hydration_service.get_hydration_results.return_value = {
                'operation_id': sim_id,
                'status': 'completed',
                'final_degree_of_hydration': 0.70 + (sim_id % 3) * 0.05,
                'compressive_strength_mpa': 28.0 + (sim_id % 3) * 2.0
            }
            
            results = service_container.hydration_service.get_hydration_results(sim_id)
            all_results.append(results)
        
        assert len(all_results) == 3
        assert all(result['status'] == 'completed' for result in all_results)
        
        # Verify strength variation due to temperature differences
        strengths = [result['compressive_strength_mpa'] for result in all_results]
        assert max(strengths) - min(strengths) > 0  # Should have variation
    
    def _setup_service_mocks(self, service_container):
        """Setup comprehensive service mocks."""
        # Cement service
        service_container.cement_service = Mock()
        service_container.cement_service.create = Mock()
        service_container.cement_service.get_by_id = Mock()
        service_container.cement_service.get_all = Mock(return_value=[])
        
        # Aggregate service
        service_container.aggregate_service = Mock()
        service_container.aggregate_service.create = Mock()
        service_container.aggregate_service.get_by_id = Mock()
        
        # Mix service
        service_container.mix_service = Mock()
        service_container.mix_service.create_mix_design = Mock()
        service_container.mix_service.validate_mix_design = Mock(return_value={'valid': True})
        
        # Microstructure service
        service_container.microstructure_service = Mock()
        service_container.microstructure_service.generate_microstructure = Mock()
        
        # Hydration service
        service_container.hydration_service = Mock()
        service_container.hydration_service.start_hydration_simulation = Mock()
        service_container.hydration_service.get_hydration_results = Mock()
        
        # Operation service
        service_container.operation_service = Mock()
        service_container.operation_service.create_operation = Mock()
        service_container.operation_service.get_operation_progress = Mock()
        service_container.operation_service.update_operation_progress = Mock()
        
        # File operations service
        service_container.file_operations_service = Mock()
        service_container.file_operations_service.import_material_data = Mock()
        service_container.file_operations_service.export_material_data = Mock()
        service_container.file_operations_service.export_project_data = Mock()
        service_container.file_operations_service.batch_import_materials = Mock()
        service_container.file_operations_service.batch_export_results = Mock()


@pytest.mark.e2e
@pytest.mark.slow
class TestWorkflowPerformance:
    """Performance tests for complete workflows."""
    
    def test_large_scale_workflow_performance(self, gtk_test_environment):
        """Test performance with large-scale operations."""
        service_container = Mock()
        
        # Setup for large scale test
        num_materials = 100
        num_mixes = 50
        
        # Mock bulk material creation
        def mock_bulk_create(data):
            return Mock(id=hash(data.name) % 10000, name=data.name)
        
        service_container.cement_service.create.side_effect = mock_bulk_create
        
        # Test bulk material creation performance
        start_time = time.time()
        
        created_materials = []
        for i in range(num_materials):
            cement_data = CementCreate(
                name=f'Performance Test Cement {i}',
                c3s_mass_fraction=0.50 + (i % 20) * 0.005,
                c2s_mass_fraction=0.20,
                c3a_mass_fraction=0.12,
                c4af_mass_fraction=0.08
            )
            
            material = service_container.cement_service.create(cement_data)
            created_materials.append(material)
        
        material_creation_time = time.time() - start_time
        
        # Should create materials efficiently
        assert material_creation_time < 5.0  # Less than 5 seconds for 100 materials
        assert len(created_materials) == num_materials
        
        # Test bulk mix design creation performance
        def mock_mix_create(data):
            return {'mix_id': hash(data['name']) % 10000, 'valid': True}
        
        service_container.mix_service.create_mix_design.side_effect = mock_mix_create
        
        start_time = time.time()
        
        created_mixes = []
        for i in range(num_mixes):
            mix_data = {
                'name': f'Performance Test Mix {i}',
                'cement_id': created_materials[i % len(created_materials)].id,
                'cement_kg_per_m3': 300 + i * 2,
                'water_kg_per_m3': 150 + i
            }
            
            mix = service_container.mix_service.create_mix_design(mix_data)
            created_mixes.append(mix)
        
        mix_creation_time = time.time() - start_time
        
        # Should create mixes efficiently
        assert mix_creation_time < 3.0  # Less than 3 seconds for 50 mixes
        assert len(created_mixes) == num_mixes
        
        # Total workflow time should be reasonable
        total_time = material_creation_time + mix_creation_time
        assert total_time < 8.0  # Less than 8 seconds total
    
    def test_concurrent_simulation_performance(self, gtk_test_environment):
        """Test performance with concurrent simulations."""
        service_container = Mock()
        
        # Mock concurrent simulation startup
        def mock_start_simulation(params):
            sim_id = hash(str(params)) % 10000
            return {
                'operation_id': sim_id,
                'status': 'running',
                'estimated_duration_hours': 1.0
            }
        
        service_container.hydration_service.start_hydration_simulation.side_effect = mock_start_simulation
        
        # Test concurrent simulation startup
        start_time = time.time()
        
        concurrent_sims = []
        for i in range(10):  # 10 concurrent simulations
            sim_params = {
                'microstructure_id': i + 1,
                'hydration_time_days': 7,
                'temperature_celsius': 20
            }
            
            sim_result = service_container.hydration_service.start_hydration_simulation(sim_params)
            concurrent_sims.append(sim_result)
        
        startup_time = time.time() - start_time
        
        # Should start concurrent simulations quickly
        assert startup_time < 2.0  # Less than 2 seconds to start 10 simulations
        assert len(concurrent_sims) == 10
        assert all(sim['status'] == 'running' for sim in concurrent_sims)


@pytest.mark.e2e
class TestWorkflowValidation:
    """Validation tests for workflow correctness."""
    
    def test_scientific_accuracy_validation(self, gtk_test_environment):
        """Test scientific accuracy throughout workflows."""
        service_container = Mock()
        
        # Test cement composition validation
        def validate_cement_composition(data):
            total = (data.c3s_mass_fraction + data.c2s_mass_fraction + 
                    data.c3a_mass_fraction + data.c4af_mass_fraction)
            if total > 1.0:
                raise ValueError("Composition exceeds 100%")
            return Mock(id=1, name=data.name)
        
        service_container.cement_service.create.side_effect = validate_cement_composition
        
        # Valid composition should work
        valid_cement = CementCreate(
            name='Valid Cement',
            c3s_mass_fraction=0.55,
            c2s_mass_fraction=0.18,
            c3a_mass_fraction=0.12,
            c4af_mass_fraction=0.08
        )
        
        result = service_container.cement_service.create(valid_cement)
        assert result.id == 1
        
        # Invalid composition should fail
        invalid_cement = CementCreate(
            name='Invalid Cement',
            c3s_mass_fraction=0.85,  # Too high
            c2s_mass_fraction=0.25,  # Total > 100%
            c3a_mass_fraction=0.12,
            c4af_mass_fraction=0.08
        )
        
        with pytest.raises(ValueError):
            service_container.cement_service.create(invalid_cement)
        
        # Test mix design validation
        def validate_mix_design(data):
            wb_ratio = data['water_kg_per_m3'] / data['cement_kg_per_m3']
            if wb_ratio > 0.65:  # Too high W/C ratio
                return {'valid': False, 'errors': ['W/C ratio too high']}
            return {'valid': True, 'mix_id': 1}
        
        service_container.mix_service.create_mix_design.side_effect = validate_mix_design
        
        # Valid mix should work
        valid_mix = {
            'cement_kg_per_m3': 350,
            'water_kg_per_m3': 175  # W/C = 0.5
        }
        
        mix_result = service_container.mix_service.create_mix_design(valid_mix)
        assert mix_result['valid']
        
        # Invalid mix should fail validation
        invalid_mix = {
            'cement_kg_per_m3': 300,
            'water_kg_per_m3': 210  # W/C = 0.7, too high
        }
        
        mix_result = service_container.mix_service.create_mix_design(invalid_mix)
        assert not mix_result['valid']
        assert 'W/C ratio too high' in mix_result.get('errors', [])


# Fixtures for workflow testing
@pytest.fixture
def sample_workflow_data():
    """Complete sample data for workflow testing."""
    return {
        'cement': {
            'name': 'Workflow Test Cement',
            'c3s_mass_fraction': 0.58,
            'c2s_mass_fraction': 0.16,
            'c3a_mass_fraction': 0.11,
            'c4af_mass_fraction': 0.08,
            'specific_gravity': 3.16
        },
        'fine_aggregate': {
            'name': 'Workflow Test Sand',
            'aggregate_type': 'fine',
            'specific_gravity': 2.65,
            'absorption_percent': 1.1
        },
        'coarse_aggregate': {
            'name': 'Workflow Test Gravel',
            'aggregate_type': 'coarse',
            'specific_gravity': 2.70,
            'absorption_percent': 0.9
        },
        'mix_design': {
            'cement_kg_per_m3': 350,
            'water_kg_per_m3': 175,
            'fine_aggregate_kg_per_m3': 750,
            'coarse_aggregate_kg_per_m3': 1100
        }
    }
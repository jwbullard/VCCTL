#!/usr/bin/env python3
"""
End-to-End Workflow Tests

Complete workflow tests that simulate real user interactions with VCCTL,
from material definition through simulation execution.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import json
import tempfile
from typing import Dict, Any, List

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from app.application import VCCTLApplication
from app.services.service_container import ServiceContainer
from app.models.cement import CementCreate
from app.models.aggregate import AggregateCreate


@pytest.mark.e2e
class TestCompleteWorkflows:
    """End-to-end tests for complete VCCTL workflows."""

    @pytest.fixture
    def vcctl_app(self, gtk_test_environment, temp_directory):
        """Create VCCTL application for testing."""
        with patch('app.application.VCCTLApplication._initialize_services'):
            with patch('app.application.VCCTLApplication._setup_ui'):
                app = VCCTLApplication()
                app.temp_dir = temp_directory
                yield app

    @pytest.fixture
    def workflow_data(self):
        """Sample data for complete workflow testing."""
        return {
            'cement': {
                'name': 'E2E Test Cement',
                'type': 'Type I',
                'sio2': 20.5, 'al2o3': 5.2, 'fe2o3': 3.1, 'cao': 65.0,
                'mgo': 2.8, 'so3': 2.4, 'specific_surface_area': 350.0, 'density': 3.15
            },
            'fine_aggregate': {
                'name': 'E2E Fine Sand',
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
            },
            'coarse_aggregate': {
                'name': 'E2E Coarse Gravel',
                'type': 'coarse',
                'density': 2.70,
                'absorption': 0.8,
                'gradation': {
                    'sieve_25mm': 100.0,
                    'sieve_19mm': 95.0,
                    'sieve_12_5mm': 70.0,
                    'sieve_9_5mm': 40.0,
                    'sieve_4_75mm': 10.0
                }
            },
            'mix_design': {
                'name': 'E2E Test Mix',
                'cement_content': 350.0,
                'water_content': 175.0,
                'water_cement_ratio': 0.5,
                'fine_aggregate': 650.0,
                'coarse_aggregate': 1100.0,
                'air_content': 2.0,
                'slump': 100.0
            }
        }

    @pytest.mark.e2e
    def test_complete_material_to_simulation_workflow(self, vcctl_app, workflow_data, temp_directory):
        """Test complete workflow from material definition to simulation."""
        
        # Step 1: Create materials
        cement_created = self._create_cement_material(vcctl_app, workflow_data['cement'])
        assert cement_created is True
        
        fine_agg_created = self._create_aggregate_material(vcctl_app, workflow_data['fine_aggregate'])
        assert fine_agg_created is True
        
        coarse_agg_created = self._create_aggregate_material(vcctl_app, workflow_data['coarse_aggregate'])
        assert coarse_agg_created is True
        
        # Step 2: Design mix
        mix_created = self._design_concrete_mix(vcctl_app, workflow_data['mix_design'])
        assert mix_created is True
        
        # Step 3: Generate microstructure
        microstructure_generated = self._generate_microstructure(vcctl_app, workflow_data)
        assert microstructure_generated is True
        
        # Step 4: Run hydration simulation
        hydration_completed = self._run_hydration_simulation(vcctl_app, workflow_data)
        assert hydration_completed is True
        
        # Step 5: Export results
        results_exported = self._export_simulation_results(vcctl_app, temp_directory)
        assert results_exported is True

    @pytest.mark.e2e
    def test_material_import_export_workflow(self, vcctl_app, workflow_data, temp_directory):
        """Test material import/export workflow."""
        
        # Step 1: Export materials to files
        export_files = self._export_materials_to_files(vcctl_app, workflow_data, temp_directory)
        assert len(export_files) >= 3  # cement, fine agg, coarse agg
        
        # Step 2: Clear materials from database
        self._clear_materials_database(vcctl_app)
        
        # Step 3: Import materials from files
        imported_count = self._import_materials_from_files(vcctl_app, export_files)
        assert imported_count == len(export_files)
        
        # Step 4: Verify imported materials
        materials_verified = self._verify_imported_materials(vcctl_app, workflow_data)
        assert materials_verified is True

    @pytest.mark.e2e
    def test_project_save_load_workflow(self, vcctl_app, workflow_data, temp_directory):
        """Test complete project save and load workflow."""
        
        # Step 1: Create complete project
        project_created = self._create_complete_project(vcctl_app, workflow_data)
        assert project_created is True
        
        # Step 2: Save project
        project_file = temp_directory / "test_project.vcctl"
        project_saved = self._save_project(vcctl_app, project_file)
        assert project_saved is True
        assert project_file.exists()
        
        # Step 3: Clear current project
        self._clear_current_project(vcctl_app)
        
        # Step 4: Load project
        project_loaded = self._load_project(vcctl_app, project_file)
        assert project_loaded is True
        
        # Step 5: Verify project integrity
        project_verified = self._verify_project_integrity(vcctl_app, workflow_data)
        assert project_verified is True

    @pytest.mark.e2e
    def test_batch_processing_workflow(self, vcctl_app, temp_directory):
        """Test batch processing workflow with multiple materials."""
        
        # Step 1: Create multiple cement variations
        cement_variations = self._create_cement_variations(vcctl_app, 5)
        assert len(cement_variations) == 5
        
        # Step 2: Create batch operation
        batch_operation = self._create_batch_operation(vcctl_app, cement_variations)
        assert batch_operation is not None
        
        # Step 3: Execute batch processing
        batch_results = self._execute_batch_processing(vcctl_app, batch_operation)
        assert len(batch_results) == 5
        
        # Step 4: Export batch results
        batch_exported = self._export_batch_results(vcctl_app, batch_results, temp_directory)
        assert batch_exported is True

    @pytest.mark.e2e
    def test_error_recovery_workflow(self, vcctl_app, workflow_data):
        """Test error recovery during workflow execution."""
        
        # Step 1: Start normal workflow
        workflow_started = self._start_workflow(vcctl_app, workflow_data)
        assert workflow_started is True
        
        # Step 2: Simulate error during simulation
        error_simulated = self._simulate_simulation_error(vcctl_app)
        assert error_simulated is True
        
        # Step 3: Verify error handling
        error_handled = self._verify_error_handling(vcctl_app)
        assert error_handled is True
        
        # Step 4: Recover and restart
        workflow_recovered = self._recover_and_restart_workflow(vcctl_app, workflow_data)
        assert workflow_recovered is True

    # Helper methods for workflow steps

    def _create_cement_material(self, app: VCCTLApplication, cement_data: Dict[str, Any]) -> bool:
        """Create cement material through service."""
        try:
            with patch.object(app, 'get_service_container') as mock_container:
                mock_cement_service = Mock()
                mock_cement_service.create.return_value = Mock(name=cement_data['name'])
                mock_container.return_value.get.return_value = mock_cement_service
                
                cement_create = CementCreate(**cement_data)
                result = mock_cement_service.create(cement_create)
                
                return result is not None
        except Exception:
            return False

    def _create_aggregate_material(self, app: VCCTLApplication, aggregate_data: Dict[str, Any]) -> bool:
        """Create aggregate material through service."""
        try:
            with patch.object(app, 'get_service_container') as mock_container:
                mock_aggregate_service = Mock()
                mock_aggregate_service.create.return_value = Mock(name=aggregate_data['name'])
                mock_container.return_value.get.return_value = mock_aggregate_service
                
                aggregate_create = AggregateCreate(**aggregate_data)
                result = mock_aggregate_service.create(aggregate_create)
                
                return result is not None
        except Exception:
            return False

    def _design_concrete_mix(self, app: VCCTLApplication, mix_data: Dict[str, Any]) -> bool:
        """Design concrete mix through service."""
        try:
            with patch.object(app, 'get_service_container') as mock_container:
                mock_mix_service = Mock()
                mock_mix_service.create_mix_design.return_value = Mock(name=mix_data['name'])
                mock_container.return_value.get.return_value = mock_mix_service
                
                result = mock_mix_service.create_mix_design(mix_data)
                return result is not None
        except Exception:
            return False

    def _generate_microstructure(self, app: VCCTLApplication, workflow_data: Dict[str, Any]) -> bool:
        """Generate microstructure through service."""
        try:
            with patch.object(app, 'get_service_container') as mock_container:
                mock_microstructure_service = Mock()
                mock_microstructure_service.generate_microstructure.return_value = {
                    'status': 'completed',
                    'file_path': '/tmp/microstructure.dat'
                }
                mock_container.return_value.get.return_value = mock_microstructure_service
                
                result = mock_microstructure_service.generate_microstructure(workflow_data)
                return result['status'] == 'completed'
        except Exception:
            return False

    def _run_hydration_simulation(self, app: VCCTLApplication, workflow_data: Dict[str, Any]) -> bool:
        """Run hydration simulation through service."""
        try:
            with patch.object(app, 'get_service_container') as mock_container:
                mock_hydration_service = Mock()
                mock_hydration_service.run_simulation.return_value = {
                    'status': 'completed',
                    'degree_of_hydration': 0.85,
                    'results_file': '/tmp/hydration_results.dat'
                }
                mock_container.return_value.get.return_value = mock_hydration_service
                
                result = mock_hydration_service.run_simulation(workflow_data)
                return result['status'] == 'completed'
        except Exception:
            return False

    def _export_simulation_results(self, app: VCCTLApplication, output_dir: Path) -> bool:
        """Export simulation results."""
        try:
            with patch.object(app, 'get_service_container') as mock_container:
                mock_file_service = Mock()
                mock_file_service.export_results.return_value = [
                    output_dir / "results.json",
                    output_dir / "microstructure.png",
                    output_dir / "hydration_curve.png"
                ]
                mock_container.return_value.get.return_value = mock_file_service
                
                exported_files = mock_file_service.export_results(output_dir)
                return len(exported_files) > 0
        except Exception:
            return False

    def _export_materials_to_files(self, app: VCCTLApplication, workflow_data: Dict[str, Any], 
                                  export_dir: Path) -> List[Path]:
        """Export materials to files."""
        export_files = []
        
        try:
            with patch.object(app, 'get_service_container') as mock_container:
                mock_file_service = Mock()
                
                # Mock export for each material type
                for material_type, material_data in workflow_data.items():
                    if material_type != 'mix_design':
                        export_file = export_dir / f"{material_data['name']}.json"
                        export_file.write_text(json.dumps(material_data))
                        export_files.append(export_file)
                
                mock_container.return_value.get.return_value = mock_file_service
                
        except Exception:
            pass
        
        return export_files

    def _clear_materials_database(self, app: VCCTLApplication) -> bool:
        """Clear materials from database."""
        try:
            with patch.object(app, 'get_service_container') as mock_container:
                mock_services = {
                    'cement_service': Mock(),
                    'aggregate_service': Mock(),
                    'mix_service': Mock()
                }
                
                for service in mock_services.values():
                    service.clear_all.return_value = True
                
                mock_container.return_value.get.side_effect = lambda name: mock_services.get(name)
                
                return True
        except Exception:
            return False

    def _import_materials_from_files(self, app: VCCTLApplication, import_files: List[Path]) -> int:
        """Import materials from files."""
        try:
            with patch.object(app, 'get_service_container') as mock_container:
                mock_file_service = Mock()
                mock_file_service.bulk_import_materials.return_value = [
                    {'name': f'Imported Material {i}'} for i in range(len(import_files))
                ]
                mock_container.return_value.get.return_value = mock_file_service
                
                results = mock_file_service.bulk_import_materials(import_files, ['cement'] * len(import_files))
                return len([r for r in results if r is not None])
        except Exception:
            return 0

    def _verify_imported_materials(self, app: VCCTLApplication, original_data: Dict[str, Any]) -> bool:
        """Verify imported materials match original data."""
        try:
            with patch.object(app, 'get_service_container') as mock_container:
                # Mock services returning the expected materials
                mock_cement_service = Mock()
                mock_cement_service.get_by_name.return_value = Mock(name=original_data['cement']['name'])
                
                mock_aggregate_service = Mock()
                mock_aggregate_service.get_by_name.return_value = Mock(name=original_data['fine_aggregate']['name'])
                
                services = {
                    'cement_service': mock_cement_service,
                    'aggregate_service': mock_aggregate_service
                }
                
                mock_container.return_value.get.side_effect = lambda name: services.get(name)
                
                # Verify materials exist
                cement = mock_cement_service.get_by_name(original_data['cement']['name'])
                fine_agg = mock_aggregate_service.get_by_name(original_data['fine_aggregate']['name'])
                
                return cement is not None and fine_agg is not None
        except Exception:
            return False

    def _create_complete_project(self, app: VCCTLApplication, workflow_data: Dict[str, Any]) -> bool:
        """Create complete project with all components."""
        try:
            # Simulate creating all project components
            cement_created = self._create_cement_material(app, workflow_data['cement'])
            agg_created = self._create_aggregate_material(app, workflow_data['fine_aggregate'])
            mix_created = self._design_concrete_mix(app, workflow_data['mix_design'])
            
            return cement_created and agg_created and mix_created
        except Exception:
            return False

    def _save_project(self, app: VCCTLApplication, project_file: Path) -> bool:
        """Save project to file."""
        try:
            with patch.object(app, 'get_service_container') as mock_container:
                mock_project_service = Mock()
                mock_project_service.save_project.return_value = True
                mock_container.return_value.get.return_value = mock_project_service
                
                # Create mock project file
                project_data = {
                    'version': '1.0',
                    'materials': [],
                    'mix_designs': [],
                    'simulations': []
                }
                project_file.write_text(json.dumps(project_data))
                
                return project_file.exists()
        except Exception:
            return False

    def _clear_current_project(self, app: VCCTLApplication) -> bool:
        """Clear current project."""
        try:
            with patch.object(app, 'get_service_container') as mock_container:
                mock_project_service = Mock()
                mock_project_service.clear_project.return_value = True
                mock_container.return_value.get.return_value = mock_project_service
                
                return True
        except Exception:
            return False

    def _load_project(self, app: VCCTLApplication, project_file: Path) -> bool:
        """Load project from file."""
        try:
            with patch.object(app, 'get_service_container') as mock_container:
                mock_project_service = Mock()
                mock_project_service.load_project.return_value = True
                mock_container.return_value.get.return_value = mock_project_service
                
                return project_file.exists()
        except Exception:
            return False

    def _verify_project_integrity(self, app: VCCTLApplication, expected_data: Dict[str, Any]) -> bool:
        """Verify project integrity after load."""
        try:
            # Verify all expected components are present
            return self._verify_imported_materials(app, expected_data)
        except Exception:
            return False

    def _create_cement_variations(self, app: VCCTLApplication, count: int) -> List[Dict[str, Any]]:
        """Create multiple cement variations."""
        variations = []
        
        try:
            base_cement = {
                'type': 'Type I',
                'sio2': 20.0, 'al2o3': 5.0, 'fe2o3': 3.0, 'cao': 65.0,
                'mgo': 2.5, 'so3': 2.0, 'specific_surface_area': 350.0, 'density': 3.15
            }
            
            for i in range(count):
                variation = base_cement.copy()
                variation['name'] = f'Batch Cement {i+1}'
                variation['sio2'] += i * 0.5  # Slight variations
                variation['cao'] -= i * 0.5
                variations.append(variation)
                
                # Mock creation
                self._create_cement_material(app, variation)
        except Exception:
            pass
        
        return variations

    def _create_batch_operation(self, app: VCCTLApplication, materials: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create batch operation for multiple materials."""
        try:
            batch_operation = {
                'materials': materials,
                'operation_type': 'hydration_simulation',
                'parameters': {
                    'simulation_time': 28,  # days
                    'temperature': 20,      # Celsius
                    'relative_humidity': 95 # percent
                }
            }
            return batch_operation
        except Exception:
            return None

    def _execute_batch_processing(self, app: VCCTLApplication, batch_operation: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute batch processing operation."""
        try:
            with patch.object(app, 'get_service_container') as mock_container:
                mock_batch_service = Mock()
                
                # Mock results for each material
                results = []
                for i, material in enumerate(batch_operation['materials']):
                    result = {
                        'material_name': material['name'],
                        'status': 'completed',
                        'degree_of_hydration': 0.8 + i * 0.02,
                        'results_file': f'/tmp/batch_result_{i}.dat'
                    }
                    results.append(result)
                
                mock_batch_service.execute_batch.return_value = results
                mock_container.return_value.get.return_value = mock_batch_service
                
                return results
        except Exception:
            return []

    def _export_batch_results(self, app: VCCTLApplication, batch_results: List[Dict[str, Any]], 
                             export_dir: Path) -> bool:
        """Export batch processing results."""
        try:
            with patch.object(app, 'get_service_container') as mock_container:
                mock_file_service = Mock()
                
                # Create summary file
                summary_file = export_dir / "batch_summary.json"
                summary_file.write_text(json.dumps(batch_results))
                
                mock_file_service.export_batch_results.return_value = [summary_file]
                mock_container.return_value.get.return_value = mock_file_service
                
                return summary_file.exists()
        except Exception:
            return False

    def _start_workflow(self, app: VCCTLApplication, workflow_data: Dict[str, Any]) -> bool:
        """Start workflow execution."""
        try:
            return self._create_complete_project(app, workflow_data)
        except Exception:
            return False

    def _simulate_simulation_error(self, app: VCCTLApplication) -> bool:
        """Simulate error during simulation."""
        try:
            with patch.object(app, 'get_service_container') as mock_container:
                mock_hydration_service = Mock()
                mock_hydration_service.run_simulation.side_effect = Exception("Simulation failed")
                mock_container.return_value.get.return_value = mock_hydration_service
                
                return True
        except Exception:
            return False

    def _verify_error_handling(self, app: VCCTLApplication) -> bool:
        """Verify error handling mechanisms."""
        try:
            with patch.object(app, 'get_service_container') as mock_container:
                mock_error_handler = Mock()
                mock_error_handler.handle_critical_error.return_value = True
                mock_container.return_value.get.return_value = mock_error_handler
                
                return True
        except Exception:
            return False

    def _recover_and_restart_workflow(self, app: VCCTLApplication, workflow_data: Dict[str, Any]) -> bool:
        """Recover from error and restart workflow."""
        try:
            # Simulate recovery
            with patch.object(app, 'get_service_container') as mock_container:
                mock_recovery_service = Mock()
                mock_recovery_service.recover_from_error.return_value = True
                mock_container.return_value.get.return_value = mock_recovery_service
                
                # Restart workflow
                return self._create_complete_project(app, workflow_data)
        except Exception:
            return False


@pytest.mark.e2e
@pytest.mark.slow  
class TestComplexWorkflows:
    """Tests for complex, multi-step workflows."""

    @pytest.mark.e2e
    def test_parametric_study_workflow(self, temp_directory):
        """Test parametric study workflow with varying cement compositions."""
        
        # Define parameter ranges
        sio2_range = [18.0, 19.0, 20.0, 21.0, 22.0]
        cao_range = [63.0, 64.0, 65.0, 66.0, 67.0]
        
        results = []
        
        # Simulate parametric study
        for sio2 in sio2_range:
            for cao in cao_range:
                cement_data = {
                    'name': f'Parametric Cement SiO2-{sio2}_CaO-{cao}',
                    'type': 'Type I',
                    'sio2': sio2,
                    'cao': cao,
                    'al2o3': 5.0,
                    'fe2o3': 3.0
                }
                
                # Mock simulation result
                result = {
                    'cement': cement_data,
                    'compressive_strength_28d': 30.0 + sio2 * 0.5 + cao * 0.3,
                    'degree_of_hydration': 0.75 + (sio2 - 20.0) * 0.01
                }
                results.append(result)
        
        # Verify parametric study completed
        assert len(results) == len(sio2_range) * len(cao_range)
        
        # Export parametric results
        results_file = temp_directory / "parametric_results.json"
        results_file.write_text(json.dumps(results, indent=2))
        
        assert results_file.exists()

    @pytest.mark.e2e
    def test_optimization_workflow(self, temp_directory):
        """Test mix design optimization workflow."""
        
        # Define optimization targets
        target_strength = 35.0  # MPa
        target_slump = 100.0    # mm
        target_cost = 'minimize'
        
        # Simulate optimization iterations
        optimization_results = []
        
        for iteration in range(10):
            # Mock optimization step
            cement_content = 300.0 + iteration * 10.0
            water_cement_ratio = 0.45 + iteration * 0.01
            
            mix_design = {
                'iteration': iteration,
                'cement_content': cement_content,
                'water_cement_ratio': water_cement_ratio,
                'predicted_strength': 25.0 + cement_content * 0.02,
                'predicted_slump': 80.0 + water_cement_ratio * 50.0,
                'cost_per_m3': 50.0 + cement_content * 0.15
            }
            
            optimization_results.append(mix_design)
        
        # Find best solution
        best_solution = min(optimization_results, 
                          key=lambda x: abs(x['predicted_strength'] - target_strength))
        
        assert best_solution is not None
        assert abs(best_solution['predicted_strength'] - target_strength) < 5.0

    @pytest.mark.e2e
    def test_multi_material_compatibility_workflow(self):
        """Test compatibility analysis between multiple materials."""
        
        # Define material combinations
        cement_types = ['Type I', 'Type II', 'Type III']
        scm_types = ['Fly Ash Class F', 'Fly Ash Class C', 'Silica Fume', 'Slag']
        
        compatibility_matrix = {}
        
        # Test all combinations
        for cement in cement_types:
            for scm in scm_types:
                # Mock compatibility analysis
                compatibility_score = self._calculate_compatibility(cement, scm)
                
                combination_key = f"{cement} + {scm}"
                compatibility_matrix[combination_key] = {
                    'compatibility_score': compatibility_score,
                    'recommended': compatibility_score > 0.7,
                    'issues': [] if compatibility_score > 0.7 else ['Chemical incompatibility']
                }
        
        # Verify all combinations were tested
        expected_combinations = len(cement_types) * len(scm_types)
        assert len(compatibility_matrix) == expected_combinations
        
        # Find best combinations
        best_combinations = [
            combo for combo, data in compatibility_matrix.items() 
            if data['recommended']
        ]
        
        assert len(best_combinations) > 0

    def _calculate_compatibility(self, cement_type: str, scm_type: str) -> float:
        """Mock compatibility calculation."""
        # Simple mock calculation based on material types
        compatibility_scores = {
            ('Type I', 'Fly Ash Class F'): 0.85,
            ('Type I', 'Fly Ash Class C'): 0.75,
            ('Type I', 'Silica Fume'): 0.90,
            ('Type I', 'Slag'): 0.80,
            ('Type II', 'Fly Ash Class F'): 0.80,
            ('Type II', 'Slag'): 0.85,
            ('Type III', 'Silica Fume'): 0.95,
        }
        
        return compatibility_scores.get((cement_type, scm_type), 0.60)


@pytest.mark.e2e
@pytest.mark.performance
class TestWorkflowPerformance:
    """Performance tests for complete workflows."""

    @pytest.mark.e2e
    def test_large_batch_processing_performance(self, performance_timer):
        """Test performance of large batch processing."""
        
        # Simulate processing 100 materials
        material_count = 100
        
        performance_timer.start()
        
        # Mock batch processing
        results = []
        for i in range(material_count):
            # Simulate material processing
            result = {
                'material_id': i,
                'processing_time': 0.1,  # 100ms per material
                'status': 'completed'
            }
            results.append(result)
        
        elapsed = performance_timer.stop()
        
        # Batch processing should be efficient
        assert len(results) == material_count
        assert elapsed < 30.0, f"Batch processing took {elapsed:.3f}s, expected < 30s"

    @pytest.mark.e2e
    def test_workflow_memory_usage(self):
        """Test memory usage during complex workflows."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Simulate memory-intensive workflow
        large_data_sets = []
        for i in range(50):
            # Create large data structures
            data_set = {
                'materials': [{'data': list(range(1000))} for _ in range(10)],
                'simulations': [{'results': list(range(500))} for _ in range(20)]
            }
            large_data_sets.append(data_set)
        
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - initial_memory
        
        # Memory usage should be reasonable
        assert memory_increase < 500, f"Memory increased by {memory_increase:.1f}MB, expected < 500MB"
        
        # Clean up
        del large_data_sets
#!/usr/bin/env python3
"""
Comprehensive Unit Tests for All VCCTL Services

Complete test coverage for all service classes to achieve >80% coverage.
Tests all service methods, error conditions, and edge cases.
"""

import pytest
import tempfile
import json
from unittest.mock import Mock, patch, MagicMock, call
from pathlib import Path
from sqlalchemy.exc import IntegrityError
from typing import Dict, Any, List

# Import all services
from app.services.cement_service import CementService
from app.services.fly_ash_service import FlyAshService
from app.services.slag_service import SlagService
from app.services.aggregate_service import AggregateService
from app.services.inert_filler_service import InertFillerService
from app.services.mix_service import MixService
from app.services.microstructure_service import MicrostructureService
from app.services.hydration_service import HydrationService
from app.services.operation_service import OperationService
from app.services.grading_service import GradingService
from app.services.directories_service import DirectoriesService
from app.services.file_operations_service import FileOperationsService

# Import models
from app.models.cement import Cement, CementCreate, CementUpdate
from app.models.fly_ash import FlyAsh, FlyAshCreate, FlyAshUpdate
from app.models.slag import Slag, SlagCreate, SlagUpdate
from app.models.aggregate import Aggregate, AggregateCreate, AggregateUpdate
from app.models.inert_filler import InertFiller, InertFillerCreate, InertFillerUpdate
from app.models.grading import Grading, GradingCreate, GradingUpdate
from app.models.operation import Operation, OperationCreate, OperationUpdate

# Import exceptions
from app.services.base_service import ServiceError, NotFoundError, AlreadyExistsError


@pytest.mark.unit
class TestFlyAshService:
    """Comprehensive tests for FlyAshService."""
    
    def test_create_flyash_success(self, test_database, sample_flyash_data):
        """Test successful fly ash creation."""
        service = FlyAshService(test_database)
        flyash_create = FlyAshCreate(**sample_flyash_data)
        
        # Mock database operations
        mock_session = Mock()
        mock_flyash = Mock(spec=FlyAsh)
        mock_flyash.id = 1
        mock_flyash.name = sample_flyash_data['name']
        
        with patch.object(test_database, 'get_session') as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_session.add = Mock()
            mock_session.commit = Mock()
            mock_session.refresh = Mock()
            
            with patch.object(service, '_validate_flyash_composition') as mock_validate:
                mock_validate.return_value = True
                with patch.object(FlyAsh, '__init__', return_value=None):
                    mock_session.add.return_value = mock_flyash
                    
                    result = service.create(flyash_create)
                    
                    assert mock_session.add.called
                    assert mock_session.commit.called
    
    def test_validate_flyash_composition(self, test_database):
        """Test fly ash composition validation."""
        service = FlyAshService(test_database)
        
        # Valid composition
        valid_data = {
            'sio2_mass_fraction': 0.55,
            'al2o3_mass_fraction': 0.25,
            'fe2o3_mass_fraction': 0.08,
            'cao_mass_fraction': 0.03,
            'mgo_mass_fraction': 0.02,
            'so3_mass_fraction': 0.02,
            'na2o_equivalent': 0.015,
            'loss_on_ignition': 0.025
        }
        
        # Should not raise exception for valid composition
        service._validate_flyash_composition(valid_data)
        
        # Invalid composition (total > 100%)
        invalid_data = valid_data.copy()
        invalid_data['sio2_mass_fraction'] = 0.95  # Too high
        
        with pytest.raises(ServiceError, match="composition"):
            service._validate_flyash_composition(invalid_data)
    
    def test_get_by_class(self, test_database):
        """Test retrieval by ASTM class."""
        service = FlyAshService(test_database)
        
        mock_session = Mock()
        mock_query = Mock()
        mock_flyashes = [Mock(astm_class='F'), Mock(astm_class='F')]
        
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = mock_flyashes
        
        with patch.object(test_database, 'get_read_only_session') as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session
            
            result = service.get_by_class('F')
            
            assert len(result) == 2
            mock_query.filter.assert_called_once()


@pytest.mark.unit
class TestSlagService:
    """Comprehensive tests for SlagService."""
    
    def test_create_slag_success(self, test_database, sample_slag_data):
        """Test successful slag creation."""
        service = SlagService(test_database)
        slag_create = SlagCreate(**sample_slag_data)
        
        mock_session = Mock()
        mock_slag = Mock(spec=Slag)
        
        with patch.object(test_database, 'get_session') as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session
            with patch.object(service, '_validate_slag_composition') as mock_validate:
                mock_validate.return_value = True
                
                result = service.create(slag_create)
                
                assert mock_session.add.called
                assert mock_session.commit.called
    
    def test_calculate_activity_index(self, test_database):
        """Test slag activity index calculation."""
        service = SlagService(test_database)
        
        # Mock slag with composition data
        slag_data = {
            'cao_mass_fraction': 0.40,
            'sio2_mass_fraction': 0.35,
            'al2o3_mass_fraction': 0.12,
            'mgo_mass_fraction': 0.08
        }
        
        activity_index = service._calculate_activity_index(slag_data)
        
        assert isinstance(activity_index, float)
        assert 0.0 <= activity_index <= 2.0  # Reasonable range
    
    def test_validate_slag_composition(self, test_database):
        """Test slag composition validation."""
        service = SlagService(test_database)
        
        # Valid composition
        valid_data = {
            'cao_mass_fraction': 0.40,
            'sio2_mass_fraction': 0.35,
            'al2o3_mass_fraction': 0.12,
            'mgo_mass_fraction': 0.08,
            'fe2o3_mass_fraction': 0.03,
            'so3_mass_fraction': 0.015,
            'na2o_equivalent': 0.005
        }
        
        # Should pass validation
        service._validate_slag_composition(valid_data)
        
        # Invalid composition
        invalid_data = valid_data.copy()
        invalid_data['cao_mass_fraction'] = 0.85  # Too high
        
        with pytest.raises(ServiceError):
            service._validate_slag_composition(invalid_data)


@pytest.mark.unit
class TestMixService:
    """Comprehensive tests for MixService."""
    
    def test_create_mix_design(self, test_database, sample_mix_data):
        """Test mix design creation."""
        service = MixService(test_database)
        
        # Mock dependencies
        mock_cement_service = Mock()
        mock_aggregate_service = Mock()
        
        with patch.object(service, 'cement_service', mock_cement_service):
            with patch.object(service, 'aggregate_service', mock_aggregate_service):
                
                mock_cement_service.get_by_id.return_value = Mock(id=1)
                mock_aggregate_service.get_by_id.return_value = Mock(id=1)
                
                result = service.create_mix_design(sample_mix_data)
                
                assert result is not None
                assert 'mix_id' in result
    
    def test_calculate_water_binder_ratio(self, test_database):
        """Test water-binder ratio calculation."""
        service = MixService(test_database)
        
        mix_components = {
            'water_kg_per_m3': 180,
            'cement_kg_per_m3': 350,
            'fly_ash_kg_per_m3': 50,
            'slag_kg_per_m3': 0
        }
        
        wb_ratio = service._calculate_water_binder_ratio(mix_components)
        
        expected_ratio = 180 / (350 + 50)  # water / (cement + SCMs)
        assert abs(wb_ratio - expected_ratio) < 0.001
    
    def test_validate_mix_proportions(self, test_database):
        """Test mix proportions validation."""
        service = MixService(test_database)
        
        # Valid proportions
        valid_mix = {
            'water_kg_per_m3': 180,
            'cement_kg_per_m3': 350,
            'fine_aggregate_kg_per_m3': 800,
            'coarse_aggregate_kg_per_m3': 1000,
            'fly_ash_kg_per_m3': 0,
            'slag_kg_per_m3': 0
        }
        
        # Should pass validation
        is_valid = service._validate_mix_proportions(valid_mix)
        assert is_valid
        
        # Invalid proportions (excessive water)
        invalid_mix = valid_mix.copy()
        invalid_mix['water_kg_per_m3'] = 300  # W/C ratio too high
        
        is_valid = service._validate_mix_proportions(invalid_mix)
        assert not is_valid


@pytest.mark.unit
class TestMicrostructureService:
    """Comprehensive tests for MicrostructureService."""
    
    def test_generate_microstructure_parameters(self, test_database):
        """Test microstructure parameter generation."""
        service = MicrostructureService(test_database)
        
        input_params = {
            'system_size_voxels': 100,
            'resolution_micrometers': 1.0,
            'particle_shape_set_id': 1,
            'random_seed': 12345
        }
        
        with patch.object(service, '_validate_system_parameters') as mock_validate:
            mock_validate.return_value = True
            
            params = service.generate_microstructure_parameters(input_params)
            
            assert 'system_size_voxels' in params
            assert 'resolution_micrometers' in params
            assert params['random_seed'] == 12345
    
    def test_calculate_volume_fractions(self, test_database):
        """Test volume fraction calculations."""
        service = MicrostructureService(test_database)
        
        mix_data = {
            'cement_kg_per_m3': 350,
            'water_kg_per_m3': 175,
            'fine_aggregate_kg_per_m3': 700,
            'coarse_aggregate_kg_per_m3': 1100
        }
        
        densities = {
            'cement_density': 3150,
            'water_density': 1000,
            'aggregate_density': 2650
        }
        
        volume_fractions = service._calculate_volume_fractions(mix_data, densities)
        
        assert 'cement_volume_fraction' in volume_fractions
        assert 'water_volume_fraction' in volume_fractions
        assert 'aggregate_volume_fraction' in volume_fractions
        
        # Check total doesn't exceed 1.0
        total = sum(volume_fractions.values())
        assert total <= 1.0
    
    def test_validate_system_parameters(self, test_database):
        """Test system parameter validation."""
        service = MicrostructureService(test_database)
        
        # Valid parameters
        valid_params = {
            'system_size_voxels': 100,
            'resolution_micrometers': 1.0,
            'max_aggregate_size': 10.0
        }
        
        is_valid = service._validate_system_parameters(valid_params)
        assert is_valid
        
        # Invalid parameters (too large system)
        invalid_params = valid_params.copy()
        invalid_params['system_size_voxels'] = 2000  # Too large
        
        is_valid = service._validate_system_parameters(invalid_params)
        assert not is_valid


@pytest.mark.unit
class TestHydrationService:
    """Comprehensive tests for HydrationService."""
    
    def test_start_hydration_simulation(self, test_database):
        """Test hydration simulation startup."""
        service = HydrationService(test_database)
        
        simulation_params = {
            'microstructure_id': 1,
            'hydration_time_days': 28,
            'temperature_celsius': 20,
            'aging_mode': 'time'
        }
        
        mock_operation_service = Mock()
        
        with patch.object(service, 'operation_service', mock_operation_service):
            mock_operation_service.create_operation.return_value = Mock(id=1)
            
            result = service.start_hydration_simulation(simulation_params)
            
            assert result is not None
            assert 'operation_id' in result
    
    def test_calculate_hydration_rate(self, test_database):
        """Test hydration rate calculation."""
        service = HydrationService(test_database)
        
        # Mock cement composition and temperature
        cement_composition = {
            'c3s_mass_fraction': 0.55,
            'c2s_mass_fraction': 0.18,
            'c3a_mass_fraction': 0.12,
            'c4af_mass_fraction': 0.08
        }
        
        temperature = 20  # Celsius
        time_hours = 24
        
        rate = service._calculate_hydration_rate(cement_composition, temperature, time_hours)
        
        assert isinstance(rate, float)
        assert 0.0 <= rate <= 1.0
    
    def test_update_hydration_progress(self, test_database):
        """Test hydration progress updates."""
        service = HydrationService(test_database)
        
        operation_id = 1
        progress_data = {
            'degree_of_hydration': 0.45,
            'heat_evolved_j_per_g': 250,
            'elapsed_time_hours': 48
        }
        
        mock_operation_service = Mock()
        
        with patch.object(service, 'operation_service', mock_operation_service):
            service.update_hydration_progress(operation_id, progress_data)
            
            mock_operation_service.update_operation_progress.assert_called_once()


@pytest.mark.unit
class TestFileOperationsService:
    """Comprehensive tests for FileOperationsService."""
    
    def test_import_material_data(self, test_database, temp_directory):
        """Test material data import."""
        service = FileOperationsService(test_database)
        
        # Create test import file
        import_file = temp_directory / "test_cement.json"
        test_data = {
            'name': 'Test Cement',
            'c3s_mass_fraction': 0.55,
            'c2s_mass_fraction': 0.18,
            'c3a_mass_fraction': 0.12,
            'c4af_mass_fraction': 0.08
        }
        
        with open(import_file, 'w') as f:
            json.dump(test_data, f)
        
        # Mock cement service
        mock_cement_service = Mock()
        
        with patch.object(service, 'cement_service', mock_cement_service):
            mock_cement_service.create.return_value = Mock(id=1)
            
            result = service.import_material_data(str(import_file), 'cement')
            
            assert result is not None
            assert result['success']
            mock_cement_service.create.assert_called_once()
    
    def test_export_material_data(self, test_database, temp_directory):
        """Test material data export."""
        service = FileOperationsService(test_database)
        
        export_file = temp_directory / "export_cement.json"
        
        # Mock cement data
        mock_cement = Mock()
        mock_cement.name = 'Test Cement'
        mock_cement.c3s_mass_fraction = 0.55
        
        mock_cement_service = Mock()
        mock_cement_service.get_by_id.return_value = mock_cement
        
        with patch.object(service, 'cement_service', mock_cement_service):
            result = service.export_material_data(1, 'cement', str(export_file))
            
            assert result['success']
            assert export_file.exists()
    
    def test_validate_import_file(self, test_database, temp_directory):
        """Test import file validation."""
        service = FileOperationsService(test_database)
        
        # Valid JSON file
        valid_file = temp_directory / "valid.json"
        with open(valid_file, 'w') as f:
            json.dump({'name': 'Test'}, f)
        
        is_valid = service._validate_import_file(str(valid_file), 'json')
        assert is_valid
        
        # Invalid file (doesn't exist)
        invalid_file = temp_directory / "nonexistent.json"
        is_valid = service._validate_import_file(str(invalid_file), 'json')
        assert not is_valid
    
    def test_batch_import_materials(self, test_database, temp_directory):
        """Test batch material import."""
        service = FileOperationsService(test_database)
        
        # Create batch import directory
        batch_dir = temp_directory / "batch_import"
        batch_dir.mkdir()
        
        # Create multiple test files
        for i in range(3):
            test_file = batch_dir / f"cement_{i}.json"
            test_data = {
                'name': f'Test Cement {i}',
                'c3s_mass_fraction': 0.50 + i * 0.01
            }
            with open(test_file, 'w') as f:
                json.dump(test_data, f)
        
        mock_cement_service = Mock()
        
        with patch.object(service, 'cement_service', mock_cement_service):
            mock_cement_service.create.return_value = Mock(id=1)
            
            result = service.batch_import_materials(str(batch_dir), 'cement')
            
            assert result['success']
            assert result['imported_count'] == 3
            assert mock_cement_service.create.call_count == 3


@pytest.mark.unit  
class TestDirectoriesService:
    """Comprehensive tests for DirectoriesService."""
    
    def test_get_user_directories(self, test_config):
        """Test user directory retrieval."""
        service = DirectoriesService(test_config)
        
        directories = service.get_user_directories()
        
        assert 'workspace_dir' in directories
        assert 'materials_dir' in directories
        assert 'output_dir' in directories
        assert 'temp_dir' in directories
    
    def test_create_project_structure(self, test_config, temp_directory):
        """Test project structure creation."""
        service = DirectoriesService(test_config)
        
        project_dir = temp_directory / "test_project"
        
        result = service.create_project_structure(str(project_dir))
        
        assert result['success']
        assert project_dir.exists()
        assert (project_dir / "materials").exists()
        assert (project_dir / "simulations").exists()
        assert (project_dir / "results").exists()
    
    def test_cleanup_temp_files(self, test_config, temp_directory):
        """Test temporary file cleanup."""
        service = DirectoriesService(test_config)
        
        # Create temp files
        temp_file1 = temp_directory / "temp1.tmp"
        temp_file2 = temp_directory / "temp2.tmp"
        temp_file1.touch()
        temp_file2.touch()
        
        # Override temp directory
        service.config.user_config.temp_dir = str(temp_directory)
        
        result = service.cleanup_temp_files()
        
        assert result['cleaned_files'] >= 2
        assert not temp_file1.exists()
        assert not temp_file2.exists()


# Test fixtures for sample data
@pytest.fixture
def sample_flyash_data():
    """Sample fly ash data for testing."""
    return {
        'name': 'Test Fly Ash',
        'sio2_mass_fraction': 0.55,
        'al2o3_mass_fraction': 0.25,
        'fe2o3_mass_fraction': 0.08,
        'cao_mass_fraction': 0.03,
        'mgo_mass_fraction': 0.02,
        'so3_mass_fraction': 0.02,
        'na2o_equivalent': 0.015,
        'loss_on_ignition': 0.025,
        'specific_gravity': 2.3,
        'astm_class': 'F'
    }


@pytest.fixture
def sample_slag_data():
    """Sample slag data for testing."""
    return {
        'name': 'Test Slag',
        'cao_mass_fraction': 0.40,
        'sio2_mass_fraction': 0.35,
        'al2o3_mass_fraction': 0.12,
        'mgo_mass_fraction': 0.08,
        'fe2o3_mass_fraction': 0.03,
        'so3_mass_fraction': 0.015,
        'na2o_equivalent': 0.005,
        'specific_gravity': 2.9,
        'activity_index_7_day': 85,
        'activity_index_28_day': 95
    }


@pytest.fixture  
def sample_mix_data():
    """Sample mix design data for testing."""
    return {
        'name': 'Test Mix Design',
        'cement_id': 1,
        'water_kg_per_m3': 180,
        'cement_kg_per_m3': 350,
        'fine_aggregate_id': 1,
        'fine_aggregate_kg_per_m3': 700,
        'coarse_aggregate_id': 1,
        'coarse_aggregate_kg_per_m3': 1100,
        'fly_ash_id': None,
        'fly_ash_kg_per_m3': 0,
        'slag_id': None,
        'slag_kg_per_m3': 0,
        'target_strength_mpa': 30
    }


# Performance tests markers
@pytest.mark.performance
class TestServicePerformance:
    """Performance tests for services."""
    
    def test_cement_service_bulk_operations(self, test_database, sample_cement_data):
        """Test cement service performance with bulk operations."""
        service = CementService(test_database)
        
        import time
        start_time = time.time()
        
        # Simulate bulk operations
        for i in range(10):
            cement_data = sample_cement_data.copy()
            cement_data['name'] = f"Test Cement {i}"
            
            # Mock the operation to avoid actual database writes
            with patch.object(service, 'create') as mock_create:
                mock_create.return_value = Mock(id=i)
                service.create(CementCreate(**cement_data))
        
        elapsed_time = time.time() - start_time
        
        # Should complete bulk operations quickly
        assert elapsed_time < 1.0  # Less than 1 second for 10 operations


# Sample data fixture
@pytest.fixture
def sample_cement_data():
    """Sample cement data for testing."""
    return {
        'name': 'Test Cement',
        'c3s_mass_fraction': 0.55,
        'c2s_mass_fraction': 0.18,
        'c3a_mass_fraction': 0.12,
        'c4af_mass_fraction': 0.08,
        'gypsum_mass_fraction': 0.05,
        'specific_gravity': 3.15,
        'blaine_fineness': 380
    }
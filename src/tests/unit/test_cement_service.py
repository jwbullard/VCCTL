#!/usr/bin/env python3
"""
Unit Tests for Cement Service

Comprehensive test coverage for cement material management operations.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from sqlalchemy.exc import IntegrityError
from typing import Dict, Any

from app.services.cement_service import CementService
from app.models.cement import Cement, CementCreate, CementUpdate
from app.services.base_service import ServiceError, NotFoundError, AlreadyExistsError
from tests.conftest import assert_valid_cement_composition


class TestCementService:
    """Test suite for CementService."""

    def test_init(self, test_database):
        """Test service initialization."""
        service = CementService(test_database)
        
        assert service.db_service == test_database
        assert service.model_class == Cement
        assert service.default_alkali_file == 'lowalkali'
        assert service.logger.name == 'VCCTL.CementService'

    @pytest.mark.unit
    def test_get_all_success(self, test_database):
        """Test successful retrieval of all cements."""
        service = CementService(test_database)
        
        # Mock database session and query
        mock_session = Mock()
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [
            Mock(name="Cement1"), Mock(name="Cement2")
        ]
        
        with patch.object(test_database, 'get_read_only_session') as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session
            
            result = service.get_all()
            
            assert len(result) == 2
            mock_session.query.assert_called_once_with(Cement)
            mock_query.order_by.assert_called_once()

    @pytest.mark.unit
    def test_get_all_failure(self, test_database):
        """Test handling of database errors in get_all."""
        service = CementService(test_database)
        
        with patch.object(test_database, 'get_read_only_session') as mock_get_session:
            mock_get_session.return_value.__enter__.side_effect = Exception("Database error")
            
            with pytest.raises(ServiceError, match="Failed to retrieve cements"):
                service.get_all()

    @pytest.mark.unit
    def test_get_by_name_success(self, test_database):
        """Test successful retrieval of cement by name."""
        service = CementService(test_database)
        
        mock_cement = Mock(name="Test Cement")
        mock_session = Mock()
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter_by.return_value = mock_query
        mock_query.first.return_value = mock_cement
        
        with patch.object(test_database, 'get_read_only_session') as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session
            
            result = service.get_by_name("Test Cement")
            
            assert result == mock_cement
            mock_query.filter_by.assert_called_once_with(name="Test Cement")

    @pytest.mark.unit
    def test_get_by_name_not_found(self, test_database):
        """Test get_by_name when cement doesn't exist."""
        service = CementService(test_database)
        
        mock_session = Mock()
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter_by.return_value = mock_query
        mock_query.first.return_value = None
        
        with patch.object(test_database, 'get_read_only_session') as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session
            
            result = service.get_by_name("Nonexistent")
            assert result is None

    @pytest.mark.unit
    def test_create_success(self, test_database, sample_cement_data):
        """Test successful cement creation."""
        service = CementService(test_database)
        
        cement_create = CementCreate(**sample_cement_data)
        
        mock_session = Mock()
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter_by.return_value = mock_query
        mock_query.first.return_value = None  # No existing cement
        
        with patch.object(test_database, 'get_session') as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session
            
            with patch.object(service, '_validate_cement') as mock_validate:
                result = service.create(cement_create)
                
                # Verify cement was created and added to session
                mock_session.add.assert_called_once()
                mock_session.flush.assert_called_once()
                mock_validate.assert_called_once()

    @pytest.mark.unit
    def test_create_already_exists(self, test_database, sample_cement_data):
        """Test creation of cement that already exists."""
        service = CementService(test_database)
        
        cement_create = CementCreate(**sample_cement_data)
        
        mock_session = Mock()
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter_by.return_value = mock_query
        mock_query.first.return_value = Mock()  # Existing cement
        
        with patch.object(test_database, 'get_session') as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session
            
            with pytest.raises(AlreadyExistsError, match="already exists"):
                service.create(cement_create)

    @pytest.mark.unit
    def test_create_sets_default_alkali_file(self, test_database):
        """Test that default alkali file is set during creation."""
        service = CementService(test_database)
        
        cement_data = {
            'name': 'Test Cement',
            'type': 'Type I',
            'sio2': 20.0, 'al2o3': 5.0, 'fe2o3': 3.0, 'cao': 65.0
        }
        cement_create = CementCreate(**cement_data)
        
        mock_session = Mock()
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter_by.return_value = mock_query
        mock_query.first.return_value = None
        
        with patch.object(test_database, 'get_session') as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session
            
            with patch.object(service, '_validate_cement'):
                service.create(cement_create)
                
                # Check that add was called with cement having default alkali file
                call_args = mock_session.add.call_args[0][0]
                assert hasattr(call_args, 'alkali_file')

    @pytest.mark.unit
    def test_create_integrity_error(self, test_database, sample_cement_data):
        """Test handling of database integrity errors during creation."""
        service = CementService(test_database)
        
        cement_create = CementCreate(**sample_cement_data)
        
        mock_session = Mock()
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter_by.return_value = mock_query
        mock_query.first.return_value = None
        mock_session.flush.side_effect = IntegrityError("", "", "")
        
        with patch.object(test_database, 'get_session') as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session
            
            with patch.object(service, '_validate_cement'):
                with pytest.raises(ServiceError, match="invalid data"):
                    service.create(cement_create)

    @pytest.mark.unit
    def test_update_success(self, test_database):
        """Test successful cement update."""
        service = CementService(test_database)
        
        mock_cement = Mock()
        mock_cement.name = "Test Cement"
        
        mock_session = Mock()
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter_by.return_value = mock_query
        mock_query.first.return_value = mock_cement
        
        update_data = CementUpdate(sio2=21.0, al2o3=5.5)
        
        with patch.object(test_database, 'get_session') as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session
            
            with patch.object(service, '_validate_cement') as mock_validate:
                result = service.update("Test Cement", update_data)
                
                assert result == mock_cement
                mock_session.flush.assert_called_once()
                mock_validate.assert_called_once()

    @pytest.mark.unit
    def test_update_not_found(self, test_database):
        """Test update of non-existent cement."""
        service = CementService(test_database)
        
        mock_session = Mock()
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter_by.return_value = mock_query
        mock_query.first.return_value = None
        
        update_data = CementUpdate(sio2=21.0)
        
        with patch.object(test_database, 'get_session') as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session
            
            with pytest.raises(NotFoundError, match="not found"):
                service.update("Nonexistent", update_data)

    @pytest.mark.unit
    def test_delete_success(self, test_database):
        """Test successful cement deletion."""
        service = CementService(test_database)
        
        mock_cement = Mock()
        mock_session = Mock()
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter_by.return_value = mock_query
        mock_query.first.return_value = mock_cement
        
        with patch.object(test_database, 'get_session') as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session
            
            result = service.delete("Test Cement")
            
            assert result is True
            mock_session.delete.assert_called_once_with(mock_cement)

    @pytest.mark.unit
    def test_delete_not_found(self, test_database):
        """Test deletion of non-existent cement."""
        service = CementService(test_database)
        
        mock_session = Mock()
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter_by.return_value = mock_query
        mock_query.first.return_value = None
        
        with patch.object(test_database, 'get_session') as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session
            
            with pytest.raises(NotFoundError, match="not found"):
                service.delete("Nonexistent")

    @pytest.mark.unit
    def test_save_as_success(self, test_database):
        """Test successful save as operation."""
        service = CementService(test_database)
        
        mock_original = Mock()
        mock_original.to_dict.return_value = {
            'name': 'Original',
            'type': 'Type I',
            'sio2': 20.0,
            'id': 1,
            'created_at': 'timestamp',
            'updated_at': 'timestamp'
        }
        
        mock_session = Mock()
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter_by.return_value = mock_query
        
        # First call returns original, second returns None (new name doesn't exist)
        mock_query.first.side_effect = [mock_original, None]
        
        with patch.object(test_database, 'get_session') as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session
            
            result = service.save_as("Original", "Copy")
            
            # Verify new cement was added
            mock_session.add.assert_called_once()
            mock_session.flush.assert_called_once()

    @pytest.mark.unit
    def test_save_as_original_not_found(self, test_database):
        """Test save as when original cement doesn't exist."""
        service = CementService(test_database)
        
        mock_session = Mock()
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter_by.return_value = mock_query
        mock_query.first.return_value = None
        
        with patch.object(test_database, 'get_session') as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session
            
            with pytest.raises(NotFoundError, match="not found"):
                service.save_as("Nonexistent", "Copy")

    @pytest.mark.unit
    def test_save_as_new_name_exists(self, test_database):
        """Test save as when new name already exists."""
        service = CementService(test_database)
        
        mock_original = Mock()
        mock_existing = Mock()
        
        mock_session = Mock()
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter_by.return_value = mock_query
        
        # First call returns original, second returns existing cement
        mock_query.first.side_effect = [mock_original, mock_existing]
        
        with patch.object(test_database, 'get_session') as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session
            
            with pytest.raises(AlreadyExistsError, match="already exists"):
                service.save_as("Original", "Existing")

    @pytest.mark.unit
    def test_write_correlation_files_success(self, test_database, temp_directory):
        """Test successful correlation files writing."""
        service = CementService(test_database)
        
        mock_cement = Mock()
        mock_files = [temp_directory / "file1.txt", temp_directory / "file2.txt"]
        
        with patch.object(service, 'get_by_name', return_value=mock_cement):
            with patch.object(service, '_write_files_from_cement', return_value=mock_files):
                result = service.write_correlation_files("Test Cement", temp_directory)
                
                assert result == mock_files

    @pytest.mark.unit
    def test_write_correlation_files_cement_not_found(self, test_database, temp_directory):
        """Test correlation files writing when cement doesn't exist."""
        service = CementService(test_database)
        
        with patch.object(service, 'get_by_name', return_value=None):
            with pytest.raises(NotFoundError, match="not found"):
                service.write_correlation_files("Nonexistent", temp_directory)


class TestCementValidation:
    """Test cement validation logic."""

    @pytest.mark.unit
    def test_validate_cement_success(self, test_database, sample_cement_data):
        """Test successful cement validation."""
        service = CementService(test_database)
        cement = Cement(**sample_cement_data)
        
        # Should not raise any exceptions
        service._validate_cement(cement)

    @pytest.mark.unit
    def test_validate_cement_composition(self, sample_cement_data):
        """Test cement composition validation."""
        # Test with valid composition
        assert_valid_cement_composition(sample_cement_data, tolerance=0.1)
        
        # Test with invalid composition
        invalid_data = sample_cement_data.copy()
        invalid_data['sio2'] = 50.0  # Makes total > 100%
        
        with pytest.raises(AssertionError, match="Cement composition totals"):
            assert_valid_cement_composition(invalid_data, tolerance=0.1)


class TestCementFileOperations:
    """Test cement file operation methods."""

    @pytest.mark.unit
    def test_write_files_from_cement(self, test_database, temp_directory, sample_cement_data):
        """Test writing cement files to directory."""
        service = CementService(test_database)
        cement = Cement(**sample_cement_data)
        
        with patch('pathlib.Path.write_text') as mock_write:
            with patch('pathlib.Path.exists', return_value=False):
                with patch('pathlib.Path.mkdir'):
                    result = service._write_files_from_cement(cement, temp_directory)
                    
                    # Should return list of file paths
                    assert isinstance(result, list)
                    assert len(result) > 0
                    
                    # Should have written files
                    assert mock_write.call_count > 0

    @pytest.mark.unit
    def test_generate_img_in_content(self, test_database, sample_cement_data):
        """Test generation of .img.in file content."""
        service = CementService(test_database)
        cement = Cement(**sample_cement_data)
        
        content = service._generate_img_in_content(cement)
        
        assert isinstance(content, str)
        assert len(content) > 0
        # Should contain cement properties
        assert str(cement.sio2) in content
        assert str(cement.al2o3) in content

    @pytest.mark.unit  
    def test_generate_psd_content(self, test_database, sample_cement_data):
        """Test generation of PSD file content."""
        service = CementService(test_database)
        cement = Cement(**sample_cement_data)
        
        content = service._generate_psd_content(cement)
        
        assert isinstance(content, str)
        assert len(content) > 0
        # Should contain fineness information
        assert str(cement.specific_surface_area) in content


@pytest.mark.performance
class TestCementServicePerformance:
    """Performance tests for cement service operations."""

    def test_create_performance(self, test_database, sample_cement_data, performance_timer):
        """Test cement creation performance."""
        service = CementService(test_database)
        cement_create = CementCreate(**sample_cement_data)
        
        with patch.object(service, '_validate_cement'):
            with patch.object(test_database, 'get_session') as mock_session:
                mock_session.return_value.__enter__.return_value = Mock()
                
                performance_timer.start()
                
                try:
                    service.create(cement_create)
                except:
                    pass  # We're testing performance, not functionality
                
                elapsed = performance_timer.stop()
                
                # Cement creation should be fast
                assert elapsed < 0.1, f"Cement creation took {elapsed:.3f}s, expected < 0.1s"

    def test_bulk_operations_performance(self, test_database, performance_timer):
        """Test performance of bulk cement operations."""
        service = CementService(test_database)
        
        # Mock database operations
        with patch.object(test_database, 'get_read_only_session') as mock_session:
            mock_session.return_value.__enter__.return_value.query.return_value.order_by.return_value.all.return_value = []
            
            performance_timer.start()
            
            # Simulate multiple get_all calls
            for _ in range(100):
                service.get_all()
            
            elapsed = performance_timer.stop()
            
            # 100 operations should complete quickly
            assert elapsed < 1.0, f"100 get_all operations took {elapsed:.3f}s, expected < 1.0s"


# Integration fixtures for cement testing

@pytest.fixture
def cement_service_with_data(test_database, sample_cement_data):
    """Cement service with test data pre-loaded."""
    service = CementService(test_database)
    
    # Mock successful creation
    with patch.object(service, '_validate_cement'):
        with patch.object(test_database, 'get_session') as mock_session:
            mock_session.return_value.__enter__.return_value = Mock()
            
            cement_create = CementCreate(**sample_cement_data)
            service.create(cement_create)
    
    return service


@pytest.fixture
def multiple_cements_data():
    """Multiple cement data sets for testing."""
    return [
        {
            'name': 'Type I Portland',
            'type': 'Type I',
            'sio2': 20.1, 'al2o3': 5.1, 'fe2o3': 3.0, 'cao': 64.8,
            'mgo': 2.9, 'so3': 2.6, 'specific_surface_area': 350
        },
        {
            'name': 'Type II Portland',
            'type': 'Type II', 
            'sio2': 21.2, 'al2o3': 4.8, 'fe2o3': 3.2, 'cao': 63.5,
            'mgo': 3.1, 'so3': 2.2, 'specific_surface_area': 370
        },
        {
            'name': 'Type III High Early',
            'type': 'Type III',
            'sio2': 20.8, 'al2o3': 5.5, 'fe2o3': 2.9, 'cao': 64.2,
            'mgo': 2.7, 'so3': 3.0, 'specific_surface_area': 450
        }
    ]
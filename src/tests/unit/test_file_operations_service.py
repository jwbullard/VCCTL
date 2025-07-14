#!/usr/bin/env python3
"""
Unit Tests for File Operations Service

Tests for file import/export, validation, and simulation file generation.
"""

import pytest
import json
import csv
from unittest.mock import Mock, patch, mock_open, MagicMock
from pathlib import Path
from io import StringIO
from typing import Dict, Any

from app.services.file_operations_service import FileOperationsService
from app.services.directories_service import DirectoriesService
from app.utils.file_operations import FileValidator, ValidationResult


class TestFileOperationsService:
    """Test suite for FileOperationsService."""

    @pytest.fixture
    def mock_directories_service(self):
        """Mock directories service."""
        mock_service = Mock(spec=DirectoriesService)
        mock_service.get_materials_directory.return_value = Path("/test/materials")
        mock_service.get_output_directory.return_value = Path("/test/output")
        mock_service.get_temp_directory.return_value = Path("/test/temp")
        return mock_service

    @pytest.fixture
    def file_service(self, mock_directories_service):
        """File operations service with mocked dependencies."""
        return FileOperationsService(mock_directories_service)

    @pytest.mark.unit
    def test_init(self, mock_directories_service):
        """Test service initialization."""
        service = FileOperationsService(mock_directories_service)
        
        assert service.directories_service == mock_directories_service
        assert hasattr(service, 'file_importer')
        assert hasattr(service, 'validator')
        assert hasattr(service, 'parallel_writer')
        assert service.logger.name == 'VCCTL.Services.FileOperations'

    @pytest.mark.unit
    def test_import_material_from_json_success(self, file_service, sample_cement_data, temp_directory):
        """Test successful JSON material import."""
        json_file = temp_directory / "test_cement.json"
        json_file.write_text(json.dumps(sample_cement_data))
        
        # Mock file validation
        mock_validation = ValidationResult(is_valid=True, errors=[])
        with patch.object(file_service.validator, 'validate_file', return_value=mock_validation):
            result = file_service.import_material_from_file(json_file, 'cement')
            
            assert result == sample_cement_data
            assert result['name'] == sample_cement_data['name']

    @pytest.mark.unit
    def test_import_material_validation_failure(self, file_service, temp_directory):
        """Test material import with validation failure."""
        json_file = temp_directory / "invalid.json"
        json_file.write_text('invalid json')
        
        # Mock file validation failure
        mock_validation = ValidationResult(is_valid=False, errors=['Invalid format'])
        with patch.object(file_service.validator, 'validate_file', return_value=mock_validation):
            with pytest.raises(ValueError, match="File validation failed"):
                file_service.import_material_from_file(json_file, 'cement')

    @pytest.mark.unit
    def test_import_material_unsupported_format(self, file_service, temp_directory):
        """Test import with unsupported file format."""
        txt_file = temp_directory / "test.txt"
        txt_file.write_text("some content")
        
        # Mock successful validation
        mock_validation = ValidationResult(is_valid=True, errors=[])
        with patch.object(file_service.validator, 'validate_file', return_value=mock_validation):
            with pytest.raises(ValueError, match="Unsupported file format"):
                file_service.import_material_from_file(txt_file, 'cement')

    @pytest.mark.unit
    def test_import_csv_material_success(self, file_service, temp_directory):
        """Test successful CSV material import."""
        csv_content = """name,type,sio2,al2o3,fe2o3,cao,mgo,so3
Test Cement,Type I,20.5,5.2,3.1,65.0,2.8,2.4"""
        
        csv_file = temp_directory / "test_cement.csv"
        csv_file.write_text(csv_content)
        
        # Mock file validation
        mock_validation = ValidationResult(is_valid=True, errors=[])
        with patch.object(file_service.validator, 'validate_file', return_value=mock_validation):
            result = file_service.import_material_from_file(csv_file, 'cement')
            
            assert result['name'] == 'Test Cement'
            assert result['type'] == 'Type I'
            assert result['sio2'] == 20.5

    @pytest.mark.unit
    def test_export_material_to_json(self, file_service, sample_cement_data, temp_directory):
        """Test material export to JSON format."""
        export_path = temp_directory / "export_cement.json"
        
        with patch('pathlib.Path.write_bytes') as mock_write:
            file_service.export_material_to_file(sample_cement_data, export_path, 'json')
            
            mock_write.assert_called_once()
            written_data = mock_write.call_args[0][0]
            
            # Verify JSON content
            parsed_data = json.loads(written_data.decode('utf-8'))
            assert parsed_data == sample_cement_data

    @pytest.mark.unit
    def test_export_material_to_csv(self, file_service, sample_cement_data, temp_directory):
        """Test material export to CSV format."""
        export_path = temp_directory / "export_cement.csv"
        
        with patch.object(file_service, '_export_csv_material') as mock_csv_export:
            mock_csv_export.return_value = b"csv,content,here"
            
            with patch('pathlib.Path.write_bytes') as mock_write:
                file_service.export_material_to_file(sample_cement_data, export_path, 'csv')
                
                mock_csv_export.assert_called_once_with(sample_cement_data)
                mock_write.assert_called_once_with(b"csv,content,here")

    @pytest.mark.unit 
    def test_export_material_unsupported_format(self, file_service, sample_cement_data, temp_directory):
        """Test export with unsupported format."""
        export_path = temp_directory / "export_cement.txt"
        
        with pytest.raises(ValueError, match="Unsupported export format"):
            file_service.export_material_to_file(sample_cement_data, export_path, 'txt')

    @pytest.mark.unit
    def test_bulk_import_materials_success(self, file_service, temp_directory):
        """Test bulk material import."""
        # Create test files
        cement_data = {"name": "Cement1", "type": "Type I", "sio2": 20.0}
        flyash_data = {"name": "FlyAsh1", "type": "Class F", "sio2": 55.0}
        
        cement_file = temp_directory / "cement1.json"
        flyash_file = temp_directory / "flyash1.json"
        
        cement_file.write_text(json.dumps(cement_data))
        flyash_file.write_text(json.dumps(flyash_data))
        
        file_paths = [cement_file, flyash_file]
        material_types = ['cement', 'flyash']
        
        # Mock validation
        mock_validation = ValidationResult(is_valid=True, errors=[])
        with patch.object(file_service.validator, 'validate_file', return_value=mock_validation):
            results = file_service.bulk_import_materials(file_paths, material_types)
            
            assert len(results) == 2
            assert results[0] == cement_data
            assert results[1] == flyash_data

    @pytest.mark.unit
    def test_bulk_import_materials_partial_failure(self, file_service, temp_directory):
        """Test bulk import with some files failing."""
        # Create valid and invalid files
        valid_data = {"name": "Valid", "type": "Type I", "sio2": 20.0}
        
        valid_file = temp_directory / "valid.json"
        invalid_file = temp_directory / "invalid.json"
        
        valid_file.write_text(json.dumps(valid_data))
        invalid_file.write_text("invalid json")
        
        file_paths = [valid_file, invalid_file]
        material_types = ['cement', 'cement']
        
        # Mock validation - first file valid, second invalid
        def mock_validate(path, **kwargs):
            if path == valid_file:
                return ValidationResult(is_valid=True, errors=[])
            else:
                return ValidationResult(is_valid=False, errors=['Invalid JSON'])
        
        with patch.object(file_service.validator, 'validate_file', side_effect=mock_validate):
            results = file_service.bulk_import_materials(file_paths, material_types)
            
            # Should return results for valid files and None for invalid
            assert len(results) == 2
            assert results[0] == valid_data
            assert results[1] is None

    @pytest.mark.unit
    def test_generate_simulation_files_success(self, file_service, temp_directory):
        """Test simulation file generation."""
        materials = {
            'cement': {'name': 'Test Cement', 'sio2': 20.0},
            'aggregate': {'name': 'Test Sand', 'density': 2.65}
        }
        
        with patch.object(file_service, '_generate_material_files') as mock_gen_files:
            mock_gen_files.return_value = ['file1.dat', 'file2.dat']
            
            with patch.object(file_service, '_generate_mix_file') as mock_gen_mix:
                mock_gen_mix.return_value = 'mix.dat'
                
                result = file_service.generate_simulation_files(materials, temp_directory)
                
                mock_gen_files.assert_called_once_with(materials, temp_directory)
                mock_gen_mix.assert_called_once_with(materials, temp_directory)
                
                assert 'material_files' in result
                assert 'mix_file' in result

    @pytest.mark.unit
    def test_validate_imported_data_cement(self, file_service):
        """Test validation of imported cement data."""
        valid_cement = {
            'name': 'Test Cement',
            'type': 'Type I',
            'sio2': 20.0, 'al2o3': 5.0, 'fe2o3': 3.0, 'cao': 65.0,
            'mgo': 2.0, 'so3': 2.0, 'k2o': 1.0, 'na2o': 1.0
        }
        
        is_valid, errors = file_service.validate_imported_data(valid_cement, 'cement')
        assert is_valid
        assert len(errors) == 0

    @pytest.mark.unit
    def test_validate_imported_data_cement_invalid(self, file_service):
        """Test validation of invalid cement data."""
        invalid_cement = {
            'name': '',  # Empty name
            'sio2': -5.0,  # Negative percentage
            'cao': 150.0  # Percentage > 100
        }
        
        is_valid, errors = file_service.validate_imported_data(invalid_cement, 'cement')
        assert not is_valid
        assert len(errors) > 0
        assert any('name' in error.lower() for error in errors)

    @pytest.mark.unit
    def test_archive_files_success(self, file_service, temp_directory):
        """Test file archiving functionality."""
        # Create test files
        file1 = temp_directory / "file1.txt"
        file2 = temp_directory / "file2.txt"
        file1.write_text("content1")
        file2.write_text("content2")
        
        archive_path = temp_directory / "archive.zip"
        
        with patch('zipfile.ZipFile') as mock_zipfile:
            mock_zip = MagicMock()
            mock_zipfile.return_value.__enter__.return_value = mock_zip
            
            result = file_service.archive_files([file1, file2], archive_path)
            
            assert result == archive_path
            assert mock_zip.write.call_count == 2


class TestFileOperationsHelpers:
    """Test helper methods for file operations."""

    @pytest.fixture
    def file_service(self, mock_directories_service):
        """File operations service."""
        mock_service = Mock(spec=DirectoriesService)
        return FileOperationsService(mock_service)

    @pytest.mark.unit
    def test_export_csv_material(self, file_service, sample_cement_data):
        """Test CSV export helper method."""
        result = file_service._export_csv_material(sample_cement_data)
        
        assert isinstance(result, bytes)
        
        # Parse CSV and verify content
        csv_content = result.decode('utf-8')
        reader = csv.DictReader(StringIO(csv_content))
        rows = list(reader)
        
        assert len(rows) == 1
        assert rows[0]['name'] == sample_cement_data['name']

    @pytest.mark.unit
    def test_import_json_material(self, file_service, temp_directory, sample_cement_data):
        """Test JSON import helper method."""
        json_file = temp_directory / "test.json"
        json_file.write_text(json.dumps(sample_cement_data))
        
        result = file_service._import_json_material(json_file)
        assert result == sample_cement_data

    @pytest.mark.unit
    def test_import_json_material_invalid(self, file_service, temp_directory):
        """Test JSON import with invalid JSON."""
        json_file = temp_directory / "invalid.json"
        json_file.write_text("invalid json content")
        
        with pytest.raises(json.JSONDecodeError):
            file_service._import_json_material(json_file)

    @pytest.mark.unit
    def test_generate_material_files(self, file_service, temp_directory):
        """Test material file generation."""
        materials = {
            'cement': {'name': 'Test Cement', 'sio2': 20.0},
            'flyash': {'name': 'Test Fly Ash', 'sio2': 55.0}
        }
        
        with patch('pathlib.Path.write_text') as mock_write:
            result = file_service._generate_material_files(materials, temp_directory)
            
            assert isinstance(result, list)
            assert len(result) >= len(materials)
            assert mock_write.call_count >= len(materials)

    @pytest.mark.unit
    def test_generate_mix_file(self, file_service, temp_directory):
        """Test mix file generation."""
        materials = {
            'cement': {'name': 'Test Cement', 'content': 350.0},
            'water': {'content': 175.0}
        }
        
        with patch('pathlib.Path.write_text') as mock_write:
            result = file_service._generate_mix_file(materials, temp_directory)
            
            assert isinstance(result, str)
            mock_write.assert_called_once()


@pytest.mark.filesystem
class TestFileOperationsIntegration:
    """Integration tests requiring filesystem access."""

    def test_real_file_import_export_cycle(self, temp_directory, sample_cement_data):
        """Test complete import/export cycle with real files."""
        # Setup service with real directories service
        from app.services.directories_service import DirectoriesService
        from app.config.user_config import UserConfig
        
        user_config = UserConfig()
        user_config.materials_dir = str(temp_directory / "materials")
        user_config.output_dir = str(temp_directory / "output")
        user_config.temp_dir = str(temp_directory / "temp")
        
        # Create directories
        Path(user_config.materials_dir).mkdir(exist_ok=True)
        Path(user_config.output_dir).mkdir(exist_ok=True)
        Path(user_config.temp_dir).mkdir(exist_ok=True)
        
        directories_service = DirectoriesService(user_config)
        file_service = FileOperationsService(directories_service)
        
        # Export data to file
        export_path = temp_directory / "test_cement.json"
        file_service.export_material_to_file(sample_cement_data, export_path, 'json')
        
        # Verify file was created
        assert export_path.exists()
        
        # Import data back
        imported_data = file_service.import_material_from_file(export_path, 'cement')
        
        # Verify data integrity
        assert imported_data == sample_cement_data


@pytest.mark.performance
class TestFileOperationsPerformance:
    """Performance tests for file operations."""

    def test_bulk_import_performance(self, temp_directory, performance_timer):
        """Test performance of bulk import operations."""
        from app.services.directories_service import DirectoriesService
        
        # Create mock service
        mock_directories = Mock(spec=DirectoriesService)
        file_service = FileOperationsService(mock_directories)
        
        # Create multiple test files
        test_data = {"name": "Test", "type": "Type I", "sio2": 20.0}
        files = []
        
        for i in range(50):
            test_file = temp_directory / f"test_{i}.json"
            test_file.write_text(json.dumps(test_data))
            files.append(test_file)
        
        material_types = ['cement'] * 50
        
        # Mock validation to always pass
        mock_validation = ValidationResult(is_valid=True, errors=[])
        with patch.object(file_service.validator, 'validate_file', return_value=mock_validation):
            performance_timer.start()
            
            results = file_service.bulk_import_materials(files, material_types)
            
            elapsed = performance_timer.stop()
            
            # Should process 50 files quickly
            assert len(results) == 50
            assert elapsed < 5.0, f"Bulk import took {elapsed:.3f}s, expected < 5.0s"

    def test_large_file_export_performance(self, temp_directory, performance_timer):
        """Test performance of large file export."""
        mock_directories = Mock(spec=DirectoriesService)
        file_service = FileOperationsService(mock_directories)
        
        # Create large data set
        large_data = {
            'name': 'Large Dataset',
            'data': [{'item': i, 'value': i * 1.5} for i in range(10000)]
        }
        
        export_path = temp_directory / "large_export.json"
        
        performance_timer.start()
        
        file_service.export_material_to_file(large_data, export_path, 'json')
        
        elapsed = performance_timer.stop()
        
        # Large export should complete in reasonable time
        assert elapsed < 2.0, f"Large export took {elapsed:.3f}s, expected < 2.0s"


# Mock fixtures for file operations testing

@pytest.fixture
def mock_file_validator():
    """Mock file validator."""
    validator = Mock(spec=FileValidator)
    validator.validate_file.return_value = ValidationResult(is_valid=True, errors=[])
    return validator


@pytest.fixture
def mock_parallel_writer():
    """Mock parallel file writer."""
    writer = Mock()
    writer.write_files_parallel.return_value = True
    return writer
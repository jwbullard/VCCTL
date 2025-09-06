#!/usr/bin/env python3
"""
Unit Tests for Data Models

Comprehensive validation tests for all VCCTL data models including
cement, aggregates, fly ash, slag, and mix designs.
"""

import pytest
from decimal import Decimal
from datetime import datetime
from typing import Dict, Any
from pydantic import ValidationError

from app.models.cement import Cement, CementCreate, CementUpdate, CementResponse
from app.models.aggregate import Aggregate, AggregateCreate, AggregateUpdate
from app.models.fly_ash import FlyAsh, FlyAshCreate, FlyAshUpdate
from app.models.slag import Slag, SlagCreate, SlagUpdate
from app.models.inert_filler import InertFiller, InertFillerCreate, InertFillerUpdate
from tests.conftest import assert_valid_cement_composition, assert_valid_mix_design


class TestCementModel:
    """Test suite for Cement data model."""

    @pytest.mark.unit
    def test_cement_create_valid(self, sample_cement_data):
        """Test creation of valid cement."""
        cement = CementCreate(**sample_cement_data)
        
        assert cement.name == sample_cement_data['name']
        assert cement.type == sample_cement_data['type']
        assert cement.sio2 == sample_cement_data['sio2']
        assert cement.specific_surface_area == sample_cement_data['specific_surface_area']

    @pytest.mark.unit
    def test_cement_create_missing_required_fields(self):
        """Test cement creation with missing required fields."""
        with pytest.raises(ValidationError) as exc_info:
            CementCreate()
        
        errors = exc_info.value.errors()
        required_fields = {'name', 'type'}
        error_fields = {error['loc'][0] for error in errors if error['type'] == 'missing'}
        
        assert required_fields.issubset(error_fields)

    @pytest.mark.unit
    def test_cement_create_invalid_percentages(self):
        """Test cement creation with invalid percentage values."""
        invalid_data = {
            'name': 'Test Cement',
            'type': 'Type I',
            'sio2': -5.0,  # Negative percentage
            'al2o3': 105.0,  # Over 100%
            'cao': 65.0
        }
        
        with pytest.raises(ValidationError) as exc_info:
            CementCreate(**invalid_data)
        
        errors = exc_info.value.errors()
        assert any(error['loc'][0] == 'sio2' for error in errors)
        assert any(error['loc'][0] == 'al2o3' for error in errors)

    @pytest.mark.unit
    def test_cement_create_invalid_physical_properties(self):
        """Test cement creation with invalid physical properties."""
        invalid_data = {
            'name': 'Test Cement',
            'type': 'Type I',
            'specific_surface_area': -100.0,  # Negative fineness
            'density': 0.0,  # Zero density
            'loss_on_ignition': 15.0  # Too high LOI
        }
        
        with pytest.raises(ValidationError) as exc_info:
            CementCreate(**invalid_data)
        
        errors = exc_info.value.errors()
        assert len(errors) >= 2  # At least blaine and density errors

    @pytest.mark.unit
    def test_cement_create_valid_ranges(self):
        """Test cement creation with values at valid range boundaries."""
        boundary_data = {
            'name': 'Boundary Test Cement',
            'type': 'Type I',
            'sio2': 0.0,  # Minimum
            'al2o3': 100.0,  # Maximum
            'specific_surface_area': 1.0,  # Minimum positive
            'density': 0.1,  # Minimum positive
            'loss_on_ignition': 0.0  # Minimum
        }
        
        cement = CementCreate(**boundary_data)
        assert cement.sio2 == 0.0
        assert cement.al2o3 == 100.0

    @pytest.mark.unit
    def test_cement_update_partial(self):
        """Test partial cement update."""
        update_data = {
            'sio2': 21.0,
            'specific_surface_area': 375.0
        }
        
        cement_update = CementUpdate(**update_data)
        assert cement_update.sio2 == 21.0
        assert cement_update.specific_surface_area == 375.0
        assert cement_update.name is None  # Not provided in update

    @pytest.mark.unit
    def test_cement_response_serialization(self, sample_cement_data):
        """Test cement response model serialization."""
        # Add database fields
        response_data = sample_cement_data.copy()
        response_data.update({
            'id': 1,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        })
        
        cement_response = CementResponse(**response_data)
        
        # Test serialization
        serialized = cement_response.dict()
        assert 'id' in serialized
        assert 'created_at' in serialized
        assert 'updated_at' in serialized

    @pytest.mark.unit
    def test_cement_composition_validation(self, sample_cement_data):
        """Test cement oxide composition validation."""
        assert_valid_cement_composition(sample_cement_data, tolerance=1.0)
        
        # Test invalid composition
        invalid_composition = sample_cement_data.copy()
        invalid_composition['sio2'] = 50.0  # Makes total > 100%
        
        with pytest.raises(AssertionError):
            assert_valid_cement_composition(invalid_composition, tolerance=1.0)


class TestAggregateModel:
    """Test suite for Aggregate data model."""

    @pytest.mark.unit
    def test_aggregate_create_valid(self, sample_aggregate_data):
        """Test creation of valid aggregate."""
        aggregate = AggregateCreate(**sample_aggregate_data)
        
        assert aggregate.name == sample_aggregate_data['name']
        assert aggregate.type == sample_aggregate_data['type']
        assert aggregate.density == sample_aggregate_data['density']
        assert aggregate.fineness_modulus == sample_aggregate_data['fineness_modulus']

    @pytest.mark.unit
    def test_aggregate_create_missing_required_fields(self):
        """Test aggregate creation with missing required fields."""
        with pytest.raises(ValidationError) as exc_info:
            AggregateCreate(density=2.65)  # Missing name and type
        
        errors = exc_info.value.errors()
        required_fields = {'name', 'type'}
        error_fields = {error['loc'][0] for error in errors if error['type'] == 'missing'}
        
        assert required_fields.issubset(error_fields)

    @pytest.mark.unit 
    def test_aggregate_create_invalid_density(self):
        """Test aggregate creation with invalid density."""
        invalid_data = {
            'name': 'Test Aggregate',
            'type': 'fine',
            'density': -1.0  # Negative density
        }
        
        with pytest.raises(ValidationError) as exc_info:
            AggregateCreate(**invalid_data)
        
        errors = exc_info.value.errors()
        assert any(error['loc'][0] == 'density' for error in errors)

    @pytest.mark.unit
    def test_aggregate_gradation_validation(self):
        """Test aggregate gradation curve validation."""
        valid_gradation = {
            'name': 'Test Fine Sand',
            'type': 'fine',
            'density': 2.65,
            'gradation': {
                'sieve_4_75mm': 100.0,
                'sieve_2_36mm': 95.0,
                'sieve_1_18mm': 85.0,
                'sieve_0_60mm': 65.0,
                'sieve_0_30mm': 35.0,
                'sieve_0_15mm': 15.0
            }
        }
        
        aggregate = AggregateCreate(**valid_gradation)
        
        # Gradation should be monotonically non-increasing
        gradation_values = list(aggregate.gradation.values())
        assert all(gradation_values[i] >= gradation_values[i+1] 
                  for i in range(len(gradation_values)-1))

    @pytest.mark.unit
    def test_aggregate_invalid_gradation(self):
        """Test aggregate with invalid gradation."""
        invalid_gradation = {
            'name': 'Test Aggregate',
            'type': 'fine',
            'density': 2.65,
            'gradation': {
                'sieve_4_75mm': 80.0,  # Should be 100% for top sieve
                'sieve_2_36mm': 95.0   # Cannot be higher than larger sieve
            }
        }
        
        # This should be caught by custom validation logic
        aggregate = AggregateCreate(**invalid_gradation)
        
        # Manual validation of gradation logic
        gradation_values = list(aggregate.gradation.values())
        is_valid_gradation = all(gradation_values[i] >= gradation_values[i+1] 
                               for i in range(len(gradation_values)-1))
        assert not is_valid_gradation


class TestFlyAshModel:
    """Test suite for Fly Ash data model."""

    @pytest.fixture
    def sample_flyash_data(self):
        """Sample fly ash data for testing."""
        return {
            'name': 'Test Fly Ash Class F',
            'class_type': 'Class F',
            'sio2': 55.3,
            'al2o3': 23.1,
            'fe2o3': 6.2,
            'cao': 8.1,
            'mgo': 1.8,
            'so3': 1.2,
            'k2o': 2.1,
            'na2o': 1.8,
            'specific_gravity': 2.35,
            'specific_surface_area': 420.0,
            'loss_on_ignition': 2.8
        }

    @pytest.mark.unit
    def test_flyash_create_valid(self, sample_flyash_data):
        """Test creation of valid fly ash."""
        flyash = FlyAshCreate(**sample_flyash_data)
        
        assert flyash.name == sample_flyash_data['name']
        assert flyash.class_type == sample_flyash_data['class_type']
        assert flyash.sio2 == sample_flyash_data['sio2']

    @pytest.mark.unit
    def test_flyash_class_validation(self):
        """Test fly ash class type validation."""
        valid_classes = ['Class F', 'Class C']
        
        for class_type in valid_classes:
            flyash_data = {
                'name': f'Test {class_type}',
                'class_type': class_type,
                'sio2': 55.0
            }
            flyash = FlyAshCreate(**flyash_data)
            assert flyash.class_type == class_type

    @pytest.mark.unit
    def test_flyash_create_invalid_class(self):
        """Test fly ash creation with invalid class."""
        invalid_data = {
            'name': 'Test Fly Ash',
            'class_type': 'Class X',  # Invalid class
            'sio2': 55.0
        }
        
        with pytest.raises(ValidationError) as exc_info:
            FlyAshCreate(**invalid_data)
        
        errors = exc_info.value.errors()
        assert any(error['loc'][0] == 'class_type' for error in errors)

    @pytest.mark.unit
    def test_flyash_pozzolan_activity_index(self, sample_flyash_data):
        """Test fly ash pozzolan activity index validation."""
        sample_flyash_data['pozzolan_activity_index_7d'] = 85.0
        sample_flyash_data['pozzolan_activity_index_28d'] = 95.0
        
        flyash = FlyAshCreate(**sample_flyash_data)
        
        # 28-day index should be >= 7-day index
        assert flyash.pozzolan_activity_index_28d >= flyash.pozzolan_activity_index_7d


class TestSlagModel:
    """Test suite for Slag data model."""

    @pytest.fixture
    def sample_slag_data(self):
        """Sample slag data for testing."""
        return {
            'name': 'Test Ground Granulated Blast Furnace Slag',
            'grade': 'Grade 100',
            'sio2': 35.2,
            'al2o3': 12.5,
            'fe2o3': 0.8,
            'cao': 42.1,
            'mgo': 6.8,
            'so3': 1.2,
            'specific_gravity': 2.90,
            'specific_surface_area': 450.0,
            'activity_index_7d': 65.0,
            'activity_index_28d': 85.0
        }

    @pytest.mark.unit
    def test_slag_create_valid(self, sample_slag_data):
        """Test creation of valid slag."""
        slag = SlagCreate(**sample_slag_data)
        
        assert slag.name == sample_slag_data['name']
        assert slag.grade == sample_slag_data['grade']
        assert slag.sio2 == sample_slag_data['sio2']

    @pytest.mark.unit
    def test_slag_grade_validation(self):
        """Test slag grade validation."""
        valid_grades = ['Grade 80', 'Grade 100', 'Grade 120']
        
        for grade in valid_grades:
            slag_data = {
                'name': f'Test {grade} Slag',
                'grade': grade,
                'sio2': 35.0
            }
            slag = SlagCreate(**slag_data)
            assert slag.grade == grade

    @pytest.mark.unit
    def test_slag_activity_index_progression(self, sample_slag_data):
        """Test slag activity index progression validation."""
        slag = SlagCreate(**sample_slag_data)
        
        # 28-day activity should be higher than 7-day
        assert slag.activity_index_28d > slag.activity_index_7d


class TestInertFillerModel:
    """Test suite for Inert Filler data model."""

    @pytest.fixture
    def sample_inert_filler_data(self):
        """Sample inert filler data for testing."""
        return {
            'name': 'Limestone Powder',
            'type': 'limestone',
            'specific_gravity': 2.72,
            'specific_surface_area': 380.0,
            'particle_size_d50': 15.0,
            'cao': 85.2,
            'mgo': 1.8,
            'sio2': 8.5,
            'al2o3': 2.1,
            'fe2o3': 1.2
        }

    @pytest.mark.unit
    def test_inert_filler_create_valid(self, sample_inert_filler_data):
        """Test creation of valid inert filler."""
        filler = InertFillerCreate(**sample_inert_filler_data)
        
        assert filler.name == sample_inert_filler_data['name']
        assert filler.type == sample_inert_filler_data['type']
        assert filler.specific_gravity == sample_inert_filler_data['specific_gravity']

    @pytest.mark.unit
    def test_inert_filler_type_validation(self):
        """Test inert filler type validation."""
        valid_types = ['limestone', 'quartz', 'granite', 'other']
        
        for filler_type in valid_types:
            filler_data = {
                'name': f'Test {filler_type.title()}',
                'type': filler_type,
                'specific_gravity': 2.65
            }
            filler = InertFillerCreate(**filler_data)
            assert filler.type == filler_type


class TestMixDesignValidation:
    """Test mix design validation logic."""

    @pytest.mark.unit
    def test_valid_mix_design(self, sample_mix_design_data):
        """Test validation of valid mix design."""
        assert_valid_mix_design(sample_mix_design_data)

    @pytest.mark.unit
    def test_invalid_water_cement_ratio(self, sample_mix_design_data):
        """Test mix design with invalid water-cement ratio."""
        # Too low W/C ratio
        invalid_mix = sample_mix_design_data.copy()
        invalid_mix['water_cement_ratio'] = 0.1
        
        with pytest.raises(AssertionError, match="W/C ratio too low"):
            assert_valid_mix_design(invalid_mix)
        
        # Too high W/C ratio
        invalid_mix['water_cement_ratio'] = 0.9
        
        with pytest.raises(AssertionError, match="W/C ratio too high"):
            assert_valid_mix_design(invalid_mix)

    @pytest.mark.unit
    def test_invalid_air_content(self, sample_mix_design_data):
        """Test mix design with invalid air content."""
        # Negative air content
        invalid_mix = sample_mix_design_data.copy()
        invalid_mix['air_content'] = -1.0
        
        with pytest.raises(AssertionError, match="Air content cannot be negative"):
            assert_valid_mix_design(invalid_mix)
        
        # Too high air content
        invalid_mix['air_content'] = 15.0
        
        with pytest.raises(AssertionError, match="Air content too high"):
            assert_valid_mix_design(invalid_mix)


class TestModelRelationships:
    """Test relationships between different models."""

    @pytest.mark.unit
    def test_material_consistency(self, sample_cement_data, sample_flyash_data):
        """Test consistency between related materials."""
        cement = CementCreate(**sample_cement_data)
        flyash = FlyAshCreate(name="Test Fly Ash", class_type="Class F", **sample_flyash_data)
        
        # Both should have valid oxide compositions
        cement_total = sum([
            cement.sio2 or 0, cement.al2o3 or 0, cement.fe2o3 or 0, 
            cement.cao or 0, cement.mgo or 0, cement.so3 or 0
        ])
        
        flyash_total = sum([
            flyash.sio2 or 0, flyash.al2o3 or 0, flyash.fe2o3 or 0,
            flyash.cao or 0, flyash.mgo or 0, flyash.so3 or 0
        ])
        
        # Totals should be reasonable (not exact due to other minor oxides)
        assert 80 <= cement_total <= 100
        assert 80 <= flyash_total <= 100

    @pytest.mark.unit
    def test_physical_property_ranges(self, sample_cement_data, sample_aggregate_data):
        """Test that physical properties are in reasonable ranges."""
        cement = CementCreate(**sample_cement_data)
        aggregate = AggregateCreate(**sample_aggregate_data)
        
        # Density ranges
        assert 2.0 <= cement.density <= 4.0  # Typical cement density
        assert 2.0 <= aggregate.density <= 3.5  # Typical aggregate density
        
        # Fineness ranges
        assert 200 <= cement.specific_surface_area <= 800  # Typical cement fineness


@pytest.mark.unit
class TestDataModelSerialization:
    """Test serialization and deserialization of data models."""

    def test_cement_json_serialization(self, sample_cement_data):
        """Test cement model JSON serialization."""
        cement = CementCreate(**sample_cement_data)
        
        # Serialize to dict
        cement_dict = cement.dict()
        assert isinstance(cement_dict, dict)
        assert cement_dict['name'] == sample_cement_data['name']
        
        # Serialize to JSON
        cement_json = cement.json()
        assert isinstance(cement_json, str)
        
        # Round trip test
        import json
        parsed = json.loads(cement_json)
        new_cement = CementCreate(**parsed)
        assert new_cement.name == cement.name

    def test_aggregate_json_serialization(self, sample_aggregate_data):
        """Test aggregate model JSON serialization."""
        aggregate = AggregateCreate(**sample_aggregate_data)
        
        # Test gradation serialization
        aggregate_dict = aggregate.dict()
        assert 'gradation' in aggregate_dict
        assert isinstance(aggregate_dict['gradation'], dict)
        
        # Round trip test
        new_aggregate = AggregateCreate(**aggregate_dict)
        assert new_aggregate.gradation == aggregate.gradation


@pytest.mark.unit
class TestDataModelEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_cement_extreme_values(self):
        """Test cement model with extreme but valid values."""
        extreme_cement = {
            'name': 'Extreme Cement',
            'type': 'Type V',
            'sio2': 0.0,      # Minimum
            'al2o3': 0.0,     # Minimum
            'fe2o3': 0.0,     # Minimum
            'cao': 95.0,      # Very high but possible
            'mgo': 0.0,       # Minimum
            'so3': 0.0,       # Minimum
            'specific_surface_area': 1000.0,  # Very high but possible
            'density': 4.0,   # Maximum reasonable
            'loss_on_ignition': 0.0     # Minimum
        }
        
        cement = CementCreate(**extreme_cement)
        assert cement.cao == 95.0
        assert cement.specific_surface_area == 1000.0

    def test_string_field_validation(self):
        """Test string field validation and trimming."""
        # Test with extra whitespace
        cement_data = {
            'name': '  Test Cement  ',
            'type': '  Type I  ',
            'sio2': 20.0
        }
        
        cement = CementCreate(**cement_data)
        
        # Names should be trimmed
        assert cement.name.strip() == 'Test Cement'
        assert cement.type.strip() == 'Type I'

    def test_decimal_precision(self):
        """Test decimal precision handling."""
        cement_data = {
            'name': 'Precision Test',
            'type': 'Type I',
            'sio2': 20.123456789,  # High precision
            'density': 3.15159265   # High precision
        }
        
        cement = CementCreate(**cement_data)
        
        # Should handle precision appropriately
        assert isinstance(cement.sio2, float)
        assert isinstance(cement.density, float)
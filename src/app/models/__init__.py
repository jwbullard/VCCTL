#!/usr/bin/env python3
"""
VCCTL Models Package

Contains all SQLAlchemy models for the VCCTL application.
Converted from Java JPA entities to Python SQLAlchemy models.
"""

# Import all models to make them available
from app.models.cement import Cement, CementCreate, CementUpdate, CementResponse
from app.models.fly_ash import FlyAsh, FlyAshCreate, FlyAshUpdate, FlyAshResponse
from app.models.slag import Slag, SlagCreate, SlagUpdate, SlagResponse
from app.models.aggregate import Aggregate, AggregateCreate, AggregateUpdate, AggregateResponse
# Removed InertFiller - replaced with Filler
from app.models.filler import Filler, FillerCreate, FillerUpdate, FillerResponse
from app.models.silica_fume import SilicaFume, SilicaFumeCreate, SilicaFumeUpdate, SilicaFumeResponse
from app.models.limestone import Limestone, LimestoneCreate, LimestoneUpdate, LimestoneResponse
from app.models.psd_data import PSDData, PSDDataCreate, PSDDataUpdate, PSDDataResponse
from app.models.particle_shape_set import ParticleShapeSet, ParticleShapeSetCreate, ParticleShapeSetUpdate, ParticleShapeSetResponse
from app.models.grading import Grading, GradingCreate, GradingUpdate, GradingResponse, GradingType
from app.models.operation import Operation, Result, OperationStatus, OperationType, ResultType
from app.models.db_file import DbFile, DbFileCreate, DbFileUpdate, DbFileResponse
from app.models.aggregate_sieve import AggregateSieve, AggregateSieveCreate, AggregateSieveUpdate, AggregateSieveResponse, SieveType
from app.models.mix_design import MixDesign, MixDesignCreate, MixDesignUpdate, MixDesignResponse, MixDesignComponentData, MixDesignPropertiesData
from app.models.hydration_parameters import HydrationParameters
from app.models.hydration_parameter_set import HydrationParameterSet, HydrationParameterSetCreate, HydrationParameterSetUpdate, HydrationParameterSetResponse
from app.models.temperature_profile import TemperatureProfileDB
from app.models.elastic_moduli_operation import ElasticModuliOperation
from app.models.microstructure_operation import MicrostructureOperation
from app.models.hydration_operation import HydrationOperation

# Export all models for easy importing
__all__ = [
    # SQLAlchemy Models
    'Cement',
    'FlyAsh',
    'Slag',
    'Aggregate', 
    'InertFiller',
    'Filler',
    'SilicaFume',
    'Limestone',
    'PSDData',
    'ParticleShapeSet',
    'Grading',
    'Operation',
    'Result',
    'DbFile',
    'AggregateSieve',
    'MixDesign',
    'HydrationParameters',
    'HydrationParameterSet',
    'TemperatureProfileDB',
    'ElasticModuliOperation',
    'MicrostructureOperation',
    'HydrationOperation',
    
    # Pydantic Create Models
    'CementCreate',
    'FlyAshCreate',
    'SlagCreate',
    'AggregateCreate',
    'InertFillerCreate',
    'FillerCreate',
    'SilicaFumeCreate',
    'LimestoneCreate',
    'ParticleShapeSetCreate',
    'GradingCreate',
    'DbFileCreate',
    'AggregateSieveCreate',
    'MixDesignCreate',
    'HydrationParameterSetCreate',
    
    # Pydantic Update Models
    'CementUpdate',
    'FlyAshUpdate',
    'SlagUpdate',
    'AggregateUpdate',
    'InertFillerUpdate',
    'FillerUpdate',
    'SilicaFumeUpdate',
    'LimestoneUpdate',
    'ParticleShapeSetUpdate',
    'GradingUpdate',
    'DbFileUpdate',
    'AggregateSieveUpdate',
    'MixDesignUpdate',
    'HydrationParameterSetUpdate',
    
    # Pydantic Response Models
    'CementResponse',
    'FlyAshResponse',
    'SlagResponse',
    'AggregateResponse',
    'InertFillerResponse',
    'FillerResponse',
    'SilicaFumeResponse',
    'LimestoneResponse',
    'ParticleShapeSetResponse',
    'GradingResponse',
    'DbFileResponse',
    'AggregateSieveResponse',
    'MixDesignResponse',
    'HydrationParameterSetResponse',
    
    # Enumerations
    'GradingType',
    'OperationStatus',
    'OperationType',
    'ResultType',
    'SieveType',
]


def get_all_models():
    """Get list of all SQLAlchemy model classes."""
    return [
        Cement,
        FlyAsh,
        Slag,
        Aggregate,
        InertFiller,
        Filler,
        SilicaFume,
        Limestone,
        ParticleShapeSet,
        Grading,
        Operation,
        Result,
        DbFile,
        AggregateSieve,
        MixDesign,
        HydrationParameters,
        HydrationParameterSet,
        TemperatureProfileDB,
        ElasticModuliOperation,
        MicrostructureOperation,
        HydrationOperation,
    ]


def get_model_by_name(model_name: str):
    """Get model class by name."""
    model_map = {
        'cement': Cement,
        'fly_ash': FlyAsh,
        'slag': Slag,
        'aggregate': Aggregate,
        'filler': Filler,
        'silica_fume': SilicaFume,
        'limestone': Limestone,
        'particle_shape_set': ParticleShapeSet,
        'grading': Grading,
        'operation': Operation,
        'mix_design': MixDesign,
        'hydration_parameters': HydrationParameters,
        'temperature_profile': TemperatureProfileDB,
        'elastic_moduli_operation': ElasticModuliOperation,
        'microstructure_operation': MicrostructureOperation,
        'hydration_operation': HydrationOperation,
    }
    return model_map.get(model_name.lower())


def get_create_model_by_name(model_name: str):
    """Get Pydantic create model by name."""
    create_model_map = {
        'cement': CementCreate,
        'fly_ash': FlyAshCreate,
        'slag': SlagCreate,
        'aggregate': AggregateCreate,
        'filler': FillerCreate,
        'silica_fume': SilicaFumeCreate,
        'limestone': LimestoneCreate,
        'particle_shape_set': ParticleShapeSetCreate,
        'grading': GradingCreate,
        'operation': OperationCreate,
        'mix_design': MixDesignCreate,
    }
    return create_model_map.get(model_name.lower())


def get_update_model_by_name(model_name: str):
    """Get Pydantic update model by name."""
    update_model_map = {
        'cement': CementUpdate,
        'fly_ash': FlyAshUpdate,
        'slag': SlagUpdate,
        'aggregate': AggregateUpdate,
        'filler': FillerUpdate,
        'silica_fume': SilicaFumeUpdate,
        'limestone': LimestoneUpdate,
        'particle_shape_set': ParticleShapeSetUpdate,
        'grading': GradingUpdate,
        'operation': OperationUpdate,
        'mix_design': MixDesignUpdate,
    }
    return update_model_map.get(model_name.lower())


def get_response_model_by_name(model_name: str):
    """Get Pydantic response model by name."""
    response_model_map = {
        'cement': CementResponse,
        'fly_ash': FlyAshResponse,
        'slag': SlagResponse,
        'aggregate': AggregateResponse,
        'filler': FillerResponse,
        'silica_fume': SilicaFumeResponse,
        'limestone': LimestoneResponse,
        'particle_shape_set': ParticleShapeSetResponse,
        'grading': GradingResponse,
        'operation': OperationResponse,
        'mix_design': MixDesignResponse,
    }
    return response_model_map.get(model_name.lower())
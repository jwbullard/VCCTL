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
from app.models.inert_filler import InertFiller, InertFillerCreate, InertFillerUpdate, InertFillerResponse
from app.models.silica_fume import SilicaFume, SilicaFumeCreate, SilicaFumeUpdate, SilicaFumeResponse
from app.models.limestone import Limestone, LimestoneCreate, LimestoneUpdate, LimestoneResponse
from app.models.particle_shape_set import ParticleShapeSet, ParticleShapeSetCreate, ParticleShapeSetUpdate, ParticleShapeSetResponse
from app.models.grading import Grading, GradingCreate, GradingUpdate, GradingResponse, GradingType
from app.models.operation import Operation, OperationCreate, OperationUpdate, OperationResponse, OperationStatus, OperationType
from app.models.db_file import DbFile, DbFileCreate, DbFileUpdate, DbFileResponse
from app.models.aggregate_sieve import AggregateSieve, AggregateSieveCreate, AggregateSieveUpdate, AggregateSieveResponse, SieveType
from app.models.mix_design import MixDesign, MixDesignCreate, MixDesignUpdate, MixDesignResponse, MixDesignComponentData, MixDesignPropertiesData
from app.models.hydration_parameters import HydrationParameters

# Export all models for easy importing
__all__ = [
    # SQLAlchemy Models
    'Cement',
    'FlyAsh',
    'Slag',
    'Aggregate', 
    'InertFiller',
    'SilicaFume',
    'Limestone',
    'ParticleShapeSet',
    'Grading',
    'Operation',
    'DbFile',
    'AggregateSieve',
    'MixDesign',
    'HydrationParameters',
    
    # Pydantic Create Models
    'CementCreate',
    'FlyAshCreate',
    'SlagCreate',
    'AggregateCreate',
    'InertFillerCreate',
    'SilicaFumeCreate',
    'LimestoneCreate',
    'ParticleShapeSetCreate',
    'GradingCreate',
    'OperationCreate',
    'DbFileCreate',
    'AggregateSieveCreate',
    'MixDesignCreate',
    
    # Pydantic Update Models
    'CementUpdate',
    'FlyAshUpdate',
    'SlagUpdate',
    'AggregateUpdate',
    'InertFillerUpdate',
    'SilicaFumeUpdate',
    'LimestoneUpdate',
    'ParticleShapeSetUpdate',
    'GradingUpdate',
    'OperationUpdate',
    'DbFileUpdate',
    'AggregateSieveUpdate',
    'MixDesignUpdate',
    
    # Pydantic Response Models
    'CementResponse',
    'FlyAshResponse',
    'SlagResponse',
    'AggregateResponse',
    'InertFillerResponse',
    'SilicaFumeResponse',
    'LimestoneResponse',
    'ParticleShapeSetResponse',
    'GradingResponse',
    'OperationResponse',
    'DbFileResponse',
    'AggregateSieveResponse',
    'MixDesignResponse',
    
    # Enumerations
    'GradingType',
    'OperationStatus',
    'OperationType',
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
        SilicaFume,
        Limestone,
        ParticleShapeSet,
        Grading,
        Operation,
        DbFile,
        AggregateSieve,
        MixDesign,
        HydrationParameters,
    ]


def get_model_by_name(model_name: str):
    """Get model class by name."""
    model_map = {
        'cement': Cement,
        'fly_ash': FlyAsh,
        'slag': Slag,
        'aggregate': Aggregate,
        'inert_filler': InertFiller,
        'silica_fume': SilicaFume,
        'limestone': Limestone,
        'particle_shape_set': ParticleShapeSet,
        'grading': Grading,
        'operation': Operation,
        'mix_design': MixDesign,
        'hydration_parameters': HydrationParameters,
    }
    return model_map.get(model_name.lower())


def get_create_model_by_name(model_name: str):
    """Get Pydantic create model by name."""
    create_model_map = {
        'cement': CementCreate,
        'fly_ash': FlyAshCreate,
        'slag': SlagCreate,
        'aggregate': AggregateCreate,
        'inert_filler': InertFillerCreate,
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
        'inert_filler': InertFillerUpdate,
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
        'inert_filler': InertFillerResponse,
        'silica_fume': SilicaFumeResponse,
        'limestone': LimestoneResponse,
        'particle_shape_set': ParticleShapeSetResponse,
        'grading': GradingResponse,
        'operation': OperationResponse,
        'mix_design': MixDesignResponse,
    }
    return response_model_map.get(model_name.lower())
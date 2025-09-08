#!/usr/bin/env python3
"""
Phase 3 Test: Hydration Operations with Clean Naming, Parameter Storage, and Lineage

This test validates that Phase 3 implementation works correctly:
1. Hydration operations use clean user-defined names
2. UI parameters are captured and stored completely
3. Operations are properly linked to parent microstructure operations
4. Complete operation lineage tracking works
5. Operations can be loaded and restored
"""

import json
import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

try:
    from app.database.service import DatabaseService
    from app.models.operation import Operation, OperationStatus, OperationType
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)

def setup_logging():
    """Setup logging for testing."""
    logger = logging.getLogger('Phase3Test')
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
    logger.addHandler(handler)
    return logger

def test_clean_hydration_operation_creation():
    """Test creating a hydration operation with clean naming."""
    logger = logging.getLogger('Phase3Test')
    
    try:
        db_service = DatabaseService()
        
        with db_service.get_session() as session:
            # First create a parent microstructure operation
            parent_ui_params = {
                'mix_name': 'ParentMix',
                'operation_name': 'ParentMicrostructure',
                'components': [
                    {'index': 0, 'type': 'cement', 'name': 'Portland', 'mass_kg_m3': 300.0}
                ],
                'system_size_x': 100,
                'system_size_y': 100,
                'system_size_z': 100,
                'resolution_micrometers': 1.0,
                'captured_at': '2025-01-07T16:00:00'
            }
            
            parent_operation = Operation(
                name='ParentMicrostructure',
                operation_type=OperationType.MICROSTRUCTURE.value,
                status=OperationStatus.COMPLETED.value,
                stored_ui_parameters=parent_ui_params
            )
            session.add(parent_operation)
            session.flush()
            
            # Now create hydration operation with complete UI parameters
            hydration_ui_params = {
                'operation_name': 'MyHydrationTest',
                'operation_type': 'hydration',
                'source_microstructure': {
                    'name': 'ParentMicrostructure',
                    'path': './Operations/ParentMicrostructure'
                },
                'captured_at': '2025-01-07T16:00:00',
                'max_simulation_time_hours': 168.0,
                'target_degree_of_hydration': 0.8,
                'random_seed': 12345,
                'curing_conditions': {
                    'initial_temperature_celsius': 25.0,
                    'thermal_mode': 'isothermal',
                    'moisture_mode': 'saturated',
                    'temperature_profile': 'constant_25c'
                },
                'time_calibration': {
                    'time_conversion_factor': 1.0
                },
                'advanced_settings': {
                    'c3a_fraction': 0.08,
                    'ettringite_formation': True,
                    'csh2_formation': True,
                    'ch_formation': True,
                    'ph_computation': True,
                    'random_seed': 12345
                },
                'database_modifications': {
                    'cement_dissolution_rate': 1.2
                }
            }
            
            # Create hydration operation with lineage
            hydration_operation = Operation(
                name='MyHydrationTest',  # Clean user-defined name
                operation_type=OperationType.HYDRATION.value,
                status=OperationStatus.QUEUED.value,
                stored_ui_parameters=hydration_ui_params,
                parent_operation_id=parent_operation.id  # Phase 3: Lineage tracking
            )
            
            session.add(hydration_operation)
            session.commit()
            
            # Verify operation was saved correctly
            loaded_hydration = session.query(Operation).filter_by(name='MyHydrationTest').first()
            
            if loaded_hydration.name == 'MyHydrationTest':
                logger.info("✓ Clean hydration operation name saved correctly")
            else:
                logger.error(f"✗ Operation name incorrect: expected 'MyHydrationTest', got '{loaded_hydration.name}'")
                return False
            
            # Verify lineage relationship
            if loaded_hydration.parent_operation_id == parent_operation.id:
                logger.info("✓ Hydration-to-microstructure lineage saved correctly")
            else:
                logger.error("✗ Lineage relationship failed")
                return False
            
            # Verify UI parameters were saved
            if loaded_hydration.stored_ui_parameters:
                params = loaded_hydration.stored_ui_parameters
                if params.get('operation_name') == 'MyHydrationTest':
                    logger.info("✓ Hydration UI parameters saved correctly")
                else:
                    logger.error(f"✗ UI parameters corrupted: {params}")
                    return False
            else:
                logger.error("✗ No UI parameters saved")
                return False
            
            # Clean up
            session.delete(hydration_operation)
            session.delete(parent_operation)
            session.commit()
            
            return True
            
    except Exception as e:
        logger.error(f"✗ Clean hydration operation creation test failed: {e}")
        return False

def test_complex_hydration_parameter_storage():
    """Test that complex hydration UI parameters can be stored and retrieved correctly."""
    logger = logging.getLogger('Phase3Test')
    
    try:
        db_service = DatabaseService()
        
        with db_service.get_session() as session:
            # Create complex hydration UI parameters (simulating real UI state)
            complex_ui_params = {
                'operation_name': 'ComplexHydrationTest',
                'operation_type': 'hydration',
                'source_microstructure': {
                    'name': 'ComplexMicrostructure',
                    'path': './Operations/ComplexMicrostructure'
                },
                'captured_at': '2025-01-07T16:30:00',
                'max_simulation_time_hours': 720.0,  # 30 days
                'target_degree_of_hydration': 0.95,
                'random_seed': 98765,
                'curing_conditions': {
                    'initial_temperature_celsius': 20.0,
                    'thermal_mode': 'temperature_profile',
                    'moisture_mode': 'sealed',
                    'temperature_profile': 'custom_adiabatic'
                },
                'time_calibration': {
                    'time_conversion_factor': 2.5
                },
                'advanced_settings': {
                    'c3a_fraction': 0.12,
                    'ettringite_formation': True,
                    'csh2_formation': False,  # Disabled
                    'ch_formation': True,
                    'ph_computation': True,
                    'random_seed': 98765
                },
                'database_modifications': {
                    'cement_dissolution_rate': 0.8,
                    'c3a_dissolution_bias': 1.5,
                    'nucleation_probability': 0.95
                },
                'temperature_profile': {
                    'name': 'Early Age Adiabatic',
                    'description': 'Custom early age adiabatic temperature rise',
                    'points': [
                        {'time_hours': 0, 'temperature_celsius': 20.0},
                        {'time_hours': 24, 'temperature_celsius': 65.0},
                        {'time_hours': 168, 'temperature_celsius': 50.0},
                        {'time_hours': 720, 'temperature_celsius': 20.0}
                    ]
                }
            }
            
            operation = Operation(
                name='ComplexHydrationTest',
                operation_type=OperationType.HYDRATION.value,
                status=OperationStatus.QUEUED.value,
                stored_ui_parameters=complex_ui_params
            )
            
            session.add(operation)
            session.commit()
            operation_id = operation.id
            
            # Retrieve and verify all parameters
            loaded_op = session.query(Operation).filter_by(id=operation_id).first()
            params = loaded_op.stored_ui_parameters
            
            # Test specific parameter retrieval
            tests = [
                ('operation_name', 'ComplexHydrationTest'),
                ('max_simulation_time_hours', 720.0),
                ('target_degree_of_hydration', 0.95),
                ('random_seed', 98765)
            ]
            
            for param_name, expected_value in tests:
                actual_value = params.get(param_name)
                if actual_value == expected_value:
                    logger.info(f"✓ Parameter {param_name} = {actual_value}")
                else:
                    logger.error(f"✗ Parameter {param_name}: expected {expected_value}, got {actual_value}")
                    session.delete(operation)
                    session.commit()
                    return False
            
            # Test nested parameter structures
            curing_conditions = params.get('curing_conditions', {})
            if curing_conditions.get('thermal_mode') == 'temperature_profile':
                logger.info("✓ Nested curing conditions stored correctly")
            else:
                logger.error(f"✗ Curing conditions incorrect: {curing_conditions}")
                session.delete(operation)
                session.commit()
                return False
            
            # Test temperature profile data
            temp_profile = params.get('temperature_profile', {})
            if temp_profile.get('name') == 'Early Age Adiabatic':
                points = temp_profile.get('points', [])
                if len(points) == 4 and points[1]['temperature_celsius'] == 65.0:
                    logger.info("✓ Complex temperature profile stored correctly")
                else:
                    logger.error(f"✗ Temperature profile points incorrect: {points}")
                    session.delete(operation)
                    session.commit()
                    return False
            else:
                logger.error(f"✗ Temperature profile incorrect: {temp_profile}")
                session.delete(operation)
                session.commit()
                return False
            
            # Clean up
            session.delete(operation)
            session.commit()
            
            return True
            
    except Exception as e:
        logger.error(f"✗ Complex parameter storage test failed: {e}")
        return False

def test_operation_lineage_chain():
    """Test that operation lineage chains work correctly (microstructure -> hydration)."""
    logger = logging.getLogger('Phase3Test')
    
    try:
        db_service = DatabaseService()
        
        with db_service.get_session() as session:
            # Create microstructure operation
            micro_op = Operation(
                name='ChainMicrostructure',
                operation_type=OperationType.MICROSTRUCTURE.value,
                status=OperationStatus.COMPLETED.value,
                stored_ui_parameters={
                    'mix_name': 'ChainMix',
                    'cement_content': 350,
                    'w_c_ratio': 0.45
                }
            )
            session.add(micro_op)
            session.flush()
            
            # Create hydration operation linked to microstructure
            hydration_op = Operation(
                name='ChainHydration',
                operation_type=OperationType.HYDRATION.value,
                status=OperationStatus.QUEUED.value,
                parent_operation_id=micro_op.id,
                stored_ui_parameters={
                    'source_microstructure_name': 'ChainMicrostructure',
                    'max_time': 168,
                    'temperature': 25
                }
            )
            session.add(hydration_op)
            session.commit()
            
            # Test lineage relationships
            loaded_hydration = session.query(Operation).filter_by(name='ChainHydration').first()
            loaded_micro = session.query(Operation).filter_by(name='ChainMicrostructure').first()
            
            # Test parent relationship
            if loaded_hydration.parent_operation_id == loaded_micro.id:
                logger.info("✓ Parent lineage relationship stored correctly")
            else:
                logger.error("✗ Parent lineage relationship failed")
                return False
            
            # Test accessing parent operation
            if loaded_hydration.parent_operation:
                parent_name = loaded_hydration.parent_operation.name
                if parent_name == 'ChainMicrostructure':
                    logger.info("✓ Parent operation accessible through relationship")
                else:
                    logger.error(f"✗ Parent operation name wrong: expected 'ChainMicrostructure', got '{parent_name}'")
                    return False
            else:
                logger.error("✗ Parent operation not accessible")
                return False
            
            # Test parameter inheritance (child can access parent parameters)
            if loaded_hydration.parent_operation.stored_ui_parameters:
                parent_params = loaded_hydration.parent_operation.stored_ui_parameters
                cement_content = parent_params.get('cement_content')
                if cement_content == 350:
                    logger.info("✓ Parameter inheritance from parent working")
                else:
                    logger.error(f"✗ Parameter inheritance failed: expected 350, got {cement_content}")
                    return False
            else:
                logger.error("✗ Cannot access parent parameters")
                return False
            
            # Clean up
            session.delete(hydration_op)
            session.delete(micro_op)
            session.commit()
            
            return True
            
    except Exception as e:
        logger.error(f"✗ Lineage chain test failed: {e}")
        return False

def main():
    """Run Phase 3 comprehensive tests."""
    logger = setup_logging()
    
    logger.info("=" * 60)
    logger.info("Phase 3 Hydration Operations Test")
    logger.info("Testing clean naming, parameter storage, and lineage")
    logger.info("=" * 60)
    
    tests = [
        ("Clean Hydration Operation Creation", test_clean_hydration_operation_creation),
        ("Complex Parameter Storage and Retrieval", test_complex_hydration_parameter_storage),
        ("Operation Lineage Chain", test_operation_lineage_chain)
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n{test_name}...")
        try:
            result = test_func()
            results.append((test_name, result))
            if result:
                logger.info(f"✅ {test_name} PASSED")
            else:
                logger.error(f"❌ {test_name} FAILED")
        except Exception as e:
            logger.error(f"❌ {test_name} ERROR: {e}")
            results.append((test_name, False))
    
    # Summary
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    logger.info("\n" + "=" * 60)
    if passed == total:
        logger.info("🎉 Phase 3 Tests PASSED!")
        logger.info("✓ Clean hydration operation naming working")
        logger.info("✓ UI parameter capture and storage working")
        logger.info("✓ Hydration-to-microstructure lineage working")
        logger.info("✓ Parameter inheritance working")
        logger.info("✓ Complete operation lineage system ready!")
    else:
        logger.error(f"❌ Phase 3 Tests FAILED: {passed}/{total} passed")
        logger.error("Fix issues before proceeding")
    logger.info("=" * 60)
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
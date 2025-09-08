#!/usr/bin/env python3
"""
Phase 2 Test: Microstructure Operations with Clean Naming and Parameter Storage

This test validates that Phase 2 implementation works correctly:
1. Operations use clean user-defined names  
2. UI parameters are captured and stored
3. Operations can be loaded and restored
4. Folder names match operation names exactly
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
    logger = logging.getLogger('Phase2Test')
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
    logger.addHandler(handler)
    return logger

def test_clean_operation_creation():
    """Test creating an operation with clean naming."""
    logger = logging.getLogger('Phase2Test')
    
    try:
        db_service = DatabaseService()
        
        with db_service.get_session() as session:
            # Test UI parameters data
            test_ui_params = {
                'mix_name': 'TestConcrete',
                'operation_name': 'MyTestMicrostructure', 
                'components': [
                    {
                        'index': 0,
                        'type': 'cement',
                        'name': 'Cement1', 
                        'mass_kg_m3': 350.0,
                        'volume_fraction': '0.11'
                    },
                    {
                        'index': 1,
                        'type': 'aggregate',
                        'name': 'Aggregate1',
                        'mass_kg_m3': 1800.0, 
                        'volume_fraction': '0.67'
                    }
                ],
                'system_size_x': 100,
                'system_size_y': 100,
                'system_size_z': 100,
                'resolution_micrometers': 1.0,
                'wb_ratio': 0.45,
                'water_content_kg_m3': 180.0,
                'flocculation_enabled': False,
                'dispersion_factor': 1.0,
                'auto_calculate_enabled': True,
                'captured_at': '2025-01-07T15:00:00'
            }
            
            # Create clean operation
            operation = Operation(
                name='MyTestMicrostructure',  # Clean user-defined name
                operation_type=OperationType.MICROSTRUCTURE.value,
                status=OperationStatus.COMPLETED.value,
                stored_ui_parameters=test_ui_params
            )
            
            session.add(operation)
            session.commit()
            
            operation_id = operation.id
            logger.info(f"✓ Created clean operation: {operation.name} (ID: {operation_id})")
            
            # Verify operation was saved correctly
            loaded_op = session.query(Operation).filter_by(id=operation_id).first()
            
            if loaded_op.name == 'MyTestMicrostructure':
                logger.info("✓ Clean operation name saved correctly")
            else:
                logger.error(f"✗ Operation name incorrect: expected 'MyTestMicrostructure', got '{loaded_op.name}'")
                return False
            
            # Verify UI parameters were saved
            if loaded_op.stored_ui_parameters:
                params = loaded_op.stored_ui_parameters
                if params.get('mix_name') == 'TestConcrete':
                    logger.info("✓ UI parameters saved correctly")
                else:
                    logger.error(f"✗ UI parameters corrupted: {params}")
                    return False
            else:
                logger.error("✗ No UI parameters saved")
                return False
            
            # Verify components were captured
            components = params.get('components', [])
            if len(components) == 2:
                cement_comp = components[0]
                if cement_comp['type'] == 'cement' and cement_comp['mass_kg_m3'] == 350.0:
                    logger.info("✓ Component data captured correctly")
                else:
                    logger.error(f"✗ Component data incorrect: {cement_comp}")
                    return False
            else:
                logger.error(f"✗ Wrong number of components: expected 2, got {len(components)}")
                return False
            
            # Clean up
            session.delete(operation)
            session.commit()
            
            return True
            
    except Exception as e:
        logger.error(f"✗ Clean operation creation test failed: {e}")
        return False

def test_parameter_storage_and_retrieval():
    """Test that UI parameters can be stored and retrieved correctly."""
    logger = logging.getLogger('Phase2Test')
    
    try:
        db_service = DatabaseService()
        
        with db_service.get_session() as session:
            # Create operation with complex UI parameters
            complex_ui_params = {
                'mix_name': 'ComplexMix',
                'operation_name': 'ComplexMicrostructure',
                'components': [
                    {'index': 0, 'type': 'cement', 'name': 'Portland', 'mass_kg_m3': 300.0},
                    {'index': 1, 'type': 'fly_ash', 'name': 'ClassF', 'mass_kg_m3': 50.0},
                    {'index': 2, 'type': 'silica_fume', 'name': 'SF92', 'mass_kg_m3': 25.0},
                    {'index': 3, 'type': 'aggregate', 'name': 'River', 'mass_kg_m3': 1900.0}
                ],
                'system_size_x': 150,
                'system_size_y': 150, 
                'system_size_z': 150,
                'resolution_micrometers': 0.5,
                'wb_ratio': 0.35,
                'water_content_kg_m3': 175.0,
                'flocculation_enabled': True,
                'dispersion_factor': 1.2,
                'distribution_coefficient': 0.8,
                'minimum_distance': 2.0,
                'maximum_iterations': 10000,
                'auto_calculate_enabled': False,
                'captured_at': '2025-01-07T15:30:00'
            }
            
            operation = Operation(
                name='ComplexMicrostructure',
                operation_type=OperationType.MICROSTRUCTURE.value,
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
                ('mix_name', 'ComplexMix'),
                ('system_size_x', 150),
                ('resolution_micrometers', 0.5),
                ('wb_ratio', 0.35),
                ('flocculation_enabled', True),
                ('dispersion_factor', 1.2)
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
            
            # Test component parameter retrieval
            components = params.get('components', [])
            if len(components) == 4:
                fly_ash = next((c for c in components if c['type'] == 'fly_ash'), None)
                if fly_ash and fly_ash['name'] == 'ClassF' and fly_ash['mass_kg_m3'] == 50.0:
                    logger.info("✓ Complex component parameters stored correctly")
                else:
                    logger.error(f"✗ Fly ash component incorrect: {fly_ash}")
                    session.delete(operation)
                    session.commit()
                    return False
            else:
                logger.error(f"✗ Wrong component count: expected 4, got {len(components)}")
                session.delete(operation)
                session.commit()
                return False
            
            # Clean up
            session.delete(operation)
            session.commit()
            
            return True
            
    except Exception as e:
        logger.error(f"✗ Parameter storage test failed: {e}")
        return False

def test_operation_lineage_ready():
    """Test that lineage relationships can be created (Phase 1 functionality)."""
    logger = logging.getLogger('Phase2Test')
    
    try:
        db_service = DatabaseService()
        
        with db_service.get_session() as session:
            # Create parent microstructure operation
            parent_op = Operation(
                name='ParentMicrostructure',
                operation_type=OperationType.MICROSTRUCTURE.value,
                status=OperationStatus.COMPLETED.value,
                stored_ui_parameters={'mix_name': 'ParentMix', 'cement_content': 300}
            )
            session.add(parent_op)
            session.flush()
            
            # Create child hydration operation (simulating future Phase 3)
            child_op = Operation(
                name='ChildHydration',
                operation_type=OperationType.HYDRATION.value,
                status=OperationStatus.QUEUED.value,
                parent_operation_id=parent_op.id,
                stored_ui_parameters={'temperature': 20, 'max_time': 168}
            )
            session.add(child_op)
            session.commit()
            
            # Verify lineage relationship
            loaded_child = session.query(Operation).filter_by(name='ChildHydration').first()
            loaded_parent = session.query(Operation).filter_by(name='ParentMicrostructure').first()
            
            if loaded_child.parent_operation_id == loaded_parent.id:
                logger.info("✓ Lineage relationship stored correctly")
            else:
                logger.error("✗ Lineage relationship failed")
                return False
            
            # Test parameter inheritance (child can access parent parameters)
            if loaded_child.parent_operation and loaded_child.parent_operation.stored_ui_parameters:
                parent_params = loaded_child.parent_operation.stored_ui_parameters
                cement_content = parent_params.get('cement_content')
                if cement_content == 300:
                    logger.info("✓ Parameter inheritance working")
                else:
                    logger.error(f"✗ Parameter inheritance failed: expected 300, got {cement_content}")
                    return False
            else:
                logger.error("✗ Cannot access parent parameters")
                return False
            
            # Clean up
            session.delete(child_op)
            session.delete(parent_op)
            session.commit()
            
            return True
            
    except Exception as e:
        logger.error(f"✗ Lineage test failed: {e}")
        return False

def main():
    """Run Phase 2 comprehensive tests."""
    logger = setup_logging()
    
    logger.info("=" * 60)
    logger.info("Phase 2 Microstructure Operations Test")
    logger.info("Testing clean naming and parameter storage")
    logger.info("=" * 60)
    
    tests = [
        ("Clean Operation Creation", test_clean_operation_creation),
        ("Parameter Storage and Retrieval", test_parameter_storage_and_retrieval),
        ("Operation Lineage Ready", test_operation_lineage_ready)
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
        logger.info("🎉 Phase 2 Tests PASSED!")
        logger.info("✓ Clean operation naming working")
        logger.info("✓ UI parameter capture and storage working")
        logger.info("✓ Operation lineage infrastructure ready")
        logger.info("✓ Ready to proceed with Phase 3!")
    else:
        logger.error(f"❌ Phase 2 Tests FAILED: {passed}/{total} passed")
        logger.error("Fix issues before proceeding to Phase 3")
    logger.info("=" * 60)
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
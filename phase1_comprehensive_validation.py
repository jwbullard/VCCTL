#!/usr/bin/env python3
"""
Comprehensive Phase 1 Validation Script

Tests all aspects of the Phase 1 implementation:
1. Database schema changes
2. SQLAlchemy model functionality
3. Lineage relationship functionality
4. UI parameter storage and retrieval
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
    from app.models.hydration_operation import HydrationOperation
    from sqlalchemy.orm import sessionmaker
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)

def setup_logging():
    """Setup logging for validation."""
    logger = logging.getLogger('Phase1Validation')
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
    logger.addHandler(handler)
    return logger

def test_database_connectivity():
    """Test basic database connectivity."""
    logger = logging.getLogger('Phase1Validation')
    
    try:
        db_service = DatabaseService()
        db_service.initialize_database()
        logger.info("✓ Database connectivity successful")
        return db_service
    except Exception as e:
        logger.error(f"✗ Database connectivity failed: {e}")
        return None

def test_operation_model_enhancements(db_service):
    """Test the enhanced Operation model with new fields."""
    logger = logging.getLogger('Phase1Validation')
    
    try:
        with db_service.get_session() as session:
            # Test 1: Create operation with lineage
            test_ui_params = {
                "mix_name": "TestMix",
                "cement_content": 350,
                "water_cement_ratio": 0.45,
                "aggregate_type": "normal",
                "timestamp": "2025-01-07T12:00:00"
            }
            
            parent_op = Operation(
                name="TestParent",
                operation_type=OperationType.MICROSTRUCTURE.value,
                status=OperationStatus.COMPLETED.value,
                stored_ui_parameters=test_ui_params
            )
            session.add(parent_op)
            session.flush()  # Get ID without committing
            
            child_op = Operation(
                name="TestChild",
                operation_type=OperationType.HYDRATION.value,
                status=OperationStatus.QUEUED.value,
                parent_operation_id=parent_op.id,
                stored_ui_parameters={"hydration_time": 168, "temperature": 25}
            )
            session.add(child_op)
            session.commit()
            
            logger.info(f"✓ Created operations - Parent ID: {parent_op.id}, Child ID: {child_op.id}")
            
            # Test 2: Verify relationships
            loaded_child = session.query(Operation).filter_by(name="TestChild").first()
            loaded_parent = session.query(Operation).filter_by(name="TestParent").first()
            
            if loaded_child.parent_operation_id == loaded_parent.id:
                logger.info("✓ Parent-child relationship stored correctly")
            else:
                logger.error("✗ Parent-child relationship failed")
                return False
            
            if loaded_child.parent_operation:
                logger.info(f"✓ Parent relationship accessible: {loaded_child.parent_operation.name}")
            else:
                logger.error("✗ Parent relationship not accessible")
                return False
            
            if loaded_parent.child_operations and len(loaded_parent.child_operations) > 0:
                logger.info(f"✓ Child relationships accessible: {[c.name for c in loaded_parent.child_operations]}")
            else:
                logger.error("✗ Child relationships not accessible")
                return False
            
            # Test 3: Verify UI parameters
            if loaded_parent.stored_ui_parameters:
                params = loaded_parent.stored_ui_parameters
                if params.get("mix_name") == "TestMix":
                    logger.info("✓ UI parameters stored and retrieved correctly")
                else:
                    logger.error(f"✗ UI parameters corrupted: {params}")
                    return False
            else:
                logger.error("✗ UI parameters not stored")
                return False
            
            # Test 4: JSON functionality
            if isinstance(loaded_parent.stored_ui_parameters, dict):
                logger.info("✓ JSON fields properly deserialized")
            else:
                logger.error(f"✗ JSON fields not deserialized: {type(loaded_parent.stored_ui_parameters)}")
                return False
            
            # Clean up
            session.delete(child_op)
            session.delete(parent_op)
            session.commit()
            logger.info("✓ Test cleanup completed")
            
            return True
            
    except Exception as e:
        logger.error(f"✗ Operation model test failed: {e}")
        return False

def test_hydration_lineage(db_service):
    """Test HydrationOperation lineage to microstructure operations."""
    logger = logging.getLogger('Phase1Validation')
    
    try:
        with db_service.get_session() as session:
            # Create a microstructure operation
            microstructure_op = Operation(
                name="TestMicrostructure",
                operation_type=OperationType.MICROSTRUCTURE.value,
                status=OperationStatus.COMPLETED.value,
                stored_ui_parameters={
                    "cement_type": "Portland",
                    "w_c_ratio": 0.4,
                    "aggregate_content": 60
                }
            )
            session.add(microstructure_op)
            session.flush()
            
            # Create a hydration operation
            hydration_op = Operation(
                name="TestHydration",
                operation_type=OperationType.HYDRATION.value,
                status=OperationStatus.QUEUED.value,
                parent_operation_id=microstructure_op.id,
                stored_ui_parameters={
                    "max_time": 168,
                    "temperature": 20,
                    "aging_mode": "normal"
                }
            )
            session.add(hydration_op)
            session.flush()
            
            # Note: We can't fully test HydrationOperation without all its required fields
            # But we can test the lineage concept
            
            logger.info(f"✓ Hydration operation linked to microstructure: {hydration_op.parent_operation_id}")
            
            # Test parameter access from parent
            if hydration_op.parent_operation and hydration_op.parent_operation.stored_ui_parameters:
                parent_params = hydration_op.parent_operation.stored_ui_parameters
                cement_type = parent_params.get("cement_type")
                w_c_ratio = parent_params.get("w_c_ratio")
                
                logger.info(f"✓ Can access parent microstructure parameters: cement={cement_type}, w/c={w_c_ratio}")
            else:
                logger.error("✗ Cannot access parent microstructure parameters")
                return False
            
            # Clean up
            session.delete(hydration_op)
            session.delete(microstructure_op)
            session.commit()
            
            return True
            
    except Exception as e:
        logger.error(f"✗ Hydration lineage test failed: {e}")
        return False

def test_existing_operations_compatibility(db_service):
    """Test that existing operations are still accessible."""
    logger = logging.getLogger('Phase1Validation')
    
    try:
        with db_service.get_session() as session:
            # Get existing operations
            existing_ops = session.query(Operation).all()
            
            if len(existing_ops) > 0:
                logger.info(f"✓ Found {len(existing_ops)} existing operations")
                
                # Check that they have new fields (should be NULL)
                first_op = existing_ops[0]
                logger.info(f"✓ Existing operation compatibility - Name: {first_op.name}, "
                          f"Parent: {first_op.parent_operation_id}, UI Params: {first_op.stored_ui_parameters}")
                
                # Test updating an existing operation
                original_params = first_op.stored_ui_parameters
                test_params = {"retrofitted": True, "original_name": first_op.name}
                first_op.stored_ui_parameters = test_params
                session.commit()
                
                # Verify update
                session.refresh(first_op)
                if first_op.stored_ui_parameters.get("retrofitted"):
                    logger.info("✓ Existing operations can be updated with new fields")
                    
                    # Restore original
                    first_op.stored_ui_parameters = original_params
                    session.commit()
                else:
                    logger.error("✗ Cannot update existing operations with new fields")
                    return False
            else:
                logger.warning("No existing operations found for compatibility testing")
            
            return True
            
    except Exception as e:
        logger.error(f"✗ Existing operations compatibility test failed: {e}")
        return False

def main():
    """Run comprehensive Phase 1 validation."""
    logger = setup_logging()
    
    logger.info("=" * 60)
    logger.info("Phase 1 Comprehensive Validation")
    logger.info("Testing lineage tracking and UI parameter storage")
    logger.info("=" * 60)
    
    # Test 1: Database connectivity
    logger.info("\n1. Testing database connectivity...")
    db_service = test_database_connectivity()
    if not db_service:
        logger.error("Cannot proceed without database connectivity")
        return False
    
    # Test 2: Operation model enhancements
    logger.info("\n2. Testing Operation model enhancements...")
    if not test_operation_model_enhancements(db_service):
        return False
    
    # Test 3: Hydration lineage
    logger.info("\n3. Testing hydration operation lineage...")
    if not test_hydration_lineage(db_service):
        return False
    
    # Test 4: Existing operations compatibility
    logger.info("\n4. Testing existing operations compatibility...")
    if not test_existing_operations_compatibility(db_service):
        return False
    
    logger.info("\n" + "=" * 60)
    logger.info("🎉 Phase 1 validation PASSED!")
    logger.info("✓ Database schema enhanced successfully")
    logger.info("✓ Operation lineage tracking functional")
    logger.info("✓ UI parameter storage working")
    logger.info("✓ Existing operations remain compatible")
    logger.info("Ready to proceed with Phase 2!")
    logger.info("=" * 60)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
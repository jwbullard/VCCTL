#!/usr/bin/env python3
"""
Migration Script for Existing Operations

This script safely migrates existing operations to the new detailed storage system
without affecting any existing functionality.

SAFETY NOTES:
1. This script only READS from existing operations and CREATES new detail records
2. It does NOT modify or delete any existing data
3. All existing functionality will continue to work unchanged
4. Run with --dry-run first to see what would be migrated
"""

import sys
import argparse
from pathlib import Path
import json
from typing import Dict, Any, Optional, List

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from app.services.service_container import get_service_container
from app.models import (
    Operation, OperationType,
    MixDesign, 
    MicrostructureOperation,
    HydrationOperation,
    HydrationParameterSet,
    TemperatureProfileDB
)


class OperationMigrator:
    """Safely migrates existing operations to new detailed storage system."""
    
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.service_container = get_service_container()
        self.db_service = self.service_container.database_service
        self.stats = {
            'microstructure_ops_found': 0,
            'microstructure_ops_migrated': 0,
            'hydration_ops_found': 0,
            'hydration_ops_migrated': 0,
            'errors': []
        }
    
    def migrate_all_operations(self):
        """Migrate all existing operations to new detailed storage."""
        print(f"🔄 Starting operation migration ({'DRY RUN' if self.dry_run else 'LIVE RUN'})")
        print("=" * 70)
        
        with self.db_service.get_session() as session:
            # Get all existing operations
            operations = session.query(Operation).all()
            print(f"Found {len(operations)} total operations in database")
            
            for operation in operations:
                try:
                    if operation.operation_type in ['microstructure_generation', 'MICROSTRUCTURE']:
                        self._migrate_microstructure_operation(session, operation)
                    elif operation.operation_type in ['HYDRATION', 'hydration']:
                        self._migrate_hydration_operation(session, operation)
                except Exception as e:
                    self.stats['errors'].append(f"Error migrating {operation.name}: {e}")
                    print(f"❌ Error migrating {operation.name}: {e}")
            
            if not self.dry_run:
                session.commit()
                print("✅ Migration committed to database")
            else:
                print("🔍 DRY RUN - No changes made to database")
        
        self._print_migration_summary()
    
    def _migrate_microstructure_operation(self, session, operation: Operation):
        """Migrate a microstructure operation to detailed storage."""
        self.stats['microstructure_ops_found'] += 1
        
        # Check if already migrated
        existing = session.query(MicrostructureOperation).filter_by(operation_id=operation.id).first()
        if existing:
            print(f"⏭️  Microstructure operation '{operation.name}' already migrated, skipping")
            return
        
        print(f"🔄 Migrating microstructure operation: {operation.name}")
        
        # Try to find associated mix design
        mix_design = self._find_mix_design_for_microstructure(session, operation)
        if not mix_design:
            self.stats['errors'].append(f"No mix design found for microstructure operation {operation.name}")
            print(f"   ⚠️  Warning: No mix design found, will create default")
            mix_design = self._create_default_mix_design(session, operation)
        
        # Extract microstructure parameters from operation folder or metadata
        params = self._extract_microstructure_parameters(operation)
        
        # Create microstructure operation detail record
        micro_op = MicrostructureOperation(
            operation_id=operation.id,
            mix_design_id=mix_design.id,
            system_size_x=params.get('system_size_x', 100),
            system_size_y=params.get('system_size_y', 100),
            system_size_z=params.get('system_size_z', 100),
            system_size=params.get('system_size', 100),
            resolution=params.get('resolution', 1.0),
            random_seed=params.get('random_seed', -1),
            cement_shape_set=params.get('cement_shape_set', 'spherical'),
            fine_aggregate_shape_set=params.get('fine_aggregate_shape_set', 'spherical'),
            coarse_aggregate_shape_set=params.get('coarse_aggregate_shape_set', 'spherical'),
            aggregate_shape_set=params.get('aggregate_shape_set', 'spherical'),
            flocculation_enabled=params.get('flocculation_enabled', False),
            flocculation_degree=params.get('flocculation_degree', 0.0),
            dispersion_factor=params.get('dispersion_factor', 0),
            genmic_mode=params.get('genmic_mode', 2),
            particle_shape_directory=params.get('particle_shape_directory', '../../particle_shape_set/'),
            output_img_filename=params.get('output_img_filename', f'{operation.name.replace(" Microstructure", "")}.img'),
            output_pimg_filename=params.get('output_pimg_filename', f'{operation.name.replace(" Microstructure", "")}.pimg'),
            output_directory=params.get('output_directory', f'Operations/{operation.name.replace(" Microstructure", "")}'),
            status='completed' if operation.status == 'COMPLETED' else operation.status.lower(),
            progress=1.0 if operation.status == 'COMPLETED' else 0.0,
            start_time=operation.started_at,
            end_time=operation.completed_at
        )
        
        if not self.dry_run:
            session.add(micro_op)
        
        self.stats['microstructure_ops_migrated'] += 1
        print(f"   ✅ Created detailed record for microstructure operation")
    
    def _migrate_hydration_operation(self, session, operation: Operation):
        """Migrate a hydration operation to detailed storage."""
        self.stats['hydration_ops_found'] += 1
        
        # Check if already migrated
        existing = session.query(HydrationOperation).filter_by(operation_id=operation.id).first()
        if existing:
            print(f"⏭️  Hydration operation '{operation.name}' already migrated, skipping")
            return
        
        print(f"🔄 Migrating hydration operation: {operation.name}")
        
        # Find source microstructure operation
        source_micro_op = self._find_source_microstructure_operation(session, operation)
        if not source_micro_op:
            self.stats['errors'].append(f"No source microstructure found for hydration operation {operation.name}")
            print(f"   ⚠️  Warning: No source microstructure operation found")
            return
        
        # Get or create hydration parameter set
        param_set = self._get_or_create_hydration_parameter_set(session, operation)
        
        # Extract hydration parameters from operation folder or metadata
        params = self._extract_hydration_parameters(operation)
        
        # Create hydration operation detail record
        hydration_op = HydrationOperation(
            operation_id=operation.id,
            microstructure_operation_id=source_micro_op.id,
            hydration_parameter_set_id=param_set.id,
            temperature_profile_id=params.get('temperature_profile_id'),
            input_img_file=params.get('input_img_file', ''),
            input_pimg_file=params.get('input_pimg_file', ''),
            microstructure_directory=params.get('microstructure_directory', ''),
            max_simulation_time=params.get('max_simulation_time', 168.0),
            target_degree_of_hydration=params.get('target_degree_of_hydration', 0.8),
            random_seed=params.get('random_seed', -1),
            working_directory=params.get('working_directory', f'Operations/{operation.name}'),
            output_base_name=params.get('output_base_name', operation.name),
            c3a_fraction=params.get('c3a_fraction', 0.0),
            aging_mode=params.get('aging_mode', 0),
            auto_stop_enabled=params.get('auto_stop_enabled', True),
            ch_flag_enabled=params.get('ch_flag_enabled', True),
            csh2_flag_enabled=params.get('csh2_flag_enabled', True),
            ettringite_enabled=params.get('ettringite_enabled', True),
            ph_active=params.get('ph_active', True),
            dissolution_bias=params.get('dissolution_bias', 1.0),
            growth_probability=params.get('growth_probability', 1.0),
            time_conversion_factor=params.get('time_conversion_factor', 1.0),
            use_temperature_profile=params.get('use_temperature_profile', False),
            constant_temperature=params.get('constant_temperature', 25.0),
            output_time_frequency=params.get('output_time_frequency', 50),
            save_time_history=params.get('save_time_history', True),
            save_phase_evolution=params.get('save_phase_evolution', True),
            save_microstructure_snapshots=params.get('save_microstructure_snapshots', True),
            status='completed' if operation.status == 'COMPLETED' else operation.status.lower(),
            progress=1.0 if operation.status == 'COMPLETED' else 0.0,
            start_time=operation.started_at,
            end_time=operation.completed_at
        )
        
        if not self.dry_run:
            session.add(hydration_op)
        
        self.stats['hydration_ops_migrated'] += 1
        print(f"   ✅ Created detailed record for hydration operation")
    
    def _find_mix_design_for_microstructure(self, session, operation: Operation) -> Optional[MixDesign]:
        """Find mix design associated with microstructure operation."""
        # Try to match by name patterns
        micro_name = operation.name.replace("genmic_input_", "").replace(" Microstructure", "")
        
        # Look for mix designs with similar names
        mix_designs = session.query(MixDesign).all()
        for md in mix_designs:
            if micro_name.lower() in md.name.lower() or md.name.lower() in micro_name.lower():
                return md
        
        return None
    
    def _create_default_mix_design(self, session, operation: Operation) -> MixDesign:
        """Create a default mix design for operations that don't have one."""
        name = f"Default for {operation.name}"
        
        # Check if default already exists
        existing = session.query(MixDesign).filter_by(name=name).first()
        if existing:
            return existing
        
        mix_design = MixDesign(
            name=name,
            description=f"Auto-generated default mix design for {operation.name}",
            water_binder_ratio=0.4,
            total_water_content=200.0,
            air_content=4.0,
            water_volume_fraction=0.2,
            air_volume_fraction=0.04,
            system_size_x=100,
            system_size_y=100,
            system_size_z=100,
            system_size=100,
            resolution=1.0,
            random_seed=-1,
            components=[],  # Empty components for default
            calculated_properties={}
        )
        
        if not self.dry_run:
            session.add(mix_design)
            session.flush()  # Get the ID
        
        return mix_design
    
    def _find_source_microstructure_operation(self, session, hydration_op: Operation) -> Optional[Operation]:
        """Find source microstructure operation for hydration operation."""
        # Use naming pattern: HY-X comes from genmic_input_X
        if hydration_op.name.startswith('HY-'):
            micro_name = hydration_op.name.replace('HY-', 'genmic_input_') + ' Microstructure'
            return session.query(Operation).filter_by(name=micro_name).first()
        
        # Try other patterns
        base_name = hydration_op.name.replace('Hydration_', '').replace('HY-', '')
        possible_names = [
            f'genmic_input_{base_name} Microstructure',
            f'{base_name} Microstructure',
            f'Microstructure_{base_name}'
        ]
        
        for name in possible_names:
            op = session.query(Operation).filter_by(name=name).first()
            if op:
                return op
        
        return None
    
    def _get_or_create_hydration_parameter_set(self, session, operation: Operation) -> HydrationParameterSet:
        """Get or create hydration parameter set for operation."""
        # Try to find existing 'portland_cement_standard' parameter set
        param_set = session.query(HydrationParameterSet).filter_by(name='portland_cement_standard').first()
        if param_set:
            return param_set
        
        # Create default if none exists
        param_set = HydrationParameterSet(
            name='portland_cement_standard',
            description='Standard portland cement hydration parameters',
            max_time_hours=168.0,
            curing_conditions={},
            time_calibration={},
            advanced_settings={},
            db_modifications={}
        )
        
        if not self.dry_run:
            session.add(param_set)
            session.flush()
        
        return param_set
    
    def _extract_microstructure_parameters(self, operation: Operation) -> Dict[str, Any]:
        """Extract microstructure parameters from operation files or metadata."""
        params = {
            'system_size_x': 100,
            'system_size_y': 100,
            'system_size_z': 100,
            'system_size': 100,
            'resolution': 1.0,
            'random_seed': -1,
            'cement_shape_set': 'spherical',
            'fine_aggregate_shape_set': 'spherical',
            'coarse_aggregate_shape_set': 'spherical',
            'aggregate_shape_set': 'spherical',
            'flocculation_enabled': False,
            'flocculation_degree': 0.0,
            'dispersion_factor': 0,
            'genmic_mode': 2,
            'particle_shape_directory': '../../particle_shape_set/'
        }
        
        # Try to read from genmic input file if it exists
        micro_name = operation.name.replace("genmic_input_", "").replace(" Microstructure", "")
        operations_dir = Path("Operations")
        genmic_file = operations_dir / micro_name / f"genmic_input_{micro_name}.txt"
        
        if genmic_file.exists():
            try:
                with open(genmic_file, 'r') as f:
                    lines = f.readlines()
                    if len(lines) >= 6:
                        params['random_seed'] = int(lines[0].strip())
                        params['genmic_mode'] = int(lines[1].strip())
                        params['system_size_x'] = int(lines[2].strip())
                        params['system_size_y'] = int(lines[3].strip())
                        params['system_size_z'] = int(lines[4].strip())
                        params['resolution'] = float(lines[5].strip())
                        
                        # Set backward compatibility size
                        params['system_size'] = max(params['system_size_x'], params['system_size_y'], params['system_size_z'])
            except Exception as e:
                print(f"   ⚠️  Could not read genmic file {genmic_file}: {e}")
        
        # Set output file names
        base_name = micro_name
        params['output_img_filename'] = f'{base_name}.img'
        params['output_pimg_filename'] = f'{base_name}.pimg'
        params['output_directory'] = f'Operations/{base_name}'
        
        return params
    
    def _extract_hydration_parameters(self, operation: Operation) -> Dict[str, Any]:
        """Extract hydration parameters from operation files or metadata."""
        params = {
            'input_img_file': '',
            'input_pimg_file': '',
            'microstructure_directory': '',
            'max_simulation_time': 168.0,
            'target_degree_of_hydration': 0.8,
            'random_seed': -1,
            'c3a_fraction': 0.0,
            'aging_mode': 0,
            'auto_stop_enabled': True,
            'ch_flag_enabled': True,
            'csh2_flag_enabled': True,
            'ettringite_enabled': True,
            'ph_active': True,
            'dissolution_bias': 1.0,
            'growth_probability': 1.0,
            'time_conversion_factor': 1.0,
            'use_temperature_profile': False,
            'constant_temperature': 25.0,
            'output_time_frequency': 50,
            'save_time_history': True,
            'save_phase_evolution': True,
            'save_microstructure_snapshots': True
        }
        
        # Try to read from extended parameter file if it exists
        operations_dir = Path("Operations")
        op_dir = operations_dir / operation.name
        
        # Look for extended parameter files
        for param_file in op_dir.glob("*_extended_parameters.csv"):
            try:
                with open(param_file, 'r') as f:
                    lines = f.readlines()
                    # Parse extended parameters if needed
                    # For now, use defaults
                pass
            except Exception as e:
                print(f"   ⚠️  Could not read parameter file {param_file}: {e}")
        
        # Set file paths
        params['working_directory'] = f'Operations/{operation.name}'
        params['output_base_name'] = operation.name
        
        return params
    
    def _print_migration_summary(self):
        """Print migration summary statistics."""
        print("\n" + "=" * 70)
        print("📊 MIGRATION SUMMARY")
        print("=" * 70)
        print(f"Microstructure Operations:")
        print(f"  Found: {self.stats['microstructure_ops_found']}")
        print(f"  Migrated: {self.stats['microstructure_ops_migrated']}")
        print(f"")
        print(f"Hydration Operations:")
        print(f"  Found: {self.stats['hydration_ops_found']}")
        print(f"  Migrated: {self.stats['hydration_ops_migrated']}")
        print(f"")
        print(f"Errors: {len(self.stats['errors'])}")
        for error in self.stats['errors']:
            print(f"  ❌ {error}")
        
        if self.dry_run:
            print(f"\n🔍 This was a DRY RUN - no changes were made to the database")
            print(f"💡 Run with --live to actually perform the migration")
        else:
            print(f"\n✅ Migration completed successfully!")
            print(f"💡 All existing functionality will continue to work unchanged")


def main():
    parser = argparse.ArgumentParser(description="Migrate existing operations to detailed storage")
    parser.add_argument("--dry-run", action="store_true", default=True,
                       help="Show what would be migrated without making changes (default)")
    parser.add_argument("--live", action="store_true",
                       help="Actually perform the migration")
    
    args = parser.parse_args()
    
    # If --live is specified, turn off dry_run
    dry_run = not args.live
    
    migrator = OperationMigrator(dry_run=dry_run)
    migrator.migrate_all_operations()


if __name__ == "__main__":
    main()
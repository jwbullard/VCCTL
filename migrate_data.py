#!/usr/bin/env python3
"""
VCCTL Data Migration Script

Migrates data from the original H2 database to SQLite.
Supports both Flyway script migration and direct H2 database migration.
"""

import sys
import argparse
import logging
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from app.database.service import database_service
from app.database.migrations import create_migration_manager


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
        ]
    )


def migrate_from_flyway(flyway_dir: Path, verbose: bool = False):
    """Migrate data from Flyway scripts."""
    setup_logging(verbose)
    logger = logging.getLogger('VCCTL.Migration.CLI')
    
    try:
        logger.info("Starting Flyway migration process")
        
        # Initialize database service
        logger.info("Initializing database service")
        db_service = database_service
        db_service.initialize_database()
        
        # Create migration manager
        migration_manager = create_migration_manager(db_service)
        
        # Check database status
        version_info = migration_manager.check_database_version()
        logger.info(f"Database status: {version_info}")
        
        # Create initial schema if needed
        if not version_info['initialized']:
            logger.info("Creating initial database schema")
            migration_manager.create_initial_schema()
        
        # Run Flyway migration
        logger.info(f"Migrating data from Flyway scripts in: {flyway_dir}")
        migration_manager.migrate_from_flyway_scripts(flyway_dir)
        
        # Validate migration
        logger.info("Validating migrated data")
        validation_results = migration_manager.validate_migration()
        
        logger.info("Migration validation results:")
        logger.info(f"Status: {validation_results['status']}")
        logger.info(f"Table counts: {validation_results['table_counts']}")
        
        if validation_results['errors']:
            logger.error("Validation errors:")
            for error in validation_results['errors']:
                logger.error(f"  - {error}")
        
        if validation_results['warnings']:
            logger.warning("Validation warnings:")
            for warning in validation_results['warnings']:
                logger.warning(f"  - {warning}")
        
        if validation_results['status'] == 'success':
            logger.info("✅ Migration completed successfully!")
        elif validation_results['status'] == 'warning':
            logger.warning("⚠️ Migration completed with warnings")
        else:
            logger.error("❌ Migration completed with errors")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False


def create_seed_data(verbose: bool = False):
    """Create seed data for fresh installations."""
    setup_logging(verbose)
    logger = logging.getLogger('VCCTL.Migration.CLI')
    
    try:
        logger.info("Creating seed data")
        
        # Initialize database service
        db_service = database_service
        db_service.initialize_database()
        
        # Create migration manager
        migration_manager = create_migration_manager(db_service)
        
        # Create initial schema if needed
        version_info = migration_manager.check_database_version()
        if not version_info['initialized']:
            logger.info("Creating initial database schema")
            migration_manager.create_initial_schema()
        
        # Create seed data
        migration_manager.seed_initial_data()
        
        logger.info("✅ Seed data created successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Seed data creation failed: {e}")
        return False


def check_migration_status(verbose: bool = False):
    """Check the current migration status."""
    setup_logging(verbose)
    logger = logging.getLogger('VCCTL.Migration.CLI')
    
    try:
        # Initialize database service
        db_service = database_service
        
        # Create migration manager
        migration_manager = create_migration_manager(db_service)
        
        # Check database status
        version_info = migration_manager.check_database_version()
        
        print("🔍 Database Migration Status")
        print("=" * 40)
        print(f"Initialized: {version_info['initialized']}")
        print(f"Schema exists: {version_info['schema_exists']}")
        print(f"Current version: {version_info['current_version']}")
        print(f"Applied migrations: {len(version_info['applied_migrations'])}")
        
        if version_info['applied_migrations']:
            print("\nApplied migrations:")
            for migration in version_info['applied_migrations']:
                print(f"  - {migration}")
        
        # Check table counts if database is initialized
        if version_info['initialized']:
            print("\n📊 Table Information")
            print("-" * 20)
            
            try:
                health_info = db_service.health_check()
                print(f"Database size: {health_info.get('database_size', 0)} bytes")
                print(f"Tables count: {health_info.get('tables_count', 0)}")
                
                # Get detailed table info
                table_info = db_service.get_table_info()
                for table in table_info:
                    print(f"  {table['name']}: {table['row_count']} rows")
                    
            except Exception as e:
                logger.warning(f"Could not get table information: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to check migration status: {e}")
        return False


def reset_database(verbose: bool = False, confirm: bool = False):
    """Reset the database (WARNING: destructive operation)."""
    setup_logging(verbose)
    logger = logging.getLogger('VCCTL.Migration.CLI')
    
    if not confirm:
        response = input("⚠️  WARNING: This will delete ALL data! Are you sure? (type 'yes' to confirm): ")
        if response.lower() != 'yes':
            logger.info("Reset cancelled")
            return True
    
    try:
        logger.warning("Resetting database - all data will be lost!")
        
        # Initialize database service
        db_service = database_service
        
        # Create migration manager
        migration_manager = create_migration_manager(db_service)
        
        # Reset database
        migration_manager.reset_database()
        
        logger.info("✅ Database reset completed!")
        return True
        
    except Exception as e:
        logger.error(f"Database reset failed: {e}")
        return False


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="VCCTL Data Migration Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python migrate_data.py status                    # Check migration status
  python migrate_data.py flyway /path/to/scripts   # Migrate from Flyway scripts
  python migrate_data.py seed                      # Create seed data
  python migrate_data.py reset                     # Reset database (dangerous!)
        """
    )
    
    parser.add_argument(
        'command',
        choices=['status', 'flyway', 'seed', 'reset'],
        help='Migration command to execute'
    )
    
    parser.add_argument(
        'path',
        nargs='?',
        help='Path to Flyway scripts directory (for flyway command)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--yes',
        action='store_true',
        help='Confirm destructive operations without prompting'
    )
    
    args = parser.parse_args()
    
    # Execute command
    success = False
    
    if args.command == 'status':
        success = check_migration_status(args.verbose)
    
    elif args.command == 'flyway':
        if not args.path:
            print("❌ Error: Flyway command requires a path to the scripts directory")
            print("Example: python migrate_data.py flyway ../vcctl-backend/src/main/resources/db/migration/")
            return 1
        
        flyway_dir = Path(args.path)
        if not flyway_dir.exists():
            print(f"❌ Error: Flyway scripts directory not found: {flyway_dir}")
            return 1
        
        success = migrate_from_flyway(flyway_dir, args.verbose)
    
    elif args.command == 'seed':
        success = create_seed_data(args.verbose)
    
    elif args.command == 'reset':
        success = reset_database(args.verbose, args.yes)
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
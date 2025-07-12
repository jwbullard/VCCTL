# VCCTL Data Migration Guide

This guide explains how to migrate data from the original H2 database to SQLite for the VCCTL GTK3 application.

## Overview

The migration process converts the original VCCTL Spring Boot + H2 database to a SQLite database suitable for the GTK3 desktop application. It preserves all material data, binary content, and relationships.

## Prerequisites

1. **Install Dependencies**:
   ```bash
   # Check current requirements
   python check_requirements.py
   
   # Install missing packages
   pip install -r requirements.txt
   ```

2. **Source Data**: Access to the original Flyway migration scripts from the Spring Boot application:
   ```
   vcctl-backend/src/main/resources/db/migration/
   ```

## Migration Methods

### Method 1: Flyway Scripts Migration (Recommended)

This method processes the original Flyway SQL scripts and converts them to SQLite format.

```bash
# Check current database status
python migrate_data.py status

# Migrate data from Flyway scripts
python migrate_data.py flyway ../vcctl-backend/src/main/resources/db/migration/

# Verify migration
python migrate_data.py status
```

### Method 2: Seed Data Only

For fresh installations without existing data:

```bash
# Create basic seed data
python migrate_data.py seed

# Check results
python migrate_data.py status
```

## Migration Process Details

### 1. Schema Creation
- Creates all SQLAlchemy tables
- Sets up indexes and constraints
- Initializes migration tracking

### 2. Data Conversion
The migration handles:
- **Binary Data**: Preserves hexadecimal-encoded BLOB data
- **Large Files**: Processes 20MB+ files in chunks
- **Material Data**: Converts all cement, fly ash, slag, aggregate data
- **File References**: Maintains PSD and alkali file references
- **Sieve Data**: Preserves aggregate grading information

### 3. Data Validation
Post-migration validation checks:
- Table row counts
- Data integrity constraints
- Material property validation
- Binary data preservation

## Migrated Data Structure

### Core Materials
- **Cement**: 168+ cement types with composition data
- **Fly Ash**: Class F and Class C fly ash materials
- **Slag**: Ground granulated blast-furnace slag types
- **Aggregates**: Coarse and fine aggregate specifications
- **Inert Fillers**: Quartz, limestone, and other fillers

### Supporting Data
- **Particle Size Distributions (PSDs)**: Reference curves
- **Alkali Characteristics**: Chemical composition files
- **Sieve Specifications**: Standard ASTM sieve sizes
- **Grading Curves**: Aggregate gradation data
- **Shape Sets**: Particle shape definitions

### Binary Content
- **Images**: GIF format aggregate and cement images
- **Analysis Data**: X-ray diffraction, chemical analysis
- **Statistical Data**: Shape statistics and material properties

## Troubleshooting

### Common Issues

1. **Missing Dependencies**:
   ```bash
   python check_requirements.py
   pip install -r requirements.txt
   ```

2. **Large File Processing**:
   - Files are processed in 50-statement batches
   - Memory usage is controlled for large binary data
   - Failed statements are logged but don't stop migration

3. **Database Reset** (if needed):
   ```bash
   python migrate_data.py reset
   ```

### Validation Errors

The migration includes comprehensive validation:
- **Warnings**: Non-critical issues (e.g., unusual property values)
- **Errors**: Critical issues that prevent proper operation

### Performance Considerations

- **Initial Migration**: 5-15 minutes depending on system performance
- **Database Size**: ~50-100MB after complete migration
- **Memory Usage**: Peak ~200MB during large file processing

## Database Schema

The migrated SQLite database includes these tables:

| Table | Records | Description |
|-------|---------|-------------|
| `cement` | 168+ | Portland cement compositions |
| `fly_ash` | 2+ | Supplementary cementitious materials |
| `slag` | 2+ | Ground granulated blast-furnace slag |
| `aggregate` | 20+ | Coarse and fine aggregates |
| `inert_filler` | 5+ | Non-reactive fillers |
| `grading` | 10+ | Particle size distribution curves |
| `particle_shape_set` | 15+ | Shape definitions |
| `aggregate_sieve` | 20+ | Standard sieve specifications |
| `db_file` | 50+ | PSD and alkali characteristic files |
| `operation` | 0+ | Simulation tracking (initially empty) |

## Data Integrity

### Preserved Elements
- ✅ All binary data (images, analysis files)
- ✅ Material property relationships
- ✅ File references and cross-links
- ✅ Numerical precision
- ✅ Metadata and descriptions

### Validation Checks
- Property value ranges (specific gravity, fractions)
- Relationship integrity (PSD references)
- Binary data completeness
- Standard compliance (sieve sizes)

## Next Steps

After successful migration:

1. **Test Application**: Launch the GTK3 application to verify data access
2. **Backup Database**: Create backup of migrated SQLite database
3. **Performance Tuning**: Optimize for your specific use patterns

## Support

For migration issues:
1. Check logs for detailed error messages
2. Verify all dependencies are correctly installed
3. Ensure source Flyway scripts are accessible
4. Review validation results for data quality issues

The migration system is designed to be robust and handle the complex scientific data in VCCTL while providing clear feedback on any issues encountered.
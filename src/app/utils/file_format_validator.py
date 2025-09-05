#!/usr/bin/env python3
"""
Enhanced File Format Validation for VCCTL

Provides comprehensive file format validation, content verification,
and schema validation for VCCTL material and data files.
"""

import json
import csv
import xml.etree.ElementTree as ET
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re

from .file_operations import FileValidationResult


class MaterialType(Enum):
    """Supported material types for validation."""
    CEMENT = "cement"
    FLY_ASH = "flyash"
    SLAG = "slag"
    AGGREGATE = "aggregate"
    FILLER = "filler"


class ValidationSeverity(Enum):
    """Validation issue severity levels."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    """Represents a validation issue."""
    severity: ValidationSeverity
    message: str
    location: Optional[str] = None
    suggestion: Optional[str] = None


@dataclass
class SchemaValidationResult:
    """Result of schema validation."""
    is_valid: bool = True
    material_type: Optional[MaterialType] = None
    issues: List[ValidationIssue] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def errors(self) -> List[ValidationIssue]:
        """Get validation errors."""
        return [issue for issue in self.issues if issue.severity == ValidationSeverity.ERROR]
    
    @property
    def warnings(self) -> List[ValidationIssue]:
        """Get validation warnings."""
        return [issue for issue in self.issues if issue.severity == ValidationSeverity.WARNING]
    
    @property
    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return len(self.errors) > 0


class MaterialSchemaValidator:
    """Validates material data against expected schemas."""
    
    # Required fields for each material type
    REQUIRED_FIELDS = {
        MaterialType.CEMENT: {
            'name': str,
            'sil': (int, float),
            'alu': (int, float),
            'fer': (int, float),
            'cal': (int, float),
            'mag': (int, float),
            'sul': (int, float),
            'alk': (int, float),
            'c3s': (int, float),
            'c2s': (int, float),
            'c3a': (int, float),
            'c4af': (int, float),
        },
        MaterialType.FLY_ASH: {
            'name': str,
            'sil': (int, float),
            'alu': (int, float),
            'fer': (int, float),
            'cal': (int, float),
            'mag': (int, float),
            'sul': (int, float),
            'alk': (int, float),
            'pozzolan_activity_index': (int, float),
        },
        MaterialType.SLAG: {
            'name': str,
            'sil': (int, float),
            'alu': (int, float),
            'fer': (int, float),
            'cal': (int, float),
            'mag': (int, float),
            'sul': (int, float),
            'alk': (int, float),
            'glass_content': (int, float),
        },
        MaterialType.AGGREGATE: {
            'name': str,
            'specific_gravity': (int, float),
            'absorption': (int, float),
            'gradation': dict,
        },
        MaterialType.FILLER: {
            'name': str,
            'specific_gravity': (int, float),
            'surface_area': (int, float),
        }
    }
    
    # Value ranges for validation
    VALUE_RANGES = {
        'sil': (0.0, 100.0),
        'alu': (0.0, 100.0),
        'fer': (0.0, 100.0),
        'cal': (0.0, 100.0),
        'mag': (0.0, 100.0),
        'sul': (0.0, 100.0),
        'alk': (0.0, 100.0),
        'c3s': (0.0, 100.0),
        'c2s': (0.0, 100.0),
        'c3a': (0.0, 100.0),
        'c4af': (0.0, 100.0),
        'specific_gravity': (1.0, 5.0),
        'absorption': (0.0, 30.0),
        'pozzolan_activity_index': (0.0, 200.0),
        'glass_content': (0.0, 100.0),
        'surface_area': (0.0, 10000.0),
    }
    
    def __init__(self):
        """Initialize the schema validator."""
        self.logger = logging.getLogger('VCCTL.MaterialSchemaValidator')
    
    def validate_material_data(self, data: Dict[str, Any], 
                             expected_type: Optional[MaterialType] = None) -> SchemaValidationResult:
        """
        Validate material data against schema.
        
        Args:
            data: Material data dictionary
            expected_type: Expected material type (auto-detected if None)
            
        Returns:
            SchemaValidationResult with validation details
        """
        result = SchemaValidationResult()
        
        try:
            # Detect material type if not specified
            if expected_type is None:
                detected_type = self._detect_material_type(data)
                if detected_type is None:
                    result.is_valid = False
                    result.issues.append(ValidationIssue(
                        ValidationSeverity.ERROR,
                        "Cannot determine material type from data",
                        suggestion="Add material type field or ensure required fields are present"
                    ))
                    return result
                result.material_type = detected_type
            else:
                result.material_type = expected_type
            
            # Validate required fields
            self._validate_required_fields(data, result.material_type, result)
            
            # Validate field types and ranges
            self._validate_field_types_and_ranges(data, result.material_type, result)
            
            # Material-specific validation
            self._validate_material_specific(data, result.material_type, result)
            
            # Cross-field validation
            self._validate_cross_fields(data, result.material_type, result)
            
            # Set overall validity
            result.is_valid = not result.has_errors
            
            # Collect metadata
            result.metadata = {
                'field_count': len(data),
                'numeric_fields': len([k for k, v in data.items() if isinstance(v, (int, float))]),
                'string_fields': len([k for k, v in data.items() if isinstance(v, str)]),
            }
            
        except Exception as e:
            self.logger.error(f"Schema validation failed: {e}")
            result.is_valid = False
            result.issues.append(ValidationIssue(
                ValidationSeverity.ERROR,
                f"Validation error: {e}"
            ))
        
        return result
    
    def _detect_material_type(self, data: Dict[str, Any]) -> Optional[MaterialType]:
        """Detect material type from data fields."""
        # Check for explicit type field
        if 'type' in data:
            type_value = data['type'].lower()
            for mat_type in MaterialType:
                if mat_type.value == type_value:
                    return mat_type
        
        # Detect by characteristic fields
        if 'c3s' in data or 'c2s' in data or 'c3a' in data or 'c4af' in data:
            return MaterialType.CEMENT
        elif 'pozzolan_activity_index' in data:
            return MaterialType.FLY_ASH
        elif 'glass_content' in data:
            return MaterialType.SLAG
        elif 'gradation' in data:
            return MaterialType.AGGREGATE
        elif 'surface_area' in data and 'specific_gravity' in data and len(data) < 10:
            return MaterialType.FILLER
        
        return None
    
    def _validate_required_fields(self, data: Dict[str, Any], 
                                 material_type: MaterialType,
                                 result: SchemaValidationResult) -> None:
        """Validate that all required fields are present."""
        required_fields = self.REQUIRED_FIELDS.get(material_type, {})
        
        for field_name, field_type in required_fields.items():
            if field_name not in data:
                result.issues.append(ValidationIssue(
                    ValidationSeverity.ERROR,
                    f"Missing required field: {field_name}",
                    location=field_name,
                    suggestion=f"Add {field_name} field with type {field_type.__name__}"
                ))
    
    def _validate_field_types_and_ranges(self, data: Dict[str, Any],
                                       material_type: MaterialType,
                                       result: SchemaValidationResult) -> None:
        """Validate field types and value ranges."""
        required_fields = self.REQUIRED_FIELDS.get(material_type, {})
        
        for field_name, value in data.items():
            # Skip metadata fields
            if field_name.startswith('_'):
                continue
            
            # Check type if field is required
            if field_name in required_fields:
                expected_type = required_fields[field_name]
                if not isinstance(value, expected_type):
                    result.issues.append(ValidationIssue(
                        ValidationSeverity.ERROR,
                        f"Wrong type for field {field_name}: expected {expected_type}, got {type(value)}",
                        location=field_name,
                        suggestion=f"Convert {field_name} to {expected_type.__name__}"
                    ))
                    continue
            
            # Check value ranges for numeric fields
            if isinstance(value, (int, float)) and field_name in self.VALUE_RANGES:
                min_val, max_val = self.VALUE_RANGES[field_name]
                if not (min_val <= value <= max_val):
                    severity = ValidationSeverity.WARNING if abs(value - min_val) < 1 or abs(value - max_val) < 1 else ValidationSeverity.ERROR
                    result.issues.append(ValidationIssue(
                        severity,
                        f"Value out of range for {field_name}: {value} not in [{min_val}, {max_val}]",
                        location=field_name,
                        suggestion=f"Check if {field_name} value is correct"
                    ))
    
    def _validate_material_specific(self, data: Dict[str, Any],
                                  material_type: MaterialType,
                                  result: SchemaValidationResult) -> None:
        """Perform material-specific validation."""
        if material_type == MaterialType.CEMENT:
            self._validate_cement_specific(data, result)
        elif material_type == MaterialType.FLY_ASH:
            self._validate_fly_ash_specific(data, result)
        elif material_type == MaterialType.SLAG:
            self._validate_slag_specific(data, result)
        elif material_type == MaterialType.AGGREGATE:
            self._validate_aggregate_specific(data, result)
        elif material_type == MaterialType.FILLER:
            self._validate_filler_specific(data, result)
    
    def _validate_cement_specific(self, data: Dict[str, Any], 
                                result: SchemaValidationResult) -> None:
        """Validate cement-specific constraints."""
        # Check oxide sum (should be close to 100%)
        oxide_fields = ['sil', 'alu', 'fer', 'cal', 'mag', 'sul', 'alk']
        oxide_sum = sum(data.get(field, 0) for field in oxide_fields)
        
        if oxide_sum < 95 or oxide_sum > 105:
            result.issues.append(ValidationIssue(
                ValidationSeverity.WARNING,
                f"Oxide sum unusual: {oxide_sum:.1f}% (expected ~100%)",
                suggestion="Check oxide percentages for accuracy"
            ))
        
        # Check phase sum (C3S + C2S + C3A + C4AF should be reasonable)
        phase_fields = ['c3s', 'c2s', 'c3a', 'c4af']
        phase_sum = sum(data.get(field, 0) for field in phase_fields)
        
        if phase_sum > 100:
            result.issues.append(ValidationIssue(
                ValidationSeverity.ERROR,
                f"Phase sum too high: {phase_sum:.1f}% (should not exceed 100%)",
                suggestion="Check calculated phase percentages"
            ))
        elif phase_sum < 70:
            result.issues.append(ValidationIssue(
                ValidationSeverity.WARNING,
                f"Phase sum low: {phase_sum:.1f}% (typically 80-95%)",
                suggestion="Verify phase calculation method"
            ))
    
    def _validate_fly_ash_specific(self, data: Dict[str, Any],
                                 result: SchemaValidationResult) -> None:
        """Validate fly ash-specific constraints."""
        # Check SiO2 + Al2O3 + Fe2O3 content (ASTM C618 requirement)
        saf_sum = data.get('sil', 0) + data.get('alu', 0) + data.get('fer', 0)
        
        if saf_sum < 70:
            result.issues.append(ValidationIssue(
                ValidationSeverity.WARNING,
                f"SiO2+Al2O3+Fe2O3 = {saf_sum:.1f}% (ASTM C618 requires ≥70% for Class F)",
                location="sil,alu,fer",
                suggestion="Verify fly ash classification"
            ))
        
        # Check pozzolan activity index
        if 'pozzolan_activity_index' in data:
            pai = data['pozzolan_activity_index']
            if pai < 75:
                result.issues.append(ValidationIssue(
                    ValidationSeverity.WARNING,
                    f"Low pozzolan activity index: {pai}% (ASTM C618 requires ≥75%)",
                    location="pozzolan_activity_index"
                ))
    
    def _validate_slag_specific(self, data: Dict[str, Any],
                              result: SchemaValidationResult) -> None:
        """Validate slag-specific constraints."""
        # Check glass content
        if 'glass_content' in data:
            glass = data['glass_content']
            if glass < 67:
                result.issues.append(ValidationIssue(
                    ValidationSeverity.WARNING,
                    f"Low glass content: {glass}% (ASTM C989 typically requires ≥67%)",
                    location="glass_content"
                ))
    
    def _validate_aggregate_specific(self, data: Dict[str, Any],
                                   result: SchemaValidationResult) -> None:
        """Validate aggregate-specific constraints."""
        # Check gradation data structure
        if 'gradation' in data:
            gradation = data['gradation']
            if not isinstance(gradation, dict):
                result.issues.append(ValidationIssue(
                    ValidationSeverity.ERROR,
                    "Gradation must be a dictionary of sieve sizes and percentages",
                    location="gradation"
                ))
            else:
                # Validate gradation percentages
                for sieve, percent in gradation.items():
                    if not isinstance(percent, (int, float)):
                        result.issues.append(ValidationIssue(
                            ValidationSeverity.ERROR,
                            f"Gradation percentage must be numeric: {sieve} = {percent}",
                            location=f"gradation.{sieve}"
                        ))
                    elif not (0 <= percent <= 100):
                        result.issues.append(ValidationIssue(
                            ValidationSeverity.ERROR,
                            f"Gradation percentage out of range: {sieve} = {percent}%",
                            location=f"gradation.{sieve}"
                        ))
    
    def _validate_filler_specific(self, data: Dict[str, Any],
                                      result: SchemaValidationResult) -> None:
        """Validate inert filler-specific constraints."""
        # Check reasonable surface area
        if 'surface_area' in data:
            sa = data['surface_area']
            if sa > 5000:
                result.issues.append(ValidationIssue(
                    ValidationSeverity.WARNING,
                    f"Very high surface area: {sa} m²/kg (typical range: 200-2000)",
                    location="surface_area"
                ))
            elif sa < 50:
                result.issues.append(ValidationIssue(
                    ValidationSeverity.WARNING,
                    f"Very low surface area: {sa} m²/kg (typical range: 200-2000)",
                    location="surface_area"
                ))
    
    def _validate_cross_fields(self, data: Dict[str, Any],
                             material_type: MaterialType,
                             result: SchemaValidationResult) -> None:
        """Validate relationships between fields."""
        # Common validation: name should be reasonable
        if 'name' in data:
            name = data['name']
            if not isinstance(name, str) or len(name.strip()) == 0:
                result.issues.append(ValidationIssue(
                    ValidationSeverity.ERROR,
                    "Material name cannot be empty",
                    location="name"
                ))
            elif len(name) > 100:
                result.issues.append(ValidationIssue(
                    ValidationSeverity.WARNING,
                    f"Material name very long: {len(name)} characters",
                    location="name"
                ))


class EnhancedFileFormatValidator:
    """Enhanced file format validator with schema validation."""
    
    def __init__(self):
        """Initialize the enhanced validator."""
        self.logger = logging.getLogger('VCCTL.EnhancedFileFormatValidator')
        self.material_validator = MaterialSchemaValidator()
    
    def validate_material_file(self, file_path: Path, 
                             expected_type: Optional[MaterialType] = None) -> Tuple[FileValidationResult, SchemaValidationResult]:
        """
        Validate a material file with both format and schema validation.
        
        Args:
            file_path: Path to the file to validate
            expected_type: Expected material type
            
        Returns:
            Tuple of (file_validation_result, schema_validation_result)
        """
        from .file_operations import FileValidator
        
        # First validate file format
        file_validator = FileValidator()
        file_result = file_validator.validate_file(file_path)
        
        # Initialize schema result
        schema_result = SchemaValidationResult()
        
        if not file_result.is_valid:
            schema_result.is_valid = False
            schema_result.issues.append(ValidationIssue(
                ValidationSeverity.ERROR,
                "File format validation failed"
            ))
            return file_result, schema_result
        
        try:
            # Parse file content based on format
            data = self._parse_file_content(file_path, file_result.file_type)
            
            # Validate material schema
            schema_result = self.material_validator.validate_material_data(data, expected_type)
            
        except Exception as e:
            self.logger.error(f"Schema validation failed for {file_path}: {e}")
            schema_result.is_valid = False
            schema_result.issues.append(ValidationIssue(
                ValidationSeverity.ERROR,
                f"Content parsing failed: {e}"
            ))
        
        return file_result, schema_result
    
    def _parse_file_content(self, file_path: Path, file_type: str) -> Dict[str, Any]:
        """Parse file content based on type."""
        if file_type == 'application/json':
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        elif file_type == 'text/csv':
            data = {}
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Take first row as single material
                    for key, value in row.items():
                        # Try to convert numeric values
                        try:
                            if '.' in value:
                                data[key] = float(value)
                            else:
                                data[key] = int(value)
                        except (ValueError, TypeError):
                            data[key] = value
                    break
            return data
        
        elif file_type == 'application/xml':
            tree = ET.parse(file_path)
            root = tree.getroot()
            data = {}
            
            for element in root:
                if element.text:
                    try:
                        # Try numeric conversion
                        if '.' in element.text:
                            data[element.tag] = float(element.text)
                        else:
                            data[element.tag] = int(element.text)
                    except ValueError:
                        data[element.tag] = element.text
            
            return data
        
        else:
            raise ValueError(f"Unsupported file type for material parsing: {file_type}")
    
    def generate_validation_report(self, file_path: Path,
                                 file_result: FileValidationResult,
                                 schema_result: SchemaValidationResult) -> str:
        """Generate a comprehensive validation report."""
        report_lines = [
            f"Validation Report for: {file_path.name}",
            "=" * 50,
            "",
            f"File Format Validation: {'PASS' if file_result.is_valid else 'FAIL'}",
            f"File Type: {file_result.file_type}",
            f"File Size: {file_result.size_bytes} bytes",
        ]
        
        if file_result.errors:
            report_lines.extend([
                "",
                "File Format Errors:",
                *[f"  - {error}" for error in file_result.errors]
            ])
        
        if file_result.warnings:
            report_lines.extend([
                "",
                "File Format Warnings:",
                *[f"  - {warning}" for warning in file_result.warnings]
            ])
        
        report_lines.extend([
            "",
            f"Schema Validation: {'PASS' if schema_result.is_valid else 'FAIL'}",
        ])
        
        if schema_result.material_type:
            report_lines.append(f"Material Type: {schema_result.material_type.value}")
        
        if schema_result.errors:
            report_lines.extend([
                "",
                "Schema Errors:",
                *[f"  - {issue.message}" + (f" ({issue.location})" if issue.location else "") 
                  for issue in schema_result.errors]
            ])
        
        if schema_result.warnings:
            report_lines.extend([
                "",
                "Schema Warnings:",
                *[f"  - {issue.message}" + (f" ({issue.location})" if issue.location else "") 
                  for issue in schema_result.warnings]
            ])
        
        if schema_result.metadata:
            report_lines.extend([
                "",
                "Metadata:",
                *[f"  {key}: {value}" for key, value in schema_result.metadata.items()]
            ])
        
        return "\n".join(report_lines)
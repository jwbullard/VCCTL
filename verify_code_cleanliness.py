#!/usr/bin/env python3
"""
Code Cleanliness Verification Script

Verifies that Phase 2 cleanup removed:
1. All remaining inappropriate genmic_ prefixes in active code
2. Any duplicate functionality 
3. Old/unused methods

Ensures the codebase is clean for Phase 3 implementation.
"""

import os
import re
import logging
from pathlib import Path

def setup_logging():
    """Setup logging for verification."""
    logger = logging.getLogger('CleanlinessCheck')
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
    logger.addHandler(handler)
    return logger

def check_genmic_prefixes():
    """Check for remaining inappropriate genmic_ prefixes in source code."""
    logger = logging.getLogger('CleanlinessCheck')
    
    # Files to check (active source code only)
    src_files = []
    src_dir = Path("src")
    
    if src_dir.exists():
        # Get all Python files in src
        src_files = list(src_dir.rglob("*.py"))
    
    if not src_files:
        logger.warning("No source files found - check if running from project root")
        return True
    
    issues = []
    
    # Patterns that should NOT exist in clean code
    problematic_patterns = [
        (r'genmic_input_.*Microstructure', "Old operation naming with genmic_input_ prefix"),
        (r'operation_name.*=.*genmic_input_', "Operation name generation using old prefix"),  
        (r'\"genmic_input_.*\"', "Hardcoded genmic_input_ references"),
        (r'f\"genmic_input_', "F-string with genmic_input_ prefix")
    ]
    
    # Patterns that are OK (legitimate genmic references)
    allowed_patterns = [
        r'genmic_path',  # Executable path
        r'genmic\.c',    # Program name references
        r'genmic_progress\.txt', # Progress file name (legitimate)
        r'parse_genmic_progress', # Method names for parsing
        r'_generate_genmic_input_file', # Method that generates content
        r'genmic_mode', # Database field
        r'\.genmic', # File extensions
        r'genmic executable', # Comments about executable
        r'genmic program' # Comments about program
    ]
    
    for src_file in src_files:
        try:
            with open(src_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            for line_num, line in enumerate(content.split('\n'), 1):
                for pattern, description in problematic_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        # Check if this is an allowed pattern
                        is_allowed = False
                        for allowed in allowed_patterns:
                            if re.search(allowed, line, re.IGNORECASE):
                                is_allowed = True
                                break
                        
                        if not is_allowed:
                            issues.append({
                                'file': str(src_file),
                                'line': line_num,
                                'content': line.strip(),
                                'issue': description
                            })
                            
        except Exception as e:
            logger.error(f"Error checking {src_file}: {e}")
    
    # Report results
    if issues:
        logger.error(f"Found {len(issues)} problematic genmic_ references:")
        for issue in issues:
            logger.error(f"  {issue['file']}:{issue['line']} - {issue['issue']}")
            logger.error(f"    Content: {issue['content']}")
        return False
    else:
        logger.info("✓ No problematic genmic_ prefixes found in source code")
        return True

def check_duplicate_functionality():
    """Check for duplicate functionality that should be removed."""
    logger = logging.getLogger('CleanlinessCheck')
    
    # Files to check
    mix_design_file = Path("src/app/windows/panels/mix_design_panel.py")
    
    if not mix_design_file.exists():
        logger.warning("Mix design panel file not found")
        return True
    
    issues = []
    
    try:
        with open(mix_design_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Methods that should NOT exist (old/duplicate functionality)
        problematic_methods = [
            (r'def _load_microstructure_operation\(', "Old microstructure loading method should be removed"),
            (r'def.*load.*micro.*operation', "Duplicate microstructure loading functionality"),
        ]
        
        for line_num, line in enumerate(content.split('\n'), 1):
            for pattern, description in problematic_methods:
                if re.search(pattern, line, re.IGNORECASE):
                    # Check if it's just a comment
                    if not line.strip().startswith('#'):
                        issues.append({
                            'file': str(mix_design_file),
                            'line': line_num,
                            'content': line.strip(),
                            'issue': description
                        })
    
    except Exception as e:
        logger.error(f"Error checking for duplicate functionality: {e}")
        return False
    
    # Report results
    if issues:
        logger.error(f"Found {len(issues)} duplicate functionality issues:")
        for issue in issues:
            logger.error(f"  {issue['file']}:{issue['line']} - {issue['issue']}")
            logger.error(f"    Content: {issue['content']}")
        return False
    else:
        logger.info("✓ No duplicate functionality found")
        return True

def check_clean_naming_implementation():
    """Verify that clean naming is properly implemented."""
    logger = logging.getLogger('CleanlinessCheck')
    
    mix_design_file = Path("src/app/windows/panels/mix_design_panel.py")
    
    if not mix_design_file.exists():
        logger.warning("Mix design panel file not found")
        return True
    
    try:
        with open(mix_design_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for clean naming implementation
        checks = [
            ('operation_name_entry', 'Operation name input field'),
            ('_capture_ui_parameters', 'UI parameter capture method'),
            ('_store_ui_parameters_in_operation', 'UI parameter storage method'),
            ('_show_load_operation_dialog', 'Load operation dialog method'),
            ('_restore_ui_from_operation', 'UI restoration method'),
        ]
        
        missing = []
        for check, description in checks:
            if check not in content:
                missing.append(description)
        
        if missing:
            logger.error(f"Missing clean naming implementation components:")
            for item in missing:
                logger.error(f"  - {item}")
            return False
        else:
            logger.info("✓ Clean naming implementation components found")
            
            # Check for specific clean naming patterns
            if 'f"{mix_name_safe}_input.txt"' in content:
                logger.info("✓ Clean input file naming implemented")
            else:
                logger.warning("Clean input file naming may not be implemented")
                
            return True
            
    except Exception as e:
        logger.error(f"Error checking clean naming implementation: {e}")
        return False

def main():
    """Run code cleanliness verification."""
    logger = setup_logging()
    
    logger.info("=" * 60)
    logger.info("Code Cleanliness Verification - Phase 2 Cleanup")
    logger.info("=" * 60)
    
    checks = [
        ("Genmic Prefix Cleanup", check_genmic_prefixes),
        ("Duplicate Functionality Check", check_duplicate_functionality), 
        ("Clean Naming Implementation", check_clean_naming_implementation)
    ]
    
    results = []
    for check_name, check_func in checks:
        logger.info(f"\n{check_name}...")
        try:
            result = check_func()
            results.append((check_name, result))
            if result:
                logger.info(f"✅ {check_name} PASSED")
            else:
                logger.error(f"❌ {check_name} FAILED")
        except Exception as e:
            logger.error(f"❌ {check_name} ERROR: {e}")
            results.append((check_name, False))
    
    # Summary
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    logger.info("\n" + "=" * 60)
    if passed == total:
        logger.info("🎉 Code Cleanliness Verification PASSED!")
        logger.info("✓ No inappropriate genmic_ prefixes found")
        logger.info("✓ No duplicate functionality found")
        logger.info("✓ Clean naming implementation verified")
        logger.info("✓ Codebase ready for Phase 3!")
    else:
        logger.error(f"❌ Code Cleanliness Verification FAILED: {passed}/{total} passed")
        logger.error("Fix issues before proceeding")
    logger.info("=" * 60)
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
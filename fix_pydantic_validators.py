#!/usr/bin/env python3
"""
Fix Pydantic v2 compatibility issues in model files.
Updates @validator and @root_validator to Pydantic v2 equivalents.
"""

import os
import re
from pathlib import Path

def fix_pydantic_imports(content: str) -> str:
    """Fix pydantic imports to use v2 validators."""
    # Replace validator imports
    content = re.sub(
        r'from pydantic import ([^,\n]*,\s*)?validator([^,\n]*,\s*)?',
        r'from pydantic import \1field_validator\2',
        content
    )
    content = re.sub(
        r'from pydantic import ([^,\n]*,\s*)?root_validator([^,\n]*,\s*)?',
        r'from pydantic import \1model_validator\2',
        content
    )
    
    # Add missing imports if needed
    if '@field_validator' in content and 'field_validator' not in content:
        content = re.sub(
            r'from pydantic import ([^,\n]*)',
            r'from pydantic import \1, field_validator',
            content
        )
    
    if '@model_validator' in content and 'model_validator' not in content:
        content = re.sub(
            r'from pydantic import ([^,\n]*)',
            r'from pydantic import \1, model_validator',
            content
        )
    
    return content

def fix_field_validators(content: str) -> str:
    """Fix @validator decorators to @field_validator."""
    # Pattern to match @validator decorator and the function
    validator_pattern = r'@validator\((.*?)\)\s*\n\s*def\s+(\w+)\s*\(\s*cls\s*,\s*v\s*\):'
    
    def replace_validator(match):
        field_name = match.group(1)
        func_name = match.group(2)
        return f'@field_validator({field_name})\n    @classmethod\n    def {func_name}(cls, v):'
    
    content = re.sub(validator_pattern, replace_validator, content, flags=re.MULTILINE)
    return content

def fix_root_validators(content: str) -> str:
    """Fix @root_validator decorators to @model_validator."""
    # Pattern to match @root_validator decorator and the function
    root_validator_pattern = r'@root_validator(?:\([^)]*\))?\s*\n\s*def\s+(\w+)\s*\(\s*cls\s*,\s*values\s*\):'
    
    def replace_root_validator(match):
        func_name = match.group(1)
        return f'@model_validator(mode=\'after\')\n    def {func_name}(self):'
    
    content = re.sub(root_validator_pattern, replace_root_validator, content, flags=re.MULTILINE)
    
    # Fix function body to use self instead of values
    content = re.sub(r'values\.get\([\'"](\w+)[\'"]\)', r'self.\1', content)
    content = re.sub(r'return values', r'return self', content)
    
    return content

def fix_file(file_path: Path) -> bool:
    """Fix a single file. Returns True if file was modified."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        content = original_content
        content = fix_pydantic_imports(content)
        content = fix_field_validators(content)
        content = fix_root_validators(content)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Fixed {file_path}")
            return True
        else:
            print(f"⏭️  No changes needed for {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ Error fixing {file_path}: {e}")
        return False

def main():
    """Main function to fix all model files."""
    models_dir = Path('src/app/models')
    
    if not models_dir.exists():
        print(f"❌ Models directory not found: {models_dir}")
        return False
    
    python_files = list(models_dir.glob('*.py'))
    fixed_count = 0
    
    print(f"🔧 Fixing Pydantic validators in {len(python_files)} files...")
    
    for file_path in python_files:
        if file_path.name == '__init__.py':
            continue
        
        if fix_file(file_path):
            fixed_count += 1
    
    print(f"\n✨ Fixed {fixed_count} files")
    return True

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
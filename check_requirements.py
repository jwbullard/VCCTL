#!/usr/bin/env python3
"""
Check if required dependencies are installed for VCCTL.
"""

import sys
import importlib
from pathlib import Path

# Required packages
REQUIRED_PACKAGES = [
    ('sqlalchemy', 'SQLAlchemy>=2.0.0'),
    ('pydantic', 'pydantic>=2.0.0'),
    ('gi', 'PyGObject>=3.42.0'),
    ('yaml', 'PyYAML>=6.0'),
    ('pandas', 'pandas>=2.0.0'),
    ('numpy', 'numpy>=1.24.0'),
]

def check_package(package_name, requirement_str):
    """Check if a package is available."""
    try:
        module = importlib.import_module(package_name)
        version = getattr(module, '__version__', 'unknown')
        return True, version
    except ImportError:
        return False, None

def main():
    """Check all requirements."""
    print("🔍 Checking VCCTL Requirements")
    print("=" * 40)
    
    missing_packages = []
    
    for package_name, requirement_str in REQUIRED_PACKAGES:
        available, version = check_package(package_name, requirement_str)
        
        if available:
            print(f"✅ {requirement_str:<20} (installed: {version})")
        else:
            print(f"❌ {requirement_str:<20} (missing)")
            missing_packages.append(requirement_str)
    
    print("\n" + "=" * 40)
    
    if missing_packages:
        print("❌ Missing dependencies found!")
        print("\nTo install missing packages:")
        print("pip install " + " ".join([f'"{pkg}"' for pkg in missing_packages]))
        print("\nOr install all at once:")
        print("pip install -r requirements.txt")
        return 1
    else:
        print("✅ All requirements satisfied!")
        return 0

if __name__ == '__main__':
    sys.exit(main())
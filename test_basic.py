#!/usr/bin/env python3
"""
Basic test script to verify project structure and imports without GUI.
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test basic imports without initializing GTK."""
    print("Testing basic project structure...")
    
    try:
        # Test app_info import
        from app.resources.app_info import APP_NAME, APP_VERSION
        print(f"✓ App info loaded: {APP_NAME} v{APP_VERSION}")
    except ImportError as e:
        print(f"✗ Failed to import app_info: {e}")
        return False
    
    try:
        # Test directory structure
        import app
        import app.windows
        import app.models
        import app.services
        import app.database
        import app.utils
        print("✓ All app modules can be imported")
    except ImportError as e:
        print(f"✗ Failed to import app modules: {e}")
        return False
    
    print("✓ Basic project structure test passed!")
    return True

def test_paths():
    """Test that required directories exist."""
    print("\nTesting directory structure...")
    
    required_dirs = [
        'src',
        'src/app',
        'src/app/windows',
        'src/app/models',
        'src/app/services',
        'src/app/database',
        'src/app/utils',
        'src/app/resources',
        'src/tests',
        'src/data'
    ]
    
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"✓ {dir_path}")
        else:
            print(f"✗ {dir_path} - missing")
            return False
    
    print("✓ All required directories exist!")
    return True

def main():
    """Run basic tests."""
    print("VCCTL GTK3 Project - Basic Structure Test")
    print("=" * 50)
    
    success = True
    success &= test_paths()
    success &= test_imports()
    
    print("\n" + "=" * 50)
    if success:
        print("✓ All basic tests passed!")
        print("\nTo run the full application (requires GTK3):")
        print("  source dev-setup.sh")
        print("  python src/main.py")
        return 0
    else:
        print("✗ Some tests failed!")
        return 1

if __name__ == '__main__':
    sys.exit(main())
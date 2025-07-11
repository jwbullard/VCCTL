#!/usr/bin/env python3
"""
VCCTL GTK3 Application Entry Point

Virtual Cement and Concrete Testing Laboratory
Desktop application using GTK3 and Python
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app.application import VCCTLApplication
except ImportError as e:
    print(f"Error importing application: {e}")
    print("Make sure GTK3 and PyGObject are properly installed.")
    print("Run: pip install PyGObject")
    sys.exit(1)


def main():
    """Main entry point for the VCCTL GTK application."""
    try:
        app = VCCTLApplication()
        return app.run(sys.argv)
    except Exception as e:
        print(f"Error starting application: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
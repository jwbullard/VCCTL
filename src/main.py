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

from app.application import VCCTLApplication


def main():
    """Main entry point for the VCCTL GTK application."""
    app = VCCTLApplication()
    return app.run(sys.argv)


if __name__ == '__main__':
    sys.exit(main())
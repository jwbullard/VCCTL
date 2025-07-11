#!/bin/bash
# Development environment setup script for VCCTL GTK3

# Set GTK/GObject environment variables
export PKG_CONFIG_PATH="/opt/homebrew/lib/pkgconfig:$PKG_CONFIG_PATH"
export GI_TYPELIB_PATH="/opt/homebrew/lib/girepository-1.0:$GI_TYPELIB_PATH"
export LD_LIBRARY_PATH="/opt/homebrew/lib:$LD_LIBRARY_PATH"
export DYLD_LIBRARY_PATH="/opt/homebrew/lib:$DYLD_LIBRARY_PATH"

# Activate virtual environment
source vcctl-gtk-env/bin/activate

echo "Development environment configured!"
echo "GTK3 version: $(pkg-config --modversion gtk+-3.0)"
echo "Python: $(python --version)"
echo ""
echo "To run the application:"
echo "  python src/main.py"
echo ""
echo "To run tests:"
echo "  pytest src/tests/"
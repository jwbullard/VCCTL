#!/bin/bash
# Development environment setup script for VCCTL GTK3

# Set GTK/GObject environment variables for macOS Homebrew
export PKG_CONFIG_PATH="/opt/homebrew/lib/pkgconfig:$PKG_CONFIG_PATH"
export GI_TYPELIB_PATH="/opt/homebrew/lib/girepository-1.0:$GI_TYPELIB_PATH"
export LD_LIBRARY_PATH="/opt/homebrew/lib:$LD_LIBRARY_PATH"
export DYLD_LIBRARY_PATH="/opt/homebrew/lib:$DYLD_LIBRARY_PATH"

# Additional library paths for macOS
export DYLD_FALLBACK_LIBRARY_PATH="/opt/homebrew/lib:$DYLD_FALLBACK_LIBRARY_PATH"

# Activate virtual environment
source vcctl-gtk-env/bin/activate

echo "Development environment configured!"

# Check if required libraries are available
if command -v pkg-config >/dev/null 2>&1; then
    echo "GTK3 version: $(pkg-config --modversion gtk+-3.0 2>/dev/null || echo 'Not found')"
else
    echo "pkg-config not found"
fi

echo "Python: $(python --version)"
echo ""

# Test basic GTK import
echo "Testing GTK3 import..."
if python -c "import gi; gi.require_version('Gtk', '3.0'); from gi.repository import Gtk; print('✓ GTK3 import successful')" 2>/dev/null; then
    echo "✓ GTK3 environment ready"
else
    echo "✗ GTK3 import failed - check environment setup"
fi

echo ""
echo "To run the application:"
echo "  python src/main.py"
echo ""
echo "To run tests:"
echo "  pytest src/tests/"
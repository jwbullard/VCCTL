#!/bin/bash
# VCCTL GTK3 Environment Setup Script for macOS

echo "Setting up VCCTL GTK3 environment..."

# Activate virtual environment
source vcctl-gtk-env/bin/activate

# Set up GTK3 environment variables for macOS with Homebrew
export PKG_CONFIG_PATH="/opt/homebrew/lib/pkgconfig:/opt/homebrew/share/pkgconfig"
export GI_TYPELIB_PATH="/opt/homebrew/lib/girepository-1.0"
export DYLD_LIBRARY_PATH="/opt/homebrew/lib:$DYLD_LIBRARY_PATH"

echo "Environment variables set:"
echo "PKG_CONFIG_PATH: $PKG_CONFIG_PATH"
echo "GI_TYPELIB_PATH: $GI_TYPELIB_PATH"
echo "DYLD_LIBRARY_PATH: $DYLD_LIBRARY_PATH"

echo "Testing GTK3 import..."
python -c "import gi; gi.require_version('Gtk', '3.0'); from gi.repository import Gtk; print('✅ GTK3 import successful!')" 2>/dev/null

echo "Environment ready! You can now run:"
echo "  python src/main.py"
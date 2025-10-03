#!/bin/bash
# macOS Build Script for VCCTL
# Automates the PyInstaller packaging process with required fixes

set -e  # Exit on error

echo "========================================="
echo "  VCCTL macOS Build Script"
echo "========================================="
echo ""

# Clean previous builds
echo "🧹 Cleaning previous builds..."
python3 -m PyInstaller vcctl.spec --clean --noconfirm

# Fix GTK library conflict (PIL's libharfbuzz conflicts with system GTK)
echo ""
echo "🔧 Fixing libharfbuzz conflict..."
rm -rf dist/VCCTL.app/Contents/Frameworks/PIL/__dot__dylibs/libharfbuzz.0.dylib 2>/dev/null || true
rm -f dist/VCCTL.app/Contents/Frameworks/libharfbuzz.0.dylib 2>/dev/null || true
cp /opt/homebrew/lib/libharfbuzz.0.dylib dist/VCCTL.app/Contents/Frameworks/

echo "✅ libharfbuzz fix applied"

# Verify the app bundle was created
if [ -d "dist/VCCTL.app" ]; then
    echo ""
    echo "========================================="
    echo "✅ Build complete!"
    echo "========================================="
    echo ""
    echo "📦 App location: dist/VCCTL.app"
    echo "📏 App size: $(du -sh dist/VCCTL.app | cut -f1)"
    echo ""
    echo "Testing app launch..."
    echo ""

    # Test launch
    open -a dist/VCCTL.app

    # Wait and check if running
    sleep 8
    if ps aux | grep "Contents/MacOS/vcctl" | grep -v grep > /dev/null; then
        echo "✅ App launched successfully!"
        echo ""
        echo "The VCCTL app is now running."
        echo "You can find it in dist/VCCTL.app"
    else
        echo "❌ App failed to launch."
        echo "Check error logs in /tmp/vcctl-test-err.log"
        exit 1
    fi
else
    echo "❌ Build failed! dist/VCCTL.app not found."
    exit 1
fi

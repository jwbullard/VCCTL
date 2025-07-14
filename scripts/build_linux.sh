#!/bin/bash
"""
Linux AppImage build script for VCCTL
Creates a portable AppImage package for Linux systems
"""

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="$PROJECT_ROOT/build"
DIST_DIR="$PROJECT_ROOT/dist"
APPDIR="$BUILD_DIR/VCCTL.AppDir"

echo -e "${BLUE}🐧 Building VCCTL Linux AppImage${NC}"
echo "Project root: $PROJECT_ROOT"

# Create build directories
mkdir -p "$BUILD_DIR" "$DIST_DIR"

# Install build dependencies
echo -e "${YELLOW}📦 Installing build dependencies...${NC}"
pip install pyinstaller>=5.13.0 setuptools wheel

# Download AppImageTool if not present
APPIMAGE_TOOL="$BUILD_DIR/appimagetool"
if [ ! -f "$APPIMAGE_TOOL" ]; then
    echo -e "${YELLOW}⬇️  Downloading AppImageTool...${NC}"
    wget -O "$APPIMAGE_TOOL" \
        "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
    chmod +x "$APPIMAGE_TOOL"
fi

# Build standalone executable
echo -e "${YELLOW}🔨 Building standalone executable...${NC}"
cd "$PROJECT_ROOT"
pyinstaller --clean --noconfirm vcctl.spec

# Create AppDir structure
echo -e "${YELLOW}📁 Creating AppDir structure...${NC}"
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin" "$APPDIR/usr/lib" "$APPDIR/usr/share/applications"

# Copy executable
if [ -d "$DIST_DIR/vcctl" ]; then
    cp -r "$DIST_DIR/vcctl" "$APPDIR/usr/bin/"
else
    echo -e "${RED}❌ Executable not found in $DIST_DIR/vcctl${NC}"
    exit 1
fi

# Create desktop entry
cat > "$APPDIR/vcctl.desktop" << EOF
[Desktop Entry]
Type=Application
Name=VCCTL
Comment=Virtual Cement and Concrete Testing Laboratory
Exec=vcctl
Icon=vcctl
Categories=Science;Education;Engineering;
Terminal=false
StartupWMClass=vcctl
EOF

# Copy desktop entry to standard location
cp "$APPDIR/vcctl.desktop" "$APPDIR/usr/share/applications/"

# Create AppRun script
cat > "$APPDIR/AppRun" << 'EOF'
#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"
export PATH="${HERE}/usr/bin:${PATH}"
export LD_LIBRARY_PATH="${HERE}/usr/lib:${LD_LIBRARY_PATH}"
export PYTHONPATH="${HERE}/usr/lib/python3/site-packages:${PYTHONPATH}"

# Set up GTK environment
export XDG_DATA_DIRS="${HERE}/usr/share:${XDG_DATA_DIRS}"
export GI_TYPELIB_PATH="${HERE}/usr/lib/girepository-1.0:${GI_TYPELIB_PATH}"

# Change to the application directory
cd "${HERE}/usr/bin/vcctl"

# Execute the application
exec "${HERE}/usr/bin/vcctl/vcctl" "$@"
EOF

chmod +x "$APPDIR/AppRun"

# Copy icon
ICON_SRC="$PROJECT_ROOT/src/app/resources/icons"
if [ -f "$ICON_SRC/vcctl.png" ]; then
    cp "$ICON_SRC/vcctl.png" "$APPDIR/vcctl.png"
elif [ -f "$ICON_SRC/vcctl.svg" ]; then
    # Convert SVG to PNG if needed
    if command -v convert >/dev/null 2>&1; then
        convert "$ICON_SRC/vcctl.svg" -resize 256x256 "$APPDIR/vcctl.png"
    else
        cp "$ICON_SRC/vcctl.svg" "$APPDIR/vcctl.svg"
    fi
else
    echo -e "${YELLOW}⚠️  Icon not found, using default${NC}"
    # Create a simple default icon
    echo "P3 64 64 255 100 100 100" > "$APPDIR/vcctl.ppm"
fi

# Copy system dependencies
echo -e "${YELLOW}📚 Copying system dependencies...${NC}"

# GTK3 and GObject dependencies
SYSTEM_LIBS=(
    "libgtk-3.so.0"
    "libgdk-3.so.0"
    "libgio-2.0.so.0"
    "libgobject-2.0.so.0"
    "libglib-2.0.so.0"
    "libcairo-gobject.so.2"
    "libcairo.so.2"
    "libpango-1.0.so.0"
    "libpangocairo-1.0.so.0"
    "libgdk_pixbuf-2.0.so.0"
    "libgirepository-1.0.so.1"
)

mkdir -p "$APPDIR/usr/lib"
for lib in "${SYSTEM_LIBS[@]}"; do
    if lib_path=$(ldconfig -p | grep "$lib" | awk '{print $4}' | head -1); then
        if [ -f "$lib_path" ]; then
            cp "$lib_path" "$APPDIR/usr/lib/" 2>/dev/null || true
        fi
    fi
done

# Copy GI typelib files
if [ -d "/usr/lib/x86_64-linux-gnu/girepository-1.0" ]; then
    mkdir -p "$APPDIR/usr/lib/girepository-1.0"
    cp /usr/lib/x86_64-linux-gnu/girepository-1.0/Gtk-3.0.typelib "$APPDIR/usr/lib/girepository-1.0/" 2>/dev/null || true
    cp /usr/lib/x86_64-linux-gnu/girepository-1.0/Gdk-3.0.typelib "$APPDIR/usr/lib/girepository-1.0/" 2>/dev/null || true
    cp /usr/lib/x86_64-linux-gnu/girepository-1.0/GObject-2.0.typelib "$APPDIR/usr/lib/girepository-1.0/" 2>/dev/null || true
    cp /usr/lib/x86_64-linux-gnu/girepository-1.0/Gio-2.0.typelib "$APPDIR/usr/lib/girepository-1.0/" 2>/dev/null || true
fi

# Create GTK settings
mkdir -p "$APPDIR/usr/share/gtk-3.0"
cat > "$APPDIR/usr/share/gtk-3.0/settings.ini" << EOF
[Settings]
gtk-theme-name=Adwaita
gtk-icon-theme-name=Adwaita
gtk-font-name=Sans 10
gtk-cursor-theme-name=Adwaita
gtk-cursor-theme-size=24
gtk-toolbar-style=GTK_TOOLBAR_BOTH
gtk-toolbar-icon-size=GTK_ICON_SIZE_LARGE_TOOLBAR
gtk-button-images=1
gtk-menu-images=1
gtk-enable-event-sounds=1
gtk-enable-input-feedback-sounds=1
EOF

# Build AppImage
echo -e "${YELLOW}🏗️  Building AppImage...${NC}"
APPIMAGE_PATH="$DIST_DIR/VCCTL-x86_64.AppImage"

# Remove existing AppImage
rm -f "$APPIMAGE_PATH"

# Run AppImageTool
"$APPIMAGE_TOOL" "$APPDIR" "$APPIMAGE_PATH"

if [ -f "$APPIMAGE_PATH" ]; then
    chmod +x "$APPIMAGE_PATH"
    echo -e "${GREEN}✅ Linux AppImage built successfully: $APPIMAGE_PATH${NC}"
    
    # Display file size
    SIZE=$(du -h "$APPIMAGE_PATH" | cut -f1)
    echo -e "${BLUE}📦 Package size: $SIZE${NC}"
    
    # Test the AppImage
    echo -e "${YELLOW}🧪 Testing AppImage...${NC}"
    if "$APPIMAGE_PATH" --help >/dev/null 2>&1; then
        echo -e "${GREEN}✅ AppImage test passed${NC}"
    else
        echo -e "${YELLOW}⚠️  AppImage test failed (may require GUI environment)${NC}"
    fi
else
    echo -e "${RED}❌ Failed to create AppImage${NC}"
    exit 1
fi

echo -e "${GREEN}🎉 Linux build completed successfully!${NC}"
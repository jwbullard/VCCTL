#!/bin/bash
"""
macOS application bundle and DMG build script for VCCTL
Creates a signed macOS application bundle and DMG installer
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
APP_NAME="VCCTL.app"
DMG_NAME="VCCTL-macOS.dmg"

echo -e "${BLUE}🍎 Building VCCTL macOS Package${NC}"
echo "Project root: $PROJECT_ROOT"

# Check if we're on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo -e "${RED}❌ This script must be run on macOS${NC}"
    exit 1
fi

# Create build directories
mkdir -p "$BUILD_DIR" "$DIST_DIR"

# Install build dependencies
echo -e "${YELLOW}📦 Installing build dependencies...${NC}"
pip install pyinstaller>=5.13.0 setuptools wheel

# Build standalone executable using PyInstaller
echo -e "${YELLOW}🔨 Building application bundle...${NC}"
cd "$PROJECT_ROOT"

# Clean previous builds
rm -rf "$DIST_DIR/$APP_NAME"

# Run PyInstaller with macOS bundle configuration
pyinstaller --clean --noconfirm vcctl.spec

# Check if app bundle was created
if [ ! -d "$DIST_DIR/$APP_NAME" ]; then
    echo -e "${RED}❌ Application bundle not found: $DIST_DIR/$APP_NAME${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Application bundle created: $DIST_DIR/$APP_NAME${NC}"

# Verify app bundle structure
echo -e "${YELLOW}🔍 Verifying app bundle structure...${NC}"
required_files=(
    "$DIST_DIR/$APP_NAME/Contents/MacOS/vcctl"
    "$DIST_DIR/$APP_NAME/Contents/Info.plist"
)

for file in "${required_files[@]}"; do
    if [ ! -e "$file" ]; then
        echo -e "${RED}❌ Missing required file: $file${NC}"
        exit 1
    fi
done

# Fix permissions
echo -e "${YELLOW}🔐 Setting proper permissions...${NC}"
chmod +x "$DIST_DIR/$APP_NAME/Contents/MacOS/vcctl"

# Copy additional resources
echo -e "${YELLOW}📁 Copying additional resources...${NC}"

# Copy icon if available
ICON_DIR="$PROJECT_ROOT/src/app/resources/icons"
if [ -f "$ICON_DIR/vcctl.icns" ]; then
    cp "$ICON_DIR/vcctl.icns" "$DIST_DIR/$APP_NAME/Contents/Resources/"
elif [ -f "$ICON_DIR/vcctl.png" ]; then
    # Convert PNG to ICNS if needed
    if command -v sips >/dev/null 2>&1; then
        mkdir -p "$DIST_DIR/$APP_NAME/Contents/Resources"
        sips -s format icns "$ICON_DIR/vcctl.png" --out "$DIST_DIR/$APP_NAME/Contents/Resources/vcctl.icns"
    fi
fi

# Update Info.plist with proper values
echo -e "${YELLOW}📝 Updating Info.plist...${NC}"
INFO_PLIST="$DIST_DIR/$APP_NAME/Contents/Info.plist"

# Backup original Info.plist
cp "$INFO_PLIST" "$INFO_PLIST.backup"

# Update Info.plist using PlistBuddy
/usr/libexec/PlistBuddy -c "Set :CFBundleName VCCTL" "$INFO_PLIST" 2>/dev/null || true
/usr/libexec/PlistBuddy -c "Set :CFBundleDisplayName 'Virtual Cement and Concrete Testing Laboratory'" "$INFO_PLIST" 2>/dev/null || true
/usr/libexec/PlistBuddy -c "Set :CFBundleIdentifier gov.nist.vcctl" "$INFO_PLIST" 2>/dev/null || true
/usr/libexec/PlistBuddy -c "Set :CFBundleVersion 1.0.0" "$INFO_PLIST" 2>/dev/null || true
/usr/libexec/PlistBuddy -c "Set :CFBundleShortVersionString 1.0.0" "$INFO_PLIST" 2>/dev/null || true
/usr/libexec/PlistBuddy -c "Set :LSMinimumSystemVersion 10.14" "$INFO_PLIST" 2>/dev/null || true
/usr/libexec/PlistBuddy -c "Set :LSApplicationCategoryType public.app-category.education" "$INFO_PLIST" 2>/dev/null || true
/usr/libexec/PlistBuddy -c "Set :NSHighResolutionCapable true" "$INFO_PLIST" 2>/dev/null || true
/usr/libexec/PlistBuddy -c "Set :NSRequiresAquaSystemAppearance false" "$INFO_PLIST" 2>/dev/null || true

# Add document types for VCCTL files
/usr/libexec/PlistBuddy -c "Add :CFBundleDocumentTypes array" "$INFO_PLIST" 2>/dev/null || true
/usr/libexec/PlistBuddy -c "Add :CFBundleDocumentTypes:0 dict" "$INFO_PLIST" 2>/dev/null || true
/usr/libexec/PlistBuddy -c "Add :CFBundleDocumentTypes:0:CFBundleTypeName string 'VCCTL Project'" "$INFO_PLIST" 2>/dev/null || true
/usr/libexec/PlistBuddy -c "Add :CFBundleDocumentTypes:0:CFBundleTypeExtensions array" "$INFO_PLIST" 2>/dev/null || true
/usr/libexec/PlistBuddy -c "Add :CFBundleDocumentTypes:0:CFBundleTypeExtensions:0 string vcctl" "$INFO_PLIST" 2>/dev/null || true
/usr/libexec/PlistBuddy -c "Add :CFBundleDocumentTypes:0:CFBundleTypeRole string Editor" "$INFO_PLIST" 2>/dev/null || true

# Code signing (if developer certificate is available)
echo -e "${YELLOW}🔒 Checking for code signing...${NC}"
SIGNING_IDENTITY=$(security find-identity -v -p codesigning | grep "Developer ID Application" | head -1 | grep -o '"[^"]*"' | tr -d '"' || echo "")

if [ -n "$SIGNING_IDENTITY" ]; then
    echo -e "${YELLOW}🔐 Signing application with: $SIGNING_IDENTITY${NC}"
    
    # Sign all binaries and libraries first
    find "$DIST_DIR/$APP_NAME" -type f \( -name "*.dylib" -o -name "*.so" -o -perm +111 \) -exec codesign --force --sign "$SIGNING_IDENTITY" {} \; 2>/dev/null || true
    
    # Sign the main application
    codesign --force --sign "$SIGNING_IDENTITY" --deep "$DIST_DIR/$APP_NAME" 2>/dev/null || {
        echo -e "${YELLOW}⚠️  Code signing failed, continuing without signature${NC}"
    }
    
    # Verify signature
    if codesign --verify --deep --strict "$DIST_DIR/$APP_NAME" 2>/dev/null; then
        echo -e "${GREEN}✅ Application signed successfully${NC}"
    else
        echo -e "${YELLOW}⚠️  Signature verification failed${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  No Developer ID certificate found, skipping code signing${NC}"
    echo -e "${YELLOW}   To enable signing, install a Developer ID Application certificate${NC}"
fi

# Test the application bundle
echo -e "${YELLOW}🧪 Testing application bundle...${NC}"
if "$DIST_DIR/$APP_NAME/Contents/MacOS/vcctl" --help >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Application bundle test passed${NC}"
else
    echo -e "${YELLOW}⚠️  Application bundle test failed (may require GUI environment)${NC}"
fi

# Create DMG installer
echo -e "${YELLOW}💿 Creating DMG installer...${NC}"

# Create DMG staging directory
DMG_STAGING="$BUILD_DIR/dmg_staging"
rm -rf "$DMG_STAGING"
mkdir -p "$DMG_STAGING"

# Copy app bundle to staging
cp -R "$DIST_DIR/$APP_NAME" "$DMG_STAGING/"

# Create Applications symlink
ln -sf /Applications "$DMG_STAGING/Applications"

# Create background image if available
BACKGROUND_DIR="$PROJECT_ROOT/src/app/resources/images"
if [ -f "$BACKGROUND_DIR/dmg_background.png" ]; then
    mkdir -p "$DMG_STAGING/.background"
    cp "$BACKGROUND_DIR/dmg_background.png" "$DMG_STAGING/.background/"
fi

# Create DS_Store for window layout (optional)
cat > "$DMG_STAGING/.DS_Store_template" << 'EOF'
# This would contain binary data for DMG window positioning
# For now, we'll rely on default hdiutil behavior
EOF

# Create temporary DMG
TEMP_DMG="$BUILD_DIR/temp.dmg"
rm -f "$TEMP_DMG"

# Calculate size needed (add 10MB buffer)
SIZE_MB=$(du -sm "$DMG_STAGING" | cut -f1)
SIZE_MB=$((SIZE_MB + 10))

hdiutil create -srcfolder "$DMG_STAGING" -volname "VCCTL" -fs HFS+ -fsargs "-c c=64,a=16,e=16" -format UDRW -size ${SIZE_MB}m "$TEMP_DMG"

# Mount the temporary DMG
MOUNT_DIR="/tmp/vcctl_dmg_mount"
mkdir -p "$MOUNT_DIR"
hdiutil attach "$TEMP_DMG" -noautoopen -quiet -mountpoint "$MOUNT_DIR"

# Configure DMG appearance
echo -e "${YELLOW}🎨 Configuring DMG appearance...${NC}"

# Set icon positions using AppleScript
osascript << EOF
tell application "Finder"
    tell disk "VCCTL"
        open
        set current view of container window to icon view
        set toolbar visible of container window to false
        set statusbar visible of container window to false
        set the bounds of container window to {400, 100, 900, 450}
        set viewOptions to the icon view options of container window
        set arrangement of viewOptions to not arranged
        set icon size of viewOptions to 72
        set position of item "VCCTL.app" of container window to {150, 175}
        set position of item "Applications" of container window to {350, 175}
        close
        open
        update without registering applications
        delay 2
        close
    end tell
end tell
EOF

# Unmount temporary DMG
hdiutil detach "$MOUNT_DIR" -quiet

# Convert to final compressed DMG
FINAL_DMG="$DIST_DIR/$DMG_NAME"
rm -f "$FINAL_DMG"

hdiutil convert "$TEMP_DMG" -format UDZO -imagekey zlib-level=9 -o "$FINAL_DMG"

# Clean up
rm -f "$TEMP_DMG"
rm -rf "$DMG_STAGING"

if [ -f "$FINAL_DMG" ]; then
    echo -e "${GREEN}✅ DMG installer created: $FINAL_DMG${NC}"
    
    # Display file size
    SIZE=$(du -h "$FINAL_DMG" | cut -f1)
    echo -e "${BLUE}📦 DMG size: $SIZE${NC}"
    
    # Test DMG
    echo -e "${YELLOW}🧪 Testing DMG...${NC}"
    if hdiutil verify "$FINAL_DMG" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ DMG verification passed${NC}"
    else
        echo -e "${YELLOW}⚠️  DMG verification failed${NC}"
    fi
else
    echo -e "${RED}❌ Failed to create DMG installer${NC}"
    exit 1
fi

# Create ZIP archive as alternative distribution
echo -e "${YELLOW}📦 Creating ZIP archive...${NC}"
ZIP_NAME="VCCTL-macOS.zip"
cd "$DIST_DIR"
rm -f "$ZIP_NAME"
zip -r -q "$ZIP_NAME" "$APP_NAME"

if [ -f "$ZIP_NAME" ]; then
    echo -e "${GREEN}✅ ZIP archive created: $ZIP_NAME${NC}"
    SIZE=$(du -h "$ZIP_NAME" | cut -f1)
    echo -e "${BLUE}📦 ZIP size: $SIZE${NC}"
fi

# Summary
echo -e "${GREEN}🎉 macOS build completed successfully!${NC}"
echo
echo -e "${BLUE}📦 Built packages:${NC}"
echo "  - Application bundle: $APP_NAME"
echo "  - DMG installer: $DMG_NAME"
if [ -f "$DIST_DIR/$ZIP_NAME" ]; then
    echo "  - ZIP archive: $ZIP_NAME"
fi

echo
echo -e "${BLUE}📋 Installation instructions:${NC}"
echo "  1. Mount the DMG file: $DMG_NAME"
echo "  2. Drag VCCTL.app to the Applications folder"
echo "  3. Launch VCCTL from Launchpad or Applications folder"

if [ -z "$SIGNING_IDENTITY" ]; then
    echo
    echo -e "${YELLOW}⚠️  Security Note:${NC}"
    echo "  The application is not code signed. Users may need to:"
    echo "  1. Right-click the app and select 'Open'"
    echo "  2. Click 'Open' when prompted about unidentified developer"
    echo "  3. Or disable Gatekeeper temporarily: sudo spctl --master-disable"
fi

cd "$PROJECT_ROOT"
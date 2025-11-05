# Creating macOS DMG Distribution Package

This document provides step-by-step instructions for creating a DMG (Disk Image) distribution package for VCCTL on macOS.

## Prerequisites

- macOS 10.14 or later
- PyInstaller installed (`pip install pyinstaller`)
- Git repository with latest changes pulled
- Optional: `create-dmg` tool for enhanced DMG creation

## Step 1: Pull Latest Changes

```bash
cd /path/to/VCCTL
git pull origin main
```

This ensures you have the latest code including the `edu.tamu.vcctl` bundle identifier.

## Step 2: Build macOS Application

```bash
# Build the VCCTL.app bundle using PyInstaller
python3 -m PyInstaller vcctl-macos.spec --clean --noconfirm
```

**Build Time:** Approximately 2-3 minutes

**Output Location:** `dist/VCCTL.app`

**Verify Build:**
```bash
ls -lh dist/VCCTL.app
# Should show a complete .app bundle

# Check bundle identifier
/usr/libexec/PlistBuddy -c "Print :CFBundleIdentifier" \
  dist/VCCTL.app/Contents/Info.plist
# Should output: edu.tamu.vcctl
```

## Step 3: Create DMG (Choose One Method)

### Method A: Using create-dmg Tool (Recommended)

The `create-dmg` tool creates professional-looking DMG files with custom backgrounds and drag-to-Applications shortcuts.

**Install create-dmg:**
```bash
brew install create-dmg
```

**Create DMG:**
```bash
create-dmg \
  --volname "VCCTL 10.0.0" \
  --window-pos 200 120 \
  --window-size 800 400 \
  --icon-size 100 \
  --icon "VCCTL.app" 200 190 \
  --hide-extension "VCCTL.app" \
  --app-drop-link 600 185 \
  "VCCTL-10.0.0-macOS-arm64.dmg" \
  "dist/VCCTL.app"
```

**Parameters Explained:**
- `--volname`: Name shown when DMG is mounted
- `--window-pos`: Position of Finder window when DMG opens
- `--window-size`: Size of Finder window
- `--icon-size`: Size of icons in Finder window
- `--icon`: Position of VCCTL.app icon
- `--hide-extension`: Hides .app extension in Finder
- `--app-drop-link`: Creates "Applications" folder shortcut at position

**Output:** `VCCTL-10.0.0-macOS-arm64.dmg` (~800-900 MB)

### Method B: Using hdiutil (Built into macOS)

The built-in `hdiutil` command creates a simple, functional DMG without custom styling.

```bash
hdiutil create -volname "VCCTL 10.0.0" \
  -srcfolder dist/VCCTL.app \
  -ov -format UDZO \
  VCCTL-10.0.0-macOS-arm64.dmg
```

**Parameters Explained:**
- `-volname`: Volume name shown when mounted
- `-srcfolder`: Source application bundle
- `-ov`: Overwrite existing file if present
- `-format UDZO`: Compressed read-only format (UDZO = zlib compression)

**Output:** `VCCTL-10.0.0-macOS-arm64.dmg` (~800-900 MB)

## Step 4: Test DMG

**Mount and Test:**
```bash
# Mount the DMG
open VCCTL-10.0.0-macOS-arm64.dmg

# DMG should open in Finder
# Drag VCCTL.app to Applications (or desktop for testing)
# Launch VCCTL from Applications

# Verify it runs correctly
# Test key features:
# - Materials panel loads
# - Mix design works
# - Microstructure generation works
# - 3D visualization works
```

**Unmount DMG:**
```bash
hdiutil detach /Volumes/VCCTL\ 10.0.0
```

## Step 5: Verify DMG Properties

```bash
# Check DMG file size
ls -lh VCCTL-10.0.0-macOS-arm64.dmg

# Get detailed DMG information
hdiutil imageinfo VCCTL-10.0.0-macOS-arm64.dmg
```

## Architecture-Specific Builds

### Apple Silicon (ARM64)
The default build on Apple Silicon Macs creates ARM64 binaries.

**DMG Naming:** `VCCTL-10.0.0-macOS-arm64.dmg`

### Intel (x86_64)
If you need an Intel-compatible build:

```bash
# Build for Intel architecture
arch -x86_64 python3 -m PyInstaller vcctl-macos.spec --clean --noconfirm

# Create Intel DMG
hdiutil create -volname "VCCTL 10.0.0" \
  -srcfolder dist/VCCTL.app \
  -ov -format UDZO \
  VCCTL-10.0.0-macOS-x86_64.dmg
```

**DMG Naming:** `VCCTL-10.0.0-macOS-x86_64.dmg`

### Universal Binary (Both Architectures)
For maximum compatibility, create a universal binary:

```bash
# Build both architectures separately first
# Then use lipo to combine binaries
# (More complex - see Apple documentation)
```

## Code Signing and Notarization (Optional)

For distribution outside the App Store, you may want to sign and notarize the application to avoid Gatekeeper warnings.

**Requirements:**
- Apple Developer Program membership ($99/year)
- Developer ID Application certificate
- App-specific password for notarization

**Basic Signing:**
```bash
codesign --deep --force --verify --verbose \
  --sign "Developer ID Application: Your Name (TEAM_ID)" \
  dist/VCCTL.app
```

**Notarization:**
```bash
# Create DMG first, then notarize
xcrun notarytool submit VCCTL-10.0.0-macOS-arm64.dmg \
  --apple-id "your@email.com" \
  --team-id "TEAM_ID" \
  --password "app-specific-password" \
  --wait

# Staple notarization ticket to DMG
xcrun stapler staple VCCTL-10.0.0-macOS-arm64.dmg
```

**Note:** Code signing and notarization are optional for initial releases but recommended for wider distribution.

## Troubleshooting

### DMG Creation Fails
```bash
# Error: Resource busy
# Solution: Unmount any existing VCCTL volumes
hdiutil detach /Volumes/VCCTL\ 10.0.0

# Error: File exists
# Solution: Use -ov flag or delete existing DMG
rm VCCTL-10.0.0-macOS-arm64.dmg
```

### Application Won't Launch from DMG
```bash
# Check for quarantine attribute
xattr -l dist/VCCTL.app

# Remove quarantine if present
xattr -rd com.apple.quarantine dist/VCCTL.app

# Rebuild DMG
```

### Bundle Identifier Issues
```bash
# Verify correct bundle ID
/usr/libexec/PlistBuddy -c "Print :CFBundleIdentifier" \
  dist/VCCTL.app/Contents/Info.plist

# Should show: edu.tamu.vcctl
# If not, rebuild with: python3 -m PyInstaller vcctl-macos.spec --clean
```

## Distribution Checklist

- [ ] Latest code pulled from GitHub
- [ ] Application built with PyInstaller
- [ ] Bundle identifier verified (`edu.tamu.vcctl`)
- [ ] DMG created successfully
- [ ] DMG tested on clean macOS installation
- [ ] All core features verified working
- [ ] DMG file size is reasonable (~800-900 MB)
- [ ] DMG naming follows convention: `VCCTL-10.0.0-macOS-arm64.dmg`
- [ ] (Optional) Application signed with Developer ID
- [ ] (Optional) DMG notarized by Apple
- [ ] DMG ready for GitHub release upload

## GitHub Release Upload

Once DMG is created and tested:

```bash
# The DMG file is ready to upload to GitHub Releases
ls -lh VCCTL-10.0.0-macOS-arm64.dmg

# Upload via GitHub web interface:
# 1. Go to repository → Releases → Draft new release
# 2. Tag: v10.0.0
# 3. Upload VCCTL-10.0.0-macOS-arm64.dmg
# 4. Add release notes
# 5. Publish release
```

## Additional Resources

- [create-dmg GitHub](https://github.com/create-dmg/create-dmg)
- [Apple Code Signing Guide](https://developer.apple.com/documentation/security/code_signing_services)
- [Apple Notarization Guide](https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution)
- [PyInstaller macOS Documentation](https://pyinstaller.org/en/stable/operating-mode.html#macos)

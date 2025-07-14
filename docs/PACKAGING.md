# VCCTL Packaging and Distribution Guide

**Virtual Cement and Concrete Testing Laboratory**  
**Desktop Application Packaging Documentation**

---

## Table of Contents

1. [Overview](#overview)
2. [Build System](#build-system)
3. [Platform-Specific Packaging](#platform-specific-packaging)
4. [Continuous Integration](#continuous-integration)
5. [Distribution Channels](#distribution-channels)
6. [Quality Assurance](#quality-assurance)
7. [Troubleshooting](#troubleshooting)
8. [Developer Guide](#developer-guide)

---

## Overview

VCCTL uses a comprehensive packaging system to create distributable packages for Linux, Windows, and macOS platforms. The build system is designed to be reproducible, automated, and cross-platform compatible.

### Supported Package Formats

- **Linux**: AppImage (portable, self-contained)
- **Windows**: NSIS installer + portable ZIP
- **macOS**: DMG installer + ZIP bundle
- **Universal**: Python wheel + source distribution

### Key Features

- **Cross-platform builds** with platform-specific optimizations
- **Automated dependency bundling** for standalone packages
- **Code signing support** for macOS and Windows (when certificates available)
- **Continuous integration** with GitHub Actions
- **Quality assurance** with automated testing
- **Multiple distribution formats** per platform

---

## Build System

### Requirements

#### System Dependencies

**Linux:**
```bash
sudo apt-get install \
  libgtk-3-dev \
  libgirepository1.0-dev \
  pkg-config \
  gir1.2-gtk-3.0 \
  python3-gi \
  python3-gi-cairo
```

**macOS:**
```bash
brew install gtk+3 pygobject3 adwaita-icon-theme
```

**Windows:**
- Visual Studio Build Tools or Visual Studio Community
- GTK3 runtime environment
- NSIS (for installer creation)

#### Python Dependencies

```bash
pip install pyinstaller>=5.13.0 setuptools wheel
```

### Build Commands

#### Quick Build (Current Platform)

```bash
# Using Make
make build

# Using Python script
python scripts/build.py

# Platform-specific
scripts/build_linux.sh      # Linux
scripts/build_windows.bat   # Windows
scripts/build_macos.sh      # macOS
```

#### Clean Build

```bash
make clean build
```

#### Development Build

```bash
make dev-setup
make test
make build
```

---

## Platform-Specific Packaging

### Linux AppImage

The Linux build creates a portable AppImage that includes all dependencies.

#### Build Process

1. **PyInstaller Build**: Creates standalone Python executable
2. **AppDir Creation**: Structures files in AppImage format
3. **Dependency Bundling**: Includes GTK3 and Python libraries
4. **Desktop Integration**: Adds .desktop file and icon
5. **AppImage Generation**: Creates final .AppImage file

#### Output

```
dist/VCCTL-x86_64.AppImage
```

#### Usage

```bash
chmod +x VCCTL-x86_64.AppImage
./VCCTL-x86_64.AppImage
```

#### Features

- **Portable**: Runs on any Linux distribution
- **Self-contained**: No system dependencies required
- **Desktop integration**: Automatically registers file associations
- **Version independence**: Works across different Linux versions

### Windows Packages

The Windows build creates both an installer and portable package.

#### Installer (NSIS)

Professional installer with:
- Start Menu shortcuts
- Desktop shortcuts
- Add/Remove Programs integration
- Uninstaller creation
- Registry entries
- Administrative installation

#### Portable Package

ZIP archive containing:
- Standalone executable
- All dependencies
- Documentation
- Configuration files

#### Build Process

1. **PyInstaller Build**: Creates Windows executable
2. **Dependency Collection**: Bundles required DLLs
3. **NSIS Script Generation**: Creates installer script
4. **Installer Compilation**: Builds .exe installer
5. **ZIP Creation**: Creates portable package

#### Output

```
dist/VCCTL-Setup-x64.exe      # Installer
dist/VCCTL-Portable-x64.zip   # Portable
```

#### Code Signing

When a valid code signing certificate is available:
- Executable signing with timestamp
- Installer signing
- SmartScreen compatibility

### macOS Packages

The macOS build creates both a DMG installer and ZIP bundle.

#### Application Bundle

Standard macOS .app bundle with:
- Proper Info.plist configuration
- Icon integration
- Document type associations
- Retina display support
- Dark mode compatibility

#### DMG Installer

Professional DMG with:
- Custom background (optional)
- Application and Applications folder
- Drag-and-drop installation
- Volume customization

#### Build Process

1. **PyInstaller Build**: Creates macOS app bundle
2. **Bundle Configuration**: Updates Info.plist
3. **Code Signing**: Signs binaries and bundle
4. **DMG Creation**: Creates disk image
5. **Notarization**: Apple notarization (if certificates available)

#### Output

```
dist/VCCTL.app           # Application bundle
dist/VCCTL-macOS.dmg     # DMG installer
dist/VCCTL-macOS.zip     # ZIP bundle
```

#### Code Signing

When Developer ID certificates are available:
- Application signing
- Binary signing
- Notarization for Gatekeeper compatibility

---

## Continuous Integration

### GitHub Actions

Automated builds on:
- **Push** to main/develop branches
- **Pull requests** to main branch
- **Tag creation** (triggers releases)

### Build Matrix

| Platform | OS Version | Python | Architecture |
|----------|------------|--------|--------------|
| Linux    | Ubuntu 20.04 | 3.9  | x86_64      |
| Windows  | Latest     | 3.9    | x64         |
| macOS    | 12         | 3.9    | x86_64      |

### Workflow Steps

1. **Source Checkout**: Get latest code
2. **Environment Setup**: Install dependencies
3. **Testing**: Run test suite
4. **Building**: Create platform packages
5. **Artifact Upload**: Store build artifacts
6. **Release Creation**: Automatic releases for tags

### Configuration

```yaml
# .github/workflows/build.yml
name: Build and Package VCCTL
on:
  push:
    branches: [ main, develop ]
    tags: [ 'v*' ]
```

---

## Distribution Channels

### GitHub Releases

Primary distribution via GitHub Releases:
- Automatic release creation for version tags
- Multi-platform package distribution
- Release notes generation
- Asset management

### Package Managers

**Future support planned for:**
- **Linux**: APT repositories, Flatpak, Snap
- **Windows**: Chocolatey, winget
- **macOS**: Homebrew cask
- **Python**: PyPI (for library usage)

### Direct Download

Official website distribution:
- Platform detection
- Latest version downloads
- Installation instructions
- System requirements

---

## Quality Assurance

### Automated Testing

#### Unit Tests
```bash
pytest tests/unit/
```

#### Integration Tests
```bash
pytest tests/integration/
```

#### End-to-End Tests
```bash
pytest tests/e2e/
```

#### Package Testing
```bash
python scripts/test_installation.py dist/VCCTL-x86_64.AppImage
```

### Manual Testing

#### Installation Testing
- Clean system installation
- Upgrade testing
- Uninstallation verification
- Permission testing

#### Functionality Testing
- Basic application launch
- Core feature testing
- Performance verification
- Memory usage monitoring

#### Platform Testing
- Multiple OS versions
- Different hardware configurations
- Various user environments
- Accessibility compliance

### Test Environments

#### Docker Containers
```bash
# Ubuntu 18.04 test
docker run -it ubuntu:18.04 bash

# CentOS 7 test
docker run -it centos:7 bash
```

#### Virtual Machines
- Windows 10/11 clean installs
- macOS versions 10.14+
- Linux distributions

---

## Troubleshooting

### Common Build Issues

#### Linux

**Problem**: Missing GTK dependencies
```bash
# Solution
sudo apt-get install libgtk-3-dev libgirepository1.0-dev
```

**Problem**: AppImage creation fails
```bash
# Solution: Install AppImageTool
wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
chmod +x appimagetool-x86_64.AppImage
```

#### Windows

**Problem**: PyInstaller import errors
```bash
# Solution
pip install pywin32 pywin32-ctypes
```

**Problem**: NSIS not found
```bash
# Solution
choco install nsis
# Add to PATH: C:\Program Files (x86)\NSIS
```

#### macOS

**Problem**: GTK import errors
```bash
# Solution
brew install gtk+3 pygobject3
export PKG_CONFIG_PATH="/usr/local/lib/pkgconfig"
```

**Problem**: Code signing fails
```bash
# Solution: Check certificates
security find-identity -v -p codesigning
```

### Performance Issues

#### Large Package Size
- Remove unnecessary dependencies
- Use UPX compression
- Optimize asset inclusion

#### Slow Build Times
- Use build caching
- Parallel processing
- Incremental builds

### Runtime Issues

#### Missing Dependencies
- Update dependency bundling
- Check library compatibility
- Verify system requirements

#### Permission Problems
- Adjust file permissions
- Check security policies
- Update installation methods

---

## Developer Guide

### Setting Up Build Environment

#### Prerequisites
```bash
git clone https://github.com/nist/vcctl-gtk.git
cd vcctl-gtk
make dev-setup
```

#### Build Testing
```bash
make clean
make test
make build
```

### Adding New Platforms

#### 1. Create Build Script
```bash
scripts/build_newplatform.sh
```

#### 2. Update PyInstaller Spec
```python
# vcctl.spec
if sys.platform == 'newplatform':
    # Platform-specific configuration
```

#### 3. Add CI Configuration
```yaml
# .github/workflows/build.yml
build-newplatform:
  runs-on: newplatform-latest
```

#### 4. Update Documentation
- Installation instructions
- System requirements
- Troubleshooting guide

### Custom Packaging

#### Modifying PyInstaller Configuration
```python
# vcctl.spec
a = Analysis(
    ['src/main.py'],
    pathex=['custom/path'],
    datas=[('custom/data', 'data')],
    hiddenimports=['custom.module'],
)
```

#### Adding Custom Resources
```python
# Include custom icons
datas=[
    ('custom/icons/', 'icons/'),
    ('custom/themes/', 'themes/'),
]
```

#### Platform-Specific Customization
```bash
# Linux: Custom AppDir structure
mkdir -p build/VCCTL.AppDir/usr/share/custom

# Windows: Custom installer sections
echo "Custom installer logic" >> scripts/installer_custom.nsi

# macOS: Custom Info.plist entries
/usr/libexec/PlistBuddy -c "Add :CustomKey string CustomValue" Info.plist
```

### Release Process

#### 1. Version Bump
```bash
# Update version in setup.py, vcctl.spec, etc.
git tag v1.0.0
```

#### 2. Trigger Build
```bash
git push origin v1.0.0
```

#### 3. Verify Packages
```bash
# Download and test all platform packages
python scripts/test_installation.py dist/package
```

#### 4. Update Documentation
- Release notes
- Installation guides
- System requirements

### Advanced Configuration

#### Custom Build Variants
```bash
# Debug build
python scripts/build.py --debug

# Minimal build
python scripts/build.py --minimal

# Development build
python scripts/build.py --dev
```

#### Build Hooks
```python
# hooks/hook-custom.py
from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files('custom_package')
```

#### Cross-Compilation
```bash
# Build for different architectures
python scripts/build.py --arch arm64
python scripts/build.py --arch x86_64
```

---

**Document Version**: 1.0  
**Last Updated**: [Current Date]  
**Maintained by**: VCCTL Development Team, NIST Building and Fire Research Laboratory
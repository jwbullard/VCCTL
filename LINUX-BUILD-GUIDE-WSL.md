# Linux Build Guide for VCCTL Using WSL on Windows

## Overview

This guide provides complete step-by-step instructions for building Linux packages of VCCTL on Windows using WSL (Windows Subsystem for Linux). WSL allows you to compile native Linux binaries and create Linux distribution packages without needing a separate Linux computer.

**Key Advantage:** WSL provides a genuine Linux environment on Windows, producing identical executables to those built on native Linux systems.

---

## Table of Contents

1. [What is WSL?](#what-is-wsl)
2. [Prerequisites](#prerequisites)
3. [Installing WSL](#installing-wsl)
4. [Setting Up the Linux Environment](#setting-up-the-linux-environment)
5. [Installing Build Dependencies](#installing-build-dependencies)
6. [Accessing Your VCCTL Source Code](#accessing-your-vcctl-source-code)
7. [Compiling the C Executables](#compiling-the-c-executables)
8. [Building the Linux Python Package](#building-the-linux-python-package)
9. [Testing the Linux Build](#testing-the-linux-build)
10. [Creating Distribution Packages](#creating-distribution-packages)
11. [Troubleshooting](#troubleshooting)
12. [WSL vs Native Linux](#wsl-vs-native-linux)

---

## What is WSL?

**Windows Subsystem for Linux (WSL)** is a compatibility layer that allows you to run a genuine Linux kernel and Linux distributions directly on Windows 10/11.

### WSL Benefits for VCCTL:

- **Native Linux binaries** - Identical to Ubuntu/Debian compilation
- **Same build process** - Use standard Linux tools (GCC, apt, make)
- **No dual boot needed** - Run Linux alongside Windows
- **File system integration** - Access Windows files from Linux
- **Resource efficient** - Shares system resources with Windows

### WSL 1 vs WSL 2:

- **WSL 2 (Recommended)** - Full Linux kernel, faster file system performance
- **WSL 1** - Translation layer, better cross-OS file performance

This guide uses **WSL 2** as it provides the most authentic Linux experience.

---

## Prerequisites

### System Requirements

- **Operating System:**
  - Windows 11 (any version)
  - Windows 10 version 2004 or higher (Build 19041 or higher)
- **Architecture:** x64 or ARM64
- **Virtualization:** Enabled in BIOS/UEFI
- **Disk Space:** ~10 GB free space for Ubuntu and build tools
- **RAM:** 4 GB minimum (8 GB recommended)

### Check Windows Version

Open PowerShell and run:
```powershell
winver
```

Ensure you see Version 2004 or higher.

### Check Virtualization Status

Open Task Manager → Performance → CPU
Look for "Virtualization: Enabled"

If disabled, enable in BIOS (varies by manufacturer).

---

## Installing WSL

### Method 1: Automatic Install (Windows 11 or Windows 10 22H2+)

Open **PowerShell as Administrator** and run:

```powershell
wsl --install -d Ubuntu-22.04
```

This single command:
- Enables WSL feature
- Installs WSL 2
- Downloads Ubuntu 22.04
- Sets Ubuntu as default distribution

**Restart your computer when prompted.**

### Method 2: Manual Install (Older Windows 10)

**Step 1: Enable WSL Feature**
```powershell
# Run as Administrator
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
```

**Step 2: Enable Virtual Machine Platform**
```powershell
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
```

**Step 3: Restart Computer**

**Step 4: Download WSL 2 Kernel Update**
- Visit: https://aka.ms/wsl2kernel
- Download and install the update package

**Step 5: Set WSL 2 as Default**
```powershell
wsl --set-default-version 2
```

**Step 6: Install Ubuntu**
- Open Microsoft Store
- Search for "Ubuntu 22.04 LTS"
- Click "Get" to install

### Verify Installation

```powershell
wsl --list --verbose
```

Expected output:
```
  NAME            STATE           VERSION
* Ubuntu-22.04    Running         2
```

The `VERSION` column should show `2` (WSL 2).

---

## Setting Up the Linux Environment

### First Launch

1. Open "Ubuntu 22.04" from Start Menu
2. Wait for initial setup (1-2 minutes)
3. Create a Linux username (can be different from Windows username)
4. Create a Linux password (will be needed for `sudo` commands)

**Important:** This username and password are **only for Linux**, separate from Windows.

### Update Package Database

```bash
sudo apt update
sudo apt upgrade -y
```

This ensures all packages are current.

### Configure Git (Optional but Recommended)

If you plan to commit changes from WSL:

```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

---

## Installing Build Dependencies

### Step 1: Install Core Build Tools

```bash
sudo apt install -y build-essential cmake pkg-config
```

**Packages installed:**
- `build-essential` - Meta-package including GCC, G++, make, libc-dev
- `cmake` - Build system generator (version 3.22+)
- `pkg-config` - Library configuration helper

### Step 2: Install Required Libraries

```bash
sudo apt install -y libpng-dev zlib1g-dev
```

**Libraries installed:**
- `libpng-dev` - PNG image library headers and development files
- `zlib1g-dev` - Compression library headers

### Step 3: Install Python and GTK Dependencies

```bash
sudo apt install -y python3 python3-pip python3-venv \
                    python3-gi python3-gi-cairo gir1.2-gtk-3.0 \
                    libgirepository1.0-dev libcairo2-dev
```

**Packages installed:**
- `python3` - Python 3.10+ interpreter
- `python3-pip` - Python package installer
- `python3-venv` - Virtual environment support
- `python3-gi` - Python GObject Introspection bindings
- `gir1.2-gtk-3.0` - GTK 3 typelib files
- `libgirepository1.0-dev` - GObject introspection development files
- `libcairo2-dev` - Cairo graphics library development files

### Step 4: Verify Installation

```bash
gcc --version          # Should show GCC 11.x or newer
cmake --version        # Should show CMake 3.22 or newer
python3 --version      # Should show Python 3.10 or newer
pkg-config --version   # Should show 0.29 or newer
```

---

## Accessing Your VCCTL Source Code

WSL can access Windows files through the `/mnt` directory.

### Understanding Path Mapping

| Windows Path | WSL Path |
|-------------|----------|
| `C:\Users\jwbullard\Desktop\foo\VCCTL` | `/mnt/c/Users/jwbullard/Desktop/foo/VCCTL` |
| `D:\Projects\VCCTL` | `/mnt/d/Projects/VCCTL` |

### Navigate to VCCTL Directory

```bash
cd /mnt/c/Users/YOUR_USERNAME/Desktop/foo/VCCTL
```

Replace `YOUR_USERNAME` with your Windows username.

### Verify Access

```bash
ls -la
```

You should see all VCCTL project files:
```
backend/
src/
vcctl.spec
README.md
...
```

### Performance Tip: Copy to WSL Filesystem (Optional)

For **faster build times**, copy VCCTL to the native Linux filesystem:

```bash
# Create projects directory in Linux home
mkdir -p ~/projects

# Copy VCCTL to Linux filesystem
cp -r /mnt/c/Users/YOUR_USERNAME/Desktop/foo/VCCTL ~/projects/

# Work from Linux filesystem
cd ~/projects/VCCTL
```

**Performance difference:**
- **Windows filesystem** (`/mnt/c/...`): Slower due to translation layer
- **Linux filesystem** (`~/projects/...`): Native speed (2-3x faster builds)

**Trade-off:** Changes in `~/projects/VCCTL` won't appear in Windows File Explorer automatically.

**Recommendation for VCCTL:**
- **Development:** Keep code on Windows (`/mnt/c/...`) for easy editing in Windows IDEs
- **Building:** Work from Windows path, accept slightly slower build time
- **OR:** Copy to Linux filesystem only for final package builds

---

## Compiling the C Executables

### Step 1: Navigate to Backend Directory

```bash
cd /mnt/c/Users/YOUR_USERNAME/Desktop/foo/VCCTL/backend
```

Or if you copied to Linux filesystem:
```bash
cd ~/projects/VCCTL/backend
```

### Step 2: Create Build Directory

```bash
mkdir -p build-linux
cd build-linux
```

### Step 3: Configure with CMake

```bash
cmake ..
```

**Expected output:**
```
-- The C compiler identification is GNU 11.4.0
-- The CXX compiler identification is GNU 11.4.0
-- Detecting C compiler ABI info - done
-- Check for working C compiler: /usr/bin/cc - skipped
-- Detecting C compile features - done
-- Found ZLIB: /usr/lib/x86_64-linux-gnu/libz.so (found version "1.2.11")
-- Found PNG: /usr/lib/x86_64-linux-gnu/libpng.so (found version "1.6.37")
Found MATH_LIB: [/usr/lib/x86_64-linux-gnu/libm.so]
-- Configuring done (0.4s)
-- Generating done (0.1s)
-- Build files have been written to: /mnt/c/Users/YOUR_USERNAME/Desktop/foo/VCCTL/backend/build-linux
```

**Note:** No special CMake flags needed for Linux! Standard build process works.

### Step 4: Compile All Executables

```bash
make -j$(nproc)
```

**Explanation:**
- `make` - Build system
- `-j$(nproc)` - Use all available CPU cores for parallel compilation

**Build progress:**
```
[  1%] Building C object src/vcctllib/CMakeFiles/vcctl.dir/breakflocs.c.o
[  2%] Building C object src/vcctllib/CMakeFiles/vcctl.dir/calcporedist3d.c.o
...
[ 28%] Built target vcctl
[ 31%] Built target aggvrml
...
[100%] Built target disrealnew
```

**Build time:** 1-2 minutes with parallel compilation on modern hardware.

### Step 5: Verify Linux Executables

```bash
ls -lh *.out 2>/dev/null || ls -lh * | grep -E "^-rwx"
```

You should see 26 Linux executables (no `.exe` extension):

```
-rwxr-xr-x 1 user user  89K Oct 15 12:00 aggvrml
-rwxr-xr-x 1 user user  78K Oct 15 12:00 apstats
-rwxr-xr-x 1 user user  84K Oct 15 12:00 chlorattack3d
-rwxr-xr-x 1 user user 156K Oct 15 12:00 disrealnew
-rwxr-xr-x 1 user user  73K Oct 15 12:00 distfapart
-rwxr-xr-x 1 user user  72K Oct 15 12:00 distfarand
-rwxr-xr-x 1 user user  81K Oct 15 12:00 dryout
-rwxr-xr-x 1 user user 121K Oct 15 12:00 elastic
-rwxr-xr-x 1 user user 102K Oct 15 12:00 genaggpack
-rwxr-xr-x 1 user user 142K Oct 15 12:00 genmic
...
```

**Note:** Linux binaries are typically smaller than Windows MinGW executables (no extra DLL dependencies).

### Step 6: Test a Simple Executable

```bash
./stat3d --help
```

Expected output:
```
Usage: stat3d [-h,--help] [-q,--quiet | -s,--silent]
      -j,--json progress.json -w,--workdir working_directory
...
```

### Step 7: Copy to Standard Location

```bash
# Create bin-linux directory if it doesn't exist
mkdir -p ../bin-linux

# Copy all executables
cp aggvrml apstats chlorattack3d disrealnew distfapart distfarand \
   dryout elastic genaggpack genmic hydmovie image100 leach3d \
   measagg oneimage onepimage perc3d perc3d-leach poredist3d \
   rand3d stat3d totsurf sulfattack3d transport \
   thames2vcctl thames2vcctlcorr ../bin-linux/
```

Or simply:
```bash
cp [a-z]* ../bin-linux/  # Copy all executables
```

---

## Building the Linux Python Package

### Step 1: Install Python Dependencies

Navigate to VCCTL root directory:

```bash
cd /mnt/c/Users/YOUR_USERNAME/Desktop/foo/VCCTL
```

Create and activate a virtual environment (recommended):

```bash
python3 -m venv venv-linux
source venv-linux/bin/activate
```

Install required packages:

```bash
pip install --upgrade pip
pip install PyInstaller sqlalchemy pandas numpy matplotlib pillow pyyaml pydantic reportlab openpyxl
```

**If pyvista is available for Linux:**
```bash
pip install pyvista
```

### Step 2: Update vcctl.spec for Linux

The `vcctl.spec` file should detect the platform automatically. Verify it contains:

```python
import sys

# Platform-specific binaries
if sys.platform == 'darwin':
    platform_binaries = [
        ('backend/bin/genmic', 'backend/bin/'),
        # ... macOS executables
    ]
elif sys.platform == 'win32':
    platform_binaries = [
        ('backend/bin-windows/genmic.exe', 'backend/bin/'),
        # ... Windows executables
    ]
else:  # Linux
    platform_binaries = [
        ('backend/bin-linux/genmic', 'backend/bin/'),
        ('backend/bin-linux/disrealnew', 'backend/bin/'),
        ('backend/bin-linux/elastic', 'backend/bin/'),
        ('backend/bin-linux/genaggpack', 'backend/bin/'),
        ('backend/bin-linux/perc3d', 'backend/bin/'),
        ('backend/bin-linux/stat3d', 'backend/bin/'),
        ('backend/bin-linux/oneimage', 'backend/bin/'),
        # ... all 26 Linux executables
    ]
```

### Step 3: Build Linux Package with PyInstaller

```bash
pyinstaller vcctl.spec
```

**Build output:**
```
INFO: Building Analysis because Analysis-00.toc is non existent
INFO: Running Analysis Analysis-00.toc
...
INFO: Building EXE from EXE-00.toc completed successfully.
INFO: Building COLLECT COLLECT-00.toc completed successfully.
```

**Result:** Linux application bundle at `dist/VCCTL/`

### Step 4: Verify Package Contents

```bash
ls -lh dist/VCCTL/
```

Expected contents:
```
drwxr-xr-x 1 user user   512 Oct 15 12:10 _internal/
-rwxr-xr-x 1 user user   15M Oct 15 12:10 VCCTL
```

The `VCCTL` file (no extension) is the Linux executable.

Check that C executables are included:
```bash
ls -lh dist/VCCTL/_internal/backend/bin/
```

Should show all 26 Linux executables.

---

## Testing the Linux Build

### Step 1: Run the Application

```bash
cd dist/VCCTL
./VCCTL
```

**Note:** WSL requires X server for GUI applications.

### Option A: Install X Server on Windows

**Install VcXsrv (Recommended):**
1. Download from: https://sourceforge.net/projects/vcxsrv/
2. Install with default settings
3. Launch "XLaunch" from Start Menu
4. Choose "Multiple windows" → "Start no client" → "Disable access control"

**Configure WSL to use X server:**
```bash
# Add to ~/.bashrc
echo 'export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk "{print \$2}"):0' >> ~/.bashrc
source ~/.bashrc
```

### Option B: Headless Testing

Test without GUI (for command-line operations):

```bash
# Test database access
python3 << EOF
from app.database.database_service import DatabaseService
db = DatabaseService()
print("Database initialized successfully")
EOF
```

### Step 2: Test C Executable Integration

Create a test operation to verify Python can call C executables:

```bash
# From dist/VCCTL directory
mkdir -p test_operations
cd test_operations

# Test genmic help
../_internal/backend/bin/genmic --help
```

Expected: Help message displays without errors.

---

## Creating Distribution Packages

### Option 1: AppImage (Recommended)

**AppImage** is a universal Linux package format that runs on all distributions.

**Install appimagetool:**
```bash
wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
chmod +x appimagetool-x86_64.AppImage
```

**Create AppImage directory structure:**
```bash
mkdir -p VCCTL.AppDir/usr/bin
mkdir -p VCCTL.AppDir/usr/lib
mkdir -p VCCTL.AppDir/usr/share/applications
mkdir -p VCCTL.AppDir/usr/share/icons

# Copy VCCTL files
cp -r dist/VCCTL/* VCCTL.AppDir/usr/bin/

# Create desktop entry
cat > VCCTL.AppDir/usr/share/applications/vcctl.desktop << 'EOF'
[Desktop Entry]
Type=Application
Name=VCCTL
Comment=Virtual Cement and Concrete Testing Laboratory
Exec=VCCTL
Icon=vcctl
Categories=Science;Engineering;
Terminal=false
EOF

# Copy icon (if you have one)
# cp icons/vcctl.png VCCTL.AppDir/usr/share/icons/vcctl.png

# Create AppRun script
cat > VCCTL.AppDir/AppRun << 'EOF'
#!/bin/bash
SELF=$(readlink -f "$0")
HERE=${SELF%/*}
export PATH="${HERE}/usr/bin:${PATH}"
export LD_LIBRARY_PATH="${HERE}/usr/lib:${LD_LIBRARY_PATH}"
exec "${HERE}/usr/bin/VCCTL" "$@"
EOF

chmod +x VCCTL.AppDir/AppRun

# Build AppImage
./appimagetool-x86_64.AppImage VCCTL.AppDir VCCTL-10.0.0-x86_64.AppImage
```

**Result:** `VCCTL-10.0.0-x86_64.AppImage` - Single file that runs on any Linux distribution.

### Option 2: Tarball Distribution

Simple compressed archive:

```bash
cd dist
tar -czf VCCTL-10.0.0-linux-x86_64.tar.gz VCCTL/

# Optional: Create installation script
cat > install.sh << 'EOF'
#!/bin/bash
tar -xzf VCCTL-10.0.0-linux-x86_64.tar.gz -C /opt/
ln -s /opt/VCCTL/VCCTL /usr/local/bin/vcctl
echo "VCCTL installed to /opt/VCCTL"
echo "Run with: vcctl"
EOF

chmod +x install.sh
```

**Result:** `VCCTL-10.0.0-linux-x86_64.tar.gz` + installation script

### Option 3: Debian Package (.deb)

For Ubuntu/Debian-based distributions:

**Install packaging tools:**
```bash
sudo apt install -y debhelper dh-make
```

**Create package structure:**
```bash
mkdir -p vcctl-10.0.0/DEBIAN
mkdir -p vcctl-10.0.0/opt/vcctl
mkdir -p vcctl-10.0.0/usr/bin

# Copy files
cp -r dist/VCCTL/* vcctl-10.0.0/opt/vcctl/

# Create symlink
ln -s /opt/vcctl/VCCTL vcctl-10.0.0/usr/bin/vcctl

# Create control file
cat > vcctl-10.0.0/DEBIAN/control << EOF
Package: vcctl
Version: 10.0.0
Section: science
Priority: optional
Architecture: amd64
Depends: python3 (>= 3.10), libgtk-3-0, libpng16-16, zlib1g
Maintainer: VCCTL Team <vcctl@example.com>
Description: Virtual Cement and Concrete Testing Laboratory
 VCCTL is a comprehensive software system for modeling cement
 microstructure development and properties.
EOF

# Build package
dpkg-deb --build vcctl-10.0.0
```

**Result:** `vcctl-10.0.0.deb`

**Install with:**
```bash
sudo dpkg -i vcctl-10.0.0.deb
```

### Option 4: Snap Package

Universal Linux package with automatic updates:

**Install snapcraft:**
```bash
sudo apt install -y snapd snapcraft
```

**Create snapcraft.yaml:**
```bash
mkdir snap
cat > snap/snapcraft.yaml << 'EOF'
name: vcctl
version: '10.0.0'
summary: Virtual Cement and Concrete Testing Laboratory
description: |
  VCCTL is a comprehensive software system for modeling cement
  microstructure development and properties.

base: core22
confinement: strict
grade: stable

apps:
  vcctl:
    command: usr/bin/VCCTL
    plugs:
      - home
      - desktop
      - desktop-legacy
      - wayland
      - x11

parts:
  vcctl:
    plugin: dump
    source: dist/VCCTL
    organize:
      '*': usr/bin/
EOF

# Build snap
snapcraft
```

**Result:** `vcctl_10.0.0_amd64.snap`

---

## Troubleshooting

### Problem: "WSL 2 requires an update to its kernel component"

**Solution:**
Download and install: https://aka.ms/wsl2kernel

### Problem: "Cannot connect to X server"

**Cause:** No X server running on Windows or DISPLAY not set.

**Solution:**
1. Install VcXsrv on Windows
2. Launch XLaunch
3. In WSL:
   ```bash
   export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):0
   ```

### Problem: "Permission denied" when accessing /mnt/c/...

**Cause:** File permissions issue between Windows and WSL.

**Solution:**
```bash
# Add to /etc/wsl.conf
sudo tee /etc/wsl.conf << EOF
[automount]
options = "metadata,umask=22,fmask=11"
EOF

# Restart WSL
wsl --shutdown
# Open Ubuntu again
```

### Problem: Build is very slow from /mnt/c/...

**Cause:** Cross-filesystem operations are slower.

**Solution:**
Copy project to Linux filesystem:
```bash
cp -r /mnt/c/Users/YOUR_USERNAME/Desktop/foo/VCCTL ~/projects/
cd ~/projects/VCCTL
# Build from here
```

### Problem: "ImportError: No module named 'gi'"

**Cause:** PyGObject not installed.

**Solution:**
```bash
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0
```

### Problem: "libpng.so.16: cannot open shared object file"

**Cause:** Runtime library not found.

**Solution:**
```bash
sudo apt install libpng16-16 zlib1g
```

### Problem: Executables work in build directory but fail in package

**Cause:** Missing dynamic library dependencies.

**Solution:**
Check dependencies:
```bash
ldd dist/VCCTL/_internal/backend/bin/genmic
```

Missing libraries should be bundled by PyInstaller. If not, add to `vcctl.spec`:
```python
binaries=[
    ('/usr/lib/x86_64-linux-gnu/libpng16.so.16', '.'),
    # ... other libraries
]
```

---

## WSL vs Native Linux

### When WSL is Sufficient:

✅ Building packages for Ubuntu/Debian
✅ Testing on x86_64 architecture
✅ Development and debugging
✅ Creating AppImages or tarballs

### When Native Linux is Needed:

❌ Building for specific distributions (Fedora, Arch, SUSE)
❌ Testing on ARM64 architecture
❌ Creating distribution-specific packages (.rpm for Fedora)
❌ Testing hardware-specific features
❌ Final validation before release

### Hybrid Workflow (Recommended):

1. **Develop on macOS/Windows** - Main development environment
2. **Build Linux packages in WSL** - Quick Linux builds
3. **Final testing on native Linux VM** - Validation before release

This gives you the convenience of WSL with the assurance of native testing.

---

## Performance Comparison

### Build Times (26 C executables + PyInstaller package):

| Environment | Location | Time | Notes |
|------------|----------|------|-------|
| WSL → Windows FS | `/mnt/c/...` | ~3-4 min | Slower due to FS translation |
| WSL → Linux FS | `~/projects/...` | ~1-2 min | Native speed |
| Native Linux | Any location | ~1-2 min | Baseline performance |
| MinGW (Windows) | Windows FS | ~3-4 min | Similar to WSL on Windows FS |

**Recommendation:** For occasional Linux builds, working from `/mnt/c/...` is fine. For frequent builds, copy to Linux filesystem.

---

## Best Practices

### 1. Keep Source on Windows

**Advantages:**
- Easy editing in Windows IDEs (VS Code, PyCharm)
- Integrated with Windows File Explorer
- Accessible from both Windows and WSL

**Location:** `/mnt/c/Users/YOUR_USERNAME/Desktop/foo/VCCTL`

### 2. Build Artifacts on Linux FS

**Create output directory in Linux:**
```bash
mkdir -p ~/vcctl-builds
```

**Build there:**
```bash
cd /mnt/c/Users/YOUR_USERNAME/Desktop/foo/VCCTL
pyinstaller vcctl.spec --distpath ~/vcctl-builds/dist --workpath ~/vcctl-builds/build
```

**Result:** Fast builds, source stays on Windows.

### 3. Automated Build Script

Create `build-linux.sh` in VCCTL root:

```bash
#!/bin/bash
set -e

echo "Building VCCTL for Linux..."

# Build C executables
cd backend
rm -rf build-linux
mkdir build-linux
cd build-linux
cmake ..
make -j$(nproc)
cp [a-z]* ../bin-linux/
cd ../..

# Build Python package
pyinstaller vcctl.spec

echo "Build complete: dist/VCCTL/VCCTL"
```

**Make executable:**
```bash
chmod +x build-linux.sh
```

**Run from WSL:**
```bash
./build-linux.sh
```

---

## Integration with Multi-Platform Workflow

### Complete VCCTL Build Matrix:

| Platform | Environment | Output | Build Guide |
|----------|------------|--------|-------------|
| macOS (ARM64) | Native macOS | VCCTL.app | macOS packaging docs |
| Windows (x64) | MSYS2 MinGW | VCCTL.exe | WINDOWS-BUILD-GUIDE.md |
| Linux (x64) | WSL Ubuntu | VCCTL binary | LINUX-BUILD-GUIDE-WSL.md (this guide) |

### Unified vcctl.spec

Your `vcctl.spec` should handle all three platforms:

```python
import sys
from pathlib import Path

# Detect platform
IS_MACOS = sys.platform == 'darwin'
IS_WINDOWS = sys.platform == 'win32'
IS_LINUX = sys.platform.startswith('linux')

# Platform-specific configuration
if IS_MACOS:
    platform_binaries = [
        ('backend/bin/genmic', 'backend/bin/'),
        # ... 7 macOS executables
    ]
    icon = 'icons/vcctl.icns'
elif IS_WINDOWS:
    platform_binaries = [
        ('backend/bin-windows/genmic.exe', 'backend/bin/'),
        # ... 26 Windows executables
    ]
    icon = 'icons/vcctl.ico'
else:  # Linux
    platform_binaries = [
        ('backend/bin-linux/genmic', 'backend/bin/'),
        # ... 26 Linux executables
    ]
    icon = 'icons/vcctl.png'

# Rest of spec file...
```

---

## Frequently Asked Questions

### Q: Can I build Windows packages from WSL?

**A:** No. WSL builds Linux binaries only. For Windows packages, use MinGW on Windows or cross-compilation (complex).

### Q: Can I run the Linux VCCTL GUI from WSL?

**A:** Yes, but requires X server (VcXsrv) on Windows. Works but adds complexity. Better for testing headless operations.

### Q: Should I install Ubuntu 20.04 or 22.04?

**A:** Use **Ubuntu 22.04 LTS** (recommended) - Newer libraries, supported until 2027.

### Q: Can I use WSL 1 instead of WSL 2?

**A:** Yes, but WSL 2 is faster and more compatible. Highly recommend WSL 2.

### Q: How do I transfer the Linux package to a real Linux computer?

**A:**
1. Package is in `/mnt/c/Users/YOUR_USERNAME/Desktop/foo/VCCTL/dist/`
2. Accessible from Windows File Explorer
3. Copy via USB, network share, or cloud storage

### Q: Do I need to rebuild for different Linux distributions?

**A:**
- **AppImage** - Runs on all distributions (recommended)
- **.deb** - Ubuntu/Debian only
- **Tarball** - Universal but no package management
- **Snap** - Universal with automatic updates

### Q: Can WSL access my GPU for visualization?

**A:** WSL 2 supports GPU acceleration (WSLg), but setup is complex. For VCCTL 3D visualization, test on native Linux.

---

## Additional Resources

### WSL Documentation
- Official docs: https://learn.microsoft.com/en-us/windows/wsl/
- WSL 2 setup: https://learn.microsoft.com/en-us/windows/wsl/install
- GUI apps: https://learn.microsoft.com/en-us/windows/wsl/tutorials/gui-apps

### Linux Packaging
- AppImage: https://appimage.org/
- Snap: https://snapcraft.io/
- Debian packaging: https://www.debian.org/doc/manuals/maint-guide/

### X Server for Windows
- VcXsrv: https://sourceforge.net/projects/vcxsrv/
- Xming: http://www.straightrunning.com/XmingNotes/
- Windows 11 WSLg: Built-in (no extra software needed)

### VCCTL Project
- GitHub: https://github.com/jwbullard/VCCTL
- Issues: https://github.com/jwbullard/VCCTL/issues

---

## Revision History

| Date | Version | Changes |
|------|---------|---------|
| 2025-10-15 | 1.0 | Initial version - WSL build instructions for Linux |

---

## License

This documentation is part of the VCCTL project. See the main project LICENSE file for details.

---

**Document prepared by:** VCCTL Development Team
**Last updated:** October 15, 2025
**For:** VCCTL Version 10.0.0 and later

**Platform:** WSL 2 on Windows 10/11 → Ubuntu 22.04 LTS → Linux x86_64 packages

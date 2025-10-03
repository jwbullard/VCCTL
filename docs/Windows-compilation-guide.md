# Windows Compilation Guide - VCCTL C Executables

## Overview

This guide explains how to compile the VCCTL C executables on Windows for packaging with PyInstaller. The executables are required for:
- `genmic` - Microstructure generation
- `disrealnew` - Hydration simulation
- `elastic` - Elastic moduli calculations
- `genaggpack` - Aggregate packing
- `perc3d` - Connectivity/percolation analysis
- `stat3d` - Microstructure statistics
- `oneimage` - Image processing
- ...and 15+ additional utilities

---

## Prerequisites

### Required Software

1. **CMake** (version 3.10 or higher)
   - Download from: https://cmake.org/download/
   - Install and add to PATH during installation

2. **C Compiler** - Choose ONE option:

   **Option A: Visual Studio (Recommended)**
   - Download: Visual Studio 2022 Community Edition (free)
   - URL: https://visualstudio.microsoft.com/downloads/
   - During installation, select "Desktop development with C++"
   - Includes MSVC compiler

   **Option B: MinGW-w64**
   - Download: https://www.mingw-w64.org/
   - Or use MSYS2: https://www.msys2.org/
   - Simpler but may have compatibility issues

3. **Git** (to transfer files)
   - Download from: https://git-scm.com/download/win
   - Or use USB drive/network share to transfer `backend/` folder

---

## Step 1: Transfer Files to Windows

### Method A: Git Clone (Recommended)
```powershell
git clone <your-repo-url>
cd vcctl-gtk/backend
```

### Method B: Direct Copy
Copy only the `backend/` folder from your macOS machine to Windows:
```
backend/
├── CMakeLists.txt
├── src/
│   ├── genmic.c
│   ├── disrealnew.c
│   ├── elastic.c
│   ├── include/
│   ├── vcctllib/
│   └── ...
├── include/
└── lib/
```

---

## Step 2: Build Dependencies

The project requires:
- **libpng** - PNG image library
- **zlib** - Compression library
- **libm** - Math library (included with compiler)

### Option 1: Use vcpkg (Easiest)

```powershell
# Install vcpkg
git clone https://github.com/Microsoft/vcpkg.git
cd vcpkg
.\bootstrap-vcpkg.bat

# Install dependencies
.\vcpkg install libpng:x64-windows
.\vcpkg install zlib:x64-windows

# Integrate with CMake
.\vcpkg integrate install
```

### Option 2: Manual Build (Advanced)

If you prefer to build from source, follow the libpng and zlib documentation.

---

## Step 3: Configure CMake

Open PowerShell or Command Prompt in the `backend/` directory:

### Using Visual Studio (MSVC):
```powershell
mkdir build-windows
cd build-windows

# Configure with vcpkg toolchain (if using vcpkg)
cmake .. -DCMAKE_TOOLCHAIN_FILE=C:/path/to/vcpkg/scripts/buildsystems/vcpkg.cmake

# Or without vcpkg (if libs are in system paths)
cmake ..
```

### Using MinGW:
```powershell
mkdir build-windows
cd build-windows
cmake .. -G "MinGW Makefiles"
```

---

## Step 4: Build Executables

### Using Visual Studio:
```powershell
# Build all executables in Release mode
cmake --build . --config Release

# Executables will be in: build-windows/Release/*.exe
```

### Using MinGW:
```powershell
# Build all executables
cmake --build .

# Executables will be in: build-windows/*.exe
```

---

## Step 5: Verify Build

Check that all required executables were built:

```powershell
dir Release\*.exe  # For MSVC
# Or
dir *.exe  # For MinGW
```

You should see:
- `genmic.exe` ✓
- `disrealnew.exe` ✓
- `elastic.exe` ✓
- `genaggpack.exe` ✓
- `perc3d.exe` ✓
- `stat3d.exe` ✓
- `oneimage.exe` ✓
- And 15+ other executables

---

## Step 6: Test Executables

Test that the executables run:

```powershell
.\Release\genmic.exe --version  # Should show version or usage
.\Release\elastic.exe --help    # Should show help message
```

---

## Step 7: Copy to PyInstaller Backend Folder

Create a `backend/bin-windows/` folder in your project and copy all `.exe` files:

```powershell
# Create directory
New-Item -ItemType Directory -Force -Path ..\..\backend\bin-windows

# Copy all executables
Copy-Item Release\*.exe ..\..\backend\bin-windows\
# Or for MinGW:
Copy-Item *.exe ..\..\backend\bin-windows\
```

---

## Step 8: Transfer Back to macOS

### Method A: Git Commit
```powershell
git add backend/bin-windows/*.exe
git commit -m "Add Windows compiled executables"
git push
```

Then on macOS:
```bash
git pull
```

### Method B: Direct Copy
Copy `backend/bin-windows/` folder back to your macOS machine via:
- Network share
- USB drive
- Cloud storage (Dropbox, OneDrive, etc.)

---

## Step 9: Update PyInstaller Spec for Windows

On macOS, you'll need to update `vcctl.spec` to include Windows executables conditionally:

```python
import sys

# Platform-specific binaries
if sys.platform == 'darwin':
    platform_binaries = [
        ('backend/bin/genmic', 'backend/bin/'),
        ('backend/bin/disrealnew', 'backend/bin/'),
        # ... macOS executables
    ]
elif sys.platform == 'win32':
    platform_binaries = [
        ('backend/bin-windows/genmic.exe', 'backend/bin/'),
        ('backend/bin-windows/disrealnew.exe', 'backend/bin/'),
        # ... Windows executables
    ]
elif sys.platform == 'linux':
    platform_binaries = [
        ('backend/bin-linux/genmic', 'backend/bin/'),
        # ... Linux executables
    ]
else:
    platform_binaries = []

# Analysis configuration
a = Analysis(
    ['src/main.py'],
    binaries=platform_binaries,
    # ... rest of config
)
```

---

## Troubleshooting

### CMake can't find libraries
**Problem:** `FATAL_ERROR "Did not find lib libpng"`

**Solution:**
- If using vcpkg: Ensure you specified `-DCMAKE_TOOLCHAIN_FILE` correctly
- Check that vcpkg installed correctly: `.\vcpkg list`
- Try: `cmake .. -DCMAKE_PREFIX_PATH="C:/path/to/vcpkg/installed/x64-windows"`

### Compiler not found
**Problem:** `No CMAKE_C_COMPILER could be found`

**Solution:**
- For MSVC: Run CMake from "Developer Command Prompt for VS 2022"
- For MinGW: Add MinGW bin folder to PATH
- Verify: `where cl` (MSVC) or `where gcc` (MinGW)

### Missing DLL at runtime
**Problem:** Executable fails with "missing DLL" error

**Solution:**
- Copy required DLLs to same folder as .exe:
  - `libpng16.dll`
  - `zlib1.dll`
- Or use static linking: `cmake .. -DBUILD_SHARED_LIBS=OFF`

### Build fails with linker errors
**Problem:** Undefined reference to math functions

**Solution:**
- Math library is usually auto-linked on Windows
- If issues persist, explicitly link: Add to CMakeLists.txt:
  ```cmake
  if(WIN32)
      # No explicit math lib needed on Windows
  endif()
  ```

---

## Alternative: Cross-Compilation from macOS (Advanced)

If you want to compile for Windows from macOS without a Windows machine:

```bash
# Install MinGW cross-compiler
brew install mingw-w64

# Create toolchain file
cat > mingw-toolchain.cmake << EOF
set(CMAKE_SYSTEM_NAME Windows)
set(CMAKE_C_COMPILER x86_64-w64-mingw32-gcc)
set(CMAKE_CXX_COMPILER x86_64-w64-mingw32-g++)
set(CMAKE_RC_COMPILER x86_64-w64-mingw32-windres)
set(CMAKE_FIND_ROOT_PATH /opt/homebrew/opt/mingw-w64)
EOF

# Build
mkdir build-mingw
cd build-mingw
cmake .. -DCMAKE_TOOLCHAIN_FILE=../mingw-toolchain.cmake
make
```

**Note:** This approach may have issues with library dependencies and is less reliable than native Windows compilation.

---

## Summary Checklist

- [ ] Install CMake on Windows
- [ ] Install Visual Studio or MinGW
- [ ] (Optional) Install vcpkg for dependencies
- [ ] Transfer `backend/` folder to Windows
- [ ] Configure CMake in `build-windows/` directory
- [ ] Build all executables
- [ ] Test executables run correctly
- [ ] Copy `.exe` files to `backend/bin-windows/`
- [ ] Transfer back to macOS
- [ ] Update `vcctl.spec` for platform-specific binaries
- [ ] Test Windows PyInstaller build

---

## Next Steps

After compiling Windows executables:
1. Update PyInstaller spec for cross-platform binaries
2. Create Windows packaging workflow
3. Test on Windows with PyInstaller
4. Repeat for Linux (using similar CMake process)

---

*Last Updated: October 3, 2025*

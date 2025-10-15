# Windows Build Guide for VCCTL Backend C Programs

## Overview

This guide provides complete step-by-step instructions for compiling all 26 VCCTL backend C programs on Windows using MinGW/GCC. The MinGW toolchain is recommended over MSVC due to better compatibility with the VCCTL codebase.

**Important:** The VCCTL backend programs were originally developed for Unix/Linux systems. While they can be compiled with Microsoft Visual C++ (MSVC), the MinGW/GCC toolchain provides better compatibility and avoids known bugs in MSVC-compiled executables.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installing MSYS2 and MinGW](#installing-msys2-and-mingw)
3. [Installing Required Dependencies](#installing-required-dependencies)
4. [Obtaining the VCCTL Source Code](#obtaining-the-vcctl-source-code)
5. [Configuring the Build with CMake](#configuring-the-build-with-cmake)
6. [Compiling the Executables](#compiling-the-executables)
7. [Verifying the Build](#verifying-the-build)
8. [Troubleshooting](#troubleshooting)
9. [Alternative: MSVC Compilation (Not Recommended)](#alternative-msvc-compilation-not-recommended)

---

## Prerequisites

### System Requirements

- **Operating System:** Windows 10 or Windows 11 (64-bit)
- **Disk Space:** ~5 GB free space for MSYS2, build tools, and source code
- **RAM:** 4 GB minimum (8 GB recommended for faster compilation)
- **Internet Connection:** Required for downloading MSYS2 and dependencies

### Required Software

All software will be installed through MSYS2 package manager (pacman). No separate downloads needed.

---

## Installing MSYS2 and MinGW

### Step 1: Download MSYS2 Installer

1. Visit the official MSYS2 website: https://www.msys2.org/
2. Download the installer: `msys2-x86_64-<version>.exe`
3. Run the installer with default settings
4. **Default installation path:** `C:\msys64`

### Step 2: Initial MSYS2 Setup

1. After installation completes, the MSYS2 terminal will open automatically
2. Update the package database:
   ```bash
   pacman -Syu
   ```
3. When prompted to close the terminal, type `Y` and close the window
4. Reopen MSYS2 from the Start menu (search for "MSYS2 MINGW64")
5. Complete the update:
   ```bash
   pacman -Su
   ```

**Important:** Always use "MSYS2 MINGW64" terminal (not "MSYS2 MSYS" or "MSYS2 UCRT64") for building VCCTL.

---

## Installing Required Dependencies

Open the MSYS2 MINGW64 terminal and install the following packages:

### Step 1: Install Core Build Tools

```bash
pacman -S mingw-w64-x86_64-gcc \
          mingw-w64-x86_64-cmake \
          mingw-w64-x86_64-make \
          mingw-w64-x86_64-pkg-config
```

When prompted, type `Y` to proceed with installation.

**Packages installed:**
- `gcc` - GNU C Compiler (GCC) version 15.2.0 or newer
- `cmake` - Build system generator
- `make` - Build automation tool (mingw32-make)
- `pkg-config` - Helper tool for library configuration

### Step 2: Install Required Libraries

```bash
pacman -S mingw-w64-x86_64-libpng \
          mingw-w64-x86_64-zlib
```

**Libraries installed:**
- `libpng` - PNG image library (required for image I/O)
- `zlib` - Compression library (dependency for libpng)

### Step 3: Verify Installation

Check that all tools are correctly installed:

```bash
gcc --version
cmake --version
mingw32-make --version
pkg-config --version
```

Expected output:
- GCC: version 15.2.0 or newer
- CMake: version 3.26 or newer
- mingw32-make: version 4.4 or newer
- pkg-config: version 2.3 or newer

---

## Obtaining the VCCTL Source Code

### Option 1: Clone from GitHub (Recommended)

If you have git installed:

```bash
cd /c/Users/YOUR_USERNAME/Desktop
git clone https://github.com/jwbullard/VCCTL.git
cd VCCTL/backend
```

Replace `YOUR_USERNAME` with your Windows username.

### Option 2: Download ZIP Archive

1. Visit https://github.com/jwbullard/VCCTL
2. Click "Code" → "Download ZIP"
3. Extract to a convenient location (e.g., Desktop)
4. In MSYS2 terminal, navigate to the backend directory:
   ```bash
   cd /c/Users/YOUR_USERNAME/Desktop/VCCTL/backend
   ```

**Note:** MSYS2 uses Unix-style paths. Windows `C:\` becomes `/c/` in MSYS2.

---

## Configuring the Build with CMake

### Step 1: Create Build Directory

From the `backend` directory:

```bash
rm -rf build-mingw          # Remove any existing build directory
mkdir build-mingw           # Create fresh build directory
cd build-mingw              # Enter build directory
```

### Step 2: Set MinGW Path

Ensure MinGW binaries are in your PATH:

```bash
export PATH="/c/msys64/mingw64/bin:$PATH"
```

**Note:** This is only needed for the current terminal session. Add to `~/.bashrc` to make permanent.

### Step 3: Run CMake Configuration

Configure the build system with CMake:

```bash
cmake -G "MinGW Makefiles" \
      -DCMAKE_MAKE_PROGRAM=/c/msys64/mingw64/bin/mingw32-make.exe \
      -DCMAKE_C_COMPILER=/c/msys64/mingw64/bin/gcc.exe \
      -DCMAKE_PREFIX_PATH=/c/msys64/mingw64 \
      ..
```

**What this does:**
- `-G "MinGW Makefiles"` - Use MinGW-compatible makefiles
- `-DCMAKE_MAKE_PROGRAM` - Specify mingw32-make location
- `-DCMAKE_C_COMPILER` - Specify GCC compiler location
- `-DCMAKE_PREFIX_PATH` - Tell CMake where to find libraries
- `..` - Source directory (parent of build-mingw)

**Expected output:**
```
-- The C compiler identification is GNU 15.2.0
-- Detecting C compiler ABI info - done
-- Found ZLIB: C:/msys64/mingw64/lib/libz.dll.a (found version "1.3.1")
-- Found PNG: C:/msys64/mingw64/lib/libpng.dll.a (found version "1.6.50")
Found MATH_LIB: [C:/msys64/mingw64/lib/libm.a]
-- Configuring done (0.3s)
-- Generating done (0.8s)
-- Build files have been written to: C:/Users/YOUR_USERNAME/Desktop/VCCTL/backend/build-mingw
```

If you see errors, refer to [Troubleshooting](#troubleshooting) section.

---

## Compiling the Executables

### Step 1: Run the Build

From the `build-mingw` directory:

```bash
/c/msys64/mingw64/bin/mingw32-make.exe
```

**Build progress:**
```
[  1%] Building C object src/vcctllib/CMakeFiles/vcctl.dir/breakflocs.c.obj
[  2%] Building C object src/vcctllib/CMakeFiles/vcctl.dir/calcporedist3d.c.obj
...
[ 28%] Built target vcctl
[ 31%] Built target aggvrml
...
[100%] Built target disrealnew
```

**Build time:** Approximately 2-3 minutes on modern hardware.

### Step 2: Verify Compilation Success

Check that all executables were created:

```bash
ls -lh *.exe
```

You should see 26 executables:

**Core VCCTL Programs (7):**
- `genmic.exe` (640 KB) - Microstructure generation
- `disrealnew.exe` (713 KB) - Hydration simulation
- `elastic.exe` (570 KB) - Elastic moduli calculations
- `genaggpack.exe` (531 KB) - Aggregate packing
- `perc3d.exe` (509 KB) - Percolation/connectivity analysis
- `stat3d.exe` (504 KB) - Microstructure statistics
- `oneimage.exe` (462 KB) - Image processing

**Additional Utilities (19):**
- `aggvrml.exe` (475 KB) - Aggregate VRML output
- `apstats.exe` (447 KB) - Aggregate particle statistics
- `chlorattack3d.exe` (470 KB) - Chloride attack simulation
- `distfapart.exe` (441 KB) - Distance far apart analysis
- `distfarand.exe` (439 KB) - Random distance analysis
- `dryout.exe` (454 KB) - Drying simulation
- `hydmovie.exe` (461 KB) - Hydration movie generation
- `image100.exe` (464 KB) - Image processing (100x100)
- `leach3d.exe` (454 KB) - Leaching simulation
- `measagg.exe` (453 KB) - Aggregate measurement
- `onepimage.exe` (461 KB) - Periodic image processing
- `perc3d-leach.exe` (455 KB) - Percolation with leaching
- `poredist3d.exe` (479 KB) - Pore distribution analysis
- `rand3d.exe` (489 KB) - Random microstructure generation
- `sulfattack3d.exe` (471 KB) - Sulfate attack simulation
- `thames2vcctl.exe` (451 KB) - THAMES to VCCTL converter
- `thames2vcctlcorr.exe` (451 KB) - THAMES converter (corrected)
- `totsurf.exe` (446 KB) - Total surface area calculation
- `transport.exe` (516 KB) - Transport property simulation

**Note:** File sizes are approximate and may vary slightly between builds.

---

## Verifying the Build

### Step 1: Copy Executables to Final Location

```bash
# From build-mingw directory
cp *.exe ../bin-windows/
```

This copies all executables to the standard Windows binary directory.

### Step 2: Test a Simple Executable

Test the `stat3d` program (simple and safe to test):

```bash
cd ../bin-windows
./stat3d.exe --help
```

Expected output:
```
Usage: stat3d [-h,--help] [-q,--quiet | -s,--silent]
      -j,--json progress.json -w,--workdir working_directory
...
```

### Step 3: Test genmic (Critical Program)

**Warning:** Full genmic test requires proper input file and can run for several minutes. For quick verification:

```bash
./genmic.exe --help
```

Expected output:
```
Usage: genmic [-h,--help] [-q,--quiet | -s,--silent]
      -j,--json progress.json -w,--workdir working_directory
...
```

If you see the help message, genmic is correctly compiled.

---

## Troubleshooting

### Problem: "cmake: command not found"

**Cause:** CMake not installed or not in PATH.

**Solution:**
```bash
pacman -S mingw-w64-x86_64-cmake
```

### Problem: "gcc: command not found"

**Cause:** GCC not installed or wrong MSYS2 terminal.

**Solution:**
1. Ensure you're using "MSYS2 MINGW64" terminal (not MSYS or UCRT64)
2. Install GCC:
   ```bash
   pacman -S mingw-w64-x86_64-gcc
   ```

### Problem: "Could not find PNG library"

**Cause:** libpng not installed.

**Solution:**
```bash
pacman -S mingw-w64-x86_64-libpng mingw-w64-x86_64-zlib
```

### Problem: CMake error "By not providing 'Findunofficial-getopt-win32.cmake'"

**Cause:** CMakeLists.txt is trying to use MSVC-specific getopt library.

**Solution:** This should not occur with current CMakeLists.txt. If it does, verify you're using the latest version:
```bash
git pull origin main  # Update to latest code
```

The CMakeLists.txt should have:
```cmake
if(MSVC)
    find_package(unofficial-getopt-win32 REQUIRED)
endif()
```

NOT:
```cmake
if(WIN32)
    find_package(unofficial-getopt-win32 REQUIRED)
endif()
```

### Problem: Compilation errors in imageutil.c about png.h

**Cause:** Custom png.h header file conflicting with system libpng.

**Solution:**
```bash
# From backend directory
cd src/include
mv png.h png.h.msvc-only  # Rename to disable it
```

This file is only needed for MSVC builds, not MinGW.

### Problem: "redefinition of 'clock_gettime'" error

**Cause:** win32_compat.h defining clock_gettime for all Windows builds.

**Solution:** Verify `backend/src/include/win32_compat.h` has:
```c
#if defined(_WIN32) && defined(_MSC_VER)
```

NOT:
```c
#ifdef _WIN32
```

MinGW has built-in clock_gettime and doesn't need the compatibility layer.

### Problem: Build succeeds but executables crash immediately

**Possible causes:**
1. Missing DLL dependencies
2. Incorrect MSYS2 environment

**Solution:**
1. Check DLL dependencies:
   ```bash
   ldd genmic.exe
   ```
   All DLLs should be found in `/c/msys64/mingw64/bin`

2. Ensure you're running executables from MSYS2 terminal, not Windows Command Prompt

3. If running from Windows Command Prompt, add to PATH:
   ```
   C:\msys64\mingw64\bin
   ```

---

## Alternative: MSVC Compilation (Not Recommended)

**Warning:** MSVC-compiled executables have known bugs. MinGW/GCC is strongly recommended.

### Known Issues with MSVC

- **genmic.exe crash:** Consistently crashes at "Extra pixels (cumulative) = 8" during particle adjustment
- **Root cause:** Memory alignment or array bounds handling difference between MSVC and GCC
- **Status:** Unresolved

### If You Must Use MSVC

Requirements:
- Visual Studio 2022 (Build Tools or Community Edition)
- vcpkg package manager
- CMake 3.26 or newer

**vcpkg dependencies:**
```cmd
vcpkg install libpng:x64-windows zlib:x64-windows getopt-win32:x64-windows
```

**CMake configuration:**
```cmd
cd backend
mkdir build-msvc
cd build-msvc
cmake -G "Visual Studio 17 2022" -A x64 ^
      -DCMAKE_TOOLCHAIN_FILE=C:/path/to/vcpkg/scripts/buildsystems/vcpkg.cmake ^
      ..
cmake --build . --config Release
```

**Result:**
- Executables will be in `build-msvc/Release/`
- **genmic.exe will crash** - this is a known bug
- Other executables may work correctly

**Recommendation:** Use MinGW/GCC instead to avoid these issues.

---

## Advanced Topics

### Building in Release vs Debug Mode

**Default:** Release mode with `-O2` optimization

**To build Debug mode:**
```bash
cmake -G "MinGW Makefiles" \
      -DCMAKE_BUILD_TYPE=Debug \
      -DCMAKE_C_FLAGS="-g -O0" \
      ...
```

Debug builds are larger and slower but include debugging symbols for troubleshooting.

### Parallel Compilation

Speed up compilation using multiple CPU cores:

```bash
mingw32-make.exe -j4  # Use 4 parallel jobs
```

Replace `4` with your CPU core count for optimal speed.

### Clean Build

To rebuild from scratch:

```bash
cd backend/build-mingw
mingw32-make.exe clean    # Remove object files
mingw32-make.exe          # Rebuild
```

Or remove entire build directory:

```bash
cd backend
rm -rf build-mingw
mkdir build-mingw
# ... run cmake again
```

---

## Integration with PyInstaller Windows Package

After building the executables, they can be bundled with the VCCTL Python application using PyInstaller.

### Step 1: Copy Executables to Package Location

```bash
# From backend directory
cp build-mingw/*.exe bin-windows/
```

### Step 2: Verify vcctl.spec References

The `vcctl.spec` file should include:

```python
# Platform-specific binaries
if sys.platform == 'win32':
    platform_binaries = [
        ('backend/bin-windows/genmic.exe', 'backend/bin/'),
        ('backend/bin-windows/disrealnew.exe', 'backend/bin/'),
        ('backend/bin-windows/elastic.exe', 'backend/bin/'),
        # ... all 26 executables
    ]
```

### Step 3: Build Windows Package

```bash
# From VCCTL root directory
export PATH="/c/msys64/mingw64/bin:$PATH"
/c/msys64/mingw64/bin/python -m PyInstaller vcctl.spec
```

**Result:** Complete Windows package at `dist/VCCTL/VCCTL.exe`

---

## Frequently Asked Questions

### Q: Why MinGW instead of MSVC?

**A:** MSVC-compiled genmic.exe has a critical bug that causes crashes during particle size distribution adjustment. MinGW/GCC produces stable executables without this issue. The VCCTL codebase was originally developed for Unix/Linux systems and works better with GCC-based compilers.

### Q: Can I use MinGW-w64 from mingw-w64.org instead of MSYS2?

**A:** Technically yes, but MSYS2 provides easier dependency management through pacman. Standalone MinGW-w64 requires manual library installation.

### Q: Do I need to install Python in MSYS2?

**A:** Only if you plan to build the PyInstaller package from within MSYS2. For just compiling C executables, Python is not needed.

### Q: Can I compile on Windows and run on Linux?

**A:** No, these are Windows executables (.exe). For Linux, you must compile on a Linux system or use cross-compilation (advanced, not covered here).

### Q: How much disk space do the compiled executables use?

**A:** All 26 executables total approximately 13 MB. Individual executables range from 440 KB to 713 KB.

### Q: Can I distribute the executables without MSYS2?

**A:** Yes, but you must bundle the MinGW DLLs:
- libgcc_s_seh-1.dll
- libstdc++-6.dll
- libwinpthread-1.dll
- libpng16-16.dll
- zlib1.dll

PyInstaller handles this automatically when building the Windows package.

---

## Additional Resources

### MSYS2 Documentation
- Official website: https://www.msys2.org/
- Package search: https://packages.msys2.org/

### CMake Documentation
- Official website: https://cmake.org/
- Command-line reference: https://cmake.org/cmake/help/latest/manual/cmake.1.html

### VCCTL Project
- GitHub repository: https://github.com/jwbullard/VCCTL
- Issue tracker: https://github.com/jwbullard/VCCTL/issues

---

## Revision History

| Date | Version | Changes |
|------|---------|---------|
| 2025-10-15 | 1.0 | Initial version - MinGW/GCC build instructions |

---

## License

This documentation is part of the VCCTL project. See the main project LICENSE file for details.

---

**Document prepared by:** VCCTL Development Team
**Last updated:** October 15, 2025
**For:** VCCTL Version 10.0.0 and later

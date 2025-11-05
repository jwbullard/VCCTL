# Creating a GitHub Release for VCCTL

This document provides step-by-step instructions for creating and publishing a GitHub release for VCCTL.

## Prerequisites

- Both distribution packages created:
  - **Windows:** `VCCTL-10.0.0-Windows-x64.zip` (719 MB)
  - **macOS:** `VCCTL-10.0.0-macOS-arm64.dmg` (~800-900 MB)
- Git repository with all changes committed and pushed
- GitHub account with write access to the repository
- Release notes prepared

## Step 1: Create Git Tag

Tags mark specific points in your repository's history as important (e.g., releases).

```bash
# Navigate to repository
cd /path/to/VCCTL

# Ensure you're on main branch with latest changes
git checkout main
git pull origin main

# Create annotated tag for version 10.0.0
git tag -a v10.0.0 -m "VCCTL Version 10.0.0 - First Public Release"

# Push tag to GitHub
git push origin v10.0.0
```

**Verify Tag:**
```bash
# List all tags
git tag

# Show tag details
git show v10.0.0
```

## Step 2: Navigate to GitHub Releases

1. Open your web browser
2. Go to your repository: `https://github.com/jwbullard/VCCTL`
3. Click on **"Releases"** (right side of page, below "About")
4. Click **"Draft a new release"** button

## Step 3: Configure Release

### Release Tag
- **Choose a tag:** Select `v10.0.0` from dropdown
- If tag doesn't appear, ensure you pushed it: `git push origin v10.0.0`

### Release Title
```
VCCTL 10.0.0 - Virtual Cement and Concrete Testing Laboratory
```

### Target Branch
- **Target:** `main` (default)

### Release Description

Copy and paste the prepared release notes (see template below).

## Step 4: Upload Distribution Files

Click **"Attach binaries by dropping them here or selecting them"**

Upload these files:
1. `dist/VCCTL-10.0.0-Windows-x64.zip` (719 MB)
2. `VCCTL-10.0.0-macOS-arm64.dmg` (~800-900 MB)

**Important:** Wait for both uploads to complete (progress bar shows 100%)

## Step 5: Additional Options

### Pre-release
- [ ] Leave unchecked (this is a stable release)

### Create a discussion for this release
- [ ] Optional - check if you want to enable community discussion

### Set as the latest release
- [x] Check this box (recommended for v10.0.0)

## Step 6: Publish Release

1. Review all information
2. Click **"Publish release"** button
3. GitHub will create the release page

## Step 7: Verify Release

After publishing:

1. Navigate to Releases page
2. Verify release appears with correct version
3. Click on release to view details
4. Test download links:
   - Click on `VCCTL-10.0.0-Windows-x64.zip` to download
   - Click on `VCCTL-10.0.0-macOS-arm64.dmg` to download
5. Verify file sizes match original files

## Release Notes Template

```markdown
# VCCTL 10.0.0 - First Public Release

Virtual Cement and Concrete Testing Laboratory - Professional desktop application for modeling and simulating cement and concrete materials.

## Downloads

Choose the appropriate version for your operating system:

- **Windows (64-bit):** [VCCTL-10.0.0-Windows-x64.zip](https://github.com/jwbullard/VCCTL/releases/download/v10.0.0/VCCTL-10.0.0-Windows-x64.zip) (719 MB)
- **macOS (Apple Silicon):** [VCCTL-10.0.0-macOS-arm64.dmg](https://github.com/jwbullard/VCCTL/releases/download/v10.0.0/VCCTL-10.0.0-macOS-arm64.dmg) (~800 MB)

## Installation Instructions

### Windows Installation

1. **Download** the ZIP file: `VCCTL-10.0.0-Windows-x64.zip`
2. **Extract** the ZIP archive to your desired location:
   - Recommended: `C:\Program Files\VCCTL\`
   - Alternative: Any folder with write permissions
3. **Run** `VCCTL.exe` from the extracted folder
4. **First Launch:** Application will extract particle and aggregate shape sets (~30 seconds)

**No installation required** - This is a portable application that runs directly from the extracted folder.

### macOS Installation

1. **Download** the DMG file: `VCCTL-10.0.0-macOS-arm64.dmg`
2. **Open** the downloaded DMG file (double-click)
3. **Drag** the VCCTL.app icon to your Applications folder
4. **Launch** VCCTL from Applications folder
5. **First Launch:**
   - You may see a security warning (application is not notarized)
   - Right-click VCCTL.app → Open → Confirm to open
   - Application will extract particle and aggregate shape sets (~30 seconds)

**macOS Gatekeeper Note:** This application is not code-signed or notarized. See Security Notes below.

## System Requirements

### Windows
- **Operating System:** Windows 10 or Windows 11 (64-bit)
- **Processor:** Intel/AMD x64 processor, 1 GHz or faster
- **Memory:** 2 GB RAM minimum, 4 GB recommended
- **Storage:** 3 GB available disk space (1.3 GB application + data files)
- **Graphics:** Any graphics card with OpenGL 3.3 support

### macOS
- **Operating System:** macOS 10.14 (Mojave) or later
- **Processor:** Apple Silicon (M1/M2/M3) or Intel x86_64
- **Memory:** 2 GB RAM minimum, 4 GB recommended
- **Storage:** 3 GB available disk space
- **Graphics:** Any graphics card with OpenGL 3.3 support

## Features

### Materials Management
- **Cement Compositions:** Portland cement (ASTM C150 types), blended cements
- **Supplementary Materials:** Fly ash (Class C/F), slag, silica fume
- **Aggregates:** Fine and coarse aggregates with full PSD support
- **Inert Fillers:** Limestone, quartz, and custom fillers

### Mix Design
- Virtual concrete and mortar mixture creation
- Automatic validation against physical constraints
- Water-to-cement ratio optimization
- Aggregate packing simulation

### Microstructure Generation
- 3D digital microstructures (resolution down to 1 μm)
- Particle shape library (23,000+ realistic particles)
- Periodic boundary conditions
- Initial phase assemblies for hydration

### Hydration Simulation
- **Modes:**
  - Isothermal hydration (constant temperature)
  - Adiabatic hydration (self-heating)
  - Temperature profile hydration (time-varying temperature)
- **Kinetics Models:**
  - Knudsen parabolic time calibration
  - Calorimetry data calibration
  - Chemical shrinkage calibration
- **Progress Tracking:** Real-time monitoring with pause/resume support
- **Concurrent Operations:** Run multiple simulations simultaneously

### Property Calculations
- **Elastic Moduli:** Bulk modulus, shear modulus, Young's modulus, Poisson's ratio
- **ITZ Analysis:** Interfacial transition zone characterization
- **3D Strain Energy:** Visualization of stress distribution

### Visualization
- **3D Microstructure Viewer:** Interactive phase rendering with VTK
- **Phase Controls:** Show/hide individual phases, adjust opacity
- **Camera Controls:** Rotation, zoom, pan, view reset
- **2D Plots:** Real-time hydration kinetics and property evolution

## What's New in Version 10.0.0

This is the first public release of VCCTL as a standalone desktop application.

### Core Features
- Complete rewrite in Python with GTK3 user interface
- Cross-platform support (Windows and macOS)
- Modern database architecture (SQLAlchemy)
- Real-time 3D visualization (PyVista/VTK)

### Temperature Profile Mode
- Support for complex thermal histories
- CSV-based temperature profile input
- Automatic temperature interpolation during simulation

### Concurrent Operations
- Run multiple hydration simulations simultaneously
- Independent progress tracking per operation
- Pause/resume individual operations

### User Experience Improvements
- Clean, modern interface with Carbon icons
- Comprehensive documentation (built-in Help menu)
- Automatic data extraction on first launch
- Platform-specific data directories

## Known Issues

1. **macOS Security Warning:** Application is not notarized, requiring manual approval on first launch
2. **3D Rendering Performance:** Large microstructures (>200³ voxels) may render slowly on older hardware
3. **Windows SmartScreen:** May show warning on first launch - click "More info" → "Run anyway"

## Security Notes

### Code Signing Status
- **Windows:** Not code-signed (may trigger SmartScreen warning)
- **macOS:** Not code-signed or notarized (requires manual approval)

### Why Unsigned?
Code signing certificates cost $100-400/year. As an academic project, we've prioritized functionality over code signing. The source code is publicly available on GitHub for verification.

### How to Verify Safety
1. Download only from official GitHub Releases page
2. Verify file sizes match those listed above
3. Check MD5/SHA256 checksums (see Checksums section below)
4. Review source code on GitHub: https://github.com/jwbullard/VCCTL

## Checksums

Verify file integrity using these checksums:

### Windows Package
```
MD5:    [to be added after final build]
SHA256: [to be added after final build]
```

### macOS Package
```
MD5:    [to be added after final build]
SHA256: [to be added after final build]
```

**Generate checksums yourself:**
```bash
# Windows (PowerShell)
Get-FileHash VCCTL-10.0.0-Windows-x64.zip -Algorithm MD5
Get-FileHash VCCTL-10.0.0-Windows-x64.zip -Algorithm SHA256

# macOS/Linux
md5 VCCTL-10.0.0-macOS-arm64.dmg
shasum -a 256 VCCTL-10.0.0-macOS-arm64.dmg
```

## Getting Help

- **Documentation:** Built into application (Help menu → User Guide)
- **GitHub Issues:** [Report bugs or request features](https://github.com/jwbullard/VCCTL/issues)
- **Email:** jwbullard@tamu.edu

## License

[Include your license information here - e.g., MIT, GPL, etc.]

## Credits

**Original Development:** NIST Building and Fire Research Laboratory
**Current Maintainer:** Jeffrey W. Bullard, Texas A&M University

**Built with:**
- Python 3.12
- GTK3 (user interface)
- PyVista/VTK (3D visualization)
- SQLAlchemy (database)
- NumPy/SciPy (scientific computing)

---

**Bundle Identifier:** edu.tamu.vcctl
**Version:** 10.0.0
**Release Date:** [Current Date]
```

## Post-Release Tasks

After publishing the release:

### 1. Update Documentation
- Update README.md with installation links
- Update any website or project pages

### 2. Generate Checksums
```bash
# Windows
md5sum dist/VCCTL-10.0.0-Windows-x64.zip
sha256sum dist/VCCTL-10.0.0-Windows-x64.zip

# macOS
md5 VCCTL-10.0.0-macOS-arm64.dmg
shasum -a 256 VCCTL-10.0.0-macOS-arm64.dmg
```

Add checksums to release notes (Edit release on GitHub).

### 3. Announce Release
- Post on relevant forums/mailing lists
- Update university/department website
- Social media announcement (if applicable)

### 4. Monitor Issues
- Watch GitHub Issues for bug reports
- Respond to user questions promptly
- Plan bug fix releases as needed (v10.0.1, v10.0.2, etc.)

## Creating Patch Releases

For bug fixes (v10.0.1, v10.0.2, etc.):

```bash
# Make fixes and commit
git commit -m "Fix [description]"
git push origin main

# Create patch release tag
git tag -a v10.0.1 -m "VCCTL Version 10.0.1 - Bug Fixes"
git push origin v10.0.1

# Create release on GitHub
# Upload updated packages
# Include "What's Fixed" section in release notes
```

## Creating Minor Releases

For new features (v10.1.0, v10.2.0, etc.):

```bash
# Develop new features in feature branch
git checkout -b feature/new-capability
git commit -m "Add new feature"
git checkout main
git merge feature/new-capability
git push origin main

# Create minor release tag
git tag -a v10.1.0 -m "VCCTL Version 10.1.0 - New Features"
git push origin v10.1.0

# Create release on GitHub
# Upload new packages
# Include "What's New" section highlighting features
```

## Troubleshooting GitHub Releases

### Tag Already Exists
```bash
# Delete local tag
git tag -d v10.0.0

# Delete remote tag
git push origin :refs/tags/v10.0.0

# Recreate tag
git tag -a v10.0.0 -m "Updated message"
git push origin v10.0.0
```

### Upload Failed
- Check file size (GitHub limit: 2 GB per file)
- Check internet connection
- Try uploading via GitHub CLI: `gh release upload v10.0.0 file.zip`

### Release Not Appearing
- Ensure tag was pushed: `git push origin v10.0.0`
- Check repository visibility (public vs private)
- Refresh GitHub page

## Additional Resources

- [GitHub Releases Documentation](https://docs.github.com/en/repositories/releasing-projects-on-github)
- [Semantic Versioning](https://semver.org/)
- [GitHub CLI for Releases](https://cli.github.com/manual/gh_release)

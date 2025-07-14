# VCCTL Installation Guide

**Virtual Cement and Concrete Testing Laboratory**  
**Desktop Application Installation Instructions**

---

## Table of Contents

1. [Quick Installation](#quick-installation)
2. [System Requirements](#system-requirements)
3. [Pre-Installation Checklist](#pre-installation-checklist)
4. [Linux Installation](#linux-installation)
5. [Windows Installation](#windows-installation)
6. [macOS Installation](#macos-installation)
7. [Development Installation](#development-installation)
8. [Verification](#verification)
9. [Troubleshooting](#troubleshooting)
10. [Uninstallation](#uninstallation)

---

## Quick Installation

**Choose the appropriate package for your platform:**

### Linux (Recommended)
```bash
# Download and run AppImage
wget https://github.com/usnistgov/vcctl/releases/latest/download/VCCTL-x86_64.AppImage
chmod +x VCCTL-x86_64.AppImage
./VCCTL-x86_64.AppImage
```

### Windows
1. Download [VCCTL-Setup-x64.exe](https://github.com/usnistgov/vcctl/releases/latest/download/VCCTL-Setup-x64.exe)
2. Run installer as Administrator
3. Launch from Start Menu

### macOS
1. Download [VCCTL-macOS.dmg](https://github.com/usnistgov/vcctl/releases/latest/download/VCCTL-macOS.dmg)
2. Mount DMG and drag VCCTL.app to Applications
3. Launch from Launchpad

**For detailed installation instructions and troubleshooting, continue reading below.**

---

## System Requirements

### Minimum Requirements

- **Operating System**: 
  - Linux: Ubuntu 18.04+ / CentOS 7+ / Fedora 30+
  - Windows: Windows 10 (64-bit)
  - macOS: 10.14 (Mojave) or later
- **Processor**: 64-bit x86 processor, 2 GHz dual-core
- **Memory**: 4 GB RAM
- **Storage**: 2 GB available disk space
- **Graphics**: OpenGL 3.0 compatible graphics card
- **Network**: Internet connection for initial setup and updates

### Recommended Requirements

- **Processor**: 64-bit x86 processor, 3 GHz quad-core or better
- **Memory**: 8 GB RAM (16 GB for large simulations)
- **Storage**: 10 GB available disk space (SSD recommended)
- **Graphics**: Dedicated graphics card with 2 GB VRAM
- **Network**: Broadband internet connection

### Dependencies

#### Linux
- GTK3 3.22 or later
- Python 3.8 or later
- NumPy, SciPy scientific libraries
- OpenGL libraries

#### Windows
- Visual C++ Redistributable 2019 or later
- .NET Framework 4.7.2 or later
- GTK3 runtime environment

#### macOS
- Xcode Command Line Tools
- Homebrew package manager (recommended)
- GTK3 via Homebrew

---

## Pre-Installation Checklist

Before installing VCCTL, ensure your system meets the requirements:

### System Check

1. **Verify Operating System**
   ```bash
   # Linux
   lsb_release -a
   
   # macOS
   sw_vers
   
   # Windows
   winver
   ```

2. **Check Available Memory**
   ```bash
   # Linux/macOS
   free -h
   
   # Windows (PowerShell)
   Get-WmiObject -Class Win32_ComputerSystem | Select TotalPhysicalMemory
   ```

3. **Check Disk Space**
   ```bash
   # Linux/macOS
   df -h
   
   # Windows
   dir
   ```

4. **Verify Graphics Support**
   ```bash
   # Linux
   glxinfo | grep "OpenGL version"
   
   # macOS
   system_profiler SPDisplaysDataType
   
   # Windows
   dxdiag
   ```

### User Permissions

Ensure you have administrative privileges for installation:

- **Linux**: Use `sudo` or root access
- **Windows**: Run installer as Administrator
- **macOS**: Administrative user account required

---

## Linux Installation

### Method 1: AppImage (Recommended)

**AppImage is the easiest way to install VCCTL on Linux. It works on all distributions and requires no system modifications.**

1. **Download AppImage**
   ```bash
   # Download latest release
   wget https://github.com/usnistgov/vcctl/releases/latest/download/VCCTL-x86_64.AppImage
   
   # Or download specific version
   wget https://github.com/usnistgov/vcctl/releases/download/v1.0.0/VCCTL-x86_64.AppImage
   ```

2. **Make Executable and Run**
   ```bash
   chmod +x VCCTL-x86_64.AppImage
   ./VCCTL-x86_64.AppImage
   ```

3. **Optional: Install to System**
   ```bash
   # Move to applications directory
   sudo mkdir -p /opt/vcctl
   sudo mv VCCTL-x86_64.AppImage /opt/vcctl/vcctl
   
   # Create desktop entry
   cat > ~/.local/share/applications/vcctl.desktop << EOF
   [Desktop Entry]
   Name=VCCTL
   Comment=Virtual Cement and Concrete Testing Laboratory
   Exec=/opt/vcctl/vcctl
   Icon=vcctl
   Terminal=false
   Type=Application
   Categories=Science;Education;Engineering;
   EOF
   
   # Make desktop entry executable
   chmod +x ~/.local/share/applications/vcctl.desktop
   ```

4. **Add to PATH (Optional)**
   ```bash
   # Add to ~/.bashrc or ~/.zshrc
   echo 'export PATH="/opt/vcctl:$PATH"' >> ~/.bashrc
   source ~/.bashrc
   
   # Now you can run: vcctl
   ```

### Method 2: Package Manager

#### Ubuntu/Debian

1. **Add VCCTL Repository**
   ```bash
   # Add GPG key
   wget -qO - https://packages.nist.gov/vcctl/gpg.key | sudo apt-key add -
   
   # Add repository
   echo "deb https://packages.nist.gov/vcctl/ubuntu $(lsb_release -cs) main" | \
   sudo tee /etc/apt/sources.list.d/vcctl.list
   
   # Update package list
   sudo apt update
   ```

2. **Install VCCTL**
   ```bash
   sudo apt install vcctl-desktop
   ```

3. **Install Dependencies** (if not automatically resolved)
   ```bash
   sudo apt install python3 python3-pip python3-gi python3-gi-cairo \
                    gir1.2-gtk-3.0 libgtk-3-dev python3-numpy python3-scipy \
                    python3-matplotlib python3-skimage
   ```

#### CentOS/RHEL/Fedora

1. **Add VCCTL Repository**
   ```bash
   # Add repository file
   sudo tee /etc/yum.repos.d/vcctl.repo << EOF
   [vcctl]
   name=VCCTL Repository
   baseurl=https://packages.nist.gov/vcctl/centos/\$releasever/\$basearch/
   gpgcheck=1
   gpgkey=https://packages.nist.gov/vcctl/gpg.key
   enabled=1
   EOF
   ```

2. **Install VCCTL**
   ```bash
   # CentOS/RHEL
   sudo yum install vcctl-desktop
   
   # Fedora
   sudo dnf install vcctl-desktop
   ```

### Method 2: AppImage (Universal)

1. **Download AppImage**
   ```bash
   wget https://github.com/usnistgov/vcctl/releases/latest/download/VCCTL-x86_64.AppImage
   ```

2. **Make Executable**
   ```bash
   chmod +x VCCTL-x86_64.AppImage
   ```

3. **Run VCCTL**
   ```bash
   ./VCCTL-x86_64.AppImage
   ```

4. **Optional: Install to System**
   ```bash
   # Move to applications directory
   sudo mv VCCTL-x86_64.AppImage /opt/vcctl/
   
   # Create desktop entry
   cat > ~/.local/share/applications/vcctl.desktop << EOF
   [Desktop Entry]
   Name=VCCTL
   Comment=Virtual Cement and Concrete Testing Laboratory
   Exec=/opt/vcctl/VCCTL-x86_64.AppImage
   Icon=vcctl
   Terminal=false
   Type=Application
   Categories=Science;Education;
   EOF
   ```

### Method 3: Source Installation

1. **Install Build Dependencies**
   ```bash
   # Ubuntu/Debian
   sudo apt install git python3-dev python3-venv build-essential \
                    libgtk-3-dev libgirepository1.0-dev pkg-config
   
   # CentOS/RHEL
   sudo yum groupinstall "Development Tools"
   sudo yum install git python3-devel gtk3-devel gobject-introspection-devel
   ```

2. **Clone Repository**
   ```bash
   git clone https://github.com/usnistgov/vcctl.git
   cd vcctl/desktop
   ```

3. **Create Virtual Environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

4. **Install Python Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Build and Install**
   ```bash
   python setup.py build
   sudo python setup.py install
   ```

---

## Windows Installation

### Method 1: Windows Installer (Recommended)

**The Windows installer provides the easiest installation experience with automatic setup and configuration.**

1. **Download Installer**
   ```powershell
   # Download using PowerShell
   Invoke-WebRequest -Uri "https://github.com/usnistgov/vcctl/releases/latest/download/VCCTL-Setup-x64.exe" -OutFile "VCCTL-Setup-x64.exe"
   ```
   
   Or manually:
   - Visit [VCCTL Releases](https://github.com/usnistgov/vcctl/releases/latest)
   - Download `VCCTL-Setup-x64.exe`

2. **Run Installer**
   - Right-click installer and select "Run as administrator"
   - Follow installation wizard steps
   - Accept license agreement
   - Choose installation directory (default: `C:\Program Files\VCCTL`)
   - Select components to install
   - Click "Install"

3. **Post-Installation**
   - Desktop shortcut created automatically
   - Start Menu entry added
   - File associations configured for .vcctl files

### Method 2: Portable Installation

1. **Download Portable Package**
   ```powershell
   # Using PowerShell
   Invoke-WebRequest -Uri "https://github.com/usnistgov/vcctl/releases/latest/download/VCCTL-Portable-x64.zip" -OutFile "VCCTL-Portable.zip"
   ```

2. **Extract Archive**
   ```powershell
   Expand-Archive -Path "VCCTL-Portable.zip" -DestinationPath "C:\VCCTL"
   ```

3. **Run VCCTL**
   ```cmd
   cd C:\VCCTL
   VCCTL.exe
   ```

### Prerequisites Installation

If VCCTL fails to start, install prerequisites:

1. **Visual C++ Redistributable**
   - Download from Microsoft website
   - Install vc_redist.x64.exe

2. **GTK3 Runtime**
   ```powershell
   # Using chocolatey (if installed)
   choco install gtk-runtime
   
   # Or download from https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer
   ```

---

## macOS Installation

### Method 1: DMG Installer (Recommended)

**The DMG installer provides a native macOS installation experience with drag-and-drop installation.**

1. **Download DMG File**
   ```bash
   # Download using curl
   curl -L -o VCCTL-macOS.dmg "https://github.com/usnistgov/vcctl/releases/latest/download/VCCTL-macOS.dmg"
   ```
   
   Or manually:
   - Visit [VCCTL Releases](https://github.com/usnistgov/vcctl/releases)
   - Download `VCCTL-macOS.dmg`

2. **Install Application**
   - Double-click DMG file to mount
   - Drag VCCTL.app to Applications folder
   - Eject DMG file

3. **First Launch**
   - Right-click VCCTL.app and select "Open"
   - Click "Open" when security dialog appears
   - (Required for unsigned applications)

### Method 2: Homebrew Installation

1. **Install Homebrew** (if not already installed)
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. **Add VCCTL Tap**
   ```bash
   brew tap usnistgov/vcctl
   ```

3. **Install VCCTL**
   ```bash
   brew install --cask vcctl
   ```

### Method 3: Source Installation

1. **Install Xcode Command Line Tools**
   ```bash
   xcode-select --install
   ```

2. **Install Dependencies via Homebrew**
   ```bash
   brew install python3 gtk+3 pygobject3 numpy scipy matplotlib
   ```

3. **Clone and Build**
   ```bash
   git clone https://github.com/usnistgov/vcctl.git
   cd vcctl/desktop
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   python setup.py build
   python setup.py install
   ```

---

## Development Installation

For developers or advanced users who want to modify VCCTL:

### Setting Up Development Environment

1. **Install Git and Python**
   ```bash
   # Ensure git and python3 are installed
   git --version
   python3 --version
   ```

2. **Clone Repository**
   ```bash
   git clone https://github.com/usnistgov/vcctl.git
   cd vcctl
   ```

3. **Create Development Environment**
   ```bash
   # Create virtual environment
   python3 -m venv dev-env
   
   # Activate environment
   # Linux/macOS:
   source dev-env/bin/activate
   # Windows:
   dev-env\Scripts\activate
   ```

4. **Install in Development Mode**
   ```bash
   # Install dependencies
   pip install -r requirements-dev.txt
   
   # Install VCCTL in editable mode
   pip install -e .
   ```

5. **Install Development Tools**
   ```bash
   # Code formatting and linting
   pip install black flake8 mypy pytest
   
   # Documentation tools
   pip install sphinx sphinx-rtd-theme
   ```

### Building from Source

1. **Build Documentation**
   ```bash
   cd docs
   make html
   ```

2. **Run Tests**
   ```bash
   pytest tests/
   ```

3. **Format Code**
   ```bash
   black src/
   flake8 src/
   ```

4. **Build Distribution Packages**
   ```bash
   pip install build
   python -m build
   ```

---

## Verification

After installation, verify VCCTL is working correctly:

### Basic Functionality Test

1. **Launch VCCTL**
   - Linux: `vcctl` or use desktop launcher
   - Windows: Start Menu → VCCTL
   - macOS: Applications → VCCTL

2. **Check Interface**
   - Main window opens without errors
   - All tabs are accessible (Home, Materials, Mix Design, etc.)
   - Menu bar and toolbars display correctly

3. **Test Help System**
   - Press F1 to open help
   - Navigate through help topics
   - Search for "cement" in help system

4. **Create Test Material**
   - Go to Materials tab
   - Click "New Cement"
   - Enter basic cement properties
   - Save material successfully

### Performance Test

1. **Generate Small Microstructure**
   - Create simple mix design
   - Generate 50×50×50 μm microstructure
   - Verify generation completes without errors

2. **Check Resource Usage**
   - Monitor memory usage during operations
   - Verify no excessive CPU usage when idle
   - Check disk space usage

### Integration Test

1. **File Operations**
   - Save project file
   - Export material data
   - Import sample data (if available)

2. **Help Documentation**
   - Open user manual
   - Verify all sections load correctly
   - Test search functionality

---

## Troubleshooting

### Common Installation Issues

#### Linux Issues

**Problem**: `ImportError: No module named 'gi'`
```bash
# Solution: Install PyGObject
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0
# or
pip install PyGObject
```

**Problem**: `GLib.Error: g-invoke-error-quark`
```bash
# Solution: Update GTK3 and dependencies
sudo apt update && sudo apt upgrade
sudo apt install --reinstall libgtk-3-0 libgtk-3-dev
```

**Problem**: Permission denied errors
```bash
# Solution: Fix file permissions
sudo chown -R $USER:$USER ~/.local/share/vcctl
chmod -R 755 ~/.local/share/vcctl
```

#### Windows Issues

**Problem**: "VCCTL.exe - Entry Point Not Found"
```
Solution: Install Visual C++ Redistributable 2019
Download from: https://aka.ms/vs/16/release/vc_redist.x64.exe
```

**Problem**: "GTK libraries not found"
```
Solution: Install GTK3 Runtime
Download GTK3 installer for Windows
Or use: choco install gtk-runtime
```

**Problem**: DLL load errors
```
Solution: Ensure system PATH includes:
- C:\Program Files\VCCTL\bin
- C:\GTK3\bin (if manually installed)
```

#### macOS Issues

**Problem**: "VCCTL.app is damaged and can't be opened"
```bash
# Solution: Remove quarantine attribute
xattr -dr com.apple.quarantine /Applications/VCCTL.app
```

**Problem**: Python framework issues
```bash
# Solution: Reinstall Python via Homebrew
brew uninstall python3
brew install python3
```

**Problem**: GTK theme issues
```bash
# Solution: Set GTK theme environment variable
export GTK_THEME=Adwaita:light
```

### Performance Issues

**Problem**: Slow startup
- Check antivirus software (exclude VCCTL directory)
- Verify SSD has sufficient free space
- Update graphics drivers

**Problem**: High memory usage
- Reduce microstructure system size
- Close other applications
- Increase virtual memory/swap

**Problem**: Graphics rendering issues
- Update graphics drivers
- Check OpenGL support: `glxinfo | grep OpenGL`
- Disable GPU acceleration if necessary

### Network Issues

**Problem**: Update check fails
- Check internet connectivity
- Verify firewall settings
- Use proxy settings if required

**Problem**: Package download fails
- Try different mirror/repository
- Check DNS resolution
- Use manual download method

---

## Uninstallation

### Linux Uninstallation

#### Package Manager Installation
```bash
# Ubuntu/Debian
sudo apt remove vcctl-desktop
sudo apt autoremove

# CentOS/RHEL/Fedora
sudo yum remove vcctl-desktop
# or
sudo dnf remove vcctl-desktop
```

#### AppImage Installation
```bash
# Remove AppImage file
rm ~/Applications/VCCTL-x86_64.AppImage
rm ~/.local/share/applications/vcctl.desktop

# Remove user data (optional)
rm -rf ~/.local/share/vcctl
rm -rf ~/.config/vcctl
```

#### Source Installation
```bash
# If installed system-wide
sudo pip uninstall vcctl

# If installed in virtual environment
rm -rf vcctl-dev-env

# Remove user data
rm -rf ~/.local/share/vcctl
```

### Windows Uninstallation

#### Installer Version
1. Control Panel → Programs and Features
2. Select "VCCTL" from list
3. Click "Uninstall"
4. Follow uninstaller prompts

#### Portable Version
1. Delete VCCTL folder
2. Remove desktop shortcuts
3. Clear registry entries (optional):
   ```cmd
   reg delete "HKEY_CURRENT_USER\Software\VCCTL" /f
   ```

#### Clean Removal
```cmd
# Remove user data
rmdir /s "%APPDATA%\VCCTL"
rmdir /s "%LOCALAPPDATA%\VCCTL"

# Remove temporary files
rmdir /s "%TEMP%\VCCTL"
```

### macOS Uninstallation

#### Application Bundle
```bash
# Remove application
rm -rf /Applications/VCCTL.app

# Remove user data
rm -rf ~/Library/Application\ Support/VCCTL
rm -rf ~/Library/Preferences/gov.nist.vcctl.plist
rm -rf ~/Library/Caches/gov.nist.vcctl
```

#### Homebrew Installation
```bash
brew uninstall --cask vcctl
brew untap usnistgov/vcctl
```

#### Complete Cleanup
```bash
# Remove all VCCTL-related files
find ~ -name "*vcctl*" -type f -delete 2>/dev/null
find ~ -name "*VCCTL*" -type d -exec rm -rf {} + 2>/dev/null
```

---

## Support and Resources

### Getting Help

- **Documentation**: [VCCTL User Manual](USER_MANUAL.md)
- **GitHub Issues**: [Report bugs and request features](https://github.com/usnistgov/vcctl/issues)
- **NIST Contact**: [Building and Fire Research Laboratory](https://www.nist.gov/laboratories/engineering-laboratory/smart-connected-systems-division/inorganic-materials-group)

### Community Resources

- **User Forums**: Discussion and community support
- **Video Tutorials**: Step-by-step installation guides
- **Training Materials**: Workshop presentations and examples
- **Research Papers**: Academic publications using VCCTL

### Professional Support

- **Consulting Services**: Custom development and training
- **Enterprise Support**: Priority support for organizations
- **Training Courses**: Hands-on workshops and certification

---

**Document Version**: 1.0  
**Last Updated**: [Current Date]  
**Maintained by**: VCCTL Development Team, NIST
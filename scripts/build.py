#!/usr/bin/env python3
"""
Cross-platform build script for VCCTL
Handles building distribution packages for all supported platforms
"""

import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


class VCCTLBuilder:
    """Build system for VCCTL distribution packages."""
    
    def __init__(self, project_root=None):
        self.project_root = Path(project_root) if project_root else Path(__file__).parent.parent
        self.build_dir = self.project_root / "build"
        self.dist_dir = self.project_root / "dist"
        self.current_platform = platform.system().lower()
        
        # Create build directories
        self.build_dir.mkdir(exist_ok=True)
        self.dist_dir.mkdir(exist_ok=True)
    
    def clean(self):
        """Clean build artifacts."""
        print("🧹 Cleaning build artifacts...")
        
        # Remove build directories
        if self.build_dir.exists():
            shutil.rmtree(self.build_dir)
        if self.dist_dir.exists():
            shutil.rmtree(self.dist_dir)
        
        # Remove PyInstaller cache
        pycache_dirs = list(self.project_root.rglob("__pycache__"))
        for cache_dir in pycache_dirs:
            shutil.rmtree(cache_dir)
        
        print("✅ Build artifacts cleaned")
    
    def install_build_dependencies(self):
        """Install dependencies required for building."""
        print("📦 Installing build dependencies...")
        
        build_deps = [
            "pyinstaller>=5.13.0",
            "setuptools>=68.0.0",
            "wheel>=0.41.0",
        ]
        
        # Platform-specific dependencies
        if self.current_platform == "linux":
            build_deps.extend([
                "python-appimage>=1.2.0",
            ])
        elif self.current_platform == "windows":
            build_deps.extend([
                "pywin32>=306",
                "pywin32-ctypes>=0.2.2",
            ])
        
        for dep in build_deps:
            subprocess.run([sys.executable, "-m", "pip", "install", dep], check=True)
        
        print("✅ Build dependencies installed")
    
    def build_executable(self):
        """Build standalone executable using PyInstaller."""
        print("🔨 Building standalone executable...")
        
        spec_file = self.project_root / "vcctl.spec"
        if not spec_file.exists():
            raise FileNotFoundError(f"PyInstaller spec file not found: {spec_file}")
        
        # Run PyInstaller
        cmd = [
            "pyinstaller",
            "--clean",
            "--noconfirm",
            str(spec_file)
        ]
        
        subprocess.run(cmd, cwd=self.project_root, check=True)
        print("✅ Standalone executable built")
    
    def build_linux_appimage(self):
        """Build Linux AppImage package."""
        if self.current_platform != "linux":
            print("⚠️  Skipping Linux AppImage (not on Linux)")
            return
        
        print("🐧 Building Linux AppImage...")
        
        # Create AppDir structure
        appdir = self.build_dir / "VCCTL.AppDir"
        appdir.mkdir(exist_ok=True)
        
        # Copy executable and dependencies
        dist_vcctl = self.dist_dir / "vcctl"
        if dist_vcctl.exists():
            shutil.copytree(dist_vcctl, appdir / "usr" / "bin" / "vcctl")
        
        # Create desktop entry
        desktop_content = """[Desktop Entry]
Type=Application
Name=VCCTL
Comment=Virtual Cement and Concrete Testing Laboratory
Exec=vcctl
Icon=vcctl
Categories=Science;Education;Engineering;
Terminal=false
StartupWMClass=vcctl
"""
        
        (appdir / "vcctl.desktop").write_text(desktop_content)
        
        # Create AppRun script
        apprun_content = """#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"
export PATH="${HERE}/usr/bin:${PATH}"
export LD_LIBRARY_PATH="${HERE}/usr/lib:${LD_LIBRARY_PATH}"
export PYTHONPATH="${HERE}/usr/lib/python3/site-packages:${PYTHONPATH}"
cd "${HERE}"
exec "${HERE}/usr/bin/vcctl/vcctl" "$@"
"""
        
        apprun_file = appdir / "AppRun"
        apprun_file.write_text(apprun_content)
        apprun_file.chmod(0o755)
        
        # Copy icon
        icon_src = self.project_root / "src" / "app" / "resources" / "icons" / "vcctl.png"
        if icon_src.exists():
            shutil.copy2(icon_src, appdir / "vcctl.png")
        
        # Build AppImage using appimagetool
        appimage_path = self.dist_dir / "VCCTL-x86_64.AppImage"
        try:
            subprocess.run([
                "appimagetool",
                str(appdir),
                str(appimage_path)
            ], check=True)
            print("✅ Linux AppImage built successfully")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("⚠️  appimagetool not found. Install AppImageKit to build AppImage")
    
    def build_windows_installer(self):
        """Build Windows installer using NSIS."""
        if self.current_platform != "windows":
            print("⚠️  Skipping Windows installer (not on Windows)")
            return
        
        print("🪟 Building Windows installer...")
        
        # Create NSIS script
        nsis_script = self.build_dir / "vcctl_installer.nsi"
        nsis_content = """
!define APPNAME "VCCTL"
!define COMPANYNAME "NIST"
!define DESCRIPTION "Virtual Cement and Concrete Testing Laboratory"
!define VERSIONMAJOR 1
!define VERSIONMINOR 0
!define VERSIONBUILD 0

!define HELPURL "https://vcctl.nist.gov/help"
!define UPDATEURL "https://vcctl.nist.gov/updates"
!define ABOUTURL "https://vcctl.nist.gov/about"

!define INSTALLSIZE 100000  # Estimated size in KB

RequestExecutionLevel admin
InstallDir "$PROGRAMFILES64\\${COMPANYNAME}\\${APPNAME}"

Name "${APPNAME}"
Icon "vcctl.ico"
outFile "..\\dist\\VCCTL-Setup-x64.exe"

page directory
page instfiles

section "install"
    setOutPath $INSTDIR
    
    # Copy application files
    file /r "..\\dist\\vcctl\\*.*"
    
    # Create desktop shortcut
    createShortCut "$DESKTOP\\VCCTL.lnk" "$INSTDIR\\vcctl.exe" "" "$INSTDIR\\vcctl.exe" 0
    
    # Create start menu shortcut
    createDirectory "$SMPROGRAMS\\${COMPANYNAME}"
    createShortCut "$SMPROGRAMS\\${COMPANYNAME}\\${APPNAME}.lnk" "$INSTDIR\\vcctl.exe" "" "$INSTDIR\\vcctl.exe" 0
    
    # Registry entries for Add/Remove Programs
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "DisplayName" "${APPNAME}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "UninstallString" "$INSTDIR\\uninstall.exe"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "InstallLocation" "$INSTDIR"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "DisplayIcon" "$INSTDIR\\vcctl.exe"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "Publisher" "${COMPANYNAME}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "HelpLink" "${HELPURL}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "URLUpdateInfo" "${UPDATEURL}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "URLInfoAbout" "${ABOUTURL}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "DisplayVersion" "${VERSIONMAJOR}.${VERSIONMINOR}.${VERSIONBUILD}"
    WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "VersionMajor" ${VERSIONMAJOR}
    WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "VersionMinor" ${VERSIONMINOR}
    WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "NoModify" 1
    WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "NoRepair" 1
    WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "EstimatedSize" ${INSTALLSIZE}
    
    # Create uninstaller
    writeUninstaller "$INSTDIR\\uninstall.exe"
sectionEnd

section "uninstall"
    delete "$DESKTOP\\VCCTL.lnk"
    delete "$SMPROGRAMS\\${COMPANYNAME}\\${APPNAME}.lnk"
    rmDir "$SMPROGRAMS\\${COMPANYNAME}"
    
    # Remove application files
    rmDir /r "$INSTDIR"
    
    # Remove registry entries
    DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}"
sectionEnd
"""
        
        nsis_script.write_text(nsis_content)
        
        # Run NSIS to create installer
        try:
            subprocess.run([
                "makensis",
                str(nsis_script)
            ], check=True)
            print("✅ Windows installer built successfully")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("⚠️  NSIS not found. Install NSIS to build Windows installer")
    
    def build_macos_dmg(self):
        """Build macOS DMG installer."""
        if self.current_platform != "darwin":
            print("⚠️  Skipping macOS DMG (not on macOS)")
            return
        
        print("🍎 Building macOS DMG...")
        
        app_bundle = self.dist_dir / "VCCTL.app"
        if not app_bundle.exists():
            print("❌ VCCTL.app not found. Build executable first.")
            return
        
        # Create DMG staging directory
        dmg_staging = self.build_dir / "dmg_staging"
        dmg_staging.mkdir(exist_ok=True)
        
        # Copy app bundle to staging
        shutil.copytree(app_bundle, dmg_staging / "VCCTL.app", dirs_exist_ok=True)
        
        # Create Applications symlink
        (dmg_staging / "Applications").symlink_to("/Applications")
        
        # Create DMG
        dmg_path = self.dist_dir / "VCCTL-macOS.dmg"
        subprocess.run([
            "hdiutil", "create", "-volname", "VCCTL",
            "-srcfolder", str(dmg_staging),
            "-ov", "-format", "UDZO",
            str(dmg_path)
        ], check=True)
        
        print("✅ macOS DMG built successfully")
    
    def build_all(self):
        """Build packages for current platform."""
        print(f"🚀 Building VCCTL for {self.current_platform}...")
        
        self.install_build_dependencies()
        self.build_executable()
        
        if self.current_platform == "linux":
            self.build_linux_appimage()
        elif self.current_platform == "windows":
            self.build_windows_installer()
        elif self.current_platform == "darwin":
            self.build_macos_dmg()
        
        print("🎉 Build completed successfully!")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Build VCCTL distribution packages")
    parser.add_argument("--clean", action="store_true", help="Clean build artifacts")
    parser.add_argument("--platform", choices=["linux", "windows", "macos", "all"],
                       default="current", help="Target platform to build")
    parser.add_argument("--project-root", type=str, help="Project root directory")
    
    args = parser.parse_args()
    
    builder = VCCTLBuilder(args.project_root)
    
    if args.clean:
        builder.clean()
        return
    
    if args.platform == "current" or args.platform == "all":
        builder.build_all()
    else:
        print(f"Building for {args.platform} is not fully implemented yet")


if __name__ == "__main__":
    main()
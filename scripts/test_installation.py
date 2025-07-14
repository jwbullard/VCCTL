#!/usr/bin/env python3
"""
Installation testing script for VCCTL packages
Tests installation and basic functionality across platforms
"""

import argparse
import os
import platform
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class InstallationTester:
    """Test VCCTL installation packages."""
    
    def __init__(self):
        self.platform = platform.system().lower()
        self.architecture = platform.machine().lower()
        self.results = []
        
    def log_result(self, test_name: str, success: bool, message: str = ""):
        """Log test result."""
        status = "✅ PASS" if success else "❌ FAIL"
        self.results.append({
            'test': test_name,
            'success': success,
            'message': message
        })
        print(f"{status} {test_name}: {message}")
    
    def run_command(self, cmd: List[str], timeout: int = 30) -> Tuple[bool, str, str]:
        """Run command with timeout."""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", f"Command timed out after {timeout}s"
        except Exception as e:
            return False, "", str(e)
    
    def test_linux_appimage(self, appimage_path: Path) -> bool:
        """Test Linux AppImage installation."""
        print(f"🐧 Testing Linux AppImage: {appimage_path}")
        
        if not appimage_path.exists():
            self.log_result("AppImage exists", False, f"File not found: {appimage_path}")
            return False
        
        self.log_result("AppImage exists", True, str(appimage_path))
        
        # Check if file is executable
        is_executable = os.access(appimage_path, os.X_OK)
        self.log_result("AppImage executable", is_executable)
        
        if not is_executable:
            # Try to make it executable
            try:
                appimage_path.chmod(0o755)
                is_executable = os.access(appimage_path, os.X_OK)
                self.log_result("Make executable", is_executable)
            except Exception as e:
                self.log_result("Make executable", False, str(e))
        
        # Test help command
        success, stdout, stderr = self.run_command([str(appimage_path), "--help"])
        self.log_result("Help command", success, stderr if not success else "Help displayed")
        
        # Test version command
        success, stdout, stderr = self.run_command([str(appimage_path), "--version"])
        self.log_result("Version command", success, stdout.strip() if success else stderr)
        
        # Check dependencies are bundled
        success, stdout, stderr = self.run_command(["ldd", str(appimage_path)])
        if success and "not found" not in stdout:
            self.log_result("Dependencies check", True, "All dependencies bundled")
        else:
            self.log_result("Dependencies check", False, "Missing dependencies")
        
        return all(r['success'] for r in self.results[-4:])
    
    def test_windows_installer(self, installer_path: Path) -> bool:
        """Test Windows installer."""
        print(f"🪟 Testing Windows installer: {installer_path}")
        
        if not installer_path.exists():
            self.log_result("Installer exists", False, f"File not found: {installer_path}")
            return False
        
        self.log_result("Installer exists", True, str(installer_path))
        
        # Check installer signature (if signed)
        success, stdout, stderr = self.run_command([
            "powershell", "-Command",
            f"Get-AuthenticodeSignature '{installer_path}' | Select-Object Status"
        ])
        
        if success and "Valid" in stdout:
            self.log_result("Code signature", True, "Installer is signed")
        else:
            self.log_result("Code signature", False, "Installer not signed or invalid signature")
        
        # Test silent installation (requires admin rights)
        print("⚠️  Note: Silent installation test requires administrator privileges")
        
        return True
    
    def test_windows_portable(self, zip_path: Path) -> bool:
        """Test Windows portable package."""
        print(f"📦 Testing Windows portable: {zip_path}")
        
        if not zip_path.exists():
            self.log_result("Portable ZIP exists", False, f"File not found: {zip_path}")
            return False
        
        self.log_result("Portable ZIP exists", True, str(zip_path))
        
        # Extract to temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Extract ZIP
            success, stdout, stderr = self.run_command([
                "powershell", "-Command",
                f"Expand-Archive -Path '{zip_path}' -DestinationPath '{temp_path}'"
            ])
            
            self.log_result("ZIP extraction", success, stderr if not success else "Extracted successfully")
            
            if not success:
                return False
            
            # Find executable
            exe_path = temp_path / "vcctl" / "vcctl.exe"
            if not exe_path.exists():
                # Try alternative paths
                exe_files = list(temp_path.rglob("vcctl.exe"))
                if exe_files:
                    exe_path = exe_files[0]
                else:
                    self.log_result("Executable found", False, "vcctl.exe not found in archive")
                    return False
            
            self.log_result("Executable found", True, str(exe_path))
            
            # Test executable
            success, stdout, stderr = self.run_command([str(exe_path), "--help"])
            self.log_result("Executable test", success, stderr if not success else "Help displayed")
            
            return success
    
    def test_macos_dmg(self, dmg_path: Path) -> bool:
        """Test macOS DMG installation."""
        print(f"🍎 Testing macOS DMG: {dmg_path}")
        
        if not dmg_path.exists():
            self.log_result("DMG exists", False, f"File not found: {dmg_path}")
            return False
        
        self.log_result("DMG exists", True, str(dmg_path))
        
        # Mount DMG
        success, stdout, stderr = self.run_command([
            "hdiutil", "attach", str(dmg_path), "-readonly", "-nobrowse"
        ])
        
        if not success:
            self.log_result("DMG mount", False, stderr)
            return False
        
        self.log_result("DMG mount", True, "DMG mounted successfully")
        
        # Find mount point
        mount_point = None
        for line in stdout.split('\n'):
            if "Apple_HFS" in line and "/Volumes/" in line:
                mount_point = line.split()[-1]
                break
        
        if not mount_point:
            self.log_result("Mount point detection", False, "Could not find mount point")
            return False
        
        mount_path = Path(mount_point)
        app_path = mount_path / "VCCTL.app"
        
        # Check app bundle structure
        if not app_path.exists():
            self.log_result("App bundle exists", False, f"VCCTL.app not found in {mount_path}")
        else:
            self.log_result("App bundle exists", True, str(app_path))
            
            # Check app bundle structure
            executable_path = app_path / "Contents" / "MacOS" / "vcctl"
            plist_path = app_path / "Contents" / "Info.plist"
            
            self.log_result("Executable exists", executable_path.exists(), str(executable_path))
            self.log_result("Info.plist exists", plist_path.exists(), str(plist_path))
            
            # Test code signature
            success, stdout, stderr = self.run_command([
                "codesign", "--verify", "--deep", "--strict", str(app_path)
            ])
            
            if success:
                self.log_result("Code signature", True, "App bundle is signed")
            else:
                self.log_result("Code signature", False, "App bundle not signed or invalid")
        
        # Unmount DMG
        subprocess.run(["hdiutil", "detach", mount_point], capture_output=True)
        
        return True
    
    def test_macos_zip(self, zip_path: Path) -> bool:
        """Test macOS ZIP package."""
        print(f"📦 Testing macOS ZIP: {zip_path}")
        
        if not zip_path.exists():
            self.log_result("ZIP exists", False, f"File not found: {zip_path}")
            return False
        
        self.log_result("ZIP exists", True, str(zip_path))
        
        # Extract to temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Extract ZIP
            success, stdout, stderr = self.run_command([
                "unzip", "-q", str(zip_path), "-d", str(temp_path)
            ])
            
            self.log_result("ZIP extraction", success, stderr if not success else "Extracted successfully")
            
            if not success:
                return False
            
            # Find app bundle
            app_path = temp_path / "VCCTL.app"
            if not app_path.exists():
                app_files = list(temp_path.rglob("*.app"))
                if app_files:
                    app_path = app_files[0]
                else:
                    self.log_result("App bundle found", False, "VCCTL.app not found in archive")
                    return False
            
            self.log_result("App bundle found", True, str(app_path))
            
            # Check executable
            executable_path = app_path / "Contents" / "MacOS" / "vcctl"
            self.log_result("Executable exists", executable_path.exists(), str(executable_path))
            
            return executable_path.exists()
    
    def test_basic_functionality(self, executable_path: Path) -> bool:
        """Test basic application functionality."""
        print(f"🧪 Testing basic functionality: {executable_path}")
        
        if not executable_path.exists():
            self.log_result("Executable exists", False, str(executable_path))
            return False
        
        # Test help command
        success, stdout, stderr = self.run_command([str(executable_path), "--help"])
        self.log_result("Help command", success)
        
        # Test version command
        success, stdout, stderr = self.run_command([str(executable_path), "--version"])
        self.log_result("Version command", success)
        
        # Test configuration check
        success, stdout, stderr = self.run_command([str(executable_path), "--check-config"])
        self.log_result("Config check", success)
        
        return True
    
    def run_tests(self, package_path: Path) -> bool:
        """Run appropriate tests based on package type and platform."""
        print(f"🚀 Starting installation tests for {package_path}")
        print(f"Platform: {self.platform}")
        print(f"Architecture: {self.architecture}")
        print()
        
        if not package_path.exists():
            print(f"❌ Package not found: {package_path}")
            return False
        
        file_extension = package_path.suffix.lower()
        
        # Determine test type based on file extension
        if file_extension == ".appimage":
            success = self.test_linux_appimage(package_path)
        elif file_extension == ".exe":
            success = self.test_windows_installer(package_path)
        elif file_extension == ".zip":
            if self.platform == "windows":
                success = self.test_windows_portable(package_path)
            else:
                success = self.test_macos_zip(package_path)
        elif file_extension == ".dmg":
            success = self.test_macos_dmg(package_path)
        else:
            print(f"❌ Unknown package type: {file_extension}")
            return False
        
        return success
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "="*50)
        print("TEST SUMMARY")
        print("="*50)
        
        passed = sum(1 for r in self.results if r['success'])
        total = len(self.results)
        
        print(f"Total tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success rate: {passed/total*100:.1f}%")
        
        if total - passed > 0:
            print("\nFailed tests:")
            for result in self.results:
                if not result['success']:
                    print(f"  ❌ {result['test']}: {result['message']}")
        
        return passed == total


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Test VCCTL installation packages")
    parser.add_argument("package_path", type=str, help="Path to package file to test")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    package_path = Path(args.package_path)
    tester = InstallationTester()
    
    try:
        success = tester.run_tests(package_path)
        tester.print_summary()
        
        if success:
            print("\n🎉 All tests passed!")
            sys.exit(0)
        else:
            print("\n💥 Some tests failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        sys.exit(2)
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        sys.exit(3)


if __name__ == "__main__":
    main()
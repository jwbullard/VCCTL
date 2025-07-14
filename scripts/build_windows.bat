@echo off
REM Windows executable and installer build script for VCCTL
REM Creates a Windows executable and NSIS installer package

setlocal enabledelayedexpansion

REM Colors for output (limited in batch)
set "GREEN=[92m"
set "YELLOW=[93m"
set "RED=[91m"
set "BLUE=[94m"
set "NC=[0m"

REM Configuration
set "PROJECT_ROOT=%~dp0.."
set "BUILD_DIR=%PROJECT_ROOT%\build"
set "DIST_DIR=%PROJECT_ROOT%\dist"

echo %BLUE%🪟 Building VCCTL Windows Package%NC%
echo Project root: %PROJECT_ROOT%

REM Create build directories
if not exist "%BUILD_DIR%" mkdir "%BUILD_DIR%"
if not exist "%DIST_DIR%" mkdir "%DIST_DIR%"

REM Install build dependencies
echo %YELLOW%📦 Installing build dependencies...%NC%
pip install pyinstaller>=5.13.0 setuptools wheel pywin32 pywin32-ctypes
if %errorlevel% neq 0 (
    echo %RED%❌ Failed to install dependencies%NC%
    exit /b 1
)

REM Build standalone executable
echo %YELLOW%🔨 Building standalone executable...%NC%
cd /d "%PROJECT_ROOT%"
pyinstaller --clean --noconfirm vcctl.spec
if %errorlevel% neq 0 (
    echo %RED%❌ Failed to build executable%NC%
    exit /b 1
)

REM Check if executable was created
if not exist "%DIST_DIR%\vcctl\vcctl.exe" (
    echo %RED%❌ Executable not found in %DIST_DIR%\vcctl\vcctl.exe%NC%
    exit /b 1
)

REM Create portable ZIP package
echo %YELLOW%📦 Creating portable ZIP package...%NC%
cd /d "%DIST_DIR%"
if exist "VCCTL-Portable-x64.zip" del "VCCTL-Portable-x64.zip"
powershell -command "Compress-Archive -Path 'vcctl' -DestinationPath 'VCCTL-Portable-x64.zip'"
if %errorlevel% neq 0 (
    echo %YELLOW%⚠️  Failed to create ZIP package%NC%
) else (
    echo %GREEN%✅ Portable ZIP package created: VCCTL-Portable-x64.zip%NC%
)

REM Create NSIS installer script
echo %YELLOW%📝 Creating NSIS installer script...%NC%

set "NSIS_SCRIPT=%BUILD_DIR%\vcctl_installer.nsi"

(
echo ^!define APPNAME "VCCTL"
echo ^!define COMPANYNAME "NIST"
echo ^!define DESCRIPTION "Virtual Cement and Concrete Testing Laboratory"
echo ^!define VERSIONMAJOR 1
echo ^!define VERSIONMINOR 0
echo ^!define VERSIONBUILD 0
echo.
echo ^!define HELPURL "https://vcctl.nist.gov/help"
echo ^!define UPDATEURL "https://vcctl.nist.gov/updates"
echo ^!define ABOUTURL "https://vcctl.nist.gov/about"
echo.
echo ^!define INSTALLSIZE 100000
echo.
echo RequestExecutionLevel admin
echo InstallDir "$PROGRAMFILES64\${COMPANYNAME}\${APPNAME}"
echo.
echo Name "${APPNAME}"
echo outFile "..\dist\VCCTL-Setup-x64.exe"
echo.
echo page directory
echo page instfiles
echo.
echo section "install"
echo     setOutPath $INSTDIR
echo.
echo     # Copy application files
echo     file /r "..\dist\vcctl\*.*"
echo.
echo     # Create desktop shortcut
echo     createShortCut "$DESKTOP\VCCTL.lnk" "$INSTDIR\vcctl.exe" "" "$INSTDIR\vcctl.exe" 0
echo.
echo     # Create start menu shortcut
echo     createDirectory "$SMPROGRAMS\${COMPANYNAME}"
echo     createShortCut "$SMPROGRAMS\${COMPANYNAME}\${APPNAME}.lnk" "$INSTDIR\vcctl.exe" "" "$INSTDIR\vcctl.exe" 0
echo.
echo     # Registry entries for Add/Remove Programs
echo     WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayName" "${APPNAME}"
echo     WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "UninstallString" "$INSTDIR\uninstall.exe"
echo     WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "InstallLocation" "$INSTDIR"
echo     WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayIcon" "$INSTDIR\vcctl.exe"
echo     WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "Publisher" "${COMPANYNAME}"
echo     WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "HelpLink" "${HELPURL}"
echo     WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "URLUpdateInfo" "${UPDATEURL}"
echo     WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "URLInfoAbout" "${ABOUTURL}"
echo     WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayVersion" "${VERSIONMAJOR}.${VERSIONMINOR}.${VERSIONBUILD}"
echo     WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "VersionMajor" ${VERSIONMAJOR}
echo     WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "VersionMinor" ${VERSIONMINOR}
echo     WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "NoModify" 1
echo     WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "NoRepair" 1
echo     WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "EstimatedSize" ${INSTALLSIZE}
echo.
echo     # Create uninstaller
echo     writeUninstaller "$INSTDIR\uninstall.exe"
echo sectionEnd
echo.
echo section "uninstall"
echo     delete "$DESKTOP\VCCTL.lnk"
echo     delete "$SMPROGRAMS\${COMPANYNAME}\${APPNAME}.lnk"
echo     rmDir "$SMPROGRAMS\${COMPANYNAME}"
echo.
echo     # Remove application files
echo     rmDir /r "$INSTDIR"
echo.
echo     # Remove registry entries
echo     DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}"
echo sectionEnd
) > "%NSIS_SCRIPT%"

REM Build NSIS installer if NSIS is available
echo %YELLOW%🏗️  Building NSIS installer...%NC%
where makensis >nul 2>nul
if %errorlevel% equ 0 (
    cd /d "%BUILD_DIR%"
    makensis vcctl_installer.nsi
    if %errorlevel% equ 0 (
        echo %GREEN%✅ Windows installer built successfully: VCCTL-Setup-x64.exe%NC%
    ) else (
        echo %RED%❌ Failed to build NSIS installer%NC%
    )
) else (
    echo %YELLOW%⚠️  NSIS not found. Install NSIS to build installer%NC%
    echo %YELLOW%   Download from: https://nsis.sourceforge.io/%NC%
)

REM Display results
echo.
echo %GREEN%🎉 Windows build completed!%NC%
echo.
echo %BLUE%📦 Built packages:%NC%
if exist "%DIST_DIR%\vcctl" (
    echo   - Standalone executable: %DIST_DIR%\vcctl\vcctl.exe
)
if exist "%DIST_DIR%\VCCTL-Portable-x64.zip" (
    for %%I in ("%DIST_DIR%\VCCTL-Portable-x64.zip") do echo   - Portable ZIP: %%~nxI ^(%%~zI bytes^)
)
if exist "%DIST_DIR%\VCCTL-Setup-x64.exe" (
    for %%I in ("%DIST_DIR%\VCCTL-Setup-x64.exe") do echo   - Windows installer: %%~nxI ^(%%~zI bytes^)
)

REM Test executable
echo.
echo %YELLOW%🧪 Testing executable...%NC%
"%DIST_DIR%\vcctl\vcctl.exe" --help >nul 2>nul
if %errorlevel% equ 0 (
    echo %GREEN%✅ Executable test passed%NC%
) else (
    echo %YELLOW%⚠️  Executable test failed (may require GUI environment)%NC%
)

endlocal
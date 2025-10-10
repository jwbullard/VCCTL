@echo off
REM Windows PyInstaller Build Script for VCCTL
REM This script must be run from MSYS2 MinGW 64-bit terminal

echo Building VCCTL for Windows...
cd /d %~dp0

REM Run PyInstaller with Python from MSYS2
C:\msys64\mingw64\bin\python.exe -m PyInstaller vcctl.spec

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Build successful!
    echo Package location: dist\VCCTL\
    echo.
) else (
    echo.
    echo Build failed with error code %ERRORLEVEL%
    echo.
)

pause

@echo off
REM ============================================================
REM Neuroscience Test Maker - Setup and Run Script
REM ============================================================
REM This script checks for Python dependencies and installs
REM missing packages before launching the application.
REM ============================================================

echo.
echo ============================================================
echo   Neuroscience Test Maker - Setup and Launch
echo ============================================================
echo.

REM Check for Python - prioritize 3.12 and 3.11 for best compatibility
set PYTHON_CMD=python

echo Checking for compatible Python versions...
echo.

REM Try Python 3.12 first (best compatibility)
py -3.12 --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_CMD=py -3.12
    echo [OK] Found Python 3.12 ^(recommended^)
    py -3.12 --version
    goto :python_found
)

REM Try Python 3.11 next (also good)
py -3.11 --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_CMD=py -3.11
    echo [OK] Found Python 3.11 ^(recommended^)
    py -3.11 --version
    goto :python_found
)

REM Fall back to whatever python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH!
    echo.
    echo Please install Python 3.11 or 3.12 from:
    echo https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

echo [WARNING] Using default Python ^(may have compatibility issues^)
python --version
echo.
echo NOTE: Python 3.11 or 3.12 recommended for best pygame compatibility.
echo If you have issues, install Python 3.12 from python.org
echo.

:python_found
echo.

REM Check if pip is available
%PYTHON_CMD% -m pip --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] pip is not available!
    echo.
    echo Please reinstall Python with pip enabled.
    pause
    exit /b 1
)

echo [OK] pip found:
%PYTHON_CMD% -m pip --version
echo.

REM Check if requirements.txt exists
if not exist "requirements.txt" (
    echo [ERROR] requirements.txt not found!
    echo.
    echo Please make sure you're running this script from the
    echo Neuroscience-Test-Maker directory.
    pause
    exit /b 1
)

echo ============================================================
echo   Checking and Installing Dependencies
echo ============================================================
echo.

REM Install/upgrade required packages
echo Installing required packages from requirements.txt...
echo.
echo [Note] If pygame fails to install, see docs/TROUBLESHOOTING.md
echo.
%PYTHON_CMD% -m pip install --upgrade pip setuptools wheel --quiet --disable-pip-version-check
%PYTHON_CMD% -m pip install -r requirements.txt --prefer-binary

if errorlevel 1 (
    echo.
    echo ============================================================
    echo [WARNING] Some packages failed to install!
    echo ============================================================
    echo.
    echo Common issue: pygame doesn't support Python 3.14 yet.
    echo.
    echo SOLUTIONS:
    echo 1. Try installing pygame from wheel:
    echo    python -m pip install pygame --only-binary :all:
    echo.
    echo 2. Use Python 3.11 or 3.12 ^(recommended^):
    echo    Download from https://www.python.org/downloads/
    echo.
    echo 3. Continue anyway ^(app may work if pygame installed^)
    echo.
    pause
    
    REM Try to install pygame from prebuilt wheel as fallback
    echo.
    echo Attempting to install pygame from prebuilt wheel...
    python -m pip install pygame --only-binary :all: --disable-pip-version-check
    
    if errorlevel 1 (
        echo [WARNING] Pygame installation failed. The app may not run correctly.
    ) else (
    %PYTHON_CMD%ho [OK] Pygame installed from prebuilt wheel!
    )
    echo.
) else (
    echo.
    echo [OK] All dependencies installed successfully!
    echo.
)

echo ============================================================
echo   Launching Neuroscience Test Maker
echo ============================================================
echo.

REM Launch the application
%PYTHON_CMD% launcher.py

REM Check if launcher exited with error
if errorlevel 1 (
    echo.
    echo [ERROR] Application exited with an error.
    echo.
    pause
    exit /b 1
)

echo.
echo Application closed successfully.
echo.
pause

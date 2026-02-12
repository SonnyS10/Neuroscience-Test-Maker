@echo off
REM ============================================================
REM Quick Pygame Fix for Python 3.14+
REM ============================================================
REM This script attempts to install pygame using prebuilt wheels
REM which avoids compilation issues with newer Python versions
REM ============================================================

echo.
echo ============================================================
echo   Pygame Installation Fix for Python 3.14+
echo ============================================================
echo.

python --version
echo.

echo Attempting to install pygame from prebuilt wheel...
echo This should work on Python 3.14+ without compilation.
echo.

python -m pip install --upgrade pip setuptools wheel
python -m pip uninstall pygame -y
python -m pip install pygame --only-binary :all:

if errorlevel 1 (
    echo.
    echo ============================================================
    echo [ERROR] Pygame wheel installation failed.
    echo ============================================================
    echo.
    echo The issue is that pygame doesn't have prebuilt wheels for
    echo Python 3.14 yet ^(it's too new^).
    echo.
    echo RECOMMENDED SOLUTION:
    echo Install Python 3.11 or 3.12 from:
    echo https://www.python.org/downloads/
    echo.
    echo Then run setup_and_run.bat again.
    echo.
    pause
    exit /b 1
) else (
    echo.
    echo [OK] Pygame installed successfully!
    echo.
    echo Now installing other dependencies...
    python -m pip install Pillow numpy
    echo.
    echo [OK] All dependencies installed!
    echo.
    echo You can now run: setup_and_run.bat
    echo.
    pause
)

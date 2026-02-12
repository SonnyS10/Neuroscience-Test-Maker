# Installation Troubleshooting

## Pygame Installation Issues (Python 3.14+)

### The Problem

If you see errors like:
```
ModuleNotFoundError: No module named 'setuptools._distutils.msvccompiler'
ERROR: Failed to build 'pygame' when getting requirements to build wheel
```

This is because **pygame doesn't fully support Python 3.14 yet** (it's very new). Pygame tries to compile from source and fails due to missing distutils in Python 3.14.

### Solution 1: Use a Stable Python Version (Recommended)

**Download and install Python 3.11 or 3.12:**
1. Go to https://www.python.org/downloads/
2. Download Python 3.11.8 or 3.12.2 (stable releases)
3. Install with "Add Python to PATH" checked
4. Run `setup_and_run.bat` again

### Solution 2: Try Prebuilt Pygame Wheel (May Not Work)

Run the pygame fix script:
```bash
fix_pygame.bat
```

This attempts to install pygame from prebuilt wheels. However, wheels may not be available for Python 3.14 yet.

### Solution 3: Manual Installation

Try installing dependencies one by one:

```bash
# Upgrade pip and tools
python -m pip install --upgrade pip setuptools wheel

# Try pygame from wheel only (no compilation)
python -m pip install pygame --only-binary :all:

# If that fails, try the latest development version
python -m pip install pygame --pre --only-binary :all:

# Install other dependencies
python -m pip install Pillow numpy
```

### Solution 4: Use a Virtual Environment with Python 3.12

If you have multiple Python versions:

```bash
# Create virtual environment with Python 3.12
py -3.12 -m venv venv

# Activate it
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the app
python test_maker.py
```

## Other Common Issues

### Issue: "Python is not recognized"

**Solution:** Add Python to your PATH:
1. Search for "Environment Variables" in Windows
2. Edit the "Path" variable
3. Add Python installation directory (e.g., `C:\Python312\`)
4. Add Scripts directory (e.g., `C:\Python312\Scripts\`)
5. Restart command prompt

### Issue: "pip is not available"

**Solution:** Install pip:
```bash
python -m ensurepip --upgrade
```

### Issue: Missing Visual C++ Build Tools

If you see errors about Visual C++ or MSVCCompiler:

**Solution:** You don't need to install build tools if you use a compatible Python version (3.11-3.12) or prebuilt wheels.

## Checking Your Installation

After installation, verify everything works:

```bash
# Test Python
python --version

# Test pygame
python -c "import pygame; print(pygame.version.ver)"

# Test other packages
python -c "import PIL; import numpy; print('OK')"

# Run the app
python launcher.py
```

## Quick Reference

| Python Version | Pygame Status | Recommendation |
|---------------|---------------|----------------|
| 3.14          | ❌ Not supported | Use 3.12 instead |
| 3.13          | ⚠️ Limited support | Use 3.12 instead |
| 3.12          | ✅ Fully supported | **Recommended** |
| 3.11          | ✅ Fully supported | **Recommended** |
| 3.10          | ✅ Fully supported | OK |
| 3.9 or older  | ⚠️ Deprecated | Upgrade to 3.11/3.12 |

## Still Having Issues?

1. Check you're running the script from the correct directory
2. Try running as Administrator
3. Disable antivirus temporarily during installation
4. Check Windows Defender isn't blocking downloads
5. Ensure you have internet connection for downloading packages

## Alternative: Run Without Installing

If you just want to test the core functionality without pygame:

```bash
# Run tests (don't need pygame)
python tests/test_export.py

# Use demo mode (minimal dependencies)
python demo.py
```

The GUI requires pygame, but the export and timeline features work without it.

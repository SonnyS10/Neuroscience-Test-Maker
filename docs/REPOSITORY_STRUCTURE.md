# Repository Structure

## Overview

This document describes the organization of the Neuroscience Test Maker repository after restructuring for better maintainability and clarity.

## Directory Structure

```
Neuroscience-Test-Maker/
│
├── Root Directory (Application Files)
│   ├── test_maker.py           # Main GUI application
│   ├── export_formats.py       # Multi-format export functionality
│   ├── launcher.py             # Interactive launcher menu
│   ├── demo.py                 # Command-line demo
│   ├── setup_and_run.bat       # Windows setup and launch script
│   ├── requirements.txt        # Python dependencies
│   ├── .gitignore              # Git ignore rules
│   └── README.md               # Main documentation
│
├── docs/                       # Documentation
│   ├── QUICKSTART.md           # Quick start guide for new users
│   ├── EXPORT_FORMATS.md       # Detailed export format specifications
│   ├── SYNCHRONIZATION.md      # Synchronization approach documentation
│   ├── IMPLEMENTATION.md       # Implementation details and design decisions
│   └── AUDIO_FEATURES.md       # Audio stimulus features documentation
│
├── tests/                      # Test Suite
│   ├── test_core.py            # Core timeline and event logic tests
│   ├── test_export.py          # Export functionality tests
│   └── test_audio_features.py  # Audio features tests
│
├── basic_auditory_stimulus/    # Audio Stimulus Module
│   ├── audio_tone_maker.py     # Audio tone generator GUI
│   └── __pycache__/            # Python cache (auto-generated)
│
└── examples/                   # Example Files
    ├── sample_test.json        # Example test configuration
    ├── sample_export_eeglab.txt # Example EEGLAB export
    └── sample_export_eprime.txt # Example E-Prime export
```

## File Purposes

### Root Level Files

**Application Files:**
- `test_maker.py` - Main application with GUI for creating and managing test timelines
- `export_formats.py` - Handles exporting to JSON, EEGLAB, and E-Prime formats
- `launcher.py` - Interactive menu for launching app, demo, or tests
- `demo.py` - Command-line demonstration without GUI

**Setup & Configuration:**
- `setup_and_run.bat` - Automated setup script for Windows users
- `requirements.txt` - Lists all Python package dependencies
- `README.md` - Main documentation and getting started guide

### Documentation (docs/)

All documentation files organized in one location:

- **QUICKSTART.md** - Step-by-step guide for creating your first test
- **EXPORT_FORMATS.md** - Complete guide to all export formats (EEGLAB, E-Prime, JSON)
- **SYNCHRONIZATION.md** - Detailed explanation of timeline-based synchronization
- **IMPLEMENTATION.md** - Technical implementation details and architecture
- **AUDIO_FEATURES.md** - Audio stimulus generation features

### Tests (tests/)

All test files organized for easy CI/CD integration:

- **test_core.py** - Tests timeline management, event handling, and serialization
- **test_export.py** - Tests JSON, EEGLAB, and E-Prime export functionality
- **test_audio_features.py** - Tests audio stimulus features

### Modules

**basic_auditory_stimulus/** - Self-contained audio stimulus generator module

### Examples (examples/)

Sample files demonstrating application usage and export formats

## Running the Application

### Windows Users (Recommended)

Simply double-click:
```
setup_and_run.bat
```

This will:
1. Check Python installation
2. Install/update dependencies
3. Launch the application

### All Platforms

Using the launcher:
```bash
python launcher.py
```

Direct launch:
```bash
python test_maker.py
```

## Running Tests

### All Tests
```bash
python tests/test_core.py
python tests/test_export.py
python tests/test_audio_features.py
```

### From Launcher
```bash
python launcher.py
# Then select option 3
```

## Development Guidelines

### Adding New Features

1. **Main application code**: Add to root directory or create new module folder
2. **Documentation**: Add to `docs/` folder
3. **Tests**: Add to `tests/` folder
4. **Examples**: Add to `examples/` folder

### Documentation Standards

- Use Markdown format (.md)
- Place in `docs/` folder
- Link from main README.md when appropriate
- Keep examples up-to-date

### Testing Standards

- Place test files in `tests/` folder
- Use descriptive test names: `test_<feature>.py`
- Import from parent directory: `sys.path.insert(0, str(Path(__file__).parent.parent))`
- Include docstrings explaining what's being tested

### File Naming Conventions

- **Python modules**: lowercase with underscores (e.g., `export_formats.py`)
- **Documentation**: UPPERCASE for major docs (e.g., `README.md`, `QUICKSTART.md`)
- **Test files**: Prefix with `test_` (e.g., `test_export.py`)
- **Examples**: Prefix with `sample_` (e.g., `sample_test.json`)

## Benefits of This Structure

### Organization
- Clear separation of concerns
- Easy to find specific file types
- Logical grouping of related files

### Maintainability
- Tests isolated from main code
- Documentation centralized
- Easy to add new features

### Professional
- Standard Python project structure
- Easy for new contributors to understand
- Compatible with CI/CD pipelines

### User-Friendly
- Simple setup with batch file
- Clear entry points
- Good documentation structure

## Migration Notes

If you have old file paths in your code:

**Old Path** → **New Path**
- `QUICKSTART.md` → `docs/QUICKSTART.md`
- `EXPORT_FORMATS.md` → `docs/EXPORT_FORMATS.md`
- `test_export.py` → `tests/test_export.py`

**Imports in test files:**
```python
# Old
sys.path.insert(0, str(Path(__file__).parent))

# New
sys.path.insert(0, str(Path(__file__).parent.parent))
```

## Future Enhancements

Potential additions to the structure:

- `src/` folder for complex multi-file features
- `data/` folder for datasets or stimulus banks
- `scripts/` folder for utility scripts
- `config/` folder for configuration files
- `.github/` folder for GitHub Actions CI/CD

## Questions?

See the main [README.md](../README.md) for general information or open an issue on GitHub.

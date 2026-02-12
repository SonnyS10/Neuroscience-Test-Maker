# Neuroscience Test Maker

A user-friendly GUI application for building multi-modal neuroscience experiments with synchronized stimulus presentation.

## 📚 Documentation

- **[Quick Start Guide](docs/QUICKSTART.md)** - Get started in minutes
- **[Export Formats Guide](docs/EXPORT_FORMATS.md)** - EEGLAB, E-Prime, and JSON export
- **[Synchronization Guide](docs/SYNCHRONIZATION.md)** - Understanding timeline-based sync
- **[Implementation Details](docs/IMPLEMENTATION.md)** - Architecture and design decisions
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions (pygame, Python versions)
- **[Repository Structure](docs/REPOSITORY_STRUCTURE.md)** - Project organization

## Features

- **Multi-Modal Support**: Currently supports image (visual) and audio (auditory) stimuli
- **Timeline-Based Synchronization**: Precise millisecond-level synchronization of multiple modalities
- **User-Friendly GUI**: Intuitive interface built with Python's tkinter
- **Test Management**: Save, load, and edit test configurations as JSON files
- **Multiple Export Formats**: Export to EEGLAB, E-Prime, and JSON formats
- **Preview Functionality**: Preview your test execution before running actual experiments

## Installation

### Prerequisites
- Python 3.7 or higher (**3.11 or 3.12 recommended**)
  - **Note:** Python 3.14 has pygame compatibility issues. Use 3.11 or 3.12 for best results.

### Setup

1. Clone the repository:
```bash
git clone https://github.com/SonnyS10/Neuroscience-Test-Maker.git
cd Neuroscience-Test-Maker
```

2. **Windows Users - Easy Setup:**
   - Double-click `setup_and_run.bat`
   - The script will automatically check and install all dependencies
   - Then launch the application

3. **Manual Setup (All Platforms):**
   ```bash
   pip install -r requirements.txt
   ```
   
   **Troubleshooting:** If you get pygame errors, see [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)

## Usage

### Quick Start

**Windows (Easiest):**
```bash
setup_and_run.bat
```
Double-click the file or run it from command prompt. It will handle everything!

**All Platforms:**
The easiest way to get started is using the launcher:
```bash
python launcher.py
```

This will present you with a menu to:
1. Launch the GUI application
2. Run a command-line demo
3. Run the test suite
4. Exit

### Starting the Application Directly

Run the test maker GUI:
```bash
python test_maker.py
```

Or run the command-line demo (works without a display):
```bash
python demo.py
```

### Building a Test

1. **Set Test Information**: Enter a name and description for your test
2. **Add Stimuli**: 
   - Click "Add Image Stimulus" to add visual stimuli
   - Click "Add Audio Stimulus" to add auditory stimuli
3. **Configure Each Stimulus**:
   - Select the stimulus file (image or audio)
   - Set the timestamp (when it should appear in milliseconds)
   - Set the duration (how long it should be displayed/played)
   - Configure modality-specific options (position for images, volume for audio)
4. **Review Timeline**: All stimuli appear in the timeline view, sorted by timestamp
5. **Preview**: Click "Preview Test" to see a simulation of your test
6. **Save**: Save your test configuration for later use or execution

### Exporting Tests

The test maker supports exporting to multiple formats for integration with popular research platforms:

**Export Methods:**

1. **Using Save As (Quick Method)**:
   - Go to **File → Save Test As...**
   - Choose your file extension:
     - `.json` for native format (editable)
     - `.txt` with "eeglab" in filename for EEGLAB
     - `.txt` with "eprime" in filename for E-Prime
   - The format is automatically detected from the extension

2. **Using Export Menu (Explicit Selection)**:
   - Go to **File → Export As**
   - Choose your format:
     - **EEGLAB Format (.txt)** - Tab-delimited event markers
     - **E-Prime Format (.txt)** - Tab-delimited experimental design
     - **JSON Format (.json)** - Native editable format

**Supported Formats:**

- **JSON**: Native format, can be reloaded into the application
- **EEGLAB**: Tab-delimited event list for EEG analysis (import with `pop_importevent`)
- **E-Prime**: Tab-delimited format compatible with E-Prime and Excel

For detailed information about export formats, see [EXPORT_FORMATS.md](docs/EXPORT_FORMATS.md).

### Synchronization Approach

The application uses a **timeline-based synchronization** model:

- Events are scheduled on a timeline with millisecond precision
- Each stimulus event has:
  - **Type**: image or audio
  - **Timestamp**: when it starts (ms from test beginning)
  - **Duration**: how long it lasts
  - **Modality-specific data**: file path, position, volume, etc.

Multiple stimuli can be active simultaneously, allowing for synchronized multi-modal presentation.

### File Format

Tests are saved as JSON files with the following structure:

```json
{
  "metadata": {
    "name": "Test Name",
    "description": "Test description",
    "duration_ms": 5000
  },
  "events": [
    {
      "event_type": "image",
      "timestamp_ms": 0,
      "data": {
        "filepath": "/path/to/image.png",
        "duration_ms": 2000,
        "position": "center"
      }
    },
    {
      "event_type": "audio",
      "timestamp_ms": 1000,
      "data": {
        "filepath": "/path/to/sound.wav",
        "duration_ms": 3000,
        "volume": 1.0
      }
    }
  ]
}
```

## Synchronization Options Explained

The application currently implements **timeline-based synchronization**, which is the most common approach in neuroscience experiments. Here are the synchronization approaches that were considered:

### 1. Timeline-Based (Implemented)
- **How it works**: Events are scheduled at specific timestamps on a timeline
- **Pros**: 
  - Precise timing control
  - Easy to visualize and edit
  - Predictable execution
  - Standard in neuroscience
- **Cons**: 
  Randomization and counterbalancing
- Block design support
- Integration with data collection systems
- Direct import from EEGLAB and E-Prime format
- **How it works**: Events trigger other events (e.g., "play sound when image appears")
- **Pros**: 
  - More flexible
  - Good for reactive experiments
  - Can adapt to participant responses
- **Cons**: 
  - Harder to predict timing
  - More complex to implement
- **Best for**: Interactive experiments, response-dependent protocols

### 3. Hybrid Approach (Future Enhancement)
- **How it works**: Combines timeline and event-driven approaches
- **Pros**: 
  - Maximum flexibility
  - Can handle both fixed and dynamic timing
- **Cons**: 
  - Most complex to implement and understand
- **Best for**: Advanced experiments with mixed requirements

## Future Enhancements

- Additional modalities (tactile, olfactory, etc.)
- Event-driven triggers
- Participant response recording
- Real-time execution with actual stimulus presentation
- Export to common experiment platforms (PsychoPy, E-Prime, etc.)
- Randomization and counterbalancing
- Block design support
- Integration with data collection systems

## Architecture

### Project Structure

```
Neuroscience-Test-Maker/
├── test_maker.py          # Main GUI application
├── export_formats.py      # Export to multiple formats
├── launcher.py            # Interactive launcher script
├── demo.py                # Command-line demo
├── setup_and_run.bat      # Windows setup and launch script
├── requirements.txt       # Python dependencies
├── README.md              # This file
├── docs/                  # Documentation
│   ├── QUICKSTART.md      # Quick start guide
│   ├── SYNCHRONIZATION.md # Synchronization documentation
│   ├── EXPORT_FORMATS.md  # Export formats guide
│   ├── IMPLEMENTATION.md  # Implementation details
│   └── AUDIO_FEATURES.md  # Audio features documentation
├── tests/                 # Test suite
│   ├── test_core.py       # Core logic tests
│   ├── test_export.py     # Export functionality tests
│   └── test_audio_features.py # Audio features tests
├── basic_auditory_stimulus/ # Audio stimulus generator
└── examples/              # Example test configurations
    ├── sample_test.json
    ├── sample_export_eeglab.txt
    └── sample_export_eprime.txt
```

### Core Components

1. **StimulusEvent**: Represents a single stimulus event with type, timing, and data
2. **TestTimeline**: Manages the collection of events with synchronization logic
3. **TestBuilderGUI**: Main user interface for test creation
4. **StimulusDialog**: Dialog for adding/editing stimulus events
5. **PreviewWindow**: Preview test execution visually

### Design Principles

- **Separation of Concerns**: Timeline logic is separate from GUI
- **Extensibility**: Easy to add new modality types
- **Serialization**: Tests are saved as human-readable JSON
- **Type Safety**: Type hints throughout for better code quality
## Repository Structure

The project is organized into clear, logical folders:

- **Root** - Main application files and launcher
- **docs/** - All documentation (guides, specifications, implementation details)
- **tests/** - Complete test suite
- **examples/** - Sample files demonstrating features
- **basic_auditory_stimulus/** - Audio stimulus generation module

See [docs/REPOSITORY_STRUCTURE.md](docs/REPOSITORY_STRUCTURE.md) for complete details.
## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## License

This project is open source and available under the MIT License.
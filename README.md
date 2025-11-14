# Neuroscience Test Maker

A user-friendly GUI application for building multi-modal neuroscience experiments with synchronized stimulus presentation.

## Features

- **Multi-Modal Support**: Currently supports image (visual) and audio (auditory) stimuli
- **Timeline-Based Synchronization**: Precise millisecond-level synchronization of multiple modalities
- **User-Friendly GUI**: Intuitive interface built with Python's tkinter
- **Test Management**: Save, load, and edit test configurations as JSON files
- **Preview Functionality**: Preview your test execution before running actual experiments

## Installation

### Prerequisites
- Python 3.7 or higher

### Setup

1. Clone the repository:
```bash
git clone https://github.com/SonnyS10/Neuroscience-Test-Maker.git
cd Neuroscience-Test-Maker
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Quick Start

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
  - Less flexible for dynamic experiments
- **Best for**: Controlled experiments with predetermined timing

### 2. Event-Driven (Future Enhancement)
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
├── launcher.py            # Interactive launcher script
├── demo.py               # Command-line demo
├── test_core.py          # Core logic tests
├── requirements.txt      # Python dependencies
├── README.md            # This file
├── QUICKSTART.md        # Quick start guide
├── SYNCHRONIZATION.md   # Detailed synchronization documentation
└── examples/
    └── sample_test.json  # Example test configuration
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

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## License

This project is open source and available under the MIT License.
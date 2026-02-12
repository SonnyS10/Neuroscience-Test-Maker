# Export Formats Guide

## Overview

The Neuroscience Test Maker now supports exporting your test timelines to multiple formats for compatibility with popular neuroscience research platforms:

- **JSON Format** - Native editable format (default)
- **EEGLAB Format** - Tab-delimited event list for EEGLAB
- **E-Prime Format** - Tab-delimited format for E-Prime

## Export Methods

### Method 1: Save As (with Format Selection)

1. Go to **File → Save Test As...**
2. Choose the file extension to determine the export format:
   - `.json` - JSON format (native, editable)
   - `.txt` with "eeglab" in filename - EEGLAB format
   - `.txt` with "eprime" in filename - E-Prime format
   - `.txt` generic - defaults to EEGLAB format
3. The file will be automatically saved in the appropriate format

### Method 2: Export Menu (Explicit Format Selection)

1. Go to **File → Export As**
2. Choose your desired format:
   - **EEGLAB Format (.txt)**
   - **E-Prime Format (.txt)**
   - **JSON Format (.json)**
3. Select the destination and filename

## Format Specifications

### JSON Format (.json)

**Purpose:** Native format for the Neuroscience Test Maker

**Features:**
- Human-readable and editable
- Can be reloaded into the application
- Contains complete test information including metadata

**Structure:**
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
        "file_path": "images/stimulus1.jpg",
        "duration_ms": 1000
      }
    }
  ]
}
```

**Use Cases:**
- Saving and loading tests within the application
- Sharing test designs with collaborators
- Version control and backup

### EEGLAB Format (.txt)

**Purpose:** Import event markers into EEGLAB for EEG data analysis

**Features:**
- Tab-delimited text format
- Contains event timing, type, and stimulus information
- Can be imported into EEGLAB using gui_addevent or pop_importevent

**Columns:**
- **Latency(ms)** - Time of event onset in milliseconds
- **Type** - Event type (image, audio, etc.)
- **Duration(ms)** - Duration of the event
- **EventID** - Unique event identifier (sequential)
- **StimulusFile** - Filename of the stimulus (without path)

**Example:**
```
Latency(ms)	Type	Duration(ms)	EventID	StimulusFile
# Exported from Neuroscience Test Maker
# Test: My EEG Experiment
# Description: Visual oddball task

Latency(ms)	Type	Duration(ms)	EventID	StimulusFile
0	image	1000	1	stimulus1.jpg
500	audio	2000	2	tone1.wav
2000	image	1500	3	stimulus2.jpg
```

**Importing into EEGLAB:**
1. Open EEGLAB
2. Load your EEG dataset
3. Use: **Edit → Event values → Import from ASCII file**
4. Select your exported .txt file
5. Map columns: Latency → latency, Type → type, etc.

**Note:** You may need to convert latency from milliseconds to samples based on your EEG sampling rate:
```matlab
% In EEGLAB, convert ms to samples (assuming 500 Hz sampling rate)
EEG = pop_importevent(EEG, 'event', 'your_file.txt', ...
    'fields', {'latency', 'type', 'duration'}, ...
    'timeunit', 0.001);  % Convert ms to seconds
```

### E-Prime Format (.txt)

**Purpose:** Import experimental design into E-Prime or analyze timing data

**Features:**
- Tab-delimited format with E-Prime headers
- UTF-8 with BOM for Excel compatibility
- Contains procedure, trial, and timing information

**Columns:**
- **Procedure** - Procedure name (default: "TrialProc")
- **Trial** - Trial number (sequential)
- **Stimulus** - Stimulus identifier (derived from filename)
- **StimulusFile** - Full filename of the stimulus
- **OnsetTime** - Onset time in milliseconds
- **Duration** - Duration in milliseconds
- **Type** - Stimulus type (image, audio)
- **Modality** - Modality in uppercase (IMAGE, AUDIO)

**Example:**
```
*** Header Start ***
VersionNumber:	1.0
LevelName:	Session
Title:	My Experiment
Description:	Auditory attention task
Exported:	Neuroscience Test Maker
*** Header End ***

Procedure	Trial	Stimulus	StimulusFile	OnsetTime	Duration	Type	Modality
TrialProc	1	stimulus1	stimulus1.jpg	0	1000	image	IMAGE
TrialProc	2	tone1	tone1.wav	500	2000	audio	AUDIO
TrialProc	3	stimulus2	stimulus2.jpg	2000	1500	image	IMAGE

*** End of data ***
```

**Importing into E-Prime:**
1. Open E-Prime
2. Create a new experiment or open existing
3. Use **Edit → Import** or copy-paste data
4. Map columns to E-Prime variables

**Notes:**
- Can be opened directly in Excel or SPSS for analysis
- OnsetTime is in milliseconds from experiment start
- Compatible with E-DataAid for data merging

## Best Practices

### File Naming Conventions

**EEGLAB:**
- Use descriptive names: `experiment_name_eeglab.txt`
- Include subject/session info: `sub01_ses01_eeglab.txt`

**E-Prime:**
- Match E-Prime naming: `experiment_name_eprime.txt`
- Include condition info: `oddball_visual_eprime.txt`

**JSON:**
- Use descriptive names: `experiment_name.json`
- Version control friendly: `oddball_v1.json`

### Workflow Recommendations

1. **Design Phase:**
   - Create test in GUI
   - Save as JSON for editing and version control

2. **Data Collection:**
   - Export to E-Prime format for experimental delivery
   - Keep JSON backup

3. **Analysis Phase:**
   - Export to EEGLAB format for EEG analysis
   - Use JSON for reference to original design

### Tips for Integration

**EEGLAB Integration:**
- Export events before collecting data to verify timing
- After data collection, merge your event file with EEG data
- Adjust latency for sampling rate if needed
- Use event types as markers for epoching

**E-Prime Integration:**
- Export before building E-Prime experiment
- Use as template for stimulus timing
- Verify OnsetTime matches your experimental needs
- Consider adding response collection in E-Prime

## Troubleshooting

### EEGLAB Import Issues

**Problem:** Events not aligning with EEG data  
**Solution:** Check sampling rate conversion (ms to samples)

**Problem:** Missing stimulus files  
**Solution:** Ensure stimulus files are in EEGLAB's path

### E-Prime Import Issues

**Problem:** Encoding errors in Excel  
**Solution:** Files use UTF-8 with BOM, open with "Text Import Wizard"

**Problem:** Column alignment  
**Solution:** Ensure tab delimiters are preserved when copying

### General Issues

**Problem:** Export menu not available  
**Solution:** Ensure `export_formats.py` is in the same directory

**Problem:** File extension not recognized  
**Solution:** Manually specify format using Export submenu

## Testing Export Functionality

Run the test suite to verify all export formats work correctly:

```bash
python test_export.py
```

This will:
- Create sample test data
- Export to all formats
- Verify content and structure
- Report results

## Format Comparison

| Feature | JSON | EEGLAB | E-Prime |
|---------|------|--------|---------|
| **Human Readable** | ✓ | ✓ | ✓ |
| **Editable** | ✓ | ✓ | ✓ |
| **Re-importable** | ✓ | ✗ | ✗ |
| **EEG Analysis** | ✗ | ✓ | ✗ |
| **Experimental Delivery** | ✗ | ✗ | ✓ |
| **Complete Metadata** | ✓ | Partial | Partial |
| **File Size** | Medium | Small | Small |

## Example Workflow

### Complete Experiment Workflow

1. **Design Test** (Test Maker GUI)
   - Add stimuli and set timing
   - Save as `mydisplay.json`

2. **Export for E-Prime** (Pre-experiment)
   - Export → E-Prime Format
   - Use timing info in E-Prime design
   - Run experiment

3. **Export for EEGLAB** (Post-experiment)
   - Export → EEGLAB Format  
   - Import events into EEGLAB
   - Analyze EEG data with event markers

4. **Archive** (Version Control)
   - Keep JSON file in git
   - Document any timing adjustments
   - Store export outputs with data

## Additional Resources

- **EEGLAB**: https://sccn.ucsd.edu/eeglab/
- **E-Prime**: https://pstnet.com/products/e-prime/
- **Test Maker Documentation**: See README.md

## Version Information

- Export functionality added: Version 2.0
- Supported formats: JSON, EEGLAB (.txt), E-Prime (.txt)
- Format auto-detection based on file extension

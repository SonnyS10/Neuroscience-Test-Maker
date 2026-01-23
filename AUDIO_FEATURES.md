# Audio Features Enhancement

This document describes the new audio features added to the Neuroscience Test Maker.

## New Features

### 1. Default Audio Stimulus Selection

When adding an audio stimulus to your test, you now have access to a library of pre-recorded audio stimuli from the `basic_auditory_stimulus` folder.

**Features:**
- **Dropdown Selection**: Choose from 50 pre-recorded tone frequencies (100Hz to 5000Hz)
- **Easy Selection**: Simply select from the "Default Audio" dropdown in the Add Audio Stimulus dialog
- **Automatic Path Setting**: When you select a default audio, it automatically fills in the custom file path

**Available Tones:**
- Frequency range: 100Hz to 5000Hz in 100Hz increments
- File format: WAV (1 second duration each)
- High quality audio optimized for neuroscience experiments

### 2. Audio Preview Functionality

Both default and custom audio files can now be previewed before adding them to your test.

**Preview Options:**
- **Default Audio Preview**: Click the "Preview" button next to the default audio dropdown
- **Custom Audio Preview**: Click the "Preview" button next to the browse button for custom files
- **Real-time Playback**: Uses pygame for high-quality audio playback
- **Stop Control**: Click OK in the preview dialog to stop playback

### 3. Real Audio Playback During Test Preview

The test preview now includes actual audio playback instead of just visual indicators.

**New Preview Capabilities:**
- **Synchronized Playback**: Audio plays at the correct timestamps during preview
- **Volume Control**: Respects the volume settings for each audio event
- **Automatic Stopping**: Audio stops automatically when the event duration expires
- **Error Handling**: Shows error messages for invalid or missing audio files
- **Multiple Audio Support**: Can handle multiple overlapping audio events

## Technical Implementation

### Dependencies
- **pygame**: Used for audio loading and playback
- **pygame.mixer**: Handles audio mixing and real-time playback
- **Path handling**: Robust file path management for cross-platform compatibility

### Audio File Support
- **Primary Format**: WAV files (recommended for best compatibility)
- **Additional Formats**: MP3, OGG (depending on pygame compilation)
- **Sample Rate**: Supports various sample rates (pygame handles conversion)

### Performance Optimizations
- **Lazy Loading**: Audio files are only loaded when needed
- **Memory Management**: Automatic cleanup of audio resources
- **Thread Safety**: Audio operations are properly synchronized with the GUI

## Usage Instructions

### Adding a Default Audio Stimulus

1. Click **"Add Audio Stimulus"** in the main interface
2. In the dialog that opens:
   - Select a tone from the **"Default Audio"** dropdown (e.g., "tone_1000Hz")
   - Click **"Preview"** to hear the selected tone
   - Set the **timestamp** when the audio should play (in milliseconds)
   - Set the **duration** for how long the audio should play
   - Adjust the **volume** (0.0 to 1.0)
   - Click **"OK"** to add to your test

### Adding a Custom Audio File

1. Click **"Add Audio Stimulus"** in the main interface
2. In the dialog:
   - Click **"Browse..."** under "Custom File"
   - Select your audio file from the file dialog
   - Click **"Preview"** to test your custom audio
   - Configure timing and volume settings
   - Click **"OK"** to add to your test

### Previewing Your Complete Test

1. Click **"Preview Test"** in the main interface
2. The preview window will open showing:
   - **Visual indicators** for images (blue rectangles)
   - **Audio indicators** with speaker icons (green circles)
   - **Real audio playback** for all audio stimuli
3. Use **"Start"** to begin the preview
4. Use **"Stop"** to halt playback (also stops all audio)
5. Close the window to clean up audio resources

## Best Practices

### Audio File Selection
- **Use WAV files** for best compatibility and quality
- **Keep files short** for better memory usage
- **Test all custom audio** using the preview feature before finalizing your test

### Timing Considerations
- **Account for audio loading time** in your timing calculations
- **Consider audio duration** when planning overlapping stimuli
- **Use consistent sample rates** for multiple audio files when possible

### Volume Settings
- **Test volume levels** using the preview feature
- **Consider participant comfort** when setting volume levels
- **Use consistent volume** across similar stimuli for scientific validity

## Troubleshooting

### Common Issues

**"Could not play audio" Error:**
- Check that the audio file exists and is not corrupted
- Ensure the file format is supported (WAV recommended)
- Verify pygame is properly installed

**No Default Audio Options:**
- Ensure the `basic_auditory_stimulus` folder exists in the project directory
- Check that the folder contains .wav files
- Restart the application if the folder was recently added

**Audio Not Playing in Preview:**
- Check your system's audio output settings
- Ensure no other application is blocking audio access
- Try with a different audio file to isolate the issue

**Performance Issues:**
- Close the preview window when not in use
- Avoid very long audio files or too many simultaneous audio events
- Ensure adequate system memory for audio buffering

## File Structure

```
basic_auditory_stimulus/
├── tone_100Hz.wav
├── tone_200Hz.wav
├── tone_300Hz.wav
├── ...
└── tone_5000Hz.wav
```

Each tone file is exactly 1 second long and contains a pure sine wave at the specified frequency.
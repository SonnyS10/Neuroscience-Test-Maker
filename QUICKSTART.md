# Quick Start Guide

## Creating Your First Test

### 1. Launch the Application
```bash
python test_maker.py
```

### 2. Set Up Test Information
- In the "Test Information" section, enter:
  - **Test Name**: e.g., "My First Neuroscience Test"
  - **Description**: e.g., "Testing visual and auditory synchronization"

### 3. Add Your First Image Stimulus
1. Click **"Add Image Stimulus"**
2. In the dialog:
   - Click **"Browse..."** and select an image file (PNG, JPG, etc.)
   - Set **Time (ms)**: `0` (start immediately)
   - Set **Duration (ms)**: `2000` (show for 2 seconds)
   - Select **Position**: `center`
   - Click **"OK"**

### 4. Add an Audio Stimulus
1. Click **"Add Audio Stimulus"**
2. In the dialog:
   - Click **"Browse..."** and select an audio file (WAV, MP3, etc.)
   - Set **Time (ms)**: `1000` (start after 1 second)
   - Set **Duration (ms)**: `3000` (play for 3 seconds)
   - Set **Volume**: `1.0` (full volume)
   - Click **"OK"**

### 5. Review the Timeline
- Your stimuli now appear in the timeline view
- They are automatically sorted by timestamp
- You can see the type, timing, and details of each stimulus

### 6. Preview Your Test
1. Click **"Preview Test"**
2. In the preview window, click **"▶ Start"**
3. Watch the simulation of your test execution
4. Click **"⏸ Stop"** to stop the preview

### 7. Save Your Test
1. Go to **File > Save Test As...**
2. Choose a location and filename (e.g., `my_first_test.json`)
3. Click **"Save"**

## Tips for Building Tests

### Synchronization Examples

**Simultaneous Presentation** (Visual + Auditory at same time):
- Image at 1000ms, duration 2000ms
- Audio at 1000ms, duration 2000ms
→ Both start together at 1 second

**Sequential Presentation** (One after another):
- Image at 0ms, duration 1000ms
- Audio at 1000ms, duration 1000ms
→ Audio starts when image ends

**Overlapping Presentation**:
- Image at 0ms, duration 3000ms
- Audio at 1000ms, duration 2000ms
→ Audio plays while image is still visible

### Common Patterns

**Fixation Cross → Stimulus**:
```
1. Fixation cross at 0ms, duration 500ms
2. Target stimulus at 500ms, duration 2000ms
```

**Cue → Target → Response Prompt**:
```
1. Audio cue at 0ms, duration 500ms
2. Visual target at 1000ms, duration 1500ms
3. Response prompt at 3000ms, duration 2000ms
```

**Multi-Modal Stroop-like Task**:
```
1. Visual word at 0ms, duration 2000ms
2. Audio word at 0ms, duration 1000ms (simultaneous)
```

## Keyboard Shortcuts

- **Ctrl+N**: New Test
- **Ctrl+O**: Open Test
- **Ctrl+S**: Save Test

## Troubleshooting

**Problem**: Can't find my test file
- **Solution**: Test files are saved as `.json` files. Look for files with the `.json` extension in your save location.

**Problem**: Preview window shows placeholders instead of actual images/audio
- **Solution**: The preview currently shows placeholders. Full playback will be implemented in future versions.

**Problem**: Added stimulus at wrong time
- **Solution**: Select the stimulus in the timeline and click "Remove Selected", then add it again with the correct timestamp.

## Next Steps

- Explore the example test in `examples/sample_test.json`
- Try creating complex multi-modal experiments
- Read the full README for more advanced features
- Provide feedback for future enhancements!

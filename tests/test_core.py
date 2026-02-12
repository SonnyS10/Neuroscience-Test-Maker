#!/usr/bin/env python3
"""
Unit tests for the Neuroscience Test Maker core logic.
Tests the timeline and event management without GUI dependencies.
"""

import sys
import json
import tempfile
from pathlib import Path

# Import core classes (avoiding GUI imports)
sys.path.insert(0, str(Path(__file__).parent.parent))

# Mock tkinter to allow importing test_maker module
import sys
from unittest.mock import MagicMock

sys.modules['tkinter'] = MagicMock()
sys.modules['tkinter.ttk'] = MagicMock()
sys.modules['tkinter.filedialog'] = MagicMock()
sys.modules['tkinter.messagebox'] = MagicMock()

from test_maker import StimulusEvent, TestTimeline


def test_stimulus_event_creation():
    """Test creating a stimulus event."""
    print("Testing StimulusEvent creation...")
    event = StimulusEvent(
        event_type='image',
        timestamp_ms=1000,
        data={'filepath': '/path/to/image.png', 'duration_ms': 2000}
    )
    
    assert event.event_type == 'image'
    assert event.timestamp_ms == 1000
    assert event.data['filepath'] == '/path/to/image.png'
    assert event.data['duration_ms'] == 2000
    print("✓ StimulusEvent creation works")


def test_stimulus_event_serialization():
    """Test serializing and deserializing events."""
    print("Testing StimulusEvent serialization...")
    original = StimulusEvent(
        event_type='audio',
        timestamp_ms=500,
        data={'filepath': '/path/to/sound.wav', 'duration_ms': 1000, 'volume': 0.8}
    )
    
    # Serialize
    data = original.to_dict()
    assert data['event_type'] == 'audio'
    assert data['timestamp_ms'] == 500
    
    # Deserialize
    restored = StimulusEvent.from_dict(data)
    assert restored.event_type == original.event_type
    assert restored.timestamp_ms == original.timestamp_ms
    assert restored.data == original.data
    print("✓ StimulusEvent serialization works")


def test_timeline_add_event():
    """Test adding events to timeline."""
    print("Testing TestTimeline.add_event...")
    timeline = TestTimeline()
    
    event1 = StimulusEvent('image', 1000, {'filepath': 'img1.png', 'duration_ms': 2000})
    event2 = StimulusEvent('audio', 500, {'filepath': 'sound1.wav', 'duration_ms': 1500})
    
    timeline.add_event(event1)
    timeline.add_event(event2)
    
    # Events should be sorted by timestamp
    assert len(timeline.events) == 2
    assert timeline.events[0].timestamp_ms == 500  # Audio first
    assert timeline.events[1].timestamp_ms == 1000  # Image second
    print("✓ TestTimeline.add_event works and sorts correctly")


def test_timeline_remove_event():
    """Test removing events from timeline."""
    print("Testing TestTimeline.remove_event...")
    timeline = TestTimeline()
    
    event1 = StimulusEvent('image', 1000, {'filepath': 'img1.png', 'duration_ms': 2000})
    event2 = StimulusEvent('audio', 500, {'filepath': 'sound1.wav', 'duration_ms': 1500})
    
    timeline.add_event(event1)
    timeline.add_event(event2)
    
    timeline.remove_event(event1)
    
    assert len(timeline.events) == 1
    assert timeline.events[0].event_type == 'audio'
    print("✓ TestTimeline.remove_event works")


def test_timeline_duration_calculation():
    """Test automatic duration calculation."""
    print("Testing timeline duration calculation...")
    timeline = TestTimeline()
    
    # Add event at 1000ms with 2000ms duration
    event = StimulusEvent('image', 1000, {'filepath': 'img1.png', 'duration_ms': 2000})
    timeline.add_event(event)
    
    # Duration should be at least 3000ms (1000 + 2000)
    assert timeline.test_metadata['duration_ms'] >= 3000
    print("✓ Timeline duration calculation works")


def test_timeline_get_events_at_time():
    """Test getting active events at a specific time."""
    print("Testing TestTimeline.get_events_at_time...")
    timeline = TestTimeline()
    
    event1 = StimulusEvent('image', 0, {'filepath': 'img1.png', 'duration_ms': 2000})
    event2 = StimulusEvent('audio', 1000, {'filepath': 'sound1.wav', 'duration_ms': 3000})
    event3 = StimulusEvent('image', 5000, {'filepath': 'img2.png', 'duration_ms': 1000})
    
    timeline.add_event(event1)
    timeline.add_event(event2)
    timeline.add_event(event3)
    
    # At 1500ms, both event1 and event2 should be active
    active_at_1500 = timeline.get_events_at_time(1500)
    assert len(active_at_1500) == 2
    
    # At 500ms, only event1 should be active
    active_at_500 = timeline.get_events_at_time(500)
    assert len(active_at_500) == 1
    assert active_at_500[0].event_type == 'image'
    
    # At 5500ms, only event3 should be active
    active_at_5500 = timeline.get_events_at_time(5500)
    assert len(active_at_5500) == 1
    assert active_at_5500[0].timestamp_ms == 5000
    
    print("✓ TestTimeline.get_events_at_time works")


def test_timeline_serialization():
    """Test saving and loading timeline to/from file."""
    print("Testing timeline save/load...")
    timeline = TestTimeline()
    timeline.test_metadata['name'] = 'Test Experiment'
    timeline.test_metadata['description'] = 'A test description'
    
    event1 = StimulusEvent('image', 0, {'filepath': 'img1.png', 'duration_ms': 2000, 'position': 'center'})
    event2 = StimulusEvent('audio', 1000, {'filepath': 'sound1.wav', 'duration_ms': 1500, 'volume': 0.8})
    
    timeline.add_event(event1)
    timeline.add_event(event2)
    
    # Save to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name
    
    try:
        timeline.save_to_file(temp_path)
        
        # Load from file
        loaded_timeline = TestTimeline.load_from_file(temp_path)
        
        # Verify metadata
        assert loaded_timeline.test_metadata['name'] == 'Test Experiment'
        assert loaded_timeline.test_metadata['description'] == 'A test description'
        
        # Verify events
        assert len(loaded_timeline.events) == 2
        assert loaded_timeline.events[0].event_type == 'image'
        assert loaded_timeline.events[0].timestamp_ms == 0
        assert loaded_timeline.events[0].data['position'] == 'center'
        assert loaded_timeline.events[1].event_type == 'audio'
        assert loaded_timeline.events[1].data['volume'] == 0.8
        
        print("✓ Timeline save/load works")
    finally:
        # Clean up
        Path(temp_path).unlink()


def test_synchronization_scenario():
    """Test a realistic multi-modal synchronization scenario."""
    print("Testing realistic synchronization scenario...")
    timeline = TestTimeline()
    
    # Scenario: Attention test with synchronized visual and auditory cues
    # 1. Fixation cross (0-500ms)
    # 2. Audio beep (500-700ms) 
    # 3. Target image appears with tone (1000-3000ms for image, 1000-2000ms for tone)
    # 4. Distractor image (2500-3500ms)
    
    timeline.add_event(StimulusEvent('image', 0, 
        {'filepath': 'fixation.png', 'duration_ms': 500, 'position': 'center'}))
    
    timeline.add_event(StimulusEvent('audio', 500, 
        {'filepath': 'beep.wav', 'duration_ms': 200, 'volume': 0.8}))
    
    timeline.add_event(StimulusEvent('image', 1000, 
        {'filepath': 'target.png', 'duration_ms': 2000, 'position': 'center'}))
    
    timeline.add_event(StimulusEvent('audio', 1000, 
        {'filepath': 'tone.wav', 'duration_ms': 1000, 'volume': 1.0}))
    
    timeline.add_event(StimulusEvent('image', 2500, 
        {'filepath': 'distractor.png', 'duration_ms': 1000, 'position': 'top-right'}))
    
    # Check synchronization at key time points
    
    # At 250ms: Only fixation should be active
    active = timeline.get_events_at_time(250)
    assert len(active) == 1
    assert active[0].data['filepath'] == 'fixation.png'
    
    # At 600ms: Only beep should be active
    active = timeline.get_events_at_time(600)
    assert len(active) == 1
    assert active[0].data['filepath'] == 'beep.wav'
    
    # At 1500ms: Both target image and tone should be active (synchronized)
    active = timeline.get_events_at_time(1500)
    assert len(active) == 2
    event_types = {e.event_type for e in active}
    assert 'image' in event_types
    assert 'audio' in event_types
    
    # At 2700ms: Both target image and distractor should be active
    active = timeline.get_events_at_time(2700)
    assert len(active) == 2
    assert all(e.event_type == 'image' for e in active)
    
    print("✓ Realistic synchronization scenario works correctly")


def run_all_tests():
    """Run all tests."""
    print("\n" + "="*60)
    print("Running Neuroscience Test Maker Core Logic Tests")
    print("="*60 + "\n")
    
    tests = [
        test_stimulus_event_creation,
        test_stimulus_event_serialization,
        test_timeline_add_event,
        test_timeline_remove_event,
        test_timeline_duration_calculation,
        test_timeline_get_events_at_time,
        test_timeline_serialization,
        test_synchronization_scenario,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} error: {e}")
            failed += 1
    
    print("\n" + "="*60)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*60 + "\n")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

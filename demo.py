#!/usr/bin/env python3
"""
Command-line demo of the Neuroscience Test Maker core functionality.
Demonstrates creating and managing a multi-modal test without the GUI.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

# Mock tkinter to allow importing test_maker module
sys.modules['tkinter'] = MagicMock()
sys.modules['tkinter.ttk'] = MagicMock()
sys.modules['tkinter.filedialog'] = MagicMock()
sys.modules['tkinter.messagebox'] = MagicMock()

from test_maker import StimulusEvent, TestTimeline


def demo_basic_test():
    """Create a basic multi-modal test."""
    print("\n" + "="*70)
    print("DEMO: Creating a Basic Multi-Modal Neuroscience Test")
    print("="*70 + "\n")
    
    # Create a new timeline
    timeline = TestTimeline()
    timeline.test_metadata['name'] = 'Attention Task Demo'
    timeline.test_metadata['description'] = 'Multi-modal attention test with synchronized visual and auditory stimuli'
    
    print("Test Information:")
    print(f"  Name: {timeline.test_metadata['name']}")
    print(f"  Description: {timeline.test_metadata['description']}\n")
    
    # Add events
    print("Adding stimuli to timeline...\n")
    
    # 1. Fixation cross
    print("1. Fixation cross (0ms - 500ms)")
    timeline.add_event(StimulusEvent(
        event_type='image',
        timestamp_ms=0,
        data={
            'filepath': '/path/to/fixation_cross.png',
            'duration_ms': 500,
            'position': 'center'
        }
    ))
    
    # 2. Audio cue
    print("2. Audio cue (500ms - 700ms)")
    timeline.add_event(StimulusEvent(
        event_type='audio',
        timestamp_ms=500,
        data={
            'filepath': '/path/to/beep.wav',
            'duration_ms': 200,
            'volume': 0.8
        }
    ))
    
    # 3. Target stimulus (visual)
    print("3. Target image (1000ms - 3000ms)")
    timeline.add_event(StimulusEvent(
        event_type='image',
        timestamp_ms=1000,
        data={
            'filepath': '/path/to/target.png',
            'duration_ms': 2000,
            'position': 'center'
        }
    ))
    
    # 4. Synchronized tone
    print("4. Synchronized tone (1000ms - 2000ms) [SYNCHRONIZED with target image]")
    timeline.add_event(StimulusEvent(
        event_type='audio',
        timestamp_ms=1000,
        data={
            'filepath': '/path/to/tone.wav',
            'duration_ms': 1000,
            'volume': 1.0
        }
    ))
    
    # 5. Distractor
    print("5. Distractor image (2500ms - 3500ms)")
    timeline.add_event(StimulusEvent(
        event_type='image',
        timestamp_ms=2500,
        data={
            'filepath': '/path/to/distractor.png',
            'duration_ms': 1000,
            'position': 'top-right'
        }
    ))
    
    print(f"\nTotal test duration: {timeline.test_metadata['duration_ms']}ms")
    print(f"Total events: {len(timeline.events)}")
    
    return timeline


def demo_synchronization_check(timeline):
    """Demonstrate checking synchronization at different time points."""
    print("\n" + "="*70)
    print("DEMO: Checking Multi-Modal Synchronization")
    print("="*70 + "\n")
    
    time_points = [250, 600, 1500, 2700, 4000]
    
    for time_ms in time_points:
        active_events = timeline.get_events_at_time(time_ms)
        print(f"At {time_ms}ms:")
        
        if not active_events:
            print("  No active stimuli")
        else:
            for event in active_events:
                filepath = Path(event.data['filepath']).name
                print(f"  - {event.event_type.upper()}: {filepath}")
                if event.event_type == 'image':
                    print(f"    Position: {event.data['position']}")
                elif event.event_type == 'audio':
                    print(f"    Volume: {event.data['volume']}")
        print()


def demo_save_load(timeline):
    """Demonstrate saving and loading a test."""
    print("="*70)
    print("DEMO: Saving and Loading Tests")
    print("="*70 + "\n")
    
    # Save to file
    output_file = '/tmp/demo_test.json'
    timeline.save_to_file(output_file)
    print(f"✓ Saved test to: {output_file}")
    
    # Load from file
    loaded_timeline = TestTimeline.load_from_file(output_file)
    print(f"✓ Loaded test from: {output_file}")
    print(f"  Test name: {loaded_timeline.test_metadata['name']}")
    print(f"  Events loaded: {len(loaded_timeline.events)}")
    
    # Show JSON structure
    print(f"\nJSON structure preview:")
    import json
    with open(output_file, 'r') as f:
        data = json.load(f)
    print(json.dumps(data, indent=2)[:500] + "...")
    
    return loaded_timeline


def demo_timeline_visualization(timeline):
    """Create a simple text visualization of the timeline."""
    print("\n" + "="*70)
    print("DEMO: Timeline Visualization")
    print("="*70 + "\n")
    
    # Create a simple timeline visualization
    max_time = timeline.test_metadata['duration_ms']
    scale = max_time / 60  # 60 characters wide
    
    print("Timeline (0ms to {}ms):".format(max_time))
    print("=" * 62)
    
    for event in timeline.events:
        start_pos = int(event.timestamp_ms / scale)
        duration_chars = max(1, int(event.data['duration_ms'] / scale))
        
        # Create visualization line
        line = [' '] * 62
        for i in range(start_pos, min(start_pos + duration_chars, 62)):
            line[i] = '█'
        
        # Event info
        filepath = Path(event.data['filepath']).name
        symbol = '👁' if event.event_type == 'image' else '🔊'
        
        print(f"{symbol} {''.join(line)} {event.event_type}: {filepath}")
        print(f"   {event.timestamp_ms}ms → {event.timestamp_ms + event.data['duration_ms']}ms")
    
    print("=" * 62)


def main():
    """Run all demos."""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*68 + "║")
    print("║" + "  NEUROSCIENCE TEST MAKER - CORE FUNCTIONALITY DEMO".center(68) + "║")
    print("║" + " "*68 + "║")
    print("╚" + "="*68 + "╝")
    
    # Create test
    timeline = demo_basic_test()
    
    # Check synchronization
    demo_synchronization_check(timeline)
    
    # Save and load
    loaded_timeline = demo_save_load(timeline)
    
    # Visualize
    demo_timeline_visualization(loaded_timeline)
    
    print("\n" + "="*70)
    print("DEMO COMPLETE")
    print("="*70)
    print("\nKey Takeaways:")
    print("  • Timeline-based synchronization allows precise timing control")
    print("  • Multiple modalities can be active simultaneously")
    print("  • Events are automatically sorted by timestamp")
    print("  • Tests can be saved/loaded as JSON for portability")
    print("  • Easy to query active events at any time point")
    print("\nTo use the GUI, run: python test_maker.py")
    print("(Requires X display - not available in headless environment)\n")


if __name__ == "__main__":
    main()

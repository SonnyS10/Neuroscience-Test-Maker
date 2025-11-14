# Synchronization Approaches for Multi-Modal Neuroscience Tests

This document explains the different synchronization approaches available for coordinating multiple sensory modalities in neuroscience experiments.

## Overview

When running experiments with multiple modalities (e.g., visual + auditory stimuli), precise timing and synchronization are critical. The choice of synchronization approach affects:
- Timing precision
- Flexibility of experimental design
- Complexity of test creation
- Ability to respond to participant behavior

## 1. Timeline-Based Synchronization (IMPLEMENTED)

### Description
Events are scheduled on a timeline with absolute timestamps. Each event has:
- **Timestamp**: When it starts (milliseconds from test start)
- **Duration**: How long it lasts
- **Type**: What modality (image, audio, etc.)
- **Data**: Modality-specific parameters

### How It Works
```
Timeline: 0ms ----500ms----1000ms----1500ms----2000ms----2500ms
          |       |        |         |         |         |
Events:   Image1  Audio1   Image2    Audio2    Image3
          (2s)    (0.5s)   (1s)      (1s)      (1s)
```

Events can overlap:
```
Timeline: 0ms ----500ms----1000ms----1500ms----2000ms
          |                |         
Events:   Image1-----------(2s duration)-----------|
                           Audio1---(1s duration)--|
```

### Advantages
- ✅ **Precise control**: Exact timing down to milliseconds
- ✅ **Predictable**: Easy to visualize and understand
- ✅ **Repeatable**: Same timing every trial
- ✅ **Standard**: Common in neuroscience research
- ✅ **Easy to edit**: Visual timeline makes adjustments simple

### Disadvantages
- ❌ **Less flexible**: Cannot easily adapt to participant responses
- ❌ **Fixed timing**: All timing must be predetermined

### Best For
- Controlled experiments
- Stimulus presentation studies
- EEG/fMRI paradigms with fixed timing
- Attention and perception studies
- Multi-sensory integration research

### Implementation in Test Maker
```python
# Add image at 0ms for 2000ms
event1 = StimulusEvent('image', 0, {
    'filepath': 'fixation.png',
    'duration_ms': 2000
})

# Add synchronized audio at 1000ms (overlaps with image)
event2 = StimulusEvent('audio', 1000, {
    'filepath': 'tone.wav',
    'duration_ms': 1000
})

timeline.add_event(event1)
timeline.add_event(event2)
```

## 2. Event-Driven Synchronization (FUTURE)

### Description
Events trigger other events based on conditions or triggers. Instead of absolute times, events are linked by cause-and-effect relationships.

### How It Works
```
Trigger Chain:
Image1 → (on_display) → Audio1
Audio1 → (on_complete) → Image2
Image2 → (on_key_press) → Audio2
```

### Advantages
- ✅ **Flexible**: Adapts to participant behavior
- ✅ **Interactive**: Responds to input
- ✅ **Complex logic**: Can implement conditional flows
- ✅ **Natural**: Matches real-world cause-effect

### Disadvantages
- ❌ **Less predictable**: Timing varies by participant
- ❌ **Harder to visualize**: Complex trigger chains
- ❌ **Timing uncertainty**: Cannot guarantee exact timings
- ❌ **More complex**: Requires understanding of triggers

### Best For
- Interactive experiments
- Response-dependent paradigms
- Adaptive testing
- Training applications
- Decision-making studies

### Example Use Cases
```
# Participant-paced presentation
"Show fixation → Wait for spacebar → Show stimulus"

# Conditional branching
"Show question → If correct response → Positive feedback
              → If incorrect response → Negative feedback"

# Reaction time tasks
"Show cue → When participant presses button → Show target
        → Record reaction time"
```

## 3. Hybrid Synchronization (FUTURE)

### Description
Combines timeline-based and event-driven approaches. Uses absolute timing where precision is needed, and triggers where flexibility is needed.

### How It Works
```
Timeline:
0ms: Fixation cross (timeline-based, 500ms)
500ms: Audio cue (timeline-based, 200ms)
700ms: → WAIT FOR KEY PRESS (event-driven)
       → On key press: Show stimulus (timeline-based from this point)
       → Stimulus visible for 2000ms
       → Audio tone at stimulus_start + 1000ms
```

### Advantages
- ✅ **Best of both**: Precision where needed, flexibility where needed
- ✅ **Realistic**: Matches actual experiment requirements
- ✅ **Powerful**: Can handle complex scenarios

### Disadvantages
- ❌ **Most complex**: Requires understanding both approaches
- ❌ **Harder to design**: Need to plan carefully
- ❌ **Potential conflicts**: Timeline and triggers can interact unexpectedly

### Best For
- Advanced experiments
- Self-paced sections with fixed timing requirements
- Training followed by testing
- Experiments with multiple phases

## Comparison Table

| Feature | Timeline-Based | Event-Driven | Hybrid |
|---------|----------------|--------------|---------|
| Timing Precision | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| Flexibility | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Ease of Use | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| Visualization | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ |
| Repeatability | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ |
| Participant Response | ⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

## Technical Implementation Details

### Timeline-Based (Current)
The `TestTimeline` class maintains a sorted list of `StimulusEvent` objects:

```python
class TestTimeline:
    def get_events_at_time(self, timestamp_ms, tolerance_ms=0):
        """Get all events active at a given timestamp"""
        active_events = []
        for event in self.events:
            event_end = event.timestamp_ms + event.data.get('duration_ms', 0)
            if event.timestamp_ms <= timestamp_ms <= event_end:
                active_events.append(event)
        return active_events
```

### Event-Driven (Planned)
Would add trigger mechanisms:

```python
class Trigger:
    def __init__(self, trigger_type, condition, action):
        self.trigger_type = trigger_type  # 'on_display', 'on_key', 'on_complete'
        self.condition = condition        # What to check
        self.action = action             # What event to trigger
```

### Hybrid (Planned)
Would combine both:

```python
class HybridEvent:
    def __init__(self, timing_mode, ...):
        self.timing_mode = timing_mode  # 'absolute' or 'triggered'
        # ... rest of implementation
```

## Recommendations

### For Beginners
Start with **Timeline-Based** synchronization:
- Easier to understand and visualize
- Sufficient for most basic experiments
- Good for learning principles

### For Advanced Users
Consider **Hybrid** approach:
- Use timeline for fixed-timing sections
- Use triggers for participant-paced sections
- Provides maximum flexibility

### For Specific Use Cases

**EEG/fMRI Studies**: Timeline-Based
- Need precise, repeatable timing
- Fixed stimulus presentation critical
- Synchronization with recording equipment

**Behavioral Studies**: Hybrid
- Some fixed timing for consistency
- Some flexibility for participant responses
- Natural flow of experiment

**Training Applications**: Event-Driven
- Fully adaptive to learner
- Progress based on performance
- Self-paced learning

## Future Development

The Neuroscience Test Maker roadmap includes:

1. **Phase 1 (Current)**: Timeline-based synchronization ✓
2. **Phase 2**: Add simple triggers (key press, mouse click)
3. **Phase 3**: Complex event-driven logic (conditions, branching)
4. **Phase 4**: Full hybrid mode with visual programming interface
5. **Phase 5**: Advanced features (randomization, counterbalancing, loops)

## References

Common neuroscience experiment platforms and their approaches:
- **PsychoPy**: Primarily timeline-based with some event handling
- **E-Prime**: Hybrid approach with timeline and procedural logic
- **Presentation**: Timeline-based with trigger support
- **OpenSesame**: Primarily timeline-based with scripting
- **jsPsych**: Event-driven JavaScript framework

For more information on timing precision in neuroscience experiments:
- Bridges et al. (2020). "Timing accuracy in psychological experiments"
- Plant & Turner (2009). "Millisecond precision psychological research"

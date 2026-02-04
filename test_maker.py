#!/usr/bin/env python3
"""
Neuroscience Test Maker
A multi-modal test builder for neuroscience experiments with synchronized image and audio presentation.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import threading
import time
import pygame
import glob
try:
    from basic_auditory_stimulus.audio_tone_maker import ToneGeneratorGUI
except ImportError:
    ToneGeneratorGUI = None


class StimulusEvent:
    """Represents a single stimulus event in the test timeline."""
    
    def __init__(self, event_type: str, timestamp_ms: int, data: Dict[str, Any]):
        """
        Args:
            event_type: Type of stimulus ('image' or 'audio')
            timestamp_ms: Time in milliseconds from test start
            data: Event-specific data (e.g., file path, duration, etc.)
        """
        self.event_type = event_type
        self.timestamp_ms = timestamp_ms
        self.data = data
        self.id = id(self)  # Unique identifier
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize event to dictionary."""
        return {
            'event_type': self.event_type,
            'timestamp_ms': self.timestamp_ms,
            'data': self.data
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StimulusEvent':
        """Deserialize event from dictionary."""
        return cls(
            event_type=data['event_type'],
            timestamp_ms=data['timestamp_ms'],
            data=data['data']
        )


class TestTimeline:
    """Manages the timeline of stimulus events with synchronization."""
    
    def __init__(self):
        self.events: List[StimulusEvent] = []
        self.test_metadata = {
            'name': 'Untitled Test',
            'description': '',
            'duration_ms': 0
        }
    
    def add_event(self, event: StimulusEvent):
        """Add an event to the timeline and sort by timestamp."""
        self.events.append(event)
        self.events.sort(key=lambda e: e.timestamp_ms)
        self._update_duration()
    
    def remove_event(self, event: StimulusEvent):
        """Remove an event from the timeline."""
        if event in self.events:
            self.events.remove(event)
            self._update_duration()
    
    def _update_duration(self):
        """Update total test duration based on events."""
        if self.events:
            max_timestamp = max(e.timestamp_ms for e in self.events)
            # Add buffer for last event (assume 1 second default)
            max_duration = max_timestamp + max(
                e.data.get('duration_ms', 1000) for e in self.events
            )
            self.test_metadata['duration_ms'] = max_duration
        else:
            self.test_metadata['duration_ms'] = 0
    
    def get_events_at_time(self, timestamp_ms: int, tolerance_ms: int = 0) -> List[StimulusEvent]:
        """Get all events that should be active at a given timestamp."""
        active_events = []
        for event in self.events:
            event_end = event.timestamp_ms + event.data.get('duration_ms', 0)
            if event.timestamp_ms - tolerance_ms <= timestamp_ms <= event_end + tolerance_ms:
                active_events.append(event)
        return active_events
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize timeline to dictionary."""
        return {
            'metadata': self.test_metadata,
            'events': [event.to_dict() for event in self.events]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TestTimeline':
        """Deserialize timeline from dictionary."""
        timeline = cls()
        timeline.test_metadata = data.get('metadata', timeline.test_metadata)
        timeline.events = [StimulusEvent.from_dict(e) for e in data.get('events', [])]
        timeline.events.sort(key=lambda e: e.timestamp_ms)
        return timeline
    
    def save_to_file(self, filepath: str):
        """Save timeline to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load_from_file(cls, filepath: str) -> 'TestTimeline':
        """Load timeline from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)


class TestBuilderGUI:
    """Main GUI for the neuroscience test builder."""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Neuroscience Test Maker")
        self.root.geometry("1000x700")
        
        self.timeline = TestTimeline()
        self.current_file = None
        
        self._setup_ui()
        self._setup_menu()
    
    def _setup_menu(self):
        """Create menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Test", command=self.new_test)
        file_menu.add_command(label="Open Test...", command=self.open_test)
        file_menu.add_command(label="Save Test", command=self.save_test)
        file_menu.add_command(label="Save Test As...", command=self.save_test_as)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
    
    def _setup_ui(self):
        """Set up the main user interface."""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Test metadata section
        metadata_frame = ttk.LabelFrame(main_frame, text="Test Information", padding="10")
        metadata_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(metadata_frame, text="Test Name:").grid(row=0, column=0, sticky=tk.W)
        self.name_entry = ttk.Entry(metadata_frame, width=40)
        self.name_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        self.name_entry.insert(0, self.timeline.test_metadata['name'])
        
        ttk.Label(metadata_frame, text="Description:").grid(row=1, column=0, sticky=tk.W)
        self.desc_entry = ttk.Entry(metadata_frame, width=40)
        self.desc_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5)
        
        metadata_frame.columnconfigure(1, weight=1)
        
        # Modality buttons
        modality_frame = ttk.LabelFrame(main_frame, text="Add Stimulus", padding="10")
        modality_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N), pady=(0, 10))
        
        ttk.Button(modality_frame, text="Add Image Stimulus", 
                  command=self.add_image_stimulus).pack(fill=tk.X, pady=2)
        ttk.Button(modality_frame, text="Add Audio Stimulus", 
                  command=self.add_audio_stimulus).pack(fill=tk.X, pady=2)
        
        # Timeline view (list)
        timeline_frame = ttk.LabelFrame(main_frame, text="Timeline Events", padding="10")
        timeline_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(10, 0), pady=(0, 5))
        
        # Timeline tree
        self.timeline_tree = ttk.Treeview(timeline_frame, 
                                         columns=('Type', 'Time', 'Details'),
                                         show='headings', height=8)
        self.timeline_tree.heading('Type', text='Type')
        self.timeline_tree.heading('Time', text='Time (ms)')
        self.timeline_tree.heading('Details', text='Details')
        self.timeline_tree.column('Type', width=100)
        self.timeline_tree.column('Time', width=100)
        self.timeline_tree.column('Details', width=300)
        
        scrollbar = ttk.Scrollbar(timeline_frame, orient=tk.VERTICAL, 
                                 command=self.timeline_tree.yview)
        self.timeline_tree.configure(yscrollcommand=scrollbar.set)
        
        self.timeline_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Visual Timeline (video editor style)
        visual_timeline_frame = ttk.LabelFrame(main_frame, text="Visual Timeline", padding="10")
        visual_timeline_frame.grid(row=2, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(10, 0), pady=(5, 10))
        
        # Canvas for visual timeline
        self.timeline_canvas = tk.Canvas(visual_timeline_frame, bg='#2b2b2b', 
                                        highlightthickness=1, highlightbackground='gray')
        self.timeline_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar for timeline
        timeline_scrollbar = ttk.Scrollbar(visual_timeline_frame, orient=tk.HORIZONTAL,
                                          command=self.timeline_canvas.xview)
        timeline_scrollbar.pack(fill=tk.X)
        self.timeline_canvas.configure(xscrollcommand=timeline_scrollbar.set)
        
        # Bind canvas resize
        self.timeline_canvas.bind('<Configure>', lambda e: self.draw_visual_timeline())
        
        # Timeline controls
        controls_frame = ttk.Frame(main_frame)
        controls_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Button(controls_frame, text="Remove Selected", 
                  command=self.remove_selected_event).pack(side=tk.LEFT, padx=2)
        ttk.Button(controls_frame, text="Preview Test", 
                  command=self.preview_test).pack(side=tk.LEFT, padx=2)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, 
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Configure grid weights
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)  # Timeline events row
        main_frame.rowconfigure(2, weight=1)  # Visual timeline row (same height as events)
    
    def add_image_stimulus(self):
        """Add an image stimulus to the timeline."""
        dialog = StimulusDialog(self.root, "Add Image Stimulus", "image")
        if dialog.result:
            event = StimulusEvent(
                event_type='image',
                timestamp_ms=dialog.result['timestamp_ms'],
                data={
                    'filepath': dialog.result['filepath'],
                    'duration_ms': dialog.result['duration_ms'],
                    'position': dialog.result.get('position', 'center')
                }
            )
            self.timeline.add_event(event)
            self.refresh_timeline_view()
            self.status_var.set(f"Added image stimulus at {event.timestamp_ms}ms")
    
    def add_audio_stimulus(self):
        """Add an audio stimulus to the timeline."""
        dialog = StimulusDialog(self.root, "Add Audio Stimulus", "audio")
        if dialog.result:
            event = StimulusEvent(
                event_type='audio',
                timestamp_ms=dialog.result['timestamp_ms'],
                data={
                    'filepath': dialog.result['filepath'],
                    'duration_ms': dialog.result['duration_ms'],
                    'volume': dialog.result.get('volume', 1.0)
                }
            )
            self.timeline.add_event(event)
            self.refresh_timeline_view()
            self.status_var.set(f"Added audio stimulus at {event.timestamp_ms}ms")
    
    def refresh_timeline_view(self):
        """Refresh the timeline tree view."""
        # Clear existing items
        for item in self.timeline_tree.get_children():
            self.timeline_tree.delete(item)
        
        # Add events
        for event in self.timeline.events:
            details = f"File: {Path(event.data['filepath']).name}, Duration: {event.data['duration_ms']}ms"
            self.timeline_tree.insert('', tk.END, iid=str(event.id),
                                     values=(event.event_type.capitalize(), 
                                           event.timestamp_ms, 
                                           details))
        
        # Update visual timeline
        self.draw_visual_timeline()
    
    def draw_visual_timeline(self):
        """Draw the visual timeline with channels like a video editor."""
        self.timeline_canvas.delete('all')
        
        if not self.timeline.events:
            # Show empty state
            self.timeline_canvas.create_text(
                self.timeline_canvas.winfo_width() // 2,
                self.timeline_canvas.winfo_height() // 2,
                text="No stimuli added yet",
                fill='gray',
                font=('Arial', 10, 'italic')
            )
            return
        
        # Calculate timeline dimensions
        canvas_width = max(800, self.timeline_canvas.winfo_width())
        canvas_height = self.timeline_canvas.winfo_height()
        
        # Timeline settings
        left_margin = 80
        right_margin = 20
        timeline_width = canvas_width - left_margin - right_margin
        
        # Get max time with buffer
        max_time = self.timeline.test_metadata['duration_ms']
        if max_time == 0:
            max_time = 5000  # Default 5 seconds
        
        # Pixels per millisecond
        px_per_ms = timeline_width / max_time
        
        # Assign channels to events (avoid overlaps)
        channels = self._assign_channels()
        num_channels = max(channels.values()) + 1 if channels else 1
        
        # Channel settings
        channel_height = min(30, (canvas_height - 40) / num_channels)
        channel_spacing = 2
        top_margin = 20
        
        # Update canvas scroll region
        self.timeline_canvas.configure(scrollregion=(0, 0, canvas_width, canvas_height))
        
        # Draw time ruler
        self._draw_time_ruler(left_margin, timeline_width, max_time, px_per_ms)
        
        # Draw channel backgrounds and labels
        for i in range(num_channels):
            y = top_margin + i * (channel_height + channel_spacing)
            
            # Channel background
            self.timeline_canvas.create_rectangle(
                left_margin, y, canvas_width - right_margin, y + channel_height,
                fill='#3c3c3c', outline='#555555', width=1
            )
            
            # Channel label
            self.timeline_canvas.create_text(
                left_margin - 10, y + channel_height // 2,
                text=f"Ch {i+1}",
                fill='#aaaaaa',
                font=('Arial', 8),
                anchor='e'
            )
        
        # Draw events as blocks
        for event in self.timeline.events:
            channel = channels[event.id]
            x_start = left_margin + event.timestamp_ms * px_per_ms
            x_end = left_margin + (event.timestamp_ms + event.data['duration_ms']) * px_per_ms
            y = top_margin + channel * (channel_height + channel_spacing)
            
            # Color based on type
            if event.event_type == 'image':
                color = '#4a90e2'  # Blue for images
                text_color = 'white'
            else:  # audio
                color = '#50c878'  # Green for audio
                text_color = 'white'
            
            # Draw event block
            block_id = self.timeline_canvas.create_rectangle(
                x_start, y + 2, x_end, y + channel_height - 2,
                fill=color, outline='white', width=1,
                tags=('event', str(event.id))
            )
            
            # Add event label (truncate if needed)
            filename = Path(event.data['filepath']).stem
            block_width = x_end - x_start
            
            if block_width > 40:  # Only show text if block is wide enough
                label = filename[:int(block_width / 7)]  # Approximate character width
                self.timeline_canvas.create_text(
                    x_start + 5, y + channel_height // 2,
                    text=label,
                    fill=text_color,
                    font=('Arial', 8, 'bold'),
                    anchor='w',
                    tags=('event_text', str(event.id))
                )
            
            # Bind click event for selection
            self.timeline_canvas.tag_bind(block_id, '<Button-1>', 
                                         lambda e, eid=event.id: self._select_event_visual(eid))
    
    def _draw_time_ruler(self, left_margin, timeline_width, max_time, px_per_ms):
        """Draw time ruler with tick marks."""
        ruler_y = 10
        
        # Draw ruler line
        self.timeline_canvas.create_line(
            left_margin, ruler_y, left_margin + timeline_width, ruler_y,
            fill='#888888', width=1
        )
        
        # Calculate appropriate tick interval (aim for ~10 ticks)
        tick_intervals = [100, 250, 500, 1000, 2000, 5000, 10000]
        tick_interval = tick_intervals[0]
        for interval in tick_intervals:
            if max_time / interval <= 10:
                tick_interval = interval
                break
        
        # Draw ticks
        current_time = 0
        while current_time <= max_time:
            x = left_margin + current_time * px_per_ms
            
            # Draw tick
            self.timeline_canvas.create_line(
                x, ruler_y, x, ruler_y + 5,
                fill='#888888', width=1
            )
            
            # Draw time label
            time_label = f"{current_time}ms"
            if current_time >= 1000:
                time_label = f"{current_time/1000:.1f}s"
            
            self.timeline_canvas.create_text(
                x, ruler_y - 5,
                text=time_label,
                fill='#aaaaaa',
                font=('Arial', 7),
                anchor='s'
            )
            
            current_time += tick_interval
    
    def _assign_channels(self):
        """Assign channels to events to avoid overlaps."""
        if not self.timeline.events:
            return {}
        
        # Sort events by start time
        sorted_events = sorted(self.timeline.events, key=lambda e: e.timestamp_ms)
        
        # Track channel occupancy: channel_index -> end_time
        channel_ends = []
        event_channels = {}
        
        for event in sorted_events:
            event_start = event.timestamp_ms
            event_end = event.timestamp_ms + event.data['duration_ms']
            
            # Find first available channel
            assigned_channel = None
            for i, end_time in enumerate(channel_ends):
                if event_start >= end_time:
                    # This channel is free
                    assigned_channel = i
                    channel_ends[i] = event_end
                    break
            
            # If no channel available, create new one
            if assigned_channel is None:
                assigned_channel = len(channel_ends)
                channel_ends.append(event_end)
            
            event_channels[event.id] = assigned_channel
        
        return event_channels
    
    def _select_event_visual(self, event_id):
        """Select an event from the visual timeline."""
        # Find and select in tree view
        try:
            self.timeline_tree.selection_set(str(event_id))
            self.timeline_tree.see(str(event_id))
        except tk.TclError:
            pass
    
    def remove_selected_event(self):
        """Remove the selected event from timeline."""
        selection = self.timeline_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an event to remove.")
            return
        
        for item_id in selection:
            # Find event by id
            event_to_remove = None
            for event in self.timeline.events:
                if str(event.id) == item_id:
                    event_to_remove = event
                    break
            
            if event_to_remove:
                self.timeline.remove_event(event_to_remove)
        
        self.refresh_timeline_view()
        self.status_var.set("Event(s) removed")
    
    def open_tone_generator(self):
        """Open the advanced tone generator window."""
        if ToneGeneratorGUI is None:
            messagebox.showerror("Error", "Tone generator not available. Check that audio_tone_maker.py exists in the basic_auditory_stimulus folder.")
            return
        
        try:
            # Pass callback to add generated tones to timeline
            ToneGeneratorGUI(parent=self.root, on_tone_generated=self.on_tone_generated_callback)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open tone generator: {str(e)}")
    
    def quick_tone_generator(self):
        """Open quick tone generator dialog."""
        dialog = QuickToneDialog(self.root, self.on_tone_generated_callback)
    
    def on_tone_generated_callback(self, filepath, duration_seconds, timestamp_offset=0):
        """Callback when a tone is generated from the tone generator.
        
        Args:
            filepath: Path to generated audio file
            duration_seconds: Duration in seconds
            timestamp_offset: Offset in milliseconds (for batch generation)
        """
        # Calculate timestamp based on timeline or use offset
        if timestamp_offset > 0:
            timestamp_ms = timestamp_offset
        else:
            # If no offset, place at the end of the timeline
            if self.timeline.events:
                last_event_end = max(e.timestamp_ms + e.data['duration_ms'] for e in self.timeline.events)
                timestamp_ms = last_event_end + 500  # 500ms gap
            else:
                timestamp_ms = 0
        
        # Create audio event
        event = StimulusEvent(
            event_type='audio',
            timestamp_ms=timestamp_ms,
            data={
                'filepath': filepath,
                'duration_ms': int(duration_seconds * 1000),
                'volume': 1.0
            }
        )
        self.timeline.add_event(event)
        self.refresh_timeline_view()
        
        if timestamp_offset == 0:  # Only show status for single tones
            self.status_var.set(f"Added generated tone at {timestamp_ms}ms")
    
    def new_test(self):
        """Create a new test."""
        if self.timeline.events and messagebox.askyesno(
            "Confirm New Test", 
            "Current test will be lost. Continue?"):
            self.timeline = TestTimeline()
            self.current_file = None
            self.name_entry.delete(0, tk.END)
            self.name_entry.insert(0, self.timeline.test_metadata['name'])
            self.desc_entry.delete(0, tk.END)
            self.refresh_timeline_view()
            self.status_var.set("New test created")
    
    def open_test(self):
        """Open a test from file."""
        filepath = filedialog.askopenfilename(
            title="Open Test",
            filetypes=[("Test files", "*.json"), ("All files", "*.*")]
        )
        if filepath:
            try:
                self.timeline = TestTimeline.load_from_file(filepath)
                self.current_file = filepath
                self.name_entry.delete(0, tk.END)
                self.name_entry.insert(0, self.timeline.test_metadata['name'])
                self.desc_entry.delete(0, tk.END)
                self.desc_entry.insert(0, self.timeline.test_metadata.get('description', ''))
                self.refresh_timeline_view()
                self.status_var.set(f"Opened: {filepath}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open test: {str(e)}")
    
    def save_test(self):
        """Save the current test."""
        if self.current_file:
            self._save_to_file(self.current_file)
        else:
            self.save_test_as()
    
    def save_test_as(self):
        """Save the test to a new file."""
        filepath = filedialog.asksaveasfilename(
            title="Save Test As",
            defaultextension=".json",
            filetypes=[("Test files", "*.json"), ("All files", "*.*")]
        )
        if filepath:
            self._save_to_file(filepath)
            self.current_file = filepath
    
    def _save_to_file(self, filepath: str):
        """Internal method to save test to file."""
        try:
            # Update metadata from UI
            self.timeline.test_metadata['name'] = self.name_entry.get()
            self.timeline.test_metadata['description'] = self.desc_entry.get()
            
            self.timeline.save_to_file(filepath)
            self.status_var.set(f"Saved: {filepath}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save test: {str(e)}")
    
    def preview_test(self):
        """Preview the test execution."""
        if not self.timeline.events:
            messagebox.showinfo("No Events", "Add some stimuli to the timeline first.")
            return
        
        PreviewWindow(self.root, self.timeline)
    
    def show_about(self):
        """Show about dialog."""
        messagebox.showinfo(
            "About Neuroscience Test Maker",
            "Neuroscience Test Maker v1.0\n\n"
            "A multi-modal test builder for neuroscience experiments.\n\n"
            "Supports synchronized presentation of:\n"
            "- Visual stimuli (images)\n"
            "- Auditory stimuli (audio files)\n\n"
            "Timeline-based synchronization with millisecond precision."
        )


class StimulusDialog:
    """Dialog for adding a stimulus event."""
    
    def __init__(self, parent, title: str, stimulus_type: str):
        self.result = None
        self.stimulus_type = stimulus_type
        
        # Initialize pygame mixer for audio preview
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        
        # Initialize tone generator for audio stimuli
        self.tone_generator = None
        if stimulus_type == 'audio':
            try:
                from basic_auditory_stimulus.audio_tone_maker import ToneGenerator
                self.tone_generator = ToneGenerator()
            except ImportError:
                pass
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("500x550" if stimulus_type == 'audio' else "400x250")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Get default audio files if this is an audio dialog
        self.default_audio_files = []
        if stimulus_type == 'audio':
            basic_audio_path = Path(__file__).parent / 'basic_auditory_stimulus'
            if basic_audio_path.exists():
                self.default_audio_files = list(basic_audio_path.glob('*.wav'))
                self.default_audio_files.sort(key=lambda x: x.name)
        
        # File selection
        current_row = 0
        
        # Audio-specific options at top
        if stimulus_type == 'audio':
            # Instructions label
            inst_label = ttk.Label(self.dialog, text="Choose audio source:", 
                                  font=('Arial', 10, 'bold'))
            inst_label.grid(row=current_row, column=0, columnspan=3, sticky=tk.W, padx=10, pady=(10, 5))
            current_row += 1
            
            # Tabbed notebook for different audio sources
            self.audio_notebook = ttk.Notebook(self.dialog)
            self.audio_notebook.grid(row=current_row, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=5)
            current_row += 1
            
            # Tab 1: Generate New Tone
            tone_tab = ttk.Frame(self.audio_notebook, padding="10")
            self.audio_notebook.add(tone_tab, text="Generate Tone")
            
            tone_row = 0
            ttk.Label(tone_tab, text="Frequency (Hz):").grid(row=tone_row, column=0, sticky=tk.W, pady=3)
            self.tone_freq_var = tk.StringVar(value="440")
            ttk.Entry(tone_tab, textvariable=self.tone_freq_var, width=15).grid(row=tone_row, column=1, sticky=tk.W, padx=5, pady=3)
            tone_row += 1
            
            ttk.Label(tone_tab, text="Duration (seconds):").grid(row=tone_row, column=0, sticky=tk.W, pady=3)
            self.tone_duration_var = tk.StringVar(value="1.0")
            ttk.Entry(tone_tab, textvariable=self.tone_duration_var, width=15).grid(row=tone_row, column=1, sticky=tk.W, padx=5, pady=3)
            tone_row += 1
            
            ttk.Label(tone_tab, text="Amplitude (0.0-1.0):").grid(row=tone_row, column=0, sticky=tk.W, pady=3)
            self.tone_amplitude_var = tk.StringVar(value="0.5")
            ttk.Entry(tone_tab, textvariable=self.tone_amplitude_var, width=15).grid(row=tone_row, column=1, sticky=tk.W, padx=5, pady=3)
            tone_row += 1
            
            # Quick presets
            preset_label = ttk.Label(tone_tab, text="Quick Presets:")
            preset_label.grid(row=tone_row, column=0, columnspan=2, sticky=tk.W, pady=(10, 3))
            tone_row += 1
            
            preset_frame = ttk.Frame(tone_tab)
            preset_frame.grid(row=tone_row, column=0, columnspan=2, sticky=tk.W, pady=3)
            presets = [("A 440Hz", 440), ("C 261Hz", 261), ("C 523Hz", 523), ("1kHz", 1000)]
            for i, (label, freq) in enumerate(presets):
                ttk.Button(preset_frame, text=label, width=10,
                          command=lambda f=freq: self.tone_freq_var.set(str(f))).grid(row=i//2, column=i%2, padx=2, pady=2)
            tone_row += 1
            
            ttk.Button(tone_tab, text="Generate & Use This Tone", 
                      command=self.generate_tone).grid(row=tone_row, column=0, columnspan=2, pady=10)
            tone_row += 1
            
            ttk.Button(tone_tab, text="Preview Tone", 
                      command=self.preview_generated_tone).grid(row=tone_row, column=0, columnspan=2, pady=3)
            
            # Tab 2: Existing Files
            file_tab = ttk.Frame(self.audio_notebook, padding="10")
            self.audio_notebook.add(file_tab, text="Existing Files")
            
            file_row = 0
            if self.default_audio_files:
                ttk.Label(file_tab, text="Select Audio File:").grid(row=file_row, column=0, sticky=tk.W, pady=5)
                file_row += 1
                self.default_audio_var = tk.StringVar(value="Select audio...")
                default_names = ["Select audio..."] + [f.stem for f in self.default_audio_files]
                self.default_combo = ttk.Combobox(file_tab, textvariable=self.default_audio_var, 
                                                 values=default_names, width=30, state="readonly")
                self.default_combo.grid(row=file_row, column=0, columnspan=2, padx=5, pady=5)
                self.default_combo.bind('<<ComboboxSelected>>', self.on_default_selected)
                file_row += 1
                ttk.Button(file_tab, text="Preview Selected", 
                          command=self.preview_default_audio).grid(row=file_row, column=0, columnspan=2, pady=5)
                file_row += 1
                
                ttk.Separator(file_tab, orient='horizontal').grid(row=file_row, column=0, columnspan=2, sticky='ew', pady=10)
                file_row += 1
            
            ttk.Label(file_tab, text="Or Browse for File:").grid(row=file_row, column=0, sticky=tk.W, pady=5)
            file_row += 1
            self.filepath_var = tk.StringVar()
            filepath_entry = ttk.Entry(file_tab, textvariable=self.filepath_var, width=30)
            filepath_entry.grid(row=file_row, column=0, columnspan=2, padx=5, pady=5)
            file_row += 1
            
            button_frame = ttk.Frame(file_tab)
            button_frame.grid(row=file_row, column=0, columnspan=2, pady=5)
            ttk.Button(button_frame, text="Browse...", command=self.browse_file).pack(side=tk.LEFT, padx=2)
            ttk.Button(button_frame, text="Preview", command=self.preview_custom_audio).pack(side=tk.LEFT, padx=2)
            
            # Separator before common options
            ttk.Separator(self.dialog, orient='horizontal').grid(row=current_row, column=0, columnspan=3, sticky='ew', padx=10, pady=10)
            current_row += 1
        else:
            # Image stimulus - original layout
            ttk.Label(self.dialog, text="Image File:").grid(row=current_row, column=0, sticky=tk.W, padx=10, pady=5)
            # Image stimulus - original layout
            ttk.Label(self.dialog, text="Image File:").grid(row=current_row, column=0, sticky=tk.W, padx=10, pady=5)
            self.filepath_var = tk.StringVar()
            filepath_entry = ttk.Entry(self.dialog, textvariable=self.filepath_var, width=30)
            filepath_entry.grid(row=current_row, column=1, padx=5, pady=5)
            ttk.Button(self.dialog, text="Browse...", 
                      command=self.browse_file).grid(row=current_row, column=2, padx=10, pady=5)
            current_row += 1
        
        # Common fields (Timestamp, Duration, etc.)
        ttk.Label(self.dialog, text="Time (ms):").grid(row=current_row, column=0, sticky=tk.W, padx=10, pady=5)
        self.timestamp_var = tk.StringVar(value="0")
        ttk.Entry(self.dialog, textvariable=self.timestamp_var, width=15).grid(
            row=current_row, column=1, sticky=tk.W, padx=5, pady=5)
        current_row += 1
        
        # Duration - auto-fill for generated tones
        ttk.Label(self.dialog, text="Duration (ms):").grid(row=current_row, column=0, sticky=tk.W, padx=10, pady=5)
        self.duration_var = tk.StringVar(value="1000")
        duration_entry = ttk.Entry(self.dialog, textvariable=self.duration_var, width=15)
        duration_entry.grid(row=current_row, column=1, sticky=tk.W, padx=5, pady=5)
        if stimulus_type == 'audio':
            ttk.Label(self.dialog, text="(auto-set for generated tones)", 
                     font=('Arial', 8, 'italic'), foreground='gray').grid(row=current_row, column=2, sticky=tk.W, padx=5)
        current_row += 1
        
        # Type-specific options
        if stimulus_type == 'image':
            ttk.Label(self.dialog, text="Position:").grid(row=current_row, column=0, sticky=tk.W, padx=10, pady=5)
            self.position_var = tk.StringVar(value="center")
            position_combo = ttk.Combobox(self.dialog, textvariable=self.position_var, 
                                         values=['center', 'top-left', 'top-right', 
                                               'bottom-left', 'bottom-right'], width=12)
            position_combo.grid(row=current_row, column=1, sticky=tk.W, padx=5, pady=5)
        elif stimulus_type == 'audio':
            ttk.Label(self.dialog, text="Volume (0-1):").grid(row=current_row, column=0, sticky=tk.W, padx=10, pady=5)
            self.volume_var = tk.StringVar(value="1.0")
            ttk.Entry(self.dialog, textvariable=self.volume_var, width=15).grid(
                row=current_row, column=1, sticky=tk.W, padx=5, pady=5)
        current_row += 1
        
        # Buttons
        button_frame = ttk.Frame(self.dialog)
        button_frame.grid(row=current_row, column=0, columnspan=3, pady=20)
        ttk.Button(button_frame, text="OK", command=self.ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side=tk.LEFT, padx=5)
        
        # Center dialog
        self.dialog.update_idletasks()
        x = (parent.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (parent.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        self.dialog.wait_window()
    
    def generate_tone(self):
        """Generate a tone and set it as the file to use."""
        if not self.tone_generator:
            messagebox.showerror("Error", "Tone generator not available")
            return
        
        try:
            import numpy as np
            
            frequency = float(self.tone_freq_var.get())
            duration = float(self.tone_duration_var.get())
            amplitude = float(self.tone_amplitude_var.get())
            
            if frequency <= 0:
                raise ValueError("Frequency must be positive")
            if duration <= 0 or duration > 10:
                raise ValueError("Duration must be between 0 and 10 seconds")
            if not (0.0 <= amplitude <= 1.0):
                raise ValueError("Amplitude must be between 0.0 and 1.0")
            
            # Generate tone
            audio_data = self.tone_generator.generate_tone(frequency, duration, amplitude)
            
            # Save to file
            output_dir = Path(__file__).parent / 'basic_auditory_stimulus'
            output_dir.mkdir(exist_ok=True)
            
            if frequency == int(frequency):
                filename = f"tone_{int(frequency)}Hz.wav"
            else:
                filename = f"tone_{frequency:.1f}Hz.wav"
            
            filepath = output_dir / filename
            self.tone_generator.save_tone(audio_data, str(filepath))
            
            # Set as the selected file
            self.filepath_var.set(str(filepath))
            
            # Auto-set duration in milliseconds
            self.duration_var.set(str(int(duration * 1000)))
            
            # Switch to the existing files tab to show it's selected
            self.audio_notebook.select(1)
            
            messagebox.showinfo("Success", f"Generated {frequency}Hz tone!\n\nFile: {filename}\n\nClick OK to add to timeline.")
            
        except ValueError as e:
            messagebox.showerror("Invalid Input", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate tone: {str(e)}")
    
    def preview_generated_tone(self):
        """Preview the tone that would be generated."""
        if not self.tone_generator:
            messagebox.showerror("Error", "Tone generator not available")
            return
        
        try:
            import numpy as np
            import tempfile
            
            frequency = float(self.tone_freq_var.get())
            duration = float(self.tone_duration_var.get())
            amplitude = float(self.tone_amplitude_var.get())
            
            if frequency <= 0:
                raise ValueError("Frequency must be positive")
            if duration <= 0 or duration > 10:
                raise ValueError("Duration must be between 0 and 10 seconds")
            if not (0.0 <= amplitude <= 1.0):
                raise ValueError("Amplitude must be between 0.0 and 1.0")
            
            # Generate tone
            audio_data = self.tone_generator.generate_tone(frequency, duration, amplitude)
            
            # Save to temporary file and play using pygame.mixer.music (handles mono audio better)
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                tmp_path = tmp_file.name
            
            self.tone_generator.save_tone(audio_data, tmp_path)
            
            try:
                pygame.mixer.music.load(tmp_path)
                pygame.mixer.music.play()
                messagebox.showinfo("Preview", f"Playing {frequency}Hz tone...\nClick OK to stop.")
                pygame.mixer.music.stop()
            finally:
                # Clean up temp file
                import os
                try:
                    os.unlink(tmp_path)
                except:
                    pass
            
        except ValueError as e:
            messagebox.showerror("Invalid Input", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to preview tone: {str(e)}")
    
    def on_default_selected(self, event=None):
        """Handle default audio selection."""
        selected = self.default_audio_var.get()
        if selected != "Select audio..." and selected != "Select default audio...":
            # Find the matching file
            for file_path in self.default_audio_files:
                if file_path.stem == selected:
                    self.filepath_var.set(str(file_path))
                    break
    
    def preview_default_audio(self):
        """Preview the selected default audio."""
        selected = self.default_audio_var.get()
        if selected == "Select audio..." or selected == "Select default audio...":
            messagebox.showinfo("No Selection", "Please select an audio file first.")
            return
        
        # Find the matching file
        for file_path in self.default_audio_files:
            if file_path.stem == selected:
                try:
                    pygame.mixer.music.load(str(file_path))
                    pygame.mixer.music.play()
                    messagebox.showinfo("Preview", f"Playing: {file_path.name}\nClick OK to stop.")
                    pygame.mixer.music.stop()
                except pygame.error as e:
                    messagebox.showerror("Preview Error", f"Could not play audio: {str(e)}")
                break
    
    def preview_custom_audio(self):
        """Preview the selected custom audio file."""
        filepath = self.filepath_var.get()
        if not filepath:
            messagebox.showinfo("No File", "Please select an audio file first.")
            return
        
        try:
            pygame.mixer.music.load(filepath)
            pygame.mixer.music.play()
            messagebox.showinfo("Preview", f"Playing: {Path(filepath).name}\nClick OK to stop.")
            pygame.mixer.music.stop()
        except (pygame.error, FileNotFoundError) as e:
            messagebox.showerror("Preview Error", f"Could not play audio: {str(e)}")
    
    def browse_file(self):
        """Browse for stimulus file."""
        if self.stimulus_type == 'image':
            filetypes = [("Image files", "*.png *.jpg *.jpeg *.bmp *.gif"), ("All files", "*.*")]
        else:  # audio
            filetypes = [("Audio files", "*.wav *.mp3 *.ogg"), ("All files", "*.*")]
        
        filepath = filedialog.askopenfilename(title=f"Select {self.stimulus_type} file",
                                             filetypes=filetypes)
        if filepath:
            self.filepath_var.set(filepath)
            # Clear default audio selection when custom file is selected
            if self.stimulus_type == 'audio' and hasattr(self, 'default_audio_var'):
                self.default_audio_var.set("Select default audio...")
    
    def ok(self):
        """Validate and accept dialog."""
        if not self.filepath_var.get():
            messagebox.showwarning("Missing File", "Please select a file.")
            return
        
        try:
            timestamp_ms = int(self.timestamp_var.get())
            duration_ms = int(self.duration_var.get())
            
            if timestamp_ms < 0 or duration_ms <= 0:
                raise ValueError("Invalid time values")
            
            self.result = {
                'filepath': self.filepath_var.get(),
                'timestamp_ms': timestamp_ms,
                'duration_ms': duration_ms
            }
            
            if self.stimulus_type == 'image':
                self.result['position'] = self.position_var.get()
            elif self.stimulus_type == 'audio':
                volume = float(self.volume_var.get())
                if not 0 <= volume <= 1:
                    raise ValueError("Volume must be between 0 and 1")
                self.result['volume'] = volume
            
            self.dialog.destroy()
        except ValueError as e:
            messagebox.showerror("Invalid Input", f"Please check your inputs: {str(e)}")
    
    def cancel(self):
        """Cancel dialog."""
        self.dialog.destroy()


class QuickToneDialog:
    """Quick dialog for generating a single tone and adding it to timeline."""
    
    def __init__(self, parent, callback):
        self.callback = callback
        
        # Initialize pygame mixer and numpy
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        
        try:
            import numpy as np
            from basic_auditory_stimulus.audio_tone_maker import ToneGenerator
            self.tone_generator = ToneGenerator()
        except ImportError as e:
            messagebox.showerror("Error", f"Required modules not available: {str(e)}")
            return
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Quick Tone Generator")
        self.dialog.geometry("400x350")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        ttk.Label(main_frame, text="Generate & Add Tone", 
                 font=('Arial', 12, 'bold')).pack(pady=(0, 15))
        
        # Frequency
        freq_frame = ttk.Frame(main_frame)
        freq_frame.pack(fill=tk.X, pady=5)
        ttk.Label(freq_frame, text="Frequency (Hz):", width=20).pack(side=tk.LEFT)
        self.freq_var = tk.StringVar(value="440")
        ttk.Entry(freq_frame, textvariable=self.freq_var, width=15).pack(side=tk.LEFT, padx=5)
        
        # Duration
        duration_frame = ttk.Frame(main_frame)
        duration_frame.pack(fill=tk.X, pady=5)
        ttk.Label(duration_frame, text="Duration (seconds):", width=20).pack(side=tk.LEFT)
        self.duration_var = tk.StringVar(value="1.0")
        ttk.Entry(duration_frame, textvariable=self.duration_var, width=15).pack(side=tk.LEFT, padx=5)
        
        # Amplitude
        amplitude_frame = ttk.Frame(main_frame)
        amplitude_frame.pack(fill=tk.X, pady=5)
        ttk.Label(amplitude_frame, text="Amplitude (0.0-1.0):", width=20).pack(side=tk.LEFT)
        self.amplitude_var = tk.StringVar(value="0.5")
        ttk.Entry(amplitude_frame, textvariable=self.amplitude_var, width=15).pack(side=tk.LEFT, padx=5)
        
        # Timestamp
        time_frame = ttk.Frame(main_frame)
        time_frame.pack(fill=tk.X, pady=5)
        ttk.Label(time_frame, text="Start Time (ms):", width=20).pack(side=tk.LEFT)
        self.timestamp_var = tk.StringVar(value="0")
        ttk.Entry(time_frame, textvariable=self.timestamp_var, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(time_frame, text="End", 
                  command=self.set_end_time).pack(side=tk.LEFT, padx=2)
        
        # Volume
        volume_frame = ttk.Frame(main_frame)
        volume_frame.pack(fill=tk.X, pady=5)
        ttk.Label(volume_frame, text="Playback Volume (0.0-1.0):", width=20).pack(side=tk.LEFT)
        self.volume_var = tk.StringVar(value="1.0")
        ttk.Entry(volume_frame, textvariable=self.volume_var, width=15).pack(side=tk.LEFT, padx=5)
        
        # Quick presets
        preset_frame = ttk.LabelFrame(main_frame, text="Quick Presets", padding="10")
        preset_frame.pack(fill=tk.X, pady=10)
        
        presets = [
            ("A (440Hz)", 440),
            ("C (261Hz)", 261),
            ("Middle C (523Hz)", 523),
            ("1kHz", 1000),
        ]
        
        for i, (label, freq) in enumerate(presets):
            ttk.Button(preset_frame, text=label, width=12,
                      command=lambda f=freq: self.freq_var.set(str(f))).grid(
                          row=i//2, column=i%2, padx=5, pady=2)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=15)
        
        ttk.Button(button_frame, text="Preview", 
                  command=self.preview_tone).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Generate Only", 
                  command=self.generate_only).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Generate & Add", 
                  command=self.generate_and_add).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", 
                  command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        # Center dialog
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.dialog.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
    
    def set_end_time(self):
        """Set timestamp to end of current timeline."""
        # This will be handled by the callback automatically
        self.timestamp_var.set("auto")
    
    def preview_tone(self):
        """Preview the tone before adding."""
        try:
            import numpy as np
            import tempfile
            
            frequency = float(self.freq_var.get())
            duration = float(self.duration_var.get())
            amplitude = float(self.amplitude_var.get())
            
            if frequency <= 0:
                raise ValueError("Frequency must be positive")
            if duration <= 0 or duration > 10:
                raise ValueError("Duration must be between 0 and 10 seconds")
            if not (0.0 <= amplitude <= 1.0):
                raise ValueError("Amplitude must be between 0.0 and 1.0")
            
            # Generate tone
            audio_data = self.tone_generator.generate_tone(frequency, duration, amplitude)
            
            # Save to temporary file and play using pygame.mixer.music (handles mono audio better)
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                tmp_path = tmp_file.name
            
            self.tone_generator.save_tone(audio_data, tmp_path)
            
            try:
                pygame.mixer.music.load(tmp_path)
                pygame.mixer.music.play()
                messagebox.showinfo("Preview", f"Playing {frequency}Hz tone...\\nClick OK to stop.")
                pygame.mixer.music.stop()
            finally:
                # Clean up temp file
                import os
                try:
                    os.unlink(tmp_path)
                except:
                    pass
            
        except ValueError as e:
            messagebox.showerror("Invalid Input", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to preview tone: {str(e)}")
    
    def generate_only(self):
        """Generate tone and save to file without adding to timeline."""
        try:
            import numpy as np
            from pathlib import Path
            
            frequency = float(self.freq_var.get())
            duration = float(self.duration_var.get())
            amplitude = float(self.amplitude_var.get())
            
            if frequency <= 0:
                raise ValueError("Frequency must be positive")
            if duration <= 0 or duration > 10:
                raise ValueError("Duration must be between 0 and 10 seconds")
            if not (0.0 <= amplitude <= 1.0):
                raise ValueError("Amplitude must be between 0.0 and 1.0")
            
            # Generate tone
            audio_data = self.tone_generator.generate_tone(frequency, duration, amplitude)
            
            # Save to file
            output_dir = Path(__file__).parent / 'basic_auditory_stimulus'
            output_dir.mkdir(exist_ok=True)
            
            if frequency == int(frequency):
                filename = f"tone_{int(frequency)}Hz.wav"
            else:
                filename = f"tone_{frequency:.1f}Hz.wav"
            
            filepath = output_dir / filename
            self.tone_generator.save_tone(audio_data, str(filepath))
            
            messagebox.showinfo("Success", f"Generated {frequency}Hz tone!\\n\\nSaved to:\\n{filepath}")
            
        except ValueError as e:
            messagebox.showerror("Invalid Input", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate tone: {str(e)}")
    
    def generate_and_add(self):
        """Generate tone and add to timeline."""
        try:
            import numpy as np
            from pathlib import Path
            
            frequency = float(self.freq_var.get())
            duration = float(self.duration_var.get())
            amplitude = float(self.amplitude_var.get())
            volume = float(self.volume_var.get())
            timestamp_str = self.timestamp_var.get()
            
            if frequency <= 0:
                raise ValueError("Frequency must be positive")
            if duration <= 0 or duration > 10:
                raise ValueError("Duration must be between 0 and 10 seconds")
            if not (0.0 <= amplitude <= 1.0):
                raise ValueError("Amplitude must be between 0.0 and 1.0")
            if not (0.0 <= volume <= 1.0):
                raise ValueError("Volume must be between 0.0 and 1.0")
            
            # Generate tone
            audio_data = self.tone_generator.generate_tone(frequency, duration, amplitude)
            
            # Save to file
            output_dir = Path(__file__).parent / 'basic_auditory_stimulus'
            output_dir.mkdir(exist_ok=True)
            
            if frequency == int(frequency):
                filename = f"tone_{int(frequency)}Hz.wav"
            else:
                filename = f"tone_{frequency:.1f}Hz.wav"
            
            filepath = output_dir / filename
            self.tone_generator.save_tone(audio_data, str(filepath))
            
            # Parse timestamp
            if timestamp_str.lower() == "auto":
                timestamp_ms = 0  # Callback will handle auto-placement
            else:
                timestamp_ms = int(timestamp_str)
                if timestamp_ms < 0:
                    raise ValueError("Timestamp must be non-negative")
            
            # Call callback to add to timeline
            self.callback(str(filepath), duration, timestamp_ms)
            
            messagebox.showinfo("Success", f"Generated and added {frequency}Hz tone!")
            self.dialog.destroy()
            
        except ValueError as e:
            messagebox.showerror("Invalid Input", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate tone: {str(e)}")


class PreviewWindow:
    """Window for previewing test execution."""
    
    def __init__(self, parent, timeline: TestTimeline):
        self.timeline = timeline
        
        # Initialize pygame mixer for audio playback
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        
        self.window = tk.Toplevel(parent)
        self.window.title("Test Preview")
        self.window.geometry("800x600")
        self.window.transient(parent)
        
        # Track currently playing audio events
        self.playing_audio = {}  # event_id -> (sound_object, start_time)
        
        # Handle window closing to stop audio
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Preview canvas
        self.canvas = tk.Canvas(self.window, bg='gray', width=800, height=500)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Control panel
        control_frame = ttk.Frame(self.window)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(control_frame, text="▶ Start", command=self.start_preview).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="⏸ Stop", command=self.stop_preview).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Close", command=self.window.destroy).pack(side=tk.RIGHT, padx=5)
        
        # Progress
        self.progress_var = tk.StringVar(value="Ready")
        ttk.Label(control_frame, textvariable=self.progress_var).pack(side=tk.LEFT, padx=20)
        
        self.running = False
        self.preview_thread = None
    
    def on_closing(self):
        """Handle window closing - stop all audio and close window."""
        self.stop_preview()
        pygame.mixer.stop()  # Stop all sounds
        self.window.destroy()
    
    def start_preview(self):
        """Start preview playback."""
        if self.running:
            return
        
        self.running = True
        self.preview_thread = threading.Thread(target=self._run_preview, daemon=True)
        self.preview_thread.start()
    
    def stop_preview(self):
        """Stop preview playback."""
        self.running = False
        pygame.mixer.stop()  # Stop all audio
        self.playing_audio.clear()
    
    def _run_preview(self):
        """Run the preview in a separate thread."""
        start_time = time.time() * 1000  # Convert to ms
        
        while self.running:
            current_time_ms = (time.time() * 1000) - start_time
            
            # Check if test is complete
            if current_time_ms > self.timeline.test_metadata['duration_ms']:
                self.running = False
                self.progress_var.set("Preview complete")
                break
            
            # Get active events
            active_events = self.timeline.get_events_at_time(int(current_time_ms))
            
            # Update display
            self.window.after(0, self._update_display, current_time_ms, active_events)
            
            time.sleep(0.016)  # ~60 FPS
        
        self.window.after(0, self._clear_display)
    
    def _update_display(self, current_time_ms: float, events: List[StimulusEvent]):
        """Update the preview display."""
        self.progress_var.set(f"Time: {int(current_time_ms)}ms / {self.timeline.test_metadata['duration_ms']}ms")
        
        # Clear canvas
        self.canvas.delete("all")
        
        # Handle audio events - stop audio that should no longer be playing
        events_to_remove = []
        for event_id, (sound, start_time) in self.playing_audio.items():
            # Find the event to check if it should still be playing
            event = next((e for e in self.timeline.events if id(e) == event_id), None)
            if event and current_time_ms > start_time + event.data['duration_ms']:
                # Audio should stop
                sound.stop()
                events_to_remove.append(event_id)
        
        for event_id in events_to_remove:
            del self.playing_audio[event_id]
        
        # Display active events and start new audio
        for event in events:
            if event.event_type == 'image':
                # Show image placeholder with filename
                filename = Path(event.data['filepath']).name
                self.canvas.create_rectangle(250, 150, 550, 350, fill='lightblue', outline='black')
                self.canvas.create_text(400, 250, text=f"Image:\n{filename}", 
                                      font=('Arial', 12), justify=tk.CENTER)
            elif event.event_type == 'audio':
                # Show audio indicator
                filename = Path(event.data['filepath']).name
                self.canvas.create_oval(50, 50, 150, 150, fill='lightgreen', outline='black')
                self.canvas.create_text(100, 100, text=f"🔊\n{filename}", 
                                      font=('Arial', 10), justify=tk.CENTER)
                
                # Start audio if not already playing
                event_id = id(event)
                if event_id not in self.playing_audio:
                    try:
                        # Load and play the audio
                        sound = pygame.mixer.Sound(event.data['filepath'])
                        # Set volume from event data
                        volume = event.data.get('volume', 1.0)
                        sound.set_volume(volume)
                        sound.play()
                        self.playing_audio[event_id] = (sound, current_time_ms)
                    except (pygame.error, FileNotFoundError) as e:
                        # Show error on canvas instead
                        self.canvas.create_text(100, 130, text=f"Error: {str(e)[:20]}...", 
                                              font=('Arial', 8), fill='red', justify=tk.CENTER)
    
    def _clear_display(self):
        """Clear the preview display."""
        self.canvas.delete("all")
        pygame.mixer.stop()  # Stop all sounds
        self.playing_audio.clear()
        self.progress_var.set("Preview stopped")


def main():
    """Main entry point for the application."""
    root = tk.Tk()
    app = TestBuilderGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

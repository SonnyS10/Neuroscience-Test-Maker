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
        ttk.Button(modality_frame, text="Generate Audio Tones", 
                  command=self.open_tone_generator).pack(fill=tk.X, pady=2)
        
        # Timeline view
        timeline_frame = ttk.LabelFrame(main_frame, text="Timeline", padding="10")
        timeline_frame.grid(row=1, column=1, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(10, 0))
        
        # Timeline tree
        self.timeline_tree = ttk.Treeview(timeline_frame, 
                                         columns=('Type', 'Time', 'Details'),
                                         show='headings', height=15)
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
        main_frame.rowconfigure(1, weight=1)
    
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
        """Open the tone generator window."""
        if ToneGeneratorGUI is None:
            messagebox.showerror("Error", "Tone generator not available. Check that audio_tone_maker.py exists in the basic_auditory_stimulus folder.")
            return
        
        try:
            ToneGeneratorGUI(parent=self.root)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open tone generator: {str(e)}")
    
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
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("450x350" if stimulus_type == 'audio' else "400x250")
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
        
        # Add default audio selection for audio stimuli
        if stimulus_type == 'audio' and self.default_audio_files:
            ttk.Label(self.dialog, text="Default Audio:").grid(row=current_row, column=0, sticky=tk.W, padx=10, pady=5)
            self.default_audio_var = tk.StringVar(value="Select default audio...")
            default_names = ["Select default audio..."] + [f.stem for f in self.default_audio_files]
            self.default_combo = ttk.Combobox(self.dialog, textvariable=self.default_audio_var, 
                                             values=default_names, width=27, state="readonly")
            self.default_combo.grid(row=current_row, column=1, padx=5, pady=5)
            self.default_combo.bind('<<ComboboxSelected>>', self.on_default_selected)
            ttk.Button(self.dialog, text="Preview", 
                      command=self.preview_default_audio).grid(row=current_row, column=2, padx=5, pady=5)
            current_row += 1
            
            # Add separator
            ttk.Separator(self.dialog, orient='horizontal').grid(row=current_row, column=0, columnspan=3, sticky='ew', padx=10, pady=5)
            current_row += 1
        
        ttk.Label(self.dialog, text="Custom File:").grid(row=current_row, column=0, sticky=tk.W, padx=10, pady=5)
        self.filepath_var = tk.StringVar()
        filepath_entry = ttk.Entry(self.dialog, textvariable=self.filepath_var, width=30)
        filepath_entry.grid(row=current_row, column=1, padx=5, pady=5)
        
        # Create frame for browse and preview buttons
        if stimulus_type == 'audio':
            button_frame = ttk.Frame(self.dialog)
            button_frame.grid(row=current_row, column=2, padx=5, pady=5)
            ttk.Button(button_frame, text="Browse...", command=self.browse_file).pack(side=tk.TOP, pady=1)
            ttk.Button(button_frame, text="Preview", command=self.preview_custom_audio).pack(side=tk.TOP, pady=1)
        else:
            ttk.Button(self.dialog, text="Browse...", 
                      command=self.browse_file).grid(row=current_row, column=2, padx=10, pady=5)
        current_row += 1
        
        # Timestamp
        ttk.Label(self.dialog, text="Time (ms):").grid(row=current_row, column=0, sticky=tk.W, padx=10, pady=5)
        self.timestamp_var = tk.StringVar(value="0")
        ttk.Entry(self.dialog, textvariable=self.timestamp_var, width=15).grid(
            row=current_row, column=1, sticky=tk.W, padx=5, pady=5)
        current_row += 1
        
        # Duration
        ttk.Label(self.dialog, text="Duration (ms):").grid(row=current_row, column=0, sticky=tk.W, padx=10, pady=5)
        self.duration_var = tk.StringVar(value="1000")
        ttk.Entry(self.dialog, textvariable=self.duration_var, width=15).grid(
            row=current_row, column=1, sticky=tk.W, padx=5, pady=5)
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
    
    def on_default_selected(self, event=None):
        """Handle default audio selection."""
        selected = self.default_audio_var.get()
        if selected != "Select default audio...":
            # Find the matching file
            for file_path in self.default_audio_files:
                if file_path.stem == selected:
                    self.filepath_var.set(str(file_path))
                    break
    
    def preview_default_audio(self):
        """Preview the selected default audio."""
        selected = self.default_audio_var.get()
        if selected == "Select default audio...":
            messagebox.showinfo("No Selection", "Please select a default audio file first.")
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

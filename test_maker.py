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
from PIL import Image, ImageTk
import io
import sounddevice as sd
import soundfile as sf
import numpy as np


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
        self.root.geometry("1400x750")
        
        self.timeline = TestTimeline()
        self.current_file = None
        self.unsaved_changes = False
        self.asset_folders = []  # List of loaded asset folders
        self.available_assets = []  # List of available asset files
        
        self._setup_ui()
        self._setup_menu()
        
        # Set up close handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
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
        file_menu.add_command(label="Export EEG Markers (CSV)...", command=self.export_markers_csv)
        file_menu.add_command(label="Export EEG Markers (BIDS-TSV)...", command=self.export_markers_tsv)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)
        
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
        
        # Create horizontal PanedWindow to separate left sidebar from right content
        main_paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True)
        
        # Left sidebar container
        left_sidebar = ttk.Frame(main_paned)
        main_paned.add(left_sidebar, weight=1)
        
        # Right content container
        right_content = ttk.Frame(main_paned)
        main_paned.add(right_content, weight=3)
        
        # Test metadata section (in left sidebar)
        metadata_frame = ttk.LabelFrame(left_sidebar, text="Test Information", padding="10")
        metadata_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(metadata_frame, text="Test Name:").grid(row=0, column=0, sticky=tk.W)
        self.name_entry = ttk.Entry(metadata_frame, width=30)
        self.name_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        self.name_entry.insert(0, self.timeline.test_metadata['name'])
        
        ttk.Label(metadata_frame, text="Description:").grid(row=1, column=0, sticky=tk.W)
        self.desc_entry = ttk.Entry(metadata_frame, width=30)
        self.desc_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        
        metadata_frame.columnconfigure(1, weight=1)
        
        # Modality buttons (in left sidebar)
        modality_frame = ttk.LabelFrame(left_sidebar, text="Add Stimulus", padding="10")
        modality_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(modality_frame, text="Add Image Stimulus", 
                  command=self.add_image_stimulus).pack(fill=tk.X, pady=2)
        ttk.Button(modality_frame, text="Add Audio Stimulus", 
                  command=self.add_audio_stimulus).pack(fill=tk.X, pady=2)
        
        # Asset browser section (in left sidebar)
        asset_frame = ttk.LabelFrame(left_sidebar, text="Available Assets", padding="10")
        asset_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Folder management buttons
        folder_btn_frame = ttk.Frame(asset_frame)
        folder_btn_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(folder_btn_frame, text="+ Add Folder", 
                  command=self.add_asset_folder).pack(side=tk.LEFT, padx=2)
        ttk.Button(folder_btn_frame, text="Clear All", 
                  command=self.clear_asset_folders).pack(side=tk.LEFT, padx=2)
        
        # Asset list with scrollbar
        asset_list_frame = ttk.Frame(asset_frame)
        asset_list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.asset_listbox = tk.Listbox(asset_list_frame, height=10)
        asset_scrollbar = ttk.Scrollbar(asset_list_frame, orient=tk.VERTICAL,
                                       command=self.asset_listbox.yview)
        self.asset_listbox.configure(yscrollcommand=asset_scrollbar.set)
        
        self.asset_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        asset_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Double-click to add asset to timeline
        self.asset_listbox.bind('<Double-Button-1>', self.add_asset_from_list)
        
        # Add selected asset button
        ttk.Button(asset_frame, text="Add Selected to Timeline",
                  command=lambda: self.add_asset_from_list(None)).pack(fill=tk.X, pady=(5, 0))
        
        # Timeline controls (in left sidebar)
        controls_frame = ttk.Frame(left_sidebar)
        controls_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(controls_frame, text="Remove Selected", 
                  command=self.remove_selected_event).pack(fill=tk.X, pady=2)
        ttk.Button(controls_frame, text="Preview Test", 
                  command=self.preview_test).pack(fill=tk.X, pady=2)
        
        # Timeline view with visual graph (in right content area)
        timeline_frame = ttk.LabelFrame(right_content, text="Timeline", padding="10")
        timeline_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Create a PanedWindow for resizable sections
        paned = ttk.PanedWindow(timeline_frame, orient=tk.VERTICAL)
        paned.pack(fill=tk.BOTH, expand=True)
        
        # Visual timeline canvas section
        canvas_container = ttk.Frame(paned)
        paned.add(canvas_container, weight=3)
        
        canvas_frame = ttk.Frame(canvas_container)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        # Timeline canvas with scrollbars
        self.timeline_canvas = tk.Canvas(canvas_frame, bg='#2b2b2b', height=200, 
                                        highlightthickness=0)
        
        # Horizontal scrollbar
        h_scroll = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, 
                                command=self.timeline_canvas.xview)
        # Vertical scrollbar
        v_scroll = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL,
                                command=self.timeline_canvas.yview)
        
        self.timeline_canvas.configure(xscrollcommand=h_scroll.set, 
                                      yscrollcommand=v_scroll.set)
        
        # Grid layout for canvas and scrollbars
        self.timeline_canvas.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
        v_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scroll.grid(row=1, column=0, sticky=(tk.E, tk.W))
        
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)
        
        # Bind canvas events for interaction
        self.timeline_canvas.bind('<Button-1>', self.on_timeline_click)
        self.timeline_canvas.bind('<B1-Motion>', self.on_timeline_drag)
        self.timeline_canvas.bind('<ButtonRelease-1>', self.on_timeline_release)
        self.timeline_canvas.bind('<Double-Button-1>', self.on_timeline_double_click)
        
        # Track dragging state
        self.dragging_item = None
        self.drag_start_x = 0
        self.drag_offset = 0
        self.resize_edge = None  # 'left', 'right', or None
        
        # Event details section (resizable)
        details_container = ttk.Frame(paned)
        paned.add(details_container, weight=1)
        
        # Timeline tree (details list)
        list_label = ttk.Label(details_container, text="Event Details:", font=('Arial', 9, 'bold'))
        list_label.pack(anchor=tk.W, pady=(5, 2))
        
        tree_frame = ttk.Frame(details_container)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        self.timeline_tree = ttk.Treeview(tree_frame, 
                                         columns=('Type', 'Time', 'Details'),
                                         show='tree headings', height=8)
        self.timeline_tree.heading('#0', text='Icon')
        self.timeline_tree.heading('Type', text='Type')
        self.timeline_tree.heading('Time', text='Time (ms)')
        self.timeline_tree.heading('Details', text='Details')
        self.timeline_tree.column('#0', width=60)
        self.timeline_tree.column('Type', width=80)
        self.timeline_tree.column('Time', width=80)
        self.timeline_tree.column('Details', width=250)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, 
                                 command=self.timeline_tree.yview)
        self.timeline_tree.configure(yscrollcommand=scrollbar.set)
        
        self.timeline_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind right-click for context menu
        self.timeline_tree.bind('<Button-3>', self.show_context_menu)
        self.timeline_tree.bind('<<TreeviewSelect>>', self.on_tree_select)
        
        # Store thumbnail images to prevent garbage collection
        self.thumbnail_images = {}
        self.timeline_block_images = {}
        
        # Status bar (in right content area)
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(right_content, textvariable=self.status_var, 
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, pady=(0, 0))
    
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
                    'position': dialog.result.get('position', 'center'),
                    'marker_code': dialog.result.get('marker_code', 1)
                }
            )
            self.timeline.add_event(event)
            self.refresh_timeline_view()
            self.mark_unsaved()
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
                    'volume': dialog.result.get('volume', 1.0),
                    'marker_code': dialog.result.get('marker_code', 1)
                }
            )
            self.timeline.add_event(event)
            self.refresh_timeline_view()
            self.mark_unsaved()
            self.status_var.set(f"Added audio stimulus at {event.timestamp_ms}ms")
    
    def add_asset_folder(self):
        """Add a folder of assets to the asset browser."""
        folder_path = filedialog.askdirectory(title="Select Asset Folder")
        if folder_path:
            self.asset_folders.append(folder_path)
            self.refresh_asset_list()
            self.status_var.set(f"Added asset folder: {Path(folder_path).name}")
    
    def clear_asset_folders(self):
        """Clear all asset folders."""
        if messagebox.askyesno("Clear Assets", "Remove all asset folders from the browser?"):
            self.asset_folders.clear()
            self.available_assets.clear()
            self.asset_listbox.delete(0, tk.END)
            self.status_var.set("Asset folders cleared")
    
    def refresh_asset_list(self):
        """Refresh the list of available assets from loaded folders."""
        self.asset_listbox.delete(0, tk.END)
        self.available_assets.clear()
        
        # Supported file extensions
        image_exts = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.tif', '.webp', '.svg', '.ico'}
        audio_exts = {'.wav', '.mp3', '.ogg', '.flac', '.aiff'}
        
        # Scan all folders
        for folder in self.asset_folders:
            try:
                for item in Path(folder).rglob('*'):
                    if item.is_file():
                        ext = item.suffix.lower()
                        if ext in image_exts or ext in audio_exts:
                            asset_type = 'image' if ext in image_exts else 'audio'
                            self.available_assets.append({
                                'path': str(item),
                                'name': item.name,
                                'type': asset_type,
                                'folder': folder
                            })
            except Exception as e:
                print(f"Error scanning folder {folder}: {e}")
        
        # Display in listbox
        for asset in self.available_assets:
            icon = "🖼️" if asset['type'] == 'image' else "🔊"
            display_name = f"{icon} {asset['name']}"
            self.asset_listbox.insert(tk.END, display_name)
        
        self.status_var.set(f"Found {len(self.available_assets)} assets")
    
    def add_asset_from_list(self, event):
        """Add selected asset from the list to the timeline."""
        selection = self.asset_listbox.curselection()
        if not selection:
            if event is None:  # Called from button, not double-click
                messagebox.showinfo("No Selection", "Please select an asset to add.")
            return
        
        idx = selection[0]
        asset = self.available_assets[idx]
        
        # Open simplified dialog with pre-filled filepath
        if asset['type'] == 'image':
            dialog = StimulusDialog(self.root, f"Add {asset['name']}", "image", 
                                   prefill_path=asset['path'])
            if dialog.result:
                event_obj = StimulusEvent(
                    event_type='image',
                    timestamp_ms=dialog.result['timestamp_ms'],
                    data={
                        'filepath': dialog.result['filepath'],
                        'duration_ms': dialog.result['duration_ms'],
                        'position': dialog.result.get('position', 'center'),
                        'marker_code': dialog.result.get('marker_code', 1)
                    }
                )
                self.timeline.add_event(event_obj)
                self.refresh_timeline_view()
                self.mark_unsaved()
                self.status_var.set(f"Added {asset['name']} at {event_obj.timestamp_ms}ms")
        else:  # audio
            dialog = StimulusDialog(self.root, f"Add {asset['name']}", "audio",
                                   prefill_path=asset['path'])
            if dialog.result:
                event_obj = StimulusEvent(
                    event_type='audio',
                    timestamp_ms=dialog.result['timestamp_ms'],
                    data={
                        'filepath': dialog.result['filepath'],
                        'duration_ms': dialog.result['duration_ms'],
                        'volume': dialog.result.get('volume', 1.0),
                        'marker_code': dialog.result.get('marker_code', 1)
                    }
                )
                self.timeline.add_event(event_obj)
                self.refresh_timeline_view()
                self.mark_unsaved()
                self.status_var.set(f"Added {asset['name']} at {event_obj.timestamp_ms}ms")
    
    def refresh_timeline_view(self):
        """Refresh the timeline tree view and visual graph."""
        # Clear existing items
        for item in self.timeline_tree.get_children():
            self.timeline_tree.delete(item)
        
        # Clear old thumbnails
        self.thumbnail_images.clear()
        
        # Add events to tree
        for event in self.timeline.events:
            marker = event.data.get('marker_code', 1)
            details = f"File: {Path(event.data['filepath']).name}, Duration: {event.data['duration_ms']}ms, Marker: {marker}"
            
            # Create thumbnail/icon
            icon_image = None
            if event.event_type == 'image':
                icon_image = self.create_thumbnail(event.data['filepath'], event.id)
            
            # Insert with thumbnail
            item_id = self.timeline_tree.insert('', tk.END, iid=str(event.id),
                                     values=(event.event_type.capitalize(), 
                                           event.timestamp_ms, 
                                           details))
            
            if icon_image:
                self.timeline_tree.item(item_id, image=icon_image)
            elif event.event_type == 'audio':
                # Use text for audio icon since emojis work in values
                self.timeline_tree.item(item_id, text='🔊')
        
        # Redraw visual timeline
        self.draw_visual_timeline()
    
    def draw_visual_timeline(self):
        """Draw the visual timeline graph with blocks."""
        self.timeline_canvas.delete('all')
        self.timeline_block_images.clear()
        
        if not self.timeline.events:
            # Show help text
            self.timeline_canvas.create_text(400, 100, 
                text="Add stimuli to see them on the timeline\nDouble-click to edit • Drag to move • Drag edges to resize",
                font=('Arial', 11), fill='#888888', justify=tk.CENTER)
            return
        
        # Calculate timeline dimensions
        max_time = max(e.timestamp_ms + e.data['duration_ms'] for e in self.timeline.events)
        max_time = max(max_time, 10000)  # Minimum 10 seconds
        
        # Scale: pixels per millisecond
        canvas_width = max(800, max_time / 10)  # At least 800px, or 0.1 px/ms
        pixels_per_ms = canvas_width / max_time
        
        # Assign events to rows to avoid overlap
        event_rows = self.assign_events_to_rows()
        num_rows = len(event_rows)
        
        # Draw time ruler
        ruler_height = 30
        self.timeline_canvas.create_rectangle(0, 0, canvas_width, ruler_height, 
                                             fill='#1e1e1e', outline='')
        
        # Draw time markers every second
        for ms in range(0, int(max_time) + 1000, 1000):
            x = ms * pixels_per_ms
            self.timeline_canvas.create_line(x, ruler_height - 10, x, ruler_height,
                                            fill='#555555', width=1)
            self.timeline_canvas.create_text(x, 15, text=f"{ms/1000:.1f}s",
                                            font=('Arial', 8), fill='#aaaaaa')
        
        # Calculate canvas height based on number of rows
        block_height = 120
        row_spacing = 30
        total_height = ruler_height + (num_rows * (block_height + row_spacing)) + 20
        self.timeline_canvas.configure(scrollregion=(0, 0, canvas_width, total_height))
        
        # Draw events as blocks in their assigned rows
        y_start = ruler_height + 20
        
        for row_idx, events_in_row in enumerate(event_rows):
            y_offset = y_start + (row_idx * (block_height + row_spacing))
            
            for event in events_in_row:
                x1 = event.timestamp_ms * pixels_per_ms
                x2 = (event.timestamp_ms + event.data['duration_ms']) * pixels_per_ms
                y1 = y_offset
                y2 = y_offset + block_height
                
                # Choose color based on type
                if event.event_type == 'image':
                    color = '#4a90e2'  # Blue
                    edge_color = '#357abd'
                else:  # audio
                    color = '#50c878'  # Green
                    edge_color = '#3da660'
                
                # Draw block
                block_id = self.timeline_canvas.create_rectangle(
                    x1, y1, x2, y2, fill=color, outline=edge_color, width=2,
                    tags=('block', f'event_{event.id}', f'row_{row_idx}')
                )
                
                # Add image thumbnail or audio icon
                if event.event_type == 'image':
                    self.draw_block_thumbnail(event, x1, y1, x2, y2)
                else:
                    # Draw audio icon
                    center_x = (x1 + x2) / 2
                    center_y = (y1 + y2) / 2
                    self.timeline_canvas.create_text(center_x, center_y, 
                        text='🔊', font=('Arial', 40), fill='white',
                        tags=('block', f'event_{event.id}', f'row_{row_idx}'))
                
                # Add filename label
                filename = Path(event.data['filepath']).name
                if len(filename) > 20:
                    filename = filename[:17] + '...'
                
                # Add marker code badge
                marker = event.data.get('marker_code', 1)
                badge_text = f"M{marker}"
                
                self.timeline_canvas.create_text((x1 + x2) / 2, y2 + 10,
                    text=f"{filename} [{badge_text}]", font=('Arial', 9, 'bold'), fill='white',
                    tags=('block', f'event_{event.id}', f'row_{row_idx}'))
                
                # Draw resize handles
                handle_width = 8
                # Left handle
                self.timeline_canvas.create_rectangle(x1, y1, x1 + handle_width, y2,
                    fill='#ffffff', outline='', tags=('handle', 'left', f'event_{event.id}'))
                # Right handle
                self.timeline_canvas.create_rectangle(x2 - handle_width, y1, x2, y2,
                    fill='#ffffff', outline='', tags=('handle', 'right', f'event_{event.id}'))
    
    def assign_events_to_rows(self) -> List[List[StimulusEvent]]:
        """Assign events to rows to avoid overlapping blocks."""
        if not self.timeline.events:
            return []
        
        # Sort events by start time
        sorted_events = sorted(self.timeline.events, key=lambda e: e.timestamp_ms)
        
        rows = []
        
        for event in sorted_events:
            event_start = event.timestamp_ms
            event_end = event.timestamp_ms + event.data['duration_ms']
            
            # Try to find a row where this event fits without overlap
            placed = False
            for row in rows:
                # Check if event overlaps with any event in this row
                overlaps = False
                for existing_event in row:
                    existing_start = existing_event.timestamp_ms
                    existing_end = existing_event.timestamp_ms + existing_event.data['duration_ms']
                    
                    # Check for overlap
                    if not (event_end <= existing_start or event_start >= existing_end):
                        overlaps = True
                        break
                
                if not overlaps:
                    row.append(event)
                    placed = True
                    break
            
            # If no suitable row found, create a new row
            if not placed:
                rows.append([event])
        
        return rows
    
    def draw_block_thumbnail(self, event, x1, y1, x2, y2):
        """Draw a thumbnail image on a timeline block."""
        try:
            img = Image.open(event.data['filepath'])
            # Calculate thumbnail size to fit in block
            block_width = int(x2 - x1 - 10)
            block_height = int(y2 - y1 - 30)
            
            if block_width > 20 and block_height > 20:
                img.thumbnail((block_width, block_height), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.timeline_block_images[event.id] = photo
                
                # Center image in block
                img_x = x1 + (x2 - x1) / 2
                img_y = y1 + (y2 - y1 - 20) / 2
                self.timeline_canvas.create_image(img_x, img_y, image=photo,
                    tags=('block', f'event_{event.id}'))
        except Exception as e:
            print(f"Error drawing thumbnail: {e}")
    
    def create_thumbnail(self, filepath: str, event_id: int) -> Optional[ImageTk.PhotoImage]:
        """Create a thumbnail image for the timeline."""
        try:
            img = Image.open(filepath)
            img.thumbnail((60, 60), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            # Store reference to prevent garbage collection
            self.thumbnail_images[event_id] = photo
            return photo
        except Exception as e:
            print(f"Error creating thumbnail: {e}")
            return None
    
    def show_context_menu(self, event):
        """Show context menu on right-click."""
        # Select the item under cursor
        item_id = self.timeline_tree.identify_row(event.y)
        if item_id:
            self.timeline_tree.selection_set(item_id)
            
            # Create context menu
            menu = tk.Menu(self.root, tearoff=0)
            menu.add_command(label="Edit", command=self.edit_selected_event)
            menu.add_command(label="Remove", command=self.remove_selected_event)
            menu.add_separator()
            menu.add_command(label="Duplicate", command=self.duplicate_selected_event)
            
            try:
                menu.tk_popup(event.x_root, event.y_root)
            finally:
                menu.grab_release()
    
    def edit_selected_event(self):
        """Edit the selected event."""
        selection = self.timeline_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an event to edit.")
            return
        
        item_id = selection[0]
        event_to_edit = None
        for event in self.timeline.events:
            if str(event.id) == item_id:
                event_to_edit = event
                break
        
        if event_to_edit:
            # Open dialog with existing values
            dialog = StimulusDialog(self.root, f"Edit {event_to_edit.event_type.capitalize()} Stimulus", 
                                  event_to_edit.event_type, event_to_edit)
            if dialog.result:
                # Update event
                event_to_edit.timestamp_ms = dialog.result['timestamp_ms']
                event_to_edit.data['filepath'] = dialog.result['filepath']
                event_to_edit.data['duration_ms'] = dialog.result['duration_ms']
                event_to_edit.data['marker_code'] = dialog.result.get('marker_code', 1)
                
                if event_to_edit.event_type == 'image':
                    event_to_edit.data['position'] = dialog.result.get('position', 'center')
                else:
                    event_to_edit.data['volume'] = dialog.result.get('volume', 1.0)
                
                self.timeline.events.sort(key=lambda e: e.timestamp_ms)
                self.refresh_timeline_view()
                self.mark_unsaved()
                self.status_var.set(f"Updated {event_to_edit.event_type} stimulus")
    
    def duplicate_selected_event(self):
        """Duplicate the selected event."""
        selection = self.timeline_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an event to duplicate.")
            return
        
        item_id = selection[0]
        event_to_duplicate = None
        for event in self.timeline.events:
            if str(event.id) == item_id:
                event_to_duplicate = event
                break
        
        if event_to_duplicate:
            new_event = StimulusEvent(
                event_type=event_to_duplicate.event_type,
                timestamp_ms=event_to_duplicate.timestamp_ms + 1000,  # Offset by 1 second
                data=event_to_duplicate.data.copy()
            )
            self.timeline.add_event(new_event)
            self.refresh_timeline_view()
            self.mark_unsaved()
            self.status_var.set(f"Duplicated {event_to_duplicate.event_type} stimulus")
    
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
        self.mark_unsaved()
        self.status_var.set("Event(s) removed")
    
    def on_tree_select(self, event):
        """Handle tree selection to highlight on canvas."""
        selection = self.timeline_tree.selection()
        if selection:
            # Highlight selected block on canvas
            self.timeline_canvas.delete('highlight')
            for item_id in selection:
                items = self.timeline_canvas.find_withtag(f'event_{item_id}')
                for item in items:
                    bbox = self.timeline_canvas.bbox(item)
                    if bbox:
                        self.timeline_canvas.create_rectangle(
                            bbox[0]-3, bbox[1]-3, bbox[2]+3, bbox[3]+3,
                            outline='yellow', width=3, tags='highlight')
                        break
    
    def on_timeline_click(self, event):
        """Handle mouse click on timeline canvas."""
        x = self.timeline_canvas.canvasx(event.x)
        y = self.timeline_canvas.canvasy(event.y)
        
        # Check if clicking on a handle
        items = self.timeline_canvas.find_overlapping(x, y, x, y)
        for item in items:
            tags = self.timeline_canvas.gettags(item)
            if 'handle' in tags:
                # Start resize operation
                if 'left' in tags:
                    self.resize_edge = 'left'
                elif 'right' in tags:
                    self.resize_edge = 'right'
                
                # Find event id
                for tag in tags:
                    if tag.startswith('event_'):
                        self.dragging_item = tag.replace('event_', '')
                        break
                self.drag_start_x = x
                return
            elif 'block' in tags:
                # Start drag operation
                for tag in tags:
                    if tag.startswith('event_'):
                        self.dragging_item = tag.replace('event_', '')
                        # Calculate offset from block start
                        event = self.get_event_by_id(int(self.dragging_item))
                        if event:
                            max_time = max(e.timestamp_ms + e.data['duration_ms'] for e in self.timeline.events)
                            canvas_width = max(800, max_time / 10)
                            pixels_per_ms = canvas_width / max(max_time, 10000)
                            block_start_x = event.timestamp_ms * pixels_per_ms
                            self.drag_offset = x - block_start_x
                        break
                self.drag_start_x = x
                self.resize_edge = None
                return
    
    def on_timeline_drag(self, event):
        """Handle mouse drag on timeline canvas."""
        if not self.dragging_item:
            return
        
        x = self.timeline_canvas.canvasx(event.x)
        event_obj = self.get_event_by_id(int(self.dragging_item))
        if not event_obj:
            return
        
        # Calculate scale
        max_time = max(e.timestamp_ms + e.data['duration_ms'] for e in self.timeline.events)
        canvas_width = max(800, max_time / 10)
        pixels_per_ms = canvas_width / max(max_time, 10000)
        
        if self.resize_edge:
            # Resize operation
            delta_ms = (x - self.drag_start_x) / pixels_per_ms
            
            if self.resize_edge == 'left':
                new_start = max(0, event_obj.timestamp_ms + delta_ms)
                new_duration = event_obj.data['duration_ms'] - (new_start - event_obj.timestamp_ms)
                if new_duration > 100:  # Minimum duration
                    event_obj.timestamp_ms = int(new_start)
                    event_obj.data['duration_ms'] = int(new_duration)
            elif self.resize_edge == 'right':
                new_duration = event_obj.data['duration_ms'] + delta_ms
                if new_duration > 100:
                    event_obj.data['duration_ms'] = int(new_duration)
            
            self.drag_start_x = x
        else:
            # Move operation
            new_time = max(0, (x - self.drag_offset) / pixels_per_ms)
            event_obj.timestamp_ms = int(new_time)
        
        # Live update
        self.timeline.events.sort(key=lambda e: e.timestamp_ms)
        self.draw_visual_timeline()
    
    def on_timeline_release(self, event):
        """Handle mouse release on timeline canvas."""
        if self.dragging_item:
            # Final update
            self.refresh_timeline_view()
            self.mark_unsaved()
            self.status_var.set("Timeline updated")
        
        self.dragging_item = None
        self.resize_edge = None
        self.drag_start_x = 0
    
    def on_timeline_double_click(self, event):
        """Handle double-click to edit event."""
        x = self.timeline_canvas.canvasx(event.x)
        y = self.timeline_canvas.canvasy(event.y)
        
        items = self.timeline_canvas.find_overlapping(x, y, x, y)
        for item in items:
            tags = self.timeline_canvas.gettags(item)
            for tag in tags:
                if tag.startswith('event_'):
                    event_id = tag.replace('event_', '')
                    self.timeline_tree.selection_set(event_id)
                    self.edit_selected_event()
                    return
    
    def get_event_by_id(self, event_id: int):
        """Get event object by ID."""
        for event in self.timeline.events:
            if event.id == event_id:
                return event
        return None
    
    def new_test(self):
        """Create a new test."""
        if self.unsaved_changes:
            result = messagebox.askyesnocancel(
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save before creating a new test?"
            )
            if result is True:  # Yes - save first
                self.save_test()
                if self.unsaved_changes:  # Save was cancelled
                    return
            elif result is None:  # Cancel
                return
            # result is False means No - continue without saving
        
        self.timeline = TestTimeline()
        self.current_file = None
        self.name_entry.delete(0, tk.END)
        self.name_entry.insert(0, self.timeline.test_metadata['name'])
        self.desc_entry.delete(0, tk.END)
        self.refresh_timeline_view()
        self.mark_saved()
        self.status_var.set("New test created")
    
    def open_test(self):
        """Open a test from file."""
        if self.unsaved_changes:
            result = messagebox.askyesnocancel(
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save before opening another test?"
            )
            if result is True:  # Yes - save first
                self.save_test()
                if self.unsaved_changes:  # Save was cancelled
                    return
            elif result is None:  # Cancel
                return
            # result is False means No - continue without saving
        
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
                self.mark_saved()
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
            
            # Update total duration based on events
            if self.timeline.events:
                max_time = max(e.timestamp_ms + e.data['duration_ms'] for e in self.timeline.events)
                self.timeline.test_metadata['duration_ms'] = max_time
            else:
                self.timeline.test_metadata['duration_ms'] = 0
            
            self.timeline.save_to_file(filepath)
            self.mark_saved()
            self.status_var.set(f"Saved: {filepath}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save test: {str(e)}")
    
    def export_markers_csv(self):
        """Export EEG event markers as CSV file."""
        if not self.timeline.events:
            messagebox.showinfo("No Events", "No events to export.")
            return
        
        filepath = filedialog.asksaveasfilename(
            title="Export EEG Markers (CSV)",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if filepath:
            try:
                import csv
                with open(filepath, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    # Write header
                    writer.writerow(['onset_ms', 'duration_ms', 'marker_code', 'event_type', 'stimulus_file'])
                    
                    # Write events sorted by timestamp
                    for event in sorted(self.timeline.events, key=lambda e: e.timestamp_ms):
                        writer.writerow([
                            event.timestamp_ms,
                            event.data['duration_ms'],
                            event.data.get('marker_code', 1),
                            event.event_type,
                            Path(event.data['filepath']).name
                        ])
                
                messagebox.showinfo("Export Successful", f"Exported {len(self.timeline.events)} markers to:\n{filepath}")
                self.status_var.set(f"Exported markers to: {filepath}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export markers: {str(e)}")
    
    def export_markers_tsv(self):
        """Export EEG event markers as BIDS-compatible TSV file."""
        if not self.timeline.events:
            messagebox.showinfo("No Events", "No events to export.")
            return
        
        filepath = filedialog.asksaveasfilename(
            title="Export EEG Markers (BIDS-TSV)",
            defaultextension=".tsv",
            filetypes=[("TSV files", "*.tsv"), ("All files", "*.*")]
        )
        
        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    # Write BIDS-compatible header
                    f.write('onset\\tduration\\tvalue\\tevent_type\\tstim_file\\n')
                    
                    # Write events sorted by timestamp (convert ms to seconds for BIDS)
                    for event in sorted(self.timeline.events, key=lambda e: e.timestamp_ms):
                        onset_sec = event.timestamp_ms / 1000.0
                        duration_sec = event.data['duration_ms'] / 1000.0
                        marker = event.data.get('marker_code', 1)
                        
                        f.write(f'{onset_sec:.3f}\\t{duration_sec:.3f}\\t{marker}\\t{event.event_type}\\t{Path(event.data["filepath"]).name}\\n')
                
                messagebox.showinfo("Export Successful", f"Exported {len(self.timeline.events)} markers to BIDS format:\n{filepath}")
                self.status_var.set(f"Exported BIDS markers to: {filepath}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export markers: {str(e)}")
    
    def load_test(self, filepath: str):
        """Load a test from file (used by startup window)."""
        try:
            self.timeline = TestTimeline.load_from_file(filepath)
            self.current_file = filepath
            self.name_entry.delete(0, tk.END)
            self.name_entry.insert(0, self.timeline.test_metadata['name'])
            self.desc_entry.delete(0, tk.END)
            self.desc_entry.insert(0, self.timeline.test_metadata.get('description', ''))
            self.refresh_timeline_view()
            self.mark_saved()
            self.status_var.set(f"Opened: {filepath}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load test: {str(e)}")
    
    def preview_test(self):
        """Preview the test execution."""
        if not self.timeline.events:
            messagebox.showinfo("No Events", "Add some stimuli to the timeline first.")
            return
        
        # Check if there are any audio events
        has_audio = any(event.event_type == 'audio' for event in self.timeline.events)
        
        audio_device = 0  # Default device
        if has_audio:
            # Show audio device selection dialog
            device_dialog = AudioDeviceDialog(self.root)
            if device_dialog.result is None:
                # User cancelled
                return
            audio_device = device_dialog.result
        
        PreviewWindow(self.root, self.timeline, audio_device)
    
    def on_closing(self):
        """Handle window close event."""
        if self.unsaved_changes:
            result = messagebox.askyesnocancel(
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save before closing?"
            )
            if result is True:  # Yes - save and close
                self.save_test()
                if self.unsaved_changes:  # Save was cancelled
                    return
                self.root.destroy()
            elif result is False:  # No - close without saving
                self.root.destroy()
            # None/Cancel - do nothing, keep window open
        else:
            self.root.destroy()
    
    def mark_unsaved(self):
        """Mark the document as having unsaved changes."""
        self.unsaved_changes = True
        # Update window title to show unsaved state
        title = "Neuroscience Test Maker"
        if self.current_file:
            title += f" - {Path(self.current_file).name}"
        title += " *"
        self.root.title(title)
    
    def mark_saved(self):
        """Mark the document as saved."""
        self.unsaved_changes = False
        # Update window title
        title = "Neuroscience Test Maker"
        if self.current_file:
            title += f" - {Path(self.current_file).name}"
        self.root.title(title)
    
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
    """Dialog for adding/editing stimulus events."""
    
    def __init__(self, parent, title: str, stimulus_type: str, existing_event: Optional[StimulusEvent] = None, prefill_path: str = None):
        self.result = None
        self.stimulus_type = stimulus_type
        self.existing_event = existing_event
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("550x350")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # File selection
        ttk.Label(self.dialog, text="File:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        # Use prefill_path if provided, otherwise use existing_event path, otherwise empty
        initial_path = prefill_path if prefill_path else (existing_event.data['filepath'] if existing_event else "")
        self.filepath_var = tk.StringVar(value=initial_path)
        filepath_entry = ttk.Entry(self.dialog, textvariable=self.filepath_var, width=40)
        filepath_entry.grid(row=0, column=1, columnspan=2, padx=5, pady=5, sticky=(tk.W, tk.E))
        ttk.Button(self.dialog, text="Browse...", 
                  command=self.browse_file).grid(row=0, column=3, padx=10, pady=5)
        
        # Start Time (when stimulus appears)
        time_label = ttk.Label(self.dialog, text="Start Time:")
        time_label.grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        
        # Tooltip for start time
        time_help = ttk.Label(self.dialog, text="ℹ️", foreground="blue", cursor="hand2")
        time_help.grid(row=1, column=0, sticky=tk.E, padx=2)
        self.create_tooltip(time_help, "When the stimulus appears in the test timeline")
        
        # Time slider (0-30 seconds)
        time_frame = ttk.Frame(self.dialog)
        time_frame.grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        initial_time_ms = existing_event.timestamp_ms if existing_event else 0
        self.time_slider = tk.Scale(time_frame, from_=0, to=30000, orient=tk.HORIZONTAL,
                                    resolution=100, length=250, command=self.update_time_entry)
        self.time_slider.set(initial_time_ms)
        self.time_slider.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Label(time_frame, text="ms:").pack(side=tk.LEFT, padx=(5, 2))
        self.timestamp_var = tk.StringVar(value=str(initial_time_ms))
        self.time_entry = ttk.Entry(time_frame, textvariable=self.timestamp_var, width=8)
        self.time_entry.pack(side=tk.LEFT)
        self.time_entry.bind('<Return>', lambda e: self.update_time_slider())
        self.time_entry.bind('<FocusOut>', lambda e: self.update_time_slider())
        
        # Duration (how long stimulus stays active)
        duration_label = ttk.Label(self.dialog, text="Duration:")
        duration_label.grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
        
        # Tooltip for duration
        duration_help = ttk.Label(self.dialog, text="ℹ️", foreground="blue", cursor="hand2")
        duration_help.grid(row=2, column=0, sticky=tk.E, padx=2)
        self.create_tooltip(duration_help, "How long the stimulus stays visible/plays")
        
        # Duration slider (0-30 seconds)
        duration_frame = ttk.Frame(self.dialog)
        duration_frame.grid(row=2, column=1, columnspan=2, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        initial_duration_ms = existing_event.data['duration_ms'] if existing_event else 1000
        self.duration_slider = tk.Scale(duration_frame, from_=0, to=30000, orient=tk.HORIZONTAL,
                                        resolution=100, length=250, command=self.update_duration_entry)
        self.duration_slider.set(initial_duration_ms)
        self.duration_slider.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Label(duration_frame, text="ms:").pack(side=tk.LEFT, padx=(5, 2))
        self.duration_var = tk.StringVar(value=str(initial_duration_ms))
        self.duration_entry = ttk.Entry(duration_frame, textvariable=self.duration_var, width=8)
        self.duration_entry.pack(side=tk.LEFT)
        self.duration_entry.bind('<Return>', lambda e: self.update_duration_slider())
        self.duration_entry.bind('<FocusOut>', lambda e: self.update_duration_slider())
        
        # Type-specific options
        if stimulus_type == 'image':
            ttk.Label(self.dialog, text="Position:").grid(row=3, column=0, sticky=tk.W, padx=10, pady=5)
            default_pos = existing_event.data.get('position', 'center') if existing_event else "center"
            self.position_var = tk.StringVar(value=default_pos)
            position_combo = ttk.Combobox(self.dialog, textvariable=self.position_var, 
                                         values=['center', 'top-left', 'top-right', 
                                               'bottom-left', 'bottom-right'], width=15)
            position_combo.grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)
        elif stimulus_type == 'audio':
            ttk.Label(self.dialog, text="Volume (0-1):").grid(row=3, column=0, sticky=tk.W, padx=10, pady=5)
            default_vol = existing_event.data.get('volume', 1.0) if existing_event else 1.0
            self.volume_var = tk.StringVar(value=str(default_vol))
            ttk.Entry(self.dialog, textvariable=self.volume_var, width=15).grid(
                row=3, column=1, sticky=tk.W, padx=5, pady=5)
        
        # EEG Marker Code
        marker_label = ttk.Label(self.dialog, text="EEG Marker:")
        marker_label.grid(row=4, column=0, sticky=tk.W, padx=10, pady=5)
        
        marker_help = ttk.Label(self.dialog, text="ℹ️", foreground="blue", cursor="hand2")
        marker_help.grid(row=4, column=0, sticky=tk.E, padx=2)
        self.create_tooltip(marker_help, "Event marker code for EEG analysis (1-255)")
        
        default_marker = existing_event.data.get('marker_code', 1) if existing_event else 1
        self.marker_var = tk.StringVar(value=str(default_marker))
        marker_entry = ttk.Entry(self.dialog, textvariable=self.marker_var, width=15)
        marker_entry.grid(row=4, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(self.dialog)
        button_frame.grid(row=5, column=0, columnspan=4, pady=20)
        ttk.Button(button_frame, text="OK", command=self.ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side=tk.LEFT, padx=5)
        
        # Center dialog
        self.dialog.update_idletasks()
        x = (parent.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (parent.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        self.dialog.wait_window()
    
    def browse_file(self):
        """Browse for stimulus file."""
        if self.stimulus_type == 'image':
            filetypes = [("Image files", "*.png *.jpg *.jpeg *.bmp *.gif *.tiff *.tif *.webp *.svg *.ico"), ("All files", "*.*")]
        else:  # audio
            filetypes = [("Audio files", "*.wav *.mp3 *.ogg"), ("All files", "*.*")]
        
        filepath = filedialog.askopenfilename(title=f"Select {self.stimulus_type} file",
                                             filetypes=filetypes)
        if filepath:
            self.filepath_var.set(filepath)
    
    def update_time_entry(self, value):
        """Update time entry when slider moves."""
        self.timestamp_var.set(str(int(float(value))))
    
    def update_time_slider(self):
        """Update time slider when entry changes."""
        try:
            value = int(self.timestamp_var.get())
            if 0 <= value <= 30000:
                self.time_slider.set(value)
            else:
                # Allow custom values beyond slider range
                pass
        except ValueError:
            pass
    
    def update_duration_entry(self, value):
        """Update duration entry when slider moves."""
        self.duration_var.set(str(int(float(value))))
    
    def update_duration_slider(self):
        """Update duration slider when entry changes."""
        try:
            value = int(self.duration_var.get())
            if 0 <= value <= 30000:
                self.duration_slider.set(value)
            else:
                # Allow custom values beyond slider range
                pass
        except ValueError:
            pass
    
    def create_tooltip(self, widget, text):
        """Create a tooltip for a widget."""
        def show_tooltip(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root + 10}+{event.y_root + 10}")
            label = tk.Label(tooltip, text=text, background="#ffffe0", 
                           relief=tk.SOLID, borderwidth=1, font=("Arial", 9))
            label.pack()
            widget.tooltip = tooltip
        
        def hide_tooltip(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip
        
        widget.bind('<Enter>', show_tooltip)
        widget.bind('<Leave>', hide_tooltip)
    
    def ok(self):
        """Validate and accept dialog."""
        if not self.filepath_var.get():
            messagebox.showwarning("Missing File", "Please select a file.")
            return
        
        try:
            timestamp_ms = int(self.timestamp_var.get())
            duration_ms = int(self.duration_var.get())
            marker_code = int(self.marker_var.get())
            
            if timestamp_ms < 0 or duration_ms <= 0:
                raise ValueError("Invalid time values")
            
            if not (1 <= marker_code <= 255):
                messagebox.showwarning("Invalid Marker", "EEG marker code must be between 1 and 255.")
                return
            
            self.result = {
                'filepath': self.filepath_var.get(),
                'timestamp_ms': timestamp_ms,
                'duration_ms': duration_ms,
                'marker_code': marker_code
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


class AudioDeviceDialog:
    """Dialog for selecting audio output device."""
    
    def __init__(self, parent):
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Select Audio Output Device")
        self.dialog.geometry("450x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Instructions
        ttk.Label(self.dialog, text="Select the audio output device for test preview:", 
                 font=('Arial', 10, 'bold')).pack(pady=10, padx=10)
        
        # Get available audio devices
        try:
            devices = []
            device_list = sd.query_devices()
            for i, device in enumerate(device_list):
                # Only show output devices
                if device['max_output_channels'] > 0:
                    devices.append((i, device['name']))
        except Exception as e:
            devices = [(None, "Default Audio Device")]
            print(f"Error getting audio devices: {e}")
        
        # Device list
        list_frame = ttk.Frame(self.dialog)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.device_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, 
                                         font=('Arial', 10))
        self.device_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.device_listbox.yview)
        
        # Populate devices
        self.devices = devices
        for idx, name in devices:
            self.device_listbox.insert(tk.END, name)
        
        # Select first device by default
        if devices:
            self.device_listbox.selection_set(0)
        
        # Buttons
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="OK", command=self.ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side=tk.LEFT, padx=5)
        
        # Center dialog
        self.dialog.update_idletasks()
        x = (parent.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (parent.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        self.dialog.wait_window()
    
    def ok(self):
        """Accept selection."""
        selection = self.device_listbox.curselection()
        if selection:
            idx = selection[0]
            self.result = self.devices[idx][0]  # Return device index
        else:
            self.result = None  # Use default
        self.dialog.destroy()
    
    def cancel(self):
        """Cancel selection."""
        self.result = None
        self.dialog.destroy()


class PreviewWindow:
    """Window for previewing test execution."""
    
    def __init__(self, parent, timeline: TestTimeline, audio_device: int = 0):
        self.timeline = timeline
        self.audio_device = audio_device
        self.window = tk.Toplevel(parent)
        self.window.title("Test Preview")
        self.window.geometry("800x600")
        self.window.transient(parent)
        
        # Store audio device
        self.audio_device = audio_device
        self.audio_enabled = True
        
        # Track playing audio streams
        self.active_audio = {}  # event_id -> stop_event
        
        # Cleanup on close
        self.window.protocol("WM_DELETE_WINDOW", self.cleanup_and_close)
        
        # Preview canvas
        self.canvas = tk.Canvas(self.window, bg='gray', width=800, height=500)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Control panel
        control_frame = ttk.Frame(self.window)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(control_frame, text="▶ Start", command=self.start_preview).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="⏸ Stop", command=self.stop_preview).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Close", command=self.cleanup_and_close).pack(side=tk.RIGHT, padx=5)
        
        # Progress
        self.progress_var = tk.StringVar(value="Ready")
        ttk.Label(control_frame, textvariable=self.progress_var).pack(side=tk.LEFT, padx=20)
        
        self.running = False
        self.preview_thread = None
    
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
        self.stop_all_audio()
    
    def cleanup_and_close(self):
        """Cleanup resources before closing."""
        self.running = False
        self.stop_all_audio()
        self.window.destroy()
    
    def stop_all_audio(self):
        """Stop all currently playing audio."""
        try:
            sd.stop()  # Stop all sounddevice playback
            self.active_audio.clear()
        except:
            pass
    
    def play_audio_file(self, filepath: str, volume: float, event_id: int):
        """Play an audio file using sounddevice."""
        try:
            # Read audio file
            data, samplerate = sf.read(filepath)
            
            # Apply volume
            data = data * volume
            
            # Mark as active
            self.active_audio[event_id] = True
            
            # Play audio on selected device
            sd.play(data, samplerate, device=self.audio_device, blocking=True)
            
            # Remove from active when done
            if event_id in self.active_audio:
                del self.active_audio[event_id]
                
        except Exception as e:
            print(f"Error playing audio: {e}")
            if event_id in self.active_audio:
                del self.active_audio[event_id]
    
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
        
        # Display active events
        for event in events:
            if event.event_type == 'image':
                # Try to show actual image
                try:
                    img = Image.open(event.data['filepath'])
                    # Resize to fit canvas while maintaining aspect ratio
                    img.thumbnail((600, 400), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    
                    # Store reference to prevent garbage collection
                    self._current_image = photo
                    
                    # Position based on event data
                    position = event.data.get('position', 'center')
                    if position == 'center':
                        x, y = 400, 300
                    elif position == 'top-left':
                        x, y = img.width // 2 + 10, img.height // 2 + 10
                    elif position == 'top-right':
                        x, y = 800 - img.width // 2 - 10, img.height // 2 + 10
                    elif position == 'bottom-left':
                        x, y = img.width // 2 + 10, 600 - img.height // 2 - 10
                    elif position == 'bottom-right':
                        x, y = 800 - img.width // 2 - 10, 600 - img.height // 2 - 10
                    else:
                        x, y = 400, 300
                    
                    self.canvas.create_image(x, y, image=photo)
                except Exception as e:
                    # Fallback to placeholder
                    filename = Path(event.data['filepath']).name
                    self.canvas.create_rectangle(250, 150, 550, 350, fill='lightblue', outline='black')
                    self.canvas.create_text(400, 250, text=f"Image:\n{filename}\n(Preview unavailable)", 
                                          font=('Arial', 12), justify=tk.CENTER)
            elif event.event_type == 'audio':
                # Play audio if not already playing
                if self.audio_enabled and event.id not in self.active_audio:
                    try:
                        # Start audio playback in a separate thread
                        volume = event.data.get('volume', 1.0)
                        audio_thread = threading.Thread(
                            target=self.play_audio_file,
                            args=(event.data['filepath'], volume, event.id),
                            daemon=True
                        )
                        audio_thread.start()
                    except Exception as e:
                        print(f"Error starting audio: {e}")
                
                # Show audio indicator in corner
                filename = Path(event.data['filepath']).name
                self.canvas.create_oval(10, 10, 110, 110, fill='lightgreen', outline='black', width=2)
                self.canvas.create_text(60, 60, text=f"🔊\n{filename}", 
                                      font=('Arial', 10), justify=tk.CENTER)
        
        # Stop audio that is no longer active
        current_audio_ids = {event.id for event in events if event.event_type == 'audio'}
        to_remove = []
        for event_id in list(self.active_audio.keys()):
            if event_id not in current_audio_ids:
                to_remove.append(event_id)
        for event_id in to_remove:
            if event_id in self.active_audio:
                del self.active_audio[event_id]
    
    def _clear_display(self):
        """Clear the preview display."""
        self.canvas.delete("all")
        self.stop_all_audio()
        self.progress_var.set("Preview stopped")


class StartupWindow:
    """Startup window for creating new tests or opening existing ones."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Neuroscience Test Maker - Welcome")
        self.root.geometry("700x500")
        self.root.resizable(False, False)
        
        # Center the window
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (700 // 2)
        y = (self.root.winfo_screenheight() // 2) - (500 // 2)
        self.root.geometry(f"700x500+{x}+{y}")
        
        self.recent_tests = self.load_recent_tests()
        self.create_widgets()
    
    def load_recent_tests(self) -> List[str]:
        """Load list of recently opened tests."""
        config_file = Path.home() / '.neuroscience_test_maker' / 'recent.json'
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    data = json.load(f)
                    # Filter to only existing files
                    return [p for p in data.get('recent_tests', []) if Path(p).exists()]
            except:
                pass
        return []
    
    def save_recent_test(self, filepath: str):
        """Save a test to the recent tests list."""
        config_dir = Path.home() / '.neuroscience_test_maker'
        config_dir.mkdir(exist_ok=True)
        config_file = config_dir / 'recent.json'
        
        # Add to front of list, remove duplicates, keep max 10
        recent = [filepath]
        for path in self.recent_tests:
            if path != filepath:
                recent.append(path)
        recent = recent[:10]
        
        try:
            with open(config_file, 'w') as f:
                json.dump({'recent_tests': recent}, f, indent=2)
        except:
            pass
    
    def create_widgets(self):
        """Create the startup window widgets."""
        # Title
        title_label = tk.Label(self.root, text="Neuroscience Test Maker", 
                              font=('Arial', 24, 'bold'), fg='#2c3e50')
        title_label.pack(pady=20)
        
        subtitle_label = tk.Label(self.root, text="Multi-Modal Test Builder for Neuroscience Experiments", 
                                 font=('Arial', 11), fg='#7f8c8d')
        subtitle_label.pack(pady=(0, 30))
        
        # Main action buttons frame
        action_frame = tk.Frame(self.root)
        action_frame.pack(pady=10)
        
        # Create New Test button
        new_btn = tk.Button(action_frame, text="📝 Create New Test", 
                           font=('Arial', 14, 'bold'), bg='#3498db', fg='white',
                           command=self.create_new_test, padx=30, pady=15,
                           cursor='hand2', relief=tk.RAISED, bd=3)
        new_btn.grid(row=0, column=0, padx=10)
        
        # Create from Template button (disabled for now)
        template_btn = tk.Button(action_frame, text="📋 Create from Template", 
                                font=('Arial', 14), bg='#95a5a6', fg='white',
                                state=tk.DISABLED, padx=30, pady=15,
                                relief=tk.RAISED, bd=3)
        template_btn.grid(row=0, column=1, padx=10)
        
        # Open Existing Test button
        open_btn = tk.Button(action_frame, text="📂 Open Test File", 
                            font=('Arial', 14), bg='#2ecc71', fg='white',
                            command=self.open_test, padx=30, pady=15,
                            cursor='hand2', relief=tk.RAISED, bd=3)
        open_btn.grid(row=1, column=0, columnspan=2, pady=10)
        
        # Recent tests section
        if self.recent_tests:
            recent_label = tk.Label(self.root, text="Recent Tests", 
                                   font=('Arial', 12, 'bold'), fg='#2c3e50')
            recent_label.pack(pady=(20, 10))
            
            # Create scrollable frame for recent tests
            recent_frame = tk.Frame(self.root, relief=tk.SUNKEN, bd=1)
            recent_frame.pack(pady=10, padx=40, fill=tk.BOTH, expand=True)
            
            canvas = tk.Canvas(recent_frame, height=150)
            scrollbar = tk.Scrollbar(recent_frame, orient="vertical", command=canvas.yview)
            scrollable_frame = tk.Frame(canvas)
            
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            # Add recent test items
            for i, test_path in enumerate(self.recent_tests):
                self.create_recent_test_item(scrollable_frame, test_path, i)
            
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
        else:
            # No recent tests message
            no_recent_label = tk.Label(self.root, text="No recent tests", 
                                      font=('Arial', 10, 'italic'), fg='#95a5a6')
            no_recent_label.pack(pady=30)
    
    def create_recent_test_item(self, parent, test_path, index):
        """Create a clickable recent test item."""
        item_frame = tk.Frame(parent, relief=tk.RAISED, bd=1, bg='white')
        item_frame.pack(fill=tk.X, padx=5, pady=2)
        
        test_name = Path(test_path).stem
        
        name_label = tk.Label(item_frame, text=test_name, 
                             font=('Arial', 10, 'bold'), bg='white', anchor='w')
        name_label.pack(side=tk.LEFT, padx=10, pady=5, fill=tk.X, expand=True)
        
        path_label = tk.Label(item_frame, text=test_path, 
                             font=('Arial', 8), fg='#7f8c8d', bg='white', anchor='w')
        path_label.pack(side=tk.LEFT, padx=10)
        
        # Make the whole frame clickable
        for widget in [item_frame, name_label, path_label]:
            widget.bind("<Button-1>", lambda e, path=test_path: self.open_recent_test(path))
            widget.bind("<Enter>", lambda e, f=item_frame: f.config(bg='#ecf0f1'))
            widget.bind("<Leave>", lambda e, f=item_frame: f.config(bg='white'))
            widget.config(cursor='hand2')
    
    def create_new_test(self):
        """Create a new test from scratch."""
        self.root.destroy()
        root = tk.Tk()
        app = TestBuilderGUI(root)
        root.mainloop()
    
    def open_test(self):
        """Open an existing test file."""
        filepath = filedialog.askopenfilename(
            title="Open Test File",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filepath:
            self.open_test_file(filepath)
    
    def open_recent_test(self, filepath: str):
        """Open a recent test file."""
        if Path(filepath).exists():
            self.open_test_file(filepath)
        else:
            messagebox.showerror("File Not Found", 
                               f"The file does not exist:\n{filepath}")
    
    def open_test_file(self, filepath: str):
        """Open a test file and launch the editor."""
        self.save_recent_test(filepath)
        self.root.destroy()
        root = tk.Tk()
        app = TestBuilderGUI(root)
        app.load_test(filepath)
        root.mainloop()


def main():
    """Main entry point for the application."""
    root = tk.Tk()
    app = StartupWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Export module for multiple file formats (EEGLAB, E-Prime, JSON).
Supports exporting neuroscience test timelines to various research platforms.
"""

import json
import csv
from typing import Dict, Any, List
from pathlib import Path


class ExportFormats:
    """Handles exporting test timelines to multiple formats."""
    
    # Format definitions
    JSON = "json"
    EEGLAB = "eeglab"
    EPRIME = "eprime"
    
    @staticmethod
    def get_format_info():
        """Get information about available export formats."""
        return {
            ExportFormats.JSON: {
                'name': 'JSON Format',
                'extension': '.json',
                'description': 'Native format (editable)',
                'filter': ('JSON files', '*.json')
            },
            ExportFormats.EEGLAB: {
                'name': 'EEGLAB Event List',
                'extension': '.txt',
                'description': 'Tab-delimited event markers for EEGLAB',
                'filter': ('EEGLAB files', '*.txt')
            },
            ExportFormats.EPRIME: {
                'name': 'E-Prime Format',
                'extension': '.txt',
                'description': 'Tab-delimited format for E-Prime',
                'filter': ('E-Prime files', '*.txt')
            }
        }
    
    @staticmethod
    def export_json(timeline_data: Dict[str, Any], filepath: str):
        """
        Export timeline to JSON format (native format).
        
        Args:
            timeline_data: Dictionary representation of the timeline
            filepath: Output file path
        """
        with open(filepath, 'w') as f:
            json.dump(timeline_data, f, indent=2)
    
    @staticmethod
    def export_eeglab(timeline_data: Dict[str, Any], filepath: str):
        """
        Export timeline to EEGLAB event list format.
        
        EEGLAB expects tab-delimited text with columns:
        - Latency (in samples or seconds)
        - Type (event type/code)
        - Duration (in samples or seconds)
        - Urevent (unique event number)
        
        Args:
            timeline_data: Dictionary representation of the timeline
            filepath: Output file path
        """
        events = timeline_data.get('events', [])
        metadata = timeline_data.get('metadata', {})
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f, delimiter='\t')
            
            # Write header
            writer.writerow(['Latency(ms)', 'Type', 'Duration(ms)', 'EventID', 'StimulusFile'])
            writer.writerow(['# Exported from Neuroscience Test Maker'])
            writer.writerow([f"# Test: {metadata.get('name', 'Untitled')}"])
            writer.writerow([f"# Description: {metadata.get('description', '')}"])
            writer.writerow([])  # Blank line
            
            # Write column headers again for data
            writer.writerow(['Latency(ms)', 'Type', 'Duration(ms)', 'EventID', 'StimulusFile'])
            
            # Write events
            for idx, event in enumerate(events, start=1):
                latency_ms = event.get('timestamp_ms', 0)
                event_type = event.get('event_type', 'unknown')
                duration_ms = event.get('data', {}).get('duration_ms', 0)
                
                # Get stimulus file path if available
                stimulus_file = ''
                if event_type == 'image':
                    stimulus_file = event.get('data', {}).get('file_path', '')
                elif event_type == 'audio':
                    stimulus_file = event.get('data', {}).get('file_path', '')
                
                # Extract filename only for cleaner output
                if stimulus_file:
                    stimulus_file = Path(stimulus_file).name
                
                writer.writerow([
                    latency_ms,
                    event_type,
                    duration_ms,
                    idx,
                    stimulus_file
                ])
    
    @staticmethod
    def export_eprime(timeline_data: Dict[str, Any], filepath: str):
        """
        Export timeline to E-Prime compatible format.
        
        E-Prime expects tab-delimited text with specific columns:
        - Procedure
        - Trial
        - Stimulus
        - OnsetTime
        - Duration
        - Type
        
        Args:
            timeline_data: Dictionary representation of the timeline
            filepath: Output file path
        """
        events = timeline_data.get('events', [])
        metadata = timeline_data.get('metadata', {})
        
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:  # BOM for Excel compatibility
            writer = csv.writer(f, delimiter='\t')
            
            # E-Prime header information
            writer.writerow(['*** Header Start ***'])
            writer.writerow(['VersionNumber:', '1.0'])
            writer.writerow(['LevelName:', 'Session'])
            writer.writerow(['Title:', metadata.get('name', 'Untitled')])
            writer.writerow(['Description:', metadata.get('description', '')])
            writer.writerow(['Exported:', 'Neuroscience Test Maker'])
            writer.writerow(['*** Header End ***'])
            writer.writerow([])
            
            # Column headers
            writer.writerow([
                'Procedure',
                'Trial',
                'Stimulus',
                'StimulusFile',
                'OnsetTime',
                'Duration',
                'Type',
                'Modality'
            ])
            
            # Write events
            for idx, event in enumerate(events, start=1):
                event_type = event.get('event_type', 'unknown')
                onset_ms = event.get('timestamp_ms', 0)
                duration_ms = event.get('data', {}).get('duration_ms', 0)
                
                # Get stimulus identifier
                stimulus_name = f"{event_type}_{idx}"
                stimulus_file = ''
                
                if event_type == 'image':
                    stimulus_file = event.get('data', {}).get('file_path', '')
                elif event_type == 'audio':
                    stimulus_file = event.get('data', {}).get('file_path', '')
                
                # Extract filename only
                if stimulus_file:
                    stimulus_file = Path(stimulus_file).name
                    stimulus_name = Path(stimulus_file).stem
                
                writer.writerow([
                    'TrialProc',           # Procedure
                    idx,                   # Trial number
                    stimulus_name,         # Stimulus name
                    stimulus_file,         # Stimulus file
                    onset_ms,              # OnsetTime (ms)
                    duration_ms,           # Duration (ms)
                    event_type,            # Type
                    event_type.upper()     # Modality
                ])
            
            # E-Prime footer
            writer.writerow([])
            writer.writerow(['*** End of data ***'])
    
    @staticmethod
    def export_timeline(timeline_data: Dict[str, Any], filepath: str, format_type: str):
        """
        Export timeline to specified format.
        
        Args:
            timeline_data: Dictionary representation of the timeline
            filepath: Output file path
            format_type: One of ExportFormats constants (JSON, EEGLAB, EPRIME)
        
        Raises:
            ValueError: If format_type is not supported
        """
        if format_type == ExportFormats.JSON:
            ExportFormats.export_json(timeline_data, filepath)
        elif format_type == ExportFormats.EEGLAB:
            ExportFormats.export_eeglab(timeline_data, filepath)
        elif format_type == ExportFormats.EPRIME:
            ExportFormats.export_eprime(timeline_data, filepath)
        else:
            raise ValueError(f"Unsupported export format: {format_type}")
    
    @staticmethod
    def get_file_filters():
        """
        Get file type filters for save dialog.
        
        Returns:
            List of tuples (description, pattern) for file dialog
        """
        formats = ExportFormats.get_format_info()
        filters = [
            ("All supported formats", "*.json *.txt"),
        ]
        
        for format_type, info in formats.items():
            filters.append(info['filter'])
        
        filters.append(("All files", "*.*"))
        return filters
    
    @staticmethod
    def detect_format_from_extension(filepath: str) -> str:
        """
        Detect export format from file extension.
        
        Args:
            filepath: File path with extension
            
        Returns:
            Format type constant (JSON, EEGLAB, or EPRIME)
        """
        ext = Path(filepath).suffix.lower()
        
        if ext == '.json':
            return ExportFormats.JSON
        elif ext == '.txt':
            # For .txt files, check filename for hints
            filename = Path(filepath).stem.lower()
            if 'eeglab' in filename or 'eeg' in filename:
                return ExportFormats.EEGLAB
            elif 'eprime' in filename or 'e-prime' in filename:
                return ExportFormats.EPRIME
            else:
                # Default to EEGLAB for generic .txt files
                return ExportFormats.EEGLAB
        else:
            # Default to JSON
            return ExportFormats.JSON

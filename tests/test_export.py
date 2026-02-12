#!/usr/bin/env python3
"""
Test script for export functionality.
Tests exporting to JSON, EEGLAB, and E-Prime formats.
"""

import sys
import os
from pathlib import Path
import tempfile

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from export_formats import ExportFormats


def create_sample_timeline_data():
    """Create sample timeline data for testing (without importing test_maker)."""
    return {
        'metadata': {
            'name': 'Sample Export Test',
            'description': 'Testing multi-format export functionality',
            'duration_ms': 5000
        },
        'events': [
            {
                'event_type': 'image',
                'timestamp_ms': 0,
                'data': {
                    'file_path': 'images/stimulus1.jpg',
                    'duration_ms': 1000
                }
            },
            {
                'event_type': 'audio',
                'timestamp_ms': 500,
                'data': {
                    'file_path': 'audio/tone1.wav',
                    'duration_ms': 2000
                }
            },
            {
                'event_type': 'image',
                'timestamp_ms': 2000,
                'data': {
                    'file_path': 'images/stimulus2.jpg',
                    'duration_ms': 1500
                }
            },
            {
                'event_type': 'audio',
                'timestamp_ms': 3000,
                'data': {
                    'file_path': 'audio/tone2.wav',
                    'duration_ms': 1000
                }
            }
        ]
    }


def test_json_export():
    """Test JSON export."""
    print("\n=== Testing JSON Export ===")
    timeline_data = create_sample_timeline_data()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        filepath = f.name
    
    try:
        ExportFormats.export_json(timeline_data, filepath)
        
        # Read back and verify
        with open(filepath, 'r') as f:
            content = f.read()
            if 'Sample Export Test' in content and 'stimulus1.jpg' in content:
                print("✓ JSON export successful")
                print(f"  File: {filepath}")
                print(f"  Size: {len(content)} bytes")
                return True
            else:
                print("✗ JSON export failed - content verification failed")
                return False
    except Exception as e:
        print(f"✗ JSON export failed: {e}")
        return False
    finally:
        if os.path.exists(filepath):
            os.unlink(filepath)


def test_eeglab_export():
    """Test EEGLAB export."""
    print("\n=== Testing EEGLAB Export ===")
    timeline_data = create_sample_timeline_data()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='_eeglab.txt', delete=False) as f:
        filepath = f.name
    
    try:
        ExportFormats.export_eeglab(timeline_data, filepath)
        
        # Read back and verify
        with open(filepath, 'r') as f:
            content = f.read()
            # Check for expected headers and data
            if ('Latency(ms)' in content and 
                'Type' in content and 
                'stimulus1.jpg' in content):
                print("✓ EEGLAB export successful")
                print(f"  File: {filepath}")
                print(f"  Preview:")
                lines = content.split('\n')
                for line in lines[:8]:  # Show first 8 lines
                    print(f"    {line}")
                return True
            else:
                print("✗ EEGLAB export failed - content verification failed")
                return False
    except Exception as e:
        print(f"✗ EEGLAB export failed: {e}")
        return False
    finally:
        if os.path.exists(filepath):
            os.unlink(filepath)


def test_eprime_export():
    """Test E-Prime export."""
    print("\n=== Testing E-Prime Export ===")
    timeline_data = create_sample_timeline_data()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='_eprime.txt', delete=False) as f:
        filepath = f.name
    
    try:
        ExportFormats.export_eprime(timeline_data, filepath)
        
        # Read back and verify
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            content = f.read()
            # Check for expected headers and data
            if ('Procedure' in content and 
                'OnsetTime' in content and 
                'TrialProc' in content):
                print("✓ E-Prime export successful")
                print(f"  File: {filepath}")
                print(f"  Preview:")
                lines = content.split('\n')
                for line in lines[:12]:  # Show first 12 lines
                    print(f"    {line}")
                return True
            else:
                print("✗ E-Prime export failed - content verification failed")
                return False
    except Exception as e:
        print(f"✗ E-Prime export failed: {e}")
        return False
    finally:
        if os.path.exists(filepath):
            os.unlink(filepath)


def test_format_detection():
    """Test format detection from file extension."""
    print("\n=== Testing Format Detection ===")
    
    tests = [
        ('test.json', ExportFormats.JSON),
        ('data_eeglab.txt', ExportFormats.EEGLAB),
        ('experiment_eprime.txt', ExportFormats.EPRIME),
        ('generic.txt', ExportFormats.EEGLAB),  # Default for .txt
    ]
    
    all_passed = True
    for filepath, expected_format in tests:
        detected = ExportFormats.detect_format_from_extension(filepath)
        if detected == expected_format:
            print(f"✓ {filepath} -> {detected}")
        else:
            print(f"✗ {filepath} -> {detected} (expected {expected_format})")
            all_passed = False
    
    return all_passed


def main():
    """Run all export tests."""
    print("="*60)
    print("Export Functionality Test Suite")
    print("="*60)
    
    results = {
        'JSON Export': test_json_export(),
        'EEGLAB Export': test_eeglab_export(),
        'E-Prime Export': test_eprime_export(),
        'Format Detection': test_format_detection(),
    }
    
    print("\n" + "="*60)
    print("Test Results Summary")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(results.values())
    print("\n" + "="*60)
    if all_passed:
        print("✓ All tests passed!")
    else:
        print("✗ Some tests failed")
    print("="*60 + "\n")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

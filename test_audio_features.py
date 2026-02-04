#!/usr/bin/env python3
"""
Test script to validate the new audio features.
"""

import pygame
from pathlib import Path
import os

def test_basic_audio_access():
    """Test accessing basic auditory stimulus files."""
    print("Testing basic auditory stimulus access...")
    
    basic_audio_path = Path(__file__).parent / 'basic_auditory_stimulus'
    print(f"Audio folder exists: {basic_audio_path.exists()}")
    
    if basic_audio_path.exists():
        wav_files = list(basic_audio_path.glob('*.wav'))
        print(f"Found {len(wav_files)} .wav files")
        
        if wav_files:
            print("First 5 files:")
            for file in sorted(wav_files)[:5]:
                print(f"  - {file.name}")
        return wav_files
    else:
        print("Basic audio folder not found!")
        return []

def test_pygame_audio(wav_files):
    """Test pygame audio functionality."""
    print("\nTesting pygame audio functionality...")
    
    if not wav_files:
        print("No audio files to test!")
        return
    
    # Initialize pygame mixer
    try:
        pygame.mixer.init()
        print("Pygame mixer initialized successfully")
    except pygame.error as e:
        print(f"Failed to initialize pygame mixer: {e}")
        return
    
    # Test loading a file
    test_file = wav_files[0]
    print(f"Testing with file: {test_file.name}")
    
    try:
        sound = pygame.mixer.Sound(str(test_file))
        print(f"Successfully loaded audio file: {test_file.name}")
        print(f"File length: {sound.get_length():.2f} seconds")
        
        # Test playing (but don't actually play in the test)
        print("Audio file can be played (not playing in this test)")
        
    except pygame.error as e:
        print(f"Failed to load audio file: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

def main():
    """Main test function."""
    print("Audio Features Test")
    print("==================")
    
    wav_files = test_basic_audio_access()
    test_pygame_audio(wav_files)
    
    print("\nTest completed!")

if __name__ == "__main__":
    main()
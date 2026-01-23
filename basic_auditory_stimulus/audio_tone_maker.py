#!/usr/bin/env python3
"""
Audio Tone Maker
Generates sine wave tones at specified frequencies for neuroscience experiments.
"""

import numpy as np
import wave
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
import math


class ToneGenerator:
    """Class for generating audio tones."""
    
    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate
    
    def generate_tone(self, frequency, duration_seconds, amplitude=0.5):
        """
        Generate a sine wave tone.
        
        Args:
            frequency (float): Frequency in Hz
            duration_seconds (float): Duration in seconds
            amplitude (float): Amplitude (0.0 to 1.0)
        
        Returns:
            numpy.ndarray: Audio samples
        """
        num_samples = int(self.sample_rate * duration_seconds)
        t = np.linspace(0, duration_seconds, num_samples, False)
        
        # Generate sine wave
        wave_data = amplitude * np.sin(2 * np.pi * frequency * t)
        
        # Convert to 16-bit integers
        audio_data = (wave_data * 32767).astype(np.int16)
        
        return audio_data
    
    def save_tone(self, audio_data, filename):
        """
        Save audio data to a WAV file.
        
        Args:
            audio_data (numpy.ndarray): Audio samples
            filename (str): Output filename
        """
        with wave.open(filename, 'w') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(audio_data.tobytes())
    
    def generate_frequency_range(self, start_freq, end_freq, step, duration_seconds, 
                                output_dir, amplitude=0.5, prefix="tone"):
        """
        Generate a range of tones.
        
        Args:
            start_freq (float): Starting frequency in Hz
            end_freq (float): Ending frequency in Hz
            step (float): Frequency step in Hz
            duration_seconds (float): Duration of each tone in seconds
            output_dir (str): Output directory
            amplitude (float): Amplitude (0.0 to 1.0)
            prefix (str): Filename prefix
        
        Returns:
            list: List of generated filenames
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        generated_files = []
        frequencies = np.arange(start_freq, end_freq + step, step)
        
        for freq in frequencies:
            # Generate tone
            audio_data = self.generate_tone(freq, duration_seconds, amplitude)
            
            # Create filename
            if freq.is_integer():
                filename = f"{prefix}_{int(freq)}Hz.wav"
            else:
                filename = f"{prefix}_{freq:.1f}Hz.wav"
            
            filepath = output_path / filename
            
            # Save tone
            self.save_tone(audio_data, str(filepath))
            generated_files.append(str(filepath))
        
        return generated_files


class ToneGeneratorGUI:
    """GUI for the tone generator."""
    
    def __init__(self, parent=None):
        self.generator = ToneGenerator()
        
        # Create window
        if parent:
            self.window = tk.Toplevel(parent)
            self.window.transient(parent)
            self.window.grab_set()
        else:
            self.window = tk.Tk()
        
        self.window.title("Audio Tone Generator")
        self.window.geometry("500x600")
        
        self.setup_gui()
        
        # Center window
        self.window.update_idletasks()
        if parent:
            x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.window.winfo_width() // 2)
            y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.window.winfo_height() // 2)
            self.window.geometry(f"+{x}+{y}")
    
    def setup_gui(self):
        """Set up the GUI elements."""
        # Main frame
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Audio Tone Generator", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # Frequency settings
        freq_frame = ttk.LabelFrame(main_frame, text="Frequency Settings", padding="10")
        freq_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Start frequency
        ttk.Label(freq_frame, text="Start Frequency (Hz):").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.start_freq_var = tk.StringVar(value="100")
        ttk.Entry(freq_frame, textvariable=self.start_freq_var, width=15).grid(row=0, column=1, padx=(10, 0), pady=2)
        
        # End frequency
        ttk.Label(freq_frame, text="End Frequency (Hz):").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.end_freq_var = tk.StringVar(value="1000")
        ttk.Entry(freq_frame, textvariable=self.end_freq_var, width=15).grid(row=1, column=1, padx=(10, 0), pady=2)
        
        # Step size
        ttk.Label(freq_frame, text="Step Size (Hz):").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.step_var = tk.StringVar(value="100")
        ttk.Entry(freq_frame, textvariable=self.step_var, width=15).grid(row=2, column=1, padx=(10, 0), pady=2)
        
        # Audio settings
        audio_frame = ttk.LabelFrame(main_frame, text="Audio Settings", padding="10")
        audio_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Duration
        ttk.Label(audio_frame, text="Duration (seconds):").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.duration_var = tk.StringVar(value="1.0")
        ttk.Entry(audio_frame, textvariable=self.duration_var, width=15).grid(row=0, column=1, padx=(10, 0), pady=2)
        
        # Amplitude
        ttk.Label(audio_frame, text="Amplitude (0.0-1.0):").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.amplitude_var = tk.StringVar(value="0.5")
        ttk.Entry(audio_frame, textvariable=self.amplitude_var, width=15).grid(row=1, column=1, padx=(10, 0), pady=2)
        
        # Output settings
        output_frame = ttk.LabelFrame(main_frame, text="Output Settings", padding="10")
        output_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Output directory
        ttk.Label(output_frame, text="Output Directory:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.output_dir_var = tk.StringVar(value=str(Path(__file__).parent))
        dir_entry = ttk.Entry(output_frame, textvariable=self.output_dir_var, width=35)
        dir_entry.grid(row=0, column=1, padx=(10, 5), pady=2)
        ttk.Button(output_frame, text="Browse", command=self.browse_directory).grid(row=0, column=2, pady=2)
        
        # Filename prefix
        ttk.Label(output_frame, text="Filename Prefix:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.prefix_var = tk.StringVar(value="tone")
        ttk.Entry(output_frame, textvariable=self.prefix_var, width=15).grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # Quick presets
        preset_frame = ttk.LabelFrame(main_frame, text="Quick Presets", padding="10")
        preset_frame.pack(fill=tk.X, pady=(0, 10))
        
        preset_buttons_frame = ttk.Frame(preset_frame)
        preset_buttons_frame.pack()
        
        ttk.Button(preset_buttons_frame, text="Basic Range\n(100-1000Hz)", 
                  command=self.preset_basic).pack(side=tk.LEFT, padx=5)
        ttk.Button(preset_buttons_frame, text="Extended Range\n(100-5000Hz)", 
                  command=self.preset_extended).pack(side=tk.LEFT, padx=5)
        ttk.Button(preset_buttons_frame, text="High Frequency\n(1000-10000Hz)", 
                  command=self.preset_high).pack(side=tk.LEFT, padx=5)
        
        # Single tone section
        single_frame = ttk.LabelFrame(main_frame, text="Generate Single Tone", padding="10")
        single_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(single_frame, text="Frequency (Hz):").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.single_freq_var = tk.StringVar(value="440")
        ttk.Entry(single_frame, textvariable=self.single_freq_var, width=15).grid(row=0, column=1, padx=(10, 0), pady=2)
        ttk.Button(single_frame, text="Generate Single Tone", 
                  command=self.generate_single_tone).grid(row=0, column=2, padx=(20, 0), pady=2)
        
        # Progress and status
        self.progress_var = tk.StringVar(value="Ready")
        ttk.Label(main_frame, textvariable=self.progress_var).pack(pady=(10, 5))
        
        self.progress_bar = ttk.Progressbar(main_frame, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=(0, 10))
        
        # Generate button
        generate_btn = ttk.Button(main_frame, text="Generate Tone Range", 
                                 command=self.generate_tones)
        generate_btn.pack(pady=10)
        
        # Close button
        ttk.Button(main_frame, text="Close", command=self.window.destroy).pack()
    
    def browse_directory(self):
        """Browse for output directory."""
        directory = filedialog.askdirectory(title="Select Output Directory", 
                                          initialdir=self.output_dir_var.get())
        if directory:
            self.output_dir_var.set(directory)
    
    def preset_basic(self):
        """Set basic frequency range preset."""
        self.start_freq_var.set("100")
        self.end_freq_var.set("1000")
        self.step_var.set("100")
    
    def preset_extended(self):
        """Set extended frequency range preset."""
        self.start_freq_var.set("100")
        self.end_freq_var.set("5000")
        self.step_var.set("100")
    
    def preset_high(self):
        """Set high frequency range preset."""
        self.start_freq_var.set("1000")
        self.end_freq_var.set("10000")
        self.step_var.set("500")
    
    def validate_inputs(self):
        """Validate user inputs."""
        try:
            start_freq = float(self.start_freq_var.get())
            end_freq = float(self.end_freq_var.get())
            step = float(self.step_var.get())
            duration = float(self.duration_var.get())
            amplitude = float(self.amplitude_var.get())
            
            if start_freq <= 0 or end_freq <= 0 or step <= 0:
                raise ValueError("Frequencies and step must be positive")
            
            if start_freq >= end_freq:
                raise ValueError("Start frequency must be less than end frequency")
            
            if duration <= 0:
                raise ValueError("Duration must be positive")
            
            if not (0.0 <= amplitude <= 1.0):
                raise ValueError("Amplitude must be between 0.0 and 1.0")
            
            if not os.path.exists(self.output_dir_var.get()):
                raise ValueError("Output directory does not exist")
            
            return start_freq, end_freq, step, duration, amplitude
            
        except ValueError as e:
            messagebox.showerror("Invalid Input", str(e))
            return None
    
    def generate_single_tone(self):
        """Generate a single tone."""
        try:
            frequency = float(self.single_freq_var.get())
            duration = float(self.duration_var.get())
            amplitude = float(self.amplitude_var.get())
            
            if frequency <= 0:
                raise ValueError("Frequency must be positive")
            
            # Generate tone
            audio_data = self.generator.generate_tone(frequency, duration, amplitude)
            
            # Create filename
            prefix = self.prefix_var.get() or "tone"
            if frequency.is_integer():
                filename = f"{prefix}_{int(frequency)}Hz.wav"
            else:
                filename = f"{prefix}_{frequency:.1f}Hz.wav"
            
            filepath = Path(self.output_dir_var.get()) / filename
            
            # Save tone
            self.generator.save_tone(audio_data, str(filepath))
            
            self.progress_var.set(f"Generated: {filename}")
            messagebox.showinfo("Success", f"Generated single tone: {filename}")
            
        except ValueError as e:
            messagebox.showerror("Invalid Input", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate tone: {str(e)}")
    
    def generate_tones(self):
        """Generate the tone range."""
        inputs = self.validate_inputs()
        if not inputs:
            return
        
        start_freq, end_freq, step, duration, amplitude = inputs
        
        try:
            # Calculate number of tones
            frequencies = np.arange(start_freq, end_freq + step, step)
            total_tones = len(frequencies)
            
            # Setup progress bar
            self.progress_bar['maximum'] = total_tones
            self.progress_bar['value'] = 0
            
            # Generate tones
            prefix = self.prefix_var.get() or "tone"
            output_dir = self.output_dir_var.get()
            
            generated_files = []
            
            for i, freq in enumerate(frequencies):
                # Update progress
                self.progress_var.set(f"Generating {freq:.1f}Hz... ({i+1}/{total_tones})")
                self.progress_bar['value'] = i + 1
                self.window.update()
                
                # Generate tone
                audio_data = self.generator.generate_tone(freq, duration, amplitude)
                
                # Create filename
                if freq.is_integer():
                    filename = f"{prefix}_{int(freq)}Hz.wav"
                else:
                    filename = f"{prefix}_{freq:.1f}Hz.wav"
                
                filepath = Path(output_dir) / filename
                
                # Save tone
                self.generator.save_tone(audio_data, str(filepath))
                generated_files.append(filename)
            
            # Complete
            self.progress_var.set(f"Generated {len(generated_files)} tones successfully!")
            messagebox.showinfo("Success", 
                              f"Generated {len(generated_files)} tones in:\n{output_dir}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate tones: {str(e)}")
        finally:
            self.progress_bar['value'] = 0


def main():
    """Main function for standalone usage."""
    app = ToneGeneratorGUI()
    app.window.mainloop()


if __name__ == "__main__":
    main()
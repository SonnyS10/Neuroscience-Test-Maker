#!/usr/bin/env python3
"""
Launcher script for Neuroscience Test Maker.
Provides a menu to choose between GUI mode and demo mode.
"""

import sys
import subprocess


def check_display():
    """Check if display is available for GUI."""
    import os
    return 'DISPLAY' in os.environ or sys.platform == 'win32' or sys.platform == 'darwin'


def show_menu():
    """Show launcher menu."""
    print("\n" + "="*60)
    print("  Neuroscience Test Maker - Launcher")
    print("="*60)
    print("\nPlease select an option:")
    print("\n  1. Launch GUI Application")
    print("  2. Run Command-Line Demo")
    print("  3. Run Core Logic Tests")
    print("  4. Exit")
    print("\n" + "="*60)
    
    choice = input("\nEnter your choice (1-4): ").strip()
    return choice


def launch_gui():
    """Launch the GUI application."""
    if not check_display():
        print("\n⚠ Warning: No display detected!")
        print("The GUI requires a graphical display to run.")
        print("You may want to run the demo instead (option 2).\n")
        response = input("Continue anyway? (y/n): ").strip().lower()
        if response != 'y':
            return
    
    print("\nLaunching GUI application...")
    print("(Press Ctrl+C to exit)\n")
    try:
        subprocess.run([sys.executable, 'test_maker.py'])
    except KeyboardInterrupt:
        print("\n\nGUI closed.")
    except Exception as e:
        print(f"\n✗ Error launching GUI: {e}")


def run_demo():
    """Run the command-line demo."""
    print("\nRunning command-line demo...\n")
    try:
        subprocess.run([sys.executable, 'demo.py'])
    except Exception as e:
        print(f"\n✗ Error running demo: {e}")


def run_tests():
    """Run the test suite."""
    print("\nRunning core logic tests...\n")
    try:
        result = subprocess.run([sys.executable, 'test_core.py'])
        if result.returncode == 0:
            print("\n✓ All tests passed!")
        else:
            print("\n✗ Some tests failed.")
    except Exception as e:
        print(f"\n✗ Error running tests: {e}")


def main():
    """Main launcher function."""
    while True:
        choice = show_menu()
        
        if choice == '1':
            launch_gui()
        elif choice == '2':
            run_demo()
        elif choice == '3':
            run_tests()
        elif choice == '4':
            print("\nExiting. Goodbye!\n")
            break
        else:
            print("\n✗ Invalid choice. Please enter 1, 2, 3, or 4.")
        
        if choice in ['1', '2', '3']:
            input("\nPress Enter to continue...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nExiting. Goodbye!\n")

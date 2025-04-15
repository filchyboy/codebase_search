#!/usr/bin/env python3
"""
Debug script to test the CLI's threading and console output.
This will help identify issues with the search output not displaying properly.
"""

import os
import sys
import time
import threading
import subprocess
from pathlib import Path

def run_command(cmd):
    """Run a shell command and return its output."""
    try:
        result = subprocess.run(cmd, shell=True, check=True, 
                              capture_output=True, text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"

def get_terminal_width():
    """Get the terminal width."""
    try:
        return os.get_terminal_size().columns
    except:
        return 80

def print_divider():
    """Print a divider line."""
    width = get_terminal_width()
    print("-" * width)

def test_output_interleaving():
    """Test if output from different threads gets interleaved."""
    print("\nTesting output interleaving...")
    print_divider()
    
    def thread_function(thread_id):
        for i in range(5):
            print(f"Thread {thread_id} message {i}")
            time.sleep(0.1)
    
    # Create and start threads
    threads = []
    for i in range(3):
        t = threading.Thread(target=thread_function, args=(i,))
        threads.append(t)
        t.start()
    
    # Wait for threads to finish
    for t in threads:
        t.join()
    
    print_divider()
    print("If the output is interleaved, the CLI might have similar issues")
    print("with multiple threads printing to the console simultaneously.")

def test_signal_handling():
    """Test signal handling to see if it's interfering with output."""
    print("\nTesting signal handling...")
    print_divider()
    
    def signal_handler():
        print("Signal handler called")
        time.sleep(0.5)
        print("Signal handler complete")
    
    # Simulate a signal being received
    print("Simulating signal receipt...")
    signal_thread = threading.Thread(target=signal_handler)
    signal_thread.start()
    
    # Print while signal is being handled
    for i in range(5):
        print(f"Main thread message {i}")
        time.sleep(0.1)
    
    signal_thread.join()
    print_divider()
    print("If output is interrupted, signals might be affecting CLI output.")

def test_rich_console():
    """Test if Rich console formatting affects output visibility."""
    print("\nTesting Rich console simulation...")
    print_divider()
    
    # Simulate Rich console output with ANSI colors
    print("\033[32mThis is green text\033[0m")
    print("\033[1mThis is bold text\033[0m")
    print("\033[3mThis is italic text\033[0m")
    print("\033[4mThis is underlined text\033[0m")
    
    # Simulate a status message
    print("\033[2mStatus: Background process running...\033[0m")
    
    # Print normal text after
    print("This is normal text that should appear after formatted text")
    print_divider()
    print("If formatted text doesn't appear correctly, it might explain")
    print("why the search report with Rich formatting isn't visible.")

def simulate_search_command():
    """Simulate the search command with direct printing."""
    print("\nSimulating search command...")
    print_divider()
    
    # Simulate the search process
    print("Starting search...")
    time.sleep(0.5)
    
    # Simulate a background process message
    print("\033[2mIndex update started in background\033[0m")
    
    # Simulate search results
    found_count = 42
    files_count = 5
    
    # Simulate direct printing (what we added in our fix)
    print("\nDEBUG: Search report should appear below this line")
    print(f"Found {found_count} matches in {files_count} files")
    
    # Simulate Rich console output (might not appear)
    print("\033[1;32m\nSEARCH REPORT: 'test'\033[0m")
    print("\033[0;36m• Total files in directory:    100\033[0m")
    print("\033[0;36m• Files searched:              80\033[0m")
    print("\033[0;36m• Files skipped/excluded:      20\033[0m")
    print("\033[0;36m• Files with matches:          5\033[0m")
    print("\033[0;36m• Total matches found:         42\033[0m")
    
    print_divider()
    print("If you can see the direct DEBUG line but not the formatted report,")
    print("the CLI is likely having issues with Rich console formatting.")

def main():
    """Run all tests."""
    print("=== DEBUG OUTPUT TESTS ===")
    print("These tests will help diagnose issues with the CLI output")
    
    test_output_interleaving()
    test_signal_handling()
    test_rich_console()
    simulate_search_command()
    
    print("\nAll tests complete. Check the output above to diagnose CLI issues.")

if __name__ == "__main__":
    main()
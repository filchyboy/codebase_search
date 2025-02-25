#!/usr/bin/env python3
"""
Report script that directly runs a search and shows detailed results.
This bypasses the CLI interface to provide clear, direct results.
"""

import os
import re
import glob
import time
from pathlib import Path

def count_files(base_dir):
    """Count total files in the directory."""
    count = 0
    for root, _, files in os.walk(base_dir):
        count += len(files)
    return count

def search_with_report(base_dir, search_term):
    """Run a search with detailed reporting."""
    print(f"\n--- SEARCH REPORT: '{search_term}' ---")
    
    # Start timing
    start_time = time.time()
    
    # Track statistics
    total_files = count_files(base_dir)
    files_searched = 0
    files_skipped = 0
    files_with_matches = 0
    total_matches = 0
    matches = []
    
    # Excluded directories - hardcoded for simplicity in this report
    excluded_dirs = [".git", "node_modules", "vendor", "dist", "build", "__pycache__"]
    
    # Files we'll skip (binary and large files)
    excluded_extensions = [".pyc", ".pyo", ".exe", ".dll", ".obj", ".bin", 
                          ".jpg", ".png", ".gif", ".zip", ".tar.gz"]
    
    # Walk the directory tree
    for root, dirs, files in os.walk(base_dir):
        # Skip excluded directories (modify dirs in-place)
        for excl in excluded_dirs:
            if excl in dirs:
                files_skipped += 1
                dirs.remove(excl)
        
        # Process each file
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, base_dir)
            
            # Skip excluded file types
            if any(file.endswith(ext) for ext in excluded_extensions):
                files_skipped += 1
                continue
                
            # Skip large files (over 1MB)
            try:
                if os.path.getsize(file_path) > 1000000:
                    files_skipped += 1
                    continue
            except:
                files_skipped += 1
                continue
                
            # Count this file as searched
            files_searched += 1
            
            # Try to read and search the file
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    file_matches = 0
                    for i, line in enumerate(f, 1):
                        if search_term in line:
                            file_matches += 1
                            total_matches += 1
                            matches.append((rel_path, i, line.strip()))
                    
                    if file_matches > 0:
                        files_with_matches += 1
            except:
                # Skip files we can't read
                pass
    
    # Calculate elapsed time
    elapsed = time.time() - start_time
    
    # Print report
    print(f"\nSearch completed in {elapsed:.2f} seconds")
    print(f"Total files in directory:    {total_files}")
    print(f"Files searched:              {files_searched}")
    print(f"Files skipped/excluded:      {files_skipped}")
    print(f"Files with matches:          {files_with_matches}")
    print(f"Total matches found:         {total_matches}")
    
    # Show first 10 matches
    if matches:
        print("\nFirst 10 matches:")
        for i, (file, line_num, content) in enumerate(matches[:10]):
            # Truncate long content
            if len(content) > 80:
                content = content[:77] + "..."
            print(f"{i+1}. {file}:{line_num} - {content}")
        
        if len(matches) > 10:
            print(f"\n... and {len(matches) - 10} more matches.")
    else:
        print("\nNo matches found.")
    
    # Compare with the expected 78 matches for "match"
    if search_term == "match" and total_matches != 78:
        print(f"\nNOTE: Expected 78 matches for 'match', but found {total_matches}.")
        print("This might indicate filtering or search differences between this script and the CLI.")

if __name__ == "__main__":
    # Use same base directory as the CLI
    base_dir = "/Users/malevich/Repos/codebase_search"
    
    # Search for multiple terms to compare results
    terms = ["match", "exclusion", "search", "config"]
    for term in terms:
        search_with_report(base_dir, term)
        print("\n" + "-" * 60)
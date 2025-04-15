#!/usr/bin/env python3
"""
Simple search script that doesn't rely on the CLI infrastructure.
Uses basic file search to find matches in the codebase.
"""

import os
import re
from pathlib import Path

def simple_search(base_dir, search_term):
    """Simple search implementation to find matches."""
    print(f"Searching for '{search_term}' in {base_dir}")
    
    # Excluded directories - match our settings
    excluded_dirs = [".git", "node_modules", "vendor", "js"]
    
    # Files we'll skip
    excluded_extensions = [".pyc", ".pyo", ".exe", ".dll", ".obj", ".bin"]
    
    # Track found matches
    matches = []
    
    # Walk the directory
    for root, dirs, files in os.walk(base_dir):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in excluded_dirs]
        
        for file in files:
            # Skip excluded file types
            if any(file.endswith(ext) for ext in excluded_extensions):
                continue
                
            # Get the full path
            file_path = os.path.join(root, file)
            
            # Skip large files (> 1MB)
            if os.path.getsize(file_path) > 1000000:
                continue
                
            # Try to read the file
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for i, line in enumerate(f, 1):
                        if search_term in line:
                            rel_path = os.path.relpath(file_path, base_dir)
                            matches.append((rel_path, i, line.strip()))
            except Exception as e:
                # Skip files we can't read
                pass
    
    # Print results
    print(f"\nFound {len(matches)} matches:\n")
    
    for file_path, line_num, line_content in matches[:20]:  # Show top 20
        print(f"{file_path}:{line_num} - {line_content[:100]}")
        
    if len(matches) > 20:
        print(f"\n... and {len(matches) - 20} more matches")

if __name__ == "__main__":
    base_dir = "/Users/malevich/Repos/codebase_search"
    search_term = "match"
    simple_search(base_dir, search_term)
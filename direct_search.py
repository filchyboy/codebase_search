#!/usr/bin/env python3

"""
Simplified direct search tool that avoids the CLI infrastructure.
This tool will help diagnose issues with the search process.
"""

import os
import re
import sys
from pathlib import Path

# Add the directory containing code-search-cli to the path
sys.path.insert(0, os.path.dirname(__file__))

# Try various import approaches
HAS_CLI_MODULES = False

try:
    print("Attempting to import directly from 'code-search-cli'...")
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "code-search-cli"))
    from cli.managers.search_engine import SearchEngine
    from cli.managers.config_manager import ConfigManager
    HAS_CLI_MODULES = True
    print("Direct import successful")
except ImportError as e:
    print(f"Direct import failed: {str(e)}")
    
    try:
        print("Attempting alternate import path...")
        # Try the current directory structure
        from code_search_cli.cli.managers.search_engine import SearchEngine
        from code_search_cli.cli.managers.config_manager import ConfigManager
        HAS_CLI_MODULES = True
        print("Alternate import successful")
    except ImportError as e:
        print(f"Alternate import failed: {str(e)}")
        print("Using basic search instead")
        HAS_CLI_MODULES = False

def simple_search(base_dir, query):
    """Basic search implementation that doesn't depend on CLI modules."""
    print(f"Searching for '{query}' in {base_dir}")
    
    matches = []
    files_searched = 0
    
    # Walk the directory tree
    for root, dirs, files in os.walk(base_dir):
        # Skip common excluded directories
        dirs[:] = [d for d in dirs if d not in [".git", "node_modules", "vendor"]]
        
        for file in files:
            # Skip binary and non-text files
            if any(file.endswith(ext) for ext in [".pyc", ".pyo", ".exe", ".dll", ".jpg", ".png"]):
                continue
                
            file_path = os.path.join(root, file)
            
            # Skip large files
            try:
                if os.path.getsize(file_path) > 1000000:  # 1MB
                    continue
            except:
                continue
                
            files_searched += 1
            
            # Try to read the file
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for i, line in enumerate(f, 1):
                        if query in line:
                            matches.append((file_path, i, line.strip()))
            except:
                pass
    
    # Print results
    print(f"\nFound {len(matches)} matches in {len(set(m[0] for m in matches))} files")
    print(f"Files searched: {files_searched}")
    
    # Show first 10 matches
    if matches:
        print("\nFirst 10 matches:")
        for i, (file_path, line_num, content) in enumerate(matches[:10]):
            rel_path = os.path.relpath(file_path, base_dir)
            print(f"{i+1}. {rel_path}:{line_num} - {content[:80]}")
        
        if len(matches) > 10:
            print(f"\n... and {len(matches) - 10} more matches")

def cli_search(base_dir, query):
    """Search using the CLI modules to diagnose issues."""
    print(f"Starting CLI search for '{query}' in {base_dir}")
    
    try:
        # Create config manager
        config = ConfigManager()
        config.set_base_dir(str(base_dir))
        print("Config manager created successfully")
        
        # Create search engine
        search_engine = SearchEngine(base_dir, config)
        print("Search engine created successfully")
        
        # Get exclusions info
        exclusions = search_engine.exclusions_manager.get_combined_exclusions()
        print(f"Exclusions loaded: {len(exclusions.get('user_path', []))} path exclusions")
        
        # Run search
        print(f"Executing search...")
        results = search_engine.search(query, use_regex=False, case_sensitive=True)
        print(f"Search completed with {len(results)} results")
        
        # Show results
        file_count = len(set(r.file_path for r in results))
        print(f"\nFound {len(results)} matches in {file_count} files")
        
        # Show first few matches
        if results:
            print("\nFirst 10 matches:")
            for i, result in enumerate(results[:10]):
                rel_path = os.path.relpath(result.file_path, base_dir)
                content = result.line_content
                if len(content) > 80:
                    content = content[:77] + "..."
                print(f"{i+1}. {rel_path}:{result.line_number} - {content}")
            
            if len(results) > 10:
                print(f"\n... and {len(results) - 10} more matches")
                
    except Exception as e:
        import traceback
        print(f"Error during CLI search: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    # Use current directory or first argument if provided
    base_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    query = sys.argv[2] if len(sys.argv) > 2 else "match"
    
    print(f"=== DIRECT SEARCH TOOL ===")
    print(f"Base directory: {base_dir}")
    print(f"Search query: {query}")
    print(f"CLI modules available: {HAS_CLI_MODULES}")
    print("-" * 50)
    
    # Run basic search
    print("\n=== BASIC SEARCH ===")
    simple_search(base_dir, query)
    
    # If CLI modules are available, run CLI search
    if HAS_CLI_MODULES:
        print("\n\n=== CLI SEARCH ===")
        cli_search(base_dir, query)
    
    print("\nSearch complete!")
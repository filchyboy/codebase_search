#!/usr/bin/env python3
"""
Script to diagnose and fix the CLI search functionality.
This script checks the shutdown process and adds direct printing to ensure
the search report is visible even if the Rich console has issues.
"""

import os
import sys
import shutil

# Function to modify the search_cli.py file
def fix_search_cli():
    print("Starting CLI fix...")
    
    # Path to the search_cli.py file
    file_path = os.path.join(os.getcwd(), "code-search-cli/cli/search_cli.py")
    
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        return False
    
    print(f"Found file: {file_path}")
    
    # Create a backup
    backup_path = file_path + ".bak"
    shutil.copy2(file_path, backup_path)
    print(f"Created backup: {backup_path}")
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            
        # Modify the content to add direct printing
        if "print(f\"\\nDEBUG: Search report should appear below this line\")" not in content:
            print("Adding direct print debugging...")
            
            # Find the pattern for the search report
            report_pattern = "# Generate a detailed search report"
            if report_pattern in content:
                # Add direct printing before the search report
                new_content = content.replace(
                    report_pattern,
                    "# Add direct print debugging for search report\n"
                    "        print(f\"\\nDEBUG: Search report should appear below this line\")\n"
                    "        print(f\"Found {len(search_results)} matches in {len(set(r.file_path for r in search_results))} files\")\n"
                    "        # Generate a detailed search report"
                )
                
                # Write the modified content back to the file
                with open(file_path, 'w') as f:
                    f.write(new_content)
                    
                print("Successfully added debugging to search_cli.py")
                return True
            else:
                print(f"Error: Pattern '{report_pattern}' not found in file")
                return False
        else:
            print("Debugging already added to file")
            return True
    
    except Exception as e:
        print(f"Error: {str(e)}")
        # Restore backup if there was an error
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, file_path)
            print("Restored backup due to error")
        return False

# Function to fix the graceful shutdown
def fix_shutdown():
    print("\nFixing graceful shutdown...")
    
    # Path to the search_cli.py file
    file_path = os.path.join(os.getcwd(), "code-search-cli/cli/search_cli.py")
    
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        return False
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            
        # Add a simple shutdown that doesn't hang
        if "# Force kill after brief delay" not in content:
            print("Adding simplified shutdown...")
            
            # Find the pattern for the shutdown function
            shutdown_pattern = "def perform_graceful_shutdown():"
            if shutdown_pattern in content:
                # Add an import if needed
                if "import os, signal" not in content:
                    content = content.replace(
                        "import signal",
                        "import signal\nimport os"
                    )
                
                # Find where the shutdown function ends
                shutdown_end = content.find("# Set up the signal handler for graceful exit")
                if shutdown_end > 0:
                    # Insert a forced kill mechanism
                    shutdown_code = (
                        "    # Force kill after brief delay\n"
                        "    import threading\n"
                        "    def force_exit():\n"
                        "        import time\n"
                        "        time.sleep(1.0)  # Wait 1 second more\n"
                        "        os.kill(os.getpid(), signal.SIGKILL)  # Force kill\n"
                        "        \n"
                        "    threading.Thread(target=force_exit, daemon=True).start()\n"
                    )
                    
                    new_content = content[:shutdown_end] + shutdown_code + content[shutdown_end:]
                    
                    # Write the modified content back to the file
                    with open(file_path, 'w') as f:
                        f.write(new_content)
                        
                    print("Successfully fixed shutdown in search_cli.py")
                    return True
                else:
                    print("Error: Could not find end of shutdown function")
                    return False
            else:
                print(f"Error: Pattern '{shutdown_pattern}' not found in file")
                return False
        else:
            print("Shutdown fix already applied")
            return True
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("=== CLI Fix Tool ===")
    print("This tool will add direct print debugging to the search report")
    print("and fix the graceful shutdown process.")
    
    # Fix the search CLI
    fix_result = fix_search_cli()
    
    # Fix the shutdown process
    shutdown_result = fix_shutdown()
    
    if fix_result and shutdown_result:
        print("\nAll fixes applied successfully! Try running the CLI again.")
        print("Run 'code-search' and search for 'match'")
    else:
        print("\nSome fixes could not be applied. Check the errors above.")
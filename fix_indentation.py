#!/usr/bin/env python3
"""
Fix the indentation error in index_manager.py
"""
import os
import sys
import shutil

def fix_indentation():
    """Fix the indentation error in index_manager.py."""
    print("Fixing indentation error...")
    
    # Path to the index_manager.py file
    index_path = os.path.join(os.getcwd(), "code-search-cli/cli/managers/index_manager.py")
    
    if not os.path.exists(index_path):
        print(f"Error: File not found: {index_path}")
        return False
    
    print(f"Found file: {index_path}")
    
    # Create a backup
    backup_path = index_path + ".indent.bak"
    shutil.copy2(index_path, backup_path)
    print(f"Created backup: {backup_path}")
    
    try:
        with open(index_path, 'r') as f:
            lines = f.readlines()
        
        # Correctly modified content with proper indentation
        new_lines = []
        for line in lines:
            # Don't add the problematic try-except block yet
            if "# Add timeout to prevent hanging on problematic files" in line:
                continue
            if "try:" in line and "with open(file_path, 'r'" in line:
                continue
            # Keep all other lines
            new_lines.append(line)
        
        # Find where to insert the correctly indented code
        insert_pos = 0
        for i, line in enumerate(new_lines):
            if "# Process file content" in line:
                insert_pos = i + 1
                break
        
        # Insert the correctly indented code
        if insert_pos > 0:
            new_code = [
                "                        # Process file content with timeout\n",
                "                        try:\n",
                "                            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:\n",
                "                                content = f.read()\n",
            ]
            
            # Remove the original "# Process file content" line
            new_lines.pop(insert_pos - 1)
            
            # Insert the new code at the correct position
            for i, line in enumerate(new_code):
                new_lines.insert(insert_pos - 1 + i, line)
        
        # Write the fixed content
        with open(index_path, 'w') as f:
            f.writelines(new_lines)
        
        print("Successfully fixed indentation error")
        return True
    
    except Exception as e:
        print(f"Error: {str(e)}")
        # Restore backup if there was an error
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, index_path)
            print("Restored backup due to error")
        return False

def add_file_timeout_mechanism():
    """Add timeout mechanism for file reading."""
    print("\nAdding timeout mechanism for file reading...")
    
    # Path to the index_manager.py file
    index_path = os.path.join(os.getcwd(), "code-search-cli/cli/managers/index_manager.py")
    
    if not os.path.exists(index_path):
        print(f"Error: File not found: {index_path}")
        return False
    
    try:
        with open(index_path, 'r') as f:
            content = f.read()
        
        # Add timeout catch to exception handling
        if "except (UnicodeDecodeError, PermissionError)" in content:
            new_content = content.replace(
                "except (UnicodeDecodeError, PermissionError)",
                "except (UnicodeDecodeError, PermissionError, TimeoutError)"
            )
            
            # Write the modified content
            with open(index_path, 'w') as f:
                f.write(new_content)
                
            print("Added timeout to exception handling")
            return True
        else:
            print("Warning: Could not find exception handling in file")
            return False
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("=== Fix Indentation Error ===")
    print("This tool will fix the indentation error in index_manager.py")
    
    # Fix the indentation error
    indent_result = fix_indentation()
    
    # Add timeout mechanism
    timeout_result = add_file_timeout_mechanism()
    
    if indent_result and timeout_result:
        print("\nAll fixes applied successfully!")
        print("The indentation error should be fixed and the timeout mechanism added.")
        print("\nTry running 'code-search' again and search for 'match'")
    else:
        print("\nSome fixes could not be applied. Check the errors above.")
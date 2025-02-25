#!/usr/bin/env python3
"""
Script to modify the CLI to use plain text output for search reports
instead of Rich formatting, which may not display correctly in all terminals.
"""

import os
import sys
import shutil

def fix_search_report():
    """Replace Rich formatted output with plain text in search_cli.py"""
    print("Starting search report fix...")
    
    # Path to the search_cli.py file
    file_path = os.path.join(os.getcwd(), "code-search-cli/cli/search_cli.py")
    
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        return False
    
    print(f"Found file: {file_path}")
    
    # Create a backup
    backup_path = file_path + ".plain.bak"
    shutil.copy2(file_path, backup_path)
    print(f"Created backup: {backup_path}")
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Find the search report section and replace Rich formatting with plain text
        report_section = "            # Show search report with actual statistics"
        if report_section in content:
            # Find the start and end of the report section
            start_pos = content.find(report_section)
            # Find where the report ends (likely before the "# Show first 10 matches" line)
            end_marker = "            # Show first 10 matches"
            end_pos = content.find(end_marker, start_pos)
            
            if start_pos > 0 and end_pos > start_pos:
                # Original section
                original_section = content[start_pos:end_pos]
                
                # Create replacement with plain text
                replacement = """            # Show search report with plain text (no Rich formatting)
            print("\\n=====================================")
            print(f"SEARCH REPORT: '{query}'")
            print(f"• Total files in directory:    {total_files}")
            print(f"• Files searched:              {files_searched}")
            print(f"• Files skipped/excluded:      {files_skipped}")
            print(f"• Files with matches:          {file_count}")
            print(f"• Total matches found:         {len(search_results)}")
            print("=====================================\\n")
            
            # Also try with Rich console for terminals that support it
"""
                
                # Replace the original section with the new version
                new_content = content.replace(original_section, replacement)
                
                # Write the modified content back to the file
                with open(file_path, 'w') as f:
                    f.write(new_content)
                
                print("Successfully replaced Rich formatting with plain text")
                return True
            else:
                print("Error: Could not find the end of the report section")
                return False
        else:
            print(f"Error: Report section not found in file")
            return False
            
    except Exception as e:
        print(f"Error: {str(e)}")
        # Restore backup if there was an error
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, file_path)
            print("Restored backup due to error")
        return False

def fix_report_matches():
    """Replace Rich formatted output for matches with plain text"""
    print("\nFixing matches display...")
    
    # Path to the search_cli.py file
    file_path = os.path.join(os.getcwd(), "code-search-cli/cli/search_cli.py")
    
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        return False
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Find the matches section
        matches_section = "            # Show first 10 matches"
        if matches_section in content:
            # Find the start and end of the matches section
            start_pos = content.find(matches_section)
            # Find the end of the matches section
            end_marker = "                if len(search_results) > 10:"
            end_pos = content.find(end_marker, start_pos)
            
            if start_pos > 0 and end_pos > start_pos:
                # Original section
                original_section = content[start_pos:end_pos]
                
                # Create replacement with plain text
                replacement = """            # Show first 10 matches with plain text
            if search_results:
                print("\\nFirst 10 matches:")
                for i, result in enumerate(search_results[:10]):
                    rel_path = os.path.relpath(result.file_path, base_dir)
                    # Truncate long content
                    content = result.line_content
                    if len(content) > 80:
                        content = content[:77] + "..."
                    print(f"{i+1}. {rel_path}:{result.line_number} - {content}")
"""
                
                # Replace the original section with the new version
                new_content = content.replace(original_section, replacement)
                
                # Write the modified content back to the file
                with open(file_path, 'w') as f:
                    f.write(new_content)
                
                print("Successfully replaced matches formatting with plain text")
                return True
            else:
                print("Error: Could not find the end of the matches section")
                return False
        else:
            print(f"Error: Matches section not found in file")
            return False
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("=== Plain Output Fix ===")
    print("This tool will replace Rich formatted output with plain text")
    print("to ensure visibility in terminals that don't support ANSI escape codes.")
    
    # Fix the search report
    report_result = fix_search_report()
    
    # Fix the matches display
    matches_result = fix_report_matches()
    
    if report_result and matches_result:
        print("\nAll fixes applied successfully! Try running the CLI again.")
        print("Run 'code-search' and search for 'match'")
    else:
        print("\nSome fixes could not be applied. Check the errors above.")
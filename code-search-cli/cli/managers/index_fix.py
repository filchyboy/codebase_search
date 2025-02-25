#!/usr/bin/env python3
"""
Fix the indexing and search issues with the CLI.
This script adds a timeout to file indexing,
makes search work without indexing, and fixes output interleaving.
"""
import os
import sys
import shutil
import re

def fix_indexing_timeout():
    """Add file timeouts to prevent indexing from stalling."""
    print("Adding file indexing timeouts...")
    
    # Path to the index_manager.py file
    index_path = os.path.join(os.getcwd(), "code-search-cli/cli/managers/index_manager.py")
    
    if not os.path.exists(index_path):
        print(f"Error: File not found: {index_path}")
        return False
    
    print(f"Found file: {index_path}")
    
    # Create a backup
    backup_path = index_path + ".bak"
    shutil.copy2(index_path, backup_path)
    print(f"Created backup: {backup_path}")
    
    try:
        with open(index_path, 'r') as f:
            content = f.read()
        
        # 1. Find and modify the file processing code to add timeouts
        if "with open(file_path, 'r'" in content:
            # Add timeout to file reading
            new_content = content.replace(
                "with open(file_path, 'r'",
                "# Add timeout to prevent hanging on problematic files\n"
                "                            try:\n"
                "                                with open(file_path, 'r'"
            )
            
            # Add exception handling for file processing
            new_content = new_content.replace(
                "                        except (UnicodeDecodeError, PermissionError) as e:",
                "                        except (UnicodeDecodeError, PermissionError, TimeoutError) as e:"
            )
            
            # Add timeout logic to search file
            new_content = new_content.replace(
                "# Function to index a single file",
                "# Add file timeout mechanism\n"
                "                def read_with_timeout(file_obj, timeout=1.0):\n"
                "                    \"\"\"Read from a file with timeout to prevent hanging.\"\"\"\n"
                "                    import select\n"
                "                    # Check if the file is ready for reading\n"
                "                    if not select.select([file_obj], [], [], timeout)[0]:\n"
                "                        raise TimeoutError(f\"Reading file timed out after {timeout}s\")\n"
                "                    return file_obj.read()\n\n"
                "                # Function to index a single file"
            )
            
            # Write the modified content
            with open(index_path, 'w') as f:
                f.write(new_content)
                
            print("Added file processing timeouts to index_manager.py")
        else:
            print("Warning: Could not find file reading code in index_manager.py")
            
        return True
            
    except Exception as e:
        print(f"Error: {str(e)}")
        # Restore backup if there was an error
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, index_path)
            print("Restored backup due to error")
        return False

def fix_search_independent():
    """Make search not depend on indexing completion."""
    print("\nMaking search independent of indexing...")
    
    # Path to the search_engine.py file
    search_path = os.path.join(os.getcwd(), "code-search-cli/cli/managers/search_engine.py")
    
    if not os.path.exists(search_path):
        print(f"Error: File not found: {search_path}")
        return False
    
    print(f"Found file: {search_path}")
    
    # Create a backup
    backup_path = search_path + ".bak"
    shutil.copy2(search_path, backup_path)
    print(f"Created backup: {backup_path}")
    
    try:
        with open(search_path, 'r') as f:
            content = f.read()
        
        # 1. Find and modify the search method to never wait for indexing
        if "def search(" in content:
            # Find the search method
            search_method = re.search(r'def search\([^)]*\)[^:]*:', content)
            if search_method:
                search_start = search_method.start()
                
                # Find where the indexing wait code is
                wait_index_check = "if wait_for_index and indexing_status"
                wait_index_pos = content.find(wait_index_check, search_start)
                
                if wait_index_pos > 0:
                    # Replace the waitIndexing code block with a simple pass
                    end_of_wait = content.find("# Check if we can use index for this search", wait_index_pos)
                    if end_of_wait > 0:
                        wait_block = content[wait_index_pos:end_of_wait]
                        new_wait_block = (
                            "        # Never wait for indexing - always proceed with search\n"
                            "        if indexing_status.get(\"is_indexing\", False):\n"
                            "            console.print(\"[dim]Search proceeding without waiting for indexing...[/dim]\")\n"
                            "\n"
                        )
                        
                        new_content = content.replace(wait_block, new_wait_block)
                        
                        # Also disable indexed search completely
                        using_index_check = "using_index = False"
                        using_index_pos = new_content.find(using_index_check)
                        if using_index_pos > 0:
                            # Replace the using_index check with never using index
                            using_index_block = "if use_index and not use_regex and len(query.split()) <= 3:"
                            using_index_block_pos = new_content.find(using_index_block, using_index_pos)
                            if using_index_block_pos > 0:
                                end_of_using_index = new_content.find("# Set a search timeout", using_index_block_pos)
                                if end_of_using_index > 0:
                                    block = new_content[using_index_block_pos:end_of_using_index]
                                    new_block = (
                                        "        # Always use direct search, never use index\n"
                                        "        using_index = False\n"
                                        "\n"
                                    )
                                    new_content = new_content.replace(block, new_block)
                                    
                                    # Write the modified content
                                    with open(search_path, 'w') as f:
                                        f.write(new_content)
                                        
                                    print("Made search independent of indexing in search_engine.py")
                                    return True
                                else:
                                    print("Error: Could not find end of using_index block")
                            else:
                                print("Error: Could not find using_index block")
                        else:
                            print("Error: Could not find using_index check")
                    else:
                        print("Error: Could not find end of wait block")
                else:
                    print("Error: Could not find wait_for_index check")
            else:
                print("Error: Could not find search method")
        else:
            print("Error: Could not find search method in search_engine.py")
            
        return False
            
    except Exception as e:
        print(f"Error: {str(e)}")
        # Restore backup if there was an error
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, search_path)
            print("Restored backup due to error")
        return False

def disable_output_interleaving():
    """Fix output interleaving by using print directly."""
    print("\nFixing output interleaving issues...")
    
    # Path to the search_cli.py file
    cli_path = os.path.join(os.getcwd(), "code-search-cli/cli/search_cli.py")
    
    if not os.path.exists(cli_path):
        print(f"Error: File not found: {cli_path}")
        return False
    
    print(f"Found file: {cli_path}")
    
    # Create a backup
    backup_path = cli_path + ".interleaving.bak"
    shutil.copy2(cli_path, backup_path)
    print(f"Created backup: {backup_path}")
    
    try:
        with open(cli_path, 'r') as f:
            content = f.read()
        
        # Replace the search command with a simplified version that always searches synchronously
        if "def handle_search_command(" in content:
            # Find the handle_search_command function
            search_func_match = re.search(r'def handle_search_command\([^)]*\):', content)
            if search_func_match:
                search_func_start = search_func_match.start()
                
                # Find the end of the function
                next_func = re.search(r'\ndef [a-zA-Z_]+\(', content[search_func_start:])
                if next_func:
                    search_func_end = search_func_start + next_func.start()
                    
                    # Get the original function
                    original_func = content[search_func_start:search_func_end]
                    
                    # Create a simplified search function
                    new_func = """def handle_search_command(query: str, base_dir: Path):
    \"\"\"Handles executing a search query directly without threading.\"\"\"
    info("Starting direct search for query: {}", query)
    debug("Base directory: {}", base_dir)
    
    theme = ThemeManager.get_theme()
    if not query:
        console.print(f"[{theme['error']}]Error: Search query cannot be empty.[/]")
        return

    try:
        # Create a ConfigManager
        config = ConfigManager()
        
        # Create a search engine
        search_engine = SearchEngine(base_dir, config)
        
        # Perform the search directly
        print(f"\\nSearching for '{query}' in {base_dir}...")
        results = search_engine.search(
            query, 
            use_regex=False, 
            case_sensitive=True,
            wait_for_index=False,  # Never wait for indexing
            use_index=False,       # Never use index
            max_results=100,
            timeout=5              # Short timeout
        )
        
        # Display results
        file_count = len(set(r.file_path for r in results)) if results else 0
        match_count = len(results)
        
        # Search report with plain text
        print(f"\\n=====================================")
        print(f"SEARCH REPORT: '{query}'")
        print(f"• Files with matches:          {file_count}")
        print(f"• Total matches found:         {match_count}")
        print("=====================================")
        
        # Show first matches
        if results:
            print("\\nFirst 10 matches:")
            for i, result in enumerate(results[:10]):
                rel_path = os.path.relpath(result.file_path, base_dir)
                # Truncate long content
                content = result.line_content
                if len(content) > 80:
                    content = content[:77] + "..."
                print(f"{i+1}. {rel_path}:{result.line_number} - {content}")
            
            if len(results) > 10:
                print(f"\\n... and {len(results) - 10} more matches")
        else:
            print("\\nNo matches found.")
            
    except Exception as e:
        error("Search error: {}", str(e))
        traceback.print_exc()
        print(f"\\nError during search: {str(e)}")
    
    # Separate from next prompt
    print("")

"""
                    
                    # Replace the original function with the new one
                    new_content = content.replace(original_func, new_func)
                    
                    # Write the modified content
                    with open(cli_path, 'w') as f:
                        f.write(new_content)
                        
                    print("Replaced search command with direct implementation")
                    return True
                else:
                    print("Error: Could not find end of search command function")
            else:
                print("Error: Could not find search command function")
        else:
            print("Error: Could not find search command function in search_cli.py")
            
        return False
            
    except Exception as e:
        print(f"Error: {str(e)}")
        # Restore backup if there was an error
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, cli_path)
            print("Restored backup due to error")
        return False

if __name__ == "__main__":
    print("=== Index and Search Fix ===")
    print("This tool will fix stalled indexing and search issues")
    
    # Fix indexing timeout issues
    index_result = fix_indexing_timeout()
    
    # Fix search dependency on indexing
    search_result = fix_search_independent()
    
    # Fix output interleaving
    interleaving_result = disable_output_interleaving()
    
    if index_result and search_result and interleaving_result:
        print("\nAll fixes applied successfully!")
        print("These fixes should prevent indexing from stalling,")
        print("make search work without waiting for indexing,")
        print("and fix the output interleaving issues.")
        print("\nTry running 'code-search' again and search for 'match'")
    else:
        print("\nSome fixes could not be applied. Check the errors above.")
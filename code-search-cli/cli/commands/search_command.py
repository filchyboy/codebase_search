"""Interactive search command implementation."""

import click
from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich.panel import Panel
from rich.syntax import Syntax
import os
import sys
import traceback
from pathlib import Path
import re

from cli.managers.config_manager import ConfigManager
from cli.managers.search_engine import SearchEngine
from cli.managers.theme_manager import ThemeManager
from cli.logger import setup_logger

logger = setup_logger()
console = Console()

def format_search_results(results, query, theme=None):
    """Format search results for display.
    
    Args:
        results: List of SearchResult objects
        query: The search query
        theme: Theme dictionary for styling
        
    Returns:
        Formatted rich Text object
    """
    try:
        if not theme:
            theme = ThemeManager.get_theme()
        
        # Add debugging
        print(f"format_search_results called with {len(results)} results for: {query}")
        
        # Early return for empty results to avoid confusion
        if not results:
            print("Warning: Empty results list")
            return Text(f"No results found for: {query}", style=theme['warning'])
        
        # Skip additional filtering - our main search already applies filters
        filtered_results = results
        
        # Group results by file
        files = {}
        for result in filtered_results:
            # Debug individual results
            print(f"Processing result: {result.file_path}:{result.line_number}")
            
            if result.file_path not in files:
                files[result.file_path] = []
            files[result.file_path].append(result)
        
        # Build output with rich Text objects
        output = Text()
        output.append(f"Found {len(filtered_results)} matches in {len(files)} files\n\n", style=theme['highlight'])
        
        # Emergency fallback for debugging - simple text output in case rich formatting fails
        print(f"RESULTS: Found {len(filtered_results)} matches in {len(files)} files")
        
        for file_path, file_results in files.items():
            # Add file header
            rel_path = os.path.relpath(file_path)
            output.append(f"{rel_path}\n", style=theme['success'])
            print(f"FILE: {rel_path}")
            
            # Add each matching line
            for result in file_results:
                try:
                    line_text = Text()
                    
                    # Add line number
                    line_text.append(f"{result.line_number}:", style=theme['highlight'])
                    print(f"  LINE {result.line_number}: {result.line_content[:80].strip()}")
                    
                    # Add line content with highlighted matches
                    content = result.line_content
                    
                    # Handle case when there are no match positions
                    if not result.match_positions:
                        # Safely handle missing match positions
                        line_text.append(f" {content}", style=theme['text'])
                    else:
                        last_end = 0
                        
                        for start, end in result.match_positions:
                            # Add text before match
                            if start > last_end:
                                line_text.append(content[last_end:start])
                            
                            # Add highlighted match
                            line_text.append(content[start:end], style=f"bold {theme['error']}")
                            last_end = end
                        
                        # Add any remaining text after the last match
                        if last_end < len(content):
                            line_text.append(content[last_end:])
                    
                    # Add the formatted line to output
                    output.append("  ")
                    output.append(line_text)
                    output.append("\n")
                except Exception as e:
                    # Fallback for individual result formatting errors
                    print(f"Error formatting result: {str(e)}")
                    output.append(f"  {result.line_number}: {result.line_content}\n")
            
            # Add separator between files
            output.append("\n")
        
        return output
        
    except Exception as e:
        # Critical error - fall back to simple text
        print(f"CRITICAL ERROR in format_search_results: {str(e)}")
        print(traceback.format_exc())
        error_text = Text()
        error_text.append(f"Found {len(results)} results for '{query}'\n", style="bold")
        error_text.append("Error formatting results. See below for raw output:\n\n")
        
        # Add simple text results
        for i, result in enumerate(results[:20]):
            error_text.append(f"{result.file_path}:{result.line_number} - {result.line_content[:80]}\n")
            
        return error_text

def interactive_search(base_dir: Path):
    """Run an interactive search loop."""
    theme = ThemeManager.get_theme()
    console.print(f"\n[{theme['highlight']}]Code Search CLI[/{theme['highlight']}] - Interactive Mode")
    console.print(f"Type your search term and press Enter. Press [{theme['error']}]Ctrl+C[/{theme['error']}] to exit.\n")
    
    config = ConfigManager()
    search_engine = SearchEngine(base_dir, config)

    while True:
        try:
            # Get user input for the search term
            search_term = console.input(f"[{theme['highlight']}]Search:[/{theme['highlight']}] ").strip()
            if not search_term:
                continue  # Skip empty inputs
                
            # Check if the search term is an excluded directory
            # Get all exclusion patterns from configuration
            config = ConfigManager()
            exclusions_manager = ExclusionsManager(str(base_dir), config)
            exclusions = exclusions_manager.get_combined_exclusions()
            
            # Collect all excluded terms
            excluded_terms = set()
            for category in exclusions.values():
                for pattern in category:
                    # Convert glob patterns to simple terms
                    term = pattern.rstrip('/*').rstrip('/').lstrip('*').lstrip('.')
                    if term and len(term) > 2:  # Only add meaningful terms
                        excluded_terms.add(term.lower())
            
            # Only block core excluded terms - don't over-block
            core_excluded = {"vendor", "node_modules", ".git"}
            if search_term.lower() in core_excluded:
                console.print(f"[{theme['warning']}]'{search_term}' is excluded from searches as it typically refers to directories that are excluded by your settings.[/{theme['warning']}]")
                continue

            # Show a status while searching
            with console.status(f"[{theme['highlight']}]Searching for: {search_term}[/{theme['highlight']}]") as status:
                # Determine if this is a regex search (starts with / and ends with /)
                use_regex = False
                if search_term.startswith('/') and search_term.endswith('/') and len(search_term) > 2:
                    use_regex = True
                    search_term = search_term[1:-1]  # Remove the slashes
                
                # Determine if this is case-insensitive (ends with i)
                case_sensitive = True
                if use_regex and search_term.endswith('i') and len(search_term) > 1:
                    case_sensitive = False
                    search_term = search_term[:-1]  # Remove the i flag
                    
                # Perform the search - explicitly don't wait for index and limit to 100 results
                try:
                    # Add timeout to prevent hanging
                    results = search_engine.search(
                        search_term, 
                        use_regex, 
                        case_sensitive, 
                        wait_for_index=False,
                        max_results=100,
                        timeout=30
                    )
                except TimeoutError:
                    # Prevent search from hanging
                    status.update("[red]Search timed out. Try a more specific query.[/red]")
                    results = []
                
                # Use the exclusions from the config
                # Get exclusion patterns from the configuration - use new exclusion structure
                exclusions = search_engine.exclusions_manager.get_combined_exclusions()
                
                # Get only path exclusions for filtering file paths
                path_patterns = set()
                if "language" in exclusions:
                    path_patterns.update(exclusions["language"])
                if "framework" in exclusions:
                    path_patterns.update(exclusions["framework"])
                if "user_path" in exclusions:
                    path_patterns.update(exclusions["user_path"])
                
                # Get string exclusions for filtering content
                string_patterns = set()
                if "user_string" in exclusions:
                    string_patterns.update(exclusions["user_string"])
                
                # Filter results using configured exclusions, but ensure we're not excluding everything
                filtered_results = results.copy()
                
                # First apply path exclusions
                if path_patterns and results:
                    # Debug the filtering process - save original count
                    original_count = len(filtered_results)
                    
                    # Only exclude paths that contain the exclusion pattern as a directory component
                    # For example, 'vendor' should match '/vendor/' or '/vendor' but not 'vendorName'
                    for result in results[:]:
                        path_str = str(result.file_path)
                        path_parts = path_str.split('/')
                        
                        # Check each pattern against complete path
                        for pattern in path_patterns:
                            # Skip very short patterns that might cause over-exclusion
                            if len(pattern) <= 2:
                                continue
                                
                            # Only exclude if pattern matches a complete path segment
                            if pattern in path_parts or f"/{pattern}" in path_str or f"{pattern}/" in path_str:
                                if result in filtered_results:
                                    filtered_results.remove(result)
                                break
                    
                    # If we've excluded everything, go back to the original results
                    # This is a safety check to prevent over-filtering
                    if not filtered_results and original_count > 0:
                        filtered_results = results.copy()
                
                # Now apply string exclusions to content if any exist
                if string_patterns and filtered_results:
                    # Save original count
                    original_count = len(filtered_results)
                    
                    # Filter out results with matching content exclusions
                    for result in filtered_results[:]:
                        line_content = result.line_content
                        
                        # Check each string pattern against the line content
                        for pattern in string_patterns:
                            if pattern in line_content:
                                if result in filtered_results:
                                    filtered_results.remove(result)
                                break
                    
                    # If we've excluded everything, revert to previous results
                    if not filtered_results and original_count > 0:
                        filtered_results = results.copy()
                        
                # Make sure we never return an empty list if there were results
                if not filtered_results and results:
                    filtered_results = results.copy()
                
                # Update status when search completes
                status.update(f"[{theme['success']}]Found {len(filtered_results)} results for: {search_term}[/{theme['success']}]")
                
                # Format the results for display
                formatted_results = format_search_results(filtered_results, search_term, theme)
                
            # Display results after search is complete (outside status context)
            console.print(formatted_results)
            
            # Print a summary if we got results
            if filtered_results:
                file_count = len(set(r.file_path for r in filtered_results))
                console.print(f"[{theme['success']}]Found {len(filtered_results)} matches in {file_count} files[/{theme['success']}]")
            else:
                # Make sure we always show feedback
                console.print(f"[{theme['warning']}]No matches found for: {search_term}[/{theme['warning']}]")
                
            # IMPORTANT - add a blank line to separate from next prompt
            console.print("")

        except KeyboardInterrupt:
            console.print(f"\n[{theme['success']}]Exiting Code Search CLI.[/{theme['success']}]")
            break
        except Exception as e:
            console.print(f"[{theme['error']}]Error: {str(e)}[/{theme['error']}]")

@click.command()
@click.option(
    "--base-dir",
    "-d",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help="Base directory for code search.",
)
@click.option(
    "--regex",
    "-r",
    is_flag=True,
    help="Interpret the query as a regular expression.",
)
@click.option(
    "--ignore-case",
    "-i",
    is_flag=True,
    help="Perform case-insensitive search.",
)
@click.argument("query", required=False)
def search(base_dir: Path = None, query: str = None, regex: bool = False, ignore_case: bool = False):
    """Search through the codebase. If no query is provided, enters interactive mode."""
    try:
        config = ConfigManager()
        theme = ThemeManager.get_theme()
        search_dir = base_dir or Path(config.get_base_dir())
        
        if not search_dir.exists():
            console.print(f"[{theme['error']}]Error: Search directory does not exist. Run init command first.[/{theme['error']}]")
            return

        if not query:
            # Interactive mode
            interactive_search(search_dir)
            return

        # Single search mode using the search engine
        search_engine = SearchEngine(search_dir, config)
        results = search_engine.search(query, regex, not ignore_case)
        
        # Apply exclusions from config, not hardcoded values
        exclusions_manager = ExclusionsManager(str(search_dir), config)
        exclusion_patterns = exclusions_manager.generate_search_exclusion_regex()
        path_pattern = exclusion_patterns.get("path", "(?!)")
        
        # Filter results based on path exclusions from config
        if path_pattern and path_pattern != "(?!)":
            try:
                path_regex = re.compile(path_pattern)
                filtered_results = [r for r in results if not path_regex.search(str(r.file_path))]
            except:
                # If regex fails, use original results
                filtered_results = results
        else:
            filtered_results = results
        
        # Display the results
        formatted_results = format_search_results(filtered_results, query, theme)
        console.print(formatted_results)

    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        console.print(f"[{theme['error']}]Error: {str(e)}[/{theme['error']}]")
        raise click.Abort()

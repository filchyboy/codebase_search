"""Search engine for code search CLI using native Python implementation."""

import os
import re
from pathlib import Path
from typing import List, Dict, Pattern, Optional, Union, Set, Iterator
import fnmatch
from rich.console import Console

from cli.managers.exclusions_manager import ExclusionsManager
from cli.managers.config_manager import ConfigManager

console = Console()

class SearchResult:
    """Represents a single search result."""
    
    def __init__(self, file_path: Path, line_number: int, line_content: str, match_positions: List[tuple]):
        """Initialize a search result.
        
        Args:
            file_path: Path to the file containing the match
            line_number: Line number of the match (1-based)
            line_content: Content of the line containing the match
            match_positions: List of (start, end) positions of matches in the line
        """
        self.file_path = file_path
        self.line_number = line_number
        self.line_content = line_content
        self.match_positions = match_positions
    
    def __str__(self) -> str:
        """Return a string representation of the search result."""
        return f"{self.file_path}:{self.line_number}: {self.line_content}"


class SearchEngine:
    """Native Python implementation of code search functionality."""
    
    def __init__(self, base_dir: Union[str, Path], config_manager: Optional[ConfigManager] = None):
        """Initialize the search engine.
        
        Args:
            base_dir: Base directory to search in
            config_manager: Configuration manager instance (will create one if not provided)
        """
        self.base_dir = Path(base_dir)
        self.config = config_manager or ConfigManager()
        self.exclusions_manager = ExclusionsManager(str(self.base_dir), self.config)
        
        # Initialize the index manager
        from cli.managers.index_manager import IndexManager
        self.index_manager = IndexManager(str(self.base_dir), self.config)
        
        # Initialize search statistics
        self.search_stats = {
            "files_searched": 0,
            "files_excluded": 0,
            "files_with_matches": 0,
            "match_count": 0,
            "exclusion_patterns_used": 0,
            "excluded_by_pattern": {},
            "search_time": 0
        }
    
    def _should_exclude(self, path: Path) -> bool:
        """Check if a path should be excluded based on path exclusion patterns.
        
        Args:
            path: Path to check
            
        Returns:
            True if the path should be excluded, False otherwise
        """
        # Get path exclusion patterns (only system_generated and user_path)
        exclusions = self.exclusions_manager.get_combined_exclusions()
        path_patterns = set()
        
        # Only include path-based exclusions (system_generated and user_path)
        if "language" in exclusions:
            path_patterns.update(exclusions["language"])
        if "framework" in exclusions:
            path_patterns.update(exclusions["framework"])
        if "user_path" in exclusions:
            path_patterns.update(exclusions["user_path"])
        
        # String exclusions should not affect path filtering
        # (user_string exclusions are only applied to file content)
        
        # Convert path to relative path for matching
        rel_path = path.relative_to(self.base_dir)
        path_str = str(rel_path)
        
        # First check for exact directory name in path parts (e.g., "vendor")
        path_parts = path_str.split('/')
        for pattern in path_patterns:
            # Remove trailing /* if present for directory pattern checking
            clean_pattern = pattern.rstrip('/*')
            if clean_pattern in path_parts:
                # Update statistics
                self.search_stats["files_excluded"] += 1
                if pattern not in self.search_stats["excluded_by_pattern"]:
                    self.search_stats["excluded_by_pattern"][pattern] = 0
                self.search_stats["excluded_by_pattern"][pattern] += 1
                return True
        
        # Check if path matches any exclusion pattern
        for pattern in path_patterns:
            # Handle directory exclusions (patterns ending with /)
            if pattern.endswith('/'):
                if self._path_matches_dir_pattern(path_str, pattern):
                    # Update statistics
                    self.search_stats["files_excluded"] += 1
                    if pattern not in self.search_stats["excluded_by_pattern"]:
                        self.search_stats["excluded_by_pattern"][pattern] = 0
                    self.search_stats["excluded_by_pattern"][pattern] += 1
                    return True
            # Handle regular file pattern
            elif fnmatch.fnmatch(path_str, pattern):
                # Update statistics
                self.search_stats["files_excluded"] += 1
                if pattern not in self.search_stats["excluded_by_pattern"]:
                    self.search_stats["excluded_by_pattern"][pattern] = 0
                self.search_stats["excluded_by_pattern"][pattern] += 1
                return True
            # Check if any parent directory matches the pattern
            elif any(fnmatch.fnmatch(str(parent), pattern) 
                    for parent in rel_path.parents):
                # Update statistics
                self.search_stats["files_excluded"] += 1
                if pattern not in self.search_stats["excluded_by_pattern"]:
                    self.search_stats["excluded_by_pattern"][pattern] = 0
                self.search_stats["excluded_by_pattern"][pattern] += 1
                return True
                
        return False
    
    def _path_matches_dir_pattern(self, path: str, pattern: str) -> bool:
        """Check if a path matches a directory pattern.
        
        Args:
            path: Path string to check
            pattern: Directory pattern (ending with /)
            
        Returns:
            True if path matches the pattern
        """
        # Remove trailing slash for matching
        dir_pattern = pattern.rstrip('/')
        
        # Simple case: exact directory match
        if path == dir_pattern:
            return True
            
        # Path is a subdirectory of the pattern
        if path.startswith(f"{dir_pattern}/"):
            return True
            
        # Check if directory appears anywhere in the path
        if f"/{dir_pattern}/" in f"/{path}/":
            return True
            
        return False
    
    def _walk_files(self) -> Iterator[Path]:
        """Walk through files in the base directory, respecting path exclusions.
        
        Yields:
            Path objects for each file that should be searched
        """
        # Pre-load exclusion patterns for better performance
        exclusions = self.exclusions_manager.get_combined_exclusions()
        
        # Only use path exclusions for directory filtering
        path_patterns = set()
        if "language" in exclusions:
            path_patterns.update(exclusions["language"])
        if "framework" in exclusions:
            path_patterns.update(exclusions["framework"])
        if "user_path" in exclusions:
            path_patterns.update(exclusions["user_path"])
            
        # Use the configured path exclusions instead of hardcoded values
        common_dir_exclusions = {p.rstrip('/*').rstrip('/') for p in path_patterns}
        
        for root, dirs, files in os.walk(self.base_dir):
            root_path = Path(root)
            
            # Check if current directory should be excluded based on path exclusions
            rel_root = str(root_path.relative_to(self.base_dir))
            skip_dir = False
            
            # Skip processing if we're in an excluded directory
            for excluded_dir in common_dir_exclusions:
                if excluded_dir in rel_root.split('/'):
                    skip_dir = True
                    break
                    
            if skip_dir:
                # Clear dirs to prevent walking into subdirectories
                dirs[:] = []
                continue
                
            # Filter out excluded directories
            # This modifies dirs in-place to avoid walking into excluded directories
            dirs[:] = [d for d in dirs if not self._should_exclude(root_path / d)]
            
            # Yield files that aren't excluded by path patterns
            for file in files:
                file_path = root_path / file
                if not self._should_exclude(file_path):
                    yield file_path
    
    def search(self, query: str, use_regex: bool = False, case_sensitive: bool = True, 
             show_progress: bool = True, use_index: bool = True, wait_for_index: bool = False,
             max_results: int = 1000, timeout: int = 60) -> List[SearchResult]:
        """Search for a pattern in files under the base directory.
        
        Args:
            query: Search query
            use_regex: Whether to interpret the query as a regex pattern
            case_sensitive: Whether to perform case-sensitive search
            show_progress: Whether to show a progress indicator
            use_index: Whether to use the index for faster searches when possible
            wait_for_index: Whether to wait for indexing to complete before searching
            max_results: Maximum number of results to return
            timeout: Maximum time (in seconds) to spend searching
            
        Returns:
            List of SearchResult objects
        
        Raises:
            TimeoutError: If the search takes longer than the specified timeout
        """
        # Reset search statistics
        self.search_stats = {
            "files_searched": 0,
            "files_excluded": 0,
            "files_with_matches": 0,
            "match_count": 0,
            "exclusion_patterns_used": 0,
            "excluded_by_pattern": {},
            "search_time": 0,
            "query": query,
            "use_regex": use_regex,
            "case_sensitive": case_sensitive
        }
        
        # Record search start time
        search_start_time = time.time()
        from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
        from rich.console import Console
        from concurrent.futures import ThreadPoolExecutor
        import threading
        
        results = []
        files_searched = 0
        files_matched = 0
        total_files = 0
        
        # Check if we should wait for ongoing indexing
        indexing_status = self.index_manager.get_indexing_status()
                # Never wait for indexing - always proceed with search
        if indexing_status.get("is_indexing", False):
            console.print("[dim]Search proceeding without waiting for indexing...[/dim]")

# Check if we can use index for this search
        using_index = False
                # Always use direct search, never use index
        using_index = False

# Set a search timeout
        search_start_time = time.time()
        
        # Get configured path exclusions instead of using hardcoded values
        exclusions = self.exclusions_manager.get_combined_exclusions()
        path_patterns = set()
        if "language" in exclusions:
            path_patterns.update(exclusions["language"])
        if "framework" in exclusions:
            path_patterns.update(exclusions["framework"]) 
        if "user_path" in exclusions:
            path_patterns.update(exclusions["user_path"])
            
        # Only block if the query is EXACTLY one of the configured path exclusions
        if query in path_patterns:
            console = Console()
            console.print(f"[yellow]'{query}' is excluded from searches as it matches a path exclusion pattern.[/yellow]")
            return []
            
        # If we can use the index for this search
        if using_index:
            indexed_search_start = time.time()
            
            # Use the index to get candidate files
            candidate_files = self.index_manager.search(query, use_regex, case_sensitive)
            
            if candidate_files:
                # Found candidates in the index, now search them for exact matches
                total_files = len(candidate_files)
                
                # For thread safety
                results_lock = threading.Lock()
                counter_lock = threading.Lock()
                
                # Apply exclusions from config, not hardcoded values
                
                try:
                    # Compile the search pattern
                    if use_regex:
                        flags = 0 if case_sensitive else re.IGNORECASE
                        pattern = re.compile(query, flags)
                    else:
                        # For plain text search, escape special regex characters
                        escaped_query = re.escape(query)
                        flags = 0 if case_sensitive else re.IGNORECASE
                        pattern = re.compile(escaped_query, flags)
                    
                    # Convert relative paths from index to full paths
                    search_files = [self.base_dir / file_path for file_path in candidate_files]
                    
                    # Function to search a single file
                    def search_file(file_path):
                        nonlocal files_searched, files_matched
                        
                        # Check if we've exceeded timeout
                        if time.time() - search_start_time > timeout:
                            raise TimeoutError("Search timed out")
                            
                        # Check if we've reached the result limit
                        with counter_lock:
                            if len(results) >= max_results:
                                return []
                        
                        try:
                            # Apply path exclusions from config, not hardcoded values
                            if self._should_exclude(file_path):
                                with counter_lock:
                                    files_searched += 1
                                return []
                            
                            # Don't check anything else - we want to minimize exclusions
                            # to ensure we get search results
                            
                            if self._is_binary_file(file_path):
                                with counter_lock:
                                    files_searched += 1
                                return []
                            
                            file_results = []
                            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                                for i, line in enumerate(f, start=1):
                                    # Check timeout periodically
                                    if i % 1000 == 0 and time.time() - search_start_time > timeout:
                                        raise TimeoutError("Search timed out")
                                        
                                    matches = list(pattern.finditer(line))
                                    if matches:
                                        match_positions = [(m.start(), m.end()) for m in matches]
                                        result = SearchResult(
                                            file_path=file_path,
                                            line_number=i,
                                            line_content=line.rstrip('\n'),
                                            match_positions=match_positions
                                        )
                                        # We've already filtered at the file level, so just add results
                                        file_results.append(result)
                                        
                                        # Check if adding these results would exceed max_results
                                        with counter_lock:
                                            if len(results) + len(file_results) >= max_results:
                                                break
                            
                            with counter_lock:
                                files_searched += 1
                                if file_results:
                                    files_matched += 1
                            
                            return file_results
                        
                        except (UnicodeDecodeError, PermissionError, OSError):
                            with counter_lock:
                                files_searched += 1
                            return []
                        except TimeoutError:
                            raise  # Re-raise timeout errors
                    
                    # Use progress indicator if requested
                    if show_progress and search_files:
                        with Progress(
                            SpinnerColumn(),
                            TextColumn("[progress.description]{task.description}"),
                            TextColumn("[{task.completed}/{task.total}]"),
                            TimeElapsedColumn(),
                            console=Console(),
                            transient=True
                        ) as progress:
                            # Create progress tasks with indication that we're using the index
                            search_task = progress.add_task(f"Searching indexed files for: {query}", total=len(search_files))
                            
                            # Use thread pool for faster search
                            with ThreadPoolExecutor(max_workers=min(32, os.cpu_count() * 4)) as executor:
                                # Submit all search tasks
                                future_to_file = {executor.submit(search_file, file): file for file in search_files}
                                
                                # Process results as they complete
                                for future in future_to_file:
                                    file_results = future.result()
                                    with results_lock:
                                        results.extend(file_results)
                                    progress.update(search_task, advance=1, 
                                                description=f"Searching indexed files: {query} - Found {len(results)} matches in {files_matched} files")
                    else:
                        # No progress indicator, simpler execution
                        for file_path in search_files:
                            results.extend(search_file(file_path))
                    
                    indexed_search_time = time.time() - indexed_search_start
                    
                    # If using index was successful, return results
                    return results
                    
                except re.error as e:
                    # Handle invalid regex
                    console = Console()
                    console.print(f"Invalid regular expression: {str(e)}")
                    return []
        
        # Fall back to full search if index search was not used or returned no results
        
        # For thread safety in progress reporting
        results_lock = threading.Lock()
        counter_lock = threading.Lock()
        
        # Get path exclusions from the exclusions manager
        exclusions = self.exclusions_manager.get_combined_exclusions()
        path_patterns = set()
        if "language" in exclusions:
            path_patterns.update(exclusions["language"])
        if "framework" in exclusions:
            path_patterns.update(exclusions["framework"])
        if "user_path" in exclusions:
            path_patterns.update(exclusions["user_path"])
        
        try:
            # Compile the search pattern
            if use_regex:
                flags = 0 if case_sensitive else re.IGNORECASE
                pattern = re.compile(query, flags)
            else:
                # For plain text search, escape special regex characters
                escaped_query = re.escape(query)
                flags = 0 if case_sensitive else re.IGNORECASE
                pattern = re.compile(escaped_query, flags)
            
            # Collect all files to search first
            search_files = list(self._walk_files())
            
            # Function to search a single file
            def search_file(file_path):
                nonlocal files_searched, files_matched
                
                try:
                    # Apply path exclusions from config, not hardcoded values
                    if self._should_exclude(file_path):
                        with counter_lock:
                            files_searched += 1
                        return []
                    
                    # Don't check anything else - we want to minimize exclusions
                    # to ensure we get search results
                    
                    if self._is_binary_file(file_path):
                        with counter_lock:
                            files_searched += 1
                        return []
                    
                    file_results = []
                    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                        for i, line in enumerate(f, start=1):
                            matches = list(pattern.finditer(line))
                            if matches:
                                match_positions = [(m.start(), m.end()) for m in matches]
                                result = SearchResult(
                                    file_path=file_path,
                                    line_number=i,
                                    line_content=line.rstrip('\n'),
                                    match_positions=match_positions
                                )
                                # We've already filtered at the file level, so just add results
                                file_results.append(result)
                    
                    with counter_lock:
                        files_searched += 1
                        if file_results:
                            files_matched += 1
                    
                    return file_results
                
                except (UnicodeDecodeError, PermissionError, OSError):
                    with counter_lock:
                        files_searched += 1
                    return []
            
            # Use progress indicator if requested
            if show_progress and search_files:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    TextColumn("[{task.completed}/{task.total}]"),
                    TimeElapsedColumn(),
                    console=Console(),
                    transient=True
                ) as progress:
                    # Create progress tasks
                    search_task = progress.add_task(f"Searching all files for: {query}", total=len(search_files))
                    
                    # Use thread pool for faster search
                    with ThreadPoolExecutor(max_workers=min(32, os.cpu_count() * 4)) as executor:
                        # Submit all search tasks
                        future_to_file = {executor.submit(search_file, file): file for file in search_files}
                        
                        # Process results as they complete
                        for future in future_to_file:
                            file_results = future.result()
                            with results_lock:
                                results.extend(file_results)
                            progress.update(search_task, advance=1, 
                                           description=f"Searching files for: {query} - Found {len(results)} matches in {files_matched} files")
            else:
                # No progress indicator, simpler execution
                for file_path in search_files:
                    results.extend(search_file(file_path))
                    
        except re.error as e:
            # Handle invalid regex
            console = Console()
            console.print(f"Invalid regular expression: {str(e)}")
            return []
            
        return results
    
    def _is_binary_file(self, file_path: Path) -> bool:
        """Check if a file is binary.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if the file is binary, False otherwise
        """
        # Check file extension first
        binary_extensions = {
            '.pdf', '.png', '.jpg', '.jpeg', '.gif', '.bmp',
            '.zip', '.tar', '.gz', '.bz2', '.xz', '.rar',
            '.exe', '.dll', '.so', '.dylib', '.class',
            '.pyc', '.pyd', '.pyo', '.o', '.obj',
        }
        
        if file_path.suffix.lower() in binary_extensions:
            return True
            
        # If extension check doesn't catch it, read a small chunk
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(4096)
                # If it contains null bytes or too many non-printable chars, it's binary
                return b'\x00' in chunk or sum(c < 9 or (c > 13 and c < 32) for c in chunk) > len(chunk) * 0.3
        except (PermissionError, OSError):
            # If we can't read it, assume it's binary to skip it
            return True
"""Index manager for code search CLI.

This module provides functionality to index files in a directory for faster searches.
It supports background indexing that doesn't block normal application operation.
"""

import os
import re
import json
import time
import hashlib
import queue
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any, Union
from datetime import datetime
import threading
from concurrent.futures import ThreadPoolExecutor

from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.console import Console
from rich.status import Status

from cli.managers.config_manager import ConfigManager
from cli.managers.exclusions_manager import ExclusionsManager

console = Console()

# Global variables for tracking background indexing
background_indexer = None
indexing_status = {
    "is_indexing": False,
    "files_processed": 0,
    "total_files": 0,
    "start_time": 0,
    "current_file": "",
    "errors": []
}

class BackgroundIndexer(threading.Thread):
    """Background thread for indexing files without blocking the main application."""
    
    def __init__(self, index_manager, force=False):
        """Initialize the background indexer.
        
        Args:
            index_manager: IndexManager instance
            force: Force reindexing even if the index is valid
        """
        super().__init__(daemon=True)  # Run as daemon thread
        self.index_manager = index_manager
        self.force = force
        self.stop_event = threading.Event()
        
    def run(self):
        """Run the indexing task in the background."""
        global indexing_status
        
        try:
            # Set global status
            indexing_status["is_indexing"] = True
            indexing_status["start_time"] = time.time()
            indexing_status["files_processed"] = 0
            indexing_status["errors"] = []
            
            # Get files to index
            files_to_index = self.index_manager._get_files_to_index()
            indexing_status["total_files"] = len(files_to_index)
            
            if not files_to_index:
                indexing_status["is_indexing"] = False
                return
                
            # Initialize new index
            new_index = {"files": {}, "words": {}}
            files_processed = 0
            total_size = 0
            
            # Common words to ignore (stopwords)
            stopwords = {
                "the", "and", "is", "in", "to", "a", "of", "for", "with", "on", "at", "by", "an",
                "be", "this", "that", "it", "as", "from", "or", "are", "not", "was", "were", "if",
                "i", "you", "he", "she", "they", "we", "them", "him", "her", "his", "our", "their",
                "who", "what", "when", "where", "why", "how", "which", "there", "here", "out", "up",
                "can", "will", "all", "some", "any", "each", "have", "has", "had", "does", "did",
                "its", "your", "my", "our", "their"
            }
            
            # Process files in parallel with ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=min(8, os.cpu_count() or 4)) as executor:
                # Function to index a single file
                def index_file(file_path):
                    if self.stop_event.is_set():
                        return None, None, None
                        
                    rel_path = str(file_path.relative_to(self.index_manager.base_dir))
                    indexing_status["current_file"] = rel_path
                    
                    try:
                        # Get file stats
                        file_stat = os.stat(file_path)
                        file_size = file_stat.st_size
                        file_mtime = file_stat.st_mtime
                        
                        # Skip large files (> 1MB)
                        if file_size > 1024 * 1024:
                            return rel_path, {"too_large": True, "mtime": file_mtime, "size": file_size}, {}
                        
                        # Process file content with timeout
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                                content = f.read()
                        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                            content = f.read()
                        
                        # Create file signature
                        file_hash = hashlib.md5(content.encode('utf-8', errors='replace')).hexdigest()
                        
                        # Extract words from content
                        words = set(re.findall(r'\w+', content.lower()))
                        words = {w for w in words if len(w) > 2 and w not in stopwords}
                        
                        # Create word positions index
                        word_positions = {}
                        for word in words:
                            positions = []
                            for m in re.finditer(r'\b' + re.escape(word) + r'\b', content.lower()):
                                positions.append(m.start())
                            if positions:
                                word_positions[word] = positions[:100]  # Limit to first 100 positions
                        
                        file_info = {
                            "mtime": file_mtime,
                            "size": file_size,
                            "hash": file_hash,
                            "word_count": len(words)
                        }
                        
                        return rel_path, file_info, word_positions
                    
                    except (UnicodeDecodeError, PermissionError, OSError) as e:
                        indexing_status["errors"].append(f"Error indexing {rel_path}: {str(e)}")
                        return None, None, None
                
                # Submit indexing tasks in batches to avoid memory issues
                batch_size = 50
                for i in range(0, len(files_to_index), batch_size):
                    if self.stop_event.is_set():
                        break
                        
                    batch = files_to_index[i:i+batch_size]
                    futures = {executor.submit(index_file, file): file for file in batch}
                    
                    for future in futures:
                        if self.stop_event.is_set():
                            break
                            
                        file_path, file_info, word_positions = future.result()
                        
                        if file_path and file_info:
                            with self.index_manager._lock:
                                # Update file index
                                new_index["files"][file_path] = file_info
                                files_processed += 1
                                total_size += file_info.get("size", 0)
                                
                                # Update word index
                                for word, positions in word_positions.items():
                                    if word not in new_index["words"]:
                                        new_index["words"][word] = {}
                                    new_index["words"][word][file_path] = positions
                        
                        indexing_status["files_processed"] = files_processed
            
            # Only update the index if not stopped
            if not self.stop_event.is_set():
                # Update metadata
                self.index_manager.metadata = {
                    "last_indexed": datetime.now().isoformat(),
                    "file_count": files_processed,
                    "total_size": total_size,
                    "base_dir": str(self.index_manager.base_dir),
                    "version": "1.0.0"
                }
                
                # Save the new index
                self.index_manager.index = new_index
                self.index_manager._save_index()
                self.index_manager._save_metadata()
        
        except Exception as e:
            indexing_status["errors"].append(f"Indexing error: {str(e)}")
        
        finally:
            # Always reset indexing status when done
            indexing_status["is_indexing"] = False
            
    def stop(self):
        """Stop the indexing process."""
        self.stop_event.set()


class IndexManager:
    """Manages file indexing for fast searching."""
    
    def __init__(self, base_dir: str, config_manager: Optional[ConfigManager] = None):
        """Initialize the index manager.
        
        Args:
            base_dir: Base directory to index
            config_manager: Configuration manager instance
        """
        self.base_dir = Path(base_dir)
        self.config = config_manager or ConfigManager()
        self.exclusions_manager = ExclusionsManager(str(self.base_dir), self.config)
        
        # Index directory is in the .code-search-cli directory in the base directory
        self.index_dir = self.base_dir / ".code-search-cli"
        self.index_dir.mkdir(exist_ok=True)
        
        # Main index file
        self.index_file = self.index_dir / "search_index.json"
        
        # Index metadata
        self.index_meta_file = self.index_dir / "index_meta.json"
        
        # Lock for thread-safety
        self._lock = threading.Lock()
        
        # Load index if it exists
        self.index = self._load_index()
        self.metadata = self._load_metadata()
        
        # Check if index needs to be created and start background indexing if needed
        if not self.is_index_valid() or self.needs_reindex():
            self.start_background_indexing()
        
    def _load_index(self) -> Dict[str, Any]:
        """Load the search index from disk."""
        if not self.index_file.exists():
            return {"files": {}, "words": {}}
        
        try:
            with open(self.index_file, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {"files": {}, "words": {}}
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Load the index metadata from disk."""
        if not self.index_meta_file.exists():
            return {
                "last_indexed": None,
                "file_count": 0,
                "total_size": 0,
                "base_dir": str(self.base_dir),
                "version": "1.0.0"
            }
        
        try:
            with open(self.index_meta_file, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {
                "last_indexed": None,
                "file_count": 0,
                "total_size": 0,
                "base_dir": str(self.base_dir),
                "version": "1.0.0"
            }
    
    def _save_index(self) -> None:
        """Save the search index to disk."""
        with self._lock:
            with open(self.index_file, "w") as f:
                json.dump(self.index, f)
    
    def _save_metadata(self) -> None:
        """Save the index metadata to disk."""
        with self._lock:
            with open(self.index_meta_file, "w") as f:
                json.dump(self.metadata, f)
    
    def is_index_valid(self) -> bool:
        """Check if the index is valid and up-to-date.
        
        Returns:
            True if the index is valid, False otherwise
        """
        # Check if metadata matches current base directory
        if self.metadata.get("base_dir") != str(self.base_dir):
            return False
        
        # Check if index exists
        if not self.index_file.exists() or not self.index_meta_file.exists():
            return False
        
        # Check if index is empty
        if not self.index.get("files") or not self.index.get("words"):
            return False
        
        # Check if index is too old (older than 24 hours)
        last_indexed = self.metadata.get("last_indexed")
        if not last_indexed:
            return False
        
        try:
            last_indexed_time = datetime.fromisoformat(last_indexed)
            now = datetime.now()
            if (now - last_indexed_time).total_seconds() > 86400:  # 24 hours
                return False
        except (ValueError, TypeError):
            return False
        
        return True
    
    def needs_reindex(self) -> bool:
        """Check if a reindex is needed based on file changes.
        
        Returns:
            True if reindex is needed, False otherwise
        """
        if not self.is_index_valid():
            return True
        
        # Check a sample of files to see if they've changed
        indexed_files = list(self.index.get("files", {}).keys())
        sample_size = min(20, len(indexed_files))
        
        if sample_size == 0:
            return True
        
        # Check if sample files still exist and haven't changed
        for file_path in indexed_files[:sample_size]:
            full_path = self.base_dir / file_path
            if not full_path.exists():
                return True
            
            file_info = self.index["files"][file_path]
            current_mtime = os.path.getmtime(full_path)
            
            # If modification time has changed, reindex
            if abs(current_mtime - file_info.get("mtime", 0)) > 0.1:  # Allow small time differences
                return True
        
        return False
    
    def start_background_indexing(self, force: bool = False) -> None:
        """Start indexing in a background thread.
        
        Args:
            force: Force reindexing even if the index is valid
        """
        global background_indexer
        
        # Ensure we're not already indexing
        if background_indexer and background_indexer.is_alive():
            return
            
        # Don't index if it's not needed and not forced
        if not force and self.is_index_valid() and not self.needs_reindex():
            return
            
        # Create and start the background indexer
        background_indexer = BackgroundIndexer(self, force)
        background_indexer.start()
        
        # Log to console with small notice message
        console.print("[dim]Index update started in background[/dim]")
        
    def stop_background_indexing(self) -> None:
        """Stop any background indexing process."""
        global background_indexer
        
        if background_indexer and background_indexer.is_alive():
            background_indexer.stop()
            console.print("[yellow]Stopping background indexing...[/yellow]")
            
    def get_indexing_status(self) -> Dict[str, Any]:
        """Get the current status of background indexing.
        
        Returns:
            Dictionary with indexing status information
        """
        global indexing_status, background_indexer
        
        # Calculate progress percentage if possible
        progress = 0
        if indexing_status["total_files"] > 0:
            progress = (indexing_status["files_processed"] / indexing_status["total_files"]) * 100
            
        # Calculate elapsed time
        elapsed_time = 0
        if indexing_status["start_time"] > 0:
            elapsed_time = time.time() - indexing_status["start_time"]
            
        # Check if indexer is still alive
        is_alive = background_indexer and background_indexer.is_alive()
        
        return {
            "is_indexing": indexing_status["is_indexing"] and is_alive,
            "files_processed": indexing_status["files_processed"],
            "total_files": indexing_status["total_files"],
            "progress": progress,
            "elapsed_time": elapsed_time,
            "current_file": indexing_status["current_file"],
            "errors": indexing_status["errors"]
        }
    
    def wait_for_indexing(self, timeout: Optional[float] = None) -> bool:
        """Wait for background indexing to complete.
        
        Args:
            timeout: Maximum time to wait in seconds, or None to wait forever
            
        Returns:
            True if indexing completed, False if timed out
        """
        global background_indexer
        
        if not background_indexer or not background_indexer.is_alive():
            return True
            
        start_time = time.time()
        while background_indexer.is_alive():
            if timeout and (time.time() - start_time) > timeout:
                return False
            time.sleep(0.1)
            
        return True
        
    def create_index(self, force: bool = False, background: bool = True) -> None:
        """Create or update the search index.
        
        Args:
            force: Force reindexing even if the index is valid
            background: Run indexing in the background
        """
        # If background indexing is requested, start it and return
        if background:
            self.start_background_indexing(force)
            return
        
        # Otherwise, do synchronous indexing
        if not force and self.is_index_valid() and not self.needs_reindex():
            console.print("[green]Index is up to date.[/green]")
            return
        
        console.print("[yellow]Creating search index...[/yellow]")
        
        # Use the BackgroundIndexer but run it in the foreground
        indexer = BackgroundIndexer(self, force)
        indexer.run()  # This will run synchronously
        
        # Final status message
        console.print(f"[green]Indexed {indexing_status['files_processed']} files[/green]")
    
    def _get_files_to_index(self) -> List[Path]:
        """Get all files to index, respecting path exclusions.
        
        Returns:
            List of Path objects for each file to index
        """
        from cli.managers.search_engine import SearchEngine
        
        # Create a temporary search engine to use its file traversal logic
        search_engine = SearchEngine(self.base_dir, self.config)
        
        # Force refresh exclusions before walking files
        search_engine.exclusions_manager = self.exclusions_manager
        
        # Get exclusions explicitly to ensure they're loaded
        exclusions = self.exclusions_manager.get_combined_exclusions()
        console.print(f"[dim]Using {len(exclusions.get('user_path', []))} user path exclusions for indexing[/dim]")
        
        # Get all files to index, respecting exclusions from updated system
        return list(search_engine._walk_files())
    
    def search(self, query: str, use_regex: bool = False, case_sensitive: bool = True) -> List[Dict[str, Any]]:
        """Search the index for matching files.
        
        Args:
            query: Search query
            use_regex: Whether to interpret the query as a regex pattern
            case_sensitive: Whether to perform case-sensitive search
            
        Returns:
            List of match information dictionaries
        """
        if not self.is_index_valid():
            console.print("[yellow]Index is not valid. Creating index...[/yellow]")
            self.create_index()
        
        # For regex searches or complex queries, fall back to full search
        if use_regex or len(query.split()) > 3 or any(c in query for c in "\"'()[]{}*+?.\\|"):
            return []
        
        results = []
        
        # Process the query
        terms = query.lower().split()
        terms = [term for term in terms if len(term) > 2]
        
        if not terms:
            return []
        
        # Find files containing all terms
        candidate_files = set()
        
        # First term
        first_term = terms[0]
        if first_term in self.index.get("words", {}):
            candidate_files = set(self.index["words"][first_term].keys())
        
        # Additional terms narrow down the results
        for term in terms[1:]:
            if term not in self.index.get("words", {}):
                candidate_files = set()
                break
            
            term_files = set(self.index["words"][term].keys())
            candidate_files &= term_files
        
        # No matching files
        if not candidate_files:
            return []
        
        # Sort candidate files by relevance (number of term occurrences)
        candidates_with_score = []
        for file_path in candidate_files:
            score = 0
            for term in terms:
                if term in self.index.get("words", {}) and file_path in self.index["words"][term]:
                    score += len(self.index["words"][term][file_path])
            
            candidates_with_score.append((file_path, score))
        
        # Sort by score (descending)
        candidates_with_score.sort(key=lambda x: x[1], reverse=True)
        
        # Return top matches
        top_candidates = [file_path for file_path, _ in candidates_with_score[:100]]
        
        return top_candidates
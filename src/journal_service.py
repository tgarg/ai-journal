from typing import List, Optional, Dict, Any
from pathlib import Path

from .models import JournalEntry
from .storage import StorageBackend
from .markdown_importer import MarkdownImporter
from .reflection import ReflectionService
from .ollama_client import OllamaClient


class EntryNotFoundError(Exception):
    """Raised when requested entry doesn't exist"""
    pass


class InvalidEntryError(Exception):
    """Raised when entry data is invalid"""
    pass


class JournalService:
    """
    Business logic layer for journal operations.
    
    Provides CRUD operations and business rules for journal entries,
    sitting between UI interfaces (CLI, web) and storage layer.
    """
    
    def __init__(self, storage: StorageBackend, ollama_client: Optional[OllamaClient] = None):
        """Initialize service with storage backend and optional AI client."""
        self.storage = storage
        self._reflection_service = None
        if ollama_client:
            self._reflection_service = ReflectionService(ollama_client)
    
    def create_entry(self, content: str, title: str = None, tags: List[str] = None) -> JournalEntry:
        """
        Create a new journal entry.
        
        Args:
            content: Entry content (can be empty)
            title: Optional title for the entry
            tags: Optional list of tags
            
        Returns:
            Created JournalEntry
        """
        if tags is None:
            tags = []
            
        entry = JournalEntry(
            title=title,
            content=content,
            tags=tags.copy()  # Avoid mutable default issues
        )
        
        self.storage.save_entry(entry)
        return entry
    
    def get_entry(self, entry_id: str) -> JournalEntry:
        """
        Get a specific journal entry by ID.
        
        Args:
            entry_id: Unique identifier for the entry
            
        Returns:
            JournalEntry object
            
        Raises:
            EntryNotFoundError: If entry with given ID doesn't exist
        """
        entry = self.storage.load_entry(entry_id)
        if not entry:
            raise EntryNotFoundError(f"Entry with ID '{entry_id}' not found")
        return entry
    
    def list_entries(self, limit: int = 50) -> List[JournalEntry]:
        """
        List journal entries, newest first.
        
        Args:
            limit: Maximum number of entries to return (default: 50)
            
        Returns:
            List of JournalEntry objects, sorted by creation date (newest first)
        """
        all_entries = self.storage.load_all_entries()
        
        if limit is not None and limit > 0:
            return all_entries[:limit]
        
        return all_entries
    
    def update_entry(self, entry_id: str, content: str = None, title: str = None, tags: List[str] = None) -> JournalEntry:
        """
        Update an existing journal entry.
        
        Args:
            entry_id: Unique identifier for the entry
            content: New content (None = don't update)
            title: New title (None = don't update)
            tags: New tags list (None = don't update, [] = clear all tags)
            
        Returns:
            Updated JournalEntry object
            
        Raises:
            EntryNotFoundError: If entry with given ID doesn't exist
            InvalidEntryError: If no fields provided for update
        """
        # Validate that at least one field is being updated
        if all(x is None for x in [content, title, tags]):
            raise InvalidEntryError("At least one field must be updated")
        
        # Get existing entry (will raise EntryNotFoundError if not found)
        entry = self.get_entry(entry_id)
        
        # Apply updates
        if content is not None:
            entry.update_content(content, title)
        elif title is not None:
            entry.update_content(entry.content, title)
        
        if tags is not None:
            entry.tags = tags.copy()  # Avoid reference issues
            # Update timestamp since we modified the entry
            from datetime import datetime
            entry.updated_at = datetime.now()
        
        # Save updated entry
        self.storage.save_entry(entry)
        return entry
    
    def import_from_directory(self, directory_path: Path) -> tuple[List[JournalEntry], int]:
        """
        Import journal entries from markdown files in a directory, skipping duplicates.
        
        Duplicates are detected by matching both date and content.
        
        Args:
            directory_path: Path to directory containing markdown files
            
        Returns:
            tuple: (imported_entries, skipped_count)
            
        Raises:
            FileNotFoundError: If directory doesn't exist
        """
        if not directory_path.exists():
            raise FileNotFoundError(f"Directory '{directory_path}' not found")
        
        if not directory_path.is_dir():
            raise ValueError(f"'{directory_path}' is not a directory")
        
        # Get existing entries to check for duplicates
        existing_entries = self.storage.load_all_entries()
        
        # Create temporary importer to process files
        temp_importer = MarkdownImporter(self.storage)
        
        imported_entries = []
        skipped_count = 0
        
        # Process each markdown file individually
        for md_file in directory_path.glob("*.md"):
            try:
                # Import single file to get potential entry
                potential_entry = temp_importer.import_file(md_file)
                
                # Check for duplicates
                if not self._is_duplicate(potential_entry, existing_entries + imported_entries):
                    # Save non-duplicate entry
                    self.storage.save_entry(potential_entry)
                    imported_entries.append(potential_entry)
                else:
                    skipped_count += 1
                    
            except Exception as e:
                # Log error but continue with other files
                print(f"Warning: Failed to import {md_file.name}: {e}")
                continue
        
        return imported_entries, skipped_count
    
    def _is_duplicate(self, new_entry: JournalEntry, existing_entries: List[JournalEntry]) -> bool:
        """
        Check if entry is duplicate based on date and content.
        
        Args:
            new_entry: Entry to check
            existing_entries: List of existing entries to compare against
            
        Returns:
            True if duplicate found, False otherwise
        """
        new_date = new_entry.created_at.date()
        new_content = new_entry.content.strip()
        
        for existing in existing_entries:
            if (existing.created_at.date() == new_date and 
                existing.content.strip() == new_content):
                return True
        
        return False
    
    def generate_reflection_prompt(self, entry_id: str, strategy: str = "empathetic_v1") -> Dict[str, Any]:
        """
        Generate an AI reflection prompt for a journal entry.
        
        Args:
            entry_id: Unique identifier for the entry
            strategy: Prompt generation strategy to use
            
        Returns:
            Dict containing reflection prompt and metadata
            
        Raises:
            EntryNotFoundError: If entry with given ID doesn't exist
            ValueError: If no AI client configured or invalid strategy
            requests.exceptions.RequestException: If AI service unavailable
        """
        if not self._reflection_service:
            raise ValueError("No AI client configured. Initialize JournalService with an OllamaClient to use reflection prompts.")
        
        entry = self.get_entry(entry_id)
        return self._reflection_service.generate_reflection_prompt(entry.content, strategy)
    
    def list_reflection_strategies(self) -> List[str]:
        """
        List available reflection prompt strategies.
        
        Returns:
            List of strategy names
            
        Raises:
            ValueError: If no AI client configured
        """
        if not self._reflection_service:
            raise ValueError("No AI client configured. Initialize JournalService with an OllamaClient to use reflection prompts.")
        
        return self._reflection_service.list_strategies()
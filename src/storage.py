from abc import ABC, abstractmethod
from typing import List, Optional
from .models import JournalEntry


class StorageBackend(ABC):
    """Abstract interface for journal entry storage backends."""
    
    @abstractmethod
    def save_entry(self, entry: JournalEntry) -> None:
        """Save or update a journal entry."""
        pass
    
    @abstractmethod
    def load_entry(self, entry_id: str) -> Optional[JournalEntry]:
        """Load a specific journal entry by ID."""
        pass
    
    @abstractmethod
    def load_all_entries(self) -> List[JournalEntry]:
        """Load all journal entries, sorted by creation date (newest first)."""
        pass
    
    @abstractmethod
    def delete_entry(self, entry_id: str) -> bool:
        """Delete a journal entry. Returns True if deleted, False if not found."""
        pass
    
    @abstractmethod
    def search_entries(self, query: str) -> List[JournalEntry]:
        """Search entries by content or title. Returns matching entries."""
        pass
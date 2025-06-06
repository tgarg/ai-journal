import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from .models import JournalEntry
from .storage import StorageBackend


class JSONStorage(StorageBackend):
    """Simple JSON file-based storage for journal entries."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.entries_file = self.data_dir / "entries.json"
    
    def _serialize_entry(self, entry: JournalEntry) -> Dict[str, Any]:
        """Convert JournalEntry to JSON-serializable dict."""
        return {
            "id": entry.id,
            "title": entry.title,
            "content": entry.content,
            "created_at": entry.created_at.isoformat(),
            "updated_at": entry.updated_at.isoformat(),
            "tags": entry.tags
        }
    
    def _deserialize_entry(self, data: Dict[str, Any]) -> JournalEntry:
        """Convert dict to JournalEntry object."""
        return JournalEntry(
            id=data["id"],
            title=data["title"],
            content=data["content"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            tags=data["tags"]
        )
    
    def save_entry(self, entry: JournalEntry) -> None:
        """Save or update a journal entry."""
        entries = self._load_all_entries_dict()
        
        # Update existing entry or add new one
        entries[entry.id] = self._serialize_entry(entry)
        
        with open(self.entries_file, 'w') as f:
            json.dump(entries, f, indent=2)
    
    def load_entry(self, entry_id: str) -> Optional[JournalEntry]:
        """Load a specific journal entry by ID."""
        entries = self._load_all_entries_dict()
        entry_data = entries.get(entry_id)
        if entry_data:
            return self._deserialize_entry(entry_data)
        return None
    
    def load_all_entries(self) -> List[JournalEntry]:
        """Load all journal entries, sorted by creation date (newest first)."""
        entries_data = self._load_all_entries_dict()
        entries = [self._deserialize_entry(data) for data in entries_data.values()]
        return sorted(entries, key=lambda e: e.created_at, reverse=True)
    
    def delete_entry(self, entry_id: str) -> bool:
        """Delete a journal entry. Returns True if deleted, False if not found."""
        entries = self._load_all_entries_dict()
        if entry_id in entries:
            del entries[entry_id]
            with open(self.entries_file, 'w') as f:
                json.dump(entries, f, indent=2)
            return True
        return False
    
    def search_entries(self, query: str) -> List[JournalEntry]:
        """Search entries by content or title. Returns matching entries."""
        query_lower = query.lower()
        matching_entries = []
        
        for entry in self.load_all_entries():
            # Search in title and content
            if (entry.title and query_lower in entry.title.lower()) or \
               query_lower in entry.content.lower():
                matching_entries.append(entry)
        
        return matching_entries
    
    def _load_all_entries_dict(self) -> Dict[str, Dict[str, Any]]:
        """Load all entries from JSON file as dict."""
        if not self.entries_file.exists():
            return {}
        
        try:
            with open(self.entries_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
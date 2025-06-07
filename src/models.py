from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
import uuid


@dataclass
class JournalEntry:
    """Represents a single journal entry with metadata and content."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: Optional[str] = None
    content: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)
    
    def update_content(self, content: str, title: Optional[str] = None) -> None:
        """Update the entry content and metadata."""
        self.content = content
        if title is not None:
            self.title = title
        self.updated_at = datetime.now()
    
    def add_tag(self, tag: str) -> None:
        """Add a tag to the entry if not already present."""
        if tag not in self.tags:
            self.tags.append(tag)
    
    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the entry."""
        if tag in self.tags:
            self.tags.remove(tag)
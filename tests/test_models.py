import pytest
from datetime import datetime, timedelta
from src.models import JournalEntry


class TestJournalEntry:
    
    def test_creation_with_defaults(self):
        entry = JournalEntry()
        
        assert entry.id is not None
        assert len(entry.id) == 36  # UUID length
        assert entry.title is None
        assert entry.content == ""
        assert isinstance(entry.created_at, datetime)
        assert isinstance(entry.updated_at, datetime)
        assert entry.tags == []
    
    def test_creation_with_values(self):
        now = datetime.now()
        entry = JournalEntry(
            id="test-id",
            title="Test Title",
            content="Test content",
            created_at=now,
            updated_at=now,
            tags=["tag1", "tag2"]
        )
        
        assert entry.id == "test-id"
        assert entry.title == "Test Title"
        assert entry.content == "Test content"
        assert entry.created_at == now
        assert entry.updated_at == now
        assert entry.tags == ["tag1", "tag2"]
    
    def test_update_content(self):
        entry = JournalEntry(content="Original content")
        original_updated_at = entry.updated_at
        
        # Wait a small amount to ensure timestamp difference
        import time
        time.sleep(0.01)
        
        entry.update_content("New content", "New title")
        
        assert entry.content == "New content"
        assert entry.title == "New title"
        assert entry.updated_at > original_updated_at
    
    def test_update_content_without_title(self):
        entry = JournalEntry(title="Original title", content="Original content")
        
        entry.update_content("New content")
        
        assert entry.content == "New content"
        assert entry.title == "Original title"  # Should remain unchanged
    
    def test_add_tag(self):
        entry = JournalEntry()
        
        entry.add_tag("new-tag")
        assert "new-tag" in entry.tags
        assert len(entry.tags) == 1
        
        # Adding same tag again should not duplicate
        entry.add_tag("new-tag")
        assert len(entry.tags) == 1
    
    def test_add_tag_to_existing_tags(self):
        entry = JournalEntry(tags=["existing-tag"])
        
        entry.add_tag("new-tag")
        assert "existing-tag" in entry.tags
        assert "new-tag" in entry.tags
        assert len(entry.tags) == 2
    
    def test_remove_tag(self):
        entry = JournalEntry(tags=["tag1", "tag2", "tag3"])
        
        entry.remove_tag("tag2")
        assert "tag2" not in entry.tags
        assert "tag1" in entry.tags
        assert "tag3" in entry.tags
        assert len(entry.tags) == 2
    
    def test_remove_nonexistent_tag(self):
        entry = JournalEntry(tags=["tag1", "tag2"])
        
        # Should not raise error
        entry.remove_tag("nonexistent")
        assert len(entry.tags) == 2
        assert entry.tags == ["tag1", "tag2"]
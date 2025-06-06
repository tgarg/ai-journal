import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime

from src.models import JournalEntry
from src.json_storage import JSONStorage


class TestJSONStorage:
    
    @pytest.fixture
    def temp_storage(self):
        """Create a temporary storage for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield JSONStorage(temp_dir)
    
    @pytest.fixture
    def sample_entry(self):
        """Create a sample journal entry for testing."""
        return JournalEntry(
            id="test-id",
            title="Test Entry",
            content="This is test content",
            tags=["test", "sample"]
        )
    
    def test_save_and_load_entry(self, temp_storage, sample_entry):
        temp_storage.save_entry(sample_entry)
        
        loaded_entry = temp_storage.load_entry("test-id")
        assert loaded_entry is not None
        assert loaded_entry.id == sample_entry.id
        assert loaded_entry.title == sample_entry.title
        assert loaded_entry.content == sample_entry.content
        assert loaded_entry.tags == sample_entry.tags
    
    def test_load_nonexistent_entry(self, temp_storage):
        loaded_entry = temp_storage.load_entry("nonexistent-id")
        assert loaded_entry is None
    
    def test_save_overwrites_existing_entry(self, temp_storage, sample_entry):
        # Save initial entry
        temp_storage.save_entry(sample_entry)
        
        # Modify and save again
        sample_entry.content = "Updated content"
        temp_storage.save_entry(sample_entry)
        
        # Load and verify
        loaded_entry = temp_storage.load_entry("test-id")
        assert loaded_entry.content == "Updated content"
    
    def test_load_all_entries_empty(self, temp_storage):
        entries = temp_storage.load_all_entries()
        assert entries == []
    
    def test_load_all_entries_sorted_by_date(self, temp_storage):
        # Create entries with different dates
        entry1 = JournalEntry(id="1", content="First", created_at=datetime(2024, 1, 1))
        entry2 = JournalEntry(id="2", content="Second", created_at=datetime(2024, 1, 3))
        entry3 = JournalEntry(id="3", content="Third", created_at=datetime(2024, 1, 2))
        
        # Save in random order
        temp_storage.save_entry(entry2)
        temp_storage.save_entry(entry1)
        temp_storage.save_entry(entry3)
        
        # Load and verify order (newest first)
        entries = temp_storage.load_all_entries()
        assert len(entries) == 3
        assert entries[0].id == "2"  # 2024-01-03
        assert entries[1].id == "3"  # 2024-01-02
        assert entries[2].id == "1"  # 2024-01-01
    
    def test_delete_entry(self, temp_storage, sample_entry):
        temp_storage.save_entry(sample_entry)
        
        # Verify entry exists
        assert temp_storage.load_entry("test-id") is not None
        
        # Delete entry
        result = temp_storage.delete_entry("test-id")
        assert result is True
        
        # Verify entry is gone
        assert temp_storage.load_entry("test-id") is None
    
    def test_delete_nonexistent_entry(self, temp_storage):
        result = temp_storage.delete_entry("nonexistent-id")
        assert result is False
    
    def test_search_entries_by_content(self, temp_storage):
        entry1 = JournalEntry(id="1", content="I love programming in Python")
        entry2 = JournalEntry(id="2", content="JavaScript is also great")
        entry3 = JournalEntry(id="3", content="Python makes data science easy")
        
        for entry in [entry1, entry2, entry3]:
            temp_storage.save_entry(entry)
        
        # Search for "Python"
        results = temp_storage.search_entries("Python")
        assert len(results) == 2
        assert all("Python" in entry.content for entry in results)
    
    def test_search_entries_by_title(self, temp_storage):
        entry1 = JournalEntry(id="1", title="My Python Journey", content="Content 1")
        entry2 = JournalEntry(id="2", title="Learning JavaScript", content="Content 2")
        entry3 = JournalEntry(id="3", title="Advanced Python", content="Content 3")
        
        for entry in [entry1, entry2, entry3]:
            temp_storage.save_entry(entry)
        
        # Search for "Python" in titles
        results = temp_storage.search_entries("Python")
        assert len(results) == 2
        assert all("Python" in entry.title for entry in results)
    
    def test_search_entries_case_insensitive(self, temp_storage):
        entry = JournalEntry(id="1", content="I LOVE programming")
        temp_storage.save_entry(entry)
        
        results = temp_storage.search_entries("love")
        assert len(results) == 1
        assert results[0].id == "1"
    
    def test_search_entries_no_matches(self, temp_storage, sample_entry):
        temp_storage.save_entry(sample_entry)
        
        results = temp_storage.search_entries("nonexistent")
        assert results == []
    
    def test_persistence_across_instances(self, temp_storage, sample_entry):
        # Save with first instance
        temp_storage.save_entry(sample_entry)
        
        # Create new instance with same directory
        new_storage = JSONStorage(temp_storage.data_dir)
        
        # Verify data persists
        loaded_entry = new_storage.load_entry("test-id")
        assert loaded_entry is not None
        assert loaded_entry.content == sample_entry.content
    
    def test_corrupted_json_file_handling(self, temp_storage):
        # Write invalid JSON to file
        with open(temp_storage.entries_file, 'w') as f:
            f.write("invalid json content")
        
        # Should handle gracefully and return empty results
        entries = temp_storage.load_all_entries()
        assert entries == []
        
        # Should still be able to save new entries
        entry = JournalEntry(content="New entry")
        temp_storage.save_entry(entry)
        
        entries = temp_storage.load_all_entries()
        assert len(entries) == 1
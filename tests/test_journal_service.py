import pytest
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock
import requests

from src.models import JournalEntry
from src.journal_service import JournalService, EntryNotFoundError, InvalidEntryError
from src.ollama_client import OllamaClient


class TestJournalService:
    
    @pytest.fixture
    def mock_storage(self):
        """Create a mock storage backend."""
        return Mock()
    
    @pytest.fixture
    def service(self, mock_storage):
        """Create a JournalService with mock storage."""
        return JournalService(mock_storage)
    
    @pytest.fixture
    def mock_ollama_client(self):
        """Create a mock Ollama client."""
        return Mock(spec=OllamaClient)
    
    @pytest.fixture
    def service_with_ai(self, mock_storage, mock_ollama_client):
        """Create a JournalService with AI capabilities."""
        return JournalService(mock_storage, mock_ollama_client)
    
    @pytest.fixture
    def sample_entry(self):
        """Create a sample journal entry."""
        return JournalEntry(
            id="test-id",
            title="Test Entry",
            content="Sample content",
            created_at=datetime(2024, 1, 1),
            tags=["test"]
        )

    def test_create_entry_basic(self, service, mock_storage):
        """Test creating a basic entry."""
        entry = service.create_entry("Test content")
        
        assert entry.content == "Test content"
        assert entry.title is None
        assert entry.tags == []
        mock_storage.save_entry.assert_called_once_with(entry)
    
    def test_create_entry_with_all_fields(self, service, mock_storage):
        """Test creating entry with title and tags."""
        entry = service.create_entry(
            content="Test content",
            title="Test Title", 
            tags=["tag1", "tag2"]
        )
        
        assert entry.content == "Test content"
        assert entry.title == "Test Title"
        assert entry.tags == ["tag1", "tag2"]
        mock_storage.save_entry.assert_called_once_with(entry)
    
    def test_create_entry_tags_default_handling(self, service, mock_storage):
        """Test that None tags become empty list."""
        entry = service.create_entry("Content", tags=None)
        
        assert entry.tags == []
        mock_storage.save_entry.assert_called_once()
    
    def test_get_entry_success(self, service, mock_storage, sample_entry):
        """Test successfully getting an entry."""
        mock_storage.load_entry.return_value = sample_entry
        
        result = service.get_entry("test-id")
        
        assert result == sample_entry
        mock_storage.load_entry.assert_called_once_with("test-id")
    
    def test_get_entry_not_found(self, service, mock_storage):
        """Test getting non-existent entry raises error."""
        mock_storage.load_entry.return_value = None
        
        with pytest.raises(EntryNotFoundError) as exc_info:
            service.get_entry("nonexistent-id")
        
        assert "nonexistent-id" in str(exc_info.value)
        mock_storage.load_entry.assert_called_once_with("nonexistent-id")
    
    def test_list_entries_default_limit(self, service, mock_storage):
        """Test listing entries with default limit."""
        entries = [JournalEntry(content=f"Entry {i}") for i in range(100)]
        mock_storage.load_all_entries.return_value = entries
        
        result = service.list_entries()
        
        assert len(result) == 50  # Default limit
        assert result == entries[:50]
        mock_storage.load_all_entries.assert_called_once()
    
    def test_list_entries_custom_limit(self, service, mock_storage):
        """Test listing entries with custom limit."""
        entries = [JournalEntry(content=f"Entry {i}") for i in range(100)]
        mock_storage.load_all_entries.return_value = entries
        
        result = service.list_entries(limit=10)
        
        assert len(result) == 10
        assert result == entries[:10]
    
    def test_list_entries_no_limit(self, service, mock_storage):
        """Test listing all entries without limit."""
        entries = [JournalEntry(content=f"Entry {i}") for i in range(100)]
        mock_storage.load_all_entries.return_value = entries
        
        result = service.list_entries(limit=None)
        
        assert len(result) == 100
        assert result == entries
    
    def test_list_entries_fewer_than_limit(self, service, mock_storage):
        """Test listing when fewer entries than limit exist."""
        entries = [JournalEntry(content=f"Entry {i}") for i in range(10)]
        mock_storage.load_all_entries.return_value = entries
        
        result = service.list_entries(limit=50)
        
        assert len(result) == 10
        assert result == entries
    
    def test_update_entry_content_only(self, service, mock_storage, sample_entry):
        """Test updating only content."""
        mock_storage.load_entry.return_value = sample_entry
        
        result = service.update_entry("test-id", content="New content")
        
        assert result.content == "New content"
        assert result.title == "Test Entry"  # Unchanged
        mock_storage.save_entry.assert_called_once_with(sample_entry)
    
    def test_update_entry_title_only(self, service, mock_storage, sample_entry):
        """Test updating only title."""
        mock_storage.load_entry.return_value = sample_entry
        
        result = service.update_entry("test-id", title="New Title")
        
        assert result.title == "New Title"
        assert result.content == "Sample content"  # Unchanged
        mock_storage.save_entry.assert_called_once_with(sample_entry)
    
    def test_update_entry_tags_only(self, service, mock_storage, sample_entry):
        """Test updating only tags."""
        mock_storage.load_entry.return_value = sample_entry
        
        result = service.update_entry("test-id", tags=["new", "tags"])
        
        assert result.tags == ["new", "tags"]
        assert result.content == "Sample content"  # Unchanged
        mock_storage.save_entry.assert_called_once_with(sample_entry)
    
    def test_update_entry_clear_tags(self, service, mock_storage, sample_entry):
        """Test clearing tags with empty list."""
        mock_storage.load_entry.return_value = sample_entry
        
        result = service.update_entry("test-id", tags=[])
        
        assert result.tags == []
        mock_storage.save_entry.assert_called_once_with(sample_entry)
    
    def test_update_entry_all_fields(self, service, mock_storage, sample_entry):
        """Test updating all fields at once."""
        mock_storage.load_entry.return_value = sample_entry
        
        result = service.update_entry(
            "test-id",
            content="New content",
            title="New title", 
            tags=["new", "tags"]
        )
        
        assert result.content == "New content"
        assert result.title == "New title"
        assert result.tags == ["new", "tags"]
        mock_storage.save_entry.assert_called_once_with(sample_entry)
    
    def test_update_entry_no_changes(self, service, mock_storage):
        """Test updating with no changes raises error."""
        with pytest.raises(InvalidEntryError) as exc_info:
            service.update_entry("test-id")
        
        assert "At least one field must be updated" in str(exc_info.value)
        mock_storage.load_entry.assert_not_called()
    
    def test_update_entry_not_found(self, service, mock_storage):
        """Test updating non-existent entry raises error."""
        mock_storage.load_entry.return_value = None
        
        with pytest.raises(EntryNotFoundError):
            service.update_entry("nonexistent-id", content="New content")
    
    def test_is_duplicate_same_date_and_content(self, service):
        """Test duplicate detection with same date and content."""
        entry1 = JournalEntry(content="Same content", created_at=datetime(2024, 1, 1))
        entry2 = JournalEntry(content="Same content", created_at=datetime(2024, 1, 1))
        
        result = service._is_duplicate(entry2, [entry1])
        
        assert result is True
    
    def test_is_duplicate_same_date_different_content(self, service):
        """Test no duplicate with same date but different content."""
        entry1 = JournalEntry(content="Content 1", created_at=datetime(2024, 1, 1))
        entry2 = JournalEntry(content="Content 2", created_at=datetime(2024, 1, 1))
        
        result = service._is_duplicate(entry2, [entry1])
        
        assert result is False
    
    def test_is_duplicate_different_date_same_content(self, service):
        """Test no duplicate with different date but same content."""
        entry1 = JournalEntry(content="Same content", created_at=datetime(2024, 1, 1))
        entry2 = JournalEntry(content="Same content", created_at=datetime(2024, 1, 2))
        
        result = service._is_duplicate(entry2, [entry1])
        
        assert result is False
    
    def test_is_duplicate_whitespace_handling(self, service):
        """Test duplicate detection handles whitespace correctly."""
        entry1 = JournalEntry(content="  Content with spaces  ", created_at=datetime(2024, 1, 1))
        entry2 = JournalEntry(content="Content with spaces", created_at=datetime(2024, 1, 1))
        
        result = service._is_duplicate(entry2, [entry1])
        
        assert result is True
    
    def test_is_duplicate_empty_list(self, service):
        """Test duplicate detection with empty existing entries."""
        entry = JournalEntry(content="New content", created_at=datetime(2024, 1, 1))
        
        result = service._is_duplicate(entry, [])
        
        assert result is False


class TestJournalServiceImport:
    """Test import functionality separately due to complexity."""
    
    @pytest.fixture
    def mock_storage(self):
        return Mock()
    
    @pytest.fixture
    def service(self, mock_storage):
        return JournalService(mock_storage)
    
    def test_import_directory_not_found(self, service):
        """Test import with non-existent directory."""
        non_existent_path = Path("/nonexistent/directory")
        
        with pytest.raises(FileNotFoundError) as exc_info:
            service.import_from_directory(non_existent_path)
        
        assert "not found" in str(exc_info.value)
    
    def test_import_directory_is_file(self, service):
        """Test import when path is a file, not directory."""
        with tempfile.NamedTemporaryFile() as temp_file:
            file_path = Path(temp_file.name)
            
            with pytest.raises(ValueError) as exc_info:
                service.import_from_directory(file_path)
            
            assert "not a directory" in str(exc_info.value)
    
    def test_import_empty_directory(self, service, mock_storage):
        """Test import from directory with no markdown files."""
        mock_storage.load_all_entries.return_value = []
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            imported, skipped = service.import_from_directory(temp_path)
            
            assert imported == []
            assert skipped == 0
    
    def test_import_with_duplicates(self, service, mock_storage):
        """Test import with existing duplicate entries."""
        # Existing entry
        existing_entry = JournalEntry(
            content="Existing content",
            created_at=datetime(2024, 1, 1)
        )
        mock_storage.load_all_entries.return_value = [existing_entry]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create markdown file that would be duplicate
            md_file = temp_path / "2024-01-01-test.md"
            md_file.write_text("Existing content")
            
            # Mock the importer to return our test entry
            from unittest.mock import patch
            with patch('src.journal_service.MarkdownImporter') as mock_importer_class:
                mock_importer = mock_importer_class.return_value
                mock_importer.import_file.return_value = JournalEntry(
                    content="Existing content",
                    created_at=datetime(2024, 1, 1)
                )
                
                imported, skipped = service.import_from_directory(temp_path)
                
                assert len(imported) == 0
                assert skipped == 1
                mock_storage.save_entry.assert_not_called()


class TestJournalServiceReflectionPrompts:
    """Test AI reflection prompt functionality."""
    
    @pytest.fixture
    def mock_storage(self):
        return Mock()
    
    @pytest.fixture
    def mock_ollama_client(self):
        return Mock(spec=OllamaClient)
    
    @pytest.fixture
    def service_with_ai(self, mock_storage, mock_ollama_client):
        return JournalService(mock_storage, mock_ollama_client)
    
    @pytest.fixture
    def service_without_ai(self, mock_storage):
        return JournalService(mock_storage)
    
    @pytest.fixture
    def sample_entry(self):
        return JournalEntry(
            id="test-123",
            content="Had a challenging day at work. My manager gave me feedback that was hard to hear.",
            title="Tough Day"
        )
    
    def test_generate_reflection_prompt_success(self, service_with_ai, mock_storage, mock_ollama_client, sample_entry):
        """Test successful reflection prompt generation."""
        # Setup
        mock_storage.load_entry.return_value = sample_entry
        mock_ollama_client.generate.return_value = "How did you feel when receiving that feedback?"
        
        # Execute
        result = service_with_ai.generate_reflection_prompt("test-123")
        
        # Verify
        assert result["reflection_prompt"] == "How did you feel when receiving that feedback?"
        assert result["strategy_used"] == "empathetic_v1"
        assert "timestamp" in result
        assert "entry_preview" in result
        
        mock_storage.load_entry.assert_called_once_with("test-123")
        mock_ollama_client.generate.assert_called_once()
    
    def test_generate_reflection_prompt_custom_strategy(self, service_with_ai, mock_storage, mock_ollama_client, sample_entry):
        """Test reflection prompt generation with custom strategy."""
        # Setup
        mock_storage.load_entry.return_value = sample_entry
        mock_ollama_client.generate.return_value = "What patterns do you notice in feedback situations?"
        
        # Execute
        result = service_with_ai.generate_reflection_prompt("test-123", strategy="analytical_v1")
        
        # Verify
        assert result["strategy_used"] == "analytical_v1"
        mock_ollama_client.generate.assert_called_once()
    
    def test_generate_reflection_prompt_entry_not_found(self, service_with_ai, mock_storage):
        """Test reflection prompt generation with non-existent entry."""
        # Setup
        mock_storage.load_entry.return_value = None
        
        # Execute & Verify
        with pytest.raises(EntryNotFoundError):
            service_with_ai.generate_reflection_prompt("nonexistent-id")
    
    def test_generate_reflection_prompt_no_ai_client(self, service_without_ai):
        """Test reflection prompt generation without AI client configured."""
        with pytest.raises(ValueError) as exc_info:
            service_without_ai.generate_reflection_prompt("test-123")
        
        assert "No AI client configured" in str(exc_info.value)
    
    def test_generate_reflection_prompt_invalid_strategy(self, service_with_ai, mock_storage, sample_entry):
        """Test reflection prompt generation with invalid strategy."""
        # Setup
        mock_storage.load_entry.return_value = sample_entry
        
        # Execute & Verify
        with pytest.raises(ValueError) as exc_info:
            service_with_ai.generate_reflection_prompt("test-123", strategy="invalid_strategy")
        
        assert "Unknown strategy" in str(exc_info.value)
    
    def test_generate_reflection_prompt_ollama_error(self, service_with_ai, mock_storage, mock_ollama_client, sample_entry):
        """Test reflection prompt generation when Ollama fails."""
        # Setup
        mock_storage.load_entry.return_value = sample_entry
        mock_ollama_client.generate.side_effect = requests.exceptions.ConnectionError("Ollama not available")
        
        # Execute & Verify
        with pytest.raises(requests.exceptions.ConnectionError):
            service_with_ai.generate_reflection_prompt("test-123")
    
    def test_list_reflection_strategies_success(self, service_with_ai):
        """Test listing available reflection strategies."""
        strategies = service_with_ai.list_reflection_strategies()
        
        assert isinstance(strategies, list)
        assert "empathetic_v1" in strategies
        assert "analytical_v1" in strategies
        assert "socratic_v1" in strategies
    
    def test_list_reflection_strategies_no_ai_client(self, service_without_ai):
        """Test listing strategies without AI client configured."""
        with pytest.raises(ValueError) as exc_info:
            service_without_ai.list_reflection_strategies()
        
        assert "No AI client configured" in str(exc_info.value)
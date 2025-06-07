import pytest
import sys
from io import StringIO
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from pathlib import Path

from src.cli import JournalCLI, main
from src.models import JournalEntry
from src.journal_service import EntryNotFoundError, InvalidEntryError


# Fixtures available to all test classes
@pytest.fixture
def mock_service():
    """Create a mock journal service."""
    return Mock()

@pytest.fixture
def cli_with_mock_service(mock_service):
    """Create CLI instance with mocked service."""
    with patch('src.cli.JournalService', return_value=mock_service):
        with patch('src.cli.JSONStorage'):
            cli = JournalCLI()
            cli.service = mock_service
            return cli

@pytest.fixture
def sample_entries():
    """Create sample journal entries for testing."""
    return [
        JournalEntry(
            id="550e8400-e29b-41d4-a716-446655440000",
            title="Morning thoughts",
            content="Today I woke up feeling energized and ready to tackle the day.",
            created_at=datetime(2024, 1, 15, 8, 30),
            tags=["morning", "energy"]
        ),
        JournalEntry(
            id="8b2c1f90-123a-4567-8901-234567890123",
            title="Evening reflection",
            content="Had an interesting conversation with my colleague about AI.",
            created_at=datetime(2024, 1, 14, 20, 15),
            tags=["work", "ai"]
        )
    ]


class TestJournalCLI:
    pass


class TestCreateEntry:
    
    def test_create_entry_with_all_fields(self, cli_with_mock_service):
        """Test creating entry with content, title, and tags."""
        mock_entry = JournalEntry(id="new-id", content="Test content", title="Test title")
        cli_with_mock_service.service.create_entry.return_value = mock_entry
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            cli_with_mock_service.create_entry(
                content="Test content",
                title="Test title", 
                tags="tag1,tag2"
            )
        
        cli_with_mock_service.service.create_entry.assert_called_once_with(
            content="Test content",
            title="Test title",
            tags=["tag1", "tag2"]
        )
        assert "Created entry new-id" in mock_stdout.getvalue()
    
    def test_create_entry_with_empty_content(self, cli_with_mock_service):
        """Test creating entry with empty content."""
        mock_entry = JournalEntry(id="new-id", content="")
        cli_with_mock_service.service.create_entry.return_value = mock_entry
        
        with patch('sys.stdout', new_callable=StringIO):
            cli_with_mock_service.create_entry(content=None)
        
        cli_with_mock_service.service.create_entry.assert_called_once_with(
            content="",
            title=None,
            tags=[]
        )
    
    def test_create_entry_with_tags_parsing(self, cli_with_mock_service):
        """Test tag parsing with spaces and commas."""
        mock_entry = JournalEntry(id="new-id")
        cli_with_mock_service.service.create_entry.return_value = mock_entry
        
        cli_with_mock_service.create_entry(tags="tag1, tag2 , tag3")
        
        cli_with_mock_service.service.create_entry.assert_called_once_with(
            content="",
            title=None,
            tags=["tag1", "tag2", "tag3"]
        )
    
    def test_create_entry_service_error(self, cli_with_mock_service):
        """Test handling service errors during creation."""
        cli_with_mock_service.service.create_entry.side_effect = Exception("Service error")
        
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            with pytest.raises(SystemExit) as exc_info:
                cli_with_mock_service.create_entry(content="Test")
        
        assert exc_info.value.code == 1
        assert "Error creating entry: Service error" in mock_stderr.getvalue()


class TestListEntries:
    
    def test_list_entries_with_data(self, cli_with_mock_service, sample_entries):
        """Test listing entries with sample data."""
        cli_with_mock_service.service.list_entries.return_value = sample_entries
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            cli_with_mock_service.list_entries(limit=10)
        
        output = mock_stdout.getvalue()
        
        # Check table header
        assert "ID" in output
        assert "Date" in output
        assert "Title" in output
        assert "Preview" in output
        
        # Check entry data
        assert "550e8400" in output  # Short ID
        assert "2024-01-15" in output  # Date
        assert "Morning thoughts" in output  # Title
        assert "Today I woke up feeling" in output  # Content preview
        
        cli_with_mock_service.service.list_entries.assert_called_once_with(limit=10)
    
    def test_list_entries_empty(self, cli_with_mock_service):
        """Test listing when no entries exist."""
        cli_with_mock_service.service.list_entries.return_value = []
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            cli_with_mock_service.list_entries()
        
        output = mock_stdout.getvalue()
        assert "No journal entries found" in output
    
    def test_list_entries_no_title(self, cli_with_mock_service):
        """Test listing entries that have no title."""
        entry_no_title = JournalEntry(
            id="no-title-id",
            title=None,
            content="Content without title",
            created_at=datetime(2024, 1, 15)
        )
        cli_with_mock_service.service.list_entries.return_value = [entry_no_title]
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            cli_with_mock_service.list_entries()
        
        output = mock_stdout.getvalue()
        assert "(no title)" in output
    
    def test_list_entries_service_error(self, cli_with_mock_service):
        """Test handling service errors during listing."""
        cli_with_mock_service.service.list_entries.side_effect = Exception("Service error")
        
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            with pytest.raises(SystemExit) as exc_info:
                cli_with_mock_service.list_entries()
        
        assert exc_info.value.code == 1
        assert "Error listing entries: Service error" in mock_stderr.getvalue()


class TestShowEntry:
    
    def test_show_entry_success(self, cli_with_mock_service, sample_entries):
        """Test showing an entry successfully."""
        entry = sample_entries[0]
        cli_with_mock_service.service.list_entries.return_value = [entry]
        cli_with_mock_service.service.get_entry.return_value = entry
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            cli_with_mock_service.show_entry("550e8400")
        
        output = mock_stdout.getvalue()
        
        # Check metadata display
        assert "ID: 550e8400" in output
        assert "Title: Morning thoughts" in output
        assert "Created: 2024-01-15 08:30:00" in output
        assert "Tags: morning, energy" in output
        
        # Check content display
        assert "Today I woke up feeling energized" in output
    
    def test_show_entry_no_title_no_tags(self, cli_with_mock_service):
        """Test showing entry with no title or tags."""
        entry = JournalEntry(
            id="test-id",
            title=None,
            content="Content only",
            created_at=datetime(2024, 1, 15),
            tags=[]
        )
        cli_with_mock_service.service.list_entries.return_value = [entry]
        cli_with_mock_service.service.get_entry.return_value = entry
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            cli_with_mock_service.show_entry("test-id")
        
        output = mock_stdout.getvalue()
        assert "Title: (no title)" in output
        assert "Tags: (no tags)" in output
    
    def test_show_entry_not_found(self, cli_with_mock_service):
        """Test showing non-existent entry."""
        cli_with_mock_service.service.list_entries.return_value = []
        
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            with pytest.raises(SystemExit) as exc_info:
                cli_with_mock_service.show_entry("nonexistent")
        
        assert exc_info.value.code == 1
        assert "Entry with ID 'nonexistent' not found" in mock_stderr.getvalue()
    
    def test_show_entry_with_content(self, cli_with_mock_service):
        """Test showing entry with regular content."""
        entry = JournalEntry(
            id="content-id", 
            content="Regular ASCII content for testing",
            created_at=datetime(2024, 1, 15)
        )
        cli_with_mock_service.service.list_entries.return_value = [entry]
        cli_with_mock_service.service.get_entry.return_value = entry
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            cli_with_mock_service.show_entry("content-id")
        
        output = mock_stdout.getvalue()
        assert "Regular ASCII content for testing" in output


class TestEditEntry:
    
    def test_edit_entry_success(self, cli_with_mock_service, sample_entries):
        """Test editing entry successfully."""
        entry = sample_entries[0]
        updated_entry = JournalEntry(id=entry.id, title="Updated title", content=entry.content)
        
        cli_with_mock_service.service.list_entries.return_value = [entry]
        cli_with_mock_service.service.update_entry.return_value = updated_entry
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            cli_with_mock_service.edit_entry("550e8400", title="Updated title")
        
        cli_with_mock_service.service.update_entry.assert_called_once_with(
            entry_id=entry.id,
            content=None,
            title="Updated title",
            tags=None
        )
        assert "Updated entry 550e8400" in mock_stdout.getvalue()
    
    def test_edit_entry_with_tags(self, cli_with_mock_service, sample_entries):
        """Test editing entry with tags."""
        entry = sample_entries[0]
        cli_with_mock_service.service.list_entries.return_value = [entry]
        cli_with_mock_service.service.update_entry.return_value = entry
        
        cli_with_mock_service.edit_entry("550e8400", tags="new,tags,here")
        
        cli_with_mock_service.service.update_entry.assert_called_once_with(
            entry_id=entry.id,
            content=None,
            title=None,
            tags=["new", "tags", "here"]
        )
    
    def test_edit_entry_empty_tags(self, cli_with_mock_service, sample_entries):
        """Test editing entry with empty tags string."""
        entry = sample_entries[0]
        cli_with_mock_service.service.list_entries.return_value = [entry]
        cli_with_mock_service.service.update_entry.return_value = entry
        
        cli_with_mock_service.edit_entry("550e8400", tags="")
        
        cli_with_mock_service.service.update_entry.assert_called_once_with(
            entry_id=entry.id,
            content=None,
            title=None,
            tags=[]
        )
    
    def test_edit_entry_not_found(self, cli_with_mock_service):
        """Test editing non-existent entry."""
        cli_with_mock_service.service.list_entries.return_value = []
        
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            with pytest.raises(SystemExit) as exc_info:
                cli_with_mock_service.edit_entry("nonexistent", title="New title")
        
        assert exc_info.value.code == 1
        assert "Entry with ID 'nonexistent' not found" in mock_stderr.getvalue()
    
    def test_edit_entry_invalid_update(self, cli_with_mock_service, sample_entries):
        """Test editing with invalid update (no fields)."""
        entry = sample_entries[0]
        cli_with_mock_service.service.list_entries.return_value = [entry]
        cli_with_mock_service.service.update_entry.side_effect = InvalidEntryError("No fields to update")
        
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            with pytest.raises(SystemExit) as exc_info:
                cli_with_mock_service.edit_entry("550e8400", content=None)
        
        assert exc_info.value.code == 1
        assert "Invalid update: No fields to update" in mock_stderr.getvalue()


class TestImportEntries:
    
    def test_import_entries_success(self, cli_with_mock_service, sample_entries):
        """Test importing entries successfully."""
        cli_with_mock_service.service.import_from_directory.return_value = (sample_entries, 1)
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            cli_with_mock_service.import_entries("./test_dir")
        
        output = mock_stdout.getvalue()
        
        assert "Import complete:" in output
        assert "Imported: 2 entries" in output
        assert "Skipped: 1 duplicates" in output
        assert "550e8400 - 2024-01-15 - Morning thoughts" in output
        
        cli_with_mock_service.service.import_from_directory.assert_called_once_with(Path("./test_dir"))
    
    def test_import_entries_many_entries(self, cli_with_mock_service):
        """Test importing many entries (more than 5)."""
        many_entries = [
            JournalEntry(id=f"id-{i}", title=f"Entry {i}", created_at=datetime(2024, 1, i+1))
            for i in range(10)
        ]
        cli_with_mock_service.service.import_from_directory.return_value = (many_entries, 0)
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            cli_with_mock_service.import_entries("./test_dir")
        
        output = mock_stdout.getvalue()
        assert "Imported: 10 entries" in output
        assert "... and 5 more" in output
    
    def test_import_entries_no_entries(self, cli_with_mock_service):
        """Test importing from empty directory."""
        cli_with_mock_service.service.import_from_directory.return_value = ([], 0)
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            cli_with_mock_service.import_entries("./empty_dir")
        
        output = mock_stdout.getvalue()
        assert "Imported: 0 entries" in output
        assert "Skipped: 0 duplicates" in output
    
    def test_import_entries_directory_not_found(self, cli_with_mock_service):
        """Test importing from non-existent directory."""
        cli_with_mock_service.service.import_from_directory.side_effect = FileNotFoundError("Directory not found")
        
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            with pytest.raises(SystemExit) as exc_info:
                cli_with_mock_service.import_entries("./nonexistent")
        
        assert exc_info.value.code == 1
        assert "Directory not found" in mock_stderr.getvalue()


class TestUtilityMethods:
    
    def test_short_id(self, cli_with_mock_service):
        """Test short ID generation."""
        full_id = "550e8400-e29b-41d4-a716-446655440000"
        short_id = cli_with_mock_service._short_id(full_id)
        assert short_id == "550e8400"
    
    def test_resolve_short_id_exact_match(self, cli_with_mock_service, sample_entries):
        """Test resolving short ID with exact match."""
        cli_with_mock_service.service.list_entries.return_value = sample_entries
        
        resolved_id = cli_with_mock_service._resolve_short_id("550e8400")
        assert resolved_id == "550e8400-e29b-41d4-a716-446655440000"
    
    def test_resolve_short_id_already_full(self, cli_with_mock_service):
        """Test resolving ID that's already full length."""
        full_id = "550e8400-e29b-41d4-a716-446655440000"
        resolved_id = cli_with_mock_service._resolve_short_id(full_id)
        assert resolved_id == full_id
    
    def test_resolve_short_id_not_found(self, cli_with_mock_service):
        """Test resolving non-existent short ID."""
        cli_with_mock_service.service.list_entries.return_value = []
        
        with pytest.raises(EntryNotFoundError) as exc_info:
            cli_with_mock_service._resolve_short_id("nonexist")
        
        assert "No entry found with ID starting with 'nonexist'" in str(exc_info.value)
    
    def test_resolve_short_id_ambiguous(self, cli_with_mock_service):
        """Test resolving ambiguous short ID."""
        # Create entries with same prefix
        entries = [
            JournalEntry(id="550e8400-e29b-41d4-a716-446655440000", title="Entry 1"),
            JournalEntry(id="550e8401-e29b-41d4-a716-446655440000", title="Entry 2")
        ]
        cli_with_mock_service.service.list_entries.return_value = entries
        
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            with pytest.raises(SystemExit) as exc_info:
                cli_with_mock_service._resolve_short_id("550e84")
        
        assert exc_info.value.code == 1
        stderr_output = mock_stderr.getvalue()
        assert "Ambiguous ID '550e84'" in stderr_output
        assert "550e8400 - Entry 1" in stderr_output
        assert "550e8401 - Entry 2" in stderr_output
    
    def test_truncate_text(self, cli_with_mock_service):
        """Test text truncation."""
        # Short text - no truncation
        short_text = "Short"
        assert cli_with_mock_service._truncate(short_text, 10) == "Short"
        
        # Long text - truncation
        long_text = "This is a very long text that needs truncation"
        truncated = cli_with_mock_service._truncate(long_text, 20)
        assert len(truncated) == 20
        assert truncated.endswith("...")
    
    def test_get_content_preview(self, cli_with_mock_service):
        """Test content preview generation."""
        # Empty content
        assert cli_with_mock_service._get_content_preview("", 50) == "(empty)"
        
        # Short content
        short_content = "Short content"
        assert cli_with_mock_service._get_content_preview(short_content, 50) == "Short content"
        
        # Long content with word boundary truncation
        long_content = "This is a very long piece of content that should be truncated at word boundaries"
        preview = cli_with_mock_service._get_content_preview(long_content, 30)
        assert len(preview) <= 33  # 30 + "..."
        assert preview.endswith("...")
        assert " " not in preview[-4:]  # Should not end with partial word


class TestMainFunction:
    
    def test_main_with_create_command(self):
        """Test main function with create command."""
        test_args = ['journal.py', 'create', '--content', 'Test content', '--title', 'Test title']
        
        with patch('sys.argv', test_args):
            with patch('src.cli.JournalCLI') as mock_cli_class:
                mock_cli = Mock()
                mock_cli_class.return_value = mock_cli
                
                main()
                
                mock_cli.create_entry.assert_called_once_with(
                    content='Test content',
                    title='Test title',
                    tags=None
                )
    
    def test_main_with_list_command(self):
        """Test main function with list command."""
        test_args = ['journal.py', 'list', '--limit', '10']
        
        with patch('sys.argv', test_args):
            with patch('src.cli.JournalCLI') as mock_cli_class:
                mock_cli = Mock()
                mock_cli_class.return_value = mock_cli
                
                main()
                
                mock_cli.list_entries.assert_called_once_with(limit=10)
    
    def test_main_with_show_command(self):
        """Test main function with show command."""
        test_args = ['journal.py', 'show', 'abc123']
        
        with patch('sys.argv', test_args):
            with patch('src.cli.JournalCLI') as mock_cli_class:
                mock_cli = Mock()
                mock_cli_class.return_value = mock_cli
                
                main()
                
                mock_cli.show_entry.assert_called_once_with('abc123')
    
    def test_main_with_edit_command(self):
        """Test main function with edit command."""
        test_args = ['journal.py', 'edit', 'abc123', '--title', 'New title', '--tags', 'tag1,tag2']
        
        with patch('sys.argv', test_args):
            with patch('src.cli.JournalCLI') as mock_cli_class:
                mock_cli = Mock()
                mock_cli_class.return_value = mock_cli
                
                main()
                
                mock_cli.edit_entry.assert_called_once_with(
                    'abc123',
                    content=None,
                    title='New title',
                    tags='tag1,tag2'
                )
    
    def test_main_with_import_command(self):
        """Test main function with import command."""
        test_args = ['journal.py', 'import', './import_data']
        
        with patch('sys.argv', test_args):
            with patch('src.cli.JournalCLI') as mock_cli_class:
                mock_cli = Mock()
                mock_cli_class.return_value = mock_cli
                
                main()
                
                mock_cli.import_entries.assert_called_once_with('./import_data')
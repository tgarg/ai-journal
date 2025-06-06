import pytest
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock

from src.models import JournalEntry
from src.markdown_importer import MarkdownImporter


class TestMarkdownImporter:
    
    @pytest.fixture
    def mock_storage(self):
        """Create a mock storage backend."""
        return Mock()
    
    @pytest.fixture
    def importer(self, mock_storage):
        """Create a MarkdownImporter with mock storage."""
        return MarkdownImporter(mock_storage)
    
    def test_extract_date_from_filename_dash_format(self, importer):
        file_path = Path("2024-01-15-my-entry.md")
        date = importer._extract_date_from_filename(file_path)
        
        assert date is not None
        assert date.year == 2024
        assert date.month == 1
        assert date.day == 15
    
    def test_extract_date_from_filename_underscore_format(self, importer):
        file_path = Path("2024_01_15_my_entry.md")
        date = importer._extract_date_from_filename(file_path)
        
        assert date is not None
        assert date.year == 2024
        assert date.month == 1
        assert date.day == 15
    
    def test_extract_date_from_filename_compact_format(self, importer):
        file_path = Path("20240115-journal.md")
        date = importer._extract_date_from_filename(file_path)
        
        assert date is not None
        assert date.year == 2024
        assert date.month == 1
        assert date.day == 15
    
    def test_extract_date_from_filename_no_date(self, importer):
        file_path = Path("my-journal-entry.md")
        date = importer._extract_date_from_filename(file_path)
        
        assert date is None
    
    def test_parse_frontmatter_with_yaml(self, importer):
        content = """---
title: My Test Entry
date: 2024-01-15
tags: [personal, reflection]
---

This is the body content of the entry."""
        
        frontmatter, body = importer._parse_frontmatter(content)
        
        assert frontmatter["title"] == "My Test Entry"
        assert frontmatter["date"] == "2024-01-15"
        assert frontmatter["tags"] == ["personal", "reflection"]
        assert body == "This is the body content of the entry."
    
    def test_parse_frontmatter_without_yaml(self, importer):
        content = "Just regular markdown content without frontmatter."
        
        frontmatter, body = importer._parse_frontmatter(content)
        
        assert frontmatter == {}
        assert body == content
    
    def test_parse_frontmatter_empty_yaml(self, importer):
        content = """---
---

Body content here."""
        
        frontmatter, body = importer._parse_frontmatter(content)
        
        assert frontmatter == {}
        assert body == "Body content here."
    
    def test_parse_date_various_formats(self, importer):
        # Test different date formats
        test_cases = [
            ("2024-01-15", datetime(2024, 1, 15)),
            ("2024-01-15 10:30:00", datetime(2024, 1, 15, 10, 30, 0)),
            ("2024-01-15T10:30:00", datetime(2024, 1, 15, 10, 30, 0)),
            ("2024/01/15", datetime(2024, 1, 15)),
        ]
        
        for date_str, expected in test_cases:
            result = importer._parse_date(date_str)
            assert result == expected
    
    def test_parse_date_invalid_format(self, importer):
        result = importer._parse_date("invalid-date")
        assert result is None
    
    def test_parse_date_none_input(self, importer):
        result = importer._parse_date(None)
        assert result is None
    
    def test_import_file_with_frontmatter(self, importer):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("""---
title: Test Entry
date: 2024-01-15
tags: test, imported
---

This is my journal entry content.""")
            f.flush()
            
            file_path = Path(f.name)
            
        try:
            entry = importer.import_file(file_path)
            
            assert entry.title == "Test Entry"
            assert entry.content == "This is my journal entry content."
            assert entry.created_at.year == 2024
            assert entry.created_at.month == 1
            assert entry.created_at.day == 15
            assert "test" in entry.tags
            assert "imported" in entry.tags
        finally:
            file_path.unlink()
    
    def test_import_file_date_priority(self, importer):
        # Test that filename date takes priority over frontmatter date
        with tempfile.NamedTemporaryFile(mode='w', suffix='2024-01-15-test.md', delete=False) as f:
            f.write("""---
title: Test Entry
date: 2023-12-01
---

Content here.""")
            f.flush()
            
            file_path = Path(f.name)
            
        try:
            entry = importer.import_file(file_path)
            
            # Should use filename date (2024-01-15), not frontmatter date (2023-12-01)
            assert entry.created_at.year == 2024
            assert entry.created_at.month == 1
            assert entry.created_at.day == 15
        finally:
            file_path.unlink()
    
    def test_import_file_without_frontmatter(self, importer):
        with tempfile.NamedTemporaryFile(mode='w', suffix='2024-01-15-simple.md', delete=False) as f:
            f.write("Just simple content without frontmatter.")
            f.flush()
            
            file_path = Path(f.name)
            
        try:
            entry = importer.import_file(file_path)
            
            assert entry.title == file_path.stem  # Should use filename as title
            assert entry.content == "Just simple content without frontmatter."
            assert entry.tags == []
        finally:
            file_path.unlink()
    
    def test_import_directory(self, importer, mock_storage):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test markdown files
            file1 = temp_path / "2024-01-01-entry1.md"
            file2 = temp_path / "2024-01-02-entry2.md"
            file3 = temp_path / "not-markdown.txt"  # Should be ignored
            
            file1.write_text("Entry 1 content")
            file2.write_text("Entry 2 content")
            file3.write_text("Not markdown")
            
            entries = importer.import_directory(temp_path)
            
            assert len(entries) == 2
            assert mock_storage.save_entry.call_count == 2
    
    def test_import_directory_with_pattern(self, importer, mock_storage):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create files with different extensions
            (temp_path / "entry1.md").write_text("MD content")
            (temp_path / "entry2.markdown").write_text("Markdown content")
            (temp_path / "entry3.txt").write_text("Text content")
            
            # Import only .markdown files
            entries = importer.import_directory(temp_path, "*.markdown")
            
            assert len(entries) == 1
            assert mock_storage.save_entry.call_count == 1
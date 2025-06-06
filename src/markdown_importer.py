import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import uuid

from .models import JournalEntry
from .storage import StorageBackend


class MarkdownImporter:
    """Utility for importing markdown journal entries."""
    
    def __init__(self, storage: StorageBackend):
        self.storage = storage
    
    def import_file(self, file_path: Path) -> JournalEntry:
        """Import a single markdown file as a journal entry."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse frontmatter and content
        frontmatter, body = self._parse_frontmatter(content)
        
        # Extract metadata
        title = frontmatter.get('title') or file_path.stem
        created_at = self._extract_date_from_filename(file_path) or \
                    self._parse_date(frontmatter.get('date')) or \
                    self._get_file_date(file_path)
        tags = frontmatter.get('tags', [])
        if isinstance(tags, str):
            tags = [tag.strip() for tag in tags.split(',')]
        
        # Create entry
        entry = JournalEntry(
            id=str(uuid.uuid4()),
            title=title,
            content=body.strip(),
            created_at=created_at,
            updated_at=created_at,
            tags=tags
        )
        
        return entry
    
    def import_directory(self, directory_path: Path, pattern: str = "*.md") -> List[JournalEntry]:
        """Import all markdown files from a directory."""
        imported_entries = []
        
        for file_path in directory_path.glob(pattern):
            if file_path.is_file():
                try:
                    entry = self.import_file(file_path)
                    self.storage.save_entry(entry)
                    imported_entries.append(entry)
                except Exception as e:
                    print(f"Error importing {file_path}: {e}")
        
        return imported_entries
    
    def _extract_date_from_filename(self, file_path: Path) -> Optional[datetime]:
        """Extract date from filename patterns like 2024-01-15, 20240115, etc."""
        filename = file_path.stem
        
        # Common date patterns in filenames
        patterns = [
            r'(\d{4}-\d{2}-\d{2})',  # 2024-01-15
            r'(\d{4}_\d{2}_\d{2})',  # 2024_01_15
            r'(\d{8})',              # 20240115
            r'(\d{4}\d{2}\d{2})',    # 20240115
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename)
            if match:
                date_str = match.group(1)
                
                # Try different formats
                formats = [
                    "%Y-%m-%d",
                    "%Y_%m_%d", 
                    "%Y%m%d"
                ]
                
                for fmt in formats:
                    try:
                        return datetime.strptime(date_str, fmt)
                    except ValueError:
                        continue
        
        return None
    
    def _parse_frontmatter(self, content: str) -> tuple[Dict[str, Any], str]:
        """Parse YAML frontmatter from markdown content."""
        frontmatter = {}
        body = content
        
        # Check for YAML frontmatter
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                frontmatter_text = parts[1].strip()
                body = parts[2].strip()
                
                # Simple YAML parsing for common fields
                for line in frontmatter_text.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip()
                        value = value.strip().strip('"\'')
                        
                        # Handle lists
                        if value.startswith('[') and value.endswith(']'):
                            value = [item.strip().strip('"\'') for item in value[1:-1].split(',')]
                        
                        frontmatter[key] = value
        
        return frontmatter, body
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string in various formats."""
        if not date_str:
            return None
        
        # Common date formats
        formats = [
            "%Y-%m-%d",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y/%m/%d",
            "%m/%d/%Y",
            "%d/%m/%Y"
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        return None
    
    def _get_file_date(self, file_path: Path) -> datetime:
        """Get file creation/modification date as fallback."""
        try:
            # Use modification time as fallback
            return datetime.fromtimestamp(file_path.stat().st_mtime)
        except:
            return datetime.now()
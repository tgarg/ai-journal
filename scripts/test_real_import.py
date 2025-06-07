#!/usr/bin/env python3
"""
Temporary test script to import user's actual markdown journal entries.
This script will be replaced by CLI and web interface functionality later.
"""

import sys
from pathlib import Path

# Add src to Python path to import our modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import only what we need and avoid relative import issues
from models import JournalEntry
from json_storage import JSONStorage  
from markdown_importer import MarkdownImporter


def main():
    print("🚀 Testing real journal data import...")
    
    # Initialize storage and importer (relative to project root)
    project_root = Path(__file__).parent.parent
    storage = JSONStorage(project_root / "data")
    importer = MarkdownImporter(storage)
    
    # Check import directory
    import_dir = project_root / "import_data"
    if not import_dir.exists():
        print("❌ import_data directory not found!")
        return
    
    # List markdown files
    md_files = list(import_dir.glob("*.md"))
    print(f"📁 Found {len(md_files)} markdown files:")
    for file in md_files:
        print(f"  - {file.name}")
    
    if not md_files:
        print("⚠️  No .md files found in import_data/")
        return
    
    # Import all files
    print(f"\n🔄 Importing {len(md_files)} entries...")
    try:
        imported_entries = importer.import_directory(import_dir)
        print(f"✅ Successfully imported {len(imported_entries)} entries!")
        
        # Show details of imported entries
        print(f"\n📊 Import Results:")
        for i, entry in enumerate(imported_entries, 1):
            print(f"  {i}. {entry.title or entry.id[:8]} - {entry.created_at.strftime('%Y-%m-%d')} ({len(entry.content)} chars)")
        
        # Test storage functionality
        print(f"\n💾 Testing storage...")
        all_entries = storage.load_all_entries()
        print(f"  Total entries in storage: {len(all_entries)}")
        
        # Test search functionality
        test_searches = ["today", "feeling", "work"]
        for term in test_searches:
            results = storage.search_entries(term)
            print(f"  Entries containing '{term}': {len(results)}")
        
        # Show sample entry content
        if imported_entries:
            sample = imported_entries[0]
            print(f"\n📝 Sample entry preview:")
            print(f"  Title: {sample.title}")
            print(f"  Date: {sample.created_at}")
            print(f"  Tags: {sample.tags}")
            print(f"  Content preview: {sample.content[:200]}...")
        
        print(f"\n🎉 Import test completed successfully!")
        print(f"📁 Data saved to: data/entries.json")
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
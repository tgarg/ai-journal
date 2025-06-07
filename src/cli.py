#!/usr/bin/env python3
"""
AI Journal CLI Interface

Command-line interface for managing journal entries using the JournalService.
Supports creating, listing, viewing, editing, and importing journal entries.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from .models import JournalEntry
from .json_storage import JSONStorage
from .journal_service import JournalService, EntryNotFoundError, InvalidEntryError
from .ollama_client import OllamaClient


class JournalCLI:
    """Command-line interface for journal operations."""
    
    def __init__(self, data_dir: str = "data"):
        """Initialize CLI with storage and service."""
        self.storage = JSONStorage(data_dir)
        # Try to initialize with AI client, fallback to basic service if unavailable
        try:
            self.ollama_client = OllamaClient()
            self.service = JournalService(self.storage, self.ollama_client)
        except Exception:
            # AI features unavailable, use basic service
            self.service = JournalService(self.storage)
            self.ollama_client = None
    
    def create_entry(self, content: str = None, title: str = None, tags: str = None) -> None:
        """Create a new journal entry."""
        try:
            tag_list = []
            if tags:
                tag_list = [tag.strip() for tag in tags.split(',')]
            
            if not content:
                content = ""  # Allow empty content as per design decision
            
            entry = self.service.create_entry(content=content, title=title, tags=tag_list)
            print(f"Created entry {self._short_id(entry.id)}")
            
        except Exception as e:
            print(f"Error creating entry: {e}", file=sys.stderr)
            sys.exit(1)
    
    def list_entries(self, limit: int = 50) -> None:
        """List journal entries in table format."""
        try:
            entries = self.service.list_entries(limit=limit)
            
            if not entries:
                print("No journal entries found.")
                return
            
            # Print table header
            print(f"{'ID':<8} | {'Date':<10} | {'Title':<20} | {'Preview'}")
            print("-" * 80)
            
            # Print entries
            for entry in entries:
                short_id = self._short_id(entry.id)
                date_str = entry.created_at.strftime("%Y-%m-%d")
                title = entry.title or "(no title)"
                title = self._truncate(title, 20)
                preview = self._get_content_preview(entry.content, 50)
                
                print(f"{short_id:<8} | {date_str:<10} | {title:<20} | {preview}")
                
        except Exception as e:
            print(f"Error listing entries: {e}", file=sys.stderr)
            sys.exit(1)
    
    def show_entry(self, entry_id: str) -> None:
        """Show a specific journal entry."""
        try:
            full_id = self._resolve_short_id(entry_id)
            entry = self.service.get_entry(full_id)
            
            print(f"ID: {self._short_id(entry.id)}")
            print(f"Title: {entry.title or '(no title)'}")
            print(f"Created: {entry.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Updated: {entry.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Tags: {', '.join(entry.tags) if entry.tags else '(no tags)'}")
            print("-" * 50)
            # Handle encoding issues in content display
            try:
                print(entry.content)
            except UnicodeEncodeError:
                # Fallback to ASCII-safe version
                safe_content = entry.content.encode('ascii', errors='ignore').decode('ascii')
                print(safe_content)
                print("\n[Note: Some special characters were removed for display compatibility]")
            
        except EntryNotFoundError:
            print(f"Entry with ID '{entry_id}' not found.", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error showing entry: {e}", file=sys.stderr)
            sys.exit(1)
    
    def edit_entry(self, entry_id: str, content: str = None, title: str = None, tags: str = None) -> None:
        """Edit an existing journal entry."""
        try:
            full_id = self._resolve_short_id(entry_id)
            
            # Parse tags if provided
            tag_list = None
            if tags is not None:
                tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
            
            # Update entry
            updated_entry = self.service.update_entry(
                entry_id=full_id,
                content=content,
                title=title,
                tags=tag_list
            )
            
            print(f"Updated entry {self._short_id(updated_entry.id)}")
            
        except EntryNotFoundError:
            print(f"Entry with ID '{entry_id}' not found.", file=sys.stderr)
            sys.exit(1)
        except InvalidEntryError as e:
            print(f"Invalid update: {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error updating entry: {e}", file=sys.stderr)
            sys.exit(1)
    
    def import_entries(self, directory: str) -> None:
        """Import journal entries from markdown files."""
        try:
            directory_path = Path(directory)
            imported_entries, skipped_count = self.service.import_from_directory(directory_path)
            
            print(f"Import complete:")
            print(f"  Imported: {len(imported_entries)} entries")
            print(f"  Skipped: {skipped_count} duplicates")
            
            if imported_entries:
                print(f"\nImported entries:")
                for entry in imported_entries[:5]:  # Show first 5
                    short_id = self._short_id(entry.id)
                    date_str = entry.created_at.strftime("%Y-%m-%d")
                    title = entry.title or "(no title)"
                    print(f"  {short_id} - {date_str} - {title}")
                
                if len(imported_entries) > 5:
                    print(f"  ... and {len(imported_entries) - 5} more")
            
        except FileNotFoundError as e:
            print(f"Directory not found: {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error importing entries: {e}", file=sys.stderr)
            sys.exit(1)
    
    def _short_id(self, full_id: str) -> str:
        """Convert full UUID to short ID (first 8 characters)."""
        return full_id[:8]
    
    def _resolve_short_id(self, short_id: str) -> str:
        """Resolve short ID to full UUID."""
        if len(short_id) >= 32:  # Already full ID
            return short_id
        
        # Find matching entry
        entries = self.service.list_entries(limit=None)  # Get all entries
        matches = [entry for entry in entries if entry.id.startswith(short_id)]
        
        if not matches:
            raise EntryNotFoundError(f"No entry found with ID starting with '{short_id}'")
        
        if len(matches) > 1:
            print(f"Ambiguous ID '{short_id}'. Matches:", file=sys.stderr)
            for match in matches[:5]:  # Show first 5 matches
                print(f"  {self._short_id(match.id)} - {match.title or '(no title)'}", file=sys.stderr)
            sys.exit(1)
        
        return matches[0].id
    
    def _truncate(self, text: str, max_length: int) -> str:
        """Truncate text to max_length, adding ... if needed."""
        if len(text) <= max_length:
            return text
        return text[:max_length-3] + "..."
    
    def _safe_console_text(self, text: str) -> str:
        """Convert text to console-safe encoding, replacing problematic characters."""
        if not text:
            return text
        return text.encode('ascii', errors='replace').decode('ascii')
    
    def _get_content_preview(self, content: str, max_length: int) -> str:
        """Get a preview of content, truncating at word boundaries."""
        if not content:
            return "(empty)"
        
        # Remove newlines and extra whitespace
        preview = " ".join(content.split())
        
        # Make console-safe
        preview = self._safe_console_text(preview)
        
        if len(preview) <= max_length:
            return preview
        
        # Truncate at word boundary
        truncated = preview[:max_length]
        last_space = truncated.rfind(' ')
        
        if last_space > max_length * 0.8:  # If we can find a reasonable word boundary
            return truncated[:last_space] + "..."
        else:
            return truncated + "..."
    
    def generate_reflection_prompt(self, entry_id: str, strategies: str = None) -> None:
        """Generate reflection prompt(s) for a journal entry."""
        try:
            # Resolve short ID to full ID
            full_id = self._resolve_short_id(entry_id)
            
            # Get the entry to show context
            entry = self.service.get_entry(full_id)
            
            # Parse strategies
            if strategies:
                strategy_list = [s.strip() for s in strategies.split(',')]
            else:
                strategy_list = ["empathetic_v1"]  # Default strategy
            
            # Show entry context
            print(f"Entry: {self._short_id(entry.id)} ({entry.created_at.strftime('%Y-%m-%d')})")
            print(f"Title: {self._safe_console_text(entry.title or '(no title)')}")
            print(f"Content: {self._get_content_preview(entry.content, 200)}")
            print()
            
            # Generate prompts for each strategy
            for strategy in strategy_list:
                try:
                    result = self.service.generate_reflection_prompt(full_id, strategy)
                    
                    print(f"Strategy: {strategy}")
                    print(f"Reflection Prompt: \"{self._safe_console_text(result['reflection_prompt'])}\"")
                    print()
                    
                except ValueError as e:
                    if "Unknown strategy" in str(e):
                        available = self.service.list_reflection_strategies()
                        print(f"Error: Unknown strategy '{strategy}'. Available: {', '.join(available)}", file=sys.stderr)
                    else:
                        print(f"Error: {e}", file=sys.stderr)
                    sys.exit(1)
                except Exception as e:
                    print(f"Error generating prompt for strategy '{strategy}': {e}", file=sys.stderr)
                    sys.exit(1)
            
        except EntryNotFoundError as e:
            print(f"Entry not found: {e}", file=sys.stderr)
            sys.exit(1)
        except ValueError as e:
            if "No AI client configured" in str(e):
                print("Error: AI features unavailable. Please ensure Ollama is running.", file=sys.stderr)
                print("Start Ollama with: ollama serve", file=sys.stderr)
            else:
                print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    
    def run_reflection_experiment(self, args):
        """Run experimental prompt testing - delegates to experimental module."""
        try:
            from src.experiments.reflection_prompts import PromptExperimenter
            
            experimenter = PromptExperimenter(self.service, self.service._reflection_service)
            experimenter.run_experiment(args)
            
        except ImportError as e:
            print(f"Error: Experimental module not available: {e}")
        except Exception as e:
            print(f"Error running experiment: {e}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="AI Journal - Command-line interface for managing journal entries",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s create --content "Today was a good day" --title "Daily reflection"
  %(prog)s list --limit 10
  %(prog)s show 550e8400
  %(prog)s edit 550e8400 --title "Updated title"
  %(prog)s import ./import_data
  %(prog)s prompt 550e8400 --strategies empathetic_v1,analytical_v1
  %(prog)s reflect-experiment --entries 550e8400,a2edc1b6
  %(prog)s reflect-experiment --recent 3
  %(prog)s reflect-experiment --all
        """
    )
    
    # Create subparsers for commands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    subparsers.required = True
    
    # Create command
    create_parser = subparsers.add_parser('create', help='Create a new journal entry')
    create_parser.add_argument('--content', help='Entry content')
    create_parser.add_argument('--title', help='Entry title')
    create_parser.add_argument('--tags', help='Comma-separated tags')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List journal entries')
    list_parser.add_argument('--limit', type=int, default=50, help='Maximum number of entries to show (default: 50)')
    
    # Show command
    show_parser = subparsers.add_parser('show', help='Show a specific journal entry')
    show_parser.add_argument('entry_id', help='Entry ID (full or shortened)')
    
    # Edit command
    edit_parser = subparsers.add_parser('edit', help='Edit an existing journal entry')
    edit_parser.add_argument('entry_id', help='Entry ID (full or shortened)')
    edit_parser.add_argument('--content', help='New content')
    edit_parser.add_argument('--title', help='New title')
    edit_parser.add_argument('--tags', help='New comma-separated tags')
    
    # Import command
    import_parser = subparsers.add_parser('import', help='Import journal entries from markdown files')
    import_parser.add_argument('directory', help='Directory containing markdown files')
    
    # Prompt command
    prompt_parser = subparsers.add_parser('prompt', help='Generate AI reflection prompts for a journal entry')
    prompt_parser.add_argument('entry_id', help='Entry ID (full or shortened)')
    prompt_parser.add_argument('--strategies', help='Comma-separated strategies (e.g., empathetic_v1,analytical_v1)')
    
    # Reflect experiment command
    experiment_parser = subparsers.add_parser('reflect-experiment', help='Experimental prompt testing tool')
    experiment_group = experiment_parser.add_mutually_exclusive_group(required=True)
    experiment_group.add_argument('--entries', help='Comma-separated entry IDs to experiment with')
    experiment_group.add_argument('--all', action='store_true', help='Run experiment on all journal entries')
    experiment_group.add_argument('--recent', type=int, metavar='N', help='Run experiment on N most recent entries')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Initialize CLI
    cli = JournalCLI()
    
    # Route to appropriate command
    if args.command == 'create':
        cli.create_entry(content=args.content, title=args.title, tags=args.tags)
    elif args.command == 'list':
        cli.list_entries(limit=args.limit)
    elif args.command == 'show':
        cli.show_entry(args.entry_id)
    elif args.command == 'edit':
        cli.edit_entry(args.entry_id, content=args.content, title=args.title, tags=args.tags)
    elif args.command == 'import':
        cli.import_entries(args.directory)
    elif args.command == 'prompt':
        cli.generate_reflection_prompt(args.entry_id, strategies=args.strategies)
    elif args.command == 'reflect-experiment':
        cli.run_reflection_experiment(args)


if __name__ == '__main__':
    main()
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**ai-journal** is an AI-powered journaling application that helps users develop consistent self-reflection practices that increase self-awareness, improve decision-making, and help them live life in ways that resonate deeply.

### Core User Stories
- Create and edit journal entries with AI analysis and prompts
- Chat interface with AI from journal entries or home page
- AI develops memory about user's life (people, challenges, goals, emotions, locations)
- AI identifies patterns and connections between thoughts over time
- Import existing digital journals

### Technical Strategy
- Local LLM usage via Ollama during development, Claude API as project advances
- Build unit tests and evals for LLM outputs
- Modular code architecture
- **Development approach**: Backend-first with CLI interface, then web API, finally web/mobile frontend

## Project Architecture

The core architecture centers around:

- **Data Layer**: 
  - **JournalEntry** (`src/models.py`): Core data model with metadata and helper methods
  - **StorageBackend** (`src/storage.py`): Abstract interface for storage backends  
  - **JSONStorage** (`src/json_storage.py`): File-based storage with search capabilities
  - **MarkdownImporter** (`src/markdown_importer.py`): Import existing markdown journals with date extraction from filenames
- **AI Integration**: 
  - **OllamaClient** (`src/ollama_client.py`): Primary interface to local LLM models via Ollama API, handling text generation, system prompts, and model management
- **Interface Layers** (development status):
  1. ✅ **CLI Interface** (`src/cli.py`): Complete command-line interface with argparse
  2. **Web API**: REST API using FastAPI for frontend integration (planned)
  3. **Web Frontend**: Browser-based interface for journal management (planned)
  4. **Mobile App**: Future mobile application support (planned)
- **Modular Design**: Built for extensibility with plans to support multiple LLM providers (starting with Ollama, expanding to Claude API)

## Development Commands

### CLI Usage
```bash
# Main entry point for journal operations
python journal.py <command> [options]

# Available commands:
python journal.py create [--content CONTENT] [--title TITLE] [--tags TAGS]
python journal.py list [--limit N]
python journal.py show <entry_id>
python journal.py edit <entry_id> [--content CONTENT] [--title TITLE] [--tags TAGS]
python journal.py import <directory>

# Examples:
python journal.py list --limit 10
python journal.py show a2edc1b6
python journal.py edit a2edc1b6 --title "Updated title"
python journal.py import import_data/
```

### Testing
```bash
# Run unit tests only (default behavior)
ai-journal-env/Scripts/python.exe -m pytest

# Run all tests including integration tests
ai-journal-env/Scripts/python.exe -m pytest -m ""

# Run only integration tests
ai-journal-env/Scripts/python.exe -m pytest -m "integration"

# Run only slow tests (integration tests)
ai-journal-env/Scripts/python.exe -m pytest -m "slow"

# Install development dependencies
pip install -e .[test]
```

### Test Organization
- **Unit tests**: Fast, mocked tests for all components (102 tests total)
  - `tests/test_models.py`: JournalEntry model tests (8 tests)
  - `tests/test_json_storage.py`: JSON storage backend tests (13 tests)
  - `tests/test_markdown_importer.py`: Markdown import utility tests (15 tests)
  - `tests/test_journal_service.py`: Business logic layer tests (25 tests)
  - `tests/test_cli.py`: Command-line interface tests (33 tests)
  - `tests/test_ollama_client_unit.py`: Ollama client unit tests (8 tests)
- **Integration tests**: Real API calls in `tests/test_ollama_client_integ.py`, marked as "slow" and skipped by default
- Integration tests require a running Ollama server and will skip gracefully if unavailable

### Project Configuration
- **Build system**: Modern setuptools with pyproject.toml
- **Testing framework**: pytest with custom markers for test categorization
- **Dependencies**: Core dependency on `requests` for HTTP communication

## Key Development Patterns

### Storage Backend Pattern
Use the `StorageBackend` abstract interface for all data persistence. The current `JSONStorage` implementation can be easily swapped for encrypted storage (SQLite + SQLCipher) when needed.

### Date Extraction Priority
The markdown importer follows this hierarchy for entry dates:
1. Date extracted from filename patterns (2024-01-15, 20240115, etc.)
2. Date from frontmatter `date` field
3. File modification timestamp as fallback

### Error Handling
The OllamaClient implements comprehensive error handling for HTTP requests and API communication. Follow this pattern when extending API functionality.

### Testing Strategy
- Unit tests use mocking to isolate functionality
- Integration tests verify real API behavior  
- Tests are organized with clear separation between fast unit tests and slower integration tests
- Use pytest markers to categorize tests appropriately
- Always write tests alongside new functionality

### Development Workflow
This project serves as a learning environment for product management skills and AI application development:

**Product Management Learning Goals**:
- Practice requirement clarification and scope management
- Understand technical trade-offs and their business implications
- Learn AI-specific product decisions (model selection, data pipelines, evaluation)
- Experience realistic PM-engineering collaboration patterns

**Collaborative Process**:
- **Planning before coding**: Always discuss architectural decisions and implementation plan before writing code
- **Technical alternatives**: Present multiple approaches with business trade-offs (performance vs. complexity, cost vs. accuracy)
- **Decision documentation**: Explain rationale for technical choices and their product implications
- **Iterative feedback**: Modify plans based on product requirements and technical constraints
- **AI considerations**: Highlight where current decisions will affect future AI feature integration

## Architectural Decisions

### Service Layer Pattern
The application uses a service layer (`JournalService`) to separate business logic from interface concerns:

**Decision**: Add `JournalService` class between CLI/web interfaces and data storage
**Rationale**: 
- Enables testing business logic independently of UI
- Prepares for future web API without code duplication
- Centralizes validation and business rules
- Makes storage backend swapping easier

**Implementation**: Service takes `StorageBackend` via dependency injection, returns domain objects (`JournalEntry`)

### CLI Design Pattern
**Decision**: Single CLI script with subcommands (`journal.py create`, `journal.py list`)
**Rationale**:
- Standard Unix/Python CLI pattern
- Extensible architecture for adding new commands
- Familiar user experience
- Single entry point simplifies distribution

### Layered Architecture
```
CLI Interface → Journal Service → Storage Backend → Data Files
     ↓               ↓                 ↓              ↓
User Commands → Business Logic → Data Operations → JSON/SQLite
```

**Separation of Concerns**:
- **CLI** (`src/cli.py`): User interaction, argument parsing, output formatting
- **Service** (`src/journal_service.py`): Business logic, validation, orchestration
- **Storage** (`src/json_storage.py`): Data persistence, CRUD operations, search
- **Models** (`src/models.py`): Data structures and domain logic

### CLI Design Pattern
**Decision**: Single script with argparse subcommands (`python journal.py <command>`)
**Benefits**:
- Standard Unix/Python CLI pattern familiar to users
- Built-in help generation and argument validation
- Extensible architecture for adding new commands
- Clean entry point via `journal.py` wrapper script

**Key Features**:
- **Short ID support**: User-friendly 8-character identifiers (e.g., `a2edc1b6`)
- **Table output**: Formatted display with content previews for list command
- **Error handling**: Graceful failures with helpful error messages
- **Encoding safety**: Handles unicode/emoji content without crashes

## Code Principles
- Always use descriptive variable names
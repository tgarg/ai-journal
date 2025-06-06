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
- **Interface Layers** (planned development order):
  1. **CLI Interface**: Command-line tools for journal operations
  2. **Web API**: REST API using FastAPI for frontend integration  
  3. **Web Frontend**: Browser-based interface for journal management
  4. **Mobile App**: Future mobile application support
- **Modular Design**: Built for extensibility with plans to support multiple LLM providers (starting with Ollama, expanding to Claude API)

## Development Commands

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
- **Unit tests**: Fast, mocked tests for all components
  - `tests/test_models.py`: JournalEntry model tests
  - `tests/test_json_storage.py`: JSON storage backend tests
  - `tests/test_markdown_importer.py`: Markdown import utility tests
  - `tests/test_ollama_client_unit.py`: Ollama client unit tests
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

## Code Principles
- Always use descriptive variable names
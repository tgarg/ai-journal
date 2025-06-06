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
- Local LLM usage via Ollama during development, Gemini 2.5 Flash API for production
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
  - **Experiments Framework** (`src/experiments/`): A/B testing infrastructure for AI prompt optimization and feature evaluation
- **Interface Layers** (development status):
  1. ✅ **CLI Interface** (`src/cli.py`): Complete command-line interface with argparse
  2. **REST API**: FastAPI layer for mobile and web interfaces (in development)
  3. **Mobile App**: React Native app for on-the-go journaling (Phase 2 priority)
  4. **Web Frontend**: Browser-based interface for journal management (planned)
- **Modular Design**: Built for extensibility with plans to support multiple LLM providers (starting with Ollama, expanding to Gemini API)

## Development Commands

### API Development (Primary Interface)
```bash
# Start FastAPI development server
uvicorn src.api.main:app --reload

# API endpoints will be available at http://localhost:8000
# API documentation at http://localhost:8000/docs
```

### CLI Usage (Development/Testing)
```bash
# Basic journal operations for development
python journal.py create [--content CONTENT] [--title TITLE] [--tags TAGS]
python journal.py list [--limit N]
python journal.py show <entry_id>
python journal.py import <directory>
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
- **Unit tests**: Fast, mocked tests for all components
  - `tests/test_models.py`: JournalEntry model tests
  - `tests/test_json_storage.py`: JSON storage backend tests
  - `tests/test_markdown_importer.py`: Markdown import utility tests
  - `tests/test_journal_service.py`: Business logic layer tests
  - `tests/test_cli.py`: Command-line interface tests
  - `tests/test_ollama_client.py`: Ollama client unit tests
- **Integration tests**: Real API calls marked as "slow" and "integration", skipped by default
  - `tests/test_ollama_client.py`: Ollama client integration tests
  - `tests/test_reflection.py`: Reflection service integration tests
- Integration tests require a running LLM service and will skip gracefully if unavailable

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

### API-First Architecture
**Decision**: REST API as primary interface with CLI as development tool
**Rationale**:
- Enables mobile app development
- Supports multiple client interfaces (web, mobile, CLI)
- Standard HTTP/JSON for cross-platform compatibility
- Scalable for future features

### Layered Architecture
```
API/CLI Interface → Journal Service → Storage Backend → Data Files
        ↓               ↓                 ↓              ↓
HTTP/Commands → Business Logic → Data Operations → JSON/SQLite
```

**Separation of Concerns**:
- **API** (`src/api/`): HTTP endpoints, request/response handling, authentication
- **CLI** (`src/cli.py`): Development interface, argument parsing, local operations
- **Service** (`src/journal_service.py`): Business logic, validation, orchestration
- **Storage** (`src/json_storage.py`): Data persistence, CRUD operations, search
- **Models** (`src/models.py`): Data structures and domain logic

## Development Roadmap

### Phase 1: API Foundation (Current Focus)
**Goal**: Build REST API layer with hybrid LLM support for mobile app
- FastAPI server setup with existing service layer integration
- Journal CRUD endpoints (create, read, update, delete entries)
- LLM provider abstraction (OllamaProvider + GeminiProvider)
- Basic authentication system
- Chat/conversation API endpoints for AI interactions
- Implement the conversational loop via API
- A/B testing framework integration for prompt experiments
- API documentation, testing, and cloud deployment

### Phase 2: Mobile MVP
**Goal**: Launch mobile app for on-the-go journaling with AI
- React Native app with voice-to-text capture and entry creation
- Basic journal browsing and viewing with API integration
- Connect mobile app to conversation endpoints
- Implement "go deeper" prompt flow on mobile
- Test effectiveness of AI conversation loop in real usage

### Phase 3: Intelligence Layer
**Goal**: Add RAG and Knowledge Graph for context-aware AI
- Vector embeddings and semantic search for journal entries
- Enhance API conversation endpoints with retrieved context
- A/B test RAG vs non-RAG prompt effectiveness
- Entity extraction from journal entries
- Pattern detection and relationship mapping
- Integration with conversation APIs

### Key Architectural Changes
- **API-first approach**: REST API becomes primary interface, CLI becomes thin wrapper
- **LLM Provider Abstraction**: Support both Ollama (development) and Gemini 2.5 Flash (production/mobile)
- **Mobile-first development**: Prioritize mobile experience for daily usage and real-world testing

## Code Principles
- Always use descriptive variable names
- **No emojis in code**: Do not use Unicode emojis in print statements, comments, or any code output to avoid Windows console encoding issues (UnicodeEncodeError with cp1252). Use plain text instead.
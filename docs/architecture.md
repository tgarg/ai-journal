# Architecture Documentation

## System Architecture

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

## Key Design Decisions

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

## Implementation Details

### Layered Architecture
```
API/CLI Interface → Journal Service → Storage Backend → Data Files
        ↓               ↓                 ↓              ↓
HTTP/Commands → Business Logic → Data Operations → JSON/SQLite
```

### Separation of Concerns
- **API** (`src/api/`): HTTP endpoints, request/response handling, authentication
- **CLI** (`src/cli.py`): Development interface, argument parsing, local operations
- **Service** (`src/journal_service.py`): Business logic, validation, orchestration
- **Storage** (`src/json_storage.py`): Data persistence, CRUD operations, search
- **Models** (`src/models.py`): Data structures and domain logic

## Technical Strategy

### LLM Integration Strategy
- **Development**: Local LLM usage via Ollama for fast iteration
- **Production**: Gemini 2.5 Flash API for reliability and performance
- **Testing**: Build unit tests and evals for LLM outputs
- **Architecture**: Modular code architecture with clear separation of concerns

### Development Approach
Backend-first with CLI interface, then web API, finally web/mobile frontend

## Development Patterns

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
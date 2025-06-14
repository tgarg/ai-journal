# Development Guide

## Development Workflow

This project serves as a learning environment for product management skills and AI application development:

### Product Management Learning Goals
- Practice requirement clarification and scope management
- Understand technical trade-offs and their business implications
- Learn AI-specific product decisions (model selection, data pipelines, evaluation)
- Experience realistic PM-engineering collaboration patterns

### Collaborative Process
- **Planning before coding**: Always discuss architectural decisions and implementation plan before writing code
- **Technical alternatives**: Present multiple approaches with business trade-offs (performance vs. complexity, cost vs. accuracy)
- **Decision documentation**: Explain rationale for technical choices and their product implications
- **Iterative feedback**: Modify plans based on product requirements and technical constraints
- **AI considerations**: Highlight where current decisions will affect future AI feature integration

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

### Testing Commands
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

## Test Organization

### Unit Tests
Fast, mocked tests for all components:
- `tests/test_models.py`: JournalEntry model tests
- `tests/test_json_storage.py`: JSON storage backend tests
- `tests/test_markdown_importer.py`: Markdown import utility tests
- `tests/test_journal_service.py`: Business logic layer tests
- `tests/test_cli.py`: Command-line interface tests
- `tests/test_ollama_client.py`: Ollama client unit tests

### Integration Tests
Real API calls marked as "slow" and "integration", skipped by default:
- `tests/test_ollama_client.py`: Ollama client integration tests
- `tests/test_reflection.py`: Reflection service integration tests

Integration tests require a running LLM service and will skip gracefully if unavailable.

## Project Configuration

- **Build system**: Modern setuptools with pyproject.toml
- **Testing framework**: pytest with custom markers for test categorization
- **Dependencies**: Core dependency on `requests` for HTTP communication

## Development Roadmap

### Phase 1: API Foundation (Current Focus)
**Goal**: Build REST API layer with hybrid LLM support for mobile app

#### Tech Stack Decision
- **FastAPI**: Async performance, auto OpenAPI docs, mobile-first JSON APIs
- **Pydantic**: Built-in request/response validation, type safety
- **Uvicorn**: ASGI server with hot reload and production capabilities

#### Implementation Plan (feature/api-foundation branch)

**Phase 1a: Setup & Foundation**
1. Create feature branch `feature/api-foundation`
2. Update pyproject.toml dependencies (FastAPI, Uvicorn, Pydantic)
3. Install dependencies with `pip install -e .[test]`
4. Create `src/api/` directory structure
5. Create basic `src/api/main.py` with FastAPI app
6. Test server runs with `uvicorn src.api.main:app --reload`

**Phase 1b: Core API Implementation**
7. `src/api/models.py`: Pydantic request/response schemas
8. `src/api/dependencies.py`: Dependency injection for JournalService
9. `src/api/exceptions.py`: HTTP exception handlers
10. Journal CRUD endpoints:
    - `POST /entries`: Create journal entry
    - `GET /entries`: List entries with pagination
    - `GET /entries/{entry_id}`: Get specific entry
    - `PUT /entries/{entry_id}`: Update entry
11. AI reflection endpoints:
    - `POST /entries/{entry_id}/reflect`: Generate reflection prompt
    - `GET /reflection/strategies`: List available strategies
12. `GET /health`: Service health check

**Phase 1c: Testing & Documentation**
13. Integration tests for API endpoints
14. Error handling validation
15. API documentation review at `/docs`

**Success Criteria**
- ✅ FastAPI server runs successfully
- ✅ All Journal CRUD operations accessible via REST API
- ✅ Auto-generated API docs available
- ✅ Proper HTTP error handling
- ✅ Integration tests passing

**Future Phase 1 Work**
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
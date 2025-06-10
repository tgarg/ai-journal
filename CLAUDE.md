# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Project Context

**ai-journal** is an AI-powered journaling application for voice-to-text journaling with AI reflection prompts. Python backend with FastAPI REST API, targeting React Native mobile app.

**Tech Stack**: Python, FastAPI, Ollama/Gemini LLMs, pytest, JSON storage
**Current Phase**: Building REST API layer (Phase 1 of 3)

## Commands

### Development
```bash
# Run tests (default: unit tests only)
ai-journal-env/Scripts/python.exe -m pytest

# Run all tests including integration
ai-journal-env/Scripts/python.exe -m pytest -m ""

# Start API server (when implemented)
uvicorn src.api.main:app --reload

# CLI operations
python journal.py create/list/show/import
```

### Installation
```bash
pip install -e .[test]
```

## Development Approach

- Think critically about design patterns, edge cases, and maintainability
- Prioritize security: prevent injection attacks and excessive privileges
- Break complex features into smaller, testable components
- Ask clarifying questions rather than making assumptions

## Code Style

- Use descriptive variable names
- No emojis in code (Windows encoding issues)
- 2-space indentation for consistency
- Use abstract `StorageBackend` interface for persistence
- Follow OllamaClient pattern for HTTP/API error handling
- Always write tests alongside new functionality
- Follow SOLID principles and favor composition over inheritance
- Fail fast: detect problems early in development
- Write meaningful logs with appropriate levels
- Use dependency injection for better testability

## Security Priorities

- Validate all API inputs and sanitize data
- Follow principle of least privilege
- Implement proper error handling without exposing internals

## Architecture Essentials

### Core Structure
```
API/CLI Interface → Journal Service → Storage Backend → Data Files
        ↓               ↓                 ↓              ↓
HTTP/Commands → Business Logic → Data Operations → JSON/SQLite
```

### Key Components
- **JournalService** (`src/journal_service.py`): Business logic layer
- **StorageBackend** (`src/storage.py`): Abstract storage interface
- **OllamaClient** (`src/ollama_client.py`): LLM integration
- **Models** (`src/models.py`): JournalEntry dataclass

### Design Decisions
- **API-First**: REST API as primary interface, CLI as development tool
- **Service Layer**: Separates business logic from interface concerns
- **LLM Strategy**: Ollama (dev) → Gemini 2.5 Flash (prod)

## User Journey (Mobile Focus)

**Core Flow**: Open app → Record voice → Review text → Tap "Go Deeper" → AI prompts → Voice response → Save conversation

**Key Features**:
- Voice-to-text journaling with pause/resume
- AI "Go Deeper" prompts based on entry content
- Conversational AI flow with clear visual distinction
- Offline capability with sync

## Project-Specific Notes

- Test organization: unit tests (fast) vs integration tests (real API calls)
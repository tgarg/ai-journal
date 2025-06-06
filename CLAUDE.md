# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Architecture

**ai-journal** is an AI-powered journaling application that helps users develop consistent self-reflection practices. The core architecture centers around:

- **OllamaClient** (`src/ollama_client.py`): Primary interface to local LLM models via Ollama API, handling text generation, system prompts, and model management
- **Modular Design**: Built for extensibility with plans to support multiple LLM providers (starting with Ollama, expanding to Claude API)

## Development Commands

### Testing
```bash
# Run unit tests only (default behavior)
pytest

# Run all tests including integration tests
pytest -m ""

# Run only integration tests
pytest -m "integration"

# Run only slow tests (integration tests)
pytest -m "slow"

# Install development dependencies
pip install -e .[test]
```

### Test Organization
- **Unit tests**: Fast, mocked tests in `tests/test_ollama_client_unit.py`
- **Integration tests**: Real API calls in `tests/test_ollama_client_integ.py`, marked as "slow" and skipped by default
- Integration tests require a running Ollama server and will skip gracefully if unavailable

### Project Configuration
- **Build system**: Modern setuptools with pyproject.toml
- **Testing framework**: pytest with custom markers for test categorization
- **Dependencies**: Core dependency on `requests` for HTTP communication

## Key Development Patterns

### Error Handling
The OllamaClient implements comprehensive error handling for HTTP requests and API communication. Follow this pattern when extending API functionality.

### Testing Strategy
- Unit tests use mocking to isolate functionality
- Integration tests verify real API behavior
- Tests are organized with clear separation between fast unit tests and slower integration tests
- Use pytest markers to categorize tests appropriately
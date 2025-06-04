import pytest
import requests
import warnings
from src.ollama_client import OllamaClient

def is_ollama_running() -> bool:
    """Check if Ollama server is running and accessible."""
    try:
        response = requests.get("http://localhost:11434/api/tags")
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        return False

@pytest.fixture(autouse=True)
def check_ollama_status():
    """Automatically check Ollama status before each test."""
    if not is_ollama_running():
        warnings.warn(
            "⚠️ Ollama server is not running. Tests will be skipped. "
            "Please start Ollama to run the full test suite.",
            category=UserWarning
        )
        pytest.skip("Ollama server is not running")

@pytest.fixture
def client():
    return OllamaClient()

def test_client_initialization():
    # Test default initialization
    client = OllamaClient()
    assert client.base_url == "http://localhost:11434"
    assert client.model == "mistral"
    
    # Test custom initialization
    custom_url = "http://custom:11434"
    custom_model = "llama2"
    client = OllamaClient(base_url=custom_url, model=custom_model)
    assert client.base_url == custom_url
    assert client.model == custom_model

def test_generate_response(client):
    # Test basic generation
    response = client.generate("Hello, how are you?")
    assert isinstance(response, str)
    assert len(response) > 0
    
    # Test with system prompt
    system_prompt = "You are a helpful assistant that speaks in a friendly tone."
    response = client.generate(
        "What's the weather like?",
        system=system_prompt
    )
    assert isinstance(response, str)
    assert len(response) > 0
    
    # Test with temperature
    response = client.generate(
        "Tell me a short story",
        temperature=0.7
    )
    assert isinstance(response, str)
    assert len(response) > 0

def test_list_models(client):
    models = client.list_models()
    assert isinstance(models, dict)
    assert "models" in models
    # Verify the response structure
    assert isinstance(models["models"], list)
    if len(models["models"]) > 0:
        assert "name" in models["models"][0] 
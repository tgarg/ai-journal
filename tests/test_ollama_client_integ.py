import pytest
import requests
import warnings
from ollama_client import OllamaClient

def is_ollama_running() -> bool:
    """Check if Ollama server is running and accessible."""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        return response.status_code == 200
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        return False

class TestOllamaClientIntegration:
    """Integration tests that actually call Ollama - slow but thorough."""
    
    @pytest.fixture(autouse=True)
    def check_ollama_status(self):
        """Automatically check Ollama status before each integration test."""
        if not is_ollama_running():
            warnings.warn(
                "⚠️ Ollama server is not running. Integration tests will be skipped. "
                "Please start Ollama to run the full test suite.",
                category=UserWarning
            )
            pytest.skip("Ollama server is not running")

    def test_generate_response_integration(self):
        """Integration test - actually calls Ollama API."""
        client = OllamaClient()
        
        # Test basic generation
        response = client.generate("Say 'Hello World' and nothing else.")
        assert isinstance(response, str)
        assert len(response.strip()) > 0
        
    def test_list_models_integration(self):
        """Integration test for listing models."""
        client = OllamaClient()
        models = client.list_models()
        
        assert isinstance(models, dict)
        assert "models" in models
        assert isinstance(models["models"], list)
        if len(models["models"]) > 0:
            assert "name" in models["models"][0]
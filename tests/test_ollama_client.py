import pytest
import requests
import warnings
from unittest.mock import Mock, patch
from ollama_client import OllamaClient

@pytest.fixture
def client():
    return OllamaClient()

@pytest.fixture
def mock_response():
    """Mock response object for requests."""
    mock = Mock()
    mock.status_code = 200
    mock.raise_for_status.return_value = None
    return mock

def is_ollama_running() -> bool:
    """Check if Ollama server is running and accessible."""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        return response.status_code == 200
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        return False

class TestOllamaClientUnit:
    """Unit tests that mock the HTTP requests - fast and reliable."""
    
    def test_client_initialization(self):
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
        
        # Test URL normalization (removes trailing slash)
        client = OllamaClient(base_url="http://localhost:11434/")
        assert client.base_url == "http://localhost:11434"

    @patch('requests.post')
    def test_generate_basic(self, mock_post, mock_response):
        """Test basic generation with mocked response."""
        mock_response.json.return_value = {"response": "Hello! I'm doing well, thank you."}
        mock_post.return_value = mock_response
        
        client = OllamaClient()
        response = client.generate("Hello, how are you?")
        
        # Verify the response
        assert response == "Hello! I'm doing well, thank you."
        
        # Verify the API call was made correctly
        mock_post.assert_called_once_with(
            "http://localhost:11434/api/generate",
            json={
                "model": "mistral",
                "prompt": "Hello, how are you?",
                "stream": False
            }
        )

    @patch('requests.post')
    def test_generate_with_system_prompt(self, mock_post, mock_response):
        """Test generation with system prompt."""
        mock_response.json.return_value = {"response": "Friendly response here!"}
        mock_post.return_value = mock_response
        
        client = OllamaClient()
        system_prompt = "You are a helpful assistant that speaks in a friendly tone."
        response = client.generate("What's the weather like?", system=system_prompt)
        
        assert response == "Friendly response here!"
        mock_post.assert_called_once_with(
            "http://localhost:11434/api/generate",
            json={
                "model": "mistral",
                "prompt": "What's the weather like?",
                "system": system_prompt,
                "stream": False
            }
        )

    @patch('requests.post')
    def test_generate_with_temperature(self, mock_post, mock_response):
        """Test generation with temperature parameter."""
        mock_response.json.return_value = {"response": "Creative story here!"}
        mock_post.return_value = mock_response
        
        client = OllamaClient()
        response = client.generate("Tell me a short story", temperature=0.7)
        
        assert response == "Creative story here!"
        mock_post.assert_called_once_with(
            "http://localhost:11434/api/generate",
            json={
                "model": "mistral",
                "prompt": "Tell me a short story",
                "options": {"temperature": 0.7},
                "stream": False
            }
        )

    @patch('requests.post')
    def test_generate_with_all_parameters(self, mock_post, mock_response):
        """Test generation with all optional parameters."""
        mock_response.json.return_value = {"response": "Complete response!"}
        mock_post.return_value = mock_response
        
        client = OllamaClient()
        response = client.generate(
            "Tell me about AI",
            system="You are an AI expert",
            temperature=0.5
        )
        
        assert response == "Complete response!"
        mock_post.assert_called_once_with(
            "http://localhost:11434/api/generate",
            json={
                "model": "mistral",
                "prompt": "Tell me about AI",
                "system": "You are an AI expert",
                "options": {"temperature": 0.5},
                "stream": False
            }
        )

    @patch('requests.get')
    def test_list_models(self, mock_get, mock_response):
        """Test listing available models."""
        expected_models = {
            "models": [
                {"name": "mistral:latest", "size": 4109805568},
                {"name": "llama2:latest", "size": 3825819519}
            ]
        }
        mock_response.json.return_value = expected_models
        mock_get.return_value = mock_response
        
        client = OllamaClient()
        models = client.list_models()
        
        assert models == expected_models
        mock_get.assert_called_once_with("http://localhost:11434/api/tags")

    @patch('requests.post')
    def test_generate_http_error(self, mock_post):
        """Test that HTTP errors are properly raised."""
        mock_post.return_value.raise_for_status.side_effect = requests.exceptions.HTTPError("API Error")
        
        client = OllamaClient()
        with pytest.raises(requests.exceptions.HTTPError):
            client.generate("Hello")

    @patch('requests.get')
    def test_list_models_http_error(self, mock_get):
        """Test that HTTP errors are properly raised for list_models."""
        mock_get.return_value.raise_for_status.side_effect = requests.exceptions.HTTPError("API Error")
        
        client = OllamaClient()
        with pytest.raises(requests.exceptions.HTTPError):
            client.list_models()

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

    @pytest.mark.integration
    @pytest.mark.slow
    def test_generate_response_integration(self):
        """Integration test - actually calls Ollama API."""
        client = OllamaClient()
        
        # Test basic generation
        response = client.generate("Say 'Hello World' and nothing else.")
        assert isinstance(response, str)
        assert len(response.strip()) > 0
        
    @pytest.mark.integration
    @pytest.mark.slow
    def test_list_models_integration(self):
        """Integration test for listing models."""
        client = OllamaClient()
        models = client.list_models()
        
        assert isinstance(models, dict)
        assert "models" in models
        assert isinstance(models["models"], list)
        if len(models["models"]) > 0:
            assert "name" in models["models"][0]
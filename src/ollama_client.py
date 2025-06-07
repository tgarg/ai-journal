import requests
from typing import Optional, Dict, Any

class OllamaClient:
    """Client for interacting with the Ollama API."""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "mistral"):
        """Initialize the Ollama client.
        
        Args:
            base_url: The base URL for the Ollama API. Defaults to localhost.
            model: The model to use for generation. Defaults to mistral.
        """
        self.base_url = base_url.rstrip('/')
        self.model = model

    def generate(self, 
                prompt: str, 
                system: Optional[str] = None,
                temperature: Optional[float] = None) -> str:
        """Generate a response from the Ollama model.
        
        Args:
            prompt: The input prompt for the model
            system: Optional system prompt to guide the model's behavior
            temperature: Optional temperature parameter (0.0 to 1.0)
            
        Returns:
            The model's response as a string
            
        Raises:
            requests.exceptions.RequestException: If the API request fails
        """
        payload: Dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        
        if system:
            payload["system"] = system
        if temperature is not None:
            payload["options"] = {"temperature": temperature}
            
        response = requests.post(
            f"{self.base_url}/api/generate",
            json=payload
        )
        response.raise_for_status()
        return response.json()["response"]
    
    def list_models(self) -> Dict[str, Any]:
        """List all available models.
        
        Returns:
            Dict containing the list of available models
            
        Raises:
            requests.exceptions.RequestException: If the API request fails
        """
        response = requests.get(f"{self.base_url}/api/tags")
        response.raise_for_status()
        return response.json() 
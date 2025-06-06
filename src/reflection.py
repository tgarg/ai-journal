from datetime import datetime
from typing import Dict, Any
from .ollama_client import OllamaClient


class ReflectionService:
    """Service for generating AI-powered reflection prompts from journal entries."""
    
    SYSTEM_PROMPT = """You are an expert journaling coach who helps people develop deeper self-awareness through thoughtful reflection. You generate questions that are:
- Empathetic and non-judgmental
- Specific to the person's situation
- Designed to uncover insights and patterns
- Encouraging of emotional exploration

Generate exactly one thoughtful follow-up question based on the journal entry provided."""

    GENERATORS = {
        "empathetic_v1": "Here is a journal entry: '{content}'\n\nGenerate a single, compassionate follow-up question that would help this person explore their emotions and feelings more deeply. Make it specific to their situation.",
        
        "analytical_v1": "Here is a journal entry: '{content}'\n\nGenerate a single, thoughtful question that helps this person identify patterns, root causes, or logical connections in their experience.",
        
        "socratic_v1": "Here is a journal entry: '{content}'\n\nGenerate a single, thought-provoking question that helps this person examine their assumptions or see their situation from a new perspective."
    }
    
    def __init__(self, ollama_client: OllamaClient):
        """Initialize the reflection service with an Ollama client."""
        self.ollama_client = ollama_client
        
    def generate_reflection_prompt(self, 
                                 entry_content: str, 
                                 strategy: str = "empathetic_v1") -> Dict[str, Any]:
        """Generate a reflection prompt for the given journal entry.
        
        Args:
            entry_content: The journal entry content to generate a prompt for
            strategy: The prompt generation strategy to use
            
        Returns:
            Dict containing the generated prompt and metadata
            
        Raises:
            ValueError: If strategy is not recognized
            requests.exceptions.RequestException: If Ollama API fails
        """
        if strategy not in self.GENERATORS:
            available_strategies = list(self.GENERATORS.keys())
            raise ValueError(f"Unknown strategy '{strategy}'. Available: {available_strategies}")
            
        generation_prompt = self.GENERATORS[strategy].format(content=entry_content)
        
        reflection_prompt = self.ollama_client.generate(
            prompt=generation_prompt,
            system=self.SYSTEM_PROMPT
        )
        
        return {
            "reflection_prompt": reflection_prompt.strip(),
            "strategy_used": strategy,
            "timestamp": datetime.now(),
            "entry_preview": entry_content[:100] + "..." if len(entry_content) > 100 else entry_content
        }
    
    def list_strategies(self) -> list[str]:
        """Return list of available prompt generation strategies."""
        return list(self.GENERATORS.keys())
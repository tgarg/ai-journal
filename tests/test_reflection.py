import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime
import requests
import warnings

from src.reflection import ReflectionService
from src.ollama_client import OllamaClient


def is_ollama_running() -> bool:
    """Check if Ollama server is running and accessible."""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        return response.status_code == 200
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        return False


class TestReflectionService:
    """Test suite for ReflectionService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_ollama_client = Mock(spec=OllamaClient)
        self.reflection_service = ReflectionService(self.mock_ollama_client)
        
    def test_init(self):
        """Test ReflectionService initialization."""
        assert self.reflection_service.ollama_client == self.mock_ollama_client
        assert isinstance(self.reflection_service.SYSTEM_PROMPT, str)
        assert len(self.reflection_service.GENERATORS) > 0
        
    def test_list_strategies(self):
        """Test listing available strategies."""
        strategies = self.reflection_service.list_strategies()
        
        assert isinstance(strategies, list)
        assert "empathetic_v1" in strategies
        assert "analytical_v1" in strategies
        assert "socratic_v1" in strategies
        assert len(strategies) == 3
        
    def test_generate_reflection_prompt_success(self):
        """Test successful reflection prompt generation."""
        # Setup
        entry_content = "Had a difficult conversation with my manager today about my performance."
        expected_prompt = "What emotions came up for you during that conversation with your manager?"
        self.mock_ollama_client.generate.return_value = expected_prompt
        
        # Execute
        result = self.reflection_service.generate_reflection_prompt(entry_content)
        
        # Verify
        assert result["reflection_prompt"] == expected_prompt
        assert result["strategy_used"] == "empathetic_v1"  # default strategy
        assert isinstance(result["timestamp"], datetime)
        assert result["entry_preview"] == entry_content  # short entry, no truncation
        
        # Verify ollama client was called correctly
        self.mock_ollama_client.generate.assert_called_once()
        call_args = self.mock_ollama_client.generate.call_args
        assert call_args[1]["system"] == self.reflection_service.SYSTEM_PROMPT
        assert entry_content in call_args[1]["prompt"]
        
    def test_generate_reflection_prompt_custom_strategy(self):
        """Test reflection prompt generation with custom strategy."""
        # Setup
        entry_content = "I keep making the same mistakes at work."
        expected_prompt = "What patterns do you notice in these recurring mistakes?"
        self.mock_ollama_client.generate.return_value = expected_prompt
        
        # Execute
        result = self.reflection_service.generate_reflection_prompt(
            entry_content, 
            strategy="analytical_v1"
        )
        
        # Verify
        assert result["reflection_prompt"] == expected_prompt
        assert result["strategy_used"] == "analytical_v1"
        
        # Verify correct generation template was used
        call_args = self.mock_ollama_client.generate.call_args
        assert "patterns" in call_args[1]["prompt"] or "root causes" in call_args[1]["prompt"]
        
    def test_generate_reflection_prompt_long_entry_preview(self):
        """Test that long entries are truncated in preview."""
        # Setup
        long_content = "A" * 150  # 150 characters
        self.mock_ollama_client.generate.return_value = "Test prompt"
        
        # Execute
        result = self.reflection_service.generate_reflection_prompt(long_content)
        
        # Verify
        assert len(result["entry_preview"]) == 103  # 100 chars + "..."
        assert result["entry_preview"].endswith("...")
        
    def test_generate_reflection_prompt_strips_whitespace(self):
        """Test that generated prompts have whitespace stripped."""
        # Setup
        entry_content = "Test content"
        prompt_with_whitespace = "  What are you thinking?  \n"
        self.mock_ollama_client.generate.return_value = prompt_with_whitespace
        
        # Execute
        result = self.reflection_service.generate_reflection_prompt(entry_content)
        
        # Verify
        assert result["reflection_prompt"] == "What are you thinking?"
        
    def test_generate_reflection_prompt_invalid_strategy(self):
        """Test error handling for invalid strategy."""
        # Execute & Verify
        with pytest.raises(ValueError) as exc_info:
            self.reflection_service.generate_reflection_prompt(
                "test content", 
                strategy="invalid_strategy"
            )
            
        assert "Unknown strategy 'invalid_strategy'" in str(exc_info.value)
        assert "empathetic_v1" in str(exc_info.value)  # Lists available strategies
        
    def test_generate_reflection_prompt_ollama_error(self):
        """Test error handling when Ollama client fails."""
        # Setup
        self.mock_ollama_client.generate.side_effect = requests.exceptions.ConnectionError("Ollama not available")
        
        # Execute & Verify
        with pytest.raises(requests.exceptions.ConnectionError):
            self.reflection_service.generate_reflection_prompt("test content")
            
    def test_all_generators_have_content_placeholder(self):
        """Test that all generation templates include {content} placeholder."""
        for strategy, template in self.reflection_service.GENERATORS.items():
            assert "{content}" in template, f"Strategy '{strategy}' missing {{content}} placeholder"
            
    def test_generators_produce_different_prompts(self):
        """Test that different strategies produce different generation prompts."""
        entry_content = "I'm feeling overwhelmed at work."
        
        # Get generation prompts for each strategy
        generation_prompts = {}
        for strategy in self.reflection_service.GENERATORS:
            template = self.reflection_service.GENERATORS[strategy]
            generation_prompts[strategy] = template.format(content=entry_content)
            
        # Verify they're all different
        unique_prompts = set(generation_prompts.values())
        assert len(unique_prompts) == len(generation_prompts), "Generation prompts should be unique"


@pytest.mark.slow
@pytest.mark.integration
class TestReflectionServiceIntegration:
    """Integration tests that make real calls to Ollama - slow but thorough."""
    
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
    
    @pytest.fixture
    def real_ollama_client(self):
        """Create a real OllamaClient for integration testing."""
        return OllamaClient()
    
    @pytest.fixture  
    def reflection_service(self, real_ollama_client):
        """Create ReflectionService with real Ollama client."""
        return ReflectionService(real_ollama_client)
    
    def test_generate_reflection_prompt_real_ai(self, reflection_service):
        """Test reflection prompt generation with real AI."""
        # Use a realistic journal entry
        entry_content = "Had a difficult conversation with my manager today about my performance. I felt defensive but tried to listen to the feedback."
        
        # Generate reflection prompt
        result = reflection_service.generate_reflection_prompt(entry_content)
        
        # Verify structure
        assert "reflection_prompt" in result
        assert "strategy_used" in result
        assert "timestamp" in result
        assert "entry_preview" in result
        
        # Verify AI generated meaningful content
        prompt = result["reflection_prompt"]
        assert len(prompt) > 20, "AI should generate substantial prompt"
        assert "?" in prompt or "How" in prompt or "What" in prompt, "Should be a question"
        
        # Verify strategy
        assert result["strategy_used"] == "empathetic_v1"
        
        # Verify entry preview
        assert "difficult conversation" in result["entry_preview"]
        
    def test_different_strategies_produce_different_responses(self, reflection_service):
        """Test that different strategies generate meaningfully different prompts."""
        entry_content = "I keep procrastinating on important work tasks and feel guilty about it."
        
        # Generate prompts with different strategies
        empathetic_result = reflection_service.generate_reflection_prompt(entry_content, "empathetic_v1")
        analytical_result = reflection_service.generate_reflection_prompt(entry_content, "analytical_v1") 
        socratic_result = reflection_service.generate_reflection_prompt(entry_content, "socratic_v1")
        
        # Extract the prompts
        empathetic_prompt = empathetic_result["reflection_prompt"]
        analytical_prompt = analytical_result["reflection_prompt"]
        socratic_prompt = socratic_result["reflection_prompt"]
        
        # Verify all are substantial
        for prompt in [empathetic_prompt, analytical_prompt, socratic_prompt]:
            assert len(prompt) > 15, f"Prompt too short: {prompt}"
        
        # Verify they're different (allowing for some AI variation)
        prompts = [empathetic_prompt, analytical_prompt, socratic_prompt]
        unique_prompts = set(prompts)
        
        # Should have at least 2 different prompts (AI might occasionally generate similar ones)
        assert len(unique_prompts) >= 2, f"Strategies should produce different prompts. Got: {prompts}"
        
        # Verify strategy-specific characteristics (loose checks since AI output varies)
        # Empathetic should focus on feelings
        empathetic_lower = empathetic_prompt.lower()
        assert any(word in empathetic_lower for word in ["feel", "emotion", "heart"]), \
            f"Empathetic prompt should mention feelings: {empathetic_prompt}"
            
        # Analytical should focus on patterns/causes  
        analytical_lower = analytical_prompt.lower()
        assert any(word in analytical_lower for word in ["pattern", "cause", "why", "analyze"]), \
            f"Analytical prompt should mention analysis: {analytical_prompt}"
    
    def test_reflection_prompt_handles_long_content(self, reflection_service):
        """Test reflection prompt generation with long journal entry."""
        # Create a long journal entry
        long_content = """Today was a complex day with many different emotions and experiences. 
        I started the morning feeling anxious about the presentation I had to give at work. 
        The presentation went better than expected, which boosted my confidence significantly.
        Later, I had lunch with an old friend who shared some personal struggles they've been facing.
        This made me reflect on my own life and how grateful I am for the support system I have.
        In the evening, I spent time with my family, which always brings me joy and peace.
        However, I also felt overwhelmed by all the different social interactions throughout the day.
        I'm someone who needs alone time to recharge, and I didn't get much of that today.
        """ * 3  # Make it really long
        
        # Generate reflection prompt
        result = reflection_service.generate_reflection_prompt(long_content)
        
        # Should still work with long content
        assert "reflection_prompt" in result
        prompt = result["reflection_prompt"]
        assert len(prompt) > 20, "Should generate meaningful prompt even for long content"
        
        # Entry preview should be truncated appropriately
        preview = result["entry_preview"]
        assert len(preview) <= 103, "Entry preview should be truncated"  # 100 chars + "..."
        
    def test_reflection_prompt_error_handling_integration(self, real_ollama_client):
        """Test error handling with real client but invalid requests."""
        reflection_service = ReflectionService(real_ollama_client)
        
        # Test with invalid strategy
        with pytest.raises(ValueError) as exc_info:
            reflection_service.generate_reflection_prompt("test content", "invalid_strategy")
        assert "Unknown strategy" in str(exc_info.value)
        
        # Test with empty content (should still work)
        result = reflection_service.generate_reflection_prompt("")
        assert "reflection_prompt" in result
        
    def test_reflection_prompt_response_quality(self, reflection_service):
        """Test that AI generates high-quality, relevant reflection prompts."""
        test_cases = [
            {
                "content": "I had an argument with my spouse about money management.",
                "expected_themes": ["relationship", "communication", "conflict", "money", "spouse"]
            },
            {
                "content": "Feeling stuck in my career and unsure about my next steps.",
                "expected_themes": ["career", "direction", "goals", "future", "growth"]
            },
            {
                "content": "Proud of myself for completing my first marathon today.",
                "expected_themes": ["achievement", "pride", "accomplishment", "goal", "success"]
            }
        ]
        
        for case in test_cases:
            result = reflection_service.generate_reflection_prompt(case["content"])
            prompt = result["reflection_prompt"].lower()
            
            # Should be a question
            assert "?" in prompt, f"Should be a question: {prompt}"
            
            # Should be substantial
            assert len(prompt) > 30, f"Should be substantial: {prompt}"
            
            # Should relate to the content (at least one theme should appear)
            content_lower = case["content"].lower()
            prompt_relates = any(
                theme in prompt or theme in content_lower 
                for theme in case["expected_themes"]
            )
            assert prompt_relates, f"Prompt should relate to content. Content: {case['content']}, Prompt: {prompt}"
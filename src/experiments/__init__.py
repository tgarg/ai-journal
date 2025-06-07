"""
Experimental module for AI journal feature testing and improvement.

This module contains experimental functionality for testing various AI features.
It's designed to be temporary/evolving and is kept separate from core journal functionality.

Current experiments:
- reflection_prompts: Testing AI reflection prompt strategies
"""

# Import from specific experiment modules
from .reflection_prompts import PromptExperimenter

__all__ = ['PromptExperimenter']
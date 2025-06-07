"""
Experimental prompt templates for testing new reflection strategies.

These templates are separate from the core reflection service to allow
rapid iteration without modifying production code.
"""

# Experimental prompt templates using {content} placeholder
EXPERIMENTAL_TEMPLATES = {
    "emotional_awareness_v1": """Here is a journal entry: '{content}'

Generate a single question for deeper reflection that validates emotional experiences while extending awareness""",

    "perspective_v1": """Here is a journal entry: '{content}'

Generate a single question for deeper reflection that validates emotional experiences while offering an alternative perspective""",

    "assumptions_v1": """Here is a journal entry: '{content}'

Generate a single question for deeper reflection that validates the writer's experience while gently challenging their assumptions""",
}

def get_available_experimental_variants():
    """Return list of available experimental variant names."""
    return list(EXPERIMENTAL_TEMPLATES.keys())

def get_experimental_template(variant_name: str) -> str:
    """
    Get experimental template by name.
    
    Args:
        variant_name: Name of the experimental variant
        
    Returns:
        Template string with {content} placeholder
        
    Raises:
        KeyError: If variant_name is not found
    """
    if variant_name not in EXPERIMENTAL_TEMPLATES:
        available = list(EXPERIMENTAL_TEMPLATES.keys())
        raise KeyError(f"Unknown experimental variant '{variant_name}'. Available: {available}")
    
    return EXPERIMENTAL_TEMPLATES[variant_name]
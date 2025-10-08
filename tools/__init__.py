"""
Package des outils Chat-Help MCP
Outils d'assistance ultra-puissants pour LLM
"""

__version__ = "2.0.0"
__author__ = "Département Informatique"

# Imports avec gestion d'erreur
try:
    # Web & Veille
    from .web_navigator import navigate_web
    from .tech_watcher import watch_tech
    
    # Code
    from .code_expert import analyze_code_expert
    
    # Apprentissage
    from .learning_assistant import (
        create_learning_path,
        explain_advanced,
        explain_concept,
        get_joke,
        motivational_quote
    )
    
    __all__ = [
        'navigate_web',
        'watch_tech',
        'analyze_code_expert',
        'create_learning_path',
        'explain_advanced',
        'explain_concept',
        'get_joke',
        'motivational_quote',
    ]

except ImportError as e:
    import logging
    logging.error(f"Erreur d'import dans tools/__init__.py: {e}")
    raise
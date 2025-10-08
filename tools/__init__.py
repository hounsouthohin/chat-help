"""
Package des outils Chat-Help MCP
Outils d'assistance ultra-puissants pour LLM
"""

__version__ = "2.0.0"
__author__ = "Département Informatique"

# Outils Web & Veille
from .web_navigator import navigate_web
from .tech_watcher import watch_tech

# Outils Code
from .code_expert import analyze_code_expert

# Outils Apprentissage  
from .learning_assistant import create_learning_path, explain_advanced

# Anciens outils (conservés pour compatibilité)
from .web_navigator import *
from .learning_assistant import *
from .code_expert import *
from tech_watcher import *


__all__ = [
    # Nouveaux outils puissants
    'navigate_web',
    'watch_tech',
    'analyze_code_expert',
    'create_learning_path',
    'explain_advanced',
    
]
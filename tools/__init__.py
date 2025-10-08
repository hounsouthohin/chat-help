"""
Package des outils Chat-Help
Outils d'assistance pour étudiants en informatique
"""

__version__ = "1.0.0"
__author__ = "Département Informatique"

from .wiki_tools import search_wiki
from .learning_tools import explain_concept, get_joke, motivational_quote
from .code_tools import analyze_code, debug_helper
from .web_automation import browser_navigate
from .email_tools import check_emails, respond_to_email

__all__ = [
    'search_wiki',
    'explain_concept',
    'get_joke',
    'motivational_quote',
    'analyze_code',
    'debug_helper',
    'browser_navigate',
    'check_emails',
    'respond_to_email'
]
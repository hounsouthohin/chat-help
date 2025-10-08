#!/usr/bin/env python3
"""
Serveur MCP Complet avec Outils Ultra-Puissants
Protocol: MCP 2024-11-05
Transport: HTTP Streamable
"""
import asyncio
import json
import logging
from aiohttp import web

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Imports des outils
from tools.web_navigator import navigate_web
from tools.tech_watcher import watch_tech
from tools.code_expert import analyze_code_expert
from tools.learning_assistant import create_learning_path, explain_advanced


# Définition COMPLÈTE des outils MCP
TOOLS = [
    # ===== NOUVEAUX OUTILS PUISSANTS =====
    {
        "name": "navigate_web",
        "description": "🌐 Navigateur web intelligent - Recherche approfondie sur n'importe quelle plateforme avec crawling multi-niveaux",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Requête de recherche"
                },
                "start_url": {
                    "type": "string",
                    "description": "URL de départ (optionnel, sinon recherche multi-moteurs)"
                },
                "depth": {
                    "type": "integer",
                    "description": "Profondeur de recherche (1-3)",
                    "default": 2
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "watch_tech",
        "description": "📡 Veille technologique automatisée - Agrégation RSS, détection de tendances, sujets émergents",
        "inputSchema": {
            "type": "object",
            "properties": {
                "categories": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Catégories: dev, ai_ml, security, cloud, general_tech, data_science"
                },
                "keywords": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Mots-clés spécifiques à rechercher"
                },
                "hours_back": {
                    "type": "integer",
                    "description": "Période en heures (défaut: 24)",
                    "default": 24
                }
            }
        }
    },
    {
        "name": "analyze_code_expert",
        "description": "🔬 Analyseur de code expert - Analyse profonde, auto-correction, génération de tests, audit sécurité",
        "inputSchema": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Code source à analyser"
                },
                "language": {
                    "type": "string",
                    "description": "Langage: python, javascript, typescript, java, go, rust"
                },
                "include_tests": {
                    "type": "boolean",
                    "description": "Générer des tests unitaires",
                    "default": true
                },
                "auto_fix": {
                    "type": "boolean",
                    "description": "Tenter de corriger automatiquement",
                    "default": false
                }
            },
            "required": ["code", "language"]
        }
    },
    {
        "name": "create_learning_path",
        "description": "🎓 Créateur de parcours d'apprentissage - Curriculum personnalisé, ressources, exercices, projets",
        "inputSchema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "Sujet à apprendre"
                },
                "level": {
                    "type": "string",
                    "description": "Niveau: beginner, intermediate, advanced",
                    "default": "beginner"
                },
                "goals": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Objectifs d'apprentissage spécifiques"
                },
                "time_per_week": {
                    "type": "integer",
                    "description": "Heures disponibles par semaine",
                    "default": 10
                }
            },
            "required": ["topic"]
        }
    },
    {
        "name": "explain_advanced",
        "description": "💡 Explicateur avancé - Explications adaptatives avec exemples, analogies, quiz, exercices",
        "inputSchema": {
            "type": "object",
            "properties": {
                "concept": {
                    "type": "string",
                    "description": "Concept à expliquer"
                },
                "level": {
                    "type": "string",
                    "description": "Niveau: beginner, intermediate, advanced",
                    "default": "intermediate"
                },
                "with_examples": {
                    "type": "boolean",
                    "description": "Inclure des exemples de code",
                    "default": true
                },
                "with_analogies": {
                    "type": "boolean",
                    "description": "Inclure des analogies",
                    "default": true
                }
            },
            "required": ["concept"]
        }
    },
    
    # ===== OUTILS CLASSIQUES (conservés) =====
    {
        "name": "search_wiki",
        "description": "📚 Recherche Wikipedia basique",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "category": {"type": "string"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "explain_concept",
        "description": "📖 Explication simple de concept",
        "inputSchema": {
            "type": "object",
            "properties": {
                "concept": {"type": "string"},
                "level": {"type": "string", "default": "intermediate"}
            },
            "required": ["concept"]
        }
    },
    {
        "name": "analyze_code",
        "description": "🔍 Analyse de code basique",
        "inputSchema": {
            "type": "object",
            "properties": {
                "code": {"type": "string"},
                "language": {"type": "string"}
            },
            "required": ["code", "language"]
        }
    },
    {
        "name": "debug_helper",
        "description": "🐛 Aide au débogage",
        "inputSchema": {
            "type": "object",
            "properties": {
                "error_message": {"type": "string"},
                "context": {"type": "string"}
            },
            "required": ["error_message"]
        }
    },
    {
        "name": "get_joke",
        "description": "😄 Blague aléatoire",
        "inputSchema": {
            "type": "object",
            "properties": {
                "language": {"type": "string", "default": "fr"}
            }
    },
]
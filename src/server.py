#!/usr/bin/env python3
"""
Chat-Help MCP Server
Serveur MCP pour assistant IA destiné aux étudiants en informatique
"""

import asyncio
import json
import sys
from typing import Any
from mcp.server import Server
from mcp.types import Tool, TextContent
from src.tools.wiki_tools import search_wiki_content
from src.tools.learning_tools import explain_concept, analyze_code, debug_helper
from src.tools.fun_tools import get_programming_joke, get_motivational_quote

# Initialisation du serveur MCP
app = Server("chat-help")

# Définition des outils disponibles
TOOLS = [
    Tool(
        name="search_wiki",
        description="Recherche dans la documentation du wiki du département informatique. Utile pour trouver des guides, tutoriels et ressources.",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Terme ou sujet à rechercher dans le wiki"
                },
                "category": {
                    "type": "string",
                    "description": "Catégorie optionnelle (programmation, réseaux, systemes, bases-de-donnees)",
                    "enum": ["programmation", "réseaux", "systemes", "bases-de-donnees", "general"]
                }
            },
            "required": ["query"]
        }
    ),
    Tool(
        name="explain_concept",
        description="Explique un concept informatique de manière simplifiée avec des exemples. Parfait pour l'apprentissage.",
        inputSchema={
            "type": "object",
            "properties": {
                "concept": {
                    "type": "string",
                    "description": "Le concept à expliquer (ex: récursivité, pointeurs, TCP/IP)"
                },
                "level": {
                    "type": "string",
                    "description": "Niveau de détail souhaité",
                    "enum": ["debutant", "intermediaire", "avance"],
                    "default": "intermediaire"
                }
            },
            "required": ["concept"]
        }
    ),
    Tool(
        name="analyze_code",
        description="Analyse du code fourni avec suggestions d'amélioration, détection d'erreurs potentielles et bonnes pratiques.",
        inputSchema={
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Le code à analyser"
                },
                "language": {
                    "type": "string",
                    "description": "Langage de programmation",
                    "enum": ["python", "java", "javascript", "c", "cpp", "sql"]
                }
            },
            "required": ["code", "language"]
        }
    ),
    Tool(
        name="debug_helper",
        description="Aide au débogage en analysant un message d'erreur et en suggérant des solutions.",
        inputSchema={
            "type": "object",
            "properties": {
                "error_message": {
                    "type": "string",
                    "description": "Message d'erreur complet"
                },
                "context": {
                    "type": "string",
                    "description": "Contexte optionnel (code, actions effectuées)"
                }
            },
            "required": ["error_message"]
        }
    ),
    Tool(
        name="get_joke",
        description="Obtient une blague de programmation pour détendre l'atmosphère!",
        inputSchema={
            "type": "object",
            "properties": {
                "language": {
                    "type": "string",
                    "description": "Langue de la blague",
                    "enum": ["fr", "en"],
                    "default": "fr"
                }
            }
        }
    ),
    Tool(
        name="motivational_quote",
        description="Citation motivante pour booster le moral pendant les sessions d'étude.",
        inputSchema={
            "type": "object",
            "properties": {}
        }
    )
]

@app.list_tools()
async def list_tools() -> list[Tool]:
    """Liste tous les outils disponibles"""
    return TOOLS

@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Exécute un outil selon son nom"""
    
    try:
        if name == "search_wiki":
            result = await search_wiki_content(
                arguments.get("query"),
                arguments.get("category", "general")
            )
        
        elif name == "explain_concept":
            result = await explain_concept(
                arguments.get("concept"),
                arguments.get("level", "intermediaire")
            )
        
        elif name == "analyze_code":
            result = await analyze_code(
                arguments.get("code"),
                arguments.get("language")
            )
        
        elif name == "debug_helper":
            result = await debug_helper(
                arguments.get("error_message"),
                arguments.get("context", "")
            )
        
        elif name == "get_joke":
            result = await get_programming_joke(
                arguments.get("language", "fr")
            )
        
        elif name == "motivational_quote":
            result = await get_motivational_quote()
        
        else:
            result = {"error": f"Outil inconnu: {name}"}
        
        return [TextContent(
            type="text",
            text=json.dumps(result, ensure_ascii=False, indent=2)
        )]
    
    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": str(e),
                "tool": name
            }, ensure_ascii=False, indent=2)
        )]

async def main():
    """Point d'entrée principal du serveur"""
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())


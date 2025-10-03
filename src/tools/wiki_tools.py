"""
Outils de recherche dans le wiki
"""

import aiohttp
import asyncio
from typing import Dict, Any

WIKI_BASE_URL = "http://dicjlinux02.cegepjonquiere.ca:3000"

async def search_wiki_content(query: str, category: str = "general") -> Dict[str, Any]:
    """
    Recherche dans le contenu du wiki
    
    Args:
        query: Terme de recherche
        category: Catégorie de recherche
    
    Returns:
        Résultats de recherche avec liens et extraits
    """
    try:
        # Simulation de recherche (à adapter selon l'API réelle du wiki)
        async with aiohttp.ClientSession() as session:
            # Si le wiki a une API de recherche
            search_url = f"{WIKI_BASE_URL}/api/search"
            params = {
                "q": query,
                "category": category
            }
            
            try:
                async with session.get(search_url, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "success": True,
                            "query": query,
                            "category": category,
                            "results": data.get("results", []),
                            "count": len(data.get("results", []))
                        }
            except Exception as api_error:
                # Si pas d'API, retour avec message informatif
                return {
                    "success": True,
                    "query": query,
                    "category": category,
                    "message": f"Recherche pour '{query}' dans la catégorie '{category}'",
                    "wiki_url": f"{WIKI_BASE_URL}/search?q={query.replace(' ', '+')}",
                    "note": "Pour des résultats complets, consultez directement le wiki",
                    "suggestions": generate_search_suggestions(query, category)
                }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Erreur lors de la recherche: {str(e)}",
            "query": query,
            "wiki_url": WIKI_BASE_URL
        }

def generate_search_suggestions(query: str, category: str) -> list:
    """Génère des suggestions de recherche selon la catégorie"""
    
    suggestions_by_category = {
        "programmation": [
            "Consultez la section 'Langages de programmation'",
            "Vérifiez les tutoriels et exemples de code",
            "Cherchez dans les bonnes pratiques de développement"
        ],
        "réseaux": [
            "Consultez la documentation sur les protocoles réseau",
            "Vérifiez les guides de configuration",
            "Cherchez dans la section sécurité réseau"
        ],
        "systemes": [
            "Consultez les guides d'administration système",
            "Vérifiez la documentation Linux/Windows",
            "Cherchez dans les commandes système courantes"
        ],
        "bases-de-donnees": [
            "Consultez les tutoriels SQL",
            "Vérifiez les schémas de bases de données",
            "Cherchez dans l'optimisation des requêtes"
        ],
        "general": [
            "Utilisez la barre de recherche du wiki",
            "Parcourez les catégories principales",
            "Consultez l'index alphabétique"
        ]
    }
    
    return suggestions_by_category.get(category, suggestions_by_category["general"])
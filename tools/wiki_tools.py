"""
Outils de recherche dans le wiki du département
"""

import json
import os
from typing import Optional, Dict, Any
import httpx


WIKI_API_URL = "https://fr.wikipedia.org/w/api.php"  # Exemple avec Wikipedia
# Pour un vrai wiki interne, remplacer par l'URL de votre wiki


async def search_wiki(query: str, category: Optional[str] = None) -> Dict[str, Any]:
    """
    Recherche dans le wiki du département
    
    Args:
        query: Terme à rechercher
        category: Catégorie optionnelle pour filtrer
    
    Returns:
        Résultats de la recherche avec extraits
    """
    try:
        # Recherche via l'API Wikipedia (exemple)
        async with httpx.AsyncClient() as client:
            params = {
                "action": "query",
                "format": "json",
                "list": "search",
                "srsearch": f"{query} {category if category else ''}",
                "utf8": 1,
                "srlimit": 5
            }
            
            response = await client.get(WIKI_API_URL, params=params)
            data = response.json()
            
            if "query" in data and "search" in data["query"]:
                results = []
                for item in data["query"]["search"]:
                    # Récupérer l'extrait complet
                    extract = await get_page_extract(client, item["title"])
                    
                    results.append({
                        "title": item["title"],
                        "snippet": item["snippet"],
                        "extract": extract,
                        "category": category or "general"
                    })
                
                return {
                    "success": True,
                    "query": query,
                    "category": category,
                    "results_count": len(results),
                    "results": results
                }
            else:
                return {
                    "success": False,
                    "error": "Aucun résultat trouvé",
                    "query": query
                }
                
    except Exception as e:
        return {
            "success": False,
            "error": f"Erreur lors de la recherche: {str(e)}",
            "query": query
        }


async def get_page_extract(client: httpx.AsyncClient, title: str) -> str:
    """Récupère l'extrait d'une page"""
    try:
        params = {
            "action": "query",
            "format": "json",
            "prop": "extracts",
            "titles": title,
            "exintro": True,
            "explaintext": True,
            "utf8": 1
        }
        
        response = await client.get(WIKI_API_URL, params=params)
        data = response.json()
        
        pages = data.get("query", {}).get("pages", {})
        for page_id, page_data in pages.items():
            return page_data.get("extract", "")[:500]  # Limiter à 500 caractères
        
        return ""
    except:
        return ""
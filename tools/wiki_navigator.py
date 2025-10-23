# tools/wiki_navigator.py
"""
Wiki Navigator - Recherche dans la documentation locale
Compatible avec PostgreSQL via Next.js API
"""

import httpx
import os
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# Configuration

WIKI_BASE_URL = os.getenv("WIKI_URL", "http://10.10.10.5:3001")

async def wiki_search(query: str, limit: int = 5, categories: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Recherche dans le Wiki
    
    Args:
        query: Terme de recherche
        limit: Nombre de résultats max
        categories: Filtrer par catégories
    
    Returns:
        Résultats de recherche
    """
    try:
        logger.info(f"🔍 Recherche Wiki: '{query}'")
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{WIKI_BASE_URL}/api/wiki/search",
                json={
                    "query": query,
                    "limit": limit,
                    "categories": categories or []
                },
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 200:
                logger.error(f"❌ Search failed: {response.status_code}")
                return {
                    "success": False,
                    "error": f"Erreur HTTP {response.status_code}",
                    "query": query
                }
            
            data = response.json()
            
            if not data.get("success") or data.get("total", 0) == 0:
                return {
                    "success": True,
                    "query": query,
                    "message": "Aucun article trouvé",
                    "results": []
                }
            
            # Formater pour l'AI Agent
            formatted_results = []
            for result in data["results"]:
                formatted_results.append({
                    "titre": result["title"],
                    "categorie": result["category"],
                    "auteur": result.get("author", ""),
                    "description": result["description"],
                    "lien": f"{WIKI_BASE_URL}{result['url']}",
                    "tags": result.get("tags", []),
                    "difficulte": result.get("difficulty", ""),
                    "temps_lecture": f"{result.get('readingTime', 5)} min",
                    "extrait": result.get("snippet", ""),
                    "score": result.get("score", 0)
                })
            
            logger.info(f"✅ {len(formatted_results)} résultats trouvés")
            
            return {
                "success": True,
                "query": query,
                "source": "Wiki Documentation (PostgreSQL)",
                "total": data["total"],
                "results": formatted_results,
                "message": f"Trouvé {len(formatted_results)} article(s)"
            }
            
    except httpx.TimeoutException:
        logger.error("⏱️ Timeout")
        return {
            "success": False,
            "error": "Le Wiki ne répond pas",
            "query": query
        }
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "query": query
        }


async def wiki_get_article(article_id: str) -> Dict[str, Any]:
    """
    Récupère un article complet
    
    Args:
        article_id: ID de l'article
    
    Returns:
        Article complet
    """
    try:
        logger.info(f"📄 Récupération article: {article_id}")
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{WIKI_BASE_URL}/api/wiki/article/{article_id}"
            )
            
            if response.status_code == 404:
                return {
                    "success": False,
                    "error": f"Article '{article_id}' non trouvé",
                    "article_id": article_id
                }
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"Erreur HTTP {response.status_code}",
                    "article_id": article_id
                }
            
            data = response.json()
            article = data["article"]
            
            logger.info(f"✅ Article récupéré: {article['title']}")
            
            return {
                "success": True,
                "article": {
                    "id": article["id"],
                    "titre": article["title"],
                    "categorie": article["category"],
                    "auteur": article["author"],
                    "description": article["description"],
                    "contenu": article["content"],
                    "tags": article["tags"],
                    "difficulte": article["difficulty"],
                    "temps_lecture": f"{article['readingTime']} min",
                    "lien": f"{WIKI_BASE_URL}/article/{article['id']}",
                    "liens_externes": article.get("externalLinks", []),
                    "fichiers": article.get("attachmentFiles", []),
                    "derniere_maj": article["updatedAt"]
                }
            }
            
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "article_id": article_id
        }


async def wiki_list_categories() -> Dict[str, Any]:
    """
    Liste les catégories
    
    Returns:
        Liste des catégories
    """
    try:
        logger.info("📚 Récupération catégories")
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{WIKI_BASE_URL}/api/wiki/categories"
            )
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"Erreur HTTP {response.status_code}"
                }
            
            data = response.json()
            
            logger.info(f"✅ {data['total']} catégories")
            
            return {
                "success": True,
                "total": data["total"],
                "categories": data["categories"],
                "message": f"{data['total']} catégories disponibles"
            }
            
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }
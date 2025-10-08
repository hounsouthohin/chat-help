"""
Web Navigator - 100% Gratuit
Niveau 1: SearXNG (docker local)
Niveau 2: DuckDuckGo API (gratuit, pas de clé)
Niveau 3: Requests direct (scraping léger)
"""

import httpx
import os
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

SEARXNG_URL = os.getenv("SEARXNG_URL", "http://searxng:8080")
READABILITY_URL = os.getenv("READABILITY_URL", "http://readability:3000")


async def navigate_web(query: str, 
                      start_url: Optional[str] = None,
                      depth: int = 2) -> Dict[str, Any]:
    """
    Navigation web intelligente 100% gratuite
    
    Args:
        query: Requête de recherche
        start_url: URL de départ (optionnel)
        depth: Profondeur (1-3)
    
    Returns:
        Résultats de recherche
    """
    
    # NIVEAU 1 : SearXNG local (docker)
    try:
        logger.info(f"🔍 Recherche SearXNG: {query}")
        result = await _search_searxng(query)
        if result.get("success"):
            logger.info("✅ SearXNG OK")
            return result
    except Exception as e:
        logger.warning(f"❌ SearXNG failed: {e}")
    
    # NIVEAU 2 : DuckDuckGo API (gratuit, pas de clé)
    try:
        logger.info(f"🔍 Recherche DuckDuckGo: {query}")
        result = await _search_duckduckgo(query)
        if result.get("success"):
            logger.info("✅ DuckDuckGo OK")
            return result
    except Exception as e:
        logger.warning(f"❌ DuckDuckGo failed: {e}")
    
    # NIVEAU 3 : Wikipedia (toujours disponible)
    try:
        logger.info(f"🔍 Recherche Wikipedia: {query}")
        result = await _search_wikipedia(query)
        logger.info("✅ Wikipedia fallback OK")
        return result
    except Exception as e:
        logger.error(f"❌ Tous les providers ont échoué: {e}")
        return {
            "success": False,
            "error": "Tous les moteurs de recherche ont échoué",
            "query": query
        }


async def _search_searxng(query: str) -> Dict[str, Any]:
    """Recherche via SearXNG local"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{SEARXNG_URL}/search",
            params={
                "q": query,
                "format": "json",
                "language": "fr"
            },
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            
            results = []
            for item in data.get("results", [])[:10]:
                results.append({
                    "title": item.get("title"),
                    "url": item.get("url"),
                    "snippet": item.get("content", "")[:300],
                    "engine": item.get("engine")
                })
            
            return {
                "success": True,
                "provider": "searxng",
                "query": query,
                "results_count": len(results),
                "results": results
            }
        
        return {"success": False}


async def _search_duckduckgo(query: str) -> Dict[str, Any]:
    """
    Recherche via DuckDuckGo Instant Answer API
    100% gratuit, pas de clé API requise
    """
    async with httpx.AsyncClient() as client:
        # API Instant Answer (gratuite)
        response = await client.get(
            "https://api.duckduckgo.com/",
            params={
                "q": query,
                "format": "json",
                "no_html": 1,
                "skip_disambig": 1
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            
            results = []
            
            # Résultat principal
            if data.get("AbstractText"):
                results.append({
                    "title": data.get("Heading", query),
                    "url": data.get("AbstractURL"),
                    "snippet": data.get("AbstractText"),
                    "source": data.get("AbstractSource")
                })
            
            # Related topics
            for topic in data.get("RelatedTopics", [])[:5]:
                if isinstance(topic, dict) and topic.get("Text"):
                    results.append({
                        "title": topic.get("Text", "")[:100],
                        "url": topic.get("FirstURL"),
                        "snippet": topic.get("Text", "")
                    })
            
            # Si pas de résultats, scraper la page HTML
            if not results:
                html_results = await _scrape_duckduckgo_html(query, client)
                results.extend(html_results)
            
            return {
                "success": True,
                "provider": "duckduckgo",
                "query": query,
                "results_count": len(results),
                "results": results
            }
        
        return {"success": False}


async def _scrape_duckduckgo_html(query: str, client: httpx.AsyncClient) -> list:
    """Scrape DuckDuckGo HTML (backup)"""
    try:
        response = await client.get(
            "https://html.duckduckgo.com/html/",
            params={"q": query},
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []
        
        for result in soup.find_all('div', class_='result')[:10]:
            title_tag = result.find('a', class_='result__a')
            snippet_tag = result.find('a', class_='result__snippet')
            
            if title_tag:
                results.append({
                    "title": title_tag.get_text(strip=True),
                    "url": title_tag.get('href', ''),
                    "snippet": snippet_tag.get_text(strip=True) if snippet_tag else ""
                })
        
        return results
    except:
        return []


async def _search_wikipedia(query: str) -> Dict[str, Any]:
    """Recherche Wikipedia (toujours disponible)"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://fr.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "format": "json",
                "list": "search",
                "srsearch": query,
                "utf8": 1,
                "srlimit": 10
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            
            results = []
            for item in data.get("query", {}).get("search", []):
                results.append({
                    "title": item.get("title"),
                    "url": f"https://fr.wikipedia.org/wiki/{item.get('title', '').replace(' ', '_')}",
                    "snippet": item.get("snippet", "").replace('<span class="searchmatch">', '').replace('</span>', '')
                })
            
            return {
                "success": True,
                "provider": "wikipedia",
                "query": query,
                "results_count": len(results),
                "results": results,
                "note": "Résultats de Wikipedia uniquement (fallback)"
            }
        
        return {"success": False}


async def extract_content(url: str) -> Dict[str, Any]:
    """
    Extrait le contenu d'une page web
    Utilise Readability (docker) ou BeautifulSoup
    """
    # Niveau 1: Readability service
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{READABILITY_URL}/parse",
                json={"url": url},
                timeout=15
            )
            if response.status_code == 200:
                return {
                    "success": True,
                    "provider": "readability",
                    **response.json()
                }
    except:
        pass
    
    # Niveau 2: BeautifulSoup direct
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extraire texte principal
            for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
                tag.decompose()
            
            return {
                "success": True,
                "provider": "beautifulsoup",
                "title": soup.title.string if soup.title else "",
                "content": soup.get_text(separator='\n', strip=True)[:5000]
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
"""
Tech Watcher - 100% Gratuit
Niveau 1: Miniflux (docker local)
Niveau 2: APIs gratuites (Dev.to, HN, Reddit)
Niveau 3: RSS direct avec feedparser
"""

import httpx
import feedparser
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

MINIFLUX_URL = os.getenv("MINIFLUX_URL", "http://miniflux:8080")


async def watch_tech(categories: Optional[List[str]] = None,
                    keywords: Optional[List[str]] = None,
                    hours_back: int = 24) -> Dict[str, Any]:
    """
    Veille technologique 100% gratuite
    """
    
    # NIVEAU 1 : Miniflux local (si configuré)
    try:
        logger.info("📡 Tentative Miniflux...")
        result = await _watch_miniflux(categories, keywords, hours_back)
        if result.get("success"):
            logger.info("✅ Miniflux OK")
            return result
    except Exception as e:
        logger.warning(f"❌ Miniflux failed: {e}")
    
    # NIVEAU 2 : APIs gratuites (Dev.to, HN, Reddit)
    try:
        logger.info("📡 Tentative APIs gratuites...")
        result = await _watch_free_apis(categories, keywords, hours_back)
        if result.get("success"):
            logger.info("✅ APIs gratuites OK")
            return result
    except Exception as e:
        logger.warning(f"❌ APIs gratuites failed: {e}")
    
    # NIVEAU 3 : RSS direct (toujours disponible)
    logger.info("📡 Fallback RSS direct...")
    return await _watch_rss_direct(categories, keywords, hours_back)


async def _watch_miniflux(categories, keywords, hours_back) -> Dict:
    """Utilise Miniflux local"""
    # TODO: Implémenter quand Miniflux est configuré
    return {"success": False}


async def _watch_free_apis(categories, keywords, hours_back) -> Dict:
    """
    Agrège plusieurs APIs gratuites sans clé
    """
    all_articles = []
    
    async with httpx.AsyncClient() as client:
        # 1. Dev.to (gratuit, pas de clé)
        try:
            response = await client.get(
                "https://dev.to/api/articles",
                params={"per_page": 20, "top": 7},
                timeout=10
            )
            if response.status_code == 200:
                for item in response.json():
                    all_articles.append({
                        "title": item.get("title"),
                        "url": item.get("url"),
                        "published": item.get("published_at"),
                        "source": "Dev.to",
                        "tags": item.get("tag_list", [])
                    })
        except:
            pass
        
        # 2. Hacker News via Algolia (gratuit, officiel)
        try:
            query = " ".join(keywords) if keywords else "technology"
            response = await client.get(
                "https://hn.algolia.com/api/v1/search",
                params={
                    "query": query,
                    "tags": "story",
                    "numericFilters": f"created_at_i>{int((datetime.now() - timedelta(hours=hours_back)).timestamp())}"
                },
                timeout=10
            )
            if response.status_code == 200:
                for item in response.json().get("hits", []):
                    all_articles.append({
                        "title": item.get("title"),
                        "url": item.get("url") or f"https://news.ycombinator.com/item?id={item.get('objectID')}",
                        "published": item.get("created_at"),
                        "source": "Hacker News",
                        "points": item.get("points", 0)
                    })
        except:
            pass
        
        # 3. Reddit (gratuit, JSON public)
        try:
            subreddits = "programming+python+webdev+technology"
            response = await client.get(
                f"https://www.reddit.com/r/{subreddits}/hot.json",
                params={"limit": 25},
                headers={"User-Agent": "TechWatcher/1.0"},
                timeout=10
            )
            if response.status_code == 200:
                for item in response.json().get("data", {}).get("children", []):
                    data = item.get("data", {})
                    all_articles.append({
                        "title": data.get("title"),
                        "url": data.get("url"),
                        "published": datetime.fromtimestamp(data.get("created_utc", 0)).isoformat(),
                        "source": f"r/{data.get('subreddit')}",
                        "score": data.get("score", 0)
                    })
        except:
            pass
    
    return {
        "success": True,
        "provider": "free_apis",
        "articles": all_articles,
        "total": len(all_articles)
    }


async def _watch_rss_direct(categories, keywords, hours_back) -> Dict:
    """
    Parse RSS directement (fallback garanti)
    """
    RSS_FEEDS = {
        "dev": [
            "https://news.ycombinator.com/rss",
            "https://dev.to/feed",
        ],
        "ai_ml": [
            "https://www.kdnuggets.com/feed",
        ],
        "general": [
            "https://techcrunch.com/feed/",
        ]
    }
    
    feeds_to_parse = []
    if categories:
        for cat in categories:
            feeds_to_parse.extend(RSS_FEEDS.get(cat, []))
    else:
        # Toutes les catégories par défaut
        for feeds in RSS_FEEDS.values():
            feeds_to_parse.extend(feeds)
    
    all_articles = []
    cutoff = datetime.now() - timedelta(hours=hours_back)
    
    async with httpx.AsyncClient() as client:
        for feed_url in feeds_to_parse:
            try:
                response = await client.get(feed_url, timeout=10)
                feed = feedparser.parse(response.text)
                
                for entry in feed.entries[:15]:
                    # Parse date
                    pub_date = None
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        from time import mktime
                        pub_date = datetime.fromtimestamp(mktime(entry.published_parsed))
                    
                    # Filtrer par date
                    if pub_date and pub_date < cutoff:
                        continue
                    
                    all_articles.append({
                        "title": entry.get("title", ""),
                        "url": entry.get("link", ""),
                        "published": pub_date.isoformat() if pub_date else "",
                        "source": feed_url.split("//")[1].split("/")[0],
                        "summary": entry.get("summary", "")[:200]
                    })
            except Exception as e:
                logger.warning(f"Failed to parse {feed_url}: {e}")
    
    return {
        "success": True,
        "provider": "rss_direct",
        "articles": all_articles,
        "total": len(all_articles)
    }
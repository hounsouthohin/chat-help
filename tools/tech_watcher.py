"""
Tech Watcher - UNIVERSEL - Veille sur N'IMPORTE quelle technologie
Stratégie: Utilise les keywords directement sans catégories fixes
"""

import httpx
import feedparser
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
import asyncio
import re

logger = logging.getLogger(__name__)

SEARXNG_URL = os.getenv("SEARXNG_URL", "http://searxng:8080")
MINIFLUX_URL = os.getenv("MINIFLUX_URL", "http://miniflux:8080")


async def watch_tech(
    query: Optional[str] = None,
    keywords: Optional[List[str]] = None,
    hours_back: int = 24,
    sources: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Veille technologique UNIVERSELLE
    
    Args:
        query: Recherche libre (ex: "Rust programming", "Kubernetes cloud")
        keywords: Liste de mots-clés spécifiques
        hours_back: Nombre d'heures à remonter
        sources: Sources spécifiques ["reddit", "hn", "devto", "rss", "searxng"]
    
    Returns:
        Dict avec articles, total, provider, etc.
    """
    
    # 🎯 Construit la requête de recherche intelligente
    search_query = _build_search_query(query, keywords)
    logger.info(f"🔍 Universal Tech Watch - Query: '{search_query}'")
    
    # Détermine les sources à utiliser (toutes par défaut)
    active_sources = sources or ["devto", "hn", "reddit", "rss", "searxng"]
    
    all_articles = []
    results_by_source = {}
    
    # 🌐 Niveau 1: SearXNG (le plus puissant si disponible)
    if "searxng" in active_sources and SEARXNG_URL:
        try:
            logger.info("📡 Trying SearXNG (most powerful)...")
            searxng_results = await _search_searxng(search_query, hours_back)
            if searxng_results.get("success") and searxng_results.get("total", 0) > 5:
                logger.info(f"✅ SearXNG: {searxng_results['total']} articles - USING THIS")
                return searxng_results
            results_by_source["searxng"] = searxng_results
        except Exception as e:
            logger.warning(f"❌ SearXNG failed: {e}")
    
    # 🔥 Niveau 2: APIs gratuites spécialisées (parallèle)
    api_tasks = []
    if "devto" in active_sources:
        api_tasks.append(_search_devto(search_query, hours_back))
    if "hn" in active_sources:
        api_tasks.append(_search_hackernews(search_query, hours_back))
    if "reddit" in active_sources:
        api_tasks.append(_search_reddit(search_query, hours_back))
    
    if api_tasks:
        logger.info(f"📡 Fetching {len(api_tasks)} API sources in parallel...")
        api_results = await asyncio.gather(*api_tasks, return_exceptions=True)
        
        for i, result in enumerate(api_results):
            if isinstance(result, Exception):
                logger.warning(f"API {i} failed: {result}")
                continue
            if result.get("articles"):
                all_articles.extend(result["articles"])
                source_name = result.get("source", f"api_{i}")
                results_by_source[source_name] = result
                logger.info(f"✅ {source_name}: {len(result['articles'])} articles")
    
    # 📰 Niveau 3: RSS dynamique (toujours actif)
    if "rss" in active_sources:
        try:
            logger.info("📡 Fetching RSS feeds...")
            rss_results = await _search_rss_dynamic(search_query, hours_back)
            if rss_results.get("articles"):
                all_articles.extend(rss_results["articles"])
                results_by_source["rss"] = rss_results
                logger.info(f"✅ RSS: {len(rss_results['articles'])} articles")
        except Exception as e:
            logger.warning(f"❌ RSS failed: {e}")
    
    # 🎯 Déduplique et trie les résultats
    all_articles = _deduplicate_articles(all_articles)
    all_articles = _rank_articles(all_articles, search_query)
    
    return {
        "success": len(all_articles) > 0,
        "provider": "multi_source",
        "query": search_query,
        "articles": all_articles[:50],  # Top 50
        "total": len(all_articles),
        "sources_used": list(results_by_source.keys()),
        "results_by_source": {k: v.get("total", 0) for k, v in results_by_source.items()},
        "hours_back": hours_back
    }


def _build_search_query(query: Optional[str], keywords: Optional[List[str]]) -> str:
    """
    Construit une requête de recherche intelligente
    """
    if query:
        return query.strip()
    
    if keywords:
        # Combine intelligemment les keywords
        return " ".join(keywords[:5])  # Max 5 keywords
    
    return "technology news"  # Fallback


async def _search_searxng(query: str, hours_back: int) -> Dict:
    """
    SearXNG - Le plus puissant (agrège Google, Bing, DuckDuckGo, etc.)
    """
    try:
        time_range = "day" if hours_back <= 24 else "week" if hours_back <= 168 else "month"
        
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(
                f"{SEARXNG_URL}/search",
                params={
                    "q": query,
                    "format": "json",
                    "categories": "general,science,it",
                    "time_range": time_range,
                    "language": "en"
                }
            )
            
            if response.status_code != 200:
                return {"success": False, "articles": []}
            
            results = response.json().get("results", [])
            articles = []
            
            for item in results[:30]:
                articles.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "published": item.get("publishedDate", ""),
                    "source": "SearXNG",
                    "engine": item.get("engine", ""),
                    "content": item.get("content", "")[:300],
                    "score": item.get("score", 0)
                })
            
            return {
                "success": True,
                "source": "searxng",
                "articles": articles,
                "total": len(articles)
            }
    except Exception as e:
        logger.error(f"SearXNG error: {e}")
        return {"success": False, "articles": []}


async def _search_devto(query: str, hours_back: int) -> Dict:
    """
    Dev.to - Articles de développement
    """
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            # Dev.to ne supporte pas vraiment la recherche par API
            # On utilise les tags ou top articles
            response = await client.get(
                "https://dev.to/api/articles",
                params={
                    "per_page": 30,
                    "top": "7" if hours_back <= 168 else "30"
                }
            )
            
            if response.status_code != 200:
                return {"articles": []}
            
            articles = []
            cutoff = datetime.now() - timedelta(hours=hours_back)
            
            for item in response.json():
                pub_date = datetime.fromisoformat(item.get("published_at", "").replace("Z", "+00:00"))
                
                if pub_date < cutoff:
                    continue
                
                # Filtre par pertinence (simple matching)
                title_lower = item.get("title", "").lower()
                tags = " ".join(item.get("tag_list", [])).lower()
                if not any(word.lower() in title_lower or word.lower() in tags 
                          for word in query.split()):
                    continue
                
                articles.append({
                    "title": item.get("title"),
                    "url": item.get("url"),
                    "published": item.get("published_at"),
                    "source": "Dev.to",
                    "tags": item.get("tag_list", []),
                    "score": item.get("public_reactions_count", 0)
                })
            
            return {"source": "devto", "articles": articles, "total": len(articles)}
    except Exception as e:
        logger.error(f"Dev.to error: {e}")
        return {"articles": []}


async def _search_hackernews(query: str, hours_back: int) -> Dict:
    """
    Hacker News via Algolia - Très efficace
    """
    try:
        timestamp = int((datetime.now() - timedelta(hours=hours_back)).timestamp())
        
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                "https://hn.algolia.com/api/v1/search",
                params={
                    "query": query,
                    "tags": "story",
                    "numericFilters": f"created_at_i>{timestamp}",
                    "hitsPerPage": 30
                }
            )
            
            if response.status_code != 200:
                return {"articles": []}
            
            articles = []
            for item in response.json().get("hits", []):
                url = item.get("url") or f"https://news.ycombinator.com/item?id={item.get('objectID')}"
                articles.append({
                    "title": item.get("title"),
                    "url": url,
                    "published": item.get("created_at"),
                    "source": "Hacker News",
                    "score": item.get("points", 0),
                    "comments": item.get("num_comments", 0)
                })
            
            return {"source": "hackernews", "articles": articles, "total": len(articles)}
    except Exception as e:
        logger.error(f"Hacker News error: {e}")
        return {"articles": []}


async def _search_reddit(query: str, hours_back: int) -> Dict:
    """
    Reddit - Détecte automatiquement les subreddits pertinents
    """
    try:
        # 🎯 Mapping intelligent de requêtes vers subreddits
        subreddit_map = {
            "ai": "MachineLearning+artificial+deeplearning+LocalLLaMA",
            "machine learning": "MachineLearning+deeplearning+datascience",
            "robot": "robotics+ROS+automation+roboticists",
            "python": "Python+learnpython+pythoncoding",
            "javascript": "javascript+node+reactjs+webdev",
            "rust": "rust+rust_gamedev",
            "kubernetes": "kubernetes+devops+selfhosted",
            "docker": "docker+selfhosted+homelab",
            "blockchain": "CryptoCurrency+ethereum+Bitcoin",
            "cybersecurity": "cybersecurity+netsec+AskNetsec",
            "gaming": "gaming+Games+pcgaming",
            "cloud": "aws+AZURE+googlecloud+devops"
        }
        
        # Détecte les subreddits pertinents
        query_lower = query.lower()
        relevant_subs = []
        for key, subs in subreddit_map.items():
            if key in query_lower:
                relevant_subs.append(subs)
        
        # Fallback vers subreddits généraux tech
        subreddits = "+".join(relevant_subs) if relevant_subs else "programming+technology+python+webdev+machinelearning"
        
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"https://www.reddit.com/r/{subreddits}/search.json",
                params={
                    "q": query,
                    "sort": "relevance",
                    "t": "week" if hours_back <= 168 else "month",
                    "limit": 30
                },
                headers={"User-Agent": "TechWatcher/2.0"}
            )
            
            if response.status_code != 200:
                return {"articles": []}
            
            articles = []
            cutoff = datetime.now() - timedelta(hours=hours_back)
            
            for item in response.json().get("data", {}).get("children", []):
                data = item.get("data", {})
                created = datetime.fromtimestamp(data.get("created_utc", 0))
                
                if created < cutoff:
                    continue
                
                articles.append({
                    "title": data.get("title"),
                    "url": data.get("url"),
                    "published": created.isoformat(),
                    "source": f"r/{data.get('subreddit')}",
                    "score": data.get("score", 0),
                    "comments": data.get("num_comments", 0)
                })
            
            return {"source": "reddit", "articles": articles, "total": len(articles)}
    except Exception as e:
        logger.error(f"Reddit error: {e}")
        return {"articles": []}


async def _search_rss_dynamic(query: str, hours_back: int) -> Dict:
    """
    RSS dynamique - Sélectionne les flux selon la requête
    """
    # 🎯 Base de flux RSS organisée par thème
    RSS_FEEDS = {
        "general": [
            "https://news.ycombinator.com/rss",
            "https://techcrunch.com/feed/",
            "https://www.theverge.com/rss/index.xml",
        ],
        "dev": [
            "https://dev.to/feed",
            "https://stackoverflow.blog/feed/",
        ],
        "ai": [
            "https://www.kdnuggets.com/feed",
            "https://machinelearningmastery.com/feed/",
        ],
        "security": [
            "https://krebsonsecurity.com/feed/",
            "https://www.schneier.com/blog/atom.xml",
        ],
        "robotics": [
            "https://spectrum.ieee.org/feeds/robotics.rss",
            "https://www.therobotreport.com/feed/",
        ],
        "cloud": [
            "https://aws.amazon.com/blogs/aws/feed/",
        ]
    }
    
    # Détecte les flux pertinents
    query_lower = query.lower()
    selected_feeds = RSS_FEEDS.get("general", []).copy()
    
    for theme, feeds in RSS_FEEDS.items():
        if theme in query_lower or any(word in query_lower for word in theme.split()):
            selected_feeds.extend(feeds)
    
    # Limite à 5 flux max pour la vitesse
    selected_feeds = list(set(selected_feeds))[:5]
    
    articles = []
    cutoff = datetime.now() - timedelta(hours=hours_back)
    
    async with httpx.AsyncClient(timeout=15) as client:
        for feed_url in selected_feeds:
            try:
                response = await client.get(feed_url)
                feed = feedparser.parse(response.text)
                
                for entry in feed.entries[:15]:
                    pub_date = None
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        from time import mktime
                        pub_date = datetime.fromtimestamp(mktime(entry.published_parsed))
                    
                    if pub_date and pub_date < cutoff:
                        continue
                    
                    articles.append({
                        "title": entry.get("title", ""),
                        "url": entry.get("link", ""),
                        "published": pub_date.isoformat() if pub_date else "",
                        "source": feed.feed.get("title", "RSS"),
                        "summary": entry.get("summary", "")[:300]
                    })
            except:
                pass
    
    return {"articles": articles, "total": len(articles)}


def _deduplicate_articles(articles: List[Dict]) -> List[Dict]:
    """
    Supprime les doublons par URL
    """
    seen_urls = set()
    unique = []
    
    for article in articles:
        url = article.get("url", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique.append(article)
    
    return unique


def _rank_articles(articles: List[Dict], query: str) -> List[Dict]:
    """
    Classe les articles par pertinence et score
    """
    query_words = set(query.lower().split())
    
    def calculate_relevance(article):
        title = article.get("title", "").lower()
        score = article.get("score", 0)
        
        # Score de pertinence basique
        relevance = sum(1 for word in query_words if word in title)
        
        # Combine relevance + social score
        return (relevance * 100) + score
    
    articles.sort(key=calculate_relevance, reverse=True)
    return articles


# 🧪 Test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test avec différentes technologies
    test_queries = [
        "Rust programming",
        "Kubernetes deployment",
        "robotics ROS",
        "blockchain ethereum",
        "cybersecurity vulnerabilities"
    ]
    
    async def test_all():
        for test_query in test_queries:
            print(f"\n{'='*60}")
            print(f"🔍 Testing: {test_query}")
            print(f"{'='*60}")
            
            result = await watch_tech(query=test_query, hours_back=48)
            print(f"✅ Found {result['total']} articles")
            print(f"📡 Sources: {result['sources_used']}")
            
            for i, article in enumerate(result['articles'][:3], 1):
                print(f"{i}. {article['title'][:70]}... - {article['source']}")
    
    asyncio.run(test_all())
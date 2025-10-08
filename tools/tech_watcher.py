"""
Tech Watcher - Veille Technologique Automatisée
Agrégation RSS, analyse de tendances, détection de nouveautés tech
"""

import asyncio
import httpx
import feedparser
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import re
import hashlib
import logging

logger = logging.getLogger(__name__)


class TechWatcher:
    """Système de veille technologique intelligent"""
    
    # Sources RSS tech de qualité
    RSS_SOURCES = {
        "dev": [
            "https://dev.to/feed",
            "https://news.ycombinator.com/rss",
            "https://www.reddit.com/r/programming/.rss",
            "https://github.blog/feed/",
        ],
        "ai_ml": [
            "https://www.artificialintelligence-news.com/feed/",
            "https://machinelearningmastery.com/feed/",
            "https://www.kdnuggets.com/feed",
        ],
        "security": [
            "https://www.bleepingcomputer.com/feed/",
            "https://thehackernews.com/feeds/posts/default",
            "https://krebsonsecurity.com/feed/",
        ],
        "cloud": [
            "https://aws.amazon.com/blogs/aws/feed/",
            "https://azure.microsoft.com/en-us/blog/feed/",
            "https://cloud.google.com/blog/rss",
        ],
        "general_tech": [
            "https://techcrunch.com/feed/",
            "https://www.theverge.com/rss/index.xml",
            "https://arstechnica.com/feed/",
            "https://www.wired.com/feed/rss",
        ],
        "data_science": [
            "https://towardsdatascience.com/feed",
            "https://www.datasciencecentral.com/feed/",
        ]
    }
    
    def __init__(self):
        self.cache = {}
        self.trends = defaultdict(int)
        
    async def tech_watch(self, 
                        categories: Optional[List[str]] = None,
                        keywords: Optional[List[str]] = None,
                        hours_back: int = 24,
                        max_articles: int = 50) -> Dict[str, Any]:
        """
        Effectue une veille technologique
        
        Args:
            categories: Catégories à surveiller (dev, ai_ml, security, etc.)
            keywords: Mots-clés spécifiques à rechercher
            hours_back: Nombre d'heures en arrière
            max_articles: Nombre max d'articles à retourner
        """
        try:
            # Catégories par défaut
            if not categories:
                categories = ["dev", "ai_ml", "general_tech"]
            
            # Collecter les feeds
            all_articles = []
            for category in categories:
                if category in self.RSS_SOURCES:
                    category_articles = await self._fetch_category(
                        category, hours_back
                    )
                    all_articles.extend(category_articles)
            
            # Filtrer par mots-clés si fournis
            if keywords:
                all_articles = self._filter_by_keywords(all_articles, keywords)
            
            # Trier par pertinence et date
            all_articles = sorted(
                all_articles,
                key=lambda x: (x.get('relevance_score', 0), x.get('published', '')),
                reverse=True
            )[:max_articles]
            
            # Analyser les tendances
            trends = self._analyze_trends(all_articles)
            
            # Détecter les sujets émergents
            emerging = self._detect_emerging_topics(all_articles)
            
            return {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "categories": categories,
                "keywords": keywords,
                "period_hours": hours_back,
                "total_articles": len(all_articles),
                "articles": all_articles,
                "trends": trends,
                "emerging_topics": emerging,
                "summary": self._generate_summary(all_articles, trends)
            }
            
        except Exception as e:
            logger.error(f"Erreur tech_watch: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _fetch_category(self, category: str, hours_back: int) -> List[Dict[str, Any]]:
        """Récupère les articles d'une catégorie"""
        articles = []
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        feeds = self.RSS_SOURCES.get(category, [])
        
        async with httpx.AsyncClient() as client:
            tasks = [self._fetch_feed(client, url, category) for url in feeds]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, list):
                    for article in result:
                        # Filtrer par date
                        pub_date = article.get('published_datetime')
                        if pub_date and pub_date > cutoff_time:
                            articles.append(article)
        
        return articles
    
    async def _fetch_feed(self, client: httpx.AsyncClient, url: str, category: str) -> List[Dict[str, Any]]:
        """Récupère un feed RSS"""
        try:
            response = await client.get(url, timeout=15)
            feed = feedparser.parse(response.text)
            
            articles = []
            for entry in feed.entries[:20]:
                article = self._parse_entry(entry, category)
                if article:
                    articles.append(article)
            
            return articles
            
        except Exception as e:
            logger.warning(f"Erreur fetch {url}: {str(e)}")
            return []
    
    def _parse_entry(self, entry, category: str) -> Optional[Dict[str, Any]]:
        """Parse une entrée de feed"""
        try:
            # Extraire la date
            pub_date = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                from time import mktime
                pub_date = datetime.fromtimestamp(mktime(entry.published_parsed))
            
            # Extraire le contenu
            content = ""
            if hasattr(entry, 'summary'):
                content = entry.summary
            elif hasattr(entry, 'content'):
                content = entry.content[0].value if entry.content else ""
            
            # Nettoyer le HTML
            content_clean = re.sub(r'<[^>]+>', '', content)
            
            # Extraire les mots-clés
            keywords = self._extract_keywords_from_text(
                entry.title + " " + content_clean
            )
            
            # Score de pertinence
            relevance = self._calculate_article_relevance(entry.title, content_clean, keywords)
            
            return {
                "title": entry.title,
                "link": entry.link,
                "published": entry.get('published', ''),
                "published_datetime": pub_date,
                "category": category,
                "summary": content_clean[:300],
                "keywords": keywords,
                "relevance_score": relevance,
                "source": entry.get('source', {}).get('title', 'Unknown')
            }
            
        except Exception as e:
            logger.warning(f"Erreur parse entry: {str(e)}")
            return None
    
    def _filter_by_keywords(self, articles: List[Dict], keywords: List[str]) -> List[Dict]:
        """Filtre les articles par mots-clés"""
        filtered = []
        keywords_lower = [k.lower() for k in keywords]
        
        for article in articles:
            text = (article.get('title', '') + ' ' + article.get('summary', '')).lower()
            
            # Vérifier si au moins un mot-clé est présent
            if any(keyword in text for keyword in keywords_lower):
                # Boost le score de pertinence
                article['relevance_score'] = article.get('relevance_score', 0) + 0.3
                filtered.append(article)
        
        return filtered
    
    def _extract_keywords_from_text(self, text: str) -> List[str]:
        """Extrait les mots-clés techniques d'un texte"""
        # Mots-clés tech communs
        tech_patterns = [
            r'\b(Python|JavaScript|TypeScript|Rust|Go|Java|C\+\+|Ruby)\b',
            r'\b(React|Vue|Angular|Django|Flask|FastAPI|Node\.js)\b',
            r'\b(Docker|Kubernetes|AWS|Azure|GCP|Cloud)\b',
            r'\b(AI|ML|Machine Learning|Deep Learning|Neural Network)\b',
            r'\b(API|REST|GraphQL|gRPC|WebSocket)\b',
            r'\b(Git|GitHub|GitLab|CI/CD|DevOps)\b',
            r'\b(SQL|PostgreSQL|MySQL|MongoDB|Redis)\b',
            r'\b(Security|Cybersecurity|Encryption|Authentication)\b',
        ]
        
        keywords = set()
        for pattern in tech_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            keywords.update(matches)
        
        return list(keywords)[:10]
    
    def _calculate_article_relevance(self, title: str, content: str, keywords: List[str]) -> float:
        """Calcule le score de pertinence d'un article"""
        score = 0.0
        
        # Mots-clés dans le titre (plus important)
        for kw in keywords:
            if kw.lower() in title.lower():
                score += 0.3
        
        # Mots-clés dans le contenu
        for kw in keywords:
            count = content.lower().count(kw.lower())
            score += min(count * 0.1, 0.5)
        
        # Longueur du contenu (articles plus longs = plus de détails)
        if len(content) > 500:
            score += 0.2
        
        return min(score, 1.0)
    
    def _analyze_trends(self, articles: List[Dict]) -> Dict[str, Any]:
        """Analyse les tendances à partir des articles"""
        # Compter les mots-clés
        keyword_freq = defaultdict(int)
        category_freq = defaultdict(int)
        
        for article in articles:
            for kw in article.get('keywords', []):
                keyword_freq[kw] += 1
            
            category = article.get('category', 'unknown')
            category_freq[category] += 1
        
        # Top tendances
        top_keywords = sorted(
            keyword_freq.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        top_categories = sorted(
            category_freq.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return {
            "hot_keywords": [
                {"keyword": kw, "mentions": count}
                for kw, count in top_keywords
            ],
            "active_categories": [
                {"category": cat, "article_count": count}
                for cat, count in top_categories
            ]
        }
    
    def _detect_emerging_topics(self, articles: List[Dict]) -> List[Dict[str, Any]]:
        """Détecte les sujets émergents"""
        # Grouper par mots-clés récents
        recent_keywords = defaultdict(list)
        
        for article in articles:
            for kw in article.get('keywords', []):
                recent_keywords[kw].append(article)
        
        # Identifier les sujets avec croissance rapide
        emerging = []
        for kw, kw_articles in recent_keywords.items():
            if len(kw_articles) >= 3:  # Au moins 3 articles
                emerging.append({
                    "topic": kw,
                    "article_count": len(kw_articles),
                    "first_seen": min(a.get('published', '') for a in kw_articles),
                    "trend": "rising",
                    "sample_articles": [
                        {"title": a['title'], "link": a['link']}
                        for a in kw_articles[:3]
                    ]
                })
        
        # Trier par nombre d'articles
        emerging = sorted(emerging, key=lambda x: x['article_count'], reverse=True)
        
        return emerging[:5]
    
    def _generate_summary(self, articles: List[Dict], trends: Dict) -> str:
        """Génère un résumé de la veille"""
        if not articles:
            return "Aucun article trouvé pour cette période."
        
        summary = f"📰 Veille Technologique - {len(articles)} articles analysés\n\n"
        
        # Top tendances
        if trends.get('hot_keywords'):
            summary += "🔥 Tendances chaudes:\n"
            for item in trends['hot_keywords'][:5]:
                summary += f"  • {item['keyword']} ({item['mentions']} mentions)\n"
            summary += "\n"
        
        # Articles récents
        summary += "📌 Articles récents notables:\n"
        for article in articles[:5]:
            summary += f"  • {article['title']}\n"
            summary += f"    {article.get('link', '')}\n"
        
        return summary


# Instance globale
watcher = TechWatcher()


async def watch_tech(categories: Optional[List[str]] = None,
                    keywords: Optional[List[str]] = None,
                    hours_back: int = 24) -> Dict[str, Any]:
    """
    Fonction principale de veille technologique
    
    Args:
        categories: Catégories à surveiller
        keywords: Mots-clés spécifiques
        hours_back: Période en heures
    
    Returns:
        Résultats de veille structurés
    """
    return await watcher.tech_watch(categories, keywords, hours_back)
"""
Web Navigator - Navigateur Web Intelligent et Puissant
Capable de naviguer sur n'importe quelle plateforme et d'effectuer des recherches approfondies
"""

import asyncio
import httpx
from bs4 import BeautifulSoup
from typing import Dict, Any, List, Optional
import re
from urllib.parse import urljoin, urlparse
import logging
from datetime import datetime
import hashlib
from collections import defaultdict

logger = logging.getLogger(__name__)


class WebNavigator:
    """Navigateur web intelligent avec capacités de recherche avancées"""
    
    def __init__(self):
        self.visited_urls = set()
        self.search_results = []
        self.max_depth = 3
        self.max_pages = 20
        self.timeout = 30
        
    async def smart_search(self, query: str, start_url: Optional[str] = None, 
                          search_depth: int = 2) -> Dict[str, Any]:
        """
        Recherche intelligente sur le web
        
        Args:
            query: Requête de recherche
            start_url: URL de départ (optionnel, sinon recherche Google)
            search_depth: Profondeur de recherche (1-3)
        """
        try:
            self.visited_urls.clear()
            self.search_results = []
            self.max_depth = min(search_depth, 3)
            
            results = {
                "success": True,
                "query": query,
                "start_url": start_url,
                "timestamp": datetime.now().isoformat(),
                "pages_analyzed": 0,
                "findings": [],
                "related_links": [],
                "summary": ""
            }
            
            if start_url:
                # Recherche sur une plateforme spécifique
                await self._crawl_platform(start_url, query, depth=0)
            else:
                # Recherche web générale
                search_urls = await self._multi_search_engine(query)
                for url in search_urls[:10]:
                    await self._analyze_page(url, query)
            
            # Compiler les résultats
            results["findings"] = self.search_results[:20]
            results["pages_analyzed"] = len(self.visited_urls)
            results["related_links"] = await self._find_related_content(query)
            results["summary"] = self._generate_summary(query)
            
            return results
            
        except Exception as e:
            logger.error(f"Erreur smart_search: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "query": query
            }
    
    async def _multi_search_engine(self, query: str) -> List[str]:
        """Recherche sur plusieurs moteurs"""
        urls = []
        
        # Google Search
        google_urls = await self._search_google(query)
        urls.extend(google_urls)
        
        # DuckDuckGo Search
        ddg_urls = await self._search_duckduckgo(query)
        urls.extend(ddg_urls)
        
        # Bing Search
        bing_urls = await self._search_bing(query)
        urls.extend(bing_urls)
        
        # Dédupliquer
        return list(dict.fromkeys(urls))
    
    async def _search_google(self, query: str) -> List[str]:
        """Recherche Google via API personnalisée"""
        try:
            async with httpx.AsyncClient() as client:
                # Utiliser Google Custom Search API ou scraping éthique
                url = f"https://www.google.com/search?q={query}"
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
                
                response = await client.get(url, headers=headers, timeout=10)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                links = []
                for a in soup.find_all('a', href=True):
                    href = a['href']
                    if '/url?q=' in href:
                        # Extraire l'URL réelle
                        match = re.search(r'/url\?q=(.*?)&', href)
                        if match:
                            real_url = match.group(1)
                            if real_url.startswith('http'):
                                links.append(real_url)
                
                return links[:10]
        except:
            return []
    
    async def _search_duckduckgo(self, query: str) -> List[str]:
        """Recherche DuckDuckGo"""
        try:
            async with httpx.AsyncClient() as client:
                url = f"https://html.duckduckgo.com/html/?q={query}"
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                }
                
                response = await client.get(url, headers=headers, timeout=10)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                links = []
                for a in soup.find_all('a', class_='result__url', href=True):
                    href = a['href']
                    if href.startswith('http'):
                        links.append(href)
                
                return links[:10]
        except:
            return []
    
    async def _search_bing(self, query: str) -> List[str]:
        """Recherche Bing"""
        try:
            async with httpx.AsyncClient() as client:
                url = f"https://www.bing.com/search?q={query}"
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                }
                
                response = await client.get(url, headers=headers, timeout=10)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                links = []
                for a in soup.find_all('a', href=True):
                    href = a['href']
                    if href.startswith('http') and 'bing.com' not in href:
                        links.append(href)
                
                return links[:10]
        except:
            return []
    
    async def _crawl_platform(self, base_url: str, query: str, depth: int = 0):
        """Explore une plateforme en profondeur"""
        if depth >= self.max_depth or len(self.visited_urls) >= self.max_pages:
            return
        
        if base_url in self.visited_urls:
            return
        
        self.visited_urls.add(base_url)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(base_url, timeout=self.timeout, follow_redirects=True)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Analyser la page
                page_data = self._extract_content(soup, query)
                if page_data["relevance_score"] > 0.3:
                    self.search_results.append({
                        "url": base_url,
                        "title": page_data["title"],
                        "content": page_data["content"][:500],
                        "relevance": page_data["relevance_score"],
                        "depth": depth
                    })
                
                # Trouver les liens internes
                domain = urlparse(base_url).netloc
                for link in soup.find_all('a', href=True):
                    next_url = urljoin(base_url, link['href'])
                    next_domain = urlparse(next_url).netloc
                    
                    # Rester sur le même domaine
                    if next_domain == domain and next_url not in self.visited_urls:
                        await self._crawl_platform(next_url, query, depth + 1)
                        
        except Exception as e:
            logger.error(f"Erreur crawl {base_url}: {str(e)}")
    
    async def _analyze_page(self, url: str, query: str):
        """Analyse une page web"""
        if url in self.visited_urls:
            return
        
        self.visited_urls.add(url)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10, follow_redirects=True)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                page_data = self._extract_content(soup, query)
                
                if page_data["relevance_score"] > 0.2:
                    self.search_results.append({
                        "url": url,
                        "title": page_data["title"],
                        "content": page_data["content"][:500],
                        "relevance": page_data["relevance_score"],
                        "keywords": page_data["keywords"]
                    })
        except:
            pass
    
    def _extract_content(self, soup: BeautifulSoup, query: str) -> Dict[str, Any]:
        """Extrait et analyse le contenu d'une page"""
        # Titre
        title = ""
        if soup.title:
            title = soup.title.string or ""
        
        # Texte principal
        for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
            tag.decompose()
        
        text = soup.get_text(separator=' ', strip=True)
        
        # Mots-clés
        keywords = self._extract_keywords(text)
        
        # Score de pertinence
        relevance = self._calculate_relevance(text, query)
        
        return {
            "title": title,
            "content": text,
            "keywords": keywords,
            "relevance_score": relevance
        }
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extrait les mots-clés importants"""
        # Mots courants à ignorer
        stopwords = {'le', 'la', 'les', 'un', 'une', 'des', 'de', 'du', 'et', 'ou', 'mais'}
        
        words = re.findall(r'\b[a-zàéèêëïôùû]{4,}\b', text.lower())
        word_freq = defaultdict(int)
        
        for word in words:
            if word not in stopwords:
                word_freq[word] += 1
        
        # Top 10 mots
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, _ in sorted_words[:10]]
    
    def _calculate_relevance(self, text: str, query: str) -> float:
        """Calcule le score de pertinence"""
        text_lower = text.lower()
        query_lower = query.lower()
        query_words = query_lower.split()
        
        # Compter les occurrences
        score = 0.0
        for word in query_words:
            if len(word) > 2:
                count = text_lower.count(word)
                score += count * len(word) / 100
        
        return min(score, 1.0)
    
    async def _find_related_content(self, query: str) -> List[Dict[str, str]]:
        """Trouve du contenu connexe"""
        related = []
        
        # Suggestions basées sur les résultats
        domains = set()
        for result in self.search_results[:5]:
            domain = urlparse(result["url"]).netloc
            if domain not in domains:
                domains.add(domain)
                related.append({
                    "domain": domain,
                    "url": result["url"],
                    "relevance": "high"
                })
        
        return related[:5]
    
    def _generate_summary(self, query: str) -> str:
        """Génère un résumé des résultats"""
        if not self.search_results:
            return f"Aucun résultat trouvé pour '{query}'"
        
        top_results = sorted(self.search_results, 
                           key=lambda x: x.get("relevance", 0), 
                           reverse=True)[:3]
        
        summary = f"Recherche pour '{query}' - {len(self.search_results)} résultats pertinents trouvés.\n"
        summary += f"Pages analysées: {len(self.visited_urls)}.\n\n"
        summary += "Top 3 résultats:\n"
        
        for i, result in enumerate(top_results, 1):
            summary += f"{i}. {result.get('title', 'Sans titre')} (pertinence: {result.get('relevance', 0):.2f})\n"
        
        return summary


# Instance globale
navigator = WebNavigator()


async def navigate_web(query: str, start_url: Optional[str] = None, 
                      depth: int = 2) -> Dict[str, Any]:
    """
    Fonction principale de navigation web
    
    Args:
        query: Requête de recherche
        start_url: URL de départ (optionnel)
        depth: Profondeur de recherche (1-3)
    
    Returns:
        Résultats de recherche structurés
    """
    return await navigator.smart_search(query, start_url, depth)
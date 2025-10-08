"""
Web Navigator - Production Ready
✅ Recherche web (SearXNG, DuckDuckGo, Wikipedia)
✅ Extraction de contenu de pages spécifiques
✅ Détection automatique d'URLs
✅ Extraction intelligente de sections
"""

import httpx
import os
from typing import Dict, Any, Optional, List
from bs4 import BeautifulSoup
import re
import logging
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)

SEARXNG_URL = os.getenv("SEARXNG_URL", "http://searxng:8080")


async def navigate_web(query: str, 
                      start_url: Optional[str] = None,
                      depth: int = 2) -> Dict[str, Any]:
    """
    Navigation web intelligente
    
    Modes:
    1. Si query contient une URL → Fetch et analyse ce site
    2. Si start_url fourni → Fetch ce site
    3. Sinon → Recherche web normale
    
    Args:
        query: Recherche OU URL à analyser
        start_url: URL optionnelle à visiter
        depth: Profondeur (non utilisé pour l'instant)
    
    Returns:
        Résultats de recherche OU contenu extrait du site
    """
    
    # ====================================================
    # MODE 1: DÉTECTION AUTOMATIQUE D'URL DANS LA QUERY
    # ====================================================
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    urls_found = re.findall(url_pattern, query)
    
    if urls_found or start_url:
        target_url = urls_found[0] if urls_found else start_url
        logger.info(f"🌐 Mode: Fetch URL - {target_url}")
        
        # Déterminer le contexte/focus de la recherche
        focus = _determine_focus(query)
        
        return await _fetch_and_analyze_website(target_url, focus, query)
    
    # ====================================================
    # MODE 2: RECHERCHE WEB NORMALE
    # ====================================================
    logger.info(f"🔍 Mode: Web Search - {query}")
    
    # Niveau 1: SearXNG (local, docker)
    try:
        logger.info("Trying SearXNG...")
        result = await _search_searxng(query)
        if result.get("success"):
            logger.info("✅ SearXNG OK")
            return result
    except Exception as e:
        logger.warning(f"⚠️ SearXNG failed: {e}")
    
    # Niveau 2: DuckDuckGo (gratuit, sans clé)
    try:
        logger.info("Trying DuckDuckGo...")
        result = await _search_duckduckgo(query)
        if result.get("success"):
            logger.info("✅ DuckDuckGo OK")
            return result
    except Exception as e:
        logger.warning(f"⚠️ DuckDuckGo failed: {e}")
    
    # Niveau 3: Wikipedia (fallback)
    try:
        logger.info("Trying Wikipedia...")
        result = await _search_wikipedia(query)
        logger.info("✅ Wikipedia OK")
        return result
    except Exception as e:
        logger.error(f"❌ All providers failed: {e}")
        return {
            "success": False,
            "error": "Tous les moteurs de recherche ont échoué",
            "query": query
        }


def _determine_focus(query: str) -> str:
    """Détermine le focus de la recherche dans le contexte"""
    query_lower = query.lower()
    
    if any(kw in query_lower for kw in ['propos', 'about', 'qui', 'what', 'entreprise', 'company']):
        return 'about'
    elif any(kw in query_lower for kw in ['service', 'offre', 'produit', 'product']):
        return 'services'
    elif any(kw in query_lower for kw in ['contact', 'email', 'phone', 'adresse']):
        return 'contact'
    elif any(kw in query_lower for kw in ['équipe', 'team', 'membres']):
        return 'team'
    else:
        return 'general'


async def _fetch_and_analyze_website(url: str, focus: str = 'general', 
                                     context: str = "") -> Dict[str, Any]:
    """
    Récupère et analyse un site web spécifique
    
    Args:
        url: URL du site à analyser
        focus: Section à chercher (about, services, contact, general)
        context: Contexte de la requête originale
    
    Returns:
        Analyse complète du site
    """
    try:
        logger.info(f"🔍 Fetching and analyzing: {url} (focus: {focus})")
        
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=20.0
        ) as client:
            response = await client.get(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7"
                }
            )
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "mode": "fetch_url",
                    "error": f"HTTP {response.status_code}",
                    "url": url
                }
            
            # Parser le HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Nettoyer les éléments inutiles
            for tag in soup(['script', 'style', 'nav', 'footer', 'iframe', 
                           'noscript', 'header', 'aside', 'button']):
                tag.decompose()
            
            # Extraire les informations de base
            analysis = {
                "success": True,
                "mode": "fetch_url",
                "url": url,
                "title": _extract_title(soup),
                "description": _extract_meta_description(soup),
                "language": _detect_language(soup),
            }
            
            # Extraction selon le focus
            if focus == 'about':
                analysis["about_section"] = _extract_about_section(soup)
                analysis["company_info"] = _extract_company_info(soup)
                
            elif focus == 'services':
                analysis["services"] = _extract_services(soup)
                
            elif focus == 'contact':
                analysis["contact_info"] = _extract_contact_info(soup, response.text)
                
            elif focus == 'team':
                analysis["team_info"] = _extract_team_info(soup)
                
            else:  # general
                # Extraire tout
                analysis["about_section"] = _extract_about_section(soup)
                analysis["services"] = _extract_services(soup)
                analysis["contact_info"] = _extract_contact_info(soup, response.text)
                analysis["main_content"] = _extract_main_content(soup)[:2000]
            
            # Liens importants
            analysis["important_links"] = _extract_important_links(soup, url)
            
            # Générer un résumé
            analysis["summary"] = _generate_summary(analysis, focus)
            
            logger.info(f"✅ Analysis complete: {len(str(analysis))} bytes")
            return analysis
            
    except httpx.TimeoutException:
        logger.error(f"⏱️ Timeout fetching {url}")
        return {
            "success": False,
            "mode": "fetch_url",
            "error": "Le site met trop de temps à répondre (timeout)",
            "url": url
        }
    except httpx.RequestError as e:
        logger.error(f"🌐 Network error fetching {url}: {e}")
        return {
            "success": False,
            "mode": "fetch_url",
            "error": f"Erreur réseau: {str(e)}",
            "url": url
        }
    except Exception as e:
        logger.error(f"❌ Error analyzing {url}: {e}", exc_info=True)
        return {
            "success": False,
            "mode": "fetch_url",
            "error": str(e),
            "url": url
        }


# ====================================================
# FONCTIONS D'EXTRACTION
# ====================================================

def _extract_title(soup: BeautifulSoup) -> str:
    """Extrait le titre du site"""
    # 1. Title tag
    if soup.title and soup.title.string:
        return soup.title.string.strip()
    
    # 2. H1
    h1 = soup.find('h1')
    if h1:
        return h1.get_text(strip=True)
    
    # 3. meta og:title
    og_title = soup.find('meta', property='og:title')
    if og_title and og_title.get('content'):
        return og_title['content'].strip()
    
    return "Titre non trouvé"


def _extract_meta_description(soup: BeautifulSoup) -> str:
    """Extrait la meta description"""
    # 1. meta description
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    if meta_desc and meta_desc.get('content'):
        return meta_desc['content'].strip()
    
    # 2. meta og:description
    og_desc = soup.find('meta', property='og:description')
    if og_desc and og_desc.get('content'):
        return og_desc['content'].strip()
    
    # 3. Premier paragraphe
    first_p = soup.find('p')
    if first_p:
        return first_p.get_text(strip=True)[:200]
    
    return "Description non trouvée"


def _detect_language(soup: BeautifulSoup) -> str:
    """Détecte la langue du site"""
    html_tag = soup.find('html')
    if html_tag and html_tag.get('lang'):
        return html_tag['lang']
    return "fr"  # défaut


def _extract_about_section(soup: BeautifulSoup) -> Optional[str]:
    """Extrait la section À propos"""
    
    about_keywords = [
        'about', 'à propos', 'qui sommes', 'notre entreprise', 
        'our company', 'notre histoire', 'our story', 'mission',
        'vision', 'valeurs', 'values', 'qui nous sommes'
    ]
    
    # 1. Chercher par ID/classe
    for keyword in about_keywords:
        element = soup.find(id=re.compile(keyword, re.I)) or \
                 soup.find(class_=re.compile(keyword, re.I))
        if element:
            text = element.get_text(separator='\n', strip=True)
            if len(text) > 50:  # Éviter les faux positifs
                return text[:2500]
    
    # 2. Chercher dans les headings
    for heading in soup.find_all(['h1', 'h2', 'h3', 'h4']):
        heading_text = heading.get_text(strip=True).lower()
        if any(keyword in heading_text for keyword in about_keywords):
            # Récupérer le contenu suivant
            content_parts = [heading.get_text(strip=True)]
            for sibling in heading.find_next_siblings(['p', 'div', 'ul', 'section'], limit=20):
                text = sibling.get_text(strip=True)
                if len(text) > 20:  # Éviter les éléments vides
                    content_parts.append(text)
                if len('\n'.join(content_parts)) > 2000:
                    break
            
            result = '\n\n'.join(content_parts)
            if len(result) > 100:
                return result[:2500]
    
    # 3. Chercher dans les liens (peut indiquer une page à visiter)
    for link in soup.find_all('a', href=True):
        link_text = link.get_text(strip=True).lower()
        href = link['href'].lower()
        if any(keyword in link_text or keyword in href for keyword in about_keywords):
            return f"ℹ️ Section 'À propos' potentiellement disponible sur : {link['href']}"
    
    return None


def _extract_company_info(soup: BeautifulSoup) -> Dict[str, Any]:
    """Extrait les infos basiques de l'entreprise"""
    info = {}
    
    # Nom de l'entreprise
    org_schema = soup.find('script', type='application/ld+json')
    if org_schema:
        try:
            import json
            data = json.loads(org_schema.string)
            if isinstance(data, dict):
                info['name'] = data.get('name', '')
                info['type'] = data.get('@type', '')
        except:
            pass
    
    # Meta tags
    og_site_name = soup.find('meta', property='og:site_name')
    if og_site_name:
        info['name'] = og_site_name.get('content', '')
    
    return info if info else None


def _extract_services(soup: BeautifulSoup) -> Optional[str]:
    """Extrait la section Services"""
    
    service_keywords = [
        'service', 'solution', 'offre', 'produit', 'product',
        'nos services', 'our services', 'what we do', 'ce que nous faisons'
    ]
    
    # Même logique que about
    for keyword in service_keywords:
        element = soup.find(id=re.compile(keyword, re.I)) or \
                 soup.find(class_=re.compile(keyword, re.I))
        if element:
            text = element.get_text(separator='\n', strip=True)
            if len(text) > 50:
                return text[:2000]
    
    for heading in soup.find_all(['h2', 'h3', 'h4']):
        heading_text = heading.get_text(strip=True).lower()
        if any(keyword in heading_text for keyword in service_keywords):
            content_parts = []
            for sibling in heading.find_next_siblings(['p', 'ul', 'div'], limit=15):
                text = sibling.get_text(strip=True)
                if len(text) > 20:
                    content_parts.append(text)
            
            result = '\n\n'.join(content_parts)
            if len(result) > 100:
                return result[:2000]
    
    return None


def _extract_contact_info(soup: BeautifulSoup, html_text: str) -> Optional[Dict[str, Any]]:
    """Extrait les informations de contact"""
    contact = {}
    
    # Emails
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, html_text)
    # Filtrer les emails courants/spam
    emails = [e for e in emails if not any(spam in e.lower() for spam in 
              ['example', 'test', 'spam', 'noreply', 'no-reply'])]
    if emails:
        contact['emails'] = list(set(emails))[:5]
    
    # Téléphones
    phone_pattern = r'(\+?\d{1,3}[-.\s]?)?(\(?\d{2,4}\)?[-.\s]?){1,4}\d{2,4}'
    phones = re.findall(phone_pattern, html_text)
    if phones:
        # Nettoyer et formatter
        clean_phones = []
        for phone in phones[:5]:
            if isinstance(phone, tuple):
                phone_str = ''.join(str(p) for p in phone if p)
            else:
                phone_str = str(phone)
            # Garder seulement si ressemble à un vrai numéro
            if len(phone_str.replace(' ', '').replace('-', '')) >= 8:
                clean_phones.append(phone_str)
        if clean_phones:
            contact['phones'] = clean_phones[:3]
    
    # Adresse physique
    address_element = soup.find(class_=re.compile('address|location|adresse', re.I))
    if address_element:
        contact['address'] = address_element.get_text(strip=True)
    
    # Réseaux sociaux
    social_links = []
    social_domains = ['facebook.com', 'twitter.com', 'linkedin.com', 
                     'instagram.com', 'youtube.com', 'github.com']
    for link in soup.find_all('a', href=True):
        href = link['href'].lower()
        if any(domain in href for domain in social_domains):
            social_links.append(link['href'])
    if social_links:
        contact['social_media'] = list(set(social_links))[:5]
    
    return contact if contact else None


def _extract_team_info(soup: BeautifulSoup) -> Optional[str]:
    """Extrait les infos sur l'équipe"""
    team_keywords = ['équipe', 'team', 'membres', 'members', 'staff']
    
    for keyword in team_keywords:
        element = soup.find(id=re.compile(keyword, re.I)) or \
                 soup.find(class_=re.compile(keyword, re.I))
        if element:
            return element.get_text(separator='\n', strip=True)[:1500]
    
    return None


def _extract_main_content(soup: BeautifulSoup) -> str:
    """Extrait le contenu principal"""
    # Chercher balises sémantiques
    main = soup.find('main') or \
           soup.find('article') or \
           soup.find('div', class_=re.compile('content|main|body', re.I)) or \
           soup.find('body')
    
    if main:
        text = main.get_text(separator='\n', strip=True)
    else:
        text = soup.get_text(separator='\n', strip=True)
    
    # Nettoyer
    lines = [line.strip() for line in text.split('\n') if line.strip() and len(line.strip()) > 10]
    return '\n'.join(lines)


def _extract_important_links(soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
    """Extrait les liens importants (About, Contact, etc.)"""
    important_keywords = ['about', 'propos', 'contact', 'service', 'equipe', 'team']
    links = []
    
    for link in soup.find_all('a', href=True):
        href = link['href']
        text = link.get_text(strip=True).lower()
        
        if any(keyword in text or keyword in href.lower() for keyword in important_keywords):
            # Convertir en URL absolue
            absolute_url = urljoin(base_url, href)
            links.append({
                "text": link.get_text(strip=True),
                "url": absolute_url
            })
    
    return links[:10]  # Limiter à 10 liens


def _generate_summary(analysis: Dict[str, Any], focus: str) -> str:
    """Génère un résumé de l'analyse"""
    parts = []
    
    parts.append(f"📊 Analyse du site : {analysis['title']}")
    
    if analysis.get('description'):
        parts.append(f"📝 {analysis['description'][:200]}")
    
    if analysis.get('about_section'):
        about_preview = analysis['about_section'][:150]
        parts.append(f"\nℹ️ À propos : {about_preview}...")
    
    if analysis.get('services'):
        parts.append(f"\n🛠️ Services trouvés")
    
    if analysis.get('contact_info'):
        contact = analysis['contact_info']
        contact_parts = []
        if contact.get('emails'):
            contact_parts.append(f"{len(contact['emails'])} email(s)")
        if contact.get('phones'):
            contact_parts.append(f"{len(contact['phones'])} téléphone(s)")
        if contact_parts:
            parts.append(f"\n📞 Contact : {', '.join(contact_parts)}")
    
    if analysis.get('important_links'):
        parts.append(f"\n🔗 {len(analysis['important_links'])} liens importants trouvés")
    
    return '\n'.join(parts)


# ====================================================
# FONCTIONS DE RECHERCHE WEB
# ====================================================

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
                "mode": "search",
                "provider": "searxng",
                "query": query,
                "results_count": len(results),
                "results": results
            }
        
        return {"success": False}


async def _search_duckduckgo(query: str) -> Dict[str, Any]:
    """Recherche DuckDuckGo"""
    async with httpx.AsyncClient() as client:
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
            
            if data.get("AbstractText"):
                results.append({
                    "title": data.get("Heading", query),
                    "url": data.get("AbstractURL"),
                    "snippet": data.get("AbstractText"),
                    "source": data.get("AbstractSource")
                })
            
            for topic in data.get("RelatedTopics", [])[:8]:
                if isinstance(topic, dict) and topic.get("Text"):
                    results.append({
                        "title": topic.get("Text", "")[:100],
                        "url": topic.get("FirstURL"),
                        "snippet": topic.get("Text", "")
                    })
            
            if results:
                return {
                    "success": True,
                    "mode": "search",
                    "provider": "duckduckgo",
                    "query": query,
                    "results_count": len(results),
                    "results": results
                }
        
        return {"success": False}


async def _search_wikipedia(query: str) -> Dict[str, Any]:
    """Recherche Wikipedia"""
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
                title = item.get("title", "")
                results.append({
                    "title": title,
                    "url": f"https://fr.wikipedia.org/wiki/{title.replace(' ', '_')}",
                    "snippet": item.get("snippet", "").replace('<span class="searchmatch">', '').replace('</span>', '')
                })
            
            return {
                "success": True,
                "mode": "search",
                "provider": "wikipedia",
                "query": query,
                "results_count": len(results),
                "results": results,
                "note": "Résultats Wikipedia (fallback)"
            }
        
        return {"success": False}
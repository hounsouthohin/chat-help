"""
Outils d'apprentissage et de motivation
"""

import random
import httpx
from typing import Dict, Any


async def explain_concept(concept: str, level: str = "intermediaire") -> Dict[str, Any]:
    """
    Explique un concept informatique via une API externe
    Utilise une vraie API d'apprentissage
    """
    try:
        # Utilisation de l'API Wikipedia ou d'autres ressources éducatives
        async with httpx.AsyncClient() as client:
            # Recherche sur Wikipedia
            wiki_url = "https://fr.wikipedia.org/w/api.php"
            params = {
                "action": "query",
                "format": "json",
                "prop": "extracts|links",
                "titles": concept,
                "exintro": True,
                "explaintext": True,
                "utf8": 1
            }
            
            response = await client.get(wiki_url, params=params)
            data = response.json()
            
            pages = data.get("query", {}).get("pages", {})
            explanation = ""
            links = []
            
            for page_id, page_data in pages.items():
                if page_id != "-1":
                    explanation = page_data.get("extract", "")
                    links = [link.get("title") for link in page_data.get("links", [])[:5]]
            
            # Rechercher des exemples sur GitHub
            github_examples = await search_github_examples(client, concept)
            
            # Adapter au niveau
            if level == "debutant":
                intro = "🎓 Explication simple : "
            elif level == "avance":
                intro = "🔬 Explication avancée : "
            else:
                intro = "📚 Explication : "
            
            return {
                "success": True,
                "concept": concept,
                "level": level,
                "explanation": intro + explanation[:800],
                "related_topics": links,
                "examples": github_examples,
                "resources": [
                    f"https://fr.wikipedia.org/wiki/{concept.replace(' ', '_')}",
                    f"https://github.com/search?q={concept}&type=repositories"
                ]
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Erreur: {str(e)}",
            "concept": concept
        }


async def search_github_examples(client: httpx.AsyncClient, concept: str) -> list:
    """Recherche des exemples sur GitHub"""
    try:
        headers = {"Accept": "application/vnd.github.v3+json"}
        url = f"https://api.github.com/search/repositories?q={concept}+language:python&sort=stars&per_page=3"
        
        response = await client.get(url, headers=headers)
        data = response.json()
        
        examples = []
        for item in data.get("items", [])[:3]:
            examples.append({
                "name": item["name"],
                "description": item["description"],
                "url": item["html_url"],
                "stars": item["stargazers_count"]
            })
        
        return examples
    except:
        return []


async def get_joke(language: str = "fr") -> Dict[str, Any]:
    """
    Récupère une blague via une API externe
    """
    try:
        async with httpx.AsyncClient() as client:
            if language == "fr":
                # API de blagues en français
                response = await client.get("https://www.blagues-api.fr/api/random", 
                                           headers={"Accept": "application/json"})
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "joke": data.get("joke", ""),
                        "answer": data.get("answer", ""),
                        "language": "fr"
                    }
            else:
                # API de blagues en anglais
                response = await client.get("https://official-joke-api.appspot.com/jokes/programming/random")
                if response.status_code == 200:
                    data = response.json()[0]
                    return {
                        "success": True,
                        "setup": data.get("setup", ""),
                        "punchline": data.get("punchline", ""),
                        "language": "en"
                    }
        
        # Fallback si les APIs ne fonctionnent pas
        return get_fallback_joke(language)
        
    except:
        return get_fallback_joke(language)


def get_fallback_joke(language: str) -> Dict[str, Any]:
    """Blagues de secours"""
    jokes_fr = [
        {"joke": "Pourquoi les développeurs préfèrent-ils le mode sombre ?", 
         "answer": "Parce que la lumière attire les bugs ! 🐛"},
        {"joke": "Comment appelle-t-on un informaticien qui sort dehors ?", 
         "answer": "Un bug rare ! 🌞"}
    ]
    
    jokes_en = [
        {"setup": "Why do programmers prefer dark mode?", 
         "punchline": "Because light attracts bugs! 🐛"},
        {"setup": "How many programmers does it take to change a lightbulb?", 
         "punchline": "None, that's a hardware problem! 💡"}
    ]
    
    joke = random.choice(jokes_fr if language == "fr" else jokes_en)
    return {"success": True, **joke, "language": language}


async def motivational_quote() -> Dict[str, Any]:
    """
    Récupère une citation motivante via API
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("https://api.quotable.io/random?tags=technology|success")
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "quote": data.get("content", ""),
                    "author": data.get("author", ""),
                    "tags": data.get("tags", [])
                }
    except:
        pass
    
    # Citations de secours
    quotes = [
        {"quote": "Le code est comme l'humour. Quand vous devez l'expliquer, c'est mauvais.", 
         "author": "Cory House"},
        {"quote": "D'abord, résolvez le problème. Ensuite, écrivez le code.", 
         "author": "John Johnson"},
        {"quote": "Tout langage de programmation est parfait pour écrire de mauvais programmes.", 
         "author": "Herbert Mayer"}
    ]
    
    quote = random.choice(quotes)
    return {"success": True, **quote, "tags": ["motivation", "programming"]}
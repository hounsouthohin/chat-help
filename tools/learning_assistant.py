"""
Learning Assistant - 100% Gratuit
APIs sans clé + fallback local
"""

import httpx
import random
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


# ===== BASES DE DONNÉES LOCALES =====

JOKES_DB = {
    "fr": [
        {
            "joke": "Pourquoi les développeurs préfèrent-ils le mode sombre ?",
            "answer": "Parce que la lumière attire les bugs ! 🐛"
        },
        {
            "joke": "Comment appelle-t-on un informaticien qui sort dehors ?",
            "answer": "Un bug rare ! 🌞"
        },
        {
            "joke": "Pourquoi les programmeurs confondent-ils Halloween et Noël ?",
            "answer": "Parce que Oct 31 = Dec 25 ! 🎃🎄"
        },
        {
            "joke": "Qu'est-ce qu'un développeur sans café ?",
            "answer": "Un programme en mode veille ! ☕"
        },
        {
            "joke": "Comment un développeur répare-t-il sa voiture ?",
            "answer": "Il la redémarre ! 🚗"
        }
    ],
    "en": [
        {
            "setup": "Why do programmers prefer dark mode?",
            "punchline": "Because light attracts bugs! 🐛"
        },
        {
            "setup": "How many programmers does it take to change a lightbulb?",
            "punchline": "None, that's a hardware problem! 💡"
        },
        {
            "setup": "Why do Java developers wear glasses?",
            "punchline": "Because they can't C# ! 👓"
        }
    ]
}

QUOTES_DB = [
    {
        "quote": "Le code est comme l'humour. Quand vous devez l'expliquer, c'est mauvais.",
        "author": "Cory House"
    },
    {
        "quote": "D'abord, résolvez le problème. Ensuite, écrivez le code.",
        "author": "John Johnson"
    },
    {
        "quote": "La simplicité est la sophistication suprême.",
        "author": "Leonardo da Vinci"
    },
    {
        "quote": "Le meilleur code est celui que vous n'avez pas besoin d'écrire.",
        "author": "Jeff Atwood"
    },
    {
        "quote": "Les programmes doivent être écrits pour être lus par des humains, et seulement accessoirement pour être exécutés par des machines.",
        "author": "Harold Abelson"
    }
]

LEARNING_PATHS_DB = {
    "python": {
        "beginner": [
            {"week": 1, "topic": "Variables et types de données", "hours": 5},
            {"week": 2, "topic": "Structures de contrôle (if, for, while)", "hours": 5},
            {"week": 3, "topic": "Fonctions et modules", "hours": 5},
            {"week": 4, "topic": "Listes et dictionnaires", "hours": 5},
            {"week": 5, "topic": "Programmation orientée objet", "hours": 8},
            {"week": 6, "topic": "Gestion des fichiers", "hours": 5},
            {"week": 7, "topic": "Exceptions et débogage", "hours": 5},
            {"week": 8, "topic": "Projet final", "hours": 10}
        ],
        "intermediate": [
            {"week": 1, "topic": "Compréhensions et générateurs", "hours": 6},
            {"week": 2, "topic": "Décorateurs et contextes", "hours": 6},
            {"week": 3, "topic": "Tests unitaires (pytest)", "hours": 6},
            {"week": 4, "topic": "Async/await et asyncio", "hours": 8},
            {"week": 5, "topic": "APIs REST avec FastAPI", "hours": 8},
            {"week": 6, "topic": "Bases de données (SQLAlchemy)", "hours": 8}
        ],
        "advanced": [
            {"week": 1, "topic": "Métaprogrammation", "hours": 10},
            {"week": 2, "topic": "Performance et profiling", "hours": 10},
            {"week": 3, "topic": "Design patterns", "hours": 10},
            {"week": 4, "topic": "Architecture microservices", "hours": 12}
        ]
    },
    "javascript": {
        "beginner": [
            {"week": 1, "topic": "Variables, types et opérateurs", "hours": 5},
            {"week": 2, "topic": "Fonctions et scope", "hours": 5},
            {"week": 3, "topic": "DOM et événements", "hours": 6},
            {"week": 4, "topic": "Arrays et objets", "hours": 5},
            {"week": 5, "topic": "ES6+ features", "hours": 6},
            {"week": 6, "topic": "Async/Promises", "hours": 6},
            {"week": 7, "topic": "Fetch et APIs", "hours": 6},
            {"week": 8, "topic": "Projet final", "hours": 10}
        ]
    }
}


# ===== EXPLAIN CONCEPT =====

async def explain_concept(concept: str, level: str = "intermediaire") -> Dict[str, Any]:
    """
    Explique un concept - Version gratuite
    Niveau 1: Wikipedia API (gratuit)
    Niveau 2: GitHub search (gratuit)
    Niveau 3: Base de données locale
    """
    
    # NIVEAU 1 : Wikipedia (toujours gratuit)
    try:
        logger.info(f"📚 Recherche Wikipedia: {concept}")
        result = await _explain_wikipedia(concept, level)
        if result.get("success"):
            logger.info("✅ Wikipedia OK")
            return result
    except Exception as e:
        logger.warning(f"❌ Wikipedia failed: {e}")
    
    # NIVEAU 2 : GitHub (gratuit, pas de clé nécessaire)
    try:
        logger.info(f"🔍 Recherche GitHub: {concept}")
        result = await _explain_github(concept, level)
        if result.get("success"):
            logger.info("✅ GitHub OK")
            return result
    except Exception as e:
        logger.warning(f"❌ GitHub failed: {e}")
    
    # NIVEAU 3 : Réponse générique locale
    return {
        "success": True,
        "provider": "local",
        "concept": concept,
        "level": level,
        "explanation": f"Concept: {concept}. Pour une explication détaillée, consultez la documentation officielle.",
        "resources": [
            f"https://fr.wikipedia.org/wiki/{concept.replace(' ', '_')}",
            f"https://github.com/search?q={concept}",
            f"https://stackoverflow.com/search?q={concept}"
        ]
    }


async def _explain_wikipedia(concept: str, level: str) -> Dict[str, Any]:
    """Wikipedia API (100% gratuit)"""
    async with httpx.AsyncClient() as client:
        # Recherche
        response = await client.get(
            "https://fr.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "format": "json",
                "prop": "extracts|links",
                "titles": concept,
                "exintro": True,
                "explaintext": True,
                "utf8": 1
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            pages = data.get("query", {}).get("pages", {})
            
            for page_id, page_data in pages.items():
                if page_id != "-1":
                    explanation = page_data.get("extract", "")
                    links = [link.get("title") for link in page_data.get("links", [])[:5]]
                    
                    # Adapter au niveau
                    if level == "debutant":
                        intro = "🎓 Explication simple : "
                    elif level == "avance":
                        intro = "🔬 Explication avancée : "
                    else:
                        intro = "📚 Explication : "
                    
                    return {
                        "success": True,
                        "provider": "wikipedia",
                        "concept": concept,
                        "level": level,
                        "explanation": intro + explanation[:800],
                        "related_topics": links,
                        "url": f"https://fr.wikipedia.org/wiki/{concept.replace(' ', '_')}"
                    }
        
        return {"success": False}


async def _explain_github(concept: str, level: str) -> Dict[str, Any]:
    """GitHub API (gratuit sans authentification, limite: 60 req/h)"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.github.com/search/repositories",
            params={
                "q": f"{concept} language:python",
                "sort": "stars",
                "per_page": 5
            },
            headers={"Accept": "application/vnd.github.v3+json"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            
            examples = []
            for item in data.get("items", []):
                examples.append({
                    "name": item["name"],
                    "description": item["description"],
                    "url": item["html_url"],
                    "stars": item["stargazers_count"],
                    "language": item["language"]
                })
            
            return {
                "success": True,
                "provider": "github",
                "concept": concept,
                "level": level,
                "explanation": f"Voici {len(examples)} projets populaires sur GitHub relatifs à '{concept}':",
                "examples": examples,
                "resources": [item["url"] for item in examples]
            }
        
        return {"success": False}


# ===== GET JOKE =====

async def get_joke(language: str = "fr") -> Dict[str, Any]:
    """
    Blague aléatoire - Version gratuite
    Niveau 1: API gratuite (sans clé)
    Niveau 2: Base de données locale
    """
    
    # NIVEAU 1 : API officielle JokeAPI (gratuit, sans clé)
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://v2.jokeapi.dev/joke/Programming",
                params={
                    "lang": "en" if language == "en" else "fr",
                    "type": "single"
                },
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "provider": "jokeapi",
                    "joke": data.get("joke"),
                    "language": language
                }
    except:
        pass
    
    # NIVEAU 2 : Base de données locale (toujours disponible)
    jokes = JOKES_DB.get(language, JOKES_DB["fr"])
    joke = random.choice(jokes)
    
    return {
        "success": True,
        "provider": "local",
        **joke,
        "language": language
    }


# ===== MOTIVATIONAL QUOTE =====

async def motivational_quote() -> Dict[str, Any]:
    """
    Citation motivante - Version gratuite
    Niveau 1: API Quotable (gratuit)
    Niveau 2: Base de données locale
    """
    
    # NIVEAU 1 : Quotable API (100% gratuit)
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.quotable.io/random",
                params={"tags": "technology|success"},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "provider": "quotable",
                    "quote": data.get("content"),
                    "author": data.get("author"),
                    "tags": data.get("tags", [])
                }
    except:
        pass
    
    # NIVEAU 2 : Base locale
    quote = random.choice(QUOTES_DB)
    return {
        "success": True,
        "provider": "local",
        **quote,
        "tags": ["motivation", "programming"]
    }


# ===== CREATE LEARNING PATH =====

async def create_learning_path(topic: str, 
                               level: str = "beginner",
                               goals: List[str] = None,
                               time_per_week: int = 10) -> Dict[str, Any]:
    """
    Créer un parcours d'apprentissage
    Version gratuite avec base de données locale
    """
    
    topic_lower = topic.lower()
    
    # Chercher dans la base locale
    if topic_lower in LEARNING_PATHS_DB:
        path = LEARNING_PATHS_DB[topic_lower].get(level, LEARNING_PATHS_DB[topic_lower].get("beginner"))
        
        # Ajuster selon time_per_week
        adjusted_path = []
        for item in path:
            adjusted_item = item.copy()
            # Adapter la durée
            weeks_needed = max(1, adjusted_item["hours"] // time_per_week)
            adjusted_item["weeks_needed"] = weeks_needed
            adjusted_path.append(adjusted_item)
        
        # Chercher des ressources gratuites
        resources = await _find_free_resources(topic)
        
        return {
            "success": True,
            "provider": "local_curriculum",
            "topic": topic,
            "level": level,
            "total_weeks": len(adjusted_path),
            "time_per_week": time_per_week,
            "path": adjusted_path,
            "resources": resources,
            "goals": goals or [f"Maîtriser {topic}"],
            "next_steps": [
                "📚 Suivre le curriculum semaine par semaine",
                "💻 Pratiquer avec des projets personnels",
                "🤝 Rejoindre une communauté de développeurs"
            ]
        }
    
    # Générer un parcours générique
    return {
        "success": True,
        "provider": "generic",
        "topic": topic,
        "level": level,
        "message": f"Parcours générique pour {topic}",
        "path": [
            {"week": 1, "topic": "Fondamentaux", "hours": time_per_week},
            {"week": 2, "topic": "Pratique de base", "hours": time_per_week},
            {"week": 3, "topic": "Concepts intermédiaires", "hours": time_per_week},
            {"week": 4, "topic": "Projet pratique", "hours": time_per_week},
        ],
        "resources": await _find_free_resources(topic)
    }


async def _find_free_resources(topic: str) -> List[Dict[str, str]]:
    """Trouve des ressources gratuites"""
    resources = []
    
    # Ressources génériques
    resources.append({
        "name": "Documentation officielle",
        "url": f"https://www.google.com/search?q={topic}+official+documentation",
        "type": "docs"
    })
    
    resources.append({
        "name": "Tutoriels YouTube",
        "url": f"https://www.youtube.com/results?search_query={topic}+tutorial",
        "type": "video"
    })
    
    resources.append({
        "name": "Articles sur Dev.to",
        "url": f"https://dev.to/search?q={topic}",
        "type": "articles"
    })
    
    # Essayer de trouver sur GitHub
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.github.com/search/repositories",
                params={
                    "q": f"{topic} awesome",
                    "sort": "stars",
                    "per_page": 3
                },
                timeout=5
            )
            
            if response.status_code == 200:
                for item in response.json().get("items", []):
                    resources.append({
                        "name": item["name"],
                        "url": item["html_url"],
                        "type": "github",
                        "stars": item["stargazers_count"]
                    })
    except:
        pass
    
    return resources


# ===== EXPLAIN ADVANCED =====

async def explain_advanced(concept: str,
                          level: str = "intermediate",
                          with_examples: bool = True,
                          with_analogies: bool = True) -> Dict[str, Any]:
    """
    Explication avancée avec exemples et analogies
    """
    
    # Obtenir l'explication de base
    basic_explanation = await explain_concept(concept, level)
    
    result = {
        **basic_explanation,
        "advanced": True
    }
    
    # Ajouter des exemples de code si demandé
    if with_examples:
        result["code_examples"] = await _generate_code_examples(concept)
    
    # Ajouter des analogies si demandé
    if with_analogies:
        result["analogies"] = _generate_analogies(concept)
    
    # Quiz interactif
    result["quiz"] = _generate_quiz(concept)
    
    return result


async def _generate_code_examples(concept: str) -> List[Dict]:
    """Génère des exemples de code"""
    # Pour l'instant, exemples génériques
    return [
        {
            "title": f"Exemple basique de {concept}",
            "code": f"# Exemple pour {concept}\n# TODO: Implémenter",
            "language": "python"
        }
    ]


def _generate_analogies(concept: str) -> List[str]:
    """Génère des analogies"""
    analogies_db = {
        "api": ["Une API c'est comme un serveur au restaurant : vous passez commande (requête) et il vous apporte votre plat (réponse)"],
        "database": ["Une base de données c'est comme une bibliothèque : les livres sont rangés par catégorie pour les retrouver facilement"],
        "git": ["Git c'est comme une machine à remonter le temps pour votre code : vous pouvez revenir en arrière à tout moment"],
    }
    
    concept_lower = concept.lower()
    for key in analogies_db:
        if key in concept_lower:
            return analogies_db[key]
    
    return [f"{concept} peut être comparé à..."]


def _generate_quiz(concept: str) -> Dict:
    """Génère un quiz"""
    return {
        "questions": [
            {
                "question": f"Quelle est la principale utilité de {concept} ?",
                "options": ["Option A", "Option B", "Option C"],
                "correct": 0
            }
        ]
    }
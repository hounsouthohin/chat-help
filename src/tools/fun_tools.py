"""
Outils ludiques pour détendre l'atmosphère
"""

import random
from typing import Dict, Any

async def get_programming_joke(language: str = "fr") -> Dict[str, Any]:
    """
    Retourne une blague de programmation
    """
    
    jokes_fr = [
        {
            "joke": "Pourquoi les programmeurs préfèrent-ils le mode sombre?",
            "punchline": "Parce que la lumière attire les bugs! 🐛"
        },
        {
            "joke": "Comment appelle-t-on un développeur qui ne teste pas son code?",
            "punchline": "Un optimiste! 😄"
        },
        {
            "joke": "Pourquoi les programmeurs confondent-ils Halloween et Noël?",
            "punchline": "Parce que Oct 31 = Dec 25 (en octal)! 🎃🎄"
        },
        {
            "joke": "Un programmeur va au supermarché. Sa femme lui dit: 'Achète du pain, et si ils ont des œufs, prends-en 6.'",
            "punchline": "Il revient avec 6 pains. 'Ils avaient des œufs!' 🍞"
        },
        {
            "joke": "Il y a 10 types de personnes dans le monde...",
            "punchline": "Ceux qui comprennent le binaire et ceux qui ne le comprennent pas! 01"
        },
        {
            "joke": "Pourquoi Java et JavaScript sont comme une voiture et une barre de chocolat?",
            "punchline": "Parce qu'ils n'ont que le nom en commun! ☕🍫"
        },
        {
            "joke": "Un SQL entre dans un bar et voit deux tables...",
            "punchline": "Il s'approche et demande: 'Je peux vous JOIN?' 🍺"
        },
        {
            "joke": "Quelle est la différence entre un développeur junior et un développeur senior?",
            "punchline": "Le senior sait que 'ça marche sur ma machine' n'est PAS une solution! 💻"
        }
    ]
    
    jokes_en = [
        {
            "joke": "Why do programmers always mix up Christmas and Halloween?",
            "punchline": "Because Oct 31 == Dec 25! 🎃🎄"
        },
        {
            "joke": "Why do Java developers wear glasses?",
            "punchline": "Because they can't C#! 👓"
        },
        {
            "joke": "How many programmers does it take to change a light bulb?",
            "punchline": "None, that's a hardware problem! 💡"
        },
        {
            "joke": "A SQL query walks into a bar, walks up to two tables and asks...",
            "punchline": "'Can I JOIN you?' 🍺"
        },
        {
            "joke": "What's a programmer's favorite hangout place?",
            "punchline": "Foo Bar! 🍻"
        }
    ]
    
    jokes = jokes_fr if language == "fr" else jokes_en
    joke = random.choice(jokes)
    
    return {
        "success": True,
        "language": language,
        "joke": joke["joke"],
        "punchline": joke["punchline"],
        "mood_boost": "😄 Prends une pause, tu le mérites!"
    }

async def get_motivational_quote() -> Dict[str, Any]:
    """
    Retourne une citation motivante pour étudiants en informatique
    """
    
    quotes = [
        {
            "quote": "Le code est comme l'humour. Quand tu dois l'expliquer, c'est mauvais.",
            "author": "Cory House",
            "emoji": "💡"
        },
        {
            "quote": "Tout d'abord, résous le problème. Ensuite, écris le code.",
            "author": "John Johnson",
            "emoji": "🎯"
        },
        {
            "quote": "Le meilleur message d'erreur est celui qui ne s'affiche jamais.",
            "author": "Thomas Fuchs",
            "emoji": "✅"
        },
        {
            "quote": "Apprendre à écrire des programmes étire ton esprit et t'aide à mieux penser.",
            "author": "Bill Gates",
            "emoji": "🧠"
        },
        {
            "quote": "La simplicité est l'ultime sophistication.",
            "author": "Leonardo da Vinci",
            "emoji": "🎨"
        },
        {
            "quote": "Le code propre lit toujours comme une prose bien écrite.",
            "author": "Robert C. Martin",
            "emoji": "📖"
        },
        {
            "quote": "Les erreurs ne sont pas des échecs, ce sont des leçons.",
            "author": "Anonyme",
            "emoji": "🌱"
        },
        {
            "quote": "Teste ton code comme si la personne qui le maintiendra était un violent psychopathe qui sait où tu habites.",
            "author": "Martin Golding",
            "emoji": "🧪"
        },
        {
            "quote": "Le débogage est deux fois plus difficile que d'écrire le code. Donc si tu écris le code aussi intelligemment que possible, tu ne seras pas assez intelligent pour le déboguer.",
            "author": "Brian Kernighan",
            "emoji": "🔍"
        },
        {
            "quote": "N'abandonne jamais! Les meilleurs développeurs sont ceux qui persévèrent.",
            "author": "Anonyme",
            "emoji": "💪"
        },
        {
            "quote": "Chaque expert a déjà été un débutant. Continue d'apprendre!",
            "author": "Anonyme",
            "emoji": "🚀"
        },
        {
            "quote": "L'expérience est le nom que chacun donne à ses erreurs.",
            "author": "Oscar Wilde",
            "emoji": "⭐"
        }
    ]
    
    quote = random.choice(quotes)
    
    return {
        "success": True,
        "quote": quote["quote"],
        "author": quote["author"],
        "emoji": quote["emoji"],
        "encouragement": "Continue comme ça, tu fais du super travail! 💪"
    }
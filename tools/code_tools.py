"""
Outils d'analyse et de débogage de code
"""

import re
import httpx
from typing import Dict, Any, Optional
import subprocess
import tempfile
import os


async def analyze_code(code: str, language: str) -> Dict[str, Any]:
    """
    Analyse le code avec des outils externes et APIs
    """
    try:
        analysis = {
            "success": True,
            "language": language,
            "line_count": len(code.split('\n')),
            "issues": [],
            "suggestions": [],
            "metrics": {}
        }
        
        # Analyse Python avec pylint
        if language == "python":
            pylint_results = await run_pylint(code)
            analysis["issues"].extend(pylint_results.get("issues", []))
            analysis["metrics"] = pylint_results.get("metrics", {})
        
        # Analyse via API externe pour détecter les vulnérabilités
        security_check = await check_code_security(code, language)
        if security_check.get("vulnerabilities"):
            analysis["issues"].extend(security_check["vulnerabilities"])
        
        # Suggestions de bonnes pratiques
        best_practices = await get_best_practices(code, language)
        analysis["suggestions"] = best_practices
        
        # Recherche de code similaire sur GitHub
        similar_code = await find_similar_code(code, language)
        analysis["similar_examples"] = similar_code
        
        return analysis
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "language": language
        }


async def run_pylint(code: str) -> Dict[str, Any]:
    """Exécute pylint sur le code Python"""
    try:
        # Créer un fichier temporaire
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        # Exécuter pylint
        result = subprocess.run(
            ['pylint', temp_file, '--output-format=json'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # Nettoyer
        os.unlink(temp_file)
        
        if result.stdout:
            import json
            pylint_output = json.loads(result.stdout)
            
            issues = []
            for item in pylint_output:
                issues.append({
                    "line": item.get("line"),
                    "type": item.get("type"),
                    "message": item.get("message"),
                    "symbol": item.get("symbol")
                })
            
            return {
                "issues": issues,
                "metrics": {"pylint_score": 10.0 - len(issues) * 0.5}
            }
        
        return {"issues": [], "metrics": {}}
        
    except Exception as e:
        return {"issues": [{"message": f"Erreur pylint: {str(e)}"}], "metrics": {}}


async def check_code_security(code: str, language: str) -> Dict[str, Any]:
    """
    Vérifie les vulnérabilités de sécurité via API
    """
    vulnerabilities = []
    
    # Vérifications basiques
    if language == "python":
        if "eval(" in code:
            vulnerabilities.append({
                "severity": "high",
                "message": "Utilisation de eval() détectée - risque d'injection de code",
                "recommendation": "Utiliser ast.literal_eval() ou json.loads()"
            })
        
        if "exec(" in code:
            vulnerabilities.append({
                "severity": "high",
                "message": "Utilisation de exec() - risque de sécurité",
                "recommendation": "Éviter exec() ou utiliser dans un environnement sandboxé"
            })
        
        if re.search(r'password\s*=\s*["\']', code, re.IGNORECASE):
            vulnerabilities.append({
                "severity": "medium",
                "message": "Mot de passe potentiellement hardcodé",
                "recommendation": "Utiliser des variables d'environnement"
            })
    
    return {"vulnerabilities": vulnerabilities}


async def get_best_practices(code: str, language: str) -> list:
    """Suggestions de bonnes pratiques"""
    suggestions = []
    
    if language == "python":
        # Vérifier les conventions PEP 8
        if not re.search(r'""".*"""', code) and "def " in code:
            suggestions.append({
                "type": "documentation",
                "message": "Ajouter des docstrings aux fonctions",
                "priority": "medium"
            })
        
        if "print(" in code and "def " in code:
            suggestions.append({
                "type": "debugging",
                "message": "Utiliser logging au lieu de print() pour le débogage",
                "priority": "low"
            })
        
        # Vérifier la longueur des lignes
        long_lines = [i+1 for i, line in enumerate(code.split('\n')) if len(line) > 79]
        if long_lines:
            suggestions.append({
                "type": "style",
                "message": f"Lignes trop longues (>79 caractères) : {long_lines[:5]}",
                "priority": "low"
            })
    
    return suggestions


async def find_similar_code(code: str, language: str) -> list:
    """Recherche du code similaire sur GitHub"""
    try:
        # Extraire une fonction ou classe représentative
        code_snippet = code[:200].replace('\n', ' ').strip()
        
        async with httpx.AsyncClient() as client:
            headers = {"Accept": "application/vnd.github.v3+json"}
            url = f"https://api.github.com/search/code?q={code_snippet[:50]}&per_page=3"
            
            response = await client.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                examples = []
                for item in data.get("items", [])[:3]:
                    examples.append({
                        "name": item.get("name"),
                        "repository": item.get("repository", {}).get("full_name"),
                        "url": item.get("html_url")
                    })
                
                return examples
    except:
        pass
    
    return []


async def debug_helper(error_message: str, context: Optional[str] = None) -> Dict[str, Any]:
    """
    Aide au débogage en analysant l'erreur via Stack Overflow API
    """
    try:
        # Extraire le type d'erreur
        error_type = extract_error_type(error_message)
        
        # Rechercher sur Stack Overflow
        stackoverflow_solutions = await search_stackoverflow(error_message, error_type)
        
        # Analyses communes d'erreurs
        common_solutions = get_common_solutions(error_type, error_message)
        
        # Rechercher dans la documentation Python si applicable
        doc_links = await get_documentation_links(error_type)
        
        return {
            "success": True,
            "error_type": error_type,
            "error_message": error_message,
            "stackoverflow_solutions": stackoverflow_solutions,
            "common_solutions": common_solutions,
            "documentation": doc_links,
            "context_analysis": analyze_context(context) if context else None
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_message": error_message
        }


def extract_error_type(error_message: str) -> str:
    """Extrait le type d'erreur du message"""
    # Chercher les patterns communs
    patterns = [
        r'(\w+Error):',
        r'(\w+Exception):',
        r'(\w+Warning):'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, error_message)
        if match:
            return match.group(1)
    
    return "UnknownError"


async def search_stackoverflow(error_message: str, error_type: str) -> list:
    """Recherche des solutions sur Stack Overflow"""
    try:
        async with httpx.AsyncClient() as client:
            # API Stack Exchange
            url = "https://api.stackexchange.com/2.3/search/advanced"
            params = {
                "order": "desc",
                "sort": "votes",
                "q": error_type,
                "accepted": "True",
                "site": "stackoverflow",
                "pagesize": 3
            }
            
            response = await client.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                solutions = []
                for item in data.get("items", []):
                    solutions.append({
                        "title": item.get("title"),
                        "score": item.get("score"),
                        "link": item.get("link"),
                        "is_answered": item.get("is_answered"),
                        "tags": item.get("tags", [])
                    })
                
                return solutions
    except:
        pass
    
    return []


def get_common_solutions(error_type: str, error_message: str) -> list:
    """Base de connaissances des solutions communes"""
    solutions = []
    
    common_errors = {
        "SyntaxError": [
            "Vérifier les parenthèses, crochets et accolades",
            "Vérifier l'indentation du code",
            "Vérifier les deux-points après if, for, def, etc."
        ],
        "NameError": [
            "Vérifier que la variable est définie avant utilisation",
            "Vérifier l'orthographe du nom de la variable",
            "Vérifier la portée de la variable (scope)"
        ],
        "TypeError": [
            "Vérifier les types de données passés aux fonctions",
            "Convertir les types si nécessaire (int(), str(), etc.)",
            "Vérifier la signature de la fonction"
        ],
        "IndexError": [
            "Vérifier la taille de la liste/tableau",
            "Utiliser len() pour vérifier avant d'accéder",
            "Les index commencent à 0"
        ],
        "KeyError": [
            "Vérifier que la clé existe dans le dictionnaire",
            "Utiliser dict.get() avec une valeur par défaut",
            "Vérifier l'orthographe de la clé"
        ],
        "ImportError": [
            "Installer le module avec pip install",
            "Vérifier le nom du module",
            "Vérifier le PYTHONPATH"
        ],
        "AttributeError": [
            "Vérifier que l'objet a cet attribut/méthode",
            "Utiliser dir() pour lister les attributs disponibles",
            "Vérifier le type de l'objet"
        ]
    }
    
    if error_type in common_errors:
        solutions = [{"solution": s, "priority": "high"} for s in common_errors[error_type]]
    
    return solutions


async def get_documentation_links(error_type: str) -> list:
    """Liens vers la documentation officielle"""
    base_docs = {
        "python": "https://docs.python.org/3/library/exceptions.html",
        "java": "https://docs.oracle.com/javase/tutorial/essential/exceptions/",
        "javascript": "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Errors"
    }
    
    return [
        {
            "language": "Python",
            "url": base_docs["python"],
            "description": "Documentation officielle Python sur les exceptions"
        }
    ]


def analyze_context(context: str) -> Dict[str, Any]:
    """Analyse le contexte fourni"""
    analysis = {
        "has_code": bool(re.search(r'(def |class |import )', context)),
        "code_blocks": len(re.findall(r'```', context)) // 2,
        "mentioned_files": re.findall(r'[\w/]+\.py', context),
        "mentioned_functions": re.findall(r'def (\w+)', context)
    }
    
    return analysis
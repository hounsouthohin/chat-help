"""
Outils d'apprentissage et d'aide au développement
"""

from typing import Dict, Any
import re

async def explain_concept(concept: str, level: str = "intermediaire") -> Dict[str, Any]:
    """
    Explique un concept informatique de manière pédagogique
    """
    
    # Base de connaissances simplifiée (peut être étendue)
    explanations = {
        "récursivité": {
            "debutant": "Une fonction qui s'appelle elle-même. Comme des poupées russes!",
            "intermediaire": "Une technique où une fonction résout un problème en se rappelant elle-même avec des paramètres différents, jusqu'à atteindre un cas de base.",
            "avance": "Paradigme algorithmique utilisant la pile d'appels pour résoudre des problèmes divisibles en sous-problèmes similaires. Complexité spatiale O(n) due à la pile."
        },
        "pointeurs": {
            "debutant": "Une variable qui contient l'adresse mémoire d'une autre variable.",
            "intermediaire": "Référence à un emplacement mémoire permettant l'accès indirect aux données et la manipulation de structures dynamiques.",
            "avance": "Abstraction du modèle mémoire permettant l'arithmétique de pointeurs, l'allocation dynamique et l'implémentation de structures de données complexes."
        }
    }
    
    concept_lower = concept.lower()
    
    # Recherche de correspondances partielles
    matched_concept = None
    for key in explanations.keys():
        if key in concept_lower or concept_lower in key:
            matched_concept = key
            break
    
    if matched_concept:
        return {
            "success": True,
            "concept": concept,
            "level": level,
            "explanation": explanations[matched_concept].get(level, explanations[matched_concept]["intermediaire"]),
            "suggestion": "💡 Pour approfondir, consultez le wiki ou demandez des exemples de code!"
        }
    else:
        return {
            "success": True,
            "concept": concept,
            "level": level,
            "explanation": f"Le concept '{concept}' nécessite une recherche plus approfondie.",
            "suggestions": [
                "Recherchez ce concept dans le wiki",
                "Consultez la documentation officielle",
                "Demandez des exemples de code spécifiques"
            ],
            "note": "💡 Je peux mieux expliquer: récursivité, pointeurs, classes, héritage, polymorphisme, TCP/IP, etc."
        }

async def analyze_code(code: str, language: str) -> Dict[str, Any]:
    """
    Analyse du code avec suggestions d'amélioration
    """
    
    analysis = {
        "success": True,
        "language": language,
        "code_length": len(code),
        "lines": len(code.split('\n')),
        "issues": [],
        "suggestions": [],
        "good_practices": []
    }
    
    # Analyses basiques par langage
    if language == "python":
        # Vérifier l'indentation
        if '\t' in code:
            analysis["issues"].append("⚠️ Utilisation de tabulations détectée. PEP 8 recommande 4 espaces.")
        
        # Vérifier les conventions de nommage
        if re.search(r'\bdef [A-Z]', code):
            analysis["issues"].append("⚠️ Les fonctions Python devraient utiliser snake_case (minuscules avec underscores).")
        
        # Bonnes pratiques
        if 'def ' in code and '"""' not in code and "'''" not in code:
            analysis["suggestions"].append("💡 Ajoutez des docstrings à vos fonctions pour une meilleure documentation.")
        
        analysis["good_practices"].extend([
            "Utilisez des noms de variables descriptifs",
            "Limitez la longueur des fonctions (max 20-30 lignes)",
            "Utilisez les list comprehensions pour plus de concision"
        ])
    
    elif language == "java":
        if not re.search(r'public class \w+', code):
            analysis["issues"].append("⚠️ Assurez-vous que votre classe est correctement déclarée.")
        
        analysis["good_practices"].extend([
            "Suivez la convention CamelCase pour les classes",
            "Utilisez camelCase pour les méthodes et variables",
            "Commentez les méthodes publiques avec JavaDoc"
        ])
    
    elif language == "javascript":
        if 'var ' in code:
            analysis["suggestions"].append("💡 Préférez 'let' ou 'const' à 'var' pour une meilleure portée des variables.")
        
        analysis["good_practices"].extend([
            "Utilisez 'const' par défaut, 'let' si nécessaire",
            "Utilisez les fonctions fléchées pour plus de concision",
            "Activez le mode strict avec 'use strict'"
        ])
    
    # Score de qualité simple
    issues_count = len(analysis["issues"])
    if issues_count == 0:
        analysis["quality_score"] = "✅ Excellent"
    elif issues_count <= 2:
        analysis["quality_score"] = "👍 Bon"
    else:
        analysis["quality_score"] = "⚠️ Nécessite des améliorations"
    
    return analysis

async def debug_helper(error_message: str, context: str = "") -> Dict[str, Any]:
    """
    Aide au débogage basée sur le message d'erreur
    """
    
    error_lower = error_message.lower()
    
    solutions = []
    error_type = "Erreur générale"
    
    # Détection des erreurs courantes
    if "syntaxerror" in error_lower or "syntax error" in error_lower:
        error_type = "Erreur de syntaxe"
        solutions = [
            "Vérifiez les parenthèses, crochets et accolades (doivent être bien fermés)",
            "Vérifiez les guillemets (simples ou doubles bien fermés)",
            "Vérifiez l'indentation (particulièrement en Python)",
            "Recherchez les virgules manquantes dans les listes ou paramètres"
        ]
    
    elif "indentation" in error_lower:
        error_type = "Erreur d'indentation"
        solutions = [
            "Utilisez des espaces de manière cohérente (4 espaces recommandés en Python)",
            "Ne mélangez pas tabulations et espaces",
            "Vérifiez que tous les blocs sont correctement indentés",
            "Utilisez un éditeur qui affiche les caractères invisibles"
        ]
    
    elif "nameerror" in error_lower or "not defined" in error_lower:
        error_type = "Variable non définie"
        solutions = [
            "Vérifiez l'orthographe de la variable",
            "Assurez-vous que la variable est définie avant son utilisation",
            "Vérifiez la portée (scope) de la variable",
            "Importez le module si c'est une fonction externe"
        ]
    
    elif "typeerror" in error_lower:
        error_type = "Erreur de type"
        solutions = [
            "Vérifiez les types des variables utilisées",
            "Convertissez les types si nécessaire (int(), str(), float())",
            "Vérifiez le nombre de paramètres passés à une fonction",
            "Assurez-vous que l'objet supporte l'opération demandée"
        ]
    
    elif "indexerror" in error_lower or "out of range" in error_lower:
        error_type = "Index hors limites"
        solutions = [
            "Vérifiez que l'index est dans les limites de la liste (0 à len(liste)-1)",
            "Vérifiez que la liste n'est pas vide avant d'y accéder",
            "Utilisez len() pour connaître la taille de la liste",
            "Utilisez des boucles avec range(len(liste)) pour éviter les débordements"
        ]
    
    elif "keyerror" in error_lower:
        error_type = "Clé inexistante"
        solutions = [
            "Vérifiez que la clé existe dans le dictionnaire",
            "Utilisez .get() avec une valeur par défaut: dict.get('cle', 'defaut')",
            "Vérifiez l'orthographe de la clé",
            "Utilisez 'if cle in dict:' pour vérifier l'existence"
        ]
    
    elif "attributeerror" in error_lower:
        error_type = "Attribut inexistant"
        solutions = [
            "Vérifiez que l'objet possède cet attribut/méthode",
            "Vérifiez l'orthographe de l'attribut",
            "Assurez-vous que l'objet est du bon type",
            "Consultez la documentation de la classe"
        ]
    
    elif "importerror" in error_lower or "modulenotfounderror" in error_lower:
        error_type = "Module introuvable"
        solutions = [
            "Installez le module avec: pip install nom_module",
            "Vérifiez l'orthographe du nom du module",
            "Assurez-vous d'être dans le bon environnement virtuel",
            "Vérifiez que le fichier existe si c'est un module local"
        ]
    
    else:
        solutions = [
            "Lisez attentivement le message d'erreur complet",
            "Recherchez le message d'erreur sur Google ou Stack Overflow",
            "Consultez la documentation officielle",
            "Testez avec des print() pour déboguer étape par étape",
            "Utilisez un débogueur (debugger) pour examiner l'état du programme"
        ]
    
    return {
        "success": True,
        "error_type": error_type,
        "original_error": error_message,
        "context": context if context else "Aucun contexte fourni",
        "solutions": solutions,
        "tips": [
            "🔍 Lisez toujours l'erreur de bas en haut (la dernière ligne est souvent la plus importante)",
            "💡 Le numéro de ligne indiqué pointe souvent vers l'erreur ou juste après",
            "📚 Consultez le wiki pour des exemples de résolution d'erreurs courantes"
        ]
    }
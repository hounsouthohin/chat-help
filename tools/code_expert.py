"""
Code Expert - Version Gratuite
Analyse statique sans dépendances externes lourdes
"""

import ast
import re
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


async def analyze_code_expert(code: str, 
                              language: str,
                              include_tests: bool = True,
                              auto_fix: bool = False) -> Dict[str, Any]:
    """
    Analyse de code 100% gratuite sans outils externes
    """
    
    if language == "python":
        return await _analyze_python_simple(code, include_tests, auto_fix)
    else:
        return await _analyze_generic(code, language)


async def _analyze_python_simple(code: str, include_tests: bool, auto_fix: bool) -> Dict:
    """Analyse Python sans pylint/bandit (qui peuvent manquer)"""
    
    issues = []
    warnings = []
    
    # 1. ANALYSE SYNTAXIQUE
    try:
        ast.parse(code)
    except SyntaxError as e:
        issues.append({
            "type": "syntax",
            "severity": "error",
            "line": e.lineno,
            "message": str(e)
        })
        # Si erreur de syntaxe, arrêter l'analyse
        return {
            "success": False,
            "language": "python",
            "issues": issues,
            "error": "Erreur de syntaxe, impossible de continuer l'analyse"
        }
    
    # 2. ANALYSE DE SÉCURITÉ (patterns basiques)
    security_patterns = {
        r'eval\s*\(': "Utilisation dangereuse de eval()",
        r'exec\s*\(': "Utilisation dangereuse de exec()",
        r'pickle\.loads': "Désérialisation non sécurisée (pickle)",
        r'subprocess\.call.*shell\s*=\s*True': "Injection de commande possible",
        r'password\s*=\s*["\'][^"\']+["\']': "Mot de passe en dur",
        r'api[_-]?key\s*=\s*["\'][^"\']+["\']': "Clé API en dur",
    }
    
    for pattern, message in security_patterns.items():
        if re.search(pattern, code, re.IGNORECASE):
            issues.append({
                "type": "security",
                "severity": "high",
                "message": message,
                "pattern": pattern
            })
    
    # 3. ANALYSE DE QUALITÉ
    lines = code.split('\n')
    
    # Lignes trop longues
    for i, line in enumerate(lines, 1):
        if len(line) > 120:
            warnings.append({
                "type": "style",
                "severity": "low",
                "line": i,
                "message": f"Ligne trop longue ({len(line)} caractères)"
            })
    
    # Imports en double
    import_lines = [line for line in lines if line.strip().startswith('import ') or line.strip().startswith('from ')]
    if len(import_lines) != len(set(import_lines)):
        warnings.append({
            "type": "style",
            "severity": "low",
            "message": "Imports en double détectés"
        })
    
    # 4. COMPLEXITÉ
    function_count = code.count('def ')
    class_count = code.count('class ')
    complexity_score = len(re.findall(r'\bif\b|\bfor\b|\bwhile\b', code))
    
    # 5. GÉNÉRATION DE TESTS (si demandé)
    tests = None
    if include_tests:
        functions = re.findall(r'def\s+(\w+)\s*\(', code)
        tests = {
            "framework": "pytest",
            "tests_suggested": len(functions),
            "functions": functions,
            "template": f"# Tests suggérés pour {len(functions)} fonction(s)\nimport pytest\n\n"
        }
    
    return {
        "success": True,
        "language": "python",
        "provider": "simple_analysis",
        "metrics": {
            "lines_of_code": len(lines),
            "functions": function_count,
            "classes": class_count,
            "complexity_score": complexity_score
        },
        "issues": issues,
        "warnings": warnings,
        "tests": tests,
        "quality_score": max(0, 10 - len(issues) - len(warnings) * 0.5),
        "recommendations": _generate_recommendations(issues, warnings)
    }


async def _analyze_generic(code: str, language: str) -> Dict:
    """Analyse basique pour autres langages"""
    
    issues = []
    warnings = []
    
    # Patterns universels
    if 'eval(' in code:
        issues.append({"message": "eval() détecté"})
    if 'password' in code.lower():
        warnings.append({"message": "Possible mot de passe en dur"})
    
    return {
        "success": True,
        "language": language,
        "provider": "generic_analysis",
        "issues": issues,
        "warnings": warnings,
        "note": f"Analyse basique pour {language}, analyse avancée non disponible"
    }


def _generate_recommendations(issues: list, warnings: list) -> list:
    """Génère des recommandations"""
    recommendations = []
    
    if any('security' in str(i) for i in issues):
        recommendations.append("🔒 Auditer la sécurité du code")
    
    
    if any('password' in str(i).lower() for i in issues):
        recommendations.append("🔐 Utiliser des variables d'environnement pour les secrets")
    
    if any('ligne trop longue' in str(w).lower() for w in warnings):
        recommendations.append("📏 Limiter les lignes à 80-100 caractères")
    
    if len(issues) == 0 and len(warnings) == 0:
        recommendations.append("✅ Code propre, bon travail!")
    
    return recommendations
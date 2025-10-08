"""
Code Expert - Analyseur de Code Expert
Analyse profonde, auto-correction, génération de tests, détection de bugs
"""

import asyncio
import httpx
import re
import ast
import subprocess
import tempfile
import os
from typing import Dict, Any, List, Optional
import logging
import json

logger = logging.getLogger(__name__)


class CodeExpert:
    """Expert en analyse et amélioration de code"""
    
    def __init__(self):
        self.supported_languages = {
            "python": self._analyze_python,
            "javascript": self._analyze_javascript,
            "typescript": self._analyze_typescript,
            "java": self._analyze_java,
            "go": self._analyze_go,
            "rust": self._analyze_rust,
        }
    
    async def expert_analyze(self, 
                           code: str, 
                           language: str,
                           include_tests: bool = True,
                           auto_fix: bool = False) -> Dict[str, Any]:
        """
        Analyse experte complète du code
        
        Args:
            code: Code source à analyser
            language: Langage de programmation
            include_tests: Générer des tests unitaires
            auto_fix: Tenter de corriger automatiquement
        """
        try:
            language = language.lower()
            
            if language not in self.supported_languages:
                return {
                    "success": False,
                    "error": f"Langage non supporté: {language}",
                    "supported": list(self.supported_languages.keys())
                }
            
            # Analyse de base
            basic_analysis = await self.supported_languages[language](code)
            
            # Analyse de sécurité
            security = await self._security_audit(code, language)
            
            # Analyse de performance
            performance = await self._performance_analysis(code, language)
            
            # Analyse de qualité
            quality = await self._code_quality(code, language)
            
            # Complexité
            complexity = self._calculate_complexity(code, language)
            
            # Suggestions d'amélioration
            improvements = await self._suggest_improvements(code, language, basic_analysis)
            
            # Génération de tests
            tests = None
            if include_tests:
                tests = await self._generate_tests(code, language)
            
            # Auto-correction
            fixed_code = None
            if auto_fix and basic_analysis.get("issues"):
                fixed_code = await self._auto_fix_code(code, language, basic_analysis["issues"])
            
            # Documentation générée
            docs = await self._generate_documentation(code, language)
            
            # Recherche de code similaire (meilleurs exemples)
            similar = await self._find_similar_code(code, language)
            
            return {
                "success": True,
                "language": language,
                "metrics": {
                    "lines_of_code": len(code.split('\n')),
                    "complexity": complexity,
                    "quality_score": quality.get("score", 0)
                },
                "analysis": basic_analysis,
                "security": security,
                "performance": performance,
                "quality": quality,
                "improvements": improvements,
                "tests": tests,
                "fixed_code": fixed_code,
                "documentation": docs,
                "similar_examples": similar,
                "summary": self._generate_analysis_summary(basic_analysis, security, quality)
            }
            
        except Exception as e:
            logger.error(f"Erreur expert_analyze: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _analyze_python(self, code: str) -> Dict[str, Any]:
        """Analyse spécifique Python"""
        issues = []
        warnings = []
        
        # Analyse syntaxique
        try:
            ast.parse(code)
        except SyntaxError as e:
            issues.append({
                "type": "syntax",
                "severity": "error",
                "line": e.lineno,
                "message": str(e),
                "code": "SYNTAX_ERROR"
            })
        
        # Pylint
        pylint_results = await self._run_pylint(code)
        issues.extend(pylint_results.get("errors", []))
        warnings.extend(pylint_results.get("warnings", []))
        
        # Bandit (sécurité)
        bandit_results = await self._run_bandit(code)
        issues.extend(bandit_results.get("issues", []))
        
        # MyPy (typage)
        mypy_results = await self._run_mypy(code)
        warnings.extend(mypy_results.get("type_issues", []))
        
        return {
            "issues": issues,
            "warnings": warnings,
            "info": {
                "has_type_hints": "def " in code and "->" in code,
                "has_docstrings": '"""' in code or "'''" in code,
                "follows_pep8": len(issues) == 0
            }
        }
    
    async def _run_pylint(self, code: str) -> Dict[str, Any]:
        """Exécute Pylint"""
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            result = subprocess.run(
                ['pylint', temp_file, '--output-format=json', '--disable=C0111'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            os.unlink(temp_file)
            
            if result.stdout:
                pylint_output = json.loads(result.stdout)
                
                errors = []
                warnings = []
                
                for item in pylint_output:
                    issue = {
                        "line": item.get("line"),
                        "column": item.get("column"),
                        "type": item.get("type"),
                        "message": item.get("message"),
                        "symbol": item.get("symbol"),
                        "severity": "error" if item.get("type") == "error" else "warning"
                    }
                    
                    if item.get("type") == "error":
                        errors.append(issue)
                    else:
                        warnings.append(issue)
                
                return {"errors": errors, "warnings": warnings}
            
            return {"errors": [], "warnings": []}
            
        except Exception as e:
            logger.warning(f"Pylint error: {str(e)}")
            return {"errors": [], "warnings": []}
    
    async def _run_bandit(self, code: str) -> Dict[str, Any]:
        """Analyse de sécurité avec Bandit"""
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            result = subprocess.run(
                ['bandit', '-f', 'json', temp_file],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            os.unlink(temp_file)
            
            if result.stdout:
                bandit_output = json.loads(result.stdout)
                
                issues = []
                for item in bandit_output.get("results", []):
                    issues.append({
                        "type": "security",
                        "severity": item.get("issue_severity", "low").lower(),
                        "line": item.get("line_number"),
                        "message": item.get("issue_text"),
                        "confidence": item.get("issue_confidence"),
                        "code": item.get("test_id")
                    })
                
                return {"issues": issues}
            
            return {"issues": []}
            
        except Exception as e:
            logger.warning(f"Bandit error: {str(e)}")
            return {"issues": []}
    
    async def _run_mypy(self, code: str) -> Dict[str, Any]:
        """Vérification de types avec MyPy"""
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            result = subprocess.run(
                ['mypy', temp_file, '--show-error-codes'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            os.unlink(temp_file)
            
            type_issues = []
            for line in result.stdout.split('\n'):
                if ': error:' in line or ': note:' in line:
                    type_issues.append({"message": line.strip()})
            
            return {"type_issues": type_issues}
            
        except Exception as e:
            logger.warning(f"MyPy error: {str(e)}")
            return {"type_issues": []}
    
    async def _analyze_javascript(self, code: str) -> Dict[str, Any]:
        """Analyse JavaScript/TypeScript"""
        issues = []
        warnings = []
        
        # Vérifications basiques
        if "eval(" in code:
            issues.append({
                "type": "security",
                "severity": "high",
                "message": "Utilisation de eval() détectée",
                "recommendation": "Éviter eval() pour des raisons de sécurité"
            })
        
        if "var " in code:
            warnings.append({
                "type": "style",
                "severity": "low",
                "message": "Utilisation de 'var' au lieu de 'let' ou 'const'",
                "recommendation": "Préférer let/const pour le scope de bloc"
            })
        
        return {
            "issues": issues,
            "warnings": warnings,
            "info": {
                "uses_strict": "'use strict'" in code,
                "uses_es6": "=>" in code or "const " in code,
            }
        }
    
    async def _analyze_typescript(self, code: str) -> Dict[str, Any]:
        """Analyse TypeScript"""
        return await self._analyze_javascript(code)
    
    async def _analyze_java(self, code: str) -> Dict[str, Any]:
        """Analyse Java"""
        issues = []
        warnings = []
        
        # Conventions Java
        if not re.search(r'public class \w+', code):
            warnings.append({
                "message": "Pas de classe publique trouvée"
            })
        
        return {"issues": issues, "warnings": warnings}
    
    async def _analyze_go(self, code: str) -> Dict[str, Any]:
        """Analyse Go"""
        return {"issues": [], "warnings": []}
    
    async def _analyze_rust(self, code: str) -> Dict[str, Any]:
        """Analyse Rust"""
        return {"issues": [], "warnings": []}
    
    async def _security_audit(self, code: str, language: str) -> Dict[str, Any]:
        """Audit de sécurité approfondi"""
        vulnerabilities = []
        
        # Patterns dangereux universels
        dangerous_patterns = {
            "eval": {"severity": "critical", "message": "Injection de code possible"},
            "exec": {"severity": "critical", "message": "Exécution de code arbitraire"},
            "password": {"severity": "medium", "message": "Mot de passe potentiellement hardcodé"},
            "api_key": {"severity": "high", "message": "Clé API exposée"},
            "subprocess": {"severity": "medium", "message": "Exécution de commandes système"},
            "pickle": {"severity": "high", "message": "Désérialisation non sécurisée"},
        }
        
        for pattern, details in dangerous_patterns.items():
            if pattern in code.lower():
                vulnerabilities.append({
                    "pattern": pattern,
                    "severity": details["severity"],
                    "message": details["message"],
                    "found_at": code.lower().find(pattern)
                })
        
        # Recherche de secrets
        secret_patterns = [
            (r'password\s*=\s*["\'][^"\']+["\']', "Mot de passe en clair"),
            (r'api[_-]?key\s*=\s*["\'][^"\']+["\']', "Clé API en clair"),
            (r'secret\s*=\s*["\'][^"\']+["\']', "Secret en clair"),
            (r'token\s*=\s*["\'][^"\']+["\']', "Token en clair"),
        ]
        
        for pattern, message in secret_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                vulnerabilities.append({
                    "type": "secret_exposed",
                    "severity": "high",
                    "message": message,
                    "recommendation": "Utiliser des variables d'environnement"
                })
        
        return {
            "total_vulnerabilities": len(vulnerabilities),
            "critical": sum(1 for v in vulnerabilities if v.get("severity") == "critical"),
            "high": sum(1 for v in vulnerabilities if v.get("severity") == "high"),
            "medium": sum(1 for v in vulnerabilities if v.get("severity") == "medium"),
            "vulnerabilities": vulnerabilities,
            "security_score": max(0, 10 - len(vulnerabilities))
        }
    
    async def _performance_analysis(self, code: str, language: str) -> Dict[str, Any]:
        """Analyse de performance"""
        issues = []
        
        # Boucles inefficaces
        if "for " in code and "append(" in code:
            issues.append({
                "type": "performance",
                "message": "Utilisation de append dans une boucle",
                "recommendation": "Considérer list comprehension"
            })
        
        # Imports multiples
        import_count = len(re.findall(r'^import |^from .+ import', code, re.MULTILINE))
        if import_count > 20:
            issues.append({
                "type": "performance",
                "message": f"{import_count} imports détectés",
                "recommendation": "Réduire les dépendances"
            })
        
        return {
            "issues": issues,
            "score": max(0, 10 - len(issues))
        }
    
    async def _code_quality(self, code: str, language: str) -> Dict[str, Any]:
        """Analyse de qualité du code"""
        quality_metrics = {
            "has_comments": "#" in code or "//" in code or "/*" in code,
            "has_docstrings": '"""' in code or "'''" in code,
            "proper_naming": not bool(re.search(r'\b[a-z]{1,2}\b\s*=', code)),
            "no_long_lines": all(len(line) <= 100 for line in code.split('\n')),
            "no_long_functions": True  # Simplifié
        }
        
        score = sum(quality_metrics.values()) / len(quality_metrics) * 10
        
        return {
            "score": round(score, 2),
            "metrics": quality_metrics,
            "grade": "A" if score >= 9 else "B" if score >= 7 else "C" if score >= 5 else "D"
        }
    
    def _calculate_complexity(self, code: str, language: str) -> Dict[str, Any]:
        """Calcule la complexité cyclomatique"""
        # Complexité basée sur les structures de contrôle
        complexity = 1  # Base
        
        # Compter les structures
        complexity += code.count("if ")
        complexity += code.count("elif ")
        complexity += code.count("else:")
        complexity += code.count("for ")
        complexity += code.count("while ")
        complexity += code.count("and ")
        complexity += code.count("or ")
        complexity += code.count("try:")
        complexity += code.count("except")
        
        return {
            "cyclomatic_complexity": complexity,
            "rating": "low" if complexity < 10 else "medium" if complexity < 20 else "high",
            "maintainability": "good" if complexity < 15 else "fair" if complexity < 30 else "poor"
        }
    
    async def _suggest_improvements(self, code: str, language: str, analysis: Dict) -> List[Dict]:
        """Suggère des améliorations"""
        suggestions = []
        
        # Basé sur les issues
        if analysis.get("issues"):
            suggestions.append({
                "priority": "high",
                "category": "bugs",
                "message": f"{len(analysis['issues'])} problèmes détectés à corriger",
                "action": "Corriger les erreurs signalées"
            })
        
        # Documentation
        if not analysis.get("info", {}).get("has_docstrings"):
            suggestions.append({
                "priority": "medium",
                "category": "documentation",
                "message": "Ajouter des docstrings aux fonctions",
                "action": "Documenter le code avec des docstrings"
            })
        
        # Type hints (Python)
        if language == "python" and not analysis.get("info", {}).get("has_type_hints"):
            suggestions.append({
                "priority": "medium",
                "category": "type_safety",
                "message": "Ajouter des annotations de type",
                "action": "Utiliser type hints pour améliorer la maintenabilité"
            })
        
        return suggestions
    
    async def _generate_tests(self, code: str, language: str) -> Dict[str, Any]:
        """Génère des tests unitaires"""
        if language != "python":
            return {"message": "Génération de tests disponible seulement pour Python actuellement"}
        
        # Extraire les fonctions
        functions = re.findall(r'def (\w+)\(([^)]*)\):', code)
        
        tests = []
        for func_name, params in functions:
            test_code = f"""
def test_{func_name}():
    \"\"\"Test pour {func_name}\"\"\"
    # TODO: Implémenter le test
    result = {func_name}({self._generate_test_params(params)})
    assert result is not None
"""
            tests.append({
                "function": func_name,
                "test_code": test_code.strip()
            })
        
        full_test_file = "import pytest\n\n" + "\n\n".join(t["test_code"] for t in tests)
        
        return {
            "framework": "pytest",
            "tests_generated": len(tests),
            "test_file": full_test_file,
            "individual_tests": tests
        }
    
    def _generate_test_params(self, params: str) -> str:
        """Génère des paramètres de test"""
        if not params.strip():
            return ""
        
        # Simplification: valeurs par défaut
        param_list = [p.strip().split(':')[0].split('=')[0].strip() for p in params.split(',') if p.strip()]
        return ", ".join(f"None" for _ in param_list)
    
    async def _auto_fix_code(self, code: str, language: str, issues: List[Dict]) -> Optional[str]:
        """Tente de corriger automatiquement le code"""
        if language != "python":
            return None
        
        try:
            # Utiliser autopep8
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            result = subprocess.run(
                ['autopep8', '--in-place', '--aggressive', '--aggressive', temp_file],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            with open(temp_file, 'r') as f:
                fixed_code = f.read()
            
            os.unlink(temp_file)
            
            return fixed_code if fixed_code != code else None
            
        except Exception as e:
            logger.warning(f"Auto-fix error: {str(e)}")
            return None
    
    async def _generate_documentation(self, code: str, language: str) -> Dict[str, Any]:
        """Génère la documentation"""
        if language != "python":
            return {"message": "Documentation auto disponible pour Python uniquement"}
        
        # Extraire fonctions et classes
        functions = re.findall(r'def (\w+)\(([^)]*)\)(?:\s*->\s*([^:]+))?:', code)
        classes = re.findall(r'class (\w+)(?:\(([^)]*)\))?:', code)
        
        docs = {
            "functions": [],
            "classes": []
        }
        
        for func_name, params, return_type in functions:
            docs["functions"].append({
                "name": func_name,
                "parameters": params,
                "return_type": return_type or "Unknown",
                "description": f"Function {func_name}"
            })
        
        for class_name, bases in classes:
            docs["classes"].append({
                "name": class_name,
                "inherits": bases or "object",
                "description": f"Class {class_name}"
            })
        
        return docs
    
    async def _find_similar_code(self, code: str, language: str) -> List[Dict]:
        """Trouve du code similaire (exemples de qualité)"""
        try:
            # Extraire une signature de fonction
            snippet = code[:200].replace('\n', ' ').strip()
            
            async with httpx.AsyncClient() as client:
                url = f"https://api.github.com/search/code"
                params = {
                    "q": f"{snippet[:50]} language:{language}",
                    "sort": "indexed",
                    "per_page": 5
                }
                headers = {"Accept": "application/vnd.github.v3+json"}
                
                response = await client.get(url, params=params, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    examples = []
                    for item in data.get("items", [])[:5]:
                        examples.append({
                            "name": item.get("name"),
                            "repository": item.get("repository", {}).get("full_name"),
                            "url": item.get("html_url"),
                            "stars": item.get("repository", {}).get("stargazers_count", 0)
                        })
                    
                    return examples
        except:
            pass
        
        return []
    
    def _generate_analysis_summary(self, basic: Dict, security: Dict, quality: Dict) -> str:
        """Génère un résumé de l'analyse"""
        summary = "📊 Analyse de Code - Résumé\n\n"
        
        # Problèmes
        issue_count = len(basic.get("issues", []))
        warning_count = len(basic.get("warnings", []))
        
        if issue_count > 0:
            summary += f"❌ {issue_count} erreur(s) détectée(s)\n"
        if warning_count > 0:
            summary += f"⚠️ {warning_count} avertissement(s)\n"
        
        # Sécurité
        vuln_count = security.get("total_vulnerabilities", 0)
        if vuln_count > 0:
            summary += f"🔒 {vuln_count} vulnérabilité(s) de sécurité\n"
        
        # Qualité
        quality_score = quality.get("score", 0)
        summary += f"⭐ Score de qualité: {quality_score}/10 ({quality.get('grade', 'N/A')})\n"
        
        return summary


# Instance globale
expert = CodeExpert()


async def analyze_code_expert(code: str, language: str, 
                              include_tests: bool = True,
                              auto_fix: bool = False) -> Dict[str, Any]:
    """
    Fonction principale d'analyse experte
    
    Args:
        code: Code source
        language: Langage
        include_tests: Générer tests
        auto_fix: Auto-correction
    """
    return await expert.expert_analyze(code, language, include_tests, auto_fix)
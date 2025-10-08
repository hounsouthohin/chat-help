# Rapport Complet : Implémentation MCP avec n8n et Ollama

## Résumé Exécutif

Ce document présente l'implémentation complète d'une architecture basée sur le **Model Context Protocol (MCP)** intégrée avec **n8n** et **Ollama**, permettant de créer un système d'automatisation intelligent avec des outils personnalisés.

**Résultat final** : ✅ Système opérationnel avec 6 outils MCP fonctionnels accessibles depuis n8n via AI Agent

---

## 1. Architecture Finale

### 1.1 Stack Technologique

```
┌─────────────────── USER ───────────────────┐
                      ↓
              [Interface Chat n8n]
                      ↓
┌─────────────── n8n Workflow ───────────────┐
│  Chat Trigger → AI Agent (Ollama)          │
│                      ↓                      │
│              [MCP Client Node]             │
│         (HTTP Streamable Transport)        │
└────────────────────┬───────────────────────┘
                     │ JSON-RPC 2.0
                     ↓
┌──────── chat-help-mcp Server ──────────────┐
│  Protocol: MCP 2024-11-05                  │
│  Transport: HTTP Streamable                │
│  Port: 8080                                │
│                                            │
│  Outils disponibles (6):                  │
│  ├─ search_wiki                           │
│  ├─ explain_concept                       │
│  ├─ analyze_code                          │
│  ├─ debug_helper                          │
│  ├─ get_joke                              │
│  └─ motivational_quote                    │
└────────────────────────────────────────────┘
```

### 1.2 Flux de données

```
User Message
    ↓
Chat Trigger (n8n)
    ↓
AI Agent (Ollama llama3.2)
    ↓
Décision d'utiliser un outil MCP
    ↓
MCP Client Node
    ↓
HTTP POST → chat-help-mcp:8080/
    ↓
Exécution de l'outil Python
    ↓
Résultat JSON-RPC
    ↓
AI Agent formatte la réponse
    ↓
User reçoit la réponse
```

---

## 2. Configuration Docker

### 2.1 Services déployés

| Service | Image | Port | Réseau | Rôle |
|---------|-------|------|--------|------|
| **postgres** | postgres:16-alpine | 5432 | demo | Base de données n8n |
| **n8n** | n8nio/n8n:latest | 5678 | demo | Moteur de workflows |
| **ollama** | ollama/ollama:latest | 11434 | demo | Modèle IA (llama3.2) |
| **qdrant** | qdrant/qdrant | 6333 | demo | Base vectorielle |
| **chat-help-mcp** | chat-help-mcp (custom) | 8080 | demo | Serveur MCP |

### 2.2 Réseau Docker

Tous les services sont sur le réseau `demo`, permettant la communication inter-conteneurs :
- n8n → chat-help-mcp : `http://chat-help-mcp:8080/`
- n8n → ollama : `http://ollama:11434`

---

## 3. Serveur MCP - Implémentation détaillée

### 3.1 Fichier principal : `server.py`

```python
#!/usr/bin/env python3
"""
Serveur MCP conforme au protocole officiel 2024-11-05
Transport: HTTP Streamable
"""
import asyncio
import json
import logging
from aiohttp import web

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import des outils
from tools.wiki_tools import search_wiki
from tools.learning_tools import explain_concept, get_joke, motivational_quote
from tools.code_tools import analyze_code, debug_helper

# Configuration
PROTOCOL_VERSION = "2024-11-05"
SERVER_INFO = {
    "name": "chat-help-mcp",
    "version": "1.0.0"
}

# Définition des 6 outils MCP
TOOLS = [
    {
        "name": "search_wiki",
        "description": "Recherche sur Wikipedia",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Terme de recherche"},
                "category": {"type": "string", "description": "Catégorie optionnelle"}
            },
            "required": ["query"]
        }
    },
    # ... autres outils
]

class MCPHTTPServer:
    """Serveur MCP avec transport HTTP standard"""
    
    def __init__(self):
        self.app = web.Application()
        self.initialized = False
        self.setup_cors()
        self.setup_routes()
    
    def setup_routes(self):
        """Configure les endpoints MCP"""
        # Endpoint principal JSON-RPC
        self.app.router.add_post('/', self.handle_jsonrpc)
        
        # Endpoints REST alternatifs
        self.app.router.add_post('/initialize', self.handle_initialize_rest)
        self.app.router.add_get('/tools', self.handle_tools_list_rest)
        self.app.router.add_post('/tools/call', self.handle_tool_call_rest)
        
        # Health check
        self.app.router.add_get('/health', self.health_check)
    
    async def handle_jsonrpc(self, request):
        """
        Gère les requêtes JSON-RPC selon le protocole MCP
        
        Méthodes supportées:
        - initialize : Handshake initial
        - tools/list : Liste des outils
        - tools/call : Exécution d'un outil
        - ping : Health check
        """
        data = await request.json()
        method = data.get('method')
        params = data.get('params', {})
        req_id = data.get('id')
        
        if method == 'initialize':
            return await self.handle_initialize(params, req_id)
        elif method == 'tools/list':
            return await self.handle_tools_list(req_id)
        elif method == 'tools/call':
            return await self.handle_tool_call(params, req_id)
        # ... autres méthodes
```

### 3.2 Protocole JSON-RPC 2.0

#### Format de requête

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "get_joke",
    "arguments": {
      "language": "fr"
    }
  }
}
```

#### Format de réponse

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\"success\": true, \"joke\": \"...\", \"answer\": \"...\"}"
      }
    ]
  }
}
```

#### Format d'erreur

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32601,
    "message": "Method not found: unknown_method"
  }
}
```

---

## 4. Protocole de Transport : HTTP Streamable

### 4.1 Qu'est-ce que HTTP Streamable ?

Le transport **HTTP Streamable** est une variante du protocole MCP qui utilise HTTP standard pour la communication, contrairement à SSE (Server-Sent Events) ou stdio.

**Caractéristiques** :
- ✅ Requêtes/Réponses HTTP classiques (POST)
- ✅ Format JSON-RPC 2.0
- ✅ Compatible avec les firewalls
- ✅ Facile à déboguer
- ✅ Pas de connexion persistante

### 4.2 Séquence d'initialisation

```
n8n MCP Client                 chat-help-mcp Server
      |                                  |
      |  POST /                          |
      |  {"method": "initialize"}        |
      |--------------------------------->|
      |                                  |
      |  200 OK                          |
      |  {protocolVersion, capabilities} |
      |<---------------------------------|
      |                                  |
      |  POST /                          |
      |  {"method": "tools/list"}        |
      |--------------------------------->|
      |                                  |
      |  200 OK                          |
      |  {tools: [...]}                  |
      |<---------------------------------|
      |                                  |
      | ✓ Connexion établie              |
```

### 4.3 Appel d'outil

```
n8n MCP Client                 chat-help-mcp Server
      |                                  |
      |  POST /                          |
      |  {"method": "tools/call",        |
      |   "params": {                    |
      |     "name": "get_joke",          |
      |     "arguments": {...}           |
      |   }}                             |
      |--------------------------------->|
      |                                  |
      |         Exécution de l'outil     |
      |         └─> get_joke(args)       |
      |                                  |
      |  200 OK                          |
      |  {"result": {"content": [...]}}  |
      |<---------------------------------|
```

---

## 5. Outils MCP Disponibles

### 5.1 search_wiki

**Description** : Recherche sur Wikipedia

**Paramètres** :
```json
{
  "query": "string (requis)",
  "category": "string (optionnel)"
}
```

**Exemple d'utilisation** :
```json
{
  "name": "search_wiki",
  "arguments": {
    "query": "Python programming"
  }
}
```

**Implémentation** (`tools/wiki_tools.py`) :
```python
async def search_wiki(query: str, category: str = None) -> dict:
    """Recherche sur Wikipedia"""
    try:
        import wikipediaapi
        wiki = wikipediaapi.Wikipedia('fr')
        page = wiki.page(query)
        
        if page.exists():
            return {
                "success": True,
                "title": page.title,
                "summary": page.summary[:500],
                "url": page.fullurl
            }
        else:
            return {
                "success": False,
                "error": "Page non trouvée"
            }
    except Exception as e:
        return {"success": False, "error": str(e)}
```

### 5.2 explain_concept

**Description** : Explique un concept de manière pédagogique

**Paramètres** :
```json
{
  "concept": "string (requis)",
  "level": "beginner | intermediate | advanced (optionnel)"
}
```

### 5.3 analyze_code

**Description** : Analyse du code source

**Paramètres** :
```json
{
  "code": "string (requis)",
  "language": "string (requis)"
}
```

### 5.4 debug_helper

**Description** : Aide au débogage d'erreurs

**Paramètres** :
```json
{
  "error_message": "string (requis)",
  "context": "string (optionnel)"
}
```

### 5.5 get_joke

**Description** : Obtient une blague aléatoire

**Paramètres** :
```json
{
  "language": "fr | en (optionnel, défaut: fr)"
}
```

**Exemple de réponse** :
```json
{
  "success": true,
  "joke": "Comment appelle-t-on un informaticien qui sort dehors ?",
  "answer": "Un bug rare ! 🌞",
  "language": "fr"
}
```

### 5.6 motivational_quote

**Description** : Obtient une citation motivante

**Paramètres** : Aucun

---

## 6. Intégration avec n8n

### 6.1 Configuration du nœud MCP Client

**Paramètres obligatoires** :

| Paramètre | Valeur | Description |
|-----------|--------|-------------|
| **Endpoint** | `http://chat-help-mcp:8080/` | URL du serveur MCP |
| **Server Transport** | `HTTP Streamable` | Type de transport |
| **Authentication** | `None` | Pas d'authentification |
| **Tools to Include** | `All` | Inclure tous les outils |

### 6.2 Workflow n8n

```
┌─────────────────┐
│  Chat Trigger   │ ← Point d'entrée utilisateur
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│   AI Agent      │ ← Ollama llama3.2
│                 │
│  Chat Model: ──────→ Ollama Chat Model (llama3.2)
│  Memory: ───────────→ Window Buffer Memory
│  Tools: ────────────→ MCP Client
└─────────────────┘
         │
         ↓
┌─────────────────┐
│   MCP Client    │ ← Connexion au serveur MCP
│                 │
│  Endpoint: http://chat-help-mcp:8080/
│  Transport: HTTP Streamable
│  
│  Outils exposés:
│  - search_wiki
│  - explain_concept
│  - analyze_code
│  - debug_helper
│  - get_joke
│  - motivational_quote
└─────────────────┘
```

### 6.3 Fonctionnement

1. **User** envoie un message via le chat
2. **Chat Trigger** capture le message
3. **AI Agent** (Ollama) analyse le message
4. **AI Agent** décide d'utiliser un outil MCP si nécessaire
5. **MCP Client** appelle le serveur `chat-help-mcp:8080`
6. **Serveur MCP** exécute l'outil Python
7. **Résultat** retourne via JSON-RPC
8. **AI Agent** formatte et renvoie la réponse à l'utilisateur

---

## 7. Déploiement

### 7.1 Prérequis

- Docker et Docker Compose installés
- 8 Go RAM minimum
- 20 Go d'espace disque

### 7.2 Procédure de déploiement

```powershell
# 1. Cloner/préparer le projet
cd self-hosted-ai-starter-kit

# 2. Configurer les variables d'environnement
# Éditer .env avec les valeurs appropriées

# 3. Construire l'image du serveur MCP
docker-compose build chat-help-mcp

# 4. Démarrer tous les services
docker-compose up -d

# 5. Vérifier que tous les conteneurs sont démarrés
docker ps

# 6. Vérifier les logs
docker logs chat-help-mcp
docker logs n8n
docker logs ollama

# 7. Accéder à n8n
# Ouvrir http://localhost:5678
```

### 7.3 Vérification du déploiement

```powershell
# Health check du serveur MCP
curl http://localhost:8080/health

# Résultat attendu:
# {
#   "status": "ok",
#   "service": "chat-help-mcp",
#   "protocol": "MCP-HTTP",
#   "version": "1.0.0",
#   "tools_count": 6,
#   "initialized": false
# }

# Test de la liste des outils
$body = @{
    jsonrpc = "2.0"
    id = 1
    method = "tools/list"
    params = @{}
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8080/" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body
```

---

## 8. Tests et Validation

### 8.1 Test unitaire d'un outil

```powershell
# Test de get_joke
$body = @{
    jsonrpc = "2.0"
    id = 1
    method = "tools/call"
    params = @{
        name = "get_joke"
        arguments = @{
            language = "fr"
        }
    }
} | ConvertTo-Json -Depth 10

$response = Invoke-WebRequest -Uri "http://localhost:8080/" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body

$response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

### 8.2 Test dans n8n

1. Créer un workflow avec Chat Trigger + AI Agent + MCP Client
2. Lancer le workflow en mode test
3. Envoyer un message : "Raconte-moi une blague"
4. Vérifier que l'AI Agent appelle l'outil `get_joke`
5. Confirmer la réponse contient bien une blague

### 8.3 Logs de débogage

```powershell
# Suivre les logs en temps réel
docker logs -f chat-help-mcp

# Logs attendus lors d'un appel d'outil:
# INFO:__main__:📨 JSON-RPC: tools/call (id: 1)
# INFO:__main__:🔧 Appel outil: get_joke
# INFO:__main__:🔧 Exécution: get_joke
```

---

## 9. Problèmes Rencontrés et Solutions

### 9.1 Problème : "Could not connect to your MCP server"

**Cause** : Incompatibilité de transport SSE (Server-Sent Events)

**Solution** : Utiliser le transport "HTTP Streamable" au lieu de "Server Sent Events (Deprecated)"

### 9.2 Problème : "Waiting to execute..."

**Cause** : Le serveur ne répond pas au format attendu par n8n

**Solution** : Implémenter correctement le protocole JSON-RPC 2.0 avec les méthodes :
- `initialize`
- `tools/list`
- `tools/call`

### 9.3 Problème : Conteneurs ne communiquent pas

**Cause** : Mauvaise configuration réseau Docker

**Solution** : 
- Vérifier que tous les conteneurs sont sur le même réseau `demo`
- Utiliser les noms de conteneurs (`chat-help-mcp`) et non `localhost`

```bash
# Vérifier le réseau
docker network inspect self-hosted-ai-starter-kit_demo
```

### 9.4 Évolution du transport : SSE → HTTP Streamable

| Tentative | Transport | Résultat |
|-----------|-----------|----------|
| 1 | SSE (format personnalisé) | ❌ n8n ne reconnaît pas les outils |
| 2 | SSE (format MCP deprecated) | ❌ n8n affiche "waiting to execute" |
| 3 | SSE + HTTP POST combinés | ❌ Incompatibilité de format |
| 4 | **HTTP Streamable + JSON-RPC** | ✅ **FONCTIONNE** |

---

## 10. Monitoring et Maintenance

### 10.1 Health checks

```powershell
# Vérifier l'état de tous les services
docker-compose ps

# Health
Tutorial Complet : Connecter un Serveur MCP à n8n via Docker
📚 Table des matières

Vue d'ensemble du projet
Architecture du système
Composants du serveur MCP
Configuration Docker
Connexion à n8n
Étapes que vous avez suivies
Dépannage


🎯 Vue d'ensemble du projet {#vue-densemble}
Qu'est-ce qu'on a construit ?
Vous avez créé un serveur MCP (Model Context Protocol) qui expose des outils d'assistance (veille technologique, navigation web, apprentissage, etc.) que n8n peut utiliser dans ses workflows d'automatisation.
MCP = Model Context Protocol : Un protocole qui permet aux LLMs (comme les agents n8n) d'utiliser des outils externes de manière standardisée.
Schéma de l'architecture
┌─────────────────────────────────────────────────┐
│              Docker Network (demo)              │
│                                                 │
│  ┌──────────────┐         ┌─────────────────┐  │
│  │     n8n      │ ◄─────► │  chat-help-mcp  │  │
│  │  (Port 5678) │  HTTP   │   (Port 8080)   │  │
│  └──────────────┘         └─────────────────┘  │
│         │                          │            │
│         │                    ┌─────▼─────┐      │
│    ┌────▼────┐              │  8 Outils  │      │
│    │Postgres │              │ MCP Tools  │      │
│    └─────────┘              └────────────┘      │
│                                                 │
└─────────────────────────────────────────────────┘
         ▲
         │ Utilisateur accède via http://localhost:5678

🏗️ Architecture du système {#architecture}
Les 3 couches principales

Couche Réseau (Docker) : Tous les conteneurs communiquent via le réseau demo
Couche Application (MCP Server) : Serveur Python qui expose les outils via HTTP
Couche Client (n8n) : Consomme les outils MCP dans ses workflows


🛠️ Composants du serveur MCP {#composants-mcp}
1. Le fichier server.py
C'est le cœur de votre serveur MCP. Voici comment il fonctionne :
a) Import et configuration
pythonfrom aiohttp import web  # Serveur web asynchrone
import asyncio
import json
import logging

# Configuration des logs
LOG_FILE = "/app/data/mcp_server.log"
logging.basicConfig(level=logging.INFO)
Pourquoi aiohttp ? : Parce qu'on a besoin d'un serveur web asynchrone pour gérer plusieurs requêtes simultanées efficacement.
b) Définition des outils
pythonTOOLS = [
    {
        "name": "navigate_web",
        "description": "🌐 Navigateur web intelligent",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                # ... autres paramètres
            },
            "required": ["query"]
        }
    },
    # ... 7 autres outils
]
Format MCP : Chaque outil est décrit avec :

name : Identifiant unique
description : Ce que fait l'outil
inputSchema : Schéma JSON des paramètres attendus

c) La classe MCPHTTPServer
pythonclass MCPHTTPServer:
    def __init__(self):
        self.app = web.Application()
        self.setup_cors()      # Configure CORS pour autoriser n8n
        self.setup_routes()    # Définit les endpoints HTTP
Rôle : Gère les requêtes HTTP et les traduit en appels d'outils MCP.
d) Les endpoints clés
EndpointMéthodeRôle/POSTPrincipal - Reçoit les requêtes JSON-RPC de n8n/healthGETVérification que le serveur fonctionne/toolsGETListe tous les outils disponibles/initializePOSTInitialisation de la connexion MCP
e) Le protocole JSON-RPC 2.0
Votre serveur communique avec n8n via JSON-RPC 2.0 :
Requête d'initialisation :
json{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05"
  }
}
Réponse :
json{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2024-11-05",
    "capabilities": {"tools": {}},
    "serverInfo": {
      "name": "chat-help",
      "version": "2.0.0"
    }
  }
}

🐳 Configuration Docker {#configuration-docker}
1. Le Dockerfile (votre container)
Structure typique :
dockerfileFROM python:3.11-slim

WORKDIR /app

# Installation des dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code
COPY . .

# Port exposé
EXPOSE 8080

# Commande de démarrage
CMD ["python", "server.py"]
Ce qui se passe :

Part d'une image Python légère
Installe les dépendances (aiohttp, etc.)
Copie votre code
Expose le port 8080
Lance server.py au démarrage

2. Le docker-compose.yaml
Service chat-help-mcp
yamlchat-help-mcp:
  build: .                        # Construit l'image depuis le Dockerfile
  container_name: chat-help-mcp   # Nom du conteneur
  hostname: chat-help-mcp         # Nom DNS dans le réseau Docker
  networks:
    - demo                        # Réseau partagé avec n8n
  ports:
    - "8080:8080"                 # Port externe:interne
  environment:
    - MCP_HOST=0.0.0.0           # Écoute sur toutes les interfaces
    - MCP_PORT=8080               # Port interne
  command: python server.py       # Commande de démarrage
  healthcheck:                    # Vérification de santé
    test: ["CMD-SHELL", "python -c 'import urllib.request; urllib.request.urlopen(\"http://localhost:8080/health\")'"]
    interval: 10s                 # Teste toutes les 10s
    retries: 5                    # 5 tentatives max
    start_period: 15s             # Attendre 15s avant le premier test
Pourquoi le healthcheck ? : Pour que n8n attende que le serveur MCP soit vraiment prêt avant de démarrer.
Service n8n
yamln8n:
  image: n8nio/n8n:latest
  container_name: chat-help-n8n
  hostname: n8n
  networks:
    - demo                        # Même réseau que MCP
  depends_on:
    postgres:
      condition: service_healthy
    chat-help-mcp:
      condition: service_healthy  # Attend que MCP soit healthy
  environment:
    - N8N_SKIP_RESPONSE_COMPRESSION=true  # Important pour MCP/SSE
La magie du depends_on : n8n attend que MCP soit complètement démarré et fonctionnel.
Le réseau Docker
yamlnetworks:
  demo:
    name: chat-help_demo
    driver: bridge
Résolution DNS automatique : Dans le réseau demo, chaque conteneur peut appeler un autre par son hostname :

http://chat-help-mcp:8080 → Conteneur MCP
http://postgres:5432 → Conteneur Postgres


🔌 Connexion à n8n {#connexion-n8n}
Configuration du nœud MCP Client
Dans n8n, vous avez configuré le nœud MCP Client avec :
Endpoint: http://chat-help-mcp:8080
Server Transport: HTTP Streamable
Authentication: None
Tools to Include: All
Pourquoi cette URL fonctionne ?

chat-help-mcp : Hostname du conteneur MCP (résolution DNS Docker)
:8080 : Port interne du serveur
Pas de /stream ou /message : Le endpoint racine / gère automatiquement les requêtes JSON-RPC

Flux de communication
n8n Agent
   │
   │ 1. POST http://chat-help-mcp:8080/
   │    {"jsonrpc":"2.0", "method":"tools/list", "id":1}
   │
   ▼
chat-help-mcp (port 8080)
   │
   │ 2. Traitement par handle_jsonrpc()
   │
   ▼
Retourne la liste des 8 outils
   │
   ▼
n8n Agent voit les outils disponibles
   │
   │ 3. POST http://chat-help-mcp:8080/
   │    {"jsonrpc":"2.0", "method":"tools/call", 
   │     "params":{"name":"get_joke", "arguments":{"language":"fr"}}}
   │
   ▼
Exécution de l'outil get_joke()
   │
   ▼
Retourne la blague à n8n

📝 Étapes que vous avez suivies {#étapes-suivies}
Phase 1 : Création du serveur MCP

Écrit server.py avec :

Import des outils depuis /tools/
Définition des 8 outils MCP
Classe MCPHTTPServer avec routes HTTP
Handlers JSON-RPC pour initialize, tools/list, tools/call


Créé les outils dans /tools/ :

web_navigator.py : Fonction navigate_web()
tech_watcher.py : Fonction watch_tech()
code_expert.py : Fonction analyze_code_expert()
learning_assistant.py : Fonctions d'apprentissage


Configuré le Dockerfile :

Base Python 3.11
Installation des dépendances
Exposition du port 8080



Phase 2 : Configuration Docker Compose

Ajouté le service chat-help-mcp :

Build depuis Dockerfile
Exposition port 8080
Réseau demo
Variables d'environnement
Healthcheck avec Python urllib


Configuré les dépendances :

n8n depends_on chat-help-mcp
Attente du statut healthy


Ajouté les hostnames :

Chaque service a un hostname pour DNS



Phase 3 : Tests et debugging

Test du serveur :

powershell   docker-compose up -d
   docker logs chat-help-mcp
   Invoke-RestMethod http://localhost:8080/health

Test de connectivité réseau :

powershell   docker exec -it chat-help-n8n sh
   wget http://chat-help-mcp:8080/health

Configuration n8n MCP Client :

URL: http://chat-help-mcp:8080
Transport: HTTP Streamable



Phase 4 : Résolution des problèmes

Problème healthcheck :

Initialement : wget non disponible → unhealthy
Solution : Utiliser Python urllib.request pour le healthcheck


Problème de résolution DNS :

Ajout explicite des hostname
Utilisation du nom de conteneur exact dans n8n




🔧 Dépannage {#dépannage}
Problème : Container unhealthy
Symptôme : docker ps montre (unhealthy)
Diagnostic :
powershelldocker logs chat-help-mcp --tail 20
docker inspect chat-help-mcp --format='{{json .State.Health}}'
Solutions :

Vérifier que le serveur démarre sans erreur
Tester /health manuellement : curl localhost:8080/health
Adapter le healthcheck selon les outils disponibles dans l'image

Problème : n8n ne se connecte pas
Symptôme : "Could not connect to your MCP server"
Diagnostic :
powershell# Test depuis n8n
docker exec -it chat-help-n8n sh
wget -qO- http://chat-help-mcp:8080/health

# Vérifier le réseau
docker network inspect chat-help_demo
Solutions :

Vérifier que les deux conteneurs sont sur le même réseau
Utiliser le bon hostname (celui dans container_name)
Ne pas ajouter /stream ou /message à l'URL
Vérifier les logs n8n : docker logs chat-help-n8n

Problème : Outils non visibles
Symptôme : MCP connecté mais pas d'outils
Diagnostic :
powershell# Tester l'endpoint tools
Invoke-RestMethod -Method Post -Uri "http://localhost:8080/" `
  -Body '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' `
  -ContentType "application/json"
Solution : Vérifier que TOOLS est bien défini et que les fonctions sont importées

🎓 Ce que vous avez appris

Protocole MCP : Communication standardisée entre LLMs et outils
JSON-RPC 2.0 : Format de requête/réponse pour API
Docker Networking : Résolution DNS entre conteneurs
Healthchecks : Vérification de santé des services
Dépendances Docker : Ordre de démarrage avec depends_on
CORS : Autorisation des requêtes cross-origin
Asyncio Python : Serveur web asynchrone avec aiohttp


🚀 Pour aller plus loin

Ajouter de nouveaux outils : Créez une fonction dans /tools/ et ajoutez-la à TOOLS
Monitorer les logs : docker logs -f chat-help-mcp
Sécuriser : Ajouter une authentification (API key)
Scaler : Déployer plusieurs instances derrière un load balancer
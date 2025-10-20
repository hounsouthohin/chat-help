🎤 Présentation : Architecture d'un Chatbot IA avec MCP, n8n et Next.js
Durée : 5 minutes

📌 Slide 1 : Introduction (30 secondes)
Projet : Chat-Help
Un assistant IA intelligent pour le support technique
Objectif :
Créer un chatbot capable de :

Répondre aux questions techniques
Naviguer sur le web en temps réel
Mémoriser les conversations
Utiliser des outils externes (MCP)

Technologies :

MCP (Model Context Protocol) : Protocole d'outils pour LLM
n8n : Orchestrateur de workflows
Ollama : LLM local (Llama2)
Next.js : Interface utilisateur


🏗️ Slide 2 : Architecture globale (1 minute)
Les 3 couches principales
┌─────────────────────────────────────┐
│  COUCHE 1 : Interface Utilisateur  │
│  Next.js (localhost:3000)           │
│  - Page chatbot                     │
│  - API Route                        │
└──────────────┬──────────────────────┘
               │ HTTP POST
               ↓
┌─────────────────────────────────────┐
│  COUCHE 2 : Orchestration          │
│  n8n Workflow (Docker)              │
│  - Webhook                          │
│  - AI Agent                         │
│  - Formatage                        │
└──────────────┬──────────────────────┘
               │
         ┌─────┼─────┬─────────┐
         ↓     ↓     ↓         ↓
┌─────────────────────────────────────┐
│  COUCHE 3 : Services IA            │
│  - Ollama (LLM)                    │
│  - Postgres (Mémoire)              │
│  - MCP Server (Outils)             │
└─────────────────────────────────────┘
```

**Point clé :** Séparation des responsabilités

---

## 🔌 Slide 3 : MCP - Model Context Protocol (1 minute)

### Qu'est-ce que MCP ?

**Problème :** Les LLM sont limités à générer du texte
**Solution :** MCP leur donne accès à des outils externes

### Architecture MCP
```
┌──────────────┐
│   LLM        │ "Je veux chercher sur le web"
└──────┬───────┘
       │ Appelle l'outil
       ↓
┌──────────────┐
│  MCP Server  │ Protocole JSON-RPC 2.0
│              │
│  8 Outils :  │
│  ✓ Navigation web
│  ✓ Veille techno
│  ✓ Analyse code
│  ✓ Blagues...
└──────────────┘
Communication : JSON-RPC 2.0
json// n8n → MCP
{
  "method": "tools/call",
  "params": {
    "name": "navigate_web",
    "arguments": { "query": "actualités IA" }
  }
}

// MCP → n8n
{
  "result": {
    "content": "Voici les dernières actualités..."
  }
}
```

**Avantage :** Les LLM deviennent **actionnables**

---

## ⚙️ Slide 4 : n8n - L'orchestrateur (1 minute)

### Pourquoi n8n ?

**Rôle :** Coordonner tous les composants sans coder

### Workflow en 4 étapes
```
1. WEBHOOK
   ↓ Reçoit : { message, userId, sessionId }
   
2. EXTRACT DATA
   ↓ Prépare les données
   
3. AI AGENT (le cerveau)
   │
   ├─► Ollama : Génère le texte
   ├─► Postgres Memory : Se souvient
   └─► MCP Client : Utilise les outils
   ↓
   
4. FORMAT RESPONSE
   ↓ Retourne : { output, timestamp }
Configuration AI Agent
yamlChat Model: Ollama (llama2)
Memory: Postgres (historique)
Tools: MCP Client (8 outils)
```

**Point clé :** **Tout est visual** dans n8n, pas besoin de coder

---

## 🌉 Slide 5 : Communication Docker ↔ Next.js (1 minute)

### Le défi : Deux environnements séparés
```
┌──────────────────────────┐
│  Next.js (Machine Hôte)  │
│  localhost:3000          │
└────────┬─────────────────┘
         │ Comment communiquer ?
         │
         ↓ Port exposé : 5678
┌──────────────────────────┐
│  Docker Network          │
│  ┌────────────────────┐  │
│  │  n8n               │  │
│  │  port 5678:5678    │  │
│  └──────┬─────────────┘  │
│         │                │
│    ┌────┴────┬───────┐   │
│    ↓         ↓       ↓   │
│  Ollama   MCP   Postgres │
│  :11434   :8080  :5432   │
└──────────────────────────┘
Solution : Ports exposés
Dans Docker :

Réseau interne : http://chat-help-mcp:8080
Communication via hostnames

Depuis Next.js :

Accès externe : http://localhost:5678
Via port exposé

Code Next.js :
javascriptfetch('http://localhost:5678/webhook/chatbot', {
  method: 'POST',
  body: JSON.stringify({ message: "Bonjour" })
})
```

---

## 🔄 Slide 6 : Flux complet (1 minute)

### De la question à la réponse
```
1. USER
   "Comment déployer sur staging ?"
   │
   ↓
2. NEXT.JS (API Route)
   POST /api/chatbot
   │
   ↓ localhost:5678
3. N8N WEBHOOK
   Reçoit la requête
   │
   ↓
4. AI AGENT décide
   "Je dois chercher dans la documentation"
   │
   ↓
5. MCP CLIENT
   Appelle navigate_web("staging deployment")
   │
   ↓
6. MCP SERVER
   Exécute la recherche web
   │
   ↓ Retourne les résultats
7. OLLAMA
   Génère une réponse avec le contexte
   │
   ↓
8. POSTGRES MEMORY
   Sauvegarde la conversation
   │
   ↓
9. FORMAT RESPONSE
   Structure la réponse
   │
   ↓
10. RETOUR → USER
    "Voici comment déployer sur staging..."
```

**Temps total : ~3-5 secondes**

---

## 🎯 Slide 7 : Concepts clés (30 secondes)

### Les 5 piliers du projet

| Concept | Technologie | Rôle |
|---------|-------------|------|
| **Protocole MCP** | JSON-RPC 2.0 | Communication standardisée LLM ↔ Outils |
| **Orchestration** | n8n Workflow | Coordonne tous les services |
| **LLM Local** | Ollama (Llama2) | Génère les réponses |
| **Mémoire** | Postgres | Historique des conversations |
| **Conteneurisation** | Docker | Isolation et déploiement |

### Avantages

✅ **Modularité** : Chaque service est indépendant
✅ **Extensibilité** : Facile d'ajouter des outils MCP
✅ **Privacy** : LLM local, données privées
✅ **No-code** : n8n permet de modifier sans programmer

---

## 🚀 Slide 8 : Démo & Conclusion (30 secondes)

### Points forts

1. **Architecture moderne** : Microservices + Orchestration
2. **MCP** : Standard émergent pour les outils LLM
3. **Hybride** : Docker (backend) + Next.js (frontend)
4. **Scalable** : Facile d'ajouter Ollama, Qdrant, etc.

### Cas d'usage

- Support technique automatisé
- Assistant de documentation
- Recherche intelligente
- Automatisation de tâches

### Évolutions possibles

- Ajouter d'autres modèles (GPT-4, Claude)
- Plus d'outils MCP (GitHub, Jira, Slack)
- Interface vocale
- Multi-utilisateurs avec authentification

---

## 📊 Slide Bonus : Schéma récapitulatif
```
           USER
            │
            ↓
    ┌───────────────┐
    │   Next.js     │
    │  (Frontend)   │
    └───────┬───────┘
            │ localhost:5678
            ↓
    ┌───────────────┐
    │  n8n Workflow │ ◄─── Orchestrateur
    └───────┬───────┘
            │
    ┌───────┼───────┬─────────┐
    ↓       ↓       ↓         ↓
┌────────┐ ┌────┐ ┌──────┐ ┌──────┐
│ Ollama │ │MCP │ │Memory│ │...   │
│  LLM   │ │8   │ │Post- │ │autres│
│        │ │outils│ │gres │ │      │
└────────┘ └────┘ └──────┘ └──────┘

    Tout dans Docker

🎤 Script de présentation (5 minutes)
[0:00-0:30] Introduction
"Bonjour, je vais vous présenter Chat-Help, un assistant IA intelligent que j'ai développé. Ce projet combine 3 technologies clés : MCP pour les outils, n8n pour l'orchestration, et Ollama pour le LLM."
[0:30-1:30] Architecture
"L'architecture se compose de 3 couches : l'interface Next.js, l'orchestrateur n8n, et les services IA dans Docker. Chaque couche a une responsabilité précise, ce qui rend le système modulaire et maintenable."
[1:30-2:30] MCP Protocol
"Le point innovant est l'utilisation de MCP - Model Context Protocol. C'est un protocole qui permet aux LLM d'utiliser des outils externes. Par exemple, le chatbot peut chercher sur le web, analyser du code, ou faire de la veille technologique. La communication se fait via JSON-RPC 2.0."
[2:30-3:30] n8n Orchestrateur
"n8n coordonne tout. Un workflow visuel en 4 étapes : réception du message, préparation des données, AI Agent qui utilise Ollama + MCP + la mémoire Postgres, puis formatage de la réponse. Tout est configurable sans coder."
[3:30-4:30] Communication
"Le défi était de connecter Next.js qui tourne sur la machine hôte, avec n8n dans Docker. Solution : les ports exposés. Next.js appelle localhost:5678, qui est le port de n8n exposé depuis Docker. À l'intérieur du réseau Docker, les services communiquent via leurs hostnames."
[4:30-5:00] Conclusion
"En résumé : une architecture modulaire, le protocole MCP qui donne des super-pouvoirs aux LLM, et une orchestration no-code avec n8n. Le système est extensible, privé avec un LLM local, et scalable. Merci de votre attention !"
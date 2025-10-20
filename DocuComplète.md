📚 Documentation Complète : Projet Chat-Help avec Wiki Next.js
🎯 Vue d'ensemble du projet
Qu'est-ce qu'on a construit ?
Un écosystème complet d'assistant IA comprenant :

MCP Server : Serveur Python exposant des outils (navigation web, veille techno, etc.)
n8n Workflow : Orchestrateur qui coordonne l'AI Agent, Ollama et les outils MCP
Wiki Next.js : Interface utilisateur pour interagir avec le chatbot


🏗️ Architecture globale
┌─────────────────────────────────────────────────────────┐
│              Machine Hôte (Windows)                     │
│                                                         │
│  Wiki Next.js (localhost:3000)                         │
│       │                                                 │
│       │ HTTP POST /api/chatbot                         │
│       ↓                                                 │
│  ┌────────────────────────────────────────────────┐    │
│  │         Docker Network (demo)                  │    │
│  │                                                │    │
│  │  n8n (localhost:5678) ← Port exposé           │    │
│  │     │                                          │    │
│  │     ├─► AI Agent                               │    │
│  │     │   ├─► Ollama (llama2)                    │    │
│  │     │   ├─► Postgres Memory                    │    │
│  │     │   └─► MCP Client                         │    │
│  │     │       └─► MCP Server (port 8080)         │    │
│  │     │           └─► 8 Outils                   │    │
│  │     │                                          │    │
│  │     └─► Response → Wiki                        │    │
│  └────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘

📦 Partie 1 : Infrastructure Docker
Configuration docker-compose.yml (éléments clés)
yamlservices:
  # MCP Server
  chat-help-mcp:
    build: .
    container_name: chat-help-mcp
    hostname: chat-help-mcp
    networks:
      - demo
    ports:
      - "8080:8080"  # Exposé pour tests externes
    environment:
      - MCP_HOST=0.0.0.0
      - MCP_PORT=8080

  # n8n
  n8n:
    image: n8nio/n8n:latest
    container_name: chat-help-n8n
    hostname: n8n
    networks:
      - demo
    ports:
      - "5678:5678"  # ⚠️ CRITIQUE : Port pour Next.js
    depends_on:
      chat-help-mcp:
        condition: service_healthy
      ollama:
        condition: service_healthy
    environment:
      - OLLAMA_HOST=ollama:11434

  # Ollama
  ollama:
    image: ollama/ollama:latest
    container_name: chat-help-ollama
    networks:
      - demo
    ports:
      - "11434:11434"

networks:
  demo:
    name: chat-help_demo
    driver: bridge
Points essentiels :

Port 5678 de n8n DOIT être exposé pour Next.js
Tous les services dans le même réseau demo
MCP et Ollama doivent être healthy avant n8n

Démarrage
powershellcd M:\chat-help
docker-compose up -d

# Vérifier
docker ps
docker logs chat-help-n8n --tail 20

🔌 Partie 2 : Connexion MCP ↔ n8n
2.1 Configuration du MCP Server (CORS + HTTP)
Le serveur MCP expose plusieurs endpoints :
python# server.py (extraits essentiels)
class MCPHTTPServer:
    def setup_cors(self):
        # Autorise n8n à communiquer
        self.app.middlewares.append(self.cors_middleware)
    
    def setup_routes(self):
        self.app.router.add_post('/', self.handle_jsonrpc)
        self.app.router.add_get('/health', self.health)
        self.app.router.add_get('/tools', self.list_tools)
Endpoints disponibles :

POST / : Endpoint principal (JSON-RPC 2.0)
GET /health : Vérification de santé
GET /tools : Liste des outils

2.2 Configuration n8n → MCP Client
Dans le workflow n8n, nœud MCP Client :
yamlNode: MCP Client (dans AI Agent)
Type: @n8n/n8n-nodes-langchain.toolMcp

Configuration:
  Endpoint: http://chat-help-mcp:8080
  Server Transport: HTTP Streamable
  Authentication: None
  Tools to Include: All
Pourquoi ça fonctionne :

HTTP Streamable : Protocole pour communication temps-réel via Server-Sent Events (SSE)
hostname chat-help-mcp : Résolution DNS automatique dans le réseau Docker
CORS configuré : Le MCP Server autorise les requêtes depuis n8n

Protocole de communication (JSON-RPC 2.0) :
javascript// n8n appelle le MCP
POST http://chat-help-mcp:8080/
{
  "jsonrpc": "2.0",
  "method": "tools/list",
  "id": 1
}

// MCP répond
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "tools": [
      { "name": "navigate_web", "description": "..." },
      { "name": "watch_tech", "description": "..." },
      // ... 6 autres outils
    ]
  }
}
```

---

## ⚙️ Partie 3 : Configuration du Workflow n8n

### 3.1 Structure du workflow
```
Webhook → Extract Data → AI Agent → Format Response
          (Code)          │          (Code)
                          ├─► Ollama Chat Model
                          ├─► Postgres Memory
                          └─► MCP Client
3.2 Nœud 1 : Webhook
yamlHTTP Method: POST
Path: chatbot
Response Mode: lastNode
URL générée : http://localhost:5678/webhook/chatbot
3.3 Nœud 2 : Extract Data (Code)
javascriptconst body = $input.first().json.body || $input.first().json;

return {
  json: {
    chatInput: body.message || "Bonjour",
    sessionId: body.sessionId || `session_${Date.now()}`,
    userId: body.userId || "anonymous"
  }
};
3.4 Nœud 3 : AI Agent (Configuration)
Paramètres principaux :
yamlText: ={{ $json.chatInput }}
Sous-nœuds essentiels :
A. Ollama Chat Model
yamlBase URL: http://ollama:11434
Model: llama2
B. Postgres Chat Memory
yamlSession ID: ={{ $json.sessionId }}
Table Name: chat_memory
Connection: postgres (DB n8n)
C. MCP Client
yamlEndpoint: http://chat-help-mcp:8080
Transport: HTTP Streamable
Tools: All
3.5 Nœud 4 : Format Response (Code)
javascriptconst response = $input.first().json;
const extractData = $('Extract Data').first().json;

return {
  json: {
    output: response.output || "Pas de réponse",
    userId: extractData.userId,
    sessionId: extractData.sessionId,
    timestamp: new Date().toISOString()
  }
};
3.6 Activation
⚠️ ÉTAPE CRITIQUE : Activer le workflow avec le toggle en haut à droite
Test du workflow :
powershellInvoke-RestMethod -Method Post `
  -Uri "http://localhost:5678/webhook/chatbot" `
  -Body '{"message":"Bonjour","userId":"test"}' `
  -ContentType "application/json"
```

---

## 🌐 Partie 4 : Intégration Wiki Next.js

### 4.1 Pourquoi localhost:5678 fonctionne

**Le pont entre Docker et Next.js :**
```
Wiki Next.js (hors Docker)
    │
    │ Accès au port EXPOSÉ
    ↓
localhost:5678 → n8n (dans Docker)
    │
    │ Communication INTERNE au réseau Docker
    ↓
chat-help-mcp:8080, ollama:11434, etc.
Le port 5678 est exposé dans docker-compose, donc accessible depuis la machine hôte via localhost:5678.
4.2 API Route Next.js
Créer /pages/api/chatbot.js :
javascriptexport default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { message, userId, sessionId } = req.body;
  
  // ✅ Communication via port exposé
  const N8N_WEBHOOK_URL = 'http://localhost:5678/webhook/chatbot';

  const response = await fetch(N8N_WEBHOOK_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message: message.trim(),
      userId: userId || 'anonymous',
      sessionId: sessionId || `session_${Date.now()}`
    }),
    signal: AbortSignal.timeout(30000)
  });

  const data = await response.json();
  
  return res.status(200).json({
    response: data.output,
    timestamp: data.timestamp
  });
}
Points clés :

URL : http://localhost:5678 (pas d'hostname Docker)
Timeout de 30 secondes
Gestion d'erreurs

4.3 Page Chatbot
Créer /pages/chatbot.js :
javascriptimport { useState } from 'react';
import Header from '../components/Header';

export default function ChatbotPage() {
  const [messages, setMessages] = useState([...]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const sendMessage = async (e) => {
    e.preventDefault();
    
    // Ajouter message utilisateur
    setMessages(prev => [...prev, { type: 'user', content: input }]);
    setLoading(true);

    // Appel API
    const response = await fetch('/api/chatbot', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: input, userId: 'user123' })
    });

    const data = await response.json();
    
    // Ajouter réponse bot
    setMessages(prev => [...prev, { type: 'bot', content: data.response }]);
    setLoading(false);
  };

  return (
    <>
      <Header />
      {/* Interface chat */}
    </>
  );
}
4.4 Navigation (Card dans index.js)
jsx<Link href="/chatbot">
  <div className="nav-category chatbot">
    <span className="nav-category-icon">🤖</span>
    <h3>Assistant IA</h3>
    <p>Chatbot avec n8n et MCP</p>
  </div>
</Link>

🧪 Partie 5 : Tests et Validation
Test 1 : Infrastructure Docker
powershell# Vérifier les conteneurs
docker ps

# Tester MCP
Invoke-RestMethod http://localhost:8080/health

# Tester n8n
Invoke-RestMethod http://localhost:5678
Test 2 : Workflow n8n
powershell# Test direct du webhook
Invoke-RestMethod -Method Post `
  -Uri "http://localhost:5678/webhook/chatbot" `
  -Body '{"message":"Test","userId":"test"}' `
  -ContentType "application/json"
Test 3 : Intégration complète
powershell# Démarrer Wiki
cd M:\Projet-Automne-2025-Wiki
npm run dev

# Ouvrir http://localhost:3000
# Cliquer sur "Assistant IA"
# Envoyer un message

🔧 Dépannage
Erreur : "n8n is not available"
powershell# Vérifier n8n
docker logs chat-help-n8n --tail 20
docker restart chat-help-n8n
```

### Erreur : "Error in workflow"

**Dans n8n :**
1. Aller dans "Executions"
2. Cliquer sur l'exécution en erreur
3. Identifier le nœud en rouge

**Causes fréquentes :**
- Postgres Memory sans `sessionId`
- Ollama sans modèle installé : `docker exec -it chat-help-ollama ollama pull llama2`
- MCP Server injoignable

### Erreur : "webhook not registered"

**Le workflow n8n n'est pas activé.**

Solution : Activer le toggle en haut à droite dans n8n.

---

## 📊 Schéma de communication complet
```
User Browser (localhost:3000/chatbot)
    │
    ├─► Envoie message via formulaire
    │
    ↓
Next.js API Route (/api/chatbot)
    │
    ├─► fetch('http://localhost:5678/webhook/chatbot')
    │
    ↓
Docker Network (n8n reçoit via port 5678)
    │
    ├─► Webhook → Extract Data → AI Agent
    │                              │
    │                              ├─► Ollama (http://ollama:11434)
    │                              ├─► Postgres Memory
    │                              └─► MCP Client
    │                                  └─► POST http://chat-help-mcp:8080/
    │                                      (JSON-RPC: tools/call)
    │                                      │
    │                                      └─► Exécute navigate_web(), etc.
    │
    └─► Format Response → Retour au webhook → Next.js → Browser

🎯 Points clés à retenir
Communication MCP ↔ n8n

HTTP Streamable pour temps-réel
CORS activé dans le MCP Server
JSON-RPC 2.0 comme protocole
Hostname Docker : chat-help-mcp:8080

Communication n8n ↔ Next.js

Port exposé : 5678
URL depuis Next.js : http://localhost:5678
Webhook path : /webhook/chatbot
Pas de hostname Docker depuis Next.js

Workflow n8n

Webhook : Point d'entrée
Extract Data : Prépare les données
AI Agent : Orchestre Ollama + Memory + MCP
Format Response : Structure la réponse


✅ Checklist finale

 Docker containers démarrés et healthy
 Workflow n8n créé et activé
 MCP Client configuré : http://chat-help-mcp:8080
 Webhook testé directement
 /pages/api/chatbot.js créé
 /pages/chatbot.js créé
 Card ajoutée dans index.js
 Wiki démarré : npm run dev
 Test end-to-end réussi
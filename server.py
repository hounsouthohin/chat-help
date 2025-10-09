#!/usr/bin/env python3
"""
Serveur MCP Production Ready
Protocol: MCP 2024-11-05
Transport: HTTP (compatible n8n MCP Client)
"""
import asyncio
import json
import logging
import sys
import os
from aiohttp import web
from typing import Dict, Any

# ====================================================
# LOGGING
# ====================================================

LOG_FILE = os.getenv("MCP_LOG_FILE", "/app/data/mcp_server.log")
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)

# ====================================================
# IMPORTS DES OUTILS
# ====================================================

try:
    from tools.web_navigator import navigate_web
    from tools.tech_watcher import watch_tech
    from tools.code_expert import analyze_code_expert
    from tools.learning_assistant import (
        create_learning_path,
        explain_advanced,
        explain_concept,
        get_joke,
        motivational_quote
    )
    logger.info("✅ Tous les outils chargés")
except Exception as e:
    logger.error(f"❌ Erreur import: {e}", exc_info=True)
    sys.exit(1)


# ====================================================
# DÉFINITION DES OUTILS - SCHEMAS SIMPLIFIÉS
# ====================================================

TOOLS = [
    {
        "name": "navigate_web",
        "description": "🌐 Recherche web intelligente OU analyse de site spécifique. Détecte automatiquement les URLs dans le texte.",
        "inputSchema": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "Requête ou URL à analyser"}},
            "required": ["query"]
        }
    },
    {
        "name": "watch_tech",
        "description": "📡 Veille technologique - Actualités et tendances tech récentes",
        "inputSchema": {
            "type": "object",
            "properties": {"keywords": {"type": "string", "description": "Mots-clés séparés par des virgules"}}
        }
    },
    {
        "name": "analyze_code_expert",
        "description": "🔬 Analyse de code avec détection de bugs, audit sécurité, suggestions",
        "inputSchema": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Code source à analyser"},
                "language": {"type": "string", "description": "Langage (python, js, java...)"}
            },
            "required": ["code", "language"]
        }
    },
    {
        "name": "create_learning_path",
        "description": "🎓 Crée un parcours d'apprentissage personnalisé avec ressources et planning",
        "inputSchema": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "Sujet à apprendre"},
                "level": {"type": "string", "description": "beginner, intermediate, advanced"}
            },
            "required": ["topic"]
        }
    },
    {
        "name": "explain_advanced",
        "description": "💡 Explication approfondie d'un concept avec exemples et analogies",
        "inputSchema": {
            "type": "object",
            "properties": {"concept": {"type": "string", "description": "Concept à expliquer"}},
            "required": ["concept"]
        }
    },
    {
        "name": "explain_concept",
        "description": "📖 Explication simple d'un concept avec ressources Wikipedia et GitHub",
        "inputSchema": {
            "type": "object",
            "properties": {"concept": {"type": "string", "description": "Concept à expliquer"}},
            "required": ["concept"]
        }
    },
    {
        "name": "get_joke",
        "description": "😄 Raconte une blague de programmation",
        "inputSchema": {"type": "object", "properties": {"language": {"type": "string"}}}
    },
    {
        "name": "motivational_quote",
        "description": "💪 Citation motivante sur la tech et le développement",
        "inputSchema": {"type": "object", "properties": {}}
    }
]


# ====================================================
# MAPPING DES OUTILS
# ====================================================

TOOLS_MAP = {
    "navigate_web": navigate_web,
    "watch_tech": watch_tech,
    "analyze_code_expert": analyze_code_expert,
    "create_learning_path": create_learning_path,
    "explain_advanced": explain_advanced,
    "explain_concept": explain_concept,
    "get_joke": get_joke,
    "motivational_quote": motivational_quote,
}


# ====================================================
# NORMALISATION DES ARGUMENTS
# ====================================================

def normalize_arguments(tool_name: str, arguments: Any) -> Dict[str, Any]:
    """Normalise les arguments pour chaque outil (compatibilité n8n)"""
    logger.info(f"🔍 Normalisation pour {tool_name}")
    logger.info(f"   Type reçu: {type(arguments)}")
    logger.info(f"   Valeur brute: {arguments}")

    if isinstance(arguments, str):
        logger.info("   → Conversion string vers dict")
        if tool_name == "navigate_web":
            return {"query": arguments}
        elif tool_name in ["explain_concept", "explain_advanced"]:
            return {"concept": arguments}
        elif tool_name == "create_learning_path":
            return {"topic": arguments, "level": "beginner"}
        elif tool_name == "watch_tech":
            return {"keywords": arguments}
        elif tool_name == "get_joke":
            return {"language": "fr"}
        elif tool_name == "analyze_code_expert":
            return {"code": arguments, "language": "python"}
        else:
            return {"input": arguments}

    if not arguments:
        logger.info("   → Arguments vides, utilisation des valeurs par défaut")
        if tool_name == "motivational_quote":
            return {}
        elif tool_name == "get_joke":
            return {"language": "fr"}
        return {}

    if isinstance(arguments, dict):
        logger.info("   → Dict reçu, vérification des champs requis")

        if tool_name == "navigate_web" and "query" not in arguments:
            for key, value in arguments.items():
                if isinstance(value, str) and value.strip():
                    arguments["query"] = value
                    break

        if tool_name == "watch_tech" and "keywords" in arguments:
            if isinstance(arguments["keywords"], str):
                arguments["keywords"] = [k.strip() for k in arguments["keywords"].split(",")]

        if tool_name == "create_learning_path":
            arguments.setdefault("level", "beginner")
            arguments.setdefault("time_per_week", 10)

        if tool_name == "get_joke":
            arguments.setdefault("language", "fr")

        if tool_name == "explain_advanced":
            arguments.setdefault("level", "intermediate")
            arguments.setdefault("with_examples", True)
            arguments.setdefault("with_analogies", True)

        if tool_name == "explain_concept":
            arguments.setdefault("level", "intermediaire")

        logger.info(f"   → Arguments finaux: {arguments}")
        return arguments

    logger.warning(f"⚠️ Type inattendu: {type(arguments)}, tentative de conversion")
    return {"input": str(arguments)}


# ====================================================
# EXÉCUTION DES OUTILS
# ====================================================

async def execute_tool(name: str, arguments: Any) -> Dict[str, Any]:
    """Exécute un outil MCP"""
    try:
        logger.info("=" * 70)
        logger.info(f"🔧 EXÉCUTION OUTIL: {name}")
        logger.info("=" * 70)

        if name not in TOOLS_MAP:
            return {"success": False, "error": f"Outil inconnu: {name}", "available_tools": list(TOOLS_MAP.keys())}

        normalized_args = normalize_arguments(name, arguments)
        tool_func = TOOLS_MAP[name]

        logger.info("⚙️  Exécution de la fonction...")
        result = await tool_func(**normalized_args) if asyncio.iscoroutinefunction(tool_func) else tool_func(**normalized_args)

        logger.info(f"✅ Résultat obtenu: {len(str(result))} caractères")
        return result

    except Exception as e:
        logger.error(f"❌ Erreur dans {name}: {e}", exc_info=True)
        return {"success": False, "error": str(e), "tool": name}


# ====================================================
# SERVEUR HTTP MCP
# ====================================================

class MCPHTTPServer:
    """Serveur MCP compatible n8n"""

    def __init__(self):
        self.app = web.Application()
        self.initialized = False
        self.setup_cors()
        self.setup_routes()

    def setup_cors(self):
        @web.middleware
        async def cors_middleware(request, handler):
            if request.method == "OPTIONS":
                response = web.Response()
            else:
                response = await handler(request)
            response.headers.update({
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization"
            })
            return response

        self.app.middlewares.append(cors_middleware)

    def setup_routes(self):
        self.app.router.add_post("/", self.handle_jsonrpc)
        self.app.router.add_post("/mcp", self.handle_jsonrpc)
        self.app.router.add_post("/message", self.handle_jsonrpc)
        self.app.router.add_post("/initialize", self.handle_initialize_rest)
        self.app.router.add_get("/tools", self.handle_tools_list_rest)
        self.app.router.add_post("/tools/call", self.handle_tool_call_rest)
        self.app.router.add_get("/health", self.health_check)

    async def health_check(self, _):
        return web.json_response({
            "status": "healthy",
            "service": "chat-help-mcp",
            "version": "2.0.0",
            "protocol": "MCP-HTTP",
            "tools_count": len(TOOLS),
            "initialized": self.initialized,
            "tools": [t["name"] for t in TOOLS]
        })

    async def handle_jsonrpc(self, request):
        try:
            data = await request.json()
            method = data.get("method")
            params = data.get("params", {})
            req_id = data.get("id")

            if method == "initialize":
                response = await self.handle_initialize(params, req_id)
            elif method == "tools/list":
                response = await self.handle_tools_list(req_id)
            elif method == "tools/call":
                response = await self.handle_tool_call(params, req_id)
            elif method == "ping":
                response = self.make_response(req_id, {"status": "pong"})
            else:
                response = self.make_error(req_id, -32601, f"Method not found: {method}")

            return web.json_response(response)

        except Exception as e:
            logger.error(f"Erreur serveur: {e}", exc_info=True)
            return web.json_response(self.make_error(None, -32603, str(e)), status=500)

    async def handle_initialize(self, params, req_id):
        self.initialized = True
        return self.make_response(req_id, {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "chat-help", "version": "2.0.0"}
        })

    async def handle_tools_list(self, req_id):
        return self.make_response(req_id, {"tools": TOOLS})

    async def handle_tool_call(self, params, req_id):
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        if not tool_name:
            return self.make_error(req_id, -32602, "Missing tool name")

        result = await execute_tool(tool_name, arguments)
        return self.make_response(req_id, {
            "content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}]
        })

    async def handle_initialize_rest(self, request):
        data = await request.json()
        response = await self.handle_initialize(data, 1)
        return web.json_response(response["result"])

    async def handle_tools_list_rest(self, _):
        response = await self.handle_tools_list(1)
        return web.json_response(response["result"])

    async def handle_tool_call_rest(self, request):
        data = await request.json()
        response = await self.handle_tool_call(data, 1)
        return web.json_response(response["result"])

    def make_response(self, req_id, result):
        return {"jsonrpc": "2.0", "id": req_id, "result": result}

    def make_error(self, req_id, code, message):
        return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}


# ====================================================
# MAIN
# ====================================================

async def main():
    server = MCPHTTPServer()
    runner = web.AppRunner(server.app)
    await runner.setup()

    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_PORT", "8080"))
    site = web.TCPSite(runner, host, port)
    await site.start()

    logger.info(f"🚀 MCP HTTP Server running at http://{host}:{port}")
    await asyncio.Event().wait()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Arrêt du serveur MCP")
    except Exception as e:
        logger.error(f"💥 Erreur fatale: {e}", exc_info=True)
        sys.exit(1)

#!/usr/bin/env python3
"""
Serveur MCP conforme au protocole officiel 2024-11-05
Transport: HTTP (compatible n8n MCP Client)
"""
import asyncio
import json
import logging
import sys
import os
from aiohttp import web

# Logging
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

# Imports des outils
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
    logger.info("✅ Outils chargés")
except Exception as e:
    logger.error(f"❌ Erreur import: {e}", exc_info=True)
    sys.exit(1)

# Définition des outils MCP
TOOLS = [
    {
        "name": "navigate_web",
        "description": "🌐 Navigateur web intelligent",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "start_url": {"type": "string"},
                "depth": {"type": "integer", "default": 2}
            },
            "required": ["query"]
        }
    },
    {
        "name": "watch_tech",
        "description": "📡 Veille technologique",
        "inputSchema": {
            "type": "object",
            "properties": {
                "categories": {"type": "array", "items": {"type": "string"}},
                "keywords": {"type": "array", "items": {"type": "string"}},
                "hours_back": {"type": "integer", "default": 24}
            }
        }
    },
    {
        "name": "analyze_code_expert",
        "description": "🔬 Analyseur de code",
        "inputSchema": {
            "type": "object",
            "properties": {
                "code": {"type": "string"},
                "language": {"type": "string"},
                "include_tests": {"type": "boolean", "default": True},
                "auto_fix": {"type": "boolean", "default": False}
            },
            "required": ["code", "language"]
        }
    },
    {
        "name": "create_learning_path",
        "description": "🎓 Parcours d'apprentissage",
        "inputSchema": {
            "type": "object",
            "properties": {
                "topic": {"type": "string"},
                "level": {"type": "string", "default": "beginner"},
                "goals": {"type": "array", "items": {"type": "string"}},
                "time_per_week": {"type": "integer", "default": 10}
            },
            "required": ["topic"]
        }
    },
    {
        "name": "explain_advanced",
        "description": "💡 Explications avancées",
        "inputSchema": {
            "type": "object",
            "properties": {
                "concept": {"type": "string"},
                "level": {"type": "string", "default": "intermediate"},
                "with_examples": {"type": "boolean", "default": True},
                "with_analogies": {"type": "boolean", "default": True}
            },
            "required": ["concept"]
        }
    },
    {
        "name": "explain_concept",
        "description": "📖 Explication concept",
        "inputSchema": {
            "type": "object",
            "properties": {
                "concept": {"type": "string"},
                "level": {"type": "string", "default": "intermediaire"}
            },
            "required": ["concept"]
        }
    },
    {
        "name": "get_joke",
        "description": "😄 Blague",
        "inputSchema": {
            "type": "object",
            "properties": {
                "language": {"type": "string", "default": "fr"}
            }
        }
    },
    {
        "name": "motivational_quote",
        "description": "💪 Citation motivante",
        "inputSchema": {"type": "object", "properties": {}}
    }
]

# Map des fonctions
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

# État du serveur
SERVER_INFO = {
    "name": "chat-help",
    "version": "2.0.0"
}

PROTOCOL_VERSION = "2024-11-05"

async def execute_tool(name: str, arguments: dict) -> dict:
    """Exécute un outil"""
    try:
        logger.info(f"🔧 Exécution: {name}")
        
        if name not in TOOLS_MAP:
            return {"error": f"Outil inconnu: {name}"}
        
        tool_func = TOOLS_MAP[name]
        
        # Exécuter fonction async ou sync
        if asyncio.iscoroutinefunction(tool_func):
            result = await tool_func(**arguments)
        else:
            result = tool_func(**arguments)
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Erreur outil {name}: {str(e)}", exc_info=True)
        return {"error": str(e)}


class MCPHTTPServer:
    """Serveur MCP avec transport HTTP standard"""
    
    def __init__(self):
        self.app = web.Application()
        self.initialized = False
        self.setup_cors()
        self.setup_routes()
    
    def setup_cors(self):
        """Configure CORS"""
        @web.middleware
        async def cors_middleware(request, handler):
            if request.method == "OPTIONS":
                response = web.Response()
            else:
                try:
                    response = await handler(request)
                except web.HTTPException as ex:
                    response = ex
            
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            return response
        
        self.app.middlewares.append(cors_middleware)
    
    def setup_routes(self):
        """Configure les routes MCP"""
        # Route principale JSON-RPC (CELLE QUE N8N UTILISE)
        self.app.router.add_post('/', self.handle_jsonrpc)
        self.app.router.add_post('/mcp', self.handle_jsonrpc)
        
        # Routes REST alternatives
        self.app.router.add_post('/initialize', self.handle_initialize_rest)
        self.app.router.add_get('/tools', self.handle_tools_list_rest)
        self.app.router.add_post('/tools/call', self.handle_tool_call_rest)
        
        # Health check
        self.app.router.add_get('/health', self.health_check)
    
    async def health_check(self, request):
        """Health check"""
        return web.json_response({
            'status': 'healthy',
            'service': 'chat-help-mcp',
            'protocol': 'MCP-HTTP',
            'version': SERVER_INFO['version'],
            'tools_count': len(TOOLS),
            'initialized': self.initialized
        })
    
    async def handle_jsonrpc(self, request):
        """Gère les requêtes JSON-RPC"""
        try:
            data = await request.json()
            logger.info(f"📨 JSON-RPC: {data.get('method', 'unknown')} (id: {data.get('id')})")
            
            method = data.get('method')
            params = data.get('params', {})
            req_id = data.get('id')
            
            # Router vers la bonne méthode
            if method == 'initialize':
                response = await self.handle_initialize(params, req_id)
            elif method == 'tools/list':
                response = await self.handle_tools_list(req_id)
            elif method == 'tools/call':
                response = await self.handle_tool_call(params, req_id)
            elif method == 'ping':
                response = self.make_response(req_id, {})
            else:
                response = self.make_error(req_id, -32601, f"Method not found: {method}")
            
            return web.json_response(response)
            
        except json.JSONDecodeError:
            logger.error("❌ Parse error: Invalid JSON")
            return web.json_response(
                self.make_error(None, -32700, "Parse error"),
                status=400
            )
        except Exception as e:
            logger.error(f"❌ Erreur: {str(e)}", exc_info=True)
            return web.json_response(
                self.make_error(None, -32603, str(e)),
                status=500
            )
    
    async def handle_initialize(self, params, req_id):
        """Initialisation du serveur MCP"""
        logger.info(f"🔧 Initialisation - Protocol: {params.get('protocolVersion', 'unknown')}")
        
        self.initialized = True
        
        return self.make_response(req_id, {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {
                "tools": {}
            },
            "serverInfo": SERVER_INFO
        })
    
    async def handle_tools_list(self, req_id):
        """Liste les outils disponibles"""
        logger.info(f"📋 Liste des outils demandée ({len(TOOLS)} outils)")
        
        return self.make_response(req_id, {
            "tools": TOOLS
        })
    
    async def handle_tool_call(self, params, req_id):
        """Appelle un outil"""
        tool_name = params.get('name')
        arguments = params.get('arguments', {})
        
        if not tool_name:
            return self.make_error(req_id, -32602, "Missing tool name")
        
        logger.info(f"🔧 Appel outil: {tool_name} avec args: {arguments}")
        
        # Exécuter l'outil
        result = await execute_tool(tool_name, arguments)
        
        # Retourner le résultat au format MCP
        return self.make_response(req_id, {
            "content": [{
                "type": "text",
                "text": json.dumps(result, ensure_ascii=False, indent=2)
            }]
        })
    
    # Routes REST alternatives
    async def handle_initialize_rest(self, request):
        """Initialisation via REST"""
        data = await request.json()
        response = await self.handle_initialize(data, 1)
        return web.json_response(response['result'])
    
    async def handle_tools_list_rest(self, request):
        """Liste des outils via REST"""
        response = await self.handle_tools_list(1)
        return web.json_response(response['result'])
    
    async def handle_tool_call_rest(self, request):
        """Appel d'outil via REST"""
        data = await request.json()
        response = await self.handle_tool_call(data, 1)
        return web.json_response(response['result'])
    
    def make_response(self, req_id, result):
        """Crée une réponse JSON-RPC"""
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": result
        }
    
    def make_error(self, req_id, code, message):
        """Crée une erreur JSON-RPC"""
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {
                "code": code,
                "message": message
            }
        }


async def main():
    """Lance le serveur"""
    server = MCPHTTPServer()
    runner = web.AppRunner(server.app)
    await runner.setup()
    
    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_PORT", "8080"))
    
    site = web.TCPSite(runner, host, port)
    await site.start()
    
    logger.info("=" * 70)
    logger.info("🚀 Serveur MCP HTTP Standard démarré!")
    logger.info(f"📍 Endpoint: http://{host}:{port}/")
    logger.info(f"📋 Outils: {len(TOOLS)}")
    logger.info(f"📡 Protocol: {PROTOCOL_VERSION}")
    logger.info("=" * 70)
    logger.info("")
    logger.info("🎯 Endpoints disponibles:")
    logger.info("  POST /               - JSON-RPC principal (pour n8n)")
    logger.info("  POST /mcp            - JSON-RPC alternatif")
    logger.info("  POST /initialize     - Initialisation REST")
    logger.info("  GET  /tools          - Liste des outils REST")
    logger.info("  POST /tools/call     - Appel d'outil REST")
    logger.info("  GET  /health         - Health check")
    logger.info("=" * 70)
    logger.info("")
    logger.info("⚙️  Configuration n8n MCP Client:")
    logger.info("  Endpoint: http://chat-help-mcp:8080")
    logger.info("  Transport: HTTP Streamable")
    logger.info("=" * 70)
    logger.info("")
    logger.info("📋 Outils disponibles:")
    for tool in TOOLS:
        logger.info(f"  ✓ {tool['name']}: {tool['description']}")
    logger.info("=" * 70)
    
    await asyncio.Event().wait()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Serveur arrêté")
    except Exception as e:
        logger.error(f"💥 Erreur fatale: {e}", exc_info=True)
        sys.exit(1)
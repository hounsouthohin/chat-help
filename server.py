#!/usr/bin/env python3
"""
Serveur MCP conforme au protocole officiel 2024-11-05
Transport: HTTP (pas SSE)
"""
import asyncio
import json
import logging
from aiohttp import web

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from tools.wiki_tools import search_wiki
from tools.learning_tools import explain_concept, get_joke, motivational_quote
from tools.code_tools import analyze_code, debug_helper

# Définition des outils MCP
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
    {
        "name": "explain_concept",
        "description": "Explique un concept de manière pédagogique",
        "inputSchema": {
            "type": "object",
            "properties": {
                "concept": {"type": "string", "description": "Concept à expliquer"},
                "level": {"type": "string", "description": "Niveau: beginner, intermediate, advanced", "default": "intermediate"}
            },
            "required": ["concept"]
        }
    },
    {
        "name": "analyze_code",
        "description": "Analyse du code source",
        "inputSchema": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Code à analyser"},
                "language": {"type": "string", "description": "Langage de programmation"}
            },
            "required": ["code", "language"]
        }
    },
    {
        "name": "debug_helper",
        "description": "Aide au débogage d'erreurs",
        "inputSchema": {
            "type": "object",
            "properties": {
                "error_message": {"type": "string", "description": "Message d'erreur"},
                "context": {"type": "string", "description": "Contexte de l'erreur"}
            },
            "required": ["error_message"]
        }
    },
    {
        "name": "get_joke",
        "description": "Obtient une blague aléatoire",
        "inputSchema": {
            "type": "object",
            "properties": {
                "language": {"type": "string", "description": "Langue", "default": "fr"}
            }
        }
    },
    {
        "name": "motivational_quote",
        "description": "Obtient une citation motivante",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    }
]

# État du serveur
SERVER_INFO = {
    "name": "chat-help-mcp",
    "version": "1.0.0"
}

PROTOCOL_VERSION = "2024-11-05"

async def execute_tool(name: str, arguments: dict) -> dict:
    """Exécute un outil"""
    try:
        logger.info(f"🔧 Exécution: {name}")
        
        if name == "search_wiki":
            return await search_wiki(arguments.get("query"), arguments.get("category"))
        elif name == "explain_concept":
            return await explain_concept(arguments.get("concept"), arguments.get("level", "intermediate"))
        elif name == "analyze_code":
            return await analyze_code(arguments.get("code"), arguments.get("language"))
        elif name == "debug_helper":
            return await debug_helper(arguments.get("error_message"), arguments.get("context"))
        elif name == "get_joke":
            return await get_joke(arguments.get("language", "fr"))
        elif name == "motivational_quote":
            return await motivational_quote()
        else:
            return {"error": f"Outil inconnu: {name}"}
    except Exception as e:
        logger.error(f"❌ Erreur: {str(e)}", exc_info=True)
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
        # Route principale JSON-RPC
        self.app.router.add_post('/', self.handle_jsonrpc)
        self.app.router.add_post('/mcp', self.handle_jsonrpc)
        
        # Routes REST alternatives (au cas où n8n les utilise)
        self.app.router.add_post('/initialize', self.handle_initialize_rest)
        self.app.router.add_get('/tools', self.handle_tools_list_rest)
        self.app.router.add_post('/tools/call', self.handle_tool_call_rest)
        
        # Health check
        self.app.router.add_get('/health', self.health_check)
    
    async def health_check(self, request):
        """Health check"""
        return web.json_response({
            'status': 'ok',
            'service': 'chat-help-mcp',
            'protocol': 'MCP-HTTP',
            'version': '1.0.0',
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
        
        logger.info(f"🔧 Appel outil: {tool_name}")
        
        # Exécuter l'outil
        result = await execute_tool(tool_name, arguments)
        
        # Retourner le résultat au format MCP
        return self.make_response(req_id, {
            "content": [{
                "type": "text",
                "text": json.dumps(result, ensure_ascii=False)
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
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    
    logger.info("=" * 70)
    logger.info("🚀 Serveur MCP HTTP Standard démarré!")
    logger.info(f"📍 Endpoint: http://0.0.0.0:8080/")
    logger.info(f"📋 Outils: {len(TOOLS)}")
    logger.info(f"📡 Protocol: {PROTOCOL_VERSION}")
    logger.info("=" * 70)
    logger.info("")
    logger.info("Endpoints disponibles:")
    logger.info("  POST / ou /mcp          - JSON-RPC principal")
    logger.info("  POST /initialize        - Initialisation REST")
    logger.info("  GET  /tools             - Liste des outils REST")
    logger.info("  POST /tools/call        - Appel d'outil REST")
    logger.info("  GET  /health            - Health check")
    logger.info("=" * 70)
    logger.info("")
    logger.info("Configuration n8n:")
    logger.info("  Endpoint: http://chat-help-mcp:8080/")
    logger.info("  Transport: HTTP Streamable")
    logger.info("=" * 70)
    logger.info("")
    logger.info("📋 Outils disponibles:")
    for tool in TOOLS:
        logger.info(f"  - {tool['name']}: {tool['description']}")
    logger.info("")
    
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
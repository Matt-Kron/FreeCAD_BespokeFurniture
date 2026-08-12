import json
import http.server
import socket
import socketserver
import threading
from pathlib import Path
import importlib.util

import FreeCAD
from PySide import QtCore
# from .tools.add_object import add_object
# from .tools.remove_object import remove_object
# from .tools.get_document_tree import get_document_tree
# from .tools.get_geo_structure import get_geo_structure

global_rpc_server = None
active_rpc_port = None  # Conserve le port réellement attribué

TOOLS_REGISTRY = {}

def load_tools():
    tools_dir = Path(__file__).parent / "tools"

    # Nettoyage des fichiers .meta.json orphelins (sans .py correspondant)
    for meta_file in tools_dir.glob("*.meta.json"):
        if not meta_file.with_suffix(".py").exists():
            meta_file.unlink()  # Supprime le fichier orphelin

    for file in tools_dir.glob("*.py"):
        if file.name.startswith("_"):
            continue
        spec = importlib.util.spec_from_file_location(file.stem, file)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        if hasattr(mod, "TOOL_META") and hasattr(mod, "run"):
            TOOLS_REGISTRY[mod.TOOL_META["name"]] = mod.run

            # ✅ Génération automatique du .meta.json
            meta_file = file.with_suffix(".meta.json")
            with open(meta_file, "w", encoding="utf-8") as f:
                json.dump(mod.TOOL_META, f, indent=2, ensure_ascii=False)

class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True

def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """Vérifie si un port est actuellement ouvert/occupé par un service."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0

# Dispatcher Qt pour rediriger les appels vers le thread principal UI
class RPCDispatcher(QtCore.QObject):
    dispatch_signal = QtCore.Signal(dict, list)

    def __init__(self):
        super().__init__()
        self.dispatch_signal.connect(self._execute_in_main_thread)
        self.result = None
        self.error = None
        self.completed = threading.Event()

    @QtCore.Slot(dict, list)
    def _execute_in_main_thread(self, func_map, args):
        try:
            self.result = func_map['target'](*args)
            self.error = None
        except Exception as e:
            self.error = str(e)
            self.result = None
        finally:
            self.completed.set()

    def run_safe(self, target_func, args):
        self.completed.clear()
        self.dispatch_signal.emit({'target': target_func}, args)
        self.completed.wait()
        if self.error:
            raise Exception(self.error)
        return self.result

# --- API EXPOSÉE POUR LE DESSIN DE MEUBLES ---
#
# Mapping des méthodes JSON-RPC
# RPC_METHODS =
# {
#     "add_object": add_object,
#     "remove_object": remove_object,
#     "get_document_tree": get_document_tree,
#     "get_geo_structure": get_geo_structure
# }

dispatcher = RPCDispatcher()

# Serveur HTTP basique JSON-RPC
class JSONRPCHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Silencer les logs HTTP de base dans la console FreeCAD

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length).decode('utf-8')
        request = json.loads(body)

        method_name = request.get("method")
        params = request.get("params", [])
        req_id = request.get("id")

        if method_name not in TOOLS_REGISTRY:
            response = {"jsonrpc": "2.0", "error": {"code": -32601, "message": "Method not found"}, "id": req_id}
        else:
            try:
                # Exécution sécurisée sur le thread UI FreeCAD
                result = dispatcher.run_safe(TOOLS_REGISTRY[method_name], params)
                response = {"jsonrpc": "2.0", "result": result, "id": req_id}
            except Exception as e:
                response = {"jsonrpc": "2.0", "error": {"code": -32000, "message": str(e)}, "id": req_id}

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf-8'))

def start_rpc_server(default_port=9147, max_attempts=10):
    global global_rpc_server, active_rpc_port

    stop_rpc_server()  # Arrête l'instance précédente si elle existe
    load_tools()

    # Si on a déjà tourné sur un port spécifique, on réessaie prioritairement celui-ci
    start_port = active_rpc_port if active_rpc_port else default_port
    port = start_port

    for attempt in range(max_attempts):
        try:
            server = ReusableTCPServer(("127.0.0.1", port), JSONRPCHandler)
            thread = threading.Thread(target=server.serve_forever)
            thread.daemon = True
            thread.start()

            global_rpc_server = server
            active_rpc_port = port  # Mémorisation du port attribué !

            print(f"[RPC Server] Serveur démarré avec succès sur http://127.0.0.1:{port}")
            return server, port

        except OSError as e:
            if e.errno == 98:  # Port occupé
                print(f"[RPC Server] Le port {port} est occupé. Essai sur le port {port + 1}...")
                port += 1
            else:
                raise e

    raise RuntimeError(f"Impossible de trouver un port libre dans la plage d'essais.")

def stop_rpc_server():
    """Arrête proprement le serveur RPC en cours d'exécution."""
    global global_rpc_server
    if global_rpc_server is not None:
        try:
            global_rpc_server.shutdown()
            global_rpc_server.server_close()
            global_rpc_server = None
            print("[RPC Server] Serveur arrêté avec succès.")
        except Exception as e:
            print(f"[RPC Server] Erreur lors de l'arrêt : {e}")
    else:
        print("[RPC Server] Aucun serveur actif à arrêter.")

def restart_rpc_server():
    """Redémarre sur le port actuel ou le port par défaut."""
    return start_rpc_server()


# Démarrage au chargement du script
# rpc_server = start_rpc_server()

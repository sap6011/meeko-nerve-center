import http.server
import socketserver
import socket
import json
from pathlib import Path

DATA = Path("data")
DATA.mkdir(exist_ok=True)

def broadcast():
    PORT = 8080
    Handler = http.server.SimpleHTTPRequestHandler
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
    print(f"📡 BROADCAST ACTIVE: Access the Swarm at http://{local_ip}:{PORT}")
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        httpd.serve_forever()

if __name__ == "__main__":
    broadcast()


# -- LIVE_WIRE topology connector --
def _wire_state():
    _r = json.loads((DATA / "brain_state.json").read_text()) if (DATA / "brain_state.json").exists() else {}
    try: _h=json.loads((DATA/"homeostasis_state.json").read_text(encoding="utf-8"))
    except: _h={}
    try: _c=json.loads((DATA/"neural_cortex_state.json").read_text(encoding="utf-8"))
    except: _c={}
    (DATA / "spore_server_state.json").write_text(json.dumps({"last_run": __import__("datetime").datetime.now().isoformat(), "status": "wired","nervous_system":{"equilibrium":_h.get("equilibrium",0),"trend":_h.get("trend","unknown"),"brain_confidence":_c.get("decision_confidence",0)}}, indent=2), encoding="utf-8")

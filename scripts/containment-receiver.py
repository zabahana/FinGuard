"""Local controlled sink. Records paths only; never stores submitted payloads."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread, Lock, Event

root = Path('artifacts/openshell')
root.mkdir(parents=True, exist_ok=True)
lock = Lock()
class Receiver(BaseHTTPRequestHandler):
    def respond(self):
        with lock, (root / 'receiver.jsonl').open('a') as stream:
            stream.write(json.dumps({'method':self.command,'path':self.path,'port':self.server.server_port})+'\n')
        self.send_response(200)
        self.send_header('Content-Type','application/json')
        self.end_headers()
        self.wfile.write(b'{"controlled_receiver":true}')
    do_GET = do_POST = respond
    def log_message(self, *args):
        pass
servers = [ThreadingHTTPServer(('127.0.0.1', port), Receiver) for port in (18081,18082)]
for server in servers:
    Thread(target=server.serve_forever, daemon=True).start()
print('Controlled receivers listening on loopback ports 18081 and 18082', flush=True)
Event().wait()

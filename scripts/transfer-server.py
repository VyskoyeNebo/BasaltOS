#!/usr/bin/env python3
"""Local-only file bridge for the isolated VirtualBox NAT builder."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import shutil
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_PUT(self):
        relative = unquote(urlsplit(self.path).path).lstrip('/')
        target = (ROOT / relative).resolve()
        if not target.is_relative_to(ROOT) or relative.split('/')[0] not in ('work', 'out'):
            self.send_error(403)
            return
        target.parent.mkdir(parents=True, exist_ok=True)
        remaining = int(self.headers['Content-Length'])
        partial = target.with_name(target.name + '.partial')
        with partial.open('wb') as output:
            while remaining:
                block = self.rfile.read(min(1024 * 1024, remaining))
                if not block:
                    self.send_error(400)
                    return
                output.write(block)
                remaining -= len(block)
        partial.replace(target)
        self.send_response(201)
        self.send_header('Content-Length', '0')
        self.end_headers()

print('BasaltOS transfer bridge: http://127.0.0.1:8181', flush=True)
ThreadingHTTPServer(('127.0.0.1', 8181), Handler).serve_forever()

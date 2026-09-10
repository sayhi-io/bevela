"""Authenticated loopback-only read API and static observatory."""
import base64
import hashlib
import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading
from urllib.parse import urlparse, parse_qs

from .model import project
from .runtime import Store
from .workspace_inventory import observe as observe_workspace
from .local_git import Observer as LocalGitObserver

WEB=Path(__file__).parent/'web'


def handler(store,principals):
    local_git_observer=LocalGitObserver(store.config)
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args): pass  # No paths, credentials, or provider bodies in access logs.

        def send(self,status,body,kind='application/json'):
            data=json.dumps(body).encode() if kind=='application/json' else body
            self.send_response(status)
            self.send_header('Content-Type',kind)
            self.send_header('Content-Length',str(len(data)))
            self.send_header('Cache-Control','no-store')
            self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Referrer-Policy','no-referrer')
            self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'; form-action 'none'")
            if status==401:self.send_header('WWW-Authenticate','Basic realm="Project Intent", charset="UTF-8"')
            self.end_headers();self.wfile.write(data)

        def identity(self):
            value=self.headers.get('Authorization','')
            try:
                scheme,encoded=value.split(' ',1)
                if scheme!='Basic':return None
                name,token=base64.b64decode(encoded,validate=True).decode().split(':',1)
                principal=principals.get(name)
                if principal and hmac.compare_digest(hashlib.sha256(token.encode()).hexdigest(),principal['token_sha256']):
                    return principal
            except (ValueError,UnicodeError):pass
            return None

        def do_GET(self):
            if self.headers.get('Host') not in (f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}'):
                return self.send(403,{'error':'Host not allowed'})
            principal=self.identity()
            if not principal:return self.send(401,{'error':'Independent Project Intent credentials required'})
            request=urlparse(self.path)
            if request.path=='/api/v1/observatory':
                query=parse_qs(request.query)
                if set(query)-{'scope'} or len(query.get('scope',[]))>1:return self.send(400,{'error':'Invalid query'})
                selected=query.get('scope',[None])[0]
                try:result=project(store.view(),principal['scopes'],selected)
                except PermissionError:return self.send(403,{'error':'Scope not authorized'})
                inventory=observe_workspace(store.config,principal,result,selected)
                if inventory is not None:result['workspace_inventory']=inventory
                local_git=local_git_observer.view(principal,selected)
                if local_git is not None:result['local_git']=local_git
                return self.send(200,result)
            assets={'/':('index.html','text/html; charset=utf-8'),'/app.js':('app.js','text/javascript; charset=utf-8'),'/theme.js':('theme.js','text/javascript; charset=utf-8'),'/style.css':('style.css','text/css; charset=utf-8')}
            assets.update({'/observatory':('observatory.html','text/html; charset=utf-8'),'/observatory.js':('observatory.js','text/javascript; charset=utf-8'),'/observatory.css':('observatory.css','text/css; charset=utf-8')})
            assets['/workstream-map']=('observatory.html','text/html; charset=utf-8')
            assets.update({'/minimap.js':('minimap.js','text/javascript; charset=utf-8'),'/minimap.css':('minimap.css','text/css; charset=utf-8')})
            for name in ('workstream-map.js','workstream-map-facts.js','workstream-map.css','worker-group-facts.js','worker-groups.js','worker-groups.css','activity-views-facts.js','identity-facts.js','design-lab.js','design-lab.css'):
                assets['/'+name]=(name,'text/css; charset=utf-8' if name.endswith('.css') else 'text/javascript; charset=utf-8')
            if request.path in assets:
                file,kind=assets[request.path];return self.send(200,(WEB/file).read_bytes(),kind)
            return self.send(404,{'error':'Not found'})

        def do_POST(self):self.send(405,{'error':'Read-only observatory'})
        do_PUT=do_POST
        do_PATCH=do_POST
        do_DELETE=do_POST
    return Handler


def serve(config,port=8290):
    store=Store(config)
    server=ThreadingHTTPServer(('127.0.0.1',port),handler(store,config['principals']))
    stop=threading.Event()
    def refresh():
        while not stop.is_set():
            store.refresh();stop.wait(30)
    worker=threading.Thread(target=refresh,daemon=True);worker.start()
    print(f'Project Intent read-only observatory: http://127.0.0.1:{port}',flush=True)
    try:server.serve_forever()
    finally:stop.set();server.server_close()

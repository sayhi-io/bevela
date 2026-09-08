"""Opt-in real configured inventory proof, isolated loopback service, no writes."""
import json
import os
from pathlib import Path
import threading
from http.server import ThreadingHTTPServer
from playwright.sync_api import sync_playwright
from project_intent.runtime import Store
from project_intent.server import handler

config=json.loads(Path(os.environ['PI_MAP_CONFIG']).read_text())
access=json.loads(Path(os.environ['PI_MAP_ACCESS']).read_text())
store=Store(config)
server=ThreadingHTTPServer(('127.0.0.1',0),handler(store,config['principals']))
threading.Thread(target=server.serve_forever,daemon=True).start()
try:
    with sync_playwright() as p:
        browser=p.chromium.launch()
        page=browser.new_page(http_credentials={k:access[k] for k in ('username','password')},viewport={'width':1440,'height':1100})
        url='http://127.0.0.1:'+str(server.server_port)
        page.goto(url+'/observatory#sources');page.wait_for_selector('.inventory-table tbody tr')
        payload=page.request.get(url+'/api/v1/observatory').json()
        inventory=payload['workspace_inventory']
        assert inventory['status']=='observed'
        assert page.locator('.inventory-table tbody tr').count()==inventory['repository_count']
        assert inventory['repository_count']==20 and inventory['connected_count']==2
        page.locator('.inventory-table details summary').first.click()
        page.locator('.inventory-table details summary').first.focus()
        page.evaluate('render(data)')
        assert page.locator('.inventory-table details').first.get_attribute('open') is not None
        assert page.locator('.inventory-table summary:focus').count()==1
        out=Path(os.environ['PI_MAP_OUTPUT']);out.mkdir(parents=True,exist_ok=True)
        page.screenshot(path=str(out/'inventory.png'),full_page=True)
        page.select_option('#scope','sayhi/sparkops')
        page.wait_for_function('()=>document.querySelectorAll(".inventory-table tbody tr").length===1')
        assert 'sayhi-verify' not in page.locator('#workspace-inventory').inner_text()
        page.set_viewport_size({'width':390,'height':844})
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        browser.close()
finally:
    server.shutdown();server.server_close()
print('PASS real20-repository inventory,2connections,selected-scope isolation,mobile layout')

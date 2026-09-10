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
        assert inventory['repository_count']>0
        page.locator('.inventory-table button').first.click()
        selected=page.locator('#workspace-detail-title').inner_text()
        page.evaluate('render(data)')
        assert page.locator('#workspace-detail-title').inner_text()==selected
        page.keyboard.press('Escape')
        assert page.locator('.inventory-table button:focus').count()==1
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
print('PASS configured repository inventory,setup guide,selected-scope isolation,mobile layout')

"""Opt-in owner visual probe over REAL configured state; never changes live caches.

Run with PI_MAP_CONFIG, PI_MAP_ACCESS, PI_MAP_OUTPUT paths in the environment.
Artifacts are private observations, not checked-in test fixtures.
"""
import copy
import json
import os
from pathlib import Path
import shutil
import threading
from http.server import ThreadingHTTPServer
from playwright.sync_api import sync_playwright
from project_intent.runtime import Store
from project_intent.server import handler


def main():
    out=Path(os.environ['PI_MAP_OUTPUT']);out.mkdir(parents=True,exist_ok=True)
    config=copy.deepcopy(json.loads(Path(os.environ['PI_MAP_CONFIG']).read_text()))
    access=json.loads(Path(os.environ['PI_MAP_ACCESS']).read_text())
    for i,scope in enumerate(config['scopes']):
        cache=out/f'cache-{i}.json'
        if Path(scope['cache']).exists():shutil.copyfile(scope['cache'],cache)
        scope['cache']=str(cache)
    store=Store(config);store.refresh()
    server=ThreadingHTTPServer(('127.0.0.1',0),handler(store,config['principals']))
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    errors=[]
    try:
        with sync_playwright() as p:
            options={'executable_path':os.environ['BROWSER_EXECUTABLE']} if os.getenv('BROWSER_EXECUTABLE') else {}
            browser=p.chromium.launch(headless=True,args=['--disable-gpu','--disable-software-rasterizer'],**options)
            ctx=browser.new_context(http_credentials={'username':access['username'],'password':access['password']},viewport={'width':1536,'height':1100},reduced_motion='reduce')
            page=ctx.new_page();page.on('pageerror',lambda error:errors.append(str(error)))
            url=f'http://127.0.0.1:{server.server_port}'
            page.goto(url+'/workstream-map');page.wait_for_selector('.map-jelly')
            assert page.locator('#workstream-map').is_visible()
            result=page.request.get(url+'/api/v1/observatory').json()
            (out/'observation.json').write_text(json.dumps(result,indent=2)+'\n')
            page.select_option('#scope','sayhi/sparkops')
            page.wait_for_function("() => document.querySelectorAll('.map-jelly').length === 10")
            page.locator('.seam-choice').filter(has_text='spire/ha-authority').click()
            page.wait_for_function("() => document.querySelectorAll('.map-jelly').length === 3")
            assert page.locator('.convergence-band').count()==2
            page.screenshot(path=str(out/'sparkops-ha-dark.png'),full_page=True)
            page.locator('.display-options>summary').click();page.select_option('#theme','light');page.locator('.display-options>summary').click()
            page.screenshot(path=str(out/'sparkops-ha-light.png'),full_page=True)
            port=page.locator('.map-port.selected').first;port.focus();page.keyboard.press('Enter')
            page.wait_for_selector('#seam-detail[open]')
            assert page.locator('#seam-title').inner_text()=='spire/ha-authority'
            page.screenshot(path=str(out/'boundary-detail.png'),full_page=True)
            page.keyboard.press('Escape');assert not page.locator('#seam-detail').evaluate('(n)=>n.open')
            page.set_viewport_size({'width':390,'height':844})
            page.wait_for_timeout(250)
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            page.screenshot(path=str(out/'sparkops-ha-mobile.png'),full_page=True)
            page.set_viewport_size({'width':1536,'height':1100})
            page.route('**/api/v1/observatory*',lambda route:route.abort())
            page.click('#refresh');page.wait_for_selector('#error:not([hidden])')
            page.wait_for_function("() => document.getElementById('map-observation').textContent.includes('Disconnected')")
            assert page.locator('.worker-touching,.worker-approaching').count()==0
            page.select_option('#scope','sayhi/project-intent')
            assert page.locator('.map-jelly').count()==0
            page.unroute('**/api/v1/observatory*');page.click('#refresh');page.wait_for_selector('.map-jelly')
            page.check('#map-closed')
            page.screenshot(path=str(out/'platform-all-lifecycles.png'),full_page=True)
            page.goto(url+'/observatory#work');page.wait_for_selector('#workstreams .work-group')
            assert page.locator('.work-group .activity-chart').count()==0
            assert page.locator('.work-group .execution-badge').count()==0
            page.screenshot(path=str(out/'worker-groups-light.png'),full_page=True)
            page.locator('.display-options>summary').click();page.select_option('#theme','dark');page.locator('.display-options>summary').click();page.screenshot(path=str(out/'worker-groups-dark.png'),full_page=True)
            chip=page.locator('#workstreams .worker-chip.reporting').first
            selected_session=chip.get_attribute('data-session')
            selected_workstream=chip.get_attribute('data-group')
            chip.focus();page.keyboard.press('Enter');page.wait_for_selector('#worker-detail[open]')
            page.evaluate('() => refresh()')
            page.wait_for_timeout(100)
            page.screenshot(path=str(out/'worker-session-detail.png'),full_page=True)
            page.keyboard.press('Escape');assert not page.locator('#worker-detail').evaluate('(n)=>n.open')
            page.wait_for_function('(target) => document.activeElement.dataset.session===target.session && document.activeElement.dataset.group===target.workstream',arg={'session':selected_session,'workstream':selected_workstream})
            page.keyboard.press('Enter');page.wait_for_selector('#worker-detail[open]')
            page.route('**/api/v1/observatory*',lambda route:route.abort())
            page.evaluate('() => refresh()');page.wait_for_selector('#error:not([hidden])')
            captions=page.locator('#worker-detail .activity-caption').all_text_contents()
            assert captions,'This real-data probe requires an enrolled reporting session with telemetry history.'
            assert all('Retained history' in c for c in captions),captions
            page.keyboard.press('Escape');page.unroute('**/api/v1/observatory*');page.click('#refresh')
            page.wait_for_selector('#error[hidden]',state='attached')
            page.set_viewport_size({'width':390,'height':844});page.wait_for_timeout(250)
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            page.screenshot(path=str(out/'worker-groups-mobile.png'),full_page=True)
            page.route('**/api/v1/observatory*',lambda route:route.abort());page.click('#refresh')
            page.wait_for_selector('#error:not([hidden])')
            page.wait_for_function("() => document.querySelectorAll('.worker-chip.reporting,.worker-chip.present').length===0")
            page.select_option('#scope','sayhi/sparkops');assert page.locator('.work-group').count()==0
            page.unroute('**/api/v1/observatory*');page.click('#refresh');page.wait_for_selector('#workstreams .work-group')
            assert not errors,errors
            (out/'checks.json').write_text(json.dumps({'passed':['real normalized data','three HA surfaces and two undirected bands','keyboard boundary inspection and Escape','light/dark','390px no horizontal overflow','reduced motion context','disconnect suppresses worker declarations','scope change clears retained map','reconnect','all lifecycle filter','group cards have no charts','per-session keyboard inspector','group badge disconnect suppression','group scope clearing'],'workstreams':[w['key'] for w in result['workstreams']],'console_errors':errors},indent=2)+'\n')
            browser.close()
    finally:server.shutdown();server.server_close();thread.join()


if __name__=='__main__':main()

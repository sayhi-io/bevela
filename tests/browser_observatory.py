import argparse,copy,json,threading
from pathlib import Path
from http.server import ThreadingHTTPServer
from playwright.sync_api import sync_playwright, expect
from project_intent.runtime import Store
from project_intent.server import handler

parser=argparse.ArgumentParser(description='Browser dogfood over enrolled real state; never stops real services')
parser.add_argument('--state-dir',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
state=args.state_dir
out=args.output
out.mkdir(parents=True,exist_ok=True)
access=json.loads((state/'operator-access.json').read_text())
config=json.loads((state/'config.json').read_text())
credentials={'username':access['username'],'password':access['password']}
results=[]
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True)
 context=browser.new_context(http_credentials=credentials,viewport={'width':1440,'height':1000})
 page=context.new_page();errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
 page.goto(access['url'],wait_until='networkidle')
 page.wait_for_selector('.work-card')
 assert page.title()=='Mission Control · SayHi Project Intent'
 page.screenshot(path=str(out/'mission-control.png'))
 assert page.locator('#connection').text_content().startswith('Project Intent available')
 assert 'ENV-SUBSTRATE-01' in page.locator('#workstreams').inner_text()
 assert page.locator('.metric').count()==4
 assert not page.locator('#attention-dialog').is_visible()
 assert page.locator('.attention-panel').count()==0
 assert page.locator('.judgment-bar').bounding_box()['height']<100
 page.locator('#notifications').click()
 expect(page.locator('#attention-dialog')).to_be_visible()
 assert page.locator('#notification-count').inner_text()!='—'
 page.keyboard.press('Escape')
 expect(page.locator('#attention-dialog')).not_to_be_visible()
 expect(page.locator('#notifications')).to_be_focused()
 page.locator('#notifications').click()
 page.locator('#attention .attention-workstream').first.click()
 expect(page.locator('#detail')).to_be_visible()
 page.locator('#close').click()
 expect(page.locator('#attention-dialog')).to_be_visible()
 page.locator('#attention-close').click()
 results.append('Compact four-status header, notifications, Escape/focus return and workstream drill-down passed')
 page.locator('.work-card',has_text='ENV-SUBSTRATE-01').locator('.work-title').click()
 assert page.locator('#detail').is_visible()
 assert 'Availability: unknown / occupancy: unknown' in page.locator('#detail-content').inner_text()
 assert 'sparkops/local-dev-v1' in page.locator('#detail-content').inner_text()
 page.screenshot(path=str(out/'workstream-detail.png'))
 page.locator('#close').click()
 page.locator('#scope').select_option('sayhi/project-intent')
 scoped_payload=context.request.get(access['url']+'/api/v1/observatory?scope=sayhi/project-intent').json()
 open_work=[w for w in scoped_payload['workstreams'] if w['state'] in ('active','blocked','ready')]
 expect(page.locator('.work-card')).to_have_count(len(open_work))
 for work in scoped_payload['workstreams']:
  if work['state'] in ('active','blocked','ready'):
   assert work['id'] in page.locator('#workstreams').inner_text()
  else:
   assert work['id'] not in page.locator('#workstreams').inner_text()
 assert 'DEV-MCP-COMPAT-01' not in page.locator('#workstreams').inner_text()
 results.append('Real data, detail, environment unknown, and scope selection passed')
 page.set_viewport_size({'width':390,'height':844})
 assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
 page.locator('#notifications').click()
 expect(page.locator('#attention-dialog')).to_be_visible()
 assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
 page.locator('#attention-close').click()
 page.screenshot(path=str(out/'mission-control-mobile.png'))
 results.append('Mobile viewport has no horizontal overflow')
 assert not errors,errors
 context.close()
 reader=json.loads((state/'sparkops-reader-access.json').read_text())
 restricted=browser.new_context(http_credentials={'username':reader['username'],'password':reader['password']})
 response=restricted.request.get(access['url']+'/api/v1/observatory')
 payload=response.json();assert all(s['id']=='sayhi/sparkops' for s in payload['scopes'])
 assert restricted.request.get(access['url']+'/api/v1/observatory?scope=sayhi/project-intent').status==403
 restricted.close();results.append('Product-only credential cannot access platform scope')
 # Isolated observer instance: real last-known snapshots, no product feeds or PM
 # network calls. This never shuts down any actual product/provider service.
 outage=copy.deepcopy(config)
 for scope in outage['scopes']:
  scope['presence_sources']=[str(out/'intentionally-unavailable-execution-feed')]
  scope['enrollment_sources']=[]
  scope['activity_sources']=[]
  scope['provider']={'kind':'snapshot','path':scope['cache']}
 offline=Store(outage)
 for scoped in offline.states.values():scoped['provider_status']='unavailable'
 server=ThreadingHTTPServer(('127.0.0.1',0),handler(offline,outage['principals']))
 worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
 isolated=browser.new_context(http_credentials=credentials,viewport={'width':1440,'height':1000})
 q=isolated.new_page();q.goto('http://127.0.0.1:'+str(server.server_port),wait_until='networkidle');q.wait_for_selector('.work-card')
 assert q.locator('.work-card').count()>=8
 isolated_payload=isolated.request.get('http://127.0.0.1:'+str(server.server_port)+'/api/v1/observatory').json()
 assert all(not w['workers'] and w['activity']['status']=='not-connected' for w in isolated_payload['workstreams'])
 assert 'cached/offline provider state' in q.locator('#connection').text_content()
 q.locator('#notifications').click()
 assert 'Execution observations unavailable; durable intent remains visible' in q.locator('#attention').inner_text()
 q.screenshot(path=str(out/'outage-observatory.png'))
 isolated.close();server.shutdown();server.server_close();worker.join()
 results.append('Browser remains useful with real cached state, provider marked unavailable and all execution feeds absent; no real service stopped')
 browser.close()
(out/'browser-results.json').write_text(json.dumps({'passed':results,'page_errors':errors},indent=2)+'\n')
print(json.dumps(results,indent=2))

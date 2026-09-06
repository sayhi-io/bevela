"""Candidate assets over real cached state; no live service/provider mutation."""
import argparse
import copy
import json
from pathlib import Path
import threading
from http.server import ThreadingHTTPServer
from playwright.sync_api import sync_playwright, expect
from project_intent.runtime import Store
from project_intent.server import handler

parser=argparse.ArgumentParser()
parser.add_argument('--state-dir',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
config=json.loads((args.state_dir/'config.json').read_text())
access=json.loads((args.state_dir/'operator-access.json').read_text())
for scope in config['scopes']:scope['provider']={'kind':'snapshot','path':scope['cache']}
store=Store(config)
server=ThreadingHTTPServer(('127.0.0.1',0),handler(store,config['principals']))
thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
base='http://127.0.0.1:'+str(server.server_port)
results=[]
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(headless=True)
  context=browser.new_context(http_credentials={'username':access['username'],'password':access['password']},viewport={'width':1440,'height':1050})
  page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.goto(base+'/observatory');page.wait_for_selector('#rested .tile')
  expect(page.locator('#view-title')).to_have_text('Overview')
  expect(page.locator('#architecture')).not_to_be_visible()
  page.locator('#theme').select_option('dark')
  page.wait_for_function("() => getComputedStyle(document.querySelector('#live-work .work-card')).backgroundColor==='rgb(25, 32, 27)'")
  page.screenshot(path=str(args.output/'home-dark.png'),animations='disabled')
  page.locator('#view-nav a[href="#handoffs"]').click()
  expect(page.locator('#reports .report-card').first).to_be_visible()
  page.locator('#reports button').first.click()
  expect(page.locator('#worker-report-detail')).to_be_visible()
  assert 'publication receipt' in page.locator('#worker-report-detail').inner_text()
  receipt=page.locator('#worker-report-detail details').first
  receipt.locator('summary').click();receipt.locator('summary').focus()
  page.evaluate('() => render(data)')
  expect(receipt).to_have_attribute('open','')
  expect(receipt.locator('summary')).to_be_focused()
  page.keyboard.press('Escape')
  page.go_back();expect(page.locator('#view-title')).to_have_text('Overview')
  page.go_forward();expect(page.locator('#view-title')).to_have_text('Handoffs')
  page.locator('#scope').select_option('sayhi/project-intent')
  page.wait_for_function("() => data && data.scopes.length===1")
  assert 'sayhi/sparkops' not in page.locator('#reports').inner_text()
  page.locator('#theme').select_option('light')
  page.wait_for_function("() => getComputedStyle(document.querySelector('#reports .tile')).backgroundColor==='rgb(250, 252, 246)'")
  page.screenshot(path=str(args.output/'handoffs-light.png'),animations='disabled')
  page.locator('#view-nav a[href="#home"]').focus();page.keyboard.press('Enter')
  expect(page.locator('#view-title')).to_be_focused()
  page.set_viewport_size({'width':390,'height':844})
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
  page.screenshot(path=str(args.output/'home-mobile.png'))
  for view in ['work','architecture','environments','handoffs','sources']:
   page.locator('#view-nav a[href="#'+view+'"]').click()
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),view
  results.append('Candidate-only real-cache desktop/mobile, light/dark, navigation/history/keyboard and scoped report/detail checks passed')
  # Browser disconnection retains clearly labeled observations; no real outage.
  page.route('**/api/v1/observatory*',lambda route:route.abort())
  page.locator('#refresh').click();expect(page.locator('#error')).to_be_visible()
  assert 'retained view' in page.locator('#connection-summary').inner_text()
  assert not errors,errors
  results.append('Connection failure labeled retained view, no invented live state')
  context.close();browser.close()
finally:
 server.shutdown();server.server_close();thread.join()
(args.output/'results.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results,indent=2))

"""Minimap interactions over the real local cache; candidate-only loopback server."""
import argparse
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
server=ThreadingHTTPServer(('127.0.0.1',0),handler(Store(config),config['principals']))
thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(headless=True)
  context=browser.new_context(http_credentials=access,viewport={'width':1440,'height':1050},reduced_motion='reduce')
  page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.goto(f'http://127.0.0.1:{server.server_port}/observatory#work')
  page.wait_for_selector('#workstreams .work-card')
  expect(page.locator('#page-minimap')).not_to_be_visible()
  page.screenshot(path=str(args.output/'minimap-collapsed-desktop.png'),animations='disabled')
  page.locator('#minimap-toggle').click()
  expect(page.locator('#page-minimap')).to_be_visible()
  expect(page.locator('.minimap-entry')).to_have_count(3)
  assert page.locator('.minimap-entry').first.get_attribute('aria-label').startswith('1. All workstreams')
  page.locator('[aria-label="Card view"]').click()
  expect(page.locator('#page-minimap')).to_have_attribute('data-mode','cards')
  assert page.locator('.minimap-preview-row').first.inner_text() in page.locator('#workstreams').inner_text()
  page.locator('.minimap-entry').first.focus()
  page.evaluate('render(data)')
  expect(page.locator('.minimap-entry').first).to_be_focused()
  page.locator('#theme').select_option('light')
  page.wait_for_function("() => getComputedStyle(document.querySelector('#page-minimap')).backgroundColor==='rgb(251, 252, 250)'")
  page.screenshot(path=str(args.output/'minimap-cards-light.png'),animations='disabled')
  page.locator('#minimap-width').focus();before=page.locator('#page-minimap').bounding_box()['width']
  page.keyboard.press('ArrowRight');assert page.locator('#page-minimap').bounding_box()['width']>before
  grip=page.locator('.minimap-grip').bounding_box();page.mouse.move(grip['x']+8,grip['y']+20);page.mouse.down();page.mouse.move(grip['x']+88,grip['y']+20);page.mouse.up()
  assert page.locator('#page-minimap').bounding_box()['width']>before+50
  page.locator('[aria-label="List view"]').click()
  page.locator('[data-map-key="initiatives"]').click()
  expect(page.locator('#initiatives').locator('xpath=..').locator('h2')).to_be_focused()
  expect(page.locator('[data-map-key="initiatives"]')).to_have_attribute('aria-current','location')
  page.keyboard.press('Escape');expect(page.locator('#minimap-toggle')).to_be_focused()
  page.locator('#minimap-toggle').click()
  page.locator('#view-nav a[href="#architecture"]').click()
  expect(page.locator('.minimap-entry')).to_have_count(page.locator('#architecture .tile').count())
  target=page.locator('.minimap-entry').last
  target.focus();page.evaluate('render(data)')
  expect(page.locator('.minimap-entry').last).to_be_focused()
  target.click()
  expect(page.locator('#architecture .tile').last.locator('h3')).to_be_focused()
  assert page.locator('#minimap-index').evaluate('(node) => node.scrollTop > 0')
  page.locator('#theme').select_option('dark')
  page.wait_for_function("() => getComputedStyle(document.querySelector('#page-minimap')).backgroundColor==='rgb(28, 37, 31)'")
  page.screenshot(path=str(args.output/'minimap-list-dark.png'),animations='disabled')
  page.locator('#notifications').click();page.keyboard.press('Escape')
  expect(page.locator('#page-minimap')).to_be_visible()
  page.set_viewport_size({'width':390,'height':844})
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
  page.wait_for_function("() => document.querySelector('#page-minimap').getBoundingClientRect().right <= innerWidth")
  box=page.locator('#page-minimap').bounding_box();assert box['x']>=0 and box['x']+box['width']<=390 and box['y']>=80,box
  page.screenshot(path=str(args.output/'minimap-mobile.png'),animations='disabled')
  page.keyboard.press('Escape')
  page.screenshot(path=str(args.output/'minimap-collapsed-mobile.png'),animations='disabled')
  page.locator('#minimap-toggle').click()
  page.route('**/api/v1/observatory*',lambda route:route.abort())
  page.locator('#scope').select_option('sayhi/project-intent')
  expect(page.locator('#error')).to_be_visible()
  expect(page.locator('.minimap-source')).to_contain_text('Connection unavailable')
  assert 'sayhi/sparkops' not in page.locator('#page-minimap').inner_text()
  assert page.locator('.minimap-preview-row').count()==0
  page.unroute('**/api/v1/observatory*');page.locator('#refresh').click()
  page.wait_for_function("() => data && data.scopes.length===1")
  assert 'sayhi/sparkops' not in page.locator('#page-minimap').inner_text()
  assert not errors,errors
  context.close();browser.close()
finally:
 server.shutdown();server.server_close();thread.join()
print('Real-cache minimap list/cards, refresh focus, resize, scope failure, dialogs, keyboard, light/dark and mobile passed')

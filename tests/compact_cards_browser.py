"""Opt-in real-data UI probe. Requires PI_MAP_ACCESS; previews source assets only."""
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

access = json.loads(Path(os.environ['PI_MAP_ACCESS']).read_text())
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(http_credentials={k: access[k] for k in ('username', 'password')}, viewport={'width': 1440, 'height': 1000})
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))

    def asset(route):
        name = route.request.url.rsplit('/', 1)[-1]
        route.fulfill(body=Path('project_intent/web', name).read_text(), content_type='text/css' if name.endswith('css') else 'text/javascript')

    for name in ('worker-groups.js', 'worker-groups.css'):
        page.route('**/' + name, asset)
    page.goto('http://127.0.0.1:8290/observatory#work')
    page.wait_for_selector('.work-group:visible')
    assert page.locator('.work-group:visible').evaluate_all('(xs)=>xs.every(x=>x.getBoundingClientRect().height===280)')
    assert page.locator('.work-group details').count() == 0
    page.locator('.work-group:visible .history-trigger').first.click()
    identifier = page.locator('.session-history-row code').first.inner_text()
    page.locator('#session-history input').fill(identifier)
    assert page.locator('.session-history-row').count() == 1
    page.evaluate('render(data)')
    assert page.locator('#session-history input').input_value() == identifier
    page.locator('.session-history-row button').last.click()
    page.locator('#worker-detail').wait_for(state='visible')
    page.evaluate('render(data)')
    page.keyboard.press('Escape')
    page.wait_for_function("()=>!!document.activeElement.closest('.session-history-row')")
    page.evaluate("document.getElementById('error').hidden=false")
    page.wait_for_timeout(100)
    assert 'tok/s' not in page.locator('.session-history-row').inner_text()
    page.locator('#session-history .detail-top button').focus()
    page.keyboard.press('Escape')
    page.wait_for_function("()=>document.activeElement.classList.contains('history-trigger')")
    page.evaluate("document.getElementById('error').hidden=true;render(data)")
    output = Path(os.environ['PI_MAP_OUTPUT'])
    output.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(output / 'desktop.png'))
    page.set_viewport_size({'width': 390, 'height': 844})
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    page.screenshot(path=str(output / 'mobile.png'))
    assert not errors, errors
    browser.close()
print('PASS: uniform cards, separate searchable history, refresh/outage, focus restoration, mobile layout')

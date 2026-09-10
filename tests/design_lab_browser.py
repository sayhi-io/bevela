"""Opt-in real-data visual proof; source assets previewed, API reads unchanged."""
import json
import os
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import expect, sync_playwright

access=json.loads(Path(os.environ['PI_MAP_ACCESS']).read_text())
out=Path(os.environ['PI_MAP_OUTPUT']);out.mkdir(parents=True,exist_ok=True)
with sync_playwright() as p:
    options={'executable_path':os.environ['BROWSER_EXECUTABLE']} if os.getenv('BROWSER_EXECUTABLE') else {}
    browser=p.chromium.launch(args=['--disable-gpu','--disable-software-rasterizer'],**options)
    context=browser.new_context(http_credentials={k:access[k] for k in ('username','password')},viewport={'width':1536,'height':1100},reduced_motion='reduce')
    page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))

    def source(route):
        path=urlparse(route.request.url).path
        name='observatory.html' if path in ('/observatory','/workstream-map') else path.removeprefix('/')
        file=Path('project_intent/web')/name
        if '/' not in name and file.is_file():
            kind='text/html' if name.endswith('.html') else 'text/css' if name.endswith('.css') else 'text/javascript'
            route.fulfill(body=file.read_bytes(),content_type=kind)
        else:route.continue_()

    page.route('http://127.0.0.1:8290/**',source)
    reference=None
    for variant in ('default','plan','studio','console','unknown'):
        page.set_viewport_size({'width':1536,'height':1100})
        page.goto('http://127.0.0.1:8290/observatory?design='+variant+'#work')
        page.wait_for_selector('.work-group:visible .work-identicon')
        expect(page.locator('.design-picker select')).to_be_hidden()
        page.locator('.display-options>summary').click()
        expect(page.locator('.design-picker select')).to_be_visible()
        assert page.locator('html').get_attribute('data-design')==('default' if variant=='unknown' else variant)
        key=page.locator('.work-group:visible').first.get_attribute('data-group')
        mark=page.locator('.work-group:visible .work-identicon').first.inner_html()
        if reference is None:reference=(key,mark)
        if reference[0]==key:assert reference[1]==mark
        for theme in ('light','dark'):
            page.select_option('#theme',theme)
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
            assert page.locator('.work-group:visible .pr-chip').evaluate_all('(xs)=>xs.every(x=>{const p=x.parentElement.getBoundingClientRect(),r=x.getBoundingClientRect();return r.bottom<=p.bottom+1&&r.top>=p.top-1;})')
            page.screenshot(path=str(out/(variant+'-'+theme+'.png')))
        page.locator('.display-options>summary').click()
        page.locator('.work-group:visible .group-context').first.click()
        assert page.locator('#detail .work-identicon').first.inner_html()==mark
        page.keyboard.press('Escape')
        page.set_viewport_size({'width':390,'height':844})
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),variant
        page.screenshot(path=str(out/(variant+'-mobile.png')))
        page.locator('#view-nav a[href="#map"]').click()
        page.wait_for_selector('.jelly-center .work-identicon')
        assert page.locator('#workstream-map').is_visible()
    page.locator('.display-options>summary').click()
    page.select_option('.design-picker select','plan')
    page.wait_for_url('**design=plan#map')
    page.wait_for_selector('.jelly-center .work-identicon')
    assert page.locator('html').get_attribute('data-design')=='plan'
    assert not errors,errors
    browser.close()
print('PASS5flags × light/dark/mobile, stable card/detail avatars, map icons/navigation, no JS errors')

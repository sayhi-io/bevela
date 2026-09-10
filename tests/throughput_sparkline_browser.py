"""Deterministic local-asset browser probe; no service, credentials or live data.

Run with the checkout-owned optional Playwright environment (docs/OPERATIONS.md):
  BROWSER_EXECUTABLE=/path/to/headless_shell .venv/bin/python \
    tests/throughput_sparkline_browser.py --output /private/evidence/sparklines
"""
import argparse
import copy
import json
import mimetypes
import os
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright, expect
from project_intent.model import project

ROOT = Path(__file__).resolve().parents[1]
NOW = 1800000000


def fixture():
    snapshot = json.loads((ROOT / '.project-intent/snapshot.json').read_text())
    scope = snapshot['scope_id']
    payload = project([{'id': scope, 'label': 'Project Intent', 'snapshot': snapshot,
                        'provider_status': 'offline'}], [scope])
    work = next(w for w in payload['workstreams'] if w['id'] == 'PI-MISSION-01')
    work['title'] = 'Physical TPM baseline gates and narrow Go mechanics adapter experiment'
    work['workers'] = [{'session': 'sparkline-browser-fixture', 'status': 'active',
                        'working': 'Deterministic UI fixture, not a real registration',
                        'heartbeat_at': '2027-01-15T07:59:59Z',
                        'expires_at': '2027-01-15T09:00:00Z'}]
    values = [9, 13, 12, 20, 22, 17, 8, 9, 14, 13, 24, 19, 17, 19.6]
    metric = {'session': 'sparkline-browser-fixture', 'status': 'recent',
              'last_report_at': NOW-2,
              'points': [{'at': NOW-782+i*60, 'value': value}
                         for i, value in enumerate(values)]}
    work['activity'] = {'sessions': [metric]}
    payload['workstreams'] = [work]
    return payload


def run(output):
    output.mkdir(parents=True, exist_ok=True)
    payload = fixture()
    with sync_playwright() as p:
        options = {'executable_path': os.environ['BROWSER_EXECUTABLE']} if os.getenv('BROWSER_EXECUTABLE') else {}
        # This SVG/CSS probe needs no GPU. DGX headless software-GPU startup can
        # stall compositor frames; use Chromium's CPU page rendering explicitly.
        browser = p.chromium.launch(args=['--disable-gpu', '--disable-software-rasterizer'], **options)
        page = browser.new_page(viewport={'width': 1440, 'height': 1000})
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.add_init_script(f'Date.now = () => {NOW * 1000};')

        def route(request):
            url = urlsplit(request.request.url)
            if url.netloc != 'pi.test':
                request.abort()
            elif url.path == '/api/v1/observatory':
                request.fulfill(json=payload)
            else:
                name = 'observatory.html' if url.path == '/observatory' else url.path.lstrip('/')
                asset = ROOT / 'project_intent/web' / name
                if asset.parent != ROOT / 'project_intent/web' or not asset.is_file():
                    request.fulfill(status=404)
                else:
                    request.fulfill(body=asset.read_bytes(), content_type=mimetypes.guess_type(name)[0] or 'text/plain')

        page.route('**/*', route)
        page.goto('http://pi.test/observatory')
        card = page.locator('#live-work .work-group').first
        chart = card.locator('.worker-throughput')
        expect(chart).to_be_visible()
        expect(chart.locator('.worker-rate')).to_have_text('19.6 tok/s')
        assert ' C' in chart.locator('path').get_attribute('d')
        assert chart.locator('circle, text, line, rect').count() == 0
        for width in (1440, 800, 390, 320):
            page.set_viewport_size({'width': width, 'height': 1000})
            for theme in ('light', 'dark'):
                page.select_option('#theme', theme)
                bounds, history = chart.bounding_box(), card.locator('.history-trigger').bounding_box()
                assert bounds['height'] == 32
                assert bounds['x'] + bounds['width'] <= history['x'] - 4
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                card.screenshot(path=str(output / f'card-{width}-{theme}.png'))
        chart.focus()
        page.keyboard.press('Enter')
        expect(page.locator('#worker-detail')).to_be_visible()
        page.evaluate('render(data)')
        page.keyboard.press('Escape')
        expect(chart).to_be_focused()
        card.locator('.history-trigger').click()
        expect(page.locator('#session-history')).to_be_visible()
        page.keyboard.press('Escape')
        expect(card.locator('.history-trigger')).to_be_focused()
        # Other sessions stay individually available in history, not squeezed
        # into unreadable values/zero-width charts or added into a combined rate.
        multiple = copy.deepcopy(payload)
        work = multiple['workstreams'][0]
        for i in range(1, 4):
            presence = dict(work['workers'][0], session=f'fixture-{i}')
            work['workers'].append(presence)
            work['activity']['sessions'].append(dict(work['activity']['sessions'][0], session=f'fixture-{i}'))
        page.evaluate('value => render(value)', multiple)
        expect(card.locator('.worker-throughput')).to_have_count(1)
        assert card.locator('.history-trigger').inner_text().startswith('+3')
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        assert card.locator('.worker-throughput').evaluate_all('(nodes) => nodes.every(n => n.getBoundingClientRect().right <= n.closest(".worker-strip").querySelector(".history-trigger").getBoundingClientRect().left)')
        rate = card.locator('.worker-rate').bounding_box()
        svg = card.locator('.worker-sparkline').bounding_box()
        assert svg['width'] >= 40
        assert rate['x'] + rate['width'] < svg['x']
        assert svg['x'] + svg['width'] < card.locator('.history-trigger').bounding_box()['x']
        card.locator('.history-trigger').click()
        expect(page.locator('.session-history-row')).to_have_count(4)
        page.keyboard.press('Escape')
        # A genuine zero stays measured; a lone sample never fabricates a line.
        zero = copy.deepcopy(payload)
        zero['workstreams'][0]['activity']['sessions'][0]['points'] = [{'at': NOW-2, 'value': 0}]
        page.evaluate('value => render(value)', zero)
        expect(card.locator('.worker-rate')).to_have_text('0.0 tok/s')
        assert card.locator('.worker-sparkline path').count() == 0
        for kind in ('stale', 'unmeasured', 'released', 'ambiguous'):
            unknown = copy.deepcopy(payload)
            work = unknown['workstreams'][0]
            if kind == 'stale':
                work['activity']['sessions'][0]['status'] = 'stale'
            elif kind == 'unmeasured':
                work['activity'] = {'status': 'not-connected', 'points': []}
            elif kind == 'released':
                work['workers'][0]['status'] = 'inactive'
            else:
                work['workers'].append(copy.deepcopy(work['workers'][0]))
            page.evaluate('value => render(value)', unknown)
            assert page.locator('.worker-throughput').count() == 0
        page.evaluate('value => render(value)', payload)
        page.evaluate('document.getElementById("error").hidden = false')
        expect(page.locator('.worker-throughput')).to_have_count(0)
        page.evaluate('document.getElementById("error").hidden = true; render(data)')
        expect(chart).to_be_visible()
        assert not errors, errors
        browser.close()
    print('PASS: curved real-sample rendering, 4 widths × 2 themes, multiple sessions, keyboard/detail/history, zero/single/unknown/released/ambiguous/outage states')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    run(parser.parse_args().output)

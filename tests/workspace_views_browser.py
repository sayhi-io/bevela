"""Deterministic database views and repository guide; no external service writes."""
import argparse
import copy
import mimetypes
import os
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import expect, sync_playwright
from activity_views_browser import ROOT, fixture


def run(output):
    output.mkdir(parents=True, exist_ok=True)
    payload = fixture()
    work = payload['workstreams'][0]
    work['statement'] += ' searchable-hidden-work-description'
    for i in range(1, 16):
        other = copy.deepcopy(work)
        other.update(id=f'fixture-{i}', key=f'{work["scope_id"]}:fixture-{i}',
                     title=f'Other work {i}', state='blocked', workers=[])
        other['local_reports'] = []
        other['handoff_summary'] = f'Provider handoff {i}'
        other['handoff_at'] = None
        payload['workstreams'].append(other)
    for i in range(45):
        report = copy.deepcopy(work['local_reports'][0])
        report['id'] = f'additional-{i}'
        report['payload']['packet']['summary'] = f'Additional report {i}; hidden-tail-{i}'
        work['local_reports'].append(report)
    payload['workspace_inventory'] = {
        'status': 'observed', 'repository_count': 3, 'connected_count': 1,
        'observed_at': payload['observed_at'], 'meaning': 'Fixture canonical Git directories.',
        'repositories': [
            {'repository': 'connected-repo', 'scope': work['scope_id'],
             'checkout': '/fixture/task', 'intent_status': 'configured',
             'provider_status': 'live', 'enrolled_workstreams': 16},
            {'repository': 'unmapped-repo', 'scope': None, 'checkout': "/fixture/it's a repo",
             'intent_status': 'not-mapped', 'enrolled_workstreams': None},
            {'repository': 'disconnected-repo', 'scope': work['scope_id'], 'checkout': '/fixture/mapped',
             'intent_status': 'scope-not-connected', 'enrolled_workstreams': None},
        ],
    }
    unavailable = False
    with sync_playwright() as p:
        options = {'executable_path': os.environ['BROWSER_EXECUTABLE']} if os.getenv('BROWSER_EXECUTABLE') else {}
        browser = p.chromium.launch(args=['--disable-gpu', '--disable-software-rasterizer'], **options)
        page = browser.new_page(viewport={'width': 1440, 'height': 1000})
        errors, writes = [], []
        page.on('pageerror', lambda error: errors.append(str(error)))

        def route(request):
            url = urlsplit(request.request.url)
            if request.request.method != 'GET':
                writes.append(request.request.method + ' ' + url.path)
                request.abort()
            elif url.netloc != 'pi.test':
                request.abort()
            elif url.path == '/api/v1/observatory':
                request.fulfill(status=503) if unavailable else request.fulfill(json=payload)
            else:
                name = 'observatory.html' if url.path == '/observatory' else url.path.lstrip('/')
                asset = ROOT / 'project_intent/web' / name
                if asset.parent != ROOT / 'project_intent/web' or not asset.is_file():
                    request.fulfill(status=404)
                else:
                    request.fulfill(body=asset.read_bytes(), content_type=mimetypes.guess_type(name)[0] or 'text/plain')

        def navigate(view):
            page.locator(f'#view-nav a[href="#{view}"]').click()
            expect(page.locator('html')).to_have_attribute('data-current-view', view)

        page.route('**/*', route)
        page.goto('http://pi.test/observatory#work')
        expect(page.locator('#work-count')).to_have_text('16 of 16')
        page.locator('#work-filter').select_option('blocked')
        expect(page.locator('#workstreams .work-group:visible')).to_have_count(15)
        page.locator('#work-group').select_option('state')
        expect(page.locator('.work-group-heading')).to_have_text('blocked · 15')
        page.locator('#work-sort').select_option('title')
        titles = page.locator('#workstreams .work-group:visible .work-title').all_inner_texts()
        assert titles[0].strip() == 'Other work 1' and titles[-1].strip() == 'Other work 9', titles
        page.locator('#work-search').fill('Other work 3')
        expect(page.locator('#workstreams .work-group:visible')).to_have_count(1)
        page.locator('#work-search').fill('unmatched-term')
        expect(page.locator('#work-count')).to_have_text('0 of 16')
        expect(page.locator('#workstreams .database-empty')).to_be_visible()
        page.locator('#work-filter').select_option('')
        page.locator('#work-search').fill('searchable-hidden-work-description')
        expect(page.locator('#workstreams .work-group:visible')).to_have_count(16)
        page.locator('#work-search').fill('')
        page.evaluate("""() => {
          window.countChanges = 0;
          window.countObserver = new MutationObserver(records => window.countChanges += records.length);
          for (const node of document.querySelectorAll('.database-count')) window.countObserver.observe(node, {childList:true,subtree:true,characterData:true});
          render(data);
        }""")
        assert page.evaluate('window.countChanges') == 0
        page.evaluate('window.countObserver.disconnect()')

        navigate('developers')
        page.locator('#developer-search').fill('Other work 15')
        expect(page.locator('#developer-evidence .developer-card')).to_have_count(0)  # undated handoffs aren't timed observations
        page.locator('#developer-search').fill('calendar-active-session')
        expect(page.locator('#developer-active .developer-card')).to_have_count(1)
        page.locator('#developer-search').fill('')

        navigate('handoffs')
        expect(page.locator('#reports .reference-row')).to_have_count(40)
        page.locator('#handoff-more').click()
        expect(page.locator('#reports .reference-row')).to_have_count(46)
        page.locator('#handoff-search').fill('hidden-tail-44')
        expect(page.locator('#reports .reference-row')).to_have_count(1)
        page.locator('#reports .record-link').click()
        expect(page.locator('#workspace-detail')).to_be_visible()
        assert 'hidden-tail-44' in page.locator('#workspace-detail-content').inner_text()
        page.evaluate("""() => {data.workstreams[0].local_reports.at(-1).payload.packet.summary += ' Updated evidence'; render(data);} """)
        assert 'Updated evidence' in page.locator('#workspace-detail-content').inner_text()
        page.evaluate("() => {data.workstreams[0].title='Updated work title'; render(data);}")
        assert 'Updated work title' in page.locator('#workspace-detail-content').inner_text()
        page.keyboard.press('Escape')
        expect(page.locator('#reports .record-link')).to_be_focused()
        page.evaluate('render(data)')
        expect(page.locator('#reports .record-link')).to_be_focused()
        page.locator('#handoff-search').fill('')
        page.locator('#handoff-type').select_option('handoff')
        expect(page.locator('#reports .reference-row')).to_have_count(16)
        assert 'Undated' in page.locator('#reports').inner_text()
        expect(page.locator('#handoff-state')).to_be_hidden()
        page.locator('#reports .record-link').first.click()
        page.locator('#workspace-detail .event-source summary').click()
        page.locator('#workspace-detail .event-source summary').focus()
        page.evaluate("() => {data.workstreams[0].provider_identifier='UPDATED-REF'; render(data);}")
        assert 'UPDATED-REF' in page.locator('#workspace-detail .event-source').inner_text()
        expect(page.locator('#workspace-detail .event-source summary')).to_be_focused()
        page.keyboard.press('Escape')

        navigate('architecture')
        page.locator('#architecture-search').fill('no-such-constraint')
        expect(page.locator('#architecture-count')).to_have_text('0 records')
        page.locator('#architecture-search').fill('')
        page.locator('#architecture .record-link').first.click()
        assert payload['architecture'][0]['statement'] in page.locator('#workspace-detail-content').inner_text()
        page.keyboard.press('Escape')

        navigate('environments')
        page.locator('#environment-search').fill('no-such-environment')
        expect(page.locator('#environment-count')).to_have_text('0 records')
        page.locator('#environment-search').fill('')

        navigate('sources')
        page.locator('#source-filter').select_option('needs-setup')
        expect(page.locator('.inventory-table tbody tr')).to_have_count(2)
        page.locator('#source-search').fill('unmapped')
        expect(page.locator('.inventory-table tbody tr')).to_have_count(1)
        page.locator('.inventory-table button').first.click()
        expect(page.locator('#workspace-detail-title')).to_have_text('unmapped-repo')
        assert 'does not change configuration' in page.locator('#workspace-detail-content').inner_text()
        expect(page.locator('#setup-scope')).to_have_value('')
        page.locator('#setup-scope').fill('org/new-project')
        assert "--scope 'org/new-project'" in page.locator('.setup-snippet pre').first.inner_text()
        assert "it'\"'\"'s a repo" in page.locator('.setup-snippet pre').first.inner_text()
        page.evaluate('render(data)')
        expect(page.locator('#setup-scope')).to_have_value('org/new-project')
        page.screenshot(path=str(output / 'repository-guide.png'))
        page.keyboard.press('Escape')
        expect(page.locator('.inventory-table button').first).to_be_focused()
        page.locator('#source-filter').select_option('')
        page.locator('#source-search').fill('')
        page.locator('#source-mode').select_option('scopes')
        expect(page.locator('#workspace-inventory')).to_be_hidden()
        page.locator('#source-mode').select_option('repositories')
        page.locator('#repository-setup').click()
        expect(page.locator('#workspace-detail .record-link')).to_have_count(3)
        page.locator('#workspace-detail .record-link').first.click()
        page.keyboard.press('Escape')
        expect(page.locator('#repository-setup')).to_be_focused()

        for width in (1440, 390):
            page.set_viewport_size({'width': width, 'height': 1000 if width == 1440 else 844})
            for theme in ('light', 'dark'):
                page.evaluate('theme=>document.documentElement.dataset.theme=theme', theme)
                for view in ('home', 'work', 'developers', 'calendar', 'map', 'architecture', 'environments', 'handoffs', 'sources'):
                    navigate(view)
                    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'), (view, width, theme)
                    page.screenshot(path=str(output / f'{view}-{width}-{theme}.png'))
                page.locator('.inventory-table button').first.click()
                assert page.locator('#workspace-detail').evaluate('node=>node.scrollWidth<=node.clientWidth'), (width, theme)
                page.keyboard.press('Escape')

        # Scope changes clear the pane and all old records before a failed response.
        page.locator('.inventory-table button').first.click()
        unavailable = True
        page.locator('#scope').select_option(work['scope_id'])
        expect(page.locator('#workspace-detail')).not_to_be_visible()
        expect(page.locator('#workspace-detail-content')).to_be_empty()
        expect(page.locator('#error')).to_be_visible()
        for view, control in [('work', '#work-search'), ('sources', '#source-search'), ('handoffs', '#handoff-search'), ('architecture', '#architecture-search'), ('environments', '#environment-search'), ('developers', '#developer-search')]:
            navigate(view)
            page.locator(control).fill('')
        for selector in ('#workstreams', '#reports', '#workspace-inventory', '#architecture', '#environments', '#developer-active'):
            expect(page.locator(selector)).to_be_empty()
        assert not errors, errors
        assert not writes, writes
        browser.close()
    print('PASS: view controls, repository guidance, undated evidence, scope failure, nine views at two widths/themes; no writes')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    run(parser.parse_args().output)

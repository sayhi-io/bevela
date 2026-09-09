"""Native Chromium acceptance for the Luna release study's history-v2 browser."""

import asyncio
import json
import os
from pathlib import Path
import re
import select
import subprocess
import unittest
from urllib.parse import parse_qs, urlencode, urlparse

from playwright.async_api import async_playwright, expect


HERE = Path(__file__).resolve().parent
EXECUTABLE = os.environ.get(
    "BROWSER_EXECUTABLE",
    "/home/meanaverage/sayhi/state/project-intent/browser-test/"
    "chromium_headless_shell-1234/chrome-linux/headless_shell",
)


class LunaReleaseBrowser(unittest.IsolatedAsyncioTestCase):
    """The fixture is the only state-mutating service used by these tests."""

    def setUp(self):
        checkout = os.environ.get("TRIAL_CHECKOUT")
        if not checkout:
            raise RuntimeError("TRIAL_CHECKOUT required")
        self.server = subprocess.Popen(
            ["node", str(HERE / "luna_release_fixture.mjs")],
            stdout=subprocess.PIPE,
            stderr=None,
            text=True,
            env=os.environ.copy(),
        )
        try:
            if not select.select([self.server.stdout], [], [], 10)[0]:
                raise RuntimeError("Luna fixture did not become ready within 10 seconds")
            line = self.server.stdout.readline()
            if not line:
                raise RuntimeError("Luna fixture exited before readiness")
            self.fixture = json.loads(line)
            self.origin = self.fixture["origin"]
            for key in ("rows", "components", "marker"):
                if key not in self.fixture:
                    raise RuntimeError(f"Luna fixture readiness omitted {key}")
        except BaseException:
            self.server.terminate()
            self.server.wait(timeout=10)
            raise

    def tearDown(self):
        self.server.terminate()
        try:
            self.server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.server.kill()
            self.server.wait(timeout=10)
        self.server.stdout.close()

    async def asyncSetUp(self):
        self.pw = await async_playwright().start()
        self.browser = await self.pw.chromium.launch(executable_path=EXECUTABLE)
        self.context = await self.browser.new_context(viewport={"width": 1280, "height": 900})
        await self.context.route("**/*", self.only_local)
        self.page = await self.context.new_page()
        self.page.set_default_timeout(3000)
        self.component = self.page.get_by_role("combobox", name="Incident component", exact=True)
        self.state = self.page.get_by_role("combobox", name="Incident state", exact=True)
        self.more = self.page.get_by_role("button", name="Load more", exact=True)
        self.refresh = self.page.get_by_role("button", name="Refresh history", exact=True)
        self.status = self.page.locator("#historyStatus")
        self.snapshot = self.page.locator("#historySnapshot")
        self.rows = self.page.locator("#incidents [data-incident-id]")
        self.c0, self.c1, self.empty = [c["id"] for c in self.fixture["components"][:3]]

    async def asyncTearDown(self):
        await self.context.close()
        await self.browser.close()
        await self.pw.stop()

    async def only_local(self, route):
        if urlparse(route.request.url).netloc == urlparse(self.origin).netloc:
            await route.continue_()
        else:
            await route.abort()

    async def fixture_action(self, action, **values):
        response = await self.page.request.post(
            self.origin + "/__fixture",
            data=json.dumps({"action": action, **values}),
            headers={"content-type": "application/json"},
        )
        self.assertEqual(response.status, 204, await response.text())

    def expected(self, component="", state=""):
        rows = [r for r in self.fixture["rows"]
                if (not component or r["componentId"] == component)
                and (not state or r["state"] == state)]
        return [r["id"] for r in sorted(rows, key=lambda r: (r["startedAt"], r["id"]), reverse=True)]

    async def ids(self):
        return await self.rows.evaluate_all("rows => rows.map(row => row.dataset.incidentId)")

    async def assert_ids(self, ids):
        await self.page.wait_for_function("""expected => JSON.stringify(Array.from(
          document.querySelectorAll('#incidents [data-incident-id]'),
          row => row.dataset.incidentId)) === JSON.stringify(expected)""", arg=ids)
        self.assertEqual(await self.ids(), ids)

    async def first_page(self, component="", state="", expected_ids=None):
        expected = self.expected(component, state) if expected_ids is None else expected_ids
        await self.page.wait_for_function("""expected => {
          const status = document.querySelector('#historyStatus');
          const ids = Array.from(document.querySelectorAll('#incidents [data-incident-id]'),
            row => row.dataset.incidentId);
          return status && expected.length > 0 && ids.length > 0 &&
            !/loading/i.test(status.textContent) &&
            JSON.stringify(ids) === JSON.stringify(expected.slice(0, ids.length));
        }""", arg=expected)
        ids = await self.ids()
        self.assertGreater(len(ids), 0)
        self.assertEqual(ids, expected[:len(ids)])
        return ids

    async def open_history(self, component="", state="", snapshot=""):
        values = {"component": component, "state": state, "snapshot": snapshot}
        query = urlencode({key: value for key, value in values.items() if value})
        response = await self.page.goto(self.origin + "/" + ("?" + query if query else ""))
        self.assertIsNotNone(response, "Harness did not receive a document response")
        self.assertEqual(response.status, 200, "Harness did not receive an HTML success response")
        self.assertIn("text/html", response.headers.get("content-type", ""),
                      "Harness did not receive HTML")
        self.assertEqual(await self.component.count(), 1, "Missing feature: Incident component history filter")
        self.assertEqual(await self.state.count(), 1, "Missing feature: Incident state history filter")
        await expect(self.component).to_have_value(component)
        await expect(self.state).to_have_value(state)
        return await self.first_page(component, state)

    def assert_url(self, component="", state="", snapshot=None):
        query = parse_qs(urlparse(self.page.url).query)
        self.assertEqual(query.get("component", [""]), [component])
        self.assertEqual(query.get("state", [""]), [state])
        if snapshot is not None:
            self.assertEqual(query.get("snapshot", [""]), [snapshot])

    async def test_history_v2_snapshot_and_filters_are_pinned_across_navigation(self):
        await self.open_history(self.c0, "resolved")
        snapshot = await self.snapshot.get_attribute("data-snapshot-id")
        self.assertTrue(snapshot)
        requests = []
        self.page.on("request", lambda request: requests.append(request.url)
                     if "/api/incidents" in request.url else None)
        await self.page.reload()
        await expect(self.snapshot).to_have_attribute("data-snapshot-id", snapshot)
        await self.state.select_option("investigating")
        current = await self.first_page(self.c0, "investigating")
        current_snapshot = await self.snapshot.get_attribute("data-snapshot-id")
        self.assert_url(self.c0, "investigating", current_snapshot)
        self.assertTrue(any("view=history-v2" in url for url in requests))
        self.assertTrue(any(parse_qs(urlparse(url).query).get("snapshot") == [snapshot]
                            for url in requests))
        await self.page.go_back()
        await expect(self.state).to_have_value("resolved")
        await expect(self.snapshot).to_have_attribute("data-snapshot-id", snapshot)
        self.assert_url(self.c0, "resolved", snapshot)
        await self.assert_ids(self.expected(self.c0, "resolved")[:await self.rows.count()])
        await self.page.go_forward()
        await expect(self.state).to_have_value("investigating")
        await self.assert_ids(current)

    async def test_refresh_starts_new_snapshot_and_old_snapshot_is_frozen(self):
        await self.open_history()
        old_snapshot = await self.snapshot.get_attribute("data-snapshot-id")
        old_ids = await self.ids()
        old_text = await self.rows.all_text_contents()
        await self.fixture_action("mutate")
        await self.page.goto(self.origin + "/?snapshot=" + old_snapshot)
        await expect(self.snapshot).to_have_attribute("data-snapshot-id", old_snapshot)
        await self.assert_ids(old_ids)
        self.assertEqual(await self.rows.all_text_contents(), old_text)
        await self.refresh.click()
        # The fixture deletes incident-060 and adds a backdated row. Old snapshot
        # replay must retain the original rows, but explicit refresh must see the
        # changed dataset. Keeping the old oracle here falsely rejected correctness.
        changed_rows = [r for r in self.fixture["rows"] if r["id"] != "incident-060"]
        changed_rows.append({"id": "late-backdated", "startedAt": self.fixture["rows"][7]["startedAt"]})
        changed_ids = [r["id"] for r in sorted(changed_rows, key=lambda r: (r["startedAt"], r["id"]), reverse=True)]
        await self.page.wait_for_function("""old => {
          const node = document.querySelector('#historySnapshot');
          return node && node.dataset.snapshotId && node.dataset.snapshotId !== old;
        }""", arg=old_snapshot)
        await self.first_page(expected_ids=changed_ids)
        new_snapshot = await self.snapshot.get_attribute("data-snapshot-id")
        self.assertTrue(new_snapshot)
        self.assertNotEqual(old_snapshot, new_snapshot)
        self.assert_url(snapshot=new_snapshot)

    async def test_expiry_is_explicit_and_refresh_recovers(self):
        await self.open_history()
        old_snapshot = await self.snapshot.get_attribute("data-snapshot-id")
        await self.fixture_action("advance", milliseconds=31 * 60 * 1000)
        await self.page.goto(self.origin + "/?snapshot=" + old_snapshot)
        await expect(self.status).to_contain_text(re.compile("expired|410", re.I))
        self.assertTrue(await self.refresh.is_visible())
        await self.refresh.click()
        await self.first_page()

    async def test_network_failure_is_distinct_and_retry_preserves_filter_and_snapshot(self):
        await self.open_history(self.c0, "resolved")
        snapshot = await self.snapshot.get_attribute("data-snapshot-id")
        before = await self.ids()
        self.assertLess(len(before), len(self.expected(self.c0, "resolved")))
        await self.fixture_action("fail-next", count=1)
        await self.more.click()
        await expect(self.status).to_contain_text(re.compile("error|failed|unable", re.I))
        self.assertNotRegex(await self.status.inner_text(), re.compile("no (incidents|results)", re.I))
        await self.page.get_by_role("button", name="Retry", exact=True).click()
        await self.page.wait_for_function(
            "count => document.querySelectorAll('#incidents [data-incident-id]').length > count",
            arg=len(before),
        )
        await expect(self.component).to_have_value(self.c0)
        await expect(self.state).to_have_value("resolved")
        self.assert_url(self.c0, "resolved", snapshot)
        ids = await self.ids()
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(ids, self.expected(self.c0, "resolved")[:len(ids)])

    async def test_revision_two_retention_expires_previous_snapshot(self):
        await self.open_history()
        old_snapshot = await self.snapshot.get_attribute("data-snapshot-id")
        await self.fixture_action("retention", minutes=10)
        await self.fixture_action("advance", milliseconds=11 * 60 * 1000)
        await self.page.goto(self.origin + "/?snapshot=" + old_snapshot)
        await expect(self.status).to_contain_text(re.compile("expired|410", re.I))
        self.assertTrue(await self.refresh.is_visible())

    async def test_old_filter_response_cannot_replace_new_selection(self):
        await self.open_history()
        held, release = asyncio.Event(), asyncio.Event()

        async def reorder(route):
            query = parse_qs(urlparse(route.request.url).query)
            if query.get("component") == [self.c0]:
                response = await route.fetch()
                held.set()
                await release.wait()
                try:
                    await route.fulfill(response=response)
                except Exception:
                    pass
            else:
                await route.continue_()

        await self.page.route("**/api/incidents*", reorder)
        await self.component.select_option(self.c0)
        await asyncio.wait_for(held.wait(), 5)
        await self.component.select_option(self.c1)
        latest = await self.first_page(self.c1)
        release.set()
        await self.page.wait_for_timeout(150)
        await self.assert_ids(latest)
        self.assert_url(self.c1, snapshot=await self.snapshot.get_attribute("data-snapshot-id"))

    async def test_duplicate_load_more_does_not_duplicate_rows(self):
        before = await self.open_history()
        await self.more.evaluate("button => { button.click(); button.click(); button.click(); }")
        await self.page.wait_for_function(
            "count => document.querySelectorAll('#incidents [data-incident-id]').length > count",
            arg=len(before),
        )
        ids = await self.ids()
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(ids, self.expected()[:len(ids)])

    async def test_literal_text_keyboard_focus_and_narrow_layout(self):
        await self.open_history()
        await expect(self.rows.first).to_contain_text(self.fixture["marker"])
        self.assertEqual(await self.page.locator("[data-history-marker]").count(), 0)
        await self.page.set_viewport_size({"width": 375, "height": 812})
        await self.component.focus()
        await self.component.press("ArrowDown")
        await self.component.press("Enter")
        await self.first_page(await self.component.input_value())
        await expect(self.component).to_be_focused()
        await self.refresh.focus()
        await self.refresh.press("Enter")
        await self.first_page(await self.component.input_value())
        await expect(self.refresh).to_be_focused()
        attrs = await self.status.evaluate("node => [node.getAttribute('role'), node.getAttribute('aria-live')]")
        self.assertTrue(attrs[0] == "status" or attrs[1] == "polite")
        self.assertTrue(await self.page.evaluate(
            "document.documentElement.scrollWidth <= window.innerWidth + 1"))
        for control in (self.component, self.state):
            box = await control.bounding_box()
            self.assertIsNotNone(box)
            self.assertGreaterEqual(box["x"], 0)
            self.assertLessEqual(box["x"] + box["width"], 376)


if __name__ == "__main__":
    unittest.main(verbosity=2)

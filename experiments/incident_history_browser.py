"""Common native-browser acceptance; deterministic data, no product writes."""
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


class IncidentHistoryBrowser(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        if not os.environ.get("TRIAL_CHECKOUT"):
            raise RuntimeError("TRIAL_CHECKOUT required")
        cls.server = subprocess.Popen(
            ["node", str(HERE / "incident_history_browser_server.mjs")],
            stdout=subprocess.PIPE, stderr=None, text=True,
        )
        try:
            # A missing worker/module is a harness error, not a feature failure.
            if not select.select([cls.server.stdout], [], [], 10)[0]:
                raise RuntimeError("Fixture server did not become ready within 10 seconds")
            line = cls.server.stdout.readline()
            if not line:
                raise RuntimeError("Fixture server exited before readiness")
            cls.fixture = json.loads(line)
            cls.origin = cls.fixture["origin"]
        except BaseException:
            cls.server.terminate()
            cls.server.wait(timeout=10)
            raise

    @classmethod
    def tearDownClass(cls):
        cls.server.terminate()
        try:
            cls.server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            cls.server.kill()
            cls.server.wait(timeout=10)
        cls.server.stdout.close()

    async def asyncSetUp(self):
        self.pw = await async_playwright().start()
        self.release_events = []
        self.browser = await self.pw.chromium.launch(executable_path=EXECUTABLE)
        self.context = await self.browser.new_context(viewport={"width": 1280, "height": 900})
        await self.context.route("**/*", self.only_local)
        self.page = await self.context.new_page()
        self.page.set_default_timeout(3000)
        self.component = self.page.get_by_role("combobox", name="Incident component", exact=True)
        self.state = self.page.get_by_role("combobox", name="Incident state", exact=True)
        self.more = self.page.get_by_role("button", name="Load more", exact=True)
        self.status = self.page.locator("#historyStatus")
        self.rows = self.page.locator("#incidents [data-incident-id]")
        self.c0, self.c1, self.empty_component = [c["id"] for c in self.fixture["components"][:3]]

    async def asyncTearDown(self):
        for event in self.release_events:
            event.set()
        await self.context.close()
        await self.browser.close()
        await self.pw.stop()

    async def only_local(self, route):
        if urlparse(route.request.url).netloc == urlparse(self.origin).netloc:
            await route.continue_()
        else:
            await route.abort()

    def expected(self, component="", state=""):
        rows = [r for r in self.fixture["rows"]
                if (not component or r["componentId"] == component)
                and (not state or r["state"] == state)]
        return [r["id"] for r in sorted(rows, key=lambda r: (r["startedAt"], r["id"]), reverse=True)]

    async def ids(self):
        return await self.rows.evaluate_all("rows => rows.map(r => r.dataset.incidentId)")

    async def assert_ids(self, ids):
        await self.page.wait_for_function("""ids => JSON.stringify(Array.from(
          document.querySelectorAll('#incidents [data-incident-id]'),
          r => r.dataset.incidentId)) === JSON.stringify(ids)""", arg=ids)
        self.assertEqual(await self.ids(), ids)

    async def first_page(self, component="", state=""):
        # UI is free to choose any accepted API page size; inspect its rendered
        # prefix and ensure a complete, correctly ordered page from the real API.
        await self.page.wait_for_function("""expected => {
          const s = document.querySelector('#historyStatus');
          const ids = Array.from(document.querySelectorAll('#incidents [data-incident-id]'),
            r => r.dataset.incidentId);
          return s && !/loading/i.test(s.textContent) &&
            ids.length && JSON.stringify(ids) === JSON.stringify(expected.slice(0, ids.length));
        }""", arg=self.expected(component, state))
        ids = await self.ids()
        self.assertGreater(len(ids), 0)
        self.assertLessEqual(len(ids), 50)
        self.assertEqual(ids, self.expected(component, state)[:len(ids)])
        return ids

    async def open_history(self, component="", state=""):
        query = urlencode({k: v for k, v in {"component": component, "state": state}.items() if v})
        await self.page.goto(self.origin + "/" + ("?" + query if query else ""))
        # Base must fail with this explicit missing-feature assertion, not timeout.
        self.assertEqual(await self.component.count(), 1,
                         "Missing feature: Incident component history filter")
        self.assertEqual(await self.state.count(), 1,
                         "Missing feature: Incident state history filter")
        await expect(self.component).to_have_value(component)
        await expect(self.state).to_have_value(state)
        return await self.first_page(component, state)

    def assert_url(self, component="", state=""):
        query = parse_qs(urlparse(self.page.url).query)
        self.assertEqual(query.get("component", [""]), [component])
        self.assertEqual(query.get("state", [""]), [state])

    async def test_existing_summary_and_local_api_fixture(self):
        response = await self.page.request.get(self.origin + "/api/status")
        self.assertEqual(response.status, 200)
        snapshot = await response.json()
        self.assertEqual(len(snapshot["incidents"]), 20)
        self.assertGreaterEqual(len(snapshot["components"]), 3)
        await self.page.goto(self.origin)
        await expect(self.page.locator("#summary")).to_contain_text(snapshot["overall"]["message"])
        await expect(self.page.get_by_role("button", name="Report a problem")).to_be_visible()

    async def test_initial_reload_back_forward_and_composed_filters(self):
        initial = await self.open_history(self.c0, "resolved")
        await self.page.reload()
        await expect(self.component).to_have_value(self.c0)
        await expect(self.state).to_have_value("resolved")
        await self.assert_ids(initial)
        await self.state.select_option("investigating")
        current = await self.first_page(self.c0, "investigating")
        self.assert_url(self.c0, "investigating")
        await self.page.go_back()
        await expect(self.state).to_have_value("resolved")
        await self.assert_ids(initial)
        await self.page.go_forward()
        await expect(self.state).to_have_value("investigating")
        await self.assert_ids(current)

    async def test_pagination_complete_then_filter_clears_pages_and_cursor(self):
        await self.open_history()
        for _ in range(70):
            ids = await self.ids()
            self.assertEqual(ids, self.expected()[:len(ids)])
            if len(ids) == len(self.expected()):
                break
            await expect(self.more).to_be_enabled()
            await self.more.click()
            await self.page.wait_for_function(
                "n => document.querySelectorAll('#incidents [data-incident-id]').length > n", arg=len(ids))
        self.assertEqual(await self.ids(), self.expected())
        self.assertFalse(await self.more.is_visible() and await self.more.is_enabled())
        requests = []
        self.page.on("request", lambda r: requests.append(r.url) if "/api/incidents" in r.url else None)
        await self.component.select_option(self.c1)
        current = await self.first_page(self.c1)
        self.assertLess(len(current), 67)
        self.assertTrue(requests, "filter change must query full history")
        self.assertNotIn("cursor", parse_qs(urlparse(requests[0]).query))
        self.assert_url(self.c1)

    async def test_slow_old_response_cannot_replace_new_selection(self):
        await self.open_history()
        held = asyncio.Event()
        release = asyncio.Event()
        self.release_events.append(release)
        finished = asyncio.Event()

        async def reorder(route):
            query = parse_qs(urlparse(route.request.url).query)
            if query.get("component") == [self.c0]:
                response = await route.fetch()
                held.set()
                await release.wait()
                try:
                    await route.fulfill(response=response)
                except Exception:
                    # An application may cancel the old request, which is valid.
                    pass
                finally:
                    finished.set()
            else:
                await route.continue_()

        await self.page.route("**/api/incidents*", reorder)
        await self.component.select_option(self.c0)
        await asyncio.wait_for(held.wait(), 5)
        await self.component.select_option(self.c1)
        latest = await self.first_page(self.c1)
        release.set()
        await asyncio.wait_for(finished.wait(), 5)
        await self.page.wait_for_timeout(150)
        await self.assert_ids(latest)
        self.assert_url(self.c1)

    async def test_old_pagination_response_cannot_append_after_filter_change(self):
        await self.open_history()
        held, release, finished = asyncio.Event(), asyncio.Event(), asyncio.Event()
        self.release_events.append(release)

        async def reorder(route):
            if "cursor" in parse_qs(urlparse(route.request.url).query):
                response = await route.fetch()
                held.set()
                await release.wait()
                try:
                    await route.fulfill(response=response)
                except Exception:
                    pass  # Cancellation by the application is valid.
                finally:
                    finished.set()
            else:
                await route.continue_()

        await self.page.route("**/api/incidents*", reorder)
        await self.more.click()
        await asyncio.wait_for(held.wait(), 5)
        await self.component.select_option(self.c1)
        latest = await self.first_page(self.c1)
        release.set()
        await asyncio.wait_for(finished.wait(), 5)
        await self.page.wait_for_timeout(150)
        await self.assert_ids(latest)
        self.assert_url(self.c1)

    async def test_duplicate_load_more_and_loading_announcement(self):
        before = await self.open_history()
        held = asyncio.Event()
        release = asyncio.Event()
        self.release_events.append(release)

        async def delay(route):
            if "cursor" in parse_qs(urlparse(route.request.url).query):
                response = await route.fetch()
                held.set()
                await release.wait()
                await route.fulfill(response=response)
            else:
                await route.continue_()

        await self.page.route("**/api/incidents*", delay)
        await self.more.click()
        await asyncio.wait_for(held.wait(), 5)
        await expect(self.status).to_contain_text(re.compile("loading", re.I))
        # Native .click() respects disabled; three activations exercise a pending
        # request without Playwright waiting until the control is enabled again.
        await self.more.evaluate("b => { b.click(); b.click(); b.click(); }")
        release.set()
        await self.page.wait_for_function(
            "n => document.querySelectorAll('#incidents [data-incident-id]').length > n", arg=len(before))
        await self.page.wait_for_timeout(150)
        ids = await self.ids()
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(ids, self.expected()[:len(ids)])

    async def test_empty_error_retry_preserves_filters(self):
        await self.open_history()
        await self.component.select_option(self.empty_component)
        await expect(self.status).to_contain_text(re.compile("no (incidents|results)", re.I))
        await self.assert_ids([])
        self.assertFalse(await self.more.is_visible() and await self.more.is_enabled())
        fail = True

        async def once(route):
            nonlocal fail
            if fail:
                fail = False
                await route.abort("failed")
            else:
                await route.continue_()

        await self.page.route("**/api/incidents*", once)
        await self.component.select_option(self.c0)
        await expect(self.status).to_contain_text(re.compile("error|failed|unable", re.I))
        self.assertNotRegex(await self.status.inner_text(), re.compile("no (incidents|results)", re.I))
        await self.page.get_by_role("button", name="Retry", exact=True).click()
        await self.first_page(self.c0)
        await expect(self.component).to_have_value(self.c0)
        self.assert_url(self.c0)

    async def test_incident_summary_is_inert_text(self):
        await self.open_history()
        await expect(self.rows.first).to_contain_text(self.fixture["marker"])
        self.assertEqual(await self.page.locator("[data-history-marker]").count(), 0)

    async def test_keyboard_focus_live_region_and_mobile(self):
        await self.open_history()
        await self.page.set_viewport_size({"width": 375, "height": 812})
        await self.component.focus()
        options = await self.component.locator("option").evaluate_all("options => options.map(o => o.value)")
        await self.component.press("Home")
        for _ in range(options.index(self.c0)):
            await self.component.press("ArrowDown")
        await self.component.press("Enter")
        selected_component = await self.component.input_value()
        self.assertIn(selected_component, [c["id"] for c in self.fixture["components"]])
        await self.first_page(selected_component)
        await expect(self.component).to_be_focused()
        await self.state.focus()
        await self.state.press("ArrowDown")
        await self.state.press("Enter")
        state = await self.state.input_value()
        self.assertIn(state, ("investigating", "resolved"))
        await self.first_page(selected_component, state)
        await expect(self.state).to_be_focused()
        # Return to all history so load-more is guaranteed regardless of state.
        await self.component.select_option("")
        await self.state.select_option("")
        before = await self.first_page()
        await self.more.focus()
        await self.more.press("Enter")
        await self.page.wait_for_function(
            "n => document.querySelectorAll('#incidents [data-incident-id]').length > n", arg=len(before))
        if await self.more.is_visible():
            await expect(self.more).to_be_focused()
        attrs = await self.status.evaluate("s => [s.getAttribute('role'), s.getAttribute('aria-live')]")
        self.assertTrue(attrs[0] == "status" or attrs[1] == "polite")
        self.assertTrue((await self.status.inner_text()).strip())
        self.assertTrue(await self.page.evaluate(
            "document.documentElement.scrollWidth <= window.innerWidth + 1"))
        for control in (self.component, self.state):
            box = await control.bounding_box()
            self.assertIsNotNone(box)
            self.assertGreaterEqual(box["x"], 0)
            self.assertLessEqual(box["x"] + box["width"], 376)


if __name__ == "__main__":
    unittest.main(verbosity=2)

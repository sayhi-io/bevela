"""Post-invalidation browser oracle repair; never substitutes into Study03 v1.

Retains the frozen suite, replacing only navigation's transient row-count oracle
with the exact first-page IDs captured before navigation. A future scored study
must explicitly freeze this version; diagnostic passes are not rescoring.
"""
import unittest
from urllib.parse import parse_qs, urlparse

from playwright.async_api import expect

import luna_release_browser as frozen


class LunaReleaseBrowser(frozen.LunaReleaseBrowser):
    async def test_history_v2_snapshot_and_filters_are_pinned_across_navigation(self):
        original_ids = await self.open_history(self.c0, "resolved")
        original_snapshot = await self.snapshot.get_attribute("data-snapshot-id")
        self.assertTrue(original_snapshot)
        requests = []
        self.page.on("request", lambda request: requests.append(request.url)
                     if "/api/incidents" in request.url else None)

        await self.page.reload()
        await self.assert_ids(original_ids)
        await expect(self.snapshot).to_have_attribute("data-snapshot-id", original_snapshot)
        await self.state.select_option("investigating")
        current_ids = await self.first_page(self.c0, "investigating")
        current_snapshot = await self.snapshot.get_attribute("data-snapshot-id")
        self.assert_url(self.c0, "investigating", current_snapshot)
        self.assertTrue(any(parse_qs(urlparse(url).query).get("view") == ["history-v2"]
                            for url in requests))
        self.assertTrue(any(parse_qs(urlparse(url).query).get("snapshot") == [original_snapshot]
                            for url in requests))

        await self.page.go_back()
        await expect(self.state).to_have_value("resolved")
        # Snapshot metadata may be set from the URL before the response arrives.
        # Never derive expected results from a live loading-state row count.
        await self.assert_ids(original_ids)
        await expect(self.snapshot).to_have_attribute("data-snapshot-id", original_snapshot)
        self.assert_url(self.c0, "resolved", original_snapshot)

        await self.page.go_forward()
        await expect(self.state).to_have_value("investigating")
        await self.assert_ids(current_ids)
        await expect(self.snapshot).to_have_attribute("data-snapshot-id", current_snapshot)
        self.assert_url(self.c0, "investigating", current_snapshot)


if __name__ == "__main__":
    unittest.main(verbosity=2)

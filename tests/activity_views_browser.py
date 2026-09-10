"""Deterministic candidate-asset browser probe; no service or provider mutation."""
import argparse
from datetime import datetime, timedelta, timezone
import json
import mimetypes
import os
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import expect, sync_playwright
from project_intent.model import project

ROOT = Path(__file__).resolve().parents[1]


def fixture():
    now = datetime.now(timezone.utc)
    snapshot = json.loads((ROOT / ".project-intent/snapshot.json").read_text())
    scope = snapshot["scope_id"]
    payload = project([{"id": scope, "label": "Project Intent", "snapshot": snapshot,
                        "provider_status": "offline"}], [scope])
    work = payload["workstreams"][0]
    work["title"] = "Calendar browser fixture"
    work["workers"] = [{
        "session": "calendar-active-session", "status": "active",
        "working": "Build the evidence calendar",
        "heartbeat_at": (now - timedelta(minutes=1)).isoformat(),
        "expires_at": (now + timedelta(minutes=59)).isoformat(),
    }]
    work["local_reports"] = [{
        "id": "calendar-report", "created_at": (now - timedelta(minutes=10)).isoformat(),
        "payload": {"session": "calendar-active-session", "packet": {
            "summary": "Calendar rendering passed focused review.",
        }}, "publication": {"state": "local"},
    }]
    work["handoff_at"] = (now - timedelta(days=2)).isoformat()
    work["handoff_summary"] = "Developer board handoff recorded."
    payload["recently_rested"] = [{
        "workstream": work["key"], "session": "calendar-rested-session",
        "working": "Finished the board facts", "status": "inactive",
        "reported_inactive_at": (now - timedelta(minutes=20)).isoformat(),
    }]
    payload["rested_coverage"] = {"total": 1}
    payload["observed_at"] = now.isoformat()
    payload["workstreams"] = [work]
    return payload


def run(output):
    output.mkdir(parents=True, exist_ok=True)
    payload = fixture()
    with sync_playwright() as playwright:
        options = {"executable_path": os.environ["BROWSER_EXECUTABLE"]} if os.getenv("BROWSER_EXECUTABLE") else {}
        # The shared DGX headless shell can stall compositor frames; this probe
        # needs only deterministic DOM/CSS rendering, so use its established CPU path.
        browser = playwright.chromium.launch(
            args=["--disable-gpu", "--disable-software-rasterizer"], **options
        )
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))

        def route(request):
            url = urlsplit(request.request.url)
            if url.netloc != "pi.test":
                request.abort()
            elif url.path == "/api/v1/observatory":
                request.fulfill(json=payload)
            else:
                name = "observatory.html" if url.path in ("/", "/observatory") else url.path.lstrip("/")
                asset = ROOT / "project_intent/web" / name
                if asset.parent != ROOT / "project_intent/web" or not asset.is_file():
                    request.fulfill(status=404)
                else:
                    request.fulfill(body=asset.read_bytes(), content_type=mimetypes.guess_type(name)[0] or "text/plain")

        page.route("**/*", route)
        page.goto("http://pi.test/observatory")
        page.locator('#view-nav a[href="#developers"]').click()
        expect(page.locator("#view-title")).to_have_text("Developers")
        expect(page.locator("#developer-active .developer-card")).to_have_count(1)
        expect(page.locator("#developer-released .developer-card")).to_have_count(1)
        expect(page.locator("#developer-evidence .developer-card")).to_have_count(1)
        assert "calendar-active-session" in page.locator("#developer-active").inner_text()
        assert "lifecycle alone never" in page.locator("#developer-board-coverage").inner_text().lower()
        page.locator("#theme").select_option("dark")
        expect(page.locator("html")).to_have_attribute("data-theme", "dark")
        page.screenshot(path=str(output / "developers-dark.png"), animations="disabled")

        page.locator('#view-nav a[href="#calendar"]').click()
        expect(page.locator("#view-title")).to_have_text("Calendar")
        marked = page.locator("#calendar-grid .calendar-day:has(.event-mark)")
        assert marked.count() >= 2
        today = page.locator('#calendar-grid .calendar-day.today')
        today.click()
        expect(page.locator("#calendar-day-events .calendar-event")).to_have_count(2)
        day_text = page.locator("#calendar-day-events").inner_text()
        assert "worker report" in day_text.lower(), day_text
        assert "reported inactive" in day_text.lower(), day_text
        page.locator("#calendar-day-events button").first.click()
        expect(page.locator("#detail")).to_be_visible()
        page.keyboard.press("Escape")
        month = page.locator("#calendar-month").inner_text()
        page.locator("#calendar-previous").click()
        assert page.locator("#calendar-month").inner_text() != month
        page.locator("#calendar-today").click()
        expect(page.locator("#calendar-month")).to_have_text(month)
        expect(page.locator('#calendar-grid .calendar-day[aria-pressed="true"]')).to_be_focused()
        assert "not evidence that no work occurred" in page.locator("#calendar-coverage").inner_text()
        page.locator("#theme").select_option("light")
        expect(page.locator("html")).to_have_attribute("data-theme", "light")
        page.screenshot(path=str(output / "calendar-light.png"), animations="disabled")

        page.set_viewport_size({"width": 390, "height": 844})
        for view in ("developers", "calendar"):
            page.locator(f'#view-nav a[href="#{view}"]').click()
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), view
        page.screenshot(path=str(output / "calendar-mobile.png"), animations="disabled")
        assert not errors, errors
        browser.close()
    (output / "results.json").write_text(json.dumps([
        "Developers Board active/released/evidence lanes passed",
        "Calendar evidence, navigation, focus, detail, theme and mobile checks passed",
    ], indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.output)
    print("PASS: Developers Board and evidence calendar browser validation")

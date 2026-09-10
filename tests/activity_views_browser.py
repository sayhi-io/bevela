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
    work["pull_requests"] = [{
        "repository": "https://github.com/sayhi-io/bevela", "number": 14,
        "url": "https://github.com/sayhi-io/bevela/pull/14", "relationship": "implementation",
        "observation_status": "last-known", "observation": {
            "observed_at": (now - timedelta(minutes=5)).isoformat(), "source": "browser fixture",
            "head": "a" * 40, "state": "merged",
        },
    }]
    payload["recently_rested"] = [{
        "workstream": work["key"], "session": "calendar-rested-session",
        "working": "Finished the board facts", "status": "inactive",
        "reported_inactive_at": (now - timedelta(minutes=20)).isoformat(),
    }]
    payload["rested_coverage"] = {"total": 1}
    payload["observed_at"] = now.isoformat()
    payload["workstreams"] = [work]
    payload["local_git"] = {"status": "observed", "commits": [{
        "scope": scope, "repository": "sayhi-project-intent", "oid": "b" * 40,
        "committed_at": (now - timedelta(minutes=7)).isoformat(),
        "subject": "Record local Git calendar evidence", "publication": "local-only",
    }]}
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
        expect(page.locator(".judgment-bar")).to_be_hidden()
        expect(page.locator("#developer-active .developer-card")).to_have_count(1)
        expect(page.locator("#developer-released .developer-card")).to_have_count(1)
        expect(page.locator("#developer-evidence .developer-card")).to_have_count(1)
        assert "calendar-active-session" in page.locator("#developer-active").inner_text()
        assert "lifecycle alone never" in page.locator("#developer-board-coverage").inner_text().lower()
        page.locator(".display-options > summary").click()
        page.locator("#theme").select_option("dark")
        expect(page.locator("html")).to_have_attribute("data-theme", "dark")
        page.locator(".display-options > summary").click()
        page.screenshot(path=str(output / "developers-dark.png"), animations="disabled")

        page.locator('#view-nav a[href="#calendar"]').click()
        expect(page.locator("#view-title")).to_have_text("Calendar")
        expect(page.locator("#product-title")).to_have_text("Calendar")
        expect(page.locator("#product-description")).to_contain_text("Timestamped handoffs")
        expect(page.locator(".judgment-bar")).to_be_hidden()
        expect(page.locator(".status-tools > span")).to_be_hidden()
        expect(page.locator("#calendar-week")).to_have_attribute("aria-pressed", "true")
        expect(page.locator("#calendar-grid .calendar-day")).to_have_count(7)
        assert "(day:" not in page.locator("#calendar-month").inner_text()
        marked = page.locator("#calendar-grid .calendar-day:has(.event-mark)")
        assert marked.count() >= 2
        today = page.locator('#calendar-grid .calendar-day.today')
        today.click()
        expect(page.locator("#calendar-day-events .calendar-event")).to_have_count(4)
        day_text = page.locator("#calendar-day-events").inner_text()
        assert "worker report" in day_text.lower(), day_text
        assert "reported inactive" in day_text.lower(), day_text
        assert "pull request observed" in day_text.lower(), day_text
        assert "record local git calendar evidence" in day_text.lower(), day_text
        assert "local-only" in day_text.lower(), day_text
        page.locator("#calendar-day-events button").first.click()
        expect(page.locator("#detail")).to_be_visible()
        page.keyboard.press("Escape")
        week = page.locator("#calendar-month").inner_text()
        page.locator("#calendar-previous").click()
        assert page.locator("#calendar-month").inner_text() != week
        page.locator("#calendar-today").click()
        expect(page.locator("#calendar-month")).to_have_text(week)
        expect(page.locator('#calendar-grid .calendar-day[aria-pressed="true"]')).to_be_focused()
        assert "not evidence that no work occurred" in page.locator("#calendar-coverage").text_content()
        status = page.locator(".statusline").bounding_box()
        evidence = page.locator("#calendar-evidence-types").bounding_box()
        coverage = page.locator("#calendar-coverage-summary").bounding_box()
        assert status["y"] <= evidence["y"] < status["y"] + status["height"], (status, evidence)
        assert status["y"] <= coverage["y"] < status["y"] + status["height"], (status, coverage)
        shell = page.locator(".calendar-shell").bounding_box()
        detail = page.locator(".calendar-detail").bounding_box()
        assert shell["width"] <= 930, shell
        assert detail["y"] >= shell["y"] + shell["height"], (shell, detail)
        cards = page.locator("#calendar-day-events .calendar-event")
        assert len({round(cards.nth(index).bounding_box()["x"]) for index in range(cards.count())}) >= 2

        page.locator("#calendar-month-view").click()
        expect(page.locator("#calendar-month-view")).to_have_attribute("aria-pressed", "true")
        expect(page.locator("#calendar-grid .calendar-day")).to_have_count(42)
        page.screenshot(path=str(output / "calendar-month-dark.png"), animations="disabled")
        page.locator("#calendar-week").click()
        expect(page.locator("#calendar-grid .calendar-day")).to_have_count(7)
        expect(page.locator('#calendar-grid .calendar-day.today[aria-pressed="true"]')).to_have_count(1)
        page.locator(".display-options > summary").click()
        page.locator("#theme").select_option("light")
        expect(page.locator("html")).to_have_attribute("data-theme", "light")
        page.locator(".display-options > summary").click()
        page.screenshot(path=str(output / "calendar-week-light.png"), animations="disabled")

        page.locator('#view-nav a[href="#handoffs"]').click()
        expect(page.locator("#rested")).to_be_hidden()
        expect(page.locator(".handoff-layout")).to_be_visible()
        expect(page.locator("#reports .report-card")).to_have_count(1)
        expect(page.locator("#handoffs .handoff-item")).to_have_count(1)
        page.screenshot(path=str(output / "handoffs-light.png"), animations="disabled")
        page.locator('#view-nav a[href="#work"]').click()
        expect(page.locator("#convergence")).to_be_hidden()
        expect(page.locator(".work-layout")).to_be_visible()
        expect(page.locator("#workstreams .work-card")).to_have_count(1)
        expect(page.locator("#initiatives .initiative-item")).to_have_count(1)
        page.screenshot(path=str(output / "work-light.png"), animations="disabled")
        page.locator('#view-nav a[href="#architecture"]').click()
        expect(page.locator("#architecture .architecture-row")).to_have_count(4)
        expect(page.locator(".ledger-head")).to_be_visible()
        page.screenshot(path=str(output / "architecture-light.png"), animations="disabled")
        page.locator('#view-nav a[href="#environments"]').click()
        expect(page.locator("#environments .environment-row")).to_have_count(1)
        expect(page.locator(".matrix-head")).to_be_visible()
        limitations = page.locator("#environments .environment-row > div").nth(2)
        expect(limitations).to_contain_text("No production or fleet authority")
        expect(limitations).to_contain_text("Native provider provisional")
        assert '{"requirement"' not in limitations.inner_text()
        page.screenshot(path=str(output / "environments-light.png"), animations="disabled")
        page.locator('#view-nav a[href="#sources"]').click()
        expect(page.locator(".sources-layout")).to_be_visible()
        expect(page.locator("#sources .source-item")).to_have_count(1)
        page.screenshot(path=str(output / "sources-light.png"), animations="disabled")
        page.locator('#view-nav a[href="#home"]').click()
        expect(page.locator("#product-title")).to_have_text("Mission Control")
        expect(page.locator(".status-tools > span")).to_be_visible()
        expect(page.locator(".judgment-bar")).to_be_visible()
        expect(page.locator("#rested")).to_be_visible()
        expect(page.locator("#convergence")).to_be_visible()
        page.locator("#rested-coverage a").click()
        expect(page.locator("#view-title")).to_have_text("Developers")
        expect(page.locator("#developer-released .developer-card")).to_have_count(1)

        page.set_viewport_size({"width": 390, "height": 844})
        for view in ("home", "developers", "calendar", "map", "work", "architecture", "environments", "handoffs", "sources"):
            page.locator(f'#view-nav a[href="#{view}"]').click()
            if view != "home":
                expect(page.locator(".judgment-bar")).to_be_hidden()
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), view
        page.screenshot(path=str(output / "calendar-mobile.png"), animations="disabled")
        assert not errors, errors
        browser.close()
    (output / "results.json").write_text(json.dumps([
        "Developers Board active/released/evidence lanes passed",
        "Calendar week/month evidence, stacked detail, focus, theme and mobile checks passed",
        "Overview-only summaries and distinct Work, Architecture, Environment, Handoff and Source layouts passed",
    ], indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.output)
    print("PASS: Developers Board and evidence calendar browser validation")

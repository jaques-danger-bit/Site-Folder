#!/usr/bin/env python3
"""Read-only browser checks for coach pages and pending purchase pages.

All nonlocal requests and all mutation requests are intercepted and aborted.
No intake, booking, payment or messaging request reaches a live service.
"""
import argparse
import base64
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urlparse
import xml.etree.ElementTree as ET

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
CHROME = "/home/jaquesdanger/.cache/puppeteer/chrome/linux-149.0.7827.22/chrome-linux64/chrome"
COACHES = ("Justin", "Zach", "Rhylie")
CTA = "I’m ready to start training"


def brand_check(page, base):
    images = page.locator("header img, nav img, a.stg-brand img, [data-brand-logo], .stg-footer-badge")
    candidates = images.evaluate_all("""nodes => nodes.filter(n => n.tagName === 'IMG')
      .map(n => ({src:n.getAttribute('src'), loaded:n.complete && n.naturalWidth > 0}))""")
    svg_sources = [item for item in candidates if item["src"] and
                   (item["src"].startswith("data:image/svg+xml") or
                    urlparse(item["src"]).path.endswith(".svg"))]
    verified = []
    for item in svg_sources:
        assert item["loaded"], "SVG brand image did not load"
        src = item["src"]
        if src.startswith("data:"):
            metadata, encoded = src.split(",", 1)
            raw = base64.b64decode(encoded) if ";base64" in metadata else unquote(encoded).encode()
        else:
            parsed = urlparse(src)
            assert not parsed.netloc or parsed.netloc == urlparse(base).netloc, "Logo requires external request"
            path = unquote(parsed.path)
            local = ROOT / path.split("/coach-pages/", 1)[-1].lstrip("/")
            if not local.exists():
                local = ROOT / path.removeprefix("assets/")
            raw = local.read_bytes()
        svg = ET.fromstring(raw)
        assert svg.tag.rsplit("}", 1)[-1] == "svg"
        assert any(el.tag.rsplit("}", 1)[-1] in {"path", "polygon", "polyline", "rect", "text", "use"}
                   for el in svg.iter()), "SVG has no logo geometry"
        assert not page.locator(".stg-brand-mark").count(), "Old typed STG mark remains"
        verified.append({"svg_sha256": hashlib.sha256(raw).hexdigest(), "embedded": src.startswith("data:")})
    if verified:
        assert len(verified) >= 2, "Expected supplied header and footer SVG logos"
        return {"logos": verified}
    inline = page.locator("header svg, nav svg, a.stg-brand svg")
    assert inline.count(), "Actual SVG branding not present"
    assert not page.locator(".stg-brand-mark").count(), "Old typed STG mark remains"
    return {"svg_sha256": hashlib.sha256(inline.first.evaluate("n=>n.outerHTML").encode()).hexdigest(), "inline": True}


def run(base, chrome):
    results, navigations, all_blocked = [], [], []
    base = base.rstrip("/")
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=chrome, headless=True, args=["--no-sandbox"])
        for coach in COACHES:
            slug = coach.lower()
            for kind in ("landing", "purchase"):
                stem = slug if kind == "landing" else "start-" + slug
                for embedded in (False, True):
                    for viewport, width, height in (("desktop",1440,1000),("mobile",390,844),("small-mobile",320,740)):
                        context = browser.new_context(viewport={"width":width,"height":height})
                        page = context.new_page()
                        errors, blocked = [], []
                        page.on("pageerror", lambda error: errors.append(str(error)))
                        fixture_path = "/coach-pages/qa-" + stem + ".html"

                        def route_request(route):
                            request = route.request
                            parsed = urlparse(request.url)
                            if request.method not in {"GET", "HEAD"}:
                                blocked.append({"url":request.url,"method":request.method})
                                route.abort()
                            elif embedded and parsed.path == fixture_path:
                                block = (ROOT / "blocks" / (stem + "-copy-paste.html")).read_text()
                                route.fulfill(status=200,content_type="text/html",body=(
                                    '<!doctype html><html lang="en"><head><meta charset="utf-8">'
                                    '<meta name="viewport" content="width=device-width,initial-scale=1">'
                                    '<link rel="icon" href="data:,"><style>body{margin:0}</style></head><body><div id="host-html-block">'
                                    + block + '</div></body></html>'))
                            elif parsed.netloc == urlparse(base).netloc:
                                route.continue_()
                            else:
                                blocked.append({"url":request.url,"method":request.method})
                                route.abort()

                        page.route("**/*", route_request)
                        path = fixture_path if embedded else "/coach-pages/" + stem + ".html"
                        page.goto(base + path, wait_until="networkidle")
                        page.evaluate("document.fonts.ready")
                        page.wait_for_function("[...document.querySelectorAll('header img,nav img,[data-brand-logo]')].every(n=>n.tagName!=='IMG'||n.complete)")
                        text = page.locator("body").inner_text()
                        assert coach in text
                        if coach == "Zach":
                            assert "tactical" in text.lower(), "Tactical role is missing"
                            assert "firearms" not in text.lower(), "Old firearms wording remains"
                        else:
                            assert "competition prep" in text.lower() or "bodybuilding" in text.lower(), "Competition prep category is missing"
                        brand = brand_check(page, base)
                        photo = page.locator('.stg-hero-photo, .stg-purchase-photo').first
                        photo_src = photo.get_attribute('src')
                        if embedded:
                            assert photo_src.startswith('data:image/jpeg;base64,'), 'Photo is not embedded'
                            assert base64.b64decode(photo_src.split(',',1)[1]) == (ROOT/'assets'/(slug+'.jpg')).read_bytes(), 'Embedded photo mismatch'
                            requested_assets = page.evaluate("performance.getEntriesByType('resource').map(r=>r.name).filter(n=>/^https?:/.test(n))")
                            assert not requested_assets, (stem, 'Block depended on external assets', requested_assets)
                        else:
                            assert urlparse(photo_src).path.endswith('assets/'+slug+'.jpg'), photo_src
                        geometry = page.evaluate("({width:innerWidth,scrollWidth:document.documentElement.scrollWidth})")
                        assert geometry["scrollWidth"] == width, (stem, viewport, geometry)
                        assert not errors, (stem, errors)
                        if kind == "landing":
                            link = page.locator(".stg-hero [data-purchase-link]").first
                            assert link.text_content().strip() == CTA
                            assert link.is_visible(), "Ready-to-train link not visible"
                            rect = link.bounding_box()
                            assert rect and rect["x"] >= -1 and rect["x"] + rect["width"] <= width + 1
                            # At regular phone/desktop sizes it should be accessible on the first screen.
                            if viewport != "small-mobile":
                                assert rect["y"] < height, (stem, viewport, "Purchase CTA below first screen", rect)
                            href = link.get_attribute("href")
                            assert urlparse(href).path.endswith("start-" + slug + ".html"), href
                            assert page.locator('a[href="#' + slug + '-intake"]').filter(has_text="Book a call with " + coach).count(), "Call option removed"
                            goals = page.locator('select[name="goal"]').inner_text().lower()
                            assert ("tactical" in goals) if coach == "Zach" else ("competition" in goals or "bodybuilding" in goals)
                            if viewport == "mobile":
                                link.click()
                                page.wait_for_url("**/start-" + slug + ".html")
                                assert page.locator('[data-purchase-embed="' + slug + '"]').is_visible()
                                navigations.append({"coach":coach,"embedded":embedded,"destination":urlparse(page.url).path})
                        else:
                            slot = page.locator('[data-purchase-embed="' + slug + '"]')
                            assert slot.count() == 1
                            assert "Online enrollment is being prepared." in slot.inner_text()
                            assert not slot.locator("iframe, stripe-buy-button, input, button[type=submit]").count(), "Unconfigured payment action present"
                            assert not page.locator('script[src*="stripe"],iframe[src*="stripe"]').count()
                            expected = slug + ".html#" + slug + "-intake"
                            assert page.locator('a[href="' + expected + '"]').count(), "Coach-specific call fallback missing"
                            assert not page.locator("body").inner_text().lower().count("stripe embed"), "Implementation note in customer flow"
                        assert not blocked, (stem, viewport, blocked)
                        all_blocked.extend(blocked)
                        results.append({"coach":coach,"page":kind,"embedded":embedded,"viewport":viewport,
                                        "width":width,"no_overflow":True,"javascript_errors":errors,"brand":brand})
                        context.close()
        browser.close()
    photo_checks = []
    source = Path('/home/jaquesdanger/Strikeline-data/coach-social-personas/2026-10-30/sources')
    for coach in COACHES:
        original = source / (coach + '-highlight-source-photo.jpg')
        current = ROOT / 'assets' / (coach.lower() + '.jpg')
        assert original.read_bytes() == current.read_bytes(), coach + ' photo changed'
        photo_checks.append({"coach":coach,"original_bytes_preserved":True,"sha256":hashlib.sha256(current.read_bytes()).hexdigest()})
    evidence = {"status":"passed","checked_at_utc":datetime.now(timezone.utc).isoformat(),"page_view_checks":len(results),
                "standalone_pages":6,"self_contained_blocks":6,"purchase_navigations":navigations,
                "live_mutations":0,"external_requests":all_blocked,"photo_checks":photo_checks,"results":results,
                "scope":"Local rendering and navigation with all external/mutation requests blocked. No actual purchases, intake submissions, bookings, publishing or DM sends."}
    (ROOT / 'evidence' / 'redesign-tests.json').write_text(json.dumps(evidence,indent=2)+'\n')
    print(json.dumps({"status":"passed","page_view_checks":len(results),"navigation_checks":len(navigations),"photo_checks":len(photo_checks),"live_mutations":0}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-url',default='http://127.0.0.1:8795')
    parser.add_argument('--chrome',default=CHROME)
    args = parser.parse_args()
    run(args.base_url,args.chrome)

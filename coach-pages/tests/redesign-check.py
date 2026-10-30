#!/usr/bin/env python3
"""Read-only regression checks for coach landings and sourced checkout offers.

The Stripe loader is fulfilled locally with a deterministic render-only stub.
All other external requests and every mutation are aborted. This does not test
live checkout or create sessions, payments, subscriptions, bookings or leads.
"""
import argparse
import base64
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse
import xml.etree.ElementTree as ET

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
CHROME = "/home/jaquesdanger/.cache/puppeteer/chrome/linux-149.0.7827.22/chrome-linux64/chrome"
COACHES = ("Justin", "Zach", "Rhylie")
CTA = "I’m ready to start training"
APPROVED_COMMIT = "967e407"
STRIPE_SCRIPT = "https://js.stripe.com/v3/buy-button.js"
# Independently checked against the saved public Stripe GET responses, rather
# than derived from the templates or offers.json that those templates consume.
EXPECTED_OFFERS = {
    "assessment": {"amount":175,"cadence":"one time","product":"Nutrition + Training Assessment",
                   "button":"buy_btn_1UWFCARzFn0Z1SgZqB6Sx8fi","url":"https://buy.stripe.com/fZueVf0L480x3sPdAfgQE2z"},
    "online": {"amount":350,"cadence":"per month","product":"Online Coaching — Monthly",
               "button":"buy_btn_1UWFDHRzFn0Z1SgZci4LXSUf","url":"https://buy.stripe.com/fZucN70L4fsZgfB0NtgQE2A"},
    "inperson": {"amount":475,"cadence":"per month","product":"Monthly Coaching — Foundation",
                 "button":"buy_btn_1UWFE2RzFn0Z1SgZvpUqdxYp","url":"https://buy.stripe.com/dRmcN765o94B5AXao3gQE2B"}
}
STRIPE_STUB = """(() => {
  class TestBuyButton extends HTMLElement {
    connectedCallback() {
      if (this.shadowRoot) return;
      const root = this.attachShadow({mode:'open'});
      root.innerHTML = '<style>:host{display:block;max-width:100%}.fixture{box-sizing:border-box;max-width:100%;padding:24px 16px;border-radius:8px;background:white;color:#151515;font:16px sans-serif;text-align:center}button{display:block;box-sizing:border-box;max-width:100%;margin:16px auto 0;padding:12px 16px;border:0;border-radius:5px;background:#1649b5;color:white}</style><div class="fixture"><strong>Stripe render fixture</strong><p>Payment actions disabled in this test.</p><button type="button" disabled>Secure checkout preview</button></div>';
      this.dataset.testRender = 'ready';
    }
  }
  customElements.define('stripe-buy-button', TestBuyButton);
})();"""


def source_and_baseline_check():
    pinned = [f"{coach.lower()}.html" for coach in COACHES]
    pinned += [f"blocks/{coach.lower()}-copy-paste.html" for coach in COACHES]
    pinned += ["assets/coach.css", "assets/intake.js", "assets/fonts.css", "assets/fonts-remote.css"]
    baseline = []
    for name in pinned:
        approved = subprocess.check_output(["git", "show", f"{APPROVED_COMMIT}:coach-pages/{name}"], cwd=ROOT.parent)
        current = (ROOT/name).read_bytes()
        allowed_change = None
        if name.endswith(".html"):
            slug = Path(name).name.split("-copy-paste")[0].removesuffix(".html")
            original_phone = (f'Phone <small>Optional</small></label><input id="{slug}-phone" '
                              'name="phone" type="tel" autocomplete="tel" maxlength="40" placeholder="Your phone number">').encode()
            required_phone = (f'Phone <small>Required</small></label><input id="{slug}-phone" '
                              'name="phone" type="tel" autocomplete="tel" maxlength="40" placeholder="Your phone number" '
                              r'pattern=".*\S.*" title="Enter your phone number." required>').encode()
            assert approved.count(original_phone) == 1, f"Approved phone field not found exactly once: {name}"
            assert current.count(required_phone) == 1, f"Exact authorized required-phone field missing: {name}"
            approved = approved.replace(original_phone,required_phone,1)
            allowed_change = "Phone label Required; input required with whitespace-rejecting pattern and title"
        assert approved == current, f"Approved landing changed beyond the exact authorized phone field: {name}"
        baseline.append({"path":name,"sha256":hashlib.sha256(current).hexdigest(),"allowed_change":allowed_change})
    receipt_path = ROOT / "evidence/services-20261030/stripe-public-read.json"
    receipt = json.loads(receipt_path.read_text())
    public = {response["data"]["id"]:response for response in receipt["responses"]}
    offers_data = json.loads((ROOT/"offers.json").read_text())
    configured = {offer["slug"]:offer for offer in offers_data["offers"]}
    assert set(configured) == set(EXPECTED_OFFERS), "Expected the user-approved assessment plus two coaching offers"
    source_checks = []
    for slug, expected in EXPECTED_OFFERS.items():
        response = public[expected["button"]]
        data = response["data"]
        price = data["line_item_group"]["line_items"][0]["price"]
        assert response["status"] == 200 and data["active"]
        assert price["currency"] == "usd" and price["unit_amount"] == expected["amount"] * 100
        assert price["product"]["name"] == expected["product"]
        assert data["checkout_url"] == expected["url"]
        assert (price["recurring"] is None) if slug == "assessment" else (price["recurring"]["interval"] == "month")
        offer = configured[slug]
        assert offer["checkoutReady"] and offer["buttonId"] == expected["button"]
        assert offer["amount"] == expected["amount"] and offer["cadence"] == expected["cadence"]
        assert offer["stripeProductName"] == expected["product"] and offer["checkoutUrl"] == expected["url"]
        source_checks.append({"service":slug,"button_id":expected["button"],"product":expected["product"],
                              "amount_usd":expected["amount"],"cadence":expected["cadence"],"public_get_status":response["status"]})
    return baseline, source_checks, offers_data["publishableKey"], hashlib.sha256(receipt_path.read_bytes()).hexdigest()


def route_fixture(page, base, stem, embedded, mode="render"):
    blocked, loaders = [], []
    fixture_path = "/coach-pages/qa-" + stem + ".html"

    def route_request(route):
        request = route.request
        parsed = urlparse(request.url)
        if request.method not in {"GET", "HEAD"}:
            blocked.append({"url":request.url,"method":request.method})
            route.abort()
        elif request.url == STRIPE_SCRIPT:
            loaders.append({"url":request.url,"method":request.method,"mode":mode})
            if mode == "failed":
                route.abort("failed")
            else:
                route.fulfill(status=200,content_type="application/javascript",body=STRIPE_STUB if mode == "render" else "/* deliberately unavailable custom element */")
        elif embedded and parsed.path == fixture_path:
            block = (ROOT/"blocks"/(stem+"-copy-paste.html")).read_text()
            route.fulfill(status=200,content_type="text/html",body=(
                '<!doctype html><html lang="en"><head><meta charset="utf-8">'
                '<meta name="viewport" content="width=device-width,initial-scale=1">'
                '<link rel="icon" href="data:,"><style>body{margin:0}</style></head>'
                '<body><div id="host-html-block">'+block+'</div></body></html>'))
        elif parsed.netloc == urlparse(base).netloc:
            route.continue_()
        else:
            blocked.append({"url":request.url,"method":request.method})
            route.abort()

    page.route("**/*",route_request)
    path = fixture_path if embedded else "/coach-pages/"+stem+".html"
    return base+path, blocked, loaders


def assert_checkout_url(href, slug, service):
    expected = EXPECTED_OFFERS[service]
    parsed = urlparse(href)
    target = urlparse(expected["url"])
    assert (parsed.scheme,parsed.netloc,parsed.path) == (target.scheme,target.netloc,target.path), href
    assert parse_qs(parsed.query).get("client_reference_id") == [f"stg_{slug}_{service}"], href


def assert_geometry(page, width, label):
    geometry = page.evaluate("({width:innerWidth,scrollWidth:document.documentElement.scrollWidth})")
    assert geometry["scrollWidth"] == width, (label,geometry)


def purchase_check(page, slug, publishable_key, loaders, mode="render"):
    text = page.locator("body").inner_text()
    assert page.locator("[data-offer-id]").count() == 3
    assert not page.locator("[data-program-conversation]").count()
    assert "standalone program" not in text.lower() and "$30" not in text
    assert "Online enrollment is being prepared." not in text
    for unsupported in ("24/7 support","unlimited support","guaranteed results","weekly check-ins"):
        assert unsupported not in text.lower(), unsupported
    assert page.locator('[data-purchase-embed="'+slug+'"]').count() == 1
    assert not page.locator("stripe-buy-button").count(), "Stripe must stay lazy before intent"
    assert not page.locator('script[src="'+STRIPE_SCRIPT+'"]').count()
    assert not loaders
    assert page.locator('a[href="'+slug+'.html#'+slug+'-intake"]').count(), "Coach-specific call path missing"
    dialog = page.locator("dialog[data-checkout-dialog]")
    checks = []
    for index,(service,expected) in enumerate(EXPECTED_OFFERS.items()):
        card = page.locator('[data-offer-id="'+service+'"]')
        assert card.locator(".stg-offer-price strong").inner_text() == "$"+str(expected["amount"])
        assert expected["cadence"] in card.locator(".stg-offer-price").inner_text()
        if service == "assessment":
            assert expected["product"].lower() in card.inner_text().lower()
            assert "no monthly subscription" in card.inner_text().lower()
        elif service == "inperson":
            assert "30-day cancellation notice" in card.inner_text()
            assert "one coaching session per week" in card.inner_text().lower()
        opener = card.locator('[data-open-checkout="'+service+'"]')
        assert_checkout_url(opener.get_attribute("href"),slug,service)
        opener.click()
        dialog.wait_for(state="visible")
        assert dialog.get_attribute("data-active-offer") == service
        reference = f"stg_{slug}_{service}"
        assert dialog.get_attribute("data-client-reference-id") == reference
        assert "$"+str(expected["amount"]) in dialog.locator("[data-checkout-details]").inner_text()
        fallback = dialog.locator("[data-checkout-fallback]")
        assert fallback.is_visible()
        assert_checkout_url(fallback.get_attribute("href"),slug,service)
        assert fallback.get_attribute("target") == "_top"
        if mode == "render":
            button = dialog.locator("stripe-buy-button[data-test-render='ready']")
            button.wait_for(state="visible")
            assert button.get_attribute("buy-button-id") == expected["button"]
            assert button.get_attribute("publishable-key") == publishable_key
            assert button.get_attribute("client-reference-id") == reference
            assert page.locator("stripe-buy-button").count() == 1
            assert not dialog.locator("[data-checkout-status]").get_attribute("data-state")
        else:
            if mode == "timeout" and index == 0:
                page.clock.fast_forward(13000)
            dialog.locator('[data-checkout-status][data-state="error"]').wait_for(state="visible")
            assert "could not load" in dialog.locator("[data-checkout-status]").inner_text()
            assert not dialog.locator("stripe-buy-button").count()
        assert page.locator('script[src="'+STRIPE_SCRIPT+'"]').count() == 1
        assert len(loaders) == 1, "Stripe loader requested more than once"
        bounds = dialog.bounding_box()
        width = page.viewport_size["width"]
        assert bounds and bounds["x"] >= -1 and bounds["x"]+bounds["width"] <= width+1
        assert dialog.evaluate("n=>n.scrollWidth <= n.clientWidth + 1"), "Dialog horizontally overflows"
        assert_geometry(page,width,slug+"/"+service)
        if index % 2:
            page.keyboard.press("Escape")
        else:
            dialog.locator("[data-checkout-close]").click()
        dialog.wait_for(state="hidden")
        # Native dialog.close() hides synchronously, then dispatches its close
        # event in a later task where the enhancement removes the mounted widget.
        page.locator("stripe-buy-button").wait_for(state="detached")
        page.wait_for_function("document.body.style.overflow !== 'hidden'")
        assert opener.evaluate("n=>document.activeElement===n"), "Dialog did not restore initiating focus"
        assert not page.locator("stripe-buy-button").count(), "Closed widget was not removed"
        assert page.evaluate("document.body.style.overflow") != "hidden"
        checks.append({"service":service,"button_id":expected["button"],"reference":reference,
                       "verified_fallback":True,"focus_restored":True,"mode":mode})
    return checks


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
    baseline, source_checks, publishable_key, source_hash = source_and_baseline_check()
    results, navigations, failures, no_javascript, all_blocked = [], [], [], [], []
    base = base.rstrip("/")
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=chrome,headless=True,args=["--no-sandbox"])
        for coach in COACHES:
            slug = coach.lower()
            for kind in ("landing","purchase"):
                stem = slug if kind == "landing" else "start-"+slug
                for embedded in (False,True):
                    for viewport,width,height in (("desktop",1440,1000),("mobile",390,844),("small-mobile",320,740)):
                        context = browser.new_context(viewport={"width":width,"height":height})
                        page = context.new_page()
                        errors = []
                        page.on("pageerror",lambda error:errors.append(str(error)))
                        url,blocked,loaders = route_fixture(page,base,stem,embedded)
                        page.goto(url,wait_until="networkidle")
                        page.evaluate("document.fonts.ready")
                        page.wait_for_function("[...document.querySelectorAll('header img,nav img,[data-brand-logo]')].every(n=>n.tagName!=='IMG'||n.complete)")
                        text = page.locator("body").inner_text()
                        assert coach in text
                        if coach == "Zach":
                            assert "tactical" in text.lower(), "Tactical role missing"
                            assert "firearms" not in text.lower(), "Old firearms wording remains"
                        else:
                            assert "competition prep" in text.lower() or "bodybuilding" in text.lower()
                        brand = brand_check(page,base)
                        photo_src = page.locator(".stg-hero-photo").first.get_attribute("src")
                        if embedded:
                            assert photo_src.startswith("data:image/jpeg;base64,")
                            assert base64.b64decode(photo_src.split(",",1)[1]) == (ROOT/"assets"/(slug+".jpg")).read_bytes()
                            assets = page.evaluate("performance.getEntriesByType('resource').map(r=>r.name).filter(n=>/^https?:/.test(n))")
                            assert not assets, (stem,"Block required assets before checkout intent",assets)
                        else:
                            assert urlparse(photo_src).path.endswith("assets/"+slug+".jpg")
                        assert_geometry(page,width,stem+"/"+viewport)
                        checkout_checks = []
                        if kind == "landing":
                            link = page.locator(".stg-hero [data-purchase-link]").first
                            assert link.text_content().strip() == CTA and link.is_visible()
                            bounds = link.bounding_box()
                            assert bounds and bounds["x"] >= -1 and bounds["x"]+bounds["width"] <= width+1
                            if viewport != "small-mobile":
                                assert bounds["y"] < height, (stem,viewport,"CTA below first screen",bounds)
                            assert urlparse(link.get_attribute("href")).path.endswith("start-"+slug+".html")
                            assert page.locator('a[href="#'+slug+'-intake"]').filter(has_text="Book a call with "+coach).count()
                            goals = page.locator('select[name="goal"]').inner_text().lower()
                            assert ("tactical" in goals) if coach == "Zach" else ("competition" in goals or "bodybuilding" in goals)
                            if viewport == "mobile":
                                link.click()
                                page.wait_for_url("**/start-"+slug+".html")
                                assert page.locator('[data-purchase-page="'+slug+'"]').is_visible()
                                assert page.locator('[data-purchase-embed="'+slug+'"]').count() == 1
                                navigations.append({"coach":coach,"embedded":embedded,"destination":urlparse(page.url).path})
                        else:
                            checkout_checks = purchase_check(page,slug,publishable_key,loaders)
                            if embedded:
                                assets = page.evaluate("performance.getEntriesByType('resource').map(r=>r.name).filter(n=>/^https?:/.test(n))")
                                assert assets == [STRIPE_SCRIPT], (stem,"Unexpected block dependency",assets)
                        assert not errors, (stem,viewport,errors)
                        assert not blocked, (stem,viewport,blocked)
                        all_blocked.extend(blocked)
                        results.append({"coach":coach,"page":kind,"embedded":embedded,"viewport":viewport,
                                        "width":width,"no_overflow":True,"javascript_errors":errors,"brand":brand,
                                        "checkout_checks":checkout_checks,"stubbed_loader_requests":len(loaders)})
                        context.close()
            # Independent loader failure and disabled-JavaScript paths for each
            # standalone purchase page and each pasted HTML block.
            for embedded in (False,True):
                context = browser.new_context(viewport={"width":320,"height":740})
                page = context.new_page()
                errors = []
                page.on("pageerror",lambda error:errors.append(str(error)))
                url,blocked,loaders = route_fixture(page,base,"start-"+slug,embedded,"failed")
                page.goto(url,wait_until="networkidle")
                checks = purchase_check(page,slug,publishable_key,loaders,"failed")
                assert not blocked and not errors, (slug,blocked,errors)
                failures.append({"coach":coach,"embedded":embedded,"width":320,"failure":"loader_aborted","checks":checks})
                context.close()
                context = browser.new_context(viewport={"width":320,"height":740},java_script_enabled=False)
                page = context.new_page()
                url,blocked,loaders = route_fixture(page,base,"start-"+slug,embedded)
                page.goto(url,wait_until="networkidle")
                for service in EXPECTED_OFFERS:
                    link = page.locator('[data-open-checkout="'+service+'"]')
                    assert link.is_visible()
                    assert_checkout_url(link.get_attribute("href"),slug,service)
                    assert link.get_attribute("target") == "_top"
                assert not loaders and not blocked
                no_javascript.append({"coach":coach,"embedded":embedded,"three_attributed_fallback_links":True})
                context.close()
            print(json.dumps({"coach":coach,"status":"passed"}),flush=True)
        # A script can download successfully without defining its custom element.
        # Fast-forward the browser clock to verify that timeout also retains links.
        context = browser.new_context(viewport={"width":320,"height":740})
        page = context.new_page()
        page.clock.install()
        url,blocked,loaders = route_fixture(page,base,"start-justin",False,"timeout")
        page.goto(url,wait_until="networkidle")
        timeout_checks = purchase_check(page,"justin",publishable_key,loaders,"timeout")
        assert not blocked
        failures.append({"coach":"Justin","embedded":False,"width":320,"failure":"custom_element_timeout","checks":timeout_checks})
        context.close()
        browser.close()
    photo_checks = []
    source = Path("/home/jaquesdanger/Strikeline-data/coach-social-personas/2026-10-30/sources")
    for coach in COACHES:
        original = source/(coach+"-highlight-source-photo.jpg")
        current = ROOT/"assets"/(coach.lower()+".jpg")
        assert original.read_bytes() == current.read_bytes(), coach+" photo changed"
        photo_checks.append({"coach":coach,"original_bytes_preserved":True,"sha256":hashlib.sha256(current.read_bytes()).hexdigest()})
    evidence = {"status":"passed","checked_at_utc":datetime.now(timezone.utc).isoformat(),"page_view_checks":len(results),
                "standalone_pages":6,"self_contained_blocks":6,"purchase_navigations":navigations,"live_mutations":0,
                "external_requests":all_blocked,"approved_landing_commit":APPROVED_COMMIT,"approved_landing_preservation_checks":baseline,
                "source_checks":source_checks,"source_receipt_sha256":source_hash,"photo_checks":photo_checks,
                "loader_failure_checks":failures,"javascript_disabled_checks":no_javascript,"results":results,
                "stripe_rendering":"Deterministic local custom-element stub. Actual Stripe iframe appearance and availability are outside this suite.",
                "source_scope":"Product name, amount, cadence and fallback URL cross-checked with the separate saved public Stripe GET receipt. No live Stripe requests performed by this suite.",
                "scope":"Local rendering and navigation. Stripe loader fulfilled locally or deliberately failed; all other external and mutation requests blocked. Checkout links inspected but never followed. No sessions, payments, subscriptions, intake submissions, bookings, publishing or DMs."}
    (ROOT/"evidence/redesign-tests.json").write_text(json.dumps(evidence,indent=2)+"\n")
    print(json.dumps({"status":"passed","page_view_checks":len(results),"navigation_checks":len(navigations),
                      "checkout_dialog_checks":sum(len(item["checkout_checks"]) for item in results),
                      "loader_failure_views":len(failures),"javascript_disabled_views":len(no_javascript),
                      "landing_preservation_checks":len(baseline),"photo_checks":len(photo_checks),"live_mutations":0}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-url',default='http://127.0.0.1:8795')
    parser.add_argument('--chrome',default=CHROME)
    args = parser.parse_args()
    run(args.base_url,args.chrome)

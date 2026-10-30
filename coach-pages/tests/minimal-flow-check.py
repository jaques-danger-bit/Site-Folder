#!/usr/bin/env python3
"""Focused browser checks for photo-only landings, dark intake and pricing.

Formspree is fulfilled synthetically; Stripe is a local render-only stub.
Every other external request or mutation is blocked. No real lead or payment.
"""
import argparse
import json
from datetime import datetime, timezone
from email import policy
from email.parser import BytesParser
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
CHROME = "/home/jaquesdanger/.cache/puppeteer/chrome/linux-149.0.7827.22/chrome-linux64/chrome"
COACHES = {"justin":"3017439","zach":"3017453","rhylie":"3065290"}
BUTTONS = {"assessment":"buy_btn_1UWFCARzFn0Z1SgZqB6Sx8fi","online":"buy_btn_1UWFDHRzFn0Z1SgZci4LXSUf","inperson":"buy_btn_1UWFE2RzFn0Z1SgZvpUqdxYp"}
ENDPOINT = "https://formspree.io/f/mdajqedj"
STRIPE = "https://js.stripe.com/v3/buy-button.js"
PHONE = "+1 (202) 555-0100"
STUB = """customElements.define('stripe-buy-button',class extends HTMLElement{
 connectedCallback(){this.dataset.fixture='ready';this.style.display='block';this.style.padding='20px';
 this.textContent='Checkout render fixture — no payment actions';}
});"""


def intercept(page, base):
    state = {"synthetic_receipts":[],"stubbed_stripe_loads":0,"blocked":[],"errors":[]}
    page.on("pageerror",lambda error:state["errors"].append(str(error)))
    def route_request(route):
        request = route.request
        if request.url == ENDPOINT and request.method == "POST":
            raw = ("Content-Type: "+request.headers["content-type"]+"\r\n\r\n").encode()+request.post_data_buffer
            message = BytesParser(policy=policy.default).parsebytes(raw)
            fields = {part.get_param("name",header="content-disposition"):part.get_payload(decode=True).decode() for part in message.iter_parts()}
            state["synthetic_receipts"].append(fields)
            route.fulfill(status=200,content_type="application/json",body='{"ok":true}')
        elif request.url == STRIPE and request.method == "GET":
            state["stubbed_stripe_loads"] += 1
            route.fulfill(status=200,content_type="application/javascript",body=STUB)
        elif request.method in {"GET","HEAD"} and urlsplit(request.url).netloc == urlsplit(base).netloc:
            route.continue_()
        else:
            state["blocked"].append({"method":request.method,"url":request.url})
            route.abort()
    page.route("**/*",route_request)
    return state


def visual_check(page, width):
    result = page.evaluate(r"""() => {
      const arrows=/[\u2190-\u21ff\u27f0-\u27ff\u2900-\u297f\u2b05-\u2b07\u2b95]/u;
      const visible=n=>{const r=n.getBoundingClientRect(),s=getComputedStyle(n);return r.width>0&&r.height>0&&s.visibility!=='hidden'&&s.display!=='none';};
      const arrowNodes=[],lightBlocks=[];
      for(const n of document.querySelectorAll('body *')){
        if(!visible(n))continue;
        for(const which of ['::before','::after']){
          if(arrows.test(getComputedStyle(n,which).content||''))arrowNodes.push(n.tagName+which);
        }
        if(!n.children.length&&arrows.test(n.innerText||''))arrowNodes.push(n.tagName+' text');
        if(n.matches('section,header,footer,main,article,dialog,form,.stg-form-area,.stg-form-fields,.stg-success')){
          const r=n.getBoundingClientRect(),s=getComputedStyle(n),v=(s.backgroundColor.match(/[\d.]+/g)||[]).map(Number);
          if(r.width*r.height>10000&&v.length>=3&&(v.length<4||v[3]>.8)&&v.slice(0,3).every(x=>x>=220))lightBlocks.push(n.tagName+'.'+n.className);
        }
      }
      return {width:innerWidth,scrollWidth:document.documentElement.scrollWidth,arrowNodes,lightBlocks};
    }""")
    assert result["scrollWidth"] == width, result
    assert not result["arrowNodes"], result
    assert not result["lightBlocks"], result
    return result


def close_intake(page, dialog, trigger, mode="click"):
    if mode == "escape":
        page.keyboard.press("Escape")
    elif mode == "space":
        dialog.locator("[data-intake-close]").focus()
        page.keyboard.press("Space")
    else:
        dialog.locator("[data-intake-close]").click()
    dialog.wait_for(state="hidden")
    page.wait_for_function("document.documentElement.style.overflow !== 'hidden'")
    assert trigger.evaluate("n=>document.activeElement===n"), "Intake did not restore trigger focus"
    assert not urlsplit(page.url).fragment.endswith("-intake")


def intake_submit(page, dialog, coach, staff, state):
    form = dialog.locator("form")
    form.locator('[name="firstName"]').fill("Preview Visitor")
    form.locator('[name="email"]').fill("preview@example.invalid")
    goal = form.locator('[name="goal"]')
    value = goal.evaluate("n=>[...n.options].find(o=>o.value&&!o.disabled).value")
    goal.select_option(value)
    phone = form.locator('[name="phone"]')
    assert phone.get_attribute("required") is not None
    assert phone.get_attribute("pattern") == r".*\S.*"
    for invalid in ("","   "):
        phone.fill(invalid)
        form.locator('button[type="submit"]').click()
        form.evaluate("n=>n.dispatchEvent(new Event('submit',{bubbles:true,cancelable:true}))")
        page.wait_for_timeout(60)
        assert not state["synthetic_receipts"], "Invalid phone reached the intercepted endpoint"
    phone.fill(PHONE)
    form.locator('button[type="submit"]').click()
    dialog.locator("[data-intake-success]").wait_for(state="visible")
    assert len(state["synthetic_receipts"]) == 1
    payload = state["synthetic_receipts"][0]
    assert payload["phone"] == PHONE and payload["coach"] == coach.title()
    assert payload["utm_source"] == "minimal_audit"
    booking = dialog.locator("[data-booking-link]")
    assert booking.is_visible()
    target = urlsplit(booking.get_attribute("href"))
    assert target.hostname == "training.strikelinetraining.com" and target.path == "/a/booking/"
    assert parse_qs(target.query)["staffId"] == [staff] and parse_qs(target.query)["serviceId"] == ["38920"]


def run(base, output):
    views, submissions, navigations, smoke, fallback = [], [], [], [], []
    base = base.rstrip("/")
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROME,headless=True,args=["--no-sandbox"])
        for index,(coach,staff) in enumerate(COACHES.items()):
            for width,height in ((1440,1000),(390,844),(320,740)):
                context = browser.new_context(viewport={"width":width,"height":height})
                page = context.new_page()
                state = intercept(page,base)
                landing = base+f"/{coach}/?utm_source=minimal_audit"
                page.goto(landing,wait_until="networkidle")
                page.evaluate("document.fonts.ready")
                assert page.locator("main > section").count() == 1
                assert page.locator("main > section.stg-hero").count() == 1
                assert not page.locator(".stg-intro,.stg-process,.stg-faq,.stg-faqs,.stg-sticky,footer").count()
                actions = page.locator(".stg-hero-actions a")
                assert actions.count() == 2
                buy = page.locator("[data-purchase-link]")
                assert buy.count() == 1 and buy.inner_text().strip() == "I’m ready to start training"
                assert buy.get_attribute("href") == f"/{coach}/start/"
                trigger = page.locator("[data-open-intake]")
                assert trigger.count() == 1 and trigger.get_attribute("href") == f"#{coach}-intake"
                dialog = page.locator("dialog[data-intake-dialog]")
                assert not dialog.is_visible()
                visual_check(page,width)
                trigger.click()
                dialog.wait_for(state="visible")
                assert dialog.evaluate("n=>n.open&&n.matches(':modal')")
                assert dialog.evaluate("n=>n.scrollWidth<=n.clientWidth+1")
                visual_check(page,width)
                close_intake(page,dialog,trigger)
                trigger.click()
                close_intake(page,dialog,trigger,"escape")
                if width == 390:
                    trigger.click()
                    close_intake(page,dialog,trigger,"space")
                    trigger.click()
                    intake_submit(page,dialog,coach,staff,state)
                    visual_check(page,width)
                    close_intake(page,dialog,trigger)
                    submissions.append({"coach":coach,"required_phone":True,"synthetic_receipt":True,"correct_public_booking":True})
                # Direct links must open the same intake and preserve campaign query.
                page.goto(landing+f"#{coach}-intake",wait_until="networkidle")
                dialog = page.locator("dialog[data-intake-dialog]")
                dialog.wait_for(state="visible")
                close_intake(page,dialog,page.locator("[data-open-intake]"),"escape")
                assert parse_qs(urlsplit(page.url).query)["utm_source"] == ["minimal_audit"]
                page.locator("[data-purchase-link]").click()
                page.wait_for_url("**/"+coach+"/start/")
                page.wait_for_load_state("networkidle")
                assert not page.locator(".stg-hero,details,.stg-purchase-faqs").count()
                assert page.locator("main > section").count() == 1
                assert page.locator("[data-offer-id]").count() == 3
                heading = page.locator(".stg-enrollment h1")
                assert heading.is_visible() and heading.bounding_box()["y"] < height
                visual_check(page,width)
                if width == 390:
                    service = list(BUTTONS)[index]
                    page.locator('[data-open-checkout="'+service+'"]').click()
                    checkout = page.locator("dialog[data-checkout-dialog]")
                    widget = checkout.locator('stripe-buy-button[data-fixture="ready"]')
                    widget.wait_for(state="visible")
                    assert widget.get_attribute("buy-button-id") == BUTTONS[service]
                    assert widget.get_attribute("client-reference-id") == f"stg_{coach}_{service}"
                    fallback_url = urlsplit(checkout.locator("[data-checkout-fallback]").get_attribute("href"))
                    assert fallback_url.hostname == "buy.stripe.com"
                    assert parse_qs(fallback_url.query)["client_reference_id"] == [f"stg_{coach}_{service}"]
                    assert state["stubbed_stripe_loads"] == 1
                    page.keyboard.press("Escape")
                    checkout.wait_for(state="hidden")
                    page.wait_for_function("document.body.style.overflow !== 'hidden'")
                    smoke.append({"coach":coach,"service":service,"attribution":True,"direct_fallback":True})
                    talk = page.locator('.stg-purchase-talk a[href="/'+coach+'/#'+coach+'-intake"]')
                    talk.click()
                    page.wait_for_url("**/"+coach+"/#"+coach+"-intake")
                    page.locator("dialog[data-intake-dialog]").wait_for(state="visible")
                    navigations.append({"coach":coach,"pricing_to_intake_hash":True})
                assert not state["blocked"] and not state["errors"], state
                views.append({"coach":coach,"width":width,"landing_and_pricing":True,"two_hero_actions":True,
                              "no_extra_sections":True,"dark_surfaces":True,"no_arrow_text_or_pseudo_content":True,
                              "cta_and_direct_hash":True,"focus_restored":True,"no_overflow":True})
                context.close()
            context = browser.new_context(viewport={"width":320,"height":740},java_script_enabled=False)
            page = context.new_page()
            state = intercept(page,base)
            page.goto(base+f"/{coach}/#{coach}-intake",wait_until="networkidle")
            dialog = page.locator("dialog[data-intake-dialog]")
            assert dialog.is_visible() and dialog.locator('[name="phone"]').is_visible()
            assert dialog.locator('[name="phone"]').get_attribute("required") is not None
            visual_check(page,320)
            dialog.locator("[data-intake-close]").click()
            dialog.wait_for(state="hidden")
            assert not state["synthetic_receipts"] and not state["blocked"]
            fallback.append({"coach":coach,"javascript_disabled":True,"dark_intake_available":True,"close_works":True})
            context.close()
            print(json.dumps({"coach":coach,"status":"passed"}),flush=True)
        browser.close()
    receipt = {"status":"passed","checked_at_utc":datetime.now(timezone.utc).isoformat(),"base_url":base,
               "responsive_flow_views":views,"synthetic_intakes":submissions,"pricing_to_intake":navigations,
               "stripe_smoke_checks":smoke,"no_javascript_fallbacks":fallback,"live_mutations":0,
               "scope":"Local/browser render checks with synthetic Formspree receipts and a Stripe custom-element stub. Other external requests and mutations blocked. No real leads, bookings, checkout sessions, or payments."}
    output.write_text(json.dumps(receipt,indent=2)+"\n")
    print(json.dumps({"status":"passed","responsive_flow_views":len(views),"synthetic_intakes":len(submissions),
                      "stripe_smoke_checks":len(smoke),"no_javascript_fallbacks":len(fallback),"live_mutations":0}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url",default="http://127.0.0.1:8797")
    parser.add_argument("--evidence",type=Path,default=ROOT/"evidence/minimal-flow-checks.json")
    args = parser.parse_args()
    run(args.base_url,args.evidence)

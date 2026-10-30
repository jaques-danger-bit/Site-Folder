#!/usr/bin/env python3
"""Verify complete landing/pricing content fits each supported viewport.

Checks real text/control bounds and clipping ancestors as well as document
scroll dimensions. External services are blocked or rendered with a local
Stripe stub. No form POST, booking, checkout session or payment is performed.
"""
import argparse
import hashlib
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("minimal_flow",ROOT/"tests/minimal-flow-check.py")
minimal = importlib.util.module_from_spec(spec)
spec.loader.exec_module(minimal)
VIEWPORTS = ((320,568),(375,667),(390,844),(430,932),(768,1024),(1280,720),(1366,768),(1440,900),(844,390))
COACHES = ("justin","zach","rhylie")
OFFERS = {
    "assessment":{"title":"Nutrition + Training Assessment","price":"$175","terms":"Ongoing coaching sold separately."},
    "online":{"title":"Online Coaching","price":"$350","terms":None},
    "inperson":{"title":"In-Person Coaching","price":"$475","terms":"30-day cancellation notice required."},
}


def intercept(page, base):
    state = {"blocked":[],"errors":[],"stripe_stubs":0}
    page.on("pageerror",lambda error:state["errors"].append(str(error)))
    def handler(route):
        request = route.request
        if request.method == "GET" and request.url == minimal.STRIPE:
            state["stripe_stubs"] += 1
            route.fulfill(status=200,content_type="application/javascript",body=minimal.STUB)
        elif request.method in {"GET","HEAD"} and urlsplit(request.url).netloc == urlsplit(base).netloc:
            route.continue_()
        else:
            state["blocked"].append({"method":request.method,"url":request.url})
            route.abort()
    page.route("**/*",handler)
    return state


def measure(page):
    return page.evaluate(r"""() => {
      const problems=[],textBoxes=[],controls=[];
      const arrow=/[\u2190-\u21ff\u2794-\u27bf\u27f0-\u27ff\u2900-\u297f\u2b00-\u2b11\u2b95]/u;
      const rect=r=>({x:r.x,y:r.y,width:r.width,height:r.height,right:r.right,bottom:r.bottom});
      const describe=n=>n.tagName.toLowerCase()+(n.id?'#'+n.id:'')+(n.className&&typeof n.className==='string'?'.'+n.className.split(' ').join('.'):'');
      const visible=n=>{
        if(n.closest('script,style,noscript,dialog:not([open]),[hidden],[aria-hidden="true"],.stg-skip'))return false;
        for(let p=n;p;p=p.parentElement){const s=getComputedStyle(p);if(s.display==='none'||s.visibility==='hidden'||Number(s.opacity)===0)return false;}
        return n.getClientRects().length>0;
      };
      const check=(r,n,label)=>{
        if(r.width<.1||r.height<.1)return;
        if(r.x < -2 || r.y < -2 || r.right > innerWidth+2 || r.bottom > innerHeight+2)problems.push({kind:'outside viewport',node:describe(n),label,rect:rect(r)});
        for(let p=n.parentElement;p&&p!==document.documentElement;p=p.parentElement){
          const s=getComputedStyle(p),b=p.getBoundingClientRect();
          const clipsX=/hidden|clip|auto|scroll/.test(s.overflowX),clipsY=/hidden|clip|auto|scroll/.test(s.overflowY);
          if((clipsX&&(r.x<b.x-2||r.right>b.right+2))||(clipsY&&(r.y<b.y-2||r.bottom>b.bottom+2)))problems.push({kind:'ancestor clipping',node:describe(n),ancestor:describe(p),label,rect:rect(r),clip:rect(b)});
        }
      };
      const walk=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);
      while(walk.nextNode()){
        const text=walk.currentNode,n=text.parentElement;
        if(!text.textContent.trim()||!visible(n))continue;
        const range=document.createRange();range.selectNodeContents(text);
        for(const r of range.getClientRects()){check(r,n,text.textContent.trim().slice(0,90));textBoxes.push({text:text.textContent.trim().slice(0,90),rect:rect(r)});}
        if(arrow.test(text.textContent))problems.push({kind:'arrow text',node:describe(n),text:text.textContent});
      }
      for(const n of document.querySelectorAll('body *')){
        if(!visible(n))continue;
        for(const pseudo of ['::before','::after'])if(arrow.test(getComputedStyle(n,pseudo).content||''))problems.push({kind:'pseudo arrow',node:describe(n),pseudo});
        if(n.matches('a,button,[data-brand-logo]')){const r=n.getBoundingClientRect();check(r,n,n.textContent.trim().slice(0,90));controls.push({node:describe(n),text:n.textContent.trim(),rect:rect(r)});}
      }
      const rootStyle=getComputedStyle(document.documentElement),bodyStyle=getComputedStyle(document.body);
      if([rootStyle.overflowY,bodyStyle.overflowY].some(x=>x==='hidden'||x==='clip'))problems.push({kind:'root scroll masking',html:rootStyle.overflowY,body:bodyStyle.overflowY});
      return {width:innerWidth,height:innerHeight,scrollWidth:document.documentElement.scrollWidth,scrollHeight:Math.max(document.documentElement.scrollHeight,document.body.scrollHeight),problems,textBoxes,controls};
    }""")


def assert_visible_bounds(locator,width,height):
    assert locator.count() == 1 and locator.is_visible(), "Required content missing or hidden"
    bounds = locator.bounding_box()
    assert bounds and bounds["width"]>0 and bounds["height"]>0
    assert bounds["x"]>=-2 and bounds["y"]>=-2 and bounds["x"]+bounds["width"]<=width+2 and bounds["y"]+bounds["height"]<=height+2, bounds


def smoke(page, coach, kind, state):
    if kind == "landing":
        trigger = page.locator("[data-open-intake]")
        trigger.click()
        dialog = page.locator("dialog[data-intake-dialog]")
        dialog.wait_for(state="visible")
        phone = dialog.locator('[name="phone"]')
        assert phone.get_attribute("required") is not None and phone.get_attribute("pattern") == r".*\S.*"
        for invalid in ("","   "):
            phone.fill(invalid)
            assert not phone.evaluate("n=>n.checkValidity()")
        phone.fill(minimal.PHONE)
        assert phone.evaluate("n=>n.checkValidity()")
        minimal.close_intake(page,dialog,trigger,"escape")
        return {"intake_modal":True,"phone_required":True,"empty_and_whitespace_invalid":True,"focus_restored":True,"form_submitted":False}
    service = list(OFFERS)[COACHES.index(coach)]
    trigger = page.locator('[data-open-checkout="'+service+'"]')
    trigger.click()
    dialog = page.locator("dialog[data-checkout-dialog]")
    button = dialog.locator('stripe-buy-button[data-fixture="ready"]')
    button.wait_for(state="visible")
    assert button.get_attribute("buy-button-id") == minimal.BUTTONS[service]
    reference = f"stg_{coach}_{service}"
    assert button.get_attribute("client-reference-id") == reference
    target = urlsplit(dialog.locator("[data-checkout-fallback]").get_attribute("href"))
    assert target.hostname == "buy.stripe.com" and parse_qs(target.query)["client_reference_id"] == [reference]
    assert state["stripe_stubs"] == 1
    page.keyboard.press("Escape")
    dialog.wait_for(state="hidden")
    page.wait_for_function("document.body.style.overflow !== 'hidden'")
    assert trigger.evaluate("n=>n===document.activeElement")
    return {"stripe_service":service,"reference":reference,"fallback_correct":True,"focus_restored":True,"real_widget_loaded":False}


def pricing_baseline_check(browser, base, baseline_path):
    baseline = json.loads(baseline_path.read_text())
    files,views = [],[]
    for item in baseline["files"]:
        current = (ROOT/item["path"]).read_bytes()
        assert len(current) == item["bytes"] and hashlib.sha256(current).hexdigest() == item["sha256"], "Pricing/shared baseline changed: "+item["path"]
        files.append({"path":item["path"],"sha256":item["sha256"],"unchanged":True})
    for expected in baseline["style_views"]:
        context = browser.new_context(viewport=expected["viewport"])
        page = context.new_page()
        state = intercept(page,base)
        page.goto(base.rstrip("/")+"/"+expected["coach"]+"/start/",wait_until="networkidle")
        page.evaluate("document.fonts.ready")
        current = page.evaluate("""selectors=>Object.fromEntries(selectors.map(selector=>[selector,[...document.querySelectorAll(selector)].map(n=>{const s=getComputedStyle(n),r=n.getBoundingClientRect(),props=['display','position','fontFamily','fontSize','fontWeight','lineHeight','letterSpacing','color','backgroundColor','padding','margin','border','gap','gridTemplateColumns','gridTemplateRows','alignItems','justifyContent'];return {rect:{x:r.x,y:r.y,width:r.width,height:r.height},styles:Object.fromEntries(props.map(k=>[k,s[k]]))};})]))""",list(expected["selectors"]))
        assert current == expected["selectors"], {"pricing_style_changed":expected["coach"],"viewport":expected["viewport"],"selectors":[key for key in current if current[key] != expected["selectors"][key]]}
        assert not state["blocked"] and not state["errors"],state
        views.append({"coach":expected["coach"],"viewport":expected["viewport"],"computed_styles_and_bounds_unchanged":True})
        context.close()
    return {"baseline":str(baseline_path),"files":files,"computed_style_views":views,"status":"passed"}


def run(base, output, screenshots, landing_only=False, pricing_baseline=None):
    results, failures = [], []
    screenshots.mkdir(parents=True,exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=minimal.CHROME,headless=True,args=["--no-sandbox"])
        for coach in COACHES:
            for kind in (("landing",) if landing_only else ("landing","pricing")):
                route = f"/{coach}/"+("start/" if kind == "pricing" else "")
                for width,height in VIEWPORTS:
                    context = browser.new_context(viewport={"width":width,"height":height})
                    page = context.new_page()
                    state = intercept(page,base)
                    try:
                        page.goto(base.rstrip("/")+route,wait_until="networkidle")
                        page.evaluate("document.fonts.ready")
                        assert not page.locator(".stg-offer-number,.stg-offer-badge,.stg-offer-top,hr,[role=separator],[class*=divider]").count(), "Number, badge or decorative divider remains"
                        if kind == "landing":
                            assert page.locator(".stg-hero-actions a").count() == 2
                            if landing_only:
                                # Restored screenshot design intentionally includes the
                                # header Talk link, specialty line and bottom full name.
                                for selector in (".stg-nav-call",".stg-hero .stg-kicker",".stg-hero-meta strong"):
                                    assert_visible_bounds(page.locator(selector),width,height)
                                assert not page.locator(".stg-helper,.stg-intro,.stg-process,.stg-faqs,.stg-sticky").count()
                            for selector in ("h1",".stg-hero-description","[data-purchase-link]","[data-open-intake]"):
                                assert_visible_bounds(page.locator(selector),width,height)
                        else:
                            assert page.locator("[data-offer-id]").count() == 3
                            assert not page.locator(".stg-hero").count()
                            for service,expected in OFFERS.items():
                                card = page.locator('[data-offer-id="'+service+'"]')
                                assert card.locator("h3").inner_text().strip().lower() == expected["title"].lower()
                                assert expected["price"] in card.locator(".stg-offer-price").inner_text()
                                if expected["terms"]:
                                    assert card.locator(".stg-offer-terms").inner_text().strip() == expected["terms"]
                                    assert_visible_bounds(card.locator(".stg-offer-terms"),width,height)
                                else:
                                    assert not card.locator(".stg-offer-terms").count(), "Redundant subscription term remains"
                                price_text = card.locator(".stg-offer-price").inner_text().lower()
                                assert ("one time" in price_text or "one-time" in price_text) if service == "assessment" else ("month" in price_text)
                                for selector in ("h3",".stg-offer-price",".stg-offer-description","[data-open-checkout]"):
                                    assert_visible_bounds(card.locator(selector),width,height)
                        report = measure(page)
                        assert report["scrollWidth"] <= width and report["scrollHeight"] <= height+2, {"width":width,"height":height,"scrollWidth":report["scrollWidth"],"scrollHeight":report["scrollHeight"]}
                        assert not report["problems"], report["problems"]
                        evidence = {"coach":coach,"page":kind,"viewport":{"width":width,"height":height},"measurement":report}
                        if (width,height) in {(320,568),(390,844),(1440,900)}:
                            shot = screenshots/f"{coach}-{kind}-{width}x{height}.png"
                            page.screenshot(path=str(shot),full_page=False)
                            evidence["screenshot"] = str(shot)
                        if (width,height) == (390,844):
                            evidence["smoke"] = smoke(page,coach,kind,state)
                            if landing_only:
                                header = page.locator(".stg-nav-call")
                                header.click()
                                dialog = page.locator("dialog[data-intake-dialog]")
                                dialog.wait_for(state="visible")
                                minimal.close_intake(page,dialog,header,"escape")
                                evidence["header_talk_smoke"] = {"opens_intake":True,"focus_restored":True}
                        assert not state["blocked"] and not state["errors"], state
                        results.append(evidence)
                    except Exception as error:
                        shot = screenshots/f"FAIL-{coach}-{kind}-{width}x{height}.png"
                        page.screenshot(path=str(shot),full_page=True)
                        failure = {"coach":coach,"page":kind,"viewport":{"width":width,"height":height},"error":str(error),"measurement":measure(page),"screenshot":str(shot)}
                        failures.append(failure)
                        print(json.dumps({"status":"failed","coach":coach,"page":kind,"width":width,"height":height,"error":str(error)}),flush=True)
                    context.close()
            print(json.dumps({"coach":coach,"finished":True}),flush=True)
        preservation = pricing_baseline_check(browser,base,pricing_baseline) if pricing_baseline else None
        browser.close()
    receipt = {"status":"failed" if failures else "passed","checked_at_utc":datetime.now(timezone.utc).isoformat(),
               "base_url":base,"viewport_sizes":VIEWPORTS,"passed_page_views":len(results),"failed_page_views":len(failures),
               "results":results,"failures":failures,"pricing_preservation":preservation,"live_mutations":0,
               "scope":"Actual rendered text/control bounds, ancestor clipping and document dimensions at9sizes. Restored-hero mode checks27landings and compares pricing files/styles to its pre-edit baseline. Intake validity/focus checks and optional Stripe stubs only; no form POST, booking, checkout session or payment."}
    output.write_text(json.dumps(receipt,indent=2)+"\n")
    print(json.dumps({"status":receipt["status"],"passed_page_views":len(results),"failed_page_views":len(failures),"evidence":str(output)}))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url",default="http://127.0.0.1:8797")
    parser.add_argument("--evidence",type=Path,default=ROOT/"evidence/viewport-fit-checks.json")
    parser.add_argument("--screenshots",type=Path,default=ROOT/"evidence/screenshots/viewport-fit")
    parser.add_argument("--landing-only",action="store_true")
    parser.add_argument("--pricing-baseline",type=Path)
    args = parser.parse_args()
    run(args.base_url,args.evidence,args.screenshots,args.landing_only,args.pricing_baseline)

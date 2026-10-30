#!/usr/bin/env python3
"""Bounded confirmation-state QA with mocked Formspree responses only."""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
CHROME = "/home/jaquesdanger/.cache/puppeteer/chrome/linux-149.0.7827.22/chrome-linux64/chrome"
ENDPOINT = "https://formspree.io/f/mdajqedj"
COACHES = {"Justin":"3017439","Zach":"3017453","Rhylie":"3065290"}
CONFIRMATION = "A coach will reach out to you soon. Prefer to choose a time now? Book a call that fits your schedule."


def run(base, output, screenshot):
    checks = []
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROME,headless=True,args=["--no-sandbox"])
        for coach,mode in [(name,"success") for name in COACHES]+[("Justin","error")]:
            context = browser.new_context(viewport={"width":390,"height":844})
            page = context.new_page()
            state = {"mocked_posts":0,"blocked":[],"errors":[]}
            page.on("pageerror",lambda error:state["errors"].append(str(error)))
            def handler(route):
                request = route.request
                if request.url == ENDPOINT and request.method == "POST":
                    state["mocked_posts"] += 1
                    route.fulfill(status=200 if mode == "success" else 422,
                                  content_type="application/json",body='{"ok":true}' if mode == "success" else '{"ok":false}')
                elif request.method in {"GET","HEAD"} and urlsplit(request.url).netloc == urlsplit(base).netloc:
                    route.continue_()
                else:
                    state["blocked"].append({"method":request.method,"url":request.url})
                    route.abort()
            page.route("**/*",handler)
            page.goto(base.rstrip("/")+"/"+coach.lower()+"/",wait_until="networkidle")
            page.locator("[data-open-intake]").click()
            dialog = page.locator("dialog[data-intake-dialog]")
            dialog.wait_for(state="visible")
            form = dialog.locator("form[data-coach-intake]")
            assert form.locator('button[type="submit"]').inner_text().strip() == "Send my details"
            form.locator('[name="firstName"]').fill("Preview Visitor")
            form.locator('[name="email"]').fill("preview@example.invalid")
            form.locator('[name="phone"]').fill("+1 (202) 555-0100")
            goal = form.locator('[name="goal"]')
            goal.select_option(goal.evaluate("n=>[...n.options].find(o=>o.value&&!o.disabled).value"))
            form.locator('button[type="submit"]').click()
            page.locator('[data-form-status][data-state="'+mode+'"]').wait_for(state="visible")
            assert state["mocked_posts"] == 1
            success = dialog.locator("[data-intake-success]")
            if mode == "success":
                assert success.is_visible()
                assert success.locator("h3").text_content().strip() == "Thank you!"
                assert success.locator("p").inner_text().strip() == CONFIRMATION
                assert not success.locator(".stg-kicker").count(), "Mandatory next-step kicker remains"
                assert page.locator("[data-form-status]").inner_text().strip() == "Your details were received."
                booking = success.locator("[data-booking-link]")
                assert booking.is_visible() and booking.inner_text().strip() == "Book a call with "+coach
                target = urlsplit(booking.get_attribute("href"))
                assert target.scheme == "https" and target.hostname == "training.strikelinetraining.com" and target.path == "/a/booking/"
                query = parse_qs(target.query)
                assert query["staffId"] == [COACHES[coach]] and query["serviceId"] == ["38920"]
                assert not form.locator("[data-form-fields]").is_visible()
                if coach == "Justin" and screenshot:
                    screenshot.parent.mkdir(parents=True,exist_ok=True)
                    dialog.screenshot(path=str(screenshot))
                result = {"coach":coach,"mode":mode,"thank_you":True,"coach_outreach_copy":True,
                          "self_booking_optional":True,"booking_url":booking.get_attribute("href"),"no_automatic_navigation":True}
            else:
                assert not success.is_visible(), "Failed intake showed the outreach promise"
                assert form.locator("[data-form-fields]").is_visible()
                assert form.locator('button[type="submit"]').is_enabled()
                assert form.locator('[name="email"]').input_value() == "preview@example.invalid"
                result = {"coach":coach,"mode":mode,"no_false_confirmation":True,"answers_retained":True,"retry_available":True}
            assert urlsplit(page.url).netloc == urlsplit(base).netloc
            assert not state["blocked"] and not state["errors"],state
            result["mocked_posts"] = state["mocked_posts"]
            checks.append(result)
            context.close()
        browser.close()
    receipt = {"status":"passed","checked_at_utc":datetime.now(timezone.utc).isoformat(),"base_url":base,
               "checks":checks,"screenshot":str(screenshot) if screenshot else None,"live_submissions":0,
               "scope":"Three successful Formspree receipts and one422 error fulfilled locally by request interception. All other external or mutation requests blocked. Booking links inspected only; no real leads, bookings, messages, payments or checkout sessions."}
    output.write_text(json.dumps(receipt,indent=2)+"\n")
    print(json.dumps({"status":"passed","success_states":3,"error_states":1,"live_submissions":0,"evidence":str(output)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url",default="http://127.0.0.1:8797")
    parser.add_argument("--evidence",type=Path,default=ROOT/"evidence/intake-confirmation-checks.json")
    parser.add_argument("--screenshot",type=Path)
    args = parser.parse_args()
    run(args.base_url,args.evidence,args.screenshot)

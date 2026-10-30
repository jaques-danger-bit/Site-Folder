#!/usr/bin/env python3
"""Browser contract checks. All external traffic is intercepted; no live intake sends."""
import argparse
import asyncio
import json
from datetime import datetime, timezone
from email import policy
from email.parser import BytesParser
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

from playwright.async_api import async_playwright

ENDPOINT = "https://formspree.io/f/mdajqedj"
CHROME = "/home/jaquesdanger/.cache/puppeteer/chrome/linux-149.0.7827.22/chrome-linux64/chrome"
STAFF = {"Justin": "3017439", "Zach": "3017453", "Rhylie": "3065290"}
PHONE = "+1 (202) 555-0100"


def fields_from_request(request):
    header = request.headers["content-type"]
    message = BytesParser(policy=policy.default).parsebytes(
        ("Content-Type: " + header + "\r\n\r\n").encode() + request.post_data_buffer
    )
    return {
        part.get_param("name", header="content-disposition"): part.get_payload(decode=True).decode()
        for part in message.iter_parts()
    }


async def fixture(browser, base, coach="Justin", mode="success", timeout=False, embed=False):
    context = await browser.new_context(viewport={"width": 390, "height": 844})
    await context.add_init_script("""
      window.intakeEvents = [];
      document.addEventListener('stg:intake-success', event => window.intakeEvents.push(event.detail));
    """)
    if timeout:
        await context.add_init_script("""
          const normalTimeout = window.setTimeout;
          window.setTimeout = (fn, delay, ...args) => normalTimeout(fn, delay === 20000 ? 100 : delay, ...args);
        """)
    page = await context.new_page()
    state = {"mode": mode, "requests": [], "unexpected": []}

    async def route_request(route):
        request = route.request
        if request.url == ENDPOINT:
            assert request.method == "POST"
            state["requests"].append(fields_from_request(request))
            current = state["mode"]
            if current in {"slow-success", "timeout"}:
                await asyncio.sleep(0.35)
            try:
                if current == "network":
                    await route.abort("failed")
                elif current in {"422", "429"}:
                    await route.fulfill(status=int(current), content_type="application/json", body='{"ok":false}')
                elif current == "malformed":
                    await route.fulfill(status=200, content_type="text/html", body="unexpected HTML")
                elif current == "false-ok":
                    await route.fulfill(status=200, content_type="application/json", body='{"ok":false}')
                else:
                    await route.fulfill(status=200, content_type="application/json", body='{"ok":true}')
            except Exception:
                # An aborted timeout request may already be gone when this mock finishes.
                if current != "timeout":
                    raise
        elif embed and urlparse(request.url).path == "/coach-pages/test-embed/" + coach.lower() + ".html":
            block = (Path(__file__).resolve().parents[1] / "blocks" / (coach.lower() + "-copy-paste.html")).read_text()
            await route.fulfill(status=200, content_type="text/html", body=(
                '<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>'
                '<body><div id="host-html-block">' + block + '</div></body></html>'
            ))
        elif urlparse(request.url).netloc == urlparse(base).netloc:
            await route.continue_()
        else:
            state["unexpected"].append(request.url)
            await route.abort()

    await page.route("**/*", route_request)
    query = urlencode({
        "utm_source": "instagram", "utm_medium": "social", "utm_campaign": "x" * 200,
        "coach": "Wrong coach", "source": "override-attempt", "redirect": "https://example.invalid/",
        "email": "query-must-not-send@example.invalid", "arbitrary": "must-not-send"
    })
    segment = "/coach-pages/test-embed/" if embed else "/coach-pages/"
    await page.goto(base.rstrip("/") + segment + coach.lower() + ".html?" + query)
    await page.wait_for_function("document.querySelector('form[data-coach-intake]')?.dataset.intakeBound === 'true'")
    state["source"] = await page.locator('form [name="source"]').input_value()
    state["storage"] = await page.evaluate("JSON.stringify([Object.entries(localStorage), Object.entries(sessionStorage)])")
    return context, page, state


async def fill_form(page):
    await page.locator('form [name="firstName"]').fill("Preview Visitor")
    await page.locator('form [name="email"]').fill("preview@example.invalid")
    await page.locator('form [name="phone"]').fill(PHONE)
    goal = page.locator('form [name="goal"]')
    if await goal.evaluate("el => el.tagName") == "SELECT":
        value = await goal.evaluate("el => [...el.options].find(option => option.value && !option.disabled).value")
        await goal.select_option(value)
    else:
        await goal.fill("Build strength")
    await page.locator('form [name="goalNotes"]').fill("Preview-only test; never sent to a live service.")


async def wait_state(page, state):
    await page.wait_for_function("state => document.querySelector('[data-form-status]').dataset.state === state", arg=state)


async def required_phone_check(page, state):
    phone = page.locator('form [name="phone"]')
    assert await phone.get_attribute("required") is not None
    assert await phone.get_attribute("pattern") == r".*\S.*"
    assert await phone.get_attribute("type") == "tel"
    assert await phone.get_attribute("autocomplete") == "tel"
    assert await phone.get_attribute("maxlength") == "40"
    phone_id = await phone.get_attribute("id")
    label = await page.locator('label[for="'+phone_id+'"]').inner_text()
    assert "required" in label.lower() and "optional" not in label.lower()
    for invalid in ("", "   "):
        await phone.fill(invalid)
        assert not await phone.evaluate("el=>el.checkValidity()")
        # Both native submission and a scripted submit must respect validity.
        await page.locator('form button[type="submit"]').click()
        await page.locator('form[data-coach-intake]').evaluate("form=>form.dispatchEvent(new Event('submit',{bubbles:true,cancelable:true}))")
        await page.wait_for_timeout(80)
        assert not state["requests"], "Empty or whitespace-only phone reached intake endpoint"
        assert not await page.locator('[data-intake-success]').is_visible()
    await phone.fill(PHONE)
    assert await phone.evaluate("el=>el.checkValidity()"), "Formatted phone was rejected"


async def run(base, chrome):
    checks = []
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(executable_path=chrome, headless=True, args=["--no-sandbox"])
        for coach, staff in STAFF.items():
            context, page, state = await fixture(browser, base, coach, "slow-success")
            await page.wait_for_function("document.querySelector('[data-sticky-cta]').hidden")
            await fill_form(page)
            await required_phone_check(page, state)
            await page.wait_for_function("document.querySelector('[data-sticky-cta]').hidden")
            await page.locator('form button[type="submit"]').click()
            await page.locator('form[data-coach-intake]').evaluate("form => form.dispatchEvent(new Event('submit', {bubbles: true, cancelable: true}))")
            await wait_state(page, "success")
            assert len(state["requests"]) == 1, "Duplicate submit escaped the lock"
            sent = state["requests"][0]
            for key in ["firstName", "email", "phone", "goal", "goalNotes", "source", "coach", "submission_id"]:
                assert sent.get(key), (coach, key)
            assert sent["coach"] == coach and sent["source"] == state["source"]
            assert sent["email"] == "preview@example.invalid"
            assert sent["phone"] == PHONE
            assert sent["utm_source"] == "instagram" and sent["utm_medium"] == "social"
            assert len(sent["utm_campaign"]) == 120
            assert not {"redirect", "arbitrary", "referrer", "query"}.intersection(sent)
            assert await page.locator('[data-intake-success]').is_visible()
            assert not await page.locator('[data-sticky-cta]').is_visible()
            assert not await page.locator('[data-form-fields]').is_visible()
            booking = urlparse(await page.locator('[data-intake-success] [data-booking-link]').get_attribute("href"))
            params = parse_qs(booking.query)
            assert booking.netloc == "training.strikelinetraining.com"
            assert params["staffId"] == [staff] and params["serviceId"] == ["38920"]
            assert urlparse(page.url).netloc == urlparse(base).netloc, "Unexpected automatic navigation"
            assert await page.evaluate("window.intakeEvents") == [{"coach": coach, "submission_id": sent["submission_id"]}]
            assert await page.evaluate("JSON.stringify([Object.entries(localStorage), Object.entries(sessionStorage)])") == state["storage"]
            assert not any(urlparse(url).path.startswith('/a/booking') for url in state["unexpected"])
            checks.append(coach + ": required phone blocks empty/whitespace, formatted phone payload, attribution, duplicate lock, booking route, no PII storage/event, contextual sticky CTA")
            await context.close()

        for mode in ["422", "429", "malformed", "false-ok", "network", "timeout"]:
            context, page, state = await fixture(browser, base, mode=mode, timeout=(mode == "timeout"))
            await fill_form(page)
            await page.locator('form button[type="submit"]').click()
            await wait_state(page, "error")
            assert len(state["requests"]) == 1
            assert not await page.locator('[data-intake-success]').is_visible()
            assert await page.locator('form [name="email"]').input_value() == "preview@example.invalid"
            assert await page.locator('form button[type="submit"]').is_enabled()
            assert await page.evaluate("window.intakeEvents") == []
            original_id = state["requests"][0]["submission_id"]
            state["mode"] = "success"
            await page.locator('form button[type="submit"]').click()
            await wait_state(page, "success")
            assert len(state["requests"]) == 2
            assert state["requests"][1]["submission_id"] == original_id
            assert state["requests"][1]["email"] == state["requests"][0]["email"]
            checks.append(mode + ": preserve answers, no false success, explicit retry keeps ID")
            await context.close()

        context, page, state = await fixture(browser, base)
        await page.locator('form button[type="submit"]').click()
        assert not state["requests"], "Blank required fields submitted"
        await fill_form(page)
        await page.locator('form [name="email"]').fill("not-an-email")
        await page.locator('form button[type="submit"]').click()
        assert not state["requests"], "Invalid email submitted"
        checks.append("Native required-field and email validation blocks network")
        await context.close()

        for coach, staff in STAFF.items():
            context, page, state = await fixture(browser, base, coach, embed=True)
            await fill_form(page)
            await required_phone_check(page, state)
            await page.locator('form button[type="submit"]').click()
            await wait_state(page, "success")
            assert len(state["requests"]) == 1
            sent = state["requests"][0]
            assert sent["coach"] == coach and sent["source"] == state["source"]
            assert sent["phone"] == PHONE, "Required phone omitted from payload"
            booking = urlparse(await page.locator('[data-intake-success] [data-booking-link]').get_attribute("href"))
            assert parse_qs(booking.query)["staffId"] == [staff]
            assert not state["unexpected"], "Self-contained block requested an external asset"
            assert await page.locator('[data-intake-success]').is_visible()
            checks.append(coach + " paste block: required phone blocks empty/whitespace, formatted phone payload, wrapped-host receipt, correct coach booking, embedded assets")
            await context.close()
        await browser.close()
    receipt = {"status":"passed", "checked_at_utc":datetime.now(timezone.utc).isoformat(),
               "check_count":len(checks), "live_submissions":0, "checks":checks,
               "required_phone":{"standalone_pages":3,"wrapped_blocks":3,"blocked_values":["","   "],
                                 "submission_paths_checked":["native submit","scripted submit"],"successful_phone_payload":PHONE},
               "scope":"Local browser contract checks. Formspree responses are synthetic; other external requests are aborted. No live intake submissions, bookings, payments, or messages."}
    (Path(__file__).resolve().parents[1]/"evidence/intake-tests.json").write_text(json.dumps(receipt,indent=2)+"\n")
    print(json.dumps(receipt,indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8795")
    parser.add_argument("--chrome", default=CHROME)
    args = parser.parse_args()
    asyncio.run(run(args.base_url, args.chrome))

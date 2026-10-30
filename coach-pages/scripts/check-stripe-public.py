#!/usr/bin/env python3
"""Inspect real Stripe Buy Button widgets without checkout navigation or payments."""
import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from playwright.async_api import async_playwright
ROOT = Path(__file__).resolve().parents[1]
CHROME = '/home/jaquesdanger/.cache/puppeteer/chrome/linux-149.0.7827.22/chrome-linux64/chrome'
BASE = 'http://127.0.0.1:8795'
async def main():
    offers = json.loads((ROOT/'offers.json').read_text())['offers']
    receipt = {'checked_at_utc':datetime.now(timezone.utc).isoformat(), 'method':'Open local chooser dialogs and render real Stripe widgets. Allow GET/HEAD/OPTIONS only; block checkout navigation and all other methods.', 'payments_attempted':0, 'results':[], 'blocked_requests':[]}
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path=CHROME,headless=True,args=['--no-sandbox'])
        for width in [1440,320]:
            ctx = await browser.new_context(viewport={'width':width,'height':1000},device_scale_factor=1)
            async def route(r):
                req = r.request
                host = urlparse(req.url).hostname or ''
                if req.method not in ['GET','HEAD','OPTIONS'] or host in ['buy.stripe.com','checkout.stripe.com']:
                    receipt['blocked_requests'].append({'host':host,'method':req.method})
                    await r.abort()
                else:
                    await r.continue_()
            await ctx.route('**/*',route)
            page = await ctx.new_page()
            await page.goto(BASE+'/coach-pages/start-justin.html',wait_until='domcontentloaded')
            await page.evaluate('document.fonts.ready')
            for offer in offers:
                if not offer.get('checkoutReady'): continue
                await page.locator('[data-open-checkout="'+offer['slug']+'"]').click()
                dialog = page.get_by_role('dialog')
                await dialog.wait_for(state='visible')
                button = dialog.locator('stripe-buy-button')
                await button.wait_for(state='attached')
                assert await button.get_attribute('buy-button-id') == offer['buttonId']
                assert await button.get_attribute('client-reference-id') == 'stg_justin_'+offer['slug']
                text = ''
                for _ in range(40):
                    for f in page.frames:
                        if 'buy-button-app-' in f.url and offer['buttonId'] in f.url:
                            try: text = await f.locator('body').inner_text(timeout=500)
                            except Exception: pass
                    if offer['stripeProductName'] in text and '$'+str(offer['amount']) in text: break
                    await page.wait_for_timeout(250)
                assert offer['stripeProductName'] in text, text
                assert '$'+str(offer['amount']) in text, text
                if offer['cadence']=='per month': assert 'month' in text, text
                geometry = await dialog.evaluate('(e)=>({width:e.clientWidth,scrollWidth:e.scrollWidth,height:e.clientHeight,scrollHeight:e.scrollHeight})')
                assert geometry['scrollWidth'] <= geometry['width']+1, geometry
                assert await page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
                screenshot='stripe-'+offer['slug']+'-'+str(width)+'.png'
                await page.screenshot(path=str(ROOT/'evidence/screenshots'/screenshot))
                receipt['results'].append({'offer':offer['slug'],'viewport':width,'text':text,'dialog':geometry,'client_reference_id':await button.get_attribute('client-reference-id'),'screenshot':'screenshots/'+screenshot})
                await page.keyboard.press('Escape')
                await dialog.wait_for(state='hidden')
            await ctx.close()
        await browser.close()
    receipt['status']='passed'
    (ROOT/'evidence/stripe-public-render.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({'status':'passed','real_widgets_checked':len(receipt['results']),'payments_attempted':0},indent=2))
if __name__=='__main__': asyncio.run(main())

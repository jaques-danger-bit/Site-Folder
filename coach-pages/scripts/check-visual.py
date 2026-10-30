"""Browser screenshots of original assets; external requests are blocked."""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT/'evidence/screenshots'
SHOTS.mkdir(exist_ok=True)
results = []
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/home/jaquesdanger/.cache/puppeteer/chrome/linux-149.0.7827.22/chrome-linux64/chrome', headless=True, args=['--no-sandbox'])
    for coach in ['justin','zach','rhylie']:
        for kind,width,height in [('desktop',1440,1000),('mobile',390,844),('small-mobile',320,740)]:
            page = browser.new_page(viewport={'width':width,'height':height},device_scale_factor=1)
            errors = []
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.route('https://**/*',lambda r:r.abort())
            page.goto(f'http://127.0.0.1:8795/coach-pages/{coach}.html')
            page.evaluate('document.fonts.ready')
            page.locator('.stg-mini-portrait').scroll_into_view_if_needed()
            page.wait_for_function('[...document.images].every(i=>i.complete && i.naturalWidth>0)')
            page.evaluate('document.documentElement.style.scrollBehavior="auto";window.scrollTo({top:0,left:0,behavior:"instant"})')
            page.wait_for_function('window.scrollY === 0')
            page.wait_for_timeout(200)
            if kind != 'small-mobile':
                page.screenshot(path=str(SHOTS/f'{coach}-{kind}-hero.png'))
                page.screenshot(path=str(SHOTS/f'{coach}-{kind}.png'),full_page=True)
            result = {'coach':coach,'viewport':kind,'jsErrors':errors,**page.evaluate('({width:innerWidth,scrollWidth:document.documentElement.scrollWidth,allImagesLoaded:[...document.images].every(i=>i.complete&&i.naturalWidth>0),heroHeight:document.querySelector(".stg-hero").clientHeight})')}
            assert result['scrollWidth']==width, result
            assert result['allImagesLoaded'] and not errors, result
            results.append(result)
            page.close()
    browser.close()
(ROOT/'evidence/visual-check.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results))

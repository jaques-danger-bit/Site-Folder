"""Build coach purchase pages; checkout stays pending until approved embeds arrive.

Integration: call build_purchase_pages(root, coaches, embedded_fonts, shared_css,
logo_svg) from build.py. The optional purchase-embeds/{slug}.html file contains
the exact trusted checkout embed supplied by the owner. Missing, empty, or
comment-only files render the honest pending state. Do not put credentials in
those files. The generator does not create products, prices, or payment links.
"""

from pathlib import Path
import base64
import html
import re
import xml.etree.ElementTree as ET


def _data_uri(mime, content):
    return 'data:' + mime + ';base64,' + base64.b64encode(content).decode('ascii')


def _embed(root, slug):
    path = root / 'purchase-embeds' / (slug + '.html')
    if not path.is_file():
        return ''
    content = path.read_text(encoding='utf-8')
    # Empty configuration placeholders must not accidentally remove the useful fallback.
    if not re.sub(r'<!--.*?-->', '', content, flags=re.S).strip():
        return ''
    return content


def _markup(coach, logo_uri, embed, badge_uri):
    esc = html.escape
    slug, name = coach['slug'], coach['name']
    back = slug + '.html'
    talk = back + '#' + slug + '-intake'
    focus = ''.join('<li>' + esc(goal['label']) + '</li>' for goal in coach['goals']
                    if 'not sure' not in goal['value'].lower())
    content = embed or f'''<div class="stg-enrollment-empty" data-enrollment-pending>
<h3>Online enrollment is being prepared.</h3>
<p>You can still take the next step. Tell {esc(name)} what you want to work on and talk through the right training option for you.</p>
<a class="stg-button" href="{talk}" target="_top">Talk with {esc(name)}</a>
</div>'''
    return f'''<div class="stg-coach-page stg-purchase-page" data-coach="{esc(name)}">
<a class="stg-skip" href="#{slug}-enrollment">Skip to enrollment</a>
<header class="stg-purchase-header"><div class="stg-shell stg-purchase-header-inner">
<a class="stg-brand" href="https://strikelinetraining.com/" target="_top" aria-label="Strikeline Training Group home"><img data-brand-logo src="{logo_uri}" alt="Strikeline Training Group"></a>
<a class="stg-purchase-back" href="{back}" target="_top">← Back to {esc(name)}</a></div></header>
<main>
<section class="stg-purchase-hero" aria-labelledby="{slug}-purchase-title">
<img class="stg-purchase-photo" src="assets/{slug}.jpg" alt="{esc(coach['fullName'])} at Strikeline" fetchpriority="high" decoding="async">
<div class="stg-shell stg-purchase-layout">
<div class="stg-purchase-copy"><p class="stg-kicker">{esc(coach['specialty'])}</p><h1 id="{slug}-purchase-title"><span>Start training</span><span>with {esc(name)}.</span></h1><p>Put your goal into motion. Find the training option that fits what you want to build.</p>
<div class="stg-purchase-focus"><p class="stg-purchase-focus-label">What are you working toward?</p><ul class="stg-purchase-focus-list">{focus}</ul></div></div>
<section class="stg-enrollment" id="{slug}-enrollment" aria-labelledby="{slug}-enrollment-title"><p class="stg-kicker">Your next step</p><h2 id="{slug}-enrollment-title">Make room<br>for your goal.</h2><p class="stg-enrollment-intro">Training with {esc(name)} starts with choosing the right fit for you.</p>
<div data-purchase-embed="{slug}">{content}</div>
<p class="stg-purchase-help">Have a question before you start? <a href="{talk}" target="_top">Talk with {esc(name)}</a>.</p></section>
</div></section>
<section class="stg-purchase-faqs" aria-labelledby="{slug}-purchase-faq-title"><div class="stg-shell stg-purchase-faq-layout"><h2 id="{slug}-purchase-faq-title">A clear next step.</h2><div>
<details><summary>Can I talk with {esc(name)} before choosing?</summary><p>Yes. Share your goal in the short intake, then continue to {esc(name)}’s call-booking page. <a href="{talk}" target="_top">Start the conversation</a>.</p></details>
<details><summary>Where can I review the training options?</summary><p>Available enrollment options will appear here with their pricing and details. You can also talk with {esc(name)} about your goal and the options that may suit you.</p></details>
</div></div></section>
</main><footer class="stg-footer"><div class="stg-shell stg-footer-inner"><div class="stg-purchase-footer-brand"><img class="stg-footer-badge" src="{badge_uri}" alt="Strikeline Training Group"><p>BEAUFORT, SOUTH CAROLINA</p></div><div class="stg-footer-links"><a href="https://strikelinetraining.com/privacy-policy" target="_top">Privacy</a><a href="https://strikelinetraining.com/terms-and-conditions" target="_top">Terms</a><a href="mailto:info@strikelinetraining.com">Contact</a></div></div></footer>
</div>'''


def build_purchase_pages(root, coaches, embedded_fonts, shared_css, logo_svg):
    """Write three standalone purchase pages and three self-contained HTML blocks.

    Returns their relative paths. Only owner-provided local embed HTML, if any,
    is inserted; when absent the pages display a pending enrollment message.
    All original JPEG and SVG bytes are preserved in their embedded data URLs.
    """
    root = Path(root)
    svg_root = ET.fromstring(logo_svg)
    if svg_root.tag.split('}')[-1] != 'svg':
        raise ValueError('Purchase pages require the supplied SVG logo.')
    logo_uri = _data_uri('image/svg+xml', logo_svg.encode('utf-8'))
    badge_file = root / 'assets' / 'strikeline-badge-white.svg'
    badge_uri = _data_uri('image/svg+xml', badge_file.read_bytes()) if badge_file.is_file() else logo_uri
    purchase_css = (root / 'assets' / 'purchase.css').read_text(encoding='utf-8')
    (root / 'blocks').mkdir(exist_ok=True)
    outputs = []
    for coach in coaches:
        slug, name = coach['slug'], coach['name']
        if slug not in {'justin', 'zach', 'rhylie'}:
            raise ValueError('Unexpected coach slug: ' + slug)
        body = _markup(coach, logo_uri, _embed(root, slug), badge_uri)
        page = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="Explore training with {html.escape(coach['fullName'],quote=True)} at Strikeline."><meta name="color-scheme" content="dark"><title>Start training with {html.escape(name)} | Strikeline</title><link rel="stylesheet" href="assets/fonts.css"><link rel="stylesheet" href="assets/coach.css"><link rel="stylesheet" href="assets/purchase.css"><style>body{{margin:0;background:#101312}}</style></head><body>{body}</body></html>'''
        filename = 'start-' + slug + '.html'
        (root / filename).write_text(page, encoding='utf-8')
        image_uri = _data_uri('image/jpeg', (root / 'assets' / (slug + '.jpg')).read_bytes())
        embedded_body = body.replace('assets/' + slug + '.jpg', image_uri)
        block = ('<!-- Strikeline ' + name + ' purchase page. Paste once into a full-width HTML section. '
                 'Checkout remains pending until its approved embed is provided. Photos, fonts and SVG logo are embedded. -->\n'
                 + '<style>' + embedded_fonts + '\n' + shared_css + '\n' + purchase_css + '</style>\n'
                 + embedded_body + '\n')
        blockname = 'blocks/start-' + slug + '-copy-paste.html'
        (root / blockname).write_text(block, encoding='utf-8')
        outputs.extend([filename, blockname])
    return outputs

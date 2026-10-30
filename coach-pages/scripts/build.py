"""Generate standalone pages and self-contained HTML blocks. No image transformation."""
from pathlib import Path
import json, html, base64, re
from purchase_pages import build_purchase_pages

ROOT = Path(__file__).resolve().parents[1]
esc = html.escape

def markup(c):
    slug, name = c['slug'], c['name']
    intake = f'{slug}-intake'
    reasons = ''.join(f'<article class="stg-reason"><div class="stg-number">0{i+1}</div><h3>{esc(r["title"])}</h3><p>{esc(r["text"])}</p></article>' for i,r in enumerate(c['reasons']))
    faqs = ''.join(f'<details><summary>{esc(f["question"])}</summary><p>{esc(f["answer"])}</p></details>' for f in c['faqs'])
    opts = ''.join(f'<option value="{esc(g["value"],quote=True)}">{esc(g["label"])}</option>' for g in c['goals'])
    lines = ''.join(f'<span>{esc(line)}</span>' for line in c['heroLines'])
    photo = f'assets/{slug}.jpg'
    return f'''<div class="stg-coach-page" data-coach="{name}" style="--photo-position:{c['photoPosition']}">
<a class="stg-skip" href="#{intake}">Skip to the short form</a>
<main>
<section class="stg-hero" aria-labelledby="{slug}-title">
 <img class="stg-hero-photo" src="{photo}" alt="{esc(c['fullName'])} at Strikeline" fetchpriority="high" decoding="async" width="853" height="1280">
 <header class="stg-nav"><div class="stg-shell stg-nav-inner"><a class="stg-brand" href="https://strikelinetraining.com/" aria-label="Strikeline Training Group home"><img class="stg-brand-logo" data-brand-logo src="assets/strikeline-logo-white.svg" alt="Strikeline Training Group" width="200" height="50"></a><a class="stg-nav-call" href="#{intake}">Talk with {name} ↗</a></div></header>
 <div class="stg-shell stg-hero-content"><div class="stg-hero-copy"><p class="stg-kicker">{name} · {esc(c['specialty'])}</p><h1 id="{slug}-title">{lines}</h1><p class="stg-hero-description">{esc(c['subhead'])}</p><div class="stg-hero-actions"><a class="stg-button" data-purchase-link href="{esc(c['purchaseUrl'],quote=True)}" target="_top">I’m ready to start training</a><a class="stg-button stg-button-secondary" href="#{intake}">Book a call with {name}</a></div><p class="stg-helper">Ready to begin? Explore training options. Have questions? Let’s talk first.</p></div></div>
 <div class="stg-hero-bottom"><div class="stg-shell stg-hero-meta"><div><strong>{esc(c['fullName'])}</strong>Your next step starts with a conversation.</div><a href="#{slug}-approach">Get to know the approach ↓</a></div></div>
</section>
<section class="stg-intro" id="{slug}-approach" aria-labelledby="{slug}-approach-title"><div class="stg-shell"><div class="stg-section-heading"><p class="stg-kicker">A goal. A starting point. A next step.</p><h2 id="{slug}-approach-title">{esc(c['introHeading'])}</h2></div><div class="stg-reasons">{reasons}</div><div class="stg-ready-row"><div><p class="stg-kicker">Your next move</p><h3>Ready to train with {name}?</h3></div><a class="stg-button" data-purchase-link href="{esc(c['purchaseUrl'],quote=True)}" target="_top">I’m ready to start training</a></div></div></section>
<section class="stg-process" aria-label="How to book a call"><div class="stg-shell stg-process-inner"><p class="stg-kicker">Prefer to talk first?</p><div class="stg-process-step"><b>01</b><p><strong>Share your goal.</strong>A few details about you and what you want to work on.</p></div><div class="stg-process-step"><b>02</b><p><strong>Book your call.</strong>Choose a time on {name}’s booking page.</p></div><div class="stg-process-step"><b>03</b><p><strong>Talk through the fit.</strong>Discuss your starting point, options and next step.</p></div></div></section>
<section class="stg-intake" id="{intake}" aria-labelledby="{slug}-intake-title"><div class="stg-shell stg-intake-layout"><div class="stg-intake-heading"><p class="stg-kicker">Let’s talk about your goal</p><h2 id="{slug}-intake-title">{esc(c['closingHeading'])}</h2><p>{esc(c['closingText'])}</p><div class="stg-mini-portrait"><img src="{photo}" alt="" loading="lazy" width="68" height="78"><div><strong>{esc(c['fullName'])}</strong><span>{esc(c['specialty'])}</span></div></div></div>
<div class="stg-form-area"><form data-coach-intake action="https://formspree.io/f/mdajqedj" method="POST" aria-label="Short intake for {name}">
<input type="hidden" name="_subject" value="{name} — Coach landing page mini intake"><input type="hidden" name="coach" value="{name}"><input type="hidden" name="source" value="coach-landing-{slug}"><div hidden aria-hidden="true"><label>Leave this empty<input name="_gotcha" type="text" tabindex="-1" autocomplete="off"></label></div>
<div data-form-fields><h3 class="stg-form-title">Tell me what you want to work on.</h3><p class="stg-form-intro">Start with the basics. We’ll talk through the details on your call.</p><div class="stg-fields">
<div class="stg-field"><label for="{slug}-name">Your name</label><input id="{slug}-name" name="firstName" autocomplete="name" maxlength="160" placeholder="Your name" required></div>
<div class="stg-field"><label for="{slug}-email">Email</label><input id="{slug}-email" name="email" type="email" autocomplete="email" maxlength="254" placeholder="you@example.com" required></div>
<div class="stg-field stg-wide"><label for="{slug}-phone">Phone <small>Required</small></label><input id="{slug}-phone" name="phone" type="tel" autocomplete="tel" maxlength="40" placeholder="Your phone number" pattern=".*\\S.*" title="Enter your phone number." required></div>
<div class="stg-field stg-wide"><label for="{slug}-goal">What would you like help with?</label><select id="{slug}-goal" name="goal" required><option value="" disabled selected>Choose your focus</option>{opts}</select></div>
<div class="stg-field stg-wide"><label for="{slug}-notes">Anything you’d like me to know? <small>Optional</small></label><textarea id="{slug}-notes" name="goalNotes" maxlength="1200" placeholder="Your goal, experience, or a question you want to ask."></textarea></div></div>
<p class="stg-form-note">Send these details to Strikeline about working with {name}. <a href="https://strikelinetraining.com/privacy-policy" target="_blank" rel="noopener">Privacy policy</a>.</p>
<button class="stg-button" type="submit">Continue to book with {name}</button>
<noscript><p class="stg-form-note">Your browser will open the form’s confirmation page after sending. Then <a href="{esc(c['bookingUrl'],quote=True)}" target="_blank" rel="noopener">book your call with {name}</a>.</p></noscript></div>
<p data-form-status role="status" aria-live="polite" aria-atomic="true"></p></form>
<div class="stg-success" data-intake-success hidden><div class="stg-kicker">Next: choose your time</div><h3 tabindex="-1">Your details are in.<br>Let’s find a time to talk.</h3><p>Finish by choosing a time on {name}’s booking page. Your call is confirmed when you complete that booking.</p><a class="stg-button" data-booking-link href="{esc(c['bookingUrl'],quote=True)}" target="_blank" rel="noopener">Book a call with {name}</a></div></div></div></section>
<section class="stg-faqs" aria-labelledby="{slug}-faq-title"><div class="stg-shell stg-faq-layout"><h2 id="{slug}-faq-title">Before we talk.</h2><div>{faqs}</div></div></section>
</main><footer class="stg-footer"><div class="stg-shell stg-footer-inner"><div class="stg-footer-brand"><img class="stg-footer-badge" src="assets/strikeline-badge-white.svg" alt="Strikeline Training Group" width="90" height="65"><p>BEAUFORT, SOUTH CAROLINA</p></div><div class="stg-footer-links"><a href="https://strikelinetraining.com/privacy-policy">Privacy</a><a href="https://strikelinetraining.com/terms-and-conditions">Terms</a><a href="mailto:info@strikelinetraining.com">Contact</a></div></div></footer>
<div class="stg-sticky" data-sticky-cta><a class="stg-button" data-purchase-link href="{esc(c['purchaseUrl'],quote=True)}" target="_top">I’m ready to start training</a><a class="stg-sticky-call" href="#{intake}">Prefer to talk? Book a call with {name}</a></div>
</div>'''

def build():
    coaches = json.loads((ROOT/'coaches.json').read_text())
    css = (ROOT/'assets/coach.css').read_text()
    js = (ROOT/'assets/intake.js').read_text()
    fonts = (ROOT/'assets/fonts.css').read_text()
    embedded_fonts = re.sub(r'url\(([^)]+)\)', lambda m:'url(data:font/ttf;base64,'+base64.b64encode((ROOT/'assets'/m[1]).read_bytes()).decode()+')', fonts)
    for c in coaches:
        body = markup(c)
        page = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="{esc(c['subhead'],quote=True)}"><meta name="color-scheme" content="dark"><title>Train with {c['name']} | Strikeline</title><link rel="stylesheet" href="assets/fonts.css"><link rel="stylesheet" href="assets/coach.css"><style>body{{margin:0;background:#101312}}html{{scroll-behavior:smooth}}@media(prefers-reduced-motion:reduce){{html{{scroll-behavior:auto}}}}</style></head><body>{body}<script src="assets/intake.js" defer></script></body></html>'''
        (ROOT/(c['slug']+'.html')).write_text(page)
        image = 'data:image/jpeg;base64,'+base64.b64encode((ROOT/'assets'/(c['slug']+'.jpg')).read_bytes()).decode()
        body = body.replace('assets/'+c['slug']+'.jpg',image)
        for logo in ['strikeline-logo-white.svg','strikeline-badge-white.svg']:
            body = body.replace('assets/'+logo, 'data:image/svg+xml;base64,'+base64.b64encode((ROOT/'assets'/logo).read_bytes()).decode())
        block = '<!-- Strikeline '+c['name']+' landing page. Paste once into a full-width HTML block. Photos and fonts are embedded. Form submits to the existing live mini-intake endpoint. -->\n<style>'+embedded_fonts+'\n'+css+'</style>\n'+body+'\n<script>'+js+'</script>\n'
        (ROOT/'blocks'/(c['slug']+'-copy-paste.html')).write_text(block)
    build_purchase_pages(ROOT, coaches, embedded_fonts, css, (ROOT/'assets/strikeline-logo-white.svg').read_text())
    cards = ''.join(f'<a href="{c["slug"]}.html"><img src="assets/{c["slug"]}.jpg" alt="{c["name"]}"><span>{c["name"]}<small>{esc(c["specialty"])}</small></span></a>' for c in coaches)
    (ROOT/'index.html').write_text('''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Coach landing page review | Strikeline</title><link rel="stylesheet" href="assets/fonts.css"><style>body{margin:0;background:#101312;color:#f1eee6;font-family:Manrope,sans-serif;padding:6vw}h1{font:700 clamp(44px,6vw,90px)/1 'Barlow Condensed';text-transform:uppercase;margin:20px 0}p{color:#b8b9b0;line-height:1.8;max-width:750px}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:24px;margin-top:40px}a{color:inherit;text-decoration:none}img{width:100%;height:420px;object-fit:cover;object-position:50% 20%}span{display:block;font:700 40px 'Barlow Condensed';text-transform:uppercase;margin-top:16px}small{display:block;font:12px Manrope;text-transform:none;margin-top:6px}a:focus-visible{outline:3px solid #f4793d;outline-offset:5px}@media(max-width:700px){.grid{grid-template-columns:1fr}img{height:380px}}</style><p>STRIKELINE / COACH PAGE REVIEW</p><h1>Three coaches.<br>Three ways to start.</h1><p>Choose a coach to review the landing page and its separate purchase page. Purchase options open Stripe checkout. Mini-intake forms use the existing endpoint; automated checks intercept submissions.</p><div class="grid">'''+cards+'</div></html>')
    print('Generated three landing pages, three purchase pages, six self-contained blocks and review index.')

if __name__ == '__main__':
    build()

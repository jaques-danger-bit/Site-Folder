"""Build comparison-first coach purchase pages from verified offers.json data.

Does not create products, payments or subscriptions. The pending design's
optional external-HTML mechanism is retired; only configured public IDs are used.
"""
from pathlib import Path
import base64
import html
import json
import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
import xml.etree.ElementTree as ET


def _data_uri(mime, content):
    return 'data:' + mime + ';base64,' + base64.b64encode(content).decode('ascii')


def _load_offers(root):
    data = json.loads((root / 'offers.json').read_text(encoding='utf-8'))
    if data.get('currency') != 'USD':
        raise ValueError('Purchase pages format verified USD offers only.')
    if not re.fullmatch(r'pk_(?:live|test)_[A-Za-z0-9]+', data.get('publishableKey', '')):
        raise ValueError('A valid Stripe publishable key is required.')
    offers, seen = data.get('offers', []), set()
    if not offers:
        raise ValueError('At least one verified offer is required.')
    for offer in offers:
        slug = offer.get('slug', '')
        if not re.fullmatch(r'[a-z][a-z0-9_]*', slug) or slug in seen:
            raise ValueError('Offer slugs must be unique lowercase identifiers.')
        seen.add(slug)
        if offer.get('checkoutReady'):
            if not re.fullmatch(r'buy_btn_[A-Za-z0-9]+', offer.get('buttonId', '')):
                raise ValueError('Ready offer requires its verified Stripe Buy Button ID.')
            url = urlsplit(offer.get('checkoutUrl', ''))
            if url.scheme != 'https' or url.netloc != 'buy.stripe.com' or not url.path.strip('/'):
                raise ValueError('Checkout fallback must be a verified Stripe payment link.')
        amount = offer.get('amount')
        if isinstance(amount, bool) or not isinstance(amount, (int, float)) or amount <= 0:
            raise ValueError('Offer price must be a positive verified amount.')
        for field in ('name', 'badge', 'cadence', 'billing', 'fit', 'promise', 'description', 'terms', 'cta'):
            if not isinstance(offer.get(field), str) or not offer[field].strip():
                raise ValueError('Missing verified offer field: ' + field)
        if not isinstance(offer.get('features'), list) or not all(isinstance(item, str) and item for item in offer['features']):
            raise ValueError('Offer features must be a list of verified descriptions.')
    return data


def _price(amount):
    return '$' + (f'{amount:,.0f}' if amount == int(amount) else f'{amount:,.2f}')


def _checkout_url(url, reference):
    parts = urlsplit(url)
    query = [(key, value) for key, value in parse_qsl(parts.query, keep_blank_values=True) if key != 'client_reference_id']
    query.append(('client_reference_id', reference))
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def _offer_card(offer, coach_slug):
    esc = html.escape
    slug = offer['slug']
    ready = offer.get('checkoutReady', False)
    reference = f'stg_{coach_slug}_{slug}'
    checkout = _checkout_url(offer['checkoutUrl'], reference) if ready else f'{coach_slug}.html#{coach_slug}-intake'
    action_attrs = f'data-open-checkout="{slug}" aria-haspopup="dialog"' if ready else 'data-program-conversation'
    featured = ' stg-offer-featured' if offer.get('featured') else ''
    descriptions = {
        'assessment': 'Nutrition + training review.',
        'online': 'Custom training, check-ins + nutrition.',
        'inperson': 'Full programming + 1 session/week in Beaufort.',
    }
    terms = {
        'assessment': 'Ongoing coaching sold separately.',
        'online': '',
        'inperson': '30-day cancellation notice required.',
    }
    description = descriptions.get(slug, offer['description'])
    term = terms.get(slug, offer['terms'])
    term_markup = '<p class="stg-offer-terms">' + esc(term) + '</p>' if term else ''
    return f'''<article class="stg-offer{featured}" data-offer-id="{slug}" aria-labelledby="{coach_slug}-{slug}-title">
<h3 id="{coach_slug}-{slug}-title">{esc(offer['name'])}</h3>
<p class="stg-offer-price"><strong>{_price(offer['amount'])}</strong><span>USD · {esc(offer['cadence'])}</span></p>
<p class="stg-offer-description">{esc(description)}</p>{term_markup}
<a class="stg-button" {action_attrs} href="{esc(checkout, quote=True)}" target="_top" aria-label="Choose {esc(offer['name'], quote=True)}">Choose</a>
</article>'''


def _markup(coach, logo_uri, offers_data, badge_uri):
    esc = html.escape
    slug, name = coach['slug'], coach['name']
    back = slug + '.html'
    talk = back + '#' + slug + '-intake'
    offers = offers_data['offers']
    cards = ''.join(_offer_card(offer, slug) for offer in offers)
    config = {
        'coach': slug, 'publishableKey': offers_data['publishableKey'],
        'offers': [{
            'slug': offer['slug'], 'name': offer['name'], 'stripeProductName': offer['stripeProductName'],
            'price': _price(offer['amount']), 'cadence': offer['cadence'], 'terms': offer['terms'],
            'buttonId': offer['buttonId'], 'reference': f"stg_{slug}_{offer['slug']}",
            'checkoutUrl': _checkout_url(offer['checkoutUrl'], f"stg_{slug}_{offer['slug']}")
        } for offer in offers if offer.get('checkoutReady')]
    }
    config_json = json.dumps(config, ensure_ascii=False).replace('<', '\\u003c')
    dialog = ''
    if config['offers']:
        first = config['offers'][0]
        dialog = f'''<dialog class="stg-checkout-dialog" data-checkout-dialog aria-labelledby="{slug}-checkout-title" aria-describedby="{slug}-checkout-details"><button type="button" class="stg-checkout-close" data-checkout-close aria-label="Close checkout">×</button><h2 id="{slug}-checkout-title" data-checkout-title>{esc(first['name'])}</h2><p class="stg-checkout-details" id="{slug}-checkout-details" data-checkout-details>{esc(first['price'] + ' ' + first['cadence'])}</p><p class="stg-checkout-terms" data-checkout-terms>{esc(first['terms'])}</p><p class="stg-checkout-status" data-checkout-status role="status" aria-live="polite"></p><div class="stg-stripe-mount" data-purchase-embed="{slug}"></div><a class="stg-checkout-fallback" data-checkout-fallback href="{esc(first['checkoutUrl'], quote=True)}" target="_top">Open secure checkout directly</a><p class="stg-checkout-note">Payments are handled by Stripe.</p></dialog>'''
    return f'''<div class="stg-coach-page stg-purchase-page" data-coach="{esc(name)}" data-purchase-page="{slug}">
<a class="stg-skip" href="#{slug}-enrollment">Skip to training options</a>
<header class="stg-purchase-header"><div class="stg-shell stg-purchase-header-inner"><a class="stg-brand" href="{back}" target="_top" aria-label="Back to {esc(name)}"><img class="stg-brand-logo" data-brand-logo src="{logo_uri}" alt="Strikeline Training Group"></a><nav class="stg-purchase-links" aria-label="Coach navigation"><a href="{back}" target="_top">Back to {esc(name)}</a></nav></div></header>
<main class="stg-purchase-main">
<section class="stg-enrollment" id="{slug}-enrollment" aria-labelledby="{slug}-enrollment-title"><div class="stg-shell">
<h1 class="stg-purchase-title" id="{slug}-enrollment-title">Train with {esc(name)}</h1>
<div class="stg-offers" style="--offer-count:{min(len(offers), 3)}">{cards}</div>
</div></section>
</main><footer class="stg-purchase-footer"><div class="stg-shell stg-purchase-footer-inner"><a class="stg-purchase-talk-link" href="{talk}" target="_top">Talk with {esc(name)}</a><div class="stg-purchase-legal"><a href="https://strikelinetraining.com/privacy-policy" target="_top">Privacy</a><a href="https://strikelinetraining.com/terms-and-conditions" target="_top">Terms</a></div></div></footer>
{dialog}<script type="application/json" data-purchase-config>{config_json}</script>
</div>'''


def build_purchase_pages(root, coaches, embedded_fonts, shared_css, logo_svg):
    """Write three purchase pages and self-contained blocks from verified offers."""
    root = Path(root)
    svg_root = ET.fromstring(logo_svg)
    if svg_root.tag.split('}')[-1] != 'svg':
        raise ValueError('Purchase pages require the supplied SVG logo.')
    logo_uri = _data_uri('image/svg+xml', logo_svg.encode('utf-8'))
    badge_file = root / 'assets' / 'strikeline-badge-white.svg'
    badge_uri = _data_uri('image/svg+xml', badge_file.read_bytes()) if badge_file.is_file() else logo_uri
    purchase_css = (root / 'assets' / 'purchase.css').read_text(encoding='utf-8')
    purchase_js = (root / 'assets' / 'purchase.js').read_text(encoding='utf-8')
    offers_data = _load_offers(root)
    (root / 'blocks').mkdir(exist_ok=True)
    outputs = []
    for coach in coaches:
        slug, name = coach['slug'], coach['name']
        if slug not in {'justin', 'zach', 'rhylie'}:
            raise ValueError('Unexpected coach slug: ' + slug)
        body = _markup(coach, logo_uri, offers_data, badge_uri)
        page = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="Choose training and coaching support with {html.escape(coach['fullName'],quote=True)} at Strikeline. View pricing and enroll securely with Stripe."><meta name="color-scheme" content="dark"><title>Start training with {html.escape(name)} | Strikeline</title><link rel="stylesheet" href="assets/fonts.css"><link rel="stylesheet" href="assets/coach.css"><link rel="stylesheet" href="assets/purchase.css"><style>body{{margin:0;background:#101312}}</style></head><body>{body}<script src="assets/purchase.js"></script></body></html>'''
        filename = 'start-' + slug + '.html'
        (root / filename).write_text(page, encoding='utf-8')
        block = ('<!-- Strikeline ' + name + ' purchase page. Paste once into a full-width HTML section. Fonts and actual SVG logos are embedded. Stripe loads once when a ready option is chosen. -->\n'
                 + '<style>' + embedded_fonts + '\n' + shared_css + '\n' + purchase_css + '</style>\n'
                 + body + '\n<script>' + purchase_js + '</script>\n')
        blockname = 'blocks/start-' + slug + '-copy-paste.html'
        (root / blockname).write_text(block, encoding='utf-8')
        outputs.extend([filename, blockname])
    return outputs

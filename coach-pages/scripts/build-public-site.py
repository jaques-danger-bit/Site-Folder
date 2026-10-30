"""Package only approved customer-facing pages/assets for a separate public site.

Run from any directory. Generates coach-pages/publish (ignored) and an audit
manifest under evidence. Does not deploy, submit forms, or change source pages.
"""
from datetime import datetime, timezone
from hashlib import sha256
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
import json
import re
import shutil
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'publish'
COACHES = ('justin', 'zach', 'rhylie')
ASSETS = (
    'justin.jpg', 'zach.jpg', 'rhylie.jpg',
    'strikeline-logo-white.svg', 'strikeline-badge-white.svg',
    'barlow-condensed-bold.ttf', 'manrope-regular.ttf', 'manrope-bold.ttf',
    'barlowcondensed-OFL.txt', 'manrope-OFL.txt',
    'fonts.css', 'coach.css', 'intake.js', 'purchase.css', 'purchase.js',
)
ROUTES = {f'{slug}.html': f'{slug}/index.html' for slug in COACHES}
ROUTES.update({f'start-{slug}.html': f'{slug}/start/index.html' for slug in COACHES})


def rewrite_url(value):
    if value == 'https://strikelinetraining.com/':
        return '/'
    if value.startswith('assets/'):
        return '/' + value
    path = re.split(r'[?#]', value, maxsplit=1)[0]
    if path in ROUTES:
        clean = '/' + ROUTES[path].removesuffix('index.html')
        return clean + value[len(path):]
    return value


def rewrite_html(text):
    return re.sub(r'\b(href|src)=("|\')(.*?)\2',
                  lambda match: match[1] + '=' + match[2] + rewrite_url(match[3]) + match[2],
                  text, flags=re.S)


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []
        self.ids = set()
    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if data.get('id'):
            self.ids.add(data['id'])
        for name in ('href', 'src', 'action'):
            if data.get(name):
                self.urls.append((tag, name, data[name]))


def verify_package():
    expected = {'index.html', '_redirects'} | set(ROUTES.values()) | {'assets/' + name for name in ASSETS}
    found = {path.relative_to(DEST).as_posix() for path in DEST.rglob('*') if path.is_file()}
    if found != expected:
        raise ValueError(f'Public allowlist mismatch. Extra: {found-expected}; missing: {expected-found}')
    pages = {}
    for name in sorted(path for path in found if path.endswith('.html')):
        parser = Links()
        parser.feed((DEST / name).read_text())
        pages[name] = parser
    external = set()
    for name, page in pages.items():
        for tag, attr, raw in page.urls:
            url = urlsplit(unescape(raw))
            if url.scheme or url.netloc:
                if url.scheme != 'data':
                    external.add(url.netloc or url.scheme)
                continue
            path = url.path
            target = DEST / (path.lstrip('/') if path.startswith('/') else str(Path(name).parent / path)) if path else DEST / name
            if target.is_dir():
                target = target / 'index.html'
            if not target.is_file():
                raise ValueError(f'Broken public {attr} in {name}: {raw}')
            if url.fragment and target.suffix == '.html':
                relative = target.relative_to(DEST).as_posix()
                if url.fragment not in pages[relative].ids:
                    raise ValueError(f'Broken public anchor in {name}: {raw}')
    for path in DEST.rglob('*'):
        if path.is_file() and path.suffix in {'.html', '.css', '.js', '.svg'}:
            if b'stgportal.netlify.app' in path.read_bytes().lower():
                raise ValueError(f'Internal portal reference in {path.relative_to(DEST)}')
    return sorted(found), sorted(external)


def build():
    if DEST.is_symlink() or DEST.resolve().parent != ROOT.resolve():
        raise ValueError('Refusing unexpected publish directory.')
    if DEST.exists():
        shutil.rmtree(DEST)
    (DEST / 'assets').mkdir(parents=True)
    source_hashes = {}
    for name in ASSETS:
        source = ROOT / 'assets' / name
        shutil.copyfile(source, DEST / 'assets' / name)
        source_hashes['assets/' + name] = sha256(source.read_bytes()).hexdigest()
    selector = ROOT / 'public' / 'index.html'
    shutil.copyfile(selector, DEST / 'index.html')
    source_hashes['public/index.html'] = sha256(selector.read_bytes()).hexdigest()
    for source_name, output_name in ROUTES.items():
        source = ROOT / source_name
        target = DEST / output_name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(rewrite_html(source.read_text(encoding='utf-8')), encoding='utf-8')
        source_hashes[source_name] = sha256(source.read_bytes()).hexdigest()
    redirects = []
    for source_name, output_name in ROUTES.items():
        clean = '/' + output_name.removesuffix('index.html')
        redirects.extend([f'/{source_name} {clean} 301', f'/coach-pages/{source_name} {clean} 301'])
    (DEST / '_redirects').write_text('\n'.join(redirects) + '\n')
    files, external = verify_package()
    manifest = {
        'builtAt': datetime.now(timezone.utc).isoformat(),
        'outputDirectory': str(DEST),
        'routes': ['/'] + ['/' + name.removesuffix('index.html') for name in ROUTES.values()],
        'sources': source_hashes,
        'files': [{'path': name, 'bytes': (DEST/name).stat().st_size, 'sha256': sha256((DEST/name).read_bytes()).hexdigest()} for name in files],
        'publicHostsOrSchemes': external,
        'checks': {'allowlistOnly': True, 'localLinksAndAnchorsResolve': True, 'noInternalPortalLinks': True,
                   'originalAssetsByteIdentical': all((ROOT/'assets'/name).read_bytes() == (DEST/'assets'/name).read_bytes() for name in ASSETS)},
        'behavior': {'formEndpointUnchanged': 'https://formspree.io/f/mdajqedj',
                     'publicBookingCalendarPreserved': 'training.strikelinetraining.com/a/booking/',
                     'legacyRedirectStatus': 301, 'noSpaCatchall': True},
    }
    (ROOT / 'evidence').mkdir(exist_ok=True)
    report = ROOT / 'evidence' / 'public-site-manifest.json'
    report.write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({'output': str(DEST), 'files': len(files), 'bytes': sum(item['bytes'] for item in manifest['files']), 'manifest': str(report)}, indent=2))


if __name__ == '__main__':
    build()

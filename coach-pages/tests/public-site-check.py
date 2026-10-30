#!/usr/bin/env python3
"""Bounded, GET-only audit of the independently hosted customer package.

Only the supplied site's origin is contacted. No page scripts execute; forms,
Stripe, booking calendars and the internal portal are never requested.
"""
import argparse
import base64
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import parse_qs, unquote, urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

ROOT = Path(__file__).resolve().parents[1]
PUBLISH = ROOT / "publish"
COACHES = {"justin":"3017439", "zach":"3017453", "rhylie":"3065290"}
ASSETS = {"justin.jpg","zach.jpg","rhylie.jpg","strikeline-logo-white.svg","strikeline-badge-white.svg",
          "barlow-condensed-bold.ttf","manrope-regular.ttf","manrope-bold.ttf","barlowcondensed-OFL.txt",
          "manrope-OFL.txt","fonts.css","coach.css","intake.js","purchase.css","purchase.js"}
OFFERS = {"assessment":"buy_btn_1UWFCARzFn0Z1SgZqB6Sx8fi", "online":"buy_btn_1UWFDHRzFn0Z1SgZci4LXSUf",
          "inperson":"buy_btn_1UWFE2RzFn0Z1SgZvpUqdxYp"}
STRIPE_PATHS = {"assessment":"/fZueVf0L480x3sPdAfgQE2z", "online":"/fZucN70L4fsZgfB0NtgQE2A", "inperson":"/dRmcN765o94B5AXao3gQE2B"}
LOGO_HASHES = {"strikeline-logo-white.svg":"98dcd4a09c49f5d2040ec709c5a8eefa8b2fce086ade2d62ac4c81cdbc1ae212",
               "strikeline-badge-white.svg":"ddd49927c9b1aa7bc1b41840fe7b37bf3f4683808802349434af42714f78a7fd"}
FORBIDDEN = "stgportal.netlify.app"
ENDPOINT = "https://formspree.io/f/mdajqedj"


class Page(HTMLParser):
    def __init__(self, raw):
        super().__init__()
        self.nodes, self.links, self.ids, self.config = [], [], set(), None
        self.stack, self.hero_actions = [], []
        self.script_config = False
        self.config_text = ""
        self.feed(raw.decode())
    def handle_starttag(self, tag, attrs):
        node = dict(attrs)
        self.nodes.append((tag,node))
        if tag == "a" and any("stg-hero-actions" in parent.get("class", "").split() for _,parent in self.stack):
            self.hero_actions.append(node)
        if node.get("id"):
            self.ids.add(node["id"])
        for key in ("href","src","action"):
            if node.get(key):
                self.links.append((tag,key,node[key]))
        if tag == "script" and "data-purchase-config" in node:
            self.script_config = True
        if tag not in {"area","base","br","col","embed","hr","img","input","link","meta","param","source","track","wbr"}:
            self.stack.append((tag,node))
    def handle_data(self, data):
        if self.script_config:
            self.config_text += data
    def handle_endtag(self, tag):
        if tag == "script" and self.script_config:
            self.script_config = False
            self.config = json.loads(self.config_text)
        for index in range(len(self.stack)-1,-1,-1):
            if self.stack[index][0] == tag:
                self.stack = self.stack[:index]
                break
    def matching(self, tag, attribute):
        return [node for name,node in self.nodes if name == tag and attribute in node]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def static_check():
    routes = {"/":"index.html"}
    for coach in COACHES:
        routes[f"/{coach}/"] = f"{coach}/index.html"
        routes[f"/{coach}/start/"] = f"{coach}/start/index.html"
    expected = set(routes.values()) | {"assets/"+name for name in ASSETS} | {"_redirects"}
    actual = {p.relative_to(PUBLISH).as_posix() for p in PUBLISH.rglob("*") if p.is_file()}
    assert actual == expected, {"extra":sorted(actual-expected),"missing":sorted(expected-actual)}
    assert not any(p.is_symlink() for p in PUBLISH.rglob("*")), "Publish symlink found"
    pages = {route:Page((PUBLISH/name).read_bytes()) for route,name in routes.items()}
    source_dir = Path("/home/jaquesdanger/Strikeline-data/coach-social-personas/2026-10-30/sources")
    for name in ASSETS:
        assert (PUBLISH/"assets"/name).read_bytes() == (ROOT/"assets"/name).read_bytes(), name
    for coach in COACHES:
        assert (PUBLISH/"assets"/(coach+".jpg")).read_bytes() == (source_dir/(coach.title()+"-highlight-source-photo.jpg")).read_bytes()
    for name,digest in LOGO_HASHES.items():
        assert sha((PUBLISH/"assets"/name).read_bytes()) == digest, name
    external = set()
    link_count = 0
    for route,page in pages.items():
        raw = (PUBLISH/routes[route]).read_text()
        assert FORBIDDEN not in unquote(raw).lower()
        for tag,attribute,raw_url in page.links:
            url = urlsplit(raw_url)
            if url.scheme == "data":
                if raw_url.startswith("data:image/svg+xml;base64,"):
                    assert sha(base64.b64decode(raw_url.split(",",1)[1])) in LOGO_HASHES.values()
                continue
            assert url.scheme in {"","https","mailto"}, raw_url
            if url.netloc:
                assert url.hostname in {"strikelinetraining.com","training.strikelinetraining.com","formspree.io","buy.stripe.com"}, raw_url
                external.add(url.hostname)
                if url.hostname == "strikelinetraining.com":
                    assert url.path in {"/privacy-policy","/terms-and-conditions"}, raw_url
                continue
            if url.scheme == "mailto":
                continue
            resolved = urlsplit(urljoin("https://audit.invalid"+route,raw_url))
            target = resolved.path.lstrip("/")
            if not target or target.endswith("/"):
                target += "index.html"
            assert target in actual, (route,raw_url,target)
            if resolved.fragment:
                target_route = "/"+target.removesuffix("index.html")
                assert resolved.fragment in pages[target_route].ids, (route,raw_url)
            link_count += 1
        for node in page.matching("a","aria-label"):
            if node.get("aria-label") == "Strikeline Training Group home":
                assert node["href"] == "/"
    for coach,staff in COACHES.items():
        page = pages[f"/{coach}/"]
        assert len(page.hero_actions) == 2, "Landing must have exactly two hero actions"
        assert {node["href"] for node in page.hero_actions} == {f"/{coach}/start/",f"#{coach}-intake"}
        forbidden_classes = {"stg-intro","stg-process","stg-faq","stg-faqs","stg-sticky"}
        assert not any(forbidden_classes.intersection(node.get("class", "").split()) for _,node in page.nodes)
        assert len(page.matching("dialog","data-intake-dialog")) == 1
        forms = page.matching("form","data-coach-intake")
        assert len(forms) == 1 and forms[0]["action"] == ENDPOINT and forms[0]["method"].upper() == "POST"
        phones = [n for tag,n in page.nodes if tag == "input" and n.get("name") == "phone"]
        assert len(phones) == 1 and "required" in phones[0] and phones[0]["pattern"] == r".*\S.*"
        purchase_links = page.matching("a","data-purchase-link")
        assert len(purchase_links) == 1
        for node in purchase_links:
            assert node["href"] == f"/{coach}/start/"
        booking = page.matching("a","data-booking-link")
        assert len(booking) == 1
        target = urlsplit(booking[0]["href"])
        assert target.hostname == "training.strikelinetraining.com" and target.path == "/a/booking/"
        query = parse_qs(target.query)
        assert query["staffId"] == [staff] and query["serviceId"] == ["38920"]
        purchase = pages[f"/{coach}/start/"]
        assert not any("stg-hero" in node.get("class", "").split() for _,node in purchase.nodes)
        assert not any(tag == "details" for tag,_ in purchase.nodes), "Extra purchase FAQ remains"
        assert purchase.config["coach"] == coach
        offers = {offer["slug"]:offer for offer in purchase.config["offers"]}
        assert set(offers) == set(OFFERS)
        actions = {n["data-open-checkout"]:n for n in purchase.matching("a","data-open-checkout")}
        assert set(actions) == set(OFFERS)
        for service,button_id in OFFERS.items():
            offer = offers[service]
            assert offer["buttonId"] == button_id and offer["reference"] == f"stg_{coach}_{service}"
            target = urlsplit(actions[service]["href"])
            assert target.hostname == "buy.stripe.com" and target.path == STRIPE_PATHS[service]
            assert parse_qs(target.query)["client_reference_id"] == [f"stg_{coach}_{service}"]
        assert any(n.get("href") == f"/{coach}/#{coach}-intake" for tag,n in purchase.nodes if tag == "a")
    redirects = []
    for line in (PUBLISH/"_redirects").read_text().splitlines():
        old,new,status = line.split()
        assert status == "301" and new in routes and old.startswith("/")
        assert "*" not in line and FORBIDDEN not in line
        redirects.append((old,new))
    assert len(redirects) == 12
    for path in actual:
        if Path(path).suffix in {".html",".js",".css",".svg"} or path == "_redirects":
            assert FORBIDDEN.encode() not in (PUBLISH/path).read_bytes().lower(), path
    return routes, redirects, {"publish_file_count":len(actual),"local_links_checked":link_count,
                              "original_assets_preserved":15,"required_phone_pages":3,"matching_booking_routes":3,
                              "minimal_landing_shapes":3,"pricing_without_hero":3,
                              "attributed_stripe_options":9,"external_link_hosts":sorted(external),
                              "internal_portal_references":0,"legacy_rules":len(redirects)}


def fetch(base, path):
    history = []
    origin = urlsplit(base)
    class SameOriginRedirect(HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            target = urlsplit(newurl)
            assert (target.scheme,target.netloc) == (origin.scheme,origin.netloc), "Blocked cross-origin redirect: "+newurl
            history.append({"status":code,"destination":newurl})
            return super().redirect_request(req,fp,code,msg,headers,newurl)
    request = Request(base.rstrip("/")+path,headers={"User-Agent":"StrikelinePublicPageAudit/1.0","Accept-Encoding":"identity"},method="GET")
    opener = build_opener(SameOriginRedirect())
    try:
        response = opener.open(request,timeout=30)
    except HTTPError as error:
        response = error
    with response:
        return {"path":path,"status":response.status,"url":response.geturl(),"body":response.read(),"redirects":history}


def run(base, output):
    routes,redirects,static = static_check()
    is_local = urlsplit(base).hostname in {"127.0.0.1","localhost"}
    targets = dict(routes)
    targets.update({"/assets/"+name:"assets/"+name for name in ASSETS})
    with ThreadPoolExecutor(max_workers=6) as pool:
        responses = list(pool.map(lambda path:fetch(base,path),targets))
    checks = []
    for response in responses:
        path = response["path"]
        assert response["status"] == 200, (path,response["status"])
        assert response["body"] == (PUBLISH/targets[path]).read_bytes(), "Hosted bytes differ: "+path
        checks.append({"path":path,"status":response["status"],"sha256":sha(response["body"]),"matches_package":True})
    denied = ["/coaches.json","/offers.json","/evidence/intake-tests.json","/scripts/build.py",
              "/tests/intake-check.py","/blocks/justin-copy-paste.html","/.env","/.git/config"]
    denied_checks = []
    for path in denied:
        response = fetch(base,path)
        assert response["status"] == 404, ("Excluded path was not404",path,response["status"])
        denied_checks.append({"path":path,"status":404})
    redirect_checks = []
    if not is_local:
        for old,new in redirects:
            response = fetch(base,old+"?utm_source=link_audit&utm_medium=qa")
            assert response["status"] == 200 and response["redirects"]
            assert response["redirects"][0]["status"] == 301
            final = urlsplit(response["url"])
            assert final.path == new and parse_qs(final.query) == {"utm_source":["link_audit"],"utm_medium":["qa"]}
            assert response["body"] == (PUBLISH/routes[new]).read_bytes()
            redirect_checks.append({"from":old,"to":new,"status":301,"utm_preserved":True})
    receipt = {"status":"passed","checked_at_utc":datetime.now(timezone.utc).isoformat(),"base_url":base,
               "static":static,"http_checks":checks,"excluded_path_checks":denied_checks,"redirect_checks":redirect_checks,
               "live_mutations":0,"external_service_requests":0,
               "scope":"GET-only checks to this origin. No page scripts, forms, bookings, Stripe checkout or internal portal requested. Public calendar hrefs retained; legal links to the main public website are allowed. Local Python server does not apply Netlify redirects; redirect HTTP checks run on live hosting only."}
    output.write_text(json.dumps(receipt,indent=2)+"\n")
    print(json.dumps({"status":"passed","base":base,"package_files":static["publish_file_count"],
                      "matching_http_files":len(checks),"excluded_404_paths":len(denied_checks),
                      "legacy_redirects":len(redirect_checks),"live_mutations":0,"evidence":str(output)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url",required=True)
    parser.add_argument("--evidence",required=True,type=Path)
    args = parser.parse_args()
    run(args.base_url,args.evidence)

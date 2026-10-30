# Coach landing pages

Latest user decision, October 30, 2026: **use the original screenshot hero from commit `967e407` and rework the existing page.** That hero is the fixed visual and copy reference. Restore its full descriptive paragraphs, header Talk link, specialty label, original typography, left-aligned buttons, photo gradients/crops and footer name. The normal-height mobile headline is 48px; Justin's desktop photo retains its 13% horizontal shift and Rhylie's mobile photo retains its original transform. Targeted height overrides preserve viewport fit.

**Future changes must be the smallest change needed for the user's request. Do not rewrite approved copy or redesign the crop, font or layout without a new explicit direction.** Preserve the original reference while applying only necessary fit or functional fixes. Previously requested exclusions remain: no arrows, helper/approach filler or extra white pages/sections. The compact pricing pages and current dark intake remain unchanged. **I’m ready to start training** opens `/{coach}/start/`; **Book a call** opens the same-page intake. Phone stays required. The restoration was published as deploy `6ae4b72d98525fce2aaba2af` on October 30, 2026 at 15:26:39 UTC. Deploy `6ae4ae07bdc610bf593a3f50` is the preceding compact-hero revision.

## Review and use

- `index.html`: local review index.
- `justin.html`, `zach.html`, `rhylie.html`: hero-only coach landing pages with same-page intake dialogs.
- `start-justin.html`, `start-zach.html`, `start-rhylie.html`: separate purchase-page sources. Package them with `scripts/build-public-site.py`; do not publish the whole `coach-pages/` directory.
- `public/index.html`: customer-facing coach selector. `publish/`: ignored, allowlisted deployment output containing the selector, six routed pages, public assets and legacy redirects.
- `blocks/*-copy-paste.html`: six self-contained blocks: one landing block and one `start-{slug}-copy-paste.html` purchase block per coach. Landing blocks include the original supplied JPEG, SVG logos, fonts and intake behavior. Purchase blocks contain the dark pricing comparison, SVG logos, fonts and checkout behavior. Assets are embedded as data URLs with scoped styles. Paste one per full-width HTML/custom-code section that permits JavaScript. The host controls outer padding and iframe height. A restrictive host may strip inline scripts or data images, so check the actual host before publishing. No remote photo or logo URL is needed.
- `coaches.json`: approved coach copy, booking routes and `purchaseUrl`. `assets/landing.css`: restored hero styles scoped to `.stg-landing-page`; keep landing changes here so shared styles do not alter pricing. `assets/coach.css`: shared layout. `assets/intake.js`: shared form behavior. `offers.json`, `assets/purchase.css`, `assets/purchase.js` and `scripts/purchase_pages.py`: verified offers, purchase layout, selected-offer dialog and generation.
- `FUNNEL-NOTES.md`: the two-path flow, supplied Stripe offers, ManyChat plan and current integration limits.

`purchaseUrl` defaults to `start-{slug}.html` in the local source pages. The public packager rewrites these links to `/{slug}/start/`, return links to `/{slug}/`, assets to `/assets/`, with each coach’s logo/navigation staying in that coach’s two-page flow. Website-builder blocks retain their source-relative links; before using a block elsewhere, set its purchase and return links to the corresponding public URLs below. Purchase/return links use `target="_top"` so navigation can leave an iframe; the host must permit that navigation.

From the repository root, run `python3 -m http.server 8795 --bind 127.0.0.1` and open `http://127.0.0.1:8795/coach-pages/`. These pages point at a real intake endpoint. Automated checks intercept all external requests; previewing does not require submitting test leads.

Rebuild the pages and blocks with `python3 coach-pages/scripts/build.py`. The generator assembles all six pages and six blocks without transforming the portraits or SVG artwork. The original Dropbox logo assets are `strikeline-07.svg` and `strikeline-08.svg`; file paths and verified hashes are in `evidence/dropbox-logo-provenance.json`. Font licenses are in `assets/*-OFL.txt`.

## Separate public hosting

Reuse **https://strikeline-coaching.netlify.app**, Netlify site ID `d40f2639-dc6b-4a77-8d46-d297b2cc9b23`. The restored original hero was published as deploy `6ae4b72d98525fce2aaba2af` on October 30, 2026 at 15:26:39 UTC. The [deployment receipt](evidence/hosting-deploy.json) establishes publication; consult the matching [live byte/link checks](evidence/public-site-live-checks.json) for hosted verification, which is separate. Local restoration evidence is in `evidence/restored-hero-checks.json`. Historical receipts remain in `evidence/history/`; the marketing-site and internal-portal deployments stay separate.

| Page | Public route |
|---|---|
| Coach selector | https://strikeline-coaching.netlify.app/ |
| Justin | https://strikeline-coaching.netlify.app/justin/ |
| Justin’s training options | https://strikeline-coaching.netlify.app/justin/start/ |
| Zach | https://strikeline-coaching.netlify.app/zach/ |
| Zach’s training options | https://strikeline-coaching.netlify.app/zach/start/ |
| Rhylie | https://strikeline-coaching.netlify.app/rhylie/ |
| Rhylie’s training options | https://strikeline-coaching.netlify.app/rhylie/start/ |

Build from the repository root, then deploy only the generated public directory:

```sh
python3 coach-pages/scripts/build.py
python3 coach-pages/scripts/build-public-site.py
cd coach-pages
netlify deploy --prod --no-build --dir publish --site d40f2639-dc6b-4a77-8d46-d297b2cc9b23
```

The packager allows exactly 24 files: seven customer-facing HTML pages, 16 public assets including the scoped `landing.css` and font licenses, and `_redirects`. It excludes source configuration, copy-paste blocks, scripts, tests, research, evidence and documentation. It validates local links and anchors, rejects internal portal references, and preserves original asset bytes. `evidence/public-site-manifest.json` records source/output hashes and the file/route inventory. `publish/` and `.netlify/` are ignored. Do not deploy the repository root or all of `coach-pages/`.

Legacy `/{coach}.html`, `/start-{coach}.html` and matching `/coach-pages/` forms receive 301 redirects to the clean routes. There is no SPA catchall. The user explicitly retained the public `training.strikelinetraining.com/a/booking/` calendars; that public calendar remains the post-intake destination. Customer navigation has no internal-portal links. The existing Formspree action and required phone field remain unchanged. The origin-specific OPTIONS result in `evidence/hosting-form-preflight.json` checks CORS only; it does not prove lead acceptance, notifications or downstream import.

## Purchase redesign and supplied Stripe offers

The compact pricing page is unchanged by the hero restoration: three columns on desktop and three rows on mobile, with all choices visible in one viewport. A simple **Train with {coach}** header leads into each offer's name, price and cadence, concise factual description, material terms and **Choose** button. The footer contains only a Talk link and legal links. Do not reintroduce offer numbers, badges, divider lines, marketing headings or the bottom talk block. The original screenshot selection applies to the landing hero, not a new pricing redesign.

Each **Choose** button opens a native dialog with the actual Stripe Buy Button, loaded only for the selected offer through one shared loader. Keep the verified direct Stripe link visible as a fallback. The Talk link returns to the selected coach's intake dialog. The full-bleed photo hero appears only on the landing page.

Read-only public Stripe responses confirm **Online Coaching — Monthly: $350/month** and **Monthly Coaching — Foundation: $475/month**. Foundation includes full programming and one session/week, with 30-day cancellation notice. The user confirmed **Nutrition + Training Assessment: $175 one-time** as the entry offer. The public website's $175 Standalone Program with $30 updates is a different offer and is excluded from this three-offer checkout set. Do not transfer its update fee or the website contact form's 30-minute description to the paid assessment. Evidence and proposed copy: `evidence/services-20261030/RESEARCH-NOTES.md` and `offer-comparison.json`.

Use static `client-reference-id="stg_{coach}_{offer}"` for the selected coach/offer. This is a purchase reference, not proof of backend assignment or fulfillment. All three actual Stripe widgets rendered through read-only public GETs at desktop 1440px and mobile 320px (six views); `evidence/stripe-public-render.json` records the check. No payment was made. Stripe connector reauthentication was unavailable; no dashboard settings were changed and no deployed fulfillment webhook was verified. A bounded local portal-code read found a founders-only webhook that ignores other purchases and no function consuming `client_reference_id`; this is a local-code finding, not deployed-state evidence. Verify live coach assignment and fulfillment before relying on automated assignment or delivery. No automatic onboarding or delivery deadline is promised in the public copy.

The separate hosting audit did **not** verify Stripe’s post-payment destinations. `evidence/stripe-return-audit.json` found no configured completion URL in the accessible public responses or matching local link configuration. Absence of an internal-portal address in those responses does not prove where Stripe sends a buyer after payment. Its read-only browser filter also blocked Stripe’s POST initialization, so the resulting checkout-page error is not evidence that the payment links are broken. No purchase or account setting change was performed; post-payment routing and fulfillment remain separate checks.

## Existing mini intake

Verified public gateway: `https://formspree.io/f/mdajqedj`.

The secondary hero CTA opens the dark native intake dialog. Direct links use `/{coach}/#{coach}-intake`, such as `/rhylie/#rhylie-intake`. Without JavaScript, CSS `:target` displays the same intake and native form POST remains available. The form is not a white section below the hero. Closing it returns the visitor to the landing hero.

Source: [Site-Folder index.html at the reviewed commit](https://github.com/jaques-danger-bit/Site-Folder/blob/82a4326a25579020adc6c51022f4a5ebba4f54ba/index.html), form `applyForm`. The matching form was found in the site footer. A bounded search did not find a separate original mini-intake paste block. The newly supplied blocks adapt this verified form contract.

Preserved field names: `firstName`, `email`, `phone`, `goal`, `goalNotes`, `source`, `_subject`, `_gotcha`. Name, email, phone and goal are required. Phone rejects empty or whitespace-only input without imposing a country-specific format. Each page supplies a fixed `coach` and `source=coach-landing-{slug}`. Allowlisted UTM fields and an in-memory `submission_id` are added to the submitted payload. URL parameters cannot change the coach or booking route. In an iframe, campaign parameters must be present on the iframe URL; the block cannot automatically read a cross-origin parent page’s URL.

The existing backend imports Formspree → Google Sheet → hourly portal sync. The current portal import does not persist dedicated coach assignment or UTM fields and deduplicates by submission date plus email. These pages identify the coach in the submitted source, subject and coach field; they do not implement CRM assignment, immediate portal delivery, server idempotency or ManyChat. Confirm sheet column mappings and Formspree domain/notification settings during deployment. Do not use the secret-protected `sync-lite-intake` job as a public form action.

Success is displayed only after HTTP success and JSON `{ok:true}`. It means the form gateway accepted the details, not that the call is booked. The visitor then opens the verified coach booking link and chooses a time. Answers stay in memory on errors, with explicit retry and no automatic resubmission; the same client-generated submission ID is retained for diagnosis, not a guarantee of server deduplication. Without JavaScript the native form POST remains available, with a separate booking fallback link.

## Booking verification

All three links were inspected in the current public booking UI without entering personal data, selecting a slot or submitting a booking. Filters showed the correct coach and Free Intro Call / Strategy Call. Evidence: `evidence/booking-verification.json`. Availability is dynamic. Rhylie had one transient loading failure that cleared on retry.

| Coach | Staff ID | Service ID |
|---|---|---|
| Justin Poole | 3017439 | 38920 |
| Zach Vazquez | 3017453 | 38920 |
| Rhylie Erdmann | 3065290 | 38920 |

## Copy and review boundaries

The supplied JustJump personas inform the copy: specific goals, understandable coaching decisions and a clear next step. These are proposed marketing pages, not measured conversion evidence. No invented testimonials, personal stories awaiting coach approval, prices or support schedules are included. The latest user direction uses **tactical training** in Zach’s landing-page copy and explicitly includes **bodybuilding competition prep** for both Justin and Rhylie. This confirms those marketing service categories and supersedes the prior omission of competition prep; it does not establish certifications, competitive achievements, specific prep inclusions, or client outcomes. Earlier social-profile copy and source records remain preserved.

Source snapshots, photo hashes, checks and viewport screenshots are in `evidence/`; none belongs in the public package. The original marketing-site pages, deployment configuration and other funnels are not modified by this additive feature. Separate-site publication is tracked by its deployment receipt and live checks. A controlled live form-to-inbox/import check remains separate from those hosting checks and the local intercepted tests.

## Validation

Run the restoration suite while serving `publish/` locally:

```sh
/home/jaquesdanger/.cache/raptor-browser-venv/bin/python coach-pages/tests/viewport-fit-check.py --base-url http://127.0.0.1:8797 --landing-only --pricing-baseline coach-pages/evidence/restored-hero-pricing-baseline.json --evidence coach-pages/evidence/restored-hero-checks.json
```

`evidence/restored-hero-checks.json` passed all 27 landing views: three coaches at nine viewport sizes, including 320×568 and 844×390. Actual text/control bounds, ancestor clipping and document dimensions were checked. Pricing preservation passed all 11 file hashes and nine computed-style/bounds comparisons against `restored-hero-pricing-baseline.json`. This is local evidence, not a deployment or payment claim. At browser text enlargement, content may reflow and scroll to remain accessible.

The former compact-hero matrix in `evidence/viewport-fit-checks.json` passed 54 views, with its own hosted revision verified by `viewport-fit-live-smoke.json`. Those reports are historical for hero appearance; they must not override the user's selected original reference. The older `intake-check.py` and `redesign-check.py` also encode superseded page structures and are not the restoration's structural acceptance suite.

The preceding minimal-flow suite passed nine responsive coach flows, three synthetic intakes with blank-phone rejection, three pricing-to-intake hash navigations, three stubbed Stripe dialog checks and three no-JavaScript intake fallbacks. That dated evidence verifies the earlier revision. Form submissions and Stripe behavior were intercepted; no real lead, booking or payment was created.

Earlier evidence remains historical: `evidence/redesign-tests.json` passed 36 responsive views, 54 checkout dialogs, six landing-to-purchase navigations, 21 loader-failure fallback offers and 18 JavaScript-disabled direct links. Its ten byte-identical landing files and earlier screenshots describe the previous checkout revision, not the newly reduced page structure. Likewise, the six read-only real Stripe renders establish widget rendering, not payment or fulfillment.

Phone remains visibly required in every intake and block, including the no-JavaScript fallback. The former phone-only markup exception is superseded by the user's explicit minimal-flow correction; it must not prevent removing the unwanted sections. Gateway-side Formspree configuration is unchanged. `evidence/intake-tests.json` records its own tested revision; older screenshots may show the former optional label.

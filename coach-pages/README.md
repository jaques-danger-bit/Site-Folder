# Coach landing pages

Three landing pages and three separate purchase pages for Justin, Zach and Rhylie, redesigned October 30, 2026. Original supplied portraits, actual Dropbox SVG logos and buyer-informed copy support two visible paths: **I’m ready to start training** opens the selected coach’s purchase page; **Book a call** leads through the mini intake to that coach’s intro-call booking.

## Review and use

- `index.html`: local review index.
- `justin.html`, `zach.html`, `rhylie.html`: coach landing pages.
- `start-justin.html`, `start-zach.html`, `start-rhylie.html`: separate purchase pages. Deploy this directory with its `assets/` folder to serve all six pages.
- `blocks/*-copy-paste.html`: six self-contained blocks: one landing block and one `start-{slug}-copy-paste.html` purchase block per coach. Each includes the original supplied JPEG, SVG logos and local fonts as data URLs, with scoped styles. Landing blocks also include intake behavior. Paste one per full-width HTML/custom-code section that permits JavaScript. The host controls outer padding and iframe height. A restrictive host may strip inline scripts or data images, so check the actual host before publishing. No remote photo or logo URL is needed.
- `coaches.json`: editable coach copy, booking routes and `purchaseUrl`. `offers.json`: the three user-selected, publicly verified offers and Stripe destinations. `assets/coach.css`: shared layout. `assets/intake.js`: shared form behavior. `assets/purchase.css`, `assets/purchase.js` and `scripts/purchase_pages.py`: purchase layout, selected-offer dialog and generation.
- `FUNNEL-NOTES.md`: the two-path flow, supplied Stripe offers, ManyChat plan and current integration limits.

`purchaseUrl` defaults to `start-{slug}.html`, which works when the six files are hosted together. Website-builder embeds must use the actual published purchase-page URL after the host/slugs are chosen. Also update the purchase page’s return-to-coach links when its landing page uses a different published URL. Purchase/return links use `target="_top"` so navigation can leave an iframe; the host must permit that navigation.

From the repository root, run `python3 -m http.server 8795 --bind 127.0.0.1` and open `http://127.0.0.1:8795/coach-pages/`. These pages point at a real intake endpoint. Automated checks intercept all external requests; previewing does not require submitting test leads.

Rebuild the pages and blocks with `python3 coach-pages/scripts/build.py`. The generator assembles all six pages and six blocks without transforming the portraits or SVG artwork. Header logo: Dropbox `strikeline-07.svg`; footer badge: `strikeline-08.svg`. Original file paths and verified hashes are in `evidence/dropbox-logo-provenance.json`. Font licenses are in `assets/*-OFL.txt`.

## Purchase redesign and supplied Stripe offers

The user selected the v2 landing-page design: full-bleed coach portrait, charcoal treatment and orange CTA. Preserve that landing design and carry it into the separate purchase pages, followed by a clear offer comparison. Each **Choose** button opens a native dialog with the actual Stripe Buy Button, loaded only for the selected offer through one shared loader. Keep the verified direct Stripe link visible as a fallback. The call route remains available for visitors who want help deciding.

Read-only public Stripe responses confirm **Online Coaching — Monthly: $350/month** and **Monthly Coaching — Foundation: $475/month**. Foundation includes full programming and one session/week, with 30-day cancellation notice. The user confirmed **Nutrition + Training Assessment: $175 one-time** as the entry offer. The public website's $175 Standalone Program with $30 updates is a different offer and is excluded from this three-offer checkout set. Do not transfer its update fee or the website contact form's 30-minute description to the paid assessment. Evidence and proposed copy: `evidence/services-20261030/RESEARCH-NOTES.md` and `offer-comparison.json`.

Use static `client-reference-id="stg_{coach}_{offer}"` for the selected coach/offer. This is a purchase reference, not proof of backend assignment or fulfillment. All three actual Stripe widgets rendered through read-only public GETs at desktop 1440px and mobile 320px (six views); `evidence/stripe-public-render.json` records the check. No payment was made. Stripe connector reauthentication was unavailable; no dashboard settings were changed and no deployed fulfillment webhook was verified. A bounded local portal-code read found a founders-only webhook that ignores other purchases and no function consuming `client_reference_id`; this is a local-code finding, not deployed-state evidence. Verify live coach assignment and fulfillment before launch. No automatic onboarding or delivery deadline is promised in the public copy.

## Existing mini intake

Verified public gateway: `https://formspree.io/f/mdajqedj`.

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

Source snapshots, photo hashes, checks and viewport screenshots are in `evidence/`. The original site pages, deployment configuration and other funnels are not modified by this additive feature. Publishing and a controlled live form-to-inbox/import check remain separate from the local intercepted tests.

## Validation

Run the intercepted form suite with `python coach-pages/tests/intake-check.py` in an environment with Playwright and Chromium. Local runner: `/home/jaquesdanger/.cache/raptor-browser-venv/bin/python`. The script accepts `--base-url` and `--chrome` overrides; see the defaults near its entry point. Visual capture: `coach-pages/scripts/check-visual.py`. Checks include successful receipt, all coach routes, required-field validation, duplicate submissions, explicit retries, failures, and complete embedded blocks. See the dated JSON evidence for what was actually run.

The final purchase suite passed 36 responsive views (six pages plus six wrapped blocks at 1440, 390 and 320px), 54 checkout dialogs and six landing-to-purchase navigations. Seven loader-failure/timeout views verified 21 attributed fallback offers; six JavaScript-disabled views verified 18 direct links. At that checkout-revision run, ten approved landing files were byte-identical to commit `967e407`; the later required-phone change is documented below. Original portraits are preserved. All external traffic in this suite was intercepted. Evidence: `evidence/redesign-tests.json`. These checks verify rendered behavior, offer selection, keyboard focus, one-loader behavior and references; they do not verify real payment or downstream fulfillment.

### Required phone follow-up

Phone is now visibly required in every coach mini intake and copy-paste block. Native HTML validation rejects empty and whitespace-only values, including without JavaScript; the existing scripted submit handler also checks form validity. This is the sole authorized change to the approved landing markup. The baseline test permits exactly this field/label edit while preserving all other approved bytes. Gateway-side Formspree configuration is unchanged. See the refreshed `evidence/intake-tests.json` for submission checks; earlier screenshot captures may show the prior optional label.

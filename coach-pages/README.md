# Coach landing pages

Three landing pages and three separate purchase pages for Justin, Zach and Rhylie, redesigned October 30, 2026. Original supplied portraits, actual Dropbox SVG logos and buyer-informed copy support two visible paths: **I’m ready to start training** opens the selected coach’s purchase page; **Book a call** leads through the mini intake to that coach’s intro-call booking.

## Review and use

- `index.html`: local review index.
- `justin.html`, `zach.html`, `rhylie.html`: coach landing pages.
- `start-justin.html`, `start-zach.html`, `start-rhylie.html`: separate purchase pages. Deploy this directory with its `assets/` folder to serve all six pages.
- `blocks/*-copy-paste.html`: six self-contained blocks: one landing block and one `start-{slug}-copy-paste.html` purchase block per coach. Each includes the original supplied JPEG, SVG logos and local fonts as data URLs, with scoped styles. Landing blocks also include intake behavior. Paste one per full-width HTML/custom-code section that permits JavaScript. The host controls outer padding and iframe height. A restrictive host may strip inline scripts or data images, so check the actual host before publishing. No remote photo or logo URL is needed.
- `coaches.json`: editable copy, booking routes and `purchaseUrl`. `assets/coach.css`: shared layout. `assets/intake.js`: shared form behavior. `assets/purchase.css` and `scripts/purchase_pages.py`: purchase-page layout and generation.
- `FUNNEL-NOTES.md`: the two-path flow, pending payment-embed integration, ManyChat plan and current integration limits.

`purchaseUrl` defaults to `start-{slug}.html`, which works when the six files are hosted together. Website-builder embeds must use the actual published purchase-page URL after the host/slugs are chosen. Also update the purchase page’s return-to-coach links when its landing page uses a different published URL. Purchase/return links use `target="_top"` so navigation can leave an iframe; the host must permit that navigation.

From the repository root, run `python3 -m http.server 8795 --bind 127.0.0.1` and open `http://127.0.0.1:8795/coach-pages/`. These pages point at a real intake endpoint. Automated checks intercept all external requests; previewing does not require submitting test leads.

Rebuild the pages and blocks with `python3 coach-pages/scripts/build.py`. The generator assembles all six pages and six blocks without transforming the portraits or SVG artwork. Header logo: Dropbox `strikeline-07.svg`; footer badge: `strikeline-08.svg`. Original file paths and verified hashes are in `evidence/dropbox-logo-provenance.json`. Font licenses are in `assets/*-OFL.txt`.

## Purchase pages and pending embeds

The purchase-page design is ready for the embed links the user will provide after reviewing the redesign. Until those arrive, each page honestly says online enrollment is being prepared and offers a call with the same coach. No product, price, payment link, or active checkout is invented.

The purchase generator reads an optional `purchase-embeds/{slug}.html` containing the supplied trusted public checkout embed. Missing, empty or comment-only files keep the pending state. Once the actual embed/link is provided, wire its public markup to the matching coach and rebuild. Never place secret API keys in embed files. Verify the actual product, price, billing terms and success destination when integrating; the redesign itself does not activate payments.

## Existing mini intake

Verified public gateway: `https://formspree.io/f/mdajqedj`.

Source: [Site-Folder index.html at the reviewed commit](https://github.com/jaques-danger-bit/Site-Folder/blob/82a4326a25579020adc6c51022f4a5ebba4f54ba/index.html), form `applyForm`. The matching form was found in the site footer. A bounded search did not find a separate original mini-intake paste block. The newly supplied blocks adapt this verified form contract.

Preserved field names: `firstName`, `email`, `phone`, `goal`, `goalNotes`, `source`, `_subject`, `_gotcha`. Name, email and goal are required; phone is optional. Each page supplies a fixed `coach` and `source=coach-landing-{slug}`. Allowlisted UTM fields and an in-memory `submission_id` are added to the submitted payload. URL parameters cannot change the coach or booking route. In an iframe, campaign parameters must be present on the iframe URL; the block cannot automatically read a cross-origin parent page’s URL.

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

Redesign checks: `coach-pages/tests/redesign-check.py` verifies six standalone pages and six wrapped blocks at 1440, 390 and 320px (36 rendered views), six purchase navigations, actual SVG logo geometry, unchanged portrait bytes, updated service copy and honest pending checkout states. It blocks external mutations. The current run passed; details are in `evidence/redesign-tests.json`.

# Coach landing pages

Three distinct pages for Justin, Zach and Rhylie, prepared October 30, 2026. Original supplied portraits, charcoal/orange direction and buyer-informed copy lead to the existing mini intake, then a coach-specific intro-call booking.

## Review and use

- `index.html`: local review index.
- `justin.html`, `zach.html`, `rhylie.html`: complete static pages; deploy this directory with its `assets/` folder to serve them.
- `blocks/*-copy-paste.html`: one self-contained HTML block per coach, including the exact supplied JPEG and local fonts as data URLs, scoped styles and intake behavior. Paste one into a full-width HTML/custom-code section that permits JavaScript. The host controls any outer padding or iframe height; use full width and enough height for the entire page. A restrictive host may strip inline scripts or data images, so check the actual host before publishing. No remote photo URL is needed.
- `coaches.json`: editable copy and routing. `assets/coach.css`: shared layout. `assets/intake.js`: shared form behavior.
- `FUNNEL-NOTES.md`: separate Stripe purchase-page recommendation, ManyChat plan and current integration limits.

From the repository root, run `python3 -m http.server 8795 --bind 127.0.0.1` and open `http://127.0.0.1:8795/coach-pages/`. These pages point at a real intake endpoint. Automated checks intercept all external requests; previewing does not require submitting test leads.

Rebuild the pages and blocks with `python3 coach-pages/scripts/build.py`. The generator only assembles text and embeds/copies original photo bytes; it does not transform the portraits. Font licenses are in `assets/*-OFL.txt`.

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

The supplied JustJump personas inform the copy: specific goals, understandable coaching decisions and a clear next step. These are proposed marketing pages, not measured conversion evidence. No invented testimonials, personal stories awaiting coach approval, prices or support schedules are included. Zach’s strength/firearms roles are user-confirmed. Rhylie’s NPC Bikini highlight topic is not used as a contest-prep credential or unverified service claim.

Source snapshots, photo hashes, checks and viewport screenshots are in `evidence/`. The original site pages, deployment configuration and other funnels are not modified by this additive feature. Publishing and a controlled live form-to-inbox/import check remain separate from the local intercepted tests.

## Validation

Run the intercepted form suite with `python coach-pages/tests/intake-check.py` in an environment with Playwright and Chromium. Local runner: `/home/jaquesdanger/.cache/raptor-browser-venv/bin/python`. The script accepts `--base-url` and `--chrome` overrides; see the defaults near its entry point. Visual capture: `coach-pages/scripts/check-visual.py`. Checks include successful receipt, all coach routes, required-field validation, duplicate submissions, explicit retries, failures, and complete embedded blocks. See the dated JSON evidence for what was actually run.

# Coach landing-page funnel handoff

Prepared October 30, 2026. This records the page flow, supplied payment embeds, separate public-site packaging and later integration work. No transaction, Stripe dashboard change, messaging activation or gateway configuration change is part of this review. Phone is now required in the page and block markup.

## Current two-path flow

The user now requires two visible choices on each coach page:

- **I’m ready to start training** → that coach’s separate `/{slug}/start/` public purchase page. This path does not require submitting the mini intake.
- **Book a call** → mini intake → successful Formspree acceptance → coach-specific call-booking CTA.

This supersedes the earlier call-only landing-page recommendation. Keep the selected coach consistent through either path. Local sources still use `start-{slug}.html`; the public packager rewrites navigation to clean routes. Builder-hosted blocks need the public destination URLs and permitted top-level iframe navigation.

The redesign uses the actual Dropbox SVG files: `strikeline-07.svg` for headers and `strikeline-08.svg` for footers, with provenance in `evidence/dropbox-logo-provenance.json`. Zach’s current landing copy uses tactical training. Justin’s and Rhylie’s pages now explicitly include user-authorized bodybuilding competition prep, alongside their broader strength/physique focus. These categories do not imply additional credentials, outcomes or detailed service terms.

The repository discovery identified `Site-Folder` `main/index.html` as the current short-form source and `https://formspree.io/f/mdajqedj` as its endpoint. The existing downstream path is Formspree → sheet → hourly portal import, with daily email deduplication. Current import code does not persist coach selection or UTM fields. Adding fixed coach/source and campaign fields to the new front end therefore does **not** prove they reach the portal. Verify and extend the sheet/import mapping separately before relying on coach attribution or automated routing there.

The browser-generated `submission_id` is a diagnostic identifier only. It is not a server-verified lead reference, authenticated ManyChat contact identifier, or backend idempotency guarantee. A Formspree success response confirms acceptance by that endpoint, not completion of the later sheet/import pipeline or a booked call. Retain the booking link on the success screen and avoid telling a visitor a DM has already been sent.

Read-only booking findings are recorded in `evidence/booking-verification.json`. Staff IDs are Justin `3017439`, Zach `3017453`, and Rhylie `3065290`; the existing intro-call route specifies service `38920`. All three destinations rendered the public Free Intro Call calendar; opening Filters showed Justin Poole, Zach Vazquez, and Rhylie Erdmann respectively, plus the Strategy Call category. Rhylie’s initial loading error cleared on independent retry. This verifies the displayed staff/service routing, not a completed booking or continuing slot availability. No appointment, login, or personal-data submission is part of this review.

## Separate public site and delivery boundary

The public site is `https://strikeline-coaching.netlify.app`, Netlify site `d40f2639-dc6b-4a77-8d46-d297b2cc9b23`. It has seven customer routes: `/` for the coach selector; `/justin/`, `/zach/`, `/rhylie/` for the approved landing pages; and `/justin/start/`, `/zach/start/`, `/rhylie/start/` for purchase options. [The deployment receipt](evidence/hosting-deploy.json) records production deploy `6ae4a3067dc975fa84639d40` on October 30, 2026. Publication and live validation are distinct: use that receipt and the latest [live-check report](evidence/public-site-live-checks.json) for the deployed revision and verified behavior. Site creation and a successful local package build alone do not prove deployment.

The user explicitly kept the public booking calendars at `training.strikelinetraining.com/a/booking/`. Keep those destinations, their coach/service identity and the Formspree endpoint intact. Public logo links return to the new coach selector, and customer navigation contains no internal-portal links. Name, email, phone and goal remain required; phone rejects blank and whitespace-only input.

`scripts/build-public-site.py` packages only seven HTML pages, 15 public assets and a legacy 301 redirect map into ignored `publish/`. It rewrites asset paths and coach/purchase navigation without changing the approved source pages or purchase behavior. Configuration, blocks, documentation, research, evidence, scripts and tests stay outside that 23-file allowlist. Original asset bytes and route/file hashes are recorded in `evidence/public-site-manifest.json`.

After rebuilding the sources and package, deployment from `coach-pages/` uses:

```sh
netlify deploy --prod --no-build --dir publish --site d40f2639-dc6b-4a77-8d46-d297b2cc9b23
```

Never deploy the whole `coach-pages/` directory or repository root. Hosting verification covers public routes, assets, redirects, phone validation, booking destinations and checkout references without creating a lead, booking or payment. The origin-specific Formspree OPTIONS check in `evidence/hosting-form-preflight.json` establishes only the observed CORS response, not gateway acceptance or downstream delivery.

## Separate Stripe purchase page

The user approved the v2 full-bleed landing design with orange CTA and rejected the earlier purchase treatment. Preserve the landing pages and use that visual direction for the separate purchase pages: full-bleed portrait → offer comparison → **Choose** → native dialog containing the selected actual Stripe Buy Button. Load only the selected embed through one loader and keep a verified direct Stripe checkout link visible as a fallback. Retain the same-coach call path.

Public Stripe GETs confirm online coaching at $350/month and Foundation coaching at $475/month. Foundation specifies full programming, one session/week and 30-day cancellation notice. The user confirmed the $175 one-time Nutrition + Training Assessment as the entry offer. This resolves the earlier mismatch by choosing the assessment; the website's separate Standalone Program and its $30 updates are not part of this checkout set. Do not call the assessment a program or assign it the website contact form's 30-minute duration. See `evidence/services-20261030/RESEARCH-NOTES.md` for sources, scope and concise card copy.

For cold buyers, compare the level of support, relevant fit, actual inclusions and price/cadence in plain language. The purchase page is a conversion hypothesis to test, not evidence of improved sales. Do not invent client proof, check-in frequency, response times or a commitment term to fill gaps in the product descriptions.

Each coach/offer uses static `client-reference-id="stg_{coach}_{offer}"`. That reference provides attribution for a future verified backend; it does not itself assign the coach, grant app access or deliver programming. All three actual Stripe widgets and product metadata were inspected read-only, including six widget renders at 1440px and 320px. Evidence is in `evidence/stripe-public-render.json`; no checkout was completed. Stripe connector reauthentication was unavailable, so no dashboard settings or live webhook configuration were inspected or changed.

A bounded local read found `stg-portal/netlify/functions/founders-webhook.js` explicitly ignores non-founders coaching purchases; `stripe-payouts.js` reads product metadata, and no `client_reference_id` consumer was found in the functions searched. This describes the local checkout, not the deployed backend. Verify actual coach assignment and fulfillment before relying on automated assignment or delivery. The page/embed request does not authorize building an assumed onboarding backend; public copy must not promise automatic onboarding or a delivery deadline.

- [Stripe Buy Button documentation](https://docs.stripe.com/payment-links/buy-button)
- [Stripe Checkout options](https://docs.stripe.com/payments/checkout)
- [Stripe post-payment events, fulfillment, redirects and metrics](https://docs.stripe.com/payment-links/post-payment)

Count purchases from verified Stripe events, with appropriate handling for delayed payment methods; a thank-you-page visit alone is not proof of payment. Confirm the real post-payment destination and fulfillment as separate account-level checks; publication of the coaching pages does not verify either. Live purchases and Stripe account configuration remain separate from read-only embed verification.

The separate-hosting audit left post-payment destinations **unverified**. Accessible public Stripe responses did not expose a configured completion URL, and the bounded local exact-link search found no matching legacy configuration. No internal-portal address appeared in the inspected responses, but this does not prove the after-payment destination. The audit blocked Stripe’s POST initialization; its resulting browser error is not evidence of a broken payment link. See `evidence/stripe-return-audit.json`. Publishing the public pages does not verify, alter or guarantee Stripe’s completion redirect, coach assignment or fulfillment.

Measure page views, intake starts, accepted intakes, booking-link clicks, confirmed bookings, attended calls, sales, refunds and revenue by coach and acquisition source. Keep clicks separate from actual bookings. For the purchase page, compare qualified purchases and net revenue against traffic cost, not just checkout starts. Judge the direct-purchase hypothesis with observed results; no conversion lift is promised.

## ManyChat after the mini-intake — later stage

A web form submission, email or Instagram handle alone does not establish an Instagram messaging relationship. Normal automated Instagram follow-up requires an eligible interaction and an open messaging window. An external webhook or API request does not remove those requirements.

For a website-first visitor, keep the booking CTA available immediately after intake. An optional **Continue in Instagram** button can later use the correctly connected coach/account's ManyChat Instagram Ref URL. The current documented Ref URL flow is mobile-app-only; new users need Conversation Starters enabled or must manually message. Keep a direct booking alternative for desktop visitors. Pass an opaque reference rather than personal intake answers in the referral URL.

For an Instagram-first visitor, establish the contact through an eligible DM interaction, then send the intake link with a server-verifiable reference. A future authenticated backend event can match the accepted intake to the correct coach/account and known ManyChat contact, then trigger the appropriate booking message while the messaging window permits it. The frontend's present diagnostic `submission_id` does not provide that secure mapping.

Required later work: select and verify the connected Instagram accounts, authenticate the intake-event source, implement contact/lead mapping and deduplication, persist coach/source fields, verify current API capabilities, configure the permitted flow, and test success/failure paths without duplicate or wrong-coach messages. Treat browser-supplied fields as untrusted; validate coach/account routing on the server. Keep credentials and message-sending operations on the server. If matching or the messaging window is unavailable, preserve the booking path instead of claiming a DM was delivered.

- [ManyChat Instagram Ref URL trigger, mobile and new-user requirements](https://help.manychat.com/hc/en-us/articles/14281276006684-Instagram-Ref-URL-Trigger)
- [ManyChat Instagram automation rules and messaging window](https://manychat.com/blog/instagram-dm-automation-rules/)
- [ManyChat developer tools and contact identifiers](https://help.manychat.com/hc/en-us/articles/14281252007580-Dev-Tools-Basics)

These are implementation recommendations based on official documentation checked October 30, 2026. ManyChat configuration and activation are intentionally deferred until after the landing-page and mini-intake work.

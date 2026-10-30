# Coach landing-page funnel handoff

Updated October 30, 2026 after the user explicitly selected the **original screenshot hero, commit `967e407`**, and requested reworking the existing page rather than repeated redesigns. That is the fixed hero reference. Restore the full original paragraphs, header Talk link, specialty label, typography, left-aligned buttons, photo treatment/crops and footer name. Compact pricing and the current intake remain unchanged. The restoration passed local validation and was published as deploy `6ae4b72d98525fce2aaba2af` on October 30, 2026 at 15:26:39 UTC; live verification is recorded separately. No transaction, Stripe dashboard change, messaging activation or gateway configuration change is part of this work.

**Future edits must make the smallest necessary change against the selected original reference.** Do not introduce unsolicited copy, crop, font or layout redesigns. Targeted height adjustments remain permitted to satisfy the existing fit requirement; they do not authorize replacing the design again.

## Current two-path flow

Each hero has two visible choices:

- **I’m ready to start training** opens that coach's `/{slug}/start/` directly at the compact dark three-offer comparison, with every option visible in the viewport.
- **Book a call** opens the dark native mini-intake dialog on the same hero page. After Formspree accepts the form, the visitor can open the coach-specific public booking calendar.

The restored hero uses the original 48px mobile headline at normal heights, original gradients and object positions, Justin's 13% desktop photo shift and Rhylie's mobile transform. Height-specific overrides preserve fit. Previously requested exclusions still apply: no arrows, helper/approach filler, white sections, process, FAQ or sticky additions. The footer name is restored. Direct intake links remain `/{coach}/#{coach}-intake`; with JavaScript disabled, CSS `:target` reveals the same dark form and native POST remains available. Name, email, phone and goal remain required.

Keep the selected coach consistent through either path. Local sources use `start-{slug}.html`; the public packager rewrites navigation to clean routes. Builder-hosted blocks need the public destination URLs and permitted top-level iframe navigation.

The original Dropbox SVG assets and portraits remain intact, with logo provenance in `evidence/dropbox-logo-provenance.json`. Zach’s current landing copy uses tactical training. Justin’s and Rhylie’s pages include user-authorized bodybuilding competition prep alongside their broader strength/physique focus. These categories do not imply additional credentials, outcomes or detailed service terms.

The repository discovery identified `Site-Folder` `main/index.html` as the current short-form source and `https://formspree.io/f/mdajqedj` as its endpoint. The existing downstream path is Formspree → sheet → hourly portal import, with daily email deduplication. Current import code does not persist coach selection or UTM fields. Adding fixed coach/source and campaign fields to the new front end therefore does **not** prove they reach the portal. Verify and extend the sheet/import mapping separately before relying on coach attribution or automated routing there.

The browser-generated `submission_id` is a diagnostic identifier only. It is not a server-verified lead reference, authenticated ManyChat contact identifier, or backend idempotency guarantee. A Formspree success response confirms acceptance by that endpoint, not completion of the later sheet/import pipeline or a booked call. Retain the booking link on the success screen and avoid telling a visitor a DM has already been sent.

Read-only booking findings are recorded in `evidence/booking-verification.json`. Staff IDs are Justin `3017439`, Zach `3017453`, and Rhylie `3065290`; the existing intro-call route specifies service `38920`. All three destinations rendered the public Free Intro Call calendar; opening Filters showed Justin Poole, Zach Vazquez, and Rhylie Erdmann respectively, plus the Strategy Call category. Rhylie’s initial loading error cleared on independent retry. This verifies the displayed staff/service routing, not a completed booking or continuing slot availability. No appointment, login, or personal-data submission is part of this review.

## Separate public site and delivery boundary

Reuse `https://strikeline-coaching.netlify.app`, Netlify site `d40f2639-dc6b-4a77-8d46-d297b2cc9b23`. Its seven routes remain `/` for the coach selector; `/justin/`, `/zach/`, `/rhylie/` for landing heroes; and each coach's `/start/` route for pricing. The restored original hero was published as deploy `6ae4b72d98525fce2aaba2af` at 15:26:39 UTC on October 30, 2026. Its [deployment receipt](evidence/hosting-deploy.json) establishes publication; consult the matching [live-check report](evidence/public-site-live-checks.json) for hosted verification. Deploy `6ae4ae07bdc610bf593a3f50` remains the preceding compact-hero revision.

Local `evidence/restored-hero-checks.json` passed 27 landing views across nine sizes, including 320×568 and 844×390. It also verified 11 unchanged file hashes and nine unchanged pricing style/bounds comparisons. `assets/landing.css` scopes the restoration to landing pages; pricing/shared behavior is preserved. The earlier 54-view compact-hero report and its live smoke remain historical and must not be mistaken for the selected visual baseline. Prior receipts remain under `evidence/history/`.

The user explicitly kept the public booking calendars at `training.strikelinetraining.com/a/booking/`. Keep those destinations, their coach/service identity and the Formspree endpoint intact. Logo/navigation links stay within the selected coach’s landing and pricing flow, and customer navigation contains no internal-portal links. Name, email, phone and goal remain required; phone rejects blank and whitespace-only input.

`scripts/build-public-site.py` packages only seven HTML pages, 16 public assets including scoped `landing.css`, and a legacy 301 redirect map into ignored `publish/`. It rewrites asset paths and coach/purchase navigation without changing the approved source pages or purchase behavior. Configuration, blocks, documentation, research, evidence, scripts and tests stay outside that 24-file allowlist. Original asset bytes and route/file hashes are recorded in `evidence/public-site-manifest.json`.

After rebuilding the sources and package, deployment from `coach-pages/` uses:

```sh
netlify deploy --prod --no-build --dir publish --site d40f2639-dc6b-4a77-8d46-d297b2cc9b23
```

Never deploy the whole `coach-pages/` directory or repository root. Hosting verification covers public routes, assets, redirects, phone validation, booking destinations and checkout references without creating a lead, booking or payment. The origin-specific Formspree OPTIONS check in `evidence/hosting-form-preflight.json` establishes only the observed CORS response, not gateway acceptance or downstream delivery.

## Separate Stripe purchase page

The compact purchase page remains unchanged: three columns on desktop and three rows on mobile, with every choice visible within one viewport. Its **Train with {coach}** header is followed by each offer's name, full price/cadence, concise factual description, material terms and **Choose** button. There are no numbers, badges, divider lines, marketing headings, bottom talk block, photo hero or FAQ. The footer keeps Talk and legal links. Restoring the original landing screenshot does not authorize another purchase-page redesign.

A **Choose** button opens a native dialog containing the selected actual Stripe Buy Button. Load only that embed through one loader and keep a verified direct Stripe checkout link visible as a fallback. The footer Talk link returns to the same coach's dark intake dialog on the landing page.

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

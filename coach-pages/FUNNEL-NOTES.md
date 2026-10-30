# Coach landing-page funnel handoff

Prepared October 30, 2026. This records the recommended flow and later integration work; it does not activate payments, messaging, or production form changes.

## Current call-booking flow

Coach page → mini-intake → successful Formspree acceptance → coach-specific call-booking CTA.

The repository discovery identified `Site-Folder` `main/index.html` as the current short-form source and `https://formspree.io/f/mdajqedj` as its endpoint. The existing downstream path is Formspree → sheet → hourly portal import, with daily email deduplication. Current import code does not persist coach selection or UTM fields. Adding fixed coach/source and campaign fields to the new front end therefore does **not** prove they reach the portal. Verify and extend the sheet/import mapping separately before relying on coach attribution or automated routing there.

The browser-generated `submission_id` is a diagnostic identifier only. It is not a server-verified lead reference, authenticated ManyChat contact identifier, or backend idempotency guarantee. A Formspree success response confirms acceptance by that endpoint, not completion of the later sheet/import pipeline or a booked call. Retain the booking link on the success screen and avoid telling a visitor a DM has already been sent.

Read-only booking findings are recorded in `evidence/booking-verification.json`. Staff IDs are Justin `3017439`, Zach `3017453`, and Rhylie `3065290`; the existing intro-call route specifies service `38920`. All three destinations rendered the public Free Intro Call calendar; opening Filters showed Justin Poole, Zach Vazquez, and Rhylie Erdmann respectively, plus the Strategy Call category. Rhylie’s initial loading error cleared on independent retry. This verifies the displayed staff/service routing, not a completed booking or continuing slot availability. No appointment, login, or personal-data submission is part of this review.

## Separate Stripe purchase page

Recommendation: retain call booking as the primary next step for custom coaching. A separate purchase link can be useful for a fixed offer whose outcome, deliverables, fit, price, duration/access, billing terms, cancellation/refund terms, and fulfillment are already clear. A defined program or fixed-scope session could fit this model **if it is an actual available offer**. No offer, price, certification, or result is invented here.

The simplest first integration is an existing Stripe Payment Link with its copy-paste Buy Button/card. Fully embedded Checkout is also available through Checkout Sessions and entails more integration work. Decide from the actual offer and buyer experience; an embed alone is not evidence of better cold-traffic conversion.

- [Stripe Buy Button documentation](https://docs.stripe.com/payment-links/buy-button)
- [Stripe Checkout options](https://docs.stripe.com/payments/checkout)
- [Stripe post-payment events, fulfillment, redirects and metrics](https://docs.stripe.com/payment-links/post-payment)

Before activation, select the real product/price and configure the correct success destination and fulfillment. Count purchases from verified Stripe events, with appropriate handling for delayed payment methods; a thank-you-page visit alone is not proof of payment. Payment configuration, live purchases and Stripe account changes remain future work.

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

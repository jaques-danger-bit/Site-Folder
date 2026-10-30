# Stripe post-payment destination audit

Checked October 30, 2026. **The three post-payment destinations remain unverified.** No internal-portal URL appeared in the accessible public data, but that does not establish where Stripe redirects after payment.

| Offer | Supplied public Payment Link | Finding |
| --- | --- | --- |
| $175 assessment | https://buy.stripe.com/fZueVf0L480x3sPdAfgQE2z | Public HTML and observed bootstrap config expose no configured success/return URL. |
| $350/month online | https://buy.stripe.com/fZucN70L4fsZgfB0NtgQE2A | Same limitation. |
| $475/month Foundation | https://buy.stripe.com/dRmcN765o94B5AXao3gQE2B | Same limitation. |

The public HTML was identical across all three links. The observed `/payment-links/{id}` GET endpoint returned merchant/branding bootstrap data without return, success, completion or redirect fields. Previously captured successful public Buy Button responses also lacked those fields. No `stgportal.netlify.app` literal appeared in those responses or the accessible browser DOM.

Browser inspection allowed GET/HEAD/OPTIONS only. Stripe's payment-link initialization POST was blocked, so the resulting page error is **not** evidence that the live link is broken. No data was entered, payment clicked, account setting changed, or secret configuration read. No payment or subscription was created. Stripe connector reauthentication remained unavailable.

A bounded exact search for the three link tokens and Buy Button IDs in the local `stg-portal` and Site-Folder feature checkout found no legacy configuration outside the new `coach-pages` feature. No environment/credential files were inspected. This establishes no deployed routing behavior.

Stop at this boundary: do not claim that Stripe's after-payment destination avoids the internal portal, or that coach assignment and fulfillment are verified. Inspect the actual Payment Link after-payment setting through authenticated Stripe access when available. The user's retained public Exercise booking links are outside this audit and were not changed.

Machine-readable evidence, statuses, blocked methods and source URLs: `stripe-return-audit.json`.

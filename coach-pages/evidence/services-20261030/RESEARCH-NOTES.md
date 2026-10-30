# Public services and purchase-copy research

Captured 2026-10-30. Research only; no product configuration changed, no checkout submitted, no booking or purchase created. Website HTML/text and link lists are captured alongside this note; `website-manifest.json` records final URLs, retrieval time and SHA-256. Stripe facts below come from the root agent's read-only `stripe-public-read.json`; `offer-comparison.json` extracts only relevant product fields.

## Verified offers and resolved selection

**User decision: use the $175 assessment.** Current checkout order is Nutrition + Training Assessment ($175 one-time), Online Coaching ($350/month), and In-Person Foundation ($475/month). The website's separate standalone program is excluded. The original mismatch is preserved below as evidence.

| Offer on public services page | Website price and scope | Supplied Stripe product | Decision boundary |
| --- | --- | --- | --- |
| Standalone Program | $175; program updates $30 each. A goal-based coach-built program for independent training. The website does not print a recurring cadence or explicitly say one-time. | **Nutrition + Training Assessment**, $175 USD one-time. Description says a comprehensive nutrition and training assessment. | Different fulfillment. Do not put the standalone-program name or $30-update claim above this assessment checkout. User resolved the selection: use the actual assessment, not the standalone program. |
| Online Coaching | $350/month; goal-based programming, remote training support, plan fits the buyer's training setup. | **Online Coaching — Monthly**, $350 USD each month. Description adds custom programming, check-ins and nutrition protocol. | Price and delivery mode align. No check-in frequency, response-time guarantee, cancellation window or minimum commitment is stated in this product response. |
| In-Person Coaching | $475/month; training at the Beaufort gym, technique guidance and programming around the buyer's goals. | **Monthly Coaching — Foundation**, $475 USD each month. Description specifies full programming and one session per week; 30-day cancellation notice. | Amount and general format align. Preserve the Foundation tier and its one-session-per-week limit; do not imply unlimited sessions. Display the 30-day notice near the decision. |

Website source: https://strikelinetraining.com/services#menu

Read-only Stripe product sources and corresponding hosted checkout destinations:

- Online: https://merchant-ui-api.stripe.com/buy-button/buy_btn_1UWFDHRzFn0Z1SgZci4LXSUf → https://buy.stripe.com/fZucN70L4fsZgfB0NtgQE2A
- Foundation: https://merchant-ui-api.stripe.com/buy-button/buy_btn_1UWFE2RzFn0Z1SgZvpUqdxYp → https://buy.stripe.com/dRmcN765o94B5AXao3gQE2B
- Assessment (supplied as standalone): https://merchant-ui-api.stripe.com/buy-button/buy_btn_1UWFCARzFn0Z1SgZqB6Sx8fi → https://buy.stripe.com/fZueVf0L480x3sPdAfgQE2z

The three website checkout links go to Exercise.com package 76121 (standalone), 76795 (in-person), and 76120 (online), respectively. Those pages are client-rendered and exposed no offer text to the web reader. They are a different checkout route from the newly supplied Stripe buttons; no claim is made that their fulfillment, coach assignment, or purchase automation is equivalent.

## Assessment language is not one uniform offer

The services page describes its assessment CTA as thirty minutes with the head coach. Its destination is https://strikelinetraining.com/#assessment, a contact form titled “Let's talk about your goals,” not a priced checkout. The form sends details to the coaching team. Do not transfer this duration, head-coach identity or free-intro-call status to the Stripe paid Nutrition + Training Assessment. The public website does not tie that paid product to this form.

## Terms and inclusions: what is and is not established

- Foundation's Stripe description explicitly requires 30-day cancellation notice. No minimum contract term, notice delivery method, missed-session policy, session length, rollover rule, refund policy, or first-session scheduling process is established by the captured product.
- Online's description establishes custom programming, check-ins and a nutrition protocol. It does not establish weekly check-ins, unlimited messages, response hours, a minimum term, a cancellation policy, or an initial delivery deadline.
- Assessment establishes one-time nutrition/training assessment only. The captured product does not establish its duration, report format, whether an ongoing program is included, credit toward coaching, scheduling procedure or delivery deadline.
- All three Stripe price records have `tax_behavior: unspecified`; do not promise tax-inclusive pricing or add a tax amount. Recurring prices have monthly interval count 1 and no trial duration in the response. Do not market a free trial.
- https://strikelinetraining.com/terms-and-conditions is website Terms of Use (last amended April 1, 2026), not a detailed coaching purchase agreement. No cancellation, refund, minimum-commitment or fulfillment timetable was found there. It does not cure the product-specific gaps above.
- Public gym membership is separately listed at $59.99/month plus a $50 one-time Basic Gym Use fee. Coaching cards do not establish whether that membership is included or additional; do not add that fee to a coaching checkout or promise membership inclusion without confirmation.
- The home page publicly offers muscle/physique training, nutrition guidance, competition prep and posing support as service categories. That does not establish all of them as included in every package, with every coach, at these prices. User direction authorizes bodybuilding competition-prep positioning for Justin/Rhylie and tactical-training positioning for Zach; detailed package scope remains a separate question.
- Avoid turning the generic coaching prices into a priced tactical weapons course or a guaranteed full competition-prep package. Named credentials on general site copy are not automatically credentials for each of the three coaches.

## Recommended price hierarchy and card copy

Design recommendation, not validated conversion evidence: use a clear three-level comparison by support, with Online visually emphasized for a broadly distributed social audience. Give every option its own reason to choose it. Do not call one “most popular” or “best value” without supporting sales data. Keep amounts and cadence adjacent. Do not convert monthly subscriptions into per-week figures.

The user-selected hierarchy is **assessment → online coaching → in-person coaching**. The first card is an assessment, not a cheaper training plan. Do not attach the website program's $30 update fee or a 30-minute duration to this offer.

### Online Coaching

**$350 / month**

Your coach's guidance, wherever you train.

- A program built around your goals and setup
- Check-ins to support your training
- A nutrition protocol alongside your programming

Fit line: For you if you want ongoing coaching while training independently.

CTA: **Start online coaching**

### In-Person Coaching · Foundation

**$475 / month**

Build your plan. Train with a coach beside you.

- Full training programming
- One coached session each week in Beaufort
- Guidance on technique and exercise execution

Fit line: For you if you want hands-on coaching on the gym floor.

Visible term: **30-day cancellation notice required.**

CTA: **Start in-person coaching**

### Nutrition + Training Assessment — user-confirmed entry offer

**Nutrition + Training Assessment · $175 one-time**

Take a closer look at your nutrition and training.

One comprehensive assessment of your nutrition and training. Ongoing coaching is a separate choice.

CTA: **Start with an assessment**

Do not pad this card with invented deliverables. Its current product description is too sparse to promise a personalized ongoing program, turnaround time or action-plan document.

## Buyer reasoning and coach-specific bridge copy

These are proposed messages based on the authorized working ladders in `coach-social-media-persona/references/buyer-personas-and-ladders.md`, not validated customer quotes or outcome claims.

- **Aaron:** “Does the preparation match my requirement and timeline?” Show relevant starting-point assessment, priorities and progress measures. Zach's tactical category can invite the conversation; do not promise every selection standard or that the generic subscription includes tactical skills instruction. Bridge: “Build strength and skills with a clear reason for the work.”
- **Pat:** “What makes this coaching worth more than a program?” Explain independent plan versus ongoing review versus coached sessions. Show the reasoning behind actual training adjustments; avoid using a coach's physique as evidence of client outcomes. Justin bridge: “Give your strength, physique or competition goal a clear direction.”
- **Amanda:** “Will I understand what to do, and what support am I buying?” Use plain-language inclusions, a comprehensible next step and realistic milestones. Do not assume all women are beginners or need weight loss. Rhylie bridge: “Build your physique with direction you understand and support you can see.”

The comparison must resolve location, level of support, price/cadence, what the buyer receives and how to take the next step. No source supports a promise of immediate coach assignment, a specific coach response deadline, or automatic program delivery after these Stripe links. Root owns verification of the post-payment flow and supplied embed behavior.

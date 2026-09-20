# Travel Cost Estimator

"Roughly what will that trip cost?" is a question that gets answered with a guess,
and the guess is wrong often enough that people stop trusting the number. This skill
answers it with **live fares** pulled from your corporate booking tool, and fills the
lines the booking tool doesn't cover by benchmarking against **your own approved
expense reports** — so the number holds up when your manager pushes back on it.

It produces a forwardable estimate: headline figure, cost table, all the options it
considered, and the assumptions stated as assumptions.

## The important part: it never books anything

Your corporate booking tool is a live booking system. Real money, real tickets, real
change fees. Letting an agent loose in one is a genuinely bad idea unless the
boundary is explicit, so the boundary is the first thing in the skill and it's
absolute:

> **Search and price only.** Never click `Continue` past fare selection, `Select
> hotel` into a booking funnel, `Book`, `Reserve`, `Hold`, `Confirm`, or anything on
> a traveller-details or payment page. Reading fares off a results page is safe.
> The results page is where you stop.

If a flow ever lands on a payment or traveller-details page, the skill stops and
tells you where it is rather than clicking its way back out. Every estimate it
produces states **"Nothing booked."**

## What makes it different

**It benchmarks the unbookable lines against your actual reimbursements.** Ground
transport, meals, and parking aren't in the booking tool, and this is exactly where
estimates get invented. The skill pulls totals from your own approved expense
reports for comparable trips and derives the figures from those — then labels them
"assumption" in the table rather than dressing them up as priced.

**It always surfaces a materially cheaper alternative**, even when that breaks your
stated airline or hotel preference. You get the trade-off — cost vs. proximity vs.
loyalty — and you choose. It won't silently optimise for price, and it won't
silently optimise for your preferences. Presenting one option as if it were the only
option is the failure mode it's built to avoid.

**It knows the DOM tricks that make these portals workable.** Enterprise booking
tools are old, slow, and hostile to automation. The skill carries the specific
patterns:

- **Date fields are hidden inputs behind a calendar widget.** Assigning `.value`
  directly is ignored by the framework — you have to go through
  `HTMLInputElement.prototype`'s native setter and dispatch `input`/`change`/`blur`
  yourself. Driving the visible calendar picker instead is flaky and slow.
- **Location controls are select2-style widgets** whose real `<select>` is
  `aria-hidden` and unclickable. You drive the visible proxy span.
- **Pick the airport option, not the metro/city option** — the city entry resolves to
  a different and much less useful inventory set.
- **Results take ~20 seconds.** Read the page text rather than snapshotting; the
  results table is huge and a snapshot burns context for nothing.
- **A search click that times out waiting for navigation usually submitted fine.**
  Retrying double-submits.
- **Don't reuse a deep link with a session token in it** — it expires and the symptom
  is a misleading "Cookies are disabled" page, not a session error.

**One gotcha worth the price of admission on its own:** when forwarding the estimate
over Teams, resolve the recipient by **UPN**, not by vanity SMTP alias.
`First.Last@company.com` works for mail and fails Teams chat creation with
`user_not_found`. That error looks like "this person doesn't exist" and isn't.

## How to use it

1. Ask for a trip estimate — "price up a two-day visit to the Orlando customer the
   week of the 26th".
2. Confirm your travel preferences the first time: home airport, preferred airline
   and hotel chain, cabin class your policy allows. It reuses these afterwards but
   re-confirms dates every run.
3. Watch it price flights and hotels, or don't — it writes the full working to a file.
4. Read the headline number and the one or two judgement calls it flags.
5. Optionally have it draft the message to your approver. It shows you the exact text
   and recipient and waits for confirmation before sending.

## Requirements

- Browser automation (Playwright) with an existing SSO session to your corporate
  booking tool. The skill never asks for credentials — if SSO isn't working it stops.
- Read access to your own mailbox, for the expense-report benchmarking step.
- The DOM selectors are written against Cytric/Amadeus-family portals. Concur Travel,
  Egencia, and similar tools use different field names — inspect once and substitute.
  The **techniques** (native setter, select2 proxy, long waits) transfer unchanged.

## Tips

- **Don't skip the home-airport confirmation.** Guessing it from your city silently
  produces a plausible, useless number when your metro has several airports.
- Ask it explicitly whether a rental car is likely. It's the most common reason an
  estimate comes in low.
- Prices drift daily. An estimate is a snapshot, and the skill says so in every
  output — re-run it if the trip is more than a couple of weeks out.
- The estimate contains your dates, destination, and customer. Treat it as private
  until you've decided to share it.

## Known limitations

- Estimates only. By design it cannot and will not book, hold, or confirm anything.
- Fares are not held. What it quotes today is not what you'll pay next week.
- Selectors are portal-specific and will need adjusting for a different booking tool.

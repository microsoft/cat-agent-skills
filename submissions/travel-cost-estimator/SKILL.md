---
name: travel-cost-estimator
description: Use this skill whenever the user needs a cost estimate for a business trip — including "what will it cost to get to X", "price up that customer visit", "I need a travel budget for the offsite", or a manager asking for a number before approving travel. Prices flights and hotels live from the company's browser-based booking tool, benchmarks the non-bookable lines against the user's own approved expense reports, and produces a forwardable estimate. Do NOT use this skill to actually book, hold, or confirm travel.
---

# Travel cost estimator

Produce a defensible trip estimate from **live fares and rates**, not guesses, and
present it so the user can forward or approve it in seconds.

The estimate has two halves. Flights and hotels come from the corporate booking tool.
Ground transport, meals, and parking are not in the booking tool, so they get
benchmarked against what the user has actually been reimbursed before.

---

## HARD GUARDRAIL — read this first

**The corporate booking tool is a live booking system. Real money, real tickets,
real change fees, real non-refundable segments.**

You are here to **search and price only.**

**Never click:** `Continue` past fare selection · `Select hotel` into a booking
funnel · `Book` · `Reserve` · `Hold` · `Confirm` · anything on a traveller-details
or payment page.

Reading fares off a **results page** is safe — results and the booking funnel are
separate pages, and the results page is where you stop. That line is the whole
guardrail.

If a flow ever lands on a page showing traveller details, payment fields, or a
confirm button: **stop immediately, do not click anything, and tell the user where
you are.** Do not try to navigate back out by clicking through.

Every estimate you produce must state **"Nothing booked."** explicitly.

---

## Step 0 — establish the traveller's preferences

Before the first search, confirm (or reuse from a previous run):

| | |
|---|---|
| Home airport | |
| Preferred airline / alliance | |
| Preferred hotel chain | |
| Cabin class permitted by policy | |
| Trip dates and destination | |
| Rental car likely? | |

Do not assume a home airport from the user's city — many metros have several, and
the wrong one silently produces a plausible, useless number.

Record these preferences so later runs skip this step, but **re-confirm the dates
every time.**

---

## Step 1 — reach the booking tool

Use the company's SSO entry point for the booking tool (commonly a corporate
shortlink or an intranet tile) so the existing session is reused.

**Two failure modes worth knowing:**

1. **Don't reuse a previously pasted deep link** containing a session token
   (`id=`, `_dp_=`, or similar). These are session-scoped and expire, and the
   symptom is misleading — you land on a generic *"Cookies are disabled"* error
   rather than a session-expired message. Go back to the clean entry point.
2. **Don't use the vendor's direct login URL.** It presents a username/password
   form with no SSO path. **Never ask the user for their credentials** — if SSO
   isn't working, stop and say so.

---

## Step 2 — price the flight

Navigate to the flight search. The DOM patterns below are typical of enterprise
booking portals (Cytric/Amadeus, and similar Concur/Egencia-family tools) and will
save a lot of wasted time:

**1. Origin and destination are comboboxes, not text inputs.**

```js
await page.getByRole('combobox', { name: /arrival location/i }).click();
await page.keyboard.type('Orlando');
await page.waitForTimeout(3500);           // suggestion lookup is server-side and slow
await page.getByRole('option', { name: /Orlando International \(MCO\)/i }).click();
```

Pick the **airport** option, not the city option. Metro-area city entries
(e.g. a city code covering several fields) resolve to a different, less useful
inventory set for air search.

**2. Airline filter is another combobox** — type the carrier, click the option,
then press `Escape` to close the dropdown. Leaving it open blocks the search button.

**3. Date fields are hidden inputs behind a calendar widget.** Clicking the visible
date label opens a date picker that is awkward and flaky to drive. Set the hidden
inputs directly with the native setter and dispatch the events the framework
listens for:

```js
await page.evaluate(({ depart, ret }) => {
  function setVal(name, value) {
    const el = document.querySelector(`input[name="${name}"]`);
    if (!el) return;
    const setter = Object.getOwnPropertyDescriptor(
      window.HTMLInputElement.prototype, 'value'
    )?.set;
    if (!setter) return;
    setter.call(el, String(value));
    ['input', 'change', 'blur'].forEach(e =>
      el.dispatchEvent(new Event(e, { bubbles: true }))
    );
  }
  setVal('air-departure-date-month', depart.month);
  setVal('air-departure-date-day', depart.day);
  setVal('air-departure-date-year', depart.year);
  setVal('air-return-date-month', ret.month);
  setVal('air-return-date-day', ret.day);
  setVal('air-return-date-year', ret.year);
}, { depart: { month: 8, day: 26, year: 2026 }, ret: { month: 8, day: 27, year: 2026 } });
```

Field names vary by tool — inspect once and reuse. The **technique** transfers even
when the names don't: assigning `.value` directly is ignored by React/Angular, so you
must go through the prototype setter and fire the events.

**4. Search, then wait ~20 s.** Results are genuinely slow. Read the rendered page
text rather than taking a full accessibility snapshot — the results table is large
and a snapshot wastes an enormous amount of context for no benefit.

**Capture per option:** flight numbers, departure and arrival times, stops, total
travel time, fare, and whether it is flagged **in policy**.

---

## Step 3 — price the hotel

Start from a **fresh session at the entry point** rather than back-navigating out of
flight results — back-navigation frequently restores a half-populated form.

**DOM patterns:**

1. **The location control is often a select2-style widget.** The real
   `select[name="location"]` is `aria-hidden` and cannot be clicked. Drive the
   visible proxy instead:

   ```js
   await page.locator('span.select2-selection[role="combobox"]').first().click();
   await page.keyboard.type('Orlando');
   await page.waitForTimeout(4500);
   await page.locator('li[role="option"], .select2-results__option').first().click();
   ```

2. **Dates use the same hidden-input pattern** as flights, typically named
   `date-range-from-*` and `date-range-to-*`.

3. **The search click may time out waiting for navigation.** That's usually fine —
   the form submitted and the page updated in place. Wait ~20 s and read the page
   rather than retrying the click, which can double-submit.

4. **Chain filters live in a facet list** and are often overlapped by a sticky
   header. Click with `{ force: true }`, then wait ~12 s for the results to refilter.

**Capture per option:** hotel name, brand, distance from the search point, nightly
rate, whether breakfast is included, and the in-policy flag.

---

## Step 4 — fill the non-bookable lines

Ground transport, meals, and parking aren't in the booking tool. **Benchmark them
against the user's own approved expense reports rather than inventing numbers** —
this is what makes the estimate defensible when a manager questions it.

Search the user's mail for their expense system's notification messages (approved
report summaries usually carry a report ID and a total). Pull the totals for
comparable trips — same trip length, similar destination type — and derive the
per-line figures from those.

Then state each non-bookable line **as an explicit assumption**, e.g.:

- Ground transport (rideshare, both directions)
- Meals (per diem x days)
- Airport parking (x days) — or omit if arriving by other means

Never present these as if they were priced. Label them "assumption" in the table.

**If a rental car is plausible, say so.** It moves the number materially and is the
most common reason an estimate turns out low.

---

## Step 5 — build the estimate

Write the full working to a file so it can be revisited, and keep the chat response
short.

Structure:

1. **Header** — customer or purpose, traveller, route, dates, and the date priced
2. **Recommended estimate** — a single rounded figure a manager can approve, with
   the cost table beneath it
3. **All flight options** — times, stops, fares, in-policy flags, plus your
   recommendation and the reasoning
4. **All hotel options** — preferred chain first, alternatives after
5. **Basis for the non-bookable lines** — which past reports you benchmarked against
6. **Caveats** — live pricing is not held, fares drift daily, **nothing booked**

### Two judgement rules

**Always surface a materially cheaper alternative, even when it breaks the stated
preference.** Give the trade-off — cost vs. proximity vs. loyalty status — and let
the traveller choose. Do not silently optimise for price, and do not silently
optimise for preference. Presenting one option as though it were the only option is
the failure mode here.

**Recommend the non-stop when the time saved is significant.** On a short trip a
modest premium that buys back hours in each direction is usually correct — but
present it as a choice with the delta stated in both dollars and hours, not as a
foregone conclusion.

---

## Step 6 — send it on (only when asked)

If the user asks you to forward the estimate to their manager or approver:

**Resolve the recipient by UPN, not by display alias.** A vanity SMTP alias
(`First.Last@company.com`) usually works for mail but **fails for Teams chat
creation with `user_not_found`** — Teams resolves on the UPN
(`flast@company.com`). Look the UPN up rather than guessing, and don't conclude the
person doesn't exist when the alias fails.

**Show the user the exact message and recipient, and get explicit confirmation
before sending.** A travel estimate contains the user's dates, destination, and
customer — treat it as private until they say otherwise.

Message shape — keep it to a screen:

- One line of context (purpose, dates)
- **The headline number, in bold**
- The cost table
- The one or two judgement calls, stated as explicit questions rather than buried
  in prose
- "Fares are live as of today and in policy. **Nothing booked yet.**"

Approvers want the number and the options, not the process.

---

## Output style

Lead with the number. Put the trade-offs where they cannot be missed. Never present
a single option as if it were the only one. Always state that nothing was booked.

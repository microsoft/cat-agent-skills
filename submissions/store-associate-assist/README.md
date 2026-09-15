# Store Associate Assist

For the store associate on the floor with a customer in front of them and a question that
spans a category no one person can master — product, policy, promotion, procedure.

It takes the question with store, role and department context, retrieves the applicable
policy, product attributes and current promotion, resolves the policy and compares products
deterministically, and returns a cited answer — or a drafted escalation when the answer is
not in scope.

## How it works

1. Takes the question with store, role and department context.
2. Retrieves the applicable policy, SOP and product sources.
3. Builds the side-by-side comparison (deterministic).
4. Checks the current promotion, price and eligibility (deterministic).
5. Drafts the cited answer or the escalation.

The policy resolution and product comparison come from deterministic engines; the model
retrieves, orchestrates and writes the cited prose.

## Example scenario

Price-match pressure, with the customer standing there. Three things the documents settle:

- The **exclusion clause outranks the general one** — marketplace and third-party sellers are
  excluded, and the answer cites the clause rather than the general policy.
- The bundle promotion **ended one day before**, and the eligibility test names the failing
  leg with exact dates.
- Price execution stays a manager action, so the draft gives the associate the script *and* a
  manager escalation.

A naive assistant matches the price because "the old manager did". This one cites why not.

## What you bring

Store SOPs and the employee handbook, returns and price-match policy, a PIM or catalog
extract, promotion packs, and planogram notes.

## Boundaries

Answers and drafts only. It never overrides a price, authorises a refund, reserves inventory
or changes a schedule.

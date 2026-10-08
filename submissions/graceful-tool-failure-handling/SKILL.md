---
name: graceful-tool-failure-handling
description: >-
  Use this skill whenever a tool call, connector, API request, or file
  operation fails, times out, or returns an unexpected result, before
  deciding how to respond to the user. Applies any time a needed capability
  isn't available or doesn't behave as expected.
---

When something doesn't work, say exactly what happened and offer a real
path forward. Never continue as if it worked, and never go silent about it.

## Instructions

1. When a tool call fails, times out, returns an error, or returns something
   that doesn't look like what was expected, stop and notice it rather than
   proceeding on an assumption about what it probably would have returned.

2. Tell the user plainly: what was attempted, what happened instead, and
   whether it's worth retrying. Match the framing to the failure, a timeout
   might be worth one retry, a permissions error usually isn't going to
   resolve itself on retry, a "not configured" state needs setup, not a
   retry.

3. Never fabricate a result to fill the gap left by a failed tool call. If a
   ticket-creation tool fails, don't present a plausible-looking ticket
   number. If a search returns nothing, don't answer as if it had returned
   something. The honest response is "this didn't work" plus what's known
   without it, not a smoothed-over answer that hides the failure.

4. Distinguish a capability that failed from a capability that was never
   available in the first place. "The connector isn't configured on this
   platform" and "the connector is configured but returned an error" call for
   different responses: the first needs a setup step from an admin, the
   second might just need a retry or a different approach.

5. Offer the best available fallback: a manual version of what the tool would
   have done, a different tool that can accomplish the same goal, or a clear
   statement of what the user needs to do themselves. Don't just report the
   failure and stop there if there's a reasonable way to still help.

6. If a task depends on a chain of tool calls and one partway through fails,
   report exactly how far it got and what's now in an incomplete state,
   rather than presenting the whole task as either fully done or fully
   failed when the truth is in between.

7. For a task that already has some safe, completed side effects (a file was
   created before a later step failed), say what already happened so nothing
   gets silently duplicated or left in an inconsistent state on a retry.

## Guardrails

- Never present output that depended on a failed tool call as if the call had
  succeeded.
- Never invent an ID, confirmation number, or result that a tool didn't
  actually return.
- Don't apologize excessively or dwell on the failure. State it once, clearly,
  and move to what can still be done.
- Don't silently retry an operation that has side effects (creating,
  sending, or deleting something) without telling the user a retry is
  happening, in case the first attempt actually succeeded despite an
  ambiguous error.

## Tone

Direct and unbothered. A tool failure is routine information to relay, not
something to be defensive or overly apologetic about.

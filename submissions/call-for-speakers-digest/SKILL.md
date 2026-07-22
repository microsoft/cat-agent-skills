---
name: call-for-speakers-digest
description: >-
  Weekly digest of open conference Call for Speakers (CFP) opportunities
  matching the person's topics of interest, delivered as an HTML email.
  Use this skill when someone asks to be notified about speaking
  opportunities, wants a recurring CFP digest, asks "what conferences are
  taking submissions right now", or wants to set up a weekly speaker
  opportunity search. Also use on the skill's own recurring weekly run to
  refresh the digest, and when the person wants to update their topics,
  location or format preferences, or exclude a conference they're already
  committed elsewhere for.
---

# Call for Speakers Digest

## Compatibility

Requires web search. Building the HTML digest in Copilot Studio specifically requires Code Interpreter enabled on the agent, printing raw HTML into the chat as text won't render it. Sending the digest as an actual email requires a connected email tool (Gmail, Outlook). Without Code Interpreter or an email tool, present the finished digest as plain formatted chat text instead and say so plainly, don't pretend it was sent or rendered as a file when it wasn't.

## Step 1: Build the speaker profile (first run only)

Ask for, and remember, this profile so it doesn't need to be re-collected every week:

1. **Topics** — the technologies, subject areas, or themes they want to speak about (e.g. "Copilot Studio, Power Platform, AI agents"). This is the one required field.

1b. **Check whether the topics collectively sit inside one bigger platform or ecosystem, and offer to broaden to it.** People naming specific products they work in day to day usually won't think to say "and treat this as shorthand for the whole platform," that's your job to notice, not theirs to volunteer. If the topics given all live under one identifiable umbrella (Copilot Studio, Copilot Cowork, and Agent 365 are all Microsoft 365, for example), say so plainly and ask whether to search that entire ecosystem rather than staying narrow to just the named products, since a huge amount of genuinely relevant content lives at conferences and events branded at the platform level rather than the specific-product level, and staying narrow risks silently missing most of it. If they say yes, ask if there's anything within that ecosystem they specifically want excluded (using the Microsoft 365 example: someone focused on Copilot Studio and Agent 365 likely doesn't want Teams-only or device-management/Intune content, even though those are technically part of the same platform). Remember both the broadened scope and any exclusions as part of the profile.

If they'd rather stay narrow to just the named topics, that's a legitimate choice too, don't push, just make sure they've actually been offered the broader option once so it's an informed choice rather than a default they never got to consider.

2. **Format preference** (optional) — in-person, virtual, hybrid, or no preference.
3. **Travel willingness** (optional) — domestic only, will travel internationally, or virtual-only. Matters for filtering out events that don't fit.
4. **Anything to exclude** (optional) — conferences they're already committed to, already spoke at recently, or specifically don't want surfaced.
5. **Known community hubs** (optional) — if they already know of a community-specific site or event series in their space (the way Microsoft's ecosystem has communitydays.org), ask once and remember it as a standing source to check every week, on top of the general ones in Step 2. Don't make them repeat this.

On every run after the first, don't re-ask all of this. Just check in briefly: "Still want [topics/scope], or should I update anything?" and proceed with the remembered profile if they don't respond with changes.

## Step 2: Search for open CFPs

Check **every** source below, every single run, and treat this as a minimum, not a target to stop at once reached: a distinct search or page fetch for each of the browsable aggregators, targeted searches against community hubs (see below for why "fetch the hub page" doesn't always work), a site-specific search on Sessionize and run.events for each topic, and at least one broadened-term general search per topic. For a profile with 2-3 topics, that's easily 10+ separate searches or fetches before you're done, not 2 or 3. If your final list has fewer than about 5 open CFPs, that's a signal something got skipped, go back and check which of the sources below you didn't actually hit before finalizing.

**Some sites are JavaScript-rendered and won't give you real data if you fetch the page directly.** A direct fetch of a listing/search page sometimes returns just a page shell, filter controls, a loading spinner, no actual list content, because the real data loads client-side after the page renders. If a fetched page looks like that (filter UI but no actual entries, or a visible loading indicator), don't trust it as "no results," it means that page can't be fetched directly and you need to search it instead. Individual item pages on these same sites are usually still fully indexed and readable even when the aggregate listing page isn't, fetching a specific event's own URL directly works fine even on a site whose listing page doesn't.

**Browsable aggregators** (check these directly, they track CFP deadlines themselves):
- **confs.tech/cfp** — community-maintained conference list, filterable by topic, includes exact CFP close dates.
- **papercall.io/events** — public open-CFP listing with close dates.
- **adatosystems.com/cfp-tracker/** — actively-maintained, sortable table of open CFPs across general tech (leans DevOps/cloud/security/data, but broad), with event dates, CFP close dates, and direct links.
- **cfpradar.dev** — actively-maintained CFP aggregator, ranks and matches by topic fit, covers general tech through niche community events.
- **sessionize.com/user-groups** — a genuine public, paginated directory (300+ entries) specifically for recurring user groups and meetups, filterable by "Open CFP" and keyword. This is a real exception to the Sessionize rule below, don't skip it, it's a strong source for regional/community meetup CFPs and reads fine on a direct fetch. It only covers recurring meetups though, not one-off annual conferences, those still fall under the search-only rule below. Don't manually page through all of it, use the page's own keyword search and "Open CFP" filter, or a scoped web search like `site:sessionize.com/user-groups [topic]`, to jump straight to relevant entries.

**Community-specific hubs** — if the person's topics point to a specific professional community, check whether that community has a dedicated hub site the way Microsoft's ecosystem does:
- **communitydays.org** — covers M365 Community Days events (Microsoft 365, Power Platform, Copilot, Viva) globally. Its events listing page is JavaScript-rendered and won't return real data from a direct fetch, search it instead: `site:communitydays.org "call for speakers"` plus each topic. Individual event pages found this way (e.g. `communitydays.org/event/...`) are fully readable directly, that's where the actual CFP link and close date live, on the event's own page, not the listing page.
- If the topics point somewhere else (security, data engineering, a specific language community, etc.), search for whether an equivalent hub exists for that community rather than assuming confs.tech and Papercall cover everything, they skew general web/dev and miss plenty of vertical communities.

**Submission platforms with no public browse page** — these host individual standalone conferences' CFPs but don't offer a central list for that event type, don't try to browse them, search them the same way you'd search anything else:
- **Sessionize, for standalone conferences** (not the user-groups directory above): `site:sessionize.com "call for speakers" [topic]`
- **run.events**: `site:run.events "call for speakers" [topic]` (used by events like European Collaboration Summit)

**General web search** per topic, formatted like `"[topic]" "call for speakers" <current year>` (and optionally also `"[topic]" "call for speakers" <next year>`), or `"[topic]" CFP deadline`, to catch anything the above miss entirely.

**For every topic, identify the broader ecosystem or platform it belongs to, and search under that umbrella too, not just the literal topic string.** This matters more than naming lag on new products, community events are frequently branded at the ecosystem level even when individual sessions cover a much narrower thing someone actually cares about. A conference branded "Microsoft 365 Summit" or "SharePoint Conference" can easily have Copilot Studio or Agent 365 sessions in it without ever using those words in its own name or general marketing. Searching only the exact topic strings will systematically miss this entire category of genuinely relevant events, it's not a rare edge case.

Work out the umbrella terms yourself using what you know about each topic (don't ask the person to enumerate these, that's your job): if someone's topic is "Copilot Studio," the umbrella includes things like "Microsoft 365," "SharePoint," "Power Platform," "Microsoft Foundry," and "Copilot for M365." If someone's topic is a Kubernetes operator, the umbrella includes "CNCF," "Cloud Native," "Kubernetes" more broadly. Search both layers, the specific topic and the umbrella it sits in, every run. When a result only matches at the umbrella level, use judgment about whether the event plausibly covers the narrower topic (a general "Microsoft 365 Summit" likely does touch Copilot content; a "SharePoint permissions deep-dive" meetup probably doesn't), and don't discard something just because you're not 100% certain, note the uncertainty in the digest instead of silently dropping it.

**If the profile includes a broadened ecosystem scope from Step 1b, actually search that ecosystem's name directly** (e.g. "Microsoft 365 call for speakers"), not just the original narrow topics plus inferred umbrella terms, and apply whatever exclusions were captured (skip Teams-only or device-management content if that's what got excluded, for instance). This scope also covers platform-wide, product-agnostic conference brands that don't map to any single named topic at all, things like TechCon365 or PowerCon in the Microsoft space, which cover the whole platform rather than one product. Check for these by name specifically, and if a known one is currently between CFP cycles (last one closed, next one not yet open), don't drop it, note it in the digest as "not open yet, worth watching" so it doesn't silently disappear from consideration until its next call happens to open.

For each candidate, confirm the CFP is genuinely still open (deadline in the future relative to today) before including it. Discard anything already closed, don't include it "for reference."

## Step 3: Extract details, don't guess at them

For each open CFP, pull:

- Event name and a direct link to the CFP submission page (not just the conference homepage)
- CFP close date
- Event dates
- Format: in-person, virtual, or hybrid, plus city if in-person/hybrid
- Speaker benefits, if the CFP page states them (travel covered, hotel covered, honorarium, free ticket). **If the page doesn't say, write "not specified," don't assume benefits exist or don't exist.**

**Every one of these details comes from actually opening and reading that specific event's current listing, never from what you already know about the conference from a previous year.** Recurring community and regional events change host city, dates, and sometimes name year to year, often every single year. Confusing this year's instance with last year's, or one regional chapter with a similarly-named one (e.g. mixing up two different regional instances of the same conference series), produces a confidently wrong answer that looks correct, which is worse than an obvious gap. If you're not looking at the live page for that exact event instance right now, don't state a detail as fact.

Apply the profile's filters (format preference, travel willingness, excluded events) before finalizing the list. If a detail is genuinely unclear from the source page, say so in the digest rather than filling the gap with a plausible-sounding guess, the same rule any legitimate research skill should follow.

## Step 4: Don't repeat the same CFP every week for no reason

Keep a running record of which CFPs have already appeared in a previous digest (event name + CFP link is enough to key on). Don't re-list something that already went out unless its deadline is now inside the final 7 days, that's worth a "closing soon" resurfacing even if they've seen it before. Otherwise, only genuinely new listings belong in this week's digest.

## Step 5: Build the HTML digest

Structure:
- A one-line header: how many open CFPs matched this week, and the date range covered.
- Sort by CFP close date, soonest first. Anything closing within 7 days should be visually distinct (bold, a colored badge, whatever's simplest, "Closing soon" is the point).
- One entry per CFP: event name (linked to the actual CFP page), close date, event dates, format + location, speaker benefits, and a short one-line note tying it back to why it matched their topics.
- Keep the HTML simple and email-client-safe: inline styles, no external stylesheets or web fonts, table-based layout if you want reliable rendering across email clients rather than modern CSS flex/grid, which many email clients still don't support well.

## Step 6: Deliver it

If an email tool is connected, send the digest to the person's own address (confirm which address the first time, then reuse it). If nothing is connected, deliver the digest as an HTML file **only if** the current runtime supports writing/attaching files; otherwise, present the digest as formatted chat text and say plainly that it wasn't sent.

## Step 7: Set up the weekly cadence

This skill doesn't schedule itself, recurring/scheduled task support depends on the platform it's running in. The first time you run this, check whether the current platform has a way to schedule a recurring task (Cowork and Scout both do), and if so, tell the person to set this skill up as a weekly recurring task (their choice of day) rather than triggering it manually every time. If the platform has no such feature, say so plainly and let them know they'll need to trigger it themselves each week instead.

## A few things to keep in mind

- If zero CFPs match this week, say that plainly in a short digest rather than skipping the email entirely, "nothing new matched your topics this week" is a legitimate and useful message.
- If the person's topics are very narrow and search keeps coming up empty over several weeks, say so and offer to broaden the topic list, don't keep silently returning nothing.
- Keep the tone factual and scannable, this is meant to be read in under a minute, not a newsletter.

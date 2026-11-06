# KYC Research Pack: final self-check

SKILL.md step 9. Run it after the artifact and the chat reply are drafted and before
either is delivered. The lint script enforces what a script can see; the rest is read
here, item by item.


**Run the linter first** (`house-rules.md` § 13). Save the artifact text and the chat reply
you are about to send (for example `reply.md`), then run
`python scripts/lint_deliverable.py <artifact> --reply reply.md --searches searches.md`, where
`searches.md` logs every document each search returned, one `HIT | <query> | <document> |
used`, `rejected (Gn)`, `duplicate (Gn)` or `set aside` line each, incidental hits included, plus one
`REQ | <source> | ok`, `failed` or `not attempted` line per request (`house-rules.md` § 13). Fix every `ERROR`, resolve every
`CHECK` (cite its (Gn) or (Dn), or confirm it is a listed exception), and run it again until it
prints `ERROR: 0`. It flags each line and cell that breaks the checks below; still run the
checks it cannot judge (fact sentence or gap sentence, interpretation, data minimisation).
Then rebuild any `.docx` or `.xlsx` from the fixed text and send the fixed reply.

The last step before counting (`house-rules.md` § 4 and § 9). The Open items list is the
G-list; the Determinations outstanding list is the D-list.

1. **List every gap mentioned anywhere**: the chat reply, the artifact (including Notes
   columns, handling notes, and marker cells), and the footer. Confirm each has a G-bullet;
   add any missing.
2. **Marker-token grep.** Grep the artifact, the chat reply, and the footer, outside the
   G-list, for every marker token: `NOT FOUND`, `NOT RETRIEVED`, `GAP`,
   `NEEDS FEED`, `NOT LEGIBLE`, `UNRESOLVED MATCH`, `AS OF`, `PROPOSED - not in force`,
   `DRAFT - not approved`, and `PENDING CODIFICATION`.
   Confirm a (Gn) follows each hit; where none does, add the G-bullet and the ID. Grep
   `NOT DETERMINED` the same way for its (Dn), summary prose in the chat reply and memo
   included; cite the Dn or rephrase without the token. The D-list intro line is the only exception.
3. **IDs resolve both ways.** Every (Gn) and (Dn) cited exists in its list; every G-bullet is
   cited at least once or stands alone as the only record of its shortfall.
4. **Fact cells carry no marker.** A cell the outline does not list as a marker cell states
   the source in plain words (`none stated in <source>`); rewrite any marker token there.
5. **Each G-bullet holds one shortfall and leads with its marker**, naming the source
   searched. Split any bullet holding two. One instrument's PROPOSED status, or one document's
   DRAFT status, is one G-bullet naming every row it applies to; merge duplicates.
   One G-bullet holds one shortfall about one source. A rejected or unopened document mentioned
   inside a deferral bullet gets its own bullet. An incidental hit you considered and rejected
   also gets `GAP - scope mismatch, not a candidate: <doc> (Gn)`; one unrelated by title and
   unopened is `set aside` in the log only (`house-rules.md` § 4). Rejected candidates come
   last in the G-list; the chat reply leads with at most five findings.
6. **Each D-bullet holds one decision and the token.** Each reads
   `Dn - NOT DETERMINED - <one question> - <decider> decides`; add the token to any
   D-bullet that names a decider without it. Grep each D-bullet for " and ", " or ", "/", and a
   second question mark; split every bullet joining two decisions into its own D-numbers.
   Name one decider per bullet. Every UNRESOLVED MATCH disposition is its own D-bullet.
   The D-list opens with exactly
   `Decisions outstanding (each NOT DETERMINED below cites its own Dn):`,
   never merged with an outline heading, and with no other marker line.
   Where the request names a decision body (for example "the onboarding committee"), the
   decider is still the compliance owner, with the body mentioned as
   "(for the onboarding committee)" (`record-outline.md` § 8).
7. **Footer counts equal the list counts**: G-bullets per marker type, D-bullets for
   `NOT DETERMINED`.
8. **Hedge-word grep.** Grep the chat reply and the artifact for the likelihood and hedge
   words listed in `house-rules.md` § 2 and rewrite every hit on a determination statement.
   Rewrite every "likely" wherever it is written, including descriptions of sources, for example
   "a candidate source (Dn)".
9. **Gap-sentence grep.** Grep the chat reply, the artifact (notes and reasoning cells
   included), and the footer for the gap phrases in `house-rules.md` § 4 ("Every gap sentence
   cites its ID"):
   `not retrieved`, `retrieval not attempted`, `not opened`, `did not return`,
   `returned nothing`, `not found`, `no record`, `not located`, `none located`,
   `none retrieved`, `not provided`, `not configured`, `not stated`, `states no`,
   `not verified`, `unverified`, `not performed`, `not checked`, `not covered`, `out of scope`,
   `incomplete`, `omitted`, `extract`, `excerpt`, `unidentified`, `does not mention`,
   `rejected`, `nothing responsive`, `does not address`, `did not cover`, `could not locate`,
   `not mapped`, `undated`, `skipped`, `withheld`, `not needed`, `none found`,
   or `no candidate`.
   A sentence reporting what a source contains, or what this artifact records, is a fact
   sentence and needs no ID. Every other hit cites a (Gn) or (Dn) in the same sentence, or is a decline of the
   request, a statement of what the skill never does, or verbatim quoted source text; otherwise
   add the bullet and cite it. A file withheld under data minimisation reads
   `GAP - not opened: <file> withheld under data minimisation (Gn)`, with nothing asserted about
   its contents.
   Re-read the sentence after every ID-bearing sentence: if it contains a gap phrase, it
   carries its own (Gn) or (Dn), in the chat reply, memo, and cells alike.
10. **`[covered entity]` grep.** Where the rule's definitions section is not retrieved (either form, `house-rules.md` § 2), grep
    the artifact (title line included) and the chat reply for `institution`, `institutions`, `firm`, `firms`, `bank`, `banks`, `broker`, `dealer`,
    `covered financial institution`, and `financial institution`.
    Replace every hit inside a quote or paraphrase of what the rule requires or whom it binds
    with `[covered entity]` (`house-rules.md` § 2). The user's own named entities stay.
11. **One connector, one bullet.** Each unconfigured connector is its own `NEEDS FEED`
    G-bullet. Split any G-bullet joining two shortfalls with ";" or " and ", and any D-bullet
    asking about two paragraphs.
12. **No negated marker.** Rewrite any negated marker token ("not PENDING CODIFICATION") as
    the positive result, for example `Result: forthcoming change`.
13. **Dates.** Every day count says `calendar days` or `business days`, the day part of a
    compound figure included (`6 months 15 calendar days`). In every date table, a
    row with no calendar date leads with `NOT FOUND - ... (Gn)`. A deferred ladder has one
    `NOT FOUND` G-bullet per missing date per candidate instrument.
14. **Targeted checks** (`house-rules.md` § 4 and § 5): one G-bullet per rejected document;
    `NOT RETRIEVED` only for a source requested; no non-existence claim; no guessed owner;
    every relative deadline in the chat reply quoted or labelled with its unit; an adjectival
    form such as "180-day" is quoted with its paragraph number or labelled "180-calendar-day".
    Also: no superseded version's in-force span unless a document prints it (a `Supersedes`
    line or a review period never supplies one, `house-rules.md` § 5); every pair of sources
    that disagree has its `GAP - conflicting sources` bullet; every location a source names
    has its own outcome or `GAP - <location> retrieval not attempted (Gn)` bullet; every
    absence bullet leads with `NOT FOUND`; a draft or superseded document names its control
    of record; a SAR decline reads only `<category> withheld under data minimisation.`; no
    rejected hit carries a private name, title, or URL path; month and year forms are quoted;
    no "will require you to"; every search hit in `searches.md` is named in the artifact as used, has
    its own `GAP - scope mismatch, not a candidate` bullet, or is `set aside` and counted in the
    Coverage line (walk the log, not the artifact);
    every summary-block count counts rows or obligations, not G-bullets;
    and nothing anywhere, chat reply included, says a rule or document "has not
    been published" or "does not exist" (`house-rules.md` § 3 and § 4).

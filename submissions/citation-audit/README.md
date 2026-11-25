# Citation Audit

Citation Audit checks a draft against source files you supply. Every factual claim is marked SUPPORTED, PARTIAL, UNSUPPORTED, or STALE, with the source span, a score, and a SHA-256 manifest of the files that were read.

The bundled Python scripts assign the verdicts. The agent splits the draft into claims and reports the ledger. It does not grade its own confidence, and it does not edit the draft.

## Before you start

Python 3 reads Markdown, plain text, HTML, and Word `.docx` with the standard library.

PDF text is read only when `pdfplumber`, `pypdfium2`, or `pypdf` is already installed. The skill does not install packages and does not fetch sources over the network.

Two inputs are required: the draft, and the files it is supposed to rest on. If the source files are missing, the audit stops and does not certify the draft.

## How to use it

Ask to verify a draft, check its citations, or confirm that its claims appear in the sources. Give the agent the draft and those source files.

From the skill directory, ingest the files first:

```bash
python scripts/ingest_draft.py --draft draft.md --source policy-2025.md --out corpus.json
```

Repeat `--source` once for each source file. Then write `claims.json` with one fact per item (`id`, `text`, `type`, `location`). `type` is `quantitative`, `quotation`, `attribution`, `paraphrase`, or `causal`. To see sentence candidates before editing that file:

```bash
python scripts/verify_spans.py --corpus corpus.json --segment --claims-out claims.json --out verdicts.json
```

Split any candidate that states two facts, then verify the edited file and build the ledger:

```bash
python scripts/verify_spans.py --corpus corpus.json --claims claims.json --out verdicts.json
python scripts/build_ledger.py --corpus corpus.json --verdicts verdicts.json --claims claims.json --out-dir .
```

The run writes:

- `claim-ledger.html`, with blockers before the full table
- `claim-ledger.csv` and `claim-ledger.xlsx`, with the same rows
- `audit_manifest.json`, with each verdict, score, and a SHA-256 of the draft, every source, and the claim list

When those names already exist, the next run uses `-v2`, `-v3`, and so on.

## How to read a verdict

SUPPORTED means the wording is a near-exact span in the corpus and the numbers and units match. It means the supplied files contain the claim. It does not mean the claim is true outside those files.

PARTIAL is string overlap from 0.75 up to 0.95. The words are close. The score is not a judgement that the source entails the sentence. The cutoffs are fixed in version 1.0.0.

UNSUPPORTED means no span reached 0.75, or the sources disagree and neither date is strictly newer.

STALE means a span matches the claim and a different source, with a strictly newer date, disagrees on a number or a negation. The date comes from a labeled line (`as of`, `updated`, `effective`, `revised`, `dated`) or from the filename. A date mentioned only in the body is not used.

The same files and the same `claims.json` produce the same manifest. A new claim list can change the ledger, because splitting claims is not part of the verifier.

## Where this skill stops

Content Quality Auditor and Blog Content Auditor score clarity and structure. Deliverable Quality Gate runs a professional-services release review. Global Greenwashing Claim Auditor screens environmental marketing claims. Agent Red Team tests an agent you own. Citation Audit does not do those jobs.

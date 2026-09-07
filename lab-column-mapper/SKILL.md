---
name: lab-column-mapper
description: Use this skill when a Power Automate flow triggers the agent with a payload describing an unknown source column from a lab results file that broke an Azure Data Factory ingestion pipeline. The skill semantically matches the source column against the canonical clinical schema indexed in Azure AI Search, scoped first by the sending lab and then by clinical domain, and writes a suggested destination-column mapping to the Dataverse review queue for a clinical informatics steward to approve. Also activates on manual invocations like "map this lab column", "the ADF pipeline failed on column X, what should it map to", or "suggest a canonical column for this lab feed field".
---

# Lab Column Mapper

## What this skill does

Given an unknown column from an incoming lab results file, retrieve the most likely canonical destination column from a health system's clinical warehouse, explain why, and write the suggestion to the review queue.

## Input payload

The skill is invoked with a JSON payload delivered by Power Automate. Every field is required unless marked optional.

| Field | Type | Description |
|---|---|---|
| `source_column_name` | string | The unrecognized column header from the incoming file (e.g., `PT_MRN`, `spec_collected_dt`). |
| `source_column_sample_values` | array of strings | Up to 5 sample values, de-identified. **Never include raw PHI — the caller must hash or redact patient identifiers before invoking.** |
| `source_lab_id` | string | Stable identifier for the sending lab (e.g., `LAB-QUEST-001`). |
| `source_lab_name` | string | Human-readable lab name (e.g., `Quest Diagnostics`). |
| `source_file_name` | string | Name of the file that failed ingestion. |
| `source_domain` | string | One of `lab-observations`, `orders`, `specimens`, `results`. Used to scope the search. |
| `pipeline_run_id` | string | ADF pipeline run ID for traceability. |
| `source_column_description` | string, optional | If the sending lab publishes a data dictionary, the human description of the column. Boosts match confidence significantly when present. |

## Retrieval steps

Perform these steps in order. Do not skip to a broader search until the previous scope has been tried.

### Step 1 — Same-lab scoped search

Query the Azure AI Search index `lab-canonical-schema` with:

- **Search text:** `source_column_name` + `source_column_description` (if present) + a synthesized query from the sample values (e.g., if samples look like dates, add "date time timestamp"; if samples look like numeric with units, add "quantity measurement value").
- **Filter:** `source_lab_id eq '{source_lab_id}' or previously_mapped_from_labs/any(l: l eq '{source_lab_id}')`
- **Top:** 5
- **Semantic ranking:** on. Use the `column-descriptions` semantic configuration.

If the top result has a `@search.rerankerScore` ≥ **2.5**, accept it as the primary suggestion and go to Step 3.

### Step 2 — Same-domain broader search

If Step 1 returns no result at or above the threshold, re-query with:

- **Same search text.**
- **Filter:** `clinical_domain eq '{source_domain}'`
- **Top:** 8
- **Semantic ranking:** on.

Accept the top result at `@search.rerankerScore` ≥ **2.2** as the primary suggestion. Capture the next 2 candidates as alternatives.

If no result clears the threshold, produce a `no_confident_match` outcome (see Step 3) and let the human decide from scratch.

### Step 3 — Format the suggestion

Build a suggestion record with this schema:

```json
{
  "suggestion_id": "<new GUID>",
  "pipeline_run_id": "<from payload>",
  "source_column_name": "<from payload>",
  "source_lab_id": "<from payload>",
  "source_lab_name": "<from payload>",
  "source_file_name": "<from payload>",
  "suggested_destination_column": "<canonical column name, or null if no_confident_match>",
  "suggested_destination_loinc": "<LOINC code if the canonical column has one, else null>",
  "confidence": "high | medium | low | no_confident_match",
  "confidence_score": <0.0 to 1.0, derived from the rerankerScore normalized>,
  "reasoning": "<one to two sentences citing WHICH signals drove the match — description match, sample-value shape, prior mapping history for this lab>",
  "alternatives": [
    { "destination_column": "<name>", "confidence_score": <0.0 to 1.0> },
    { "destination_column": "<name>", "confidence_score": <0.0 to 1.0> }
  ],
  "status": "pending_review",
  "created_at": "<ISO-8601 UTC>"
}
```

Confidence bands from `@search.rerankerScore`:

- `>= 3.0` → `high`, `confidence_score = min(1.0, rerankerScore / 4.0)`
- `2.5 – 2.99` → `medium`
- `2.2 – 2.49` → `low`
- `< 2.2` → `no_confident_match`, `suggested_destination_column = null`

## Write to Dataverse

Call the `lab_column_mapping_suggestions` table's Create action via the Dataverse connector with the suggestion record. Return the new record ID to the caller so Power Automate can notify the clinical informatics steward.

## Response to the caller

Return this JSON to Power Automate:

```json
{
  "suggestion_id": "<the ID>",
  "review_url": "<Power App URL for the steward, if configured; else null>",
  "summary": "<one-line human-readable summary — 'PT_MRN → patient_mrn (high confidence)' or 'No confident match found for PT_MRN — manual review required'>"
}
```

## Interaction guardrails

- Never invent a destination column. Only propose columns that appear in the Azure AI Search index. If nothing clears the low threshold, emit `no_confident_match` and let a human decide.
- Never propose a mapping that would change data type incompatibly (e.g., mapping a text column to a date column). Check the `data_type` field on the index result before finalizing the suggestion.
- Never include raw sample values from the payload in the `reasoning` field. Describe the *shape* of the values ("looks like an ISO date"), not the values themselves.
- If the payload is missing required fields, respond to Power Automate with an error object `{ "error": "missing_field", "field": "<name>" }` and do not query the index.
- If Azure AI Search returns an error, retry once with exponential backoff (1s, then 2s). If it still fails, write a stub suggestion with `status = "search_unavailable"` and surface it for human review.
- Do not auto-approve. This skill only *suggests* — approval belongs to the clinical informatics steward.

## References

- Canonical schema documentation and index configuration: see `README.md` in this skill package.
- LOINC (Logical Observation Identifiers Names and Codes): https://loinc.org/
- Azure AI Search semantic ranking: https://learn.microsoft.com/azure/search/semantic-search-overview
- Dataverse connector for Power Automate: https://learn.microsoft.com/power-automate/dataverse/overview

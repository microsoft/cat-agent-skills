# Lab Column Mapper

**Author:** [Rafsan Huseynov](https://www.linkedin.com/in/rafsanhuseynov) — AI Solution Architect, Microsoft MVP
**Platform:** Copilot Studio
**Version:** 1.0.0

A Copilot Studio skill that resolves **schema drift** in a health system's lab results ingestion pipeline. When a new column header shows up in a lab feed that Azure Data Factory doesn't know how to map, this skill semantically matches it against the canonical clinical schema and proposes a mapping for a clinical informatics steward to approve.

## Why this exists

A regional health system typically ingests lab results from many external sources: national reference labs (LabCorp, Quest, Mayo Clinic Labs), hospital-owned labs, specialty labs (pathology, molecular diagnostics, genomics), and point-of-care device vendors. Every lab sends result files (CSV, Excel, or delimited text) with slightly different column headers for the same clinical concept:

- `patient_mrn` vs `medical_record_number` vs `pat_id` vs `subject_identifier`
- `loinc_code` vs `test_code` vs `analyte_id` vs `assay_code`
- `result_value_numeric` vs `observation_value` vs `numeric_result` vs `qty`
- `collection_datetime` vs `specimen_collected_at` vs `sample_drawn_time`
- `abnormal_flag` vs `interpretation` vs `result_flag` vs `abn_ind`

The canonical warehouse table has one standard name per concept, typically anchored to **LOINC** codes for the test itself. When a lab adds a new panel, upgrades their LIS, or a new lab is onboarded, the incoming file has column names the pipeline has never seen. Azure Data Factory fails the load. Without this skill, a data engineer manually reads the file, guesses the mapping, updates the ADF mapping table, and reruns the pipeline — often with a 24-hour delay.

This skill automates the *suggestion* step. A clinical informatics steward still approves before anything hits SQL.

## Architecture

```
┌──────────────────┐        ┌──────────────────────┐        ┌────────────────────┐
│ Lab file arrives │───────▶│ Azure Data Factory   │───────▶│ SQL clinical       │
│ (CSV / Excel)    │        │ ingestion pipeline   │        │ warehouse          │
└──────────────────┘        └──────────┬───────────┘        └────────────────────┘
                                        │
                                        │ (on unknown column)
                                        ▼
                            ┌──────────────────────┐
                            │ Power Automate flow  │
                            │ (failure handler)    │
                            └──────────┬───────────┘
                                        │
                                        ▼
                            ┌──────────────────────┐        ┌────────────────────┐
                            │ Copilot Studio agent │───────▶│ Azure AI Search    │
                            │ (this skill)         │◀───────│ canonical schema   │
                            └──────────┬───────────┘        │ index              │
                                        │                    └────────────────────┘
                                        │ (writes suggestion)
                                        ▼
                            ┌──────────────────────┐        ┌────────────────────┐
                            │ Dataverse review     │◀──────▶│ Clinical informa-  │
                            │ queue                │        │ tics steward (via  │
                            │                      │        │ model-driven app)  │
                            └──────────┬───────────┘        └────────────────────┘
                                        │ (on approve)
                                        ▼
                            ┌──────────────────────┐
                            │ SQL column-mapping   │
                            │ table                │
                            └──────────┬───────────┘
                                        │
                                        │ (weekly reindex)
                                        ▼
                            ┌──────────────────────┐
                            │ Azure AI Search      │
                            │ index refreshed with │
                            │ new mapping history  │
                            └──────────────────────┘
```

The loop is: **Suggest → Review → Apply → Learn.** The weekly reindex is what makes the system smarter over time — approved mappings become part of the search corpus, so the same column never has to be suggested twice.

## What the maker needs to build

This skill is the **runtime intelligence**. The maker provides the surrounding infrastructure. Below is what each piece requires.

### 1. Azure AI Search index — `lab-canonical-schema`

Create a search index that describes every column in your canonical clinical warehouse. Recommended fields:

| Field | Type | Searchable | Filterable | Facetable | Purpose |
|---|---|---|---|---|---|
| `canonical_column_name` | Edm.String | Yes | Yes | No | The destination column in SQL (e.g., `patient_mrn`). |
| `column_description` | Edm.String | Yes | No | No | Human description of what the column means. **This is the strongest matching signal.** |
| `data_type` | Edm.String | No | Yes | Yes | SQL type (`nvarchar`, `datetime2`, `decimal`, etc.). Used to reject incompatible mappings. |
| `clinical_domain` | Edm.String | No | Yes | Yes | One of `lab-observations`, `orders`, `specimens`, `results`. |
| `loinc_code` | Edm.String | Yes | Yes | No | LOINC code, if applicable. |
| `synonyms` | Collection(Edm.String) | Yes | No | No | Known aliases (populate over time as mappings are approved). |
| `previously_mapped_from_labs` | Collection(Edm.String) | No | Yes | Yes | Lab IDs that have historically mapped to this column. Boosts same-lab matches. |
| `example_source_names` | Collection(Edm.String) | Yes | No | No | Actual source names that have been mapped here (e.g., `PT_MRN`, `patient_number`, `mrn`). |

Enable **semantic ranking** on the index and create a semantic configuration named `column-descriptions` that prioritizes the `column_description` and `example_source_names` fields for reranking.

The SKILL.md's retrieval steps assume these field and configuration names. If you rename them, update the SKILL.md accordingly.

### 2. Dataverse table — `lab_column_mapping_suggestions`

Create a Dataverse table to hold pending suggestions for the steward to review. Recommended columns:

| Column | Type | Notes |
|---|---|---|
| `suggestion_id` | GUID (primary) | Generated by the skill. |
| `pipeline_run_id` | Text | ADF run ID for traceability. |
| `source_column_name` | Text | The unrecognized column header. |
| `source_lab_id` | Lookup or Text | Reference to the sending lab. |
| `source_lab_name` | Text | Denormalized for readability. |
| `source_file_name` | Text | The file that failed. |
| `suggested_destination_column` | Text | The canonical target (nullable). |
| `suggested_destination_loinc` | Text | LOINC code, if applicable. |
| `confidence` | Choice | `high`, `medium`, `low`, `no_confident_match`. |
| `confidence_score` | Decimal | 0.0 to 1.0. |
| `reasoning` | Multiline text | Why the skill picked this. |
| `alternatives` | Multiline text (JSON) | Runner-up candidates. |
| `status` | Choice | `pending_review`, `approved`, `rejected`, `search_unavailable`. |
| `steward_notes` | Multiline text | Optional notes from the reviewer. |
| `approved_by` | Lookup (User) | Who approved. |
| `approved_at` | DateTime | When approved. |

Build a small **model-driven Power App** on top of this table with a view of `pending_review` items and a form that lets the steward approve, reject, or override the suggestion.

### 3. Power Automate flow — failure handler

Create a Power Automate flow triggered by ADF failure notifications (via HTTP webhook, Azure Monitor alert, or the Azure Data Factory connector).

The flow does:

1. Parses the ADF failure message to extract the source column name, sending lab, file name, and pipeline run ID.
2. De-identifies sample values if any (see PHI safety note below).
3. Calls the Copilot Studio agent using the [Copilot Studio connector](https://learn.microsoft.com/connectors/copilotstudio/) with the payload defined in SKILL.md.
4. On approval later (a separate flow triggered by the `approved` status in Dataverse), writes the new mapping to the SQL column-mapping table so the next ADF run picks it up.

### 4. SQL column-mapping table

A simple table read by the ADF pipeline at the start of each run to know how to map incoming columns.

```sql
CREATE TABLE lab_column_mappings (
    mapping_id            uniqueidentifier PRIMARY KEY DEFAULT NEWID(),
    lab_id                nvarchar(64)     NOT NULL,
    source_column_name    nvarchar(256)    NOT NULL,
    destination_column    nvarchar(256)    NOT NULL,
    clinical_domain       nvarchar(64)     NOT NULL,
    approved_by           nvarchar(256)    NOT NULL,
    approved_at           datetime2        NOT NULL,
    dataverse_suggestion_id uniqueidentifier NULL
);

CREATE UNIQUE INDEX ix_lab_source
    ON lab_column_mappings (lab_id, source_column_name);
```

### 5. Weekly Azure AI Search reindex

Schedule an Azure Function or a Data Factory pipeline to run weekly. It reads the approved mappings from SQL, updates the `previously_mapped_from_labs`, `synonyms`, and `example_source_names` fields on the corresponding canonical documents in the search index, and pushes them back with a partial update.

## PHI safety

**This skill maps schema metadata, not patient data.** It receives a source column name, sample values (which should already be de-identified by the caller), the lab identifier, and the file name. It never touches PHI in its logic.

That said, when you deploy the surrounding pipeline, standard healthcare data protections still apply:

- The Power Automate flow **must** de-identify or hash sample values before including them in the payload to the agent. Reject the pattern of "just send the first 5 rows raw" — that's PHI in a chat conversation log.
- Enable **encryption at rest** on Dataverse, SQL, and the Azure AI Search index.
- Use **private endpoints** for Azure AI Search and SQL if the health system's data classification requires it.
- Enable Microsoft **Purview** DLP policies on the Copilot Studio environment.
- Log every suggestion and approval — this is the audit trail HIPAA compliance officers will ask for.

## Copilot Studio setup

1. Create a new agent in Copilot Studio (new experience).
2. Enable **file uploads** and add the Dataverse and Azure AI Search connectors.
3. Upload this skill as a ZIP: `Build → Skills → Add skill → Upload a skill`.
4. Add a **tool** for `Search documents in Azure AI Search` pointing at the `lab-canonical-schema` index.
5. Add a **tool** for `Create a new row in Dataverse` pointing at the `lab_column_mapping_suggestions` table.
6. Add a **tool** for the Copilot Studio agent invocation from Power Automate (so the flow can call the agent).
7. In agent settings, turn on **generative orchestration** so the skill's trigger conditions activate correctly.

## Licensing

**Copilot Studio consumption — Copilot Credits.** As of September 1, 2025, Copilot Studio agents consume **Copilot Credits** (the successor to "messages"). Credits come from one of three configurations:

- **Prepaid capacity packs only** — Copilot Studio capacity pack subscriptions provide 25,000 credits per pack per month. When credits are exhausted, the agent is unavailable until the next monthly reset.
- **Pay-as-you-go only** — link a Power Platform environment to an Azure subscription billing plan; every credit is billed to Azure. No prepaid commitment.
- **Prepaid + pay-as-you-go (recommended)** — prepaid credits are consumed first, and overage automatically switches to pay-as-you-go so there's no service interruption. This is the standard enterprise configuration.

Forecast expected credit consumption with the [Copilot Studio agent usage estimator](https://microsoft.github.io/copilot-studio-estimator/) before committing to a pack size.

**Publishing the agent** — the user who publishes must have one of:
- A Microsoft 365 Copilot license, or
- A Copilot Studio User license with credits allocated to the environment (or "Draw from tenant pool" enabled).

**Everything else in the architecture:**
- **Azure AI Search** — Standard S1 or higher. Semantic ranker (used by this skill) requires S1+ and has separate metered pricing for reranking requests.
- **Dataverse** — the `lab_column_mapping_suggestions` table consumes standard Dataverse storage, typically included in Power Platform licensing at low volumes.
- **Power Automate** — the Dataverse and Copilot Studio connectors used by the failure-handler flow are standard connectors. The SQL Server connector is premium and requires a Power Automate Premium license or per-flow license.
- **Azure Data Factory** — standard ADF pipeline consumption applies to the upstream ingestion pipeline this skill supports.

For the most current and complete billing and pricing details, see the [Microsoft Copilot Studio Licensing Guide](https://go.microsoft.com/fwlink/?linkid=2320995) and the [Copilot Credit Guide](https://go.microsoft.com/fwlink/?linkid=2368800).

## Testing offline

The `scripts/rank_column_matches.py` helper lets you test the ranking logic against a canonical schema JSON file without wiring up Azure AI Search. Useful when you're first defining your canonical column descriptions and want to see how well the semantic match performs on typical source column names.

```bash
python scripts/rank_column_matches.py \
    --source-column "PT_MRN" \
    --source-samples "MRN-hash-abc,MRN-hash-def" \
    --canonical-schema canonical_schema.json \
    --lab-id LAB-QUEST-001
```

It prints a ranked list of candidate destination columns with a similarity score, matching what the agent would see back from Azure AI Search. Iterate on your `column_description` fields until the top match for common inputs is stable, then push those descriptions to the actual index.

## Known limitations

- The skill assumes column-level mapping only. Cross-column transformations (e.g., "concatenate `first_name` + `last_name` into `patient_full_name`") require a separate pattern.
- LOINC codes are the vocabulary anchor. Result columns without LOINC equivalents (workflow columns like `report_status`) rely on description matching alone.
- The suggestion quality depends heavily on the quality of the `column_description` field in the index. Invest in writing descriptions the way a clinician would talk about the field, not the way a DBA would.
- The `search_unavailable` fallback surfaces the issue but doesn't retry autonomously later. A separate flow to re-attempt stalled suggestions is left to the maker.

## Acknowledgments

Skill design, architecture, and domain patterns by Rafsan Huseynov. Documentation drafting, SKILL.md structure, and the offline ranking helper were prepared collaboratively with Claude (Anthropic), following the modular submission pattern established by the CAT Agent Skills reviewers.

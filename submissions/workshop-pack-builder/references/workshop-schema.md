# Pack spec: workshop.json

One JSON file drives every output and every check. Write it in step 3, fill it through step 6, and pass
it to `timing.py`, `build_deck.py`, `build_docs.py` and `check_pack.py`. A complete example is
`assets/example/workshop.example.json`.

## Top level

| Key | Type | Required | Notes |
|---|---|---|---|
| `title` | string | yes | Session title. States the outcome where possible. |
| `subtitle` | string | no | One line: length, format, topic. |
| `version` | string | no | For example "1.0". |
| `organization` | string | no | Who runs it, or the fictional case company. |
| `audience` | object | yes | `who`, `level`, `size` (integer). |
| `format` | string | yes | `in person`, `virtual` or `hybrid`. |
| `total_minutes` | integer | yes | Session length. Modules add up to exactly this. |
| `start_time` | "HH:MM" | no | Adds clock times to agendas. |
| `constraints` | list of strings | no | Tools, rooms, access, accessibility. |
| `executive_summary` | string | yes | Two to four sentences. Opens every document. |
| `sources` | list | yes | `id` (S1, S2...), `title`, `type`, `location` (path or URL). IDs match the source map. |
| `objectives` | list | yes | `id` (O1...), `text` (starts with an observable verb). |
| `modules` | list | yes | See below. |
| `gaps` | list of strings | yes | What the sources do not cover. An empty list is allowed. |
| `pre_read` | object | no | `minutes`, `summary`, `items` (each `text`, `sources`). |
| `survey` | object | no | `questions` (each `text`, `type`: `scale` or `open`). |
| `follow_up_email` | object | no | `subject`, `summary`, `points`, optional `sign_off`. |

## Module

| Key | Type | Required | Notes |
|---|---|---|---|
| `id` | string | yes | M1, M2... |
| `title` | string | yes | |
| `type` | string | yes | `opening`, `content`, `exercise`, `discussion`, `closing` or `break`. |
| `minutes` | integer | yes | 5, 10, 15, 20, 30, 45 or 60. |
| `objectives` | list of IDs | yes | Empty only for breaks. |
| `key_points` | list | yes | Each `text` and `sources` (list of refs). Empty only for breaks. |
| `talk_track` | string | yes | Spoken text for the facilitator. |
| `setup` | string | yes | What to prepare. |
| `fallback` | string | yes | Module-level plan B. May be empty for breaks. |
| `activities` | list | yes | At least one, except for breaks. |

## Activity

| Key | Type | Required | Notes |
|---|---|---|---|
| `id` | string | yes | A1, A2... |
| `kind` | string | yes | `exercise` (gets an exercise sheet in the workbook) or `discussion`. |
| `title` | string | yes | |
| `objective` | string | yes | |
| `timebox` | integer | yes | Allowed values only. Sum per module no more than the module's minutes. |
| `instructions` | list of strings | yes | Three to six steps. |
| `materials` | list of strings | yes | |
| `expected_output` | string | yes | |
| `debrief` | list of strings | yes | Two or three questions. |
| `fallback` | string | yes | |
| `sources` | list of refs | yes | |

## Source refs

Refs come from `build_source_map.py`: `S<n>.slide<k>` for decks, `S<n>.sec<k>` for documents, Markdown,
text and web pages, `S<n>.table<k>` for Word tables, `S<n>.page<k>` for PDFs. A bare `S<n>` cites a whole
source; use it only when no finer unit applies. `check_pack.py --source-map` fails on any ref that is not
in the map.

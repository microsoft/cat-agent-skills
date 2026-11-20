# Companies House API quick reference

Base URL: `https://api.company-information.service.gov.uk`

## Authentication
HTTP Basic: API key as the username, empty password.
`Authorization: Basic base64("<API_KEY>:")`.
Create a key at https://developer.company-information.service.gov.uk/ (register → create application → add a **REST** key).

## Limits
600 requests per 5 minutes per key; `429` when exceeded.

## Endpoints

| Endpoint | Notes |
| --- | --- |
| `GET /search/companies?q={text}&items_per_page=5&start_index=0` | Items: `title`, `company_number`, `company_status`, `date_of_creation`, `address_snippet`, `company_type` |
| `GET /company/{number}` | `company_name`, `company_number`, `company_status`, `company_status_detail`, `type`, `date_of_creation`, `date_of_cessation`, `sic_codes`, `registered_office_address`, `accounts`, `confirmation_statement`, `previous_company_names`, `jurisdiction`, `has_charges`, `has_insolvency_history`, `has_been_liquidated` |
| `GET /company/{number}/officers?items_per_page=35` | `items[]`: `name`, `officer_role`, `appointed_on`, `resigned_on`, `nationality`, `country_of_residence`, `occupation`, `date_of_birth{month,year}` |
| `GET /company/{number}/persons-with-significant-control` | `items[]`: `name`, `kind`, `natures_of_control`, `notified_on`, `ceased_on` |
| `GET /company/{number}/charges` | `items[]`: `status`, `created_on`, `classification` |
| `GET /company/{number}/insolvency` | `cases[]`: `type`, `dates` (404 if none) |
| `GET /company/{number}/filing-history?items_per_page=10` | `items[]`: `date`, `category`, `description` |

## Company status values
`active`, `dissolved`, `liquidation`, `receivership`, `administration`, `voluntary-arrangement`, `converted-closed`, `insolvency-proceedings`, `registered`, `removed`, `closed`, `open`.

## Company number formats
8 characters: digits (England & Wales, e.g. `00445790`) or prefixes `SC` (Scotland), `NI` (N. Ireland), `OC`/`SO`/`NC` (LLPs), `IP`, `RC`, etc.

## Test data
`00445790` (Tesco PLC) is active; useful for smoke tests.

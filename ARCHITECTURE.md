# Architecture

This document describes the internal structure of aa-sdr-generator: how the
modules connect, how data flows from the Adobe Analytics API to the final
Excel file, and the reasoning behind key design decisions.


## Directory layout

```
aa-sdr-generator/
  config/
    endpoints.py        # URL constants for Adobe IMS and Analytics 2.0 API
    environment.py      # .env loader via pydantic-settings, auto-writes discovered values
    sdr_config.py       # YAML config loader (template path, output dir, RSID filters, metadata)
  core/
    auth.py             # OAuth2 client credentials flow, JWT decode, token lifecycle
    client.py           # AdobeClient (HTTP layer) and AdobeAnalyticsClient (typed API methods)
  models/
    adobe/
      ims.py            # TokenResponse with expiry check
      analytics.py      # Pydantic models for every API response shape
  exporters/
    excel.py            # Template loader, sheet fillers, SDR generation orchestrator
  templates/
    aa_en_BRD_SDR_template.xlsx   # Official Adobe BRD/SDR template (versioned asset)
  main.py               # Entry point: load config, build client, call generate_sdr()
  config.yaml            # User-editable run configuration
  .env                   # Credentials (not committed)
```


## Data flow

```
config.yaml ──> SdrConfig
                    │
                    ▼
.env ──> Auth ──> AdobeClient ──> AdobeAnalyticsClient
                                        │
                    ┌───────────────────┼───────────────────┐
                    ▼                   ▼                   ▼
              get_suites()      get_dimensions()     get_metrics()
                    │           get_calc_metrics()   get_segments()
                    │                   │                   │
                    ▼                   ▼                   ▼
             filter_suites()    Pydantic models      Pydantic models
             (glob match)       (validated)          (validated)
                    │                   │                   │
                    └──────────┬────────┘───────────────────┘
                               ▼
                     openpyxl: load template
                     _fill_sheet() per data sheet
                     _fill_metrics_segments_sheet()
                     _set_org_name()
                               │
                               ▼
                      out/{rsid}_sdr.xlsx
```


## Module responsibilities

### config/

**endpoints.py** holds URL constants. All Adobe API paths live here so that
changing a base URL or path prefix is a single-file edit.

**environment.py** wraps pydantic-settings to load `.env`. On first run, the
auth module writes auto-discovered values (`ORG_ID`, `TECHNICAL_ACCOUNT_ID`,
`GLOBAL_COMPANY_ID`) back to `.env` via `write_env()`. This avoids requiring
the user to know values they cannot easily look up.

**sdr_config.py** defines the YAML schema. `RsidFilter` holds include/exclude
glob lists. `SdrMetadata` holds per-run values (organization name, author, date).
`SdrConfig.from_yaml()` is the single entry point for loading configuration.


### core/

**auth.py** implements the full OAuth2 client credentials lifecycle:

1. Exchange client_id + client_secret for an access token at Adobe IMS
2. Decode the JWT to extract org_id and technical_account_id
3. Cache the token in memory, auto-refresh when within 1 hour of expiry
4. Write discovered values to `.env` on first run (bootstrap)

Uses `authlib` for the OAuth2 session. Token decoding is manual base64 since
we only need claims extraction, not signature verification (the token comes
directly from Adobe IMS over TLS).

**client.py** has two layers:

`AdobeClient` is the HTTP transport. It manages a `requests.Session` with retry
logic (3 retries on 429/502/503/504 with backoff), injects the auth header,
handles 401 by refreshing the token and retrying. Exposes `_authenticated_request()`
for single calls and `_paginated_request()` for endpoints that return
`{content, lastPage}` envelopes.

`AdobeAnalyticsClient` provides typed methods for each Analytics 2.0 endpoint.
Each method builds the URL, assembles query params, calls the transport, and
returns validated Pydantic models. The client auto-discovers `GLOBAL_COMPANY_ID`
on construction if not already in `.env`.

**ID normalization.** The Analytics 2.0 API has an inconsistency: list endpoints
return IDs like `variables/evar1` and `metrics/pageviews`, but single-item
endpoints expect just `evar1` and `pageviews`. The single-item methods strip the
prefix (`id.split("/")[-1]`) so callers can pass IDs straight from a list response
without worrying about the format mismatch.


### models/

**ims.py** contains `TokenResponse` with an `is_expired` property that fires
when the token is within 1 hour of expiry (conservative buffer for long-running
batch jobs).

**analytics.py** has Pydantic models for every API response the tool consumes:
`DiscoveryResponse`, `SuiteResponse`, `MetricResponse`, `DimensionResponse`,
`CalculatedMetricResponse`, `SegmentResponse`, and their nested types. All
fields beyond `id` are `Optional` because the API returns different subsets
depending on the `expansion` parameter.


### exporters/

**excel.py** is the SDR generation orchestrator. Key design decisions:

**Template-based, not generated.** The tool loads the official Adobe BRD/SDR
`.xlsx` template and writes into its existing cells. This preserves all styling,
merged cells, conditional formatting, dropdowns, and cross-sheet formulas
(`=Glossary!C2`). Generating an equivalent workbook from scratch would require
hundreds of lines of openpyxl formatting code and would drift from the official
template whenever Adobe updates it.

**Shared fill logic.** eVars, props, and custom events all have the same column
layout (col 3 = identifier, col 4 = name, col 5 = description, data starts
at row 7). A single `_fill_sheet()` function handles all three, parameterized
by an alias map for special cases like `pageName` mapping to the `page` dimension.

**Index-then-lookup.** API responses are indexed by case-folded short ID into a
dict. The fill loop iterates over template rows (which contain pre-printed
variable identifiers like `eVar1`, `prop3`, `event100`), looks each up in
the index, and writes the API values. Rows with no API match are left untouched.
This means the template controls which variables appear in the SDR, not the API.

**Organization name.** The Glossary sheet cell C2 holds the org name. Five other
sheets reference it via `=Glossary!C2`. The reserved reporting sheet has a
hardcoded `"Client Name"` instead of the formula (Adobe template inconsistency),
so we set it directly. If no organization is specified in `config.yaml`,
the tool falls back to `companyName` from the `/discovery/me` endpoint.


## Report suite selection

The tool fetches all visible report suites in a single paginated call, then
filters client-side using `fnmatch` glob patterns from `config.yaml`:

```yaml
rsids:
  include: ["mycompany*"]
  exclude: ["*_dev"]
```

This avoids the need for exact RSID lists and scales to orgs with many suites
sharing a naming convention (e.g. `mycompanybe`, `mycompanyde`, `mycompanypl`).


## What the 2.0 API does not expose

Some SDR columns cannot be auto-filled because the Analytics 2.0 API does not
have admin/component-settings endpoints:

| Column | Sheet | Why it is blank |
|--------|-------|-----------------|
| eVar Allocation | eVars | Report suite config, not in 2.0 API |
| eVar Expiration | eVars | Report suite config, not in 2.0 API |
| eVar Merchandising | eVars | Report suite config, not in 2.0 API |
| List Prop Delimiter | props | Report suite config, not in 2.0 API |
| Event Type | custom events | Report suite config, not in 2.0 API |
| Unique Event Recording | custom events | Report suite config, not in 2.0 API |

The legacy 1.4 Admin API (`ReportSuite.GetEvars`, `ReportSuite.GetProps`,
`ReportSuite.GetSuccessEvents`) exposed these settings, but it reaches end
of life in mid 2026. This tool intentionally does not depend on it.

These columns are left blank for manual review. The rest of the SDR
(names, descriptions, calculated metric definitions, segment containers)
is fully automated.


## Dependencies and rationale

| Package | Version | Role |
|---------|---------|------|
| requests | 2.33+ | HTTP client with session, retry, and connection pooling |
| authlib | 1.7+ | OAuth2 client credentials grant |
| pydantic | 2.13+ | API response validation and typed models |
| pydantic-settings | 2.14+ | `.env` file loading with type coercion |
| openpyxl | 3.1+ | Read/write the Excel template without losing formatting |
| pyyaml | 6.0+ | Parse `config.yaml` |

No pandas. No CLI framework. No third-party Adobe SDK. The tool stays small
enough to read end to end and deploy without heavy transitive dependencies.


## Future considerations

**Classifications.** The 2.0 API has a classifications dataset endpoint
(`GET /classifications/datasets/compatibilityMetrics/{rsid}`) that lists
datasets per metric. It could feed a new sheet or annotate existing dimension
rows. Not yet implemented.

**Virtual Report Suites.** The 2.0 API supports listing, creating, and managing
VRS (`GET /reportsuites/virtualreportsuites`). Useful if the tool should
generate SDRs against VRS or annotate suites as virtual. Not yet implemented.

**Raw export.** A second exporter (`exporters/raw.py`) could write the same
`list[dict]` data to CSV or JSON for downstream ETL pipelines, alongside the
Excel output.

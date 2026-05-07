# aa-sdr-generator

Generates Adobe Analytics Solution Design Reference (SDR) documents by pulling
live component metadata from the Adobe Analytics 2.0 API and writing it into
the official BRD/SDR Excel template.

Point it at a `config.yaml`, run it, get one pre-filled `.xlsx` per report suite.


## What it does

For each matching report suite the tool:

1. Fetches **dimensions** (eVars, props, reserved dimensions)
2. Fetches **metrics** (custom events, reserved metrics)
3. Fetches **calculated metrics** and **segments**
4. Loads the official Adobe BRD/SDR template from `templates/`
5. Fills every data sheet with names, descriptions, and metadata from the API
6. Writes one `{rsid}_sdr.xlsx` per suite to the output directory

Sheets that get populated:

| Sheet | API source | What gets filled |
|-------|-----------|-----------------|
| eVars | Dimensions | Variable name, description |
| props | Dimensions | Variable name, description (with alias mapping for `pageName`) |
| custom events (metrics) | Metrics | Event name, description |
| metrics-segments | Calculated Metrics + Segments | Name, description, format/container level |
| reserved reporting | Template (static) | Organization name only |
| Glossary | Template (static) | Organization name |

Columns that require Adobe Analytics Admin settings (eVar allocation/expiration,
prop list delimiter, event type) are left blank. The 2.0 API does not expose
report suite component configuration. The legacy 1.4 Admin API did, but it
reaches end of life in mid 2026.


## Inspiration and differences from aa_auto_sdr

This project was inspired by [aa_auto_sdr](https://github.com/brian-a-au/aa_auto_sdr)
by Brian Au. Both tools solve the same problem: automating SDR generation from
Adobe Analytics metadata. The differences are deliberate:

| | aa_auto_sdr | aa-sdr-generator |
|---|---|---|
| **API access** | Via `aanalytics2` third-party SDK | Direct HTTP calls to the 2.0 API |
| **Dependencies** | `aanalytics2`, `pandas`, `click`, and their transitive trees | `requests`, `pydantic`, `authlib`, `openpyxl`, `pyyaml` |
| **Interface** | CLI with interactive prompts | Config-driven (`config.yaml`), no interactive input |
| **Report suite selection** | Interactive picker or explicit RSID argument | Glob patterns in YAML (e.g. `mycompany*`), supports batch generation |
| **Template handling** | Generates Excel from scratch | Fills the official Adobe BRD/SDR template, preserving styling, formulas, and dropdowns |
| **Data layer** | Pandas DataFrames | Pydantic models, validated at the API boundary |
| **Auth** | Delegated to `aanalytics2` | Custom OAuth2 client credentials flow with JWT decoding and token auto-refresh |

The direct API approach avoids a ~200MB dependency tree (`pandas` + `aanalytics2`),
gives full visibility into what HTTP calls happen, and makes the Pydantic models
the single source of truth for response shapes.

The config-driven design fits corporate environments where the tool runs
unattended on a schedule (cron, Jenkins, Airflow) without interactive terminals.


## Quickstart

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- An Adobe Developer Console project with OAuth Server-to-Server credentials
  and the Adobe Analytics API added

### Setup

```bash
git clone https://github.com/paolobietolini/aa-sdr-generator.git
cd aa-sdr-generator
uv sync
```

Create a `.env` file from the example:

```
CLIENT_ID=your_client_id
CLIENT_SECRET=your_client_secret
SCOPES=openid,AdobeID,additional_info.projectedProductContext
```

On first run, the tool auto-discovers `ORG_ID`, `TECHNICAL_ACCOUNT_ID`, and
`GLOBAL_COMPANY_ID` from the token and `/discovery/me` endpoint, and writes
them back to `.env` for subsequent runs.

### Configure

Edit `config.yaml`:

```yaml
template_path: ./templates/aa_en_BRD_SDR_template.xlsx
output_dir: ./out/

rsids:
  include:
    - "mycompany*"
  exclude:
    - "*_dev"
    - "*_test"

metadata:
  organization: null   # null = auto-detect from /discovery/me companyName
  author: Your Name
  date: "2026-05-07"
```

The `rsids.include` list uses glob patterns (fnmatch syntax). The tool pulls
all visible report suites, then filters client-side.

### Run

```bash
uv run python main.py
```

Output:

```
  mycompanyprod: eVars=94 props=48 events=148 cms=12 segs=5 -> out/mycompanyprod_sdr.xlsx
  mycompanystg:  eVars=94 props=48 events=148 cms=0  segs=0 -> out/mycompanystg_sdr.xlsx
```


## API endpoints used

All calls go to `https://analytics.adobe.io/api/{globalCompanyId}/`.

| Endpoint | Purpose |
|----------|---------|
| `GET /discovery/me` | Bootstrap: resolve org, company, and global company ID |
| `GET /reportsuites/collections/suites` | List all report suites (paginated) |
| `GET /dimensions?rsid={rsid}` | All dimensions for a suite (eVars, props, reserved) |
| `GET /metrics?rsid={rsid}` | All metrics for a suite (events, reserved) |
| `GET /calculatedmetrics?rsids={rsid}` | Calculated metrics (paginated) |
| `GET /segments?rsids={rsid}` | Segments (paginated) |

Single-item endpoints (`/dimensions/{id}`, `/metrics/{id}`, etc.) are also
implemented but not used during SDR generation.


## Roadmap

- [ ] Classifications support via the 2.0 classifications dataset API
- [ ] Virtual Report Suites listing and metadata
- [ ] Raw export mode (CSV/JSON) alongside the Excel template
- [ ] Logging with structured output for production environments


## License

[BSD-3](LICENSE)

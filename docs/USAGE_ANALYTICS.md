# Usage Analytics (Cloud Logging → BigQuery)

Production tool usage is captured as structured JSON logs and exported to BigQuery via a Cloud Logging sink. No custom database or application-side persistence layer.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Cloud Run: medical-mcps                                        │
│                                                                   │
│  MedicalFastMCP.call_tool()                                       │
│       │                                                           │
│       ▼                                                           │
│  usage_logging.log_tool_call()  →  stdout (JSON line)             │
│       { event, tool, args_keys, outcome, latency_ms, ... }        │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  Cloud Logging (automatic for Cloud Run)                          │
│  Retention: 30 days (platform default)                          │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼  Log Router sink: medical-mcps-usage
┌─────────────────────────────────────────────────────────────────┐
│  BigQuery dataset: medical_mcps_analytics                       │
│  Tables: run_googleapis_com_YYYYMMDD (auto-created by sink)       │
│  Retention: 1 year (dataset default_table_expiration)           │
└─────────────────────────────────────────────────────────────────┘
```

**Complementary:** Sentry MCP traces (`tools/call <name>`) remain useful for 30-day drill-down with latency and optional PII. BigQuery is the durable, SQL-queryable learning store.

## What gets logged

Every tool invocation passes through `MedicalFastMCP.call_tool()` and emits one JSON event:

| Field | Description |
|-------|-------------|
| `event` | Always `tool_call` (sink filter key) |
| `tool` | Tool name, e.g. `pubmed_search_articles` |
| `args_keys` | Sorted argument names only — **not values** |
| `arg_count` | Number of arguments |
| `outcome` | `ok`, `unknown_tool`, `validation_error`, `client_error`, `upstream_error`, `error` |
| `latency_ms` | Round-trip time for the tool call |
| `error_type` | Present when `outcome` is an error class |

Argument **values** are intentionally omitted to limit PHI/PII in the warehouse.

## GCP resources

| Resource | Name | Purpose |
|----------|------|---------|
| Cloud Run service | `medical-mcps` | Source of logs |
| Log sink | `medical-mcps-usage` | Routes `tool_call` events to BigQuery |
| BigQuery dataset | `medical_mcps_analytics` | Analytics warehouse |
| Sink service account | `service-<project>@gcp-sa-logging.iam.gserviceaccount.com` | Writer to dataset |

## Setup

Run once per GCP project (idempotent):

```bash
# Ensure gcloud points at the right project
gcloud config set project YOUR_PROJECT_ID

# Provision dataset + sink + IAM
bash scripts/setup_usage_analytics.sh
```

Or with an explicit project:

```bash
GCP_PROJECT_ID=your-project bash scripts/setup_usage_analytics.sh
```

The script:

1. Creates `medical_mcps_analytics` (or updates expiration if it exists)
2. Creates/updates sink `medical-mcps-usage` with filter `jsonPayload.event="tool_call"`
3. Grants the sink writer identity `roles/bigquery.dataEditor` on the dataset

**Retention:** dataset `default_table_expiration` is **31,536,000 seconds (1 year)**. Each daily table inherits this on creation.

## Example queries

Top tools (last 30 days — adjust table wildcard as needed):

```sql
SELECT
  jsonPayload.tool AS tool,
  COUNT(*) AS calls
FROM `YOUR_PROJECT.medical_mcps_analytics.run_googleapis_com_*`
WHERE jsonPayload.event = 'tool_call'
  AND _TABLE_SUFFIX >= FORMAT_DATE('%Y%m%d', DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY))
GROUP BY 1
ORDER BY calls DESC
LIMIT 25;
```

Unknown / hallucinated tools:

```sql
SELECT
  jsonPayload.tool AS tool,
  COUNT(*) AS calls
FROM `YOUR_PROJECT.medical_mcps_analytics.run_googleapis_com_*`
WHERE jsonPayload.outcome = 'unknown_tool'
GROUP BY 1
ORDER BY calls DESC;
```

Error rate by tool:

```sql
SELECT
  jsonPayload.tool AS tool,
  jsonPayload.outcome AS outcome,
  COUNT(*) AS n
FROM `YOUR_PROJECT.medical_mcps_analytics.run_googleapis_com_*`
WHERE jsonPayload.event = 'tool_call'
GROUP BY 1, 2
ORDER BY n DESC;
```

p95 latency:

```sql
SELECT
  jsonPayload.tool AS tool,
  APPROX_QUANTILES(CAST(jsonPayload.latency_ms AS FLOAT64), 100)[OFFSET(95)] AS p95_ms
FROM `YOUR_PROJECT.medical_mcps_analytics.run_googleapis_com_*`
WHERE jsonPayload.event = 'tool_call'
  AND jsonPayload.latency_ms IS NOT NULL
GROUP BY 1
ORDER BY p95_ms DESC
LIMIT 20;
```

## Verify end-to-end

1. Deploy a build that includes structured usage logging.
2. Call any tool on production, e.g. `https://mcp.cloud.curiloo.com/tools/unified/mcp`.
3. Wait a few minutes for the sink to flush.
4. Run the top-tools query above — you should see rows.

Cloud Logging (immediate check):

```bash
gcloud logging read \
  'resource.type="cloud_run_revision"
   resource.labels.service_name="medical-mcps"
   jsonPayload.event="tool_call"' \
  --limit=5 --format=json
```

## Teardown

```bash
gcloud logging sinks delete medical-mcps-usage --project=YOUR_PROJECT_ID
bq rm -r -f -d YOUR_PROJECT_ID:medical_mcps_analytics
```

## Why not Terraform?

This is a small, stable footprint (one dataset, one sink). The setup script and this doc are the source of truth until the project grows enough to warrant full IaC.

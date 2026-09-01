#!/usr/bin/env bash
# Provision Cloud Logging → BigQuery usage analytics for medical-mcps.
#
# Idempotent: safe to re-run. Creates dataset/sink if missing; updates expiration.
#
# Prerequisites:
#   - gcloud CLI authenticated (`gcloud auth login`)
#   - bq CLI available (bundled with gcloud)
#   - permissions: logging.sinks.create, bigquery.datasets.create, IAM on dataset
#
# Usage:
#   GCP_PROJECT_ID=my-project scripts/setup_usage_analytics.sh

set -euo pipefail

PROJECT_ID="${GCP_PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}"
DATASET_ID="medical_mcps_analytics"
SINK_NAME="medical-mcps-usage"
SERVICE_NAME="medical-mcps"
LOCATION="${BQ_LOCATION:-US}"
# 365 days — matches docs/USAGE_ANALYTICS.md retention policy
EXPIRATION_SECONDS=31536000

if [[ -z "${PROJECT_ID}" || "${PROJECT_ID}" == "(unset)" ]]; then
  echo "Error: set GCP_PROJECT_ID or run 'gcloud config set project <id>'" >&2
  exit 1
fi

echo "Project:  ${PROJECT_ID}"
echo "Dataset:  ${DATASET_ID}"
echo "Sink:     ${SINK_NAME}"
echo "Service:  ${SERVICE_NAME}"
echo "Location: ${LOCATION}"
echo "Retention: ${EXPIRATION_SECONDS}s (1 year per table)"

LOG_FILTER=$(cat <<EOF
resource.type="cloud_run_revision"
resource.labels.service_name="${SERVICE_NAME}"
jsonPayload.event="tool_call"
EOF
)

if bq show --project_id="${PROJECT_ID}" "${DATASET_ID}" >/dev/null 2>&1; then
  echo "Dataset exists; updating default table expiration..."
  bq update --default_table_expiration="${EXPIRATION_SECONDS}" \
    "${PROJECT_ID}:${DATASET_ID}"
else
  echo "Creating dataset..."
  bq mk \
    --project_id="${PROJECT_ID}" \
    --location="${LOCATION}" \
    --dataset \
    --default_table_expiration="${EXPIRATION_SECONDS}" \
    --description="Tool usage events exported from Cloud Run logs (1 year retention)" \
    "${DATASET_ID}"
fi

if gcloud logging sinks describe "${SINK_NAME}" --project="${PROJECT_ID}" >/dev/null 2>&1; then
  echo "Sink exists; updating filter..."
  gcloud logging sinks update "${SINK_NAME}" \
    --project="${PROJECT_ID}" \
    --log-filter="${LOG_FILTER}"
else
  echo "Creating log sink..."
  gcloud logging sinks create "${SINK_NAME}" \
    --project="${PROJECT_ID}" \
    "bigquery.googleapis.com/projects/${PROJECT_ID}/datasets/${DATASET_ID}" \
    --log-filter="${LOG_FILTER}"
fi

WRITER_IDENTITY="$(gcloud logging sinks describe "${SINK_NAME}" \
  --project="${PROJECT_ID}" \
  --format='value(writerIdentity)')"
echo "Sink writer: ${WRITER_IDENTITY}"

echo "Granting BigQuery WRITER on dataset..."
if bq add-iam-policy-binding \
  --member="${WRITER_IDENTITY}" \
  --role="roles/bigquery.dataEditor" \
  "${PROJECT_ID}:${DATASET_ID}" >/dev/null 2>&1; then
  echo "Granted via dataset IAM policy binding."
else
  echo "IAM policy binding unavailable; adding dataset access entry..."
  ACCESS_FILE="$(mktemp)"
  bq show --format=prettyjson "${PROJECT_ID}:${DATASET_ID}" > "${ACCESS_FILE}"
  python3 - "${WRITER_IDENTITY}" "${ACCESS_FILE}" <<'PY'
import json
import sys

writer = sys.argv[1].removeprefix("serviceAccount:")
path = sys.argv[2]
with open(path, encoding="utf-8") as fh:
    dataset = json.load(fh)

access = dataset.get("access", [])
entry = {"role": "WRITER", "userByEmail": writer}
if entry not in access:
    access.append(entry)
dataset["access"] = access

with open(path, "w", encoding="utf-8") as fh:
    json.dump(dataset, fh)
PY
  bq update --dataset --source "${ACCESS_FILE}" "${PROJECT_ID}:${DATASET_ID}"
  rm -f "${ACCESS_FILE}"
  echo "Granted via dataset access list."
fi

cat <<EOF

Done.

Verify after deploy + a few tool calls:
  bq query --project_id=${PROJECT_ID} --use_legacy_sql=false '
    SELECT
      jsonPayload.tool AS tool,
      jsonPayload.outcome AS outcome,
      COUNT(*) AS calls
    FROM \`${PROJECT_ID}.${DATASET_ID}.run_googleapis_com_*\`
    WHERE jsonPayload.event = "tool_call"
    GROUP BY 1, 2
    ORDER BY calls DESC
    LIMIT 20'

See docs/USAGE_ANALYTICS.md for architecture and example queries.
EOF

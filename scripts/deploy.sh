#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# KultureSync Cloud Run Production Deployment Script
# Configured for asynchronous background graph execution & budget safeguards
# ==============================================================================

SERVICE_NAME="${SERVICE_NAME:-kulture-sync-agent}"
REGION="${REGION:-us-central1}"
PROJECT_ID="${PROJECT_ID:-$(gcloud config get-value project 2>/dev/null || echo '')}"

if [[ -z "${PROJECT_ID}" ]]; then
  echo "Error: No active GCP project set. Run 'gcloud config set project <PROJECT_ID>' first." >&2
  exit 1
fi

echo "================================================================="
echo " Deploying Service: ${SERVICE_NAME}"
echo " GCP Project:       ${PROJECT_ID}"
echo " Target Region:     ${REGION}"
echo "================================================================="

# Navigate to workspace root containing the parent multi-project Dockerfile
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${WORKSPACE_ROOT}"

echo "Executing build and deployment from: ${WORKSPACE_ROOT}"

gcloud run deploy "${SERVICE_NAME}" \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --source="." \
  --allow-unauthenticated \
  --port=8080 \
  --cpu=2 \
  --memory=2Gi \
  --no-cpu-throttling \
  --min-instances=1 \
  --max-instances=3 \
  --concurrency=80 \
  --timeout=3600 \
  --set-env-vars="PYTHONUNBUFFERED=1"

echo "================================================================="
echo " Deployment Complete!"
SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" --platform=managed --region="${REGION}" --project="${PROJECT_ID}" --format='value(status.url)')
echo " Service Endpoint: ${SERVICE_URL}"
echo " Health Check:     curl -s ${SERVICE_URL}/"
echo "================================================================="

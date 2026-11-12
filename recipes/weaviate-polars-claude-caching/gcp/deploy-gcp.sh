#!/usr/bin/env bash
# ==============================================================================
# GCP Cloud Run / Compute Deployment Script for Sovereign Agent Pipeline
# Region: europe-west4 (Eemshaven, Netherlands)
# Zero-Egress European Sovereign Cloud Deployment
# ==============================================================================

set -euo pipefail

PROJECT_ID="${GCP_PROJECT_ID:-$(gcloud config get-value project 2>/dev/null || echo '')}"
REGION="${GCP_REGION:-europe-west4}"
SERVICE_NAME="sovereign-agent-pipeline"
REPO_NAME="agent-artifacts"

if [ -z "${PROJECT_ID}" ]; then
  echo "Error: GCP_PROJECT_ID is not set. Run 'gcloud config set project <id>' first."
  exit 1
fi

echo "======================================================================"
echo "DEPLOYING SOVEREIGN AGENT PIPELINE TO GCP (europe-west4, Netherlands)"
echo "Project:  ${PROJECT_ID}"
echo "Region:   ${REGION}"
echo "Service:  ${SERVICE_NAME}"
echo "======================================================================"

# 1. Enable Required GCP APIs
echo "[1/4] Ensuring APIs are enabled..."
gcloud services enable \
  artifactregistry.googleapis.com \
  run.googleapis.com \
  compute.googleapis.com \
  secretmanager.googleapis.com \
  --project="${PROJECT_ID}"

# 2. Build Container Image via Cloud Build
IMAGE_TAG="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${SERVICE_NAME}:latest"
echo "[2/4] Building container image: ${IMAGE_TAG}..."
cd "$(dirname "${BASH_SOURCE[0]}")/.."
gcloud builds submit --tag "${IMAGE_TAG}" --project="${PROJECT_ID}"

# 3. Deploy to Cloud Run in europe-west4
echo "[3/4] Deploying to Cloud Run in ${REGION}..."
gcloud run deploy "${SERVICE_NAME}" \
  --image "${IMAGE_TAG}" \
  --region "${REGION}" \
  --platform managed \
  --memory 2Gi \
  --cpu 2 \
  --min-instances 1 \
  --no-allow-unauthenticated \
  --set-env-vars="DATA_RESIDENCY=${REGION},PYTHONUNBUFFERED=1" \
  --project="${PROJECT_ID}"

echo "[4/4] Sovereign Cloud Run deployment completed in ${REGION}."

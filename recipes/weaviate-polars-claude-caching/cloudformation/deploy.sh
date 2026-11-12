#!/usr/bin/env bash
# ==============================================================================
# AWS CloudFormation Deployment Script for Sovereign Weaviate Vector Memory Stack
# Region: eu-central-1 (Frankfurt, Germany)
# Standard: EU AI Act Annex IV / GDPR Zero-Egress Architecture
# ==============================================================================

set -euo pipefail

STACK_NAME="${STACK_NAME:-sovereign-weaviate-claude-stack}"
REGION="${AWS_REGION:-eu-central-1}"
ENVIRONMENT="${ENVIRONMENT:-prod}"
INSTANCE_TYPE="${INSTANCE_TYPE:-m6i.xlarge}"
TEMPLATE_FILE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/template.yaml"

echo "======================================================================"
echo "DEPLOYING SOVEREIGN AGENTIC STACK TO AWS CLOUDFORMATION"
echo "Stack Name:  ${STACK_NAME}"
echo "Region:      ${REGION} (Frankfurt)"
echo "Environment: ${ENVIRONMENT}"
echo "Instance:    ${INSTANCE_TYPE}"
echo "======================================================================"

# 1. Validate template syntax
echo "[1/3] Validating CloudFormation template syntax..."
aws cloudformation validate-template \
  --template-body "file://${TEMPLATE_FILE}" \
  --region "${REGION}" > /dev/null

echo "      Template syntax validated successfully."

# 2. Deploy or update CloudFormation Stack
echo "[2/3] Executing stack deployment in ${REGION}..."
aws cloudformation deploy \
  --template-file "${TEMPLATE_FILE}" \
  --stack-name "${STACK_NAME}" \
  --region "${REGION}" \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
      EnvironmentName="${ENVIRONMENT}" \
      WeaviateInstanceType="${INSTANCE_TYPE}" \
  --no-fail-on-empty-changeset

# 3. Retrieve and print deployment outputs
echo "[3/3] Fetching stack outputs..."
aws cloudformation describe-stacks \
  --stack-name "${STACK_NAME}" \
  --region "${REGION}" \
  --query "Stacks[0].Outputs[*].[OutputKey,OutputValue]" \
  --output table

echo "======================================================================"
echo "Sovereign cluster active. Connect with Weaviate v4 Python client:"
echo "export WEAVIATE_URL=\"http://<WeaviatePrivateIp>:8080\""
echo "======================================================================"

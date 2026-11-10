# 3. Adopt Mistral AI & Sovereign vLLM Inference for EU Deployments

Date: 2026-02-01

## Status
Accepted

## Context
Deploying enterprise AI within the European Union requires compliance with GDPR data residency mandates and the EU AI Act. Relying exclusively on US-hosted closed proprietary APIs introduces legal risks regarding transatlantic data transfer (Schrems II) and data retention policies.

## Decision
We adopt **Mistral AI** foundation models (`Mistral-Large`, `Codestral`, and `Mixtral-8x7B`) as our primary model family for EU production environments. For high-security sovereign enterprise tiers, models will be hosted on private `vLLM` clusters running exclusively in AWS Frankfurt (`eu-central-1`) or on-premise private VPCs.

## Consequences
- **Positive**: 100% data sovereignty; zero prompts or embeddings leave the European economic perimeter.
- **Positive**: Open weights allow self-hosting, transparent auditing, and immunity from third-party vendor deprecations.
- **Positive**: High code and multilingual reasoning performance across European languages (German, French, Spanish, Italian).
- **Negative**: Requires managing private GPU cluster infrastructure and autoscaling.

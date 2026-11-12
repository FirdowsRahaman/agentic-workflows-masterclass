# Lab 9: Sovereign European Agent with Mistral AI & vLLM 

This hands-on lab demonstrates how to build a production-grade autonomous agent using **Mistral AI** foundation models (`Mistral Large` / `Codestral`) and private **vLLM** sovereign inference endpoints, designed to satisfy European Union data residency and GDPR compliance requirements.

---

## Learning Objectives

1. Configure Mistral AI models (`mistral-large-latest`, `codestral-latest`) using official APIs or local `vLLM` sovereign clusters.
2. Implement strict zero-data-retention routing where prompt data never leaves the European Union (`eu-central-1` / `eu-west-1`).
3. Execute tool-calling with Mistral's native function-calling format.
4. Implement automated fallback between sovereign private clusters and public API endpoints.

---

## Architecture

```
User Prompt ──▶ [GDPR PII Masking Gateway]
                       │
                       ▼
          [LangGraph Agent Controller]
                       │
         ┌─────────────┴─────────────┐
         ▼                           ▼
[Sovereign vLLM Cluster]   [Mistral API (Paris DC)]
 (Frankfurt eu-central-1)   (Fallback Endpoint)
         │                           │
         └─────────────┬─────────────┘
                       ▼
          [Isolated Tool Execution Sandbox]
                       │
                       ▼
          [Audit Telemetry & Logging]
```

---

## Running the Lab

1. Ensure your `.env` contains your Mistral API key (or local vLLM URL):
   ```bash
   MISTRAL_API_KEY="your-mistral-api-key"
   # Optional: set for private sovereign cluster
   SOVEREIGN_VLLM_URL="http://localhost:8000/v1"
   ```

2. Run the agent script:
   ```bash
   python agent.py
   ```

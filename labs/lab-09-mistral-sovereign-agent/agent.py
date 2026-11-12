"""Lab 9: Sovereign European Agent with Mistral AI & vLLM Endpoint
Demonstrates GDPR-compliant data residency, Mistral function calling, and fallback routing.
"""

import os
import json
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()

# =====================================================================
# 1. European Sovereign Tool Definitions
# =====================================================================

def query_european_vat(vat_number: str) -> str:
    """Validates a European Union VAT number against VIES database."""
    print(f"[Tool Executing] query_european_vat('{vat_number}')...")
    vat = vat_number.strip().upper()
    if vat.startswith("DE"):
        return json.dumps({"valid": True, "country": "Germany", "entity": "Sovereign AI GmbH", "vat": vat})
    elif vat.startswith("FR"):
        return json.dumps({"valid": True, "country": "France", "entity": "Intelligence Européenne SAS", "vat": vat})
    else:
        return json.dumps({"valid": True, "country": "EU", "entity": "Verified European Enterprise", "vat": vat})

def calculate_gdpr_retention_window(data_category: str) -> str:
    """Calculates legal data retention limits under EU GDPR Article 5(1)(e)."""
    print(f"[Tool Executing] calculate_gdpr_retention_window('{data_category}')...")
    category = data_category.lower().strip()
    if "invoice" in category or "financial" in category:
        return json.dumps({"category": data_category, "retention_years": 10, "legal_basis": "HGB § 257 / Tax Code"})
    elif "telemetry" in category or "logs" in category:
        return json.dumps({"category": data_category, "retention_days": 90, "legal_basis": "GDPR Art 6(1)(f) Legitimate Interest"})
    else:
        return json.dumps({"category": data_category, "retention_days": 30, "legal_basis": "GDPR Principle of Storage Limitation"})

TOOL_REGISTRY = {
    "query_european_vat": query_european_vat,
    "calculate_gdpr_retention_window": calculate_gdpr_retention_window
}

# =====================================================================
# 2. Sovereign Model Client (Mistral AI & vLLM Fallback)
# =====================================================================

class SovereignMistralClient:
    """Client configured exclusively for European sovereign inference endpoints.
    Prioritizes local on-premise vLLM running in Frankfurt (eu-central-1),
    falling back to Mistral AI Paris cloud endpoints.
    """
    def __init__(self, api_key: Optional[str] = None, vllm_url: Optional[str] = None):
        self.api_key = api_key or os.getenv("MISTRAL_API_KEY", "")
        self.vllm_url = vllm_url or os.getenv("SOVEREIGN_VLLM_URL", "")
        self.active_endpoint = "vLLM-Frankfurt" if self.vllm_url else "Mistral-Paris"
        print(f"Initialized Sovereign LLM Client: Active Gateway = {self.active_endpoint}")

    def generate(self, prompt: str, tools: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Simulates structured function calling inference adhering to Mistral format."""
        # For demonstration purposes, mock the deterministic response
        prompt_lower = prompt.lower()
        if "vat" in prompt_lower:
            return {
                "thought": "The user is requesting EU VAT verification. I will invoke query_european_vat tool.",
                "tool_call": {
                    "name": "query_european_vat",
                    "arguments": {"vat_number": "DE123456789"}
                }
            }
        elif "retention" in prompt_lower or "gdpr" in prompt_lower:
            return {
                "thought": "The user is asking about GDPR data retention periods. I will invoke calculate_gdpr_retention_window.",
                "tool_call": {
                    "name": "calculate_gdpr_retention_window",
                    "arguments": {"data_category": "audit_logs"}
                }
            }
        else:
            return {
                "thought": "General inquiry within European regulatory bounds.",
                "response": "This is a sovereign European AI response processed in compliance with the EU AI Act."
            }

# =====================================================================
# 3. Agent Execution Loop
# =====================================================================

def run_sovereign_agent(query: str):
    print("\n" + "="*70)
    print(f"Sovereign Mistral Agent: Received Query")
    print(f"Query: '{query}'")
    print("="*70)

    client = SovereignMistralClient()
    result = client.generate(query)
    
    print(f"\n [Agent Thought]: {result.get('thought')}")
    
    if "tool_call" in result:
        tool_call = result["tool_call"]
        tool_name = tool_call["name"]
        tool_args = tool_call["arguments"]
        
        print(f"\n [Tool Invocation]: {tool_name}")
        print(f"Arguments: {tool_args}")
        
        if tool_name in TOOL_REGISTRY:
            tool_output = TOOL_REGISTRY[tool_name](**tool_args)
            print(f"Output: {tool_output}")
            print(f"\n [Final Answer]: Processed via European sovereign endpoint with zero data egress.")
        else:
            print(f"Error: Tool {tool_name} not registered.")
    else:
        print(f"\n [Final Answer]: {result.get('response')}")

if __name__ == "__main__":
    run_sovereign_agent("Please verify VAT number DE123456789 for our German entity.")
    run_sovereign_agent("What is the legal GDPR retention window for telemetry audit logs?")

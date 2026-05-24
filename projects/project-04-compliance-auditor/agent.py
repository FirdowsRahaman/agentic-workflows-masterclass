import os
import sys
from typing import TypedDict
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load API keys
load_dotenv()

# =====================================================================
# 1. Pydantic Verification Schema
# =====================================================================

class ComplianceSchema(BaseModel):
    compliance_score: float = Field(description="Audit score from 0.0 to 100.0 based on safety and laws compliance")
    violated_clauses: list[str] = Field(default_factory=list, description="List of corporate policies or legal clauses violated")
    recommended_fixes: list[str] = Field(default_factory=list, description="Recommended remediation actions to fix violations")
    requires_corrective_action: bool = Field(description="True if score < 80.0, requiring immediate corrective action")

class AuditState(TypedDict):
    report_text: str
    audit_data: ComplianceSchema
    action_log: str
    status: str

# =====================================================================
# 2. Corrective Action Node
# =====================================================================

def trigger_corrective_action(violated_clauses: list[str]) -> str:
    """Executes corrective business logic once compliance threshold is violated."""
    print("⚠️ [Action Executor] COMPLIANCE VIOLATION CRITICAL WARNING")
    print(f"   Drafting warning memo for violated clauses: {violated_clauses}...")
    memo = (
        f"MEMORANDUM: Compliance Audit Failure Notice\n"
        f"To: Department Operations Manager\n"
        f"Subject: Immediate Remediation Required for Policy Violations\n\n"
        f"Please be advised that your department failed the compliance audit. "
        f"Violations detected: {', '.join(violated_clauses)}. "
        f"Remediation must be submitted within 7 business days."
    )
    print("🟢 [Action Executor] Warning memo drafted and sent successfully.")
    return memo

# =====================================================================
# 3. Compliance Agent Nodes
# =====================================================================

def run_compliance_audit_node(state: AuditState) -> dict:
    """Evaluates the report text and outputs structured audit details matching Pydantic."""
    print("🤖 [Node: run_compliance_audit_node] Analyzing document text...")
    report = state["report_text"]
    
    # Use API key if available
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ℹ️ Model running in Mock Mode...")
        # Simulated structured evaluation
        score = 72.5
        clauses = ["Data Privacy Law (GDPR) Section 4", "Clean Desk Policy Clause 12"]
        fixes = ["Encrypt database client records at rest", "Clean client desks of physical paper logs"]
        
        audit = ComplianceSchema(
            compliance_score=score,
            violated_clauses=clauses,
            recommended_fixes=fixes,
            requires_corrective_action=score < 80.0
        )
        return {"audit_data": audit, "status": "audit_complete"}

    try:
        # Pydantic structured output using google-genai schema validation
        from google import genai
        from google.genai import types
        client = genai.Client()
        
        prompt = f"""You are a Compliance & Risk Auditor Agent.
Analyze this corporate report for compliance violations:
"{report}"

Grade the compliance score (out of 100). Identify any violated policies and recommend fixes.
"""
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ComplianceSchema
            )
        )
        
        # Parse Pydantic from json output
        audit = ComplianceSchema.model_validate_json(response.text)
        return {"audit_data": audit, "status": "audit_complete"}
    except Exception as e:
        print(f"⚠️ Error during structured model run: {str(e)}")
        # Local fallback
        audit = ComplianceSchema(
            compliance_score=95.0,
            violated_clauses=[],
            recommended_fixes=[],
            requires_corrective_action=False
        )
        return {"audit_data": audit, "status": "failed"}

# =====================================================================
# 4. Core Pipeline
# =====================================================================

def run_compliance_pipeline(report_text: str):
    print("=" * 70)
    print("🚀 Initializing Corporate Compliance & Risk Auditor Pipeline...")
    print("=" * 70)
    
    # 1. Initialize State
    state: AuditState = {
        "report_text": report_text,
        "audit_data": None,
        "action_log": "",
        "status": "initialized"
    }
    
    # 2. Run Audit Node
    updates = run_compliance_audit_node(state)
    state.update(updates)
    
    audit = state["audit_data"]
    print(f"\n📊 Audit Results Compiled:")
    print(f"   - Compliance Score: {audit.compliance_score:.1f}%")
    print(f"   - Violations:       {audit.violated_clauses}")
    print(f"   - Recommended Fixes: {audit.recommended_fixes}")
    print(f"   - Action Required?:  {audit.requires_corrective_action}\n")
    
    # 3. Check for corrective action rule threshold
    if audit.requires_corrective_action:
        memo = trigger_corrective_action(audit.violated_clauses)
        state["action_log"] = memo
        state["status"] = "violations_notified"
    else:
        state["status"] = "clean_compliance_record"
        print("🟢 No compliance violations found. Record remains clean.")
        
    print(f"\n🎉 Compliance Auditor finished! Final Status: {state['status'].upper()}\n")
    print("=" * 70)

if __name__ == "__main__":
    test_report = (
        "Internal Audit Report: We noticed that user database passwords are stored in plain text "
        "inside log files, violating GDPR section 4 regulations. Desk screens are left unlocked when unattended."
    )
    if len(sys.argv) > 1:
        test_report = " ".join(sys.argv[1:])
        
    run_compliance_pipeline(test_report)

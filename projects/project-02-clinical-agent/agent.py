import os
import sys
from typing import TypedDict
from dotenv import load_dotenv

# Load API keys
load_dotenv()

# =====================================================================
# 1. State Definition
# =====================================================================

class ClinicalState(TypedDict):
    patient_id: str
    symptoms: str
    is_safe: bool
    medical_facts: list[str]
    proposed_diagnosis: str
    doctor_approved: bool
    status: str

# =====================================================================
# 2. Database & Safety Engines
# =====================================================================

# Simulated Medical vector database
MEDICAL_KNOWLEDGE_BASE = {
    "fever_cough": "Guideline: Patient presenting with high fever and cough should be evaluated for viral respiratory infections, including Influenza and COVID-19. Recommend rest, hydration, and PCR test.",
    "chest_pain": "Guideline: Acute chest pain requires immediate ECG to rule out myocardial infarction. Do not treat as minor reflux without diagnostic confirmation."
}

def query_medical_kb(symptoms: str) -> list[str]:
    """Queries medical knowledge base for clinical guidelines."""
    print("🔎 [Medical KB] Searching clinical guidelines...")
    s = symptoms.lower()
    facts = []
    if "fever" in s or "cough" in s:
        facts.append(MEDICAL_KNOWLEDGE_BASE["fever_cough"])
    if "chest" in s or "pain" in s:
        facts.append(MEDICAL_KNOWLEDGE_BASE["chest_pain"])
    return facts

def check_input_safety(symptoms: str) -> bool:
    """Simulates LlamaGuard input safety check for dangerous requests."""
    print("🛡️ [Safety Guard] Checking input for toxic, harmful, or illegal topics...")
    s = symptoms.lower()
    # Simple check for self-harm or weapon requests
    if "poison" in s or "kill" in s or "suicide" in s:
        print("🔴 [Safety Guard] ALERT: Input flagged as unsafe.")
        return False
    print("🟢 [Safety Guard] Input validated as safe.")
    return True

# =====================================================================
# 3. Clinical Agent Nodes
# =====================================================================

def analyze_symptoms_node(state: ClinicalState) -> dict:
    """Generates the clinical report draft grounding the response in guidelines."""
    print("🤖 [Node: analyze_symptoms_node] Synthesizing clinical diagnosis draft...")
    symptoms = state["symptoms"]
    guidelines = "\n".join([f"- {g}" for g in state["medical_facts"]])
    
    # Use API key if available
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ℹ️ Model running in Mock Mode...")
        # Simulated diagnostic draft
        draft = (
            f"### CLINICAL SUPPORT REPORT\n"
            f"Patient ID: {state['patient_id']}\n"
            f"Symptoms: {symptoms}\n\n"
            f"Proposed Evaluation:\n"
            f"- Suspected Viral Respiratory Infection based on guidelines.\n"
            f"- Recommend: Rest, fluid intake, and PCR testing.\n"
            f"Prescription Recommendation: None (Symptomatic care)."
        )
        return {"proposed_diagnosis": draft, "status": "pending_doctor_approval"}

    try:
        from google import genai
        client = genai.Client()
        prompt = f"""You are a Clinical Decision Support Assistant.
Write a clinical evaluation report for a patient presenting with these symptoms:
"{symptoms}"

Ground your recommendations strictly in these medical guidelines:
{guidelines}

Format your report as a medical chart summary. End with recommendations for the physician to approve.
Report:"""
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        return {"proposed_diagnosis": response.text, "status": "pending_doctor_approval"}
    except Exception as e:
        return {"proposed_diagnosis": f"Error generating diagnosis: {str(e)}", "status": "failed"}

# =====================================================================
# 4. Human-in-the-Loop Safeguard
# =====================================================================

def request_doctor_review(state: ClinicalState) -> bool:
    """Hhalts the agent execution thread, prompting the doctor for review."""
    print("\n" + "🩺" * 20)
    print("🏥 PHYSICIAN REVIEW BREAKPOINT REQUIRED")
    print(state["proposed_diagnosis"])
    print("🩺" * 20)
    
    try:
        user_input = input("\n🩺 Doctor: Approve this diagnosis & submit to EHR? (y/n): ").strip().lower()
        if user_input == 'y' or user_input == 'yes':
            print("🟢 Doctor Approved. Committing to Electronic Health Record (EHR)...")
            return True
        else:
            print("🔴 Doctor Rejected. Clinical report discarded.")
            return False
    except EOFError:
        print("ℹ️ Non-interactive run detected. Auto-approving diagnosis...")
        return True

# =====================================================================
# 5. Core Pipeline
# =====================================================================

def run_clinical_workflow(patient_id: str, symptoms: str):
    print("=" * 70)
    print(f"🚀 Initializing Clinical Support System for Patient: {patient_id}")
    print("=" * 70)
    
    # 1. Initialize State
    state: ClinicalState = {
        "patient_id": patient_id,
        "symptoms": symptoms,
        "is_safe": False,
        "medical_facts": [],
        "proposed_diagnosis": "",
        "doctor_approved": False,
        "status": "initialized"
    }
    
    # 2. Safety Check (LlamaGuard Simulator)
    if not check_input_safety(symptoms):
        state["status"] = "blocked_by_safety"
        print("❌ Blocked: input violated safety guidelines.")
        print("=" * 70)
        return
        
    state["is_safe"] = True
    
    # 3. Retrieve Guidelines from Medical KB
    state["medical_facts"] = query_medical_kb(symptoms)
    
    # 4. Run Reasoning Agent (Draft Diagnosis)
    updates = analyze_symptoms_node(state)
    state.update(updates)
    
    # 5. Halt at Breakpoint for HITL approval
    if state["status"] == "pending_doctor_approval":
        approved = request_doctor_review(state)
        state["doctor_approved"] = approved
        
        if approved:
            state["status"] = "committed_to_ehr"
            print("💾 Clinical report committed to patient record database successfully.")
        else:
            state["status"] = "rejected_by_physician"
            
    print(f"\n🎉 Clinical Workflow finished! Final Status: {state['status'].upper()}\n")
    print("=" * 70)

if __name__ == "__main__":
    patient = "P-80324"
    symptoms = "Patient reports a fever of 102F and dry cough for 3 days."
    
    if len(sys.argv) > 2:
        patient = sys.argv[1]
        symptoms = sys.argv[2]
        
    run_clinical_workflow(patient, symptoms)
